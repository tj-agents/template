"""Find Python that loads source by path instead of importing it by name."""

from __future__ import annotations

import ast
import json
import subprocess
from collections.abc import Iterable, Iterator
from enum import Enum, auto
from pathlib import Path, PurePosixPath

BASELINE = ".agents/plugins/path-loading-baseline.json"
PATH_LOADERS = frozenset(
    {
        "importlib.util.spec_from_file_location",
        "importlib.machinery.SourceFileLoader",
        "runpy.run_path",
        "sys.path.insert",
        "sys.path.append",
        "sys.path.extend",
    }
)
SKIPPED_DIRECTORIES = frozenset({".git", ".venv", "__pycache__", "node_modules"})


class Walked(Enum):
    ANCESTOR = auto()
    BUNDLE_ROOT = auto()


type Anchor = Path | Walked


class Loads:
    def __init__(self, tree: ast.Module, file: Path) -> None:
        self.file = file
        self.names: dict[str, str] = {}
        self.constants: dict[str, list[ast.expr]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        self.names[alias.asname] = alias.name
                    else:
                        root = alias.name.split(".", 1)[0]
                        self.names[root] = root
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                for alias in node.names:
                    self.names[alias.asname or alias.name] = (
                        f"{node.module}.{alias.name}"
                    )
        for statement in tree.body:
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                target, value = statement.targets[0].id, statement.value
            elif (
                isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.value is not None
            ):
                target, value = statement.target.id, statement.value
            else:
                continue
            self.constants.setdefault(target, []).append(value)

    def qualified(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return self.names.get(node.id)
        if isinstance(node, ast.Attribute):
            owner = self.qualified(node.value)
            return f"{owner}.{node.attr}" if owner else None
        return None

    def anchor(
        self,
        node: ast.expr,
        ancestor: str | None = None,
        seen: frozenset[str] = frozenset(),
    ) -> Anchor | None:
        if isinstance(node, ast.Name):
            if node.id == ancestor:
                return Walked.ANCESTOR
            values = self.constants.get(node.id, [])
            if len(values) != 1 or node.id in seen:
                return None
            return self.anchor(values[0], ancestor, seen | {node.id})
        if isinstance(node, ast.Call):
            return self.anchor_call(node, ancestor, seen)
        if isinstance(node, ast.Attribute) and node.attr == "parent":
            owner = self.anchor(node.value, ancestor, seen)
            return owner.parent if isinstance(owner, Path) else None
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "parents"
            and isinstance(node.slice, ast.Constant)
            and type(node.slice.value) is int
        ):
            owner = self.anchor(node.value.value, ancestor, seen)
            if not isinstance(owner, Path):
                return None
            parents = owner.parents
            return (
                parents[node.slice.value] if node.slice.value < len(parents) else None
            )
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return self.join(self.anchor(node.left, ancestor, seen), [node.right])
        return None

    def anchor_call(
        self, node: ast.Call, ancestor: str | None, seen: frozenset[str]
    ) -> Anchor | None:
        function = node.func
        if node.keywords:
            return None
        if self.qualified(function) == "pathlib.Path":
            return (
                self.file
                if len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "__file__"
                else None
            )
        if isinstance(function, ast.Attribute) and function.attr in {
            "resolve",
            "absolute",
        }:
            return None if node.args else self.anchor(function.value, ancestor, seen)
        if isinstance(function, ast.Attribute) and function.attr == "joinpath":
            return self.join(self.anchor(function.value, ancestor, seen), node.args)
        if (
            isinstance(function, ast.Name)
            and function.id == "next"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.GeneratorExp)
        ):
            return self.nearest_ancestor(node.args[0], seen)
        return None

    def nearest_ancestor(
        self, walk: ast.GeneratorExp, seen: frozenset[str]
    ) -> Anchor | None:
        if len(walk.generators) != 1:
            return None
        generator = walk.generators[0]
        if (
            generator.is_async
            or not isinstance(generator.target, ast.Name)
            or not isinstance(generator.iter, ast.Attribute)
            or generator.iter.attr != "parents"
            or not isinstance(self.anchor(generator.iter.value, None, seen), Path)
        ):
            return None
        return self.anchor(walk.elt, generator.target.id, seen)

    @staticmethod
    def join(owner: Anchor | None, segments: Iterable[ast.expr]) -> Anchor | None:
        if owner is None:
            return None
        for segment in segments:
            if not isinstance(segment, ast.Constant) or not isinstance(
                segment.value, str
            ):
                return None
            relative = PurePosixPath(segment.value)
            if (
                not segment.value
                or "\\" in segment.value
                or ":" in segment.value
                or relative.is_absolute()
                or ".." in relative.parts
            ):
                return None
            if isinstance(owner, Path):
                owner = owner.joinpath(*relative.parts)
            elif owner is Walked.ANCESTOR:
                if relative.parts[0] != ".agents":
                    return None
                owner = Walked.BUNDLE_ROOT
        return owner

    def bootstrap(self, statement: ast.stmt, root: Path) -> bool:
        if not isinstance(statement, ast.Expr) or not isinstance(
            statement.value, ast.Call
        ):
            return False
        call = statement.value
        if (
            self.qualified(call.func) != "sys.path.insert"
            or call.keywords
            or len(call.args) != 2
            or not isinstance(call.args[0], ast.Constant)
            or call.args[0].value != 0
            or not isinstance(call.args[1], ast.Call)
            or not isinstance(call.args[1].func, ast.Name)
            or call.args[1].func.id != "str"
            or len(call.args[1].args) != 1
            or call.args[1].keywords
        ):
            return False
        target = self.anchor(call.args[1].args[0])
        return target is Walked.BUNDLE_ROOT or (
            isinstance(target, Path) and target.is_relative_to(root)
        )


