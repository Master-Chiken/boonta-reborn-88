# PowerPC ABI probe for the N64Recomp header

Date: 2026-11-25  
Status: the pinned header requires a clean-room 64x64-to-128 multiply fallback and target-endian byte-lane adapter for devkitPPC. **Host tests, Dolphin GDB client unit tests, GameCube/Wii cross-compilation, DOL linking, and synthetic PowerPC memory execution under Dolphin all pass** in runs [45681454118](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45681454118) and [45682077821](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45682077821). Latest source commit: `36d3fb59b52cc6972e15327a4d7386736e159a21`. This is emulated GameCube DOL evidence for the listed helper operations only; no original Racer generated code, full runtime, GX renderer, physical Wii, or physical GameCube has been tested.

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

## Target-endian memory adapter: compile-time and Dolphin execution evidence

The pinned upstream header uses little-endian host lane adjustments for:
- `MEM_B` and `MEM_BU`: `address ^ 3`;
- `MEM_H` and `MEM_HU`: `address ^ 2`.

The local adapter now selects:
- **little-endian host:** retain those XOR adjustments unchanged;
- **big-endian host:** use the N64 address directly for byte and halfword accesses.

`MEM_W` remains a direct aligned access. The `SD`/`LD` word order was not changed; the DOL checks that the high word appears at offset 0 and the low word at offset 4 on big-endian PowerPC.

Host tests verify the selector in little-endian and forced-big-endian modes. In addition, the standalone GameCube DOL now executes the actual patched upstream `MEM_B/H/HU/BU/W`, `SD/LD`, and the upstream MIPS unaligned helpers on a 32-bit big-endian PowerPC CPU emulated by Dolphin.

The passing vectors cover:
- signed and unsigned byte/halfword reads, including 64-bit sign extension into `gpr`;
- word/doubleword reads and writes, including the `SD/LD` word layout;
- every byte lane of `LWL/LWR/SWL/SWR` and `LDL/LDR/SDL/SDR`;
- explicit negative-result sign-extension cases for `LWL/LWR`.

This is real guest-code execution under Dolphin's GameCube emulation, not a native hardware result. It validates only the helpers and synthetic backing memory used by this DOL; it does not validate a complete N64 RDRAM map, PI/MMIO, heap, or original Racer code.

## Acceptance and limits

A green workflow means:

1. host tests pass for the big-endian byte-layout reference helpers;
2. host tests pass for both little-endian and forced-big-endian lane selection;
3. host tests pass for the portable 64x64-to-128 multiply fallback against a 128-bit reference;
4. the Dolphin GDB RSP client passes its host protocol tests;
5. the pinned N64Recomp header, with only the documented multiply and lane-selector changes applied in the ephemeral workspace, compiles for GameCube and Wii;
6. the two resulting object files have the expected ELF32, big-endian PowerPC identity;
7. the standalone synthetic GameCube DOL reaches its `PASS` marker under Dolphin after exercising the enumerated scalar and unaligned memory helpers.

Run [45681454118](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45681454118) reached `START` and then `PASS`. The diagnostic run before the LWR reference-vector correction reached `FAIL` at `LWR`; the actual value was `0xFFFFFFFFAABBCC11`, and the test's former zero-extended expected value was incorrect for the N64Recomp MIPS64 helper semantics. The test vector was corrected; the helper implementation was not changed.

It does **not** mean that:

- the unmodified N64Recomp header compiles unchanged (the observed toolchain explicitly rejects its `__int128` path);
- an actual GameCube or Wii executed the DOL; the execution evidence is Dolphin emulation;
- generated Racer game functions were compiled or run;
- the full N64 runtime, segmented RDRAM map, PI/ROM reads, scheduler, GX graphics, audio or input works;
- the probe proves every MIPS instruction path beyond the explicit test vectors;
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

## Dolphin run 28: GDB port was not enabled by the config token

Workflow run: https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45672755100  
Commit: `87cabba1c900bdde7b6b36426f39d25b85a6182f`

- Host big-endian model/selector/multiply tests passed.
- The pinned header compiled for GameCube and Wii; the DOL linked, validated and exported its three initial stage/failure symbols.
- Dolphin NoGUI 2512 installed and launched, but the GDB client could not connect to port 55000 after 30 seconds. The DOL stage was therefore not inspected.
- Root cause: Dolphin's command-line config parser names the `System::Main` section `Dolphin`, not `Main`. The correct override is `Dolphin.General.GDBPort=55000`; `Main.General.GDBPort` is silently ignored by the parser's recognized system-name map.

The workflow now uses the correct configuration token. This was a test-harness configuration error; it is not evidence of a memory-helper failure or a successful DOL execution.

