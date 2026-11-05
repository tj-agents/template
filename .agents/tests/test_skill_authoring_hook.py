import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "plugins" / "skill"
HOOK = PACKAGE / "hooks" / "pretooluse" / "claude" / "skill_authoring.py"


class SkillAuthoringHookTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.transcript = self.root / "session.jsonl"
        self.transcript.write_text("", encoding="utf-8")

    def load_procedure(self, error: bool = False, procedure: str = "skill:new") -> None:
        records = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_1",
                            "name": "Skill",
                            "input": {"skill": procedure},
                        }
                    ]
                },
            },
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_1",
                            "is_error": error,
                            "content": "Launching skill: " + procedure,
                        }
                    ]
                },
            },
        ]
        self.transcript.write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )

    def run_hook(
        self, tool: str, tool_input: dict[str, str], transcript: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(HOOK)],
            input=json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": tool,
                    "cwd": str(self.root),
                    "transcript_path": (
                        str(self.transcript) if transcript is None else transcript
                    ),
                    "tool_input": tool_input,
                }
            ),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def write(
        self, path: Path, tool: str = "Write"
    ) -> subprocess.CompletedProcess[str]:
        return self.run_hook(tool, {"file_path": str(path), "content": "x"})

    def shell(
        self, command: str, tool: str = "Bash"
    ) -> subprocess.CompletedProcess[str]:
        return self.run_hook(tool, {"command": command})

    def existing(self, relative: str) -> Path:
        path = self.root / relative / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("---\nname: existing\n---\n", encoding="utf-8")
        return path

    def test_a_new_skill_is_refused_until_the_procedure_is_loaded(self) -> None:
        target = self.root / ".agents" / "demo" / "utility" / "fresh" / "SKILL.md"
        refused = self.write(target)
        self.assertEqual(2, refused.returncode)
        self.assertIn("skill:new", refused.stderr)
        self.load_procedure(error=True)
        self.assertEqual(2, self.write(target).returncode)
        self.load_procedure()
        self.assertEqual(0, self.write(target).returncode)

    def test_retired_creation_name_does_not_admit_a_write(self) -> None:
        for procedure in ("template:new-skill", "skill:create"):
            with self.subTest(procedure=procedure):
                self.load_procedure(procedure=procedure)
                self.assertEqual(
                    2, self.write(self.root / "fresh" / "SKILL.md").returncode
                )

    def test_existing_skill_requires_update_for_write_and_edit(self) -> None:
        existing = self.root / "existing" / "SKILL.md"
        existing.parent.mkdir()
        existing.write_text("---\nname: existing\n---\n", encoding="utf-8")
        for tool in ("Write", "Edit", "MultiEdit"):
            with self.subTest(tool=tool):
                self.load_procedure()
                self.assertEqual(2, self.write(existing, tool).returncode)
                self.load_procedure(procedure="skill:update")
                self.assertEqual(0, self.write(existing, tool).returncode)
        self.assertEqual(0, self.write(self.root / "README.md").returncode)

    def test_update_can_create_a_replacement_path_without_creation_alias(self) -> None:
        self.load_procedure(procedure="skill:update")
        self.assertEqual(0, self.write(self.root / "renamed" / "SKILL.md").returncode)

    def test_shell_edit_of_an_existing_skill_requires_update(self) -> None:
        self.existing("present")
        for tool, command in (
            ("Bash", "sed -i s/a/b/ present/SKILL.md"),
            ("Bash", "mkdir -p sub && cd present && sed -i s/a/b/ SKILL.md"),
            ("PowerShell", "Set-Content -Path present\\SKILL.md -Value y"),
        ):
            with self.subTest(command=command):
                self.transcript.write_text("", encoding="utf-8")
                refused = self.shell(command, tool)
                self.assertEqual(2, refused.returncode)
                self.assertIn("skill:update", refused.stderr)
                self.assertIn(str(Path("present") / "SKILL.md"), refused.stderr)
                self.load_procedure()
                self.assertEqual(2, self.shell(command, tool).returncode)
                self.load_procedure(procedure="skill:update")
                self.assertEqual(0, self.shell(command, tool).returncode)

    def test_cd_resolves_later_relative_paths(self) -> None:
        self.existing("sub/present")
        self.load_procedure()
        self.assertEqual(
            2, self.shell("cd sub && sed -i s/a/b/ present/SKILL.md").returncode
        )
        self.assertEqual(0, self.shell("sed -i s/a/b/ present/SKILL.md").returncode)

    def test_shell_creation_requires_new_or_update(self) -> None:
        for tool, command in (
            ("Bash", "cat > fresh/SKILL.md <<'EOF'\n---\nname: don't\n---\nEOF"),
            ("Bash", "echo x > fresh/SKILL.md"),
            ("PowerShell", "'y' | Out-File fresh\\SKILL.md"),
        ):
            with self.subTest(command=command):
                self.transcript.write_text("", encoding="utf-8")
                refused = self.shell(command, tool)
                self.assertEqual(2, refused.returncode)
                self.assertIn("skill:new", refused.stderr)
                self.load_procedure()
                self.assertEqual(0, self.shell(command, tool).returncode)

    def test_inline_code_that_writes_a_skill_is_refused(self) -> None:
        self.assertEqual(
            2,
            self.shell("""python -c "open('x/SKILL.md','w').write('y')" """).returncode,
        )

    def test_reads_are_admitted_without_a_procedure(self) -> None:
        self.existing("x")
        for tool, command in (
            ("Bash", """python -c "print(open('x/SKILL.md').read())" """),
            ("Bash", "cat x/SKILL.md"),
            ("Bash", "grep -n a x/SKILL.md"),
            ("Bash", "git diff -- x/SKILL.md"),
            ("PowerShell", "Get-Content x\\SKILL.md"),
        ):
            with self.subTest(command=command):
                self.assertEqual(0, self.shell(command, tool).returncode)

    def test_moving_or_deleting_a_skill_directory_requires_update(self) -> None:
        self.existing("skilldir/inner")
        (self.root / "a.txt").write_text("a", encoding="utf-8")
        self.assertEqual(0, self.shell("git mv a.txt b.txt").returncode)
        for tool, command in (
            ("Bash", "git mv skilldir other"),
            ("Bash", "rm -rf skilldir"),
            ("PowerShell", "Remove-Item skilldir -Recurse"),
        ):
            with self.subTest(command=command):
                self.load_procedure()
                self.assertEqual(2, self.shell(command, tool).returncode)
                self.load_procedure(procedure="skill:update")
                self.assertEqual(0, self.shell(command, tool).returncode)

    def test_ordinary_shell_command_exits_before_reading_anything(self) -> None:
        for tool in ("Bash", "PowerShell"):
            with self.subTest(tool=tool):
                self.assertEqual(
                    0, self.run_hook(tool, {"command": "ls -la"}, "").returncode
                )

    def test_unreadable_operands_and_malformed_commands_are_admitted(self) -> None:
        long = "a" * 300
        for tool, command in (
            ("Bash", f"rm -rf {long}/b"),
            ("PowerShell", f"Remove-Item {long}\\b -Recurse"),
            ("Bash", 'rm -rf "a\0b"'),
            ("PowerShell", 'Remove-Item "a\0b"'),
            ("Bash", "echo 'unterminated > x/SKILL.md"),
        ):
            with self.subTest(command=command[:40]):
                admitted = self.shell(command, tool)
                self.assertEqual(0, admitted.returncode, admitted.stderr)

    def test_deleting_a_tree_finds_a_deeply_nested_skill(self) -> None:
        self.existing(".agents/demo/utility/family/group/member")
        for tool, command in (
            ("Bash", "rm -rf .agents"),
            ("PowerShell", "Remove-Item .agents -Recurse -Force"),
        ):
            with self.subTest(tool=tool):
                self.assertEqual(2, self.shell(command, tool).returncode)

    def test_powershell_here_string_bodies_are_text(self) -> None:
        self.existing("x")
        body = '$m = @"\nRemove-Item "x\\SKILL.md"; > SKILL.md\n"@\nWrite-Output $m'
        admitted = self.shell(body, "PowerShell")
        self.assertEqual(0, admitted.returncode, admitted.stderr)
        literal = "$m = @'\nit's an example\nRemove-Item x -Recurse\n'@\n"
        self.assertEqual(0, self.shell(literal, "PowerShell").returncode)
        refused = self.shell(body + "\nSet-Content x\\SKILL.md -Value y", "PowerShell")
        self.assertEqual(2, refused.returncode)
        self.assertIn("skill:update", refused.stderr)

    def test_powershell_what_if_changes_nothing(self) -> None:
        self.existing("x")
        for command in (
            "Remove-Item x -Recurse -WhatIf",
            "Move-Item x y -WhatIf",
            "Copy-Item x\\SKILL.md fresh\\SKILL.md -WhatIf",
            "Set-Content x\\SKILL.md -Value y -WhatIf",
        ):
            with self.subTest(command=command):
                self.assertEqual(0, self.shell(command, "PowerShell").returncode)
        self.assertEqual(
            2,
            self.shell(
                "Remove-Item x -Recurse -WhatIf:$false", "PowerShell"
            ).returncode,
        )

    def test_claude_filters_writes_and_starts_shell_hooks(self) -> None:
        manifest = json.loads(
            (PACKAGE / "hooks" / "claude.json").read_text(encoding="utf-8")
        )["hooks"]
        self.assertEqual(["PreToolUse"], list(manifest))
        groups = manifest["PreToolUse"]
        self.assertEqual(
            ["Write", "Edit", "MultiEdit", "Bash", "PowerShell"],
            [group["matcher"] for group in groups],
        )
        for group in groups:
            filters = [hook.get("if") for hook in group["hooks"]]
            expected = (
                group["matcher"] + "(**/SKILL.md)"
                if group["matcher"] in {"Write", "Edit", "MultiEdit"}
                else None
            )
            self.assertEqual([expected], filters)
        self.assertFalse((PACKAGE / "hooks" / "codex.json").exists())


if __name__ == "__main__":
    unittest.main()
