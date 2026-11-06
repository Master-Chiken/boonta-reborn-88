# Autonomous context budget

This file is the compact context rule for all scheduled Gemini, OpenRouter and Groq cycles.

## Why the limit exists

The dashboard and research queue issues are append-only histories. Their full bodies are tens of thousands of characters, and the canonical task ledger contains lengthy evidence arrays. Loading all of them into each provider request wastes free-tier tokens and can exceed provider tokens-per-minute limits before useful work begins.

## Mandatory retrieval budget

- Start with the owner-approved task brief already passed to the workflow and `docs/automation/task-ledger-summary.json`.
- Do not fetch full issue bodies or call `issue_read` for #156, #226 or #279. Do not read their full comment histories. Use a narrow issue/PR search only when a specific unresolved question requires it.
- Do not read the full `docs/automation/task-ledger.json`. It is the canonical write target; the compact summary is the read index. Read only the relevant task record when a planned update requires exact fields.
- Do not list every PR, branch, commit, issue or workflow run. Search only for the exact task/dependency, then inspect the smallest relevant result.
- Do not fetch full PR diffs or workflow logs unless the exact PR/job is relevant and failed. Never fetch attachments, images, media, ROMs, disc images, BIOS, binaries or the 452 KB route dossier.
- Keep newly retrieved repository/issue text below 1,500 tokens per cycle. Keep a provider request small enough to leave room for the prompt and tool schemas. If the provider reports a TPM, context-size, quota or rate-limit error, stop; do not repeat the same request.

## Source of truth and safe fallback

The workflow task brief is the owner-approved task direction for that cycle. The compact summary identifies active, blocked and in-review work without duplicating evidence histories. GitHub remains authoritative for live PR state and exact head SHAs; inspect only the specific PR needed to validate the selected task.

If the task brief and compact summary do not identify a safe next action, stop and return a precise `BLOCKED` report. Do not infer missing owner intent from old comments, stale prose or external repository content.

All existing clean-room, provenance, licensing, €0/free-tier, one-writer, branch and human-review safeguards continue to apply. This context budget does not authorize changing provider settings, secrets, billing, cooldowns, repository permissions or merge rules.
