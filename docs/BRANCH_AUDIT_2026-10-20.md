# Branch audit — 2026-10-20

## Purpose

Record a read-only inventory before reducing remote branches. This document is a decision aid, not authorization to delete refs. No branch deletion, force-push, workflow dispatch, or merge was performed for this audit.

## Current branch inventory

| Branch | Known role / comparison | Recommendation |
|---|---|---|
| `main` | Primary branch | Protect |
| `dev` | Integration branch; current target for gameplay PRs #214 and #243 | Protect |
| `archive/branch-heads-20261019` | Archived branch-head snapshot | Preserve until its checkpoint and recovery value are verified |
| `docs/reverse-engineering-80-20-20261020` | Head for PR #242; 69 commits ahead of `main`, 0 behind `main`; 14 files changed | Keep pending review and exact-head required checks |
| `fix/steering-stick-deadzone-20261019-14221623089412890411` | Compared with `dev`: 16 commits ahead, 1 behind; 4 files changed (two gameplay files and two cleanup workflows) | Do not merge as a gameplay-only change; split and review workflow changes independently |
| `fix/steering-stick-deadzone-clean-20261020` | Compared with `dev`: 2 commits ahead, 0 behind; only `gamecube-demo/source/gameplay_state.h` and `gamecube-demo/tests/test_gameplay_state.c` changed | Keep while PR #243 is under review |
| `fix/width-aware-rail-collision-20261017` | Compared with `dev`: 26 commits ahead, 1 behind; 10 files changed across gameplay, tests, Dolphin tooling, docs, and workflow | Keep while PR #214 is under review |

Branch search returned seven branches; a follow-up cursor page was empty.

## Pull request gates

### PR #214 — width-aware rail collision

- Open, draft, targets `dev`.
- Current head recorded as `db1f9747b8193d6cc4e77e0f69a073cd5e210eb5`.
- Reviewer requested: `Biddy-Pinky`; no review submission was found in the latest review-list query.
- Manual visible-Dolphin acceptance remains outstanding: rail/edge feel, boost drain and recharge, overheat, manual three-lap completion, restart, and longer-session stability.
- A recent exact-SHA workflow lookup showed only one PR-triggered workflow run; do not infer from that lookup alone that every historical CI job was rerun on the current SHA.

### PR #243 — analog steering deadzone

- Open, draft, targets `dev`.
- Current head recorded as `d1c5bf755a587765908a152fbf8874231bf6fe75`.
- Reviewer requested: `Master-Chiken`; no review submission was found in the latest review-list query.
- Automated tests/build/diagnostics were previously reported green, but manual controller-feel acceptance is still outstanding.
- A recent exact-SHA workflow lookup showed only one PR-triggered workflow run; recheck all required jobs on the current SHA before treating the full CI gate as newly confirmed.

### PR #242 — research-first documentation and workflow changes

- Open; explicitly returned to draft pending review.
- Head recorded as `a8961406723c453bc44e8d81b24d7a6d3b88451e`; base is `main`.
- The comparison to `main` reports 69 commits ahead and 14 changed files. Comparison to `dev` reports a substantially larger/diverged history, so its base must not be casually changed.
- On the current head, the latest workflow lookup showed success for `AI free-tier safety checks` and `Step 102 source-import provenance guard`; `trusted source-import path guard` was not visible for that exact SHA. Confirm or rerun it before considering the required gate complete.
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

1. Complete review and acceptance gates for #214 and #243.
2. Verify the missing exact-head check on #242 and review its broad history/base carefully.
3. Split cleanup automation out of #233 into a separately reviewed proposal; do not automatically carry over its deletion workflow.
4. Re-run this inventory after any merge, then propose branch retirement candidates with evidence. No deletion is authorized by this document.
