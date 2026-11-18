# Regenerated Template 1.4.0 consumer compatibility probe

Producer: d0b42f2382e477c48ee7d062005b1813d712bee6
Producer materialization: `git archive d0b42f2382e477c48ee7d062005b1813d712bee6`, extracted to a temporary root, followed by `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/sync-generated.ps1` and `-Check`.
Producer result: 219 generated files; Kit and Template packaged `new-plugin/templates/repository/.agents/sync_generated.py.in` byte-match the canonical template and declare `KIT_VERSION = "1.4.0"`.
Consumer exports: C:\Users\TOMMYS~1\AppData\Local\Temp\kit-consumer-compat-verified-ebcef3ee4d4148efaadc0a12ad081a4b

Each consumer was a read-only `git archive` export of the recorded main SHA. The generated producer package's `plugins/kit/skills/update/scripts/update.py` updated the temporary export. Every update, `.agents/sync-generated.ps1 -Check`, packaged `kit:check`, and packaged update `--dry-run` exited 0. All resulting pins and reusable CI references were `1.4.0`; old public identities remained present and authored manifest hashes were unchanged.

| Consumer | Base | Generation | Tests | Result |
|---|---|---:|---|---|
| react | d746b647d0d9f4ceb38838d61bac2ba161d4a01b | 129 files | 5 passed | compatible |
| dotnet | dd937097b7a2e489fc0986119af1ca5320e74fa7 | 189 files | 16 passed, 2 skipped | compatible |
| rust | 579f95d539215d493c1f20ea8372343a7a16bde5 | 101 files | 10 passed | compatible |
| nvim | 66b3e431bb0b51591442b13cb8d2f7147238eed4 | 21 files | 0 discovered, exit 3 | blocked: no existing test framework/files or CI test step found |
| work | 3b021cab6943a422870772de88266b9323d494d9 | 37 files | 5 run, 1 failed | blocked: `.agents/tests/test_packaging.py:56` requires `plugins/work/skills/*/SKILL.md` to byte-equal the authored procedure; generated output is now a thin entry that links to `.agents/work/utility/<skill>/SKILL.md` |

Work failure evidence: `plugins/work/skills/ask/SKILL.md` contains the generated canonical-definition link. `.agents/tests/test_packaging.py:58-59` already validates that thin-entry shape for Claude and Codex, but line 56 retains the obsolete package-copy equality assertion.

No original consumer checkout, branch, commit, or remote was changed. No native machine installation was performed.

## Follow-up: Work baseline and nvim declared CI

A fresh read-only archive of Work base `3b021cab6943a422870772de88266b9323d494d9` ran `.agents/tests` with 5 discovered tests and exit 0. Before update, `plugins/work/skills/ask/SKILL.md` byte-equaled `.agents/work/utility/ask/SKILL.md` and contained no canonical-definition link. After the generated Template 1.4.0 update, the package entry contains that link and resolves to the unchanged authored definition. The update trigger is the generated output representation, not changed Work authored content.

Required consumer correction: Work owner should update `.agents/tests/test_packaging.py:56` to validate package thin entries by resolving their canonical links, as lines 58-59 already do for Claude and Codex. No producer or consumer repair was made here.

Nvim's declared CI calls reusable `plugin-ci.yml`. Its repository-tests step is conditional on `Test-Path .agents/tests/test_*.py`; the exact updated nvim export has no matching path, so CI would skip that step. Completed applicable disposable checks: packaged update exit 0, generation freshness exit 0, packaged canonical check exit 0, packaged update dry-run exit 0, pin/workflow identity checks exit 0. The standalone discovery exit 3 records an absent suite, but is not a declared-CI compatibility failure. Public-corpus, Core tier-payload, and native host checks were not run in this no-install disposable probe.
