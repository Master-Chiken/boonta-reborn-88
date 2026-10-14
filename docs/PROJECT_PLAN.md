# Project plan

## Objective

Reconstruct *Star Wars: Episode I — Racer* as faithfully as possible, using existing PC reverse-engineering work and comparative study of the PC, Dreamcast, and Nintendo 64 editions, then deliver an enhanced, genuinely playable native GameCube/Wii version with improved graphics and bonus content. This is a staged engineering project; the full reconstruction is not yet available.

## Confirmed inputs and findings

- The source archive `Star_Wars_Racer_GameCube_Step102.zip` has been inspected.
- It contains C source modules, a GameCube Makefile, tests, research tools, documentation, and prototype assets.
- The archive describes a source prototype with 25 course entries, 23 vehicle/pod presets and variants, physics, rival AI, items, race modes, UI, and progression scaffolding.
- Its host release suite passed in a temporary environment: host shell checks and 91 Python unit tests passed. This does not establish a native cross-build.
- The archive itself says the real devkitPPC/libogc `.dol` build and Dolphin/console runtime test are still pending.
- The source archive has not yet been imported into this GitHub repository. The existing native workflow checks for the source tree and fails early until it is present.
- The Dreamcast/KallistiOS starter is a separate experiment, not the main target.

## Guiding decisions

1. **Use the right source of truth.** Treat the Step 102 GameCube/Wii prototype as the strongest existing port candidate, and use the PC, Dreamcast and Nintendo 64 editions plus documented PC reverse-engineering research as comparison/reference inputs. The small `gamecube/` procedural demo is only a toolchain/learning slice, not the final foundation.
2. **Audit before publishing.** Check code provenance, license compatibility, asset rights, and generated data before importing files into a public repository.
3. **Cloud-first build.** Prefer GitHub Actions/devkitPro containers to avoid requiring local toolchain installation or large downloads on the user's computer.
4. **Test evidence matters.** Record exact commands and results. Never label a host test as a native build or a successful compile as a working game.
5. **Keep copyrighted content out of the public repository.** No ROMs, disc images, BIOS files, or unclear extracted commercial payloads.

## Phases and acceptance criteria

### Phase 0 — Prototype audit
- [x] Create public repository and initial documentation.
- [x] Inspect the Step 102 source archive.
- [x] Identify source modules, build scripts, tests, target, and limitations.
- [ ] Create a path-by-path source import manifest for the Step 102 archive.
- [ ] Finish code/license/provenance review of external dependencies, generated route data, sample model/material files and audio.
- [ ] Select the exact source/assets subset safe to publish.

**Exit criterion:** a reviewed source-only import list and clear provenance notes.

### Phase 1 — Import and automated host tests
- [ ] Import cleared GameCube/Wii source, headers, Makefile, tests, tools, and build docs.
- [ ] Run host checks in GitHub Actions.
- [ ] Fix CI failures without disabling or weakening tests.

**Exit criterion:** the source tree exists in GitHub and the host test suite passes in CI.

### Phase 2 — Clean-room prototype build
- [x] Add original procedural 3D ring-track/pod driving prototype in `gamecube/`.
- [x] Build a non-empty `boonta_demo.dol` using devkitPPC/libogc in GitHub Actions.
- [x] Add repository safety CI and CodeQL static analysis; recent branch runs passed.
- [ ] Test the DOL in Dolphin and record actual boot/render/input results.

**Exit criterion:** a repeatable build plus a recorded runtime boot/input test. Compile success alone is not runtime proof.

### Phase 3 — Import and test the full Step 102 source prototype
- [ ] Prepare a path-by-path import manifest and complete provenance review.
- [ ] Import only source, tests, tools, and documentation whose redistribution is approved; exclude uncleared assets and derived PC mod data.
- [ ] Run host regression tests in CI.
- [ ] Build the full native source prototype.

**Exit criterion:** reviewed source tree exists in GitHub and its actual host/native build checks run in CI.

### Phase 4 — First runtime validation
- [ ] Run the DOL in Dolphin or on suitable hardware.
- [ ] Record whether it boots, draws a frame, reads controller input, and starts a race.
- [ ] Fix the first runtime blocker.

**Exit criterion:** a repeatable boot and input test. Compilation alone is not sufficient.

### Phase 5 — Faithful original-game vertical slice
- [ ] Load one course with a consistent route, visible road, and collision.
- [ ] Control one pod with a follow camera.
- [ ] Validate acceleration, braking, steering, collision, lap timing, and frame pacing.
- [ ] Record memory and performance limits.

**Exit criterion:** a short repeatable playable race on the target environment.

### Phase 6 — Improve and expand beyond the original
Only after the faithful gameplay baseline is stable:
- improve original/cleared textures, materials, lighting, and effects;
- add course-specific scenery and additional vehicles;
- finish audio, progression, and bonus features;
- measure performance on GameCube and Wii separately.

Define what “HD” means for each target before promising it: native console resolution, replacement assets, rendering changes, or emulator upscaling are different outcomes.

### Phase 7 — Packaging
- [ ] Build and validate GameCube and Wii targets separately.
- [ ] Determine lawful homebrew executable and packaging formats.
- [ ] Validate any image conversion separately; a DOL build does not automatically produce a valid NKit ISO or WBFS.
- [ ] Publish only code and assets that can be redistributed.

## Required version-comparison matrix

Maintain a living matrix for PC, Dreamcast and Nintendo 64, with the GameCube/Wii target as the implementation column. Track at least: physics and handling, acceleration/boost/heat/damage, vehicle statistics, rival AI, track layout and route data, pickups/hazards, race modes, menus/HUD, progression/save behavior, audio, graphics/resource formats, and platform limitations. Each row must identify its evidence source and confidence (confirmed by execution, documented by a source, inferred, or unknown). Do not silently treat PC data as console data.

## Definition of done for each task

- Changed files are committed in a reviewable branch/PR.
- Relevant tests and toolchain versions are recorded.
- Build and runtime results are reported truthfully.
- Third-party code/assets have provenance and license notes.
- ROMs, disc images, BIOS files, and uncleared commercial payloads remain outside the repository.
