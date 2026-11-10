import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / ".github/scripts/check_required_contexts.py"
REQUIRED = [
    "verify / default-branch",
    "verify / hosts",
    "verify / verify (ubuntu-latest)",
    "verify / verify (windows-latest)",
]


@pytest.fixture
def candidate(tmp_path: Path) -> Path:
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    for name in ("ci.yml", "plugin-ci.yml"):
        (workflows / name).write_bytes((ROOT / ".github/workflows" / name).read_bytes())
    policy = {
        "repositories": {
            "template": {
                "rulesets": {
                    "merge-policy": {
                        "rules": [
                            {
                                "type": "required_status_checks",
                                "parameters": {
                                    "required_status_checks": [
                                        {"context": context} for context in REQUIRED
                                    ]
                                },
                            }
                        ]
                    }
                }
            }
        }
    }
    (tmp_path / "github-configuration.json").write_text(json.dumps(policy), "utf-8")
    return tmp_path


def check(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(CHECKER),
            "--root",
            str(root),
            "--configuration",
            str(root / "github-configuration.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_shared_workflow_preserves_declared_required_contexts(candidate: Path) -> None:
    result = check(candidate)
    assert result.returncode == 0, result.stderr
    assert all(context in result.stdout for context in REQUIRED)


@pytest.mark.parametrize(
    ("filename", "before", "after", "missing"),
    [
        ("plugin-ci.yml", "name: default-branch", "name: Renamed", REQUIRED[0]),
        ("plugin-ci.yml", "name: hosts", "name: Renamed", REQUIRED[1]),
        ("plugin-ci.yml", "name: verify", "name: Renamed", REQUIRED[2]),
        (
            "plugin-ci.yml",
            "ubuntu-latest, windows-latest",
            "ubuntu-latest",
            REQUIRED[3],
        ),
        ("ci.yml", "name: verify", "name: Renamed", REQUIRED[0]),
    ],
)
def test_renamed_required_context_fails(
    candidate: Path, filename: str, before: str, after: str, missing: str
) -> None:
    path = candidate / ".github/workflows" / filename
    content = path.read_text("utf-8")
    assert before in content
    path.write_text(content.replace(before, after), "utf-8")
    result = check(candidate)
    assert result.returncode == 1
    assert missing in result.stderr


def test_new_policy_context_cannot_be_silently_ignored(candidate: Path) -> None:
    path = candidate / "github-configuration.json"
    path.write_text(
        path.read_text("utf-8").replace("verify / hosts", "verify / new-gate")
    )
    result = check(candidate)
    assert result.returncode == 1
    assert "verify / new-gate" in result.stderr


def test_configuration_without_shared_checks_fails(candidate: Path) -> None:
    (candidate / "github-configuration.json").write_text("{}", "utf-8")
    result = check(candidate)
    assert result.returncode == 1
    assert "declares no shared" in result.stderr
