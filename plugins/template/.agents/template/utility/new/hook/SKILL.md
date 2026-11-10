---
name: new-hook
description: Add a Claude Code or Codex hook to a plugin repository so it can never block a prompt or tool call, fails open, stays fast and behaves the same on both hosts. Use before writing or changing any hook.
kind: utility
domain: template
profile: core
applicability: plugin repositories with host hooks
requires: python
provenance: house
---

# New hook

A hook runs on every session start, prompt or tool call. A broken, slow or stale hook therefore breaks
every session on the machine. Use a hook only when nothing else can do the job:

| Need | Use instead of a hook |
|---|---|
| Standards and conventions | a skill the agent loads when relevant |
| Enforcing a rule | lint, type checks and tests in CI |
| Forbidding a command or path | native permission deny rules |
| Telling Tommy something is stale | one warning from a single shared hook |

## Rules

1. **Never block.** Never emit `"decision": "block"` or `"permissionDecision": "deny"`, and never exit 2.
   Tell the user with `systemMessage`, which both hosts show. Tell the model with
   `hookSpecificOutput.additionalContext`.
2. **Fail open.** On any error, exit 0 with no output. A failed update or check is a warning at most.
3. **Stay fast.** Target under 1 second. A hook never touches the network, installs, or spawns `claude` or
   `codex`. Long work starts detached, and a later event reports how it went.
4. **One behavior for both hosts.** Register the same script for Claude and Codex, and test it on both.

## Example

```python
import json
import sys


def notice() -> str | None:
    return "Plugins updated: type /reload-plugins."


def main() -> int:
    try:
        json.load(sys.stdin)
        warning = notice()
    except Exception:
        return 0
    if warning:
        print(json.dumps({"systemMessage": warning}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Declare the script under `requires.hooks` in the repository's harness manifest, then regenerate. Add a test
that feeds each event the hook handles and asserts that the exit code is 0 and that the output never contains
`decision` or `permissionDecision`.
