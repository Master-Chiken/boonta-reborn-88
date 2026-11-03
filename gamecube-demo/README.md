# GameCube first-render / driving-input prototype

This directory is a **clean-room, original technical slice** for Boonta Reborn 88. It is separate from the unreviewed Step 102 source bundle and contains no extracted game code, commercial assets, models, textures, music, voices, ROMs, or disc images.

## Current scope

- Native GameCube GX initialization and 3D colored-vertex rendering.
- A genuinely scrolling procedural desert course:  curved asphalt segments, lane markers, and faceted canyon walls advance continuously with race distance; the start/finish stripe approaches once per lap instead of receding. The environment uses a warm desert floor, daylight sky, and original low-poly canyon geometry.
- A spline-aligned desert canyon with a deterministic staggered rock-ridge silhouette and faceted outcrops, avoiding uniform wall tops.
- An original low-poly twin-engine racer authored in `boonta-mesh-v1` JSON, exported to a validated C mesh and textured through the native GX RGB565 path; its exhaust plumes still lengthen with speed and boost.
- GameCube controller steering with lateral inertia, off-road speed loss, and rail-edge recovery, plus throttle, brake, pitch, and slide. Pitching nose-down increases forward progress at the cost of steering authority; pitching nose-up slows progress but improves steering. Holding L initiates a low-grip slide: it increases turn impulse while retaining sideways drift, so releasing it early is part of cornering. Pitch/slide state is exposed in the HUD and covered by deterministic host tests.
- Three clean-room procedural rival craft approach at staggered intervals, change lanes with independent phases, can collide with the player, and can be overtaken; up to eight overtake markers are shown in the HUD.
- A basic speed bar, steering-position tick, rechargeable boost-energy meter, overheat/cooldown bar, race clock, current-lap timer and best-lap display, lap-progress bar, repeating start/finish stripe, and three completed-lap indicators (the prototype's configured race limit).
- A Start-button pause toggle with a visible pause icon; gameplay simulation freezes while paused.
- A reproducible CI build that uploads the resulting DOL and ELF if compilation succeeds.

This is a gameplay prototype, not the completed racer and not a port of the commercial game. Rival behavior is deliberately simple and scripted; collision response and overtake counting are prototypes, not a full physics or race-position system. Audio, saves, a title menu, and a full physics model are not implemented.

## Original player mesh and texture

The player's hull is an original source-authored indexed mesh. The project validates its positions, UVs and indices on the host, exports a deterministic C header, and checks that the generated header matches the source. The matching 16×16 RGB8 texture source is validated and quantized to GX-tiled RGB565 by a small host-side exporter; aligned texels are copied and cache-flushed before GX upload. This is an owned test asset, not extracted game content. Runtime filesystem loading and proprietary model/texture parsing are not implemented.

The procedural course, rival craft, controls, dynamic exhaust and HUD remain separate from this asset. Successful rendering in Dolphin is evidence for this one original mesh/texture path, not proof of full game-asset compatibility or manual-controller acceptance.

## Runtime track source

The current demo oval is now authored as the clean-room `boonta-route-graph-v1` source in `gamecube-demo/data/original-test-oval-route-graph.json`. Its separate `original-test-oval-surface-widths.json` map supplies the road-width classes referenced by the graph's surface bindings.

The graph contains eight topology nodes and eight cubic Bezier edges. Each Bezier edge is the exact Catmull-Rom-to-Bezier conversion of the prior eight-point test oval, and the graph's progress spans are proportional to sampled physical edge lengths. The offline bake samples each edge 16 times, writes `boonta-track-v1`, and the existing track exporter produces `source/generated_track.h`. The native renderer still consumes this compiled C header; it does **not** parse route-graph JSON at runtime. The denser baked points approximate the authored Bezier path through the existing Catmull-Rom track sampler.

The production sampler is shared in `source/track_sampling.h`; the native renderer and `tests/test_track_sampling.c` call the same C implementation. The host regression checks every generated-point boundary, negative camera look-behind and multi-lap wrap, seam position/tangent continuity, and the three-lap finish counter using the compiled `BOONTA_TRACK_LENGTH`. It also measures the actual C sampler over 16,384 substeps: **184.563812 m** of Catmull-Rom path versus **184.532593 m** of compiled lap distance (**0.01692%** difference, below the 0.02% guard). This is a numerical/runtime-code regression, not a human-driven race acceptance result. The sampler now scales all chord intervals by one common factor so its modulo period is exactly the same `BOONTA_TRACK_LENGTH` constant used by the lap counter; relative segment proportions and course geometry are preserved.

Regenerate the committed header from the route source with:

```sh
python3 tools/route_graph_format/export_closed_loop_track.py \
  gamecube-demo/data/original-test-oval-route-graph.json \
  /tmp/original-test-oval-track.json \
  --half-width 3.5 --samples-per-edge 16 \
  --surface-widths gamecube-demo/data/original-test-oval-surface-widths.json

python3 tools/track_format/validate_track.py /tmp/original-test-oval-track.json
python3 tools/track_format/export_track_header.py \
  /tmp/original-test-oval-track.json \
  gamecube-demo/source/generated_track.h --symbol "original test oval"
```

Branched graphs remain preserved in route-graph format; they are not yet executable by this single-loop runtime.

## Controls

- Control Stick left/right (or D-pad): steer.
- Control Stick up/forward: pitch down for more forward progress but weaker steering; down/back: pitch up for slower progress and tighter control.
- L trigger: slide/drift through corners; turn response grows while sideways drift lasts longer.
- A: accelerate.
- B: brake.
- Hold X + A: engage boost while accelerating; energy drains and recharges on release. Heat rises during boost; at 98% heat, boost locks out until the engine cools to 60% or below.
- Start: toggle pause/resume; the pause icon appears in the center of the HUD.
- Y: reset the run, lap counter, rival, overtake indicators, and pause state.

## Build

Use the official devkitPro GameCube/Wii environment (devkitPPC + libogc). In a configured shell, run:

```sh
make clean
make
```

The expected files are `boonta_gc_demo.dol` and `boonta_gc_demo.elf`. GitHub Actions runs the same build in the `devkitpro/devkitppc` container and keeps successful outputs as a short-retention artifact.

## Latest CI build and visible-render evidence

The latest recorded clean-room prototype validation is [GameCube first-render run #69](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727969531). The host gameplay/pause tests, native devkitPPC/libogc build, DOL/ELF structure checks, and bounded headless Dolphin process smoke passed. The optional [Software Renderer capture and logs](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727969531/artifacts/11970040471) show the procedural road, colored rails, center markers, player pod, and rival pod.

This proves that a visible prototype scene renders in the CI Dolphin Software Renderer environment. It does **not** prove a complete playable racer. See the [build status report](../docs/GAMECUBE_FIRST_RENDER_STATUS.md) for evidence and limitations.

## Runtime validation still required

The remaining acceptance checks are interactive steering, acceleration/braking, boost and overheat cooldown, pause/resume (the clocks should freeze), reset (all clocks should return to zero), completion of a three-lap run with current/best lap timing, and longer-session stability. A screenshot or headless process smoke cannot verify controller response or race completion. Physical GameCube/Wii behavior is also unverified. Record the Dolphin version/backend or console setup and the outcome when performing an interactive test.

## Optional full-race CI diagnostic

For a longer free GitHub Actions check, open **Actions → GameCube first-render prototype build → Run workflow** and enable `full_race_diagnostic`. This uses a deterministic 6,000-frame neutral-steering DTM movie, launches the current DOL in Dolphin's Software Renderer, and checks the captured frame for the prototype's centered three-lap finish flag. The movie, log and screenshot are retained in the workflow artifact for seven days.

The normal push/PR pipeline leaves this option disabled to keep routine CI fast and reduce free Actions-minute usage. The finish-banner check shows that the tested build reached and rendered the prototype's finish state under this scripted emulator run; it is not a substitute for live-controller, long-session or physical GameCube/Wii validation.

## Source boundary

The C source and geometry here are original procedural scaffolding created for this repository. Do not add Step 102 source, third-party mod data, or commercial game content to this folder unless provenance and redistribution rights are separately cleared.

## What the automated Dolphin checks prove

The scripted DTM comparison is a **bidirectional input-path and camera-follow smoke diagnostic**. It captures neutral, right-input, and left-input frames. Both steered frames must keep the pod inside the image and near its neutral screen position. The test estimates the road center from the dark blue-grey asphalt boundaries across multiple rows, so the check remains valid when the terrain palette changes: right steering must shift that road silhouette left and the HUD marker right, while left steering must shift the road silhouette right and the HUD marker left.

The initial capture showed the pod moving from about x=429 to x=748 and clipping at the right image edge. That exposed a real camera-follow issue. The camera now follows the pod's lateral offset; the updated Software Renderer test requires the pod to remain un-clipped with no more than 80 px centroid drift and the road silhouette to shift at least 25 px in the expected direction for both steering inputs. Those are automated scene checks, not tuning claims about handling quality.

Keep validation claims separate:

- **Host tests and native DOL/ELF build:** the tested code compiles and its deterministic helper tests pass.
- **Dolphin null-video smoke:** the emulator process accepts/runs the DOL for the bounded smoke window; this is not visual verification.
- **Software-renderer camera-follow diagnostic:** scene signatures, pod framing, and road-silhouette/HUD response are checked against a neutral baseline in both left and right steering directions.
- **Interactive steering and complete race:** still require a visible Dolphin session (or physical hardware) with an actual controller profile, acceleration/braking/steering, three lap crossings, finish, reset, and evidence recorded against the tested commit.

Do not report the scripted capture as proof that the game is fully playable. Follow the interactive acceptance checklist in `../docs/NEXT_MILESTONE.md`.

