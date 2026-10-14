# Project plan

## Objective

Build toward a playable enhanced racing prototype inspired by *Star Wars: Episode I — Racer*, with native GameCube/Wii homebrew as the primary target. This is a staged engineering project, not a claim that a full remaster is already available.

## Confirmed inputs and findings

- The source archive `Star_Wars_Racer_GameCube_Step102.zip` has been inspected.
- It contains C source modules, a GameCube Makefile, tests, research tools, documentation, and prototype assets.
- The archive describes a source prototype with 25 course entries, 23 vehicle/pod presets and variants, physics, rival AI, items, race modes, UI, and progression scaffolding.
- Its host release suite passed in a temporary environment: host shell checks and 91 Python unit tests passed. This does not establish a native cross-build.
- The archive itself says the real devkitPPC/libogc `.dol` build and Dolphin/console runtime test are still pending.
- The source archive has not yet been imported into this GitHub repository. The existing native workflow checks for the source tree and fails early until it is present.
- The Dreamcast/KallistiOS starter is a separate experiment, not the main target.

## Guiding decisions

1. **Use the right source of truth.** Work from the Step 102 GameCube/Wii prototype, not from the Dreamcast smoke-test branch.
2. **Audit before publishing.** Check code provenance, license compatibility, asset rights, and generated data before importing files into a public repository.
3. **Cloud-first build.** Prefer GitHub Actions/devkitPro containers to avoid requiring local toolchain installation or large downloads on the user's computer.
4. **Test evidence matters.** Record exact commands and results. Never label a host test as a native build or a successful compile as a working game.
5. **Keep copyrighted content out of the public repository.** No ROMs, disc images, BIOS files, or unclear extracted commercial payloads.
6. **Use PC reverse engineering as evidence, not as console source code.** Prioritize SW_RACER_RE for PC behavior research, then map findings to Step 102 and explicitly test any GameCube/Wii differences. Its upstream code is AGPL-3.0; do not copy or adapt it into this repository unless license compatibility and resulting obligations are deliberately reviewed.

## Phases and acceptance criteria

### Phase 0 — Prototype audit
- [x] Create public repository and initial documentation.
- [x] Inspect the Step 102 source archive.
- [x] Identify source modules, build scripts, tests, target, and limitations.
- [ ] Create a path-by-path source import manifest for the Step 102 archive.
- [ ] Finish code/license/provenance review of external dependencies, generated route data, sample model/material files and audio.
- [ ] Select the exact source/assets subset safe to publish.
- [ ] Establish a behavior-reference matrix linking SW_RACER_RE research to Step 102 modules/tests for race/laps, pod physics/control, and spline/track format.
- [ ] Keep verified PC behavior separate from unverified GameCube/Wii assumptions.

**Exit criterion:** a reviewed source-only import list, clear provenance notes, and an evidence-linked reference matrix for the first gameplay slice.

### Phase 1 — Import and automated host tests
- [ ] Import cleared GameCube/Wii source, headers, Makefile, tests, tools, and build docs.
- [ ] Run host checks in GitHub Actions.
- [ ] Fix CI failures without disabling or weakening tests.

**Exit criterion:** the source tree exists in GitHub and the host test suite passes in CI.

### Phase 2 — First native build
- [ ] Build with devkitPPC/libogc in GitHub Actions.
- [ ] Archive the DOL/ELF and compiler log.
- [ ] Fix actual cross-compiler errors.

**Exit criterion:** a non-empty `swe1r_gc_port.dol` is produced by the native toolchain.

### Phase 3 — First runtime validation
- [ ] Run the DOL in Dolphin or on suitable hardware.
- [ ] Record whether it boots, draws a frame, reads controller input, and starts a race.
- [ ] Fix the first runtime blocker.

**Exit criterion:** a repeatable boot and input test. Compilation alone is not sufficient.

### Phase 4 — Playable vertical slice
- [ ] Load one course with a consistent route, visible road, and collision.
- [ ] Control one pod with a follow camera.
- [ ] Validate acceleration, braking, steering, collision, lap timing, and frame pacing.
- [ ] Record memory and performance limits.

**Exit criterion:** a short repeatable playable race on the target environment.

### Phase 5 — Expand and enhance
Only after the vertical slice is stable:
- improve original/cleared textures, materials, lighting, and effects;
- add course-specific scenery and additional vehicles;
- finish audio, progression, and bonus features;
- measure performance on GameCube and Wii separately.

Define what “HD” means for each target before promising it: native console resolution, replacement assets, rendering changes, or emulator upscaling are different outcomes.

### Phase 6 — Packaging
- [ ] Build and validate GameCube and Wii targets separately.
- [ ] Determine lawful homebrew executable and packaging formats.
- [ ] Validate any image conversion separately; a DOL build does not automatically produce a valid NKit ISO or WBFS.
- [ ] Publish only code and assets that can be redistributed.

## Priority reverse-engineering reference

SW_RACER_RE is a Tier 1 research source for the PC version, not the GameCube source of truth. Start with race/lap behavior, pod physics and input, and route/spline formats. Maintain citations to the exact upstream file/commit, note confidence and platform, map findings to Step 102 code/tests, then write independent console-target code. See [SW_RACER_RE study plan](SW_RACER_RE_STUDY_PLAN.md).

## Definition of done for each task

- Changed files are committed in a reviewable branch/PR.
- Relevant tests and toolchain versions are recorded.
- Build and runtime results are reported truthfully.
- Third-party code/assets have provenance and license notes.
- ROMs, disc images, BIOS files, and uncleared commercial payloads remain outside the repository.
