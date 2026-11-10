import argparse
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode


@dataclass(frozen=True, slots=True)
class Finding:
    path: Path
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}: {self.message}"


def members(node: Node | None) -> Iterator[tuple[str, Node]]:
    if isinstance(node, MappingNode):
        for key, value in node.value:
            if isinstance(key, ScalarNode):
                yield key.value, value


def member(node: Node | None, key: str) -> Node | None:
    return next((value for name, value in members(node) if name == key), None)


def scalar(node: Node | None) -> str:
    return node.value if isinstance(node, ScalarNode) else ""


def check_file(path: Path) -> list[Finding]:
    found: list[Finding] = []
    root = yaml.compose(path.read_text(encoding="utf-8"), Loader=yaml.SafeLoader)

    def report(node: Node | None, rule: str, message: str) -> None:
        found.append(
            Finding(path, node.start_mark.line + 1 if node else 1, rule, message)
        )

    def names(node: Node | None, pattern: str, kind: str) -> None:
        for name, value in members(node):
            if not re.fullmatch(pattern, name):
                report(value, "naming", f"{kind} {name!r} has the wrong case")

    def environment(node: Node | None, step: bool = False) -> None:
        names(node, r"[A-Z_][A-Z0-9_]*", "environment variable")
        if not step:
            if re.search(r"\$\{\{[\s\S]*?\bsecrets\b", scalar(node)):
                report(node, "secret-env", "secret environment belongs in step env")
            for name, value in members(node):
                if re.search(r"\$\{\{[\s\S]*?\bsecrets\b", scalar(value)):
                    report(value, "secret-env", f"secret {name!r} belongs in step env")

    def declarations(node: Node | None) -> None:
        for kind in ("inputs", "outputs"):
            names(member(node, kind), r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", kind)
        names(member(node, "secrets"), r"[A-Z_][A-Z0-9_]*", "secret")

    workflow = path.parent.name == "workflows"
    name = member(root, "name")
    if workflow and not re.fullmatch(r"[A-Z][^\n]*", scalar(name)):
        report(name, "naming", "workflow name must start with an uppercase letter")
    environment(member(root, "env"))
    declarations(root)
    for _, event in members(member(root, "on")):
        declarations(event)
    names(member(root, "jobs"), r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", "job")

    def steps(node: Node | None, default_shell: str) -> None:
        if not isinstance(node, SequenceNode):
            return
        for step in node.value:
            run = member(step, "run")
            uses = member(step, "uses")
            step_name = member(step, "name")
            if not scalar(step_name) and not uses and "\n" in scalar(run).strip():
                report(step, "naming", "multi-line run step needs a name")
            elif step_name and not re.match(r"[A-Z]", scalar(step_name)):
                report(
                    step_name, "naming", "step name must start with an uppercase letter"
                )
            environment(member(step, "env"), step=True)
            shell = scalar(member(step, "shell")) or default_shell
            script = scalar(run).strip()
            if (
                shell.split()[:1] == ["bash"]
                and "\n" in script
                and script.splitlines()[0].strip() != "set -euo pipefail"
            ):
                report(
                    run, "bash-strict", "multi-line bash starts with set -euo pipefail"
                )

    defaults = scalar(member(member(member(root, "defaults"), "run"), "shell"))
    for job_name, job in members(member(root, "jobs")):
        uses = member(job, "uses")
        reference = scalar(uses)
        template = "tj-agents/template/.github/workflows/plugin-ci.yml@"
        if reference.startswith(template) and not re.fullmatch(
            r"(?:main|[a-fA-F0-9]{40})", reference.removeprefix(template)
        ):
            report(uses, "template-ref", "shared Template CI uses main or a full SHA")
        job_title = member(job, "name")
        if not re.match(r"[A-Z]", scalar(job_title)):
            report(
                job_title or job,
                "naming",
                f"job {job_name!r} name {scalar(job_title)!r} "
                "must start with an uppercase letter",
            )
        environment(member(job, "env"))
        names(member(job, "outputs"), r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", "output")
        job_defaults = scalar(member(member(member(job, "defaults"), "run"), "shell"))
        runner = scalar(member(job, "runs-on"))
        implicit_shell = "pwsh" if runner.startswith("windows-") else "bash"
        steps(member(job, "steps"), job_defaults or defaults or implicit_shell)
    runs = member(root, "runs")
    if scalar(member(runs, "using")) == "composite":
        steps(member(runs, "steps"), "")
    return found


def workflow_files(root: Path) -> list[Path]:
    workflows = root / ".github/workflows"
    files = [
        path
        for path in workflows.glob("*")
        if path.suffix in {".yml", ".yaml"} and path.is_file()
    ]
    actions = root / ".github/actions"
    files.extend(actions.rglob("action.yml"))
    files.extend(actions.rglob("action.yaml"))
    return sorted(files)


def apply_baseline(root: Path, found: list[Finding], path: Path) -> list[Finding]:
    if not path.is_file():
        return found
    entries: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"{path}: baseline must be a list")
    remaining = found.copy()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "path",
            "rule",
            "message",
            "reason",
        }:
            raise ValueError(f"{path}: baseline needs path, rule, message and reason")
        if not all(
            isinstance(value, str) and value.strip() for value in entry.values()
        ):
            raise ValueError(f"{path}: baseline fields must be nonempty strings")
        if not (root / entry["path"]).is_file():
            continue
        match = next(
            (
                finding
                for finding in remaining
                if finding.path.relative_to(root).as_posix() == entry["path"]
                and finding.rule == entry["rule"]
                and finding.message == entry["message"]
            ),
            None,
        )
        if match is None:
            if (
                path.resolve()
                == Path(__file__).with_name("workflow-baseline.json").resolve()
            ):
                continue
            raise ValueError(f"{path}: stale baseline entry: {entry['message']}")
        remaining.remove(match)
        print(f"Baselined {match}: {entry['reason']}")
    return remaining


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", type=Path)
    arguments = parser.parse_args()
    found = []
    for path in workflow_files(arguments.root):
        try:
            found.extend(check_file(path))
        except yaml.YAMLError as error:
            print(f"{path}: invalid YAML: {error}", file=sys.stderr)
            return 1
    try:
        local = arguments.root / ".github/workflow-baseline.json"
        baseline = arguments.baseline or (
            local
            if local.is_file()
            else Path(__file__).with_name("workflow-baseline.json")
        )
        found = apply_baseline(arguments.root, found, baseline)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    for finding in found:
        print(finding, file=sys.stderr)
    return int(bool(found))


if __name__ == "__main__":
    raise SystemExit(main())
