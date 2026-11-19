"""Real immutable Git dependency for generator-upgrade integration tests."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def template_source(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[str, dict[str, str]]:
    producer = tmp_path_factory.mktemp("template-source")
    package = producer / "packages/tj-template"
    shutil.copytree(
        ROOT / "packages/tj-template",
        package,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "dist"),
    )
    generator = package / "src/tj_template/plugins/generation.py"
    body = generator.read_text(encoding="utf-8")
    signature = "def synchronize(root: Path, check: bool) -> int:\n"
    assert body.count(signature) == 1
    generator.write_text(
        body.replace(
            signature,
            signature + "    if not check:\n"
            '        (root / "selected-generator.txt").write_text(\n'
            '            "selected Git source", encoding="utf-8")\n',
        ),
        encoding="utf-8",
        newline="\n",
    )

    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", "-C", str(producer), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Template fixture")
    git("config", "user.email", "template@example.invalid")
    git("add", "packages")
    git("-c", "commit.gpgsign=false", "commit", "-qm", "fixture generator")
    revision = git("rev-parse", "HEAD")
    environment = dict(os.environ)
    count = int(environment.get("GIT_CONFIG_COUNT", "0"))
    # Append exact URL rewrites in child environments only. Preserve existing
    # scoped credentials and never modify the user's Git configuration files.
    for offset, suffix in enumerate(("", ".git")):
        environment[f"GIT_CONFIG_KEY_{count + offset}"] = (
            f"url.{producer.as_uri()}.insteadOf"
        )
        environment[f"GIT_CONFIG_VALUE_{count + offset}"] = (
            "https://github.com/tj-agents/template" + suffix
        )
    environment["GIT_CONFIG_COUNT"] = str(count + 2)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    return revision, environment
