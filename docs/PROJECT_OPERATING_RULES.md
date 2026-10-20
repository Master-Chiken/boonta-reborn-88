# Project operating rules

This is the operating agreement for the public Racer repository. The canonical dashboard is [issue #156](https://github.com/Master-Chiken/boonta-reborn-88/issues/156).

## 1. Work allocation: 80% reverse engineering

The intended engineering effort is **80% reverse engineering and evidence-led research, 20% implementation, testing, integration, and project management combined**.

Measure this in comparable work blocks, not vague intentions: for every ten 45–60 minute blocks, target eight research blocks and at most two combined implementation/testing/management blocks. If a week has less time, keep the same ratio; do not create extra work to meet a quota. Record the block's task ID and result in the active issue. This is an effort target, not a claim that reverse engineering alone makes the game playable.

Reverse-engineering work includes:
- investigating the reviewed PC source/decompilation or an authorized local binary/runtime artifact;
- mapping symbols, functions, structures, formats, state transitions, physics, route/spline systems, and timing assumptions;
- comparing the PC reference with the candidate Step 102 source and the current clean-room GameCube implementation;
- creating evidence-linked behavior specifications with confidence levels, platform boundaries, unknowns, and reproducible follow-up tests.

Reading generic documentation, changing CI, mass-producing reports, and speculative coding do **not** count as reverse engineering. Install or use a tool such as REA/Ghidra only when a specific question requires binary/runtime evidence and the actual target format is supported. Do not spend a work block configuring a tool before confirming that it can analyze the chosen artifact.

## 2. Prevent overload: a one-item work queue

- Keep **one active task** at a time. Only one research question may be in progress; other ideas stay in the backlog.
- Keep at most **three next-up items** visible in issue #156. Close or park duplicates instead of opening more tracking issues.
- Each research item must answer one concrete question and produce one bounded dossier. Do not begin implementation while the evidence is still ambiguous.
- A research dossier must record: question, exact source/revision, evidence links, observed facts, inferences, target-platform caveats, unknowns, Step 102 mapping status, and the next reproducible test.
- Finish each work block with a small note: what was established, what was not established, and the next action. Do not start an unrelated task mid-session.
- Do not create a branch for every note. Gather research evidence in the active issue/dossier; make one focused documentation PR when a coherent result is ready.
- No new CI/AI workflow or repository policy change unless it removes a demonstrated blocker to the active task. No scheduled AI coordination reports.

## 3. Evidence-led study → map → implement → validate

1. **Study:** inspect the exact source, binary, format or observed runtime behavior needed to answer one question.
2. **Map:** compare findings against the actual candidate Step 102 files and the current GameCube prototype. Mark absent/unavailable inputs explicitly; never pretend a mapping was checked if the archive is unavailable.
3. **Specify:** write the behavior independently, state what is fact vs inference, and choose a measurable acceptance test.
4. **Implement only when justified:** spend part of the 20% engineering allocation on the smallest implementation that follows the evidence. A finding does not automatically require a code change.
5. **Validate:** run exact-head host tests and the native DOL/ELF build. Use visible Dolphin/controller checks for gameplay behavior and mark physical GameCube/Wii results separately.
6. **Record:** link the dossier, commits, tests and unresolved questions to the canonical issue #156.

## 4. Product direction and active tasks

The goal remains a credible native GameCube racing slice with behavior informed by reverse engineering, not an endless procedural mock-up or speculative port.

- Active reverse-engineering queue: [RE-001 — map route/spline progression between the PC reference and the current GameCube prototype](https://github.com/Master-Chiken/boonta-reborn-88/issues/226).
- Existing validation gate: [issue #126 — interactive three-lap Dolphin acceptance](https://github.com/Master-Chiken/boonta-reborn-88/issues/126). The owner can run this one-time check on PR #214 when convenient; it does not authorize parallel gameplay coding.
- Parked implementation candidates: [PR #214](https://github.com/Master-Chiken/boonta-reborn-88/pull/214) and [PR #233](https://github.com/Master-Chiken/boonta-reborn-88/pull/233). Do not merge either just to clear the queue. PR #233 contains unrelated historical maintenance commits and must not be merged as-is.
- Next research topics only after RE-001 is recorded: map the candidate Step 102 source, if available, then study race state/laps and pod control/traction as separate dossiers. Do not run them concurrently.

## 5. One responsible writer, no branch sprawl

- Use **one write-capable AI/agent at a time**. Read-only research can be parallelized only when it has non-overlapping, explicit questions; to avoid overload, prefer one investigator and one synthesis.
- A substantial change requires an approved scope, bounded file list, and observable acceptance criteria before writing begins.
- One implementation task normally means one short-lived branch and one PR. Base new branches on the current intended target.
- `main` is stable/release integration and must not receive direct pushes. Gameplay changes target protected `dev`; docs/policy may target `main`.
- `archive/branch-heads-20261019` is a protected recovery archive, never a development base and never merged wholesale.
- AI agents may open PRs but must not merge them, enable auto-merge, bypass branch rules, alter repository settings, force-push, or delete branch refs.
- Automatic deletion of merged PR head branches is enabled. Target a branch budget of 10 refs or fewer; a warning is a review trigger, not permission for unattended deletion.

## 6. AI and budget controls

- Project budget: **€0**. No paid model, billing, payment method, paid fallback, paid cloud resource or upgrade. If free quota is exhausted, stop.
- The read-only Gemini coordinator is manual-only and posts requested reports to the canonical issue #156.
- Planning mode is read-only. Keep `GEMINI_WRITE_ENABLED` absent or not equal to `true` unless the owner deliberately approves one exact implementation plan and decides to unlock the separate write workflow.
- One agent-generated summary or green configuration check is not evidence that the game works.
- Never send secrets, ROMs, disc images, BIOS, commercial archives, extracted proprietary models/textures/audio, or uncertain-provenance data to hosted AI services, public issues, CI artifacts, or the repository.

## 7. Source, platform and licensing boundaries

- `SW_RACER_RE` is a Windows-PC reverse-engineering/decompilation reference, not a verified GameCube implementation. Its documented analysis coverage is not the same as complete implementation.
- Upstream `SW_RACER_RE` code is licensed AGPL-3.0 according to its repository; link to source and summarize observations by default. Do not copy/adapt source into the project's existing license without a deliberate license review and owner decision.
- Step 102 remains on hold until proposed files have a documented origin, license/provenance decision and redistribution disposition. Do not bulk-import its archive.
- Keep PC facts, Step 102 facts, and GameCube/Wii hypotheses in separate fields. A PC finding alone never proves console behavior.

## 8. Definition of done

A task is complete only when:
1. its question has been answered with traceable evidence, or the exact blocker is recorded;
2. its fact/inference/unknown distinctions and platform boundaries are explicit;
3. the dossier links to the relevant sources and next reproducible check;
4. any approved code change stays within scope and has exact-head tests;
5. the outcome and one next action are recorded in issue #156.

These rules prioritize deep understanding over parallel coding, automation churn, and a growing backlog.