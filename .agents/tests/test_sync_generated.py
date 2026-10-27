import contextlib
import importlib.util
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "sync_generated", ROOT / ".agents" / "sync_generated.py"
)
assert SPEC is not None
assert SPEC.loader is not None
sync_generated: Any = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_generated)


def skill_text(
    name: str, kind: str, body: str = "", domain: str = "demo", profile: str = "core"
) -> str:
    return (
        f"---\nname: {name}\ndescription: The {name} skill.\nkind: {kind}\n"
        f"domain: {domain}\nprofile: {profile}\n"
        f"applicability: demo projects\nrequires: demo\nprovenance: house\n---\n\n"
        f"# {name}\n\n{body}"
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write(path, json.dumps(value, indent=2) + "\n")


def make_repository(root: Path, plugins: tuple[str, ...] = ("demo",)) -> None:
    write_json(
        root / ".agents/plugins/template.json",
        {"schema_version": 1, "repository": "owner/demo", "type": "stack"},
    )
    write_json(
        root / ".agents/plugins/payloads.json",
        {"payloads": {plugin: [plugin] for plugin in plugins}},
    )
    for host in ("claude", "codex"):
        templates = {
            "claude": {"description": "Demo.", "owner": {"name": "Owner"}},
            "codex": {"interface": {"displayName": "Demo"}},
        }
        write_json(
            root / f".agents/plugins/manifests/{host}/marketplace.json", templates[host]
        )
    for plugin in plugins:
        write_json(
            root / f".agents/tiers/{plugin}.json",
            {
                "schema_version": 1,
                "tier": plugin,
                "applies": "stack-present",
                "owner_repository": ["owner/demo"],
                "detect": {"files": ["demo.toml"]},
            },
        )
        common = {
            "name": plugin,
            "description": f"The {plugin} plugin.",
            "author": {"name": "Owner"},
            "repository": "https://github.com/owner/demo",
            "skills": "./skills/",
            "keywords": [plugin],
        }
        write_json(
            root / f".agents/plugins/manifests/claude/{plugin}.json",
            {**common, "displayName": plugin.title()},
        )
        write_json(
            root / f".agents/plugins/manifests/codex/{plugin}.json",
            {
                **common,
                "interface": {
                    "displayName": plugin.title(),
                    "category": "Productivity",
                },
            },
        )
        write(
            root / f".agents/{plugin}/utility/tool/SKILL.md",
            skill_text(
                "tool",
                "utility",
                "Run `<skill-directory>/scripts/run.py`. See [the notes]"
                "(templates/notes.md).\n",
            ),
        )
        write(root / f".agents/{plugin}/utility/tool/scripts/run.py", "print('run')\n")
        write(root / f".agents/{plugin}/utility/tool/templates/notes.md", "notes\n")
        write(
            root / f".agents/{plugin}/contract/style/SKILL.md",
            skill_text("style", "contract", f"Pairs with `{plugin}:tool`.\n"),
        )


def add_publication(root: Path, package: str, source: str) -> None:
    payload_path = root / ".agents/plugins/payloads.json"
    payloads = json.loads(payload_path.read_text(encoding="utf-8"))
    payloads["payloads"][package] = [source]
    write_json(payload_path, payloads)
    for host in ("claude", "codex"):
        manifest_path = root / f".agents/plugins/manifests/{host}/{source}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["name"] = package
        if host == "claude":
            manifest["displayName"] = package.title()
        else:
            manifest["interface"]["displayName"] = package.title()
        write_json(root / f".agents/plugins/manifests/{host}/{package}.json", manifest)


def build(root: Path) -> dict[str, bytes]:
    return cast(dict[str, bytes], sync_generated.build(root))


def assert_rejected(root: Path, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build(root)


def synchronize(root: Path, check: bool) -> tuple[int, str]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        code = sync_generated.synchronize(root, check)
    return code, stream.getvalue()


@pytest.fixture
def demo_root(tmp_path: Path) -> Path:
    make_repository(tmp_path)
    return tmp_path


@pytest.fixture
def installed_distribution(
    demo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any], list[list[str]]]:
    write(
        demo_root / "pyproject.toml",
        '[project]\nname = "fixture"\nversion = "0.1.0"\n'
        'dependencies = ["fixture-lib"]\n',
    )
    write(demo_root / "uv.lock", "# Resolution is mocked at the uv boundary.\n")
    site = demo_root / "installed"
    contents = {
        "fixture_lib/__init__.py": "VALUE = 42\n",
        "fixture_lib/data.txt": "data\n",
        "fixture_lib/__pycache__/__init__.cpython-312.pyc": "cache",
        "fixture_lib-0.1.0.dist-info/METADATA": "Name: fixture-lib\n",
        "fixture_lib-0.1.0.dist-info/WHEEL": "Root-Is-Purelib: true\n",
        "fixture_lib-0.1.0.dist-info/entry_points.txt": (
            "[demo]\nprobe=fixture_lib:VALUE\n"
        ),
        "fixture_lib-0.1.0.dist-info/LICENSE": "legacy license\n",
        "fixture_lib-0.1.0.dist-info/RECORD": "receipt",
        "fixture_lib-0.1.0.dist-info/direct_url.json": "local install provenance",
        "fixture_lib-0.1.0.dist-info/licenses/LICENSE": "license\n",
    }
    for relative, content in contents.items():
        write(site / relative, content)
    metadata: dict[str, Any] = {
        "name": "fixture-lib",
        "pure": True,
        "root": str(site),
        "files": list(contents),
    }
    calls: list[list[str]] = []

    def resolve(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, json.dumps(metadata), "")

    monkeypatch.setattr(sync_generated.shutil, "which", lambda _name: "uv")
    monkeypatch.setattr(sync_generated.subprocess, "run", resolve)
    return site, metadata, calls


def test_distribution_resources_ship_stable_files_and_resolve_once(
    demo_root: Path,
    installed_distribution: tuple[Path, dict[str, Any], list[list[str]]],
) -> None:
    site, _metadata, calls = installed_distribution
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {
            "payloads": {"demo": ["demo"]},
            "resources": [
                {"plugin": "demo", "distribution": "fixture-lib", "destination": target}
                for target in ("runtime", "skills/tool/scripts")
            ],
        },
    )
    output = build(demo_root)
    assert len(calls) == 1
    assert calls[0][1:4] == ["run", "--locked", "--no-editable"]
    for target in ("runtime", "skills/tool/scripts"):
        prefix = f"plugins/demo/{target}/"
        assert output[prefix + "fixture_lib/__init__.py"] == b"VALUE = 42\n"
        assert output[prefix + "fixture_lib/data.txt"] == b"data\n"
        assert output[prefix + "fixture_lib-0.1.0.dist-info/licenses/LICENSE"]
        assert output[prefix + "fixture_lib-0.1.0.dist-info/METADATA"]
        assert output[prefix + "fixture_lib-0.1.0.dist-info/entry_points.txt"]
        assert output[prefix + "fixture_lib-0.1.0.dist-info/LICENSE"]
    assert not any("direct_url" in path or path.endswith("/RECORD") for path in output)
    assert not any("__pycache__" in path for path in output)
    for host in ("claude", "codex"):
        assert (
            output[f".{host}/skills/tool/scripts/fixture_lib/__init__.py"]
            == b"VALUE = 42\n"
        )
    assert synchronize(demo_root, check=False)[0] == 0
    write(site / "fixture_lib/__init__.py", "VALUE = 43\n")
    assert synchronize(demo_root, check=True)[0] != 0


@pytest.mark.parametrize(
    "record",
    ["../outside.py", "/outside.py", "C:/outside.py", "a\\b.py", "a//b.py", "a/./b.py"],
)
def test_distribution_resources_reject_escaping_records(
    demo_root: Path,
    installed_distribution: tuple[Path, dict[str, Any], list[list[str]]],
    record: str,
) -> None:
    _site, metadata, _calls = installed_distribution
    metadata["files"] = [record]
    with pytest.raises(ValueError, match="Unsafe Python distribution record"):
        sync_generated.distribution_files(demo_root, "fixture-lib")


