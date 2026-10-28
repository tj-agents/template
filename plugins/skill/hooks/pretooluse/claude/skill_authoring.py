from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
shared = importlib.import_module("skill_authoring")


def procedure_loaded(transcript: str | None, procedures: set[str]) -> bool:
    if not transcript:
        return False
    requested, succeeded = set(), set()
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
                    if (
                        item.get("type") == "tool_use"
                        and item.get("name") == "Skill"
                        and (item.get("input") or {}).get("skill") in procedures
                    ):
                        requested.add(item.get("id"))
                    elif item.get("type") == "tool_result" and not item.get("is_error"):
                        succeeded.add(item.get("tool_use_id"))
    except OSError:
        return False
    return bool(requested & succeeded)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    path = (data.get("tool_input") or {}).get("file_path")
    procedures = shared.required_procedures(path, data.get("cwd"))
    if not procedures or procedure_loaded(data.get("transcript_path"), procedures):
        return 0
    names = " or ".join(sorted(procedures))
    sys.stderr.write(
        f"SKILL - load {names} and the current host native skill creator before authoring. "
        "Updates must remove retired names, aliases and active callers. The file was not written.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
