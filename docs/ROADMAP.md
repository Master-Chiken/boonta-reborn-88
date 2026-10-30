# Boonta Reborn 88 – Project Roadmap

Last updated: 2026-10-21

**Goal**  
Create an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), native on GameCube / Wii, with improved visuals and bonus content.  
Unofficial fan / homebrew project. Clean-room first.

---

## Product strategy — reconstruct first, enhance second

The intended order is now explicit: **use reverse engineering to reconstruct a faithful, playable baseline of the original game before adding the HD++ improvements.** The current procedural GameCube demo is a technical harness, not the intended substitute for the original courses, route system, handling or race flow.

### Stage A — original-faithful playable baseline

- Reverse-engineer the original's route/course representation, pod handling, lap/race state, rivals, collision/recovery, camera, HUD and race flow from version-tagged PC, N64 and Dreamcast evidence where available.
- Implement those behaviors independently for native GameCube/Wii, keeping platform-specific assumptions explicit.
- Establish how original course and model data can be read; use only content the owner can lawfully supply locally, and do not publish or redistribute proprietary assets.
- Validate one representative course from start to finish, then reset and start another race. Do not call the baseline complete while the route/course remains only a procedural placeholder.

### Stage B — improve after the baseline works

- Improve visuals, presentation, handling quality-of-life and performance without silently changing the reference behavior.
- Add extra original or provenance-cleared courses, pods, modes and bonus content as separate, testable work.
- Keep every enhancement distinguishable from the reconstructed baseline so regressions can be identified.

The research target is not “copy PC code into GameCube.” PC source is a source of behavioral evidence; N64/Dreamcast evidence must be evaluated independently, and gaps remain unknown until supported. Upstream code licenses and the project's clean-room policy still apply. Reverse engineering can establish behavior and formats, but it does not itself grant rights to redistribute the original game executable or proprietary assets.

## Phase 0 – Foundations

**Status: prototype foundations and CI are in place; interactive acceptance is still open.**

- [x] Clean-room procedural GX prototype.
- [x] Basic driving, boost/heat, rivals, lap system and HUD.
- [x] Native DOL/ELF build, artifact validation and CI.
- [x] Host tests for deterministic gameplay, pause/reset, steering, collisions and state boundaries.
- [x] Dolphin headless process smoke.
- [x] Automated D-pad left/right and analog-stick left/right steering diagnostics.
- [x] Automated Y-reset scenario with a visible HUD-state assertion.
- [x] Scripted Start pause/resume visible-state checks passed on PR #180 head in [run #38954611194](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38954611194).
- [x] Original source-authored indexed player-pod mesh and 16×16 RGB8 texture are validated and deterministically exported to the GX mesh / tiled RGB565 headers ([PR #203](https://github.com/Master-Chiken/boonta-reborn-88/pull/203), merged).
- [x] Readable `FINISH` label and varied procedural canyon skyline are integrated ([PR #202](https://github.com/Master-Chiken/boonta-reborn-88/pull/202), [PR #204](https://github.com/Master-Chiken/boonta-reborn-88/pull/204), merged).
- [x] Scripted three-lap finish-banner and orange `FINISH`-label pixel checks passed on PR #204 head in [run #39057247310](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39057247310); this was DTM-driven, not a manual race.
- [ ] **Manual controller + live finish/reset/restart acceptance** — required acceptance gate before claiming playability or accepting relevant gameplay changes; it is not a second active research queue.
  → See [`NEXT_MILESTONE.md`](NEXT_MILESTONE.md) and [current test evidence/status](GAMECUBE_FIRST_RENDER_STATUS.md).

The current visual/asset sequence is integrated on `main`: PR #202 (finish label, merge commit `2c632fe3fbe5220c158ede9bc53b7b62842abf20`), PR #203 (source-authored player mesh/texture, merge commit `662bd10368a566f18872ee70e1f95f95f48cafdc`), and PR #204 (varied canyon silhouette, merge commit `72acf968e3214b086b00b77240bb20b889314917`). Their exact-head workflows passed.

The post-merge mainline GameCube workflow [#39062005581](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39062005581), run on the code-bearing merge commit `72acf968e3214b086b00b77240bb20b889314917`, passed the native DOL/ELF build and artifact validation, host pause/reset tests, the 12-second Dolphin Null-backend smoke, and the non-blocking Software Renderer diagnostic. A later main commit `8b7c9a8a1e19e6a14eccc182103120e835400b4b` only updates the root README. The mainline diagnostic is a short capture/steering check, not a full-race run; the three-lap finish and label were separately detected on PR #204 in run #39057247310.

Automated movies and rendered frames prove only the specific scripted responses they test. They do **not** establish live-controller playability, longer-session stability or physical-console compatibility.

---

## Phase 1 – Playable Vertical Slice

**Goal:** one enjoyable circuit that feels good for several minutes.

- Stable, responsive controls and racing feel.
- Stable, pleasant camera.
- Reliable track collision and rail recovery.
- A complete three-lap race with clean finish, pause, reset and restart.
- Stable frame pacing (target 60 fps or a solid 30 fps).
- Basic audio feedback (optional but recommended).

**Exit criteria:** manual controller acceptance is complete in visible Dolphin, a multi-minute session is stable, and evidence is recorded. Physical GameCube/Wii acceptance, if claimed, needs a separate real-hardware run.

---

## Phase 2 – Core Content

- 3–5 original/procedurally authored or provenance-cleared tracks.
- Multiple pods with different stats.
- Improved rival AI.
- Basic menus and HUD polish.
- Minimal sound set (engine, boost, impacts, UI).

## Phase 3 – Remaster & Bonuses

- Visual upgrades (materials, effects, and higher internal resolution where possible).
- Extra modes (Time Trial, Versus, etc.).
- Quality-of-life options.
- Wii-specific improvements if relevant.
- Further polish and stability.

---

## Parallel / Restricted Track

**Step 102 source archive** remains under strict import hold until full provenance, authorship and licence review is complete. No commercial ROMs, extracted proprietary assets, or unclear code may enter the public repo.

---

## Guiding principles

1. **Make it work, make it good, make it fast — in that order.** First prove correct end-to-end behavior, then improve quality/maintainability, then optimize measured bottlenecks.
2. Clean-room first; publish only original or redistribution-cleared code/assets.
3. One coherent playable vertical slice before broad content expansion.
4. Keep CI green and evidence-based.
5. Interactive playability matters more than feature/branch/PR count.
6. Legal caution over speed.


## How to follow progress

- Current acceptance gate → `docs/NEXT_MILESTONE.md`
- Build/runtime evidence → `docs/GAMECUBE_FIRST_RENDER_STATUS.md`
- Overall plan → this file
