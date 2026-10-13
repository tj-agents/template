# Template

Template creates plugin repositories and owns the parts they share: the layout, the generator, the root files and CI.
It is itself a plugin repository in that layout, with every skill of kind `utility` under `.agents/kit/utility/<name>/`.

The files a plugin repository vendors have one source, under `.agents/kit/utility/new-plugin/templates/repository/`.
Template's own copies of `.agents/sync_generated.py`, `.agents/sync-generated.ps1`, `.gitattributes`, `.gitignore` and
`CLAUDE.md` must stay byte-identical to those templates; the tests enforce it. Change the template first.
`template:check` and `template:update` read those templates and `template:check`'s `standard.json`, the one statement of what each
repository type requires.

`.github/workflows/plugin-ci.yml` is the CI every plugin repository calls, pinned to a Template release tag. Changing the
generator, a vendored file or the workflow is a Template release: bump `KIT_VERSION`, `.agents/plugins/kit.json` and the
Codex manifest version together, then tag `v<version>` after the merge.

`.codex/skills/`, `.claude/skills/`, `.agents/INDEX.md`, both marketplace files and `plugins/*` are generated. Run
`pwsh .agents/sync-generated.ps1` after authored changes; `pwsh .agents/sync-generated.ps1 -Check` and
`python -B -m unittest discover -s .agents/tests -p "test_*.py"` must pass before delivery.
