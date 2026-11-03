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


## Steam-PC address-correlation audit — 2026-11-03

A recursive tree comparison was performed between:

- `SW_RACER_RE` at `66120be334a3fd38c10a259f3528cffbfed8ddc5`, scanning the 153 literal `HANG("TODO")` bodies across 11 source modules and reading each adjacent function-address comment;
- `DeonPoncini/swep1r_decomp` at `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`, whose README explicitly identifies its target as the **Steam version** and which contains the frozen `c/` and `asm/` Ghidra exports.

### Exact-address file coverage

A candidate was counted only when **both** `c/FUN_<address>.c` and `asm/FUN_<address>.s` exist at the exact address. This is a filesystem/tree correlation, not proof of identical executable bytes, code equivalence or a successful runtime match.

| SW_RACER_RE module | TODO bodies | Steam C+ASM exact-address candidates | No candidate in either Steam export |
|---|---:|---:|---:|
| `swrRace.c` | 31 | 27 | 4 |
| `swrObj.c` | 58 | 41 | 17 |
| `swrSpline.c` | 2 | 1 | 1 |
| `swrControl.c` | 11 | 10 | 1 |
| `swrModel.c` | 12 | 12 | 0 |
| `swrRender.c` | 15 | 15 | 0 |
| `swrSound.c` | 3 | 2 | 1 |
| `swrUI.c` | 9 | 9 | 0 |
| `swrMultiplayer.c` | 8 | 8 | 0 |
| `swrWeather.c` | 3 | 3 | 0 |
| `swrLoader.c` | 1 | 1 | 0 |
| **Total** | **153** | **129 (84.3%)** | **24 (15.7%)** |

### The 24 unresolved address candidates

No matching `c/FUN_<address>.c` + `asm/FUN_<address>.s` pair was found in the pinned Steam export tree for these addresses:

| SW_RACER_RE function | Address | File / line |
|---|---:|---|
| `swrRace_SelectProfileMenu` | `0x00401340` | `src/Swr/swrRace.c:33` |
| `swrRace_AdvanceSplineCursor` | `0x0047F8E0` | `src/Swr/swrRace.c:4753` |
| `swrRace_UpdateSplineBinding` | `0x0047FBB0` | `src/Swr/swrRace.c:4759` |
| `swrRace_ComputeTrackOffset` | `0x0047FCA0` | `src/Swr/swrRace.c:4765` |
| `swrObjcMan_F0` | `0x00451CD0` | `src/Swr/swrObj.c:181` |
| `swrObjcMan_F2` | `0x00451D40` | `src/Swr/swrObj.c:187` |
| `swrObjcMan_F3` | `0x004542E0` | `src/Swr/swrObj.c:193` |
| `swrObjcMan_F4` | `0x004543F0` | `src/Swr/swrObj.c:199` |
| `swrObjScene_F0` | `0x00454A10` | `src/Swr/swrObj.c:206` |
| `swrObjScene_F4` | `0x00454A30` | `src/Swr/swrObj.c:212` |
| `swrObjHang_F2` | `0x00457B00` | `src/Swr/swrObj.c:261` |
| `swrObjHang_F3` | `0x00457B90` | `src/Swr/swrObj.c:267` |
| `swrObjHang_F4` | `0x0045A040` | `src/Swr/swrObj.c:298` |
| `swrObjJdge_UpdateSplineGuideNodes` | `0x0045E970` | `src/Swr/swrObj.c:909` |
| `swrObjJdge_UpdateOvertakeSounds` | `0x0045EF70` | `src/Swr/swrObj.c:1073` |
| `swrObjElmo_F0` | `0x00467CD0` | `src/Swr/swrObj.c:2057` |
| `swrObjElmo_F3` | `0x00468570` | `src/Swr/swrObj.c:2063` |
| `swrObjElmo_F4` | `0x00468660` | `src/Swr/swrObj.c:2069` |
| `swrObjToss_F2` | `0x0047B9E0` | `src/Swr/swrObj.c:2486` |
| `swrObjToss_F3` | `0x0047BA30` | `src/Swr/swrObj.c:2492` |
| `swrObjToss_F4` | `0x0047BBA0` | `src/Swr/swrObj.c:2498` |
| `swrSpline_ProjectPointStub` | `0x0047EB50` | `src/Swr/swrSpline.c:524` |
| `swrControl_MappingsMenu` | `0x00402250` | `src/Main/swrControl.c:10` |
| `swrSound_SelectPlanetIntroMusic` | `0x00427AD0` | `src/Swr/swrSound.c:1312` |

