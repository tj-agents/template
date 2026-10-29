---
name: check
description: Check a plugin repository against the shared layout and standard — the one folder structure, vendored files, required skill metadata and sections, and concrete examples in added or updated skill contracts. The canonical description of the plugin layout. Use when asked whether a plugin repository conforms, before delivering a structural change to one, or when a layout question comes up.
kind: utility
domain: template
profile: core
applicability: plugin repositories
requires: python
provenance: house
---

# Plugin repository check

Every plugin repository, Template included, has the same layout. The repository name identifies its main plugin namespace; separately named sibling plugins may share the repository.

```text
<repo>/
  AGENTS.md  CLAUDE.md  README.md
  .gitattributes  .gitignore            vendored
  .github/workflows/ci.yml              vendored; calls Template's plugin-ci.yml from main
  plans/                                optional
  .agents/
    <plugin>/<kind>/<name>/SKILL.md     one folder per plugin; the main plugin is named after the repository
    <plugin>/<kind>/<name>/scripts/     a skill's own files sit beside it and ship beside it
    <plugin>/<kind>/<name>/templates/
    <plugin>/<kind>/<family>/<member>/SKILL.md   a family groups related skills; <family>/SKILL.md is optional
    tiers/<plugin>.json
    plugins/template.json               repository and type
    plugins/payloads.json               published plugins, dependencies, compatibility aliases, mapped resources and host adapters
    plugins/adapters/<host>/<plugin>/<skill>.md  optional host-only discovery extension body
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

CI supplies its exact `--base` and `--head` range. Locally, the checker considers working, staged and untracked
skills against `HEAD`, plus commits since `origin/main` when that ref is available. A fresh or non-Git repository
checks every skill. Run update to refresh vendored files when they differ.

## Template adoption

New plugin scaffolds declare Template in `.agents/plugins.json`. Check existing coding repositories,
including applications without Template layout, with `--adoption`. This checks declaration drift only;
use Agent's `agent:plugins` settings check and native project admission/installation to prove
both hosts load it. The explicit adoption check permits a staged rollout without making unrelated
layout checks fail before existing repositories migrate.

```bash
python <skill-directory>/scripts/check.py --root ../coding-repository --adoption
```

## Skill families

Related skills share a family folder, family first: `state/client/` and `state/server/`, never `client-state/`
and `server-state/`. A skill's published name is its folder path below the kind folder joined by hyphens, so
`.agents/react/convention/state/client/SKILL.md` publishes `react:state-client`, and `result/carriers/` keeps the name
`result-carriers`. A family folder can hold its own `SKILL.md` as the family's shared rules; inside a skill
folder, only a folder with its own `SKILL.md` is a member, and anything else ships as that skill's files.
In projects without a selected policy that forbids compatibility aliases, renaming a published skill keeps
its old name until its `removeAfter` date. Apply the consuming project's explicit policy and published commitments.

## Skill content

Use `skill:check` to assess skill content and executable assets. This repository checker validates the
structural subset listed below; authoring and review apply the remaining skill requirements.

## What it enforces

- The vendored files equal the current Template source, with `ci.yml` rendered for the repository's owner.
- Only the layout's entries under `.agents/` and `.agents/plugins/`; `SOURCE_LAYOUT.md` and `sources.json` are retired.
- The skills its type in `standard.json` requires, with their kind, profile and sections:
  - **stack**: `knowledge`, `direction` (kind `knowledge`); `learning` (kind `policy`); `style`, `structure`
    (with `## File structure`), `domain-design`, `errors`, `testing`, `build`, `libraries` (kind `convention`);
    and a `scaffold` in any of its plugins. Its tier
    applies where the stack is present.
  - **tool**: `knowledge`, `direction` (kind `knowledge`); `learning` (kind `policy`); its tier always applies.
  - **utility**: only skills of kind `utility`; its tier declares `always` or `stack-present`. New utilities default to `always`.
  - **profile**: at least one policy in the main plugin, with supporting policies, conventions, workflows and
    utilities; its tier always applies after explicit project selection. Its generated host dependencies and
    harness requirements include the canonical `tj-agents/base` capability.
