# Next milestone: visible Dreamcast test scene

## Goal

Turn the existing clean-room Dreamcast starter into a small, visible technical demo before attempting any game-specific features. This is a prototype milestone, not a claim that the original commercial game has been ported.

## Current verified baseline

- The repository README reports that the KallistiOS starter has compiled in CI.
- The current starter is described as printing a console message and polling controller input.
- Emulator or real-hardware behavior has not yet been verified.
- The browser prototype is a separate track and must not be confused with the Dreamcast build.

## Work sequence

1. **Inspect the current build** — review `dreamcast/main.c`, `dreamcast/Makefile`, and the existing GitHub Actions workflow before changing code.
2. **Add a visible screen** — draw an original title screen with a simple background, a project label, and a controller-input indicator using APIs supported by the installed KallistiOS version.
3. **Show controller state** — display whether a controller is connected and which buttons are pressed, without assuming hardware has been tested.
4. **Build in CI** — use the existing workflow and check the build log. Fix compile errors before adding more features.
5. **Test the artifact** — run the generated ELF in a compatible Dreamcast emulator if one is available. Record emulator name/version and results; otherwise mark runtime testing as pending.
6. **Start an original 3D scene** — only after the visible screen is verified, add a simple original track-like scene using placeholder geometry.

## Acceptance criteria

- The existing CI build passes.
- The screen-drawing code is based on documented APIs available in the project's KallistiOS environment.
- Controller feedback is visible or its limitation is documented.
- Build success and runtime testing are reported separately.
- No commercial ROMs, disc images, BIOS files, or extracted proprietary assets are committed.

## What the project owner needs to do now

No local download is required for this planning step. Open the [repository Actions page](../actions) and check the latest `Dreamcast build` workflow run. If it is green, the next coding task is the visible test screen. If it is red, open the failed run and share the error text so the build can be fixed first.

## Legal and scope note

This is an unofficial research and original-code project. A technical prototype inspired by a racing game is not the same as a remaster of the original game. Use only original or appropriately licensed code and assets, and do not distribute copyrighted game data.
