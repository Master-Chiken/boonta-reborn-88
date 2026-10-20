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


## Follow-up: race progress and standings inspected

Source: https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/Swr/swrObj.c

Static inspection of `swrRace_GetLapProgressIfAvailable`, `swrObjJdge_GetRacerProgress`, `swrObjJdge_GetRacerRankValue`, and `swrObjJdge_UpdateStandings` adds these specific observations:

- The lap-progress helper returns `-1.0` when there is no active race object or no first local player; otherwise it delegates to the local player's spline cursor progress.
- The standing-progress value combines completed laps with a current-lap fraction and applies a wrap correction around the start/finish boundary. Negative output is clamped to zero.
- A racer that is not marked finished is ranked by progress. A finished racer is initially ranked using `maxRaceTime - total_time`, then the standings pass normalizes finished entries back to progress for gap calculations.
- The standings pass resets position and AI-tether flags, assigns ranks, and records progress gaps to leader, local players, and pace-setter. The source comments identify `-100.0` as the no-local-player sentinel for player gap fields.
- The implementation shown uses a repeated maximum-selection pass rather than a library sort. Equal-rank/tie behavior should be tested rather than assumed.

### Boonta test candidates derived from this evidence

1. No active race / no local player: progress query must return an explicit unavailable state rather than accidentally report zero progress.
2. Start/finish wrap: just-before and just-after boundary samples must not produce a near-one-lap discontinuity.
3. Lap count plus fraction: same lap, different spline fractions; then adjacent lap with equivalent fractions.
4. Finished versus unfinished racers: verify final ordering and displayed gap remain coherent when finishers cross the line at different times.
5. Missing local player: gap display should not confuse the source's `-100.0` sentinel with a real distance.
6. Equal progress / equal finish-time edge cases: document tie behavior from a controlled test before choosing a Boonta rule.

These are **PC-source-derived test hypotheses**, not claims about N64/Dreamcast implementation. The next source pass remains focused on spline cursor updates and placement; then compare externally observable behavior on the console releases.


## Follow-up: spline progress and lap completion

Source: https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/Swr/swrRace.c

### Verified in the reconstructed PC source

- `swrRace_LapProgress` computes normalized progress from the current spline control point's baked base/span values plus `segmentT` times the span.
- For a closed-loop track, progress is clamped to `0.9999` instead of reaching `1.0`; the start/finish wrap is handled by the lap-completion logic. For an open point-to-point spline, progress may reach `1.0`.
- `swrRace_LapCompletion` uses previous/current progress and a high-water mark (`lapCompMax`) to detect forward crossing. Near the start/finish line it unwraps values around zero by subtracting one from high progress, so crossing the line can be tested without treating a backward snap as a valid lap.
- If the racer is dead, crossing checks are forced on. Remote racers use multiplayer progress arrays rather than the local spline cursor.
- `swrRace_UpdateRaceProgress` orchestrates cursor advance, current track-mesh lookup, sample-spacing/projection state, and lap-completion processing.

### Important holes in the reference

The same source marks several central routines as `HANG("TODO")`: `swrRace_AdvanceSplineCursor`, `swrRace_GetTrackMeshAtCursor`, `swrRace_UpdateSplineBinding`, and `swrRace_ComputeTrackOffset`. The comments give some intended semantics, but these bodies are not reconstructed here. The header separately documents `swrRace_UpdateSplineCursor` as advancing by speed or re-synchronizing from position and `swrRace_PlaceOnTrack` as initial placement, but the existence of those declarations does not supply their algorithms.

### More precise Boonta regression cases

- Closed-loop progress never returns exactly `1.0`; open-route progress can.
- Lap completion occurs on forward crossing, not merely because a pod's current progress is lower than its previous progress near wrap.
- Test crossing with previous progress around 0.8–1.0 and current progress around 0.0–0.1, plus a backward teleport/snap across the line.
- Test the dead-racer and remote-racer branches independently.
- Keep normalized spline progress separate from world-space distance; the PC source's standings gaps are expressed in lap units.

### Cross-platform limitation

These findings are specific to the inspected PC source. They do not prove that N64/Dreamcast use the same progress representation, control-point sampling, wrap thresholds, or multiplayer path. For console comparison, use controlled observations (lap counter, finish trigger, ranking and respawn behavior) tied to an identified release. No console ROM/disc data should be committed.


## Goal alignment — research must unblock the first complete race

The final goal is not to produce an endless archive of format notes. Boonta Reborn 88 aims to become an enhanced GameCube/Wii remaster/remake; the immediate proof point is **one complete, enjoyable three-lap race that can be driven manually, finishes correctly, resets, and starts again**. The broader vision (upgraded presentation, content and bonus modes) depends on this foundation.

### Why this source pass matters to that goal

Pinned PC reference:
https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c

The current PC source has a useful lap-progress model:
- `swrRace_LapProgress` combines a baked progress base/span for the current spline control point with `segmentT`.
- Closed tracks clamp progress below 1.0; open tracks can reach 1.0.
- `swrRace_LapCompletion` tracks previous and high-water progress, unwraps progress around the start/finish seam, suppresses a likely backward jump across the line, and has a distinct open-track completion rule.
- `swrRace_UpdateRaceProgress` sequences cursor advance, track-mesh lookup, spline projection/binding, track offset, lap completion and forward/backward checkpoint counters.
- `outCrossTime` is intended to locate the fraction of the frame before a start/finish crossing, so lap timing can be sub-frame accurate.

**Critical limit:** `swrRace_AdvanceSplineCursor`, `swrRace_GetTrackMeshAtCursor`, `swrRace_UpdateSplineBinding`, and `swrRace_ComputeTrackOffset` remain `HANG("TODO")` in this reconstructed PC source. Therefore the lap-completion logic is informative, but the full spline-following pipeline is not a finished, runnable oracle. Do not blindly port its logic or assume console versions use the same representation.

### Revised research priority

The asset-container/PC-N64-DC format question remains documented but is no longer the only focus. It should not delay the playable-race milestone unless asset loading is actually blocking it.

**Active research question:** what is the smallest evidence-backed race-progress/finish contract that Boonta needs to pass a manual three-lap race, and which parts are supported by the PC reference versus still unknown for N64/Dreamcast?

1. Map the current GameCube implementation and acceptance checks to PC source concepts: spline progress, start/finish crossing, lap timing, finish order, reset/restart.
2. Mark each behavior as **PC source-supported**, **console-unverified**, **Boonta currently implemented**, or **manually tested**. Never conflate these statuses.
3. Inspect N64/Dreamcast-specific source/evidence for differences where available; absent evidence stays unknown, not “same as PC”.
4. Only after the comparison, spend the remaining 20% on one bounded test/fix with regression coverage and visible Dolphin evidence. Do not make broad gameplay changes from source notes alone.

### Exit gate for this research thread

This thread is useful only if it produces a short acceptance matrix for: start, crossing the finish line once per lap, lap count, timing, finish placement, pause/resume, reset, and second race start. Every row must say PASS / FAIL / NOT TESTED and identify whether the evidence is automated, visible Dolphin, or physical hardware. The immediate milestone remains manual three-lap acceptance (issue #126); a build or headless test alone is not proof of a complete race.
