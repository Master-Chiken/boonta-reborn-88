#ifndef BOONTA_TESTS_RECOMP_ABI_RSP_DMEM_ENDIAN_H
#define BOONTA_TESTS_RECOMP_ABI_RSP_DMEM_ENDIAN_H

/*
 * Clean-room RSP DMEM byte-lane reference adapter.
 *
 * The pinned RSP implementation stores DMEM in host-word-swizzled order on
 * little-endian hosts and uses RSP_MEM_* helpers that assume that layout.
 * Broadway/GameCube/Wii PowerPC is big-endian, so byte lanes must remain
 * natural there. This adapter keeps the architectural RSP address separate
 * from the host backing index.
 *
 * It is a test/reference layer; upstream librecomp/rsp.hpp is not modified.
 */

#include <stddef.h>
#include <stdint.h>

#define N64_RSP_DMEM_SIZE UINT32_C(0x1000)
#define N64_RSP_DMEM_MASK (N64_RSP_DMEM_SIZE - 1)

#if defined(N64_RSP_FORCE_BIG_ENDIAN_FOR_TEST)
#define N64_RSP_DMEM_HOST_BIG_ENDIAN 1
#elif defined(__BYTE_ORDER__) && defined(__ORDER_BIG_ENDIAN__) && \
      (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN__)
#define N64_RSP_DMEM_HOST_BIG_ENDIAN 1
#else
#define N64_RSP_DMEM_HOST_BIG_ENDIAN 0
#endif

static inline uint32_t n64_rsp_dmem_host_byte_index(uint32_t logical_address)
{
    uint32_t address = logical_address & N64_RSP_DMEM_MASK;
#if N64_RSP_DMEM_HOST_BIG_ENDIAN
    return address;
#else
    return address ^ UINT32_C(3);
#endif
}

static inline uint32_t n64_rsp_dmem_host_word_byte_index(uint32_t byte)
{
#if N64_RSP_DMEM_HOST_BIG_ENDIAN
    return byte & UINT32_C(3);
#else
    return (byte & UINT32_C(3)) ^ UINT32_C(3);
#endif
}

/* Native byte index of the two bytes in an architectural halfword load. */
static inline uint32_t n64_rsp_dmem_host_half_load_byte_index(uint32_t byte)
{
#if N64_RSP_DMEM_HOST_BIG_ENDIAN
    return byte & UINT32_C(1);
#else
    return (byte & UINT32_C(1)) ^ UINT32_C(1);
#endif
}

/* Native byte index of the low 16 bits of a uint32_t store source. */
static inline uint32_t n64_rsp_dmem_host_half_store_byte_index(uint32_t byte)
{
#if N64_RSP_DMEM_HOST_BIG_ENDIAN
    return (byte & UINT32_C(1)) + UINT32_C(2);
#else
    return ((byte & UINT32_C(1)) + UINT32_C(2)) ^ UINT32_C(3);
#endif
}

static inline uint8_t n64_rsp_dmem_load_u8(
    const uint8_t dmem[N64_RSP_DMEM_SIZE],
    uint32_t offset,
    uint32_t address)
{
    return dmem[n64_rsp_dmem_host_byte_index(offset + address)];
}

static inline int8_t n64_rsp_dmem_load_s8(
    const uint8_t dmem[N64_RSP_DMEM_SIZE],
    uint32_t offset,
    uint32_t address)
{
    return (int8_t)n64_rsp_dmem_load_u8(dmem, offset, address);
}

static inline void n64_rsp_dmem_store_u8(
    uint8_t dmem[N64_RSP_DMEM_SIZE],
    uint32_t offset,
    uint32_t address,
    uint8_t value)
{
    dmem[n64_rsp_dmem_host_byte_index(offset + address)] = value;
}

static inline uint16_t n64_rsp_dmem_load_u16(
    const uint8_t dmem[N64_RSP_DMEM_SIZE],
    uint32_t offset,
    uint32_t address)
{
    uint16_t value;
    uint8_t *bytes = (uint8_t *)&value;
    uint32_t i;

    for (i = 0; i < 2; ++i) {
        bytes[n64_rsp_dmem_host_half_load_byte_index(i)] =
            n64_rsp_dmem_load_u8(dmem, offset + i, address);
    }
    return value;
}

static inline int32_t n64_rsp_dmem_load_s16(
    const uint8_t dmem[N64_RSP_DMEM_SIZE],
    uint32_t offset,
    uint32_t address)
{
    return (int32_t)(int16_t)n64_rsp_dmem_load_u16(dmem, offset, address);
}

/* Mirrors RSP_MEM_H_STORE: val's low 16 bits are stored big-endian. */
static inline void n64_rsp_dmem_store_u16_low(
    uint8_t dmem[N64_RSP_DMEM_SIZE],
    uint32_t offset,
    uint32_t address,
    uint32_t value)
{
    const uint8_t *bytes = (const uint8_t *)&value;
    uint32_t i;

    for (i = 0; i < 2; ++i) {
        n64_rsp_dmem_store_u8(
            dmem, offset + i, address,
            bytes[n64_rsp_dmem_host_half_store_byte_index(i)]);
    }
}

static inline uint32_t n64_rsp_dmem_load_u32(
    const uint8_t dmem[N64_RSP_DMEM_SIZE],
    uint32_t offset,
    uint32_t address)
{
    uint32_t value;
    uint8_t *bytes = (uint8_t *)&value;
    uint32_t i;

    for (i = 0; i < 4; ++i) {
        bytes[n64_rsp_dmem_host_word_byte_index(i)] =
            n64_rsp_dmem_load_u8(dmem, offset + i, address);
    }
    return value;
}

static inline void n64_rsp_dmem_store_u32(
    uint8_t dmem[N64_RSP_DMEM_SIZE],
    uint32_t offset,
    uint32_t address,
    uint32_t value)
{
    const uint8_t *bytes = (const uint8_t *)&value;
    uint32_t i;

    for (i = 0; i < 4; ++i) {
        n64_rsp_dmem_store_u8(
            dmem, offset + i, address,
            bytes[n64_rsp_dmem_host_word_byte_index(i)]);
    }
}

#endif
