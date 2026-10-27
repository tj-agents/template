#!/usr/bin/env python3
"""Resolve authored skill references against the shipped repositories that publish
the referenced plugins."""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

IDENTITY = r"[a-z][a-z0-9-]*"
QUALIFIED = re.compile(rf"(?<![\w:-])({IDENTITY}):({IDENTITY})(?![\w/-])")
BACKTICK = re.compile(r"`([^`\n]+)`")
BARE = re.compile(
    rf"(?:\bskill\s+`({IDENTITY})`|`({IDENTITY})`\s+skill\b)", re.IGNORECASE
)
LIST = re.compile(r"\bskills?\s*\(([^)\n]+)\)", re.IGNORECASE)
BACKTICK_LIST = r"`[^`\n]+`(?:\s*(?:,\s*(?:(?:and|or)\s+)?|(?:and|or)\s+)`[^`\n]+`)*"
NAMED_LIST = re.compile(
    rf"(?:\bskills\s*:?\s+(?P<prefix>{BACKTICK_LIST})|(?P<suffix>{BACKTICK_LIST})\s+skills\b)",
    re.IGNORECASE,
)
COMMENT = re.compile(r"<!--.*?-->")
MARKETPLACE_PLUGINS = "plugins.json"
TOKEN_VARIABLE = "SKILL_REFERENCES_TOKEN"
PLACEHOLDER = re.compile(
    r"[{}<>*]|^(?:namespace:skill|plugin:skill|your-plugin:your-skill)$"
)


def inventory(roots: list[Path]) -> set[str]:
    return {
        f"{path.parent.parent.parent.name}:{path.parent.name}"
        for root in roots
        for path in (root / "plugins").glob("*/skills/*/SKILL.md")
    }


def authored(root: Path) -> Iterator[tuple[Path, str | None]]:
    for name in ("AGENTS.md", "CLAUDE.md", "README.md"):
        path = root / name
        if path.is_file():
            yield path, None
    canonical = root / ".agents"
    active = list(canonical.glob("*/**/SKILL.md"))
    for path in sorted(active):
        relative = path.relative_to(canonical)
        if relative.parts[0] in ("tests", "plugins") or any(
            part in ("templates", "fixtures", "node_modules") for part in relative.parts
        ):
            continue
        yield path, relative.parts[0]
    if not active:
        for path in sorted((root / "plugins").glob("*/skills/*/SKILL.md")):
            yield path, path.parent.parent.parent.name


def references(line: str, namespaces: set[str]) -> list[str]:
    line = COMMENT.sub("", line)
    explicit = {match.group(1) for match in BACKTICK.finditer(line)}
    found = set()
    listed = {
        match.group(1)
        for group in NAMED_LIST.finditer(line)
        for match in BACKTICK.finditer(group.group("prefix") or group.group("suffix"))
    }
    for match in QUALIFIED.finditer(line):
        reference = match.group(0)
        containing = next((item for item in explicit if reference in item), None)
        skill_context = bool(
            re.search(
                rf"(?:skills?\s+`?{re.escape(reference)}`?|`?{re.escape(reference)}`?\s+skills?\b|[/$]{re.escape(reference)}\b|--skill\s+{re.escape(reference)}\b)",
                line,
                re.IGNORECASE,
            )
        )
        skill_context = skill_context or any(
            reference in group.group(1) for group in LIST.finditer(line)
        )
        if (match.group(1) in namespaces or skill_context or reference in listed) and (
            containing is None or not PLACEHOLDER.search(containing)
        ):
            found.add(reference)
    for match in BARE.finditer(line):
        name = match.group(1) or match.group(2)
        if name in {
            "knowledge",
            "contract",
            "utility",
            "policy",
            "convention",
        } and re.search(r"\b(?:a|an)\s+$", line[: match.start()], re.IGNORECASE):
            continue
        found.add(name)
    for name in listed:
        if re.fullmatch(IDENTITY, name) and not PLACEHOLDER.search(name):
            found.add(name)
    for group in LIST.finditer(line):
        for match in BACKTICK.finditer(group.group(1)):
            if re.fullmatch(IDENTITY, match.group(1)) and not PLACEHOLDER.search(
                match.group(1)
            ):
                found.add(match.group(1))
    return sorted(found)


def external_skills(configs: Sequence[Path]) -> tuple[set[str], list[str]]:
    identities = set()
    problems = []
    for path in configs:
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
            entries = config.get("external_skills", {})
            if not isinstance(entries, dict):
                raise ValueError("external_skills must be an object")
            for name, rationale in entries.items():
                if (
                    not re.fullmatch(rf"{IDENTITY}:{IDENTITY}", name)
                    or not isinstance(rationale, str)
                    or not rationale.strip()
                ):
                    raise ValueError(
                        "external_skills needs exact namespace:skill names "
                        "and nonempty rationale"
                    )
                identities.add(name)
        except (OSError, ValueError, AttributeError) as error:
            problems.append(f"{path}:1: {error}")
    return identities, problems


def reference_problem(
    reference: str, local: str | None, shipped: set[str], known: set[str]
) -> str | None:
    if ":" in reference:
        candidates = [reference] if reference in known else []
    elif local and f"{local}:{reference}" in shipped:
        candidates = [f"{local}:{reference}"]
    else:
        candidates = sorted(
            name for name in known if name.split(":", 1)[1] == reference
        )
    if not candidates:
        return f"missing skill {reference}"
    if len(candidates) > 1:
        return f"ambiguous skill {reference}: {', '.join(candidates)}"
    return None


