# Code review - Fix/PortableOutputIdentities

**Review status:** `complete`
**Reviewed up to commit:** `a6f73ff05627929181d2eb43cce68cfbbd3d5422` `(2026-10-12)`
**Security-reviewed up to commit:** `a6f73ff05627929181d2eb43cce68cfbbd3d5422`
**Judgment:** `approved`

## Review pass - 2026-10-12 - full

**Candidate base:** `d0b42f2382e477c48ee7d062005b1813d712bee6`
**Candidate head:** `7b6e4caefb205eb7e7bfa0894121c77c6eb334d6`
**Candidate branch:** `Fix/PortableOutputIdentities`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:ad732a6f1bf31e2243eea98713ee15b56802c0b7c39fc31778d3087a491ffbda` `(8 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\H3dqmQqgDdSL1X9Qc9MaIj\dlRozZMhgRGyTYHcgVwqeF\9nZa7LkQrYUQr7VsfPPrAI`
**Candidate bundle identity:** `sha256:d610fa2527a1430a58e90fad870ddc5eed00195675d0d24e064bafe458c6bc77`
**Work-order path:** `reviews/Fix-PortableOutputIdentities.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`
**Binary patch:** `sha256:3108b475b6e3f31f25d5efcb21d828fb5d224beca9c5b196fbcc6e45a09eec2c`
**Descriptor:** `C:\Users\TommySeery\source\repos\tj-agents\kit\.git\agent-workflow\runs\portable-output-identities\review\f6765aecb910ad8510afb56c7cf3eb008c623a2b3c3df72b663b829a354c48a8\descriptor.json`
**Descriptor identity:** `b29286e70d444225551a74648f0ee479827116d298bb5d76a82fc903a45b5781`
**Synchronization:** `{"base": "d0b42f2382e477c48ee7d062005b1813d712bee6", "base_ref": "origin/Refactor/TemplatePublication", "behind": 0, "head_after": "7b6e4caefb205eb7e7bfa0894121c77c6eb334d6", "head_before": "7b6e4caefb205eb7e7bfa0894121c77c6eb334d6"}`
**Routed technical rules:** none; tier gate resolves no applicable stack conventions.
**Selected lenses:** native-general, workflow; security covers cumulative trunk range.

### Findings

- [x] **POI-1 - MEDIUM - native-general** - `.agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in:92`
  Full Unicode casefold falsely merges distinct valid Windows output identities. `Stra\u00dfe.md` and `STRASSE.md` build at the parent but fail at this head; Root reproduced Windows ordinal inequality and two distinct temporary files. The same over-rejection occurs for sharp-s/capital-sharp-s and ordinary/final sigma controls. Replace full folding with a qualified portable identity comparison that preserves these valid pairs while rejecting actual Windows aliases; synchronize the canonical and vendored generator and add regression tests. Native source evidence is retained under .agents/continuation/native-review-7b6e4ca.log; source correction awaits bounded design and independent qualification.


Native Codex review ran at the frozen head against exactd0 parent in a detached checkout and exited0; Root confirmed POI-1 through ordinal and filesystem probes. Disposable native checkout removed after clean/HEAD verification. Fresh Workflowv2 dispatch identity-full-7b6e4ca-workflow completed with matching immutable identities and no claims. Fresh cumulative security dispatch identity-full-7b6e4ca-security completed over28b551300c54061801b2c68b2b5fecd5efd7bbc1..7b6e4caefb205eb7e7bfa0894121c77c6eb334d6, no claims, thirteen invalid-map negatives and source/publication boundary probes exit0. Parent validated result fields, status, scope, artifact identities, citations and acceptance boundaries; POI-1 is the sole retained MEDIUM defect.

Security bundle identity:7fda3f8f277fdd5ddc4b5fc3420bf0b74806d692ab421ab732474051a10e9a5f; patch864993e55cee9a0c9dfef453f8f2771b7a8c4c492969646078edb2517e384924; pathsete159986134bb3b4a9a71ef30106447188095185b0810d50b9422522e5b4a5646. Security descriptor:shared Git agent-workflow/runs/portable-output-identities-security/review/f26d2a0e50d4d91201e4df59bfb59fe86443b7ce2fa940a39317643b97fd2775/descriptor.json. Installed review lifecycle snapshotSHA256c6fa6f0c584469c95188de7cc38fe8537bc87cb6001a3583f78356d88497c6ec recorded through workflow_ops skills.

## Agent host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "candidate_head": "a6f73ff05627929181d2eb43cce68cfbbd3d5422",
  "shared_source": ".agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Validate complete output file and implied-directory identities before either native output tree is removed or written.",
      "source": ".agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in",
      "mapping": "Canonical template and byte-identical root generator emit .claude/skills plus both independent Kit and Template publications.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Exact head a6f73ff05627929181d2eb43cce68cfbbd3d5422 CI38245559736 attempt1 passed Windows/Linux repository tests, conformance and pinned native host acceptance; publisher skipped. Exact stateless source126tests/38.827s, focused64tests/219freshness/canonical parity and copied workflows passed. Native incremental review independently regenerated a disposable source copy and passed126tests/54.238s; fresh workflow lens12identitytests/0.445s and no claims. Existing runtime binding reproduces two checkout-layout failures at unchanged7b6 and remains scoped to1.5. No installed-agent procedure execution claimed."
      }
    },
    {
      "host": "codex",
      "behavior": "Validate complete output file and implied-directory identities before either native output tree is removed or written.",
      "source": ".agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in",
      "mapping": "Canonical template and byte-identical root generator emit .codex/skills plus both independent Kit and Template publications.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Exact head a6f73ff05627929181d2eb43cce68cfbbd3d5422 CI38245559736 attempt1 passed Windows/Linux repository tests, conformance and pinned native host acceptance; publisher skipped. Exact stateless source126tests/38.827s, focused64tests/219freshness/canonical parity and copied workflows passed. Native incremental review independently regenerated a disposable source copy and passed126tests/54.238s; fresh workflow lens12identitytests/0.445s and no claims. Existing runtime binding reproduces two checkout-layout failures at unchanged7b6 and remains scoped to1.5. No installed-agent procedure execution claimed."
      }
    }
  ]
}
```

Parent synthesis: changes requested at the frozen head; one MEDIUM POI-1 requires serial repair and fresh incremental review. Exact-head CI is green; no other retained finding.

POI-1 remediation authorized after frozen proposal afd1bd0aea4a4902a2a7af11035a110a6740171586bf8ac1750e1d6af27a0833 independent L2/L4 qualification: pinned table/UTF-16 keys, shared and exact-publication drivers, all nine Cpp packages, native BMP and filesystem controls passed. One exclusive L4 source writer owns canonical template, root mirror and focused generator tests; original finding and full pass remain immutable.

## Review pass - 2026-10-12 - incremental

**Candidate base:** `7b6e4caefb205eb7e7bfa0894121c77c6eb334d6`
**Candidate head:** `a6f73ff05627929181d2eb43cce68cfbbd3d5422`
**Candidate branch:** `Fix/PortableOutputIdentities`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:a29256ee26e5ef44a58dcdf7bf67a5a98f24bd878c18a2f831b180f90045c9d8`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\H3dqmQqgDdSL1X9Qc9MaIj\dlRozZMhgRGyTYHcgVwqeF\2xpnUu73w_9_Bg4i2xv0K7`
**Candidate bundle identity:** `sha256:9a6ffd915ca15c440ce06b4df492030dda61832cec5e599898f78c1329d023af`
**Work-order path:** `reviews/Fix-PortableOutputIdentities.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`
**Binary patch:** `sha256:1e5b4a98b35986ac3b0e599df746ae0bba14466307540da9760393dfb6edea5e`
**Descriptor:** `C:\Users\TommySeery\source\repos\tj-agents\kit\.git\agent-workflow\runs\portable-output-identities\review\db1a6752eef7c3ff7f060e22db1bf42bb750afbe1691993e5cb12376a878cef7\descriptor.json`
**Descriptor identity:** `ddcfebe7fb8604e5f0e581ebdd4b3b1234ea8105ff1942600891f4133cf4fef7`
**Synchronization:** `{"base": "7b6e4caefb205eb7e7bfa0894121c77c6eb334d6", "base_ref": "7b6e4caefb205eb7e7bfa0894121c77c6eb334d6", "behind": 0, "head_after": "a6f73ff05627929181d2eb43cce68cfbbd3d5422", "head_before": "a6f73ff05627929181d2eb43cce68cfbbd3d5422"}`
**Routed technical rules:** none; installed tier gate confirms no applicable stack conventions.
**Selected lenses:** native-general, workflow.

### Findings

No new findings. Native Codex incremental review at exacta6 against7b6 exited0 with no actionable regressions; retained native-review-a6f73ff.log and .exit. Fresh Workflowv2 identity-incremental-a6f-workflow completed with matching candidate/patch/path/bundle identities and claims[]. Parent checked schema fields, frozen source citations, canonical parity, prewrite order, twelve focused tests and acceptance boundaries. Security-sensitive delta classification is empty; prior cumulative marker7b6 covers unchanged trunk security paths, carried through this delta. Original finding/text/full-pass judgment remain immutable.

POI-1 fix: a6f73ff05627929181d2eb43cce68cfbbd3d5422 copies the independently qualified pinned table and UTF-16 identity keys. Root verified all three identity-function ASTs and declarationSHA dab0575edcb5aa824c84dbdff349016687a105e999e396626c5a392f2de90923 against frozen proposal; canonical/root equalSHA e716dc49f29790d1c6f12e5f8af7e99972952b2f489d4582c14c16614ac5ec9d. Focused64tests/7.922s and219freshness passed. Exact committed stateless source export regenerated219 and passed126tests/38.827s; three candidate blobs byte-matched. Original checkout126 had two binding-filename conformance failures; unchanged7b6 export with same binding reproduced exactly those two among119tests. Prior CI38195004191 Windows/Linux repository-tests and conformance steps genuinely succeeded; binding is runtime checkout input and exact filename allowance stays in1.5. No check/test was weakened or binding moved. Writer stopped; native/workflow incremental review pending, push held. Cumulative PR diff452substantive+194mirror over eight authored paths; repair312substantive+146mirror.

Incremental evidence: CI38245559736 attempt1 genuinely executed Windows/Linux repository-tests/conformance and pinned-host acceptance successfully; publisher skipped. Remote origin/Fix/PortableOutputIdentities confirmed exacta6f73ff05627929181d2eb43cce68cfbbd3d5422 after stable push. Host-coverage validator passed at exacta6; parent completed incremental approval, original POI-1 resolved.
