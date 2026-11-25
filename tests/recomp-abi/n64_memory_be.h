#ifndef BOONTA_TESTS_RECOMP_ABI_N64_MEMORY_BE_H
#define BOONTA_TESTS_RECOMP_ABI_N64_MEMORY_BE_H

#include <stdint.h>

/*
 * Clean-room reference helpers for the N64's big-endian byte layout.
 *
 * This header is a small test oracle, not a replacement for N64Recomp's
 * production memory macros. Callers must validate the address range before
 * using these helpers.
 */
static inline uint8_t n64_be_read_u8(const uint8_t *memory, uint32_t address) {
    return memory[address];
}

static inline uint16_t n64_be_read_u16(const uint8_t *memory, uint32_t address) {
    return ((uint16_t)memory[address] << 8) |
           (uint16_t)memory[address + 1];
}

static inline uint32_t n64_be_read_u32(const uint8_t *memory, uint32_t address) {
    return ((uint32_t)memory[address] << 24) |
           ((uint32_t)memory[address + 1] << 16) |
           ((uint32_t)memory[address + 2] << 8) |
           (uint32_t)memory[address + 3];
}

static inline uint64_t n64_be_read_u64(const uint8_t *memory, uint32_t address) {
    return ((uint64_t)n64_be_read_u32(memory, address) << 32) |
           (uint64_t)n64_be_read_u32(memory, address + 4);
}

static inline int16_t n64_be_read_s16(const uint8_t *memory, uint32_t address) {
    return (int16_t)n64_be_read_u16(memory, address);
}

static inline int32_t n64_be_read_s32(const uint8_t *memory, uint32_t address) {
    return (int32_t)n64_be_read_u32(memory, address);
}

static inline void n64_be_write_u8(uint8_t *memory, uint32_t address, uint8_t value) {
    memory[address] = value;
}

static inline void n64_be_write_u16(uint8_t *memory, uint32_t address, uint16_t value) {
    memory[address] = (uint8_t)(value >> 8);
    memory[address + 1] = (uint8_t)value;
}

static inline void n64_be_write_u32(uint8_t *memory, uint32_t address, uint32_t value) {
    memory[address] = (uint8_t)(value >> 24);
    memory[address + 1] = (uint8_t)(value >> 16);
    memory[address + 2] = (uint8_t)(value >> 8);
    memory[address + 3] = (uint8_t)value;
}

static inline void n64_be_write_u64(uint8_t *memory, uint32_t address, uint64_t value) {
    n64_be_write_u32(memory, address, (uint32_t)(value >> 32));
    n64_be_write_u32(memory, address + 4, (uint32_t)value);
}

#endif
