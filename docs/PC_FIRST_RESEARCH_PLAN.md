# PC-first research and reuse plan

## Decision

The original Windows PC release of *Star Wars: Episode I Racer* (1999) is the primary behavioral and systems reference for Boonta Reborn. Existing public reverse-engineering, modding, asset-format and reimplementation work must be audited before writing replacement systems from scratch.

This plan does **not** assume that PC code can be compiled for GameCube/Wii. The PC version is the primary source for understanding the game; the selected console target still needs a separate renderer, platform layer, memory budget and input implementation.

## Public projects to audit first

| Priority | Project | What it contributes | How Boonta Reborn should use it | Caveat |
|---|---|---|---|---|
| P0 | [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | PC executable reverse engineering, function hooks, symbols, type information, Ghidra scripts and a separate HD replacement-renderer effort | Map game systems and function relationships; identify handling, race flow, AI, track loading, assets and renderer boundaries; keep a dated map of verified vs inferred behavior | Its stated goal is to document/reimplement some functions, not fully decompile or matching-compile the game. Its code and assets require license/provenance review before reuse |
| P0 | [SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods) | PC asset unpack/repack tools, texture packs and track mods | Learn the data pipeline and how existing modders validate round-trips; use only tools/files whose license and origin are cleared | Modded game assets and track data are not automatically redistributable |
| P0 | [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) | Parsers/extractors for spline, sprite, texture and save/string data; GPL-2.0-or-later | Use as a format reference and test candidate workflows against a user-supplied lawful local game installation | Tools may emit copyrighted assets; do not commit extracted game content to the public repository |
| P1 | [swe1r-assets](https://github.com/akopetsch/swe1r-assets) | MIT-licensed C# library for reading, editing and writing model/spline/sprite/texture blocks | Evaluate as a useful format/round-trip reference; document exact supported blocks and test results | MIT applies to the library, not to original game assets |
| P1 | [Sw_Racer](https://github.com/Olganix/Sw_Racer) | Additional file-format and extraction research | Compare parser assumptions and file structures with other tools | Review the exact license file and dependency terms before copying code |
| P1 | [OpenSWE1R](https://github.com/OpenSWE1R/openswe1r) | Earlier open-source PC port approach using a Windows API subset and x86 emulation | Study architecture, portability decisions and known gaps; mine issues/history for lessons | Project is marked deprecated and still depends on the original executable/assets; not a ready-made GameCube/Wii port |
| P1 | [OpenSWE1R/swe1r-re](https://github.com/OpenSWE1R/swe1r-re) | Earlier PC function documentation and analysis | Cross-check names, behavior hypotheses and binary-version assumptions | Older, partial documentation; distinguish hypotheses from verified semantics |
| P2 | [swe1r-patcher](https://github.com/JayFoxRox/swe1r-patcher) | Runtime patches and debug/modding behavior | Use for research leads about existing functions and compatibility | Its repository states restrictive redistribution/non-commercial terms; do not copy its code/assets into Boonta Reborn without explicit permission |
| P2 | [PCVR fork](https://github.com/GameOrDie007/Star-Wars-Episode-I-Racer-PCVR) | Renderer-hook work based on SW_RACER_RE | Review only for rendering-hook concepts and any upstream changes not present in the main repository | A fork is not automatically more authoritative than upstream; review license and diff |

## Research workflow

1. **Record provenance first.** For every external repository, save URL, commit SHA, retrieval date, declared license, submodule/dependency licenses, and whether any game-derived binary/assets are present.
2. **Use PC as the systems reference.** Build a subsystem index for: boot/configuration, menus, race progression, player handling/physics, boost/heat, collisions, rival AI, track/spline loading, vehicle parameters, camera, HUD, audio, saves, multiplayer and unlocks.
3. **Separate evidence levels.** Mark every finding CONFIRMED-IN-CODE, CONFIRMED-IN-RUN, DOCUMENTED, INFERRED, or UNKNOWN. Record executable version/hash when a finding depends on a binary.
4. **Validate against the actual game when possible.** Use a lawful local installation owned by the user. Capture input/output observations and compare PC behavior with console versions. Do not upload the executable, disc image, ROM, BIOS or extracted proprietary assets.
5. **Extract formats without publishing copyrighted output.** Keep local-only test fixtures private. Public CI should use synthetic fixtures or independently authored data unless redistribution rights are explicit.
6. **Prefer reusable tools over copied data.** When a tool is permissively licensed, consider using it as a separate dependency or adapting its documented format. Respect GPL obligations if code is reused; do not assume a tool's license grants rights to the game's assets.
7. **Only then port the systems.** Reimplement verified behavior in portable code, with a console-specific renderer and platform layer. Keep PC-only APIs/hooks out of the native GameCube/Wii build.

## First concrete deliverables

- A PC subsystem/function map linked to source paths and symbol/function addresses where publicly documented.
- An asset-format matrix: block type, parser/tool, read/write support, test status, and whether output must remain local-only.
- A gameplay comparison checklist for PC vs Dreamcast vs N64 vs GameCube/Wii.
- A legal/provenance register for all code and content considered for import.
- A prioritized port backlog, with handling/physics, track loading and race progression ahead of cosmetic additions.

## Non-negotiable boundaries

- Do not commit game executables, ROMs, disc images, BIOS files, extracted proprietary models/textures/audio, or unclear mod-derived track geometry.
- Do not treat “open source”, “public GitHub repository”, or a tool's license as permission to redistribute the original game or its assets.
- Do not describe an existing partial decompilation as a complete source port.
- Do not merge the Step 102 candidate or external code into main until provenance and runtime checks are resolved.
- Keep all work within the project's free-only constraint: no paid APIs, no billing, no paid CI services.
