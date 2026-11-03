from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
shared = importlib.import_module("skill_authoring")

SHELLS = {"Bash": "bash", "PowerShell": "powershell"}


def loaded_skills(transcript: str | None) -> set[str]:
    if not transcript:
        return set()
    requested: dict[str, str] = {}
    succeeded: set[str] = set()
    try:
        with Path(transcript).open(encoding="utf-8", errors="replace") as stream:
            for line in stream:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                for item in (record.get("message") or {}).get("content") or []:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "tool_use" and item.get("name") == "Skill":
                        requested[item.get("id")] = (item.get("input") or {}).get(
                            "skill"
                        )
                    elif item.get("type") == "tool_result" and not item.get("is_error"):
                        succeeded.add(item.get("tool_use_id"))
    except OSError:
        return set()
    return {skill for key, skill in requested.items() if key in succeeded}


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
    if tool == "SendFeedback":
        if "template:self-repair" in loaded_skills(data.get("transcript_path")):
            return 0
        sys.stderr.write(
            "SELF-REPAIR - load template:self-repair before host feedback. Host feedback is only "
            "for a genuine host defect no tj-agents source can fix. The feedback was not sent.\n"
        )
        return 2
    cwd = data.get("cwd")
    required = {
        target: procedures
        for target in targets(tool, data.get("tool_input") or {}, cwd)
        if (procedures := shared.required_procedures(target, cwd))
    }
    if not required:
        return 0
    loaded = loaded_skills(data.get("transcript_path"))
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
