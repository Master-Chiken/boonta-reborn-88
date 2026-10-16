# Boonta Reborn 88 — GameCube/Wii prototype

An unofficial research and homebrew project aiming toward an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), with GameCube/Wii as the primary native targets.

This repository contains two distinct tracks that must not be confused:

- **Clean-room demo** in `gamecube-demo/`: original procedural GX rendering and driving prototype, now using an authored closed-loop oval spline for the road, floor, canyon and racer placement. It includes steering, throttle/brake, boost with heat/cooldown, three procedural rivals, lap timing, and a three-lap finish marker. Host tests cover 50/60 Hz cadence, invalid-state guards, lap/finish transitions and rival behavior. Native DOL/ELF build, artifact validation and Dolphin process smoke pass in CI. The latest mainline CI [run #38948039632](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38948039632) passed host tests, native build, Dolphin headless smoke, and automated Software Renderer diagnostics for D-pad/analog-stick steering and the Y-reset HUD state; see the [diagnostic artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38948039632/artifacts/12066738177). An earlier run [#38899605111](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38899605111) captured the finish banner after a 12,000-poll scripted three-lap race. These are deterministic CI diagnostics, not manual acceptance: **live controller play, pause/reset interaction, current-head full-race acceptance, long-session frame pacing, and physical hardware remain unverified**.
- **Step 102 source prototype**: a separate source archive investigated for a fuller reconstruction. It is not automatically part of `main`; its provenance, license, generated course data, and any assets must be reviewed before importing or redistributing it.

## Rule for every future change

**Read [AGENTS.md](AGENTS.md) before planning or implementing any work.** It is the project's required pre-flight checklist for value, duplicate-work checks, scope, licensing/provenance, tests, review, and evidence. Do not start a new feature until its outcome, smallest useful scope, risks, and acceptance checks are clear.

## Project direction

- **Primary target:** native GameCube/Wii homebrew.
- **Current verified technical milestone:** main commit `cacec9c35d9a41258493c619368a6537d952a7a9` builds non-empty `boonta_gc_demo.dol` and `.elf` with devkitPPC/libogc, and [CI run #38948039632](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38948039632) passes native build/validation, host tests, Dolphin headless smoke, and automated steering/reset diagnostics. See [the current build status report](docs/GAMECUBE_FIRST_RENDER_STATUS.md).
- **Runtime evidence boundary:** run #38948039632 verifies scripted D-pad and analog-stick steering diagnostics plus a visible Y-reset state check on the current mainline. The prior [run #38899605111](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38899605111) showed a scripted three-lap finish banner on an earlier runtime-tested commit. Neither test proves live user-controlled racing, reset while paused, a current-head full-race acceptance run, sustained frame pacing, or physical-hardware compatibility.
- **Fuller gameplay baseline:** the Step 102 archive describes course/pod presets, racing physics, drift/boost/heat/damage, rival AI, pickups/hazards, race modes, HUD, and save/progression scaffolding. Treat those as archive-described scope, not as features verified in the clean-room demo.

## Current next milestones

1. Run the manual controller acceptance checklist in `docs/NEXT_MILESTONE.md`: stick/D-pad, A/B, X+A, Start, Y reset and live restart; record Dolphin version/backend and evidence.
2. Expand host regression coverage for camera-follow timing and lap/finish interactions. Host tests now also exercise repeated rival contacts across several successive frames, alongside pause, speed, boost, lap boundaries, and rival events.
3. Test a longer visible session for frame pacing, rendering stability, and recovery from off-road/rail contact.
4. Establish the playable vertical slice: one complete course, controllable pod, camera follow, collision, and clean finish/reset.
5. Continue the Step 102 source/license audit independently; import only files whose authorship and redistribution rights are clear. Keep build, visible rendering, scripted race, manual control, and physical hardware as separate acceptance gates.

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
