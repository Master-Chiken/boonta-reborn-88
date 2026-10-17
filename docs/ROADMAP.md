# Boonta Reborn 88 – Project Roadmap

Last updated: 2026-10-18

**Goal**  
Create a faithful, enhanced and playable fan remaster inspired by *Star Wars: Episode I – Racer* (1999), targeting GameCube and/or Wii. The project is unofficial and clean-room first. Gameplay quality and original-game content take precedence over visual upgrades; bonus content and DLC-style ideas come last.

---

## Non-negotiable development priority

**Follow this order. Do not skip ahead because a later phase is more exciting:**

1. **Gameplay first — absolute priority.** Make the game work and feel right: responsive controls, speed, steering, boost/heat, collisions, rival interactions, camera, lap logic, finish, pause, reset/restart, stability and frame pacing. Prove these in a visible, manually controlled Dolphin session before treating the vertical slice as accepted.
2. **Original game content second.** Reconstruct or restore the core *Episode I – Racer* experience: original-game tracks, pods/vehicles, racing flow, rivals, progression, and recognizable course identity, using only code/assets/data with documented provenance and lawful redistribution status. Prioritize the essential original experience over adding new material.
3. **Graphics and remaster polish third.** Improve track readability, pod models, materials, effects, lighting, HUD and performance only after the gameplay foundation is reliable and the core original content is underway. Measure GameCube and Wii constraints separately; “HD++” is a long-term quality vision, not a claim of native HD output on legacy hardware.
4. **Bonus content and DLC-style expansions last.** New tracks/pods, bonus modes, extra packs, “HD+++ Premium” ideas and broader remake-style ambitions are stretch goals. They must not delay gameplay acceptance or the core original content.

Use the engineering rule **“Make it work, make it good, make it fast”** in that order: first prove correct end-to-end behavior, then improve quality and maintainability, and only then optimize measured bottlenecks. This is a development gate, not permission to skip testing.

---

## Phase 0 – Foundations

**Status: prototype foundations and CI are in place; interactive acceptance is still open.**

