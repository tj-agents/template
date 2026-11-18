# Cpp package compatibility design

Date: October 12, 2026. Owning goal: the root `GOAL.md` in this directory. Status: bounded proposal for parent and independent assessment; no production implementation or readiness claim. This file is the investigation's only write lease. Cpp source, checkout, refs, independent PRs, configuration and installed plugins remain untouched.

## Finding and owner

Cpp needs a recorded consumer successor. None of its existing independent PRs implements physically packaged canonical definitions with thin native discovery entries. Cpp owns its multi-package generator and has no Kit pin. Do not replace it with Kit's generator, apply Kit starter checks, add a Template dependency, move authored definitions, or change public package identities.

The exact recorded baseline is `tj-agents/cpp` main `38d3b060d42c32921580d49949b411395e7eb245`. The object exists locally and GitHub's `commits/main` returned the same SHA during this investigation. The original checkout is **not** that baseline: it is `Feature/TierConventionsStructure` at `5e1aa7a6486b6bbb71a240c4ebf5a52a90d09198`. All source findings below use immutable objects, not its working files. Root and nearest AGENTS plus baseline README were read; no nested authored-source AGENTS was found in the recorded tree. Cpp standards are inspected payloads, not programming rules for this Python work.

All six open PRs belong to GitHub author `tomjseery`; their checkout/session owner retains delivery control. The ahead/behind counts are relative to recorded main, reported below in head-ahead/main-ahead order. Every PR targets `main`; these are independent branches, not a stack owned by this goal.

| PR and owner branch | Exact head | Counts | Relevant ownership and observed gate |
|---|---|---|---|
| PR37 `Feature/SelectionProfiles` | `3b42f8e8c568763d857d286224bcd7884a5e8bf6` | 2 / 2 | Adds `.agents/plugins/selection-profiles/cpp.json`, `selection_profiles` source map, `selection-profile.json` output, a cpp harness root, parity tests/workflow. GitHub base `057e169afd86b66878361a7b3d4b135ab71915a3`; mergeable/clean. Description waits for Core reader `c9b0037` publication through Core PR140; not independently verified here. |
| PR35 `Refactor/CppConventionVocabulary` | `35c0ab44503e2b6eb20d729678e23ca8269a6ef3` | 1 / 4 | Moves ten contract capabilities to convention and learning to policy; changes source `contentRewrites`, lexical kind validation, manifests/version record and guidance tests. Base `1a4b42d6ca8e7df8650932b3688c5ee48b5e12fb`; mergeable false/dirty. Preserve renamed folders and teaching semantics. |
| PR34 `Feature/TierConventionsStructure` | `5e1aa7a6486b6bbb71a240c4ebf5a52a90d09198` | 4 / 4 | Adds `.agents/tiers/*.json`, tier emission, alias INDEX rows and Core payload checker CI. Same base `1a4b42d`; false/dirty. PR description names Core PR68 prerequisite; do not adopt its checker/version choices. |
| PR32 `Feature/ConditionalSkillRoutes` | `1f3dce6cec1e67cb68825f2ea2a96e14a770bbdb` | 1 / 6 | Owns `.agents/gen_skill_routes.py`, route tests, generated route resource bytes and tool package versions. |
| PR31 `Feature/MsvcEditorEnvironment` | `d960b856c78f9693847e185cd7b1058aefd0375e` | 3 / 6 | Owns scaffold scripts/templates and clangd guidance/tests, plus all package versions. No machine installation is performed by this investigation. |
| PR23 `Docs/Clarify-Naming-Guidance` | `6f03b2a0d09d1ed4f0edf49e76fe431d2af2c89f` | 3 / 22 | Owns base style/domain guidance and cpp/base/cpp-standards versions. |

PR addresses are `https://github.com/tj-agents/cpp/pull/<number>`. The original root and separate vocabulary/selection/capability-harness checkouts are already occupied. PR36 capability harness is merged through `057e169`; its historical checkout remains independent. Create no successor in any occupied checkout. A later authorized writer uses then-current main after relevant owners reconcile, or an explicitly parent-recorded dependency base; it must not merge into another owner's feature branch. No exact successor base/version can be honestly assigned before that reconciliation.

## Exact source and package evidence

At the baseline `.agents/plugins/sources.json` schema 2 declares four kind-layout sources: `.agents/base` -> cpp, `.agents/gpp` -> gpp, `.agents/msvc` -> msvc, `.agents/win32` -> win32; domain is cpp. It also declares nine packages, flat `.codex/skills` / `.claude/skills` adapter names, host manifest roots and explicit runtime resources. It owns generated roots. `.agents/skills` is retired and forbidden. The packaged roots are `plugins/<package>`.

