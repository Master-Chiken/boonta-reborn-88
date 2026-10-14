# Boonta Reborn 88 — GameCube/Wii prototype

An unofficial research and homebrew project aiming toward an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), with GameCube/Wii as the primary native targets.

This is **not yet a finished remaster or verified native port**. The source-only Step 102 prototype is now imported on the open draft PR branch. The devkitPPC/libogc build succeeds and produces a 307,428-byte `swe1r_gc_port.dol`. A headless Dolphin smoke test also passed: the emulator remained active for 20 seconds without a detected fatal error. Visible rendering and actual gameplay still need verification.

## Project direction

- **Primary target:** native GameCube/Wii homebrew prototype.
- **Imported source baseline:** Step 102 native C gameplay/rendering code, the GameCube Makefile, tools, and host-side tests now live in `source/`, `data/`, `tools/`, `tests/`, and the root `Makefile` on PR #22's working branch.
- **Prototype scope described by its README:** 25-course catalog, 23 vehicle presets/variants, racing physics, drift/boost/heat/damage, rival AI, pickups/hazards, single race, championship, time trial, Mirror Cup, HUD, and save/progression scaffolding.
- **Host tests:** the source-import GitHub Actions workflow passed all 32 host shell checks and 5 Python policy tests. The native-build workflow also passed its static source preflight; the first compiler attempt exposed outdated libogc constants, which are being corrected. Host tests are not runtime proof.
- **Native executable:** GitHub Actions produced a non-empty `swe1r_gc_port.dol` (307,428 bytes) and `swe1r_gc_port.elf` (~1.5 MB), available in the build artifact. The headless Dolphin smoke test kept the emulator active for 20 seconds with no detected fatal error. This does **not** prove visible rendering, controller input, or a completed race.
- **Separate exploratory track:** `dreamcast/` is a small clean-room KallistiOS starter. It is not the main game prototype and must not be confused with the GameCube/Wii code.

## Current repository limitation

The native-build workflow passes the source check, static preflight, host regression suite, and native build. The headless Dolphin smoke test also passes. Next: capture/inspect the rendered scene and verify controller input and a complete race.

## Legal and asset policy

- Do not commit commercial ROMs, disc images, BIOS files, extracted proprietary textures/models/audio, or other copyrighted game payloads.
- The source prototype documents that some course centerlines derive from a modded PC spline dataset; review provenance and redistribution rights before publishing those generated data files.
- Review the license and provenance of external reverse-engineering projects before reusing their code.
- Keep any lawful user-owned game images local. The repository should contain original code, documentation, tools, tests, and assets that are cleared for redistribution only.

## Next milestones

1. Import and review the source-only GameCube/Wii prototype, excluding ROMs/disc images and assets with unclear redistribution rights.
2. Run the host regression suite in GitHub Actions.
3. Build the native GameCube `.dol` using devkitPPC/libogc in CI and archive the build log/artifact.
4. Test the DOL in Dolphin; record boot, rendering, controls, and failures separately from compile success.
5. Improve one vertical slice: a single course, one controllable pod, stable camera, track collision, and frame timing.
6. Only after that slice works, expand assets, progression, presentation, and packaging.

The Dreamcast test branch is separate and is not a substitute for these milestones.


## Optional AI-assisted workflow

A GitHub-hosted Gemini agent can review the repository and help prepare code changes from GitHub comments. Setup and safety rules: [AI automation guide](docs/AI_AUTOMATION_SETUP.md). It only sees files committed to this repository; ChatGPT uploads of the original PC/N64 games are not automatically available to it.
