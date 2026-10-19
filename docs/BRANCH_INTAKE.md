# Branch intake queue

## Purpose

The Branch intake queue turns existing branch work into small, reviewable pull requests without creating new working branches. It complements the weekly branch-governance audit: the audit counts and classifies refs; the intake queue compares branch tips with the default branch and surfaces distinct changes that are small enough to review safely.

## What the automation does

- Runs twice daily and can be started manually from GitHub Actions.
- Scans existing branches and open pull requests, then compares unique branch tips with the default branch.
- Skips branches already represented by an open pull request, tips already under review, and branches with no unique file changes.
- Prioritizes small fixes and tests, then features, tooling, documentation, security, and maintenance work.
- Creates up to 5 draft pull requests per scheduled run; a manual run can select 1, 3, 5, or 10.
- Starts the existing GameCube prototype build and host regression pipeline for candidates that change the prototype source, tests, headers, data, Makefile, or tools.
- Defers oversized changes, overlapping changes, archives/proprietary-looking payloads, and Step 102/source-import work for deliberate review.

## Safety guarantees

- It does not create branches: each draft PR points to an existing branch.
- It does not push to the default branch, merge pull requests, force-push, or delete branches.
- It does not treat opening a PR or a green CI job as approval to merge.
- Changes touching the same path as an open or newly selected PR are serialized rather than piled into competing PRs.
- The original branch refs and commits remain available even after work is merged or deemed redundant.

## How to use it

1. Open the repository's Actions tab and select **Branch intake queue**.
2. Select **Run workflow**. Use 5 for the normal batch, or 10 when an accelerated review session is available.
3. Open the created draft PRs in priority order. Inspect their full diffs and mergeability, resolve any stale-base conflicts, and check the exact head SHA.
4. For prototype code candidates, inspect the dispatched GameCube build/host-test run. If dispatch failed or the branch changed during intake, run validation manually against the current branch head.
5. Use the mainline acceptance gate before merging. Do not merge changes with missing tests, unclear source provenance, unreviewed workflow/security changes, or unresolved visual/interactive validation requirements.

## Deliberate limitations

A branch being ahead of the default branch is evidence of unique commits, not evidence that the implementation is useful or correct. The automation therefore creates draft PRs only. Large or overlapping branches need an agent or maintainer to compare their diffs, identify the canonical implementation, reconcile conflicts, add tests, and retarget the resulting work to the current default branch.

The workflow uses GitHub-hosted Actions and the repository token; it requires no paid AI API and does not enable the repository's gated AI writer.
  
## First-run permission requirement

The first live queue run may report that GitHub Actions is not permitted to create pull requests, even though the workflow declares `pull-requests: write`. This is a separate repository setting. A repository admin must open **Settings → Actions → General → Workflow permissions**, enable **Allow GitHub Actions to create and approve pull requests**, and save. The queue uses this permission only to open draft PRs and has no automated merge, approval, direct-push, force-push, or branch-deletion step. The workflow now stops at the first permission-denied response and explains this setting instead of repeating failed create attempts for every candidate.

## Freshness gate

The intake queue automatically defers any candidate branch more than **10 commits behind `main`**. This prevents a tiny merge-base diff from making a very old implementation look safe when current files have evolved substantially. These branches are **not deleted or modified**; their unique changes should be reviewed against current `main` and cherry-picked or reconciled in a focused PR. Branches within the freshness window still pass the patch-equivalence, final-tree, overlap, size, and source-provenance checks before a draft PR is created.

