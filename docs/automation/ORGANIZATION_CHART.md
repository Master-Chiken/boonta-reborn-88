# Boonta Reborn — agent organization chart

**Status:** declarative policy only. This file does not create agents, grant credentials, or change the active GitHub Actions workflow.

## Command structure

```text
Human Owner / Board
└── CEO / Mission Commander
    ├── Chief of Staff / Operations Controller (deterministic)
    ├── CTO / Engineering Commander
    │   ├── Reverse Engineering & Asset Intelligence
    │   ├── Engine & Gameplay
    │   ├── Graphics & Asset Pipeline
    │   └── Platform & Build
    ├── QA / Verification (independent reporting line)
    └── Release & Integration
```

The role registry at `docs/automation/agent-roles.json` is the machine-readable authority for role IDs, manager relationships, responsibilities, and declared tool capabilities.

## Separation of responsibilities

- **Human Owner / Board:** owns the mission, the €0 ceiling, risk acceptance, governance, provider/permission changes, and all merge decisions.
- **CEO:** decomposes the mission into measurable objectives, prioritizes the queue, and delegates bounded tasks. It does not implement or certify its own changes.
- **Chief of Staff:** deterministic control logic, not another model call. Enforces the canonical ledger, reservations, one-writer lock, cooldowns, budgets, schedules, and audit reports.
- **CTO:** owns engineering architecture and integration boundaries. It cannot waive independent QA.
- **Specialists:** execute only their assigned bounded mission and approved file/tool scope.
- **QA:** reports PASS, FAIL, or BLOCKED using reproducible evidence. QA must not be the implementer for the change being accepted.
- **Release & Integration:** checks exact-head CI, provenance, release notes, and merge readiness. It cannot merge.

## Operating invariants

1. Every non-root role has exactly one manager. The reporting graph is acyclic and all roles lead to the Human Owner.
2. Cross-unit work is delegated through managers; there is no lateral command or self-promotion.
3. One active repository mission and one writer at a time. No parallel provider calls; at most one provider invocation per scheduled run.
4. GitHub Actions remains the only production writer. Model agents do not receive repository write credentials.
5. The canonical `docs/automation/task-ledger.json` remains the source of truth. Any UI/control plane is a mirror until reconciliation parity is proven.
6. The provider order remains Gemini → OpenRouter Free → Groq Free. Only explicitly verified €0/free-tier use is permitted; no paid fallback.
7. Exact task identity, exact PR head, provenance, required CI, independent QA, and human merge approval are mandatory.
8. No agent may merge/auto-merge, force-push, write protected branches, change secrets/billing/permissions/branch protection, alter provider order/cooldowns, or bypass safety gates.
9. A blocked worker stops and escalates upward with evidence; it does not invent scope, retry a quota failure, or silently select another task.
10. Role names are operational boundaries, not a promise of concurrent independent models. Under the free-tier policy, roles may be staffed serially by the existing provider workflow.

## Current deployment boundary

This is a GitHub Actions-based, Paperclip-inspired governance model. It is **not** a deployed Paperclip server or dashboard. No verified always-on, persistent, no-card/no-billing host has been established. Do not make an external control plane a prerequisite for autonomous work.
