# Neutral route graph format v1

This folder defines an original, platform-neutral logical route graph for clean-room authoring and host tests. It is **not** a parser for the commercial game and it is not a binary layout proposal for GameCube, Wii, N64 or Dreamcast.

## Files and commands

- schema.json — JSON Schema Draft 2020-12 structural contract.
- validate_route_graph.py — standard-library semantic validator, cubic curve evaluator, per-edge and whole-graph sampled-length helpers, normalized progress allocator and host cursor with branch history.
- export_closed_loop_track.py — explicit offline bake from a simple closed route graph into the existing track-v1 format.
- fixtures/ — small synthetic graphs only.

Run the validator on the open Bezier example with:

    python3 tools/route_graph_format/validate_route_graph.py tools/route_graph_format/fixtures/open-bezier.json

Run the synthetic host suite with:

    python3 -m unittest discover -s tests -p 'test_route_graph_format.py' -v

The existing boonta-track-v1 parser, exporter, source fixture and generated header remain backward-compatible as a compatibility and regression path. The first native curve-runtime representation is generated separately from the route graph; see **Native GameCube/Wii runtime curve evaluation** below.

## Contract

A document identifies boonta-route-graph-v1, schema version 1, a source platform/release/revision, the project axis convention (x lateral, y up, z forward; metres), nodes and directed edges.

Nodes contain stable IDs, positions and optional up hints. Directed topology is carried only by edge from/to references; incoming/outgoing adjacency is derived and validated rather than duplicated in two places.

Edges carry one curve:

- cubic_bezier: control1 and control2 are **absolute world-space positions**, not offsets. Endpoint positions come from the from and to nodes.
- uniform_cubic_bspline: exactly four control-node IDs for the evaluation window. The edge's directed from/to topology links are stored independently; the schema does not infer a fixed control-window index for those links. The B-spline's evaluated positions at t=0 and t=1 must meet the edge's topology endpoint positions, so neighboring route edges cannot jump in world space.

Each edge carries an explicit normalized progress interval. At a split all outgoing edges share a start value; at a rejoin all incoming edges share an end value. Interior nodes must be progress-continuous. An open route starts at 0 and terminates at 1. A closed route returns to the start node at 1 and begins there at 0.

surface_binding is an optional sequence of (t, surface_id) samples from t=0 to t=1. It deliberately contains no road width, mesh data or collision dimensions. Those belong to separate surface/geometry assets. metadata is an opaque extension object; the validator does not assign semantics to it.

## Offline bridge into the current GameCube/Wii track pipeline

The first runtime bridge is deliberately narrow: it accepts a **single unbranched closed loop** (one incoming and one outgoing edge per route node), samples its cubic Bezier or uniform cubic B-spline edges, and writes a normal `boonta-track-v1` JSON track. The existing `tools/track_format/export_track_header.py` then generates the C header consumed by the native demo.

Example using only the synthetic closed-loop fixture:

    python3 tools/route_graph_format/export_closed_loop_track.py \
        tools/route_graph_format/fixtures/closed-loop.json \
        /tmp/route-track.json --half-width 3.6 --samples-per-edge 24
    python3 tools/track_format/validate_track.py /tmp/route-track.json
    python3 tools/track_format/export_track_header.py \
        /tmp/route-track.json /tmp/generated_route_track.h --symbol "route graph demo"

For an experimental equal-distance bake, add `--sampling-mode arc_length`. The default `parameter` mode preserves the earlier byte-for-byte export behavior.

Geometry stays separate from topology. `--half-width` is required; an edge with `surface_binding` additionally needs a JSON object mapping every referenced surface ID to an explicit half-width, supplied with `--surface-widths widths.json`. Missing mappings and widths outside track-v1's 0.5–100 metre range are errors, not guessed defaults.

Each edge contributes a fixed number of samples; the shared endpoint is emitted once by the next edge. The first point alone is marked as the current track-v1 start/finish checkpoint. The current runtime still counts laps by closed-loop distance and does not consume intermediate checkpoint gates.

The default `--sampling-mode parameter` uses equally spaced curve parameters and preserves existing output. The optional `--sampling-mode arc_length` builds a bounded lookup (128–8192 intervals per edge) and numerically inverts sampled 3D distance to place the same number of samples more evenly along that edge. Surface bindings are still evaluated at the resulting curve parameter `t`. This is an approximation, not analytic arc-length inversion; it is a host-side bake option, not a runtime change. Compare both outputs and run visible-Dolphin acceptance before replacing the current checked-in oval header.

**Not yet exported:** open routes and branching/rejoining graphs. These remain valid in route-graph-v1 and are rejected by this first bake path; selecting a branch and flattening it requires an explicit route choice, not an arbitrary edge ordering. This is a deterministic offline conversion, not a runtime graph loader, a live branch selector, or proof of GameCube/Wii source-format parity. The baked samples are then interpolated by the existing track-v1 Catmull-Rom runtime, so sampling density affects the approximation.

