import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / ".agents/template/utility/check/scripts/check_workflows.py"
VALID = """name: CI
on: push
permissions:
  contents: read
jobs:
  unit-tests:
    name: Run unit tests
    runs-on: ubuntu-latest
    steps:
      - name: Test package
        env:
          TOKEN: ${{ secrets.READ_TOKEN }}
        run: |
          set -euo pipefail
          echo ready
          echo done
"""


def check(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(CHECKER), "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def write(root: Path, content: str, relative: str = ".github/workflows/ci.yml") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_step_secret_and_strict_bash_pass(tmp_path: Path) -> None:
    write(tmp_path, VALID)
    result = check(tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("before", "after", "diagnostic"),
    [
        ("name: CI", "name: ci", "workflow name"),
        ("unit-tests:", "unit_tests:", "job 'unit_tests'"),
        ("name: Run unit tests", "name: run unit tests", "job 'unit-tests' name"),
        ("name: Test package", "name: test package", "step name"),
        ("          set -euo pipefail\n", "", "bash-strict"),
        ("TOKEN:", "token:", "environment variable 'token'"),
        (
            "on: push",
            "on:\n  workflow_dispatch:\n    inputs:\n"
            "      bad_name:\n        type: string",
            "inputs 'bad_name'",
        ),
        (
            "on: push",
            "on:\n  workflow_call:\n    secrets:\n"
            "      bad-name:\n        required: true",
            "secret 'bad-name'",
        ),
    ],
)
def test_workflow_violations_fail_with_source_location(
    tmp_path: Path, before: str, after: str, diagnostic: str
) -> None:
    write(tmp_path, VALID.replace(before, after))
    result = check(tmp_path)
    assert result.returncode == 1
    assert "ci.yml:" in result.stderr
    assert diagnostic in result.stderr


@pytest.mark.parametrize("scope", ["workflow", "job"])
def test_secrets_in_broad_environment_fail(tmp_path: Path, scope: str) -> None:
    if scope == "workflow":
        content = VALID.replace(
            "jobs:", "env:\n  TOKEN: ${{ secrets.READ_TOKEN }}\njobs:"
        )
    else:
        content = VALID.replace(
            "    steps:", "    env:\n      TOKEN: ${{ secrets.READ_TOKEN }}\n    steps:"
        )
    write(tmp_path, content)
    result = check(tmp_path)
    assert result.returncode == 1
    assert "secret-env" in result.stderr


def test_powershell_and_single_command_bash_do_not_need_strict_prologue(
    tmp_path: Path,
) -> None:
    content = VALID.replace(
        "    steps:", "    defaults:\n      run:\n        shell: pwsh\n    steps:"
    )
    write(tmp_path, content.replace("          set -euo pipefail\n", ""))
    assert check(tmp_path).returncode == 0
    write(
        tmp_path,
        VALID.replace("          set -euo pipefail\n", "").replace(
            "          echo done\n", ""
        ),
    )
    assert check(tmp_path).returncode == 0


def test_composite_action_bash_is_checked(tmp_path: Path) -> None:
    write(
        tmp_path,
        "name: Prepare\nruns:\n  using: composite\n  steps:\n"
        "    - name: Prepare files\n      shell: bash\n      run: |\n"
        "        echo first\n        echo second\n",
        ".github/actions/prepare/action.yaml",
    )
    result = check(tmp_path)
    assert result.returncode == 1
    assert "action.yaml:" in result.stderr
    assert "bash-strict" in result.stderr


@pytest.mark.parametrize(
    "runner",
    [
        "windows-latest",
        "[windows-latest]",
        "[self-hosted, Windows, X64]",
        "${{ matrix.os }}\n    strategy:\n      matrix:\n        os: [windows-latest]",
    ],
)
def test_implicit_windows_powershell_passes(tmp_path: Path, runner: str) -> None:
    content = VALID.replace("ubuntu-latest", runner).replace(
        "          set -euo pipefail\n", ""
    )
    write(tmp_path, content)
    result = check(tmp_path)
    assert result.returncode == 0, result.stderr


def test_unknown_runner_requires_shell_for_multiline_run(tmp_path: Path) -> None:
    content = VALID.replace("ubuntu-latest", "${{ inputs.runner }}")
    write(tmp_path, content)
    result = check(tmp_path)
    assert result.returncode == 1
    assert "shell-resolution" in result.stderr
    write(
        tmp_path,
        content.replace("        run: |", "        shell: bash\n        run: |"),
    )
    assert check(tmp_path).returncode == 0


def test_matrix_include_requires_explicit_shell(tmp_path: Path) -> None:
    content = VALID.replace(
        "ubuntu-latest",
        "${{ matrix.os }}\n    strategy:\n      matrix:\n"
        "        os: [windows-latest]\n        include:\n"
        "          - os: ubuntu-latest",
    ).replace("          set -euo pipefail\n", "")
    write(tmp_path, content)
    result = check(tmp_path)
    assert result.returncode == 1
    assert "shell-resolution" in result.stderr


def test_exact_baseline_does_not_hide_new_violations_and_rejects_stale_entries(
    tmp_path: Path,
) -> None:
    write(tmp_path, VALID.replace("name: CI", "name: ci"))
    baseline = [
        {
            "path": ".github/workflows/ci.yml",
            "rule": "naming",
            "message": "workflow name must start with an uppercase letter",
            "reason": "Fixture's existing workflow name.",
        }
    ]
    write(tmp_path, json.dumps(baseline), ".github/workflow-baseline.json")
    assert check(tmp_path).returncode == 0
    write(
        tmp_path,
        VALID.replace("name: CI", "name: ci").replace(
            "          set -euo pipefail\n", ""
        ),
    )
    result = check(tmp_path)
    assert result.returncode == 1
    assert "bash-strict" in result.stderr
    write(tmp_path, VALID)
    assert "stale baseline" in check(tmp_path).stderr


def test_malformed_yaml_fails(tmp_path: Path) -> None:
    write(tmp_path, "jobs: [")
    result = check(tmp_path)
    assert result.returncode == 1
    assert "invalid YAML" in result.stderr


def test_only_supported_template_reference_is_baselined(tmp_path: Path) -> None:
    content = (
        "name: CI\non: push\njobs:\n  verify:\n    name: Verify\n"
        "    uses: tj-agents/template/.github/workflows/plugin-ci.yml@"
    )
    write(tmp_path, content + "main\n")
    assert check(tmp_path).returncode == 0
    write(tmp_path, content + "unreviewed\n")
    result = check(tmp_path)
    assert result.returncode == 1
    assert "template-ref" in result.stderr


def test_zizmor_rejects_all_five_selected_security_violations(tmp_path: Path) -> None:
    write(
        tmp_path,
        """name: Unsafe
on: pull_request_target
permissions: write-all
jobs:
  unsafe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - run: echo '${{ github.event.pull_request.title }}'
""",
    )
    executable = shutil.which("zizmor")
    assert executable is not None
    result = subprocess.run(
        [
            executable,
            "--offline",
            "--pedantic",
            "--no-config",
            "--format",
            "json",
            str(tmp_path / ".github"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode != 0
    findings: object = json.loads(result.stdout)
    assert isinstance(findings, list)
    rules = {item["ident"] for item in findings if isinstance(item, dict)}
    assert {
        "excessive-permissions",
        "unpinned-uses",
        "artipacked",
        "template-injection",
        "dangerous-triggers",
    } <= rules
