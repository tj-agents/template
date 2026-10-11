# Compatible Template publication

Status: implementation-ready successor design, 2026-10-11.
Owner: plans/template-structure/GOAL.md in the Refactor-TemplateStructureContract checkout. This reference owns no separate goal or ledger.
Parent artifact: 88c2c25fc763539a230561ed57b2c701e261e2f1, source version 1.3.0, draft PR #8. Parent CI 38182114392 passed Windows, Linux and native acceptance.
Successor: Refactor/TemplatePublication, source version 1.4.0, immediate PR base Refactor/TemplateStructureContract. Delivery is gated on PR #4, then PR #8, their generated publication and release consequences. The exact producer artifact is available now, so implementation and cumulative verification can proceed without taking the taxonomy owner's work.
Expected scope: generator/template and focused tests, paired Template manifests/harness, payload declaration, namespace-neutral canonical utility references, public README and .github/scripts/validate_hosts.py isolated native acceptance. Approximately 600?850 substantive lines; assess and split again if the scope exceeds that estimate. Generated outputs remain uncommitted.

Implementation paths follow root AGENTS.md: canonical generator template before its byte-identical vendored copy; generated artifacts through sync; no explanatory code comments; coordinated version bump. The repository has no skill-routes table or applicable language tier. Existing Python unittest and standard-library patterns are the implementation conventions. Core retains runtime, settings, hooks, catalog and detailed requires semantics.

## Consumption contract

The repository remains tj-agents/kit and the marketplace remains kit-agents. Both `kit` and `template` install independently from the same repository release. Each publication ships the same canonical `.agents/kit` procedures and resources, plus thin native discovery entries. Consumers may choose Template while all existing Kit addresses, workflow references and source/pin identities remain valid. No repository rename or duplicate authored capability tree is part of this slice.

Authored payloads become `{"payloads": {"kit": ["kit"], "template": ["kit"]}}`. Tiers, local adapters and dependencies/aliases remain owned by canonical source. Native manifests, package directories, selection.plugin and marketplace entries use public identity. Local discovery entries still emit once and retain their current names.

## Generator wiring

Destination: `.agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in`, then mirror `.agents/sync_generated.py` byte-for-byte.

Current `validate_payloads` accepts only `{plugin: [plugin] for plugin in plugins}` and returns None. Replace that equality with this normalization and return the mapping after the existing dependency/alias checks:

```python
    declarations = payloads.get("payloads")
    if not isinstance(declarations, dict) or not declarations:
        raise ValueError(".agents/plugins/payloads.json: payloads must be a nonempty object")
    publications = {}
    for package, owners in sorted(declarations.items()):
        if not isinstance(package, str) or not NAME.fullmatch(package):
            raise ValueError(f".agents/plugins/payloads.json: invalid package {package!r}")
        if (
            not isinstance(owners, list)
            or len(owners) != 1
            or not isinstance(owners[0], str)
            or owners[0] not in plugins
        ):
            raise ValueError(f".agents/plugins/payloads.json: {package} must select exactly one canonical source")
        publications[package] = owners[0]
    for source in plugins:
        if publications.get(source) != source:
            raise ValueError(f".agents/plugins/payloads.json: {source} must retain its identity publication")
```

Keep unknown-field, dependency envelope, source-key ownership, duplicate dependency and compatibility alias validation. Replace the entire inner dependency condition, including the current source-only membership check, with:

```python
        for need in needs:
            if (
                (need not in publications and not re.fullmatch(r"[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*", need))
                or publications.get(need) == plugin
            ):
                raise ValueError(f".agents/plugins/payloads.json: {plugin} cannot depend on {need}")
```

Here `plugin` remains the canonical source owning the dependency list. Change validate_payloads' annotation to dict[str, str] and end it with `return publications` after all existing alias checks. A fixture must prove a source can depend on another source's public alias and rejects every alias of its own source. Qualified dependencies need the marketplace identity, so call this helper after `load_manifests`:

```python
def validate_publication_dependencies(publications: dict, dependencies: dict, marketplace: str) -> None:
    for source, needs in dependencies.items():
        for need in needs:
            if "/" not in need:
                continue
            owner, package = need.split("/", 1)
            if owner == marketplace and (
                package not in publications or publications[package] == source
            ):
                raise ValueError(f".agents/plugins/payloads.json: {source} cannot depend on {need}")
```

Project only structured alias replacement targets; do not rewrite authored prose:

```python
def publication_aliases(package: str, aliases: dict) -> dict:
    return {
        name: {
            "replacedBy": f"{package}:{declaration['replacedBy'].split(':', 1)[1]}",
            "removeAfter": declaration["removeAfter"],
        }
        for name, declaration in aliases.items()
    }
```

The current build loop combines local discovery and public packaging. Split it into two loops. The deciding order is:

