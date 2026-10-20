# Multi-agent research and handoff playbook

**Status:** process proposal on the documentation PR; no automatic merge or writer access is granted by this document.
**Current active question:** [Issue #226 — route/spline and lap progression evidence](https://github.com/Master-Chiken/boonta-reborn-88/issues/226).

## Goal

Use every useful participant without creating multiple agents that independently solve the same task, modify the same files, or produce conflicting claims. Parallel work is allowed only as **separate evidence lanes under the one active research question**. The owner remains the decision-maker.

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

## Current RE-001: non-overlapping lanes

The task is still one question: trace route progress to the finish/lap state, keeping N64 evidence separate from PC/Dreamcast/GameCube/Wii evidence.

1. **Local binary lane — owner + local research session.** Continue N64 ROM/disassembly work locally. Keep the ROM and all extracted bytes/assets local. Record addresses, instruction/call relationships, confidence, and unresolved semantics; publish only safe prose and public URLs.
2. **Public-source lane — Jules, only when the owner assigns it.** Independently check the pinned public N64 project [sp00nznet/racer at 11f6f70469f995304422f2209a47e9c2df5ff6d0](https://github.com/sp00nznet/racer/tree/11f6f70469f995304422f2209a47e9c2df5ff6d0), its symbols and tools, and the historical [TheForce.Net N64 code listing](https://www.theforce.net/videogames/codes/n64/racer.asp). Answer only: does the public material directly map RAM addresses 0x8011900A / 0x80119092 to a field or writer, or is the match only suggestive? Return evidence links and unknowns. Do not touch gameplay code, modify the canonical RE-001 dossier, or upload local ROM data.
3. **Falsification lane — Gemini CLI, read-only.** Review only the public issue/dossier and cited public sources. Try to disprove the proposed mapping between the lap option, participant event counter, finish state, and HUD. Distinguish facts, inferences and unknowns. Do not write files or approve merging.
4. **Integration lane — coordinator.** Compare each output against local-source evidence, resolve contradictions, and fold only supported conclusions into the canonical RE-001 dossier. A new agent report is not automatically a new truth.
5. **Human gate — owner and requested reviewer.** Before implementation, confirm whether the evidence actually answers the question and decide the next test. Runtime memory watch or visual tests that require the private ROM/emulator must be performed in a suitable local environment.

These lanes can overlap in time because they answer different evidentiary subquestions. They must not create different active product questions or make competing changes to the same canonical dossier.

## Single-writer and no-duplicate-PR rules

- At most **one write-capable agent at a time**. All other agents are read-only reviewers or clearly non-overlapping researchers.
- Never ask two coding agents to implement the same behavior concurrently. Before assigning anything, inspect open issues, branches and PR diffs.
- An agent task must name the canonical issue, target branch, files it may change, files it must not change, acceptance criteria and expected output.
- A reviewer should receive the same exact diff/source pins and should be asked to challenge it, not independently rewrite it.
- No auto-merge, agent self-approval, direct push to main, automatic branch deletion, extra cloud billing, or merging merely to clear the queue.
- The present open PRs include **three overlapping steering-deadzone proposals**: [#233](https://github.com/Master-Chiken/boonta-reborn-88/pull/233), [#243](https://github.com/Master-Chiken/boonta-reborn-88/pull/243) and [#247](https://github.com/Master-Chiken/boonta-reborn-88/pull/247). PR #247 was created by Jules; its two gameplay files have the same core deadzone change as #243, while #233 also carries unrelated branch-cleanup workflow work. Do not merge all three. Compare full diffs/checks, select at most one canonical implementation, and keep the unrelated changes separate. This overlap is a concrete reason to route tasks before launching additional agents.
- Research-first documentation changes do not validate the gameplay PRs. Every PR still needs exact-head checks, review, provenance checks where applicable, and the right level of manual acceptance.

## Required task request template

Canonical issue: #226
Active research question: Does the N64 lap/finish transition map to the public RAM-code addresses?
Agent role: independent public-source check (read-only)
Allowed inputs: public links and repository files listed in the issue
Forbidden: private ROM uploads, extracted course/assets, gameplay changes, merging, settings/billing changes
Required output:
1. Exact URLs and commit pins inspected.
2. Confirmed observations with line/address references.
3. Inferences clearly marked with confidence.
4. Evidence against the hypothesis and unknowns.
5. One minimal reproducible next check.
Stop condition: If a conclusion requires access to the owner's local ROM, report that blocker instead of guessing.

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
