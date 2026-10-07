from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("skill_references", ROOT / ".agents/kit/utility/check/scripts/check_skill_references.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class SkillReferenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def write(self, name, body):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def skill(self, plugin, name, body=""):
        self.write(f"plugins/{plugin}/skills/{name}/SKILL.md", "published")
        return self.write(f".agents/{plugin}/utility/{name}/SKILL.md", body)

    def test_old_clip_description_detects_both_missing_ask_skills(self):
        self.skill("machine", "clip", "---\ndescription: Used by Teams-message skills (`ask-the-team`, `ask-infra`).\n---")
        problems = checker.check([self.root])
        self.assertEqual(2, len(problems))
        self.assertTrue(any(":2: missing skill ask-the-team" in item for item in problems))
        self.assertTrue(any(":2: missing skill ask-infra" in item for item in problems))

    def test_namespaces_aliases_and_unknown_explicit_namespace(self):
        self.skill("work", "ask-person", "Load work:ask-person and the `wrong:ask-person` skill; skip `work:*` and `plugin:skill`.")
        self.write("plugins/work/skills/message-person/SKILL.md", "alias")
        self.write("README.md", "Load `work:message-person`.")
        self.assertEqual(1, len(checker.check([self.root])))
        self.assertIn("missing skill wrong:ask-person", checker.check([self.root])[0])

    def test_bare_resolves_locally_then_uniquely_and_reports_ambiguity(self):
        self.skill("one", "shared", "The `shared` skill pairs with skill `unique`.")
        self.skill("two", "shared")
        self.skill("two", "unique")
        self.assertEqual([], checker.check([self.root]))
        self.write("AGENTS.md", "Use the `shared` skill.")
        self.assertIn("ambiguous skill shared: one:shared, two:shared", checker.check([self.root])[0])

    def test_history_adapters_fixtures_templates_and_non_skill_identifiers_are_not_scanned(self):
        self.skill("one", "real", "Use `file-path`, https://host:123, and `namespace:skill`. ")
        for name in ("plans/old.md", ".codex/skills/old/SKILL.md", ".agents/tests/fixtures/old/SKILL.md", ".agents/one/utility/real/templates/old/SKILL.md.in"):
            self.write(name, "Use `one:missing`.")
        self.assertEqual([], checker.check([self.root]))

    def test_unknown_namespace_requires_skill_context_not_oauth_scope(self):
        self.skill("one", "real", "Use OAuth `admin:org`, plus `/unknown:invoke` and skills (`unknown:list`).")
        problems = checker.check([self.root])
        self.assertEqual(2, len(problems))
        self.assertTrue(any("unknown:invoke" in item for item in problems))
        self.assertTrue(any("unknown:list" in item for item in problems))

    def test_source_roots_use_sibling_inventory_without_scanning_sibling_body(self):
        sibling = self.root / "sibling"
        self.skill("one", "real", "Use `two:legacy`.")
        path = sibling / "plugins/two/skills/legacy/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("Use `two:missing`.", encoding="utf-8")
        self.assertEqual([], checker.check([self.root, sibling], source_roots=[self.root]))

    def test_a_kind_skill_is_prose_but_a_requested_named_skill_is_checked(self):
        self.skill("one", "real", "A `contract` skill gains a rule. An `utility` skill runs scripts.")
        self.assertEqual([], checker.check([self.root]))
        self.write("README.md", "Load the `contract` skill.")
        self.assertIn("missing skill contract", checker.check([self.root])[0])

    def test_multiple_roots_and_legacy_payload_body(self):
        sibling = self.root / "sibling"
        self.skill("one", "real", "Use `two:legacy`.")
        path = sibling / "plugins/two/skills/legacy/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("Use `one:real`.", encoding="utf-8")
        self.assertEqual([], checker.check([self.root, sibling]))
        path.write_text("Use `two:missing`.", encoding="utf-8")
        self.assertIn("missing skill two:missing", checker.check([self.root, sibling])[0])

    def test_exact_external_declaration_needs_rationale_and_rejects_wildcard(self):
        self.skill("one", "real", "Load `outside:exact`.")
        config = self.write("references.json", json.dumps({"external_skills": {"outside:exact": "Owned by a separate project repository."}}))
        self.assertEqual([], checker.check([self.root], [config]))
        config.write_text(json.dumps({"external_skills": {"outside:*": "anything"}}), encoding="utf-8")
        self.assertTrue(any("exact namespace:skill" in item for item in checker.check([self.root], [config])))


if __name__ == "__main__":
    unittest.main()