- A required skill's legacy kind (`contract` for a convention, `knowledge` for `learning`) still satisfies the
  check during the compatibility period; a fresh scaffold always emits the new kind.
- Manifests, harnesses, selections and payloads name no marketplace but `tj-agents`.
- `payloads.json` may map a regular file or recursive directory from `.agents/hooks`, any declared canonical
  plugin's `.agents/<plugin>/runtime` or `resources` directory, or discovered skill assets beside its `SKILL.md`
  (never the body itself), into a declared `plugins/<package>/` destination. Runtime and resources directories
  are permitted only when mapped. A resource may instead declare `distribution` with a Python distribution
  name from the project's runtime dependencies and committed `uv.lock`. Generation collects a locked,
  non-editable pure Python wheel through uv, rejecting import hooks, links and escaping records. Declare
  each required distribution; adapters import from their shipped package root. Resources under
  `skills/<skill>/` also map beside repository-local host scripts and separate installed Codex entries.
  Authored source uses the project's declared uv environment. See the repository README
  for the resource format. Its optional
  `host_adapters` entries append a host-specific extension body from the exact
  `.agents/plugins/adapters/<host>/<plugin>/<skill>.md` path to that host's generated discovery
  entry and installed target-host skill entry; shared instruction remains only in the canonical `SKILL.md`.
  Packages with extensions retain `skills/` for Claude and generate `codex-skills/` with a matching Codex manifest.
- Every skill of kind `contract` or `convention` opens with an `Owns …` line after its title.
- Every added or updated canonical `SKILL.md` contains a meaningful fenced code, command, configuration, or
  input/output example. `check_examples.py` is the standalone form for an explicit `--base`/`--head` range or
  one or more working-tree `--path` values. It excludes generated payloads and skill assets; unchanged legacy
  skills are not retrofitted. Follow `engineering:docs` for the authoring decision this validation enforces.
- Skill names are foldered: no flat names in one kind folder that share a hyphen-separated first or last word,
  nor a flat name sharing a family folder's word; no member repeating its family (`state/client-state/`); no
  name repeating its namespace (`dotnet-stack` under `dotnet`). Declared compatibility aliases are exempt.

The generator separately rejects malformed frontmatter, unresolved skill references and files that would not
ship. Extra skills beyond the required set are allowed.

## Corpus skill references

Run `python <skill-directory>/scripts/check_skill_references.py --root <repository> --source-root <repository> --marketplace tj-agents/marketplace`.
`--marketplace` reads the marketplace's plugin list and fetches only the repositories that publish a plugin the
source references, into a temporary directory; set `SKILL_REFERENCES_TOKEN` for private repositories.
Each root inventories actual shipped `plugins/*/skills/*/SKILL.md`, including compatibility aliases.
The checker scans active authored skills and root AGENTS.md, CLAUDE.md and README.md, including descriptions.
It excludes historical plans, generated adapters, test fixtures and vendored templates.

Known plugin namespaces resolve qualified names; unknown namespaces need explicit skill wording or an invocation.
Bare names marked as skills resolve locally first, then uniquely across the corpus. Missing and ambiguous names fail
with file and line evidence. `--source-root` restricts authored scanning while every `--root` supplies inventory;
without it, every root is scanned. Plugin CI resolves the current repository's references through the marketplace.
HTML comments, such as generated-block markers, are not references.

Use `--reference-path` for active canonical documents outside the default skill layout. Markdown
references resolve against the same shipped inventories as a directory's other Markdown files.
Paths must stay inside the scanned repositories. Missing paths fail the check.

```bash
python -B .agents/template/utility/check/scripts/check_skill_references.py --root ../app --root ../react --source-root ../app --reference-path ../app/standards
# A standards document still requiring a retired producer skill fails with its file and missing identity.
```

A repository may declare exact external identities in `.agents/plugins/skill-references.json` under
`external_skills`, mapping each `namespace:skill` to its rationale. This covers standards shipped outside
the marketplace; wildcards and empty rationales fail.
Detailed tier predicates and harness requirements remain core's payload contract.
