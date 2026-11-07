# Next milestone: Interactive validation of the clean-room racing slice

Last updated: 2026-11-02

## Goal of this milestone

Prove that the current clean-room prototype in `gamecube-demo/` is **actually playable** with a real controller in a visible Dolphin session (and later on real hardware).

This is the gate before expanding the vertical slice.

## What is already verified (CI)

- Host regression tests for gameplay state, steering, boost/heat, lap boundaries, rivals, pause/reset and numeric state guards.
- Native `boonta_gc_demo.dol` / `.elf` build using devkitPPC/libogc with artifact validation.
- Bounded Dolphin Null-backend process smoke.
- Source-authored indexed twin-engine player mesh (275 vertices, 169 triangles) with an original 16×16 RGB8 texture source, validated and deterministically exported to GX-ready C headers.
- Readable three-lap finish panel and varied procedural canyon skyline.
- Exact-head Software Renderer diagnostics and visual detectors for steering/reset and the finished banner.

These prove the tested code compiles, deterministic assertions pass, and the tested scripted states can render. They do **not** prove live controller response or a manually driven three-lap race.

## Latest automated evidence (2026-10-17)

PR #202 (readable `FINISH` label), PR #203 (authored mesh/texture), and PR #204 (varied canyon) are now merged. The exact-head run [#39057247310](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39057247310) passed host tests, native build/artifact checks, Dolphin process smoke, and the Software Renderer diagnostic. Its scripted three-lap DTM frame passed both the centered finish-banner detector and orange `FINISH`-label detector.

Post-merge mainline run [#39062005581](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39062005581), executed on the game-code merge commit `72acf968e3214b086b00b77240bb20b889314917`, also passed its native DOL/ELF build, host pause/reset tests, Null-backend smoke and non-blocking Software Renderer diagnostic. That push run intentionally used the shorter capture/steering diagnostic rather than the long full-race DTM. Subsequent main commits update documentation only; the code-bearing tree validated by run #39062005581 has not changed. The live-controller checklist below remains the outstanding acceptance gate.

The tests remain scripted. Keep every item in the checklist below pending until a person records a visible Dolphin session with a configured controller. They also do not establish physical GameCube/Wii compatibility.

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


## Native Wii Classic Controller acceptance (separate from GameCube)

The native Wii backend is carried by [PR #269](https://github.com/Master-Chiken/boonta-reborn-88/pull/269), rebuilt on current `main` after the D-pad pitch prerequisite in [PR #264](https://github.com/Master-Chiken/boonta-reborn-88/pull/264) was integrated. The active branch is `feat/native-wii-classic-input-main-20261102`. PR #268 is the superseded stacked predecessor and is closed unmerged.

**Automated exact-head evidence for PR #269 (head `03a66d0c02e6cb39c51460ad75ad9a3a40aecc9c`):**

- Host input/gameplay tests — PASS.
- Native GameCube DOL/ELF build and artifact validation — PASS.
- Native Wii DOL/ELF build and artifact validation — PASS.
- Dolphin null-backend process smoke — PASS.
- Optional Software Renderer diagnostic — PASS; this is a scripted GameCube-pad diagnostic, not a Wii Classic Controller test.
- AI safety and source-import provenance checks — PASS.

**Manual hardware acceptance remains NOT TESTED and mandatory before merging PR #269:**

1. Load the Wii DOL on a real Wii with the Under Control controller connected through Wii Remote channel 0.
2. Confirm the runtime detects `WPAD_EXP_CLASSIC`; Wii Remote-only and non-Classic expansions must remain neutral.
3. Test left-stick steering/pitch, D-pad steering/pitch, A/B throttle/brake, X+A boost, ZL/ZR and analog L/R shoulders for slide, Plus pause/restart, and Y reset.
4. Disconnect and reconnect the controller; verify neutral input while disconnected and recovery only after Classic detection and report setup.
5. Record the Wii model, controller identification, exact tested build SHA, results, and video or notes.

The button masks and Classic expansion identifiers are cross-checked against the current upstream libogc `wpad.h`; its implementation also exposes the Classic shoulder values as normalized raw values divided by `0x1F`. This source check is not a substitute for a physical test.

Do not mark physical compatibility as passed from cross-compilation or Dolphin. The original N64 game running in Not64 is a separate input path and is not covered by this Boonta backend.
