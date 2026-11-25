#include "ppc_int128_compat.h"

#include <assert.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

static uint64_t next_random(uint64_t *state) {
    uint64_t x = *state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *state = x;
    return x * UINT64_C(2685821657736338717);
}

static void check_unsigned(uint64_t a, uint64_t b) {
    uint64_t low = 0;
    uint64_t high = 0;
    DMULTU(a, b, &low, &high);
#if defined(__SIZEOF_INT128__)
    {
        const __uint128_t expected = (__uint128_t)a * (__uint128_t)b;
        assert(low == (uint64_t)expected);
        assert(high == (uint64_t)(expected >> 64));
    }
#endif
}

static void check_signed(int64_t a, int64_t b) {
    int64_t low = 0;
    int64_t high = 0;
    DMULT(a, b, &low, &high);
#if defined(__SIZEOF_INT128__)
    {
        const __int128_t expected = (__int128_t)a * (__int128_t)b;
        assert((uint64_t)low == (uint64_t)expected);
        assert((uint64_t)high == (uint64_t)(((__uint128_t)expected) >> 64));
    }
#endif
}

int main(void) {
    uint64_t state = UINT64_C(0x4D595DF4D0F33173);
    uint64_t low = 0;
    uint64_t high = 0;

    DMULTU(UINT64_MAX, 2, &low, &high);
    assert(low == UINT64_C(0xFFFFFFFFFFFFFFFE));
    assert(high == UINT64_C(1));

    DMULTU(UINT64_C(0x100000001), UINT64_C(0x100000001), &low, &high);
    assert(low == UINT64_C(0x0000000200000001));
    assert(high == UINT64_C(1));

    check_signed(-2, 3);
    check_signed(INT64_MIN, -1);
    check_signed(INT64_MIN, 2);
    check_signed(INT64_MAX, INT64_MAX);
    check_signed(-1, -1);
    check_signed(0, INT64_MIN);

    for (unsigned i = 0; i < 10000; ++i) {
        const uint64_t a = next_random(&state);
        const uint64_t b = next_random(&state);
        check_unsigned(a, b);
        check_signed((int64_t)a, (int64_t)b);
    }

    puts("Portable PPC 64x64 -> 128-bit multiply: PASS");
    return 0;
}
