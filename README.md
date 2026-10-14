# Boonta Reborn 88 — GameCube/Wii prototype

An unofficial research and homebrew project aiming toward an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), with GameCube/Wii as the primary native targets.

This is **not yet a finished remaster or verified native port**. The main blocker is to bring the existing Step 102 source prototype into this GitHub repository, run its host-side regression suite in CI, and obtain the first real devkitPPC/libogc GameCube build.

## Project direction

- **Primary target:** native GameCube/Wii homebrew prototype.
- **Existing source of truth:** `Star_Wars_Racer_GameCube_Step102.zip`, audited separately from this repository. It contains C gameplay/rendering code, a GameCube Makefile, research/build tools, documentation, and host-side tests.
- **Prototype scope described by its README:** 25-course catalog, 23 vehicle presets/variants, racing physics, drift/boost/heat/damage, rival AI, pickups/hazards, single race, championship, time trial, Mirror Cup, HUD, and save/progression scaffolding.
- **Host tests:** The full Step 102 archive previously passed its host release suite, including 91 Python unit tests, in a clean temporary environment. Separately, the 123-file source-only bundle passed 32 shell regression checks and 5 Python policy tests (see [`docs/STEP102_HOST_VALIDATION.md`](docs/STEP102_HOST_VALIDATION.md)). These are host-side checks, not GitHub Actions results, a native GameCube build, or a runtime test.
- **Native executable:** no verified `.dol` is currently present in this GitHub repository. A real devkitPPC/libogc cross-build and Dolphin/console boot test remain outstanding.
- **Separate exploratory track:** `dreamcast/` is a small clean-room KallistiOS starter. It is not the main game prototype and must not be confused with the GameCube/Wii code.

## Current repository limitation

The source-only bundle is still being reviewed separately. Its files have **not yet been imported into this repository**; source provenance and redistribution permissions must be reviewed before import. See [`docs/SOURCE_IMPORT_GATE.md`](docs/SOURCE_IMPORT_GATE.md). Until an approved source subset is imported, this repository cannot produce the game's DOL.

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