## GDB-visible DOL execution markers

The DOL retains diagnostic globals in its ELF:
- `g_probe_stage`: four ASCII bytes, initially `INIT`, then `STAR`, `FAIL`, or `PASS`;
- `g_probe_failure_code`: identifies a 32-bit or 64-bit assertion;
- `g_probe_failure_label`: the first failed assertion's name;
- `g_probe_failure_actual` and `g_probe_failure_expected`: the mismatching values stored as 64-bit integers.

The DOL also exports three distinct noinline functions: `probe_start_marker`, `probe_pass_marker`, and `probe_fail_marker`. Each writes a different value to a volatile marker sink so the linker cannot fold their addresses together. The cross-compile job extracts their addresses and text symbols with `powerpc-eabi-nm`, then uploads them alongside the DOL.

The Dolphin job enables the built-in GDB server on localhost port 55000 using `Dolphin.General.GDBPort`, and enables `Dolphin.Interface.DebugModeEnabled` so Dolphin's JIT checks software breakpoints. The host RSP client sets GDB `Z0` breakpoints at the three marker functions, continues the guest, and waits for stop packets:
1. `probe_start_marker` proves the DOL reached `main()`;
2. `probe_pass_marker` proves all enumerated memory assertions completed;
3. `probe_fail_marker` identifies an assertion failure; the client then reads the failure code, label, actual value, and expected value via GDB memory reads.

The pass/fail decision therefore depends on the guest's actual PowerPC execution path, not emulator uptime or EXI debug UART output. The host also runs unit tests for the RSP packet/ACK handling, including asynchronous continue and stop replies.

Acceptance remains strict:
- `PASS` proves the DOL reached the end of the enumerated helper tests under Dolphin's GameCube emulation.
- `FAIL` identifies a test failure; fix the test oracle or helper only after checking the exact upstream semantics and actual/expected values.
- no marker, a timeout, or a stop at an unexpected PC is **not** a successful memory test.

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

## Successful synthetic execution under Dolphin — runs 47 and 50

- Run 47: https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45681454118  
  Tested memory-vector commit: `316ef641238e309f518e3eef9cddd81f0f0397b4`
- Run 50: https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45682077821  
  Documentation and host-client-test commit: `36d3fb59b52cc6972e15327a4d7386736e159a21`

Both runs passed the host memory-model tests, GameCube/Wii cross-compilation, DOL link/structure checks, and Dolphin guest execution. Run 50 additionally passed all four host tests of the Dolphin GDB RSP client.

Dolphin 2512 accepted all three GDB software breakpoints. It stopped first at `probe_start_marker` (PC `0x800033a4`) and then at `probe_pass_marker` (PC `0x800033b8`). It did not reach `probe_fail_marker`. This proves that the synthetic DOL executed the enumerated memory assertions to completion in Dolphin's GameCube core.

The first DOL execution exposed a test-oracle error for `LWR` sign extension. The guest returned `0xFFFFFFFFAABBCC11`; the former expected value was `0x00000000AABBCC11`. The exact pinned MIPS64 helper explicitly casts the merged 32-bit result through `int32_t`, so the test vector was corrected to expect sign extension across the full 64-bit `gpr`. The helper implementation itself was not modified. Both run 47 and run 50 reached `PASS` with the corrected vectors.

The backing memory in the DOL is synthetic and bounded to a small test array. These runs validate only the explicitly enumerated memory helpers and vectors, not the complete N64 address space or original Racer code.

## Next gate — segmented N64 memory model

The ABI/memory-helper gate is now **PASS in Dolphin**, but this does not yet run original Racer code. The next engineering task is a bounded, host-testable memory adapter to replace the desktop runtime's contiguous 512 MiB RDRAM allocation and 4 GiB virtual reservation.

The adapter must:

1. translate N64 virtual addresses into checked, bounded backing regions instead of assuming `rdram + offset` is valid for the full 512 MiB range;
2. model the N64 cached/uncached aliases deliberately, with host tests for valid and invalid ranges;
3. route MMIO, PI and ROM reads through explicit callbacks rather than returning arbitrary pointers;
4. keep the original N64 virtual address semantics separate from host pointers;
5. provide a reverse mapping for heap pointers returned by `recomp_alloc`, because the upstream heap helper currently calculates an N64 address by subtracting the single contiguous RDRAM base;
6. keep Wii memory constraints explicit: 24 MiB MEM1 + 64 MiB MEM2 on Wii, not a hypothetical contiguous 512 MiB region.

Do not begin the full runtime or GX renderer until this memory adapter has host tests and a small PPC/Dolphin proof. The next adapter should preserve the pinned upstream behavior where possible, with every target-specific divergence covered by synthetic tests.
