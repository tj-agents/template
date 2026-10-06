from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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


class GeneratorTestCase(unittest.TestCase):
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
        for directory in ("plugins/demo/skills/tool", ".claude/skills/tool", ".codex/skills/tool"):
            self.assertIn(f"{directory}/scripts/run.py", output)
            self.assertIn(f"{directory}/templates/notes.md", output)
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
            self.assertIn(f"plugins/demo/skills/{name}/SKILL.md", output)
            self.assertIn(f".codex/skills/{name}/SKILL.md", output)
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
        self.assert_rejected("does not resolve from generated plugins/demo/skills/style")

    def test_missing_skill_directory_file(self) -> None:
        write(self.root / ".agents/demo/contract/style/SKILL.md", skill_text("style", "contract", "Run `<skill-directory>/scripts/missing.py`.\n"))
        self.assert_rejected("scripts/missing.py does not resolve")

    def test_payloads_must_match_the_plugin_folders(self) -> None:
        write_json(self.root / ".agents/plugins/payloads.json", {"payloads": {"other": ["other"]}})
        self.assert_rejected("payloads must map each plugin folder")

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


class KitRepositoryTests(unittest.TestCase):
    def test_kit_generated_outputs_are_current(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, sync_generated.synchronize(ROOT, check=True))


if __name__ == "__main__":
    unittest.main()
