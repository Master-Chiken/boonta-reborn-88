#include "virtual_block.h"

#include <algorithm>
#include <charconv>
#include <climits>
#include <cstring>
#include <filesystem>
#include <limits>
#include <map>
#include <optional>
#include <string>
#include <system_error>

#include "hook_helper.h"
#include "patch.h"
#include "custom_tracks.h"// SWR_*BLOCK_PATH_PTR

extern "C" FILE *hook_log;

namespace {
    // Indexed by swrLoader_TYPE, which the game uses as a small dense enum.
    constexpr int NUM_BLOCK_TYPES = 4;

    std::optional<VirtualBlockView> views[NUM_BLOCK_TYPES];

    // Reads served from a view vs delegated to the file, per type. Reported on close so a load can
    // be seen to have gone through the view without logging every read (there are thousands).
    struct ReadStats {
        uint32_t from_header;
        uint32_t from_memory;
        uint32_t from_file;
        uint32_t unmapped;
        uint32_t wrong_block;// the path was swapped, so the view does not describe this file
    };
    ReadStats stats[NUM_BLOCK_TYPES];

    bool valid_type(swrLoader_TYPE type) {
        return (int) type >= 0 && (int) type < NUM_BLOCK_TYPES;
    }

    const char *type_name(swrLoader_TYPE type) {
        switch (type) {
            case swrLoader_TYPE_MODEL_BLOCK:
                return "model";
            case swrLoader_TYPE_SPRITE_BLOCK:
                return "sprite";
            case swrLoader_TYPE_SPLINE_BLOCK:
                return "spline";
            case swrLoader_TYPE_TEXTURE_BLOCK:
                return "texture";
            default:
                return "?";
        }
    }

    // The region covering [offset, offset + size), or nullptr when the read spans a boundary or
    // falls in a hole.
    const VirtualRegion *find_region(const VirtualBlockView &view, long offset, size_t size) {
        // Reject negative or overflowing ranges before doing signed-long arithmetic.
        if (offset < 0 || size > static_cast<size_t>(LONG_MAX))
            return nullptr;
        const long span = static_cast<long>(size);
        if (offset > LONG_MAX - span)
            return nullptr;

        auto it = std::upper_bound(view.regions.begin(), view.regions.end(), offset,
                                   [](long value, const VirtualRegion &region) {
                                       return value < region.virtual_offset;
                                   });
        if (it == view.regions.begin())
            return nullptr;

        --it;
        const long region_size = static_cast<long>(it->size);
        if (offset < it->virtual_offset || it->virtual_offset > LONG_MAX - region_size)
            return nullptr;
        if (offset + span <= it->virtual_offset + region_size)
            return &*it;
        return nullptr;
    }
}

namespace {
    // Words per table entry. The loader reads a model entry as three consecutive words
    // (mask_off, model_off, and the next entry's mask_off as its end), a texture entry as two
    // (pixels_off, palette_off, ending where the next entry's pixels begin) and a spline entry as
    // one (ending at the next entry's offset). Every layout therefore needs one extra slot past
    // the last entry to terminate it.
    int table_words(swrLoader_TYPE type) {
        switch (type) {
            case swrLoader_TYPE_MODEL_BLOCK:
            case swrLoader_TYPE_TEXTURE_BLOCK:
                return 2;
            case swrLoader_TYPE_SPLINE_BLOCK:
                return 1;
            default:
                return 0;
        }
    }

    uint64_t table_header_size(swrLoader_TYPE type, uint64_t count) {
        if (type == swrLoader_TYPE_MODEL_BLOCK)
            return 4ULL + 4ULL * (2ULL * count + 1ULL);
        if (type == swrLoader_TYPE_SPLINE_BLOCK)
            return 4ULL + 4ULL * (count + 1ULL);
        if (type == swrLoader_TYPE_TEXTURE_BLOCK)
            return 4ULL + 8ULL * count;
        return 0;
    }

    uint32_t read_be32(const std::vector<uint8_t> &bytes, size_t offset) {
        return (uint32_t) bytes[offset] << 24 | (uint32_t) bytes[offset + 1] << 16 |
            (uint32_t) bytes[offset + 2] << 8 | (uint32_t) bytes[offset + 3];
    }

