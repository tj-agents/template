#!/usr/bin/env python3
"""Check a plugin repository against Template's layout and standard."""

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


new_plugin = load_module("template_new_plugin", NEW_PLUGIN / "scripts/new_plugin.py")
generator = load_module("template_generator", new_plugin.GENERATOR_TEMPLATE)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def owns_templates(root: Path) -> bool:
    return (root / ".agents/template/utility/new-plugin/templates/repository").is_dir()


def check_vendored(root: Path, repository: str, pinned: str) -> list[str]:
    running = new_plugin.template_version()
    if pinned != running:
        return [f".agents/plugins/template.json pins Template {pinned}; this check is {running}: run update"]
    problems = []
    for relative, expected in new_plugin.vendored_files(repository).items():
        if relative == ".github/workflows/ci.yml" and owns_templates(root):
            continue
        path = root / relative
        if not path.is_file():
            problems.append(f"{relative}: missing; run update")
        elif text(path) != expected:
            problems.append(f"{relative}: differs from release {running}; change it in the source repository, then run update")
    return problems


def check_files(root: Path) -> list[str]:
    problems = [f"{name}: required" for name in STANDARD["root_files"] if not (root / name).is_file()]
    problems += [f"{name}: retired; Template documents the layout" for name in STANDARD["retired_files"] if (root / name).exists()]
    plugins_root = root / ".agents/plugins"
    if not plugins_root.is_dir():
        return [*problems, ".agents/plugins: required"]
    for entry in sorted(plugins_root.iterdir()):
        retired = f".agents/plugins/{entry.name}" in STANDARD["retired_files"]
        if entry.name not in STANDARD["plugins_entries"] and not retired:
            problems.append(f".agents/plugins/{entry.name}: not part of the plugin layout")
    return problems


def check_agents_entries(root: Path, plugins: set[str]) -> list[str]:
    problems = []
    agents_root = root / ".agents"
    if not agents_root.is_dir():
        return [".agents: required"]
    for entry in sorted(agents_root.iterdir()):
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
    allowed_kinds = {rule["kind"], *rule.get("legacy_kinds", [])}
    if skill["kind"] not in allowed_kinds or skill["metadata"]["profile"] != rule["profile"]:
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
    else:
        try:
            applies = json.loads(text(tier_path)).get("applies")
        except (json.JSONDecodeError, AttributeError) as error:
            problems.append(f".agents/tiers/{namespace}.json: not a JSON object ({error})")
        else:
            if applies not in (standard["applies"] if isinstance(standard["applies"], list) else [standard["applies"]]):
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
            if skill["kind"] in ("contract", "convention") and not opening(skill["body"]).startswith(STANDARD["convention_opening"]):
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


def check_effective_dependency_projection(root: Path, config: dict, generated: dict[str, bytes]) -> list[str]:
    if config["type"] != "stack":
        return []
    paths = [path for path in generated if path == ".claude-plugin/marketplace.json" or path.endswith(("/selection.json", "/harness.json", "/.claude-plugin/plugin.json"))]
    present = [path for path in paths if (root / path).is_file()]
    if not present:
        return []
    problems = []
    for path in paths:
        actual = root / path
        if not actual.is_file():
            problems.append(f"{path}: effective dependency projection is missing or differs")
            continue
        try:
            expected = json.loads(generated[path])
            observed = json.loads(text(actual))
        except (json.JSONDecodeError, UnicodeDecodeError):
            problems.append(f"{path}: effective dependency projection is missing or differs")
            continue
        if not isinstance(expected, dict) or not isinstance(observed, dict):
            matches = False
        elif path.endswith("/selection.json"):
            matches = observed.get("dependencies") == expected.get("dependencies")
        elif path.endswith("/harness.json"):
            observed_requires = observed.get("requires")
            expected_requires = expected.get("requires")
            matches = (
                isinstance(observed_requires, dict)
                and isinstance(expected_requires, dict)
                and observed_requires.get("plugins") == expected_requires.get("plugins")
                and observed_requires.get("marketplaces") == expected_requires.get("marketplaces")
            )
        elif path.endswith("/.claude-plugin/plugin.json"):
            matches = observed.get("dependencies") == expected.get("dependencies")
        else:
            matches = observed.get("allowCrossMarketplaceDependenciesOn") == expected.get("allowCrossMarketplaceDependenciesOn")
        if not matches:
            problems.append(f"{path}: effective dependency projection is missing or differs")
    return problems


def check(root: Path) -> list[str]:
    config_path = root / ".agents/plugins/template.json"
    if not config_path.is_file():
        return [".agents/plugins/template.json: missing; this is not a Template plugin repository"]
    try:
        config = json.loads(text(config_path))
    except json.JSONDecodeError as error:
        return [f".agents/plugins/template.json: invalid JSON ({error})"]
    if not isinstance(config, dict):
        return [".agents/plugins/template.json: must be a JSON object"]
    match = generator.REPOSITORY.fullmatch(str(config.get("repository", "")))
    if match is None:
        return [".agents/plugins/template.json: repository must be owner/name with a lowercase name"]
    kind = config.get("type")
    if kind not in STANDARD["types"]:
        return [f".agents/plugins/template.json: type must be one of {', '.join(STANDARD['types'])}"]
    namespace = match.group(1)
    problems = check_vendored(root, config["repository"], str(config.get("template")))
    problems += check_files(root)
    try:
        plugins = generator.discover(root, namespace)
    except (ValueError, json.JSONDecodeError, OSError, TypeError, AttributeError) as error:
        return problems + [str(error)]
    problems += check_agents_entries(root, set(plugins))
    problems += check_standard(root, kind, namespace, plugins)
    try:
        generated = generator.build(root)
    except (ValueError, json.JSONDecodeError, OSError, TypeError, AttributeError) as error:
        return problems + [str(error)]
    payloads_path = root / ".agents/plugins/payloads.json"
    try:
        aliases = json.loads(text(payloads_path)).get("compatibilitySkillAliases", {}) if payloads_path.is_file() else {}
    except (json.JSONDecodeError, AttributeError) as error:
        return problems + [f".agents/plugins/payloads.json: not a JSON object ({error})"]
    problems += check_names(plugins, aliases)
    problems += check_effective_dependency_projection(root, config, generated)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    root = parser.parse_args().root.resolve()
    problems = check(root)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"{root.name} does not conform to Template {new_plugin.template_version()}: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"{root.name} conforms to Template {new_plugin.template_version()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
