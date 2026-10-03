---
name: update
description: Move a plugin repository to this kit release — re-vendor the generator, sync-generated.ps1, .gitattributes, .gitignore, CLAUDE.md and the ci.yml caller, update the pin in .agents/plugins/kit.json, and regenerate. Use when kit:check or the generator reports a pin mismatch or a drifted vendored file, or when adopting a new kit release.
kind: utility
domain: kit
profile: core
applicability: plugin repositories
requires: python
provenance: house
---

# Update to this kit release

```bash
python <skill-directory>/scripts/update.py --root <repository> [--dry-run]
```

It overwrites each vendored file that differs from this release, pins `.agents/plugins/kit.json` to it, then runs
the repository's generator. `--dry-run` lists what would change. A local edit to a vendored file is lost: make
that change in kit instead.

Afterwards run `kit:check`, review the diff and commit it as one change.
