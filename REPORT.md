# Immortal6 validation report

Tested ROM SHA-256: `5248dfd2b06b7c736ad1212f8709128855fd5253012f75b25e2f21f32adc5a35`.

## Implemented audit fixes

- P2 body graphics moved to B800–BFFF and weapon graphics to DC20–DE1F. All eight native small-object slots at D280–DB7F retain their original layout. Migration invalidates their cached graphics mappings.
- Native dialogue also owns B800. P2 rendering and updates are suspended during story/menu ownership, then its body and weapon graphics are reloaded.
- Effects A900–B7FF are restored from immutable ROM bank 35F100–35FFFF. The shared decompression buffer FF2FA8 is no longer overwritten ahead of queued DMA.
- Allocator DA1A now excludes the reserved META/P2 slots even when the metadata marker is zero; the other three allocator exclusions are retained.
- 93 adapters route audited combat accesses to the selected hero. Special attacks, direct health drains and grabs aimed at P2 preserve P1's health. P2 remains invulnerable with hit reactions; equivalent P1 paths retain original damage.
- Grab ownership stays with its initial victim when the other hero moves closer. Release removes ownership; room spawn clears the masks.

## Results

| Suite | Passed checks |
| --- | ---: |
| Basic gameplay | 18 |
| Local regressions | 13 |
| Features | 9 |
| Hit reactions | 10 |
| First-battle story progression | 10 |
| Damage isolation | 12 |
| Serialized rollback equality | 1 |
| Burning graphics | 15 |
| Native audit fixtures | 21 |
| VRAM scenarios | 4 |
| **Total** | **113** |

VRAM sampling covered 3,020 frames across beach, combat, village, cave, fire, map and first-battle story scenarios. The observed full-screen horizontal scroll table occupies DC00–DC03. Dialogue hiding and subsequent body reload were exercised. Save/restore and rollback compared all serialized bytes. Fire rendering was checked for P1, P2 and both burning simultaneously.

The extracted Windows patcher and the pinned-payload Python builder both recreated the same ROM as the assembled source build. Original ROM and previous Immortal5 output were unchanged. Machine-readable results are in reports/.

## Limits

Controlled native handler calls do not establish natural coverage of every enemy encounter. Sampled DMA queues do not trace every direct CPU write to VDP. The full campaign and every graphics mode remain untested. No new internet sessions were run for this release. RetroArch and the core were unchanged.

Tests use Python, NumPy and Pillow; audit fixtures also use vasm. Some fixtures depend on private user gameplay states under the development workspace, omitted from public archives. The Windows patcher needs none of these test dependencies.
