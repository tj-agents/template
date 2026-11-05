from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
transcript = importlib.import_module("transcript")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    if "template:self-repair" in transcript.loaded_skills(data.get("transcript_path")):
        return 0
    sys.stderr.write(
        "SELF-REPAIR - load template:self-repair before host feedback. Host feedback is "
        "only for a genuine host defect no tj-agents source can fix. The feedback was "
        "not sent.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
