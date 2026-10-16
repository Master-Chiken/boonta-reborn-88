# Next milestone: Interactive validation of the clean-room racing slice

Last updated: 2026-10-16

## Goal of this milestone

Prove that the current clean-room prototype in `gamecube-demo/` is **actually playable** with a real controller in a visible Dolphin session (and later on real hardware).

This is the gate before expanding the vertical slice.

## What is already verified (CI)

- Host regression tests (speed, boost/overheat, steering, lap boundaries, rivals, pause/reset, finite-state guards, etc.)
- Consistent 50/60 Hz cadence handling
- Native `boonta_gc_demo.dol` / `.elf` build with devkitPPC/libogc
- Bounded Dolphin null-video smoke
- Visible Software Renderer capture (road, rails, markers, player + rival pods)

These prove the code compiles, the deterministic logic works, and a scene can render.  
They do **not** yet prove live controller response or a completed three-lap race.

## New automated evidence on current main (2026-10-16)

The latest CI on main commit `cacec9c35d9a41258493c619368a6537d952a7a9` is [run #38948039632](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38948039632). It passed host tests, native DOL/ELF build and validation, Dolphin Null-backend smoke, and the non-blocking Software Renderer diagnostic. Automated input diagnostics now include D-pad steering, analog-stick left/right steering and a Y-reset HUD assertion. See the [captured diagnostic artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38948039632/artifacts/12066738177).

These are deterministic movie-driven emulator tests. They do **not** complete any of the manual controller acceptance items below; leave the checklist pending until someone records an actual visible Dolphin session with a configured controller.


## Interactive acceptance checklist

Load the latest mainline DOL in a **visible** Dolphin session.  
Record: Dolphin version, video backend, video mode, controller profile, and evidence (short video or screenshots + notes).

Test in this exact order:

1. **Reset (Y)**  
   Pod returns to start position, speed and lap counters reset, rivals and overtake markers reset, boost refilled, pause/finish state cleared.

2. **Throttle / Brake (A / B)**  
   Acceleration and braking visibly change speed. Speed falls naturally when released.

3. **Steering**  
   Control Stick left/right + D-pad. Correct direction, inertia present, drift damps when released, steering stays bounded.

4. **Off-road & rails**  
   Drive off the road → speed loss visible. Rail recovery works without freezing or breaking rendering.

5. **Boost (X + A)**  
   Energy drains while boosting, recharges after release. Overheat lockout behaves correctly.

6. **Pause (Start)**  
   Pause icon appears, simulation freezes. Resume works. Reset (Y) while paused is clean.

7. **Full three-lap race**  
   Three lap crossings counted correctly. Finish flag appears. Movement stops after the race limit. Reset allows a new run.

8. **Longer session**  
   Several minutes of play. No sustained graphical corruption, crashes, or severe frame pacing issues.

### Acceptance criteria

- [ ] Scene starts without fatal error
- [ ] All controls above behave as described
- [ ] Three-lap race reaches finish and stops cleanly
- [ ] Reset starts a fresh run
- [ ] No sustained corruption or crash in longer session
- [ ] CI host tests + native build still pass on the exact commit tested
- [ ] Evidence recorded (video/screenshots + notes)

Any item not tested remains **pending**. Do not claim hardware compatibility from Dolphin alone.

## After this milestone

Once the interactive checklist is fully green:

1. Fix any bugs found during the session and add regression tests.
2. Improve the procedural track, camera and collision as one coherent vertical slice.
3. Only then expand content (more tracks, pods, AI, presentation, bonuses).

## Parallel track (do not mix)

Step 102 source archive remains on **import hold**.  
See `SOURCE_IMPORT_GATE.md` and related Step 102 documents.  
Do not merge unclear-provenance code or any commercial assets.
