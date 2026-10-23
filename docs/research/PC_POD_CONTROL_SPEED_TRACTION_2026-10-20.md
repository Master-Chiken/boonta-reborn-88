# PC pod control, speed and traction — 2026-10-20

## Question

How does the pinned PC reverse-engineering source separate player input, target steering, forward speed and traction, and which parts differ from the current Boonta GameCube prototype?

**Evidence class:** STATIC-ANALYZED PC source plus static inspection of the Boonta prototype. Not a retail runtime measurement. No conclusion about N64, Dreamcast, GameCube retail or Wii behavior is implied.

## Pinned source

Repository: [tim-tim707/SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab)  
Commit: `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`  
License: AGPL-3.0; reference only pending an explicit license decision.

Key routines:
- [`swrRace_UpdatePlayerControl`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c) — gathers configured analog/digital input and commits throttle, target turn rate, pitch/tilt and control flags. Its source comment identifies a preserved retail bug: the analog pitch low clamp writes +0.8 instead of -0.8.
- [`swrRace_CalcTargetTurnRate`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c) — dispatches local input, remote state or AI autopilot; runs catch-up for racers in the racing state; applies AI proximity force; scales and clamps target turn rate by `paceMultiplier` and pod `maxTurnRate`.
- [`swrRace_UpdateSpeed`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c) — integrates throttle into `accelThrust`, applies acceleration/deceleration and air-brake factors, maps that state through pod acceleration/max-speed stats, then applies speed multiplier, surface factor/bonus and a minimum speed on a specific surface state.
- [`swrRace_ApplyTraction`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c) — updates velocity direction by blending desired velocity with the previous velocity using a grip-derived traction factor; surface grip, pod anti-skid, slide state and pace multiplier affect the blend.
- [`PodHandlingData` / race state types](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/types.h) — separates pod stats, target/current turn state, velocity direction and surface state.

## Behavior inferred from source

### Input and steering are separate stages

The local control routine first gathers configured inputs. A later target-turn routine dispatches according to racer type (local, remote, AI), applies AI proximity behavior when applicable, and clamps the target turn rate. Therefore a single scalar “steering input” is not the entire steering model: control mapping, target turn rate, pod turn-rate limits and the later motion update are separate responsibilities.

### Forward speed is a stateful curve, not a direct button-to-speed assignment

The PC speed routine integrates throttle into `accelThrust`; its acceleration factor changes during boost / boost-start. Near-zero throttle uses a deceleration path, reverse/braking input has separate logic, and air brakes apply another deceleration factor. The resulting state is mapped through each pod's acceleration and maximum-speed parameters, then adjusted for speed multiplier and surface effects.

### Traction changes the velocity direction

The PC traction routine forms a desired velocity from the supplied direction and magnitude, derives a traction factor from `antiSkid × surfaceGripFactor × slide2`, and blends desired velocity with the previous `velocityDir`. It then normalizes the blended direction and reapplies the desired magnitude. This is a stateful direction/velocity model, not just a fixed lateral damping coefficient.

### Catch-up interacts with handling

The PC code also scales target turn rate by `paceMultiplier`; the separate AI dossier describes how AI pacing changes that multiplier. This coupling means speed balancing and steering limits should not be researched as wholly independent systems.

## Comparison with current Boonta prototype

In the inspected [`gamecube-demo/source/main.c`](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/gamecube-demo/source/main.c), the current target uses a smaller, explicit arcade-style state:

- acceleration/braking updates a scalar `g_speed`;
- steering is converted to a scalar command, modified by pitch;
- `boonta_lateral_velocity_after_steering_slide_scaled` introduces lateral inertia and slide behavior;
- lateral position integrates that velocity and is clamped to a fixed range;
- off-road and rail helpers adjust speed/position;
- track distance advances using speed, boost and pitch.

The source paths therefore differ: the PC reconstruction has pod-stat-driven forward acceleration and a 3D velocity-direction traction blend, while the prototype uses a scalar speed and lateral-velocity model. This is an architecture comparison, not a verdict that the prototype is wrong. The current demo is a synthetic test environment, and the console implementation has not been mapped.

## Cross-platform evidence status

| Version | What this pass establishes | Status |
|---|---|---|
| Windows PC | Function responsibilities and key state flow in the pinned public RE source. | STATIC-ANALYZED; no runtime measurement in this dossier. |
| N64 | No same-scenario source or runtime trace collected. | UNKNOWN. |
| Dreamcast | No same-scenario source or runtime trace collected. | UNKNOWN. |
| GameCube / Wii retail | Original console internals not inspected. | UNKNOWN. |
| Boonta GameCube prototype | Input → scalar speed/lateral motion path inspected. | TARGET SOURCE INSPECTED; not yet accepted against retail behavior. |

Official retrospective material says the game was valued for responsive controls and engine overheating, but does not document the internal equations: https://www.starwars.com/news/star-wars-episode-i-racer-legacy

## Minimal comparison experiment

When identified original builds and lawful runtime access are available, run the same track and pod with the same upgrade state, difficulty, control sensitivity and boost state:

1. Hold full throttle on a straight and record speed over fixed time intervals.
2. Release throttle, then apply air brake; record deceleration curves.
3. Apply a fixed steering input at low and high speed; record heading/lateral response and recovery after release.
4. Repeat with slide/drift input and on two surfaces with different grip.
5. Repeat on PC, N64 and Dreamcast, noting build/region, hardware or emulator, frame rate and capture method.

Video can show broad response but cannot prove the source-level formulas. Avoid claiming exact numerical parity without reliable state measurements. Do not put proprietary executables, ROMs, disc images or extracted game assets in the public repository.

## Decision

**Do not change Boonta physics from this comparison alone.** The next useful step is to identify a reproducible observable symptom or fidelity requirement, then measure it against identified original releases. Keep PC formulas as hypotheses/reference until console behavior is checked; do not copy AGPL implementation code.
