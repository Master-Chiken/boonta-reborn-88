# Branch governance — Boonta Reborn 88

## Policy

- **Target:** no more than 30 active working branches.
- **Do not delete branches automatically.** This is an explicit project rule.
- The total branch count may remain above 30 while inactive or historical branches are retained.
- Preserve every branch's commits and useful work. Prefer reviewing, testing, and merging completed work into `main`; do not merge merely to reduce the count.
- Keep `main` protected and require relevant CI checks before merging.
- Avoid creating a branch when an existing work branch can safely be reused. Prefer one focused branch per task and avoid duplicate `-v2` / `-v3` branches unless the reason is documented.
- An AI agent may inventory branches, classify candidates, prepare consolidation PRs, and report recommendations. It must not delete branches or force-push without explicit human authorization.

## What counts as active?

The scheduled GitHub Actions audit treats a branch as active if it is the default branch, has an open pull request, or its latest commit is no more than 30 days old. This is a practical heuristic, not proof that a branch is safe to retire.

## Automated audit

The `Branch governance audit` workflow runs weekly and on demand. It reports:
- total branches and active branches;
- whether the 30-active-branch target is exceeded;
- branches with open pull requests;
- branches with no recent commits that may be reviewed for consolidation.

If the target is exceeded, it opens a single tracking issue (if one is not already open). It does not merge or delete branches automatically. The issue should be worked through by the project maintainers and AI agents, preserving branch contents and contributions.

## Manual review sequence

1. Identify each branch's purpose, latest commit, open PR, and whether its commits are already represented in `main`.
2. Group duplicate or related work and select a canonical branch for each task.
3. Test and merge useful work through PRs.
4. Keep historical or uncertain branches untouched until their contents have been reviewed and preserved.
5. Report active count and remaining blockers; aim for 30 or fewer active branches without deleting branch refs.

## Automated intake of branch work

The companion [Branch intake queue](BRANCH_INTAKE.md) compares existing branch tips with the default branch and prepares a limited number of draft PRs for small, distinct changes. It runs the existing GameCube prototype tests for relevant code candidates and defers overlapping, oversized, and Step 102/source-import changes for manual review.

The intake queue does not create branches, merge PRs, push to the default branch, force-push, or delete history. A draft PR is only a review surface; each candidate must still pass the exact-head checks and the mainline acceptance gate before a maintainer merges it.
