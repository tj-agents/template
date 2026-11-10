import argparse
import re
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import check_workflows
import yaml


@dataclass(frozen=True, slots=True)
class WorkflowPin:
    path: Path
    line: int
    repository: str
    ref: str


def workflow_pins(path: Path) -> Iterator[WorkflowPin]:
    root = yaml.compose(path.read_text(encoding="utf-8"), Loader=yaml.SafeLoader)
    for _, job in check_workflows.members(check_workflows.member(root, "jobs")):
        uses = check_workflows.member(job, "uses")
        reference = check_workflows.scalar(uses)
        if not reference or reference.startswith("./"):
            continue
        match = re.fullmatch(
            r"([\w.-]+/[\w.-]+)/\.github/workflows/[^/@]+\.ya?ml@([^@\s]+)",
            reference,
        )
        if match is None or uses is None:
            raise ValueError(
                f"{path}: invalid reusable-workflow reference {reference!r}"
            )
        yield WorkflowPin(path, uses.start_mark.line + 1, match[1], match[2])


def github_field(endpoint: str, query: str) -> str:
    result = subprocess.run(
        ["gh", "api", endpoint, "--jq", query],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    value = result.stdout.strip()
    if not value or value == "null":
        raise ValueError(f"GitHub returned no {query} for {endpoint}")
    return value


def check_pin(pin: WorkflowPin, default_branch: str) -> str | None:
    comparison = f"{quote(pin.ref, safe='')}...{quote(default_branch, safe='')}"
    status = github_field(f"repos/{pin.repository}/compare/{comparison}", ".status")
    if status in {"ahead", "identical"}:
        return None
    return (
        f"{pin.path}:{pin.line}: workflow-pin: {pin.repository}@{pin.ref} "
        f"is not an ancestor of its default branch {default_branch!r}; "
        "repin to a commit on that branch"
    )


def check(root: Path) -> list[str]:
    failures = []
    defaults: dict[str, str] = {}
    for path in check_workflows.workflow_files(root):
        if path.parent.name != "workflows":
            continue
        failures.extend(check_file(path, defaults))
    return failures


def check_file(path: Path, defaults: dict[str, str]) -> list[str]:
    failures = []
    for pin in workflow_pins(path):
        if pin.repository not in defaults:
            defaults[pin.repository] = github_field(
                f"repos/{pin.repository}", ".default_branch"
            )
        failure = check_pin(pin, defaults[pin.repository])
        if failure is not None:
            failures.append(failure)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    try:
        failures = check(arguments.root)
    except (
        OSError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        ValueError,
        yaml.YAMLError,
    ) as error:
        print(
            f"workflow-pin: cannot verify producer ancestry: {error}", file=sys.stderr
        )
        return 1
    for failure in failures:
        print(failure, file=sys.stderr)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
