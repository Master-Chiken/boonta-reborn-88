# Next milestone: restore the native GameCube/Wii prototype in CI

## Goal

Use the existing Step 102 GameCube/Wii source prototype as the primary project baseline. The next milestone is not another Dreamcast screen: it is a reviewed source-only import, automated host tests, and the first native GameCube cross-build.

## Audit findings

- The source archive `Star_Wars_Racer_GameCube_Step102.zip` is available in the project history/library and has been inspected.
- It contains a C prototype, GameCube Makefile, gameplay/renderer modules, tools, docs, and host tests.
- The archive README describes 25 course entries, 23 pod presets/variants, physics, drift/boost/heat/damage, rival AI, pickups/hazards, several race modes, HUD, and save/progression scaffolding.
- The host release suite passed in a clean temporary environment: host shell checks and 91 Python unit tests passed. This is not a native target build.
- The archive README explicitly says that a real devkitPPC/libogc `.dol` build and Dolphin/console runtime test remain pending.
- The source prototype has not yet been imported into this GitHub repository. The existing native workflow intentionally stops until its source tree is present.
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

- Source provenance and redistribution boundaries are documented.
- Host tests pass in GitHub Actions.
- Native GameCube cross-build produces a non-empty DOL.
- Compile success and emulator/hardware testing are reported separately.
- No commercial ROMs, disc images, BIOS files, or uncleared proprietary assets are committed.

## What the project owner needs to do now

Nothing needs to be installed locally for this planning step. Keep the source archive available in the ChatGPT Library. The work can continue in GitHub with cloud CI; an actual emulator/console run may still require a separate runtime environment.
