# SW_RACER_RE → Step 102 → GameCube behavior matrix

This is an evidence-tracking document, not an assertion that the PC version and console versions behave identically. Keep the rows until evidence is recorded. Never mark a behavior as confirmed for GameCube/Wii solely because it appears in PC source.

The research rows below track PC findings mapped to Step 102 and console hypotheses; they are not a summary of the clean-room demo's implementation. On main, gamecube-demo/ has deterministic helpers for selected steering, boost, lap/finish, rival and off-road behavior, with host regression tests and a visible CI scene. That does not confirm equivalence to the original PC, GameCube, or N64 game, nor does it prove live controller behavior or a completed race.

**Reference snapshot:** SW_RACER_RE branch master at commit a9863edd4caaa573f89ff634fa7d1cd6d41738ab (reviewed 2026-10-14).  
**Status legend:** NOT STARTED · PC EVIDENCE RECORDED · PROTOTYPE MAPPED · STEP102 MAPPED · CONSOLE HYPOTHESIS · IMPLEMENTED · TESTED.  
**Current allocation:** 80% reverse-engineering research / 20% implementation, testing and management combined. Only one research question is active; see [RE-001 route/spline dossier](research/RE-001-route-spline-progress.md).

## Initial source observations from the reviewed PC revision

These are real source reads, not assumptions about the console versions. They are intentionally short behavioral/structural notes; no upstream code is copied into the project.