The four public packages are cpp, gpp, msvc and win32; compatibility packages are base, gcc, windows, cpp-standards and gpp-standards. Windows remains the combined msvc+win32 payload. Preserve `cpp-agents`, all existing `name:`, qualified IDs, dependencies, aliases, profile inputs and March 31, 2027 retirement dates. Preserve flat repository adapters such as cpp-build and windows-cpp-knowledge; those are distinct from package-local discovery names.

`.agents/sync_generated.py:adapter_body` already emits thin repository adapters pointing into authored `.agents`. Its `build` package loop instead writes `package_body` procedures directly to `plugins/<package>/skills/<name>/SKILL.md`. Both authored native manifests specify `./skills/`; one physical directory supplies both hosts. Native pairing does not require separate directories. Leave both roots and all interface/hooks/host fields unchanged.

`package_body` already preserves compatibility `skillNames`, single-pass `identifierRewrites` and checked `contentRewrites`. It replaces all resource-relative references with `../../resources/...`, which is correct for today's full native entry but wrong for a canonical body moved four levels below package root. `compatibility_alias_body` produces metadata plus a dated local redirect to `../<target>/SKILL.md`. Those aliases also need their own physical canonical definition: linking an alias entry directly to a target with a different metadata name fails the shared identity contract.

The only local Markdown resource links among the 18 authored capabilities are the three scaffold links: gpp `../scripts/new-gpp-project.sh`, msvc `../scripts/New-MsvcProject.ps1`, win32 `../scripts/Add-Win32App.ps1`. Their `<skill-directory>/../scripts/...` commands refer to the invoked native entry directory. Other Markdown links are external documentation; a `[]()` IIFE expression appears inside code and is not a resource link. Parent reference extraction must preserve code semantics.

Four authored harnesses ship verbatim. Each declares its canonical scope, sources/payloads and host manifest inputs. Cpp also declares session-context and hook manifests; tool packages declare `.agents/gen_skill_routes.py` and shared base templates. These metadata/file roots are **not shipped** at baseline. Runtime scripts/templates already ship at declared `resources/<scope>/utility/scripts` destinations, including shared base resources and rendered route profiles. Preserve those bytes/addresses; no new runtime interpretation or script execution is required for projection.

## Minimum correction

Keep the existing source schema and generator. Emit the full projected procedure under `plugins/<package>/.agents/<scope>/<kind>/<published-name>/SKILL.md`; ordinary public packages retain their authored relative source path. Compatibility packages use existing projected public names at that same layout depth. Generate a small wrapper at existing `skills/<published-name>/SKILL.md` with the projected canonical header and one direct `.agents` link. No extended-adapter declaration is needed: the ordinary wrapper exactly matches the shared validator's accepted Kit-style body. Preserve any additional frontmatter/host/lane fields verbatim; no current model/effort fields were detected and none is introduced.

Alias definitions live beside their canonical target in the projected kind directory, with unchanged alias metadata/dated redirect. Both native hosts reach the same alias definition and metadata name. This preserves the 15 canonical-package aliases and the five compatibility packages without treating them as exceptional extensions.

Resource contexts are explicit:

| Context | gpp scaffold example |
|---|---|
| Authored source | `.agents/gpp/utility/scaffold/SKILL.md` links `../scripts/new-gpp-project.sh` |
| Packaged canonical | `plugins/gpp/.agents/gpp/utility/scaffold/SKILL.md` links `../../../../resources/gpp/utility/scripts/new-gpp-project.sh` |
| Native invocation placeholder in canonical text | `<skill-directory>/../../resources/gpp/utility/scripts/new-gpp-project.sh` |
| Claude and Codex discovery entry | `plugins/gpp/skills/scaffold/SKILL.md` links `../../.agents/gpp/utility/scaffold/SKILL.md` |

Runtime resources stay at their existing destinations, with no second script/template tree. Existing source-to-resource declarations provide explicit harness projections for otherwise absent runtime roots such as `.agents/base/utility/scripts`. Canonical links themselves require physical `.agents` definitions and cannot use these projections. Physical scope roots take precedence, as in the parent common validator. For nonresource **file** roots in each authored canonical harness, ship exact source bytes under their original `.agents/...` path inside that package. This includes sources.json, payloads.json, both native manifests, cpp's session-context/hook manifests and tool packages' route generator. If PR37 lands, its new selection-profile source file is copied automatically from its actual harness declaration; its existing `selection-profile.json` projection also remains unchanged. No copied inputs are made executable by this design.

