# Boonta Reborn 88 — first GameCube driving prototype

This folder contains a **clean-room, original procedural 3D driving prototype** for the GameCube/Wii homebrew toolchain. It does not reuse commercial game code, models, textures, audio, or route data.

## Features implemented in code

- Procedural ring circuit with colored curbs, center markers, pylons, and a checkerboard finish marker.
- Original low-poly pod model with twin engine shapes and boost flames.
- Chase camera and a simple speed/boost/lap HUD.
- Acceleration, braking, boost energy and heat, lateral lane adjustment, pause, and restart.
- Three-lap finish condition.

## Controls

| Button | Action |
|---|---|
| A | Accelerate |
| B | Brake |
| X | Boost |
| D-pad Left / Right | Adjust lane position |
| START | Pause / resume |
| Y | Reset race or restart after finish |

## What has been verified

The GitHub Actions workflow compiles the C program with devkitPPC/libogc into a non-empty `boonta_demo.dol` and uploads it as a short-lived build artifact. This is a **compile result only**. The DOL has not yet been confirmed to boot in Dolphin or on physical hardware, and the visual/gameplay behavior must still be tested.

The current build run is linked from the [repository Actions page](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-smoke.yml).

## Build in the cloud

The repository contains a Codespaces dev-container configuration and a [cloud-development guide](../docs/CLOUD_DEV_WORKFLOW.md). No local toolchain needs to be installed. Codespaces usage is limited on free personal plans; stop it when idle and never enable paid billing for this project.

## Important limitations

- This is a first gameplay experiment, not the complete Step 102 prototype, and not a remaster.
- There are no rival racers, imported original tracks, menus, championship/save system, or final art/audio yet.
- The full Step 102 archive remains outside the repository while code licensing, third-party provenance, and asset redistribution rights are reviewed.
- The DOL needs an actual emulator/hardware runtime test before we call the prototype playable.

No commercial ROM, disc image, or extracted commercial game asset belongs in this directory.