## Current runtime oval source

The native prototype's active test oval has now been converted into the canonical clean-room source at `gamecube-demo/data/original-test-oval-route-graph.json`, with explicit width classes in `gamecube-demo/data/original-test-oval-surface-widths.json`. The eight edge curves are cubic Bezier segments formed by converting the previous Catmull-Rom test points to their mathematically equivalent Bezier handles. Progress intervals are proportional to sampled 3D edge lengths.

The checked-in `gamecube-demo/source/generated_track.h` is deterministically baked from this route graph using 16 samples per edge, then exported through the existing track-v1 header generator. Host test `test_runtime_oval_route_graph_is_the_canonical_header_source` checks this entire conversion against the committed C header. The 8-node source is deliberately the same original prototype oval; no commercial course coordinates or retail assets are involved.

This moves the **current simple loop's authoring source** to route-graph-v1. The native runtime evaluates generated cubic Bezier curves through a shared, host-tested C sampler and advances a topology cursor alongside race distance. The cursor and edge-local sampler are connected for the current oval; live branch-choice input is not yet connected. The legacy track-v1 header remains checked for deterministic compatibility and as a geometric comparison baseline.

## Evidence and deliberate limits

The PC source pinned to [SW_RACER_RE commit a9863edd4caaa573f89ff634fa7d1cd6d41738ab](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab) directly shows:
- Bezier evaluation using node A position, A handle2, B handle1, B position;
- a four-node uniform cubic B-spline window;
- directed next/previous links and a cursor branch selector/history;
- progress spans consumed as base + t * span.

This neutral schema expresses those logical responsibilities without copying the PC record layout. The Ghidra Steam-PC cross-check is pinned separately at [d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef). PC evidence does not prove console parity; no GameCube/Wii route sample has been identified.

The PC cursor uses the fourth lookahead node for a B-spline forward-link decision and shifts the full four-node window at a boundary. The logical schema therefore keeps directed edge topology separate from the four-point curve window instead of assuming a universal middle-pair mapping. The evaluator uses the standard uniform cubic basis. Optional up hints are linearly blended between the edge's topology endpoints and orthogonalized against the tangent; this is an explicit clean-room policy, **not a claim to reproduce the PC rotation interpolation**. Degenerate tangents fail safely.

The sampled progress allocator apportions a caller-supplied normalized interval in proportion to already-sampled physical edge lengths. Use `sample_route_edge_lengths()` to bake all graph edges at one chosen sample density with one validation/index pass, then select the edge lengths for each branch path and feed them to `allocate_progress_spans()`. The per-edge `sample_edge_length()` helper remains available for focused queries. This mirrors the documented progress-mapping responsibility but is not a reverse-engineered importer.

The host cursor records the actual chosen edge path. Reverse movement walks that stored history, so a rejoin does not guess which incoming branch was used. Forward movement replays history unless an explicit new branch choice replaces the future path. Its `move(delta_parameter)` argument remains a local normalized-parameter step, not metres. A separate `move_distance(delta_distance)` now advances through per-edge 3D arc-length lookup tables, built lazily only for edges actually visited and cached at a configurable sample density (128 intervals by default). It converts distance to local `t`, crosses edges with explicit branch choices, reverses through the recorded path, and can replace a previously cached future branch after backing up before a split. Tests also verify a Bezier whose parameter speed is strongly non-uniform. Its result includes `distance_on_edge` and `edge_length`; normalized `progress` still follows the graph-authored progress interval interpolated by local `t`, not a separately inferred distance coordinate. Both APIs are host-testable and neither is connected to gameplay runtime, projection/rebinding, collision, lap events, or GX.

Example distance-driven host use (using the route fixture names):

```python
from validate_route_graph import RouteCursor

cursor = RouteCursor(graph, distance_samples=128)
state = cursor.move_distance(18.0, {"split": "right-1"})
print(state["edge_id"], state["distance_on_edge"], state["progress"])
cursor.move_distance(-2.5)  # reverse follows the recorded right-branch history
```

The distance lookup uses sampled 3D chord lengths and linear inversion, so `t` is approximate at the selected lookup density. The graph-authored normalized progress remains `progress.start + t * (progress.end - progress.start)`; it is deliberately not silently replaced by a new distance-progress interpretation.




### Measured bake comparison on the existing clean-room oval (2026-11-03)

The two sample distributions were compared on the eight-edge, 128-point oval (16 samples per edge). The reference was each authored Bezier edge evaluated at 4096 parameter intervals; the runtime side reproduced the current `track_sample_at` behavior: chord-length segment selection followed by uniform Catmull-Rom interpolation. At nine positions per runtime segment, the reconstructed position was compared with the authored route at the same accumulated travelled distance.

