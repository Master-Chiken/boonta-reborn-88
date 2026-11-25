#ifndef BOONTA_N64_MEMORY_MAP_H
#define BOONTA_N64_MEMORY_MAP_H

/*
 * Bounded N64 address-space model.
 *
 * This is a host-testable contract, not yet the production Wii runtime.
 * Guest regions are described by their N64 virtual base and an explicitly
 * supplied host backing pointer. No 512 MiB/4 GiB reservation is assumed.
 */

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define N64_MEMORY_RDRAM_GUEST_BASE       UINT32_C(0x80000000)
#define N64_MEMORY_RDRAM_SIZE             UINT32_C(0x00800000)
#define N64_MEMORY_KSEG1_RDRAM_BASE       UINT32_C(0xA0000000)
#define N64_MEMORY_RUNTIME_GUEST_BASE     UINT32_C(0x80800000)
#define N64_MEMORY_RUNTIME_SIZE           UINT32_C(0x00800000)
#define N64_MEMORY_MEM1_HEAP_GUEST_BASE   UINT32_C(0x81000000)
#define N64_MEMORY_MEM1_HEAP_SIZE         UINT32_C(0x00800000)
#define N64_MEMORY_MEM2_HEAP_GUEST_BASE   UINT32_C(0x90000000)
#define N64_MEMORY_MEM2_HEAP_SIZE         UINT32_C(0x04000000)
#define N64_MEMORY_KSEG1_MEM2_BASE        UINT32_C(0xB0000000)
#define N64_MEMORY_MEM1_TOTAL_SIZE        UINT32_C(0x01800000)
#define N64_MEMORY_MEM2_TOTAL_SIZE        UINT32_C(0x04000000)

typedef enum N64MemoryAccess {
    N64_MEMORY_ACCESS_READ = 1,
    N64_MEMORY_ACCESS_WRITE = 2
} N64MemoryAccess;

typedef enum N64MemoryRegionKind {
    N64_MEMORY_REGION_RDRAM = 1,
    N64_MEMORY_REGION_RUNTIME = 2,
    N64_MEMORY_REGION_MEM1_HEAP = 3,
    N64_MEMORY_REGION_MEM2_HEAP = 4,
    N64_MEMORY_REGION_OTHER = 5
} N64MemoryRegionKind;

enum {
    N64_MEMORY_PERM_READ = 1u << 0,
    N64_MEMORY_PERM_WRITE = 1u << 1
};

typedef enum N64MemoryStatus {
    N64_MEMORY_STATUS_OK = 0,
    N64_MEMORY_STATUS_MMIO,
    N64_MEMORY_STATUS_BAD_ARGUMENT,
    N64_MEMORY_STATUS_BAD_ADDRESS_EXTENSION,
    N64_MEMORY_STATUS_BAD_MAP,
    N64_MEMORY_STATUS_UNMAPPED,
    N64_MEMORY_STATUS_CROSSES_REGION,
    N64_MEMORY_STATUS_ACCESS_DENIED,
    N64_MEMORY_STATUS_UNHANDLED_MMIO
} N64MemoryStatus;

typedef struct N64MemoryRegion {
    uint32_t guest_base;
    uint32_t size;
    uint8_t *host_base;
    uint8_t permissions;
    N64MemoryRegionKind kind;
    const char *name;
} N64MemoryRegion;

/*
 * MMIO is value-based: callbacks receive the original uncached device
 * address and a 1/2/4/8-byte access. They must implement register side
 * effects and byte order explicitly; MMIO is never exposed as an arbitrary
 * host pointer.
 */
typedef int (*N64MemoryMmioCallback)(
    void *user,
    uint32_t device_address,
    size_t width,
    N64MemoryAccess access,
    uint64_t *value);

typedef void (*N64MemoryFaultCallback)(
    void *user,
    N64MemoryStatus status,
    uint64_t raw_address,
    uint32_t normalized_address,
    size_t width,
    N64MemoryAccess access);

typedef struct N64MemoryMap {
    const N64MemoryRegion *regions;
    size_t region_count;
    N64MemoryMmioCallback mmio;
    N64MemoryFaultCallback fault;
    void *user;
} N64MemoryMap;

/*
 * Validate that guest regions are non-empty, have backing memory and do not
 * overlap in guest address space. Host backing ranges may be independently
 * allocated; reverse translation resolves each range by its host pointer.
 */
N64MemoryStatus n64_memory_map_validate(const N64MemoryMap *map);

/*
 * Resolve a normal RAM/runtime/heap address to a host pointer.
 *
 * Physical RDRAM addresses, KSEG0 addresses, and KSEG1 aliases are normalized
 * to a configured canonical region. A KSEG1 address not backed by a region
 * is reported as MMIO by the resolver. The returned pointer is valid only
 * for the requested width and permissions.
 */
N64MemoryStatus n64_memory_translate(
    const N64MemoryMap *map,
    uint64_t guest_address,
    size_t width,
    N64MemoryAccess access,
    uint8_t **host_pointer);

/* Big-endian N64 scalar accessors. Width must be 1, 2, 4, or 8 bytes. */
N64MemoryStatus n64_memory_read(
    const N64MemoryMap *map,
    uint64_t guest_address,
    size_t width,
    uint64_t *value);

N64MemoryStatus n64_memory_write(
    const N64MemoryMap *map,
    uint64_t guest_address,
    size_t width,
    uint64_t value);

/*
 * Convert an allocation/backing pointer to its canonical guest address.
 * This is the reverse mapping required when recomp_alloc returns memory
 * from either MEM1 or MEM2. The returned address is the region's configured
 * KSEG0 base, never an uncached alias.
 */
N64MemoryStatus n64_memory_host_to_guest(
    const N64MemoryMap *map,
    const void *host_pointer,
    size_t span,
    uint32_t *guest_address);

const char *n64_memory_status_string(N64MemoryStatus status);

#ifdef __cplusplus
}
#endif

#endif /* BOONTA_N64_MEMORY_MAP_H */
