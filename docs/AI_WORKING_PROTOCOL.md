# AI coordination protocol — Boonta Reborn 88

**Purpose:** keep every human and AI contributor aligned on one technical objective and prevent duplicated work, speculative implementation and platform drift.

## 1. Single project objective

Prioritize research and engineering that moves toward a native, playable Star Wars: Episode I – Racer remaster for GameCube and/or Wii: understand the original game, recover or parse lawfully available original-format data, convert compatible data, and integrate it into a working target runtime. Synthetic clean-room demo assets are useful test harnesses, not proof that original-game data has been recovered or that the original game has been ported.

Do not let side experiments, broad refactors, extra content, renderer polish, or a second platform displace the current highest-value blocker. Dreamcast is a separate experiment. PC and N64 are research references, not assumed-compatible source formats.

## 2. Mandatory reuse-first decision order

Before any new implementation:

1. Search existing Boonta source, tools, fixtures, tests, documentation, issues, branches and open PRs.
2. Search relevant community/upstream repositories and prior art.
3. Compare exact platform, format/version, input/output requirements, maintenance, dependencies, license, provenance and redistribution constraints.
4. Reuse suitable in-repository code or a compatible upstream solution.
5. If needed, add the smallest adapter or focused extension.
6. Create a replacement only after documenting why existing options cannot satisfy the requirement.

Never infer compatibility from a project name or from support for the PC/N64 release. Never copy code/assets before rights and provenance are checked. If evidence is missing, the correct next task is a focused investigation, not speculative coding.

Use [REUSE_FIRST_AUDIT.md](REUSE_FIRST_AUDIT.md) as the starting inventory and keep it current when findings materially change.

## 3. Shared work protocol for every agent

At the start of a task, inspect the current default branch and relevant open PRs/issues. State:

- **Goal:** the specific blocker and milestone it advances.
- **Already exists:** relevant Boonta implementation and community solutions checked.
- **Reuse choice:** what will be reused and why it is suitable.
- **Remaining gap:** the smallest capability that is genuinely missing.
- **Risks:** target/format uncertainty, license/provenance, dependency and €0 budget constraints.
- **Acceptance evidence:** exact tests and observable result; identify what automated tests cannot prove.
- **Integration:** existing branch/PR to use or reason a new one is needed.

Before starting work, check whether another contributor/agent is already addressing the same files or behavior. Prefer extending an appropriate existing PR over creating a duplicate. If the work overlaps, coordinate the scope instead of making parallel conflicting implementations.

## 4. Role boundaries

- **Read-only coordinator/research agents:** inspect, compare, report evidence, and recommend one next task. They do not write code or assume approval.
- **Code-writing agents:** implement only the approved scope, on a task branch, after verifying approval and re-reading the current instructions.
- **Review agents:** independently check correctness, reuse, compatibility, license/provenance, tests and scope. Do not treat another AI's assertion as proof.
- **All agents:** no direct pushes to main, no merging or auto-merge, no paid model/API/cloud fallback, no secret disclosure, and no public import of ROMs, disc images or uncleared commercial assets.

A repository instruction cannot force an external AI service to load it in every mode. When using an external agent manually, provide this protocol and the relevant project instructions as context.

## 5. Required output from an AI proposal

Every substantial proposal must identify the reused components and link to their source, explain the remaining gap, list license/platform uncertainties, and give a testable acceptance criterion. If no reusable solution is suitable, show what was checked and why it was rejected. Avoid vague recommendations such as “build a new framework” without evidence.

## 6. Verification and truthful reporting

Keep these claims separate: host tests, native DOL/ELF build, Dolphin null-backend smoke, scripted visual/DTM checks, manual controller-driven Dolphin play, and physical GameCube/Wii hardware tests. A successful build or screenshot is not proof of a complete playable race.

The budget is €0. If a free quota is exhausted, stop rather than enabling billing or switching to a paid fallback. Never transmit secrets or private/commercial assets to an external AI provider.

## 7. Definition of progress

Progress means a verified reduction in the highest-priority blocker to a native playable race, ideally by reusing proven work. Number of commits, branches, tools, generated assets or AI comments is not progress by itself.
