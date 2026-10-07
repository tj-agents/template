# kit

Meta-scaffolder for plugin repositories. Every stack, tool and utility plugin repository shares one layout, one
vendored generator and one CI workflow, all owned here.

## Skills

- `kit:new-plugin` creates a stack, tool or utility plugin repository.
- `kit:check` checks a plugin repository against the layout and the standard its type requires.
- `kit:update` moves a plugin repository to this kit release.

## Repository types

| Type | Skills created | Tier |
|---|---|---|
| stack | `learning`, `knowledge`, `direction`; `style`, `structure`, `domain-design`, `errors`, `testing`, `build`, `libraries`; `scaffold` | applies where the stack is detected |
| tool | `learning`, `knowledge`, `direction` | always |
| utility | the utility skills it needs | always |

## Shared CI

A plugin repository's `.github/workflows/ci.yml` calls `.github/workflows/plugin-ci.yml` at the kit tag it pins.
The workflow checks the generated outputs, runs the repository's own tests, `kit:check` and core's tier payload check, and
installs the marketplace with the real Claude Code and Codex CLIs. It reads the organization's private `kit` and
`core` repositories with the `TJ_AGENTS_READ_TOKEN` secret: a fine-grained token with read-only Contents access.

## Authoring and verification

```powershell
pwsh .agents/sync-generated.ps1
pwsh .agents/sync-generated.ps1 -Check
python -B -m unittest discover -s .agents/tests -p "test_*.py"
```

Utility tiers default to `always`; an explicitly scoped utility may declare `stack-present`, including core's v3
predicates. Core validates their detailed shape. New repositories include a self/dependency harness manifest under
`.agents/plugins/manifests/harness/`; the generator ships any declared manifest as `plugins/<plugin>/harness.json`.
Existing repositories can add one when needed. Selection dependencies accept local plugin names or exact
`marketplace/plugin` identities; the generator preserves external identities for the consuming harness.

`kit:check` also ships `scripts/check_skill_references.py`. Supply repeated `--root` arguments for the actual
plugin corpus; add `--source-root` to scan selected repositories against that inventory. Exact external skill
identities require a rationale in `.agents/plugins/skill-references.json`. Public CI checks the calling repository
against kit, core, react and dotnet, using `GITHUB_TOKEN` unless an optional read token is supplied.
