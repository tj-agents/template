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
| stack | `knowledge`, `direction` (knowledge); `learning` (policy); `style`, `structure`, `domain-design`, `errors`, `testing`, `build`, `libraries` (convention); `scaffold` (utility) | applies where the stack is detected |
| tool | `knowledge`, `direction` (knowledge); `learning` (policy) | always |
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
