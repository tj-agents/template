# Native skill authoring

## Resolve the outcome before the edit

State the user's intended outcome and explicit constraints separately from an agent's proposed fix.
For a behavior or integration change, apply `base:solution-assessment` before prescribing the edit,
carrying forward that idea's completed assessment and its rationale in the existing task context.
Routine wording edits reuse the existing decision. Preserve a user-required approach; if it conflicts
with the outcome or project constraints, surface that conflict rather than silently replacing it.

Use the assessment to select the owning boundary. The result may require deterministic code or an
existing native integration rather than additional instructions. Give the creator the outcome,
constraints, relevant existing capabilities, assessment and observable acceptance conditions so it can
challenge an agent's proposed edit. Keep any resulting work within the existing authorization.

```text
Outcome: generated release metadata reflects the selected package version.
User constraint: keep the existing release command.
Agent proposal: add a reminder to the release skill.
Assessment: the existing generator owns these values and already runs from that command.
Brief: repair that generator path and keep the skill's invocation current.
Check: invoke the release command in its existing test fixture and inspect the generated metadata;
       a well-formed reminder would not establish the requested behavior.
```

## Use the native creator

Discover the current host's advertised creator and load it after resolving the brief.
For Codex, use the native `skill-creator` capability from its current skill catalog. For Claude Code,
discover the installed Anthropic Skill Creator plugin's advertised skill; the official plugin is
`skill-creator@claude-plugins-official` ([upstream](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator)).
Resolve its actual invocation from native discovery rather than assuming a slash-command identity.

Pass the resolved brief, identity, source path, concern boundary, selected prerequisites, concrete use case,
selected project metadata/layout requirements and acceptance checks to that creator. Let it choose its authoring
and evaluation method within those constraints. Do not embed another general-purpose creation workflow,
copy the creator, or let a native initializer move the canonical source into a user profile.

If the native creator is missing, report the exact host/capability gap and use an authorized supported
installation path when available. Keep dependent authoring pending until discovery succeeds; continue
independent work. Do not silently bypass this gate or substitute the other host's metadata.
