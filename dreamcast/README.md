# Dreamcast starter — Boonta Reborn 88

This directory contains a **separate, clean-room Dreamcast homebrew starter**. It is not a port of the existing GameCube/Wii executable and contains no commercial game image or extracted proprietary assets.

## Current smoke test

The current branch adds a visible video-output smoke test using KallistiOS's PowerVR API:

- Initializes the PVR renderer.
- Renders a frame continuously.
- Shows a dark teal background when a controller is detected, a blue background while a button is pressed, and a purple background when no controller is detected.
- Continues to print diagnostic messages through the configured KOS console output.

This is deliberately a minimal video/controller check, **not yet a game menu or a racing scene**.

## Build status

The original starter compiled in GitHub Actions. The new visible-screen change must pass its own CI build before it can be considered compile-verified. Neither this screen nor gameplay has yet been confirmed in an emulator or on a physical Dreamcast.

The automated workflow uses the KallistiOS toolchain container configured in [the Dreamcast workflow](../.github/workflows/dreamcast-build.yml). You do not need to install this toolchain to see the CI build result.

To build locally, install and configure [KallistiOS](https://github.com/KallistiOS/KallistiOS), set `KOS_BASE`, load the KOS environment, and run `make` from this directory.

## Next milestones

1. Confirm this branch compiles in CI.
2. Run the ELF in a compatible emulator, if available.
3. Add an original 3D scene using placeholder geometry.
4. Add visible controller indicators and then basic vehicle movement.

## Legal / asset boundary

Use only original code and assets you have the right to use. Do not commit a commercial disc image, BIOS, or extracted copyrighted game assets to this repository.
