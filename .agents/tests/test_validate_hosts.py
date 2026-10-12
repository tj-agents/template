from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("validate_hosts", ROOT / ".github/scripts/validate_hosts.py")
validate_hosts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_hosts)


class PublicCorpusWorkflowTests(unittest.TestCase):
    def test_public_inventory_does_not_require_caller_owned_stack_repositories(self):
        workflow = (ROOT / ".github/workflows/plugin-ci.yml").read_text(encoding="utf-8")
        repositories = [line.strip().removeprefix("repository: ") for line in workflow.splitlines()
                        if line.strip().startswith("repository:")]
        public_stacks = {name for name in repositories if name.endswith(("/react", "/dotnet"))}
        self.assertEqual({"tj-agents/react", "tj-agents/dotnet"}, public_stacks)


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


class CodexStandaloneInstallTests(unittest.TestCase):
    def test_each_publication_uses_a_separate_home_and_accepts_only_itself(self) -> None:
        selected = {}
        homes = []

        def fake_run(command, environment=None):
            home = environment["CODEX_HOME"]
            homes.append((home, command))
            if command[:3] == ["codex", "plugin", "add"]:
                selected[home] = command[3].split("@", 1)[0]
                return subprocess.CompletedProcess(command, 0, "", "")
            if command == ["codex", "plugin", "list", "--json"]:
                report = {"installed": [{"name": selected[home], "installed": True, "enabled": True, "marketplaceName": "demo-agents"}]}
                return subprocess.CompletedProcess(command, 0, json.dumps(report), "")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marketplace = root / ".agents/plugins/marketplace.json"
            marketplace.parent.mkdir(parents=True)
            marketplace.write_text(json.dumps({"name": "demo-agents", "plugins": [{"name": "demo"}, {"name": "template"}]}), encoding="utf-8")
            original = validate_hosts.run
            try:
                validate_hosts.run = fake_run
                self.assertEqual([], validate_hosts.validate_codex(root))
            finally:
                validate_hosts.run = original
        installs = [(home, command[3].split("@", 1)[0]) for home, command in homes if command[:3] == ["codex", "plugin", "add"]]
        self.assertEqual(["demo", "template"], [name for _, name in installs])
        self.assertEqual(2, len({home for home, _ in installs}))

    def test_an_implicit_second_install_is_rejected(self) -> None:
        def fake_run(command, environment=None):
            if command == ["codex", "plugin", "list", "--json"]:
                report = {"installed": [
                    {"name": "demo", "installed": True, "enabled": True, "marketplaceName": "demo-agents"},
                    {"name": "template", "installed": True, "enabled": True, "marketplaceName": "demo-agents"},
                ]}
                return subprocess.CompletedProcess(command, 0, json.dumps(report), "")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marketplace = root / ".agents/plugins/marketplace.json"
            marketplace.parent.mkdir(parents=True)
            marketplace.write_text(json.dumps({"name": "demo-agents", "plugins": [{"name": "demo"}]}), encoding="utf-8")
            original = validate_hosts.run
            try:
                validate_hosts.run = fake_run
                self.assertEqual(["codex standalone install of demo enabled ['demo', 'template']"], validate_hosts.validate_codex(root))
            finally:
                validate_hosts.run = original


if __name__ == "__main__":
    unittest.main()
