#!/usr/bin/env python3
"""Validate a plugin repository's marketplace and plugins with the real
Claude Code and Codex CLIs."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any


def run(
    command: list[str],
    environment: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(command[0])
    if executable is None:
        raise SystemExit(f"error: {command[0]} is not on PATH")
    return subprocess.run(
        [executable, *command[1:]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
        timeout=180,
        cwd=cwd,
    )


def tolerated(warning: dict[str, Any]) -> bool:
    # Claude manifests omit version on purpose: Claude then treats every
    # pushed commit as an update.
    path = str(warning.get("path", ""))
    return path == "version" or path.endswith("→ version")


def problems(report: Any, where: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(report, dict):
        location = report.get("file") or where
        for error in report.get("errors") or []:
            found.append(
                f"{location}: {error.get('path', '')}: {error.get('message', error)}"
            )
        for warning in report.get("warnings") or []:
            if not tolerated(warning):
                message = warning.get("message", warning)
                found.append(f"{location}: {warning.get('path', '')}: {message}")
        for key, value in report.items():
            if key not in ("errors", "warnings"):
                found.extend(problems(value, location))
    elif isinstance(report, list):
        for item in report:
            found.extend(problems(item, where))
    return found


def validate_claude(root: Path) -> list[str]:
    targets = [root / ".claude-plugin/marketplace.json"]
    targets += sorted(path for path in (root / "plugins").iterdir() if path.is_dir())
    found: list[str] = []
    for target in targets:
        result = run(
            ["claude", "plugin", "validate", "--strict", "--json", str(target)]
        )
        try:
            report = json.loads(result.stdout)
        except ValueError:
            found.append(
                f"{target}: claude plugin validate returned no report: "
                f"{result.stderr.strip()}"
            )
            continue
        found.extend(problems(report, str(target)))
    return found


def validate_codex(root: Path) -> list[str]:
    marketplace = json.loads(
        (root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
    )
    expected = {entry["name"] for entry in marketplace["plugins"]}
    found = []
    for name in sorted(expected):
        with tempfile.TemporaryDirectory() as home:
            environment = {**os.environ, "CODEX_HOME": home}
            steps = [
                ["codex", "plugin", "marketplace", "add", str(root)],
                ["codex", "plugin", "add", f"{name}@{marketplace['name']}"],
            ]
            failed = False
            for step in steps:
                result = run(step, environment)
                if result.returncode != 0:
                    output = result.stderr.strip() or result.stdout.strip()
                    found.append(f"{' '.join(step)}: {output}")
                    failed = True
                    break
            if failed:
                continue
            result = run(["codex", "plugin", "list", "--json"], environment)
            if result.returncode != 0:
                output = result.stderr.strip() or result.stdout.strip()
                found.append(f"codex plugin list: {output}")
                continue
            try:
                listing = json.loads(result.stdout)
            except ValueError:
                found.append(f"codex plugin list returned no JSON report for {name}")
                continue
            installed = {
                entry["name"]
                for entry in listing.get("installed", [])
                if entry.get("installed")
                and entry.get("enabled")
                and entry.get("marketplaceName") == marketplace["name"]
            }
            if installed != {name}:
                found.append(
                    f"codex standalone install of {name} enabled {sorted(installed)}"
                )
    return found


def package_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
        and not {".git", "__pycache__", ".in_use"}.intersection(
            path.relative_to(root).parts
        )
        and path.suffix != ".pyc"
    }


def upgrade_command(command: list[str], environment: dict[str, str]) -> str:
    result = run(command, environment, cwd=Path(environment["CODEX_HOME"]).parent)
    if result.returncode:
        raise RuntimeError(
            f"{' '.join(command)}: {(result.stderr or result.stdout).strip()}"
        )
    return result.stdout


def installed_roots(
    host: str, home: Path, environment: dict[str, str]
) -> dict[str, Path]:
    listing = json.loads(
        upgrade_command([host, "plugin", "list", "--json"], environment)
    )
    if host == "codex":
        return {
            f"{entry['name']}@{entry['marketplaceName']}": home
            / "plugins/cache"
            / entry["marketplaceName"]
            / entry["name"]
            / entry["version"]
            for entry in listing["installed"]
            if entry.get("installed") and entry.get("enabled")
        }
    entries = listing if isinstance(listing, list) else listing["plugins"]
    enabled = {entry["id"] for entry in entries if entry.get("enabled")}
    registry = json.loads(
        (home / "plugins/installed_plugins.json").read_text(encoding="utf-8")
    )
    return {
        identity: Path(entry["installPath"])
        for identity, versions in registry["plugins"].items()
        if identity in enabled
        for entry in versions
        if entry["scope"] == "user"
    }


def validate_upgrades(root: Path, baseline: str | None) -> list[str]:
    if baseline and not re.fullmatch(r"[0-9a-f]{40}", baseline):
        raise ValueError(
            "Upgrade validation requires an existing full baseline commit SHA"
        )
    return [
        error
        for host in ("claude", "codex")
        if (
            error := validate_upgrade(
                root, baseline if baseline != "0" * 40 else None, host
            )
        )
        is not None
    ]


def copy_publication(root: Path, source: Path, targets: tuple[str, ...]) -> None:
    for relative in targets:
        destination = source / relative
        if not destination.resolve().is_relative_to(source.resolve()):
            raise ValueError(
                "Upgrade snapshot target escapes the disposable marketplace"
            )
        if destination.exists():
            if destination.is_dir():
                shutil.rmtree(destination)
            else:
                destination.unlink()
        if (root / relative).is_dir():
            shutil.copytree(root / relative, destination)
        else:
            shutil.copy2(root / relative, destination)


def validate_upgrade(root: Path, baseline: str | None, host: str) -> str | None:
    targets = ("plugins", ".agents/plugins", ".claude-plugin", ".gitattributes")
    with tempfile.TemporaryDirectory(prefix=f"{host} upgrade é ") as temporary:
        directory = Path(temporary)
        home, source = directory / "home", directory / "marketplace"
        source.mkdir()
        home.mkdir()
        environment = {
            **os.environ,
            "CLAUDE_CONFIG_DIR": str(home),
            "CODEX_HOME": str(home),
        }
        archive = directory / "baseline.tar"
        try:
            if baseline:
                upgrade_command(
                    [
                        "git",
                        "-C",
                        str(root),
                        "archive",
                        "--output",
                        str(archive),
                        baseline,
                        "--",
                        *targets,
                    ],
                    environment,
                )
                with tarfile.open(archive) as snapshot:
                    snapshot.extractall(source, filter="data")
            else:
                copy_publication(root, source, targets)
            for arguments in (
                ["init", "--initial-branch=main"],
                ["config", "core.autocrlf", "false"],
                ["config", "user.name", "Upgrade acceptance"],
                ["config", "user.email", "acceptance@example.invalid"],
            ):
                upgrade_command(["git", "-C", str(source), *arguments], environment)

            def commit(message: str) -> None:
                upgrade_command(["git", "-C", str(source), "add", "."], environment)
                upgrade_command(
                    [
                        "git",
                        "-C",
                        str(source),
                        "-c",
                        "core.hooksPath=",
                        "-c",
                        "commit.gpgSign=false",
                        "commit",
                        "--allow-empty",
                        "-m",
                        message,
                    ],
                    environment,
                )

            def catalog() -> tuple[str, dict[str, str]]:
                path = (
                    ".claude-plugin/marketplace.json"
                    if host == "claude"
                    else ".agents/plugins/marketplace.json"
                )
                document = json.loads((source / path).read_text(encoding="utf-8"))
                return document["name"], {
                    entry["name"]: entry["source"]["path"]
                    if isinstance(entry["source"], dict)
                    and entry["source"].get("source") == "local"
                    else entry["source"]
                    for entry in document["plugins"]
                }

            def install(name: str) -> None:
                command = [
                    host,
                    "plugin",
                    "install" if host == "claude" else "add",
                    name,
                ]
                if host == "claude":
                    command.extend(["--scope", "user"])
                upgrade_command(command, environment)

            commit("Published baseline")
            marketplace, previous = catalog()
            if host == "codex":
                (home / "config.toml").write_text(
                    f"[marketplaces.{json.dumps(marketplace)}]\n"
                    'source_type = "git"\n'
                    f"source = {json.dumps(source.as_uri())}\n",
                    encoding="utf-8",
                )
                upgrade_command(
                    [host, "plugin", "marketplace", "upgrade", marketplace], environment
                )
            else:
                upgrade_command(
                    [host, "plugin", "marketplace", "add", str(source)], environment
                )
            for name in previous:
                install(f"{name}@{marketplace}")
            roots = installed_roots(host, home, environment)
            missing = {f"{name}@{marketplace}" for name in previous} - roots.keys()
            if missing:
                raise RuntimeError(
                    f"Baseline installation is incomplete: {sorted(missing)}"
                )
            copy_publication(root, source, targets)
            commit("Candidate publication")
            current_marketplace, current = catalog()
            if current_marketplace != marketplace:
                raise RuntimeError("Marketplace identity changed across the upgrade")
            upgrade_command(
                [
                    host,
                    "plugin",
                    "marketplace",
                    "update" if host == "claude" else "upgrade",
                    marketplace,
                ],
                environment,
            )
            for name in previous.keys() - current.keys():
                upgrade_command(
                    [
                        host,
                        "plugin",
                        "uninstall" if host == "claude" else "remove",
                        f"{name}@{marketplace}",
                    ],
                    environment,
                )
            for name in current:
                if host == "claude" and name in previous:
                    upgrade_command(
                        [
                            host,
                            "plugin",
                            "update",
                            f"{name}@{marketplace}",
                            "--scope",
                            "user",
                        ],
                        environment,
                    )
                else:
                    install(f"{name}@{marketplace}")
            roots = installed_roots(host, home, environment)
            for name, package in current.items():
                if not isinstance(package, str) or not package.startswith("./plugins/"):
                    raise RuntimeError(
                        f"Upgrade requires a generated local package source: {name}"
                    )
                actual = roots.get(f"{name}@{marketplace}")
                expected_bytes = package_bytes(source / package)
                actual_bytes = package_bytes(actual) if actual is not None else {}
                if actual_bytes != expected_bytes:
                    changed = sorted(
                        key
                        for key in expected_bytes.keys() | actual_bytes.keys()
                        if expected_bytes.get(key) != actual_bytes.get(key)
                    )
                    raise RuntimeError(
                        f"Installed bytes differ after upgrade: {name}@{marketplace}: "
                        f"{changed[:8]} (installed={len(actual_bytes)}, "
                        f"expected={len(expected_bytes)})"
                    )
        except (
            OSError,
            ValueError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as error:
            return f"{host} baseline-to-candidate upgrade: {error}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline")
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    found = validate_claude(root) + validate_codex(root)
    found += validate_upgrades(root, arguments.baseline)
    for problem in found:
        print(problem, file=sys.stderr)
    if found:
        return 1
    print(f"Claude Code and Codex accept {root.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
