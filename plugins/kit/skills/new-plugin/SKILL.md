---
name: new-plugin
description: Create a plugin repository in the shared layout — a stack (knowledge tier, a teaching policy, the seven conventions and a project scaffold), a tool (knowledge tier and teaching policy only) or a utility — with the generator, root files and CI vendored from kit and pinned to its release. Use when starting a new language stack, a new tool to learn, or a new utility plugin.
kind: utility
domain: kit
profile: core
applicability: new plugin repositories
requires: python, pwsh
provenance: house
---

# New plugin repository

Creates `<destination>/<name>/` from this skill's `templates/` and builds its generated outputs. The repository
name is the plugin namespace, so `<owner>/zig` publishes skills as `zig:<name>`.

## Create a plugin repository

```bash
python <skill-directory>/scripts/new_plugin.py --repository <owner>/zig --type stack --stack Zig \
  --description "Zig learning companion and standards." --destination ~/source/repos/<owner> \
  --detect-file build.zig --detect-glob "*.zig"
```

| Type | Skills created | Tier |
|---|---|---|
| `stack` | `knowledge`, `direction` (knowledge); `learning` (policy); `style`, `structure`, `domain-design`, `errors`, `testing`, `build`, `libraries` (convention); `scaffold` (utility) | `stack-present`, from `--detect-file` and `--detect-glob` |
| `tool` | `knowledge`, `direction` (knowledge); `learning` (policy) | `always` |
| `utility` | one utility skill named by `--skill` | `always` |

`--author` defaults to `git config user.name` and `--learner` to the author's first name. `--stack` is the display name.
`--keywords` and `--category` feed the manifests. `--dry-run` lists the files without writing. The destination
must exist and the repository folder must not. The script does not run `git init` or touch anything outside the
new folder.

Every skill starts as a skeleton with its required sections and `_Nothing yet._`. Conventions grow through the new
repository's `learning` convention procedure; `scaffold` gets its scripts and templates once `structure` has an
agreed File structure.

## Publish it

1. `git init -b main`, commit, then `gh repo create <owner>/<name> --private --source . --push`.
2. `gh secret set TJ_AGENTS_READ_TOKEN --repo <owner>/<name>` with the read-only token CI uses.
3. Add the plugin to the shared marketplace's `catalog.json` and regenerate it.

## Validation

The script fails if the new repository does not generate cleanly. Before the first push,
`pwsh .agents/sync-generated.ps1 -Check` and `kit:check` pass in it; CI then runs both from kit at the pinned tag.
