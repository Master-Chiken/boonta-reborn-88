# Next milestone: move from toolchain demo toward the faithful GameCube/Wii reconstruction

## Current confirmed progress

- The separate clean-room C prototype in `gamecube/source/main.c` now builds into a non-empty `boonta_demo.dol` through GitHub Actions.
- The prototype draws a procedural ring track, pylons, finish marker, original low-poly pod, chase camera, and HUD, with acceleration, braking, boost/heat, lateral movement, pause/reset, and a three-lap finish state implemented in code.
- The latest confirmed native cross-build is the [GameCube prototype workflow](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-smoke.yml).
- Repository safety and CodeQL have also passed on a recent branch revision.
- **Not verified yet:** booting the DOL, graphics, controller input, complete race behavior, or performance in Dolphin/console.
- The Step 102 source archive remains subject to file-group and asset provenance review. PR #17 contains a selective source-only candidate on a separate branch; it remains a draft and has not been merged into `main`.
- Latest inspected Step 102 CI evidence: host regression, source-policy check, and native DOL build passed; visible Dolphin preview failed because Dolphin exited before a valid frame was captured. See [the dated diagnostic record](STEP102_IMPORT_AUDIT.md#latest-ci-evidence-reviewed-2026-10-14).

## Latest gameplay increment — rival contact and impact feedback

The prototype now detects simple player/rival contact when racers are close both around the circuit and across the track. Contact applies a speed penalty, a small lateral displacement, and a short cooldown to avoid applying the penalty on every frame. The HUD displays the impact count. This is a deliberately simple first gameplay rule; it is not realistic collision physics.

The portable logic tests now include collision penalty, cooldown, reset, and lateral-separation checks. Treat the latest successful GitHub Actions run—not a hard-coded suite count in this document—as the source of truth for validation. Visual HUD layout and the actual feel of collisions still need interactive Dolphin testing.

## Latest gameplay increment — deterministic rival lane movement

The clean-room race logic now gives each of the three procedural rivals a smooth, bounded lane sway. The motion is deterministic (no random-number state), keeps rivals in their original lane order, and remains within the track's lateral limits. This is a small gameplay improvement, not original-game AI or a substitute for interactive playtesting.

A new host test checks that rival lane movement is bounded, smooth between frames, repeatable for identical inputs, and does not let rivals cross lanes. Confirm the latest GitHub Actions result before treating the change as validated; test-suite counts can change as coverage grows.

## Platform decision update — GameCube vs Wii remains open

The N64 edition running through Wii64/Cube64 is a **reference/testing option**, not the final remaster. It may help compare the N64 game's course layouts, handling, rivals and progression, but compatibility for this specific game must be tested. Emulation does not provide the source code or automatically create an HD remaster.

Do not choose the final native target by assumption. Keep GameCube and Wii open until the same minimal native vertical slice has evidence for boot, rendering, controller input, one complete race, frame pacing and memory/performance. Record emulator/version/settings separately from real-hardware results. Keep any ROM/disc image and proprietary extracted assets out of the public repository.

The intended order remains: faithful original-game baseline first; then the best graphics upgrades feasible within native console limits; then original bonus content. “HD” must distinguish higher-quality assets and enhanced rendering from native 720p/1080p output, which should not be promised for GameCube/Wii.

## PC-first research direction

The original Windows PC game and existing community reverse-engineering/modding work are the primary research starting point. Use the [PC-first research and reuse plan](PC_FIRST_RESEARCH_PLAN.md), the detailed [PC technical map and external research inventory](PC_TECHNICAL_MAP.md), and the first [code-level findings from SW_RACER_RE](PC_SOURCE_FINDINGS.md) before implementing systems from scratch. The technical map records existing tools, subsystem questions, evidence levels, and a prioritized research workflow. The source findings already identify spline loading/traversal, track progress, ground contact, vehicle state, AI flags, progression/menu functions, and the PC replacement-renderer boundary. They distinguish direct code evidence from assumptions that still require runtime checks. No ROMs, executables or extracted commercial assets should be committed.

## Work sequence toward the actual end goal

1. Keep the build/safety/static-analysis checks green, but do not mistake the procedural `gamecube/` demo for the intended game.
2. Complete the [Step 102 path-by-path clearance register](STEP102_PATH_REVIEW_REGISTER.md). Treat every path as held until authorship, origin and redistribution terms are evidenced; resolve licensing before import.
3. Import the cleared GameCube/Wii-oriented source candidate to a review branch, preserving the tests and build infrastructure. Exclude uncleared track centerlines, models, audio, ROMs and disc images.
4. Reproduce the archive's reported host test suite in GitHub Actions, then build the full candidate with devkitPPC/libogc.
5. Diagnose the failed visible-preview run from its [CI log and artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38634953318), then test the candidate in Dolphin: boot, rendering, controller input, race start/finish, tracks, vehicles, modes, saves, stability and performance. Fix real blockers from evidence.
6. Run a small platform comparison: GameCube-target DOL and Wii-target build where supported, using the same scene and test checklist. Separately test whether Wii64/Cube64 can run the N64 edition as a reference; record its compatibility without treating it as the port.
7. Create the PC/Dreamcast/N64 comparison matrix and verify each important gameplay/system claim against documentation or a lawful local run of the relevant edition.
8. Implement missing original-game systems and content until a faithful playable baseline exists.
9. Only after that baseline is stable, work on improved graphics, bonus content, new modes and quality-of-life improvements.

## Owner-only actions

- To use the optional Gemini GitHub agent, create a free Gemini API key and add it as the repository secret `GEMINI_API_KEY`. Do not enable billing. See [AI automation setup](AI_AUTOMATION_SETUP.md).
- To test interactively without local installs, create a Codespace on `audit/step102-import-gate`; stop/delete it afterward to respect free quotas. See [cloud guide](CLOUD_DEV_WORKFLOW.md).
- For Dolphin runtime proof, a person must open/download the artifact and run it in Dolphin on an appropriate environment. The automated compile cannot substitute for this visual check.

## Free-only policy

Do not add a payment method, enable billing, or use paid APIs. Free-tier quotas can change; stop if a quota is unavailable or exhausted.


## New portable subsystem — sampled track path primitives

- Added `gamecube/source/track_path.h` and `track_path.c`: clean-room polyline path utilities for open/closed centerlines, total arc length, distance/progress sampling, unit tangent, and nearest-segment projection.
- Added `gamecube/tests/track_path_test.c` with synthetic-only fixtures covering open endpoints, closed-loop wrapping, negative progress, nearest projection, and invalid/degenerate inputs.
- Added a strict `-std=c99 -Wall -Wextra -Werror` host-test step to `.github/workflows/gamecube-smoke.yml`.
- **Integration status:** the renderer and `race_logic.c` still use the existing circular-track model. The new path module is not yet connected to player movement, AI, lap counting, or rendering. This is the first reusable geometry foundation, not yet a gameplay change.
- **Validation status:** commits were fetched back from GitHub to verify file contents and workflow insertion. Await the new CI run before claiming the strict tests or native DOL build pass for this revision.


## Sampled-track rendering milestone (in progress)

- `gamecube/source/main.c` now initializes a clean-room, 96-point closed centerline with gentle radius variation and uses the shared `TrackPath` sampler to place the player and rivals.
- Road surface, contrasting kerbs, center markers, finish line, pylons, pod orientation, and chase camera now derive from the sampled path instead of drawing only a perfect circular ring.
- Rendering uses direct indexed centerline samples for repeated road vertices to avoid recalculating the full path length for every vertex. Vehicle placement still uses the generic path sampler.
- **Gameplay limitation:** race progress, lap detection, opponent AI, and collision checks still use the old angular/circular approximation. This milestone changes prototype geometry and placement, not yet the full physics model.
- **Validation:** the CI run for commit `17f29af471a85d125b2787232f55658c9c46860b` built a non-empty GameCube DOL and passed both host test jobs. Dolphin visual-frame and process checks were still running at last inspection. The rendering optimization is included in the current branch; the newest host tests pass. Native build and Dolphin visual/process checks are tracked separately.


## Track-aware race progression (implemented; host tests green)

- `race_update_track_dt(..., track_length)` advances player and rival progress using the sampled centerline length, converting world-units-per-second to normalized lap progress. Legacy `race_update_dt` remains available for circular callers without a path.
- The GameCube prototype caches `track_path_length(&track_path)` after generating its clean-room centerline and now calls the track-aware update each frame.
- Regression coverage includes track-length-based progress and the legacy fallback. GitHub Actions host tests passed: `race_logic_test: 15 suites passed` and `track_path_test: 6 suites passed`.
- Native GameCube build and Dolphin runtime checks for the newest revision were still running at the last check. This is still a procedural prototype; rival collision thresholds remain approximate and are not original-game physics.


## Latest validation checkpoint — 2026-10-14

- Commit `524469ec154299d138e360b2c3d1d714d31837f2`: host regression jobs passed with `race_logic_test: 15 suites passed` and `track_path_test: 6 suites passed`.
- The same revision's GameCube build job completed successfully and uploaded a non-empty DOL.
- The null-video Dolphin process smoke test had passed on the prior geometry revision; the OpenGL frame-capture diagnostic failed because Dolphin exited before the script could capture a frame. Therefore **actual visible gameplay is not yet verified**; the OpenGL failure is a tooling/runtime-validation blocker, not evidence that the image rendered correctly.


## Cross-platform source material supplied for research — 2026-10-15

Use the user's existing local reference material before reinventing track/game systems:

- `Game SW Racer 1999.zip` — the supplied PC-game archive (kept as a local reference; do not commit its executable or extracted commercial assets).
- `SW Racer 1999- (US).z64` — the supplied N64 ROM (local-only reference; never add the ROM to GitHub or CI).
- `Star_Wars_Racer_GameCube_Step102.zip` — 359-file source/research archive, about 2.65 MB uncompressed. Its accompanying inventory classifies 171 source/tool/test files for license review, 152 documentation files for review, and 25 files as hold-for-provenance. **No file in that inventory is marked cleared for redistribution.**
- The PC reverse-engineering repositories and tool findings documented in `PC_TECHNICAL_MAP.md` and `PC_SOURCE_FINDINGS.md` remain the best starting point for understanding the game. Reuse ideas and independently verified formats; do not assume a PC function, track coordinate system, or asset layout transfers unchanged to N64, GameCube/Wii, or Dreamcast.
- A separate Dreamcast archive/image is not confirmed in the currently visible Library inventory. Dreamcast stays in the comparison plan, but no Dreamcast-specific extraction result should be claimed until its supplied source is identified and examined.

The workflow is: keep originals local; inspect the archive's own notes/tools; record which edition each finding belongs to; verify results against synthetic tests and, where lawful, a local run; then port only clean-room logic or files with clear redistribution permission. Never push a ROM, disc image, proprietary executable, or unreviewed extracted models, textures, audio, or track data.

## Latest gameplay increment — track-length-aware contact threshold

- Collision distance now scales with the known centerline length: the prototype converts a fixed 2.5 world-unit contact radius into normalized lap-angle space. The legacy 0.12-radian threshold remains for callers without a valid track length.
- Added a regression test that compares near and far contact at two different track lengths. This prevents longer courses from making the collision window arbitrarily wide in world space.
- Verified the latest PR-triggered CI host run: `race_logic_test: 16 suites passed`, `track_path_test: 6 suites passed`, native GameCube DOL build passed, repository safety passed. The optional Dolphin OpenGL frame-capture diagnostic still failed because Dolphin exited before a frame could be captured; visible gameplay remains unverified.
- Source/test commits: `905a5e7a483a7b624c58501a09dfcbba0b345847` and `0789eadcde8875cf32e0fe5069726318d83b5048`. The changes are on `audit/step102-import-gate`; `main` remains untouched.
