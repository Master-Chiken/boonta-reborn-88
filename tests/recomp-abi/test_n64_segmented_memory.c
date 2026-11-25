#include "n64_segmented_memory.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

#define N64_ADDR(address) n64_segmented_sign_extend((uint32_t)(address))

static uint8_t test_rdram[N64_SEGMENTED_RDRAM_SIZE];
static uint8_t test_extended[N64_SEGMENTED_EXTENDED_SIZE];
static uint8_t test_mod_ram[0x1000];
static uint8_t test_heap[0x2000];
static uint8_t test_rom[64];

typedef struct callback_state {
    uint32_t mmio_address;
    uint8_t mmio_width;
    n64_segmented_access mmio_access;
    uint64_t mmio_value;
    unsigned mmio_calls;
    unsigned rom_calls;
    int fail_mmio;
    int fail_rom;
} callback_state;

static int test_rom_read(
    void *context, uint32_t rom_offset, uint8_t *destination, size_t length)
{
    callback_state *state = (callback_state *)context;

    ++state->rom_calls;
    if (state->fail_rom || rom_offset > sizeof(test_rom) ||
        length > sizeof(test_rom) - rom_offset) {
        return -1;
    }

    memcpy(destination, test_rom + rom_offset, length);
    return 0;
}

static int test_mmio_access(
    void *context,
    uint32_t virtual_address,
    uint8_t width,
    n64_segmented_access access,
    uint64_t *value)
{
    callback_state *state = (callback_state *)context;

    ++state->mmio_calls;
    state->mmio_address = virtual_address;
    state->mmio_width = width;
    state->mmio_access = access;

    if (state->fail_mmio) {
        return -1;
    }

    if (access == N64_SEGMENTED_ACCESS_READ) {
        *value = UINT64_C(0xA1B2C3D4E5F60718);
    } else {
        state->mmio_value = *value;
    }
    return 0;
}

static n64_segmented_memory make_memory(callback_state *state)
{
    n64_segmented_memory memory;

    memset(&memory, 0, sizeof(memory));
    memory.rdram = test_rdram;
    memory.extended = test_extended;
    memory.mod_ram = test_mod_ram;
    memory.mod_ram_size = sizeof(test_mod_ram);
    memory.heap = test_heap;
    memory.heap_size = sizeof(test_heap);
    memory.rom_size = sizeof(test_rom);
    memory.rom_read = test_rom_read;
    memory.mmio_access = test_mmio_access;
    memory.callback_context = state;
    return memory;
}

static void test_configuration_validation(callback_state *state)
{
    n64_segmented_memory memory = make_memory(state);
    n64_segmented_memory invalid = memory;

    assert(n64_segmented_memory_validate(&memory) == N64_SEGMENTED_OK);

    invalid.extended = invalid.rdram + 16;
    assert(n64_segmented_memory_validate(&invalid) ==
           N64_SEGMENTED_INVALID_CONFIGURATION);

    invalid = memory;
    invalid.mod_ram_size =
        (size_t)(N64_SEGMENTED_KSEG0_LIMIT - N64_SEGMENTED_MOD_RAM_BASE) + 1;
    assert(n64_segmented_memory_validate(&invalid) ==
           N64_SEGMENTED_INVALID_CONFIGURATION);

    invalid = memory;
    invalid.rom_read = NULL;
    assert(n64_segmented_memory_validate(&invalid) ==
           N64_SEGMENTED_INVALID_CONFIGURATION);

    invalid = memory;
    invalid.heap = NULL;
    assert(n64_segmented_memory_validate(&invalid) ==
           N64_SEGMENTED_INVALID_CONFIGURATION);

    assert(n64_segmented_memory_validate(NULL) ==
           N64_SEGMENTED_INVALID_ARGUMENT);
}

static void test_rdram_and_kseg1_alias(const n64_segmented_memory *memory)
{
    uint64_t value = 0;
    n64_segmented_span span;

    assert(n64_segmented_write(memory, N64_ADDR(0x80000120), 8,
                               UINT64_C(0x0123456789ABCDEF)) == N64_SEGMENTED_OK);
    assert(test_rdram[0x120] == 0x01);
    assert(test_rdram[0x127] == 0xEF);

    assert(n64_segmented_read(memory, N64_ADDR(0x80000120), 8, &value) ==
           N64_SEGMENTED_OK);
    assert(value == UINT64_C(0x0123456789ABCDEF));

    /* KSEG1 is an alias of the first 8 MiB, not a second RAM bank. */
    assert(n64_segmented_read(memory, N64_ADDR(0xA0000120), 8, &value) ==
           N64_SEGMENTED_OK);
    assert(value == UINT64_C(0x0123456789ABCDEF));

    assert(n64_segmented_resolve(memory, N64_ADDR(0x80000120), 8,
                                 N64_SEGMENTED_ACCESS_READ, &span) ==
           N64_SEGMENTED_OK);
    assert(span.kind == N64_SEGMENTED_REGION_RDRAM);
    assert(span.host_pointer == test_rdram + 0x120);

    assert(n64_segmented_resolve(memory, N64_ADDR(0xA0000120), 8,
                                 N64_SEGMENTED_ACCESS_READ, &span) ==
           N64_SEGMENTED_OK);
    assert(span.kind == N64_SEGMENTED_REGION_RDRAM);
    assert(span.host_pointer == test_rdram + 0x120);
}

