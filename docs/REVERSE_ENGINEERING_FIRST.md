# Reverse-engineering first: mandatory reuse gate

**Status: mandatory project rule.** This policy applies to every human and AI contributor, every provider (Gemini, OpenRouter, Groq, Copilot, Jules or another agent), and every task: gameplay, rendering, tracks, vehicles, assets, audio, tools, parsers, tests, documentation and automation.

## Non-negotiable rule

> **Never manually recreate, re-model, re-code, re-author, or approximate an element before establishing that the existing game, its documented reverse-engineering work, the repository, or an already available tool cannot recover, explain, convert, reuse, or reproduce it automatically.**

The default is **DISCOVER → VERIFY → EXTRACT/CONVERT/REUSE → INTEGRATE → TEST**. Rebuilding from scratch is the exception and requires a short, evidence-backed reason.

This rule does **not** authorize copying third-party source code or redistributing commercial game content. Reuse is permitted only when provenance, licence, platform/version compatibility and redistribution rights are verified. Where rights are unclear, preserve the finding and keep the material local/on hold; do not replace that legal restriction with a manual copy or an unlicensed substitute.

## Mandatory pre-implementation gate

Before writing a new implementation or creating an asset by hand, the contributor must:

1. **Search existing work first:** inspect the current Boonta source, generated outputs, exporters, parsers, fixtures, tests, docs, open PRs/branches and canonical issues. Reuse or continue an existing candidate rather than creating a duplicate.
2. **Identify the original/reference:** name the exact game/platform/version, public source/repository revision, file/format, symbol/function, asset identifier or observed runtime behavior relevant to the task. Do not assume PC, N64, Dreamcast, GameCube and Wii data or behavior are interchangeable.
3. **Choose the least-duplicative recovery path:** determine whether the needed result can be extracted, decoded, converted, generated, reconstructed from documented data, or reproduced by an existing tool. Prefer an existing tool/pipeline; add a converter only when a specific missing conversion is demonstrated.
4. **Verify safety and compatibility:** record exact revision, source, licence/provenance, platform, format, dependencies and compatibility. Keep AGPL or otherwise incompatible code read-only unless an explicit licence review authorizes reuse. Keep commercial ROMs/disc images/BIOS and proprietary or unclear-provenance assets out of the public repository, CI and hosted model prompts.
5. **Record evidence and unknowns:** separate confirmed facts, inferences and unknowns. A README, AI claim, filename, visual resemblance or success on another platform is not proof. If the required source/archive is unavailable, say so; never pretend it was inspected.
6. **Only then decide to rebuild:** manual recreation or a new implementation is allowed only if evidence shows the original element is unavailable, unrecoverable, incompatible with the target, legally unusable, or materially unsuitable. State which condition applies and why extraction/conversion/reuse was rejected.

If any gate item is unresolved, the task is **RESEARCH/BLOCKED**, not permission to guess and build. Ask one narrow research question or record the exact external dependency.

## Required task/PR evidence

Every relevant task and PR must include a compact **Reuse / reverse-engineering decision**:

- Existing candidate(s) inspected (file, tool, PR, source revision or asset/format).
- Recovery path tested or ruled out, with evidence.
- Platform/version and compatibility status.
- Licence/provenance status; anything on HOLD.
- What is being reused, converted, independently reimplemented, or manually recreated—and why.
- Acceptance test proving the result, plus what remains unverified.

For recovered or converted outputs, add deterministic tests/fixtures where practical (for example: parser bounds, decoded dimensions, stable hashes/metadata, round-trip or equivalence checks). Do not claim an original asset/behavior was recovered unless the source and conversion result are traceable.

## Agent decision contract

Before a write-capable agent edits files, its plan must explicitly answer:

1. What existing original/reference/repository work did I inspect?
2. What can be recovered or reused without new manual recreation?
3. What exact licence, provenance or platform boundary limits reuse?
4. Why is any proposed new implementation genuinely necessary?
5. What evidence and test will prove the result?

A reviewer must reject a change that skips this gate, duplicates recoverable work, or substitutes speculative hand-built content for an unexamined recoverable original. The gate is not an 80/20 research quota: research must be targeted and sufficient to make the reuse decision, then implementation and tests can proceed.

## Practical boundaries for Boonta Reborn

- The original Racer has no identified retail GameCube/Wii release. The native GameCube/Wii build is our clean-room port target; use PC/N64/Dreamcast work only as separately labelled behavioral/format evidence, never as proof of console parity.
- Existing reverse-engineering dossiers, system matrices, route-runtime PRs, code, exporters and tests are project assets. Inspect and reuse them before opening another investigation or subsystem.
- Keep the Step 102 archive, AGPL source, ROM-derived code, commercial assets and uncertain data on HOLD unless a specific item receives a documented provenance/licence decision.
- Reconstruct behavior independently when required; do not copy code, proprietary data, structure layouts or constants from sources whose licence or provenance does not permit it.
- Do not create a broad new inventory, converter, framework or toolchain merely to satisfy this rule. Use the smallest targeted check that answers the selected task.

**Short version:** if reverse engineering can recover it, do not rebuild it by hand. If reuse is unsafe or impossible, prove why, record the reason, then implement the smallest clean-room alternative.
