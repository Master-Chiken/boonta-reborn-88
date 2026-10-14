# Next milestone: move from toolchain demo toward the faithful GameCube/Wii reconstruction

## Current confirmed progress

- The separate clean-room C prototype in `gamecube/source/main.c` now builds into a non-empty `boonta_demo.dol` through GitHub Actions.
- The prototype draws a procedural ring track, pylons, finish marker, original low-poly pod, chase camera, and HUD, with acceleration, braking, boost/heat, lateral movement, pause/reset, and a three-lap finish state implemented in code.
- The latest confirmed native cross-build is the [GameCube prototype workflow](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-smoke.yml).
- Repository safety and CodeQL have also passed on a recent branch revision.
- **Not verified yet:** booting the DOL, graphics, controller input, complete race behavior, or performance in Dolphin/console.
- The Step 102 source archive remains outside the repo pending its separate code/asset provenance review.

## Latest gameplay increment — rival contact and impact feedback

The prototype now detects simple player/rival contact when racers are close both around the circuit and across the track. Contact applies a speed penalty, a small lateral displacement, and a short cooldown to avoid applying the penalty on every frame. The HUD displays the impact count. This is a deliberately simple first gameplay rule; it is not realistic collision physics.

The portable logic tests now include collision penalty, cooldown, reset, and lateral-separation checks. The expected suite count is 13, but these new changes must pass GitHub Actions before being considered validated. Visual HUD layout and the actual feel of collisions still need interactive Dolphin testing.

## Latest gameplay increment — deterministic rival lane movement

The clean-room race logic now gives each of the three procedural rivals a smooth, bounded lane sway. The motion is deterministic (no random-number state), keeps rivals in their original lane order, and remains within the track's lateral limits. This is a small gameplay improvement, not original-game AI or a substitute for interactive playtesting.

A new host test checks that rival lane movement is bounded, smooth between frames, repeatable for identical inputs, and does not let rivals cross lanes. The expected host test output is now `race_logic_test: 11 suites passed`. Confirm the GitHub Actions result before treating the change as validated.

## Work sequence toward the actual end goal

1. Keep the build/safety/static-analysis checks green, but do not mistake the procedural `gamecube/` demo for the intended game.
2. Finish the Step 102 path-by-path manifest review. The manifest already classifies source/tests/tools/docs separately from assets and PC-mod-derived route data; resolve authorship and licensing for each source group before import.
3. Import the cleared GameCube/Wii-oriented source candidate to a review branch, preserving the tests and build infrastructure. Exclude uncleared track centerlines, models, audio, ROMs and disc images.
4. Reproduce the archive's reported host test suite in GitHub Actions, then build the full candidate with devkitPPC/libogc.
5. Test the full candidate in Dolphin: boot, rendering, controller input, race start/finish, tracks, vehicles, modes, saves, stability and performance. Fix real blockers from evidence.
6. Create the PC/Dreamcast/N64 comparison matrix and verify each important gameplay/system claim against documentation or a lawful local run of the relevant edition.
7. Implement missing original-game systems and content until a faithful playable baseline exists.
8. Only after that baseline is stable, work on improved graphics, bonus content, new modes and quality-of-life improvements.

## Owner-only actions

- To use the optional Gemini GitHub agent, create a free Gemini API key and add it as the repository secret `GEMINI_API_KEY`. Do not enable billing. See [AI automation setup](AI_AUTOMATION_SETUP.md).
- To test interactively without local installs, create a Codespace on `audit/step102-import-gate`; stop/delete it afterward to respect free quotas. See [cloud guide](CLOUD_DEV_WORKFLOW.md).
- For Dolphin runtime proof, a person must open/download the artifact and run it in Dolphin on an appropriate environment. The automated compile cannot substitute for this visual check.

## Free-only policy

Do not add a payment method, enable billing, or use paid APIs. Free-tier quotas can change; stop if a quota is unavailable or exhausted.
