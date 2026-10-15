# Repository audit — 2026-10-15

## Scope and method
Read-only inspection of the public repository tree, the GameCube prototype Makefile and README, the GameCube status/milestone documents, the relevant GitHub Actions workflow definitions, recent workflow runs, and PR #53. This is a repository/CI audit, not a local build or visual emulator test.

## Executive summary
The repository is active and has a reproducible clean-room GameCube demonstration. It is **not yet a port of the commercial Star Wars Episode I: Racer game**. The main immediate blocker is evidence of visible in-game rendering and input behavior; the current CI's Dolphin null-video smoke test is only a process-startup check.

## What is currently verified
- Repository default branch: `main`; repository is public.
- `gamecube-demo/` contains a standalone clean-room C prototype, Makefile, host tests and tools.
- Recent workflow run #49 (2026-10-15; commit `56cb06548684f99c4078d1a5fde41580e0087045`) passed:
  - host gameplay-state tests;
  - host pause/resume tests;
  - devkitPPC/libogc DOL and ELF build;
  - DOL/ELF structural validation;
  - 12-second Dolphin process smoke using the Null video backend.
- A newer PR #53 run on 2026-10-15 also passed the build, host tests and Null-backend process smoke. Its separate experimental software-renderer diagnostic failed during dependency installation, before frame capture. That failure is non-blocking and does not mean the native build failed.
- Existing CI already covers meaningful build/test steps; duplicating more generic workflows is not the best next investment.

## Important gaps and risks
1. **No confirmed visible frame yet.** The Null backend does not prove visible GX rendering, controls, lap flow, frame pacing or playability.
2. **Prototype scope is limited.** The README explicitly lists audio, saves, title menu, full physics and multi-rival race logic as not implemented. Current track and craft are procedural placeholders.
3. **Original game integration is not established.** This clean-room demo does not yet load original game tracks, models, textures or other proprietary assets; it should not be described as a completed remaster or port.
4. **Legacy native workflow is stale relative to the current layout.** `.github/workflows/native-build.yml` expects top-level `Makefile`, `source/`, `tests/` and a `swe1r_gc_port.dol`, while the current demonstrated target lives under `gamecube-demo/` and produces `boonta_gc_demo.dol`. Manual dispatch of that legacy workflow is therefore likely to stop at its source-archive guard until deliberately reconciled.
5. **Optional renderer diagnostic is brittle.** In PR #53 the optional software-renderer job failed installing its dependencies; it did not reach the launch/capture step. Keep this diagnostic non-blocking while improving its environment reproducibly.
6. **Runtime validation still requires a visual inspection.** A successful compiler, artifact validator, or headless process smoke is not equivalent to a screenshot showing the road/craft or proof that controller input works.

## Recommended next actions (ordered)
1. Fix or clearly retire the stale `native-build.yml` so maintainers are not misled by a second incompatible build path.
2. Preserve the reliable `gamecube-demo-build.yml` build/test path; avoid adding duplicate CI checks without a distinct purpose.
3. Make visual evidence the next acceptance gate: capture a Dolphin Software Renderer frame in a stable environment, retain the image/log, and mark the result as diagnostic until geometry and controls are manually confirmed.
4. Add a concise runtime test record: emulator/version, backend, whether the road/craft are visible, steering, throttle/brake, pause/reset, and any failures.
5. After visual boot is confirmed, implement one feature at a time (camera follow, course collision, race flow, then menu/assets pipeline) with tests and reviewable pull requests.
6. Keep the Step 102 archive/source provenance separate from the clean-room demo. Do not import ROMs, disc images, or uncleared commercial assets.

## Manual follow-up needed
A human needs to inspect a captured frame or run Dolphin interactively to confirm visible rendering and controller behavior. CI metadata alone cannot establish those results. Before any Step 102 source import, review provenance and redistribution rights for each file.

## References
- [GameCube demo README](../gamecube-demo/README.md)
- [GameCube first-render status](GAMECUBE_FIRST_RENDER_STATUS.md)
- [Next milestone](NEXT_MILESTONE.md)
- [Current GameCube build workflow](../.github/workflows/gamecube-demo-build.yml)
- [Legacy native build workflow](../.github/workflows/native-build.yml)
- [PR #53: optional Dolphin software-renderer diagnostic](https://github.com/Master-Chiken/boonta-reborn-88/pull/53)
