# Beyond Oasis Coop: spirit ally fix validation

Release: coop-8. ROM SHA-256: `665f32f2f400dd9a3f8a4123a37af7530bb206014efbced6fd4fb45bbfbf41fb`.

Efreet previously acquired P2 through native hostile-object scans. P2 occupies slot 20, inside the original scan range. Four hostile scans now stop at slot 18; allied masked collision scans omit slots 19/20. Spirit updates retain the native P1 owner position instead of the nearest-enemy hero alias. A final allied hit guard protects both heroes. Ordinary enemy and bomb collision paths retain their behavior.

## Current evidence

All 172 checks passed on this ROM: basic 18, features 8, local regression 13, hit reaction 10, story 10, damage 12, burning graphics 15, VRAM 4, serialized rollback 1, native audit fixtures 21, spirits 60. Machine-readable results are in `reports/`; earlier results are archived under `reports/coop-6` and `reports/coop-7` with their original hashes.

The spirit suite reproduces Efreet selecting, hitting and burning P2 on the preceding ROM. It tests Dytto, Efreet, Shade and Bow using native target acquisition and masked collision routines; real enemy slot 18 remains targetable, and bombs retain their collision with P2. Native Dytto/Efreet/Bow attack tables damage enemies while sparing P2. Each spirit is spawned through its native constructor and runs 600 ordinary game frames, followed by serialized save/restore comparison. Controlled fixtures do not cover every special ability or the entire campaign.

The first-boss test also resumes an already blocked state. Its dialogue driver now waits for native control release with a strict 2,040-frame bound. The previous 952-frame assumption failed on both the preceding ROM and the candidate; the old broken enemy counter still reproduces its softlock under the new bound. The fixed build releases controls and P1 can move.

Graphics tests cover burning effects and 3,020 sampled frames in seven scenes. The existing gold subtitle and darkened P2 artwork remain. RetroArch and the bundled core are unchanged. Full campaign and new internet sessions were not tested.

## Build and patchers

The source builder must reproduce the pinned ROM using the original dump and assembled payload. Windows and Python BPS patchers must reproduce the same hash. Bash launcher tests run under Git Bash on Windows with a path conversion shim: paths with spaces, another working directory, terminal selection, empty selection, EOF, bad arguments, simulated GUI cancellation, unsupported ROM and refusing original overwrite. Native Linux and real Zenity/KDialog windows have not been exercised.