def extra_references(
    paths: Sequence[Path],
    source_roots: list[Path],
    namespaces: set[str],
    seen: set[Path],
    problems: list[str],
) -> Iterator[tuple[Path, int, str]]:
    roots = [root.resolve() for root in source_roots]
    for requested in paths:
        path = requested.resolve()
        if not any(path.is_relative_to(root) for root in roots):
            problems.append(
                f"{requested}:1: reference path is outside scanned repositories"
            )
            continue
        if not path.exists():
            problems.append(f"{path}:1: reference path does not exist")
            continue
        if path.is_file() and path.suffix.lower() != ".md":
            problems.append(f"{path}:1: expected Markdown")
            continue
        files = sorted(path.rglob("*")) if path.is_dir() else [path]
        for file in files:
            if not file.is_file() or file.suffix.lower() != ".md":
                continue
            resolved = file.resolve()
            if not any(resolved.is_relative_to(root) for root in roots):
                problems.append(
                    f"{file}:1: reference file is outside scanned repositories"
                )
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                body = file.read_text(encoding="utf-8")
                for number, line in enumerate(body.splitlines(), 1):
                    for reference in references(line, namespaces):
                        yield file, number, reference
            except OSError as error:
                problems.append(f"{file}:1: {error}")


def check(
    roots: list[Path],
    configs: Sequence[Path] = (),
    source_roots: list[Path] | None = None,
    reference_paths: Sequence[Path] = (),
) -> list[str]:
    shipped = inventory(roots)
    external, problems = external_skills(configs)
    known = shipped | external
    namespaces = {name.split(":", 1)[0] for name in known}
    scanned = source_roots if source_roots is not None else roots
    seen: set[Path] = set()
    for root in scanned:
        for path, local in authored(root):
            seen.add(path.resolve())
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                for reference in references(line, namespaces):
                    problem = reference_problem(reference, local, shipped, known)
                    if problem:
                        problems.append(f"{path}:{number}: {problem}")
    for path, number, reference in extra_references(
        reference_paths, scanned, namespaces, seen, problems
    ):
        problem = reference_problem(reference, None, shipped, known)
        if problem:
            problems.append(f"{path}:{number}: {problem}")
    return problems


def clone(repository: str, destination: Path) -> Path:
    token = os.environ.get(TOKEN_VARIABLE)
    credentials = f"x-access-token:{token}@" if token else ""
    subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--depth",
            "1",
            f"https://{credentials}github.com/{repository}.git",
            str(destination),
        ],
        check=True,
        capture_output=True,
    )
    return destination


def referenced_namespaces(roots: Sequence[Path]) -> set[str]:
    return {
        match.group(1)
        for root in roots
        for path, _ in authored(root)
        for match in QUALIFIED.finditer(path.read_text(encoding="utf-8"))
    }


def publishers(marketplace: str, checkout: Path) -> dict[str, str]:
    owner = marketplace.split("/", 1)[0]
    plugins = json.loads((checkout / MARKETPLACE_PLUGINS).read_text(encoding="utf-8"))
    return {
        plugin["name"]: f"{owner}/{plugin['repository']}"
        for plugin in plugins["plugins"]
    }


def published_roots(
    marketplace: str,
    sources: Sequence[Path],
    workspace: Path,
    fetch: Callable[[str, Path], Path] = clone,
) -> list[Path]:
    repositories = publishers(
        marketplace, fetch(marketplace, workspace / "marketplace")
    )
    wanted = sorted(
        {
            repositories[name]
            for name in referenced_namespaces(sources)
            if name in repositories
        }
    )
    return [
        fetch(repository, workspace / repository.split("/", 1)[1])
        for repository in wanted
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        action="append",
        type=Path,
        help="scan only these source roots; --root still supplies inventory",
    )
    parser.add_argument(
        "--reference-path",
        action="append",
        type=Path,
        default=[],
        help="check active Markdown paths inside scanned repositories",
    )
    parser.add_argument("--config", action="append", type=Path, default=[])
    parser.add_argument(
        "--marketplace",
        help="owner/repository whose plugin list names each plugin's publisher",
    )
    arguments = parser.parse_args()
    roots = list(dict.fromkeys(root.resolve() for root in arguments.root))
    with tempfile.TemporaryDirectory(prefix="skill-references-") as workspace:
        if arguments.marketplace:
            roots += published_roots(arguments.marketplace, roots, Path(workspace))
        return report(roots, arguments, parser)


def report(
    roots: list[Path], arguments: argparse.Namespace, parser: argparse.ArgumentParser
) -> int:
    configs = arguments.config + [
        root / ".agents/plugins/skill-references.json"
        for root in roots
        if (root / ".agents/plugins/skill-references.json").is_file()
    ]
    source_roots = (
        [root.resolve() for root in arguments.source_root]
        if arguments.source_root
        else None
    )
    if source_roots is not None and any(root not in roots for root in source_roots):
        parser.error("every --source-root must also be an inventory --root")
    problems = check(roots, configs, source_roots, arguments.reference_path)
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        shipped_count = len(inventory(roots))
        print(
            f"Skill references resolve across {len(roots)} repositories "
            f"({shipped_count} shipped skills)"
        )
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
