# Cross-platform reference matrix — Boonta Reborn

Status date: 2026-11-07. This file began as a research checklist, not a claim that the prototype reproduces the original game.

> **Historical snapshot warning:** parts of this 2026-10-15 matrix refer to obsolete source paths and a prior Step 102 branch. Do not use those lines as evidence of the current implementation. The live target prototype is under [gamecube-demo/](../gamecube-demo/). For current cross-platform goals use [VERSION_COMPARISON_MATRIX.md](VERSION_COMPARISON_MATRIX.md); for the source inventory and confidence-labelled findings use [the parked platform-source inventory](research/PLATFORM_SOURCE_MATRIX_2026-10-20.md), [the parked cross-platform findings](research/CROSS_PLATFORM_FINDINGS_2026-10-20.md), and the current [RE-002 PC/N64/Dreamcast dossier](research/RE-002-platform-source-matrix.md). These documents have different roles; preserve their evidence and do not create another duplicate matrix.

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

## Current code-level checkpoint — verified against main on 2026-11-07

The live implementation is in `gamecube-demo/`, not the old `gamecube/source/` path cited by this 2026-10-15 snapshot.

- `gamecube-demo/source/main.c` is the native GX rendering/input prototype. Its source describes an original authored mesh/texture and procedural closed-loop scrolling course; it explicitly requires a closed-loop generated track.
- `gamecube-demo/source/gameplay_state.h` contains resettable player/rival race state and deterministic simulation helpers, including frame-delta scaling and finite-value handling.
- `gamecube-demo/tests/test_gameplay_state.c` exercises those deterministic gameplay-state helpers with host-side C tests.
- `gamecube-demo/README.md` describes the scope and limits: this remains a prototype, with scripted rivals and provisional collision/handling, and no runtime filesystem loading or proprietary model/texture parsing.
- The current source tree does **not** contain `gamecube/source/track_path.c` or `gamecube/source/race_logic.c`. Those references in the original 2026-10-15 checkpoint are stale and must not be used as current implementation evidence.
- The old branch reference `audit/step102-import-gate` is not a current main-branch implementation location. Step 102 remains subject to the separate provenance/HOLD rules; this matrix does not authorize importing its archive.

The existence of a native DOL build or host tests is not, by itself, proof of full race acceptance or compatibility with commercial game assets. See the current prototype README and exact-head Actions evidence before making a status claim.

## Current research routing

The original five-step task list below belonged to the 2026-10-15 snapshot and is superseded by the live task queues. Do not restart Step 102 review or create a platform matrix duplicate from this historical checklist.

- Native GameCube/Wii target and integration decisions belong to [issue #226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226).
- PC/N64/Dreamcast comparative source evidence belongs to [issue #279](https://github.com/Master-Chiken/boonta-reborn-88/issues/279) and the linked RE-002 dossier.
- The N64 asset pipeline currently follows the owner-approved T1 → T2 sequence: reproduce the local CompWolf metadata inventory first ([PR #334](https://github.com/Master-Chiken/boonta-reborn-88/pull/334)); only after the owner-local counts reconcile should a single Pupp record be inspected for a possible GameCube conversion. Keep all commercial data local.
- Existing PRs and the canonical task ledger determine the current next implementation action. Human review and merge remain required.

