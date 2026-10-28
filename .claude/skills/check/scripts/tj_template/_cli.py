"""Installed command for plugin generation and generated-file verification."""

import argparse
from pathlib import Path

from tj_template.plugins.generation import synchronize


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command, description in (
        ("generate", "Build plugin payloads and host discovery files."),
        ("check", "Verify generated files without changing them."),
    ):
        command_parser = commands.add_parser(command, help=description)
        command_parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    try:
        return synchronize(arguments.root.resolve(), arguments.command == "check")
    except ValueError as error:
        print(f"error: {error}")
        return 2
