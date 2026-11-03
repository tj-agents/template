import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "plugins" / "template"
HOOK = PACKAGE / "hooks" / "pretooluse" / "claude" / "send_feedback.py"


class SendFeedbackHookTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.transcript = Path(directory.name) / "session.jsonl"
        self.transcript.write_text("", encoding="utf-8")

    def load(self, procedure: str, error: bool = False) -> None:
        use = {"type": "tool_use", "id": "toolu_1", "name": "Skill"}
        result = {"type": "tool_result", "tool_use_id": "toolu_1", "is_error": error}
        records = [
            {"message": {"content": [{**use, "input": {"skill": procedure}}]}},
            {"message": {"content": [result]}},
        ]
        self.transcript.write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )

    def send(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(HOOK)],
            input=json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "SendFeedback",
                    "transcript_path": str(self.transcript),
                    "tool_input": {"feedback": "x"},
                }
            ),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_host_feedback_requires_self_repair(self) -> None:
        refused = self.send()
        self.assertEqual(2, refused.returncode)
        self.assertIn("template:self-repair", refused.stderr)
        self.load("skill:update")
        self.assertEqual(2, self.send().returncode)
        self.load("template:self-repair", error=True)
        self.assertEqual(2, self.send().returncode)
        self.load("template:self-repair")
        self.assertEqual(0, self.send().returncode)

    def test_claude_starts_the_hook_only_for_host_feedback(self) -> None:
        manifest = json.loads(
            (PACKAGE / "hooks" / "claude.json").read_text(encoding="utf-8")
        )["hooks"]
        self.assertEqual(["PreToolUse"], list(manifest))
        self.assertEqual(
            ["SendFeedback"], [group["matcher"] for group in manifest["PreToolUse"]]
        )
        self.assertFalse((PACKAGE / "hooks" / "codex.json").exists())


if __name__ == "__main__":
    unittest.main()
