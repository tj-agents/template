"""Run the consumer's locked generator from the reusable CI workflow."""

import argparse
from pathlib import Path

from tj_template.plugins.dependencies import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        return run(arguments.root.resolve(), check=arguments.check)
    except ValueError as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
