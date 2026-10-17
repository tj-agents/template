from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
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

    def step(self, job: str, name: str) -> str:
        start = job.index(f"      - name: {name}\n")
        end = job.find("      - ", start + 1)
        return job[start:end] if end != -1 else job[start:]

    def assert_generation_precedes(self, job: str, following: str) -> None:
        generate = self.step(job, "regenerate generated files from authored sources")
        current = self.step(job, "generated files are current")
        self.assertLess(job.index(generate), job.index(current))
        self.assertLess(job.index(current), job.index(following))
        self.assertIn("if: inputs.generate_before_verify", generate)
        self.assertIn("./.agents/sync-generated.ps1\n          if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }", generate)
        self.assertNotIn("if:", current)
        self.assertIn("./.agents/sync-generated.ps1 -Check\n          if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }", current)

    def test_reusable_generation_defaults_to_off(self) -> None:
        inputs = self.plugin_ci[:self.plugin_ci.index("    secrets:")]
        self.assertIn(
            "      template_ref:\n        description: Template source ref; defaults to main and may be overridden for candidate checks.\n        required: false\n        default: main\n        type: string",
            inputs,
        )
        self.assertIn(
            "      generate_before_verify:\n        required: false\n        default: false\n        type: boolean",
            inputs,
        )

    def test_verify_and_hosts_regenerate_before_acceptance(self) -> None:
        verify = self.job("verify", self.plugin_ci, "hosts")
        hosts = self.job("hosts", self.plugin_ci)
        self.assertIn("matrix:\n        os: [ubuntu-latest, windows-latest]", verify)
        self.assertIn("ref: ${{ inputs.template_ref }}", verify)
        self.assert_generation_precedes(verify, "- name: repository tests")
        self.assertLess(verify.index("- name: generated files are current"), verify.index("- name: the repository conforms"))
        self.assert_generation_precedes(hosts, "- name: Claude Code and Codex accept")
        self.assertIn("ref: ${{ inputs.template_ref }}", hosts)
        self.assertIn("repository: ${{ inputs.template_repository }}", verify)
        self.assertIn("repository: ${{ inputs.template_repository }}", hosts)

    def test_regeneration_is_main_push_only_and_uses_the_verified_head(self) -> None:
        self.assertIn("push:\n    branches: [main]", self.ci)
        self.assertIn("pull_request:", self.ci)
        regenerate = self.job("regenerate", self.ci)
        self.assertIn("if: github.event_name == 'push'", regenerate)
        self.assertIn("needs: verify", regenerate)
        self.assertIn("ref: ${{ github.sha }}", regenerate)
        self.assertIn("group: regenerate-main", regenerate)
        self.assertIn("cancel-in-progress: false", regenerate)
        self.assertIn("generate_before_verify: true", self.job("verify", self.ci, "regenerate"))
        self.assertIn("template_repository: ${{ github.repository }}", self.job("verify", self.ci, "regenerate"))

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
        self.assertIn("git ls-remote --exit-code origin refs/heads/main", regenerate)
        self.assertLess(regenerate.index("git ls-remote --exit-code origin refs/heads/main"), regenerate.index("git add --"))
        self.assertIn("$PSNativeCommandUseErrorActionPreference = $false", regenerate)
        self.assertIn("$PSNativeCommandUseErrorActionPreference = $nativeErrorActionPreference", regenerate)


class RegenerationPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.remote = self.root / "remote.git"
        self.repository = self.root / "repository"
        self.git(self.root, "init", "--bare", str(self.remote))
        self.git(self.root, "init", str(self.repository))
        self.git(self.repository, "checkout", "-b", "main")
        self.git(self.repository, "config", "user.name", "Fixture")
        self.git(self.repository, "config", "user.email", "fixture@example.com")
        for relative in (
            ".codex/skills/placeholder.txt",
            ".claude/skills/placeholder.txt",
            ".agents/INDEX.md",
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
            "plugins/demo/INDEX.md",
        ):
            path = self.repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("baseline\n", encoding="utf-8")
        (self.repository / "source.txt").write_text("source\n", encoding="utf-8")
        self.git(self.repository, "add", ".")
        self.git(self.repository, "commit", "-m", "source")
        self.git(self.repository, "remote", "add", "origin", str(self.remote))
        self.git(self.repository, "push", "-u", "origin", "HEAD:main")
        self.source = self.git(self.repository, "rev-parse", "HEAD").stdout.strip()
        self.publisher = self.publisher_script(CI.read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        self.directory.cleanup()

    def git(self, directory: Path, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *arguments],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def publisher_script(self, workflow: str) -> str:
        regenerate = PluginCiGenerationTests().job("regenerate", workflow)
        publisher = PluginCiGenerationTests().step(regenerate, "commit and push the regeneration")
        body = publisher.split("        run: |\n", 1)[1]
        return "\n".join(line.removeprefix("          ") for line in body.splitlines())

    def remote_tip(self) -> str:
        return self.git(self.root, f"--git-dir={self.remote}", "rev-parse", "refs/heads/main").stdout.strip()

    def change_generated_output(self) -> None:
        (self.repository / "plugins/demo/INDEX.md").write_text("generated\n", encoding="utf-8")

    def run_publisher(self) -> subprocess.CompletedProcess:
        environment = os.environ | {"GITHUB_SHA": self.source}
        return subprocess.run(
            ["pwsh", "-NoProfile", "-Command", self.publisher],
            cwd=self.repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
        )

    def advance_main(self, name: str) -> str:
        advance = self.root / name
        self.git(self.root, "clone", "--branch", "main", str(self.remote), str(advance))
        self.git(advance, "config", "user.name", "Advance")
        self.git(advance, "config", "user.email", "advance@example.com")
        (advance / "advance.txt").write_text("advance\n", encoding="utf-8")
        self.git(advance, "add", "advance.txt")
        self.git(advance, "commit", "-m", "advance main")
        self.git(advance, "push", "origin", "HEAD:main")
        return self.remote_tip()

    def install_hook(self, location: Path, name: str, body: str) -> None:
        hook = (location / "hooks" if (location / "HEAD").is_file() else location / ".git/hooks") / name
        hook.write_text(body, encoding="utf-8", newline="\n")
        hook.chmod(hook.stat().st_mode | stat.S_IXUSR)

    def test_current_source_publishes_generated_scope_with_the_source_parent(self) -> None:
        self.change_generated_output()
        result = self.run_publisher()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        published = self.remote_tip()
        self.assertEqual(self.source, self.git(self.root, f"--git-dir={self.remote}", "rev-parse", f"{published}^").stdout.strip())
        self.assertEqual(
            ["plugins/demo/INDEX.md"],
            self.git(self.root, f"--git-dir={self.remote}", "diff-tree", "--no-commit-id", "--name-only", "-r", published).stdout.splitlines(),
        )
        self.assertEqual(
            f"Regenerate packages for {self.source}",
            self.git(self.root, f"--git-dir={self.remote}", "log", "-1", "--format=%s", published).stdout.strip(),
        )

    def test_preexisting_newer_main_skips_publication_before_staging(self) -> None:
        advanced = self.advance_main("preexisting")
        self.change_generated_output()
        result = self.run_publisher()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(advanced, self.remote_tip())
        self.assertEqual(self.source, self.git(self.repository, "rev-parse", "HEAD").stdout.strip())
        self.assertEqual(" M plugins/demo/INDEX.md", self.git(self.repository, "status", "--short").stdout.rstrip())

    def test_main_advance_during_push_skips_superseded_publication(self) -> None:
        advance = self.root / "race"
        self.git(self.root, "clone", "--branch", "main", str(self.remote), str(advance))
        self.git(advance, "config", "user.name", "Advance")
        self.git(advance, "config", "user.email", "advance@example.com")
        location = advance.as_posix()
        self.install_hook(
            self.repository,
            "pre-push",
            "#!/bin/sh\n"
            f"printf advance > '{location}/advance.txt'\n"
            f"git -C '{location}' add advance.txt\n"
            f"git -C '{location}' commit -m 'advance main'\n"
            f"git -C '{location}' push origin HEAD:main\n",
        )
        self.change_generated_output()
        result = self.run_publisher()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertNotEqual(self.source, self.remote_tip())
        self.assertEqual("advance main", self.git(self.root, f"--git-dir={self.remote}", "log", "-1", "--format=%s", "refs/heads/main").stdout.strip())

    def test_rejected_push_preserves_the_original_failure_when_main_is_unchanged(self) -> None:
        self.install_hook(self.remote, "pre-receive", "#!/bin/sh\nexit 1\n")
        self.change_generated_output()
        result = self.run_publisher()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(self.source, self.remote_tip())


if __name__ == "__main__":
    unittest.main()
