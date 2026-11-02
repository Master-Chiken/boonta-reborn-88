# Neutral route graph format v1

This folder defines an original, platform-neutral logical route graph for clean-room authoring and host tests. It is **not** a parser for the commercial game and it is not a binary layout proposal for GameCube, Wii, N64 or Dreamcast.

## Files and commands

- schema.json — JSON Schema Draft 2020-12 structural contract.
- validate_route_graph.py — standard-library semantic validator, cubic curve evaluator, sampled-length helper, normalized progress allocator and host cursor with branch history.
- fixtures/ — small synthetic graphs only.

Run the validator on the open Bezier example with:

    python3 tools/route_graph_format/validate_route_graph.py tools/route_graph_format/fixtures/open-bezier.json

Run the synthetic host suite with:

    python3 -m unittest discover -s tests -p 'test_route_graph_format.py' -v

The existing boonta-track-v1 parser, exporter, source fixture, generated header and runtime are untouched. The new module has no runtime/renderer dependency and is not wired into the GameCube/Wii executable.

## Contract

A document identifies boonta-route-graph-v1, schema version 1, a source platform/release/revision, the project axis convention (x lateral, y up, z forward; metres), nodes and directed edges.

Nodes contain stable IDs, positions and optional up hints. Directed topology is carried only by edge from/to references; incoming/outgoing adjacency is derived and validated rather than duplicated in two places.

Edges carry one curve:

- cubic_bezier: control1 and control2 are **absolute world-space positions**, not offsets. Endpoint positions come from the from and to nodes.
- uniform_cubic_bspline: exactly four control-node IDs. The edge topology runs from the second control node to the third; the outer two supply the four-node curve window.

Each edge carries an explicit normalized progress interval. At a split all outgoing edges share a start value; at a rejoin all incoming edges share an end value. Interior nodes must be progress-continuous. An open route starts at 0 and terminates at 1. A closed route returns to the start node at 1 and begins there at 0.

surface_binding is an optional sequence of (t, surface_id) samples from t=0 to t=1. It deliberately contains no road width, mesh data or collision dimensions. Those belong to separate surface/geometry assets. metadata is an opaque extension object; the validator does not assign semantics to it.

## Evidence and deliberate limits

The PC source pinned to [SW_RACER_RE commit a9863edd4caaa573f89ff634fa7d1cd6d41738ab](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab) directly shows:
- Bezier evaluation using node A position, A handle2, B handle1, B position;
- a four-node uniform cubic B-spline window;
- directed next/previous links and a cursor branch selector/history;
- progress spans consumed as base + t * span.

This neutral schema expresses those logical responsibilities without copying the PC record layout. The Ghidra Steam-PC cross-check is pinned separately at [d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef). PC evidence does not prove console parity; no GameCube/Wii route sample has been identified.

The B-spline evaluator uses the standard uniform cubic basis. Optional up hints are linearly blended between the edge's topology endpoints and orthogonalized against the tangent; this is an explicit clean-room policy, **not a claim to reproduce the PC rotation interpolation**. Degenerate tangents fail safely.

The sampled progress allocator apportions a caller-supplied normalized interval in proportion to already-sampled physical edge lengths. It mirrors the documented progress-mapping responsibility but is not a reverse-engineered importer. The caller remains responsible for sampling each curve at a known density.

The host cursor records the actual chosen edge path. Reverse movement walks that stored history, so a rejoin does not guess which incoming branch was used. Forward movement replays history unless an explicit new branch choice replaces the future path. The cursor is a testable logical component only; it is not connected to gameplay runtime, projection/rebinding, collision, lap events, or GX.

## Validation boundary

The validator checks missing/duplicate IDs, malformed links, reachability, open/closed endpoint rules, progress continuity across branches/rejoins, curve parameters, finite values and sorted surface bindings. It does not decode source binaries, infer track width, or import proprietary coordinates. The fixtures are synthetic and carry source.platform = synthetic.

This is a **schema/host-fixture milestone**, not proof that a complete original Racer course or race is playable.