def test_distribution_resources_reach_separate_installed_codex_entry(
    demo_root: Path,
    installed_distribution: tuple[Path, dict[str, Any], list[list[str]]],
) -> None:
    extension = ".agents/plugins/adapters/codex/demo/tool.md"
    write(demo_root / extension, "Use the native Codex tool.\n")
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {
            "payloads": {"demo": ["demo"]},
            "host_adapters": [
                {"skill": "demo:tool", "host": "codex", "source": extension},
            ],
            "resources": [
                {
                    "plugin": "demo",
                    "distribution": "fixture-lib",
                    "destination": "skills/tool/scripts",
                },
            ],
        },
    )

    output = build(demo_root)

    for directory in ("skills", "codex-skills"):
        assert (
            output[f"plugins/demo/{directory}/tool/scripts/fixture_lib/__init__.py"]
            == b"VALUE = 42\n"
        )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"pure": False}, "pure Python wheel"),
        ({"name": "wrong"}, "identity does not match"),
        ({"files": ["hook.pth"]}, "cannot require .pth"),
        ({"files": ["missing.py"]}, "Missing or escaped"),
        ({"files": ["fixture_lib/__init__.py"] * 2}, "Duplicate Python"),
    ],
)
def test_distribution_resources_reject_unsupported_installs(
    demo_root: Path,
    installed_distribution: tuple[Path, dict[str, Any], list[list[str]]],
    change: dict[str, Any],
    message: str,
) -> None:
    _site, metadata, _calls = installed_distribution
    metadata.update(change)
    with pytest.raises(ValueError, match=message):
        sync_generated.distribution_files(demo_root, "fixture-lib")


def test_distribution_resources_require_declared_locked_runtime_dependency(
    demo_root: Path,
    installed_distribution: tuple[Path, dict[str, Any], list[list[str]]],
) -> None:
    with pytest.raises(ValueError, match="not a runtime dependency"):
        sync_generated.distribution_files(demo_root, "undeclared")
    (demo_root / "uv.lock").unlink()
    with pytest.raises(ValueError, match=r"require a regular uv\.lock"):
        sync_generated.distribution_files(demo_root, "fixture-lib")


def test_distribution_resources_reject_links(
    demo_root: Path,
    installed_distribution: tuple[Path, dict[str, Any], list[list[str]]],
) -> None:
    site, metadata, _calls = installed_distribution
    linked = site / "linked"
    try:
        linked.symlink_to(site / "fixture_lib", target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    metadata["files"] = ["linked/__init__.py"]
    with pytest.raises(ValueError, match="Linked Python distribution resource"):
        sync_generated.distribution_files(demo_root, "fixture-lib")


def test_distribution_collision_does_not_mutate_installed_output(
    demo_root: Path,
    installed_distribution: tuple[Path, dict[str, Any], list[list[str]]],
) -> None:
    assert synchronize(demo_root, check=False)[0] == 0
    original = (demo_root / "plugins/demo/skills/tool/SKILL.md").read_bytes()
    resource = {
        "plugin": "demo",
        "distribution": "fixture-lib",
        "destination": "runtime",
    }
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {"payloads": {"demo": ["demo"]}, "resources": [resource, resource]},
    )
    with pytest.raises(ValueError, match="duplicate resource output"):
        synchronize(demo_root, check=False)
    assert (demo_root / "plugins/demo/skills/tool/SKILL.md").read_bytes() == original


