# Branch lifecycle policy

This repository uses two permanent development references, retained recovery archives, and short-lived task branches. The live branch inventory and itemized retirement evidence are tracked in [issue #248](https://github.com/Master-Chiken/boonta-reborn-88/issues/248).

AI coordination, testing gates, provenance rules and the one-task queue are defined in [`PROJECT_OPERATING_RULES.md`](PROJECT_OPERATING_RULES.md).

## Permanent development references

- `main`: stable, release-ready integration branch.
- `dev`: normal gameplay and feature integration branch.

These are permanent development references. Do not rename, delete, or force-push them.

## Retained recovery archives

The following archive refs are retained recovery points, not development bases:

- `archive/branch-heads-20261019`: protected recovery archive.
- `archive/rival-ai-history-20261107`: pinned recovery history for the rival-AI work.
- `archive/branch-heads-20261126`: recovery checkpoint whose tree matches `main` and whose commit preserves the distinct branch tips present when it was created.

Do not rename, delete, force-push, or merge these archives wholesale into `main` or `dev`. New archives are not automatically permanent: each must be explicitly recorded in the live inventory and protected by the retirement workflow before another branch cleanup can rely on it.

The five references above (`main`, `dev`, and the three named archives) are the retained baseline for the 2026-11-26 branch cleanup. Any future change to that baseline requires a documented owner decision and an updated inventory in issue #248.

## Task branch rules

1. Create a task branch only when work is about to begin. One focused task should normally have one branch and one pull request.
2. Use a short, descriptive prefix such as `fix/`, `feat/`, `test/`, `docs/`, or `chore/`.
3. Normal gameplay changes target `dev`. Promotion of validated work from `dev` to `main` is a separate release action. Documentation-only work may follow its explicitly selected target when needed.
4. Do not keep a branch after its pull request has merged. Do not create a replacement branch merely to rename an existing one.
5. Before closing an unmerged pull request, decide whether its work is still needed; remove or archive the task branch only after confirming that its work is recoverable.
6. Keep branch commits recoverable through merged history or a verified recovery archive before retiring a branch. Never merge an archive wholesale into `main` or `dev`.
7. Never retire a branch while it is the head or base of an open pull request. Resolve the pull request first, then review the branch disposition separately.

## Branch budget

- **Warning threshold:** 10 total branch refs.
- **Red line:** more than 20 total branch refs.
- **Active-work target:** 10 or fewer branches with a recent commit or an open PR.
- An alert is a review trigger, not permission for unattended deletion. The governance workflow reports inventory and opens or updates one tracking issue; it does not delete or force-move branches.
- GitHub Actions runs after a branch-creation event and cannot retroactively block the creation. Enable GitHub's built-in **Automatically delete head branches** setting to clean up merged PR heads.

## Closeout checklist

When a task is complete:

- [ ] PR targets the correct branch and required CI checks pass.
- [ ] PR is merged, or intentionally closed with the reason recorded.
- [ ] The task branch has no other open PR using it.
- [ ] If merged, automatic PR-head deletion removed the branch; otherwise review its disposition.
- [ ] The branch inventory remains under budget, or the budget-alert issue documents the cleanup plan.

## Repository setting

An administrator should enable **Settings → General → Pull Requests → Automatically delete head branches**. This deletes the head branch after its PR is merged, except where branch protections or repository rules prevent deletion. Retained development and recovery references must be protected or explicitly excluded from the retirement workflow; open PR head/base refs must never be retired while their PR remains open.
