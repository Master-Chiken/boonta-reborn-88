# Platform behavior and verification matrix

This file connects the imported Step102 module structure to regression checks and to the external PC research reference. It is a navigation map for ongoing work, not a statement that every feature is fully playable.

| Area | GameCube/Wii implementation | Existing host-side checks | What remains to verify |
|---|---|---|---|
| Build and input loop | `source/main.c`, `Makefile` | `tests/test_native_syntax_host.sh`, native devkitPPC build | Boot in visible Dolphin; confirm menu, pause, reset and real controller mapping |
| Vehicle physics and steering | `source/racer_physics.c`, `source/track_direction.c` | `tests/test_physics_host.sh`, `tests/test_high_speed_steering_host.sh`, `tests/test_track_direction_host.sh` | Test analog/digital handling, high speed control, frame pacing and feel in emulator/hardware |
| Course geometry and traversal | `source/track_catalog.c`, `source/track_centerline.generated.h`, `source/race_gate_geometry.c` | `tests/test_track_catalog_host.sh`, `tests/test_track_projection_continuity_host.sh`, `tests/test_race_gate_geometry_host.sh` | Verify visible route bounds and lap/checkpoint progression; current fallback is a demo/procedural course, not the imported PC-mod courses |
| Collision and pickups | `source/collision_mesh.c`, `source/race_items.c` | `tests/test_collision_mesh_host.sh`, `tests/test_race_items_host.sh`, `tests/test_track_lateral_boundary_host.sh` | Confirm in-game collisions and items behave as intended at runtime |
| Rival AI and race flow | `source/rival_ai.c`, `source/race_flow.c`, `source/race_standings.c` | `tests/test_ai_difficulty_host.sh`, `tests/test_race_flow_host.sh`, `tests/test_race_standings_host.sh`, `tests/test_finish_line_crossing_host.sh` | Verify a complete race with visible rivals, lap count, finish order and reset |
| Race modes and championship | `source/race_mode_select.c`, `source/championship.c` | `tests/test_race_mode_select_host.sh`, `tests/test_championship_host.sh`, `tests/test_full_session_host.sh` | Exercise mode selection and a full championship session interactively |
| Garage and save progression | `source/garage_progression.c`, `source/career_save.c` | `tests/test_garage_progression_host.sh`, `tests/test_career_save_host.sh`, `tests/test_career_card_syntax_host.sh` | Test actual GameCube memory-card behaviour on hardware or an explicitly configured emulator memory card |
| Models, text and rendering | `source/pod_model.c`, `source/game_text.c`, `source/main.c` | `tests/test_pod_model_host.sh`, native DOL build | Inspect a captured visible Dolphin frame; verify text, models, camera and rendering quality |
| Voice/audio | `source/voice_over.c`, `source/voice_over_runtime.c` | `tests/test_voice_over_runtime_host.sh`, where applicable | Voice/audio media files were excluded due unclear redistribution provenance; audio asset integration is intentionally unfinished |

## How to use SW_RACER_RE

[SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) is a PC decompilation/modding reference, not a portable GameCube implementation. When researching expected behavior, document a specific upstream file/function and the observed behavior, then write a separate test for our implementation. Do not directly import PC hooks or files from its repository without a deliberate AGPL/licensing review.

See [reference-project and licensing notes](REFERENCE_PROJECTS.md).

## Current verified baseline

- Source-only import and provenance path checker: passed in GitHub Actions.
- Host regression suite: passed.
- Native devkitPPC/libogc compile: passed, producing `swe1r_gc_port.dol` (about 301 KiB).
- Headless null-backend Dolphin process smoke test: passed.
- A separate visible-frame capture workflow is being hardened; until its screenshot artifact has been inspected, **visible rendering and gameplay are unverified**.
- Step102 source provenance/license review is still required before PR #17 can be merged.

Results: [source-only import validation run](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38628014235) and [current native-build workflow](https://github.com/Master-Chiken/boonta-reborn-88/actions).
