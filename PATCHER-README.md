# Beyond Oasis Coop patcher

Extract the archive and run **Create-Coop-ROM.cmd**. Select your unmodified Beyond Oasis (U) ROM. Only this SHA-256 is accepted:

`eb19bda4982366a2fd43d65ab8a7f9709d83a8cc902c14a682c088c16359c263`

Output: `generated/Beyond Oasis Coop.bin`. Your original is never overwritten. A different filename is fine; a different dump is unsupported.

P2 uses the original darkened artwork, is invulnerable, and reacts to hits. P2 temporarily hides during story dialogue/menu graphics ownership. Full-campaign and new internet-session compatibility are not verified.

The patcher-only archive does not include an emulator or core. The full release includes the tested Genesis Plus GX v1.7.4-coop1 core and a launcher for a separately installed RetroArch 1.22.2. For detailed instructions, see the repository README.

Share this patcher, not a game ROM. Both players must use identical patched ROMs for netplay.

The resulting ROM can be loaded in any compatible Mega Drive / Genesis emulator on any platform with two controller ports. The included Windows patching scripts and tested RetroArch configuration are optional conveniences; universal emulator compatibility has not been individually verified.

[English instructions](README.md) | [Русская инструкция](README.ru.md)

## Linux

Requires Python 3, no extra packages: `bash create-coop-rom.sh "/path/to/original.bin"`. Without a path, the script uses an optional Zenity/KDialog file picker or asks in the terminal. Output: `generated/Beyond Oasis Coop.bin`. The original is never overwritten.
