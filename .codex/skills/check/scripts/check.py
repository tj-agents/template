#!/usr/bin/env python3
"""Check a plugin repository against Template's layout and standard."""

import argparse
import importlib.util
import json
import subprocess
import sys
from collections.abc import Iterator
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any, TypedDict

from tj_template.plugins import generation as generator

sys.dont_write_bytecode = True

SKILL_DIRECTORY = Path(__file__).resolve().parents[1]
NEW_PLUGIN = SKILL_DIRECTORY.parent / "new/plugin"
if not NEW_PLUGIN.is_dir():
    NEW_PLUGIN = SKILL_DIRECTORY.parent / "new-plugin"
STANDARD = json.loads((SKILL_DIRECTORY / "standard.json").read_text(encoding="utf-8"))

type JSONObject = dict[str, Any]

IDENTITY_FILES = (
    ".agents/plugins/payloads.json",
    ".agents/plugins/manifests/*/*.json",
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    "plugins/*/harness.json",
    "plugins/*/selection.json",
    "plugins/*/.claude-plugin/plugin.json",
    "plugins/*/.codex-plugin/plugin.json",
)
IDENTITY_FIELDS = {"plugin", "plugins", "dependencies"}


class SkillRecord(TypedDict):
    plugin: str
    name: str
    kind: str
    body: str
    metadata: dict[str, str]
    directory: str
    files: list[str]


type PluginSkills = dict[str, SkillRecord]
type Plugins = dict[str, PluginSkills]


def load_module(name: str, path: Path) -> Any:
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


new_plugin = load_module("template_new_plugin", NEW_PLUGIN / "scripts/new_plugin.py")
examples = load_module(
    "template_check_examples", SKILL_DIRECTORY / "scripts/check_examples.py"
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def git_output(root: Path, *arguments: str) -> bytes | None:
    result = subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, check=False
    )
    return result.stdout if result.returncode == 0 else None


def skill_example_paths(
    root: Path, plugins: Plugins | None, base: str | None, head: str, merge_base: bool
) -> tuple[set[Path], bool]:
    top_level = git_output(root, "rev-parse", "--show-toplevel")
    owns_repository = (
        top_level is not None
        and Path(top_level.decode("utf-8").strip()).resolve() == root
    )
    if base is not None:
        if not owns_repository:
            raise ValueError(
                "an explicit --base range requires --root to be a Git repository root"
            )
        try:
            changed_paths = examples.changed_paths(root, base, head, merge_base)
        except examples.CheckError as error:
            raise ValueError(str(error)) from error
        return {
            root.joinpath(*path.parts)
            for path in changed_paths
            if path.name == "SKILL.md" and examples.is_authored_guidance(path)
        }, True

    assert plugins is not None
    records = {
        root / skill["directory"] / "SKILL.md"
        for skills in plugins.values()
        for skill in skills.values()
    }
    current = git_output(root, "rev-parse", "--verify", "HEAD^{commit}")
    if current is None or not owns_repository:
        return records, False

    changed_bytes = git_output(root, "diff", "--name-only", "-z", "HEAD") or b""
    changed_bytes += (
        git_output(root, "ls-files", "--others", "--exclude-standard", "-z") or b""
    )
    merge_base_ref = git_output(root, "merge-base", "HEAD", "origin/main")
    if merge_base_ref is not None:
        try:
            changed_bytes += b"\0".join(
                path.as_posix().encode("utf-8")
                for path in examples.changed_paths(
                    root, merge_base_ref.decode("utf-8").strip(), "HEAD"
                )
            )
        except examples.CheckError as error:
            raise ValueError(str(error)) from error
    paths = {
        root / Path(raw.decode("utf-8", errors="surrogateescape"))
        for raw in changed_bytes.split(b"\0")
        if raw
    }
    return records.intersection(paths), False


def check_skill_examples(
    root: Path,
    plugins: Plugins | None,
    base: str | None,
    head: str,
    merge_base: bool,
) -> list[str]:
    if not STANDARD["skill_content"]["requires_concrete_fenced_example"]:
        return []
    if base is not None:
        try:
            head = examples.commit(root, head, "--head")
        except examples.CheckError as error:
            raise ValueError(str(error)) from error
    paths, committed = skill_example_paths(root, plugins, base, head, merge_base)
    problems = []
    for path in sorted(paths):
        try:
            content = (
                examples.committed_text(
                    root,
                    head,
                    examples.normalized_path(path.relative_to(root).as_posix()),
                )
                if committed
                else text(path)
            )
        except (examples.CheckError, OSError, UnicodeDecodeError) as error:
            problems.append(
                f"{path.relative_to(root).as_posix()}: cannot read skill ({error})"
            )
            continue
        if not examples.has_concrete_example(content):
            problems.append(
                f"{path.relative_to(root).as_posix()}: add a concrete "
                "non-placeholder fenced example"
            )
    return problems