def path_loads(source: bytes, file: Path, root: Path) -> list[tuple[int, str]]:
    tree = ast.parse(source, str(file))
    loads = Loads(tree, file)
    sanctioned = {
        id(statement.value)
        for statement in tree.body
        if isinstance(statement, ast.Expr) and loads.bootstrap(statement, root)
    }
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and id(node) not in sanctioned:
            name = loads.qualified(node.func)
            if name in PATH_LOADERS:
                found.append((node.lineno, name))
    return sorted(found)


def python_files(root: Path, excluded: Iterable[str]) -> Iterator[str]:
    skipped = tuple(excluded)
    listed = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "*.py",
        ],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if listed.returncode == 0:
        relatives = sorted(
            {raw.decode("utf-8") for raw in listed.stdout.split(b"\0") if raw}
        )
    else:
        relatives = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*.py")
            if not SKIPPED_DIRECTORIES.intersection(path.relative_to(root).parts)
        )
    for relative in relatives:
        if (root / relative).is_file() and not any(
            relative == entry or relative.startswith(f"{entry}/") for entry in skipped
        ):
            yield relative


def violations(
    root: Path, excluded: Iterable[str]
) -> tuple[dict[str, list[tuple[int, str]]], list[str]]:
    found: dict[str, list[tuple[int, str]]] = {}
    problems = []
    resolved = root.resolve()
    for relative in python_files(root, excluded):
        path = resolved / relative
        try:
            loads = path_loads(path.read_bytes(), path, resolved)
        except (OSError, SyntaxError, ValueError) as error:
            problems.append(f"{relative}: cannot scan for path loading ({error})")
            continue
        if loads:
            found[relative] = loads
    return found, problems


def read_baseline(root: Path) -> dict[str, int] | None:
    path = root / BASELINE
    if not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not all(
        isinstance(key, str) and type(value) is int and value > 0
        for key, value in document.items()
    ):
        raise ValueError(f"{BASELINE}: map each repository path to a positive count")
    return document


def check(root: Path, excluded: Iterable[str], command: str) -> list[str]:
    found, problems = violations(root, excluded)
    try:
        baseline = read_baseline(root)
    except (OSError, ValueError) as error:
        return [*problems, str(error)]
    allowed = baseline or {}
    for relative, loads in sorted(found.items()):
        if len(loads) > allowed.get(relative, 0):
            lines = ", ".join(f"{line} {name}" for line, name in loads)
            problems.append(
                f"{relative}: {len(loads)} path load(s), baseline allows "
                f"{allowed.get(relative, 0)} ({lines}); import the package by name "
                "after the module-level bundle-root bootstrap"
            )
    stale = [
        relative
        for relative, count in sorted(allowed.items())
        if len(found.get(relative, [])) < count
    ]
    problems += [
        f"{BASELINE}: {relative} allows {allowed[relative]} path load(s) but "
        f"{len(found.get(relative, []))} remain; shrink it with `{command}`"
        for relative in stale
    ]
    if baseline is None and found:
        problems.append(
            f"{BASELINE}: record the existing path loads with `{command}` and commit it"
        )
    return problems


def write_baseline(root: Path, excluded: Iterable[str]) -> dict[str, int]:
    found, problems = violations(root, excluded)
    if problems:
        raise ValueError("\n".join(problems))
    counts = {relative: len(loads) for relative, loads in found.items()}
    current = read_baseline(root)
    if current is not None:
        counts = {
            relative: min(count, counts[relative])
            for relative, count in current.items()
            if relative in counts
        }
    path = root / BASELINE
    if counts:
        path.write_text(
            json.dumps(dict(sorted(counts.items())), indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    else:
        path.unlink(missing_ok=True)
    return counts
