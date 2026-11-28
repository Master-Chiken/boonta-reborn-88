#include "rsp_dmem_endian.h"

#include <assert.h>
#include <stdio.h>

int main(void)
{
#if N64_RSP_DMEM_HOST_BIG_ENDIAN
    assert(n64_rsp_dmem_host_byte_index(0) == 0);
    assert(n64_rsp_dmem_host_byte_index(1) == 1);
    assert(n64_rsp_dmem_host_byte_index(2) == 2);
    assert(n64_rsp_dmem_host_byte_index(3) == 3);
    assert(n64_rsp_dmem_host_word_byte_index(0) == 0);
    assert(n64_rsp_dmem_host_word_byte_index(3) == 3);
    assert(n64_rsp_dmem_host_half_load_byte_index(0) == 0);
    assert(n64_rsp_dmem_host_half_load_byte_index(1) == 1);
    assert(n64_rsp_dmem_host_half_store_byte_index(0) == 2);
    assert(n64_rsp_dmem_host_half_store_byte_index(1) == 3);
#else
    assert(n64_rsp_dmem_host_byte_index(0) == 3);
    assert(n64_rsp_dmem_host_byte_index(1) == 2);
    assert(n64_rsp_dmem_host_byte_index(2) == 1);
    assert(n64_rsp_dmem_host_byte_index(3) == 0);
    assert(n64_rsp_dmem_host_word_byte_index(0) == 3);
    assert(n64_rsp_dmem_host_word_byte_index(3) == 0);
    assert(n64_rsp_dmem_host_half_load_byte_index(0) == 1);
    assert(n64_rsp_dmem_host_half_load_byte_index(1) == 0);
    assert(n64_rsp_dmem_host_half_store_byte_index(0) == 1);
    assert(n64_rsp_dmem_host_half_store_byte_index(1) == 0);
#endif

    puts("RSP DMEM lane selector: PASS");
    return 0;
}
