# GameCube first-render / driving-input prototype

This directory is a **clean-room, original technical slice** for Boonta Reborn 88. It is separate from the unreviewed Step 102 source bundle and contains no extracted game code, commercial assets, models, textures, music, voices, ROMs, or disc images.

## Current scope

- Native GameCube GX initialization and 3D colored-vertex rendering.
- A procedural scrolling curved road with edge strips and barrier rails.
- An original placeholder twin-engine hover craft built from primitive geometry.
- GameCube controller steering with lateral inertia, off-road speed loss, and rail-edge recovery, plus throttle and brake. Off-road drag and rail-bounce boundaries are covered by strict host unit tests.
- Three clean-room procedural rival craft approach at staggered intervals, change lanes with independent phases, can collide with the player, and can be overtaken; up to eight overtake markers are shown in the HUD.
- A basic speed bar, steering-position tick, rechargeable boost-energy meter, overheat/cooldown bar, race clock, current-lap timer and best-lap display, lap-progress bar, repeating start/finish stripe, and three completed-lap indicators (the prototype's configured race limit).
- A Start-button pause toggle with a visible pause icon; gameplay simulation freezes while paused.
- A reproducible CI build that uploads the resulting DOL and ELF if compilation succeeds.

This is a gameplay prototype, not the completed racer and not a port of the commercial game. Rival behavior is deliberately simple and scripted; collision response and overtake counting are prototypes, not a full physics or race-position system. Audio, saves, a title menu, and a full physics model are not implemented.

## Controls

- Control Stick left/right (or D-pad): steer.
- A: accelerate.
- B: brake.
- Hold X + A: engage boost while accelerating; energy drains and recharges on release. Heat rises during boost; at 98% heat, boost locks out until the engine cools to 60% or below.
- Start: toggle pause/resume; the pause icon appears in the center of the HUD.
- Y: reset the run, lap counter, rival, overtake indicators, and pause state.

## Build

Use the official devkitPro GameCube/Wii environment (devkitPPC + libogc). In a configured shell, run:

```sh
make clean
make
```

The expected files are `boonta_gc_demo.dol` and `boonta_gc_demo.elf`. GitHub Actions runs the same build in the `devkitpro/devkitppc` container and keeps successful outputs as a short-retention artifact.

## Latest CI build and visible-render evidence

The latest recorded clean-room prototype validation is [GameCube first-render run #69](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727969531). The host gameplay/pause tests, native devkitPPC/libogc build, DOL/ELF structure checks, and bounded headless Dolphin process smoke passed. The optional [Software Renderer capture and logs](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727969531/artifacts/11970040471) show the procedural road, colored rails, center markers, player pod, and rival pod.

This proves that a visible prototype scene renders in the CI Dolphin Software Renderer environment. It does **not** prove a complete playable racer. See the [build status report](../docs/GAMECUBE_FIRST_RENDER_STATUS.md) for evidence and limitations.

## Runtime validation still required

The remaining acceptance checks are interactive steering, acceleration/braking, boost and overheat cooldown, pause/resume (the clocks should freeze), reset (all clocks should return to zero), completion of a three-lap run with current/best lap timing, and longer-session stability. A screenshot or headless process smoke cannot verify controller response or race completion. Physical GameCube/Wii behavior is also unverified. Record the Dolphin version/backend or console setup and the outcome when performing an interactive test.

## Source boundary

The C source and geometry here are original procedural scaffolding created for this repository. Do not add Step 102 source, third-party mod data, or commercial game content to this folder unless provenance and redistribution rights are separately cleared.

## What the automated Dolphin checks prove

The scripted DTM comparison is an **input-path smoke diagnostic**. It checks that expected scene colors render, that the cyan player-pod surface shifts between neutral and right-input captures, and that the HUD steering-state marker changes. If the pod reaches the image border, the diagnostic reports a quality warning rather than silently treating the frame as an ideal steering result.

This is evidence of a **visible response to scripted input in Dolphin's Software Renderer**, not proof of representative handling, track-relative motion, use of a real controller, or a completed race.

Keep validation claims separate:

- **Host tests and native DOL/ELF build:** the tested code compiles and its deterministic helper tests pass.
- **Dolphin null-video smoke:** the emulator process accepts/runs the DOL for the bounded smoke window; this is not visual verification.
- **Software-renderer input diagnostic:** scene signatures, visible player-pod displacement, and the independent HUD marker are compared against a neutral baseline.
- **Interactive steering and complete race:** still require a visible Dolphin session (or physical hardware) with an actual controller profile, acceleration/braking/steering, three lap crossings, finish, reset, and evidence recorded against the tested commit.

Do not report the scripted capture as proof that the game is fully playable. Follow the interactive acceptance checklist in `../docs/NEXT_MILESTONE.md`.

