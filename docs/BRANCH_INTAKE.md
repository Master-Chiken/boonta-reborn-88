# Branch intake queue

## Purpose

The Branch intake queue is a **manual review aid** for existing branch work. It helps a maintainer identify one small, non-duplicate candidate without creating new working branches or opening a flood of competing PRs. The queue is secondary to the active integration item in [Issue #156](https://github.com/Master-Chiken/boonta-reborn-88/issues/156).

## Current operating mode

- **Manual-dispatch only**: there is no cron schedule and no push-triggered intake run.
- **At most one draft PR per deliberate run**: `max_prs` is fixed at `1`; do not broaden it to batches.
- The workflow scans current refs and open PRs, compares branch tips with `main`, and reports candidates only after checking overlap, stale bases, patch-equivalent work, diff size, source/provenance holds, and current PR usage.
- A branch more than 10 commits behind `main` is deferred for deliberate re-evaluation; a stale branch is not deleted or modified just because it is old.
- Draft PR creation is optional and subordinate to review capacity. The current repository setting does **not** allow GitHub Actions to create and approve PRs. The workflow can therefore report that creation is blocked even when the inventory and shortlist are valid.

## Safety guarantees

- Intake does not create branches, push to `main`, merge PRs, force-push, or delete branch refs.
- It does not treat a branch being ahead of `main`, a draft PR, or green CI as evidence that code is correct or should be merged.
- It skips existing open-PR heads, duplicate/patch-equivalent work, overlapping candidates, oversized changes, and Step 102/source-import material that requires provenance review.
- Prototype candidates use the repository's GameCube build/host-test pipeline. Visible manual Dolphin controller testing is still required before claiming a complete playable race.
- Preserve useful and uncertain refs. The separate archive-backed retirement workflow has its own protection, exact-SHA, open-PR, and reachability guards; intake is never permission to retire a branch.

## How to use it

1. Open **Actions → Branch intake queue → Run workflow** only after the current `NOW` task in Issue #156 has reached a reviewable handoff.
2. Leave `max_prs` at `1`. Never re-run just to increase the candidate count.
3. Read the job summary and select at most one candidate. Compare its complete diff with current `main`, check the exact head SHA, and confirm that it does not overlap another active PR.
4. If draft-PR creation is blocked by the repository permission setting, **keep this permission disabled** for this task queue. Use the candidate report as a read-only shortlist; do not enable broad Actions PR-creation permission just to make the automation succeed.
5. Any selected candidate must have an explicit goal, acceptance criteria, test evidence, source/provenance assessment, and a human-reviewed integration decision. Park it if any of those are missing.

## Work-in-progress rule

Issue #156 is the single source of truth for `NOW`, `NEXT`, and `PARK`. Keep one active runtime implementation or integration candidate at a time. Do not dispatch another intake run while a candidate is waiting for validation, review, or integration. Finish the current handoff first: **make it work, make it good, make it fast**.

## Budget and source policy

The queue uses the existing GitHub Actions environment and does not require a paid AI API. Keep project spend at €0. Do not enable billing, commit commercial ROM/disc images or proprietary extracted assets, or import external source material without a documented provenance/licensing review.
