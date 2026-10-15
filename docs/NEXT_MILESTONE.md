# Next milestone: verify the native runtime, then lock down the first playable race

## Current verified state (2026-10-15)

- The source-only GameCube/Wii prototype is on PR #22's branch, `work/step102-import-gate`.
- The devkitPPC/libogc cross-build succeeds and produces a non-empty `swe1r_gc_port.dol` (about 307 KB).
- The host regression suite and static project preflight pass.
- The headless Dolphin smoke test remains alive for its 20-second window without a detected fatal boot error.
- **Visible rendering is still unverified.** Repeated CI runs produced no PNG/BMP from Dolphin, even when running the older minimal GX renderer's DOL as a control under the same user profile, software renderer, and frame-dump config. This shows the current capture method/environment is unable to provide usable evidence; it does not prove either DOL renders black.
- The workflow writes both `Config/Dolphin.ini` (`[Movie] DumpFrames=True`, `[General] DumpPath`) and `Config/GFX.ini` (`[Settings] DumpFramesAsImages=True`, EFB/XFB diagnostics) before startup and archives the configs/file listings.
- The diagnostic now attempts the known minimal GX control DOL first. If that control produces no image, it records the failure and skips the main-DOL capture instead of repeatedly treating the same broken capture path as a game regression. Visual capture is diagnostic-only; the native build, host regression, and emulator smoke checks remain the reliable automated gates.
- Latest control-comparison run (control and main DOL both produced no frame): https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38707260620
- Do not mark visual validation passed until a real non-black frame has been captured and reviewed, manually or through a reliable CI capture path.

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
