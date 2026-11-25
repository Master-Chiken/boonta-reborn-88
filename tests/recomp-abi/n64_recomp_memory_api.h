#ifndef BOONTA_TESTS_RECOMP_ABI_N64_RECOMP_MEMORY_API_H
#define BOONTA_TESTS_RECOMP_ABI_N64_RECOMP_MEMORY_API_H

/*
 * Experimental C-compatible bridge from N64Recomp's historical uint8_t*
 * "rdram" argument to the segmented memory reference model.
 *
 * The pointer passed to generated functions is an opaque context token. It is
 * not a host pointer to a contiguous guest RAM image. Use read/write helpers
 * for scalar accesses and the RAM-only conversion for libultra TO_PTR.
 *
 * This file is a clean-room integration prototype. It is not patched into
 * upstream N64Recomp or N64ModernRuntime.
 */

#include "n64_segmented_memory.h"

typedef struct n64_recomp_memory_handle n64_recomp_memory_handle;

typedef void (*n64_recomp_memory_fault_fn)(
    void *context,
    n64_segmented_result result,
    uint64_t guest_address,
    size_t width,
    n64_segmented_access access);

struct n64_recomp_memory_handle {
    n64_segmented_memory *memory;
    n64_segmented_result last_error;
    n64_recomp_memory_fault_fn fault;
    void *fault_context;
};

static inline void n64_recomp_memory_handle_init(
    n64_recomp_memory_handle *handle,
    n64_segmented_memory *memory,
    n64_recomp_memory_fault_fn fault,
    void *fault_context)
{
    if (handle == NULL) return;
    handle->memory = memory;
    handle->last_error = N64_SEGMENTED_OK;
    handle->fault = fault;
    handle->fault_context = fault_context;
}

static inline uint8_t *n64_recomp_memory_token(n64_recomp_memory_handle *handle)
{
    /* The generated ABI still says uint8_t*, but the value is opaque. */
    return (uint8_t *)(void *)handle;
}

static inline n64_recomp_memory_handle *n64_recomp_memory_from_token(
    const uint8_t *token)
{
    return (n64_recomp_memory_handle *)(void *)token;
}

static inline void n64_recomp_memory_record_fault(
    n64_recomp_memory_handle *handle,
    n64_segmented_result result,
    uint64_t guest_address,
    size_t width,
    n64_segmented_access access)
{
    if (handle == NULL) return;
    handle->last_error = result;
    if (handle->fault != NULL) {
        handle->fault(handle->fault_context, result, guest_address, width, access);
    }
}

static inline n64_segmented_result n64_recomp_memory_last_error(
    const uint8_t *token)
{
    n64_recomp_memory_handle *handle = n64_recomp_memory_from_token(token);
    return handle == NULL ? N64_SEGMENTED_INVALID_ARGUMENT : handle->last_error;
}

static inline void n64_recomp_memory_clear_error(uint8_t *token)
{
    n64_recomp_memory_handle *handle = n64_recomp_memory_from_token(token);
    if (handle != NULL) handle->last_error = N64_SEGMENTED_OK;
}

static inline uint64_t n64_recomp_load_unsigned(
    uint8_t *token, uint64_t guest_address, size_t width)
{
    n64_recomp_memory_handle *handle = n64_recomp_memory_from_token(token);
    uint64_t value = 0;
    n64_segmented_result result;

    if (handle == NULL || handle->memory == NULL) {
        n64_recomp_memory_record_fault(
            handle, N64_SEGMENTED_INVALID_ARGUMENT, guest_address, width,
            N64_SEGMENTED_ACCESS_READ);
        return 0;
    }

    result = n64_segmented_read(handle->memory, guest_address, width, &value);
    if (result != N64_SEGMENTED_OK) {
        n64_recomp_memory_record_fault(
            handle, result, guest_address, width, N64_SEGMENTED_ACCESS_READ);
        return 0;
    }

    handle->last_error = N64_SEGMENTED_OK;
    return value;
}

static inline uint64_t n64_recomp_load_s8(uint8_t *token, uint64_t address)
{
    return (uint64_t)(int64_t)(int8_t)n64_recomp_load_unsigned(token, address, 1);
}

