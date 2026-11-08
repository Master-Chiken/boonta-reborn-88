#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace track_manifest_policy {

inline constexpr uint32_t kMaxTrackAssetBytes = 64U * 1024U * 1024U;
inline constexpr uint64_t kMaxBlockIndexExclusive = 1'000'000ULL;
inline constexpr size_t kMaxSlugBytes = 128;

inline bool is_slug_character(unsigned char ch) noexcept {
    return (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
           (ch >= '0' && ch <= '9') || ch == '.' || ch == '_' || ch == '-';
}

inline bool is_valid_slug(std::string_view slug) noexcept {
    if (slug.empty() || slug.size() > kMaxSlugBytes || slug == "." || slug == "..")
        return false;
    for (unsigned char ch : slug) {
        if (!is_slug_character(ch))
            return false;
    }
    return true;
}

// Normalize a SHA-256 hex digest to lowercase ASCII. This is locale-independent because hashes
// are protocol identifiers, not human-language text.
inline bool normalize_sha256(std::string_view sha, std::string *normalized) {
    if (normalized == nullptr || sha.size() != 64)
        return false;

    normalized->clear();
    normalized->reserve(64);
    for (unsigned char ch : sha) {
        if (ch >= '0' && ch <= '9') {
            normalized->push_back(static_cast<char>(ch));
        } else if (ch >= 'a' && ch <= 'f') {
            normalized->push_back(static_cast<char>(ch));
        } else if (ch >= 'A' && ch <= 'F') {
            normalized->push_back(static_cast<char>(ch - 'A' + 'a'));
        } else {
            normalized->clear();
            return false;
        }
    }
    return true;
}

inline bool is_canonical_sha256(std::string_view sha) {
    std::string normalized;
    return normalize_sha256(sha, &normalized) && normalized == sha;
}

inline bool is_valid_asset_index_and_size(int64_t index, int64_t size) noexcept {
    return index >= 0 &&
           static_cast<uint64_t>(index) < kMaxBlockIndexExclusive &&
           size > 0 && static_cast<uint64_t>(size) <= kMaxTrackAssetBytes;
}

inline bool is_valid_placement(int64_t planet, int64_t planet_track_number,
                               int64_t favorite_pilot, int64_t overrides_stock_slot) noexcept {
    return planet >= 0 && planet < 8 &&
           planet_track_number >= 0 && planet_track_number <= 255 &&
           favorite_pilot >= 0 && favorite_pilot <= 255 &&
           overrides_stock_slot >= -1 && overrides_stock_slot < 25;
}

} // namespace track_manifest_policy
