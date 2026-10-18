import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents/template/utility/new-plugin"
SCRIPT = SKILL / "scripts/new_plugin.py"
TEMPLATES = SKILL / "templates/repository"
CORE_PAYLOAD_CHECK = ROOT / ".core/plugins/base/hooks/check_tier_payload.py"
CORE_EXAMPLES_CHECK = (
    ROOT
    / ".core/.agents/engineering/convention/docs/scripts/check_examples.py"
)
PLACEHOLDER = re.compile(r"\{\{[A-Za-z_]+\}\}")
VENDORED = (
    ".agents/sync_generated.py",
    ".agents/sync-generated.ps1",
    ".gitattributes",
    ".gitignore",
    "CLAUDE.md",
)
STACK_SKILLS = {
    "knowledge": {"knowledge", "direction"},
    "policy": {"learning"},
    "convention": {
        "style",
        "structure",
        "domain-design",
        "errors",
        "testing",
        "build",
        "libraries",
    },
    "utility": {"scaffold"},
}


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def create(
    destination: Path, name: str, kind: str, *extra: str
) -> subprocess.CompletedProcess[str]:
    return run(
        str(SCRIPT),
        "--repository",
        f"owner/{name}",
        "--type",
        kind,
        "--description",
        f"The {name} plugin.",
        "--destination",
        str(destination),
        "--author",
        "Ada Lovelace",
        *extra,
    )


def skills(destination: Path, name: str) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for path in (destination / name / ".agents" / name).glob("*/*/SKILL.md"):
        found.setdefault(path.parent.parent.name, set()).add(path.parent.name)
    return found


