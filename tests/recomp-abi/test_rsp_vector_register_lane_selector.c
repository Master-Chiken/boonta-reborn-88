#include "rsp_vector_register_endian.h"

#include <assert.h>
#include <stdio.h>

int main(void)
{
#if N64_RSP_VECTOR_HOST_BIG_ENDIAN
    assert(n64_rsp_vector_byte_storage_index(0) == 0);
    assert(n64_rsp_vector_byte_storage_index(7) == 7);
    assert(n64_rsp_vector_byte_storage_index(8) == 8);
    assert(n64_rsp_vector_byte_storage_index(15) == 15);
    assert(n64_rsp_vector_half_storage_index(0) == 0);
    assert(n64_rsp_vector_half_storage_index(3) == 3);
    assert(n64_rsp_vector_half_storage_index(4) == 4);
    assert(n64_rsp_vector_half_storage_index(7) == 7);
#else
    assert(n64_rsp_vector_byte_storage_index(0) == 15);
    assert(n64_rsp_vector_byte_storage_index(7) == 8);
    assert(n64_rsp_vector_byte_storage_index(8) == 7);
    assert(n64_rsp_vector_byte_storage_index(15) == 0);
    assert(n64_rsp_vector_half_storage_index(0) == 7);
    assert(n64_rsp_vector_half_storage_index(3) == 4);
    assert(n64_rsp_vector_half_storage_index(4) == 3);
    assert(n64_rsp_vector_half_storage_index(7) == 0);
#endif

    puts("RSP vector register lane selector: PASS");
    return 0;
}
