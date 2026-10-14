# Boonta Reborn 88 — enhanced GameCube/Wii reconstruction

An unofficial reverse-engineering and homebrew project aiming to reconstruct the original *Star Wars: Episode I – Racer* (1999) as faithfully as possible, using documented PC research and comparisons with the PC, Dreamcast, and Nintendo 64 editions. The target is an enhanced, genuinely playable native GameCube/Wii release, with improved graphics and additional bonus content. This is the destination, not the current completion status.

This is **not yet a finished remaster or verified port of the original game**. A separate clean-room GameCube prototype now compiles to a DOL in GitHub Actions. The full Step 102 racing prototype has not been imported, and the new DOL has not yet been runtime-tested in Dolphin or on hardware.

## Actual end goal

- **Final goal:** a faithful reconstruction of the original game's core experience, adapted to run natively on GameCube/Wii, then enhanced with improved graphics, extras and bonus content.
- **Research inputs:** existing PC reverse-engineering documentation/code, the PC edition, and lawful local analysis of Dreamcast and Nintendo 64 editions. Compare versions to identify gameplay rules, data formats, track/vehicle differences and platform-specific behavior; do not assume one edition's formats match another.
- **Current source candidate:** `Star_Wars_Racer_GameCube_Step102.zip`, audited separately from this repository. It is the strongest existing GameCube/Wii-oriented prototype candidate, but its provenance and assets still require review. It contains C gameplay/rendering code, a GameCube Makefile, research/build tools, documentation, and host-side tests.
- **Prototype scope described by its README:** 25-course catalog, 23 vehicle presets/variants, racing physics, drift/boost/heat/damage, rival AI, pickups/hazards, single race, championship, time trial, Mirror Cup, HUD, and save/progression scaffolding.
- **Host tests:** I ran the archive's host release suite in a clean temporary environment. All host shell checks and 91 Python unit tests passed after restoring the executable bits encoded in the ZIP. This is not a native GameCube build and is not a runtime test.
- **First native DOL:** `gamecube/boonta_demo.dol` is built by CI from original procedural code. This verifies the toolchain and compilation only, not emulator boot or playability.
- **Separate exploratory track:** `dreamcast/` is a small clean-room KallistiOS starter. It is not the main game prototype and must not be confused with the GameCube/Wii code.

## Current repository limitation

The current repository is still far short of the final goal: the full Step 102 source prototype has **not yet been imported**. The separate clean-room prototype in `gamecube/` now contains a procedural 3D loop track, original pod, chase camera, HUD, acceleration/braking/boost, lane adjustment, pause, and a three-lap finish condition. CI confirms a DOL is produced; actual runtime validation remains outstanding. See [`gamecube/README.md`](gamecube/README.md).

## Legal and asset policy

- Do not commit commercial ROMs, disc images, BIOS files, extracted proprietary textures/models/audio, or other copyrighted game payloads.
- The source prototype documents that some course centerlines derive from a modded PC spline dataset; review provenance and redistribution rights before publishing those generated data files.
- Review the license and provenance of external reverse-engineering projects before reusing their code.
- Keep any lawful user-owned game images local. The repository should contain original code, documentation, tools, tests, and assets that are cleared for redistribution only.

## Reverse-engineering workbench

The [PC/Dreamcast/Nintendo 64 comparison matrix](docs/VERSION_COMPARISON_MATRIX.md) tracks the systems that must be measured or documented before implementation: physics, vehicles, tracks, AI, items, modes, UI, graphics, audio, progression, and performance. The goal is faithful reconstruction first, visual improvements and bonus content second.

## Next milestones toward the real goal

1. Complete a path-by-path provenance review of the Step 102 source archive and select the code/tools/docs that can be safely used.
2. Build the actual full GameCube/Wii-oriented prototype from that source, not treat the tiny procedural demo as the final foundation.
3. Reproduce the host tests, compile with devkitPPC/libogc, and validate boot/render/controller input in Dolphin.
4. Create a version-comparison matrix for PC, Dreamcast and Nintendo 64: physics, tracks, vehicle stats, AI, items, menus, modes, progression, and file formats. Mark each claim as measured, documented, or still unknown.
5. Reconstruct and validate original gameplay systems and content using documented reverse-engineering findings; keep proprietary ROMs/disc images and unclear extracted assets outside the public repository.
6. Once the faithful playable baseline works, improve graphics within GameCube/Wii limits, add original bonus content, and measure performance on both targets.
7. Package and document GameCube and Wii builds separately.

The Dreamcast test branch is separate and is not a substitute for these milestones.


## Cloud development (no local installation)

The repository includes a Codespaces dev-container for working in the browser with the devkitPPC/GameCube toolchain. See [Cloud development workflow](docs/CLOUD_DEV_WORKFLOW.md). Codespaces has usage quotas on free personal plans; stop or delete the cloud workspace when finished.

## Free development tools

The project is intended to stay at **€0**: see [Free tooling and setup requirements](docs/FREE_TOOLING.md) for GitHub Actions, the Codespaces quota, the optional Gemini agent, and the actions that still require the owner. Do not enable paid billing.

## Optional AI-assisted workflow

A GitHub-hosted Gemini agent can review the repository and help prepare code changes from GitHub comments. Setup and safety rules: [AI automation guide](docs/AI_AUTOMATION_SETUP.md). It only sees files committed to this repository; ChatGPT uploads of the original PC/N64 games are not automatically available to it.