def owns_templates(root: Path) -> bool:
    return (root / ".agents/template/utility/new/plugin/templates/repository").is_dir()


def check_vendored(root: Path, repository: str) -> list[str]:
    problems = []
    for relative, expected in new_plugin.vendored_files(repository).items():
        if relative == ".github/workflows/ci.yml" and owns_templates(root):
            continue
        path = root / relative
        if not path.is_file():
            problems.append(f"{relative}: missing; run update")
        elif text(path) != expected:
            problems.append(
                f"{relative}: differs from current Template; change it in "
                "the source repository, then run update"
            )
    return problems


def check_files(root: Path) -> list[str]:
    problems = [
        f"{name}: required"
        for name in STANDARD["root_files"]
        if not (root / name).is_file()
    ]
    problems += [
        f"{name}: retired; Template documents the layout"
        for name in STANDARD["retired_files"]
        if (root / name).exists()
    ]
    plugins_root = root / ".agents/plugins"
    if not plugins_root.is_dir():
        return [*problems, ".agents/plugins: required"]
    for entry in sorted(plugins_root.iterdir()):
        retired = f".agents/plugins/{entry.name}" in STANDARD["retired_files"]
        if entry.name not in STANDARD["plugins_entries"] and not retired:
            problems.append(
                f".agents/plugins/{entry.name}: not part of the plugin layout"
            )
    return problems


def check_agents_entries(root: Path, plugins: set[str]) -> list[str]:
    problems = []
    agents_root = root / ".agents"
    if not agents_root.is_dir():
        return [".agents: required"]
    for entry in sorted(agents_root.iterdir()):
        if entry.name == "__pycache__":
            continue
        allowed = (
            STANDARD["agents_folders"] + sorted(plugins)
            if entry.is_dir()
            else STANDARD["agents_files"]
        )
        if entry.name not in allowed:
            problems.append(f".agents/{entry.name}: not part of the plugin layout")
    return problems


def headings(body: str) -> set[str]:
    return {line.rstrip() for line in body.splitlines() if line.startswith("## ")}


def opening(body: str) -> str:
    match = generator.FRONTMATTER.match(body)
    assert match is not None
    lines = match.group("body").splitlines()
    after_title = False
    for line in lines:
        if line.startswith("# "):
            after_title = True
        elif after_title and line.strip():
            return line
    return ""


def skill_problems(
    skill: SkillRecord, name: str, rule: JSONObject, namespace: str
) -> list[str]:
    problems = []
    allowed_kinds = {rule["kind"], *rule.get("legacy_kinds", [])}
    if (
        skill["kind"] not in allowed_kinds
        or skill["metadata"]["profile"] != rule["profile"]
    ):
        problems.append(
            f"{skill['directory']}: {name} is kind {rule['kind']}, "
            f"profile {rule['profile']}"
        )
    present = headings(skill["body"])
    for heading in rule["sections"]:
        heading = heading.replace("{namespace}", namespace)
        if heading not in present:
            problems.append(f"{skill['directory']}/SKILL.md: missing section {heading}")
    return problems


