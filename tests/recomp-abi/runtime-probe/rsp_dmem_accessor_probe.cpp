/*
 * Executes scalar RSP DMEM helpers extracted from the exact pinned
 * N64ModernRuntime rsp.hpp, with the BE lane adapter applied by the extractor.
 */
#include <recomp.h>
#include "pinned_rsp_dmem_accessors.hpp"

#include <stdint.h>
#include <string.h>

uint8_t dmem[0x1000];

extern "C" int run_pinned_rsp_dmem_accessor_probe(void) {
    memset(dmem, 0, sizeof(dmem));

    dmem[0x100] = 0x11;
    dmem[0x101] = 0x22;
    dmem[0x102] = 0x33;
    dmem[0x103] = 0x44;
    if (RSP_MEM_BU(0, 0x100) != 0x11 ||
        RSP_MEM_BU(0, 0x103) != 0x44 ||
        RSP_MEM_B(0, 0x100) != 0x11) {
        return 1;
    }
    if (RSP_MEM_W_LOAD(0, 0x100) != UINT32_C(0x11223344) ||
        RSP_MEM_HU_LOAD(0, 0x100) != UINT32_C(0x1122) ||
        RSP_MEM_HU_LOAD(2, 0x100) != UINT32_C(0x3344)) {
        return 2;
    }

    dmem[0x110] = 0x80;
    dmem[0x111] = 0x01;
    if (RSP_MEM_H_LOAD(0, 0x110) != UINT32_C(0xFFFF8001)) {
        return 3;
    }

    RSP_MEM_W_STORE(0, 0x120, UINT32_C(0xA1B2C3D4));
    if (dmem[0x120] != 0xA1 || dmem[0x121] != 0xB2 ||
        dmem[0x122] != 0xC3 || dmem[0x123] != 0xD4 ||
        RSP_MEM_W_LOAD(0, 0x120) != UINT32_C(0xA1B2C3D4)) {
        return 4;
    }

    RSP_MEM_H_STORE(0, 0x130, UINT32_C(0xDEADBEEF));
    if (dmem[0x130] != 0xBE || dmem[0x131] != 0xEF ||
        RSP_MEM_HU_LOAD(0, 0x130) != UINT32_C(0xBEEF)) {
        return 5;
    }

    RSP_MEM_BU(0, 0xFFF) = UINT8_C(0x5A);
    RSP_MEM_BU(0, 0x000) = UINT8_C(0xA5);
    if (RSP_MEM_BU(1, 0xFFF) != UINT8_C(0xA5)) {
        return 6;
    }

    /* Exercise the exact pinned RDRAM<->DMEM DMA helpers through patched MEM_B. */
    uint8_t rdram[0x1000] = {};
    rdram[0x100] = 0x10;
    rdram[0x101] = 0x21;
    rdram[0x102] = 0x32;
    rdram[0x103] = 0x43;
    dma_rdram_to_dmem(rdram, 0x200, 0x103, 3); /* inclusive length; address aligns to 8 */
    if (dmem[0x200] != 0x10 || dmem[0x201] != 0x21 ||
        dmem[0x202] != 0x32 || dmem[0x203] != 0x43) {
        return 7;
    }

    dmem[0x210] = 0xA0;
    dmem[0x211] = 0xB1;
    dmem[0x212] = 0xC2;
    dmem[0x213] = 0xD3;
    dma_dmem_to_rdram(rdram, 0x210, 0x107, 3);
    if (rdram[0x100] != 0xA0 || rdram[0x101] != 0xB1 ||
        rdram[0x102] != 0xC2 || rdram[0x103] != 0xD3) {
        return 8;
    }

    return 0;
}
