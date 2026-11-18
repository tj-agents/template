---
name: review
description: Run the canonical isolated code-review workflow over one frozen branch, PR, commit-range, or path candidate with the host's native reviewer, relevant fresh read-only lenses, validated evidence, and parent-only deduplication, severity, judgment, and work-order writing. Use for a first full code review when asked to review a branch or PR; use incremental-review for later commits, big-review for a very large diff, docs-review for a meta-only diff, and address-review for existing findings.

kind: workflow
domain: process
---

# Canonical isolated code review

Review one immutable candidate through the host's mandatory native reviewer and relevant repository-aware lenses.
Subordinate contexts return evidence only. The strong parent validates every result, verifies citations,
deduplicates, assigns severity, makes the final judgment, and is the sole writer of the canonical work order
defined by `review-lifecycle`.

## Arguments and selection

```text
[low|medium|high|max] [<pr-number>|<branch>|<path>] [--comment] [--fix]
```

- Effort applies to the native layer and every lens. `low` and `medium` keep only high-confidence defects;
  `high` and `max` broaden coverage and may retain lower-confidence findings when their uncertainty and
  concrete fix are explicit. With no value, reuse the last review effort.
- No target means the current worktree's branch. A PR resolves its base, head branch, and head SHA through the
  forge. Resolve a branch's actual base from its open PR or owning stack map: the immediate parent for
  a stack child, otherwise the trunk. A path scopes that same branch candidate.
- `--comment` posts finalized findings to the target PR after the work order is complete.
- `--fix` explicitly authorizes the combined review -> `address-review` -> `incremental-review` lifecycle.
  The same transition is authorized when this review is a stage of an implementation workflow whose original
  request already authorized fixing its candidate. Otherwise review is read-only and ends after judgment.

`<engineering>` is the installed engineering plugin root: two directories above this skill's host entry
point (`<engineering>/skills/review/` in Claude Code, `<engineering>/codex-skills/review/` in Codex). Every
helper below runs from there against the reviewed repository, which needs no `.agents/` of its own.

Use `incremental-review` when the canonical work order already has a completed watermark and HEAD moved.
Use `big-review` when the frozen changed surface is too large for one pass, normally more than 300 files or
several substantial components. Use `docs-review` for a documentation/meta-only diff.

## Stage 1 — resolve and freeze the candidate

Resolve the target before reading or writing review state. An implementation workflow synchronizes with the
remote base exactly once, immediately before this final review, while the worktree is clean. Then invoke the
shared deterministic review preparation operation:

Run these Python workflow commands with `python` on Windows or `python3` on Linux/macOS:

```bash
python <engineering>/workflows/workflow_ops.py --root <repository-root> --workflow-run-id <id> review-prepare --base <actual-base> --head HEAD --synchronize
```

Use the same resolved actual base for preparation, reconciliation and PR preflight. A stack child's
review covers its layer against the parent; its tests still validate the cumulative tree. Do not merge
main directly into each child as a substitute for reconciling the stack from its bottom.

A review-only request over an already immutable remote or commit candidate omits `--synchronize`. The helper
returns one compact Git-private descriptor and an external temporary bundle containing the binary patch and NUL path manifest. It
also records the one synchronization, candidate identity, routed rule hashes, relevant lenses, security-path
classification, and one wave.
Do not reconstruct those facts through separate shell calls.

Freeze a candidate descriptor containing the full base SHA, full head SHA, target branch, scope as `all` or
an exact bounded value,
exact sorted changed-path set, SHA-256 of their UTF-8 bytes joined by one NUL byte with no trailing NUL, path
count, canonical work-order path, and new-or-append mode. Every later command and dispatch uses
`<base>..<head>`, never a live replacement
for `<head>`.

The helper stores the authoritative descriptor in repository-private Git state and materializes the candidate
bundle defined by `review-lifecycle` in an external temporary cache. It validates the exact patch, NUL path
manifest, descriptor identity, and hashes before returning.
Add its paths and identities to every immutable-artifact set. A host without safe read-only Git reads this
bundle; no reviewer depends on the implementation transcript.