def check_standard(
    root: Path, kind: str, namespace: str, plugins: Plugins
) -> list[str]:
    standard = STANDARD["types"][kind]
    problems = []
    if namespace not in plugins:
        return [
            f".agents/{namespace}: a repository's main plugin folder is "
            "named after the repository"
        ]
    tier_path = root / f".agents/tiers/{namespace}.json"
    if not tier_path.is_file():
        problems.append(f".agents/tiers/{namespace}.json: required")
    else:
        try:
            applies = json.loads(text(tier_path)).get("applies")
        except (json.JSONDecodeError, AttributeError) as error:
            problems.append(
                f".agents/tiers/{namespace}.json: not a JSON object ({error})"
            )
        else:
            if applies not in (
                standard["applies"]
                if isinstance(standard["applies"], list)
                else [standard["applies"]]
            ):
                problems.append(
                    f".agents/tiers/{namespace}.json: a {kind} repository "
                    f"applies {standard['applies']}"
                )
    for required_kind in standard.get("required_kinds", []):
        if not any(
            skill["kind"] == required_kind for skill in plugins[namespace].values()
        ):
            problems.append(
                f"plugin {namespace}: a {kind} repository needs at least "
                f"one {required_kind} skill"
            )
    for name, rule in standard["skills"].items():
        owners = plugins.values() if rule.get("anywhere") else [plugins[namespace]]
        candidates = [skills[name] for skills in owners if name in skills]
        if not candidates:
            where = "any plugin" if rule.get("anywhere") else f"plugin {namespace}"
            problems.append(
                f"{name}: a {kind} repository needs this {rule['kind']} "
                f"skill in {where}"
            )
            continue
        found = [skill_problems(skill, name, rule, namespace) for skill in candidates]
        if all(found):
            problems += [problem for skill_found in found for problem in skill_found]
    for skills in plugins.values():
        for skill in skills.values():
            if "only_kinds" in standard and skill["kind"] not in standard["only_kinds"]:
                allowed = ", ".join(standard["only_kinds"])
                problems.append(
                    f"{skill['directory']}: a {kind} repository has only "
                    f"{allowed} skills"
                )
            if skill["kind"] in ("contract", "convention") and not opening(
                skill["body"]
            ).startswith(STANDARD["convention_opening"]):
                problems.append(
                    f"{skill['directory']}/SKILL.md: a contract opens with "
                    "an `Owns …` line after its title"
                )
    return problems


def check_names(plugins: Plugins, aliases: dict[str, JSONObject]) -> list[str]:
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
                problems.append(
                    f"{skill['directory']}: a skill name does not repeat "
                    f"its namespace {plugin}"
                )
            for index, part in enumerate(parts[1:], 1):
                for family in parts[:index]:
                    if (
                        part == family
                        or part.startswith(f"{family}-")
                        or part.endswith(f"-{family}")
                    ):
                        problems.append(
                            f"{skill['directory']}: {part} repeats its family {family}"
                        )
            if len(parts) > 1:
                families.add((skill["kind"], parts[0]))
            elif "-" in parts[0]:
                words = parts[0].split("-")
                for word in {words[0], words[-1]}:
                    flat.setdefault((skill["kind"], word), set()).add(parts[0])
        for (kind, word), names in sorted(flat.items()):
            if len(names) > 1 or (kind, word) in families:
                sharing = ", ".join(sorted(names))
                problems.append(
                    f".agents/{plugin}/{kind}: {sharing} share `{word}`; fold "
                    f"them into the family folder {word}/<member>/"
                )
    return problems


def marketplace_references(value: Any, field: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            if (field == "marketplaces" and key == "id") or key == "marketplace":
                yield key, str(item)
            else:
                nested = field if field == "dependencies" else key
                yield from marketplace_references(item, nested)
    elif isinstance(value, list):
        for item in value:
            yield from marketplace_references(item, field)
    elif isinstance(value, str):
        if field == "allowCrossMarketplaceDependenciesOn":
            yield field, value
        elif field in IDENTITY_FIELDS and "@" in value:
            yield field, value.rsplit("@", 1)[1]
        elif field in IDENTITY_FIELDS and "/" in value:
            yield field, value.split("/", 1)[0]


def check_marketplace_identity(root: Path) -> list[str]:
    marketplace = generator.TJ_AGENTS_MARKETPLACE
    problems = []
    paths = sorted({path for pattern in IDENTITY_FILES for path in root.glob(pattern)})
    for path in paths:
        relative = path.relative_to(root).as_posix()
        try:
            document = json.loads(text(path))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        found = list(marketplace_references(document))
        named = isinstance(document, dict) and "name" in document
        if path.name == "marketplace.json" and named:
            found.append(("name", str(document["name"])))
        problems += [
            f"{relative}: {field} uses marketplace {name}; {marketplace} is "
            "the only marketplace"
            for field, name in found
            if name != marketplace
        ]
    return problems


def check_effective_dependency_projection(
    root: Path, config: JSONObject, generated: dict[str, bytes]
) -> list[str]:
    if config["type"] not in ("stack", "profile"):
        return []
    paths = [
        path
        for path in generated
        if path == ".claude-plugin/marketplace.json"
        or path.endswith(
            ("/selection.json", "/harness.json", "/.claude-plugin/plugin.json")
        )
    ]
    present = [path for path in paths if (root / path).is_file()]
    if not present:
        return []
    problems = []
    for path in paths:
        actual = root / path
        if not actual.is_file():
            problems.append(
                f"{path}: effective dependency projection is missing or differs"
            )
            continue
        try:
            expected = json.loads(generated[path])
            observed = json.loads(text(actual))
        except (json.JSONDecodeError, UnicodeDecodeError):
            problems.append(
                f"{path}: effective dependency projection is missing or differs"
            )
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
                and observed_requires.get("marketplaces")
                == expected_requires.get("marketplaces")
            )
        elif path.endswith("/.claude-plugin/plugin.json"):
            matches = observed.get("dependencies") == expected.get("dependencies")
        else:
            matches = observed.get(
                "allowCrossMarketplaceDependenciesOn"
            ) == expected.get("allowCrossMarketplaceDependenciesOn")
        if not matches:
            problems.append(
                f"{path}: effective dependency projection is missing or differs"
            )
    return problems


