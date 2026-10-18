# Personal-project standards

Status: active; Template profile support is the first delivery slice.
Owner: Codex session 01a14fcb-9d5d-7530-9fc7-8d3452d4760a acknowledged the handoff on 2026-10-18 and owns this workstream. The originating session retains the Concertable CLI launch repair and owns no Template or personal implementation writes after handoff.
Checkout: C:/Users/tommy/source/repos/tj-agents/template/.worktrees/Feature-PersonalProfile
Branch: Feature/PersonalProfile
Initial base: 50b7e59 (fetched Template origin/main).
PR: not opened
Lane: L3 for the bounded open design and wording investigation; route specified implementation and review at the appropriate lower lane once decided.

## Authorization and original context

Tommy explicitly requested a separate personal-project standards repository, then requested an actual handoff to implement it and to include the initial context. His latest requirement is that the principle below be a MUST HAVE RULE for ALL personal projects. He authorizes investigating the best wording and handling rather than merely copying his phrasing. This is execution authority, not a prompt-only request or a request to keep the proposal deferred.

The trigger was a broken `codex` launch from Concertable: a current terminal bootstrap could not find an authenticated machine coordinator because installed configuration still selected an obsolete marketplace/repository identity. The source and installed configuration had diverged despite a migration having been considered completed earlier. Core PR https://github.com/tj-agents/core/pull/299 merged the canonical coordinator, made Codex plugin repair possible without a coordinator, and retired a separate PowerShell no-daemon wrapper/installer in favor of the shared portable launcher. Windows/Linux CI passed and core package registries were migrated. However a fresh actual session still failed: `selected package dotnet is missing from the current publisher catalog`. Old stack selections remained under a publisher whose catalog had changed. The predecessor had verified CLI version commands, which bypassed the real session refresh path, so that evidence was insufficient. The originating session is now repairing the remaining publisher bindings and will verify a real session. Do not duplicate that repair.

Tommy is frustrated by compatibility scaffolding and extra engineering constraints that create maintenance work without serving a real user. These personal projects currently have no live users beyond him and a few collaborating developers whose upgrades can be coordinated. Do not invent hypothetical external consumers to justify retaining obsolete behavior.

## Required outcome

Create a reusable `personal` standards plugin/repository, expected owner/name `tj-agents/personal`, and make its requirements mandatory and reliably loaded in all personal projects. It must be an actual selected project policy with verified adoption, not optional advice that an agent may miss.

The firm rule is to keep one current supported solution: remove obsolete names, aliases, fallback implementations, adapters, old configuration formats, and compatibility branches when replacing them. Coordinate and migrate known callers, project declarations, installed registrations, generated artifacts, and live runtime entry points in the same cutover. A changed source tree, successful generation, passing unit tests or `--version` alone does not establish that a migration is complete. Verify the behavior that users actually invoke, including supported Windows/Linux launch paths. An agent must not independently add a backwards-compatibility exception; an explicit contrary user requirement must be surfaced as a deliberate policy decision rather than a hidden fallback.

Investigate concise, unambiguous wording and the correct loading/enforcement mechanism. Consider checks that can catch retired active bindings being reintroduced. Define personal-project scope from explicit adoption/ownership, and keep employer repositories outside it. Known intended personal scope includes Tommy's tj-agents repositories and his Concertable project; inventory real project selections and preserve unrelated work. Do not assume every directory in his user profile is personal.

Investigate other useful personal defaults with the same concrete-benefit criterion: avoid speculative abstractions, dependencies, configuration switches, duplicate implementation paths and process machinery. Use proportionate verification. Assess whether any Core rules are personal preferences rather than shared mechanisms (automatic session closing and default commit/planning/review cadence were examples for assessment, not pre-decided wholesale deletions). Move genuinely personal-only policy to its proper owner while keeping a single authored definition. Keep generic capability mechanisms in Core. Do not turn this task into another large checklist or layer of overhead.

## Template is mandatory

Use `tj-agents/template` to scaffold the personal repository. Do not hand-build a plugin skeleton or copy a repository layout around Template.

Assessment already performed: fetched Template main at 50b7e59 supports only stack, tool and utility repository types. `.agents/template/utility/check/standard.json` limits utility repositories to utility skills, so a policy/profile repository does not currently fit. Extend Template with an appropriate supported policy/profile repository type (choose the clearest design after inspecting its generator/checker), test that capability and deliver it as a focused first slice. Then scaffold personal through that supported Template command. Reuse Template generation, validation, root files and CI. Do not add backwards compatibility shims for this new type.

