# Template

Template creates plugin repositories and owns the parts they share: the layout, the generator, the root files and CI.
It is itself a plugin repository in that layout, with every skill of kind `utility` under `.agents/template/utility/<name>/`.

The files a plugin repository vendors have one source, under `.agents/template/utility/new-plugin/templates/repository/`.
Template's own copies of `.agents/sync_generated.py`, `.agents/sync-generated.ps1`, `.gitattributes`, `.gitignore` and
`CLAUDE.md` must stay byte-identical to those templates; the tests enforce it. Change the template first.
`template:check` and `template:update` read those templates and `template:check`'s `standard.json`, the one statement of what each
repository type requires.

Template plugin CI runs from the main branch. Plugin repositories follow main and run template:update to refresh the exact
vendored content; Template changes do not require version bumps or tags.

`.codex/skills/`, `.claude/skills/`, `.agents/INDEX.md`, both marketplace files and `plugins/*` are generated. Run
`pwsh .agents/sync-generated.ps1` after authored changes; `pwsh .agents/sync-generated.ps1 -Check` and
`python -B -m unittest discover -s .agents/tests -p "test_*.py"` must pass before delivery.
