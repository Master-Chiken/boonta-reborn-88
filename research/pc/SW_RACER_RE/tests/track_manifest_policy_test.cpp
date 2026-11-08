#include "../dinput_hook/track_manifest_policy.h"

#include <cstdint>
#include <iostream>
#include <string>

namespace {
int failures = 0;

void check(bool condition, const char *name) {
    if (condition) {
        std::cout << "PASS: " << name << '\n';
    } else {
        std::cerr << "FAIL: " << name << '\n';
        ++failures;
    }
}

std::string repeated(char ch, std::size_t n) {
    return std::string(n, ch);
}
}

int main() {
    using namespace track_manifest_policy;

    check(is_valid_slug("Tatooine_01-track.v2"), "slug accepts documented ASCII characters");
    check(!is_valid_slug(""), "slug rejects empty value");
    check(!is_valid_slug("."), "slug rejects dot");
    check(!is_valid_slug(".."), "slug rejects dot-dot");
    check(!is_valid_slug("../outside"), "slug rejects path traversal");
    check(!is_valid_slug("track/name"), "slug rejects path separator");
    check(!is_valid_slug("track name"), "slug rejects spaces");
    check(!is_valid_slug(repeated('a', kMaxSlugBytes + 1)), "slug rejects values over max length");

    std::string normalized;
    check(normalize_sha256(repeated('A', 64), &normalized) &&
              normalized == repeated('a', 64),
          "SHA-256 normalizes uppercase ASCII to lowercase");
    check(is_canonical_sha256(repeated('a', 64)), "canonical lowercase SHA-256 is accepted");
    check(!is_canonical_sha256(repeated('A', 64)), "non-canonical uppercase SHA-256 is rejected as a path key");
    check(!normalize_sha256(repeated('a', 63), &normalized), "SHA-256 rejects short digest");
    check(!normalize_sha256(repeated('g', 64), &normalized), "SHA-256 rejects non-hex characters");
    check(!normalize_sha256(repeated('a', 64), nullptr), "SHA-256 rejects null output");

    check(is_valid_asset_index_and_size(0, 1), "asset accepts lowest index and smallest size");
    check(is_valid_asset_index_and_size(999999, kMaxTrackAssetBytes), "asset accepts max index and max size");
    check(!is_valid_asset_index_and_size(-1, 1), "asset rejects negative index");
    check(!is_valid_asset_index_and_size(1000000, 1), "asset rejects index at exclusive limit");
    check(!is_valid_asset_index_and_size(0, 0), "asset rejects empty payload");
    check(!is_valid_asset_index_and_size(0, static_cast<int64_t>(kMaxTrackAssetBytes) + 1),
          "asset rejects payload above max size");

    check(is_valid_placement(0, 0, 0, -1), "placement accepts defaults");
    check(is_valid_placement(7, 255, 255, 24), "placement accepts upper boundaries");
    check(!is_valid_placement(-1, 0, 0, -1), "placement rejects negative planet");
    check(!is_valid_placement(8, 0, 0, -1), "placement rejects planet outside range");
    check(!is_valid_placement(0, -1, 0, -1), "placement rejects negative track number");
    check(!is_valid_placement(0, 0, 256, -1), "placement rejects favorite pilot above range");
    check(!is_valid_placement(0, 0, 0, 25), "placement rejects stock slot outside range");

    return failures == 0 ? 0 : 1;
}
