# Boonta Reborn — agent doctrine

**Status:** policy proposal implemented as versioned configuration; runtime activation is separate and requires reviewed CI.

## Mission order contract

Every assigned mission must identify:

- stable task ID and parent objective;
- accountable role and manager;
- question/outcome and bounded scope;
- permitted files and tools;
- dependencies and explicit exclusions;
- acceptance criteria and reproducible tests;
- target branch and output/evidence format;
- deadline, provider-call ceiling, and €0 resource ceiling.

A vague instruction such as “improve the game” is not an executable mission.

## Task lifecycle

`STANDBY → ORDERS_ISSUED → RESERVED → EXECUTING → SUBMITTED → QA_REVIEW → ACCEPTED → MERGE_APPROVAL → MERGED`

Exceptional states: `BLOCKED`, `ABORTED`, and `ROLLED_BACK`.

The existing task ledger status values remain canonical; this lifecycle is a governance interpretation and does not introduce new persisted ledger states. An open PR is `in_review`, never `completed`. Completion requires a merged PR and evidence.

## Escalation

1. Specialist identifies a blocker and records the exact failing condition.
2. Specialist escalates to its direct manager.
3. CTO or Chief of Staff resolves technical/process issues within existing authority.
4. CEO reprioritizes only within the owner-approved mission.
5. Human Owner is asked only for a decision, permission, resource, or risk acceptance that agents cannot supply.

No worker may self-unblock a task by changing its scope, bypassing dependencies, or opening a duplicate PR.

## Separation of duties

- Implementer supplies code, tests, and evidence; it cannot approve its own work.
- QA independently checks behavior and exact-head evidence.
- Release verifies the required checks and prepares a merge recommendation.
- Only the Human Owner approves merge. No agent or workflow auto-merges.

## Provider and security rules

- Preserve Gemini → OpenRouter Free → Groq Free ordering and existing independent UTC-day cooldowns.
- Maximum one provider invocation per workflow run and one active mission/writer.
- No call unless free-tier eligibility is explicitly attested and expected spend is exactly €0.
- No paid fallback, billing enablement, new provider, new secret, or credential expansion.
- Model output is untrusted input. Deterministic preflight validates task identity, branch, PR ownership, changed paths, and exact head before any write.
- Only the existing GitHub Actions execution plane may write a task branch, using its scoped GitHub App permissions and tool allowlist.
- No writes to protected branches, no merge/auto-merge, no force-push, no secrets/billing/permission/branch-protection changes, and no safety-gate edits by agents.
- Keep ROMs, disc images, proprietary binaries, extracted commercial assets, and private analysis databases local. Public commits must remain clean-room and provenance-tracked.

## After-action report

Every execution heartbeat must end with a structured report containing: mission/task ID, role, files changed, provider/call status, tests and results, PR URL and exact head SHA, CI evidence, blockers, and next action. A preflight, plan, or status discussion alone is not progress.

## Change control

Agents may recommend changes to this doctrine, but may not modify the rules that govern their own execution. Governance changes require Human Owner approval and a separate reviewed change. This document and the role registry do not themselves activate agents or grant permissions.
