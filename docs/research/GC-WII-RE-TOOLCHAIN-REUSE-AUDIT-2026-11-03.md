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
