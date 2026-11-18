# Template 1.4.0 consumer compatibility probe

Producer: d0b42f2382e477c48ee7d062005b1813d712bee6
Expected version: 1.4.0
Temporary exports: C:\Users\TOMMYS~1\AppData\Local\Temp\kit-consumer-compat-52befc0ccb7f4ba598a09e498d0cbcde

Failure: the producer package's `kit:update` resolves version 1.2.2. `plugins/kit/skills/new-plugin/templates/repository/.agents/sync_generated.py.in` contains `KIT_VERSION = "1.2.2"`. Packaged `new_plugin.py` derives `kit_version()` from that template, and packaged `update.py` writes that result to `.agents/plugins/kit.json`.

Every exact consumer export updated its pin and reusable workflow tag to 1.2.2, then passed freshness, canonical check, and packaged dry-run at 1.2.2:

| Consumer | Base | Tests |
|---|---|---|
| react | d746b647d0d9f4ceb38838d61bac2ba161d4a01b | 5 passed |
| dotnet | dd937097b7a2e489fc0986119af1ca5320e74fa7 | 16 passed, 2 skipped |
| rust | 579f95d539215d493c1f20ea8372343a7a16bde5 | 10 passed |
| nvim | 66b3e431bb0b51591442b13cb8d2f7147238eed4 | 0 discovered, exit 3 |
| work | 3b021cab6943a422870772de88266b9323d494d9 | 5 passed |

For all five exports, update/freshness/check/dry-run exited 0; public identities were found and authored manifest hashes were unchanged. No original consumer checkout, branch, commit, or remote was changed.

Superseded: this probe copied the producer's intentionally stale committed plugins/kit payload without first generating frozen authored source. It is not compatibility evidence. See template-1.4.0-regenerated-consumer-compatibility.md.
