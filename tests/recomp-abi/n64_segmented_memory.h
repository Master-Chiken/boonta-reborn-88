#ifndef BOONTA_TESTS_RECOMP_ABI_N64_SEGMENTED_MEMORY_H
#define BOONTA_TESTS_RECOMP_ABI_N64_SEGMENTED_MEMORY_H

/*
 * Clean-room, host-testable address-space model for the N64Recomp runtime.
 *
 * This is a reference adapter, not yet a production replacement for
 * N64Recomp's MEM_* macros. It deliberately separates 32-bit N64 virtual
 * addresses from host pointers and models the runtime's known logical
 * windows without reserving a contiguous 512 MiB host allocation.
 */

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <limits.h>

#define N64_SEGMENTED_RDRAM_BASE       UINT32_C(0x80000000)
#define N64_SEGMENTED_RDRAM_SIZE       ((size_t)8 * 1024 * 1024)
#define N64_SEGMENTED_EXTENDED_BASE    UINT32_C(0x80800000)
#define N64_SEGMENTED_EXTENDED_SIZE    ((size_t)8 * 1024 * 1024)
#define N64_SEGMENTED_MOD_RAM_BASE     UINT32_C(0x81000000)
#define N64_SEGMENTED_KSEG0_LIMIT      UINT32_C(0xA0000000)
#define N64_SEGMENTED_KSEG1_BASE       UINT32_C(0xA0000000)
#define N64_SEGMENTED_KSEG1_RDRAM_END  UINT32_C(0xA0800000)
#define N64_SEGMENTED_MMIO_BASE        UINT32_C(0xA3F00000)
#define N64_SEGMENTED_MMIO_END         UINT32_C(0xA5000000)
#define N64_SEGMENTED_ROM_BASE         UINT32_C(0xB0000000)
#define N64_SEGMENTED_ROM_WINDOW_SIZE  UINT32_C(0x10000000)

typedef enum n64_segmented_result {
    N64_SEGMENTED_OK = 0,
    N64_SEGMENTED_INVALID_ARGUMENT,
    N64_SEGMENTED_INVALID_CONFIGURATION,
    N64_SEGMENTED_NONCANONICAL_ADDRESS,
    N64_SEGMENTED_UNMAPPED_ADDRESS,
    N64_SEGMENTED_RANGE_CROSSES_REGION,
    N64_SEGMENTED_READ_ONLY,
    N64_SEGMENTED_UNSUPPORTED_WIDTH,
    N64_SEGMENTED_CALLBACK_MISSING,
    N64_SEGMENTED_CALLBACK_FAILED,
    N64_SEGMENTED_HOST_POINTER_UNMAPPED
} n64_segmented_result;

typedef enum n64_segmented_region_kind {
    N64_SEGMENTED_REGION_NONE = 0,
    N64_SEGMENTED_REGION_RDRAM,
    N64_SEGMENTED_REGION_EXTENDED,
    N64_SEGMENTED_REGION_MOD_RAM,
    N64_SEGMENTED_REGION_HEAP,
    N64_SEGMENTED_REGION_ROM,
    N64_SEGMENTED_REGION_MMIO
} n64_segmented_region_kind;

typedef enum n64_segmented_access {
    N64_SEGMENTED_ACCESS_READ = 0,
    N64_SEGMENTED_ACCESS_WRITE = 1
} n64_segmented_access;

/*
 * ROM callback copies bytes from the cartridge image at a PI ROM offset.
 * Return zero on success and nonzero on failure.
 */
typedef int (*n64_segmented_rom_read_fn)(
    void *context, uint32_t rom_offset, uint8_t *destination, size_t length);

/*
 * MMIO callback receives a canonical 32-bit KSEG1 register address.
 * value is an input for writes and an output for reads. Values are numeric
 * host integers; byte ordering is handled by the caller's register model.
 * Return zero on success and nonzero on failure.
 */
typedef int (*n64_segmented_mmio_fn)(
    void *context,
    uint32_t virtual_address,
    uint8_t width,
    n64_segmented_access access,
    uint64_t *value);

typedef struct n64_segmented_memory {
    /* Fixed 8 MiB guest RDRAM and fixed 8 MiB extended runtime window. */
    uint8_t *rdram;
    uint8_t *extended;

    /*
     * Variable runtime-owned regions:
     *   mod_ram begins at 0x81000000;
     *   heap immediately follows mod_ram, as in librecomp's init_heap().
     * The supplied host buffers may live in separate MEM1/MEM2 allocations.
     */
    uint8_t *mod_ram;
    size_t mod_ram_size;
    uint8_t *heap;
    size_t heap_size;

    size_t rom_size;
    n64_segmented_rom_read_fn rom_read;
    n64_segmented_mmio_fn mmio_access;
    void *callback_context;
} n64_segmented_memory;

