# SW_RACER_RE portable-system lessons for Boonta — 2026-11-08

This is a **behavior/architecture research note**, not a code import. The inspected upstream source is Windows-PC/DirectInput/OpenGL-specific and is licensed AGPL-3.0. No upstream implementation, game asset, proprietary data, binary or vendor dependency was copied into the clean-room GameCube/Wii runtime.

## Exact source revisions inspected

Repository: [tim-tim707/SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE), branch `master`, reviewed 2026-11-08.

| File | Exact blob SHA | What it demonstrates | Boonta disposition |
|---|---|---|---|
| `dinput_hook/ai_tuning.cpp` | `a7f2f5d7d6cbc936b3d0b3cd05aa6e6d4ceec3f0` | Separates per-track AI level/spread, pace-setter behavior, rubberbanding, global speed scale, proximity avoidance, blocking, scripted shortcuts and solo catch-up. Captures track defaults only after track load; settings persist separately. | **Adapt as behavior requirements**, not copied code/constants. Boonta needs a race AI state model and deterministic scenarios; current demo's lane-sway rivals are not equivalent. |
| `dinput_hook/perf_stats.cpp` | `51c15c27c43ab2fcf05f346bf6ee836793d75f16` | Separates CPU frame work, present/swap wait, GPU elapsed time and draw counts. Reads GPU query results several frames later from a ring to avoid blocking the render thread. | **Adapt the measurement model.** For GX, first add portable CPU frame timing and subsystem counters; only add platform GPU/FIFO measurements after confirming supported libogc APIs and profiling overhead. |
| `dinput_hook/perf_stats.h` | `fbddae6c02c0207537a492825675071d2bbb531c` | Defines a compact per-frame telemetry contract. | Use as a design reference for a small fixed-size telemetry struct and optional HUD/debug output. |
| `dinput_hook/game_deltas/swrSound_delta.cpp` | `7b834f8af486a7412cbdbd194cb7109c56f88413` | Avoids repeated sound-file probes by listing search directories once and caching parsed WAV headers keyed by normalized path, size and modification time; falls back to stock lookup on misses/aliases. | **Adapt the cache/invalidation pattern only.** Current Boonta has no audio subsystem; do not port Windows APIs, game sound-bank layouts, WAV cache binary format or proprietary audio. |
| `dinput_hook/model_replacement.cpp` | `53cc76da6d22158caa74a8134b7ba1cdba4b8a93` | Maps stock model IDs to loose files, assembles a one-entry model block, temporarily swaps a global loader path, then restores it. | **Reference only.** This depends on PC RAWM/model-block semantics and global PC loader state. For Boonta, first define an owned asset manifest/format and a bounded, validated GX resource loader; no RAWM compatibility is implied. |
| `dinput_hook/model_replacement.h` | `93fefb18505326a2804c9500d38e42ce1bbc0621` | Documents the PC-specific RAWM chunk contract. | **Do not transplant** its byte layout, IDs, loader assumptions or extracted payloads to GameCube. |
| `dinput_hook/game_deltas/sony_pad_rumble.cpp` | `f4f49c810020f7df2bfe0d0fd4736a3c073b9484` | Windows HID/SetupAPI implementation for Sony controller rumble. | **Do not port.** Only the high-level capability idea (optional rumble feedback) is a future input requirement; GameCube PAD rumble and Wii controller support need native platform APIs and explicit hardware tests. |

## Concrete implementation opportunities

### 1. Make performance measurable before expanding graphics

Boonta's current clean-room prototype already has native GX rendering, route sampling, HUD and rivals. Add a low-overhead telemetry contract before adding expensive scenery:

- frame delta and rolling CPU update/render milliseconds;
- counts for visible road segments, wall sections, rival pods and submitted GX batches;
- route-sampler/cache counters only in diagnostic builds;
- maximum and rolling-average frame time, not only an average;
- deterministic host tests for counter reset/aggregation;
- no synchronous GPU readback in the frame loop.

Do not claim GPU time from CPU wall-clock measurements. Add hardware/GX-specific metrics only after checking the exact supported API and profiling their cost.

### 2. Specify rivals as race agents, not decorative lane motion

The PC tuning panel reveals useful independent behavior dimensions:

- authored per-track baseline difficulty and pack spread;
- pace-setting versus each rival's actual speed response;
- catch-up/rubberbanding policy;
- nearest-rival avoidance and collision/blocking policy;
- scripted shortcut choices versus free route decisions;
- player catch-up assist as a separate optional rule.

Boonta should first implement deterministic host-side policy functions with explicit inputs/outputs and fixed-step tests. Keep AI decisions separate from vehicle physics and rendering. Do not copy PC tuning ranges or assume their units/timing match the console game.

### 3. Build an owned asset pipeline with explicit manifests

The PC model replacement mechanism demonstrates a useful workflow shape (ID -> replacement record -> validate -> load -> restore), but its binary format and global-path swap are not portable. Boonta's own pipeline should instead use:

- a versioned JSON or generated manifest for owned assets;
- stable logical IDs, dimensions, format, byte length and content hash;
- explicit GX-compatible texture/mesh formats and alignment;
- bounds/overflow checks before allocation or DMA;
- synthetic fixtures and byte-exact round-trip tests;
- immutable resource handles rather than temporarily mutating a global file path.

Do not build an importer around PC RAWM/RAWS/RAWT assumptions without independent format proof and a lawful target-version test fixture.

### 4. Audio: separate discovery, metadata and playback

The upstream audio optimization suggests avoiding repeated directory scans and parsing the same header on every registration. When Boonta audio begins, measure startup and playback separately, keep metadata caching invalidated by source identity/version, and design bounded voice/channel allocation. First evaluate native GameCube audio support and dependencies; the existing research inventory lists AudiOGC as an archived MIT candidate, not an approved dependency. Review embedded library notices and test compatibility before adding it.

## Prioritized Boonta follow-up

1. **P0 — Race progression and rival behavior:** finish a coherent playable race slice before spending time on advanced audio, rumble or asset replacement.
2. **P1 — Telemetry:** establish CPU/frame-time and draw/batch baselines to prevent regressions while improving the scene.
3. **P1 — Asset manifest/loader design:** define a clean-room owned format and synthetic fixtures before loading more assets.
4. **P2 — Audio prototype:** evaluate native audio engine/toolchain fit and implement original test tones/effects only.
5. **P3 — Rumble:** only after controller backend consolidation and real hardware/emulator verification.

## Evidence and limitations

- Source observations above are **CONFIRMED-IN-CODE** at the exact blob SHAs shown.
- The PC mod's behavior has not been independently re-run here; no **CONFIRMED-IN-RUN** claim is made.
- No source code was imported from these files, and no Windows build or commercial-game asset extraction was performed.
- PC code remains within the AGPL-3.0 research boundary. Do not copy it into the repository's MIT GameCube/Wii runtime without a deliberate license decision.
- Boonta's current GameCube prototype README documents a visible CI scene and scripted finish diagnostic, but interactive three-lap controller acceptance remains outstanding.
