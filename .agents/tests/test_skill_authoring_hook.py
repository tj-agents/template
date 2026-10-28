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

    def write(
        self, path: Path, tool: str = "Write"
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(HOOK)],
            input=json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": tool,
                    "cwd": str(self.root),
                    "transcript_path": str(self.transcript),
                    "tool_input": {"file_path": str(path), "content": "x"},
                }
            ),
            capture_output=True,
            text=True,
            timeout=30,
        )

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

    def test_claude_starts_the_hook_only_for_skill_writes(self) -> None:
        manifest = json.loads(
            (PACKAGE / "hooks" / "claude.json").read_text(encoding="utf-8")
        )["hooks"]
        self.assertEqual(["PreToolUse"], list(manifest))
        for group, tool in zip(
            manifest["PreToolUse"], ("Write", "Edit", "MultiEdit"), strict=True
        ):
            self.assertEqual(tool, group["matcher"])
            self.assertEqual(
                [tool + "(**/SKILL.md)"], [hook["if"] for hook in group["hooks"]]
            )
        self.assertFalse((PACKAGE / "hooks" / "codex.json").exists())


if __name__ == "__main__":
    unittest.main()
