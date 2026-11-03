# Template subject layout implementation

Authorised by Tommy on 2026-10-29 in the repository-structure conversation. The agreed cross-repository
design lives in [Docs](../../../docs/plans/repository-structure/REPOSITORY_STRUCTURE.md). This plan owns
only Template's producing implementation and its integration evidence; it does not replace that design.

## Outcome and consumption contract

Publish canonical skills at `.agents/<namespace>/skills/<subject>/SKILL.md`; derive public names by
flattening the subject path and read kind independently from metadata. Permit exactly policy, standard,
operation, workflow, learning and reference. A kind change preserves paths and public identities.

Template's generator, checker, scaffold, update, documentation and generated entries must agree. Stack
and tool starters keep teaching in a learning skill and proficiency/goals in a declared plain resource,
`learning/knowledge.md`; direction is a reference skill. Generic plugin creation requires explicit
`--skill-kind`. Profile retains its required policy while accepting every valid kind for other skills.

Native entries project custom fields into `metadata.tj-agents-*` while retaining extended canonical
source. Claude-only native fields cause a separate Codex projection when required. Shared resources
ship only through explicit mappings. A consumer using the new generator must use the new source layout;
there is no old-kind layout parser or alias for the former utility preset.

```text
Source: .agents/template/skills/structure/SKILL.md, kind: standard
Public: template:structure
Native: name: structure; metadata.tj-agents-kind: standard
Reclassify: edit kind; source path and public name remain unchanged
```

The generator's existing function boundary implements discovery as
`load_skill(root, plugin, directory, name, namespace)`: kind is obtained from the parsed source metadata.
`new_plugin.plan` emits explicit learner-data resource mappings. `update` validates the current type and
source discovery before replacing vendored files, so a retired-layout consumer remains intact on refusal.

## Delivery slice

Branch: `Refactor/SubjectSkillLayout` in the normal Template checkout. Base:
`772a05cf83c58e160afd3bdb33f8ece545410d45` (`origin/main` fetched 2026-10-29). PR: not opened.

Scope: generator template and its vendored root, checker/standard, scaffold/update, source moves,
native projections, directly affected tests, workflow command paths and owning documentation.
No package versions or tags are needed. No other open Template PR is modified.

The source move, strict discovery, checker and scaffold changes are one atomic format cutover. Splitting
them would produce a generator that cannot discover its own source or scaffolds that fail their checker.
Separating tests from behavior or introducing a permanent dual-layout parser was rejected. Generated
copies are measured separately from authored changes; path-only moves are recognised by Git. Native
metadata is qualified in the same consumer-facing candidate so both host projections have a concrete
format for the new kinds. Keep this scope frozen rather than add unrelated generator work.

Existing publisher workflows resolve Template from main. Before landing a breaking producer, reconcile
their source migrations and workflow paths against this exact candidate, together with Core's discovery
and standards-reader changes. Cross-repository candidate references must be recorded in the global
design. Passing Template's own checks is not evidence that those consumers or installed hosts migrated.

## Verification and applicable standards

Python scripts/tests: python:build, python:style, python:testing and existing script-repository layout.
Skill definitions: native skill-creator through skill:new/update and skill:check. Workflow changes:
github-actions:build. Instructions: base:agent-files; shared behavior: engineering:docs. User's zero-comment
rule applies to all code. Worker leases are disjoint and reconciled before directory moves.

Run generation/freshness, ruff format/check, mypy and affected pytest suites. Exercise copied installed
package creation, checking and update with the producer checkout unavailable. Validate generated native
headers with the installed native validator, then run real Claude/Codex package acceptance. CI supplies
Windows/Linux and pinned-host execution. A failed or absent installed check remains incomplete.

## Execution readiness

Authority: Tommy's explicit request to reorganise the repos and subsequent "ok lets go?". The host reports
the normal Template checkout after native `/cd`. Source and standards are identified above. No new
dependency, generic runtime layer, cross-repository import lookup or compatibility alias is authorised.
Stop publication on a failing required check, conflicting repair owner, or unmet producer/consumer
cutover. Continue independent local implementation and diagnostics within this same goal.

Execution uses specified implementation with the parent retaining architecture, acceptance and diagnosis.
The source implementation is ready for validation; this is not a verdict that the global rollout is ready
to land. Exact next action: finish integration tests, commit the coherent candidate, freeze its review,
resolve findings, then prepare dependent consumer candidates before producer landing.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/template/skills/structure/SKILL.md",
  "hosts": [
    {
      "host": "claude",
      "behavior": "discovers stable public skills from the new subject layout",
      "source": ".agents/template/skills/new/plugin/templates/repository/.agents/sync_generated.py.in",
      "mapping": "canonical source to .claude/skills and plugins/template/skills",
      "verification": {"level": "installed", "result": "passed", "evidence": "python -B .github/scripts/validate_hosts.py --root .; installed Claude native strict validation on Windows; Linux CI pending"}
    },
    {
      "host": "codex",
      "behavior": "discovers stable public skills with supported native metadata",
      "source": ".agents/template/skills/new/plugin/templates/repository/.agents/sync_generated.py.in",
      "mapping": "canonical source to .codex/skills and the declared Codex package skill root",
      "verification": {"level": "installed", "result": "passed", "evidence": "native quick_validate.py plus validate_hosts.py isolated marketplace add, package add and enabled listing on Windows; Linux CI pending"}
    }
  ]
}
```
