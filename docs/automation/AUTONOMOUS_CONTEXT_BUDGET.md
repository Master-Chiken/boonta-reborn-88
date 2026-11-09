# Autonomous provider context budget

This is the shared context and execution budget for scheduled Gemini, OpenRouter Free and Groq Free cycles.

## Non-negotiable cycle budget

- One model provider invocation at most per Boonta Autonomous Loop run. If a provider fails, do not call the next provider in that same run. Advance only on a later eligible scheduled cycle after the earlier provider's same-day cooldown is active.
- Provider order: Gemini first; OpenRouter Free only on a later cycle when Gemini is cooldown-skipped; Groq Free only on a later cycle when both Gemini and OpenRouter are cooldown-skipped.
- A successful preflight is configuration evidence, not model execution or project progress. A run is engineering progress only when a provider invocation completed and its report is validated against a new or advanced open PR at the exact current head SHA.
- Never use a paid route, billing fallback, additional provider, or secret rotation to bypass a Free-tier quota. The project budget remains €0.

## Context and tool limits

- Start with the owner-approved workflow brief and `docs/automation/task-ledger-summary.json`. A read-only task-eligibility preflight must confirm exactly one eligible task before any provider is launched. Read the required project/provenance policies once; then read only files directly needed for the selected task.
- Keep newly retrieved repository/issue text below **1,500 tokens per cycle**. Keep full issue bodies and comment histories for #156, #226 and #279 out of provider context. Do not enumerate all PRs/branches or fetch attachments, images, media, binaries, ROMs, disc images, BIOS, or the approximately 452 KB route dossier.
- Do not fetch the full `docs/automation/task-ledger.json` for task selection. Use the compact summary; read a narrow task record only when a justified ledger update is required.
- The global eligibility preflight rejects malformed/ambiguous task ledgers, multiple active tasks, or an active task that already has a PR/head. The only blocked-task exception is the explicitly tracked post-cooldown activation bootstrap, and all three providers share the same `task_ready` gate.
- Gemini CLI: pin the verified `0.67.0` release; exactly 1 attempt per invocation, automatic fetch-error retries disabled, maximum 3 session turns, and 11 GitHub MCP tools: add_issue_comment, create_pull_request, pull_request_read, create_branch, get_file_contents, push_files, search_pull_requests, list_workflow_runs, list_workflow_jobs, get_workflow_run and get_job_logs. Actions tools are restricted to the exact PR-head CI and failed-job diagnostics.
- OpenRouter Free: OpenCode v1.19.5, maximum 3 build steps and the same 11 GitHub MCP tools. Before inference, the GET-only key preflight requires at least 3 remaining daily Free requests as a minimum no-go reserve equal to the configured build-step ceiling; a smaller balance is skipped before model invocation. OpenCode build steps are agentic iterations, not a promise that every cycle uses exactly 3 provider requests: actual request count can vary, so this reserve is not a guarantee of cycle completion. A process-group watchdog stops OpenCode on the first explicit Free daily/minute quota, 429/rate-limit, TPM, oversized-request or authentication refusal; a signal handler also terminates the child process group when the 180-second hard timeout is reached. Actions tools are restricted to the exact PR-head CI and failed-job diagnostics.
- The branch automation self-test executes both the static provider-handoff contract checker and the production OpenRouter watchdog heredoc using a local fake `opencode` process. Runtime cases verify first-refusal HTTP 429 handling, descendant-process termination, normal project output without false positives, SIGTERM cleanup and preservation of the captured report. These tests are offline and do not consume provider quota.
- Groq Free: OpenCode v1.19.5, maximum 3 build steps, 3,072 context tokens, 512 output tokens and the reviewed six GitHub MCP writer tools only; newly retrieved text below 800 tokens and prompt ceiling 5,000 characters; 90-second hard timeout. The workflow watches the combined CLI output and terminates the process group on the first Groq TPM, HTTP 429/rate-limit, HTTP 401/authentication or Free-quota refusal, preventing OpenCode's internal retry loop from repeating requests after a terminal provider refusal. The mitigation does not weaken the provider cooldown or substitute for a live exact-account verification. Its watchdog also handles SIGTERM/SIGINT by terminating the process group. Offline integration tests execute both production watchdogs with fake local OpenCode processes, covering TPM/quota, HTTP 401/429, descendant cleanup, normal output and runner-signal cleanup without provider calls.
- The autonomous loop snapshots only currently open PR heads and records a timestamp. A cycle-fresh report must cite a PR created after that snapshot or an existing open PR advanced after it; reopening an older closed PR is not progress.
- Shell is denied to the OpenCode agents. Repository writes use one branch, one logical push_files operation and one reviewable PR. Never merge, auto-merge, force-push or write to protected branches.
- Do not reread the same file, call broad search/list operations or retry unavailable tools. Keep tasks small enough for the per-provider turn/step budget.

