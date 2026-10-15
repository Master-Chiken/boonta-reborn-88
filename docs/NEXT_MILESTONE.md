# Next milestone: verify the native runtime, then lock down the first playable race

## Current verified state (2026-10-15)

- The source-only GameCube/Wii prototype is on PR #22's branch, `work/step102-import-gate`.
- The devkitPPC/libogc cross-build succeeds and produces a non-empty `swe1r_gc_port.dol` (about 307 KB) and ELF.
- The static preflight and complete host regression suite pass.
- The headless Dolphin smoke test remains alive through its configured 20-second window without a detected fatal boot error. This does not prove visible rendering.
- Source provenance and redistribution rights are not fully cleared; keep PR #22 in draft until the review is complete.

## Latest visual-capture findings

- Earlier run [#38708412384](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38708412384) used an Ubuntu 26.04 runner and could not create a normal Dolphin GUI window. Its logs contain the same Qt startup errors reported for Dolphin's Ubuntu 26.04 package; this is an emulator/host diagnostic failure, not evidence that either DOL renders black.
- The run [#38714239484](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38714239484) on Ubuntu 24.04 captured 800×600 windows for both the minimal GX control and current prototype. Both images reported the same mean intensity (0.336923), and the window tree also contained a small `Error` dialog. Although the job ended green because visual capture is diagnostic-only and uses `continue-on-error`, this is **not accepted as proof of a game frame**; the script may have captured the Dolphin library/main window rather than the render surface.
- The follow-up workflow change on commit `0998db217da439be23c84825e5859c955f643545` writes a valid `[Display]` config using a here-document, prefers the visible window titled exactly `Dolphin` (the separate render surface when present), and compares the prototype capture to the minimal GX control with normalized RMSE. Nearly identical images should now be rejected instead of being marked visually valid.
- The verification run for that change is [#38714853204](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38714853204). Recheck its `dolphin-visual` job and logs before updating the state below.
- Do not mark visible rendering passed until a suitable in-game image is captured and reviewed. A non-black screenshot by itself is insufficient because Dolphin's UI can also be non-black.

## Audit findings

- The Step 102 prototype contains course entries, pod presets, physics, drift/boost/heat/damage, rival AI, pickups/hazards, race modes, HUD, and save/progression scaffolding. These are prototype features, not proof of parity with the commercial game.
- Existing host tests cover many gameplay modules, including multi-track simulations and championship standings. They do not replace an interactive emulator/console run of the main loop, controller handling, visible rendering, and finish/restart flow.
- The separate Dreamcast starter and its CI artifact do not validate the GameCube/Wii prototype.
- Keep the project clean-room: no ROMs, disc images, BIOS files, or uncleared proprietary assets.

## Work sequence

1. Keep the host regression suite green and require a successful native DOL build for every gameplay change.
2. Get a validated in-game frame from Dolphin. If the selected window is still the UI or an error dialog appears, inspect the archived `dolphin.log`, window tree, window titles and capture artifact; don't infer a game-render defect from an emulator UI failure.
3. Add a repeatable controller-input test for menu navigation and starting a race. A successful boot/smoke test alone does not verify controls.
4. Verify the vertical slice end-to-end: one course, controllable pod, camera follow, track boundaries/collision, rival movement, lap progression, finish state, restart and stable frame timing.
5. Once runtime behavior is observable, fix gameplay/rendering defects before adding more features.

## Acceptance criteria

- [ ] Source provenance and redistribution boundaries documented.
- [x] Host regression suite passes in GitHub Actions.
- [x] Native GameCube cross-build produces a non-empty DOL/ELF.
- [x] Limited headless Dolphin smoke test stays alive without detected fatal boot errors.
- [ ] A non-black **game-render** frame is captured and manually reviewed; Dolphin UI screenshots do not count.
- [ ] Controller navigation and driving controls are verified interactively.
- [ ] One race is completed end-to-end, including lap progression, finish and restart.
- [x] CI artifacts preserve native build, emulator logs, window tree and images for review (seven-day retention).

## What the project owner needs to do

No local installation is required for the current cloud build/test loop. If CI still cannot capture the game's render surface, one manual Dolphin run with the generated DOL or a physical-console run may be needed.