typedef struct n64_segmented_span {
    n64_segmented_region_kind kind;
    uint32_t virtual_address;
    uint32_t region_offset;
    uint8_t *host_pointer; /* Non-NULL only for RAM-backed regions. */
} n64_segmented_span;

static inline uint64_t n64_segmented_sign_extend(uint32_t address)
{
    return (uint64_t)(int64_t)(int32_t)address;
}

static inline bool n64_segmented_width_supported(size_t width)
{
    return width == 1 || width == 2 || width == 4 || width == 8;
}

static inline bool n64_segmented_host_range_valid(const void *pointer, size_t size)
{
    uintptr_t start;

    if (pointer == NULL || size == 0) {
        return false;
    }

    start = (uintptr_t)pointer;
    return size <= (size_t)(UINTPTR_MAX - start);
}

static inline bool n64_segmented_host_ranges_overlap(
    const void *first, size_t first_size, const void *second, size_t second_size)
{
    uintptr_t first_start;
    uintptr_t second_start;
    uintptr_t first_end;
    uintptr_t second_end;

    if (first_size == 0 || second_size == 0) {
        return false;
    }

    if (!n64_segmented_host_range_valid(first, first_size) ||
        !n64_segmented_host_range_valid(second, second_size)) {
        return true;
    }

    first_start = (uintptr_t)first;
    second_start = (uintptr_t)second;
    first_end = first_start + first_size;
    second_end = second_start + second_size;

    return first_start < second_end && second_start < first_end;
}

/*
 * Validate the caller-supplied backing regions once before using the map.
 * No memory is allocated here; the Wii platform layer must choose and supply
 * bounded MEM1/MEM2 buffers explicitly.
 */
static inline n64_segmented_result n64_segmented_memory_validate(
    const n64_segmented_memory *memory)
{
    size_t logical_tail_limit =
        (size_t)(N64_SEGMENTED_KSEG0_LIMIT - N64_SEGMENTED_MOD_RAM_BASE);

    if (memory == NULL || memory->rdram == NULL || memory->extended == NULL) {
        return N64_SEGMENTED_INVALID_ARGUMENT;
    }

    if ((memory->mod_ram_size != 0 && memory->mod_ram == NULL) ||
        (memory->heap_size != 0 && memory->heap == NULL)) {
        return N64_SEGMENTED_INVALID_CONFIGURATION;
    }

    if (memory->mod_ram_size > logical_tail_limit ||
        memory->heap_size > logical_tail_limit - memory->mod_ram_size) {
        return N64_SEGMENTED_INVALID_CONFIGURATION;
    }

    if (memory->rom_size > (size_t)N64_SEGMENTED_ROM_WINDOW_SIZE ||
        (memory->rom_size != 0 && memory->rom_read == NULL)) {
        return N64_SEGMENTED_INVALID_CONFIGURATION;
    }

    if (!n64_segmented_host_range_valid(memory->rdram, N64_SEGMENTED_RDRAM_SIZE) ||
        !n64_segmented_host_range_valid(memory->extended, N64_SEGMENTED_EXTENDED_SIZE)) {
        return N64_SEGMENTED_INVALID_CONFIGURATION;
    }

    if (memory->mod_ram_size != 0 &&
        !n64_segmented_host_range_valid(memory->mod_ram, memory->mod_ram_size)) {
        return N64_SEGMENTED_INVALID_CONFIGURATION;
    }

    if (memory->heap_size != 0 &&
        !n64_segmented_host_range_valid(memory->heap, memory->heap_size)) {
        return N64_SEGMENTED_INVALID_CONFIGURATION;
    }

    if (n64_segmented_host_ranges_overlap(
            memory->rdram, N64_SEGMENTED_RDRAM_SIZE,
            memory->extended, N64_SEGMENTED_EXTENDED_SIZE) ||
        n64_segmented_host_ranges_overlap(
            memory->rdram, N64_SEGMENTED_RDRAM_SIZE,
            memory->mod_ram, memory->mod_ram_size) ||
        n64_segmented_host_ranges_overlap(
            memory->rdram, N64_SEGMENTED_RDRAM_SIZE,
            memory->heap, memory->heap_size) ||
        n64_segmented_host_ranges_overlap(
            memory->extended, N64_SEGMENTED_EXTENDED_SIZE,
            memory->mod_ram, memory->mod_ram_size) ||
        n64_segmented_host_ranges_overlap(
            memory->extended, N64_SEGMENTED_EXTENDED_SIZE,
            memory->heap, memory->heap_size) ||
        n64_segmented_host_ranges_overlap(
            memory->mod_ram, memory->mod_ram_size,
            memory->heap, memory->heap_size)) {
        return N64_SEGMENTED_INVALID_CONFIGURATION;
    }

    return N64_SEGMENTED_OK;
}

