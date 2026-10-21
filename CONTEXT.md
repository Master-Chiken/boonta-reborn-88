# Boonta Reborn 88 — Project Context

**Last checked:** 2026-10-21  
**Purpose:** Paste this file at the start of a new working conversation to restore the project's verified context.

## Project goal

Boonta Reborn 88 is an unofficial, clean-room homebrew project aiming to build an enhanced racing game inspired by *Star Wars: Episode I – Racer* for Nintendo GameCube and Wii. It does not have to reproduce every detail of the N64 release; the priority is a reliable, enjoyable game that works on the target hardware.

- **PC release:** primary research/reference source for game behavior, data structures, and file-format investigations.
- **Dreamcast release:** secondary console reference.
- **N64 release:** additional reference, not the required implementation target.
- **Current runtime:** `gamecube-demo/`, an original prototype using devkitPPC/libogc and native GX rendering.

The repository currently declares the MIT License for its own code. That license does **not** grant rights to commercial game assets or to code/data from third-party projects.

## Verified project status

### What exists

- A native GameCube DOL/ELF build path.
- An original prototype scene with a procedural desert course, canyon geometry, rival pods, and a source-authored player mesh/texture.
- Prototype systems for steering, throttle/brake, boost/heat, lap timing, pause, and reset.
- Automated host-side C/Python checks, artifact validation, and scripted Dolphin diagnostics for selected states.
- Public research dossiers and source-preservation records.

### What is not yet proven or integrated

- **The prototype has not passed manual playability acceptance.** A person has not yet documented a complete three-lap race using a configured controller in visible Dolphin.
- The finish/reset/restart flow, long-session stability, and input behavior still need human-operated acceptance on an exact identified build.
- Physical GameCube/Wii compatibility has not been demonstrated.
- The commercial game's original tracks, models, textures, sounds, and other extracted assets are not integrated into the clean-room prototype.
- A successful build, host test, headless emulator start, scripted input movie, or rendered screenshot is not proof of manual playability.

