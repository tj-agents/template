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
STUB = (
    ROOT
    / ".agents/template/utility/new/plugin/templates/repository"
    / ".github/workflows/ci.yml.in"
)
REGENERATION_COMMIT = (
    "!startsWith(github.event.head_commit.message, 'Regenerate packages for ')"
)


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
    assert f"if: github.event_name != 'push' || {REGENERATION_COMMIT}" in generate
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


def test_generation_is_not_an_opt_in_and_the_updater_key_is_optional(
    plugin_ci: str,
) -> None:
    inputs = plugin_ci[: plugin_ci.index("    secrets:")]
    secrets = plugin_ci[
        plugin_ci.index("    secrets:") : plugin_ci.index("permissions:")
    ]
    assert (
        "      template_ref:\n"
        "        description: Template source ref; defaults to main and may be "
        "overridden for candidate checks.\n"
        "        required: false\n"
        "        default: main\n"
        "        type: string" in inputs
    )
    assert "generate_before_verify" not in plugin_ci
    assert "      UPDATE_APP_PRIVATE_KEY:\n" in secrets
    key = secrets[secrets.index("      UPDATE_APP_PRIVATE_KEY:\n") :]
    assert "        required: false\n" in key


def test_verify_provisions_the_pinned_tj_hook_candidate(plugin_ci: str) -> None:
    inputs = plugin_ci[: plugin_ci.index("    secrets:")]
    verify = job("verify", plugin_ci, "hosts")
    provision = step(verify, "build the pinned tj_hook candidate")
    assert "default: cd8c726e2aadc321251de599b75c4e72e21cecb9" in inputs
    assert "repository: tj-agents/cli" in verify
    assert "ref: ${{ inputs.cli_ref }}" in verify
    assert "path: .tj-cli" in verify
    assert "persist-credentials: false" in verify
    assert "cargo build --locked --release --bin tj_hook" in provision
    assert "$binaryDirectory >> $env:GITHUB_PATH" in provision
    assert verify.index(provision) < verify.index("- name: repository tests")


def test_verify_and_hosts_regenerate_before_acceptance(plugin_ci: str) -> None:
    verify = job("verify", plugin_ci, "hosts")
    hosts = job("hosts", plugin_ci, "regeneration-unconfigured")
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
    setup_uv = (
        "- uses: astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884 # v10.3.0"
    )
    assert setup_uv in hosts
    assert hosts.index(setup_uv) < hosts.index(
        "- name: regenerate generated files from authored sources"
    )


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


def test_regeneration_publishes_only_unregenerated_main_pushes_after_verification(
    plugin_ci: str,
) -> None:
    regenerate = job("regenerate", plugin_ci)
    condition = regenerate[: regenerate.index("    needs:")]
    assert "github.event_name == 'push' && github.ref == 'refs/heads/main'" in condition
    assert REGENERATION_COMMIT in condition
    assert "vars.UPDATE_APP_CLIENT_ID != ''" in condition
    assert "needs: [verify, hosts]" in regenerate
    assert "environment: update-pins" in regenerate
    assert "group: regenerate-main" in regenerate
    assert "cancel-in-progress: false" in regenerate
    assert "ref: ${{ github.sha }}" in regenerate
    assert "token: ${{ steps.app-token.outputs.token }}" in regenerate
    assert "client-id: ${{ vars.UPDATE_APP_CLIENT_ID }}" in regenerate
    assert "private-key: ${{ secrets.UPDATE_APP_PRIVATE_KEY }}" in regenerate
    assert "permission-contents: write" in regenerate
    assert "permission-workflows" not in regenerate
    assert "contents: write" not in plugin_ci.replace("permission-contents: write", "")
    order = [
        "- name: mint the updater token",
        "- name: regenerate generated files from authored sources",
        "- name: generated files are current",
        "- name: commit and push the regeneration",
    ]
    positions = [regenerate.index(name) for name in order]
    assert positions == sorted(positions)


def test_unconfigured_regeneration_succeeds_with_a_notice(plugin_ci: str) -> None:
    unconfigured = job("regeneration-unconfigured", plugin_ci, "regenerate")
    assert "vars.UPDATE_APP_CLIENT_ID == ''" in unconfigured
    assert REGENERATION_COMMIT in unconfigured
    assert "::notice " in unconfigured
    regenerate = job("regenerate", plugin_ci)
    assert (
        "UPDATE_APP_KEY_PRESENT: ${{ secrets.UPDATE_APP_PRIVATE_KEY != '' }}"
        in regenerate
    )
    missing = step(regenerate, "report skipped publication")
    assert "if: env.UPDATE_APP_KEY_PRESENT != 'true'" in missing
    assert "::notice " in missing
    steps = regenerate[regenerate.index("    steps:\n") :].split("      - ")[1:]
    assert len(steps) > 1
    for later in steps[1:]:
        assert "if: env.UPDATE_APP_KEY_PRESENT == 'true'" in later


def test_callers_pass_the_updater_key_and_template_has_no_second_publisher(
    ci: str,
) -> None:
    passed = "      UPDATE_APP_PRIVATE_KEY: ${{ secrets.UPDATE_APP_PRIVATE_KEY }}\n"
    assert passed in ci
    assert passed in STUB.read_text(encoding="utf-8")
    assert "  regenerate:\n" not in ci
    assert "generate_before_verify" not in ci
    assert "template_repository: ${{ github.repository }}" in job(
        "verify", ci, "system-python-resources"
    )


def test_staging_is_limited_to_generated_roots(plugin_ci: str) -> None:
    regenerate = job("regenerate", plugin_ci)
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
    publisher = publisher_script(PLUGIN_CI.read_text(encoding="utf-8"))
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
