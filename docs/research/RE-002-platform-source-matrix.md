# RE-002 — PC / Nintendo 64 / Dreamcast source matrix

> **Queue status: ACTIVE — research-only comparative evidence track.** The owner activated [RE-002 / issue #279](https://github.com/Master-Chiken/boonta-reborn-88/issues/279) on 2026-11-03. [RE-001 / issue #226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226) remains the native GameCube/Wii research and implementation queue. RE-002 is limited to PC/N64/Dreamcast public-source and documented-behavior comparison; it creates no gameplay implementation branch and does not establish GameCube/Wii parity.

**Status:** ACTIVE; comparative research and documentation only; no game code changed  
**Last updated:** 2026-11-03  
**Purpose:** use the original released game versions as behavioral references, then use public reverse-engineering repositories to explain what can be observed. This is not a claim that original commercial source code is public.

## Decision

Treat the original PC, N64 and Dreamcast releases as three separate evidence targets. The PC version is currently the strongest code-level reference because public projects document its Windows executable. N64 and Dreamcast are essential comparison targets, but this audit has **not yet found a verified public, complete source decompilation for either console version**.

Do not infer that a PC implementation is identical on a console. For every mechanic, record the platform, game revision, observation, source/repository evidence, confidence and test still needed.

## Resumed scope and baseline — 2026-11-03

The existing matrix and cross-platform notes are being completed rather than replaced. The following evidence is already available and is the starting baseline for #279:

- **PC source map:** the latest inspected [Master-Chiken/SW_RACER_RE snapshot](https://github.com/Master-Chiken/SW_RACER_RE/tree/66120be334a3fd38c10a259f3528cffbfed8ddc5) is pinned to `66120be334a3fd38c10a259f3528cffbfed8ddc5` and declares AGPL-3.0. Its source tree has distinct race, object/judge, spline, model/animation, render, sound, UI, multiplayer, weather and loader modules. A first marker screen recorded 31 `HANG` markers in `swrRace.c`, 58 in `swrObj.c`, 2 in `swrSpline.c`, 11 in `swrControl.c`, 16 in `swrModel.c`, 15 in `swrRender.c`, 3 in `swrSound.c`, 9 in `swrUI.c`, 8 in `swrMultiplayer.c`, 3 in `swrWeather.c`, and 1 in `swrLoader.c`. These are triage counts only: each marker still needs function/call-path classification, and a `HANG("TODO")` in a hook/reconstruction does not establish that the retail PC binary lacks that behavior.
- **PC cross-check:** the frozen [Steam-PC Ghidra reference](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef) is pinned separately at `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`. No root license was identified in the reviewed snapshot; read-only function/type comparison only. Do not merge its symbols or addresses into the other PC executable without version reconciliation.
- **N64 research references:** [sp00nznet/racer](https://github.com/sp00nznet/racer/tree/694c5663b3a7c30e2862fc240344f34683f99a9c) is a pinned N64/MIPS static-recompilation project, useful for methods and platform bring-up, not an original GC/Wii or PC codebase. [dguillot-gh/star-wars-racer-recomp](https://github.com/dguillot-gh/star-wars-racer-recomp/tree/68d3d2709cf71c07b5abed3627e01b03696cefd2) is an Android host port of that N64 recompile, not an independent game implementation. [OpenSWE1R/swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) documents an N64-specific `Comp` model-block decompression path; the tool is GPL-2.0-or-later and is a format reference, not permission to publish extracted assets.
- **Dreamcast asset evidence:** [swe1r-assets](https://github.com/akopetsch/swe1r-assets/tree/922ef535f6598a1330ff93d6b07258956f990b34) at `922ef535f6598a1330ff93d6b07258956f990b34` maps Dreamcast release selectors to the same generic block IDs as Windows International/Mac in its `Release.csv`. Its checksum catalogue does not expose separate Dreamcast model/spline/texture hashes; the combined `win_de__mac__dc` sprite label is not proof of whole-file identity. This is tool-author metadata, not independent verification from a retail Dreamcast disc.
- **Dreamcast code gap:** no verified public complete Dreamcast decompilation or source-level parser has been established in the reviewed evidence. Interviews/previews remain documentary leads; announced features must not be treated as shipped runtime facts.

The work remaining is to turn the PC marker inventory into function-level subsystem maps; update N64 source/format/render/input/audio evidence with exact revisions; check for stronger Dreamcast-specific code or primary evidence; and reconcile all three into one confidence-labelled matrix. No external game binaries, ROMs, discs, BIOS or proprietary assets were inspected or uploaded as part of this baseline.

## Source priority

| Priority | Source | Platform/evidence | Use | Confidence / limit |
|---|---|---|---|---|
| P0 | [Original PC release — inspected through SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | Windows executable, public symbols, function analysis, Ghidra scripts and hooks | Primary code-level behavioral oracle for handling, race progression, AI, splines, collision, HUD, camera and loading | Partial analysis/reimplementation, not full source. Repository declares AGPL-3.0; use as a research reference unless a separate license decision authorizes code reuse. |
| P0 | [Original Nintendo 64 release — N64-specific tool evidence](https://github.com/OpenSWE1R/swe1r-tools) | The tool README explicitly says its “Comp” model-block decompressor is for data found in the N64 version; community guide also documents Expansion Pak and Rumble Pak behavior | Build a console-specific checklist for memory/texture limits, rendering, controller behavior, vibration, sound, track geometry and differences from PC | This is tooling/documentation, not an N64 source decompilation. No N64 binary/ROM should be uploaded or committed. |
| P0 | [Original Dreamcast release — contemporary developer interview](https://www.timeextension.com/features/the-making-of-star-wars-episode-1-racer-maybe-we-cant-make-a-great-racing-game-but-we-can-make-an-excellent-toy) | Developer recollections describe the Dreamcast port, hardware, cutscenes, music and late project trade-offs; contemporary preview also records planned enhancements | Treat Dreamcast as its own target for visual fidelity, frame pacing, audio/music, cutscenes and controls; use the retail version as the final authority when lawful access exists | Interviews/previews are secondary evidence and may describe plans rather than the shipped build. No verified public Dreamcast code decompilation found in this pass. |
| P1 | [OpenSWE1R/swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) | GPL-2.0-or-later; parsers for spline, sprite, texture, save/profile/string data, plus N64 “Comp” chunk note | Cross-check format hypotheses and identify platform-specific compression branches | Old project (last inspected history 2018); not a universal cross-platform extractor. Do not copy GPL code into the MIT project without a deliberate licensing decision. |
| P1 | [swe1r-assets](https://github.com/akopetsch/swe1r-assets) | MIT library for PC `data/lev01` model/spline/sprite/texture blocks; documents bit-perfect no-op reserialization | Candidate for a PC-only no-op round-trip experiment after a lawful local test input is available | PC block support does not prove N64 or Dreamcast compatibility. Library licence does not cover original game assets. |
| P1 | [OpenSWE1R/swe1r-re](https://github.com/OpenSWE1R/swe1r-re) | Earlier Windows-PC function documentation and analysis | Cross-check PC function hypotheses and binary-version assumptions | Partial/deprecated, Windows-focused. |
| P1 | [Frozen Steam PC decompilation](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef) | Read-only Ghidra-derived PC function/type reference | Cross-check specific addresses and types against SW_RACER_RE | README says it is not a complete source translation; no root licence was identified in the reviewed snapshot. Read-only; no code copying. |
| P2 | [Official Nintendo Japan N64 product page](https://www.nintendo.co.jp/n01/n64/software/nus_p_nepj/index.html) | Official platform/product reference | Establish official N64 identity and basic release context | Not a source-code repository and not enough to establish low-level runtime behavior. |
| P2 | [PC manual (archived scan)](https://files.replacementdocs.com/Star_Wars_-_Episode1_Racer_-_AU_Manual_-_PC.pdf) | Manual rules for tournament progression, Free Play settings, upgrades and race configuration | Turn documented intended behavior into a test checklist | A manual describes intended behavior, not necessarily bugs/edge cases or every platform version. Prefer an official manual when available. |

## Confirmed comparison leads (not yet target-verified)

The following are useful test hypotheses from public documentation, not a substitute for testing the exact retail builds:

- **PC:** Windows executable analysis is available; the README for SW_RACER_RE states that the project documents/reimplements selected functions, not a full decompilation.
- **N64:** its tool ecosystem explicitly identifies an N64-specific “Comp” model-block compression path. Public player references document Expansion Pak and Rumble Pak support. Verify the actual cartridge/revision and Expansion Pak state before comparing graphics or performance.
- **Dreamcast:** developer recollections report high-resolution graphics and the return of prerendered cutscenes compared with the N64 release; the shipped game must be checked before treating interview statements as implementation requirements.
- **Multiplayer, audio, cutscenes, texture detail, controller mapping and performance** are likely platform differentiators and should be tested separately, rather than grouped into a generic “console version” row.

## Required evidence format

For each finding, use one row in the research ledger:

`ID | subsystem | platform | exact version/revision | evidence type | observation | source URL + commit/page | confidence | reproduction steps | open question`

Allowed evidence types:
- `CODE` — directly supported by inspected code/decompilation.
- `RUNTIME` — directly observed in the exact game build.
- `OFFICIAL-DOC` — official manual/product documentation.
- `DEVELOPER-INTERVIEW` — developer recollection; useful but not definitive.
- `COMMUNITY-REPORT` — hypothesis to verify.
- `INFERENCE` — reasoned conclusion, explicitly not verified.

Allowed confidence states:
- `CONFIRMED`, `SUPPORTED`, `HYPOTHESIS`, `UNKNOWN`, `CONFLICTING`.

## Active sequence — RE-002 / issue #279

1. **PC subsystem map:** continue from RE-001 route/spline/progress and map the next highest-value areas in SW_RACER_RE: handling/physics, collision, AI/racing line, boost/heat, track loading, camera and race completion. Pin each function to an exact commit and binary revision.
2. **N64 evidence audit:** inspect only public tool/source repositories and published documentation for N64-specific formats, memory/rendering constraints, controller and rumble behavior. Search for a genuine N64 reverse-engineering project before assuming one exists.
3. **Dreamcast evidence audit:** search for public Dreamcast-specific repositories, format notes and developer documentation. Separate announced features from the retail release. If no code-level source is found, record that as an evidence gap rather than filling it with PC assumptions.
4. **Cross-platform behavior matrix:** compare one mechanic at a time across PC/N64/Dreamcast, then mark what remains unknown for GameCube/Wii. Do not use a PC-only finding as proof of target-console behavior.
5. **Handoff only:** recommend any target-port specification or test to RE-001 / issue #226 with exact platform boundaries. RE-002 itself remains documentation-only; do not implement gameplay or copy third-party code.

## Handling and licensing boundaries

- “Official source” here means the original released game/build and official documentation as the behavioral reference; it does **not** mean that the original source code has been located.
- Never upload or commit commercial executables, ROMs, disc images, BIOS files or extracted proprietary models, textures, audio or track geometry.
- Public repositories may be read and cited, but their code licences remain binding. A source-code licence does not grant rights to game assets.
- Use lawful local game copies for runtime comparisons; keep extracted content local-only unless redistribution rights are explicit.
- Step 102 is intentionally outside this research sequence and is not a blocker for this platform/source audit.


**Activation decision (2026-11-03):** the owner has explicitly activated this bounded comparative track in issue #279. Research may proceed independently from the native GameCube/Wii implementation queue only because the platforms and deliverables are non-overlapping. One write-capable agent at a time remains mandatory; RE-002 must not produce gameplay changes or duplicate RE-001's runtime work.


## Function-level placeholder triage — SW_RACER_RE

**Pinned source:** `Master-Chiken/SW_RACER_RE` commit `66120be334a3fd38c10a259f3528cffbfed8ddc5`. This is a fresh source-tree scan of the reviewed PC research repository, not an executable runtime test.

### Marker inventory

The scan distinguishes three different things: (1) `HANG("TODO")` placeholder bodies; (2) `HANG(...)` calls that reject invalid/unsupported input; and (3) comments that mention TODO, crashes or unfinished behavior. They must not be counted as the same kind of missing implementation.

| Module | `HANG("TODO")` bodies | `HANG` guards / invalid-input stops | Other TODO / crash comments | Primary subsystem signal |
|---|---:|---:|---:|---|
| `swrRace.c` | 31 | 0 | 6 | Race/menu flow, vehicle setup, parts/damage, engine UI, triggers, spline binding/progression, wall collision and hover pads |
| `swrObj.c` | 58 | 0 | 0 | Hangar/scene lifecycle, track setup/loading, judge/HUD, pod animation/physics, dust/fireballs and world triggers |
| `swrSpline.c` | 2 | 0 | 0 | Point projection and nearby-point collection |
| `swrControl.c` | 11 | 0 | 0 | Input mappings, input polling/startup/shutdown and force feedback |
| `swrModel.c` | 12 | 4 | 8 | Model/texture/animation loading, puppet/model scene management, light streaks and text |
| `swrRender.c` | 15 | 0 | 0 | Mesh conversion, normals/fog, scene submission, transforms, frustum and LOD |
| `swrSound.c` | 3 | 0 | 0 | Audio startup, spatial playback and planet-intro music selection |
| `swrUI.c` | 9 | 0 | 2 | UI message/key handling, circuits/track selection, unlock condition, UI audio and window element loading |
| `swrMultiplayer.c` | 8 | 0 | 0 | Player/session state, in-race synchronization and event transport |
| `swrWeather.c` | 3 | 0 | 0 | Weather velocity, particle cap and stretch |
| `swrLoader.c` | 1 | 0 | 3 | LZSS decompression plus file-type/read/open plumbing |
| **Total** | **153** | **4** | **19** | **176 distinct scan hits; not 176 missing retail-game features** |

Sources: [race](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrRace.c), [object/judge/scene](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrObj.c), [spline](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrSpline.c), [control](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Main/swrControl.c), [model](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrModel.c), [render](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrRender.c), [sound](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrSound.c), [UI](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrUI.c), [multiplayer](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrMultiplayer.c), [weather](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrWeather.c), [loader](https://github.com/Master-Chiken/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrLoader.c).

### What the placeholders actually point to

- **Race lifecycle and race simulation:** `swrRace_UpdatePartsHealth` (1035), `swrRace_CheckResetInput` (2755), `swrRace_ApplyEngineDamage` (2761), `swrRace_SpawnFlameAttack` (2767), `swrRace_SendFlameAttackEvent` (2773), and `swrRace_TriggerHandler` (4654) leave damage, reset, hazard/event and trigger behavior unresolved in this reconstruction. The route-to-world binding path is also stubbed at `swrRace_GetTrackMeshAtCursor` (4745), `swrRace_AdvanceSplineCursor` (4753), `swrRace_UpdateSplineBinding` (4759), and `swrRace_ComputeTrackOffset` (4765). Collision/vehicle-ground response has explicit stubs at `swrRace_CollideBlockMove` (4848), `swrRace_DetectWallScrape` (4854), `swrRace_ApplyWallCollision` (4860), and `swrRace_UpdateHoverPads` (4866).
- **Course setup and scene construction:** `swrObjJdge_InitTrack` (2051), `LoadTrackModels` (1961), `LoadTrackSpline` (1967), `InitPrimaryLight` (1973), `swrObjJdge_AddTriggersToScene` (1931), and the trigger scene/load functions (3048–3066) form a cluster around preparing the race world. These are especially important to inspect as one caller/callee chain rather than independent TODO entries.
- **Pod and world physics/animation:** `swrObjTest_UpdateControlAndMove` (2474), `swrObjTest_UpdatePhysicsContact` (2480), `swrRace_PoddAnimateVariousThings` (2369), `swrRace_PoddAnimateSteeringParts` (2375), and `swrRace_Explode` (2461) indicate an unfinished or unhooked area spanning movement, contact response, visual animation and destruction. The marker scan alone does not prove which behavior is present elsewhere or what the retail executable does.
- **Rendering and assets:** `swrModel_LoadModelIntoScene` (1663), `swrModel_ClearLoadedModels` (1669), `swrModel_ReloadAnimations` (1675), `swrModel_LoadTextureDataAndPalette` (1738), `swrModel_LoadModelTexture` (1757), `swrModel_LoadPuppet` (1842), and the render-scene functions in `swrRender.c` (14–199) cover major asset and draw submission boundaries. The four model `HANG` guards reject invalid primitive/node/animation/texture state; they are not counted as missing feature implementations.
- **Input, audio, progression and multiplayer:** the control module has stubs for mapping management and polling (`swrControl_ProcessInputs`, line 23, plus lines 10–69); audio has startup, spatial play and planet-intro selection (lines 24, 1077, 1312); UI has key/message handlers, circuit/track navigation and a tournament unlock predicate; multiplayer's eight stubs include player/session state and event sending. These systems need to be traced to determine which are genuinely absent from the reconstruction and which are intentionally platform-hook placeholders.

### Prioritized RE-002 investigation order

1. **Track/world bring-up chain:** trace `swrObjJdge_InitTrack` → model/spline loading → model/trigger scene registration → race-ready state. Record exact callers/callees, data dependencies and the smallest confirmed boot-to-first-course chain. This is the most useful bridge between asset loading, track construction, scene graph and race start.
2. **Race update chain:** map the callers and state dependencies around `swrRace_UpdateRaceProgress`, cursor advancement/binding, collision, hover-pad response, damage and finish progression. Preserve the known TODO boundary; do not infer that the HANG body is the same as the commercial binary's body.
3. **Pod control and physics chain:** connect input sampling to control forces, movement, track contact, wall scrape/collision, slide/boost/heat, damage and repair. Distinguish the existence of named hooks from verified end-to-end behavior.
4. **Front-end/progression chain:** trace menu state and course selection through vehicle/pilot selection, save/profile settings, tournament/circuit unlocks and results persistence.
5. **Platform-specific comparison:** only after the PC call paths are coherent, add the N64 and Dreamcast evidence row-by-row. Existing N64 recompilation work is MIPS evidence about that N64 build; it is not an independent PC or GameCube/Wii validation source.

**Interpretation boundary:** the 153 `HANG("TODO")` bodies identify where this PC reconstruction currently leaves explicit holes. They do not mean that 153 retail game systems are missing, nor that the corresponding behavior is absent from the commercial PC game. Some function bodies may be available in the separately pinned Steam-PC Ghidra reference, but its executable build and address space differ and its repository's root licence was not identified. Cross-match by function semantics and version first; keep it read-only.
