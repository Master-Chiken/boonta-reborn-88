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

#include <string.h>

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

/*
 * Status-returning read API for future generated-code integration.
 *
 * Unlike the legacy value-returning helpers below, this contract distinguishes
 * a legitimate zero loaded from guest RAM from a failed access. The output is
 * only modified after a successful access. Generated code must branch to its
 * memory-fault path whenever the returned status is not N64_SEGMENTED_OK.
 */
static inline n64_segmented_result n64_recomp_try_load(
    uint8_t *token,
    uint64_t guest_address,
    size_t width,
    uint64_t *output)
{
    n64_recomp_memory_handle *handle = n64_recomp_memory_from_token(token);
    uint64_t value = 0;
    n64_segmented_result result;

    if (handle == NULL || handle->memory == NULL || output == NULL) {
        result = N64_SEGMENTED_INVALID_ARGUMENT;
    } else {
        result = n64_segmented_read(
            handle->memory, guest_address, width, &value);
    }

    if (result != N64_SEGMENTED_OK) {
        n64_recomp_memory_record_fault(
            handle, result, guest_address, width, N64_SEGMENTED_ACCESS_READ);
        return result;
    }

    *output = value;
    handle->last_error = N64_SEGMENTED_OK;
    return N64_SEGMENTED_OK;
}

static inline n64_segmented_result n64_recomp_try_load_u8(
    uint8_t *token, uint64_t address, uint8_t *output)
{
    uint64_t value;
    n64_segmented_result result =
        n64_recomp_try_load(token, address, 1, &value);
    if (result == N64_SEGMENTED_OK) *output = (uint8_t)value;
    return result;
}

static inline n64_segmented_result n64_recomp_try_load_u16(
    uint8_t *token, uint64_t address, uint16_t *output)
{
    uint64_t value;
    n64_segmented_result result =
        n64_recomp_try_load(token, address, 2, &value);
    if (result == N64_SEGMENTED_OK) *output = (uint16_t)value;
    return result;
}

static inline n64_segmented_result n64_recomp_try_load_u32(
    uint8_t *token, uint64_t address, uint32_t *output)
{
    uint64_t value;
    n64_segmented_result result =
        n64_recomp_try_load(token, address, 4, &value);
    if (result == N64_SEGMENTED_OK) *output = (uint32_t)value;
    return result;
}

static inline n64_segmented_result n64_recomp_try_load_u64(
    uint8_t *token, uint64_t address, uint64_t *output)
{
    return n64_recomp_try_load(token, address, 8, output);
}

static inline n64_segmented_result n64_recomp_try_load_s8(
    uint8_t *token, uint64_t address, int8_t *output)
{
    uint64_t value;
    n64_segmented_result result =
        n64_recomp_try_load(token, address, 1, &value);
    if (result == N64_SEGMENTED_OK) *output = (int8_t)value;
    return result;
}

static inline n64_segmented_result n64_recomp_try_load_s16(
    uint8_t *token, uint64_t address, int16_t *output)
{
    uint64_t value;
    n64_segmented_result result =
        n64_recomp_try_load(token, address, 2, &value);
    if (result == N64_SEGMENTED_OK) *output = (int16_t)value;
    return result;
}

static inline n64_segmented_result n64_recomp_try_load_s32(
    uint8_t *token, uint64_t address, int32_t *output)
{
    uint64_t value;
    n64_segmented_result result =
        n64_recomp_try_load(token, address, 4, &value);
    if (result == N64_SEGMENTED_OK) *output = (int32_t)value;
    return result;
}

static inline n64_segmented_result n64_recomp_try_load_s64(
    uint8_t *token, uint64_t address, int64_t *output)
{
    uint64_t value;
    n64_segmented_result result =
        n64_recomp_try_load(token, address, 8, &value);
    if (result == N64_SEGMENTED_OK) *output = (int64_t)value;
    return result;
}

/*
 * Legacy convenience reads below keep the original value-returning probe
 * interface. They set last_error and return zero on failure; generated
 * production code must use n64_recomp_try_load() instead.
 */
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
 * Copy raw guest bytes through a checked, RAM-only span. The guest range must
 * fit in one backing region; callers that cross a region boundary must split
 * the request deliberately. This preserves the guest byte sequence rather
 * than converting it to a host numeric integer.
 */
static inline n64_segmented_result n64_recomp_copy_from_guest(
    uint8_t *token,
    uint64_t guest_address,
    void *destination,
    size_t length)
{
    n64_recomp_memory_handle *handle = n64_recomp_memory_from_token(token);
    uint8_t *source = NULL;
    n64_segmented_result result;

    if (handle == NULL || handle->memory == NULL ||
        destination == NULL || length == 0) {
        result = N64_SEGMENTED_INVALID_ARGUMENT;
    } else {
        result = n64_segmented_host_pointer_for_guest(
            handle->memory, guest_address, length,
            N64_SEGMENTED_ACCESS_READ, &source);
    }

    if (result != N64_SEGMENTED_OK) {
        n64_recomp_memory_record_fault(
            handle, result, guest_address, length, N64_SEGMENTED_ACCESS_READ);
        return result;
    }

    memmove(destination, source, length);
    handle->last_error = N64_SEGMENTED_OK;
    return N64_SEGMENTED_OK;
}

static inline n64_segmented_result n64_recomp_copy_to_guest(
    uint8_t *token,
    uint64_t guest_address,
    const void *source,
    size_t length)
{
    n64_recomp_memory_handle *handle = n64_recomp_memory_from_token(token);
    uint8_t *destination = NULL;
    n64_segmented_result result;

    if (handle == NULL || handle->memory == NULL ||
        source == NULL || length == 0) {
        result = N64_SEGMENTED_INVALID_ARGUMENT;
    } else {
        result = n64_segmented_host_pointer_for_guest(
            handle->memory, guest_address, length,
            N64_SEGMENTED_ACCESS_WRITE, &destination);
    }

    if (result != N64_SEGMENTED_OK) {
        n64_recomp_memory_record_fault(
            handle, result, guest_address, length, N64_SEGMENTED_ACCESS_WRITE);
        return result;
    }

    memmove(destination, source, length);
    handle->last_error = N64_SEGMENTED_OK;
    return N64_SEGMENTED_OK;
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
