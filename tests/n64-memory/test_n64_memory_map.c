#include "n64_memory_map.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #condition); \
        return 1; \
    } \
} while (0)

typedef struct TestContext {
    uint8_t mmio_registers[64];
    uint32_t mmio_calls;
    uint32_t fault_calls;
    N64MemoryStatus last_fault;
    uint64_t last_fault_raw;
    uint32_t last_fault_normalized;
    size_t last_fault_width;
    N64MemoryAccess last_fault_access;
    int mmio_enabled;
} TestContext;

static int test_mmio(
    void *user,
    uint32_t device_address,
    size_t width,
    N64MemoryAccess access,
    uint64_t *value) {
    TestContext *context = (TestContext *)user;
    uint32_t offset;
    uint64_t result = 0u;
    size_t i;

    if (context == NULL || value == NULL || !context->mmio_enabled ||
        device_address < UINT32_C(0xA4600000)) {
        return 0;
    }

    offset = device_address - UINT32_C(0xA4600000);
    if ((uint64_t)offset + width > sizeof(context->mmio_registers)) {
        return 0;
    }

    ++context->mmio_calls;
    if (access == N64_MEMORY_ACCESS_READ) {
        for (i = 0u; i < width; ++i) {
            result = (result << 8) | context->mmio_registers[offset + i];
        }
        *value = result;
    } else {
        for (i = 0u; i < width; ++i) {
            size_t shift = (width - 1u - i) * 8u;
            context->mmio_registers[offset + i] = (uint8_t)(*value >> shift);
        }
    }

    return 1;
}

static void test_fault(
    void *user,
    N64MemoryStatus status,
    uint64_t raw_address,
    uint32_t normalized_address,
    size_t width,
    N64MemoryAccess access) {
    TestContext *context = (TestContext *)user;
    if (context == NULL) {
        return;
    }

    ++context->fault_calls;
    context->last_fault = status;
    context->last_fault_raw = raw_address;
    context->last_fault_normalized = normalized_address;
    context->last_fault_width = width;
    context->last_fault_access = access;
}

static int expect_status(
    N64MemoryStatus actual,
    N64MemoryStatus expected,
    const char *test_name) {
    if (actual != expected) {
        fprintf(stderr, "FAIL %s: got %s, expected %s\n",
                test_name,
                n64_memory_status_string(actual),
                n64_memory_status_string(expected));
        return 0;
    }
    return 1;
}

