# Boonta Reborn — reverse-engineering-first work plan

You are working on a GameCube/Wii-native racing prototype inspired by Star Wars Episode I: Racer. Do not reinvent mechanics already investigated in the PC decompilation project.

## Required workflow for gameplay changes
1. Search `tim-tim707/SW_RACER_RE` before implementing any race, pod, handling, boost/heat, track traversal, HUD, save, ranking or unlock feature.
2. Read the relevant PC source, type definitions and `data_symbols.syms`; distinguish confirmed implementation from comments/hypotheses and TODO/HANG stubs.
3. Record the PC function/variable, observed behaviour, confidence, and corresponding Step 102 module.
4. Compare the finding against Step 102 and reuse its existing module where possible. Implement only missing behaviour.
5. Add deterministic host tests for the behaviour and edge cases.
6. Keep PC Windows/DirectX ABI, addresses and DLL hooks out of the native GameCube build unless independently redesigned for libogc.
7. Do not import commercial game assets, ROM/disc images, extracted proprietary payloads or route datasets without explicit redistribution clearance.

## Initial priority areas
- Pod physics: turn response/rate, acceleration curve, coasting, air brake, hover height.
- Boost: thrust, heat drain/cooling, failure threshold and timing.
- Race timing: delta-time clamping and stable behaviour at varying frame rates.
- Results: finish ordering, unfinished-racer ranking and progression/unlock flags.
- Track traversal: spline/segment progression, checkpoints, off-track recovery and collision.
- HUD: speed/heat/boost feedback, minimap positioning and race-state indicators.

Use `docs/PC_REVERSE_ENGINEERING_FINDINGS.md` as the starting research map. Do not treat it as a substitute for reading the relevant source before changing code.