/*
 * Resolve one contiguous range. KSEG0 maps to separate host buffers for main
 * RDRAM, the runtime's 8–16 MiB extension, mod RAM and the bounded heap.
 * KSEG1 mirrors only the first 8 MiB, matching the pinned recomp.h hook.
 */
static inline n64_segmented_result n64_segmented_resolve(
    const n64_segmented_memory *memory,
    uint64_t n64_address,
    size_t length,
    n64_segmented_access access,
    n64_segmented_span *span)
{
    uint32_t address;
    uint64_t offset;
    size_t remaining;

    if (memory == NULL || span == NULL || length == 0 || length > UINT32_MAX) {
        return N64_SEGMENTED_INVALID_ARGUMENT;
    }

    if (access != N64_SEGMENTED_ACCESS_READ &&
        access != N64_SEGMENTED_ACCESS_WRITE) {
        return N64_SEGMENTED_INVALID_ARGUMENT;
    }

    address = (uint32_t)n64_address;
    if (n64_address != n64_segmented_sign_extend(address)) {
        return N64_SEGMENTED_NONCANONICAL_ADDRESS;
    }

    span->kind = N64_SEGMENTED_REGION_NONE;
    span->virtual_address = address;
    span->region_offset = 0;
    span->host_pointer = NULL;

    if (address >= N64_SEGMENTED_RDRAM_BASE &&
        address < N64_SEGMENTED_KSEG0_LIMIT) {
        offset = (uint64_t)address - N64_SEGMENTED_RDRAM_BASE;

        if (offset < N64_SEGMENTED_RDRAM_SIZE) {
            remaining = N64_SEGMENTED_RDRAM_SIZE - (size_t)offset;
            if (length > remaining) return N64_SEGMENTED_RANGE_CROSSES_REGION;
            span->kind = N64_SEGMENTED_REGION_RDRAM;
            span->region_offset = (uint32_t)offset;
            span->host_pointer = memory->rdram + (size_t)offset;
            return N64_SEGMENTED_OK;
        }

        if (offset < (uint64_t)N64_SEGMENTED_RDRAM_SIZE +
                     N64_SEGMENTED_EXTENDED_SIZE) {
            size_t extended_offset =
                (size_t)(offset - N64_SEGMENTED_RDRAM_SIZE);
            remaining = N64_SEGMENTED_EXTENDED_SIZE - extended_offset;
            if (length > remaining) return N64_SEGMENTED_RANGE_CROSSES_REGION;
            span->kind = N64_SEGMENTED_REGION_EXTENDED;
            span->region_offset = (uint32_t)extended_offset;
            span->host_pointer = memory->extended + extended_offset;
            return N64_SEGMENTED_OK;
        }

        if (offset >= (uint64_t)(N64_SEGMENTED_MOD_RAM_BASE -
                                 N64_SEGMENTED_RDRAM_BASE)) {
            size_t tail_offset = (size_t)(
                offset - (N64_SEGMENTED_MOD_RAM_BASE - N64_SEGMENTED_RDRAM_BASE));

            if (tail_offset < memory->mod_ram_size) {
                remaining = memory->mod_ram_size - tail_offset;
                if (length > remaining) return N64_SEGMENTED_RANGE_CROSSES_REGION;
                span->kind = N64_SEGMENTED_REGION_MOD_RAM;
                span->region_offset = (uint32_t)tail_offset;
                span->host_pointer = memory->mod_ram + tail_offset;
                return N64_SEGMENTED_OK;
            }

            if (tail_offset >= memory->mod_ram_size) {
                size_t heap_offset = tail_offset - memory->mod_ram_size;
                if (heap_offset < memory->heap_size) {
                    remaining = memory->heap_size - heap_offset;
                    if (length > remaining) return N64_SEGMENTED_RANGE_CROSSES_REGION;
                    span->kind = N64_SEGMENTED_REGION_HEAP;
                    span->region_offset = (uint32_t)heap_offset;
                    span->host_pointer = memory->heap + heap_offset;
                    return N64_SEGMENTED_OK;
                }
            }
        }

        return N64_SEGMENTED_UNMAPPED_ADDRESS;
    }

    if (address >= N64_SEGMENTED_KSEG1_BASE &&
        address < N64_SEGMENTED_KSEG1_RDRAM_END) {
        offset = (uint64_t)address - N64_SEGMENTED_KSEG1_BASE;
        remaining = N64_SEGMENTED_RDRAM_SIZE - (size_t)offset;
        if (length > remaining) return N64_SEGMENTED_RANGE_CROSSES_REGION;
        span->kind = N64_SEGMENTED_REGION_RDRAM;
        span->region_offset = (uint32_t)offset;
        span->host_pointer = memory->rdram + (size_t)offset;
        return N64_SEGMENTED_OK;
    }

    if (address >= N64_SEGMENTED_MMIO_BASE &&
        address < N64_SEGMENTED_MMIO_END) {
        remaining = (size_t)(N64_SEGMENTED_MMIO_END - address);
        if (length > remaining) return N64_SEGMENTED_RANGE_CROSSES_REGION;
        if (!n64_segmented_width_supported(length)) {
            return N64_SEGMENTED_UNSUPPORTED_WIDTH;
        }
        span->kind = N64_SEGMENTED_REGION_MMIO;
        return N64_SEGMENTED_OK;
    }

    if (address >= N64_SEGMENTED_ROM_BASE &&
        address < N64_SEGMENTED_ROM_BASE + N64_SEGMENTED_ROM_WINDOW_SIZE) {
        size_t rom_offset = (size_t)(address - N64_SEGMENTED_ROM_BASE);
        if (access == N64_SEGMENTED_ACCESS_WRITE) return N64_SEGMENTED_READ_ONLY;
        if (rom_offset > memory->rom_size ||
            length > memory->rom_size - rom_offset) {
            return N64_SEGMENTED_UNMAPPED_ADDRESS;
        }
        if (!n64_segmented_width_supported(length)) {
            return N64_SEGMENTED_UNSUPPORTED_WIDTH;
        }
        span->kind = N64_SEGMENTED_REGION_ROM;
        span->region_offset = (uint32_t)rom_offset;
        return N64_SEGMENTED_OK;
    }

    return N64_SEGMENTED_UNMAPPED_ADDRESS;
}

