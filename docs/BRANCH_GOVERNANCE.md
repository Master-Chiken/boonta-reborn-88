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

**Verified ruleset gap as of 2026-10-23:** the live GitHub rulesets for `main` and `dev` require pull requests and an approving review, but neither ruleset defines required CI status checks. A green check can therefore provide evidence without necessarily blocking a merge when it fails or is missing.

Before describing CI as mandatory or enabling any auto-merge policy, the repository owner must configure the intended stable status checks under GitHub repository **Settings → Rules → Rulesets**, preserve the current approval/latest-push safeguards, and re-read the live ruleset to verify that the selected checks are enforced on the intended branch. Until that verification is complete, keep manual review as the merge gate and do not enable automatic merging. Ruleset configuration is an owner-side repository setting; this workflow does not change it.

### Suggested baseline checks for `main`

The following exact GitHub Actions check-run names were observed passing on recent pull requests and are produced by workflows that trigger for every pull request targeting `main`, without path filters:

- `Verify Gemini free-only guardrails` — static AI free-tier safety check.
- `Reject known held assets and data` — source-import/provenance policy plus its unit tests.
- `Check proposed source paths using trusted base policy` — trusted-base path-policy validation.

Select these under **Require status checks to pass before merging** for the `main` ruleset. If GitHub asks for the expected source, choose **GitHub Actions**. Recheck the current ruleset after saving; do not assume documentation or a green run makes a check mandatory.

**Do not globally require path-filtered checks as an initial step:** `Read-only Wii64 tooling unit tests`, `Branch automation self-test`, `GameCube first-render prototype build`, and Dolphin diagnostics only run for selected file paths or opt-in cases. Requiring a path-filtered workflow globally can leave unrelated pull requests stuck waiting for a check that did not run. If the project later wants every relevant gameplay/tooling test to be a formal merge gate, add and test an always-running aggregate check that runs those tests conditionally based on changed paths, then require that aggregate check.

These three baseline checks are the universal policy/provenance gate; they do **not** replace gameplay build tests, visible Dolphin acceptance, independent code review, or the owner's verification of the Google Free-tier billing state.

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
