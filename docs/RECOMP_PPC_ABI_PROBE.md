# PowerPC ABI probe for the N64Recomp header

Date: 2026-11-25  
Status: the pinned header requires a clean-room 64x64-to-128 multiply fallback, target-endian scalar memory lanes and a big-endian FPR layout adapter for devkitPPC. **Host tests, GameCube/Wii cross-compilation, DOL linking, segmented-map and opaque-context execution, pinned RSP DMEM/RDRAM DMA helper checks, pinned `RSP::r128` accessors, FPR FR-mode checks and the separate opaque-context RSP DMA adapter all pass** in Dolphin workflow run [#45892145434](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45892145434). The validated probe code includes the opaque DMA adapter introduced on implementation commit `c9a2455708ef2089e9aa46c2f3516966b737caf9`; subsequent commits through `110fece47b8e4437f3d5d1c6a266a7ba28d4c743` update the audit/PR documentation only. GDB reached `probe_pass_marker`. This is bounded reference-adapter evidence only: the full upstream runtime and generated Racer code remain unmodified and unintegrated. No physical Wii, physical GameCube, full RSP task/microcode path, GX renderer, audio or controller integration has been validated.

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

## Segmented N64 address-space model — host and Dolphin proof

The direct-pointer audit is maintained separately in [`SEGMENTED_MEMORY_INTEGRATION_AUDIT.md`](SEGMENTED_MEMORY_INTEGRATION_AUDIT.md). It identifies the pinned runtime's contiguous `TO_PTR` conversion, heap base subtraction, and Racer-specific direct `rdram + offset` writes that still need migration.

The next adapter is now implemented as a standalone clean-room reference model in
`tests/recomp-abi/n64_segmented_memory.h`. It deliberately does **not** replace the
pinned upstream `MEM_*` macros yet.

### Logical layout represented

- `0x80000000–0x807fffff`: 8 MiB N64 RDRAM.
- `0x80800000–0x80ffffff`: 8 MiB runtime extension, used by the pinned runtime for PI handles at `0x80800000` and patch data beginning at `0x80801000`.
- `0x81000000`: beginning of mod RAM; the heap starts immediately after the mod data, matching pinned `librecomp::init_heap()`.
- KSEG1 `0xA0000000–0xA07fffff`: alias of the first 8 MiB of RDRAM only.
- MMIO is routed through an explicit callback (the current prototype uses a coarse `0xA3f00000–0xA4ffffff` window; production must refine this to device register ranges).
- Cartridge ROM at `0xB0000000` is read through a callback and is read-only.

Each RAM window has its own host pointer and explicit backing length. Production setup must provide the complete 8 MiB RDRAM and 8 MiB extension buffers. Smaller backing lengths are allowed only to run bounded adapter probes without allocating large static arrays in a GameCube DOL. Any access outside the supplied backing is rejected rather than falling through to another region or into host memory.

The model also separates the 32-bit N64 virtual address from host pointers. It validates canonical sign-extended guest addresses, checks all ranges and backing-buffer overlaps, routes ROM/MMIO through callbacks rather than fake pointers, and reverse-maps host allocations to canonical KSEG0 addresses. The reverse mapping is the operation needed to replace the pinned heap helper's current `host_pointer - rdram_base` assumption.

### Host test coverage

`tests/recomp-abi/test_n64_segmented_memory.c` passes under strict C11 warnings. It exercises:

- full logical 8 MiB RDRAM and 8 MiB extension windows, including end-of-region and crossing accesses;
- KSEG1 aliasing and rejection of its address immediately beyond the 8 MiB mirror;
- PI/patch extension addresses, mod RAM, and heap immediately after mod RAM;
- host-pointer-to-guest-address reverse mappings for all RAM-backed segments;
- noncanonical pointer rejection and unmapped/unsupported accesses;
- MMIO callback reads/writes and region-end checks;
- read-only ROM callback reads and ROM range failures;
- partial backing buffers, including the distinction between a valid logical window and an unbacked host range.

The same CI job also passes the pre-existing big-endian byte-layout tests, little-/big-endian lane-selector tests, the portable 64x64-to-128 multiply vectors, and four host tests for the Dolphin GDB RSP client.

### PowerPC execution under Dolphin

Workflow run [#59](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45685312494)  
Commit: `eea15a5d1733d933e6310f7591bbe110c015a614`

- Host tests: **passed**.
- Patched pinned N64Recomp header cross-compilation for GameCube and Wii: **passed**.
- Standalone GameCube DOL build, structural validation and GDB symbol extraction: **passed**.
- Dolphin 2512 GameCube emulation: **passed**.

GDB stopped at:
- `probe_start_marker`, PC `0x80003488` — DOL main-entry reached;
- `probe_pass_marker`, PC `0x8000349c` — both the original memory-helper vectors and the new segmented-map probe completed;
- `probe_fail_marker` was not reached.

The segmented PPC probe uses small but distinct backing buffers (4 KiB RDRAM, 8 KiB extended window, 256 bytes of mod RAM, and 512 bytes of heap) mapped at the real N64 guest base addresses. It executes the RDRAM and KSEG1 alias, extended PI/patch addresses, mod/heap boundary, reverse mapping, MMIO callback, ROM callback, and unbacked/noncanonical rejection paths. The host tests separately cover the complete 8 MiB logical boundaries. This is a proof of the current adapter's bounded mapping logic on big-endian PPC emulated by Dolphin; it is not a full 8 MiB physical-memory stress test.

### Opaque RDRAM token and typed access API — runs 65 and 66

The clean-room prototype `tests/recomp-abi/n64_recomp_memory_api.h` tests the proposed way to preserve the generated ABI `void(uint8_t* rdram, recomp_context* ctx)` while making the `rdram` value an opaque memory-context token rather than a pointer to a contiguous 512 MiB byte array.

The API currently includes:
- typed guest-address loads for signed/unsigned 8-, 16-, 32- and 64-bit values;
- typed 8-, 16-, 32- and 64-bit stores routed through the segmented map and MMIO callback;
- RAM-only `TO_PTR` equivalents requiring an object size, plus a separate one-byte `void*` form;
- host-to-guest reverse mapping in the underlying segmented model;
- a last-error value and optional fault callback.

Host run [#65](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45687258977) passed the opaque-token adapter tests. Dolphin run [#66](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45687846361) passed the same API exercised from the big-endian PPC DOL. It additionally verifies that the error state clears when a subsequent read/write succeeds after a previous rejected pointer/range operation.

GDB again stopped at `probe_start_marker` (PC `0x80003488`) then `probe_pass_marker` (PC `0x8000349c`); `probe_fail_marker` was not reached. The CI host also passed the little-/big-endian lane tests, segmented memory API tests, and GDB RSP unit tests; the pinned header cross-compiled for GameCube and Wii and the standalone DOL linked and validated.

**Important limit:** the opaque context is still a reference adapter only. Current upstream `TO_PTR`, heap, RSP, libultra and Racer callbacks continue to assume `rdram` is a real byte-array base. Do not pass the opaque token into the unmodified runtime.

### RSP DMEM scalar endian reference — run 86

The audit now includes `tests/recomp-abi/rsp_dmem_endian.h`, a clean-room reference for the 4 KiB RSP DMEM host-byte layout. It preserves the current little-endian word-swizzled layout and selects natural byte lanes on big-endian PowerPC. It tests signed/unsigned byte and halfword reads, word reads/writes, low-half stores, offsets and address wraparound.

Host tests and the same scalar DMEM vectors in the GameCube DOL both passed in workflow run [#86](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45689096458). Dolphin GDB stopped at `probe_start_marker` (PC `0x80003494`) and then `probe_pass_marker` (PC `0x800034a8`); `probe_fail_marker` was not reached.

### Pinned RSP::r128 accessors and FPR register layout — run 45892145434

The PPC DOL now compiles the exact `union RSP::r128` declaration and its `byte`, `element`, `u8`, `s16` and `u16` accessors extracted from pinned `N64ModernRuntime@63b808662fc8b604e09552f7c2c8cc7015e8313c`. The workflow fetches and verifies that exact commit, extracts the union into an ephemeral header, builds the probe at the target optimization level, and executes it on Dolphin's big-endian GameCube CPU. Reads and writes cover all byte and halfword lanes, including boundary indices, const and mutable accessors, and raw backing bytes. Run [#45892145434](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45892145434) reached `probe_start_marker` then `probe_pass_marker`; `probe_fail_marker` was not reached.

The standalone reference model's 16-bit accessors now use `memcpy` instead of type-punning `uint64_t[]` as `uint16_t[]`, so the `-O2` host/DOL checks do not rely on undefined strict-aliasing behavior. The extracted `RSP::r128` view types use GCC `may_alias` for 8/16-bit union access, matching the alias-safety requirement found in the public Wii runtime patch. The BE mapping uses natural logical indices; the LE model retains the upstream desktop reversed indexing. The DOL separately tests the extracted upstream accessor methods, so a pass is not solely a pass of the model.

The same target patcher now reverses the `fpr` union's float/word fields only on big-endian targets. PowerPC compile-time assertions verify `fh/u32h` at offset 0, `fl/u32l` at offset 4, and `d/u64` at offset 0. The DOL then reproduces the pinned runtime's two `f_odd` pointer configurations and exercises the generator-shaped `ctx->f_odd[(n - 1) * 2]` access:
- FR=0: odd F1 singles map to `f0.u32h`, leaving `f0.u32l` intact.
- FR=1: odd F1 singles map to `f1.u32l`, leaving `f1.u32h` intact.
- Full 64-bit and float bit views preserve the expected words.

These tests prove the selected ABI layout and scalar access paths only. They do not execute RSP vector instructions, establish vector-microcode semantics, or call the full runtime's `cop0_status_write`; the probe reproduces its exact documented `f_odd` pointer setup.

### Pinned RSP DMEM helpers and RDRAM DMA — run 45892145434

The workflow also extracts the exact scalar helper block and the two DMA helper definitions from pinned `N64ModernRuntime/librecomp/include/librecomp/rsp.hpp` at `63b808662fc8b604e09552f7c2c8cc7015e8313c`. The ephemeral test header applies the BE byte-lane adapter to `RSP_MEM_B/BU`, `RSP_MEM_W_LOAD/STORE`, `RSP_MEM_HU/H_LOAD` and `RSP_MEM_H_STORE`; it also includes the original `dma_rdram_to_dmem` and `dma_dmem_to_rdram` functions, which use the patched `recomp.h` `MEM_B` path for RDRAM.

The GameCube DOL checks direct signed/unsigned byte access, word and halfword loads/stores, sign extension, the 4 KiB DMEM wrap, then transfers four bytes in both directions using the original inclusive-length and 8-byte DRAM-address alignment behavior. Host tests, cross-compilation, DOL linking and Dolphin execution all passed. GDB reached `probe_start_marker` then `probe_pass_marker` in run [#45892145434](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45892145434).

This proves the extracted scalar helpers and DMA copy loops with bounded synthetic RDRAM/DMEM only. It does not validate `recomp::rsp::run_task`, the full RSP task lifecycle, IMEM/DMEM task loading, the opaque segmented-memory context in runtime DMA, RSP vector instruction semantics, or actual microcode execution.

### Opaque segmented-memory RSP DMA adapter — run 45892145434

A separate clean-room prototype, `tests/recomp-abi/n64_recomp_rsp_dma.h`, now connects the tested pinned `RSP_MEM_BU` DMEM accessor to the existing opaque `n64_recomp_memory_api.h`. Its RDRAM↔DMEM byte loops use `n64_recomp_load_u8` and `n64_recomp_store_u8`; the token is never treated as a host array. The loop preserves the pinned runtime's inclusive length and 8-byte DRAM alignment, checks the 4 KiB DMEM bounds, and propagates segmented-memory errors.

The Dolphin probe runs this adapter against the physically separate `segmented_rdram` backing used by `run_segmented_probe`. It verifies both transfer directions and the resulting bytes, then attempts a transfer beyond the backing buffer and checks that `N64_SEGMENTED_UNMAPPED_ADDRESS` is returned and retained as the handle's last error. Run [#45892145434](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45892145434) passed host tests, GameCube/Wii cross-compilation, DOL linking and Dolphin execution.

This is an integration prototype, not a patch to upstream `rsp.hpp` or `recomp::rsp::run_task`. It proves the copy algorithm can use the opaque handle safely; the real runtime task callback chain still needs to call it instead of its raw `MEM_B` pointer-lvalue DMA helpers.
### Still not integrated or proven

- The pinned upstream `recomp.h` still has its original direct pointer arithmetic. Generated Racer code does not yet call this segmented resolver.
- The direct-pointer audit is maintained in [`SEGMENTED_MEMORY_INTEGRATION_AUDIT.md`](SEGMENTED_MEMORY_INTEGRATION_AUDIT.md). It records the remaining `TO_PTR`, heap, mod-config, Racer SI/PI/VI, RSP DMA, SP dump, audio-buffer and thread/libultra consumers.
- `recomp_alloc/free` and mod-config string allocations must use the heap backing plus reverse map instead of subtracting a single contiguous host RDRAM base.
- The pinned `rsp.hpp` scalar `RSP_MEM_*` helpers and RDRAM↔DMEM DMA copy functions now have isolated PPC/Dolphin execution evidence, but they are not integrated with the segmented opaque-memory context or full `recomp::rsp::run_task`; migration of task loading, IMEM/DMEM source spans, debug dumps and microcode lifecycle remains open.
- The code generator must emit typed stores for `SW/SH/SB/SWC1/SD` and rewrite the unaligned store helpers. Pointer-lvalue `MEM_*` assignments cannot invoke MMIO callbacks.
- The MMIO callback is currently a test double, not a set of working SP/DP/MI/VI/AI/PI/SI device models.
- The ROM callback is currently a test fixture, not the Racer cartridge/PI DMA implementation.
- The `RSP::r128` scalar byte/halfword accessors are exercised from the pinned union declaration with BE lane and `may_alias` adapters. RSP VU state fields marked little-endian, vector instruction semantics, SIMD paths, and full RSP task/microcode execution remain untested.
- The 512 MiB logical KSEG0 window is not an allocation request. A Wii implementation must use bounded physical buffers in its real MEM1/MEM2 budget; it cannot assume a contiguous 512 MiB host region.
- No original Racer generated functions, scheduler, GX renderer, RSP microcode, audio, controller input, or physical Wii/GameCube hardware has been tested.

The next engineering gate is to integrate the resolver at the N64 memory-hook boundary and audit every helper that directly derives a host pointer from an N64 address. Keep the current reference tests as the acceptance contract. Do not start the GX renderer or full runtime bring-up until those call sites and the reverse heap mapping use the segmented memory context.