Retain harness source_roots and `requires` verbatim. No new harness is required for compatibility packages, which currently have none. Do not ship global source metadata/harness inputs in those packages: existing tests prohibit canonical qualified IDs leaking into compatibility payloads. Legacy canonical procedures still undergo the existing identifier/content rewrites.

## Complete bounded generator helpers

Add `posixpath` and `stat` to the existing standard-library imports. These helpers use existing baseline `package_body`, `metadata`, `FRONTMATTER`, `compatibility_alias_body`, `read`, `PurePosixPath`, `re` and `json`; they require no Kit module/API. `emit` is the existing duplicate-rejecting closure in `build`. Prefix relocation handles the concrete declared resource syntax present in these sources, including angle destinations. It is a projection operation, not the shared reference/security validator. Future undeclared local-reference syntax must fail the common package check until its source owner supplies a supported projection.

```python
def package_canonical_relative(skill: dict, name: str) -> str:
    source = PurePosixPath(skill["relative"])
    return (source.parent.with_name(name) / "SKILL.md").as_posix()


def package_definition(skill: dict, package: str, cfg: dict, resources: list[dict]) -> tuple[str, str, str]:
    name, body = package_body(skill, package, cfg, [])
    canonical = package_canonical_relative(skill, name)
    source_directory = PurePosixPath(skill["relative"]).parent.as_posix()
    canonical_directory = PurePosixPath(canonical).parent.as_posix()
    for resource in resources:
        if package not in resource["plugins"]:
            continue
        source_reference = posixpath.relpath(resource["source"], source_directory)
        native_reference = posixpath.relpath(resource["destination"], f"skills/{name}")
        canonical_reference = posixpath.relpath(resource["destination"], canonical_directory)
        body = body.replace(
            f"<skill-directory>/{source_reference}/",
            f"<skill-directory>/{native_reference}/",
        )
        for opener in ("](", "](<"):
            body = body.replace(
                f"{opener}{source_reference}/",
                f"{opener}{canonical_reference}/",
            )
    return name, canonical, body


def package_discovery_body(body: str, canonical: str, name: str) -> str:
    match = FRONTMATTER.match(body)
    if match is None:
        raise ValueError(f"{canonical}: missing frontmatter")
    values = metadata(body, PurePosixPath(canonical))
    if values["name"] != name:
        raise ValueError(f"{canonical}: projected name disagrees")
    title = next((line for line in match.group("body").splitlines() if line.startswith("# ")), f"# {name}")
    relative = posixpath.relpath(canonical, f"skills/{name}")
    return (
        f"---\n{match.group('header')}\n---\n\n{title}\n\n"
        f"Read and follow the [canonical definition]({relative}) in full.\n"
        "This discovery entry is generated; edit the referenced `.agents/` definition.\n"
    )


def emit_package_capabilities(package: str, cfg: dict, skills: dict, resources: list[dict], emit):
    owned = [skill for skill in skills.values() if skill["scope"] in cfg["scopes"]]
    prefix = f"plugins/{package}"
    names = set()
    aliases = {}
    for skill in sorted(owned, key=lambda item: item["name"]):
        name, canonical, body = package_definition(skill, package, cfg, resources)
        if name in names:
            raise ValueError(f"{package}: duplicate emitted skill {name}")
        names.add(name)
        emit(f"{prefix}/{canonical}", body)
        emit(f"{prefix}/skills/{name}/SKILL.md", package_discovery_body(body, canonical, name))
    for alias_name, alias in cfg.get("compatibilitySkillAliases", {}).items():
        if alias_name in names:
            raise ValueError(f"{package}: duplicate emitted skill {alias_name}")
        skill = skills[alias["source"]]
        target_name = cfg.get("skillNames", {}).get(skill["identifier"], skill["name"])
        canonical = package_canonical_relative(skill, alias_name)
        body = compatibility_alias_body(skill, alias_name, target_name, alias["removeAfter"])
        names.add(alias_name)
        aliases[alias_name] = {"replacedBy": f"{package}:{target_name}", "removeAfter": alias["removeAfter"]}
        emit(f"{prefix}/{canonical}", body)
        emit(f"{prefix}/skills/{alias_name}/SKILL.md", package_discovery_body(body, canonical, alias_name))
    return owned, names, aliases


def harness_input_path(root, relative: str):
    path = (root / relative).absolute()
    for ancestor in (*reversed(path.parents), path):
        try:
            info = ancestor.lstat()
        except OSError as error:
            raise ValueError(f"{ancestor}: unreadable harness input ({error})") from None
        if (
            stat.S_ISLNK(info.st_mode)
            or getattr(info, "st_file_attributes", 0) & 0x400
            or getattr(ancestor, "is_junction", lambda: False)()
        ):
            raise ValueError(f"{ancestor}: harness input must not be or sit under a link or junction")
    return path, info


def emit_harness_input_files(root, package: str, harness: dict, emit):
    roots = harness.get("source_roots")
    if (
        not isinstance(roots, list) or not roots
        or not all(isinstance(relative, str) and relative for relative in roots)
        or len(roots) != len(set(roots))
    ):
        raise ValueError(f"{package}: invalid harness source_roots")
    for relative in roots:
        if not isinstance(relative, str):
            raise ValueError(f"{package}: invalid harness source root")
        source = PurePosixPath(relative)
        if (
            source.is_absolute() or ".." in source.parts or "\\" in relative
            or ":" in relative or len(source.parts) < 2
            or source.parts[0] != ".agents" or source.as_posix() != relative
        ):
            raise ValueError(f"{package}: unsafe harness source root {relative!r}")
        path, info = harness_input_path(root, relative)
        if stat.S_ISREG(info.st_mode):
            emit(f"plugins/{package}/{relative}", read(path))
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"{package}: missing harness input {relative}")
```

