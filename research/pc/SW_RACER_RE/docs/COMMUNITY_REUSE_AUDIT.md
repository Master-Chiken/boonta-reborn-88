# Community Reuse Audit — SW_RACER_RE

**Audit date:** 2026-10-16  
**Scope:** Public community repositories and the current default branch. This is a preliminary technical audit; no external source code or game assets were imported.

## Executive summary

Use prior work as **references, test oracles, and sources of regression cases** before considering direct code imports.

A GitHub compare of `tim-tim707/SW_RACER_RE:master` against `Master-Chiken/SW_RACER_RE:master` reports **27 commits ahead and 0 behind** at the time of this audit. The working fork already contains the upstream history through the comparison point, plus 27 commits of its own. Do not re-apply upstream changes already in the common history.

The default branch is primarily a **Windows PC decompilation / DLL-hook and modding project**. The clean-room GameCube/Wii prototype is tracked separately at [`Master-Chiken/boonta-reborn-88`](https://github.com/Master-Chiken/boonta-reborn-88), whose README and status docs describe the native DOL/ELF build and CI/Dolphin checks. Keep its results and completion estimates separate from this PC hook/decompilation repository: a prototype elsewhere is not code in this branch, and automated DTM/render tests are not the same as live-controller or hardware acceptance. In this audit, the missing `gamecube-demo/README.md` and `docs/NEXT_MILESTONE.md` paths on this repository's default branch are therefore a repository-boundary distinction, not evidence that the other project does not exist.

## 1. Fork comparison

- Upstream: https://github.com/tim-tim707/SW_RACER_RE
- Working fork: https://github.com/Master-Chiken/SW_RACER_RE
- Compare: https://github.com/tim-tim707/SW_RACER_RE/compare/master...Master-Chiken:master

The 27-commit delta includes a custom-track catalog downloader/browser, manifest validation and content hashes, atomic manifest publication, a content store, virtual model/spline/texture blocks, asset extraction and validation tools, hardened model parsing, regression tests, and fixes for cursor policy, cinematic audio, and HD replacement defaults. It also adds governance and fork-first contribution documentation.

**Decision:** keep these additions and test them. Re-compare before future syncs; do not merge identical work twice.

## 2. External projects and practical value

### A. Upstream decompilation — highest-priority reference
**Repo:** https://github.com/tim-tim707/SW_RACER_RE

The README reports 1,518 / 2,132 functions analysed (71.2%) as of 2026-06-12. That measures function analysis, not implementation completeness or total project completion.

Use it for function addresses, symbols, behaviour notes, and real custom-track bug histories. Useful regression cases documented in upstream history include:
- bounds-check custom-track block counts and offsets before allocation/read;
- prevent lap-record writes for tracks without save slots;
- invalidate texture caches when switching mapped blocks;
- handle failed model loads without null dereferences or stale custom paths;
- verify custom-track navigation in free play while preserving tournament behaviour.

Our fork is 0 commits behind the comparison point, so inspect whether a fix is already present before porting anything. The history is a source of tests and understanding, not a reason to cherry-pick blindly.

### B. swe1r-assets — best candidate for differential asset tests
**Repo:** https://github.com/akopetsch/swe1r-assets  
**Declared licence:** MIT.

This .NET library reads/modifies/writes model, spline, sprite and texture block files and advertises bit-perfect reserialization when unchanged. Use it as an independent comparison tool on a small set of local, legally obtained game files. Compare our extraction/repack results, offsets, counts and metadata. Treat it as a test oracle first, not a required runtime dependency.

### C. blender-swe1r — artist workflow and round-trip reference
**Repo:** https://github.com/louriccia/blender-swe1r  
**Declared licence:** GPL-3.0; README describes it as work in progress, requires Blender 5.0+, and lists Podd/MAlt import/export as unsupported.

Use it to assess interoperability with community asset-authoring workflows. Do not assume every format or round trip is supported.

### D. swe1r-tools — historical format reference
**Repo:** https://github.com/OpenSWE1R/swe1r-tools  
**Declared licence:** GPL-2.0-or-later; the OpenSWE1R organization marks it deprecated.

Its scripts extract spline, sprite and texture blocks, extract strings, parse save data and handle some model chunks. Compare format assumptions and expected outputs, but prefer our maintained implementation for normal workflows.

### E. SWE1R-Mods — real-world test cases
**Repo:** https://github.com/louriccia/SWE1R-Mods

Contains community track modifications, texture packs and unpack/repack scripts. Use it to derive a local compatibility matrix (for example, reversed/scaled tracks and texture replacements). Check item licences and permissions before copying or redistributing files.

### F. OpenSWE1R — architecture reference, not a drop-in port
**Repo:** https://github.com/OpenSWE1R/openswe1r  
**Declared licence:** GPL-2.0-or-later.

This older PC port combines x86 CPU emulation with a Windows API compatibility layer. Its target differs from both the Windows DLL-hook project and a clean-room GameCube implementation. Learn from behaviour and compatibility decisions; do not transplant its architecture without a separate feasibility review.

### G. OpenJKDF2 — targeted engine-pattern reference
The upstream notes already identify possible similarities between Racer and the Sith/Jedi Knight engine family. Use OpenJKDF2 only when a specific subsystem is relevant. Similarity is a hypothesis to verify, not proof that functions are interchangeable.

### H. swep1r_decomp — frozen decompilation/type reference
**Repository:** https://github.com/DeonPoncini/swep1r_decomp

The README describes a decompilation of the Steam PC version intended to help recover type definitions, function signatures, and DAT/global-variable information for the main decompilation effort. It explicitly says the repository is a reference snapshot and will not be developed further.

**Recommended use:** consult it when an unresolved function signature or structure layout needs an additional cross-check. Treat every type/address as a hypothesis to reconcile against the current upstream symbols and the exact game version; do not cherry-pick the repository as a second active implementation.

### I. Star-Wars-Episode-I-Racer-PCVR — downstream hook-architecture reference
**Repository:** https://github.com/GameOrDie007/Star-Wars-Episode-I-Racer-PCVR  
**Declared licence:** AGPL-3.0.

This downstream fork adds OpenXR stereo rendering, head tracking, a world-locked 2D panel, and Quest controller support on top of the PC hook mod. Its README specifies a 32-bit OpenXR runtime, illustrating that third-party integrations can depend on particular runtime and renderer configurations.

**Recommended use:** treat it as a possible compatibility partner/test target for the Windows PC hook, renderer, and input paths—not as proof of GameCube progress. Compare the fork's integration points and known issues before making renderer/input changes; avoid importing code without reviewing the exact fork revision, licence notices, and dependency requirements.

## 3. Prioritised action plan

### P0 — keep platform scope and runtime claims precise
1. Keep Windows PC decompilation/DLL-hook work in this repository and native clean-room GameCube/Wii work in [`boonta-reborn-88`](https://github.com/Master-Chiken/boonta-reborn-88), with separate roadmaps and completion estimates.
2. Link to the separate project's [interactive acceptance milestone](https://github.com/Master-Chiken/boonta-reborn-88/blob/main/docs/NEXT_MILESTONE.md) when cross-referencing its status; do not imply that its source lives on this PC repository's default branch.
3. For either workstream, define reproducible tests and record real results. Automated rendering/input movies, live visible-manual control, and physical-hardware acceptance are separate evidence levels.

### P1 — convert upstream experience into regression coverage
1. Add or verify tests for truncated/invalid block files, oversized counts, invalid offsets, missing model assets, cache changes between stock/custom tracks, save-record boundaries, and free-play navigation.
2. Build a small local test matrix using stock data and legally obtained community-created test tracks.
3. Re-run the upstream comparison before syncing; port only fixes that are absent and compatible.

### P1 — independently validate our asset pipeline
1. Select representative model, spline, sprite and texture blocks.
2. Compare our extractor/repacker with `swe1r-assets` or documented outputs from existing tools.
3. Check byte-identical unchanged round trips where the format/tool promises that property; document intentional differences otherwise.
4. Record tool versions, input/output hashes and pass/fail results.

### P2 — delegate bounded contributor tasks
- custom-track parser/cache regression tests;
- asset-format documentation and differential testing;
- Blender workflow compatibility checks;
- reproduction and repair of one concrete runtime issue per task;
- GameCube prototype validation after its location and build/run procedure are confirmed.

Use forks and pull requests; retain owner review for merges into `master`.

### P3 — licence and provenance checks before importing code
The working repository declares AGPL-3.0. The projects above declare MIT, GPL-3.0 or GPL-2.0-or-later as noted. Check the actual licence and notices for each file and assess compatibility with the repository and distribution plans before copying code, especially GPL code. Prefer references, behavioural notes, independent tests and compatible small utilities over wholesale imports. Never commit the original game executable or proprietary game assets.

## 4. What is and is not established

**Established:** fork commit delta; broad scope of recent additions; stated function-analysis percentage; advertised capabilities and licences in the referenced project READMEs.

**Not established:** that every feature works in a real game session; compatibility of every tool with every game version; live physical-controller or console compatibility for the separate GameCube prototype; or that external code can be merged without code-level review and tests.

## Recommended next milestone: Independent compatibility and runtime evidence

- checked upstream comparison;
- documented custom-track regression cases;
- at least one independent asset round-trip comparison;
- an independent asset round-trip comparison and a reproducible PC custom-track runtime check in this repository;
- separate from this audit, complete the manual controller/Dolphin acceptance checklist in [`boonta-reborn-88`](https://github.com/Master-Chiken/boonta-reborn-88) before claiming interactive or hardware playability.

Recalculate the overall completion estimate only after collecting these results.
