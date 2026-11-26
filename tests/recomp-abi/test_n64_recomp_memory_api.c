#include "n64_recomp_memory_api.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

#define N64_ADDR(address) n64_segmented_sign_extend((uint32_t)(address))

typedef struct mmio_test_state {
    unsigned reads;
    unsigned writes;
    uint64_t last_write;
    uint32_t last_address;
    uint8_t last_width;
} mmio_test_state;

typedef struct guest_object {
    uint32_t first;
    uint32_t second;
} guest_object;

static uint8_t rdram[0x4000];
static uint8_t extended[0x2000];
static uint8_t mod_ram[0x100];
static uint8_t heap[0x200];
static uint8_t rom[16];

static int mmio_access(
    void *context,
    uint32_t address,
    uint8_t width,
    n64_segmented_access access,
    uint64_t *value)
{
    mmio_test_state *state = (mmio_test_state *)context;
    state->last_address = address;
    state->last_width = width;
    if (access == N64_SEGMENTED_ACCESS_READ) {
        ++state->reads;
        *value = width == 8
            ? UINT64_C(0xA1B2C3D4E5F60718)
            : UINT32_C(0xA1B2C3D4);
    } else {
        ++state->writes;
        state->last_write = *value;
    }
    return 0;
}

static int rom_read(
    void *context, uint32_t offset, uint8_t *destination, size_t length)
{
    (void)context;
    if (offset > sizeof(rom) || length > sizeof(rom) - offset) return -1;
    memcpy(destination, rom + offset, length);
    return 0;
}

