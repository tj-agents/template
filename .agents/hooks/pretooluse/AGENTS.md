# PreToolUse hooks

A PreToolUse hook runs before the host's tool call, so every launch is latency on the agent's work. Add one only
when all of these hold:

- It enforces a must-never rule that a skill description, `AGENTS.md` or CI cannot enforce in time.
- Its decision is deterministic: a path, a file's existence, a transcript record. It never scans a repository,
  calls git or the network, or resolves plugins.
- The host filters it declaratively, so ordinary tool calls never start its process. On Claude that is the handler's
  `if` field, for example `"if": "Write(**/SKILL.md)"`.

Codex matches PreToolUse only by tool name, so a Codex hook would launch on every `apply_patch`. Add no Codex
PreToolUse hook until Codex can filter by path; Codex relies on `AGENTS.md` and CI for the same rule.

Host-neutral logic lives here and is imported by each host's implementation under `.claude/hooks/pretooluse/` or
`.codex/hooks/pretooluse/`. Never put one host's payload or transcript format in this folder.

```text
skill_authoring.py                           shared: does this write create a new SKILL.md?
.claude/hooks/pretooluse/skill_authoring.py  Claude: block it until skill:new or skill:update is loaded
```
