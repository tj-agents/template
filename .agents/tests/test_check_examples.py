import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / ".agents/template/utility/check/scripts/check_examples.py"


class ExampleCheckerTests(unittest.TestCase):
    root: Path
    base: str

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory[str](prefix="example-checker-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Example Checker")
        self.git("config", "user.email", "examples@example.invalid")
        self.write("README.md", "base\n")
        self.commit()
        self.base = self.git("rev-parse", "HEAD").stdout.strip()

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            check=True,
            text=True,
            capture_output=True,
        )

    def write(self, relative: str, content: str) -> None:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def commit(self) -> None:
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture")

    def check(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(CHECKER), "--root", str(self.root), *arguments],
            text=True,
            capture_output=True,
        )

    @staticmethod
    def skill(body: str) -> str:
        return "---\nname: example\n---\n" + body

    def test_added_modified_and_renamed_guidance_requires_real_examples(self) -> None:
        relative = ".agents/example/convention/example/SKILL.md"
        self.write(
            relative,
            self.skill("# Rule\n\n```text\nInput: source\nOutput: result\n```\n"),
        )
        self.commit()
        self.assertEqual(0, self.check("--base", self.base).returncode)
        first = self.git("rev-parse", "HEAD").stdout.strip()

        self.write(relative, self.skill("# Rule\n\nNo demonstration.\n"))
        self.commit()
        failed = self.check("--base", first)
        self.assertEqual(1, failed.returncode)
        self.assertIn(relative, failed.stderr)
        second = self.git("rev-parse", "HEAD").stdout.strip()

        renamed = ".agents/example/convention/renamed/SKILL.md"
        (self.root / renamed).parent.mkdir(parents=True, exist_ok=True)
        self.git("mv", relative, renamed)
        self.commit()
        self.assertEqual(1, self.check("--base", second).returncode)

    def test_deleted_and_unchanged_guidance_do_not_require_retrofit(self) -> None:
        relative = ".agents/example/convention/old/SKILL.md"
        self.write(relative, self.skill("# Old\n"))
        self.commit()
        unchanged = self.git("rev-parse", "HEAD").stdout.strip()
        self.write("README.md", "changed\n")
        self.commit()
        self.assertEqual(0, self.check("--base", unchanged).returncode)
        before_delete = self.git("rev-parse", "HEAD").stdout.strip()
        (self.root / relative).unlink()
        self.commit()
        self.assertEqual(0, self.check("--base", before_delete).returncode)

    def test_empty_placeholder_and_structural_fences_fail(self) -> None:
        cases = {
            "frontmatter": "---\nexample: ```text\nInput: not body\n```\n---\n# Rule\n",
            "empty": self.skill("# Rule\n\n```text\n\n```\n"),
            "placeholder": self.skill("# Rule\n\n```bash\n# TODO\n...\n```\n"),
            "structural": self.skill(
                "# Rule\n\n```json\n"
                '{"schema_version": 1, "shared_source": "x", "hosts": []}\n```\n'
            ),
            "coverage": self.skill(
                "# Rule\n\n```json agent-host-coverage\n"
                '{"schema_version": 1, "shared_source": "x", "hosts": []}\n```\n'
            ),
            "completion": self.skill(
                "# Rule\n\n```json\n"
                '{"schema_version": 1, "candidate_head": "abc", '
                '"completion": true}\n```\n'
            ),
            "comments": self.skill(
                "# Rule\n\n```text\n/* TODO */\n<!-- TBD -->\n```\n"
            ),
            "multiline-block": self.skill("# Rule\n\n```text\n/*\nTODO\n*/\n```\n"),
            "multiline-html": self.skill("# Rule\n\n```text\n<!--\nTBD\n-->\n```\n"),
        }
        for name, body in cases.items():
            with self.subTest(name=name):
                relative = f".agents/example/convention/{name}/SKILL.md"
                self.write(relative, body)
                self.assertEqual(1, self.check("--path", relative).returncode)

    def test_nonempty_backtick_and_tilde_fences_are_examples(self) -> None:
        for name, fence in (("ticks", "```"), ("tildes", "~~~~")):
            with self.subTest(name=name):
                relative = f".agents/example/convention/{name}/SKILL.md"
                self.write(
                    relative,
                    self.skill(
                        f"# Rule\n\n{fence}text\n"
                        f"Input: source\nOutput: result\n{fence}\n"
                    ),
                )
                self.assertEqual(0, self.check("--path", relative).returncode)

    def test_meaningful_comment_and_directive_examples_pass(self) -> None:
        examples = {
            "slash": "// Explain why this is safe",
            "block": "/* Explain why this is safe */",
            "html": "<!-- Explain why this is safe -->",
            "heading": "# Example heading",
            "cpp": "#include <vector>",
            "csharp": "#nullable enable",
        }
        for name, content in examples.items():
            with self.subTest(name=name):
                relative = f".agents/example/convention/{name}/SKILL.md"
                self.write(relative, self.skill(f"# Rule\n\n```text\n{content}\n```\n"))
                self.assertEqual(0, self.check("--path", relative).returncode)

    def test_template_namespace_and_real_json_configuration_are_examples(self) -> None:
        relative = ".agents/template/utility/check/SKILL.md"
        self.write(
            relative, self.skill('# Check\n\n```json\n{"host": "localhost"}\n```\n')
        )
        self.assertEqual(0, self.check("--path", relative).returncode)

    def test_nested_assets_are_excluded_but_fixtures_namespace_is_checked(self) -> None:
        self.write(
            ".agents/example/convention/real/templates/SKILL.md",
            self.skill("# Generated\n"),
        )
        self.write(
            ".agents/example/convention/real/resources/SKILL.md",
            self.skill("# Resource\n"),
        )
        self.write(
            ".agents/example/convention/real/fixtures/SKILL.md",
            self.skill("# Fixture\n"),
        )
        self.write(
            ".agents/fixtures/convention/check/SKILL.md",
            self.skill("# Plugin namespace\n"),
        )
        self.commit()
        failed = self.check("--base", self.base)
        self.assertEqual(1, failed.returncode)
        self.assertIn(".agents/fixtures/convention/check/SKILL.md", failed.stderr)

    def test_changed_root_code_conventions_requires_an_example(self) -> None:
        self.write("CODE_CONVENTIONS.md", "# Code conventions\n\nUse clear names.\n")
        self.commit()
        failed = self.check("--base", self.base)
        self.assertEqual(1, failed.returncode)
        self.assertIn("CODE_CONVENTIONS.md", failed.stderr)

    def test_installed_checker_runs_against_a_consumer(self) -> None:
        package = self.root / "installed-template" / "skills" / "check"
        shutil.copytree(ROOT / "plugins/template/skills/check", package)
        helper = package / "scripts/check_examples.py"
        self.assertTrue(helper.is_file())
        consumer = self.root / "consumer"
        consumer.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=consumer, check=True)
        (consumer / "RULES.md").write_text(
            "# Rules\n\n```text\nInput: change\nOutput: reviewed\n```\n",
            encoding="utf-8",
        )
        passed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(helper),
                "--root",
                str(consumer),
                "--path",
                "RULES.md",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, passed.returncode, passed.stderr)
        (consumer / "RULES.md").write_text("# Rules\n\nNo example.\n", encoding="utf-8")
        failed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(helper),
                "--root",
                str(consumer),
                "--path",
                "RULES.md",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(1, failed.returncode)
        self.assertIn("RULES.md", failed.stderr)

    def test_example_fenced_inside_html_comment_does_not_count(self) -> None:
        relative = ".agents/example/convention/commented/SKILL.md"
        self.write(
            relative, self.skill("# Rule\n\n<!--\n```text\nInput: hidden\n```\n-->\n")
        )
        self.assertEqual(1, self.check("--path", relative).returncode)

    def test_explicit_paths_check_working_tree_and_support_root_standards(self) -> None:
        self.write(
            "SOURCE_LAYOUT.md",
            "# Layout\n\n```text\nInput: source\nOutput: package\n```\n",
        )
        self.assertEqual(0, self.check("--path", "SOURCE_LAYOUT.md").returncode)
        self.write(
            "RULES.md", "# Rules\n\n```text\nInput: change\nOutput: verified\n```\n"
        )
        self.assertEqual(0, self.check("--path", "RULES.md").returncode)
        for path in ("missing.md", "../outside.md", "fixtures/RULES.md"):
            with self.subTest(path=path):
                self.assertEqual(1, self.check("--path", path).returncode)

    def test_invalid_base_fails_closed_and_zero_base_checks_initial_guidance(
        self,
    ) -> None:
        self.write(
            "AGENTS.md", "# Guidance\n\n```text\nInput: change\nOutput: action\n```\n"
        )
        self.commit()
        self.assertEqual(1, self.check("--base", "not-a-commit").returncode)
        self.assertEqual(0, self.check("--base", "0" * 40).returncode)
