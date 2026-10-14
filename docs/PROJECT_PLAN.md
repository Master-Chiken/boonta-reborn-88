# Project plan

## Objective

Investigate a realistic path toward an enhanced Star Wars: Episode I — Racer experience on GameCube and Wii, without assuming that PC reverse-engineering work is directly portable to those consoles.

## Guiding decisions

1. **Audit before implementation.** Check the prototype archive, its provenance, source code, dependencies, licenses, and existing build scripts before trusting or importing it.
2. **Use a small proof of concept.** First prove the chosen toolchain and target environment with a minimal homebrew executable; do not start by promising a full remaster.
3. **Keep two tracks distinct.**
   - Track A: quick baseline using existing N64 emulation on Wii/Cube-compatible homebrew, if compatible with the user's own game copy.
   - Track B: native port or reimplementation for GameCube/Wii, which requires separate engine, asset-format, input, audio, graphics, storage, and performance work.
4. **Test evidence matters.** Record exact versions, commands, expected outputs, and actual results. Never label a build as working without a build/test result.
5. **Keep copyrighted game content out of the public repository.** No ROMs, disc images, extracted proprietary assets, or copied code of unclear origin.

## Phases and acceptance criteria

### Phase 0 — Repository and prototype audit
- [x] Create public repository with README, .gitignore, and license.
- [x] Add initial project plan, research notes, and build guide.
- [ ] Inspect the existing prototype archive without modifying the only copy.
- [ ] Identify language, source files, dependencies, licenses, and target platform.
- [ ] Decide whether any part is safe and useful to import.

**Exit criterion:** a file inventory and a concise assessment that distinguishes verified contents from assumptions.

### Phase 1 — Select the technical baseline
- [ ] Confirm what executable/source material actually exists.
- [ ] Compare a Wii N64-emulator baseline with a native homebrew baseline.
- [ ] Establish the exact development toolchain and a minimal build procedure.
- [ ] Review relevant third-party licenses before reusing code or tooling.

**Exit criterion:** a documented architecture decision based on inspected files and a reproducible minimal build.

### Phase 2 — First bootable test
- [ ] Create the smallest homebrew test that can be launched on the selected target or emulator.
- [ ] Record target, hardware/emulator version, build command, and result.
- [ ] Keep generated binaries and images out of Git; attach only lawful logs or screenshots if needed.

**Exit criterion:** a reproducible test with documented evidence. A test app is not a game port.

### Phase 3 — Feasibility of the game
- [ ] Identify which game version and data formats are being studied.
- [ ] Verify whether PC-oriented asset tools can parse any relevant console-format data; do not assume they can.
- [ ] Map high-level subsystems: rendering, track geometry, vehicles/physics, controls, audio, menus, save data, and resource loading.
- [ ] Estimate what must be reimplemented versus what could be reused lawfully.

**Exit criterion:** subsystem inventory and an evidence-backed feasibility assessment.

### Phase 4 — Vertical slice
Only after a viable architecture is selected:
- [ ] Load one small test scene or track.
- [ ] Display one vehicle and accept basic input.
- [ ] Test stable frame timing and memory use.
- [ ] Document known limitations before expanding scope.

**Exit criterion:** a repeatable, narrowly scoped playable slice.

### Phase 5 — Enhanced presentation and bonus features
Potential later work, only once the base is stable:
- improved textures/materials and rendering;
- optional visual effects and quality settings;
- additional time trials, unlockables, or challenge modes;
- per-platform configuration and packaging.

Every feature must have a defined implementation and test plan. “HD” should be specified precisely (render resolution, assets, filtering, or emulator upscaling) rather than used as a vague label.

### Phase 6 — Packaging and release
- [ ] Build and validate each platform target separately.
- [ ] Determine whether a homebrew executable, installable app, or disc image is appropriate.
- [ ] Treat Wii WBFS packaging and GameCube image packaging as separate tasks.
- [ ] Test output in an emulator and, where available, on real hardware.
- [ ] Publish only original code and material that the project is allowed to redistribute.

## Definition of done for each task

A task is complete only when:
- the changed files are committed;
- the toolchain/command and target are recorded;
- build/test results are reported truthfully;
- third-party code/assets have provenance and license notes;
- generated game images and copyrighted game content remain outside this repository.
