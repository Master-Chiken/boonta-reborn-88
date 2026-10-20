# RE-001 — Route/spline progression: PC reference vs current GameCube prototype

**Research date:** 2026-10-20  
**Status:** PC-source evidence recorded; current prototype mapped. The historical Step 102 bundle is optional background material, not a required source baseline.  
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

**Decision:** no further PC-only inference can responsibly close the table-write gap from the checked-in named functions alone. Keep the reader/layout as mapped, keep both callback bodies explicitly unresolved, and proceed only with source/trace evidence that exposes the raw label code. The old Step 102 bundle is not a blocker; it was an early research compilation, not a canonical console source archive. GameCube/Wii behavior remains unknown until supported by actual target-specific source or runtime evidence.

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

Use these cases as PC-derived hypotheses. A small Boonta test sheet can be built against the current prototype independently; do not label PC predictions as GameCube acceptance criteria until target-specific behavior is supported by code or runtime evidence.
This provides a substantially better **PC-side behavioral reference** for the missing route lifecycle: build the cursor graph/progress tables → sample and associate spline points with track meshes → advance the cursor across track-node planes → rebind it when the active mesh changes → compute the local track offset → detect lap crossing from normalized progress. It also explains why reading `swrRace_LapProgress` alone was insufficient: that helper consumes progress-table entries prepared by the spline-build stage and a cursor maintained by the race-update path.

**Limits:** these are decompiler-derived observations for the frozen Steam PC executable. The current `SW_RACER_RE` source remains stubbed in these places, and exact source/build parity between these PC references is not established. None of this verifies GameCube/Wii behavior. It improves the PC hypothesis and identifies what to compare against the current prototype; it does not justify copying code or porting this architecture to the prototype.

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

## Step 102 — historical context, not a source gate

The user clarified on 2026-10-20 that “Step 102” was an early research bundle assembled collaboratively from collected game references, manuals, and reverse-engineering material to help start Boonta Reborn. It is not the game itself, not a verified native GameCube source tree, and not more authoritative than the current project or stronger version-pinned references. Its absence must not block RE-001 or future work.

No file from that historical bundle was inspected for this dossier, so no claims are made about its contents, completeness, or redistribution status. Do not spend effort recovering it, recreating it, or integrating it wholesale. If a specific note is later useful, trace that individual claim to a reliable source and assess any data's provenance separately. Deleting the bundle is not required for progress; make no destructive change without an explicit request.

GameCube/Wii parity remains **unknown** because the available PC evidence and the current clean-room prototype do not establish original console behavior. Resolve that uncertainty through the current code/tests and any lawful, version-specific console evidence that is actually available—not by treating the old bundle as a missing dependency.

## Next question (not active until RE-001 is reviewed)

After the route/cursor comparison is accepted, take a separate evidence block for **PC pod-control/traction**: trace how player input becomes target turn rate, how the target is capped by vehicle stats/pace, how current turn rate changes over delta time, and how traction blends desired velocity with current velocity. Then compare those responsibilities with the prototype's scalar lateral-velocity/damping helpers. Do not change those helpers until the comparison has a source-linked specification.

## Disposition

- [x] PC source functions inspected at the pinned revision.
- [x] Current prototype route sampling and lap counter mapped to exact source lines.
- [x] Facts separated from console hypotheses.
- [x] Step 102 dependency removed from the critical path after owner clarification; no archive recovery or import is required.
- [ ] GameCube/Wii route/race behavior — still unverified; requires target-specific evidence, not the historical bundle.
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

The PC reverse-engineering repository is a behavioral reference, not a complete port or full decompilation: its README explicitly says it targets selected function documentation/reimplementation rather than full decompilation. See https://github.com/tim-tim707/SW_RACER_RE. The project's existing clean-room rule and source-license review still apply. The historical Step 102 bundle is optional context, not an assumed dependency. Any game-derived data must be checked for provenance and licensing; do not substitute unauthorized ROM/disc material.

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


## Follow-up source pass — serializer boundary and count-driven spline lists (2026-10-20)