When the descriptor reports `host_coverage.required`, its frozen paths touch an agent surface.
`base:plan-artifacts` owns the coverage-record shape and evidence requirements.

If the branch moves while work is active, do not widen the pass. Cancel any dispatch whose baseline is no
longer trustworthy, finish or restart the frozen pass, and leave later commits to `incremental-review`.

## Stage 2 — open the canonical work order

Read `review-lifecycle`. Use only `reviews/<branch-slug>.md`; staged, documentation, and incremental modes
share it. Before expensive review work, have the parent create the immutable pass identity and set
the top-level `Review status`, current `Judgment`, and new `Pass judgment` to `in-progress`, `pending`, and
`pending`. A first pass has no completion watermark yet. An interrupted
incremental pass retains the earlier completed watermark but remains merge-blocking through its status.
Record every descriptor field, including branch, scope, bundle path and identity, canonical work-order path,
and `new` or `append` mode, before dispatch.

No lens writes the artifact. Append a confirmed finding only after the parent validates its result and
evidence. The parent may buffer independent lens results long enough to synthesize them together; recovery
identity and confirmed findings must remain durable.

## Stage 3 — native layer

Run the host's own native reviewer first, covering correctness, simplification, reuse, efficiency, and
error handling, over the frozen range `<frozen-base>..<frozen-head>` and scope. `review`'s host entry point
names that reviewer and its invocation (`<engineering>/skills/review/SKILL.md` in Claude Code,
`<engineering>/codex-skills/review/SKILL.md` in Codex). It is a tool call; reading the diff yourself is not
this layer. Keep only findings on lines changed inside the frozen range and scope. When the host
reviewer is not callable in this session, dispatch the existing `review-lens` capability with the bounded
lens `native-general` instead. Record in the work order which native layer ran. Do not invent or require a
second repository agent definition.

A `native-general` dispatch receives the frozen base, head, path digest, exact scoped paths, materialized
bundle path and identity, effort, rule-independent objective, read-only tools, and no prior lens
conclusions. Validate the result against Workflow v2 before using it. Agent/role/model unavailability falls
back to the parent over the same descriptor and bundle.

## Stage 4 — load applicable rules

Two mechanical rule sources; neither depends on anything wired into the reviewed repository.

**Tier conventions — every repository.** Run the tier gate shipped with this plugin in conventions mode
against the reviewed repository root, using `python` on Windows or `python3` on Linux/macOS:

```bash
python <engineering>/hooks/tier_gate.py --conventions --project <repository-root>
```

The base package's tiers README owns the output contract. Read every listed convention whose domain the
frozen paths plainly touch, and check each changed file against the conventions of the tier(s) that own
its language. Do not substitute the session's already-loaded skill list for this resolution; the gate
reads the same installed declarations that gated the session.

**Repository routes — repositories that carry them.** When the frozen tree ships `.agents/skill-routes.json`,
`review-prepare` runs this plugin's router over it: the descriptor's `routed_skills` names every skill the
frozen paths owe, plugin-owned ones included, and `route_violations` holds each deny-pattern hit. A
repository without a route table owes only its tier conventions; that absence is normal, not a defect.

Read every routed skill, the root and nearest changed-path `AGENTS.md` files, and the architecture premise
from the exported frozen tree, never the live checkout. A route violation is evidence, not a hint.
Invoke additional standards only when the diff plainly touches their domain; a missing route is a
route-table defect rather than a list to duplicate here. If the candidate contains plans or
implementation-ready design references, load plans and apply its implementation-design review gate to
those artifacts, including their implementation-path standards.

Record the owning `review` lifecycle and the helper's routed technical rule identities with
`<engineering>/workflows/workflow_ops.py skills`. Read only identities returned as `load`; an unchanged
identity returned as `cached` is already available to this logical workflow and is not reread after
compaction. The descriptor's hashes prove whether a cached body still matches the frozen candidate. Check
every changed file against each routed rule; a changed or missing hash requires a new body read.

## Stage 5 — choose and dispatch fresh lenses

Choose only lenses supported by the frozen paths, rules, and risk:

