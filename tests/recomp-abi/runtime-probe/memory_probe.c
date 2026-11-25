/*
 * Clean-room PowerPC execution probe for the pinned N64Recomp memory macros.
 *
 * This is a standalone GameCube DOL with no game ROM or generated game code.
 * It runs the exact patched MEM_* and MIPS unaligned-load/store helpers on
 * big-endian Broadway-compatible PowerPC. A global stage marker is read by
 * Dolphin's built-in GDB stub, avoiding reliance on the optional EXI debug UART.
 */
#include <gccore.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <recomp.h>
#include "n64_memory_be.h"

static uint8_t test_rdram[128] ATTRIBUTE_ALIGN(32);
static uint32_t mmio_scratch[8] ATTRIBUTE_ALIGN(32);

/*
 * GDB-readable execution state. Byte arrays deliberately avoid endian
 * ambiguity when the remote stub reads guest memory.
 */
volatile uint8_t g_probe_stage[4] __attribute__((used, aligned(4))) = {
    'I', 'N', 'I', 'T'
};
volatile uint32_t g_probe_failure_code __attribute__((used, aligned(4))) = 0;
volatile uint8_t g_probe_failure_label[24] __attribute__((used, aligned(4))) = {0};

static void set_probe_stage(uint8_t a, uint8_t b, uint8_t c, uint8_t d) {
    g_probe_stage[0] = a;
    g_probe_stage[1] = b;
    g_probe_stage[2] = c;
    g_probe_stage[3] = d;
    __asm__ volatile("" ::: "memory");
}

static void set_failure_label(const char *label) {
    size_t i = 0;
    for (; i < sizeof(g_probe_failure_label) - 1 && label[i] != '\0'; ++i) {
        g_probe_failure_label[i] = (uint8_t)label[i];
    }
    g_probe_failure_label[i] = 0;
    __asm__ volatile("" ::: "memory");
}

void *rdram_mmio_write(uint32_t offset) {
    (void)offset;
    return mmio_scratch;
}

void *rdram_bad_access(uint64_t n64_addr) {
    (void)n64_addr;
    return mmio_scratch;
}

static int fail_u32(const char *label, uint32_t actual, uint32_t expected) {
    (void)actual;
    (void)expected;
    g_probe_failure_code = UINT32_C(1);
    set_failure_label(label);
    return 0;
}

static int fail_u64(const char *label, uint64_t actual, uint64_t expected) {
    (void)actual;
    (void)expected;
    g_probe_failure_code = UINT32_C(2);
    set_failure_label(label);
    return 0;
}

#define CHECK_U32(label, expression, expected_value) do { \
    const uint32_t actual_value = (uint32_t)(expression); \
    const uint32_t expected_u32 = (uint32_t)(expected_value); \
    if (actual_value != expected_u32) return fail_u32((label), actual_value, expected_u32); \
} while (0)

#define CHECK_U64(label, expression, expected_value) do { \
    const uint64_t actual_value = (uint64_t)(expression); \
    const uint64_t expected_u64 = (uint64_t)(expected_value); \
    if (actual_value != expected_u64) return fail_u64((label), actual_value, expected_u64); \
} while (0)

