# OpenRouter Free PR review — retired integration

**Status checked: 2026-10-21 — NOT ACTIVE on `main`.**

This file documents a historical experiment. Do not follow the old setup instructions below; the workflow is not present on the current default branch.

## What it was designed to do

The workflow added by historical [PR #14](https://github.com/Master-Chiken/boonta-reborn-88/pull/14) was designed as an optional, manual, read-only second opinion on a pull request targeting `main`. Its diff was capped at 30,000 bytes, it blocked several common credential patterns, and it was configured to use the `openrouter/free` route. It could publish a review comment but could not change files, push branches, or merge pull requests.

PR #14 was merged on 2026-10-14. The workflow was subsequently removed by [PR #31](https://github.com/Master-Chiken/boonta-reborn-88/pull/31), whose changes removed `.github/workflows/openrouter-free-review.yml`. The current `main` workflow directory does not contain that workflow.

## Why it is not enabled

The current [AI safety guard](../tools/check_ai_free_safety.py) explicitly rejects GitHub Actions workflows that reference `OPENROUTER_API_KEY` or `openrouter.ai` under the project's strict €0 setup. Do not reintroduce the workflow, weaken the guard, create an API key, or add a repository secret as part of ordinary project work.

This is a deliberate configuration boundary, not evidence that a review job is currently waiting or running. The present AI workflow configuration uses a manual read-only Gemini coordinator, with a separate gated workflow for any write-capable plan/execute path. A successful CI safety check does not mean an AI agent is continuously working.

## What OpenRouter is — for reference only

OpenRouter is a hosted API service that routes requests to language models from different providers using a common interface. The old integration used `openrouter/free`, which selects from available free models; it was not a direct Claude/Anthropic API integration and could not guarantee which model would answer.

The official pricing page currently lists free model access and a limit of 50 requests/day for the Free offering, but models and limits may change. Free usage is not a guarantee of stable availability or a privacy guarantee. Any request would send the included pull-request diff to OpenRouter and the selected model provider. Never send private, secret, commercial, or unclear-provenance data to an external model service.

## Current decision

- **OpenRouter PR review:** retired; no active workflow on `main`.
- **API key/secret:** not required for the current workflow set; do not create one for this project task.
- **Budget:** remain at €0; no paid fallback, billing, or payment method.
- **Future reconsideration:** only after the owner explicitly revisits the architecture and free-only policy, with a new security review. Do not alter the current guard to make the old workflow pass.

## Historical references

- [PR #14 — original workflow](https://github.com/Master-Chiken/boonta-reborn-88/pull/14)
- [PR #31 — free-only AI safety hardening and workflow removal](https://github.com/Master-Chiken/boonta-reborn-88/pull/31)
- [Current AI safety guard](../tools/check_ai_free_safety.py)
- [OpenRouter pricing](https://openrouter.ai/pricing)
- [OpenRouter free-model route](https://openrouter.ai/openrouter/free/)
- [OpenRouter privacy policy](https://openrouter.ai/privacy/)
