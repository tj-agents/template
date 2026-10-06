# Kit source scanner must tolerate continuation runtime state

## Authorization and ownership

Bounded standards-defect side workstream authorized by engineering:session-guidance. Own only this isolated kit checkout on `Fix/ContinuationSourceScan`. Implement, validate, independently review, open a plain GitHub PR and merge once kit gates pass. Do not install or update consumers, edit dotnet, publish to another scope, or make destructive changes. Repository tagging/release publication remains subject to its existing authorization gate.

The originating session retains `C:/Users/TommySeery/.claude/plans/tj-agents/DOTNET_VALUES_STRUCT_BIAS_PLAN.md` and both dotnet slice PRs; do not adopt or rewrite that goal. This side goal is the only owner of the scanner/runtime compatibility defect.

## Evidence and acceptance

In dotnet using vendored kit 1.1.0, engineering:persistent-workflow initializes its documented canonical owner at `.agents/continuation/owner.json` and creates events/lock/scheduler files there. `pwsh .agents/sync-generated.ps1` then fails before generation with `error: .agents/continuation/events.jsonl: only kind folders belong in a plugin folder`.

The vendored generator declares `RESERVED_AGENT_DIRS = {"plugins", "tiers", "tests", "hooks"}` and interprets continuation as a plugin. Kit owns the source at `.agents/kit/utility/new-plugin/templates/repository/sync_generated.py` (resolve exact template path from repository); generator copies are vendored and must remain identical. Dotnet's own generator is deliberately unchanged. Its foreground owner archived only local runtime state and continues normal generation, tests, review and CI.

Acceptance: supported local continuation state is excluded from authored-plugin discovery and packaged content; malformed authored plugin directories are still rejected. Add meaningful regression coverage through the normal generator entry point. Keep the single template source and mirrors synchronized; run kit required conformance/generated-file/tests and exact-head PR CI. Account for kit release/version conventions without silently installing into consumers or bypassing a release gate. Record PR and observed final outcome here.

## Next Steps

1. Read kit AGENTS.md and this checkout's clean Git identity; acknowledge pickup in this goal before source edits.
2. Diagnose reserved metadata directory discovery and implement the smallest correct source-owner fix with regression tests and required manifest/version updates. Implementation/review lane L4: a specified scanner fix testable through the CLI.
3. Generate, validate, independently review, open and merge the scoped kit PR when gates pass; record any genuine release-publication gate and exact next action. Do not invoke another continuation in the source tree until this defect is resolved.

## Handoff

One successor launch is being submitted by the originating session. No duplicate launch or source writer is authorized. Record pickup and first action here.
## Pickup and progress

- Successor acknowledged pickup on 2026-10-06 in the exact authorized worktree and branch. Git has only the two supplied untracked handoff artifacts; origin is https://github.com/tj-agents/kit.git.
- Owning lifecycle: engineering:plan-execution; implementation and independent review: L4 through bounded lane workers. No continuation runtime will be initialized in this checkout.
- Delivery slice: reserve continuation runtime metadata during source discovery, CLI regression tests, synchronized generator mirrors and required patch release metadata. First action: inspect scanner and test fixtures, then implement this slice.


- Implementation complete: reserve continuation in scanner and conformance layout, exercise runtime owner/events/locks/scheduler through generator CLI, retain malformed authored-plugin rejection, add conformance CLI regression, synchronize templates/mirrors/generated payloads and patch metadata to 1.1.1.
- Validation observed: generation produced 104 files; generated -Check passed; all 66 unittest tests passed; kit conformance passed for 1.1.1; git diff --check clean.
- Measured candidate before plan: 15 files, 60 insertions/21 deletions; authored behavior/tests/version owner changes are 48 insertions/9 deletions across 7 paths, remaining mirrors/generated payloads 12/12 across 8 paths. Single scoped slice, no split required. Next: commit, synchronize/freeze independently reviewed candidate, then exact-head PR CI and authorized merge.
- Release tag/publication and worktree deletion remain outside the handoff's authorization; retain this checkout and record release next action after merge.

