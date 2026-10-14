# Boonta Reborn 88 — GameCube/Wii project

An unofficial research and homebrew project aiming toward an enhanced, playable racing experience inspired by Star Wars: Episode I – Racer (1999), with Nintendo GameCube/Wii as the primary native targets.

**This is not a finished remaster or verified port.** The repository contains research, planning, build automation, a separate Dreamcast starter, and draft work toward a clean-room GameCube demo. The previously supplied Step 102 source prototype has not yet been imported into main.

## Start here

- [Current status and continuity map](docs/PROJECT_STATUS_AND_MAP.md) — what exists, where it lives, and what each test result does and does not prove.
- [Source and artifact register](docs/SOURCE_AND_ARTIFACT_REGISTER.md) — previously supplied inputs, upstream research links, and rules for safe import.
- [Project plan](docs/PROJECT_PLAN.md) — phases, decisions, and acceptance criteria.
- [Technical research](docs/TECHNICAL_RESEARCH.md) — external research and platform trade-offs.
- [Next milestone](docs/NEXT_MILESTONE.md) — the path from source audit to a playable vertical slice.
- [Build guide](docs/BUILD_GUIDE.md) — target-specific build evidence and known limits.
- [AI automation setup](docs/AI_AUTOMATION_SETUP.md) — free-only/tool safety and setup requirements.

## Current repository state

- **Main branch:** project documentation, GitHub workflows, and a small Dreamcast/KallistiOS experiment. The Dreamcast path is not the main GameCube/Wii project.
- **Step 102 archive:** supplied separately in the ChatGPT conversation. It is a candidate source baseline, but its full path-by-path provenance and redistribution review is not complete. ChatGPT uploads do not automatically become GitHub files or become visible to GitHub-hosted agents.
- **PR #13 — GameCube demo:** [open draft pull request](https://github.com/Master-Chiken/boonta-reborn-88/pull/13). It adds a clean-room procedural racing demo and a native build workflow. Its latest checked CI run [succeeded](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38615309738), but this is a separate demo, not the Step 102 source and not visual/input verification.
- **PR #14 — OpenRouter Free review:** [merged](https://github.com/Master-Chiken/boonta-reborn-88/pull/14). It is a manually triggered, comment-only review helper. It needs a repository secret to run, sends a capped public PR diff to an external service, and has no paid fallback.
- **PR #15 — Gemini safety hardening:** [draft](https://github.com/Master-Chiken/boonta-reborn-88/pull/15). Its proposed changes are not active on main until reviewed and merged.

## Intended native project scope

The Step 102 prototype README describes a larger set of systems: a course catalog, pod presets, racing physics, drift/boost/heat/damage, rival AI, pickups/hazards, race modes, HUD, and progression scaffolding. Those are descriptions of the archive, not features currently confirmed in the main branch.

The near-term goal is to audit and import only cleared source, run the source prototype's host tests in GitHub Actions, produce a native GameCube DOL with devkitPPC/libogc, and then verify boot, graphics, and controller input in an interactive emulator or on hardware. Compilation, a headless process test, and actual gameplay are separate validation stages.

## Safety and redistribution

- Do not commit commercial ROMs, disc images, BIOS files, or uncleared extracted textures, models, audio, or other proprietary payloads.
- Review source licenses, provenance, generated course data, and redistribution rights before import.
- Keep private game archives out of public issues, CI artifacts, AI reviewer prompts, and public releases.
- Do not enable billing or a paid API/model fallback to keep an automation running.
- Record actual test evidence and do not describe a successful compile as a working playable game.

The repository is unofficial and is not affiliated with or endorsed by the original rights holders.