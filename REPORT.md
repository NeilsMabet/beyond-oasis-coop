# Beyond Oasis Coop: gold title update validation

ROM SHA-256: `83b6161c3df8c15a211d492a57c67c46412c49090a2a0bd4114e2d6937d3a7f2`.

The subtitle is encoded as 54 native 4bpp tiles at VRAM D400–DABF, with tilemap entries on plane A at C896, C916 and C996. Title-only palette 2 provides the original gold colors and a black outline. The original title planes use palette 0 and the original font uses palette 3. No game mechanics were changed.

An actual emulator screenshot was compared with the previous build at the same frame. All changed pixels are inside the subtitle region: x=89–230, y=137–156 at 320×224. The original logo and surrounding title artwork are unchanged. The new tilemap persists while the start prompt blinks.

Passed suites on the new ROM:

- checks: 18 checks.
- features: 8 checks.
- local-regressions: 13 checks.
- hit-reaction: 10 checks.
- rollback-regression: 1 checks.
- gold-title: 1 checks.
- native audit fixtures: 21 checks.

Total: 72 checks passed.

Previous gameplay audit results (113 checks) are preserved separately in reports/coop-6 and apply to the preceding ROM hash. The full campaign and new internet sessions were not tested for this art update. RetroArch and the core are unchanged. The Windows BPS patcher and source builder must reproduce the hash above.

## Linux patcher helper

Bash syntax and launcher branches were exercised using Git Bash on Windows, with a path-conversion shim for the Windows Python runtime. Covered: explicit paths with spaces, launch from another working directory, terminal file selection, empty selection, EOF, invalid arguments, simulated GUI cancellation, unsupported ROM and refusing to overwrite the source. The Python BPS applier reproduced the pinned ROM hash. Native Linux and real Zenity/KDialog windows were not exercised in this environment.
