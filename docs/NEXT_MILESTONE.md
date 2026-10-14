# Next milestone: boot the first native GameCube/Wii build

## Goal

Use the existing Step 102 GameCube/Wii source prototype as the primary project baseline. The source-only import and host-test gate are now complete on PR #22. The devkitPPC/libogc cross-build succeeds and produces a non-empty `swe1r_gc_port.dol` (307,428 bytes). A headless Dolphin smoke test passed for 20 seconds without a detected fatal error. The active milestone is visual/runtime validation. The first visual CI attempt failed because no visible Dolphin window was found and the screenshot fallback captured a black Xvfb root window; that is a capture/launch failure, not proof that the game itself renders black. The workflow now waits up to 30 seconds for a visible Dolphin window before capturing, and the rerun is in progress.

## Audit findings

- The source archive `Star_Wars_Racer_GameCube_Step102.zip` is available in the project history/library and has been inspected.
- It contains a C prototype, GameCube Makefile, gameplay/renderer modules, tools, docs, and host tests.
- The archive README describes 25 course entries, 23 pod presets/variants, physics, drift/boost/heat/damage, rival AI, pickups/hazards, several race modes, HUD, and save/progression scaffolding.
- The source-import workflow passed all 32 host shell checks and 5 Python policy tests. This is not a native target build.
- The CI build succeeded on 2026-10-14 and uploaded `swe1r_gc_port.dol` (307,428 bytes), the ELF, and the build log. A headless Dolphin run stayed active for 20 seconds without a detected fatal error; visible rendering, controls, and race completion remain unverified.
- The source-only prototype is imported on PR #22's working branch: 45 files under `source/`, 70 under `tests/`, six under `tools/`, the `data/` demo track inputs, and the root `Makefile`. The temporary encoded archive was removed after extraction.
- The separate Dreamcast starter and its CI artifact do not validate the GameCube/Wii prototype.

## Work sequence

1. Keep provenance and redistribution boundaries explicit; do not add ROMs/disc images or unclear proprietary payloads.
2. Keep the host regression suite green as source changes land.
3. Capture the actual Dolphin game window (not the Xvfb root window) and verify the course/HUD are visible. The updated workflow waits for a visible Dolphin window; if none appears, it fails with a specific diagnostic.
4. Verify controller navigation and whether a race can be completed; fix runtime issues without weakening host tests. The vertical slice target remains one course, one controllable pod, camera follow, track collision, and stable frame timing.

## Acceptance criteria

- Source provenance and redistribution boundaries are documented.
- Host tests pass in GitHub Actions.
- Native GameCube cross-build produces a non-empty DOL. **PASS** in GitHub Actions.
- Compile success and emulator/hardware testing are reported separately. **Headless emulator smoke: PASS; visual/gameplay test: pending.** The initial visual job failed to find a visible Dolphin window, so its black root-window screenshot is not valid evidence about game rendering.
- No commercial ROMs, disc images, BIOS files, or uncleared proprietary assets are committed.

## What the project owner needs to do now

Nothing needs to be installed locally for this planning step. Keep the source archive available in the ChatGPT Library. The work can continue in GitHub with cloud CI; an actual emulator/console run may still require a separate runtime environment.
