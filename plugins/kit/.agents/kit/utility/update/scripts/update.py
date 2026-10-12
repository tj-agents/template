#!/usr/bin/env python3
"""Vendor this kit release's shared files into a plugin repository and pin the repository to it."""

from __future__ import annotations

import argparse
import importlib.util
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True

NEW_PLUGIN = Path(__file__).resolve().parents[2] / "new-plugin"


def load_new_plugin():
    loader = SourceFileLoader("kit_new_plugin", str(NEW_PLUGIN / "scripts/new_plugin.py"))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader("kit_new_plugin", loader))
    loader.exec_module(module)
    return module


def update(root: Path, dry_run: bool) -> list[str]:
    new_plugin = load_new_plugin()
    config_path = root / ".agents/plugins/kit.json"
    if not config_path.is_file():
        raise ValueError(f"{config_path}: missing; this is not a kit plugin repository")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not new_plugin.REPOSITORY.fullmatch(str(config.get("repository", ""))):
        raise ValueError(".agents/plugins/kit.json: repository must be owner/name with a lowercase name")
    owns_templates = (root / ".agents/kit/utility/new-plugin/templates/repository").is_dir()
    changed: list[str] = []
    for relative, expected in new_plugin.vendored_files(config["repository"]).items():
        if relative == ".github/workflows/ci.yml" and owns_templates:
            continue
        path = root / relative
        current = path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.is_file() else None
        if current != expected:
            changed.append(relative)
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(expected, encoding="utf-8", newline="\n")
    version = new_plugin.kit_version()
    if config.get("kit") != version:
        changed.append(".agents/plugins/kit.json")
        if not dry_run:
            config["kit"] = version
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    try:
        changed = update(root, arguments.dry_run)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for relative in changed:
        print(f"{'would update' if arguments.dry_run else 'updated'} {relative}")
    if arguments.dry_run or not changed:
        print("already current" if not changed else "dry run: nothing written")
        return 0
    return subprocess.run([sys.executable, "-B", str(root / ".agents/sync_generated.py"), "--root", str(root)], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
