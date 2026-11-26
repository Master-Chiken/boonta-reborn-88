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
#include "n64_segmented_memory.h"
#include "n64_recomp_memory_api.h"
#include "rsp_dmem_endian.h"
#include "rsp_vector_register_endian.h"

/* Compiled from the exact pinned N64ModernRuntime RSP::r128 accessor union. */
extern int run_pinned_rsp_r128_accessor_probe(void);
extern int run_pinned_rsp_dmem_accessor_probe(void);
extern int run_opaque_rsp_dma_probe(uint8_t *rdram_token);

static uint8_t test_rdram[128] ATTRIBUTE_ALIGN(32);
static uint32_t mmio_scratch[8] ATTRIBUTE_ALIGN(32);

/*
 * Small, physically separate backing windows for the segmented-map PPC probe.
 * The guest-visible addresses still use the real N64 8 MiB/8 MiB logical
 * windows; only the portions touched by this bounded test are backed.
 */
static uint8_t segmented_rdram[0x1000] ATTRIBUTE_ALIGN(32);
static uint8_t segmented_extended[0x2000] ATTRIBUTE_ALIGN(32);
static uint8_t segmented_mod_ram[0x100] ATTRIBUTE_ALIGN(32);
static uint8_t segmented_heap[0x200] ATTRIBUTE_ALIGN(32);
static uint8_t segmented_rom[16] ATTRIBUTE_ALIGN(32);
static uint8_t rsp_dmem_probe[N64_RSP_DMEM_SIZE] ATTRIBUTE_ALIGN(32);
static uint64_t rsp_vector_words[2] ATTRIBUTE_ALIGN(16);

typedef struct segmented_probe_callbacks {
    uint32_t mmio_address;
    uint8_t mmio_width;
    n64_segmented_access mmio_access;
    uint64_t mmio_written_value;
} segmented_probe_callbacks;

static int segmented_rom_read(
    void *context, uint32_t rom_offset, uint8_t *destination, size_t length)
{
    (void)context;
    if (rom_offset > sizeof(segmented_rom) ||
        length > sizeof(segmented_rom) - rom_offset) {
        return -1;
    }
    memcpy(destination, segmented_rom + rom_offset, length);
    return 0;
}

static int segmented_mmio_access(
    void *context,
    uint32_t virtual_address,
    uint8_t width,
    n64_segmented_access access,
    uint64_t *value)
{
    segmented_probe_callbacks *callbacks =
        (segmented_probe_callbacks *)context;

    callbacks->mmio_address = virtual_address;
    callbacks->mmio_width = width;
    callbacks->mmio_access = access;
    if (access == N64_SEGMENTED_ACCESS_READ) {
        *value = width == 8
            ? UINT64_C(0xA1B2C3D4E5F60718)
            : UINT32_C(0xA1B2C3D4);
    } else {
        callbacks->mmio_written_value = *value;
    }
    return 0;
}

#define CHECK_SEGMENTED(label, expression, expected_value) do { \
    const uint32_t actual_value = (uint32_t)(expression); \
    const uint32_t expected_u32 = (uint32_t)(expected_value); \
    if (actual_value != expected_u32) return fail_u32((label), actual_value, expected_u32); \
} while (0)

/*
 * GDB-readable execution state. Byte arrays deliberately avoid endian
 * ambiguity when the remote stub reads guest memory.
 */
volatile uint8_t g_probe_stage[4] __attribute__((used, aligned(4))) = {
    'I', 'N', 'I', 'T'
};
volatile uint32_t g_probe_failure_code __attribute__((used, aligned(4))) = 0;
volatile uint8_t g_probe_failure_label[24] __attribute__((used, aligned(4))) = {0};
volatile uint64_t g_probe_failure_actual __attribute__((used, aligned(8))) = 0;
volatile uint64_t g_probe_failure_expected __attribute__((used, aligned(8))) = 0;

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

/*
 * These noinline marker functions are GDB software-breakpoint targets.
 * The breakpoint stops Dolphin at a known guest PC, avoiding unreliable
 * host Ctrl-C polling and remote reads of DOL data addresses.
 */
/*
 * Distinct volatile stores prevent the linker/compiler from folding the
 * three noinline breakpoint targets into identical code addresses.
 */
volatile uint32_t g_probe_marker_sink __attribute__((used, aligned(4))) = 0;

