import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "sync_generated", ROOT / ".agents" / "sync_generated.py"
)
assert SPEC is not None
assert SPEC.loader is not None
sync_generated: Any = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_generated)


def skill_text(
    name: str, kind: str, body: str = "", domain: str = "demo", profile: str = "core"
) -> str:
    return (
        f"---\nname: {name}\ndescription: The {name} skill.\nkind: {kind}\n"
        f"domain: {domain}\nprofile: {profile}\n"
        f"applicability: demo projects\nrequires: demo\nprovenance: house\n---\n\n"
        f"# {name}\n\n{body}"
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write(path, json.dumps(value, indent=2) + "\n")


def make_repository(root: Path, plugins: tuple[str, ...] = ("demo",)) -> None:
    write_json(
        root / ".agents/plugins/template.json",
        {"schema_version": 1, "repository": "owner/demo", "type": "stack"},
    )
    write_json(
        root / ".agents/plugins/payloads.json",
        {"payloads": {plugin: [plugin] for plugin in plugins}},
    )
    for host in ("claude", "codex"):
        templates = {
            "claude": {
                "name": "demo-agents",
                "description": "Demo.",
                "owner": {"name": "Owner"},
            },
            "codex": {"name": "demo-agents", "interface": {"displayName": "Demo"}},
        }
        write_json(
            root / f".agents/plugins/manifests/{host}/marketplace.json", templates[host]
        )
    for plugin in plugins:
        write_json(
            root / f".agents/tiers/{plugin}.json",
            {
                "schema_version": 1,
                "tier": plugin,
                "applies": "stack-present",
                "owner_repository": ["owner/demo"],
                "detect": {"files": ["demo.toml"]},
            },
        )
        common = {
            "name": plugin,
            "description": f"The {plugin} plugin.",
            "author": {"name": "Owner"},
            "repository": "https://github.com/owner/demo",
            "skills": "./skills/",
            "keywords": [plugin],
        }
        write_json(
            root / f".agents/plugins/manifests/claude/{plugin}.json",
            {**common, "displayName": plugin.title()},
        )
        write_json(
            root / f".agents/plugins/manifests/codex/{plugin}.json",
            {
                **common,
                "interface": {
                    "displayName": plugin.title(),
                    "category": "Productivity",
                },
            },
        )
        write(
            root / f".agents/{plugin}/utility/tool/SKILL.md",
            skill_text(
                "tool",
                "utility",
                "Run `<skill-directory>/scripts/run.py`. See [the notes]"
                "(templates/notes.md).\n",
            ),
        )
        write(root / f".agents/{plugin}/utility/tool/scripts/run.py", "print('run')\n")
        write(root / f".agents/{plugin}/utility/tool/templates/notes.md", "notes\n")
        write(
            root / f".agents/{plugin}/contract/style/SKILL.md",
            skill_text("style", "contract", f"Pairs with `{plugin}:tool`.\n"),
        )


def add_publication(root: Path, package: str, source: str) -> None:
    payload_path = root / ".agents/plugins/payloads.json"
    payloads = json.loads(payload_path.read_text(encoding="utf-8"))
    payloads["payloads"][package] = [source]
    write_json(payload_path, payloads)
    for host in ("claude", "codex"):
        manifest_path = root / f".agents/plugins/manifests/{host}/{source}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["name"] = package
        if host == "claude":
            manifest["displayName"] = package.title()
        else:
            manifest["interface"]["displayName"] = package.title()
        write_json(root / f".agents/plugins/manifests/{host}/{package}.json", manifest)


def build(root: Path) -> dict[str, bytes]:
    return cast(dict[str, bytes], sync_generated.build(root))


def assert_rejected(root: Path, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build(root)


def synchronize(root: Path, check: bool) -> tuple[int, str]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        code = sync_generated.synchronize(root, check)
    return code, stream.getvalue()


@pytest.fixture
def demo_root(tmp_path: Path) -> Path:
    make_repository(tmp_path)
    return tmp_path


def test_external_selection_dependency_is_preserved_and_shape_checked(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    path = tmp_path / ".agents/plugins/payloads.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    payloads["dependencies"] = {"demo": ["base-agents/machine"]}
    write_json(path, payloads)
    assert json.loads(build(tmp_path)["plugins/demo/selection.json"])[
        "dependencies"
    ] == [
        "tj-agents/base",
        "tj-agents/engineering",
        "tj-agents/machine",
        "base-agents/machine",
    ]
    invalid_dependencies: tuple[Any, ...] = (
        "base-agents/*",
        "base-agents/machine/extra",
        "unknown",
        {},
    )
    for invalid in invalid_dependencies:
        payloads["dependencies"] = {"demo": [invalid]}
        write_json(path, payloads)
        with pytest.raises(ValueError):
            build(tmp_path)


def test_optional_harness_is_shipped_without_requiring_migration(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    assert "plugins/demo/harness.json" not in build(tmp_path)
    manifest = {
        "schema_version": 1,
        "plugin": "demo-agents/demo",
        "source_roots": [".agents/demo"],
        "requires": {},
    }
    write_json(tmp_path / ".agents/plugins/manifests/harness/demo.json", manifest)
    generated = json.loads(build(tmp_path)["plugins/demo/harness.json"])
    assert generated["requires"]["plugins"] == [
        "demo-agents/demo",
        "tj-agents/base",
        "tj-agents/engineering",
        "tj-agents/machine",
    ]
    assert generated["requires"]["marketplaces"] == [
        {"id": "tj-agents", "repository": "tj-agents/marketplace"}
    ]


def test_ships_skill_local_files_beside_the_package_and_adapter_entries(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    output = build(tmp_path)
    canonical = "plugins/demo/.agents/demo/utility/tool"
    adapter = "plugins/demo/skills/tool"
    assert (tmp_path / ".agents/demo/utility/tool/SKILL.md").read_bytes() == output[
        f"{canonical}/SKILL.md"
    ]
    for directory in (
        canonical,
        adapter,
        ".claude/skills/tool",
        ".codex/skills/tool",
    ):
        assert f"{directory}/scripts/run.py" in output
        assert f"{directory}/templates/notes.md" in output
    assert (
        "canonical definition](../../.agents/demo/utility/tool/SKILL.md)"
        in output[f"{adapter}/SKILL.md"].decode()
    )
    assert (
        "canonical definition](../../../.agents/demo/utility/tool/SKILL.md)"
        in output[".claude/skills/tool/SKILL.md"].decode()
    )


def test_marketplaces_and_selection_are_derived_from_manifests_and_frontmatter(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    output = build(tmp_path)
    claude = json.loads(output[".claude-plugin/marketplace.json"])
    codex = json.loads(output[".agents/plugins/marketplace.json"])
    assert claude["plugins"] == [
        {
            "name": "demo",
            "source": "./plugins/demo",
            "description": "The demo plugin.",
            "category": "Productivity",
            "keywords": ["demo"],
        }
    ]
    assert codex["plugins"][0]["source"] == {
        "source": "local",
        "path": "./plugins/demo",
    }
    selection = json.loads(output["plugins/demo/selection.json"])
    assert selection["profiles"] == {"core": ["style", "tool"]}
    assert "- `tool` — utility — core" in output["plugins/demo/INDEX.md"].decode()


def test_publications_share_one_source_and_keep_one_local_adapter_set(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    add_publication(tmp_path, "template", "demo")
    for package in ("demo", "template"):
        write_json(
            tmp_path / f".agents/plugins/manifests/harness/{package}.json",
            {
                "schema_version": 1,
                "plugin": f"demo-agents/{package}",
                "source_roots": [".agents/demo"],
                "requires": {},
            },
        )
    output = build(tmp_path)
    for package in ("demo", "template"):
        canonical = f"plugins/{package}/.agents/demo/utility/tool/SKILL.md"
        adapter = f"plugins/{package}/skills/tool/SKILL.md"
        assert (tmp_path / ".agents/demo/utility/tool/SKILL.md").read_bytes() == output[
            canonical
        ]
        assert (
            "canonical definition](../../.agents/demo/utility/tool/SKILL.md)"
            in output[adapter].decode()
        )
        assert (
            json.loads(output[f"plugins/{package}/selection.json"])["plugin"] == package
        )
        assert (
            json.loads(output[f"plugins/{package}/harness.json"])["plugin"]
            == f"demo-agents/{package}"
        )
    assert (
        sum(
            name.endswith("/SKILL.md")
            for name in output
            if name == ".claude/skills/tool/SKILL.md"
        )
        == 1
    )
    assert [
        item["name"]
        for item in json.loads(output[".agents/plugins/marketplace.json"])["plugins"]
    ] == ["demo", "template"]


def test_aliases_are_projected_for_each_publication(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write(
        tmp_path / ".agents/demo/contract/old-style/SKILL.md",
        skill_text("old-style", "contract", "Use `demo:style`.\n"),
    )
    add_publication(tmp_path, "template", "demo")
    payloads = json.loads(
        (tmp_path / ".agents/plugins/payloads.json").read_text(encoding="utf-8")
    )
    payloads["compatibilitySkillAliases"] = {
        "demo": {"old-style": {"replacedBy": "demo:style", "removeAfter": "2027-03-31"}}
    }
    write_json(tmp_path / ".agents/plugins/payloads.json", payloads)
    selection = json.loads(build(tmp_path)["plugins/template/selection.json"])
    assert selection["compatibilitySkillAliases"] == {
        "old-style": {"replacedBy": "template:style", "removeAfter": "2027-03-31"}
    }
    assert selection["profiles"] == {"core": ["style", "tool"]}


def test_several_plugins_prefix_their_adapter_entries(tmp_path: Path) -> None:
    make_repository(tmp_path, ("demo", "extra"))
    output = build(tmp_path)
    assert ".claude/skills/extra-tool/SKILL.md" in output
    assert ".claude/skills/tool/SKILL.md" not in output


def test_an_alias_forwards_within_its_plugin_and_stays_out_of_profiles(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write(
        tmp_path / ".agents/demo/contract/old-style/SKILL.md",
        skill_text("old-style", "contract", "Use `demo:style`.\n"),
    )
    payloads = json.loads((tmp_path / ".agents/plugins/payloads.json").read_text())
    payloads["compatibilitySkillAliases"] = {
        "demo": {"old-style": {"replacedBy": "demo:style", "removeAfter": "2027-03-31"}}
    }
    write_json(tmp_path / ".agents/plugins/payloads.json", payloads)
    selection = json.loads(build(tmp_path)["plugins/demo/selection.json"])
    assert selection["profiles"] == {"core": ["style", "tool"]}
    payloads["compatibilitySkillAliases"]["demo"]["old-style"]["replacedBy"] = (
        "demo:missing"
    )
    write_json(tmp_path / ".agents/plugins/payloads.json", payloads)
    assert_rejected(tmp_path, "alias must forward")


def test_a_family_member_publishes_its_folder_path_joined_by_hyphens(
    demo_root: Path,
) -> None:
    write(
        demo_root / ".agents/demo/contract/state/client/SKILL.md",
        skill_text("state-client", "contract"),
    )
    write(
        demo_root / ".agents/demo/contract/state/server/SKILL.md",
        skill_text("state-server", "contract"),
    )
    output = build(demo_root)
    for name in ("state-client", "state-server"):
        suffix = name.removeprefix("state-")
        assert f"plugins/demo/.agents/demo/contract/state/{suffix}/SKILL.md" in output
        assert f"plugins/demo/skills/{name}/SKILL.md" in output
        assert f".codex/skills/{name}/SKILL.md" in output
    assert (
        "canonical definition](../../.agents/demo/contract/state/client/SKILL.md)"
        in output["plugins/demo/skills/state-client/SKILL.md"].decode()
    )
    assert (
        "canonical definition](../../../.agents/demo/contract/state/client/SKILL.md)"
        in output[".claude/skills/state-client/SKILL.md"].decode()
    )
    assert (
        "- `state-client` — contract — core" in output["plugins/demo/INDEX.md"].decode()
    )


def test_a_family_skill_ships_its_own_files_but_not_its_members(
    demo_root: Path,
) -> None:
    write(
        demo_root / ".agents/demo/contract/naming/SKILL.md",
        skill_text("naming", "contract"),
    )
    write(demo_root / ".agents/demo/contract/naming/templates/rules.md", "rules\n")
    write(
        demo_root / ".agents/demo/contract/naming/collaborators/SKILL.md",
        skill_text("naming-collaborators", "contract"),
    )
    write(
        demo_root / ".agents/demo/contract/naming/collaborators/templates/roles.md",
        "roles\n",
    )
    output = build(demo_root)
    assert "plugins/demo/skills/naming/templates/rules.md" in output
    assert "plugins/demo/skills/naming/collaborators/SKILL.md" not in output
    assert "plugins/demo/skills/naming-collaborators/templates/roles.md" in output


def test_a_member_named_without_its_family(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/state/client/SKILL.md",
        skill_text("client", "contract"),
    )
    assert_rejected(demo_root, "name must be state-client")


def test_a_file_in_a_family_folder(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/state/client/SKILL.md",
        skill_text("state-client", "contract"),
    )
    write(demo_root / ".agents/demo/contract/state/notes.md", "stray\n")
    assert_rejected(demo_root, "only skill folders")


def test_a_linked_member_folder_is_not_shipped(
    demo_root: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    write(outside / "SKILL.md", skill_text("style-linked", "contract"))
    link = demo_root / ".agents/demo/contract/style/linked"
    try:
        if os.name == "nt":
            import _winapi

            _winapi.CreateJunction(str(outside), str(link))
        else:
            link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"cannot create a link here: {error}")
    assert_rejected(demo_root, "links are not shipped")


def test_a_family_name_colliding_with_a_flat_skill(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/state/client/SKILL.md",
        skill_text("state-client", "contract"),
    )
    write(
        demo_root / ".agents/demo/contract/state-client/SKILL.md",
        skill_text("state-client", "contract"),
    )
    assert_rejected(demo_root, "duplicate skill state-client")


def test_missing_frontmatter_field(demo_root: Path) -> None:
    path = demo_root / ".agents/demo/contract/style/SKILL.md"
    write(path, path.read_text().replace("provenance: house\n", ""))
    assert_rejected(demo_root, "missing provenance")


def test_domain_other_than_the_repository_namespace(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", domain="other"),
    )
    assert_rejected(demo_root, "domain must be demo")


def test_kind_other_than_its_folder(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/knowledge/style/SKILL.md",
        skill_text("style", "contract"),
    )
    assert_rejected(demo_root, "kind must equal its kind folder")


def test_kind_with_a_digit_is_rejected(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract2/style/SKILL.md",
        skill_text("style", "contract2"),
    )
    assert_rejected(demo_root, "kind must be one lowercase word")


def test_kind_with_a_hyphen_is_rejected(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/my-kind/style/SKILL.md",
        skill_text("style", "my-kind"),
    )
    assert_rejected(demo_root, "kind must be one lowercase word")


def test_an_unknown_lowercase_kind_is_accepted(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/policy/learning/SKILL.md",
        skill_text("learning", "policy"),
    )
    output = build(demo_root)
    assert "plugins/demo/skills/learning/SKILL.md" in output


def test_file_directly_under_a_plugin_folder(demo_root: Path) -> None:
    write(demo_root / ".agents/demo/notes.md", "stray\n")
    assert_rejected(demo_root, "only kind folders")


def test_folder_without_skill_under_a_kind_folder(demo_root: Path) -> None:
    write(demo_root / ".agents/demo/utility/empty/notes.md", "stray\n")
    assert_rejected(demo_root, "only skill folders")


def test_unknown_qualified_and_bare_references(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", "See `demo:missing`.\n"),
    )
    assert_rejected(demo_root, "unknown skill reference demo:missing")
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", "See the `missing` skill.\n"),
    )
    assert_rejected(demo_root, "unknown skill reference `missing` skill")


def test_link_that_leaves_the_package(demo_root: Path) -> None:
    write(demo_root / "README.md", "readme\n")
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", "See [the readme](../../../../README.md).\n"),
    )
    assert_rejected(demo_root, "does not resolve from generated")


def test_package_links_cannot_reach_the_package_parent(demo_root: Path) -> None:
    make_repository(demo_root, ("demo", "extra"))
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", "See [the packages](../../../../..).\n"),
    )
    assert_rejected(demo_root, "does not resolve from .agents/demo/contract/style")


def test_package_adapters_cannot_link_to_another_package(
    demo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_repository(demo_root, ("demo", "extra"))
    assert "plugins/extra/INDEX.md" in build(demo_root)
    adapter_body = sync_generated.adapter_body

    def cross_package_adapter(
        skill: dict[str, Any], adapter_dir: str, canonical_dir: str | None = None
    ) -> str:
        body: str = adapter_body(skill, adapter_dir, canonical_dir)
        if adapter_dir == "plugins/demo/skills/style":
            return body + "See [the extra package](../../../extra/INDEX.md).\n"
        return body

    monkeypatch.setattr(sync_generated, "adapter_body", cross_package_adapter)
    assert_rejected(
        demo_root, "does not resolve from generated plugins/demo/skills/style"
    )


def test_package_links_can_reach_in_package_ancestors_and_resources(
    demo_root: Path,
) -> None:
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text(
            "style",
            "contract",
            "See [the notes](../../utility/tool/templates/notes.md).\n",
        ),
    )
    output = build(demo_root)
    assert (
        b"[the notes](../../utility/tool/templates/notes.md)"
        in output["plugins/demo/.agents/demo/contract/style/SKILL.md"]
    )
    for host in (".claude", ".codex"):
        assert (
            b"canonical definition](../../../.agents/demo/contract/style/SKILL.md)"
            in output[f"{host}/skills/style/SKILL.md"]
        )


def test_missing_skill_directory_file(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text(
            "style", "contract", "Run `<skill-directory>/scripts/missing.py`.\n"
        ),
    )
    assert_rejected(demo_root, "scripts/missing.py does not resolve")


def test_payloads_select_known_sources_and_retain_identity_publications(
    demo_root: Path,
) -> None:
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {"payloads": {"other": ["other"]}},
    )
    assert_rejected(demo_root, "other must select exactly one canonical source")
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {"payloads": {"published": ["demo"]}},
    )
    assert_rejected(demo_root, "demo must retain its identity publication")
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {"payloads": {"demo": ["demo", "demo"]}},
    )
    assert_rejected(demo_root, "demo must select exactly one canonical source")


def test_dependencies_reject_local_aliases_and_self_dependencies(
    demo_root: Path,
) -> None:
    make_repository(demo_root, ("demo", "extra"))
    add_publication(demo_root, "template", "extra")
    payloads = json.loads(
        (demo_root / ".agents/plugins/payloads.json").read_text(encoding="utf-8")
    )
    payloads["dependencies"] = {"demo": ["template"]}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "cannot depend on local alias template")
    payloads["dependencies"] = {"extra": ["template"]}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "extra cannot depend on local alias template")
    payloads["dependencies"] = {"demo": ["demo-agents/demo"]}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "demo cannot depend on demo-agents/demo")
    payloads["dependencies"] = {"demo": ["demo-agents/missing"]}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "demo cannot depend on demo-agents/missing")


