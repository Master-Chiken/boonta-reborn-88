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

This means a complete migration must cover the whole chain, not just change `RSP_MEM_B`:
- Resolve the guest `OSTask` address with a checked object-range lookup before dereferencing it.
- Replace the debug dump's raw 8 MiB indexing with a checked guest-memory copy; otherwise the opaque token would be read as an array.
- Preserve the opaque memory handle through `submit_rsp_task`, the `RDRAM_ARG` callback and `RspUcodeFunc` boundary.
- Replace the DMA helpers' `MEM_B` pointer-lvalue operations with a checked RDRAM-to-DMEM / DMEM-to-RDRAM range-copy interface that reports unmapped/MMIO access and handles region boundaries.
- Only after the source memory and task path is safe should the game RSP ucode be enabled; vector instruction and microcode semantics remain a separate validation gate.

The existing DOL proves only that the extracted scalar lanes and copy loops behave correctly on a bounded contiguous test buffer. It does not prove these APIs are integrated into the runtime, nor that `run_task` can safely consume an opaque handle.

**Remaining RSP gate:** the scalar `RSP_MEM_*` accessors and the two pinned RDRAM↔DMEM DMA helper functions now have isolated big-endian PPC/Dolphin test coverage. The extracted test copy applies natural BE lanes; the actual upstream runtime is not patched or integrated. Before enabling Racer RSP microcode, migrate task loading/DMA to checked memory-context spans, execute the full `run_task` setup and microcode path, and test vector instruction semantics plus VU state fields marked little-endian.

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
- [ ] Integrate the opaque context into the runtime helpers; do not pass it into current upstream code before the raw-pointer consumers listed above are migrated.
- [ ] Migrate generated scalar/unaligned stores to callback-capable typed writes.
- [ ] Port the heap and Racer-specific direct-access call sites.
- [x] Add a clean-room RSP DMEM scalar lane adapter with little-/big-endian host selection and host/PPC tests for 8/16/32-bit access, low-half stores and 4 KiB wrap (run [#86](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45689096458)).
- [x] Execute the pinned `rsp.hpp` `RSP_MEM_B/BU`, word/halfword load/store helpers plus original `dma_rdram_to_dmem` and `dma_dmem_to_rdram` definitions through the BE-adapted DOL copy; verify signed/unsigned scalar access, 4 KiB wrap, inclusive DMA lengths and both transfer directions on Dolphin (run [#45888134135](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45888134135)). This is bounded synthetic RDRAM/DMEM execution, not `run_task`, IMEM or microcode validation.
- [x] Verify pinned `RSP::r128.byte/element/u8/s16/u16` scalar accessor lanes on big-endian PowerPC using the exact extracted union methods with BE index and `may_alias` adapters in the Dolphin DOL (run [#45888134135](https://github.com/Master-Chicken/boonta-reborn-88/actions/runs/45888134135)). This does not validate vector instruction semantics, VU state fields marked little-endian, or SIMD paths.
- [x] Prototype and execute RDRAM↔DMEM DMA through the opaque segmented-memory token using checked byte operations, with alignment, inclusive length, bounds and unmapped-backing tests (run [#45891822170](https://github.com/Master-Chicken/boonta-reborn-88)). This is a test adapter only.
- [ ] Replace the real RSP microcode DMA and debug-dump raw-pointer paths with the checked adapter; the current opaque token must never be indexed as raw RDRAM.
- [ ] Add real PI/MMIO device models and integration tests.

No upstream repository has been modified. No Racer ROM, generated Racer source, assets, or other proprietary content is part of this audit.
