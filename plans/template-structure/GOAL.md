# Template ownership and uniform tj-agents package structure

Status: active; handoff accepted by native Codex session 01a12ccc-aaa2-7631-943f-7fe2947f05cd.
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

Scope: whole goal through all remaining implementation and terminal delivery.
Current slice: canonical installed package structure, shared check validation, and source-first CI against the taxonomy parent.
Remaining scope: compatible Template publication, consumer migration, and shared package checks for legacy/Core layouts.
Done when: all accepted capabilities are reviewed, validated, normally merged and released, with compatible consumer migration verified.

Finish the first structural slice through the L4 writer: reconcile the taxonomy parent while retaining main's later fixes, package canonical definitions with thin discovery entries, and validate complete structural input through check. Validate and independently review the child delta, publish its PR against the taxonomy parent, and land bottom-up once the parent owner lands PR #4. Continue the compatible Template publication and consumer migration slices below. Do not merge the child into the taxonomy feature branch.

## Pickup and investigation evidence

- 2026-10-11: successor session 01a12ccc-aaa2-7631-943f-7fe2947f05cd read the handoff, this goal, AGENTS.md and README.md in the owning checkout. No transfer receipt was supplied by the predecessor.
- Loaded canonical plan-execution, lanes, git-branching and handoff procedures. This repository has no installed Workflow v2 runtime; use the runtime-unavailable plan loop and this goal as the progress owner.
- Fetched origin; HEAD d2695e79102d0d6f65e2ee181a98994368e28736 is current with origin/main 28b5513. Git tree was clean at pickup.
- PR #4 remains OPEN at b085210d06e42c10d840cf7f969c7484b730f945, targeting main. It owns learning policy/convention taxonomy and its version 1.2.2 generator changes. Do not overwrite its checkout or publish a competing taxonomy migration.
- Phase: compatibility and structural investigation; lane L3 because the migration alternatives remain unresolved. Applied through bounded lane_l3 reader structure_design; no implementation writes delegated yet.
- Native gh access and Git fetch required sandbox escalation and succeeded. Continuation initialization/claim and scheduler capability are being resolved; no unattended continuation is claimed.

## Delivery map and resolved design

The structural mismatch is concrete: installed Kit packages contain full procedures directly in `skills/` and omit the canonical `.agents/` tree that Core packages carry. Also, check accepts a missing Codex manifest directory or an empty payload mapping. Baseline full suite passed 94 tests on Windows.

1. Structural package/check slice (active): canonical packaged definitions plus thin entries and resource siblings; generator structural validation in check; negative fixtures and isolated packaged utility execution. Expected 300–600 substantive lines in about 10 authored files. Release target 1.3.0 after parent version 1.2.2. Validate cumulative parent and child with full unittest and sync checks, both OS CI jobs, both real host acceptance and isolated package execution.
2. Compatible Template publication: expose a `template` plugin from the same canonical capability source while retaining `kit`, `kit-agents`, `tj-agents/kit`, `.agents/plugins/kit.json` and old workflow addresses. Generalize publication/source identity only after the first slice lands; test Kit-only and Template-only installations. No second authored capability tree or premature repository rename.
3. Compatible consumer migration: inventory actual remote pins, catalog and public references; update scoped consumers in isolated owned branches after released package acceptance. Retain the old facade until existing consumers and pins are verified.
4. Wider shared structural coverage: reconcile legacy consumers and Core's richer canonical/runtime source layout with those owners. Core currently has no kit.json, and Kit retires SOURCE_LAYOUT.md/sources.json that Core owns. Do not apply utility-only or stack-specific scaffold assumptions to Core's runtime packages.

The first slice depends on PR #4's taxonomy and overlaps its generator/check/version paths. PR #4 is still open and has a separate owner; immediate authorized execution must avoid an independent competing taxonomy patch. Therefore the current branch consumes verified parent b085210d06e42c10d840cf7f969c7484b730f945 as a stack child; PR base will be Refactor/KitTaxonomyVocabulary. Its merge into this checkout conflicts with main's subsequent release/continuation changes; L4 writer structure_implementation owns reconciliation and validation here only. No writes to the parent's checkout or branch are authorized by this dependency.

Implementation phase: L4, specified/testable package and checker changes applied through lane_l4 writer. Root retains architecture, review, authorization and delivery decisions. Do not commit generated host/plugin outputs in the child implementation; retain only generated material required by the parent merge until post-merge regeneration policy is reconciled.

## Continuation and gates

Continuation owner initialized at .agents/continuation/owner.json (owner 0a16a38d0f59197f91e5e355) and claimed by native Codex PID 500. Scheduler dry-run verified the Windows ScheduledTasks proposal. Actual registration was rejected by automatic approval review: development-goal authority did not explicitly authorize an unattended scheduler that could later push, merge and release. Tommy explicitly approved scheduled continuation in this native session after the proposal and rejection were explained. Registration succeeded: AgentStandards-Continuation-07e4ac93dbb9e48829b7a4da9f48fc2d143d4ea9d03bd07afa13c6b03b3f9a74. An observed supported wake returned working while the foreground lease was held, and launches remained zero. Maintain that lease while foreground/subordinate writes continue; checkpoint and yield before unattended continuation. No duplicate writer launched. Foreground work continues.

