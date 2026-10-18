# Reverse-engineering and native-port plan

Last updated: 2026-10-18

## Mission

The main engineering objective is to make *Star Wars: Episode I – Racer* playable on GameCube and/or Wii by understanding the original game's executable behavior and data formats, then rebuilding or adapting the necessary components for the target platform. This is primarily a reverse-engineering, decompilation, data-recovery, format-conversion, and porting project—not a from-scratch racing-game design exercise.

**Capacity rule:** at least 80% of engineering effort should support the original-game recovery/porting path. Improvements should normally reuse proven community work, existing mods, documented tools, and compatible open-source pipelines. New bespoke gameplay or graphics systems are justified only when they unblock the port or when no suitable reusable solution exists.

## Workstreams

### 1. Establish the source and target matrix

- Identify the exact original release(s) available for lawful analysis (platform, region, version, executable and data-file hashes).
- Record which target is first: GameCube, Wii, or both. Prefer one demonstrable target path before maintaining two.
- Inventory the repository's existing reverse-engineering work, scripts, assets, file-format notes, and open pull requests.
- Maintain a source ledger for community repositories, mods, tools and research: URL, license, upstream commit/release, relevant paths, dependencies, tested status, and any redistribution restrictions.
- Do not assume a mod or GitHub repository is compatible merely because it concerns the same game.

### 2. Recover and document original data

- Work from a copy the contributor is entitled to analyze; document extraction steps without committing commercial game dumps or unlicensed assets.
- Identify archive/container structures, compression, endianness, alignment, indexes, checksums, and version differences.
- Prioritize the minimum data needed for one original race: course geometry/layout, player pod, textures/materials, collision data, race parameters, rivals, HUD and essential audio.
- Write small inspection and extraction tools that produce reproducible manifests and hashes.
- Preserve raw evidence separately from converted outputs; never silently overwrite unknown formats.

### 3. Reverse-engineer runtime behavior

- Map executable sections, symbols, strings, imports, data references, and major update/render/input loops.
- Use Ghidra and other appropriate disassembly/decompilation tools to produce hypotheses, then validate them against observed behavior and data references.
- Maintain function notes and confidence labels: confirmed, strongly inferred, or unknown.
- Prioritize file loading, track/pod initialization, physics/handling, race/lap progression, rendering, controller input and audio.
- Separate facts about the original executable from assumptions in the current procedural prototype.

### 4. Reuse community work first

For every relevant public mod, repository or tool:

1. Verify its actual source, license, maintenance state and provenance.
2. Identify reusable parsers, format specifications, conversion scripts, decompilation notes and compatibility patches.
3. Pin the upstream revision and record any local adaptation.
4. Add a minimal reproducible test or fixture for each imported tool/format behavior.
5. Keep proprietary assets and code out of the repository unless redistribution is explicitly authorized; provide documented local extraction/import workflows where appropriate.

### 5. Build a data-to-target pipeline

- Define an intermediate representation for recovered tracks, pods, materials, textures and race parameters.
- Build deterministic converters from verified source formats into GameCube/Wii-compatible structures.
- Prefer a thin compatibility layer around recovered behavior over reimplementing systems without evidence.
- Add one integration milestone at a time: load a real recovered data item, render it, move through a real track layout, then complete a race.
- Keep provenance metadata beside every generated output so the build can explain where each input came from and how it was transformed.

### 6. Prove progress end to end

A successful compiler run or a headless Dolphin smoke test is not a playable port. Acceptance must show the exact tested commit and cover:

- a recognizable course/data set derived through the documented pipeline;
- controllable pod movement using a configured controller;
- road/collision behavior and race progression;
- a complete three-lap race, finish, reset and restart;
- logs and evidence sufficient for another contributor to reproduce the test.

Physical GameCube/Wii compatibility is a separate test from Dolphin.

## Priorities and gates

1. **P0 — inventory and source ledger:** establish what is already available upstream and what the project can legally/reproducibly reuse.
2. **P1 — one original data path:** document and parse one real source format, then convert a minimal race-critical item.
3. **P2 — executable understanding:** map the original runtime components needed to consume that data and identify what can be reused, reconstructed or replaced.
4. **P3 — native integration:** connect recovered data and runtime behavior to the GameCube/Wii build.
5. **P4 — complete playable race:** pass the visible, manual Dolphin acceptance checklist.
6. **P5 — community improvements:** apply compatible existing mods and only then consider additional polish or new content.

The existing procedural GX prototype is useful as a test harness and temporary fallback. It is not a substitute for recovering the original game's content and behavior.

## Legal and provenance boundary

This is an unofficial fan project. Reverse-engineering notes and original tools should be separated from copyrighted game data. Do not commit full disc images, commercial executables, extracted proprietary assets, or third-party material whose redistribution rights are unclear. Record licenses and upstream attribution, and use local user-provided extraction inputs where that is the appropriate workflow.

## Current status

This document defines the intended work strategy; it does not claim that the original executable has been decompiled, that commercial assets have been recovered, or that a complete native port already works. Each claim should be upgraded only when a reproducible artifact and test evidence exist.
