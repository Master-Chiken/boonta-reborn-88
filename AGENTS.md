# Project-wide guardrails — read before every change

These rules apply to **every future project change**, not just the current GameCube milestone: gameplay code, rendering, input, asset tools, parsers, collision, UI, tests, CI, documentation, and proposed integrations. Read this file before planning or implementing work.

## Required pre-flight: decide before coding

Before starting any change, answer these questions:

1. **Outcome:** What concrete player-visible or developer-blocking problem does this solve? Which project milestone or acceptance criterion does it advance?
2. **Existing work:** Have the current source, README/status docs, open issues, pull requests, branches, and relevant tests been checked? Is this already implemented or being worked on elsewhere? Reuse or complete existing work rather than creating a duplicate.
3. **Smallest useful change:** What is the smallest end-to-end improvement that can be built and verified? Avoid speculative refactors, unrelated tooling, new platforms, and feature creep.
4. **Dependencies and risks:** Are platform, file format, toolchain, license, provenance, performance, or compatibility assumptions confirmed? Identify unknowns and investigate them before depending on them.
5. **Acceptance and tests:** What observable result will prove success? Decide the relevant automated and manual tests before implementation, and state what they cannot prove.
6. **Safe integration:** Which existing branch/PR should carry the change? Check its diff against current `main`, avoid duplicate/stale work, and preserve a clear review and rollback path.

**Do not start implementation until the goal, scope, risks, and acceptance test are clear.** If a key format, license, or behavior is uncertain, make the next task a focused investigation with explicit evidence—not a guess-based implementation.

## Product priorities

Optimize for a **working, playable vertical slice**, not for the number of commits, branches, tools, or features.

Keep work in this order unless measured evidence shows a different blocker:

1. One complete closed circuit, one controllable pod, stable camera, steering/throttle/brake/boost, track-edge and collision response, HUD/lap timing, finish, and clean reset/restart.
2. A validated, renderer-friendly mesh pipeline; then one confirmed model and texture format; then collision/track data that matches the visible course.
3. Minimum UI states needed to complete and restart a race, plus stability and presentation polish.
4. Only after the first slice is accepted: more tracks and pods, player/pod stats, expanded menus, race modes, progression, and bonus content.

Do not start a converter, broad asset catalog, major rewrite, new renderer/platform, or content expansion merely because it is interesting. It must remove a demonstrated blocker or be explicitly prioritized.

## Clean-room, assets, and licensing

- Keep the clean-room GameCube/Wii prototype separate from PC reverse-engineering and unreviewed source archives.
- Never import code, datasets, models, textures, collision data, audio, or generated files with unclear origin or redistribution rights.
- Never commit commercial ROMs, disc images, BIOS files, extracted proprietary assets, or dumps to this public repository.
- Confirm the exact platform/version and file format before writing a parser. Similar-looking PC and GameCube/Wii formats must not be assumed compatible.
- Use original or synthetic fixtures for public tests. Keep any lawful local reference data local unless redistribution permission is documented.
- Review each external dependency or borrowed code path for license, compatibility, attribution, and actual benefit before adopting it.

## Branches, pull requests, and integration

- Do not push directly to `main`; make changes reviewable through pull requests and preserve rollback options.
- Prefer an appropriate existing branch/PR over creating another branch. Respect the project branch ceiling and any active branch-governance issue.
- Never delete useful branches, commits, or files automatically. Do not merge stale fork histories wholesale; compare unique diffs and integrate selectively.
- Avoid parallel PRs that change the same behavior/files without a clear dependency plan.
- Keep the change focused. Separate unrelated work so that each review can explain its purpose, risk, and evidence.

## Required validation and honest reporting

Use the strongest practical level of validation for the claim being made, and report these separately:

- **Host tests/static checks:** logic or tools covered by those tests pass.
- **Native DOL/ELF build and artifact validation:** the tested source compiles for the target and the artifacts pass structural checks.
- **Dolphin null-backend smoke:** the emulator can run the binary for the tested interval; this is not visual or gameplay proof.
- **Dolphin Software Renderer / scripted DTM:** only the visible frames and scripted inputs/states actually asserted are verified.
- **Visible manual Dolphin session:** required to claim real-time play with a configured controller, a complete manually driven race, reset/restart, and longer-session stability.
- **Physical GameCube/Wii:** hardware compatibility requires separate hardware evidence.

Add or update deterministic regression tests for reproduced bugs. Exercise malformed/truncated/out-of-range inputs for parsers where appropriate. Do not claim a feature is complete from compilation, a still image, or a scripted test that does not cover that feature.

## Definition of done for every change

Every task/PR should state:

- the problem and why it matters to the playable project;
- the exact scope changed and any important non-goals;
- tests/checks run, with links to CI/artifacts where available;
- tests not run and remaining manual/runtime/license uncertainties;
- the next smallest action that advances the approved milestone.

Update the relevant status/roadmap documentation when a change materially alters the project state. A task is not done merely because code was written or committed.

**When in doubt, inspect first, reduce scope, protect the clean-room boundary, and prove the result before expanding.**