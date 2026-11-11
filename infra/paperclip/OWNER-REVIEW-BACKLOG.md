# Owner-review backlog candidates and queue-liveness contract

**Status: Candidate B is owner-approved and staged as the single active task `GC-RACE-PROGRESSION` in PR #393 (target branch `dev`). Candidate A and Candidate C remain proposals and are not approved.**

This document records the owner-approved next task and preserves the queue-approval boundary. The canonical task source remains `docs/automation/task-ledger.json` on `main`; PR #393 stages the ledger and compact summary update together. The task becomes visible to the main-branch scheduler only after PR #393 is merged.

## Audited current state

Before PR #393, main commit `4fdfd6292e5379977b0ca240c47d9c15e2b320eb` (ledger updated 2026-11-10) contained 11 records. PR #393 stages the owner-approved `GC-RACE-PROGRESSION` row as the sole active task on `dev`; after it merges, the ledger will contain 12 records (9 completed, 2 blocked, 1 active):

| State | Count |
|---|---:|
| completed | 9 |
| blocked | 2 |
| queued | 0 |
| active | 0 |
| in_review | 0 |

The blocked tasks are `AUTOMATION-LEDGER-ACTIVATION` and `N64-COMPWOLF-PUPP-T2-PARSE-PROBE`. Do not automatically activate the N64 T2 task: it requires an owner-local SDK/probe and licence/provenance checks.

The documentation drift identified in the earlier backlog draft has now been corrected on the current documentation branch: PR #274 and PR #269 are recorded as merged with their exact merge SHAs in `docs/NEXT_MILESTONE.md` and `docs/PROJECT_OPERATING_RULES.md`. The current PR state, merge commit and current `main` files must continue to outrank copied historical prose. A future status-sync check should flag any documentation claim that a linked PR is open/draft when GitHub reports it merged/closed.

## Candidate sequence — require explicit owner approval before adding to the ledger

These candidates are proposals, not instructions to the autonomous scheduler. Keep at most three next-up items visible, consistent with `docs/PROJECT_OPERATING_RULES.md`.

### Candidate A — Phase 1 reuse / compatibility decision

**Historical roadmap origin, not an active task assignment:** the 2026-11-06 direction in `docs/PROJECT_OPERATING_RULES.md` and the activation task's historical `next_action` identify a useful question: consume the existing read-only PC/N64/Dreamcast evidence in issue #279 and decide what can be reused, converted, adapted, independently reimplemented or must remain on hold for the native GameCube/Wii target. As of 2026-11-11 this candidate is not in the canonical ledger and is not authorized for autonomous execution.

**Bounded deliverable:** one concise system-by-system decision matrix for the Phase 1 baseline. Do not recreate PR #282's complete-game matrix or repeat #279's source inventory.

**Acceptance criteria:**
- Every system row links the exact existing Boonta candidate, evidence dossier and source revision already available.
- Each row chooses exactly one disposition: reuse as-is, convert, adapt, clean-room reimplement, unavailable, or HOLD.
- PC/N64/Dreamcast observations remain separate from GameCube/Wii facts; unknown target behavior stays UNKNOWN.
- Licence, provenance and redistribution boundaries are explicit. No ROM, disc image, extracted commercial asset, private analysis database or unclear-provenance payload is uploaded.
- The result identifies the smallest next implementation slice and a testable acceptance criterion.
- No gameplay code changes are bundled into this decision-only task.

### Candidate B — end-to-end race progression using existing mainline systems

<escape>**Owner decision, 2026-11-11: APPROVED.**</escape> This is the next official engineering task, recorded as `GC-RACE-PROGRESSION` with status `active` and target branch `dev` in PR #393. It becomes eligible for the scheduled writer only after PR #393 is merged.

**Source of priority:** reuse the rival racing implementation already integrated by PR #327; do not rebuild the rival subsystem. PR #307 remains explicitly deferred until the race slice is coherent.

