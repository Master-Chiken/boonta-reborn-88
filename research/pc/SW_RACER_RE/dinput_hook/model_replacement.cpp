#include "model_replacement.h"

#include "custom_tracks.h" // SWR_MODELBLOCK_PATH_PTR

#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <string>
#include <system_error>
#include <vector>

extern "C" {
#include "game_deltas/tracks_delta.h" // CUSTOM_TRACK_MODELID_BEGIN
}

extern "C" FILE *hook_log;

bool enable_model_replacement = true;
namespace fs = std::filesystem;

namespace {
constexpr uint64_t RAW_HEADER_SIZE = 12;
constexpr uint64_t BLOCK_HEADER_SIZE = 16;
constexpr uint32_t MAX_MASK_SIZE = 153600; // swrLoader_MaskBuffer capacity
constexpr uint32_t MAX_MODEL_SIZE = 64U * 1024U * 1024U;
constexpr uint64_t MAX_RAW_SIZE = RAW_HEADER_SIZE + MAX_MASK_SIZE + MAX_MODEL_SIZE;

std::map<int, fs::path> replacement_models;
bool loaded_replacement_models_at_least_once = false;
const char *saved_modelblock_path = nullptr;
std::string temp_block_path_storage;

void log_line(const char *msg) {
    if (hook_log) {
        std::fprintf(hook_log, "%s\n", msg);
        std::fflush(hook_log);
    }
}

uint32_t read_le32(const uint8_t *p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) |
           (static_cast<uint32_t>(p[3]) << 24);
}

void store_be32(std::vector<uint8_t> &out, size_t offset, uint32_t value) {
    out[offset] = static_cast<uint8_t>(value >> 24);
    out[offset + 1] = static_cast<uint8_t>(value >> 16);
    out[offset + 2] = static_cast<uint8_t>(value >> 8);
    out[offset + 3] = static_cast<uint8_t>(value);
}

bool parse_model_filename(const std::string &name, int &id) {
    constexpr char suffix[] = ".bin";
    constexpr size_t suffix_size = sizeof(suffix) - 1;
    if (name.size() <= suffix_size ||
        name.compare(name.size() - suffix_size, suffix_size, suffix) != 0)
        return false;

    const char *first = name.data();
    const char *last = first + name.size() - suffix_size;
    unsigned int parsed = 0;
    const auto result = std::from_chars(first, last, parsed, 10);
    if (result.ec != std::errc{} || result.ptr != last ||
        parsed > static_cast<unsigned int>(std::numeric_limits<int>::max()))
        return false;
    id = static_cast<int>(parsed);
    return true;
}

bool read_raw_chunk(const fs::path &path, std::vector<uint8_t> &raw) {
    const std::string filename = path.string();
    FILE *file = std::fopen(filename.c_str(), "rb");
    if (!file) {
        if (hook_log) {
            std::fprintf(hook_log, "[model_replacement] cannot open %s\n", filename.c_str());
            std::fflush(hook_log);
        }
        return false;
    }

    if (std::fseek(file, 0, SEEK_END) != 0) {
        std::fclose(file);
        log_line("[model_replacement] fseek failed while reading a replacement.");
        return false;
    }
    const long length = std::ftell(file);
    if (length < static_cast<long>(RAW_HEADER_SIZE) ||
        static_cast<uint64_t>(length) > MAX_RAW_SIZE ||
        std::fseek(file, 0, SEEK_SET) != 0) {
        std::fclose(file);
        log_line("[model_replacement] replacement has an invalid or excessive file size.");
        return false;
    }

    try {
        raw.resize(static_cast<size_t>(length));
    } catch (...) {
        std::fclose(file);
        log_line("[model_replacement] unable to allocate replacement file buffer.");
        return false;
    }

    const size_t bytes_read = std::fread(raw.data(), 1, raw.size(), file);
    const int close_status = std::fclose(file);
    if (bytes_read != raw.size() || close_status != 0) {
        raw.clear();
        log_line("[model_replacement] replacement read was incomplete.");
        return false;
    }

    if (std::memcmp(raw.data(), "RAWM", 4) != 0) {
        raw.clear();
        log_line("[model_replacement] replacement has invalid RAWM magic.");
        return false;
    }

    const uint32_t mask_size = read_le32(raw.data() + 4);
    const uint32_t model_size = read_le32(raw.data() + 8);
    const uint64_t declared_size = RAW_HEADER_SIZE +
        static_cast<uint64_t>(mask_size) + static_cast<uint64_t>(model_size);
    if (mask_size > MAX_MASK_SIZE || model_size < 4 || model_size > MAX_MODEL_SIZE ||
        (mask_size % 4) != 0 || (model_size % 4) != 0 ||
        declared_size != raw.size()) {
        raw.clear();
        log_line("[model_replacement] replacement sizes are invalid.");
        return false;
    }
    return true;
}
} // namespace

