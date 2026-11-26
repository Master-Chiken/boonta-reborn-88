# Segmented memory integration audit

Date: 2026-11-25

This audit follows the host and Dolphin validation of the clean-room segmented address-space model in `tests/recomp-abi/n64_segmented_memory.h`. It records where the pinned runtime still assumes a single contiguous host `rdram` buffer and separates safe interception points from paths that bypass the memory macros.

## Source revisions inspected

- `dguillot-gh/N64Recomp` header: [`36286fb9a96f325a64b3c600131ba00af44654fc`](https://github.com/dguillot-gh/N64Recomp/blob/36286fb9a96f325a64b3c600131ba00af44654fc/include/recomp.h)
- `dguillot-gh/N64ModernRuntime`: [`63b808662fc8b604e09552f7c2c8cc7015e8313c`](https://github.com/dguillot-gh/N64ModernRuntime/tree/63b808662fc8b604e09552f7c2c8cc7015e8313c)
- `dguillot-gh/star-wars-racer-recomp`: [`68d3d2709cf71c07b5abed3627e01b03696cefd2`](https://github.com/dguillot-gh/star-wars-racer-recomp/tree/68d3d2709cf71c07b5abed3627e01b03696cefd2)

All observations below refer to these immutable revisions, not a moving branch.

## Confirmed contiguous-memory assumptions

### 1. libultra pointer conversion

[`ultramodern/include/ultramodern/ultra64.h`](https://github.com/dguillot-gh/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/include/ultramodern/ultra64.h#L23-L46) defines guest pointers as 32-bit integers and converts them using:

```c
#define PTR(x) int32_t
#define RDRAM_ARG uint8_t *rdram,
#define TO_PTR(type, var) ((type*)(&rdram[(uint64_t)var - 0xFFFFFFFF80000000]))
```

This is a direct base subtraction. It is used by the generic argument decoder in [`helpers.hpp`](https://github.com/dguillot-gh/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/include/librecomp/helpers.hpp#L9-L32), including pointer-typed arguments, and by libultra structures such as PI handles and thread/message-queue structures.

**Required change:** replace this conversion with a bounded guest-to-host lookup. The new `n64_segmented_host_pointer_for_guest()` helper now provides the reference behavior: it returns a pointer only when the complete range is inside one backed RAM segment; it refuses MMIO and ROM with `N64_SEGMENTED_NOT_RAM_BACKED`. Host tests and the Dolphin PPC probe now exercise this behavior. This helper is not wired into upstream `TO_PTR` yet.

### 2. Heap initialization and allocation

[`librecomp/src/heap.cpp`](https://github.com/dguillot-gh/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/heap.cpp#L9-L51):

- `get_heap()` uses `&rdram[heap_offset]`.
- `init_heap()` derives an offset from `0x80000000` and gives O1Heap the rest of the contiguous `recomp::mem_size` reservation.
- `recomp_alloc()` subtracts the same single `rdram` base from the host pointer to form the guest address.
- `recomp_free()` maps the guest pointer back through `TO_PTR`.

**Required change:** initialize the allocator on the dedicated heap backing buffer in the memory context. On allocation, reverse-map the returned host pointer to its N64 guest address. On free, use the checked guest-to-host mapper and reject pointers outside the heap allocation. Do not derive an offset by subtracting one RDRAM base.

### 3. Runtime reservation

[`librecomp/src/recomp.cpp`](https://github.com/dguillot-gh/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/recomp.cpp#L831-L850) reserves a 4 GiB virtual region and makes the first 512 MiB accessible. This is an implementation detail of the desktop runtime, not a Wii physical-memory budget. The Wii port must keep the 512 MiB guest logical window separate from the bounded MEM1/MEM2 buffers that actually back supported regions.

## Call sites already routed through the memory macros

These sites are structurally compatible with a future typed memory adapter, provided the generated load/store operations are changed where lvalue semantics currently bypass callbacks:

- Mod section loading, BSS clearing and MIPS relocation reads/writes in [`mods.cpp`](https://github.com/dguillot-gh/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/mods.cpp#L2241-L2285) use `MEM_B` and `MEM_W`.
- Patch payload writes in [`overlays.cpp`](https://github.com/dguillot-gh/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/overlays.cpp#L185-L188) use `MEM_B`.
- ROM DMA/PIO destination writes and save-buffer transfers in [`pi.cpp`](https://github.com/dguillot-gh/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/pi.cpp#L67-L88) use `MEM_B`. ROM source data is a host-side vector, so it does not need to be represented as a RAM pointer.

These paths can remain behind the N64 memory API once the memory macros are migrated to typed reads and writes. They should not be treated as proof that the memory abstraction is already integrated.

## Confirmed direct-memory bypasses in the Racer-specific layer

The pinned Racer app adds several direct accesses that bypass `MEM_*` and `TO_PTR`:

1. **Synthetic SI/PIF response:** [`src/main.cpp`](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/main.cpp#L94-L117) writes directly through `rdram + (addr - 0x80000000)` in `__osSiRawStartDma_recomp`.
2. **PI handle and libultra state setup:** [`on_game_init`](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/main.cpp#L582-L660) directly creates an `OSPiHandle*` at guest address `0x80800000`, uses `memset` on the resulting host pointer, writes N64 globals through a local `rdram + offset` lambda, and clears a VI-state block with `memset(rdram + offset, ...)`.
3. **Native boost-state query:** [JNI helper](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/main.cpp#L431-L444) reads game globals by directly adding `addr - 0x80000000` to a saved RDRAM host pointer.
4. **Crash address reporting:** [crash reporter](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/main.cpp#L740-L758) converts fault addresses back to guest addresses by subtracting the one saved `g_rdram_base`.

**Required change:** these platform and game callbacks must receive the memory context (or a narrow callback interface) and use bounded accessors. PI handle setup must request a RAM-backed host pointer for `0x80800000`; scalar global writes and SI data writes should use typed big-endian stores; block clearing should validate the whole range; crash reporting should use the reverse map rather than subtracting a single base. The native boost query must use the same accessor and stop assuming all guest addresses live in one host array.

## Critical macro/API design constraint

The pinned `recomp.h` has pointer-lvalue macros:

- `MEM_B/H/HU/BU/W(...)` expand to a host pointer dereference.
- `SD` calls the address hook once, then writes two raw 32-bit words through the returned pointer.
- `LD` reads two words through `MEM_W`.
- `do_swl/swr/sdl/sdr` use `MEM_W(...)=...` stores internally.

Returning a pointer from a hook is adequate for RAM-backed spans, but **cannot implement real MMIO callbacks**. A pointer-lvalue store cannot call a device callback at the moment of the write, and `SD` bypasses the scalar-width macros after obtaining its pointer. A scratch word is only a fallback sink; it is not PI/VI/AI/SI/SP/DP device behavior.

The production adapter therefore needs a coordinated change to the recompiled load/store surface, not just a replacement of `rdram_mmio_hook`:

1. Keep a fast RAM path for aligned and unaligned RAM-backed accesses, but route non-RAM reads and writes through typed device callbacks.
2. Change generated store operations and inline unaligned-store helpers to call explicit typed write helpers; preserve operation ordering and N64 big-endian semantics.
3. Make `SD` perform two checked 32-bit writes (or one checked 64-bit transaction when a device supports it); make `LD` perform checked reads.
4. Replace `TO_PTR` with the new RAM-only resolver for in-RAM structures. Non-RAM addresses must not become C pointers.
5. Change heap initialization/allocation/free to use the dedicated heap buffer and reverse mapping.
6. Update Racer-specific SI, PI-handle, VI-state, native boost and crash-reporting helpers to use the context API.
7. Audit every remaining helper that receives `uint8_t* rdram` or uses `RDRAM_ARG`; the list above covers the exact inspected call sites, not a claim that every file in the upstream runtime has been exhaustively rewritten.

## Concrete N64Recomp code-generation seam

The pinned C generator already separates memory loads from stores:

- `src/cgenerator.cpp` `setup_op()` maps `LW/LWU/LH/LHU/LB/LBU/LD` to value expressions such as `MEM_W`, `MEM_H`, `MEM_BU`, and `LD` ([lines 58–69](https://github.com/dguillot-gh/N64Recomp/blob/36286fb9a96f325a64b3c600131ba00af44654fc/src/cgenerator.cpp#L58-L69)).
- `CGenerator::process_store_op()` maps `SW/SH/SB/SWC1` to `StoreSyntax::Assignment`, which emits `MEM_W(...)=value`, `MEM_H(...)=value` or `MEM_B(...)=value`. It maps `SD/SDC1` to `SD(...)`, and `SWL/SWR/SDL/SDR` to helper calls that receive `rdram` ([lines 585–660](https://github.com/dguillot-gh/N64Recomp/blob/36286fb9a96f325a64b3c600131ba00af44654fc/src/cgenerator.cpp#L585-L660)).
- The store instruction classification is already centralized in `include/recompiler/operations.h` and `src/operations.cpp` ([operations.cpp](https://github.com/dguillot-gh/N64Recomp/blob/36286fb9a96f325a64b3c600131ba00af44654fc/src/operations.cpp#L182-L193)).

This is a tractable fork/patch point. The proposed change is to retain the existing load mappings as checked value-returning accessors, but make `process_store_op()` emit checked typed write calls instead of pointer-lvalue assignments:

| MIPS store | Current emission | Required typed emission |
|---|---|---|
| `SW` / `SWC1` | `MEM_W(offset, base) = value` | `n64_mem_write32(rdram, base + offset, value)` |
| `SH` | `MEM_H(offset, base) = value` | `n64_mem_write16(rdram, base + offset, value)` |
| `SB` | `MEM_B(offset, base) = value` | `n64_mem_write8(rdram, base + offset, value)` |
| `SD` / `SDC1` | `SD(value, offset, base)` | `n64_mem_write64(rdram, base + offset, value)` or two ordered 32-bit device writes |
| `SWL/SWR/SDL/SDR` | direct helper calls | helper implementations using checked read/modify/write operations |

The exact 64-bit device behavior must be defined per device: RAM can accept a big-endian 64-bit operation, while MMIO may require two ordered 32-bit writes or reject unsupported widths. It must not be implemented as an unchecked raw pointer store.

### Preserve the generated-function ABI without pretending the handle is RAM

Generated functions have the fixed signature `void(uint8_t* rdram, recomp_context* ctx)` in the pinned header. A practical migration can preserve that C ABI by treating the `rdram` argument as an **opaque pointer to a memory context**, not as the address of a contiguous byte array. Every consumer of that argument must then be audited:

- patched `MEM_*` and typed read/write helpers recover the context handle and resolve a guest address through the segmented map;
- `TO_PTR(type, guest)` uses the RAM-only resolver with a bounded object size; a `TO_PTR(void, guest)` specialization uses a one-byte validity check or a dedicated free-pointer lookup;
- `recomp_alloc/free` obtain the heap backing from the context and use host-to-guest reverse mapping;
- runtime thread, queue, PI, overlay, mod, save and Racer-specific helpers must stop treating the opaque argument as a raw `uint8_t[]`;
- no helper may perform `rdram + guest_offset` once the pointer becomes opaque.

This approach avoids changing every generated function signature at once, but it is safe only after the complete direct-access audit is implemented. Until then, the current code must continue to receive a real contiguous base pointer; do not pass a context object into the existing upstream runtime.

### Required helper migration

The current `do_swl/swr/sdl/sdr` helpers perform read/modify/write operations using `MEM_W` lvalues. They need to use value-returning reads and explicit writes, preserving the existing masks and sign-extension behavior. `SD` must stop obtaining one pointer and writing two raw words. Hand-written runtime stores in `mods.cpp`, `overlays.cpp`, and `pi.cpp` must be converted from `MEM_* = value` to the matching typed write API. Racer-specific `memset` and direct pointer writes identified above must use a checked bulk-fill or typed access function.

The reference model currently implements the translation and callback semantics, but not yet this production C API, the generator patch, a fault policy, or real PI/MMIO device models. Those remain separate engineering gates.

## Additional runtime consumers found in the pinned tree

The following files were inspected at the same immutable N64ModernRuntime revision after the first audit. These are further migration obligations; the previous list was not exhaustive.

### Mod configuration strings

`librecomp/src/mod_config_api.cpp`:
- `return_string()` calls `recomp::alloc(rdram, size)`, subtracts the returned host pointer from `rdram`, and adds the N64 base to synthesize a guest address.
- It copies the returned string through `MEM_B`.
- `recomp_free_config_string()` converts the guest pointer back into `rdram + offset` before calling `recomp::free`.

The pointer subtraction is invalid for an opaque context token. Use the allocator's host-to-guest reverse map, typed string writes (or a checked bulk write), and heap-only free validation.

### RSP DMEM scalar lane proof

The new reference adapter `tests/recomp-abi/rsp_dmem_endian.h` reproduces the current RSP DMEM scalar memory contract without modifying upstream. It separates the RSP's logical 4 KiB address from the host backing index:

- little-endian hosts use the current word-swizzled byte lane (`address ^ 3`);
- big-endian PowerPC hosts use the logical byte address unchanged;
- 16-bit host byte indices and the low-half store-source indices are selected independently, matching the current little-endian implementation's `(i + 2) ^ 3` operations.

Host run [#86](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45689096458) passed DMEM 8/16/32-bit reads/writes, signed byte and halfword extension, low-half writes, address offsets, all byte lanes and 4 KiB wraparound. Its host lane-selector test also compiled the forced big-endian selection branch.

The same DOL then executed the DMEM vectors on big-endian PowerPC in Dolphin. GDB stopped at `probe_start_marker` (PC `0x80003494`) then `probe_pass_marker` (PC `0x800034a8`); `probe_fail_marker` was not reached. This validates the clean-room DMEM scalar adapter under Dolphin, not the upstream RSP vector engine or any RSP microcode.

### Pinned RSP DMEM helpers and DMA copy loops — run 45888134135

The workflow now extracts the exact scalar helper block and the original `dma_rdram_to_dmem` / `dma_dmem_to_rdram` definitions from pinned `N64ModernRuntime/librecomp/include/librecomp/rsp.hpp` at `63b808662fc8b604e09552f7c2c8cc7015e8313c`. It applies the BE lane adapter only to the ephemeral extracted test header, and the original DMA helpers use the patched `recomp.h` `MEM_B` path for RDRAM.

The GameCube DOL checks `RSP_MEM_B/BU`, word and halfword load/store helpers, signed halfword extension, the `0xFFF → 0x000` wrap, and four-byte RDRAM↔DMEM transfers in both directions, including the original inclusive length and 8-byte DRAM alignment. Host tests, GameCube/Wii cross-compilation, DOL linking and Dolphin execution passed in run [#45888134135](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45888134135). The GDB harness reached `probe_pass_marker`.

This is still a bounded synthetic probe. It does not call `recomp::rsp::run_task`, load an `OSTask` end-to-end, migrate the opaque segmented-memory token into the runtime DMA path, execute vector instructions, or run the game's RSP microcode.

### Opaque segmented RDRAM DMA adapter — run 45891822170

The reference header `tests/recomp-abi/n64_recomp_rsp_dma.h` now adapts the pinned RSP DMEM byte accessor to the segmented memory API. Its RDRAM→DMEM path uses `n64_recomp_load_u8`; its DMEM→RDRAM path uses `n64_recomp_store_u8`. It never performs host pointer arithmetic on the opaque `uint8_t* rdram` token.

The Dolphin probe passes the token created by `run_segmented_probe` and uses the discontiguous `segmented_rdram` backing. It verifies both transfer directions, alignment to an 8-byte DRAM boundary, inclusive length, DMEM range rejection and an RDRAM read that crosses the physical backing boundary. The expected unmapped error is returned and recorded in the handle. Host tests, GameCube/Wii cross-compilation, DOL linking and Dolphin all pass in run [#45891822170](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45891822170).

This demonstrates a safe adapter contract, not an upstream runtime integration. The original `dma_rdram_to_dmem` / `dma_dmem_to_rdram` definitions still use `MEM_B` lvalue access and have only been separately tested on a contiguous synthetic RDRAM array. The runtime must replace or route those helpers through the checked adapter before the opaque token reaches `run_task`.

### RSP task loading, DMEM and IMEM

`librecomp/src/sp.cpp` and `librecomp/src/rsp.cpp` are a separate raw-memory path:
- `osSpTaskStartGo_recomp()` obtains `OSTask*` through `TO_PTR`, optionally dumps microcode by reading `rdram[i ^ 3]`, then calls `ultramodern::submit_rsp_task(rdram, task)`.
- `recomp::rsp::run_task()` copies the `OSTask` to the 4 KiB `dmem` array, then calls `dma_rdram_to_dmem(rdram, ...)` to copy microcode data into DMEM, and finally calls the recompiled RSP ucode with `rdram`.
- `librecomp/include/librecomp/rsp.hpp` defines DMA helpers that copy each byte through `MEM_B` lvalue reads/writes between RDRAM and DMEM.
- The same header defines `RSP_MEM_B/BU` with an unconditional `^ 3` lane transform, and constructs halfword/word operations by rearranging host byte addresses. `rsp_vu_impl.hpp` uses these primitives extensively for vector loads/stores.

The RSP adapter must read RDRAM via checked spans or a bounded copy API before the ucode is executed. The microcode dump must use the same path. It must not index the opaque token or assume all source bytes live in the first host buffer. DMEM/IMEM remain separate fixed-size RSP memory windows.

### Exact pinned RSP task call chain and opaque-memory blockers

Source inspection at `N64ModernRuntime@63b808662fc8b604e09552f7c2c8cc7015e8313c` confirms the call chain:

1. `librecomp/src/sp.cpp::osSpTaskStartGo_recomp(rdram, ctx)` obtains the `OSTask*` with `TO_PTR(OSTask, ctx->r4)`. Its optional `dump_frame` path reads an entire 8 MiB image using raw `rdram[i ^ 3]` byte indexing. It then calls `ultramodern::submit_rsp_task(rdram, ctx->r4)`.
2. `ultramodern/include/ultramodern/rsp.hpp` defines the callback as `bool(RDRAM_ARG const OSTask* task)`; `ultramodern/src/rsp.cpp::run_task` forwards the RDRAM argument and task pointer unchanged to the registered callback.
3. `librecomp/src/rsp.cpp::recomp::rsp::run_task(uint8_t* rdram, const OSTask* task)` copies the task into `dmem[0xFC0]`, calls `dma_rdram_to_dmem(rdram, 0x0000, task->t.ucode_data, 0xF80 - 1)`, then invokes `ucode_func(rdram, task->t.ucode)`.
4. The pinned `rsp.hpp` DMA functions use `MEM_B` lvalue reads/writes for the RDRAM side and `RSP_MEM_B` for DMEM. Their original loops have an isolated BE/Dolphin test on a bounded contiguous byte array (run #45888134135). A separate reference adapter now exercises both transfer directions through the opaque segmented-memory token and returns a checked error at the backing boundary (run #45891822170), but the upstream callback path has not yet been switched to it.

### Asynchronous OSTask ownership in the pinned event queue

The exact `ultramodern/src/events.cpp::submit_rsp_task` implementation resolves the guest address again with `TO_PTR(OSTask, task_)`. It then has two different ownership policies:
- `M_GFXTASK` is copied by value into `SpTaskAction{ *task }` and placed on the graphics action queue.
- Every other task is enqueued as the raw host pointer with `sp_task_queue.enqueue(task)`; the SP task thread dequeues that `OSTask*` later and calls `ultramodern::rsp::run_task`.

That non-graphics pointer can outlive the synchronous `osSpTaskStartGo_recomp` call and refers directly into the guest-RDRAM backing. A checked resolution at enqueue time does not by itself prove pointer lifetime or prevent the guest task record from being overwritten before dequeue. The queue migration should snapshot the `OSTask` by value (matching the existing graphics path) or store a guest address plus an explicit backing lease. The snapshot should preserve guest addresses for ucode/data buffers; those ranges are resolved/copied through the opaque memory API only when the worker consumes the task.

The new Dolphin `OSTask` test proves only synchronous object resolution and full-object bounds. It does not exercise the asynchronous queue lifetime. This remains a separate integration gate.

This means a complete migration must cover the whole chain, not just change `RSP_MEM_B`:
- Resolve the guest `OSTask` address with a checked object-range lookup before dereferencing it.
- Replace the debug dump's raw 8 MiB indexing with a checked guest-memory copy; otherwise the opaque token would be read as an array.
- Preserve the opaque memory handle through `submit_rsp_task`, the `RDRAM_ARG` callback and `RspUcodeFunc` boundary.
- Replace the DMA helpers' `MEM_B` pointer-lvalue operations with a checked RDRAM-to-DMEM / DMEM-to-RDRAM range-copy interface that reports unmapped/MMIO access and handles region boundaries.
- Only after the source memory and task path is safe should the game RSP ucode be enabled; vector instruction and microcode semantics remain a separate validation gate.

There are now two deliberately separate DOL proofs:

- The pinned-helper probe compiles the extracted original `rsp.hpp` scalar accessors and DMA functions against a bounded contiguous `uint8_t rdram[]` test buffer. This checks the original helper arithmetic and endian adaptation, not opaque-context support.
- The opaque-context probe uses `tests/recomp-abi/n64_recomp_rsp_dma.h` to implement equivalent RDRAM↔DMEM byte transfers with `n64_recomp_load_u8/store_u8` and the pinned BE-adapted `RSP_MEM_BU` accessor. `run_segmented_probe()` actually calls `run_opaque_rsp_dma_probe(rdram_token)` with separate backing arrays (4 KiB RDRAM, 8 KiB extension, mod RAM and heap). It verifies aligned DRAM address, inclusive length, both directions, DMEM end-boundary rejection, a RDRAM transfer that crosses from mapped to unmapped backing, error propagation and error clearing. Final run [#45892145434](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45892145434) reached GDB `probe_pass_marker`.

The second proof validates the adapter contract over a segmented memory context; it does not patch the pinned runtime or call its `recomp::rsp::run_task` / `ultramodern::submit_rsp_task` path. The original runtime still queues a raw `OSTask*` for non-graphics tasks and calls the original DMA helpers using `MEM_B` lvalue operations. The opaque adapter therefore remains a reference integration seam, not completed runtime migration.

**Remaining RSP gate:** the scalar `RSP_MEM_*` accessors and the two pinned RDRAM↔DMEM DMA helper functions now have isolated big-endian PPC/Dolphin test coverage. The extracted test copy applies natural BE lanes; the actual upstream runtime is not patched or integrated. Before enabling Racer RSP microcode, migrate task loading/DMA to checked memory-context spans, execute the full `run_task` setup and microcode path, and test vector instruction semantics plus VU state fields marked little-endian.

The shutdown path is part of this same change: `join_event_threads()` currently enqueues `nullptr` as the worker-exit sentinel, then joins the SP task thread. A value queue cannot preserve this sentinel as a null object pointer. Use an explicit queue item such as `SpTaskItem{kind = Task|Stop, task = ...}` (or `std::optional<OSTask>`) and enqueue `Stop` before joining. The task variant should own its copied `OSTask`; the address fields inside the structure remain N64 guest addresses and must be resolved when buffers are consumed.

### Checked guest byte spans and pinned OSTask resolution — run 45892729669

The opaque memory API now provides `n64_recomp_copy_from_guest` and `n64_recomp_copy_to_guest`. Each function resolves the complete byte range as RAM-backed before copying with `memmove`; it preserves byte order, rejects MMIO/ROM and rejects a range that crosses a backing-region boundary. Failures are written to the handle's error state with the guest address, copy length and access direction.

The Dolphin DOL verifies both copy directions with exact byte patterns, MMIO/ROM rejection, backing-boundary rejection and recorded error state. The probe also includes the exact `OSTask` layout from the pinned `ultramodern/ultra64.h`, writes a synthetic task into guest RDRAM, resolves it using `N64_RECOMP_TO_PTR(OSTask, token, address)`, verifies its fields, and rejects a task beginning at the final physically backed byte. Run [#45892729669](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45892729669) reached `probe_pass_marker`.

These tests give two directly reusable primitives for the real `osSpTaskStartGo_recomp` migration: bounded guest-object resolution and checked byte-span copies. They do not alter the upstream `TO_PTR` macro or prove every runtime object consumer has been migrated.
## RDRAM consumer lifetime inventory — pinned runtime

All source links below refer to the same immutable `N64ModernRuntime@63b808662fc8b604e09552f7c2c8cc7015e8313c` revision. This inventory separates short synchronous byte access from host pointers that escape the current call stack.

### 1. Raw-base ABI and guest-pointer conversion

[`ultra64.h`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/include/ultramodern/ultra64.h#L23-L43) defines the recomp ABI as `uint8_t* rdram` (`RDRAM_ARG`) and expands `TO_PTR(type, var)` into direct pointer arithmetic from that base. That is not a context handle: every function receiving the value can index it or turn a guest address into a host pointer without a checked region lookup.

[`helpers.hpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/include/librecomp/helpers.hpp#L8-L72) centralizes some conversions through `_arg<T*>`, but it still returns a raw `TO_PTR` pointer. `_arg_string` then scans with `MEM_B` until NUL without an explicit maximum length or a validated range. This should become a bounded guest-string copy (maximum bytes plus region/fault handling), not a returned pointer into guest RAM.

### 2. Host pointers that outlive a single operation

| Consumer | Pinned source behavior | Required migration |
|---|---|---|
| Thread scheduler | [`threads.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/src/threads.cpp#L149-L211) resolves guest `OSThread` addresses with `TO_PTR`; `thread_self` stores a guest pointer value and code uses resolved `OSThread*` around semaphore waits/resume. | Keep guest addresses/IDs in host scheduler state and resolve fields on each access, or hold an explicit pinned-span lease across the wait. Do not keep an unpinned pointer into movable/discontiguous backing. |
| RSP task queue | [`events.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/src/events.cpp#L45-L60) copies graphics `OSTask` values into `SpTaskAction`, but [the non-graphics queue stores `OSTask*`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/src/events.cpp#L182-L183). The task worker dequeues that pointer later and calls `rsp::run_task` ([lines 339–362](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/src/events.cpp#L339-L362)). | Queue an `OSTask` snapshot by value (as the graphics path already does); keep guest addresses for its buffers, and resolve/copy those ranges only when the task worker consumes them. The memory context must outlive the worker. |
| Renderer | The event system retains `events_context.rdram` and passes the raw base to `create_render_context` ([`events.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/src/events.cpp#L401-L406)); the callback interface accepts `uint8_t* rdram` ([`renderer_context.hpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/include/ultramodern/renderer_context.hpp#L98-L117)). | Replace the raw base with a long-lived memory-interface object. Renderer tasks should resolve framebuffer/display-list ranges through bounded read-only views or copy them into renderer-owned buffers; specify cache-coherency and lifetime explicitly. |
| Audio | [`audio.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/src/audio.cpp#L25-L35) calls `TO_PTR(int16_t, audio_data_)` then passes the pointer to `queue_samples`. The callback type is `void(int16_t*, size_t)` and has no stated copy/lifetime contract ([`ultramodern.hpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/include/ultramodern/ultramodern.hpp#L145-L158)). | Make the boundary copy audio samples into an owned queue packet, or define a strictly synchronous callback contract and enforce it in every platform backend. An asynchronous audio queue must not retain an unpinned guest-RAM pointer. |
| VI mode state | [`events.cpp::osViSetMode`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/ultramodern/src/events.cpp#L500-L505) converts the guest `OSViMode` address with `TO_PTR` and stores the resulting host `OSViMode*` in `ViState::mode`. The VI thread later dereferences that pointer in `ViState::update_vi()` while advancing the double-buffered VI state. | Store the guest `OSViMode` address in VI state and resolve/copy the complete structure through the checked memory API in the VI worker. A by-value snapshot is also possible only after confirming that callers do not mutate a mode structure after `osViSetMode`. Never retain the raw `TO_PTR` result in the long-lived VI state. |


**VI-specific validation gate:** test `osViSetMode` with a valid `OSViMode` in each supported RAM backing, reject an object that crosses a backing boundary, and verify the VI worker reads the same guest mode address after the double-buffered state transition. If the implementation chooses a value snapshot instead, add a compatibility test for mode-structure mutation after the call before accepting that semantic change.

### Additional raw-pointer lifetime across blocking waits

The previous table identifies the thread scheduler at a high level. Two more pinned runtime helpers have concrete local host pointers that survive a blocking wait and are then dereferenced:

- **Timer worker — `ultramodern/src/timer.cpp`:** `timer_thread()` stores the guest timer address and a timestamp snapshot in `ActiveTimer`, which is a good start. But it resolves `cur_timer_` to `OSTimer* cur_timer` before calling `timer_context.action_queue.wait_dequeue_timed(...)` (around lines 141–150). When the wait finishes, it reads `cur_timer->mq`, `cur_timer->msg` and `cur_timer->interval`, and may write `cur_timer->timestamp` (around lines 159–164). Keep the guest timer address across the wait and re-resolve the complete `OSTimer` range after waking, before reading or updating it. The timer object's guest-side lifetime must also be validated until expiry/cancellation.
- **Blocking message queues — `ultramodern/src/mesgqueue.cpp`:** `do_send()` and `do_recv()` resolve `OSMesgQueue* mq` before their blocking loops (around lines 94–108 and 134–145). A full/empty queue calls `run_next_thread_and_wait()`; after the scheduler resumes this guest thread, the functions continue to use the pre-wait `mq` pointer for queue fields and message-buffer access. Retain `mq_` as the guest address and re-resolve/revalidate the queue structure after every yield. Resolve the message buffer from its guest address for each checked operation; do not retain `OSMesgQueue*` or a message-buffer pointer across the wait.

**Required tests:** exercise a blocked send and a blocked receive with a scheduler yield between initial inspection and resumed access; test queue/message-buffer structures wholly inside a supported backing, crossing a backing boundary, and unmapped. For timers, wake the worker through an add/remove action while its timed wait is pending, then verify expiry and periodic reload use a fresh checked resolution. These tests validate pointer lifetime and bounds only; they do not establish exact N64 timing or device-interrupt parity.

### Guest thread queues, scheduler waits and controller structures

The guest-thread list is not a host-only container. In the pinned `ultramodern/src/threadqueue.cpp`, `queue_to_ptr()` returns a host pointer to either the native running-queue head or a guest-RAM `PTR(OSThread)` slot. The insert/pop/remove helpers then traverse `OSThread::next`, `OSThread::queue` and `OSThread::priority` through host pointers and pointer-to-pointer lvalues. A segmented-memory migration must keep the native running-queue head as native state, but represent every guest queue head/link as an N64 address and access each field through checked typed reads/writes. Do not return a host `PTR(OSThread)*` into guest backing.

There is also a separate **source-level queue-removal defect to test before porting**: in the pinned `thread_queue_remove()`, the loop advances the guest cursor `cur`, but reconstructs `cur_ptr` from the original `queue_` on each iteration rather than from `cur`. If the first entry is not the target and has a non-null successor, the loop appears to reread the original head indefinitely. Treat this as an observed code-path defect pending a minimal reproduction; do not silently fold a speculative correction into the memory-port patch. Add head, middle, tail, absent-target and single-entry removal tests, including a multi-node queue whose first node is not the target.

The pinned `threads.cpp::_thread_func()` resolves `OSThread* self` before the initial `wait_for_resumed()` and then reads `self->context` and `self->sp` after the wait. A checked resolver used only at function entry would leave this pointer-lifetime bug intact. Keep `self_` as a guest address and resolve the structure after the semaphore wait and before each later access. The creator side in `osCreateThread()` also retains `OSThread* t` across the initialization semaphore wait and should be re-resolved before its post-wait logging or state access. Scheduler host contexts/semaphores can remain native objects; the guest `OSThread` fields must not be cached as native pointers across waits.

The pinned `ultramodern/src/input.cpp` resolves the guest `OSContStatus[4]` array with `TO_PTR` in `osContInit()` and `osContGetQuery()`, then writes through native struct fields. This is synchronous, so it does not need a long-lived lease, but it still needs a checked four-element object range or field-level checked writes. Preserve libultra's exact partial-write behavior: for a disconnected controller the implementation updates `err_no` and intentionally leaves `type` and `status` untouched. A whole-array zero-fill/copy-out would change observable behavior. The `bitpattern` argument to `osContInit` is a host pointer supplied by the recomp wrapper, not the guest `data_` address; keep those two address domains distinct.

### Timer worker lifetime

In the pinned `ultramodern/src/timer.cpp`, `init_timers()` detaches the timer worker thread. There is no matching timer stop/join in this file, unlike the explicit event and thread-cleaner joins elsewhere. The memory context passed into that detached worker must therefore outlive every timer operation and cannot be freed/replaced merely because game execution or graphics shutdown has started. Before using a dynamically owned segmented context, add an explicit stop action and join, or prove and enforce process-lifetime ownership. This is independent of the need to re-resolve an `OSTimer` after its timed wait.

**Additional tests:** queue traversal and removal for head/middle/tail/absent entries; thread start/resume and destroy while suspended; controller status writes for connected and disconnected pads with guard bytes around the four-element array; and runtime shutdown with an active and an idle timer worker. These should be host unit tests first, then target-specific checks when a real Wii/GameCube build path is available.

### Downstream Racer backend behavior at the pinned project revision

The public runtime interfaces do not state callback pointer lifetimes. The pinned downstream project source at `star-wars-racer-recomp@68d3d2709cf71c07b5abed3627e01b03696cefd2` shows two different concrete behaviors:

- **Audio callback:** [`src/audio.cpp`](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/audio.cpp#L41-L65) reads the supplied `int16_t*` immediately and copies each sample pair into its own static `std::vector<int16_t>` before submitting that vector to SDL's queued-audio API. The callback does not store the caller's RDRAM pointer. This is a workable synchronous-copy contract to formalize at the runtime boundary; a future Wii audio backend should likewise copy samples into owned storage before returning.
- **RT64 renderer:** [`src/rt64_render_context.cpp`](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/rt64_render_context.cpp#L70-L100) stores `rdram_` for the renderer's full lifetime and assigns it to `RT64::Application::Core::RDRAM`. Its [`send_dl`](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/rt64_render_context.cpp#L208-L234) passes that same base to `processDisplayLists`; the debug [`dump_dl`](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/rt64_render_context.cpp#L238-L257) performs direct `rdram_ + a` reads. This backend therefore assumes one stable contiguous RDRAM base and is not directly compatible with an opaque/discontiguous handle. It is also an RT64/Vulkan/D3D12 HLE backend rather than a Wii GX renderer. The Wii renderer path needs its own display-list parser/command ownership and bounded guest-memory reads; merely changing the callback argument type is insufficient.

The audio and renderer paths should not be classified the same way: the former consumes/copies during the callback, while the latter deliberately retains the RDRAM base across the renderer lifetime.

A further graphics-queue nuance is important before changing ownership semantics. In pinned `events.cpp`, the graphics queue stores `SpTaskAction{ *task }` (an `OSTask` value), then the worker calls `sp_complete()` before `send_dl()` and `dp_complete()` after `send_dl()`. The source comment explicitly says games usually preserve RSP inputs until RDP completion. Thus, the graphics task record itself is already snapshotted; its referenced guest display-list/texture/framebuffer ranges remain guest addresses and must be read through a valid renderer memory interface until the backend has consumed them. The non-graphics RSP queue is different: it stores an unowned `OSTask*` and should be converted to a by-value task item with an explicit stop variant.

### 3. Contiguous allocator and reverse mapping assumptions

[`heap.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/heap.cpp#L7-L50) places `O1HeapInstance` at `&rdram[heap_offset]`, initializes O1Heap over the remaining contiguous RDRAM tail, returns a native pointer from `alloc`, and derives guest addresses by subtracting the RDRAM base. [`mod_config_api.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/mod_config_api.cpp#L38-L75) repeats the pointer-subtraction pattern for returned strings and reconstructs a host pointer for free.

A segmented implementation must choose one of two explicit designs:
- Keep the guest heap inside a stable contiguous RDRAM arena, with a guest-address allocator and bounds checks; or
- Make allocations return guest virtual addresses/handles and maintain a checked reverse map from guest allocation to backing storage. Free must validate the allocation identity; it must not subtract an opaque token or trust an arbitrary guest pointer.

The current O1Heap metadata and allocation headers must remain address-stable for the full lifetime of each allocation.

### 4. Synchronous consumers that can use checked copies

These paths copy or consume data before returning, so they should migrate to `copy_from_guest`, `copy_to_guest`, or typed scalar accessors rather than taking persistent host pointers:

- ROM/PI PIO loops in [`pi.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/pi.cpp#L67-L88).
- Save transfer loops: [`save_write`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/pi.cpp#L232-L247) copies guest data into the native save buffer before it signals the asynchronous disk writer; [`save_read`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/pi.cpp#L249-L260) copies in the other direction synchronously.
- Flash page writes copy guest bytes into the fixed `write_buffer` before queueing completion; Flash reads write from save storage synchronously ([`flash.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/flash.cpp#L140-L199)).
- Debug printing copies bytes into `to_print` before `fwrite` ([`print.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/print.cpp#L32-L45)).
- Mod sections/relocations and overlay patch data are written synchronously through `MEM_B/MEM_W` in [`mods.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/mods.cpp#L2241-L2291) and [`overlays.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/overlays.cpp#L185-L188).

These are good early migration targets once the typed API exists. They still need explicit range checks, correct endian widths, MMIO rejection/dispatch, and fault propagation.

### 5. Memory-window reservation

[`recomp.cpp`](https://github.com/N64Recomp/N64ModernRuntime/blob/63b808662fc8b604e09552f7c2c8cc7015e8313c/librecomp/src/recomp.cpp#L831-L856) reserves a large virtual address window, commits/protects `mem_size`, and relies on direct base-plus-offset addressing and protected pages to catch invalid accesses. A Wii implementation cannot assume desktop `mmap`/`VirtualAlloc` semantics. The target needs bounded MEM1/MEM2 backing, explicit guest-region translation, and distinct MMIO/ROM/invalid outcomes. The logical 512 MiB N64 KSEG0 range is not a request to allocate 512 MiB of physical memory.

### Migration order derived from this inventory

1. Establish the long-lived memory context and checked RAM/MMIO/ROM region classification, with read/write/copy operations and fault reporting.
2. Change generated `MEM_*` and unaligned load/store helpers from pointer-lvalue expressions to typed calls; this is necessary for region crossing and MMIO side effects.
3. Convert short synchronous readers/writers first: debug print, save/flash transfers, PI PIO/DMA, mod/overlay writes, and bounded strings.
4. Introduce a safe guest-object API: either a short-lived pinned lease with explicit ownership or copy-in/copy-out structures. Ban raw `TO_PTR` from escaping into queues or across waits.
5. Migrate heap allocation and free to stable guest addresses with validated reverse mapping.
6. Replace asynchronous interfaces (RSP task queue, renderer, audio, thread scheduler) with owned snapshots, guest addresses resolved at consumption time, or explicit reference-counted leases.
7. Only then port PI/MMIO device models, RSP task/IMEM/DMEM loading, microcode, GX and game-level execution.

## Wii GX architecture reference: DKR-R-WII

A separate Wii recompiler port, [`DKR-R-WII@0d8dc9c65563f3c7548f25a2fc73366043bfe94e`](https://github.com/Ch1nguya/DKR-R-WII/tree/0d8dc9c65563f3c7548f25a2fc73366043bfe94e), provides a useful architecture comparison, not a renderer to transplant unchanged:

- [`null_renderer.cpp`](https://github.com/Ch1nguya/DKR-R-WII/blob/0d8dc9c65563f3c7548f25a2fc73366043bfe94e/runtime-recomp/src/game/null_renderer.cpp#L70-L168) initializes the GX FIFO, GX viewport/scissor, vertex descriptors, TEV defaults and then includes the Wii renderer modules.
- [`wii_renderer_dlparse.inc`](https://github.com/Ch1nguya/DKR-R-WII/blob/0d8dc9c65563f3c7548f25a2fc73366043bfe94e/runtime-recomp/src/game/wii_renderer_dlparse.inc) implements a title-specific display-list parser with per-opcode handlers. It decodes N64 RDRAM data into GX state and geometry rather than asking RT64 to interpret the list.
- [`wii_renderer_geometry.inc`](https://github.com/Ch1nguya/DKR-R-WII/blob/0d8dc9c65563f3c7548f25a2fc73366043bfe94e/runtime-recomp/src/game/wii_renderer_geometry.inc) batches GX triangles and subdivides projected N64 geometry to improve perspective-correct texture appearance.
- [`wii_renderer_rdp_state.inc`](https://github.com/Ch1nguya/DKR-R-WII/blob/0d8dc9c65563f3c7548f25a2fc73366043bfe94e/runtime-recomp/src/game/wii_renderer_rdp_state.inc) tracks emulated RDP state and reads big-endian values from guest RDRAM. [`wii_textures.inc`](https://github.com/Ch1nguya/DKR-R-WII/blob/0d8dc9c65563f3c7548f25a2fc73366043bfe94e/runtime-recomp/src/game/wii_textures.inc) handles N64 texture memory/decoding and maps the color combiner to GX TEV stages.
- Its pinned Wii runtime patch explicitly avoids an 8 MiB snapshot per GFX task on GEKKO, because it measured that copy as too expensive. The graphics worker parses the live RDRAM-backed display list first, then sends SP completion and DP completion; the patch inserts a short delay between those completion edges. On non-GEKKO builds it instead snapshots 8 MiB per accepted graphics task and passes that immutable buffer to `send_dl`. This is a concrete alternative to always copying full RDRAM, but it depends on strict producer/consumer ordering and a stable contiguous backing.
- The same patch's `TO_PTR` for GEKKO uses the low 24-bit physical offset, and its `recomp::start` allocates a 16 MiB buffer for RDRAM plus the extended area. This illustrates a compact contiguous-memory strategy for that title.

**Memory-layout caveat before reusing the 16 MiB strategy:** the public Wii patch changes the GEKKO allocation to 16 MiB and adds a 24-bit physical-address mask to `TO_PTR`, but its visible `addresses.hpp` hunk changes integer types only; it does not show a reduced heap size or a relocated `mod_rdram_start`. In the separate N64ModernRuntime snapshot pinned by this audit (`63b808662fc8b604e09552f7c2c8cc7015e8313c`), the values are `mem_size = 512 MiB` and `mod_rdram_start = 0x81000000`; `init_heap()` derives `heap_offset = address - 0x80000000` and `heap_size = mem_size - heap_offset`. Applied literally, that would put the default heap start at offset 16 MiB and advertise a 496 MiB heap, which is not bounded by the 16 MiB allocation.

This is an **unresolved comparison, not proof of a bug in the DKR-R-WII binary**: the public DKR-R-WII tree at this revision has no `.gitmodules` file or gitlink for N64ModernRuntime, while its dependency patch script expects a `patches/manifest.json` that is not present in the published tree. The exact external runtime checkout used to build its release therefore cannot be independently established from this repository snapshot. Before copying the 16 MiB design, obtain the actual dependency checkout and confirm where `init_heap`, mod storage, PI handles and all RDRAM accesses are bounded.

For Star Wars Racer, the transferable lesson is the **GX pipeline shape** (display-list decode → N64 RDP state/texture emulation → GX TEV and geometry), not DKR's opcode handlers, texture assumptions, audio mixer, or task schedule. Racer's own GBI/microcode, display-list command set, texture formats, memory footprint and SP/DP completion contract must be audited before choosing either live-RDRAM synchronization or per-task snapshots.

## Star Wars Racer graphics/audio split versus DKR's GX renderer

The pinned public Racer runtime source at `star-wars-racer-recomp@68d3d2709cf71c07b5abed3627e01b03696cefd2` shows a different graphics/audio split from DKR:

- [`src/main.cpp`](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/main.cpp#L254-L281) says the RSP microcode callback is only reached for non-graphics tasks. It registers the audio `aspMain` ucode at `0x80099450`, recompiled by RSPRecomp from `aspMain.toml` into `rsp/aspMain.cpp`; unknown non-graphics ucode falls back to a no-op. Graphics tasks are routed to the renderer instead of running through this RSP callback.
- [`src/rt64_render_context.cpp`](https://github.com/dguillot-gh/star-wars-racer-recomp/blob/68d3d2709cf71c07b5abed3627e01b03696cefd2/src/rt64_render_context.cpp#L208-L234) passes the task's `ucode`, `ucode_data` and `data_ptr` to RT64: it loads the GBI with `loadUCodeGBI(ucode, ucode_data, true)`, resets RT64's HLE RSP state, then processes the display list from RDRAM. Its debug dump uses common F3DEX2 opcode names, but the runtime dynamically provides the ucode addresses to RT64; do not assume every Racer task uses the same static command table without checking the selected GBI.
- The same file documents RT64 as a Vulkan/D3D12 HLE renderer. This is the desktop graphics path that must be replaced by a Wii GX path; changing only the callback signature or endian lane helpers does not port it.

This changes the renderer-port estimate: DKR's `wii_renderer_dlparse.inc` is specifically a F3DDKR display-list implementation. It is useful as a GX technique reference (RDP state, N64 texture memory, TEV, geometry subdivision), but not as the command parser for Racer. A Racer GX renderer must implement the actual GBI that its RT64 setup selects from the Racer ucode task fields, preserve RT64-equivalent state/combiner behavior, and read all vertex/texture/display-list ranges through the runtime's memory-lifetime contract.

The audio path is a separate decision. Racer's current desktop setup reuses recompiled `aspMain`; DKR instead advertises a native PowerPC audio mixer replacing its sound microcode. For Racer, keep the RSPRecomp audio path only after full audio RSP instruction/DMEM/DMA semantics and output parity are verified, or qualify a native mixer as a separate project. The current scalar `RSP::r128`/DMEM tests do not validate `aspMain` execution.

### libultra / controller / flash helpers

- `librecomp/src/cont.cpp` resolves message queues, controller status and pad structures through `_arg<T*>`/ `TO_PTR`, and writes controller results through `MEM_H/MEM_B`. This should work with the RAM-only object resolver plus typed writes after the libultra structure helpers are migrated.
- `librecomp/src/flash.cpp` resolves `OSIoMesg*` through `TO_PTR`, reads/writes guest buffers through `MEM_B`, and forwards `rdram` to save read/write routines. Those save helpers need a context-aware range copy API and must not retain a raw byte-array assumption.
- `librecomp/src/ai.cpp` passes `rdram` and guest addresses to `ultramodern::queue_audio_buffer()`. That function and any deferred audio consumer must be checked to ensure it copies guest bytes while the memory context is valid, rather than retaining an opaque handle as a raw array.
- `librecomp/src/vi.cpp` forwards the memory argument to VI helpers. Their implementation and framebuffer pointer handling must use checked guest-to-host conversion where the framebuffer lies in RDRAM; device state itself must not be a raw MMIO pointer.

The current inspection is a targeted static audit of the named files, not a complete proof that every `rdram` consumer in all upstream translation units has been enumerated.

## Next validation gates

- [x] Host tests for the logical 8 MiB RDRAM / 8 MiB extension ranges, aliases, bounds, callbacks and reverse mapping.
- [x] PPC/Dolphin probe of bounded discontiguous RDRAM, extension, mod, heap, MMIO, ROM and reverse-mapping behavior (run #59).
- [x] Host tests for the RAM-only `TO_PTR` replacement and opaque memory API: RDRAM, KSEG1, extension, mod and heap produce host pointers; MMIO/ROM are refused; typed scalar loads/stores and bounds/errors are checked. Error state clears after the next successful read/write.
- [x] Dolphin PPC execution of the opaque `uint8_t* rdram` context token, typed read/write API, RAM-only `TO_PTR` adapter and success-after-error recovery, alongside the segmented mapping tests (run [#65](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45687258977) and [#66](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/45687846361)).
- [x] Add checked raw-byte span copies from/to the opaque token and verify both directions, MMIO/ROM refusal, backing-boundary rejection and error state. The same DOL resolves the exact pinned `OSTask` layout using `N64_RECOMP_TO_PTR`, verifies its fields and rejects an object crossing the backing boundary (run [#45892729669](https://github.com/Master-Chicken/boonta-reborn-88)).
- [ ] Integrate the opaque context into the runtime helpers; do not pass it into current upstream code before the raw-pointer consumers listed above are migrated.
- [ ] Migrate generated scalar/unaligned stores to callback-capable typed writes.
- [ ] Port the heap and Racer-specific direct-access call sites.
- [x] Add a clean-room RSP DMEM scalar lane adapter with little-/big-endian host selection and host/PPC tests for 8/16/32-bit access, low-half stores and 4 KiB wrap (run [#86](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45689096458)).
- [x] Execute the pinned `rsp.hpp` `RSP_MEM_B/BU`, word/halfword load/store helpers plus original `dma_rdram_to_dmem` and `dma_dmem_to_rdram` definitions through the BE-adapted DOL copy; verify signed/unsigned scalar access, 4 KiB wrap, inclusive DMA lengths and both transfer directions on Dolphin (run [#45888134135](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45888134135)). This is bounded synthetic RDRAM/DMEM execution, not `run_task`, IMEM or microcode validation.
- [x] Exercise the separate opaque-context DMA bridge `n64_recomp_rsp_dma.h` from `run_segmented_probe()` with non-contiguous RDRAM/extension/mod/heap backing; verify both transfer directions, alignment/inclusive length, DMEM bounds, mapped-to-unmapped RDRAM failure, error propagation and clearing (Dolphin run [#45892145434](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45892145434)). This validates the adapter seam only; the upstream `rsp.hpp`/`run_task` call chain remains unmodified.
- [x] Verify pinned `RSP::r128.byte/element/u8/s16/u16` scalar accessor lanes on big-endian PowerPC using the exact extracted union methods with BE index and `may_alias` adapters in the Dolphin DOL (run [#45888134135](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45888134135)). This does not validate vector instruction semantics, VU state fields marked little-endian, or SIMD paths.

- [ ] Replace the real RSP microcode DMA and debug-dump raw-pointer paths with the checked adapter; the current opaque token must never be indexed as raw RDRAM.
- [ ] Add real PI/MMIO device models and integration tests.

No upstream repository has been modified. No Racer ROM, generated Racer source, assets, or other proprietary content is part of this audit.
