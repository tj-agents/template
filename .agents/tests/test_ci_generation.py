import json
import os
import subprocess
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
    generate = step(job_body, "Regenerate generated files from authored sources")
    current = step(job_body, "Generated files are current")
    assert job_body.index(generate) < job_body.index(current)
    assert job_body.index(current) < job_body.index(following)
    assert f"if: github.event_name != 'push' || {REGENERATION_COMMIT}" in generate
    assert (
        "python -B .template/.agents/template/utility/update/scripts/update.py --root ."
        in generate
    )
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


def test_verification_and_publication_share_one_resolved_template(
    plugin_ci: str,
) -> None:
    resolver = job("resolve-template", plugin_ci, "verify")
    assert "ref: ${{ inputs.template_ref }}" in resolver
    assert "git -C .template rev-parse HEAD" in resolver
    assert "sha: ${{ steps.template.outputs.sha }}" in resolver
    # A moving input ref is resolved once; every consumer uses that same commit.
    assert plugin_ci.count("ref: ${{ inputs.template_ref }}") == 1
    assert plugin_ci.count("ref: ${{ needs.resolve-template.outputs.sha }}") == 3
    for name, following in (
        ("verify", "host-platforms"),
        ("host-platforms", "hosts"),
        ("regenerate", None),
    ):
        consumer = job(name, plugin_ci, following)
        assert "resolve-template" in consumer[: consumer.index("    steps:")]
        assert "ref: ${{ needs.resolve-template.outputs.sha }}" in consumer


def test_checkout_does_not_persist_the_publication_token(plugin_ci: str) -> None:
    steps = plugin_ci.split("      - ")[1:]
    for checkout in (value for value in steps if "uses: actions/checkout@" in value):
        assert "persist-credentials: false" in checkout
    publication = step(job("regenerate", plugin_ci), "Publish generated files")
    assert "token: ${{ steps.app-token.outputs.token }}" in publication
    assert (
        "uses: tj-agents/github-actions/.github/actions/publish-generated@"
        "1a8099ab95aaf609704f892087081c35d15b331a" in publication
    )
    assert "source-sha: ${{ github.sha }}" in publication
    assert "permissions: {}" in job("hosts", plugin_ci, "regeneration-unconfigured")


def test_self_checkout_uses_its_repository_token(plugin_ci: str) -> None:
    checkouts = [
        value
        for value in plugin_ci.split("      - ")
        if "repository: ${{ inputs.template_repository }}" in value
    ]
    assert len(checkouts) == 4
    for checkout in checkouts:
        assert (
            "(inputs.template_repository == github.repository || "
            "inputs.template_repository == 'tj-agents/template') "
            "&& secrets.GITHUB_TOKEN "
            "|| secrets.read_token || secrets.GITHUB_TOKEN" in checkout
        )
    cli = next(
        value
        for value in plugin_ci.split("      - ")
        if "repository: tj-agents/cli" in value
    )
    assert "token: ${{ secrets.GITHUB_TOKEN }}" in cli
    assert "SKILL_REFERENCES_TOKEN: ${{ secrets.GITHUB_TOKEN }}" in plugin_ci


def test_verify_provisions_the_pinned_tj_hook_candidate(plugin_ci: str) -> None:
    inputs = plugin_ci[: plugin_ci.index("    secrets:")]
    verify = job("verify", plugin_ci, "hosts")
    provision = step(verify, "Build the pinned tj_hook candidate")
    assert "default: 92e29a7589a5dcf462af36d960684e49146d9d3b" in inputs
    assert "repository: tj-agents/cli" in verify
    assert "ref: ${{ inputs.cli_ref }}" in verify
    assert "path: .tj-cli" in verify
    assert "persist-credentials: false" in verify
    assert "cargo build --locked --release --bin tj_hook" in provision
    assert "$binaryDirectory >> $env:GITHUB_PATH" in provision
    assert verify.index(provision) < verify.index("- name: Repository tests")


def test_verify_and_hosts_regenerate_before_acceptance(plugin_ci: str) -> None:
    verify = job("verify", plugin_ci, "hosts")
    hosts = job("host-platforms", plugin_ci, "hosts")
    assert "matrix:\n        os: [ubuntu-latest, windows-latest]" in verify
    assert "matrix:\n        os: [ubuntu-latest, windows-latest]" in hosts
    stable_gate = job("hosts", plugin_ci, "regeneration-unconfigured")
    assert "if: always()" in stable_gate
    assert "needs: host-platforms" in stable_gate
    assert 'test "$HOST_RESULT" = success' in stable_gate
    assert '--baseline "$env:UPGRADE_BASE"' in hosts
    assert "uv run --project .template --locked --no-dev python -B" in hosts
    assert "ref: ${{ needs.resolve-template.outputs.sha }}" in verify
    assert_generation_precedes(verify, "- name: Repository tests")
    assert verify.index("- name: Generated files are current") < verify.index(
        "- name: The repository conforms"
    )
    assert_generation_precedes(hosts, "- name: Claude Code and Codex accept")
    assert "ref: ${{ needs.resolve-template.outputs.sha }}" in hosts
    assert "repository: ${{ inputs.template_repository }}" in verify
    assert "repository: ${{ inputs.template_repository }}" in hosts
    setup_uv = (
        "- uses: astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884 # v10.3.0"
    )
    assert setup_uv in hosts
    assert hosts.index(setup_uv) < hosts.index(
        "- name: Regenerate generated files from authored sources"
    )


