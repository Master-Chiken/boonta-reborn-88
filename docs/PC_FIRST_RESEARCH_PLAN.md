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

## Verified existing-work snapshot — 2026-10-20

This snapshot separates what has a direct implementation or test artifact from what is merely a research lead. “Verified” here means the repository, code, tests or named CI run were inspected; it does not mean I executed every external tool or verified the commercial game at runtime.

### 1. Boonta Reborn itself — keep the working slice

- **Implemented:** `gamecube-demo/` contains native GX rendering, an original procedural track and pod, state-based driving controls, boost/heat, laps, HUD, pause/reset and host regression tests. Root `LICENSE` is MIT for the repository's own code; it does not grant rights to Star Wars game content.
- **Automated evidence:** the project documents native devkitPPC/libogc DOL/ELF builds, host tests, DOL/ELF validation, and Dolphin process/render diagnostics. A visible procedural frame and scripted finish diagnostic are useful evidence, but neither proves a human can control and complete the race.
- **Still unverified:** manual-controller end-to-end race acceptance; physical GameCube/Wii behavior; integration of the private Step 102 candidate; compatibility with original commercial models/textures/audio. The Step 102 ZIP/manifest and its path/license evidence remain gating inputs, not something to bypass.
- **Rule:** preserve this working clean-room slice. Do not replace it wholesale with a third-party project or mix it with the unreviewed Step 102 bundle.

### 2. External projects and best use

