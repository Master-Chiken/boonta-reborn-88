#ifndef BOONTA_TESTS_RECOMP_ABI_RSP_VECTOR_REGISTER_ENDIAN_H
#define BOONTA_TESTS_RECOMP_ABI_RSP_VECTOR_REGISTER_ENDIAN_H

/*
 * Clean-room reference for the pinned N64ModernRuntime RSP::r128 scalar
 * register accessors.
 *
 * The upstream SISD accessors reverse the raw 16-byte / 8-halfword arrays:
 *   byte(index)   -> raw[15 - index]
 *   element(index)-> raw[7 - index]
 * This is the little-endian host representation used by the desktop runtime.
 *
 * For a big-endian host, the two uint64_t words keep their numeric identity,
 * but each word's byte representation is reversed relative to LE. The
 * architectural high 64-bit half is u128[1], and the low 64-bit half is
 * u128[0]. Therefore logical lanes 0..7 live in the BE memory bytes of
 * u128[1] (raw offsets 8..15), and lanes 8..15 in u128[0] (raw 0..7).
 *
 * This reference is intentionally separate from upstream rsp_vu.hpp.
 */

#include <stdint.h>
#include <stddef.h>
#include <string.h>

#if defined(N64_RSP_VECTOR_FORCE_BIG_ENDIAN_FOR_TEST)
#define N64_RSP_VECTOR_HOST_BIG_ENDIAN 1
#elif defined(__BYTE_ORDER__) && defined(__ORDER_BIG_ENDIAN__) && \
      (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN__)
#define N64_RSP_VECTOR_HOST_BIG_ENDIAN 1
#else
#define N64_RSP_VECTOR_HOST_BIG_ENDIAN 0
#endif

static inline uint32_t n64_rsp_vector_byte_storage_index(uint32_t logical_index)
{
    uint32_t index = logical_index & UINT32_C(15);
#if N64_RSP_VECTOR_HOST_BIG_ENDIAN
    return (index + UINT32_C(8)) & UINT32_C(15);
#else
    return UINT32_C(15) - index;
#endif
}

static inline uint32_t n64_rsp_vector_half_storage_index(uint32_t logical_index)
{
    uint32_t index = logical_index & UINT32_C(7);
#if N64_RSP_VECTOR_HOST_BIG_ENDIAN
    return (index + UINT32_C(4)) & UINT32_C(7);
#else
    return UINT32_C(7) - index;
#endif
}

static inline uint8_t n64_rsp_vector_load_u8(
    const uint64_t words[2], uint32_t logical_index)
{
    const uint8_t *raw = (const uint8_t *)words;
    return raw[n64_rsp_vector_byte_storage_index(logical_index)];
}

static inline void n64_rsp_vector_store_u8(
    uint64_t words[2], uint32_t logical_index, uint8_t value)
{
    uint8_t *raw = (uint8_t *)words;
    raw[n64_rsp_vector_byte_storage_index(logical_index)] = value;
}

static inline uint16_t n64_rsp_vector_load_u16(
    const uint64_t words[2], uint32_t logical_index)
{
    const uint8_t *raw = (const uint8_t *)words;
    const size_t byte_offset =
        (size_t)n64_rsp_vector_half_storage_index(logical_index) * sizeof(uint16_t);
    uint16_t value;
    memcpy(&value, raw + byte_offset, sizeof(value));
    return value;
}

static inline int16_t n64_rsp_vector_load_s16(
    const uint64_t words[2], uint32_t logical_index)
{
    return (int16_t)n64_rsp_vector_load_u16(words, logical_index);
}

static inline void n64_rsp_vector_store_u16(
    uint64_t words[2], uint32_t logical_index, uint16_t value)
{
    uint8_t *raw = (uint8_t *)words;
    const size_t byte_offset =
        (size_t)n64_rsp_vector_half_storage_index(logical_index) * sizeof(uint16_t);
    memcpy(raw + byte_offset, &value, sizeof(value));
}

#endif
