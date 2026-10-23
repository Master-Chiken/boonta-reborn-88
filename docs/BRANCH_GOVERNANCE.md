# Branch governance — Boonta Reborn 88

## Policy

- **Active-branch target:** no more than 10 active working branches.
- **Total-count warning:** 10 or more branch refs.
- **Red line:** more than 20 total branch refs.
- **Do not delete branches automatically.** This is an explicit project rule.
- The total branch count may remain above the active-branch target while inactive or historical branches are retained.
- Preserve every branch's commits and useful work. Prefer reviewing, testing, and merging completed work into `main`; do not merge merely to reduce the count.
- Keep `main` protected. Do not describe CI as merge-blocking unless the applicable GitHub ruleset explicitly requires the selected status checks.
- Avoid creating a branch when an existing work branch can safely be reused. Prefer one focused branch per task and avoid duplicate `-v2` / `-v3` branches unless the reason is documented.
- An AI agent may inventory branches, classify candidates, prepare consolidation PRs, and report recommendations. It must not delete branches or force-push without explicit human authorization.

## Merge gates and required status checks

**Live ruleset state verified on 2026-10-23:** `Protect main 2` is active for `main` and currently requires a pull request, one approving review, approval of the latest push, and the three required status checks listed below. The owner saved this ruleset and the live GitHub API confirms the checks are enforced. The `Protect dev` ruleset still requires a pull request and an approval but does not define required CI status checks. Therefore, CI is a merge-blocking gate for `main`, but not yet for `dev`.

Ruleset configuration is an owner-side repository setting; repository workflows do not change it. Preserve existing approval/latest-push safeguards. Do not enable automatic merging merely because these checks are green: independent review, scope review, and the applicable gameplay acceptance gate remain necessary.

### Required status checks for `main` (live verified 2026-10-23)

The following exact GitHub Actions check-run names are now configured in the `main` ruleset and were observed passing on recent pull requests. They are triggered for every pull request targeting `main`, without path filters:

- `Verify Gemini free-only guardrails` — static AI free-tier safety check.
- `Reject known held assets and data` — source-import/provenance policy plus its unit tests.
- `Check proposed source paths using trusted base policy` — trusted-base path-policy validation.

The ruleset also requires the pull-request branch to be up to date before merging. Do not describe unrelated path-filtered tests as globally required.

### Remaining gap on `dev`

The `Protect dev` ruleset does not currently require CI status checks. Do not copy the `main` check list directly onto `dev` until the workflows are confirmed to trigger on PRs targeting `dev`; otherwise GitHub could wait for required checks that never run. If `dev` is meant to have the same enforcement, first add/verify stable checks or an always-running aggregate gate for `dev`, then configure and re-read the live `dev` ruleset.

**Do not globally require path-filtered checks:** `Read-only Wii64 tooling unit tests`, `Branch automation self-test`, `GameCube first-render prototype build`, and Dolphin diagnostics only run for selected file paths or opt-in cases. Requiring a path-filtered workflow globally can leave unrelated pull requests stuck waiting for a check that did not run. If the project later wants every relevant gameplay/tooling test to be a formal merge gate, add and test an always-running aggregate check that runs those tests conditionally based on changed paths, then require that aggregate check.

The three baseline checks on `main` are a universal policy/provenance gate; they do **not** replace gameplay build tests, visible Dolphin acceptance, independent code review, or the owner's verification of the Google Free-tier billing state.

## What counts as active?

The GitHub Actions audit treats a branch as active if it is the default branch, has an open pull request, its latest commit is no more than 30 days old, or its commit date cannot be verified. The unknown-date rule is deliberately conservative. This is a practical heuristic, not proof that a branch is safe to retire.

## Automated audit

The `Branch governance audit` workflow runs weekly, on demand, when a branch is created, after relevant policy changes reach `main`, and after the archived-branch cleanup workflow completes. It reports:
- total branches and active branches;
- whether the 10-active-branch target is exceeded, whether the 10-ref warning is reached, and whether the total exceeds the 20-ref red line;
- branches with open pull requests;
- branches with no recent commits that may be reviewed for consolidation.

When the total-count warning or red line is reached, it opens or updates one tracking issue rather than spamming comments. It does not merge or delete branches automatically. The issue should be worked through by the project maintainers and AI agents, preserving branch contents and contributions.

## Manual review sequence

1. Identify each branch's purpose, latest commit, open PR, and whether its commits are already represented in `main`.
2. Group duplicate or related work and select a canonical branch for each task.
3. Test and merge useful work through PRs.
4. Keep historical or uncertain branches untouched until their contents have been reviewed and preserved.
5. Report active count and remaining blockers; aim for 10 or fewer active branches, investigate the total-count warning at 10 refs and red line above 20, and do not delete branch refs automatically.

## Automated intake of branch work

The companion [Branch intake queue](BRANCH_INTAKE.md) compares existing branch tips with the default branch and prepares a limited number of draft PRs for small, distinct changes. It runs the existing GameCube prototype tests for relevant code candidates and defers overlapping, oversized, and Step 102/source-import changes for manual review.

The intake queue does not create branches, merge PRs, push to the default branch, force-push, or delete history. A draft PR is only a review surface; each candidate must still pass the exact-head checks and the mainline acceptance gate before a maintainer merges it.
