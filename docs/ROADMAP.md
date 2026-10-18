# Boonta Reborn 88 – Project Roadmap

Last updated: 2026-10-18

**Product goal**  
Make *Star Wars: Episode I – Racer* (1999) playable on GameCube and/or Wii through reverse engineering, decompilation, original-data recovery/conversion, and native porting. The project is unofficial; the original release did not have a dedicated native GameCube/Wii edition.

**Resource rule:** at least 80% of engineering effort is reserved for the reverse-engineering/recovery/porting path and reuse of community tools, research and mods. New bespoke improvements are secondary. See the [reverse-engineering and native-port plan](REVERSE_ENGINEERING_PLAN.md).

**Longer-term possibilities**
After the playable race and essential racing content are established, the project may pursue stronger visual presentation, additional original or rights-cleared tracks and pods, bonus modes, and optional content packs. “HD++ Remaster” and “HD+++ Premium” are internal ambition labels, not promises or descriptions of the current build. A broader Racer-inspired experience remains a distant possibility subject to feasibility and rights.

**Platform reality:** HD++ and HD+++ Premium describe quality and scope, not native HD video output on GameCube/Wii. Console builds must fit legacy hardware and video-output limits. A true-HD-resolution edition would require a separate, more capable target and remains optional.

Unofficial fan/homebrew project, not affiliated with or endorsed by the original rights holders.

---

## Non-negotiable development priority

**Follow this order. At least 80% of effort must support the original-game recovery and porting path:**

1. **Reverse-engineer and inventory.** Identify exact game versions, executable/data containers, file formats, runtime systems and existing project work; maintain a provenance/licensing ledger.
2. **Recover and convert original data.** Build reproducible parsers/converters for real track, pod, texture, collision and race data, starting with the minimum needed for one course. Keep raw evidence separate from derived outputs.
3. **Understand and port the runtime.** Use disassembly/decompilation and observed behavior to identify the minimum original-game systems needed for native GameCube/Wii integration. Reuse proven community tooling and compatible mod work before writing replacements.
4. **Prove one complete race.** Use recovered original data and a configured controller in visible Dolphin to complete three laps, finish, reset and restart. Headless tests alone are not acceptance.
5. **Improve only after the core path.** Prefer existing mods and upstream community work for visual/gameplay upgrades. New tracks, pods, modes or bespoke polish are stretch goals, not the main work.

Use **“Make it work, make it good, make it fast”** in that order: first prove correct end-to-end behavior, then improve quality and maintainability, and only then optimize measured bottlenecks. This is a development gate, not permission to skip testing.

---

## Phase 0 – Foundations

**Status: a procedural GX prototype and CI are in place; original-game data recovery, native integration and manual acceptance remain the central work.**

