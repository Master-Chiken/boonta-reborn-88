# RE-001 — Compatibility boundary: N64 spline records and Boonta track v1

**Date:** 2026-10-20  
**Status:** research/specification only; no parser or gameplay code added  
**Parent:** [RE-001 route/spline progression dossier](RE-001-route-spline-progress.md)

## Decision

Keep `boonta-track-v1` as the current authored test-track format. **Do not use it as a lossless target for a retail N64 spline record.** It currently stores an ordered point list (`x`, `y`, `z`, `half_width`, `checkpoint`) and a `closed_loop` flag. It has no explicit graph edges, branch history, curve handles, raw-format provenance, or platform-specific record adapter. The N64 records appear structurally richer, and the semantic interpretation of their link/progress words is not yet cross-validated between public readers.

A future adapter should have two distinct stages: (1) preserve and validate the raw bytes for a named platform/release record; (2) convert only fields whose semantics have adequate evidence into a normalized route graph. Keep uncertain source words and fields unknown, rather than quietly forcing them into v1 fields.

## Evidence-based mapping matrix

| Candidate source field / behavior | Existing `boonta-track-v1` | Evidence status | Decision for conversion |
|---|---|---|---|
| Position vector | `x`, `y`, `z` | The MIT record model and Blender parser both read a 3-float vector at byte 16, but the MIT class cites Blender as a reference; this is not independent reverse-engineering corroboration. Axis convention and scale for the game build still need confirmation. | Potentially map after a local coordinate-system and unit check; do not assume the target GameCube units from PC tooling. |
| Two control vectors at offsets 40 and 52 | No control handles; current runtime samples its own authored point path | Offsets are present in both the MIT record model and the Blender parser. Blender uses them as Bezier handles; the MIT reader calls them control points. | Retain as raw/control vectors. Implement a Bezier interpretation only after runtime or stronger source evidence validates it. |
| Outgoing/incoming point links | Ordered list; implicit next point, single loop flag | Blender interprets the first 8 halfwords as link counts/indices. MIT labels the same raw words mostly unknown and names a single `PreviousNodeId` at offset 8. | Do not encode this as confirmed topology yet. Preserve the halfwords and validate them against a N64 code path or marker observation first. |
| Rotation / orientation | None | Blender reads a vector beginning at byte 28; the MIT reader leaves bytes 28–35 uninterpreted and models only a float at byte 36. Their interpretations conflict. | Leave orientation semantics unknown. Do not export these words as Euler angles or up-vector until validated. |
| Progress / branch metadata (bytes 64–83 in Blender's interpretation) | Optional boolean `checkpoint` | Blender names these shorts `progress`, `unk_set[]`, `unk`; MIT sees `Unk_40` followed by a separate segment header. No independent semantic mapping has been established. | Do not map progress bands or unknown words to checkpoint flags. Preserve raw bytes/words only in private audit tooling. |
| Half-width / road boundaries | `half_width` is an authored metre value clamped by the current demo's road/collision path | No validated road width is identified in the spline point interpretation. Width may be a separate model/collision concern. | Never invent `half_width` from the control points. Derive it only from verified geometry/physics data or mark it unavailable. |
| Closed loop / finish | One `closed_loop` bool; first point is documented as start/finish reference for v1 authored data | The Blender parser can trace some links back to node 0, but full engine semantics and the retail finish line are not independently proven from that parser. | Do not equate every `next` edge to point 0 with a lap event. Confirm lap crossing via code or observed debug behavior. |
| Alternate routes and branch rejoins | Not representable in v1 | Blender's interpreted graph shows branches/joins on candidate value ID 110; MIT's field names do not independently confirm those link arrays. | Requires a graph-capable representation if confirmed. Avoid flattening branches into one point list because that is lossy. |
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
2. Trace the N64 code which loads and reads a spline record. Verify at least the link-count/index fields, position/vector scale and curve-control usage against actual code references.
3. Compare the raw record layout against the N64 reader and the Blender parser explicitly; document every disagreement rather than selecting whichever interpretation makes a plausible curve.
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