---
name: new-skill
description: Resolve ownership, naming and applicability before creating, splitting, renaming or consolidating a skill, then delegate authoring to the current host's native skill creator. Use for direct skill-creation requests in any selected repository, including adding a skill to an existing plugin; new repositories use new-plugin.
kind: utility
domain: template
profile: core
applicability: skill authoring in selected repositories
requires: native skill creator, python, pwsh
provenance: house
---

# Create a skill

Apply this constraint before native authoring. Template owns the shared contract and projections;
the native creator owns the authoring method. Keep the existing goal and authorization.

```text
Request: add SQLx persistence guidance for a Rust/Tauri application.
Resolve: rust-sqlx:persistence, a separately selected sibling plugin in tj-agents/rust.
Scope: SQLx pools, bound queries and transactions; SQLite rules explicitly scoped.
Exclude: Tauri commands and product meal rules.
Delegate: the current host's discovered native skill creator, with this resolved brief.
Finish: Template generation/checks, evidence routes, then fresh Claude and Codex loading.
```

## Resolve the brief

Inspect the capability index, existing skills, repository instructions and selected policy. Extend the
existing concern owner when it already covers the behavior. Keep product behavior in its application.
Name ordinary ecosystem concerns by purpose: `react:validation` can use explicitly selected Zod without
claiming Zod is required by React. Give a framework its own selectable namespace when its execution model,
lifecycle or substantial API practices warrant one, such as `efcore:specification` or `tauri:commands`.
Disambiguate cross-ecosystem library names: Rust SQLx and Go sqlx are unrelated, so use `rust-sqlx`.

A namespace need not have its own repository. The repository name identifies the main plugin; separately
named siblings may share that source repository, as dotnet/efcore do. Use existing payload, manifest and
tier contracts when registering a necessary sibling. Create no empty placeholder skill families.

Keep library policy and choices with one owner, such as `react:libraries`; detailed usage belongs to its
concern skill. State selected prerequisites and scope so optional choices stay optional. A convention
still follows its owner's learning/decision procedure; a creation request does not adopt invented rules.

Choose the current kind and metadata from `template:check` and its canonical standard. Current scaffolds
use convention, policy, knowledge and utility; do not copy legacy contract metadata into a new skill.
Author once under `.agents/<plugin>/<kind>/<name>/SKILL.md`, with family folders where appropriate.
Specify the published identity, discovery description, prerequisites, behavioral example and assets
actually needed. Do not author generated host copies or transplant host-specific UI metadata.

## Delegate native authoring

Discover the current host's advertised creator and load it only after resolving the brief above.
For Codex, use the native `skill-creator` capability from its current skill catalog. For Claude Code,
discover the installed Anthropic Skill Creator plugin's advertised skill; the official plugin is
`skill-creator@claude-plugins-official` ([upstream](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator)).
Resolve its actual invocation from native discovery rather than assuming a slash-command identity.

Pass the resolved identity, source path, concern boundary, selected prerequisites, concrete use case,
Template metadata/layout requirements and acceptance checks to that creator. Let it choose its authoring
and evaluation method within those constraints. Do not embed another general-purpose creation workflow,
copy the creator, or let a native initializer move the canonical source into a user profile.

If the native creator is missing, report the exact host/capability gap and use an authorized supported
installation path when available. Keep dependent authoring pending until discovery succeeds; continue
independent work. Do not silently bypass this gate or substitute the other host's metadata.

## Integrate and verify

Add concern/framework evidence routes through the owning tier, or record explicit design-time
classification when no write evidence applies. Avoid routing every optional skill from a language
extension. For a rename or consolidation, apply the selected clean-cut policy to known references,
selections, routes, templates and generated payloads in the same cutover; leave no forwarding alias
when that policy forbids it.

Regenerate with the repository's supported generator, run `template:check`, generated freshness and
focused corpus-reference/routing checks, and verify fresh Codex and Claude discovery and loading.
Exercise a direct creation request: this Template gate must load before native creator delegation.
Separate source checks from installed runtime acceptance and record any unresolved host gate.

Namespace suitability is a reviewed authoring decision. Keep deterministic layout/metadata validation
in the existing tools rather than inventing a naming popularity heuristic or another schema.