void refresh_replacement_models() {
    std::map<int, fs::path> discovered;
    std::error_code ec;
    const fs::path directory("./assets/replacement_models");
    if (!fs::is_directory(directory, ec) || ec) {
        replacement_models.clear();
        loaded_replacement_models_at_least_once = !ec;
        if (hook_log) {
            std::fprintf(hook_log, "[model_replacement] replacement directory unavailable: %s\n",
                         directory.string().c_str());
            std::fflush(hook_log);
        }
        return;
    }

    fs::recursive_directory_iterator it(
        directory, fs::directory_options::skip_permission_denied, ec);
    const fs::recursive_directory_iterator end;
    while (it != end) {
        if (ec) {
            ec.clear();
            it.increment(ec);
            continue;
        }
        std::error_code entry_error;
        if (it->is_regular_file(entry_error) && !entry_error) {
            int id = -1;
            if (parse_model_filename(it->path().filename().string(), id)) {
                const auto [position, inserted] = discovered.emplace(id, it->path());
                if (!inserted && hook_log) {
                    std::fprintf(hook_log,
                                 "[model_replacement] duplicate id %d; keeping %s, ignoring %s\n",
                                 id, position->second.string().c_str(), it->path().string().c_str());
                }
            }
        }
        it.increment(ec);
    }

    replacement_models.swap(discovered);
    loaded_replacement_models_at_least_once = true;
    if (hook_log) {
        std::fprintf(hook_log, "[model_replacement] discovered %zu replacement(s)\n",
                     replacement_models.size());
        std::fflush(hook_log);
    }
}

bool try_prepare_loose_model(MODELID *model_id) {
    // Do not clobber a path swap if a nested model load re-enters this hook.
    if (!model_id || !enable_model_replacement || saved_modelblock_path)
        return false;
    if (!loaded_replacement_models_at_least_once)
        refresh_replacement_models();

    const int requested_id = static_cast<int>(*model_id);
    if (requested_id < 0 || requested_id >= CUSTOM_TRACK_MODELID_BEGIN)
        return false;

    const auto found = replacement_models.find(requested_id);
    if (found == replacement_models.end())
        return false;

    std::vector<uint8_t> raw;
    if (!read_raw_chunk(found->second, raw))
        return false;

    const uint32_t mask_size = read_le32(raw.data() + 4);
    const uint32_t model_size = read_le32(raw.data() + 8);
    const uint64_t end_offset64 = BLOCK_HEADER_SIZE +
        static_cast<uint64_t>(mask_size) + static_cast<uint64_t>(model_size);
    if (end_offset64 > std::numeric_limits<uint32_t>::max() ||
        end_offset64 > std::numeric_limits<size_t>::max()) {
        log_line("[model_replacement] generated model block is too large.");
        return false;
    }

    const uint32_t mask_offset = static_cast<uint32_t>(BLOCK_HEADER_SIZE);
    const uint32_t model_offset = mask_offset + mask_size;
    const uint32_t end_offset = static_cast<uint32_t>(end_offset64);
    std::vector<uint8_t> block;
    try {
        block.resize(static_cast<size_t>(end_offset));
    } catch (...) {
        log_line("[model_replacement] unable to allocate temporary model block.");
        return false;
    }

    // Store the block offsets in big-endian bytes without unaligned integer stores or aliasing.
    store_be32(block, 0, 1);
    store_be32(block, 4, mask_offset);
    store_be32(block, 8, model_offset);
    store_be32(block, 12, end_offset);
    std::memcpy(block.data() + mask_offset, raw.data() + RAW_HEADER_SIZE, mask_size);
    std::memcpy(block.data() + model_offset,
                raw.data() + RAW_HEADER_SIZE + mask_size, model_size);

    temp_block_path_storage = "./assets/replacement_models/.loose_model_cache.bin";
    const std::string cache_path = temp_block_path_storage;
    FILE *out = std::fopen(cache_path.c_str(), "wb");
    if (!out) {
        if (hook_log) {
            std::fprintf(hook_log, "[model_replacement] cannot create %s\n", cache_path.c_str());
            std::fflush(hook_log);
        }
        return false;
    }
    bool write_ok = std::fwrite(block.data(), 1, block.size(), out) == block.size();
    if (std::fflush(out) != 0)
        write_ok = false;
    if (std::fclose(out) != 0)
        write_ok = false;
    if (!write_ok) {
        std::remove(cache_path.c_str());
        log_line("[model_replacement] temporary model block was not written completely.");
        return false;
    }

    if (!SWR_MODELBLOCK_PATH_PTR || !*SWR_MODELBLOCK_PATH_PTR) {
        std::remove(cache_path.c_str());
        log_line("[model_replacement] model block path pointer is unavailable.");
        return false;
    }

    saved_modelblock_path = *SWR_MODELBLOCK_PATH_PTR;
    *SWR_MODELBLOCK_PATH_PTR = temp_block_path_storage.c_str();
    *model_id = static_cast<MODELID>(0);
    if (hook_log) {
        std::fprintf(hook_log, "[model_replacement] replacing model %d from %s\n",
                     requested_id, found->second.string().c_str());
        std::fflush(hook_log);
    }
    return true;
}

void finalize_loose_model() {
    if (saved_modelblock_path) {
        *SWR_MODELBLOCK_PATH_PTR = saved_modelblock_path;
        saved_modelblock_path = nullptr;
    }
}
