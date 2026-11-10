import subprocess
import sys
from pathlib import Path

import check_workflow_pins
import pytest

PIN = "7a06ba176a7245248fee3270842e0c4ed3030653"


def workflow(root: Path, reference: str) -> Path:
    path = root / ".github/workflows/ci.yml"
    path.parent.mkdir(parents=True)
    path.write_text(
        "name: CI\non: push\njobs:\n  verify:\n    uses: " + reference + "\n",
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize("status", ["ahead", "identical"])
def test_ancestor_and_default_tip_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    workflow(tmp_path, f"owner/producer/.github/workflows/build.yml@{PIN}")
    requests = []

    def github(endpoint: str, query: str) -> str:
        requests.append((endpoint, query))
        return "release/main" if query == ".default_branch" else status

    monkeypatch.setattr(check_workflow_pins, "github_field", github)
    assert check_workflow_pins.check(tmp_path) == []
    assert requests == [
        ("repos/owner/producer", ".default_branch"),
        (
            f"repos/owner/producer/compare/{PIN}...release%2Fmain",
            ".status",
        ),
    ]


@pytest.mark.parametrize("status", ["behind", "diverged", "unexpected"])
def test_unmerged_or_rebased_pin_fails_with_location_and_fix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    path = workflow(tmp_path, f"owner/producer/.github/workflows/build.yaml@{PIN}")
    monkeypatch.setattr(
        check_workflow_pins,
        "github_field",
        lambda _endpoint, query: "trunk" if query == ".default_branch" else status,
    )
    failures = check_workflow_pins.check(tmp_path)
    assert len(failures) == 1
    assert f"{path}:5: workflow-pin:" in failures[0]
    assert "not an ancestor" in failures[0]
    assert "default branch 'trunk'" in failures[0]
    assert "repin to a commit" in failures[0]


def test_only_external_job_workflow_references_are_checked(tmp_path: Path) -> None:
    path = workflow(tmp_path, "./.github/workflows/local.yml")
    path.write_text(
        path.read_text(encoding="utf-8")
        + "  test:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: owner/action@unmerged\n",
        encoding="utf-8",
    )
    action = tmp_path / ".github/actions/action.yml"
    action.parent.mkdir(parents=True)
    action.write_text("runs:\n  using: composite\n  steps: []\n", encoding="utf-8")
    assert check_workflow_pins.check(tmp_path) == []


@pytest.mark.parametrize("failure", ["access", "timeout", "missing", "yaml"])
def test_cli_fails_closed_when_ancestry_cannot_be_verified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    path = workflow(tmp_path, f"owner/producer/.github/workflows/build.yml@{PIN}")
    if failure == "yaml":
        path.write_text("jobs: [", encoding="utf-8")

    def github(_endpoint: str, _query: str) -> str:
        if failure == "access":
            raise subprocess.CalledProcessError(1, ["gh", "api"])
        if failure == "timeout":
            raise subprocess.TimeoutExpired(["gh", "api"], 60)
        raise ValueError("GitHub returned no default branch")

    monkeypatch.setattr(check_workflow_pins, "github_field", github)
    monkeypatch.setattr(
        sys, "argv", ["check_workflow_pins.py", "--root", str(tmp_path)]
    )
    assert check_workflow_pins.main() == 1
    assert "cannot verify producer ancestry" in capsys.readouterr().err


def test_github_query_uses_read_only_structured_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def run(
        arguments: list[str], **options: object
    ) -> subprocess.CompletedProcess[str]:
        assert arguments == [
            "gh",
            "api",
            "repos/owner/producer",
            "--jq",
            ".default_branch",
        ]
        assert options["check"] is True
        assert options["timeout"] == 60
        return subprocess.CompletedProcess(arguments, 0, "trunk\n", "")

    monkeypatch.setattr(subprocess, "run", run)
    assert (
        check_workflow_pins.github_field("repos/owner/producer", ".default_branch")
        == "trunk"
    )
