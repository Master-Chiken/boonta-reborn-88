# Branch governance — two-permanent-branch model

## Target branch model

The project has **two permanent integration branches**:

- **`main` — stable/release branch.** This remains the repository default branch and is protected. Only a reviewed promotion from `dev` should normally reach `main`.
- **`dev` — integration branch.** New implementation work is reviewed and integrated here first. Protect this branch before relying on it as the default PR target.

Task branches and recovery references may exist temporarily. “Two branches” means two permanent integration branches, not that an open pull request may never have its own branch.

## Contribution workflow

1. Start a focused temporary branch from the current `dev`, preferably named `task/<short-name>`, `fix/<short-name>`, `feat/<short-name>`, or `docs/<short-name>`.
2. Open a pull request targeting `dev`. Keep the PR draft while work is incomplete. Review the complete diff and require the relevant CI checks to pass on the exact head SHA.
3. Merge into `dev` only after review. Do not push directly to `main` or `dev`.
4. Promote integrated work by opening a separate PR from `dev` to `main`. The release PR must pass the relevant checks and the product acceptance gates; a green build alone does not prove manual playability.
5. Retire the temporary task branch after its PR is merged or intentionally closed and its current tip is known to be recoverable. Reuse a branch only if it is still dedicated to the same task.

The repository default branch remains `main` for stable public browsing and releases. The branch-intake automation targets `dev` for candidate changes. It must exclude `main`, `dev`, and all `archive/*` or `recovery/*` references from normal task intake.

## No-loss branch retirement

- **Do not delete branches automatically.** An agent may inventory, compare, classify, and prepare a deletion recommendation, but a human maintainer must authorize each retirement.
- Before retiring a ref, record its exact current SHA and confirm it has not moved since the inventory.
- Check all open PR head references. Never retire a branch used by an open PR.
- Compare the branch tip with both `dev` and `main`; confirm all unique changes are either integrated, deliberately retained elsewhere, or explicitly rejected after review.
- Confirm the exact tip is reachable from `main`, `dev`, or a verified recovery checkpoint. A JSON file containing a SHA is not, by itself, a recovery mechanism.
- Remove only one ref at a time, verify the result, then refresh the inventory. Do not force-push or rewrite commits to reduce the count.
- A branch being behind `main` with no unique commits is a strong retirement candidate, but open PRs, protection, and the current ref SHA still need checking.

## Recovery references

The project is temporarily retaining recovery references while the migration is completed:

- `archive/branch-heads-20261019` is the existing protected archive. Never merge this branch wholesale into `main` or `dev`; its history intentionally includes captured branch tips.
- `recovery/branch-heads-20261019-verified` is a verified multi-parent checkpoint. Its checkpoint commit has the exact pre-cleanup live branch heads as parents and the accompanying snapshot manifest records their names and SHAs.
- Keep these recovery references until the owner confirms the needed unique work has been accounted for and the branch cleanup is complete. They are temporary safety references, not permanent integration branches.

## Manual verified ref-retirement workflow

The `.github/workflows/retire-verified-branch.yml` workflow is an owner-operated tool for the **five refs explicitly reviewed in the inventory**. It is manual-only and is available for use after the workflow has been merged to `main` and `main` remains the repository default.

Before it can retire a ref, it requires the repository owner account, a run from `main`, a selection from the fixed allowlist, the exact pinned SHA, and the branch name typed again as confirmation. It checks the current head SHA, rejects protected refs, rejects any open PR that uses the branch as head or base, and confirms that the exact tip is reachable from the protected recovery archive. It repeats the head/protection, open-PR, and archive-ancestry checks immediately before the single DELETE-ref operation, then verifies that GitHub no longer lists the branch.

The allowlist is intentionally limited to `recovery/branch-heads-20261019-verified` and these four refs whose tips were verified as already represented in `main`: `feat/game-finish-banner-label-20261017`, `feat/rocky-canyon-silhouette-20261017`, `feat/source-driven-racer-mesh-texture-20261017`, and `test/dolphin-pause-state-acceptance`.

This workflow does not retire arbitrary branches, does not run on push/schedule/PR events, and cannot merge or rewrite commits. A ref outside this allowlist requires a separate inventory, review, and owner-authorized retirement. Because deletion uses GitHub's ref API, there remains a tiny race between the final read and DELETE if someone moves a branch concurrently; avoid pushing to a retirement candidate during a run. If any check fails, the workflow stops before deletion.

## Automated audit and intake

The `Branch governance audit` workflow reports branch count, open-PR references, recent activity, and candidates for review. It must not delete or merge branches.

The `Branch intake queue` compares candidate branches with `dev` and opens draft PRs targeting `dev`. It does not push to either permanent branch, merge PRs, force-push, or delete references. Step 102/source-import work and large, stale, or overlapping changes remain deferred for manual review.

## Current migration safeguards

- `main` is protected. Configure an equivalent protection ruleset for `dev` before merging the migration PR or retargeting ongoing work to `dev`.
- Existing PRs should not be retargeted merely to conform to the new model while their review or acceptance gates are active.
- The rail-collision gameplay PR remains draft until the human-operated Dolphin acceptance checklist is recorded.
- Branch-count reduction must never be used as a reason to merge unreviewed gameplay, provenance-sensitive content, or the multi-parent recovery archive.
