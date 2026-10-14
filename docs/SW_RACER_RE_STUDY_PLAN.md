# SW_RACER_RE — priority research reference for Boonta Reborn 88

**Review snapshot:** 2026-10-14  
**Upstream repository:** https://github.com/tim-tim707/SW_RACER_RE  
**Branch reviewed:** master  
**Latest commit reviewed:** \`a9863edd4caaa573f89ff634fa7d1cd6d41738ab\` (2026-10-05)  
**Upstream license reported by GitHub:** GNU AGPL v3.0

## Decision

Treat SW_RACER_RE as a **Tier 1 technical and behavioral research reference** for understanding the original PC game's systems. It must be linked to the Step 102 work and reviewed before implementing important gameplay, track, asset-format, or rendering behavior.

It is **not** the native GameCube source of truth and is not a drop-in console port. The upstream README explicitly says its goal is to document and re-implement selected functions for modding, not to obtain matching compilation or decompile the entire game. Its current documented progress (71.2%, 1,518 of 2,132 functions analyzed on 2026-06-12) is a dated upstream figure and means functions analyzed, not necessarily functions fully reimplemented.

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
- \`src/Swr/swrRace.c\` and \`src/Swr/swrRace.h\` — race subsystem research;
- \`src/Swr/swrSpline.c\` and \`src/Swr/swrSpline.h\` — spline subsystem research;
- \`src/Swr/swrModel.c\`, \`swrObj.c\`, and \`swrRender.c\` — model/object/rendering research;
- \`src/Swr/swrAssetBuffer.c\` and \`swrLoader.c\` — resource and loading research;
- \`src/Main/swrControl.c\` and \`src/Platform/stdControl.c\` — control/platform research;
- \`src/Engine/rdCamera.c\` and \`src/Primitives/rdMatrix.c\` — camera and transform research;
- \`data_symbols.syms\` and \`src/generated/hook_generated.c\` — upstream symbol/function index described by its README;
- \`dinput_hook/game_deltas/\` — PC mod/hook changes which can be useful for understanding fixes, but are Windows-specific.

Use these paths as reading entry points, not as permission to copy files. The exact module-to-feature mapping still needs to be checked against the relevant function bodies, notes, and tests.

## Critical platform distinction

This repository primarily studies the **Windows PC executable**. Its hook is a 32-bit Windows \`dinput.dll\` built with a MinGW/Clang toolchain; the PC project uses Windows-oriented APIs and replacement-renderer technology.

Boonta Reborn's primary target is native GameCube/Wii homebrew (PowerPC/libogc/GX). PC functions, addresses, calling conventions, DirectX paths, PC asset files, and hook code cannot be assumed to compile or behave the same on GameCube/Wii. Use the PC research to derive a testable *behavioral specification*, then implement or adapt that behavior separately for the console target. Validate every platform-specific assumption.

## Required workflow: study → map → implement → test

For each important feature:

1. **Record the upstream evidence.** Link to the exact upstream file/function/note and the reviewed commit. State whether the finding is confirmed, inferred, or still uncertain.
2. **Map it to Step 102.** Identify the corresponding source module, function, data structure, test, or the fact that no equivalent currently exists. Candidate source files already named in the archive handoff include \`source/main.c\`, \`source/racer_physics.c\`, \`source/rival_ai.c\`, and \`source/track_catalog.c\`; confirm exact mapping from the archive before making changes.
3. **Separate PC fact from console hypothesis.** Record what appears true of the Windows game separately from what must be tested on the GameCube/N64 version.
4. **Specify independent behavior.** Write down inputs, state transitions, equations/parameters where verified, edge cases, timing assumptions, and an observable pass/fail result.
5. **Implement on a review branch.** Prefer independently written code that follows the behavioral specification; do not copy or adapt upstream code unless licensing and compatibility have been reviewed and the project owner explicitly chooses the consequences.
6. **Add tests.** Unit-test portable logic first, then compile with the native console toolchain and test actual behavior in an interactive emulator/hardware environment.
7. **Record evidence.** Link test logs and CI runs; do not call a PC behavior proven on console merely because the PC implementation or host tests pass.

## Priority study matrix

| Priority | Research topic | Upstream starting points | Deliverable for Boonta Reborn | Required validation |
|---|---|---|---|---|
| P0 | Racing state and lap progression | \`src/Swr/swrRace.c\`, race HUD and function/symbol records | A short behavior note and mapping to Step 102's race-flow code/tests | Start, lap crossings, finish/reset, edge cases; compare PC and console evidence separately |
| P0 | Pod control and physics | Control modules, gameplay functions, relevant symbols and notes | A behavior sheet for acceleration, braking, steering, drift, boost/heat, collisions and damage, with an explicit confidence level for every rule | Unit tests plus controlled, repeatable tests of the chosen target; do not assume PC physics timing equals console timing |
| P0 | Track route and spline model | \`src/Swr/swrSpline.c\`, track block/format work, \`dinput_hook/game_deltas/tracks_delta.c\` and related notes | A format/coordinate-system note; distinguish route behavior from third-party track data | Inspect actual target-version data and validate coordinate scale, orientation, spline progression and lap closure |
| P1 | Camera and transforms | \`src/Engine/rdCamera.c\`, \`src/Primitives/rdMatrix.c\`, renderer notes | Camera, look-ahead, roll/bank, transform and clipping behavior specification | Compare frame sequences in the reference game and interactive target build |
| P1 | Rival AI and objects | Object and race research, symbols, related delta files | AI behavior table: target selection, lines, speed, overtaking, collisions and recovery | Repeatable scenarios and deterministic tests in the project implementation |
| P1 | Assets and loading | \`src/Swr/swrAssetBuffer.c\`, \`swrLoader.c\`, \`swrModel.c\`, file-format research | Format notes only: header, alignment, block relationships, endianness and size constraints where verified | Validate against lawful target-version test inputs and a documented parser; no assets copied by default |
| P2 | Renderer, weather, HUD and effects | \`swrRender.c\`, \`swrDisplay.c\`, \`swrWeather.c\`, \`swrPlayerHUD.h\`, PC \`dinput_hook\` changes | Rendering feature map ordered by console feasibility and performance cost | GX/libogc implementation and emulator/console visual tests |
| P2 | Audio and presentation | \`swrSound.c\`, release notes and relevant functions | High-level event/behavior notes, not extracted sound data | Target audio tests; use only original or clearly licensed assets |

## License and asset boundaries

- Upstream source files are marked by the repository's **AGPL-3.0** license. Do not paste or adapt its code into this repository under the existing MIT license without a deliberate, qualified license-compatibility review and a clear decision about the resulting licensing obligations.
- The upstream repository also contains third-party dependencies and an \`assets/\` tree. A root software license is not proof that every texture, model, sound, binary block, custom track, or other asset in that tree can be redistributed.
- Do not copy upstream compiled binaries, commercial game assets, extracted resource blocks, textures, models, music, voice, track data, or ROM/disc content into Boonta Reborn.
- Keep references and links in documentation. Record a URL, exact commit, relevant path, and summarized technical observation rather than duplicating source code.
- Facts and observable behaviors can guide an independently implemented design, but source code and creative assets require their own permissions. This is a project hygiene rule, not legal advice.

## Relationship to Step 102 and the current demo

- **Step 102** remains the candidate source baseline for native GameCube/Wii work, subject to the separate path-by-path provenance and redistribution gate. Its existing PC-derived route centerline data remains on hold until its own provenance is resolved.
- **The clean-room demo in PR #13** is a separate minimal proof of concept. Use it to validate the console toolchain and experiment with small gameplay slices; do not use it as a substitute for studying the original game's systems.
- **SW_RACER_RE** is the priority reference for PC-side reverse engineering and behavior research. It does not remove the need to inspect GameCube-specific code/data or test differences in the console version.
- **The Dreamcast folder** remains a separate experiment and is not a GameCube/Wii implementation path.

## Next concrete task

Create a versioned feature mapping table for the first three items above (race/laps, pod physics/control, and spline/track format), then use it to guide the Step 102 audit and the first playable GameCube vertical slice. Start read-only. Do not bulk-import either archive or merge a code change just because this research exists.

## Sources

- Upstream repository: https://github.com/tim-tim707/SW_RACER_RE
- Upstream README at reviewed branch: https://github.com/tim-tim707/SW_RACER_RE/blob/master/README.md
- Upstream notes: https://github.com/tim-tim707/SW_RACER_RE/blob/master/NOTES.md
- Upstream license: https://github.com/tim-tim707/SW_RACER_RE/blob/master/LICENSE
- Recent PC mod releases/feature notes: https://github.com/tim-tim707/SW_RACER_RE/releases