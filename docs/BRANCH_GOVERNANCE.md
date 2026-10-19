# Branch governance — Boonta Reborn 88

## Policy: unlimited branch count, disciplined task completion

- **No project-defined numerical cap** on total or active branches. Total and active counts remain informational; branch inventory does not block useful work, fail an audit, or trigger branch deletion.
- **Finish work before starting more work.** Jules must handle one implementation task at a time and must not start another independent task until the current task has reached a review-ready handoff: implementation complete, relevant tests attempted, failures fixed where practical, final diff reviewed, PR submitted, relevant CI checks terminal, and a truthful completion report posted.
- If external dependencies genuinely block completion, Jules must document the exact blocker and evidence, preserve the branch, list completed work/tests/remaining steps, and wait for a decision. A red test alone is not permission to abandon a task; fix it where possible.
- A task is handed off when its PR is reviewable and relevant CI checks are complete, or when a concrete external blocker is explicitly recorded. Human review and merge remain separate; Jules does not merge automatically.
- Unlimited branches do **not** mean unlimited simultaneous tasks, duplicate branches, or speculative work. Each branch must correspond to a concrete task, a clearly scoped workstream, or preserved historical work. Prefer one focused branch per task and continue an existing branch for the same task.
- Branch count does not control concurrency. Jules has one active implementation task at a time. Biddy-Pinky may run up to two genuinely independent workstreams under the project’s existing policy: at most one runtime implementation plus one non-overlapping research/documentation/tooling/review task.
- Do not push directly to main. Use focused pull requests, review the full diff, and validate exact-head CI before merge. No automatic merge, force-push, history rewriting, or automatic deletion of useful branches.
- Keep the budget at €0. Never enable billing or use paid tools. Preserve clean-room and source-provenance restrictions.

## Single-maintainer delivery queue (work-in-progress control)

- `Issue #201` is the single source of truth for the active integration queue. It must contain one `NOW` item, one `NEXT` item, and a short parked list; other open issues/PRs do not automatically become active tasks.
- **One active runtime implementation or integration candidate at a time.** This limits in-flight decision/review work, not the total number of branches. Preserve unique queued work and do not delete branches or close useful PRs merely to reduce counts.
- Do not start a new runtime PR while the current runtime PR is being implemented, waiting on required checks/review, or ready for integration. Reuse its branch/PR for follow-up fixes.
- Independent documentation/research can be recorded as `NEXT` or `PARKED`, but should not generate another PR requiring maintainer attention until the current `NOW` item has a reviewable handoff. The exception is an urgent security, provenance, or blocking build/CI issue.
- Every active PR must have a narrow scope, linked issue, exact-head CI evidence, explicit manual checks still needed, overlap/dependency note, and one next action.
- Integrate sequentially. After a runtime or workflow PR is merged, retest every remaining PR that overlaps the changed files against its exact current head/base. Don't batch-merge and don't merge merely to reduce open counts.
- When the maintainer is blocked or unavailable, agents should complete the current task's tests/self-review and leave a truthful handoff, not open unrelated PRs to appear busy.

## Coordination alerts (not caps)

- **General contributors:** show an informational coordination alert at **105 total repository branches**. At that point, finish and hand off the current task before starting an unrelated task; do not abandon or interrupt the task already in progress.
- **Biddy-Pinky:** use a separate informational threshold of **200 total repository branches**, rather than applying the general 105-branch alert to that contributor. Biddy-Pinky may still run up to two genuinely independent workstreams under the existing policy.
- These are reminders for task sequencing, not branch caps. Neither threshold may fail CI, block creation of useful branches, create issues automatically, trigger merges, or delete/rewrite history. The inventory workflow only reports whether each alert threshold has been reached.

## What counts as active?

The audit uses a 30-day/open-PR heuristic to describe branch activity. This is an observability measure only, not a target, limit, work gate, or proof that a branch is safe to delete.

## Automated audit

The Branch governance audit workflow runs weekly and on demand. It reports:
- total and active branch counts;
- open pull requests;
- branch tips with known or unknown commit dates;
- inactive branch references that may be reviewed manually.

It does not impose a numeric cap, fail because of branch count, create an issue just because a count target is exceeded, merge branches, or delete branches automatically. It reports the general 105-branch coordination alert and the Biddy-Pinky-specific 200-branch alert without interrupting active work. It should not run a full inventory on every branch-creation event.

## Manual review sequence

1. Identify a branch's purpose, latest commit, linked task/PR, and whether its work is represented in main.
2. Check whether the responsible agent has completed the task lifecycle or documented a real blocker.
3. Group duplicate or related changes and pick a canonical branch only when duplication is proven.
4. Test and integrate useful work through reviewed PRs.
5. Preserve historical or uncertain branches until their contents and dependencies are understood. Do not clean up branches merely to reach a number.

## Automated intake of branch work

The companion [Branch intake queue](BRANCH_INTAKE.md) is **manual-dispatch only**. It can surface at most **one draft PR per deliberate run**. It has no cron schedule and no push-triggered PR creation. This prevents the workflow from continuously adding review requests while the owner is already processing the active queue. It still screens stale bases, overlapping paths, oversized changes, patch-equivalent work, and Step 102/source-import provenance holds.

The intake queue does not merge PRs, push to the default branch, force-push, or delete history. A draft PR is only a review surface; each candidate must pass exact-head checks and the mainline acceptance gate before a maintainer merges it. Do not dispatch it again until the current candidate has been accepted, parked, or rejected in Issue #201.

## Dependabot update-volume control

- GitHub Actions version updates run weekly, not daily.
- Group all major `actions/*` updates into one candidate PR; group minor/patch updates separately.
- Keep `open-pull-requests-limit: 1` for version updates so Dependabot does not leave a queue of routine upgrade PRs waiting for one maintainer.
- This is an update-PR workload limit, not a ban on updates. Security alerts/updates remain enabled and should still receive priority review; do not disable security updates to reduce noise.
- Grouped dependency changes still need current-head CI and review; do not merge a group of major action upgrades just because Dependabot opened it.

