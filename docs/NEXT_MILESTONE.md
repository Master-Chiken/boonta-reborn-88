# Next milestone: verify the native runtime, then lock down the first playable race

## Current verified state (2026-10-15)

- The source-only GameCube/Wii prototype is on PR #22's branch, `work/step102-import-gate`.
- The devkitPPC/libogc cross-build succeeds and produces a non-empty `swe1r_gc_port.dol` (about 307 KB).
- The host regression suite and static project preflight pass.
- The headless Dolphin smoke test remains alive for its 20-second window without a detected fatal boot error.
- **Visible rendering is still unverified.** The latest frame job produced no image. Inspection of Dolphin's current configuration source revealed that actual frame-dump activation is the main `[Movie]` key `DumpFrames`; `GFX.ini`'s `DumpFramesAsImages` only controls image output format, and is not itself the runtime dump toggle.
- The workflow now writes both `Config/Dolphin.ini` (`[Movie] DumpFrames=True`, `[General] DumpPath`) and `Config/GFX.ini` (`[Settings] DumpFramesAsImages=True`, EFB/XFB diagnostics) before startup, then archives both configs and the file listing. This is a targeted fix based on Dolphin's config schema; the next CI result must confirm whether it works.
- Latest completed diagnostic run before the corrected Movie setting: https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38705925288
- The revised workflow triggers a fresh run. Do not call visual validation passed until the job captures a non-black image.

## Audit findings

- The source archive `Star_Wars_Racer_GameCube_Step102.zip` contains a C prototype, GameCube Makefile, gameplay/renderer modules, tools, documentation, and host tests.
- The imported prototype includes course entries, pod presets, physics, drift/boost/heat/damage, rival AI, pickups/hazards, race modes, HUD, and save/progression scaffolding. These are prototype features, not proof of parity with the commercial game.
- The native-source import audit previously passed 32 host shell checks and 5 Python policy tests.
- The separate Dreamcast starter and its CI artifact do not validate the GameCube/Wii prototype.
- Keep the project clean-room: no ROMs, disc images, BIOS files, or uncleared proprietary assets.

## Work sequence

1. Keep the host regression suite green and require a successful native DOL build for every gameplay change.
2. Get a verified in-game frame from Dolphin. Inspect the effective config and renderer logs if frame dumping still fails; do not interpret an absent image as proof that the game rendered black.
3. Add a repeatable controller-input test for menu navigation and starting a race. A successful boot/smoke test alone does not verify controls.
4. Verify the vertical slice end-to-end: one course, controllable pod, camera follow, track boundaries/collision, rival movement, lap progression, finish state, and stable frame timing.
5. Once runtime behavior is observable, fix gameplay/rendering defects before adding more features.

## Acceptance criteria

- Source provenance and redistribution boundaries documented.
- Host regression suite passes in GitHub Actions.
- Native GameCube cross-build produces a non-empty DOL. **PASS**.
- Headless Dolphin smoke test stays alive without detected fatal boot errors. **PASS, limited scope**.
- Non-black in-game frame captured and reviewed. **PENDING**.
- Controller navigation and race completion verified. **PENDING**.
- No commercial ROMs, disc images, BIOS files, or uncleared proprietary assets committed.

## What the project owner needs to do

No local installation is required for the current cloud build/test loop. Continue work on the existing PR branch. A real emulator/console run may still be needed if CI cannot provide reliable visual capture.
