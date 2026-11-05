# GameCube/Wii reverse-engineering toolchain and reuse audit

**Audit date:** 2026-11-03  
**Repository baseline:** `Master-Chiken/boonta-reborn-88` main `26f6d9c3dc3535902d5043bd0883eef8db8e9334`  
**Purpose:** Identify existing public tools and research that can shorten the path to a complete, evidence-led Boonta Reborn implementation. This is a tool/reference audit, not approval to copy any third-party game code or assets.

## Owner priority

The immediate objective is to understand and reconstruct the original game’s systems before spending time polishing the current procedural demo or requesting human gameplay acceptance.

Target allocation: approximately 80% reverse-engineering, source/tool/format research and system mapping; 20% focused clean-room implementation and integration. Keep only short automated compile/unit/provenance checks as development guardrails. Defer human Dolphin acceptance and physical Wii/controller acceptance until a substantially complete playable slice exists and the owner explicitly resumes acceptance.

The current `gamecube-demo/` is a technical scaffold, not the intended final game. Do not treat a green build or a successful three-lap test as the main deliverable for this phase.

## Executive decision

**Use a GameCube/Wii-native reverse-engineering chain as the primary technical path.** The highest-value combination discovered in this audit is:

1. **decomp-toolkit (dtk)** for disc/DOL/REL inspection, extraction, splitting, relocation/function-boundary analysis, and initial project configuration.
2. **Ghidra GameCube Loader with the Gekko/Broadway language extension** for DOL/REL/apploader loading and correct GameCube/Wii PowerPC paired-single disassembly/decompilation.
3. **powerpc-rs** as a lightweight independent Gekko/Broadway instruction decoder/assembler reference.
4. **objdiff** for comparing PowerPC object files and tracking matching progress if/when a matching decompilation is practical.
5. **dtk-template** as the project-structure reference for per-version configs, symbols, splits, build hashes, ignored original files and automated reporting.
6. **Gecko** as an optional dynamic analysis/debugger environment, only after compatibility with the actual Racer GameCube/Wii release is confirmed.
7. **gcrecomp** as an experimental code-generation/runtime research candidate, not as a proven Racer port or drop-in engine.

For PC behavioural research, continue using `SW_RACER_RE`, the Steam PC research snapshot and the older OpenSWE1R format tools, but never assume PC addresses, structures or assets match the GameCube/Wii release. The N64 `sp00nznet/racer` project is a useful static-recompilation case study, not a PowerPC source base.

## Target/platform rule

The PC, N64 and GameCube/Wii versions are distinct executable/platform contexts:

- **Windows PC:** x86; the existing `SW_RACER_RE` hooks, symbols, Ghidra/IDA scripts and PC asset tooling are behavioural/source-analysis references.
- **Nintendo 64:** MIPS; `sp00nznet/racer` is an N64 static recompilation project and uses the N64 binary/runtime.
- **GameCube:** 32-bit big-endian IBM PowerPC 750-derived Gekko, with GameCube-specific paired-single instructions and GX/DSP hardware.
- **Wii:** Broadway PowerPC 750CL-derived CPU and related SDK/runtime; DOL/REL and many low-level concepts are shared with GameCube, but this does not prove game assets, symbols, layouts or runtime details are interchangeable.

A finding from one version is a **lead** until checked against the exact target executable, disc revision, region and module. Keep evidence labels explicit: `CONFIRMED-IN-CODE`, `CONFIRMED-IN-RUN`, `DOCUMENTED`, `INFERRED`, `UNKNOWN`.

## Priority A — tools directly suited to GameCube/Wii

### 1. decomp-toolkit — primary DOL/REL and disc analysis tool