    void write_be32(std::vector<uint8_t> &bytes, size_t offset, uint32_t value) {
        bytes[offset] = (uint8_t) (value >> 24);
        bytes[offset + 1] = (uint8_t) (value >> 16);
        bytes[offset + 2] = (uint8_t) (value >> 8);
        bytes[offset + 3] = (uint8_t) value;
    }

    // One entry of the source block: where its payload starts and ends, and where its second
    // section begins relative to the start (0 when it has none).
    struct SourceEntry {
        uint32_t begin;
        uint32_t end;
        uint32_t split;
    };

    bool read_source_entries(swrLoader_TYPE type, const char *path,
                             std::vector<SourceEntry> *entries) {
        if (entries == nullptr || path == nullptr)
            return false;
        const int words = table_words(type);
        if (words == 0)
            return false;

        FILE *f = fopen(path, "rb");
        if (!f)
            return false;
        if (fseek(f, 0, SEEK_END) != 0) {
            fclose(f);
            return false;
        }
        const long file_length = ftell(f);
        if (file_length < 4 || fseek(f, 0, SEEK_SET) != 0) {
            fclose(f);
            return false;
        }

        uint8_t count_bytes[4] = {};
        if (fread(count_bytes, 1, sizeof(count_bytes), f) != sizeof(count_bytes)) {
            fclose(f);
            return false;
        }
        const uint32_t count = (uint32_t) count_bytes[0] << 24 |
                               (uint32_t) count_bytes[1] << 16 |
                               (uint32_t) count_bytes[2] << 8 |
                               (uint32_t) count_bytes[3];

        // The stock formats differ at the tail of their offset tables:
        // model = 2 words per entry plus one final model-end offset;
        // spline = one offset per entry plus one final end offset;
        // texture = exactly two words per entry, with the final texture ending at EOF.
        constexpr uint32_t MAX_BLOCK_ENTRIES = 1'000'000;
        if (count > MAX_BLOCK_ENTRIES) {
            fclose(f);
            return false;
        }
        uint64_t table_words_count = 0;
        if (type == swrLoader_TYPE_MODEL_BLOCK)
            table_words_count = 2ULL * count + 1ULL;
        else if (type == swrLoader_TYPE_SPLINE_BLOCK)
            table_words_count = static_cast<uint64_t>(count) + 1ULL;
        else if (type == swrLoader_TYPE_TEXTURE_BLOCK)
            table_words_count = 2ULL * count;
        else {
            fclose(f);
            return false;
        }

        const uint64_t table_bytes64 = 4ULL * table_words_count;
        const uint64_t table_end64 = 4ULL + table_bytes64;
        if (table_bytes64 > std::numeric_limits<size_t>::max() ||
            table_end64 > static_cast<uint64_t>(file_length)) {
            fclose(f);
            return false;
        }

        std::vector<uint8_t> table;
        try {
            table.resize(static_cast<size_t>(table_bytes64));
        } catch (...) {
            fclose(f);
            return false;
        }
        if (!table.empty() && fread(table.data(), 1, table.size(), f) != table.size()) {
            fclose(f);
            return false;
        }
        fclose(f);

        const uint32_t table_end = static_cast<uint32_t>(table_end64);
        entries->clear();
        try {
            entries->resize(count);
        } catch (...) {
            return false;
        }

        for (uint32_t i = 0; i < count; i++) {
            const size_t table_offset = 4u * static_cast<size_t>(words) * i;
            const uint32_t first = read_be32(table, table_offset);
            uint32_t second = 0;
            uint32_t next_first = 0;

            if (words == 2) {
                second = read_be32(table, table_offset + 4);
                if (type == swrLoader_TYPE_TEXTURE_BLOCK) {
                    next_first = (i + 1 < count)
                                     ? read_be32(table, 4u * static_cast<size_t>(words) * (i + 1u))
                                     : static_cast<uint32_t>(file_length);
                } else {
                    next_first = read_be32(table, 4u * static_cast<size_t>(words) * (i + 1u));
                }
            } else {
                next_first = read_be32(table, 4u * static_cast<size_t>(words) * (i + 1u));
            }

            if (first < table_end || next_first < first ||
                next_first > static_cast<uint64_t>(file_length)) {
                entries->clear();
                return false;
            }

            uint32_t split = 0;
            if (words == 2) {
                if (type == swrLoader_TYPE_MODEL_BLOCK) {
                    if (next_first != first && (second <= first || second > next_first)) {
                        entries->clear();
                        return false;
                    }
                    split = second >= first ? second - first : 0;
                } else {
                    // For textures, palette offset zero means no palette is present.
                    if (second != 0 && (second < first || second > next_first)) {
                        entries->clear();
                        return false;
                    }
                    split = second != 0 ? second - first : 0;
                }
            }

            (*entries)[i] = {first, next_first, split};
        }
        return true;
    }
}

