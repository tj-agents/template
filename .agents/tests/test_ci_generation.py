import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_CI = ROOT / ".github/workflows/plugin-ci.yml"
CI = ROOT / ".github/workflows/ci.yml"


def job(name: str, workflow: str, next_name: str | None = None) -> str:
    start = workflow.index(f"  {name}:\n")
    end = workflow.index(f"  {next_name}:\n", start) if next_name else len(workflow)
    return workflow[start:end]


def step(job_body: str, name: str) -> str:
    start = job_body.index(f"      - name: {name}\n")
    end = job_body.find("      - ", start + 1)
    return job_body[start:end] if end != -1 else job_body[start:]


def assert_generation_precedes(job_body: str, following: str) -> None:
    generate = step(job_body, "regenerate generated files from authored sources")
    current = step(job_body, "generated files are current")
    assert job_body.index(generate) < job_body.index(current)
    assert job_body.index(current) < job_body.index(following)
    assert "if: inputs.generate_before_verify" in generate
    assert (
        "./.agents/sync-generated.ps1\n"
        "          if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }" in generate
    )
    assert "if:" not in current
    assert (
        "./.agents/sync-generated.ps1 -Check\n"
        "          if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }" in current
    )


@pytest.fixture
def plugin_ci() -> str:
    return PLUGIN_CI.read_text(encoding="utf-8")


@pytest.fixture
def ci() -> str:
    return CI.read_text(encoding="utf-8")


def test_reusable_generation_defaults_to_off(plugin_ci: str) -> None:
    inputs = plugin_ci[: plugin_ci.index("    secrets:")]
    assert (
        "      template_ref:\n"
        "        description: Template source ref; defaults to main and may be "
        "overridden for candidate checks.\n"
        "        required: false\n"
        "        default: main\n"
        "        type: string" in inputs
    )
    assert (
        "      generate_before_verify:\n"
        "        required: false\n"
        "        default: false\n"
        "        type: boolean" in inputs
    )


def test_verify_and_hosts_regenerate_before_acceptance(plugin_ci: str) -> None:
    verify = job("verify", plugin_ci, "hosts")
    hosts = job("hosts", plugin_ci)
    assert "matrix:\n        os: [ubuntu-latest, windows-latest]" in verify
    assert "ref: ${{ inputs.template_ref }}" in verify
    assert_generation_precedes(verify, "- name: repository tests")
    assert verify.index("- name: generated files are current") < verify.index(
        "- name: the repository conforms"
    )
    assert_generation_precedes(hosts, "- name: Claude Code and Codex accept")
    assert "ref: ${{ inputs.template_ref }}" in hosts
    assert "repository: ${{ inputs.template_repository }}" in verify
    assert "repository: ${{ inputs.template_repository }}" in hosts


def test_verify_checks_changed_authored_guidance_against_the_event_base(
    plugin_ci: str,
) -> None:
    verify = job("verify", plugin_ci, "hosts")
    assert "ref: ${{ github.event.pull_request.head.sha || github.sha }}" in verify
    assert "fetch-depth: 0" in verify
    comparison = step(verify, "resolve the authored-guidance comparison range")
    assert "github.event.pull_request.base.sha" in comparison
    assert "github.event.before" in comparison
    assert "GUIDANCE_EXAMPLES_BASE=$base" in comparison
    assert "GUIDANCE_EXAMPLES_HEAD=$head" in comparison
    assert "$mergeBase = '--merge-base'" in comparison
    assert "GUIDANCE_EXAMPLES_MERGE_BASE=$mergeBase" in comparison
    conformance = step(verify, "the repository conforms to the current Template source")
    assert ".template/.agents/template/utility/check/scripts/check.py" in conformance
    assert "'--base', $env:GUIDANCE_EXAMPLES_BASE" in conformance
    assert "'--head', $env:GUIDANCE_EXAMPLES_HEAD" in conformance
    assert "$env:GUIDANCE_EXAMPLES_MERGE_BASE" in conformance
    assert "changed authored guidance has concrete examples" not in verify
    assert (
        ".core/.agents/engineering/convention/docs/scripts/check_examples.py"
        not in verify
    )


