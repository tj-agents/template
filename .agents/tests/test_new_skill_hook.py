import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "plugins" / "template"
HOOK = PACKAGE / "hooks" / "pretooluse" / "claude" / "new_skill.py"


class NewSkillHookTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.transcript = self.root / "session.jsonl"
        self.transcript.write_text("", encoding="utf-8")

    def load_procedure(self, error=False):
        records = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_1",
                            "name": "Skill",
                            "input": {"skill": "template:new-skill"},
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
                            "content": "Launching skill: template:new-skill",
                        }
                    ]
                },
            },
        ]
        self.transcript.write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )

    def write(self, path):
        return subprocess.run(
            [sys.executable, "-B", str(HOOK)],
            input=json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Write",
                    "cwd": str(self.root),
                    "transcript_path": str(self.transcript),
                    "tool_input": {"file_path": str(path), "content": "x"},
                }
            ),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_a_new_skill_is_refused_until_the_procedure_is_loaded(self):
        target = self.root / ".agents" / "demo" / "utility" / "fresh" / "SKILL.md"
        refused = self.write(target)
        self.assertEqual(2, refused.returncode)
        self.assertIn("template:new-skill", refused.stderr)
        self.load_procedure(error=True)
        self.assertEqual(2, self.write(target).returncode)
        self.load_procedure()
        self.assertEqual(0, self.write(target).returncode)

    def test_existing_skills_and_other_files_pass_without_the_procedure(self):
        existing = self.root / "existing" / "SKILL.md"
        existing.parent.mkdir()
        existing.write_text("---\nname: existing\n---\n", encoding="utf-8")
        self.assertEqual(0, self.write(existing).returncode)
        self.assertEqual(0, self.write(self.root / "README.md").returncode)

    def test_claude_starts_the_hook_only_for_skill_writes(self):
        manifest = json.loads(
            (PACKAGE / "hooks" / "claude.json").read_text(encoding="utf-8")
        )["hooks"]
        self.assertEqual(["PreToolUse"], list(manifest))
        (group,) = manifest["PreToolUse"]
        self.assertEqual("Write", group["matcher"])
        self.assertEqual(
            ["Write(**/SKILL.md)"], [hook["if"] for hook in group["hooks"]]
        )
        self.assertFalse((PACKAGE / "hooks" / "codex.json").exists())


if __name__ == "__main__":
    unittest.main()
