# Code review — Refactor/TemplateStructureContract

> **This file is a work order, not a discussion.** Fix open findings directly and record each disposition.

**Review status:** `complete`
**Reviewed up to commit:** `88c2c25fc763539a230561ed57b2c701e261e2f1`  `(2026-10-11)`
**Security-reviewed up to commit:** `88c2c25fc763539a230561ed57b2c701e261e2f1`
**Judgment:** `approved`

## Review pass — 2026-10-11 — full

**Candidate base:** `b085210d06e42c10d840cf7f969c7484b730f945`
**Candidate head:** `a7a85858c28a5dcfff45faab4a1c458627839573`
**Candidate branch:** `Refactor/TemplateStructureContract`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:4c60bd12ff968b0c32420915af7a544c87e74be0243ff67609db5af9f78f6e78` `(46 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\H3dqmQqgDdSL1X9Qc9MaIj\ORDIpGHVvh6hAsvbsj6ew4\YgQMcMJhiQ3fyHJZxenb3W`
**Candidate bundle identity:** `sha256:9342ff70f22e32841b1eafaffcc504c41ce588aea3e54eab4a3cceb7a3f2d8d1`
**Work-order path:** `reviews/Refactor-TemplateStructureContract.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`
**Binary patch:** `sha256:31bf651dfa2f84536d21ecb54b1215ba634c1565f82d6be9511b861fc82186f6`
**Descriptor:** `C:\Users\TommySeery\source\repos\tj-agents\kit\.git\agent-workflow\runs\template-structure\review\62040c70c261890ddfc87259c5e9dbdd670f8daaf6d77dff0fd247d981d530ae\descriptor.json`
**Descriptor identity:** `6fe688c8246c50041ca77d111a4bbaca0736ff9c9b78edd595abbb30c688c8ce`
**Synchronization:** `{"base": "b085210d06e42c10d840cf7f969c7484b730f945", "base_ref": "origin/Refactor/KitTaxonomyVocabulary", "behind": 0, "head_after": "a7a85858c28a5dcfff45faab4a1c458627839573", "head_before": "a7a85858c28a5dcfff45faab4a1c458627839573"}`
**Routed technical rules:** none; repository has no route table and no applicable installed stack tier.
**Selected lenses:** native-general, workflow, security.

### Findings

- [x] **TS-1 — HIGH — native-general/workflow** — `.github/workflows/plugin-ci.yml:48`
  Unconditional generation before `-Check` lets non-Kit callers validate repaired temporary outputs while merging stale published packages; only Kit currently has a main publication job. Make pre-verification generation an explicit default-false reusable-workflow input, opt Kit in, and leave both hosts’ freshness checks unconditional.
  Confidence: high. Acceptance: ordinary callers retain a failing freshness gate for stale committed artifacts; Kit’s source-only PRs still regenerate before acceptance.
  Fix: 88c2c25fc763539a230561ed57b2c701e261e2f1 adds the explicit default-false input, gates generation in both reusable jobs, and opts Kit in. Four focused tests and git diff --check passed; incremental review follows.

Native Codex review ran against the frozen base in a detached frozen-head checkout (exit 0). Its request to commit generated Kit output was discarded because the recorded goal explicitly keeps generated output uncommitted and requires verified main publication before release. The reusable-caller finding above is retained.

The configured workflow review role failed to launch because its fixed model is unsupported by this ChatGPT account; the bounded check returned to the parent. The native layer independently identified the retained workflow defect. Security dispatch ts-full-a7a8585-security completed under the existing packaged review-lens contract in L2 with matching immutable identities and no candidate findings; its evidence covers event/SHA guards, permissions, generated staging and non-forced publication.

## Agent host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "candidate_head": "88c2c25fc763539a230561ed57b2c701e261e2f1",
  "shared_source": ".agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in and .agents/kit/utility/check/scripts/check.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Thin discovery entries resolve canonical procedures and copied resource siblings support repository creation, drift checking and repair.",
      "source": ".agents/kit/utility",
      "mapping": ".claude/skills and plugins/kit/skills link to canonical .agents definitions; native manifest/marketplace acceptance remains supported.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Full source suite and generated freshness passed in exact-head CI run 38182114392 on Windows and Linux; native package acceptance passed with pinned Claude 2.1.282 and Codex 0.159.2. Four focused CI-generation tests also passed locally and independently against the frozen tree. Prior isolated copied package create/check/drift/update and canonical check passed. This source record does not claim an installed agent executed the procedure."
      }
    },
    {
      "host": "codex",
      "behavior": "Thin discovery entries resolve canonical procedures and copied resource siblings support repository creation, drift checking and repair.",
      "source": ".agents/kit/utility",
      "mapping": ".codex/skills and plugins/kit/skills link to canonical .agents definitions; native manifest/marketplace acceptance remains supported.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Full source suite and generated freshness passed in exact-head CI run 38182114392 on Windows and Linux; native package acceptance passed with pinned Claude 2.1.282 and Codex 0.159.2. Four focused CI-generation tests also passed locally and independently against the frozen tree. Prior isolated copied package create/check/drift/update and canonical check passed. This source record does not claim an installed agent executed the procedure."
      }
    }
  ]
}
```

## Review pass — 2026-10-11 — incremental

**Candidate base:** `a7a85858c28a5dcfff45faab4a1c458627839573`
**Candidate head:** `88c2c25fc763539a230561ed57b2c701e261e2f1`
**Candidate branch:** `Refactor/TemplateStructureContract`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:075d9278025d3f3bc8fb3956dbe0578bc2ecd13d5101823026a545a79ae20c58` `(4 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\H3dqmQqgDdSL1X9Qc9MaIj\ORDIpGHVvh6hAsvbsj6ew4\gtp2OiPFOjzFe1_W6_VRhl`
**Candidate bundle identity:** `sha256:446acc4a2939bcd9fb2f2eee0da7959fa95e18f0ec1c7fec48787e042caf9038`
**Work-order path:** `reviews/Refactor-TemplateStructureContract.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`
**Binary patch:** `sha256:6c195279c84d76e708f728115985a95b3a06505646f06b015bb18980707f7d90`
**Descriptor:** `C:/Users/TommySeery/source/repos/tj-agents/kit/.git/agent-workflow/runs/template-structure/review/82da763a23c53a3cc57b5fd6ebf551865449ef6cd99034cfe3675727481f3f27/descriptor.json`
**Descriptor identity:** `ba729b79299795af5df869d3130d6209ec18b7d3666c4176b0d95f79fa08e321`
**Synchronization:** none; remediation delta follows the completed full pass.
**Routed technical rules:** none.
**Selected lenses:** native-general, workflow, security.

### Findings

No new candidate findings were returned by the native reviewer or fresh workflow/security lenses. Parent validated all immutable identities and changed-line evidence, retained no new findings, and approved the four-path delta. The moving host-coverage check passed against the exact descriptor.

Native Codex review ran in the detached frozen-head checkout against a7a85858c28a5dcfff45faab4a1c458627839573 and exited 0. It confirmed the reusable default and unconditional freshness gates; focused tests passed. Its attempted broad fixture tests could not create temporary directories in the read-only sandbox, and freshness predictably failed on the intentionally source-only exported commit. Those attempts are not validation evidence; exact-head remote generation and source tests passed. Security dispatch ts-incremental-88c2c25-security matched all identities and found no defects. Workflow dispatch ts-incremental-88c2c25-workflow confirmed ordinary generated consumers omit the opt-in and all four frozen workflow tests passed; its formal identity addendum matched the descriptor. The prior pass identity, original TS-1 text/severity and completed changes-requested judgment remain intact.
