import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "skill_references",
    ROOT / ".agents/template/utility/check/scripts/check_skill_references.py",
)
assert SPEC is not None
assert SPEC.loader is not None
checker: Any = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def write(root: Path, name: str, body: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def skill(root: Path, plugin: str, name: str, body: str = "") -> Path:
    write(root, f"plugins/{plugin}/skills/{name}/SKILL.md", "published")
    return write(root, f".agents/{plugin}/utility/{name}/SKILL.md", body)


def test_old_clip_description_detects_both_missing_ask_skills(tmp_path: Path) -> None:
    skill(
        tmp_path,
        "machine",
        "clip",
        "---\ndescription: Used by Teams-message skills (`ask-the-team`, "
        "`ask-infra`).\n---",
    )
    problems = checker.check([tmp_path])
    assert len(problems) == 2
    assert any(":2: missing skill ask-the-team" in item for item in problems)
    assert any(":2: missing skill ask-infra" in item for item in problems)


def test_namespaces_aliases_and_unknown_explicit_namespace(tmp_path: Path) -> None:
    skill(
        tmp_path,
        "work",
        "ask-person",
        "Load work:ask-person and the `wrong:ask-person` skill; skip `work:*` "
        "and `plugin:skill`.",
    )
    write(tmp_path, "plugins/work/skills/message-person/SKILL.md", "alias")
    write(tmp_path, "README.md", "Load `work:message-person`.")
    assert len(checker.check([tmp_path])) == 1
    assert "missing skill wrong:ask-person" in checker.check([tmp_path])[0]


def test_bare_resolves_locally_then_uniquely_and_reports_ambiguity(
    tmp_path: Path,
) -> None:
    skill(tmp_path, "one", "shared", "The `shared` skill pairs with skill `unique`.")
    skill(tmp_path, "two", "shared")
    skill(tmp_path, "two", "unique")
    assert checker.check([tmp_path]) == []
    write(tmp_path, "AGENTS.md", "Use the `shared` skill.")
    assert (
        "ambiguous skill shared: one:shared, two:shared" in checker.check([tmp_path])[0]
    )


def test_history_adapters_fixtures_templates_and_non_skill_identifiers_are_not_scanned(
    tmp_path: Path,
) -> None:
    skill(
        tmp_path,
        "one",
        "real",
        "Use `file-path`, https://host:123, and `namespace:skill`. ",
    )
    for name in (
        "plans/old.md",
        ".codex/skills/old/SKILL.md",
        ".agents/tests/fixtures/old/SKILL.md",
        ".agents/one/utility/real/templates/old/SKILL.md.in",
    ):
        write(tmp_path, name, "Use `one:missing`.")
    assert checker.check([tmp_path]) == []


def test_unknown_namespace_requires_skill_context_not_oauth_scope(
    tmp_path: Path,
) -> None:
    skill(
        tmp_path,
        "one",
        "real",
        "Use OAuth `admin:org`, plus `/unknown:invoke` and skills (`unknown:list`).",
    )
    problems = checker.check([tmp_path])
    assert len(problems) == 2
    assert any("unknown:invoke" in item for item in problems)
    assert any("unknown:list" in item for item in problems)


def test_source_roots_use_sibling_inventory_without_scanning_sibling_body(
    tmp_path: Path,
) -> None:
    sibling = tmp_path / "sibling"
    skill(tmp_path, "one", "real", "Use `two:legacy`.")
    path = sibling / "plugins/two/skills/legacy/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("Use `two:missing`.", encoding="utf-8")
    assert checker.check([tmp_path, sibling], source_roots=[tmp_path]) == []


def test_a_kind_skill_is_prose_but_a_requested_named_skill_is_checked(
    tmp_path: Path,
) -> None:
    skill(
        tmp_path,
        "one",
        "real",
        "A `contract` skill gains a rule. An `utility` skill runs scripts.",
    )
    assert checker.check([tmp_path]) == []
    write(tmp_path, "README.md", "Load the `contract` skill.")
    assert "missing skill contract" in checker.check([tmp_path])[0]


@pytest.mark.parametrize(
    "body",
    [
        "Use the `real` and `missing` skills.",
        "Use the `real`, `missing`, and `another-missing` skills.",
        "Use skills `real` or `missing`.",
        "Use skills: `real`, `missing`.",
    ],
)
def test_ordinary_plural_skill_lists_resolve_every_name(
    tmp_path: Path, body: str
) -> None:
    skill(tmp_path, "one", "real")
    write(tmp_path, "README.md", body)
    problems = checker.check([tmp_path])
    assert len(problems) == (2 if "another-missing" in body else 1)
    assert any("missing skill missing" in item for item in problems)


def test_ordinary_plural_skill_lists_resolve_qualified_and_builtin_names(
    tmp_path: Path,
) -> None:
    skill(tmp_path, "one", "real")
    write(tmp_path, "README.md", "Use the `one:real` and `unknown:missing` skills.")
    assert "missing skill unknown:missing" in checker.check([tmp_path])[0]
    write(tmp_path, "README.md", "The `file` and `directory` values control output.")
    assert checker.check([tmp_path]) == []


def test_concrete_hyphenated_names_are_not_illustrative_placeholders(
    tmp_path: Path,
) -> None:
    skill(tmp_path, "sample", "real")
    write(
        tmp_path,
        "README.md",
        "Use `sample:nonexistent-plugin` and skills (`missing-plugin`).",
    )
    problems = checker.check([tmp_path])
    assert len(problems) == 2
    assert any("missing skill sample:nonexistent-plugin" in item for item in problems)
    assert any("missing skill missing-plugin" in item for item in problems)
    write(
        tmp_path,
        "README.md",
        "Examples: `plugin:skill`, `namespace:skill`, `your-plugin:your-skill`, "
        "`sample:*`, and skills (`<skill-name>`).",
    )
    assert checker.check([tmp_path]) == []


def test_multiple_roots_and_legacy_payload_body(tmp_path: Path) -> None:
    sibling = tmp_path / "sibling"
    skill(tmp_path, "one", "real", "Use `two:legacy`.")
    path = sibling / "plugins/two/skills/legacy/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("Use `one:real`.", encoding="utf-8")
    assert checker.check([tmp_path, sibling]) == []
    path.write_text("Use `two:missing`.", encoding="utf-8")
    assert "missing skill two:missing" in checker.check([tmp_path, sibling])[0]


def test_exact_external_declaration_needs_rationale_and_rejects_wildcard(
    tmp_path: Path,
) -> None:
    skill(tmp_path, "one", "real", "Load `outside:exact`.")
    config = write(
        tmp_path,
        "references.json",
        json.dumps(
            {
                "external_skills": {
                    "outside:exact": "Owned by a separate project repository."
                }
            }
        ),
    )
    assert checker.check([tmp_path], [config]) == []
    config.write_text(
        json.dumps({"external_skills": {"outside:*": "anything"}}), encoding="utf-8"
    )
    assert any(
        "exact namespace:skill" in item for item in checker.check([tmp_path], [config])
    )
