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

### Cross-check against the frozen Steam PC decompilation

**Additional reference found on 2026-10-20:** [`DeonPoncini/swep1r_decomp`](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef). Its README says it is a frozen Ghidra decompilation of the **Steam PC version**, retained as a reference for types, signatures and addresses. This is a different evidence source/build context from the pinned `SW_RACER_RE` revision. No root `LICENSE` file was found in the queried repository, so this is a **read-only analysis reference only**: do not copy or adapt its implementation into this project.

The useful discovery is that this snapshot contains function bodies for several addresses that remain `HANG("TODO")` in the reviewed `SW_RACER_RE` reconstruction:

- [`FUN_0047f6f0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f6f0.c) is the post-load spline builder. It checks the spline/control-point input, resets progress state where needed, calls the graph-progress builder with a `100.0` sampling parameter, then walks the spline again with a `10.0` sampling parameter to bake a spline-sample-to-track-mesh association. It optionally runs a validation pass.
- [`FUN_0047f470`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f470.c) initializes the per-node progress/order tables and enumerates connected control-point paths and branch choices. It dispatches each selected route path to the trace routine, rather than assuming the entire spline is one linear list.
- [`FUN_0047f060`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f060.c) repeatedly evaluates a spline cursor along a selected path and accumulates distances between evaluated positions. Those accumulated distances populate a per-node normalized progress base and a span for the segment parameter. This supports the conclusion that the PC progress table is intended to approximate arc length over the connected route, not simply divide the control-point index by node count.
- [`FUN_0047ee20`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ee20.c) walks the connected path and invokes a callback at the requested sample density; the builder passes `10.0` and a callback at `0x0047ea20` to bake the sampled-route-to-track-mesh lookup.
- [`FUN_0047f8e0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c) corresponds by address to `swrRace_AdvanceSplineCursor`. It moves the cursor's segment parameter (`segmentT`) in `0.01` increments/decrements while comparing the vehicle's current position with the spline frame's node plane. It emits forward/backward crossing flags and estimates the crossing fraction from the prior/current position's signed projections; when the projection delta is below `0.01`, the fraction is set to zero. This is more specific than a distance-only cursor advance.
- [`FUN_0047fbb0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c) corresponds by address to `swrRace_UpdateSplineBinding`. The refresh path requires both mesh references to be non-null and different, and a race-state bit to be clear; a separate mesh flag can reject the refresh. If the changed mesh stores a nonzero 16-bit spline-sample index at offset `+0x3c`, the code seeks the cursor to that value and invokes the crossing check before refreshing the mesh binding and associated projection state. The precise semantic names of these offsets remain unverified.
- [`FUN_0047fca0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c) corresponds by address to `swrRace_ComputeTrackOffset`. It projects the vehicle position relative to the cursor frame, measures a residual offset, and writes a normalized residual direction when its magnitude is greater than `0.1`; below that threshold it uses the fallback direction `(0, 0, 1)`. The exact semantic names of the result fields remain unverified.

#### Sampling density and callback boundary — additional verified detail

The frozen Steam PC snapshot allows the **sampling schedule** to be stated more precisely, while leaving one important callback detail unresolved:

- [`FUN_0047f6f0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f6f0.c) runs two separate passes: `FUN_0047f470(..., 100.0, ...)` to prepare route progress, then `FUN_0047ee20(..., 10.0, ..., &LAB_0047ea20)` for the sample-to-mesh pass.
- [`FUN_0047f060`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f060.c) advances the evaluated cursor in `1 / density` parameter increments and sums distances between consecutive 3D samples. With the builder's `100.0` density, this is an approximately 100-interval-per-segment chord-length approximation used to assign a progress base and segment span. It is not an analytic arc-length solution.
- [`FUN_0047ee20`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ee20.c) traverses candidate connected paths and their branch/lookahead choices; for each eligible segment it resets the segment parameter to 0 and calls the callback at `t = 0.0, 0.1, ... 0.9` before advancing to the next segment. In other words, `10.0` is **parameter-space density**, not a promise of equal world-space distance between samples.
- [`FUN_0047e8b0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047e8b0.c) independently uses the same progress-band structure: divide the progress value by 10 for the node band, use the remainder to derive `segmentT`, and consult stored branch metadata when the value falls outside the direct node-index range.

**Callback limit:** the builder passes the raw code label `0x0047ea20`, not a separately named `FUN_0047ea20` visible in the snapshot's function inventory. The reviewed decompiled sources expose the traversal and call contract, but not a clean, separately inspectable callback body under that name. Therefore the exact lookup-table population fields and the callback's individual writes remain **unverified**; the separate lookup reader is now mapped, but that does not reconstruct the table's write side. The defensible conclusion is the two-pass architecture and its sampling densities—not a fully reconstructed mesh-association structure.

#### Table initialization and route-order enumeration — new source evidence
#### Progress tracing across connected nodes — additional algorithm detail

