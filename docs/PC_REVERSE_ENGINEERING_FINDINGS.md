# PC reverse-engineering findings to guide the GameCube/Wii port

**Purpose:** convert existing PC decompilation research into actionable, platform-neutral implementation tasks for Boonta Reborn. This document is a research map, not a claim that the PC code can be compiled on GameCube.

## Primary research source

- Project: https://github.com/tim-tim707/SW_RACER_RE
- Its README reports 71.2% of functions analysed as of 12 June 2026 (1,518 / 2,132). “Analysed” does not mean every function is complete or matching-compiled.
- The repository's current source of truth is `data_symbols.syms` and `src/generated/hook_generated.c`; `src/types.h` contains reconstructed types. The project uses Ghidra and x32dbg, and its `dinput_hook` is a separate PC DLL injection/rendering mod.
- Treat its PC-address-specific hooks, Windows/DirectX types and ABI as research-only for the native GameCube target. Review its AGPL-3.0 license and third-party dependencies before copying any code.

## Concrete findings to carry into our own engine

### Pod handling / physics

The PC source's `src/types.h` identifies a pod-stats structure with these named tuning variables:
- `turnResponse`: how quickly steering approaches the target turn rate.
- `maxTurnRate`: cap on turn rate.
- `acceleration`: documented as a speed-curve denominator; lower values accelerate faster.
- `airBrakeInv`: air-brake decay parameter; lower values mean stronger braking.
- `deceleration_interval`: coasting deceleration parameter.
- `boost_thrust`: boost force.
- `heatRate` and `coolRate`: boost heat/cooling rates.
- `hoverHeight`: ride height above the track.
- `repairRate`: pit-droid repair rate.

These names and comments are strong leads for our own parameter model. Do not assume their numeric values or units map directly to the Step 102 model without inspecting both implementations.

### Boost and heat

In the PC `src/Swr/swrRace.c`, the analysed update path decreases `engineTemp` by `deltaTime * heatRate` while boosting and increases it by `deltaTime * coolRate` when not boosting. A separate PC-mod note describes the gauge as a 0–100 “coolness” value, where reaching zero causes engine failure. That is a concrete behavioural hypothesis to test against the original PC game and then reproduce independently in our port.

### Frame timing

The symbol data identifies `swrRace_minDeltaTimeSecs`, `swrRace_maxDeltaTimeSecs` and `swrRace_msToSecondsScale`. The PC race update also uses `swrRace_deltaTimeSecs` for movement-related state updates. This suggests our GameCube update should use a controlled delta-time path and clamp unusually large frame intervals rather than letting boost, heat or steering vary with frame rate. The exact original clamp values should be read from the corresponding implementation before matching them.

### Race results and unlock progression

The symbol annotations identify:
- `swrObjJdge_maxRaceTime`: baseline time used to rank unfinished racers.
- `swrRace_favPilotUnlockMask`: per-pilot “beaten their track” bits.
- `swrRace_unlockedPilotsMask`: persistent unlock mask used when loading content and changed by an unlock-all cheat.
- `swrObjJdge_minimapAnchorX`: HUD/minimap layout anchor.

These are useful leads for matching finish-order handling, rival ranking, pilot unlock progression and HUD positioning. They are names/annotations from the PC research, not proof that the same memory layout or bitmask can be copied.

## Next implementation plan

1. Compare Step 102's pod physics source against these PC findings field by field.
2. Create a mapping table: PC variable/function → observed behaviour → Step 102 field/function → confidence/test.
3. Add deterministic host tests for acceleration convergence, coasting, steering response, boost heat drain/cooling, engine failure threshold, frame-time clamping and finish-order ranking.
4. Implement only missing behaviours in Step 102, using independent GameCube-friendly C and fixed/controlled time-step logic where appropriate.
5. Inspect PC source and symbol annotations for save/progression and course/spline traversal before implementing those systems anew.
6. Keep a citation and license/provenance note for each research source; do not copy PC hooks, proprietary game assets, ROM data or uncleared extracted track datasets.

## Evidence links

- PC pod-stat type definitions: https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/types.h
- PC race update / heat and coasting logic: https://github.com/tim-tim707/SW_RACER_RE/blob/master/src/Swr/swrRace.c
- PC reconstructed global symbols: https://github.com/tim-tim707/SW_RACER_RE/blob/master/data_symbols.syms
- Project scope and progress: https://github.com/tim-tim707/SW_RACER_RE/blob/master/README.md
