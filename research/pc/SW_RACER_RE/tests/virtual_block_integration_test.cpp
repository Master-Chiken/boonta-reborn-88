#include "../dinput_hook/virtual_block.h"
#include "../dinput_hook/hook_helper.h"
#include "../dinput_hook/patch.h"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

extern "C" {
FILE *hook_log = nullptr;

// Link-only stubs for the game loader: this test exercises the virtual block builder and view
// lifecycle, not the injected loader hooks themselves.
void swrLoader_OpenBlock(swrLoader_TYPE) {}
size_t swrLoader_ReadAt(swrLoader_TYPE, long, void *, size_t) { return 0; }
void swrLoader_CloseBlock(swrLoader_TYPE) {}
}

std::map<void *, void *> hook_replacements;
std::map<void *, DebugFunctionInfo> hooks;

bool WriteMemory(PatchOwner, void *, const void *, size_t) {
    return true;
}

namespace {
namespace fs = std::filesystem;

int failures = 0;

void check(bool condition, const char *name) {
    if (condition) {
        std::cout << "PASS: " << name << '\n';
    } else {
        std::cerr << "FAIL: " << name << '\n';
        ++failures;
    }
}

void append_be32(std::vector<uint8_t> *bytes, uint32_t value) {
    bytes->push_back(static_cast<uint8_t>(value >> 24));
    bytes->push_back(static_cast<uint8_t>(value >> 16));
    bytes->push_back(static_cast<uint8_t>(value >> 8));
    bytes->push_back(static_cast<uint8_t>(value));
}

void write_be32(std::vector<uint8_t> *bytes, size_t offset, uint32_t value) {
    (*bytes)[offset] = static_cast<uint8_t>(value >> 24);
    (*bytes)[offset + 1] = static_cast<uint8_t>(value >> 16);
    (*bytes)[offset + 2] = static_cast<uint8_t>(value >> 8);
    (*bytes)[offset + 3] = static_cast<uint8_t>(value);
}

uint32_t read_be32(const std::vector<uint8_t> &bytes, size_t offset) {
    return (static_cast<uint32_t>(bytes[offset]) << 24) |
           (static_cast<uint32_t>(bytes[offset + 1]) << 16) |
           (static_cast<uint32_t>(bytes[offset + 2]) << 8) |
           static_cast<uint32_t>(bytes[offset + 3]);
}

std::vector<uint8_t> make_block(uint32_t count, std::initializer_list<uint32_t> table,
                                const std::vector<uint8_t> &payload) {
    std::vector<uint8_t> bytes;
    append_be32(&bytes, count);
    for (uint32_t value : table)
        append_be32(&bytes, value);
    bytes.insert(bytes.end(), payload.begin(), payload.end());
    return bytes;
}

void write_bytes(const fs::path &path, const std::vector<uint8_t> &bytes) {
    std::ofstream file(path, std::ios::binary);
    if (!bytes.empty())
        file.write(reinterpret_cast<const char *>(bytes.data()),
                   static_cast<std::streamsize>(bytes.size()));
    if (!file)
        throw std::runtime_error("failed to write " + path.string());
}

std::vector<uint8_t> read_range(const fs::path &path, long offset, uint32_t size) {
    std::ifstream file(path, std::ios::binary);
    file.seekg(offset, std::ios::beg);
    std::vector<uint8_t> bytes(size);
    if (size != 0)
        file.read(reinterpret_cast<char *>(bytes.data()), static_cast<std::streamsize>(size));
    if (!file)
        throw std::runtime_error("failed to read " + path.string());
    return bytes;
}

std::vector<uint8_t> sequence(uint8_t first, size_t count) {
    std::vector<uint8_t> bytes(count);
    for (size_t i = 0; i < count; ++i)
        bytes[i] = static_cast<uint8_t>(first + i);
    return bytes;
}

void test_model_fallback_and_override(const fs::path &root) {
    const fs::path path = root / "stock-model.bin";
    const auto stock_payload = sequence(0x10, 16);
    // Count=2; each model entry has mask/model offsets plus a terminal model-end offset.
    // The two 8-byte payloads start at 24 and 32; the model split is four bytes in each.
    write_bytes(path, make_block(2, {24, 28, 32, 36, 40}, stock_payload));

    VirtualOverride replacement{1, sequence(0xA0, 8), 4};
    VirtualBlockView view{};
    check(virtual_block_BuildView(swrLoader_TYPE_MODEL_BLOCK, path.string().c_str(),
                                  {replacement}, &view),
          "model block view builds with one replacement");

    if (view.header.empty() || view.regions.size() != 2 || view.owned.size() != 1) {
        check(false, "model view contains two regions and owns replacement memory");
        return;
    }
    check(read_be32(view.header, 0) == 2 && view.header.size() == 24,
          "model view preserves source entry count and valid header layout");
    check(read_be32(view.header, 4) == 24 && read_be32(view.header, 8) == 28 &&
              read_be32(view.header, 12) == 32 && read_be32(view.header, 16) == 36 &&
              read_be32(view.header, 20) == 40,
          "model view rewrites offsets consistently across fallback and override entries");

    const VirtualRegion &fallback = view.regions[0];
    const VirtualRegion &overridden = view.regions[1];
    check(fallback.virtual_offset == 24 && fallback.size == 8 && fallback.memory == nullptr &&
              fallback.file_offset == 24,
          "undeclared model index maps to its original stock-file byte range");
    check(read_range(path, fallback.file_offset, fallback.size) == sequence(0x10, 8),
          "stock model fallback resolves to the original bytes");
    check(overridden.virtual_offset == 32 && overridden.size == 8 &&
              overridden.memory != nullptr && overridden.file_offset == 0,
          "declared model index maps to replacement memory rather than stock bytes");
    check(std::vector<uint8_t>(overridden.memory, overridden.memory + overridden.size) ==
              sequence(0xA0, 8),
          "model override retains the supplied payload");
    check(view.owned.front() == sequence(0xA0, 8),
          "replacement payload lifetime is owned by the installed view");

    FILE *saved_log = hook_log;
    hook_log = nullptr;
    virtual_block_Install(swrLoader_TYPE_MODEL_BLOCK, std::move(view));
    check(virtual_block_IsInstalled(swrLoader_TYPE_MODEL_BLOCK),
          "model view installs when hook logging is unavailable");
    virtual_block_Remove(swrLoader_TYPE_MODEL_BLOCK);
    hook_log = saved_log;
    check(!virtual_block_IsInstalled(swrLoader_TYPE_MODEL_BLOCK),
          "model view removes cleanly when hook logging is unavailable");
}

void test_spline_fallback_and_override(const fs::path &root) {
    const fs::path path = root / "stock-spline.bin";
    const auto stock_payload = sequence(0x30, 8);
    write_bytes(path, make_block(2, {16, 20, 24}, stock_payload));

    VirtualOverride replacement{0, sequence(0xD0, 4), 0};
    VirtualBlockView view{};
    check(virtual_block_BuildView(swrLoader_TYPE_SPLINE_BLOCK, path.string().c_str(),
                                  {replacement}, &view),
          "spline block view builds with one replacement");

    if (view.header.empty() || view.regions.size() != 2) {
        check(false, "spline view contains both stock fallback and replacement regions");
        return;
    }
    check(read_be32(view.header, 0) == 2 && view.header.size() == 16 &&
              read_be32(view.header, 4) == 16 && read_be32(view.header, 8) == 20 &&
              read_be32(view.header, 12) == 24,
          "spline header keeps both entries and a terminal offset");
    check(view.regions[0].memory != nullptr && view.regions[0].virtual_offset == 16 &&
              std::vector<uint8_t>(view.regions[0].memory,
                                   view.regions[0].memory + view.regions[0].size) ==
                  sequence(0xD0, 4),
          "declared spline index maps to replacement memory");
    check(view.regions[1].memory == nullptr && view.regions[1].file_offset == 20 &&
              view.regions[1].size == 4 &&
              read_range(path, view.regions[1].file_offset, view.regions[1].size) ==
                  sequence(0x34, 4),
          "undeclared spline index falls through to original stock data");

    virtual_block_Install(swrLoader_TYPE_SPLINE_BLOCK, std::move(view));
    check(virtual_block_IsInstalled(swrLoader_TYPE_SPLINE_BLOCK),
          "install marks a spline view active");
    virtual_block_Remove(swrLoader_TYPE_SPLINE_BLOCK);
    check(!virtual_block_IsInstalled(swrLoader_TYPE_SPLINE_BLOCK),
          "removing the spline view restores pass-through state");
}

void test_texture_fallback_and_override(const fs::path &root) {
    const fs::path path = root / "stock-texture.bin";
    const auto stock_payload = sequence(0x50, 16);
    // Texture table has two words per entry and uses EOF as the final entry end.
    // Entry 0 has a four-byte palette; entry 1 has no palette (second offset = 0).
    write_bytes(path, make_block(2, {20, 24, 28, 0}, stock_payload));

    VirtualOverride replacement{1, sequence(0xE0, 8), 0};
    VirtualBlockView view{};
    check(virtual_block_BuildView(swrLoader_TYPE_TEXTURE_BLOCK, path.string().c_str(),
                                  {replacement}, &view),
          "texture block view builds with one replacement");

    if (view.header.empty() || view.regions.size() != 2) {
        check(false, "texture view contains both stock fallback and replacement regions");
        return;
    }
    check(read_be32(view.header, 0) == 2 && view.header.size() == 20 &&
              read_be32(view.header, 4) == 20 && read_be32(view.header, 8) == 24 &&
              read_be32(view.header, 12) == 28 && read_be32(view.header, 16) == 0,
          "texture header preserves stock palette split and no-palette marker");
    check(view.regions[0].memory == nullptr && view.regions[0].file_offset == 20 &&
              view.regions[0].size == 8 &&
              read_range(path, view.regions[0].file_offset, view.regions[0].size) ==
                  sequence(0x50, 8),
          "undeclared texture index resolves to the original stock pixels and palette");
    check(view.regions[1].memory != nullptr && view.regions[1].file_offset == 0 &&
              view.regions[1].size == 8 &&
              std::vector<uint8_t>(view.regions[1].memory,
                                   view.regions[1].memory + view.regions[1].size) ==
                  sequence(0xE0, 8),
          "declared texture index maps to its replacement payload");

    virtual_block_Install(swrLoader_TYPE_TEXTURE_BLOCK, std::move(view));
    check(virtual_block_IsInstalled(swrLoader_TYPE_TEXTURE_BLOCK),
          "install marks a texture view active");
    virtual_block_Remove(swrLoader_TYPE_TEXTURE_BLOCK);
    check(!virtual_block_IsInstalled(swrLoader_TYPE_TEXTURE_BLOCK),
          "removing the texture view restores pass-through state");
}

void test_malformed_source_and_overrides(const fs::path &root) {
    const fs::path malformed = root / "truncated-model.bin";
    std::vector<uint8_t> short_header;
    append_be32(&short_header, 0xFFFFFFFFU);
    write_bytes(malformed, short_header);
    VirtualBlockView view{};
    check(!virtual_block_BuildView(swrLoader_TYPE_MODEL_BLOCK, malformed.string().c_str(), {},
                                   &view),
          "model builder rejects a truncated oversized source offset table");

    const fs::path path = root / "stock-model.bin";
    const auto stock_payload = sequence(0x10, 16);
    write_bytes(path, make_block(2, {24, 28, 32, 36, 40}, stock_payload));
    VirtualBlockView preserved{};
    check(virtual_block_BuildView(swrLoader_TYPE_MODEL_BLOCK, path.string().c_str(), {}, &preserved),
          "model builder creates a baseline view before a rejected rebuild");
    const auto preserved_header = preserved.header;
    const auto preserved_source_path = preserved.source_path;
    const auto preserved_regions = preserved.regions;

    check(!virtual_block_BuildView(
              swrLoader_TYPE_MODEL_BLOCK, path.string().c_str(),
              {{0, sequence(0xA0, 8), 4}, {0, sequence(0xB0, 8), 4}}, &preserved),
          "model builder rejects duplicate replacement indices");
    check(preserved.header == preserved_header &&
              preserved.source_path == preserved_source_path &&
              preserved.regions.size() == preserved_regions.size() &&
              !preserved.regions.empty() &&
              preserved.regions[0].virtual_offset == preserved_regions[0].virtual_offset &&
              preserved.regions[0].size == preserved_regions[0].size &&
              preserved.regions[0].file_offset == preserved_regions[0].file_offset,
          "failed rebuild leaves the previously prepared view unchanged");
    check(!virtual_block_BuildView(swrLoader_TYPE_MODEL_BLOCK, path.string().c_str(),
                                   {{3, sequence(0xC0, 8), 4}}, &view),
          "model builder rejects sparse extension that would create missing entries");
    check(!virtual_block_BuildView(swrLoader_TYPE_MODEL_BLOCK, path.string().c_str(),
                                   {{0, sequence(0xA0, 8), 0}}, &view),
          "model builder rejects a malformed mask/model split");
}
} // namespace

int main() {
    const fs::path original_directory = fs::current_path();
    const fs::path root = fs::temp_directory_path() / "swracer-virtual-block-integration-tests";
    std::error_code ec;
    fs::remove_all(root, ec);
    fs::create_directories(root);
    fs::current_path(root);
    hook_log = std::tmpfile();

    test_model_fallback_and_override(root);
    test_spline_fallback_and_override(root);
    test_texture_fallback_and_override(root);
    test_malformed_source_and_overrides(root);

    if (hook_log != nullptr) {
        std::fclose(hook_log);
        hook_log = nullptr;
    }
    fs::current_path(original_directory);
    fs::remove_all(root, ec);
    return failures == 0 ? 0 : 1;
}
