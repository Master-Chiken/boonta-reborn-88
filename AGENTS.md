# Project-wide guardrails — read before every change

These rules apply to **every future project change**, not just the current GameCube milestone: gameplay code, rendering, input, asset tools, parsers, collision, UI, tests, CI, documentation, and proposed integrations. Read this file before planning or implementing work.

## Equal standard for every contributor

This rule applies without exception to **the project owner (Master-Chiken), Biddy-Pinky, this assistant, and every other human or AI-assisted contributor**. It governs project planning, priorities, implementation, testing, reviews, documentation, research, and performance work—not only code merged to `main`. No contributor gets a shortcut because of role, urgency, convenience, branch/fork, or because a task is labelled as an optimization. Whoever proposes or reviews a change must verify the same sequence and ask for evidence: correct end-to-end behaviour first, maintainable and well-handled behaviour second, measured optimization third. The same expectations apply when reviewing work authored by the project owner or Biddy-Pinky.

## Mandatory engineering order: Make it work, make it good, make it fast

This order applies to every project task. Do not skip ahead to polish or optimization while the end-to-end behavior is still incorrect.

1. **Make it work.** Deliver the smallest correct end-to-end behavior for the stated goal. Define observable acceptance criteria, handle expected edge cases, and add/run tests that demonstrate the behavior. A build passing alone is not enough when behavior has not been tested.
2. **Make it good.** Once it works, improve clarity, maintainability, error handling, appropriate architecture, and player/developer experience. Keep the scope focused; do not turn “good” into an excuse for speculative frameworks, oversized refactors, or feature creep.
3. **Make it fast.** Only after correctness and design quality are adequate, optimize demonstrated bottlenecks. Measure/profile first, compare before/after where practical, add regression or benchmark coverage, and verify that the optimization preserves behavior. Do not perform speculative performance tuning.

The order is a decision rule, not a demand for unnecessary work: if a stage is already satisfied, record the evidence and move on. For a performance-focused task, reproduce and define the required behavior first, preserve correctness and maintainability, then optimize the measured bottleneck.

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

## Branches, task lifecycle, pull requests, and integration

- **No project-defined numerical branch cap.** Total and active branch counts are informational only. Never block useful work, fail an audit, interrupt an active task, or delete/rewrite branches solely because a count reaches a threshold. GitHub's own service constraints still apply; the project imposes no arbitrary branch-count ceiling.
- **Coordination alerts are not caps.** For general contributors, report an informational alert at 105 total repository branches. For Biddy-Pinky, use the contributor-specific alert threshold of 200 total branches rather than 105. An alert does not interrupt work already in progress or fail a workflow; it is a reminder to complete and hand off the current task before starting an unrelated task. Preserve Biddy-Pinky's allowance for up to two genuinely independent workstreams, provided they do not overlap and each is documented and tested.
- Every branch must represent a concrete task or a clearly documented existing workstream. Use one focused branch per task; do not create empty, speculative, or duplicate branches merely because the count is unlimited. Prefer continuing the existing branch for the same task.
- **Jules must finish one task before starting an unrelated task.** After beginning a task, continue until it is implemented, relevant tests have been run, failures have been addressed where possible, the final diff has been self-reviewed, a reviewable PR has been submitted, relevant CI checks are terminal, and a truthful completion report is posted. Do not start another independent Jules task while any of these steps remain unfinished.
- Jules' task is considered handed off when its PR is reviewable, checks are complete or a concrete external blocker is documented, and the report explicitly states what is waiting on a human. A task does not need to be merged to count as handed off; Jules must never merge automatically or bypass owner review.
- If a real external blocker prevents completion, record the exact blocker and evidence, preserve the branch and current work, report tests and remaining steps, and wait for the next decision. Do not silently abandon a task or label ordinary test failures as external blockers.
- Branch count never determines parallelism. Parallel work is allowed only when the project’s contributor policy permits it and the tasks are genuinely independent. Jules is limited to one active implementation task at a time. Preserve Biddy-Pinky’s established allowance of up to two independent workstreams (at most one runtime implementation and one non-overlapping research/documentation/tooling/review task), unless the owner explicitly changes that policy.
- Do not push directly to main; integrate through reviewable PRs and preserve rollback options. Never delete useful branches, commits, or files automatically. Do not merge stale fork histories wholesale; compare unique diffs and integrate selectively.
- Avoid parallel PRs that change the same behavior/files without a clear dependency plan. Keep each change focused so its purpose, risk, and evidence can be reviewed.

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