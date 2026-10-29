---
name: new-plugin
description: Create a stack, tool, plugin or project policy profile repository in the shared layout, with the generator, root files and CI following the selected package's main branch. Use when starting a language stack, a tool to learn, a general plugin or a reusable project profile.
kind: operation
domain: template
profile: core
applicability: new plugin repositories
requires: python, pwsh
provenance: house
---

# New plugin repository

Creates `<destination>/<name>/` from this skill's `templates/` and builds its generated outputs. The repository
name identifies the main plugin namespace, so `<owner>/zig` publishes skills as `zig:<name>`.
Apply `template:structure` for authored and generated content placement.

## Create a plugin repository

```bash
python <skill-directory>/scripts/new_plugin.py --repository <owner>/zig --type stack --stack Zig \
  --description "Zig learning companion and standards." --destination ~/source/repos/<owner> \
  --detect-file build.zig --detect-glob "*.zig"
```

| Type | Skills created | Tier |
|---|---|---|
| `stack` | `direction` (reference); `learning` (learning); `style`, `structure`, `domain-design`, `errors`, `testing`, `build`, `libraries` (standard); `scaffold` (operation); learner data at `.agents/<namespace>/learning/knowledge.md` | `stack-present`, from `--detect-file` and `--detect-glob` |
| `tool` | `direction` (reference); `learning` (learning); learner data at `.agents/<namespace>/learning/knowledge.md` | `always` |
| `plugin` | one skill named by `--skill`, with the explicit `--skill-kind` | `always` |
| `profile` | one policy named by `--skill` | `always`, in explicitly adopting projects |

Presets select starter content; every preset permits additional skills of any supported kind. Choose each
skill's kind from its responsibility, independently of its preset and directory.

```bash
python <skill-directory>/scripts/new_plugin.py --repository <owner>/search --type plugin \
  --skill query --skill-kind operation --description "Search the selected source." \
  --destination ~/source/repos/<owner>
```

Create a policy profile with `--type profile --skill <policy-name>`. It has no stack detection or teaching
scaffolding and requires at least one policy in its main plugin. It inherits `base@tj-agents` from
`tj-agents/marketplace`. Add mandatory host hooks to the shipped harness manifest and verify their actual
delivery; neither discovery nor an `always` tier proves session loading.

`--author` defaults to `git config user.name` and `--learner` to the author's first name. `--stack` is the display name.
`--keywords` and `--category` feed the manifests. `--dry-run` lists the files without writing. The destination
must exist and the repository folder must not. The script does not run `git init` or touch anything outside the
new folder.

Every starter is explicitly unfinished. Replace it with the skill's actual behaviour and a meaningful fenced code,
command, configuration, or input/output example before the first validation; `template:check` rejects an unfinished
starter until that example exists. Standards grow through the new repository's `learning` decision procedure;
`scaffold` gets its scripts and templates once `structure` has an agreed File structure.

## Publish it

1. `uv lock`, `git init -b main`, commit, then `gh repo create <owner>/<name> --public --source . --push`; plugin
   repositories are public so the shared marketplace can install them and CI runs.
2. Only while a repository plugin CI reads is private: `gh secret set TJ_AGENTS_READ_TOKEN --repo <owner>/<name>`.
3. Add the plugin to the shared marketplace's `plugins.json` and regenerate it.

After Git initialization, use `agent:plugins` with the scaffolded `.agents/plugins.json`
to generate both native host settings and complete project admission/installation. Preserve other
selections. CI workflow imports alone do not install Template.

## Validation

The script fails if the new repository does not generate cleanly. Before the first push,
`pwsh .agents/sync-generated.ps1 -Check` and `check` pass in it; CI then runs both from Template's main branch.
