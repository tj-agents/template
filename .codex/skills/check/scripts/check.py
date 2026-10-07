#!/usr/bin/env python3
"""Check a plugin repository against kit's layout and standard."""

from __future__ import annotations

import argparse
import importlib.util
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

SKILL_DIRECTORY = Path(__file__).resolve().parents[1]
NEW_PLUGIN = SKILL_DIRECTORY.parent / "new-plugin"
STANDARD = json.loads((SKILL_DIRECTORY / "standard.json").read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    loader = SourceFileLoader(name, str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(module)
    return module


new_plugin = load_module("kit_new_plugin", NEW_PLUGIN / "scripts/new_plugin.py")
generator = load_module("kit_generator", new_plugin.GENERATOR_TEMPLATE)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def owns_templates(root: Path) -> bool:
    return (root / ".agents/kit/utility/new-plugin/templates/repository").is_dir()


def check_vendored(root: Path, repository: str, pinned: str) -> list[str]:
    running = new_plugin.kit_version()
    if pinned != running:
        return [f".agents/plugins/kit.json pins kit {pinned}; this check is kit {running}: run kit:update"]
    problems = []
    for relative, expected in new_plugin.vendored_files(repository).items():
        if relative == ".github/workflows/ci.yml" and owns_templates(root):
            continue
        path = root / relative
        if not path.is_file():
            problems.append(f"{relative}: missing; run kit:update")
        elif text(path) != expected:
            problems.append(f"{relative}: differs from kit {running}; change it in kit, then run kit:update")
    return problems


def check_files(root: Path) -> list[str]:
    problems = [f"{name}: required" for name in STANDARD["root_files"] if not (root / name).is_file()]
    problems += [f"{name}: retired; kit documents the layout" for name in STANDARD["retired_files"] if (root / name).exists()]
    for entry in sorted((root / ".agents/plugins").iterdir()):
        retired = f".agents/plugins/{entry.name}" in STANDARD["retired_files"]
        if entry.name not in STANDARD["plugins_entries"] and not retired:
            problems.append(f".agents/plugins/{entry.name}: not part of the plugin layout")
    return problems


def check_agents_entries(root: Path, plugins: set[str]) -> list[str]:
    problems = []
    for entry in sorted((root / ".agents").iterdir()):
        if entry.name == "__pycache__":
            continue
        allowed = STANDARD["agents_folders"] + sorted(plugins) if entry.is_dir() else STANDARD["agents_files"]
        if entry.name not in allowed:
            problems.append(f".agents/{entry.name}: not part of the plugin layout")
    return problems


def headings(body: str) -> set[str]:
    return {line.rstrip() for line in body.splitlines() if line.startswith("## ")}


def opening(body: str) -> str:
    lines = generator.FRONTMATTER.match(body).group("body").splitlines()
    after_title = False
    for line in lines:
        if line.startswith("# "):
            after_title = True
        elif after_title and line.strip():
            return line
    return ""


def skill_problems(skill: dict, name: str, rule: dict, namespace: str) -> list[str]:
    problems = []
    if skill["kind"] != rule["kind"] or skill["metadata"]["profile"] != rule["profile"]:
        problems.append(f"{skill['directory']}: {name} is kind {rule['kind']}, profile {rule['profile']}")
    present = headings(skill["body"])
    for heading in rule["sections"]:
        heading = heading.replace("{namespace}", namespace)
        if heading not in present:
            problems.append(f"{skill['directory']}/SKILL.md: missing section {heading}")
    return problems


def check_standard(root: Path, kind: str, namespace: str, plugins: dict[str, dict[str, dict]]) -> list[str]:
    standard = STANDARD["types"][kind]
    problems = []
    if namespace not in plugins:
        return [f".agents/{namespace}: a repository's main plugin folder is named after the repository"]
    tier_path = root / f".agents/tiers/{namespace}.json"
    if not tier_path.is_file():
        problems.append(f".agents/tiers/{namespace}.json: required")
    elif json.loads(text(tier_path)).get("applies") not in (standard["applies"] if isinstance(standard["applies"], list) else [standard["applies"]]):
        problems.append(f".agents/tiers/{namespace}.json: a {kind} repository applies {standard['applies']}")
    for name, rule in standard["skills"].items():
        owners = plugins.values() if rule.get("anywhere") else [plugins[namespace]]
        candidates = [skills[name] for skills in owners if name in skills]
        if not candidates:
            where = "any plugin" if rule.get("anywhere") else f"plugin {namespace}"
            problems.append(f"{name}: a {kind} repository needs this {rule['kind']} skill in {where}")
            continue
        found = [skill_problems(skill, name, rule, namespace) for skill in candidates]
        if all(found):
            problems += [problem for skill_found in found for problem in skill_found]
    for plugin, skills in plugins.items():
        for skill in skills.values():
            if "only_kinds" in standard and skill["kind"] not in standard["only_kinds"]:
                problems.append(f"{skill['directory']}: a {kind} repository has only {', '.join(standard['only_kinds'])} skills")
            if skill["kind"] == "contract" and not opening(skill["body"]).startswith(STANDARD["contract_opening"]):
                problems.append(f"{skill['directory']}/SKILL.md: a contract opens with an `Owns â€¦` line after its title")
    return problems


def check_names(plugins: dict[str, dict[str, dict]], aliases: dict[str, dict]) -> list[str]:
    problems = []
    for plugin, skills in plugins.items():
        exempt = set(aliases.get(plugin, {}))
        flat: dict[tuple[str, str], set[str]] = {}
        families: set[tuple[str, str]] = set()
        for skill in skills.values():
            if skill["name"] in exempt:
                continue
            parts = skill["directory"].split("/")[3:]
            if parts[0] == plugin or parts[0].startswith(f"{plugin}-"):
                problems.append(f"{skill['directory']}: a skill name does not repeat its namespace {plugin}")
            for index, part in enumerate(parts[1:], 1):
                for family in parts[:index]:
                    if part == family or part.startswith(f"{family}-") or part.endswith(f"-{family}"):
                        problems.append(f"{skill['directory']}: {part} repeats its family {family}")
            if len(parts) > 1:
                families.add((skill["kind"], parts[0]))
            elif "-" in parts[0]:
                words = parts[0].split("-")
                for word in {words[0], words[-1]}:
                    flat.setdefault((skill["kind"], word), set()).add(parts[0])
        for (kind, word), names in sorted(flat.items()):
            if len(names) > 1 or (kind, word) in families:
                problems.append(
                    f".agents/{plugin}/{kind}: {', '.join(sorted(names))} share `{word}`; "
                    f"fold them into the family folder {word}/<member>/"
                )
    return problems


def check(root: Path) -> list[str]:
    config_path = root / ".agents/plugins/kit.json"
    if not config_path.is_file():
        return [".agents/plugins/kit.json: missing; this is not a kit plugin repository"]
    config = json.loads(text(config_path))
    match = generator.REPOSITORY.fullmatch(str(config.get("repository", "")))
    if match is None:
        return [".agents/plugins/kit.json: repository must be owner/name with a lowercase name"]
    kind = config.get("type")
    if kind not in STANDARD["types"]:
        return [f".agents/plugins/kit.json: type must be one of {', '.join(STANDARD['types'])}"]
    namespace = match.group(1)
    problems = check_vendored(root, config["repository"], str(config.get("kit")))
    problems += check_files(root)
    try:
        plugins = generator.discover(root, namespace)
    except ValueError as error:
        return problems + [str(error)]
    problems += check_agents_entries(root, set(plugins))
    problems += check_standard(root, kind, namespace, plugins)
    payloads_path = root / ".agents/plugins/payloads.json"
    try:
        aliases = json.loads(text(payloads_path)).get("compatibilitySkillAliases", {}) if payloads_path.is_file() else {}
    except (json.JSONDecodeError, AttributeError) as error:
        return problems + [f".agents/plugins/payloads.json: not a JSON object ({error})"]
    problems += check_names(plugins, aliases)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    root = parser.parse_args().root.resolve()
    problems = check(root)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"{root.name} does not conform to kit {new_plugin.kit_version()}: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"{root.name} conforms to kit {new_plugin.kit_version()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
