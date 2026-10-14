# Dreamcast port investigation — Star Wars: Episode I – Racer

## Status (updated 2026-10-14)

**Target platform under investigation: Sega Dreamcast.** The supplied archive has not been inspected internally in this environment, so its exact contents are not confirmed.

A separate, clean-room Dreamcast homebrew starter now exists in `dreamcast/`. The GitHub Actions workflow successfully compiled it with KallistiOS and uploaded the ELF artifact in run [38568111117](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38568111117). This confirms the toolchain and starter compile; it does **not** confirm gameplay, on-console operation, or a port of the commercial game.

## Keep the tracks separate

The existing GameCube/Wii prototype is not a Dreamcast executable. Dreamcast is a different architecture and toolchain. Keep the GameCube/Wii research and Dreamcast starter separate; do not overwrite or relabel one as the other.

## Next technical steps

1. Add a simple video mode and visible original test screen using documented KallistiOS APIs.
2. Read controller input reliably and display changing input state on screen.
3. Add an original, minimal 3D scene and camera only after the video/input smoke test is stable.
4. Keep platform-independent gameplay logic separate from platform-specific graphics, audio, storage, and input.
5. Test on an emulator or real Dreamcast when available; until then, label CI compilation as compile-only validation.
6. Inspect the supplied archive locally only if needed to confirm its format. Do not upload it to GitHub.

## Legal and asset boundary

Use original code and assets you have the right to use. Do not commit a commercial disc image, BIOS, or extracted proprietary game assets to this repository. Keep any legally obtained game image local and comply with applicable law.

## Current limitations

- CI compiles the clean-room starter to an ELF and stores it as an artifact.
- The starter currently prints a message through KOS console output and polls the first controller.
- No video scene, race track, vehicle physics, audio, or commercial game assets are implemented.
- No successful emulator or real-hardware test has been recorded.
