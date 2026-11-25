#include "n64_memory_map.h"

#include <limits.h>

#define N64_MEMORY_ADDRESS_SPACE_END UINT64_C(0x100000000)
#define N64_MEMORY_KSEG0_BASE UINT32_C(0x80000000)
#define N64_MEMORY_KSEG0_END  UINT32_C(0xA0000000)
#define N64_MEMORY_KSEG1_BASE UINT32_C(0xA0000000)
#define N64_MEMORY_KSEG1_END  UINT32_C(0xC0000000)
#define N64_MEMORY_KSEG1_RDRAM_END (N64_MEMORY_KSEG1_BASE + N64_MEMORY_RDRAM_SIZE)
#define N64_MEMORY_PHYSICAL_LIMIT UINT32_C(0x20000000)

typedef struct N64MemoryResolved {
    uint32_t canonical_address;
    uint32_t mmio_address;
    const N64MemoryRegion *region;
    uint8_t *host_pointer;
    int is_mmio;
} N64MemoryResolved;

static int n64_memory_width_is_valid(size_t width) {
    return width == 1u || width == 2u || width == 4u || width == 8u;
}

static int n64_memory_region_kind_is_valid(N64MemoryRegionKind kind) {
    return kind >= N64_MEMORY_REGION_RDRAM && kind <= N64_MEMORY_REGION_OTHER;
}

static int n64_memory_region_contains(
    const N64MemoryRegion *region,
    uint32_t address,
    size_t width) {
    uint64_t start;
    uint64_t end;
    uint64_t region_start;
    uint64_t region_end;

    if (region == NULL || width == 0u) {
        return 0;
    }

    start = (uint64_t)address;
    end = start + (uint64_t)width;
    region_start = (uint64_t)region->guest_base;
    region_end = region_start + (uint64_t)region->size;

    return start >= region_start && end <= region_end;
}

static const N64MemoryRegion *n64_memory_find_region_start(
    const N64MemoryMap *map,
    uint32_t address) {
    size_t i;

    if (map == NULL || (map->region_count != 0u && map->regions == NULL)) {
        return NULL;
    }

    for (i = 0u; i < map->region_count; ++i) {
        const N64MemoryRegion *region = &map->regions[i];
        if (address >= region->guest_base &&
            (uint64_t)address < (uint64_t)region->guest_base + region->size) {
            return region;
        }
    }

    return NULL;
}

static N64MemoryStatus n64_memory_normalize_address(
    uint64_t raw_address,
    uint32_t *address) {
    uint32_t low;
    uint64_t sign_extended;

    if (address == NULL) {
        return N64_MEMORY_STATUS_BAD_ARGUMENT;
    }

    low = (uint32_t)raw_address;
    sign_extended = (low & UINT32_C(0x80000000)) != 0u
        ? (UINT64_C(0xFFFFFFFF00000000) | (uint64_t)low)
        : (uint64_t)low;

    /*
     * Generated N64 code may carry a 32-bit address as either a zero-extended
     * or sign-extended gpr. Reject every other 64-bit shape rather than
     * silently truncating a malformed host pointer or arithmetic result.
     */
    if (raw_address != (uint64_t)low && raw_address != sign_extended) {
        return N64_MEMORY_STATUS_BAD_ADDRESS_EXTENSION;
    }

    *address = low;
    return N64_MEMORY_STATUS_OK;
}

