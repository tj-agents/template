---
name: check
description: Check a skill's content, metadata, examples and executable assets against the shared skill contract. Use when authoring or reviewing a skill; plugin repository layout checks use template:check.
kind: utility
domain: template
profile: core
applicability: skill authoring and review
requires: selected project validation tools
provenance: house
---

# Skill check

Assess the canonical skill and its shipped host adapters and assets. `skill:new` and `skill:update`
apply this contract before native authoring and when verifying the result. `engineering:skill-authoring`
owns concern selection, sizing, naming and discovery triggers. For Template-layout repositories,
`template:check` owns repository layout and its machine-checked kind and metadata standard.

```text
Request: review a skill that polls CI through an inline Python heredoc.
Change: ship the polling implementation in scripts/watch.py with typed inputs and outputs.
Skill: reference that file and show its concise invocation.
Verify: run the selected type checker and focused behavior tests; review the instructions and host loading.
Native-only skill: validate its native format; Template is not required.
Template repository: also run its generator and template:check.
```

## Content and metadata

Check that the name, description and supported metadata match the canonical source and each host's
discovery entry. Apply the format, kind and required sections selected by the host and project.
Template-layout repositories use `template:check`'s standard for their additional metadata and sections.
Every convention or contract opens with `Owns …` after its title. Each added or updated skill includes
a meaningful fenced code, invocation, configuration or input/output example of its actual behavior.
Follow `engineering:docs` for one rule per owner and concrete examples; a teaching example may stay inline.

## Executable skill assets

Keep a skill's executable implementation in separate source files under its `scripts/` directory.
Shared implementation belongs in the existing owning runtime; host-specific code follows that host's
runtime layout. `SKILL.md` and host adapters give instructions, reference the shipped files and show
concise invocations. Do not make the agent reconstruct executable logic from Markdown code blocks,
heredocs or inline interpreter strings on each run.

Use deterministic scripts for work determined by fixed inputs. Give their inputs and outputs explicit
types, include the files in the project's selected type-checking or compiler checks, and test meaningful
behavior. Moving code into a file alone does not provide type safety. Use native host tools where they
already supply the required behavior; this placement rule does not justify reimplementing them.

Short invocation, configuration and teaching examples may remain inline. They demonstrate the skill's
behavior; they are not a second implementation for the agent to copy and execute.

## Verify the result

Run the validation applicable to the selected format and project. Native-only skills use the current
host's native creator validation. Template-layout repositories use their existing generator and
`template:check` for layout, metadata, references and examples; Template's extended metadata follows
that validator rather than a native-format-only schema.
Run the selected type checker or compiler and focused tests for changed executable assets. Review content
and asset placement directly: the layout checker does not infer whether an arbitrary code block is an
implementation or an example. Verify fresh supported host discovery and loading when entry points change,
and report any unverified installed entry point with its resolver and observable acceptance condition.
