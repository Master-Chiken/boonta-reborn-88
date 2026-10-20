# RE-001 — Route/spline progression: PC reference vs current GameCube prototype

**Research date:** 2026-10-20  
**Status:** PC-source evidence recorded; current prototype mapped; Step 102 mapping **not verified**.  
**Scope limit:** This dossier investigates route representation and progress only. It does not determine the correct console implementation, prove the complete original-PC progress path is functional in this reconstruction, or approve any code/data import.

## The question

How does the reviewed SW_RACER_RE PC source represent a route position and advance along a spline, and how does that compare with the track-sampling and lap-progress model currently used by Boonta's clean-room GameCube prototype?

## Sources and revision

- **PC research source:** [SW_RACER_RE, commit `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab), specifically [swrSpline_LoadSpline](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L14-L78), [cursor branch stepping](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L180-L223), [cursor evaluation](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L245-L313), and [seek-to-progress](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L373-L410).
- **GameCube prototype:** `main` commit `fa8cee047ae8e74c30c87cd94977c434bb1c7398`, especially [track sampling and arc-length lookup](https://github.com/Master-Chiken/boonta-reborn-88/blob/fa8cee047ae8e74c30c87cd94977c434bb1c7398/gamecube-demo/source/main.c#L173-L240), [distance/lap update](https://github.com/Master-Chiken/boonta-reborn-88/blob/fa8cee047ae8e74c30c87cd94977c434bb1c7398/gamecube-demo/source/main.c#L1256-L1275), and [lap counter helper](https://github.com/Master-Chiken/boonta-reborn-88/blob/fa8cee047ae8e74c30c87cd94977c434bb1c7398/gamecube-demo/source/gameplay_state.h#L330-L377).
- **Upstream project description:** the SW_RACER_RE README says the project documents/re-implements selected functions to support modding; it explicitly does not aim for matching compilation or a complete decompilation. Its reported 71.2% function-analysis figure is dated 2026-06-12 and describes analysis coverage, not completed implementation. See the [upstream README](https://github.com/tim-tim707/SW_RACER_RE).

## Observed facts

### PC reference — linked spline cursor

1. **The loaded route is structured data, not only a list of positions.** `swrSpline_LoadSpline` opens a spline block, reads the spline count and offset bounds, rejects an out-of-range spline index, loads the selected block into an asset buffer, establishes a runtime control-point pointer, and converts selected multi-byte fields to the expected in-memory representation. The control points contain position/orientation/handle data and links such as `next1`/`next2`, plus connection counts.
2. **Progress can be translated into a cursor state.** `swrSpline_CursorSeekToProgress` uses `progress / 10` as a segment/node band and converts the remainder to a normalized segment parameter. Beyond the simple band range, it consults branch metadata (`unk_set`) and chooses a linked path through stored connection fields.
3. **The cursor can traverse the connection graph.** `swrSpline_CursorStep` examines the current lead node's connection count and the cursor's branch selector; it advances through the selected next node or marks a dead end. This is evidence of branch-capable traversal in this PC implementation.
4. **Position and orientation are sampled together.** `swrSpline_CursorEvaluate` advances the segment parameter by cursor velocity times the PC frame delta, moves across node links when the parameter crosses a segment boundary, clamps the parameter, and interpolates position, tangent and up direction. `swrSpline_EvaluateToMatrix` builds a coordinate basis from the tangent and up direction.
5. **A whole-track length is exposed.** `swrSpline_GetTrackLength` returns cached route length; `swrRace.c` uses this value to normalize at least some race/AI pacing parameters.
6. **The reconstructed PC lap-progress calculation uses spline progress, not simple distance division.** `swrRace_LapProgress` combines a control point's baked progress base with `segmentT` scaled by that segment's span. Closed tracks clamp at 0.9999 so the wrap can be detected; point-to-point tracks clamp at 1.0. See [swrRace_LapProgress and swrRace_LapCompletion](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c#L4663-L4740).
7. **Lap crossing compares normalized progress with a high-water mark.** Near the wrap, the logic can subtract 1.0 from progress above 0.8 so crossing the finish reads as overtaking a negative high-water value. For an open track, the helper reports completion at progress 1.0. This is source-level logic, not proof that the full race-progress path works end to end.
8. **The surrounding end-to-end progress path is unfinished in this reviewed reconstruction.** `swrRace_UpdateRaceProgress` calls `swrRace_AdvanceSplineCursor`, track-mesh lookup, spline binding/offset updates, and then lap completion. In this same revision, `swrRace_AdvanceSplineCursor`, `swrRace_GetTrackMeshAtCursor`, `swrRace_UpdateSplineBinding`, and `swrRace_ComputeTrackOffset` are `HANG("TODO")` stubs. See [the progress update path](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c#L4742-L4800). The reconstructed repository exposes useful lap-progress logic but does not supply a fully working reference implementation for route advancement.

### Additional PC detail — curve families, cursor state, and mesh mapping

The pinned source distinguishes three spline types in `src/types_enums.h`:

- `SPLINE_TYPE_BSPLINE = 0`: cubic B-spline interpolation over a four-node lookahead window. Position uses four control-point positions; the spline-type-specific basis also determines the tangent.
- `SPLINE_TYPE_BEZIER_FLAT = 1`: cubic Bezier interpolation from the start/end positions and their `handle2`/`handle1` control handles. Its up direction is fixed to +Z in the inspected interpolation routine.
- `SPLINE_TYPE_BEZIER = 2`: the Bezier position path with rotation/up information interpolated rather than the flat +Z special case.

These are directly visible in [the pinned spline type enum](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/types_enums.h) and [`swrSpline_Interpolate`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L86-L177). This is an important design distinction: the same cursor interface can evaluate curves whose control-point layout and orientation data differ. The current dossier does not identify which curve types appear in the retail GameCube version.

The source describes a cursor as a 0x30-byte state containing a spline pointer, velocity, normalized segment parameter `segmentT`, cached tangent length, four node-lookahead indices, start/end flags, a branch selector, and branch-history flags. `swrSpline_CursorEvaluate` advances the parameter by `velocity * swrRace_deltaTimeSecs`, repeatedly steps forward or backward when the parameter exits [0, 1], clamps at a path end, and evaluates position, tangent and up together. `swrSpline_CursorStep` selects a linked next node using the branch selector and available next-link count, while preserving enough branch bits to resolve later lookahead nodes. See [the cursor declaration notes](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.h) and [cursor stepping/evaluation](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L180-L313).

A second layer is intended to connect the route to the visible track: the comments in `swrSpline.h` describe a build pass that traces graph paths to create per-node normalized progress values and bakes ten cursor samples per node into a sample-to-track-mesh lookup. This must be treated as **documented intent, not fully verified executable behavior**: in the pinned revision, repository search did not locate function bodies for the declared `swrSpline_TraceProgress`, `swrSpline_BuildProgressTable` or `swrSpline_Build` routines, and the race-update path calls `HANG("TODO")` stubs for track-mesh lookup, cursor advancement and spline binding/offset updates. The data model is informative, but the reconstructed source does **not** provide a complete executable reference for the full pod-to-track progression path.

### Current GameCube prototype — closed curve and scalar distance

1. The runtime samples the checked-in generated test track through `track_sample_at`. It caches Euclidean straight-line distances between adjacent control points, wraps each point's successor with modulo point count, and uses those chord lengths to locate a parameter (t = target / segmentLength) for Catmull–Rom interpolation. This is a chord-based approximation to distance along the smoothed curve: the inspected function does not build an arc-length lookup table for the Catmull–Rom curve itself, so constant travelled-distance increments are not proven to yield constant physical distance on the smoothed curve. The runtime explicitly requires a closed-loop track with at least four points.
2. The race state keeps one scalar `g_distance`. Each active frame advances that distance using current speed, boost and pitch; it updates the lap count from the floor-divided previous/current distance against `RACE_LAP_DISTANCE`. The race finishes when the counter reaches the configured three-lap limit.
3. The distance-based lap helper is defensive around non-finite values, backward distance and overflow. Those are useful safety properties, but they are not evidence that the original game uses the same route model.

## Comparison

| Dimension | PC reference evidence | Current GameCube prototype | Confidence / limit |
|---|---|---|---|
| Route representation | Spline header plus control-point records, connection links and branch metadata | Authored point sequence sampled as a closed Catmull–Rom loop | High for these two codebases; no conclusion yet about Step 102 |
| Position along route | Cursor stores segment parameter/node lookahead and can traverse linked nodes | Scalar travelled distance selects a location on the closed curve | High for current source |
| Branch handling | The inspected PC cursor uses next-node connections and branch selection | The inspected prototype path has no equivalent spline-graph cursor in this path | High for the inspected functions; may not describe every subsystem |
| Orientation | Route position, tangent and up direction feed a matrix basis | Track frame is derived from nearby samples of the closed curve | High for inspected functions |
| Lap progression | `swrRace_LapProgress` / `swrRace_LapCompletion` use normalized spline progress, a high-water mark and wrap handling; the caller's route-advance path contains TODO/HANG stubs | Floor-divided travelled distance increments laps and ends after three laps | High for inspected code; full PC runtime path remains incomplete in this reconstruction, and console parity is unknown |
| GameCube/Wii parity | PC source only | Step 102 console candidate not mapped here | **Unknown** |

## Interpretation — what this tells us (and what it doesn't)

The prototype's current route is a compact, controllable test-course model. The PC reference contains a more explicit spline-cursor/connection-graph abstraction that can express branch choices and returns position/orientation as a route sample. Its reconstructed lap-progress helper uses normalized spline progress and a wrap/high-water comparison, while the prototype counts laps using travelled distance. The PC caller path is still incomplete because key movement/binding helpers are TODO/HANG stubs. These are materially different models.

That difference makes route/cursor mapping a high-value reverse-engineering question before a large implementation decision. It does **not** prove that the GameCube version uses the same graph layout, the same PC format, the same route data or the same lap-trigger logic. Nor does it prove that porting the PC design is automatically correct for GameCube. The original console candidate must be inspected before choosing an architecture.

## Step 102 mapping status

**Not verified in this pass.** The project register references a private `Star_Wars_Racer_GameCube_Step102.zip` candidate and a separate manifest, but those files were not available in the connected file workspace for this research pass, and they are not checked into the public repository. Therefore, no Step 102 filename/function is claimed as inspected.

The next Step 102 task is to inspect only the candidate source archive's route/race files and tests locally, match actual file contents to the PC observations above, and record each file's provenance/license status. Do not upload commercial game archives/ROMs/disc images or extracted assets to hosted tools; do not publish the Step 102 archive or bulk-import it.

## Next question (not active until RE-001 is reviewed)

After the route/cursor comparison is accepted, take a separate evidence block for **PC pod-control/traction**: trace how player input becomes target turn rate, how the target is capped by vehicle stats/pace, how current turn rate changes over delta time, and how traction blends desired velocity with current velocity. Then compare those responsibilities with the prototype's scalar lateral-velocity/damping helpers. Do not change those helpers until the comparison has a source-linked specification.

## Disposition

- [x] PC source functions inspected at the pinned revision.
- [x] Current prototype route sampling and lap counter mapped to exact source lines.
- [x] Facts separated from console hypotheses.
- [ ] Step 102 route/race source mapping — blocked until the private candidate source archive is available to inspect.
- [x] PC lap-progress / finish-crossing logic traced at function level.
- [ ] End-to-end PC route advancement proven; the required cursor/binding helpers are TODO/HANG stubs in the reviewed revision.
- [ ] Any implementation decision — deliberately deferred.

No game code or game assets were changed by this research item.