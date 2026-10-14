# Boonta Reborn 88 — GameCube/Wii prototype

An unofficial research and homebrew project aiming toward an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), with GameCube/Wii as the primary native targets.

This is **not yet a finished remaster or verified port of the original game**. A separate clean-room GameCube prototype now compiles to a DOL in GitHub Actions. The full Step 102 racing prototype has not been imported, and the new DOL has not yet been runtime-tested in Dolphin or on hardware.

## Project direction

- **Primary target:** native GameCube/Wii homebrew prototype.
- **Existing source of truth:** `Star_Wars_Racer_GameCube_Step102.zip`, audited separately from this repository. It contains C gameplay/rendering code, a GameCube Makefile, research/build tools, documentation, and host-side tests.
- **Prototype scope described by its README:** 25-course catalog, 23 vehicle presets/variants, racing physics, drift/boost/heat/damage, rival AI, pickups/hazards, single race, championship, time trial, Mirror Cup, HUD, and save/progression scaffolding.
- **Host tests:** I ran the archive's host release suite in a clean temporary environment. All host shell checks and 91 Python unit tests passed after restoring the executable bits encoded in the ZIP. This is not a native GameCube build and is not a runtime test.
- **First native DOL:** `gamecube/boonta_demo.dol` is built by CI from original procedural code. This verifies the toolchain and compilation only, not emulator boot or playability.
- **Separate exploratory track:** `dreamcast/` is a small clean-room KallistiOS starter. It is not the main game prototype and must not be confused with the GameCube/Wii code.

## Current repository limitation

The full Step 102 source prototype has **not yet been imported**. The separate clean-room prototype in `gamecube/` now contains a procedural 3D loop track, original pod, chase camera, HUD, acceleration/braking/boost, lane adjustment, pause, and a three-lap finish condition. CI confirms a DOL is produced; actual runtime validation remains outstanding. See [`gamecube/README.md`](gamecube/README.md).

## Legal and asset policy

- Do not commit commercial ROMs, disc images, BIOS files, extracted proprietary textures/models/audio, or other copyrighted game payloads.
- The source prototype documents that some course centerlines derive from a modded PC spline dataset; review provenance and redistribution rights before publishing those generated data files.
- Review the license and provenance of external reverse-engineering projects before reusing their code.
- Keep any lawful user-owned game images local. The repository should contain original code, documentation, tools, tests, and assets that are cleared for redistribution only.

## Next milestones

1. Test the current `boonta_demo.dol` in Dolphin and record boot, graphics, controller input, and any crash/log evidence.
2. Complete the Step 102 source/asset provenance audit and create a safe import list.
3. Import only cleared source code, headers, tests, build tools, and documentation; keep uncertain route data and commercial assets out.
4. Run the source prototype's host regression suite in GitHub Actions.
5. Build the full source prototype with devkitPPC/libogc only after import and host tests are ready.
6. Improve the playable slice and expand content only after runtime validation.

The Dreamcast test branch is separate and is not a substitute for these milestones.


## Cloud development (no local installation)

The repository includes a Codespaces dev-container for working in the browser with the devkitPPC/GameCube toolchain. See [Cloud development workflow](docs/CLOUD_DEV_WORKFLOW.md). Codespaces has usage quotas on free personal plans; stop or delete the cloud workspace when finished.

## Free development tools

The project is intended to stay at **€0**: see [Free tooling and setup requirements](docs/FREE_TOOLING.md) for GitHub Actions, the Codespaces quota, the optional Gemini agent, and the actions that still require the owner. Do not enable paid billing.

## Optional AI-assisted workflow

A GitHub-hosted Gemini agent can review the repository and help prepare code changes from GitHub comments. Setup and safety rules: [AI automation guide](docs/AI_AUTOMATION_SETUP.md). It only sees files committed to this repository; ChatGPT uploads of the original PC/N64 games are not automatically available to it.
