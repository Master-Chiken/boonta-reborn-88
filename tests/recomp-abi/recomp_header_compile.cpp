#include <recomp.h>

#include "n64_memory_be.h"
#include "ppc_memory_lane_compat.h"

#include <cstddef>
#include <cstdint>

#if !defined(__BYTE_ORDER__) || !defined(__ORDER_BIG_ENDIAN__)
#error "The PowerPC compiler must expose its target byte order"
#endif

#if __BYTE_ORDER__ != __ORDER_BIG_ENDIAN__
#error "This probe must be compiled for the big-endian PowerPC target"
#endif

#if !RECOMP_MEM_HOST_IS_BIG_ENDIAN
#error "The patched N64 memory macros must select natural big-endian byte lanes"
#endif

static_assert(RECOMP_MEM_BYTE_LANE(0x100) == 0x100, "PowerPC byte lanes must not be XOR-adjusted");
static_assert(RECOMP_MEM_HALF_LANE(0x100) == 0x100, "PowerPC halfword lanes must not be XOR-adjusted");

static_assert(sizeof(void *) == 4, "Wii/GameCube target pointers must be 32-bit");
static_assert(sizeof(uintptr_t) == 4, "Wii/GameCube uintptr_t must be 32-bit");
static_assert(sizeof(gpr) == 8, "N64 general-purpose register slots are 64-bit");
static_assert(sizeof(fpr) == 8, "N64 floating-point register slots are 64-bit");
static_assert(offsetof(fpr, d) == 0, "FPR double must start at offset zero");
static_assert(offsetof(fpr, u64) == 0, "FPR 64-bit integer must start at offset zero");
static_assert(offsetof(fpr, fh) == 0, "Big-endian FPR high float must be first");
static_assert(offsetof(fpr, fl) == 4, "Big-endian FPR low float must be second");
static_assert(offsetof(fpr, u32h) == 0, "Big-endian FPR high word must be first");
static_assert(offsetof(fpr, u32l) == 4, "Big-endian FPR low word must be second");
static_assert(offsetof(recomp_context, hi) == 512, "Unexpected recomp_context HI offset");
static_assert(offsetof(recomp_context, lo) == 520, "Unexpected recomp_context LO offset");
static_assert(offsetof(recomp_context, f_odd) == 528, "Unexpected recomp_context pointer offset");
static_assert(offsetof(recomp_context, status_reg) == 532, "Unexpected recomp_context status offset");
static_assert(offsetof(recomp_context, mips3_float_mode) == 536, "Unexpected recomp_context mode offset");
static_assert(sizeof(recomp_context) == 544, "Unexpected 32-bit PowerPC recomp_context size");

/*
 * Compile-only probe: exercise the real upstream declarations and macros.
 * This function is never executed by this workflow.
 */
RECOMP_FUNC void recomp_header_abi_probe(uint8_t *rdram, recomp_context *ctx) {
    int64_t signed_low = 0;
    int64_t signed_high = 0;
    uint64_t unsigned_low = 0;
    uint64_t unsigned_high = 0;
    int64_t quotient = 0;
    int64_t remainder = 0;
    uint64_t unsigned_quotient = 0;
    uint64_t unsigned_remainder = 0;

    DMULT((int64_t)ctx->r1, (int64_t)ctx->r2, &signed_low, &signed_high);
    DMULTU(ctx->r3, ctx->r4, &unsigned_low, &unsigned_high);
    DDIV((int64_t)ctx->r5, (int64_t)ctx->r6, &quotient, &remainder);
    DDIVU(ctx->r7, ctx->r8, &unsigned_quotient, &unsigned_remainder);

    ctx->r9 = ADD32(ctx->r9, ctx->r10);
    ctx->r11 = (gpr)MEM_BU(0, ctx->r12);
    MEM_B(1, ctx->r13) = (int8_t)ctx->r14;
    MEM_H(0, ctx->r13) = (int16_t)ctx->r14;
    MEM_HU(2, ctx->r13) = (uint16_t)ctx->r14;
    MEM_W(4, ctx->r13) = (int32_t)ctx->r14;
    SD(ctx->r15, 0, ctx->r16);

    ctx->lo = LD(0, ctx->r16);
    ctx->hi = (uint64_t)signed_high ^ unsigned_high;
    ctx->r17 = (gpr)signed_low ^ unsigned_low;
    ctx->r18 = (gpr)quotient ^ (gpr)remainder;
    ctx->r19 = unsigned_quotient ^ unsigned_remainder;

    set_cop1_cs(get_cop1_cs());
    ctx->status_reg = (uint32_t)CVT_W_D(1.5);
    ctx->r20 = (gpr)n64_be_read_u32(rdram, 0);
}
