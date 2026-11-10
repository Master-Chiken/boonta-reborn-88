# Open-source automation alternatives — Boonta Reborn

**Research date:** 2026-11-11  
**Decision:** keep GitHub Actions as the only cloud scheduler, keep Paperclip optional and local, and evaluate Goose or Aider only as optional Mac-side workers. Do not add a second scheduler or a new server stack.

This review is about the orchestration and coding-agent layer. These projects do not provide a guaranteed free inference quota. A local agent can avoid per-request API charges only when it is configured with a local model (for example Ollama); that moves the cost to the Mac's hardware, electricity and execution time, and model quality depends on the available hardware.

## Candidate comparison

| Project | What it contributes | Zero-cost fit | Decision for this repository |
|---|---|---|---|
| [Paperclip](https://github.com/paperclipai/paperclip) | Agent organization, roles, task assignment, persistent run history, approvals and coordination. It orchestrates agents; it is not itself a model or coding-agent framework. | Self-hosted locally; no hosted Paperclip account is required. It stops when the Mac sleeps or its service is stopped. | Keep as the optional human-facing control panel. Leave its routine disabled while GitHub Actions is the active scheduler. |
| [Goose](https://github.com/aaif-goose/goose) | Local desktop app, CLI and API; MCP extensions, reusable recipes and subagents. Supports local and hosted model providers, including Ollama. | Apache-2.0 project; local execution is possible with a local model. Hosted providers still have their own price/quota rules. | Best candidate for a later Mac-side worker or research/review assistant. It is not a replacement for the canonical GitHub task ledger or a cloud scheduler. Integrate only after a small local smoke test and an exclusive writer lease. |
| [Aider](https://github.com/Aider-AI/aider) | Terminal coding agent with repository mapping, Git integration, and automatic lint/test feedback. It can connect to local Ollama models. | Apache-2.0 project; local inference avoids an external model API charge but needs sufficient Mac memory/compute. | Strong alternative for a focused local code-edit/test worker. Not an orchestration/control plane; do not run it in parallel with the GitHub Actions writer. |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Low-level framework for stateful agent workflows, durable execution, checkpointing, retries/interrupt patterns and human approval. | Open-source framework, but a real deployment still needs application code, a persistence choice and a model route. | Useful only if we decide to replace parts of the custom orchestration with a bespoke runtime. Too much new code to add while the current workflow is still being stabilized. |
| [Kestra](https://github.com/kestra-io/kestra) | General workflow orchestration with YAML flows, schedules, event triggers, retries, timeouts, quotas, sequential/parallel tasks and audit history. | Apache-2.0 and self-hostable, but requires a continuously running service/worker stack. | Technically capable, but unnecessary infrastructure for one public GitHub repository with an existing schedule. Do not add now. |
| [n8n](https://github.com/n8n-io/n8n) | Visual workflow automation and AI workflow nodes with many integrations. | Self-hosted Community Edition is governed by the Sustainable Use License, not a conventional OSI open-source licence; usage conditions apply. | Exclude from this plan: it adds another service and does not solve the model quota/runtime failures. |

## Recommended architecture

1. **GitHub Actions remains the sole recurring cloud scheduler.** Keep the existing four daily UTC opportunities and the current serialized writer group. Do not enable Paperclip routines or another scheduler.
2. **The canonical task ledger remains the one source of truth.** Paperclip issues, Goose sessions and Aider sessions must carry the exact `BOONTA_TASK_ID`, target branch and acceptance criteria from the ledger. They must not create a parallel queue.
3. **One writer at a time.** A local worker must not start while a GitHub Actions writer owns the task. A local worker must use a unique branch and PR, and release/record its lease on success, failure or interruption. Never let Paperclip and GitHub Actions write simultaneously.
4. **Use local inference only as an optional Mac-side route.** If Ollama is later tested, first check available RAM, storage and model quality on the actual Mac. Do not download a large model or run a long model pull without checking available disk and memory. Local inference is not guaranteed to match hosted-model quality.
5. **Keep deterministic checks outside the model.** YAML validation, Python compilation, ledger validation, exact-task checks, provenance checks, diff checks and test suites remain ordinary scripts/CI. The model should not be asked to certify its own output.
6. **Keep every model attempt bounded.** One provider invocation per scheduled run; no same-run cascade. If a provider fails or its quota is uncertain, preserve the cooldown and wait for the next eligible cycle. A successful readiness check is not a model invocation.
7. **Require evidence at the end.** A task is progress only when the exact task PR exists, its body has the matching task marker, all required checks pass on the exact current head SHA, and the canonical ledger is reconciled. An open PR remains `in_review`, not completed.

## What the current failure evidence says

The latest maintainer diagnosis in issue [#226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226) records three different failure modes:

- **Gemini:** the CLI request failed with `TypeError: fetch failed sending request` after readiness and GitHub App checks passed. This points to a transport/network failure, not a missing-key diagnosis. Keep same-day cooldowns; do not hammer the endpoint with immediate retries.
- **OpenRouter Free:** inference completed, but the agent exceeded its old tool-step budget and did not produce the required exact task report. The mainline direct-delivery path now preloads task context and sharply limits the normal branch/patch/PR sequence.
- **Groq Free:** the agent returned malformed JSON tool-call arguments. The mainline profile was reduced to a short context/output budget and a lower temperature. This is a mitigation, not a guarantee.

The open PR [#384](https://github.com/Master-Chiken/boonta-reborn-88/pull/384) adds a fresh, GET-only task revalidation after the shared writer slot is acquired, with 15 offline regression scenarios. It is still a PR and must not be described as merged until GitHub says so.

## Immediate plan

- Keep the existing GitHub Actions schedule and its €0/provider cooldown gates.
- Review and merge PRs only through the repository's required independent review and branch protections.
- Observe the first post-reset scheduled cycle; record whether a model call really happened, whether its report passed validation, and whether a same-task PR passed exact-head checks.
- If hosted Free-tier routes continue to fail, perform a small owner-local Goose **or** Aider + Ollama feasibility test on the existing Mac. Do not install both, do not add a self-hosted runner, and do not change the cloud workflow until that test proves a useful local model can edit/test the repo inside the one-writer policy.

## References

- Paperclip overview and local quickstart: https://github.com/paperclipai/paperclip
- Goose project and supported local providers: https://github.com/aaif-goose/goose
- Goose subagents and recipes: https://github.com/aaif-goose/goose/tree/main/documentation/docs/guides
- Aider with local Ollama models: https://github.com/Aider-AI/aider/blob/main/aider/website/docs/llms/ollama.md
- Aider Git integration: https://github.com/Aider-AI/aider/blob/main/aider/website/docs/git.md
- LangGraph durable execution and checkpointing: https://github.com/langchain-ai/langgraph
- Kestra orchestration capabilities: https://github.com/kestra-io/kestra
- n8n licence FAQ: https://support.n8n.io/article/can-i-use-your-license-for-my-use-case


## Additional candidates checked — 2026-11-11

The first comparison focused on Paperclip, Goose and Aider. These additional tools solve different parts of the failure chain; they should not all be installed.

| Project | Newly verified capability | What it could solve | Decision |
|---|---|---|---|
| [OpenCode SDK](https://docs.opencode.ai/docs/sdk/) | Typed JavaScript/TypeScript client for the OpenCode server. Its API exposes sessions, child sessions, status, diffs, abort and permission operations. OpenCode also supports primary agents, subagents and per-agent tool permissions. | Better programmatic control and observability around the OpenCode runtime already used by the OpenRouter/Groq path. A controller could inspect the session and capture diffs rather than depending on free-form final prose. | **Best low-disruption technical spike.** Do not replace the existing CLI workflow until a small fixture proves the SDK provides reliable completion and failure semantics. It does not fix a model that emits malformed tool-call arguments and does not provide inference quota. |
| [OpenHands Software Agent SDK](https://github.com/OpenHands/software-agent-sdk) | Python, TypeScript and REST APIs for coding agents; supports local workspaces or ephemeral Docker/Kubernetes workspaces and publishes GitHub workflow examples. | Could replace part of the custom agent execution layer with a purpose-built coding-agent SDK and isolated workspaces. | Keep as a comparison candidate, not a new dependency. It still needs a model/provider and introduces another runtime and sandbox to maintain. |
| [Dagger](https://github.com/dagger/dagger) | Sandboxed, incremental execution with content-based caching, typed artifacts and detailed traces; can run locally or in CI when a container runtime is available. | More actionable build/test feedback and less repeated test work after agent edits. | Useful as a future **verification layer**, not an agent or scheduler. First compare its value against the existing Make/Python/GitHub Actions checks; do not add Docker/Dagger just for decoration. |
| [Restate](https://github.com/restatedev/restate) / [Temporal](https://docs.temporal.io/) | Durable execution, persisted workflow state, timers and targeted retry of failed activities. | Long-running orchestration that resumes after worker or process failure without replaying completed steps. | Technically relevant but operationally disproportionate here: it adds a service/worker deployment while GitHub Actions already provides scheduling, run history and serialized jobs. Revisit only if the repository outgrows Actions. |
| [Ollama structured outputs](https://github.com/ollama/ollama/blob/main/docs/api.md) | Local inference API supports JSON-schema-constrained structured responses. | Can make a locally generated final report conform to a schema, instead of relying on prose. | Useful in a local model experiment. **Do not confuse structured final output with valid native tool calls**; tool-call compatibility still needs its own tests. |

## Newly identified repository-level blockers

A fresh read of `docs/automation/task-ledger.json` on `main` (updated 2026-11-10) found 11 total task records:

- 9 `completed`
- 2 `blocked`
- 0 `queued`
- 0 `active`
- 0 `in_review`

The two blocked tasks are `AUTOMATION-LEDGER-ACTIVATION` and `N64-COMPWOLF-PUPP-T2-PARSE-PROBE`. Consequently, **a successful provider invocation alone will not create a continuing game-development queue**. After the activation task is closed, the scheduler has no pre-approved queued task to select unless the canonical ledger is deliberately replenished.

Required queue-liveness improvement:

1. Keep task selection deterministic and fail closed when no task is eligible; never ask a model to invent a task ID or silently activate a blocked task.
2. Prepare a small, ranked backlog from already-approved project roadmap/research evidence, with a task ID, one bounded question, platform scope, acceptance criteria, test plan and exact source links for each candidate.
3. Have the repository owner approve those candidates before adding them as `queued` records to the canonical ledger. Do not mark a candidate active merely to make a provider run.
4. Add a queue-health test that fails or emits a clear `EMPTY_QUEUE` state when there are no queued/active tasks and the activation bootstrap is no longer eligible.
5. After each merged PR, reconcile the exact task and automatically promote at most one already-approved queued task. Completion still requires a merged PR and exact-head evidence.

## Cross-runtime locking — a non-negotiable gap

The Actions concurrency group serializes GitHub Actions jobs; it is not a distributed lock shared with a local Paperclip, Goose, Aider or OpenCode process on the Mac. A local agent cannot assume that the cloud writer is idle just because its own local process is the only local agent.

Until a real cross-runtime lease protocol is implemented and tested:

- Keep Paperclip routines disabled.
- Keep any local coding agent read-only, or let it prepare a local patch without pushing it.
- Let GitHub Actions remain the only process that writes branches and opens PRs.
- Do not register the Mac as a persistent self-hosted runner for this public repository. GitHub explicitly warns that self-hosted runners can be compromised by untrusted pull-request code.
- A future lease must have atomic acquisition, a task ID, base SHA, owner/run identity, expiry/heartbeat, stale-lease recovery and compare-and-swap release tests. A plain issue comment or local file lock is not an atomic repository-wide lease.

## Failure-specific improvements (not just another agent framework)

| Observed failure | Practical fix | Guardrail |
|---|---|---|
| Gemini `TypeError: fetch failed sending request` | Separate provider reachability/credential preflight from inference; capture sanitized transport phase, HTTP status and request ID where available. | Never blindly replay an inference POST after an ambiguous network failure: the provider may have received it and charged/consumed free quota. Keep the provider cooldown until the next eligible UTC day. |
| OpenRouter agent exhausted its tool-step budget without a valid task report | Keep direct task context preloaded and deterministic branch/patch/PR operations bounded. Capture branch, commit, PR number and exact head SHA from tool/API results, then assemble the machine report from those facts. | Do not let the model self-certify progress with prose. |
| Groq/OpenCode tool-call arguments were malformed | Qualify each provider/model combination with a tiny synthetic tool-call contract test before allowing it into the autonomous allowlist. Record model ID and result; disable only the failing model route until requalified. | A model being labelled Free does not prove reliable function calling. No fallback to a paid model. |
| Model invocation succeeds but there is no next task | Add the owner-approved queue-seeding process above and an explicit `EMPTY_QUEUE` state. | Never invent backlog or turn blocked owner-only work into active work. |
| Local and cloud agents could write at the same time | Keep local agents read-only until a shared lease is proven; retain GitHub Actions as sole writer. | A GitHub Actions concurrency key does not lock an external Mac process. |

## Updated recommendation

1. **Keep the current architecture for now:** GitHub Actions is the single cloud scheduler; GitHub task ledger is the source of truth; Paperclip remains an optional local dashboard.
2. **Do not install every candidate.** The next worthwhile engineering spike is OpenCode SDK session/result capture because OpenCode is already in the provider path. Build it in a throwaway fixture or isolated branch first.
3. **Do not add a self-hosted runner.** It adds public-repository security exposure and is unnecessary for the current workflow.
4. **Do not add Temporal/Restate/Kestra yet.** The observed problems are provider transport/tool-call reliability and an empty task queue, not a lack of a general-purpose scheduler.
5. **Prepare approved game tasks before claiming ongoing autonomy.** A stable scheduler with no queued work is healthy but idle; it is not a continuously productive game-development system.

## Additional official references

- OpenCode agents and subagent permissions: https://opencode.ai/docs/agents/
- OpenCode SDK and typed session APIs: https://docs.opencode.ai/docs/sdk/
- OpenHands Software Agent SDK and GitHub workflow examples: https://github.com/OpenHands/software-agent-sdk
- Dagger execution, cache and tracing: https://docs.dagger.io/getting-started/introduction/
- Goose Development Kit persisted-state resume: https://goose-docs.ai/docs/gdk/
- Ollama structured outputs and API: https://github.com/ollama/ollama/blob/main/docs/api.md
- GitHub guidance on self-hosted-runner security: https://docs.github.com/en/actions/reference/security/secure-use
- Temporal retry policies: https://docs.temporal.io/encyclopedia/retry-policies
- Restate durable execution: https://github.com/restatedev/restate


### Local inference alternative: llama.cpp server

[llama.cpp](https://github.com/ggml-org/llama.cpp) is worth one controlled comparison with Ollama because its server exposes OpenAI-compatible endpoints, schema-constrained JSON responses and function/tool calling. OpenCode can discover local Ollama/LM Studio/vLLM models and can be configured for other OpenAI-compatible servers.

This is a **candidate for a local Mac experiment only**, not a new GitHub Actions dependency. It may improve strict output formatting for a suitable model, but neither the server nor constrained JSON makes a weak coding model reliable. Tool calling depends on the model/chat template and must pass the same synthetic contract test used for hosted providers. Do not download a model until the Mac's RAM, free disk and available acceleration have been checked.

Official references:
- llama.cpp HTTP server: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- OpenCode local model support: https://opencode.ai/docs/models/
- Ollama tool calling: https://github.com/ollama/ollama/blob/main/docs/capabilities/tool-calling.mdx


## Free-model routing: a more targeted OpenRouter improvement

The current mainline `.github/workflows/openrouter-plan-execute.yml` configures the generic `openrouter/free` route. That preserves a zero-price route, but the selected model can change as OpenRouter's free pool changes. For a workflow whose success depends on native function/tool calls, a **pinned model with a tested tool-call contract** is more reproducible.

OpenRouter's live free catalogue now lists several newer candidates:

| Candidate | Published capability | Important caveat | Current decision |
|---|---|---|---|
| `thinkingmachines/inkling-2-small:free` | Released 2026-11-09; described as trained on long-horizon coding/agent workflows; supports tool calls. | Its model page says it does not support `response_format`, and currently warns it is unavailable through EU in-region routing. | High-priority canary candidate only if the account's routing policy allows it; structured report still needs local validation. |
| `xingchen-agi/xing4.0-29b-a4b:free` | Described as tuned for complex engineering, tool calls and multi-step planning; supports tool calls and JSON-schema structured output. | Its model page currently warns it is unavailable through EU in-region routing. Provider availability and quota remain variable. | Strong capability candidate, but do not select until the routing-region check passes. |
| `google/gemma-4-26b-a4b-it:free` | Native function calling and structured output support; free model variant. | Its model page currently warns it is unavailable through EU in-region routing. | Keep as a backup canary candidate subject to the same regional check. |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | Supports `tools` and `tool_choice`; designed for reasoning/orchestration. | Large model; free rate limits and observed availability are not equivalent to reliable coding-agent success. | Do not choose based on headline context size or agentic marketing alone. |

The OpenRouter Free endpoints are rate-limited. Its current documentation states 20 requests/minute and 50 requests/day for `:free` model variants without buying credits; failed attempts also count toward the free request cap. The existing workflow's quota preflight should remain authoritative and no quota purchase or paid route is allowed.

### Recommended model-qualification sequence

1. Read the current model catalogue and model endpoint metadata before each qualification; do not assume yesterday's free model or provider is still available.
2. Check region/routing compatibility. The model pages above currently show an EU in-region routing warning; if the account enforces EU in-region routing, reject those candidates without sending an inference request.
3. Run one owner-authorized synthetic canary against the exact OpenCode MCP tool schemas used by Boonta. The canary must call one harmless mock/read-only tool, return correctly typed arguments, preserve a tool result and emit the exact machine-readable completion envelope.
4. Validate function-call parsing, argument schema, model response termination, latency and final report shape. Record the exact model slug, provider, date and pass/fail outcome.
5. Pin only a passing `:free` model in the OpenRouter workflow. Keep the generic `openrouter/free` route disabled as an autonomous writing route if it cannot guarantee a tested tool-call profile.
6. Requalify after model/provider changes. On a failed canary, keep the existing cooldown and skip that model; never cascade to a paid route or retry an ambiguous inference POST.

This is a model-adapter improvement, not a replacement for the queue-liveness and cross-runtime lease work above.

## A provider option that is no longer available

Do not build a new fallback around **GitHub Models**. GitHub announced that the service was fully retired on **2026-07-30**, including its playground, catalogue and inference API. It is not a current free model endpoint for this project.


## Highest-value next experiment: structured patch proposal + deterministic GitHub delivery

The current OpenRouter path asks OpenCode to coordinate reasoning, native GitHub MCP tool calls, and the final report in one short run. The observed failure modes include malformed native tool-call arguments (Groq) and a missing machine-readable completion report after the model consumed its step budget (OpenRouter).

A lower-coupling alternative is to make the model return **one typed patch proposal** and let ordinary code own every side effect:

1. The preflight supplies one exact task ID, base branch/SHA, acceptance criteria and a bounded source context. If it cannot provide enough source context, stop as BLOCKED; do not make the model browse the repository.
2. The model returns one JSON object matching a strict schema, for example: `task_id`, `base_sha`, `summary`, `unified_diff`, `tests_to_run` and `limitations`. All fields are required; unknown properties are rejected.
3. A deterministic validator checks the exact task/base identity, JSON schema, diff syntax, allowed paths, protected-path policy, patch size and expected base blob/HEAD SHA. It rejects path traversal, symlinks, binary changes, secrets, generated artifacts and files outside the task allowlist.
4. Apply the diff only in an isolated temporary checkout with `git apply --check`; then run the repository's existing targeted tests, safety/provenance checks and diff review.
5. Only after all local checks pass does a deterministic GitHub writer create one unique task branch, push the already validated patch, open a PR with the exact task marker and capture the actual PR number/head SHA from GitHub.
6. A separate live validator checks the PR, exact head/base, changed files and required CI. It—not the model—produces the final PROGRESS/BLOCKED report.

This removes branch creation, file-write and PR-creation MCP tool calls from the model's reasoning budget. It also makes malformed model tool-call JSON a proposal-validation failure rather than a partially completed repository operation. It does **not** eliminate model mistakes: an invalid or unsafe diff is rejected, never repaired by blindly retrying an inference request.

### Structured-output contract

- Prefer a strict JSON Schema `response_format` only when the selected model **and exact provider endpoint** declare structured-output support.
- For OpenRouter, set `provider.require_parameters: true` so the router rejects an endpoint that cannot honor the requested parameters. Read the selected endpoint metadata and fail closed when support is absent.
- Keep the schema intentionally small: one patch, bounded number of files/bytes, no arbitrary shell commands, no model-supplied GitHub API operations.
- Check both `finish_reason` and JSON Schema validation. Reject output truncated by `max_tokens`, a refusal, missing diff, unexpected file paths or mismatched task/base SHA.
- If using OpenCode SDK v2 `session.prompt({ format: { type: "json_schema", schema, retryCount: 0 } })`, explicitly set `retryCount: 0` for a strict one-provider-request budget. The SDK's documented default is two structured-output retries; leaving that default could use more than one request. Any retry policy must be explicit and budgeted.
- Run a synthetic no-write canary before introducing this path. The canary should verify schema conformance, patch rejection, and deterministic writer behavior using a temporary fixture repo; it must not create a real branch or call a provider during ordinary CI.

This is a **small isolated prototype**, not an immediate replacement of the current provider route. The current main workflows remain unchanged until the prototype proves: one request, valid schema, rejection of hostile/malformed patches, successful synthetic test execution, and an exact-head mock PR delivery.

Official references:
- OpenRouter's structured-output guide (published 2026-11-10) explains strict JSON Schema, endpoint-specific support, `require_parameters: true`, tool-schema forcing, response healing limitations and local validation: https://openrouter.ai/blog/tutorials/structured-output-llm/
- OpenCode SDK v2 documents `session.prompt` JSON Schema output, `StructuredOutputError` and default `retryCount: 2`: https://docs.opencode.ai/docs/sdk/