bool virtual_block_BuildView(swrLoader_TYPE type, const char *source_path,
                             std::vector<VirtualOverride> overrides, VirtualBlockView *out) {
    const int words = table_words(type);
    if (words == 0 || source_path == nullptr || out == nullptr)
        return false;

    std::vector<SourceEntry> source;
    if (!read_source_entries(type, source_path, &source)) {
        if (hook_log) {
            fprintf(hook_log, "[virtual_block] cannot read or validate source block '%s'\n",
                    source_path);
            fflush(hook_log);
        }
        return false;
    }

    constexpr uint32_t MAX_BLOCK_ENTRIES = 1'000'000;
    std::sort(overrides.begin(), overrides.end(),
              [](const VirtualOverride &a, const VirtualOverride &b) {
                  return a.index < b.index;
              });

    uint64_t count64 = source.size();
    uint32_t previous_index = 0;
    bool have_previous = false;
    for (const VirtualOverride &entry: overrides) {
        if (entry.index == UINT32_MAX || entry.payload.empty() ||
            entry.payload.size() > UINT32_MAX || entry.split > entry.payload.size()) {
            if (hook_log) {
                fprintf(hook_log, "[virtual_block] malformed override for entry %u\n", entry.index);
                fflush(hook_log);
            }
            return false;
        }
        if (have_previous && entry.index == previous_index) {
            if (hook_log) {
                fprintf(hook_log, "[virtual_block] duplicate override index %u\n", entry.index);
                fflush(hook_log);
            }
            return false;
        }
        have_previous = true;
        previous_index = entry.index;

        if (type == swrLoader_TYPE_MODEL_BLOCK &&
            (entry.split == 0 || entry.split >= entry.payload.size()))
            return false;
        if (type == swrLoader_TYPE_TEXTURE_BLOCK &&
            entry.split >= entry.payload.size() && entry.split != 0)
            return false;
        if (type == swrLoader_TYPE_SPLINE_BLOCK && entry.split != 0)
            return false;

        count64 = std::max(count64, static_cast<uint64_t>(entry.index) + 1ULL);
    }

    if (count64 > MAX_BLOCK_ENTRIES)
        return false;
    const uint64_t header_size64 = table_header_size(type, count64);
    if (header_size64 > UINT32_MAX || header_size64 > static_cast<uint64_t>(LONG_MAX) ||
        header_size64 > std::numeric_limits<size_t>::max())
        return false;

    VirtualBlockView view;
    view.source_path = source_path;
    view.owned.reserve(overrides.size());
    const uint32_t count = static_cast<uint32_t>(count64);
    view.header.assign(static_cast<size_t>(header_size64), 0);
    view.regions.reserve(static_cast<size_t>(count));
    write_be32(view.header, 0, count);

    uint64_t cursor = header_size64;
    size_t override_index = 0;
    for (uint32_t i = 0; i < count; i++) {
        VirtualOverride *replacement = nullptr;
        if (override_index < overrides.size() && overrides[override_index].index == i)
            replacement = &overrides[override_index++];

        uint64_t size = 0;
        uint32_t split = 0;
        if (replacement != nullptr) {
            split = replacement->split;
            size = replacement->payload.size();
            if (cursor + size > UINT32_MAX || cursor + size > static_cast<uint64_t>(LONG_MAX))
                return false;
            view.owned.push_back(std::move(replacement->payload));
            view.regions.push_back({static_cast<long>(cursor), static_cast<uint32_t>(size),
                                    view.owned.back().data(), 0});
        } else if (i < source.size() && source[i].end > source[i].begin) {
            size = static_cast<uint64_t>(source[i].end) - source[i].begin;
            if (cursor + size > UINT32_MAX || cursor + size > static_cast<uint64_t>(LONG_MAX))
                return false;
            split = source[i].split;
            view.regions.push_back({static_cast<long>(cursor), static_cast<uint32_t>(size),
                                    nullptr, static_cast<long>(source[i].begin)});
        } else if (i >= source.size()) {
            // Extending a block with sparse indices would create malformed entries. Do not install
            // a partial view that can crash when the game requests one of those gaps.
            if (hook_log) {
                fprintf(hook_log, "[virtual_block] missing extension entry %u; refusing view\n", i);
                fflush(hook_log);
            }
            return false;
        }

        write_be32(view.header, 4u + 4u * static_cast<size_t>(words) * i,
                   static_cast<uint32_t>(cursor));
        if (words == 2) {
            const uint32_t second =
                type == swrLoader_TYPE_MODEL_BLOCK
                    ? static_cast<uint32_t>(cursor + (size != 0 ? split : 0))
                    : (size != 0 && split != 0 ? static_cast<uint32_t>(cursor + split) : 0);
            write_be32(view.header, 4u + 4u * static_cast<size_t>(words) * i + 4, second);
        }
        cursor += size;
    }

    if (cursor > UINT32_MAX || cursor > static_cast<uint64_t>(LONG_MAX))
        return false;
    if (type != swrLoader_TYPE_TEXTURE_BLOCK)
        write_be32(view.header, 4u + 4u * static_cast<size_t>(words) * count,
                   static_cast<uint32_t>(cursor));

    *out = std::move(view);
    return true;
}