The source is under `.agents/template/utility/new-plugin/` and `.agents/template/utility/check/`. Read the current checkout's AGENTS.md and README.md; the primary local Template checkout was stale, so use this fresh isolated checkout. No other writer owns this branch. Source generation conventions differ from Core; follow Template's own rules.

## Completion and delivery

Own the authorized work through implementation, review, checks, the repository's permitted PR/merge delivery, marketplace integration, and real adoption/host verification. Keep one maintained goal, and record the independent delivery slices and actual repository/branch/PR locations as execution moves. Do not accumulate speculative parallel PRs. Install/project-selection changes needed for this user-authorized personal policy are in scope; preserve employer scope and unrelated settings. Use the current approved publishers and no legacy aliases.

Before writing governed code in a newly created repository, apply its owning plugin selection and pass the shipped selection check. No second agent is authorized to write this workstream. Do not adopt or close the predecessor's Concertable launch-repair goal.

## Next Steps

1. Acknowledge ownership in this goal, inspect current Template source and available standards, and investigate the best policy/profile type and mandatory delivery mechanism. Do not repeat the already-complete broad assessment of whether a separate personal profile is useful.
2. Record the chosen concise policy wording, applicability/enforcement approach, acceptance evidence, and delivery slices here. The user delegated these bounded wording/design choices; do not stop at a proposal when authorized implementation can proceed.
3. Implement and deliver Template's policy/profile support with meaningful generator/checker/scaffold coverage. Then scaffold `tj-agents/personal` through Template, author the required policy, integrate its canonical marketplace selection and verify real loading/adoption in covered personal projects.
4. Assess Core personal-only candidates against evidence and avoid copying instruction bodies or adding generic requirements with no concrete benefit. Report the delivered policy, adoption coverage, tests and any genuine unresolved gate honestly.

## Decisions and progress — 2026-10-18

- Pickup verified by reading the handoff and this goal; native session claimed `personal-projects/standards` in the session store. No second writer is authorized. The checkout is clean at the recorded base and has no commits missing from fetched `origin/main`.
- Use the repository type `profile`: it describes a reusable selection of project policies, distinct from a teaching stack or an executable utility. It must contain a policy, may contain supporting conventions/workflows/utilities, and always applies after explicit selection. There is no directory-name or home-directory heuristic. Profiles inherit only the canonical `tj-agents/base` capability dependency.
- Required policy wording: "Keep one current supported solution. When replacing behavior, remove the superseded names, aliases, fallbacks, adapters, configuration formats and branches. Migrate all known callers, project declarations, installed registrations, generated artifacts and live entry points in the same cutover. Verify the entry points people actually use on supported platforms; source edits, generation, unit tests and version commands alone do not prove completion. Do not add a compatibility exception independently. Surface an explicit contrary user requirement as a deliberate policy decision."
- Mandatory loading will reuse Core's shipped harness requirements and host instruction delivery, with one authored policy body. Source inspection confirms Core already delivers policy bodies with source hashes and provides `--instruction-fragment` support. Detailed adopter/host coverage remains to verify; discovery and `always` applicability alone are not acceptance evidence.
- The bounded design choices are explicitly delegated in this goal despite no `.agents/settings.json` default delegation. Investigation is L3; specified implementation is L4, with the current owner retained because no in-session capability switch is available. No model switch or subordinate dispatch is claimed.

## Delivery slices and acceptance

1. **Template profile support** — current branch `Feature/PersonalProfile`, base `50b7e59`, no PR yet. Add generator type, policy skeleton, standard/checker rules, dependency projection, focused tests and documentation; expected under 400 substantive lines plus generated adapters/payloads. Keep vendored generator byte-identical to its source. Acceptance: profile scaffold/check round trip; missing policy, invalid kind/detection/name and dependency drift failures; required full tests and generation check; reviewed candidate and Template CI before merge.
2. **Personal plugin and marketplace** — only after slice 1 lands. Scaffold `tj-agents/personal` through Template's supported command, select owning standards before governed implementation, author the concise policy and its mandatory host transport, publish through the canonical marketplace. Acceptance: fresh scaffold, Template checks, host instruction evidence, marketplace selection and payload checks. Record exact repositories, branches and PRs when created.
3. **Explicit adoption and policy ownership** — inventory known tj-agents and Concertable selections; preserve employer scope and unrelated work. Add personal selection with committed declarations and drift checks, verify actual supported host entry points, and assess Core-only candidates from evidence. Keep generic mechanisms in Core and one authored policy definition. Record coverage and unresolved platform evidence here.

Current tooling: default shell runner fails during helper setup; the approved escalated runner works. Read-only Node access and process execution work within the sandbox, but Git metadata writes and session-store access require the approved runner. GitHub authentication is available through that runner. These are host permission constraints, not evidence of a source defect in this workstream.