| Candidate | What exists and current evidence | Best next use | Do not assume |
|---|---|---|---|
| [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | Windows-PC function/symbol research, Ghidra import scripts, `data_symbols.syms`, generated hooks, and a 32-bit `dinput.dll` mod build path. Reviewed tip: [`a9863edd`](https://github.com/tim-tim707/SW_RACER_RE/commit/a9863edd4caaa573f89ff634fa7d1cd6d41738ab), 2026-10-05. Release [v0.17](https://github.com/tim-tim707/SW_RACER_RE/releases/tag/v0.17) published 2026-08-28. The latest green CI run found in this audit is [run 36903363545](https://github.com/tim-tim707/SW_RACER_RE/actions/runs/36903363545) on earlier PR head `b9122dfe`, not the reviewed tip. README's dated 71.2% is functions **analysed**, not necessarily reimplemented; the later release's “over 75% done” phrase is not directly comparable. | Highest-priority PC behavioral oracle: map one subsystem/function at a time, pin exact source and binary version, and record TODO/HANG gaps. | Not the original source for every function, not a full clean-room game, not a native GameCube/Wii port. GitHub reports AGPL-3.0; no code import without a separate license/architecture decision. |
| [Ghidra](https://github.com/NationalSecurityAgency/ghidra) | Latest release observed: [12.1.4](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build), pinned release-tag commit [`8b6bbb8`](https://github.com/NationalSecurityAgency/ghidra/commit/8b6bbb857accdfa20dc5b2f5dea471178c2e9fbc), published 2026-09-21. Its [Headless Analyzer](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md) supports scripted binary import/analysis and repeatable non-GUI scripts. `SW_RACER_RE` README documents Ghidra 10.2.2 for its existing workflow. | Use only when there is a specific binary/version to analyse; generate a repeatable function/address/import report via scripts and pin the tool version. | Ghidra analyses executables/ROM binaries; it does **not** replace the asset parsers below. Do not upgrade an existing analysis project blindly. The current distribution is roughly 570 MB, so do not download it just to “have the tool”; first establish target binary, storage space and needed output. |
| [swe1r-assets](https://github.com/akopetsch/swe1r-assets) | MIT C#/.NET library; inspected main tip [`922ef53`](https://github.com/akopetsch/swe1r-assets/commit/922ef535f6598a1330ff93d6b07258956f990b34), 2024-07-10. README documents deserialize/modify/serialize with bit-perfect no-op reserialization for `out_modelblock.bin`, `out_splineblock.bin`, `out_spriteblock.bin`, and `out_textureblock.bin`. Extensive format/reserialization test files exist; the workflow found in this audit is release/package publishing rather than an automatically verified current test run. | **Best candidate for a controlled PC block-format round-trip test** once a lawful local input is available: unpack without changes, repack, compare hashes, then test one isolated field change. | MIT covers the library code, not the original game assets. PC `data/lev01` support does not prove GameCube asset compatibility. |
| [blender-swe1r](https://github.com/louriccia/blender-swe1r) | GPL-3 Blender import/export extension marked WIP; inspected `main` tip [`212ed6b`](https://github.com/louriccia/blender-swe1r/commit/212ed6be805700cb02bf0c28c126eaa79f9ba763) (2026-07-17). README says Blender 5.0+ and documents model, collision, texture, vertex-colour, animation and spline editing. Main README still reports Podd/MAlt unsupported. A separate public branch [`claude/magical-feynman-cvts21` / commit `c941778`](https://github.com/louriccia/blender-swe1r/commit/c941778586bc0fe22b8cf084fb240e3dc68cec00) has passing [Tests run 39183458436](https://github.com/louriccia/blender-swe1r/actions/runs/39183458436) on 2026-10-19; that commit adds Podd/MAlt merge-on-import handling and synthetic parser tests, but it is not evidence that the feature is released on `main`. | Inspect that branch's small Podd/MAlt fix and tests as a possible extraction/import lead; test using synthetic fixtures first, then a private lawful local game file if needed. | Do not label the unreleased branch as the default stable tool. GPL-3 obligations and proprietary asset rights are separate questions. |
| [OpenSWE1R/swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) | GPL-2.0-or-later tools; inspected master [`2399115`](https://github.com/OpenSWE1R/swe1r-tools/commit/239911513834e19d1530fc908b6dc40eabea25fc) (2018-05-10): spline-block to OBJ; sprite/texture blocks to PNG; string/save/profile parsers. Its README specifies Python 3 and notes the `decompress.c` “Comp” model-block path is found in the N64 version. | Read as an independent format reference and compare its output/assumptions with `swe1r-assets`. | Older helper collection, not an all-platform asset extractor. Do not copy GPL code into the MIT repo without a deliberate license decision. |
| [SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods) | Inspected main [`a0c55e3`](https://github.com/louriccia/SWE1R-Mods/commit/a0c55e301a01ce0212b2146a280782cacab155e6) (2024-02-21): Node.js unpack/repack scripts and mod examples for `.bin` blocks are documented. The repository includes actual mod/content files; a root license for the full repository was not established in this audit. Its README includes N64-labelled content, so confirm format/platform per block. | Read the tool flow; if separately licensed tools are used, run against private local inputs and compare no-op round trips. | Do not copy or publish its textures, models, geometry or mod outputs; do not assume the repository's contents are redistributable. |
| [Sw_Racer](https://github.com/Olganix/Sw_Racer) | Older C/C++/CMake format research; inspected master [`76c8ad9`](https://github.com/Olganix/Sw_Racer/commit/76c8ad9cea549ea18457846a135a7f25d48b3813) (2018-05-24); documents `.bin` model-block conversion to XML/Collada. README states GPL-2.0-or-later and calls out dependency/licensing conditions for the Unicorn backend. | Secondary corroboration only if a parser disagreement remains. | Not the primary modern pipeline; do not pull its code/dependencies into Boonta without reviewing the license and age/platform limits. |
| [swe1r-assets-unity](https://github.com/akopetsch/swe1r-assets-unity) | MIT Unity package, inspected main [`2fcae91`](https://github.com/akopetsch/swe1r-assets-unity/commit/2fcae9138583da959882171095920ab9b802168b) (2024-11-16), explicitly a WIP sample project based on `swe1r-assets`. | Low priority; inspect only if a later Unity-based asset-visualisation task is selected. | Not a ready-made game or higher-priority extraction path than the underlying asset library. |
| [Frozen Steam PC decompilation](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef) | Address-matched Ghidra decompilation useful for cross-checking PC function bodies and memory accesses. README says its source view is for type clarification/compilation attempts, not full source translation; no root license was identified in the reviewed snapshot. | Read-only cross-check for a concrete RE question; record function/address/commit and confidence. | No code copying/adaptation and no claim of GameCube parity. |

### 3. What “works” means — evidence gates

Classify each candidate with one of these states, and keep the exact hash/commit/test link:

- **SOURCE-FOUND** — code/data format documentation is present.
- **BUILD-VERIFIED** — exact commit built; this is not runtime proof.
- **ROUNDTRIP-VERIFIED** — a lawful local input is unpacked/repacked with a byte-identical no-op result.
- **BEHAVIOR-VERIFIED** — the exact version was run and an observable behavior was captured.
- **TARGET-VERIFIED** — that behavior/resource format was matched to the actual GameCube/Wii target evidence.
- **HELD** — provenance, licence, build/runtime evidence, or platform mapping is insufficient.

Current high-level triage: Boonta's clean-room prototype has build/test/render evidence but lacks manual race acceptance; SW_RACER_RE is the leading **PC research** source but its reviewed tip was not confirmed green by the most recent CI run found; asset parsers are promising for PC block files but have not been round-trip tested in this project. Step 102 is **out of the critical path** unless it later answers a specific technical question. PC/N64/Dreamcast data is not treated as GameCube data without direct evidence.

### 4. First experiments — no game implementation yet

1. Keep one inventory ledger of repository URL, branch and commit SHA, release/test link, license, target platform, asset/data scope, and what was actually verified.
2. Select **one** asset type and **one** PC file-format tool. Prefer a synthetic fixture first, then (only if available within the user's lawful/local workflow) a private local input. Run no-op unpack/repack and require byte-for-byte equality before editing anything.
3. For code behavior, pick one subsystem from SW_RACER_RE, link the exact functions and source addresses, then compare it with the current clean-room helper and list the tests needed to verify behavior. No copying code yet.
4. For Ghidra, do not install/download until there is an identified binary and enough local storage. Use headless scripts only after one narrow question needs binary evidence. Preserve the original project/version and record the exact processor/language and binary hash.
5. Treat every game-derived extraction as local-only by default. Public CI uses synthetic/independently authored fixtures; no ROM/disc/executable, private assets or extracted proprietary content goes into GitHub or hosted AI review.

The governing sequence is **MAKE IT WORK → MAKE IT GOOD → MAKE IT FAST**: first prove the smallest complete path works, then compare its behavior/assets with a measured reference, and profile/optimise only after correctness. “Fast” does not mean skipping provenance, compatibility or verification.


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
- Step 102 is not a current milestone or blocker; leave it untouched unless it becomes directly relevant to a defined research question.
- Do not import external code or original-game content into main without a separate license/provenance review.
- Keep all work within the project's free-only constraint: no paid APIs, no billing, no paid CI services.


## Cross-platform research focus — PC, Nintendo 64, Dreamcast

**Purpose:** use the original retail game versions as private, local behavioral/format references and use public GitHub research as the primary index of what is already understood. This is research for an independent GameCube/Wii implementation, not a plan to copy commercial game code or assets.

### Evidence and comparison matrix

| Reference | Best use first | Important caveat | First evidence to collect |
|---|---|---|---|
| PC Windows retail version | Highest-priority code/behavior reference because SW_RACER_RE and the frozen Steam Ghidra view expose functions, symbols, globals and function addresses | Windows x86 behavior is not console behavior; exact executable/build hash matters | Pin executable hash locally; map handling/physics, route progression, lap/finish, track loading and AI functions to the public function map |
| Nintendo 64 retail version | Console-side track/asset format and gameplay comparison; check N64-specific model compression, texture limits and console-specific mechanics | N64 is a distinct build/asset pipeline; never treat an N64 ROM or extracted payload as a PC file or GameCube source | Record cartridge/revision identity privately; compare track layout, route branches, lap rules, pod handling and visual simplifications against PC |
| Dreamcast retail version | Cross-check console behavior and the closer-to-PC feature set, rendering, track data and sound/cinematic differences | Dreamcast binaries and disc contents have not been publicly established as a reusable source tree; do not assume PC parity in every subsystem | Record disc/revision identity privately; test a short, repeatable set of gameplay observations against PC and N64 |
| GameCube/Wii target prototype | Acceptance target for the clean-room port | Emulator success is not manual gameplay acceptance; no PC/N64/Dreamcast evidence automatically proves target parity | Record build hash, emulator/version/settings, input method, capture, and reproducible race scenario |

### GitHub research hierarchy

1. **Primary PC function map:** [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE), pin every finding to a commit and function/address. Its own README says it analyzes and re-implements selected functions; the percentage reported is analysis progress, not a complete port.
2. **PC implementation/architecture reference:** [OpenSWE1R](https://github.com/OpenSWE1R/openswe1r) and [OpenSWE1R reverse-engineering notes](https://github.com/OpenSWE1R/swe1r-re). These are useful for architecture and historic analysis, but both projects are marked deprecated by their organization and focus on Windows x86, not N64/Dreamcast ports.
3. **Independent PC cross-check:** [frozen Steam decompilation](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef). Read-only reference for types and function behavior; do not copy its source.
4. **Asset-format cross-check:** [swe1r-assets](https://github.com/akopetsch/swe1r-assets), [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools), and [SWE1R-Mods tooling/docs](https://github.com/louriccia/SWE1R-Mods). Treat format/platform claims per block; the tools do not establish that every format works across PC/N64/Dreamcast.
5. **Console-specific research gap:** do not assume that a GitHub project mentioning “N64 textures” is a complete N64 reverse-engineering effort, or that any current PC decompilation documents Dreamcast. Search for explicit console-build evidence, format descriptions, symbol/function maps, and reproducible tests before elevating a repository.

### First research sprint (one question at a time)

1. **Freeze the reference inventory:** repository URL, commit SHA, license, platform/build identified, relevant paths/functions, test status, and confidence.
2. **PC behavior dossier:** continue RE-001 with one concrete subsystem at a time. Prioritize movement/steering and acceleration/boost/heat, then track/spline progression and lap completion, then AI/race state.
3. **Cross-platform observation sheet:** for one short track and one pod, record the same reproducible sequence on PC, N64 and Dreamcast: acceleration, steering response, wall contact, jump/landing, boost/overheat, lap transition and finish. Keep captures/notes private where they include proprietary assets.
4. **Format triangulation:** document each block/container signature and parser support separately by platform; test synthetic fixtures first. Only attempt a private local no-op round trip when a legal local input and a concrete question exist.
5. **Port decision:** implement only after the behavior is sufficiently specified and compared against the existing GameCube code. Keep the research-to-implementation ratio at **8 of every 10 focused work blocks**, and do not start a second subsystem while the active question is unresolved.

### Evidence labels for every finding

- **DOCUMENTED** — public repository/document says it; no independent test.
- **STATIC-ANALYZED** — code, symbols or binary metadata inspected.
- **RUNTIME-OBSERVED** — the identified original version was run and the observation recorded.
- **CROSS-PLATFORM-COMPARED** — same scenario measured on at least two identified versions.
- **TARGET-ACCEPTED** — corresponding behavior passed a repeatable GameCube/Wii test.
- **UNKNOWN** — platform/build/provenance or evidence is missing.

Never promote a finding from DOCUMENTED to RUNTIME-OBSERVED or TARGET-ACCEPTED without the corresponding evidence.


## Cross-platform source research

The platform-by-platform source inventory is maintained in [`docs/research/PLATFORM_SOURCE_MATRIX_2026-10-20.md`](research/PLATFORM_SOURCE_MATRIX_2026-10-20.md). Step 102 is parked and is not a critical-path dependency. Current research should prioritize identified original PC, N64 and Dreamcast versions, official feature references, and version-pinned GitHub reverse-engineering projects. Do not assume PC findings apply to consoles without a cross-platform comparison.
