# GameCube prototype status

Last updated: 2026-10-24


## Owner priority update — 2026-10-24

Continue implementation and automated regression work now; do not wait for physical-controller testing or broad public playtesting before advancing the racing slice. Finish/review the existing candidates first:

- [PR #214 — width-aware rail collision](https://github.com/Master-Chiken/boonta-reborn-88/pull/214), current head `324962374e1c359e3b8e476e3b37a834547f7d72`. Its latest commit adds frame-time-scaled off-road-drag regression assertions without changing runtime physics. [Exact-head workflow #40129536252](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40129536252) passed all four jobs: host C/Python tests, native DOL/ELF build, Dolphin headless process smoke, and the optional non-blocking Software Renderer diagnostic. Artifacts: [DOL/ELF](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40129536252/artifacts/12573901814), [headless smoke](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40129536252/artifacts/12574717505), and [renderer bundle](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40129536252/artifacts/12574039567), expiring 31 October 2026.
- [PR #247 — analog steering deadzone](https://github.com/Master-Chiken/boonta-reborn-88/pull/247), current code head `defd893f3c25fa240e24bc9524545ef1d12d4b4f`. [Workflow #40098910954](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40098910954) passed the policy guards, host tests, native build, headless Dolphin process smoke, and Software Renderer diagnostic. Its branch adds source-contract coverage for the stick/D-pad steering call path and bounded Dolphin installation steps.
- [PR #259 — Start restart after finish](https://github.com/Master-Chiken/boonta-reborn-88/pull/259), current PR head `52733175993d70d8fce9d8260ad5428af511412f`; the latest commit updates control documentation, while the runtime code from `67968afb0b00754b7d642814e4d59c41c9ce3704` is unchanged. Exact-head workflow [#40111152677](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40111152677) passed all policy gates and all four GameCube jobs. The scripted capture detected the three-lap finish banner at capture poll #83, then the clean reset HUD after pressing Start alone at capture poll #174; capture polls are about three seconds apart, not Dolphin internal frame indices. This confirms the automated restart path, not human-controlled playability. Artifacts: [DOL](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40111152677/artifacts/12566602823), [headless smoke](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40111152677/artifacts/12566124749), and [finish/restart diagnostic bundle](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40111152677/artifacts/12566629556), expiring 31 October 2026.

All three gameplay PRs remain open with independent review requested; no formal review has been submitted yet, and nothing has been merged. The visible-Dolphin manual acceptance checklist stays pending and is deliberately deferred until the racing slice is more consolidated. It remains required before claiming full playability; physical GameCube/Wii compatibility is a separate later milestone.

## Current mainline and reproducible CI evidence

- **Most recent code-bearing main commit:** `72acf968e3214b086b00b77240bb20b889314917` (PR #204). Later main commits update only README/project-status documentation and do not change the tested game code.
- **Post-merge mainline CI:** [run #39062005581](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39062005581) completed successfully on that game-code tree: native DOL/ELF build and artifact validation, host pause/reset tests, Dolphin Null-backend smoke, and the non-blocking Software Renderer diagnostic all passed.
- **Player mesh/texture:** PR #203 is merged; it adds an original indexed twin-engine mesh, an original 16×16 RGB8 source texture, deterministic GX-ready headers and host-side format/quantization/tile-order tests. Its exact-head build, tests, and Dolphin diagnostics passed in [run #39051326423](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39051326423).
- **Finish banner and canyon:** PR #202 adds the readable finish label and guarded GX quad writes; PR #204 adds the varied canyon profile/fins. The exact-head PR #204 Software Renderer workflow [run #39057247310](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39057247310) detected both the centered three-lap finish banner and orange `FINISH` label on a DTM-scripted completion frame.
- **Headless smoke:** the 12-second Null-backend process check passed. This proves bounded startup/process behavior, not that a person can control the game.
- **Evidence limits:** the full-race result is scripted; the mainline push diagnostic itself was the shorter capture/steering check. Neither is a live user-controlled race, long-session stability test, or physical-console acceptance.

## What is now covered automatically

The clean-room prototype now has:
- native DOL/ELF compile and structural validation;
- deterministic host tests for steering, speed, boost/heat, lap boundaries, rivals, pause/reset and numeric state handling;
- a source-authored player mesh and RGB565 texture path with deterministic export and generated-header parity tests;
- scripted D-pad/analog steering, Y-reset, pause/resume, and a separate full-race finish-label diagnostic on PR #204;
- an original player mesh, rival craft, varied canyon skyline and readable finish panel visible in Software Renderer captures;
- bounded Dolphin startup smoke and non-blocking renderer diagnostics.

These checks cover only the behaviors and frames they assert; they do not establish manual playability.

## Still pending — interactive acceptance

The prototype has **not** been declared fully playable. A person must run the current mainline DOL in a visible Dolphin session with a configured controller, record the Dolphin version/backend/profile, and save the evidence described in [`NEXT_MILESTONE.md`](NEXT_MILESTONE.md).

Pending acceptance items:
- [ ] Start the scene in a visible Dolphin session without a fatal error.
- [ ] Use a real configured controller to verify reset (Y), including that all race state starts clean.
- [ ] Verify throttle/brake/coasting (A/B) by hand.
- [ ] Verify analog stick and D-pad directions, inertia and return-to-center by hand.
- [ ] Verify off-road slowdown and rail recovery in live play.
- [ ] Verify boost (X+A), energy recharge and overheat lockout in live play.
- [ ] Verify Start pause/resume, plus reset while paused.
- [ ] Complete a live three-lap race, confirm finish/stop, and reset into a new run.
- [ ] Play for several minutes without crashes, sustained graphical corruption or severe frame pacing problems.
- [ ] Record video/screenshots and notes including Dolphin version, video backend/mode and controller profile.

A CI-generated DTM, HUD assertion or rendered frame is valuable evidence, but does not satisfy the manual checklist. Dolphin results do not establish compatibility with physical GameCube/Wii hardware.

## Next engineering priorities

1. Finish the existing rail-collision, steering-deadzone, and finish/restart candidates with exact-head CI and appropriate independent review; avoid duplicate branches/tasks.
2. Refine handling, pitch/slide trade-offs, boost/heat feedback, rival behavior, camera stability, track readability, and collision as one coherent slice. Add narrow host regression tests for code-testable behavior changes.
3. Once this slice is consolidated, run the full visible-Dolphin checklist and collect player feedback. A scripted DTM or rendered frame does not satisfy the manual checklist.
4. After the race is reliable, expand original content (track variants, handling profiles, rivals, presentation, and progression).
5. Keep the €0 and clean-room constraints; do not merge stale branch histories wholesale or delete branches automatically.

## Restricted parallel track: Step 102

Step 102 source/archive imports remain on **provenance and licensing hold**. Keep that track separate from the clean-room runtime. Do not merge uncertain source or commercial assets until origin, authorship and redistribution rights have been established.
