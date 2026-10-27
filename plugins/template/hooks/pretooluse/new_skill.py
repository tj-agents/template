"""Decide whether a write creates a new skill definition (Python 3.9+)."""

from __future__ import annotations

from pathlib import Path

SKILL_FILE = "SKILL.md"
PROCEDURE = "template:new-skill"
MESSAGE = (
    "TEMPLATE - creating a new skill requires the template:new-skill procedure first: it resolves ownership, "
    "naming and whether an existing skill should be extended instead. Load template:new-skill, follow it, then "
    "retry. Edits to existing skills are not affected. The file was NOT written.\n"
)


def creates_skill(path: str | None, cwd: str | None) -> bool:
    if not path:
        return False
    target = Path(path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target
    return target.name == SKILL_FILE and not target.exists()
