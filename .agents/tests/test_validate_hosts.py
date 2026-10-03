from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("validate_hosts", ROOT / ".github/scripts/validate_hosts.py")
validate_hosts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_hosts)


class ClaudeReportTests(unittest.TestCase):
    def test_only_the_omitted_version_warning_is_tolerated(self) -> None:
        report = {
            "success": False,
            "manifest": {
                "file": "marketplace.json",
                "errors": [],
                "warnings": [
                    {"path": "plugins[0] plugin.json → version", "message": "No version specified."},
                    {"path": "plugins[0] plugin.json → homepage", "message": "Unrecognized field."},
                ],
            },
            "contents": [{"file": "skills/x/SKILL.md", "errors": [{"path": "name", "message": "Missing name."}], "warnings": []}],
        }
        self.assertEqual(
            [
                "marketplace.json: plugins[0] plugin.json → homepage: Unrecognized field.",
                "skills/x/SKILL.md: name: Missing name.",
            ],
            validate_hosts.problems(report),
        )

    def test_a_plugin_manifest_without_version_passes(self) -> None:
        report = {"manifest": {"file": "plugin.json", "errors": [], "warnings": [{"path": "version", "message": "No version."}]}}
        self.assertEqual([], validate_hosts.problems(report))


if __name__ == "__main__":
    unittest.main()
