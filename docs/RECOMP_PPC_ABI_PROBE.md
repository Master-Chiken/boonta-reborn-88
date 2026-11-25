# PowerPC ABI probe for the N64Recomp header

Date: 2026-11-25  
Status: the original header's native `__int128` path is unsupported by this devkitPPC target; a local multiply fallback and target-endian byte-lane adapter are used for the probe. Host tests, GameCube/Wii cross-compilation and the standalone GameCube DOL link have passed. Dolphin NoGUI confirms that its GameCube core is initialized and the DOL boot is requested, but UART markers are not emitted. The current CI revision replaces UART-based success detection with a GDB-readable stage marker; its execution result is pending.

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

`tests/recomp-abi/ppc_memory_lane_compat.h` adds a compile-time lane selector:
- big-endian targets (including Broadway PowerPC) use the address unchanged for byte and halfword accesses;
- little-endian targets retain the original XOR 3 / XOR 2 adjustments.

The patcher rewrites only the two byte and two halfword lane expressions in the fetched header, then injects this local adapter before the memory macros. The PowerPC compile probe has static assertions that the big-endian branch is selected and that these lane transforms are identity operations. A separate host test compiles both selector branches, including a force-big-endian test mode; that mode tests the selector only, not native big-endian pointer dereferences.

`tests/recomp-abi/test_ppc_mul64.c` checks edge cases and 10,000 deterministic operand pairs. On host builds where `__int128` is available, the result is compared with a compiler-provided 128-bit reference. The compatibility implementation itself does not use `__int128`.

`tests/recomp-abi/patch_recomp_header_for_ppc.py` applies two deliberately narrow changes to the ephemeral copy of the pinned header: it replaces the upstream conditional `DMULT/DMULTU` block with the local compatibility header, and it routes the two byte and two halfword lane adjustments through the target-endian selector. It checks that each anchor and expression occurs exactly the expected number of times and stops if the source layout differs. All other declarations and code in `recomp.h` remain from the exact upstream commit.

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

## Target-endian memory adapter: compile-time evidence only

The pinned upstream header uses little-endian host lane adjustments for:
- `MEM_B` and `MEM_BU`: `address ^ 3`;
- `MEM_H` and `MEM_HU`: `address ^ 2`.

The local adapter now selects:
- **little-endian host:** retain those XOR adjustments unchanged;
- **big-endian host:** use the N64 address directly for byte and halfword accesses.

`MEM_W` already dereferences the aligned address directly and is not changed. The `SD`/`LD` word order is also not changed; on a big-endian target its high word at offset 0 and low word at offset 4 should match N64 byte layout, but this still needs runtime verification.

The PowerPC compile probe checks that the compiler selects the big-endian branch and that its byte/halfword lane transforms are identity operations. A host test checks the selector in both little- and forced-big-endian modes. These tests verify the selector and preprocessor wiring, **not actual PPC memory dereferences**.

A native big-endian execution test remains necessary for byte, halfword, word, doubleword, and unaligned MIPS load/store behavior, including `LWL/LWR/SWL/SWR/LDL/LDR/SDL/SDR`. Do not claim these operations are fully correct until that test runs on an actual PowerPC target or a suitable big-endian emulator.

## Acceptance and limits

A green workflow means:

1. host tests pass for the big-endian byte-layout reference helpers;
2. host tests pass for both little-endian and forced-big-endian lane selection;
3. host tests pass for the portable 64x64-to-128 multiply fallback against a 128-bit reference;
4. the pinned N64Recomp header, with only the documented multiply and lane-selector changes applied in the ephemeral workspace, compiles for GameCube and Wii;
5. the two resulting object files have the expected ELF32, big-endian PowerPC identity.

It does **not** mean that:

- the unmodified N64Recomp header compiles unchanged (the observed toolchain explicitly rejects its `__int128` path);
- a PPC object was executed on hardware or an emulator;
- a DOL or ELF was linked against libogc;
- generated Racer game functions were compiled;
- the full runtime, bounded RDRAM map, scheduler, graphics, audio or input works;
- the actual `MEM_*` and unaligned MIPS load/store semantics have been executed on big-endian PowerPC; the current CI checks compile-time selection and host reference models only;
- the multiplication fallback has been validated through all MIPS instruction paths;
- a ROM or any ROM-derived content was used.

No ROM, generated functions, extracted assets, emulator binary or APK is part of this probe.

## Dolphin NoGUI runs 21–22: boot requested, main still unproven

- Run 21: https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45670641463  
  Commit: `81362a0d7a7a854a70950a30745b038bcdb9acb6`
- Run 22: https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45671113685  
  Commit: `cfcef7c23cc1db952d3124ea6387222a333401f0`

Both runs passed host tests, the GameCube/Wii cross-compiles and the DOL build/structural validation. Dolphin NoGUI 2512 produced these startup records:

- GameCube core startup was logged.
- EXI channel 0, device 1 was assigned the IPL MaskROM device.
- `Booting from executable: .../recomp_memory_probe.dol` was logged.
- Neither libogc `SYS_Report` nor a direct libogc EXI transfer produced the expected `START` marker before the 25-second timeout.

These runs confirm that Dolphin initializes a GameCube core and requests the DOL boot. They do **not** prove that the DOL reached `main()`, nor that any PowerPC memory helper executed.

## GDB-visible DOL execution marker

The current probe exports three symbols from its ELF:
- `g_probe_stage`: four ASCII bytes, initially `INIT`, set to `STAR` at the first instruction of `main()`, then `FAIL` or `PASS`;
- `g_probe_failure_code`: identifies whether a 32-bit or 64-bit assertion failed;
- `g_probe_failure_label`: the label of the first failed assertion.

The cross-compile job extracts their guest addresses with `powerpc-eabi-nm` and uploads those addresses alongside the DOL. The Dolphin job checks out the Python RSP client, enables Dolphin's built-in GDB server on localhost port 55000, lets the guest run, interrupts it, and reads the marker bytes through the GDB remote memory-read command. This avoids relying on the EXI debug UART and gives a direct memory observation of the guest program state.

Acceptance remains strict:
- `PASS` proves the DOL reached the end of the enumerated memory tests under Dolphin's GameCube emulation.
- `FAIL` identifies a failed scalar-width family and label; investigate before claiming compatibility.
- `STAR`, `INIT`, a GDB timeout, or any other state is **not** a successful memory test.

This is emulator evidence only, not a physical GameCube or Wii hardware test, and it does not validate the full N64 runtime, renderer, scheduler, audio or input integration.

## Dolphin run 16: no execution evidence yet

Workflow run: https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45666984369  
Commit: `6cf119f8406b613aafbf5701d48141db7f1c2995`

- The host tests passed.
- The exact pinned header cross-compiled for GameCube and Wii; the standalone GameCube DOL linked and passed the DOL/ELF structural validator.
- Dolphin 2512 installed successfully and remained alive until the 12-second timeout.
- The DOL's direct `SYS_Report` `START` marker was not captured. The uploaded artifact contained a 659-byte Qt-warning-only stdout file, an empty `dolphin.log`, and an empty `Logger.ini`. There was no `PASS` or `FAIL` marker.
- Therefore this run does **not** establish whether the DOL started, and it says nothing about the correctness or incorrectness of the memory operations.

The next workflow revision writes the expected `Logger.ini` settings explicitly before launch, prints Dolphin's version and CLI help, and allows a longer bounded run. This is a logging/launch diagnostic, not a relaxation of the test's acceptance criteria.

## Next gate

Obtain a captured DOL `START` marker and then `PASS` from Dolphin before claiming PPC memory execution. A `FAIL` marker must be traced to its exact operation and corrected. If no marker appears again, isolate Dolphin's DOL launch and OSReport path before changing the memory helpers. After successful emulated execution, test a small generated-code sample; do not start the full Racer runtime or GX renderer based on compile-only evidence.