Canonical checklists:
- [Issue #126 — interactive three-lap acceptance](https://github.com/Master-Chiken/boonta-reborn-88/issues/126)
- [Current milestone checklist](docs/NEXT_MILESTONE.md)
- [GameCube prototype status/evidence](docs/GAMECUBE_FIRST_RENDER_STATUS.md)
- [Build guide](docs/BUILD_GUIDE.md)

## Current engineering direction

The latest owner-confirmed research direction is approximately **80% evidence-led reverse engineering and 20% implementation, tests, integration, and project management**. Keep one active research question and one canonical work queue. Do not start parallel research queues or implementation tasks that overlap.

- Canonical research queue: [issue #226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226).
- Tester recruitment: [issue #250](https://github.com/Master-Chiken/boonta-reborn-88/issues/250); detailed acceptance record: [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126).
- Research operating/documentation PR: [PR #242](https://github.com/Master-Chiken/boonta-reborn-88/pull/242), open/draft/unmerged as last checked. Live GitHub metadata on 2026-10-21 reports head `8e8afa33ebf72722c3342b5bdeb6383ff3e326d5`; older prose in the PR description still refers to `58eda2d389a0201d7f02c3e68d344e017564cf7d` and must not override the live head.
- Reuse inventory PR: [PR #246](https://github.com/Master-Chiken/boonta-reborn-88/pull/246), open and unmerged as last checked.
- Project dashboard: [issue #156](https://github.com/Master-Chiken/boonta-reborn-88/issues/156).

Do not merge, close, auto-merge, delete, or force-push an existing PR or branch unless the owner explicitly requests that action. Do not merge old branch histories wholesale. Use a short-lived task branch and a reviewable PR; documentation normally targets `main`, while gameplay changes follow the repository's current `dev`/review rules.

## RE-001 — Route and spline progression

**Scope:** understand how route position and progress are represented and advanced, compare the PC reference against the clean-room prototype, and clearly separate evidence from inference. Do not change gameplay code as part of this research unless a separate task is explicitly approved.

### Evidence currently recorded

- The pinned public PC reference is [SW_RACER_RE at `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab). It documents a linked spline cursor and route/progress operations, but several important implementations remain stubs or unavailable as readable source.
- The frozen Steam-PC reference is [`swep1r_decomp` at `d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef). It is read-only evidence, not code to import.
- The public N64 static-recompilation navigation reference is [`sp00nznet/racer` at `11f6f70469f995304422f2209a47e9c2df5ff6d0`](https://github.com/sp00nznet/racer/tree/11f6f70469f995304422f2209a47e9c2df5ff6d0). A generic symbol or an auto-detected address label is not proof of a function's semantic purpose.
- The N64 lap HUD's data flow for the current/configured lap fraction and the `FINAL LAP` selector has been traced at local static-code level and recorded in issue #226/PR #242. This is not runtime validation.
- A public N64 symbol table places address `0x80080DB4` inside the recorded range for `func_80080BEC`; it does not identify `0x80080DB4` as a separately named semantic function. Treat it as an address inside the containing function unless cross-references prove a finer boundary.
- The N64 manager-to-results-screen transition remains unresolved. Generic `Fini`/`Abrt` tags and phase changes alone do not prove selection of a results renderer or scene.
- Public Dreamcast binary-string research contains names such as `OUT_SPLINEBLOCK.BIN`, `OUT_MODELBLOCK.BIN`, `OUT_SPRITEBLOCK.BIN`, and `OUT_TEXTUREBLOCK.BIN`. Matching filenames do not establish that Dreamcast and PC binary layouts are identical.
- Proposed edge-case tests, including the `splineSampleIndex == 0` sentinel ambiguity, are hypotheses/test designs until executed against valid evidence. Do not call them confirmed bugs.

### Next bounded research step

Continue only RE-001. Seek positive evidence connecting the N64 “all local participants finished” condition through the manager phase/state writer to a positively identified results UI/resource/scene selection. Record exact sources/revisions, direct observations, inference, counter-evidence, unknowns, and the smallest next check. If the necessary local disassembly/xrefs are unavailable, state the blocker and stop rather than guessing.

## Reuse, licensing, and provenance

- Review the reuse inventory proposed in [PR #246](https://github.com/Master-Chiken/boonta-reborn-88/pull/246). It is a separate open PR so the mainline file may not exist until it is merged.
- A source repository can be useful for **research** without being safe to copy into Boonta.
- Check exact revisions, file-level notices, dependencies, compatibility with the project's MIT license, and redistribution obligations before copying code.
- Known unresolved areas include OpenGX's overall/file-level licensing and compatibility, conflicting licensing statements in Sw_Racer, and the license/provenance of scripts and assets in SWE1R-Mods.
- swe1r-tools reports GPLv2-or-later for its source. SW_RACER_RE reports AGPL-3.0. These licenses do not grant rights over commercial game assets.
- decomp.anything is an optional future research tool, not a requirement. Its repository declares MIT at the checked revision, but its prerequisites, third-party components, free-only workflow, and practical usefulness for this project still need review before adoption.
- Never commit or upload ROMs, disc images, BIOS files, extracted commercial models/textures/audio, raw game data, or content of unclear provenance to the public repository, issues, CI artifacts, or AI services. Keep legally held local reference files local; do not ask the owner to upload them.

## Source shelf and historical research leads

These links preserve previously identified avenues. They are **leads to evaluate**, not a claim that their code, data, or licenses are approved for reuse.

### PC reference and file-format tools

- [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) — partial PC research/reimplementation; retain the pinned commit listed above when making a specific claim.
- [Steam-PC decompilation reference](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef) — read-only comparison source; never copy its code into Boonta.
- [Sw_Racer (Olganix)](https://github.com/Olganix/Sw_Racer) and [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) — format/tooling leads with license and per-format limitations described in PR #246.

### N64 tooling and navigation

- [N64Recomp](https://github.com/N64Recomp/N64Recomp) — general static-recompilation tooling; not a decompilation of Racer by itself.
- [sp00nznet/racer at pinned revision](https://github.com/sp00nznet/racer/tree/11f6f70469f995304422f2209a47e9c2df5ff6d0) — public N64 static-recompilation/symbol-navigation reference. Generic symbols and detected address labels do not prove semantics.

### Dreamcast reverse-engineering and tooling leads

- [Dreamcast Disassembly, Debugging and Decompilation Diaries](https://github.com/AltoRetrato/Dreamcast-Disassembly-Debugging-and-Decompilation-Diaries)
- [tbg-decomp](https://github.com/lhsazevedo/tbg-decomp)
- [recv-dc-decomp](https://github.com/fmil95/recv-dc-decomp)
- [Flycast](https://github.com/flyinghead/flycast) — emulator/reference implementation; not proof of original Racer data structures.
- [gditools3](https://github.com/AltoRetrato/gditools3) — GD-ROM tooling lead; use only with lawfully held local media.
- [mc.pp.se/dc](https://mc.pp.se/dc/) — Dreamcast technical documentation.
- [Dreamcast extracted-string index](https://github.com/lhsazevedo/dc-redump-extracted-data/blob/832abe37573642c56298d3efd006f72416391755/output/Star%20Wars%20-%20Episode%20I%20-%20Racer%20%28USA%29/bins/1ST_READ.BIN.strings.txt) — string names are a research clue, not reusable game assets and not proof of PC/Dreamcast format identity.
- `borer.lol` — previously mentioned as a possible lead; its role, license, and relevance have not been verified. Do not rely on it until checked.

Before relying on any of these sources, record the repository or page, exact revision/date, platform, relevant file/claim, license/provenance, and limitations. Keep commercial binaries and extracted content out of Boonta, issues, CI artifacts, and AI services.

## Working rules for AI-assisted contributions

1. Read the current branch, issue, PR, and source state before claiming something is current.
2. All public repository documentation and new issues must be written in English. Explain significant published changes separately in French in the chat.
3. Say **“unknown” / “to verify”** when evidence is insufficient. Do not invent licenses, commands, supported features, test results, or platform parity.
4. Never claim the game is playable until manual controller acceptance is documented.
5. Prefer browser-based research and GitHub editing when practical; do not require the owner to install local tools for documentation-only tasks.
6. Do not edit gameplay code, alter repository settings, enable paid services, trigger destructive workflows, merge PRs, delete branches, or enable auto-merge without explicit authorization.
7. Distinguish verified facts, reasonable inference, and unknowns in every research result.
8. No test is considered run merely because a command is documented. Record the exact commit and evidence for each test actually executed.

