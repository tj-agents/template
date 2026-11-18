# Template layout progress

Plan: [Template layout](TEMPLATE_LAYOUT_PLAN.md).
Branch: `Refactor/SubjectSkillLayout`. Checkout: `C:/Users/TommySeery/source/repos/tj-agents/template`.
Base: `772a05cf83c58e160afd3bdb33f8ece545410d45`. Head: `9a8c457fc2a54be56ca8bc603d1b2e44ff60ff31`; initial candidate `8804758284a4f2e5754f5d137c4fd26199791d0a`.
PR: https://github.com/tj-agents/template/pull/56 (draft).

The source move, six kinds, native metadata projection, checker/scaffold and update preflight are
implemented. Generation/freshness passes for 202 files. Ruff format/lint and strict mypy pass;
Template conforms to its checker. Marketplace references resolve across 9 repositories and 192 shipped
skills. Copied-package creation, checking and update pass without producer access. The native skill
validator accepts the generated structure entry; the installed Claude Code and Codex CLIs accept both
published packages through isolated native validation on Windows.

The complete suite passed 301 tests and 27 subtests with one existing Windows symlink skip. Review
found two native YAML defects: whitespace before a key separator omitted required fields, and existing
four-space metadata mappings conflicted with generated two-space keys. Both are repaired together in
native_header. Six affected regression/copied-package/freshness cases pass after repair; eight generated
host YAML projections parse with required fields and nested metadata preserved. Ruff/mypy/freshness pass.
The plan host-coverage record uses the required installed verification level. Exact-head CI passed on
Windows and Linux, including pinned host acceptance and the system-Python packaged-library check.
CI run: https://github.com/tj-agents/template/actions/runs/40883476543. Native incremental review found no
actionable regression and independently passed all 136 generator tests with one existing skip. The canonical
private review receipt covers the fixing head; both original findings are resolved.

The candidate includes 63 authored/control/test/plan diff entries (1,348 insertions, 762 deletions at the
first staged measurement); remaining entries are vendored/generated copies. The plan records why source
discovery, scaffolding and checking must cut over together. The unrelated existing review file is excluded.

Next: prepare Core discovery/kind/standards-reader and dependent publisher candidates against exact
Template producer 9a8c457fc2a54be56ca8bc603d1b2e44ff60ff31 before producer landing. The global
cross-repository migration remains owned by this conversation.

Publication scope assessment: the runtime preflight found a current capitalised feature branch, no
uncommitted code, no base lag and no red generated-sync PR. No existing PR owns this branch. Its
assess-scope route is resolved by the already approved atomic Template slice in the implementation plan.
This direct user task has no roadmap item; this progress document is not a provider roadmap ledger.
The reviewed candidate needs remote Windows/Linux and pinned-host CI; publish it as a draft while the
coordinated Core/publisher cutover remains pending.

Current boundary: native directory retargeting to C:/Users/TommySeery/source/repos/tj-agents/core is
required before parent implementation continues there. The same conversation owns the global goal.
Template remains draft pending coordinated consumers; no merge or workspace rollout has occurred.

The exact-head CI watcher completed successfully in this foreground session. The delivery binding
was released at the native-directory capability boundary; no scheduler or auto-merge is armed.
Review descriptors/receipts remain in Git-private state; both disposable review worktrees/bundles were
verified and removed. Template conformance passes after removal of the transient delivery binding.
Core integration must reconcile the existing worktree-local persistent binding with Template control
entry validation: the supported binder creates a file the checker currently refuses while present.

Directory-transfer incident, 2026-10-29: the requested native `/cd` failed with
`Active background terminals block /cd.` Every recorded parent/fork terminal handle now returns
unknown process id; no task command remains in the verified frontend's process descendants. These
checks do not prove the native terminal inventory is empty. The shared-daemon terminal-list request
returns thread-not-found for this embedded conversation, so it cannot establish readiness. Native
`/stop` followed by `/ps` remains pending user input. Do not repeat the directory-change request until
that result is reconciled. The prepared [cleanup-prerequisite patch](cd-terminal-cleanup.patch) passes
`git apply --check`. Its required implementation and closure checks are recorded in the shared
[rollout plan](../../../docs/plans/repository-structure/REPOSITORY_STRUCTURE.md#required-directory-transfer-repair).
Core source application, delivery and installed-host verification remain pending. Tommy subsequently
directed structure work to resume first, without further manual directory-switch prerequisites. Defer
the background-terminal repair until afterwards and retain it across context recovery.
