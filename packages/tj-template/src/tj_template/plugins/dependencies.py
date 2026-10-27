"""Declare the installed generator in a consumer's uv project."""

import re
import subprocess
import tomllib
from pathlib import Path

REPOSITORY = "https://github.com/tj-agents/template"
SUBDIRECTORY = "packages/tj-template"
COMMIT = re.compile(r"[0-9a-f]{40}")
TOOL_PROJECT = Path("tools/plugin-generation")


def resolve_revision(reference: str | None) -> str:
    """Resolve main once, or validate an explicitly selected immutable source."""
    if reference is None:
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--exit-code", REPOSITORY, "refs/heads/main"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise ValueError("Cannot resolve Template's current main commit") from error
        fields = result.stdout.split()
        reference = fields[0] if fields else ""
    if COMMIT.fullmatch(reference) is None:
        raise ValueError("--template-ref must be a full immutable Git commit")
    return reference


def project_files(name: str, revision: str) -> dict[str, str]:
    """Supply a new script project's normal dependency declaration."""
    return {
        (TOOL_PROJECT / ".python-version").as_posix(): "3.12\n",
        (TOOL_PROJECT / "pyproject.toml").as_posix(): (
            f'[project]\nname = "{name}-development"\nversion = "0.1.0"\n'
            'requires-python = ">=3.12"\ndependencies = []\n\n'
            '[dependency-groups]\ndev = ["tj-template"]\n\n'
            "[tool.uv]\npackage = false\n\n[tool.uv.sources]\n"
            f'tj-template = {{ git = "{REPOSITORY}", rev = "{revision}", '
            f'subdirectory = "{SUBDIRECTORY}" }}\n'
        ),
    }


def configure(root: Path, name: str, revision: str, dry_run: bool) -> bool:
    """Update the generator dependency while preserving existing project settings.

    Existing projects are edited and locked by uv. A freshly scaffolded project's
    already matching declaration remains unchanged; its publishing step runs uv lock.
    """
    project = root if (root / "pyproject.toml").is_file() else root / TOOL_PROJECT
    path = project / "pyproject.toml"
    ancestor = root
    for part in (*project.relative_to(root).parts, "pyproject.toml"):
        ancestor /= part
        if ancestor.is_symlink() or ancestor.is_junction():
            raise ValueError(f"Generator project must not follow a link: {ancestor}")
    lock = project / "uv.lock"
    if lock.is_symlink() or lock.is_junction():
        raise ValueError(f"Generator lockfile must not be a link: {lock}")
    if path.is_file():
        config = tomllib.loads(path.read_text(encoding="utf-8"))
        groups = config.get("dependency-groups", {})
        dependencies = [*config.get("project", {}).get("dependencies", [])]
        for group in groups.values():
            dependencies.extend(item for item in group if isinstance(item, str))
        source = (
            config.get("tool", {}).get("uv", {}).get("sources", {}).get("tj-template")
        )
        if isinstance(source, dict) and source.get("workspace") is True:
            return False
        if (
            any(
                re.match(r"tj-template(?:\s|[<>=!~;@]|$)", item)
                for item in dependencies
            )
            and isinstance(source, dict)
            and source.get("git") == REPOSITORY
            and source.get("rev") == revision
            and source.get("subdirectory") == SUBDIRECTORY
        ):
            return False
    if dry_run:
        return True
    if not path.is_file():
        for relative, text in project_files(name, revision).items():
            destination = root / relative
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(text, encoding="utf-8", newline="\n")
        command = ["uv", "lock", "--project", str(project)]
    else:
        command = [
            "uv",
            "add",
            "--project",
            str(project),
            "--dev",
            "--no-sync",
            f"tj-template @ git+{REPOSITORY}@{revision}#subdirectory={SUBDIRECTORY}",
        ]
    try:
        subprocess.run(command, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError(
            "Cannot install and lock the Template generator dependency"
        ) from error
    return True