__attribute__((noinline, used, externally_visible)) void probe_start_marker(void) {
    g_probe_marker_sink = UINT32_C(0x53544152); /* STAR */
    __asm__ volatile("" ::: "memory");
}

__attribute__((noinline, used, externally_visible)) void probe_pass_marker(void) {
    g_probe_marker_sink = UINT32_C(0x50415353); /* PASS */
    __asm__ volatile("" ::: "memory");
}

__attribute__((noinline, used, externally_visible)) void probe_fail_marker(void) {
    g_probe_marker_sink = UINT32_C(0x4641494C); /* FAIL */
    __asm__ volatile("" ::: "memory");
}

/*
 * Keep all marker sections reachable to the linker even if interprocedural
 * analysis proves one branch unlikely for this fixed test input. The GDB
 * harness needs every possible outcome address present in the ELF.
 */
void (* volatile g_probe_start_marker_ref)(void) __attribute__((used)) = probe_start_marker;
void (* volatile g_probe_pass_marker_ref)(void) __attribute__((used)) = probe_pass_marker;
void (* volatile g_probe_fail_marker_ref)(void) __attribute__((used)) = probe_fail_marker;

void *rdram_mmio_write(uint32_t offset) {
    (void)offset;
    return mmio_scratch;
}

void *rdram_bad_access(uint64_t n64_addr) {
    (void)n64_addr;
    return mmio_scratch;
}

static int fail_u32(const char *label, uint32_t actual, uint32_t expected) {
    g_probe_failure_code = UINT32_C(1);
    g_probe_failure_actual = (uint64_t)actual;
    g_probe_failure_expected = (uint64_t)expected;
    set_failure_label(label);
    return 0;
}

