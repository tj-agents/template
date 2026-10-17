---
name: update
description: Refresh a plugin repository from Template's main branch — re-vendor the generator, sync-generated.ps1, .gitattributes, .gitignore, CLAUDE.md and the ci.yml caller, remove legacy version metadata, and regenerate. Use when check reports drifted vendored files or when adopting current Template content.
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

It overwrites each vendored file that differs from the current Template source, removes a legacy config pin and top-level
manifest versions, then runs the repository's generator. --dry-run lists every change without writing. Make changes to
vendored files in Template.

Afterwards run `check`, review the diff and commit it as one change.
