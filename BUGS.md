# Bugs

## B001 — Required repository plugin configuration rejected

Kind: bug. Observed: 2026-10-16. Priority: P2. State: active.
Owner: tj-agents/template, Fix/RepositoryPluginConfiguration.
Evidence: a new utility scaffold plus mandatory machine:plugin-lock write/check succeeds,
then template:check rejects .agents/plugins.lock.json as outside the layout. Fresh scaffolds
also pin v1.6.0, which has not been published. CI workflow references retain renamed kit owner.
Impact: new standards-injected plugin repositories cannot pass the shared check and remote CI.
Cause: the closed layout allowlist predates portable consumer configuration; release publication lag.
Repair: accept named shared configuration owners while continuing to reject unknown JSON,
use canonical template repository identity for CI, and publish the validated Template release.
Resolution condition: injected fresh repository passes conformance and reusable CI resolves.
Verification: pending source tests and Windows/Linux CI; no installed acceptance claimed.
Next action: validate focused regression and review this bounded prerequisite release.
