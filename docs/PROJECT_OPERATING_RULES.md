# Project operating rules

This document is the operating agreement for the public Racer repository. The canonical live dashboard and engineering queue is [issue #156](https://github.com/Master-Chiken/boonta-reborn-88/issues/156). These rules are intended to keep a solo maintainer in control while using AI tools and GitHub automation.

## 1. Product priority

The goal is a credible, interactive GameCube racing slice before speculative features or broad ports.

1. Finish and validate the existing gameplay changes in the approved queue.
2. Complete the visible Dolphin acceptance checklist in [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126).
3. Only after that acceptance gate, choose one controlled handling or fidelity improvement at a time.
4. Keep research and asset conversion work parked when it does not unblock the playable slice.
5. Do not present host tests, a native build, a headless Dolphin smoke test, or a scripted movie as proof that a person can drive a complete race.

## 2. One task, one responsible writer

- Keep **one active implementation task** at a time. Other open PRs may remain parked, but they must not receive competing edits.
- A substantial task must have a single written goal, a bounded list of files, observable acceptance criteria, and named verification steps before code is changed.
- Use **one write-capable AI agent at a time**. Do not ask Jules, Gemini, Codex or another agent to edit overlapping files concurrently.
- Read-only audits may inspect the repository, but they do not authorize code changes.
- An AI proposal is not approval. The repository owner must approve the specific plan and scope before a write-capable agent starts.
- If two PRs touch the same runtime code or tests, choose the active one first. Park the other; do not merge both blindly.

## 3. Branch and pull-request rules

- main is the stable integration/release branch. Never push directly to it.
- dev is the normal target for gameplay changes. A later promotion of validated work from dev to main is a separate decision.
- archive/branch-heads-20261019 is a protected recovery archive, not a development base. Never merge it wholesale into main or dev.
- One task normally means one short-lived branch and one PR. Base new task branches on the current intended target, not on an unrelated open PR or stale branch.
- Documentation and repository-policy changes may target main; gameplay changes target dev.
- AI agents may open PRs but must not merge PRs, enable auto-merge, bypass branch rules, change repository settings, force-push, or delete branch refs.
- GitHub's **Automatically delete head branches** setting is enabled. A merged task branch should normally disappear automatically.
- Branch budget: warning at 10 refs, red line above 20, active-work target 10 or fewer. A budget alert triggers review; it is not permission to delete unreviewed refs.

## 4. AI and workflow controls

- The project budget is **€0**. Do not enable paid models, billing, payment methods, paid fallbacks, paid cloud resources, or upgrades. If the available free quota is exhausted, stop.
- The read-only Gemini coordinator is **manual-only**. It must not run on a schedule and must post a requested report only to the canonical tracking issue #156.
- The @gemini-cli planning path must remain read-only. Code-writing execution is separate and may run only after the owner approves the exact plan and GEMINI_WRITE_ENABLED is deliberately set to the exact value true.
- Recommended current setting: keep GEMINI_WRITE_ENABLED absent or not equal to true while the existing gameplay PRs and Dolphin acceptance gate are being completed. Enable it only for one explicit, bounded task, and return to the locked state afterward.
- The branch-intake queue is manual-only and defaults to one candidate. Do not run it while existing PRs have not been reviewed.
- Never treat an agent-generated summary, successful prompt run, or green static guard as evidence that the game is playable.
- Never paste secrets, credentials, commercial game archives, ROMs, disc images, BIOS files, extracted models, textures, audio, or unclear-provenance data into AI prompts, public issues, CI artifacts, or the repository.

## 5. Verification required before merge

For code changes, checks must refer to the exact current PR head, not an older commit.

- **Host tests:** confirm portable state logic, regression tests, and tooling.
- **Native build:** confirm the actual GameCube DOL/ELF builds with the intended toolchain.
- **Dolphin process smoke:** proves only that the emulator process/build starts; a null-video run is not visual proof.
- **Visible Dolphin/controller acceptance:** proves observable controls and race behavior only for the exact tested build and setup.
- **Physical hardware:** claims about GameCube/Wii hardware require separate hardware evidence.
- A non-blocking or continue-on-error diagnostic does not become a required passing gate just because the overall workflow succeeds.
- If a test is pending, missing, failed, or not run on the exact head, record it as such. Do not merge around it to clear the queue.

## 6. Clean-room and provenance boundaries

- The Step 102 source archive remains on hold until every proposed file has a recorded origin, license/provenance decision, and redistribution disposition.
- Research from the PC release, N64 release, or a third-party reverse-engineered repository is a reference, not permission to copy code or data into the GameCube/Wii project.
- Keep platform findings separate: PC source evidence does not confirm GameCube/Wii behavior.
- Prefer original implementations, synthetic test fixtures, and evidence-linked behavioral specifications. If provenance is uncertain, stop and document the exact blocker.

## 7. Definition of done

A task is done only when:

1. The requested behavior or policy is implemented within the approved scope.
2. The diff is small enough to review and contains no unrelated cleanup.
3. The relevant exact-head checks have completed successfully, with limitations recorded.
4. Required human/controller acceptance has been recorded as PASS, FAIL, or NOT TESTED.
5. The PR is merged normally or intentionally closed with the reason documented.
6. The owner can see one clear next action in issue #156.

These rules favour a verified playable build over more branches, more automation, or more AI-generated work.