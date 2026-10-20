# SW_RACER_RE — priority research reference for Boonta Reborn 88

**Review snapshot:** 2026-10-14  
**Upstream repository:** https://github.com/tim-tim707/SW_RACER_RE  
**Branch reviewed:** master  
**Latest commit reviewed:** `a9863edd4caaa573f89ff634fa7d1cd6d41738ab` (2026-10-05)  
**Upstream license reported by GitHub:** GNU AGPL v3.0

## Decision

Treat SW_RACER_RE as a **Tier 1 technical and behavioral research reference** for understanding the original PC game's systems. It must be linked to the Step 102 work and reviewed before implementing important gameplay, track, asset-format, or rendering behavior.

It is **not** the native GameCube source of truth and is not a drop-in console port. The upstream README explicitly says its goal is to document and re-implement selected functions for modding, not to obtain matching compilation or decompile the entire game. Its current documented progress (71.2%, 1,518 of 2,132 functions analyzed on 2026-06-12) is a dated upstream figure and means functions analyzed, not necessarily functions fully reimplemented.

## Project-wide 80/20 work rule

The intended allocation is **80% reverse-engineering research and 20% implementation, testing, integration and project management combined**. Track comparable 45–60 minute work blocks: eight of ten blocks are research, no more than two are all other engineering work. Do not manufacture tasks to hit the ratio; if time is limited, preserve the ratio and finish one bounded question.

Only one research question is active at a time. Each question must end in an evidence dossier that separates observed source facts, inference, target-platform hypothesis and unknowns. Do not code while the source evidence or Step 102 mapping is still ambiguous. Tool setup and generic documentation do not count as reverse engineering unless they directly unblock the chosen question.

The first active research item is **RE-001: compare the PC spline/cursor route model with the current GameCube prototype's track sampling and distance-based lap progress**. See [the dossier](research/RE-001-route-spline-progress.md). Mapping to the private Step 102 archive remains explicitly unverified until that candidate source can be inspected.

## Why it matters

The project offers a better evidence base than guessing from screenshots or treating a minimal procedural prototype as representative of the original game. Its code, symbols, notes, and PC renderer/modding work can help the team form precise questions about:

- race flow, lap handling, race state, and HUD;
- control input, steering and camera behavior;
- pod models, world objects, collisions, and scene structure;
- spline/route and track block formats;
- model, sprite, texture, asset-buffer, and loading systems;
- rendering, fog, weather, and timing/frame-rate behavior;
- legacy engine and platform interfaces.

Examples of useful upstream areas include:
- `src/Swr/swrRace.c` and `src/Swr/swrRace.h` — race subsystem research;
- `src/Swr/swrSpline.c` and `src/Swr/swrSpline.h` — spline subsystem research;
- `src/Swr/swrModel.c`, `swrObj.c`, and `swrRender.c` — model/object/rendering research;
- `src/Swr/swrAssetBuffer.c` and `swrLoader.c` — resource and loading research;
- `src/Main/swrControl.c` and `src/Platform/stdControl.c` — control/platform research;
- `src/Engine/rdCamera.c` and `src/Primitives/rdMatrix.c` — camera and transform research;
- `data_symbols.syms` and `src/generated/hook_generated.c` — upstream symbol/function index described by its README;
- `dinput_hook/game_deltas/` — PC mod/hook changes which can be useful for understanding fixes, but are Windows-specific.

Use these paths as reading entry points, not as permission to copy files. The exact module-to-feature mapping still needs to be checked against the relevant function bodies, notes, and tests.

### First source-level findings (reviewed revision only)

