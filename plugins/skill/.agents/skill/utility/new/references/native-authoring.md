# Native skill authoring

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
