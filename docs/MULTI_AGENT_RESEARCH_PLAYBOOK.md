# Multi-agent research and handoff playbook

**Status:** process proposal on the documentation PR; no automatic merge or writer access is granted by this document.
**Current owner-authorized tracks:** [RE-001 / issue #226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226) — native GameCube/Wii research and implementation; [RE-002 / issue #279](https://github.com/Master-Chicken/boonta-reborn-88/issues/279) — read-only PC/N64/Dreamcast comparative source evidence.

## Goal

Use every useful participant without creating multiple agents that independently solve the same task, modify the same files, or produce conflicting claims. Parallel research is allowed only where the owner has explicitly authorized **non-overlapping evidence tracks**. RE-002 is read-only comparative PC/N64/Dreamcast research; it cannot create gameplay code or duplicate the native GameCube/Wii queue in RE-001. The owner remains the decision-maker.

## Roles for this project

| Participant | Best role | Boundary |
|---|---|---|
| **Owner (Master-Chiken)** | Set priority, choose scope, approve writer plans, decide merges, perform tests that require the local ROM or visible Dolphin/manual input | Owner approval cannot substitute for evidence or tests; no direct push/merge by an agent. |
| **ChatGPT / research coordinator** | Keep the active question coherent, trace locally available evidence, preserve source links, reconcile contradictions, update the canonical dossier/queue | Must identify exactly what was inspected. Do not claim to see a private file unless it was actually retrieved. |
| **Jules** | One tightly scoped independent task at a time; best for a small implementation or a public-source/documentation investigation with a named output | Jules runs against the connected GitHub repository in a cloud VM. It cannot see ROMs and archives that exist only in the owner's ChatGPT Library or computer. Never upload the private ROM to make it visible. Before another task, inspect Jules-created PRs for overlap. |
| **Gemini CLI (repo workflow)** | Independent, read-only challenge/review via an issue/PR comment beginning with @gemini-cli; identify unsupported inference, missing test cases, contradictions, and concrete blockers | Keep its write workflow locked. A review response is an opinion, not a passed test or authorization. Do not invoke paid fallbacks. |
| **Biddy-Pinky / human reviewer** | Independent challenge of assumptions, architecture, source provenance, risks, and acceptance evidence | Ask for a review of the exact commit and concrete evidence. A human review request is not proof that the review occurred. |
| **OpenRouter Free reviewer** | Optional independent text-only second opinion when the repository's manual reviewer is actually configured and its data terms are acceptable | Do not send ROMs, extracted proprietary data, credentials, or private files. Do not treat multiple models repeating the same inference as independent source evidence. |
| **Copilot cloud agent** | Optional only if already available and the owner explicitly chooses it for a scoped task | GitHub documents this agent as available on paid Copilot plans. It is excluded from the default €0 workflow; do not buy/enable a subscription for this project. |
| **CI and deterministic tests** | Verify the exact commit against predefined mechanical checks | CI can validate what tests assert. It cannot prove a complete playable race, an untested behavior, source-license clearance, or parity with another platform. |

## Current RE-001 and newly activated RE-002

The PC route/spline and AI consumer evidence is now mapped in the [canonical RE-001 dossier](research/RE-001-route-spline-progress.md): branch topology/history, sampled arc-length progress bake, split/rejoin normalization, player cursor/binding, cross-track offset, lap/high-water logic, and AI look-ahead/branch policy. The active task is now to finalize a versioned platform-neutral graph contract and synthetic host fixtures.

Do not launch competing implementation lanes. RE-001 owns native GameCube/Wii runtime research and gameplay changes; RE-002 owns comparative PC/N64/Dreamcast source evidence and documentation only. Use one write-capable agent at a time. Read-only research may proceed on the other track only with a distinct question, pinned sources and bounded file list.

Required fixture scope:
- Bezier and B-spline evaluation;
- a two-way split/rejoin whose branches have unequal physical lengths but share normalized progress between split and join;
- three-level branch-history persistence;
- open endpoints, closed-loop wrap and reverse cursor movement;
- malformed/missing/duplicate edge rejection;
- surface/collision binding kept separate from centerline width;
- legacy `boonta-track-v1` parsing/export/build/tests remain unchanged.

Platform boundary: Windows-PC static source is the current algorithm reference. N64's 84-byte records are separate evidence; Dreamcast and retail GameCube/Wii parity remain unproven. Do not merge PC and N64 structures into one assumed-identical binary schema.

The N64 finish-to-Results chain remains a historical runtime-unverified question. It must be recorded under RE-002 with its N64-only evidence boundary; it does not override the live native target task in #226. Step 102 remains on provenance hold and is not a prerequisite for either queue.

## Single-writer and no-duplicate-PR rules

- At most **one write-capable agent at a time**. All other agents are read-only reviewers or clearly non-overlapping researchers.
- Never ask two coding agents to implement the same behavior concurrently. Before assigning anything, inspect open issues, branches and PR diffs.
- An agent task must name the canonical issue, target branch, files it may change, files it must not change, acceptance criteria and expected output.
- A reviewer should receive the same exact diff/source pins and should be asked to challenge it, not independently rewrite it.
- No auto-merge, agent self-approval, direct push to main, automatic branch deletion, extra cloud billing, or merging merely to clear the queue.
- **Historical PR triage (2026-10-21):** the steering-deadzone and earlier rail-collision candidates described in the old note have since been integrated, closed or superseded. Do not use this dated paragraph as a live queue. Always query the live open-PR list and compare exact heads/files before assigning work.
- Research-first documentation changes do not validate the gameplay PRs. Every PR still needs exact-head checks, review, provenance checks where applicable, and the right level of manual acceptance.

## Required task request template

Canonical issue: #226 or #279, as explicitly selected by the owner-directed task.
Active research question: #226 — native GameCube/Wii research/integration; #279 — complete the platform-specific PC/N64/Dreamcast evidence matrix, read-only.
Agent role: one writer OR one read-only falsification reviewer; never parallel writers.
Allowed inputs: pinned public SW_RACER_RE and frozen Steam-PC Ghidra references, current Boonta schemas/build/tests, synthetic fixture data.
Forbidden: private ROM uploads, extracted/proprietary track coordinates or assets, third-party source copying, PC-to-console parity assumptions, route-v1 migration, RE-002 gameplay/runtime changes, overlapping writer tasks, settings/billing changes.
Required output:
1. Exact URLs/commit pins and changed-file list.
2. Versioned node/edge/curve/cursor/progress/surface-binding contract.
3. Synthetic fixtures and deterministic host tests for every required branch/endpoint/error case.
4. v1 unchanged proof: existing parser/exporter and test outputs remain stable.
5. Remaining unknowns and a narrow next test.
Stop condition: if a field or behavior is not supported by evidence, retain it as opaque/unknown rather than guessing.

## Source and privacy boundaries

- Jules, Gemini, Copilot, CI, and ChatGPT's local context do not automatically share the same files or task state. GitHub-visible evidence can be shared through the issue/dossier; private local bytes cannot.
- No ROM/disc image, executable dump, BIOS, extracted copyrighted assets, secrets, or uncertain-provenance archive content is to be uploaded to a hosted agent or public CI.
- Keep all source URLs, revisions, licensing notes, evidence tier, and next check in the [source preservation ledger](SOURCE_PRESERVATION_LEDGER_2026-10-21.md). Add new entries; do not discard old links.
- Existing data terms/quotas remain in force: €0 total budget, Gemini API-key/free-tier only, and stop if the free quota is unavailable.

## Definition of a good agent handoff

Every returned result must say:
- what the agent actually inspected (URLs, commit, files and/or logs);
- what it directly observed vs inferred;
- what it could not access;
- any test/check actually run, including exact commit;
- the single next action suggested.

A useful result may be “not established; here is the missing evidence.” Do not force every agent to produce a code change or a green check.
