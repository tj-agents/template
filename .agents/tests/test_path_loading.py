import json
from pathlib import Path

import path_loading
import pytest

GENERATED = ("plugins", ".claude/skills")
COMMAND = "write the baseline"


def write(root: Path, relative: str, body: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def loads(root: Path, relative: str, body: str) -> list[tuple[int, str]]:
    path = write(root, relative, body).resolve()
    return path_loading.path_loads(path.read_bytes(), path, root.resolve())


def test_path_loading_calls_are_found_through_any_import_spelling(
    tmp_path: Path,
) -> None:
    body = (
        "import importlib.util\n"
        "import runpy\n"
        "import sys\n"
        "from importlib.machinery import SourceFileLoader as Loader\n"
        "from pathlib import Path\n"
        "\n"
        "importlib.util.spec_from_file_location('m', 'm.py')\n"
        "runpy.run_path('m.py')\n"
        "Loader('m', 'm.py')\n"
        "sys.path.append('lib')\n"
        "\n"
        "def lazy():\n"
        "    sys.path.insert(0, str(Path(__file__).resolve().parent))\n"
    )
    assert loads(tmp_path, ".agents/demo/runtime/entry.py", body) == [
        (7, "importlib.util.spec_from_file_location"),
        (8, "runpy.run_path"),
        (9, "importlib.machinery.SourceFileLoader"),
        (10, "sys.path.append"),
        (13, "sys.path.insert"),
    ]


@pytest.mark.parametrize(
    "bootstrap",
    [
        "sys.path.insert(0, str(Path(__file__).resolve().parent))\n",
        "HERE = Path(__file__).resolve().parent\n"
        'sys.path.insert(0, str(HERE.parents[1] / "agent-store" / "runtime"))\n',
        "ROOT = Path(__file__).resolve().parents[3]\n"
        'sys.path.insert(0, str(ROOT / ".agents/demo/runtime"))\n',
        "sys.path.insert(0, str(next(\n"
        '    root / ".agents/demo/runtime"\n'
        "    for root in Path(__file__).resolve().parents\n"
        '    if (root / ".agents/demo/runtime/tj_demo").is_dir()\n'
        ")))\n",
    ],
)
def test_the_module_level_bundle_root_bootstrap_is_allowed(
    tmp_path: Path, bootstrap: str
) -> None:
    body = f"import sys\nfrom pathlib import Path\n\n{bootstrap}\nimport tj_demo\n"
    assert loads(tmp_path, ".agents/demo/runtime/entry.py", body) == []


@pytest.mark.parametrize(
    "bootstrap",
    [
        'sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "core"))\n',
        'sys.path.insert(0, str(Path(__file__).resolve().parent / ".." / "core"))\n',
        "sys.path.insert(0, str(next(\n"
        '    root / "core/.agents/core/runtime"\n'
        "    for root in Path(__file__).resolve().parents\n"
        '    if (root / "core").is_dir()\n'
        ")))\n",
        'sys.path.insert(0, str(Path.cwd() / ".agents/demo/runtime"))\n',
        "sys.path.insert(1, str(Path(__file__).resolve().parent))\n",
    ],
)
def test_a_bootstrap_cannot_reach_outside_its_bundle(
    tmp_path: Path, bootstrap: str
) -> None:
    root = tmp_path / "demo"
    body = f"import sys\nfrom pathlib import Path\n\n{bootstrap}"
    assert loads(root, ".agents/demo/runtime/entry.py", body) == [
        (4, "sys.path.insert")
    ]


def test_generated_outputs_are_not_scanned(tmp_path: Path) -> None:
    write(tmp_path, "plugins/demo/run.py", "import runpy\nrunpy.run_path('x')\n")
    write(tmp_path, ".claude/skills/demo/run.py", "import runpy\nrunpy.run_path('x')\n")
    assert path_loading.check(tmp_path, GENERATED, COMMAND) == []


def test_the_baseline_ratchet_only_shrinks(tmp_path: Path) -> None:
    (tmp_path / ".agents/plugins").mkdir(parents=True)
    load = "import runpy\nrunpy.run_path('x')\n"
    write(tmp_path, "one.py", load + "runpy.run_path('y')\n")
    write(tmp_path, "two.py", load)
    problems = path_loading.check(tmp_path, GENERATED, COMMAND)
    assert problems[0].startswith("one.py: 2 path load(s), baseline allows 0 (2 ")
    assert problems[-1] == (
        f"{path_loading.BASELINE}: record the existing path loads with "
        f"`{COMMAND}` and commit it"
    )

    assert path_loading.write_baseline(tmp_path, GENERATED) == {
        "one.py": 2,
        "two.py": 1,
    }
    baseline = tmp_path / path_loading.BASELINE
    assert json.loads(baseline.read_text(encoding="utf-8")) == {
        "one.py": 2,
        "two.py": 1,
    }
    assert path_loading.check(tmp_path, GENERATED, COMMAND) == []

    write(tmp_path, "three.py", load)
    write(tmp_path, "two.py", load + "runpy.run_path('y')\n")
    assert [
        problem.split(":", 1)[0]
        for problem in path_loading.check(tmp_path, GENERATED, COMMAND)
    ] == ["three.py", "two.py"]
    assert path_loading.write_baseline(tmp_path, GENERATED) == {
        "one.py": 2,
        "two.py": 1,
    }
    assert path_loading.check(tmp_path, GENERATED, COMMAND)

    write(tmp_path, "one.py", load)
    (tmp_path / "two.py").unlink()
    (tmp_path / "three.py").unlink()
    assert path_loading.check(tmp_path, GENERATED, COMMAND) == [
        f"{path_loading.BASELINE}: one.py allows 2 path load(s) but 1 remain; "
        f"shrink it with `{COMMAND}`",
        f"{path_loading.BASELINE}: two.py allows 1 path load(s) but 0 remain; "
        f"shrink it with `{COMMAND}`",
    ]
    assert path_loading.write_baseline(tmp_path, GENERATED) == {"one.py": 1}
    assert path_loading.check(tmp_path, GENERATED, COMMAND) == []

    (tmp_path / "one.py").unlink()
    assert path_loading.write_baseline(tmp_path, GENERATED) == {}
    assert not baseline.exists()


def test_a_malformed_baseline_is_reported(tmp_path: Path) -> None:
    write(tmp_path, path_loading.BASELINE, '{"one.py": 0}\n')
    assert path_loading.check(tmp_path, GENERATED, COMMAND) == [
        f"{path_loading.BASELINE}: map each repository path to a positive count"
    ]
