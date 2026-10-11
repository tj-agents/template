from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_CI = ROOT / ".github/workflows/plugin-ci.yml"
CI = ROOT / ".github/workflows/ci.yml"


class PluginCiGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plugin_ci = PLUGIN_CI.read_text(encoding="utf-8")
        self.ci = CI.read_text(encoding="utf-8")

    def job(self, name: str, workflow: str, next_name: str | None = None) -> str:
        start = workflow.index(f"  {name}:\n")
        end = workflow.index(f"  {next_name}:\n", start) if next_name else len(workflow)
        return workflow[start:end]

    def assert_generation_precedes(self, job: str, following: str) -> None:
        generate = job.index("- name: regenerate generated files from authored sources")
        current = job.index("- name: generated files are current")
        acceptance = job.index(following)
        self.assertLess(generate, current)
        self.assertLess(current, acceptance)
        self.assertIn("./.agents/sync-generated.ps1\n          if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }", job)
        self.assertIn("./.agents/sync-generated.ps1 -Check\n          if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }", job)

    def test_verify_and_hosts_regenerate_before_acceptance(self) -> None:
        verify = self.job("verify", self.plugin_ci, "hosts")
        hosts = self.job("hosts", self.plugin_ci)
        self.assertIn("matrix:\n        os: [ubuntu-latest, windows-latest]", verify)
        self.assertIn("ref: ${{ inputs.kit_ref }}", verify)
        self.assert_generation_precedes(verify, "- name: repository tests")
        self.assertLess(verify.index("- name: generated files are current"), verify.index("- name: the repository conforms"))
        self.assert_generation_precedes(hosts, "- name: Claude Code and Codex accept")
        self.assertIn("ref: ${{ inputs.kit_ref }}", hosts)

    def test_regeneration_is_main_push_only_and_uses_the_verified_head(self) -> None:
        self.assertIn("push:\n    branches: [main]", self.ci)
        self.assertIn("pull_request:", self.ci)
        regenerate = self.job("regenerate", self.ci)
        self.assertIn("if: github.event_name == 'push'", regenerate)
        self.assertIn("needs: verify", regenerate)
        self.assertIn("ref: ${{ github.sha }}", regenerate)
        self.assertIn("group: regenerate-main", regenerate)
        self.assertIn("cancel-in-progress: false", regenerate)

    def test_write_permission_and_staging_are_limited_to_regeneration(self) -> None:
        verify = self.job("verify", self.ci, "regenerate")
        regenerate = self.job("regenerate", self.ci)
        self.assertNotIn("permissions:", verify)
        self.assertIn("permissions:\n      contents: write", regenerate)
        staged = re.search(r"git add -- (?P<paths>.+)", regenerate)
        self.assertIsNotNone(staged)
        self.assertEqual(
            {
                ".codex/skills",
                ".claude/skills",
                ".agents/INDEX.md",
                ".agents/plugins/marketplace.json",
                ".claude-plugin/marketplace.json",
                "plugins",
            },
            set(staged.group("paths").split()),
        )
        self.assertIn("git diff --cached --name-only", regenerate)
        self.assertIn("git push origin HEAD:main", regenerate)


if __name__ == "__main__":
    unittest.main()
