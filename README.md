# Boonta Reborn 88 — GameCube/Wii prototype

An unofficial research and homebrew project aiming toward an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), with GameCube/Wii as the primary native targets.

This repository contains two distinct tracks that must not be confused:

- **Clean-room demo** in `gamecube-demo/`: original procedural GX rendering and driving prototype, including steering, throttle/brake, rechargeable boost, lap-progress cues, and a three-lap prototype run with a symbolic checkered finish marker. Rival collision/overtake thresholds have host tests. Its DOL/ELF build, artifact validation, 12-second Dolphin process smoke test, and a first visible frame captured with Dolphin's Software Renderer now pass in CI. The scene is still primitive; interactive controller behavior and completing a three-lap run are not yet verified.
- **Step 102 source prototype**: a separate source archive investigated for a fuller reconstruction. It is not automatically part of `main`; its provenance, license, generated course data, and any assets must be reviewed before importing or redistributing it.

## Project direction

- **Primary target:** native GameCube/Wii homebrew.
- **Current verified technical milestone:** `gamecube-demo/` produces a non-empty `boonta_gc_demo.dol` and `boonta_gc_demo.elf` with devkitPPC/libogc. See [the build status report](docs/GAMECUBE_FIRST_RENDER_STATUS.md).
- **Runtime status:** the latest recorded visible-render validation is [CI run #69](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727969531). Host tests, native build, artifact validation, and the 12-second Dolphin Null-backend smoke passed; its [Software Renderer frame artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727969531/artifacts/11970040471) shows the procedural road, colored rails, center markers, player pod and rival pod. This proves visible output in the CI renderer, not interactive controller response, a completed three-lap run, long-session stability, or physical-hardware behavior.
- **Fuller gameplay baseline:** the Step 102 archive describes course/pod presets, racing physics, drift/boost/heat/damage, rival AI, pickups/hazards, race modes, HUD, and save/progression scaffolding. Treat those as archive-described scope, not as features verified in the clean-room demo.

## Current next milestones

1. Verify controller input and a completed three-lap run in a visible Dolphin session or on suitable hardware; record emulator/version, video backend, and observed behavior.
2. Extend host-side tests for camera-follow timing, collision response over several frames, and lap/finish interactions; pause, speed, boost-meter, lap-boundary, rival-event, and race-finish transitions are already covered.
3. Establish a compact playable vertical slice: one course, controllable pod, camera follow, track collision, and stable frame timing.
4. Continue the Step 102 source and license audit independently. Import only source/data whose authorship and redistribution rights are clear.
5. Keep compile, headless process smoke tests, visible rendering, controller input, and a completed race as separate acceptance gates.

## Legal and asset policy

- Do not commit commercial ROMs, disc images, BIOS files, extracted proprietary textures/models/audio, or other copyrighted game payloads.
- The Step 102 source archive identifies course centerlines derived from a modded PC spline dataset; review provenance and redistribution rights before publishing those generated data files.
- Review the license and provenance of external reverse-engineering projects before reusing code.
- Keep any lawful user-owned game images local. The public repository should contain original code, documentation, tools, tests, and assets cleared for redistribution only.

## Wii64 reference tooling

Read-only tools now support inspecting Wii64 Rice profiles, comparing INI snapshots or named profiles, and checking fingerprints of a local Wii64 archive. Start with the [Wii64 reference tools guide](docs/WII64_REFERENCE_TOOLS.md). The tools never modify settings or extract/execute archive contents, and hash matches are not a safety or compatibility verdict.

The shared [Wii64 tooling workflow](.github/workflows/wii64-tool-tests.yml) runs the standard-library Python unit suite for changes under `tools/`. Physical Wii/vWii observations should be recorded with the [Wii64 test log template](docs/WII64_TEST_LOG_TEMPLATE.md). This reference work is separate from the native GameCube/Wii demo.

## Native build and runtime evidence

See [GameCube first-render status](docs/GAMECUBE_FIRST_RENDER_STATUS.md) and [the prototype build instructions](gamecube-demo/README.md). Successful CI artifacts are temporary workflow outputs and are not necessarily committed into the repository.

The separate `dreamcast/` starter is an exploratory KallistiOS experiment. It is not a substitute for the GameCube/Wii target.

## Optional AI-assisted workflow

A GitHub-hosted Gemini agent can review the repository and help prepare code changes from GitHub comments. Setup and safety rules: [AI automation guide](docs/AI_AUTOMATION_SETUP.md). It only sees files committed to this repository; ChatGPT uploads of the original PC/N64 games are not automatically available to it.