static void test_rdram_boundaries(const n64_segmented_memory *memory)
{
    uint64_t value = 0;

    assert(n64_segmented_write(memory, N64_ADDR(0x807FFFFC), 4,
                               UINT32_C(0xA1B2C3D4)) == N64_SEGMENTED_OK);
    assert(n64_segmented_read(memory, N64_ADDR(0x807FFFFC), 4, &value) ==
           N64_SEGMENTED_OK);
    assert(value == UINT32_C(0xA1B2C3D4));

    assert(n64_segmented_read(memory, N64_ADDR(0x807FFFFF), 2, &value) ==
           N64_SEGMENTED_RANGE_CROSSES_REGION);
    assert(n64_segmented_read(memory, N64_ADDR(0xA07FFFFF), 2, &value) ==
           N64_SEGMENTED_RANGE_CROSSES_REGION);

    /* The KSEG1 mirror ends at 0xA0800000; it does not mirror extended RAM. */
    assert(n64_segmented_read(memory, N64_ADDR(0xA0800000), 4, &value) ==
           N64_SEGMENTED_UNMAPPED_ADDRESS);
}

static void test_extended_mod_and_heap(const n64_segmented_memory *memory)
{
    uint64_t value = 0;

    /* The 8–16 MiB extension contains PI handles and patch data. */
    assert(n64_segmented_write(memory, N64_ADDR(0x80800000), 4,
                               UINT32_C(0x80800000)) == N64_SEGMENTED_OK);
    assert(n64_segmented_read(memory, N64_ADDR(0x80800000), 4, &value) ==
           N64_SEGMENTED_OK);
    assert(value == UINT32_C(0x80800000));

    assert(n64_segmented_write(memory, N64_ADDR(0x80801000), 4,
                               UINT32_C(0x50415443)) == N64_SEGMENTED_OK);
    assert(n64_segmented_read(memory, N64_ADDR(0x80801000), 4, &value) ==
           N64_SEGMENTED_OK);
    assert(value == UINT32_C(0x50415443));

    assert(n64_segmented_write(memory, N64_ADDR(0x81000000), 4,
                               UINT32_C(0x4D4F4421)) == N64_SEGMENTED_OK);
    assert(n64_segmented_read(memory, N64_ADDR(0x81000000), 4, &value) ==
           N64_SEGMENTED_OK);
    assert(value == UINT32_C(0x4D4F4421));

    /* Heap starts immediately after mod RAM, just like init_heap(). */
    assert(n64_segmented_write(memory, N64_ADDR(0x81001000), 8,
                               UINT64_C(0x1029384756ABCDEF)) == N64_SEGMENTED_OK);
    assert(n64_segmented_read(memory, N64_ADDR(0x81001000), 8, &value) ==
           N64_SEGMENTED_OK);
    assert(value == UINT64_C(0x1029384756ABCDEF));

    assert(n64_segmented_read(memory, N64_ADDR(0x81000FFF), 2, &value) ==
           N64_SEGMENTED_RANGE_CROSSES_REGION);
    assert(n64_segmented_read(memory, N64_ADDR(0x81002FFF), 2, &value) ==
           N64_SEGMENTED_RANGE_CROSSES_REGION);
    assert(n64_segmented_read(memory, N64_ADDR(0x81100000), 4, &value) ==
           N64_SEGMENTED_UNMAPPED_ADDRESS);
}

static void test_reverse_host_mapping(const n64_segmented_memory *memory)
{
    uint64_t guest = 0;

    assert(n64_segmented_guest_from_host(memory, test_rdram + 0x1234, 8, &guest) ==
           N64_SEGMENTED_OK);
    assert(guest == N64_ADDR(0x80001234));

    assert(n64_segmented_guest_from_host(memory, test_extended + 0x2345, 4, &guest) ==
           N64_SEGMENTED_OK);
    assert(guest == N64_ADDR(0x80802345));

    assert(n64_segmented_guest_from_host(memory, test_mod_ram + 0x20, 16, &guest) ==
           N64_SEGMENTED_OK);
    assert(guest == N64_ADDR(0x81000020));

    assert(n64_segmented_guest_from_host(memory, test_heap + 0x10, 16, &guest) ==
           N64_SEGMENTED_OK);
    assert(guest == N64_ADDR(0x81001010));

    assert(n64_segmented_guest_from_host(
               memory, test_rdram + N64_SEGMENTED_RDRAM_SIZE - 1, 2, &guest) ==
           N64_SEGMENTED_RANGE_CROSSES_REGION);

    assert(n64_segmented_guest_from_host(memory, test_rom, 4, &guest) ==
           N64_SEGMENTED_HOST_POINTER_UNMAPPED);
}