static N64MemoryStatus n64_memory_decode_address(
    const N64MemoryMap *map,
    uint32_t address,
    size_t width,
    N64MemoryResolved *resolved) {
    uint32_t canonical = address;
    uint32_t mmio_address = 0u;
    const N64MemoryRegion *region = NULL;

    if (resolved == NULL || width == 0u) {
        return N64_MEMORY_STATUS_BAD_ARGUMENT;
    }

    resolved->canonical_address = 0u;
    resolved->mmio_address = 0u;
    resolved->region = NULL;
    resolved->host_pointer = NULL;
    resolved->is_mmio = 0;

    /*
     * KSEG1 is not a blanket alias for every host-backed extension. Only the
     * real first 8 MiB of N64 RDRAM is mirrored at A0000000-A07FFFFF.
     * Remaining KSEG1 addresses stay device/ROM space and are sent to MMIO.
     */
    if (address >= N64_MEMORY_KSEG1_BASE && address < N64_MEMORY_KSEG1_RDRAM_END) {
        canonical = N64_MEMORY_KSEG0_BASE + (address - N64_MEMORY_KSEG1_BASE);
        region = n64_memory_find_region_start(map, canonical);
        if (region == NULL || region->kind != N64_MEMORY_REGION_RDRAM) {
            return N64_MEMORY_STATUS_UNMAPPED;
        }
        if (!n64_memory_region_contains(region, canonical, width)) {
            return N64_MEMORY_STATUS_CROSSES_REGION;
        }
    } else if (address >= N64_MEMORY_KSEG1_BASE && address < N64_MEMORY_KSEG1_END) {
        resolved->is_mmio = 1;
        resolved->mmio_address = address;
        return N64_MEMORY_STATUS_MMIO;
    } else if (address < N64_MEMORY_RDRAM_SIZE) {
        /* Physical 0..8 MiB is the RDRAM alias. */
        canonical = N64_MEMORY_KSEG0_BASE + address;
        region = n64_memory_find_region_start(map, canonical);
        if (region == NULL || region->kind != N64_MEMORY_REGION_RDRAM) {
            return N64_MEMORY_STATUS_UNMAPPED;
        }
        if (!n64_memory_region_contains(region, canonical, width)) {
            return N64_MEMORY_STATUS_CROSSES_REGION;
        }
    } else if (address < N64_MEMORY_PHYSICAL_LIMIT) {
        /*
         * Other physical bus addresses are devices/ROM domains, not host
         * backing RAM. Present them through their uncached KSEG1 address.
         */
        mmio_address = N64_MEMORY_KSEG1_BASE + address;
        resolved->is_mmio = 1;
        resolved->mmio_address = mmio_address;
        return N64_MEMORY_STATUS_MMIO;
    } else if (address >= N64_MEMORY_KSEG0_BASE && address < N64_MEMORY_KSEG0_END) {
        /* Canonical KSEG0 addresses include explicit runtime and heap regions. */
        region = n64_memory_find_region_start(map, canonical);
        if (region == NULL) {
            return N64_MEMORY_STATUS_UNMAPPED;
        }
        if (!n64_memory_region_contains(region, canonical, width)) {
            return N64_MEMORY_STATUS_CROSSES_REGION;
        }
    } else {
        return N64_MEMORY_STATUS_UNMAPPED;
    }

    if (region == NULL || region->host_base == NULL) {
        return N64_MEMORY_STATUS_BAD_MAP;
    }

    resolved->canonical_address = canonical;
    resolved->region = region;
    resolved->host_pointer = region->host_base + (size_t)(canonical - region->guest_base);
    return N64_MEMORY_STATUS_OK;
}

static void n64_memory_report_fault(
    const N64MemoryMap *map,
    N64MemoryStatus status,
    uint64_t raw_address,
    uint32_t normalized_address,
    size_t width,
    N64MemoryAccess access) {
    if (map != NULL && map->fault != NULL) {
        map->fault(
            map->user,
            status,
            raw_address,
            normalized_address,
            width,
            access);
    }
}

N64MemoryStatus n64_memory_map_validate(const N64MemoryMap *map) {
    size_t i;
    size_t j;

    if (map == NULL || (map->region_count != 0u && map->regions == NULL)) {
        return N64_MEMORY_STATUS_BAD_ARGUMENT;
    }

    for (i = 0u; i < map->region_count; ++i) {
        const N64MemoryRegion *region = &map->regions[i];
        uint64_t guest_start = (uint64_t)region->guest_base;
        uint64_t guest_end = guest_start + (uint64_t)region->size;
        uintptr_t host_start = (uintptr_t)region->host_base;

        if (region->size == 0u || region->host_base == NULL ||
            !n64_memory_region_kind_is_valid(region->kind) ||
            region->permissions == 0u ||
            (region->permissions & (uint8_t)~(N64_MEMORY_PERM_READ | N64_MEMORY_PERM_WRITE)) != 0u) {
            return N64_MEMORY_STATUS_BAD_MAP;
        }

        if (guest_end > N64_MEMORY_ADDRESS_SPACE_END ||
            guest_end <= guest_start ||
            host_start > UINTPTR_MAX - (uintptr_t)region->size) {
            return N64_MEMORY_STATUS_BAD_MAP;
        }

        for (j = i + 1u; j < map->region_count; ++j) {
            const N64MemoryRegion *other = &map->regions[j];
            uint64_t other_start = (uint64_t)other->guest_base;
            uint64_t other_end = other_start + (uint64_t)other->size;

            if (guest_start < other_end && other_start < guest_end) {
                return N64_MEMORY_STATUS_BAD_MAP;
            }
        }
    }

    return N64_MEMORY_STATUS_OK;
}

