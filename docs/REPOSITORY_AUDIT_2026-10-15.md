# Repository audit — 2026-10-15

## Scope and method
Read-only inspection of the public repository tree, the GameCube prototype Makefile and README, the GameCube status/milestone documents, the relevant GitHub Actions workflow definitions, recent workflow runs, and PR #53. This is a repository/CI audit, not a local build or visual emulator test.

## Executive summary
The repository is active and has a reproducible clean-room GameCube demonstration. It is **not yet a port of the commercial Star Wars Episode I: Racer game**. The main immediate blocker is evidence of visible in-game rendering and input behavior; the current CI's Dolphin null-video smoke test is only a process-startup check.

## What is currently verified
- Repository default branch: `main`; repository is public.
- `gamecube-demo/` contains a standalone clean-room C prototype, Makefile, host tests and tools.
- PR #56's GameCube workflow run [#57](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38725911086) passed on the exact PR head:
  - host gameplay tests (including speed, boost, lap finish, rival encounters, off-road drag and rail recovery);
  - host pause/resume tests;
  - devkitPPC/libogc DOL and ELF build;
  - DOL/ELF structural validation;
  - 12-second Dolphin process smoke using the Null video backend.
- PR #53's latest workflow revision is [run #58](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38726122245). The native build and host tests have passed; its optional software-renderer frame diagnostic is still experimental and has not yet supplied confirmed visible-game evidence. Earlier revisions failed during dependency setup before capture; this diagnostic is non-blocking.
- Existing CI covers meaningful build/test steps. Keep the reliable build and Null-backend smoke separate from experimental frame capture rather than duplicating generic checks.

## Important gaps and risks
1. **No confirmed visible frame yet.** The Null backend does not prove visible GX rendering, controls, lap flow, frame pacing or playability.
2. **Prototype scope is limited.** The README explicitly lists audio, saves, title menu, full physics and multi-rival race logic as not implemented. Current track and craft are procedural placeholders.
3. **Original game integration is not established.** This clean-room demo does not yet load original game tracks, models, textures or other proprietary assets; it should not be described as a completed remaster or port.
4. **Legacy workflow is now a compatibility entrypoint.** Commit [`6b2707c`](https://github.com/Master-Chiken/boonta-reborn-88/commit/6b2707cdb94b9361f5e72b0634660741d4635130) changed `.github/workflows/native-build.yml` into a manual entrypoint that delegates to `.github/workflows/gamecube-demo-build.yml`. It no longer contains a duplicate root-level build definition; keep this workflow labeled as compatibility plumbing.
5. **Optional renderer diagnostic is still experimental.** Prior PR #53 attempts failed before a frame was captured. The latest software-renderer job is non-blocking and is not yet evidence of visible in-game rendering. A Null-video process smoke remains useful startup evidence only.
6. **Runtime validation still requires a visual inspection.** A successful compiler, artifact validator, or headless process smoke is not equivalent to a screenshot showing the road/craft or proof that controller input works.

## Recommended next actions (ordered)
1. Preserve `gamecube-demo-build.yml` as the authoritative clean-room pipeline; `native-build.yml` is now only a manual compatibility entrypoint.
2. Make visual evidence the next acceptance gate: capture a Dolphin Software Renderer frame in a stable environment, retain the image/log, and mark the result as diagnostic until geometry and controls are manually confirmed.
3. Add a concise runtime test record: emulator/version, backend, whether the road/craft are visible, steering, throttle/brake, pause/reset, and any failures.
4. Keep the new host tests for off-road and rail response, rival encounters and race finish; add new behavior in small changes with tests.
5. After visual boot is confirmed, implement one feature at a time (camera follow, course collision, race flow, then menu/assets pipeline).
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
