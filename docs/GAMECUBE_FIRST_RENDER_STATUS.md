# GameCube prototype status

Last updated: 2026-10-16

## Current mainline and reproducible CI evidence

- **Current main commit:** `e3adea9424268d7321113acc4ffc621242212dd9` — merge of PR #180, “test: verify visible Dolphin pause and resume states.”
- **Post-merge CI for this main commit:** [run #38957249755](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38957249755) was in progress during this status update. Its final result must be checked before claiming the new main commit has passed the full workflow.
- **Host tests:** pass for gameplay and pause/reset state, including the deterministic reset helper, multi-frame rival-contact bounds, and the newer reset/steering DTM protocol and visual-detector fixtures.
- **Native build:** `boonta_gc_demo.dol` and `.elf` built with devkitPPC/libogc; artifact structure validation passed.
- **Dolphin headless smoke:** the 12-second Null-backend process check passed. This proves bounded startup/process behavior, not that a person can control the game.
- **Automated visible-render diagnostics on PR #180 head:** [run #38954611194](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38954611194) completed successfully. In addition to D-pad/stick steering and Y-reset, it detected the visible pause icon, verified the pause overlay disappeared after Start-resume with throttle movement, and detected the three-lap finish banner after a 12,000-poll scripted DTM. See the [diagnostic artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38954611194/artifacts/12070108432). The full-race DTM was explicitly enabled on that PR; standard mainline runs do not necessarily repeat the long scenario.
- **Evidence limits:** the successful PR-head test used scripted inputs and the Software Renderer. It does not constitute a live user-controlled race, long-session stability test or physical-console acceptance.
- **Build status report:** this is automated CI evidence only. It must not be labelled as physical-controller, physical-console, or long-session acceptance.

## What is now covered automatically

The project has moved beyond a static first-render test:
- native DOL/ELF compile and structural validation;
- deterministic host tests for steering, speed, boost/heat, lap boundaries, rivals, pause, reset and finite-state handling;
- automated D-pad and analog-stick movie inputs with Software Renderer response checks;
- a Y-reset movie that first changes the race state and then checks a visibly clean reset HUD;
- scripted Start pause/resume checks that assert a visible pause overlay and throttle-driven movement after resuming;
- an opt-in scripted three-lap movie with a finish-banner detector;
- bounded Dolphin startup smoke and renderer diagnostics.

These improvements make regressions easier to detect, but **DTM playback is still scripted input**, not a physical controller test.

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
