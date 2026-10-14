# Next milestone: runtime-test the clean-room GameCube driving prototype

## Current confirmed progress

- The separate clean-room C prototype in `gamecube/source/main.c` now builds into a non-empty `boonta_demo.dol` through GitHub Actions.
- The prototype draws a procedural ring track, pylons, finish marker, original low-poly pod, chase camera, and HUD, with acceleration, braking, boost/heat, lateral movement, pause/reset, and a three-lap finish state implemented in code.
- The latest confirmed native cross-build is the [GameCube prototype workflow](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-smoke.yml).
- Repository safety and CodeQL have also passed on a recent branch revision.
- **Not verified yet:** booting the DOL, graphics, controller input, complete race behavior, or performance in Dolphin/console.
- The Step 102 source archive remains outside the repo pending its separate code/asset provenance review.

## Latest gameplay increment — deterministic rival lane movement

The clean-room race logic now gives each of the three procedural rivals a smooth, bounded lane sway. The motion is deterministic (no random-number state), keeps rivals in their original lane order, and remains within the track's lateral limits. This is a small gameplay improvement, not original-game AI or a substitute for interactive playtesting.

A new host test checks that rival lane movement is bounded, smooth between frames, repeatable for identical inputs, and does not let rivals cross lanes. The expected host test output is now `race_logic_test: 11 suites passed`. Confirm the GitHub Actions result before treating the change as validated.

## Work sequence

1. Keep the build/safety/static-analysis checks green.
2. Download the `boonta-gamecube-demo-dol` artifact from the Actions run while it is retained (seven days) and test it in Dolphin.
3. Record whether it boots, whether the image is rendered, and whether the controller responds. Do not infer gameplay success from a successful compile.
4. Prepare a path-by-path source import manifest for Step 102; classify original code candidates, tests/tools/docs, and files that must be held for provenance/license review.
5. Confirm whether the user-authored/source archive code can be redistributed under the intended project license. Keep PC mod centerlines, uncertain sample audio/models, ROMs, and extracted commercial files excluded.
6. Import only the cleared source files on a separate review branch; run host tests and build the real prototype.
7. Extend the first vertical slice based on observed runtime issues, not guesses.

## Owner-only actions

- To use the optional Gemini GitHub agent, create a free Gemini API key and add it as the repository secret `GEMINI_API_KEY`. Do not enable billing. See [AI automation setup](AI_AUTOMATION_SETUP.md).
- To test interactively without local installs, create a Codespace on `audit/step102-import-gate`; stop/delete it afterward to respect free quotas. See [cloud guide](CLOUD_DEV_WORKFLOW.md).
- For Dolphin runtime proof, a person must open/download the artifact and run it in Dolphin on an appropriate environment. The automated compile cannot substitute for this visual check.

## Free-only policy

Do not add a payment method, enable billing, or use paid APIs. Free-tier quotas can change; stop if a quota is unavailable or exhausted.
