# Beyond Oasis Coop technical notes

## Actor RAM

P1: FF19E8. P2: FF2898. Metadata: FF27DC. Large actor stride: BC bytes. All four audited allocators exclude reserved metadata/P2 slots. All co-op state lives in emulator-serialized RAM.

META+1F holds migration version 6. META+20/+24 hold 32-bit P1/P2 grab-owner masks indexed by actor slot. Room spawn clears both; release removes individual ownership.

## Graphics layout

| Owner | VRAM byte range |
| --- | --- |
| Native effects | A900–B7FF |
| P2 body / native dialogue text during story lock | B800–BFFF |
| Eight native small-object slots | D280–DB7F |
| Observed full-screen horizontal scroll table | DC00–DC03 |
| P2 weapon | DC20–DE1F |

Render hook A232 suppresses P2 while FF1983 is nonzero or the menu flag FF185D is set. The caches invalidate and reload afterwards. Observed body demand is at most 54 of 64 reserved tiles; weapon demand is at most 16 of 16 tiles in checked frames. Other campaign graphics modes have not been established.

## ROM banks

Payload: 300000–30FFFF. Darkened original tiles: 310000–35F0FF. Decoded immutable effects: 35F100–35FFFF. Effect DMA uses source word address 1AF880, destination A900, length 780 words, without modifying the original shared decompression buffer.

## Native combat adapters

src/target-routes.json pins 93 source instructions, expected bytes and adapter addresses. Audited ranges: 1A39C–1AC90, 1CC42–1CD50, 2077C–20B1E and 23B02–23BC8. Earlier story operations remain owned by P1.

Adapters preserve SR. The P1 branch executes the original instruction; the P2 branch substitutes personal actor/metadata addresses. Direct health writes preserve P2 HP. Do not globally redirect every P1 literal: camera, story and inventory intentionally belong to P1.

Unproven or unreachable animation-index candidates from the audit were not changed. These notes describe bounded evidence, not full-campaign compatibility.

## Gold title subtitle

Title-only helper at ROM 30D000 loads 54 tiles from 30D100 into D400–DABF. The subtitle tilemap uses palette 2 and plane A at C896/C916/C996. The title background uses tiles 000–452 and palette 0; original text uses 780+ and palette 3. Palette RAM FF138E (palette 2, index 1) is blackened for the outline. Original title load establishes the remaining colors and normal room loading replaces the palette. `title-gold.bin` is the native asset derived from the approved artwork.
