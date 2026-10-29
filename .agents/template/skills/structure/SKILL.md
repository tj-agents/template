---
name: structure
description: Define tj-agents plugin repository source layout, skill identities, shared resources and generated host distributions. Use when creating or reorganising a plugin repository or choosing where its content belongs.
kind: standard
domain: template
profile: core
applicability: plugin repositories
requires: selected language standards
provenance: house
---

# Plugin repository structure

Owns the tj-agents plugin repository layout and the separation of authored skills, supporting content,
native host configuration and generated distribution. `template:check` validates it; `template:new-plugin`
creates it and `template:update` refreshes its vendored files.

## Authored source

```text
.agents/
  <namespace>/
    skills/
      <subject>/SKILL.md
      <family>/<member>/SKILL.md
    references/
    learning/knowledge.md
    assets/
  plugins/
  tiers/
  hooks/
  sync_generated.py
  sync-generated.ps1
.codex/
.claude/
src/<import_package>/
tests/
plugins/
```

Author each skill at `.agents/<namespace>/skills/<subject>/SKILL.md`. Its public identity is
`<namespace>:<subject>`; a nested subject path joins with hyphens. Thus `state/client/` publishes
`state-client`. Reject duplicate flattened names, including a collision with `state-client/`.
A family groups a real subject; matching words alone do not require one. Kind stays in metadata and
does not affect the path or identity. Use [Core's shared kind vocabulary](https://github.com/tj-agents/core/blob/main/SKILL_KINDS.md)
for classification. Repository presets select starter capabilities rather than a single kind.

A skill's own `scripts/`, `references/`, `templates/` and `assets/` stay beside its `SKILL.md` and ship
with it. Create shared sibling `references/` for documents read by several skills, `learning/` for
maintained learner proficiency, goals and progress, or `assets/` for shared output material only when
needed. Declare shared content in the payload resource map so installed consumers receive it. Learner
data is an ordinary resource read by the learning owner, not a discoverable skill or a place for DTOs.

## Implementation and host boundaries

Use the repository's selected language layout for substantial shared implementation. Python follows
`python:structure` and `python:modules`: a named package under `src/<import_package>/`, or package
members when independently consumed distributions justify them. Modules and subpackages describe
their actual responsibility; no universal runtime, services or infrastructure layer is required.
Do not create a distribution per skill or import implementation through instruction directories.

`.codex/` and `.claude/` contain native configuration and required thin entry points. Put substantial
host integration in the owning implementation package. Keep session, cache and database state in its
existing configured state store outside authored source. Repository `scripts/` holds actual repository
commands rather than an alternative import library.

## Generated output

`.agents/INDEX.md`, repository `.codex/skills/` and `.claude/skills/`, marketplace files and `plugins/`
are generated. Edit their declared canonical source and run `pwsh .agents/sync-generated.ps1`; use
`-Check` to verify freshness. Generate native metadata accepted by each host from the canonical
extended skill metadata. Shared instructions have one authored source; host-only extensions use the
declared adapter map.

`.agents/plugins/` owns repository/preset declarations, payload mappings, manifests and host adapter
sources; `.agents/tiers/` owns existing applicability routes. Preserve those contracts when moving a
skill. A path-only move preserves its public name and migrates its caller paths, resource maps and
generated entries together. A public rename uses `skill:update` for complete caller retirement.

The exact required root files, permitted control entries and preset capabilities live in
`template:check`'s `standard.json`; vendored files have one source in `template:new-plugin`'s
`templates/repository/`. Do not duplicate either inventory here.
