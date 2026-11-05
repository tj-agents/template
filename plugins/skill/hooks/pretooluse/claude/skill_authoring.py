from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

here = Path(__file__).resolve()
sys.path[:0] = [str(here.parents[1]), str(here.parent)]
shared = importlib.import_module("skill_authoring")
transcript = importlib.import_module("transcript")

SHELLS = {"Bash": "bash", "PowerShell": "powershell"}


def targets(tool: str, tool_input: dict[str, str], cwd: str | None) -> list[str]:
    if tool in SHELLS:
        return shared.shell_targets(tool_input.get("command") or "", cwd, SHELLS[tool])
    path = tool_input.get("file_path")
    return [path] if path else []


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    tool = data.get("tool_name") or ""
    cwd = data.get("cwd")
    try:
        required = {
            target: procedures
            for target in targets(tool, data.get("tool_input") or {}, cwd)
            if (procedures := shared.required_procedures(target, cwd))
        }
    except Exception:
        return 0
    if not required:
        return 0
    loaded = transcript.loaded_skills(data.get("transcript_path"))
    unmet = {
        target: needed for target, needed in required.items() if not needed & loaded
    }
    if not unmet:
        return 0
    names = " or ".join(sorted(set.intersection(*unmet.values())))
    outcome = (
        "The command was not run" if tool in SHELLS else "The file was not written"
    )
    sys.stderr.write(
        f"SKILL - load {names} and the current host native skill creator before authoring "
        f"{', '.join(unmet)}. Updates must remove retired names, aliases and active callers. "
        f"{outcome}.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