In `.agents/sync_generated.py:build`, replace the existing per-package owned/procedure/compatibility-alias block with this exact statement, retaining subsequent manifests, selection, hooks, tiers/profile emission and marketplace order:

```python
        owned, emitted_names, compatibility_aliases = emit_package_capabilities(
            package, cfg, skills, config.get("resources", []), emit
        )
```

Replace only the existing optional harness block with:

```python
        harness = root / ".agents/plugins/manifests/harness" / f"{package}.json"
        if harness.is_file():
            manifest = load(harness)
            emit_harness_input_files(root, package, manifest, emit)
            emit(f"{package_root}/{package}/harness.json", read(harness))
```

`emit_package_capabilities` uses the fixed `plugins` root already required by baseline `validate`; do not relax that invariant. Baseline `validated_generated_roots` checks links/junctions only in generated paths; its authored-source list prevents overlap and does not guard source reads. Baseline `read`/`load` follow links. Therefore each newly copied harness file uses the source-local `harness_input_path` before reading: lexical absolute path without `resolve`, `lstat` for every ancestor including the root and file, symlink and Windows reparse-point rejection, and junction detection when available. Nonregular/non-directory inputs fail. The common output validator cannot detect source-link reads after bytes are emitted, so it is not a substitute for this guard. No concurrent filesystem mutation protection is claimed. Existing source safety plus the final approved common checker and independent review remain required; no generation is delivered before those gates. A copied file root is not recursively interpreted, and a directory root is checked by common shipped-envelope validation with existing resource projections.

## Exact-object design probe

This driver executes only the helpers above, obtains all baseline bytes through `git archive --format=zip <exact SHA>` into memory, and modifies an in-memory package map. It performs no checkout, export, generated-file write, ref update, tool install, machine change or scaffold script execution. Its source/module imports are standard library and immutable Cpp text; `read` of the harness helper is provided by an in-memory path facade. The shared package validator is separately loaded from the parent **design artifact**, not Kit `d0b42f2382e477c48ee7d062005b1813d712bee6`, whose approved producer does not yet contain this common API. No Cpp adoption of that vendored generator is proposed. This driver measures the prototype; permanent tests must exercise actual `build`, not rely on this baseline-overlay technique.