Steam export references for representative, high-value matched functions:
- [Track initialization — `FUN_00466bd0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00466bd0.c)
- [Track model setup — `FUN_00465510`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00465510.c)
- [Spline loader — `FUN_00465d00`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00465d00.c)
- [Ground contact — `FUN_00479e10`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00479e10.c)
- [Pod update/control — `FUN_0047ab40`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ab40.c)
- [Pod contact/physics — `FUN_0047b520`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047b520.c)

### Call-chain reconstruction now supported by both PC references

The pinned `SW_RACER_RE` source provides names, types, call sites and explicit reconstruction gaps; the Steam snapshot supplies address-correlated candidate decompilation for a large majority of those gaps. The following is the first coherent track/race chain:

1. `swrObjJdge_F4` handles the `'Begn'` race sub-event and reads the selected player count, planet, model ID, spline ID, camera spline, track number, lap count and AI speed from its payload.
2. It calls `swrObjJdge_InitTrack` at `0x00466BD0`. In the Steam candidate, this entry initializes per-race globals and player bookkeeping, then calls, in order, model setup (`0x00465510`), planet/track environment setup (`0x00464630`), spline setup (`0x00465D00`), camera setup (`0x00465D50`), primary light (`0x00466370`), AI settings (`0x004667E0`) and racer spawning (`0x004663E0`).
3. The model setup candidate at `0x00465510` initializes resource buffers, resolves the track model resource and invokes dust/fireball/trigger-related setup helpers before publishing the loaded-scene state.
4. The spline setup candidate at `0x00465D00` loads the selected spline ID, stores the loaded spline pointer, invokes the spline/model binding helper and the secondary setup helper.
5. Back in `swrObjJdge_F4`, after `InitTrack` returns, the caller marks scene objects loaded, switches the judge to race-preparation state 4, sets its transition timer, selects planet intro music and establishes the viewport layout.
6. During the race tick, `swrObjJdge_F2` calls the implemented `swrRace_UpdateRaceProgress`. That function calls three unresolved cursor/binding/offset stubs (`0x0047F8E0`, `0x0047FBB0`, `0x0047FCA0)), but then runs lap-completion and checkpoint accounting. This gives a narrow, testable next research seam: identify these three spline functions, rather than treating the entire race tick as missing.
7. The implemented PC ground-contact orchestrator (`0x00479E10`) already combines ground raycast, surface-normal / gravity handling, slope steering, local wall scrape/collision and hover-pad updates; several of its callees are among the address-correlated Steam candidates.

**Important platform/build caveat:** the Steam README identifies the Steam release as its target, while the exact executable/revision that the `SW_RACER_RE` snapshot targets has not been independently hash-identified. The 129/153 result therefore means **same numeric function address plus both exported Steam C and assembly files exist**, not "same bytes", not "same retail build", and not verified behavior in that other build. Before a candidate is treated as matching, compare the function prologue/call structure and reconcile release identity. Use the Steam decompilation as a read-only semantic reference; no source is copied into Boonta.


## Follow-up search for the three missing race-spline functions — 2026-11-03

### Upstream SW_RACER_RE parent check

The project repository is a fork of `tim-tim707/SW_RACER_RE`. I checked the upstream `master` snapshot at `258f67aa858ba2e281ce8a6791e49c554b85fae0`, including `src/Swr/swrRace.c` and `src/Swr/swrSpline.c`. The following three functions are still explicit `HANG("TODO")` stubs in that upstream snapshot:

- `swrRace_AdvanceSplineCursor` — `0x0047F8E0`
- `swrRace_UpdateSplineBinding` — `0x0047FBB0`
- `swrRace_ComputeTrackOffset` — `0x0047FCA0`

The spline projection placeholder `swrSpline_ProjectPointStub` at `0x0047EB50` is also still present. Thus the fork did not contain a newer implementation of the critical cursor trio that was missed by the earlier scan.

### Independent older PC reverse-engineering documentation