@pytest.mark.parametrize("import_hook", [False, True])
def test_real_locked_wheel_runs_after_producer_and_environment_are_removed(
    tmp_path: Path,
    import_hook: bool,
) -> None:
    producer = tmp_path / "producer"
    make_repository(producer)
    wheel = producer / "fixture_lib-0.1.0-py3-none-any.whl"
    files = {
        "fixture_lib/__init__.py": "VALUE = 42\n",
        "fixture_lib-0.1.0.dist-info/METADATA": (
            "Metadata-Version: 2.1\nName: fixture-lib\nVersion: 0.1.0\n"
        ),
        "fixture_lib-0.1.0.dist-info/WHEEL": (
            "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        ),
        "fixture_lib-0.1.0.dist-info/entry_points.txt": (
            "[demo.fixture]\nprobe = fixture_lib:VALUE\n"
        ),
        "fixture_lib-0.1.0.dist-info/LICENSE": "fixture license\n",
    }
    sentinel = tmp_path / "import-hook-executed"
    if import_hook:
        files["hook.pth"] = (
            f"import pathlib; pathlib.Path({str(sentinel)!r}).write_text('executed')\n"
        )
    files["fixture_lib-0.1.0.dist-info/RECORD"] = "".join(
        f"{name},,\n" for name in (*files, "fixture_lib-0.1.0.dist-info/RECORD")
    )
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    write(
        producer / "pyproject.toml",
        '[project]\nname = "fixture"\nversion = "0.1.0"\n'
        'requires-python = ">=3.12"\ndependencies = ["fixture-lib"]\n'
        "[tool.uv]\npackage = false\n[tool.uv.sources]\n"
        'fixture-lib = {path = "fixture_lib-0.1.0-py3-none-any.whl"}\n',
    )
    uv = shutil.which("uv")
    assert uv is not None
    write(producer / ".python-version", sys.executable + "\n")
    subprocess.run([uv, "lock", "--offline", "--project", str(producer)], check=True)
    write(
        producer / ".agents/demo/runtime/entry.py",
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parent))\n"
        "from fixture_lib import VALUE\n"
        "from importlib.metadata import entry_points\n"
        "print(VALUE, next(iter(entry_points(group='demo.fixture'))).name)\n",
    )
    write(
        producer / ".agents/demo/utility/tool/scripts/run.py",
        "from fixture_lib import VALUE\nprint(VALUE)\n",
    )
    write_json(
        producer / ".agents/plugins/payloads.json",
        {
            "payloads": {"demo": ["demo"]},
            "resources": [
                {
                    "plugin": "demo",
                    "distribution": "fixture-lib",
                    "destination": "runtime",
                },
                {
                    "plugin": "demo",
                    "distribution": "fixture-lib",
                    "destination": "skills/tool/scripts",
                },
                {
                    "plugin": "demo",
                    "source": ".agents/demo/runtime",
                    "destination": "runtime",
                },
            ],
        },
    )
    if import_hook:
        with pytest.raises(ValueError, match=r"cannot require \.pth"):
            build(producer)
        assert not sentinel.exists()
        assert not (producer / "plugins").exists()
        return
    assert synchronize(producer, check=False)[0] == 0
    installed = tmp_path / "installed"
    shutil.copytree(producer / "plugins/demo", installed)
    for host in ("claude", "codex"):
        shutil.copytree(producer / f".{host}/skills", installed / f".{host}/skills")
    shutil.rmtree(producer)
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(installed / "runtime/entry.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "42 probe"
    assert (installed / "runtime/fixture_lib-0.1.0.dist-info/LICENSE").is_file()
    for host in ("claude", "codex"):
        local = subprocess.run(
            [
                sys.executable,
                "-B",
                str(installed / f".{host}/skills/tool/scripts/run.py"),
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        assert local.stdout.strip() == "42"


def test_external_selection_dependency_is_preserved_and_shape_checked(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    path = tmp_path / ".agents/plugins/payloads.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    payloads["dependencies"] = {"demo": ["tj-agents/work"]}
    write_json(path, payloads)
    output = build(tmp_path)
    assert json.loads(output["plugins/demo/selection.json"])["dependencies"] == [
        "tj-agents/base",
        "tj-agents/engineering",
        "tj-agents/work",
    ]
    assert json.loads(output["plugins/demo/.claude-plugin/plugin.json"])[
        "dependencies"
    ] == [
        "base@tj-agents",
        "engineering@tj-agents",
        "work@tj-agents",
    ]
    invalid_dependencies: tuple[Any, ...] = (
        "base-agents/machine",
        "tj-agents/*",
        "tj-agents/machine/extra",
        "unknown",
        {},
    )
    for invalid in invalid_dependencies:
        payloads["dependencies"] = {"demo": [invalid]}
        write_json(path, payloads)
        with pytest.raises(ValueError):
            build(tmp_path)


def test_optional_harness_is_shipped_without_requiring_migration(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    assert "plugins/demo/harness.json" not in build(tmp_path)
    manifest = {
        "schema_version": 1,
        "plugin": "tj-agents/demo",
        "source_roots": [".agents/demo"],
        "requires": {},
    }
    write_json(tmp_path / ".agents/plugins/manifests/harness/demo.json", manifest)
    generated = json.loads(build(tmp_path)["plugins/demo/harness.json"])
    assert generated["requires"]["plugins"] == [
        "tj-agents/demo",
        "tj-agents/base",
        "tj-agents/engineering",
    ]
    assert generated["requires"]["marketplaces"] == [
        {"id": "tj-agents", "repository": "tj-agents/marketplace"}
    ]


def test_ships_skill_local_files_beside_the_package_and_adapter_entries(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    output = build(tmp_path)
    canonical = "plugins/demo/.agents/demo/utility/tool"
    adapter = "plugins/demo/skills/tool"
    assert (tmp_path / ".agents/demo/utility/tool/SKILL.md").read_bytes() == output[
        f"{canonical}/SKILL.md"
    ]
    for directory in (
        canonical,
        adapter,
        ".claude/skills/tool",
        ".codex/skills/tool",
    ):
        assert f"{directory}/scripts/run.py" in output
        assert f"{directory}/templates/notes.md" in output
    assert "plugins/demo/codex-skills/tool/SKILL.md" not in output
    assert (
        "canonical definition](../../.agents/demo/utility/tool/SKILL.md)"
        in output[f"{adapter}/SKILL.md"].decode()
    )
    assert (
        "canonical definition](../../../.agents/demo/utility/tool/SKILL.md)"
        in output[".claude/skills/tool/SKILL.md"].decode()
    )


def test_marketplaces_and_selection_are_derived_from_manifests_and_frontmatter(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    output = build(tmp_path)
    claude = json.loads(output[".claude-plugin/marketplace.json"])
    codex = json.loads(output[".agents/plugins/marketplace.json"])
    assert claude["plugins"] == [
        {
            "name": "demo",
            "source": "./plugins/demo",
            "description": "The demo plugin.",
            "category": "Productivity",
            "keywords": ["demo"],
        }
    ]
    assert codex["plugins"][0]["source"] == {
        "source": "local",
        "path": "./plugins/demo",
    }
    selection = json.loads(output["plugins/demo/selection.json"])
    assert selection["profiles"] == {"core": ["style", "tool"]}
    assert "- `tool` — utility — core" in output["plugins/demo/INDEX.md"].decode()


def test_publications_share_one_source_and_keep_one_local_adapter_set(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    add_publication(tmp_path, "template", "demo")
    for package in ("demo", "template"):
        write_json(
            tmp_path / f".agents/plugins/manifests/harness/{package}.json",
            {
                "schema_version": 1,
                "plugin": f"tj-agents/{package}",
                "source_roots": [".agents/demo"],
                "requires": {},
            },
        )
    output = build(tmp_path)
    for package in ("demo", "template"):
        canonical = f"plugins/{package}/.agents/demo/utility/tool/SKILL.md"
        adapter = f"plugins/{package}/skills/tool/SKILL.md"
        assert (tmp_path / ".agents/demo/utility/tool/SKILL.md").read_bytes() == output[
            canonical
        ]
        assert (
            "canonical definition](../../.agents/demo/utility/tool/SKILL.md)"
            in output[adapter].decode()
        )
        assert (
            json.loads(output[f"plugins/{package}/selection.json"])["plugin"] == package
        )
        assert (
            json.loads(output[f"plugins/{package}/harness.json"])["plugin"]
            == f"tj-agents/{package}"
        )
    assert (
        sum(
            name.endswith("/SKILL.md")
            for name in output
            if name == ".claude/skills/tool/SKILL.md"
        )
        == 1
    )
    assert [
        item["name"]
        for item in json.loads(output[".agents/plugins/marketplace.json"])["plugins"]
    ] == ["demo", "template"]


def test_aliases_are_projected_for_each_publication(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write(
        tmp_path / ".agents/demo/contract/old-style/SKILL.md",
        skill_text("old-style", "contract", "Use `demo:style`.\n"),
    )
    add_publication(tmp_path, "template", "demo")
    payloads = json.loads(
        (tmp_path / ".agents/plugins/payloads.json").read_text(encoding="utf-8")
    )
    payloads["compatibilitySkillAliases"] = {
        "demo": {"old-style": {"replacedBy": "demo:style", "removeAfter": "2027-03-31"}}
    }
    write_json(tmp_path / ".agents/plugins/payloads.json", payloads)
    selection = json.loads(build(tmp_path)["plugins/template/selection.json"])
    assert selection["compatibilitySkillAliases"] == {
        "old-style": {"replacedBy": "template:style", "removeAfter": "2027-03-31"}
    }
    assert selection["profiles"] == {"core": ["style", "tool"]}


def test_several_plugins_prefix_their_adapter_entries(tmp_path: Path) -> None:
    make_repository(tmp_path, ("demo", "extra"))
    output = build(tmp_path)
    assert ".claude/skills/extra-tool/SKILL.md" in output
    assert ".claude/skills/tool/SKILL.md" not in output


def test_an_alias_forwards_within_its_plugin_and_stays_out_of_profiles(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write(
        tmp_path / ".agents/demo/contract/old-style/SKILL.md",
        skill_text("old-style", "contract", "Use `demo:style`.\n"),
    )
    payloads = json.loads((tmp_path / ".agents/plugins/payloads.json").read_text())
    payloads["compatibilitySkillAliases"] = {
        "demo": {"old-style": {"replacedBy": "demo:style", "removeAfter": "2027-03-31"}}
    }
    write_json(tmp_path / ".agents/plugins/payloads.json", payloads)
    selection = json.loads(build(tmp_path)["plugins/demo/selection.json"])
    assert selection["profiles"] == {"core": ["style", "tool"]}
    payloads["compatibilitySkillAliases"]["demo"]["old-style"]["replacedBy"] = (
        "demo:missing"
    )
    write_json(tmp_path / ".agents/plugins/payloads.json", payloads)
    assert_rejected(tmp_path, "alias must forward")


def test_a_family_member_publishes_its_folder_path_joined_by_hyphens(
    demo_root: Path,
) -> None:
    write(
        demo_root / ".agents/demo/contract/state/client/SKILL.md",
        skill_text("state-client", "contract"),
    )
    write(
        demo_root / ".agents/demo/contract/state/server/SKILL.md",
        skill_text("state-server", "contract"),
    )
    output = build(demo_root)
    for name in ("state-client", "state-server"):
        suffix = name.removeprefix("state-")
        assert f"plugins/demo/.agents/demo/contract/state/{suffix}/SKILL.md" in output
        assert f"plugins/demo/skills/{name}/SKILL.md" in output
        assert f".codex/skills/{name}/SKILL.md" in output
    assert (
        "canonical definition](../../.agents/demo/contract/state/client/SKILL.md)"
        in output["plugins/demo/skills/state-client/SKILL.md"].decode()
    )
    assert (
        "canonical definition](../../../.agents/demo/contract/state/client/SKILL.md)"
        in output[".claude/skills/state-client/SKILL.md"].decode()
    )
    assert (
        "- `state-client` — contract — core" in output["plugins/demo/INDEX.md"].decode()
    )


def test_a_family_skill_ships_its_own_files_but_not_its_members(
    demo_root: Path,
) -> None:
    write(
        demo_root / ".agents/demo/contract/naming/SKILL.md",
        skill_text("naming", "contract"),
    )
    write(demo_root / ".agents/demo/contract/naming/templates/rules.md", "rules\n")
    write(
        demo_root / ".agents/demo/contract/naming/collaborators/SKILL.md",
        skill_text("naming-collaborators", "contract"),
    )
    write(
        demo_root / ".agents/demo/contract/naming/collaborators/templates/roles.md",
        "roles\n",
    )
    output = build(demo_root)
    assert "plugins/demo/skills/naming/templates/rules.md" in output
    assert "plugins/demo/skills/naming/collaborators/SKILL.md" not in output
    assert "plugins/demo/skills/naming-collaborators/templates/roles.md" in output


def test_a_member_named_without_its_family(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/state/client/SKILL.md",
        skill_text("client", "contract"),
    )
    assert_rejected(demo_root, "name must be state-client")


def test_a_file_in_a_family_folder(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/state/client/SKILL.md",
        skill_text("state-client", "contract"),
    )
    write(demo_root / ".agents/demo/contract/state/notes.md", "stray\n")
    assert_rejected(demo_root, "only skill folders")


def test_a_linked_member_folder_is_not_shipped(
    demo_root: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    write(outside / "SKILL.md", skill_text("style-linked", "contract"))
    link = demo_root / ".agents/demo/contract/style/linked"
    try:
        if sys.platform == "win32":
            import _winapi

            _winapi.CreateJunction(str(outside), str(link))
        else:
            link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"cannot create a link here: {error}")
    assert_rejected(demo_root, "links are not shipped")


def test_a_family_name_colliding_with_a_flat_skill(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/state/client/SKILL.md",
        skill_text("state-client", "contract"),
    )
    write(
        demo_root / ".agents/demo/contract/state-client/SKILL.md",
        skill_text("state-client", "contract"),
    )
    assert_rejected(demo_root, "duplicate skill state-client")


def test_missing_frontmatter_field(demo_root: Path) -> None:
    path = demo_root / ".agents/demo/contract/style/SKILL.md"
    write(path, path.read_text().replace("provenance: house\n", ""))
    assert_rejected(demo_root, "missing provenance")


def test_domain_other_than_the_repository_namespace(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", domain="other"),
    )
    assert_rejected(demo_root, "domain must be demo")


def test_kind_other_than_its_folder(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/knowledge/style/SKILL.md",
        skill_text("style", "contract"),
    )
    assert_rejected(demo_root, "kind must equal its kind folder")


def test_kind_with_a_digit_is_rejected(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract2/style/SKILL.md",
        skill_text("style", "contract2"),
    )
    assert_rejected(demo_root, "kind must be one lowercase word")


def test_kind_with_a_hyphen_is_rejected(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/my-kind/style/SKILL.md",
        skill_text("style", "my-kind"),
    )
    assert_rejected(demo_root, "kind must be one lowercase word")


def test_an_unknown_lowercase_kind_is_accepted(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/policy/learning/SKILL.md",
        skill_text("learning", "policy"),
    )
    output = build(demo_root)
    assert "plugins/demo/skills/learning/SKILL.md" in output


def test_file_directly_under_a_plugin_folder(demo_root: Path) -> None:
    write(demo_root / ".agents/demo/notes.md", "stray\n")
    assert_rejected(demo_root, "only kind folders")


def test_folder_without_skill_under_a_kind_folder(demo_root: Path) -> None:
    write(demo_root / ".agents/demo/utility/empty/notes.md", "stray\n")
    assert_rejected(demo_root, "only skill folders")


def test_unknown_qualified_and_bare_references(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", "See `demo:missing`.\n"),
    )
    assert_rejected(demo_root, "unknown skill reference demo:missing")
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", "See the `missing` skill.\n"),
    )
    assert_rejected(demo_root, "unknown skill reference `missing` skill")


def test_link_that_leaves_the_package(demo_root: Path) -> None:
    write(demo_root / "README.md", "readme\n")
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", "See [the readme](../../../../README.md).\n"),
    )
    assert_rejected(demo_root, "does not resolve from generated")


def test_package_links_cannot_reach_the_package_parent(demo_root: Path) -> None:
    make_repository(demo_root, ("demo", "extra"))
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text("style", "contract", "See [the packages](../../../../..).\n"),
    )
    assert_rejected(demo_root, "does not resolve from .agents/demo/contract/style")


def test_package_adapters_cannot_link_to_another_package(
    demo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_repository(demo_root, ("demo", "extra"))
    assert "plugins/extra/INDEX.md" in build(demo_root)
    adapter_body = sync_generated.adapter_body

    def cross_package_adapter(
        skill: dict[str, Any], adapter_dir: str, canonical_dir: str | None = None
    ) -> str:
        body: str = adapter_body(skill, adapter_dir, canonical_dir)
        if adapter_dir == "plugins/demo/skills/style":
            return body + "See [the extra package](../../../extra/INDEX.md).\n"
        return body

    monkeypatch.setattr(sync_generated, "adapter_body", cross_package_adapter)
    assert_rejected(
        demo_root, "does not resolve from generated plugins/demo/skills/style"
    )


def test_package_links_can_reach_in_package_ancestors_and_resources(
    demo_root: Path,
) -> None:
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text(
            "style",
            "contract",
            "See [the notes](../../utility/tool/templates/notes.md).\n",
        ),
    )
    output = build(demo_root)
    assert (
        b"[the notes](../../utility/tool/templates/notes.md)"
        in output["plugins/demo/.agents/demo/contract/style/SKILL.md"]
    )
    for host in (".claude", ".codex"):
        assert (
            b"canonical definition](../../../.agents/demo/contract/style/SKILL.md)"
            in output[f"{host}/skills/style/SKILL.md"]
        )


def test_missing_skill_directory_file(demo_root: Path) -> None:
    write(
        demo_root / ".agents/demo/contract/style/SKILL.md",
        skill_text(
            "style", "contract", "Run `<skill-directory>/scripts/missing.py`.\n"
        ),
    )
    assert_rejected(demo_root, "scripts/missing.py does not resolve")


def test_resources_ship_files_and_recursive_directories_and_track_freshness(
    demo_root: Path,
) -> None:
    write(demo_root / ".agents/hooks/host.json", '{"hook": true}\n')
    write(demo_root / ".agents/demo/runtime/runner.py", "print('run')\n")
    write(demo_root / ".agents/demo/resources/nested/data.txt", "resource\n")
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {
            "payloads": {"demo": ["demo"]},
            "resources": [
                {
                    "plugin": "demo",
                    "source": ".agents/hooks/host.json",
                    "destination": "hooks/host.json",
                },
                {
                    "plugin": "demo",
                    "source": ".agents/demo/runtime",
                    "destination": "runtime",
                },
                {
                    "plugin": "demo",
                    "source": ".agents/demo/resources",
                    "destination": "resources",
                },
            ],
        },
    )
    output = build(demo_root)
    assert output["plugins/demo/hooks/host.json"] == b'{"hook": true}\n'
    assert output["plugins/demo/runtime/runner.py"] == b"print('run')\n"
    assert output["plugins/demo/resources/nested/data.txt"] == b"resource\n"
    assert synchronize(demo_root, check=False)[0] == 0
    write(demo_root / ".agents/demo/runtime/runner.py", "print('changed')\n")
    code, report = synchronize(demo_root, check=True)
    assert code == 1
    assert "STALE: plugins/demo/runtime/runner.py" in report


def test_resources_allow_declared_cross_plugin_runtime_and_skill_assets(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path, ("demo", "extra"))
    write(tmp_path / ".agents/extra/runtime/shared.py", "print('shared')\n")
    write_json(
        tmp_path / ".agents/plugins/payloads.json",
        {
            "payloads": {"demo": ["demo"], "extra": ["extra"]},
            "resources": [
                {
                    "plugin": "demo",
                    "source": ".agents/extra/runtime",
                    "destination": "runtime",
                },
                {
                    "plugin": "demo",
                    "source": ".agents/extra/utility/tool/scripts",
                    "destination": "helpers",
                },
            ],
        },
    )
    output = build(tmp_path)
    assert output["plugins/demo/runtime/shared.py"] == b"print('shared')\n"
    assert output["plugins/demo/helpers/run.py"] == b"print('run')\n"

    payloads = json.loads(
        (tmp_path / ".agents/plugins/payloads.json").read_text(encoding="utf-8")
    )
    payloads["resources"][1]["source"] = ".agents/extra/utility/tool/SKILL.md"
    write_json(tmp_path / ".agents/plugins/payloads.json", payloads)
    assert_rejected(tmp_path, "discovered skill asset path")

    payloads["resources"][1]["source"] = ".agents/missing/runtime/shared.py"
    write_json(tmp_path / ".agents/plugins/payloads.json", payloads)
    assert_rejected(tmp_path, "declared canonical plugin")


def test_resources_ignore_python_caches_and_remain_fresh(demo_root: Path) -> None:
    write(demo_root / ".agents/demo/runtime/runner.py", "print('run')\n")
    write(
        demo_root / ".agents/demo/runtime/__pycache__/runner.cpython-312.pyc",
        "bytecode\n",
    )
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {
            "payloads": {"demo": ["demo"]},
            "resources": [
                {
                    "plugin": "demo",
                    "source": ".agents/demo/runtime",
                    "destination": "runtime",
                }
            ],
        },
    )
    output = build(demo_root)
    assert output["plugins/demo/runtime/runner.py"] == b"print('run')\n"
    assert not any("__pycache__" in path or path.endswith(".pyc") for path in output)
    assert synchronize(demo_root, check=False)[0] == 0
    assert synchronize(demo_root, check=True)[0] == 0


def test_resources_reject_prefix_collisions_before_generated_output_mutation(
    demo_root: Path,
) -> None:
    assert synchronize(demo_root, check=False)[0] == 0
    generated_skill = demo_root / "plugins/demo/skills/tool/SKILL.md"
    original = generated_skill.read_bytes()
    write(demo_root / ".agents/demo/runtime/runner.py", "print('run')\n")
    payloads: dict[str, Any] = {
        "payloads": {"demo": ["demo"]},
        "resources": [
            {
                "plugin": "demo",
                "source": ".agents/demo/runtime/runner.py",
                "destination": "runtime/runner.py",
            },
            {
                "plugin": "demo",
                "source": ".agents/demo/runtime/runner.py",
                "destination": "runtime",
            },
        ],
    }
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    with pytest.raises(ValueError, match="Duplicate generated output"):
        synchronize(demo_root, check=False)
    assert generated_skill.read_bytes() == original

    payloads["resources"] = [
        {
            "plugin": "demo",
            "source": ".agents/demo/runtime/runner.py",
            "destination": "skills",
        }
    ]
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    with pytest.raises(ValueError, match="Duplicate generated output"):
        synchronize(demo_root, check=False)
    assert generated_skill.read_bytes() == original


def test_resources_reject_unsafe_missing_undeclared_and_colliding_mappings(
    demo_root: Path,
) -> None:
    write(demo_root / ".agents/demo/runtime/runner.py", "print('run')\n")
    payloads: dict[str, Any] = {"payloads": {"demo": ["demo"]}, "resources": []}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "non-skill resource directories must be declared")

    payloads["resources"] = [
        {
            "plugin": "missing",
            "source": ".agents/demo/runtime/runner.py",
            "destination": "runtime/runner.py",
        }
    ]
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "resource plugin must be a declared package")

    payloads["resources"][0]["plugin"] = "demo"
    payloads["resources"][0]["source"] = ".agents/demo/runtime/missing.py"
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "is missing")

    payloads["resources"][0]["source"] = ".agents/demo/runtime/../runtime/runner.py"
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "unsafe resource source")

    payloads["resources"][0]["source"] = ".agents/demo/runtime/runner.py"
    payloads["resources"][0]["destination"] = "../runner.py"
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "unsafe resource destination")

    payloads["resources"] = [
        {
            "plugin": "demo",
            "source": ".agents/demo/runtime/runner.py",
            "destination": "runtime/runner.py",
        },
        {
            "plugin": "demo",
            "source": ".agents/demo/runtime/runner.py",
            "destination": "runtime/runner.py",
        },
    ]
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "duplicate resource output")

    payloads["resources"] = [
        {
            "plugin": "demo",
            "source": ".agents/demo/runtime/runner.py",
            "destination": "skills/tool/SKILL.md",
        }
    ]
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "Duplicate generated output")