static int run_memory_probe(void) {
    uint8_t *rdram = test_rdram;
    const gpr n64_base = (gpr)UINT64_C(0xFFFFFFFF80000000);
    static const uint8_t initial_word[4] = {0x11, 0x22, 0x33, 0x44};
    static const uint8_t initial_dword[8] = {
        0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88
    };
    static const uint32_t lwl_expected[4] = {
        UINT32_C(0x11223344), UINT32_C(0x223344DD),
        UINT32_C(0x3344CCDD), UINT32_C(0x44BBCCDD)
    };
    static const uint32_t lwr_expected[4] = {
        UINT32_C(0xAABBCC11), UINT32_C(0xAABB1122),
        UINT32_C(0xAA112233), UINT32_C(0x11223344)
    };
    static const uint32_t swl_expected[4] = {
        UINT32_C(0x11223344), UINT32_C(0xAA112233),
        UINT32_C(0xAABB1122), UINT32_C(0xAABBCC11)
    };
    static const uint32_t swr_expected[4] = {
        UINT32_C(0x44BBCCDD), UINT32_C(0x3344CCDD),
        UINT32_C(0x223344DD), UINT32_C(0x11223344)
    };
    static const uint64_t ldl_expected[8] = {
        UINT64_C(0x1122334455667788), UINT64_C(0x22334455667788A8),
        UINT64_C(0x334455667788A7A8), UINT64_C(0x4455667788A6A7A8),
        UINT64_C(0x55667788A5A6A7A8), UINT64_C(0x667788A4A5A6A7A8),
        UINT64_C(0x7788A3A4A5A6A7A8), UINT64_C(0x88A2A3A4A5A6A7A8)
    };
    static const uint64_t ldr_expected[8] = {
        UINT64_C(0xA1A2A3A4A5A6A711), UINT64_C(0xA1A2A3A4A5A61122),
        UINT64_C(0xA1A2A3A4A5112233), UINT64_C(0xA1A2A3A411223344),
        UINT64_C(0xA1A2A31122334455), UINT64_C(0xA1A2112233445566),
        UINT64_C(0xA111223344556677), UINT64_C(0x1122334455667788)
    };
    static const uint64_t sdl_expected[8] = {
        UINT64_C(0x1122334455667788), UINT64_C(0xA111223344556677),
        UINT64_C(0xA1A2112233445566), UINT64_C(0xA1A2A31122334455),
        UINT64_C(0xA1A2A3A411223344), UINT64_C(0xA1A2A3A4A5112233),
        UINT64_C(0xA1A2A3A4A5A61122), UINT64_C(0xA1A2A3A4A5A6A711)
    };
    static const uint64_t sdr_expected[8] = {
        UINT64_C(0x88A2A3A4A5A6A7A8), UINT64_C(0x7788A3A4A5A6A7A8),
        UINT64_C(0x667788A4A5A6A7A8), UINT64_C(0x55667788A5A6A7A8),
        UINT64_C(0x4455667788A6A7A8), UINT64_C(0x334455667788A7A8),
        UINT64_C(0x22334455667788A8), UINT64_C(0x1122334455667788)
    };

    memset(test_rdram, 0, sizeof(test_rdram));
    memset(mmio_scratch, 0, sizeof(mmio_scratch));

    test_rdram[0] = 0x01; test_rdram[1] = 0x23;
    test_rdram[2] = 0x45; test_rdram[3] = 0x67;
    test_rdram[4] = 0x89; test_rdram[5] = 0xAB;
    test_rdram[6] = 0xCD; test_rdram[7] = 0xEF;

    /* Actual patched byte, halfword and word memory macros on big-endian PPC. */
    CHECK_U32("MEM_BU_0", MEM_BU(0, n64_base), UINT32_C(0x01));
    CHECK_U32("MEM_BU_1", MEM_BU(0, n64_base + 1), UINT32_C(0x23));
    CHECK_U32("MEM_BU_2", MEM_BU(0, n64_base + 2), UINT32_C(0x45));
    CHECK_U32("MEM_BU_3", MEM_BU(0, n64_base + 3), UINT32_C(0x67));
    CHECK_U32("MEM_HU_0", MEM_HU(0, n64_base), UINT32_C(0x0123));
    CHECK_U32("MEM_HU_2", MEM_HU(0, n64_base + 2), UINT32_C(0x4567));
    CHECK_U32("MEM_W", (uint32_t)MEM_W(0, n64_base), UINT32_C(0x01234567));

    /* Signed loads must extend the N64 byte/halfword sign to 32 bits. */
    test_rdram[24] = 0x80;
    test_rdram[25] = 0x7F;
    test_rdram[26] = 0xFF;
    test_rdram[27] = 0x01;
    CHECK_U32("MEM_B_NEGATIVE", MEM_B(0, n64_base + 24), UINT32_C(0xFFFFFF80));
    CHECK_U32("MEM_B_POSITIVE", MEM_B(0, n64_base + 25), UINT32_C(0x0000007F));
    CHECK_U32("MEM_B_MINUS_ONE", MEM_B(0, n64_base + 26), UINT32_C(0xFFFFFFFF));
    CHECK_U32("MEM_B_ONE", MEM_B(0, n64_base + 27), UINT32_C(0x00000001));
    CHECK_U32("MEM_H_NEGATIVE", MEM_H(0, n64_base + 24), UINT32_C(0xFFFF807F));
    CHECK_U32("MEM_H_NEGATIVE_TWO", MEM_H(0, n64_base + 26), UINT32_C(0xFFFFFF01));
    CHECK_U32("MEM_HU_HIGH_BIT", MEM_HU(0, n64_base + 24), UINT32_C(0x807F));
    CHECK_U32("MEM_HU_FF01", MEM_HU(0, n64_base + 26), UINT32_C(0xFF01));

    MEM_B(0, n64_base + 8) = (int8_t)0xA5;
    MEM_H(0, n64_base + 10) = (int16_t)0xB6C7;
    MEM_W(0, n64_base + 12) = (int32_t)UINT32_C(0xD8E9FA0B);
    MEM_B(0, n64_base + 28) = (int8_t)0xD2;
    MEM_H(0, n64_base + 30) = (int16_t)0xE3F4;
    CHECK_U32("MEM_B_STORE", test_rdram[8], UINT32_C(0xA5));
    CHECK_U32("MEM_H_STORE_HI", test_rdram[10], UINT32_C(0xB6));
    CHECK_U32("MEM_H_STORE_LO", test_rdram[11], UINT32_C(0xC7));
    CHECK_U32("MEM_W_STORE", (uint32_t)MEM_W(0, n64_base + 12),
             UINT32_C(0xD8E9FA0B));
    CHECK_U32("MEM_B_STORE_EXTRA", test_rdram[28], UINT32_C(0xD2));
    CHECK_U32("MEM_H_STORE_EXTRA_HI", test_rdram[30], UINT32_C(0xE3));
    CHECK_U32("MEM_H_STORE_EXTRA_LO", test_rdram[31], UINT32_C(0xF4));
    CHECK_U32("MEM_B_STORE_SIGNED_READ", MEM_B(0, n64_base + 28),
             UINT32_C(0xFFFFFFD2));
    CHECK_U32("MEM_H_STORE_SIGNED_READ", MEM_H(0, n64_base + 30),
             UINT32_C(0xFFFFE3F4));
    CHECK_U32("MEM_H_STORE_UNSIGNED_READ", MEM_HU(0, n64_base + 30),
             UINT32_C(0xE3F4));

    SD((gpr)UINT64_C(0x1029384756ABCDEF), 0, n64_base + 16);
    CHECK_U64("SD_LD", LD(0, n64_base + 16), UINT64_C(0x1029384756ABCDEF));
    CHECK_U32("SD_HIGH_WORD", (uint32_t)MEM_W(0, n64_base + 16),
             UINT32_C(0x10293847));
    CHECK_U32("SD_LOW_WORD", (uint32_t)MEM_W(4, n64_base + 16),
             UINT32_C(0x56ABCDEF));

    /* Actual MIPS LWL/LWR/SWL/SWR helper behavior for every byte lane. */
    for (unsigned lane = 0; lane < 4; ++lane) {
        memcpy(test_rdram + 32, initial_word, sizeof(initial_word));
        CHECK_U32("LWL", do_lwl(rdram, (gpr)UINT32_C(0xAABBCCDD), 0,
                                n64_base + 32 + lane), lwl_expected[lane]);
        memcpy(test_rdram + 32, initial_word, sizeof(initial_word));
        CHECK_U32("LWR", do_lwr(rdram, (gpr)UINT32_C(0xAABBCCDD), 0,
                                n64_base + 32 + lane), lwr_expected[lane]);

        n64_be_write_u32(test_rdram, 32, UINT32_C(0xAABBCCDD));
        do_swl(rdram, 0, n64_base + 32 + lane, (gpr)UINT32_C(0x11223344));
        CHECK_U32("SWL", n64_be_read_u32(test_rdram, 32), swl_expected[lane]);

        n64_be_write_u32(test_rdram, 32, UINT32_C(0xAABBCCDD));
        do_swr(rdram, 0, n64_base + 32 + lane, (gpr)UINT32_C(0x11223344));
        CHECK_U32("SWR", n64_be_read_u32(test_rdram, 32), swr_expected[lane]);
    }

    /* Actual MIPS LDL/LDR/SDL/SDR helper behavior for every byte lane. */
    for (unsigned lane = 0; lane < 8; ++lane) {
        memcpy(test_rdram + 40, initial_dword, sizeof(initial_dword));
        CHECK_U64("LDL", do_ldl(rdram, UINT64_C(0xA1A2A3A4A5A6A7A8), 0,
                                n64_base + 40 + lane), ldl_expected[lane]);
        memcpy(test_rdram + 40, initial_dword, sizeof(initial_dword));
        CHECK_U64("LDR", do_ldr(rdram, UINT64_C(0xA1A2A3A4A5A6A7A8), 0,
                                n64_base + 40 + lane), ldr_expected[lane]);

        n64_be_write_u64(test_rdram, 40, UINT64_C(0xA1A2A3A4A5A6A7A8));
        do_sdl(rdram, 0, n64_base + 40 + lane, (gpr)UINT64_C(0x1122334455667788));
        CHECK_U64("SDL", n64_be_read_u64(test_rdram, 40), sdl_expected[lane]);

        n64_be_write_u64(test_rdram, 40, UINT64_C(0xA1A2A3A4A5A6A7A8));
        do_sdr(rdram, 0, n64_base + 40 + lane, (gpr)UINT64_C(0x1122334455667788));
        CHECK_U64("SDR", n64_be_read_u64(test_rdram, 40), sdr_expected[lane]);
    }

    return 1;
}

int main(void) {
    set_probe_stage('S', 'T', 'A', 'R');

    if (!run_memory_probe()) {
        set_probe_stage('F', 'A', 'I', 'L');
        for (;;) {
            __asm__ volatile("nop");
        }
    }

    set_probe_stage('P', 'A', 'S', 'S');
    for (;;) {
        __asm__ volatile("nop");
    }
    return 0;
}
