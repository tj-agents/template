from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("sync_generated", ROOT / ".agents" / "sync_generated.py")
sync_generated = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_generated)


def skill_text(name: str, kind: str, body: str = "", domain: str = "demo", profile: str = "core") -> str:
    return (
        f"---\nname: {name}\ndescription: The {name} skill.\nkind: {kind}\ndomain: {domain}\nprofile: {profile}\n"
        f"applicability: demo projects\nrequires: demo\nprovenance: house\n---\n\n# {name}\n\n{body}"
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value) -> None:
    write(path, json.dumps(value, indent=2) + "\n")


def make_repository(root: Path, plugins: tuple[str, ...] = ("demo",)) -> None:
    write_json(root / ".agents/plugins/kit.json", {"schema_version": 1, "kit": sync_generated.KIT_VERSION, "repository": "owner/demo", "type": "stack"})
    write_json(root / ".agents/plugins/payloads.json", {"payloads": {plugin: [plugin] for plugin in plugins}})
    for host in ("claude", "codex"):
        templates = {
            "claude": {"name": "demo-agents", "description": "Demo.", "owner": {"name": "Owner"}},
            "codex": {"name": "demo-agents", "interface": {"displayName": "Demo"}},
        }
        write_json(root / f".agents/plugins/manifests/{host}/marketplace.json", templates[host])
    for plugin in plugins:
        write_json(
            root / f".agents/tiers/{plugin}.json",
            {"schema_version": 1, "tier": plugin, "applies": "stack-present", "owner_repository": ["owner/demo"], "detect": {"files": ["demo.toml"]}},
        )
        common = {
            "name": plugin,
            "description": f"The {plugin} plugin.",
            "author": {"name": "Owner"},
            "repository": "https://github.com/owner/demo",
            "skills": "./skills/",
            "keywords": [plugin],
        }
        write_json(root / f".agents/plugins/manifests/claude/{plugin}.json", {**common, "displayName": plugin.title()})
        write_json(
            root / f".agents/plugins/manifests/codex/{plugin}.json",
            {**common, "version": "0.1.0", "interface": {"displayName": plugin.title(), "category": "Productivity"}},
        )
        write(
            root / f".agents/{plugin}/utility/tool/SKILL.md",
            skill_text("tool", "utility", "Run `<skill-directory>/scripts/run.py`. See [the notes](templates/notes.md).\n"),
        )
        write(root / f".agents/{plugin}/utility/tool/scripts/run.py", "print('run')\n")
        write(root / f".agents/{plugin}/utility/tool/templates/notes.md", "notes\n")
        write(root / f".agents/{plugin}/contract/style/SKILL.md", skill_text("style", "contract", f"Pairs with `{plugin}:tool`.\n"))


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


class GeneratorTestCase(unittest.TestCase):
    def test_external_selection_dependency_is_preserved_and_shape_checked(self):
        make_repository(self.root)
        path = self.root / ".agents/plugins/payloads.json"
        payloads = json.loads(path.read_text(encoding="utf-8"))
        payloads["dependencies"] = {"demo": ["base-agents/machine"]}
        write_json(path, payloads)
        self.assertEqual(
            ["tj-agents/base", "tj-agents/engineering", "tj-agents/machine", "base-agents/machine"],
            json.loads(self.build()["plugins/demo/selection.json"])["dependencies"],
        )
        for invalid in ("base-agents/*", "base-agents/machine/extra", "unknown", {}):
            payloads["dependencies"] = {"demo": [invalid]}
            write_json(path, payloads)
            with self.assertRaises(ValueError):
                self.build()

    def test_optional_harness_is_shipped_without_requiring_migration(self):
        make_repository(self.root)
        self.assertNotIn("plugins/demo/harness.json", sync_generated.build(self.root))
        manifest = {"schema_version": 1, "plugin": "demo-agents/demo", "source_roots": [".agents/demo"], "requires": {}}
        write_json(self.root / ".agents/plugins/manifests/harness/demo.json", manifest)
        generated = json.loads(sync_generated.build(self.root)["plugins/demo/harness.json"])
        self.assertEqual(["demo-agents/demo", "tj-agents/base", "tj-agents/engineering", "tj-agents/machine"], generated["requires"]["plugins"])
        self.assertEqual([{"id": "tj-agents", "repository": "tj-agents/marketplace"}], generated["requires"]["marketplaces"])

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def build(self) -> dict[str, bytes]:
        return sync_generated.build(self.root)

    def assert_rejected(self, message: str) -> None:
        with self.assertRaisesRegex(ValueError, message):
            self.build()

    def synchronize(self, check: bool) -> tuple[int, str]:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = sync_generated.synchronize(self.root, check)
        return code, stream.getvalue()


