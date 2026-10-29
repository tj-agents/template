# Template layout progress

Plan: [Template layout](TEMPLATE_LAYOUT_PLAN.md).
Branch: `Refactor/SubjectSkillLayout`. Checkout: `C:/Users/TommySeery/source/repos/tj-agents/template`.
Base: `772a05cf83c58e160afd3bdb33f8ece545410d45`. Head: this metadata repair checkpoint; initial candidate `8804758284a4f2e5754f5d137c4fd26199791d0a`.
PR: not opened.

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
The plan host-coverage record now uses the required installed verification level. Linux and pinned CI
host acceptance remain outstanding.

The candidate includes 63 authored/control/test/plan diff entries (1,348 insertions, 762 deletions at the
first staged measurement); remaining entries are vendored/generated copies. The plan records why source
discovery, scaffolding and checking must cut over together. The unrelated existing review file is excluded.

Next: complete the incremental review of both YAML fixes, publish the stable producer candidate for CI,
and prepare dependent consumer candidates before producer landing. The global
cross-repository migration remains owned by this conversation.