N64MemoryStatus n64_memory_translate(
    const N64MemoryMap *map,
    uint64_t guest_address,
    size_t width,
    N64MemoryAccess access,
    uint8_t **host_pointer) {
    uint32_t normalized;
    N64MemoryResolved resolved;
    N64MemoryStatus status;
    uint8_t required_permission;

    if (host_pointer == NULL || !n64_memory_width_is_valid(width) ||
        (access != N64_MEMORY_ACCESS_READ && access != N64_MEMORY_ACCESS_WRITE)) {
        return N64_MEMORY_STATUS_BAD_ARGUMENT;
    }
    *host_pointer = NULL;

    status = n64_memory_normalize_address(guest_address, &normalized);
    if (status != N64_MEMORY_STATUS_OK) {
        n64_memory_report_fault(map, status, guest_address, 0u, width, access);
        return status;
    }

    status = n64_memory_decode_address(map, normalized, width, &resolved);
    if (status != N64_MEMORY_STATUS_OK) {
        if (status != N64_MEMORY_STATUS_MMIO) {
            n64_memory_report_fault(map, status, guest_address, normalized, width, access);
        }
        return status;
    }

    required_permission = access == N64_MEMORY_ACCESS_READ
        ? N64_MEMORY_PERM_READ
        : N64_MEMORY_PERM_WRITE;
    if ((resolved.region->permissions & required_permission) == 0u) {
        n64_memory_report_fault(
            map, N64_MEMORY_STATUS_ACCESS_DENIED, guest_address,
            resolved.canonical_address, width, access);
        return N64_MEMORY_STATUS_ACCESS_DENIED;
    }

    *host_pointer = resolved.host_pointer;
    return N64_MEMORY_STATUS_OK;
}

static uint64_t n64_memory_load_be(const uint8_t *bytes, size_t width) {
    uint64_t value = 0u;
    size_t i;

    for (i = 0u; i < width; ++i) {
        value = (value << 8) | (uint64_t)bytes[i];
    }

    return value;
}

static void n64_memory_store_be(uint8_t *bytes, size_t width, uint64_t value) {
    size_t i;

    for (i = 0u; i < width; ++i) {
        size_t shift = (width - 1u - i) * 8u;
        bytes[i] = (uint8_t)(value >> shift);
    }
}

static N64MemoryStatus n64_memory_access(
    const N64MemoryMap *map,
    uint64_t guest_address,
    size_t width,
    N64MemoryAccess access,
    uint64_t *value) {
    uint32_t normalized;
    N64MemoryResolved resolved;
    N64MemoryStatus status;
    uint8_t *host_pointer = NULL;

    if (value == NULL || !n64_memory_width_is_valid(width) ||
        (access != N64_MEMORY_ACCESS_READ && access != N64_MEMORY_ACCESS_WRITE)) {
        return N64_MEMORY_STATUS_BAD_ARGUMENT;
    }

    status = n64_memory_normalize_address(guest_address, &normalized);
    if (status != N64_MEMORY_STATUS_OK) {
        n64_memory_report_fault(map, status, guest_address, 0u, width, access);
        return status;
    }

    status = n64_memory_decode_address(map, normalized, width, &resolved);
    if (status == N64_MEMORY_STATUS_MMIO) {
        if (map == NULL || map->mmio == NULL ||
            !map->mmio(map->user, resolved.mmio_address, width, access, value)) {
            n64_memory_report_fault(
                map, N64_MEMORY_STATUS_UNHANDLED_MMIO,
                guest_address, resolved.mmio_address, width, access);
            return N64_MEMORY_STATUS_UNHANDLED_MMIO;
        }
        if (width < sizeof(uint64_t) && access == N64_MEMORY_ACCESS_READ) {
            *value &= (UINT64_C(1) << (width * 8u)) - UINT64_C(1);
        }
        if (width < sizeof(uint64_t) && access == N64_MEMORY_ACCESS_WRITE) {
            *value &= (UINT64_C(1) << (width * 8u)) - UINT64_C(1);
        }
        return N64_MEMORY_STATUS_OK;
    }
    if (status != N64_MEMORY_STATUS_OK) {
        n64_memory_report_fault(map, status, guest_address, normalized, width, access);
        return status;
    }

    if ((resolved.region->permissions &
        (access == N64_MEMORY_ACCESS_READ ? N64_MEMORY_PERM_READ : N64_MEMORY_PERM_WRITE)) == 0u) {
        n64_memory_report_fault(
            map, N64_MEMORY_STATUS_ACCESS_DENIED,
            guest_address, resolved.canonical_address, width, access);
        return N64_MEMORY_STATUS_ACCESS_DENIED;
    }

    host_pointer = resolved.host_pointer;
    if (access == N64_MEMORY_ACCESS_READ) {
        *value = n64_memory_load_be(host_pointer, width);
    } else {
        n64_memory_store_be(host_pointer, width, *value);
    }

    return N64_MEMORY_STATUS_OK;
}

