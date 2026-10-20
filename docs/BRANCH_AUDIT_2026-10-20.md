# Branch audit — 2026-10-20

## Purpose

Record a read-only inventory before reducing remote branches. This document is a decision aid, not authorization to delete refs. No branch deletion, force-push, workflow dispatch, or merge was performed for this audit.

## Current branch inventory

| Branch | Known role / comparison | Recommendation |
|---|---|---|
| `main` | Primary branch | Protect |
| `dev` | Integration branch; current target for gameplay PRs #214 and #243 | Protect |
| `archive/branch-heads-20261019` | Archived branch-head snapshot | Preserve until its checkpoint and recovery value are verified |
| `docs/reverse-engineering-80-20-20261020` | Current PR #242 head `963c14f4a7322dacd9d0f6627bd379f30ad59302`; 81 commits and 15 files changed per current PR metadata | Keep draft; current exact-head safety and provenance workflows passed, but the trusted source-import path guard was not visible and must be confirmed on this SHA |
| `fix/steering-stick-deadzone-20261019-14221623089412890411` | Compared with `dev`: 16 commits ahead, 1 behind; 4 files changed (two gameplay files and two cleanup workflows) | Do not merge as a gameplay-only change; split and review workflow changes independently |
| `fix/steering-stick-deadzone-clean-20261020` | Compared with `dev`: 2 commits ahead, 0 behind; only `gamecube-demo/source/gameplay_state.h` and `gamecube-demo/tests/test_gameplay_state.c` changed | Keep while PR #243 is under review |
| `fix/width-aware-rail-collision-20261017` | Compared with `dev`: 26 commits ahead, 1 behind; 10 files changed across gameplay, tests, Dolphin tooling, docs, and workflow | Keep while PR #214 is under review |

A fresh live branch search on 2026-10-20 returned eight refs (single page): the seven branches above plus this audit branch, `docs/branch-audit-20261020`. The branch-budget issue #235 still contains an older 27-ref snapshot; do not treat that alert body as the current inventory.

## Pull request gates

### PR #214 — width-aware rail collision

- Open, draft, targets `dev`.
- Current head recorded as `db1f9747b8193d6cc4e77e0f69a073cd5e210eb5`.
- Reviewer requested: `Biddy-Pinky`; no review submission was found in the latest review-list query.
- Manual visible-Dolphin acceptance remains outstanding: rail/edge feel, boost drain and recharge, overheat, manual three-lap completion, restart, and longer-session stability.
- The exact-SHA workflow run `39327379050` completed successfully with four jobs: host pause/resume and gameplay tests, native GameCube DOL/ELF build, Dolphin headless smoke, and non-blocking software-renderer diagnostic. The connector's workflow-run listing showed one workflow run, but its job details confirm all four jobs passed on this SHA.

### PR #243 — analog steering deadzone

- Open, draft, targets `dev`.
- Current head recorded as `d1c5bf755a587765908a152fbf8874231bf6fe75`.
- Reviewer requested: `Master-Chiken`; no review submission was found in the latest review-list query.
- Exact-SHA workflow run `39459255221` completed successfully with four jobs: host pause/resume and gameplay tests, native GameCube DOL/ELF build, Dolphin headless smoke, and non-blocking software-renderer diagnostic.
- Manual controller-feel acceptance is still outstanding; CI does not prove the stick deadzone feels correct on a real controller or in interactive Dolphin.

### PR #242 — research-first documentation and workflow changes

- Open; explicitly returned to draft pending review.
- Current head recorded as `515a195701261d5c106797f4025cf62c6b7368c1`; base is `main`.
- The comparison to `main` reports 76 commits ahead and 14 changed files. Comparison to `dev` is a substantially divergent history, so its base must not be casually changed.
- A fresh metadata check at 2026-10-20 19:24 CEST reports head `963c14f4a7322dacd9d0f6627bd379f30ad59302`, 81 commits, and 15 changed files. On this exact SHA, `Step 102 source-import provenance guard` (run `39465154135`) and `AI free-tier safety checks` (run `39465154137`) completed successfully. The trusted source-import path guard was not present in the returned workflow-run list; the full gate is therefore not confirmed. Earlier passing checks on older SHAs do not validate this head.
- Reviewer requested: `Biddy-Pinky`.