```python
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from importlib.machinery import SourceFileLoader
import hashlib
import importlib.util
import io
import json
import posixpath
import re
import stat
import subprocess
import zipfile

root = Path.cwd()
repo = "C:/Users/TommySeery/source/repos/tj-agents/cpp"
revision = globals().get("probe_revision", "38d3b060d42c32921580d49949b411395e7eb245")
reference = root / "plans/template-structure/CPP_PACKAGE_COMPATIBILITY.md"
blocks = re.findall(r"```python\n(.*?)\n```", reference.read_text(encoding="utf-8"), re.S)
archive = subprocess.check_output([
    "git", "-c", f"safe.directory={repo}", "-C", repo,
    "archive", "--format=zip", revision,
])
with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
    source = {name: bundle.read(name) for name in bundle.namelist() if not name.endswith("/")}
context = {"__name__": "cpp_packaging_design", "__file__": repo + "/.agents/sync_generated.py", "posixpath": posixpath, "stat": stat}
exec(compile(source[".agents/sync_generated.py"], revision + ":generator", "exec"), context)
exec(compile(blocks[0], str(reference) + ":helpers", "exec"), context)
config = json.loads(source[".agents/plugins/sources.json"])
skills = {}
for scope in config["scopes"]:
    for path, data in source.items():
        relative = PurePosixPath(path)
        if not path.startswith(scope["root"] + "/") or relative.name != "SKILL.md":
            continue
        if len(relative.relative_to(scope["root"]).parts) != 3:
            continue
        body = data.decode("utf-8")
        values = context["metadata"](body, relative)
        identifier = f"{scope['plugin']}:{values['name']}"
        skills[identifier] = {
            "scope": scope["name"], "relative": path, "body": body,
            "metadata": values, "name": values["name"], "identifier": identifier,
        }
outputs = {
    path: data for path, data in source.items()
    if path.startswith("plugins/") or path in config["marketplace_outputs"].values()
}
baseline = dict(outputs)

def emit(path, data):
    if path in outputs:
        raise ValueError(f"Duplicate generated output: {path}")
    outputs[path] = data.encode("utf-8") if isinstance(data, str) else data

class InputPath:
    def __init__(self, relative=""):
        self.relative = relative
    def __truediv__(self, other):
        return InputPath(posixpath.join(self.relative, str(other)))
    def is_file(self):
        return self.relative in source
    def is_dir(self):
        return any(path.startswith(self.relative + "/") for path in source)
    def absolute(self):
        return self
    @property
    def parents(self):
        return tuple(InputPath(path.as_posix() if path.as_posix() != "." else "") for path in PurePosixPath(self.relative).parents)
    def lstat(self):
        if self.relative == "" or self.is_dir():
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0)
        if self.is_file():
            return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0)
        raise FileNotFoundError(self.relative)
    def is_junction(self):
        return False
    def read_text(self, encoding="utf-8"):
        return source[self.relative].decode(encoding)

original_lstat = InputPath.lstat
original_junction = InputPath.is_junction
original_read_text = InputPath.read_text
input_reads = []
def observed_read(self, encoding="utf-8"):
    input_reads.append(self.relative)
    return original_read_text(self, encoding)
InputPath.read_text = observed_read
for blocked, mechanism in (
    (".agents/plugins/sources.json", "symlink"),
    (".agents/plugins", "symlink"),
    (".agents", "symlink"),
    ("", "symlink"),
    (".agents/plugins", "reparse"),
    (".agents/plugins", "junction"),
):
    def mocked_lstat(self):
        info = original_lstat(self)
        if self.relative == blocked and mechanism == "symlink":
            return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
        if self.relative == blocked and mechanism == "reparse":
            return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
        return info
    InputPath.lstat = mocked_lstat
    InputPath.is_junction = lambda self: self.relative == blocked and mechanism == "junction"
    input_reads.clear()
    emitted = []
    try:
        context["emit_harness_input_files"](
            InputPath(), "cpp", {"source_roots": [".agents/plugins/sources.json"]},
            lambda path, data: emitted.append(path),
        )
    except ValueError as error:
        assert "link or junction" in str(error), str(error)
    else:
        raise AssertionError((blocked, mechanism, "linked harness input accepted"))
    assert input_reads == [] and emitted == [], (blocked, mechanism, input_reads, emitted)
InputPath.lstat = original_lstat
InputPath.is_junction = original_junction
InputPath.read_text = original_read_text
print("Harness file/root/ancestor symlink, reparse and junction rejected before read/emission: PASS")

resource_count = 0
for package, cfg in config["packages"].items():
    prefix = f"plugins/{package}/"
    previous_names = {PurePosixPath(path).parent.name for path in outputs if path.startswith(prefix + "skills/") and path.endswith("/SKILL.md")}
    for path in list(outputs):
        if path.startswith(prefix + "skills/"):
            del outputs[path]
    owned, names, aliases = context["emit_package_capabilities"](
        package, cfg, skills, config.get("resources", []), emit
    )
    assert names == previous_names, (package, names, previous_names)
    selection = json.loads(source[prefix + "selection.json"])
    assert names == set(selection["skills"])
    assert aliases == selection.get("compatibilitySkillAliases", {})
    harness_path = f".agents/plugins/manifests/harness/{package}.json"
    if harness_path in source:
        context["emit_harness_input_files"](InputPath(), package, json.loads(source[harness_path]), emit)
    for path, data in baseline.items():
        if path.startswith(prefix + "resources/"):
            assert outputs[path] == data
            resource_count += 1
    for host in ("claude", "codex"):
        path = prefix + f".{host}-plugin/plugin.json"
        assert outputs[path] == baseline[path]
    for path in (prefix + "selection.json", prefix + "harness.json", prefix + "hooks/session_context.py"):
        if path in baseline:
            assert outputs[path] == baseline[path]

proposal = root / "plans/template-structure/PACKAGE_STRUCTURE.md"
loader = SourceFileLoader("shared_package_design", str(root / ".agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in"))
shared = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
loader.exec_module(shared)
shared_blocks = re.findall(r"```python\n(.*?)\n```", proposal.read_text(encoding="utf-8"), re.S)
exec(compile(shared_blocks[0], str(proposal) + ":helpers", "exec"), shared.__dict__)
projections = tuple(
    (package, resource["source"], resource["destination"])
    for resource in config["resources"] for package in resource["plugins"]
)
shared.validate_packages(outputs, source_projections=projections)
print("Exact revision:", revision)
print("Exact-revision nine-package projected shape: PASS")
print(f"Preserved resource/profile files: {resource_count}")
print(f"Baseline files: {len(baseline)}; projected files: {len(outputs)}; added files: {len(set(outputs) - set(baseline))}")
added = {path: data for path, data in outputs.items() if path not in baseline}
print(f"Added generated bytes: {sum(map(len, added.values()))}")
print("Canonical definition files:", sum(path.endswith("/SKILL.md") and "/.agents/" in path for path in added))

for package in config["packages"]:
    standalone = {path: data for path, data in outputs.items() if path.startswith(f"plugins/{package}/")}
    for host, marketplace_path in config["marketplace_outputs"].items():
        document = json.loads(outputs[marketplace_path])
        document["plugins"] = [entry for entry in document["plugins"] if entry["name"] == package]
        standalone[marketplace_path] = json.dumps(document).encode()
    selected = tuple(item for item in projections if item[0] == package)
    shared.validate_packages(standalone, source_projections=selected)
print("All nine packages independently close their shipped references: PASS")

distinct = {path: data for path, data in outputs.items() if path.startswith("plugins/gpp/")}
for host, marketplace_path in config["marketplace_outputs"].items():
    document = json.loads(outputs[marketplace_path])
    document["plugins"] = [entry for entry in document["plugins"] if entry["name"] == "gpp"]
    distinct[marketplace_path] = json.dumps(document).encode()
for path, data in tuple(distinct.items()):
    if path.startswith("plugins/gpp/skills/"):
        distinct[path.replace("/skills/", "/codex-skills/", 1)] = data
manifest_path = "plugins/gpp/.codex-plugin/plugin.json"
manifest = json.loads(distinct[manifest_path])
manifest["skills"] = "./codex-skills/"
distinct[manifest_path] = json.dumps(manifest).encode()
shared.validate_packages(distinct, source_projections=tuple(item for item in projections if item[0] == "gpp"))
print("Standalone gpp with distinct native roots and alias definitions: PASS")

def rejected(files, expected):
    try:
        shared.validate_packages(files, source_projections=projections)
    except ValueError as error:
        assert expected in str(error), (expected, str(error))
    else:
        raise AssertionError(f"Expected rejection containing {expected!r}")

for path in (
    "plugins/gpp/resources/gpp/utility/scripts/new-gpp-project.sh",
    "plugins/gpp/.agents/gpp/utility/scaffold/SKILL.md",
    "plugins/cpp/.agents/plugins/sources.json",
):
    damaged = dict(outputs)
    del damaged[path]
    rejected(damaged, "shipped")
damaged = dict(outputs)
path = "plugins/gpp/.agents/gpp/utility/scaffold/SKILL.md"
damaged[path] = damaged[path].replace(b"<skill-directory>/../../resources/", b"<skill-directory>/../../../../resources/")
rejected(damaged, "leaves package")
damaged = dict(outputs)
path = "plugins/cpp/skills/cpp-build/SKILL.md"
damaged[path] = damaged[path].replace(b"/cpp-build/SKILL.md", b"/build/SKILL.md")
rejected(damaged, "canonical definition")
damaged = dict(outputs)
path = "plugins/gpp/skills/scaffold/SKILL.md"
damaged[path] = damaged[path].replace(b"kind: utility", b"kind: policy")
rejected(damaged, "canonical kind disagrees")
damaged = dict(outputs)
for path in tuple(damaged):
    if path.startswith("plugins/gpp/resources/base/utility/scripts/"):
        del damaged[path]
rejected(damaged, "shipped")
cfg = json.loads(json.dumps(config["packages"]["cpp"]))
cfg["compatibilitySkillAliases"]["build"] = {"source": "cpp:build", "removeAfter": "2027-03-31"}
try:
    context["emit_package_capabilities"]("cpp", cfg, skills, config["resources"], lambda path, body: None)
except ValueError as error:
    assert "duplicate emitted skill build" in str(error)
else:
    raise AssertionError("Duplicate alias unexpectedly accepted")
legacy = set(config["packages"]) - {"cpp", "gpp", "msvc", "win32"}
identifiers = re.compile(r"(?<![\w@-])(?:cpp|gpp|msvc|win32):[a-z][a-z0-9-]*")
for path, data in outputs.items():
    if path.startswith("plugins/") and PurePosixPath(path).parts[1] in legacy:
        if PurePosixPath(path).suffix in {".md", ".json", ".py", ".sh", ".ps1", ".in"}:
            assert not identifiers.findall(data.decode("utf-8")), path
print("Metadata, projected harness resource, alias collision and legacy vocabulary fixtures: PASS")
try:
    shared.validate_packages(baseline, source_projections=projections)
except ValueError as error:
    print("Baseline expected incompatibility:", error)
else:
    raise AssertionError("Full-entry baseline unexpectedly conforms")
print("Missing native/canonical/harness files and wrong placeholder/alias context: PASS")
print("Parent proposal SHA256:", hashlib.sha256(proposal.read_bytes()).hexdigest())
print("Cpp helper lines:", len(blocks[0].splitlines()))
print("Cpp design probe lines:", len(blocks[-1].splitlines()))
```

