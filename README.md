# Template

Meta-scaffolder for plugin repositories. Every stack, tool and utility plugin repository shares one layout, one
vendored generator and one CI workflow, all owned here. Install the Template package to use these procedures
and resources.

## Install

Install `template@template-agents`.

## Skills

- `template:new-plugin` creates a stack, tool or utility plugin repository.
- `template:check` checks a plugin repository against the layout and the standard its type requires.
- `template:update` refreshes a plugin repository's vendored files from Template's main branch.

## Repository types

| Type | Skills created | Tier |
|---|---|---|
| stack | `knowledge`, `direction` (knowledge); `learning` (policy); `style`, `structure`, `domain-design`, `errors`, `testing`, `build`, `libraries` (convention); `scaffold` (utility) | applies where the stack is detected |
| tool | `knowledge`, `direction` (knowledge); `learning` (policy) | always |
| utility | the utility skills it needs | always |

## Shared CI

Plugin repositories call `.github/workflows/plugin-ci.yml` from Template's `main` branch. The reusable workflow accepts a candidate `template_ref` override.
The workflow checks generated outputs, runs the repository's own tests, `template:check` and core's tier payload check, and
installs the marketplace with the real Claude Code and Codex CLIs. It reads the organization's private Template and
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

`template:check` also ships `scripts/check_skill_references.py`. Supply repeated `--root` arguments for the actual
plugin corpus; add `--source-root` to scan selected repositories against that inventory. Exact external skill
identities require a rationale in `.agents/plugins/skill-references.json`. Public CI checks the calling repository
against Template, Core, React and .NET, using `GITHUB_TOKEN` unless an optional read token is supplied.
