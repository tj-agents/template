import argparse
import itertools
import json
import sys
from collections.abc import Iterator
from pathlib import Path

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode


def members(node: Node | None) -> Iterator[tuple[str, Node]]:
    if isinstance(node, MappingNode):
        for key, value in node.value:
            if isinstance(key, ScalarNode):
                yield key.value, value


def member(node: Node | None, key: str) -> Node | None:
    return next((value for name, value in members(node) if name == key), None)


def scalar(node: Node | None) -> str:
    return node.value if isinstance(node, ScalarNode) else ""


def declared_contexts(value: object) -> set[str]:
    if isinstance(value, list):
        return set().union(*(declared_contexts(item) for item in value))
    if not isinstance(value, dict):
        return set()
    if value.get("type") == "required_status_checks":
        parameters = value.get("parameters", {})
        if not isinstance(parameters, dict):
            raise ValueError("required_status_checks parameters must be an object")
        checks = parameters.get("required_status_checks", [])
        if not isinstance(checks, list):
            raise ValueError("required_status_checks must be a list")
        return {
            item["context"]
            for item in checks
            if isinstance(item, dict)
            and isinstance(item.get("context"), str)
            and item["context"].startswith("verify / ")
        }
    return set().union(*(declared_contexts(item) for item in value.values()))


def reported_contexts(root: Path) -> set[str]:
    caller = yaml.compose((root / ".github/workflows/ci.yml").read_text("utf-8"))
    prefixes = {
        scalar(member(job, "name")) or name
        for name, job in members(member(caller, "jobs"))
        if scalar(member(job, "uses")) == "./.github/workflows/plugin-ci.yml"
    }
    workflow = yaml.compose(
        (root / ".github/workflows/plugin-ci.yml").read_text("utf-8")
    )
    contexts: set[str] = set()
    for job_id, job in members(member(workflow, "jobs")):
        name = scalar(member(job, "name")) or job_id
        matrix = member(member(job, "strategy"), "matrix")
        suffixes = [""]
        if matrix is not None:
            axes = []
            for axis, values in members(matrix):
                if axis in {"include", "exclude"} or not isinstance(
                    values, SequenceNode
                ):
                    raise ValueError(
                        f"cannot resolve required-check matrix for {job_id}"
                    )
                axes.append([scalar(value) for value in values.value])
            suffixes = [f" ({', '.join(row)})" for row in itertools.product(*axes)]
        contexts.update(
            f"{prefix} / {name}{suffix}" for prefix in prefixes for suffix in suffixes
        )
    return contexts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--configuration", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        configuration: object = json.loads(arguments.configuration.read_text("utf-8"))
        required = declared_contexts(configuration)
        if not required:
            raise ValueError(
                "configuration declares no shared verify / required checks"
            )
        missing = required - reported_contexts(arguments.root)
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(error, file=sys.stderr)
        return 1
    if missing:
        print(
            "Missing required check contexts: " + ", ".join(sorted(missing)),
            file=sys.stderr,
        )
        return 1
    print("Required check contexts preserved: " + ", ".join(sorted(required)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