static inline uint64_t n64_segmented_read_be(const uint8_t *bytes, size_t width)
{
    uint64_t value = 0;
    size_t i;

    for (i = 0; i < width; ++i) {
        value = (value << 8) | bytes[i];
    }
    return value;
}

static inline void n64_segmented_write_be(
    uint8_t *bytes, size_t width, uint64_t value)
{
    size_t i;

    for (i = 0; i < width; ++i) {
        size_t shift = (width - 1 - i) * 8;
        bytes[i] = (uint8_t)(value >> shift);
    }
}

static inline n64_segmented_result n64_segmented_read(
    const n64_segmented_memory *memory,
    uint64_t n64_address,
    size_t width,
    uint64_t *value)
{
    n64_segmented_span span;
    n64_segmented_result result;
    uint8_t bytes[8];

    if (memory == NULL || value == NULL) return N64_SEGMENTED_INVALID_ARGUMENT;
    if (!n64_segmented_width_supported(width)) return N64_SEGMENTED_UNSUPPORTED_WIDTH;

    result = n64_segmented_memory_validate(memory);
    if (result != N64_SEGMENTED_OK) return result;

    result = n64_segmented_resolve(
        memory, n64_address, width, N64_SEGMENTED_ACCESS_READ, &span);
    if (result != N64_SEGMENTED_OK) return result;

    switch (span.kind) {
    case N64_SEGMENTED_REGION_RDRAM:
    case N64_SEGMENTED_REGION_EXTENDED:
    case N64_SEGMENTED_REGION_MOD_RAM:
    case N64_SEGMENTED_REGION_HEAP:
        *value = n64_segmented_read_be(span.host_pointer, width);
        return N64_SEGMENTED_OK;

    case N64_SEGMENTED_REGION_ROM:
        if (memory->rom_read == NULL) return N64_SEGMENTED_CALLBACK_MISSING;
        if (memory->rom_read(memory->callback_context, span.region_offset,
                             bytes, width) != 0) {
            return N64_SEGMENTED_CALLBACK_FAILED;
        }
        *value = n64_segmented_read_be(bytes, width);
        return N64_SEGMENTED_OK;

    case N64_SEGMENTED_REGION_MMIO:
        if (memory->mmio_access == NULL) return N64_SEGMENTED_CALLBACK_MISSING;
        *value = 0;
        if (memory->mmio_access(memory->callback_context, span.virtual_address,
                                (uint8_t)width, N64_SEGMENTED_ACCESS_READ,
                                value) != 0) {
            return N64_SEGMENTED_CALLBACK_FAILED;
        }
        return N64_SEGMENTED_OK;

    default:
        return N64_SEGMENTED_UNMAPPED_ADDRESS;
    }
}

