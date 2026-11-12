import importlib.util
import json
import os
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/template/utility/check/scripts/check_global_writes.py"


def load(name: str, path: Path) -> ModuleType:
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


global_writes = load("template_global_writes", SCRIPT)


def test_check_detects_computed_python_global_target(tmp_path: Path) -> None:
    script = tmp_path / ".agents/example/utility/tool/scripts/write.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "from pathlib import Path\n"
        'destination = Path.home() / ".codex" / "config.toml"\n'
        'destination.write_text("value")\n',
        encoding="utf-8",
    )

    findings = global_writes.check(tmp_path, {}, {}, {})

    assert [finding.line for finding in findings] == [3]


def test_check_detects_shell_aliases_and_persistent_commands(tmp_path: Path) -> None:
    script = tmp_path / ".agents/example/runtime/install.ps1"
    script.parent.mkdir(parents=True)
    script.write_text(
        '$destination = Join-Path $HOME ".claude/settings.json"\n'
        "Set-Content -Path $destination -Value '{}'\n"
        "git config --global user.name Ada\n"
        "setx CODEX_HOME C:\\codex\n"
        "codex.config.batchWrite({})\n",
        encoding="utf-8",
    )

    findings = global_writes.check(tmp_path, {}, {}, {})

    assert [finding.line for finding in findings] == [2, 3, 4, 5]


def test_check_detects_registry_and_native_request_writes(tmp_path: Path) -> None:
    script = tmp_path / ".agents/example/runtime/config.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "import winreg\n"
        'key = winreg.OpenKey(None, "Environment")\n'
        'winreg.SetValueEx(key, "CODEX_HOME", 0, 1, "value")\n'
        'server.request("config/batchWrite", {"edits": []})\n',
        encoding="utf-8",
    )

    findings = global_writes.check(tmp_path, {}, {}, {})

    assert [finding.line for finding in findings] == [3, 4]


def test_check_allows_native_request_in_temporary_host_environment(
    tmp_path: Path,
) -> None:
    script = tmp_path / "scripts/native_acceptance.py"
    script.parent.mkdir()
    script.write_text(
        "from pathlib import Path\n"
        "from tempfile import TemporaryDirectory\n"
        "\n"
        "def isolated_environment(root):\n"
        "    return {'CODEX_HOME': str(root / 'codex')}\n"
        "\n"
        "def trust_current_hooks(server, environment):\n"
        "    server.request('config/batchWrite', {'edits': []})\n"
        "\n"
        "def accept_codex(environment):\n"
        "    trust_current_hooks(None, environment)\n"
        "\n"
        "def accept():\n"
        "    with TemporaryDirectory() as temporary:\n"
        "        environment = isolated_environment(Path(temporary))\n"
        "        accept_codex(environment)\n",
        encoding="utf-8",
    )

    assert global_writes.check(tmp_path, {}, {}, {}) == []


def test_check_scans_root_shell_and_scripts_but_allows_local_staging(
    tmp_path: Path,
) -> None:
    (tmp_path / "install.sh").write_text(
        'printf value > "$HOME/.codex/config.toml"\n', encoding="utf-8"
    )
    script = tmp_path / "scripts/acquire.ps1"
    script.parent.mkdir()
    script.write_text(
        "claude plugin install demo --scope local\n"
        '$temporary = Join-Path $env:TEMP "codex"\n'
        "$env:CODEX_HOME = $temporary\n"
        "codex plugin install demo\n",
        encoding="utf-8",
    )

    findings = global_writes.check(tmp_path, {}, {}, {})

    assert [(finding.path, finding.line) for finding in findings] == [("install.sh", 1)]


def test_check_allows_reads_repository_and_temp_writes(tmp_path: Path) -> None:
    script = tmp_path / ".agents/example/utility/tool/scripts/read.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "from pathlib import Path\n"
        "import tempfile\n"
        'Path.home().joinpath(".codex", "config.toml").read_text()\n'
        '(Path(".agents") / "state.json").write_text("value")\n'
        '(Path(tempfile.gettempdir()) / "state.json").write_text("value")\n',
        encoding="utf-8",
    )

    assert global_writes.check(tmp_path, {}, {}, {}) == []


def test_check_excludes_test_fixtures(tmp_path: Path) -> None:
    script = tmp_path / ".agents/tests/fixture.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "from pathlib import Path\n"
        'Path.home().joinpath(".codex", "config.toml").write_text("value")\n',
        encoding="utf-8",
    )

    assert global_writes.check(tmp_path, {}, {}, {}) == []


def test_check_allows_root_and_verified_generated_installer(tmp_path: Path) -> None:
    installer = tmp_path / "install.ps1"
    content = (
        '$destination = Join-Path $HOME ".codex/config.toml"\n'
        'Set-Content $destination "value"\n'
    )
    installer.write_text(content, encoding="utf-8")
    destination = ".agents/example/resources/installer/install.ps1"
    virtual = f"plugins/example/{destination}"
    payloads = {
        "resources": [
            {
                "plugin": "example",
                "source": "install.ps1",
                "destination": destination,
            }
        ]
    }

    assert (
        global_writes.check(
            tmp_path,
            payloads,
            {"example": "example"},
            {virtual: installer.read_bytes()},
        )
        == []
    )