int main(void) {
    uint8_t rdram[0x100] = {0};
    uint8_t runtime[0x80] = {0};
    uint8_t mem1_heap[0x100] = {0};
    uint8_t mem2_heap_backing[0x100] = {0};
    uint8_t readonly[8] = {0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80};
    N64MemoryRegion regions[] = {
        { UINT32_C(0x80000000), sizeof(rdram), rdram,
          N64_MEMORY_PERM_READ | N64_MEMORY_PERM_WRITE,
          N64_MEMORY_REGION_RDRAM, "N64 RDRAM" },
        { UINT32_C(0x80800000), sizeof(runtime), runtime,
          N64_MEMORY_PERM_READ | N64_MEMORY_PERM_WRITE,
          N64_MEMORY_REGION_RUNTIME, "PI/runtime scratch" },
        { UINT32_C(0x81000000), sizeof(mem1_heap), mem1_heap,
          N64_MEMORY_PERM_READ | N64_MEMORY_PERM_WRITE,
          N64_MEMORY_REGION_MEM1_HEAP, "MEM1 heap" },
        /*
         * Guest extension is KSEG0 0x81800000+, but the host pointer is
         * expected to come from Wii MEM2 (or a test array here). It is not
         * guest address 0x90000000 and does not claim KSEG1/ROM space.
         */
        { N64_MEMORY_MEM2_HEAP_GUEST_BASE, sizeof(mem2_heap_backing), mem2_heap_backing,
          N64_MEMORY_PERM_READ | N64_MEMORY_PERM_WRITE,
          N64_MEMORY_REGION_MEM2_HEAP, "MEM2-backed heap" },
        { UINT32_C(0x82000000), sizeof(readonly), readonly,
          N64_MEMORY_PERM_READ, N64_MEMORY_REGION_OTHER, "read-only test region" }
    };
    TestContext context;
    N64MemoryMap map;
    N64MemoryStatus status;
    uint64_t value;
    uint32_t guest;
    uint8_t *pointer = NULL;
    uint8_t *before_pointer;
    N64MemoryRegion invalid_regions[6];

    memset(&context, 0, sizeof(context));
    context.mmio_enabled = 1;
    map.regions = regions;
    map.region_count = sizeof(regions) / sizeof(regions[0]);
    map.mmio = test_mmio;
    map.fault = test_fault;
    map.user = &context;

    CHECK(expect_status(n64_memory_map_validate(&map),
                        N64_MEMORY_STATUS_OK, "map validates"));

    /* A word written via KSEG0 is stored in N64 big-endian byte order. */
    status = n64_memory_write(&map, UINT64_C(0x80000010), 4u, UINT64_C(0x12345678));
    CHECK(expect_status(status, N64_MEMORY_STATUS_OK, "KSEG0 BE word write"));
    CHECK(rdram[0x10] == 0x12 && rdram[0x11] == 0x34 &&
          rdram[0x12] == 0x56 && rdram[0x13] == 0x78);

    value = 0u;
    CHECK(expect_status(n64_memory_read(&map, UINT64_C(0xA0000010), 4u, &value),
                        N64_MEMORY_STATUS_OK, "KSEG1 RDRAM alias read"));
    CHECK(value == UINT64_C(0x12345678));

    value = 0u;
    CHECK(expect_status(n64_memory_read(&map, UINT64_C(0x00000010), 4u, &value),
                        N64_MEMORY_STATUS_OK, "physical RDRAM alias read"));
    CHECK(value == UINT64_C(0x12345678));

    value = 0u;
    CHECK(expect_status(n64_memory_read(&map, UINT64_C(0xFFFFFFFF80000010), 4u, &value),
                        N64_MEMORY_STATUS_OK, "sign-extended KSEG0 read"));
    CHECK(value == UINT64_C(0x12345678));

    CHECK(expect_status(n64_memory_write(&map, UINT64_C(0xA0000020), 2u, UINT64_C(0xBEEF)),
                        N64_MEMORY_STATUS_OK, "KSEG1 halfword write"));
    CHECK(rdram[0x20] == 0xBE && rdram[0x21] == 0xEF);

    CHECK(expect_status(n64_memory_write(&map, UINT64_C(0x80000028), 1u, UINT64_C(0xA5)),
                        N64_MEMORY_STATUS_OK, "byte write"));
    value = 0u;
    CHECK(expect_status(n64_memory_read(&map, UINT64_C(0x80000028), 1u, &value),
                        N64_MEMORY_STATUS_OK, "byte read"));
    CHECK(value == UINT64_C(0xA5));

    CHECK(expect_status(n64_memory_write(&map, UINT64_C(0x80000030), 8u,
                                         UINT64_C(0x0123456789ABCDEF)),
                        N64_MEMORY_STATUS_OK, "doubleword write"));
    value = 0u;
    CHECK(expect_status(n64_memory_read(&map, UINT64_C(0xA0000030), 8u, &value),
                        N64_MEMORY_STATUS_OK, "doubleword alias read"));
    CHECK(value == UINT64_C(0x0123456789ABCDEF));

    /* Runtime scratch and MEM1/MEM2-backed heaps are separate mapped regions. */
    CHECK(expect_status(n64_memory_write(&map, UINT64_C(0x80800010), 4u,
                                         UINT64_C(0xCAFEBABE)),
                        N64_MEMORY_STATUS_OK, "runtime scratch write"));
    CHECK(runtime[0x10] == 0xCA && runtime[0x13] == 0xBE);

    CHECK(expect_status(n64_memory_write(&map, UINT64_C(0x81000020), 4u,
                                         UINT64_C(0x11223344)),
                        N64_MEMORY_STATUS_OK, "MEM1 heap write"));
    CHECK(expect_status(n64_memory_write(&map, UINT64_C(0x81800010), 4u,
                                         UINT64_C(0x55667788)),
                        N64_MEMORY_STATUS_OK, "MEM2-backed heap write"));
    CHECK(mem1_heap[0x20] == 0x11 && mem2_heap_backing[0x10] == 0x55);

    CHECK(expect_status(n64_memory_host_to_guest(&map, &mem1_heap[0x20], 4u, &guest),
                        N64_MEMORY_STATUS_OK, "reverse MEM1 pointer mapping"));
    CHECK(guest == UINT32_C(0x81000020));
    CHECK(expect_status(n64_memory_host_to_guest(&map, &mem2_heap_backing[0x10], 4u, &guest),
                        N64_MEMORY_STATUS_OK, "reverse MEM2 pointer mapping"));
    CHECK(guest == UINT32_C(0x81800010));

    CHECK(expect_status(n64_memory_translate(&map, UINT64_C(0x81800010), 4u,
                                             N64_MEMORY_ACCESS_READ, &pointer),
                        N64_MEMORY_STATUS_OK, "translate MEM2-backed heap"));
    CHECK(pointer == &mem2_heap_backing[0x10]);

    /* The N64 KSEG1/ROM window is not stolen for the host's MEM2 allocation. */
    pointer = NULL;
    CHECK(expect_status(n64_memory_translate(&map, UINT64_C(0xB0000010), 4u,
                                             N64_MEMORY_ACCESS_READ, &pointer),
                        N64_MEMORY_STATUS_MMIO, "KSEG1 ROM/device window"));
    CHECK(pointer == NULL);

    /* Physical PI register address dispatches through the uncached MMIO callback. */
    CHECK(expect_status(n64_memory_write(&map, UINT64_C(0x04600000), 4u,
                                         UINT64_C(0xDEADBEEF)),
                        N64_MEMORY_STATUS_OK, "physical PI MMIO write"));
    CHECK(context.mmio_calls == 1u);
    CHECK(context.mmio_registers[0] == 0xDE &&
          context.mmio_registers[1] == 0xAD &&
          context.mmio_registers[2] == 0xBE &&
          context.mmio_registers[3] == 0xEF);
    value = 0u;
    CHECK(expect_status(n64_memory_read(&map, UINT64_C(0xA4600000), 4u, &value),
                        N64_MEMORY_STATUS_OK, "KSEG1 PI MMIO read"));
    CHECK(value == UINT64_C(0xDEADBEEF));

    /* Unknown MMIO is never returned as a pointer or silently treated as RAM. */
    map.mmio = NULL;
    CHECK(expect_status(n64_memory_read(&map, UINT64_C(0xA4800000), 4u, &value),
                        N64_MEMORY_STATUS_UNHANDLED_MMIO, "unhandled MMIO"));
    map.mmio = test_mmio;

    /* Invalid 64-bit values are rejected; no blind low-32 truncation. */
    before_pointer = NULL;
    CHECK(expect_status(n64_memory_translate(&map, UINT64_C(0x0000000180000000), 4u,
                                             N64_MEMORY_ACCESS_READ, &before_pointer),
                        N64_MEMORY_STATUS_BAD_ADDRESS_EXTENSION, "bad address extension"));
    CHECK(before_pointer == NULL);

    /* Holes and accesses crossing one region boundary are rejected. */
    CHECK(expect_status(n64_memory_translate(&map, UINT64_C(0x88000000), 4u,
                                             N64_MEMORY_ACCESS_READ, &pointer),
                        N64_MEMORY_STATUS_UNMAPPED, "unmapped KSEG0 hole"));
    CHECK(expect_status(n64_memory_translate(&map, UINT64_C(0x800000FE), 4u,
                                             N64_MEMORY_ACCESS_READ, &pointer),
                        N64_MEMORY_STATUS_CROSSES_REGION, "crossing RDRAM end"));

    /* Read-only regions reject writes while permitting reads. */
    value = 0u;
    CHECK(expect_status(n64_memory_read(&map, UINT64_C(0x82000000), 4u, &value),
                        N64_MEMORY_STATUS_OK, "read-only region read"));
    CHECK(value == UINT64_C(0x10203040));
    CHECK(expect_status(n64_memory_write(&map, UINT64_C(0x82000000), 4u, UINT64_C(0x01020304)),
                        N64_MEMORY_STATUS_ACCESS_DENIED, "read-only region write"));

    /* Fault reporting preserves original address, canonical address, width and access. */
    CHECK(context.fault_calls >= 3u);
    CHECK(context.last_fault == N64_MEMORY_STATUS_ACCESS_DENIED);
    CHECK(context.last_fault_raw == UINT64_C(0x82000000));
    CHECK(context.last_fault_normalized == UINT32_C(0x82000000));
    CHECK(context.last_fault_width == 4u);
    CHECK(context.last_fault_access == N64_MEMORY_ACCESS_WRITE);

    /* Map validator rejects guest-region overlap and 32-bit address overflow. */
    memcpy(invalid_regions, regions, sizeof(regions));
    invalid_regions[5] = regions[0];
    invalid_regions[5].guest_base = UINT32_C(0x80000080);
    invalid_regions[5].size = 0x20u;
    map.regions = invalid_regions;
    map.region_count = 6u;
    CHECK(expect_status(n64_memory_map_validate(&map), N64_MEMORY_STATUS_BAD_MAP,
                        "overlapping guest regions"));

    invalid_regions[5].guest_base = UINT32_C(0xFFFFFFF0);
    invalid_regions[5].size = 0x40u;
    CHECK(expect_status(n64_memory_map_validate(&map), N64_MEMORY_STATUS_BAD_MAP,
                        "guest region wraps past 4 GiB"));

    /* Reverse mapping refuses pointers/spans that cross backing allocations. */
    map.regions = regions;
    map.region_count = sizeof(regions) / sizeof(regions[0]);
    CHECK(expect_status(n64_memory_host_to_guest(&map, &rdram[0xFF], 2u, &guest),
                        N64_MEMORY_STATUS_UNMAPPED, "reverse pointer crosses backing"));

    printf("N64 bounded memory map tests passed\n");
    return 0;
}
