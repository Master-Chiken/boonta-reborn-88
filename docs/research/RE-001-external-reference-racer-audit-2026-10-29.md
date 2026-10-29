# RE-001 external reference audit — sp00nznet/racer

**Checked:** 2026-10-29  
**Purpose:** assess whether the public N64 static-recompilation project provides useful evidence for Boonta Reborn 88's research-first workflow, without treating it as proof of GameCube/Wii behavior.

## Source checked

- Repository: [sp00nznet/racer](https://github.com/sp00nznet/racer)
- Type: *Star Wars Episode I: Racer* Nintendo 64 static recompilation using N64Recomp.
- Revision checked: default branch `main`, tree `1197119fb6d4d1e60e9dfcc3d50d610475433af2`; latest visible commit at review time was dated 2026-10-25.
- Primary evidence: its [README/status and build instructions](https://github.com/sp00nznet/racer/blob/main/README.md), [source tree](https://github.com/sp00nznet/racer/tree/main/src), and [license](https://github.com/sp00nznet/racer/blob/main/LICENSE).

## What the project reports

The README describes a static recompilation, not a clean-room GameCube port or a completed decompilation. Its stated milestone status reports a booting game, visible intro/title/menu/race output, controller input, audio, and a playable tournament race on the Boonta Training Course. It also marks the overall playable build as in progress and widescreen as experimental. These are claims made by that project's README; this audit did not independently build or run it.

The documented engineering path is useful as a *process reference*: identify functions and symbols, maintain analysis tools, distinguish stubbed/misidentified OS functions from real implementations, wire scheduling/DMA/RSP/renderer behavior incrementally, and keep explicit milestone status. The repo also documents cross-platform packaging, but that is not a current blocker for Boonta's GameCube vertical slice.

## Relevance to Boonta — bounded conclusions

1. **Do not transplant its runtime or architecture into the GameCube prototype.** This repository targets N64 static recompilation and a PC runtime; Boonta's current target is a clean-room GameCube/Wii homebrew prototype. Similar game title and track names do not establish platform equivalence.
2. **Use it as a hypothesis/index source only.** Its public status and file organization can suggest questions to investigate, but any behavior claim relevant to the original PC version or N64/GC/Wii builds needs platform-specific evidence. It does not close RE-001's outstanding manager/intermediate-phase-to-results-screen call-path gap.
3. **Keep the current priority unchanged.** RE-001 remains the sole active research question. The next bounded step remains proving the missing edge from the post-race manager lifecycle to the concrete results-panel object/substate or a confirmed scene/resource transition. Do not open a parallel RE-002 task because of this reference.
4. **Do not claim validation from screenshots or README status.** No build, emulator, ROM, or executable was run as part of this audit. This is a repository/source-description review only.

## Provenance and licensing boundary

The repository's LICENSE identifies its tools/runtime/build files/documentation as MIT-licensed, while explicitly excluding the original game's code, art, audio, data, and generated derivatives from that grant. This audit imports no code, binary, assets, ROM bytes, raw disassembly, or generated output. It records only high-level observations with links to the source. Any future code reuse would require a separate file-level license/provenance review and must not include game-derived material.

## Result

**Useful as process context; not evidence of GameCube/Wii parity and not a substitute for the remaining RE-001 trace.** No implementation change is justified by this reference audit alone.
