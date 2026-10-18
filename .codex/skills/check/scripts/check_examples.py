#!/usr/bin/env python3
"""Fail changed authored guidance that has no concrete fenced example."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path, PurePosixPath

ROOT_STANDARDS = {
    "SOURCE_LAYOUT.md",
    "SKILL_KINDS.md",
    "PACKAGING.md",
    "CODE_CONVENTIONS.md",
}
EXCLUDED_ROOTS = {
    ".claude",
    ".codex",
    ".delivery",
    "logs",
    "log",
    "plans",
    "plugins",
    "records",
    "reviews",
    "template",
    "templates",
}
PLACEHOLDERS = re.compile(
    r"^(?:todo|tbd|placeholder|coming[ -]?soon|fill[ -]?me|example|\.\.\.|…)$",
    re.IGNORECASE,
)
OPENING_FENCE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})(.*)$")
METADATA_FENCE_TAGS = {"agent-host-coverage", "agent-host-completion", "completion"}


class CheckError(Exception):
    pass


def run_git(root: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise CheckError(message or f"git {' '.join(arguments)} failed")
    return result.stdout


def commit(root: Path, reference: str, option: str) -> str:
    try:
        return (
            run_git(root, "rev-parse", "--verify", f"{reference}^{{commit}}")
            .decode()
            .strip()
        )
    except CheckError as error:
        raise CheckError(
            f"{option} '{reference}' does not resolve to a commit"
        ) from error


def is_zero_reference(reference: str) -> bool:
    return bool(re.fullmatch(r"0+", reference))


def normalized_path(raw: str) -> PurePosixPath:
    path = PurePosixPath(raw.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or str(path) in {"", "."}:
        raise CheckError(f"path '{raw}' must be a repository-relative path")
    return path


def is_excluded(path: PurePosixPath) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    if parts[0] in EXCLUDED_ROOTS or parts[0] == "fixtures":
        return True
    return (
        len(parts) >= 6
        and parts[0] == ".agents"
        and any(part in {"fixtures", "resources", "templates"} for part in parts[4:-1])
    )


def is_authored_guidance(path: PurePosixPath) -> bool:
    if is_excluded(path):
        return False
    if len(path.parts) == 1 and path.name in ROOT_STANDARDS:
        return True
    if path.name == "AGENTS.md":
        return True
    if len(path.parts) >= 5 and path.parts[0] == ".agents" and path.name == "SKILL.md":
        return True
    return (
        len(path.parts) >= 2
        and path.suffix.lower() == ".md"
        and (path.parts[0] == "standards" or path.parts[:2] == ("docs", "standards"))
    )


def is_explicit_guidance(path: PurePosixPath) -> bool:
    return is_authored_guidance(path) or (
        not is_excluded(path) and len(path.parts) == 1 and path.suffix.lower() == ".md"
    )


def changed_paths(
    root: Path, base: str, head: str, merge_base: bool = False
) -> list[PurePosixPath]:
    head_commit = commit(root, head, "--head")
    if is_zero_reference(base):
        output = run_git(root, "ls-tree", "-r", "-z", "--name-only", head_commit)
        return [
            normalized_path(item.decode("utf-8", errors="surrogateescape"))
            for item in output.split(b"\0")
            if item
        ]

    base_commit = commit(root, base, "--base")
    if merge_base:
        try:
            base_commit = (
                run_git(root, "merge-base", base_commit, head_commit).decode().strip()
            )
        except CheckError as error:
            raise CheckError(
                "cannot find a merge base for --base and --head"
            ) from error
    output = run_git(
        root, "diff", "--name-status", "-z", "-M", base_commit, head_commit
    )
    values = [
        item.decode("utf-8", errors="surrogateescape")
        for item in output.split(b"\0")
        if item
    ]
    paths: list[PurePosixPath] = []
    index = 0
    while index < len(values):
        status = values[index]
        index += 1
        if status.startswith("D"):
            index += 1
            continue
        if status.startswith(("R", "C")):
            if index + 1 >= len(values):
                raise CheckError("git returned an incomplete rename or copy record")
            index += 1  # previous path is not the current authored source.
            paths.append(normalized_path(values[index]))
            index += 1
            continue
        if index >= len(values):
            raise CheckError("git returned an incomplete changed-path record")
        paths.append(normalized_path(values[index]))
        index += 1
    return paths


def strip_front_matter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            return "\n".join(lines[index + 1 :])
    return text


def is_structural_json(content: str) -> bool:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return False

    entries = value if isinstance(value, list) else [value]
    if not entries or not all(isinstance(entry, dict) for entry in entries):
        return False
    for entry in entries:
        keys = {re.sub(r"[^a-z]", "", str(key).lower()) for key in entry}
        if "agenthostcoverage" in keys or "agenthostcompletion" in keys:
            continue
        if "schemaversion" in keys and keys.intersection(
            {
                "sharedsource",
                "candidatehead",
                "hosts",
                "agents",
                "coverage",
                "completion",
            }
        ):
            continue
        return False
    return True


def has_meaningful_content(content: str) -> bool:
    lines = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line in {"*/", "-->"}:
            continue
        if line.startswith("//"):
            line = line[2:].strip()
        elif line.startswith("/*"):
            line = line[2:].removesuffix("*/").strip(" *")
        elif line.startswith("<!--"):
            line = line[4:].removesuffix("-->").strip()
        elif line.startswith("*") or (
            line.startswith("#") and not line.startswith("#include")
        ):
            line = line[1:].strip()
        if not line:
            continue
        lines.append(line)
    return bool(lines) and not all(PLACEHOLDERS.fullmatch(line) for line in lines)


def has_concrete_example(text: str) -> bool:
    lines = strip_front_matter(text).splitlines()
    index = 0
    while index < len(lines):
        opening = OPENING_FENCE.match(lines[index])
        if not opening:
            index += 1
            continue
        prefix = "\n".join(lines[:index])
        if prefix.rfind("<!--") > prefix.rfind("-->"):
            index += 1
            continue
        fence = opening.group(1)
        info = opening.group(2).strip().lower()
        marker, width = fence[0], len(fence)
        content: list[str] = []
        index += 1
        close = re.compile(rf"^[ ]{{0,3}}{re.escape(marker)}{{{width},}}[ \t]*$")
        while index < len(lines) and not close.match(lines[index]):
            content.append(lines[index])
            index += 1
        if index < len(lines):
            candidate = "\n".join(content).strip()
            tags = set(re.findall(r"[a-z]+(?:-[a-z]+)*", info))
            if (
                not tags.intersection(METADATA_FENCE_TAGS)
                and has_meaningful_content(candidate)
                and not is_structural_json(candidate)
            ):
                return True
        index += 1
    return False


def committed_text(root: Path, head: str, path: PurePosixPath) -> str:
    try:
        return run_git(root, "show", f"{head}:{path.as_posix()}").decode("utf-8")
    except (CheckError, UnicodeDecodeError) as error:
        raise CheckError(
            f"cannot read '{path}' from committed head '{head}'"
        ) from error


def working_text(root: Path, path: PurePosixPath) -> str:
    target = root.joinpath(*path.parts)
    try:
        resolved = target.resolve(strict=True)
    except FileNotFoundError as error:
        raise CheckError(f"path '{path}' does not exist") from error
    if root not in resolved.parents and resolved != root:
        raise CheckError(f"path '{path}' resolves outside --root")
    if not resolved.is_file():
        raise CheckError(f"path '{path}' is not a file")
    try:
        return resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise CheckError(f"path '{path}' is not UTF-8 text") from error


def parse_arguments(arguments: Iterable[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--merge-base", action="store_true")
    parser.add_argument("--path", action="append", default=[])
    values = parser.parse_args(arguments)
    if not values.path and not values.base:
        parser.error("--base is required unless one or more --path values are supplied")
    return values


def main(arguments: Iterable[str] | None = None) -> int:
    values = parse_arguments(arguments)
    root = values.root.resolve()
    if not root.is_dir():
        print(
            f"check_examples: --root '{values.root}' is not a directory",
            file=sys.stderr,
        )
        return 1

    try:
        if values.path:
            candidates = [normalized_path(raw) for raw in values.path]

            def source(path: PurePosixPath) -> str:
                return working_text(root, path)
        else:
            head = commit(root, values.head, "--head")
            candidates = changed_paths(root, values.base, head, values.merge_base)

            def source(path: PurePosixPath) -> str:
                return committed_text(root, head, path)

        guidance = sorted(
            {path for path in candidates if is_authored_guidance(path)}, key=str
        )
        if values.path:
            non_guidance = [
                path for path in candidates if not is_explicit_guidance(path)
            ]
            if non_guidance:
                raise CheckError(
                    f"path '{non_guidance[0]}' is not canonical authored guidance"
                )
            guidance = sorted(set(candidates), key=str)

        failures = [path for path in guidance if not has_concrete_example(source(path))]
    except CheckError as error:
        print(f"check_examples: {error}", file=sys.stderr)
        return 1

    for path in failures:
        print(
            f"check_examples: {path}: add a concrete non-placeholder fenced example",
            file=sys.stderr,
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
