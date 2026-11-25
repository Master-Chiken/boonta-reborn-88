# PowerPC ABI probe for the N64Recomp header

Date: 2026-11-25  
Status: cross-compile probe added; CI result is the evidence gate.

## Question

Can the exact `recomp.h` header pinned by `dguillot-gh/star-wars-racer-recomp` compile for the 32-bit, big-endian PowerPC targets used by GameCube and Wii, including its compiler attributes, 128-bit multiply helpers, floating-point environment calls, and `recomp_context` layout?

This is a narrow P1 feasibility test. It is not a port of the N64 runtime or game.

## Inputs and provenance

- Header repository: https://github.com/dguillot-gh/N64Recomp
- Exact revision: `36286fb9a96f325a64b3c600131ba00af44654fc`
- Header path: `include/recomp.h`
- The upstream repository's `LICENSE` at that revision is MIT.
- The workflow fetches that commit into the ephemeral CI workspace and compiles against its header. The upstream source is not copied or vendored into Boonta.
- Compiler image: `devkitpro/devkitppc:20261102`, a dated devkitPro PowerPC toolchain image. The devkitPro Dockerfile installs the GameCube and Wii development package groups: https://github.com/devkitPro/docker/blob/master/devkitppc/Dockerfile
- devkitPro's build instructions distinguish the GameCube `-mogc` and Wii `-mrvl` target switches: https://github.com/devkitPro/buildscripts

## What the probe checks

`tests/recomp-abi/recomp_header_compile.cpp` includes the exact pinned upstream header and forces the compiler to instantiate representative paths:

- 32-bit pointers and `uintptr_t`, 64-bit `gpr` and `fpr` storage;
- the expected offsets and 544-byte size of `recomp_context` under the 32-bit PowerPC ABI;
- the `__int128`, signed/unsigned multiply, signed/unsigned divide and sign-extension surface;
- GCC's `noipa` and `optimize("rounding-math")` attributes through `RECOMP_FUNC`;
- `fenv` and rounding-aware conversion functions;
- the actual upstream `MEM_B/H/HU/BU/W`, `SD` and `LD` macros at compile time.

The workflow compiles the same source twice: once with `-mogc` and once with `-mrvl`. It then checks that both object files are ELF32, big-endian PowerPC objects.

`tests/recomp-abi/n64_memory_be.h` is a separate clean-room reference model for N64 big-endian byte layout. Its host tests cover 8/16/32/64-bit reads and writes, unaligned reads, and signed scalar extension. It is deliberately not presented as a production replacement for N64Recomp's memory macros.

## Important semantic blocker remains

The pinned upstream header currently applies XOR lane adjustments unconditionally:

- `MEM_B` and `MEM_BU` use `address ^ 3`;
- `MEM_H` and `MEM_HU` use `address ^ 2`.

That is the little-endian-host lane strategy. A successful big-endian PowerPC compile does **not** establish that these accesses are semantically correct on Broadway. The compile probe only proves that the header's syntax, attributes, types and helper operations are accepted by the compiler.

A later, separate change must introduce a target-specific memory access layer and test the actual `MEM_*` behavior on a big-endian execution target. Do not delete or alter the existing little-endian behavior globally.

## Acceptance and limits

A green workflow means:

1. the host reference tests for the N64 big-endian byte model pass;
2. the exact upstream header at the pinned commit compiles for both devkitPPC GameCube and Wii target modes;
3. the compiled object files have the expected ELF32, big-endian PowerPC identity.

It does **not** mean that:

- a PPC object was executed on real hardware or an emulator;
- a DOL or ELF was linked against libogc;
- generated Racer game functions were compiled;
- the full runtime, RDRAM map, scheduler, graphics, audio or input works;
- the current upstream `MEM_B/H` lane adjustments are correct on PowerPC;
- a ROM or any ROM-derived content was used.

No ROM, generated functions, extracted assets, emulator binary or APK is part of this probe.

## Next gate

If the compile job passes, implement a target-specific endian adapter in an isolated compatibility header, preserving the existing little-endian macros for Android/Windows. Add runtime tests for byte/halfword/word/doubleword access and unaligned load/store semantics before attempting any Racer-generated C. If the compile job fails, record the exact compiler diagnostic and isolate the first unsupported construct before changing upstream-derived code.
