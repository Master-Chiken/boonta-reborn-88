# Technical research notes

These notes summarize public starting points. They are not proof that any project or asset format works with the GameCube or Wii edition.

## Existing Star Wars: Episode I — Racer research

### SW_RACER_RE
Repository: https://github.com/tim-tim707/SW_RACER_RE

The project documents and reimplements selected functions from the **Windows** version to support research and modding. Its README reported 71.2% of analyzed functions on 12 June 2026. That figure is a dated status from the upstream project, not a measure of console-port completion. It is not a complete decompilation and is not itself a GameCube/Wii port.

**Potential use:** learn game logic, symbols, resource handling, and research methodology. Before reusing any code, inspect the current license and file-level provenance, and confirm whether it is suitable for this project's intended license and targets.

For a pinned, evidence-based subsystem review, see the [SW_RACER_RE study plan](SW_RACER_RE_STUDY_PLAN.md) and [PC-to-console behavior matrix](SW_RACER_RE_BEHAVIOR_MATRIX.md). They record a reviewed upstream commit and keep PC observations separate from console hypotheses; they do not clear upstream code or asset reuse.

### OpenSWE1R
Repository: https://github.com/OpenSWE1R/openswe1r

An earlier open-source reimplementation/port focused on the Windows PC version. Its documented stack includes OpenGL, SDL2, OpenAL, C/C++-adjacent tooling, and Unicorn Engine. The project notes that original game art assets are still needed. Its repository is GPL-2.0.

**Potential use:** reference for engine architecture and subsystem separation. It is not evidence of a ready-to-build console version. Reusing GPL code could affect the licensing obligations of a derivative distribution and must be reviewed before any copy or port.

### SWE1R asset tooling
- https://github.com/akopetsch/swe1r-assets
- https://github.com/louriccia/SWE1R-Mods
- https://github.com/OpenSWE1R/swe1r-tools

These projects document or manipulate specific PC game asset blocks, including model, spline, sprite, and texture data. For example, the swe1r-assets library states that it can deserialize, modify, and reserialize certain block files with bit-perfect reserialization when unchanged.

**Critical caveat:** tooling documented for PC install files may not parse GameCube or N64 assets. We must inspect file signatures and formats from a legally obtained console copy before deciding whether to adapt these tools. The tools' own licenses and dependencies also need checking.

## Quick-play baseline: Wii64 / Cube64

Repository: https://github.com/emukidid/Wii64

Wii64/Cube64 is an N64 emulator/homebrew project whose README describes .z64, .v64, and .n64 ROM input. This gives us a possible low-effort route to check whether the N64 edition can run in a Wii homebrew environment.

- This route emulates the N64 version; it is not a native GameCube/Wii port.
- Compatibility and speed for this particular game must be tested, not assumed.
- It does not by itself add HD assets, bonuses, or a modern renderer.
- The upstream project declares GPL v2 and places restrictions on use of its branding; review those terms before redistribution or making a modified build.

A compatible N64 ROM must remain a local user-provided test input. Do not place ROMs or disc images in this repository.

## Platform and packaging implications

- GameCube and Wii targets are different build targets even though Wii can run GameCube software. A Wii .wbfs image is not a way to turn a GameCube executable into a Wii-native application.
- First prove a simple executable can build and launch in the chosen homebrew environment. Only then select final packaging.
- A GameCube ISO/image workflow and a Wii WBFS workflow should be documented and validated separately. Do not promise that a particular custom homebrew image can be converted to an NKit image until the toolchain is tested.
- HD requires a precise definition. Original console output limits, replacement assets, enhanced rendering, and emulator upscaling are different strategies and should not be described as interchangeable.

## Open questions to resolve

1. What is inside the existing Step102 prototype archive, and what is its source/license?
2. Is that archive source code, a prebuilt executable, documentation, or a mixture?
3. Which target should be used for the first build: Wii homebrew, GameCube homebrew, or a PC research build?
4. Is the quickest goal simply to run the original N64 version, or is a native enhanced port the non-negotiable destination?
5. Which assets/data formats are actually present in the relevant console version?
6. Which open-source components can be used without incompatible license or branding obligations?
