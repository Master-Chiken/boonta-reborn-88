# Neutral track spline format (v1)

This folder defines an **original, engine-neutral** format for tracks authored from scratch. It is not a parser for commercial game files and does not require any game dump, ROM, extracted level, or proprietary asset.

## Coordinate convention

- `x`: lateral position in metres (left/right).
- `y`: height in metres.
- `z`: forward position in metres.
- `half_width`: authored half-width in metres. In the current GameCube demo, the effective rendered and collidable half-width is bounded to 2.2–4.8 metres so scenery, road edges and rail recovery stay aligned. Values outside that runtime range remain valid in the engine-neutral format but are clamped by this demo.
- `checkpoint`: optional boolean marker used by the runtime to place a lap/progress gate.

The first point is the start/finish reference. For a closed circuit, the final point connects back to the first point; **do not duplicate the first point at the end**. For a point-to-point course, set `closed_loop` to false.

## Example

See `example_track.json`. It is a tiny, entirely original oval-ish test circuit and is only test data.

## Validation

Run:

```sh
python3 tools/track_format/validate_track.py tools/track_format/example_track.json
python3 -m unittest discover -s tests -p 'test_track_format.py'
```

The validator rejects non-finite coordinates, out-of-range values, malformed checkpoints, too few points, zero-length neighbouring segments, and excessive point counts. The exporter is wired into the GameCube prototype by the stacked runtime follow-up (PR #157): generated C data includes the closed-loop polyline length, and the current scrolling GX road samples authored lateral position, half-width, and elevation. Run `python3 tools/track_format/export_track_header.py tools/track_format/example_track.json gamecube-demo/source/generated_track.h --symbol "original test oval"` to regenerate the checked-in header. The renderer is **still not a complete world-space 3D circuit**: a tangent-based camera, world-space racer/scenery placement, and an inspected Dolphin frame remain acceptance gates.
