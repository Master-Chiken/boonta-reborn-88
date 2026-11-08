#pragma once

#include <cstdint>
#include <climits>
#include <limits>
#include <cstring>

namespace virtual_block_policy {

enum class Kind {
    Model,
    Spline,
    Texture,
};

inline constexpr uint64_t kMaxBlockEntries = 1'000'000ULL;

// Checks whether [offset, offset + size) is contained in [begin, end) without
// forming offset + size, which could overflow for untrusted read ranges.
inline bool range_within(uint64_t offset, uint64_t size, uint64_t begin,
                         uint64_t end) noexcept {
    return begin <= end && offset >= begin && offset <= end && size <= end - offset;
}

// Checks a loader's signed-long read against a virtual region without signed overflow.
// LONG_MAX is platform-dependent (32-bit in the game's Windows build).
inline bool long_range_within(long offset, uint64_t size, long begin,
                              uint64_t region_size) noexcept {
    if (offset < 0 || begin < 0)
        return false;
    const uint64_t max_offset = static_cast<uint64_t>(LONG_MAX);
    const uint64_t read_begin = static_cast<uint64_t>(offset);
    const uint64_t region_begin = static_cast<uint64_t>(begin);
    if (size > max_offset || read_begin > max_offset - size ||
        region_size > max_offset - region_begin)
        return false;
    return range_within(read_begin, size, region_begin, region_begin + region_size);
}

inline bool words_per_entry(Kind kind, uint64_t *out) noexcept {
    if (out == nullptr)
        return false;
    switch (kind) {
        case Kind::Model:
        case Kind::Texture:
            *out = 2;
            return true;
        case Kind::Spline:
            *out = 1;
            return true;
    }
    return false;
}

// Number of 32-bit words following the count field. Model blocks store two words per entry plus
// one terminal offset; spline blocks store one offset per entry plus a terminal offset; texture
// blocks store two words per entry and terminate the final payload at EOF.
inline bool table_word_count(Kind kind, uint64_t count, uint64_t *out) noexcept {
    if (out == nullptr || count > kMaxBlockEntries)
        return false;
    switch (kind) {
        case Kind::Model:
            *out = 2ULL * count + 1ULL;
            return true;
        case Kind::Spline:
            *out = count + 1ULL;
            return true;
        case Kind::Texture:
            *out = 2ULL * count;
            return true;
    }
    return false;
}

inline bool table_header_size(Kind kind, uint64_t count, uint64_t *out) noexcept {
    if (out == nullptr)
        return false;
    uint64_t words = 0;
    if (!table_word_count(kind, count, &words) ||
        words > (std::numeric_limits<uint64_t>::max() - 4ULL) / 4ULL)
        return false;
    *out = 4ULL + 4ULL * words;
    return true;
}

inline bool source_table_fits(Kind kind, uint64_t count, uint64_t file_length) noexcept {
    if (file_length < 4)
        return false;
    uint64_t header_size = 0;
    return table_header_size(kind, count, &header_size) && header_size <= file_length &&
           header_size <= std::numeric_limits<uint32_t>::max();
}

inline bool source_entry_range_valid(uint64_t table_end, uint64_t file_length,
                                     uint64_t first, uint64_t next) noexcept {
    return first >= table_end && next >= first && next <= file_length;
}

// A non-empty model has a mask followed by its model payload. An empty source entry is accepted
// exactly as before; replacement-model validation happens separately when an override is built.
inline bool source_model_split_valid(uint64_t first, uint64_t second,
                                    uint64_t next) noexcept {
    return next == first || (second > first && second <= next);
}

// A texture palette offset of zero means that there is no palette.
inline bool source_texture_split_valid(uint64_t first, uint64_t second,
                                       uint64_t next) noexcept {
    return second == 0 || (second >= first && second <= next);
}

// A view is only safe for the exact archive it was built against. A missing current
// path is not a match: treating nullptr as "no mismatch" can expose stale file offsets.
inline bool source_path_matches(const char *source_path, const char *current_path) noexcept {
    return source_path != nullptr && current_path != nullptr &&
           std::strcmp(source_path, current_path) == 0;
}

} // namespace virtual_block_policy
