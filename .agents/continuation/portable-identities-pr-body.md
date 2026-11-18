## Why

Generated paths can collide on Windows or contain reserved names even when the source checkout works on another platform. Validate the complete output map before generation removes or writes files, while preserving distinct valid Unicode filenames.

## What

- Validate portable paths, file and implied-directory identities, and file/directory conflicts.
- Use the pinned Windows reference uppercase table and UTF-16 byte identities instead of Unicode full folding. The qualified baseline is Windows 26200.9448, DLL mapping 10.0.26100.9278; future native-table drift requires review.
- Cover distinct Unicode names with different contents, aliases, ancestors, supplementary/surrogate spellings, table integrity and native filesystem behavior.
- Release as 1.4.1 with coupled Kit and Codex Kit/Template metadata. The authored PR is 452 substantive lines plus 194 generator-mirror lines across eight files; generated outputs remain publisher-owned.

## Test plan

- [x] Exact committed clean source: 126 tests passed; focused generator suite: 64 tests passed.
- [x] Generated freshness: 219 files; canonical and root generator bytes match.
- [x] Copied Kit-only and Template-only create/check/drift/update/canonical workflows passed.
- [x] Exact head a6f73ff05627929181d2eb43cce68cfbbd3d5422 CI38245559736 attempt1: Windows/Linux repository tests and conformance, pinned Claude/Codex acceptance passed; main publisher skipped.
- [x] Frozen native and independent workflow incremental review completed; POI-1 resolved and current source review approved.

Stack base: Refactor/TemplatePublication (#9). Land through the normal parent stack; verify main generated publication before the release tag. Existing runtime-binding filename allowance remains in the separate 1.5 structural slice.
