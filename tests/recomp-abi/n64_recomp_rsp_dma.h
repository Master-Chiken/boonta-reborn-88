#ifndef BOONTA_TESTS_RECOMP_ABI_N64_RECOMP_RSP_DMA_H
#define BOONTA_TESTS_RECOMP_ABI_N64_RECOMP_RSP_DMA_H

/*
 * Reference adapter for moving RSP DMEM bytes through the opaque segmented
 * RDRAM context. This is deliberately separate from upstream rsp.hpp:
 *   - DMEM lane access uses the pinned RSP_MEM_BU accessor supplied by the
 *     caller's target-adapted test header;
 *   - RDRAM access uses checked n64_recomp_load_u8/store_u8 operations;
 *   - no host pointer arithmetic is performed on the opaque token.
 *
 * The address alignment, inclusive length and 4 KiB DMEM bounds match the
 * pinned N64ModernRuntime DMA helpers. Runtime integration remains pending.
 */
#include "n64_recomp_memory_api.h"

#ifndef RSP_MEM_BU
#error "Include the target-adapted pinned RSP DMEM accessor before this header"
#endif

static inline n64_segmented_result n64_recomp_rsp_dma_rdram_to_dmem(
    uint8_t *rdram_token,
    uint32_t dmem_address,
    uint32_t dram_address,
    uint32_t inclusive_length)
{
    uint32_t byte_count;
    uint32_t aligned_dram_address;

    if (inclusive_length == UINT32_MAX) {
        return N64_SEGMENTED_INVALID_ARGUMENT;
    }
    byte_count = inclusive_length + 1;
    if (dmem_address > UINT32_C(0x1000) ||
        byte_count > UINT32_C(0x1000) - dmem_address) {
        return N64_SEGMENTED_RANGE_CROSSES_REGION;
    }

    aligned_dram_address = dram_address & UINT32_C(0xFFFFF8);
    for (uint32_t i = 0; i < byte_count; ++i) {
        const uint32_t guest_address =
            UINT32_C(0x80000000) + aligned_dram_address + i;
        const uint64_t value = n64_recomp_load_u8(
            rdram_token, n64_segmented_sign_extend(guest_address));
        const n64_segmented_result result =
            n64_recomp_memory_last_error(rdram_token);

        if (result != N64_SEGMENTED_OK) {
            return result;
        }
        RSP_MEM_BU(i, dmem_address) = (uint8_t)value;
    }
    return N64_SEGMENTED_OK;
}

static inline n64_segmented_result n64_recomp_rsp_dma_dmem_to_rdram(
    uint8_t *rdram_token,
    uint32_t dmem_address,
    uint32_t dram_address,
    uint32_t inclusive_length)
{
    uint32_t byte_count;
    uint32_t aligned_dram_address;

    if (inclusive_length == UINT32_MAX) {
        return N64_SEGMENTED_INVALID_ARGUMENT;
    }
    byte_count = inclusive_length + 1;
    if (dmem_address > UINT32_C(0x1000) ||
        byte_count > UINT32_C(0x1000) - dmem_address) {
        return N64_SEGMENTED_RANGE_CROSSES_REGION;
    }

    aligned_dram_address = dram_address & UINT32_C(0xFFFFF8);
    for (uint32_t i = 0; i < byte_count; ++i) {
        const uint32_t guest_address =
            UINT32_C(0x80000000) + aligned_dram_address + i;
        const uint8_t value = RSP_MEM_BU(i, dmem_address);
        const n64_segmented_result result = n64_recomp_store_u8(
            rdram_token, n64_segmented_sign_extend(guest_address), value);

        if (result != N64_SEGMENTED_OK) {
            return result;
        }
    }
    return N64_SEGMENTED_OK;
}

#endif
