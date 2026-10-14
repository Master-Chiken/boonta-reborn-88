# SW_RACER_RE → Step 102 → GameCube behavior matrix

This is an evidence-tracking document, not an assertion that the PC version and console versions behave identically. Keep the rows until evidence is recorded. Never mark a behavior as confirmed for GameCube/Wii solely because it appears in PC source.

**Reference snapshot:** SW_RACER_RE branch master at commit a9863edd4caaa573f89ff634fa7d1cd6d41738ab (reviewed 2026-10-14).  
**Status legend:** NOT STARTED · PC EVIDENCE RECORDED · STEP102 MAPPED · CONSOLE HYPOTHESIS · IMPLEMENTED · TESTED.

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