def test_verify_checks_changed_authored_guidance_against_the_event_base(
    plugin_ci: str,
) -> None:
    verify = job("verify", plugin_ci, "hosts")
    assert "ref: ${{ github.event.pull_request.head.sha || github.sha }}" in verify
    assert "fetch-depth: 0" in verify
    comparison = step(verify, "Resolve the authored-guidance comparison range")
    assert "github.event.pull_request.base.sha" in comparison
    assert "github.event.before" in comparison
    assert "GUIDANCE_EXAMPLES_BASE=$base" in comparison
    assert "GUIDANCE_EXAMPLES_HEAD=$head" in comparison
    assert "$mergeBase = '--merge-base'" in comparison
    assert "GUIDANCE_EXAMPLES_MERGE_BASE=$mergeBase" in comparison
    conformance = step(verify, "The repository conforms to the current Template source")
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
        "The repository conforms to the current Template source",
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
    assert "needs: [resolve-template, verify, hosts]" in regenerate
    assert "    environment: update-pins\n" in regenerate
    assert "group: regenerate-main" in regenerate
    assert "cancel-in-progress: false" in regenerate
    assert "ref: ${{ github.sha }}" in regenerate
    assert "token: ${{ steps.app-token.outputs.token }}" in regenerate
    assert "client-id: ${{ vars.UPDATE_APP_CLIENT_ID }}" in regenerate
    assert "private-key: ${{ secrets.UPDATE_APP_PRIVATE_KEY }}" in regenerate
    assert "permission-contents: write" in regenerate
    assert "permission-workflows: write" in regenerate
    assert "contents: write" not in plugin_ci.replace("permission-contents: write", "")
    order = [
        "- name: Regenerate generated files from authored sources",
        "- name: Generated files are current",
        "- name: Mint the updater token",
        "- name: Publish generated files",
    ]
    positions = [regenerate.index(name) for name in order]
    assert positions == sorted(positions)


def test_unconfigured_regeneration_fails_explicitly(plugin_ci: str) -> None:
    unconfigured = job("regeneration-unconfigured", plugin_ci, "regenerate")
    assert "vars.UPDATE_APP_CLIENT_ID == ''" in unconfigured
    assert REGENERATION_COMMIT in unconfigured
    assert "::error " in unconfigured
    assert "exit 1" in unconfigured
    regenerate = job("regenerate", plugin_ci)
    assert (
        "UPDATE_APP_KEY_PRESENT: ${{ secrets.UPDATE_APP_PRIVATE_KEY != '' }}"
        in regenerate
    )
    missing = step(regenerate, "Require automatic publication credentials")
    assert "if ($env:UPDATE_APP_KEY_PRESENT -ne 'true')" in missing
    assert "Write-Error" in missing
    assert "exit 1" in missing
    steps = regenerate[regenerate.index("    steps:\n") :].split("      - ")[1:]
    assert len(steps) > 1
    for later in steps[1:]:
        assert "if: steps.credentials.outputs.present == 'true'" in later


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


def test_staging_includes_exact_vendored_files_and_generated_roots(
    plugin_ci: str,
) -> None:
    regenerate = job("regenerate", plugin_ci)
    published = step(regenerate, "Publish generated files")
    paths = published.split("          paths: |\n", 1)[1]
    assert {line.strip() for line in paths.splitlines() if line.strip()} == {
        "CLAUDE.md",
        ".agents/sync_generated.py",
        ".github/workflows/ci.yml",
        ".gitattributes",
        ".codex/hooks/snapshot.py",
        ".codex/skills",
        ".codex/hooks/bootstrap.py",
        "plugins",
        ".agents/INDEX.md",
        ".claude/skills",
        ".agents/sync-generated.ps1",
        ".gitignore",
        ".claude-plugin/marketplace.json",
        ".agents/plugins/marketplace.json",
    }
    assert "branch: ${{ github.event.repository.default_branch }}" in published
    assert "git push" not in regenerate
    assert "git add" not in regenerate