void virtual_block_Install(swrLoader_TYPE type, VirtualBlockView view) {
    if (!valid_type(type))
        return;

    views[type] = std::move(view);
    stats[type] = {};
    fprintf(hook_log, "[virtual_block] installed %s view: %u byte header, %u region(s)\n",
            type_name(type), (unsigned) views[type]->header.size(),
            (unsigned) views[type]->regions.size());
    fflush(hook_log);
}

void virtual_block_Remove(swrLoader_TYPE type) {
    if (!valid_type(type) || !views[type].has_value())
        return;

    fprintf(hook_log, "[virtual_block] removed %s view\n", type_name(type));
    fflush(hook_log);
    views[type].reset();
}

bool virtual_block_IsInstalled(swrLoader_TYPE type) {
    return valid_type(type) && views[type].has_value();
}

namespace {
    typedef FILE **(*swrLoader_TypeToFileFn)(swrLoader_TYPE);

    FILE *block_handle(swrLoader_TYPE type) {
        FILE **file = ((swrLoader_TypeToFileFn) swrLoader_TypeToFile_ADDR)(type);
        return file ? *file : nullptr;
    }

    // The path pointer the game reads when it opens a block. Swapping these is how a custom track
    // substitutes its own archive; the sprite block is never swapped.
    const char **block_path(swrLoader_TYPE type) {
        switch (type) {
            case swrLoader_TYPE_SPLINE_BLOCK:
                return SWR_SPLINEBLOCK_PATH_PTR;
            case swrLoader_TYPE_TEXTURE_BLOCK:
                return SWR_TEXTUREBLOCK_PATH_PTR;
            case swrLoader_TYPE_MODEL_BLOCK:
                return SWR_MODELBLOCK_PATH_PTR;
            default:
                return nullptr;
        }
    }

    // Opens are frequent; only a change of the path a block reads is worth a line.
    std::string last_open_path[NUM_BLOCK_TYPES];
}

const char **virtual_block_SourcePath(swrLoader_TYPE type) {
    return block_path(type);
}

