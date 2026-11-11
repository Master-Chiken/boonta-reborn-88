# Boonta Reborn — engineering operating rules

Attach this as a shared Paperclip company skill to every Boonta agent.

## Mission and source of truth

Build an original, clean-room racing game for Nintendo GameCube first and Wii second. The repository prototype is early-stage; never describe it as fully playable or hardware-verified without human evidence.

Repository: `Master-Chiken/boonta-reborn-88`. Before every task, read `README.md`, `docs/automation/task-ledger.json`, `docs/automation/task-ledger-summary.json`, the relevant task and source issue (normally #226).

The canonical GitHub task ledger owns task identity, target branch, acceptance criteria and completion state. Paperclip issues mirror tasks; they do not silently replace the ledger.

## One-writer policy

- At most one coding task may be active.
- Before starting, inspect `main`, open PRs, the ledger and recent CI. Never duplicate a task represented by an open task PR.
- Preserve the exact `task_id`, target branch and acceptance criteria from the ledger.
- One model/provider invocation per heartbeat. Never launch a second provider as an immediate fallback in the same run.
- If an owner, identity, provider, free-tier or quota gate fails, report BLOCKED and stop. Do not retry through another key, model, account or billing route.
- Keep the Paperclip routine disabled until the owner completes a separate cutover from the current GitHub Actions schedule. Never run both schedulers as active writers.

## GitHub delivery contract

- Create a unique branch from the task's current target branch.
- Open a focused PR; do not merge it.
- Include the exact PR-body line `BOONTA_TASK_ID: <task_id>`.
- Run relevant synthetic/local tests and let GitHub Actions validate the exact PR head SHA.
- An open unmerged PR is `in_review`, never `completed`. Mark a task completed only after its PR is merged and the canonical ledger is reconciled.
- Never bypass branch protection, required reviews, status checks, CODEOWNERS or repository rules.

## Zero-cost policy

- Use only a provider credential and model explicitly confirmed by the owner as Free-tier with no paid fallback.
- Do not infer that a model is free from its name or availability in a UI.
- Do not enable billing, buy credits, upgrade a plan or switch to a paid endpoint.
- Paperclip budgets are monitoring/pause controls, not proof of zero-cost inference. The actual €0 boundary is the provider plan, credential and allowed model route.
- If pricing, Free-tier status or remaining quota is uncertain, do not call the provider. Report BLOCKED with a non-secret reason.

## Clean-room and platform boundaries

- Never upload, commit, paste into issues or send to hosted agents: ROMs, disc images, DOL/REL files, commercial executables, extracted commercial models/textures/audio, private analysis databases or other game-derived binary payloads.
- Do not download commercial game assets or bulk archives into this repository or CI.
- Import only file-level reviewed assets with compatible redistribution terms; record source URL, exact revision, path, hash and licence.
- Keep PC, Nintendo 64, GameCube and Wii findings separate. PC/N64 findings do not prove GameCube/Wii behavior or compatibility.
- Use synthetic or source-authored fixtures in CI. Keep owner-controlled lawful inputs local.
- Distinguish verified facts, hypotheses, estimates and unknowns.

## Validation and authority

Before reporting PROGRESS, verify that the PR belongs to this repository, carries the exact task ID, targets the ledger's base branch, has a non-empty diff, and that every required check passed on the current PR head SHA. Pending or skipped required checks are not passes. Otherwise report BLOCKED.

Agents may research, edit their assigned branch, run approved tests and open PRs. Agents may not merge, change secrets, repository variables, billing, GitHub App settings, branch protection, workflow permissions or integration scope. Human review remains mandatory.
