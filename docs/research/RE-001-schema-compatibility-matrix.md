# RE-001 — Compatibility boundary: N64 spline records and Boonta track v1

**Date:** 2026-10-20  
**Status:** research/specification only; no parser or gameplay code added  
**Parent:** [RE-001 route/spline progression dossier](RE-001-route-spline-progress.md)

## Decision

Keep `boonta-track-v1` as the current authored test-track format. **Do not use it as a lossless target for a retail N64 spline record.** It currently stores an ordered point list (`x`, `y`, `z`, `half_width`, `checkpoint`) and a `closed_loop` flag. It has no explicit graph edges, branch history, curve handles, raw-format provenance, or platform-specific record adapter. The N64 records are structurally richer. Local main-code disassembly now directly corroborates the 84-byte runtime node stride, position-vector access, outgoing-edge count/indices, cubic control-vector use, and consumption of the last node fields for lookup. Other field semantics remain unresolved.

A future adapter should have two distinct stages: (1) preserve and validate the raw bytes for a named platform/release record; (2) convert only fields whose semantics have adequate evidence into a normalized route graph. Keep uncertain source words and fields unknown, rather than quietly forcing them into v1 fields.

## Evidence-based mapping matrix

| Candidate source field / behavior | Existing `boonta-track-v1` | Evidence status | Decision for conversion |
|---|---|---|---|
| Position vector | `x`, `y`, `z` | In the local N64 main-code disassembly, `0x8003A4A0` traverses the 84-byte node array and reads floats at `+0x10`, `+0x14`, `+0x18` into a 3D output. This validates runtime use of a vector at byte 16; axis convention and world scale remain unknown. | Candidate position vector is strongly supported. Convert only after coordinate-axis and scale validation; don't assume target GameCube units. |
| Two control vectors at offsets 40 and 52 | No control handles; current runtime samples its own authored point path | Runtime routine `0x8003A5D0` builds a cubic-like 3D sample from per-node vectors at position offset `+0x10` and control-vector offsets `+0x28`, `+0x34` in 84-byte records. The MIT class cites Blender as a reference, so code disassembly is the new independent evidence that these bytes are consumed as curve inputs. Exact basis, axis convention and scale remain to be checked. | Preserve source handles separately from v1 points. A converter may use cubic sampling only after validating the exact curve basis and coordinate transform. |
| Outgoing/incoming point links | Ordered list; implicit next point, single loop flag | In local runtime code at `0x8007F560`, the engine walks nodes with stride `0x54`, reads a halfword at `+0x00` as a loop count, then reads outgoing point indices beginning at `+0x04`. This directly supports the Blender interpretation of outgoing count/indices. The `+0x02` incoming count and four previous-link words at `+0x08..+0x0E` are not yet equivalently traced. | A graph-capable representation is warranted for outgoing edges; keep reverse links / reciprocal semantics unconfirmed until separately traced. Don't flatten alternate outgoing edges into a single implicit successor. |
| Rotation / orientation | None | Blender reads a vector beginning at byte 28; the MIT reader leaves bytes 28–35 uninterpreted and models only a float at byte 36. Their interpretations conflict. | Leave orientation semantics unknown. Do not export these words as Euler angles or up-vector until validated. |
| Progress / branch metadata (bytes 64–83 in Blender's interpretation) | Optional boolean `checkpoint` | Runtime accessor `0x8003A4E8` reads the halfword at `+0x40`; `0x8003A50C` searches nodes by that value, and caller `0x8007FDC0` loops numeric keys and builds a key-to-node/traversal lookup from matching nodes. This gives high confidence that `+0x40` is a route order/progress/group key (not necessarily race-lap progress). Helper `0x8007EE98` divides an input by 10 and scans eight halfwords starting at `+0x42` to resolve node/sub-entry indices and a fractional cursor. The eight words are definitely consumed but their meanings remain unknown. | Preserve `+0x40` separately from `+0x42..+0x50`. A future graph representation may expose a provisional route-order key for the former; keep the eight trailing words opaque until more of the consumer is traced. Do not reduce either to a `checkpoint` boolean. |
| Half-width / road boundaries | `half_width` is an authored metre value clamped by the current demo's road/collision path | No validated road width is identified in the spline point interpretation. Width may be a separate model/collision concern. | Never invent `half_width` from the control points. Derive it only from verified geometry/physics data or mark it unavailable. |
| Closed loop / finish | One `closed_loop` bool; first point is documented as start/finish reference for v1 authored data | The Blender parser can trace some links back to node 0, but full engine semantics and the retail finish line are not independently proven from that parser. | Do not equate every `next` edge to point 0 with a lap event. Confirm lap crossing via code or observed debug behavior. |
| Alternate routes and branch rejoins | Not representable in v1 | Runtime code traverses an outgoing-edge count and indexed targets at each 84-byte node; therefore multi-edge graph structure is consumed by the engine. Candidate value ID 110's branch/join counts remain based on the Blender parser's topology interpretation until all node metadata is reconciled. | A graph-capable representation is required if we want to preserve source topology. Keep branch-selection and merge semantics separate from the existence of outgoing links. |
| Platform/release and provenance | No source platform/release fields in the v1 JSON | Research demonstrates N64 and common/default metadata can use different spline value IDs for the same logical slot. Cross-platform serialized layout parity is unproven. | Require an external provenance record or a future format-versioned asset manifest; never call a PC/default sample “N64” without evidence. |

## What v1 can do safely today

- Continue authoring original, synthetic circuits for the GameCube prototype and testing renderer/input/road collision behavior.
- Validate finite coordinates, minimum segment length, `half_width`, point count and closed/open list shape.
- Export the authored list into the existing static C header used by the test demo.

## What v1 cannot claim today

- Lossless representation of an N64 spline block or preservation of unknown words.
- Representation of multiple outgoing routes, incoming joins, branch-selection history, or route cursor state.
- An evidence-backed mapping from the N64 parser's `progress` words to v1's checkpoint bool.
- Correct native road widths, collision boundaries, spawn/respawn positions, AI routes or finish crossings from the spline points alone.
- Compatibility of N64 course records with the original GameCube/Wii release.

## Evidence gate before writing a converter

1. Confirm value ID 110's identity as Boonta Classic through a second independent clue (e.g. lawful emulator observation of the N64 debug spline-marker toggle on the known course), without relying solely on equal slot and record size.
2. [partly complete] Static N64 call paths now verify the 84-byte stride, position read, outgoing count/target reads, cubic-like control-vector reads and runtime lookups over tail metadata. Still resolve axis/scale, all incoming-link fields and precise progress/section semantics.
3. [partly complete] Compare the raw record and field offsets with the Blender parser, the MIT serialization model and the newly identified N64 consumers. Keep the MIT model's dependency on Blender explicit; no independent confirmation should be claimed where the class comments cite that parser.
4. Find the separate source of physical road width/collision or record that this field remains unknown; do not infer it from a route line.
5. Build a local-only decoder/fixture from the lawful ROM. Use synthetic test cases with no retail positions or handles in Git: invalid indices, branch split/rejoin, closed loop, reverse traversal and progress/finish crossing.
6. Only once these fields have evidence, decide whether to add a new graph format version or a separate `route_graph` asset type. Preserve v1 unchanged as the small authored-track harness.

## Source pins

- [Boonta track v1 schema and limitations](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/tools/track_format/README.md)
- [MIT spline point record model](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentData.cs)
- [MIT segment header model](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/SplineBlock/SplineSegmentHeader.cs)
- [GPL Blender spline parser](https://github.com/louriccia/blender-swe1r/blob/b0d4019addb97d51523019ca1233411fae0508d6/splineblock.py)
- [N64/default spline block metadata](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Block.csv)

## Safety / licensing boundary

This document describes format fields, metadata and research steps only. No ROM bytes, extracted coordinates, handles, geometry, copyrighted asset data or third-party implementation code is included. Third-party parsers are read-only research references; license review is required before any future code reuse.

## Runtime consumer scope caveat

The direct call sites currently tied to `func_80080BEC` are inside the generic N64 object-update/render loop at `func_80054048`; the caller passes a pointer obtained from a containing object at offset `+0x84`, and the spline-marker cheat flag gates another renderer helper in this same loop. This supports active runtime consumption of spline/cursor data, but **does not yet prove that this particular call path tracks the player's race progress or AI lap state**. Before attributing these cursor fields to player standings, identify a caller or data link from the racer/AI update path. Route graph, geometric spline evaluation, generic object-animation cursors and race-lap progression must remain separate concepts until their relationship is demonstrated.