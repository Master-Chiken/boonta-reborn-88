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


## Recheck — N64 MIPS ELF language selection and compact output (2026-11-01)

A read-only source audit of Kuna commit [`f8746b9730b525a065c89c26e358ffd7c2328bc7`](https://github.com/Noelo-Lab/kuna/commit/f8746b9730b525a065c89c26e358ffd7c2328bc7) improves the feasibility assessment, but does **not** yet pass the game-specific proof of concept.

### What is now source-verified

- Kuna vendors MIPS big-endian SLEIGH language definitions for both MIPS32 and MIPS64. The MIPS64 definitions include a 32-bit-address variant, `MIPS:BE:64:64-32addr`, with compiler-spec variants including `o32`, `n32`, and `o64`.
- The current generic ELF language composer maps `object::Architecture::Mips` to `MIPS:{endian}:32:default:default`. Therefore a big-endian MIPS ELF will not automatically select the MIPS64/32-bit-address decoder candidate simply because the file is related to Nintendo 64. The exact architecture and ABI must be established from the actual ELF header, `e_flags`, and toolchain metadata.
- Kuna's documented `--target <SLEIGH-language-id>` option can explicitly select a decoder while retaining section mappings and image base from a recognized object container. The docs state that decoder width/architecture may differ from the container header; an endian disagreement is reported, but the requested decoder is still used.
- Kuna's MIPS marker pass is gated to ELF/MIPS and handles MIPS and MIPS64 object architecture variants. That confirms a MIPS-specific analysis path exists; it is not proof that a particular N64 executable is decoded correctly.
- The latest commit adds `--omit line_mappings,variables,types` to `decompile --json` and `decompile-all --json`. Omitted collections are absent (not represented as empty), are listed in a top-level `omitted` array, and variable/stack-object and provenance work is skipped where applicable. This is useful for keeping a one-function report compact.

### Bounded proof of concept — revised

The first input must be the locally held `n64_main.elf` from the earlier analysis workflow, **not** the raw `.z64` ROM. Before decompiling, record:

1. `readelf -h -A` output: ELF class, endianness, machine, ABI flags and architecture flags;
2. the existing function map / code address convention used by the local disassembly;
3. the exact Kuna release or pinned commit and host platform.

Then select the SLEIGH language explicitly from the ELF evidence. `MIPS:BE:64:64-32addr` is a candidate to test only if the file metadata supports a 64-bit MIPS ISA with 32-bit addresses; choose its compiler model (`o32`, `n32`, or another declared model) from the actual ABI evidence, not from the game title alone.

Illustrative one-function invocation after those values are established:

```bash
kuna decompile ./n64_main.elf <known-function-address> --addr \
  --target <verified-MIPS-SLEIGH-language-id> --json \
  --omit line_mappings,variables,types
```

Compare the resulting control flow and register/data accesses against the already existing local MIPS disassembly and known writer/reader relationships. A plausible-looking C body is not accepted unless those instruction-level checks agree.

### Current result and blocker

**Source compatibility has improved from “MIPS unknown” to “MIPS ELF + MIPS big-endian SLEIGH languages are present, with an explicit decoder override available.” The exact N64 ELF/ABI selection remains unverified.**

The prior local notes mention `/tmp/n64_main.elf`, but that file and the source ROM are not mounted in the current working session. Therefore no installation, decompilation, binary upload, emulator run, or game-specific Kuna test was performed here. Do not claim Kuna has successfully decompiled this N64 binary, and do not upload the ROM, ELF, decompiler output, or extracted game data to GitHub/cloud services.

This remains a **single bounded RE-001 tool check**, not a new workstream. It does not resolve the conditional normal-finish → visible Results runtime question. RE-002 stays parked.

### Pinned upstream references

- [Kuna MIPS language definitions at the reviewed commit](https://github.com/Noelo-Lab/kuna/blob/f8746b9730b525a065c89c26e358ffd7c2328bc7/specs/Ghidra/Processors/MIPS/data/languages/mips.ldefs)
- [Kuna ELF language selection](https://github.com/Noelo-Lab/kuna/blob/f8746b9730b525a065c89c26e358ffd7c2328bc7/decompiler/crates/kuna-analysis/src/loadimage_object.rs)
- [Kuna MIPS ELF markers](https://github.com/Noelo-Lab/kuna/blob/f8746b9730b525a065c89c26e358ffd7c2328bc7/decompiler/crates/kuna-analysis/src/loader/mips_markers.rs)
- [Kuna MIPS ELF language/ABI definitions](https://github.com/Noelo-Lab/kuna/blob/f8746b9730b525a065c89c26e358ffd7c2328bc7/specs/Ghidra/Processors/MIPS/data/languages/MIPS.opinion)
- [Kuna compact JSON options](https://github.com/Noelo-Lab/kuna/blob/f8746b9730b525a065c89c26e358ffd7c2328bc7/docs/cli.md)
- [Kuna documented `--target` behavior](https://github.com/Noelo-Lab/kuna/blob/f8746b9730b525c89c26e358ffd7c2328bc7/docs/cli.md)


## Recheck — owner-held ROM, synthetic ELF and LLVM decoder validation (2026-11-01)

The earlier note that the original `n64_main.elf` was not present in the current working session remains true, but the owner-held US N64 ROM is available in the Library. It was materialized only into the private working directory for a local static-tool check; it was not uploaded to GitHub or an external analysis service.

Using the main code-section mapping documented in the pinned upstream `symbols.toml`, a **minimal synthetic ELF64 big-endian MIPS III wrapper** was constructed around the exact code-section bytes. `readelf` recognizes the ELF header and executable segment, and LLVM 17 `llvm-objdump` successfully decodes the code with a MIPS III target. A targeted local re-decode reproduces the already documented participant event-counter → configured threshold → same-record finish/skip writer/reader relationship.

### What this does and does not change

- **Improved:** the MIPS III code bytes can now be consumed by a second local disassembler without needing the earlier missing `n64_main.elf` file. The same-record finish-state logic has a fresh decoder cross-check.
- **Not resolved:** the synthetic wrapper has no data/BSS/resources, symbol table, relocations or authentic ABI metadata. Its ELF64 class and MIPS III flags are properties of the wrapper, not proof of the original analysis ELF's ABI. The compiler model for Kuna's `MIPS:BE:64:64-32addr` candidate therefore remains to be verified.
- **Still not run:** Kuna itself is not installed in the current environment; neither a Kuna one-function decompilation nor comparison of its pseudocode has occurred. The original complete ELF and its ABI/toolchain metadata are still unavailable here.
- **Runtime remains separate:** no emulator, visible race, write-watchpoint hit or Results-screen observation has been produced. This tool check does not close the conditional finish-to-Results runtime question.

Treat this as a useful local decoder/format experiment, **not** a passed Kuna proof of concept. No ROM bytes, disassembly text, generated C, assets or game-derived output were uploaded or committed. RE-002 remains parked.
