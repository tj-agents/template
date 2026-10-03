#!/usr/bin/env python3
"""Validate a plugin repository's marketplace and plugins with the real Claude Code and Codex CLIs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def run(command: list[str], environment: dict[str, str] | None = None) -> subprocess.CompletedProcess:
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
    )


def tolerated(warning: dict) -> bool:
    # Claude manifests omit version on purpose: Claude then treats every pushed commit as an update.
    path = str(warning.get("path", ""))
    return path == "version" or path.endswith("→ version")


def problems(report, where: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(report, dict):
        location = report.get("file") or where
        for error in report.get("errors") or []:
            found.append(f"{location}: {error.get('path', '')}: {error.get('message', error)}")
        for warning in report.get("warnings") or []:
            if not tolerated(warning):
                found.append(f"{location}: {warning.get('path', '')}: {warning.get('message', warning)}")
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
        result = run(["claude", "plugin", "validate", "--strict", "--json", str(target)])
        try:
            report = json.loads(result.stdout)
        except ValueError:
            found.append(f"{target}: claude plugin validate returned no report: {result.stderr.strip()}")
            continue
        found.extend(problems(report, str(target)))
    return found


def validate_codex(root: Path) -> list[str]:
    marketplace = json.loads((root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    expected = {entry["name"] for entry in marketplace["plugins"]}
    with tempfile.TemporaryDirectory() as home:
        environment = {**os.environ, "CODEX_HOME": home}
        steps = [["codex", "plugin", "marketplace", "add", str(root)]]
        steps += [["codex", "plugin", "add", f"{name}@{marketplace['name']}"] for name in sorted(expected)]
        for step in steps:
            result = run(step, environment)
            if result.returncode != 0:
                return [f"{' '.join(step)}: {result.stderr.strip() or result.stdout.strip()}"]
        listing = json.loads(run(["codex", "plugin", "list", "--json"], environment).stdout)
    installed = {
        entry["name"]
        for entry in listing.get("installed", [])
        if entry.get("installed") and entry.get("enabled") and entry.get("marketplaceName") == marketplace["name"]
    }
    return [f"codex did not install and enable {name}@{marketplace['name']}" for name in sorted(expected - installed)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    root = parser.parse_args().root.resolve()
    found = validate_claude(root) + validate_codex(root)
    for problem in found:
        print(problem, file=sys.stderr)
    if found:
        return 1
    print(f"Claude Code and Codex accept {root.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