def assert_repository_is_current(destination: Path, name: str) -> None:
    repository = destination / name
    harness = json.loads(
        (repository / f"plugins/{name}/harness.json").read_text(encoding="utf-8")
    )
    marketplaces = {entry["id"] for entry in harness["requires"]["marketplaces"]}
    assert harness["plugin"] == f"{name}-agents/{name}"
    plugins = harness["requires"]["plugins"]
    if "tj-agents/base" in plugins:
        selection = json.loads(
            (repository / f"plugins/{name}/selection.json").read_text(encoding="utf-8")
        )
        kind = json.loads((repository / ".agents/plugins/template.json").read_text())[
            "type"
        ]
        dependencies = (
            ["tj-agents/base"]
            if kind == "profile"
            else ["tj-agents/base", "tj-agents/engineering", "tj-agents/machine"]
        )
        assert plugins == [f"{name}-agents/{name}", *dependencies]
        assert selection["dependencies"] == dependencies
        claude = json.loads(
            (repository / f"plugins/{name}/.claude-plugin/plugin.json").read_text(
                encoding="utf-8"
            )
        )
        assert claude["dependencies"] == [
            f"{identity.split('/')[1]}@{identity.split('/')[0]}"
            for identity in dependencies
        ]
        marketplace = json.loads(
            (repository / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
        )
        assert marketplace["allowCrossMarketplaceDependenciesOn"] == ["tj-agents"]
    else:
        assert plugins == [f"{name}-agents/{name}", "base-agents/base"]
    assert all(
        identity.split("/")[0] in marketplaces
        for identity in [harness["plugin"], *harness["requires"]["plugins"]]
    )
    for source in (repository / ".agents" / name).rglob("SKILL.md"):
        skill_name = next(
            line.removeprefix("name: ")
            for line in source.read_text(encoding="utf-8").splitlines()
            if line.startswith("name: ")
        )
        canonical = repository / "plugins" / name / source.relative_to(repository)
        adapter = repository / "plugins" / name / "skills" / skill_name / "SKILL.md"
        assert source.read_bytes() == canonical.read_bytes(), canonical
        relative = os.path.relpath(canonical, adapter.parent).replace("\\", "/")
        assert f"canonical definition]({relative})" in adapter.read_text(
            encoding="utf-8"
        ), adapter
        assert adapter.is_file()
    result = run(
        str(repository / ".agents/sync_generated.py"),
        "--root",
        str(repository),
        "--check",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for path in repository.rglob("*"):
        if path.is_file():
            assert PLACEHOLDER.findall(path.read_text(encoding="utf-8")) == [], path
    if CORE_PAYLOAD_CHECK.is_file():
        result = run(str(CORE_PAYLOAD_CHECK), "--root", str(repository))
        assert result.returncode == 0, result.stdout + result.stderr


def test_stack_repository_has_the_standard_skills_and_a_detected_tier(
    tmp_path: Path,
) -> None:
    result = create(
        tmp_path,
        "zig",
        "stack",
        "--stack",
        "Zig",
        "--detect-file",
        "build.zig",
        "--detect-glob",
        "*.zig",
    )
    assert result.returncode == 0, result.stderr
    assert skills(tmp_path, "zig") == STACK_SKILLS
    tier = (tmp_path / "zig/.agents/tiers/zig.json").read_text(encoding="utf-8")
    assert '"applies": "stack-present"' in tier
    assert "build.zig" in tier
    structure = (tmp_path / "zig/.agents/zig/convention/structure/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "## File structure" in structure
    assert "Ada's agreed Zig project structure" in structure
    assert_repository_is_current(tmp_path, "zig")


def test_tool_repository_has_only_the_knowledge_tier(tmp_path: Path) -> None:
    assert create(tmp_path, "helix", "tool").returncode == 0
    assert skills(tmp_path, "helix") == {
        "knowledge": {"knowledge", "direction"},
        "policy": {"learning"},
    }
    assert (
        '"applies": "always"'
        in (tmp_path / "helix/.agents/tiers/helix.json").read_text()
    )
    assert_repository_is_current(tmp_path, "helix")


def test_utility_repository_has_only_its_utility(tmp_path: Path) -> None:
    assert create(tmp_path, "tools", "utility", "--skill", "sweep").returncode == 0
    assert skills(tmp_path, "tools") == {"utility": {"sweep"}}
    assert_repository_is_current(tmp_path, "tools")


def test_generated_starter_requires_a_concrete_example_when_core_is_available(
    tmp_path: Path,
) -> None:
    if not CORE_EXAMPLES_CHECK.is_file():
        pytest.skip("Core guidance-example checker is supplied by reusable CI")

    assert create(tmp_path, "tools", "utility", "--skill", "sweep").returncode == 0
    repository = tmp_path / "tools"
    relative = ".agents/tools/utility/sweep/SKILL.md"

    result = run(
        str(CORE_EXAMPLES_CHECK),
        "--root",
        str(repository),
        "--path",
        relative,
    )

    assert result.returncode == 1
    assert relative in result.stderr.replace("\\", "/")


def test_initial_plugin_passes_the_zero_base_check_after_real_examples_are_added(
    tmp_path: Path,
) -> None:
    if not CORE_EXAMPLES_CHECK.is_file():
        pytest.skip("Core guidance-example checker is supplied by reusable CI")

    assert create(tmp_path, "tools", "utility", "--skill", "sweep").returncode == 0
    repository = tmp_path / "tools"
    skill = repository / ".agents/tools/utility/sweep/SKILL.md"
    skill.write_text(
        """---
name: sweep
description: Lists stale build outputs before removing them.
kind: utility
domain: tools
profile: core
applicability: build cleanup
requires: tools
provenance: house
---

# Sweep

Lists stale build outputs before removing them.

## Example

```text
input: [\"artifacts/old.bin\"]
output: [\"artifacts/old.bin\"]
```
""",
        encoding="utf-8",
    )
    for arguments in (
        ("init",),
        ("add", "."),
        ("-c", "user.name=Template test", "-c", "user.email=test@example.com", "commit", "-m", "initial"),
    ):
        result = subprocess.run(
            ["git", *arguments],
            cwd=repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    result = run(
        str(CORE_EXAMPLES_CHECK),
        "--root",
        str(repository),
        "--base",
        "0" * 40,
        "--head",
        "HEAD",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_profile_has_a_policy_and_current_core_dependency(tmp_path: Path) -> None:
    result = create(tmp_path, "personal", "profile", "--skill", "current")
    assert result.returncode == 0, result.stdout + result.stderr
    assert skills(tmp_path, "personal") == {"policy": {"current"}}
    repository = tmp_path / "personal"
    tier = json.loads((repository / ".agents/tiers/personal.json").read_text())
    assert tier["applies"] == "always"
    assert "detect" not in tier
    assert "explicitly select" in (repository / "AGENTS.md").read_text()
    assert_repository_is_current(tmp_path, "personal")


@pytest.mark.parametrize(
    "flags,message",
    [
        ([], "needs --skill"),
        (["--skill", "Bad"], "needs --skill"),
        (["--skill", "current", "--detect-file", "x"], "only a stack"),
    ],
)
def test_profile_requires_a_policy_name_and_rejects_detection(
    tmp_path: Path, flags: list[str], message: str
) -> None:
    result = create(tmp_path, "personal", "profile", *flags)
    assert result.returncode == 2
    assert message in result.stderr
    assert not (tmp_path / "personal").exists()


def test_vendored_files_match_template_and_ci_follows_main(tmp_path: Path) -> None:
    assert create(tmp_path, "helix", "tool").returncode == 0
    repository = tmp_path / "helix"
    for relative in VENDORED:
        assert (ROOT / relative).read_bytes() == (repository / relative).read_bytes(), (
            relative
        )
    ci = (repository / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "uses: owner/template/.github/workflows/plugin-ci.yml@main" in ci
    assert "template_ref: main" in ci
    config = json.loads(
        (repository / ".agents/plugins/template.json").read_text(encoding="utf-8")
    )
    assert "template" not in config
    manifest = json.loads(
        (repository / ".agents/plugins/manifests/codex/helix.json").read_text(
            encoding="utf-8"
        )
    )
    assert "version" not in manifest


def test_refuses_an_existing_repository_and_a_stack_without_markers(
    tmp_path: Path,
) -> None:
    (tmp_path / "zig").mkdir()
    assert (
        "already exists"
        in create(tmp_path, "zig", "stack", "--detect-file", "build.zig").stderr
    )
    assert "needs --detect-file" in create(tmp_path, "odin", "stack").stderr
    assert (
        "only a stack" in create(tmp_path, "helix", "tool", "--detect-file", "x").stderr
    )


@pytest.mark.parametrize("flags", [[], ["--dry-run"]])
def test_reserved_core_dependency_namespace_fails_before_writing(
    tmp_path: Path, flags: list[str]
) -> None:
    result = create(tmp_path, "base", "utility", "--skill", "sweep", *flags)
    assert result.returncode == 2
    assert "namespace base is reserved" in result.stderr
    assert "base-agents/base" in result.stderr
    assert list(tmp_path.iterdir()) == []


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    result = create(tmp_path, "helix", "tool", "--dry-run")
    assert result.returncode == 0
    assert "helix/.agents/helix/policy/learning/SKILL.md" in result.stdout.replace(
        "\\", "/"
    )
    assert not (tmp_path / "helix").exists()


def test_template_copies_equal_their_sources() -> None:
    for relative in VENDORED:
        assert (TEMPLATES / f"{relative}.in").read_bytes() == (
            ROOT / relative
        ).read_bytes(), relative
