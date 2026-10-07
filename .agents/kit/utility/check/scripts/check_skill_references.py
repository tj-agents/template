#!/usr/bin/env python3
"""Resolve authored skill references against explicitly supplied shipped repositories."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

IDENTITY = r"[a-z][a-z0-9-]*"
QUALIFIED = re.compile(rf"(?<![\w:-])({IDENTITY}):({IDENTITY})(?![\w/-])")
BACKTICK = re.compile(r"`([^`\n]+)`")
BARE = re.compile(rf"(?:\bskill\s+`({IDENTITY})`|`({IDENTITY})`\s+skill\b)", re.IGNORECASE)
LIST = re.compile(r"\bskills?\s*\(([^)\n]+)\)", re.IGNORECASE)
BACKTICK_LIST = r"`[^`\n]+`(?:\s*(?:,\s*(?:(?:and|or)\s+)?|(?:and|or)\s+)`[^`\n]+`)*"
NAMED_LIST = re.compile(rf"(?:\bskills\s*:?\s+(?P<prefix>{BACKTICK_LIST})|(?P<suffix>{BACKTICK_LIST})\s+skills\b)", re.IGNORECASE)
PLACEHOLDER = re.compile(r"[{}<>*]|^(?:namespace:skill|plugin:skill|your-plugin:your-skill)$")


def inventory(roots: list[Path]) -> set[str]:
    return {f"{path.parent.parent.parent.name}:{path.parent.name}"
            for root in roots for path in (root / "plugins").glob("*/skills/*/SKILL.md")}


def authored(root: Path):
    for name in ("AGENTS.md", "CLAUDE.md", "README.md"):
        path = root / name
        if path.is_file():
            yield path, None
    canonical = root / ".agents"
    active = list(canonical.glob("*/**/SKILL.md"))
    for path in sorted(active):
        relative = path.relative_to(canonical)
        if relative.parts[0] in ("tests", "plugins") or any(part in ("templates", "fixtures", "node_modules") for part in relative.parts):
            continue
        yield path, relative.parts[0]
    if not active:
        for path in sorted((root / "plugins").glob("*/skills/*/SKILL.md")):
            yield path, path.parent.parent.parent.name


def references(line: str, namespaces: set[str]):
    explicit = {match.group(1) for match in BACKTICK.finditer(line)}
    found = set()
    listed = {match.group(1) for group in NAMED_LIST.finditer(line)
              for match in BACKTICK.finditer(group.group("prefix") or group.group("suffix"))}
    for match in QUALIFIED.finditer(line):
        reference = match.group(0)
        containing = next((item for item in explicit if reference in item), None)
        skill_context = bool(re.search(rf"(?:skills?\s+`?{re.escape(reference)}`?|`?{re.escape(reference)}`?\s+skills?\b|[/$]{re.escape(reference)}\b|--skill\s+{re.escape(reference)}\b)", line, re.IGNORECASE))
        skill_context = skill_context or any(reference in group.group(1) for group in LIST.finditer(line))
        if match.group(1) in namespaces or skill_context or reference in listed:
            if containing is None or not PLACEHOLDER.search(containing):
                found.add(reference)
    for match in BARE.finditer(line):
        name = match.group(1) or match.group(2)
        if name in {"knowledge", "contract", "utility", "policy", "convention"} and re.search(r"\b(?:a|an)\s+$", line[:match.start()], re.IGNORECASE):
            continue
        found.add(name)
    for name in listed:
        if re.fullmatch(IDENTITY, name) and not PLACEHOLDER.search(name):
            found.add(name)
    for group in LIST.finditer(line):
        for match in BACKTICK.finditer(group.group(1)):
            if re.fullmatch(IDENTITY, match.group(1)) and not PLACEHOLDER.search(match.group(1)):
                found.add(match.group(1))
    return sorted(found)


def external_skills(configs: list[Path]) -> tuple[set[str], list[str]]:
    identities = set()
    problems = []
    for path in configs:
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
            entries = config.get("external_skills", {})
            if not isinstance(entries, dict):
                raise ValueError("external_skills must be an object")
            for name, rationale in entries.items():
                if not re.fullmatch(rf"{IDENTITY}:{IDENTITY}", name) or not isinstance(rationale, str) or not rationale.strip():
                    raise ValueError("external_skills needs exact namespace:skill names and nonempty rationale")
                identities.add(name)
        except (OSError, ValueError, AttributeError) as error:
            problems.append(f"{path}:1: {error}")
    return identities, problems


def check(roots: list[Path], configs: list[Path] = (), source_roots: list[Path] | None = None) -> list[str]:
    shipped = inventory(roots)
    external, problems = external_skills(configs)
    known = shipped | external
    namespaces = {name.split(":", 1)[0] for name in known}
    for root in source_roots if source_roots is not None else roots:
        for path, local in authored(root):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for reference in references(line, namespaces):
                    if ":" in reference:
                        candidates = [reference] if reference in known else []
                    elif local and f"{local}:{reference}" in shipped:
                        candidates = [f"{local}:{reference}"]
                    else:
                        candidates = sorted(name for name in known if name.split(":", 1)[1] == reference)
                    if not candidates:
                        problems.append(f"{path}:{number}: missing skill {reference}")
                    elif len(candidates) > 1:
                        problems.append(f"{path}:{number}: ambiguous skill {reference}: {', '.join(candidates)}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=Path, required=True)
    parser.add_argument("--source-root", action="append", type=Path, help="scan only these source roots; --root still supplies inventory")
    parser.add_argument("--config", action="append", type=Path, default=[])
    arguments = parser.parse_args()
    roots = list(dict.fromkeys(root.resolve() for root in arguments.root))
    configs = arguments.config + [root / ".agents/plugins/skill-references.json" for root in roots
                                  if (root / ".agents/plugins/skill-references.json").is_file()]
    source_roots = [root.resolve() for root in arguments.source_root] if arguments.source_root else None
    if source_roots is not None and any(root not in roots for root in source_roots):
        parser.error("every --source-root must also be an inventory --root")
    problems = check(roots, configs, source_roots)
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        print(f"Skill references resolve across {len(roots)} repositories ({len(inventory(roots))} shipped skills)")
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
