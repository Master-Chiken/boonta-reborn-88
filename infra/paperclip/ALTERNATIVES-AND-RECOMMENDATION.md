# Open-source automation alternatives — Boonta Reborn

**Research date:** 2026-11-10  
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
