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