def check_adoption(root: Path) -> list[str]:
    """Observe declaration drift; Core owns schema and native settings validation."""
    relative = ".agents/plugins.json"
    try:
        selection = json.loads(text(root / relative))
    except (OSError, ValueError) as error:
        return [f"{relative}: Template selection is required ({error})"]
    plugins = selection.get("plugins") if isinstance(selection, dict) else None
    if not isinstance(plugins, list) or "template@tj-agents" not in plugins:
        return [f"{relative}: select template@tj-agents through agent:plugins"]
    return []


def check(
    root: Path,
    base: str | None = None,
    head: str = "HEAD",
    merge_base: bool = False,
) -> list[str]:
    config_path = root / ".agents/plugins/template.json"
    if not config_path.is_file():
        return [
            ".agents/plugins/template.json: missing; this is not a Template "
            "plugin repository"
        ]
    try:
        config = json.loads(text(config_path))
    except json.JSONDecodeError as error:
        return [f".agents/plugins/template.json: invalid JSON ({error})"]
    if not isinstance(config, dict):
        return [".agents/plugins/template.json: must be a JSON object"]
    match = generator.REPOSITORY.fullmatch(str(config.get("repository", "")))
    if match is None:
        return [
            ".agents/plugins/template.json: repository must be owner/name "
            "with a lowercase name"
        ]
    kind = config.get("type")
    if kind not in STANDARD["types"]:
        standard_types = ", ".join(STANDARD["types"])
        return [f".agents/plugins/template.json: type must be one of {standard_types}"]
    assert isinstance(kind, str)
    namespace = match.group(1)
    problems = check_vendored(root, config["repository"])
    problems += check_files(root)
    problems += check_marketplace_identity(root)
    try:
        payloads = generator.load(root / ".agents/plugins/payloads.json")
        plugins = generator.discover(
            root, namespace, generator.mapped_resource_directories(payloads)
        )
    except (
        ValueError,
        json.JSONDecodeError,
        OSError,
        TypeError,
        AttributeError,
    ) as error:
        if base is not None:
            try:
                problems += check_skill_examples(root, None, base, head, merge_base)
            except ValueError as example_error:
                problems.append(f"skill examples: {example_error}")
        return [*problems, str(error)]
    problems += check_agents_entries(root, set(plugins))
    problems += check_standard(root, kind, namespace, plugins)
    try:
        generated = generator.build(root)
    except (
        ValueError,
        json.JSONDecodeError,
        OSError,
        TypeError,
        AttributeError,
    ) as error:
        return [*problems, str(error)]
    payloads_path = root / ".agents/plugins/payloads.json"
    try:
        aliases = (
            json.loads(text(payloads_path)).get("compatibilitySkillAliases", {})
            if payloads_path.is_file()
            else {}
        )
    except (json.JSONDecodeError, AttributeError) as error:
        return [
            *problems,
            f".agents/plugins/payloads.json: not a JSON object ({error})",
        ]
    problems += check_names(plugins, aliases)
    problems += check_effective_dependency_projection(root, config, generated)
    try:
        problems += check_skill_examples(root, plugins, base, head, merge_base)
    except ValueError as error:
        problems.append(f"skill examples: {error}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--adoption",
        action="store_true",
        help="Check Template selection only, including non-plugin coding repositories",
    )
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--merge-base", action="store_true")
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    problems = (
        check_adoption(root)
        if arguments.adoption
        else check(root, arguments.base, arguments.head, arguments.merge_base)
    )
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(
            f"{root.name} does not conform to Template: {len(problems)} problem(s)",
            file=sys.stderr,
        )
        return 1
    print(f"{root.name} conforms to Template")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
