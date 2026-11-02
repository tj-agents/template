# Skill selection

Use this reference while resolving a skill's public identity. A skill is selected only when its name and
description match the work, while every installed identity consumes discovery attention.

## Concern and size

Inspect the capability index and existing skills on both hosts first. Extend the existing concern owner
when the same task already loads it. Create a skill only for a subject that a task independently consumes.

Split a skill only when both concerns are independently consumed and loading the other would add real
context cost or mislead the task. Do not split by trigger count, section count or file length. Merge skills
when every task that loads one also loads the other; keep their supporting examples and guards together.

```text
Request: add a small naming rule to an existing review skill.
Decision: extend review; the same review task already loads it.
```

## Identity and discovery

Choose a lowercase hyphenated name for the subject a reader is looking for. Before publishing it, check
both hosts for the same bare name and near misses such as plurals, reordered words or changed hyphenation.
Use a qualified `plugin:name` when referring to a shared bare name.

Write a discriminating description that states what the skill owns and says `Use when …` for only its
selection trigger. A broad description makes skills compete and obscures the right owner.

## Native capability and source

Use a host's native capability directly when it meets the request. A wrapper needs a concrete missing
workflow, policy or host capability; a copied command reference or alternate spelling does not earn a
public identity.

```text
Request: inspect native memory settings.
Decision: use the host's native controls; no wrapper skill is needed.
```

Keep one canonical definition and update each host's discovery metadata with it. Include only scripts,
resources and assets that ship with the skill and directly support its work.