### PR #233 — combined deadzone and cleanup automation

- Its comparison to `dev` reports 16 commits ahead and 1 behind.
- The four changed files are the two deadzone files plus `.github/workflows/branch-cleanup-selftest.yml` and `.github/workflows/retire-archived-branch-refs.yml`.
- Do not use this combined PR as the path to merge the gameplay fix. The cleanup workflow has `contents: write` and a delete mode; its safety gates and target list need independent security review. No workflow was run.

## Safe cleanup rules

1. Never delete `main` or `dev`.
2. Do not delete a branch merely because a similarly named branch or PR exists.
3. Before retiring any other branch, identify its associated PRs, unique commits, files not integrated into `main`/`dev`, archive checkpoint, and any workflow dependencies.
4. Prefer preserving unique work via a reviewed PR or an immutable checkpoint before any retirement.
5. Keep destructive branch-retirement automation disabled until its allowlist, checkpoint, permissions, dry-run behavior, and human approval requirements have been independently reviewed.
6. No branch should be deleted or force-pushed by an agent without explicit human authorization.
7. After merges, rerun comparisons against the then-current base; these results are a snapshot from 2026-10-20 and will become stale.

## Recommended next steps

1. Finish PR #214 first: obtain independent review and record the human-operated visible-Dolphin acceptance checklist in issue #126 against the exact tested SHA. Keep it draft/unmerged until that gate is recorded.
2. Only after #214 is accepted, handle #243 as the focused follow-up; preserve its two-file scope and do not revive the combined #233 branch.
3. Keep #242 in review: on the latest checked head `963c14f4a7322dacd9d0f6627bd379f30ad59302`, `AI free-tier safety checks` and `Step 102 source-import provenance guard` passed. The trusted source-import path guard was not visible for this exact SHA, so do not describe all required checks as green. Review the broad history/base carefully and finish only the already-scoped RE-001 documentation work.
4. Split cleanup automation out of #233 into a separately reviewed proposal; do not automatically carry over its deletion workflow.
5. Re-run this inventory after any merge, then propose branch retirement candidates with evidence. No deletion is authorized by this document.


### Follow-up verification — 2026-10-20 19:24 CEST

- A fresh PR metadata fetch shows #242 has advanced beyond the previously recorded `870cf9219c947e692097d5ed42f33007c96fc9df`: current head is `963c14f4a7322dacd9d0f6627bd379f30ad59302`, base is `fa8cee047ae8e74c30c87cd94977c434bb1c7398`, with 81 commits and 15 changed files.
- Exact-SHA workflow-run lookup for `963c14f4a7322dacd9d0f6627bd379f30ad59302` confirms two successful runs: Step 102 source-import provenance guard (run `39465154135`) and AI free-tier safety checks (run `39465154137`). The trusted source-import path guard is not present in the returned workflow-run list, so the full required gate is still not confirmed for this head. No workflow was dispatched or rerun.
- Review metadata for #214, #243, and #242 currently shows no submitted reviews and no inline review threads. This is evidence that independent review remains outstanding, not evidence of approval.
- Issue #126 remains open. Its interactive three-lap checklist is still a human-operated acceptance gate; CI and scripted frame diagnostics cannot substitute for actual input feel and a manually driven full race.


### Current-state refresh — 2026-10-20 19:30 CEST

- Re-fetched live PR metadata: #214 remains draft at `db1f9747b8193d6cc4e77e0f69a073cd5e210eb5`, and #243 remains draft at `d1c5bf755a587765908a152fbf8874231bf6fe75`; both target `dev` at base SHA `c22bf27e0aca621ea735a85e9fedb92fd1933754`.
- Re-inspected workflow jobs for exact heads: #214 run `39327379050` and #243 run `39459255221` each have all four jobs completed successfully (host pause/resume tests, native GameCube build, Dolphin headless smoke, and non-blocking software-renderer diagnostic). This does not substitute for independent review or human interactive acceptance.
- #242 remains draft at `963c14f4a7322dacd9d0f6627bd379f30ad59302`; the current exact-head workflow-run listing confirms two successes only. No repeated CI was launched.