N64MemoryStatus n64_memory_read(
    const N64MemoryMap *map,
    uint64_t guest_address,
    size_t width,
    uint64_t *value) {
    return n64_memory_access(map, guest_address, width, N64_MEMORY_ACCESS_READ, value);
}

N64MemoryStatus n64_memory_write(
    const N64MemoryMap *map,
    uint64_t guest_address,
    size_t width,
    uint64_t value) {
    return n64_memory_access(map, guest_address, width, N64_MEMORY_ACCESS_WRITE, &value);
}

N64MemoryStatus n64_memory_host_to_guest(
    const N64MemoryMap *map,
    const void *host_pointer,
    size_t span,
    uint32_t *guest_address) {
    uintptr_t host_start;
    size_t i;
    int found = 0;
    uint32_t result = 0u;

    if (map == NULL || host_pointer == NULL || guest_address == NULL ||
        span == 0u || (map->region_count != 0u && map->regions == NULL)) {
        return N64_MEMORY_STATUS_BAD_ARGUMENT;
    }

    host_start = (uintptr_t)host_pointer;
    if (host_start > UINTPTR_MAX - span) {
        return N64_MEMORY_STATUS_BAD_ARGUMENT;
    }

    for (i = 0u; i < map->region_count; ++i) {
        const N64MemoryRegion *region = &map->regions[i];
        uintptr_t region_start = (uintptr_t)region->host_base;
        uintptr_t region_end;

        if (region->host_base == NULL ||
            region_start > UINTPTR_MAX - (uintptr_t)region->size) {
            return N64_MEMORY_STATUS_BAD_MAP;
        }
        region_end = region_start + (uintptr_t)region->size;

        if (host_start >= region_start && host_start + span <= region_end) {
            if (found) {
                /* An ambiguous reverse mapping is unsafe for guest pointers. */
                return N64_MEMORY_STATUS_BAD_MAP;
            }
            found = 1;
            result = region->guest_base + (uint32_t)(host_start - region_start);
        }
    }

    if (!found) {
        return N64_MEMORY_STATUS_UNMAPPED;
    }

    *guest_address = result;
    return N64_MEMORY_STATUS_OK;
}

const char *n64_memory_status_string(N64MemoryStatus status) {
    switch (status) {
        case N64_MEMORY_STATUS_OK: return "ok";
        case N64_MEMORY_STATUS_MMIO: return "mmio";
        case N64_MEMORY_STATUS_BAD_ARGUMENT: return "bad argument";
        case N64_MEMORY_STATUS_BAD_ADDRESS_EXTENSION: return "bad address extension";
        case N64_MEMORY_STATUS_BAD_MAP: return "bad map";
        case N64_MEMORY_STATUS_UNMAPPED: return "unmapped";
        case N64_MEMORY_STATUS_CROSSES_REGION: return "crosses region";
        case N64_MEMORY_STATUS_ACCESS_DENIED: return "access denied";
        case N64_MEMORY_STATUS_UNHANDLED_MMIO: return "unhandled mmio";
        default: return "unknown";
    }
}