class BuildTests(GeneratorTestCase):
    def test_ships_skill_local_files_beside_the_package_and_adapter_entries(self) -> None:
        make_repository(self.root)
        output = self.build()
        canonical = "plugins/demo/.agents/demo/utility/tool"
        adapter = "plugins/demo/skills/tool"
        self.assertEqual(
            (self.root / ".agents/demo/utility/tool/SKILL.md").read_bytes(),
            output[f"{canonical}/SKILL.md"],
        )
        for directory in (canonical, adapter, ".claude/skills/tool", ".codex/skills/tool"):
            self.assertIn(f"{directory}/scripts/run.py", output)
            self.assertIn(f"{directory}/templates/notes.md", output)
        self.assertIn(
            "canonical definition](../../.agents/demo/utility/tool/SKILL.md)",
            output[f"{adapter}/SKILL.md"].decode(),
        )
        self.assertIn("canonical definition](../../../.agents/demo/utility/tool/SKILL.md)", output[".claude/skills/tool/SKILL.md"].decode())

    def test_marketplaces_and_selection_are_derived_from_manifests_and_frontmatter(self) -> None:
        make_repository(self.root)
        output = self.build()
        claude = json.loads(output[".claude-plugin/marketplace.json"])
        codex = json.loads(output[".agents/plugins/marketplace.json"])
        self.assertEqual([{"name": "demo", "source": "./plugins/demo", "description": "The demo plugin.", "category": "Productivity", "keywords": ["demo"]}], claude["plugins"])
        self.assertEqual({"source": "local", "path": "./plugins/demo"}, codex["plugins"][0]["source"])
        selection = json.loads(output["plugins/demo/selection.json"])
        self.assertEqual({"core": ["style", "tool"]}, selection["profiles"])
        self.assertIn("- `tool` — utility — core", output["plugins/demo/INDEX.md"].decode())

    def test_publications_share_one_source_and_keep_one_local_adapter_set(self) -> None:
        make_repository(self.root)
        add_publication(self.root, "template", "demo")
        for package in ("demo", "template"):
            write_json(
                self.root / f".agents/plugins/manifests/harness/{package}.json",
                {"schema_version": 1, "plugin": f"demo-agents/{package}", "source_roots": [".agents/demo"], "requires": {}},
            )
        output = self.build()
        for package in ("demo", "template"):
            canonical = f"plugins/{package}/.agents/demo/utility/tool/SKILL.md"
            adapter = f"plugins/{package}/skills/tool/SKILL.md"
            self.assertEqual((self.root / ".agents/demo/utility/tool/SKILL.md").read_bytes(), output[canonical])
            self.assertIn("canonical definition](../../.agents/demo/utility/tool/SKILL.md)", output[adapter].decode())
            self.assertEqual(package, json.loads(output[f"plugins/{package}/selection.json"])["plugin"])
            self.assertEqual(f"demo-agents/{package}", json.loads(output[f"plugins/{package}/harness.json"])["plugin"])
        self.assertEqual(1, sum(name.endswith("/SKILL.md") for name in output if name == ".claude/skills/tool/SKILL.md"))
        self.assertEqual(["demo", "template"], [item["name"] for item in json.loads(output[".agents/plugins/marketplace.json"])["plugins"]])

    def test_aliases_are_projected_for_each_publication(self) -> None:
        make_repository(self.root)
        write(self.root / ".agents/demo/contract/old-style/SKILL.md", skill_text("old-style", "contract", "Use `demo:style`.\n"))
        add_publication(self.root, "template", "demo")
        payloads = json.loads((self.root / ".agents/plugins/payloads.json").read_text(encoding="utf-8"))
        payloads["compatibilitySkillAliases"] = {"demo": {"old-style": {"replacedBy": "demo:style", "removeAfter": "2027-03-31"}}}
        write_json(self.root / ".agents/plugins/payloads.json", payloads)
        selection = json.loads(self.build()["plugins/template/selection.json"])
        self.assertEqual({"old-style": {"replacedBy": "template:style", "removeAfter": "2027-03-31"}}, selection["compatibilitySkillAliases"])
        self.assertEqual({"core": ["style", "tool"]}, selection["profiles"])

    def test_several_plugins_prefix_their_adapter_entries(self) -> None:
        make_repository(self.root, ("demo", "extra"))
        output = self.build()
        self.assertIn(".claude/skills/extra-tool/SKILL.md", output)
        self.assertNotIn(".claude/skills/tool/SKILL.md", output)

    def test_an_alias_forwards_within_its_plugin_and_stays_out_of_profiles(self) -> None:
        make_repository(self.root)
        write(self.root / ".agents/demo/contract/old-style/SKILL.md", skill_text("old-style", "contract", "Use `demo:style`.\n"))
        payloads = json.loads((self.root / ".agents/plugins/payloads.json").read_text())
        payloads["compatibilitySkillAliases"] = {"demo": {"old-style": {"replacedBy": "demo:style", "removeAfter": "2027-03-31"}}}
        write_json(self.root / ".agents/plugins/payloads.json", payloads)
        selection = json.loads(self.build()["plugins/demo/selection.json"])
        self.assertEqual({"core": ["style", "tool"]}, selection["profiles"])
        payloads["compatibilitySkillAliases"]["demo"]["old-style"]["replacedBy"] = "demo:missing"
        write_json(self.root / ".agents/plugins/payloads.json", payloads)
        self.assert_rejected("alias must forward")


