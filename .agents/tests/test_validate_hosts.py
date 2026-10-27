import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_hosts", ROOT / ".github/scripts/validate_hosts.py"
)
assert SPEC is not None
assert SPEC.loader is not None
validate_hosts: Any = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_hosts)


def test_plugin_ci_checks_out_no_consumer_repositories() -> None:
    workflow = (ROOT / ".github/workflows/plugin-ci.yml").read_text(encoding="utf-8")
    repositories = {
        line.strip().removeprefix("repository: ")
        for line in workflow.splitlines()
        if line.strip().startswith("repository:")
    }
    assert repositories == {"${{ inputs.template_repository }}"}


def test_only_the_omitted_version_warning_is_tolerated() -> None:
    report = {
        "success": False,
        "manifest": {
            "file": "marketplace.json",
            "errors": [],
            "warnings": [
                {
                    "path": "plugins[0] plugin.json → version",
                    "message": "No version specified.",
                },
                {
                    "path": "plugins[0] plugin.json → homepage",
                    "message": "Unrecognized field.",
                },
            ],
        },
        "contents": [
            {
                "file": "skills/x/SKILL.md",
                "errors": [{"path": "name", "message": "Missing name."}],
                "warnings": [],
            }
        ],
    }
    assert validate_hosts.problems(report) == [
        "marketplace.json: plugins[0] plugin.json → homepage: Unrecognized field.",
        "skills/x/SKILL.md: name: Missing name.",
    ]


def test_a_plugin_manifest_without_version_passes() -> None:
    report = {
        "manifest": {
            "file": "plugin.json",
            "errors": [],
            "warnings": [{"path": "version", "message": "No version."}],
        }
    }
    assert validate_hosts.problems(report) == []


def test_each_publication_uses_a_separate_home_and_accepts_only_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    selected: dict[str, str] = {}
    homes: list[tuple[str, list[str]]] = []

    def fake_run(
        command: list[str], environment: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        assert environment is not None
        home = environment["CODEX_HOME"]
        homes.append((home, command))
        if command[:3] == ["codex", "plugin", "add"]:
            selected[home] = command[3].split("@", 1)[0]
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["codex", "plugin", "list", "--json"]:
            report = {
                "installed": [
                    {
                        "name": selected[home],
                        "installed": True,
                        "enabled": True,
                        "marketplaceName": "tj-agents",
                    }
                ]
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(report), "")
        return subprocess.CompletedProcess(command, 0, "", "")

    marketplace = tmp_path / ".agents/plugins/marketplace.json"
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(
        json.dumps(
            {
                "name": "tj-agents",
                "plugins": [{"name": "demo"}, {"name": "template"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(validate_hosts, "run", fake_run)
    assert validate_hosts.validate_codex(tmp_path) == []
    installs = [
        (home, command[3].split("@", 1)[0])
        for home, command in homes
        if command[:3] == ["codex", "plugin", "add"]
    ]
    assert [name for _, name in installs] == ["demo", "template"]
    assert len({home for home, _ in installs}) == 2


def test_an_implicit_second_install_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(
        command: list[str], environment: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        if command == ["codex", "plugin", "list", "--json"]:
            report = {
                "installed": [
                    {
                        "name": "demo",
                        "installed": True,
                        "enabled": True,
                        "marketplaceName": "tj-agents",
                    },
                    {
                        "name": "template",
                        "installed": True,
                        "enabled": True,
                        "marketplaceName": "tj-agents",
                    },
                ]
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(report), "")
        return subprocess.CompletedProcess(command, 0, "", "")

    marketplace = tmp_path / ".agents/plugins/marketplace.json"
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(
        json.dumps({"name": "tj-agents", "plugins": [{"name": "demo"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(validate_hosts, "run", fake_run)
    assert validate_hosts.validate_codex(tmp_path) == [
        "codex standalone install of demo enabled ['demo', 'template']"
    ]
