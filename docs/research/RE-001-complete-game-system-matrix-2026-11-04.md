# RE-001 — complete-game system inventory and evidence gaps

**Research snapshot:** 2026-11-04  
**Purpose:** consolidate the existing PC-first plan, SW_RACER_RE study, route/spline dossier and Boonta implementation map into one system-level inventory. This is a research deliverable, not a claim of platform parity or a finished game.

## Executive decision

The existing clean-room GameCube/Wii project is an engineering scaffold, not a complete reconstruction. The next phase must understand the full game loop and its dependencies before adding more isolated prototype features.

The best current public code-level reference is still the Windows-PC project [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE), but the previously pinned snapshot is stale. Its upstream `master` was rechecked at **`258f67aa858ba2e281ce8a6791e49c554b85fae0` (2026-10-25)**. The upstream README explicitly says it documents and re-implements selected functions, not a full decompilation or matching build; its dated 71.2% figure counts functions analysed, not completed systems. The repository declares AGPL-3.0. Keep it a read-only evidence source; do not copy or adapt code into Boonta without a separate licensing decision.

**Important correction:** source-level `HANG("TODO")` occurrences are unfinished reconstructions in SW_RACER_RE, not missing features in the retail game. They must not be translated into a claim that the original game lacks those functions. A `HANG` can also be an intentional invalid-state guard. Counts below describe only the inspected source files, not the whole upstream repository and not missing game features.

## Consolidated system matrix

Evidence vocabulary:
- **PC CODE** — directly visible in the pinned SW_RACER_RE source. It is PC-only evidence.
- **BOONTA CODE** — present in this repository's clean-room implementation.
- **AUTOMATED** — a named host/build/CI check exists; this is not human gameplay acceptance.
- **UNKNOWN / BLOCKED** — the behavior or native target mapping is not established.

| System | What the complete game requires | Existing evidence / code map | Main unknowns and current gap | Priority |
|---|---|---|---|---|
| Boot, platform services and configuration | Startup, device selection, timing, configuration, resource roots, shutdown and recovery | PC source has `src/Main/swrMain.c`, `src/Swr/swrConfig.c`, `src/Swr/swrLoader.c`, `src/Platform/*`; current Boonta has a native devkitPPC/libogc build path | Original GC/Wii startup/resource assumptions are not proven. PC Windows services are not portable. PC LZSS decompression remains a `HANG("TODO")` at `swrLoader_DecompressLZSS` in the pinned snapshot. | P1 |
| Front-end and race state machine | Boot → profile → main menu → vehicle/course selection → grid/countdown → race → finish/results → next event/retry | PC entry points in `swrRace.c`: main menu, vehicle selection, course selection/info, results, hangar, settings; save functions are present | The complete transition graph, cancellation/restart edges, result commit and console equivalents need an end-to-end trace. Several PC menu entry points remain HANG stubs. | P0 |
| Tournament, progression and economy | Tournament brackets, unlocks, credits, parts shop, repairs, pit droids, vehicle stats and persistent profiles | PC `swrRace.c` contains save/profile, upgrade/stat, parts-health and menu declarations/implementations; PC source map records these surfaces | Exact unlock rules, save compatibility, progression transitions and GC/Wii behavior remain unknown. Do not reduce the game to a single race loop. | P1 |
| Course catalogue and loading | Course identity, metadata, world setup, model/spline loading, scene registration, triggers, weather and HUD setup | PC loader/model/object modules; PC-first plan and format references include `swe1r-assets`, `swe1r-tools`, `blender-swe1r`; Boonta has a synthetic track catalogue and generated demo course | Native GC/Wii course format, loading order, memory budgets, compression and real asset relationships are not confirmed. PC `swrLoader_DecompressLZSS` is a source gap. | P0 |
| Track graph, spline and progress | Main/alternate routes, branch choices, joins, cursor, tangent/up frame, route projection, progress, checkpoints, lap crossing and respawn | PC `swrSpline.c` contains loading/interpolation/cursor/seek code; PC race progress has a cursor-normalized design. Existing Boonta route-graph contract and synthetic fixtures are in the repository history; PR #274 remains a separate candidate, not an instruction to duplicate it. | PC `swrSpline_ProjectPointStub` and `swrSpline_CollectNearbyPoints` remain HANG stubs; `swrRace_AdvanceSplineCursor`, `swrRace_UpdateSplineBinding` and `swrRace_ComputeTrackOffset` remain key gaps in the PC reconstruction. No PC finding proves GC/Wii layout or behavior. | P0 |
| Pod control and handling | Input → throttle/brake → steering/turn smoothing → traction/drift → speed integration → boost/heat → vertical motion/airborne state | PC `swrRace.c` exposes `swrRace_UpdateSpeed`, `ApplyBoost`, `UpdateHeat`, `ApplyTraction`, `IntegrateMotion`, `UpdateTurn`, `Tilt`; current Boonta has clean-room physics helpers and deterministic tests | Exact update order, units, dt/frame-rate dependence, control curves, upgrades and per-pod differences need a full trace. PC behavior remains a reference hypothesis for GC/Wii. | P0 |
| Ground contact, collision and damage | Surface alignment, track mesh lookup, gravity, barriers, object collision, damage, repair, hazards and respawn | PC race code exposes raycast, ground-contact, gravity, surface-tag, collision and damage functions; the PC spline/mesh lookup dossier gives partial call-path evidence | Need complete collision query order, mesh flags, coordinate transforms, contact response and respawn selection. Several object/scene callbacks remain unimplemented in the PC reconstruction. | P0 |
| Rival AI and race ordering | Route choice, target speed, steering, overtaking, rubber-banding, collision recovery, ranking and finish order | PC source has `swrRace_AI`, normal/simplified AI flags and route-progress consumers; PC AI/catch-up reference exists in this repo | AI state/update order and difficulty modifiers need function-level tracing. The current deterministic placeholder rivals are not evidence of original AI fidelity. | P1 |
| Camera and transforms | Chase/cockpit camera, look-ahead, banking, roll, collision response, viewport and split-screen | PC `rdCamera.c`, `rdMatrix.c`, camera research notes; camera implementation has no HANG markers in the inspected file but includes release-build crash TODOs | Need camera target/lag/look-ahead formulas and link to pod orientation; PC camera math is not a GC/Wii implementation. | P1 |
| World objects, scene graph and animation | Track props, triggers, animated objects, pod parts, particle/effect attachments, scene lifecycle | PC `swrObj.c`, `swrModel.c`, `rdThing.c`, `rdPuppet.c`; object and model code contain many HANG placeholders | A large number of PC object manager/scene callbacks and model-load/animation paths remain unfinished in the public reconstruction. Need classify which are essential to race flow vs front-end/render-only. | P1 |
| Renderer, materials, lighting and effects | Model conversion, visibility/culling, transforms, materials, textures, fog, lighting, sky/weather, particles and effects | PC `swrRender.c`, `swrModel.c`, `rdMaterial.c`, `rdLight.c`; Boonta has a native GX renderer for the current procedural scene | PC render code is incomplete and Windows-specific; model conversion/scene submission and material helpers include HANG stubs. Need target-specific GX architecture, resource limits and actual content pipeline. | P1 |
| HUD, minimap and menus | Speed/engine/heat, lap/position, flags, route guidance, distance, minimap, pause/options, shop/results UI | PC `swrPlayerHUD.h`, `swrText.c`, `swrRace.c`; Boonta has a basic HUD for its prototype | HUD data contracts and timing are not fully mapped. PC text draw entry points remain HANG stubs; PC occlusion notes are resolution-specific and must not be copied as target facts. | P1 |
| Audio, music and announcer | Sound event registration, positional audio, engine/pod sounds, collisions, music state and transitions | PC `swrSound.c` includes WAVE/source/streaming logic; latest upstream also added a separate Windows replacement-hook sound delta | PC `swrSound_Startup`, `swrSound_PlaySpatial` and `swrSound_SelectPlanetIntroMusic` remain HANG stubs in the inspected source. No GC/Wii audio event map or cleared replacement assets are established. | P2 |
| Weather and track presentation | Per-track weather state, particle velocity/cap/stretch, fog, track ambience and visual transitions | PC HUD setup calls weather configuration; `swrWeather.c` declares setters | All three inspected weather setters remain HANG stubs. Need distinguish actual weather gameplay effects from render-only effects and establish GX cost. | P2 |
| Input, controller configuration and force feedback | Action mapping, analog calibration, menu navigation, rumble/force feedback, pause and multi-controller routing | PC `swrControl.c` and platform control modules; Boonta has native input scaffolding and separate Wii Classic candidate PR #269 | All 11 HANG markers in inspected PC `src/Main/swrControl.c` correspond to mapping/input/force-feedback functions. PC DirectInput is not GameCube/Wii WPAD. Physical controller acceptance remains a separate human test. | P0 |
| Multiplayer | Local player slots, split-screen, session state, networking/messages if shipped in target scope | PC headers and modules expose multiplayer/player status and DSS networking; HUD has multi-viewport code | Confirm the exact modes in scope per target/version before implementation. PC DSS networking stubs are not proof of a shipped GC/Wii multiplayer feature. | P3 / verify scope |
| Build, diagnostics and tools | Reproducible target build, synthetic fixtures, profiling, asset validation and CI provenance | Boonta has host tests, native DOL/ELF validation and CI workflows; decomp.anything is an audited local RE workbench candidate, not a game source | Keep tooling subordinate to a concrete artifact/question. No claim of a complete game from build success, headless Dolphin smoke or source-marker counts. | Continuous |

## Pinned SW_RACER_RE audit: marker counts and actionable gaps