- correctness: logic, concurrency, boundaries, exceptions, and observable failure paths;
- service isolation: runtime coupling that violates the repository's service-boundary owner;
- module boundaries: facade, visibility, and persistence ownership violations;
- seeding: writes production cannot make through the same path;
- language/framework conventions: only rules stated by the loaded standards; and
- changed-behaviour test impact: one concrete missing assertion for behavior this candidate adds or reroutes.

Each bounded dispatch uses `review-lens`, a unique dispatch/context identity, the same immutable candidate
artifacts including the materialized bundle path and identity, one exact lens or region, read-only
permissions, no subdispatch, and no sibling conclusions.
Dispatch the helper-selected lenses together in its single wave. A small candidate normally selects only
`native-general` plus a path-proven specialist lens. If a lens depends on another result, return that check to
the parent instead of starting another source-review wave. Very large candidates route to `big-review` for
staged coverage. Writers never participate in review production.

Validate each result identity, status, citations, confidence, acceptance conditions, and decision boundary.
A malformed or correctable incomplete result gets at most one focused follow-up without widening scope.
Unsupported dispatch, timeout, cancellation, or a second invalid result closes that dispatch and returns the
same bounded check to the parent. Obsolete results from a different base, head, path digest, stage, or
dispatch ID contribute nothing.

## Stage 6 — conditional security layer

The descriptor's `security` field applies the merge gate's generic and repository `security_paths`
inventory: `first_path` to the frozen paths, `trunk_first_path` to `<trunk_base>..<frozen-head>`, the range
the gate classifies. Run the layer when `first_path` is set, or when `trunk_first_path` is set and the work
order's `Security-reviewed up to commit:` marker is missing, unresolvable, or followed by a change to a
security-sensitive path before the frozen head. It covers `<trunk_base>..<frozen-head>`, or
`<frozen-base>..<frozen-head>` when `trunk_base` is null, through the host security reviewer that `review`'s
host entry point names. When the host has none that reviews exactly that range, dispatch `review-lens` with
the bounded lens `security` over it. Security evidence joins parent synthesis, while the marker is written
only when the whole pass completes. No qualifying path means no security marker.

## Stage 7 — parent synthesis and completion

The parent independently checks cited evidence and reads beyond the frozen diff only to confirm a candidate.
Drop pre-existing issues on unchanged lines, compiler/linter failures CI already owns, preferences no loaded
rule states, intentional changes, and anything below the effort-adjusted confidence bar.

Every retained finding is a defect the parent would fix and names one concrete fix. Do not keep hedged
observations. Deduplicate across native, security, concern, and region results by underlying defect and
evidence, preserving stable IDs. Lenses do not supply final severity or approval; the parent assigns
severity, writes one judgment, and records findings in the canonical shape from `review-lifecycle`.

Before completing an agent-surface pass, update the canonical work order's one moving coverage record for
the frozen head, then run with `python` on Windows or `python3` on Linux/macOS:

```bash
python <engineering>/workflows/workflow_ops.py --root <repository-root> --workflow-run-id <id> review-host-check --descriptor <descriptor-path> --work-order <canonical-work-order>
```

The command validates that record against the descriptor's frozen paths and exact head. A failed check keeps
the review incomplete.

On completion, set `Review status` to `complete`, set the current and active-pass judgments, stamp the single
`Reviewed up to commit:` marker at the frozen head, and stamp the security marker there when required. If
HEAD moved, this completed pass remains truthful at its frozen head and the later delta belongs to
`incremental-review`.

Remove the disposable candidate bundle after completion, cancellation, or terminal failure. An interrupted
pass may be resumed only after regenerating the bundle from its recorded descriptor and reproducing the
recorded bundle identity.

Apply `--comment` only after completion. Enter `address-review` only under the explicit combined
authorization described above; remediation remains a separate serial-write workflow and must return through
a fresh incremental watermark after any code change.

## Report

If a plan owns the work, completion of the whole pass is one material review transition; record only its
artifact and current gate. Report the frozen range, finding counts by severity or lens, canonical work-order
path, completed watermark, and whether an explicitly authorized remediation transition began. Do not replay
subordinate output or create a review-only commit.