- Repository: [encounter/decomp-toolkit](https://github.com/encounter/decomp-toolkit)
- Audited ref: `main` at `9d1ac132c4e073c9c48ac393cf290ff33e4c809a`
- License: MIT OR Apache-2.0 (crate metadata).
- Fit: **Very high.**

The README describes function-boundary, signature, relocation, section and object analysis; DOL and REL splitting; CodeWarrior symbol demangling; linker-script generation; disc-image inspection and virtual filesystem support. It also understands common Nintendo containers/compression such as RARC, U8, Yaz0, Yay0 and NLZSS.

Most relevant commands/workflows:
- `dtk disc info` / `disc verify`: identify the image and verify its content against Redump where supported.
- `dtk vfs ls`: inspect a disc image or nested archive without first flattening the entire filesystem.
- `dtk dol info`: inspect the main DOL, including directly through a virtual filesystem path.
- `dtk dol config main.dol rels/*.rel`: generate initial configuration from a DOL and linked RELs.
- `dtk dol split`: split the original into relocatable objects using a project configuration.
- `dtk rel info` and `dtk rel merge`: inspect RELs and merge a DOL plus associated REL modules into an ELF for analysis.
- `dtk shasum`: record exact source/build identity.

Important limitation: **dtk does not decompile the complete game into a finished replacement.** It prepares and analyses the original binary, finds likely functions/data/relocations, and creates the structure that makes function-by-function analysis and optional byte-matching possible. Splits and data boundaries still need review.

### 2. dtk-template — avoid inventing the project structure

- Repository: [encounter/dtk-template](https://github.com/encounter/dtk-template)
- Audited ref: `main` at `d366876408b754891a0392badbc63bff3490469f`
- License: CC0.
- Fit: **Very high as a template/reference.**

The template provides a standard layout and build system for GameCube/Wii decompilation projects:
- `config/[GAMEID]` with per-version configuration;
- `build.sha1` for exact binary identity;
- `symbols.txt` and `splits.txt`;
- ignored `orig/[GAMEID]` for local original game files;
- `src/` and `include/` for reconstructed source;
- REL-specific symbol/split files;
- objdiff configuration and GitHub Actions/progress reporting.

The template README says nearly all active GC/Wii decompilation projects use this structure. This is a strong pattern to adopt **for a private/local analysis workspace or a carefully separated decompilation subproject**, not a reason to add the original disc image or extracted commercial assets to the public Boonta repository.

### 3. Ghidra-GameCube-Loader + Gekko/Broadway language — correct CPU semantics

- Repository: [Cuyler36/Ghidra-GameCube-Loader](https://github.com/Cuyler36/Ghidra-GameCube-Loader)
- Audited ref: `master` at `921504c9ddba6e8d9b3655b665a60f1a33306220`
- License: Apache-2.0.
- Fit: **Very high.**

Its README documents loaders for DOL executables, REL modules, apploaders and RAM dumps, plus optional symbol-map import, namespaces and demangling.

The earlier standalone [aldelaro5/ghidra-gekko-broadway-lang](https://github.com/aldelaro5/ghidra-gekko-broadway-lang) README explicitly says the language definition supports Gekko/Broadway paired-single instructions and `dcbz_l`. It also says the work has been integrated into Cuyler36's loader repository and that maintenance continues there. Prefer the maintained loader over installing an unmaintained standalone language package.

Why this matters: a generic PowerPC language is not automatically enough for GameCube/Wii. Gekko/Broadway-specific paired-single operations and quantized loads/stores are used by real code. Incorrect decoding can poison function analysis and inferred data types.

### 4. powerpc-rs — independent Gekko/Broadway instruction decoding

- Repository: [encounter/powerpc-rs](https://github.com/encounter/powerpc-rs)
- Audited ref: `main` at `4643ee0fd3275e3a89dee709185c37968acca83b`
- License: MIT OR Apache-2.0 (`Cargo.toml`).
- Fit: **High as a supporting library/tool.**

The README identifies support for PowerPC 64-bit, Gekko (750CXe) paired singles for GameCube, Broadway (750CL) paired singles for Wii, AltiVec and Xbox 360 VMX128. It provides a Rust disassembler and assembler, with instruction definitions generated from `isa.yaml`.

Use it to cross-check instruction decoding, create compact disassembly inventories or build small targeted analysis tools. It is not a DOL/REL project manager or a high-level decompiler on its own.

### 5. objdiff — matching and object-level comparison

- Repository: [encounter/objdiff](https://github.com/encounter/objdiff)
- Audited ref: `main` at `9aeec9cbab1a056ade7dc1f1625aacc41b0f8511`
- License: MIT OR Apache-2.0.
- Fit: **High once there is source to compare.**

The tool compares relocatable object files, functions and data; supports PowerPC (GameCube/Wii), MIPS, ARM and other architectures; understands CodeWarrior symbol naming and can rebuild the current side when sources change. macOS arm64 and x86-64 GUI downloads are listed in the README.

Use it when a function or translation unit is being reconstructed and an appropriate target object/compiler configuration exists. It is not a substitute for understanding behaviour and it should not drive the project into matching every byte before we know which implementation strategy we want.

### 6. Gecko — optional dynamic reverse-engineering environment

- Repository: [ioncodes/gecko](https://github.com/ioncodes/gecko)
- Audited ref: `master` at `91950c6364d8a464d6eb0a666dbf3a6dec24d5bb`
- License: GPL-3.0.
- Fit: **High as a read-only investigation candidate; compatibility for Racer not yet confirmed.**

The README describes a cross-platform GameCube/Wii emulator and debugger with PPC/DSP JITs, DOL/apploader IDA loaders, symbol import, Lua runtime introspection, FIFO recording/playback, diagnostics and an MCP server. It may provide a useful way to observe actual memory, state transitions and runtime calls while a locally owned game copy is running.

Do not assume Star Wars Episode I: Racer is already supported merely because many other games are. First confirm the exact game version boots and that the debugger can expose the memory/function state needed. Its GPL-3.0 license is a constraint on code reuse; use it as a separate tool unless a deliberate compatibility/licensing decision is made.

### 7. gcrecomp — experimental GameCube static-recompiler candidate

- Repository: [sp00nznet/gcrecomp](https://github.com/sp00nznet/gcrecomp)
- Audited ref: `main` at `67491ae68d29567d41d09ef99989893f94751cbf`
- Root LICENSE file says MIT; GitHub's license detector returned `NOASSERTION`, so retain the explicit LICENSE and third-party notices during any further audit.
- Fit: **Potentially valuable, but experimental and unproven for Racer.**

Its README claims a Gekko PPC-to-C recompiler with DOL/REL parsing, paired-single support, control-flow-graph construction, symbol maps, OS HLE, disc/FST reading, Yaz0/RARC, GX/TEV, DSP audio and controller support. The guide explains that unresolved OS calls and game-specific behaviour still need to be handled.

The same README marks important pieces as in progress: GX vertex-format handling, draw-call pipeline and TEV shader compilation; the audio backend is described as a stub/integration in progress. It documents Windows 11 + DirectX 11 + CMake + Visual Studio 2022 as its build target. No Racer-specific bring-up or complete retail-game execution was verified in this audit.

Recommendation: inspect it for algorithms, Gekko instruction coverage, PPC context layout, DOL/REL and GX/OS HLE ideas. Do **not** replace Boonta's architecture with it, claim it is a ready-made Racer port, or import its code until its actual implementation, tests and licenses/dependencies have been reviewed against our target.

## Priority B — reverse-engineering and behavioural references for the PC version

### 8. SW_RACER_RE — principal PC systems map

- Repository: [Master-Chiken/SW_RACER_RE](https://github.com/Master-Chiken/SW_RACER_RE)
- Audited ref: `master` at `66120be334a3fd38c10a259f3528cffbfed8ddc5`
- License: AGPL-3.0.
- Fit: **Very high as a PC reference; not a GC/Wii implementation source.**

It contains PC function hooks, global symbols, Ghidra import/export scripts, type definitions and modules around race/game state, objects, splines, models, rendering, sound, UI, multiplayer, weather and platform/engine support.

The README explicitly says it documents/reimplements selected functions and does not aim for matching compilation or a complete decompilation. Its 71.2% figure is functions analysed as of 2026-06-12, not 71.2% of the full game reimplemented.

The initial marker scan recorded in issue #226 found substantial `HANG("TODO")` placeholders in hook sources, especially `swrObj.c` and `swrRace.c`. These markers mean the PC hook project has not implemented those replacements; original PC code may still run in the retail executable. Do not infer that the original game feature itself is missing.

### 9. Steam PC decompilation snapshot

- Repository: [DeonPoncini/swep1r_decomp](https://github.com/DeonPoncini/swep1r_decomp)
- Audited ref: `master` at `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`
- License: no root license was established in this audit.
- Fit: **Read-only cross-reference only.**

It can provide function/type/signature clues for the Steam PC executable and help challenge interpretations from SW_RACER_RE. Keep it read-only; do not copy its implementation or assume that the PC build's addresses and layouts map onto GameCube/Wii.

### 10. OpenSWE1R and swe1r-tools

- [OpenSWE1R](https://github.com/OpenSWE1R/openswe1r), [swe1r-re](https://github.com/OpenSWE1R/swe1r-re) and [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools)
- Audited refs: OpenSWE1R `1fcb4a8e8b5e031f0dde38b340cfca1b07e9738e`; swe1r-re `57638c19ed092d52c152d8119e0cfe55e9c9f129`; swe1r-tools `239911513834e19d1530fc908b6dc40eabea25fc`.
- License notes: swe1r-tools declares GPL-2.0-or-later; review each repo's own license and current status before reuse.
- Fit: **Useful format/tool research for PC assets; not assumed GC/Wii parsers.**

The tools cover selected spline, sprite, texture, save/string and audio-related formats. Some code/documentation is old and platform-specific; a model-block helper is explicitly tied to the N64 version. Use them as documentation or separate local tools for their supported PC formats, not as universal parsers. Do not copy extracted proprietary assets into Boonta.

### 11. sp00nznet/racer — N64 static-recompilation case study

- Repository: [sp00nznet/racer](https://github.com/sp00nznet/racer)
- Audited ref: `main` at `694c5663b3a7c30e2862fc240344f34683f99a9c`
- License: MIT for repository tools/runtime; the repository's LICENSE explicitly excludes the original game's code, art, audio, data and game-derived output.
- Fit: **High methodological value; platform mismatch.**

Its README documents a significant N64 static-recompilation effort using N64Recomp, with boot/runtime, asset loading, controller, display-list, RT64, audio and visible-race progress. It demonstrates the value of fixing low-level OS/RSP/event/runtime plumbing rather than only writing game logic.

But N64 is MIPS. It is not a GameCube/Wii PowerPC codebase and its game-derived symbols/assets are not interchangeable. Reuse its methodology and independently licensed generic tooling only after review; do not transplant its game code.

## Lower priority / not a direct game reverse-engineering solution

### Kuna and decomp.anything

- [Noelo-Lab/kuna](https://github.com/Noelo-Lab/kuna) — `main` `9b758091aee1fe850ca931298a097c79a2800bc1`, Apache-2.0. Agent-oriented Rust decompiler, CLI, web/WASM and Ghidra integration. It is promising for PC x86 function analysis and general agent-driven binary research.
- [giveen/decomp.anything](https://github.com/giveen/decomp.anything) — `main` `b410ac528ded6fa9adb7fad4f000cebbf5f341e6`, MIT. A workbench/orchestrator using matching-decomp where practical and REA procedure/function analysis elsewhere; the latest inspected main includes Kuna/unblob integration and binwalk detection.

**Important Gekko caveat:** the stock Kuna PowerPC SLEIGH files inspected here (`ppc_32_be.slaspec`, `ppc_common.sinc`, `ppc_isa.sinc`, `altivec.sinc`, `g2.sinc`) did not expose explicit `psq_*` / paired-single mnemonics in the searched source. Treat native Gekko/Broadway handling as unverified until tested. For GameCube/Wii, prefer the maintained Ghidra GameCube loader/language and independently cross-check with powerpc-rs. Do not assume that a generic PowerPC decompiler understands every Gekko instruction.

**Platform caveat:** decomp.anything's README lists Linux x86-64 and Windows WSL2; it does not document native macOS support. Kuna itself lists macOS builds. Do not make installation of decomp.anything a prerequisite for continuing Boonta work on the owner's Mac.

### AeroMESH

- Repository: [tex1ure/AeroMESH](https://github.com/tex1ure/AeroMESH)
- Audited ref: `main` at `38491790317b5ba779626c0eedb22508c844abfe`
- License: Apache-2.0.
- Fit for reverse engineering: **Low / not a priority.**

The README describes a Windows 10/11 + NVIDIA CUDA distributed inference cluster for LLMs and diffusion models over LAN/Tailscale. That can be useful infrastructure when there are multiple CUDA-capable machines and a justified need to distribute local inference. It does not parse game binaries, reconstruct functions, understand DOL/REL or extract game assets. It is not needed to make progress on Boonta's core RE work, especially on the current Mac environment. Revisit only if distributed local inference becomes a demonstrated bottleneck and matching hardware exists.

## Suggested system-mapping workflow

Do not start by writing a new game system from guesses. Start with a versioned evidence map and one connected gameplay path at a time.

### Phase 0 — establish exact local target identity

On the owner's machine, with a legally obtained GameCube/Wii copy:
1. Identify game title ID/game ID, region, revision and whether the target is GameCube or Wii.
2. Use dtk's disc/VFS commands to inspect the image and locate the main DOL, REL modules, apploader and data archives.
3. Calculate and record SHA-1/SHA-256 for the exact disc image (private), main DOL, each relevant REL and extracted executable subset.
4. Record DOL section map, entry point, SDA/SDA2 values, module list and any public symbol map candidates.
5. Keep all original executable/disc files and proprietary extracted content in a local ignored directory. Do not push the image, ROM, DOL/REL, raw binary dumps or proprietary assets to GitHub/ChatGPT.

No binary has been supplied to this audit. No claim is made yet about the exact Racer GC/Wii release contents or whether all relevant modules are known.

### Phase 1 — create a repeatable analysis workspace

Use the dtk-template conventions locally:
- per-game-ID / per-revision config;
- `build.sha1` and a manifest of exact source hashes;
- `symbols.txt` and `splits.txt`;
- original files under an ignored `orig/` directory;
- generated disassembly, REL merges and object reports under ignored `build/`;
- public repo contains only our own reports, synthetic tests, clean-room code and non-copyrighted metadata.

Use Ghidra GameCube Loader with Gekko/Broadway language for DOL/REL and PPC paired singles. Keep an independent powerpc-rs decode report for instruction-level cross-checks. Use objdiff only when original compiler/build inputs and target objects exist.

### Phase 2 — reconstruct one connected race lifecycle

Build a single cross-reference table linking:
- boot and low-memory initialization;
- DOL/REL loading, DVD filesystem, asset containers and resource lifetimes;
- menu / vehicle / track selection;
- race start and per-frame game loop;
- pod input, handling, physics, engine thrust, turning, pitch, slide, boost, heat, repair and damage;
- spline/route cursor, track projection, surface response, collisions and lap crossings;
- rival participant updates, AI route choice, overtakes and ranking;
- camera, HUD, animation, sound/DSP and visual effects;
- finish/results, tournament progression, unlocks, profile/save persistence and restart.

For each system, record:
- executable version/hash and platform;
- function address, symbol/name and source location;
- caller/callee links and relevant globals/structs;
- what the code proves vs what remains an inference;
- whether the behaviour was observed in a local running game;
- related asset block/file formats and parser confidence;
- existing public implementations/tools and their license/provenance;
- next smallest experiment that could falsify the current interpretation.

### Phase 3 — implementation decision after evidence

For each system, choose among:
- clean-room reimplementation in Boonta;
- use a separately licensed generic library/tool as a dependency;
- adapt an algorithm only after checking license and platform semantics;
- write a platform-specific replacement (GX/DSP/PAD/WPAD/DVD/OS);
- keep as an unknown until more evidence exists.

Do not bulk-copy PC, N64, Dolphin, GPL or AGPL code into the MIT Boonta repository. Tool licenses do not grant rights to the game's original code, executable, art, audio or extracted data. Keep proprietary content local and build public fixtures from original synthetic data.

## Immediate next research tasks

1. **Target identification:** prepare the local DOL/REL manifest workflow and identify the precise game/region/revision to analyse. This is the single biggest missing input; no public-source audit can substitute for the owner's exact binary.
2. **Tool viability spike:** test dtk disc/DOL/REL inspection, Ghidra loader + Gekko language, and powerpc-rs against the same exact local executable subset; compare function boundaries and paired-single decoding.
3. **Symbol search:** search active/public GC/Wii decomp projects, decomp.dev and symbol repositories for the exact game ID/title. Do not stop at generic Racer/Star Wars search results; confirm platform and version.
4. **Runtime observation:** only after target identity and tooling are established, use Gecko or an equivalent debugger for read-only traces of boot, game-state transitions, pod update and asset loading. First confirm the target game actually boots in that emulator.
5. **Connected system dossier:** start with boot → course load → race update → finish/results. Expand to vehicle physics, AI, assets and presentation using function/call/global references, not disconnected speculative notes.

## What is deliberately not being done now

- No more manual three-lap Dolphin acceptance as the next task.
- No hardware acceptance of the Under Control/Wii Classic controller yet.
- No auto-merging of PR #274 or #269.
- No wholesale replacement of the current Boonta scaffold with gcrecomp, Gecko, Kuna or any other project.
- No importing of original game code, ROM/disc images, models, textures, audio or other proprietary assets into the public repository.
- No installation of AeroMESH or other distributed LLM infrastructure without a demonstrated need and compatible hardware.

**Bottom line:** the best shortcut is not one universal AI decompiler. It is a combined, target-correct GC/Wii toolchain (dtk + Gekko-aware Ghidra + powerpc-rs + objdiff), supported by PC/N64 reverse-engineering references and optional runtime introspection. First identify and analyse the exact local target; then reconstruct connected original systems and only then implement their clean-room equivalents in Boonta.


## Additional asset-format research — PC-only unless proven otherwise

### swe1r-assets — strongest bit-perfect PC block library

- Repository: [akopetsch/swe1r-assets](https://github.com/akopetsch/swe1r-assets)
- Audited ref: `main` at `922ef535f6598a1330ff93d6b07258956f990b34` (last push recorded 2024-07-10).
- License: MIT.
- README states support for `out_modelblock.bin`, `out_splineblock.bin`, `out_spriteblock.bin` and `out_textureblock.bin`, with deserialize/modify/serialize and bit-perfect no-op reserialization.
- The README places these files in the PC game's `data/lev01` directory. Treat it as a **PC asset-format tool** until a GameCube/Wii compatibility proof exists.
- Best first use: read its format definitions and no-op round-trip tests, compare the supported fields with the other PC tools, and make a private synthetic or user-local fixture. Do not commit the resulting game-derived blocks/assets to Boonta.

### blender-swe1r — model/collision/spline editing workflow

- Repository: [louriccia/blender-swe1r](https://github.com/louriccia/blender-swe1r)
- Audited ref: `main` at the 2026-11-02 tree state (repository was pushed on 2026-11-02; README blob `f421c025147e1db84d7ad1447a486c1c46d9b3db`).
- License: GPL-3.0.
- README describes an active Work In Progress Blender 5 extension for importing/exporting models and editing mesh, collision, texture, vertex colour, animation and spline data. Its Blender round-trip test procedure reads local PC `data/lev01` files, exports to a temporary copy, and checks geometry, collision triangles, materials, animation samples, spline points and that unrelated block data remains byte-identical.
- Known issue documented upstream: template-built pods do not export LODs/animations/far-LOD and have an empty high-detail MAlt model; imported pods are exported in full.
- Best use: study its format coverage and round-trip test methodology; consider it a local PC-asset editor only after a target version is confirmed. It is not evidence of GameCube/Wii block compatibility. GPL-3.0 means no code copy into Boonta's current MIT codebase without an explicit license decision.

### SWE1R-Mods — useful unpack/repack scripts, but content is not a reusable asset pack

- Repository: [louriccia/SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods)
- Audited ref: `main` at README blob `faf4fa2d1d668705364ea0fa228875b054647e51`.
- No root license was established in this audit; do not copy its scripts or contents until licensing is clarified.
- README documents Node.js unpack/repack scripts for model, texture and other PC block files, using earlier swe1r-tools/Sw_Racer groundwork. It also contains actual track/texture mods, including N64-labelled texture content.
- Best use: inspect its parser/repacker assumptions and format documentation as research leads. Do not import its model/texture/mod output into Boonta. The existence of PC block unpackers does not establish console-format support.

### Asset-format rule

Keep separate format workspaces for PC `data/lev01` blocks and GameCube/Wii disc files. A shared extension such as `.bin` or `.arc` is not proof that their internal layouts are identical. For every parser, record the exact input platform/version, hashes, supported block IDs, round-trip guarantees, and known unsupported sections. A no-op round-trip proves preservation for the tested format and fixture, not that the format is universal.


## Additional porting leads discovered during the audit

### dguillot-gh/star-wars-racer-recomp — N64 Android host port

- Repository: [dguillot-gh/star-wars-racer-recomp](https://github.com/dguillot-gh/star-wars-racer-recomp)
- Audited ref: `main` at `68d3d2709cf71c07b5abed3627e01b03696cefd2`
- License: MIT for repository tooling/runtime; its LICENSE explicitly excludes the original game and game-derived output.
- Fit: **Useful N64 runtime/porting case study; not GC/Wii code.**

The README says this is an Android native port of the **Nintendo 64** release. It is built on `sp00nznet/racer` and N64Recomp; it carries the existing N64 function map/config/runtime glue and adds Android host work. It documents a full Tournament race from start to finish on a Pixel 8, with touch controls, sound and save persistence; the README also lists untested gamepad support and audio long-session checks. It requires a legally dumped USA N64 ROM with a documented SHA-1 and builds the recompiled code locally. Its generated game code/APK are ignored and must not be shared.

Best use: inspect the platform/runtime boundary, Android input and persistence adaptation, the documented sequence of low-level bring-up fixes, and how it preserves original game data locally. Do not treat it as independent reverse engineering of the GC/Wii release; much of its game function map and core runtime glue comes from sp00nznet/racer.

A related [dguillot-gh/racer-android](https://github.com/dguillot-gh/racer-android) branch/fork contains an earlier Android bring-up stage and documents the intro/menu/rendering milestones. Use the newer `star-wars-racer-recomp` repository as the primary reference for that porting work.

### n64hub/racer-web — N64 web-host fork (low priority)

- Repository: [n64hub/racer-web](https://github.com/n64hub/racer-web)
- Audited ref: `main` at `4e64f8065a98b6cbd567143d94739400729b535e`.
- Its README explicitly identifies it as a fork of `sp00nznet/racer`, with AI-written work on the fork's own web branch and a WebGPU browser frontend. It says it is not upstream or supported by sp00nznet.
- Best use: optional study of a separate N64 browser host, not a new source of original-game knowledge and not a basis for Boonta's GameCube/Wii target.

### Unverified Dreamcast recompilation catalogue entry

A RecompHub catalogue page lists a recently active “Star Wars: Episode I - Racer Recomp” credited to Ned Heller, release `v0.4.0`, with Windows/macOS/Linux as targets. Its own catalogue record says the original version, exact required files, license and playability are **unknown**; the page categorizes it with Dreamcast ports, but I did not resolve an authoritative source repository or verify the source platform from project files in this audit.

Treat this only as a **lead to identify**, not as a verified project to depend on. Before using it, find its official repository and inspect the source platform, exact original release/version, commit history, license, dependencies and build/acceptance evidence. Do not infer that it targets the Dreamcast binary solely from a third-party catalogue category.


## Additional DOL-analysis workbench — REA (static analysis only)

### morluto/rea — useful new DOL-to-Ghidra lane, with strict scope limits

- Repository: [morluto/rea](https://github.com/morluto/rea)
- Audited repository revision: `d896ab7bd78331efa15e35337c1f8eff45a21623` (2026-11-04).
- DOL lane introduced at: `cab78de50673c89766dba2b7687b1bbb5045c43a` (2026-10-24); latest DOL guide revision checked at `46c457f74c474b224dd540d6eae6bc23080cd95f` (2026-10-28).
- License: MIT in the root `LICENSE` at the audited revision.
- Fit: **Promising supplementary static-analysis workbench for a caller-supplied DOL; not a replacement for dtk, the GameCube Loader, Dolphin, or a full recompiler.**

The project documents an explicitly selected `gamecube-dol` target for importing a 32-bit big-endian GameCube/Wii DOL into Ghidra. Its parser validates the 0x100-byte header, section file/load ranges, section overlap, entry point and BSS gaps before launching Ghidra. It then creates initialized text/data blocks at their load addresses and an uninitialized BSS mapping. It is a static import/decompilation workflow: **it does not execute the DOL**.

The documented CLI starting points are:

```bash
rea inspect /absolute/path/to/main.dol --target-format gamecube-dol --provider ghidra --json
rea function /absolute/path/to/main.dol 0x80003130 --target-format gamecube-dol --provider ghidra --json
```

For GameCube/Wii paired-single instructions, the stock Ghidra `PowerPC:BE:32:default` language is insufficient. REA documents an optional `PowerPC:BE:32:Gekko_Broadway` override supplied by the Apache-2.0 Ghidra GameCube Loader extension. The extension must be installed in the Ghidra installation's admitted extension catalogue; otherwise the DOL lane can still pass stock PowerPC checks while Gekko/Broadway paired-single words decode incorrectly or as undefined.

**Hard boundaries from REA's own guide:**
- Only the cached MEM1 address window `0x80000000..0x81800000` is admitted. Wii MEM2 and uncached aliases are outside the lane.
- REL and RPX are not admitted. This does not cover separately loaded modules.
- DOL support is Ghidra-only; IDA and Hopper are not supported for this target.
- Disc images (ISO/GCM) are not read by this lane; the caller must first provide an extracted DOL.
- `r2`/`r13` small-data anchors are not seeded from the DOL header.
- The DOL fixture verifies parser/import mechanics using source-owned test bytes; it does **not** establish compatibility with Racer or any retail game.

The repository describes REA as an MCP/CLI workbench and supports a caller-installed Ghidra setup. Its README advertises Node.js/npm setup and optional agent configuration. No REA installation, Ghidra execution, original DOL analysis, or Racer compatibility test was performed for this audit.

**Decision:** add REA as an optional local-only front-end for a verified DOL after its exact platform/revision and hash are recorded. Keep `decomp-toolkit` as the first step for disc/FST and DOL/REL inventory, use the maintained Ghidra GameCube Loader plus its Gekko/Broadway language for correct target decoding, and use REA only where its admitted DOL/MEM1 scope fits. Do not route an unverified Wii MEM2 image or a REL through the DOL lane, and do not upload a retail DOL, ROM, disc image, Ghidra database or extracted proprietary content to Boonta CI.

## Additional GameCube research runtimes and recompiler candidates

### pureikyubu — strongest newly found dynamic-analysis candidate

- Repository: [emu-russia/pureikyubu](https://github.com/emu-russia/pureikyubu)
- Audited ref: `master` at `69572aa22ca44646807b9973dc830592c5d266e8`
- License: CC0-1.0 in the root LICENSE.
- Fit: **High as a separate read-only emulator/debugger and hardware-reference environment.**

The current README describes a work-in-progress GameCube emulator whose aim explicitly includes researching GameCube hardware and reverse-engineering game technologies. It now documents a debugger, a local MCP server, headless runs, save states and controller/I/O support; its CPU/DSP implementation includes Gekko and DSP paths. The README documents a native macOS Apple Silicon build, as well as Windows and Linux builds.

Potential Boonta use:
- run the exact local GameCube executable in a second emulator implementation and compare behaviour with Dolphin;
- use its debugger/MCP/headless mode to inspect memory, function calls, OS structures, controller state and graphics/audio scheduling where supported;
- cross-check hardware assumptions against its source and documentation.

Important limitation: its own README says compatibility remains a work in progress and some titles still fail to render or hang. No successful Star Wars Episode I: Racer run was confirmed in this audit. First check compatibility with the exact title/revision; never treat an untested emulator as a source of truth. The user's previously reported macOS 10.15.7 is not the documented Apple Silicon macOS target, so do not assume it will build on that machine.

### KaiserGranatapfel/GameCubeRecompiled — inspect only after EULA review

- Repository: [KaiserGranatapfel/GameCubeRecompiled](https://github.com/KaiserGranatapfel/GameCubeRecompiled)
- Audited ref: `main` at `d380537add5aa4116c94c3513b8e3a7dd89f2331`
- Root LICENSE: CC0-1.0.
- Fit: **Research lead only; do not select as a dependency yet.**

The README describes a PowerPC DOL-to-Rust static recompiler with Ghidra export, CFG/data-flow analysis and a native runtime. But its status text is internally uneven: the top labels it “production-ready”, while the same README lists SDK stubs, graphics, DSP audio and input integration as in progress and lists full game boot support as a medium-term goal. The inspected instruction feature list did not explicitly confirm GameCube Gekko paired-single `psq_*` instructions. The repository also uses a placeholder `yourusername/GCRecomp.git` in its quick-start command.

**Major licensing caveat:** alongside CC0, the repository contains an `EULA.md` that restricts use to educational/research/archival/personal non-commercial purposes, prohibits distribution of recompiled outputs without rights-holder permission, includes indemnification language and claims revocable use rights. This is not a simple CC0-only reuse position. Do not install it as a project dependency, copy code, contribute or use it as part of Boonta's published toolchain until the EULA/licence interaction and the exact technical capabilities have been independently reviewed.

### Distinguish the two GameCube recompiler candidates

- `sp00nznet/gcrecomp`: C/C++ Gekko-to-C toolkit; README explicitly claims DOL/REL and paired-single support, but GX vertex/draw/TEV and audio pieces are in progress. README says Windows 11 / D3D11 toolchain. Root LICENSE says MIT; confirm the third-party notices and actual code before reuse.
- `KaiserGranatapfel/GameCubeRecompiled`: Rust DOL-to-Rust recompiler; root CC0 is accompanied by a restrictive EULA, and the README's own roadmap indicates substantial runtime/graphics/audio work remains. Do not assume paired-single support from generic PowerPC claims.

Neither has been shown to run Racer in this audit. Keep both as separate experiments, not as the foundation of Boonta.
