# Next milestone: Finish and refine the clean-room racing slice

Last updated: 2026-10-24

## Owner priority update

Continue implementation and automated testing now; do not wait for physical-controller testing before advancing gameplay. Finish the current rail-collision, steering-deadzone, and finish/restart work, then refine handling, rival behavior, camera, and track readability in small, testable changes. Defer the broader visible-Dolphin playtest until the race slice is more consolidated, when testers can provide more useful feedback. Physical GameCube/Wii testing comes later still.

The manual checklist below remains required before claiming the prototype is fully playable. It is not a blanket blocker for independent code, design, or automated-test improvements. Keep test claims evidence-based, keep the €0/tooling and clean-room constraints, and do not merge without appropriate independent review and required checks.

## Goal of this milestone

Build and refine the current clean-room prototype in `gamecube-demo/` into a convincing, stable racing slice. Use host tests, native builds, and scripted Dolphin diagnostics for development; reserve human-operated visible-Dolphin acceptance for the consolidated candidate, then test physical hardware separately.

The manual acceptance checklist is the gate for declaring full playability, not a reason to pause all vertical-slice development.

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

The tests remain scripted. Keep every item in the checklist below pending until a person records a visible Dolphin session with a configured emulated GameCube controller. They also do not establish physical GameCube/Wii compatibility.

## Interactive acceptance checklist

Load the latest mainline DOL in a **visible** Dolphin session. If no physical controller is available, use the [keyboard-only Dolphin setup](DOLPHIN_KEYBOARD_TEST.md); it uses Dolphin's existing emulated GameCube controller rather than requiring a new input layer in Boonta.  
Record: Dolphin version, video backend, video mode, selected input device/profile, and evidence (short video or screenshots + notes).

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

## Next development steps

Continue this work before the manual acceptance session:

1. Finish review and integration of the existing rail-collision, steering-deadzone, and restart changes, with green exact-head CI.
2. Refine handling, pitch/slide trade-offs, boost/heat feedback, rivals, camera and course readability as one coherent vertical slice; add focused host regression tests for behavior changes.
3. Consolidate the candidate build and then run the visible-Dolphin checklist below, recording PASS / FAIL / NOT TESTED honestly.
4. Once the manual race is reliable, expand content (more original tracks, craft profiles, rival tactics, presentation and progression). Physical GameCube/Wii testing remains a later, separate check.

## Parallel track (do not mix)

Step 102 source archive remains on **import hold**.  
See `SOURCE_IMPORT_GATE.md` and related Step 102 documents.  
Do not merge unclear-provenance code or any commercial assets.
