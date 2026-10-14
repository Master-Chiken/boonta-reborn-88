# Step 102 vs. PC decompilation: physics comparison

**Scope:** this review compares the recovered Step 102 source-only bundle with the public `SW_RACER_RE` PC research tree. It is a source-level comparison, not a claim of original-game numerical equivalence. The Step 102 source remains on the review branch/workspace until its import is completed.

## What the Step 102 code currently does

Inspected files: `source/racer_physics.c`, `source/racer_physics.h`, `source/vehicle_catalog.c`, and `tests/test_racer_physics.c`.

- Clamps physics `dt` to `[0, 0.05]` seconds and rejects invalid/short tracks.
- Uses a data-driven `RacerVehicleSpec` with top speed, direct acceleration, steering, grip, boost power, heat/cooling rates, drift charge, damage resistance and display color.
- Boost is allowed when boost input and energy are positive, heat is below 100, and the racer is not overheated. Active boost consumes 24 energy units/sec at full input and adds heat using the selected pod's `boost_heat_rate`.
- On overheat, heat is clamped to 100 and boost is disabled. Cooling subtracts `boost_cooling_rate * dt`; overheat clears at heat <= 42. Energy recovers at 2.4 units/sec while not boosting.
- Acceleration is a direct positive multiplier of throttle, reduced by damage and a speed-ratio curve. Drag combines a base term, speed-dependent drag, rolling resistance, off-road severity and extra drag for heavy damage.
- Boost raises the speed ceiling to 116% of the damage-adjusted normal top speed. When boost ends, excess speed bleeds off progressively rather than snapping immediately to the normal cap.
- Steering is speed-dependent and modified by vehicle steering/grip, surface grip, damage, off-road severity and drift state. Drift creates a slip angle and charges boost energy.
- The current 23-entry vehicle catalogue is explicitly described in source comments as gameplay-balancing presets, not recovered original handling values.

## Field-by-field mapping

| PC decompilation lead | Step 102 counterpart | Assessment / next action |
|---|---|---|
| `turnResponse` | Steering-rate formula in `racer_update_vehicle_surface_width` | **Partial conceptual match.** Step 102 has a speed-dependent response curve, but no separate turn-response parameter. Keep the formula; add tests for response over speed and compare behaviour once a reference capture is available. |
| `maxTurnRate` | `RacerVehicleSpec.steering` and computed `steering_rate` | **Not equivalent yet.** The current scalar is not an explicit angular-rate cap. Add a separately tunable cap only if PC observations or source analysis support its behaviour. |
| `acceleration` (PC type comment says speed-curve denominator; lower is faster) | `RacerVehicleSpec.acceleration` (direct acceleration multiplier; higher is faster) | **Opposite parameter semantics.** Never copy PC numeric values into the Step 102 field. Translate through measured acceleration curves or an explicit conversion model. |
| `airBrakeInv` | `RacerInput.brake`, fixed `34.0f * brake` deceleration | **Gap.** There is no pod-specific air-brake parameter in this update path. Determine whether the PC variable affects air-braking or general velocity decay before implementing a counterpart. |
| `deceleration_interval` | Base/speed drag and rolling resistance | **No direct mapping.** Step 102 uses a continuous drag formula. Compare coast-down curves before changing it. |
| `boost_thrust` | `RacerVehicleSpec.boost_power` | **Conceptual match only.** Step 102 adds boost power to acceleration and applies a speed-ratio factor; verify units and response shape independently. |
| `heatRate`, `coolRate` | `boost_heat_rate`, `boost_cooling_rate` | **Sign convention differs, state model is analogous.** PC notes describe a variable that decreases while boosting and increases when cooling; Step 102 stores heat that rises while boosting and falls while cooling. Do not compare raw gauge values without converting conventions. |
| `hoverHeight` | Track-height projection / pod model | **Needs separate review.** It is not a direct field in the horizontal physics state. Inspect vertical placement and track banking in `pod_model.c` before claiming parity. |
| `repairRate` | Damage state and race-item / repair behaviour | **Needs separate review.** Current physics reduces performance as damage rises, but this does not prove that the PC pit-droid repair mechanic is reproduced. |

## Important interpretation of heat

The Step 102 field is named `boost_heat`: 0 is cool, 100 is overheated, and the hysteresis release threshold is 42. The PC research notes describe a different gauge convention (a “coolness” value that falls during boosting). This is a representation difference, not evidence that one implementation's signs are wrong. A parity comparison should convert both to a common normalized heat value before comparing duration-to-overheat and cooldown time.

## Existing regression coverage

The recovered `tests/test_racer_physics.c` already checks acceleration/braking/steering, drift charging and slip recovery, boost energy, overheat/cooling, temporary over-speed and smooth release, damage penalties, lap crossing and road-edge penalties. Those tests protect the Step 102 model; they do **not** by themselves prove parity with the original PC game.

## Next evidence-driven tasks

1. Import the project-authored Step 102 source and host tests to the repository branch, excluding the archive cache and any uncleared derived assets/data.
2. Add parameterized tests for acceleration and coast-down curves across multiple pods; record output values so later reference captures can be compared.
3. Add tests for time-to-overheat and cooldown hysteresis at several `dt` values, including the 0.05 s clamp.
4. Inspect the exact PC source statements and symbols for the named parameters, then record each observed equation and confidence level. Do not infer an equation solely from a variable name.
5. Build with devkitPPC/libogc and test in Dolphin before describing any of these systems as a working GameCube game.

## References

- PC type definitions: https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/types.h
- PC race implementation: https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/Swr/swrRace.c
- Step 102 recovered source bundle inventory and import boundaries: `docs/STEP102_IMPORT_GATE.md`
