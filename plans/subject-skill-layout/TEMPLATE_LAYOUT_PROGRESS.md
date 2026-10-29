# Template layout progress

Plan: [Template layout](TEMPLATE_LAYOUT_PLAN.md).
Branch: `Refactor/SubjectSkillLayout`. Checkout: `C:/Users/TommySeery/source/repos/tj-agents/template`.
Base: `772a05cf83c58e160afd3bdb33f8ece545410d45`. Head: this implementation checkpoint.
PR: not opened.

The source move, six kinds, native metadata projection, checker/scaffold and update preflight are
implemented. Generation/freshness passes for 202 files. Ruff format/lint and strict mypy pass;
Template conforms to its checker. Marketplace references resolve across 9 repositories and 192 shipped
skills. Copied-package creation, checking and update pass without producer access. The native skill
validator accepts the generated structure entry; the installed Claude Code and Codex CLIs accept both
published packages through isolated native validation on Windows.

Focused verification covers 163 integration cases plus 22 subtests. Generator verification covers 131
passing cases and one existing Windows symlink skip, with its two subsequently corrected fixture/freshness
cases passing separately. A final complete pytest run is in progress. Linux and pinned CI host acceptance
remain outstanding; local validation does not establish their result.

The candidate includes 63 authored/control/test/plan diff entries (1,348 insertions, 762 deletions at the
first staged measurement); remaining entries are vendored/generated copies. The plan records why source
discovery, scaffolding and checking must cut over together. The unrelated existing review file is excluded.

Next: freeze the committed candidate, complete native and applicable specialist review, reconcile the
complete test result, and prepare dependent consumer candidates before producer landing. The global
cross-repository migration remains owned by this conversation.
