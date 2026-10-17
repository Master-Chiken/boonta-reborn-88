# Branch governance — Boonta Reborn 88

## Policy: unlimited branch count, disciplined task completion

- **No project-defined numerical cap** on total or active branches. Historic targets of 30 active branches and thresholds of 100/105/200 branches are superseded. Counts are informational; they must not block useful work, fail an audit, or trigger branch deletion.
- **Finish work before starting more work.** Jules must handle one implementation task at a time and must not start another independent task until the current task has reached a review-ready handoff: implementation complete, relevant tests attempted, failures fixed where practical, final diff reviewed, PR submitted, relevant CI checks terminal, and a truthful completion report posted.
- If external dependencies genuinely block completion, Jules must document the exact blocker and evidence, preserve the branch, list completed work/tests/remaining steps, and wait for a decision. A red test alone is not permission to abandon a task; fix it where possible.
- A task is handed off when its PR is reviewable and relevant CI checks are complete, or when a concrete external blocker is explicitly recorded. Human review and merge remain separate; Jules does not merge automatically.
- Unlimited branches do **not** mean unlimited simultaneous tasks, duplicate branches, or speculative work. Each branch must correspond to a concrete task, a clearly scoped workstream, or preserved historical work. Prefer one focused branch per task and continue an existing branch for the same task.
- Branch count does not control concurrency. Jules has one active implementation task at a time. Biddy-Pinky may run up to two genuinely independent workstreams under the project’s existing policy: at most one runtime implementation plus one non-overlapping research/documentation/tooling/review task.
- Do not push directly to main. Use focused pull requests, review the full diff, and validate exact-head CI before merge. No automatic merge, force-push, history rewriting, or automatic deletion of useful branches.
- Keep the budget at €0. Never enable billing or use paid tools. Preserve clean-room and source-provenance restrictions.

## What counts as active?

The audit uses a 30-day/open-PR heuristic to describe branch activity. This is an observability measure only, not a target, limit, work gate, or proof that a branch is safe to delete.

## Automated audit

The Branch governance audit workflow runs weekly and on demand. It reports:
- total and active branch counts;
- open pull requests;
- branch tips with known or unknown commit dates;
- inactive branch references that may be reviewed manually.

It does not impose a numeric cap, fail because of branch count, create an issue just because a count target is exceeded, merge branches, or delete branches automatically. It should not run a full inventory on every branch-creation event.

## Manual review sequence

1. Identify a branch's purpose, latest commit, linked task/PR, and whether its work is represented in main.
2. Check whether the responsible agent has completed the task lifecycle or documented a real blocker.
3. Group duplicate or related changes and pick a canonical branch only when duplication is proven.
4. Test and integrate useful work through reviewed PRs.
5. Preserve historical or uncertain branches until their contents and dependencies are understood. Do not clean up branches merely to reach a number.

## Automated intake of branch work

The companion documentation BRANCH_INTAKE.md describes how the branch intake queue compares candidate tips with the default branch and prepares reviewable PRs for small, distinct changes. It runs relevant tests and defers overlapping, oversized, and Step 102/source-import changes for manual review.

The intake queue does not merge PRs, push to the default branch, force-push, or delete history. A draft PR is only a review surface; each candidate must pass exact-head checks and the mainline acceptance gate before a maintainer merges it.
