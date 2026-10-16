# Next milestone: verify an interactive GameCube racing slice

Last updated: 2026-10-16

## Current mainline baseline

The active native target is the clean-room, original procedural prototype in gamecube-demo/. It is not the full game and does not contain commercial game code or extracted assets.

Verified in GitHub Actions:
- Host regression tests cover speed input, boost/overheat, steering inertia, analog/D-pad mapping, lap boundaries and three-lap finish state, three-rival spacing and rival collision/overtake decisions, off-road drag, rail recovery, pause/reset behavior, finite-state guards, and build-artifact utilities.
- A cadence regression verifies consistent one-second outcomes at 60 and 50 gameplay updates per second; long frame deltas are capped at 50 ms for physics/state updates.
- devkitPPC/libogc produces a non-empty GameCube DOL and ELF, and the artifact validator passes.
- Dolphin remains active for the bounded 12-second null-video process smoke.
- The Software Renderer capture in run #69 shows a visible procedural road, edge rails, center markers, player pod and rival pod.

Those results establish deterministic code tests, a native build, bounded emulator startup, and a visible CI scene. They do not yet establish correct live controller input, a fully completed three-lap race, sustained frame pacing, or behavior on physical GameCube/Wii hardware.

## Additional acceptance evidence on PR #157 (not yet mainline)

On 2026-10-16, GitHub Actions run [#38891767425](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38891767425) tested the `feature/runtime-track-spline` head `e0e9d54382992a2394df05ba919a06485355a602`. The native DOL/ELF build, host gameplay/pause tests, artifact validation, and Dolphin process smoke passed. The software-renderer job also passed the deterministic left/right steering comparison and the scripted full-race diagnostic: after 12,000 controller polls with throttle held and steering neutral, the captured visible Dolphin frame was recognized as showing the three-lap finish banner.

This is evidence of automated race progression and a visible finish state on the PR branch. It is **not yet a mainline result**, and the scripted DTM is not a substitute for a person controlling the game live. Manual stick/D-pad, braking, boost, pause/resume, reset/restart, sustained frame pacing, and physical GameCube/Wii behavior remain pending. The software-renderer job is marked non-blocking in CI, so retain the artifact/log evidence and re-check the exact head before merge.

## Immediate milestone: interactive controller and race acceptance

Load the latest mainline DOL in a visible Dolphin session. Record the Dolphin version, renderer/backend, video mode, controller profile, and a short video or screenshots plus any runtime log. Test in this order:

1. Reset with Y. Check that the pod returns to the starting lateral position, speed and lap count reset, the three rivals and overtake indicators reset, boost refills, and pause/finish state clears.
2. Hold A, then B. Confirm acceleration and braking visibly change speed. Release A/B and confirm speed falls naturally rather than remaining stuck.
3. Steer left and right with the Control Stick; repeat with the D-pad. Confirm movement direction is correct, motion has the programmed inertia, releasing input damps the drift, and the steering remains bounded.
4. Drive beyond the road edge. Confirm off-road speed loss and rail-edge recovery are visible and do not freeze or destabilize rendering.
5. Hold X + A to boost. Confirm energy drains while active and recharges after release.
6. Press Start while moving. Confirm the pause icon appears and simulation freezes; press Start again and confirm it resumes. Press Y while paused and confirm a clean reset/unpause.
7. Complete three counted lap crossings. Confirm the three HUD markers advance consistently, the finish flag appears, and movement stops after the configured race limit. Press Y and confirm another run can begin.
8. Let the scene run for a longer session. Look for graphics corruption, crashes, and severe frame pacing problems.

Mark each item pass/fail with the exact evidence. A screenshot alone is not proof of controller input; a headless process smoke is not proof of visible rendering. A successful compiler run is not proof of a complete race.

### Acceptance criteria

- The visible scene starts without a fatal/boot error.
- Steering, acceleration, braking, boost, pause/resume, and reset behave as described.
- A three-lap run reaches the finish and stops; reset starts a fresh run.
- No sustained render corruption or crash appears during the longer session.
- CI host tests and native build pass on the exact code being tested.
- Any unverified item remains marked pending; do not infer hardware compatibility from Dolphin.

## Step 102 source/provenance evidence

The import hold is documented in the [source-import gate](SOURCE_IMPORT_GATE.md), [bundle audit](STEP102_BUNDLE_AUDIT.md), [host validation record](STEP102_HOST_VALIDATION.md), and [source provenance review](STEP102_SOURCE_PROVENANCE.md). These reports describe a separate archive and historical host checks only. They do **not** clear files for redistribution or provide a native build result for Step 102.

## Parallel track: Step 102 source import remains on hold

The fuller Step 102 source archive is separate from the clean-room mainline code. Do not merge draft PR #17 or #22 wholesale. The available evidence does not resolve file-by-file source authorship/license, the generated centerline header whose presence contradicts the archive README, or the origin of demo track CSV data. Keep unclear-provenance source and all commercial game payloads/assets out of the public repository until permission and derivation are documented. Build success and passing tests do not resolve licensing.

## PC research to guide faithful behavior

Use the pinned SW_RACER_RE research snapshot as a source of questions and behavior observations, not as portable GameCube code. Track each finding in the behavior matrix, distinguish observed PC facts from GameCube/N64 hypotheses, and implement independently unless a deliberate license review clears code reuse. Keep route geometry, extracted assets, ROMs and disc images out unless provenance and redistribution rights are established.

## Next technical improvements after the interactive run

- Add regression tests for any bug found during the controller session before changing behavior.
- Validate input/steering, off-road/rail response, rival interactions and finish/reset together in deterministic host tests where practical.
- Improve the procedural track, camera and collision model as a cohesive vertical slice; preserve a clean CI build and visible-render diagnostic with every change.
- Only then expand race systems, presentation, assets and bonus content.