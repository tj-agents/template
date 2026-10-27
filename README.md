# Template

Template owns the plugin and skill contract: required content, metadata, layout,
scaffolding, generated host projections, and validation across plugin repositories.
It links to Core's generic documentation guidance for authoring decisions.

## Install

Install `template@tj-agents`.

## Skills

- `template:new-skill` resolves concern ownership and scope before delegating to the current host's native creator.
- `template:new-plugin` creates a stack, tool, utility or profile plugin repository.
- `template:check` checks a plugin repository against the layout and the standard its type requires.
- `template:update` refreshes a plugin repository's vendored files from Template's main branch.

## Create a skill

Use `template:new-skill` before authoring a new skill in an existing plugin. It applies Template's
ownership, naming and applicability constraints, then delegates to the discovered native creator.
The repository names the main plugin; separately selectable sibling namespaces can share it.
The selected Template tier supplies session routing and a canonical-skill write gate through Core.
Native creator availability and fresh host loading are verified separately from source selection.

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
its unittest suite), Template's skill-content and layout validation, core's tier payload check, and
installs the marketplace with the real Claude Code and Codex CLIs. It reads Template, Core, React, .NET and Rust with
`GITHUB_TOKEN`; a repository supplies the `TJ_AGENTS_READ_TOKEN` secret, a fine-grained token with read-only Contents
access, only while one of them is private.

## Authoring and verification

Every added or updated skill must show its actual behaviour in a meaningful fenced code, command, configuration, or
input/output example. `template:check` validates that contract for local edits and CI's exact committed range; it does
not require a retrofit of unchanged skills.

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
`tj-agents/<plugin>` identities. `tj-agents` is the only marketplace: the generator names both repository
marketplace files `tj-agents`, drops any other harness marketplace, and `template:check` fails on any other.

`payloads.json` may also ship explicit package resources: a file or recursive directory from `.agents/hooks`, a
declared canonical plugin's `.agents/<plugin>/runtime` or `resources` directory, or discovered skill assets beside
that plugin's canonical `SKILL.md`, maps into `plugins/<package>/<destination>`. Optional host discovery extensions
append from the exact declared `.agents/plugins/adapters/<host>/<plugin>/<skill>.md` source, while the canonical skill
body remains singular. Packages with host extensions keep Claude entries in `skills/` and ship separate Codex entries
in `codex-skills/`; their generated Codex manifest selects that latter path.

A Python library resource replaces `source` with its distribution name. The distribution must be a runtime
dependency in `pyproject.toml`, resolved by committed `uv.lock`. Generation uses `uv run --locked --no-editable`
to collect its installed pure Python wheel; it never imports the library. Declare every distribution needed
at runtime. Native extensions, `.pth` import hooks and records outside the installed package root are rejected.
Installation receipts and caches are omitted; package code, data, licenses and runtime distribution metadata ship.
Build records (`WHEEL` and `uv_build.json`) are also omitted: their tool-version information must not make
the generated runtime depend on the builder installed on a particular machine. Wheel purity is checked
before selecting the runtime files. Runtime distribution metadata and entry points remain available.
Host adapters establish their shipped package root, then use normal public imports. Neither generation nor
runtime locates a sibling source checkout.

Resources mapped beneath `skills/<skill>/` also ship beside that skill's repository-local Claude and
Codex scripts, and beside a separate installed Codex entry when declared. This keeps all generated
entry points able to import the same bundled library. Authored source runs in the project's uv environment.

```json
{"plugin": "demo", "distribution": "owner-library", "destination": ".agents/demo/runtime"}
```

`template:check` also ships `scripts/check_skill_references.py`. Supply repeated `--root` arguments for the actual
plugin corpus; add `--source-root` to scan selected repositories against that inventory. Exact external skill
identities require a rationale in `.agents/plugins/skill-references.json`. Public CI checks the calling repository
against Template, Core, React, .NET and Rust, using `GITHUB_TOKEN` unless an optional read token is supplied.
