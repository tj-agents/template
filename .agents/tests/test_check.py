from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
NEW_PLUGIN = ROOT / ".agents/kit/utility/new-plugin/scripts/new_plugin.py"
UPDATE = ROOT / ".agents/kit/utility/update/scripts/update.py"


def load(name: str, path: Path):
    loader = SourceFileLoader(name, str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(module)
    return module


check = load("kit_check", ROOT / ".agents/kit/utility/check/scripts/check.py")


def run(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", *arguments], capture_output=True, text=True, encoding="utf-8", check=False)


class RenderedRepositoryTestCase(unittest.TestCase):
    kind = "stack"
    name = "zig"

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        destination = Path(self.directory.name)
        extra = {"stack": ["--detect-file", "build.zig"], "tool": [], "utility": ["--skill", "sweep"]}[self.kind]
        result = run(
            str(NEW_PLUGIN),
            "--repository", f"owner/{self.name}",
            "--type", self.kind,
            "--description", "A plugin.",
            "--destination", str(destination),
            "--author", "Ada Lovelace",
            *extra,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.root = destination / self.name

    def tearDown(self) -> None:
        self.directory.cleanup()

    def edit(self, relative: str, old: str, new: str) -> None:
        path = self.root / relative
        content = path.read_text(encoding="utf-8")
        self.assertIn(old, content)
        path.write_text(content.replace(old, new, 1), encoding="utf-8", newline="\n")

    def regenerate(self) -> None:
        result = run(str(self.root / ".agents/sync_generated.py"), "--root", str(self.root))
        self.assertEqual(0, result.returncode, result.stdout)

    def assert_problem(self, fragment: str) -> None:
        problems = check.check(self.root)
        self.assertTrue(any(fragment in problem for problem in problems), problems)


class StackCheckTests(RenderedRepositoryTestCase):
    def test_a_new_repository_conforms(self) -> None:
        self.assertEqual([], check.check(self.root))

    def test_missing_required_skill(self) -> None:
        for path in sorted((self.root / ".agents/zig/contract/errors").rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
        (self.root / ".agents/zig/contract/errors").rmdir()
        self.edit(".agents/zig/knowledge/learning/SKILL.md", "`zig:errors`, ", "")
        self.assert_problem("errors: a stack repository needs this contract skill in plugin zig")

    def test_missing_required_section(self) -> None:
        self.edit(".agents/zig/contract/structure/SKILL.md", "## File structure", "## Layout")
        self.assert_problem("missing section ## File structure")

    def test_wrong_standard_profile(self) -> None:
        self.edit(".agents/zig/contract/style/SKILL.md", "profile: core", "profile: contract")
        self.assert_problem("style is kind contract, profile core")

    def test_contract_without_owns_line(self) -> None:
        self.edit(".agents/zig/contract/build/SKILL.md", "Owns the toolchain pin", "Covers the toolchain pin")
        self.assert_problem("opens with an `Owns …` line")

    def test_drifted_vendored_file(self) -> None:
        self.edit(".gitignore", ".worktrees/\n", ".worktrees/\nlocal/\n")
        self.assert_problem(".gitignore: differs from kit")

    def test_other_pinned_release(self) -> None:
        path = self.root / ".agents/plugins/kit.json"
        path.write_text(json.dumps({**json.loads(path.read_text()), "kit": "0.9.0"}), encoding="utf-8")
        self.assert_problem("pins kit 0.9.0; this check is kit 1.0.0: run kit:update")

    def test_retired_and_unknown_entries(self) -> None:
        (self.root / "SOURCE_LAYOUT.md").write_text("old\n", encoding="utf-8")
        (self.root / ".agents/plugins/sources.json").write_text("{}\n", encoding="utf-8")
        (self.root / ".agents/notes.md").write_text("notes\n", encoding="utf-8")
        problems = "\n".join(check.check(self.root))
        for fragment in ("SOURCE_LAYOUT.md: retired", ".agents/plugins/sources.json: retired", ".agents/notes.md: not part"):
            self.assertIn(fragment, problems)
        (self.root / ".agents/docs").mkdir()
        problems = "\n".join(check.check(self.root))
        self.assertIn("SOURCE_LAYOUT.md: retired", problems)
        self.assertIn(".agents/docs: a plugin folder needs at least one skill", problems)

    def test_ci_layout_still_compares_the_ci_caller(self) -> None:
        nested = self.root / ".kit/.agents/kit"
        shutil.copytree(ROOT / ".agents/kit", nested)
        self.edit(".github/workflows/ci.yml", "kit_ref: v1.0.0", "kit_ref: v0.9.0")
        result = run(str(nested / "utility/check/scripts/check.py"), "--root", str(self.root))
        self.assertEqual(1, result.returncode)
        self.assertIn(".github/workflows/ci.yml: differs from kit", result.stderr)

    def test_missing_tier_is_reported(self) -> None:
        (self.root / ".agents/tiers/zig.json").unlink()
        self.assert_problem(".agents/tiers/zig.json: required")

    def test_stack_tier_must_detect_its_stack(self) -> None:
        path = self.root / ".agents/tiers/zig.json"
        tier = json.loads(path.read_text())
        tier.pop("detect")
        path.write_text(json.dumps({**tier, "applies": "always"}, indent=2) + "\n", encoding="utf-8")
        self.assert_problem("a stack repository applies stack-present")

    def test_update_restores_vendored_files_and_the_pin(self) -> None:
        self.edit(".gitignore", ".worktrees/\n", ".worktrees/\nlocal/\n")
        path = self.root / ".agents/plugins/kit.json"
        path.write_text(json.dumps({**json.loads(path.read_text()), "kit": "0.9.0"}, indent=2) + "\n", encoding="utf-8")
        dry = run(str(UPDATE), "--root", str(self.root), "--dry-run")
        self.assertIn("would update .gitignore", dry.stdout)
        self.assertIn("local/", (self.root / ".gitignore").read_text())
        result = run(str(UPDATE), "--root", str(self.root))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("updated .agents/plugins/kit.json", result.stdout)
        self.assertEqual([], check.check(self.root))


class ToolCheckTests(RenderedRepositoryTestCase):
    kind = "tool"
    name = "helix"

    def test_a_new_repository_conforms(self) -> None:
        self.assertEqual([], check.check(self.root))

    def test_learning_keeps_its_calibrate_section(self) -> None:
        self.edit(".agents/helix/knowledge/learning/SKILL.md", "## Calibrate to `helix:knowledge`", "## Calibrate")
        self.assert_problem("missing section ## Calibrate to `helix:knowledge`")


class UtilityCheckTests(RenderedRepositoryTestCase):
    kind = "utility"
    name = "tools"

    def test_a_new_repository_conforms(self) -> None:
        self.assertEqual([], check.check(self.root))

    def test_only_utility_skills(self) -> None:
        skill = self.root / ".agents/tools/knowledge/notes/SKILL.md"
        skill.parent.mkdir(parents=True)
        text = (self.root / ".agents/tools/utility/sweep/SKILL.md").read_text(encoding="utf-8")
        skill.write_text(text.replace("name: sweep", "name: notes").replace("kind: utility", "kind: knowledge"), encoding="utf-8")
        self.regenerate()
        self.assert_problem("a utility repository has only utility skills")


class SeveralPluginsTests(RenderedRepositoryTestCase):
    def test_a_conforming_scaffold_in_one_plugin_is_enough(self) -> None:
        extra = self.root / ".agents/extra"
        scaffold = (self.root / ".agents/zig/utility/scaffold/SKILL.md").read_text(encoding="utf-8")
        (extra / "utility/scaffold").mkdir(parents=True)
        broken = scaffold.replace("## Build and adapt\n", "")
        (extra / "utility/scaffold/SKILL.md").write_text(broken, encoding="utf-8")
        tier = json.loads((self.root / ".agents/tiers/zig.json").read_text())
        (self.root / ".agents/tiers/extra.json").write_text(json.dumps({**tier, "tier": "extra"}), encoding="utf-8")
        for host in ("claude", "codex"):
            source = json.loads((self.root / f".agents/plugins/manifests/{host}/zig.json").read_text())
            (self.root / f".agents/plugins/manifests/{host}/extra.json").write_text(json.dumps({**source, "name": "extra"}), encoding="utf-8")
        payloads = {"payloads": {"zig": ["zig"], "extra": ["extra"]}}
        (self.root / ".agents/plugins/payloads.json").write_text(json.dumps(payloads), encoding="utf-8")
        self.regenerate()
        self.assertEqual([], check.check(self.root))


class KitConformsTests(unittest.TestCase):
    def test_kit_conforms_to_itself(self) -> None:
        self.assertEqual([], check.check(ROOT))

    def test_kit_conforms_when_checked_from_a_nested_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            nested = Path(directory) / ".agents/kit"
            shutil.copytree(ROOT / ".agents/kit", nested)
            result = run(str(nested / "utility/check/scripts/check.py"), "--root", str(ROOT))
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
