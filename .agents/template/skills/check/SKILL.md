---
name: check
description: Check a plugin repository's layout, vendored files, required metadata, preset capabilities and changed-skill examples. Use when assessing conformance or before delivering a plugin repository change; layout design belongs to template:structure.
kind: operation
domain: template
profile: core
applicability: plugin repositories
requires: python
provenance: house
---

# Plugin repository check

Check the selected repository against `template:structure` and the machine-readable `standard.json`
beside this skill. `skill:check` owns content and executable asset assessment beyond these structural
checks. Change vendored files at their Template source, then use `template:update` to refresh consumers.

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

## What it enforces

- Vendored-file equality, permitted source/control entries, canonical metadata and preset requirements
  from `standard.json`.
- Declared manifests, payload resources, host adapters and tier routes.
- `Owns …` openings for standards and meaningful fenced examples in added or updated skills.
  `check_examples.py` also accepts an explicit `--base`/`--head` range or working-tree `--path` values.
- Public-name uniqueness after flattening subject paths and current authored references.

The generator separately rejects malformed frontmatter, unresolved skill references and files that would not
ship. Inspect content directly to decide whether its kind and supporting-file placement fit its responsibility;
a valid string and successful generation do not establish semantic correctness.

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
python -B .agents/template/skills/check/scripts/check_skill_references.py --root ../app --root ../react --source-root ../app --reference-path ../app/standards
```

A repository may declare exact external identities in `.agents/plugins/skill-references.json` under
`external_skills`, mapping each `namespace:skill` to its rationale. This covers standards shipped outside
the marketplace; wildcards and empty rationales fail.
Detailed v3 tier predicates and harness requirements remain core's payload contract.
