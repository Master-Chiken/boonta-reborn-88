# Boonta Reborn 88 — GameCube/Wii prototype

An unofficial research and homebrew project aiming toward an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), with GameCube/Wii as the primary native targets.

This repository contains two distinct tracks that must not be confused:

- **Clean-room demo** in `gamecube-demo/`: original procedural GX rendering and driving prototype, including steering, throttle/brake, rechargeable boost, lap-progress cues, and a three-lap prototype run with a symbolic checkered finish marker. Its native devkitPPC/libogc build has been verified in GitHub Actions. Visible rendering and controller behavior still require a visible Dolphin or hardware test; a headless Dolphin process smoke test passes but cannot verify graphics or controls.
- **Step 102 source prototype**: a separate source archive investigated for a fuller reconstruction. It is not automatically part of `main`; its provenance, license, generated course data, and any assets must be reviewed before importing or redistributing it.

## Project direction

- **Primary target:** native GameCube/Wii homebrew.
- **Current verified technical milestone:** `gamecube-demo/` produces a non-empty `boonta_gc_demo.dol` and `boonta_gc_demo.elf` with devkitPPC/libogc. See [the build status report](docs/GAMECUBE_FIRST_RENDER_STATUS.md).
- **Runtime status:** a 12-second Dolphin process smoke test with the null video backend now passes in CI ([run #49](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38722692467)). This confirms the DOL process stayed active, not that the game rendered visibly, accepted controller input, or completed a race. Those runtime checks remain open.
- **Fuller gameplay baseline:** the Step 102 archive describes course/pod presets, racing physics, drift/boost/heat/damage, rival AI, pickups/hazards, race modes, HUD, and save/progression scaffolding. Treat those as archive-described scope, not as features verified in the clean-room demo.

## Current next milestones

1. Run the clean-room DOL in a visible Dolphin session or on suitable hardware and record emulator/version, video backend, visible scene, and controller results.
2. Extend the host-side state tests to cover collision/overtake edge cases and frame/lap interactions; pause, speed, boost-meter and lap-boundary transitions are already covered.
3. Establish a compact playable vertical slice: one course, controllable pod, camera follow, track collision, and stable frame timing.
4. Continue the Step 102 source and license audit independently. Import only source/data whose authorship and redistribution rights are clear.
5. Keep compile, headless process smoke tests, visible rendering, controller input, and a completed race as separate acceptance gates.

## Legal and asset policy

- Do not commit commercial ROMs, disc images, BIOS files, extracted proprietary textures/models/audio, or other copyrighted game payloads.
- The Step 102 source archive identifies course centerlines derived from a modded PC spline dataset; review provenance and redistribution rights before publishing those generated data files.
- Review the license and provenance of external reverse-engineering projects before reusing code.
- Keep any lawful user-owned game images local. The public repository should contain original code, documentation, tools, tests, and assets cleared for redistribution only.

## Native build and runtime evidence

See [GameCube first-render status](docs/GAMECUBE_FIRST_RENDER_STATUS.md) and [the prototype build instructions](gamecube-demo/README.md). Successful CI artifacts are temporary workflow outputs and are not necessarily committed into the repository.

The separate `dreamcast/` starter is an exploratory KallistiOS experiment. It is not a substitute for the GameCube/Wii target.

## Optional AI-assisted workflow

A GitHub-hosted Gemini agent can review the repository and help prepare code changes from GitHub comments. Setup and safety rules: [AI automation guide](docs/AI_AUTOMATION_SETUP.md). It only sees files committed to this repository; ChatGPT uploads of the original PC/N64 games are not automatically available to it.
