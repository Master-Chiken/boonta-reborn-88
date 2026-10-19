# Project plan

## Objective

Deliver a reproducible, playable GameCube/Wii vertical slice inspired by *Star Wars: Episode I — Racer*. The current mainline prototype is an original clean-room technical slice, not a finished remaster or a completed port of the commercial game.

## Source-of-truth tracks

1. **Mainline clean-room GameCube demo:** `gamecube-demo/`. It currently has procedural course/rival/effect GX rendering plus an original source-authored indexed player-pod mesh and 16×16 RGB8 texture exported to the native GX mesh/RGB565 path, controller input code, throttle/brake, boost and overheat/cooldown, inertial steering, off-road drag, rail recovery, three staggered procedural rivals, total/current-lap/best-lap clocks, a three-lap finish state with readable FINISH banner, pause/reset logic, elapsed-time-normalized 50/60 Hz gameplay updates, strict host regressions, and automated native-build/render checks.
2. **Step 102 source archive:** a separate candidate for the fuller gameplay baseline. Do not merge its draft import PRs wholesale. Source authorship/license, generated track data, models/materials/audio, and dependencies require file-by-file review before redistribution.
3. **SW_RACER_RE and other external projects:** research references only. Keep PC observations separate from GameCube/Wii hypotheses. Review licenses before copying code or data.
4. **Dreamcast/KallistiOS starter and Wii64 tools:** separate research tracks; neither is the native GameCube release milestone.

## Current acceptance status (2026-10-17)

### Verified in CI
- [x] C99 host regressions for gameplay transitions, steering inertia, analog/D-pad mapping, lap boundaries, three-lap finish state, rival events, off-road response, and rail recovery.
- [x] Deterministic host simulation reaches the configured three-lap finish using shared race-distance/lap helpers.
- [x] Cadence regression compares one simulated second at 60 updates and 50 updates, covering acceleration/coasting/braking, boost/heat, steering movement, off-road drag, distance, and rival motion.
- [x] Speed and lap-boundary helpers recover or reject non-finite values instead of propagating NaN/infinity into the race state.
- [x] Native clean-room GameCube DOL and ELF build through devkitPPC/libogc.
- [x] DOL/ELF artifact structure validation and DOL padding.
- [x] Bounded Dolphin null-video process smoke test.
- [x] Visible Software Renderer checks on exact PR #204 head detected the varied canyon, three-lap finish banner, and orange `FINISH` label ([run #39057247310](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39057247310)).
- [x] Latest post-merge GameCube run [#39062005581](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39062005581) passed native DOL/ELF build/artifact validation, host pause/reset tests, bounded Dolphin Null-backend smoke, and the mainline Software Renderer diagnostic. It ran on code-bearing merge commit `72acf968e3214b086b00b77240bb20b889314917`; the latest main commit `8b7c9a8a1e19e6a14eccc182103120e835400b4b` only updates the root README.

- [x] Original source-authored player mesh and source texture validate and match the checked-in generated GX headers; texture and mesh boundary tests passed on PR #203.
- [x] Readable FINISH label and varied canyon silhouette are integrated and checked by a scripted visible finish-frame diagnostic on PR #204.

### Still unverified
- [ ] Interactive steering and acceleration/braking/boost behavior using a visible Dolphin controller profile or physical controller.
- [ ] One complete three-lap run in the running game, including finish display, stopping, reset, and a second run.
- [ ] Longer-session stability and sustained frame pacing.
- [ ] Physical GameCube/Wii behavior.
- [ ] General-purpose source-asset loading and an asset-backed course/collision path; current player mesh/texture path covers only the original fixture and does not parse commercial game formats.
- [ ] A native build or gameplay claim for the separate Step 102 archive.

## Work order

### A — Verify the running prototype
- Use the checklist in [Next milestone](NEXT_MILESTONE.md) to exercise every control in visible Dolphin.
- Record version/backend, controller profile, exact commit, outcomes, and evidence.
- Add a regression test for any observed bug before changing gameplay behavior.

**Exit criterion:** reproducible interactive controls and a complete three-lap race have actual evidence attached to the tested commit.

### B — Consolidate only validated behavior
- Keep each behavior change isolated in a small PR with host tests and native CI.
- Merge only after reviewing the diff and the exact-head required checks; an optional visible-render diagnostic is useful evidence but is separately labeled non-blocking.
- Port unique behavior from old branches only if it is still missing from main and has tests. If a PR is fully superseded, close the PR but preserve its branch/commits.
- Do not delete branches, source files, assets, or history as a way to reduce clutter.

**Exit criterion:** one mainline implementation for each validated prototype subsystem and fewer redundant open PRs, with historical work preserved.

### C — Improve vertical-slice feel and stability
- Verify control direction and steering calibration.
- Exercise off-road/rail response and rival interaction over multiple frames.
- Verify finish/reset behavior, camera framing, visible progress, and frame pacing together.
- Keep the visible-render diagnostic and native build passing as changes land.

**Exit criterion:** repeatable, stable short races with one course, controllable pod, visible course, rival interaction, and finish/restart.

### D — Controlled Step 102 review and integration
- Complete a file-path manifest with origins, license evidence, generated/copied data classification, redistribution decision, and reviewer.
- Exclude unclear-provenance files rather than assuming the archive is wholly open source.
- Integrate only the reviewed, cleared subset in a separate branch. Reconcile its tests and build requirements against the current demo without overwriting working mainline behavior.
- Keep private game archives, ROMs/disc images, BIOS files, extracted commercial assets, and unresolved route data outside the public repository.

**Exit criterion:** a reproducible import list whose every included file has a documented provenance/distribution disposition and whose CI tests/build pass.

### E — Packaging and enhancements
Only after a stable playable slice exists:
- define “HD” for each target separately (console output, replacement assets, rendering changes, or emulator upscaling are not equivalent);
- measure GameCube and Wii performance separately;
- expand courses, vehicles, rival logic, UI, audio, saves, and progression only with provenance-cleared assets/code;
- validate any disc-image/homebrew packaging separately from building a DOL/ELF.

## Non-negotiable engineering rules

- Cloud-first and free-tier-first; no billing or paid fallback to keep an automation running.
- No direct pushes to main; use scoped branches and pull requests.
- Never remove history or branches to tidy up; close superseded PRs while preserving their source branches.
- CI is evidence of only the tasks that actually ran. Host tests, compilation, headless startup, visible rendering, interactive input, a completed race, and hardware testing are different gates.
- Do not import Step 102 or external PC source/assets until provenance and redistribution rights have been reviewed.
- Each task should report changed paths, commit SHA, test command/result, runtime evidence, and remaining blocker.
