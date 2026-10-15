# GameCube first-render / driving-input prototype

This directory is a **clean-room, original technical slice** for Boonta Reborn 88. It is separate from the unreviewed Step 102 source bundle and contains no extracted game code, commercial assets, models, textures, music, voices, ROMs, or disc images.

## Current scope

- Native GameCube GX initialization and 3D colored-vertex rendering.
- A procedural scrolling curved road with edge strips and barrier rails.
- An original placeholder twin-engine hover craft built from primitive geometry.
- GameCube controller steering with lateral inertia, off-road speed loss, and rail-edge recovery, plus throttle and brake.
- A clean-room procedural rival craft that approaches the player, changes lanes, can collide with the player, and can be overtaken; up to eight overtake markers are shown in the HUD.
- A basic speed bar, steering-position tick, rechargeable boost-energy meter, lap-progress bar, repeating start/finish stripe, and five completed-lap indicators.
- A Start-button pause toggle with a visible pause icon; gameplay simulation freezes while paused.
- A reproducible CI build that uploads the resulting DOL and ELF if compilation succeeds.

This is a gameplay prototype, not the completed racer and not a port of the commercial game. Rival behavior is deliberately simple and scripted; collision response and overtake counting are prototypes, not a full physics or race-position system. Audio, saves, a title menu, a full physics model, and multi-rival race logic are not implemented.

## Controls

- Control Stick left/right (or D-pad): steer.
- A: accelerate.
- B: brake.
- Hold X + A: engage boost while accelerating; the energy meter drains and recharges when boost is released.
- Start: toggle pause/resume; the pause icon appears in the center of the HUD.
- Y: reset the run, lap counter, rival, overtake indicators, and pause state.

## Build

Use the official devkitPro GameCube/Wii environment (devkitPPC + libogc). In a configured shell, run:

```sh
make clean
make
```

The expected files are `boonta_gc_demo.dol` and `boonta_gc_demo.elf`. GitHub Actions runs the same build in the `devkitpro/devkitppc` container and keeps successful outputs as a short-retention artifact.

## Latest native build

The first successful devkitPPC/libogc build completed in [GitHub Actions run 38633619707](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38634127716). It produced a non-empty DOL and ELF artifact. This confirms compilation/linking only; **Dolphin/console runtime testing is still pending**. See the [build status report](../docs/GAMECUBE_FIRST_RENDER_STATUS.md) for artifact sizes, hashes, and runtime checklist.

## Runtime validation

A successful compiler exit proves only that the code compiled. Load the DOL in Dolphin or suitable hardware and confirm: visible road/pod, steering response, throttle/brake response, no obvious GX crash, and reset behavior. No runtime result is claimed by this README until such a test is performed.

## Source boundary

The C source and geometry here are original procedural scaffolding created for this repository. Do not add Step 102 source, third-party mod data, or commercial game content to this folder unless provenance and redistribution rights are separately cleared.
