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
- **N64 research references:** [sp00nznet/racer](https://github.com/sp00nznet/racer/tree/694c5663b3a7c30e2862fc240344f34683f99a9c) is a pinned N64/MIPS static-recompilation project, useful for methods and platform bring-up, not an original GC/Wii or PC codebase. Its README at this pin reports Phase 8/in-game: 878+ functions discovered, game boot and asset loading, display lists processed by RT64, visible intro/title/menu/race frames, controller/EEPROM and audio paths, and a tournament race on the Boonta Training Course; it still marks the playable build IN PROGRESS and widescreen EXPERIMENTAL. This is a meaningful PC runtime/behavior reference, not a complete source decompilation or a validated GameCube/Wii port. The repository's MIT licence covers its tooling/runtime/build code but explicitly excludes generated code derived from the commercial ROM and all game data; don't copy generated output or ROM-derived assets into Boonta. The README's macOS build requires Xcode's Metal toolchain and Homebrew SDL2, and says the macOS build was compile-checked only—not verified running on a Mac. The latest publicly indexed release is v0.4.0 dated 2026-10-30; this is a release of the recompilation project, not proof of complete playability. [dguillot-gh/star-wars-racer-recomp](https://github.com/dguillot-gh/star-wars-racer-recomp/tree/68d3d2709cf71c07b5abed3627e01b03696cefd2) is an Android host port of that N64 recompile, not an independent game implementation. [OpenSWE1R/swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) documents an N64-specific `Comp` model-block decompression path; the tool is GPL-2.0-or-later and is a format reference, not permission to publish extracted assets.
- **Dreamcast asset evidence:** [swe1r-assets](https://github.com/akopetsch/swe1r-assets/tree/922ef535f6598a1330ff93d6b07258956f990b34) at `922ef535f6598a1330ff93d6b07258956f990b34` maps Dreamcast release selectors to the same generic block IDs as Windows International/Mac in its `Release.csv`. Its checksum catalogue does not expose separate Dreamcast model/spline/texture hashes; the combined `win_de__mac__dc` sprite label is not proof of whole-file identity. This is tool-author metadata, not independent verification from a retail Dreamcast disc.
- **Dreamcast code gap:** no verified public complete Dreamcast decompilation or source-level parser has been established in the reviewed evidence. Interviews/previews remain documentary leads; announced features must not be treated as shipped runtime facts.

The work remaining is to turn the PC marker inventory into function-level subsystem maps; update N64 source/format/render/input/audio evidence with exact revisions; check for stronger Dreamcast-specific code or primary evidence; and reconcile all three into one confidence-labelled matrix. No external game binaries, ROMs, discs, BIOS or proprietary assets were inspected or uploaded as part of this baseline.

## Source priority

| Priority | Source | Platform/evidence | Use | Confidence / limit |
|---|---|---|---|---|
| P0 | [Original PC release — inspected through SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | Windows executable, public symbols, function analysis, Ghidra scripts and hooks | Primary code-level behavioral oracle for handling, race progression, AI, splines, collision, HUD, camera and loading | Partial analysis/reimplementation, not full source. Repository declares AGPL-3.0; use as a research reference unless a separate license decision authorizes code reuse. |
| P0 | [Original Nintendo 64 release — N64-specific tool evidence](https://github.com/OpenSWE1R/swe1r-tools) | The tool README explicitly says its “Comp” model-block decompressor is for data found in the N64 version; community guide also documents Expansion Pak and Rumble Pak behavior | Build a console-specific checklist for memory/texture limits, rendering, controller behavior, vibration, sound, track geometry and differences from PC | This is tooling/documentation, not an N64 source decompilation. No N64 binary/ROM should be uploaded or committed. |
| P0 | [N64 static recompilation — sp00nznet/racer](https://github.com/sp00nznet/racer/tree/694c5663b3a7c30e2862fc240344f34683f99a9c) | Pinned N64 USA/NTSC recompilation using N64Recomp, N64ModernRuntime and RT64; project README reports a visible race and controller/audio pipeline on PC, while playable-build status remains in progress | Read as a public runtime/bring-up comparison for N64 rendering, scheduling, DMA/asset loading, RSP, audio and controller behavior; extract only source-level observations with exact commit and explicit build identity | Not a decompilation and not GameCube/Wii source. MIT applies to infrastructure, not generated commercial game code/assets. macOS build is compile-checked only and requires Xcode/Metal + Homebrew SDL2; no need to build it locally for this research. |
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




## Additional resolvable PC spline gap — `swrRace_GetTrackMeshAtCursor`

The current `SW_RACER_RE` snapshot at `258f67aa858ba2e281ce8a6791e49c554b85fae0` also leaves `swrRace_GetTrackMeshAtCursor` at `0x0047F890` as `HANG("TODO")`. Unlike the three race-specific functions below it, the frozen Steam-PC export contains both `c/FUN_0047f890.c` and `asm/FUN_0047f890.s` at that exact numeric address.

The decompilation plus the current upstream `swrRace.h` comment establish the following lookup:

1. Resolve the cursor's current control-point ID with `swrSpline_getControlPoint(cursor, 0)`. This helper honours the cursor's current branch flags; it is not always a raw `nodeLookahead[0]` read.
2. Convert `segmentT` to a per-node sample slot using the ten-samples-per-node convention (`segmentT * 10`; the x86 sequence has a boundary/negative-value correction before integer conversion, so exact rounding at exceptional endpoints should be preserved from the matching build rather than guessed).
3. Index the baked mesh-pointer table at global address `0x00E23240` with `controlPointId * 10 + sampleSlot`, and return the stored mesh pointer.

This agrees with the upstream data layout:
- `swrSpline_ResetNodeProgress(node)` clears ten consecutive 4-byte entries at `spline_progress_values + node * 5 * sizeof(rdVector2) + 0xFC`; five `rdVector2` values are 40 bytes, exactly ten mesh pointers.
- The upstream header documents `swrModel_Mesh.splineSampleIndex` as the inverse mapping (first sample that hit a mesh), whereas this table is the forward mapping (sample → mesh).
- `swrRace_UpdateRaceProgress` caches the returned pointer in `player->splineTrackMesh`. The ground-raycast fast path uses that mesh as its collision target; the cached-ground path promotes it to `terrainModel`. A change from the previous frame clears a per-racer collision/cache counter.

**Evidence status:** `CODE` in the pinned Steam-PC decompilation and corroborated by the current SW_RACER_RE type/header comments. Exact binary/release identity between those two PC references remains unproven. This function is therefore a high-confidence algorithmic recovery candidate, not permission to copy Steam decompilation source into Boonta. It should be documented/recovered as a discrete table lookup before tackling the remaining three functions.


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

**B. `swrRace_UpdateSplineBinding` (`0x0047FBB0`)

The race struct records the function's result in `splineRebindResult`: `-1 = blocked`, `0 = no rebind`, and `1 = rebound to the mesh the pod is standing on`. The merged upstream [PR #264](https://github.com/tim-tim707/SW_RACER_RE/pull/264) supplies stronger, author-attributed evidence: `swrModel_Mesh.splineSampleIndex` at mesh offset `+0x3C` is the first baked spline sample index that hit that mesh, encoded as `node * 10 + sub-sample` (0 is the unset sentinel). Its commit message explicitly says that `UpdateSplineBinding` uses this inverse mapping to re-seek the cursor to the mesh the pod is standing on. A later commit in the same PR corrected the earlier name "node index" to **sample index**, because `CursorSeekToProgress` divides the supplied progress by 10.

The merged upstream [PR #264 commit `24cda80`](https://github.com/tim-tim707/SW_RACER_RE/commit/24cda80a7e21c151f0b10f2987256347fc5a2332) also documents the bake behavior: if a collision mesh is shared across different spline traversal branches, it is marked with behavior bit `0x8` ("spline-ambiguous"). That bit blocks `UpdateSplineBinding` rebinds and also feeds the judge's not-racing-zone logic.

- **Supported contract:** if a physical ground-contact mesh can be mapped unambiguously back to a baked spline sample, the race cursor can be re-seeked to that sample; return value 1 tells the caller this was a progress event and can trigger lap-crossing logic even without a forward node crossing.
- **Supported blocker:** a mesh carrying behavior bit `0x8` is not a valid rebind target because it is shared between spline branches.
- **Still unknown:** exact null/zero handling, whether the function first compares `terrainModel` and `splineTrackMesh`, all conditions that return -1 vs 0, whether it seeks directly to `splineSampleIndex` or applies a local correction, and how it handles an unset sample index. The public PR notes give the semantic contract but not the function body.

**C. `swrRace_ComputeTrackOffset` (`0x0047FCA0`)**

The race struct annotates `trackOffset` at `+0x118` as a 4-vector whose xyz encode a unit direction from the spline toward the pod and whose w stores raw distance. However, a scan of all 19 C modules in the pinned source tree found only four writes in `swrRace_ResetToSpline` (`swrObj.c:2402–2405`), which assign the neutral-looking value `{0, 0, 1, 1}`; no operational reader or non-initialization writer was found in those modules.

- **Confirmed source fact:** reset writes `trackOffset = {0, 0, 1, 1}`.
- **Unverified annotation:** xyz direction and w distance.
- **Unknown:** whether the original executable still writes/reads this field elsewhere, whether the reconstruction simply omits all uses, the exact origin point, threshold, zeroing behavior, or any AI/handling consumer.

Therefore `ComputeTrackOffset` remains an unresolved stub and the current field comment is not sufficient evidence to specify its algorithm.



### Evidence from upstream mesh/sample mapping — UpdateSplineBinding narrowed further

The merged upstream PR #264 (commit `dabc7c35309fc5bc6f1b26a8590c24c3016ebbb5`) is particularly relevant:
- `swrModel_Mesh +0x3C` was initially called a spline node index, then corrected by merged follow-up commit [`24cda80`](https://github.com/tim-tim707/SW_RACER_RE/commit/24cda80a7e21c151f0b10f2987256347fc5a2332) to `splineSampleIndex`: it records the first of ten baked samples per node that hit that collision mesh. It is a baked inverse lookup from physical mesh back to spline sample.
- `swrSpline_BakeSampleTrackMesh` creates the forward lookup (spline sample → collision mesh); the mesh's `splineSampleIndex` provides the inverse mapping (mesh → spline sample).
- A shared mesh may be hit by samples from more than one spline traversal order. The baker marks this with behavior `unk1 & 0x8` ("spline-ambiguous"); the PR's binary evidence says this specifically blocks `UpdateSplineBinding` rebinding and is also used to mark a not-racing zone.
- `swrSpline_CursorSeekToProgress` converts a sample/progress index into a node band and fractional `segmentT`: band = floor(index / 10), fractional parameter = (index - band * 10) / 10; it then follows the encoded branch bits to rebuild the lookahead.

This supports the following **candidate control flow**, not an implementation claim:

1. Obtain the current ground-contact mesh (from `player->terrainModel`, set by `swrRace_RaycastGround`).
2. Reject meshes which are not a valid track mesh, have no baked sample index (zero sentinel), or are flagged ambiguous (the exact -1/0 result split is not yet verified).
3. If the ground-contact mesh maps to a different unambiguous sample than the current cursor/track chunk, seek the cursor using the mesh's `splineSampleIndex` and report a successful rebind.
4. Otherwise leave the cursor unchanged.

Only the semantic mapping and ambiguous-mesh blocker are supported by upstream decompilation notes; the four control-flow steps above are an explicit **HYPOTHESIS** until the actual function body / matching build is recovered.

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



### Additional field-reader/writer scan

The pinned scan covered the 19 C modules in the `SW_RACER_RE` source tree, not just `swrRace.c`:

- `positionPrev` is seeded from the pod transform in `swrRace_ResetToSpline` (`swrObj.c:2438`) and is subsequently read to derive motion direction and trigger velocities; the explicit `AdvanceSplineCursor` source comment says the finish-line crossing fraction interpolates from this previous position to the current position.
- `splineRebindResult` is reset to 0 in `swrRace_ResetToSpline` and assigned from the return value of `swrRace_UpdateSplineBinding` at the end of `swrRace_UpdateRaceProgress`. The caller treats 1 as a progress/lap-crossing signal.
- `splineTrackMesh` is set to NULL during reset, assigned from the cursor's baked track-mesh table during race progress, then used as the fast ground-raycast target and as the cached-ground terrain model.
- `trackOffset` is only set to its reset value in the scanned C modules. Its operational semantics remain unconfirmed.

This scan strengthens the A/B contracts but leaves C deliberately blocked on additional evidence.

**No implementation is authorized by this note.** These contracts guide the next RE-002 evidence pass. Any eventual independent implementation must be separately scoped, licence-clean, based on confirmed executable/version evidence and validated against owner-local runtime traces before it can be considered for Boonta's own code.


## Upstream work already completed vs. the unfinished handoff

A review of the merged public pull requests in the source project's upstream repository `tim-tim707/SW_RACER_RE` confirms that most of the generic spline foundation was already completed by earlier contributors. This prevents RE-002 from reopening solved work.

| Upstream PR | Merged | What it actually delivered | Relevance to the current gap |
|---|---|---|---|
| [#41 — complete LoadSpline byteswap + map spline runtime](https://github.com/tim-tim707/SW_RACER_RE/pull/41) | 2026-06-08 | Spline loading, point/graph structures, cursor primitives, interpolation, evaluation, projection and post-load baking map | Foundation already in current source |
| [#50 — map track/level load pipeline](https://github.com/tim-tim707/SW_RACER_RE/pull/50) | 2026-06-08 | Named the `InitTrack` orchestration helpers for model/spline/environment setup, starting grid and racer spawning | Use its established track-start call graph; do not remap from scratch |
| [#120 — name engine-fire FX + spline-cursor functions](https://github.com/tim-tim707/SW_RACER_RE/pull/120) | 2026-06-18 | Added address names and prototypes for `AdvanceSplineCursor`, `UpdateSplineBinding`, `ComputeTrackOffset` (plus two fire-effect functions); **declaration/naming only** | This is the unfinished race-specific handoff |
| [#208 — reimplement cursor + evaluation runtime (14 functions)](https://github.com/tim-tim707/SW_RACER_RE/pull/208) | 2026-07-01 | Implemented 14 generic spline cursor/evaluation functions and reported clean build/link; left the separate post-load baking follow-up | Confirms generic cursor engine is not the missing piece |

The merged PR metadata reports #120 changed only one file with 14 additions; its own description explicitly says the five functions were declaration-only. PR #208 is a separate later merge and implemented the generic spline cursor/evaluation runtime. These are separate components: the race-specific cursor reconciler is called from `swrRace_UpdateRaceProgress`, while the generic spline engine provides graph traversal, interpolation and cursor evaluation.

**RE-002 therefore targets the gap left by #120, not the work completed in #41/#50/#208.** The three remaining functions need to be recovered from a matching executable/decompilation or described from verified call/data evidence; their implementation is not present in the current public upstream master.


## Independent IDA research cross-check — `everalert/swe1r-decomp`

A third public reverse-engineering repository was inspected at pinned commit `8d066b9c12ecb57bd819aaab586fd6bd2dd078a7`:

- Repository: [everalert/swe1r-decomp](https://github.com/everalert/swe1r-decomp)
- Description: “work on understanding star wars racer binary”
- Snapshot: `master`, last pushed 2025-05-23
- Repository tree contains an IDA database at `idapro/SWEP1RCR.EXE.idb`, plus `idapro/functions.txt`, `idapro/names.txt` and subsystem notes. The database itself was **not downloaded, opened, uploaded or committed** in this pass.
- No root `LICENSE` or SPDX licence was identified in the inspected tree. Treat its notes/database as read-only research material; do not copy its code or redistribute its IDB. The exact executable checksum, region and release identity are not established in the inspected notes.

### Independent function-size and naming metadata

The repository's IDA function inventory independently lists these functions and sizes:

| Address | Provisional IDA name | Function size | Stack/frame metadata | Current SW_RACER_RE mapping |
|---:|---|---:|---:|---|
| `0x0047F890` | `Unk_LapComp_GetModelMesh_47F890` | `0x44` | `0x08` frame | `swrRace_GetTrackMeshAtCursor` |
| `0x0047F8E0` | `Unk_Test_LapTiming__47F8E0` | `0x2C7` | `0x60` frame | `swrRace_AdvanceSplineCursor` |
| `0x0047FBB0` | `Unk_Test_GroundMeshTransitionCheckMaybe__47FBB0` | `0xED` | `0x10` frame | `swrRace_UpdateSplineBinding` |
| `0x0047FCA0` | `Unk_Test_UpdateNormalToSplineMaybe__47FCA0` | `0x125` | `0x64` frame | `swrRace_ComputeTrackOffset` |
| `0x0047FDD0` | `Unk_Test_FinalizeLapCompletion_47FDD0` | `0x1D3` | `0x0C` frame | `swrRace_LapCompletion` |
| `0x0047FFB0` | `Unk_Test_UpdateLapCompletion__47FFB0` | `0x10D` | `0x0C` frame | `swrRace_UpdateRaceProgress` |

Evidence: `idapro/functions.txt` lines 1418–1421 and the matching names in `idapro/names.txt` lines 1554–1557 (the pinned files are [functions.txt](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt) and [names.txt](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/names.txt)). These lengths are useful for confirming IDA's function boundaries and prioritising a later disassembly extraction. They do **not** supply the instructions or prove an exact executable match to either of the other PC snapshots.

### Independent confirmation of the race-spline state

The IDA author's `idapro/notes/Entity_Test.txt` independently records:

- `Test +0xEC`: a mesh associated with the spline point at current lap completion; referenced by `0x47FBB0` and `0x47FFB0`.
- `Test +0xF0`: previous value of `+0xEC`.
- `Test +0xF4`, `+0xF8`, `+0xFC`, `+0x100`: notes say these slots are set to zero by `0x47FBB0`. This is consistent with the current reconstruction's observation that the two projection out/result pairs are retail-zero/vestigial, though the old IDA note's field labels are unresolved.
- `Test +0x10C`: counter associated with backward spline-point movement, referenced by `0x47FFB0`; the author explicitly marks its precise semantics uncertain.
- `Test +0x10E`: value appears to be only `-1`, `0` or `1` and is calculated by `0x47FBB0`, independently corroborating the later SW_RACER_RE annotation for `splineRebindResult`.
- `Test +0x118`: vector associated with `0x47FCA0`, but the old IDA note leaves its meaning unknown. This supports keeping the operational meaning of `trackOffset` at UNKNOWN until a body or reader/writer evidence is recovered.
- `Test +0x140`: identified tentatively as the actual mesh the pod is currently standing on; the note says it matches `+0xEC` when the pod is following the track and cites `0x47FBB0`. This is consistent with the ground-contact mesh being used for cursor re-binding, but the author marks the pointer's exact structure/type as uncertain.

The same repository's `idapro/notes/RaceMechanics.txt` says spline cursor fields at offsets `+0x10` are written in the `0x47E8B0` routine while that routine is reached through `GroundMeshTransitionCheckMaybe__47FBB0`. `0x47E8B0` is the current source's `swrSpline_CursorSeekToProgress`. This independently supports the claim that the binding/recovery function re-seeks the cursor through the generic spline engine, rather than merely refreshing a mesh pointer.

Finally, `idapro/notes/Models.txt` marks the model-behaviour bit `@03` as lap-completion-related and explicitly references `0x47FBB0`. This is consistent with the later upstream description of behavior flag bit `0x8` as the spline-ambiguous/rebind blocker. The old note does not itself explain the exact bit meaning, so the stronger semantics still come from upstream PR #264.

### Updated evidence assessment

| Finding | Evidence label | Confidence | Remaining limit |
|---|---|---|---|
| `0x47FBB0` interacts with the spline seek routine `0x47E8B0` | `COMMUNITY-REPORT` (IDA notes) | `SUPPORTED` | The public repository provides call-path notes, not function pseudocode or a full assembly listing |
| `Test +0x10E` is a small status value derived by `0x47FBB0` | `COMMUNITY-REPORT` + corroborating SW_RACER_RE type annotation | `SUPPORTED` | Exact conditions for -1/0/1 remain unknown |
| `Test +0x140` is the currently stood-on mesh used during rebind | `COMMUNITY-REPORT` | `SUPPORTED` | Old note says “appears” and leaves type/structure uncertain; compare with the current typed `terrainModel` / collision-hit path |
| `Test +0x118` meaning | `COMMUNITY-REPORT` | `UNKNOWN` | Independent IDA note also leaves it unknown; do not rely on the later direction/distance comment as a verified operational contract |
| Function sizes at 0x47F8E0 / 0x47FBB0 / 0x47FCA0 | `CODE` (IDA metadata) | `CONFIRMED` for this IDA project only | Target executable/build not identified; sizes do not recover function semantics |

**Next evidence step:** recover only the two smaller, bounded functions `0x47FBB0` and `0x47FCA0` from this IDA project if the raw IDB can be inspected locally in an appropriately licensed IDA installation. For `0x47F8E0`, the function is 711 bytes and will need its full disassembly/callers/field accesses; do not infer its full implementation from the short source comment. Keep the IDB local and do not copy any code into Boonta. No function body was extracted in this pass.


### Follow-up: exact slot conversion and an independent caller for `GetTrackMeshAtCursor`

The frozen Steam assembly for `FUN_0047f890` provides more detail than the initial C pseudocode:

- It loads the cursor's `segmentT` at cursor offset `+0x08`, multiplies by the sample scale at `0x004ADF38), and compares the result against the boundary constant at `0x004ADF40`.
- On the less-than branch it subtracts the correction constant at `0x004ADF64`, then calls the x87 float-to-integer helper at `0x0049ED20`.
- It then resolves the branch-aware node via `FUN_0044E620(cursor, 0)`, computes `node * 10 + sampleSlot`, and loads a pointer from `0x00E23240`.

The companion generic seek routine `FUN_0047e8b0` uses integer division by 10 for the node band and the complementary constants `0x004ADF38` / `0x004ADF3C` to recover the fractional `segmentT`. The constants are used consistently with the ten-samples-per-node layout. Their raw values were not retrieved from the inspected export files; do not hardcode guessed decimal literals from this evidence alone. The less-than branch and correction constant are exact assembly observations; whether the correction is best described as floor, truncation correction or a special endpoint convention should be confirmed from the actual constant value and compiler helper semantics.

An independent Steam-PC caller strengthens the function's role:
- `FUN_004744B0` calls `FUN_0047f890(player + 0xAC)` on one path to obtain the mesh under the current spline cursor.
- It obtains the mesh behavior through `FUN_004318B0` and rejects the candidate if no mesh is returned or if the terrain/behavior flags at mesh behavior offset `+0x2C` intersect `0x16000`.
- A separate path performs a ground/model raycast first, then the same behavior-flag validation. The surrounding function is named in the independent IDA inventory as a possible respawn-point search, but that name is provisional; the secure claim is that the mesh lookup participates in selecting/validating a candidate location.

The independent IDA name table calls the global at `0x00E23240` `Unk_SplinePointMeshes_E23240`, consistent with the sample → mesh pointer table. Its notes also state that mesh pointers at `Test +0xEC/+0xF0` are read by race-progress and the mesh/collision path.

**Updated confidence:** the lookup purpose and table indexing are `SUPPORTED` by two PC research snapshots plus an independent caller. Exact conversion edge behavior and executable-build equivalence remain `UNKNOWN` until the constants and target binary identity are resolved.


## 2026-11-04 — Steam-PC recovery of the three race-spline routines

A targeted review of the frozen Steam-PC Ghidra export found C pseudocode for all three race-specific functions that remain HANG("TODO") in the public SW_RACER_RE reconstruction. This advances the earlier address-only correlation: the bodies can now be described from a second PC snapshot, while the independent IDA project supplies function-size and field/caller corroboration.

**Pinned evidence**
- SW_RACER_RE: tim-tim707/SW_RACER_RE commit 258f67aa858ba2e281ce8a6791e49c554b85fae0, especially [swrRace.c](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c) and [swrRace.h](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.h).
- Steam-PC decompilation: DeonPoncini/swep1r_decomp commit d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef, [src/_text23.c](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c#L126-L389): FUN_0047f8e0 at line 126, FUN_0047fbb0 at line 215, FUN_0047fca0 at line 257, and caller FUN_0047ffb0 at line 360.
- Independent IDA metadata: everalert/swe1r-decomp commit 8d066b9c12ecb57bd819aaab586fd6bd2dd078a7, [functions.txt](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt) and [Entity_Test.txt](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/notes/Entity_Test.txt). Its IDB was not opened or redistributed.

**Build boundary:** the Steam export explicitly targets the Steam release. The exact executable hash/release behind the SW_RACER_RE and IDA snapshots has not been established, and matching numeric addresses do not prove identical code. Treat the following as supported PC behavior hypotheses, not retail-build equivalence and not GameCube/Wii evidence. No source code was copied.

### swrRace_AdvanceSplineCursor — 0x0047F8E0

The Steam pseudocode shows a position-driven cursor reconciler, not a speed-times-delta cursor integrator:

1. It initializes the forward/backward outputs and sub-frame crossing time to zero, then evaluates the current spline cursor into a local frame.
2. It compares the pod's current position (transform position fields at +0x50..+0x58) and previous position (positionPrev at +0x16C..+0x174) against a plane derived from the evaluated spline frame.
3. If the pod has crossed the current plane in the forward direction, it advances cursor segmentT in 0.01 increments, reevaluating the frame until the pod is no longer beyond the next plane or the cursor's forward-end flag prevents further stepping. It sets the forward output.
4. If no forward crossing is reported and the cursor has not reached its backward-start boundary, the reverse path steps segmentT backward in 0.01 increments and sets the backward output. The cursor start/end flags are the traversal guards; this is distinct from the sign of the pod's velocity field.
5. When forward traversal enters node 0 (the start/finish boundary), it computes the crossing instant by linearly interpolating the previous and current pod positions against the plane. The result is multiplied by the raw frame delta for sub-frame lap timing. If displacement along the plane normal is below 0.01, the crossing time is set to zero.

The IDA inventory independently gives this function an extent of 0x2C7 bytes and a 0x60 stack frame. The public header's contract independently describes node-plane stepping, node-0 crossing interpolation and the same 0.01 movement threshold. Together these sources support the algorithm outline above; they do not identify every endpoint/branch edge case or establish the executable identity.

### swrRace_UpdateSplineBinding — 0x0047FBB0

The Steam pseudocode makes the mesh-to-spline inverse mapping substantially more precise:

- Rebinding is considered only when the current cursor-derived mesh (player + 0xEC) and the current terrainModel (player + 0x140) are both non-null and differ, and race flag bit 0x20000000 is clear.
- It queries the terrain mesh behavior. If the behavior record exists and bit 0x8 is set, the function returns -1 (rebind blocked). This agrees with the upstream PR #264 evidence that a mesh shared by multiple spline branches is marked spline-ambiguous.
- Otherwise it returns 1 for the rebind. If the terrain mesh's 16-bit splineSampleIndex at +0x3C is nonzero, it calls swrSpline_CursorSeekToProgress (0x0047E8B0) with that sample index, then calls swrRace_AdvanceSplineCursor to reconcile the reseeded cursor against the pod's current position.
- It refreshes the cursor-derived track mesh and the associated sample-spacing/projection fields before returning. A zero sample index skips the seek/advance pair but does not undo the rebind result.

This refines the earlier candidate flow: the status is -1 for the ambiguous-mesh rejection, 0 when the rebind gate is not entered, and 1 when a changed, valid terrain mesh is accepted. The exact semantic meaning of race flag bit 0x20000000 remains unlabelled here.

The IDA inventory lists 0x0047FBB0 as 0xED bytes with a 0x10 stack frame. Its notes independently connect this routine to CursorSeekToProgress and describe the +0x10E status as -1/0/1.

### swrRace_ComputeTrackOffset — 0x0047FCA0

The Steam pseudocode evaluates the spline cursor frame, projects the pod onto the local cross-section plane defined by that frame, and subtracts that projected point from the pod's current position:

- The magnitude of this offset is stored at player + 0x124 (the fourth component of the trackOffset vector beginning at +0x118).
- When the magnitude is greater than 0.1, the xyz components at +0x118..+0x120 are normalized to a unit direction from the projected spline point toward the pod.
- At or below 0.1, xyz is set to the fallback direction (0, 0, 1); the measured magnitude remains stored at +0x124.

This establishes the data written by the routine and the small-distance fallback. It does not prove how every downstream consumer interprets the vector, whether the projection is the globally nearest point on a curve, or what physical units the source's coordinate system uses.

The IDA inventory lists 0x0047FCA0 as 0x125 bytes with a 0x64 stack frame. Its older field note correctly leaves +0x118 unknown; the Steam body now supports the direction/magnitude write pattern, but the target executable identity remains unresolved.

### Caller sequence and practical consequence

The Steam caller FUN_0047ffb0 confirms the same overall order as the public swrRace_UpdateRaceProgress reconstruction:

AdvanceSplineCursor → cache previous/current track mesh → update sample-spacing and projection slots → clear a cache when the mesh changes → UpdateSplineBinding → ComputeTrackOffset → lap completion and forward/backward movement counters.

The key architectural separation is now clearer: the cursor advances by geometric node-plane crossings based on actual pod position; ground-mesh rebinding can reseed that cursor from the baked mesh-to-sample index; and lateral offset is calculated separately from cursor progress. These are three related but distinct operations.

### Updated evidence assessment

| Finding | Evidence label | Confidence | Remaining limit |
|---|---|---|---|
| Cursor advancement uses position-vs-spline-frame plane tests and 0.01 segment steps | CODE (Steam-PC pseudocode) + corroborating public header | SUPPORTED | Exact source-build identity and all branch/end-point cases remain unresolved |
| Node-0 crossing time is interpolated from previous/current position and scaled by raw frame delta | CODE + public header | SUPPORTED | Exact retail-build identity and unusual zero/near-zero movement behavior need runtime validation |
| Mesh rebind uses terrain mesh splineSampleIndex and generic progress seek | CODE + upstream PR #264 + IDA caller notes | SUPPORTED | The 0x20000000 gate's meaning and all malformed/null cases remain unknown |
| Behavior bit 0x8 blocks a mesh-to-spline rebind | CODE + upstream PR #264 | SUPPORTED | Applies to the inspected PC source family only |
| trackOffset.xyz is a normalized projected-to-pod direction above 0.1, otherwise fallback up; w stores magnitude | CODE (Steam-PC pseudocode) | SUPPORTED | Downstream gameplay semantics and target-build equivalence remain unverified |

**Next bounded investigation:** compare the three Steam function bodies against any lawful local binary/disassembly for the exact SW_RACER_RE target build, if such an artifact is available; otherwise trace every reader of trackOffset, splineRebindResult and the movement flags in the pinned source to establish their downstream consumers. Do not port these PC algorithms into GameCube/Wii without a separate target-specific specification.


## 2026-11-04 — Downstream race-progress consumer trace (PC reconstruction)

This pass follows the outputs of `swrRace_AdvanceSplineCursor` and the derived racer fields beyond the three function bodies. It uses only the same pinned public SW_RACER_RE source revision; it does not establish Steam/retail executable identity or GameCube/Wii behavior.

**Pinned source:** [SW_RACER_RE `swrRace.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c) (blob `c623f7fddb7a9bebb3dbe9919e0f24e49d7842d3`), [`swrObj.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c) (blob `f3d0056b624911e7715a4217cead3890a2b3ba84`), and [`types.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types.h) (blob `1519cd257d5d65e5575cce1ecd9aa0b2fe22686b`).

### Recovered consumers and state transitions

1. **Forward/backward outputs feed lap gating and judge progress state.** In `swrRace_UpdateRaceProgress` (lines 4771–4800), the local `movedForward` and `wentBackward` outputs from `swrRace_AdvanceSplineCursor` are not stored as fields. They are used immediately:
   - The lap-crossing test is enabled when `movedForward != 0` **or** the mesh-binding result equals 1 (line 4789).
   - A backward report increments `checkpointCount` and resets `moveTick` to zero (lines 4790–4793).
   - A forward report clears `checkpointCount`; when the same update did not also report backward movement, `moveTick` increments up to 200 (lines 4794–4798).
   - The integer binding result is then copied to `splineRebindResult` at +0x10E (line 4799).

2. **The judge reads the backward-progress counter, not the stored binding result.** `swrObjJdge_IsRacerRacing` checks that the racer is not finished and then returns true when `checkpointCount > 4` **or** `speedValue` is below the not-racing speed threshold (lines 1385–1400). A preceding course-specific exception returns false inside planet 1 / track 3's configured rectangle when the stood-on terrain mesh has behavior bit 0x8 (lines 1390–1394). The source therefore supports a link from repeated backward cursor reports to the judge's race-status decision; it does not justify renaming the field to a confirmed “off-track timer.”

3. **`moveTick` gates an idle accumulator, but its downstream effect is not recovered.** `swrRace_LapCompletion` adds frame delta to `idleTick` while `moveTick < 9`, otherwise clears `idleTick` (lines 4709–4712); lap completion also clears it on the open-track completion path and when a finish-line crossing is accepted (lines 4724–4736). No comparison or other read of `idleTick` was found in the pinned public reconstruction's indexed references. Its eventual consumer/effect remains UNKNOWN.

### Unresolved stored fields: do not infer consumers

- **`splineRebindResult` (+0x10E):** the pinned public reconstruction initializes it to zero during racer initialization (`swrObj.c` lines 2393–2409) and writes the current `binding` value at the end of `swrRace_UpdateRaceProgress` (`swrRace.c` line 4799). The searched public source has no other named read. The binding value does affect the immediate lap-crossing gate at line 4789, before it is stored. A separate later consumer of the field itself is **not recovered**.
- **`trackOffset` (+0x118..+0x124):** the public reconstruction initializes the vector to (0,0,1,1) in `swrObj.c` lines 2402–2405. Its `swrRace_ComputeTrackOffset` definition remains `HANG("TODO")` at `swrRace.c` lines 4762–4766, and no named field read exists in the searched public source. The Steam-PC pseudocode describes the writer, but these findings do not identify a downstream reader. Do not label it as a steering/AI/collision input without a reader/caller chain.
- **The movement outputs:** the public reconstruction exposes them as local outputs, and its race-progress caller consumes them as listed above. A broader Steam-PC xref inventory for every use outside this caller is not complete.

### Evidence assessment and next question

| Finding | Evidence label | Confidence | Remaining limit |
|---|---|---|---|
| Forward movement enables lap crossing and clears `checkpointCount` | CODE (pinned SW_RACER_RE) | CONFIRMED-IN-SOURCE | Exact executable/release identity remains unresolved |
| Backward movement increments `checkpointCount`, resets `moveTick`, and the judge checks `checkpointCount > 4` | CODE (pinned SW_RACER_RE) | CONFIRMED-IN-SOURCE | Do not infer a frame timer or universal off-track rule |
| Stored `splineRebindResult` has no named reader in the inspected public source | CODE search + pinned source | UNKNOWN consumer | Steam-wide xrefs and omitted/unimplemented source consumers may exist |
| `trackOffset` writer and readers are missing from the public reconstruction | CODE (field init and TODO stub) | UNKNOWN consumer | Steam reader inventory and exact target build identity are incomplete |
| `idleTick` is written/reset based on `moveTick` and lap completion | CODE (pinned SW_RACER_RE) | CONFIRMED-IN-SOURCE | A consequential reader/effect has not been found |

**Next bounded RE-002 task:** follow the judge's F2 race-progress call and F0/status decisions into their actual caller/state transitions, while keeping `checkpointCount`, `splineRebindResult`, and terrain behavior bit 0x8 separate. Then perform a targeted Steam-PC xref search for the racer object fields `+0x10E` and `+0x118..+0x124`; reject apparent offset matches unless the base object is demonstrably the racer structure. If the exact SW_RACER_RE target executable is not available locally, record that executable-level equivalence remains blocked rather than infer from Steam.


## 2026-11-04 — Judge F2 / HUD F3 integration of the progress fields

A follow-up through the judge callbacks narrows the effect of the previously recovered counters and separates HUD state from standings/AI ranking.

### F2: race tick and lap timing

At `swrObjJdge_F2` (0x0045EA30), judge state 1 iterates the score array and calls `swrRace_UpdateRaceProgress` for active racers (and also refreshes progress for already-finished entries in the branch shown at lines 938–946). When a lap crossing is reported:
- the pre-crossing frame slice `crossTime` is added to the current lap and total (lines 986–993);
- the remainder of the raw frame delta is added to the next/current lap (lines 1027–1039);
- on the configured final lap, the score is marked finished, the pod's local/boost flags are cleared, its AI flag is enabled and `FLAG1_FINISHED` is set (lines 994–1024).
After the per-racer pass, standings are recomputed (line 1045). When all local racers have finished, the judge enters state 2 and extrapolates still-unfinished racers' displayed total time from their current progress; in state 2 it continues refreshing each racer's progress (lines 1047–1066).

This is the concrete consumer chain for the sub-frame crossing result: cursor movement -> lap-crossing gate -> `crossTime` split -> lap counters/finish state. The locally stored `splineRebindResult` field is not needed for this chain after the immediate `binding == 1` test in `swrRace_UpdateRaceProgress`.

### F3: checkpoint counter controls the local HUD guide arrow

The public source's `swrObjJdge_UpdatePlayerHUD` calls `swrObjJdge_IsRacerRacing` only during judge state 1. If the helper returns zero, it clears `FLAG0_GUIDE_ARROW` and hides the guide node; otherwise it enables the flag and points the node at a spline position 0.5 ahead of the cursor (lines 1402–1440). Judge F3 calls this HUD function for the local player slots when the state is not 3, 4 or 5 (lines 1719–1748).

Therefore `checkpointCount > 4`—which is increased by backward cursor reports and reset by a forward report—has a directly evidenced consumer: the helper's returned racing/not-racing value, which gates the local HUD spline guide arrow. A second condition in that helper is the low-speed threshold. The planet-1 / track-3 terrain-zone exception (behavior bit 0x8 plus an X/Y rectangle) can force the helper to return zero. The inspected call path does **not** show this helper selecting race placement or directly commanding AI steering.

### Standings and AI tethers use lap progress / finish time

`swrObjJdge_GetRacerProgress` derives its key from `results_P1_Lap`, `lapCompMax` and `lapComp` (lines 413–426). `swrObjJdge_GetRacerRankValue` uses that progress for unfinished racers and `maxRaceTime - total_time` for finished racers (lines 429–435). `swrObjJdge_UpdateStandings` uses those rank values to assign positions and progress gaps, and tags the nearest AI rivals to local players for catch-up tethering (lines 438–473 and onward). This is a separate path from `checkpointCount`, `splineRebindResult` and `trackOffset`.

### Refined evidence conclusions

- **Backward/forward outputs:** confirmed immediate inputs to lap-crossing eligibility and the checkpoint/move counters. The known checkpoint consumer is the HUD guide-arrow gate through `IsRacerRacing`; no direct AI/standings use is demonstrated.
- **Lap timing:** confirmed F2 receives the crossing result, applies the pre-crossing `crossTime` to the completed lap, and assigns the raw frame remainder to the next lap.
- **`splineRebindResult` (+0x10E):** still no named reader found after its write. The transient local `binding` value is used immediately to permit the lap-crossing check.
- **`trackOffset` (+0x118..+0x124):** still no consumer identified. Its public reconstruction writer is a TODO stub; no steering, AI, standings or ground-contact role should be claimed from these sources.
- **Standing rank / catch-up:** based on lap progress and finish time, with separate leader/local-player/pacer gaps. Do not conflate these values with the lateral trackOffset vector.

**Sources:** [`swrObj.c` race tick](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L912-L1067), [HUD helper](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L1385-L1440), [F3 HUD dispatch](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L1719-L1748), and [standings rank path](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L413-L473). All findings remain confined to this pinned PC reconstruction.

## 2026-11-04 — Bounded Steam-PC field-reader search for spline outputs

This follow-up tests whether the stored outputs from the three race-spline routines have identifiable downstream readers in the pinned Steam-PC export. It is deliberately a bounded static search, not a claim that every indirect, aliased, or optimized access has been enumerated.

**Pinned sources**
- Steam-PC Ghidra export: `DeonPoncini/swep1r_decomp` at `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`, especially [`src/_text23.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c#L257-L398), [racer initialization `FUN_00475ad0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00475ad0.c#L120-L145), and [camera-manager snapshot `FUN_00451d60`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00451d60.c#L1-L40) / [restore `FUN_00452aa0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00452aa0.c#L210-L235).
- Independent public reconstruction: `tim-tim707/SW_RACER_RE` at `258f67aa858ba2e281ce8a6791e49c554b85fae0`, [`types.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types.h) for the racer field layout and [`swrObj.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.h) for named camera-manager routines.

### Search method and deconfliction

The pinned Steam-PC repository was searched for the literal field offsets in both typed and generic forms: `0x10e`, `0x118`, `0x11c`, `0x120`, and `0x124`, including direct float/short access patterns. Results were checked against the candidate function and its apparent base object; identical numeric offsets are not treated as the same field unless the base is demonstrably the racer object.

Two tempting `+0x118..+0x124` matches are not evidence of a racer-field read:
- Steam `FUN_00451d60` copies a camera object's state slots `+0x118/+0x11c/+0x120/+0x124` into its staged snapshot at `+0x274..+0x280`; the corresponding restore is `FUN_00452aa0`. The pinned SW_RACER_RE header identifies these addresses as `swrObjcMan_CommitStagedCamera` and `swrObjcMan_UpdateChaseCamera`, respectively. The same offsets occur in a different camera-manager record.
- Steam `FUN_00482f10` writes a float at `param_1 + 0x118`, but the bounded search did not establish that `param_1` is the racer object. It is therefore an untyped candidate, not a confirmed reader or consumer of `trackOffset`.

### Field-by-field result

| Racer field | Confirmed Steam-PC initialization/writer in inspected sources | Bounded search result | Conclusion |
|---|---|---|---|
| `splineRebindResult` (+0x10E) | `FUN_00475ad0` initializes it; `FUN_0047ffb0` stores the `FUN_0047fbb0` result as a short at the end of `src/_text23.c` | No direct read of the short at this racer offset was found. Other `0x10e` hits were initialization/writer contexts or unrelated literal/constant uses. | A later field consumer is **UNKNOWN / not recovered**. The transient local `binding` value is still used immediately in the lap-crossing gate before the value is stored; do not confuse that local use with a read of the stored field. |
| `trackOffset.x/y/z` (+0x118/+0x11C/+0x120) | `FUN_00475ad0` initializes the vector; `FUN_0047fca0` writes the projected direction/fallback | Exact direct float searches returned the writer in `src/_text23.c`; the `+0x118` search also found an untyped write in `FUN_00482f10` and camera-state copies, neither established as a racer-field access. No verified downstream racer read was identified. | Downstream effect remains **UNKNOWN**. Do not label it steering, AI, collision, ground contact, or rendering input yet. |
| `trackOffset.w` (+0x124) | `FUN_00475ad0` initializes it; `FUN_0047fca0` stores the measured magnitude | The bounded exact float search returned the `FUN_0047fca0` writer; other generic `+0x124` hits belonged to different object layouts. | No verified downstream racer read identified; semantics beyond “stored magnitude” remain **UNKNOWN**. |

The public reconstruction's field declarations and Steam-PC writer are mutually consistent about the racer layout, but numeric offset matches alone are insufficient to upgrade a candidate xref. This search narrows the public evidence; it does **not** prove no reader exists in the Steam executable.

### What would resolve the remaining question

A decisive result needs a complete typed xref/data-flow pass over the exact local Steam-PC executable (or its matching analysis database), including register-relative accesses and aliases, with the racer base pointer followed from its creation/callers. The current public Steam export and the pinned SW_RACER_RE source do not establish that complete chain. If the owner does not have the matching lawful executable and analysis context, keep these readers marked UNKNOWN rather than inventing a gameplay role.

**Platform boundary:** all findings above are Steam-PC source/search evidence only. They establish no Windows retail-build identity, N64, Dreamcast, GameCube, or Wii behavior. No binary, ROM, disc image, BIOS, extracted asset, analysis database, or third-party code was copied or uploaded.


## 2026-11-10 — N64 static-recompilation project status refresh

A current source-and-release review strengthens the N64 reference set without changing the GameCube/Wii target:

- Repository: [sp00nznet/racer](https://github.com/sp00nznet/racer), pinned at commit [`694c5663b3a7c30e2862fc240344f34683f99a9c`](https://github.com/sp00nznet/racer/commit/694c5663b3a7c30e2862fc240344f34683f99a9c), a static recompilation of the USA NTSC N64 binary using N64Recomp, N64ModernRuntime and RT64.
- Its pinned README reports Phase 8 / in-game and identifies 878+ discovered functions, boot/main-loop stability, PI-DMA asset loading, display lists processed by RT64, visible intro/title/menu/race frames, controller + EEPROM, audio, and a tournament race on the Boonta Training Course. The same status table still labels **Playable Build: IN PROGRESS** and widescreen **EXPERIMENTAL**. This is meaningful N64-on-PC runtime progress, but not a full decompilation and not independent evidence of GameCube/Wii behavior.
- The latest indexed release is [v0.4.0, 2026-10-30](https://recomp.gg/g/star-wars-episode-i-racer); do not infer completion from release availability.
- The repo's [LICENSE](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/LICENSE) scopes MIT to the tools, runtime, build files and docs, while explicitly excluding the commercial game and generated code derived from the user's ROM. No generated recompilation output or game asset may be copied into Boonta.
- The pinned [README](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/README.md) says macOS uses Xcode/Metal and Homebrew SDL2 and that the Mac build was compile-checked only. It is therefore not a reason to ask the owner to install another toolchain or run another local build.

**Use in RE-002:** treat this as an N64 runtime/bring-up case study. It may provide testable hypotheses about N64 execution, libultra, PI DMA, RSP task routing, display-list flow, controller and audio. Each hypothesis still needs an exact source/function or reproducible observation, and none transfers automatically to the GameCube/Wii target. Do not create a competing N64 implementation in Boonta.

## 2026-11-10 — N64 texture-block reuse path

A pinned source audit found that `swe1r-assets@922ef535f6598a1330ff93d6b07258956f990b34` already has N64 release selectors for a dedicated big-endian texture block (ID 1, 1,648 entries) and a model-material-to-texture PNG exporter. The upstream `SWE1R.Assets.Blocks.Original` project also embeds a full N64 texture-block reference resource at `Resources/out_textureblock.bin/n64.bin` (2,741,112 bytes; SHA-1 `9130090c3ceafff6ed05609045909f54f666e54f`) and a full N64 USA model-block reference resource at `Resources/out_modelblock.bin/n64_us.bin` (12,406,512 bytes). These are game-derived resource fixtures, not covered by the parser library's MIT code licence; do not copy them into Boonta or CI.

The N64 USA model catalogue names item 0087 `Pupp_Racer_Anakin_Skywalker` with a 68,284-byte payload; the owner-local Pupp candidate has the same decoded size and a successful structural parse, which is a strong candidate match but not yet a proven item-index mapping. The CLI exporter requires complete model- and texture-block files, but the lower-level `MeshMaterialExporter` accepts a single parsed `MeshMaterial` plus the texture block, so a small adapter can likely use the decoded Pupp graph without rebuilding the full outer model block. Existing UV logic is also documented: scale Tc by 4096 or 8192 on doubled axes and apply child flip flags, while leaving material flip/offset and child-selection caveats explicit.

The source tree's reference block removes the discovery uncertainty, but not the redistribution/licensing boundary: any actual export used by Boonta must run locally against owner-controlled inputs, and extracted textures remain private. Reuse the existing MIT decoder/exporter rather than writing a new PNG/palette path; do not copy the upstream embedded commercial resources or publish any extracted files. Full source review and compatibility gates: [N64 texture-block reuse audit](N64_TEXTURE_BLOCK_REUSE_AUDIT_2026-11-10.md).
