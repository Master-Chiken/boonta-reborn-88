#include "n64_memory_be.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main(void) {
    uint8_t memory[16] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    };

    assert(n64_be_read_u8(memory, 0) == UINT8_C(0x01));
    assert(n64_be_read_u16(memory, 0) == UINT16_C(0x0123));
    assert(n64_be_read_u32(memory, 0) == UINT32_C(0x01234567));
    assert(n64_be_read_u64(memory, 0) == UINT64_C(0x0123456789ABCDEF));

    /* Unaligned scalar reads must retain N64 byte order. */
    assert(n64_be_read_u16(memory, 1) == UINT16_C(0x2345));
    assert(n64_be_read_u32(memory, 2) == UINT32_C(0x456789AB));
    assert(n64_be_read_u64(memory, 1) == UINT64_C(0x23456789ABCDEF00));

    memory[0] = 0xFF;
    memory[1] = 0xFE;
    memory[2] = 0xFF;
    memory[3] = 0xFF;
    memory[4] = 0xFF;
    memory[5] = 0xFF;
    assert(n64_be_read_s16(memory, 0) == -2);
    assert(n64_be_read_s32(memory, 2) == -1);

    n64_be_write_u8(memory, 0, UINT8_C(0xA5));
    n64_be_write_u16(memory, 1, UINT16_C(0xB6C7));
    n64_be_write_u32(memory, 3, UINT32_C(0xD8E9FA0B));
    n64_be_write_u64(memory, 7, UINT64_C(0x1029384756ABCDEF));

    assert(memory[0] == 0xA5);
    assert(memory[1] == 0xB6 && memory[2] == 0xC7);
    assert(n64_be_read_u32(memory, 3) == UINT32_C(0xD8E9FA0B));
    assert(n64_be_read_u64(memory, 7) == UINT64_C(0x1029384756ABCDEF));

    puts("N64 big-endian memory model: PASS");
    return 0;
}
