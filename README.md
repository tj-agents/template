# Template

Meta-scaffolder for plugin repositories. Every stack, tool, utility and profile plugin repository shares one layout, one
vendored generator and one CI workflow, all owned here. Install the Template package to use these procedures
and resources.

## Install

Install `template@template-agents`.

## Skills

- `template:new-plugin` creates a stack, tool, utility or profile plugin repository.
- `template:check` checks a plugin repository against the layout and the standard its type requires.
- `template:update` refreshes a plugin repository's vendored files from Template's main branch.

## Repository types

| Type | Skills created | Tier |
|---|---|---|
| stack | `knowledge`, `direction` (knowledge); `learning` (policy); `style`, `structure`, `domain-design`, `errors`, `testing`, `build`, `libraries` (convention); `scaffold` (utility) | applies where the stack is detected |
| tool | `knowledge`, `direction` (knowledge); `learning` (policy) | always |
| utility | the utility skills it needs | always |
| profile | a policy named by `--skill`, with supporting policies, conventions, workflows and utilities as needed | always, in projects that explicitly select it |

A profile bundles project policies without a stack's teaching and knowledge scaffolding. It depends on
`base@tj-agents` through the canonical marketplace. Declare mandatory host delivery in its shipped harness manifest;
an `always` tier makes a selected profile applicable, but does not itself load instructions into a session.

## Shared CI

Plugin repositories call `.github/workflows/plugin-ci.yml` from Template's `main` branch. The reusable workflow accepts a candidate `template_ref` override.
The workflow checks generated outputs, runs the `python:build` gate when the repository has a `pyproject.toml` (otherwise
its unittest suite), `template:check` and core's tier payload check, and
installs the marketplace with the real Claude Code and Codex CLIs. It reads Template, Core, React and .NET with
`GITHUB_TOKEN`; a repository supplies the `TJ_AGENTS_READ_TOKEN` secret, a fine-grained token with read-only Contents
access, only while one of them is private.

## Authoring and verification

```powershell
pwsh .agents/sync-generated.ps1
pwsh .agents/sync-generated.ps1 -Check
uv sync --locked
uv run ruff format --check
uv run ruff check
uv run mypy
uv run pytest
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