Taxonomy dependency: PR #4 owner resolves parent landing. Resume condition: parent merged normally with required review/checks and released version consequences reconciled; then retarget/reconcile this child's delta onto main, rerun affected checks and deliver normally. Child implementation/review/PR preparation can continue independently.

First-slice integration adds source-first CI generation and main-only committed regeneration, because the current workflow cannot validate a source-only PR or publish its regenerated packages. This is atomic with the packaging change, under the same 1.3.0 release; L4 writer generation_ci owns only the two workflow files and a separate CI-generation test file. Expected additional size under 150 substantive lines. The regeneration job must wait for validation, have scoped contents permission, and stage only generated roots. The existing 94-test baseline is green. PR #4's remote Windows/Linux/hosts checks passed on October 5, 2026; those checks do not establish compatibility with main's later commits or a current-head independent review.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in and .agents/kit/utility/check/scripts/check.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Installed skills load canonical shared procedures and retain sibling utility resources.",
      "source": ".agents/kit/utility",
      "mapping": ".claude/skills and plugins/kit/skills link to canonical .agents definitions; native manifest and marketplace stay supported.",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Full source suite, isolated package execution, and real claude native package acceptance in CI after generation."
      }
    },
    {
      "host": "codex",
      "behavior": "Installed skills load canonical shared procedures and retain sibling utility resources.",
      "source": ".agents/kit/utility",
      "mapping": ".codex/skills and plugins/kit/skills link to canonical .agents definitions; native manifest and marketplace stay supported.",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "Full source suite, isolated package execution, and real codex native package acceptance in CI after generation."
      }
    }
  ]
}
```

Remote consumer inventory on 2026-10-11: react, dotnet, rust, nvim and work all pin kit 1.2.1; cpp and marketplace have no kit.json. All seven repositories are active and default to main. This replaces stale local-pin observations; migration remains after compatible release.

## Compatible Template publication contract

Use payloads `{kit: [kit], template: [kit]}`: each published name selects exactly one existing canonical source, and every source retains its identity publication. Reject invalid/unknown names, aggregation, empty lists and missing identity publications. Keep repository/source discovery, type checks, local adapters and source tier files keyed by canonical source. Native manifests, marketplaces, package directories, package INDEX and selection.plugin use published names. Local adapters emit once; adding Template must not rename the existing check/new-plugin/update discovery entries.

Both publications ship canonical `.agents/kit` definitions and thin entries from that same authored tree. Procedures use bare package-local skill references and relative canonical links. Do not regex-rewrite prose or compatibility addresses. Source dependencies and compatibility alias declarations remain source-owned; project structured alias replacement targets into the publication namespace while retaining dates and profiles. No implicit dependency on the counterpart Kit/Template package is allowed. Source tier remains unchanged; Core's checker and gate separately represent published plugin and tier label (verified fixture: Template plugin, Kit tier, template@kit-agents identity).

Both native manifests preserve valid paired fields and repository URLs; Template display name is Template and Kit remains available. Both explicit harness manifests require their own kit-agents publication plus base-agents/base, resolve .agents/kit source roots, and declare no new hooks or permissions. Generator validates publication/source packaging facts; Core keeps the detailed harness and runtime interpretation owner.

Verification must include invalid mappings/manifest rosters/targets; one set of local adapters; matching canonical bytes and safe thin links; source-owned dependency/alias projections; unchanged tiers; self-contained Kit-only and Template-only new-plugin/check/update execution from temporary copied packages; Core tier checker acceptance; and separate isolated native installation of each public plugin. Installing every entry together cannot prove standalone compatibility.

After compatible publication releases, the aggregate marketplace adds Template from repository kit while retaining Kit. Its remote catalog currently advertises Kit at v1.2.0. Consumer pins migrate only after release acceptance. No settings objects, preference interpretation, Core catalog policy or machine-wide installation is added here.

## Wider shared package boundary contract

The shared check should follow native manifest skill roots (Core legitimately has distinct skills and codex-skills roots), validate inventories and identity pairs, require thin entries to resolve safe canonical .agents definitions with matching name/kind/domain, resolve required resources and harness source roots, and permit declared host-specific adapter extensions. Reuse one package validator from generation and filesystem checking. Starter-repository required skills/sections and retired layout assumptions stay an additional layer. A packages-only entry lets Core and legacy packages participate without pretending they have Kit's starter schema. Core continues to own lane resolution, hook integrity, workflows, catalogs, extended-adapter wording and runtime behavior.

## Pending structural observation

The runtime writes .agents/persistent-workflow-binding.json, but standard.json currently allows only its earlier runtime folder and delivery authorization file. The wider structural coverage slice must reconcile supported transient Core runtime artifacts with starter layout enforcement and vendored ignore rules. Resolution condition: a valid runtime binding can coexist with check, is excluded from delivery, and unknown source files remain rejected. This observation is within the existing shared structure outcome; no second repair writer is created.

## Stack measurement

Taxonomy parent b085210 predates main's later source-reference scanning, continuation/delivery allowances, scoped utility tiers and harness support. Reconciliation merge 8450ee9 retains those existing main changes. Against the parent, the reconciliation checkpoint spans 43 total files with 1097 added/92 removed lines, including repeated generated resources. These inherited main changes are part of cumulative validation and the child review; they are not new competing implementations. Re-measure authored vs generated totals after the first structural implementation and CI integration commit. Parent landing/rebase will remove the inherited-main difference before final merge eligibility.