// 0x0042d680
void swrLoader_OpenBlock_delta(swrLoader_TYPE type) {
    // The game opens a block only when its handle is NULL, so a path swap while the handle is still
    // open is silently ignored and the next read comes from the previous archive. Log what the
    // handle and the path pointer are on the way in; a mismatch is the bug.
    const char **path = block_path(type);
    if (path != nullptr && valid_type(type) && last_open_path[type] != (*path ? *path : "")) {
        last_open_path[type] = *path ? *path : "";
        fprintf(hook_log, "[virtual_block] %s block now reads '%s' (handle=%p on entry)\n",
                type_name(type), last_open_path[type].c_str(), (const void *) block_handle(type));
        fflush(hook_log);
    }

    // The real file is opened either way: a view falls back to it for every entry it does not
    // override, and the game's own handle is what the original ReadAt uses.
    hook_call_original(swrLoader_OpenBlock, type);
}

// 0x0042d640
size_t swrLoader_ReadAt_delta(swrLoader_TYPE type, long offset, void *dst, size_t size) {
    if (!valid_type(type) || !views[type].has_value())
        return hook_call_original(swrLoader_ReadAt, type, offset, dst, size);

    const VirtualBlockView &view = *views[type];
    if (dst == nullptr && size != 0)
        return 0;

    // A view's fall-through offsets only mean anything in the block it was built from, and a
    // custom track swaps the block path out from under us. Serve the real file instead.
    const char **path = block_path(type);
    if (path != nullptr && *path != nullptr && view.source_path != *path) {
        stats[type].wrong_block++;
        return hook_call_original(swrLoader_ReadAt, type, offset, dst, size);
    }

    if (offset >= 0 && size <= static_cast<size_t>(LONG_MAX) &&
        offset <= LONG_MAX - static_cast<long>(size) &&
        offset + static_cast<long>(size) <= static_cast<long>(view.header.size())) {
        memcpy(dst, view.header.data() + offset, size);
        stats[type].from_header++;
        return 1;// the original returns fread's element count
    }

    if (const VirtualRegion *region = find_region(view, offset, size)) {
        const long within = offset - region->virtual_offset;
        if (region->memory != nullptr) {
            memcpy(dst, region->memory + within, size);
            stats[type].from_memory++;
            return 1;
        }
        stats[type].from_file++;
        return hook_call_original(swrLoader_ReadAt, type, region->file_offset + within, dst, size);
    }

    // Not covered by the view: pass the read through unchanged rather than failing it, so a
    // consumer we have not accounted for still sees the real block.
    stats[type].unmapped++;
    return hook_call_original(swrLoader_ReadAt, type, offset, dst, size);
}

// 0x0042d6f0
void swrLoader_CloseBlock_delta(swrLoader_TYPE type) {
    if (valid_type(type) && views[type].has_value()) {
        const ReadStats &s = stats[type];
        fprintf(hook_log,
                "[virtual_block] %s block closed: %u header, %u memory, %u file, %u unmapped, "
                "%u other-block read(s)\n",
                type_name(type), s.from_header, s.from_memory, s.from_file, s.unmapped,
                s.wrong_block);
        fflush(hook_log);
        stats[type] = {};
    }

    hook_call_original(swrLoader_CloseBlock, type);
}

// Replacing a reverse-hooked function detours the stock address but leaves the decomp reimpl in
// src/ unpatched, so delta code that calls the reimpl symbol stops reaching the stock code and
// runs the dormant body instead. For this family that is a real behaviour change:
// src/Swr/swrLoader.c's swrLoader_OpenBlock has the block paths hardcoded, while the stock code
// reads them from the pointers a custom track swaps -- so swrModel_InitializeTextureBuffer_delta,
// which calls the reimpl symbol, would silently re-open the stock archive and size the texture
// buffer from it (custom-track textures then render white). Route the reimpl at our delta too, so
// every caller lands in one place regardless of which symbol it called.
static void route_reimpl_to_delta(void *reimpl, void *delta) {
    uint8_t jmp[5] = {0xE9};
    const int32_t rel = (int32_t) ((uintptr_t) delta - ((uintptr_t) reimpl + sizeof(jmp)));
    memcpy(&jmp[1], &rel, sizeof(rel));
    WriteMemory("virtual_block", reimpl, jmp, sizeof(jmp));
}

