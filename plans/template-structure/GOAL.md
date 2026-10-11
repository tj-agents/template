# Template ownership and uniform tj-agents package structure

Status: prepared for one Codex handoff; pickup not yet verified.
Date: 2026-10-11
Branch: Refactor/TemplateStructureContract
Worktree: C:/Users/TommySeery/source/repos/tj-agents/kit/.worktrees/Refactor-TemplateStructureContract
Base: origin/main at 28b5513
Originating session: 01a12c10-0de6-7152-a9f2-9e5f374021f8
Lane: L3 for bounded naming/compatibility and structure reconciliation; re-route specified implementation to L4 and delivery to its appropriate lane.

## Outcome and authorization

Tommy explicitly requested this as the second of two handoffs: Kit supplies templates for all tj-agents packages, enforcing the same structure so those packages compose with Core. He proposed calling Kit template to make its purpose clear and said this needs fixing too. Deliver the naming and shared structure correction with meaningful verification, independent review, PR, normal merge under applicable recorded authority, required release/tag/publication consequences, and compatible consumer reference migration within this goal's scope.

Kit/template has NOTHING to do with the repository configuration object. Core owns configuration interpretation and the settings interface; do not add a settings/configuration scaffold feature, auto-merge preference interpreter or duplicated policy to this workstream. Its task is templates, common structure and structural enforcement across tj-agents packages.

Kit already owns new-plugin repository templates, check/update standards, vendored generator/root files and reusable plugin CI. Preserve that single ownership and improve the real remaining inconsistencies. Make template the clear public concept/name; assess the repository/plugin/skill naming surface and provide a compatible migration rather than a label-only README change. Reconcile actual consuming references and pins before a cutover. A rename must retain a working migration path for existing kit references, workflows and consumers; do not break published addresses by renaming first and hoping to fix callers later. Escalate genuinely missing external authority only after the concrete migration is reviewable.

## Ownership and source context

Read this checkout's AGENTS.md and README.md before edits. Canonical sources live in .agents/kit until a deliberate compatible source/naming migration is delivered. Templates are under .agents/kit/utility/new-plugin/templates/repository; check/update and standard.json own shared layout. Authored templates are canonical. Preserve byte equality of vendored copies and template tests. Generated plugins and host outputs remain uncommitted; existing release instructions require KIT_VERSION, plugin/manifest versions and a tag after merge.

Open Kit PR #4, branch Refactor/KitTaxonomyVocabulary at b085210, already owns taxonomy changes. Its checkout is C:/Users/TommySeery/source/repos/tj-agents/kit/.worktrees/Refactor-KitTaxonomyVocabulary. Do not adopt or overwrite it. Coordinate or depend on that owner when structure or naming intersects. Fix-ContinuationSourceScan is another separate owner. Start from this goal's fetched main; preserve every other's changes.

The independent Core correction is C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-RepositorySettingsContract/plans/repository-settings/GOAL.md. It is context only, not this writer's scope. Shared design documents in tj-agents/docs belong to the existing coordinator; do not edit its live checkout.

## Acceptance

- Template purpose, package/repository vocabulary and skill naming have one clear owner, with a verified compatibility path for any actual rename.
- New/check/update share one structural standard for tj-agents package types, and all package capabilities still compose with Core.
- Meaningful checks catch inconsistent package structure rather than only testing a rename string.
- Existing Core canonical layout and thin Claude/Codex adapters are respected. No duplicate runtime policy is added to package templates.
- Both host packages and supported Windows/Linux execution are verified to the appropriate source and native acceptance levels; source tests are not reported as installed-host proof.
- The independent taxonomy owner is coordinated and no competing writer alters its owned files.
- Changes are reviewed, green and normally merged; required Kit release/tag and consumer pin consequences are completed or truthfully gated with exact ownership.
- No repository configuration object or auto-merge interpretation is added to Kit/template.

## Next Steps

Acknowledge this handoff with the exact native session identity. Load plan-execution, lanes and the repository's source conventions. Inspect current template/check/update and consuming pins, reconcile PR #4, and record a bounded compatible template naming/structure migration in this same goal. Then implement the authorized correction in reviewable slices, run meaningful checks, independently review, deliver the PR through normal CI/merge, and complete required release/publication and scoped compatible reference migration. Keep the canonical goal current and record concrete gates rather than stopping after a proposal.
