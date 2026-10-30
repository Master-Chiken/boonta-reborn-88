# Kuna feasibility audit for Boonta Autonomous

**Reviewed:** 2026-10-29  
**Reference:** [Noelo-Lab/kuna](https://github.com/Noelo-Lab/kuna)  
**Scope:** determine whether Kuna is worth evaluating as a reverse-engineering tool for Boonta Reborn 88; this is not a compatibility certification.

## Executive decision

**Recommendation: run a small, isolated proof of concept before adopting it.** Kuna is a promising agent-first decompiler, but it is not a game porting tool and does not itself reconstruct assets, gameplay physics, rendering, or a complete original engine.

Kuna's README describes a Rust decompiler originally ported from Ghidra, with CLI, browser/WASM and Ghidra integration. The project emphasizes agent-driven refinement, phase-oriented implementation, configurable transforms and regression tests. The upstream project is Apache-2.0 licensed; review the exact files and bundled dependencies before any redistribution or integration.

## Potential value to Boonta

1. **Readable function pseudocode:** decompile candidate functions and compare their output with the current analysis.
2. **Call-path research:** use function and cross-reference information from the surrounding reverse-engineering workflow to help trace the finish manager, race state transitions and results UI.
3. **Agent-friendly evidence:** ask an agent to report function address, input binary/build identity, decompiler output, callers/callees, confidence, and a reproducible verification step—not just a narrative guess.
4. **Repeatable experiments:** compare output versions against a fixed sample corpus and retain logs so a tool upgrade cannot silently invalidate earlier conclusions.

## Important compatibility unknowns

The project is written in Rust and originated from Ghidra, but that alone does **not** prove it can ingest our exact GameCube executable format or decode it correctly. Before using it for RE-001, establish:

- which original game binary/build is available and legally held by the project maintainer;
- whether the relevant GameCube PowerPC instruction language/specification is supported in the exact Kuna release;
- whether the original executable/container can be loaded directly, or requires a documented conversion/import step;
- whether function boundaries, references, and data/code separation are trustworthy for this binary;
- whether output agrees with independent evidence from the existing analysis workflow.

Do not infer GameCube behavior from the N64 sp00nznet/racer project or from a decompiler's plausible-looking pseudocode alone.

## Bounded proof of concept

1. Select a tiny, already understood function or a legally available synthetic PowerPC test binary; do not commit copyrighted game binaries, ROMs, extracted assets, or generated game-derived output.
2. Pin a Kuna release/commit and document the host platform, input format, language ID, and exact invocation.
3. Run Kuna offline with no paid model/API calls. Kuna is a decompiler; any separate agent orchestration must keep the repository's free-only guardrails.
4. Compare output with a second independent analysis source and manually verify the control flow/instructions.
5. Stop if the format or language support is unclear, output is materially misleading, or the tool cannot be used reproducibly.

## Decision criteria

**Adopt as an optional analysis backend only if** the test is reproducible, supports the exact input architecture/format, provides useful evidence beyond the current workflow, and does not introduce paid calls or unreviewed game-derived files.

**Do not** make Kuna a build dependency, replace the current workflow wholesale, or create a parallel research workstream until the proof of concept passes.

## Relation to current priority

RE-001 remains the only active reverse-engineering question: establish the unproven link from the post-race manager lifecycle to the exact results-panel object/substate or confirmed scene/resource transition. Kuna may be evaluated against a narrow function relevant to that trace, but this audit alone does not resolve RE-001 and does not justify claiming the results path is understood.

## Source links

- [Kuna README and documented usage](https://github.com/Noelo-Lab/kuna#readme)
- [Kuna source tree](https://github.com/Noelo-Lab/kuna/tree/main)
- [Kuna license](https://github.com/Noelo-Lab/kuna/blob/main/LICENSE)
- [Boonta RE-001 research priority](https://github.com/Master-Chiken/boonta-reborn-88/pull/242)

**Status:** feasibility review only. No Kuna installation, decompilation, game binary analysis, emulator run, or build test was performed during this review.
