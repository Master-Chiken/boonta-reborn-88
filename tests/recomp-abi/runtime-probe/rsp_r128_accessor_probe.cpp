/*
 * Executes the exact RSP::r128 union/accessor methods extracted from the
 * pinned N64ModernRuntime revision by extract_rsp_r128_accessor.py.
 */
#include "pinned_rsp_r128_accessor.hpp"

#include <stdint.h>
#include <string.h>

extern "C" int run_pinned_rsp_r128_accessor_probe(void) {
    static const uint8_t expected_bytes[16] = {
        0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
        0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF
    };
    static const uint16_t expected_halfwords[8] = {
        0x0011, 0x2233, 0x4455, 0x6677,
        0x8899, 0xAABB, 0xCCDD, 0xEEFF
    };

    static_assert(sizeof(RSP::r128) == 16, "RSP vector register must be 128 bits");
    RSP::r128 reg{};
    memcpy(&reg, expected_bytes, sizeof(expected_bytes));

    const RSP::r128 &constant_reg = reg;
    for (u32 i = 0; i < 16; ++i) {
        if (reg.byte(i) != expected_bytes[i] ||
            reg.u8(i) != expected_bytes[i] ||
            constant_reg.byte(i) != expected_bytes[i] ||
            constant_reg.u8(i) != expected_bytes[i]) {
            return 1;
        }
    }

    for (u32 i = 0; i < 8; ++i) {
        if (reg.element(i) != expected_halfwords[i] ||
            reg.u16(i) != expected_halfwords[i] ||
            constant_reg.element(i) != expected_halfwords[i] ||
            constant_reg.u16(i) != expected_halfwords[i]) {
            return 2;
        }
    }
    if (reg.s16(7) != static_cast<int16_t>(UINT16_C(0xEEFF)) ||
        constant_reg.s16(0) != static_cast<int16_t>(UINT16_C(0x0011))) {
        return 3;
    }

    memset(&reg, 0, sizeof(reg));
    reg.byte(0) = UINT8_C(0xA0);
    reg.u8(15) = UINT8_C(0x0F);
    if (reinterpret_cast<uint8_t *>(&reg)[0] != UINT8_C(0xA0) ||
        reinterpret_cast<uint8_t *>(&reg)[15] != UINT8_C(0x0F)) {
        return 4;
    }

    reg.element(0) = UINT16_C(0x1357);
    reg.u16(7) = UINT16_C(0x2468);
    reg.s16(3) = static_cast<int16_t>(UINT16_C(0x80FF));
    const uint8_t *raw = reinterpret_cast<const uint8_t *>(&reg);
    if (raw[0] != 0x13 || raw[1] != 0x57 ||
        raw[14] != 0x24 || raw[15] != 0x68 ||
        raw[6] != 0x80 || raw[7] != 0xFF ||
        reg.element(0) != UINT16_C(0x1357) ||
        reg.u16(7) != UINT16_C(0x2468) ||
        reg.s16(3) != static_cast<int16_t>(UINT16_C(0x80FF))) {
        return 5;
    }

    return 0;
}
