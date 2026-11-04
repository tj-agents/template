import importlib.util
import json
import os
import shutil
import subprocess
import sys
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


def test_plugin_ci_checks_out_only_its_template_and_cli_dependencies() -> None:
    workflow = (ROOT / ".github/workflows/plugin-ci.yml").read_text(encoding="utf-8")
    repositories = {
        line.strip().removeprefix("repository: ")
        for line in workflow.splitlines()
        if line.strip().startswith("repository:")
    }
    assert repositories == {"${{ inputs.template_repository }}", "tj-agents/cli"}


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


@pytest.mark.parametrize("stale", [False, True])
def test_upgrade_checks_installed_bytes_in_isolated_homes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stale: bool
) -> None:
    for name in list(os.environ):
        if name == "GIT_CONFIG_COUNT" or name.startswith(
            ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
        ):
            monkeypatch.delenv(name, raising=False)
    root = tmp_path / "publisher"
    root.mkdir()
    (root / ".gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8")

    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout.strip()

    git("init", "--initial-branch=main")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "core.hooksPath", "")
    git("config", "core.longpaths", "true")
    for host, catalog in (
        ("claude", ".claude-plugin/marketplace.json"),
        ("codex", ".agents/plugins/marketplace.json"),
    ):
        path = root / catalog
        path.parent.mkdir(parents=True)
        source: Any = (
            "./plugins/demo"
            if host == "claude"
            else {"source": "local", "path": "./plugins/demo"}
        )
        path.write_text(
            json.dumps(
                {"name": "example", "plugins": [{"name": "demo", "source": source}]}
            ),
            encoding="utf-8",
        )
    payload = root / "plugins/demo/payload.txt"
    payload.parent.mkdir(parents=True)
    payload.write_text("baseline", encoding="utf-8")
    deep = root / "plugins/demo" / ("scaffold-component/" * 9) / "template.cs"
    deep.parent.mkdir(parents=True)
    deep.write_text("long path payload", encoding="utf-8")
    git("add", ".")
    git("-c", "commit.gpgSign=false", "commit", "-m", "Baseline")
    baseline = git("rev-parse", "HEAD")
    payload.write_text("candidate", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.longpaths")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "false")
    original_run = validate_hosts.run
    sources: dict[str, Path] = {}
    calls: list[tuple[str, list[str]]] = []

    def fake_run(
        command: list[str],
        environment: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if command[0] == "git":
            result: subprocess.CompletedProcess[str] = original_run(
                command, environment, cwd
            )
            return result
        assert environment is not None
        home = Path(environment["CODEX_HOME"])
        assert environment["CLAUDE_CONFIG_DIR"] == str(home)
        assert cwd == home.parent
        assert environment["GIT_CONFIG_KEY_0"] == "core.longpaths"
        assert environment["GIT_CONFIG_VALUE_0"] == "false"
        effective = original_run(
            ["git", "config", "--get", "core.longpaths"], environment
        )
        assert effective.stdout.strip() == ("true" if os.name == "nt" else "false")
        key = str(home)
        calls.append((key, command))
        if command[1:4] == ["plugin", "marketplace", "add"]:
            sources[key] = Path(command[4])
        elif command[:4] == ["codex", "plugin", "marketplace", "upgrade"]:
            source = home.parent / "marketplace"
            cloned = (
                home
                / f".tmp/marketplaces/.staging/native-upgrade-checkout-{len(calls)}"
            )
            result = original_run(
                ["git", "clone", str(source), str(cloned)], environment
            )
            assert result.returncode == 0, result.stderr
            assert len(str(cloned / deep.relative_to(root))) > 260
            assert (cloned / deep.relative_to(root)).read_text(
                encoding="utf-8"
            ) == "long path payload"
            sources[key] = cloned
            assert 'source_type = "git"' in (home / "config.toml").read_text(
                encoding="utf-8"
            )
        elif command[1:3] in (
            ["plugin", "add"],
            ["plugin", "install"],
            ["plugin", "update"],
        ):
            installed = home / "plugins/cache/example/demo/local"
            if not installed.exists() or not stale:
                shutil.copytree(
                    sources[key] / "plugins/demo", installed, dirs_exist_ok=True
                )
            registry = home / "plugins/installed_plugins.json"
            registry.write_text(
                json.dumps(
                    {
                        "plugins": {
                            "demo@example": [
                                {"installPath": str(installed), "scope": "user"}
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
        elif command[1:] == ["plugin", "list", "--json"]:
            report: Any = (
                [{"id": "demo@example", "enabled": True}]
                if command[0] == "claude"
                else {
                    "installed": [
                        {
                            "name": "demo",
                            "marketplaceName": "example",
                            "installed": True,
                            "enabled": True,
                            "version": "local",
                        }
                    ]
                }
            )
            return subprocess.CompletedProcess(command, 0, json.dumps(report), "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(validate_hosts, "run", fake_run)
    errors = validate_hosts.validate_upgrades(root, baseline)
    assert bool(errors) == stale
    assert len({home for home, _ in calls}) == 2
    assert any(command[:3] == ["claude", "plugin", "update"] for _, command in calls)
    assert any(
        command[:4] == ["codex", "plugin", "marketplace", "upgrade"]
        for _, command in calls
    )
    if stale:
        assert all("Installed bytes differ after upgrade" in error for error in errors)


def test_host_validator_runs_outside_checkout_with_installed_dependencies(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / ".github/scripts/validate_hosts.py"),
            "--help",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "--baseline" in result.stdout