namespace {
    // A discrete chunk as extract_raw_asset.py writes it: magic, one or two little-endian sizes,
    // then the payload sections verbatim. The container tells us where an entry's second section
    // starts, which is what the block's table has to encode.
    constexpr uint64_t MAX_CHUNK_BYTES = 64ULL * 1024ULL * 1024ULL;

    uint32_t read_le32(const uint8_t *p) {
        return static_cast<uint32_t>(p[0]) |
               (static_cast<uint32_t>(p[1]) << 8) |
               (static_cast<uint32_t>(p[2]) << 16) |
               (static_cast<uint32_t>(p[3]) << 24);
    }

    bool read_chunk(const std::filesystem::path &path, swrLoader_TYPE type,
                    uint32_t index, VirtualOverride *out) {
        if (out == nullptr)
            return false;
        const char *expected_magic = nullptr;
        bool two_sections = false;
        switch (type) {
            case swrLoader_TYPE_MODEL_BLOCK:
                expected_magic = "RAWM";
                two_sections = true;
                break;
            case swrLoader_TYPE_SPLINE_BLOCK:
                expected_magic = "RAWS";
                break;
            case swrLoader_TYPE_TEXTURE_BLOCK:
                expected_magic = "RAWT";
                two_sections = true;
                break;
            default:
                return false;
        }

        FILE *f = fopen(path.string().c_str(), "rb");
        if (!f)
            return false;
        if (fseek(f, 0, SEEK_END) != 0) {
            fclose(f);
            return false;
        }
        const long file_length = ftell(f);
        if (file_length < 8 || static_cast<uint64_t>(file_length) > MAX_CHUNK_BYTES ||
            fseek(f, 0, SEEK_SET) != 0) {
            fclose(f);
            return false;
        }

        uint8_t header[12] = {};
        const size_t header_size = two_sections ? 12 : 8;
        if (fread(header, 1, header_size, f) != header_size ||
            memcmp(header, expected_magic, 4) != 0) {
            fclose(f);
            return false;
        }
        const uint32_t first = read_le32(header + 4);
        const uint32_t second = two_sections ? read_le32(header + 8) : 0;
        const uint64_t payload_size = static_cast<uint64_t>(first) + second;
        if (payload_size == 0 || payload_size + header_size != static_cast<uint64_t>(file_length) ||
            payload_size > MAX_CHUNK_BYTES - header_size) {
            fclose(f);
            return false;
        }
        if (type == swrLoader_TYPE_MODEL_BLOCK &&
            (first == 0 || first % 4 != 0 || second < 4 || second % 4 != 0)) {
            fclose(f);
            return false;
        }
        if (type == swrLoader_TYPE_SPLINE_BLOCK && (first < 4 || first % 4 != 0)) {
            fclose(f);
            return false;
        }
        if (type == swrLoader_TYPE_TEXTURE_BLOCK &&
            (first == 0 || first % 4 != 0 || (second % 4) != 0)) {
            fclose(f);
            return false;
        }

        std::vector<uint8_t> payload;
        try {
            payload.resize(static_cast<size_t>(payload_size));
        } catch (...) {
            fclose(f);
            return false;
        }
        const bool complete = fread(payload.data(), 1, payload.size(), f) == payload.size();
        const int close_status = fclose(f);
        if (!complete || close_status != 0)
            return false;

        *out = {index, std::move(payload), second != 0 ? first : 0u};
        return true;
    }

