---
name: update
description: Refresh a plugin repository's installed generator and shared root files from Template's main branch, remove superseded generator copies and legacy version metadata, and regenerate. Use when adopting current Template content or repairing dependency and vendored-file drift.
kind: utility
domain: template
profile: core
applicability: plugin repositories
requires: python
provenance: house
---

# Update from Template

```bash
python <skill-directory>/scripts/update.py --root <repository> [--dry-run]
```

It pins `tj-template` to the selected immutable Template commit and updates the consumer's uv lockfile.
An existing Python project owns that dependency; other repositories keep a tool-only project in
`tools/plugin-generation`. New scaffolds declare the package in their Python development project and run `uv lock`
before publishing. `--template-ref <full-commit>` selects an explicit candidate; otherwise the updater resolves main.

The updater refreshes vendored root files, removes copied generators, a legacy config pin and top-level
manifest versions, then generates through the installed package. `--dry-run` lists changes without writing.
Authored generator code belongs only to Template's package. Source changes to other vendored files belong
in Template's repository templates.

Afterwards run `check`, review the diff and commit it as one change.
