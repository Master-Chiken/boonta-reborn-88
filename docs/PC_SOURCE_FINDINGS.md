# PC source findings — first code-level pass

Reviewed: 2026-10-14

## Source snapshot

- Main reverse-engineering project: https://github.com/tim-tim707/SW_RACER_RE
- Reviewed source snapshot for the links below: commit prefix a9863edd4caa (the repository's live default branch may move; re-check before relying on addresses).
- Project README explicitly says its goal is to document and re-implement some original functions for modding; it is not a full decompilation or matching build.
- PC HD replacement rendering is a separate DirectInput hook. It is useful evidence for where the original renderer can be replaced, but it is not a native console rendering layer.

## Findings confirmed in the public source

| Area | Evidence in source | What this tells us | Confidence / next check |
|---|---|---|---|
| Spline loading and file layout | [swrSpline.c](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caa/src/Swr/swrSpline.c) — swrSpline_LoadSpline at original PC address 0x00446fc0 | The loader reads a spline block, validates an index against the block count, reads offset bounds, byte-swaps fields, and resolves the in-memory control-point array. This is concrete evidence that track spline data is a first-class runtime structure, not just a visual centerline. | CONFIRMED-IN-CODE. Verify the full struct definitions and file bounds/endianness against parser implementations and synthetic fixtures. |
| Spline cursor and traversal | [swrSpline.h](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caa/src/Swr/swrSpline.h) documents cursor primitives, control-point lookup, interpolation, cursor stepping/evaluation/seeking and track-length/progress-table functions. | A faithful port needs a spline graph/cursor abstraction, not only a list of track vertices. Alternate branches, tangent/orientation and progress are important. | DOCUMENTED / CONFIRMED-IN-CODE declarations. Read implementations and verify runtime semantics before porting. |
| Spline progress and baked geometry | swrSpline.h lists swrSpline_BakeSampleTrackMesh, swrSpline_TraceProgress, swrSpline_BuildProgressTable, swrSpline_CollectNearbyPoints and track-length accessors. | The original code appears to derive a progress representation and sampled track mesh from spline data. This gives us an initial investigation sequence for lap progress, terrain following and nearby-track queries. | CONFIRMED-IN-CODE declarations; detailed behavior requires implementation review. |
| Vehicle ground contact | swrRace.h and the associated race/physics sources expose ground-contact and vertical-motion integration, track spline interaction, and collision query functions. | Vehicle physics and track geometry are coupled. Recreating only steering/speed values will not reproduce terrain following and impacts. | CONFIRMED-IN-CODE declarations/comments; verify exact equations and update order. |
| Vehicle state and progress | [types.h](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caa/src/types.h) contains fields such as lap progress, spline track-mesh caches, track offset, vehicle-bump timer and respawn invincibility timer. | The original state model includes more than position and velocity; it tracks progress, terrain cache and collision/respawn state. | CONFIRMED-IN-CODE. Map each field to the update function that writes/reads it. |
| Rival roles | [types_enums.h](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caa/src/types_enums.h) distinguishes AI and simplified-AI flags. | AI behavior may have more than one execution path; a single generic lane-following behavior is not enough evidence of fidelity. | CONFIRMED-IN-CODE flag definitions; behavior differences still need tracing. |
| Menus and progression surfaces | [swrRace.h](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caa/src/Swr/swrRace.h) declares main menu, vehicle selection, course selection/info, results, parts shop, upgrades, repair/parts health and save-generation functions. | The scope of a faithful game includes the tournament/economy/upgrade loop, not just a race scene. | CONFIRMED-IN-CODE declarations; test flows in PC runtime. |
| PC replacement renderer boundary | [SW_RACER_RE README](https://github.com/tim-tim707/SW_RACER_RE) and [release notes](https://github.com/tim-tim707/SW_RACER_RE/releases) describe a DirectInput hook and replacement models/fonts/custom tracks. | Community work already tackles HD assets on PC by intercepting the existing executable. The console port needs its own graphics backend and cannot simply reuse the Windows hook. | DOCUMENTED. Compare hook-specific changes against the original function map. |

## Important caution about apparent decompilation

The source is a mixture of original-function hooks, reconstructed logic, declarations, comments and stubs. For example, the public types.h excerpt documents spline projection slots whose retail projection stub is said to always return zero. A stub or commented hypothesis is not proof of how a replacement implementation should behave. Trace the call sites and distinguish original retail behavior from new helper code before copying semantics.

## Immediate source-inspection backlog

1. Read the full spline control-point and spline struct definitions in src/types.h; record field sizes, endianness, pointers vs on-disk offsets, and all unknown fields.
2. Trace the implementations and call sites for spline cursor stepping, track progress, swrRace_UpdateRaceProgress, ground contact, track-mesh lookup and respawn/reset.
3. Trace vehicle physics update order: input → engine/throttle/boost/heat → steering/lateral motion → terrain contact → collision → damage/repair → HUD/results.
4. Identify AI update entry points and compare normal AI with simplified AI; record route branch selection and any difficulty adjustments.
5. Trace course selection → race initialization → lap progression → finish/results → save/unlock updates.
6. Use the Blender add-on and parser libraries as independent cross-checks for file layout; do not assume a PC block can be loaded unchanged by the GameCube/Wii runtime.
7. Turn each verified behavior into a host-side regression test before implementing its console equivalent.

## Porting consequence

The next engineering milestone should be a portable, testable spline/track representation and race-state model based on verified PC semantics. The existing procedural console demo is not a substitute for these systems. No original game data or extracted commercial assets should be committed as test fixtures.
