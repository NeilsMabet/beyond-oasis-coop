# Beyond Oasis Coop

[Русский](README.ru.md) | English

An experimental two-player ROM hack of **Beyond Oasis** for the Sega Mega Drive / Genesis. **Beyond Oasis Coop** focuses on local co-op and fixes identified by the P2 memory audit.

![Beyond Oasis Coop title screen](docs/images/title-preview.png)

![Two heroes in a story scene](docs/images/story-preview.png)

![Both heroes with fire effects](docs/images/burn-player-3.png)

## Current gameplay

- Two independently controlled heroes: movement, jumping and attacks.
- P2 uses the original hero artwork, darkened by 25%, with no P2 label.
- P2 is invulnerable, but still reacts to hits and has actions interrupted.
- P1 owns story interactions, dialogue, inventory, pickups and spirits. The camera follows P1; P2 catches up when leaving the screen. Room transitions are shared.
- Summoned spirits treat P2 as an ally: Dytto, Efreet, Shade and Bow do not select or hit P2 through the tested targeting and attack paths.
- P2 mirrors P1's current weapon. Durability and ammunition are shared.
- Direct player attacks do not damage the other player. Original hazards, including bombs, retain their game behavior; P2's invulnerability still applies.
- During story dialogue and menu graphics transitions, P2 is temporarily hidden/paused. The original game uses that graphics bank for text; P2's artwork reloads afterwards.

**This is a prototype, not a verified full-campaign co-op conversion.** Beyond Oasis Coop has not undergone new internet play testing. Save states from selected earlier builds were tested, but new states from this release are recommended.

## Required original ROM

Supply your own unmodified **Beyond Oasis (U)** ROM, 3,145,728 bytes, with this SHA-256:

```text
eb19bda4982366a2fd43d65ab8a7f9709d83a8cc902c14a682c088c16359c263
```

Only this exact dump is supported. A different filename does not matter; different contents do. The patcher refuses mismatched files and never overwrites the original. This repository and its release archives do not contain an original or patched game ROM.

## Play on any platform

The patched ROM is intended for **any compatible Mega Drive / Genesis emulator on any platform**, with two controller ports enabled. Windows and RetroArch are not requirements of the ROM. Compatibility with every emulator has not been individually tested.

1. Apply `beyond-oasis-coop.bps` to your supported original ROM with a BPS patcher available on your platform. Alternatively, build it with Python as described below.
2. Open the resulting `Beyond Oasis Coop.bin` in your emulator.
3. Enable two standard three-button Mega Drive controllers and assign a separate input device to each port.
4. Start the game with P1; P2 appears as the helper during gameplay.

### Tested Windows setup (optional)

Tests were run with **RetroArch 1.22.2** and **Genesis Plus GX v1.7.4-coop1**. The full release includes this core and its complete source, plus Windows convenience scripts:

1. Run `Create-Coop-ROM.cmd` and select your original ROM. Output: `generated/Beyond Oasis Coop.bin`.
2. Install RetroArch separately. Run `Play-Local.cmd` and select `retroarch.exe`.
3. Assign separate devices to Port 1 and Port 2 in RetroArch's input settings.

The launcher selects the bundled core. Other compatible emulators can load the patched ROM directly. The patcher-only archive omits the core and launcher. RetroArch itself is not modified or bundled; the core contains earlier state-serialization changes. See [third-party notices](THIRD_PARTY_NOTICES.md).

### Linux patcher

Install Python 3 using your distribution's package manager, then run from the extracted release folder:

```bash
bash create-coop-rom.sh "/path/to/Beyond Oasis.bin"
```

Without an argument, `bash create-coop-rom.sh` opens a file picker if Zenity or KDialog is available in a graphical session; otherwise it asks for the path in the terminal. Cancelling the picker exits without creating a ROM. A second argument selects the output path. The default output is `generated/Beyond Oasis Coop.bin` next to the script. Spaces in paths are supported. No additional Python packages are needed.

You can also use `chmod +x create-coop-rom.sh` and launch it as `./create-coop-rom.sh`. The Windows core DLL is not needed on Linux; open the patched ROM in your compatible Linux emulator.

### Other ROM revisions

There are many region, revision, overdump and headered variants. This release does not guess which one you have or silently patch a different revision. Check SHA-256 in PowerShell:

```powershell
Get-FileHash -LiteralPath "C:\Games\Beyond Oasis.bin" -Algorithm SHA256
```

### Internet play

Internet co-op is intended to use emulator netplay. Use the same patched ROM, core and emulator settings on both PCs. This release only reports local and deterministic state tests; it does **not** claim a validated 30-minute network session, measured latency, or compatibility with arbitrary emulator versions.

## Build the ROM from source

Python 3 is required for the source build and can be used on Windows, macOS or Linux. It is not required when applying the BPS patch with a separate patcher.

```powershell
python src/build.py --rom "C:\Games\Beyond Oasis.bin"
```

This uses the pinned `src/payload.bin`. To assemble the 68000 source with **vasm 1.9d**:

```powershell
python src/build.py --rom "C:\Games\Beyond Oasis.bin" --assembler "C:\Tools\vasmm68k_mot.exe"
```

The builder verifies the original ROM, payload, expected original instructions and output SHA-256. The pinned release must reproduce:

```text
665f32f2f400dd9a3f8a4123a37af7530bb206014efbced6fd4fb45bbfbf41fb
```

Generate the BPS patch after building:

```powershell
python src/bps.py --rom "C:\Games\Beyond Oasis.bin"
```

For intentional source changes, developers must regenerate the native adapter addresses in `src/target-routes.json` and deliberately update the pinned payload/output hashes. The release builder rejects unpinned changes.

## Validation and known limits

This release passed **172 checks**, including 60 spirit regression checks. The old Efreet attack on P2 was reproduced, then the same setup passed with the fix. Coverage includes native target selection, collision masks, real spirit attack tables, 600 ordinary frames per summoned spirit, deterministic state restore, local controls, shared weapons, damage isolation, hit reactions, the first story battle, burning graphics and the memory audit fixtures. VRAM sampling covered 3,020 frames across seven bounded scenarios.

See [validation report](REPORT.md), [technical notes](RESEARCH.md) and machine-readable results in `reports/`. Tests use Python with NumPy/Pillow; native fixtures also require vasm. Some tests need private gameplay save states that are not distributed. Full campaign coverage, every enemy and graphics mode, and internet session acceptance remain unverified.

## Reporting a bug

Include the Beyond Oasis Coop build/hash, emulator and core versions, room or encounter, player actions and a screenshot. A short reproducible sequence is especially useful. Do not attach game ROMs to issues. An older save state may carry old graphics/cache data; mention which build created it.

## Credits and distribution

Beyond Oasis and its original assets belong to their respective rights holders. This is an unofficial fan project. Distribute the patch/patcher rather than game ROMs. Third-party emulator notices and the complete source corresponding to the bundled modified core are included. No blanket license is assigned to third-party game assets or emulator code; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
