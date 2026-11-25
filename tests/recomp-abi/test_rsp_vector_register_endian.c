#include "rsp_vector_register_endian.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_lane_selector(void)
{
#if N64_RSP_VECTOR_HOST_BIG_ENDIAN
    assert(n64_rsp_vector_byte_storage_index(0) == 8);
    assert(n64_rsp_vector_byte_storage_index(7) == 15);
    assert(n64_rsp_vector_byte_storage_index(8) == 0);
    assert(n64_rsp_vector_byte_storage_index(15) == 7);
    assert(n64_rsp_vector_half_storage_index(0) == 4);
    assert(n64_rsp_vector_half_storage_index(3) == 7);
    assert(n64_rsp_vector_half_storage_index(4) == 0);
    assert(n64_rsp_vector_half_storage_index(7) == 3);
#else
    assert(n64_rsp_vector_byte_storage_index(0) == 15);
    assert(n64_rsp_vector_byte_storage_index(7) == 8);
    assert(n64_rsp_vector_byte_storage_index(8) == 7);
    assert(n64_rsp_vector_byte_storage_index(15) == 0);
    assert(n64_rsp_vector_half_storage_index(0) == 7);
    assert(n64_rsp_vector_half_storage_index(3) == 4);
    assert(n64_rsp_vector_half_storage_index(4) == 3);
    assert(n64_rsp_vector_half_storage_index(7) == 0);
#endif
}

static void test_architectural_byte_and_halfword_order(void)
{
    uint64_t words[2];
    static const uint8_t expected_bytes[16] = {
        0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
        0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF
    };
    static const uint16_t expected_halfwords[8] = {
        0x0011, 0x2233, 0x4455, 0x6677,
        0x8899, 0xAABB, 0xCCDD, 0xEEFF
    };

    /* u128[0] is the low 64-bit word; u128[1] is the high 64-bit word. */
    words[0] = UINT64_C(0x8899AABBCCDDEEFF);
    words[1] = UINT64_C(0x0011223344556677);

    for (uint32_t i = 0; i < 16; ++i) {
        assert(n64_rsp_vector_load_u8(words, i) == expected_bytes[i]);
    }
    for (uint32_t i = 0; i < 8; ++i) {
        assert(n64_rsp_vector_load_u16(words, i) == expected_halfwords[i]);
    }

    assert(n64_rsp_vector_load_s16(words, 0) == INT16_C(0x0011));
    assert(n64_rsp_vector_load_s16(words, 7) == (int16_t)UINT16_C(0xEEFF));
}

static void test_lane_stores(void)
{
    uint64_t words[2] = {
        UINT64_C(0x8899AABBCCDDEEFF),
        UINT64_C(0x0011223344556677)
    };

    n64_rsp_vector_store_u8(words, 0, 0xA0);
    assert(n64_rsp_vector_load_u8(words, 0) == 0xA0);
    assert(words[1] == UINT64_C(0xA011223344556677));

    n64_rsp_vector_store_u8(words, 15, 0x0F);
    assert(n64_rsp_vector_load_u8(words, 15) == 0x0F);
    assert(words[0] == UINT64_C(0x8899AABBCCDDEE0F));

    n64_rsp_vector_store_u16(words, 0, UINT16_C(0x1357));
    assert(n64_rsp_vector_load_u16(words, 0) == UINT16_C(0x1357));

    n64_rsp_vector_store_u16(words, 7, UINT16_C(0x2468));
    assert(n64_rsp_vector_load_u16(words, 7) == UINT16_C(0x2468));
}

int main(void)
{
    test_lane_selector();
    test_architectural_byte_and_halfword_order();
    test_lane_stores();

    puts("RSP vector register endian reference: PASS");
    return 0;
}