| Bake mode | Chord-spacing CV | Maximum route deviation | RMS route deviation |
|---|---:|---:|---:|
| Legacy parameter (16/edge) | 20.67% | 0.0368 m | 0.0170 m |
| Experimental arc length (16/edge) | 15.67% | 0.0610 m | 0.0318 m |

Arc-length mode makes adjacent point spacing more uniform (about 24% lower coefficient of variation), but it increases the current Catmull-Rom runtime's maximum route deviation by about 66% and RMS deviation by about 86% at this density. The likely reason is that the current runtime interpolates each sample interval in uniform local parameter space; resampling the source curve at nonuniform Bezier parameters changes the assumptions of that interpolator.

A density sweep points in the same direction: at 32 samples per edge the parameter bake measured 0.00969 m max / 0.00428 m RMS deviation, versus 0.02061 m / 0.00815 m for arc length; at 64 per edge the respective maxima were 0.00390 m and 0.01017 m. These are deterministic host-side calculations, not emulator captures or visual/console acceptance.

**Decision:** retain `parameter` as the default and keep the checked-in 16-sample oval unchanged. Do not select the experimental arc-length bake for the current Catmull-Rom runtime. A 32-sample parameter-space bake is a candidate for a separately validated visual/build comparison, not an automatic upgrade. Arc-length mode remains available for future runtime/interpolation designs that consume true distance parameterization.


### Runtime lap-distance versus smoothed-curve length (2026-11-03)

The legacy eight-control-point oval in an earlier development snapshot had a straight-chord lap distance of 181.232191 m, while its Catmull–Rom reconstruction measured about 184.563 m (roughly 1.84% longer). The RE-001 route-graph bridge now bakes the same clean-room oval to 128 points (16 per Bezier edge), reducing the mismatch substantially:

- Generated header / polyline lap distance: **184.532595 m**.
- Reconstructed 128-segment Catmull–Rom length: **184.563791 m** (converged using up to 1024 subdivisions per runtime segment).
- Difference: **0.031196 m per lap**, or **0.01691%**.

This is the actual relationship in the 128-point branch build: the lap counter uses the generated polyline length while `track_sample_at` draws Catmull–Rom between those points. The residual is small, but not mathematically zero. A host regression now requires the reconstructed Catmull–Rom length to remain within 0.02% of the polyline length when regenerating the canonical oval. This guards the current distance/render alignment without changing speed, lap timing, or the runtime interpolation algorithm.

This is host-side geometric validation, not proof of visible race behavior or retail GameCube/Wii course parity. The code-bearing change remains in PR #274; `dev` is not updated until that PR is reviewed and merged.

### Production C sampler regression (2026-11-03)

The runtime implementation was extracted without changing its interpolation or distance-selection rules into `gamecube-demo/source/track_sampling.h`. Both `main.c` and `gamecube-demo/tests/test_track_sampling.c` now call that same C function. The host test covers all 128 generated chord boundaries, positive/negative and multi-lap wrapping, the seam tangent, and alignment between the compiled lap counter and sampler at all three race boundaries. It uses `BOONTA_TRACK_LENGTH`, the same compiled length used by the runtime's `RACE_LAP_DISTANCE`.

The test also samples the actual C Catmull-Rom output at 128 subdivisions per each of the 128 generated chord segments (16,384 substeps) and measures **184.563812 m** against the compiled **184.532593 m** lap distance. The measured difference is **0.01692%**, under the 0.02% regression threshold. This discrete C measurement is slightly below the earlier high-subdivision host reconstruction (184.563791 m); both independently show a mismatch well below 0.02%. The new test reports the measured C value in the CI log and guards the threshold. During sampler initialization, the 128 chord intervals are multiplied by one common scale factor so their wrap period is exactly `BOONTA_TRACK_LENGTH`, the same constant used by the lap counter. This preserves relative interval proportions while preventing float-summation drift from creating a slightly different lap wrap coordinate.

This closes a source-level testing gap: the geometric regression now exercises the production C sampler rather than only a Python reimplementation. It does not connect the route-graph cursor to vehicle movement, prove exact mathematical arc length, or replace visible Dolphin/hardware acceptance.

## External reverse-engineering tool references (2026-11-03)

Two public projects provide useful workflow patterns, but neither is a drop-in GameCube/Wii implementation:

- [sp00nznet/racer](https://github.com/sp00nznet/racer/tree/694c5663b3a7c30e2862fc240344f34683f99a9c) is an **N64 MIPS static recompilation** using N64Recomp. Its ROM analyzer, symbol inventory, function differ, string dumper and progress report demonstrate a repeatable pipeline: identify the exact local binary, inventory functions, retain address/symbol mappings, compare one function at a time, and track unknowns explicitly. These tools target that N64 ROM/MIPS project; they are not a GameCube/Wii DOL/ELF PowerPC decoder and no code or ROM data is imported here.

- [giveen/decomp.anything](https://github.com/giveen/decomp.anything/tree/b410ac528ded6fa9adb7fad4f000cebbf5f341e6) describes itself as a decomp.wtf fork with Windows PE matching and optional REA analysis. Its [objdiff guide](https://github.com/giveen/decomp.anything/blob/b410ac528ded6fa9adb7fad4f000cebbf5f341e6/src/decompnet/app/guide/objdiff.md) gives a transferable comparison order: match control flow/instruction count first, then operands and relocations, and leave register allocation/scheduling until last. Its x86/PE matching backend is not evidence of PowerPC support; use that order as a review method only unless a PowerPC-capable matcher is separately verified.

For any future console-binary research, keep the owner's lawful local dump and derived disassembly local, record the exact binary hash, platform/region/revision, address range and tool version, and distinguish a named match from a hypothesis. A public N64 symbol or a PC-only route observation must never be promoted to GameCube/Wii fact without target-specific evidence.

## Validation boundary

The validator checks missing/duplicate IDs, malformed links, reachability, open/closed endpoint rules, progress continuity across branches/rejoins, curve parameters, finite values and sorted surface bindings. It does not decode source binaries, infer track width, or import proprietary coordinates. The fixtures are synthetic and carry source.platform = synthetic.

This is a **schema/host-fixture milestone**, not proof that a complete original Racer course or race is playable.


## Native GameCube/Wii runtime curve evaluation (2026-11-03)

The clean-room oval now has a second generated C representation at
`gamecube-demo/source/generated_route_graph.h`. Regenerate it with:

```sh
python3 tools/route_graph_format/export_runtime_route_header.py \
  gamecube-demo/data/original-test-oval-route-graph.json \
  gamecube-demo/data/original-test-oval-surface-widths.json \
  gamecube-demo/source/generated_route_graph.h \
  --default-half-width 3.6 --distance-subdivisions 128
```

The generator accepts validated open or closed route graphs made of cubic
Bezier edges. A single unbranched loop keeps its historical traversal ordering;
branched/rejoining and open graphs preserve the authored edge order and emit
node/edge indices, progress spans, start-node, closed-loop and branch flags for
the topology cursor. It rejects unsupported curve types such as uniform cubic
B-splines rather than approximating them. Widths remain a separate per-edge
surface sample array, not part of route topology. For branched graphs the native
sampler's global wrapping API is disabled; callers must sample through a cursor
and the selected edge's local arc-distance lookup.

`gamecube-demo/source/route_graph_sampling.h` is now the production C sampler
used by `main.c`. It builds a 128-interval-per-edge 3D distance lookup and caches
the result for subsequent GX scene sampling. The cursor follows the same
physical distance delta as race state, and the renderer samples look-ahead and
look-behind positions from a copy of that cursor. The current eight-edge demo
oval still uses its generated single-loop lap coordinate for lap counting and
the finish stripe; the cursor path history is host-tested through three laps and
reset.

The shared C implementation is compiled both into the GameCube DOL and into
`gamecube-demo/tests/test_route_graph_sampling.c`. The host regression checks
all eight edge endpoints, closed-loop positive/negative wrapping, seam tangent
continuity, route length against the previous track-v1 lap coordinate, and a
16,384-step measurement of the actual C Bezier sampler. A Python regression
regenerates the header and compares it byte-for-byte with the checked-in file.

The C cursor is now a general topology component with bounded branch history,
explicit outgoing-edge choices, reverse/forward replay and open-route finish
behavior. Host tests exercise a synthetic three-decision graph; another test
generates a temporary branched native header, compiles it as strict C99, and
traverses one branch with the C cursor.

The optional
`boonta_route_graph_choose_outgoing_edge()` helper compares normalized
horizontal endpoint tangents and chooses the most left-turning, right-turning,
or straightest outgoing edge. Endpoint tangent extraction falls back from the
first derivative to the next useful derivative and then to the endpoint chord.
This is defensive handling for malformed or legacy generated C geometry: the
route-graph validator continues to reject degenerate authoring tangents. Strict
C99 host tests cover all fallback levels and left/right/neutral branch choice.
The helper is not yet connected to live controller input.

The live demo runtime remains on the existing unbranched oval: no
branch-choice control or split/rejoin route is yet connected to player input,
collision, lap progression or GX rendering. Native B-spline evaluation and
checkpoint progression inside alternate branches also remain unimplemented.
The previous track-v1 sampler remains available for regression comparison;
the live game uses the new Bezier route sampler and synchronized cursor on the
current oval.