static inline uint64_t n64_recomp_load_u8(uint8_t *token, uint64_t address)
{
    return n64_recomp_load_unsigned(token, address, 1);
}

static inline uint64_t n64_recomp_load_s16(uint8_t *token, uint64_t address)
{
    return (uint64_t)(int64_t)(int16_t)n64_recomp_load_unsigned(token, address, 2);
}

static inline uint64_t n64_recomp_load_u16(uint8_t *token, uint64_t address)
{
    return n64_recomp_load_unsigned(token, address, 2);
}

static inline uint64_t n64_recomp_load_s32(uint8_t *token, uint64_t address)
{
    return (uint64_t)(int64_t)(int32_t)n64_recomp_load_unsigned(token, address, 4);
}

static inline uint64_t n64_recomp_load_u32(uint8_t *token, uint64_t address)
{
    return n64_recomp_load_unsigned(token, address, 4);
}

static inline uint64_t n64_recomp_load_u64(uint8_t *token, uint64_t address)
{
    return n64_recomp_load_unsigned(token, address, 8);
}

static inline n64_segmented_result n64_recomp_store(
    uint8_t *token, uint64_t guest_address, size_t width, uint64_t value)
{
    n64_recomp_memory_handle *handle = n64_recomp_memory_from_token(token);
    n64_segmented_result result;

    if (handle == NULL || handle->memory == NULL) {
        result = N64_SEGMENTED_INVALID_ARGUMENT;
    } else {
        result = n64_segmented_write(handle->memory, guest_address, width, value);
    }

    if (result != N64_SEGMENTED_OK) {
        n64_recomp_memory_record_fault(
            handle, result, guest_address, width, N64_SEGMENTED_ACCESS_WRITE);
    } else if (handle != NULL) {
        handle->last_error = N64_SEGMENTED_OK;
    }
    return result;
}

static inline n64_segmented_result n64_recomp_store_u8(
    uint8_t *token, uint64_t address, uint8_t value)
{
    return n64_recomp_store(token, address, 1, value);
}

static inline n64_segmented_result n64_recomp_store_u16(
    uint8_t *token, uint64_t address, uint16_t value)
{
    return n64_recomp_store(token, address, 2, value);
}

static inline n64_segmented_result n64_recomp_store_u32(
    uint8_t *token, uint64_t address, uint32_t value)
{
    return n64_recomp_store(token, address, 4, value);
}

static inline n64_segmented_result n64_recomp_store_u64(
    uint8_t *token, uint64_t address, uint64_t value)
{
    return n64_recomp_store(token, address, 8, value);
}

/*
 * RAM-only equivalent of TO_PTR. The caller must supply the complete object
 * size. The void form is intentionally separate because sizeof(void) is not
 * portable and callers such as free() only need to validate the first byte.
 */
static inline void *n64_recomp_to_host_pointer(
    uint8_t *token, uint64_t guest_address, size_t object_size)
{
    n64_recomp_memory_handle *handle = n64_recomp_memory_from_token(token);
    uint8_t *host_pointer = NULL;
    n64_segmented_result result;

    if (handle == NULL || handle->memory == NULL) {
        result = N64_SEGMENTED_INVALID_ARGUMENT;
    } else {
        result = n64_segmented_host_pointer_for_guest(
            handle->memory, guest_address, object_size,
            N64_SEGMENTED_ACCESS_READ, &host_pointer);
    }

    if (result != N64_SEGMENTED_OK) {
        n64_recomp_memory_record_fault(
            handle, result, guest_address, object_size,
            N64_SEGMENTED_ACCESS_READ);
        return NULL;
    }
    handle->last_error = N64_SEGMENTED_OK;
    return host_pointer;
}

#define N64_RECOMP_TO_PTR(type, token, guest_address) \
    ((type *)n64_recomp_to_host_pointer((token), (guest_address), sizeof(type)))

#define N64_RECOMP_TO_PTR_VOID(token, guest_address) \
    ((void *)n64_recomp_to_host_pointer((token), (guest_address), 1))

#endif