## Production tests and measured scope

Retain existing tests and update the assertions that intentionally read full procedures from native entries. `test_cpp_structure.py` and `test_cpp_mixin_guidance.py` should read physically packaged canonical definitions; `test_canonical_names.py` should resolve the wrapper first, then verify the dated alias canonical redirect and scaffold Markdown path. Flat root-adapter tests remain unchanged. Its standalone-scaffold test must check normal links from canonical context and `<skill-directory>` from **both** native contexts, not assume the two references have the same string. Its no-canonical-ID-in-legacy-packages check remains intact.

Extend `test_capability_harness.py` to verify every declared file root is shipped byte-identically and every directory root is directly present or uniquely projected using existing resources, while unchanged source identity/permissions/hooks assertions remain. Actual `SYNC.build` tests reject duplicate alias names before overwrite and verify generated roots never consume authored inputs. Permanently retain the six source-file/root/ancestor symlink/reparse/junction cases from the executable fixture and their zero-read/zero-emission assertions; output validation cannot replace them. Add a focused package test module with a small standalone gpp fixture, distinct synthetic Claude/Codex roots, a compatibility alias and a combined windows fixture. Include metadata/name/target disagreement, missing canonical/resource/harness input, wrong canonical-vs-native placeholder context and failure with the author checkout unavailable. Keep the permanent test dependency on the approved shared validator at the eventual exact release, or run its packages-only CLI in CI; do not import an unpublished producer function into Cpp.