```python
    plugins = discover(root, namespace)
    payloads = load(root / ".agents/plugins/payloads.json")
    publications = validate_payloads(payloads, plugins)
    validate_tiers(root, plugins, repository)
    manifests, templates = load_manifests(root, publications, repository)
    validate_skill_references(plugins)
    aliases = payloads.get("compatibilitySkillAliases", {})
    dependencies = payloads.get("dependencies", {})
    validate_publication_dependencies(publications, dependencies, templates["claude"]["name"])
    single_plugin = len(plugins) == 1
```

First loop is source-keyed: emit local host adapters and repository INDEX once for each source. Second loop is `for package, source in publications.items()`: select `plugins[source]`, use published package for canonical output prefix, package adapter prefix, INDEX, selection.plugin, native manifests and harness; source for dependencies, profiles, alias declarations and tier path. Use `publication_aliases(package, aliases.get(source, {}))`. Marketplace loops use publications. `load_manifests` already consumes dictionary keys, so its expected roster becomes the public roster without weakening paired-manifest validation.

Current canonical_locations maps each source/skill to one location. Change it to lists and append every publication:

```python
    canonical_locations: dict[tuple[str, str], list[str]] = {}
    canonical_locations.setdefault((source, skill["name"]), []).append(canonical_dir)
```

In validate_file_references, validate each canonical body at every location, then validate adapter bodies as before:

```python
    for plugin, skills in plugins.items():
        for skill in skills.values():
            for directory in canonical_locations[(plugin, skill["name"])]:
                validate(plugin, skill, skill["body"], skill["directory"], directory, True, True)
```

Do not overwrite one publication's reference evidence with the other's. Preserve source skill metadata, canonical bytes and sibling adapter resource copies.

## Optional harness envelope

Current packaging merely parses and copies an optional harness file. Replace that block with this helper after the publication's canonical output has been emitted. It validates packaging facts and preserves the authored requires body without interpreting runtime policy.

```python
def harness_body(root: Path, package: str, marketplace: str, output: dict[str, bytes]) -> str | None:
    relative = f"{MANIFEST_ROOT}/harness/{package}.json"
    path = root / relative
    if not path.exists():
        return None
    try:
        body = read(path)
        manifest = json.loads(body)
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(f"{relative}: unreadable JSON ({error})") from None
    if not isinstance(manifest, dict):
        raise ValueError(f"{relative}: must be a JSON object")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError(f"{relative}: schema_version must be 1")
    if manifest.get("plugin") != f"{marketplace}/{package}":
        raise ValueError(f"{relative}: plugin must be {marketplace}/{package}")
    roots = manifest.get("source_roots")
    if not isinstance(roots, list) or not roots or not all(isinstance(value, str) and value for value in roots):
        raise ValueError(f"{relative}: source_roots must be a nonempty list of paths")
    if len(roots) != len(set(roots)):
        raise ValueError(f"{relative}: source_roots must be unique")
    for value in roots:
        source = PurePosixPath(value)
        if (
            "\\" in value or ":" in value or "\x00" in value
            or source.is_absolute() or ".." in source.parts
            or source.as_posix() != value or len(source.parts) < 2
            or source.parts[0] != ".agents"
        ):
            raise ValueError(f"{relative}: unsafe canonical source root {value!r}")
        target = f"plugins/{package}/{value}"
        if target not in output and not any(name.startswith(target + "/") for name in output):
            raise ValueError(f"{relative}: source root {value!r} is not shipped in {package}")
    return body
```

Call `harness_body(root, package, templates["claude"]["name"], output)` and emit the returned body as plugins/<package>/harness.json when present.

Template's explicit authored harness identifies kit-agents/template, resolves .agents/kit and requires kit-agents/template plus base-agents/base. Kit's existing harness remains kit-agents/kit. Both declare no new hooks or permissions. Add paired Template manifests by cloning the source paired fields, changing name and display name to Template, with both Codex package versions and KIT_VERSION/kit.json at 1.4.0. Keep repository URLs and skills roots unchanged.

## Native acceptance wiring

Current `.github/scripts/validate_hosts.py:validate_codex` creates one temporary CODEX_HOME and installs all marketplace entries together. Replace that single shared home with one home per chosen publication. Keep the marketplace add and chosen plugin add sequence, inspect installed/enabled names in that same home, and require exactly the chosen public name from this marketplace:

