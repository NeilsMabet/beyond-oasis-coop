# Beyond Oasis Co-op

An experimental two-player ROM hack of **Beyond Oasis** for the Sega Mega Drive / Genesis. **Immortal6** focuses on local co-op and fixes identified by the P2 memory audit.

## Current gameplay

- Two independently controlled heroes: movement, jumping and attacks.
- P2 uses the original hero artwork, darkened by 25%, with no P2 label.
- P2 is invulnerable, but still reacts to hits and has actions interrupted.
- P1 owns story interactions, dialogue, inventory, pickups and spirits. The camera follows P1; P2 catches up when leaving the screen. Room transitions are shared.
- P2 mirrors P1's current weapon. Durability and ammunition are shared.
- Direct player attacks do not damage the other player. Original hazards, including bombs, retain their game behavior; P2's invulnerability still applies.
- During story dialogue and menu graphics transitions, P2 is temporarily hidden/paused. The original game uses that graphics bank for text; P2's artwork reloads afterwards.

**This is a prototype, not a verified full-campaign co-op conversion.** Immortal6 has not undergone new internet play testing. Save states from selected earlier builds were tested, but new Immortal6 states are recommended.

## Required original ROM

Supply your own unmodified **Beyond Oasis (U)** ROM, 3,145,728 bytes, with this SHA-256:

```text
eb19bda4982366a2fd43d65ab8a7f9709d83a8cc902c14a682c088c16359c263
```

Only this exact dump is supported. A different filename does not matter; different contents do. The patcher refuses mismatched files and never overwrites the original. This repository and its release archives do not contain an original or patched game ROM.

## Play on Windows

1. Download and extract the full **Immortal6** release archive, or download this repository.
2. Run `Create-Coop-ROM.cmd` and select your original ROM. The result is `generated/Beyond Oasis Coop Immortal.bin`.
3. Install **RetroArch 1.22.2** separately. Run `Play-Local.cmd` and select `retroarch.exe` when prompted. The tested **Genesis Plus GX v1.7.4-coop1** core is included in `core/`.
4. Connect both controllers before starting. In RetroArch, open **Settings в†’ Input в†’ RetroPad Binds** and assign the two devices to Port 1 and Port 2. The configuration uses three-button Mega Drive controllers.
5. Start the game with P1. P2 joins as the helper during gameplay.

The small **patcher-only** archive creates the same ROM but does not include the emulator core or local launcher. Use the full archive for the tested configuration. RetroArch itself is not modified or bundled. The bundled core contains earlier state-serialization changes; it was not changed for Immortal6. See [third-party notices](THIRD_PARTY_NOTICES.md).

### Other ROM revisions

There are many region, revision, overdump and headered variants. This release does not guess which one you have or silently patch a different revision. Check SHA-256 in PowerShell:

```powershell
Get-FileHash -LiteralPath "C:\Games\Beyond Oasis.bin" -Algorithm SHA256
```

### Internet play

Internet co-op is intended to use emulator netplay. Use the same patched ROM, core and emulator settings on both PCs. This release only reports local and deterministic state tests; it does **not** claim a validated 30-minute network session, measured latency, or compatibility with arbitrary emulator versions.

## Build the ROM from source

Python 3 is required for the source build, but not for the Windows BPS patcher.

```powershell
python src/build.py --rom "C:\Games\Beyond Oasis.bin"
```

This uses the pinned `src/payload.bin`. To assemble the 68000 source with **vasm 1.9d**:

```powershell
python src/build.py --rom "C:\Games\Beyond Oasis.bin" --assembler "C:\Tools\vasmm68k_mot.exe"
```

The builder verifies the original ROM, payload, expected original instructions and output SHA-256. The pinned release must reproduce:

```text
5248dfd2b06b7c736ad1212f8709128855fd5253012f75b25e2f21f32adc5a35
```

Generate the BPS patch after building:

```powershell
python src/bps.py --rom "C:\Games\Beyond Oasis.bin"
```

For intentional source changes, developers must regenerate the native adapter addresses in `src/target-routes.json` and deliberately update the pinned payload/output hashes. The release builder rejects unpinned changes.

## Validation and known limits

**113 checks passed** on the pinned Immortal6 ROM. Coverage includes local controls, weapons, damage isolation, hit reactions, the first story battle, burning graphics, save/restore, deterministic rollback, allocator exclusions and audited grab/drain handlers. VRAM sampling covered 3,020 frames across seven bounded scenarios.

See [validation report](REPORT.md), [technical notes](RESEARCH.md) and machine-readable results in `reports/`. Tests use Python with NumPy/Pillow; native fixtures also require vasm. Some tests need private gameplay save states that are not distributed. Full campaign coverage, every enemy and graphics mode, and internet session acceptance remain unverified.

## Reporting a bug

Include the Immortal6 build/hash, emulator and core versions, room or encounter, player actions and a screenshot. A short reproducible sequence is especially useful. Do not attach game ROMs to issues. An older save state may carry old graphics/cache data; mention which build created it.

## Credits and distribution

Beyond Oasis and its original assets belong to their respective rights holders. This is an unofficial fan project. Distribute the patch/patcher rather than game ROMs. Third-party emulator notices and the complete source corresponding to the bundled modified core are included. No blanket license is assigned to third-party game assets or emulator code; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
