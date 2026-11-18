# Disposable Work packaging-test preparation

Base: work `3b021cab6943a422870772de88266b9323d494d9`
Producer: Template `d0b42f2382e477c48ee7d062005b1813d712bee6`, generated from frozen source before the temporary update.

A fresh base archive passed the original suite: 5 tests, exit 0. It ships full package procedure copies. The generated Template 1.4.0 update replaces those package copies with thin entries that reference physically shipped `.agents/work/utility/<skill>/SKILL.md` definitions.

Prepared patch: `work-template-1.4.0-packaging-test.patch`. It changes the package assertion to resolve each canonical link, assert the target is a file, and compare exact authored bytes for package, Claude, and Codex entries. It adds one negative test that substitutes a missing package target and asserts the shipped-target check fails.

Validation in the updated temporary export:

```text
python -B -m unittest discover -s .agents/tests -p "test_*.py"
Ran 6 tests in 0.036s
OK
```

No original Work checkout, branch, commit, generated production file, or remote was changed. This is owner-review preparation only; apply it after the released producer migration is authorized.

## Patch refinement: package containment

The package-target helper now applies a package-specific containment rule: for `plugins/work/skills` entries, the resolved canonical target must remain under resolved `plugins/work` before the physical-file and byte-equality checks. Claude and Codex entries retain their existing authored-root resolution behavior.

The temporary suite adds a redirect negative: a package entry changed to `../../../.agents/work/utility/ask/SKILL.md` points to an existing root-authored file, but fails because it is not physically shipped in `plugins/work`. The existing missing-target negative remains.

Validation after refinement:

```text
python -B -m unittest discover -s .agents/tests -p "test_*.py"
Ran 7 tests in 0.052s
OK
```

`work-template-1.4.0-packaging-test.patch` now has apply-ready relative headers:

```text
diff --git a/.agents/tests/test_packaging.py b/.agents/tests/test_packaging.py
--- a/.agents/tests/test_packaging.py
+++ b/.agents/tests/test_packaging.py
```

Final redirect correction: the temporary test computes the redirect with `os.path.relpath(ROOT / ".agents/work/utility/ask/SKILL.md", path.parent).replace("\\", "/")`. In this exact fixture it resolves to the existing authored `ROOT/.agents/work/utility/ask/SKILL.md`, confirmed with `is_file()` before `canonical_bytes` rejects it for escaping `ROOT/plugins/work`. The final disposable test run passed all seven tests.