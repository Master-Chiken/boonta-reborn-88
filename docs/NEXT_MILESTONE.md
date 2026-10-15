# Next milestone: restore the native GameCube/Wii prototype in CI

## Goal
Use the existing Step 102 GameCube/Wii source prototype as the primary project baseline. The next milestone is a reviewed source-only import, automated host tests, and a reproducible native GameCube cross-build—not another unrelated visual demo.

## Current GitHub work
- [PR #22: Step 102 source prototype import](https://github.com/Master-Chiken/boonta-reborn-88/pull/22) is the principal implementation candidate. It remains a draft and needs source-provenance/license review before merge.
- [PR #20: clean-room GameCube first-render prototype](https://github.com/Master-Chiken/boonta-reborn-88/pull/20) is a separate, smaller renderer/input experiment. Its successful compile is useful evidence for the toolchain, but it is not the full game.
- [PR #17: source-only import candidate](https://github.com/Master-Chiken/boonta-reborn-88/pull/17) documents earlier import work and its validation constraints.
- The current `main` branch does not contain the Step 102 `Makefile` and `source/` tree. Do not describe the full native game as integrated into `main` until that is verified from the branch contents.

## Audit findings
- The source archive `Star_Wars_Racer_GameCube_Step102.zip` is available in the project history/library and has been inspected.
- It contains a C prototype, GameCube Makefile, gameplay/renderer modules, tools, docs, and host tests.
- The archive README describes 25 course entries, 23 pod presets/variants, physics, drift/boost/heat/damage, rival AI, pickups/hazards, several race modes, HUD, and save/progression scaffolding.
- The host release suite passed in a clean temporary environment: host shell checks and 91 Python unit tests passed. This is not a native target build.
- The source prototype's own documentation says that a real devkitPPC/libogc `.dol` build and Dolphin/console runtime test must be verified separately.
- The separate Dreamcast starter and its CI artifact do not validate the GameCube/Wii prototype.

## Work sequence
1. Review the source archive's provenance, license, generated route data, and assets.
2. Import only cleared source, headers, Makefile, tools, tests, and documentation; do not import ROMs/disc images or unclear proprietary payloads.
3. Run the host test suite in GitHub Actions.
4. Use the existing devkitPPC/libogc workflow to build `swe1r_gc_port.dol`.
5. Inspect the first compiler failure if any and fix it without disabling tests.
6. Run the DOL in Dolphin if available and record actual boot/render/controller results. A successful compile alone is not runtime proof.
7. Once a build boots, focus on a small playable vertical slice: one course, one controllable pod, camera follow, track collision, and stable frame timing.

## Acceptance criteria
- Source provenance and redistribution boundaries are documented and reviewed.
- Host tests pass in GitHub Actions.
- Native GameCube cross-build produces a non-empty DOL from the intended GameCube/Wii source tree.
- Compile success and emulator/hardware testing are reported separately.
- No commercial ROMs, disc images, BIOS files, or uncleared proprietary assets are committed.
- Before calling the work integrated, verify the relevant files and commit are present on `main`.

## What the project owner needs to do now
No local installation is needed for the source-review and documentation steps. Keep the source archive available in the project Library. Cloud CI can perform host tests and cross-builds; a visible interactive Dolphin or real-console run may still require a suitable runtime environment.
