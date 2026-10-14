# Dreamcast port investigation — Star Wars: Episode I – Racer

## Status

**Target platform under investigation: Sega Dreamcast.** The user supplied an archive named `Star Wars - Episode I - Racer (USA).7z` (about 314 MiB). The filename and size are consistent with known Dreamcast releases of this title, but the archive's internal file listing has not yet been verified in this environment. Treat the platform identification as probable, not confirmed, until the archive is inspected.

## Important separation from the existing prototype

The current `Star_Wars_Racer_GameCube_Step102` prototype is aimed at GameCube/Wii and its build workflow expects a GameCube/Wii toolchain and output such as a `.dol`. That code is **not a Dreamcast executable** and should not be presented as one. Dreamcast is a different architecture and SDK/toolchain target; a Dreamcast build typically uses KallistiOS (KOS) and produces a Dreamcast-compatible `.bin`/disc image rather than a GameCube `.dol`.

Keep the current GameCube/Wii prototype intact while investigating Dreamcast. Do not overwrite or relabel it as a Dreamcast port.

## Next technical steps

1. Inspect the supplied 7z archive's file list and confirm whether it contains a `.gdi`, `.cdi`, `.bin`, `.cue`, or other disc-image components. Do not commit the commercial game disc image or extracted proprietary game assets to this repository.
2. If it is a Dreamcast disc image, record only non-sensitive technical metadata and hashes locally; do not upload the image to GitHub.
3. Establish a clean Dreamcast homebrew skeleton in a separate directory (for example `dreamcast/`) using a documented KallistiOS setup. Start with a legally original test screen and controller input, not copied game code or proprietary assets.
4. Audit whether any existing prototype logic can be ported as platform-independent original code. Keep platform-specific graphics, audio, storage, and input behind separate interfaces.
5. Add a Dreamcast CI job only after a reproducible KOS build environment and a minimal clean-room source tree exist.

## Constraints and current blocker

The archive is present in the conversation runtime, but this environment currently lacks a 7z listing/extraction utility and cannot install one from the network. Therefore the archive's internal format and contents have not yet been confirmed. No Dreamcast binary has been built.
