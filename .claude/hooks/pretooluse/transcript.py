from __future__ import annotations

import json
from pathlib import Path


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
