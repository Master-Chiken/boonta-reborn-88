# Version comparison matrix — PC, Dreamcast, Nintendo 64, GameCube/Wii

## Purpose

This document turns the project's actual goal into a verifiable reverse-engineering plan: reconstruct the original *Star Wars: Episode I — Racer* experience as faithfully as possible on native GameCube/Wii, then improve presentation and add clearly identified bonus content.

Do not fill cells from memory or assumptions. For every finding, record the evidence: exact game/version, test setup, observation or document path, and confidence. Keep game images and extracted proprietary payloads local; publish only notes, original code, and material that is cleared for redistribution.

## Evidence labels

- **Observed** — reproduced in a lawful local run with steps/screenshots/video or measured output recorded privately.
- **Documented** — stated by a named technical document or source file; cite its path and revision.
- **Inferred** — plausible explanation supported by evidence but not confirmed.
- **Unknown** — not yet tested or sourced.

## Comparison backlog

| Subsystem | PC edition | Dreamcast edition | Nintendo 64 edition | GameCube/Wii target | Required research |
|---|---|---|---|---|---|
| Main loop and timing | PC reverse-engineering repository and local test | Inspect local edition | Inspect local edition | Stable frame/update model | Determine simulation tick, frame dependence, pause behavior and timing limits |
| Vehicle physics | Compare code/documentation and measured runs | Measure independently | Measure independently | Match the selected baseline | Acceleration, braking, steering, drift, air behavior, collisions, boost, heat and damage |
| Vehicle roster/statistics | Catalog and verify | Compare differences | Compare differences | Preserve roster and recognizable handling | Identify canonical values and edition-specific changes |
| Tracks and route geometry | Inspect documented PC formats; note any mod-derived data separately | Identify format and differences | Identify format and differences | Reconstruct course layouts with legally cleared data or original re-created geometry | Layout, split paths, shortcuts, lap gates, hazards, collision boundaries and landmarks |
| Rival AI | Trace documented functions; record observed behavior | Observe rival behavior | Observe rival behavior | Reimplement equivalent behavior | Racing line, passing, recovery, difficulty, rubber-banding if present, and start behavior |
| Pickups and hazards | Inventory and test | Compare | Compare | Match original behavior before adding new items | Spawn rules, effects, cooldowns, stacking, and AI use |
| Race modes and progression | Inventory modes and unlock conditions | Compare | Compare | Recreate intended modes and progression | Single race, championship, time trial, mirrored/reverse modes if present, unlocks and save data |
| Menus, HUD and controls | Document layout and inputs | Compare platform-specific controls | Compare platform-specific controls | GameCube controller-first UI | Navigation, pause, results, lap/speed/position displays and accessibility of controls |
| Graphics and effects | Inspect rendering features, not just extracted assets | Compare visual tradeoffs | Compare visual tradeoffs | Fit within GameCube/Wii hardware limits | Geometry, textures, lighting, draw distance, particles, transparency, camera and frame rate |
| Audio | Inventory behavior and format only | Compare | Compare | Use cleared/original replacement assets where necessary | Engine pitch, music transitions, UI cues, positional effects and memory budget |
| Save/progression | Document format and behavior | Compare | Compare | Use a platform-appropriate implementation | Save slots, unlock persistence, failure recovery and data integrity |
| Performance and memory | Record baseline where measurable | Record baseline where measurable | Record baseline where measurable | Profile on emulator and hardware where available | CPU/GPU timing, RAM/ARAM, streaming, worst-case scenes and stable frame pacing |

## Source and data provenance

- docs/TECHNICAL_RESEARCH.md lists PC reverse-engineering, OpenSWE1R, SWE1R asset tooling, and Wii64/Cube64 references. Treat these as research leads, not proof of compatibility with console assets.
- docs/STEP102_IMPORT_AUDIT.md documents the Step 102 archive's missing explicit license, its identified PC-mod-derived course centerlines, and assets that require individual provenance review.
- Do not import PC-mod-derived centerline files or unclear models, textures, audio, ROMs, disc images, BIOS files, or extracted commercial payloads into the public repository.
- A legally obtained local copy can be used for private testing where lawful, but ownership alone does not grant redistribution rights. Prefer clean-room notes and independently written implementations unless code/asset reuse is clearly authorized.

## Acceptance gates

1. The Step 102 source-only candidate has a documented provenance decision for every imported file group.
2. Its host tests pass without weakening the checks; the native GameCube DOL builds.
3. Interactive testing verifies boot, rendering, controller input, and a complete race in Dolphin or on hardware.
4. A faithful playable vertical slice covers at least one complete course, vehicle selection/configuration as appropriate, rivals, laps, finish/results, and the core handling/boost systems.
5. Each subsystem in this matrix is either implemented with evidence or explicitly recorded as a known difference.
6. Only after the baseline is faithful and stable do graphics enhancements and bonus features become the priority.

## Evidence log template

For each experiment, record:

- **Edition/build:**
- **Question:**
- **Setup and reproducible steps:**
- **Observed result:**
- **Evidence location (keep proprietary captures/data private if needed):**
- **Conclusion and confidence:**
- **Implication for GameCube/Wii implementation:**
