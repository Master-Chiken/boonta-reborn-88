#include "../dinput_hook/virtual_block_policy.h"

#include <cstdint>
#include <iostream>
#include <limits>

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
}

int main() {
    using namespace virtual_block_policy;
    uint64_t words = 0;
    uint64_t header = 0;

    check(words_per_entry(Kind::Model, &words) && words == 2,
          "model format uses two words per entry");
    check(words_per_entry(Kind::Spline, &words) && words == 1,
          "spline format uses one word per entry");
    check(words_per_entry(Kind::Texture, &words) && words == 2,
          "texture format uses two words per entry");
    check(!words_per_entry(Kind::Model, nullptr), "words-per-entry rejects null output");

    check(table_header_size(Kind::Model, 1, &header) && header == 16,
          "one-entry model header includes terminal offset");
    check(table_header_size(Kind::Spline, 1, &header) && header == 12,
          "one-entry spline header includes terminal offset");
    check(table_header_size(Kind::Texture, 1, &header) && header == 12,
          "one-entry texture header matches two-word entry");
    check(table_header_size(Kind::Texture, 0, &header) && header == 4,
          "empty texture header is just the count");
    check(!table_header_size(Kind::Model, kMaxBlockEntries + 1, &header),
          "table sizing rejects unreasonable entry count");
    check(!table_header_size(Kind::Model, 1, nullptr), "table sizing rejects null output");

    check(source_table_fits(Kind::Model, 1, 16), "exact-size model table fits");
    check(!source_table_fits(Kind::Model, 1, 15), "truncated model table is rejected");
    check(!source_table_fits(Kind::Spline, 1, 11), "truncated spline table is rejected");
    check(!source_table_fits(Kind::Texture, 1, 11), "truncated texture table is rejected");
    check(!source_table_fits(Kind::Spline, kMaxBlockEntries + 1, 64ULL * 1024ULL * 1024ULL),
          "source table rejects unreasonable entry count");
    check(!source_table_fits(Kind::Model, 0, 3), "source shorter than count field is rejected");

    check(source_entry_range_valid(16, 100, 16, 40), "payload range starting at table end is accepted");
    check(source_entry_range_valid(16, 100, 100, 100), "empty terminal range at EOF is accepted");
    check(!source_entry_range_valid(16, 100, 15, 40), "payload before table end is rejected");
    check(!source_entry_range_valid(16, 100, 40, 39), "reversed payload range is rejected");
    check(!source_entry_range_valid(16, 100, 40, 101), "payload past EOF is rejected");

    check(source_model_split_valid(16, 20, 32), "model mask split inside payload is accepted");
    check(!source_model_split_valid(16, 16, 32), "non-empty model rejects split at start");
    check(!source_model_split_valid(16, 33, 32), "model rejects split past entry end");
    check(source_model_split_valid(16, 16, 16), "empty source model entry remains accepted");

    check(source_texture_split_valid(16, 0, 40), "texture without palette is accepted");
    check(source_texture_split_valid(16, 16, 40), "palette beginning at pixel payload is accepted");
    check(source_texture_split_valid(16, 40, 40), "palette ending at entry end is accepted");
    check(!source_texture_split_valid(16, 15, 40), "texture palette before pixels is rejected");
    check(!source_texture_split_valid(16, 41, 40), "texture palette past entry end is rejected");

    check(range_within(4, 4, 4, 8), "read range exactly matching its bounds is accepted");
    check(range_within(5, 3, 4, 8), "read range fully inside its bounds is accepted");
    check(range_within(8, 0, 4, 8), "empty read at the end boundary is accepted");
    check(!range_within(7, 2, 4, 8), "read range crossing the end boundary is rejected");
    check(!range_within(3, 1, 4, 8), "read range starting before its bounds is rejected");
    check(!range_within(4, 1, 8, 4), "read range rejects reversed bounds");
    check(!range_within(std::numeric_limits<uint64_t>::max() - 1, 4, 0,
                        std::numeric_limits<uint64_t>::max()),
          "read range rejects overflow without adding offset and size");

    check(long_range_within(24, 4, 24, 8),
          "signed loader range accepts a read at a region's start");
    check(long_range_within(28, 4, 24, 8),
          "signed loader range accepts a read ending exactly at the region boundary");
    check(long_range_within(32, 0, 24, 8),
          "signed loader range accepts an empty read at the region end");
    check(!long_range_within(31, 2, 24, 8),
          "signed loader range rejects a read crossing a region boundary");
    check(!long_range_within(23, 1, 24, 8),
          "signed loader range rejects a read before the region");
    check(!long_range_within(-1, 1, 24, 8),
          "signed loader range rejects negative read offsets");
    check(!long_range_within(24, 1, -1, 8),
          "signed loader range rejects negative region offsets");
    check(!long_range_within(LONG_MAX, 1, 24, 8),
          "signed loader range rejects a read overflowing LONG_MAX");
    check(!long_range_within(24, 1, 24, std::numeric_limits<uint64_t>::max()),
          "signed loader range rejects a region exceeding LONG_MAX");

    check(source_path_matches("data/lev01/out_modelblock.bin",
                              "data/lev01/out_modelblock.bin"),
          "virtual view accepts the exact source archive path");
    check(!source_path_matches("data/lev01/out_modelblock.bin",
                               "assets/custom_tracks/track/out_modelblock.bin"),
          "virtual view rejects a different archive path");
    check(!source_path_matches("data/lev01/out_modelblock.bin", nullptr),
          "virtual view rejects a missing current archive path");
    check(!source_path_matches(nullptr, "data/lev01/out_modelblock.bin"),
          "virtual view rejects a missing stored source path");

    return failures == 0 ? 0 : 1;
}
