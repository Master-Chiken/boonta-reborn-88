# GameCube prototype status

Last updated: 2026-10-24


## Owner priority update — 2026-10-24

Continue implementation and automated regression work now; do not wait for a physical controller or a final player playtest before advancing the racing slice. Complete and review the current candidates first:

- [PR #214 — width-aware rail collision](https://github.com/Master-Chiken/boonta-reborn-88/pull/214), current head `b25c4614aa9694bdcb65d5f813854e3a08860532`. The new source-contract tests and roadmap updates are under CI: host tests passed; the native GameCube build is running in [workflow #40099360797](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40099360797).
- [PR #247 — analog steering deadzone](https://github.com/Master-Chiken/boonta-reborn-88/pull/247), current head `defd893f3c25fa240e24bc9524545ef1d12d4b4f`. All required policy checks and all four GameCube workflow jobs passed in [workflow #40098910954](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40098910954).
- [PR #259 — Start restart after finish](https://github.com/Master-Chiken/boonta-reborn-88/pull/259), current head `827b63dff09055ed09e79d1ed06fabdda390208c`. All required policy checks and all four GameCube workflow jobs passed in [workflow #40098536014](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/40098536014).

The interactive checklist below remains pending until a person actually runs it. Defer the broad visible-Dolphin playtest until the gameplay slice is more consolidated so that players can give feedback on a coherent build. This is not a blanket blocker for independent code or test improvements. Real GameCube/Wii testing is a separate, later milestone. None of the CI evidence above means that manual playability or physical hardware compatibility has been established.


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
