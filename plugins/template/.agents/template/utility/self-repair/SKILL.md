---
name: self-repair
description: Repair a demonstrated defect in tj-agents' own skills, hooks, scripts, routes or lifecycle tooling, under that source repository's repair authority. Use when a mistake or failure traces to a tj-agents standard or tool, before any host product feedback; defects in other codebases or standards use their own lifecycle.
kind: utility
domain: template
profile: core
applicability: tj-agents source repositories
requires: selected engineering lifecycle
provenance: house
---

# Repair tj-agents standards and tooling

Own a bounded repair of tj-agents' reusable agent instructions or tooling. Answer the user's direct
question first and correct the active task within its existing authority. Establish a causal source
defect before changing a standard; a mistake alone does not prove the standard is defective. Never send
host feedback for a tj-agents-caused mistake. Host product feedback is only for a separately established
host defect no tj-agents source can fix.
Apply [Workflow's incidental-problems decision](https://github.com/tj-agents/core/blob/main/.agents/workflow/resources/problem-records.md#incidental-problems)
before entering the repair phase. Preserve the active goal while applying the source's repair authority.

## Establish source and authority

Read the governing source and its repository's README.md and AGENTS.md. Automatic source handling requires all
of these conditions:

- The cause is a demonstrated defect in a reusable agent standard, skill, route, hook or lifecycle tool.
- Its owning source is an explicitly authorized `tj-agents` standards or tooling repository.
- The source repository has explicitly adopted personal scope and its selected policy authorizes the
  recording and repair, within the user's existing limits.

An organization name, publisher account or checkout location does not establish these conditions.
`tj-agents/infonetica` is employer tooling and remains outside this automatic personal routine. The
observing repository need not adopt Personal: the source's existing policy supplies authority for its
item. Import that policy and selected provider operation without changing the observing task's policy.

Keep employer-owned facts within the employer task. A personal tooling record may contain only the
independently supported reusable source defect, a sanitized reproduction and source-side evidence.
Do not copy employer code, logs, identifiers or task context into its tracker. If those boundaries
prevent an actionable source record, retain the unsent facts with the original task and explain the
resolver; do not publish them elsewhere.

Standards owned outside tj-agents, such as Concertable's, and product defects are outside this skill;
they use their owner's bugfix, feature or plan workflow with that owner's authorization.

If the existing rule is adequate and the agent overlooked it, correct the task and explain the evidence.
Conclude with no standards change when no reusable source defect is established. Do not invent a rule,
hook, work item or blocker to satisfy this workflow.

```text
Personal or employer task exposes a reproducible Core handoff defect; Core explicitly adopts Personal:
apply Core's recording policy to sanitized source evidence and reconcile its repair owner. Keep the
observing task active; an eligible unowned incidental repair receives a bounded source handoff.
The affected source is tj-agents/infonetica: follow its employer authority and evidence boundaries.
Agent skipped a clear testing instruction: run the required checks and correct the task; an adequate
instruction needs no source edit.
```

## Preserve ownership and recording decisions

Before changing a shared lifecycle, use `agent:recover` to check for a verified live owner of the
same repair. Reconcile that owner and contribute the evidence without creating a duplicate writer.
Keep the original task's owner and writer lease.

Record through the source repository's selected provider under its policy and Workflow's recording contract.
Creating a record, fixing the active task and repairing a source are separate decisions. Preserve
employer-owned facts within the authorized employer task; do not redirect them into a personal tracker.
Missing recording consent does not require a substitute record or prevent unaffected authorized work.

A shared lifecycle defect that makes ownership, completion, handoff or cleanup untrustworthy is P1 by
default. Suspend the affected operations while their safety or correctness is unresolved; preserve
recovery state. Priority alone does not pause unrelated tasks or authorize new launches or repairs.

## Repair the eligible source

For a direct source-repair request, enter its normal repair lifecycle. Correct a source defect required
for the active task's acceptance within that task's existing authority, establishing the dependency
with evidence. For an incidental eligible defect, apply its recording policy and refine the canonical
item with new evidence. Reuse a verified existing repair owner; when unowned, the standing source
routine authorizes a separate bounded repair handoff by default through `workflow:handoff`. Keep the
observing task's goal, owner and next action. An explicit user limit overrides that default. This rule
does not dispatch ordinary recorded backlog work.

The source repair uses a separate source checkout when the current checkout belongs to unrelated work.
Respect exclusions on product work, installation, destructive cleanup and unrelated redesign. A skill
change follows `skill:update`.

For an eligible automatic repair, standing authorization covers implementation, tests, review, pull
request, merge and publication in that source repository once its gates pass. It does not authorize
installation into a consuming repository or publication elsewhere. Outside automatic scope, use the
specific source-repair authority the user granted and that source's normal engineering lifecycle.

```text
The eligible Core repair already has a live owner and pending PR: append evidence to its authorized
record and reconcile with that owner. Do not start a second writer or take over its delivery.
An eligible incidental Core repair has no owner: record its source evidence and hand off that bounded
repair, then continue the original task. The new source owner maintains its verified issue and boards.
```

## Preserve existing delivery ownership

When the user asks to wait for or monitor an existing pull request or delivery, treat that request as
monitoring-only. Resolve and observe the existing delivery identity without changing its worktree,
branch, binding, head, review, queue state or merge state.

Monitoring does not grant delivery authority. A transfer or merge-state change requires authority for
that exact delivery plus its ownership-transfer procedure. Standing auto-merge authorization never
authorizes taking over an unrelated pending delivery.

## Complete truthfully

Keep the original task active through a deferred repair or no-source-change outcome. After a selected
source repair is tested and committed, return to its preserved next action unless the user changed that
priority. Explain any proposed repair awaiting a decision or genuine blocker. Retain unsent facts in the
existing task when recording is not authorized. A proposal is not a completed repair.

When delivery is authorized, own it through the source repository's gates. Report source correction,
publication and installed-host verification separately; a source commit does not update instructions
already loaded in the originating session. Verify the affected supported entry points before claiming
installed behavior is repaired, or name the unverified entry point and its observable acceptance.
