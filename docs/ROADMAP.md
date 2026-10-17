# Boonta Reborn 88 – Project Roadmap

Last updated: 2026-10-17

**Primary product ambition**  
Build a future native GameCube/Wii fan-made remaster of *Star Wars: Episode I – Racer* (1999). The original 1999 release did not receive a dedicated native edition for GameCube or Wii, so Boonta Reborn 88 aims to create a new homebrew experience for those consoles rather than claim an existing port.

**Vision tiers**
- **HD++ Remaster (primary vision):** improve visual clarity and asset detail within original console limits, refine handling/camera, develop new original or rights-cleared tracks and pods, and grow the experience with improved UI/audio, progression, bonus challenges and modes.
- **HD+++ Premium (aspirational stretch goal):** take presentation and content further if performance, development resources, and rights allow; potential DLC-style packs, richer effects and environments, and a broader roster are future ideas, not current features.
- **Ideal wider dream:** if technically and practically feasible, explore a broader remake-style experience inspired by the wider *Star Wars Racer* legacy. This is not a promise to reproduce other commercial games or assets.

**Platform reality:** HD++ and HD+++ Premium are labels for visual quality, production polish, and scope, not a promise of native HD video output on GameCube/Wii. The console builds must fit their legacy hardware and video-output limits. An actual HD-resolution Premium build would require a separate platform target and remains optional.

Unofficial fan / homebrew project, not affiliated with or endorsed by the original rights holders. Clean-room first.

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
- [x] Scripted Start pause/resume visible-state checks passed on PR #180 head in [run #38954611194](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38954611194).
- [x] Original source-authored indexed player-pod mesh and 16×16 RGB8 texture are validated and deterministically exported to the GX mesh / tiled RGB565 headers ([PR #203](https://github.com/Master-Chiken/boonta-reborn-88/pull/203), merged).
- [x] Readable `FINISH` label and varied procedural canyon skyline are integrated ([PR #202](https://github.com/Master-Chiken/boonta-reborn-88/pull/202), [PR #204](https://github.com/Master-Chiken/boonta-reborn-88/pull/204), merged).
- [x] Scripted three-lap finish-banner and orange `FINISH`-label pixel checks passed on PR #204 head in [run #39057247310](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39057247310); this was DTM-driven, not a manual race.
- [ ] **Manual controller + live finish/reset/restart acceptance** — current focus.
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

## Phase 3 – HD++ Remaster and Bonuses

**Goal:** turn the validated racing slice into a distinctly enhanced Episode I – Racer-inspired experience, using original or rights-cleared assets and staying within console budgets.

- Upgrade visual clarity, art direction, pod/track detail, scenery, materials and effects where practical.
- Add original or rights-cleared circuits and pods.
- Improve UI, audio, options, progression, quality-of-life and race feedback.
- Add bonus modes and challenge content (for example Time Trial and Versus, if feasible).
- Validate frame pacing and compatibility on the targeted GameCube/Wii configurations.

## Phase 4 – HD+++ Premium (aspirational stretch goal)

This is a **long-range ambition, not a committed feature list or a description of the current prototype**. Pursue it only after the HD++ base is stable and the platform, team, rights and performance budget are clear.

- Push visual presentation, environments, effects, UI/audio and content depth to the highest level the chosen target supports.
- Consider larger content expansions: extra circuits, pods, challenge sets, bonus modes, and DLC-style packs.
- Explore a broader *Star Wars Racer*-inspired remake scope only if technically feasible and the necessary rights and redistribution conditions are clear.
- Consider a separate true-HD-resolution edition only on a suitable, more capable platform; do not imply that native GameCube/Wii output is 720p/1080p.

**Exit criteria:** a defined target platform, realistic production scope, rights/provenance review, measurable performance targets, and a stable HD++ base. Until those exist, the Premium tier remains aspirational.

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
