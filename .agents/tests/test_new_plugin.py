from __future__ import annotations

from pathlib import Path
import re
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents/kit/utility/new-plugin"
SCRIPT = SKILL / "scripts/new_plugin.py"
TEMPLATES = SKILL / "templates/repository"
CORE_PAYLOAD_CHECK = ROOT / ".core/plugins/base/hooks/check_tier_payload.py"
PLACEHOLDER = re.compile(r"\{\{[A-Za-z_]+\}\}")
VENDORED = (".agents/sync_generated.py", ".agents/sync-generated.ps1", ".gitattributes", ".gitignore", "CLAUDE.md")
STACK_SKILLS = {
    "knowledge": {"learning", "knowledge", "direction"},
    "contract": {"style", "structure", "domain-design", "errors", "testing", "build", "libraries"},
    "utility": {"scaffold"},
}


def run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", *arguments], capture_output=True, text=True, encoding="utf-8", check=False)


class NewPluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.destination = Path(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def create(self, name: str, kind: str, *extra: str) -> subprocess.CompletedProcess:
        return run(
            str(SCRIPT),
            "--repository", f"owner/{name}",
            "--type", kind,
            "--description", f"The {name} plugin.",
            "--destination", str(self.destination),
            "--author", "Ada Lovelace",
            *extra,
        )

    def skills(self, name: str) -> dict[str, set[str]]:
        found: dict[str, set[str]] = {}
        for path in (self.destination / name / ".agents" / name).glob("*/*/SKILL.md"):
            found.setdefault(path.parent.parent.name, set()).add(path.parent.name)
        return found

    def assert_repository_is_current(self, name: str) -> None:
        repository = self.destination / name
        harness = json.loads((repository / f"plugins/{name}/harness.json").read_text(encoding="utf-8"))
        marketplaces = {entry["id"] for entry in harness["requires"]["marketplaces"]}
        self.assertEqual(f"{name}-agents/{name}", harness["plugin"])
        self.assertIn("base-agents/base", harness["requires"]["plugins"])
        self.assertTrue(all(identity.split("/")[0] in marketplaces for identity in [harness["plugin"], *harness["requires"]["plugins"]]))
        result = run(str(repository / ".agents/sync_generated.py"), "--root", str(repository), "--check")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for path in repository.rglob("*"):
            if path.is_file():
                self.assertEqual([], PLACEHOLDER.findall(path.read_text(encoding="utf-8")), path)
        if CORE_PAYLOAD_CHECK.is_file():
            result = run(str(CORE_PAYLOAD_CHECK), "--root", str(repository))
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_stack_repository_has_the_standard_skills_and_a_detected_tier(self) -> None:
        result = self.create("zig", "stack", "--stack", "Zig", "--detect-file", "build.zig", "--detect-glob", "*.zig")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(STACK_SKILLS, self.skills("zig"))
        tier = (self.destination / "zig/.agents/tiers/zig.json").read_text(encoding="utf-8")
        self.assertIn('"applies": "stack-present"', tier)
        self.assertIn("build.zig", tier)
        structure = (self.destination / "zig/.agents/zig/contract/structure/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## File structure", structure)
        self.assertIn("Ada's agreed Zig project structure", structure)
        self.assert_repository_is_current("zig")

    def test_tool_repository_has_only_the_knowledge_tier(self) -> None:
        self.assertEqual(0, self.create("helix", "tool").returncode)
        self.assertEqual({"knowledge": {"learning", "knowledge", "direction"}}, self.skills("helix"))
        self.assertIn('"applies": "always"', (self.destination / "helix/.agents/tiers/helix.json").read_text())
        self.assert_repository_is_current("helix")

    def test_utility_repository_has_only_its_utility(self) -> None:
        self.assertEqual(0, self.create("tools", "utility", "--skill", "sweep").returncode)
        self.assertEqual({"utility": {"sweep"}}, self.skills("tools"))
        self.assert_repository_is_current("tools")

    def test_vendored_files_match_kit_and_ci_pins_its_release(self) -> None:
        self.assertEqual(0, self.create("helix", "tool").returncode)
        repository = self.destination / "helix"
        for relative in VENDORED:
            self.assertEqual((ROOT / relative).read_bytes(), (repository / relative).read_bytes(), relative)
        ci = (repository / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("uses: owner/kit/.github/workflows/plugin-ci.yml@v1.2.1", ci)
        self.assertIn("kit_ref: v1.2.1", ci)

    def test_refuses_an_existing_repository_and_a_stack_without_markers(self) -> None:
        (self.destination / "zig").mkdir()
        self.assertIn("already exists", self.create("zig", "stack", "--detect-file", "build.zig").stderr)
        self.assertIn("needs --detect-file", self.create("odin", "stack").stderr)
        self.assertIn("only a stack", self.create("helix", "tool", "--detect-file", "x").stderr)

    def test_reserved_core_dependency_namespace_fails_before_writing(self) -> None:
        for flags in ([], ["--dry-run"]):
            with self.subTest(flags=flags):
                result = self.create("base", "utility", "--skill", "sweep", *flags)
                self.assertEqual(2, result.returncode)
                self.assertIn("namespace base is reserved", result.stderr)
                self.assertIn("base-agents/base", result.stderr)
                self.assertEqual([], list(self.destination.iterdir()))

    def test_dry_run_writes_nothing(self) -> None:
        result = self.create("helix", "tool", "--dry-run")
        self.assertEqual(0, result.returncode)
        self.assertIn("helix/.agents/helix/knowledge/learning/SKILL.md", result.stdout.replace("\\", "/"))
        self.assertFalse((self.destination / "helix").exists())


class VendoredSourceTests(unittest.TestCase):
    def test_kit_copies_equal_their_templates(self) -> None:
        for relative in VENDORED:
            self.assertEqual((TEMPLATES / f"{relative}.in").read_bytes(), (ROOT / relative).read_bytes(), relative)


if __name__ == "__main__":
    unittest.main()
