# PC-first technical map and external research

Updated: 2026-10-14

## Purpose

Use the original Windows PC release as the main behavioral reference and mine existing community work before implementing a parallel system. This document is a research map, not a claim that a complete source port already exists.

## High-value external sources

| Source | Verified contribution | Immediate use | Status / caution |
|---|---|---|---|
| [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | Reverse-engineering project with data_symbols.syms, generated hooks, Ghidra scripts, function/type information and a separate DirectInput/HD replacement-renderer project. README says 1,518 of 2,132 functions analysed on 2026-06-12 (71.2%); analysed does not mean fully reimplemented. | Primary code map. Inspect track/spline functions, race progression, vehicle update, input, collision, camera, scene graph and renderer entry points. Pin the exact upstream commit used for each finding. | Research reference first; do not blindly copy source/assets. License and every bundled asset still need review. |
| [SW_RACER_RE releases](https://github.com/tim-tim707/SW_RACER_RE/releases) | PC mod release notes describe a dinput.dll hook, GLTF replacement models, HD fonts, custom tracks and controller support. | Learn the practical interface between the original executable and replacement renderer; identify naming conventions and track replacement workflow. | Windows PC injection architecture is not a native GameCube/Wii renderer. Treat it as design evidence, not portable code. |
| [swe1r-assets](https://github.com/akopetsch/swe1r-assets) | MIT C# library deserializes, modifies and serializes out_modelblock.bin, out_splineblock.bin, out_spriteblock.bin, and out_textureblock.bin, with bit-perfect reserialization when unchanged. | Best initial candidate for round-trip tests of file-format hypotheses; compare with other parsers. | Library license does not license the game data. Use synthetic fixtures publicly; original files remain local unless rights are cleared. |
| [blender-swe1r](https://github.com/OpenSWE1R/blender-swe1r) | Blender import/export add-on. Documentation describes track splines as controlling lap progression, start/finish, spawn/respawn, minimap, guide arrow, Zero-G mode and AI pathing; alternate spline paths can branch and rejoin the main loop. | Use its documented semantics to define a track/spline subsystem and a checklist of required data; validate on a locally owned PC installation. | Do not import the add-on or its dependencies into the console build before license/dependency review. Exported tracks may contain copyrighted geometry. |
| [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) | GPL-2.0-or-later parsers/extractors for spline, sprite, texture and save/string data; N64 modelblock decompression utility. | Cross-check block layouts and parsing assumptions; use save parser documentation to specify a clean-room save format only if needed. | GPL obligations apply to copied/derivative code; extracted content is a separate copyright question. |
| [SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods) | Unpack/repack scripts and texture/track modifications; docs for the model block and examples of altered track geometry. | Study round-trip process and modder test cases. | Treat mod-derived track data and distributed assets as held pending provenance/permission review. |
| [Sw_Racer](https://github.com/Olganix/Sw_Racer) | Earlier C/C++ tooling to understand and extract the original game's binary formats. | Compare older format assumptions against newer parser implementations. | Review License.txt and dependencies before any code reuse. |
| [OpenSWE1R/openswe1r](https://github.com/OpenSWE1R/openswe1r) | Earlier GPL-2.0 cross-platform approach combining an x86 CPU emulator and a subset of Windows API while relying on the original executable for unimplemented functions. | Study portability boundaries and failure modes. | Marked deprecated; not a native GameCube/Wii port and not a complete clean-room replacement. |
| [OpenSWE1R/swe1r-re](https://github.com/OpenSWE1R/swe1r-re) | Earlier function analysis based on a specific Windows patch executable hash. | Search for function descriptions that newer symbol databases or code still lack. | Older, partial and version-specific; verify against the binary version being studied. |
| [PCGamingWiki](https://www.pcgamingwiki.com/wiki/Star_Wars%3A_Episode_I_-_Racer) | Documents PC configuration files, input/configuration locations and save paths. | Use for practical install/runtime test setup and configuration/save inventory. | Community-maintained reference; verify claims on the target version. |
| [Save editor](https://github.com/jcfieldsdev/ep1-racer-save-editor) | GPL-3.0 Windows save editor; credits swe1r-tools for save-format information. | Supplement save-file research if progression persistence becomes a priority. | Not a game engine or gameplay implementation; review GPL terms before code reuse. |
| [PCVR fork](https://github.com/GameOrDie007/Star-Wars-Episode-I-Racer-PCVR) | PCVR work based on SW_RACER_RE with stereo rendering, head tracking and OpenXR controls. | Inspect renderer hook changes and compare with upstream to avoid duplicating already solved PC-side render research. | Fork status does not imply upstream acceptance or portable implementation. |

## PC subsystem map: what to investigate first

Rank work by its impact on fidelity and on a later console port. Do not start with HD models.

| Subsystem | Questions to answer from PC code/docs/runtime | Candidate evidence | Port implication |
|---|---|---|---|
| Track data and spline graph | How are main/alternate paths represented? How are checkpoints, lap progress, respawn, minimap and AI routes derived? | out_splineblock.bin; Blender add-on docs; reverse-engineered track functions | Define a documented, platform-neutral track schema and a converter; keep original extracted data private until cleared. |
| Vehicle handling | How are throttle, braking, steering, grip, lateral drift, airborne/Zero-G behavior and speed limits updated? What is frame/time dependence? | SW_RACER_RE function map; controlled PC gameplay observations | Create deterministic portable physics tests before rendering work. |
| Boost, heat and damage | Activation rules, energy/heat rates, cooldown, repair, collision penalties and HUD feedback | PC functions and repeated controlled runs | Test numeric behavior independently from console input/rendering. |
| Rival AI | Path following, overtaking, alternate routes, rubber-banding, collisions and difficulty differences | Spline data, AI functions, recorded races | Build an AI model around original behavior, not the demo's lane-sway rivals. |
| Race flow and progression | Race start, countdown, laps, finish conditions, rankings, unlocks, tournament state and restart | Executable functions, config/save documentation, PCGamingWiki | Define state machine and regression tests before porting menus. |
| Rendering and scene graph | Visibility, transforms, materials, lighting, effects, animation, skybox, HUD and camera | SW_RACER_RE symbols/hooks and HD replacement-renderer notes | Separate gameplay transforms from console-specific rendering; use a native renderer rather than PC DirectX/DirectInput hooks. |
| Asset formats | Model/sprite/texture/spline blocks, compression, indexing, references, endianness and round-trip integrity | swe1r-assets, blender-swe1r, swe1r-tools, Sw_Racer | Build synthetic-fixture parsers and validate bounds; do not publish extracted proprietary data. |
| Audio and presentation | Sound events, positional audio, music transitions, announcer, menus and localization | file-format tools and PC runtime observations | Recreate behavior with cleared or independently created assets. |
| Input/configuration/save | Key/controller mapping, calibration, config .cfg/.map, save schema and version compatibility | PCGamingWiki, save editor, SW_RACER_RE | Write a platform-neutral input/action layer and a documented save format; avoid carrying over PC-specific assumptions. |

## Evidence protocol

For each finding, create an entry with: subsystem, claim, source URL, repository commit or document version, function/file/address, PC executable version/hash if relevant, evidence level, reproduction steps, confidence, and console-port implications.

Use exactly these evidence levels:

- CONFIRMED-IN-CODE: directly supported by identified source or reverse-engineered function.
- CONFIRMED-IN-RUN: reproduced in a lawful local PC game installation, with build/version and steps recorded.
- DOCUMENTED: stated by a community document but not independently tested.
- INFERRED: plausible interpretation that still needs validation.
- UNKNOWN: not yet established.

Never treat a symbol name, comment, guessed decompilation or a function being analysed as proof of its exact runtime semantics.

## Fastest practical workflow

1. Pin the current upstream commit of SW_RACER_RE and review README, NOTES, symbol database, generated hooks, track-related code and the DirectInput hook's renderer boundary.
2. Read the Blender add-on's spline documentation and build a list of all track fields and behaviors it claims to represent.
3. Compare swe1r-assets, swe1r-tools and Sw_Racer on the four block families. Start with synthetic files and bit-perfect no-op round trips, then private local-game fixtures if available.
4. Create a PC-versus-console comparison checklist for one track, one podracer, a full three-lap race, alternate routes, a collision, boost/heat, finish results and persistence.
5. Implement the first portable, testable core from verified behavior: track/spline representation, race state/progression, then handling and AI. Keep rendering behind an interface.
6. Run the core tests on the host before building the console executable. Test actual Dolphin rendering/input separately; a successful DOL build or a running emulator process is not proof of playability.
7. Only after a faithful vertical slice works, evaluate improved assets, lighting/effects and extra modes.

## Public repository and legal boundaries

- The original PC executable, disc images, ROMs, BIOS files and extracted commercial assets must not be committed.
- The license for a parser/library is not the license for the game's assets or a third-party mod's derived data.
- For every candidate code dependency, record the exact commit, license, transitive dependencies, required notices and whether copyleft obligations would affect distribution.
- Keep PC-mod-derived centerlines, models, textures, sounds and unreviewed generated files on HOLD until origin and permission are documented.
- If legal clearance is not possible, use public format knowledge to write a clean-room implementation and synthetic/independently authored test data.
- The PC reference is primary for behavior; it is not automatically the best codebase to compile for GameCube/Wii. PC hooks, x86 assumptions, DirectX/Windows dependencies and large PC assets need separate treatment.

## Next implementation gate

Do not expand the procedural console demo. First deliver the PC subsystem/function map and block-format comparison, then select one minimal faithful gameplay slice to reproduce and test. Keep the current branch isolated and do not merge unreviewed source into main.