**Bounded deliverable:** inspect the current `dev`-branch race state machine and PR #327 implementation; record which start, lap, pause, finish and restart behaviors already exist; then implement only the missing single-race results/session transition and its production-helper host tests. Do not turn this into a title menu, championship, save system, multiple-track or branching-route project.

**Acceptance criteria:**
- Reuse the existing three-lap, timer, pause/restart, route-cursor and rival code; PR #327 at `69deb6778f9383887118803428e7014686865a83` is the rival baseline. Do not recreate PRs #317/#318/#319.
- Add a minimal start -> active race -> three-lap finish/results -> restart state flow using production helpers; no simulation progresses after finish and results remain immutable until restart.
- Display only measured values already available (completed laps, total time, last/best lap data and overtakes); do not fabricate rank, championship or persistent-save data.
- Host tests exercise valid/invalid transitions, exact finish, pause/timer freeze, results stability and complete restart reset.
- Native GameCube/Wii builds, artifact validation and exact-head host/Dolphin checks pass. Scripted Dolphin evidence remains scripted; live-controller and physical hardware acceptance remain unverified.
- No proprietary or Step 102 assets/code are imported; preserve clean-room provenance boundaries.

### Candidate C — one synthetic branch-to-rejoin runtime slice

**Source of priority:** `gamecube-demo/README.md` and `tools/route_graph_format/README.md` state that the current runtime drives one unbranched closed oval; route-graph branch metadata and host cursor support do not yet prove vehicle movement, collision and lap-state traversal over a split/rejoin.

**Bounded deliverable:** only after Candidate A and a stable race-progression slice, build one source-authored synthetic route graph with a split and rejoin. Prove how the player selects a branch and how route history affects finish/lap logic.

**Acceptance criteria:**
- A synthetic split → two alternative paths → rejoin fixture is used; no proprietary/original-game track data.
- Player branch input is deterministic and bounded; AI branch behavior is separately specified or explicitly deferred.
- Cursor history, forward look-ahead, lap/finish seam, collision and recovery are covered by host tests.
- Runtime branch support is not claimed merely because the neutral file format or host-side cursor can represent branches.
- Native build and exact-head automated checks pass; interactive and hardware behavior remain separately unverified.

## Required scheduler behavior when the queue is empty

1. Reconcile the full canonical ledger and generated compact summary; reject stale or schema-inconsistent summaries.
2. If there is no active/queued task and the activation bootstrap is not eligible, return a machine-readable `EMPTY_QUEUE` / `WAITING_FOR_OWNER_APPROVAL` result.
3. Do not call Gemini/OpenRouter/Groq, consume quota, create a branch, create a PR, change a task status or add a cooldown marker for an empty queue.
4. Do not promote a blocked task or invent a task ID. Only owner-approved ledger rows with complete acceptance criteria and target branch may become executable.
5. After a validated task PR is merged and reconciled, promote at most one already-approved queued task, under the same single-writer lock.
6. If issue/roadmap prose conflicts with the live ledger or live PR state, stop and report the discrepancy. Do not select work from stale narrative.

## Status freshness contract for agent context

- Every current-state prompt should include the canonical ledger commit SHA, ledger `updated_at`, selected task ID, target branch and the live PR state snapshot timestamp.
- Historical PR numbers in project docs must be checked against live GitHub before an agent acts on them.
- A linked PR that is merged must not be described as open/draft; a live open PR must not be called completed.
- A task is completed only after its PR is merged and the canonical ledger has been reconciled to the exact merge evidence.
- A green CI check on an old SHA does not validate a newer head.

## Approval and activation boundary

Candidate B is the approved exception and is staged as the active `GC-RACE-PROGRESSION` row with a matching regenerated summary in PR #393. It must not be scheduled until that PR is merged. Candidate A and Candidate C remain proposals; any later activation still requires the owner to add the exact task, scope, target branch, acceptance criteria, tests and provenance limits to the canonical ledger before the scheduler can acquire the writer slot.
