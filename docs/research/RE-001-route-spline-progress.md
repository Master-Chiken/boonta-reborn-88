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


### N64 container reconnaissance — preliminary local scan

**Reviewed:** 2026-10-20. **Scope:** private, read-only analysis of the locally supplied US Nintendo 64 image. The image, decompressed chunks, model/texture payloads, and course-coordinate records are not included in this repository.

A scan identified 92 `CompWolf`-prefixed blocks. An independently written local checker used the published `Comp`-block format as a lead and verified that each decoded stream reached its declared output length and terminator. The first four bytes of the decoded blocks grouped as follows:

| Decoded four-byte tag | Block count |
|---|---:|
| `Trak` | 19 |
| `Pupp` | 27 |
| `Part` | 44 |
| `Scen` | 2 |

Across these blocks, the checker produced 11,975,612 bytes of decoded data. The encoded streams consumed 5,869,155 bytes after their headers; the 12-byte `CompWolf` wrapper headers add another 1,104 bytes, for 5,870,259 ROM bytes across the 92 complete block records. These counts are format-validation results, not an asset export or proof that every record's semantics are known.

The `Trak` blocks are heterogeneous. Some contain a leading `Data` section with repeated `LStr` records; each observed `LStr` record is 16 bytes (a four-byte marker plus three finite big-endian floats). Other `Trak` blocks have no `LStr` record in the scan. An initial hypothesis was that these records might describe route geometry, but a follow-up cross-check found public PC-format documentation in [SWE1R-Mods' model-block reference](https://github.com/louriccia/SWE1R-Mods/blob/main/docs/modelblock.md): in PC `Trak` data, `Data` / repeated `LStr` records are documented as light-flare coordinates, not a course centerline. The N64 records match that layout, making **light-flare data the leading interpretation**, while PC-to-N64 semantic equivalence remains unconfirmed. Some sampled record groups are spatially discontinuous, which is also inconsistent with assuming they form one ordered centerline. The 19 `Trak` blocks must not be treated as 19 distinct race courses.

The next useful N64 question is therefore not “how do we turn `LStr` into a spline?” but “does the surrounding `Trak` header and its offset table correspond to the track/model layout described by the PC parser, and where is the actual route representation stored in the N64 build?” The `Anim` / `HEnd` markers and the block's six base-header offsets need a structural comparison, with PC and N64 results kept in separate evidence columns. No PC/N64 byte-layout equivalence is assumed.

The public `[swe1r-tools decompressor](https://github.com/OpenSWE1R/swe1r-tools/blob/master/decompress.c)` and its `[README](https://github.com/OpenSWE1R/swe1r-tools)` note that `Comp` chunks also occur in the N64 edition. That is a useful external format reference, not permission to copy its GPL-licensed implementation or any game data into this project. This scan records structure and counts only; it does not publish an extractor, ROM-derived course geometry, or game assets.

A second cross-check makes the interpretation more specific. The same public PC-format reference documents the six base offsets in a `Trak` model as: track-mesh parent, the same track-mesh parent again, skybox-mesh parent, and three cutscene-camera trackpoint references. The N64 scan shows the same six-word header shape in the **19 compressed `Trak` blocks**: the first two words match, the third is a non-null offset in every inspected instance, and the final three fields contain offsets or nulls. I also found **six additional `Trak` headers outside the `CompWolf` streams**. All six have the same six-offset header, the `0xFFFFFFFF` header terminator, and nearby `Anim` / `HEnd` markers. This gives **25 structurally consistent `Trak` headers in total**, matching the 25 `Trak` entries enumerated by the public PC model-block reference. That matching count and header shape is a strong cross-platform lead, but does not by itself prove a one-to-one course ordering or identical pointer semantics. In the local N64 sample, 12 of these 25 headers have a `Data` section; the two compressed `Scen` chunks also do. This is useful structural evidence for interpreting `Trak` as scene/model records—including mesh and camera references—not as the route spline itself. Runtime use of each pointer remains unverified.

This cross-check also clarifies the next boundary: the PC game loads route splines from a separate `out_splineblock.bin` file, as documented in [OpenSWE1R's level-data access notes](https://github.com/OpenSWE1R/swe1r-re/blob/master/swep1rcr.exe/Level-data-access.md) and [spline loader notes](https://github.com/OpenSWE1R/swe1r-re/blob/master/swep1rcr.exe/Splines.md). The 92 N64 `CompWolf` chunks inspected here are model records; they have not yet revealed the route-point/control structure. The next research target is the N64 executable's course-following path and its data source, not further reinterpretation of the `LStr` lights.

**Next evidence needed:** recover the historical N64 audit notes/tool candidate listed in the earlier Step 102 archive documentation (especially `export_n64_track.py` and the related ROM-track audit reports), or independently trace the N64 route/progress code and its data references. Keep all ROMs and extracted proprietary assets local; publish only the structural findings and independently authored code.


## Strong N64 evidence — native spline block located and structurally validated (2026-10-20)

This pass used the already supplied local US N64 ROM read-only. No ROM bytes, extracted points, coordinates, or track assets were added to the repository.

### Independent block identity

Pinned public reference: [akopetsch/swe1r-assets, commit 922ef535f6598a1330ff93d6b07258956f990b34](https://github.com/akopetsch/swe1r-assets/tree/922ef535f6598a1330ff93d6b07258956f990b34), especially its [block metadata](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Block.csv), [item-to-value mapping](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/BlockItem.csv), and [spline-item metadata](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/SplineBlockItem.csv).

- The N64 spline block is present at ROM file offset 0x012C7F30, length 428,212 bytes (end-exclusive offset 0x013307E4).
- Its SHA-1 is a18f0c66301cf0e11feedafadc1b374fa3b40ed6, exactly matching the public metadata row for the big-endian N64 spline block (n64, 91 items, 428,212 bytes). This exact outer-block hash is the key identity check: the parser is not merely finding a plausible byte pattern.
- The public block container layout is directly visible in Block.cs: big-endian item count, one big-endian offset per spline item, a declared end size, followed by item payloads. For 91 items, the container header is 372 bytes; the remaining 427,840 bytes are the item payloads.
- All 91 records passed the structural size check record_size == 16 + 84 * point_count. Across them, 5,076 candidate point records were parsed; coordinate/control-vector floats were finite. Under the public Blender parser's field interpretation, link counts/indices are in range, every point is reachable from point 0 and incoming/outgoing links are reciprocal. These are **parser-derived topology checks, not yet an independently confirmed semantic result**: see the cross-reader disagreement below.

### Cross-reader disagreement: raw record layout is stronger evidence than field semantics



The MIT reader and the GPL Blender parser have separate implementations of the serialized structure and align on the outer N64 block hash, count/size, 84-byte segment record size, position vector at byte 16 and control vectors at bytes 40 and 52. However, the MIT `SplineSegmentData.cs` and `SplineSegmentHeader.cs` comments explicitly cite the Blender parser as their reference, so they are **not two independent reverse-engineering discoveries**. This is a cross-implementation/layout comparison, not independent confirmation of every field semantic:



- The Blender parser interprets the first eight 16-bit words (bytes 0–15) as outgoing/incoming link counts and link indices; it reads a 3-float rotation starting at byte 28; then labels the 10 halfwords at bytes 64–83 as progress/branch metadata.

- The MIT `SplineSegmentData.cs` instead names those first eight halfwords mostly as unknown words, with `PreviousNodeId` at byte 8. It models a position/knot vector at byte 16, leaves bytes 28–35 without a decoded field, interprets the float at byte 36 separately, models the control vectors at bytes 40 and 52, and names the 32-bit word at byte 64 `Unk_40`. It then models the 16-byte `SplineSegmentHeader` after the 68-byte data record. See the pinned [MIT data model](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentData.cs), [header model](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentHeader.cs), and [Blender parser](https://github.com/louriccia/blender-swe1r/blob/b0d4019addb97d51523019ca1233411fae0508d6/splineblock.py).



This mismatch may mean one tool's semantic guesses are incomplete or wrong; it must not be papered over by assuming names align. The strong conclusions are the exact **block identity and record sizes**, plus stable vector-shaped fields at the noted byte ranges. The 180-point/187-link topology for value ID 110 remains a **candidate interpretation according to the Blender parser**, not a field-by-field cross-validated fact. Before implementing route traversal from these fields, trace the N64 code that reads them or perform a controlled runtime observation. Preserve the raw words and unknown fields in any research representation.

### Record interpretation and the Boonta Classic candidate

The item mapping provides a useful, qualified candidate for the N64 Boonta Classic spline:

- In the common/default metadata, spline block index 10 maps to value ID 10, named Trak_Tatooine_Boonta_Classic, with a record size of 15,136 bytes.
- In the N64 block, index 10 maps to value ID 110. Its record is also 15,136 bytes and its metadata name is the generic placeholder __SPLINE__110, so the N64 metadata itself does not certify the track name.
- The N64 index-10 record's item hash matches the public value-ID-110 hash when the library's actual hash convention is followed. The library calculates a BlockItem hash by hashing the part-hash bytes; for this one-part record that is SHA-1 of the SHA-1 of the raw record. Comparing the raw record SHA-1 directly with SplineBlockItem.csv would incorrectly look like a mismatch.
- The same slot and size, combined with the default slot's explicit Boonta Classic label, make N64 value ID 110 a strong Boonta Classic candidate, but I leave the semantic name provisional until another source or runtime observation confirms it. This remains a structural association, not an assertion about GameCube/Wii bytes.

### N64 value-ID-110 graph facts (no geometry disclosed)

The N64 index-10 candidate has:
- 180 point records and a header-declared 187 segments;
- exactly 187 outgoing links, with 7 points having two outgoing links and 7 points having two incoming links;
- no invalid point indices; every directed outgoing link has the matching incoming link;
- a link back to point 0 (the cycle-closing edge is from point 134 to point 0 in this parser's numbering);
- parser-labelled progress values spanning 0 through 135, with 136 distinct values.

These values support a graph-based route model with alternate branches, not a single unbranched array or a circle generated solely from distance. The progress field name is the Blender parser's interpretation; its exact retail-runtime semantics still need to be confirmed from code and/or controlled play observation. No actual positions, handles, route geometry, or exported asset files are part of this public finding.

### What this changes

The immediate blocker is no longer “locate the N64 spline block.” That question is now resolved at the container/hash/record-structure level. The remaining work is to:
1. correlate N64 value ID 110 to Boonta Classic independently of the shared index/size clue;
2. trace the N64 code path that loads these records and consumes links/progress for cursor movement, finish crossing, and AI;
3. use the N64 findings to specify a clean-room route graph API and synthetic tests, while keeping GameCube/Wii format parity explicitly unverified.

decomp.anything remains useful for code-path analysis (which code reads and uses these records); it is not required to locate or structurally parse this block and is not a one-click circuit exporter. Its N64 code splitter's documented main-segment limitation also means a missing caller is not proof the behavior is absent. No gameplay implementation change is justified by this data-only pass.

### Provenance and implementation boundary

- The MIT swe1r-assets source and GPL-3.0 blender-swe1r parser were read as independent references; no third-party parser implementation was copied into Boonta.
- The retail ROM and its derived geometry remain local. Public repository changes are documentation only.
- Confidence: high for block identity, entry count and 84-byte record accounting; medium-high for value ID 110 being in Boonta Classic's logical slot; medium for the position/control-vector byte ranges shared by both readers; **provisional** for the branching topology derived from the Blender parser; unconfirmed for exact link/progress/orientation semantics, runtime use, and GameCube/Wii serialization parity.

## New independent runtime-validation lead — N64 spline-marker debug option (2026-10-20)

A read-only ASCII string scan of the local US N64 ROM found UI labels “Spline Markers On” and “Spline Markers Off” at ROM offsets 0x000A9050 and 0x000A9064. They sit beside debug-menu labels for AI level/spread, death-speed controls, invincibility, mirrored mode, and vehicle-stat editing. This is evidence that the retail N64 build contains a spline-marker debug toggle; it does not yet prove precisely what the toggle renders or which spline indices it visualizes.

Public references for debug activation: [GameFAQs N64 cheats](https://gamefaqs.gamespot.com/n64/198780-star-wars-episode-i-racer/cheats) and [NESWORLD's N64 debug-menu note](https://www.nesworld.com/n64-hidden-starwarsep1racer.php) describe entering `RRDEBUG` in Tournament mode and the pause-menu D-pad sequence. The published sequence differs between some guides (Left, Down, Right, Up vs. Up, Left, Down, Right), so treat it as a community procedure and not as authoritative format documentation.

**More direct test code found:** [Almar's N64 GameShark code list](https://almarsguides.com/retro/walkthroughs/N64/Games/StarWarsEpisode1Racer/Gameshark/) explicitly lists `Spline Markers On: 800A52D3 0001` (page line 75). The same list includes an in-race cheat menu flag at `8009B7D7` and debug-level value at `8009B7D3`. This is a direct, address-specific lead for emulator testing, not evidence that the marker toggle was already executed or that the address/code behaves identically in every region/revision. The local ROM is the US revision, which best matches the reference context.

### Controlled observation to close the identity gap

On a legally owned US N64 ROM in a compatible emulator, add the single GameShark line `800A52D3 0001` to the emulator's cheat list and activate it for a race. The source lists it as a `Spline Markers On` code but does not explicitly document an Off code; disable/remove the cheat or restore/reset the game state to compare if needed. If direct memory codes are not supported by the chosen emulator, fall back to the RRDEBUG menu sequence and note which D-pad order works.

On the known Boonta Classic course, record only observations: whether markers appear, whether they trace the drivable centerline or alternate branches, whether toggling the cheat changes the scene, and whether the N64 index-10 candidate appears consistent with the visible course. Do not infer a raw record index from screen order alone; the binary itself labels value ID 110 as `__SPLINE__110`, not by a course name.

This provides a possible independent check on the strong slot/size association between N64 value ID 110 and the default Boonta Classic entry. It may also reveal whether the markers show route nodes, control handles, AI routes, or some other spline family. Until tested, those possibilities remain hypotheses. No screenshots, ROM strings beyond short menu labels, marker coordinates or assets were added to the public repository.

### Static cross-reference check of the GameShark address (limited, not a negative proof)

On the local US ROM, a lightweight instruction-pattern scan of the main code span given by the pinned `sp00nznet/racer` reference (ROM `0x1000` to `0x99000`, mapped from VRAM `0x80000400`) found several accesses to nearby global offsets `0x800A52D0`, `0x800A52D4`, `0x800A52D8` and `0x800A52DC`; it did not find a direct main-segment load/store with immediate offset `0x52D3` using the simple `lui 0x800A` + memory-access pattern. This scan was not a full decompiler or whole-ROM overlay scan. The byte may be addressed through a pointer, a `$gp`-relative symbol, or code loaded from another segment; therefore this result is **not evidence that the cheat code is wrong or that the flag is unused**. It only means static identification of the reader remains open and the emulator-visible toggle is the cleanest next check.

## Strong static link from GameShark flag to a conditional render helper (main N64 code)

Using the local US ROM and an ephemeral ELF wrapper for the main MIPS code span (ROM `0x1000`–`0x99000`, mapped to VRAM `0x80000400`), LLVM's MIPS disassembler confirms this call path:

- At VRAM `0x80054124`, the code loads `0x800A0000` into a register; at `0x80054128`, it executes `lw` from offset `0x52D0`, reading the **word at `0x800A52D0`**.
- At `0x80054134`, it branches around the helper when that word is zero.
- When nonzero, at `0x8005413C` the code calls `0x80053AD4`. This is the only direct `jal` to `0x80053AD4` found by scanning the main code span.
- `0x80053AD4` has its own conventional function prologue/epilogue embedded inside the broad auto-generated symbol range `func_80053384`. It runs a render-object preparation loop and calls `render_submit` at `0x800181BC` from inside that loop. The public [symbol table](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/symbols.toml) names `0x800181BC` as `render_submit`.
- Almar's community cheat listing calls the byte write `800A52D3 0001` “Spline Markers On”. On big-endian N64, address `0x800A52D3` is byte `+3` of the word read at `0x800A52D0`; so the cheat byte and the word-tested by the caller line up without requiring code to read address `...52D3` as a separate byte.

**Interpretation:** This is strong static evidence that the community's “Spline Markers On” cheat flag gates an additional rendering helper. The helper is therefore a high-confidence candidate for spline-marker visualization, not just an unrelated string near debug labels. It gives us a direct runtime experiment to perform. We still have not observed rendered markers in an emulator, so it does not by itself prove that the markers are route centerline points, control handles, AI paths or exactly spline item 110.

**What remains unresolved:** the helper consumes an object supplied by its caller and submits render objects; it doesn't in this pass expose a reliable name or struct definition for the route-node payload. Next static step is to trace which object type and data fields arrive in `$a1` at `0x80053AD4`, and compare those accesses against the byte offsets of the 84-byte candidate records. Runtime marker observation is likely to be the faster independent check.

Research hygiene: disassembly was performed locally against the supplied ROM and was not uploaded. No instruction dumps, code, ROM, or derived coordinates were committed; only the addresses and grounded call relationship are documented.
### Additional call-site detail

The caller at `0x80054048` is processing a list of runtime objects. It tests each object's flags at `+0x08`, updates/queries the object through `func_80080BEC`, then conditionally calls `0x80053AD4` when the GameShark-controlled word is nonzero. The helper reads an attached pointer at object offset `+0x84`, then passes a structure at `attached_pointer + 0xAC` through `func_8003B184` with varying float parameters. It prepares six attached render objects and submits them through `render_submit` (`0x800181BC`). `func_8003B184` in turn copies a 0x30-byte transform-like payload, changes a float parameter and calls a matrix/transform construction helper; this is compatible with sampling a runtime spline/transform representation, but not enough to equate that structure byte-for-byte with the 84-byte ROM item record.

That distinction matters: **the current static evidence has identified the debug rendering path and a spline/transform-bearing runtime object, not yet the player race cursor or lap-progress code**. The next static question is which object instances point at the course-route records and whether this attached `+0xAC` data contains centerline samples, animation paths, or another spline family.
## Source-independence caveat (2026-10-20)

The MIT asset library is a distinct serialization implementation, but its comments explicitly link the corresponding segment-data and segment-header models to `blender-swe1r/splineblock.py`. Its field names/unknown fields must therefore not be counted as an independent reverse-engineering source. The exact match of the local ROM's *whole spline block SHA-1* with published metadata remains a strong identity/length check; it does not alone validate the 84-byte record semantics. N64 static code now corroborates several important portions of the format—84-byte point stride, position/control-vector reads, outgoing-edge count/targets, and consumption of the `+0x40` key and trailing shorts. Other field semantics (incoming links, orientation, exact progress meanings, and the candidate track identity) remain provisional until their consumers or runtime behavior are verified.

## Runtime cross-reference — 84-byte node records are used by route/spline code (2026-10-20)

A deeper local disassembly of the US N64 main code materially improves confidence in the point-record interpretation. The facts below are from the supplied local ROM disassembled with LLVM's MIPS backend; no instruction dump or game data was committed. Function names are still address labels except for public symbols noted elsewhere.

### Position, controls, and node-key lookup

- At `0x8003A4A0`, code computes `point_array + index * 0x54` (84 bytes), then reads floats at node offsets `+0x10`, `+0x14`, `+0x18` and writes a three-float output. This confirms that a runtime node array with the same 84-byte stride uses the vector at `+0x10` as a 3D position-like value.
- At `0x8003A4E8`, a second accessor uses the same 84-byte stride and reads a signed halfword at `+0x40`.
- At `0x8003A50C`, code iterates the spline object's point count (`+0x04`), walks its point pointer (`+0x0C`) in 84-byte steps, and compares each node's halfword at `+0x40` to a requested value, returning the matching node index. Therefore the first halfword of the final 20-byte node tail is runtime-consumed as a key/identifier; whether its precise meaning is the Blender parser's name `progress` remains unproven.
- At `0x8003A5D0`, a numeric parameter is expanded into powers and combined with three-component vectors loaded from adjacent 84-byte records at offsets corresponding to node position (`+0x10`) and control vectors (`+0x28`, `+0x34`). The resulting three float outputs are a cubic curve sample or closely related cubic interpolation. This independently establishes that the position/control-vector portions are actively used by the runtime, though the exact curve basis/axis/scale still needs mathematical validation.

### Outgoing graph edges are directly traversed

- At `0x8007F560`, code loops over the spline's point count and advances each point pointer by `0x54`. It reads a signed halfword at node offset `+0x00` as a loop count, then reads the corresponding halfwords starting at `+0x04` as point indices, resolves those target nodes using the same `index * 0x54` calculation, and walks the resulting outgoing relationships. This is strong runtime evidence for the outgoing-edge count and destination-index interpretation at the start of the 84-byte record (consistent with Blender's `next_count` and `next` fields). The incoming count and all four previous-link words still deserve an equivalent direct cross-reference before each is called fully validated.
- The same routine iterates across nodes and outgoing edges while updating traversal/sample state and calling a supplied callback; it is not merely a file editor or debug-only code path. It confirms the native spline is consumed as a graph of linked nodes, so flattening all routes into one ordered polyline can lose real branching behavior.

### Runtime use of the tail metadata for route/section lookup

- At `0x8007EE98`, code follows a cursor object's spline pointer, reads the spline point count and node-array pointer, divides an incoming integer by 10, then scans up to eight halfwords beginning at node offset `+0x42` for that value. A match stores node and sub-entry indices and calculates a fractional remainder for the cursor state. The helper is called from the larger route/spline routines at `0x8007F430` and `0x8008080C` paths.
- This confirms that the eight shorts at `+0x42` through `+0x50` are not safely dismissible padding: the runtime consults them for a progress/section-like lookup. It **does not yet reveal each word's full meaning or prove that the incoming integer represents race-lap progress**.
- The separate `+0x40` lookup helper and the `+0x42`–`+0x50` lookup can serve distinct roles. Keep both sets of raw values until the consumer logic is understood; do not collapse them into a single `checkpoint` boolean.

### Revised confidence

- **High:** the 84-byte stride is the actual runtime node stride; `+0x10..+0x18` supplies 3D position-like values; `+0x28..+0x33` and `+0x34..+0x3F` provide control-vector-like data for cubic sampling; the first halfword is consumed as an outgoing edge count and following halfwords as destination indices; and the `+0x40` key plus eight shorts starting at `+0x42` are consumed by runtime lookup code.
- **Medium:** the `+0x40` word's semantic name is `progress`, that the eight following shorts are exactly alternate progress IDs, and the particular N64 item ID 110 is Boonta Classic.
- **Still open:** the meaning of all incoming-link fields, coordinate axis and world scale, exact cubic basis, how the graph is selected for player vs AI vs visual/debug objects, race cursor state transitions, the finish-line/lap-crossing condition, and N64/GameCube/Wii format parity.

This changes the next step: there is now enough evidence to write synthetic tests for an engine-neutral **branch-capable route graph** and a cubic-sampling API, but not enough to implement a faithful retail-game progress/lap state machine. Keep `boonta-track-v1` unchanged and keep original-ROM records local until the remaining semantics and provenance are resolved.

### Stronger interpretation of the `+0x40` key: runtime builds a progress-to-node index

Follow-up inspection of the caller at `0x8007FDC0` clarifies the use of the `+0x40` field:

- The function reads the spline runtime header at `+0x04` and `+0x08` as two separate counts, initializes a short lookup table to `-1` using the second count, then iterates the node count.
- For each integer key beginning at zero, it calls `0x8003A50C` with the spline object and that key. That accessor searches node records by the halfword at `+0x40`, returning a node index; the caller records the result and walks the node's outgoing links, preparing traversal/sample state.
- This gives **high confidence** that the halfword at node offset `+0x40` is a route-progress/order/group key used to index the spline's node graph. It is consistent with Blender naming the field `progress`, but its exact lifecycle and meaning in race standings (as opposed to spline segment grouping/path reconstruction) are still not proved.
- The top-level runtime counts also line up with the public 16-byte `Spline` header model: one count for nodes, a second count for spline segments/route groups, followed by a runtime pointer to the node array. The raw N64 block's exact top-level field meanings should still be treated separately from this runtime structure, since the loader may normalize or repack it.

`0x8007EE98` provides a second, distinct lookup: it divides its input by 10 and scans the eight shorts at `+0x42..+0x50` within each node, storing a node/sub-entry and fractional value in a cursor structure. Together these show that the tail metadata participates in runtime route indexing. They do **not** establish that these fields encode lap count or that crossing a particular edge ends a lap.

Current interpretation by evidence strength:
- outgoing-link count at `+0x00` and outgoing node IDs at `+0x04/+0x06`: directly used by runtime graph traversal;
- 3D position at `+0x10..+0x18` and control vectors at `+0x28..+0x3F`: directly used by runtime lookup/interpolation;
- node key at `+0x40`: directly used to construct a key-to-node lookup, high confidence as a progress/order/group key;
- eight shorts at `+0x42..+0x50`: directly consulted by the progress/section-to-cursor helper, precise meaning still unknown;
- reverse/incoming links at `+0x02` and `+0x08..+0x0E`, rotation-like bytes `+0x1C..+0x27`, and lap/finish semantics: still require dedicated cross-reference.

## Cursor/runtime route-association path — next layer beyond graph preparation (2026-10-20)

Read-only local MIPS disassembly now ties the graph-format work to a likely per-object route-association subsystem. The original US ROM remains local; this section records addresses/relations only.

### Runtime object and cursor refresh

- In the public symbol map, `func_80080BEC` spans a large auto-discovered region. Its opening code saves object fields at `+0xEC`/`+0xF0`, updates a cursor-like subobject at `object + 0xAC`, stores lookup outputs at `+0xF8` and `+0x100`, and calls helper bodies at `0x800807E0`, `0x800808E0` and `0x80080A1C`. If the primary cursor value changes, it clears a state word at `+0x1EE4`. These are strong signs of per-object route/cursor state refresh, but the structure offsets have not yet been assigned stable source-level field names.
- `0x800807E0` calls `0x8007EE4C` to initialize/inspect a route cursor and calls `0x8007F22C` / `0x8007F23C` with output storage at object offsets `+0xF4` and `+0xFC`; this is consistent with the cursor/query mechanism described above. The exact meaning of each output remains provisional.
- **Caller-scope caveat:** the direct `jal` references to `0x80080BEC` found in the inspected main code are all within `func_80054048` (call sites `0x8005411C`, `0x80054628`, `0x80054744`, `0x800547A0`). At `0x8005411C`, the argument is a pointer loaded from a containing object's `+0x84`; this same outer function checks the GameShark spline-marker word and conditionally calls the extra render helper. This establishes a generic object-update/render context for the known direct callers. It **does not prove** that these particular cursor updates are the player's race-progress tracker; they may be animated props, camera or other spline-attached scene objects. Need identify a separate player/AI caller or data relationship before using this path to explain race standings.
- The broad symbol range `func_80080BEC` contains several apparent helper bodies, including a routine beginning near `0x80080DB4`. The public symbol table's auto-discovered function boundaries therefore cannot be assumed to match every true function boundary; any future naming should preserve this caveat.

### Position-to-spline association candidate at `0x80080DB4`

- The routine beginning at `0x80080DB4` takes a spline-like object, checks its type/count fields, and iterates the point count while advancing through node records by 84 bytes.
- For each node it uses `0x8003A4A0` to read the node's 3D position, subtracts a query/world position, tests geometric relationships against candidate edges, and calls helpers including `0x8003B02C`. The loop reads the outgoing-edge count from offset `+0x00`, the target node index from `+0x04/+0x06`, and resolves those targets with the same `index * 0x54` stride.
- This is strong evidence of a world-position-to-route/spline association or nearest-curve operation: the engine is not just exporting curves for the debug renderer; it performs geometric queries over the route graph. The exact metric, edge selection, and returned cursor/progress representation have not yet been fully proven.
- `0x80080BEC` also uses the result of these helper paths to refresh values on the runtime object, including cursor-related outputs, so the code appears to be on the regular object update path. I have not yet isolated a verified callsite proving which racer types use this exact path (player, AI, or both).

### Lap-count / finish-line finding remains open

Search of this call path has **not** yet revealed a confirmed increment of the race lap counter or a finish-line crossing predicate. The words `LAP`, `FINAL LAP`, `LAP TIME` and `Laps:` exist in game text, but their presence alone does not identify the update function. The route-order key at node offset `+0x40`, the eight trailing shorts, the route cursor values at object offsets `+0xEC..+0x100`, and race-lap state must be kept separate until an actual consumer proves their relationship.

### Next focused trace

1. Trace all callers of the position-to-spline helper body near `0x80080DB4` and determine whether its output is used for racer progress, AI route following, collision or all of these.
2. Follow the caller-side object fields it writes and compare them with known HUD race-state reads/writes, looking for a monotonic lap counter and a wrap/finish condition.
3. Where static references stay ambiguous, use the documented N64 debug spline-marker GameShark switch in a local emulator and compare an observed marker path on a known track. No emulator is installed in the current analysis container, so that visual test remains pending.

This remains research-only. It adds no parser, ROM content, point coordinates, control handles, extracted geometry, or gameplay code to Boonta.

## Graph-preparation helper chain and per-edge callbacks

One additional control-flow pass clarifies how the game uses the graph-preparation helper. `0x800801B8` is an apparent real function boundary inside the oversized public symbol range beginning at `0x8007FDC0` (a symptom of the public auto-symbol map joining several functions). The code:

- receives a spline-like object with count fields at `+0x04` and `+0x08` and a node-array pointer at `+0x0C`;
- checks the node-count/point-array shape and initializes a scratch/output structure;
- calls `0x8007FDC0` with scalar `100.0` to initialize a key-to-node table for the current spline;
- calls `0x8007F560` with scalar `10.0` and callback `0x8007F098`, and conditionally calls it again with callback `0x8007F430` when a global option is enabled.

`0x8007F560` is now high-confidence graph traversal: it loops over the point count, reads each node's outgoing-link count at `+0x00`, walks the destination indices from `+0x04/+0x06`, resolves nodes by the `0x54` stride, and invokes the supplied callback for the resulting edges. The callbacks at `0x8007F098` and `0x8007F430` consume sampled values and mutate or submit associated state; their complete semantic contracts remain unresolved.

**Interpretation:** this establishes a graph preprocessing/sampling callback chain beyond simply parsing one point at a time. The `100.0` and `10.0` arguments are literal parameter values, not confirmed sample counts or game-world units—the callers and callback math must be fully traced before giving them those meanings. Because the helper range is used around object/cursor and render plumbing, do not label this as a player-lap initializer without an independently established caller.

### Current strongest architecture boundary

At this point static evidence supports three separate subsystems:
1. a node graph keyed by the halfword at `+0x40`, with outgoing edges and position/control vectors;
2. graph traversal and geometric sample/position-association utilities that work over that graph;
3. generic runtime-object cursor/transform update and render callbacks that can consume route-like spline data.

The remaining gap is linking these mechanisms to the specific player/AI race state that increments a lap and reports race progress. No code path found so far proves that relationship, so the current GameCube demo's distance-based lap logic must not be described as a faithful port.

## N64 lap-state addresses — public cheat-code semantics cross-check (2026-10-21)

This is a separate N64 evidence thread; do not merge its conclusions with the Windows-PC route-progress analysis above.

### Direct public evidence

- [TheForce.Net's N64 Episode I: Racer codes](https://www.theforce.net/videogames/codes/n64/racer.asp) explicitly lists `8111900A 00??` under both “Start on Lap … Player 1” and “Always on Lap … Player 1”, with values `00–04` labelled Lap 1 through Lap 5. The same page labels `81119092 00??` as the corresponding Player 2 codes, with the same value mapping.
- [GameRevolution's N64 cheat list](https://www.gamerevolution.com/guides/28992-star-wars-episode-1-racer-cheats) independently lists `8111900A0002` as “Start On Lap 3” for Player 1.
- The two player-specific target addresses differ by `0x88`. Their documented cheat semantics support interpreting these as N64 lap-state write targets; the spacing is consistent with corresponding per-player state locations, but spacing alone does not prove a C struct layout.

**Updated confidence:** high that the public cheat listings intend these addresses to set/hold the corresponding player's lap value. This is stronger than treating the addresses as arbitrary participant-state candidates. It does **not** by itself identify the native reader/writer instructions or prove the exact field layout.

### Important limits on the inference

- These are community cheat listings, not source-level symbols or instruction cross-references; the pages do not establish the exact ROM checksum/revision to which every code applies.
- The public [`sp00nznet/racer` reference at commit `11f6f70469f995304422f2209a47e9c2df5ff6d0`](https://github.com/sp00nznet/racer/tree/11f6f70469f995304422f2209a47e9c2df5ff6d0) is a static-recompilation project. Its [README](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/README.md) explicitly says that no N64 decompilation exists for the game; the checked-in `symbols.toml` is a function/VROM-symbol map, not a source-level lap-field definition. The [IDA handoff](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/docs/IDA_ANALYSIS_HANDOFF.md) references a decompiler output on a local Windows path that is not present in this public repository.
- Therefore, the public source set inspected here does not yet establish the normal runtime code path that increments the lap, handles finish-line crossing, or writes the HUD's LAP / FINAL LAP state. Keep those questions open and do not map the PC `Jdge` data or the prototype's own counters onto these addresses without a separate proof.

### Minimal next verification

On the owner's lawful local US ROM in a compatible emulator/debugger, observe writes to `0x8011900A` and `0x80119092` during an ordinary race, or use the known lap-setting cheat as a controlled intervention. Record the runtime address/function and visible result only. Keep the ROM, full memory dump, and extracted proprietary data local; no such emulator observation is claimed as completed here.

## PC-only HUD analogue — target for N64 cross-check (2026-10-21)

This subsection deliberately records PC evidence only. It must not be cited as proof that the N64 build shares its lap fields, state machine, text IDs, or call paths.

At pinned commit [a9863edd4caaa573f89ff634fa7d1cd6d41738ab](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab):

- src/Swr/swrRace.c, function swrRace_InRaceTimer (PC function address 0x00460950) formats the in-race HUD. The lap fraction uses the current completed-lap counter plus one, clamped to the configured lap count, and the configured lap count as the second number. It then renders the LAP caption using /SCREENTEXT_424/. The same routine handles a completed-lap time popup, LAP TIME (SCREENTEXT_420), New Record (SCREENTEXT_538), the FINAL LAP banner (SCREENTEXT_526), and POS (SCREENTEXT_426).
- src/Swr/swrObj.c, function swrObjJdge_F2 (PC function address 0x0045EA30) increments the per-player completed-lap counter only after swrRace_UpdateRaceProgress reports a crossing. Equality with the configured number of laps enters the finish path and sets the PC score/pod state accordingly.

Why this helps the N64 trace: the N64 ROM's local text scan showed a cluster in the same apparent ordering — LAP TIME, New Record, FINAL LAP, TIME, two %d/%d templates, LAP, POS. The PC implementation gives us specific comparison targets: one fraction should pair current lap + 1 with configured laps, while the other may be position / number of racers; the final-lap banner is selected at the transition into the last lap in this PC implementation.

Do not promote this to an N64 conclusion yet. The PC text IDs and N64 resource indices may differ, and identical labels/order do not establish shared code. The next local-only N64 step remains mapping the resource/string lookup and draw caller, then validating whether the FINAL LAP selector and lap fraction have the analogous data flow.

## N64 HUD call-path cross-check — direct local static evidence (summary only, 2026-10-21)

This section supersedes the earlier status that the local N64 HUD renderer/resource path was still unlocated. A fresh address-aware pass corrected the earlier direct-pointer search and linked the visible text resources to their caller. Exact instruction addresses, ROM file offsets, and raw disassembly remain in private local notes rather than in this public dossier.

- The local US N64 HUD function obtains the current/configured lap fraction from the same participant progress counter and manager threshold already traced through the configurable 1–5 Laps option and the route-progress event path. The first value is participant count + 1, clamped to the configured target; the second is that target. This is direct local static evidence for the displayed lap fraction, not merely a guess based on the string text.
- The second numeric fraction is a different template: participant position over the manager's total-racer count, rendered with POS. The two visually similar %d/%d templates therefore have distinct data sources.
- The same N64 HUD function references and draws FINAL LAP only when the next displayed lap equals the configured threshold, for the single-local-player layout, and during the latter fade portion of the lap-completion popup. It is not a persistent banner throughout the entire final lap.

Combined with the already documented option-to-manager-threshold and route-progress-event-to-participant-counter paths, the N64 chain is now strongly supported end-to-end for the HUD lap count and FINAL LAP selector at the static-code level.

Still open: live emulator/hardware confirmation, exact timing of the reported route-progress event relative to physical finish-line traversal, the manager's eventual results-screen transition, and all cross-platform parity. No Dolphin/N64 hardware run is claimed. The PC source reference remains a separate comparison only.
## Manager/results-screen boundary — next unresolved link (2026-10-21)

The N64 HUD path is now traced at the local static-code level, but the downstream transition into the actual results screen is still unresolved. A follow-on review of the phase/lifecycle dispatcher, its timer/event branches, and the manager-side local-player threshold check did not expose a conclusive call to a results renderer or scene-load handler.

Some generic lifecycle branches send `Fini` / `Abrt` tags or adjust phase bits, but those labels alone do not establish that they mean “race finished” or select the results UI. Do not assign those semantic names without a positive caller-to-destination data-flow chain.

A plain ASCII scan of the local US ROM found no obvious uppercase `RESULTS`, `RACE OVER`, `FINISH`, `FINISHED`, `CHAMPION`, `STANDINGS`, `PODIUM`, `RACE COMPLETE`, `CONTINUE`, or `RACE RESULTS` literals. This is weak negative evidence only: UI text may be compressed, encoded, or referenced by resource ID.

**Next bounded target:** connect the all-local-participants-done condition to the writer of the manager's lifecycle phase and then to the actual results resource/scene selection. Runtime behavior remains untested: no N64 emulator/debugger or Dolphin binary is available in this command-line environment. The lap/HUD static finding should not be read as results-transition proof.
## Lifecycle-tag disambiguation — do not treat Fini/Abrt as results events (2026-10-21)

A follow-on local static pass reviewed the race-manager phase dispatcher and the shared four-character-tag consumer. The branch that reaches the participant threshold still routes through generic lifecycle/event handling; the `Fini` / `Abrt` strings are not, on their own, evidence of a results-screen transition.

The consumer also handles other tags (including `Load`, `RStr`, and `Stop`) and performs general object flags, timers, and shared-state/fade updates. The shared event helper has callers beyond this one manager path. No direct call edge from the all-local-participants-done condition to a positively identified results renderer or scene-load handler has been demonstrated.

**Evidence status:** the N64 lap counter and `FINAL LAP` HUD selector remain directly traced at static-code level; the terminal manager/results-screen destination remains open. The next bounded target is a positive chain from the all-local-racers-done predicate through the manager phase writer into the actual results UI/resource selection. Do not infer results-screen semantics from `Fini`, `Abrt`, or phase names alone. No runtime test is claimed.
## Shared lifecycle-tag handler: no results-screen proof (2026-10-21)

Additional local static review of the generic event/tag paths confirms an important negative result. The manager phase dispatcher sends `Fini` and `Abrt` tags into a shared object lifecycle/state helper; a separate tag consumer also handles `Load`, `RStr`, and `Stop`, modifying general object flags, timers and shared fade/control state. The helper has call sites beyond this race-manager path.

No conclusive direct call edge has been established from the all-local-racers-done predicate to a results renderer or scene-load handler. The tag text alone is insufficient to identify the results transition, and the global updated in one handler is referenced elsewhere in menu/UI-related code, so it remains unnamed.

**Current boundary:** N64 lap-count and `FINAL LAP` HUD data flow are traced at local static-code level; manager phase → results-screen destination remains unresolved. The next proof must connect the all-done condition to a positively identified results UI/resource/scene selection. Runtime observation and console parity are still unverified.

## PC results-transition analogue — pinned-source refinement (2026-10-21)

This is a **PC-only comparison lead**, not evidence of N64 parity. Both source files below are pinned to `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`.

- [swrObj.c lines 918–970](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrObj.c#L918-L970): in `swrObjJdge_F2`, the state-1 dispatcher provisionally writes state 2, commented as “all local racers finished”, and re-arms state 1 while eligible local racers remain in progress.
- [swrObj.c lines 800–875](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrObj.c#L800-L875): state 4 is the post-race camera sweep. A skip/input path sets `swrRace_resultsScreenActive` immediately; the normal path advances to state 5 after sweep completion and a linger, while state 5 sets the results-active flag on its handler pass.
- [swrRace.c line 320 onward](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c#L320-L340): `swrRace_ResultsMenu` is explicitly documented as the post-race results-screen routine; its stated responsibilities include score ordering, record/name-entry handling and tournament progression/save work.

**Inference allowed:** the PC reference supplies a concrete comparison checklist for identifying (1) the all-local-racers-done gate, (2) the intervening camera/phase path, and (3) the results UI entry point. The results-active flag has path-dependent timing even in this PC implementation.

**Inference not allowed:** PC state numbers, flags, event tags, struct fields or function names must not be assigned to the N64 build. The local N64 proof still requires a positive local static call/data-flow chain from its all-done predicate through its phase writer to an identified results renderer/resource/scene selector, or controlled runtime observation. No runtime test or gameplay change is claimed.
## O. Public N64 static-recompilation source boundary — results semantics not exposed (2026-10-21)

This is a bounded public-source check on the still-open N64 results-transition question. It does not use or publish local ROM bytes, extracted game content, exact local disassembly, or private offsets.

### Direct observations

- The pinned [sp00nznet/racer README, lines 22–24](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/README.md#L22-L24) describes the repository as a static recompilation using N64Recomp and explicitly says that no N64 decompilation exists for this game.
- At the same revision, [src/section_table.cpp, lines 647–653](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/src/section_table.cpp#L647-L653) maps `func_80080BEC` to section offset `0x807EC` and size `0x5F0`, adjacent to more generic function labels.
- [symbols.toml, lines 3229–3232](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/symbols.toml#L3229-L3232) records only the generic symbol, VRAM address and size. It does not identify a results UI routine or explain the function's behavior.
- A bounded public code search for `func_80080BEC`, `0x80080BEC`, and common lifecycle tags did not yield a readable semantic body or a positive N64 results-renderer edge in that repository. This describes the scope of the checked public material; it is not proof that no other lawful public lead exists.

### Interpretation boundary

The public source confirms a function boundary, not the semantics of the local N64 phase/lifecycle code. It therefore does not close the chain:

`all local participants reached the configured lap threshold` → `manager phase/state writer` → `identified results UI/resource/scene selector`.

The pinned PC reference in section N remains only a comparison checklist. Do not transfer PC state numbers, flags, callbacks, event tags or struct fields to N64.

### Next bounded check

The useful next check requires the owner's existing local static-analysis environment: follow the write to the manager phase/state field that is reached after the all-done predicate, enumerate the consumers of that exact field, then continue to a data/resource identifier or renderer whose results-screen role is positively identified. A generic tag, phase bit, string search, or unrelated reference to a shared global is insufficient. If the consumer chain stays generic, retain the blocker rather than inventing a semantic label.

**Current status:** N64 lap-counter and `FINAL LAP` HUD path remain traced at local static-code level; the terminal results transition remains unresolved. No emulator/hardware result, gameplay change, asset import, or new platform-parity claim is made.

## P. Runtime-debugging method reference for the unresolved N64 transition (2026-10-21)

A second method reference was checked after reviewing the public static-recompilation boundary. This is a workflow lead from another N64 title, not evidence about Star Wars: Episode I – Racer.

- Chris Lewis's [Finding Jingle Town: Debugging an N64 Game without Symbols](https://blog.chrislewis.au/finding-jingle-town-debugging-an-n64-game-without-symbols/) describes using the Ares emulator with GDB remote debugging to test a concrete hypothesis about when a loader is called and how a state field changes. The article identifies breakpoint hits and observed values as the proof, rather than naming an unknown function from its address alone.
- The author's [Using Coding Agents to Decompile Nintendo 64 Games](https://blog.chrislewis.au/using-coding-agents-to-decompile-nintendo-64-games/) distinguishes matching machine code from understanding a function's broader intent, which also requires cross-references and call-site analysis.
- Applicability limit: these articles analyze Snowboard Kids 2, not SWE1R. They demonstrate a method only. The documented workflow requires a suitable local ROM, an emulator with a debug server, GDB tooling, and a symbol/address mapping or other way to set useful breakpoints. It has not been run for SWE1R in this session.

### Minimal test if a suitable local environment becomes available

1. Set a breakpoint at the already locally identified all-local-participants-done branch and record the exact manager field write reached on the final lap event.
2. Continue through each write to that same field and break on its readers; note the first branch that correlates with post-race camera/input handling.
3. Continue until a verified UI resource/scene selector or renderer is reached, confirming the screen visually. If no positive destination is reached, keep the status blocked and record the observed address/data flow without assigning unsupported semantic names.
4. Record emulator and game-region/version, breakpoint addresses, observed state values, and repeatability locally. Publish only a concise evidence summary; do not upload a ROM, raw proprietary binary, or extracted game resources.

**What this adds:** a reproducible experimental route to close the blocker. It does not itself close the results-transition question. No emulator or hardware run was executed, no ROM was uploaded, and no gameplay files changed.

## Q. Public symbol-table coverage check — N64 result-renderer lead (2026-10-21)

This pass checked the full public symbol manifest and tracked repository tree at `sp00nznet/racer` commit [`11f6f70469f995304422f2209a47e9c2df5ff6d0`](https://github.com/sp00nznet/racer/commit/11f6f70469f995304422f2209a47e9c2df5ff6d0). This is a source-availability audit, not a claim about proprietary runtime behavior.

### Directly observable from public files

- The upstream project README explicitly describes itself as a static recompilation and states that there is no existing N64 decompilation for this game ([README](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/README.md)).
- The public [`symbols.toml`](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/symbols.toml) has 880 function entries. Only a small minority have semantic names; examples include `render_submit` (0x800181BC, size 0x19C4), `main_init` (0x8002F4D0), `racer_update_speed` (0x80030154), `collision_check` (0x8003EC40), and `audio_play_sfx` (0x80046670). None of those names by itself establishes the results-screen path.
- The candidate previously inspected, `func_80080BEC`, remains generic in [`symbols.toml` lines 3229–3232](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/symbols.toml#L3229-L3232): VRAM 0x80080BEC, size 0x5F0. The generated [`section_table.cpp` lines 647–653](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/src/section_table.cpp#L647-L653) maps it to code-section offset 0x807EC, size 0x5F0; it adds no semantic meaning.
- The tracked [`src/`](https://github.com/sp00nznet/racer/tree/11f6f70469f995304422f2209a47e9c2df5ff6d0/src) directory consists of host/runtime integration files and the generated function lookup table; the generated `RecompiledFuncs/` output path was not present in the public repository tree at this commit. This pass therefore did not find a public C body or source-level call graph that ties the all-local-done path to a results UI renderer/resource selector.
- Public GitHub search for the exact candidate and results/menu/lap/finish terminology did not return a separate source repository or semantic identification. This is only a bounded search result, not proof that no other source exists.

### Evidence boundary and decision

- **Established:** the available public manifest identifies function boundaries and a few broad helpers, but the candidate path is still not semantically identified.
- **Not established:** that `render_submit` is the results renderer; that `func_80080BEC` owns race completion; that any generic phase bit, `Fini`/`Abrt` tag, or renderer entry corresponds to the results screen.
- **Decision:** no new function rename or gameplay change. Further searching the same public symbol manifest is unlikely to close RE-001. The next adequate evidence must be either a permitted local runtime/debugger trace (as outlined in section P) or a separately published, citable analysis that explicitly connects the manager state write through readers to the results-screen selector.

**Status remains BLOCKED pending semantic/runtime evidence.** No ROM was uploaded, no proprietary assets were committed, no emulator/hardware execution was done in this pass, and no gameplay source was changed.

## R. Publicly documented N64 debug mode — possible runtime aid (2026-10-21)

A targeted public-web search found independent game guides describing an N64 debug mode entered through the in-game naming/cheat flow. This is a possible convenience for a future lawful local test, not evidence of the results-screen code path.

- [GameFAQs N64 cheats page](https://gamefaqs.gamespot.com/n64/198780-star-wars-episode-i-racer/cheats) documents the `RRDEBUG` code and the pause-menu directional sequence used to expose the cheat/debug menu.
- [GameFAQs N64 FAQ](https://gamefaqs.gamespot.com/n64/198780-star-wars-episode-i-racer/faqs/2522) and [Ethereal Games' guide](https://etherealgames.com/n64/s/star-wars-episode-i-racer/cheats-secrets-tips-tricks/) describe debug controls including fast-forward and rewind during a race.
- These are community gameplay guides, not source-level reverse-engineering reports. They do not identify the manager state field, its readers, a results renderer, or any scene/resource selector. They should not be used to assign semantics to `func_80080BEC` or generic tags.

### Limited value for RE-001

The in-game debug option might make a future local race test easier to reproduce or navigate, if it is available in the user's game revision. It does not replace an emulator debugger: fast-forward/rewind behavior alone cannot prove the all-done state write or connect it to the results UI. Region/version compatibility has not been verified.

**Decision:** preserve this as a test-preparation lead only. RE-001 remains blocked pending direct data-flow evidence or a permitted local runtime trace. No game was run and no ROM or assets were accessed.

## S. Platform boundary of older OpenSWE1R analysis (2026-10-21)

A newly located community article about SWE1R reverse engineering links the historical [`OpenSWE1R/swe1r-re`](https://github.com/OpenSWE1R/swe1r-re) analysis project. Its public repository page explicitly says its function documentation is based on a **Windows patch executable** (and describes a planned shift to a Windows demo build), so it is not N64 function evidence. The same page characterizes the project as reverse-engineering and documenting functions, not a platform-neutral symbol map ([repository page](https://github.com/OpenSWE1R/swe1r-re)).

The older [`OpenSWE1R/openswe1r`](https://github.com/OpenSWE1R/openswe1r) project README describes an x86 Windows-focused compatibility/porting approach; Mac/Dreamcast/N64 support is presented as a possible future direction rather than the supported baseline. The user-owned fork [`Master-Chiken/openswe1r`](https://github.com/Master-Chiken/openswe1r) also documents this Windows/x86 approach. These are useful historical PC context, but they do not establish the N64 manager-to-results path.

### Decision

- Keep PC decompilation names as cross-reference leads only; validate any proposed analogue against N64-specific evidence.
- Do not import GPL-2.0-or-later OpenSWE1R code into Boonta Reborn 88's MIT codebase without a separate, explicit license decision.
- No proprietary executable was downloaded or opened during this check. No new semantic name is assigned and the N64 results-transition blocker remains open.


## T. N64 lap GameShark addresses — useful label, not finish-state proof (2026-10-21)

TheForce.Net's public N64 code list labels the write location `0x8011900A` as both “Start on Lap” and “Always on Lap” for Player 1, mapping values `00`–`04` to Lap 1–5. The same list labels `0x80119092` the same way for Player 2 ([source lines 88–99](https://theforce.net/videogames/codes/n64/racer.asp)). This is direct evidence about how the published GameShark codes are described, not a source-level symbol name or an independently reproduced memory trace.

### What is supported

- **High confidence — documented cheat target:** the page associates `0x8011900A` and `0x80119092` with forcing the lap value/selection for Player 1 and Player 2 respectively. It separately lists the same values for “Start on Lap” and “Always on Lap”; values `00`–`04` are labelled Lap 1–5.
- **Moderate confidence — repeated two-player layout pattern:** the address difference is `0x88`. Other pairs on the same page follow the same difference: “Low Timer” P1 `0x80119004` versus P2 `0x8011908C`, and “Always Place First” P1 `0x80118FED` versus P2 `0x80119075`. This makes a repeated player-specific memory layout plausible; the cheat list alone does not prove a C struct, universal stride, or layout for every racer.
- **Not established — participant struct member or finish flag:** the listing does not demonstrate the owning object/struct, the exact field type or lifetime, which code reads the values, whether the cheat is always accurate across regions/builds, or how final-lap crossing updates race completion. It does **not** show that either address is a finish-state field or identify a results-screen transition.
- **Not independent validation:** no console/emulator memory watch or controlled race was run in this pass. The source is a community GameShark reference, not an official disassembly.

### Decision and smallest next check

Use the addresses only as **externally documented lap-related watchpoint candidates**, not as semantically proven participant fields. In an authorized local copy/debugger, observe writes and reads at both addresses during a known lap crossing and final-lap finish; then trace the consuming state into the race-manager phase and positively identified results UI/resource selector. If a local debugger trace is unavailable, keep RE-001 blocked rather than infer the missing edge. No ROM or proprietary assets should be uploaded or committed.


## U. Ares/GDB feasibility check — historical attach crash has a recorded fix (2026-10-21)

This check narrows the tooling risk for the remaining N64 results-transition investigation. It does **not** add evidence about SWE1R's internal state machine.

### Direct public observations

- Chris Lewis' [N64 debugging walkthrough (23 Dec 2025)](https://blog.chrislewis.au/finding-jingle-town-debugging-an-n64-game-without-symbols/) demonstrates Ares remote debugging with `gdb-multiarch`, selecting `mips:4000`, connecting to the configured GDB port, setting a function breakpoint, and reading a state byte directly from memory. The walkthrough applies to **Snowboard Kids 2**, not SWE1R; it is a method reference only.
- Ares [issue #1778](https://github.com/ares-emulator/ares/issues/1778) recorded an N64 GDB-attach/continue crash in January 2025 and said v139 worked while v140–v141 and a bleeding-edge build did not.
- The issue timeline records commits [`c8ddc5d`](https://github.com/ares-emulator/ares/commit/c8ddc5d) and [`dfcd7d4`](https://github.com/ares-emulator/ares/commit/dfcd7d4), both named as fixes for the MIPS exception on GDB attach; the linked [issue #1793](https://github.com/ares-emulator/ares/issues/1793) closed the report as completed on 26 January 2025.
- The official [Ares v148 release](https://github.com/ares-emulator/ares/releases/tag/v148) was published on 30 May 2026 and is the latest non-prerelease release returned by the upstream releases API checked on 21 October 2026. The v148 tag is 812 commits ahead of, and not behind, the merged fix commit `dfcd7d4`, so the fix is included in that release's ancestry.

### Interpretation and caveats

- **High confidence:** the specific historical Ares bug report has a recorded upstream fix and closure.
- **Not established at this stage:** whether any current Ares release/platform combination works with the target SWE1R build, whether a watchpoint on the desired address fires with useful stop timing in an actual session, or whether the game's results transition can be resolved with this method. A later source audit documents the upstream N64 watchpoint implementation in section V below.
- The tutorial and bug report use different port setups (`:1235` in the tutorial's example, `:9123` in issue #1778). Do not hard-code either value; use the selected Ares build's actual configured GDB port.
- Ares/GDB debugging should therefore be treated as **testable, not guaranteed**. The later CI attempt against the public ctest homebrew confirmed the listener/GDB handshake but failed on continue; see section X. Do not proceed directly to a game-specific trace or repeat that same smoke test unless a new falsifiable hypothesis or replacement minimal homebrew addresses the observed traps.

### Minimal next runtime experiment

1. Start with official stable Ares v148 (or record the exact later stable version if one is available at test time); also record host OS, GDB version and configured port.
2. **This step was attempted in CI and did not pass**; see section X. Do not repeat the same ctest/v148 path as if still untested. A future retry needs a distinct, justified variable or a purpose-built minimal public homebrew.
3. With a lawful local N64 game copy, observe the documented lap-related watchpoint candidates `0x8011900A` (Player 1) and `0x80119092` (Player 2) through lap changes, then trace the actual all-local-done condition and its consumers to an identified results UI/resource/scene selector.
4. If the emulator setup, memory reads, or relevant state path cannot be validated, report the exact failure and leave RE-001 blocked. Do not infer results-screen semantics from the GameShark labels or PC analogues.

No runtime test was performed during this documentation pass. No ROM, disc image, proprietary asset, or executable was downloaded, uploaded, or committed. No gameplay source changed.


## V. Ares N64 memory-watchpoint support — source verified, end-to-end test pending (2026-10-21)

This follow-up checks the emulator implementation itself, rather than inferring capability from the historical attach-fix issue. All Ares code references below are pinned to commit [`9408cb43d4948fc3ea6e152a307a34348df3fe04`](https://github.com/ares-emulator/ares/commit/9408cb43d4948fc3ea6e152a307a34348df3fe04).

### Direct observations

- The Ares [GDB server README](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/nall/nall/gdb/Readme.md) explicitly documents write, read and access memory-watchpoints. It describes `normalizeAddress` as the hook used to compare GDB watchpoint addresses with the emulator's internal addresses.
- The N64 system registers [`GDB::server.hooks.normalizeAddress`](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/system/system.cpp#L162-L165), sign-extends the requested address and routes it through `cpu.devirtualizeDebug(address)`. This is evidence the N64 target has an address-normalization path; it is not an independently executed proof for SWE1R.
- The N64 CPU [memory read and write methods](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/cpu/memory.cpp#L166-L193) call `reportMemRead(access.vaddr, Size)` and `reportMemWrite(access.vaddr, Size)` for successful CPU memory accesses.
- The same source also reports debugger-originated writes in [`CPU::writeDebug`](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/cpu/memory.cpp#L196-L205). The [N64 recompiler](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/cpu/recompiler.cpp#L252-L262) includes `GDB::server.hasWatchpoints()` in its state key.
- The server compares each reported access range against configured watchpoints after address normalization ([`server.cpp`](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/nall/nall/gdb/server.cpp#L56-L84)).

### Conclusion and limits

- **Verified at source level:** the reviewed Ares N64 implementation includes memory-read/write reporting, address normalization, and watchpoint-aware recompilation state.
- **Not verified in execution:** whether the selected Ares build and host OS attach and continue reliably; whether a watchpoint on a public SWE1R lap-code address fires with useful stop timing; and whether a resulting trace can identify the manager transition to the results UI/resource.
- The proposed next test was to try a write watchpoint after the generic ctest smoke test passed. That precondition did not pass in the later CI experiment (see section X), so **do not run the game-specific watchpoint yet**. First isolate the generic ctest failure with a new hypothesis or different minimal public homebrew. Only a successful, stable debugger session can justify the subsequent local game watchpoint.
- Public cheat-list addresses remain **watchpoint candidates**, not proof of a native field or finish flag. No watchpoint was actually run here, no local game data was accessed, and no gameplay code or assets changed.



## W. Concrete GDB watchpoint procedure — local checklist, not a claimed test (2026-10-21)

This section turns the source findings above into a bounded experiment. It is documentation only; no local game or emulator was run during this pass.

### Configure the Ares debug server

- In Ares, open **Settings → Developer → Debug Server Options**, enable the server, and note the displayed port. In the reviewed pinned source, the default is `9123` ([`settings.hpp`](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/desktop-ui/settings/settings.hpp)); the UI permits changing it, so the actual configured value wins.
- Leave **Use IPv4** disabled for a normal local-only connection where possible. The reviewed UI explicitly warns that IPv4 mode binds to any device and can allow anyone on the network to access the server ([`developer.cpp`](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/desktop-ui/settings/developer.cpp)). If a specific host setup requires IPv4, restrict network access and do not expose the debug port to an untrusted network.

### Gate 1 — generic debugger connection and continuation (attempted; not passed)

Official stable [Ares v148](https://github.com/ares-emulator/ares/releases/tag/v148) was selected as the first baseline because upstream's fix for the historical attach crash is in its commit ancestry. CI ran v148 and v139; both built and accepted GDB, but neither passed the continue phase (see section X). Do not begin a blind nightly comparison: first identify a concrete cause or replace the fixture with a purpose-built minimal homebrew.

Use the public `ctest.zip` fixture attached to Ares [issue #1778](https://github.com/ares-emulator/ares/issues/1778) (source example: [libdragon's ctest directory](https://github.com/DragonMinded/libdragon/tree/trunk/examples/ctest)). Keep the zip out of the Boonta repository. This is a generic homebrew fixture, **not** a live reproduction of the historical upstream bug, which has been fixed. The current CI test connected but trapped during continued execution; the following commands preserve the original local test procedure for future diagnosis, not as an assertion that the test remains unrun:

```sh
# Terminal 1, in the extracted ctest directory:
gdb-multiarch -ex "target extended-remote :9123" -ex "break main" -ex "continue" build/ctest.elf
```

Quickly after GDB starts, launch Ares in terminal 2 from the directory containing the matching test ROM:

```sh
./ares ctest.z64
```

Confirm that GDB connects, reaches `main`, and a second `continue` does not crash the test program or emulator. Record the exact Ares build, host OS, GDB version, port, and any error verbatim. This is a generic debugger smoke test only; it is **not** a SWE1R test. Do not use the game to diagnose a broken generic connection.

### Gate 2 — observe one public lap-code candidate

Only after Gate 1 succeeds and with a lawful local copy of the game loaded, connect with GDB (substitute the actual port if it differs from the default):

```text
gdb-multiarch
(gdb) set architecture mips:4000
(gdb) target extended-remote localhost:9123
(gdb) x/2hx 0x8011900a
(gdb) watch *(unsigned short *)0x8011900a
(gdb) info watchpoints
(gdb) continue
```

The watch expression uses a 16-bit read because the public GameShark listing encodes the address using its `81`/16-bit write form; this is a practical test expression, **not** proof of the underlying field's native type. The public listing only establishes the address as a lap-related cheat target ([TheForce.Net](https://www.theforce.net/videogames/codes/n64/racer.asp)). If the debugger rejects the watchpoint, record the complete error and stop rather than inferring anything.

At a stop, record the observed PC/register state and the value before/after the event where possible, for example:

```text
(gdb) info registers
(gdb) x/8i $pc-8
(gdb) x/2hx 0x8011900a
```

Repeat across a known lap change and compare with the displayed lap. Then follow the actual writer/reader code path locally toward the all-local-participants-done predicate, manager-phase consumers, and a positively identified results UI/resource/scene selector. Keep the raw game binary, extracted assets, local offsets and disassembly in the local workspace; publish only the minimal evidence needed to describe the observed path.

### Interpretation guardrails

- GDB's `watch` stops when the watched expression's value changes, not necessarily on every write. A lack of stops does not by itself prove that the location is never written; consult GDB's [watchpoint documentation](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Set-Watchpoints.html).
- GDB's remote protocol maps write/read/access watchpoints to `Z2`/`Z3`/`Z4` packets ([official protocol reference](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Packets.html)). Source-level support in Ares is documented above, but successful packet negotiation and stop timing still need a live test.
- Do not set a semantic field name based only on a GameShark label or a watchpoint hit. A successful hit is only the first edge of the evidence chain.
- Status at the time this procedure was written was **not executed locally**. The later CI smoke attempt was **NOT PASSED**, with the exact result in section X. The N64 results transition remains blocked/unproven. No ROM, disc image, private disassembly, or proprietary assets were uploaded or committed. No gameplay code changed.



## X. Public ctest Ares/GDB smoke-test result — NOT PASSED (2026-10-21)

The controlled GitHub Actions experiment proposed in [PR #252](https://github.com/Master-Chiken/boonta-reborn-88/pull/252) was run against the public `ctest.z64` homebrew fixture referenced by Ares issue #1778. It is now closed **unmerged** because the smoke test never passed. The source branch and logs remain available. This was a debugger-tooling check only; it was not a SWE1R game run.

- [Latest matrix run #39613630406](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39613630406) built both configured Ares variants and established that the GDB listener/client handshake works.
- **Ares v139:** ctest loaded and the loopback listener opened; GDB connected, but execution trapped in `__rsp_check_assert()` before `main`.
- **Ares v148:** ctest loaded and accepted GDB; execution reached `main`, but the next `continue` trapped in `joybus_exec()`.
- Neither variant passed the bounded continue phase. This cannot be reported as a passing smoke test, nor does it establish that Ares has a general regression.
- The historical [Ares issue #1778](https://github.com/ares-emulator/ares/issues/1778) was closed after upstream fix [PR #1793](https://github.com/ares-emulator/ares/pull/1793), including commit [`dfcd7d4`](https://github.com/jcm93/ares/commit/dfcd7d4fce3d1b9b02df87e5c9f9d16d3ce918fd). The present traps are different observations and their root cause is **unknown**; do not claim the old issue has returned.
- **Disposition:** stop retries of this same ctest setup unless a new falsifiable hypothesis or a deliberately minimal public homebrew isolates the failing subsystem. Do not continue random renderer/audio setting changes. Even a clean generic homebrew pass would only validate the debugger fixture; the required research evidence must still come from a lawful local SWE1R static cross-reference or runtime trace linking the all-finished condition to an identified results UI/resource/scene.


## Y. Local N64 participant finish-threshold result — summary only (2026-10-21)

**Evidence source:** owner-side local static MIPS analysis of an identified US N64 build. Raw addresses, disassembly, string/resource offsets and ROM-derived payload remain in the owner's private notes and are intentionally not reproduced here. This section records only the safe conclusion and the remaining question.

### What the local trace supports

- A configurable option that is strongly associated with the menu's lap count is passed into the race manager as a threshold.
- A participant progress-event counter advances only when the route-progress detector reports an event; reaching that configured threshold enters a distinct state-handling path.
- The path sets a participant state flag that causes the same progress loop to skip further updates for that participant. A separate per-participant guard prevents the threshold-side action from repeating.

**Classification:** strong local static evidence for *per-participant finish handling at the configured threshold*; the semantic interpretation as a completed-lap count is a very-high-confidence inference, not runtime verification. No GameCube/Wii, Dreamcast or PC parity is implied.

### What remains unresolved

- Whether every progress event counted by this path is precisely one lap/finish-line crossing in every mode.
- The direct writer/reader for the displayed `LAP` / `FINAL LAP` HUD value.
- How the race manager aggregates all participants' finish states, selects the next manager phase, and reaches a positively identified results UI/resource/scene destination.

### Next bounded research action

Continue only the last chain: follow the already supported participant finish/skip state into its manager-side readers, establish the all-participants-finished predicate and the state/phase change, then identify the results destination from a distinct consumer/resource association. If the local call chain remains ambiguous, document the exact unresolved edge privately and keep the results transition **BLOCKED / UNPROVEN**. Do not repeat the failed Ares/GDB ctest smoke test without a new falsifiable isolation hypothesis; do not start RE-002 or change gameplay code.

No ROM bytes, raw disassembly, private addresses, extracted course records or commercial assets are published in this summary.



## Z. Alternative local trace via native N64 static recomp — source verified, not executed (2026-10-23)

**Decision:** Do not retry the failed Ares/GDB `ctest` setup. A separate, potentially more useful local observation path is available in the public N64 static-recompilation project [`sp00nznet/racer`](https://github.com/sp00nznet/racer/tree/293032ef29a620edb00ba877276c36ff0936d245), pinned here to commit `293032ef29a620edb00ba877276c36ff0936d245`. This is a testable alternative, **not** evidence that the results transition has been traced. No build was run during this review, no ROM was accessed, and no trace has been captured.

### Direct observations from the public project

- Its [README at the pinned revision](https://github.com/sp00nznet/racer/blob/293032ef29a620edb00ba877276c36ff0936d245/README.md) documents a Windows native static-recompiled build, recompiled functions, and these runtime switches: `SWE1R_WATCH=<N64 address>@<seconds>`, `SWE1R_PEEK=<addresses>`, and `SWE1R_STACKDUMP=<seconds>`. The README reports that the current project reaches a playable Boonta Training Course race, while the overall playable-build milestone remains in progress. This is the upstream project's report, not an independent run by this dossier's author.
- At the same revision, [`src/main.cpp`](https://github.com/sp00nznet/racer/blob/293032ef29a620edb00ba877276c36ff0936d245/src/main.cpp#L276-L325) loads the executable's `.map` symbols. Its crash handler prints the native stack and calls `print_peeks()`; the stack walker resolves native frames to labels such as `func_800XXXXX + offset` and prints PDB source lines if available.
- The [watch implementation](https://github.com/sp00nznet/racer/blob/293032ef29a620edb00ba877276c36ff0936d245/src/main.cpp#L394-L438) arms a Windows hardware data breakpoint (DR0) for a **four-byte write range** across other running threads, repeating thread enumeration to cover new threads. The first matching write enters the top-level exception handler, which prints the writer's stack and configured PEEK values. It is a one-hit diagnostic run; do not assume it continues after the trap.
- The implementation returns without arming if `g_rdram_base` is not initialized after the chosen delay. Also, the current code does not check/report the return value from `SetThreadContext`; the `[WATCH] armed` message by itself is not proof that a watchpoint actually fired. A run with no trap is inconclusive.
- This local toolchain requires the owner to provide a legally obtained ROM and build/run it on Windows; its repository ignores ROM images and generated recompiled code. No ROM, game binary, or extracted asset should be uploaded, committed, or sent to hosted services.

### Alignment requirement and a bounded first trace

The public [TheForce.Net N64 code list](https://www.theforce.net/videogames/codes/n64/racer.asp) labels `0x8011900A` as a Player 1 lap-related GameShark target and `0x80119092` as the analogous Player 2 target. These are watchpoint candidates only; the published labels do not establish a native field type or a finish-state flag.

Because this watch implementation always requests a four-byte range, use the aligned containing words rather than the odd-to-four-byte-alignment halfword addresses themselves:

- Player 1 candidate at `0x8011900A` is contained in the aligned range `0x80119008–0x8011900B`; arm at `0x80119008`.
- Player 2 candidate at `0x80119092` is contained in `0x80119090–0x80119093`; arm at `0x80119090`.

Intel's [Software Developer's Manual section on breakpoint-field recognition](https://cdrdv2-public.intel.com/671427/253669-sdm-vol-3b.pdf) states that four-byte data-breakpoint ranges must start at a doubleword boundary; unaligned addresses do not yield valid results. A four-byte aligned range can also cover an adjacent field, so do not assign semantics from the trap alone. Inspect the mapped PDB line/generated instruction and confirm the actual store's address/width before accepting it as the lap field.

A first, local-only calibration can use the existing runtime environment variables, set **before** starting the already-built executable:

```bat
set SWE1R_WATCH=0x80119008@60
set SWE1R_PEEK=0x80119008,0x80119090
```

Then start the owner's local static-recompiled build and enter a race promptly enough that the delay expires after RDRAM initialization but before the event of interest. Adjust the delay if the trap is from startup initialization or a neighboring field. The delay is measured from process start. Keep the log locally: it may expose native function offsets or source lines which are useful for tracing but should not be copied into the public dossier as raw ROM-derived detail.

### How this could answer the actual RE-001 question

1. Use the public lap candidate only to validate that the watchpoint fires and that the map/PDB stack output is useful.
2. In a separate local run, arm the aligned four-byte word containing the participant finish/skip flag already identified in the owner's private static notes. Keep its address and raw trace private. Arrange for the watch to arm after initialization and before that participant reaches the configured threshold; the first write may otherwise be an initialization, not the finish event.
3. On the trap, identify the actual writer instruction and the recompiled `func_XXXXXXXX + offset` frame. Use the locally generated recompiled C / function-disassembly output to establish the exact store, then search for manager-side reads/consumers of that field.
4. Close the chain only when independent evidence shows the manager's all-participants-finished predicate, the state/phase write and its consumer, and an identified results UI/resource/scene destination. A visible post-race screen is useful observation but does not by itself prove the internal writer/reader chain.

**Current classification:** a concrete, source-verified alternative to the failed Ares debugger fixture exists. It is **not yet tested by this investigation** and supplies no new gameplay finding. The N64 all-participants-finished → results destination remains **BLOCKED / UNPROVEN** until a valid local trace or equivalent positive evidence exists. Do not start RE-002, change gameplay code, publish raw ROM addresses/disassembly, or treat PC source as proof of N64 behavior.

### Host-debugger fallback for macOS/Linux — source verified, not executed (2026-10-25)

**Why:** the pinned Windows watchpoint helper above is not the only possible route. The current upstream [sp00nznet/racer](https://github.com/sp00nznet/racer/tree/1197119fb6d4d1e60e9dfcc3d50d610475433af2), pinned here to commit `1197119fb6d4d1e60e9dfcc3d50d610475433af2`, documents native macOS/Linux builds, while its `SWE1R_WATCH` helper remains Windows-only. Apple's LLDB guide documents expression-based memory watchpoints and supported 1/2/4/8-byte sizes; LLDB lists macOS debugging support for x86_64 and AArch64. See the [upstream README](https://github.com/sp00nznet/racer/blob/1197119fb6d4d1e60e9dfcc3d50d610475433af2/README.md), [upstream setup script](https://github.com/sp00nznet/racer/blob/1197119fb6d4d1e60e9dfcc3d50d610475433af2/setup.sh), [LLDB platform support](https://lldb.llvm.org/), and [Apple's LLDB watchpoint guide](https://developer.apple.com/library/archive/documentation/General/Conceptual/lldb-guide/chapters/C3-Breakpoints.html).

**Source facts checked at the pinned upstream commit:**
- The project records the host pointer to emulated RDRAM in `g_rdram_base` from the `on_game_init(uint8_t* rdram, ...)` callback in `src/main.cpp` (around lines 55–57 and 174–177).
- Its setup script configures the game with `CMAKE_BUILD_TYPE=RelWithDebInfo`, so the standard build is intended to retain debug information. The project still requires the owner's own legal US ROM on the local machine; its setup copies it to a local, git-ignored `baserom.z64`. Nothing should be uploaded or committed.
- The README explicitly says the built-in `SWE1R_STACKDUMP` / `SWE1R_WATCH` crash-trace tools remain Windows-only. The LLDB method below is a separate proposed route and is **not yet validated against this game**.

**Candidate local-only procedure (proposed; do not count as a test until run):**
1. On a host where the pinned upstream really builds and launches, start the game under LLDB with debug information. Stop at `on_game_init` and capture its `rdram` argument into a debugger convenience variable, for example: `expr -- void* $rdram_base = (void*)rdram`. Continue through initialization and into a race. Do not print or publish the ROM or its contents.
2. Pause the process before the public Player 1 lap candidate would change. Set a four-byte, write-only hardware watchpoint on the aligned containing word: `watchpoint set expression -w write -s 4 -- (uint32_t*)((uint8_t*)$rdram_base + 0x00119008)`. This host-pointer offset corresponds to N64 address 0x80119008 (the aligned word containing the public 0x8011900A lap-code candidate). Confirm `watchpoint list` reports an enabled watchpoint before continuing. LLDB may refuse the watchpoint if the host/target has no usable hardware slot; failure to arm is **inconclusive**, not a negative result.
3. On a hit, capture the thread backtrace, registers, disassembly around the stopping instruction, and the changed word locally. Verify the actual store address/width so that a write to a neighboring field is not mislabelled as the lap field.
4. Only after the public calibration has produced a valid trace should a separate local run watch the private participant finish/skip field from the owner's existing notes. Keep that field's address, raw trace, ROM-derived disassembly and resource offsets private. Follow the writer to its readers, then to the manager-level all-finished predicate, state/phase write and an identified results UI/resource/scene.

**Compatibility caveat:** the current upstream macOS setup requests Xcode and the Metal toolchain. Compatibility with the owner's older macOS/Catalina environment has **not** been verified. Do not spend time on a toolchain upgrade or make system changes solely to force this experiment; if the existing host cannot build/run it, retain **BLOCKED / UNPROVEN** and use a suitable supported local host later.

**Evidence boundary:** this improves the documented set of possible local observation methods; no LLDB run, watchpoint hit, race trace, or N64 result-screen discovery is claimed. RE-001's all-participants-finished → results destination remains **BLOCKED / UNPROVEN** until a valid target-specific trace is captured. RE-002 remains parked.

### No-hardware fallback: targeted store instrumentation in N64Recomp — source-derived design, not implemented (2026-10-25)

The native watchpoint path has a verification weakness, and LLDB may not be usable on the owner's older macOS host. A lower-cost reconnaissance step should precede the custom store logger: **use N64Recomp's existing function entry/return tracing mode**, which needs no new generator hook.

**Built-in trace-mode path verified in public source (N64Recomp `ffb39cdad1da5de07eaaa48bd1db4a89a7986771`):**
- The [config parser](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/src/config.cpp#L467-L477) accepts `[input] trace_mode = true` and appends `#include "trace.h"` to generated functions.
- The [function recompiler](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/src/recompilation.cpp#L768-L774) emits `TRACE_ENTRY()` at each generated function entry, and the [C generator](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/src/cgenerator.cpp#L480-L485) emits `TRACE_RETURN()` before returns. The pinned Racer `recomp.toml` does not enable this mode today.
- Racer's [CMake file](https://github.com/sp00nznet/racer/blob/1197119fb6d4d1e60e9dfcc3d50d610475433af2/CMakeLists.txt#L72-L80) adds `RecompiledFuncs` to the generated functions' include path. A local `RecompiledFuncs/trace.h` can therefore satisfy the added include.

**Proposed local-only reconnaissance recipe (not run):**
1. In the private Racer checkout, set `trace_mode = true` inside the existing `[input]` table in `recomp.toml`. Confirm the checked-out `deps/N64Recomp/src/config.cpp` (or the recompiler checkout actually used by the setup) supports this option.
2. From the Racer repository root, run `bash scripts/recompile.sh`. This script removes and regenerates `RecompiledFuncs`, so create `RecompiledFuncs/trace.h` **after** it completes and before compiling the game. The generator emits these macro calls without a trailing semicolon, so each macro definition below includes its own semicolon:
   
   ```c
   #ifndef RE001_TRACE_H
   #define RE001_TRACE_H
   #include <stdio.h>
   #define TRACE_ENTRY() ((void)fprintf(stderr, "[RE001_ENTER] %s\n", __func__));
   #define TRACE_RETURN() ((void)fprintf(stderr, "[RE001_RETURN] %s\n", __func__));
   #endif
   ```
3. Build the game with `cmake --build build --target SWE1Racer`. Do **not** rerun the recompile script after adding `trace.h`, because it deletes that file along with generated sources. For future regeneration, repeat the copy step.
4. Run `build/SWE1Racer` directly from the Racer repository root and redirect both stdout and stderr to a local file such as `re001_trace.log`. **Do not rely on redirecting the upstream launcher’s output:** the launcher generated by `setup.sh` runs the executable with `2> build/swe1racer.log`, so the game's trace messages on stderr are diverted into that separate file rather than the terminal capture. Direct invocation is equivalent for the pinned launcher, whose other action is to change to the repository root. Capture only one controlled race and keep the log private; the trace can be enormous and may slow the game. Do not commit the local `trace_mode` change, `trace.h`, or the log.
4. Inspect the sequence of `func_800XXXXX` entries/returns around the finish event, then cross-reference those functions in the locally generated source. This is candidate discovery only: function traces do not identify individual stores or prove a results-screen consumer.

**Limited smoke check of the example header (2026-10-25):** I compiled and ran the exact macro definitions above in a minimal standalone C17 translation unit with `-Wall -Wextra -Werror`. It printed the expected entry/return events for two test functions. This validates only the macro syntax and basic output; it does **not** verify the header include path in Racer's CMake build, the full generated project, runtime log volume, or any game behavior.

If this function trace is too noisy or too imprecise, the source-instrumented store logger below is the next step. It remains a separate, more invasive experiment. The instrumentation must stay local and preserve the game's original store semantics.

**Public source basis, pinned to N64Recomp commit `ffb39cdad1da5de07eaaa48bd1db4a89a7986771`:**
- [`include/recomp.h`](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/include/recomp.h) defines `MEM_W`, `MEM_H`, and `MEM_B` as direct lvalue accesses into `rdram`. Merely wrapping one macro is not a reliable write-event hook because the generated C uses these expressions on both sides of assignments.
- [`src/cgenerator.cpp`](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/src/cgenerator.cpp#L585-L660), in `CGenerator::process_store_op`, is a centralized source-generation point for MIPS store operations. It emits ordinary word/halfword/byte stores and routes partial/doubleword stores through helper functions. This makes address-filtered logging at each generated store a more promising interception point than patching the memory lvalue macros.
- The exact instruction address is available during recompiler processing: [`src/recompilation.cpp` at the pinned commit](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/src/recompilation.cpp#L119-L124) obtains `instr_vram = instr.getVram()`; lines [597–610](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/src/recompilation.cpp#L597-L610) populate `InstructionContext`, and lines [738–745](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/src/recompilation.cpp#L738-L745) pass it to `process_store_op`. The shared [`InstructionContext` declaration](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/include/recompiler/generator.h) does not currently contain that address. A private patch can add one compile-time `instruction_vram` field and set it when the context is populated, allowing generated tracing calls to include the exact MIPS PC without guessing from the function name.
- [`src/operations.cpp` lines 182–193](https://github.com/sp00nznet/N64Recomp/blob/ffb39cdad1da5de07eaaa48bd1db4a89a7986771/src/operations.cpp#L182-L193) maps MIPS store opcodes to store categories; `process_store_op` then emits `SW/SH/SB/SWC1` as `MEM_*` assignments, `SWL/SWR/SDL/SDR` via helpers and doubleword operations via `SD`. Keep the original store expression intact and add opt-in pre/post trace calls around it. A macro-only hook is insufficient, and replacing the write with a new generic write helper would risk changing emulation semantics.


**Concrete trace contract for a private prototype:** add a debug-only trace token around each generated store instruction. The pre-call receives the emitted MIPS PC, the effective 32-bit N64 virtual address computed from the same base-register expression and signed immediate as the original store, and the store category; it snapshots the aligned target word only when the operation can affect it. The existing generated store then runs unchanged, after which the post-call reads the word again and prints the PC, category, effective address, and before/after values. Use the store category to account for byte/halfword swizzling, partial stores (`SWL/SWR/SDL/SDR`), and doubleword writes. Enable this only in a local trace build and only for the one target region to avoid flooding output. This describes a design, not checked-in helper code.

**Minimum falsification tests before using it on the game:** use a synthetic RDRAM buffer and generated/store-helper fixtures for `SW`, `SH`, `SB`, `SWL`, `SWR` and a doubleword case. Assert (a) an overlapping write produces the right PC/category/address and before/after word, (b) a neighboring non-overlapping write does not trigger, (c) same-value writes are still reported as writes when desired, and (d) the traced and untraced versions leave identical RDRAM bytes. Only after those pass should a private local game run calibrate the candidate lap field. These tests have not been written or executed.

**Bounded implementation/test plan — proposed only:**
1. On a private local checkout, add an opt-in debug-only filter for the aligned containing word `0x80119008–0x8011900B` (the public lap-candidate address is `0x8011900A`). Log only writes whose effective address range overlaps that word; account for byte/halfword XOR-swizzling and for unaligned/doubleword instructions. Do not add this patch to the public Boonta gameplay code.
2. Rebuild the recompiler and game from the owner's own legally obtained local ROM. The instrumented build may run slower; use it for tracing only, never as a release build.
3. Calibrate against a known lap change. Accept the instrumentation only if the log identifies a real write consistent with the lap change and the generated function/source confirms the access width/address. A silent log, compile-only success, or an initialization write is inconclusive.
4. Only after that calibration, apply the same filtered logging to the private participant finish/skip field, then follow its readers to the all-participants-finished predicate, manager state/phase write, and positively identified results UI/resource/scene. Keep ROM-derived addresses and trace output local.
5. If codegen instrumentation proves too invasive, return to a supported-host debugger/watchpoint route; do not interpret a missed trace as evidence that the field is never written.

**Classification and limits:** this is a source-backed implementation hypothesis, not a patch or an executed experiment. It sees recompiled CPU store instructions that pass through the generated code; it may miss host-side runtime writes or transfers, so its coverage must be checked before treating absence as meaningful. No ROM, generated function source, binary, or raw trace is to be committed or uploaded. RE-001 remains **BLOCKED / UNPROVEN** until the manager-to-results destination chain is positively established; RE-002 stays parked.

### Upstream build/test boundary — checked 2026-10-25

Pinned upstream current `main` is `1197119fb6d4d1e60e9dfcc3d50d610475433af2` ([v0.3.0](https://github.com/sp00nznet/racer/releases/tag/v0.3.0)). Its latest work adds Linux/macOS packaging and Linux arm64/Android build targets; this improves the available ways to build the host application, but does not by itself close RE-001.

- The upstream [build workflow at that exact revision](https://github.com/sp00nznet/racer/blob/1197119fb6d4d1e60e9dfcc3d50d610475433af2/.github/workflows/build.yml) explicitly says it uses stand-ins for ROM-derived files. It creates `RecompiledFuncs/stub.c` and an empty `rsp/aspMain.cpp`, then compile-checks the frontend and `src/main.cpp`. Its successful CI therefore confirms compilation of host/build integration only; it does **not** compile the full ROM-derived game functions, run a race, or validate the results-screen transition. The full local setup uses the owner's own ROM and produces the actual build on that machine.
- Upstream [release v0.2.0](https://github.com/sp00nznet/racer/releases/tag/v0.2.0) states that the macOS build was compile-checked only and had not been played on a Mac; its built-in crash-trace tools are Windows-only. [Release v0.3.0](https://github.com/sp00nznet/racer/releases/tag/v0.3.0) says Android was tested in an x86_64 emulator to the intro and Linux arm64 only in an emulated container, not real hardware. These are useful status disclosures, not platform-runtime proof.
- In the current [Windows watchpoint implementation](https://github.com/sp00nznet/racer/blob/1197119fb6d4d1e60e9dfcc3d50d610475433af2/src/main.cpp#L410-L438), the `[WATCH] armed` message is printed before thread contexts are updated. The worker also does not check whether `CreateToolhelp32Snapshot`, `SuspendThread`, or `SetThreadContext` succeeds, and it does not report how many target threads were successfully configured. It can therefore log “armed” even when no game thread has the breakpoint installed. A log saying “armed” is not sufficient evidence: the run must actually hit the intended watchpoint and yield a credible writer trace.

**Operational decision:** first inspect whether the existing owner machine can build/run this upstream revision without a system/toolchain upgrade. If not, do not force a Catalina/Xcode migration for this research task; use a suitable already-available supported host when practical. A valid trace must stay local because it can expose ROM-derived addresses, disassembly and resource details.

**Boundary unchanged:** no full-game build or host debugger session has been executed by this review. The N64 all-participants-finished → manager state/phase → identified results UI/scene chain remains **BLOCKED / UNPROVEN** until local target-specific evidence exists.


## AA. Additional local N64 finish-state cross-check — static only (2026-10-25)

### New bounded result

A further local, static pass over the owner's N64 reference ROM strengthens the **participant-level** part of the finish chain:

- The configurable lap-related value is passed into the race manager's target field.
- A participant's progress-event counter advances only when the route-progress helper reports an event.
- When that counter reaches the configured target, a one-time branch changes that participant's state; the normal participant-update loop then skips that participant on subsequent updates.
- The manager has separate per-frame and message/render paths. The inspected post-update path revisits all configured participant records, but this pass did **not** establish a definitive all-participants-finished aggregation that switches the race manager into a results phase.

This makes participant finish/disable handling **strongly supported by static control flow**. It does not yet prove how every non-player racer is included in the race's global completion condition.

### Results UI and lifecycle disambiguation

The ROM's text data contains a user-facing “Results” entry, but no validated code/data cross-reference links that entry to the participant-threshold branch or a particular scene-load routine. The shared `Fini` and `Abrt` message tags are used by generic lifecycle paths; neither tag, by itself, identifies a results transition. They must not be used as a shortcut for the missing link.

### Evidence boundary and next step

This was a **local static disassembly/cross-reference pass only**. It did not execute the game, an emulator, or a freshly built static-recomp executable. No ROM bytes, disassembly, exact local addresses, or extracted assets are included in this public dossier.

**RE-001 status remains BLOCKED / UNPROVEN for the full chain.** The next bounded task is to identify (a) the writer/consumer that aggregates participant completion into a manager phase transition, and (b) a direct consumer of the results UI/resource/scene identifier. Do not modify Boonta gameplay logic or infer cross-platform parity before those links are demonstrated.

## AB. Local-player completion aggregation and manager-phase trace — static only (2026-10-25)

### New result: the local-player completion gate is now traced

A second pass over the private local MIPS disassembly closes the specific gap recorded in section AA: the race manager does have a completion aggregation for its registered local-player slots.

- The active manager update provisionally advances its low-nibble phase from the running value to an intermediate post-race value before iterating the participant records.
- For each participant still eligible for normal progress updates, the manager compares that participant against the local-player references. If a matching local participant has not yet acquired the participant-level finish state, the manager writes the running phase back. Consequently, the intermediate phase is retained only when no unfinished participant matches a registered local-player slot.
- The participant-level state being aggregated is the same one reached through the configured progress-event threshold path documented above. The flow is now supported statically from configured target → participant finish/skip state → local-player aggregate → intermediate manager phase.

This is evidence of a real all-local-participants-finished gate, rather than merely a post-update loop that revisits participant records. It is still static control-flow evidence, not a runtime observation.

### What follows the intermediate phase

The manager's phase callback has additional guarded stages after that gate. The intermediate phase waits on a generic event/mask condition; once that condition succeeds, it schedules a delayed `Fini`-tagged action. A later handler performs cleanup and can advance the manager into another phase under an additional global-state condition.

These are confirmed intermediate state transitions, but their labels alone do not establish a results screen. The local code paths inspected so far do not directly bind the local-player aggregate or those generic lifecycle actions to the text-bank entry “Results”, a results renderer, or a positively identified scene/resource load. That text entry sits among career/circuit and winnings strings and is therefore only a search lead.

### Updated classification and next bounded step

- **Supported statically:** configured progress-event threshold → participant finish/skip state → local-player completion aggregate → intermediate manager phase; then guarded generic-event and delayed lifecycle processing.
- **Still blocked:** the exact state/resource/scene that presents the race results, and the complete route from the manager's post-race phase to that destination.
- **Not executed:** no emulator session, physical console session, or freshly built full-game static-recomp run was performed. The ROM and the exact address-level trace remain private; no ROM bytes, disassembly, generated C or game assets were added to this repository.

**RE-001 remains BLOCKED / UNPROVEN for the full finish-to-results chain.** The next test must resolve a direct consumer of the results UI/resource/scene identifier from the post-race manager/lifecycle path. Do not infer that destination from `Fini`, from the standalone “Results” string, or from the phase number alone.
## AC. Results-panel consumer cross-reference — static only (2026-10-28)

### New result: the results UI is identified at code-consumer level

A fresh local disassembly pass over the owner's existing US N64 ROM goes beyond the isolated text-bank hit:

- A game routine loads the `~c~sResults` text-bank entry and passes it directly to the game's 2D text/UI helper with layout arguments. This is a direct consumer of the Results label, not merely a string-search match.
- The same routine iterates participant records, builds/uses an ordering array, and compares participant ordering fields to produce a leaderboard. Nearby formatting paths handle placement prefixes, racer-name fields, and a winnings/prize line. Together, these are strong static evidence for a results/placement-panel builder.
- The caller is reached through a `Hang`-labelled object/callback registry and a particular object-substate branch. That supplies a concrete UI-side path to investigate, without assuming the registry label alone describes a scene.

### What this closes — and what remains open

- **Supported statically:** configured progress-event threshold → participant finish/skip state → local-player completion aggregate → intermediate manager phase (Section AB); separately, a concrete results/placement-panel builder and its `Results` text consumer under a `Hang` object substate.
- **Still unproven:** I have not yet demonstrated the edge from the manager's intermediate/delayed lifecycle path to that particular `Hang` instance/substate, nor found a confirmed scene/resource-load identifier for the complete destination. Generic `Fini`/`Abrt` tags do not close this gap. The full finish-to-results chain therefore remains **BLOCKED / UNPROVEN**.
- **Not executed:** no emulator or game runtime was launched, and no freshly built full-game static-recomp executable was run. This is static ROM disassembly only. No ROM bytes, raw disassembly, exact local addresses/offsets, extracted text/asset dumps, or gameplay changes are included in this repository.

### Next bounded research step

Trace how the relevant `Hang` object's substate is initialized and reached, then locate the manager/lifecycle writer or dispatcher that connects the post-race phase to it. Alternatively, identify a direct scene/resource-transition consumer. Do not change Boonta gameplay logic until that edge is evidenced.

## AD. Manager-to-lifecycle call-path cross-check — static only (2026-10-29)

### New result from the bounded follow-up

A further static pass confirms that the race-progress manager's per-frame callback invokes a separate manager/lifecycle routine before its own low-phase dispatch. That routine inspects the race/participant context and, on selected branches, invokes a guarded transition helper with a lifecycle token corresponding to either normal finishing or aborting. The helper mutates the **manager object passed to it** (including its state/transition bookkeeping) and touches several named global/resource registries.

Separately, the `Hang`-labelled object has two distinct control paths:

- its main update dispatches through a primary-state table, with one state using a nested substate field;
- its message callback recognizes lifecycle/control tokens including `Fini`, `Abrt`, `Load`, `RStr`, and `Stop`, and updates lifecycle flags/secondary bookkeeping.

In the message-handler paths checked during this pass, no direct write to the `Hang` object's primary-state selector was observed. The shared token vocabulary therefore does **not** prove that the manager's finishing transition selects the results-panel substate. Nor does a call that changes the manager object's own state identify a particular `Hang` instance.

### Evidence update

- **Added:** manager update → manager/lifecycle routine → guarded normal-finish/abort transition on the manager object; independently, `Hang` main-state and lifecycle-message handling are separate mechanisms.
- **Still blocked:** no direct producer-to-consumer edge yet connects the manager's post-race phase or transition token to the specific `Hang` instance/substate that consumes the Results heading and formats the ordered participant list.
- **Not performed:** no emulator/session was launched, no runtime trace/watchpoint result was obtained, and no full static-recomp build was executed. These conclusions remain from private, local static analysis only. No ROM bytes, raw disassembly, exact offsets/addresses, text dumps, or game assets are included here.

### Next bounded test

Follow the manager's guarded transition into the object/resource dispatcher and find either (a) an explicit message send/receiver pair for the target `Hang` instance, or (b) the writer that assigns the primary/nested state used by the already identified results-panel builder. If neither edge can be resolved statically, preserve the result as **BLOCKED / UNPROVEN** and make no gameplay-code change based on this hypothesis.


## AE. Delayed finalization broadcast to registered callbacks — static only (2026-10-29)

### New result: the manager-to-Hang link is supported at message-dispatch level

The bounded follow-up connected more of the producer/consumer path than Section AD:

1. The race manager's finishing/finalization path invokes a guarded transition helper on the manager object. That helper records the incoming lifecycle token on the manager and schedules a short delayed transition, while performing separate cleanup/notification work for other registered components.
2. When the manager's delay expires, its update path passes the stored token into the manager message handler.
3. On the handler's ordinary broadcast path, the message is sent through the engine's generic **all-registered-types** dispatcher. Depending on global mode flags, the original pending token is propagated or an abort token is substituted. A separate mode-gated path bypasses this broadcast, so the behavior is conditional rather than universal.
4. The `Hang` object's previously identified message callback has explicit finalization/abort handling. The generic dispatcher walks eligible registered callbacks, so there is now a statically supported manager-lifecycle → global callback dispatch → `Hang` message-handler edge on the ordinary broadcast path.

This is the first producer-to-consumer connection found for the lifecycle **message**. It is stronger than matching token names alone.

### Remaining gap: message reception is not proof of the results substate

The newly connected edge still does **not** show that receiving the finalization message assigns the exact primary/nested state consumed by the Results/placement-panel builder:

- The `Hang` message handler updates lifecycle flags and its message-sequence bookkeeping; it does not directly write the primary-state selector in the paths checked.
- The results/placement-panel builder remains identified separately under a `Hang` state/substate branch.
- The state/object relationship that takes the receiving instance from its lifecycle sequence into that exact rendering branch remains unproven. The mode-gated bypass and abort override also mean the broadcast path cannot be assumed for every race/session.

### Evidence classification after this pass

- **Supported statically:** configured progression threshold → participant finish/skip handling → manager post-race/finalization path → delayed manager message handling → conditional all-types callback dispatch → `Hang` callback recognizes finalization/abort messages.
- **Supported separately:** a `Hang` state/substate branch consumes the Results heading and formats ordered participants, placements/names and prize-related text.
- **Still blocked:** a direct writer/transition proving that the *same relevant Hang instance* enters that exact results-panel state because of the manager lifecycle message.
- **Not performed:** no emulator, live-game trace, write-watchpoint result, or full static-recomp runtime was executed. No ROM bytes, raw disassembly, exact addresses/offsets, extracted text/resource dumps, or game assets were added here.

### Next bounded test

Inspect the `Hang` receiver's lifecycle-sequence continuation and its state dispatcher together: identify the writer or branch that changes the selector/substate used by the Results-panel consumer, then connect it to the message-driven path above. If no such direct state assignment/call can be established, leave the full finish-to-results chain **BLOCKED / UNPROVEN** and do not infer the UI transition from successful message delivery alone.


## AF. Same-object state transition reaches the Results-panel builder — static only (2026-10-29)

### New result: the previously missing state edge is now connected on the ordinary/default path

The follow-up resolves the specific state-dispatch gap left in Section AE:

1. The `Hang` lifecycle callback's `Fini` branch does more than update flags. It selects the next primary state from its internal lifecycle sequence and passes the same object plus that selected state to the class's state-transition helper, unless a separate global guard suppresses this step.
2. The transition helper stores the new primary state on that object, preserves the previous primary/nested state for transition handling, and invokes that object's state updater and presentation routine for nonzero target states.
3. The updater's own dispatch table maps the default/sentinel-sequence finishing path to a nested display mode used by the same object's presentation routine. The presentation routine contains the previously identified direct consumer of the Results heading and the ordered participant/placement/prize formatting.
4. The object is passed consistently through the lifecycle receiver → state setter → state updater → presentation routine. This closes the formerly missing same-instance link; it is no longer just a match between global message names and an independently found UI label.

### Revised assessment

**The static finish-to-results route is now connected for the ordinary all-types broadcast and default/sentinel lifecycle path**, subject to the state-transition guard described above. Other internal lifecycle-sequence values select different primary states, and the dispatcher can substitute an abort token or bypass the broadcast under mode-specific conditions. Do not generalize this one traced path into a claim that every session or mode follows it.

This remains static control-flow evidence, not proof of runtime timing or a successful visible results screen. A true end-to-end runtime confirmation would require observing the target game/emulator transition or a correctly instrumented static-recomp execution; neither was performed in this pass.

### Next validation

- Keep this finding as **STATIC PATH CONNECTED / RUNTIME UNVERIFIED**.
- If the private test environment becomes available, record whether the ordinary finishing path reaches the Results panel, and separately exercise the mode-gated bypass/abort paths.
- Do not change the clean-room GameCube implementation solely on the basis of this N64 control-flow result, and do not infer parity with PC, Dreamcast, GameCube or Wii.
- No ROM bytes, raw disassembly, exact addresses/offsets, extracted resource/text dumps or game assets were added to this public dossier.


## AG. Fini default-state dispatch cross-check — static only (2026-10-29)

### Result: the default Fini state index reaches the previously identified Results/standings builder

The private instruction-level cross-check confirms the final state-table edge described in section AF:

- On the ordinary `Hang` `Fini` path, when the optional next-state selector is absent/out of range (the sentinel/default case) and the global transition guard permits the change, the handler leaves the selected primary state at index 5 and passes that value to the state setter for the same object.
- The `Hang` primary-state dispatch table maps index 5 to a handler that calls the screen/standings routine already identified in section AC. That routine orders participant records and constructs the corresponding on-screen elements, including placement/racer data and result-related text. This is a direct state-table and same-object call edge, rather than an inference from the shared `Fini` tag alone.
- The nested-state mapping can override the default index when its selector is in the valid range; a separate global guard can alter or suppress the ordinary state change. Abort substitution, broadcast bypass and alternative lifecycle sequences remain separate cases.

### Updated evidence classification

For the ordinary default/sentinel `Fini` path, the static chain is now **CONNECTED THROUGH THE RESULTS/STANDINGS STATE HANDLER**:

configured progress target → participant finish/skip state → local-player completion gate → manager delayed finalization → registered-callback broadcast → `Hang` `Fini` receiver → same-object primary-state setter → state-table handler → Results/standings presentation builder.

**Runtime remains unverified.** No emulator or live game session was run; no write-watchpoint capture or full static-recomp runtime was executed. This conclusion is limited to the statically traced default path and is not evidence that every game mode reaches the screen, nor that N64 internals match GameCube/Wii.

The exact local ROM offsets, instruction addresses, raw disassembly, resource bytes and assets remain private and are not included in this public dossier. No clean-room gameplay code was changed based on this N64-only trace.


## AH. Fini selector matrix: Results is a conditional subpath — static only (2026-10-29)

### Secondary-sequence selector result

The follow-up decoded the control-flow distinction behind the sentinel/default route:

- The `Fini` handler begins with primary target index 5. If the object's secondary sequence selector is the negative sentinel, that target is left unchanged (provided the global transition guard permits the state setter), so the same-object primary-state table reaches the Results/standings builder described in section AG.
- If the selector is in its valid nonnegative range, a local jump table dispatches to alternate branches that replace the primary target with other state indices. Most of these branches reset the sequence selector to the negative sentinel; a smaller high-value range advances it through additional intermediate transitions before it is reset. An out-of-range nonnegative selector takes an alternate state branch rather than the Results target.
- Consequently, the static state edge is direct and well-supported **conditional on the sentinel/default branch**, but this does not by itself prove that an ordinary completed race enters `Fini` with that selector already negative, nor that a particular mode completes the intermediate sequence and delivers the subsequent `Fini` invocation.

### Updated scope

The defensible conclusion is: **the `Fini` receiver can reach the Results/standings builder on its sentinel/default subpath; other selector values deliberately take alternate state paths.** RE-001's remaining limitation is now explicit: whether the relevant live race-completion path reaches that subpath, and the visible/runtime transition, remain unverified.

No runtime/emulator execution was performed. Exact local branch addresses, offsets, raw disassembly, ROM bytes and extracted resources remain private; no retail-game payload was added to the repository and no clean-room GameCube/Wii behavior was changed based on this N64-only analysis.


## AI. Token-specific correction: the selector reset belongs to abort handling — static only (2026-10-29)

### Correction after separating each Hang message branch

A fresh instruction-level pass separated the `Hang` message switch cases instead of grouping them by shared lifecycle vocabulary:

- The `Abrt` branch contains the call that initializes the object's option/sequence data and resets the secondary state selector to its negative sentinel. That reset must **not** be used as evidence that the normal `Fini` receiver enters with the sentinel already set.
- The `Fini` branch sets the default primary target to the Results/standings state, reads the object's secondary selector, and can replace that target with an alternate state from its selector jump table. Some nonnegative values are advanced and others are reset as part of the selector's own sequence. The negative-sentinel path continues with the default target only when the global transition guard permits the state setter.
- A separate timed/UI routine writes a nonnegative sequence value (15) through its incoming object pointer under a mode/timer condition. The inspected code does not establish that this pointer is the same `Hang` instance involved in the race's finalization path, so this is a possible setter lead—not a proven producer edge.

### Refined finding

Sections AF–AH accurately establish the **conditional consumer-side path**: if the relevant `Hang` receiver reaches `Fini` with the sentinel/default selector and passes the transition guard, the same-object state dispatch reaches the Results/standings builder.

What remains unproven is the **producer-side entry condition** at the end of an actual race: which secondary selector value is present on the relevant object when the manager broadcasts normal finalization, and whether earlier lifecycle-sequence transitions bring it to the sentinel/default path. Therefore, do not describe the full live race finish-to-results path as connected yet.

No emulator, runtime instrumentation, write-watchpoint trace or full static-recomp execution was performed. No ROM bytes, raw disassembly, exact local addresses/offsets, text/resource dumps or extracted assets are added to this public dossier; no clean-room gameplay behavior is modified based on these N64-only observations.


## AJ. Re-audit of lifecycle message producers: normal Fini delivery is still unproven — static only (2026-10-29)

### Dispatcher call-site audit and relay distinction

The generic message dispatcher does support broadcasts to all registered types. Four direct call sites targeting `All!` were identified in the disassembled code paths audited:

- Two send the `Paws` pause-state message.
- One broadcasts `Abrt` (abort) through a helper whose direct caller explicitly sets that token.
- A fourth is in a manager/message handler that first handles its **incoming** token. When it receives `Fini` and the associated global guard permits, it performs a `RSet`-related operation and then can relay the original token through the all-types dispatcher; under another global-state condition it substitutes `Abrt` instead.

The fourth site therefore confirms a **conditional relay of an already-received Fini token** to registered callbacks. It does **not** identify the producer of the first normal `Fini` message from the race-finish manager. The other audited all-types broadcasts do not supply that missing producer edge. No direct first-sender path from the all-local-finished aggregate to this relay's incoming `Fini` has been established in this pass.

### What remains directly supported

- The `Hang` message receiver has distinct cases for `Fini`, `Abrt`, `Load`, `RStr`, and `Stop`.
- On the receiver's `Fini` case, the default primary target is the Results/standings state, but a secondary selector can override that target, and a global guard can suppress the transition.
- The Results/standings consumer exists under the relevant state-table handler.
- A separate state-0 path on the `Hang` class can write selector value 15 under a guarded global-event condition. This confirms a real selector writer on the `Hang` type; it does **not** prove that the condition is reached by a normal race finish.

### Revised RE-001 conclusion

The evidence supports the **receiver-side conditional path** and a **conditional Fini relay**, but the initial producer/delivery edge remains open. It is not yet proven that the race manager's all-local-finished condition emits the first normal `Fini`, that the relevant `Hang` object receives it in the required selector state, or that the Results panel appears in a real session.

**Status: BLOCKED / UNPROVEN at the race-finish → initial Fini producer edge; receiver-side Results path conditionally identified.**

No emulator, watchpoint capture, visible run, or full static-recomp runtime was executed. The local ROM, raw disassembly, exact local addresses/offsets and extracted resource payloads remain private; no game assets or retail code were added to this repository and no clean-room GameCube/Wii behavior was changed based on the N64 trace.


## AK. Manager phase callback schedules the first normal Fini transition — static only (2026-10-29)

### New producer-side result from the local instruction trace

The manager update/state callback contains a direct `Fini` transition request that was not covered by the earlier inventory of direct `All!` broadcast call sites:

- The callback first dispatches from the manager object's low-nibble phase/state. In one phase branch, it calls the event/mask helper with mask `0x201`.
- If that helper reports the condition satisfied, the branch passes the same manager object and the literal `Fini` token to the guarded transition helper. A separate branch in the same callback passes `Abrt` to that helper, so abort and normal-finish requests are distinct paths.
- The helper checks a global re-entry guard, updates the manager object's state/timer bookkeeping, stores the requested lifecycle token in the manager's pending-transition field, and runs several cleanup/notification hooks. This is a **scheduled manager transition**, not an immediate `All!` broadcast.
- On the delayed path already described in Sections AB/AE, the manager later processes that pending token. Its message handler has the conditional all-types relay that can forward the token to registered callbacks, including the `Hang` receiver; global-mode conditions can bypass the broadcast or substitute `Abrt`.

This links the manager's intermediate phase callback to the first normal `Fini` transition request at static call-site level. It corrects the narrower Section AJ conclusion, which inventoried `All!` calls but did not connect this earlier manager-state callback that queues the token.

### Revised chain and remaining conditions

The best-supported static chain is now:

`all-local-participant completion gate` → `intermediate manager phase` → `event/mask condition (0x201)` → `manager schedules Fini` → `delayed manager message handling` → `conditional all-types relay` → `Hang Fini receiver` → `same-object Results/standings state handler on the sentinel/default selector path`.

The chain is **statically connected as a conditional path**, rather than blocked at an unidentified first `Fini` request. It is not yet proof of the actual live path: the global re-entry/mode guards can change the route, the dispatcher may bypass or replace the relay with abort, and the secondary selector value on the relevant `Hang` instance at actual race completion remains unobserved. Runtime display remains unverified.

### Boundaries

This was a private local instruction/control-flow check against the user-provided N64 ROM. No emulator, live game session, write-watchpoint capture or full static-recomp execution was performed. Exact ROM offsets, instruction addresses, raw disassembly, resource bytes and extracted assets remain local and are not included in this public dossier. This N64 finding does not justify a GameCube/Wii gameplay change or platform-parity claim.


## AL. State-table handoff confirms the conditional all-types relay — static only (2026-10-29)

### Follow-through from the manager's `Fini` request

A narrower pass traced the manager callback's state-table entries and the delayed-token consumer:

1. The callback's state dispatch has a distinct handler for the phase branch that tests event/mask `0x201`. The test must return nonzero before that branch requests `Fini`; the condition is not an unconditional finish broadcast.
2. The guarded transition helper stores the pending `Fini` token, changes the manager object to its delayed-processing state, and sets its delay/timer bookkeeping. This confirms that the token is queued for a later update rather than sent immediately.
3. The delayed-processing state reads that stored token and passes it into the manager's message handler.
4. The message handler has two materially different routes. Under one global mode flag, an incoming `Fini` takes a special cleanup/state-transition path that bypasses the ordinary all-types broadcast. Otherwise it composes a manager event and broadcasts through the generic `All!` destination. On that broadcast route, a separate global-mode condition can substitute `Abrt` for the pending `Fini` token.
5. Consequently, the `Hang` receiver-side Results path is only reachable if the event/mask condition succeeds, the manager uses the ordinary relay route rather than the special bypass, the abort override does not apply, and the receiving `Hang` object is in the permitted selector/guard state.

### Current evidence grade

The static chain is now connected through the **conditional broadcast mechanism**:

`local-player completion aggregate` → `intermediate manager phase` → `event/mask 0x201 succeeds` → `queue Fini` → `delayed manager state` → `message handler` → `conditional All! relay / possible Abrt substitution / bypass` → `Hang receiver` → `conditional Results/standings state handler`.

This improves the control-flow trace; it does not collapse those gates into an observed live execution. We still lack a runtime observation of the actual flag/selector values at the end of a real race and the visible Results screen. No emulator, write-watchpoint capture or full static-recomp runtime was executed, and there is no GameCube/Wii parity claim.

The private ROM, exact local instruction addresses/offsets, raw disassembly, text/resource bytes and extracted assets remain local. No game payload or N64-derived gameplay change was added to Boonta.


## AM. Event-mask provenance cross-check: 0x201 is a generic input-edge mask, not a named finish event — static only (2026-10-29)

### New result: the mask's data source is the input-edge subsystem

A local static cross-check of the mask-query helper and its producer narrows the meaning of the 0x201 condition used by the manager state callback:

- The query helper checks a shared array of per-input-source event words, with mode/selection guards. In some modes it checks one selected word; in another it examines the first two words and updates the selected-source index based on which word matches.
- A separate input-update routine constructs the event words by reading the current controller/input packet, building a button-state mask, comparing it with the prior mask, and writing the resulting press/release edge masks into the shared arrays. The array queried by this helper is the press-edge side of that input state.
- The manager callback passes 0x201 to this generic query. The helper applies a bitwise mask; it does not identify the bits as a race-finish notification. The two bit meanings and their high-level control labels are not yet independently established here.

### Correction to the interpretation of Sections AK–AL

Sections AK–AL correctly record a conditional static call path from the manager phase callback through a guarded/delayed Fini request and the conditional relay. However, the 0x201 predicate must **not** be described as proof that all local racers have finished or as a dedicated “race finished” event: its data source is a generic input-edge mask. This makes a controller/input-triggered continuation (for example, a confirmation/skip action) a plausible explanation, but the exact high-level meaning is not yet proven.

The evidence grade is therefore refined to:

**CONDITIONAL STATIC CALL PATH CONNECTED / EVENT SEMANTICS AND RACE-FINISH CAUSALITY UNPROVEN / RUNTIME UNVERIFIED.**

The participant threshold path still supports a per-participant finish/disable transition. The Hang receiver still has a conditional state path into the Results/standings builder. What is not yet proven is that the manager's Fini request is causally produced by the aggregate completion of all local racers, rather than a generic input edge in a later phase. The global-mode bypass, possible Abrt substitution, transition guard and secondary selector conditions remain.

### Next bounded trace

1. Identify the exact meaning of the input-mask bits 0x001 and 0x200 from their source fields and downstream consumers; do not assign button names from bit positions alone.
2. Trace the manager object's phase/state writer into the callback branch that tests this mask, to determine whether that branch is a results-screen acknowledgement/skip, a manager cleanup action, or something else.
3. Keep the full live finish-to-visible-Results chain **UNPROVEN** until the producer/consumer relationship is established or runtime evidence is obtained.

No emulator, visible race session, watchpoint capture or full static-recomp runtime was performed. No ROM bytes, raw disassembly, exact local instruction addresses/offsets, extracted resource bytes or assets are added to this public dossier. No clean-room GameCube/Wii behavior was changed from this N64-only trace.

## AN. Input-word translation narrows the 0x201 source, but not its high-level meaning — static only (2026-10-29)

### New input-side evidence

A further local static pass followed the packed input word through the routine that builds the internal input-state mask:

- The internal mask is **not** a direct copy of the raw input word. It is assembled through separate source/configuration gates and remapping branches.
- One branch contributes internal bit `0x001` when source-word bit `0x400` is set and that branch's gate permits the mapping.
- A separate branch contributes internal bits `0x100` and `0x200` together when source-word bits `0x080` and `0x200` are both set and its own gate permits the mapping.
- These are input-state-mask observations, upstream of the press-edge words that the manager's generic query reads. They do not establish a one-to-one identity between an internal bit and a physical button, because the precise packed source-field semantics, gate values and active input-source mode have not been resolved.

### Downstream manager reaction

The manager branch that queries mask `0x201` converges on a state-change path that replaces the object's low-nibble state index with `5`, resets its timer-like field, and invokes a generic state-transition helper. A separate object-flag condition can reach the same state-change path even when the mask query does not match.

This supports a more precise but still limited statement: **the branch reacts to a generic input-edge mask or an alternate object-flag condition by moving to state index 5.** It does not identify state 5 as Results, prove that the queried mask is a dedicated finish signal, or show that a normal completed race necessarily takes this route.

### Remaining bounded trace

1. Resolve the packed input word and the gates that enable the two remapping branches before assigning named controller controls to `0x001` or `0x200`.
2. Identify the state-index-5 handler/consumer and its callers, then establish whether its entry is causally downstream of normal race completion or an input/skip/cleanup interaction.
3. Keep the full finish-to-visible-Results path **UNPROVEN / RUNTIME UNVERIFIED** until those links or a real runtime observation exist.

No emulator, visible race session, watchpoint capture or full static-recomp runtime was performed. Exact local addresses/offsets, raw disassembly, ROM bytes and extracted assets remain private. No game payload or N64-derived gameplay change was added to Boonta.

## AO. External N64 recompilation is a runtime-test lead, not finish-to-Results evidence — public-tooling audit (2026-10-29)

### What the public project claims

The public [`sp00nznet/racer` repository](https://github.com/sp00nznet/racer) describes an N64 static-recompilation workflow built around N64Recomp. Its README reports a stable game loop, visible frames through menus and races, SDL controller input and a race that can be driven; its [release page](https://github.com/sp00nznet/racer/releases) lists v0.3.0 dated 2026-10-25 and native installers for Windows, Linux and macOS. Those are project-maintainer status claims, not an execution performed in this RE-001 session.

The README also says the `SWE1R_STACKDUMP` / `SWE1R_WATCH` crash-trace tools are Windows-only. Consequently, the project is a credible *candidate* for a visible runtime check, but its documented tooling does not provide a ready-made cross-platform watchpoint path. A normal race run alone would show the external recomp's behavior; it would not by itself prove the specific producer/consumer edge needed in this dossier.

### What this changes — and what it does not

- **Changes:** there is now a concrete third-party runtime avenue to evaluate for the N64 reference, rather than treating “no emulator installed in the current command-line environment” as the only option. A useful instrumented session would need to observe the manager phase / pending lifecycle token, the queried input-edge condition, the receiving object's selector, and entry into the Results/standings builder on the same run.
- **Does not change:** no `sp00nznet/racer` binary was built or launched in this session, no runtime values or watchpoint trace were obtained, and the README status is not independent verification. The full ordinary race-finish → visible-Results path remains **UNPROVEN / RUNTIME UNVERIFIED**.
- **Source boundary:** this audit imports no recompilation code, decompilation code, retail-game data or assets into Boonta. The external project remains a separate analysis/runtime reference; no N64-derived GameCube/Wii gameplay implementation is justified by this result.

### Next bounded action

If a compatible instrumentable build becomes available, record one reproducible visible race completion and capture the four state observations above. Otherwise, continue the static producer/consumer audit without assigning physical button names to the unresolved packed input bits. Keep RE-002 parked.

## AP. Code-section VMA audit limits conclusions that depend on external state tables — static mapping correction (2026-10-29)

### Why this re-audit is required

The prior local scratch ELF flattened a much larger ROM range into one `.text` mapping. That is not a valid global virtual-address map for the whole ROM. The public N64Recomp reference project provides an explicit main-code section in its `symbols.toml`: ROM offset `0x1000` maps to VMA `0x80000400`, with code size `0x98000` (ending at VMA `0x80098400`). Its `recomp.toml` also declares `0x80000400` as the entrypoint. The code-only rebase is consistent with the first boot trampoline, but it does **not** define the virtual mapping of later data, global tables or overlays.

The manager callback's code is inside this mapped main-code range. It reads a jump-table pointer from a global location beyond the mapped code section, however. Treating the ROM as a single linear file-to-VMA mapping makes the table bytes look available at a plausible file offset, but that is not enough to prove they are the correct runtime table bytes. I therefore cannot independently validate the callback's state-index-to-handler mapping from the flattened scratch ELF alone.

### Evidence reclassification

- **Retained:** the instructions in the mapped main-code section directly show a state-index dispatch, a call to the generic input-mask predicate with mask `0x201`, a fallback object-flag test, and a state-change helper on the matching paths. The helper itself includes a low-nibble state update to index 5 in one branch. The helper predicate consults gated shared input words.
- **Downgraded pending a correct data/overlay map:** any claim that names a specific state-table entry, ties a manager state index to the Results/standings builder, or uses table bytes read from the linearized out-of-section region as corroboration. Sections AF–AG and related finish-to-Results descriptions above should be read as **conditional hypotheses from the previous trace, not independently verified table resolution** until those tables are located through a validated data/overlay map.
- **Still unproven:** the meaning of input bits `0x001` and `0x200` at the physical-control level; the causal relationship between normal race completion and the first `Fini` transition; the relevant selector and global-guard values at runtime; and a visible Results screen.
- **No implementation consequence:** this correction does not justify changing Boonta's GameCube/Wii code. No retail payload, raw disassembly, local exact offsets or assets are included in this dossier.

### Next bounded validation

1. Establish a trustworthy map for the global tables and any loaded data/overlay segment that contains the state-dispatch records. Do not infer their contents from a single flat ROM-to-VMA mapping.
2. Re-resolve the named state-handler edges only from correctly mapped table bytes or an independent symbol/recomp trace.
3. Update or retract the affected historical hypotheses once that independent mapping is obtained. Until then the safe overall grade is **MAIN-CODE CALL PATH PARTLY VERIFIED / DATA-TABLE DISPATCH UNVALIDATED / FINISH-TO-RESULTS UNPROVEN / RUNTIME UNVERIFIED**.

## AQ. Manager state-table bytes cross-match the ROM, but state 5 is not race-finish proof — static only (2026-10-29)

### Targeted follow-up to Section AP

The manager callback's dispatch table was rechecked independently against the private ROM bytes rather than reading the table from the flattened scratch ELF. The candidate ROM word sequence aligns with the VMA implied by the code's absolute table reference and contains a complete set of seven 32-bit targets. Every target resolves to an instruction boundary within the mapped main-code range or to a state-handler block inside that range. This is a positive table-byte/code-target cross-check for **this specific manager callback**; it does not establish a universal ROM-to-VMA map for all data or overlays.

The mapping audit therefore narrows, but does not remove, Section AP's warning:

- **Resolved for this callback:** the low-nibble state dispatch's candidate target sequence is supported by the raw ROM words and main-code targets. The handlers for the states that call the generic `0x201` input predicate are inside the manager callback's code.
- **Important semantic result:** the matching input-driven paths perform a state transition and related cleanup/timer work. Their presence shows that this manager has an input-gated state progression; it does **not** prove that the input edge denotes “all racers finished” or that this state is the Results screen.
- **Still not resolved:** the separate `Hang` state/selector table and any overlay/global table needed to prove the Results-panel dispatch have not been independently mapped in this pass. Do not use the manager-table confirmation as proof of that different dispatch table.

### Revised evidence grade

The manager's main-code state dispatch and the generic input-mask branch are now **statically cross-checked for this specific table**. The broader end-to-end claim remains **FINISH-TO-RESULTS UNPROVEN / RUNTIME UNVERIFIED**, because the causal meaning of the manager state change and the receiver-side `Hang` table/selector path are not yet shown to converge on a normal post-race Results display.

No emulator, visible race session, watchpoint capture or full static-recomp runtime was performed. The private ROM, exact local offsets, raw disassembly and extracted assets remain uncommitted. No clean-room GameCube/Wii gameplay change follows from this N64-only finding.

## AR. Hang primary-state dispatch verified; normal finish-to-state-5 entry remains open — static only (2026-10-29)

### Correct table and handler now cross-checked

A new pass identified the `Hang` object's own class/update callback, separately from the manager callback examined in Section AQ. Its primary-state updater dispatches through a 19-entry table indexed by the object's primary-state field. The table was cross-matched against the private ROM bytes, and each target resolves to a handler inside the correctly mapped main-code range. This is the relevant `Hang` primary-state table; it is distinct from the separate lifecycle-message sequence table.

The handler selected by primary-state index **5** directly invokes the already identified Results/placement-panel builder. That builder consumes the Results heading and formats ordered participant placement, racer-name and prize-related information. This closes the table-resolution gap for the **consumer side**: there is now a static, same-class route from Hang primary state 5 to the Results UI builder, rather than relying only on the separate manager's dispatch table.

### Crucial causal edge still missing

The `Fini` lifecycle receiver was rechecked in the same pass. In the inspected branch it updates generic lifecycle flags and message-sequence bookkeeping, stores a value in a shared global selector, and invokes a helper with the same object. It does **not** directly write the `Hang` object's primary-state field to 5 in that branch.

That distinction matters: a shared selector value of 5 is not equivalent to proving the object's own primary state became 5. The remaining task is to find the writer or intermediary helper/callback that moves the same `Hang` instance into primary state 5 as a consequence of normal race completion, or to obtain a controlled runtime trace that observes this transition.

### Updated evidence grade

- **Statically supported:** Hang class/update callback → its own primary-state table → state-5 handler → Results/placement-panel builder.
- **Not established:** normal race finish → first `Fini` delivery → same Hang object's primary-state field becomes 5.
- **Runtime still unverified:** no emulator, visible game session, watchpoint trace or full static-recomp execution was run.
- **No platform-parity claim:** the finding is from private N64 analysis and does not prove GameCube/Wii behavior. No ROM bytes, raw disassembly, exact local offsets, extracted assets or N64-derived gameplay implementation were added to Boonta.

### Next bounded trace

Trace all writers of the Hang object's primary-state field and identify whether the message receiver's helper or a later registered callback makes the transition to index 5. Keep the full finish-to-visible-Results path **UNPROVEN / RUNTIME UNVERIFIED** until that causal edge is shown or observed at runtime.

## AS. Fini invokes the same-object primary-state setter on the default selector path — static only (2026-10-30)

### Correction and completion of the Section AR writer check

Section AR correctly noted that the `Fini` receiver contains no literal store to the object's primary-state field. That was incomplete as an account of the receiver's full call path: the receiver delegates the state change to a helper, and the helper was not followed through to its write in that pass.

The new pass follows the arguments and the helper body:

1. The registered `Hang` object record pairs the previously identified primary-state updater with the `Fini`-capable message receiver. The same object pointer is retained in the receiver.
2. In the `Fini` branch, the receiver sets the object's lifecycle flag bit and initializes the requested primary-state value to index **5**.
3. When the object's secondary-sequence selector is the negative sentinel, the selector branch leaves that requested value unchanged and restores the sentinel. It does not replace the requested state with one of the alternate sequence values.
4. If the separate global transition guard is clear, the receiver calls the shared state-transition helper with the **same object pointer** and the requested value loaded from the selector. On this default/sentinel path that value is still **5**.
5. The helper checks the lifecycle flag bit set by the receiver. When the bit is present, it writes the supplied value into that object's primary-state field, preserves the previous primary state for transition bookkeeping, and continues the state-change processing.
6. The registered `Hang` updater dispatches from that same primary-state field. Its independently cross-checked index-5 handler reaches the Results/placement-panel builder described in Section AR.

This resolves the writer/intermediary gap for the **conditional default/sentinel Fini path**. It is not merely a shared token or a coincidentally matching global selector: the receiver passes the object pointer to the state helper, and the helper's guarded write targets the primary-state field on that same object.

### Conditions and remaining limits

The result is conditional, not universal:

- The manager's ordinary all-registered-types broadcast can deliver the finalization token to the `Hang` receiver; the mode-gated bypass and possible abort substitution documented in Section AL remain alternate routes.
- The `Hang` secondary selector must be on the negative-sentinel/default path for the requested target to remain index 5. Valid alternative selector values can choose other states.
- The separate global transition guard must permit the helper call.
- Section AM still applies: the manager's `0x201` test is a generic input-edge predicate. Its bits and remapping gates do not yet identify a dedicated “all racers finished” event or a named physical confirmation control.

### Revised evidence grade

**CONDITIONAL FINALIZATION MESSAGE → SAME HANG INSTANCE PRIMARY STATE 5 → RESULTS/PLACEMENT BUILDER STATICALLY SUPPORTED / ALL-LOCAL-FINISH → FINALIZATION TRIGGER SEMANTICS UNPROVEN / RUNTIME UNVERIFIED.**

The static evidence now connects the ordinary/default lifecycle receiver to the same object's Results state when the selector and guard conditions are met. What remains unproven is whether the generic input-edge gate after the manager's local-player completion aggregate is necessarily satisfied as a consequence of a normal completed race, and whether a real runtime session visibly presents the panel.

No emulator, visible race session, write-watchpoint capture or full static-recomp runtime was performed. No N64-to-GameCube/Wii parity is implied. No ROM bytes, raw disassembly, exact private offsets, extracted resources/assets or N64-derived gameplay implementation were added to Boonta.

### Next bounded trace

Resolve the input-word fields and gates feeding the manager's generic `0x201` press-edge query, then determine whether the resulting event is a post-race confirmation/continuation or another mode-dependent action. Keep the runtime-visible Results check pending until a controlled game/recomp session can observe it. Keep RE-002 parked.

## AT. Controller-poll follow-up does not yet identify the manager's 0x201 event source — static only (2026-10-30)

### What the additional source trace establishes

A bounded follow-up inspected one controller-poll path around the platform controller read API:

- The path invokes the platform controller read routine and then enters a separate application-side update routine.
- That update routine iterates four per-source records and changes their state/timer/threshold fields through helper calls. A later call re-arms the platform controller read operation.
- This establishes a controller-poll → application-side multi-source update path in this part of the main code.

### What it does not establish

The inspected pass did **not** positively map those four records or helper outputs to the shared press-edge words read by the manager's generic `0x201` query in Sections AM–AN. In particular:

- No verified data-flow edge yet connects a raw platform controller packet field, through the four-record updater, to the exact per-source press-edge word consumed by the manager query.
- A separate candidate routine with raw-bit tests also contains coordinate/UI-related work; without a verified cross-reference to the manager's query storage it is not promoted as the input-mask producer.
- The source-word bit mappings and their configuration gates therefore remain unresolved. Do not assign button names (A/B/Start/D-pad or otherwise) to internal bits `0x001` and `0x200`.

### Evidence grade and next step

**PLATFORM CONTROLLER POLL PATH IDENTIFIED / APPLICATION RECORD UPDATER PARTIALLY MAPPED / MANAGER 0x201 SOURCE-WORD DATA FLOW UNPROVEN.**

This is a bounded negative result: the controller path is now a concrete place to continue looking, but it does not yet explain the manager's input-edge condition. The next static step is to identify the exact storage read by the manager query, find every writer to that storage, and follow those writes back to a field in the controller packet or to a clearly identified higher-level event producer. If the required data/overlay mapping or xrefs cannot be validated, retain the unresolved status rather than naming controls from bit positions.

No emulator, controller session, watchpoint capture or full static-recomp runtime was performed. The private ROM, raw disassembly, exact local addresses/offsets, extracted resource bytes and assets remain local. No N64-derived gameplay changes or commercial game data were added to Boonta. Keep RE-002 parked.