static int fail_u64(const char *label, uint64_t actual, uint64_t expected) {
    g_probe_failure_code = UINT32_C(2);
    g_probe_failure_actual = actual;
    g_probe_failure_expected = expected;
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

static __attribute__((noinline, noipa)) int run_memory_probe(void) {
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
    /*
     * N64Recomp's MIPS64 LWR helper sign-extends the merged 32-bit result.
     * The upper word therefore follows bit 31 of the merged value; it must
     * not be expected to stay zero when the retained bytes have bit 31 set.
     */
    static const uint64_t lwr_expected[4] = {
        UINT64_C(0xFFFFFFFFAABBCC11), UINT64_C(0xFFFFFFFFAABB1122),
        UINT64_C(0xFFFFFFFFAA112233), UINT64_C(0x0000000011223344)
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

    /* Signed N64 scalar loads must extend through the full 64-bit gpr. */
    test_rdram[24] = 0x80;
    test_rdram[25] = 0x7F;
    test_rdram[26] = 0xFF;
    test_rdram[27] = 0x01;
    CHECK_U64("MEM_B_NEGATIVE", MEM_B(0, n64_base + 24), UINT64_C(0xFFFFFFFFFFFFFF80));
    CHECK_U64("MEM_B_POSITIVE", MEM_B(0, n64_base + 25), UINT64_C(0x000000000000007F));
    CHECK_U64("MEM_B_MINUS_ONE", MEM_B(0, n64_base + 26), UINT64_C(0xFFFFFFFFFFFFFFFF));
    CHECK_U64("MEM_B_ONE", MEM_B(0, n64_base + 27), UINT64_C(0x0000000000000001));
    CHECK_U64("MEM_H_NEGATIVE", MEM_H(0, n64_base + 24), UINT64_C(0xFFFFFFFFFFFF807F));
    CHECK_U64("MEM_H_NEGATIVE_TWO", MEM_H(0, n64_base + 26), UINT64_C(0xFFFFFFFFFFFFFF01));
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
    CHECK_U64("MEM_W_SIGNED_READ", MEM_W(0, n64_base + 12),
              UINT64_C(0xFFFFFFFFD8E9FA0B));
    CHECK_U32("MEM_B_STORE_EXTRA", test_rdram[28], UINT32_C(0xD2));
    CHECK_U32("MEM_H_STORE_EXTRA_HI", test_rdram[30], UINT32_C(0xE3));
    CHECK_U32("MEM_H_STORE_EXTRA_LO", test_rdram[31], UINT32_C(0xF4));
    CHECK_U64("MEM_B_STORE_SIGNED_READ", MEM_B(0, n64_base + 28),
             UINT64_C(0xFFFFFFFFFFFFFFD2));
    CHECK_U64("MEM_H_STORE_SIGNED_READ", MEM_H(0, n64_base + 30),
             UINT64_C(0xFFFFFFFFFFFFE3F4));
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
        CHECK_U64("LWL", do_lwl(rdram, (gpr)UINT32_C(0xAABBCCDD), 0,
                                n64_base + 32 + lane), lwl_expected[lane]);
        memcpy(test_rdram + 32, initial_word, sizeof(initial_word));
        CHECK_U64("LWR", do_lwr(rdram, (gpr)UINT32_C(0xAABBCCDD), 0,
                                n64_base + 32 + lane), lwr_expected[lane]);

        n64_be_write_u32(test_rdram, 32, UINT32_C(0xAABBCCDD));
        do_swl(rdram, 0, n64_base + 32 + lane, (gpr)UINT32_C(0x11223344));
        CHECK_U32("SWL", n64_be_read_u32(test_rdram, 32), swl_expected[lane]);

        n64_be_write_u32(test_rdram, 32, UINT32_C(0xAABBCCDD));
        do_swr(rdram, 0, n64_base + 32 + lane, (gpr)UINT32_C(0x11223344));
        CHECK_U32("SWR", n64_be_read_u32(test_rdram, 32), swr_expected[lane]);
    }

    /* LWL/LWR must sign-extend a negative 32-bit result to the full gpr. */
    test_rdram[64] = 0x89;
    test_rdram[65] = 0xAB;
    test_rdram[66] = 0xCD;
    test_rdram[67] = 0xEF;
    CHECK_U64("LWL_SIGNED_EXT", do_lwl(rdram, 0, 0, n64_base + 64),
              UINT64_C(0xFFFFFFFF89ABCDEF));
    CHECK_U64("LWR_SIGNED_EXT", do_lwr(rdram, 0, 0, n64_base + 67),
              UINT64_C(0xFFFFFFFF89ABCDEF));

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

static __attribute__((noinline, noipa)) int run_segmented_probe(void) {
    n64_segmented_memory memory;
    n64_recomp_memory_handle opaque_handle;
    segmented_probe_callbacks callbacks;
    uint8_t *rdram_token;
    uint64_t value = 0;
    uint64_t guest_address = 0;
    uint8_t *host_pointer = NULL;

    memset(&memory, 0, sizeof(memory));
    memset(&callbacks, 0, sizeof(callbacks));
    memset(segmented_rdram, 0, sizeof(segmented_rdram));
    memset(segmented_extended, 0, sizeof(segmented_extended));
    memset(segmented_mod_ram, 0, sizeof(segmented_mod_ram));
    memset(segmented_heap, 0, sizeof(segmented_heap));

    segmented_rom[0] = 0xDE;
    segmented_rom[1] = 0xAD;
    segmented_rom[2] = 0xBE;
    segmented_rom[3] = 0xEF;
    segmented_rom[4] = 0x10;
    segmented_rom[5] = 0x20;
    segmented_rom[6] = 0x30;
    segmented_rom[7] = 0x40;

    memory.rdram = segmented_rdram;
    memory.rdram_size = sizeof(segmented_rdram);
    memory.extended = segmented_extended;
    memory.extended_size = sizeof(segmented_extended);
    memory.mod_ram = segmented_mod_ram;
    memory.mod_ram_size = sizeof(segmented_mod_ram);
    memory.heap = segmented_heap;
    memory.heap_size = sizeof(segmented_heap);
    memory.rom_size = sizeof(segmented_rom);
    memory.rom_read = segmented_rom_read;
    memory.mmio_access = segmented_mmio_access;
    memory.callback_context = &callbacks;

    CHECK_SEGMENTED("SEG_VALIDATE", n64_segmented_memory_validate(&memory),
                    N64_SEGMENTED_OK);

    /*
     * Exercise the proposed generated-function ABI: the legacy uint8_t*
     * argument is now only an opaque memory-context token, not a byte-array
     * base. This is a probe of the adapter contract, not an upstream patch.
     */
    n64_recomp_memory_handle_init(&opaque_handle, &memory, NULL, NULL);
    rdram_token = n64_recomp_memory_token(&opaque_handle);
    CHECK_SEGMENTED("CTX_RDRAM_STORE",
        n64_recomp_store_u32(rdram_token, UINT64_C(0xFFFFFFFF80000050),
                             UINT32_C(0xCAFEBABE)),
        N64_SEGMENTED_OK);
    CHECK_U32("CTX_RDRAM_LOAD",
        n64_recomp_load_u32(rdram_token, UINT64_C(0xFFFFFFFF80000050)),
        UINT32_C(0xCAFEBABE));

    segmented_rdram[0x180] = UINT8_C(0x10);
    segmented_rdram[0x181] = UINT8_C(0x21);
    segmented_rdram[0x182] = UINT8_C(0x32);
    segmented_rdram[0x183] = UINT8_C(0x43);
    const int opaque_rsp_dma_result = run_opaque_rsp_dma_probe(rdram_token);
    if (opaque_rsp_dma_result != 0) {
        return fail_u32("CTX_RSP_DMA", (uint32_t)opaque_rsp_dma_result, 0);
    }
    CHECK_U32("CTX_RSP_DMA_WRITTEN",
        segmented_rdram[0x180], UINT8_C(0xA0));
    CHECK_SEGMENTED("CTX_RSP_DMA_CLEAR_ERROR",
        n64_recomp_memory_last_error(rdram_token), N64_SEGMENTED_OK);
    if (N64_RECOMP_TO_PTR_VOID(rdram_token,
                               UINT64_C(0xFFFFFFFF80000050)) !=
        segmented_rdram + 0x50) {
        return fail_u32("CTX_TO_PTR_RDRAM", 0, 1);
    }
    if (N64_RECOMP_TO_PTR(uint32_t, rdram_token,
                          UINT64_C(0xFFFFFFFF80800000)) !=
        (uint32_t *)(void *)segmented_extended) {
        return fail_u32("CTX_TO_PTR_EXTENSION", 0, 1);
    }
    if (N64_RECOMP_TO_PTR_VOID(rdram_token,
                               UINT64_C(0xFFFFFFFFA4600010)) != NULL) {
        return fail_u32("CTX_TO_PTR_MMIO_NULL", 1, 0);
    }
    CHECK_SEGMENTED("CTX_TO_PTR_MMIO_ERROR",
        n64_recomp_memory_last_error(rdram_token),
        N64_SEGMENTED_NOT_RAM_BACKED);
    n64_recomp_memory_clear_error(rdram_token);
    CHECK_U32("CTX_MMIO_LOAD",
        n64_recomp_load_u32(rdram_token, UINT64_C(0xFFFFFFFFA4600010)),
        UINT32_C(0xA1B2C3D4));
    CHECK_SEGMENTED("CTX_NO_ERROR_AFTER_LOAD",
        n64_recomp_memory_last_error(rdram_token),
        N64_SEGMENTED_OK);

    CHECK_SEGMENTED("SEG_RDRAM_WRITE",
        n64_segmented_write(&memory, UINT64_C(0xFFFFFFFF80000040), 4,
                            UINT32_C(0x12345678)),
        N64_SEGMENTED_OK);
    CHECK_SEGMENTED("SEG_RDRAM_READ",
        n64_segmented_read(&memory, UINT64_C(0xFFFFFFFF80000040), 4, &value),
        N64_SEGMENTED_OK);
    CHECK_U32("SEG_RDRAM_VALUE", value, UINT32_C(0x12345678));
    CHECK_SEGMENTED("SEG_KSEG1_ALIAS",
        n64_segmented_read(&memory, UINT64_C(0xFFFFFFFFA0000040), 4, &value),
        N64_SEGMENTED_OK);
    CHECK_U32("SEG_KSEG1_VALUE", value, UINT32_C(0x12345678));

    CHECK_SEGMENTED("SEG_EXTENDED_WRITE",
        n64_segmented_write(&memory, UINT64_C(0xFFFFFFFF80800000), 4,
                            UINT32_C(0x80800000)),
        N64_SEGMENTED_OK);
    CHECK_SEGMENTED("SEG_EXTENDED_READ",
        n64_segmented_read(&memory, UINT64_C(0xFFFFFFFF80800000), 4, &value),
        N64_SEGMENTED_OK);
    CHECK_U32("SEG_EXTENDED_VALUE", value, UINT32_C(0x80800000));

    CHECK_SEGMENTED("SEG_PATCH_WRITE",
        n64_segmented_write(&memory, UINT64_C(0xFFFFFFFF80801000), 4,
                            UINT32_C(0x50415443)),
        N64_SEGMENTED_OK);
    CHECK_SEGMENTED("SEG_MOD_WRITE",
        n64_segmented_write(&memory, UINT64_C(0xFFFFFFFF81000000), 4,
                            UINT32_C(0x4D4F4421)),
        N64_SEGMENTED_OK);
    CHECK_SEGMENTED("SEG_HEAP_WRITE",
        n64_segmented_write(&memory, UINT64_C(0xFFFFFFFF81000100), 8,
                            UINT64_C(0x1029384756ABCDEF)),
        N64_SEGMENTED_OK);
    CHECK_SEGMENTED("SEG_HEAP_READ",
        n64_segmented_read(&memory, UINT64_C(0xFFFFFFFF81000100), 8, &value),
        N64_SEGMENTED_OK);
    CHECK_U64("SEG_HEAP_VALUE", value, UINT64_C(0x1029384756ABCDEF));

    CHECK_SEGMENTED("SEG_REVERSE_HEAP",
        n64_segmented_guest_from_host(&memory, segmented_heap + 0x10, 8,
                                      &guest_address),
        N64_SEGMENTED_OK);
    CHECK_U64("SEG_REVERSE_HEAP_ADDRESS", guest_address,
              UINT64_C(0xFFFFFFFF81000110));

    CHECK_SEGMENTED("SEG_TO_PTR_RDRAM",
        n64_segmented_host_pointer_for_guest(
            &memory, UINT64_C(0xFFFFFFFF80000040), 4,
            N64_SEGMENTED_ACCESS_READ, &host_pointer),
        N64_SEGMENTED_OK);
    if (host_pointer != segmented_rdram + 0x40) {
        return fail_u32("SEG_TO_PTR_RDRAM_HOST", 0, 1);
    }
    CHECK_SEGMENTED("SEG_TO_PTR_EXTENDED",
        n64_segmented_host_pointer_for_guest(
            &memory, UINT64_C(0xFFFFFFFF80800000), 4,
            N64_SEGMENTED_ACCESS_READ, &host_pointer),
        N64_SEGMENTED_OK);
    if (host_pointer != segmented_extended) {
        return fail_u32("SEG_TO_PTR_EXTENDED_HOST", 0, 1);
    }
    CHECK_SEGMENTED("SEG_TO_PTR_HEAP",
        n64_segmented_host_pointer_for_guest(
            &memory, UINT64_C(0xFFFFFFFF81000100), 8,
            N64_SEGMENTED_ACCESS_WRITE, &host_pointer),
        N64_SEGMENTED_OK);
    if (host_pointer != segmented_heap) {
        return fail_u32("SEG_TO_PTR_HEAP_HOST", 0, 1);
    }
    CHECK_SEGMENTED("SEG_TO_PTR_MMIO_REJECT",
        n64_segmented_host_pointer_for_guest(
            &memory, UINT64_C(0xFFFFFFFFA4600010), 4,
            N64_SEGMENTED_ACCESS_READ, &host_pointer),
        N64_SEGMENTED_NOT_RAM_BACKED);
    if (host_pointer != NULL) {
        return fail_u32("SEG_TO_PTR_MMIO_NULL", 1, 0);
    }
    CHECK_SEGMENTED("SEG_TO_PTR_ROM_REJECT",
        n64_segmented_host_pointer_for_guest(
            &memory, UINT64_C(0xFFFFFFFFB0000004), 4,
            N64_SEGMENTED_ACCESS_READ, &host_pointer),
        N64_SEGMENTED_NOT_RAM_BACKED);
    if (host_pointer != NULL) {
        return fail_u32("SEG_TO_PTR_ROM_NULL", 1, 0);
    }

    CHECK_SEGMENTED("SEG_MMIO_READ",
        n64_segmented_read(&memory, UINT64_C(0xFFFFFFFFA4600010), 4, &value),
        N64_SEGMENTED_OK);
    CHECK_U32("SEG_MMIO_VALUE", value, UINT32_C(0xA1B2C3D4));
    CHECK_U32("SEG_MMIO_ADDRESS", callbacks.mmio_address, UINT32_C(0xA4600010));
    CHECK_U32("SEG_MMIO_WIDTH", callbacks.mmio_width, 4);
    CHECK_SEGMENTED("SEG_MMIO_WRITE",
        n64_segmented_write(&memory, UINT64_C(0xFFFFFFFFA4600010), 4,
                            UINT32_C(0xBEEF1234)),
        N64_SEGMENTED_OK);
    CHECK_U64("SEG_MMIO_WRITTEN", callbacks.mmio_written_value,
              UINT32_C(0xBEEF1234));

    CHECK_SEGMENTED("SEG_ROM_READ",
        n64_segmented_read(&memory, UINT64_C(0xFFFFFFFFB0000004), 4, &value),
        N64_SEGMENTED_OK);
    CHECK_U32("SEG_ROM_VALUE", value, UINT32_C(0x10203040));
    CHECK_SEGMENTED("SEG_ROM_WRITE",
        n64_segmented_write(&memory, UINT64_C(0xFFFFFFFFB0000004), 4, 0),
        N64_SEGMENTED_READ_ONLY);

    CHECK_SEGMENTED("SEG_RDRAM_PARTIAL_END",
        n64_segmented_read(&memory, UINT64_C(0xFFFFFFFF80000FFF), 2, &value),
        N64_SEGMENTED_RANGE_CROSSES_REGION);
    CHECK_SEGMENTED("SEG_UNBACKED_RDRAM",
        n64_segmented_read(&memory, UINT64_C(0xFFFFFFFF80001000), 4, &value),
        N64_SEGMENTED_UNMAPPED_ADDRESS);
    CHECK_SEGMENTED("SEG_UNBACKED_KSEG1",
        n64_segmented_read(&memory, UINT64_C(0xFFFFFFFFA0001000), 4, &value),
        N64_SEGMENTED_UNMAPPED_ADDRESS);
    CHECK_SEGMENTED("SEG_NONCANONICAL",
        n64_segmented_read(&memory, UINT64_C(0x0000000080000000), 4, &value),
        N64_SEGMENTED_NONCANONICAL_ADDRESS);

    return 1;
}

static __attribute__((noinline, noipa)) int run_fpr_layout_probe(void) {
    recomp_context ctx;
    memset(&ctx, 0, sizeof(ctx));

    /* FR=0: each odd single register aliases the upper half of its predecessor. */
    ctx.f0.u32h = UINT32_C(0x11223344);
    ctx.f0.u32l = UINT32_C(0x55667788);
    ctx.f_odd = &ctx.f0.u32h;
    ctx.f_odd[(1 - 1) * 2] = UINT32_C(0xA1B2C3D4);
    CHECK_U32("FPR_FR0_ODD_F1", ctx.f0.u32h, UINT32_C(0xA1B2C3D4));
    CHECK_U32("FPR_FR0_EVEN_F0", ctx.f0.u32l, UINT32_C(0x55667788));

    /* FR=1: odd singles use the low word of their own 64-bit register. */
    ctx.f1.u32h = UINT32_C(0x10293847);
    ctx.f1.u32l = UINT32_C(0x56473829);
    ctx.f_odd = &ctx.f1.u32l;
    ctx.f_odd[(1 - 1) * 2] = UINT32_C(0xDEADBEEF);
    CHECK_U32("FPR_FR1_ODD_F1", ctx.f1.u32l, UINT32_C(0xDEADBEEF));
    CHECK_U32("FPR_FR1_HIGH_F1_UNCHANGED", ctx.f1.u32h,
              UINT32_C(0x10293847));

    /* Even and full-width views must retain their exact bit patterns. */
    ctx.f2.u64 = UINT64_C(0x1122334455667788);
    CHECK_U32("FPR_U64_HIGH_WORD", ctx.f2.u32h, UINT32_C(0x11223344));
    CHECK_U32("FPR_U64_LOW_WORD", ctx.f2.u32l, UINT32_C(0x55667788));
    uint32_t float_high_bits = 0;
    uint32_t float_low_bits = 0;
    memcpy(&float_high_bits, &ctx.f2.fh, sizeof(float_high_bits));
    memcpy(&float_low_bits, &ctx.f2.fl, sizeof(float_low_bits));
    CHECK_U32("FPR_FLOAT_HIGH_BITS", float_high_bits, UINT32_C(0x11223344));
    CHECK_U32("FPR_FLOAT_LOW_BITS", float_low_bits, UINT32_C(0x55667788));

    return 1;
}

static __attribute__((noinline, noipa)) int run_rsp_dmem_probe(void) {
    static const uint8_t expected_word[4] = {0x11, 0x22, 0x33, 0x44};
    memset(rsp_dmem_probe, 0, sizeof(rsp_dmem_probe));

    for (uint32_t i = 0; i < 4; ++i) {
        n64_rsp_dmem_store_u8(rsp_dmem_probe, 0, 0x100 + i,
                              expected_word[i]);
    }

    CHECK_U32("RSP_DMEM_BYTE_0",
        n64_rsp_dmem_load_u8(rsp_dmem_probe, 0, 0x100), 0x11);
    CHECK_U32("RSP_DMEM_BYTE_3",
        n64_rsp_dmem_load_u8(rsp_dmem_probe, 0, 0x103), 0x44);
    CHECK_U32("RSP_DMEM_WORD",
        n64_rsp_dmem_load_u32(rsp_dmem_probe, 0, 0x100),
        UINT32_C(0x11223344));
    CHECK_U32("RSP_DMEM_HALF_HI",
        n64_rsp_dmem_load_u16(rsp_dmem_probe, 0, 0x100),
        UINT32_C(0x1122));
    CHECK_U32("RSP_DMEM_HALF_LO",
        n64_rsp_dmem_load_u16(rsp_dmem_probe, 0, 0x102),
        UINT32_C(0x3344));

    n64_rsp_dmem_store_u8(rsp_dmem_probe, 0, 0x200, 0x80);
    n64_rsp_dmem_store_u8(rsp_dmem_probe, 0, 0x201, 0x01);
    CHECK_U32("RSP_DMEM_SIGNED_BYTE",
        (uint32_t)(int32_t)n64_rsp_dmem_load_s8(rsp_dmem_probe, 0, 0x200),
        UINT32_C(0xFFFFFF80));
    CHECK_U32("RSP_DMEM_SIGNED_HALF",
        (uint32_t)n64_rsp_dmem_load_s16(rsp_dmem_probe, 0, 0x200),
        UINT32_C(0xFFFF8001));

    n64_rsp_dmem_store_u16_low(rsp_dmem_probe, 0, 0x202,
                               UINT32_C(0xA1B2C3D4));
    CHECK_U32("RSP_DMEM_HALF_STORE_BYTE_0",
        n64_rsp_dmem_load_u8(rsp_dmem_probe, 0, 0x202), 0xC3);
    CHECK_U32("RSP_DMEM_HALF_STORE_BYTE_1",
        n64_rsp_dmem_load_u8(rsp_dmem_probe, 0, 0x203), 0xD4);
    CHECK_U32("RSP_DMEM_HALF_STORE_VALUE",
        n64_rsp_dmem_load_u16(rsp_dmem_probe, 0, 0x202),
        UINT32_C(0xC3D4));

    n64_rsp_dmem_store_u32(rsp_dmem_probe, 0x10, 0x300,
                           UINT32_C(0xDEADBEEF));
    CHECK_U32("RSP_DMEM_WORD_STORE",
        n64_rsp_dmem_load_u32(rsp_dmem_probe, 0x10, 0x300),
        UINT32_C(0xDEADBEEF));

    n64_rsp_dmem_store_u8(rsp_dmem_probe, 0, 0xFFE, 0x11);
    n64_rsp_dmem_store_u8(rsp_dmem_probe, 0, 0xFFF, 0x22);
    n64_rsp_dmem_store_u8(rsp_dmem_probe, 0, 0x1000, 0x33);
    n64_rsp_dmem_store_u8(rsp_dmem_probe, 0, 0x1001, 0x44);
    CHECK_U32("RSP_DMEM_WRAP_BYTE_0",
        n64_rsp_dmem_load_u8(rsp_dmem_probe, 0, 0x000), 0x33);
    CHECK_U32("RSP_DMEM_WRAP_BYTE_1",
        n64_rsp_dmem_load_u8(rsp_dmem_probe, 0, 0x001), 0x44);
    CHECK_U32("RSP_DMEM_WRAP_WORD",
        n64_rsp_dmem_load_u32(rsp_dmem_probe, 0, 0xFFE),
        UINT32_C(0x11223344));

    return 1;
}

/*
 * This validates the big-endian byte/halfword lane mapping against the pinned
 * RSP::r128 accessor methods compiled separately from the exact upstream
 * union declaration. This reference check is not an RSP instruction test.
 */
static __attribute__((noinline, noipa)) int run_rsp_vector_layout_probe(void) {
    static const uint8_t expected_bytes[16] = {
        0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
        0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF
    };
    static const uint16_t expected_halfwords[8] = {
        0x0011, 0x2233, 0x4455, 0x6677,
        0x8899, 0xAABB, 0xCCDD, 0xEEFF
    };

    /* Native big-endian order: logical lanes 0..7 occupy the first word. */
    rsp_vector_words[0] = UINT64_C(0x0011223344556677);
    rsp_vector_words[1] = UINT64_C(0x8899AABBCCDDEEFF);

    for (uint32_t i = 0; i < 16; ++i) {
        CHECK_U32("RSP_VREG_BYTE",
            n64_rsp_vector_load_u8(rsp_vector_words, i),
            expected_bytes[i]);
    }
    for (uint32_t i = 0; i < 8; ++i) {
        CHECK_U32("RSP_VREG_HALF",
            n64_rsp_vector_load_u16(rsp_vector_words, i),
            expected_halfwords[i]);
    }

    CHECK_U32("RSP_VREG_BYTE_LANE_0_INDEX",
        n64_rsp_vector_byte_storage_index(0),
        0);
    CHECK_U32("RSP_VREG_BYTE_LANE_15_INDEX",
        n64_rsp_vector_byte_storage_index(15),
        15);
    CHECK_U32("RSP_VREG_HALF_LANE_0_INDEX",
        n64_rsp_vector_half_storage_index(0),
        0);
    CHECK_U32("RSP_VREG_HALF_LANE_7_INDEX",
        n64_rsp_vector_half_storage_index(7),
        7);

    n64_rsp_vector_store_u8(rsp_vector_words, 0, 0xA0);
    CHECK_U32("RSP_VREG_STORE_BYTE_HIGH",
        n64_rsp_vector_load_u8(rsp_vector_words, 0), 0xA0);
    CHECK_U64("RSP_VREG_STORE_BYTE_HIGH_WORD",
        rsp_vector_words[0], UINT64_C(0xA011223344556677));

    n64_rsp_vector_store_u8(rsp_vector_words, 15, 0x0F);
    CHECK_U32("RSP_VREG_STORE_BYTE_LOW",
        n64_rsp_vector_load_u8(rsp_vector_words, 15), 0x0F);
    CHECK_U64("RSP_VREG_STORE_BYTE_LOW_WORD",
        rsp_vector_words[1], UINT64_C(0x8899AABBCCDDEE0F));

    n64_rsp_vector_store_u16(rsp_vector_words, 0, UINT16_C(0x1357));
    CHECK_U32("RSP_VREG_STORE_HALF_HIGH",
        n64_rsp_vector_load_u16(rsp_vector_words, 0), UINT32_C(0x1357));
    n64_rsp_vector_store_u16(rsp_vector_words, 7, UINT16_C(0x2468));
    CHECK_U32("RSP_VREG_STORE_HALF_LOW",
        n64_rsp_vector_load_u16(rsp_vector_words, 7), UINT32_C(0x2468));

    return 1;
}

int main(void) {
    set_probe_stage('S', 'T', 'A', 'R');
    probe_start_marker();

    if (!run_memory_probe() || !run_segmented_probe() || !run_fpr_layout_probe() ||
        !run_rsp_dmem_probe() || !run_rsp_vector_layout_probe()) {
        set_probe_stage('F', 'A', 'I', 'L');
        probe_fail_marker();
        for (;;) {
            __asm__ volatile("nop");
        }
    }

    const int rsp_dmem_result = run_pinned_rsp_dmem_accessor_probe();
    if (rsp_dmem_result != 0) {
        (void)fail_u32("PINNED_RSP_DMEM", (uint32_t)rsp_dmem_result, 0);
        set_probe_stage('F', 'A', 'I', 'L');
        probe_fail_marker();
        for (;;) {
            __asm__ volatile("nop");
        }
    }

    const int rsp_r128_result = run_pinned_rsp_r128_accessor_probe();
    if (rsp_r128_result != 0) {
        (void)fail_u32("PINNED_RSP_R128", (uint32_t)rsp_r128_result, 0);
        set_probe_stage('F', 'A', 'I', 'L');
        probe_fail_marker();
        for (;;) {
            __asm__ volatile("nop");
        }
    }

    set_probe_stage('P', 'A', 'S', 'S');
    probe_pass_marker();
    for (;;) {
        __asm__ volatile("nop");
    }
    return 0;
}
