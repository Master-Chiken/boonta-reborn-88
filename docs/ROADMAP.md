# Boonta Reborn 88 – Project Roadmap

Last updated: 2026-10-16

**Goal**  
Create an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), native on GameCube / Wii, with improved visuals and bonus content.  
Unofficial fan / homebrew project. Clean-room first.

---

## Phase 0 – Foundations

**Status: prototype foundations and CI are in place; interactive acceptance is still open.**

- [x] Clean-room procedural GX prototype.
- [x] Basic driving, boost/heat, rivals, lap system and HUD.
- [x] Native DOL/ELF build, artifact validation and CI.
- [x] Host tests for deterministic gameplay, pause/reset, steering, collisions and state boundaries.
- [x] Dolphin headless process smoke.
- [x] Automated D-pad left/right and analog-stick left/right steering diagnostics.
- [x] Automated Y-reset scenario with a visible HUD-state assertion.
- [x] Scripted three-lap finish-banner evidence on [earlier run #38899605111](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38899605111).
- [ ] **Manual controller + live finish/reset/restart acceptance** — current focus.
  → See [`NEXT_MILESTONE.md`](NEXT_MILESTONE.md) and [current test evidence/status](GAMECUBE_FIRST_RENDER_STATUS.md).

Latest CI on current main commit `cacec9c35d9a41258493c619368a6537d952a7a9` passed native build, host tests, Dolphin headless smoke and automated Software Renderer diagnostics: [run #38948039632](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38948039632). Automated input movies prove the configured movie input produces the expected scripted response; they do **not** establish physical-controller playability.

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

1. Clean-room first; publish only original or redistribution-cleared code/assets.
2. One coherent playable vertical slice before broad content expansion.
3. Keep CI green and evidence-based.
4. Interactive playability matters more than feature/branch/PR count.
5. Legal caution over speed.

## How to follow progress

- Current acceptance gate → `docs/NEXT_MILESTONE.md`
- Build/runtime evidence → `docs/GAMECUBE_FIRST_RENDER_STATUS.md`
- Overall plan → this file