def test_resources_reject_linked_inputs(
    demo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = demo_root / ".agents/demo/runtime/runner.py"
    write(source, "print('run')\n")
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {
            "payloads": {"demo": ["demo"]},
            "resources": [
                {
                    "plugin": "demo",
                    "source": ".agents/demo/runtime/runner.py",
                    "destination": "runtime/runner.py",
                }
            ],
        },
    )
    original = sync_generated.is_link_or_junction

    def linked(path: Path) -> bool:
        return path == source or original(path)

    monkeypatch.setattr(sync_generated, "is_link_or_junction", linked)
    assert_rejected(demo_root, "contains a link or junction")


def test_host_adapters_are_appended_only_for_the_declared_host(demo_root: Path) -> None:
    codex_source = ".agents/plugins/adapters/codex/demo/tool.md"
    claude_source = ".agents/plugins/adapters/claude/demo/tool.md"
    write(
        demo_root / codex_source, "## Codex behavior\n\nUse Codex-specific controls.\n"
    )
    write(
        demo_root / claude_source,
        "## Claude behavior\n\nUse Claude-specific controls.\n",
    )
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {
            "payloads": {"demo": ["demo"]},
            "host_adapters": [
                {"skill": "demo:tool", "host": "codex", "source": codex_source},
                {"skill": "demo:tool", "host": "claude", "source": claude_source},
            ],
        },
    )
    output = build(demo_root)
    codex = output[".codex/skills/tool/SKILL.md"].decode()
    claude = output[".claude/skills/tool/SKILL.md"].decode()
    claude_package = output["plugins/demo/skills/tool/SKILL.md"].decode()
    codex_package = output["plugins/demo/codex-skills/tool/SKILL.md"].decode()
    canonical = output["plugins/demo/.agents/demo/utility/tool/SKILL.md"].decode()
    assert "## Codex behavior" in codex
    assert "## Claude behavior" not in codex
    assert "## Claude behavior" in claude
    assert "## Codex behavior" not in claude
    assert "## Claude behavior" in claude_package
    assert "## Codex behavior" not in claude_package
    assert "## Codex behavior" in codex_package
    assert "## Claude behavior" not in codex_package
    assert "Run `<skill-directory>/scripts/run.py`." in canonical
    assert "Run `<skill-directory>/scripts/run.py`." not in claude_package
    assert "Run `<skill-directory>/scripts/run.py`." not in codex_package
    assert (
        json.loads(output["plugins/demo/.claude-plugin/plugin.json"])["skills"]
        == "./skills/"
    )
    assert (
        json.loads(output["plugins/demo/.codex-plugin/plugin.json"])["skills"]
        == "./codex-skills/"
    )

    payloads = json.loads(
        (demo_root / ".agents/plugins/payloads.json").read_text(encoding="utf-8")
    )
    payloads["host_adapters"][0]["source"] = (
        ".agents/plugins/adapters/codex/demo/other.md"
    )
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "host adapter source must be")


