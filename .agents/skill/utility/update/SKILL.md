---
name: update
description: Update, rename, split or consolidate an existing skill through the current host's native skill creator, migrating its callers and removing superseded identities. Use when changing an existing skill or correcting its guidance; new skills use skill:new.
kind: utility
domain: template
profile: core
applicability: existing skill authoring in selected repositories
requires: native skill creator
provenance: house
---

# Update a skill

Owns an existing skill change from its authored source through a complete current-name cutover. Preserve
the user's requested behavior, existing authorization and the concern's source owner.

```text
Request: consolidate continuation under workflow:continue.
Find: two old public skills, host adapters, callers and a registered scheduler entry.
Update: retain workflow:continue, move its supporting contracts and transport to resources,
        migrate callers and the exact registration, and delete both old discovery entries.
Verify: fresh Claude/Codex discovery exposes only workflow:continue; the retired-name search has no
        active matches and the existing continuation behavior still works.
```

Resolve the existing canonical definition, both host entries, its source repository and current callers.
Load `engineering:skill-authoring` for concern, naming and sizing rules. Read
[native skill authoring](../new/references/native-authoring.md) and delegate this update to the
current host's discovered native skill creator with the requested change, existing files, scope and
acceptance checks. Do this for edits as well as renames; do not substitute hand-written authoring steps
for the host's native creator. Do not initialize an existing skill again.

Load `skill:check`, include its content and executable asset requirements in the brief, and apply
its checks to the completed update.

A rename or consolidation removes the former public capability in the same cutover. Delete old skill
entries, aliases, forwarding paths and competing discovery names. Keeping an old name as a differently
classified skill is still an incomplete rename. Keep supporting contracts and host adapters as resources
under their current owner rather than another discoverable name for the replaced capability.

Migrate all known authored callers, host adapters, selections, routes, templates, generated catalogs,
installed registrations and live runtime entry points. Do not add backwards compatibility, old-format
fallbacks or a second implementation. Reconcile the exact existing runtime owner before changing a live
registration; retain one writer and preserve its pending evidence.

Search the maintained corpus, generated discovery and known installed bindings for every retired qualified
identity, bare name and path. An active match keeps the update incomplete. Historical plans, commits and
review evidence may retain their original names; they are evidence, not current entry points. Record the
search scope and concrete result, then apply `skill:check` and the affected behavior tests. Template-layout
repositories also regenerate and run their Template checks; native-only skills retain native validation.
Verify fresh loading on both supported hosts and Windows/Linux behavior when executable resources changed.
Report any unverified installed entry point with its resolver and observable resume condition; source-only
checks do not establish a completed migration.
