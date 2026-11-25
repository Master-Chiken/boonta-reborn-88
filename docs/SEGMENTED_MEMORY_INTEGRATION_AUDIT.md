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

## Next validation gates

- [x] Host tests for the logical 8 MiB RDRAM / 8 MiB extension ranges, aliases, bounds, callbacks and reverse mapping.
- [x] PPC/Dolphin probe of bounded discontiguous RDRAM, extension, mod, heap, MMIO, ROM and reverse-mapping behavior.
- [ ] Add host/PPC tests for the RAM-only `TO_PTR` resolver rejection of MMIO/ROM (the resolver is now present; the latest CI run must confirm its added tests).
- [ ] Implement an opaque memory-context contract for runtime helpers while keeping generated code's ABI under review.
- [ ] Migrate generated scalar/unaligned stores to callback-capable typed writes.
- [ ] Port the heap and Racer-specific direct-access call sites.
- [ ] Add real PI/MMIO device models and integration tests.

No upstream repository has been modified. No Racer ROM, generated Racer source, assets, or other proprietary content is part of this audit.