Upstream revision: [`258f67aa858ba2e281ce8a6791e49c554b85fae0`](https://github.com/tim-tim707/SW_RACER_RE/tree/258f67aa858ba2e281ce8a6791e49c554b85fae0), 2026-10-25. The exact inspected source blob SHAs and raw `HANG(` occurrence counts are:

| File | Blob SHA | HANG occurrences | Interpretation |
|---|---|---:|---|
| `src/Swr/swrRace.c` | `c623f7fddb7a9bebb3dbe9919e0f24e49d7842d3` | 31 | Menu/debug and race-related reconstruction gaps; inspect each function, do not count as missing retail features. |
| `src/Swr/swrSpline.c` | `9b11ef9db1258c053e584a69ec78621a97bd823e` | 2 | Point projection stub and nearby-point collection stub. |
| `src/Swr/swrObj.c` | `f3d0056b624911e7715a4217cead3890a2b3ba84` | 58 | Object/scene/menu lifecycle gaps; large cluster requiring function-level classification. |
| `src/Swr/swrModel.c` | `63a97f70cbbf67a37f5aafd9eaa337dbdf0b023d` | 16 | Includes genuine invalid-type guards as well as TODO stubs; not all are missing implementations. |
| `src/Swr/swrLoader.c` | `57382032b4c6a4dcf41321174a133d1e59df2547` | 1 | LZSS decompressor stub. |
| `src/Swr/swrAssetBuffer.c` | `97bbb2ebce9a6989843b4d444c20f7724a6c820e` | 0 | No HANG marker in this inspected file. |
| `src/Swr/swrRender.c` | `5f7021f031051e4ff9abf7afb055689c195f51c2` | 15 | Mesh conversion, scene submission, transforms/culling and fog-related reconstruction gaps. |
| `src/Swr/swrDisplay.c` | `7b98deb3ee5f988498ad7e774980f2fc82ce7c9f` | 4 | Display startup/shutdown/settings gaps. |
| `src/Swr/swrEvent.c` | `71fd4a002eb3eec802a0220409632a510a2c22ba` | 1 | Event broadcast gap. |
| `src/Swr/swrText.c` | `5da827021099a597b577fdcc7f866e20fa4379d5` | 2 | Two text draw entry points. |
| `src/Swr/swrSound.c` | `12768e91089f7356776f050c9d0e589a5709b784` | 3 | Sound startup, spatial playback and intro-music selection. |
| `src/Swr/swrWeather.c` | `120d17d75179d835fc6904aee43122e87bde11d8` | 3 | Velocity, particle cap and stretch-factor setters. |
| `src/Main/swrControl.c` | `a07245861af604583ade51165dfde1325973fc0a` | 11 | Mapping UI, input processing, mapping changes and force feedback. |
| `src/Engine/rdCamera.c` | `e6ebba37070a57bf54d5620818de52683781d84a` | 0 | No HANG marker; two release-build crash TODOs remain. |
| `src/Engine/rdPuppet.c` | `3b9fa1b56058ae7e731d657d81e7cd14da06c9be` | 1 | Joint-matrix build stub. |
| `src/Engine/rdMaterial.c` | `1c912a1f0387459f4bb44fbdae2e4540872341fb` | 8 | Material load/entry, texture channel conversions and mesh material application. |

The 16 listed files contain **156 raw HANG marker occurrences**. This is a scoped sample only; it is not a repository-wide count, and a raw marker count is not a measure of game completion. The highest-value game-facing gaps are not necessarily the largest numerical clusters: route progression/binding, track loading/decompression, input, model/scene submission, race state/results and audio startup deserve semantic tracing before any priority is assigned by count.

### Highest-value gap clusters

1. **Route progression and terrain binding:** resolve the PC cursor advance/bind/track-offset functions and the two spline helper stubs. This is already the active PC-specific subtask in RE-002/#279; do not duplicate it in RE-001 or transfer its conclusions to GC/Wii.
2. **Race manager and results lifecycle:** establish the complete state transition from course selection through grid, laps, finish, results and progression. HANG markers in the PC race/object modules need caller-based triage.
3. **Track and asset bring-up:** trace course selection → loader block open/decompression → model/spline parse → scene/trigger registration → HUD/weather setup. The LZSS stub and model load/scene stubs make this a high-value dependency chain.
4. **Native controls:** trace the action model and physical controller mapping independently for GC/Wii. PC DirectInput/force feedback is a reference for action semantics, not a target implementation.
5. **World and renderer path:** classify the `swrObj.c` and `swrRender.c` gaps by whether they are race-critical, front-end-only, editor/debug-only or replacement-renderer-specific. Do not attempt to rebuild the entire PC engine as a prerequisite for a clean-room game.
6. **Progression/persistence:** map save/profile/upgrade/unlock state only after the race result lifecycle is coherent.

## Boonta implementation boundary

The current Boonta code is a clean-room native GameCube/Wii scaffold with a procedural course, GX rendering, input/physics/race-state helpers and automated checks. It is useful infrastructure, not the final game. Do not equate its current feature list with the full system inventory above.

- Keep the native build, renderer, host test harness, provenance guardrails and route-graph research as reusable infrastructure.
- Keep the current single procedural oval as a test fixture; it is not a faithful original track or a complete branch-capable content catalogue.
- Keep PR #274 as an existing candidate only. Do not start a parallel route-runtime branch or merge it just because tests pass.
- Keep PR #269's physical Wii Classic acceptance separate; do not mistake compile/input-mock success for actual hardware support.
- Keep Step 102 and all unclear-origin assets on HOLD. The public system matrix contains no extracted coordinates, ROM data, commercial assets or third-party implementation code.

## Recommended next reverse-engineering procedure

**Do not write another gameplay subsystem yet.** The next best task is a single, bounded *race lifecycle call-path trace* in the best available pinned reference:

1. On the PC evidence track, start at the course-selection result and race initialization entry points in the pinned SW_RACER_RE snapshot. Trace callers/callees and state writes through grid/countdown, active race, lap/finish detection, results-panel creation, progression/save update and return-to-menu. Mark every missing edge as UNKNOWN; do not fill it from function names.
2. Cross-check the source trace against the already-recorded independent Steam-PC snapshot only where function semantics and executable-build identity can be matched. Keep both build identities visible; do not silently merge their addresses or types.
3. Use the local N64/console research only as separate corroboration where an exact target build and reproducible observation exist. No PC-only result becomes a GC/Wii fact.
4. Produce one state diagram and one compact evidence ledger: function/address, caller/callee, state fields read/written, source revision, evidence label, confidence, and unresolved transition.
5. Only after this trace is coherent, select the next subsystem with the fewest critical unknowns and strongest target-specific evidence for a clean-room implementation.

**RE-001 target-specific blocker:** the public PC repository cannot answer native GameCube/Wii internals. No original GC/Wii source is established by this audit, and the Step 102 archive remains provenance-held. If the race lifecycle trace is later handed to the native implementation queue, each behavior must be validated against a lawful local target build or kept explicitly as a hypothesis.

## Bounded race-lifecycle trace — pinned Windows-PC evidence

**Snapshot:** [SW_RACER_RE `258f67aa858ba2e281ce8a6791e49c554b85fae0`](https://github.com/tim-tim707/SW_RACER_RE/tree/258f67aa858ba2e281ce8a6791e49c554b85fae0), 2026-10-25.  
**Evidence class:** CONFIRMED-IN-CODE for this Windows-PC reconstruction snapshot only. Not CONFIRMED-IN-RUN and not GameCube/Wii evidence. No external project was built or executed.

### What the source establishes

1. **Per-racer lap/finish accounting — `swrObjJdge_F2` (0x0045EA30).** While the judge low-nibble state is 1, it provisionally sets state 2, walks the score array, and calls `swrRace_UpdateRaceProgress`. A detected line crossing closes the previous lap using the pre-crossing portion of the frame, increments `results_P1_Lap`, then charges the remainder of the raw frame delta to the next lap. At `num_laps`, the score's finished bit (bit 1 / value 2) is set, the multiplayer `fini` event is sent, and the pod's local/boost flags are cleared while finished/AI flags are set. [Source: `swrObj.c`, F2 and continuation](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L918-L1055) · [Score fields](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types.h#L1158-L1194)

2. **Local-player completion gate and opponent finalization.** During that same F2 pass, an unfinished local score re-arms the judge low nibble to state 1. If no local racer remains active, state 2 survives: the race timer is frozen and each unfinished racer gets a projected total based on its current progress ratio. This is a manager-level "all local racers finished" condition, not necessarily every AI having physically crossed the line. [Source: F2](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L918-L1055)

3. **Standings calculation — `swrObjJdge_UpdateStandings` (0x0045D4A0).** Finished racers use an inverse-finish-time rank value; unfinished racers use lap progress. The function writes each score's finishing position and updates leader/local-player/pacer gaps. [Source: `swrObj.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L407-L590)

4. **Judge state and cleanup paths are only partly understood.** In F0 (0x0045E200), low-nibble state 2 waits on the accept/release input edge and calls `swrObjJdge_Clear(jdge, 'Fini')`. Clear stores the event, sets state 6, starts a 0.5-second timer and frees the Test/Toss/Smok/Trig/Chsr object groups. State 6 later calls `swrObjJdge_TeardownRace(jdge, jdge->event)`. The teardown function is currently a `HANG("TODO")` stub, so the actual cleanup-to-front-end handoff is not recovered. [Clear and teardown](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L350-L365) · [F0 states 2–6](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L770-L900)

5. **The initial race-to-Results handoff remains unresolved.** The earlier reading of Judge F0 states 4/5 as a post-race camera/results sequence was incorrect: the pinned Judge source plus independent IDA notes identify them as pre-race camera-intro stages (state 4 sweep initialization, state 5 sweep/orbit logic) leading to Judge state 0 countdown. The separate visible completion path is state 2 → `Clear(Fini)` → state 6 → `TeardownRace`; the teardown body and runtime receiver remain unresolved. The local label `swrObjJdge_StartPostRaceSequence` at `0x0045DFE0` is misleading for its visible use in the state-5-to-0 countdown transition. The F0 intro camera events are not evidence of the Hang Results handoff. [Judge routine and F0](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L615-L900)

6. **The actual Results menu routine is substantial — `swrRace_ResultsMenu` (0x00439CE0).** On first entry it sanitizes score times, sorts scores by finishing position, calculates local-player best laps, routes unlinked guest profiles to name entry, commits lap/race records and holder details, applies tournament prize/unlock/beat-place progression, and saves the profile. It then draws each standings row with position, racer identity and total time. Accept/cancel selects a return-to-course-selection state or a podium intro when the tournament final is won. [Source: `swrRace.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L324-L585)

### Separate cross-check against the frozen Steam-PC Ghidra snapshot

**Independent reference:** [DeonPoncini/swep1r_decomp at `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef). This is a separate Steam-PC Ghidra-derived snapshot. Its function addresses happen to overlap several SW_RACER_RE entry points, but the two executable/build identities have not been proven identical. Keep the evidence columns and globals separate; this is corroboration, not permission to merge type layouts or infer target-console behavior.

- **Results dispatcher relationship is directly visible in this Steam snapshot:** `FUN_00457620` switches on the hangar/menu state; case 5 first calls `FUN_004575d0` and then `FUN_00439ce0`. The SW_RACER_RE header independently labels `0x00457620` as `swrObjHang_F0`, and `0x00439ce0` as `swrRace_ResultsMenu`. [Steam dispatcher, case 5](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00457620.c#L100-L112)
- **State 5 is explicitly named `POST_RACE_INFO`** by `FUN_00454d40` in this Steam snapshot. The corresponding SW_RACER_RE enum also names value 5 `swrObjHang_STATE_POST_RACE_INFO`. This supports the menu-state-to-Results-panel interpretation on the separate Steam-PC build; it does not establish the preceding race-manager event path. [Steam state label](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00454d40.c#L118-L133) · [SW_RACER_RE enum](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types_enums.h#L375-L392)
- **The Results routine's side transitions are also consistent:** Steam `FUN_00439ce0` calls `FUN_00454d40(param_1, 2)` for guest name entry and `FUN_00454d40(param_1, 0x11)` for the results-intro/pilot-unlock branch, while the state setter prints `POST_RACE_INFO` for value 5. These are separate Steam-PC observations, not a merged cross-version state table. [Steam Results routine](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00439ce0.c#L150-L180) · [Steam intro transition](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00439ce0.c#L260-L275)
- **A possible teardown implementation exists, but it does not close the evidence gap:** Steam `FUN_0045dd80` contains a `Fini`-specific branch and an alternate path that sends `RSet` to `cMan` and the supplied event to `All!`. However, the snapshot's own dependency graph explicitly lists `NOT_INVOKED --> FUN_0045dd80` and `NOT_INVOKED --> FUN_00457620`. The published evidence therefore does not show those functions being reached from a caller in that graph. Treat the function body as a useful candidate/reference for future investigation, not proof of the normal retail race lifecycle. [Steam teardown candidate](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0045dd80.c#L60-L88) · [Steam dependency graph](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/docs/textures.mmd#L42-L54)

**Cross-check result:** the Results-menu destination is now supported by two separate PC source snapshots, with the Steam snapshot explicitly mapping menu state 5 to the Results routine. The race-manager-to-hangar handoff, event reachability, and teardown execution remain unresolved. No PC evidence establishes GameCube/Wii behavior.

### Third-source structural cross-check — independent IDA metadata

**Reference:** [everalert/swe1r-decomp at `8d066b9c12ecb57bd819aaab586fd6bd2dd078a7`](https://github.com/everalert/swe1r-decomp/tree/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7). This is an IDA metadata/source-analysis snapshot for the PC game, not a GameCube/Wii source tree. The labels below are analyst-assigned names, not recovered retail symbols.

- Its function inventory labels `0x0045E200` as `EntityJdgeCallback0x14` (size `0x74C`), `0x0045EA30` as `EntityJdgeCallback0x1C` (size `0x53E`), `0x0045DD80` as `Unk_Jdge_LoadFromRace` (size `0x254`), and `0x00457620` as `EntityHangCallback0x14` (size `0x468`). These addresses/lengths independently align with the Judge/Hangar callback roles already used in the SW_RACER_RE dossier; they do not establish identical PC executable builds. [IDA function table](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt#L1136) · [Judge entries](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt#L1187-L1196) · [IDA names](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/names.txt#L1220)
- The same metadata project documents `Entity_CallAll0x14`: it iterates the entity-manager table, reads a callback pointer at manager offset `0x14`, then invokes that callback for each entity that passes its flag guard. Parallel wrappers exist for offsets `0x18`, `0x1C` and `0x20`. This structurally matches the SW_RACER_RE `swrEventManager` callback layout (`f0` at `0x14`, then `f1/f2/f3` at `0x18/0x1C/0x20`). [IDA callback iterator](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/src/4508B0_Entity_CallAll0x14.c#L3-L27) · [SW_RACER_RE event-manager layout](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types.h#L1084-L1125)
- This is **structural corroboration only**. The checked metadata does not show which precise entity-manager entries hold the Judge/Hangar callbacks in a race, the callback timing relative to `Fini`, or the native console behavior. It does not override the Steam snapshot's `NOT_INVOKED` graph markers for `FUN_00457620` and `FUN_0045DD80`.

### Event-manager dispatch: what the `Swee` edge actually proves

A further pass over the same pinned SW_RACER_RE snapshot and the separate Steam-PC Ghidra snapshot clarifies the dispatcher architecture. It does **not** recover the missing camera-manager implementation.

**SW_RACER_RE event-manager layout and implementation evidence**
- The declared `swrEventManager` record places per-object callbacks at `f0=0x14`, `f1=0x18`, `f2=0x1C`, `f3=0x20`, and the sub-event callback `f4=0x24`; `head`, count and object stride are stored alongside them. This is the PC reconstruction's declared structure, not a native GameCube/Wii layout. [Pinned type declaration](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types.h#L1086-L1098)
- `swrEvent_CallAllF0` and `swrEvent_CallAllF2` independently walk the manager table and each manager's object array, invoking the selected callback slot where present and where the object's `0x1100` flag mask permits. This establishes the general periodic-callback mechanism, but the inspected files do not establish the caller's frame-order relative to other simulation phases. [F0/F2 scheduling code](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrEvent.c#L47-L105)
- `swrEvent_CallF4(event, payload)` searches the manager list for the named event (or the special `All!` broadcast), iterates that manager's objects, invokes its `f4` callback unless object flag `0x100` is set, and stops if a callback returns 2. `swrEvent_DispatchSubEvents` instead selects the manager matching the target object's own event and forwards the sub-event to that object's `f4`. [Sub-event dispatch code](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrEvent.c#L184-L229)
- The event-table declaration in `swrEvent.h` associates the `cMan` manager with `swrObjcMan_F0/F2/F3/F4`, the `Jdge` manager with the Judge callbacks, and `Hang` with the Hangar callbacks. The table is retained under a disabled preprocessor block as documentation in this source snapshot; the individual cMan and Hang callback bodies still include `HANG("TODO")` stubs. Treat the table as a reconstructed mapping, not a live executable trace. [Event table and manager callback mapping](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrEvent.h#L10-L124) · [cMan/Hang stubs](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L179-L267)

**Independent Steam-PC dispatcher cross-check**
- Steam-PC `FUN_004508b0` and `FUN_004509b0` walk the same manager-table structure and call callback slots at `+0x14` and `+0x1C`, respectively, subject to the per-object `0x1100` flag guard. This is consistent with the SW_RACER_RE F0/F2 scheduling model. [Steam F0 scheduler](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004508b0.c) · [Steam F2 scheduler](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004509b0.c)
- Steam-PC `FUN_00450c50` independently shows `CallF4`: it iterates managers matching the requested event (or `All!`), invokes each manager's callback at `+0x24` for eligible objects, and returns early when the callback returns 2. This supports the dispatcher contract, not the missing cMan implementation. [Steam F4 dispatcher](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00450c50.c)
- No recovered cMan `F0/F2/F4` body or caller path in these checked snapshots explains what a `Swee` payload does to camera-manager state. The Steam functions establish generic callback routing only.

**Revised interpretation of the two Swee requests**
- The Judge's pre-race intro path issues `Swee` to `cMan` in two distinct contexts: the state-4-to-5 camera sweep sends payload 1 (start), and the state-5-to-0 countdown transition calls the routine locally labelled `StartPostRaceSequence`, which sends payload 0 (cancel). Both use cMan F4 dispatch; neither is a call to `swrRace_ResultsMenu` or proof of the initial post-race handoff. [Payload-0 sender](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L615-L645) · [Payload-1 sender](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L810-L848)
- The actual Results routine is a separate Hangar-side menu handler selected by Hangar menu state 5 (`POST_RACE_INFO`) in the Steam snapshot. Do not conflate this with Judge low-nibble state 5 in `swrObjJdge_F0`, which is a separate race-manager branch that marks `swrRace_resultsScreenActive` and drives post-race taunt timing. The two state numbers belong to different objects/state machines. [Steam Hangar state-5 dispatcher](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00457620.c#L100-L112) · [Steam menu-state label](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00454d40.c#L118-L133) · [Judge state-5 branch](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L853-L889)
- The Judge F4 `Begn` handler initializes its low nibble to 4, while Judge F0 uses low-nibble state 4 for the camera-sweep-to-results branch. That apparent reuse/overlap is not resolved by the source call graph examined here. It may depend on omitted lifecycle calls or state timing; do not turn the labels into a single asserted sequence. [Begn state write](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L1752-L1792)

**Updated conclusion:** the generic PC event-dispatch mechanism is now independently corroborated across the SW_RACER_RE and Steam-PC snapshots. It explains how `Swee` is routed to cMan's F4 callback slot, but not what that callback does, when the cMan periodic callbacks run relative to the Judge, or how the Hangar state 5 is reached. The race-manager-to-Hangar handoff remains unresolved; no GameCube/Wii fact is established.

### Critical unresolved transitions — do not turn this into a false linear state diagram

- The source labels F0 states 3–5 as finish/camera/results phases, but the `Begn` handler in `swrObjJdge_F4` also initializes the judge low nibble to 4. The exact lifecycle context and all entry conditions for states 3–5 therefore need caller/event-order validation; their labels alone are not enough to prove a single ordered path. [`Begn` handler](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L1752-L1835)
- `swrObjJdge_TeardownRace` is a TODO stub. The object-manager `swrObjcMan_F0/F2/F3/F4` callbacks are also TODO stubs, including the `cMan` dispatcher needed to resolve the `Swee` event. [Object-manager stubs](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L177-L220)
- `swrObjHang_SetMenuState` and `swrObjHang_F0/F2/F3` are TODO stubs. The enum documents `POST_RACE_INFO = 5` and `RESULTS_INTRO = 17`, but this snapshot does not recover the complete front-end dispatcher/call edge that proves precisely when `swrRace_ResultsMenu` is entered. [Hangar stubs](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L245-L275) · [Menu state enum](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types_enums.h#L375-L392) · [SetMenuState stub](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L225-L228)
- `swrObjJdge_F4` handles `Begn/Load/RSet/Join/Mstr/Paws/Slep/Wake/JAsn`; `Fini` is documented under the `All!` event group, not as a Jdge F4 case. The full event-manager dispatch sequence remains only partially reconstructed. [Event mapping and dispatcher layout](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types.h#L1084-L1125) · [Jdge F4](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L1752-L1905)

### Resulting next procedure for native GameCube/Wii RE-001

The PC trace now gives us a concrete list of semantic checkpoints, not native offsets or state values to copy. For a lawful, owner-held GameCube/Wii build, the next target-specific experiment is:

1. Record disc/game ID, region/revision and SHA-1 of the locally held DOL; keep the binary and all extracted output local.
2. Use the already-audited GC/Wii DOL/REL toolchain on that exact build; identify the race-manager object callbacks and score/standings storage by cross-reference, not by PC address.
3. In Dolphin, capture one ordinary three-lap race continuously from the final lap through the first Results frame. Correlate visible transitions with the target-build state writes/callbacks and save/profile mutations.
4. Produce a separate GC/Wii state/event ledger. Until those observations exist, every PC state number, structure offset, event tag and result transition remains PC-only UNKNOWN for the native target.

This is a research handoff only: no third-party implementation code, ROM/DOL, commercial assets or extracted data is copied into Boonta. The AGPL-3.0 SW_RACER_RE snapshot remains a read-only reference; its README explicitly describes selected analysis/reimplementation rather than a full matching decompilation.

## Existing dossier links and non-duplication

- [PC-first research plan](../PC_FIRST_RESEARCH_PLAN.md)
- [SW_RACER_RE study plan](../SW_RACER_RE_STUDY_PLAN.md)
- [SW_RACER_RE behavior matrix](../SW_RACER_RE_BEHAVIOR_MATRIX.md)
- [PC source findings](../PC_SOURCE_FINDINGS.md)
- [RE-001 route/spline dossier](RE-001-route-spline-progress.md)
- [decomp.anything tool audit](RE-001-decomp-anything-tool-audit.md)
- [RE-001 external N64 reference audit](RE-001-external-reference-racer-audit-2026-10-29.md)
- [RE-002 PC/N64/Dreamcast comparative matrix](RE-002-platform-source-matrix.md) — separate read-only queue; do not duplicate its active PC cursor subtask.

## Reproduction and provenance

This audit inspected public GitHub source files at the exact pinned revision and recorded their blob SHAs. No external repository was cloned or built here; no ROM, executable, disc image, BIOS, extracted commercial asset, or game-derived payload was read or committed. The upstream license was inspected and is AGPL-3.0. Recheck the upstream default branch before starting a new investigation; do not silently move this snapshot's pin.


## Triage of the previously suggested AeroMESH reference

[AeroMESH](https://github.com/tex1ure/AeroMESH) was checked at its public `main` branch on 2026-11-04. Its README describes a Rust peer-to-peer pipeline-parallel LLM/diffusion inference engine for distributing model execution across consumer GPUs; the repository declares Apache-2.0. It is **not** a game reverse-engineering tool, binary decompiler, asset parser, mesh-format workbench or racing-game engine. It therefore does not solve a Boonta RE-001/RE-002 problem and should not be integrated into the game repository. Its only possible relevance is as a separate AI-infrastructure project, but the current GitHub Actions/OpenCode fallback already addresses the bounded agent-execution need without adding a distributed GPU cluster. This is an explicit non-adoption decision, not a negative judgment about AeroMESH itself.


## 2026-11-04 — cMan instance registry and the recovered F3 callback (Steam-PC cross-check)

A targeted follow-up to the unresolved post-race manager edge establishes more about the camera-manager pool, but still does not recover the receiver for the post-race `Swee` message.

**Pinned reference:** DeonPoncini/swep1r_decomp at `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef` (Steam-PC Ghidra export). This is a separate PC snapshot; the exact executable identity relative to SW_RACER_RE remains unresolved.

### Manager pool and callback dispatch

- In `FUN_00448f40`, the branch guarded by `DAT_004c17e0 == -1` configures six `cMan` objects, one `Jdge`, and one `Hang`. It does this through `FUN_00447300`.
- `FUN_00447300` reserves/initializes the requested object-manager pool and immediately dispatches a `Load` message to that manager class. `FUN_00449040` calls this setup sequence as part of allocating the large manager storage block.
- `FUN_004490a0` iterates the indexed `cMan` instances and associates each with a camera slot beginning at index 7, using the instance's transform/focus-related fields. This supports the interpretation of `cMan` as a set of per-camera manager objects, not one singleton.
- `FUN_00450c50` dispatches F4 by manager type (or `All!`). It obtains the manager F4 callback from record offset `+0x24`, iterates the manager's object array, skips objects with the `0x100` flag, and stops the dispatch when a callback returns 2. Thus a `Swee` event sent to `cMan` is routed through the F4 callback for eligible cMan instances; it is not a direct Results-menu call.

### A newly located cMan F3 body

The Steam export includes `FUN_004542e0` in `src/_text15.c` (lines 2685–2711), at the same numeric address assigned to `swrObjcMan_F3` in SW_RACER_RE. The body:
- calls `FUN_00453e00` first, which performs a substantial camera update using the cMan state/mode;
- advances a bounded oscillation using fields at `+0x39C`, `+0x3A0`, and `+0x3A4`;
- applies the resulting offset to camera-related values at `+0x140` and `+0x58`, then invokes a small update helper;
- conditionally emits terrain/region status text through `FUN_00454060`.

This is a useful PC-only F3 implementation lead, not the missing `Swee` F4 handler. The independent IDA notes below resolve this field interpretation for that separate snapshot: the vector at `+0x38C` is followed by an animation-time scalar at `+0x398`, then camera-shake offset/speed/max-offset scalars at `+0x39C`, `+0x3A0`, and `+0x3A4`. These are consistent with the three fields read by the Steam F3 body; keep the typed/vector and scalar fields distinct.

The checked Steam source search found `FUN_004542e0` but did not find same-address bodies for cMan F0 (`0x00451CD0)), F2 (`0x00451D40)) or F4 (`0x004543F0)). This is a bounded negative search result, not proof those routines do not exist in another executable or source snapshot.

### Post-race messages and teardown candidate

- Steam `FUN_0045dfe0`, at the same numeric address as the locally labelled SW_RACER_RE routine `swrObjJdge_StartPostRaceSequence`, sends `Swee(false)` to cMan F4. In the inspected reconstruction it is called by Judge F0 state-5 logic as part of the transition back to state 0 countdown; its visible body clears the Judge low nibble and resets the timer. Despite its local function name, this is not evidence of a post-race Hang/Results transition. The cMan receiver's behavior remains unknown.
- The SW_RACER_RE Judge F0 state-4-to-5 pre-race intro branch also sends `Swee` with payload 1 (start the camera sweep). A search of this pinned Steam export found the payload-0 sender at `FUN_0045dfe0`, but no second `Swee` sender. Whether that reflects an executable/build difference or an incomplete Steam source/xref export remains UNKNOWN.
- Steam `FUN_0045dd80` is a candidate teardown routine. It cleans up race object groups; on its special branch when `(DAT_0050c9f8 & 2) != 0` and the event is `Fini`, it calls `FUN_00466bd0`, sets Judge state 3 and returns without broadcasting `All!`. On the alternate branch it sleeps the Judge, sends `RSet` to cMan, and broadcasts the supplied event (substituting `Abrt` when `DAT_0050ca2c` is set). The dependency graph labels this candidate `NOT_INVOKED`, so neither branch proves the normal race-to-Hangar handoff.
- The one-object `Hang` manager is created in the same setup branch, but neither the cMan F4 result nor the Hangar callback body is recovered by this trace. The Results panel's concrete entry edge is still not proven.

### Evidence links

- [Steam manager-count setup `FUN_00448f40`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00448f40.c)
- [Steam pool initialization `FUN_00447300`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00447300.c)
- [Steam cMan camera-slot association `FUN_004490a0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004490a0.c)
- [Steam F4 event dispatcher `FUN_00450c50`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00450c50.c)
- [Steam cMan F3 body `FUN_004542e0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text15.c#L2685-L2711)
- [Steam Judge `Swee(false)` sender `FUN_0045dfe0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0045dfe0.c)
- [Steam teardown candidate `FUN_0045dd80`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0045dd80.c)
- [Steam dependency graph and NOT_INVOKED annotations](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/docs/textures.mmd#L42-L54)

**Conclusion:** the manager pool, F4 routing contract, one camera-manager F3 body, and the Boolean meaning of `Swee` are now supported. The F4 callback's full body is still not reconstructed, and the way/when the race manager causes the Hangar/Results object state to change remains unresolved. Keep those narrower gaps explicit; this remains Windows-PC evidence only and does not establish native GameCube/Wii behavior.


## 2026-11-04 — Independent IDA confirmation of cMan F4 and Swee semantics

A third, independent PC metadata/notes snapshot provides the missing event interpretation that the Steam decompilation alone did not expose.

**Pinned source:** [everalert/swe1r-decomp](https://github.com/everalert/swe1r-decomp) at `8d066b9c12ecb57bd819aaab586fd6bd2dd078a7`. This repository contains a 15 MB IDA database and analyst notes; the database was **not** downloaded or opened. Only the public text notes and function/name metadata were inspected. The exact executable hash/release identity is not established.

### F4 callback and Swee payload

- The IDA name table identifies `EntityCManCallback0x24_4543F0` at `0x004543F0`; its function inventory records a 0x529-byte function extent and 0x10-byte stack frame. This independently corroborates that cMan has a concrete F4 callback at the same address as the SW_RACER_RE TODO stub.
- The IDA `Entity_cMan.txt` event notes describe `Swee` as a two-field message: `+0x00 = 'Swee'`; `+0x04 = BOOL`, where true starts the camera sweep and false cancels it.
- The two SW_RACER_RE Judge senders have a consistent interpretation: the state-5-to-0 countdown transition calls the locally named `StartPostRaceSequence` with payload 0 (cancel), while the state-4-to-5 pre-race intro sweep sends payload 1 (start). The Steam Ghidra snapshot only exposed the payload-0 sender in the source search performed here; the independent IDA event note supplies the Boolean meaning, but does not establish why that second sender was absent from the Steam text export.
- The IDA note also says more than one cMan entity is generated and points to an entity array, independently supporting a manager pool. The exact six-instance count and camera-slot association are directly visible in the separate Steam `FUN_00448f40` / `FUN_004490a0` evidence above.

**Important limit:** the IDA `functions.txt` and `names.txt` prove a named function and its extent, and `Entity_cMan.txt` records the analyst's message interpretation. The callback's full decompiled body was not available in the inspected public text files; no claim is made that its internal control flow was recovered from source. The cMan F4 implementation is therefore now **semantically described by independent notes**, but not body-reconstructed here.

### Camera-shake field cross-check

The same IDA note labels:
- `+0x398`: camera animation time / frame-time scalar;
- `+0x39C`: camera-shake offset;
- `+0x3A0`: camera-shake speed;
- `+0x3A4`: camera-shake maximum offset.

That independently agrees with the Steam F3 body at `0x004542E0`, which advances the offset by speed, reflects it at the maximum, and applies it to camera-related values. The SW_RACER_RE `rdVector3 camShake` at `+0x38C` is a distinct preceding vector; it should not be conflated with the three shake scalars.

### Separate sweep-mode evidence — do not conflate the cameras

The Steam snapshot also reconstructs `FUN_00451EF0` as a timed, track-indexed camera sweep routine. It reads a per-track record with 0x6C-byte stride, interpolates through three timed stages, writes camera and focus transforms, and calls `FUN_00451D60` to change mode when the animation completes. The IDA notes identify mode 7 as the pre-race camera sweep and mode 6 as a spline camera similar to post-race autopilot. This is useful evidence that the camera manager contains several sweep/spline modes, but it does **not** prove that the Judge-to-Results `Swee` request runs the pre-race mode-7 routine; the IDA note itself warns that post-race camera logic may differ.

### Sources

- [IDA cMan event/entity notes](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/notes/Entity_cMan.txt)
- [IDA function extent for EntityCManCallback0x24_4543F0](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt)
- [IDA function names](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/names.txt)
- [Steam camera sweep body FUN_00451ef0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00451ef0.c)
- [Steam sweep completion helper FUN_004525d0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text15.c#L1756-L1764)
- [Steam F3 body FUN_004542e0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text15.c#L2685-L2711)

**Updated conclusion:** the meaning of the `Swee` Boolean is now independently supported (0 = cancel, 1 = start), and cMan F4 is identified by its exact callback address/extent. Its complete body and the subsequent Hangar/Results handoff remain unverified. These remain Windows-PC findings only; no native GameCube/Wii state or behavior is inferred.


## 2026-11-04 — Hang F0 / Results-menu destination recovered, handoff still unproven

The independent IDA notes and Steam-PC Ghidra source allow a narrower statement about the Hangar-side destination.

**Pinned references**
- everalert/swe1r-decomp IDA notes at `8d066b9c12ecb57bd819aaab586fd6bd2dd078a7`: [Entity_Jdge.txt](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/notes/Entity_Jdge.txt), [Entity_Hang.txt](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/notes/Entity_Hang.txt), [EntitySystem.txt](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/notes/EntitySystem.txt), and [functions.txt](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt).
- Steam-PC source at `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`: [Hang F0 callback FUN_00457620](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00457620.c) and [Results routine FUN_00439ce0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00439ce0.c).

### What is now directly supported

1. **Hang menu screen 5 is Results / POST_RACE_INFO.** The IDA `Entity_Hang.txt` note maps menu screen enum value 5 to race results and calls it `POST_RACE_INFO` in game code. This is a Hang object menu-screen field, not Judge F0's low-nibble state 5.
2. **A Steam F0 callback body exists at the Hang callback address.** IDA identifies `EntityHangCallback0x14_457620` at `0x00457620` with a 0x468-byte function extent. The Steam decompilation provides the body at the same address as `FUN_00457620`.
3. **The callback processes menu screen 5 by calling the Results routine.** In `FUN_00457620`, the code first checks Hang's active flag bit 0. If active, its menu-screen switch has case 5, which calls `FUN_004575d0` and then `FUN_00439ce0` (the Results/menu routine). The latter is therefore the concrete results destination *conditional on this Hang F0 callback running with menu screen 5*.
4. **The common entity system can call this callback through the F0 slot.** The independent `EntitySystem.txt` describes the per-frame callback at manager/entity-definition offset `+0x14` as F0 and explains that F0–F3 are dispatched in ordered periodic passes. This is consistent with the Steam generic scheduler `FUN_004508b0` and manager layout already recorded above.

### What remains unproven

- The Steam dependency graph explicitly labels `NOT_INVOKED --> FUN_00457620`. This warns that the checked static call graph does not show a direct caller. The callback-table architecture makes indirect scheduler invocation possible, but it does not establish that the Hang entity was active or received the F0 tick during the post-race transition.
- No inspected source or note yet establishes **who writes Hang menu screen 5**, who sets Hang's active flag bit 0 after race completion, or exactly when that occurs relative to the Judge state-4/5 camera sequence.
- The Steam candidate teardown `FUN_0045dd80` is also marked `NOT_INVOKED`; its body must not be treated as the proven path that activates Hang or transitions to Results.
- The SW_RACER_RE Hang F0/F2/F3/F4 handlers remain `HANG("TODO")` stubs. Do not promote Steam/IDA callback addresses or object offsets into native GameCube/Wii assumptions.

**Updated lifecycle statement:** the Results routine is now mapped to a concrete Hang F0 callback branch: *active Hang + menu screen 5 → Results routine*. The unresolved edge is the preceding writer/activation path that makes this condition true after the race. This is stronger than merely finding a Results function, but it is not yet a complete race-manager-to-Hangar runtime trace.


## 2026-11-04 — Results → pilot-unlock scene → Results return path

A further source trace found a concrete way the Hang menu can return to screen 5 after a pilot-unlock scene. This is a **Results continuation path**, not proof of the initial Judge-to-Results handoff.

**Pinned Steam-PC source:** `DeonPoncini/swep1r_decomp` revision `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`; independent IDA menu labels are from `everalert/swe1r-decomp` revision `8d066b9c12ecb57bd819aaab586fd6bd2dd078a7`.

### Exact continuation chain

1. **The Results routine selects the pilot-unlock scene.** In `FUN_00439ce0` (Hang menu screen 5 / Results), when a newly eligible pilot has not already been unlocked, the routine sets the unlock bit, saves the profile, and calls `FUN_00454d40(param_1, 0x11)` (Steam source lines 263–270). Thus it transitions the Hang menu from Results screen 5 to screen 17.
2. **Hang F0 processes screen 17.** `FUN_00457620` has case `0x11` and calls `FUN_0043d4e0` (lines 145–150). IDA `Entity_Hang.txt` labels Hang menu 17 as the new-racer unlock scene.
3. **The scene completion callback schedules screen 5.** `FUN_0043d4e0` waits on the scene transition/timer and checks the unlock-scene flags `DAT_004d6b48` / `DAT_004d6b44`. When either indicates the animation is ready to finish, it sets `DAT_0050c944 = -1` and the pending Hang screen `DAT_004bfedc = 5` (lines 40–50).
4. **Hang F0 applies the pending transition.** Later in `FUN_00457620`, while `DAT_0050c944 == -1`, it calls `FUN_0043e330` (lines 164–167). Once its transition timer/conditions complete, `FUN_0043e330` calls `FUN_00454d40(param_1, DAT_004bfedc)` (lines 33–42); with the value scheduled above, this sets Hang menu screen 5, which IDA labels `POST_RACE_INFO`.

This proves the code-level **Results screen 5 → new-pilot scene 17 → scheduled Results screen 5** continuation in the inspected PC source. It also gives one actual writer of menu screen 5: the pending-screen global `DAT_004bfedc` is set to 5 by the unlock-scene completion callback, then applied by the common menu transition helper.

### What this does not prove

- This is the post-Results pilot-unlock continuation only. It does **not** explain how the initial end-of-race camera sequence enters Hang screen 5 when no pilot unlock occurs.
- It does not establish that the Judge state-4/5 `Swee` camera sweep directly activates Hang or writes the pending screen 5.
- The separate Steam teardown candidate `FUN_0045dd80` remains annotated `NOT_INVOKED`; do not insert it into this chain.
- All addresses, menu fields and event semantics remain Windows-PC evidence. No native GameCube/Wii parity is implied.

**Sources:** [Results routine and unlock transition](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00439ce0.c), [Hang F0 screen-17 callback and transition dispatch](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00457620.c), [unlock-scene completion / pending screen 5](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0043d4e0.c), [common menu transition helper](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0043e330.c), [IDA Hang menu-state labels](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/notes/Entity_Hang.txt).

## 2026-11-04 — Steam-PC cMan F4 event dispatch and the Swee route

This pass follows the *dispatch layer* between the Judge's post-race camera message and the cMan camera-manager pool. It closes the generic event-routing question, but **does not recover the cMan F4 callback body or prove a Hangar/Results transition**.

**Pinned sources**
- Steam-PC Ghidra export: `DeonPoncini/swep1r_decomp` revision `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`: [F4 message dispatcher `FUN_00450c50`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00450c50.c), [Judge `Swee(false)` sender `FUN_0045dfe0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0045dfe0.c), [manager-pool setup `FUN_00448f40`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00448f40.c), [camera-slot assignment `FUN_004490a0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004490a0.c), [pool allocation helper `FUN_00447300`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00447300.c), and [teardown candidate `FUN_0045dd80`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0045dd80.c).
- Independent IDA metadata: `everalert/swe1r-decomp` revision `8d066b9c12ecb57bd819aaab586fd6bd2dd078a7`: [cMan event notes](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/notes/Entity_cMan.txt), [function names](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/names.txt), and [function inventory](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt).

### Dispatch contract directly visible in the Steam export

1. **The cMan message entry point is an F4 dispatch.** `FUN_00450c50(type, payload)` walks the entity-manager registry. For a matching type (or the `All!` wildcard), it reads the manager's callback pointer at record offset `+0x24` (`piVar1[9]`), then iterates that manager's object array. Objects carrying flag `0x100` are skipped. Each remaining object is passed to that callback with the payload; a callback return value of `2` stops the dispatch. A named type dispatch returns after that matching manager pool, while `All!` continues through the registry.
2. **The Judge routine at `0x0045DFE0` sends Swee(false) to the cMan pool.** `FUN_0045dfe0` builds the two-word payload `{ 'Swee', 0 }` and calls `FUN_00450c50('cMan', payload)`. The independent IDA note describes the `Swee` Boolean as `on = start camera sweep; off = cancel camera sweep`. In SW_RACER_RE the matching local label is `swrObjJdge_StartPostRaceSequence`, but its visible state-5-to-0 use belongs to the pre-race intro-to-countdown path; the label is not evidence of post-race Results activation.
3. **The pool has six cMan objects in the inspected Steam setup path.** `FUN_00448f40` calls `FUN_00447300('cMan', 6)`, then creates one `Jdge` and one `Hang` entry. `FUN_004490a0` associates the six cMan objects with camera slots beginning at slot 7 (slots 7–12 in that loop). `FUN_00447300` allocates/initializes the typed pool and dispatches its `Load` event; this inspected helper does not itself reveal where the manager-level callback pointer at `+0x24` is initialized.
4. **The independent IDA identity is consistent with that slot.** IDA names `EntityCManCallback0x24_4543F0` at `0x004543F0` and lists a `0x529`-byte function extent. This corroborates the existence and identity of a cMan F4 callback; it does not supply the body in the public text sources inspected in this pass.

### What the dispatch trace does not establish

- No inspected Steam source body for `0x004543F0` was recovered, and the callback-pointer initialization path at manager record `+0x24` remains untraced here. Do not infer the handler's internal state transitions from the generic dispatcher.
- The IDA `Entity_cMan.txt` event note supports the Boolean meaning of `Swee`; it does not say that this event directly activates Hang or selects Hang menu screen 5.
- The existing source evidence still only proves the separate Hang continuation *when Hang is active and already on screen 5*, and the Results → pilot-unlock screen 17 → Results screen 5 return path. It does not prove the initial Judge-to-Hangar transition.
- Steam `FUN_0045dd80` has a conditional `Fini` branch that returns via `FUN_00466bd0` without `All!`; only its alternate branch sends `RSet` and broadcasts the supplied event (or `Abrt`). Its dependency graph labels the candidate `NOT_INVOKED`, so it is not promoted into the normal race-finish path.
- The second Judge-side `Swee` sender with payload 1 is present in the SW_RACER_RE reconstruction but was not found in this pinned Steam text export. Keep this as a source-snapshot discrepancy, not proof that the sender is absent from the Steam executable.

**Updated lifecycle conclusion:** the route for the pre-race Judge state-5-to-0 `Swee(false)` request is explicit: *Judge countdown-transition routine → cMan F4 event dispatcher → typed cMan pool → eligible cMan objects → manager F4 callback at +0x24*. IDA independently identifies the expected cMan F4 callback as `0x004543F0`, but its body/dispatch effects remain unrecovered. The separate initial Fini-to-Hangar Results activation remains **UNKNOWN**. All findings here are pinned Windows-PC evidence only; no GameCube/Wii parity is inferred.

### Bounded callback-body availability check (same pinned Steam revision)

A final availability check targeted the exact symbol rather than searching only by address:
- The pinned Steam tree has no `c/FUN_004543f0.c` and no `asm/FUN_004543f0.s` at revision `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef` (both exact content paths return not found).
- The inspected aggregate text exports `src/_text15.c` (blob `673cbacba8fbcda3008c3788cab4501059a11b76`) and `src/_text16.c` (blob `2115bc3484118a7e89e9fc95a9239119cf608fa8`) contain no `004543F0` / `FUN_004543f0` definition; the generated prototype header is declarations only.
- A GitHub-wide search for the bare address/name returns homonymous functions in unrelated executables/projects (for example, Lucky.exe and eco.exe). Those are excluded: an x86 address/name is not a cross-executable identity.

This confirms only that the body is **not available in the inspected public Steam decompilation snapshot**; it does not prove the body cannot exist in a separate local analysis database or another correctly identified build. The IDA function name/extent and event notes remain metadata-level evidence. The cMan F4 implementation and its effects on the post-race handoff therefore remain **UNKNOWN** until the matching function body or a typed runtime trace is available.

## 2026-11-04 — Correction: Judge states 4/5 are pre-race intro, not the Results handoff

A re-check of the exact pinned Windows-PC reconstruction and its PC mod-hook delta found that earlier comments describing Judge F0 states 4/5 as a **post-race camera sweep → Results screen** are not reliable. The current code path instead supports a pre-race intro interpretation. This supersedes earlier statements in this dossier that promoted the state-4/5 comments to a post-race lifecycle fact.

**Pinned evidence**
- Base reconstruction: [SW_RACER_RE `258f67aa858ba2e281ce8a6791e49c554b85fae0`](https://github.com/tim-tim707/SW_RACER_RE/tree/258f67aa858ba2e281ce8a6791e49c554b85fae0), notably [Judge F0/F2/F4 source](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c) and [event dispatcher](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrEvent.c).
- PC mod-hook cross-check (same repository snapshot, not vanilla source): [`swrObjJdge_F0_delta`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/dinput_hook/game_deltas/swrObjJdge_delta.cpp#L1205-L1289), blob `fcc9489b533117d1ee8167307cdecc20263da11e`. This is PC mod code and analyst commentary, used as a separate interpretation cross-check; no mod code is copied.

### State path directly visible in the reconstruction

1. **Race setup writes Judge state 4.** The `Jdge` F4 `Begn` handler calls `swrObjJdge_InitTrack` (whose reconstruction body is still `HANG("TODO")`), then explicitly writes `(jdge->flag & 0xfffffff4) | 4` and sets the timer to 0.5. The final explicit write after that incomplete helper is state 4.
2. **State 4 leads to state 5.** Judge F0 case 4 advances when the camera cursor is absent/finished or the intro is skipped. It writes low-nibble state 5, sets a 9.1-second timer, changes viewport/camera parameters, sends `Swee(true)` to cMan, and initializes the post-state delay.
3. **State 5 exits to state 0.** Judge F0 case 5 calls the function labelled `swrObjJdge_StartPostRaceSequence` on accept or timer expiry. That routine sends `Swee(false)`, clears the Judge low nibble to 0, sets a 3.2-second timer, changes camera/UI/pod flags, and sets each pod's own low-nibble state to `POSTRACE` (1) until the later `Go!!` dispatch. Judge F0 case 0 is the countdown; on expiry it advances to state 1 and dispatches `Go!!` to the racer objects.
4. **The separate race-completion path is clearer.** During Judge F0 state 2, finish input/edge handling calls `swrObjJdge_Clear(jdge, 'Fini')`. That helper stores the event, sets Judge state 6, arms a 0.5-second delay, and frees the Test/Toss/Smok/Trig/Chsr pools. State 6 later calls `swrObjJdge_TeardownRace(jdge, jdge->event)`, whose SW_RACER_RE reconstruction body is still a `HANG("TODO")` stub. This is the live unresolved edge toward Hangar/Results, not the state-4/5 intro.
5. **State 3 remains unexplained.** A complete scan of the pinned `swrObj.c` state writes found no direct writer for Judge low-nibble state 3, although an F0 case-3 handler exists. Do not place that handler into a linear lifecycle without finding its writer/caller context.

### Independent PC mod-hook interpretation

The pinned `swrObjJdge_F0_delta` explicitly refers to state 4 as the **pre-race track sweep** and state 5 as the **pod orbit / binder ignition**; its fast-restart and one-stage-per-press logic skips those two intro stages before reaching the countdown. It also notes that the original track-environment setup has a camera spline available but leaves `camSweepState` null, so the stock F0/F2 paths do not walk the pre-race sweep cursor unless the mod re-enables it. This makes the distinction important: the state-4/5 F0 code can be part of the intro even when the stock sweep is dormant.

The reconstruction's own comments for F0 cases 4/5, plus other comments that call the `swrRace_resultsScreenActive` global a Results flag, conflict with the transition sequence above. Treat those comments/symbol names as analyst labels, not authoritative semantics. In particular, the function name `swrObjJdge_StartPostRaceSequence` is not proof of when it is used: in the visible state-4/5 path it is the transition that clears the Judge state to 0 and begins the countdown sequence.

### Corrected lifecycle conclusion and remaining gap

The evidence now supports this partial **Windows-PC** chain:

`Jdge/Begn` → state 4 intro → state 5 pod orbit → state 0 countdown → state 1 Go/race-start → state 2 active race → `Clear(Fini)` → state 6 cleanup delay → `TeardownRace` (body unavailable in SW_RACER_RE).

The initial post-race/hangar/results handoff is **still UNKNOWN** because the teardown body is a TODO in SW_RACER_RE and the separate Steam-PC teardown candidate `FUN_0045dd80` is still marked `NOT_INVOKED` in that snapshot's dependency graph. The Hang menu's screen-5 → Results branch remains conditional on Hang already being active and on screen 5; it is not a proven continuation of this Judge chain.

All of the above is Windows-PC evidence only. It does not identify native GameCube/Wii state numbers, flags, callbacks or results transitions.

### Independent IDA state map and exact-address label correction

The independent IDA notes remove the remaining ambiguity about the *meaning of the state numbers*, while still not proving the post-race callback chain:
- IDA `Entity_Jdge.txt` explicitly labels Judge state 0 as countdown, 1 as racing, 2 as end-race stats, 3 as unknown, 4 as camera-sweep cutscene initialization, 5 as the camera-sweep cutscene's main logic, and 6 as loading back to the cantina or reloading the race. It also notes a condition involving Judge flag/field `+0x130 that can prevent state 4 from advancing to 5. This independently agrees with the pre-race interpretation of 4/5 and supersedes the earlier prose labels in SW_RACER_RE's F0 comments.
- IDA's function names identify `0x0045DFE0` as `Unk_Jdge_StartCountdown` (extent `0x137`), `0x0045DD80` as `Unk_Jdge_LoadFromRace` (extent `0x254`), and `0x00466BD0` as `Unk_Jdge_LoadFromRaceFini` (extent `0x265`). The SW_RACER_RE reconstruction's function label `swrObjJdge_StartPostRaceSequence` at `0x0045DFE0` is therefore a misleading analyst name: its visible body resets the Judge low nibble to 0 and enters the countdown. Treat the IDA names as analyst labels, not retail symbols.
- IDA records the `Begn` event as being called from `0x0045B290` and passing a RaceData pointer/configuration to `0x00466BD0`; this agrees with the SW_RACER_RE F4 `Begn` handler and its still-incomplete `swrObjJdge_InitTrack` body.

**Steam-PC teardown candidate at the matching address:** the pinned Steam export contains `FUN_0045dd80` at the same address as SW_RACER_RE's `swrObjJdge_TeardownRace` stub and IDA's `Unk_Jdge_LoadFromRace`. Its body:
1. performs race cleanup, clears the Test/Toss/Smok/Trig/Chsr pools, and updates the per-racer result/profile records;
2. on a conditional `Fini` branch (`DAT_0050c9f8 & 2`), calls `FUN_00466bd0`, marks scene objects loaded, and sets Judge state 3;
3. otherwise sleeps the Judge, sends `RSet` to the cMan pool, and broadcasts the supplied event through `All!` (substituting `Abrt` if `DAT_0050ca2c` is set).

This is useful body-level cross-reference for the missing teardown stub, but **not a proven normal runtime edge**: the Steam snapshot's own dependency graph explicitly says `NOT_INVOKED --> FUN_0045dd80`. The body is therefore a *candidate implementation at a matching PC address*, not proof that the normal post-race path executes it in the sampled build.

**Hang F4 remains the missing receiver.** IDA names `EntityHangCallback0x24_45A040` at `0x0045A040` (extent `0x34C`), but the inspected Steam text export does not contain `c/FUN_0045a040.c` or an equivalent body. If the candidate teardown's `All!` broadcast is reached, the generic event dispatcher would send it to eligible F4 callbacks, including Hang's slot if configured; without the Hang F4 body or a verified runtime trace, it is still unknown whether/how that message sets Hang menu screen 5 (`POST_RACE_INFO`).

**Refined conclusion:** the pre-race intro state sequence is now independently corroborated, and the missing post-race question has narrowed to the state-6 teardown / Fini-or-Abrt broadcast / Hang F4 receiver chain. The teardown body at `0x0045DD80` is a promising PC cross-reference but remains marked NOT_INVOKED in the inspected Steam dependency graph. Do not claim that Judge Fini currently opens Results. No native GameCube/Wii state mapping is implied.

### Hang Results receiver: what is proven and what remains conditional

Further inspection of the pinned sources narrows the receiver side of the candidate path:

- The independent IDA `Entity_Hang.txt` note identifies Hang menu-screen field `+0x08 = 5` as **race results / POST_RACE_INFO**. This is the Hang menu screen, not the Judge F0 low-nibble state.
- In the Steam-PC export, Hang F0 dispatcher `FUN_00457620` switches on Hang menu screen `+0x08`; case 5 calls `FUN_00439ce0`. The latter creates the `Results` heading and builds the racer/position/time table. This is direct code evidence for rendering the results screen once Hang is already at screen 5.
- The IDA inventory labels Hang's F4 callback `EntityHangCallback0x24_45A040`, address `0x0045A040`, extent `0x34C`. The public Steam C export does not contain `c/FUN_0045a040.c`; the SW_RACER_RE implementation also leaves `swrObjHang_F4` as a `HANG("TODO")` stub. The callback's event handling is therefore not yet visible in these source exports.
- IDA's Hang note associates its `+0x14` transition/control field with distinct values described as loading race→cantina after quitting (6) and after finishing (7), and points to code around `0x0045A0A0` / `0x0045A2A1`. This is analyst-note evidence of separate finish/quit transition paths, not a recovered callback body or proven mapping from Fini to menu screen 5.
- The candidate Steam teardown `FUN_0045DD80` broadcasts the incoming event to `All!` only on its non-special branch. Its special branch, when `(DAT_0050c9f8 & 2) != 0` and event is `Fini`, calls `FUN_00466BD0`, marks scene objects loaded and sets Judge state 3, then returns without the `All!` broadcast. On the other branch it sleeps the Judge, sends cMan `RSet`, and broadcasts the supplied event (or `Abrt` when `DAT_0050ca2c` is set).

**What is now supported:** a Hang Results screen exists at menu screen 5 and its F0 renderer is mapped; an IDA-named Hang F4 callback exists; IDA notes distinguish finish-vs-quit loading states; and a Steam-PC teardown candidate has conditional `Fini` handling plus an `All!` broadcast on one branch.

**What is not yet proven:** that the teardown candidate is reached in the sampled Steam build (its dependency graph still marks it `NOT_INVOKED`); that the non-special `Fini` broadcast is the path taken for a normal race completion; and that Hang F4 converts that event into menu screen 5. The end-to-end Judge-Fini → Hang-POST_RACE_INFO edge remains **UNKNOWN** until the matching Hang F4 body or an exact-build runtime trace is available. Do not infer this from the screen renderer, function names, or the existence of transition-state notes.

### Final bounded Hang F4 source-export scan

A final targeted scan tested both exact source paths and the nearby aggregate text exports in the pinned Steam revision `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`:

- Exact paths `c/FUN_0045a040.c` and `asm/FUN_0045a040.s` both return not found.
- Neither `FUN_0045a040` nor the bare address `0045a040` appears in the inspected aggregate text exports `src/_text13.c` through `src/_text18.c`. Their inspected blob IDs are respectively `41d6f8858d7854098c130f68245bfd8a3e34b3ed`, `8bbc1cde926b8b19f3eda80d0f06be125521e415`, `673cbacba8fbcda3008c3788cab4501059a11b76`, `2115bc3484118a7e89e9fc95a9239119cf608fa8`, `58abf3a432ea1b2d939c8aff88209aec5aa51aaa`, and `249c3990d4d6fcf7f661d7a43fd44fdc8871cda0`.
- Positive control: `src/_text16.c` does contain the Hang F0 body `FUN_00457620` (at line 1131), which dispatches Hang menu screen 5 to `FUN_00439ce0). Thus the scan found the known Hang F0 renderer but not the IDA-named Hang F4 callback.
- The independent IDA inventory still identifies `EntityHangCallback0x24_45A040` at `0x0045A040`, extent `0x34C`. This confirms a named callback exists in that separate metadata snapshot; it does not provide its body here.

This is a bounded **public-source-export availability** result, not proof that the callback is absent from the Steam executable or from a private/local IDA database. The missing F4 receiver remains the concrete evidence blocker for the end-to-end Judge-Fini → Hang-POST_RACE_INFO path.

## 2026-11-04 — PC hover-pad ground contact and wall-collision TODO recovery

This pass closes four high-value PC-reference TODOs as one connected ground-contact/collision subsystem. It reads the exact SW_RACER_RE function addresses and then checks the corresponding Steam-PC C/assembly exports. It is a **read-only behavioural recovery**, not code reuse or a GameCube/Wii implementation claim.

**Pinned references**
- SW_RACER_RE: [commit `66120be334a3fd38c10a259f3528cffbfed8ddc5`](https://github.com/tim-tim707/SW_RACER_RE/tree/66120be334a3fd38c10a259f3528cffbfed8ddc5), in particular [`swrRace.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrRace.c), [`swrRace.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrRace.h), [`types.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/types.h), and [`types_enums.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/types_enums.h). The four target routines are still `HANG("TODO")` in this reference revision.
- Steam-PC Ghidra export: [commit `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef): [ground-contact orchestrator `FUN_00479e10`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00479e10.c), [hover pads `FUN_00476740` C](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00476740.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_00476740.s), [wall scrape `FUN_00477940` C](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00477940.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_00477940.s), [wall response `FUN_00479920` C](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00479920.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_00479920.s), and [block-move collision helper `FUN_0044abc0` C](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0044abc0.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_0044abc0.s). Supporting references: [physics-contact caller `FUN_0047b520`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047b520.c), [ground raycast `FUN_004772f0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004772f0.c), and [scrape-spark builder `FUN_00477850`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00477850.c).

### Recovered call order: physics contact → ground contact → local/non-local collision → hover pads

The Steam `FUN_0047b520` physics-contact routine calls `FUN_00479e10` for the normal ground-contact path (or a separate flat/alternate path when the flat-state bit is set). The corresponding SW_RACER_RE `swrRace_UpdateGroundContact` body provides the same high-level ordering:

1. Save the previous position and determine whether the pod is close enough for full ground work, is a local player, or is explicitly force-grounded.
2. Obtain the ground distance and surface normal through `swrRace_RaycastGround` / Steam `FUN_004772f0`, or reuse the flat-ground cache. Persist the live normal as the pod's `up` vector.
3. In ordinary or magnet/surface-relative mode, apply the corresponding slope-steering routine; apply gravity unless the zero-G-off transition flag suppresses it.
4. Resolve collisions differently by pod class: non-local pods call `swrRace_CollideBlockMove`; local human pods call `swrRace_DetectWallScrape`, combine its position/pushback delta, then call `swrRace_ApplyWallCollision`.
5. When the pod is near enough for pad data, call `swrRace_UpdateHoverPads`. Outside the pad LOD range, write the no-ground sentinel to the four pad records instead.
6. Cache the returned distance in `groundToPodMeasure` (+0x184).

This makes the split explicit: the same frame's ground solver owns terrain normal/gravity/slope alignment, but uses a conservative block-move path for non-local pods and a scrape/impulse path for local players.

### TODO 1 — `swrRace_UpdateHoverPads` (0x00476740)

**Steam-PC body recovered.** The routine selects a 0x6C-byte-stride configuration record through a pointer chain rooted at the racer object, transforms four configured local sample vectors by the pod's orientation, and derives four candidate pad heights in world space.

- When the live surface normal's Z component is within the routine's accepted range, the sample height is solved against the surface plane using the normal; outside that range it falls back to a direct vertical/Z calculation. The exact rdata boundary constants are retained symbolically because their values were not established from this source inspection.
- For valid pads, the routine builds one transform per pad at racer offset `+0x1290 + i*0x40`; invalid pads write the `-100000.0` sentinel at the per-record `+0x38) field. The current SW_RACER_RE type map identifies four shadow-node entries in the pod's part-node array (indices `0x3D..0x40`), consistent with the four generated transforms.
- It derives the returned ground distance from the selected pad-height slots (the body explicitly compares local sample slots 1 and 2), otherwise falling back to the incoming ground distance or a minimum fallback value. The caller stores that result as `groundToPodMeasure` (+0x184).

**Limits:** the semantic name and layout of the 0x6C configuration record, exact rdata threshold values, meaning of the incoming `padFlags`, and why only returned sample slots 1/2 are compared remain unresolved. Do not invent a per-pad collision/physics role beyond the source flow.

### TODO 2 — `swrRace_DetectWallScrape` (0x00477940)

**Steam-PC body recovered.** This routine derives a speed/tilt-dependent wall-scrape reach (with a 1.5-unit minimum), then performs up to two directional ray tests against the pod's collision model, clearing the shared collision-hit result between successful tests. If the impact is within the configured side/height and speed conditions, it calls `FUN_00477850` to build a scrape-spark transform and activate one of the two scrape-spark emitters. It then calls `FUN_0044abc0` to apply the final block-move clamp to the candidate position.

The supporting Steam helper `FUN_00477850` chooses pod part-node slot `0x41` or `0x42` and sets the corresponding `SCRAPE_SPARK_R` / `SCRAPE_SPARK_L` flag (0x10000000 / 0x20000000). This supports a side-specific visual scrape effect. The exact threshold constants and the full meaning of every ray-result/local variable remain symbolic.

### TODO 3 — `swrRace_ApplyWallCollision` (0x00479920)

**Steam-PC body recovered.** The routine consumes the combined wall delta and surface-up vector produced by the local-player branch:

- Projects away the component along the current surface normal, normalizes the remaining impact direction, and transforms it against the pod basis to derive a directional impact response.
- Accumulates a direction-scaled impulse into `velocityCollision` (+0x1D0..+0x1D8).
- On a hard impact, clears `THROTTLE_SETTLED` (FLAG0 0x10) and arms `wallHitCooldown` (+0x264) to 0.1; the existing per-frame code later restores the settled flag after the cooldown.
- Sets the one-shot `WALL_IMPACT_CLAMP` flag (FLAG0 0x40000) on a stronger hit. The Steam physics-contact caller consumes and clears that flag to clamp/reduce `accelThrust` (+0x1A4) as appropriate.
- Updates the collision/turn modifier field (+0x1F4) and emits a `Hitt` event through the entity callback dispatch. The event payload's second FourCC is selected from `KPow`, `RtSd`, `LtSd`, `LtFt` or `RtFt`; retain those exact tags rather than assigning unverified player-facing meanings.

This links wall collision to steering/throttle recovery and event-driven effects, rather than treating it as only a positional pushback.

### TODO 4 — `swrRace_CollideBlockMove` (0x0044ABC0)

**Steam-PC body recovered.** This is a short swept-motion guard used on non-local pods and at the end of the scrape path. It computes the vector from the previous to candidate position; if it is long enough, it normalizes the travel vector and raycasts against the supplied collision model. When the returned hit distance falls within the configured acceptance range, it resets the candidate position to the previous position and returns 1; otherwise it leaves the candidate in place and returns 0. It is a conservative movement clamp, not the richer normal/impulse response used by the local-player wall-collision path.

### Clean-room evidence boundary and remaining work

| SW_RACER_RE TODO | Steam-PC evidence | What is recovered | What remains UNKNOWN |
|---|---|---|---|
| `UpdateHoverPads` (0x00476740) | C + assembly at matching numeric address | Four transformed pad samples, per-pad transform/sentinel records, returned hover-distance selection | Config-record semantics, symbolic thresholds, padFlags semantics, exact meaning of selected pad slots |
| `DetectWallScrape` (0x00477940) | C + assembly at matching numeric address | Two wall-ray attempts, side-specific scrape effect, final block-move clamp | Symbolic reach/impact thresholds and exact local meanings |
| `ApplyWallCollision` (0x00479920) | C + assembly at matching numeric address | Tangential collision impulse, cooldown, settled-throttle reset, one-shot accel clamp, `Hitt` event tags | Numeric constants and exact player-facing semantics of the event subtypes |
| `CollideBlockMove` (0x0044ABC0) | C + assembly at matching numeric address | Swept raycast and revert-to-previous-position condition | Numeric ray-distance thresholds and target-build equivalence |

The Steam snapshot and SW_RACER_RE are separate PC research artifacts. Their equal numeric function addresses and compatible call context make these strong **PC-family cross-reference leads**, but do not prove identical executable/release builds. The Steam export is read-only; no source was copied. SW_RACER_RE is an AGPL-3.0 research project; no code was copied from it either. No binary, ROM, extracted model, sound, texture, asset, or analysis database was uploaded or committed.

**Target-platform boundary:** all four recovered bodies and the surrounding call order above are Windows-PC evidence only. They establish no GameCube/Wii function address, structure offset, shadow layout, collision flag, physics constant or behavior. For Boonta's native target, the next valid step remains to identify the exact lawful local GameCube/Wii executable/build and trace its own ground-contact/collision path with Gekko/Broadway decoding. Do not port these PC offsets or constants by analogy.

## 2026-11-04 — PC boost-charge, engine fire/damage, repair and reset-helper TODO recovery

This pass follows the same core pod-control cluster after the ground-contact work. The target SW_RACER_RE functions are TODO stubs; the pinned Steam-PC C/assembly exports provide body-level cross-reference evidence. This remains read-only research: no third-party source is copied and no console behavior is inferred.

**Pinned references**
- SW_RACER_RE source: [66120be334a3fd38c10a259f3528cffbfed8ddc5](https://github.com/tim-tim707/SW_RACER_RE/tree/66120be334a3fd38c10a259f3528cffbfed8ddc5), especially [swrRace.c](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrRace.c), [swrRace.h](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrRace.h), [types.h](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/types.h), [types_enums.h](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/types_enums.h), and [pinned data-symbol inventory](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/data_symbols.syms).
- Steam-PC reference: [d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef), including [BoostCharge C](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0046bd20.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_0046bd20.s), [engine-fire damage loop](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0046aa30.c), [repair routine C](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0046ab10.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_0046ab10.s), [reset helper](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0046a990.c), [damage accumulator](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00474cd0.c), [explosion handler](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004741d0.c), and [input/control caller](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0046bec0.c).

### TODO 1 — swrRace_BoostCharge (0x0046BD20)

**Steam-PC body and assembly recovered.** This is the boost charge/ready-state helper called during local-player control processing. It is not, by itself, the full boost activation or thrust calculation.

- The pod's boostIndicatorStatus (+0x210) has three observed states: 0 idle/not-ready, 1 charging, 2 ready. boostChargeTimer (+0x214) accumulates frame time while state 1 is valid.
- The gate checks the three named input globals swrRace_ThrottleInput (0x00EC8830), swrRace_ThrustInput (0x00EC884C) and swrRace_BoostInput (0x00EC8850); swrRace_PitchInput is a separate value at 0x00EC883C. Exact threshold values remain symbolic in this pass. In state 0, qualifying throttle/boost plus thrust input starts the charge state and zeros the timer. In state 1, the qualifying inputs must remain valid while the timer advances; crossing the pinned charge-time constant moves the indicator to state 2. Losing the required input before completion resets the charge state.
- In state 2, the boost-input signal consumes the ready state, plays the boost-ready/activation sound path (SFX 0x72) and returns 1. The caller sets BOOSTING (FLAG0 0x00800000) only when this return is nonzero and its earlier eligibility snapshot CAN_CHARGE_BOOST (FLAG0 0x00200000) was set. Releasing thrust and dropping throttle below the caller's threshold clears BOOSTING.
- The SW_RACER_RE enum annotates CAN_CHARGE_BOOST as a speed/alive eligibility gate (>0.75 max speed); the complete retail writer for that flag was not independently traced here. BOOST_OVERDRIVE (FLAG0 0x00400000) is only read/cleared in the inspected retail path and is annotated as never set, so it is not described as an active retail mechanic.

This separates the charge UI state machine from the actual boost flag and the downstream boost-thrust/heat update. The latter remains a distinct path in swrRace_UpdateSpeed and should be audited separately before making a complete boost model.

### TODO 2 — swrRace_ApplyEngineDamage (0x0046AA30) and swrRace_TakeDamage (0x00474CD0)

**Steam-PC bodies recovered; the SW_RACER_RE damage accumulator is already reconstructed.**

- Six engine sections are stored in engineHealth[6] (+0x288), engineStatus[6] (+0x2A0), and the per-section worst-damage history engineHealthMin[6] (+0x270). The three lower indices are the left engine group and the upper three are the right group.
- The Steam damage loop scans the six status words. When the per-section fire bit 0x08 is set, it applies a random, frame-time-scaled damage amount through FUN_00474CD0. The loop also updates a shared damage indicator/feedback path when any engine section is in that state. The exact random/rdata rate constants remain symbolic.
- The damage accumulator increases engineHealth[engineIndex] by PodHandlingData.damageImmunity * amount, clamps it at 1.0, writes status bit 0x01, updates engineHealthMin when a new worst damage value is reached, and adds the incoming amount to totalDamage (+0x2C4). It is a no-op under the invincibility gate, while respawn-invincible/dead, or after the race is finished. Any accepted damage clears the active BOOSTING flag.
- The PC mod-hook's independent symbol notes identify status bit 0x08 as the engine-fire state and bit 0x04 as an active-repair state. The main source confirms the bit operations but does not give full retail names for every transient status bit; bit 0x10 is therefore left as an unnamed repair/fire-control state in this dossier.

### TODO 3 — swrRace_Repair (0x0046AB10)

**Steam-PC body and assembly recovered.** This routine is part of the per-frame player-control tail: ApplyEngineDamage runs first, then Repair. AI pods marked FORCE_GROUND also set REPAIRING and invoke the same routine.

- Local analog control sets the repairing request when swrControl_repairButton is held and swrControl_repairHoldTime exceeds the half-second threshold. Digital control types use input-bit 0x80 and a held-time check; the input map identifies the repair hold-time field as hold-time slot 9. The active request is reflected in pod FLAG0 REPAIRING (0x00000400).
- The routine decrements repairTimer (+0x2BC); while REPAIRING is set it pins that timer to 0.1 seconds so the repair window remains active. It clears transient per-engine repair/cooldown flags each frame, preserves/chooses a damaged engine section, and marks the selected section with status bit 0x04.
- For a section marked for repair, the routine reduces its damage value over time using the pod's repairRate upgrade statistic and the stored worst-damage baseline. The stat is derived from the pod's Repair upgrade (upgrade category 6) and is clamped to [0,1]. The Steam body also contains randomized fire-state clearing and local-player repair audio/notification paths; exact timer and probability constants remain symbolic.
- It scans all six sections by left/right group against a damage threshold and runs a warning timer (+0x2C0). When that timer expires under the applicable group/side conditions, it calls FUN_004741D0 with a side selector (1 or 2). This is the connection between prolonged/severe engine damage and the explosion handler; exact trigger thresholds remain symbolic.

### TODO 4 — swrRace_Explode (0x004741D0) and reset helper swrRace_CheckResetInput (0x0046A990)

**Steam-PC bodies recovered.** swrRace_Explode is a separate missing SW_RACER_RE body reached from the repair/damage warning path. It rejects the request when the pod is not a local/force-ground pod, already in an incompatible death/respawn state, or already exploding. For an accepted event it clears relevant boost/control state, sets the EXPLODING flag (FLAG1 0x00004000) and the death/explosion timer (+0x310), chooses left/right engine-side geometry/effects from the side selector, and emits explosion audio/visual effects. The exact random timing/effect values are source constants still left symbolic.

The smaller helper swrRace_CheckResetInput is much narrower than its local name may imply: it tests input bit 0x2000 in the selected player's in-race input bitset and sets the pod RESPawn flag (FLAG0 0x00001000) if present. **Call-site limit:** in the inspected SW_RACER_RE source the calls to this helper are behind the swrRace_DebugFlag & 0x100 and nonzero debug-level guard. The Steam caller also places it inside a debug-enabled branch. Do not claim that this helper alone proves the normal retail reset-button path; that broader input-to-respawn route remains to be traced separately.

### Combined control / engine loop and remaining unknowns

The recovered PC-family call order is:

UpdatePlayerControl → read input / request repair → BoostCharge → damage-side suppression of boost/roll → engine-damage force/steering feedback → debug-gated reset helper → commit REPAIRING flag → ApplyEngineDamage → Repair → boost-start-window / throttle / steer commit.

The local control path sets BOOSTING only when the charge helper returns 1 and the earlier eligibility bit is present. Damage cancels BOOSTING. Repair can lower per-section damage over time, extinguish fire state, and, after its warning timer/side conditions, invoke the explosion handler.

| SW_RACER_RE TODO | Steam-PC reference | Recovered behavior | Remaining UNKNOWN |
|---|---|---|---|
| BoostCharge (0x0046BD20) | C + assembly | 0/1/2 indicator state, input-gated charge timer, consume-ready return | Exact rdata time/input thresholds; full writer of the eligibility bit |
| ApplyEngineDamage (0x0046AA30) | C | Random time-scaled damage on fire-marked engine sections; shared local feedback | Fire-bit writer/origin and exact rates |
| Repair (0x0046AB10) | C + assembly | Half-second hold request, upgrade-based repair rate, per-section repair state, warning timer → explosion | Exact transient flag meanings, damage thresholds, random fire-clear rates |
| Explode (0x004741D0) | C | Guarded side-specific explosion state/effects | Exact trigger/visual/audio parameters and native target parity |
| CheckResetInput (0x0046A990) | C | Input bit 0x2000 sets RESPawn flag | This helper is only observed behind debug gates; normal reset route unresolved |

The Steam export and SW_RACER_RE are separate Windows-PC research artifacts. Matching numeric addresses/call context are strong PC-family cross-reference leads, not proof of identical retail executable/release. No code, symbols, assets, binary, ISO, ROM, BIOS, or analysis database was copied into Boonta. No AGPL source was adapted.

**Target-platform boundary:** none of these values/addresses/flags are assigned to GameCube or Wii. A native implementation still requires an exact lawful local console build identity and a console-specific trace of input, boost, engine damage, repair, reset and explosion state. These PC findings are reference evidence only.

## 2026-11-04 — PC boost thrust and overheat loop closed across physics/contact

The previous section recovered the boost charge indicator, damage/repair and fire loop, but left the downstream thrust/heat coupling open. This pass follows the distinct per-frame speed, boost-impulse and temperature routines, then checks the physics-contact caller.

**Pinned Steam-PC bodies**
- [speed/acceleration routine FUN_004783e0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004783e0.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_004783e0.s)
- [boost accumulator/impulse FUN_004787f0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004787f0.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_004787f0.s)
- [engine temperature/overheat routine FUN_004788c0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004788c0.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_004788c0.s)
- [motion integrator FUN_00478d80](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00478d80.c)
- [physics-contact caller FUN_0047b520](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047b520.c), which calls FUN_004788c0 at line 105.
- Matching SW_RACER_RE references: [UpdateSpeed / ApplyBoost / UpdateHeat](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrRace.c), [physics-contact callback stub](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrObj.c#L925-L930), and [function declarations](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrRace.h).

### Boost is three distinct operations, not one timer

1. **Charge / ready state** (BoostCharge, 0x0046BD20): the earlier section recovered the 0→1→2 indicator and input gates. The helper's return is consumed by the controller only when the earlier CAN_CHARGE_BOOST eligibility snapshot is set.
2. **Acceleration response** (UpdateSpeed, 0x004783E0): the boost-active or boost-start state selects an acceleration factor of 4.0 rather than the ordinary 1.5. The same routine still applies throttle, traction/surface, braking, airborne and pod-stat gates; these two factors are not a universal constant multiplier on final speed.
3. **Separate boost impulse** (ApplyBoost, 0x004787F0): while BOOSTING is set, boostValue accumulates at 1.5 per second. When not boosting it decays with a 5-per-second decelerator and snaps to zero below 0.001. Air-braking clears BOOSTING. For positive boostValue, the routine returns the extra longitudinal term:
   
   boostValue * podStats.boost_thrust / (boostValue + 0.33)

   IntegrateMotion calls UpdateSpeed, adds this separate ApplyBoost result, then passes the sum into traction. This distinguishes the normal acceleration response from the additional boost impulse.

### Temperature closes the overheat → engine-fire → damage chain

The Steam-PC F2 physics-contact routine at FUN_0047B520 calls FUN_004788C0 (the matching numeric address for SW_RACER_RE swrRace_UpdateHeat) during the contact update. The recovered body shows:

- On lava, temperature falls by 20 units per second regardless of boost; the pod's tilt biases the failing side (left for tilt below -0.5, right above +0.5).
- Otherwise, an active BOOSTING flag drains engineTemp at podStats.heatRate; without boost, it recovers at podStats.coolRate.
- The gauge is capped at 100. At or below zero it is pinned to zero, one of six engine sections is selected (tilt-biased on lava, random otherwise), an engine-fireball helper is called if that section was not already burning, status bit 0x08 is set, and BOOSTING is cleared.
- The preceding section's ApplyEngineDamage routine scans status bit 0x08 and applies ongoing frame-scaled damage to those burning sections through the damage accumulator. This connects boost/lava heat to the previously recovered per-section damage, repair and explosion logic.

**Important source-wiring qualification:** the SW_RACER_RE tree contains the swrRace_UpdateHeat body and declaration, but its matching swrObjTest_UpdatePhysicsContact callback at 0x0047B520 remains a HANG("TODO") stub. The SWR text search finds no ordinary source-level call to swrRace_UpdateHeat; the Steam-PC caller supplies the concrete F2 call-site evidence for that separate PC snapshot. Do not assume the reconstructed SWR tree has already wired this helper into its frame loop, and do not infer a native console call path.

### Updated boost / thermal evidence table

| Routine | Recovered PC-family behavior | Remaining UNKNOWN |
|---|---|---|
| BoostCharge (0x0046BD20) | Charge indicator 0/1/2 and input-gated ready result | Exact rdata thresholds; complete writer of eligibility flag |
| UpdateSpeed (0x004783E0) | 4.0 vs 1.5 acceleration response when boost/boost-start is active | Symbolic speed/traction threshold constants; exact build identity |
| ApplyBoost (0x004787F0) | 1.5/sec boost-value growth, 5/sec decay, air-brake cancel, separate boost-thrust formula | Exact native-target equivalence |
| UpdateHeat (0x004788C0) | Boost heat drain, cooling, lava drain/side bias, section fire and boost cancel | Exact native-target call path; the SWR F2 wrapper remains TODO |
| ApplyEngineDamage (0x0046AA30) | Burning-section status causes ongoing damage | Complete source/origin of every fire-state path and symbolic damage rates |

The revised PC-family chain is therefore: BoostCharge ready → controller sets BOOSTING when eligible → UpdateSpeed changes acceleration response + ApplyBoost adds a separate longitudinal impulse → physics-contact UpdateHeat drains/cools temperature → overheat sets a per-section fire bit and cancels boost → ApplyEngineDamage accumulates section damage → Repair can restore sections or its warning path can invoke Explode.

This chain is supported in the pinned Windows-PC sources only. The Steam and SW_RACER_RE snapshots do not prove identical executable/release identity. The SWR physics-contact wrapper is still a TODO, and no GameCube/Wii address, flag, constant, update order or behavior is inferred.

## 2026-11-04 — PC track-trigger volumes and runtime activation pipeline

This pass recovers the missing SW_RACER_RE trigger-volume TODO as a connected track-surface → geometry → runtime-object → type-dispatch pipeline. The reference is still a separate Windows-PC snapshot; this is not a port or a claim about console trigger IDs.

**Pinned references**
- SW_RACER_RE: [revision 66120be334a3fd38c10a259f3528cffbfed8ddc5](https://github.com/tim-tim707/SW_RACER_RE/tree/66120be334a3fd38c10a259f3528cffbfed8ddc5), including [swrRace trigger and surface-tag code](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrRace.c), [trigger type/filter declarations](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/types_enums.h), [trigger data layout](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/types.h), and [object callback declarations](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrObj.h).
- Steam-PC: [revision d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef): [track-surface update FUN_00476ea0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00476ea0.c), [range test FUN_00476ac0 C](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00476ac0.c) / [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_00476ac0.s), [runtime Trig lookup/create FUN_0047c7d0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047c7d0.c), [type dispatcher FUN_0047ce60](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ce60.c), [pre-trigger script event FUN_0047e830](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047e830.c), and [destructible handler FUN_0047ca90](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ca90.c).

### 1. Surface-tag caller and trigger-list source

The SWR reconstruction's swrRace_UpdateSurfaceTag (numeric address 0x00476EA0) reads the current terrain model's swrModel_Behavior. If that behavior has a linked trigger list, it calls swrRace_ActivateTriggersInRange(pod, behavior->triggers). It also calls the same routine for the separate specialActiveTrigger global when non-null. The Steam-PC FUN_00476ea0 has the corresponding calls to FUN_00476ac0 for the mesh behavior trigger list and the global special trigger.

Thus the trigger system is attached to the current surface/track behavior plus an optional special trigger; it is not simply an unfiltered scan of every volume in the whole level.

### 2. Trigger description layout and geometric test

The SWR swrModel_TriggerDescription layout is:
- +0x00 center (rdVector3);
- +0x0C direction/orientation vector (rdVector3);
- +0x18 size_xy and +0x1C size_z;
- +0x20 affected model node;
- +0x24 16-bit trigger type;
- +0x26 16-bit filter flags;
- +0x28 linked-list next pointer.

Steam FUN_00476ac0 iterates this linked list. For the general trigger case it uses half of size_xy and half of size_z, forms the oriented horizontal segment defined by center and direction, projects the pod's current XY position onto that segment, clamps the projection to its segment endpoints, then compares squared horizontal distance against the horizontal radius and pod Z against the trigger's vertical half-height. This is a capsule/corridor-like vertical volume around an oriented segment, not an axis-aligned box.

Two trigger types (0x66 / decimal 102 and 0x68 / decimal 104 in the SWR enum) take a distinct crossing test: the routine checks the pod's previous/current positions against the trigger plane, along with the trigger's horizontal parameter and vertical bounds. Do not collapse these two plane-crossing cases into the general proximity test.

### 3. Eligibility masks — one unresolved bit-comment discrepancy

The Steam range test reads the trigger's 16-bit field at +0x26 before doing geometry. The source comments in the SWR enum describe:
- 0x02 as requiring speed above a threshold (commented as >150);
- 0x04 / 0x08 / 0x10 as lap-1 / lap-2 / lap-3 exclusions;
- 0x20 as not triggered by AI.

The Steam body is consistent with the speed and AI filters: a trigger carrying 0x02 is skipped below a symbolic speed threshold, and 0x20 is skipped when the pod lacks the LOCAL flag. For 0x04/0x08/0x10, the Steam routine compares a selector at score/race data offset +0x78 against 0/1/2 before skipping; the SWR enum calls these lap exclusions, but the precise meaning of that selector field was not independently recovered here.

**Contradiction retained:** the SWR enum comment calls bit 0x01 “enabled”, but the Steam implementation sets its local skip boolean when bit 0x01 is set. That means the observed Steam behavior is “bit set → this trigger is not tested” rather than the comment's apparent “bit set → enabled”. Do not implement or rename this bit until the source comment, exact track data and Steam behavior are reconciled. The numeric speed threshold also remains symbolic in the Steam export.

### 4. Runtime Trig allocation and one-shot suppression

After a geometric hit, Steam FUN_00476ac0 calls FUN_0047c7d0 for the trigger description:
- It searches the Trig manager for a live runtime object already associated with that exact description pointer (+0x4C).
- If a matching runtime object exists with its FIRED bit (runtime Trig flag 0x02) set, the helper returns null; this prevents an already-consumed one-shot from being handed out again.
- Otherwise it reuses the matching runtime object, or allocates a new Trig object from the manager pool, stores its type and description pointer, references the affected model node and resolves two node animation slots (8 and 9).
- The SWR runtime Trig flags separately name ACTIVE (0x01), FIRED (0x02), and FX_SPAWNED (0x04).

This separates the static model trigger description from the runtime trigger object that tracks its activation, animation and one-shot state.

### 5. Script event and type-specific effects

For the surface-range path, FUN_00476ac0 calls FUN_0047ce60(runtimeTrig, pod, 0). With the third argument's bit 0 clear, the dispatcher first calls FUN_0047e830, which sends a SithCog “trig” event for the affected model/trigger to the pod's current game-script context, then clears the runtime timer and switches on the trigger type.

Directly visible Steam branches include:
- 100 (ice destructible) and 102 (rock destructible): the shared FUN_0047ca90 path handles target removal, hit feedback and explosion presentation.
- 101 / 307: start an affected-node animation.
- 103: remove/alter the target tent object.
- 104: invoke the guarded explosion/death path.
- 105: collapsing-glacier animation plus camera-shake behavior.
- 106: dispatch to a falling-asteroid effect helper.
- 108: initialize the slalom-flag/spawn helper.
- 203: Tusken-raider hazard/event path.
- 213 and 306: earthquake / shortcut and camera-shake handling.
- 312: falling-pillar animation/shake path.
- 314 and 501: methane-vapor and lava-splash helper paths.
- 900: teleport-to-spline helper path.

The SWR enum also names balloon/flame/fish/dozer spawner IDs (208, 211, 308, 310) and unknown type 503; this inspected Steam dispatcher body does not establish their full call paths. Keep those specific cases marked unresolved rather than extrapolating from the enum labels.

### Evidence boundary and remaining work

The connected PC-family evidence is now: current terrain behavior / special trigger list → linked trigger description → filter and segment/plane hit test → Trig runtime object lookup/create with FIRED suppression → “trig” script event → type-specific object, animation, hazard, explosion, spawn or teleport helper.

The SWR source has the matching trigger activation function as HANG("TODO"), but its surface-tag caller and static trigger/runtime structures are present. The Steam source provides C and assembly for the range test, plus runtime Trig and dispatcher bodies. The two PC source snapshots remain separate and their exact executable identity is unresolved. Filter bit 0x01, selector +0x78 and symbolic geometric/speed thresholds remain specific open questions. No code was copied, and no native GameCube/Wii trigger IDs, offsets, masks or behavior are inferred.

## 2026-11-04 — PC trigger asset registration, scene construction and planet-specific loading

The previous section recovered how an already-loaded trigger description is tested and activated. This follow-up traces how trigger descriptions are registered, how their runtime Trig pool and scene group are created, and how planet/track-specific trigger models are attached to the loaded track scene. All findings below remain pinned Windows-PC reference evidence.

**Pinned Steam-PC references**
- [Judge track-scene setup FUN_00465510](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00465510.c)
- [Trigger-group setup FUN_004651F0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004651f0.c)
- [Planet/track trigger-model loader FUN_0047DDC0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ddc0.c)
- [Recursive trigger-node walker FUN_0047DC40](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047dc40.c)
- [Static trigger-description initializer FUN_0047D380](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047d380.c)
- [Scene trigger-node helper FUN_0047D310](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047d310.c)
- [Static scene-group initializer FUN_0047DD90](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047dd90.c)
- [Runtime Trig lookup/create FUN_0047C7D0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047c7d0.c)
- [Type dispatcher FUN_0047CE60](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ce60.c), [multiplayer trigger bridge FUN_0047E7E0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047e7e0.c), and [SithCog trigger-event sender FUN_0047E830](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047e830.c).
- Matching SW_RACER_RE TODO declarations are in [swrObj.c](https://github.com/tim-tim707/SW_RACER_RE/blob/66120be334a3fd38c10a259f3528cffbfed8ddc5/src/Swr/swrObj.c) at the corresponding addresses 0x004651F0, 0x0047D310, 0x0047DC40, 0x0047DD90, 0x0047DDC0, 0x0047E7E0 and 0x0047E830.

### 1. The Judge setup creates a bounded Trig pool before loading trigger assets

Steam FUN_00465510 is the track-scene setup path. After building the scene/track-model group structures, it calls FUN_004651F0(param_1). That routine:
1. allocates a typed Trig manager pool with capacity 0x1E (30 runtime trigger objects);
2. clears/resets the Trig manager state using FUN_00450DB0('Trig');
3. calls FUN_0047DDC0(judge->planet, judge->planetTrack, judge->trackModelNode) and stores its returned scene-group pointer.

The call arguments are directly cross-checked against the SWR Judge layout: +0x1AC is planet, +0x1C0 is planet-track index, and +0x30 is the track model node. This is a concrete setup call-site in the Steam snapshot; it is not yet a native-console call-site.

### 2. The static trigger scene group and per-planet model selection

Steam FUN_0047DD90 initializes a static scene/trigger-group structure at DAT_00e25de0, resets the registered-node count, initializes the backing pointer table at DAT_00e259c0, and returns that group descriptor. This is separate from the 30-object runtime Trig manager pool created immediately beforehand.

FUN_0047DDC0(planetId, planetTrack, trackModelNode) clears its working trigger-node registry, stores the planet selector and loads a planet-specific set of model IDs. Exact model IDs visible in this pinned Steam source are:

| Planet selector | Model IDs passed to the loader |
|---:|---|
| 0 | 0xFC, 0xFB, 0x134 |
| 1 | 0xFE, 0xFB, 0xC4, 0xC5 |
| 2 | 0x9B, 0x132 |
| 3 | no additional trigger models in this switch branch |
| 4 | 0x128, 0x127, 0x132, 0x13D, 0x137 |
| 5 | 0x138, 0x13D |
| 6 | 0x133 |
| 7 | 0x135 |

The model IDs are passed to Steam's model loader FUN_00448780 and their resulting scene/model handles are stored in per-slot globals. Some are grouped through FUN_0047BEE0 and registered with the scene node visibility system. When trackModelNode is non-null, each planet branch invokes FUN_0047DC40(trackModelNode) to traverse the loaded track scene and initialize embedded trigger descriptions. These IDs are model/resource selectors in the PC reference, not trigger-type IDs and not GameCube/Wii asset IDs.

### 3. Recursive track-node walk and per-description initialization

Steam FUN_0047DC40 distinguishes a mesh-like node tag (0x3064) from a general grouped node:
- For tag 0x3064, it enumerates child scene objects. If a child's resolved object has a trigger-description pointer at +0x3C, it calls FUN_0047D380(descriptionList, visibilityContext).
- For general nodes with flag 0x4000, it recurses through the child pointer array and combines the child visibility masks. When node flag 0x8000 is present, it temporarily sets a global traversal guard (DAT_0050CB50) to avoid re-entering a special visibility branch, then restores the previous value.
- Under the configured planet/culling mode, the traversal uses FUN_0047DA10 to compute a spatial visibility mask from the node's bounds and applies that mask to the node/children. The exact symbolic thresholds and meaning of every scene flag are not renamed here.

FUN_0047D380 walks each linked trigger description (next pointer at +0x28) and first registers its pointer through FUN_0047E760. That registration helper stores up to 200 description pointers in a global table used by the multiplayer bridge. It then performs trigger-type-specific scene initialization: creates or attaches scene nodes via FUN_0047D310, references model child animation slots, changes node visibility/render state, marks filter bits, and records the special active trigger for types that use that route.

FUN_0047D310(description, visibilityMask, slot) obtains or allocates a per-description scene helper from a bounded registry (50 entries, stride 0x58), records the description pointer and a slot pointer, adds it to the global scene-object list, and applies scene/visibility flags. The numeric slot and renderer flag arguments are preserved as implementation details; their complete semantic names remain unknown.

### 4. Reconciliation of trigger filter bit 0x01 — what the initializer adds

The previous range-test section correctly noted a discrepancy: SWR's enum comment calls trigger-description flag 0x01 "enabled", while Steam FUN_00476AC0 skips a description when this bit is set.

The new initializer trace narrows that conflict:
- Steam FUN_0047D380 explicitly sets bit 0x01 for type 0xD3 (decimal 211, flame-spawner family) and type 0x136 (decimal 310, dozer-spawner family) after their special scene-node setup.
- The same initializer sets bit 0x02 for type 100 and some 202/212 variants, and bit 0x20 for type 105/203/312/314/501 families. Those latter bits align with the already-observed speed / not-AI filter families.
- The types with bit 0x01 set are therefore not simply "enabled in the generic proximity pass". The evidence is consistent with "special scene-initialized / do not use ordinary proximity activation" for these particular types, but the meaning of bit 0x01 across all map data is not fully resolved. Keep the field unnamed until original track-data samples and the special per-frame spawner handlers are reconciled.

This is more specific than the earlier enum-vs-range-test contradiction, but it is not sufficient to rename the bit globally.

### 5. Multiplayer bridge and script-event suppression

Steam FUN_0047E7E0 is a separate indexed activation path: it resolves a trigger description from a global registered-description table using the requested index, obtains/reuses the runtime Trig object via FUN_0047C7D0, and calls FUN_0047CE60(..., 1). The third argument's bit 0 suppresses the dispatcher's normal pre-trigger FUN_0047E830 SithCog message.

The normal range-hit path calls FUN_0047CE60(..., 0), so it first invokes FUN_0047E830. That routine resolves the trigger's script/event index and sends the "trig" event into the relevant game-script context with the racer score/context pointer. Thus the normal geometric route and the indexed multiplayer route converge on the same runtime type dispatcher but have different pre-dispatch script-event behavior.

### Updated trigger lifecycle — static content to runtime activation

The full PC reference chain is now:

Judge track scene setup → allocate/reset 30-object Trig manager → initialize static trigger-scene group → planet-specific model/resource selection → recurse loaded track model nodes → enumerate and type-initialize trigger descriptions → register description pointers / create per-description scene helpers → at runtime, geometric or indexed lookup finds/creates Trig object → optional "trig" script event → type-specific animation, destructible, hazard, spawn, camera, or teleport behavior.

The SWR tree still has the corresponding scene-setup and initialization functions as HANG("TODO"); the Steam C/ASM supplies the comparative PC implementation. The two source snapshots are not proven identical builds. The filter bit 0x01, trigger resource/model IDs and every node/visibility mask remain PC-reference facts only. No code/assets were copied, and no native GameCube/Wii trigger model, ID, data layout, or behavior is inferred.



## 2026-11-04 — special spawner trigger boundary (types 211 and 310)

The enum labels for trigger types 211 and 310 suggest flame/dozer spawning, but their visible handling does not follow the ordinary trigger-effect path. This follow-up separates (a) description-time scene setup, (b) the generic per-object Trig callbacks, and (c) the still-unrecovered spawn/update mechanism. All conclusions remain Windows-PC comparative evidence plus the separately pinned SW_RACER_RE reconstruction; none is native GameCube/Wii evidence.

**Pinned sources**
- [SW_RACER_RE trigger enum](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types_enums.h)
- [SW_RACER_RE Trig callback wiring](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrEvent.h)
- [SW_RACER_RE Trig F0/F2/F4 and setup routines](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c)
- [Steam-PC static trigger-description initializer FUN_0047D380](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047d380.c)
- [Steam-PC runtime trigger dispatcher FUN_0047CE60](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ce60.c)
- [Steam-PC Judge scene setup FUN_00465510](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00465510.c)

### 1. What the current SWR trigger object actually updates

The pinned SWR enum labels 208 as BalloonSpawner, 211 as FlameSpawner, 308 as SpawnFish, and 310 as DozerSpawner. Its `Trig` event-manager entry wires the 0x58-byte object to `swrObjTrig_F0`, `swrObjTrig_F2`, a no-op F3, and `swrObjTrig_F4`.

In the inspected SWR implementation:
- `swrObjTrig_F0` has explicit timer/animation/camera-shake cases for several ordinary trigger effects, but no FlameSpawner (211) or DozerSpawner (310) case.
- `swrObjTrig_F2` has a distinct transform-follow path for BalloonSpawner (208) and SpawnFish (308). It does not list FlameSpawner (211) or DozerSpawner (310); its remaining switch is for FX-animation placement.
- `swrObjTrig_F4` handles object lifecycle sub-events (allocation/reset/free), not a spawner-specific spawn routine.

This establishes only that the current reconstruction's visible per-object Trig F0/F2/F4 callbacks do not implement those two types. It does **not** prove that the retail game has no separate spawner system or that no other object manager handles them.

### 2. What the Steam-PC initializer does for 211 and 310

Steam FUN_0047D380 is a static trigger-description/scene initializer, not the runtime type dispatcher:
- For type 211 (0xD3), it obtains a scene helper via FUN_0047D310(description, visibility, 2). When the helper exists, it builds an oriented transform from the description's directional fields and position/height values, applies it to the helper, and sets description byte +0x26 bit 0x01.
- For type 310 (0x136), it obtains a scene helper via FUN_0047D310(description, visibility, 0). When the helper and affected node are present, it copies the node transform onto the helper and sets the same description bit 0x01.

Neither branch visibly creates a runtime Trig object through FUN_0047C7D0 or performs a spawn. They show per-description scene attachment plus a flag write. The later Steam FUN_0047CE60 runtime dispatcher has no explicit 0xD3 or 0x136 case in its exported body either. Together with the proximity checker skipping descriptions whose +0x26 bit 0x01 is set, this supports treating these types as outside the ordinary proximity/dispatcher route until a separate consumer is identified.

### 3. Numeric namespace collision: trigger type 310 is not model ID 310

The same number appears in two different SWR enums:
- Trigger-type enum: 310 = `swrModel_TriggerType_DozerSpawner`.
- Model-ID enum: 310 = `MODELID_gate01_part`, while `MODELID_dozer_part` is 312.

Steam FUN_00465510 independently loads resource/model ID 0x136 (decimal 310) during Judge scene setup. That is a model-resource selector in this call, not evidence that trigger type 310 loads a model with the same semantic name. Do not collapse trigger-type IDs, model IDs, and track-resource selectors into one namespace. The same general caution applies to other equal numeric values such as 211.

### Remaining gap

The evidence now narrows the question: where, if anywhere, do flame/dozer spawner descriptions feed a non-Trig per-frame object or spawn manager after scene initialization? No such consumer has been established in these pinned public exports. The next valid step is a complete xref/caller trace on the exact matching local executable/analysis database or an independently verified source body; absent that, the spawn scheduler, lifetime, node-follow behavior and activation conditions remain UNKNOWN. Do not implement these types from enum comments or scene initialization alone.

No third-party code or proprietary asset was copied; no gameplay code was changed; no GameCube/Wii behavior is inferred.


## 2026-11-04 — planet-5 resource slots for the Flame/Dozer scene helpers

A follow-up matched the two special trigger-description helper slots to the planet-specific model-resource setup. This adds a concrete resource association, but still does not recover a spawner scheduler or prove runtime object creation.

**Pinned references**
- Steam-PC trigger-scene loader [FUN_0047DDC0](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ddc0.c), blob `d26c61cc3b2317a6e4621f749bad02342763d23a`.
- Steam-PC description initializer [FUN_0047D380](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047d380.c), blob `be10b94456a0af738dbaea2ac3ef553b9cb587c9`.
- Steam-PC helper allocation [FUN_0047D310](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047d310.c), blob `15d434c523d051c1a97f4ab1d857fccdf57b2ae4`.
- SWR trigger/model enum [types_enums.h](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types_enums.h), blob `3008282a2a96ef921ad343d51a60cec1a4df9545`.

### Planet selector 5 establishes the matching model resources

In Steam FUN_0047DDC0, the `param_1 == 5` branch:
- loads model ID `0x138` (decimal 312) and stores its scene pointer in `DAT_00e26fc0`;
- loads model ID `0x13D` (decimal 317) and stores its scene pointer in `DAT_00e26fc8`;
- scales the latter resource with a uniform factor represented by `0x4019999A`;
- then, when the track root is non-null, calls FUN_0047DC40 to walk and initialize the track's trigger descriptions.

The pinned SWR enums name decimal model ID 312 `MODELID_dozer_part` and decimal model ID 317 `MODELID_fx_flameanim_part`. The trigger enum separately names type 310 `DozerSpawner` and type 211 `FlameSpawner`. These are separate namespaces and separate IDs.

### The two trigger descriptions consume those resource slots

Steam FUN_0047D380 shows:
- Type 211 (`0xD3`) calls FUN_0047D310 with slot index 2, which stores a pointer to `DAT_00e26fc8`. Its helper is positioned using the description's direction/position fields before the description bit 0x01 is set.
- Type 310 (`0x136`) calls FUN_0047D310 with slot index 0, which stores a pointer to `DAT_00e26fc0`. When its affected node exists, the helper receives that node's transform before the same description bit is set.

FUN_0047D310 obtains a scene helper through FUN_0047C130. That allocator reserves from a 50-entry registry of 0x58-byte helpers initialized with object type `0xD065`; the helper stores a pointer to the selected global resource slot and is added to the trigger-scene helper list. This is a scene-transform/helper object, distinct from the runtime `Trig` manager pool. The current SWR `Trig` F0/F2 callbacks and the inspected Steam FUN_0047CE60 dispatcher still have no dedicated 211/310 runtime effect cases.

### What this proves — and does not prove

For the Steam-PC planet-selector-5 setup, there is now a direct static chain:
- FlameSpawner description 211 → helper slot 2 → loaded model ID 317 `fx_flameanim_part`.
- DozerSpawner description 310 → helper slot 0 → loaded model ID 312 `dozer_part`.

This proves the per-description scene-resource/helper association in that specific PC code path. It does **not** prove when the flame/dozer becomes active, whether another manager spawns moving entities, how lifetime/despawn works, or whether the helper itself is the visible instance. No other consumer/scheduler has been established from the inspected public export. Keep runtime spawn behavior UNKNOWN and do not implement it from this static association.

No GameCube/Wii behavior is inferred; no third-party code or game-derived asset was copied.


## 2026-11-04 — PC model-block LZSS recovery: Steam caller cross-reference closes the SWR loader TODO

This is a high-priority *loading dependency* recovered in the Steam-PC reference. The SW_RACER_RE source has a stub at the same numeric address, and the Steam export contains both the corresponding decompressor body and a model-loading caller. This closes a PC-reference understanding gap only; it does not provide a native GameCube/Wii implementation or establish that the two PC snapshots are identical executable builds.

**Pinned evidence**
- SW_RACER_RE [`swrLoader.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrLoader.c), revision `258f67aa858ba2e281ce8a6791e49c554b85fae0`, blob `57382032b4c6a4dcf41321174a133d1e59df2547`: `swrLoader_DecompressLZSS` at `0x0042D520` is `HANG("TODO")`.
- SW_RACER_RE [`swrModel.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrModel.c), same revision, blob `63a97f70cbbf67a37f5aafd9eaa337dbdf0b023d`: model-block parsing and the compressed-model caller are present.
- SW_RACER_RE [`swrLoader.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrLoader.h), blob `d9c928f0ea5d700c91db5e26d452ad7ce1c90f02`: the declared function address is `0x0042D520`.
- Separate Steam-PC export [`FUN_0042d520.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0042d520.c), revision `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`, blob `226d35b161304a01d1d84df79b075d95c075cb1d`, with the matching [assembly](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_0042d520.s), blob `815d2dfc045f88dec4680184e25267480cbf9cf6`.
- Steam-PC model loader [`FUN_00448780.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00448780.c), same revision, blob `0d5cca3cb86922df3ba5809a1e3e55cc13ce9f52`.

### 1. Decoder behavior visible in the Steam-PC body

The inspected body is an LZSS-style token stream with a 4 KiB rolling history area:
- A control byte governs up to eight following tokens, tested bit-by-bit from bit 0 upward.
- A set control bit selects a one-byte literal. The byte is copied to the output and also written into the rolling history.
- A clear control bit selects a two-byte back-reference token. The body derives a history source value and a run control from the token bytes, copies bytes from the history area to output, and mirrors each output byte back into the history area.
- The history write index starts at 1 and wraps with `& 0xFFF`. The source lookup also masks its running index with `0xFFF`, consistent with a 4096-byte circular window.
- A decoded source value of zero terminates the decompressor.

**Signed-field detail from the assembly:** for the two-byte back-reference token, the first byte is sign-extended and its low nibble contributes the upper part of the source value; the second byte is also sign-extended and added as the low component. The resulting source value is wrapped with `& 0xFFF` when read from the ring. The run control is an arithmetic right shift of the signed first byte by four, then incremented; the copy loop runs from index zero through that value inclusively. Thus, for first-byte high nibbles 0–7 the visible body copies 2–9 bytes; for high nibbles 8–E the signed control goes negative and the assembly skips the copy loop; for high nibble F it copies one byte. These are exact consequences of the inspected assembly, **not** a claim that every such token is valid in retail streams. The second byte's sign extension also means the source calculation is not safely described as a conventional unsigned 12-bit offset. The valid token domain still needs a controlled lawful stream or a verified format specification.

The assembly independently confirms that the dictionary base is computed as the compressed-input pointer minus `0x1000`. The body does not show an explicit initialization/clear of that preceding 4096-byte region. How its initial contents are made valid, and whether every stream begins with tokens that avoid undefined history, remain UNKNOWN.

### 2. The model-block caller and its safety contract

The Steam `FUN_00448780` caller shows a distinct compressed-model path:
1. It reads a model record's first 12 bytes and checks for the big-endian tag `Comp`.
2. The third 32-bit header word is treated as the declared decompressed size.
3. The compressed payload begins immediately after that 12-byte header; its stored size is the model-record span minus 12 bytes.
4. The caller chooses an 8-byte-aligned source buffer near the high end of the asset arena and keeps the output model buffer at the low end.
5. Before reading and decompressing, it checks available asset-buffer capacity for the declared output size plus an 8-byte margin, and checks that the compressed source region does not overlap the declared output span.
6. It reads the compressed payload, calls `FUN_0042D520(source, output)`, then advances the asset-buffer cursor to output start plus the declared decompressed size. The subsequent model mask pass performs byte-swaps and pointer/resource fix-ups.

The matching SWR `swrModel_LoadFromId` source has the same `Comp` header check, declared-size read, separated input/output buffer placement, preflight capacity/overlap checks, decoder call and cursor advance — but its decoder body is still the HANG stub.

**Important safety limit:** the decompressor signature receives only two pointers; its visible body has no explicit compressed-input length or output-capacity argument and performs no explicit per-token bounds check. The caller's preflight checks protect the declared output span and input/output separation, but the inspected code does not visibly compare an actual decoded byte count with the header's declared decompressed size. The zero-source terminator ends decoding. A clean-room implementation must not copy this unchecked interface as-is: it needs explicit input length, output capacity, checked history references, termination/error reporting and an exact decoded-length check.

### 3. Scope, confidence and next validation

This establishes a strong PC-family cross-reference that the SWR loader TODO corresponds to a live model-block decompressor in the pinned Steam-PC export. It does **not** establish a console compression format, asset compatibility, endian details beyond the observed PC path, or a matching executable identity between the two PC snapshots. A bounded search found the model loader as the visible Steam caller; this is not proof that no other caller exists in the executable or private analysis database.

Before any clean-room decoder is implemented, the next evidence should be a lawful, locally held, non-published test stream or a source-backed fixture with known input/output lengths. It must validate literal ordering, signed back-reference fields, ring-window initialization, overlap-copy behavior, terminator handling, truncated input, malformed offsets, maximum output and declared-size mismatch. No commercial model block, ROM, DOL/REL, extracted asset or derived game data is to be committed as a fixture.

No third-party implementation code was copied. This entire finding remains Windows-PC comparative evidence; it is not a GameCube/Wii format claim.


## 2026-11-04 — PC model-block post-decompression fix-ups and a cross-snapshot size discrepancy

The model loader does substantially more than decompress bytes. Its mask-driven pass converts marked disk words into process-local references before the model-specific structure walk. Comparing the pinned Steam-PC implementation with the pinned SW_RACER_RE reconstruction also exposed a potentially important loop-bound mismatch.

**Pinned references**
- Steam-PC [`FUN_00448780.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00448780.c), revision `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`, blob `0d5cca3cb86922df3ba5809a1e3e55cc13ce9f52`.
- Steam-PC [`FUN_004485d0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004485d0.c), blob `d7dc30619a9b99d5e603ebdf1427f89077ad1f83`.
- Steam-PC [`FUN_00448bd0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00448bd0.c), blob `4540a9c7624c3421c3944a602265c96eb3d85681`.
- SW_RACER_RE [`swrModel.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrModel.c), revision `258f67aa858ba2e281ce8a6791e49c554b85fae0`, blob `63a97f70cbbf67a37f5aafd9eaa337dbdf0b023d`.

### 1. Block directory and model-span interpretation

The Steam loader reads the model count from the start of the model block, then reads three adjacent 32-bit offsets at `8 * model_id + 4`:
- mask start;
- model data start;
- following boundary, used as the end of this model span.

It derives `mask_size = model_start - mask_start` and `model_size = following_boundary - model_start`. The mask is read to a separate fixed workspace and byte-swapped word-by-word before use. The model record itself is 8-byte aligned in the asset arena.

This is direct PC export evidence for the loader's local offset arithmetic. Do not generalize the apparent directory layout to GameCube/Wii or assume the same block layout in another PC release without a matching target sample.

### 2. Compressed and uncompressed model paths converge on a size-aware fix-up pass

The loader checks the first model word for the `Comp` tag. In the compressed branch, header word 2 supplies the declared decompressed byte count; the compressed payload is copied into a separate high-end arena region, decompressed into the low-end model region, and the asset cursor is advanced by the declared decompressed size. The uncompressed branch reads the full stored model span and advances by that span.

The Steam export keeps a working size value consistent with the actual in-memory model extent:
- compressed branch: the value is overwritten with the header's decompressed byte count;
- uncompressed branch: it remains the stored model span.

The same value bounds the subsequent pointer-fixup loop in 32-bit words.

### 3. The pointer mask distinguishes relocatable addresses from texture references

For each 32-bit word marked by the mask:
1. The loader byte-swaps the word into host order.
2. A value with the texture-reference tag (high byte `0x0A`) is passed to the texture/material loader, which writes the resulting resource references into the model data.
3. Any other nonzero marked value is treated as a model-relative pointer and rebased by adding the loaded model base address.
4. Zero remains zero.

After this relocation pass, Steam calls `FUN_004485D0`:
- it byte-swaps the root model tag;
- walks the root node-entry list until the `0xFFFFFFFF` sentinel and byte-swaps each non-null node;
- processes an optional `Data` section, including its word count and payload words;
- processes an optional `Anim` section by walking animation references until a zero entry;
- processes the optional `AltN` section, with additional alternate-node fix-ups for the `MAlt` root type.

This establishes a two-stage loader boundary: **mask-driven pointer/resource relocation first, structured node/data/animation byte-swapping second**. It is not simply a decompression routine.

### 4. Cross-snapshot discrepancy: compressed-size versus decompressed-size loop bound

The Steam-PC `FUN_00448780` assigns the header's decompressed size to its working size value in the `Comp` branch; the relocation loop then iterates over that value divided by four. For an uncompressed model, the same working value remains the stored model span, which is appropriate for that path.

In the pinned SW_RACER_RE `swrModel_LoadFromId`, the compressed branch calculates `decompressed_size` and uses it to advance the asset cursor, but the later mask relocation loop is written as `i < model_size / 4`. Here `model_size` was calculated from the stored block boundaries before the compression check. If a compressed record has a stored span smaller than its decompressed size, SWR's loop would examine fewer words than the Steam-PC loop.

**Classification: cross-snapshot source discrepancy / candidate reconstruction defect, not confirmed retail bug.** The snapshots are not proven to be the same executable build, and no matching lawful compressed model fixture was used to exercise this condition. Before changing or adapting anything, verify the expected relationship between mask bit count, stored span and decompressed size using an independently generated non-proprietary fixture or an owner-held lawful test input. Do not silently patch the third-party AGPL reference or copy its implementation into Boonta.

### 5. What this adds to the clean-room architecture

A future independently written loader needs explicit stages and error boundaries:
- validate block directory offsets and monotonic spans before subtracting;
- validate mask length against the number of words in the decompressed model;
- validate compressed input length, output capacity, and decoded byte count;
- perform tagged texture-reference resolution and relative-pointer relocation in a bounded pass;
- parse and byte-swap root nodes, data, animations and alternate nodes only after relocation succeeds;
- unwind all arena/resource allocations on any failure.

These are architecture requirements derived from PC reference behavior and memory-safety analysis. They are **not** a claim about the native GameCube/Wii model format or an implementation request until target evidence exists.

No source code, game model, compressed game block, ROM, DOL/REL, disc image, BIOS or extracted asset was copied or committed.


### 6. Texture-reference cache and animation registration continuation

The texture-marker branch is not an opaque generic pointer fix-up. Steam-PC `FUN_00447490` (revision `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`, blob `5b8382eb7d221aae55e650c2043e6071f96ade8b`) performs a resource lookup:
- invalid or out-of-range texture IDs clear both output references;
- a populated cache entry supplies the cached pair of references;
- otherwise it reads the corresponding three-offset record from the texture block, passes it through the texture-data/material creation helpers, and stores the resulting reference pair in the cache;
- a small set of hard-coded texture IDs also update dedicated global references or invoke a special post-load helper.

This confirms the `0x0A` model-word tag is a texture/resource lookup path with caching, not a model-relative address.

After model parsing, Steam-PC `FUN_00448bd0` (same revision, blob `4540a9c7624c3421c3944a602265c96eb3d85681`) walks past the root entry list and any optional `Data` section. If the next section is `Anim`, it iterates the animation references until a zero entry, calls the animation loader for each and tracks the earliest animation start value to update shared animation-buffer timing offsets. The preceding `FUN_004485d0` / `FUN_00448180` pass performs the structure-specific byte swaps for the animation records and their track payloads.

This adds an explicit dependency chain after decompression:
**model bytes → mask relocation → texture-ID cache resolution → root/node/data/animation byte-swap → animation registration/timing bookkeeping**.

The exact resource IDs, cache capacity, texture payload format and console-specific equivalent remain outside the evidence established here. No texture or animation asset was extracted or committed.


## 2026-11-04 — PC pod update callbacks and the per-frame simulation pipeline

This addendum follows the PC pod object through its recovered event callbacks. It is a **Windows-PC comparative map**, assembled from two separately pinned public code snapshots. It does not establish identical executable builds, runtime behavior, or GameCube/Wii parity.

### Pinned sources and evidence boundary

- SW_RACER_RE source/reconstruction: [revision `258f67aa858ba2e281ce8a6791e49c554b85fae0`](https://github.com/tim-tim707/SW_RACER_RE/tree/258f67aa858ba2e281ce8a6791e49c554b85fae0), declared AGPL-3.0; read-only reference.
- Separate Steam-PC Ghidra export: [revision `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef). Its executable identity is not proven to match the SW_RACER_RE snapshot.
- Evidence class: **PC CODE / cross-snapshot address correspondence**. No source code was copied, no binaries or proprietary data were used, and no external project was built or run.

### 1. The object dispatcher exposes four distinct per-frame phases

The SW_RACER_RE event-table reconstruction associates the `Test` object with:
- F0: `swrObjTest_F0` at `0x0046D170`;
- F1: `swrObjTest_UpdateControlAndMove` at `0x0047AB40`;
- F2: `swrObjTest_UpdatePhysicsContact` at `0x0047B520`;
- F3: `swrObjTest_F3` at `0x00470610`.

The reconstructed dispatch table is recorded in [`swrEvent.h` lines 12–24](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrEvent.h#L12-L24). The four corresponding SWR function bodies are still `HANG("TODO")` stubs in [`swrObj.c` around lines 2355–2479](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L2355-L2479). The dispatch table itself is inside a disabled reconstruction block; treat it as a recovered callback map, not as a compiled definition in this source snapshot.

The Steam-PC export contains bodies at the same four numeric addresses. This is a useful cross-reference, but the matching addresses do **not** prove that both projects describe the same executable build.

### 2. F0 — control selection and target preparation

Steam-PC [`FUN_0046D170.c` lines 103–120](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0046d170.c#L103-L120) calls `FUN_0046CF00` after updating several per-pod flags and state fields.

The SWR snapshot identifies address `0x0046CF00` as `swrRace_CalcTargetTurnRate` ([`swrRace.c` lines 3215 onward](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L3215-L3270)). That routine dispatches among local-human input, remote-player state and AI autopilot. For active racers it also updates catch-up/speed multipliers, applies repair/proximity behavior where appropriate, and clamps the target turn rate to pod statistics. The local control reader maps steering, pitch, throttle, brake, boost, slide, repair and taunt actions; engine damage can add steering pull and force feedback ([`swrRace_UpdatePlayerControl`, lines 2783 onward](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L2783-L2935)).

The remaining F0 helper calls at `0x0046D040` and `0x0046D100` are not assigned stronger semantics here. This is a control/flag preamble map, not a complete F0 reconstruction.

### 3. F1 — orientation, steering and translation

Steam-PC [`FUN_0047AB40.c` line 114](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ab40.c#L114) calls `FUN_00478D80` after preparing the current/previous transform, turn integration and orientation-dependent vectors. SWR labels `0x00478D80` as `swrRace_IntegrateMotion`.

The SWR helper call chain is now readable:
- `swrRace_UpdateSpeed` (`0x004783E0)): advances the throttle accumulator, maps it through pod acceleration/max-speed statistics, then applies air-brake and surface speed effects ([source](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L4242-L4331)).
- `swrRace_ApplyBoost` (`0x004787F0)): charges boost while enabled, decays stored boost when released, returns a bounded boost-thrust term and cancels boost under air-brake ([source](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L4594-L4625)).
- `swrRace_ApplyTraction` (`0x00478A70)): blends the velocity direction against the desired movement direction using pod grip, surface grip and slide state ([source](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L4378-L4496)).
- `swrRace_IntegrateMotion` (`0x00478D80)): combines speed/boost/traction with opponent-collision and slope velocity, advances the position by the frame delta, then performs up to six swept track-collision correction passes ([source](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L4499-L4590)).

This gives a concrete **helper pipeline** for the movement portion of the PC reference. It does not recover the entire F1 callback or establish equivalent GameCube/Wii physics.

### 4. F2 — contact, heat, orientation and surface state

Steam-PC [`FUN_0047B520.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047b520.c) exposes a different stage:
- line 37: `FUN_0047B0C0`, the SWR-named `swrRace_ResolvePodCollision`;
- lines 39 and 43: `FUN_00479E10` or `FUN_0047A200`, mapped by SWR to ground-contact or wall-contact handling;
- line 105: `FUN_004788C0`, the heat/engine-damage update;
- lines 117 and 120: `FUN_00477C30` or `FUN_0047A610`, mapped to orientation integration or spline-orientation update;
- line 122: `FUN_00476EA0`, mapped to surface-tag refresh.

The heat routine [`swrRace_UpdateHeat`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L4333-L4377) distinguishes lava drain, boost heat loss and idle cooling. When the stored heat bottoms out, it chooses an engine part, marks damage and clears the boosting flag. The F2 caller also performs later damage/surface/orientation work; its full dependency order needs more caller-level reconstruction before a port is specified.

### 5. F3 — model and presentation maintenance

Steam-PC [`FUN_00470610.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00470610.c) calls the SWR-mapped model/effects helpers:
- `0x0046D4C0`: reset model-node flags;
- `0x00470AE0`: pod engine animation;
- `0x004709A0`: reflection-node update;
- `0x00470A40`: engine-sound update.

This is evidence of a dedicated model/presentation phase after movement and contact handling. It is not a complete renderer or asset pipeline.

### 6. Updated architecture implication and unresolved edges

The PC evidence now supports a useful high-level separation:

`F0 control/target selection → F1 movement integration → F2 contact/heat/orientation/surface → F3 model/effects/audio maintenance`

This is a **PC reference ordering only**. Remaining gaps:
- SWR's public F0/F1/F2/F3 bodies remain TODO stubs; Steam supplies the comparative bodies, not proof of the SWR executable identity.
- F0's two remaining helper calls and several F2/F3 side effects still need semantic classification.
- Exact callback scheduling order, re-entry behavior, frame-delta semantics and runtime effects have not been observed in the original PC game here.
- None of these PC functions or field layouts is evidence of GameCube/Wii internals. Native target porting remains blocked on target-specific evidence and the separate clean-room design.

**Next highest-value research question:** identify the Steam-PC caller/dispatcher that schedules the four `Test` callbacks and establish whether F0→F1→F2→F3 is the observed per-frame order, then trace the F2 contact/ground/wall branch conditions and the inputs consumed by each. Keep unknown helper names and target-platform behavior explicitly unresolved.

No implementation code was added, no third-party code was copied, and no game-derived asset, ROM, DOL/REL, disc image, BIOS, IDB or proprietary executable was read or committed.


## 2026-11-04 — dispatcher-level ordering of the four pod update phases

The callback-map addendum above can now be extended from address correspondence to the per-frame event-manager dispatch structure.

### What the pinned PC reconstruction establishes

1. The SWR main header describes `swrMain_RunFrame` phase 1 as the world update: model animation, event callbacks F0–F3, then viewport-camera update, gated by the pause state ([`swrMain.h` lines 36–40](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Main/swrMain.h#L36-L40)).
2. The four SWR dispatchers are separate functions at `0x004508B0`, `0x00450930`, `0x004509B0` and `0x00450A30`. Each walks the event-manager table, then iterates the objects of each manager and invokes that manager's matching callback ([`swrEvent.c` lines 48–128](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrEvent.c#L48-L128)).
3. The fixed-timestep hook/replacement in [`swrMain_delta.cpp` lines 115–134](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/dinput_hook/game_deltas/swrMain_delta.cpp#L115-L134) places the world tick calls in this explicit order: model-animation update → CallAllF0 → CallAllF1 → CallAllF2 → CallAllF3.

This demonstrates a **phase-barrier architecture** in the recovered PC update path: all eligible F0 callbacks run before the global F1 pass begins; all F1 callbacks run before F2; and all F2 callbacks run before F3. It is not accurately described as one pod running F0, F1, F2 and F3 to completion before the next pod begins.

### Dispatch filters visible in the event loops

- F0, F1 and F2 require a non-null callback and a manager whose flags do not intersect `swrEvent_f0SkipMask`; each individual object is called only when `(obj->flags & 0x1100) == 0`.
- F3 also checks for a non-null callback and the per-object `0x1100` mask, but its reconstructed loop does not apply the manager-level `swrEvent_f0SkipMask` condition.
- The dispatcher iterates object arrays by each manager's declared `size` and `count`. The order is the event-manager table order followed by object order within each manager, not a separately sorted global list.

These conditions are direct reads of the pinned reconstructed C, not a complete semantic explanation of each flag. The flags' full meanings and any effects of mutation/deletion during callbacks remain outside this bounded trace.

### Important limitation

The stock `swrMain_RunFrame` body is absent from the inspected SWR C file, but a subsequent read-only audit recovered its corresponding frame routine in the separately pinned Steam-PC Ghidra export as `FUN_00445980`. The correction is documented below. The fixed-timestep hook remains supplemental reconstruction evidence, not a substitute for the Steam-PC function body or runtime validation. The Steam-PC and SWR snapshots remain separate builds with no verified executable-identity link.

No callback sequence or flag behavior is promoted to GameCube/Wii. The native target still requires its own platform-specific evidence.



## 2026-11-04 — direct Steam-PC recovery of the stock frame scheduler

A further source check located the Steam-PC function corresponding to SWR's `swrMain_RunFrame` address. This supersedes the earlier statement that only the hook and SWR header exposed the order.

**Pinned source:** [Steam-PC `FUN_00445980.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00445980.c), revision `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`. SWR maps `swrMain_RunFrame_ADDR` to the same numeric address `0x00445980` in [`swrMain.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Main/swrMain.h). This is PC cross-snapshot correspondence, not proof the executable builds are identical.

### Direct call sequence in Steam-PC code

When `param_2` is 1 or 0, `FUN_00445980` enters its world-update phase. It calls several pre/post helpers, then:
1. Calls `FUN_00445690()`, which returns global state `DAT_0050C5F0`.
2. When that return value is zero, it calls `FUN_00426660` — mapped by SWR to `swrModel_UpdateAnimations` — then:
   - `FUN_004508B0`: global F0 dispatch;
   - `FUN_004270C0`: conditional helper;
   - `FUN_00450930`: global F1 dispatch;
   - `FUN_004509B0`: global F2 dispatch;
   - `FUN_004270C0`: same conditional helper again;
   - `FUN_00450A30`: global F3 dispatch;
   - `FUN_00429540`: mapped by SWR to `swrViewport_UpdateCameras`.
3. When `FUN_00445690()` is nonzero, it calls `FUN_00445860` instead of the active object-update chain.
4. The routine then runs another `FUN_004270C0` call before leaving the simulation phase.

This direct body confirms the central **global phase barrier** and adds the previously missing placement of model-animation update before F0 and camera update after F3. The exact role of `FUN_004270C0` remains UNKNOWN; its visible body conditionally calls `FUN_00426910` when `DAT_0050C68C` is nonzero, and should not be renamed speculatively.

The routine's second branch runs when `param_2` is 2 or 0 and contains a separate rendering path. Its helper names and exact rendering responsibilities remain unassigned here. The SWR header describes phase 1 as world update and phase 2 as render, which is consistent with this Steam-PC body.

### Pause/state gate — narrow conclusion only

The state gate reads `DAT_0050C5F0`; it does not directly read a boolean pause flag in the recovered body. The SWR header characterizes the world-update phase as pause-gated. Steam-PC `FUN_00445860` contains transitions involving state values 2 and 3 and calls judge/pause-related functions, but the complete enum and state ownership are not yet established. The safe conclusion is: **the active F0–F3 update chain is selected only when the queried state equals zero; a separate state-update path runs otherwise**. Do not infer the full pause-menu state machine from these values.

### Evidence status and boundary update

- **CONFIRMED-IN-CODE / Steam-PC snapshot:** `FUN_00445980` contains the scheduler and the ordered F0–F3 calls.
- **CONFIRMED-IN-CODE / SWR reconstruction:** dispatcher addresses, per-object callback mapping and symbolic mappings for `swrModel_UpdateAnimations` (`0x00426660`) and `swrViewport_UpdateCameras` (`0x00429540`).
- **SUPPORTED cross-snapshot correspondence:** both projects map the frame scheduler and callback dispatchers to the same numeric addresses, but neither a verified executable checksum nor a same-build assertion has been established.
- **NOT CONFIRMED-IN-RUN:** no Steam-PC retail runtime trace or frame capture was produced by this analysis.
- **NOT ESTABLISHED:** no GameCube/Wii frame scheduler, update order, state layout or pause behavior is inferred.

No code was imported or changed; no commercial executable, ROM, disc image, DOL/REL, extracted asset or proprietary output was used.


## 2026-11-04 — state gate and pause-transition control path

The scheduler audit was extended to the state getter, its pre-update caller, and the transition routines. This yields a stronger interpretation of the nonzero-state branch, while keeping the original state enum unnamed.

### Direct control flow in the pinned Steam-PC export

- `FUN_00445980` calls `FUN_00445680` before reading the state getter `FUN_00445690`.
- `FUN_00445680` invokes `FUN_004457D0` when `DAT_0050C5F4 == 0`. `FUN_004457D0` only proceeds from `DAT_0050C5F0 == 0`; it checks the Judge object and the input/state conditions before calling `FUN_004456B0`.
- `FUN_004456B0`, when the same gate `DAT_0050C5F4 == 0) allows it, sets `DAT_0050C5F0 = 2`, broadcasts the four-character event tag `Paws` with parameter 1, and runs surrounding menu/audio helpers.
- On later nonzero-state frames, `FUN_00445860` advances the transition scalar. When state is 2 it increments toward 1 and then writes state 1; when state is 3 it decrements toward 0 and eventually calls `FUN_00445730`.
- `FUN_00445730` writes state 0 and broadcasts the same `Paws` event with parameter -1.
- `FUN_00445780` writes state 3. The pause/menu handler `FUN_0042AE00` calls it on input bit `0x200`; another menu-state helper `FUN_0042AB80` also uses it in selected transitions.

### Safe interpretation of the four observed values

The code supports this transition model:

| Value in `DAT_0050C5F0` | Observed transition behavior | Working interpretation |
|---:|---|---|
| 0 | Selects the F0–F3 active world-update chain | Active simulation |
| 2 | Set by the pause-entry routine; transition scalar moves toward the upper bound, then state becomes 1 | Entering pause |
| 1 | Stable target reached from state 2; the active F0–F3 chain remains bypassed | Paused/menu state |
| 3 | Set by the resume routine; transition scalar moves back toward the lower bound, then state becomes 0 | Leaving pause / resuming |

**Evidence classification:** SUPPORTED interpretation of state transitions from the pinned Steam-PC code; the numeric writes and comparisons are CONFIRMED-IN-CODE. The source does not expose a named enum for `DAT_0050C5F0`, so do not promote these working labels into official symbols. The independent `DAT_0050C5F4` gate also affects whether pause input/state changes are allowed; its full ownership and lifecycle remain UNKNOWN.

### The scheduler's repeated helper is not a timer

`FUN_004270C0` checks `DAT_0050C68C` and conditionally calls `FUN_00426910`. In the pinned export, `FUN_00426910` has an empty body that immediately returns. There is no visible timer, wait, sleep or delta-time update in this pair. Therefore the repeated call between dispatcher phases must remain an **effective no-op in this recovered snapshot**, not a guessed synchronization or frame-timing mechanism.

### Updated evidence boundary

This closes the bounded source-level state-gate question for the selected Steam-PC snapshot. It does not prove the exact transition animation, input-device mapping, retail runtime response, or same-build identity with SW_RACER_RE. The native GameCube/Wii implementation must not inherit this numeric state machine without target-specific evidence.


## 2026-11-04 — F2 contact dispatch: pod-vs-pod, ground raycast and ZON wall path

This is a bounded PC-only continuation of the pod F2 callback trace. It separates the collision stages and records the conditions visible in the pinned Steam-PC body, then compares them with the independently pinned SW_RACER_RE implementation where one exists.

### 1. F2 order: pod collision first, then one of two contact paths

Steam-PC `FUN_0047B520` calls `FUN_0047B0C0` before selecting a contact helper. It extracts bit 25 from the pod's flags0 word (`flags0 & 0x02000000`):
- bit clear: call `FUN_00479E10`, mapped in SWR to `swrRace_UpdateGroundContact`;
- bit set: call `FUN_0047A200`, mapped in SWR to `swrRace_UpdateWallContact`.

The bit is explicitly named `swrObjTest_FLAG0_ZON = 0x02000000` in [SWR `types_enums.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types_enums.h), described as zero-g/orbit. Thus the evidence supports a **normal-ground versus ZON/surface-contact dispatch**. The `UpdateWallContact` name is the SWR address mapping; it should not be mistaken for a fully recovered native GC/Wii function.

### 2. Pod-vs-pod collision is a separate pre-contact stage

Steam-PC `FUN_0047B0C0` (`swrRace_ResolvePodCollision` address) performs a proximity candidate query before ground/wall resolution:
- It is gated by `(flags0 & 0x6000) == 0` and `(flags1 & 0x02000000) == 0`. These masks are preserved as numeric conditions; their complete semantic names are not assigned here.
- It queries event type `Test`, excludes the current pod, passes squared-distance threshold `2500.0`, and requests up to four candidates.
- The common SWR event-query implementation sorts candidates in ascending squared distance. The Steam helper then uses candidate slot zero, so the nearest returned pod is the one considered by this response stage.
- It checks the candidate's corresponding flag masks again, computes a relative swept/approach quantity via helper `FUN_0047AEE0`, and requires additional separation/approach thresholds before applying a response.
- On acceptance, it adjusts both pod positions, adds collision-velocity components to both participants, runs the shared collision/death-speed helper and bleeds collision energy into each pod's state.

The distance argument is explicitly a *squared* distance in the SWR `swrEvent_FindNearestObjects` signature/implementation. A value of 2500 therefore corresponds to a 50-unit radius if the coordinate system uses the same linear game units. It is not a 2500-unit radius. The four-slot result capacity is not evidence that all four candidates are resolved in one call: this Steam body only reads slot zero.

Source boundaries:
- Steam-PC candidate resolver: [`FUN_0047B0C0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047b0c0.c).
- Steam-PC F2 caller and branch: [`FUN_0047B520.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047b520.c).
- SWR event-query implementation and sorted insertion: [`swrEvent.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrEvent.c).
- SWR address/symbol map: [`swrRace.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.h).

### 3. Normal ground-contact path: raycast, normal, slope, gravity, wall correction

The SWR source implements `swrRace_RaycastGround` and `swrRace_UpdateGroundContact` at the mapped address `0x00479E10`. The recovered steps are:

1. **Choose cast direction.** Normal mode uses `world_gravity`; magnet mode uses `-up`. The cast starts two units above the supplied position and has a long maximum range.
2. **Choose the ray query.** When `FULL_RAYCAST` is not set, it first tries the track mesh's fast `CollideRayWithMesh` query. A miss falls back to the general model raycast. In magnet mode, if the surface-relative cast misses, it retries along world gravity.
3. **Record hit/miss.** The hit node becomes `terrainModel`; the hit normal becomes the candidate up vector. A miss returns the sentinel distance 100000 and a world-up normal. The returned distance subtracts a two-unit skin.
4. **Control the full simulation region.** A fresh ground query runs for pods within approximately 1000 units of the nearest active camera, for the local human pod, or for `FORCE_GROUND` pods. The flat-surface cache can reuse the previous ground Z and up vector.
5. **Constrain magnet normal.** In magnet mode, `up.z` is clamped to at least 0.05 and renormalized, preventing an inverted/downward normal in this helper.
6. **Apply slope and gravity.** If the pod is not dead/respawning, slope steering may update the lateral/slope velocity. Magnet mode selects the magnet variant. Gravity is applied unless the pod is in the ZOFF transition.
7. **Resolve the movement against track geometry.** Non-local pods use `CollideBlockMove`. Local pods run `DetectWallScrape`, combine the immediate displacement with prior `wallPushback`, then call `ApplyWallCollision`. Flat-tagged terrain skips this wall/track correction branch.
8. **Update hover pads or invalidate stale samples.** The four pad samples are refreshed for nearby pods; beyond the update range they are explicitly marked as no-ground.
9. **Record ground distance.** The result is cached as `groundToPodMeasure`.

The LOD split matters architecturally: distant AI is not performing the same full raycast/contact workload as local/near-camera/force-ground pods. The distant fallback uses spline position for racing pods and marks a spline snap; it is not a full replacement for close-range terrain collision.

Relevant SWR source:
- [`swrRace_RaycastGround` / `swrRace_UpdateGroundContact`, lines 3685–3868](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L3685-L3868).
- [`swrRace_ApplyGravity`, lines 3409 onward](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L3409-L3490).
- [Ground-contact declaration and address](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.h).

### 4. Swept track collision is not the same as the pod-to-pod query

The SWR `swrRace_CollideTrack` implementation (`0x0044ACB0`) tests the entire segment from previous to current pod position:
- It computes the displacement and length.
- For a nontrivial segment, it casts a ray from the previous point along normalized displacement, limited to that segment length.
- On a hit, it pushes the proposed current point back out along the hit normal, adding a two-unit clearance skin.
- The motion integrator repeats this correction for up to six passes and records the resulting `wallPushback` delta.

The `swrRace_IntegrateMotion` caller skips this track collision when the pod is on a flat-tagged surface and avoids the expensive collision work for distant non-local pods unless forced to ground. AI acceleration is decelerated when repeated collision corrections occur. This is a separate track-mesh sweep from the F2 pod-to-pod resolver.

Source: [`swrRace_CollideTrack` and `swrRace_IntegrateMotion`, lines 4460–4591](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L4460-L4591).

### 5. ZON / wall-contact path: what is and is not recovered

The Steam-PC `FUN_0047A200` body confirms a distinct branch. It clears the airborne-like `flags1` bit `0x200`, then selects between:
- a near/local/ZOFF case, where the local human path runs `FUN_00477940` (mapped to `DetectWallScrape`) and `FUN_00479920` (mapped to `ApplyWallCollision`), while the non-local path runs `FUN_0044ABC0` (`CollideBlockMove`);
- a distant fallback that sets a world-up vector, supplies a default contact value and, for one racing state, marks a spline snap.

The SWR header maps these addresses and describes the wall branch, but the corresponding SWR `swrRace_UpdateWallContact`, `swrRace_DetectWallScrape` and `swrRace_ApplyWallCollision` bodies remain incomplete/TODO in the inspected source. Do not claim the full wall solver has been ported or recovered in SWR.

Steam reference:
- [`FUN_0047A200.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047a200.c).
- SWR address map: [`swrRace.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.h).
- SWR TODO helper declarations/bodies: [`swrRace.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L4850-L4868).

### 6. F2 reconstruction implications and open edges

The PC reference now supports three distinct collision/contact subsystems, in this order:
1. Pod-vs-pod proximity and pair response.
2. Contact dispatch: normal ground-raycast/contact when ZON is clear; wall/surface-contact path when ZON is set.
3. Position/velocity/contact-state bookkeeping, heat update, orientation update and surface-tag refresh.

The F2 routine derives a signed vertical/contact speed from the corrected position delta and the pod's up basis, then updates landing/death/contact state and proceeds to heat/orientation/surface behavior. The exact semantic name for every raw field/bit is not invented where no enum/structure annotation exists.

**Next highest-value research task:** finish the Steam-PC wall-contact path by tracing the internals of `FUN_00477940`, `FUN_00479920`, and `FUN_0044ABC0`; then compare their field writes against the SWR TODO signatures without importing source code. Keep the PC and native GameCube/Wii evidence separate.

No third-party source was copied into the repository; this addition is original analysis and citations only. No proprietary binary, ROM, DOL/REL, disc image, BIOS, model, texture or extracted game asset was used or committed.


## 2026-11-04 — Steam-PC internals of wall scrape, impact impulse and blocking move

This follow-up traces the three wall helpers called by the ZON contact path and distinguishes their roles. The Steam-PC export is the primary body evidence; the SWR header/types supply the cross-reconstruction names and field annotations.

### 1. `DetectWallScrape` — two scrape probes, spray condition, then blocking move

At Steam-PC address `0x00477940`, `FUN_00477940`:
- derives a live collision probe radius from the pod's collision-width field at `+0xA8), modified by the absolute tilt/manual-roll field at `+0x208), with a floor of 1.5;
- calls the collision-query helper `FUN_00444740` using the pod collision model and current movement data;
- when the first probe reports a hit, reads the collision-hit object and performs a second probe;
- only when one or two hits occurred, speed is above its threshold and the contact normal is sufficiently close to perpendicular to the pod-forward basis does it call `FUN_00477850` (mapped to `swrRace_SetupScrapeSpray`) to produce scrape spray;
- finally calls `FUN_0044ABC0` (`swrRace_CollideBlockMove`) so the proposed move can be rejected if the swept segment is blocked.

This is more specific than a single static side-ray: the probe radius is adjusted with pod tilt and collision response has a two-query path. The primitive inside `FUN_00444740` and its numeric thresholds are not renamed beyond the evidence in the decompilation.

Source: [Steam-PC `FUN_00477940.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00477940.c).

### 2. `ApplyWallCollision` — redirect velocity, set impact state and dispatch hit events

At `0x00479920`, Steam-PC `FUN_00479920`:
- computes the incoming vector's component along the supplied collision normal, removes that component to derive a deflected direction, and normalizes the result;
- calculates an impact-strength term from the incidence geometry and pod speed;
- adds a scaled collision impulse to the pod's `velocityCollision` vector at offset `+0x1D0);
- updates the turn-modifier field at `+0x1F4) from contact geometry (this is not the separate `contactSteerKick` field at `+0x1FC));
- when the impact exceeds the strong-hit threshold, clears `FLAG0_THROTTLE_SETTLED` and, when the pod is not in the excluded state mask, arms `wallHitCooldown` at `+0x264) for 0.1 seconds;
- for sufficiently strong/high-speed impact, scales down `accelThrust` at `+0x1A4), sets `FLAG0_WALL_IMPACT_CLAMP` (`0x40000)), and dispatches the `Hitt` sub-event through `swrEvent_CallF4`. The sub-event payload distinguishes a strong `KPow` response from directional side/front hit categories.

The SWR field map confirms `velocityCollision` at `0x1D0), `turnModifier` at `0x1F4), `contactSteerKick` at `0x1FC), and `wallHitCooldown` at `0x264). It names `FLAG0_WALL_IMPACT_CLAMP` as the one-shot bit consumed by F2 to clamp acceleration. This prevents a common field-offset mistake: the `+0x1F4) write is **not** the yaw-kick field at `+0x1FC).

Sources:
- Steam-PC [`FUN_00479920.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00479920.c).
- SWR [`swrRace` field layout, `types.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types.h#L501-L560).
- SWR [flag names, `types_enums.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types_enums.h#L150-L188).

### 3. `CollideBlockMove` — stop the proposed move on a swept hit

Steam-PC `FUN_0044ABC0` is materially different from `swrRace_CollideTrack`:
- computes the proposed segment `current - previous`;
- ignores segments below a small minimum length;
- normalizes the segment direction and scales the query range to a bounded probe distance;
- raycasts the collision model from the previous position along that direction;
- if the hit distance reaches the routine's collision threshold, returns a hit and copies the previous position back over the proposed current position.

This is a **blocking rollback** (snap to the previous point), not the normal-pushout correction performed by `CollideTrack`. The SWR header explicitly documents that distinction; the SWR body for `swrRace_CollideBlockMove` remains TODO.

Source: [Steam-PC `FUN_0044ABC0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0044abc0.c); SWR address/signature and contrast: [`swrRace.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.h).

### 4. Collision/contact graph after this trace

The current PC evidence supports the following distinct operations:

`F2 → ResolvePodCollision → (ZON ? UpdateWallContact : UpdateGroundContact)`

- Pod-pod response operates on a nearest candidate and updates both pods' position/velocity state.
- Normal ground contact uses ground raycasts, slope/gravity integration, local wall-scrape response or remote block-move rollback, and hover-pad sampling.
- ZON wall contact uses scrape probes, a normal-based impact response, collision impulse state and hit sub-events; the SWR wall helper bodies are still TODO.
- F1's swept `CollideTrack` remains a separate push-out solver applied after motion integration, with up to six correction passes.

This makes collision implementation planning more precise: do not collapse pod-pod, ground raycast, wall scrape, wall impact, block-move rollback and swept track push-out into one generic overlap solver.

### 5. Remaining unknowns and target-platform boundary

- Exact semantic names/units for the geometry thresholds in the Steam export remain unresolved.
- The `FUN_00444740` probe primitive has not been fully mapped to a named SWR API.
- The SWR wall scrape / ApplyWallCollision / CollideBlockMove bodies remain TODO; the names and type comments are useful maps, not executable implementations.
- Steam-PC and SWR snapshots are still not proven to be the same executable build.
- None of these PC field offsets, flags, event payloads or collision constants is evidence of GameCube/Wii behavior.

No source code was copied; this addition is original analysis of the pinned public reconstructions with provenance links only.


## 2026-11-04 — identify the wall-scrape probe primitive: swept sphere vs model

A targeted address lookup resolves the previously unnamed `FUN_00444740` helper called twice by `DetectWallScrape`.

### Direct Steam-PC wrapper sequence

The Steam-PC body at `0x00444740` is a short wrapper:
1. Return no hit if the model argument is null.
2. Call `FUN_00444200` to initialize the sphere-collision query state from the center, radius, velocity and two additional parameters.
3. Call `FUN_004440E0` to recursively traverse the supplied model hierarchy and test eligible mesh nodes.
4. Call `FUN_00444300` to resolve the sphere collision and populate the output fields.

The SWR model header independently maps those addresses as:
- `0x00444200` — `swrModel_SetupSphereCollision`;
- `0x004440E0` — `swrModel_CollideNodeRecursive`;
- `0x00444300` — `swrModel_ResolveSphereCollision`;
- `0x00444740` — `swrModel_CollideSphereWithModel`.

Its declared public signature takes a model node, sphere center, radius, velocity, two additional scalar parameters, output normal, an additional output and hit-distance output. The SWR header comments explicitly describe the pipeline as **setup → recursive model traversal → resolve** and call it a sphere sweep. The implementation body is not fully reimplemented in the inspected SWR C source; this is a symbol/signature cross-map, not a claim of a finished sphere solver.

### What this changes in the wall-scrape reconstruction

The two probes in Steam-PC `FUN_00477940` are therefore calls into a sphere-vs-model collision pipeline, not plain point rays. The enclosing routine computes a tilt-adjusted radius from the pod's collision-width field before issuing the probes. It tests two probe configurations and then applies the scrape-spray threshold logic. The exact meaning of the additional sweep parameters and the physical placement of each probe are still unresolved.

Sources:
- Steam-PC [`FUN_00444740.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444740.c).
- Steam-PC [`FUN_00444200.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444200.c), [`FUN_004440E0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004440e0.c), [`FUN_00444300.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444300.c).
- SWR [`swrModel.h` sphere-sweep addresses and signatures](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrModel.h).

**Evidence boundary:** Windows-PC code and SWR symbol/signature correspondence only. No identical-build assertion, runtime collision capture or GameCube/Wii claim is added.


## 2026-11-04 — sphere-sweep broadphase and face traversal

The collision query internals were followed one level deeper in the pinned Steam-PC export. This clarifies how the sphere probe reaches candidate mesh faces, without claiming the unresolved callback math is fully reconstructed.

### Query state setup

Steam-PC `FUN_00444200` writes global collision-query state before traversal:
- center coordinates from the supplied center;
- sphere radius and radius-squared;
- the supplied movement/velocity vector;
- projected lower/upper bounds computed from the center dot movement direction plus the two additional scalar parameters;
- collision mode value 3 and two callback function pointers (the Ghidra export labels them `LAB_004437C0` and `LAB_00443560`).

`FUN_00445150` resets a query counter and initializes four 4×4 matrix slots to identity, which are used as a transform stack during recursive node traversal. The meaning of every secondary global and callback is not assigned beyond its observed role.

### Recursive hierarchy and broadphase

- `FUN_004440E0` recursively walks the model hierarchy. For transformed nodes it composes/pushes node transforms, recurses eligible children, then restores the transform stack.
- When it reaches a mesh-node type value `0x3064`, it dispatches to `FUN_00443F10`.
- `FUN_00443F10` first transforms the query into the node's local context when needed. It builds a simple axis-aligned query bound from the sphere center ± radius, rejects nodes whose AABBs do not overlap that bound, then repeats the AABB check for child meshes before calling the face-level worker `FUN_004439F0`.
- `FUN_004439F0` obtains the mesh's stored face/vertex data and selects a callback according to the mesh's raw type value. The visible cases are values 3, 4, 5 and 7; the type-5/7 path iterates polygon fans as successive triangles. Since these are raw export values, they remain unnamed format categories here.
- `FUN_00444300` then resolves the aggregate query state and writes hit outputs (including normal and the saved query center/contact position) or reports no hit.

This establishes a standard two-stage structure: **hierarchical AABB broadphase → mesh-face narrowphase → final sphere-response pass**. It does not establish the exact triangle-sphere distance predicate inside the callback labels, because those callback bodies were not separately recovered in this pass.

### How this relates to the scrape probes

The wall-scrape path now has a bounded call graph:

`FUN_00477940` → `FUN_00444740` → `FUN_00444200` → `FUN_004440E0` → `FUN_00443F10` → `FUN_004439F0` → `FUN_00444300`

The outer scrape helper runs the sphere query twice with different output buffers. The collision model is traversed hierarchically and AABB-culled before face callbacks run. This explains why the two probes can be described as swept-sphere/model queries and why a single broadphase sphere can reject whole subtrees.

Steam-PC sources:
- [`FUN_00444200.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444200.c)
- [`FUN_00445150.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00445150.c)
- [`FUN_004440E0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004440e0.c)
- [`FUN_00443F10.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00443f10.c)
- [`FUN_004439F0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004439f0.c)
- [`FUN_00444300.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444300.c)

**Evidence boundary:** static code reading of the pinned Steam-PC export plus SWR's address/signature cross-map. Callback internals, exact sweep parameters, same-build identity, runtime behavior and GameCube/Wii parity remain unresolved.


## Sphere narrowphase dispatch and face-layout ABI — 2026-11-04

A deeper pass on the pinned Steam-PC export narrows what is known about the two callback pointers without pretending that their callback bodies have been recovered.

### Query setup and broadphase gate

`FUN_00444200` stores the two callback addresses in global slots:
- `DAT_00e98e20 = &LAB_004437C0`
- `DAT_00e985ac = &LAB_00443560`

The same setup stores the sphere center, radius and radius-squared, the supplied motion vector, and projected lower/upper bounds derived from the dot product of center and motion plus the two caller-supplied parameters. The transform-stack initializer remains `FUN_00445150`.

`FUN_00443F10` compares the query's center±radius bounds against the current model-node AABB. It then repeats the overlap test for each child mesh AABB and calls `FUN_004439F0` only for surviving mesh candidates. This is the concrete broadphase rejection point before the per-face callbacks.

### Two callback paths in the face dispatcher

`FUN_004439F0` obtains a raw mesh-type value, face count, a geometry-data pointer and an optional auxiliary pointer through the mesh accessors. The auxiliary pointer's null/non-null state selects which callback slot is used:

| Dispatcher condition | Callback slot | Observable argument pattern |
|---|---|---|
| Auxiliary pointer is null | `LAB_004437C0` via `DAT_00e98e20` | Receives per-record geometry pointers. Raw type 3 advances by `0x12` bytes; raw type 4 advances by `0x18` bytes. |
| Auxiliary pointer is non-null | `LAB_00443560` via `DAT_00e985ac` | Receives the common geometry base plus a small selector and an offset into the auxiliary data. Raw type 3 advances that auxiliary offset by 6 bytes per face; raw type 4 by 8 bytes per face. |

For raw types 5 and 7, the dispatcher reads per-polygon counts and emits successive triangle calls. The observed loop visits `n-2` triangles for a polygon with count `n`, alternates a 0/1 selector between successive triangles, and advances its flattened face-data cursor. In the auxiliary-pointer path, the per-triangle auxiliary offset advances in 2-byte units. These are raw layout/iteration observations only: the numeric mesh types are deliberately left unnamed, and no public semantic names are assigned to the selectors.

This establishes that the broadphase feeds two distinct face-data layouts into two callback ABIs. It does **not** establish the exact sphere/triangle predicate, the meaning of the selectors, the callbacks' return contract, or whether the 6/8/2-byte strides correspond to particular retail structure types.

### What remains unresolved

The pinned export's searchable function files expose the callback pointer assignments and their indirect invocation sites, but do not expose standalone bodies for `LAB_004437C0` or `LAB_00443560`. Searches for the callback labels and apparent function-name variants returned only the setup/dispatch references. The exact narrowphase math therefore remains **UNKNOWN**. `FUN_00444300` remains the final response/output stage; this pass does not reinterpret it as the face predicate.

Steam-PC source references at the pinned revision:
- [`FUN_00444200.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444200.c)
- [`FUN_00443F10.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00443f10.c)
- [`FUN_004439F0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004439f0.c)
- [`FUN_00443C50.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00443c50.c)
- [`FUN_00443E70.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00443e70.c)
- [`FUN_00444300.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444300.c)

**Evidence boundary:** static inspection of the pinned Windows-PC export only. The callback bodies, exact primitive semantics, executable identity with the separate SWR reconstruction, runtime behavior and GameCube/Wii parity remain unresolved. No game executable, ROM, disc image or extracted asset was accessed or added to the repository.


## Independent IDA name-map cross-check for collision callbacks — 2026-11-04

The separate, pinned IDA snapshot `everalert/swe1r-decomp@8d066b9c12ecb57bd819aaab586fd6bd2dd078a7` provides a useful address/name cross-check for the Steam-PC Ghidra trace:

| Address | Provisional IDA name | IDA function-table size |
|---|---|---:|
| `0x00443560` | `Unk_Model_MeshCollisionFaceCallback2Indexed` | `0x256` bytes |
| `0x004437C0` | `Unk_Model_MeshCollisionFaceCallback2` | `0x222` bytes |
| `0x00443110` | `Unk_Collision_IsInsideAABB4` | `0x26E` bytes |
| `0x00443380` | `Unk_Collision_IsInsideAABB3` | `0x1DA` bytes |

The provisional IDA names agree with the calling distinction observed in Steam-PC `FUN_004439F0`: the non-null auxiliary-data path dispatches to `0x00443560` and is labelled `Indexed`; the null-auxiliary-data path dispatches to `0x004437C0) and is labelled without that suffix. This independently strengthens the indexed/non-indexed interpretation of the two data layouts. The `Unk_` prefixes are retained: these are reverse-engineering labels, not official game symbols or verified semantic names.

The IDA name map also lists an earlier callback pair at `0x00442720` (`...CallbackIndexed`) and `0x00442C30` (`...Callback`). They are distinct function entries; this pass does not establish that the sphere query under study calls them, so they must not be conflated with the pair installed by `FUN_00444200`.

The Steam-PC bodies for `FUN_00443110` and `FUN_00443380` test the coordinates of four and three input points respectively against the current query center±radius bounds. The IDA labels describe them as 4-point and 3-point AABB helpers. Their direct caller relationship to either face callback is not established in the accessible source, so they are recorded as adjacent collision helpers, not asserted to be part of the callback body.

IDA references:
- [`idapro/names.txt`](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/names.txt)
- [`idapro/functions.txt`](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt)

Steam-PC code references:
- [`FUN_00443110.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00443110.c)
- [`FUN_00443380.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00443380.c)

**Evidence boundary:** the IDA artifact currently consulted supplies names and function-size metadata, not the callback machine-code bodies or semantic validation. The IDA and Steam-PC snapshots remain separately pinned; same-build identity, runtime behavior, exact primitive predicate and GameCube/Wii parity remain unproven.


## Collision query families: mode 1 ray traversal vs mode 3 sphere sweep — 2026-11-04

The separate IDA snapshot and Steam-PC call paths now support a clear split between two query families which share the same mesh-face enumerator but install different callback pairs.

### Mode 1: ray-style traversal

The Steam-PC entry points `FUN_00444D10` and `FUN_00444E40` initialize a query from an origin (`param_2[0..2]), direction (`param_2[3..5])) and maximum parameter/distance (`param_2[6])). Both set `DAT_00e98e1c = 1`, install:
- non-indexed callback pointer `DAT_00e98e20 = &LAB_00442C30`;
- indexed callback pointer `DAT_00e985ac = &LAB_00442720`;

and enter the recursive traversal `FUN_00444BF0`. `FUN_00444D10` returns the nearest accepted distance and writes hit position/normal outputs; `FUN_00444E40` returns the selected mesh/node reference when the supplied maximum is not exceeded. These are behavior summaries from their visible bodies; the IDA names remain provisional.

The recursive function `FUN_00444BF0` traverses model nodes and transform-bearing children, using the shared matrix stack (`FUN_00445200` push / `FUN_00445630` pop). Its leaf handler is `FUN_00444910`. When a transformed node is entered, that handler calls `FUN_004447B0` to transform the query's ray-list data into the current node space. It then derives per-axis bounds from the transformed start/end data, rejects non-overlapping node and child-mesh AABBs, and forwards surviving meshes to the common face enumerator `FUN_004439F0`.

A third mode-1 entry, `FUN_00444F10`, configures the same callback pair and query-state mode, derives axis bounds, applies type/filter flags, and invokes `FUN_004439F0` directly for its supplied mesh. Its wider caller contract is not assigned a more specific name here.

### Mode 3: sphere-sweep traversal

The wall-scrape query `FUN_00444740` calls `FUN_00444200`, then `FUN_004440E0`, then `FUN_00444300`. Setup sets `DAT_00e98e1c = 3` and installs:
- non-indexed callback pointer `DAT_00e98e20 = &LAB_004437C0`;
- indexed callback pointer `DAT_00e985ac = &LAB_00443560`.

The recursive node walker is `FUN_004440E0`, with leaf evaluator `FUN_00443F10`. Unlike mode 1's transformed ray bounds, mode 3's leaf check compares node and child-mesh AABBs with the query sphere's center±radius bounds before the common `FUN_004439F0` face dispatcher.

### Shared face enumeration, distinct callback ABI

Both families therefore share `FUN_004439F0` but not the callback pair:
- **Mode 1:** `LAB_00442C30` non-indexed / `LAB_00442720` indexed.
- **Mode 3:** `LAB_004437C0` non-indexed / `LAB_00443560` indexed.

The independent IDA name map provisionally labels mode-1 entries `Unk_Model_MeshCollisionFaceCallback` and `Unk_Model_MeshCollisionFaceCallbackIndexed`; mode-3 entries receive the corresponding `...Callback2` and `...Callback2Indexed` labels. This makes the separate callback families explicit, but the `Unk_` names remain analyst-generated, not official game symbols.

### Nearby geometric routines — relationship not established

Two other functions in this address neighborhood have meaningful bodies:
- `FUN_00442090` computes a closest contact candidate against a triangle-like three-vertex input: it tests a projected/interior candidate, falls back to closest points on the three edges when needed, compares squared separation against the global radius-squared threshold, and records the closest accepted contact. This is consistent with a sphere/triangle contact helper.
- `FUN_00442550` obtains a candidate point from the ray/plane helper `FUN_00442470`, checks whether that point lies in the supplied triangle via `FUN_00441040`, and updates the best distance/contact/normal when accepted.

These functions are recorded as nearby geometric routines only. The accessible decompiled callback bodies for `LAB_00442C30`, `LAB_00442720`, `LAB_004437C0` and `LAB_00443560` are still absent, so no direct call edge from a callback to `FUN_00442090` or `FUN_00442550` is claimed. The exact narrowphase wiring remains **UNKNOWN**.

Steam-PC references:
- [`FUN_00444D10.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444d10.c), [`FUN_00444E40.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444e40.c), [`FUN_00444F10.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444f10.c)
- [`FUN_00444BF0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444bf0.c), [`FUN_00444910.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00444910.c), [`FUN_004447B0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004447b0.c)
- [`FUN_00442090.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00442090.c), [`FUN_00442550.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00442550.c)
- [`FUN_004440E0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004440e0.c), [`FUN_00443F10.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00443f10.c), [`FUN_004439F0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004439f0.c)
- [IDA names](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/names.txt) and [IDA function table](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt)

**Evidence boundary:** Windows-PC static references only. Steam-PC Ghidra and IDA snapshots remain separately pinned; their executable/build identity is unproven. Callback machine-code bodies and exact call wiring remain unresolved. No runtime result, GameCube/Wii parity or proprietary game asset/binary access is claimed.


## Triangle narrowphase helpers: ray-plane and radius-contact cores — 2026-11-04

A further pass recovers meaningful geometric work in the shared collision code. These are direct function-to-function call relationships from the pinned Steam-PC decompilation. The exact indirect call edge from the installed face callbacks is still not present in the accessible C exports.

### Ray-style candidate: plane intersection plus triangle inclusion

`FUN_00442550` computes a ray/triangle candidate using:
1. a facing/filter decision from the triangle plane and two global filter flags (`DAT_004c1774`, `DAT_0050c5cc`);
2. `FUN_00442470`, which computes the ray/plane intersection parameter and candidate point, rejecting out-of-range or negative intersections;
3. a nearest-hit check against the current query distance `DAT_00e98258`;
4. `FUN_00441040`, which tests the candidate point against the triangle using its three edges.

On acceptance, it updates the best distance, contact position, collision/mesh reference (`DAT_00e98254`), and normal. In the reverse-facing branch it writes the negated query direction as the output normal. The two filter globals are configured in the mode-1 leaf path (`FUN_00444910`) and the direct mesh entry (`FUN_00444F10`), so this routine consumes the same ray-query filtering state. The available files do not show a direct call from `LAB_00442C30` or `LAB_00442720` to this helper; that last edge remains unverified.

### Radius-contact candidate: face projection and edge fallback

`FUN_00442090` uses `_DAT_00e98e6c`, the radius-squared value established by mode-3 sphere setup `FUN_00444200`. It:
- applies a plane-side test, with a special fallback gate;
- projects the query point against the triangle plane using `FUN_00480890`;
- rejects candidates whose squared separation exceeds the query radius squared;
- uses `FUN_00441040` for the face/interior test;
- when the projection is outside the triangle, calls `FUN_004808f0` for each of the three edges and keeps the nearest edge candidate;
- records optional contact points in a bounded debug/result buffer when the corresponding diagnostic flag is enabled.

When the accepted candidate is within the current best threshold and `DAT_00e98e1c == 3`, it directly calls `FUN_00441810` with the triangle, candidate contact and query direction. That explicit mode-3 branch is a strong link between this helper and the sphere-sweep family, but the public C export still does not show which installed face callback calls `FUN_00442090`.

### Mode-3 triangle clipping and contact reduction

`FUN_00441810` operates on the triangle's projection along the query direction and the interval `[DAT_00e98e00, DAT_00e9827c]`. It classifies the three vertices against the interval, computes edge/plane crossing points with `FUN_00441710`, and submits the resulting triangle fragments to `FUN_004414E0`.

`FUN_004414E0` computes closest-point candidates on each of its three edges using `FUN_004808F0`, selects the smallest squared separation, and forwards candidates within the current best threshold to `FUN_00441390`.

`FUN_00441390` is the shared result reducer: it updates the best distance, contact position, normal, source mesh/model reference and hit flag when the candidate is closer (or wins the tie-direction comparison). This explains how the clipped mode-3 path returns an ordinary collision result without assigning unverified semantics to the original callback labels.

### Evidence boundary and remaining gap

The bodies establish direct calls:
- `FUN_00442550` → `FUN_00442470`, `FUN_00441040`;
- `FUN_00442090` → `FUN_00480890`, `FUN_00441040`, `FUN_004808F0`, and conditionally `FUN_00441810` when mode is 3;
- `FUN_00441810` → `FUN_00441710`, `FUN_004414E0`;
- `FUN_004414E0` → `FUN_004808F0`, `FUN_00441390`.

What remains unknown is the final indirect edge from one of the four callback entry points to these helpers. The four callback bodies were not present in the fetched decompilation files, and guessed standalone `.c`/`.s` paths for them returned 404. Accordingly, the dossier does not claim that `FUN_00442550` is definitely invoked by the mode-1 callbacks or that `FUN_00442090` is definitely invoked by the mode-3 callbacks, even though their query-state use is consistent with those roles.

Steam-PC references:
- [`FUN_00442550.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00442550.c), [`FUN_00442470.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00442470.c)
- [`FUN_00442090.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00442090.c), [`FUN_00441810.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00441810.c)
- [`FUN_004414E0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004414e0.c), [`FUN_00441390.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00441390.c), [`FUN_00441040.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00441040.c)
- [`FUN_00441710.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00441710.c)

**Evidence boundary:** pinned Windows-PC static code only. The geometric helper links above are direct in the visible decompiled bodies; callback-to-helper linkage, same-build identity with the other PC snapshots, runtime behavior and GameCube/Wii parity remain UNKNOWN.


## SWR ray-callback implementation cross-check; sphere callback gap narrowed — 2026-11-04

This addendum corrects the earlier evidence boundary: **the Steam-PC Ghidra export does not expose standalone callback bodies, but the separately pinned SWR reconstruction does contain the complete mode-1 ray callback family.** This is a cross-snapshot comparison only; it does not prove the snapshots represent the same executable build.

### Mode 1 ray callbacks are present in SWR

At `tim-tim707/SW_RACER_RE@258f67aa858ba2e281ce8a6791e49c554b85fae0`, `src/Swr/swrModel.c` contains the following address-mapped implementations:

| Address | SWR source implementation | What the body establishes |
|---|---|---|
| `0x00442550` | `swrModel_CollideRayTriangle` (line 1921) | Front/back face acceptance, ray/plane intersection, nearest-distance rejection, point-in-triangle test, and recording the winning hit position/normal/node. Back-face hits reverse the reported normal. |
| `0x00442720` | `swrModel_MeshCollisionFaceCallbackIndexed` (line 1984) | Gathers 3/4 vertices via the index list, face-AABB rejects, computes triangle normal(s), then calls `swrModel_CollideRayTriangle`. |
| `0x00442C30` | `swrModel_MeshCollisionFaceCallback` (line 2015) | Same face tests for sequential/non-indexed vertex records. |
| `0x004439F0` | `swrModel_MeshIterateOverCollisionFaces` (line 2045) | Chooses indexed or sequential callback and iterates the mesh's primitive records. |
| `0x00444910` | `swrModel_CollideMeshNodeRay` (line 2228) | Transforms the ray when needed, performs node/child-mesh AABB rejection, enumerates faces and transforms accepted results back. |
| `0x00444BF0` | `swrModel_CollideNodeRecursiveRay` (line 2263) | Recurses the model tree and matrix stack, using the mesh-group leaf handler. |
| `0x00444F10` | `swrModel_CollideRayWithMesh` (line 2301) | Configures mode 1, ray data, callback pair and face acceptance, then returns the nearest hit and output point/normal. |

These bodies agree with the Steam-PC address map and the mode-1 setup/dispatcher pattern previously traced. The agreement supports the family-level mapping but does not establish an identical executable, compiler output, or byte-for-byte implementation between the two repositories.

### Primitive mapping now available as a reconstruction-side interpretation

The SWR `swrModel_MeshIterateOverCollisionFaces` implementation names raw mesh primitive types as follows:
- type 3: independent triangles;
- type 4: independent quads, split into two triangles for collision;
- types 5 and 7: triangle strips, emitting `n-2` triangles and alternating winding between successive faces.

For indexed meshes, the dispatcher reads indices; for sequential meshes, it advances directly through the vertex array. The Steam-PC export's raw types 3/4/5/7 and its observed `n-2` / alternating selector pattern are consistent with this interpretation. Label these as **SWR reconstruction mapping / cross-snapshot corroboration**, not as a separately verified Steam executable semantic enum.

### Mode 3 sphere callback family remains a source-reconstruction gap

The same SWR `swrModel.c` file contains no function definitions for:
- `swrModel_MeshCollisionFaceCallback2Indexed` (`0x00443560`);
- `swrModel_MeshCollisionFaceCallback2` (`0x004437C0`);
- `swrModel_CollideSphereTriangle` (`0x00442090`);
- `swrModel_SetupSphereCollision` (`0x00444200`);
- `swrModel_ResolveSphereCollision` (`0x00444300`);
- `swrModel_CollideSphereWithModel` (`0x00444740`).

The SWR `swrModel.h` does declare and address-map these entry points (including the two `Callback2` functions), but the code search and the inspected `swrModel.c` body do not provide their implementations. In the pinned Steam-PC Ghidra export, searches of `_text10.c`–`_text13.c` and attempted standalone function source/assembly paths also did not recover the mode-3 callback bodies. This is a bounded source-availability finding, not proof that no implementation exists in any uninspected file or other build.

Accordingly, the refined state is:
- **Mode 1 ray callbacks:** bodies available in SWR; Steam-PC call-path/addresses independently agree at the family level.
- **Mode 3 sphere callbacks:** addresses, indexed/non-indexed dispatch, broadphase, and adjacent sphere-contact helpers are recovered from Steam-PC; SWR header declarations and IDA names exist, but callback/setup/resolve implementations remain unavailable in the inspected reconstruction source.
- **Exact Steam callback-to-helper wiring for mode 3:** UNKNOWN.
- **Same-build identity and runtime parity:** UNKNOWN.

SWR references:
- [`swrModel.c` — ray triangle, callbacks, face enumerator and ray traversals](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrModel.c#L1921-L2345)
- [`swrModel.h` — address map and declarations for ray/sphere APIs](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrModel.h#L97-L121)
- [`swrModel.h` — callback and sphere API declarations](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrModel.h#L314-L345)

**License / reuse boundary:** SWR is used here as a read-only research reference. No source code or generated source has been copied into Boonta. Any future reuse requires a separate explicit compatibility and AGPL-3.0 review. The Boonta matrix records behavior, not a port.


## Wall-contact implementation gap map across Steam-PC and SWR — 2026-11-04

The mode-3 sphere-sweep gap is not an isolated collision primitive omission. The pinned SWR reconstruction also leaves most of the wall-contact chain unimplemented, while retaining a working ground/raycast path.

### Steam-PC wall-contact call path

The Steam-PC F2 update `FUN_0047B520` selects the wall-contact path `FUN_0047A200` when the relevant object flag is set; otherwise it calls the ground-contact path `FUN_00479E10`. In the wall-contact function:
- when its wall/flight condition and local-wall flag are satisfied, it calls `FUN_00477940` (wall scrape), computes the resulting wall delta from pushback plus the probe's movement delta, then calls `FUN_00479920` (wall collision response);
- the alternate blocking path calls `FUN_0044ABC0` (`CollideBlockMove`);
- other branches update vertical/spline-follow state and return a ground-distance value.

The scrape routine `FUN_00477940` computes a lean-adjusted sphere radius from collision width (`+0xA8)) with a minimum 1.5, performs up to two `FUN_00444740` sphere-vs-model probes, optionally emits scrape effects, then calls `FUN_0044ABC0` for the blocking move test. Thus the wall path depends on both the mode-3 sphere query and the block-move query; the later `FUN_00479920` routine applies the velocity/acceleration response.

The sibling ground path `FUN_00479E10` is a separate terrain-follow/ground-contact routine. This distinction matters: `FUN_0044ABC0` is not the same algorithm as `swrRace_CollideTrack`; the Steam body blocks/snaps the attempted move rather than doing the ray-based push-out used by the track collision routine.

### What SWR actually implements at the pinned revision

At `tim-tim707/SW_RACER_RE@258f67aa858ba2e281ce8a6791e49c554b85fae0`:

| Address / subsystem | SWR source state | Evidence in source |
|---|---|---|
| `0x0047A200` `swrRace_UpdateWallContact` | Declaration only; no body found in `swrRace.c` | `swrRace.h` declares the function and describes wall-scrape/collision-response versus terrain-follow dispatch. |
| `0x00477940` `swrRace_DetectWallScrape` | Explicit `HANG("TODO")` stub | `swrRace.c` line 4852. |
| `0x00479920` `swrRace_ApplyWallCollision` | Explicit `HANG("TODO")` stub | `swrRace.c` line 4858. |
| `0x0044ABC0` `swrRace_CollideBlockMove` | Explicit `HANG("TODO")` stub | `swrRace.c` line 4848. |
| `0x00444740` `swrModel_CollideSphereWithModel` | Address/declaration only in inspected SWR source | `swrModel.h` API declaration; no body in the inspected `swrModel.c`. |
| `0x00443560` / `0x004437C0` sphere face callbacks | Address/declaration only | `swrModel.h` declares the indexed/non-indexed `Callback2` pair; no body in the inspected `swrModel.c`. |
| `0x00479E10` `swrRace_UpdateGroundContact` | Body present | `swrRace.c` line 3758; includes terrain raycast/follow and ground/spline logic. |
| `0x0044ACB0` `swrRace_CollideTrack` | Body present | `swrRace.c` line 4461; swept ray segment then normal push-out with a 2-unit skin. |
| `0x00444910` / `0x00444BF0` ray mesh handler / recursive walker | Bodies present | `swrModel.c` lines 2228 and 2263; see preceding ray-callback addendum. |

The SWR source therefore has a usable raycast/ground-contact foundation but not the full wall-scrape, sphere-sweep, block-move and wall-response path that the PC trace exposes. This is a concrete reconstruction TODO/HANG inventory, not evidence that the retail program lacks those functions.

### Priority consequence

For a faithful independently implemented collision system, the next research/implementation specification should keep three separate contracts:
1. **Ground/surface following** — already has a reconstructed SWR body and raycast helpers; continue to distinguish its fast cached-mesh ray from full model raycast and spline fallback.
2. **Wall scrape / sphere sweep** — PC behavior is statically traced, but SWR's sphere setup, callbacks, face tests and resolve bodies remain unavailable in its inspected source.
3. **Blocking move / wall response** — PC `FUN_0044ABC0` and `FUN_00479920` are separate from the sphere query; SWR leaves their corresponding functions as HANG stubs.

Do not merge these into one generic “collision” routine or port PC/SWR code. The immediate highest-value reverse-engineering step is still to recover the missing mode-3 face callbacks and sphere result resolver from a verified PC disassembly/cross-reference, then separately specify block-move and wall-response acceptance behavior. No GC/Wii equivalent is known from these sources.

Steam-PC pinned references:
- [`FUN_0047B520.c` — F2 collision update](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047b520.c)
- [`FUN_0047A200.c` — wall/ground dispatch](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047a200.c)
- [`FUN_00477940.c` — wall scrape](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00477940.c)
- [`FUN_00479920.c` — wall response](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00479920.c)
- [`FUN_0044ABC0.c` — blocking move](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0044abc0.c)
- [`FUN_00479E10.c` — ground contact](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00479e10.c)

SWR pinned references:
- [`swrRace.c` — ground contact and HANG stubs](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L3758-L4866)
- [`swrRace.h` — wall-contact declaration](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.h#L539-L549)
- [`swrModel.h` — sphere and ray APIs](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrModel.h#L97-L121)

**Evidence boundary:** Steam-PC static decompilation plus separately pinned SWR source. Same-build identity, runtime behavior, and GameCube/Wii parity remain unproven. SWR is a read-only AGPL-3.0 research reference; no code was copied.


## Engine heat, failure, damage, repair and boost-charge state machine — 2026-11-04

This pass separates the thermal model, boost thrust, boost activation, engine failure damage and repair. Their SWR implementation coverage is not uniform.

### Implemented thermal and thrust pieces in SWR

The pinned SWR `swrRace.c` has bodies at the matching PC addresses:
- `swrRace_UpdateHeat` (`0x004788C0`, line 4333): temperature changes by `heatRate` while boosting, recovers by `coolRate) otherwise, and drains at 20 units/s on lava. At/below zero it selects one of six engine components, biased toward one side by manual tilt, spawns a fireball if that component was not already in failure state, sets `engineStatus[part] |= 8`, and clears the boosting flag. The gauge is clamped to 100 on the high side and zero on failure.
- `swrRace_ApplyBoost` (`0x004787F0`, line 4594): bleeds `boostValue` when not boosting, increases it by 1.5/s while boosting, cancels boost during air-brake, and returns boost thrust as `boostValue * boost_thrust / (boostValue + 0.33)).
- `swrRace_TakeDamage` (`0x00474CD0`, line 3266): refuses damage while invincible, dead/respawn-invincible or finished; cancels active boost; accumulates a per-engine health/damage value scaled by `damageImmunity`, caps it at 1.0, sets status bit 1, updates the worst-damage record and total damage.

The PC counterparts `FUN_004788C0`, `FUN_004787F0), and `FUN_00474CD0` use the same addresses/field offsets and materially matching operations in the pinned Steam-PC export. This is a strong address-level cross-check for these particular bodies, still not proof of same executable build.

### Engine-failure damage loop is a TODO in SWR

SWR `swrRace_ApplyEngineDamage` at `0x0046AA30` is an explicit `HANG("TODO")` stub (line 2759). The Steam-PC body `FUN_0046AA30`:
1. Iterates six engine-part records beginning at `player + 0x2A0), with a 4-byte stride.
2. For each record with status bit `0x8), samples the game RNG and calls `FUN_00474CD0(player, partIndex, randomScaledAmount * deltaTime)`.
3. Tracks whether any such part was present; if none, it takes a separate HUD/effect-flag path. If at least one was present, it enters a local UI/audio/effect branch.

The directly called damage helper `FUN_00474CD0` is the same-address SWR `swrRace_TakeDamage` routine described above. The thermal function's bit-8 write therefore feeds the per-frame failure-damage loop. The exact semantics of all HUD/audio globals in the no-failed-part and failed-part branches remain unresolved; they are not given speculative names here.

### Repair orchestration is also a TODO in SWR

SWR `swrRace_Repair` (`0x0046AB10`, line 2336) is a TODO stub, even though `swrRace_UpdatePlayerControl` calls both `swrRace_ApplyEngineDamage` and `swrRace_Repair` every frame (lines 3050–3051).

The PC body `FUN_0046AB10` shows that repair is not just a direct health reset:
- It advances a repair timer at `player + 0x2BC), with a short reset while the repairing flag is set.
- It walks six engine-part records at `+0x2A0), clears temporary status bits, selects an already-marked repair target or the most damaged component, and maintains per-part repair flags.
- It moves component damage/health toward the repaired state over time; a separate probability check may clear the component's bit-8 failure marker.
- It updates player-local repair audio/UI state, tracks damage on the left/right groups of three components, and invokes `FUN_004741D0` with a repair-side result when the repair timer permits.

Exact constants and the full event/audio meanings are preserved in the pinned source rather than guessed. The six-component grouping and the repair-side selection are visible; the detailed meaning of every temporary bit and global remains partially unresolved.

### Boost activation is distinct from boost thrust

SWR `swrRace_BoostCharge` (`0x0046BD20`, line 3871) is a TODO stub that returns `0`. It is called from `swrRace_UpdatePlayerControl` at line 2887. Later in that same input routine, the return value is combined with `FLAG0_CAN_CHARGE_BOOST`; only a nonzero result sets `FLAG0_BOOSTING` (lines 3158–3165). Therefore, in this reconstruction path, the current stub prevents this input-control code from latching a boost, even though `swrRace_ApplyBoost` can compute thrust once the flag is set.

The Steam-PC body `FUN_0046BD20` is a three-state gate using `player + 0x210` (states 0/1/2) and an elapsed-time field at `player + 0x214`. In outline:
- State 0 checks global timing/input conditions and arms state 1, clearing elapsed time.
- State 1 continues only while the conditions remain valid, increments the elapsed-time field by frame delta, and advances to state 2 after a fixed threshold.
- State 2 requires an additional integerized-input gate; when it passes, the function resets the state, emits a trigger/effect through `FUN_00426D10), and returns 1. Invalidated conditions reset the state.
- The exact meaning of all global input/timing predicates and the `__ftol()`-derived gate is not yet grounded, so they remain raw conditions rather than renamed controls.

### Completion status and priority

| Gameplay stage | Steam-PC source | SWR pinned source | Current gap |
|---|---|---|---|
| Heat accumulation / overheat selection | Body at `FUN_004788C0` | Implemented `swrRace_UpdateHeat` | Relatively low; cross-check confirms address-level behavior |
| Boost thrust calculation | Body at `FUN_004787F0` | Implemented `swrRace_ApplyBoost` | Relatively low |
| Boost activation gate | Body at `FUN_0046BD20` | TODO returns 0 | High; input path cannot latch boost through this result |
| Per-part failure damage | Body at `FUN_0046AA30` | HANG TODO | High |
| Underlying damage accumulator | Body at `FUN_00474CD0` | Implemented `swrRace_TakeDamage` | Lower; helper exists |
| Repair orchestration | Body at `FUN_0046AB10` | TODO | High |

Highest-value next step for this subsystem: recover and document the boost gate's exact external conditions and the six-engine repair/damage flags, then design independent tests for state transitions, damage accumulation, repair progression and overheat interruption. Do not copy the SWR or Steam implementation into Boonta; use these only as behavioral references. No GameCube/Wii parity is asserted.

Steam-PC references:
- [`FUN_0046BD20.c` — boost-charge state gate](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0046bd20.c)
- [`FUN_0046AA30.c` — per-part failure damage](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0046aa30.c)
- [`FUN_0046AB10.c` — repair orchestration](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0046ab10.c)
- [`FUN_00474CD0.c` — damage accumulator](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_00474cd0.c)
- [`FUN_004787F0.c` — boost thrust](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004787f0.c)
- [`FUN_004788C0.c` — heat/overheat](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_004788c0.c)

SWR pinned references:
- [`swrRace.c` — stubs and control caller](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L2336-L2375)
- [`swrRace.c` — boost-charge caller/latch and damage helper](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L2887-L3165)
- [`swrRace.c` — damage accumulator](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L3260-L3288)
- [`swrRace.c` — heat and boost thrust](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.c#L4333-L4618)
- [`swrRace.h` — address map](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrRace.h#L95-L121)

**Evidence boundary:** static code from separately pinned PC/SWR snapshots. The SWR and Steam code are not proven identical builds; no runtime confirmation or GameCube/Wii parity. No third-party code was copied.
