import importlib.util
import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
NEW_PLUGIN = ROOT / ".agents/template/utility/new-plugin/scripts/new_plugin.py"
UPDATE = ROOT / ".agents/template/utility/update/scripts/update.py"


def load(name: str, path: Path) -> Any:
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


check = load("template_check", ROOT / ".agents/template/utility/check/scripts/check.py")


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


EXTRA_ARGUMENTS = {
    "stack": ["--detect-file", "build.zig"],
    "tool": [],
    "utility": ["--skill", "sweep"],
    "profile": ["--skill", "current"],
}


@pytest.fixture
def repository_factory(tmp_path: Path) -> Callable[[str, str], Path]:
    def create(kind: str, name: str) -> Path:
        result = run(
            str(NEW_PLUGIN),
            "--repository",
            f"owner/{name}",
            "--type",
            kind,
            "--description",
            "A plugin.",
            "--destination",
            str(tmp_path),
            "--author",
            "Ada Lovelace",
            *EXTRA_ARGUMENTS[kind],
        )
        assert result.returncode == 0, result.stderr
        return tmp_path / name

    return create


@pytest.fixture
def zig_repo(repository_factory: Callable[[str, str], Path]) -> Path:
    return repository_factory("stack", "zig")


@pytest.fixture
def helix_repo(repository_factory: Callable[[str, str], Path]) -> Path:
    return repository_factory("tool", "helix")


@pytest.fixture
def tools_repo(repository_factory: Callable[[str, str], Path]) -> Path:
    return repository_factory("utility", "tools")


@pytest.fixture
def personal_repo(repository_factory: Callable[[str, str], Path]) -> Path:
    return repository_factory("profile", "personal")


def edit(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    content = path.read_text(encoding="utf-8")
    assert old in content
    path.write_text(content.replace(old, new, 1), encoding="utf-8", newline="\n")


def regenerate(root: Path) -> None:
    result = run(str(root / ".agents/sync_generated.py"), "--root", str(root))
    assert result.returncode == 0, result.stdout


def assert_problem(root: Path, fragment: str) -> None:
    problems = check.check(root)
    assert any(fragment in problem for problem in problems), problems


def test_a_new_stack_repository_conforms(zig_repo: Path) -> None:
    assert check.check(zig_repo) == []


def test_repository_can_declare_rolling_plugin_selection(zig_repo: Path) -> None:
    selection = {
        "schema_version": 1,
        "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}},
        "plugins": ["base@tj-agents", "engineering@tj-agents", "machine@tj-agents"],
    }
    (zig_repo / ".agents/plugins.json").write_text(
        json.dumps(selection), encoding="utf-8"
    )
    assert check.check(zig_repo) == []
    (zig_repo / ".agents/unexpected.json").write_text("{}", encoding="utf-8")
    assert_problem(zig_repo, ".agents/unexpected.json: not part of the plugin layout")


def test_generated_freshness_is_not_required(zig_repo: Path) -> None:
    for generated in (
        ".claude/skills",
        ".codex/skills",
        "plugins",
        ".claude-plugin/marketplace.json",
        ".agents/plugins/marketplace.json",
        ".agents/INDEX.md",
    ):
        path = zig_repo / generated
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    assert check.check(zig_repo) == []


def test_stack_generated_dependency_projection_must_match(zig_repo: Path) -> None:
    path = zig_repo / "plugins/zig/selection.json"
    selection = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(
        json.dumps({**selection, "dependencies": []}, indent=2) + "\n",
        encoding="utf-8",
    )
    assert_problem(
        zig_repo,
        "plugins/zig/selection.json: effective dependency projection is "
        "missing or differs",
    )


def test_stack_generated_dependency_projection_reports_wrong_json_shapes(
    zig_repo: Path,
) -> None:
    selection = zig_repo / "plugins/zig/selection.json"
    selection.write_text("[]\n", encoding="utf-8")
    assert_problem(
        zig_repo,
        "plugins/zig/selection.json: effective dependency projection is "
        "missing or differs",
    )

    harness = zig_repo / "plugins/zig/harness.json"
    harness.write_text("[]\n", encoding="utf-8")
    assert_problem(
        zig_repo,
        "plugins/zig/harness.json: effective dependency projection is "
        "missing or differs",
    )

    harness.write_text('{"requires": []}\n', encoding="utf-8")
    assert_problem(
        zig_repo,
        "plugins/zig/harness.json: effective dependency projection is "
        "missing or differs",
    )


def test_generator_validation_reports_invalid_payload_manifest_tier_and_reference(
    zig_repo: Path,
) -> None:
    payloads = zig_repo / ".agents/plugins/payloads.json"
    manifest = zig_repo / ".agents/plugins/manifests/codex/zig.json"
    tier = zig_repo / ".agents/tiers/zig.json"
    payloads.write_text('{"payloads": {}}\n', encoding="utf-8")
    assert_problem(zig_repo, "payloads must be a nonempty object")
    payloads.write_text('{"payloads": {"zig": ["zig"]}}\n', encoding="utf-8")
    manifest_body = manifest.read_text(encoding="utf-8")
    manifest.write_text("not JSON\n", encoding="utf-8")
    assert_problem(zig_repo, "invalid JSON")
    manifest.write_text(manifest_body, encoding="utf-8")
    tier_body = tier.read_text(encoding="utf-8")
    tier.write_text("not JSON\n", encoding="utf-8")
    assert_problem(zig_repo, "invalid JSON")
    tier.write_text(tier_body, encoding="utf-8")
    style = zig_repo / ".agents/zig/convention/style/SKILL.md"
    style.write_text(
        style.read_text(encoding="utf-8")
        + "\nRun `<skill-directory>/scripts/missing.py`.\n",
        encoding="utf-8",
    )
    assert_problem(zig_repo, "scripts/missing.py does not resolve")


def test_generator_validation_rejects_malformed_compatibility_aliases(
    zig_repo: Path,
) -> None:
    path = zig_repo / ".agents/plugins/payloads.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(
        json.dumps({**payloads, "compatibilitySkillAliases": []}), encoding="utf-8"
    )
    assert_problem(zig_repo, "compatibilitySkillAliases must be an object")
    path.write_text(
        json.dumps({**payloads, "compatibilitySkillAliases": {"zig": []}}),
        encoding="utf-8",
    )
    assert_problem(zig_repo, "invalid compatibility aliases for zig")