- [x] Clean-room procedural GX prototype.
- [x] Basic driving, boost/heat, rivals, lap system and HUD.
- [x] Native DOL/ELF build, artifact validation and CI.
- [x] Host tests for deterministic gameplay, pause/reset, steering, collisions and state boundaries.
- [x] Dolphin headless process smoke.
- [x] Automated D-pad left/right and analog-stick left/right steering diagnostics.
- [x] Automated Y-reset scenario with a visible HUD-state assertion.
- [x] Scripted Start pause/resume visible-state checks passed on PR #180 head in [run #38954611194](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38954611194).
- [x] Original source-authored indexed player-pod mesh and 16×16 RGB8 texture exported deterministically to native GX mesh/tiled RGB565 headers ([PR #203](https://github.com/Master-Chiken/boonta-reborn-88/pull/203), merged).
- [x] Readable `FINISH` label and varied procedural canyon skyline integrated ([PR #202](https://github.com/Master-Chiken/boonta-reborn-88/pull/202), [PR #204](https://github.com/Master-Chiken/boonta-reborn-88/pull/204), merged).
- [x] Scripted three-lap finish-banner and orange `FINISH`-label pixel checks passed on PR #204 head in [run #39057247310](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39057247310); this was DTM-driven, not a manual race.
- [ ] **Manual controller + live finish/reset/restart acceptance — current and highest-priority gate.**
  → See [`NEXT_MILESTONE.md`](NEXT_MILESTONE.md) and [current test evidence/status](GAMECUBE_FIRST_RENDER_STATUS.md).

Automated movies and rendered frames prove only the specific scripted responses they test. They do **not** establish live-controller playability, longer-session stability or physical-console compatibility.

---

## Phase 1 – Reverse engineering and original-data pipeline

**Current primary engineering phase. Reserve at least 80% of effort for this path and reuse community work wherever compatible.**

- [ ] Inventory the exact original release(s) available for analysis, platform/version, file layout and hashes; record the chosen first target (GameCube or Wii).
- [ ] Audit this repository and relevant public GitHub/modding projects for existing parsers, decompilation notes, format documentation and conversion tools.
- [ ] Maintain a source ledger with upstream URL/revision, license, provenance, relevant paths, dependencies and tested status.
- [ ] Identify and document the original executable, data containers, compression, endianness, indexes and asset relationships.
- [ ] Use Ghidra and suitable tools to map key runtime functions, strings, file loading, input, physics, track initialization, rendering and race progression; label findings confirmed/inferred/unknown.
- [ ] Build reproducible read-only inspection and extraction tools, then convert one real race-critical data item into a documented intermediate format.
- [ ] Keep proprietary game dumps/assets and unclear third-party material out of the public repository; use lawful local inputs where needed.

**Exit criteria:** a reproducible source/version inventory; a documented, tested parser or extractor for at least one real original data format; and a source-to-output trace showing exactly how a recovered item was identified and converted.

---

## Phase 2 – Native runtime integration and playable race

**Use recovered original data and reverse-engineering evidence. Do not mistake the procedural test harness for the port itself.**

- [ ] Load a recovered course layout or other race-critical data through the documented conversion pipeline.
- [ ] Identify which original runtime behaviors can be reused, reconstructed from evidence, or temporarily substituted to unblock the target port.
- [ ] Integrate the smallest useful end-to-end slice into the GameCube/Wii build: real recovered data, rendered track, controllable pod, collision and race progression.
- [ ] Prefer adapting proven community tools/mods and existing code where their license, provenance and target compatibility are verified.
- [ ] Keep format fixtures and conversion tests deterministic; track every generated asset back to its source and conversion step.
- [ ] Validate controls, handling, boost/heat, rival interactions, laps, finish, pause, reset/restart and sustained stability in visible Dolphin with a human-controlled session.
- [ ] Record exact tested commit, emulator version/backend, controller mapping, evidence and any known limitations. Physical hardware is a separate acceptance target.

**Exit criteria:** one recognizable race using data recovered through the documented pipeline; a complete manually controlled three-lap race; finish, reset and restart working; and reproducible evidence. CI/headless smoke or scripted DTM alone is insufficient.

---

## Phase 3 – Community mods and remaster polish

**Begin only after Phase 1 is accepted and Phase 2 has a clear, working content foundation.**

- Improve original or rights-cleared pod and track visuals, materials, effects, animation and environment readability.
- Refine camera presentation, HUD legibility, menus and visual feedback without harming responsiveness.
- Profile and optimize rendering and memory use against actual GameCube and Wii constraints.
- Define exactly what “HD” means for each target. Console output, replacement assets, rendering changes and emulator upscaling are not equivalent.
- Validate performance separately on each intended target; do not promise native 720p/1080p output on legacy hardware.

**Exit criteria:** measured visual improvements that preserve accepted gameplay and meet target-specific performance budgets.

---

## Phase 4 – Bonus content and DLC-style stretch goals

**Optional and last in priority. These ideas must not block Phases 1–3.**

- New original or provenance-cleared tracks and pods.
- Bonus modes such as Time Trial or Versus, plus quality-of-life options.
- Additional content packs or DLC-style expansions.
- The aspirational HD+++ Premium tier or a broader Racer-inspired remake-style experience, only if technically feasible and rights-compatible.
- Wii-specific enhancements where testing demonstrates a real benefit.

Treat these as future possibilities, not implemented features or commitments. Reassess scope only after the core game and original content are in good shape.

---

## Parallel / Restricted Track

**Step 102 source archive** remains under strict import hold until full provenance, authorship and licence review is complete. No commercial ROMs, extracted proprietary assets, or unclear code may enter the public repository. Research findings may guide clean-room implementation but do not automatically grant permission to copy source or data.

---

## Engineering rules

1. **Gameplay before content; original content before graphics; graphics before bonuses/DLC.**
2. **Make it work, make it good, make it fast — in that order.**
3. One coherent, manually verified playable slice before broad expansion.
4. Keep CI green and report exactly what each check proves; automated tests, compilation, headless startup, scripted rendering, interactive play and hardware testing are different gates.
5. Interactive playability matters more than feature, branch or PR count.
6. Clean-room first; publish only original or redistribution-cleared code/assets.
7. No automatic merges, no force-pushes to another contributor’s branch, and no destructive cleanup of history.
8. Legal caution over speed.

## How to follow progress

- Current acceptance gate → `docs/NEXT_MILESTONE.md`
- Build/runtime evidence → `docs/GAMECUBE_FIRST_RENDER_STATUS.md`
- Overall plan and mandatory priority order → this file

## Focused gameplay corrections currently under review

As of 2026-10-18, these targeted fixes are open pull requests, not yet merged into `main`:

- [PR #214 — width-aware rail collision](https://github.com/Master-Chiken/boonta-reborn-88/pull/214): make the collision/recovery boundary follow the rendered rail for narrow, reference-width and wide track segments.
- [PR #215 — analog steering deadzone test reliability](https://github.com/Master-Chiken/boonta-reborn-88/pull/215): keep the DTM steering stimulus active long enough for the diagnostic to find the visible Dolphin window, with a regression test around the former 600-frame boundary.
- [PR #216 — rival overtake/contact thresholds](https://github.com/Master-Chiken/boonta-reborn-88/pull/216): avoid premature overtake detection while a rival is still alongside and clarify the lateral-contact threshold.

Their automated checks are useful evidence for the covered code paths, but they do not close the manual-controller acceptance gate in [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126). Keep the PRs separate until they have been reviewed and the visible Dolphin test is recorded.