    // ./assets/replacement_blocks/<model|spline|texture>/<entry index>.bin
    std::vector<VirtualOverride> load_folder_overrides(swrLoader_TYPE type) {
        std::vector<VirtualOverride> overrides;
        const std::filesystem::path folder =
            std::filesystem::path("./assets/replacement_blocks") / type_name(type);
        std::error_code ec;
        if (!std::filesystem::is_directory(folder, ec) || ec)
            return overrides;

        std::vector<std::filesystem::path> files;
        std::filesystem::directory_iterator it(folder, ec);
        const std::filesystem::directory_iterator end;
        while (!ec && it != end) {
            std::error_code entry_ec;
            if (it->is_regular_file(entry_ec) && !entry_ec &&
                it->path().extension() == ".bin") {
                files.push_back(it->path());
            }
            it.increment(ec);
        }
        std::sort(files.begin(), files.end(),
                  [](const auto &a, const auto &b) {
                      return a.filename().generic_string() < b.filename().generic_string();
                  });

        std::map<uint32_t, std::filesystem::path> indexed_files;
        for (const auto &path: files) {
            const std::string stem = path.stem().generic_string();
            if (stem.empty() ||
                stem.find_first_not_of("0123456789") != std::string::npos)
                continue;

            uint32_t index = 0;
            const auto parsed = std::from_chars(stem.data(), stem.data() + stem.size(), index, 10);
            if (parsed.ec != std::errc{} || parsed.ptr != stem.data() + stem.size()) {
                if (hook_log) {
                    fprintf(hook_log, "[virtual_block] ignoring replacement with invalid index: %s\n",
                            path.generic_string().c_str());
                    fflush(hook_log);
                }
                continue;
            }
            const auto inserted = indexed_files.emplace(index, path);
            if (!inserted.second && hook_log) {
                fprintf(hook_log,
                        "[virtual_block] duplicate replacement index %u; keeping %s and ignoring %s\n",
                        index, inserted.first->second.generic_string().c_str(),
                        path.generic_string().c_str());
                fflush(hook_log);
            }
        }

        for (const auto &indexed: indexed_files) {
            VirtualOverride loaded;
            if (!read_chunk(indexed.second, type, indexed.first, &loaded)) {
                if (hook_log) {
                    fprintf(hook_log, "[virtual_block] ignoring %s: invalid discrete chunk\n",
                            indexed.second.generic_string().c_str());
                    fflush(hook_log);
                }
                continue;
            }
            if (hook_log) {
                fprintf(hook_log, "[virtual_block] %s entry %u <- %s (%u bytes, split %u)\n",
                        type_name(type), loaded.index, indexed.second.filename().generic_string().c_str(),
                        (unsigned) loaded.payload.size(), loaded.split);
                fflush(hook_log);
            }
            overrides.push_back(std::move(loaded));
        }
        return overrides;
    }

}

// Install a view per block type for whatever discrete chunks are on disk. Runs before the game
// touches a block, while the path pointers still name the stock archives.
void virtual_block_LoadFolderOverrides() {
    const swrLoader_TYPE types[] = {swrLoader_TYPE_MODEL_BLOCK, swrLoader_TYPE_SPLINE_BLOCK,
                                    swrLoader_TYPE_TEXTURE_BLOCK};
    for (swrLoader_TYPE type: types) {
        std::vector<VirtualOverride> overrides = load_folder_overrides(type);
        if (overrides.empty())
            continue;

        const char **path = block_path(type);
        VirtualBlockView view;
        if (path != nullptr && *path != nullptr &&
            virtual_block_BuildView(type, *path, std::move(overrides), &view))
            virtual_block_Install(type, std::move(view));
    }
}

void virtual_block_RegisterHooks() {
    // All three are reverse-hooked (registered in hook_generated) -> replace only.
    hook_replace(swrLoader_OpenBlock, swrLoader_OpenBlock_delta);
    hook_replace(swrLoader_ReadAt, swrLoader_ReadAt_delta);
    hook_replace(swrLoader_CloseBlock, swrLoader_CloseBlock_delta);

    route_reimpl_to_delta((void *) swrLoader_OpenBlock, (void *) swrLoader_OpenBlock_delta);
    route_reimpl_to_delta((void *) swrLoader_ReadAt, (void *) swrLoader_ReadAt_delta);
    route_reimpl_to_delta((void *) swrLoader_CloseBlock, (void *) swrLoader_CloseBlock_delta);

    virtual_block_LoadFolderOverrides();
}
