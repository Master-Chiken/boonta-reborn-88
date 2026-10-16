# Boonta Reborn 88 – Project Roadmap

Last updated: 2026-10-16

**Goal**  
Create an enhanced, playable racing experience inspired by *Star Wars: Episode I – Racer* (1999), native on GameCube / Wii, with HD visuals and bonus features.  
Unofficial fan / homebrew project. Clean-room first.

---

## Phase 0 – Foundations (current)

**Status**: Mostly complete

- [x] Clean-room procedural GX prototype
- [x] Basic driving, boost, heat, rivals, lap system, HUD
- [x] Native DOL/ELF build + CI
- [x] Host tests + native build + visible render evidence
- [x] Scripted controller-direction checks and visible three-lap finish in Dolphin CI ([run #38899605111](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38899605111))
- [ ] **Manual controller + live finish/reset/restart acceptance** ← current focus  
  → See `NEXT_MILESTONE.md`

---

## Phase 1 – Playable Vertical Slice

**Goal**: One enjoyable circuit that feels good for several minutes.

- Solid controls and physics feel
- Stable, pleasant camera
- Reliable track collision and rail recovery
- Clean 3-lap race + pause/reset/restart
- Stable frame pacing (target 60 fps or solid 30 fps)
- Basic audio feedback (optional but recommended)

**Exit criteria**: The slice is fun enough that you want to keep playing it.

---

## Phase 2 – Core Content

- 3–5 tracks (procedural or authored)
- Multiple pods with different stats
- Improved rival AI
- Basic menus + HUD polish
- Minimal sound set (engine, boost, impacts, UI)

---

## Phase 3 – Remaster & Bonuses

- Visual upgrades (better materials, effects, higher internal resolution where possible)
- Extra modes (Time Trial, Versus, etc.)
- Quality-of-life options
- Wii-specific improvements if relevant
- Further polish and stability

---

## Parallel / Restricted Track

**Step 102 source archive**  
Remains under strict import hold until full provenance and license review is complete.  
No commercial ROMs, assets, or unclear code may enter the public repository.

---

## Guiding principles

1. Clean-room first. Original code and assets only in the public repo.
2. One solid vertical slice before expanding content.
3. Keep CI green and evidence-based.
4. Interactive playability > feature count.
5. Legal caution over speed.

---

## How to follow progress

- Current focus → `docs/NEXT_MILESTONE.md`
- Build status → `docs/GAMECUBE_FIRST_RENDER_STATUS.md`
- Overall plan → this file
