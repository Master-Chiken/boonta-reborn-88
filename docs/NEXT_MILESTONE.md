# Next milestone: restore the native GameCube/Wii prototype in CI

## Goal

Use the existing Step 102 GameCube/Wii source prototype as the primary project baseline. The source-only import and host-test gate are now complete on PR #22. The active milestone is a clean native GameCube cross-build, followed by a Dolphin runtime smoke test.

## Audit findings

- The source archive `Star_Wars_Racer_GameCube_Step102.zip` is available in the project history/library and has been inspected.
- It contains a C prototype, GameCube Makefile, gameplay/renderer modules, tools, docs, and host tests.
- The archive README describes 25 course entries, 23 pod presets/variants, physics, drift/boost/heat/damage, rival AI, pickups/hazards, several race modes, HUD, and save/progression scaffolding.
- The source-import workflow passed all 32 host shell checks and 5 Python policy tests. This is not a native target build.
- The archive README explicitly says that a real devkitPPC/libogc `.dol` build and Dolphin/console runtime test remain pending.
- The source-only prototype is imported on PR #22's working branch: 45 files under `source/`, 70 under `tests/`, six under `tools/`, the `data/` demo track inputs, and the root `Makefile`. The temporary encoded archive was removed after extraction.
- The separate Dreamcast starter and its CI artifact do not validate the GameCube/Wii prototype.

## Work sequence

1. Keep provenance and redistribution boundaries explicit; do not add ROMs/disc images or unclear proprietary payloads.
2. Keep the host regression suite green as source changes land.
3. Use the devkitPPC/libogc workflow to produce `swe1r_gc_port.dol`; inspect and fix compiler errors without disabling tests.
4. Run the DOL in Dolphin if available and record actual boot/render/controller results. A successful compile alone is not runtime proof.
5. Once a build boots, focus on a small playable vertical slice: one course, one controllable pod, camera follow, track collision, and stable frame timing.

## Acceptance criteria

- Source provenance and redistribution boundaries are documented.
- Host tests pass in GitHub Actions.
- Native GameCube cross-build produces a non-empty DOL.
- Compile success and emulator/hardware testing are reported separately.
- No commercial ROMs, disc images, BIOS files, or uncleared proprietary assets are committed.

## What the project owner needs to do now

Nothing needs to be installed locally for this planning step. Keep the source archive available in the ChatGPT Library. The work can continue in GitHub with cloud CI; an actual emulator/console run may still require a separate runtime environment.
