#include "rsp_dmem_endian.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t dmem[N64_RSP_DMEM_SIZE];

static void test_byte_and_word_views(void)
{
    const uint8_t expected[4] = {0x11, 0x22, 0x33, 0x44};
    uint32_t i;

    memset(dmem, 0, sizeof(dmem));
    for (i = 0; i < 4; ++i) {
        n64_rsp_dmem_store_u8(dmem, 0, 0x100 + i, expected[i]);
    }

    for (i = 0; i < 4; ++i) {
        assert(n64_rsp_dmem_load_u8(dmem, 0, 0x100 + i) == expected[i]);
    }

    assert(n64_rsp_dmem_load_u32(dmem, 0, 0x100) ==
           UINT32_C(0x11223344));
    assert(n64_rsp_dmem_load_u16(dmem, 0, 0x100) == UINT16_C(0x1122));
    assert(n64_rsp_dmem_load_u16(dmem, 0, 0x102) == UINT16_C(0x3344));
}

static void test_signed_and_unsigned_halfword(void)
{
    memset(dmem, 0, sizeof(dmem));

    n64_rsp_dmem_store_u8(dmem, 0, 0x200, 0x80);
    n64_rsp_dmem_store_u8(dmem, 0, 0x201, 0x01);
    assert(n64_rsp_dmem_load_u16(dmem, 0, 0x200) == UINT16_C(0x8001));
    assert(n64_rsp_dmem_load_s16(dmem, 0, 0x200) == INT32_C(-32767));

    n64_rsp_dmem_store_u16_low(dmem, 0, 0x202, UINT32_C(0xA1B2C3D4));
    assert(n64_rsp_dmem_load_u8(dmem, 0, 0x202) == 0xC3);
    assert(n64_rsp_dmem_load_u8(dmem, 0, 0x203) == 0xD4);
    assert(n64_rsp_dmem_load_u16(dmem, 0, 0x202) == UINT16_C(0xC3D4));
}

static void test_word_store_and_offset(void)
{
    memset(dmem, 0, sizeof(dmem));
    n64_rsp_dmem_store_u32(dmem, 0x10, 0x300, UINT32_C(0xDEADBEEF));

    assert(n64_rsp_dmem_load_u8(dmem, 0x10, 0x300) == 0xDE);
    assert(n64_rsp_dmem_load_u8(dmem, 0x10, 0x301) == 0xAD);
    assert(n64_rsp_dmem_load_u8(dmem, 0x10, 0x302) == 0xBE);
    assert(n64_rsp_dmem_load_u8(dmem, 0x10, 0x303) == 0xEF);
    assert(n64_rsp_dmem_load_u32(dmem, 0x10, 0x300) ==
           UINT32_C(0xDEADBEEF));
}

static void test_4k_wraparound(void)
{
    memset(dmem, 0, sizeof(dmem));

    n64_rsp_dmem_store_u8(dmem, 0, 0xFFE, 0x11);
    n64_rsp_dmem_store_u8(dmem, 0, 0xFFF, 0x22);
    n64_rsp_dmem_store_u8(dmem, 0, 0x1000, 0x33);
    n64_rsp_dmem_store_u8(dmem, 0, 0x1001, 0x44);

    assert(n64_rsp_dmem_load_u8(dmem, 0, 0xFFE) == 0x11);
    assert(n64_rsp_dmem_load_u8(dmem, 0, 0xFFF) == 0x22);
    assert(n64_rsp_dmem_load_u8(dmem, 0, 0x000) == 0x33);
    assert(n64_rsp_dmem_load_u8(dmem, 0, 0x001) == 0x44);
    assert(n64_rsp_dmem_load_u32(dmem, 0, 0xFFE) ==
           UINT32_C(0x11223344));
}

static void test_lane_selector(void)
{
#if N64_RSP_DMEM_HOST_BIG_ENDIAN
    assert(n64_rsp_dmem_host_byte_index(0) == 0);
    assert(n64_rsp_dmem_host_byte_index(1) == 1);
    assert(n64_rsp_dmem_host_byte_index(2) == 2);
    assert(n64_rsp_dmem_host_byte_index(3) == 3);
    assert(n64_rsp_dmem_host_word_byte_index(0) == 0);
    assert(n64_rsp_dmem_host_half_load_byte_index(0) == 0);
    assert(n64_rsp_dmem_host_half_store_byte_index(0) == 2);
#else
    assert(n64_rsp_dmem_host_byte_index(0) == 3);
    assert(n64_rsp_dmem_host_byte_index(1) == 2);
    assert(n64_rsp_dmem_host_byte_index(2) == 1);
    assert(n64_rsp_dmem_host_byte_index(3) == 0);
    assert(n64_rsp_dmem_host_word_byte_index(0) == 3);
    assert(n64_rsp_dmem_host_half_load_byte_index(0) == 1);
    assert(n64_rsp_dmem_host_half_store_byte_index(0) == 1);
#endif
}

int main(void)
{
    test_lane_selector();
    test_byte_and_word_views();
    test_signed_and_unsigned_halfword();
    test_word_store_and_offset();
    test_4k_wraparound();

    puts("RSP DMEM endian reference: PASS");
    return 0;
}
