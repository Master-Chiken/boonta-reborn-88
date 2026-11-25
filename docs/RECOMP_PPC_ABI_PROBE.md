# PowerPC ABI probe for the N64Recomp header

Date: 2026-11-25  
Status: the original header's native `__int128` path is unsupported by this devkitPPC target; a local, tested fallback is now used for the probe. The final CI result is the evidence gate.

## Question

Can the N64Recomp header pinned by `dguillot-gh/star-wars-racer-recomp` compile for 32-bit, big-endian PowerPC GameCube and Wii targets after replacing its unsupported 64x64-to-128 multiply helper with a clean-room, portable fallback?

This is a narrow compiler/ABI feasibility test. It is not a port of the N64 runtime or game.

## Inputs and provenance

- Header repository: https://github.com/dguillot-gh/N64Recomp
- Exact revision: `36286fb9a96f325a64b3c600131ba00af44654fc`
- Header path: `include/recomp.h`
- The upstream repository's `LICENSE` at the inspected revision is MIT.
- CI fetches that exact upstream commit into an ephemeral workspace. It does not vendor or copy the upstream header into Boonta.
- Compiler image: `devkitpro/devkitppc:20261102`, using devkitPPC 16.2.0 in the observed run. The devkitPro Dockerfile installs the GameCube and Wii development package groups: https://github.com/devkitPro/docker/blob/master/devkitppc/Dockerfile
- devkitPro's build scripts distinguish the GameCube `-mogc` and Wii `-mrvl` target options: https://github.com/devkitPro/buildscripts

## Confirmed blocker in the unmodified header

The first cross-compile against the exact, unmodified upstream header failed at:

```text
#error "128-bit integer type not found"
```

The compiler itself was found and identified as `powerpc-eabi-g++ (devkitPPC) 16.2.0`; the exact N64Recomp commit was fetched successfully. The failure happened as soon as the upstream `recomp.h` selected its wide-multiply code path: this target did not define `__SIZEOF_INT128__`, and the header's non-MSVC fallback is a hard error.

**Conclusion:** the pinned header cannot be compiled unchanged by this devkitPPC target. This is a genuine adaptation requirement, not a tool-installation problem.

## The bounded fallback

`tests/recomp-abi/ppc_int128_compat.h` supplies only `DMULT` and `DMULTU` using four 32x32-bit products and explicit carry accumulation. The signed version obtains the two's-complement 128-bit product by applying the high-word corrections when either operand is negative.

`tests/recomp-abi/test_ppc_mul64.c` checks edge cases and 10,000 deterministic operand pairs. On host builds where `__int128` is available, the result is compared with a compiler-provided 128-bit reference. The compatibility implementation itself does not use `__int128`.

`tests/recomp-abi/patch_recomp_header_for_ppc.py` applies a deliberately narrow patch to the ephemeral copy of the pinned header: it replaces only the upstream conditional `DMULT/DMULTU` block with an include of the local compatibility header. All other declarations and code in `recomp.h` remain from the exact upstream commit. The patcher checks unique anchor strings and stops if the source layout differs.

This is a feasibility shim for the experiment, not a claim that the upstream project has accepted this patch. Before any production integration, review the arithmetic independently and test it through the actual generated instructions/contexts.

## What the PowerPC compile checks

`tests/recomp-abi/recomp_header_compile.cpp` includes the patched copy of the exact upstream header and forces the compiler to instantiate representative paths:

- 32-bit pointers and `uintptr_t`, 64-bit `gpr` and `fpr` storage;
- expected offsets and 544-byte size of `recomp_context` under the 32-bit PowerPC ABI;
- signed/unsigned multiplication and division helpers;
- GCC's `noipa` and `optimize("rounding-math")` attributes through `RECOMP_FUNC`;
- `fenv` and rounding-aware conversion functions;
- the upstream `MEM_B/H/HU/BU/W`, `SD` and `LD` macros at compile time.

The workflow compiles the same source twice: once with `-mogc` and once with `-mrvl`. It checks that both output objects are ELF32, big-endian PowerPC objects.

`tests/recomp-abi/n64_memory_be.h` is a separate clean-room reference model for N64 big-endian byte layout. Its host tests cover 8/16/32/64-bit reads and writes, unaligned reads, and signed scalar extension. It is not a production replacement for N64Recomp's memory macros.

## Separate, unresolved endian issue

The pinned upstream header applies XOR lane adjustments unconditionally:

- `MEM_B` and `MEM_BU` use `address ^ 3`;
- `MEM_H` and `MEM_HU` use `address ^ 2`.

Those are the little-endian-host lane adjustments. A successful big-endian PowerPC compile does **not** prove that these accesses are semantically correct on Broadway. The compile probe only proves that the syntax, types, attributes and helper operations compile after the explicit multiply shim.

A separate target-specific memory-access adapter is still required, preserving the little-endian behavior for Android/Windows. It must test byte, halfword, word, doubleword and unaligned load/store behavior on a big-endian execution target.

## Acceptance and limits

A green workflow means:

1. host tests pass for the big-endian byte-layout reference helpers;
2. host tests pass for the portable 64x64-to-128 multiply fallback against a 128-bit reference;
3. the pinned N64Recomp header, with only its `DMULT/DMULTU` block replaced in the ephemeral workspace, compiles for GameCube and Wii;
4. the two resulting object files have the expected ELF32, big-endian PowerPC identity.

It does **not** mean that:

- the unmodified N64Recomp header compiles unchanged (the observed toolchain explicitly rejects its `__int128` path);
- a PPC object was executed on hardware or an emulator;
- a DOL or ELF was linked against libogc;
- generated Racer game functions were compiled;
- the full runtime, bounded RDRAM map, scheduler, graphics, audio or input works;
- the upstream `MEM_B/H` lane adjustments are correct on PowerPC;
- the multiplication fallback has been validated through all MIPS instruction paths;
- a ROM or any ROM-derived content was used.

No ROM, generated functions, extracted assets, emulator binary or APK is part of this probe.

## Next gate

After the CI passes, isolate the N64 target-endian memory adapter and prove it with actual PPC execution (preferably a tiny DOL/ELF and a controlled test on Dolphin, then real hardware). Only then attempt a small sample of locally generated C. Do not start the full Racer runtime or GX renderer based on compile-only evidence.
