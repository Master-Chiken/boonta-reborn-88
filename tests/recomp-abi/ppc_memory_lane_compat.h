#ifndef BOONTA_TESTS_RECOMP_ABI_PPC_MEMORY_LANE_COMPAT_H
#define BOONTA_TESTS_RECOMP_ABI_PPC_MEMORY_LANE_COMPAT_H

/*
 * Select byte lanes for the host architecture used to execute recompiled
 * N64 code. N64 RDRAM is big-endian.
 *
 * Little-endian hosts keep the original XOR lane adjustments. Big-endian
 * PowerPC hosts access the N64 byte layout directly.
 *
 * RECOMP_MEMORY_FORCE_BIG_ENDIAN_FOR_TEST is only for host unit tests of
 * the selector; production builds must use compiler target byte-order macros.
 */
#if defined(RECOMP_MEMORY_FORCE_BIG_ENDIAN_FOR_TEST)
#define RECOMP_MEM_HOST_IS_BIG_ENDIAN 1
#elif defined(__BYTE_ORDER__) && defined(__ORDER_BIG_ENDIAN__) && \
      (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN__)
#define RECOMP_MEM_HOST_IS_BIG_ENDIAN 1
#else
#define RECOMP_MEM_HOST_IS_BIG_ENDIAN 0
#endif

#if RECOMP_MEM_HOST_IS_BIG_ENDIAN
#define RECOMP_MEM_BYTE_LANE(address) (address)
#define RECOMP_MEM_HALF_LANE(address) (address)
#else
#define RECOMP_MEM_BYTE_LANE(address) ((address) ^ 3)
#define RECOMP_MEM_HALF_LANE(address) ((address) ^ 2)
#endif

#endif
