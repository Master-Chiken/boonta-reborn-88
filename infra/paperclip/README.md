# Paperclip — optional free local control panel for Boonta Reborn

**No paid hosting, no VPS, no bank card, no Paperclip Cloud account.**

Paperclip is an optional local control panel for organizing coding agents. It does not replace the GitHub repository, GitHub Actions CI, branch protection, or the canonical task ledger.

## The free architecture

- **Automatic cloud work:** the existing GitHub Actions workflows remain the only scheduled writers. This repository is public, so standard GitHub-hosted Actions runners are free under GitHub's published policy.
- **Paperclip:** runs locally on the Mac you already own. It uses an embedded database; no separate database service, cloud server, subscription, or payment card is required.
- **AI:** use only an already-authorized Gemini CLI login with its confirmed Free-tier allowance. Do not add a paid API key, enable billing, or configure paid fallbacks. If the free quota is unavailable, the agent must stop and report BLOCKED.
- **GitHub:** use the existing local `gh` login for a first local smoke test, or a fine-grained token scoped only to `Master-Chiken/boonta-reborn-88` if a separate credential becomes necessary. Never paste credentials into the repository or agent prompts.

Paperclip brings the control-plane features the current workflow lacks: agent roles, persistent task threads, session continuity, atomic task checkout, delegation, run history and a shared dashboard. It does not supply a model, free inference quota or 24/7 compute.

## The availability limit — no hidden promise

Paperclip runs only while the Mac is awake and its local service is running. When the Mac is shut down or asleep, Paperclip agents and its routines stop. This is the honest zero-cost tradeoff.

GitHub Actions continues to run in GitHub's cloud on the public repository without the Mac. Keep its existing four-times-daily schedule active. Do **not** enable the Paperclip routine as a second scheduler.

## 1. Install Paperclip locally

Follow [LOCAL-QUICKSTART.md](LOCAL-QUICKSTART.md). The official local installer requires Node.js 24.11 or newer and starts Paperclip with an embedded PostgreSQL database. It does not require Docker, a VPS, an external database, a Paperclip account or a bank card.

No paid hosting is configured by this PR. The optional Compose/VPS deployment has deliberately been removed to keep the setup simple and free.

## 2. Prepare the Boonta company

After Paperclip opens at `http://localhost:3100`, create:
- Company: **Boonta Reborn 88**
- Project: **GameCube/Wii clean-room game**

Attach `BOONTA-AGENT-SKILL.md` as a shared company skill.

Start with three roles:
- **Coordinator (read-only):** reads the canonical ledger and live GitHub state, selects one eligible task, records blockers and assigns it.
- **Game engineer (single writer):** one active task, one branch, relevant tests and one PR; no merge permission.
- **QA/provenance reviewer (read-only):** checks exact-head CI, task identity, licences, platform evidence and clean-room boundaries.

Set the engineer's maximum concurrent runs to **1**. Mirror the exact task ID from the GitHub ledger. Do not create a second, conflicting queue.

## 3. Connect the existing free tools

- Use the Gemini CLI adapter only after its local environment test confirms the already-authorized Free-tier login and usable quota. Do not add API billing or paid fallbacks.
- For local Git operations, Paperclip can use a GitHub CLI login already authenticated on the same Mac. Run `gh auth status` to inspect the current local state. Do not create a broad token just to get past a failure.
- If Paperclip asks for a repository token, use a fine-grained PAT limited to this one repository and only the specific permissions required for the planned action. This does not cost money, but it is an additional credential, so do not create one until needed.

The managed Paperclip GitHub App connection is only offered to instances enrolled with Paperclip Cloud. We are not using that route or paying for Cloud enrollment.

## 4. Keep Paperclip scheduling disabled

The current GitHub Actions writer schedule is `17 0,6,12,18 * * *` UTC. `routine.example.json` mirrors those times but has `enabled: false`.

Do not enable both as autonomous writers. First verify one manually started local agent run, one fresh task PR with the exact `BOONTA_TASK_ID` marker, all required GitHub checks on the exact PR head, ledger reconciliation and a successful recovery/resume test.

Because the Mac is not guaranteed to stay awake, retain GitHub Actions as the only recurring cloud scheduler. The Paperclip routine is only a future optional local convenience; it is not required for the automatic cloud loop.

## 5. Zero-cost and authority rules

- Use only a provider login already confirmed as Free-tier. Never enable billing, buy credits, upgrade plans or use paid fallback models.
- Paperclip's budgets are monitoring and pause controls, not proof of €0 inference. The provider login and model route must themselves be confirmed free.
- One active coding task, one writing agent and one provider call per heartbeat.
- Agents may research, edit a task branch, run approved tests and open PRs. They may not merge, modify repository secrets, billing, branch protection, GitHub App settings or workflow permissions.
- An open PR remains `in_review`, never `completed`. Completion requires a merged PR and a reconciled canonical ledger.
- Never upload ROMs, disc images, proprietary executables, extracted commercial assets or private analysis databases to GitHub, CI or hosted AI tools.

## 6. Rollback and fallback

If Paperclip fails or is unavailable, stop using it and keep the existing GitHub Actions cloud schedule. Paperclip's local data lives under `~/.paperclip/`; back it up before reinstalling or changing versions. No GitHub automation or game source files depend on a running Paperclip instance.

## 7. Other free and open-source options

The expanded comparison in [ALTERNATIVES-AND-RECOMMENDATION.md](ALTERNATIVES-AND-RECOMMENDATION.md) covers Goose/GDK, Aider, OpenCode SDK, OpenHands SDK, Ollama, llama.cpp, Dagger, LangGraph, Kestra, Restate/Temporal and n8n.

The highest-value low-disruption experiment is a **structured patch proposal with deterministic GitHub delivery**: the model returns one schema-validated patch, ordinary code rejects unsafe/stale diffs, runs tests, and only then creates a branch and PR. This directly reduces dependence on fragile multi-step MCP tool calls. OpenCode SDK session/result capture is the adjacent diagnostic option, because OpenCode is already used in the provider path. Goose GDK remains a candidate for a local Mac-side agent that can resume persisted state; Aider is a focused local coding tool; Dagger is a possible deterministic build/test layer. None supplies a guaranteed free model quota.

**Important current blockers:** the canonical task ledger currently has 9 completed tasks, 2 blocked tasks and no queued/active task. Also, GitHub Actions concurrency does not lock a separate local Mac process. Therefore keep the Paperclip routine disabled and local agents read-only or local-patch-only until (1) the owner approves a replenished task backlog and (2) a tested shared lease serializes local and cloud writers. Do not register this public repository's Mac as a persistent self-hosted runner.

## References

- Paperclip upstream: https://github.com/paperclipai/paperclip
- Paperclip local installation: https://docs.paperclip.ing/guides/getting-started/installation/
- Gemini CLI adapter: https://docs.paperclip.ing/reference/adapters/gemini-cli/
- GitHub connector: https://docs.paperclip.ing/connectors/github-setup/
- GitHub Actions billing: https://docs.github.com/en/actions/concepts/billing-and-usage
