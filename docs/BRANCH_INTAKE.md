# Branch intake queue

## Purpose

The Branch intake queue turns existing branch work into small, reviewable pull requests without creating new working branches. It compares candidate branch tips to the **integration branch `dev`** and opens draft PRs targeting `dev`. The stable repository default remains `main`; release promotion is a separate PR from `dev` to `main`.

## What the automation does

- Runs twice daily and can be started manually from GitHub Actions.
- Scans existing branches and open pull requests, then compares unique branch tips with `dev`.
- Skips `main`, `dev`, archive/recovery references, branches already represented by an open PR, tips already under review, and branches with no unique file changes.
- Creates up to 5 draft PRs per scheduled run; a manual run can select 1, 3, 5, or 10.
- Starts the existing GameCube prototype build and host regression pipeline for candidates that change prototype source, tests, headers, data, Makefile, or tools.
- Defers oversized changes, overlapping changes, stale branches, archives/proprietary-looking payloads, and Step 102/source-import work for deliberate review.

## Safety guarantees

- It does not create branches: each draft PR points to an existing task branch.
- It does not push to `main` or `dev`, merge pull requests, force-push, or delete branches.
- It does not treat opening a PR or a green CI job as approval to merge.
- It keeps original refs and commits available until a human separately reviews and authorizes branch retirement.
- It treats recovery references as preservation only; they must never be merged wholesale into the product branches.

## How to use it

1. Open the repository's Actions tab and select **Branch intake queue**.
2. Select **Run workflow**. Use 5 for a normal batch, or 10 when enough review time is available.
3. Open the created draft PRs in priority order. Inspect the complete diff against current `dev`, resolve stale-base conflicts, and check the exact head SHA.
4. For prototype code candidates, inspect the dispatched GameCube build/host-test run. If dispatch failed or the branch changed during intake, run validation against the current branch head.
5. Require a maintainer review and the relevant checks before merging into `dev`. Use a separate reviewed `dev` → `main` PR for release promotion, and follow `docs/MAINLINE_ACCEPTANCE_GATE.md`.

## Deliberate limitations

A branch being ahead of `dev` is evidence of unique commits, not proof that the implementation is useful or correct. The automation creates draft PRs only. Large or overlapping branches need a maintainer to compare their diffs, reconcile conflicts, add tests, and retarget the resulting work to current `dev`.

The workflow uses GitHub-hosted Actions and the repository token; it requires no paid AI API and does not enable the repository's gated AI writer.

## First-run permission requirement

The first live queue run may report that GitHub Actions is not permitted to create pull requests, even though the workflow declares `pull-requests: write`. A repository admin must open **Settings → Actions → General → Workflow permissions**, enable **Allow GitHub Actions to create and approve pull requests**, and save. The queue uses that permission only to open draft PRs and has no automated merge, approval, direct-push, force-push, or branch-deletion step.

## Freshness gate

The intake queue automatically defers any candidate branch more than **10 commits behind `dev`**. This prevents a tiny merge-base diff from making an old implementation look safe after the current integration branch has evolved. These branches are not deleted or modified; their unique changes should be reviewed against `dev` and cherry-picked or reconciled in a focused PR. Branches inside the freshness window still pass patch-equivalence, final-tree, overlap, size, and source-provenance checks before a draft PR is created.
