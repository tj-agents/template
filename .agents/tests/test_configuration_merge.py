import json
import os
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ATTRIBUTES = (
    ROOT / ".agents/template/utility/new/plugin/templates/repository/.gitattributes.in"
)
CONFIGS = (
    (
        ".codex/config.toml",
        'model = "base"\n',
        'model = "ours"\n',
        'model = "theirs"\n',
    ),
    (
        ".claude/settings.json",
        '{"permissionMode": "base"}\n',
        '{"permissionMode": "ours"}\n',
        '{"permissionMode": "theirs"}\n',
    ),
    (
        ".agents/plugins.json",
        '{"plugins": ["base"]}\n',
        '{"plugins": ["ours"]}\n',
        '{"plugins": ["theirs"]}\n',
    ),
)


def git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=environment,
        timeout=30,
    )


def run_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    result = git(repository, *arguments)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def write(repository: Path, relative: str, content: str) -> None:
    path = repository / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def commit(repository: Path, message: str) -> None:
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", message)


def make_repository(tmp_path: Path, relative: str, base: str) -> Path:
    repository = tmp_path / "merge safety é space"
    repository.mkdir()
    run_git(repository, "init", "--initial-branch=main")
    run_git(repository, "config", "user.name", "Configuration Test")
    run_git(repository, "config", "user.email", "configuration@example.com")
    run_git(repository, "config", "commit.gpgSign", "false")
    attributes = ATTRIBUTES.read_text(encoding="utf-8")
    write(repository, ".gitattributes", attributes)
    write(repository, relative, base)
    commit(repository, "base")
    return repository


def conflict_contents(repository: Path, relative: str) -> dict[int, str]:
    return {
        stage: run_git(repository, "show", f":{stage}:{relative}").stdout
        for stage in (1, 2, 3)
    }


def parse(relative: str, content: str) -> object:
    if relative.endswith(".toml"):
        return tomllib.loads(content)
    return json.loads(content)


def assert_conflict(
    repository: Path,
    relative: str,
    base: str,
    ours: str,
    theirs: str,
    result: subprocess.CompletedProcess[str],
) -> None:
    assert result.returncode != 0
    assert "CONFLICT" in result.stdout + result.stderr
    current = (repository / relative).read_text(encoding="utf-8")
    assert current == ours
    assert parse(relative, current) == parse(relative, ours)
    assert conflict_contents(repository, relative) == {1: base, 2: ours, 3: theirs}
    assert f"UU {relative}" in run_git(repository, "status", "--porcelain").stdout


def merge_conflict(
    repository: Path, relative: str, ours: str, theirs: str
) -> subprocess.CompletedProcess[str]:
    run_git(repository, "switch", "-c", "theirs")
    write(repository, relative, theirs)
    commit(repository, "theirs")
    run_git(repository, "switch", "main")
    write(repository, relative, ours)
    commit(repository, "ours")
    return git(repository, "merge", "theirs", "--no-edit")


def cherry_pick_conflict(
    repository: Path, relative: str, ours: str, theirs: str
) -> subprocess.CompletedProcess[str]:
    run_git(repository, "switch", "-c", "theirs")
    write(repository, relative, theirs)
    commit(repository, "theirs")
    revision = run_git(repository, "rev-parse", "HEAD").stdout.strip()
    run_git(repository, "switch", "main")
    write(repository, relative, ours)
    commit(repository, "ours")
    return git(repository, "cherry-pick", revision)


def stash_conflict(
    repository: Path, relative: str, ours: str, theirs: str, pop: bool
) -> subprocess.CompletedProcess[str]:
    write(repository, relative, theirs)
    run_git(repository, "stash", "push", "-m", "theirs")
    write(repository, relative, ours)
    commit(repository, "ours")
    return git(repository, "stash", "pop" if pop else "apply")


@pytest.mark.parametrize(("relative", "base", "ours", "theirs"), CONFIGS)
@pytest.mark.parametrize(
    "operation", ("merge", "cherry-pick", "stash apply", "stash pop")
)
def test_conflicting_configuration_edits_keep_ours_and_leave_all_index_stages(
    tmp_path: Path,
    relative: str,
    base: str,
    ours: str,
    theirs: str,
    operation: str,
) -> None:
    repository = make_repository(tmp_path, relative, base)
    if operation == "merge":
        result = merge_conflict(repository, relative, ours, theirs)
    elif operation == "cherry-pick":
        result = cherry_pick_conflict(repository, relative, ours, theirs)
    else:
        result = stash_conflict(
            repository, relative, ours, theirs, operation == "stash pop"
        )
    assert_conflict(repository, relative, base, ours, theirs, result)


@pytest.mark.parametrize(("relative", "base", "_ours", "theirs"), CONFIGS)
@pytest.mark.parametrize("operation", ("merge", "stash apply", "stash pop"))
def test_one_sided_configuration_edits_apply_normally(
    tmp_path: Path,
    relative: str,
    base: str,
    _ours: str,
    theirs: str,
    operation: str,
) -> None:
    repository = make_repository(tmp_path, relative, base)
    if operation == "merge":
        run_git(repository, "switch", "-c", "theirs")
        write(repository, relative, theirs)
        commit(repository, "theirs")
        run_git(repository, "switch", "main")
        write(repository, "note.txt", "main\n")
        commit(repository, "main")
        result = git(repository, "merge", "theirs", "--no-edit")
    else:
        write(repository, relative, theirs)
        run_git(repository, "stash", "push", "-m", "theirs")
        result = git(
            repository, "stash", "pop" if operation == "stash pop" else "apply"
        )
    assert result.returncode == 0, result.stdout + result.stderr
    current = (repository / relative).read_text(encoding="utf-8")
    assert current == theirs
    assert parse(relative, current) == parse(relative, theirs)
    assert run_git(repository, "ls-files", "-u").stdout == ""
