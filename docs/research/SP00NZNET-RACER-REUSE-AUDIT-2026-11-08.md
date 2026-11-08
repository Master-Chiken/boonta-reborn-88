# sp00nznet/racer — reuse and transfer audit

**Reviewed:** 2026-11-08  
**Pinned upstream snapshot:** [sp00nznet/racer at 694c5663b3a7c30e2862fc240344f34683f99a9c](https://github.com/sp00nznet/racer/tree/694c5663b3a7c30e2862fc240344f34683f99a9c)  
**Upstream default branch:** the latest commit checked on 2026-11-08 is still 694c5663b3a7c30e2862fc240344f34683f99a9c (2026-10-30). The inspected recursive tree contains 88 entries, including directories.

## Executive decision

**Use this repository as a high-value N64 behaviour/runtime reference and local reverse-engineering toolbox. Do not treat it as a GameCube/Wii engine or source-code donor.**

The upstream README identifies the project as a **static recompilation** of the N64 release using N64Recomp. It does not claim to be a clean source decompilation. The recompiled C output is generated from the user's ROM and is deliberately not tracked. The public tree includes a host runtime bridge, frontend, build/configuration files and analysis utilities, but not the original Racer game logic as a portable C source implementation.

The target differences are decisive:

| Project | Target CPU / graphics path | Meaning for Boonta |
|---|---|---|
| sp00nznet/racer | N64 MIPS III -> native PC code; N64ModernRuntime and RT64 | Excellent N64 behaviour and analysis reference |
| Boonta GameCube/Wii | Gekko/Broadway PowerPC + GX through libogc | Requires an independent native console implementation |

MIPS instructions, N64 RSP microcode, N64 AI/VI/SI/PI interfaces, N64 DMA and RT64 display-list processing cannot be compiled into or substituted for the GameCube GX runtime. Similar system names (VI, AI, controller, audio) do not mean the hardware APIs or data layouts are interchangeable.

## What the upstream project reports

The pinned README's own status table and changelog report progress through boot, title/tournament setup and a driveable Boonta Training Course race. It also reports controller handling, EEPROM saves, audio, high-resolution RT64 rendering, a desktop launcher and menu, texture-pack support, and a local two-player deterministic-lockstep netplay path. These are **upstream author status statements**, not results independently run by Boonta.

Useful behaviour leads for Boonta are therefore:
- lifecycle coverage: boot, title, player/vehicle selection, shop/tournament setup, in-race pause/menu, restart/finish paths;
- input coverage: analog stick, digital directions, throttle/brake/boost, button rebinding, deadzone and controller disconnect/reconnect;
- presentation coverage: HUD/race scene, menus, 4:3 presentation and frame pacing;
- audio coverage: music/effects, volume, sound-buffer back-pressure and deterministic timing;
- race coverage: two-player split-screen, tournament flow, saves, race reset and end-of-race transitions.

These are **feature checklists and observed reference points**, not license grants or proof that N64 structures/behaviour match GameCube/Wii. Cross-platform findings must be validated separately.

## What was imported or adapted into Boonta

All additions live under `tools/n64_reference/`, preserve the upstream MIT notice in `LICENSE.sp00nznet`, operate on files supplied explicitly by the user, and have synthetic-only tests:

| Boonta helper | Upstream idea | Improvement / intended saving |
|---|---|---|
| `mips_function_inspector.py` | `tools/func_differ.py` | Section-relative ROM/VRAM map; z64/v64/n64 normalization; ROM-bound checks; partial MIPS III output with unsupported words left raw |
| `mips_symbol_scanner.py` | `tools/rom_analyzer.py` prologue scan | Explicit ROM/VRAM/code-size range; no guessed fixed code end; clearly provisional function boundaries |
| `mips_callgraph.py` | Call-graph pass in `tools/libultra_identify.py` | Correct JAL target region from PC+4; exact symbol-start matching; separate unresolved/ambiguous targets and indirect JALR sites |
| `mips_string_scanner.py` | `tools/string_dumper.py` | Explicit scan bounds, three N64 byte orders, categorization hints, stdout-only local output |
| `mips_os_candidates.py` | COP0/MMIO/FPU analysis in `tools/libultra_identify.py` and `tools/identify_libultra.py` | Reports instruction evidence and candidate tags; does not rename functions or claim an OS API from weak heuristics |
| `mips_symbol_progress.py` | `tools/progress.py` symbol coverage report | Counts named/automatic symbols, mapped bytes, size buckets and largest auto-named candidates; explicitly does not claim semantic completion |

The combined synthetic test coverage for these six helpers is 28 tests. They validate parsing, bounds, byte orders, selected instructions, graph edges, unresolved/indirect calls, string categorization and OS/hardware evidence tags. They do **not** validate a retail ROM or prove Racer compatibility.

## What was reviewed and deliberately not copied

| Upstream component | Decision | Reason |
|---|---|---|
| `symbols.toml` | **Reference-only; not copied** | Generated ROM-analysis metadata tied to a particular N64 revision; use a local map supplied by the owner or generated from their own ROM |
| `recomp.toml`, `rsp/aspMain.toml` | **Not copied** | N64Recomp/RSP configuration and address-space assumptions |
| `src/section_table.cpp` | **Not copied** | Generated N64 section/function table derived from the symbol map |
| `src/main.cpp` | **Not copied** | N64 static-recomp host runtime bridge, not a game-independent GX implementation |
| `RecompiledFuncs/` and other generated output | **Never import** | Generated from a commercial ROM; upstream license expressly excludes it |
| `frontend/src/input.cpp`, `config.cpp`, `audio.cpp`, `ui.cpp`, `netplay.cpp`, `rt64_context.cpp` | **Pattern reference only** | SDL, ImGui, RT64, desktop configuration, N64 input/AI callbacks and PC lockstep architecture; not a libogc/GX frontend |
| `tools/fix_fallthroughs.py`, `fix_statics.py`, `auto_stub.py`, `post_recomp_patches.py` | **Not adapted** | Patch N64Recomp-generated C files or N64Recomp configuration; no equivalent generated-code directory in Boonta |
| `tools/gen_lookup_table.py` | **Not adapted** | Emits N64Recomp's section table and requires its generated headers |
| `tools/find_rom.py` and setup/install scripts | **Not adapted** | Hard-coded to a specific USA N64 ROM identity and N64/PC toolchain installation |
| `docs/screenshots/*` | **Reference only** | Depict original-game content; do not use as Boonta art, textures or assets |
| `CMakeLists.txt`, `Makefile`, Docker and Android build files | **Not copied** | Build N64Recomp/N64ModernRuntime/RT64 host executables, not the GameCube/Wii devkitPPC/libogc application |

The upstream README says its MIT grant applies to the repository's own tools/runtime/build/documentation, but not to the commercial game or code generated from a user's ROM. This audit therefore does not copy the generated C, ROM, N64 symbol file, game assets, RSP output, or source-derived runtime output.

## How this should speed up the next research pass

For an owner-local N64 reference investigation:

1. Obtain a symbol map for the exact local ROM revision. The upstream symbol file can be inspected separately as a reference, but is not embedded in Boonta and its names are not treated as verified truth.
2. Run the string scanner to list likely menu strings, file names, debug labels and race terminology.
3. Run the call-graph tool to find caller clusters, shared helpers, unresolved direct targets and indirect-call sites.
4. Run the OS-candidate analyser to identify likely libultra/MMIO support routines so they are not confused with Racer-specific gameplay.
5. Use the symbol-progress report to prioritize the largest still-auto-named routines for manual inspection; treat all resulting ratios as name/byte metrics only.
6. Inspect only promising functions with the MIPS inspector and record the exact address, instructions, callers/callees, data references, counter-evidence and confidence.
7. Write a behavioural specification independently. Validate N64-only claims against N64 observations, then validate any proposed GameCube/Wii behaviour on its own platform.

This reduces time spent manually locating functions and separating OS support from game-specific code. It does **not** remove the need to implement Boonta's race engine, rendering, input, audio, UI, asset pipeline or course systems.

## Exact upstream references

- [Pinned README and progress/status](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/README.md)
- [Pinned MIT LICENSE and scope exclusion](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/LICENSE)
- [MIPS function disassembler](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/tools/func_differ.py)
- [ROM prologue/string analysis](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/tools/rom_analyzer.py)
- [libultra/call-graph analysis](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/tools/libultra_identify.py)
- [N64 frontend input handling](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/frontend/src/input.cpp)
- [N64 audio queue and back-pressure](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/frontend/src/audio.cpp)
- [RT64 overlay integration](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/frontend/src/ui.cpp)

**Disposition:** selected local-analysis ideas adapted; no upstream game code or asset imported; no actual N64 ROM was inspected in CI; no GameCube/Wii compatibility claim made.
