#ifndef BOONTA_TESTS_RECOMP_ABI_PPC_INT128_COMPAT_H
#define BOONTA_TESTS_RECOMP_ABI_PPC_INT128_COMPAT_H

#include <stdint.h>

/*
 * Clean-room 64x64 -> 128-bit multiply fallback.
 *
 * This probes the pinned N64Recomp header on 32-bit PowerPC compilers that
 * do not expose __int128. It uses four 32x32 products and carry accumulation.
 */
static inline void recomp_mul_u64_wide(uint64_t a, uint64_t b,
                                      uint64_t *low, uint64_t *high) {
    const uint64_t a_low = (uint32_t)a;
    const uint64_t a_high = a >> 32;
    const uint64_t b_low = (uint32_t)b;
    const uint64_t b_high = b >> 32;

    uint64_t t = a_low * b_low;
    const uint64_t low_word = (uint32_t)t;
    const uint64_t carry0 = t >> 32;

    t = a_high * b_low + carry0;
    const uint64_t middle_word = (uint32_t)t;
    const uint64_t carry1 = t >> 32;

    t = a_low * b_high + middle_word;
    const uint64_t carry2 = t >> 32;

    *low = (t << 32) | low_word;
    *high = a_high * b_high + carry1 + carry2;
}

static inline void DMULTU(uint64_t a, uint64_t b,
                          uint64_t *low64, uint64_t *high64) {
    recomp_mul_u64_wide(a, b, low64, high64);
}

static inline void DMULT(int64_t a, int64_t b,
                         int64_t *low64, int64_t *high64) {
    uint64_t low;
    uint64_t high;
    const uint64_t ua = (uint64_t)a;
    const uint64_t ub = (uint64_t)b;

    recomp_mul_u64_wide(ua, ub, &low, &high);

    /* Two's-complement correction for a signed 128-bit product. */
    if (a < 0) {
        high -= ub;
    }
    if (b < 0) {
        high -= ua;
    }

    *low64 = (int64_t)low;
    *high64 = (int64_t)high;
}

#endif