def test_continuation_runtime_is_allowed(zig_repo: Path) -> None:
    path = zig_repo / ".agents/continuation/owner.json"
    path.parent.mkdir()
    path.write_text("{}\n", encoding="utf-8")
    result = run(
        str(ROOT / ".agents/template/utility/check/scripts/check.py"),
        "--root",
        str(zig_repo),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_delivery_authorization_is_allowed_but_unknown_json_is_rejected(
    zig_repo: Path,
) -> None:
    (zig_repo / ".agents/delivery-authorization.json").write_text(
        "{}\n", encoding="utf-8"
    )
    assert check.check(zig_repo) == []
    (zig_repo / ".agents/delivery-authorization-local.json").write_text(
        "{}\n", encoding="utf-8"
    )
    assert_problem(zig_repo, ".agents/delivery-authorization-local.json: not part")


def test_portable_repository_plugin_configuration_is_allowed(zig_repo: Path) -> None:
    for filename in (
        "plugins.lock.json",
        "settings.json",
        "repository-harness.json",
    ):
        (zig_repo / ".agents" / filename).write_text("{}\n", encoding="utf-8")
    assert check.check(zig_repo) == []
    (zig_repo / ".agents/unknown-policy.json").write_text("{}\n", encoding="utf-8")
    assert_problem(zig_repo, ".agents/unknown-policy.json: not part")


def test_missing_required_skill(zig_repo: Path) -> None:
    for path in sorted(
        (zig_repo / ".agents/zig/convention/errors").rglob("*"), reverse=True
    ):
        path.unlink() if path.is_file() else path.rmdir()
    (zig_repo / ".agents/zig/convention/errors").rmdir()
    edit(zig_repo, ".agents/zig/policy/learning/SKILL.md", "`zig:errors`, ", "")
    assert_problem(
        zig_repo, "errors: a stack repository needs this convention skill in plugin zig"
    )


def test_missing_required_section(zig_repo: Path) -> None:
    edit(
        zig_repo,
        ".agents/zig/convention/structure/SKILL.md",
        "## File structure",
        "## Layout",
    )
    assert_problem(zig_repo, "missing section ## File structure")


def test_wrong_standard_profile(zig_repo: Path) -> None:
    edit(
        zig_repo,
        ".agents/zig/convention/style/SKILL.md",
        "profile: core",
        "profile: contract",
    )
    assert_problem(zig_repo, "style is kind convention, profile core")


def test_convention_without_owns_line(zig_repo: Path) -> None:
    edit(
        zig_repo,
        ".agents/zig/convention/build/SKILL.md",
        "Owns the toolchain pin",
        "Covers the toolchain pin",
    )
    assert_problem(zig_repo, "opens with an `Owns")


def test_legacy_kinds_still_satisfy_the_standard(zig_repo: Path) -> None:
    convention = zig_repo / ".agents/zig/convention/style"
    legacy = zig_repo / ".agents/zig/contract/style"
    legacy.parent.mkdir(parents=True)
    convention.rename(legacy)
    edit(
        zig_repo,
        ".agents/zig/contract/style/SKILL.md",
        "kind: convention",
        "kind: contract",
    )
    policy = zig_repo / ".agents/zig/policy/learning"
    legacy_learning = zig_repo / ".agents/zig/knowledge/learning"
    legacy_learning.parent.mkdir(parents=True, exist_ok=True)
    policy.rename(legacy_learning)
    edit(
        zig_repo,
        ".agents/zig/knowledge/learning/SKILL.md",
        "kind: policy",
        "kind: knowledge",
    )
    assert check.check(zig_repo) == []


def test_drifted_vendored_file(zig_repo: Path) -> None:
    edit(zig_repo, ".gitignore", ".worktrees/\n", ".worktrees/\nlocal/\n")
    assert_problem(zig_repo, ".gitignore: differs from current Template")


def test_legacy_config_pin_is_rejected(zig_repo: Path) -> None:
    path = zig_repo / ".agents/plugins/template.json"
    path.write_text(
        json.dumps({**json.loads(path.read_text()), "template": "0.9.0"}),
        encoding="utf-8",
    )
    assert_problem(zig_repo, "unknown fields ['template']")


def test_retired_and_unknown_entries(zig_repo: Path) -> None:
    (zig_repo / "SOURCE_LAYOUT.md").write_text("old\n", encoding="utf-8")
    (zig_repo / ".agents/plugins/sources.json").write_text("{}\n", encoding="utf-8")
    (zig_repo / ".agents/notes.md").write_text("notes\n", encoding="utf-8")
    problems = "\n".join(check.check(zig_repo))
    for fragment in (
        "SOURCE_LAYOUT.md: retired",
        ".agents/plugins/sources.json: retired",
        ".agents/notes.md: not part",
    ):
        assert fragment in problems
    (zig_repo / ".agents/docs").mkdir()
    problems = "\n".join(check.check(zig_repo))
    assert "SOURCE_LAYOUT.md: retired" in problems
    assert ".agents/docs: a plugin folder needs at least one skill" in problems


def test_ci_layout_still_compares_the_ci_caller(zig_repo: Path) -> None:
    nested = zig_repo / ".template/.agents/template"
    shutil.copytree(ROOT / ".agents/template", nested)
    edit(
        zig_repo,
        ".github/workflows/ci.yml",
        "template_ref: main",
        "template_ref: v0.9.0",
    )
    result = run(
        str(nested / "utility/check/scripts/check.py"), "--root", str(zig_repo)
    )
    assert result.returncode == 1
    assert ".github/workflows/ci.yml: differs from current Template" in result.stderr


def test_missing_tier_is_reported(zig_repo: Path) -> None:
    (zig_repo / ".agents/tiers/zig.json").unlink()
    assert_problem(zig_repo, ".agents/tiers/zig.json: required")


def test_stack_tier_must_detect_its_stack(zig_repo: Path) -> None:
    path = zig_repo / ".agents/tiers/zig.json"
    tier = json.loads(path.read_text())
    tier.pop("detect")
    path.write_text(
        json.dumps({**tier, "applies": "always"}, indent=2) + "\n", encoding="utf-8"
    )
    assert_problem(zig_repo, "a stack repository applies stack-present")


def test_update_restores_vendored_files_and_removes_legacy_versions(
    zig_repo: Path,
) -> None:
    edit(zig_repo, ".gitignore", ".worktrees/\n", ".worktrees/\nlocal/\n")
    path = zig_repo / ".agents/plugins/template.json"
    path.write_text(
        json.dumps({**json.loads(path.read_text()), "template": "0.9.0"}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    manifest_paths = [
        zig_repo / f".agents/plugins/manifests/{host}/zig.json"
        for host in ("claude", "codex")
    ]
    for manifest_path in manifest_paths:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] = "0.1.0"
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    dry = run(str(UPDATE), "--root", str(zig_repo), "--dry-run")
    assert "would update .gitignore" in dry.stdout
    assert "would update .agents/plugins/template.json" in dry.stdout
    for host in ("claude", "codex"):
        assert f"would update .agents/plugins/manifests/{host}/zig.json" in dry.stdout
    assert "local/" in (zig_repo / ".gitignore").read_text()
    assert "template" in json.loads(path.read_text(encoding="utf-8"))
    for manifest_path in manifest_paths:
        assert "version" in json.loads(manifest_path.read_text(encoding="utf-8"))
    result = run(str(UPDATE), "--root", str(zig_repo))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "updated .agents/plugins/template.json" in result.stdout
    assert check.check(zig_repo) == []
    assert "template" not in json.loads(path.read_text(encoding="utf-8"))
    for manifest_path in manifest_paths:
        assert "version" not in json.loads(manifest_path.read_text(encoding="utf-8"))
    rerun = run(str(UPDATE), "--root", str(zig_repo))
    assert rerun.returncode == 0, rerun.stdout + rerun.stderr
    assert "already current" in rerun.stdout


def test_update_rejects_missing_template_pin(zig_repo: Path) -> None:
    (zig_repo / ".agents/plugins/template.json").unlink()
    result = run(str(UPDATE), "--root", str(zig_repo))
    assert result.returncode == 2
    assert "template.json: missing" in result.stderr


def test_a_new_tool_repository_conforms(helix_repo: Path) -> None:
    assert check.check(helix_repo) == []


def test_learning_keeps_its_calibrate_section(helix_repo: Path) -> None:
    edit(
        helix_repo,
        ".agents/helix/policy/learning/SKILL.md",
        "## Calibrate to `helix:knowledge`",
        "## Calibrate",
    )
    assert_problem(helix_repo, "missing section ## Calibrate to `helix:knowledge`")


def test_utility_can_explicitly_gate_on_stack_present(tools_repo: Path) -> None:
    path = tools_repo / ".agents/tiers/tools.json"
    tier = json.loads(path.read_text())
    tier.update(schema_version=3, applies="stack-present", detect={"fact": "employer"})
    path.write_text(json.dumps(tier), encoding="utf-8")
    assert check.check(tools_repo) == []


def test_utility_rejects_unsupported_applies(tools_repo: Path) -> None:
    path = tools_repo / ".agents/tiers/tools.json"
    tier = json.loads(path.read_text())
    tier["applies"] = "sometimes"
    path.write_text(json.dumps(tier), encoding="utf-8")
    assert_problem(tools_repo, "a utility repository applies")


def test_a_new_utility_repository_conforms(tools_repo: Path) -> None:
    assert check.check(tools_repo) == []


def test_only_utility_skills(tools_repo: Path) -> None:
    skill = tools_repo / ".agents/tools/knowledge/notes/SKILL.md"
    skill.parent.mkdir(parents=True)
    text = (tools_repo / ".agents/tools/utility/sweep/SKILL.md").read_text(
        encoding="utf-8"
    )
    skill.write_text(
        text.replace("name: sweep", "name: notes").replace(
            "kind: utility", "kind: knowledge"
        ),
        encoding="utf-8",
    )
    regenerate(tools_repo)
    assert_problem(tools_repo, "a utility repository has only utility skills")


def test_a_new_profile_conforms(personal_repo: Path) -> None:
    assert check.check(personal_repo) == []


def test_profile_needs_a_policy_in_its_main_plugin(personal_repo: Path) -> None:
    policy = personal_repo / ".agents/personal/policy/current"
    utility = personal_repo / ".agents/personal/utility/current"
    utility.parent.mkdir()
    policy.rename(utility)
    policy.parent.rmdir()
    edit(
        personal_repo,
        ".agents/personal/utility/current/SKILL.md",
        "kind: policy",
        "kind: utility",
    )
    regenerate(personal_repo)
    assert_problem(
        personal_repo, "a profile repository needs at least one policy skill"
    )


def test_profile_rejects_knowledge_kind(personal_repo: Path) -> None:
    policy = personal_repo / ".agents/personal/policy/current"
    knowledge = personal_repo / ".agents/personal/knowledge/current"
    knowledge.parent.mkdir()
    policy.rename(knowledge)
    policy.parent.rmdir()
    edit(
        personal_repo,
        ".agents/personal/knowledge/current/SKILL.md",
        "kind: policy",
        "kind: knowledge",
    )
    regenerate(personal_repo)
    assert_problem(
        personal_repo,
        "a profile repository has only policy, convention, workflow, utility skills",
    )


def test_profile_is_always_applicable_once_selected(personal_repo: Path) -> None:
    path = personal_repo / ".agents/tiers/personal.json"
    tier = json.loads(path.read_text())
    tier.update(applies="stack-present", detect={"files": ["personal.json"]})
    path.write_text(json.dumps(tier), encoding="utf-8")
    assert_problem(personal_repo, "a profile repository applies always")


def test_profile_dependency_projection_is_checked(personal_repo: Path) -> None:
    path = personal_repo / "plugins/personal/harness.json"
    harness = json.loads(path.read_text())
    harness["requires"]["plugins"] = ["personal-agents/personal"]
    path.write_text(json.dumps(harness), encoding="utf-8")
    assert_problem(
        personal_repo,
        "plugins/personal/harness.json: effective dependency projection is "
        "missing or differs",
    )


def test_a_conforming_scaffold_in_one_plugin_is_enough(zig_repo: Path) -> None:
    extra = zig_repo / ".agents/extra"
    scaffold = (zig_repo / ".agents/zig/utility/scaffold/SKILL.md").read_text(
        encoding="utf-8"
    )
    (extra / "utility/scaffold").mkdir(parents=True)
    broken = scaffold.replace("## Build and adapt\n", "")
    (extra / "utility/scaffold/SKILL.md").write_text(broken, encoding="utf-8")
    tier = json.loads((zig_repo / ".agents/tiers/zig.json").read_text())
    (zig_repo / ".agents/tiers/extra.json").write_text(
        json.dumps({**tier, "tier": "extra"}), encoding="utf-8"
    )
    for host in ("claude", "codex"):
        source = json.loads(
            (zig_repo / f".agents/plugins/manifests/{host}/zig.json").read_text()
        )
        (zig_repo / f".agents/plugins/manifests/{host}/extra.json").write_text(
            json.dumps({**source, "name": "extra"}), encoding="utf-8"
        )
    payloads = {"payloads": {"zig": ["zig"], "extra": ["extra"]}}
    (zig_repo / ".agents/plugins/payloads.json").write_text(
        json.dumps(payloads), encoding="utf-8"
    )
    regenerate(zig_repo)
    assert check.check(zig_repo) == []


def add_contract(root: Path, folder: str, name: str) -> None:
    skill = root / ".agents/zig/contract" / folder / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(
        f"---\nname: {name}\ndescription: The {name} contract.\nkind: contract\n"
        f"domain: zig\nprofile: core\n"
        f"applicability: zig projects\nrequires: zig\nprovenance: house\n---\n\n"
        f"# {name}\n\nOwns {name}.\n",
        encoding="utf-8",
        newline="\n",
    )


def test_a_family_folder_conforms(zig_repo: Path) -> None:
    add_contract(zig_repo, "state", "state")
    add_contract(zig_repo, "state/client", "state-client")
    add_contract(zig_repo, "state/server", "state-server")
    assert check.check(zig_repo) == []


def test_flat_names_sharing_a_word_belong_in_a_family(zig_repo: Path) -> None:
    add_contract(zig_repo, "client-state", "client-state")
    add_contract(zig_repo, "server-state", "server-state")
    assert_problem(
        zig_repo,
        "client-state, server-state share `state`; fold them into the family "
        "folder state/<member>/",
    )


def test_a_flat_name_sharing_a_family_word(zig_repo: Path) -> None:
    add_contract(zig_repo, "state/client", "state-client")
    add_contract(zig_repo, "server-state", "server-state")
    assert_problem(zig_repo, "server-state share `state`")


def test_a_member_repeating_its_family(zig_repo: Path) -> None:
    add_contract(zig_repo, "state/client-state", "state-client-state")
    assert_problem(zig_repo, "client-state repeats its family state")


def test_a_name_repeating_its_namespace(zig_repo: Path) -> None:
    add_contract(zig_repo, "zig-rules", "zig-rules")
    assert_problem(zig_repo, "a skill name does not repeat its namespace zig")


def test_malformed_payloads_is_reported(zig_repo: Path) -> None:
    (zig_repo / ".agents/plugins/payloads.json").write_text(
        "<<<<<<< ours\n", encoding="utf-8"
    )
    assert_problem(zig_repo, ".agents/plugins/payloads.json: invalid JSON")


def test_a_compatibility_alias_keeps_its_old_name(zig_repo: Path) -> None:
    add_contract(zig_repo, "zig-style", "zig-style")
    path = zig_repo / ".agents/plugins/payloads.json"
    payloads = json.loads(path.read_text())
    payloads["compatibilitySkillAliases"] = {
        "zig": {"zig-style": {"replacedBy": "zig:style", "removeAfter": "2027-03-31"}}
    }
    path.write_text(json.dumps(payloads), encoding="utf-8")
    assert check.check(zig_repo) == []


def test_template_conforms_to_itself() -> None:
    assert check.check(ROOT) == []


def test_template_conforms_when_checked_from_a_nested_copy(tmp_path: Path) -> None:
    nested = tmp_path / ".agents/template"
    shutil.copytree(ROOT / ".agents/template", nested)
    result = run(str(nested / "utility/check/scripts/check.py"), "--root", str(ROOT))
    assert result.returncode == 0, result.stderr
