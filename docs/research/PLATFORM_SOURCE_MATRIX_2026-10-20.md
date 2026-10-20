# Platform source matrix — Star Wars: Episode I Racer
Date: 2026-10-20

## Decision and scope

Step 102 is not a critical-path dependency for this research. Keep it parked unless it later answers a concrete question. The active priority is to mine original game releases and public reverse-engineering repositories, then compare what is actually shared and what is platform-specific.

Target order remains: GameCube prototype first; Wii only after the GameCube path is reliable. Use PC as the richest documented behavior reference, with Nintendo 64 and Dreamcast as independent console references. Do not assume the PC version is a drop-in source for console behavior.

## Source hierarchy

1. **Original, identified release/build** — record platform, region, revision, executable/disc identity and the exact scenario. Any local runtime observation must be reproducible.
2. **Official publisher/developer material** — use it for release facts and high-level intended features, not undocumented internal mechanics.
3. **Public reverse-engineering repositories** — use as static-analysis evidence; pin commits and license, distinguish analyzed from implemented and tested.
4. **Community modding/extraction tools** — use for format hypotheses and reproducible parsing, not as proof that files are identical across platforms.
5. **Boonta implementation and tests** — independent target implementation. Compare against sources; do not label it original behavior until evidence supports that.

## Platform matrix

| Platform | Research role | First questions | Evidence boundary |
|---|---|---|---|
| Windows PC (1999 / later patches and GOG/Steam builds) | Primary behavioral and code reference; strongest public decompilation/tooling | Handling/physics, race-state progression, AI, route/spline evaluation, collision, track loading, save/profile behavior, asset formats | Different PC executable versions may differ. Pin the exact executable/build for every observation. PC behavior is not proof of N64, Dreamcast or GameCube behavior. |
| Nintendo 64 (1999) | Console reference for original console gameplay, presentation, controls, split-screen and console-specific data | Track geometry and route topology, racer roster, race flow, controller mapping, performance/LOD, compressed model chunks, multiplayer differences | Do not infer PC binary/data formats apply. The OpenSWE1R tools README specifically marks its `decompress.c` model-block chunk decompressor as N64-only; treat each parser separately. |
| Dreamcast (2000) | Separate console port/reference for renderer, controls, performance and content parity | Track/content differences, frame pacing, rendering effects, controller behavior, split-screen, audio and data layout | No reviewed public full Dreamcast decompilation was established in this pass. Treat behavior as UNKNOWN until a specific identified release is inspected or run. |
| GameCube (Boonta target) | Current implementation and acceptance platform | Match race feel and track progression while fitting GX, memory, input and build constraints | Only target tests, Dolphin evidence and ultimately hardware evidence can establish acceptance. |

## High-value GitHub sources

### P0 — PC behavior and code
- [tim-tim707/SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) — PC function/symbol research, types, Ghidra scripts and hooks. Its README explicitly says it documents and reimplements *some* functions; its progress numbers count analyzed functions, not necessarily implemented functions. Repository license is AGPL-3.0. Pin a commit for every research note; do not copy code into Boonta without a deliberate license decision.
- [OpenSWE1R/swe1r-re](https://github.com/OpenSWE1R/swe1r-re) — documentation/analysis of PC functions; README identifies the Windows patch executable by MD5 `d86d5d03638c24ab6279f24079825794` and notes a planned shift to the Windows demo. This is a valuable independent cross-check, but always record which build a finding refers to.
- [DeonPoncini/swep1r_decomp](https://github.com/DeonPoncini/swep1r_decomp) — frozen Steam-PC Ghidra output and type clarification; repository says it is a reference and not a full original-source translation. Keep read-only; no root license was established in the prior audit.
- [OpenSWE1R/openswe1r](https://github.com/OpenSWE1R/openswe1r) — an open-source PC port/emulation approach. Its README says it still depends on the original game binary and assets, and that Mac/Dreamcast/N64 support is a possible future direction, not current supported targets. GPL-2.0; use for architecture and behavior research, not as a ready-made GameCube port.

### P1 — data formats and tools
- [akopetsch/swe1r-assets](https://github.com/akopetsch/swe1r-assets) — MIT .NET reader/writer for PC model/spline/sprite/texture blocks, including intended bit-identical no-op reserialization. Best first candidate for a controlled format test when lawful local PC files are available.
- [OpenSWE1R/swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) — GPL-2.0-or-later parsers/extractors for spline, sprite, texture, saves and strings. The README explicitly labels its `decompress.c` “Comp” model-block chunks as N64-only. This is useful evidence that platform-specific handling exists, not proof every other parser supports N64.
- [louriccia/blender-swe1r](https://github.com/louriccia/blender-swe1r) — GPL-3.0 Blender import/export work. Main-branch support and experimental branch changes must be reported separately; do not treat an unmerged branch as released functionality.
- [louriccia/SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods) — useful unpack/repack workflow examples. Do not redistribute its payload assets; repository-wide licensing/provenance was not established in the previous audit.
- [Olganix/Sw_Racer](https://github.com/Olganix/Sw_Racer) — older GPL-2.0-or-later model-block conversion tooling; secondary corroboration only.

## Official/reference sources

- [StarWars.com — Racer legacy overview (2020)](https://www.starwars.com/news/star-wars-episode-i-racer-legacy): supports high-level feature targets such as upgrades, shortcuts, split-screen play and hazards; it is not an internal implementation specification.
- [StarWars.com — producer interview (2020)](https://www.starwars.com/news/star-wars-episode-i-racer-interview): official retrospective context on the N64 release and later control refinements. Do not treat modern re-release controls as identical to 1999 console controls.
- [Steam product page](https://store.steampowered.com/app/808910/STAR_WARS_Episode_I_Racer/): official current PC storefront metadata; useful for product/re-release facts, not reverse-engineering details.

## Work method — one active question at a time

For each question:
1. State the gameplay/system question and why it matters to GameCube.
2. Identify exact versions/builds and source repositories before looking at implementation.
3. Collect static code/symbol evidence from at least one repository; seek independent corroboration from another repo or official source.
4. Record the finding, evidence class, source commit/build, confidence, unknowns and a minimal validation scenario.
5. Compare the relevant Boonta code/tests only after the behavior is understood.
6. Implement only when a real gap is demonstrated. Keep the 80/20 ratio: 8 research/reverse-engineering blocks per 2 implementation, tests or integration blocks.
7. No broad parallel tasks, no unverified claims, no copyrighted game assets/binaries committed to public repo.

## Evidence labels

- **DOCUMENTED** — written in a source, not independently verified.
- **STATIC-ANALYZED** — code, symbols or file structure inspected.
- **RUNTIME-OBSERVED** — behavior observed on an identified original build.
- **CROSS-PLATFORM-COMPARED** — same scenario measured on at least two identified platform/build combinations.
- **TARGET-ACCEPTED** — repeatable GameCube/Wii target test passed.
- **UNKNOWN** — version, provenance or evidence is missing.

Never promote a documented or static finding to runtime-verified. Never treat PC evidence as console evidence.

## First research question

**Platform parity inventory:** establish which tracks, racers, race modes, split-screen options, upgrade systems, shortcuts and hazards are confirmed across PC, N64 and Dreamcast, using official product material first and version-pinned repository/runtime evidence second. Create a parity table with columns for platform/build, feature, evidence/source, confidence and unresolved questions. Do not begin a new implementation until the inventory reveals a concrete gap in Boonta.