static void test_canonical_addresses(const n64_segmented_memory *memory)
{
    uint64_t value = 0;

    assert(n64_segmented_read(memory, UINT64_C(0x0000000080000000), 4, &value) ==
           N64_SEGMENTED_NONCANONICAL_ADDRESS);
    assert(n64_segmented_read(memory, UINT64_C(0xFFFFFFFF80000000), 4, &value) ==
           N64_SEGMENTED_OK);
    assert(n64_segmented_resolve(memory, N64_ADDR(0x80000000), 4,
                                 (n64_segmented_access)99, &(n64_segmented_span){0}) ==
           N64_SEGMENTED_INVALID_ARGUMENT);
}

static void test_mmio(callback_state *state, const n64_segmented_memory *memory)
{
    uint64_t value = 0;
    n64_segmented_memory no_mmio = *memory;

    assert(n64_segmented_read(memory, N64_ADDR(0xA4600010), 4, &value) ==
           N64_SEGMENTED_OK);
    assert(value == UINT32_C(0xA1B2C3D4));
    assert(state->mmio_calls == 1);
    assert(state->mmio_address == UINT32_C(0xA4600010));
    assert(state->mmio_width == 4);
    assert(state->mmio_access == N64_SEGMENTED_ACCESS_READ);

    assert(n64_segmented_write(memory, N64_ADDR(0xA4600010), 4,
                               UINT32_C(0x12345678)) == N64_SEGMENTED_OK);
    assert(state->mmio_calls == 2);
    assert(state->mmio_value == UINT32_C(0x12345678));
    assert(state->mmio_access == N64_SEGMENTED_ACCESS_WRITE);

    assert(n64_segmented_read(memory, N64_ADDR(0xA4FFFFFE), 4, &value) ==
           N64_SEGMENTED_RANGE_CROSSES_REGION);
    assert(n64_segmented_read(memory, N64_ADDR(0xA2000000), 4, &value) ==
           N64_SEGMENTED_UNMAPPED_ADDRESS);
    assert(n64_segmented_read(memory, N64_ADDR(0xA4600010), 3, &value) ==
           N64_SEGMENTED_UNSUPPORTED_WIDTH);

    no_mmio.mmio_access = NULL;
    assert(n64_segmented_read(&no_mmio, N64_ADDR(0xA4600010), 4, &value) ==
           N64_SEGMENTED_CALLBACK_MISSING);

    state->fail_mmio = 1;
    assert(n64_segmented_read(memory, N64_ADDR(0xA4600010), 4, &value) ==
           N64_SEGMENTED_CALLBACK_FAILED);
    state->fail_mmio = 0;
}

static void test_rom(callback_state *state, const n64_segmented_memory *memory)
{
    uint64_t value = 0;

    assert(n64_segmented_read(memory, N64_ADDR(0xB0000004), 4, &value) ==
           N64_SEGMENTED_OK);
    assert(value == UINT32_C(0x10203040));
    assert(state->rom_calls == 1);

    assert(n64_segmented_write(memory, N64_ADDR(0xB0000004), 4,
                               UINT32_C(0xFFFFFFFF)) == N64_SEGMENTED_READ_ONLY);
    assert(n64_segmented_read(memory, N64_ADDR(0xB000003F), 2, &value) ==
           N64_SEGMENTED_UNMAPPED_ADDRESS);
    assert(n64_segmented_read(memory, N64_ADDR(0xB1000000), 4, &value) ==
           N64_SEGMENTED_UNMAPPED_ADDRESS);

    state->fail_rom = 1;
    assert(n64_segmented_read(memory, N64_ADDR(0xB0000000), 4, &value) ==
           N64_SEGMENTED_CALLBACK_FAILED);
    state->fail_rom = 0;
}

int main(void)
{
    callback_state callbacks;
    n64_segmented_memory memory;

    memset(&callbacks, 0, sizeof(callbacks));
    memset(test_rdram, 0, sizeof(test_rdram));
    memset(test_extended, 0, sizeof(test_extended));
    memset(test_mod_ram, 0, sizeof(test_mod_ram));
    memset(test_heap, 0, sizeof(test_heap));
    memset(test_rom, 0, sizeof(test_rom));

    test_rom[0] = 0xDE;
    test_rom[1] = 0xAD;
    test_rom[2] = 0xBE;
    test_rom[3] = 0xEF;
    test_rom[4] = 0x10;
    test_rom[5] = 0x20;
    test_rom[6] = 0x30;
    test_rom[7] = 0x40;

    memory = make_memory(&callbacks);

    test_configuration_validation(&callbacks);
    test_rdram_and_kseg1_alias(&memory);
    test_rdram_boundaries(&memory);
    test_extended_mod_and_heap(&memory);
    test_reverse_host_mapping(&memory);
    test_canonical_addresses(&memory);
    test_mmio(&callbacks, &memory);
    test_rom(&callbacks, &memory);

    puts("Segmented N64 address-space model: PASS");
    return 0;
}
