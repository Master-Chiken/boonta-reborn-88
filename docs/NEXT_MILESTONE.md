# Next milestone: verify the native runtime, then lock down the first playable race

## Current verified state (2026-10-15)

- The source-only GameCube/Wii prototype is on PR #22's branch, `work/step102-import-gate`.
- The devkitPPC/libogc cross-build succeeds and produces a non-empty `swe1r_gc_port.dol` (about 307 KB).
- The host regression suite and static project preflight pass.
- The headless Dolphin smoke test remains alive for its 20-second window without a detected fatal boot error.
- **Visible rendering is still unverified.** Both the GUI/Xvfb screenshot attempt and the latest software-renderer EFB/XFB dump attempt failed to produce a usable frame. The latest log contains Qt session warnings and no PNG/BMP dump; this does not prove the game's framebuffer is black.
- Latest CI run: https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38704997348
- Latest visual evidence artifact (diagnostic log only): https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38704997348/artifacts/11958620566

## Audit findings

- The source archive `Star_Wars_Racer_GameCube_Step102.zip` contains a C prototype, GameCube Makefile, gameplay/renderer modules, tools, documentation, and host tests.
- The imported prototype includes course entries, pod presets, physics, drift/boost/heat/damage, rival AI, pickups/hazards, race modes, HUD, and save/progression scaffolding. These are prototype features, not proof of parity with the commercial game.
- The native-source import audit previously passed 32 host shell checks and 5 Python policy tests.
- The separate Dreamcast starter and its CI artifact do not validate the GameCube/Wii prototype.
- Keep the project clean-room: no ROMs, disc images, BIOS files, or uncleared proprietary assets.

## Work sequence

1. Keep the host regression suite green and require a successful native DOL build for every gameplay change.
2. Replace unreliable emulator image-dump assumptions with a verified capture path. First inspect Dolphin's actual generated `GFX.ini`, supported CLI/config options, and renderer logs; do not mark rendering as passed until an actual non-black frame from the game is captured.
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