## Failure handling
- Cooldown preflight reads only issue #226 comments updated since 00:00 UTC on the current day (`since`), then verifies the embedded UTC date. Keep this bounded query in the global preflight and every provider-specific cooldown guard; the failure-recording step may still locate/update the persistent marker.


- **503 / temporary unavailability:** Gemini makes one model attempt only; after a 503 or TPM refusal, the invocation fails closed and its cooldown prevents another request until the next UTC day. A later scheduled cycle may try the next Free-only provider. Network `fetch failed` retries are disabled.
- **429 / TPM, context-size or request-too-large:** stop immediately, do not repeat the same request, and reduce the prompt/retrieved context/tool surface before the next attempt.
- **Daily Free quota or reserve insufficient:** do not call inference; wait for the next UTC day. OpenRouter preflight requires a reserve equal to its maximum configured build steps (currently 3), rather than starting with only 1–2 requests left. The API reports the counter on a UTC-day basis, and failed attempts count toward the cap. Never add credits or use a paid route.
- **Authentication or Free-tier attestation failure:** stop before inference. Do not ask for a new key when the same-run authentication already succeeded.
- If a timeout terminates a provider, treat the invocation as failed and respect its cooldown. A successful workflow preflight or cooldown check never counts as a model call.

- **Valid BLOCKED report:** do not mark the provider as failed. Persist a separate task-level UTC-day backoff marker so scheduled cycles do not spend another model call repeating the same blocked task. A validated PROGRESS report clears that marker. Owner-authorized manual dispatch or a qualifying main-branch push can re-evaluate earlier; the next UTC day also rechecks automatically.

## Reverse-engineering and provenance

Before implementation, inspect existing Boonta source, generated outputs, exporters, parsers, fixtures, tests, docs and directly related PRs. Prefer DISCOVER → VERIFY → EXTRACT/CONVERT/REUSE → INTEGRATE → TEST. Record exact source revision, platform/version, license/provenance, recovery decision and unknowns. Keep PC, N64, Dreamcast and GameCube/Wii behavior separate. Never send commercial game data or unclear-provenance material to hosted agents or public GitHub.

## Source of truth

The owner-approved workflow brief and compact task summary identify the bounded task. GitHub is authoritative for live PR state, exact head SHAs and CI evidence. If the task cannot proceed safely within this budget, stop with a specific BLOCKED report and one concrete next action; do not create empty branches/PRs or invent work.

All clean-room, licensing, €0, single-writer, exact-head and human-review rules remain in force.

## Autonomous PROGRESS acceptance

A provider's `PROGRESS` report is evidence only when all of these conditions hold:

- The report identifies the exact selected ledger task, and the PR body contains exactly one matching task-ID marker and one matching target-branch marker.
- A new PR has a non-empty diff. An existing PR must have a new head **and a different Git tree** from the pre-cycle head; an empty commit or metadata-only update is not progress.
- The PR is open, non-draft, unmerged, hosted in this repository and targets the selected `main` or `dev` branch.
- Required CI checks have completed successfully on the exact reported head SHA, from the GitHub Actions app.
- After CI polling, the validator fetches the PR again and rechecks its state, repository identity, base branch, task markers and exact current head. Any intervening change invalidates the report.

A validated `BLOCKED` report records a blocker and next action; it never counts as progress. These gates prevent stale heads, empty commits and unrelated PRs from satisfying the autonomous activation task.
