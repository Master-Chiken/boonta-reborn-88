# Next milestone: verify an interactive GameCube racing slice

Last updated: 2026-10-15

## Current mainline baseline

The active native target is the clean-room, original procedural prototype in gamecube-demo/. It is not the full game and does not contain commercial game code or extracted assets.

Verified in GitHub Actions:
- Host regression tests cover speed input, boost energy, steering inertia, lap boundaries and three-lap finish state, rival collision/overtake decisions, off-road drag, rail recovery, pause/reset behavior, and build-artifact utilities.
- devkitPPC/libogc produces a non-empty GameCube DOL and ELF, and the artifact validator passes.
- Dolphin remains active for the bounded 12-second null-video process smoke.
- The Software Renderer capture in run #69 shows a visible procedural road, edge rails, center markers, player pod and rival pod.

Those results establish deterministic code tests, a native build, bounded emulator startup, and a visible CI scene. They do not yet establish correct live controller input, a fully completed three-lap race, sustained frame pacing, or behavior on physical GameCube/Wii hardware.

## Immediate milestone: interactive controller and race acceptance

Load the latest mainline DOL in a visible Dolphin session. Record the Dolphin version, renderer/backend, video mode, controller profile, and a short video or screenshots plus any runtime log. Test in this order:

1. Reset with Y. Check that the pod returns to the starting lateral position, speed and lap count reset, the rival and overtake indicators reset, boost refills, and pause/finish state clears.
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

## Parallel track: Step 102 source import remains on hold

The fuller Step 102 source archive is separate from the clean-room mainline code. Do not merge draft PR #17 or #22 wholesale. The available evidence does not resolve file-by-file source authorship/license, the generated centerline header whose presence contradicts the archive README, or the origin of demo track CSV data. Keep unclear-provenance source and all commercial game payloads/assets out of the public repository until permission and derivation are documented. Build success and passing tests do not resolve licensing.

## PC research to guide faithful behavior

Use the pinned SW_RACER_RE research snapshot as a source of questions and behavior observations, not as portable GameCube code. Track each finding in the behavior matrix, distinguish observed PC facts from GameCube/N64 hypotheses, and implement independently unless a deliberate license review clears code reuse. Keep route geometry, extracted assets, ROMs and disc images out unless provenance and redistribution rights are established.

## Next technical improvements after the interactive run

- Add regression tests for any bug found during the controller session before changing behavior.
- Validate input/steering, off-road/rail response, rival interactions and finish/reset together in deterministic host tests where practical.
- Improve the procedural track, camera and collision model as a cohesive vertical slice; preserve a clean CI build and visible-render diagnostic with every change.
- Only then expand race systems, presentation, assets and bonus content.