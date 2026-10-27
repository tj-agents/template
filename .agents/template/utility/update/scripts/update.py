#!/usr/bin/env python3
"""Refresh a plugin repository's vendored files from Template.

Also removes legacy version metadata.
"""

import argparse
import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any

from tj_template.plugins import dependencies, generation

sys.dont_write_bytecode = True

NEW_PLUGIN = Path(__file__).resolve().parents[2] / "new/plugin"
if not NEW_PLUGIN.is_dir():
    NEW_PLUGIN = Path(__file__).resolve().parents[2] / "new-plugin"


def load_new_plugin() -> Any:
    loader = SourceFileLoader(
        "template_new_plugin", str(NEW_PLUGIN / "scripts/new_plugin.py")
    )
    spec = importlib.util.spec_from_loader("template_new_plugin", loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def update(root: Path, dry_run: bool, revision: str) -> list[str]:
    new_plugin = load_new_plugin()
    config_path = root / ".agents/plugins/template.json"
    if not config_path.is_file():
        raise ValueError(
            f"{config_path}: missing; this is not a Template plugin repository"
        )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not new_plugin.REPOSITORY.fullmatch(str(config.get("repository", ""))):
        raise ValueError(
            f"{config_path}: repository must be owner/name with a lowercase name"
        )
    owns_templates = (
        root / ".agents/template/utility/new/plugin/templates/repository"
    ).is_dir()
    changed: list[str] = []
    if generation.is_link_or_junction(root / ".agents"):
        raise ValueError("The .agents directory must not be a link or junction")
    if dependencies.configure(
        root, config["repository"].split("/")[1], revision, dry_run
    ):
        changed.append("pyproject.toml and uv.lock")
    for relative in (".agents/sync_generated.py", ".agents/sync-generated.ps1"):
        path = root / relative
        if path.exists():
            changed.append(relative)
            if not dry_run:
                path.unlink()
    for relative, expected in new_plugin.vendored_files(config["repository"]).items():
        if relative == ".github/workflows/ci.yml" and owns_templates:
            continue
        path = root / relative
        current = (
            path.read_text(encoding="utf-8").replace("\r\n", "\n")
            if path.is_file()
            else None
        )
        if current != expected:
            changed.append(relative)
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(expected, encoding="utf-8", newline="\n")
    if "template" in config:
        changed.append(".agents/plugins/template.json")
        if not dry_run:
            config.pop("template")
            config_path.write_text(
                json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n"
            )
    for host in ("claude", "codex"):
        manifest_dir = root / f".agents/plugins/manifests/{host}"
        for path in sorted(manifest_dir.glob("*.json")):
            if path.name == "marketplace.json":
                continue
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(manifest, dict) and "version" in manifest:
                changed.append(path.relative_to(root).as_posix())
                if not dry_run:
                    manifest.pop("version")
                    path.write_text(
                        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                        newline="\n",
                    )
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--template-ref",
        help="Immutable Template package commit; defaults to current main.",
    )
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    try:
        revision = dependencies.resolve_revision(arguments.template_ref)
        changed = update(root, arguments.dry_run, revision)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for relative in changed:
        print(f"{'would update' if arguments.dry_run else 'updated'} {relative}")
    if arguments.dry_run or not changed:
        print("already current" if not changed else "dry run: nothing written")
        return 0
    return generation.synchronize(root, check=False)


if __name__ == "__main__":
    raise SystemExit(main())