def test_check_allows_a_verified_sources_manifest_installer(tmp_path: Path) -> None:
    installer = tmp_path / "install.ps1"
    content = (
        '$destination = Join-Path $HOME ".codex/config.toml"\n'
        'Set-Content $destination "value"\n'
    )
    installer.write_text(content, encoding="utf-8")
    harness = tmp_path / ".agents/plugins/harness/engineering.json"
    harness.parent.mkdir(parents=True)
    harness.write_text(
        json.dumps(
            {
                "plugin": "tj-agents/engineering",
                "source_roots": ["install.ps1"],
            }
        ),
        encoding="utf-8",
    )
    manifest = tmp_path / ".agents/plugins/sources.json"
    manifest.write_text(
        json.dumps(
            {
                "scopes": [{"name": "engineering", "plugin": "engineering"}],
                "resources": [
                    {
                        "plugin": "engineering",
                        "source": "install.ps1",
                        "destination": (
                            ".agents/engineering/resources/installer/install.ps1"
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    virtual = "plugins/engineering/.agents/engineering/resources/installer/install.ps1"

    assert (
        global_writes.check(tmp_path, {}, {}, {virtual: installer.read_bytes()}) == []
    )


def test_check_rejects_spoofed_installer_and_dependency_payload(tmp_path: Path) -> None:
    installer = tmp_path / "install.ps1"
    installer.write_text("Write-Output safe\n", encoding="utf-8")
    destination = ".agents/example/resources/installer/install.ps1"
    virtual = f"plugins/example/{destination}"
    payloads = {
        "resources": [
            {
                "plugin": "example",
                "source": "install.ps1",
                "destination": destination,
            }
        ]
    }
    generated = {
        virtual: (
            b'$destination = Join-Path $HOME ".codex/config.toml"\n'
            b'Set-Content $destination "value"\n'
        ),
        "plugins/example/runtime/dependency.py": (
            b"from pathlib import Path\n"
            b'Path.home().joinpath(".claude", "settings.json").write_text("value")\n'
        ),
    }

    findings = global_writes.check(
        tmp_path,
        payloads,
        {"example": "example"},
        generated,
    )

    assert [finding.path for finding in findings] == [
        virtual,
        "plugins/example/runtime/dependency.py",
    ]


def test_check_rejects_a_hardlinked_root_installer(tmp_path: Path) -> None:
    content = (
        b'$destination = Join-Path $HOME ".codex/config.toml"\n'
        b'Set-Content $destination "value"\n'
    )
    backing = tmp_path / "backing.ps1"
    backing.write_bytes(content)
    installer = tmp_path / "install.ps1"
    try:
        os.link(backing, installer)
    except OSError as error:
        pytest.skip(f"hardlink creation unavailable: {error}")
    destination = ".agents/example/resources/installer/install.ps1"
    virtual = f"plugins/example/{destination}"
    payloads = {
        "resources": [
            {
                "plugin": "example",
                "source": "install.ps1",
                "destination": destination,
            }
        ]
    }

    findings = global_writes.check(
        tmp_path,
        payloads,
        {"example": "example"},
        {virtual: content},
    )

    assert [finding.path for finding in findings] == ["install.ps1", virtual]


def test_standalone_cli_checks_core_sources_manifest_and_installer_links(
    tmp_path: Path,
) -> None:
    content = (
        b'$destination = Join-Path $HOME ".codex/config.toml"\n'
        b'Set-Content $destination "value"\n'
    )
    installer = tmp_path / "install.ps1"
    installer.write_bytes(content)
    harness = tmp_path / ".agents/plugins/harness/engineering.json"
    harness.parent.mkdir(parents=True)
    harness.write_text(
        json.dumps(
            {
                "plugin": "tj-agents/engineering",
                "source_roots": ["install.ps1"],
            }
        ),
        encoding="utf-8",
    )
    sources = tmp_path / ".agents/plugins/sources.json"
    sources.write_text(
        json.dumps(
            {
                "scopes": [{"name": "engineering", "plugin": "engineering"}],
                "resources": [
                    {
                        "plugin": "engineering",
                        "source": "install.ps1",
                        "destination": (
                            ".agents/engineering/resources/installer/install.ps1"
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    packaged = (
        tmp_path
        / "plugins/engineering/.agents/engineering/resources/installer/install.ps1"
    )
    packaged.parent.mkdir(parents=True)
    packaged.write_bytes(content)

    command = [sys.executable, "-B", str(SCRIPT), "--root", str(tmp_path)]
    clean = subprocess.run(command, capture_output=True, text=True, check=False)

    assert clean.returncode == 0, clean.stderr
    backing = tmp_path / "backing.ps1"
    backing.write_bytes(content)
    packaged.unlink()
    try:
        os.link(backing, packaged)
    except OSError as error:
        pytest.skip(f"hardlink creation unavailable: {error}")
    rejected = subprocess.run(command, capture_output=True, text=True, check=False)

    assert rejected.returncode == 1
    assert (
        "plugins/engineering/.agents/engineering/resources/installer/install.ps1"
        in (rejected.stderr)
    )