- [x] Clean-room procedural GX prototype.
- [x] Basic driving, boost/heat, rivals, lap system and HUD.
- [x] Native DOL/ELF build, artifact validation and CI.
- [x] Host tests for deterministic gameplay, pause/reset, steering, collisions and state boundaries.
- [x] Dolphin headless process smoke.
- [x] Automated D-pad left/right and analog-stick left/right steering diagnostics.
- [x] Automated Y-reset scenario with a visible HUD-state assertion.
- [x] Scripted Start pause/resume visible-state checks passed on PR #180 head in [run #38954611194](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38954611194).
- [x] Original source-authored indexed player-pod mesh and 16×16 RGB8 texture are validated and deterministically exported to the native GX mesh / tiled RGB565 headers ([PR #203](https://github.com/Master-Chiken/boonta-reborn-88/pull/203), merged).
- [x] Readable `FINISH` label and varied procedural canyon skyline are integrated ([PR #202](https://github.com/Master-Chiken/boonta-reborn-88/pull/202), [PR #204](https://github.com/Master-Chiken/boonta-reborn-88/pull/204), merged).
- [x] Scripted three-lap finish-banner and orange `FINISH`-label pixel checks passed on PR #204 head in [run #39057247310](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39057247310); this was DTM-driven, not a manual race.
- [ ] **Manual controller + live finish/reset/restart acceptance** — current and highest-priority gate.
  → See [`NEXT_MILESTONE.md`](NEXT_MILESTONE.md) and [current test evidence/status](GAMECUBE_FIRST_RENDER_STATUS.md).

Automated movies and rendered frames prove only the specific scripted responses they test. They do **not** establish live-controller playability, longer-session stability or physical-console compatibility.

---

## Phase 1 – Gameplay: complete, responsive, stable racing

**Absolute priority. No broad content expansion or graphics overhaul before this phase passes.**

- Responsive and correctly calibrated controls; acceleration, braking, steering inertia and coasting.
- Boost, heat, cooldown and consistent speed response.
- Reliable road boundaries, off-road slowdown, rail collisions/recovery and rival interactions.
- Stable camera and clear sense of speed.
- Correct lap timing/counting, finish state, pause, reset and restart.
- Stable frame pacing (target 60 fps or a solid 30 fps, based on measured feasibility).
- Basic gameplay-critical audio feedback where feasible.

**Exit criteria:** visible Dolphin session with a configured controller; complete manually driven three-lap race; finish, stop, reset and restart work; several minutes of play without sustained corruption or crash; exact tested commit and evidence recorded. Physical GameCube/Wii acceptance requires a separate real-hardware run.

---

## Phase 2 – Core original-game content

**Recreate the essential original racing experience before adding new content.**

- Establish a track-by-track content inventory and implementation plan for the original game’s recognizable circuits.
- Reconstruct course layouts, landmarks, racing lines and course-specific hazards from documented, permitted references.
- Implement the core roster of pods/vehicles and distinguish them through meaningful, tested handling/stat differences.
- Improve rival behavior and race flow to support the intended course experience.
- Build the necessary menus, HUD, race selection, progression and core sound feedback.
- Review every proposed source, model, texture, audio file and data set for provenance and redistribution rights before integration. Prefer clean-room reimplementation or original replacements where rights are unclear.

**Exit criteria:** the core race loop is reliable and a documented, coherent slice of original-game content is playable end to end. Do not treat unclear Step 102 archive content or commercial assets as cleared.

---

## Phase 3 – Graphics and remaster polish

**Begin only after Phase 1 is accepted and Phase 2 has a clear, working content foundation.**

- Improve original or rights-cleared pod and track visuals, materials, effects, animation and environment readability.
- Refine camera presentation, HUD legibility, menus and visual feedback without harming responsiveness.
- Profile and optimize rendering and memory use against actual GameCube and Wii constraints.
- Define exactly what “HD” means for each target. Console output, replacement assets, rendering changes and emulator upscaling are not equivalent.
- Validate performance separately on each intended target; do not promise native 720p/1080p output on legacy hardware.

**Exit criteria:** measured visual improvements that preserve the accepted gameplay and meet target-specific performance budgets.

---

## Phase 4 – Bonus content and DLC-style stretch goals

**Optional and last in priority. These ideas must not block Phases 1–3.**

- New original or provenance-cleared tracks and pods.
- Bonus modes such as Time Trial or Versus, plus quality-of-life options.
- Additional content packs or DLC-style expansions.
- The aspirational HD+++ Premium tier or a broader Racer-inspired remake-style experience, only if technically feasible and rights-compatible.
- Wii-specific enhancements where testing demonstrates a real benefit.

Treat these as future possibilities, not implemented features or commitments. Reassess scope only after the core game and original content are in good shape.

---

## Parallel / Restricted Track

**Step 102 source archive** remains under strict import hold until full provenance, authorship and licence review is complete. No commercial ROMs, extracted proprietary assets, or unclear code may enter the public repository. Research findings may guide clean-room implementation but do not automatically grant permission to copy source or data.

---

## Engineering rules

1. **Gameplay before content; original content before graphics; graphics before bonuses/DLC.**
2. **Make it work, make it good, make it fast — in that order.**
3. One coherent, manually verified playable slice before broad expansion.
4. Keep CI green and report exactly what each check proves; automated tests, compilation, headless startup, scripted rendering, interactive play and hardware testing are different gates.
5. Interactive playability matters more than feature, branch or PR count.
6. Clean-room first; publish only original or redistribution-cleared code/assets.
7. No automatic merges, no force-pushes to another contributor’s branch, and no destructive cleanup of history.
8. Legal caution over speed.

## How to follow progress

- Current acceptance gate → `docs/NEXT_MILESTONE.md`
- Build/runtime evidence → `docs/GAMECUBE_FIRST_RENDER_STATUS.md`
- Overall plan and mandatory priority order → this file