[OpenSWE1R/swe1r-re](https://github.com/OpenSWE1R/swe1r-re) is explicitly documented as an older Windows-patch analysis set, using executable MD5 `d86d5d03638c24ab6279f24079825794` unless otherwise noted. Its `Splines.md` documents a spline-block loader at `0x00446FC0`:

- opens the spline block and reads the spline count;
- reads the selected spline's start/end offsets from a directory table;
- loads that data chunk;
- byte-swaps its header and per-point fields;
- iterates a fixed record stride of 42 16-bit words (84 bytes) per spline point;
- closes the block.

This is useful **PC spline asset-format evidence** for the Windows-patch executable, but it is not a cursor traversal or lap-crossing implementation. The old documentation does not identify the missing cursor trio and must not be silently combined with the Steam-PC or GameCube/Wii target. Sources: [OpenSWE1R README](https://github.com/OpenSWE1R/swe1r-re/blob/57638c19ed092d52c152d8119e0cfe55e9c9f129/README.md) and [Splines.md](https://github.com/OpenSWE1R/swe1r-re/blob/57638c19ed092d52c152d8119e0cfe55e9c9f129/swep1rcr.exe/Splines.md).

### Current conclusion and next method

- `swrRace_GetTrackMeshAtCursor` (`0x0047F890`) has an address-correlated Steam C/ASM candidate; it is a compact lookup into the per-node baked track-mesh table.
- `swrRace_AdvanceSplineCursor`, `swrRace_UpdateSplineBinding` and `swrRace_ComputeTrackOffset` have no exact-address C/ASM pair in the Steam export tree and remain unresolved in the upstream SW_RACER_RE source.
- `swrSpline_ProjectPointStub` is likewise unresolved in both candidate lists.
- The OpenSWE1R spline loader explains input data layout for an older Windows patch executable, but does not explain runtime cursor state, direction/reversal, node-plane crossing interpolation, local offset or mesh binding.

**Do not synthesize a replacement yet.** The next valid step is to inspect the named cursor's structure and all fields read/written by the implemented neighboring functions, then compare those field semantics against the Steam assembly and the older patch-version documentation. Any derived algorithm must be tagged `INFERENCE` until corroborated by another source or exact-build runtime evidence. For Boonta's actual GameCube/Wii implementation, no transfer is permitted until the relevant DOL/REL target evidence is independently established.


## Spline cursor: what the surrounding PC source already establishes

This section narrows the next task to explicit contracts and separates observed behavior from inferred missing logic. Source snapshot: `Master-Chiken/SW_RACER_RE` commit `66120be334a3fd38c10a259f3528cffbfed8ddc5`.

### Runtime state layout — source-defined

The current `swrSplineCursor` definition is 0x30 bytes:

| Offset | Field | Documented role |
|---:|---|---|
| `+0x00` | `spline` | active spline pointer |
| `+0x04` | `velocity` | signed cursor velocity; positive and negative directions are treated separately by the generic evaluator |
| `+0x08` | `segmentT` | parameter within the current segment, clamped to 0..1 by `CursorEvaluate` |
| `+0x0C` | `tangentLength` | length of the last evaluated path tangent |
| `+0x10..+0x1C` | `nodeLookahead[4]` | current node and three-node lookahead window |
| `+0x20` | `endFlag` | forward graph end reached |
| `+0x24` | `startFlag` | backward graph end reached |
| `+0x28` | `branchSelector` | branch choice when a control point has multiple outgoing/incoming edges |
| `+0x2C` | `branchFlags` | history/branch selection used by graph lookup |

The race object embeds this cursor at `+0xAC`; the judge object also embeds separate cursors for camera-follow and post-race camera sweep. These are separate walkers over the same spline graph, not one global race cursor.

### Generic spline mechanics — implemented PC source

The neighbouring primitives are already described/implemented in `swrSpline.c`:

- `swrSpline_CursorStep` (`0x0044EAA0`) advances through the control-point graph using `next1/next2`, or retreats through `prev1/prev2`; it shifts the 4-node lookahead and preserves branch history.
- `swrSpline_CursorEvaluate` (`0x0044EC40`) applies `velocity * deltaTime` to `segmentT), crosses segment boundaries via `CursorStep`, clamps at graph ends, and interpolates position, tangent and up vector.
- `swrSpline_CursorSeekToProgress` (`0x0047E8B0`) maps integer progress to a node band (`progress / 10`) and a fractional segment parameter; it handles branch tables when the progress band exceeds the direct node range.
- `swrSpline_ProjectPoint` (`0x0047EB60`) marches by small parameter steps to find the nearest point on a spline segment relative to a world-space point and tangent plane. This is a separate active function from `swrSpline_ProjectPointStub` (`0x0047EB50`), which the source comments describe as compiled out / constant-zero in the retail path.
- `swrSpline_BakeSampleTrackMesh` samples the spline 10 times per node, raycasts to the track model, and writes a baked sample-to-mesh lookup. `swrRace_GetTrackMeshAtCursor` uses that table to return the mesh under the cursor.

### The missing race-specific functions: contracts, not invented implementations

**A. `swrRace_AdvanceSplineCursor` (`0x0047F8E0`)**

Source comment: steps the cursor over each node plane the pod passed, using `segmentT += 0.01` per step; entering node 0 calculates `outCrossTime` by line-plane interpolation between `positionPrev` and `position`, scaled by the raw frame delta. The caller consumes two outputs: `outForward` and `outBackward`.

- Confirmed interface contract: mutates the per-pod cursor and returns forward/backward movement signals plus a sub-frame crossing time when the start/finish node is entered.
- Not yet confirmed: exact plane origin/normal, branch selection policy, treatment of multiple node crossings in one frame, reverse traversal edge cases, and the exact interpolation/rounding rules.
- It is not equivalent to generic `CursorEvaluate`: that routine advances by a supplied cursor velocity/time-step, while this race-specific routine is described as reconciling the pod's actual world-space motion against spline node planes.

**B. `swrRace_UpdateSplineBinding` (`0x0047FBB0`)**

The race struct records the function's result in `splineRebindResult`; the current field annotation describes `-1 = blocked`, `0 = no rebind`, and `1 = rebound to the mesh the pod is standing on`.

- Supported contract: the caller treats return value 1 as a progress event eligible to trigger lap-crossing logic, even when the cursor did not report a forward node crossing.
- Hypothesis to verify: this function reconciles the spline cursor/track chunk to the ground-contact mesh when the racer is physically standing on a neighbouring mesh. Do not yet claim it picks a particular projection, branch or cursor seek routine.

**C. `swrRace_ComputeTrackOffset` (`0x0047FCA0`)**

The race struct labels `trackOffset` at `+0x118` as a 4-vector whose xyz encode a unit direction from the spline toward the pod and whose w stores raw distance.

- Supported field contract: writes or refreshes a four-component spline-to-pod offset used alongside the current spline/track mesh.
- Unknown: the exact origin point (current sample vs another projected sample), distance threshold, zeroing behavior, use of the w component, and how lateral displacement is fed into AI or handling.
- The direction/distance interpretation is a source annotation, not yet independently validated against a caller or runtime trace.

### End-to-end progress calculation already implemented around the gaps

`swrRace_UpdateRaceProgress` calls, in sequence:

1. `AdvanceSplineCursor` -> node-crossing flags and possible sub-frame start/finish time;
2. `GetTrackMeshAtCursor` -> current and previous track chunk; clear a vestigial counter when the mesh changes;
3. the retail-constant-zero projection stub twice;
4. `UpdateSplineBinding` -> -1/0/1 result;
5. `ComputeTrackOffset`;
6. `LapCompletion` -> lap fraction is computed from `spline_progress_values[node].x + segmentT * spline_progress_values[node].y`, with closed-track wrap and open-track finish handling;
7. update the checkpoint/backtracking counter and persist `splineRebindResult`.

This makes the exact priority unambiguous: resolve A first, then B/C, and use generic cursor and spline primitives as constraints. A synthetic test suite should cover forward crossing, backward crossing, branching, graph endpoints, zero movement, a high-delta frame crossing multiple nodes, mesh-boundary changes, open point-to-point finish, closed-lap wrap and finish-line crossing partway through a frame. Expected outputs must be obtained from evidence, not guessed.

**No implementation is authorized by this note.** These contracts guide the next RE-002 evidence pass. Any eventual independent implementation must be separately scoped, licence-clean, based on confirmed executable/version evidence and validated against owner-local runtime traces before it can be considered for Boonta's own code.