VALID_HARNESS = {
    "schema_version": 1,
    "plugin": "demo-agents/demo",
    "source_roots": [".agents/demo"],
    "requires": {},
}

HARNESS_ENVELOPE_CASES: list[tuple[Any, str]] = [
    (None, "must be a JSON object"),
    ([], "must be a JSON object"),
    ({**VALID_HARNESS, "schema_version": True}, "schema_version must be 1"),
    ({**VALID_HARNESS, "schema_version": 2}, "schema_version must be 1"),
    (
        {**VALID_HARNESS, "plugin": "demo-agents/other"},
        "plugin must be demo-agents/demo",
    ),
    (
        {**VALID_HARNESS, "source_roots": None},
        "source_roots must be a nonempty list",
    ),
    (
        {**VALID_HARNESS, "source_roots": ".agents/demo"},
        "source_roots must be a nonempty list",
    ),
    ({**VALID_HARNESS, "source_roots": []}, "source_roots must be a nonempty list"),
    ({**VALID_HARNESS, "source_roots": [1]}, "source_roots must be a nonempty list"),
    (
        {**VALID_HARNESS, "source_roots": [".agents/demo", ".agents/demo"]},
        "source_roots must be unique",
    ),
    (
        {**VALID_HARNESS, "source_roots": ["/agents/demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": ["C:/agents/demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": [".agents\\demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": [".agents/../demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": [".agents/\x00demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": ["plugins/demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": [".agents/missing"]},
        "is not shipped in demo",
    ),
]


@pytest.mark.parametrize("value,message", HARNESS_ENVELOPE_CASES)
def test_harness_rejects_invalid_envelopes_and_roots(
    demo_root: Path, value: Any, message: str
) -> None:
    harness = demo_root / ".agents/plugins/manifests/harness/demo.json"
    write_json(harness, value)
    assert_rejected(demo_root, message)


def test_harness_rejects_unreadable_json(
    demo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    valid = {
        "schema_version": 1,
        "plugin": "demo-agents/demo",
        "source_roots": [".agents/demo"],
        "requires": {},
    }
    harness = demo_root / ".agents/plugins/manifests/harness/demo.json"
    write(harness, "not json\n")
    assert_rejected(demo_root, "unreadable JSON")
    harness.write_bytes(b"\xff")
    assert_rejected(demo_root, "unreadable JSON")
    write_json(harness, valid)

    def locked(path: Path) -> str:
        raise OSError("locked")

    monkeypatch.setattr(sync_generated, "read", locked)
    with pytest.raises(ValueError, match="unreadable JSON"):
        sync_generated.harness_body(demo_root, "demo", "demo-agents", {}, [], False)


def test_harness_cannot_claim_another_publication_source(demo_root: Path) -> None:
    make_repository(demo_root, ("demo", "extra"))
    add_publication(demo_root, "template", "demo")
    write_json(
        demo_root / ".agents/plugins/manifests/harness/template.json",
        {
            "schema_version": 1,
            "plugin": "demo-agents/template",
            "source_roots": [".agents/extra"],
            "requires": {},
        },
    )
    assert_rejected(demo_root, "source root '.agents/extra' is not shipped in template")


def test_publication_manifest_roster_is_complete(demo_root: Path) -> None:
    add_publication(demo_root, "template", "demo")
    (demo_root / ".agents/plugins/manifests/codex/template.json").unlink()
    assert_rejected(demo_root, "manifests/codex must hold exactly")


def test_tier_rules(demo_root: Path) -> None:
    path = demo_root / ".agents/tiers/demo.json"
    tier = json.loads(path.read_text())
    write_json(path, {**tier, "applies": "always"})
    assert_rejected(demo_root, "declares no detect markers")
    write_json(path, {key: value for key, value in tier.items() if key != "detect"})
    assert_rejected(demo_root, "needs at least one detect marker")
    write_json(path, {**tier, "owner_repository": ["owner/other"]})
    assert_rejected(demo_root, "owner_repository must name owner/demo")


def test_manifests_must_agree(demo_root: Path) -> None:
    path = demo_root / ".agents/plugins/manifests/claude/demo.json"
    write_json(path, {**json.loads(path.read_text()), "description": "Drifted."})
    assert_rejected(demo_root, "disagree on description")


def test_both_host_manifests_reject_version(demo_root: Path) -> None:
    for host in ("claude", "codex"):
        path = demo_root / f".agents/plugins/manifests/{host}/demo.json"
        write_json(path, {**json.loads(path.read_text()), "version": "1.0.0"})
        assert_rejected(demo_root, f"the {host} manifest must omit version")
        manifest = json.loads(path.read_text())
        manifest.pop("version")
        write_json(path, manifest)


def test_marketplace_templates_do_not_list_plugins(demo_root: Path) -> None:
    path = demo_root / ".agents/plugins/manifests/claude/marketplace.json"
    write_json(path, {**json.loads(path.read_text()), "plugins": []})
    assert_rejected(demo_root, "plugin entries are generated")


def test_legacy_template_config_pin_is_rejected(demo_root: Path) -> None:
    path = demo_root / ".agents/plugins/template.json"
    write_json(path, {**json.loads(path.read_text()), "template": "0.0.1"})
    assert_rejected(demo_root, r"unknown fields \['template'\]")


def test_byte_order_mark(demo_root: Path) -> None:
    path = demo_root / ".agents/demo/contract/style/SKILL.md"
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    assert_rejected(demo_root, "BOM")


def test_check_reports_missing_stale_and_extra_outputs(demo_root: Path) -> None:
    code, report = synchronize(demo_root, check=True)
    assert code == 1
    assert "MISSING: plugins/demo/skills/tool/SKILL.md" in report
    assert synchronize(demo_root, check=False)[0] == 0
    assert synchronize(demo_root, check=True)[0] == 0
    write(demo_root / "plugins/demo/INDEX.md", "edited\n")
    write(demo_root / "plugins/stale/INDEX.md", "stale\n")
    code, report = synchronize(demo_root, check=True)
    assert code == 1
    assert "STALE: plugins/demo/INDEX.md" in report
    assert "EXTRA: plugins/stale/INDEX.md" in report


def test_write_refuses_a_linked_generated_root(
    demo_root: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    link = demo_root / "plugins"
    try:
        if os.name == "nt":
            import _winapi

            _winapi.CreateJunction(str(outside), str(link))
        else:
            link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"cannot create a link here: {error}")
    with pytest.raises(ValueError, match="link or junction"):
        synchronize(demo_root, check=False)


def run_generator_cli(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / ".agents/sync_generated.py"),
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_reserves_continuation_runtime_state(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write(tmp_path / ".agents/continuation/owner.json", "{}\n")
    write(tmp_path / ".agents/continuation/events.jsonl", "{}\n")
    write(tmp_path / ".agents/continuation/locks/foreground.lock", "locked\n")
    write(tmp_path / ".agents/continuation/scheduler/state.json", "{}\n")
    result = run_generator_cli(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "plugins/continuation").exists()
    assert "continuation" not in (tmp_path / ".agents/INDEX.md").read_text(
        encoding="utf-8"
    )
    assert "continuation" not in (
        tmp_path / ".agents/plugins/marketplace.json"
    ).read_text(encoding="utf-8")


def test_rejects_malformed_authored_plugin_directory(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write(tmp_path / ".agents/authored/owner.json", "{}\n")
    result = run_generator_cli(tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert (
        ".agents/authored/owner.json: only kind folders belong in a plugin folder"
        in result.stdout
    )


def test_each_copied_package_runs_from_its_adapter_resources(tmp_path: Path) -> None:
    name = "template"
    package = tmp_path / name
    shutil.copytree(ROOT / f"plugins/{name}", package)
    new_plugin = subprocess.run(
        [
            sys.executable,
            "-B",
            str(package / "skills/new-plugin/scripts/new_plugin.py"),
            "--repository",
            "owner/example",
            "--type",
            "utility",
            "--skill",
            "sweep",
            "--description",
            "Example plugin.",
            "--destination",
            str(tmp_path),
            "--author",
            "Ada Lovelace",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert new_plugin.returncode == 0, new_plugin.stdout + new_plugin.stderr
    example = tmp_path / "example"
    adapter_check = package / "skills/check/scripts/check.py"
    canonical_check = package / ".agents/template/utility/check/scripts/check.py"
    check = subprocess.run(
        [sys.executable, "-B", str(adapter_check), "--root", str(example)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    gitignore = example / ".gitignore"
    gitignore.write_text(
        gitignore.read_text(encoding="utf-8") + "local/\n", encoding="utf-8"
    )
    drifted = subprocess.run(
        [sys.executable, "-B", str(adapter_check), "--root", str(example)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert drifted.returncode == 1
    assert ".gitignore: differs from current Template" in drifted.stderr
    update = subprocess.run(
        [
            sys.executable,
            "-B",
            str(package / "skills/update/scripts/update.py"),
            "--root",
            str(example),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert update.returncode == 0, update.stdout + update.stderr
    canonical = subprocess.run(
        [sys.executable, "-B", str(canonical_check), "--root", str(example)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert canonical.returncode == 0, canonical.stdout + canonical.stderr


def test_template_generated_outputs_are_current() -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        assert sync_generated.synchronize(ROOT, check=True) == 0