Meaningful acceptance after implementation: actual generation/freshness, full nonzero `.agents/tests` and hook discovery, route self-test, immutable package-version record, exact shared structural and Core tier checks, both native validators, isolated host acceptance for all nine packages and existing real G++/MSVC/Win32 scaffold builds where the tools exist. Existing CI pins Codex 0.154.0 / Claude 2.1.268 and currently exercises Linux; add the needed Windows source/package check without changing independent tool/profile policy. A CLI installation is not installed-agent execution. Historical signed provenance and attester behavior stay unchanged.

The source mechanism is the first helper block plus two small build replacements and two imports. It replaces the existing package loop rather than growing a second generator. Expected permanent test work is roughly 100-180 new focused lines plus 40-70 changed lines across existing guidance/name/harness assertions; this is an estimate until a writer measures the diff. Native manifests require **no root or host-field change**, but all nine packages need synchronized paired version increments because every package gains canonical definitions and wrapper changes. Append new `.agents/plugins/package-versions.json` records through the existing generator command. Version values must be chosen from reconciled current main, never copied from these independent PRs.

Generated `.agents` projections/native wrappers/resources/marketplaces/indexes/version digests are output, not additional authored source. Record generated file/byte counts separately from substantive source/test lines. Common-validator implementation remains the root producer successor and is not included in this Cpp slice's size. The checker CI checkout/version pin can only be concretely wired after the common validator actually lands/releases; Kit `d0b42f2` has no packages-only API and must not be presented as its release. Cpp still does not vendor Kit starter files or pin Kit as its own repository format.

## Probe result, limits and remaining choices