static inline n64_segmented_result n64_segmented_write(
    const n64_segmented_memory *memory,
    uint64_t n64_address,
    size_t width,
    uint64_t value)
{
    n64_segmented_span span;
    n64_segmented_result result;

    if (memory == NULL) return N64_SEGMENTED_INVALID_ARGUMENT;
    if (!n64_segmented_width_supported(width)) return N64_SEGMENTED_UNSUPPORTED_WIDTH;

    result = n64_segmented_memory_validate(memory);
    if (result != N64_SEGMENTED_OK) return result;

    result = n64_segmented_resolve(
        memory, n64_address, width, N64_SEGMENTED_ACCESS_WRITE, &span);
    if (result != N64_SEGMENTED_OK) return result;

    switch (span.kind) {
    case N64_SEGMENTED_REGION_RDRAM:
    case N64_SEGMENTED_REGION_EXTENDED:
    case N64_SEGMENTED_REGION_MOD_RAM:
    case N64_SEGMENTED_REGION_HEAP:
        n64_segmented_write_be(span.host_pointer, width, value);
        return N64_SEGMENTED_OK;

    case N64_SEGMENTED_REGION_MMIO:
        if (memory->mmio_access == NULL) return N64_SEGMENTED_CALLBACK_MISSING;
        if (memory->mmio_access(memory->callback_context, span.virtual_address,
                                (uint8_t)width, N64_SEGMENTED_ACCESS_WRITE,
                                &value) != 0) {
            return N64_SEGMENTED_CALLBACK_FAILED;
        }
        return N64_SEGMENTED_OK;

    case N64_SEGMENTED_REGION_ROM:
        return N64_SEGMENTED_READ_ONLY;

    default:
        return N64_SEGMENTED_UNMAPPED_ADDRESS;
    }
}

/*
 * Convert an allocated host pointer back to a canonical KSEG0 guest address.
 * This is the missing operation needed to replace recomp_alloc's
 * (host_pointer - rdram_base) assumption when backing regions are segmented.
 */
static inline n64_segmented_result n64_segmented_guest_from_host(
    const n64_segmented_memory *memory,
    const void *host_pointer,
    size_t length,
    uint64_t *guest_address)
{
    uintptr_t pointer;
    uintptr_t region_start;
    size_t offset;
    uint32_t guest_base;

    if (memory == NULL || host_pointer == NULL || guest_address == NULL ||
        length == 0) {
        return N64_SEGMENTED_INVALID_ARGUMENT;
    }

    pointer = (uintptr_t)host_pointer;

#define N64_SEGMENTED_REVERSE_REGION(base_ptr, region_size, guest_base_value) \
    do { \
        if ((region_size) != 0 && n64_segmented_host_range_valid((base_ptr), (region_size))) { \
            region_start = (uintptr_t)(base_ptr); \
            if (pointer >= region_start && pointer - region_start < (region_size)) { \
                offset = (size_t)(pointer - region_start); \
                if (offset < (region_size) && length <= (region_size) - offset) { \
                    guest_base = (guest_base_value); \
                    *guest_address = n64_segmented_sign_extend(guest_base + (uint32_t)offset); \
                    return N64_SEGMENTED_OK; \
                } \
                return N64_SEGMENTED_RANGE_CROSSES_REGION; \
            } \
        } \
    } while (0)

    N64_SEGMENTED_REVERSE_REGION(
        memory->rdram, N64_SEGMENTED_RDRAM_SIZE, N64_SEGMENTED_RDRAM_BASE);
    N64_SEGMENTED_REVERSE_REGION(
        memory->extended, N64_SEGMENTED_EXTENDED_SIZE, N64_SEGMENTED_EXTENDED_BASE);
    N64_SEGMENTED_REVERSE_REGION(
        memory->mod_ram, memory->mod_ram_size, N64_SEGMENTED_MOD_RAM_BASE);
    N64_SEGMENTED_REVERSE_REGION(
        memory->heap, memory->heap_size,
        N64_SEGMENTED_MOD_RAM_BASE + (uint32_t)memory->mod_ram_size);

#undef N64_SEGMENTED_REVERSE_REGION

    return N64_SEGMENTED_HOST_POINTER_UNMAPPED;
}

#endif