Pinned serializer reference: `akopetsch/ByteSerialization` commit `8f27ba1467a6a909eac44f3993aeaa93668773dc` (MIT), used by the pinned `swe1r-assets` reader. Relevant sources:
- [`ByteSerializer.cs`](https://github.com/akopetsch/ByteSerialization/blob/8f27ba1467a6a909eac44f3993aeaa93668773dc/ByteSerialization/ByteSerializer.cs)
- [`LengthComponent.cs`](https://github.com/akopetsch/ByteSerialization/blob/8f27ba1467a6a909eac44f3993aeaa93668773dc/ByteSerialization/Components/Attributes/Limiting/LengthComponent.cs)
- [`Spline.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/Spline.cs)

### Observations

- `ByteSerializer.Deserialize` builds a typed serialization node over the supplied stream and returns the deserialized object plus a context. `Serialize` builds a typed node over the object and writes generated bytes to a stream.
- The spline model serializes its header first, then a segment list whose deserialization length is bound to `Header.ElementsCount`.
- The inspected `LengthComponent` contains a TODO about setting a binding value before serialization; the callback registration is commented out in this pinned source. This is a source-level warning that collection-count/header synchronization is not automatic through this component alone. The spline class exposes an explicit `UpdateSegmentsCount()` helper, but the inspected item `Save()` path does not visibly call it before serialization.

### Implications (hypotheses, not observed failures)

A spline item whose in-memory `Segments.Count` differs from `Header.ElementsCount` may serialize a header/list combination that is inconsistent, depending on the rest of the serializer's collection behavior. Existing round-trip fixtures may avoid this state because they deserialize the list using the header's count and do not mutate it before saving. The inspected source is enough to define a targeted regression case, but not enough to assert that a real upstream fixture fails.

The typed serializer writes fields represented by the object model; its public API does not expose a general “append original unmodeled trailing bytes” argument. Since the spline item save path replaces the raw part bytes with generated serialization output, arbitrary trailing bytes outside the modeled structure are not shown to be preserved by this path. Again, this is a risk to test, not proof of data loss.

### Next falsifiable cases

For any future authorized, provenance-identified PC fixture, test separately:
1. untouched deserialize → serialize equality;
2. deliberate segment-list count change with and without `UpdateSegmentsCount()`;
3. original part length versus serialized length, including any trailing region;
4. whether unknown fields round-trip unchanged;
5. complete block equality separately from item equality.

Do not create fake golden bytes or import the upstream serializer into Boonta. This source inspection is reference research only; no serializer tests were executed in the Boonta repository.

**Disposition:** an additional model-level risk is identified: spline list count is header-bound and its synchronization helper is explicit, not visibly invoked by `Save()`. Empirical result remains **NOT RUN**; PC fixture provenance is blocked; GameCube/Wii parity remains **UNKNOWN**.


## Follow-up source pass — PC lap-progress and finish-line invariants (2026-10-20)

Pinned source: [`tim-tim707/SW_RACER_RE` commit `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab), principally [`swrRace.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c), [`swrObj.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrObj.c), and [`types.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/types.h). This is PC reverse-engineering source, not console evidence.

### Directly visible behavior

| Area | Source-level rule | Boundary or caveat |
|---|---|---|
| Progress mapping | `swrRace_LapProgress` reads the cursor's control point and computes `segmentT * span + base` from `spline_progress_values[cp]`. | Correctness depends on cursor-to-control-point binding and baked base/span values; these are not reconstructed by this function. |
| Closed vs. open route | When `swrSpline_finishNodeIdx < 0`, progress at or above 1 is clamped to `0.9999`; for an open route, values strictly above 1 are clamped to 1.0. | The source's condition means an open-route value exactly equal to 1 remains 1; a value below 1 remains unchanged. |
| Previous-frame state | `swrRace_LapCompletion` copies current `lapComp` into `lapCompPrev` before calculating the new progress. | The first call's behavior depends on initialization of `lapComp`; initialization parity needs separate tracing. |
| Remote racer | In multiplayer, a remote racer takes progress, high-water mark, and lap count from indexed remote arrays; local racers derive progress from their spline cursor. | Slot validity/index bounds and network update timing are not established by this function alone. |
| Crossing gate | Crossing logic runs only when `checkCrossing != 0` and either current progress is at most 0.8 or previous progress is at least 0.1. | This gate deliberately excludes some frames near a high-to-low wrap; it is not simply a generic “progress decreased” detector. |
| Wrap normalization | If current progress is below 0.1, a previous high value above 0.8 and/or high-water mark above 0.8 is shifted down by 1.0 for the crossing comparison. | These thresholds create a defined wrap window (0.8/0.1), not a universal tolerance for arbitrary teleports. |
| Open-route completion | On the crossing-check path, an open route completes when current progress is at least 1.0, then resets idle time and assigns `lapCompMax = lapComp`. | If the crossing gate is not entered, this function does not take that completion branch on that call. |
| Closed-route completion | A closed-route crossing requires the normalized high-water mark to be overtaken, with previous progress within 0.01 of that mark; completion is true only when the normalized high-water mark is negative. The function then resets idle time and updates the high-water mark to current progress. | This is a high-water-mark/wrap test, not a pure position-plane intersection. A true result is not established solely by crossing from a high fraction to a low fraction. |
| Dead racer | A racer with the DEAD flag forces `checkCrossing = 1`. | This overrides the caller's crossing-check request, but does not bypass the later progress and wrap conditions. |
| Per-frame caller | `swrRace_UpdateRaceProgress` asks for crossing checks when the spline cursor moved forward or binding reports 1; backward movement increments `checkpointCount` and resets `moveTick`, while forward movement clears `checkpointCount`. | Cursor advance, binding, and track-mesh lookup are TODOs in this source tree; end-to-end runtime behavior is therefore incomplete in the reconstruction. |

### Falsifiable regression vectors

These are proposed tests derived from the source, **not tests executed here**:

1. **Progress clamp:** closed route at raw progress 0.9999, 1.0, and above 1.0; open route just below, exactly at, and just above 1.0. Assert the precise outputs above.
2. **Closed-route wrap:** previous progress near 0.99, current progress near 0.02, and high-water mark near 0.99. Check normalization and the `previous - 0.01 <= max` condition independently; do not assume this alone proves a lap.
3. **Backward teleport across the line:** previous progress near 0.02, current progress near 0.99. Verify the gate and normalization do not award a lap merely because the numeric value jumped high.
4. **High-water mark threshold:** normalized maximum just below, exactly at, and just above zero. The source's final condition is strict (`maxComp < 0`), so equality at zero should not complete a closed-route lap.
5. **Crossing request:** identical progress values with `checkCrossing` false versus true; separately force the DEAD flag and verify it changes the effective request.
6. **Open finish:** progress exactly 1.0 with crossing checks enabled and disabled; verify the open-route branch is gated, and verify the high-water mark update on the enabled path.
7. **Remote/local parity:** feed equivalent synthetic progress histories through local and remote data paths, while separately checking that the remote arrays' lap count and high-water mark are sampled consistently. This would validate the reimplementation contract, not console parity.

### Evidence classification and remaining unknowns

- **Direct PC-source evidence:** the formulas, constants, branch order and state writes listed above are visible in the pinned source.
- **Derived test hypotheses:** the seven vectors above are deductions from that source and must be validated against an executable reference before being called observed game behavior.
- **Known reconstruction holes:** `swrRace_AdvanceSplineCursor`, `swrRace_GetTrackMeshAtCursor`, `swrRace_UpdateSplineBinding`, and `swrRace_ComputeTrackOffset` are TODOs. The per-frame chain that supplies cursor movement and crossing eligibility is therefore not fully reconstructed.
- **Not established:** actual GameCube/Wii progress encoding, finish-line thresholds, multiplayer behavior, or parity with PC. No console executable or game-derived asset was used, and no gameplay test was run in this pass.

**Disposition:** the PC finish-line logic is now specified as a small set of source-backed invariants and boundary tests. Next priority is to trace initialization and consumers of `lapComp` / `lapCompMax` (including standings and lap-count updates), then convert the highest-confidence invariants into independent tests for Boonta's normalized route-progress layer. Keep target-console behavior marked **UNKNOWN** until independently supported.


## Follow-up source pass — lap-count timing and standings consumer (2026-10-20)

Pinned reference remains PC source commit [`a9863edd4caaa573f89ff634fa7d1cd6d41738ab`](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab). The inspected consumer path is [`swrObj.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrObj.c), especially `swrObjJdge_F2`, `swrObjJdge_GetRacerProgress`, `swrObjJdge_GetRacerRankValue`, and `swrObjJdge_UpdateStandings`.

### Lap completion is also a timing split

In the active race-state branch, `swrObjJdge_F2` calls `swrRace_UpdateRaceProgress` for each active racer. When it reports a crossing:

1. The returned `crossTime` is added to total race time and to the currently indexed lap-time slot. The source comment describes it as the portion of the frame before the crossing.
2. The current lap index is incremented and written to `results_P1_Lap`.
3. If the new lap index equals `jdge->num_laps`, the racer is marked finished and local-player control/boost flags are changed. Otherwise, the next lap-time slot is reset to zero.
4. If the racer is not finished, the remainder of the frame, `swrRace_dt_raw_d - crossTime`, is added to the new lap and total time, with a 3000-second cap.

This means a faithful reimplementation cannot merely increment a lap counter when progress wraps: it must also split the frame's time across the old and new lap at the crossing. The source uses the **raw** frame delta for the remainder, not the clamped `swrRace_deltaTimeSecs`; the exact value and quality of `crossTime` depend on the unfinished cursor-advance path.

### Standings use lap count plus a wrap-corrected fractional metric

For unfinished racers, `swrObjJdge_GetRacerProgress` computes a placement metric from the integer lap count and `lapCompMax`, correcting the difference between `lapCompMax` and current `lapComp` by taking the absolute difference and folding values above 0.5 around the loop. Negative final progress is clamped to zero. The source therefore uses the high-water mark and current fractional progress together; the result is not simply `lap + lapComp`.

The rank helper uses this progress metric for racers whose finished flag is clear. Finished racers instead receive `maxRaceTime - total_time` as the rank value. The standings routine then repeatedly selects the highest remaining rank value and assigns positions, while also deriving gaps to the leader, local players and AI pace-setter. It writes `-100.0` to the local-player gap when no local player is available. These are source-backed PC rules; tie behavior should not be generalized beyond the exact selection/comparison logic.

### Regression vectors added to the test plan

These are proposed cases, not executed tests:

- **Frame split:** crossing at fractions 0, 0.25, 0.99 of a frame; verify the old lap receives `crossTime` and the next lap receives the remainder, without double-counting.
- **Last lap:** for `num_laps - 1` before the crossing, verify the increment reaches `num_laps` and takes the finish branch; verify the non-final branch zeroes the next lap slot.
- **Raw versus clamped delta:** choose a test where raw and clamped deltas differ, and assert which value is added to the remainder.
- **Wrap-corrected placement:** current progress and high-water mark close together, then across the 0/1 boundary; test differences on either side of the 0.5 fold threshold.
- **Finished ranking:** compare rank ordering before and after the finished flag is set, with distinct total times; test equal values separately without inventing a stable tie order.
- **No-local-player sentinel:** verify the standings gap field is `-100.0` only on the no-local-player branch.

### Evidence boundary

The timing split, lap counter update and standings formula are directly visible in the pinned PC source. The actual crossing fraction depends on `swrRace_AdvanceSplineCursor`, which remains a TODO/HANG in this source reconstruction, so the end-to-end trigger timing has not been runtime-validated. Neither these rules nor the PC data structures establish GameCube/Wii behavior. No binary, ROM, game asset, or console test was used.

**Disposition:** RE-001 now covers the PC route-progress formula, finish-line crossing conditions, lap-time split, lap-count update, and placement metric as separate contracts. Before implementation, reconcile these observations with the frozen Steam-PC decompilation and keep all target-console assumptions explicitly unresolved.


## Follow-up source pass — crossing trigger versus reconstructed implementation (2026-10-20)

Pinned PC reference: [`swrRace.c` at `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c) and [`swrRace.h` at the same commit](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.h).

### Important evidence distinction

The source has a useful mismatch between declarations/comments and executable reconstruction:

- `swrRace_AdvanceSplineCursor` is currently `HANG("TODO")`. Its nearby comment describes stepping the cursor over node planes in `segmentT += 0.01` increments and computing `outCrossTime` by line-plane interpolation of previous/current position, multiplied by the raw frame delta. This describes intended/recovered behavior, but the function body does not implement it.
- `swrRace_GetTrackMeshAtCursor`, `swrRace_UpdateSplineBinding`, and `swrRace_ComputeTrackOffset` are also `HANG("TODO")`.
- `swrRace_UpdateRaceProgress` calls those functions before `swrRace_LapCompletion`. It requests crossing evaluation when cursor movement reports forward progress or spline binding returns exactly 1. Therefore the full lap trigger cannot be validated end-to-end by running this reconstructed source as-is.
- The same update function calls `swrSpline_ProjectPointStub` twice and `swrSpline_GetSampleSpacing`; source comments describe these as retail stubs/vestigial state. Do not build a new projection algorithm around these calls without separate evidence from the original executable.

### Directly visible lap-completion state machine

The implemented `swrRace_LapCompletion` body supports these exact rules:

1. A DEAD flag forces the local `checkCrossing` argument to 1.
2. It snapshots the old `lapComp` into `lapCompPrev`, then reads current progress from the spline cursor for local racers or the multiplayer arrays for remote racers. Remote racers also copy their high-water mark and lap count from remote arrays.
3. It updates `idleTick`: accumulate frame delta while `moveTick < 9`; otherwise reset idle time to zero.
4. It skips crossing evaluation unless `checkCrossing != 0` and (`lapComp <= 0.8` or `lapCompPrev >= 0.1`). The comment identifies the excluded case as jumping backward across the line, where progress snaps high just after the previous frame was near the line.
5. When current progress is below 0.1, it subtracts 1 from the high-water mark if that mark is above 0.8, and independently subtracts 1 from previous progress if previous progress is above 0.8.
6. For an open route (`swrSpline_finishNodeIdx >= 0`), the crossing result is `lapComp >= 1.0`; on this path idle time is reset and `lapCompMax` is set to current progress even when the result is false.
7. For a closed route, the outer condition requires `maxComp < lapComp` and `lapCompPrev - 0.01 <= maxComp`. Only then is the result assigned from the strict condition `maxComp < 0`; idle time is reset and the high-water mark is updated to current progress. If the outer condition fails, the function returns false without that high-water-mark update.

This narrows the earlier shorthand: the high-water mark is **not updated on every frame**. Its write is on the open-route crossing-check path or the closed-route path that passes the overtaking/previous-progress guard. This update cadence should be preserved in any independent implementation or explicitly tested as a deliberate divergence.

### New boundary tests to prioritize

All are test proposals, not executed results:

- Hold `checkCrossing = 0` while current progress changes; verify `lapComp`/previous state changes but no crossing branch writes the high-water mark.
- Exercise the gate boundaries at current progress exactly 0.8 and just above, with previous progress exactly 0.1 and just below.
- For a closed route, vary `maxComp` around 0.8 before unwrapping, then around 0 after unwrapping; check both the outer comparison and strict negative test.
- Make the outer condition fail after the current progress wraps; verify the high-water mark remains unchanged on that call.
- For open routes, test `lapComp` just below and exactly 1.0, with crossing enabled; verify high-water mark and idle-time writes even when completion is false.
- Verify the DEAD override independently from the crossing gate, while retaining the remaining conditions.
- Do not claim the sub-frame crossing time is accurate until `swrRace_AdvanceSplineCursor` has a trustworthy executable/reference implementation or an independently observed oracle.

### Consequence for Boonta

The best near-term deliverable is a small, engine-independent unit-test suite for the *specified lap-completion state machine*, with source-derived test fixtures and no game assets. It must be labelled as a PC-reference contract test, not GameCube/Wii parity. Cursor traversal and sub-frame crossing-time interpolation remain a separate, higher-risk RE task. No Boonta code, assets, ROMs, or executables were changed or added in this pass.


## Cross-check against frozen Steam-PC decompilation — lap logic and cursor traversal (2026-10-20)

Pinned independent PC reference: [`DeonPoncini/swep1r_decomp` commit `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef), especially [`src/_text23.c`](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c). This is the frozen Steam-PC Ghidra decompilation described in issue #226; it is a separate PC reference, not console evidence and not a source to copy into Boonta.

### Comparison results

- **Lap-completion logic strongly matches.** At function address `0x0047fdd0`, the frozen decompilation matches the readable `SW_RACER_RE` implementation's branch structure: DEAD forces crossing evaluation; old progress is saved; remote multiplayer progress/high-water/lap state is loaded; idle time uses the `moveTick < 9` branch; the crossing gate uses `0.8` and `0.1`; wrap normalization subtracts 1; open routes return whether progress reached 1.0; closed routes require the high-water mark to be overtaken with the `0.01` tolerance and return true only for a negative unwrapped maximum. This is a cross-source PC corroboration of the helper's logic, not an executable test or proof of identical game builds.
- **Cursor advance has executable decompiled logic where the readable reconstruction has a TODO.** At `0x0047f8e0`, the Steam-PC decompilation initializes forward/backward outputs to zero, evaluates the cursor frame/plane against current and previous positions, and steps the segment parameter by approximately `+0.01` while moving forward. When it crosses a node boundary, it detects a change in node index; entering node 0 can compute a crossing-time fraction from the previous/current plane distances and the raw frame delta. The decompiled function also contains a separate backward traversal path that steps by approximately `-0.01` when the relevant cursor state allows it. The exact semantic interpretation of all decompiler locals remains provisional; the raw pinned function is the evidence.
- **Binding and track-offset routines also have bodies in the frozen decompilation.** `0x0047fbb0` updates the track-mesh association when the current mesh changes and is eligible, then refreshes cursor-derived mesh/sample/projection fields. `0x0047fca0` derives a track-relative offset/direction from the cursor frame and racer position, with a fallback vector when the lateral displacement is too small. These address matches explain why the corresponding `SW_RACER_RE` bodies are still HANG stubs, but they do not independently prove every field's semantic name.
- **Version confidence remains bounded.** The matching function addresses and nearly identical lap logic raise confidence that both references describe the same Windows-PC code path. They do not establish which retail build each reference exactly corresponds to, nor any GameCube/Wii parity. The Steam-PC decompilation repository has no root LICENSE file identified in the earlier audit, so it remains a read-only research reference; do not copy its code into the project.

### What this changes in the RE plan

The highest-value next action is now **not** to re-derive the lap helper from scratch. It is to record a side-by-side behavior matrix for the cursor advance and binding path: observable inputs/outputs, node-boundary cases, forward/backward steps, wrap to node 0, sub-frame crossing-time formula, and conditions that skip binding. Keep formulas as pseudocode only when directly supported by the pinned decompilation, and leave decompiler ambiguities explicit. Any unit tests created from that matrix must be marked PC-reference contract tests, not console acceptance tests.

No Boonta gameplay code, assets, ROMs, or executables were changed or imported in this pass.


## Cursor traversal/binding behavior matrix — frozen PC reference (2026-10-20)

Pinned evidence: `DeonPoncini/swep1r_decomp` commit `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`, file `src/_text23.c`. Function addresses below are PC virtual addresses. This matrix separates literal observations from semantic interpretation; it is not console evidence.

| Function | Directly observed behavior | Confidence / unresolved points |
|---|---|---|
| `0x0047f8e0` cursor advance | Initializes both output flags to zero and crossing-time output to 0. Builds a plane/frame from the cursor. While the current position is on the forward side of the plane and the cursor state at offset `+0xcc` is zero, increments the cursor parameter at `+0xb4` by `0.01`, refreshes the frame, and marks the forward output. | Direct from decompilation. The meanings of offsets and the plane orientation are inferred from use, not recovered type names. |
| `0x0047f8e0` node transition | After a forward step, compares the node/index field at `+0xbc` with its saved value. If it changed to zero, it may calculate crossing time when the current-vs-previous position projection delta is at least `0.01`; otherwise the output remains zero. | Direct branch structure. Exact semantic identity of node zero as lap/finish wrap is strongly suggested by surrounding lap logic but not a console guarantee. |
| `0x0047f8e0` crossing-time fraction | The decompiler expression is `((planeProjection - previousPositionProjection) * rawDelta) / (currentPositionProjection - previousPositionProjection)`, gated by `currentPositionProjection - previousPositionProjection >= 0.01`. The same fraction is computed in another forward-side branch even without the node-index change. | Literal algebra is directly visible; names “plane projection” and “rawDelta” are descriptive interpretations. The referenced global at `_DAT_00e22a48` is treated as the raw frame delta based on surrounding source, but must remain an explicit dependency until independently mapped. |
| `0x0047f8e0` backward traversal | Only if no forward flag was set and the state at `+0xd0` is zero, decrements cursor parameter by `0.01`, refreshes the frame, and continues while the position is on the opposite side. Sets the backward output when that side test is met; if state remains zero, it adds `0.01` back once after the loop. | Direct stepping and branch structure. Do not simplify this into a symmetric inverse of forward traversal: the loop/state tests differ. |
| `0x0047fbb0` binding refresh | Returns 0 by default. If current mesh pointer `+0x140` differs from stored association `+0xec`, both are non-null, and flag `0x20000000` at `+0x64` is clear, it checks a mesh-related byte flag; if bit `0x08` is set, returns `-1`. Otherwise marks refresh as 1. If a short at mesh offset `+0x3c` is nonzero, calls a cursor/node adjustment routine and then cursor advance; afterward refreshes association, cursor-derived scalar, and two cursor-derived vectors. | Direct gates/return values. The exact semantic meaning of the short and refreshed fields is not fully established. One call passes aliased local addresses to output parameters, so do not infer independent outputs from that call site. |
| `0x0047fca0` track-relative direction | Projects racer position relative to the cursor frame, computes a displacement and its length, stores length at `+0x124`; if length is greater than `0.1`, normalizes the displacement into `+0x118/+0x11c/+0x120`. Otherwise stores fallback direction `(0,0,1)`. | Direct math/threshold; “lateral/track-relative” is an interpretation of the frame/projection usage. |
| `0x0047ffb0` caller/orchestration | Calls cursor advance, saves prior mesh association, refreshes cursor-derived association/scalar/vectors, calls binding refresh then direction calculation, and invokes lap completion with a gate derived from the forward flag or binding result. Resets a counter when the cursor node changes; increments/reset counters according to the two cursor outputs. | Direct call sequence. Decompiled parameter reuse/aliasing means exact names for forward/backward and gate inputs must be validated against a typed reference before reimplementation. |
| `0x0047fdd0` lap completion | Independent of the cursor routine: stores prior progress, reads current progress, updates idle counter, applies the `0.8/0.1` crossing gate and open/closed-route branch. | Previously cross-checked against readable PC reconstruction; still not GameCube/Wii evidence. |

### Contract-test matrix (proposals only; not executed)

1. **Output initialization:** every call begins with forward = 0, backward = 0, crossing-time = 0; exercise forward, backward and no-step outcomes.
2. **Forward stepping:** position remains beyond successive node planes; verify parameter increments by `0.01` per traversal iteration and stops when the plane-side condition fails.
3. **Node boundary:** make the node index change without wrapping to zero, then wrap to zero; only the latter branch is eligible for the node-zero crossing-time calculation.
4. **Crossing-time guard:** projection delta just below `0.01`, exactly `0.01`, and above it; verify zero versus the fraction formula. Also test the non-node-change forward branch.
5. **Backward gating:** no forward flag + state `+0xd0 == 0`; compare state zero/nonzero and verify the final compensating `+0.01` occurs only under the decompiled condition.
6. **Binding no-op:** same mesh pointer, null pointer(s), and exclusion flag `0x20000000`; expect no refresh (`0`) from this function.
7. **Binding blocked mesh:** eligible mesh with byte bit `0x08` set; expect `-1` and no subsequent refresh in that call.
8. **Binding successful refresh:** eligible changed mesh with mesh short at `+0x3c` equal to zero and nonzero; assert return `1`, and treat cursor-adjust/advance side effects separately.
9. **Direction fallback:** displacement length at or below `0.1` gives `(0,0,1)`; above `0.1` yields normalized displacement.
10. **Caller integration:** stub cursor advance/binding independently and verify the lap-completion gate from the actual caller after resolving the aliased parameters. Do not write this test against guessed parameter names.

### Implementation boundary

This matrix is sufficient to design a small, source-derived PC contract harness, but not to implement console-faithful traversal yet. Before coding traversal, resolve the aliased output arguments in `0x0047ffb0`, map the frame/global `_DAT_00e22a48`, and establish a typed representation for cursor fields. Keep this as reverse-engineering work (80% of effort); no gameplay implementation is authorized by this note. No proprietary code or game assets are copied into Boonta.


## Timing-global provenance check (2026-10-20)

Follow-up to the cursor matrix: the pinned Steam-PC decompilation's `FUN_00480540` in `c/FUN_00480540.c` writes the double `dVar1` into the global pair `_DAT_00e22a4c:_DAT_00e22a48`. On the ordinary timing path, `dVar1` is computed from `timeGetTime() - DAT_0050cb60` multiplied by `_DAT_004adf80`; the separate frame-delta variable `_DAT_00e22a40` is clamped to at most approximately `0.1` and floored to approximately `0.002` on the normal path. The cursor-crossing formula casts `_DAT_00e22a48` to float, so the best current interpretation is that it uses the stored, un-clamped elapsed-time value rather than the separately clamped frame delta.

**Caveat:** the routine has alternate timing/freeze branches, and the double-global reconstruction plus decompiler typing needs care. This establishes the variable's write path, not a universal guarantee that every cursor call receives a raw elapsed delta under every mode. Test proposals should compare ordinary, long-frame/clamped, paused/frozen and alternate timing modes before naming this input simply `rawDelta`.

No gameplay code changed; this is source-level evidence only.


## Cross-platform source audit — PC, Nintendo 64, and platform documentation (2026-10-20)

This audit adds sources relevant to the original game and its platform context without treating a manual, a general SDK manual, or a PC decompilation as proof of N64/GameCube internals. It extends RE-001's evidence ledger; it does not open a second implementation task.

### Source hierarchy and what each source can establish

| Source | Source class | Evidence usable for this dossier | Does **not** establish |
|---|---|---|---|
| [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab) at pinned commit `a9863edd4caaa573f89ff634fa7d1cd6d41738ab` | Public PC decompilation/reimplementation research | PC spline structures, cursor routines, known TODO boundaries and named symbols at that revision | Retail N64 or GameCube implementation parity; fully functional end-to-end PC route advancement |
| [Frozen Steam-PC Ghidra decompilation](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef) at pinned commit `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef` | Secondary, frozen binary-analysis artifact | Additional PC function bodies and hypotheses to cross-check against the readable PC reconstruction | An authoritative original source tree, console behavior, or permission to copy implementation; no root license was identified in the earlier audit |
| [N64 instruction booklet scan listing](https://emulation64.fr/?id=Star+Wars+Episode+I+-+Racer&page=notices) | Scan of a retail user manual hosted by a third party | The manual's contents can ground player-facing controls, modes and published game descriptions after page-level inspection | Internal route data, collision logic, AI implementation, or exact code equivalence with PC |
| [StarWars.com / Lucasfilm interview with producer James Vicari](https://www.starwars.com/news/star-wars-episode-i-racer-interview) (2020-04-16) | Official editorial interview | Confirms the N64 game's place in the release history and that the later Switch/PS4 rerelease deliberately modernized controls | The precise N64 route/progress algorithm; it is not a technical design document |
| [Nintendo 64 Programming Manual archive](https://ultra64.ca/resources/documentation-test/) and [execution overview](https://ultra64.ca/files/documentation/online-manuals/man/pro-man/pro03/03-01.html) | Archived Nintendo SDK documentation | General N64 CPU/RCP architecture and development constraints that may contextualize a future binary/hardware investigation | Any Racer-specific spline, AI, lap counter, collision or asset format |
| [N64 Advanced Player's Reference](https://gamefaqs.gamespot.com/n64/198780-star-wars-episode-i-racer/faqs/22256) | Community-authored guide (dated 1999; author disclaims affiliation and accuracy guarantee) | Candidate player-observable differences to reproduce and verify in the actual N64 game; the guide says some material was derived from the game using a cheat code | Official documentation or source-level certainty; statements must be verified against a real game session before becoming acceptance criteria |

### Confirmed platform-level observations

1. The official StarWars.com interview identifies *Episode I: Racer* as a Nintendo 64 title and describes the 2020 rerelease's controls as intentionally modernized. This confirms that control behavior is a platform/release dimension worth tracking; it says nothing about spline internals.
2. The N64 manual scan's table of contents includes controller configuration, gameplay, game setup, two-player mode, planets and podracer characteristics. These are appropriate sources for a future **observable-behavior** checklist, not for inferring internal algorithms.
3. The 1999 N64 player reference reports at least one gameplay difference between N64 and PC on the Abyss course: on N64, competitors reportedly remain on the upper scaffold route if the player drops to the lower route, whereas on PC competitors reportedly follow the player down. This is a useful **unverified test candidate** only. It is community documentation, not an official assertion; confirm in retail builds before using it as a compatibility requirement.
4. The same community guide describes N64-only dual-controller mode and rumble behavior. Treat these as candidate N64-specific observable features, not as requirements for the clean-room GameCube prototype unless the project's target scope explicitly includes them.
5. The archived Nintendo SDK manuals explain generic platform architecture. They cannot bridge the evidence gap between the PC source and the retail N64/GameCube binaries by themselves.

### Consequence for RE-001

- **PC implementation model:** linked spline graph, branch-aware cursor and sampled progress tables are supported by the pinned PC research sources, with unresolved callback and end-to-end execution gaps already recorded above.
- **N64 behavior:** no N64 executable, disassembly, symbol map, or game-specific technical source has yet been examined in this dossier. Manual and community-guide evidence is limited to player-visible behavior.
- **GameCube/Wii behavior:** no source-specific parity has been demonstrated. The existing prototype remains a clean-room comparison target, not a proxy for the original console implementation.
- **No cross-platform transplant:** do not copy PC spline structures or assumptions into Boonta's GameCube code merely because the games share a title. First gather version-specific evidence and state exactly what it proves.
- **Next step within the existing RE-001:** finish the current PC cursor/binding evidence review and record unresolved items; then, if the dossier's completion criteria still require it, perform a controlled player-visible comparison against a legally obtained N64 copy and record build/region, hardware or emulator/version, course, starting conditions, observations and repeatability. Do not start that comparison by changing gameplay code.

No game ROM, executable, asset, or proprietary implementation was copied into Boonta during this source audit.


## RE-001 closeout — evidence status (2026-10-20)

**Disposition: PC-reference analysis documented; dossier closed for this pass. Console parity and several PC internals remain explicitly unverified.** Closing this pass means the current evidence has been organized and its limits recorded; it does not mean the original game's route system has been fully reconstructed.

| Item | Status | Closure statement |
|---|---|---|
| PC spline data, curve families and linked cursor model | **Documented from pinned PC sources** | The PC reference supports linked control-point traversal, branch selection, position/tangent/up evaluation, and multiple curve families. |
| PC progress-table build | **Documented at algorithm level** | The frozen Steam-PC decompilation supports sampled-distance progress tracing and a separate cursor-parameter sampling pass. Exact semantics of some fields remain inferred. |
| PC cursor advance / mesh binding / track offset | **Partially documented** | Branch conditions, increments, thresholds and call relationships are recorded. Decompiled aliases, unnamed fields, and callback writes remain unresolved where noted above. |
| End-to-end original PC route-progress execution | **Not confirmed** | The readable reconstruction contains TODO/HANG stubs in the progress path; source-level helper logic is not proof of a working end-to-end runtime. |
| Current clean-room GameCube prototype | **Mapped for comparison** | The prototype's sampled closed curve and distance/lap model are identified. They are comparison facts about this repository, not proof of original GameCube behavior. |
| Retail N64/GameCube/Wii route algorithm | **Unverified** | No platform-specific executable/disassembly or controlled retail runtime observation in this pass establishes internal parity. Manuals and community guides only provide limited player-visible leads. |
| Step 102 archive | **Non-blocking historical context** | It is not the original game or an authoritative platform source tree; recovery or deletion is not needed to close this research pass. |
| Implementation / tests | **No gameplay changes authorized or made** | Keep this pass research-only. Any future contract harness must be labeled PC-reference testing, not console acceptance testing. |

### Targeted output-parameter alias audit — continuation (2026-10-20)

A direct read of the frozen Steam-PC decompilation's [src/_text23.c](https://github.com/DeonPoncini/swep1r_decomp/blob/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef/src/_text23.c) makes the aliasing more precise:

- In `FUN_0047ffb0` (the per-racer progress caller), `FUN_0047f8e0` receives the frame-crossing output pointer plus `&param_2` and `&param_1` as its two integer output pointers. Those two output destinations are distinct local parameter slots. The caller first preserves the racer pointer in `iVar1`, so later writes to the local `param_1` do not replace the preserved racer reference. Do **not** describe these two output destinations as aliasing each other.
- In `FUN_0047fbb0` (the spline-binding routine), the same helper is called with `&param_1` for **both** integer output pointers. This is genuine output-target aliasing. The helper initializes both outputs to zero and can set the forward and backward indicators to one; because both pointers target the same local slot, the separate indicators cannot be recovered from this call. The binding routine does not subsequently read those local indicators, so this observation does not establish a gameplay defect.
- The helper's frame-crossing output remains a separate float output; its line-plane calculation and the direction flags are not interchangeable concepts.

**Evidence boundary:** the frozen PC decompilation establishes these call-site storage relationships. It does not prove that the same ABI, callers, or behavior exist in N64/GameCube/Wii builds. This narrows the aliasing description but does not justify assigning semantic names to every recovered field or changing gameplay code.

### Remaining uncertainty boundaries

- Keep the two call sites distinct: 0x0047ffb0 passes two distinct local output slots; 0x0047fbb0 passes the same local slot for both direction outputs. Preserve uncertainty about semantic field names and platform parity.
- Do not claim the writes performed by callbacks at 0x0047ea20 or 0x0047ece0; their standalone bodies remain unavailable in the pinned snapshot.
- Do not claim N64/GameCube/Wii parity from PC code, manuals, generic SDK documentation, or a community guide.
- Do not treat proposed boundary cases as executed tests. They are a future test design only.

**Next action:** stop work on RE-001 for now and retain this dossier as the recorded result. No RE-002 work, no gameplay-code change, no new parallel task, and no PR merge as part of this closeout.


## Platform-source search pass — N64 and Dreamcast boundary (2026-10-20)

This pass searched public project/repository descriptions for an N64- or Dreamcast-specific decompilation/reimplementation of *Star Wars Episode I: Racer*, then checked the known OpenSWE1R project descriptions to avoid misclassifying PC work as console evidence.

### Results that can be stated

- The principal public reverse-engineering project surfaced, [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE), explicitly targets the Windows PC game and says its aim is selected-function documentation/reimplementation, not a complete decompilation. Its reported analysis percentage is not completed engine coverage. The Steam Ghidra snapshot is also explicitly from the Steam PC version.
- [OpenSWE1R](https://github.com/OpenSWE1R/openswe1r) describes itself as a Windows-PC implementation using a subset of Windows API emulation and x86 emulation, and says Mac/Dreamcast/N64 support might be added later. It is not evidence of an existing N64 or Dreamcast route implementation.
- [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) does contain a utility described as decompressing a model-block chunk found in the N64 version. That is a narrow format/tool lead, **not** an N64 engine decompilation, a spline parser, or proof of route behavior.
- The public search pass did **not** surface a dedicated N64 or Dreamcast decompilation with route/spline source. This is a search result, not proof that no private, unindexed, forum-hosted, or differently named research exists.

### Decision for RE-001

Do not infer console route topology, progress fields, endianness, cursor stepping, or lap-crossing behavior from the PC source or a generic N64 model-block decompressor. Current evidence supports a PC graph/cursor model and a separate Boonta closed-loop test harness; **the GameCube/Wii/N64/Dreamcast mapping remains unverified**.

The next highest-value action is to inspect available, lawfully obtained target-version metadata and file headers locally, if a clear-provenance sample is available, without uploading or committing the binary/assets. The goal would be to establish whether a route/spline structure can be identified on the target platform before attempting any parser or runtime change. If no suitable target-specific sample is available, keep the uncertainty explicit and finish the PC-derived route behavior matrix rather than inventing console facts.

Sources checked during this pass:
- [SW_RACER_RE README](https://github.com/tim-tim707/SW_RACER_RE)
- [OpenSWE1R README](https://github.com/OpenSWE1R/openswe1r)
- [OpenSWE1R tools README](https://github.com/OpenSWE1R/swe1r-tools)
- [Frozen Steam PC decompilation README](https://github.com/DeonPoncini/swep1r_decomp)

## Supplemental N64 sample probe — local ROM container evidence (2026-10-20)

**Scope and handling.** A locally available, user-supplied N64 image was inspected for header/container metadata only. The commercial ROM, decoded art/audio/geometry, and any derived assets were not written into the repository. This is a narrow continuation of RE-001's stated next step (inspect a target-version sample), not evidence that the GameCube/Wii format is now understood.

### Header identification

- File size: 33,554,432 bytes (32 MiB).
- Header magic: `80 37 12 40`, the canonical big-endian `.z64` representation described by the public [N64 `tool64.c` header/format code](https://github.com/DylanJ/n64/blob/master/tool64.c).
- Internal title: `STAR WARS EP1 RACER`.
- Cartridge/game ID: `EP`; country code: `E`; revision byte: `0`. The public header reference maps `E` to North America/USA; see [the cartridge-ID and region notes](https://sources.debian.org/src/mame/0.251%2Bdfsg.1-1/hash/n64.xml).
- This identifies the supplied file as an N64 release candidate for analysis. It does not establish parity with PC, Dreamcast, retail GameCube, or Wii runtime behavior.

### `CompWolf` block-framing result

The ROM scan found **92** `CompWolf` markers. A temporary in-memory decoder following the framing and 4 KiB LZ77-window behavior documented in [`swe1r-tools/decompress.c`](https://github.com/OpenSWE1R/swe1r-tools/blob/master/decompress.c) successfully reached each block terminator, and every decoded output length matched the length declared in that block's header. Decoded payloads were not exported to files or committed.

Reading only each decoded payload's first four-byte tag yields:

| Tag | Blocks | Total decoded bytes |
|---|---:|---:|
| `Trak` | 19 | 9,385,848 |
| `Pupp` | 27 | 1,789,844 |
| `Part` | 44 | 680,588 |
| `Scen` | 2 | 119,332 |
| **Total** | **92** | **11,975,612** |

The `Trak` payloads have structured-looking internal headers and repeated labels including `Data`, `LStr`, `Anim`, and `HEnd`. These are observations about chunk framing, not semantic field names. The top-level scan did not identify a dedicated `Spli`/`Spline` chunk tag; route data may still be embedded in binary sections of a `Trak` payload.

### What this does and does not establish

**Established:** the supplied N64 image contains many correctly framed `CompWolf`-compressed blocks; the published decompression routine is a credible component for processing a block once its start is known; and 19 top-level payloads are tagged `Trak`.

**Not established:** a ROM-level file/index table, the mapping from those 19 chunks to named courses, the internal `Trak` section schemas, which substructure stores route-control points, or any equivalence to PC `out_splineblock.bin`. The public utility is a **single-chunk decompressor**, not a complete ROM unpacker or N64 spline parser. A tag named `Trak` must not by itself be equated with route logic.

### Next step within RE-001

Continue read-only analysis of the `Trak` section/offset tables and validate any candidate structure across at least two differently sized `Trak` chunks. Only then decide whether a small, clean-room metadata parser is justified. Keep the sample ROM and all decoded assets outside Git; no new implementation or asset-import PR is justified by this probe alone.

**Emulator clarification:** Wii64 is an N64 emulator, not a separate native edition of *Episode I: Racer*. A Wii64 compatibility-list entry is evidence only of an emulation test under the named emulator/configuration, not of a native Wii port or identical internal data layout; see the [community Wii64 compatibility list](https://wiki.gbatemp.net/wiki/Wii64_Compatibility_List).

## N64 Trak block-grammar cross-check against the PC model reader (2026-10-20)

This is a follow-on to the local N64 container probe above. It strengthens the structural result while deliberately stopping short of claiming that the N64 route/spline system has been found.

### Cross-check result

The 19 N64 `Trak` payloads were checked with an independent, read-only structural validator based on the *documented grammar* in the pinned [`blender-swe1r/modelblock.py`](https://github.com/OpenSWE1R/blender-swe1r/blob/b0dfb8bc0437f783d86fe7824fd8703fa8ab55ce/modelblock.py). No third-party implementation was copied into Boonta.

- **19/19** payloads matched the model header envelope: a `Trak` signature, six 32-bit header-offset slots followed by the `0xFFFFFFFF` sentinel, optional `Data`, `Anim` pointer list(s), and `HEnd`.
- **11/19** contain a `Data` section. Its declared size is counted in 32-bit words, matching the reference reader's convention. The sections contain **220 `LStr` records in total**, each occupying 16 bytes, with no unrecognized four-byte words in those sections.
- The `Anim` lists are terminated by a zero pointer. This check validates list framing and pointer bounds, not the semantic meaning or correctness of every animation payload.
- The post-`HEnd` tree walk encountered **5,694 unique group/model nodes** and **9,536 references from mesh-group nodes to mesh records** across the 19 blocks. All visited node types fell within the type set recognized by the pinned reference reader; no node, child-list, or mesh-reference address crossed its containing decoded `Trak` block boundary.

Reference source locations: [accepted model extensions and offset-table / section reader](https://github.com/OpenSWE1R/blender-swe1r/blob/b0dfb8bc0437f783d86fe7824fd8703fa8ab55ce/modelblock.py#L1000) and [`LStr` / `ModelData` handling](https://github.com/OpenSWE1R/blender-swe1r/blob/b0dfb8bc0437f783d86fe7824fd8703fa8ab55ce/modelblock.py#L900). The specific line anchors are navigation aids to the pinned file; the source revision is the commit named above.

### Important semantic correction: `LStr` is not a race spline

The reference reader's `LStr` class reads three big-endian floats and its display routine creates a Blender point light named `lightstreak`. Therefore, in this tool's documented interpretation, `LStr` represents a light-streak position—not a route-control point. This evidence explicitly **does not** identify route centreline, branch, lap-progress, or checkpoint data inside these `Trak` `Data` records.

### Decision

The N64 `Trak` outer model/scene-graph grammar is structurally compatible with the grammar described by this PC-oriented reader for the portions tested. This is a strong format-reuse lead for a **local, non-redistributed N64 track-model inspection/conversion experiment**, but it does not prove full geometry/animation conversion, runtime equivalence, or that the game's route spline format is shared. The parser is GPL-3.0-or-later and remains read-only; do not copy/adapt it into Boonta without a separate licensing decision. Keep the commercial ROM and any decoded game assets out of Git.

### Next evidence target

Keep the research question narrow: identify a separate route/progress representation or locate route-related structures among the N64's remaining decoded payloads without guessing that `Trak`/`LStr` means spline. Any future parser should be independently authored, host-tested on at least two blocks and several malformed cases, and keep decoded proprietary assets local.

## N64 model-block and mesh-reference validation across all decoded chunks (2026-10-20)

A further clean-room validator was run over all 92 decoded model payloads, without exporting geometry or copying third-party code. It follows the block and mesh field layout described in the same pinned, GPL-3.0-or-later reference file. This is an offset/bounds validation, not a visual import test.

### Aggregate result

| Block extension | Count | Group/model nodes walked | Mesh records referenced |
|---|---:|---:|---:|
| `Trak` | 19 | 5,694 | 9,536 |
| `Pupp` | 27 | 1,418 | 772 |
| `Part` | 44 | 134 | 1,129 |
| `Scen` | 2 | 278 | 57 |
| **Total** | **92** | **7,524** | **11,494** |

For every payload, the generic header/section parser reached `HEnd`; the scene-graph walk found recognized node types and in-bounds child lists. For all **11,494** mesh records, the validator checked the 64-byte mesh-header boundary and bounds for non-null material headers, texture/shader headers, collision tags, strip tables, collision-vertex buffers, visual-vertex buffers, texture sub-chunk pointers, and visual index streams. All index streams encountered used the command types supported by the reference reader (`1`, `3`, `5`, `6`) and had an in-block terminator (`223`); the tested triangle indices and vertex-buffer starts stayed within their referenced visual-vertex buffers. The 9,305 non-null texture references were also checked against the decoded block bounds.

**Outcome: zero structural, pointer-boundary, unknown-node-type, or index-stream errors in this validator.** That is strong evidence that the N64's 92 decoded `CompWolf` payloads use the same broad model-block/node/mesh representation expected by the PC-oriented reader. It supports a local conversion feasibility experiment far more strongly than a matching FourCC alone would.

### Evidence limits and use decision

- This validation does **not** instantiate Blender, render an imported model, compare exported geometry visually, or prove that every material/shader/texture payload has identical semantics on PC and N64.
- It does not identify the race spline/route graph or prove that N64 lap progress is stored in these model blocks.
- The GPL-3.0-or-later Blender add-on remains a read-only reference. No code from it was copied into Boonta; the decoded commercial game assets remain local and are not committed.
- The next implementation-sized experiment, if a visual conversion is needed, is to run the existing tool locally against one legal N64-derived `Trak` sample and record import/render errors without republishing the asset. In parallel, continue looking for a distinct route/progress structure instead of repurposing `LStr` light-streak positions.

## N64 spline schema cross-check and extraction gap (2026-10-20)

The critical new source is [`akopetsch/swe1r-assets`](https://github.com/akopetsch/swe1r-assets), pinned at commit `922ef535f6598a1330ff93d6b07258956f990b34`. The repository is MIT licensed and has an explicit `SplineBlockItem` reader that deserializes and reserializes `out_splineblock.bin`. Its metadata enumerates a dedicated **N64** spline-block variant; its original-resource manifest lists `out_splineblock.bin/n64.bin` with SHA-1 `a18f0c66301cf0e11feedafadc1b374fa3b40ed6`. That manifest proves the community has identified a named N64 spline-block reference, not that the block is already located in the supplied ROM or that its bytes may be copied into this project.

### Cross-check of the per-point record

Pinned source files:
- [Spline root](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/Spline.cs)
- [Spline segment data](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentData.cs)
- [Spline segment header](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentHeader.cs)
- [Spline-block deserializer/serializer](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineBlockItem.cs)

The schema's serialized `Spline` root has a header followed by a list whose count is read from `Header.ElementsCount`. Each `SplineSegment` serializes a data record and a 16-byte segment header. The data portion contains eight 16-bit words at offsets `0x00..0x0e`, a three-float vector at `0x10`, one explicitly positioned float at `0x24`, two three-float control vectors at `0x28` and `0x34`, and a 32-bit field at `0x40`. Together the declared data and segment-header fields occupy `0x54` (84) bytes. A separate read-only community parser independently uses a 16-byte spline header followed by 84-byte point records and exposes next/previous link counts, position, orientation, two control handles and progress-related words; see [`SWE1R-Mods/tools/block.js`](https://github.com/louriccia/SWE1R-Mods/blob/a0c55e301a01ce0212b2146a280782cacab155e6/tools/block.js). This is good layout-level corroboration. The field names/semantics are not perfectly settled across the two parsers, so do not promote every word to a confirmed meaning.

### The actual extraction gap

The public unpack script in `SWE1R-Mods` explicitly expects an already-extracted `out_splineblock.bin` from the PC-style `data/lev01` folder. The MIT `swe1r-assets` deserializer also accepts the block file; neither one, as inspected here, supplies the missing **retail N64 ROM → extracted spline-block** stage. The N64-specific checksum/metadata entry is a strong evidence lead, not a license to use its bundled game-derived bytes as Boonta content.

**Therefore the next task is narrowed to a read-only extractor investigation:** determine whether the N64 spline block can be recovered from the user's supplied ROM via the known asset/index layout, a ROM-specific offset table, or a documented community extractor. Do not infer that the 92 top-level `CompWolf` model chunks include the spline block; they have model-block signatures, and the route data has not been found inside them. If no extraction path is evidenced, implement only a small clean-room scanner over the user's local ROM with conservative bounds checks and tests against the documented 84-byte schema; do not import commercial asset bytes or GPL parser code.

## Exact N64 spline-block recovery from the supplied ROM (2026-10-20)

**The extraction question from the preceding section is now resolved for this supplied N64 ROM.** A read-only scan found the full N64 spline-block archive in-place inside the user's ROM, and the SHA-1 of that region exactly matches the public reference checksum in the pinned `swe1r-assets` [original-resource checksum manifest](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original/Resources/checksums.sha1).

| Check | Verified result |
|---|---|
| ROM archive start | `0x012C7F30` |
| End (exclusive) | `0x013307E4` |
| Archive length | 428,212 bytes |
| SHA-1 of that ROM region | `a18f0c66301cf0e11feedafadc1b374fa3b40ed6` |
| Pinned public reference | `a18f0c66301cf0e11feedafadc1b374fa3b40ed6  out_splineblock.bin/n64.bin` |
| Archive items | 91 |
| Total route points | 5,076 |
| Outgoing point-to-point links | 5,174 |
| Structural/link issues in the scan | 0 |

The archive table's first data offset is 372 bytes, exactly `(91 + 2) * 4` for a count word, 91 item-start offsets, and a final end offset. Each of the 91 item spans matched `16 + 84 * point_count` exactly. Across all points, next/previous counts were within the schema bounds, active next/previous indices were in-range, every outgoing edge had the corresponding reciprocal incoming link, all parsed coordinates/handles were finite and reasonably bounded, and all point rotations were `(0, 0, 1)`. The candidate contained no malformed sizes, invalid active links, or non-reciprocal links in these checks.

The matching checksum is decisive identification of the public N64 spline-block asset—not just a plausible byte pattern. It confirms that the game-specific route/control-point data is present in the supplied ROM at this location, and the MIT parser's block/record schema is applicable. The earlier section's extraction-gap assessment is superseded for this exact N64 image.

### Handling and remaining validation

The scanner and checksum calculation worked directly against the user's local ROM bytes. The spline archive or individual point/track assets were **not exported as files, committed, or added to Boonta**. Future work may create an independently implemented, bounds-checked, metadata-only reader and tests; do not copy GPL code from `blender-swe1r` / `swe1r-tools`, and do not copy or redistribute the bundled game-derived binary in the reference repository. Attribute the MIT schema source if its parser code is reused.

### Next technical milestone

Use point-level coordinates and adjacency metadata to validate route layout against the corresponding N64 `Trak` geometry, first on one course and then on additional courses. This should produce evidence about route-to-mesh alignment and branch topology. Keep route-path semantics, checkpoint/lap progression, and cross-platform equivalence labeled separately: structure and checksum are confirmed, but gameplay has not been tested from this parser output.

## Route-graph validation and compatibility with Boonta's neutral track schema (2026-10-20)

A deeper in-memory topology pass was performed on the recovered archive. No per-point coordinates or source asset files were written to disk or committed.

### Graph invariants

- **91 spline items:** 50 are closed graphs and 41 are open, with exactly one source point and one terminal point in each open item.
- **5,076 points** overall; every item length exactly fits its header count and the 84-byte record size.
- **5,174 outgoing adjacency edges** were read. Every active edge index is within the corresponding spline's point range, and each outgoing edge appears exactly once in the destination point's incoming-list slots. There were no malformed counts, non-finite vectors, broken reciprocal links, or out-of-range active indices.
- The root header's `segment_count` needs careful interpretation: on the 50 closed graphs it equals the outgoing-edge count; on each of the 41 open graphs it equals the point count, one more than the outgoing-edge count. Across the archive the header counts total 5,215, while the adjacency lists contain 5,174 edges. Do **not** treat the field as a universal edge counter without considering open vs closed topology.
- The first 8 shorts of a point record encode the link counts and indices plus two not-yet-unambiguously named slots; points carry a position vector and two 3D curve handles. All rotations in the recovered sample were `(0, 0, 1)`, consistent with the public parser's documented interpretation. That does not prove every runtime use of the fields.

For the route item whose public block metadata labels it `Trak_Tatooine_Boonta_Classic`, the corresponding size/count structure is 180 points and 187 outgoing links. The graph has **7 split points and 7 matching join points**. This is the first strong example for designing/test-driving branch support. The label is a cross-reference to community metadata, not a claim that cross-platform gameplay semantics have been confirmed.

### Compatibility gap in the current Boonta format

The clean-room `boonta-track-v1` schema is a single ordered point array with world-space `x/y/z`, `half_width`, optional `checkpoint`, and a `closed_loop` flag. The current GameCube demo samples that list as a Catmull–Rom curve. It does not encode explicit directed next/previous links, alternative branch/join topology, the two source curve handles, or the source's per-point progress metadata. Therefore the recovered course graph cannot be represented losslessly by `boonta-track-v1`; flattening it would remove shortcuts and merge behavior.

There is also no verified scale/axis transform from the N64 route-coordinate system to `boonta-track-v1` metres yet. Do not copy numeric coordinates into the public `example_track.json` or generated header.

### Next smallest implementation target

Once the current first playable circuit acceptance gate is met, use **synthetic, original test fixtures only** to prototype a platform-neutral route graph representation with:
1. explicit point IDs and directed links;
2. closed-loop vs point-to-point detection;
3. curve handles and interpolation type kept distinct from link topology;
4. a normalized progress/checkpoint abstraction decoupled from raw source field names;
5. malformed-graph tests (missing target, duplicate edge, mismatch between counts and lists, open endpoint, cycle wrap and split/rejoin).

Do not import this ROM-derived graph or extracted coordinates into the public project; this milestone is schema/behavior research, not an asset import. Preserve the existing `boonta-track-v1` oval for the first playable vertical slice until there is a tested migration plan.

## PC runtime route traversal: branch cursor and lap-progress evidence (2026-10-20)

Reference snapshot: [`SW_RACER_RE/src/Swr/swrSpline.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caa/src/Swr/swrSpline.c), [`swrSpline.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caa/src/Swr/swrSpline.h), and [`swrRace.c`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caa/src/Swr/swrRace.c). This public codebase is a partial reverse-engineering/reimplementation, not a complete verified retail source; the notes below separate implemented-looking reconstructed functions from explicit TODO/HANG stubs.

### Route cursor behavior visible in the reviewed code

- A runtime cursor carries four look-ahead node IDs, a segment parameter `segmentT`, a signed velocity, start/end flags, a branch selector and branch flags. The layout is declared in [`src/types.h`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caa/src/types.h).
- The cursor-step routine follows the indexed outgoing or incoming links and shifts the look-ahead window at each node crossing. For Bezier-style segments, the interpolator uses the current point's outgoing handle and the next point's incoming handle; B-spline mode instead uses four successive point positions. It also computes tangent/up vectors used to form the racer orientation. This supports a **graph + interpolation + cursor** model, not a simple polyline as the full runtime representation.
- The branch selector chooses among available next links. The AI section of `swrRace.c` assigns a random binary choice and contains signature-track scripts that force main-line or alternate choices in lap-progress windows. That is evidence about the reconstructed PC AI path, not proof the N64 release uses the same policy.
- `swrRace_LapProgress` combines a baked per-node base-progress value with the segment parameter times that segment's progress span. On closed tracks it caps progress below 1.0 so the finish-line wrap can be detected; open tracks can clamp to 1.0. `swrRace_LapCompletion` compares current/previous/high-water progress and unwraps values around the start/finish boundary to recognize crossings.
- `swrSpline_CursorSeekToProgress` uses `progress / 10` as a band/node index and the remainder as the segment parameter, with a branch-field lookup for progress bands that exceed direct point indices. Treat this as a serialized/runtime progress mapping in the PC code under review; do not assume the same scale directly applies to N64 or GameCube without tests.

### Critical limitations in the public PC source

The following relevant functions remain explicit TODO/HANG stubs in this reviewed snapshot: `swrSpline_ProjectPointStub`, `swrSpline_CollectNearbyPoints`, `swrRace_AdvanceSplineCursor`, `swrRace_UpdateSplineBinding`, `swrRace_ComputeTrackOffset`, and `swrRace_GetTrackMeshAtCursor`. The `swrSpline.h` declares `swrSpline_TraceProgress` and `swrSpline_BuildProgressTable`, but their bodies are not present in the reviewed `swrSpline.c` file. A few functions also deliberately preserve known retail stubs, e.g. project-point projection always returns zero in this source's model of retail behavior.

**Conclusion:** branch cursor and lap-completion *structure* is well evidenced in the PC research snapshot; the full algorithm that advances a vehicle cursor through a track and bakes per-node progress is **not yet verified end-to-end** from this public source alone. Do not treat the comments around these stubbed call sites as completed executable proof.

### Implementation consequence for Boonta

The clean-room engine should keep these concerns separate in any future neutral schema:
1. route topology (directed point IDs, next/previous edges, open/closed paths);
2. interpolation mode and control handles;
3. a cursor (active segment, parameter, branch choice/history, endpoint state);
4. normalized progress/high-water tracking and start/finish-crossing logic;
5. collision/mesh-binding and off-track/recovery behavior.

This is a design target, not permission to start a broad rewrite now. First satisfy the active one-course playable acceptance gate; then prototype these components against **synthetic graph fixtures** with deterministic tests for split/rejoin choice, open endpoints, closed-loop wrap, backward travel, and lap crossing. Keep N64/PC coordinates and extracted mesh/course payloads local and excluded from public tests.

