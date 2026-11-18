---
name: update
description: Move a plugin repository to this release — re-vendor the generator, sync-generated.ps1, .gitattributes, .gitignore, CLAUDE.md and the ci.yml caller, update the pin in .agents/plugins/kit.json, and regenerate. Use when check or the generator reports a pin mismatch or a drifted vendored file, or when adopting a new Template release.
kind: utility
domain: kit
profile: core
applicability: plugin repositories
requires: python
provenance: house
---

# Update to this release

Read and follow the [canonical definition](../../.agents/kit/utility/update/SKILL.md) in full.
This discovery entry is generated; edit the referenced `.agents/` definition.