| Finding | Evidence and observation | What it does not prove |
|---|---|---|
| **SWR-001 — spline data and traversal are first-class systems** | [swrSpline.c, spline loading](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L14-L78) shows the code opening a spline block, checking an indexed spline range, loading the selected block into an asset buffer, byte-swapping header/control-point values, and setting a runtime control-point pointer. [Interpolation and cursor routines](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L86-L315) cover progress lookup, interpolation, cursor stepping/evaluation, and transform construction. | This documents the PC project's reconstructed format/behavior only. It does not establish that GameCube uses the same block layout, endianness, coordinate system, or exact spline data. It does not clear any PC-derived track data for redistribution. |
| **SWR-002 — at least one turning update is time-scaled** | [swrRace_UpdateTurn](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c#L1714-L1744) moves a turn rate toward a target using delta-seconds and integrates turn-rate/input into heading, wrapping heading to [-180, 180] degrees. This is a useful behavior reference for steering/turn smoothing. | One function using delta time does not prove the entire simulation is frame-rate independent. The PC mod release notes warn of frame-rate-sensitive physics. Boonta must test timing behavior on its actual target rather than assume PC timing or constants transfer. |
| **SWR-003 — parts of the reverse-engineered source remain unfinished** | [swrControl_ProcessInputs](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Main/swrControl.c#L20-L24) is still marked TODO; [spline stubs](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L522-L539) include TODO functions. Other modules also contain TODO/HANG sections. | The upstream percentage is analysis coverage, not proof that all functions, input logic, or systems are implemented. Treat unfinished functions as gaps to research, not as an API ready to copy or call. |
| **SWR-004 — PC route cursor is a branch-capable spline graph** | [Loader](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L14-L78) reads a spline block and connected control-point records; [branch stepping](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L180-L223), [cursor evaluation](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L245-L313) and [progress seek](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrSpline.c#L373-L410) establish graph traversal with a segment parameter, branch selection, and position/tangent/up interpolation. The current GameCube prototype instead samples a closed point loop in [track_sample_at](https://github.com/Master-Chiken/boonta-reborn-88/blob/fa8cee047ae8e74c30c87cd94977c434bb1c7398/gamecube-demo/source/main.c#L173-L240) and increments laps by scalar distance in [main.c](https://github.com/Master-Chiken/boonta-reborn-88/blob/fa8cee047ae8e74c30c87cd94977c434bb1c7398/gamecube-demo/source/main.c#L1256-L1275). The pinned PC source also distinguishes B-spline, flat Bezier and Bezier-with-interpolated-up types, and documents a baked route-sample-to-track-mesh lookup. By contrast, the inspected prototype measures straight chords between control points, then maps the chord fraction to a Catmull–Rom parameter; this is not demonstrated to be exact arc-length sampling of the smoothed curve. See the expanded [RE-001 dossier](research/RE-001-route-spline-progress.md). See the [RE-001 dossier](research/RE-001-route-spline-progress.md) for the scope and limitations. | Confirms different representations in the inspected PC source and current clean-room prototype only. PC lap-progress/wrap helpers are now traced separately in SWR-005, but their end-to-end caller has TODO/HANG stubs; Step 102/actual GameCube route data remains unmapped. Do not infer console parity or choose an implementation yet. |
| **SWR-005 — PC lap progress is cursor-normalized, but the reconstructed path is incomplete** | [swrRace_LapProgress / swrRace_LapCompletion](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c#L4663-L4740) derive progress from a control point's baked progress and `segmentT`, clamp closed-route progress below 1.0, and detect a wrap using previous progress plus a high-water mark. The caller [swrRace_UpdateRaceProgress](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c#L4768-L4800) calls `swrRace_AdvanceSplineCursor`, but that function and several related route-binding helpers are `HANG("TODO")` stubs in this revision. | The lap-crossing helper is evidence about the reconstructed design, not proof of a complete working original-PC movement path. It proves nothing about actual GameCube/Wii logic; Step 102 mapping is still not verified. The full caveat is in the [RE-001 dossier](research/RE-001-route-spline-progress.md). |

Follow up by mapping each finding to Step 102's source and tests, then add GameCube-specific evidence when available.

## First vertical-slice research

| Subsystem | PC reference entry point | Step 102 candidate | Evidence to record | GameCube/Wii test needed | Status |
|---|---|---|---|---|---|
| Race state and laps | src/Swr/swrRace.c, symbols and relevant function records | source/main.c; confirm race-flow modules and tests from the source archive | Start/finish transitions, lap crossing/ordering, reset rules, timing and edge cases; link exact upstream locations | Verify how the selected console build detects route checkpoints/lap transitions and finishes a race | NOT STARTED |
| Pod motion and control | src/Swr/swrRace.c, src/Main/swrControl.c, relevant function/symbol entries | source/racer_physics.c; confirm control/state modules and tests | Acceleration, brake, steering, drift, boost/heat, speed caps, collision response, damage, timing assumptions; distinguish observed vs inferred behavior | Test input mapping and repeatable physics in the target build; do not assume PC frame-rate dependency applies identically | NOT STARTED |
| Route/spline and track progression | src/Swr/swrSpline.c, related track/block format notes | source/track_catalog.c, reference/data tools; source/track_centerlines_pc.generated.h remains on provenance hold | Coordinate system, scale, route progression, lane/segment representation, checkpoint order, lap closure; add format evidence without copying track data | Validate against lawful GameCube-specific inputs and the actual target code; compare route closure and coordinate orientation | NOT STARTED |
| Camera and transforms | src/Engine/rdCamera.c, src/Primitives/rdMatrix.c, src/Swr/swrRender.c | Map to the actual Step 102 camera/render files after source audit | Follow/look-ahead, orientation/bank, clipping, coordinate transforms, update order | Verify PowerPC/GX camera and frame behavior in interactive Dolphin or hardware | NOT STARTED |
| Rival AI | Relevant function/symbol records and race/object behavior; do not assume a single named AI module | source/rival_ai.c | Racing line, target selection, speed differences, overtaking, collision/recovery rules; label each finding's confidence | Create deterministic repeatable scenarios; compare observed console behavior only where target evidence exists | NOT STARTED |
| Resource formats and loading | src/Swr/swrAssetBuffer.c, swrLoader.c, swrModel.c, swrSpline.c | tools/, data/, parser tests; exact mapping awaits archive audit | Headers, alignment, byte order, dimensions, offsets, references, compression and error handling | Validate format independently against lawful target-version test inputs; no proprietary content copied | NOT STARTED |
| HUD, render effects and weather | src/Swr/swrPlayerHUD.h, swrRender.c, swrDisplay.c, swrWeather.c; PC mod deltas for examples | Map to actual Step 102 display/render modules if cleared | HUD state and ordering, fog, weather and effect triggers, visual priority | Estimate GX cost and verify each effect visually; PC renderer changes are not a console implementation | NOT STARTED |

## Evidence record template

For each new finding, record one block using this schema:

- **ID:** SWR-###
- **Question:** one specific behavior/format question.
- **Upstream reference:** URL to exact file and symbol/function, plus commit SHA.
- **Observation:** concise factual description, no code copy.
- **Confidence:** confirmed from source / inferred / community report / unverified.
- **Platform:** Windows PC / GameCube / N64 / Wii / unknown.
- **Step 102 mapping:** exact source file/function/test from the reviewed archive, or not yet mapped.
- **Console hypothesis:** what needs to be true for GameCube/Wii and what might differ.
- **Implementation target:** module/function in Boonta, to be confirmed after source mapping.
- **Acceptance test:** reproducible inputs and observable expected behavior.
- **Provenance/license:** separate status for code, data, and assets; code or assets are not cleared by a behavior note.
- **Result:** not started / tests passed / native build passed / interactive test passed, with run links.

## Import and license guardrails

- SW_RACER_RE is licensed AGPL-3.0 according to GitHub. Keep it as a linked research reference by default. Do not copy or adapt its code into this project under the existing repository license without a deliberate license-compatibility review and owner decision.
- Its assets/ and dinput_hook/ trees may contain third-party code, test resources, mod files, custom tracks or generated/extracted data. Review file-level licensing and provenance before any reuse; root LICENSE does not prove every asset is redistributable.
- Step 102 route-centerline data is independently held for provenance review. Do not treat SW_RACER_RE as clearing those files.
- Do not copy commercial ROMs/disc images, extracted models/textures/audio, binaries, or resource blocks into the public repository, CI artifacts or AI prompts.
- Do not label PC behavior confirmed on GameCube until a console-specific source/data observation or controlled target test supports it.

## Exit criteria for the first three rows

Before large gameplay work begins, produce:
1. at least one evidence-linked PC behavior note for race/lap flow;
2. a Step 102 source/test mapping for race flow and pod physics;
3. a documented spline/route hypothesis with all PC-derived route data still excluded unless separately cleared;
4. a short list of explicit GameCube validation tests to run after the DOL is available.

Only then use these results to guide the first repeatable playable vertical slice.