def test_host_adapter_assets_validate_against_pending_generated_outputs(
    demo_root: Path,
) -> None:
    codex_source = ".agents/plugins/adapters/codex/demo/tool.md"
    claude_source = ".agents/plugins/adapters/claude/demo/tool.md"
    write(demo_root / ".agents/demo/utility/tool/scripts/use.py", "print('use')\n")
    write(demo_root / codex_source, "Use [helper](scripts/use.py).\n")
    write(demo_root / claude_source, "Use [helper](scripts/use.py).\n")
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {
            "payloads": {"demo": ["demo"]},
            "host_adapters": [
                {"skill": "demo:tool", "host": "codex", "source": codex_source},
                {"skill": "demo:tool", "host": "claude", "source": claude_source},
            ],
        },
    )
    assert not (demo_root / ".codex").exists()
    output = build(demo_root)
    for host in (".codex/skills/tool", ".claude/skills/tool"):
        assert "[helper](scripts/use.py)" in output[f"{host}/SKILL.md"].decode()
        assert output[f"{host}/scripts/use.py"] == b"print('use')\n"

    write(demo_root / codex_source, "Use [missing](scripts/missing.py).\n")
    assert_rejected(demo_root, "does not resolve from")


def test_payloads_select_known_sources_and_retain_identity_publications(
    demo_root: Path,
) -> None:
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {"payloads": {"other": ["other"]}},
    )
    assert_rejected(demo_root, "other must select exactly one canonical source")
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {"payloads": {"published": ["demo"]}},
    )
    assert_rejected(demo_root, "demo must retain its identity publication")
    write_json(
        demo_root / ".agents/plugins/payloads.json",
        {"payloads": {"demo": ["demo", "demo"]}},
    )
    assert_rejected(demo_root, "demo must select exactly one canonical source")


