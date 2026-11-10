# Paperclip control plane for Boonta Reborn

Optional self-hosted Paperclip deployment for agent coordination. It does not replace the game repository, GitHub Actions CI, branch protection or the canonical task ledger.

## What it adds — and what it does not

The existing GitHub Actions system already provides cloud execution, provider preflights, free-tier gates, task selection, exact-head PR validation and CI. The gap is the agent-control layer: durable roles, persistent work threads, heartbeat/session continuity, atomic task checkout, delegation, run history and a central dashboard.

Paperclip is a control plane, not a model or agent intelligence provider. It can orchestrate Gemini CLI and OpenCode agents, but does not provide free inference, quota or game content.

## Deployment status and cost

This folder is configuration only. Paperclip is **not installed or running**, no host is provisioned, and no provider/GitHub credentials are stored here.

Continuous availability requires an always-on host. The current official VPS guide quotes roughly US$5–10/month for a small VPS; model usage and any external services may be additional. Running it on the Mac can avoid a VPS fee, but Paperclip stops when the Mac is off. The existing GitHub Actions loop remains cloud-hosted and does not need the Mac running.

The Compose stack pins the official image to upstream commit `353945c86daedc13de0f23bdf8baf1e35f718e71`, uses PostgreSQL 17 and persistent volumes, requires authentication, sets private exposure, disables telemetry and binds the UI to localhost only. Put a private HTTPS reverse proxy such as Tailscale Serve in front of port 3100. Do not expose port 3100 or PostgreSQL directly to the public internet.

## Optional €0 compute experiment

See [ORACLE-ALWAYS-FREE.md](ORACLE-ALWAYS-FREE.md) for Oracle's Always Free A1 allowance, account-verification requirement, limited regional capacity and seven-day idle-instance reclamation. This is a possible low-cost experiment, **not** a guaranteed always-on host. Never upgrade to Pay As You Go to solve a capacity shortage; keep the existing GitHub Actions schedule as the reliable cloud fallback.

## 1. Prepare the host and secrets

On an always-on Linux host with Docker Compose, from this directory:

```bash
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
```

Generate **four independent** values and paste one into each of `PAPERCLIP_DB_PASSWORD`, `BETTER_AUTH_SECRET`, `PAPERCLIP_TOOL_ACTION_SIGNING_SECRET` and `PAPERCLIP_AGENT_JWT_SECRET`. Set `PAPERCLIP_PUBLIC_URL` to the exact private HTTPS URL used to access Paperclip.

Keep `.env` private. Never put API keys or passwords in GitHub, this repository, issues or agent prompts. Keep the Paperclip image pinned to the full-SHA tag in `.env.example`; update it only through a reviewed dependency update.

## 2. Start and verify

```bash
docker compose --env-file .env -f compose.yml config --quiet
docker compose --env-file .env -f compose.yml up -d
docker compose --env-file .env -f compose.yml ps
docker compose --env-file .env -f compose.yml logs -f paperclip
```

Open the private HTTPS URL and complete authenticated onboarding. Create a company **Boonta Reborn 88** and a project **GameCube/Wii clean-room game**.

Data lives in the `paperclip-postgres` and `paperclip-data` Docker volumes. Back up both: a database dump alone does not preserve uploads, secret storage and agent workspace data. Encrypt backups and test restore before relying on the service.

## 3. Connect GitHub with least privilege

For a self-hosted instance, Paperclip's managed GitHub App path is generally available only to instances enrolled with Paperclip Cloud. Use a fine-grained PAT scoped to **only** `Master-Chiken/boonta-reborn-88`, with an expiry date.

Start with Metadata read, Contents read/write (for branch commits), Issues read/write, Pull requests read/write, and Checks read. Do not grant Actions write, workflow editing, administration, secrets or repository-wide access. Restrict the connection to the Boonta agent(s).

Important: Paperclip documents that shell `git` and `gh` operations use the connected GitHub identity and are not bounded by the connector action switches. The real security boundary is the token's repository scope plus GitHub branch protection. Keep `main` protected, require PRs, independent human review and required CI checks, and do not permit agent merges.

## 4. Add a Free-tier provider

Start with one agent and one owner-confirmed Free-tier provider. Paperclip supports `gemini_local` and `opencode_local`. Store credentials through Paperclip's secret/connection UI, not Compose or the repository. Do not add paid fallbacks.

Paperclip's cost dashboard and budgets are useful monitoring and pause controls, but they are not a guarantee of €0: usage can be reported late or be unpriced. The €0 boundary must come from a confirmed Free-tier credential/model route and refusing execution whenever the free-tier preflight is uncertain.

## 5. Create the initial team

Attach `BOONTA-AGENT-SKILL.md` as a shared company skill. Start with:
- **Coordinator (read-only):** reads the ledger and live GitHub state, selects one eligible task, records blockers and assigns it.
- **Game engineer (single writer):** one active task, unique branch, synthetic tests and one PR; no merge permission.
- **QA/provenance reviewer (read-only):** checks exact-head CI, task identity, licences, platform evidence and clean-room rules.

Set the engineer's maximum concurrent runs to **1**. Do not start parallel coding agents until a complete one-writer cycle has passed. Mirror the exact ledger `task_id` into Paperclip; do not create a second, conflicting queue.

## 6. Keep the routine disabled until cutover

The current GitHub Actions writer schedule is `17 0,6,12,18 * * *` UTC. `routine.example.json` mirrors those times but has `enabled: false`.

Do not enable both as autonomous writers. First pass a read-only GitHub test, one manually started owner-approved Free-tier agent run, one fresh task PR with the exact `BOONTA_TASK_ID` marker, exact-head GitHub Actions checks, ledger reconciliation and a successful recovery/resume test.

Only then make a separate reviewed cutover: disable the GitHub Actions writer schedule and enable the Paperclip routine with `skip_if_active` and `skip_missed`. Keep GitHub build/test workflows, exact-head validation, branch rules and human review.

## 7. Backups, updates and rollback

- Back up both Compose volumes before updating.
- Update only to a reviewed immutable `sha-<commit>` image tag; never use `latest`.
- Inspect release notes and migration requirements before changing the pin.
- On failure, restore the previous image pin with matching database/data backups.
- If Paperclip is unavailable, retain GitHub Actions as the temporary execution path. Never enable two schedulers simultaneously.

## References

- Upstream: https://github.com/paperclipai/paperclip
- Docker guide: https://github.com/paperclipai/paperclip/blob/master/doc/DOCKER.md
- VPS guide: https://docs.paperclip.ing/how-to/deploy-to-vps-or-fly/
- GitHub connector: https://docs.paperclip.ing/connectors/github-setup/
- Gemini CLI adapter: https://docs.paperclip.ing/reference/adapters/gemini-cli/
- OpenCode adapter: https://docs.paperclip.ing/reference/adapters/opencode/
- Routines: https://docs.paperclip.ing/guides/projects-workflow/routines/