The completed baseline probe exited 0 on October 12, 2026. It reported nine-package shape, all nine standalone packages, distinct native roots/aliases, missing canonical/native resource/harness inputs, metadata disagreement, misplaced placeholders, duplicate alias rejection and legacy-vocabulary preservation as PASS. Baseline rejection was expected: `plugins/base/skills/cpp-build/SKILL.md: needs exactly one link to its canonical definition`. All 149 existing resource/profile files, both native manifests and applicable selection/harness/hook bytes were preserved. Baseline inventory 263 files became 348: 85 added generated files (63 canonical definitions and 22 harness input files), totaling 419,696 added generated bytes. This is projection-size evidence; release-version manifests/records were intentionally not changed in the in-memory model.

The corrected first helper block measures 109 source lines; the two build replacements are 3 and 5 lines, plus two imports: 119 proposed source lines before subtracting the replaced loop. The executable design driver measures 251 lines, distinct from estimated permanent test changes. The source guard correction added 16 helper lines and 57 design-fixture lines, including six mocked rejection cases that assert neither read nor emission occurs. Initial shared parent proposal hash was `32f551a32e8377ef8fd6f9e97cd6116929f6d65dba7b3b53bec90da57910de60`, the version with outstanding PKG-D1/D2 qualification. The final exit-0 rerun observed corrected parent artifact `766a05e163b168585f21d3d4d9ea8510fba7d9a8e03ac619d0882960388c084d` and repeated every PASS/count above. That earlier artifact had parsed block line counts 93/3/5/194. The source-guard correction parses at 109/3/5/251 and its six source-link fixtures plus all prior shape fixtures passed against observed shared artifact 8ee3c1e1c596755b5d1568c296036f360b159dc4fdab8454243cface944658f1; Final frozen-shared revalidation is complete: the isolated driver exited 0 against f3bd9ef7144c6adbd6c9fe57935a612b4f57f74edb9f921e158cbca248889535 (54,619 bytes), verified unchanged before and after the run. Every source-link and package fixture above passed; output counts remained 263 -> 348 files, 85 additions and 419,696 added bytes. These runs establish Cpp shape against those exact proposals, not their independent security acceptance. Parent and independent assessment remain required before assigning a production writer.

Evidence commands were read-only: `git cat-file -t <baseline>` returned commit; `git show <exact-SHA>:<path>` and `git diff <baseline>...<PR-head> -- <owned-paths>` supplied generator/tests/manifests/resource evidence; `git rev-list --left-right --count` supplied the table counts; `git worktree list --porcelain` identified occupied checkouts. `gh pr list --repo tj-agents/cpp --state open --json number,title,headRefName,headRefOid,baseRefName,url,author` and `gh api repos/tj-agents/cpp/pulls/{37,35,34}` returned the documented remote owners/bases/state/descriptions. `gh api repos/tj-agents/cpp/commits/main --jq .sha` returned the exact baseline. The driver is run by reading this document's final Python block and executing it through `python -B -` from the owning root worktree; `git archive --format=zip` output remains in memory.

Early reads encountered the restricted GitHub CLI config and a Python subprocess Git ownership check. A read-only sandbox escalation enabled GitHub reads; Git subprocesses use process-local `-c safe.directory=<exact Cpp root>`, without writing global configuration. Git warned that the global ignore file could not be read; the archive/probe still exited 0. One exploratory path read requested a convention folder absent at baseline (contract is correct); a misplaced root-relative design read and patch-context failures were corrected. A final probe wrapper initially shadowed its shared-artifact path variable with the driver module and failed its post-run hash assertion; the isolated-namespace rerun exited 0 and verified the frozen hash before and after execution. No success is attributed to failed commands.

The final artifact SHA256 is returned to the parent alongside this file; the hash is not embedded into its own bytes. This artifact does not establish production generation freshness, current PR CI, parent proposal security qualification, native host acceptance or real scaffold builds. Existing PR description test claims are attributed claims, not rerun proof. No fetch, config write, refs, commits, pushes, machine installation, canonical GOAL edit or source repair occurred.

Parent must assess this concrete projection mechanism and independently check reference extraction/code handling and portable-path protection in the common validator. The real remaining decisions are owner scheduling relative to the six open Cpp PRs, the exact reconciled successor base, the nine next package versions and the final released checker CI pin. Preserving one physical `skills/` directory for both native hosts and keeping runtime resources at existing destinations are the proposed minimum choices. A later implementation writer needs an explicit isolated lease; this document grants none.

Writer stopped after recording the guarded-helper correction and final frozen shared-artifact probe; parent owns reassessment and any subsequent production lease.
