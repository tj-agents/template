# Bugs

## B001 — Required repository plugin configuration rejected

Kind: bug. Observed: 2026-10-16. Priority: P2. State: resolved.
Owner: tj-agents/template checker. Initial repair: Fix/RepositoryPluginConfiguration.
Evidence: a new utility scaffold plus mandatory machine:plugin-lock write/check succeeds,
then template:check rejects .agents/plugins.lock.json as outside the layout. Fresh scaffolds
also pin v1.6.0, which has not been published. CI workflow references retain renamed kit owner.
Impact: new standards-injected plugin repositories cannot pass the shared check and remote CI.
Cause: the closed layout allowlist predates portable consumer configuration; release publication lag.
Repair: accept named shared configuration owners while continuing to reject unknown JSON,
use canonical template repository identity for CI, and publish the validated Template release.
Resolution condition: injected fresh repository passes conformance and reusable CI resolves.
Initial verification: pending source tests and Windows/Linux CI; no installed acceptance claimed.
Initial next action: validate focused regression and review this bounded prerequisite release.

Update — 2026-10-19: the same closed layout allowlist also rejected Core's ignored
`.agents/persistent-workflow-binding.json` while a valid repository owned PR delivery.
Cause confirmed: this known runtime file was absent from `agents_files`; unknown-file rejection
was otherwise correct. Priority P2 because the defect interrupted local conformance during delivery.
Repair link: https://github.com/tj-agents/template/pull/24, merged at
`eab0c1f65eb9e6597bf6340a217d8f0bb48352d0`. The exact filename is now allowed and regression-covered.
Resolution condition: portable configuration including the runtime binding passes the checker,
unknown files remain rejected, generated standard copies are current, Windows/Linux CI is green.
Verification: locked uv format/lint/mypy passed; pytest 171 tests and 22 subtests passed;
legacy unittest 13 tests passed; generation freshness 161 files passed. PR CI 39175174170
and merged-main CI 39175371157 passed. The personal repository's setup also passed current
Template conformance and Windows/Linux CI before merging PR2.
Next action: none for this repaired layout defect. Installed CLI authentication and refresh
acceptance remain separately owned by the personal-project goal and launch-repair owner.