def test_dependencies_reject_local_aliases_and_self_dependencies(
    demo_root: Path,
) -> None:
    make_repository(demo_root, ("demo", "extra"))
    add_publication(demo_root, "template", "extra")
    payloads = json.loads(
        (demo_root / ".agents/plugins/payloads.json").read_text(encoding="utf-8")
    )
    payloads["dependencies"] = {"demo": ["template"]}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "cannot depend on local alias template")
    payloads["dependencies"] = {"extra": ["template"]}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "extra cannot depend on local alias template")
    payloads["dependencies"] = {"demo": ["tj-agents/demo"]}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "demo cannot depend on tj-agents/demo; name a package")
    payloads["dependencies"] = {"demo": ["tj-agents/extra"]}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(demo_root, "demo cannot depend on tj-agents/extra; name a package")
    payloads["dependencies"] = {"demo": ["demo-agents/missing"]}
    write_json(demo_root / ".agents/plugins/payloads.json", payloads)
    assert_rejected(
        demo_root,
        "demo cannot depend on demo-agents/missing; another repository's package",
    )


VALID_HARNESS = {
    "schema_version": 1,
    "plugin": "tj-agents/demo",
    "source_roots": [".agents/demo"],
    "requires": {},
}

HARNESS_ENVELOPE_CASES: list[tuple[Any, str]] = [
    (None, "must be a JSON object"),
    ([], "must be a JSON object"),
    ({**VALID_HARNESS, "schema_version": True}, "schema_version must be 1"),
    ({**VALID_HARNESS, "schema_version": 2}, "schema_version must be 1"),
    (
        {**VALID_HARNESS, "plugin": "tj-agents/other"},
        "plugin must be tj-agents/demo",
    ),
    (
        {**VALID_HARNESS, "plugin": "demo-agents/demo"},
        "plugin must be tj-agents/demo",
    ),
    ({**VALID_HARNESS, "requires": None}, "requires must be a JSON object"),
    (
        {**VALID_HARNESS, "requires": {"plugins": ["base-agents/base"]}},
        "requires.plugins lists only tj-agents/<package> identities",
    ),
    (
        {**VALID_HARNESS, "requires": {"plugins": "tj-agents/base"}},
        "requires.plugins lists only tj-agents/<package> identities",
    ),
    (
        {**VALID_HARNESS, "source_roots": None},
        "source_roots must be a nonempty list",
    ),
    (
        {**VALID_HARNESS, "source_roots": ".agents/demo"},
        "source_roots must be a nonempty list",
    ),
    ({**VALID_HARNESS, "source_roots": []}, "source_roots must be a nonempty list"),
    ({**VALID_HARNESS, "source_roots": [1]}, "source_roots must be a nonempty list"),
    (
        {**VALID_HARNESS, "source_roots": [".agents/demo", ".agents/demo"]},
        "source_roots must be unique",
    ),
    (
        {**VALID_HARNESS, "source_roots": ["/agents/demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": ["C:/agents/demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": [".agents\\demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": [".agents/../demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": [".agents/\x00demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": ["plugins/demo"]},
        "unsafe canonical source root",
    ),
    (
        {**VALID_HARNESS, "source_roots": [".agents/missing"]},
        "is not shipped in demo",
    ),
]


@pytest.mark.parametrize("value,message", HARNESS_ENVELOPE_CASES)
def test_harness_rejects_invalid_envelopes_and_roots(
    demo_root: Path, value: Any, message: str
) -> None:
    harness = demo_root / ".agents/plugins/manifests/harness/demo.json"
    write_json(harness, value)
    assert_rejected(demo_root, message)


def test_harness_rejects_unreadable_json(
    demo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    valid = {
        "schema_version": 1,
        "plugin": "tj-agents/demo",
        "source_roots": [".agents/demo"],
        "requires": {},
    }
    harness = demo_root / ".agents/plugins/manifests/harness/demo.json"
    write(harness, "not json\n")
    assert_rejected(demo_root, "unreadable JSON")
    harness.write_bytes(b"\xff")
    assert_rejected(demo_root, "unreadable JSON")
    write_json(harness, valid)

    def locked(path: Path) -> str:
        raise OSError("locked")

    monkeypatch.setattr(sync_generated, "read", locked)
    with pytest.raises(ValueError, match="unreadable JSON"):
        sync_generated.harness_body(demo_root, "demo", {}, [], False)


def test_harness_cannot_claim_another_publication_source(demo_root: Path) -> None:
    make_repository(demo_root, ("demo", "extra"))
    add_publication(demo_root, "template", "demo")
    write_json(
        demo_root / ".agents/plugins/manifests/harness/template.json",
        {
            "schema_version": 1,
            "plugin": "tj-agents/template",
            "source_roots": [".agents/extra"],
            "requires": {},
        },
    )
    assert_rejected(demo_root, "source root '.agents/extra' is not shipped in template")


def test_publication_manifest_roster_is_complete(demo_root: Path) -> None:
    add_publication(demo_root, "template", "demo")
    (demo_root / ".agents/plugins/manifests/codex/template.json").unlink()
    assert_rejected(demo_root, "manifests/codex must hold exactly")


def test_tier_rules(demo_root: Path) -> None:
    path = demo_root / ".agents/tiers/demo.json"
    tier = json.loads(path.read_text())
    write_json(path, {**tier, "applies": "always"})
    assert_rejected(demo_root, "declares no detect markers")
    write_json(path, {key: value for key, value in tier.items() if key != "detect"})
    assert_rejected(demo_root, "needs at least one detect marker")
    write_json(path, {**tier, "owner_repository": ["owner/other"]})
    assert_rejected(demo_root, "owner_repository must name owner/demo")


def test_manifests_must_agree(demo_root: Path) -> None:
    path = demo_root / ".agents/plugins/manifests/claude/demo.json"
    write_json(path, {**json.loads(path.read_text()), "description": "Drifted."})
    assert_rejected(demo_root, "disagree on description")


def test_both_host_manifests_reject_version(demo_root: Path) -> None:
    for host in ("claude", "codex"):
        path = demo_root / f".agents/plugins/manifests/{host}/demo.json"
        write_json(path, {**json.loads(path.read_text()), "version": "1.0.0"})
        assert_rejected(demo_root, f"the {host} manifest must omit version")
        manifest = json.loads(path.read_text())
        manifest.pop("version")
        write_json(path, manifest)


def test_marketplace_templates_do_not_list_plugins(demo_root: Path) -> None:
    path = demo_root / ".agents/plugins/manifests/claude/marketplace.json"
    write_json(path, {**json.loads(path.read_text()), "plugins": []})
    assert_rejected(demo_root, "plugin entries are generated")


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_marketplace_templates_do_not_name_the_marketplace(
    demo_root: Path, host: str
) -> None:
    path = demo_root / f".agents/plugins/manifests/{host}/marketplace.json"
    write_json(path, {"name": "demo-agents", **json.loads(path.read_text())})
    assert_rejected(demo_root, "its tj-agents name and plugin entries are generated")


def test_every_marketplace_is_tj_agents_without_cross_marketplace_grants(
    demo_root: Path,
) -> None:
    output = build(demo_root)
    for path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        marketplace = json.loads(output[path])
        assert marketplace["name"] == "tj-agents"
        assert "allowCrossMarketplaceDependenciesOn" not in marketplace


@pytest.mark.parametrize("kind", ["stack", "tool", "utility", "profile"])
def test_harness_drops_every_marketplace_but_tj_agents(
    demo_root: Path, kind: str
) -> None:
    config = demo_root / ".agents/plugins/template.json"
    write_json(config, {**json.loads(config.read_text()), "type": kind})
    write_json(
        demo_root / ".agents/plugins/manifests/harness/demo.json",
        {
            **VALID_HARNESS,
            "requires": {
                "marketplaces": [
                    {"id": "demo-agents", "repository": "owner/demo"},
                    {"id": "base-agents", "repository": "tj-agents/core"},
                ],
                "plugins": ["tj-agents/demo", "tj-agents/work"],
            },
        },
    )
    harness = json.loads(build(demo_root)["plugins/demo/harness.json"])
    assert harness["plugin"] == "tj-agents/demo"
    assert harness["requires"]["marketplaces"] == [
        {"id": "tj-agents", "repository": "tj-agents/marketplace"}
    ]
    inherited = {
        "stack": ["tj-agents/base", "tj-agents/engineering"],
        "profile": ["tj-agents/base"],
    }
    assert harness["requires"]["plugins"] == (
        ["tj-agents/demo", *inherited[kind]]
        if kind in inherited
        else ["tj-agents/demo", "tj-agents/work"]
    )


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_manifest_dependencies_name_only_tj_agents(demo_root: Path, host: str) -> None:
    path = demo_root / f".agents/plugins/manifests/{host}/demo.json"
    manifest = json.loads(path.read_text())
    write_json(path, {**manifest, "dependencies": ["base@tj-agents", "extra"]})
    build(demo_root)
    write_json(path, {**manifest, "dependencies": ["base@base-agents"]})
    assert_rejected(demo_root, f"the {host} manifest dependencies are bare packages")


def test_legacy_template_config_pin_is_rejected(demo_root: Path) -> None:
    path = demo_root / ".agents/plugins/template.json"
    write_json(path, {**json.loads(path.read_text()), "template": "0.0.1"})
    assert_rejected(demo_root, r"unknown fields \['template'\]")


def test_byte_order_mark(demo_root: Path) -> None:
    path = demo_root / ".agents/demo/contract/style/SKILL.md"
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    assert_rejected(demo_root, "BOM")


def test_check_reports_missing_stale_and_extra_outputs(demo_root: Path) -> None:
    code, report = synchronize(demo_root, check=True)
    assert code == 1
    assert "MISSING: plugins/demo/skills/tool/SKILL.md" in report
    assert synchronize(demo_root, check=False)[0] == 0
    assert synchronize(demo_root, check=True)[0] == 0
    write(demo_root / "plugins/demo/INDEX.md", "edited\n")
    write(demo_root / "plugins/stale/INDEX.md", "stale\n")
    code, report = synchronize(demo_root, check=True)
    assert code == 1
    assert "STALE: plugins/demo/INDEX.md" in report
    assert "EXTRA: plugins/stale/INDEX.md" in report


def test_write_refuses_a_linked_generated_root(
    demo_root: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside")
    link = demo_root / "plugins"
    try:
        if sys.platform == "win32":
            import _winapi

            _winapi.CreateJunction(str(outside), str(link))
        else:
            link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"cannot create a link here: {error}")
    with pytest.raises(ValueError, match="link or junction"):
        synchronize(demo_root, check=False)


def run_generator_cli(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / ".agents/sync_generated.py"),
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_reserves_continuation_runtime_state(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write(tmp_path / ".agents/continuation/owner.json", "{}\n")
    write(tmp_path / ".agents/continuation/events.jsonl", "{}\n")
    write(tmp_path / ".agents/continuation/locks/foreground.lock", "locked\n")
    write(tmp_path / ".agents/continuation/scheduler/state.json", "{}\n")
    result = run_generator_cli(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "plugins/continuation").exists()
    assert "continuation" not in (tmp_path / ".agents/INDEX.md").read_text(
        encoding="utf-8"
    )
    assert "continuation" not in (
        tmp_path / ".agents/plugins/marketplace.json"
    ).read_text(encoding="utf-8")


def test_rejects_malformed_authored_plugin_directory(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write(tmp_path / ".agents/authored/owner.json", "{}\n")
    result = run_generator_cli(tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert (
        ".agents/authored/owner.json: only kind folders belong in a plugin folder"
        in result.stdout
    )


def test_each_copied_package_runs_from_its_adapter_resources(tmp_path: Path) -> None:
    name = "template"
    package = tmp_path / name
    shutil.copytree(ROOT / f"plugins/{name}", package)
    new_plugin = subprocess.run(
        [
            sys.executable,
            "-B",
            str(package / "skills/new-plugin/scripts/new_plugin.py"),
            "--repository",
            "owner/example",
            "--type",
            "utility",
            "--skill",
            "sweep",
            "--description",
            "Example plugin.",
            "--destination",
            str(tmp_path),
            "--author",
            "Ada Lovelace",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert new_plugin.returncode == 0, new_plugin.stdout + new_plugin.stderr
    example = tmp_path / "example"
    skill = example / ".agents/example/utility/sweep/SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8")
        + "\n```text\nInput: fixture\nOutput: verified\n```\n",
        encoding="utf-8",
    )
    adapter_check = package / "skills/check/scripts/check.py"
    canonical_check = package / ".agents/template/utility/check/scripts/check.py"
    check = subprocess.run(
        [sys.executable, "-B", str(adapter_check), "--root", str(example)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    gitignore = example / ".gitignore"
    gitignore.write_text(
        gitignore.read_text(encoding="utf-8") + "local/\n", encoding="utf-8"
    )
    drifted = subprocess.run(
        [sys.executable, "-B", str(adapter_check), "--root", str(example)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert drifted.returncode == 1
    assert ".gitignore: differs from current Template" in drifted.stderr
    update = subprocess.run(
        [
            sys.executable,
            "-B",
            str(package / "skills/update/scripts/update.py"),
            "--root",
            str(example),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert update.returncode == 0, update.stdout + update.stderr
    canonical = subprocess.run(
        [sys.executable, "-B", str(canonical_check), "--root", str(example)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert canonical.returncode == 0, canonical.stdout + canonical.stderr


def add_codex_hook(root: Path) -> None:
    (root / ".codex/hooks").mkdir(parents=True)
    shutil.copyfile(
        ROOT / ".codex/hooks/snapshot.py",
        root / ".codex/hooks/snapshot.py",
    )
    shutil.copyfile(
        ROOT / ".codex/hooks/bootstrap.py",
        root / ".codex/hooks/bootstrap.py",
    )
    write(root / ".agents/hooks/probe.py", "print('probe ran')\n")
    hook = {
        "type": "command",
        "command": 'python3 -B "${PLUGIN_ROOT}/hooks/probe.py"',
        "commandWindows": 'python -B "${PLUGIN_ROOT}/hooks/probe.py"',
    }
    write_json(
        root / ".agents/hooks/demo-codex.json",
        {"hooks": {"SessionStart": [{"hooks": [hook]}]}},
    )
    path = root / ".agents/plugins/payloads.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    payloads["resources"] = [
        {
            "plugin": "demo",
            "source": ".agents/hooks/demo-codex.json",
            "destination": "hooks/codex.json",
        },
        {
            "plugin": "demo",
            "source": ".agents/hooks/probe.py",
            "destination": "hooks/probe.py",
        },
    ]
    write_json(path, payloads)


def install_package(output: dict[str, bytes], destination: Path) -> None:
    for path, data in output.items():
        relative = path.removeprefix("plugins/demo/")
        if relative != path:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


def run_codex_hook(
    command: str, package: Path, data: Path
) -> subprocess.CompletedProcess[str]:
    arguments = shlex.split(command.replace("${PLUGIN_ROOT}", package.as_posix()))
    return subprocess.run(
        [sys.executable, *arguments[1:]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PLUGIN_DATA": str(data)},
        check=False,
        timeout=30,
    )


def test_codex_hooks_run_through_a_verified_package_snapshot(tmp_path: Path) -> None:
    make_repository(tmp_path)
    add_codex_hook(tmp_path)
    output = sync_generated.build(tmp_path)
    assert output["plugins/demo/hooks/codex/snapshot.py"] == (
        ROOT / ".codex/hooks/snapshot.py"
    ).read_bytes().replace(b"\r\n", b"\n")
    hook = json.loads(output["plugins/demo/hooks/codex.json"])["hooks"]["SessionStart"][
        0
    ]["hooks"][0]
    assert hook["command"].startswith("python3 -I -B -c ")
    assert hook["commandWindows"].startswith("python -I -B -c ")
    package = tmp_path / "cache/demo/1.0.0"
    install_package(output, package)

    result = run_codex_hook(hook["command"], package, tmp_path / "data")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "probe ran\n"

    (package / "hooks/probe.py").write_text("print('tampered')\n", encoding="utf-8")
    result = run_codex_hook(hook["command"], package, tmp_path / "fresh-data")
    assert result.returncode == 2
    assert "integrity check failed" in result.stderr


def load_snapshot_loader() -> Any:
    spec = importlib.util.spec_from_file_location(
        "codex_hook_snapshot", ROOT / ".codex/hooks/snapshot.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot_package(tmp_path: Path) -> tuple[Any, Path, str]:
    loader = load_snapshot_loader()
    package = tmp_path / "cache/demo/1.0.0"
    write(package / "hooks/probe.py", "print('probe ran')\n")
    return loader, package, loader.digest_tree(package)


def counting_digests(monkeypatch: pytest.MonkeyPatch, loader: Any) -> list[Path]:
    hashed: list[Path] = []
    digest_tree = loader.digest_tree

    def counted(root: Path) -> str:
        hashed.append(Path(root))
        return cast(str, digest_tree(root))

    monkeypatch.setattr(loader, "digest_tree", counted)
    return hashed


def test_codex_hook_snapshot_is_reused_without_rehashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loader, package, expected = snapshot_package(tmp_path)
    hashed = counting_digests(monkeypatch, loader)
    snapshots = tmp_path / "snapshots"

    created = loader.Snapshot.for_package(package, expected, snapshots).resolve()
    assert created.parent == snapshots
    assert (created / loader.MARKER).read_text(encoding="utf-8") == expected
    assert len(hashed) == 2

    shutil.rmtree(package)
    assert loader.Snapshot.for_package(package, expected, snapshots).resolve() == created
    assert len(hashed) == 2


def test_codex_hook_snapshot_without_a_matching_marker_is_rebuilt(
    tmp_path: Path,
) -> None:
    loader, package, expected = snapshot_package(tmp_path)
    snapshots = tmp_path / "snapshots"
    snapshot = loader.Snapshot.for_package(package, expected, snapshots).resolve()
    partial = snapshot.with_name(snapshot.name + ".0123456789abcdef0123456789abcdef")
    shutil.copytree(package, partial)

    for marker in (None, "sha256:" + "0" * 64):
        (snapshot / loader.MARKER).unlink()
        (snapshot / "hooks/probe.py").write_text("print('stale')\n", encoding="utf-8")
        if marker is not None:
            (snapshot / loader.MARKER).write_text(marker, encoding="utf-8")
        rebuilt = loader.Snapshot.for_package(package, expected, snapshots).resolve()
        assert rebuilt == snapshot
        assert (rebuilt / loader.MARKER).read_text(encoding="utf-8") == expected
        assert (rebuilt / "hooks/probe.py").read_text(encoding="utf-8") == (
            "print('probe ran')\n"
        )
    assert partial.is_dir()


def test_codex_hook_snapshot_creation_prunes_only_stale_siblings(
    tmp_path: Path,
) -> None:
    loader, package, expected = snapshot_package(tmp_path)
    snapshots = tmp_path / "snapshots"
    stale = loader.time.time() - loader.RETENTION_SECONDS - 60

    def sibling(name: str, used: float | None, marked: bool = True) -> Path:
        path = snapshots / name
        write(path / "hooks/probe.py", "print('old')\n")
        if marked:
            write(path / loader.MARKER, "sha256:old")
        if used is not None:
            os.utime(path / loader.MARKER if marked else path, (used, used))
        return path

    old = sibling("a" * 64, stale)
    recent = sibling("b" * 64, None)
    abandoned = sibling("c" * 64 + "." + "d" * 32, stale, marked=False)
    foreign = sibling("notes", stale)

    current = loader.Snapshot.for_package(package, expected, snapshots).resolve()
    assert not old.exists()
    assert not abandoned.exists()
    assert recent.is_dir()
    assert foreign.is_dir()

    os.utime(current / loader.MARKER, (stale, stale))
    late = sibling("e" * 64, stale)
    assert loader.Snapshot.for_package(package, expected, snapshots).resolve() == current
    assert late.is_dir()
    assert loader.time.time() - (current / loader.MARKER).stat().st_mtime < 60


def test_codex_hook_runs_from_the_live_package_when_snapshots_are_unavailable(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    add_codex_hook(tmp_path)
    output = sync_generated.build(tmp_path)
    hook = json.loads(output["plugins/demo/hooks/codex.json"])["hooks"]["SessionStart"][
        0
    ]["hooks"][0]
    package = tmp_path / "cache/demo/1.0.0"
    install_package(output, package)
    unusable = tmp_path / "data-is-a-file"
    unusable.write_text("", encoding="utf-8")

    result = run_codex_hook(hook["command"], package, unusable)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "probe ran\n"

    data = tmp_path / "data"
    assert run_codex_hook(hook["command"], package, data).returncode == 0
    (snapshot,) = (data / "hook-snapshots").iterdir()
    (snapshot / "hooks/codex/snapshot.py").write_text(
        "raise SystemExit(9)\n", encoding="utf-8"
    )
    result = run_codex_hook(hook["command"], package, data)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "probe ran\n"


def test_codex_hook_commands_must_start_from_the_plugin_root(tmp_path: Path) -> None:
    make_repository(tmp_path)
    add_codex_hook(tmp_path)
    write_json(
        tmp_path / ".agents/hooks/demo-codex.json",
        {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 -B probe.py",
                                "commandWindows": "python -B probe.py",
                            }
                        ]
                    }
                ]
            }
        },
    )
    with pytest.raises(ValueError, match="Unsupported Codex hook command"):
        sync_generated.build(tmp_path)


def test_host_hook_manifests_ship_from_their_host_directory(tmp_path: Path) -> None:
    make_repository(tmp_path)
    add_codex_hook(tmp_path)
    claude_hooks = {"hooks": {"SessionStart": [{"hooks": [{"type": "command"}]}]}}
    write_json(tmp_path / ".claude/hooks/demo.json", claude_hooks)
    path = tmp_path / ".agents/plugins/payloads.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    payloads["resources"].append(
        {
            "plugin": "demo",
            "source": ".claude/hooks/demo.json",
            "destination": "hooks/claude.json",
        }
    )
    write_json(path, payloads)
    output = sync_generated.build(tmp_path)
    assert json.loads(output["plugins/demo/hooks/claude.json"]) == claude_hooks


def test_host_runtime_ships_from_its_host_directory(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write(tmp_path / ".codex/runtime/client.py", "VALUE = 1\n")
    path = tmp_path / ".agents/plugins/payloads.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    payloads["resources"] = [
        {
            "plugin": "demo",
            "source": ".codex/runtime",
            "destination": ".agents/demo/runtime/codex",
        }
    ]
    write_json(path, payloads)
    output = sync_generated.build(tmp_path)
    assert output["plugins/demo/.agents/demo/runtime/codex/client.py"] == b"VALUE = 1\n"


def test_host_resources_outside_hooks_are_rejected(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write(tmp_path / ".claude/settings.json", "{}\n")
    path = tmp_path / ".agents/plugins/payloads.json"
    payloads = json.loads(path.read_text(encoding="utf-8"))
    payloads["resources"] = [
        {
            "plugin": "demo",
            "source": ".claude/settings.json",
            "destination": "settings.json",
        }
    ]
    write_json(path, payloads)
    with pytest.raises(ValueError, match="host resource source must be below"):
        sync_generated.build(tmp_path)


def test_codex_hook_bootstrap_compiles_only_simple_statements(tmp_path: Path) -> None:
    make_repository(tmp_path)
    add_codex_hook(tmp_path)
    with (tmp_path / ".codex/hooks/bootstrap.py").open("a", encoding="utf-8") as stream:
        stream.write("if package_root:\n    pass\n")
    with pytest.raises(ValueError, match="only simple statements"):
        sync_generated.build(tmp_path)


def test_template_generated_outputs_are_current() -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        assert sync_generated.synchronize(ROOT, check=True) == 0
