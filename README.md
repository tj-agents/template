# Template

Template owns plugin repository layout, scaffolding, generated host projections and structural validation.
Its sibling Skill plugin owns skill authoring and the shared content and executable asset contract.

## Install

Install `template@tj-agents`; its authoring dependency is `skill@tj-agents`, published from this repository.

## Skills

- `skill:new` resolves a new skill's concern and scope before native creator delegation.
- `skill:check` owns skill content checks and the requirement for separate typed executable source files.
- `skill:update` updates existing skills and completes renames without old entries or compatibility aliases.
- `template:structure` owns the shared authored, generated and installed source layout.
- `template:new-plugin` creates a stack, tool, plugin or profile repository.
- `template:check` checks a plugin repository against the layout and the standard its type requires.
- `template:update` refreshes a plugin repository's vendored files from Template's main branch.

## Create a skill

Use `skill:new` for a new skill and `skill:update` when changing an existing skill. Both apply `skill:check`
and the selected ownership, naming and applicability constraints before delegating to the discovered native creator.
The repository names the main plugin; separately selectable sibling namespaces can share it.
The selected Skill tier supplies session routing and a canonical-skill write gate through Core.
Native creator availability and fresh host loading are verified separately from source selection.

## Repository types

| Type | Skills created | Tier |
|---|---|---|
| stack | `learning` (learning), `direction` (reference), construction standards and `scaffold` (operation); learner data under `learning/` | applies where the stack is detected |
| tool | `learning` (learning), `direction` (reference); learner data under `learning/` | always |
| plugin | a first skill named by `--skill`, classified explicitly with `--skill-kind` | always or explicitly scoped |
| profile | a policy named by `--skill`, with other responsibilities as needed | always, in projects that explicitly select it |

Each preset permits all six kinds: policy, standard, operation, workflow, learning and reference. Presets
select starter content and required capabilities; they do not classify every additional skill. Authored
skills live under `.agents/<namespace>/skills/<subject>/SKILL.md`. A kind change does not move the skill.

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

Plugin tiers default to `always`; an explicitly scoped plugin may declare `stack-present`, including core's v3
predicates. Core validates their detailed shape. New repositories include a self/dependency harness manifest under
`.agents/plugins/manifests/harness/`; the generator ships any declared manifest as `plugins/<plugin>/harness.json`.
Existing repositories can add one when needed. Selection dependencies accept local plugin names or exact
`tj-agents/<plugin>` identities. `tj-agents` is the only marketplace: the generator names both repository
marketplace files `tj-agents`, drops any other harness marketplace, and `template:check` fails on any other.

`payloads.json` may also ship explicit package resources: a file or recursive directory from `.agents/hooks`, a
declared canonical plugin's `.agents/<plugin>/references`, `learning` or `assets` directory, or discovered skill assets beside
that plugin's canonical `SKILL.md`, maps into `plugins/<package>/<destination>`. Optional host discovery extensions
append from the exact declared `.agents/plugins/adapters/<host>/<plugin>/<skill>.md` source, while the canonical skill
body remains singular. Packages with host extensions keep Claude entries in `skills/` and ship separate Codex entries
in `codex-skills/`; their generated Codex manifest selects that latter path.

A Python library resource replaces `source` with its distribution name. The distribution must be a runtime
dependency in `pyproject.toml`, resolved by committed `uv.lock`. Generation uses `uv run --locked --no-editable`
to collect its installed pure Python wheel; it never imports the library. Declare every distribution needed
at runtime. Native extensions, `.pth` import hooks and records outside the installed package root are rejected.
Installation receipts and caches are omitted; package code, data, licenses and stable wheel metadata ship.
Host adapters establish their shipped package root, then use normal public imports. Neither generation nor
runtime locates a sibling source checkout.

Resources mapped beneath `skills/<skill>/` also ship beside that skill's repository-local Claude and
Codex scripts, and beside a separate installed Codex entry when declared. This keeps all generated
entry points able to import the same bundled library. Authored source runs in the project's uv environment.

```json
{"plugin": "demo", "distribution": "owner-library", "destination": "python"}
```

`template:check` also ships `scripts/check_skill_references.py`. Supply repeated `--root` arguments for the actual
plugin corpus; add `--source-root` to scan selected repositories against that inventory. Exact external skill
identities require a rationale in `.agents/plugins/skill-references.json`. Public CI checks the calling repository
against Template, Core, React, .NET and Rust, using `GITHUB_TOKEN` unless an optional read token is supplied.
