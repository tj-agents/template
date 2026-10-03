---
name: check
description: Check a plugin repository against kit's layout and standard — the one folder structure, the vendored files pinned to a kit release, the skills and sections its type requires, frontmatter and profiles. The canonical description of the plugin layout. Use when asked whether a plugin repository conforms, before delivering a structural change to one, or when a layout question comes up.
kind: utility
domain: kit
profile: core
applicability: plugin repositories
requires: python
provenance: house
---

# Plugin repository check

Every plugin repository, kit included, has the same layout. The repository name is the plugin namespace.

```text
<repo>/
  AGENTS.md  CLAUDE.md  README.md
  .gitattributes  .gitignore            vendored
  .github/workflows/ci.yml              vendored; calls kit's plugin-ci.yml at the pinned tag
  plans/                                optional
  .agents/
    <plugin>/<kind>/<name>/SKILL.md     one folder per plugin; the main plugin is named after the repository
    <plugin>/<kind>/<name>/scripts/     a skill's own files sit beside it and ship beside it
    <plugin>/<kind>/<name>/templates/
    <plugin>/<kind>/<family>/<member>/SKILL.md   a family groups related skills; <family>/SKILL.md is optional
    tiers/<plugin>.json
    plugins/kit.json                    repository, type and the pinned kit release
    plugins/payloads.json               published plugins, dependencies, compatibility aliases
    plugins/manifests/{claude,codex}/<plugin>.json  marketplace.json
    hooks/  tests/                      optional
    sync_generated.py  sync-generated.ps1  vendored
  generated: .agents/INDEX.md  .claude/skills/  .codex/skills/  .claude-plugin/marketplace.json
             .agents/plugins/marketplace.json  plugins/<plugin>/
```

## Run it

```bash
python <skill-directory>/scripts/check.py --root <repository>
```

It prints each problem and exits 1, or confirms the repository conforms. CI runs it from kit at the pinned tag.
A repository pinned to another kit release is reported until `kit:update` moves it.

## Skill families

Related skills share a family folder, family first: `state/client/` and `state/server/`, never `client-state/`
and `server-state/`. A skill's published name is its folder path below the kind folder joined by hyphens, so
`.agents/react/contract/state/client/SKILL.md` publishes `react:state-client`, and `result/carriers/` keeps the name
`result-carriers`. A family folder can hold its own `SKILL.md` as the family's shared rules; inside a skill
folder, only a folder with its own `SKILL.md` is a member, and anything else ships as that skill's files.
Renaming a published skill keeps its old name as a compatibility alias until its `removeAfter` date.

## What it enforces

- The vendored files equal this kit release, with `ci.yml` rendered for the repository's owner.
- Only the layout's entries under `.agents/` and `.agents/plugins/`; `SOURCE_LAYOUT.md` and `sources.json` are retired.
- The skills its type in `standard.json` requires, with their kind, profile and sections:
  - **stack**: `learning`, `knowledge`, `direction`; `style`, `structure` (with `## File structure`),
    `domain-design`, `errors`, `testing`, `build`, `libraries`; and a `scaffold` in any of its plugins. Its tier
    applies where the stack is present.
  - **tool**: `learning`, `knowledge`, `direction`; its tier always applies.
  - **utility**: only skills of kind `utility`; its tier always applies.
- Every skill of kind `contract` opens with an `Owns …` line after its title.
- Skill names are foldered: no flat names in one kind folder that share a hyphen-separated first or last word,
  nor a flat name sharing a family folder's word; no member repeating its family (`state/client-state/`); no
  name repeating its namespace (`dotnet-stack` under `dotnet`). Declared compatibility aliases are exempt.

The generator separately rejects malformed frontmatter, unresolved skill references and files that would not
ship. Extra skills beyond the required set are allowed.
