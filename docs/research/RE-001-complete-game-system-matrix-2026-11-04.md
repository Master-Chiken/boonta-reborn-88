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

5. **A separate post-race/camera/results code path exists.** F0 contains state-3 finish-hold, state-4 camera-sweep and state-5 results/taunt branches. The camera branch can set `swrRace_resultsScreenActive`, transition its low nibble to 5, change viewport/camera settings and send `Swee` to the `cMan` event group. `swrObjJdge_StartPostRaceSequence` also sends `Swee`, changes the racer low-nibble state to POSTRACE, enables UI input and adjusts music/HUD state. [StartPostRaceSequence and F0](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/Swr/swrObj.c#L615-L900)

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

- Its function inventory labels `0x0045E200` as `EntityJdgeCallback0x14` (size `0x74C`), `0x0045EA30` as `EntityJdgeCallback0x1C` (size `0x53E`), `0x0045DD80` as `Unk_Jdge_LoadFromRace` (size `0x254`), and `0x00457620` as `EntityHangCallback0x14` (size `0x468`). These addresses/lengths independently align with the Judge/Hangar callback roles already used in the SW_RACER_RE dossier; they do not establish identical PC executable builds. [IDA function table](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt#L1136) · [Judge entries](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab586fd6bd2dd078a7/idapro/functions.txt#L1187-L1196) · [IDA names](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab4bd4f5e4e2e2f8b9/idapro/names.txt#L1220)
- The same metadata project documents `Entity_CallAll0x14`: it iterates the entity-manager table, reads a callback pointer at manager offset `0x14`, then invokes that callback for each entity that passes its flag guard. Parallel wrappers exist for offsets `0x18`, `0x1C` and `0x20`. This structurally matches the SW_RACER_RE `swrEventManager` callback layout (`f0` at `0x14`, then `f1/f2/f3` at `0x18/0x1C/0x20`). [IDA callback iterator](https://github.com/everalert/swe1r-decomp/blob/8d066b9c12ecb57bd819aaab2dd078a7/idapro/src/4508B0_Entity_CallAll0x14.c#L3-L27) · [SW_RACER_RE event-manager layout](https://github.com/tim-tim707/SW_RACER_RE/blob/258f67aa858ba2e281ce8a6791e49c554b85fae0/src/types.h#L1084-L1125)
- This is **structural corroboration only**. The checked metadata does not show which precise entity-manager entries hold the Judge/Hangar callbacks in a race, the callback timing relative to `Fini`, or the native console behavior. It does not override the Steam snapshot's `NOT_INVOKED` graph markers for `FUN_00457620` and `FUN_0045DD80`.

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
