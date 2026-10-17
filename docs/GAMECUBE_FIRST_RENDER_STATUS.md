# GameCube prototype status

Last updated: 2026-10-17

## Current mainline and reproducible CI evidence

- **Current main commit:** `8b7c9a8a1e19e6a14eccc182103120e835400b4b` — README-only follow-up. The most recent game-code merge is `72acf968e3214b086b00b77240bb20b889314917` (PR #204).
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

1. Complete the interactive acceptance checklist and turn any reproducible failure into a regression test.
2. Keep extending automated tests only where they close a clear gap; do not substitute more scripted frames for live play evidence.
3. Fix confirmed input, race-finish/reset, camera or collision defects.
4. Improve track/camera/collision feel as one coherent playable vertical slice before adding more content.
5. Review unique branch diffs against current `main`; never merge stale branch histories wholesale or delete branches automatically.

## Restricted parallel track: Step 102

Step 102 source/archive imports remain on **provenance and licensing hold**. Keep that track separate from the clean-room runtime. Do not merge uncertain source or commercial assets until origin, authorship and redistribution rights have been established.
