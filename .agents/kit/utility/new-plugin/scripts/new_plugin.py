#!/usr/bin/env python3
"""Create a plugin repository in the kit layout."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


SKILL_DIRECTORY = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL_DIRECTORY / "templates"
GENERATOR_TEMPLATE = TEMPLATES / "repository/.agents/sync_generated.py.in"
NAME = re.compile(r"^[a-z][a-z0-9-]*$")
REPOSITORY = re.compile(r"^([A-Za-z0-9_.-]+)/([a-z][a-z0-9-]*)$")
PLACEHOLDER = re.compile(r"\{\{[A-Za-z_]+\}\}")
KIT_VERSION = re.compile(r'^KIT_VERSION = "(\d+\.\d+\.\d+)"$', re.MULTILINE)
VENDORED = (
    ".agents/sync_generated.py",
    ".agents/sync-generated.ps1",
    ".gitattributes",
    ".gitignore",
    "CLAUDE.md",
    ".github/workflows/ci.yml",
)
SKILL_SETS = {"stack": ("common", "stack"), "tool": ("common", "tool"), "utility": ("utility",)}
KIND_HEADINGS = {"knowledge": "Knowledge", "contract": "Contracts, empty until a decision is recorded", "utility": "Utilities"}
AGENTS_RULES = {
    "stack": (
        "`knowledge` is {learner}'s progress record: change it only under `learning`'s Progress rules. A `contract`\n"
        "skill gains a rule only through `learning`'s convention procedure, after {learner} decides it."
    ),
    "tool": "`knowledge` is {learner}'s progress record: change it only under `learning`'s Progress rules.",
    "utility": "Every skill here is a `utility`. Its scripts and templates sit beside its `SKILL.md`.",
}
DEFAULT_PROMPTS = {
    "stack": "Teach me the next {stack} concept my current task needs.",
    "tool": "Teach me the next {stack} step at my current level.",
    "utility": "Show me what {namespace} can do.",
}


def kit_version() -> str:
    match = KIT_VERSION.search(GENERATOR_TEMPLATE.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"{GENERATOR_TEMPLATE}: no KIT_VERSION")
    return match.group(1)


def git_user_name() -> str:
    result = subprocess.run(["git", "config", "--get", "user.name"], capture_output=True, text=True, check=False)
    return result.stdout.strip()


def render(text: str, values: dict[str, str], source: PurePosixPath) -> str:
    in_json = source.name.endswith(".json.in")
    for key, value in values.items():
        replacement = json.dumps(value)[1:-1] if in_json and not key.endswith("_json") else value
        text = text.replace("{{" + key + "}}", replacement)
    leftover = PLACEHOLDER.findall(text)
    if leftover:
        raise ValueError(f"{source}: unknown placeholders {sorted(set(leftover))}")
    return text


def vendored_files(repository: str) -> dict[str, str]:
    values = {"owner": REPOSITORY.fullmatch(repository).group(1), "kit_version": kit_version()}
    return {
        relative: render(
            (TEMPLATES / "repository" / f"{relative}.in").read_text(encoding="utf-8"),
            values,
            PurePosixPath(f"{relative}.in"),
        )
        for relative in VENDORED
    }


def destination_path(relative: PurePosixPath, values: dict[str, str]) -> str:
    parts = [part.replace("__namespace__", values["namespace"]).replace("__skill__", values.get("skill", "")) for part in relative.parts]
    parts[-1] = parts[-1].removesuffix(".in")
    return PurePosixPath(*parts).as_posix()


def tier(arguments: argparse.Namespace, namespace: str) -> dict:
    declaration = {
        "schema_version": 1,
        "tier": namespace,
        "stack": arguments.stack,
        "applies": "stack-present" if arguments.type == "stack" else "always",
        "owner_repository": [arguments.repository],
    }
    if arguments.type == "stack":
        detect = {}
        if arguments.detect_file:
            detect["files"] = arguments.detect_file
        if arguments.detect_glob:
            detect["globs"] = arguments.detect_glob
        declaration["detect"] = detect
    return declaration


def skill_list(files: dict[str, str], namespace: str) -> str:
    grouped: dict[str, list[str]] = {}
    for path in files:
        parts = PurePosixPath(path).parts
        if len(parts) == 5 and parts[0] == ".agents" and parts[4] == "SKILL.md":
            grouped.setdefault(parts[2], []).append(f"`{namespace}:{parts[3]}`")
    lines = []
    for kind in sorted(grouped, key=lambda item: list(KIND_HEADINGS).index(item) if item in KIND_HEADINGS else 99):
        lines.append(f"- {KIND_HEADINGS.get(kind, kind)}: {', '.join(sorted(grouped[kind]))}.")
    return "\n".join(lines)


def plan(arguments: argparse.Namespace) -> dict[str, str]:
    match = REPOSITORY.fullmatch(arguments.repository)
    owner, namespace = match.group(1), match.group(2)
    keywords = [item.strip() for item in (arguments.keywords or namespace).split(",") if item.strip()]
    values = {
        "namespace": namespace,
        "owner": owner,
        "repository": arguments.repository,
        "Stack": arguments.stack,
        "display_name": arguments.stack,
        "description": arguments.description,
        "author": arguments.author,
        "learner": arguments.learner,
        "marketplace": f"{namespace}-agents",
        "category": arguments.category,
        "keywords_json": json.dumps(keywords),
        "default_prompt": DEFAULT_PROMPTS[arguments.type].format(stack=arguments.stack, namespace=namespace),
        "kit_version": kit_version(),
        "date": date.today().isoformat(),
        "agents_rules": AGENTS_RULES[arguments.type].format(learner=arguments.learner),
    }
    if arguments.type == "utility":
        values["skill"] = arguments.skill
    files: dict[str, str] = {}
    sources: list[tuple[Path, PurePosixPath]] = []
    for source in sorted((TEMPLATES / "repository").rglob("*.in")):
        sources.append((source, PurePosixPath(source.relative_to(TEMPLATES / "repository").as_posix())))
    for skill_set in SKILL_SETS[arguments.type]:
        base = TEMPLATES / "skills" / skill_set
        for source in sorted(base.rglob("*.in")):
            sources.append((source, PurePosixPath(".agents", namespace, source.relative_to(base).as_posix())))
    deferred = []
    for source, relative in sources:
        if relative.name == "README.md.in":
            deferred.append((source, relative))
            continue
        files[destination_path(relative, values)] = render(source.read_text(encoding="utf-8"), values, relative)
    values["skill_list"] = skill_list(files, namespace)
    for source, relative in deferred:
        files[destination_path(relative, values)] = render(source.read_text(encoding="utf-8"), values, relative)
    files[f".agents/tiers/{namespace}.json"] = json.dumps(tier(arguments, namespace), indent=2) + "\n"
    files[".agents/plugins/kit.json"] = json.dumps(
        {"schema_version": 1, "kit": values["kit_version"], "repository": arguments.repository, "type": arguments.type},
        indent=2,
    ) + "\n"
    files[".agents/plugins/payloads.json"] = json.dumps({"payloads": {namespace: [namespace]}}, indent=2) + "\n"
    return files


def validate(arguments: argparse.Namespace) -> Path:
    if not REPOSITORY.fullmatch(arguments.repository):
        raise ValueError("--repository must be owner/name with a lowercase name")
    if not arguments.description.strip():
        raise ValueError("--description is required")
    if not arguments.author:
        raise ValueError("--author is required when git config user.name is unset")
    if arguments.type in ("stack", "tool") and not arguments.learner:
        raise ValueError("--learner is required when git config user.name is unset")
    if arguments.type == "stack" and not (arguments.detect_file or arguments.detect_glob):
        raise ValueError("a stack repository needs --detect-file or --detect-glob")
    if arguments.type != "stack" and (arguments.detect_file or arguments.detect_glob):
        raise ValueError("only a stack repository declares detect markers")
    if arguments.type == "utility" and not (arguments.skill and NAME.fullmatch(arguments.skill)):
        raise ValueError("a utility repository needs --skill with a lowercase name")
    destination = arguments.destination.resolve()
    if not destination.is_dir():
        raise ValueError(f"{destination} does not exist")
    target = destination / arguments.repository.split("/", 1)[1]
    if target.exists():
        raise ValueError(f"{target} already exists")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="owner/name; the name is the plugin namespace")
    parser.add_argument("--type", required=True, choices=sorted(SKILL_SETS))
    parser.add_argument("--stack", help="display name, such as Rust; defaults to the capitalized name")
    parser.add_argument("--description", required=True, help="one sentence for the README, manifests and marketplace")
    parser.add_argument("--destination", required=True, type=Path, help="existing parent folder")
    parser.add_argument("--author", default=None)
    parser.add_argument("--learner", default=None)
    parser.add_argument("--detect-file", action="append", default=[])
    parser.add_argument("--detect-glob", action="append", default=[])
    parser.add_argument("--skill", help="first utility skill name, for a utility repository")
    parser.add_argument("--keywords", help="comma-separated; defaults to the name")
    parser.add_argument("--category", default="Productivity")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    arguments.author = arguments.author or git_user_name()
    arguments.learner = arguments.learner or (arguments.author.split()[0] if arguments.author else "")
    if not arguments.stack and REPOSITORY.fullmatch(arguments.repository):
        arguments.stack = arguments.repository.split("/", 1)[1].capitalize()
    try:
        target = validate(arguments)
        files = plan(arguments)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if arguments.dry_run:
        for path in sorted(files):
            print(f"{target.name}/{path}")
        return 0
    for relative, text in files.items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    generated = subprocess.run(
        [sys.executable, "-B", str(target / ".agents/sync_generated.py"), "--root", str(target)], check=False
    )
    if generated.returncode != 0:
        print(f"error: the new repository at {target} did not generate cleanly", file=sys.stderr)
        return generated.returncode
    print(f"created {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