```python
    found = []
    for name in sorted(expected):
        with tempfile.TemporaryDirectory() as home:
            environment = {**os.environ, "CODEX_HOME": home}
            steps = [
                ["codex", "plugin", "marketplace", "add", str(root)],
                ["codex", "plugin", "add", f"{name}@{marketplace['name']}"],
            ]
            failed = False
            for step in steps:
                result = run(step, environment)
                if result.returncode != 0:
                    found.append(f"{' '.join(step)}: {result.stderr.strip() or result.stdout.strip()}")
                    failed = True
                    break
            if failed:
                continue
            result = run(["codex", "plugin", "list", "--json"], environment)
            if result.returncode != 0:
                found.append(f"codex plugin list: {result.stderr.strip() or result.stdout.strip()}")
                continue
            try:
                listing = json.loads(result.stdout)
            except ValueError:
                found.append(f"codex plugin list returned no JSON report for {name}")
                continue
            installed = {
                entry["name"]
                for entry in listing.get("installed", [])
                if entry.get("installed") and entry.get("enabled")
                and entry.get("marketplaceName") == marketplace["name"]
            }
            if installed != {name}:
                found.append(f"codex standalone install of {name} enabled {sorted(installed)}")
    return found
```

This adds no external installations outside temporary homes and leaves Claude's existing per-package strict validation intact. Verify the native CLI behavior; an unexpected implicit installation requires a concrete design reconciliation rather than treating the shared all-plugin installation as standalone proof.

## Namespace and product wording

Canonical check/new-plugin/update procedures use bare package-local skill references and their existing relative canonical links. Replace qualified internal Kit references explicitly, retain documented public compatibility addresses, and use neutral diagnostics where the same procedure serves both packages. Public README presents Template's purpose and install addresses and explains Kit compatibility. Root instruction files remain under their current owner; do not introduce unrelated global guidance changes. Do not regex-transform generated prose.

## Verification

Extend the existing Python fixtures with add_publication(root, package, source): update payload mapping and clone both source manifests to published name/displayName. No second source tree or tier file is created. Correct the existing optional harness fixture to identify demo-agents/demo and .agents/demo; add demo-agents/template pointing to that same source. Retain absent-harness behavior.

Prove identity-only fixtures preserve existing outputs; both public manifest rosters and marketplace entries; one local adapter set; canonical byte identity; reference validation in both copies; unchanged source tiers; aliases projected with unchanged dates/profiles; no local or same-marketplace qualified counterpart dependency; malformed mappings/manifest targets rejected.

Harness negatives cover invalid JSON/UTF-8/unreadable files, scalar/array envelopes, missing/unsupported/boolean version, wrong public identity, absent/string/empty/nonstring roots, duplicate roots, absolute/drive/backslash/traversal/NUL/noncanonical paths, roots outside .agents, and safe but absent or cross-publication roots. Assert focused diagnostics rather than duplicating every implementation line.

For each public name separately, copy only that generated package into a temporary directory, invoke new-plugin/check/update through its shipped adapter resources, create a repository, detect and repair vendored drift, and run canonical check. Core's structural tier checker must accept published Template with the unchanged Kit tier. Native acceptance must install each publication in a separate isolated Codex home and validate each Claude package; no machine-wide installation and no all-plugins-only proof.

Run sync, freshness, full nonzero unittest discovery, template byte equality and diff checks. Record native source versus installation acceptance truthfully. Commit only authored source/docs; publish a child PR against its immediate parent, independently review that layer, and await the bottom-up real release baseline before consumer pin changes.

Design check: all nine mechanism snippets parse as Python; the harness path predicates contain a single-backslash value and a NUL value. Source excerpts and caller order were checked against the exact parent generator. Parsing is not an integration test; cumulative source/native acceptance remains required.

Independent implementation-design review completed on October 12, 2026. The source-only dependency membership branch was corrected to public membership and source ownership; no mechanism remains unresolved. Production verification is still required.

Deliberate Kit survivors: repository tj-agents/kit and marketplace kit-agents preserve published addresses; plugins/kit preserves existing installations; canonical .agents/kit preserves one authored source; .agents/plugins/kit.json and KIT_VERSION/kit_version preserve the existing pin and generator API; kit workflow/tag references and compatibility fixtures continue proving old-consumer behavior. Public Template identity is additive; these retained names do not represent a second template owner.

## Implementation evidence (2026-10-12)

The successor implements the 1.4.0 source-only publication layer: `kit` remains its identity publication and
`template` publishes the same `.agents/kit` canonical procedures with separate native manifests, harness and
package adapters. Local discovery remains source-owned and emits once. Generated outputs are intentionally loose.

`pwsh .agents/sync-generated.ps1 -Check` reported 219 current files. The absolute-path unittest discovery found
114 tests and completed successfully in 32.943 seconds. The Core tier payload validator accepted the unchanged Kit
tier for the published Template package. `git diff --check` passed, and the canonical generator template and the
vendored `.agents/sync_generated.py` are byte-equal.

Native validation passed with Claude Code 2.1.282 and codex-cli 0.163.0-alpha.1. Claude validated the marketplace
and each generated package; Codex installed each public package in its own temporary `CODEX_HOME` and verified the
exact enabled roster. No machine-wide installation was used. No source commit was created in this successor.

