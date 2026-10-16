# Instructions for AI coding agents

## Mandatory pre-flight

**Read the repository-root [AGENTS.md](../AGENTS.md) before planning or implementing every task.** It applies to code, rendering, controls, parsers, collision, assets, UI, tests, CI, and documentation.

Before editing, inspect current `main`, relevant source and tests, the README/status docs, related open issues, and existing pull requests/branches. Identify the concrete player-visible or developer-blocking outcome, smallest useful scope, assumptions/risks, tests and acceptance evidence. Avoid duplicate branches/PRs and speculative work. If a key behavior, format, platform, license or provenance is uncertain, investigate it before writing dependent code.

## Engineering order: Make it work, make it good, make it fast

Follow this order for every task: first establish the smallest correct, end-to-end behavior and test it; next improve maintainability, edge cases, error handling and player experience without overengineering; only then profile and optimize demonstrated performance bottlenecks. Do not polish broken behavior or prematurely optimize speculative bottlenecks. For performance-focused tasks, prove the intended behavior and baseline first, keep the solution maintainable, then benchmark the measured optimization and re-run correctness tests. Follow the fuller rule in the repository-root [AGENTS.md](../AGENTS.md).

## Equal application

These instructions apply equally to work requested by the project owner (Master-Chiken), work proposed or authored by Biddy-Pinky, and work produced with any AI coding assistant. Do not relax the order when implementing or reviewing either person's changes: establish and verify behaviour first, improve quality second, and optimize only measured bottlenecks third. State evidence and limitations honestly; role, urgency, and a performance-oriented task title do not waive the rule.

## Current project direction

- The primary target is the **clean-room native GameCube homebrew DOL**, keeping Wii compatibility where practical.
- The active prototype lives in `gamecube-demo/`: original GX rendering, a closed-loop procedural track, a controllable procedural pod, HUD, rivals, boost/heat, pause/reset and lap/finish scaffolding.
- The immediate product goal is one accepted playable vertical slice: one complete course, stable camera, controls, collision/off-road response, HUD/lap timing, finish and restart.
- The mesh/model, texture and collision-data pipeline is a subsequent engineering focus, staged from synthetic fixtures to one confirmed, safely parsed format.
- The Step 102 source archive remains on provenance/license hold. **Do not bulk-import it or prioritize import by default.** Treat archive-described features as unverified until independently reviewed and tested.
- The `dreamcast/` KallistiOS starter is a separate experiment. Do not expand it unless explicitly requested or evidence establishes it as necessary.

## Build and validation

- Use the current `gamecube-demo/Makefile`, devkitPPC/libogc workflow, and existing host tests as the project baseline.
- Run relevant host tests and the native GameCube build/artifact validation for changes that affect code/build inputs. Keep deterministic test fixtures synthetic where possible.
- Add regression coverage for reproduced defects. For parsers, exercise malformed, truncated, overflowing and out-of-range inputs; validate counts, offsets, indices, allocation limits and finite numbers before use.
- Never disable, weaken or bypass a test simply to obtain a green build. Preserve the first compiler/runtime error and diagnostic logs.
- Report evidence precisely: host tests, native build, Dolphin null-backend process smoke, scripted Software Renderer input/frame checks, visible manual-controller play and physical hardware are distinct validation levels. Do not claim a live playable race based only on compilation, headless startup, or a still frame.
- Update the relevant roadmap/status documents if tested project state changes; keep pending manual/runtime checks pending until observed.

## Clean-room and licensing boundary

- Keep the GameCube/Wii clean-room implementation separate from PC reverse-engineering code and unreviewed source archives.
- Never commit commercial ROMs, disc images, BIOS files, extracted proprietary models/textures/audio, game dumps or unclear-provenance collision/track data.
- Confirm exact platform and file-format version before parsing. Similar-looking PC and GameCube/Wii formats are not necessarily compatible.
- Prefer original or synthetic public fixtures. Keep lawful local reference data local unless redistribution rights are explicitly documented.
- Review external code, datasets, tools and dependencies individually for license, provenance, attribution and technical fit before adopting them. Treat other projects as documentation/test oracles until review is complete.

## Integration discipline

- Keep each change scoped, reviewable and reversible. Do not push directly to `main`; use a suitable existing feature branch/PR when possible.
- Check branch count and current branch-governance rules before creating branches. Prefer updating relevant existing work over creating parallel implementations.
- Do not bulk-merge stale fork histories or delete useful branches/commits automatically. Compare unique diffs and propose selective integration.
- Never auto-merge generated changes or merge code without checking the diff and required status/tests.
- A PR must explain the goal, scope/non-goals, validation evidence, remaining uncertainties, and how it advances the playable milestone.
