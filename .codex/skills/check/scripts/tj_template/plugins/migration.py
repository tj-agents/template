"""Migrate known generation instructions before retiring copied scripts."""

import os
import re
import subprocess
from pathlib import Path

from tj_template.plugins.dependencies import generator_group, project_directory
from tj_template.plugins.generation import is_link_or_junction

RETIRED_SCRIPTS = (".agents/sync_generated.py", ".agents/sync-generated.ps1")
REFERENCE = re.compile(r"\.agents[/\\]+sync(?:_generated\.py|-generated\.ps1)", re.I)
COMMAND = re.compile(
    r"\bpwsh(?:[ \t]+-NoProfile)?[ \t]+(?:\./)?\.agents[/\\]+sync-generated\.ps1"
    r"(?P<check>[ \t]+-Check)?(?=[ \t]*(?:$|[`'\";]|&&|\|\||#))",
    re.I | re.M,
)
TEXT_SUFFIXES = {".md", ".py", ".ps1", ".json", ".toml", ".yml", ".yaml", ".rules"}
IGNORED = {
    ".git",
    ".venv",
    ".worktrees",
    "node_modules",
    "target",
    "__pycache__",
}


def authored_paths(root: Path) -> list[Path]:
    """Read tracked source, or a new scaffold's files before Git initialization."""
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root:
        tracked = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout
        return [root / item.decode("utf-8") for item in tracked.split(b"\0") if item]
    result: list[Path] = []
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = [
            name
            for name in names
            if name not in IGNORED
            and not (Path(directory) / name).is_junction()
            and not (Path(directory) == root and name == "plugins")
        ]
        result.extend(Path(directory) / name for name in files)
    return result


def caller_changes(root: Path) -> dict[Path, str]:
    """Plan known Markdown rewrites and refuse unhandled callers before deletion."""
    project = project_directory(root)
    prefix = "uv run --locked --no-default-groups"
    group = generator_group(root)
    if group is not None:
        prefix += " --group " + group
    if project != root:
        prefix += " --project " + project.relative_to(root).as_posix()
    prefix += " tj-template"
    retiring = any((root / name).exists() for name in RETIRED_SCRIPTS)
    changes: dict[Path, str] = {}
    unresolved: list[str] = []
    for path in authored_paths(root):
        relative = path.relative_to(root)
        if (
            path.suffix not in TEXT_SUFFIXES
            or relative.as_posix() in RETIRED_SCRIPTS
            or relative.parts[0] == "plugins"
            or relative.parts[:2] in {(".claude", "skills"), (".codex", "skills")}
            or relative.parts[:2] == (".agents", "dependencies")
            or not path.is_file()
        ):
            continue
        ancestor = root
        for part in relative.parts:
            ancestor /= part
            if is_link_or_junction(ancestor):
                raise ValueError(
                    f"Cannot migrate a linked generation caller: {relative}"
                )
        original = path.read_text(encoding="utf-8")
        text = original
        if path.suffix == ".md":
            text = text.replace(
                "`.agents/sync_generated.py`, `.agents/sync-generated.ps1`,\n", ""
            )
            text = COMMAND.sub(
                lambda match: (
                    prefix + (" check" if match.group("check") else " generate")
                ),
                text,
            ).replace("vendored generator", "installed generator")
        if text != original:
            changes[path] = text
        if retiring and REFERENCE.search(text):
            unresolved.append(relative.as_posix())
    if unresolved:
        raise ValueError(
            "Migrate generation callers before removing scripts: "
            + ", ".join(sorted(unresolved))
        )
    return changes
