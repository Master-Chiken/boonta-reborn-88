# RE-002 — PC / Nintendo 64 / Dreamcast source matrix

> **Queue status: PARKED — reference index only.** The sole active research question is [RE-001 in issue #226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226). This file preserves existing public-source leads for later; it does **not** authorize a second active research workstream. Do not execute the future sequence below until RE-001 is resolved or explicitly blocked.

**Status:** research inventory; no game code changed  
**Date:** 2026-10-20  
**Purpose:** use the original released game versions as behavioral references, then use public reverse-engineering repositories to explain what can be observed. This is not a claim that original commercial source code is public.

## Decision

Treat the original PC, N64 and Dreamcast releases as three separate evidence targets. The PC version is currently the strongest code-level reference because public projects document its Windows executable. N64 and Dreamcast are essential comparison targets, but this audit has **not yet found a verified public, complete source decompilation for either console version**.

Do not infer that a PC implementation is identical on a console. For every mechanic, record the platform, game revision, observation, source/repository evidence, confidence and test still needed.

## Source priority

| Priority | Source | Platform/evidence | Use | Confidence / limit |
|---|---|---|---|---|
| P0 | [Original PC release — inspected through SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | Windows executable, public symbols, function analysis, Ghidra scripts and hooks | Primary code-level behavioral oracle for handling, race progression, AI, splines, collision, HUD, camera and loading | Partial analysis/reimplementation, not full source. Repository declares AGPL-3.0; use as a research reference unless a separate license decision authorizes code reuse. |
| P0 | [Original Nintendo 64 release — N64-specific tool evidence](https://github.com/OpenSWE1R/swe1r-tools) | The tool README explicitly says its “Comp” model-block decompressor is for data found in the N64 version; community guide also documents Expansion Pak and Rumble Pak behavior | Build a console-specific checklist for memory/texture limits, rendering, controller behavior, vibration, sound, track geometry and differences from PC | This is tooling/documentation, not an N64 source decompilation. No N64 binary/ROM should be uploaded or committed. |
| P0 | [Original Dreamcast release — contemporary developer interview](https://www.timeextension.com/features/the-making-of-star-wars-episode-1-racer-maybe-we-cant-make-a-great-racing-game-but-we-can-make-an-excellent-toy) | Developer recollections describe the Dreamcast port, hardware, cutscenes, music and late project trade-offs; contemporary preview also records planned enhancements | Treat Dreamcast as its own target for visual fidelity, frame pacing, audio/music, cutscenes and controls; use the retail version as the final authority when lawful access exists | Interviews/previews are secondary evidence and may describe plans rather than the shipped build. No verified public Dreamcast code decompilation found in this pass. |
| P1 | [OpenSWE1R/swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) | GPL-2.0-or-later; parsers for spline, sprite, texture, save/profile/string data, plus N64 “Comp” chunk note | Cross-check format hypotheses and identify platform-specific compression branches | Old project (last inspected history 2018); not a universal cross-platform extractor. Do not copy GPL code into the MIT project without a deliberate licensing decision. |
| P1 | [swe1r-assets](https://github.com/akopetsch/swe1r-assets) | MIT library for PC `data/lev01` model/spline/sprite/texture blocks; documents bit-perfect no-op reserialization | Candidate for a PC-only no-op round-trip experiment after a lawful local test input is available | PC block support does not prove N64 or Dreamcast compatibility. Library licence does not cover original game assets. |
| P1 | [OpenSWE1R/swe1r-re](https://github.com/OpenSWE1R/swe1r-re) | Earlier Windows-PC function documentation and analysis | Cross-check PC function hypotheses and binary-version assumptions | Partial/deprecated, Windows-focused. |
| P1 | [Frozen Steam PC decompilation](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef) | Read-only Ghidra-derived PC function/type reference | Cross-check specific addresses and types against SW_RACER_RE | README says it is not a complete source translation; no root licence was identified in the reviewed snapshot. Read-only; no code copying. |
| P2 | [Official Nintendo Japan N64 product page](https://www.nintendo.co.jp/n01/n64/software/nus_p_nepj/index.html) | Official platform/product reference | Establish official N64 identity and basic release context | Not a source-code repository and not enough to establish low-level runtime behavior. |
| P2 | [PC manual (archived scan)](https://files.replacementdocs.com/Star_Wars_-_Episode1_Racer_-_AU_Manual_-_PC.pdf) | Manual rules for tournament progression, Free Play settings, upgrades and race configuration | Turn documented intended behavior into a test checklist | A manual describes intended behavior, not necessarily bugs/edge cases or every platform version. Prefer an official manual when available. |

## Confirmed comparison leads (not yet target-verified)

The following are useful test hypotheses from public documentation, not a substitute for testing the exact retail builds:

- **PC:** Windows executable analysis is available; the README for SW_RACER_RE states that the project documents/reimplements selected functions, not a full decompilation.
- **N64:** its tool ecosystem explicitly identifies an N64-specific “Comp” model-block compression path. Public player references document Expansion Pak and Rumble Pak support. Verify the actual cartridge/revision and Expansion Pak state before comparing graphics or performance.
- **Dreamcast:** developer recollections report high-resolution graphics and the return of prerendered cutscenes compared with the N64 release; the shipped game must be checked before treating interview statements as implementation requirements.
- **Multiplayer, audio, cutscenes, texture detail, controller mapping and performance** are likely platform differentiators and should be tested separately, rather than grouped into a generic “console version” row.

## Required evidence format

For each finding, use one row in the research ledger:

`ID | subsystem | platform | exact version/revision | evidence type | observation | source URL + commit/page | confidence | reproduction steps | open question`

Allowed evidence types:
- `CODE` — directly supported by inspected code/decompilation.
- `RUNTIME` — directly observed in the exact game build.
- `OFFICIAL-DOC` — official manual/product documentation.
- `DEVELOPER-INTERVIEW` — developer recollection; useful but not definitive.
- `COMMUNITY-REPORT` — hypothesis to verify.
- `INFERENCE` — reasoned conclusion, explicitly not verified.

Allowed confidence states:
- `CONFIRMED`, `SUPPORTED`, `HYPOTHESIS`, `UNKNOWN`, `CONFLICTING`.

## Parked future sequence — not active

1. **PC subsystem map:** continue from RE-001 route/spline/progress and map the next highest-value areas in SW_RACER_RE: handling/physics, collision, AI/racing line, boost/heat, track loading, camera and race completion. Pin each function to an exact commit and binary revision.
2. **N64 evidence audit:** inspect only public tool/source repositories and published documentation for N64-specific formats, memory/rendering constraints, controller and rumble behavior. Search for a genuine N64 reverse-engineering project before assuming one exists.
3. **Dreamcast evidence audit:** search for public Dreamcast-specific repositories, format notes and developer documentation. Separate announced features from the retail release. If no code-level source is found, record that as an evidence gap rather than filling it with PC assumptions.
4. **Cross-platform behavior matrix:** compare one mechanic at a time across PC/N64/Dreamcast, then mark what remains unknown for GameCube/Wii. Do not use a PC-only finding as proof of target-console behavior.
5. **Only after the research:** propose a small independent implementation or test that addresses one measured gap. No broad rewrite and no third-party code copied into Boonta by default.

## Handling and licensing boundaries

- “Official source” here means the original released game/build and official documentation as the behavioral reference; it does **not** mean that the original source code has been located.
- Never upload or commit commercial executables, ROMs, disc images, BIOS files or extracted proprietary models, textures, audio or track geometry.
- Public repositories may be read and cited, but their code licences remain binding. A source-code licence does not grant rights to game assets.
- Use lawful local game copies for runtime comparisons; keep extracted content local-only unless redistribution rights are explicit.
- Step 102 is intentionally outside this research sequence and is not a blocker for this platform/source audit.


**Activation gate:** all items in this section remain backlog candidates. No one should pick them up in parallel while RE-001 is active; the owner must explicitly select a single next question first.
