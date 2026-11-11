# GameCube first-render / driving-input prototype

This directory is a **clean-room, original technical slice** for Boonta Reborn 88. It is separate from the unreviewed Step 102 source bundle and contains no extracted game code, commercial assets, models, textures, music, voices, ROMs, or disc images.

## Current scope

- Native GameCube GX initialization and 3D colored-vertex rendering.
- A genuinely scrolling procedural desert course:  curved asphalt segments, lane markers, and faceted canyon walls advance continuously with race distance; the start/finish stripe approaches once per lap instead of receding. The environment uses a warm desert floor, daylight sky, and original low-poly canyon geometry.
- A spline-aligned desert canyon with a deterministic staggered rock-ridge silhouette and faceted outcrops, avoiding uniform wall tops.
- An original low-poly twin-engine racer authored in `boonta-mesh-v1` JSON, exported to a validated C mesh and textured through the native GX RGB565 path; its exhaust plumes still lengthen with speed and boost.
- GameCube controller steering with lateral inertia, off-road speed loss, and rail-edge recovery, plus throttle, brake, pitch, and slide. Pitching nose-down increases forward progress at the cost of steering authority; pitching nose-up slows progress but improves steering. Holding L initiates a low-grip slide: it increases turn impulse while retaining sideways drift, so releasing it early is part of cornering. Pitch/slide state is exposed in the HUD and covered by deterministic host tests.
- Three clean-room procedural rival craft start at staggered route-distance positions and keep persistent progress for the whole race. They adjust lanes and pace for upcoming corners, can collide with the player, and can be overtaken without teleporting back ahead; up to eight overtake markers are shown in the HUD.
- A basic speed bar, steering-position tick, rechargeable boost-energy meter, overheat/cooldown bar, race clock, current-lap timer and best-lap display, lap-progress bar, repeating start/finish stripe, and three completed-lap indicators (the prototype's configured race limit).
- An explicit READY → ACTIVE → PAUSED → RESULTS session: Start begins the run, toggles pause/resume while racing, and restarts after the three-lap results screen; Y returns to READY. The results panel freezes the run and shows only measured lap count, total time, last/best lap, and overtakes.
- A time-based damped chase camera that follows both the vehicle-relative position and route look-ahead target; its exponential response is stable across 50/60 Hz update cadence, bounded after stalls, and snapped cleanly on race reset.
- A reproducible CI build that uploads the resulting DOL and ELF if compilation succeeds.

This is a gameplay prototype, not the completed racer and not a port of the commercial game. Rivals now keep independent absolute route progress, and collision/overtake events are transition-based; their pace and race strategy remain deliberately simple, and a complete leaderboard/championship system is not implemented. Audio, saves, a title menu, and a full physics model are not implemented.

## Original player mesh and texture

The player's hull is an original source-authored indexed mesh. The project validates its positions, UVs and indices on the host, exports a deterministic C header, and checks that the generated header matches the source. The matching 16×16 RGB8 texture source is validated and quantized to GX-tiled RGB565 by a small host-side exporter; aligned texels are copied and cache-flushed before GX upload. This is an owned test asset, not extracted game content. Runtime filesystem loading and proprietary model/texture parsing are not implemented.

The procedural course, rival craft, controls, dynamic exhaust and HUD remain separate from this asset. Successful rendering in Dolphin is evidence for this one original mesh/texture path, not proof of full game-asset compatibility or manual-controller acceptance.

## Runtime track source

The current demo oval is authored as the clean-room `boonta-route-graph-v1` source in `gamecube-demo/data/original-test-oval-route-graph.json`. Its separate `original-test-oval-surface-widths.json` map supplies road widths independently of route topology.

The graph has eight nodes and eight cubic Bezier edges. The native runtime now evaluates those Bezier edges directly through `source/route_graph_sampling.h`, using the generated `source/generated_route_graph.h`; it no longer uses the older Catmull–Rom track sampler as its live geometry path. The offline exporter samples the same clean-room graph into a dense legacy `boonta-track-v1` fixture for format/compatibility regression tests, but the renderer's active centerline is the direct runtime Bezier representation.

At first use, the C sampler builds a 128-interval distance lookup for each edge and caches the start distance of every edge. Per-frame samples use binary search over the eight edges (at most three comparisons) and each edge's 128 intervals (at most seven comparisons), instead of scanning the arrays linearly. Road widths remain separate surface samples and are interpolated independently. The lookup's scaled distance coordinates use the generated `BOONTA_RUNTIME_ROUTE_LENGTH` period so route wrapping and lap counting share the same lap coordinate.

The native sampler also exposes `boonta_route_graph_sampler_sample_edge_at`: callers can select one edge and sample it by local arc distance without wrapping into the next edge. It shares the cached distance lookup with the closed-loop sampler and clamps to the selected edge endpoints. `boonta_route_graph_sampler_sample_relative_to_cursor` samples look-ahead/look-behind coordinates from a copy of the active cursor, so rendering cannot mutate race history; at the initial start line it wraps a small negative look-behind across the closed-loop seam.

When a branched catalogue is compiled, the HUD lap-progress bar reads the active cursor edge's authored normalized progress span. It does not use the oval's fixed physical length, because different branch choices may produce different lap distances. The unbranched oval keeps its existing scalar-distance HUD calculation.

The separate `source/route_cursor.h` adds a distance-based topology cursor with bounded edge history, explicit choices at splits, reverse/forward replay, replaceable future decisions and distinct open-route/closed-loop terminal behavior. The generated native header carries node indices, edge endpoints, progress spans and start/closed-loop metadata. The GameCube runtime initializes this cursor alongside the race distance and advances it by the same physical distance delta as the vehicle; reset/restart reinitializes both states together. **The current single-loop oval uses the direct scalar-distance sampler for renderer queries**, avoiding two full cursor/history copies and cursor movement for each road, wall, camera and vehicle sample. The cursor is still maintained for route/lap state, and branched route catalogues use cursor-relative sampling so their selected path history drives look-ahead/look-behind. Host tests traverse the generated oval with the cursor, compare cursor-relative geometry/width against the direct whole-loop sampler across the finish seam, and verify that look-ahead/look-behind sampling does not mutate the live history. A source-contract test protects the fast path and the branched cursor adapter.

The dense native C regression measures the current runtime Bezier curve at **184.563965 m** against the generated lap coordinate **184.563477 m** (**0.00026% difference**). Tests compare direct edge samples at every one of the 128 lookup boundaries and every interval midpoint on all eight edges, as well as authored-node joins, legacy bake samples, negative and multi-lap wrap, seam continuity, and non-finite inputs. The separate older Catmull–Rom compatibility test still reports its own 0.01692% difference against the legacy track-v1 lap period; that is not the current runtime curve measurement.

The runtime currently supports one unbranched closed oval. The neutral route-graph format and host-side cursor can represent branch metadata, but runtime branch selection/history, split/rejoin traversal, and B-spline playback are not connected to vehicle movement, collision or lap state. Branched graphs remain data/tooling capability, not a claim of playable runtime support.

## Controls

- Control Stick left/right (or D-pad): steer.
- Control Stick up/forward: pitch down for more forward progress but weaker steering; down/back: pitch up for slower progress and tighter control.
- L trigger: slide/drift through corners; turn response grows while sideways drift lasts longer.
- A: accelerate.
- B: brake.
- Hold X + A: engage boost while accelerating; energy drains and recharges on release. Heat rises during boost; at 98% heat, boost locks out until the engine cools to 60% or below.
- Start: toggle pause/resume during a live race; after the finish state, Start restarts a fresh run. The pause icon appears in the center of the HUD.
- Y: reset the run, lap counter, rival, overtake indicators, and pause state at any time.

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



## Native Wii Classic Controller backend

The Wii target is built separately with `make -f Makefile.wii`; it uses libogc's `WPAD` interface and does not add Wii-only symbols to the GameCube build. At runtime, channel 0 is accepted only when `WPAD_Probe` reports `WPAD_EXP_CLASSIC` and the current sample contains Classic expansion data. A disconnected controller or a different expansion is treated as neutral input.

The Classic mapping is: left stick for steering and pitch; A/B for throttle/brake; X+A for boost; Y for reset; Plus for pause/restart; D-pad left/right for steering and up/down for pitch; ZL/ZR and the analog L/R shoulders for slide. The existing GameCube build retains its `PAD` backend.

Host tests cover button translation, analog-stick pass-through, analog shoulder scaling, digital trigger clicks, and neutral behavior for a missing or non-Classic expansion. The Wii artifact still needs a physical test on the owner's Wii with the Under Control Classic Controller; a successful cross-build does not prove that this individual unit is recognized.


### Wii Classic Controller runtime details

The Wii backend calls `WPAD_SetDataFormat(WPAD_CHAN_0, WPAD_FMT_BTNS_ACC_IR)` only after `WPAD_Probe` confirms that channel 0 is connected with a Classic expansion. libogc ignores a channel data-format request when no controller is assigned, so setup is deferred until that probe succeeds and is repeated after disconnect or a non-Classic expansion. The input loop then verifies `WPAD_DATA_EXPANSION` before reading the Classic payload. The left stick is converted from its calibrated raw minimum/centre/maximum values into the signed gameplay range; the analog shoulder values are scaled to 0–255 and the digital ZL/ZR clicks are retained.

| Classic control | Racer action |
|---|---|
| Left stick left/right | Steering |
| Left stick up/down | Pitch |
| D-pad left/right | Steering |
| D-pad up/down | Pitch |
| A / B | Accelerate / brake |
| Hold X + A | Boost |
| L / R analog shoulders or ZL / ZR clicks | Slide |
| Plus | Pause / resume; restart after finish |
| Y | Reset at any time |

There is no separate repair action in the current gameplay slice. Home, Minus and the right stick are currently unused. The mapping is for this native Boonta Wii build only; it does not configure Not64 or the original N64 game.

The current CI run verifies the GameCube and Wii native builds, host translation tests and bounded Dolphin diagnostics. It does not test the Under Control unit or prove a manually completed three-lap race.