---
name: new
description: Resolve ownership, naming and applicability before creating a skill, then delegate authoring to the current host's native skill creator. Use for direct skill-creation requests in any selected repository, including adding a skill to an existing plugin; existing skills use skill:update; new plugin repositories use template:new-plugin.
kind: workflow
domain: template
profile: core
applicability: skill authoring in selected repositories
requires: native skill creator
provenance: house
---

# Create a skill

Apply this constraint before native authoring. `skill:check` owns the skill contract, Template owns
projections, and the native creator owns the authoring method. Keep the existing goal and authorization.

```text
Request: add SQLx persistence guidance for a Rust/Tauri application.
Resolve: rust-sqlx:persistence, a separately selected sibling plugin in tj-agents/rust.
Scope: SQLx pools, bound queries and transactions; SQLite rules explicitly scoped.
Exclude: Tauri commands and product meal rules.
Delegate: the current host's discovered native skill creator, with this resolved brief.
Finish: Template generation/checks, evidence routes, then fresh Claude and Codex loading.
```

## Resolve the brief

Load `engineering:skill-authoring` for the shared existence, sizing, naming and collision rules.
Inspect the capability index, existing skills, repository instructions and selected policy. Extend the
existing concern owner when it already covers the behavior. Keep product behavior in its application.
Name ordinary ecosystem concerns by purpose: React validation can use explicitly selected Zod without
claiming Zod is required by React. Give a framework its own selectable namespace when its execution model,
lifecycle or substantial API practices warrant one, such as `efcore:specification` or `tauri:commands`.
Disambiguate cross-ecosystem library names: Rust SQLx and Go sqlx are unrelated, so use `rust-sqlx`.

A namespace need not have its own repository. The repository name identifies the main plugin; separately
named siblings may share that source repository, as dotnet/efcore do. Use existing payload, manifest and
tier contracts when registering a necessary sibling. Create no empty placeholder skill families.

Keep library policy and choices with one owner, such as `react:libraries`; detailed usage belongs to its
concern skill. State selected prerequisites and scope so optional choices stay optional. A standard
still follows its owner's learning/decision procedure; a creation request does not adopt invented rules.

Load `skill:check` and pass its content and executable asset requirements to the native creator.
Use the repository's selected skill format and source layout. In Template-layout repositories, apply
`template:structure` and choose the current kind independently of the source path. Author once under
`.agents/<namespace>/skills/<subject>/SKILL.md`, using family folders only for a useful subject grouping.
`template:check` validates the selected preset's metadata and required capabilities. Other layouts use the current host's native format and the
resolved source path. Do not impose Template metadata or tooling on a native-only skill.
Specify the published identity, discovery description, prerequisites, behavioral example and assets
actually needed. Do not author generated host copies or transplant host-specific UI metadata.

## Delegate native authoring

Read [native skill authoring](references/native-authoring.md) and use the current host's discovered
native creator with the resolved brief. Existing skill changes use `skill:update`.

## Integrate and verify

Add concern/framework evidence routes through the owning tier, or record explicit design-time
classification when no write evidence applies. Avoid routing every optional skill from a language
extension. Updates, renames and consolidations follow `skill:update`; keep only the current supported
identity in authored sources, generated discovery and installed selections.

Apply `skill:check` and the repository's existing validation. Template-layout repositories also run
their generator, `template:check`, generated freshness and corpus-reference/routing checks.
Verify fresh supported host discovery and loading.
Exercise a direct creation request: `skill:new` must load before native creator delegation.
Separate source checks from installed runtime acceptance and record any unresolved host gate.

Namespace suitability is a reviewed authoring decision. Keep deterministic layout/metadata validation
in the existing tools rather than inventing a naming popularity heuristic or another schema.
