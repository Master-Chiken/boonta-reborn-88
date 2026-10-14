# Dreamcast starter — Boonta Reborn 88

This directory contains a **separate, clean-room Dreamcast homebrew starter**. It is not a port of the existing GameCube/Wii executable and contains no commercial game image or extracted proprietary assets.

## Build status

The GitHub Actions workflow successfully compiled this starter with the KallistiOS toolchain and uploaded an ELF artifact in [workflow run 38568111117](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38568111117).

This is compile-only validation. The binary has not yet been confirmed running in an emulator or on a physical Dreamcast.

## What it currently does

- Starts with KallistiOS.
- Prints a short status message through the configured KOS console output.
- Polls the first Maple controller and reports pressed-button values to the console.

It does **not** yet render a visible game scene, race track, vehicle, audio, or gameplay.

## Build environment

The automated workflow uses the KallistiOS toolchain container configured in [the Dreamcast workflow](../.github/workflows/dreamcast-build.yml). You do not need to install this toolchain to see the CI build result.

To build locally, install and configure [KallistiOS](https://github.com/KallistiOS/KallistiOS), set `KOS_BASE`, load the KOS environment, and run `make` from this directory.

## Next milestone

1. Render a visible original test screen.
2. Verify controller input and display the state on screen.
3. Establish a basic 3D scene before adding racing physics.

## Legal / asset boundary

Use only original code and assets you have the right to use. Do not commit a commercial disc image, BIOS, or extracted copyrighted game assets to this repository.
