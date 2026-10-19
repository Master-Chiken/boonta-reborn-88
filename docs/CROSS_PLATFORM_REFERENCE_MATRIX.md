# Cross-platform reference matrix — Boonta Reborn

Status date: 2026-10-15. This is a research checklist, not a claim that the prototype already reproduces the original game.

## Source inventory and safe use

| Edition | Material currently identified | Best use | Important limitation |
|---|---|---|---|
| Windows PC | User-supplied `Game SW Racer 1999.zip`; public `SW_RACER_RE`, `swe1r-tools`, `blender-swe1r` research | Primary technical reference for spline traversal, track formats, object/model blocks, game-state functions, and established modding workflows | The PC executable and extracted game assets stay local. Function-analysis coverage is not the same as a complete reimplementation. |
| Nintendo 64 | User-supplied `SW Racer 1999- (US).z64`; Step 102 archive includes N64 extraction/inventory notes and an `export_n64_track.py` tool candidate | Compare course layout, progress/checkpoint logic, coordinate transforms, and original handling against a local N64 run | ROM is never committed. Any extracted track data or tooling must be checked for origin, license, and redistribution rights. |
| GameCube / Wii | User-supplied `Star_Wars_Racer_GameCube_Step102.zip`; current clean-room GameCube DOL prototype | Examine the supplied source/tool archive after path-by-path review; test the GameCube/Wii toolchain and input/rendering feasibility | Archive inventory reports 359 files and marks no file cleared for redistribution. The procedural DOL is not yet a faithful or visibly verified game. |
| Dreamcast | Mentioned as a required comparison platform; no distinct Dreamcast archive/image is confirmed in the currently visible Library inventory | Keep an explicit row in the comparison plan; compare only after identifying the supplied Dreamcast source and a lawful local test setup | No Dreamcast-specific file-format or runtime conclusion is currently verified. Do not infer it from the PC or console editions. |

## Subsystem comparison checklist

| System | PC reference | N64 reference | GameCube/Wii reference | Dreamcast reference | Required evidence before porting |
|---|---|---|---|---|---|
| Track centerline / spline | Public reverse-engineering and modding work documents spline/path usage | Local ROM research and candidate extraction tooling | Review archive tooling; current demo uses a clean-room sampled polyline | Pending source identification | Sample at least one course, compare route length and turns, and test closed-loop wrap and alternate branches with synthetic fixtures |
| Lap, checkpoints, respawn | Inspect original functions and modding docs | Compare local behavior and N64 notes | Current prototype has three-lap state; not yet original checkpoint/respawn behavior | Pending | Reproduce start/finish crossing, lap count, respawn point, wrong-way behavior, and alternate-path joins |
| Pod physics / handling | Main baseline for function-level study | Measure against the local N64 edition | Current clean-room acceleration/boost is provisional | Pending | Record reproducible acceleration, steering, boost/heat, ground contact, and collision scenarios; avoid tuning to a single frame rate |
| Rival AI / race position | Research AI flags, rival state, and progress logic | Compare AI/rival behavior in local gameplay | Current prototype has three deterministic placeholder rivals | Pending | Test all rivals, overtaking, lane behavior, progress across the finish line, and full race results |
| Models, textures, audio | Use format documentation and catalog only until provenance is clear | Keep extracted material local | Audit each archive path and license before any import | Pending | Record source/version/license and create original or permission-cleared replacements for public builds |
| Controller / rendering / performance | PC reference only; not directly portable | Emulator reference is not native-console proof | Native DOL build passes; visible Dolphin frame capture still fails | Pending | Separate compiler success, emulator process start, visible rendered frame, controller input, full race, and real-hardware results |

## Current code-level checkpoint

- `gamecube/source/track_path.c` provides clean-room sampled-polyline primitives: path length, progress/distance sampling, tangent, and nearest-segment projection.
- `gamecube/source/race_logic.c` now uses track length for player/rival progress when a valid path length is supplied. Contact detection converts a 2.5-unit world-space threshold into normalized lap-angle space; the old angular threshold remains as fallback.
- Latest PR-triggered host evidence: `race_logic_test: 16 suites passed`; `track_path_test: 6 suites passed`. The GameCube DOL build passed. The optional Dolphin OpenGL diagnostic exited before capturing a frame, so visible gameplay is not verified.
- The latest code/docs are on `audit/step102-import-gate`. Do not merge into `main` without explicit authorization.

## Next research tasks

1. Review the supplied Step 102 archive's source/tool license and provenance register; do not wholesale-import its 171 code/tool/test candidates.
2. Compare the candidate PC spline exporter and N64 track exporter by reading their formats and tests, then document a platform-neutral intermediate track schema without importing proprietary route coordinates.
3. Add synthetic fixtures for coordinate transforms, track-width boundaries, branch/rejoin continuity, checkpoints, and respawn.
4. Identify the Dreamcast source artifact before making any Dreamcast-specific claims.
5. Build a per-platform validation log that records source version, emulator/version/settings, test case, result, and whether the result was compile-only, process-only, visually observed, or hardware-confirmed.
