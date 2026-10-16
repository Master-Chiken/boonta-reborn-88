# Boonta Reborn 88 — GameCube/Wii prototype

An unofficial research and homebrew project aiming toward an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), with GameCube/Wii as the primary native targets.

This repository contains two distinct tracks that must not be confused:

- **Clean-room demo** in `gamecube-demo/`: original procedural GX rendering and driving prototype on a closed-loop spline, with steering, throttle/brake, boost/heat, three procedural rivals, lap timing, HUD, pause/reset and a three-lap finish marker. PR #180 has been merged as `e3adea9424268d7321113acc4ffc621242212dd9`; it adds scripted visible pause/resume checks and an opt-in full-race diagnostic. The PR-head run [#38954611194](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38954611194) passed host tests, native DOL/ELF build/artifact validation, Dolphin headless smoke, steering/reset/pause/resume frame checks, and detected the finish banner after a 12,000-poll scripted race. The post-merge mainline workflow [#38957249755](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38957249755) is the current build verification for `e3adea9424268d7321113acc4ffc621242212dd9`; check its final result before treating that commit's CI as green. Scripted results are not manual acceptance: live controller play, full manual race/restart, long-session frame pacing and physical hardware remain unverified.
- **Step 102 source prototype**: a separate source archive investigated for a fuller reconstruction. It is not automatically part of `main`; its provenance, license, generated course data, and any assets must be reviewed before importing or redistributing it.

## Rule for every future change

**Read [AGENTS.md](AGENTS.md) before planning or implementing any work.** It is the project's required pre-flight checklist for value, duplicate-work checks, scope, licensing/provenance, tests, review, and evidence. Do not start a new feature until its outcome, smallest useful scope, risks, and acceptance checks are clear.

## Project direction

- **Primary target:** native GameCube/Wii homebrew.
- **Current mainline candidate:** commit `e3adea9424268d7321113acc4ffc621242212dd9` merges PR #180's pause/resume and race-finish diagnostics. Post-merge native build/test results are recorded in [CI run #38957249755](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38957249755); consult its final status rather than inferring success from the merge alone.
- **Runtime evidence boundary:** PR-head run [#38954611194](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38954611194) visibly detected steering response, Y-reset, pause/resume and the scripted three-lap finish banner. The longer full-race scenario is opt-in and was enabled for that PR; the ordinary mainline run does not always repeat the 12,000-poll race. None of this proves live user-controlled racing, sustained frame pacing or physical-hardware compatibility.
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
