# PC source reverse-engineering pass — 2026-10-20

## Scope and evidence rules

This pass inspects public source/documentation in `tim-tim707/SW_RACER_RE`, a PC Windows reverse-engineering project. It is **not** a decompilation of the N64 or Dreamcast builds. Do not transfer PC-specific values, structure layouts, timings, or algorithms to consoles without independent corroboration.

No proprietary game binary, ROM, disc image, or extracted game asset is added to this repository. These notes contain source-level observations and links only.

## High-value source findings

### 1. Race progression and result handling are partially reconstructed

File: https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/Swr/swrRace.c

The reconstructed `swrRace_ResultsMenu` implementation documents a concrete sequence:
- sanitize out-of-range or negative total/lap times to the empty-record sentinel;
- sort racers by finishing-position field;
- find best lap times for local players;
- route an unlinked guest profile into record-name entry when it beats the record;
- update tournament progression/unlocks/prizes and autosave later in the results flow.

This is useful for defining regression cases in Boonta (invalid time rejection, ranking order, best-lap handling, local-player record comparisons, name-entry routing, save/progression boundaries). It is not evidence that console save structures or progression internals are byte-identical.

### 2. AI pace is described as player-relative rubber-banding

Source locations:
- `swrRace_AI` in https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/Swr/swrRace.c
- racer state fields in https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/types.h
- AI role flags in https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/types_enums.h
- per-track initialization `InitAISettingsForTrack` in https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/Swr/swrObj.c

The PC source comments describe three roles: a track-favorite simplified-AI pace-setter chases local player 1; one or two nearby AI racers can be tethered directly to local-player progress; the remaining field station-keeps behind the pace-setter. The key data include `gapToPacer`, `gapToLocalPlayer1`, `aiPaceOffsetTarget`, and the final `speedMultiplier` pacing path. Per-track setup seeds `swrRace_AILevel` and `ai_spread`.

Implication for Boonta: an AI system should be evaluated as a field-level pacing system, not only independent waypoint-following. Create deterministic tests for player ahead/behind, closest-AI tether assignment, pace-setter changes, and split-screen player-2 behavior. Do not copy undocumented constants from the PC source into console behavior without comparison.

### 3. Gameplay state flags expose testable behavior categories

File: https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/types_enums.h

The reconstructed PC flags name states for active racing/post-race, AI/simple AI, braking, repair, reset/respawn, death/spinout, tethered AI, spline teleport, wall-impact clamping, boost eligibility/boosting, airborne/grounded, terrain tags, finished state, and collision immunity. The comments also distinguish state-machine fields from independent bit flags.

Implication: Boonta can use these as a *candidate behavior checklist*, but should define its own portable state model rather than reproduce PC memory layout or bit values. Tests should cover legal state transitions and combinations, especially finished/dead/respawn, grounded/airborne, boost start/cancel, and wall-impact cooldown.

### 4. Track loading and spline/collision are separate research threads

The PC address map in `src/Swr/swrObj.h` identifies separate routines for:
- track models and track spline loading;
- starting-grid setup and racer spawning;
- spline-cursor initialization;
- per-track AI setup;
- race progress/standings;
- physics-contact update and turn/speed integration.

Useful index: https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/Swr/swrObj.h

Important limitation: the PC reconstructed `swrObjTest_UpdatePhysicsContact` is still marked `HANG("TODO")` in `src/Swr/swrObj.c`, even though its original address and callers are documented. Do not treat its physics implementation as reconstructed merely because a symbol exists. The PC project contains other hook/patch code around collisions, which must be separated from original-game behavior.

## Cross-platform comparison priority

The next useful step is to make a small evidence matrix, not start porting PC code:

| System | PC evidence now available | N64 / Dreamcast check needed |
|---|---|---|
| Race progression | Results sorting, record checks, tournament progression, save boundaries | Compare visible unlock/record rules; do not infer same save format |
| AI | Player-relative pacing/tether roles; per-track AI setup | Check whether same rubber-band pattern is observable in each console release |
| Track data | Distinct model/spline loading paths in PC symbols | Identify console archive/chunk formats and any platform-specific compression |
| Collision | Function boundary known; reconstructed PC contact function still TODO | Observe wall response, pod-to-pod collision, terrain reaction and recovery on each console |
| Timing/state | Named race/finish/boost/respawn flags in PC source | Compare gameplay timing only from matched builds or controlled observation |

## Source/license boundary

`SW_RACER_RE` declares AGPL-3.0. Keep it a read-only behavioral reference unless the project owners make an explicit licensing decision. Prefer independently implemented Boonta code based on documented behavior and controlled tests; do not copy code into Boonta without resolving license compatibility.

## Next action (one active task)

**Inspect the PC spline-following / progress routines only**: `swrRace_UpdateSplineCursor`, `swrRace_PlaceOnTrack`, `swrRace_GetLapProgressIfAvailable`, and `swrObjJdge_GetRacerProgress`. Record inputs, outputs, coordinate/progress conventions, and unknowns. After that, compare only externally observable progress behavior against identified N64 and Dreamcast releases. No implementation changes until that comparison reveals a specific Boonta mismatch.
