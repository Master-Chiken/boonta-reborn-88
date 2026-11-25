#include "ppc_memory_lane_compat.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main(void) {
#if RECOMP_MEMORY_FORCE_BIG_ENDIAN_FOR_TEST
    assert(RECOMP_MEM_HOST_IS_BIG_ENDIAN == 1);
    assert(RECOMP_MEM_BYTE_LANE(UINT32_C(0x100)) == UINT32_C(0x100));
    assert(RECOMP_MEM_BYTE_LANE(UINT32_C(0x101)) == UINT32_C(0x101));
    assert(RECOMP_MEM_HALF_LANE(UINT32_C(0x100)) == UINT32_C(0x100));
    assert(RECOMP_MEM_HALF_LANE(UINT32_C(0x102)) == UINT32_C(0x102));
    puts("PowerPC big-endian lane selector: PASS");
#else
    assert(RECOMP_MEM_HOST_IS_BIG_ENDIAN == 0);
    assert(RECOMP_MEM_BYTE_LANE(UINT32_C(0x100)) == UINT32_C(0x103));
    assert(RECOMP_MEM_BYTE_LANE(UINT32_C(0x101)) == UINT32_C(0x102));
    assert(RECOMP_MEM_HALF_LANE(UINT32_C(0x100)) == UINT32_C(0x102));
    assert(RECOMP_MEM_HALF_LANE(UINT32_C(0x102)) == UINT32_C(0x100));
    puts("Little-endian compatibility lane selector: PASS");
#endif
    return 0;
}