@pytest.mark.parametrize("merge_base", ["", "--merge-base"])
def test_conformance_step_passes_only_present_native_arguments(
    plugin_ci: str, tmp_path: Path, merge_base: str
) -> None:
    conformance = step(
        job("verify", plugin_ci, "hosts"),
        "the repository conforms to the current Template source",
    )
    body = conformance.split("        run: |\n", 1)[1]
    command = "\n".join(line.removeprefix("          ") for line in body.splitlines())
    checker = tmp_path / ".template/.agents/template/utility/check/scripts/check.py"
    checker.parent.mkdir(parents=True)
    checker.write_text(
        "import argparse, json\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--root')\n"
        "parser.add_argument('--base')\n"
        "parser.add_argument('--head')\n"
        "parser.add_argument('--merge-base', action='store_true')\n"
        "print(json.dumps(vars(parser.parse_args())))\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", command],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ
        | {
            "GUIDANCE_EXAMPLES_BASE": "base-commit",
            "GUIDANCE_EXAMPLES_HEAD": "head-commit",
            "GUIDANCE_EXAMPLES_MERGE_BASE": merge_base,
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {
        "root": ".",
        "base": "base-commit",
        "head": "head-commit",
        "merge_base": bool(merge_base),
    }


def test_regeneration_is_main_push_only_and_uses_the_verified_head(ci: str) -> None:
    assert "push:\n    branches: [main]" in ci
    assert "pull_request:" in ci
    regenerate = job("regenerate", ci)
    assert "if: github.event_name == 'push'" in regenerate
    assert "needs: verify" in regenerate
    assert "ref: ${{ github.sha }}" in regenerate
    assert "group: regenerate-main" in regenerate
    assert "cancel-in-progress: false" in regenerate
    assert "generate_before_verify: true" in job("verify", ci, "regenerate")
    assert "template_repository: ${{ github.repository }}" in job(
        "verify", ci, "regenerate"
    )


def test_write_permission_and_staging_are_limited_to_regeneration(ci: str) -> None:
    verify = job("verify", ci, "regenerate")
    regenerate = job("regenerate", ci)
    assert "permissions:" not in verify
    assert "permissions:\n      contents: write" in regenerate
    staged = re.search(r"git add -- (?P<paths>.+)", regenerate)
    assert staged is not None
    assert set(staged.group("paths").split()) == {
        ".codex/skills",
        ".claude/skills",
        ".agents/INDEX.md",
        ".agents/plugins/marketplace.json",
        ".claude-plugin/marketplace.json",
        "plugins",
    }
    assert "git diff --cached --name-only" in regenerate
    assert "git push origin HEAD:main" in regenerate
    assert "git ls-remote --exit-code origin refs/heads/main" in regenerate
    assert regenerate.index(
        "git ls-remote --exit-code origin refs/heads/main"
    ) < regenerate.index("git add --")
    assert "$PSNativeCommandUseErrorActionPreference = $false" in regenerate
    assert (
        "$PSNativeCommandUseErrorActionPreference = $nativeErrorActionPreference"
        in regenerate
    )


def git(directory: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def publisher_script(workflow: str) -> str:
    regenerate = job("regenerate", workflow)
    publisher = step(regenerate, "commit and push the regeneration")
    body = publisher.split("        run: |\n", 1)[1]
    return "\n".join(line.removeprefix("          ") for line in body.splitlines())


@dataclass
class PublisherHarness:
    root: Path
    remote: Path
    repository: Path
    source: str
    publisher: str


@pytest.fixture
def harness(tmp_path: Path) -> PublisherHarness:
    root = tmp_path
    remote = root / "remote.git"
    repository = root / "repository"
    git(root, "init", "--bare", str(remote))
    git(root, "init", str(repository))
    git(repository, "checkout", "-b", "main")
    git(repository, "config", "user.name", "Fixture")
    git(repository, "config", "user.email", "fixture@example.com")
    for relative in (
        ".codex/skills/placeholder.txt",
        ".claude/skills/placeholder.txt",
        ".agents/INDEX.md",
        ".agents/plugins/marketplace.json",
        ".claude-plugin/marketplace.json",
        "plugins/demo/INDEX.md",
    ):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("baseline\n", encoding="utf-8")
    (repository / "source.txt").write_text("source\n", encoding="utf-8")
    git(repository, "add", ".")
    git(repository, "commit", "-m", "source")
    git(repository, "remote", "add", "origin", str(remote))
    git(repository, "push", "-u", "origin", "HEAD:main")
    source = git(repository, "rev-parse", "HEAD").stdout.strip()
    publisher = publisher_script(CI.read_text(encoding="utf-8"))
    return PublisherHarness(root, remote, repository, source, publisher)


def remote_tip(harness: PublisherHarness) -> str:
    return git(
        harness.root, f"--git-dir={harness.remote}", "rev-parse", "refs/heads/main"
    ).stdout.strip()


def change_generated_output(harness: PublisherHarness) -> None:
    (harness.repository / "plugins/demo/INDEX.md").write_text(
        "generated\n", encoding="utf-8"
    )


def run_publisher(harness: PublisherHarness) -> subprocess.CompletedProcess[str]:
    environment = os.environ | {"GITHUB_SHA": harness.source}
    return subprocess.run(
        ["pwsh", "-NoProfile", "-Command", harness.publisher],
        cwd=harness.repository,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )


def advance_main(harness: PublisherHarness, name: str) -> str:
    advance = harness.root / name
    git(harness.root, "clone", "--branch", "main", str(harness.remote), str(advance))
    git(advance, "config", "user.name", "Advance")
    git(advance, "config", "user.email", "advance@example.com")
    (advance / "advance.txt").write_text("advance\n", encoding="utf-8")
    git(advance, "add", "advance.txt")
    git(advance, "commit", "-m", "advance main")
    git(advance, "push", "origin", "HEAD:main")
    return remote_tip(harness)


def install_hook(location: Path, name: str, body: str) -> None:
    hook = (
        location / "hooks" if (location / "HEAD").is_file() else location / ".git/hooks"
    ) / name
    hook.write_text(body, encoding="utf-8", newline="\n")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)


def test_current_source_publishes_generated_scope_with_the_source_parent(
    harness: PublisherHarness,
) -> None:
    change_generated_output(harness)
    result = run_publisher(harness)
    assert result.returncode == 0, result.stdout + result.stderr
    published = remote_tip(harness)
    assert (
        harness.source
        == git(
            harness.root, f"--git-dir={harness.remote}", "rev-parse", f"{published}^"
        ).stdout.strip()
    )
    assert git(
        harness.root,
        f"--git-dir={harness.remote}",
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        published,
    ).stdout.splitlines() == ["plugins/demo/INDEX.md"]
    assert (
        git(
            harness.root,
            f"--git-dir={harness.remote}",
            "log",
            "-1",
            "--format=%s",
            published,
        ).stdout.strip()
        == f"Regenerate packages for {harness.source}"
    )


def test_preexisting_newer_main_skips_publication_before_staging(
    harness: PublisherHarness,
) -> None:
    advanced = advance_main(harness, "preexisting")
    change_generated_output(harness)
    result = run_publisher(harness)
    assert result.returncode == 0, result.stdout + result.stderr
    assert remote_tip(harness) == advanced
    assert git(harness.repository, "rev-parse", "HEAD").stdout.strip() == harness.source
    assert (
        git(harness.repository, "status", "--short").stdout.rstrip()
        == " M plugins/demo/INDEX.md"
    )


def test_main_advance_during_push_skips_superseded_publication(
    harness: PublisherHarness,
) -> None:
    advance = harness.root / "race"
    git(harness.root, "clone", "--branch", "main", str(harness.remote), str(advance))
    git(advance, "config", "user.name", "Advance")
    git(advance, "config", "user.email", "advance@example.com")
    location = advance.as_posix()
    install_hook(
        harness.repository,
        "pre-push",
        "#!/bin/sh\n"
        f"printf advance > '{location}/advance.txt'\n"
        f"git -C '{location}' add advance.txt\n"
        f"git -C '{location}' commit -m 'advance main'\n"
        f"git -C '{location}' push origin HEAD:main\n",
    )
    change_generated_output(harness)
    result = run_publisher(harness)
    assert result.returncode == 0, result.stdout + result.stderr
    assert remote_tip(harness) != harness.source
    assert (
        git(
            harness.root,
            f"--git-dir={harness.remote}",
            "log",
            "-1",
            "--format=%s",
            "refs/heads/main",
        ).stdout.strip()
        == "advance main"
    )


def test_rejected_push_preserves_the_original_failure_when_main_is_unchanged(
    harness: PublisherHarness,
) -> None:
    install_hook(harness.remote, "pre-receive", "#!/bin/sh\nexit 1\n")
    change_generated_output(harness)
    result = run_publisher(harness)
    assert result.returncode != 0
    assert remote_tip(harness) == harness.source
