from __future__ import annotations

from pathlib import Path


def required_procedures(path: str | None, cwd: str | None) -> set[str]:
    if not path:
        return set()
    target = Path(path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target
    if target.name != "SKILL.md":
        return set()
    return {"skill:update"} if target.exists() else {"skill:create", "skill:update"}
