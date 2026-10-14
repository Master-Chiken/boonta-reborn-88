# Boonta Reborn 88 — first GameCube driving prototype

This folder contains a **clean-room, original procedural 3D driving prototype** for the GameCube/Wii homebrew toolchain. It does not reuse commercial game code, models, textures, audio, or route data.

## Features implemented in code

- Procedural ring circuit with colored curbs, center markers, pylons, and a checkerboard finish marker.
- Original low-poly pod model with twin engine shapes and boost flames.
- Chase camera and a simple speed/boost/lap HUD.
- Acceleration, braking, boost energy and heat, lateral lane adjustment, pause, and restart.
- Three procedural rival racers with deterministic, smooth lane changes, simple contact penalties, an impact cooldown, and a player-position / impact-count HUD (1st–4th).
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

The GitHub Actions workflow compiles the C program with devkitPPC/libogc into a non-empty boonta_demo.dol and uploads it as a short-lived build artifact. The latest checked run also ran the portable race-logic host tests and a headless Dolphin process smoke test. This is **not** proof that visible rendering or controller input work: Dolphin used a null video backend and stayed alive during a short process-only check. The DOL still needs an interactive test in Dolphin or on physical hardware.

See [PR #13](https://github.com/Master-Chiken/boonta-reborn-88/pull/13) and its [successful Actions run](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38613665560).

## Build in the cloud

The repository contains a Codespaces dev-container configuration and a [cloud-development guide](../docs/CLOUD_DEV_WORKFLOW.md). No local toolchain needs to be installed. Codespaces usage is limited on free personal plans; stop it when idle and never enable paid billing for this project.

## Important limitations

- This is a first gameplay experiment, not the complete Step 102 prototype and not a remaster.
- The rivals are simple procedural placeholders; they are not the original game's opponent AI.
- Contact is currently a lightweight prototype rule based on angular and lateral proximity; it is not yet full collision physics or advanced rival AI.
- There are no imported original tracks, menus, championship/save system, final art, or final audio.
- The full Step 102 archive remains outside the repository while code licensing, third-party provenance, and asset redistribution rights are reviewed.
- The DOL needs actual interactive emulator/hardware validation before we call the prototype playable.

No commercial ROM, disc image, or extracted commercial game asset belongs in this directory.