---
name: new-plugin
description: Create a stack, tool, utility or project policy profile repository in the shared layout, with the generator, root files and CI following the selected package's main branch. Use when starting a language stack, a tool to learn, a utility plugin or a reusable project profile.
kind: utility
domain: template
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
| `profile` | one policy named by `--skill`; may add policies, conventions, workflows and utilities | `always`, in explicitly adopting projects |

Create a policy profile with `--type profile --skill <policy-name>`. It has no stack detection or teaching
scaffolding and requires at least one policy in its main plugin. It inherits `base@tj-agents` from
`tj-agents/marketplace`. Add mandatory host hooks to the shipped harness manifest and verify their actual
delivery; neither discovery nor an `always` tier proves session loading.

`--author` defaults to `git config user.name` and `--learner` to the author's first name. `--stack` is the display name.
`--keywords` and `--category` feed the manifests. `--dry-run` lists the files without writing. The destination
must exist and the repository folder must not. The script does not run `git init` or touch anything outside the
new folder.

Every skill starts as a skeleton with its required sections and `_Nothing yet._`. Conventions grow through the new
repository's `learning` convention procedure; `scaffold` gets its scripts and templates once `structure` has an
agreed File structure.

## Publish it

1. `git init -b main`, commit, then `gh repo create <owner>/<name> --public --source . --push`; plugin
   repositories are public so the shared marketplace can install them and CI runs.
2. Only while a repository plugin CI reads is private: `gh secret set TJ_AGENTS_READ_TOKEN --repo <owner>/<name>`.
3. Add the plugin to the shared marketplace's `catalog.json` and regenerate it.

## Validation

The script fails if the new repository does not generate cleanly. Before the first push,
`pwsh .agents/sync-generated.ps1 -Check` and `check` pass in it; CI then runs both from Template's main branch.
