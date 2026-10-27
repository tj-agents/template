"""Claude PreToolUse: refuse a new SKILL.md until this session loaded template:new-skill (Python 3.9+)."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
shared = importlib.import_module("new_skill")


def procedure_loaded(transcript: str | None) -> bool:
    if not transcript:
        return False
    requested, succeeded = set(), set()
    try:
        with open(transcript, encoding="utf-8", errors="replace") as stream:
            for line in stream:
                if shared.PROCEDURE.split(":")[1] not in line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                for item in (record.get("message") or {}).get("content") or []:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "tool_use" and item.get("name") == "Skill" \
                            and (item.get("input") or {}).get("skill") == shared.PROCEDURE:
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
    if not shared.creates_skill(path, data.get("cwd")) or procedure_loaded(data.get("transcript_path")):
        return 0
    sys.stderr.write(shared.MESSAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