A closer read of [`FUN_0047f470`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f470.c), [`FUN_0047f450`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f450.c), [`FUN_0047f060`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f060.c), and [`FUN_0044e5e0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0044e5e0.c) clarifies the graph-progress algorithm:

- `FUN_0044e5e0` searches the fixed-stride `0x54`-byte control-point records from a requested start index for a record whose 16-bit field at offset `+0x40` equals a supplied index/key. `FUN_0047f470` repeats that search over its route/order loop, while initially setting order slots to `0xFFFF` and progress bases to `-1.0`. The 16-bit field's game-semantic name is not recovered here.
- `FUN_0047f470` enumerates a start/control point's outgoing links and, for non-type-1 splines, expands additional connected-node/lookahead choices before invoking `FUN_0047f450`. `FUN_0047f450` is only a thin wrapper around `FUN_0047f060`; the latter is where distance sampling and progress values are calculated. The route enumeration is branch-aware and uses cursor branch bits; it is not simply one pass from point 0 through every record.
- For each eligible trace, `FUN_0047f060` samples the cursor at parameter increments of `1 / density`, accumulates the Euclidean distances between successive evaluated 3D positions, and follows node transitions until it reaches an endpoint/known progress anchor or returns to its starting node. The closed-loop return path sets the trace's terminal normalized progress to `1.0`; a path joining an already-established progress anchor can use that anchor's existing value. Exact behavior still depends on the branch-specific cursor state and global guard values in this frozen PC build.
- The trace then converts the sampled distance accumulated at each visited node into normalized node progress between the trace's start and terminal progress values, in proportion to the total sampled path distance. It records each node's progress base and writes its span as the difference to the next normalized base; the last traced span is the terminal progress minus that node's base. This is a chord-sum approximation over sampled curve positions, not analytic arc-length integration.

**What this resolves:** we now have a defensible description of how the PC progress base/span table is filled at a high level, including the closed-loop terminal value and reuse of an established progress anchor. **What remains unresolved:** the sample-to-mesh table's callback write side at `0x0047ea20`, the optional callback at `0x0047ece0`, several offset semantics, and all Step 102/GameCube parity. These functions come from the frozen Steam-PC decompilation, not a clean original source tree; treat the interpretation as a PC behavioral reference.


The related helpers expose more of the data layout even though neither callback body is recoverable from the checked-in per-function files:

- [`FUN_0047f470`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f470.c) initializes each control-point progress base to `-1.0` and its route-order entry to `0xFFFF`. It then enumerates candidate route starts/orders and follows connection choices, calling the trace helper for discovered paths. This is further evidence that the PC builder treats route order and progress as graph-derived tables, not as a simple sequential point count.
- [`FUN_0047f6c0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f6c0.c) clears ten 32-bit entries per selected control point at global address `0x00e23240` (`0x28` bytes per point), then zeros the corresponding progress-base slot at `0x00e22a60` and span slot at `0x00e22a64`. The spline builder calls this reset helper conditionally when a 16-bit per-point field is zero; that field's semantic name is not established, so do not interpret the condition more specifically.
- [`FUN_0047f060`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f060.c) accumulates distances between successive evaluated 3D positions along a traced path, then writes per-control-point normalized progress bases/spans and the route-order table. Together with the ten-slot reset and the already-mapped lookup reader, this narrows the storage layout: one ten-entry lookup block per control point and a separate base/span pair. It still does not tell us which mesh/segment value each callback writes to each slot.

**Evidence status:** table clearing and progress/order initialization are directly visible in the frozen Steam-PC decompilation. The semantic identity of the 16-bit reset marker, exact callback writes, and any GameCube equivalence remain unknown.

#### Callback and initialization boundary — follow-up inspection

A targeted check of the frozen snapshot's source and assembly inventory narrows the remaining uncertainty without resolving it:

- `FUN_0047f6f0` does more than the main two passes: when global `DAT_00e259a0` is nonzero, it invokes `FUN_0047ee20` an **optional second traversal** of the same spline at density `10.0`, passing zero for the two callback context arguments and the raw label `0x0047ece0` as callback. The control-flow fact is established by [`c/FUN_0047f6f0.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f6f0.c); the purpose of the flag and the callback's actual checks/writes are **not established** by the available decompiled file.
- `FUN_0047ee20` calls its function pointer once for each sampled cursor position while enumerating node connections/lookahead paths. Its call arguments are the cursor/context block, density, two caller-supplied context values, and the callback (`param_5`). See [`c/FUN_0047ee20.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047ee20.c). This verifies the traversal/callback contract, not the behavior of either callback.
- In the public file inventory at the pinned commit, code/assembly searches for `LAB_0047ea20` and `LAB_0047ece0` locate their call sites in the builder, but there is no standalone `c/FUN_0047ea20.c`, `asm/FUN_0047ea20.s`, `c/FUN_0047ece0.c` or `asm/FUN_0047ece0.s`. Nearby identified functions end at their own returns; the labels remain orphaned code labels in the checked-in source view. This explains why a normal per-function source lookup cannot recover them; it does **not** prove what the callback code does in the executable.
- The cursor-to-mesh lookup reader, [`FUN_0047f890`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c), reads from the global table at `0x00e23240` using a ten-slots-per-control-point index. This makes that table the likely destination read by the mesh-association stage, but the callback write mapping remains a hypothesis until its instructions or table writes are recovered. Do not label the individual slot fields or the `0x0047ece0` pass as validated behavior.

**Decision:** no further PC-only inference can responsibly close the table-write gap from the checked-in named functions alone. Keep the reader/layout as mapped, keep both callback bodies explicitly unresolved, and proceed only with source/trace evidence that exposes the raw label code. The Step 102 console archive remains a separate blocker.

These observations are frozen-Steam-PC evidence only. They do not establish GameCube/Wii parity or justify porting the PC implementation.

#### Progress normalization, mesh lookup, and lap-crossing cross-check

The same frozen PC snapshot also clarifies the **read side** of the lookup/progress tables, although the callback that populates the mesh table remains unresolved:

- [`FUN_0047f810`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/c/FUN_0047f810.c) computes normalized progress as the node's stored progress base plus `segmentT` times its stored span. For a closed route it clamps at `0.9999` rather than allowing a value of `1.0`; when a finish node marks an open route, it can clamp to `1.0`.
- [`FUN_0047f890` (assembly)](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/asm/FUN_0047f890.s) derives a discrete sample from `segmentT × 10` (with an adjustment at the segment boundary), combines it with the current control-point index in a ten-slots-per-node layout, and reads the corresponding entry from the global sample-to-track-mesh lookup. This corroborates the density-10 lookup layout from the builder call, but **does not reveal exactly how the callback at `0x0047ea20` writes each table entry**.
- [`FUN_0047fdd0`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c) snapshots the prior frame's normalized progress and updates the current value. On an open route, completion is reported when progress reaches `1.0`. On a closed route, progress near the start (`< 0.1`) can be unwrapped by subtracting `1.0` from a high-water mark and from the prior value when either had been above `0.8`; the finish crossing is then detected as progress overtaking the unwrapped high-water mark, with a `0.01` tolerance against the prior progress. A guard skips the wrap check for the suspicious pattern of current progress above `0.8` after prior progress below `0.1`, which the decompilation describes as a backward jump over the line.
- The race-update caller (`FUN_0047ffb0`, also visible in [`src/_text23.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c)) enables the lap-crossing check when the cursor reports a forward node crossing or when spline binding reports that it repositioned the cursor. That means the progress comparison is not simply evaluated as an unconditional distance threshold each frame.

**Confidence boundary:** the normalized formula and closed/open clamps agree between the reconstructed `SW_RACER_RE` source and the independent Steam-PC decompilation. The more detailed cursor, lookup and wrap mechanics are verified only in the latter snapshot. Both references concern PC builds; this is not evidence of GameCube/Wii behavior, and the exact mesh-table population callback remains an open sub-question.

#### Source-derived lap-crossing boundary cases (not runtime-tested)

The branch conditions in `FUN_0047fdd0` imply the following targeted tests for a future source-mapped or controlled PC/console build. These are **predicted outcomes from the decompilation, not observed game-test results**:

| Case | Inputs/state | Predicted result in the frozen PC reference |
|---|---|---|
| Ordinary forward progress on a closed route | Crossing check enabled; previous `0.45`, current `0.46`, high-water `0.45` | Update the high-water mark to `0.46`; do not report a lap. |
| Forward wrap at the finish | Previous `0.99`, current `0.02`, high-water `0.99`, crossing check enabled | Unwrap the high-water and previous value by subtracting `1`; the negative high-water is overtaken, so report a lap. |
| Apparent backward jump over the line | Previous `0.02`, current `0.99` | The guard `current <= 0.8 || previous >= 0.1` is false, so skip this finish-crossing check. |
| Point-to-point finish | Open route; current normalized progress `1.0`; crossing check reaches the open-route branch | Report completion at `1.0`. |
| No movement/rebind trigger | Live pod, crossing-check argument false, no force-check flag | Do not run the high-water crossing branch on that call. |

Boundary values matter: the wrap normalization uses strict `< 0.1` for current progress and strict `> 0.8` for the stored high-water/previous progress; the backward-jump guard allows the check only when current progress is `<= 0.8` or previous progress is `>= 0.1`. The `0.01` comparison is also explicit. A dead-state flag can force the crossing-check argument on, and the normal race-update caller enables it on a forward node crossing or successful cursor rebind.

Use these cases to build a small test sheet only after the actual Step 102 source or a named runtime target is available. Do not mark them as GameCube acceptance criteria until the console-specific progress representation and state transitions are mapped.
This provides a substantially better **PC-side behavioral reference** for the missing route lifecycle: build the cursor graph/progress tables → sample and associate spline points with track meshes → advance the cursor across track-node planes → rebind it when the active mesh changes → compute the local track offset → detect lap crossing from normalized progress. It also explains why reading `swrRace_LapProgress` alone was insufficient: that helper consumes progress-table entries prepared by the spline-build stage and a cursor maintained by the race-update path.

**Limits:** these are decompiler-derived observations for the frozen Steam PC executable. The current `SW_RACER_RE` source remains stubbed in these places, and exact source/build parity between these PC references is not established. None of this verifies GameCube/Wii behavior or the candidate Step 102 source. It improves the PC hypothesis and identifies what to compare once the console source is available; it does not justify copying the code or porting this architecture to the current prototype.

### Current GameCube prototype — closed curve and scalar distance

1. The runtime samples the checked-in generated test track through `track_sample_at`. It caches Euclidean straight-line distances between adjacent control points, wraps each point's successor with modulo point count, and uses those chord lengths to locate a parameter (t = target / segmentLength) for Catmull–Rom interpolation. This is a chord-based approximation to distance along the smoothed curve: the inspected function does not build an arc-length lookup table for the Catmull–Rom curve itself, so constant travelled-distance increments are not proven to yield constant physical distance on the smoothed curve. The runtime explicitly requires a closed-loop track with at least four points.
2. The race state keeps one scalar `g_distance`. Each active frame advances that distance using current speed, boost and pitch; it updates the lap count from the floor-divided previous/current distance against `RACE_LAP_DISTANCE`. The race finishes when the counter reaches the configured three-lap limit.
3. The distance-based lap helper is defensive around non-finite values, backward distance and overflow. Those are useful safety properties, but they are not evidence that the original game uses the same route model.

### Quantitative check — current synthetic test oval (offline calculation, 2026-10-20)

The pinned prototype commit is also the current `main` head at the time of this check. I evaluated the eight authored control points in [`generated_track.h`](https://github.com/Master-Chiken/boonta-reborn-88/blob/fa8cee047ae8e74c30c87cd94977c434bb1c7398/gamecube-demo/source/generated_track.h) using the same Catmull–Rom interpolation formula as `track_sample_at`, and numerically sampled each of the eight segments with 20,000 subdivisions.

- The generated header sets `BOONTA_TRACK_LENGTH = 181.232191`; recomputing the straight-line chord lengths between its eight control points gives **181.23219**.
- The sampled Catmull–Rom curve length is approximately **184.56396**, about **3.33177 units / 1.838% longer** than the chord sum.
- The mapping from the prototype's nominal travel distance to 3D movement is not locally uniform: `|dP/dt| / chordLength` ranges from approximately **0.5546 to 1.2467** across the sampled segments. This is a numerical property of the current eight-point test oval, not a measurement of retail-game physics or an observed player complaint.

**Equal-step displacement check:** I then reproduced `track_sample_at` over the full loop and measured the 3D centerline displacement for successive nominal distance increments of 0.1 units (1,813 increments, including the final shorter interval). The displacement ratio `worldDistance / nominalDistance` ranged from **0.5549 to 1.2467**, with median **1.0359**, 5th percentile **0.7221**, and 95th percentile **1.2407**. The minimum occurred near nominal distance 133.5 (segment 5); the maximum near 58.8 (segment 2). Using 1.0-unit steps produced a similar range, **0.5559 to 1.2459**, so this is not merely an artefact of the chosen small step. These values reproduce the published interpolation/sample mapping numerically; they are not measurements from a running Dolphin session.

**Reference freshness check:** I compared the current `SW_RACER_RE:master` against the pinned PC revision `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`. It is 29 commits ahead, but the compare result includes no changes to `src/Swr/swrSpline.c` or `src/Swr/swrRace.c`; fetching those files at current `master` confirms that the critical route-advance, track-mesh lookup, spline-binding and track-offset routines remain `HANG("TODO")` stubs. The pinned PC analysis is therefore not superseded in this specific area by the newer default-branch source.

**Interpretation boundary:** this does not establish a lap-count bug. Both `track_sample_at`'s `fmodf(travelled, total_length)` and `RACE_LAP_DISTANCE` use the same chord-sum length, so the scalar-distance lap boundary and the parametrized course wrap are aligned. The finding is narrower: the smoothed course's world-space movement per nominal distance varies by segment and within a segment. It may influence perceived movement speed, but a visible gameplay test is needed before treating it as a defect.

**Reproducible next check:** compare equal increments of `g_distance` with the resulting world-position deltas on this same test oval; record minimum/maximum displacement and the segment locations. Do not change the runtime solely from this offline result. A true arc-length lookup table is only a candidate if a repeatable gameplay symptom or an explicit fidelity requirement justifies it.

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

**Availability re-check (2026-10-20):** Rechecked the connected conversation-file list and Library metadata; the named Step 102 source ZIP and its manifest still are not available for inspection. No console source file/function is claimed as mapped. This is an input blocker, not a reason to start implementation or substitute a commercial game ROM/disc image.

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

## Product-direction clarification — reconstruct first, enhance second

**Owner's direction (2026-10-20):** use reverse engineering to obtain/reconstruct the game first, then improve it. This supersedes any interpretation of the procedural demo as the intended end product.

For Boonta, that means a staged goal:

1. **Faithful playable baseline:** reconstruct the original game's core systems from evidence—track/route representation, pod movement and handling, lap/race state, rivals, collisions/recovery, camera, HUD and race flow—using an independently implemented GameCube/Wii codebase. The current procedural oval is a development harness, not a substitute for the original game's course structure or behavior.
2. **Original-content compatibility:** establish how the target game version represents and loads course/model/texture/spline data. Keep any commercial assets local and user-supplied from a lawful copy; do not commit or redistribute them. Shared filenames or PC formats alone do not prove GameCube compatibility.
3. **Parity validation:** compare a behavior or data claim against the relevant PC, N64 and Dreamcast evidence where available. Label each claim by platform and confidence; never silently treat PC behavior as console fact.
4. **Enhancement phase:** only after the faithful baseline is playable, add the HD++ presentation, improved controls/quality-of-life, extra pods/tracks/modes and other new content as clearly separated changes.

### Consequence for the active route/spline question

The immediate research deliverable is not “make the current distance counter more sophisticated.” It is to determine what the original route system must represent, which details are actually supported by PC evidence, and what source/binary evidence is still required from N64 or Dreamcast before claiming target-platform parity. The current prototype uses an authored closed-loop curve and travelled-distance lap count; this is enough to test the rendering/input loop but does not yet reconstruct the original game's route graph, course data or lap-crossing mechanism.

The PC reverse-engineering repository is a behavioral reference, not a complete port or full decompilation: its README explicitly says it targets selected function documentation/reimplementation rather than full decompilation. See https://github.com/tim-tim707/SW_RACER_RE. The project's existing clean-room rule and source-license review still apply. A source archive or original assets can be inspected only when provenance, access and license boundaries are clear; do not use the missing Step 102 archive as an assumed dependency, and do not replace it with an unauthorized ROM/disc dump.

### Updated completion criterion for this research thread

Before closing RE-001, the dossier must answer:
- what route representation the PC reference demonstrably uses;
- which GameCube prototype assumptions differ;
- what can be said about N64 and Dreamcast from source-backed evidence;
- what remains unproven without platform-specific executable/data evidence;
- which one next investigation most directly unlocks an original-faithful playable baseline.

No implementation change is justified solely by the PC-vs-prototype difference while the target-platform mapping remains unknown.


## New evidence — spline data is gameplay infrastructure, not just a visual curve (2026-10-20)

Pinned third-party format-tool reference: [OpenSWE1R/blender-swe1r/splineblock.py, commit b0dfb8bc0437f783d86fe7824fd8703fa8ab55ce](https://github.com/OpenSWE1R/blender-swe1r/blob/b0dfb8bc0437f783d86fe7824fd8703fa8ab55ce/splineblock.py). The companion [README at the same revision](https://github.com/OpenSWE1R/blender-swe1r/blob/b0dfb8bc0437f783d86fe7824fd8703fa8ab55ce/README.md) says its spline data is used for lap progress, start/finish, player spawn/respawn, map display, guide arrow, Zero-G mode and AI pathing. This is a modding-tool author's documented interpretation, not an official specification or proof that every platform/version uses an identical layout.

### Structure directly visible in the parser

- The parser reads spline headers with point and segment counts, then parses point records.
- A point record includes up to **two outgoing links** (next) and **four incoming links** (previous) in the fields the tool interprets as connection counts/indices.
- Point data includes position, rotation, two Bezier handles, a progress field, eight branch/unknown fields, and an additional unknown field.
- The parser builds a graph of paths: a closed main route can link the last point back to point zero, while alternate routes connect back to points on existing paths.
- The tool computes a progress band for each point by traversing reachable paths. It rejects one topology where a shortcut branches before the start/finish and rejoins after it, because its progress model cannot represent that ordering safely.
- Its own exporter states limitations around branch splits/joins and limits exported spline point counts to 255. These are **tool/exporter limitations**, not proof of hard engine limits.

### Why this changes the reconstruction plan

The current Boonta demo has a single authored closed curve and counts laps by travelled distance. That is a useful harness, but it cannot yet represent all the roles the tool associates with original spline data: graph branches, start/finish and spawn markers, alternate paths, and progress metadata used by other gameplay systems.

Therefore, the faithful-baseline work should not begin by replacing one curve formula with another. It should first define an evidence-backed **route graph data model** and identify how route progress relates to:
1. vehicle position relative to the current route segment;
2. forward/backward transitions at linked points;
3. normalized progress and start/finish crossing;
4. spawn/respawn and map/guide/AI consumers;
5. branch choice and branch rejoin rules.

The PC source provides direct support for a linked spline cursor and multiple interpolation types. The parser provides an independent, implementation-level view of the block layout. Neither source proves this exact layout is the one consumed by the retail GameCube/Wii build. Until a target-platform source or verified target-format sample is available, the data model should label the binary layout **PC/tool evidence; GameCube/Wii parity unverified**.

### Decision

Keep the current curve as a rendering/input test harness. The next architecture-level research deliverable is a platform-tagged route graph schema and behavior matrix—not a gameplay rewrite. Do not import GPL-3.0 parser code into Boonta; the source is a read-only reference unless licensing is separately reviewed.


## New source pass — route projection and topology constraints (2026-10-20)

Sources pinned for reproducibility:
- [PC spline implementation, SW_RACER_RE commit `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c)
- [PC spline declarations and cursor layout, same commit](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.h)
- [Independent format-tool README, Blender importer/exporter commit `b0dfb8bc0437f783d86fe7824fd8703fa8ab55ce`](https://github.com/OpenSWE1R/blender-swe1r/blob/b0dfb8bc0437f783d86fe7824fd8703fa8ab55ce/README.md)

### New concrete PC behavior observations

1. **The route cursor is not advanced by distance alone.** `swrSpline_ProjectPoint` evaluates the cursor's orientation frame and moves the parameter in increments of 0.01 until the target world position crosses the plane associated with the route tangent. It then backs off in the opposite direction when the target lies behind the initial sample. This is a coarse iterative projection onto route progression, not a general nearest-point-on-curve solver. The code is PC-reference evidence only.
2. **The cursor has directional graph traversal.** `swrSpline_CursorStep` uses outgoing links when advancing and incoming links when retreating, with separate start/end flags. It carries branch-selection/history bits so the lookahead nodes can follow a selected path. A clean-room implementation must test reverse motion and branch rejoin behavior rather than assume forward-only motion.
3. **Curve type changes the required lookahead.** The inspected PC code uses a four-node window for B-spline interpolation, while the Bezier path uses the current node's second handle and the next node's first handle. The flat Bezier variant uses a fixed +Z up vector; other variants interpolate rotation/up data. The exact type distribution in the target GameCube/Wii release remains unverified.
4. **The PC binary reader is endian-aware.** It reads a spline count and offset bounds from the spline block, then converts header fields, connection indices, vectors/handles and progress metadata from the on-disk byte order. Some fields are intentionally not byte-swapped in the reconstruction. Those exceptions must not be generalized to another platform without a sample and a platform-specific check.
5. **Progress seeking is an encoded mapping.** The PC function `swrSpline_CursorSeekToProgress` treats progress as bands of ten: integer division selects a base band and the remainder becomes a segment parameter. For later bands it searches branch metadata (`unk_set`) to recover the corresponding route branch. This is not a universal “node index = progress” rule.

### Tool constraints that must not be mistaken for engine constraints

The Blender add-on README calls the main path the route containing point 0/start-finish/spawn, with other paths as alternates that branch from and rejoin it. It describes cyclic laps and non-cyclic point-to-point/rally routes. Its exporter imposes constraints such as at most two outgoing branches and four incoming joins, and rejects shortcuts that straddle the finish line in a particular way. Those are documented **authoring/exporter constraints**. They may reflect engine assumptions, but this research does not prove every one is a hard runtime limit. The add-on itself describes its overall status as work in progress and lists known issues; use it as corroborating reverse-engineering evidence, not as an authoritative format specification.

### Clean-room behavior matrix to build before replacing the test harness

| Test case | Expected contract to determine from evidence |
|---|---|
| Start at point 0 | Initial cursor, spawn and start/finish relationship |
| Advance across a normal segment | Correct node-window shift and continuous position/orientation |
| Reverse across a segment boundary | Correct previous-link selection and no accidental forward lap |
| Reach a dead end on a non-cyclic route | Stable endpoint flags; no infinite traversal |
| Closed-loop wrap | Exactly one lap event for a genuine forward crossing |
| Branch with two outgoing links | Explicit, deterministic branch choice |
| Alternate route rejoins main path | Correct main-route progress after the merge |
| Same world point near two route segments | Projection rule documented; no assumption of globally nearest segment |
| B-spline vs Bezier vs flat Bezier | Correct node lookahead and up-vector policy per type |
| Invalid index/offset/count | Fail safely before out-of-bounds access |

The table defines test questions/contracts to settle; it does not claim all expected values are already known. Add numeric golden vectors only after deriving them from a pinned reference or a lawful, provenance-identified target sample.

### Current recommendation

Do **not** replace the procedural curve or the distance-based lap counter in the same change. First create a platform-tagged, versioned route representation and a host-testable route-cursor module independent of rendering. Its interface should expose position, tangent/up, segment parameter, route progress, branch state, and lap-crossing events. The existing oval remains the integration harness until that module has golden tests and the GameCube/Wii evidence gap is explicitly documented.

## Route schema proposal — logical contract, not a binary-format claim (2026-10-20)

This closes the next design deliverable without pretending the GameCube/Wii binary format has been identified. The schema below is a **logical, platform-tagged model** for later fixtures and tests. It is not a proposed byte-for-byte serialization and must not be used to parse an original asset until a named platform/release sample validates it.

### Asset-level model

| Field | Purpose | Evidence / confidence |
|---|---|---|
| `source_platform`, `source_release`, `source_revision` | Keep PC, N64, Dreamcast and any future GameCube/Wii evidence separate | Required project provenance rule; exact console revisions remain unknown |
| `route_id`, `curve_type`, `closed_loop` | Identify the route, interpolation family and cyclic/open behavior | Curve families and cyclic/non-cyclic routes are documented in PC source/tooling; target distribution unknown |
| `points[]` | Ordered control-point records | PC parser/source evidence; target record layout unknown |
| `points[].position`, `handle_in`, `handle_out`, `orientation_or_up` | Evaluate position and orientation | PC source uses positions, Bezier handles and orientation/up data; not every curve type uses every field |
| `points[].next[]`, `points[].previous[]` | Represent branches, joins and reverse traversal | PC cursor uses outgoing/incoming links; do not bake exporter limits into the schema |
| `points[].progress_base`, `progress_span` | Convert cursor segment parameter to normalized progress | Present in the PC progress path; not confirmed for console data |
| `points[].branch_metadata` | Preserve branch-selection/history data without assigning unknown semantics | PC code consults `unk_set`; exact meaning is not fully established |
| `mesh_association` (optional, unresolved) | Link sampled route locations to track geometry | PC code has a density-10 lookup table, but the writer callback is unresolved; do not fabricate its format |

Unknown or absent fields must remain explicitly unknown/optional; they must not be filled from assumptions about PC-to-console parity.

### Runtime cursor contract

A platform-neutral cursor should be able to represent:

- current control-point/node identity and the required curve-type-specific lookahead;
- normalized segment parameter `t`, movement direction, chosen branch and traversal history;
- endpoint/dead-end state for open routes;
- evaluated world position, tangent and up vector;
- route progress and a separate lap-crossing event/state.

Keep **route evaluation**, **world-position projection/rebinding**, **track-mesh association**, and **lap/race state** as separate responsibilities. The PC source identifies these as distinct operations, and several reconstructed end-to-end functions remain TODO/HANG stubs. A single “advance distance and increment lap” function would hide the unresolved behavior rather than model it.

### Required invariants for synthetic host fixtures

1. Every referenced node index is validated before dereference; invalid counts, offsets and links fail safely.
2. Forward and reverse traversal use explicit graph links; reverse traversal must not emit a forward lap event.
3. A branch choice is deterministic for a given cursor state and input; rejoining a shared node does not duplicate that node or invent progress.
4. Closed-loop lap crossing is a separate event from position wrap and can occur at most once for one forward crossing.
5. Open routes have a terminal state; reaching the endpoint must not wrap unless the route is marked cyclic.
6. Curve evaluation returns finite position/tangent/up values; degenerate tangent/up inputs are handled explicitly.
7. Binary-format decoding is behind a platform/release-specific adapter; the logical route model contains no hard-coded PC byte order or assumed N64/Dreamcast layout.

These are **clean-room safety and consistency invariants**, not claims that the original game handles malformed data the same way.

### Gate before implementation

Do not add a route-cursor implementation to the GameCube runtime until all of the following are available:

- a provenance-identified target-platform route sample or source-level evidence that supports the target data model;
- numeric expected-value fixtures for at least one normal segment, one reverse boundary transition, one branch/rejoin and one finish crossing;
- a clear decision on the current test oval's role as an integration harness;
- host tests that pass independently of GX rendering, followed by a target-specific integration test.

**Current disposition:** schema proposal recorded; binary layout and console parity remain **UNKNOWN**. The next research action is to obtain stronger target-platform evidence for route representation—not to infer it from PC field names or begin replacing the runtime.

## Follow-up source check — N64 spline-block selection is a distinct variant (2026-10-20)

A pinned cross-check of the MIT-licensed `akopetsch/swe1r-assets` repository at commit `922ef535f6598a1330ff93d6b07258956f990b34` provides one additional platform-specific fact:

- Its release metadata maps Windows International, Windows Demo, Mac and Dreamcast to `SplineBlockId = 0`, while Nintendo 64 USA, Europe and Japan use `SplineBlockId = 1`. See the [release matrix](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Release.csv).
- The library's generic spline object model includes a segment header (two 16-bit words, element count, unknown count and two further 16-bit words) and segment data with several unknown 16-bit fields, a previous-node ID, a knot vector, two control-point vectors and additional unknown fields. See [SplineSegmentHeader.cs](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentHeader.cs) and [SplineSegmentData.cs](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentData.cs).
- This is evidence that the library author selects a distinct N64 spline-block metadata variant; it is **not** proof that the PC runtime's in-memory node structure matches N64 records, nor does the metadata alone tell us the meaning of the unknown fields. The public README advertises support for four block types and bit-perfect no-op reserialization, but this pass did not execute a round-trip against a provenance-identified N64 input.

### Consequence for the route schema

Keep the logical route schema platform-tagged, but add a separate **format adapter / release profile** for N64 rather than treating PC spline data as the canonical serialized representation. Keep field semantics unknown until supported by a pinned parser description, controlled runtime observation or a verified local round-trip. Dreamcast remains a separate unresolved case: its shared `SplineBlockId = 0` mapping is the asset-tool author's mapping, not independent proof that its spline bytes or runtime behavior are identical to PC.

## New source pass — independent spline-block record layout (2026-10-20)

Pinned references:
- [MIT SWE1R asset reader: spline record model](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentData.cs)
- [MIT SWE1R asset reader: spline record header](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentHeader.cs)
- [GPL-3.0 Blender tool: splineblock.py](https://github.com/louriccia/blender-swe1r/blob/b0d4019addb97d51523019ca1233411fae0508d6/splineblock.py)

### What the independent reader adds

The MIT reader models each spline block item as a header followed by a count-governed list of segment records. Each segment record is a data record followed by a separate segment header. The data record model labels:
- six initial 16-bit words, including a field named `PreviousNodeId` at offset `0x08`;
- a three-float vector at offset `0x10`;
- a float at `0x24`;
- two three-float control-point vectors at offsets `0x28` and `0x34`;
- a 32-bit field at offset `0x40`.

The segment header model labels 16-bit words at `0x00`, `0x02`, `0x0c`, and `0x0e`, with 32-bit fields at `0x04` and `0x08`. Several names are explicitly placeholders such as `Word_00` and `Unk_40`; these are offsets and widths, not decoded semantics. The record field layout and offset attributes are useful independent evidence for a **PC/tooling schema**, but do not prove this is the layout consumed by N64, Dreamcast, GameCube or Wii builds.

The Blender parser independently describes a different-looking 0x50-byte point record using big-endian struct format `>8h48x10h`: outgoing-link count, incoming-link count, up to two outgoing indices, up to four incoming indices, a progress band, eight branch/route metadata values and an unknown field. It reads position, rotation and two Bezier handles at offsets `0x10`, `0x1c`, `0x28`, and `0x34`. Its tool comments explicitly impose exporter limits and its writer normalizes/pads the link arrays. Those implementation details are evidence of the tool's understood PC representation, not proof that the unknown words in the MIT model map one-to-one onto the Blender names.

### Important schema correction

Keep two representations separate:

1. **Raw serialized record** — platform/release-specific fields, offsets, endianness, unknown words and counts. Preserve unknown fields without assigning semantics.
2. **Normalized runtime route graph** — decoded node links, positions, curve controls, progress mapping, branch state and optional orientation data, populated only where the selected platform adapter has evidence.

In particular, the runtime PC reverse-engineering notes describe per-node progress base/span, while the Blender raw point model exposes a progress band plus `unk_set` metadata. These may be related through derived/build-time tables, but the sources do not establish that they are identical fields or that a console record stores PC's base/span directly. Treating them as one field would overstate the evidence.

### Next verification target

Use the MIT reader's documented bit-perfect no-op round-trip capability as a **reference experiment**, not as code to import: for a legally available, provenance-identified PC spline block, verify byte-identical deserialize/serialize output before using it to test field hypotheses. Then compare only independently sourced target-platform samples if available. Without a verified sample, do not create synthetic “golden” binary bytes or claim cross-platform format parity.

**Disposition:** the PC/tooling raw-record hypothesis is better constrained; target-console binary layout and the semantics of several words remain **UNKNOWN**.



## New source pass — audit of upstream spline reserialization tests (2026-10-20)

Pinned references at `akopetsch/swe1r-assets` commit `922ef535f6598a1330ff93d6b07258956f990b34`:

- [Spline reserialization test cases](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original.Tests/Reserialization/SplineBlockItemsReserializationTest.cs)
- [Shared reserialization test implementation](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.TestUtils/BlockItemsReserializationTestBase.cs)
- [Test fixture/provider](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original/OriginalBlocksProvider.cs)

### What the tests actually establish

The test suite defines individual spline-item round-trip cases for value IDs 0–90 and a set of selected IDs up to 190. The shared test logic deserializes an item, clones it, serializes the current item again, then compares the original and reserialized byte arrays; if they differ, it reports the differing item-part types. The provider loads named block files as embedded assembly resources, and the test fixture calls that provider during setup.

This is stronger evidence than a README statement alone that the author has implemented and authored a byte-equality regression harness for selected PC/tooling spline items. However, the source inspection here is **not a fresh execution of those tests**: no run result was verified in this project session, and the fact that the fixture uses embedded resources does not independently establish the provenance/release/platform of every embedded block. These upstream cases must not be reported as our own round-trip pass or as console-format validation.

### Consequence for Boonta's next experiment

The experiment design is now precise enough to avoid rebuilding the test harness from scratch:

1. Keep the upstream test implementation as a read-only reference; do not copy code or embed upstream game-derived resources.
2. For any future private, provenance-identified PC input, record the release/file identity and hash locally, run a no-op deserialize/serialize, and compare the whole-file bytes—not only decoded fields.
3. If only individual items are reserialized, also compare the outer block/table bytes separately; item equality alone does not establish container-level byte identity.
4. Record test command, tool revision, input identity, before/after hashes, and result. Then keep PC evidence separate from any target-console comparison.

**Disposition:** a credible upstream item-level test pattern exists. The current project still has no independently executed, provenance-recorded round-trip result, and GameCube/Wii parity remains **UNKNOWN**.



## Follow-up source pass — item equality versus container equality (2026-10-20)

Pinned upstream reference remains `akopetsch/swe1r-assets` commit `922ef535f6598a1330ff93d6b07258956f990b34`.

Sources inspected:
- [Upstream README: stated bit-perfect block-file capability](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/README.md)
- [Item-level round-trip base](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.TestUtils/BlockItemsReserializationTestBase.cs)
- [Original block provider](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original/OriginalBlocksProvider.cs)
- [Spline item test cases](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original.Tests/Reserialization/SplineBlockItemsReserializationTest.cs)

### Finding

The README states that the library supports bit-perfect reserialization of block files. But the inspected spline regression harness does **not**, by itself, prove whole-container equality: it takes an item returned by the provider, clones that item, serializes the item through the item-level helper, and compares `BlockItem.Bytes` with the reserialized item's bytes. The provider separately loads whole named blocks from embedded resources through `BlockLoader.Load`. The inspected test base does not compare the original complete block stream against a complete reserialized block stream, nor assert equality of the outer block header/table/index regions.

This distinguishes three claims that must not be collapsed:
- **Item-level regression coverage:** explicitly present in source for selected spline item IDs.
- **Library-level whole-block capability:** claimed by the upstream README, but not independently executed or proven by the item test inspected here.
- **Boonta/target-console validation:** not established.

A broad search of the pinned repository for block-level reserialization test names did not surface a dedicated whole-container no-op equality test. This is a bounded source search, not proof that no such test exists anywhere in the repository or in another revision.

### Experiment design update

If a provenance-identified, legally available PC block becomes available for private analysis, use two separate assertions:
1. **Item invariant:** every selected spline item's serialized bytes match its original item bytes.
2. **Container invariant:** complete output block bytes match the input byte-for-byte, including header/table/offsets/padding/unknown regions.

Report the two results independently. If the library only exposes item serialization in the chosen harness, container equality remains untested; do not infer it from passing item tests. Record input release/platform/file identity, SHA-256 before and after, exact command, tool revision, and result. No game-derived input or extracted asset should be committed to Boonta or CI.

### Current blocker and next priority

The current session has no provenance-identified PC block input available for a fresh round-trip, and we have not established a lawful, reproducible local test fixture. Do not manufacture a binary fixture that pretends to be a real game block. Mark the binary experiment blocked on input provenance/access, and continue with source-level reverse engineering that can still yield falsifiable hypotheses—next, trace the PC spline block loader's container framing and distinguish fields consumed from fields merely preserved, while maintaining a strict PC-versus-console evidence boundary.

**Disposition:** item/container test coverage is now explicitly separated. Whole-container round-trip for our own evidence remains **NOT RUN**; GameCube/Wii format and behavior parity remains **UNKNOWN**.


## Follow-up source pass — PC block framing and save-path behavior (2026-10-20)

Pinned source: `akopetsch/swe1r-assets` commit `922ef535f6598a1330ff93d6b07258956f990b34`, especially [`Block.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Block.cs), [`BlockLoader.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/BlockLoader.cs), and [`BlockItem.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/BlockItem.cs).

### Observed container structure in this PC reader

The generic block loader:
- reads a 32-bit item count;
- advances over `count × parts-per-item` 32-bit offset entries;
- reads a 32-bit terminal size;
- returns to the stream start and captures that many bytes as the complete block;
- parses the count, offsets and terminal size, then slices each item's parts using adjacent offsets and the terminal size.

The generic save path does not preserve the original header/table bytes verbatim. It recalculates the count, emits offsets in item/part order from the newly calculated header size, writes the new terminal size, then concatenates each item's bytes. This means an item-level byte-equality result is logically insufficient to prove full-block byte equality. A no-op save might still reproduce the original container, but that must be tested against a real input; the code path alone does not establish that result.

### Preservation risks to test, not assume

The source's save path makes these falsifiable questions important:
- Does the original table use exactly the same item/part order and offset policy that the writer regenerates?
- Are gaps, alignment bytes, unusual offset values, unused regions or trailing bytes represented in the parsed item parts, or could a rebuild omit/canonicalize them?
- Does each platform/release use this same container schema and endianness? Current evidence supports only the pinned PC/tooling reader's model.

The loader uses the terminal size to capture the block, but the save path derives a new terminal size from the generated header plus item-part lengths. Therefore, byte-for-byte equality of the complete block must be measured, not inferred from equal semantic fields or item payloads.

### Revised evidence ladder

1. **Source-level PC hypothesis:** the reader models a count + offset table + terminal-size header and reconstructs that header on save.
2. **Upstream item tests:** selected items are compared byte-for-byte after item-level serialization.
3. **Upstream whole-block claim:** README advertises bit-perfect reserialization, but the inspected tests do not independently demonstrate whole-block equality.
4. **Boonta experiment:** not run; no provenance-identified input or locally recorded before/after hash is available in this session.
5. **GameCube/Wii parity:** unknown; no console block sample or console-specific parser validation established.

**Disposition:** next source-level work should inspect how spline item parts are divided and whether unknown/padding bytes survive inside each part. Keep this strictly as PC reader evidence; do not transplant its header assumptions into the console adapter without independent evidence.


## Follow-up source pass — what spline item round-trip actually exercises (2026-10-20)

Pinned upstream reference: `akopetsch/swe1r-assets` commit `922ef535f6598a1330ff93d6b07258956f990b34`. Relevant files:
- [`SplineBlockItem.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineBlockItem.cs)
- [`Spline.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/Spline.cs)
- [`SplineSegment.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegment.cs)
- [`BlockItemsTestBase.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.TestUtils/BlockItemsTestBase.cs)
- [`BlockItemsReserializationTestBase.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.TestUtils/BlockItemsReserializationTestBase.cs)

### Confirmed round-trip path

The spline block item is represented by one `SplineBlockItemPart`. The generic block loader stores each part's original byte slice in `BlockItemPart.Bytes`. The test then:
1. obtains an item from the provider and clones it while it still holds the raw part bytes;
2. calls `item.Load()`, which deserializes the bytes into a structured `Spline`;
3. calls `item.Save()`, which serializes that structured object and replaces the part's byte array;
4. compares the clone's original item bytes with the newly serialized item bytes.

Therefore, the test is not merely comparing a clone of the raw bytes with itself: it exercises structured deserialize → serialize. This is a meaningful item-level regression test.

### What the test can and cannot tell us

The data model explicitly represents the spline header, a count-governed list of segments, each segment's data record and segment header. Unknown-looking values such as `Word_00`, `Unk_0a`, `Unk_40`, `Word_0`, and `UnknownCount` are still serialized fields, so the serializer can preserve them as values if its mapping is correct.

But the inspected model does not show a separate raw-byte field for arbitrary unmodeled padding or gaps *inside* the spline part. Since saving replaces the original raw part with bytes generated from the structured model, any unmodeled bytes would be at risk unless the serializer's own format/context rules explicitly preserve them. The source inspected here does not establish that arbitrary extra bytes are retained. This is a code-level risk hypothesis, not a demonstrated loss: only a real round-trip test can show whether it occurs for a given input.

This also sharpens the test's meaning: passing cases would support exact reconstruction of the modeled spline item bytes for those selected fixtures, not a general guarantee for every spline, every release, every padding pattern, the outer block container, or any console format.

### Next falsifiable checks

- Inspect the serializer's handling of trailing bytes and count-driven lists, without importing its implementation into Boonta.
- If authorized input later becomes available, record original item length, decoded segment count, serialized item length, byte diff ranges, and before/after SHA-256; report separately whether all unknown fields and any trailing region survive.
- Do not synthesize a “real” game fixture. Without provenance-identified input, mark empirical preservation tests **BLOCKED**, and continue documenting the model-level hypotheses only.

**Disposition:** upstream tests do exercise structured spline deserialize/serialize and compare original versus regenerated item bytes. No such test was executed for Boonta in this session; unknown padding preservation and GameCube/Wii parity remain **UNKNOWN**.