class FamilyTests(GeneratorTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_repository(self.root)

    def test_a_family_member_publishes_its_folder_path_joined_by_hyphens(self) -> None:
        write(self.root / ".agents/demo/contract/state/client/SKILL.md", skill_text("state-client", "contract"))
        write(self.root / ".agents/demo/contract/state/server/SKILL.md", skill_text("state-server", "contract"))
        output = self.build()
        for name in ("state-client", "state-server"):
            self.assertIn(f"plugins/demo/.agents/demo/contract/state/{name.removeprefix('state-')}/SKILL.md", output)
            self.assertIn(f"plugins/demo/skills/{name}/SKILL.md", output)
            self.assertIn(f".codex/skills/{name}/SKILL.md", output)
        self.assertIn(
            "canonical definition](../../.agents/demo/contract/state/client/SKILL.md)",
            output["plugins/demo/skills/state-client/SKILL.md"].decode(),
        )
        self.assertIn(
            "canonical definition](../../../.agents/demo/contract/state/client/SKILL.md)",
            output[".claude/skills/state-client/SKILL.md"].decode(),
        )
        self.assertIn("- `state-client` — contract — core", output["plugins/demo/INDEX.md"].decode())

    def test_a_family_skill_ships_its_own_files_but_not_its_members(self) -> None:
        write(self.root / ".agents/demo/contract/naming/SKILL.md", skill_text("naming", "contract"))
        write(self.root / ".agents/demo/contract/naming/templates/rules.md", "rules\n")
        write(self.root / ".agents/demo/contract/naming/collaborators/SKILL.md", skill_text("naming-collaborators", "contract"))
        write(self.root / ".agents/demo/contract/naming/collaborators/templates/roles.md", "roles\n")
        output = self.build()
        self.assertIn("plugins/demo/skills/naming/templates/rules.md", output)
        self.assertNotIn("plugins/demo/skills/naming/collaborators/SKILL.md", output)
        self.assertIn("plugins/demo/skills/naming-collaborators/templates/roles.md", output)

    def test_a_member_named_without_its_family(self) -> None:
        write(self.root / ".agents/demo/contract/state/client/SKILL.md", skill_text("client", "contract"))
        self.assert_rejected("name must be state-client")

    def test_a_file_in_a_family_folder(self) -> None:
        write(self.root / ".agents/demo/contract/state/client/SKILL.md", skill_text("state-client", "contract"))
        write(self.root / ".agents/demo/contract/state/notes.md", "stray\n")
        self.assert_rejected("only skill folders")

    def test_a_linked_member_folder_is_not_shipped(self) -> None:
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        write(Path(outside.name) / "SKILL.md", skill_text("style-linked", "contract"))
        link = self.root / ".agents/demo/contract/style/linked"
        try:
            if os.name == "nt":
                import _winapi

                _winapi.CreateJunction(outside.name, str(link))
            else:
                link.symlink_to(outside.name, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"cannot create a link here: {error}")
        self.assert_rejected("links are not shipped")

    def test_a_family_name_colliding_with_a_flat_skill(self) -> None:
        write(self.root / ".agents/demo/contract/state/client/SKILL.md", skill_text("state-client", "contract"))
        write(self.root / ".agents/demo/contract/state-client/SKILL.md", skill_text("state-client", "contract"))
        self.assert_rejected("duplicate skill state-client")


class RejectionTests(GeneratorTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_repository(self.root)

    def test_missing_frontmatter_field(self) -> None:
        path = self.root / ".agents/demo/contract/style/SKILL.md"
        write(path, path.read_text().replace("provenance: house\n", ""))
        self.assert_rejected("missing provenance")

    def test_domain_other_than_the_repository_namespace(self) -> None:
        write(self.root / ".agents/demo/contract/style/SKILL.md", skill_text("style", "contract", domain="other"))
        self.assert_rejected("domain must be demo")

    def test_kind_other_than_its_folder(self) -> None:
        write(self.root / ".agents/demo/knowledge/style/SKILL.md", skill_text("style", "contract"))
        self.assert_rejected("kind must equal its kind folder")

    def test_kind_with_a_digit_is_rejected(self) -> None:
        write(self.root / ".agents/demo/contract2/style/SKILL.md", skill_text("style", "contract2"))
        self.assert_rejected("kind must be one lowercase word")

    def test_kind_with_a_hyphen_is_rejected(self) -> None:
        write(self.root / ".agents/demo/my-kind/style/SKILL.md", skill_text("style", "my-kind"))
        self.assert_rejected("kind must be one lowercase word")

    def test_an_unknown_lowercase_kind_is_accepted(self) -> None:
        write(self.root / ".agents/demo/policy/learning/SKILL.md", skill_text("learning", "policy"))
        output = self.build()
        self.assertIn("plugins/demo/skills/learning/SKILL.md", output)

    def test_file_directly_under_a_plugin_folder(self) -> None:
        write(self.root / ".agents/demo/notes.md", "stray\n")
        self.assert_rejected("only kind folders")

    def test_folder_without_skill_under_a_kind_folder(self) -> None:
        write(self.root / ".agents/demo/utility/empty/notes.md", "stray\n")
        self.assert_rejected("only skill folders")

    def test_unknown_qualified_and_bare_references(self) -> None:
        write(self.root / ".agents/demo/contract/style/SKILL.md", skill_text("style", "contract", "See `demo:missing`.\n"))
        self.assert_rejected("unknown skill reference demo:missing")
        write(self.root / ".agents/demo/contract/style/SKILL.md", skill_text("style", "contract", "See the `missing` skill.\n"))
        self.assert_rejected("unknown skill reference `missing` skill")

    def test_link_that_leaves_the_package(self) -> None:
        write(self.root / "README.md", "readme\n")
        write(self.root / ".agents/demo/contract/style/SKILL.md", skill_text("style", "contract", "See [the readme](../../../../README.md).\n"))
        self.assert_rejected("does not resolve from generated")

    def test_package_links_cannot_reach_the_package_parent(self) -> None:
        make_repository(self.root, ("demo", "extra"))
        write(
            self.root / ".agents/demo/contract/style/SKILL.md",
            skill_text("style", "contract", "See [the packages](../../../../..).\n"),
        )
        self.assert_rejected("does not resolve from .agents/demo/contract/style")

    def test_package_adapters_cannot_link_to_another_package(self) -> None:
        make_repository(self.root, ("demo", "extra"))
        self.assertIn("plugins/extra/INDEX.md", self.build())
        adapter_body = sync_generated.adapter_body

        def cross_package_adapter(skill, adapter_dir, canonical_dir=None):
            body = adapter_body(skill, adapter_dir, canonical_dir)
            if adapter_dir == "plugins/demo/skills/style":
                return body + "See [the extra package](../../../extra/INDEX.md).\n"
            return body

        with mock.patch.object(sync_generated, "adapter_body", side_effect=cross_package_adapter):
            self.assert_rejected("does not resolve from generated plugins/demo/skills/style")

    def test_package_links_can_reach_in_package_ancestors_and_resources(self) -> None:
        write(
            self.root / ".agents/demo/contract/style/SKILL.md",
            skill_text("style", "contract", "See [the notes](../../utility/tool/templates/notes.md).\n"),
        )
        output = self.build()
        self.assertIn(
            b"[the notes](../../utility/tool/templates/notes.md)",
            output["plugins/demo/.agents/demo/contract/style/SKILL.md"],
        )
        for host in (".claude", ".codex"):
            self.assertIn(
                b"canonical definition](../../../.agents/demo/contract/style/SKILL.md)",
                output[f"{host}/skills/style/SKILL.md"],
            )

    def test_missing_skill_directory_file(self) -> None:
        write(self.root / ".agents/demo/contract/style/SKILL.md", skill_text("style", "contract", "Run `<skill-directory>/scripts/missing.py`.\n"))
        self.assert_rejected("scripts/missing.py does not resolve")

    def test_payloads_select_known_sources_and_retain_identity_publications(self) -> None:
        write_json(self.root / ".agents/plugins/payloads.json", {"payloads": {"other": ["other"]}})
        self.assert_rejected("other must select exactly one canonical source")
        write_json(self.root / ".agents/plugins/payloads.json", {"payloads": {"published": ["demo"]}})
        self.assert_rejected("demo must retain its identity publication")
        write_json(self.root / ".agents/plugins/payloads.json", {"payloads": {"demo": ["demo", "demo"]}})
        self.assert_rejected("demo must select exactly one canonical source")

    def test_dependencies_reject_local_aliases_and_self_dependencies(self) -> None:
        make_repository(self.root, ("demo", "extra"))
        add_publication(self.root, "template", "extra")
        payloads = json.loads((self.root / ".agents/plugins/payloads.json").read_text(encoding="utf-8"))
        payloads["dependencies"] = {"demo": ["template"]}
        write_json(self.root / ".agents/plugins/payloads.json", payloads)
        self.assert_rejected("cannot depend on local alias template")
        payloads["dependencies"] = {"extra": ["template"]}
        write_json(self.root / ".agents/plugins/payloads.json", payloads)
        self.assert_rejected("extra cannot depend on local alias template")
        payloads["dependencies"] = {"demo": ["demo-agents/demo"]}
        write_json(self.root / ".agents/plugins/payloads.json", payloads)
        self.assert_rejected("demo cannot depend on demo-agents/demo")
        payloads["dependencies"] = {"demo": ["demo-agents/missing"]}
        write_json(self.root / ".agents/plugins/payloads.json", payloads)
        self.assert_rejected("demo cannot depend on demo-agents/missing")

    def test_harness_rejects_invalid_envelopes_and_roots(self) -> None:
        harness = self.root / ".agents/plugins/manifests/harness/demo.json"
        valid = {"schema_version": 1, "plugin": "demo-agents/demo", "source_roots": [".agents/demo"], "requires": {}}
        for value, message in (
            (None, "must be a JSON object"),
            ([], "must be a JSON object"),
            ({**valid, "schema_version": True}, "schema_version must be 1"),
            ({**valid, "schema_version": 2}, "schema_version must be 1"),
            ({**valid, "plugin": "demo-agents/other"}, "plugin must be demo-agents/demo"),
            ({**valid, "source_roots": None}, "source_roots must be a nonempty list"),
            ({**valid, "source_roots": ".agents/demo"}, "source_roots must be a nonempty list"),
            ({**valid, "source_roots": []}, "source_roots must be a nonempty list"),
            ({**valid, "source_roots": [1]}, "source_roots must be a nonempty list"),
            ({**valid, "source_roots": [".agents/demo", ".agents/demo"]}, "source_roots must be unique"),
            ({**valid, "source_roots": ["/agents/demo"]}, "unsafe canonical source root"),
            ({**valid, "source_roots": ["C:/agents/demo"]}, "unsafe canonical source root"),
            ({**valid, "source_roots": [".agents\\demo"]}, "unsafe canonical source root"),
            ({**valid, "source_roots": [".agents/../demo"]}, "unsafe canonical source root"),
            ({**valid, "source_roots": [".agents/\x00demo"]}, "unsafe canonical source root"),
            ({**valid, "source_roots": ["plugins/demo"]}, "unsafe canonical source root"),
            ({**valid, "source_roots": [".agents/missing"]}, "is not shipped in demo"),
        ):
            with self.subTest(value=value):
                write_json(harness, value)
                self.assert_rejected(message)
        harness.write_text("not json\n", encoding="utf-8")
        self.assert_rejected("unreadable JSON")
        harness.write_bytes(b"\xff")
        self.assert_rejected("unreadable JSON")
        write_json(harness, valid)
        with mock.patch.object(sync_generated, "read", side_effect=OSError("locked")):
            with self.assertRaisesRegex(ValueError, "unreadable JSON"):
                sync_generated.harness_body(self.root, "demo", "demo-agents", {}, [], False)

    def test_harness_cannot_claim_another_publication_source(self) -> None:
        make_repository(self.root, ("demo", "extra"))
        add_publication(self.root, "template", "demo")
        write_json(
            self.root / ".agents/plugins/manifests/harness/template.json",
            {"schema_version": 1, "plugin": "demo-agents/template", "source_roots": [".agents/extra"], "requires": {}},
        )
        self.assert_rejected("source root '.agents/extra' is not shipped in template")

    def test_publication_manifest_roster_is_complete(self) -> None:
        add_publication(self.root, "template", "demo")
        (self.root / ".agents/plugins/manifests/codex/template.json").unlink()
        self.assert_rejected("manifests/codex must hold exactly")

    def test_tier_rules(self) -> None:
        path = self.root / ".agents/tiers/demo.json"
        tier = json.loads(path.read_text())
        write_json(path, {**tier, "applies": "always"})
        self.assert_rejected("declares no detect markers")
        write_json(path, {key: value for key, value in tier.items() if key != "detect"})
        self.assert_rejected("needs at least one detect marker")
        write_json(path, {**tier, "owner_repository": ["owner/other"]})
        self.assert_rejected("owner_repository must name owner/demo")

    def test_manifests_must_agree(self) -> None:
        path = self.root / ".agents/plugins/manifests/claude/demo.json"
        write_json(path, {**json.loads(path.read_text()), "description": "Drifted."})
        self.assert_rejected("disagree on description")

    def test_claude_manifest_omits_version(self) -> None:
        path = self.root / ".agents/plugins/manifests/claude/demo.json"
        write_json(path, {**json.loads(path.read_text()), "version": "1.0.0"})
        self.assert_rejected("omits version")

    def test_marketplace_templates_do_not_list_plugins(self) -> None:
        path = self.root / ".agents/plugins/manifests/claude/marketplace.json"
        write_json(path, {**json.loads(path.read_text()), "plugins": []})
        self.assert_rejected("plugin entries are generated")

    def test_pinned_kit_version_must_match_the_generator(self) -> None:
        path = self.root / ".agents/plugins/kit.json"
        write_json(path, {**json.loads(path.read_text()), "kit": "0.0.1"})
        self.assert_rejected("run kit:update")

    def test_byte_order_mark(self) -> None:
        path = self.root / ".agents/demo/contract/style/SKILL.md"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        self.assert_rejected("BOM")


class SynchronizeTests(GeneratorTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_repository(self.root)

    def test_check_reports_missing_stale_and_extra_outputs(self) -> None:
        code, report = self.synchronize(check=True)
        self.assertEqual(1, code)
        self.assertIn("MISSING: plugins/demo/skills/tool/SKILL.md", report)
        self.assertEqual(0, self.synchronize(check=False)[0])
        self.assertEqual(0, self.synchronize(check=True)[0])
        write(self.root / "plugins/demo/INDEX.md", "edited\n")
        write(self.root / "plugins/stale/INDEX.md", "stale\n")
        code, report = self.synchronize(check=True)
        self.assertEqual(1, code)
        self.assertIn("STALE: plugins/demo/INDEX.md", report)
        self.assertIn("EXTRA: plugins/stale/INDEX.md", report)

    def test_write_refuses_a_linked_generated_root(self) -> None:
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        link = self.root / "plugins"
        try:
            if os.name == "nt":
                import _winapi

                _winapi.CreateJunction(outside.name, str(link))
            else:
                link.symlink_to(outside.name, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"cannot create a link here: {error}")
        with self.assertRaisesRegex(ValueError, "link or junction"):
            self.synchronize(check=False)


class CliTests(GeneratorTestCase):
    def run_generator_cli(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / ".agents/sync_generated.py"), "--root", str(self.root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_reserves_continuation_runtime_state(self) -> None:
        make_repository(self.root)
        write(self.root / ".agents/continuation/owner.json", "{}\n")
        write(self.root / ".agents/continuation/events.jsonl", "{}\n")
        write(self.root / ".agents/continuation/locks/foreground.lock", "locked\n")
        write(self.root / ".agents/continuation/scheduler/state.json", "{}\n")
        result = self.run_generator_cli()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse((self.root / "plugins/continuation").exists())
        self.assertNotIn("continuation", (self.root / ".agents/INDEX.md").read_text(encoding="utf-8"))
        self.assertNotIn("continuation", (self.root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))

    def test_rejects_malformed_authored_plugin_directory(self) -> None:
        make_repository(self.root)
        write(self.root / ".agents/authored/owner.json", "{}\n")
        result = self.run_generator_cli()
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn(".agents/authored/owner.json: only kind folders belong in a plugin folder", result.stdout)


class PackagedScriptsTests(unittest.TestCase):
    def test_each_copied_package_runs_from_its_adapter_resources(self) -> None:
        for name in ("kit", "template"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                package = Path(directory) / name
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
                        directory,
                        "--author",
                        "Ada Lovelace",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(0, new_plugin.returncode, new_plugin.stdout + new_plugin.stderr)
                example = Path(directory) / "example"
                adapter_check = package / "skills/check/scripts/check.py"
                canonical_check = package / ".agents/kit/utility/check/scripts/check.py"
                check = subprocess.run(
                    [sys.executable, "-B", str(adapter_check), "--root", str(example)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(0, check.returncode, check.stdout + check.stderr)
                gitignore = example / ".gitignore"
                gitignore.write_text(gitignore.read_text(encoding="utf-8") + "local/\n", encoding="utf-8")
                drifted = subprocess.run(
                    [sys.executable, "-B", str(adapter_check), "--root", str(example)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(1, drifted.returncode)
                self.assertIn(".gitignore: differs from release", drifted.stderr)
                update = subprocess.run(
                    [sys.executable, "-B", str(package / "skills/update/scripts/update.py"), "--root", str(example)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(0, update.returncode, update.stdout + update.stderr)
                canonical = subprocess.run(
                    [sys.executable, "-B", str(canonical_check), "--root", str(example)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(0, canonical.returncode, canonical.stdout + canonical.stderr)


class KitRepositoryTests(unittest.TestCase):
    def test_kit_generated_outputs_are_current(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, sync_generated.synchronize(ROOT, check=True))


if __name__ == "__main__":
    unittest.main()