- The PC spline loader and traversal code is substantial: it opens a spline block, validates the requested index, loads its data into an asset buffer, transforms encoded values for runtime use, and exposes control-point interpolation/cursor routines. See [swrSpline.c loading](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L14-L78) and [interpolation/cursor routines](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L86-L315). This is useful format/behavior research, but it does not prove the same binary layout or data is used by GameCube.
- The PC turning routine [swrRace_UpdateTurn](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c#L1714-L1744) time-scales its turn-rate update and heading integration. That is a concrete behavior lead, not a conclusion that all physics is frame-rate independent.
- Some functions remain TODO/stubs, including [swrControl_ProcessInputs](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Main/swrControl.c#L20-L24) and [spline helper stubs](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L522-L539). Read the actual function before assuming an area is fully understood. These findings are recorded in the [behavior matrix](SW_RACER_RE_BEHAVIOR_MATRIX.md).

## Critical platform distinction

This repository primarily studies the **Windows PC executable**. Its hook is a 32-bit Windows `dinput.dll` built with a MinGW/Clang toolchain; the PC project uses Windows-oriented APIs and replacement-renderer technology.

Boonta Reborn's primary target is native GameCube/Wii homebrew (PowerPC/libogc/GX). PC functions, addresses, calling conventions, DirectX paths, PC asset files, and hook code cannot be assumed to compile or behave the same on GameCube/Wii. Use the PC research to derive a testable *behavioral specification*, then implement or adapt that behavior separately for the console target. Validate every platform-specific assumption.

## Required workflow: study → map → specify → implement only if justified → test

For each important feature:

1. **Study the exact evidence.** Link the exact upstream file/function/note and the reviewed commit. State whether the finding is confirmed, inferred or uncertain.
2. **Map to the actual target sources.** If Step 102 is available, identify the corresponding file/function/data/test. If it is unavailable in the current work surface, say so and leave the mapping unverified; do not infer it from filenames in an old handoff note.
3. **Separate platform claims.** Record Windows-PC source facts separately from Step 102 findings and GameCube/Wii hypotheses.
4. **Write an independent behavior specification.** Include inputs, state transitions, timing assumptions, edge cases and an observable pass/fail result.
5. **Decide whether code is needed.** A research result can be the deliverable; do not force an implementation just to show activity.
6. **If justified, implement on a review branch.** Keep the change small and independently written. Do not copy or adapt upstream code without a deliberate license review and owner decision.
7. **Validate and report.** Use exact-head host tests, a native console build, and interactive testing where applicable. Link evidence and preserve unknowns; a PC finding never alone proves console behavior.

## Priority study matrix

| Priority | Research topic | Upstream starting points | Deliverable for Boonta Reborn | Required validation |
|---|---|---|---|---|
| P0 | Racing state and lap progression | `src/Swr/swrRace.c`, race HUD and function/symbol records | A short behavior note and mapping to Step 102's race-flow code/tests | Start, lap crossings, finish/reset, edge cases; compare PC and console evidence separately |
| P0 | Pod control and physics | Control modules, gameplay functions, relevant symbols and notes | A behavior sheet for acceleration, braking, steering, drift, boost/heat, collisions and damage, with an explicit confidence level for every rule | Unit tests plus controlled, repeatable tests of the chosen target; do not assume PC physics timing equals console timing |
| P0 | Track route and spline model | `src/Swr/swrSpline.c`, track block/format work, `dinput_hook/game_deltas/tracks_delta.c` and related notes | A format/coordinate-system note; distinguish route behavior from third-party track data | Inspect actual target-version data and validate coordinate scale, orientation, spline progression and lap closure |
| P1 | Camera and transforms | `src/Engine/rdCamera.c`, `src/Primitives/rdMatrix.c`, renderer notes | Camera, look-ahead, roll/bank, transform and clipping behavior specification | Compare frame sequences in the reference game and interactive target build |
| P1 | Rival AI and objects | Object and race research, symbols, related delta files | AI behavior table: target selection, lines, speed, overtaking, collisions and recovery | Repeatable scenarios and deterministic tests in the project implementation |
| P1 | Assets and loading | `src/Swr/swrAssetBuffer.c`, `swrLoader.c`, `swrModel.c`, file-format research | Format notes only: header, alignment, block relationships, endianness and size constraints where verified | Validate against lawful target-version test inputs and a documented parser; no assets copied by default |
| P2 | Renderer, weather, HUD and effects | `swrRender.c`, `swrDisplay.c`, `swrWeather.c`, `swrPlayerHUD.h`, PC `dinput_hook` changes | Rendering feature map ordered by console feasibility and performance cost | GX/libogc implementation and emulator/console visual tests |
| P2 | Audio and presentation | `swrSound.c`, release notes and relevant functions | High-level event/behavior notes, not extracted sound data | Target audio tests; use only original or clearly licensed assets |

## License and asset boundaries

- Upstream source files are marked by the repository's **AGPL-3.0** license. Do not paste or adapt its code into this repository under the existing MIT license without a deliberate, qualified license-compatibility review and a clear decision about the resulting licensing obligations.
- The upstream repository also contains third-party dependencies and an `assets/` tree. A root software license is not proof that every texture, model, sound, binary block, custom track, or other asset in that tree can be redistributed.
- Do not copy upstream compiled binaries, commercial game assets, extracted resource blocks, textures, models, music, voice, track data, or ROM/disc content into Boonta Reborn.
- Keep references and links in documentation. Record a URL, exact commit, relevant path, and summarized technical observation rather than duplicating source code.
- Facts and observable behaviors can guide an independently implemented design, but source code and creative assets require their own permissions. This is a project hygiene rule, not legal advice.

## Relationship to Step 102 and the current demo

- **Step 102** remains the candidate source baseline for native GameCube/Wii work, subject to the separate path-by-path provenance and redistribution gate. Its existing PC-derived route centerline data remains on hold until its own provenance is resolved.
- **The clean-room demo in gamecube-demo/ is on main.** It now builds a native DOL/ELF and has a CI Software Renderer capture showing a visible procedural scene. Host tests cover selected prototype logic, but live controller response, a completed three-lap run, sustained stability, and physical-hardware behavior remain unverified. Treat it as the immediate interactive-validation target, not as a faithful reconstruction of the full game.
- **SW_RACER_RE** is the priority reference for PC-side reverse engineering and behavior research. It does not remove the need to inspect GameCube-specific code/data or test differences in the console version.
- **The Dreamcast folder** remains a separate experiment and is not a GameCube/Wii implementation path.

## Next concrete task — RE-001 only

Finish the route/spline progression dossier at [research/RE-001-route-spline-progress.md](research/RE-001-route-spline-progress.md). The bounded question is: **how does the reviewed PC source represent route position and advance a spline cursor, and how does that differ from the current GameCube prototype's track sampling and lap counter?**

Required output: exact source links, current-prototype mapping, facts vs unknowns, a Step 102 mapping status, and one next research question. Do not start handling/traction, AI, assets, rendering or another subsystem in parallel. Do not bulk-import either archive or make a code change merely because a behavior has been documented.

## Sources

- Upstream repository: https://github.com/tim-tim707/SW_RACER_RE
- Upstream README at reviewed branch: https://github.com/tim-tim707/SW_RACER_RE/blob/master/README.md
- Upstream notes: https://github.com/tim-tim707/SW_RACER_RE/blob/master/NOTES.md
- Upstream license: https://github.com/tim-tim707/SW_RACER_RE/blob/master/LICENSE
- Recent PC mod releases/feature notes: https://github.com/tim-tim707/SW_RACER_RE/releases