int main(void)
{
    n64_segmented_memory memory;
    n64_recomp_memory_handle handle;
    mmio_test_state callbacks;
    uint8_t *token;
    uint64_t value;
    uint64_t try_value;
    uint32_t try_word;
    int8_t try_signed_byte;
    guest_object *object;

    memset(&memory, 0, sizeof(memory));
    memset(&callbacks, 0, sizeof(callbacks));
    memset(rdram, 0, sizeof(rdram));
    memset(extended, 0, sizeof(extended));
    memset(mod_ram, 0, sizeof(mod_ram));
    memset(heap, 0, sizeof(heap));

    rom[0] = 0xDE;
    rom[1] = 0xAD;
    rom[2] = 0xBE;
    rom[3] = 0xEF;

    memory.rdram = rdram;
    memory.rdram_size = sizeof(rdram);
    memory.extended = extended;
    memory.extended_size = sizeof(extended);
    memory.mod_ram = mod_ram;
    memory.mod_ram_size = sizeof(mod_ram);
    memory.heap = heap;
    memory.heap_size = sizeof(heap);
    memory.rom_size = sizeof(rom);
    memory.rom_read = rom_read;
    memory.mmio_access = mmio_access;
    memory.callback_context = &callbacks;

    assert(n64_segmented_memory_validate(&memory) == N64_SEGMENTED_OK);
    n64_recomp_memory_handle_init(&handle, &memory, NULL, NULL);
    token = n64_recomp_memory_token(&handle);
    assert(token == (uint8_t *)(void *)&handle);
    assert(n64_recomp_memory_from_token(token) == &handle);

    /*
     * Status-returning reads distinguish a valid zero from a memory fault.
     * The output variable must remain unchanged on every failed access.
     */
    try_word = UINT32_C(0xDEADBEEF);
    assert(n64_recomp_try_load_u32(
               token, N64_ADDR(0x80000100), &try_word) == N64_SEGMENTED_OK);
    assert(try_word == UINT32_C(0x00000000)); /* Initial RDRAM word is zero. */
    /* Verify a nonzero value separately after the normal store below. */

    try_word = UINT32_C(0xCAFEBABE);
    assert(n64_recomp_try_load_u32(
               token, N64_ADDR(0x80004000), &try_word) ==
           N64_SEGMENTED_UNMAPPED_ADDRESS);
    assert(try_word == UINT32_C(0xCAFEBABE));
    /* Per-call status is returned directly; no shared sticky error is written. */
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_OK);

    try_value = UINT64_C(0x0123456789ABCDEF);
    assert(n64_recomp_try_load(
               token, N64_ADDR(0x80003FFF), 2, &try_value) ==
           N64_SEGMENTED_RANGE_CROSSES_REGION);
    assert(try_value == UINT64_C(0x0123456789ABCDEF));

    try_value = UINT64_C(0x0123456789ABCDEF);
    assert(n64_recomp_try_load(
               token, N64_ADDR(0x80000100), 3, &try_value) ==
           N64_SEGMENTED_UNSUPPORTED_WIDTH);
    assert(try_value == UINT64_C(0x0123456789ABCDEF));

    assert(n64_recomp_try_load_u32(
               token, N64_ADDR(0x80000100), NULL) ==
           N64_SEGMENTED_INVALID_ARGUMENT);

    assert(n64_recomp_try_store_u32(
               token, N64_ADDR(0x80000110), UINT32_C(0x0F0E0D0C)) ==
           N64_SEGMENTED_OK);
    try_word = 0;
    assert(n64_recomp_try_load_u32(
               token, N64_ADDR(0x80000110), &try_word) == N64_SEGMENTED_OK);
    assert(try_word == UINT32_C(0x0F0E0D0C));

    assert(n64_recomp_try_store_u32(
               token, N64_ADDR(0xB0000004), UINT32_C(0xBAD0BAD0)) ==
           N64_SEGMENTED_READ_ONLY);
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_OK);

    assert(n64_recomp_try_store_u32(
               token, N64_ADDR(0x80004000), UINT32_C(0xBAD0BAD0)) ==
           N64_SEGMENTED_UNMAPPED_ADDRESS);
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_OK);

    assert(n64_recomp_try_store(
               token, N64_ADDR(0x80003FFF), 2, UINT16_C(0x1234)) ==
           N64_SEGMENTED_RANGE_CROSSES_REGION);
    assert(n64_recomp_try_store(
               token, N64_ADDR(0x80000110), 3, UINT32_C(0x12345678)) ==
           N64_SEGMENTED_UNSUPPORTED_WIDTH);

    /* Generated load/store functions operate on guest addresses, not offsets. */
    assert(n64_recomp_store_u32(token, N64_ADDR(0x80000100),
                                UINT32_C(0x12345678)) == N64_SEGMENTED_OK);
    assert(n64_recomp_load_u32(token, N64_ADDR(0x80000100)) ==
           UINT32_C(0x12345678));
    assert(n64_recomp_try_load_u32(
               token, N64_ADDR(0x80000100), &try_word) == N64_SEGMENTED_OK);
    assert(try_word == UINT32_C(0x12345678));
    assert(n64_recomp_load_s32(token, N64_ADDR(0x80000100)) ==
           (uint64_t)(int64_t)INT32_C(0x12345678));

    assert(n64_recomp_store_u8(token, N64_ADDR(0x80000104), 0x80) ==
           N64_SEGMENTED_OK);
    assert(n64_recomp_load_s8(token, N64_ADDR(0x80000104)) ==
           UINT64_C(0xFFFFFFFFFFFFFF80));
    assert(n64_recomp_load_u8(token, N64_ADDR(0x80000104)) == 0x80);
    assert(n64_recomp_try_load_s8(
               token, N64_ADDR(0x80000104), &try_signed_byte) ==
           N64_SEGMENTED_OK);
    assert(try_signed_byte == INT8_MIN);

    assert(n64_recomp_store_u16(token, N64_ADDR(0x80800010), 0xBEEF) ==
           N64_SEGMENTED_OK);
    assert(n64_recomp_load_u16(token, N64_ADDR(0x80800010)) == 0xBEEF);

    assert(n64_recomp_store_u64(token, N64_ADDR(0x81000100),
                                UINT64_C(0x1029384756ABCDEF)) == N64_SEGMENTED_OK);
    assert(n64_recomp_load_u64(token, N64_ADDR(0x81000100)) ==
           UINT64_C(0x1029384756ABCDEF));

    /* The TO_PTR bridge maps full objects in all host-backed RAM segments. */
    object = N64_RECOMP_TO_PTR(guest_object, token, N64_ADDR(0x80000200));
    assert(object == (guest_object *)(void *)(rdram + 0x200));
    /* Host is little-endian: use typed N64 stores, not native struct writes. */
    assert(n64_recomp_store_u32(token, N64_ADDR(0x80000200),
                                UINT32_C(0xCAFEBABE)) == N64_SEGMENTED_OK);
    assert(n64_recomp_store_u32(token, N64_ADDR(0x80000204),
                                UINT32_C(0x0BADF00D)) == N64_SEGMENTED_OK);
    assert(n64_recomp_load_u32(token, N64_ADDR(0x80000200)) ==
           UINT32_C(0xCAFEBABE));
    assert(n64_recomp_load_u32(token, N64_ADDR(0x80000204)) ==
           UINT32_C(0x0BADF00D));

    assert(N64_RECOMP_TO_PTR_VOID(token, N64_ADDR(0x81000100)) == heap);
    assert(N64_RECOMP_TO_PTR_VOID(token, N64_ADDR(0xA0000100)) == rdram + 0x100);
    assert(N64_RECOMP_TO_PTR(guest_object, token, N64_ADDR(0x80800010)) ==
           (guest_object *)(void *)(extended + 0x10));

    /* MMIO is accessed by the typed callback, never converted into a C pointer. */
    value = n64_recomp_load_u32(token, N64_ADDR(0xA4600010));
    assert(value == UINT32_C(0xA1B2C3D4));
    assert(callbacks.reads == 1);
    assert(callbacks.last_address == UINT32_C(0xA4600010));
    assert(callbacks.last_width == 4);
    assert(n64_recomp_store_u32(token, N64_ADDR(0xA4600010),
                                UINT32_C(0xAABBCCDD)) == N64_SEGMENTED_OK);
    assert(callbacks.writes == 1);
    assert(callbacks.last_write == UINT32_C(0xAABBCCDD));

    assert(n64_recomp_to_host_pointer(token, N64_ADDR(0xA4600010),
                                      sizeof(uint32_t)) == NULL);
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_NOT_RAM_BACKED);
    /* A successful typed MMIO read clears the previous TO_PTR error. */
    value = n64_recomp_load_u32(token, N64_ADDR(0xA4600010));
    assert(value == UINT32_C(0xA1B2C3D4));
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_OK);

    assert(n64_recomp_to_host_pointer(token, N64_ADDR(0xB0000000),
                                      sizeof(uint32_t)) == NULL);
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_NOT_RAM_BACKED);

    /* Unbacked guest addresses report an error instead of forming an OOB pointer. */
    assert(n64_recomp_to_host_pointer(token, N64_ADDR(0x80004000), 4) == NULL);
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_UNMAPPED_ADDRESS);
    assert(n64_recomp_load_u32(token, N64_ADDR(0x80004000)) == 0);
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_UNMAPPED_ADDRESS);
    /* A valid read clears the previous failed-load state. */
    assert(n64_recomp_load_u32(token, N64_ADDR(0x80000100)) ==
           UINT32_C(0x12345678));
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_OK);

    assert(n64_recomp_store_u32(token, N64_ADDR(0x80003FFF), 0x1234) ==
           N64_SEGMENTED_RANGE_CROSSES_REGION);
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_RANGE_CROSSES_REGION);
    assert(n64_recomp_store_u32(token, N64_ADDR(0x80000108), 0x87654321) ==
           N64_SEGMENTED_OK);
    assert(n64_recomp_memory_last_error(token) == N64_SEGMENTED_OK);

    puts("Opaque N64Recomp memory-context adapter: PASS");
    return 0;
}
