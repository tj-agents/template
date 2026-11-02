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
defect before changing a standard; a mistake alone does not prove the standard is defective. Do this
before any host product feedback, which is only for a genuine host defect no tj-agents source can fix.
Apply [Workflow's incidental-problems decision](https://github.com/tj-agents/core/blob/main/.agents/workflow/resources/problem-records.md#incidental-problems)
before entering the repair phase. The active goal determines when that repair authority is exercised.

## Establish source and authority

Read the governing source and its repository's README.md and AGENTS.md. Automatic repair requires all
of these conditions:

- The cause is a demonstrated defect in a reusable agent standard, skill, route, hook or lifecycle tool.
- Its owning source is an explicitly authorized `tj-agents` standards or tooling repository.
- Both the originating task and the source repository have explicitly adopted personal scope, and the
  repair remains within the user's existing limits.

An organization name, publisher account or checkout location does not establish these conditions.
`tj-agents/infonetica` is employer tooling and remains outside automatic repair. An employer task does
not grant automatic repair authority even when the proposed destination is personal tooling. Explain
the defect and propose a separate source repair within the employer's evidence boundaries.

Standards owned outside tj-agents, such as Concertable's, and product defects are outside this skill;
they use their owner's bugfix, feature or plan workflow with that owner's authorization.

If the existing rule is adequate and the agent overlooked it, correct the task and explain the evidence.
Conclude with no standards change when no reusable source defect is established. Do not invent a rule,
hook, work item or blocker to satisfy this workflow.

```text
Personal task exposes a reproducible Core handoff defect; Core is explicitly adopted personal tooling:
establish eligible source authority, then apply Workflow's active-goal decision before repair.
Infonetica task exposes the same defect: correct the active task where authorized and propose a separate
source repair; no employer tracker item or cross-repository repair follows automatically.
Agent skipped a clear testing instruction: run the required checks and correct the task; an adequate
instruction needs no source edit.
```

## Preserve ownership and recording decisions

Before changing a shared lifecycle, use `agent:recover` to check for a verified live owner of the
same repair. Reconcile that owner and contribute the evidence without creating a duplicate writer.
Keep the original task's owner and writer lease.

Record only through the repository's selected problem-record profile under Workflow's recording contract.
Creating a record, fixing the active task and repairing a source are separate decisions. Preserve
employer-owned facts within the authorized employer task; do not redirect them into a personal tracker.
Missing recording consent does not require a substitute record or prevent unaffected authorized work.

A shared lifecycle defect that makes ownership, completion, handoff or cleanup untrustworthy is P1 by
default. Suspend the affected operations while their safety or correctness is unresolved; preserve
recovery state. Priority alone does not pause unrelated tasks or authorize new launches or repairs.

## Repair the eligible source

When repair is selected under Workflow's active-goal decision, fix the standard or tool in the current
session. For an incidental eligible defect, complete its recording decision and continue the active goal.
When the current checkout belongs to unrelated work,
use a separate worktree of the source repository from its current default branch. Hand the repair off
only when the user asks. Respect exclusions on product work, installation, destructive cleanup and
unrelated redesign. A skill change follows `skill:update`.

For an eligible automatic repair, standing authorization covers implementation, tests, review, pull
request, merge and publication in that source repository once its gates pass. It does not authorize
installation into a consuming repository or publication elsewhere. Outside automatic scope, use the
specific source-repair authority the user granted and that source's normal engineering lifecycle.

```text
The eligible Core repair already has a live owner and pending PR: append evidence to its authorized
record and reconcile with that owner. Do not start a second writer or take over its delivery.
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
