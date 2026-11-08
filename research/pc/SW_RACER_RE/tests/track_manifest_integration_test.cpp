#include "../dinput_hook/track_manifest.h"
#include "../dinput_hook/virtual_block.h"

#include <windows.h>
#include <bcrypt.h>

#include <climits>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

extern "C" {
FILE *hook_log = nullptr;
}

namespace {
namespace fs = std::filesystem;

int failures = 0;
int fail_build_type = -1;
std::vector<int> build_attempts;
std::vector<int> installed_types;

const char *model_source_path = "stock-model.bin";
const char *spline_source_path = "stock-spline.bin";
const char *texture_source_path = "stock-texture.bin";

void check(bool condition, const char *name) {
    if (condition) {
        std::cout << "PASS: " << name << '\n';
    } else {
        std::cerr << "FAIL: " << name << '\n';
        ++failures;
    }
}

void write_text(const fs::path &path, const std::string &text) {
    fs::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file.write(text.data(), static_cast<std::streamsize>(text.size()));
    if (!file)
        throw std::runtime_error("failed to write " + path.string());
}

void write_bytes(const fs::path &path, const std::vector<uint8_t> &bytes) {
    fs::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    if (!bytes.empty())
        file.write(reinterpret_cast<const char *>(bytes.data()),
                   static_cast<std::streamsize>(bytes.size()));
    if (!file)
        throw std::runtime_error("failed to write " + path.string());
}

bool sha256_hex(const std::vector<uint8_t> &data, std::string *out) {
    if (out == nullptr || data.size() > static_cast<size_t>(ULONG_MAX))
        return false;

    BCRYPT_ALG_HANDLE algorithm = nullptr;
    if (!BCRYPT_SUCCESS(
            BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0)))
        return false;

    uint8_t digest[32] = {};
    BCRYPT_HASH_HANDLE hash = nullptr;
    bool ok = BCRYPT_SUCCESS(BCryptCreateHash(algorithm, &hash, nullptr, 0, nullptr, 0, 0));
    if (ok) {
        ok = BCRYPT_SUCCESS(BCryptHashData(
                 hash, const_cast<PUCHAR>(data.data()), static_cast<ULONG>(data.size()), 0)) &&
             BCRYPT_SUCCESS(BCryptFinishHash(hash, digest, sizeof(digest), 0));
        BCryptDestroyHash(hash);
    }
    BCryptCloseAlgorithmProvider(algorithm, 0);
    if (!ok)
        return false;

    static const char HEX[] = "0123456789abcdef";
    out->clear();
    for (uint8_t byte : digest) {
        out->push_back(HEX[byte >> 4]);
        out->push_back(HEX[byte & 0x0f]);
    }
    return true;
}

void append_le32(std::vector<uint8_t> *bytes, uint32_t value) {
    bytes->push_back(static_cast<uint8_t>(value));
    bytes->push_back(static_cast<uint8_t>(value >> 8));
    bytes->push_back(static_cast<uint8_t>(value >> 16));
    bytes->push_back(static_cast<uint8_t>(value >> 24));
}

std::vector<uint8_t> raw_model_chunk() {
    std::vector<uint8_t> bytes{'R', 'A', 'W', 'M'};
    append_le32(&bytes, 4);
    append_le32(&bytes, 4);
    bytes.insert(bytes.end(), 4, 0); // mask
    bytes.insert(bytes.end(), {'M', 'o', 'd', 'l'});
    return bytes;
}

std::vector<uint8_t> raw_texture_chunk() {
    std::vector<uint8_t> bytes{'R', 'A', 'W', 'T'};
    append_le32(&bytes, 4);
    append_le32(&bytes, 0); // no palette
    bytes.insert(bytes.end(), {'T', 'E', 'X', '0'});
    return bytes;
}

std::string asset_json(const std::string &sha, size_t size, const char *index_name,
                       uint32_t index) {
    return std::string("{\"sha256\":\"") + sha + "\",\"size\":" +
           std::to_string(size) + ",\"" + index_name + "\":" +
           std::to_string(index) + "}";
}

std::string manifest_json(const std::string &slug, int schema, const std::string &model_json,
                          const std::string &placement_json =
                              "{\"planet\":0,\"planet_track_number\":0,"
                              "\"favorite_pilot\":0,\"overrides_stock_slot\":0}",
                          const std::string &textures_json = "[]",
                          const std::string &spline_json = "") {
    const std::string spline_field =
        spline_json.empty() ? "" : ",\"spline\":" + spline_json;
    return "{\"schema\":" + std::to_string(schema) + ",\"slug\":\"" + slug +
           "\",\"version\":\"1.0.0\",\"name\":\"Test Track\","
           "\"author\":{\"name\":\"CI\"},\"model\":" + model_json +
           spline_field + ",\"textures\":" + textures_json + ",\"placement\":" +
           placement_json + "}";
}
fs::path write_manifest(const fs::path &root, const std::string &name,
                        const std::string &json) {
    const fs::path path = root / "manifests" / name / "track.json";
    write_text(path, json);
    return path;
}

std::string put_blob(const fs::path &root, const std::vector<uint8_t> &bytes) {
    std::string hash;
    if (!sha256_hex(bytes, &hash))
        throw std::runtime_error("could not compute SHA-256 for test fixture");
    write_bytes(root / "assets" / "content" / hash.substr(0, 2) / hash, bytes);
    return hash;
}

void reset_view_state() {
    fail_build_type = -1;
    build_attempts.clear();
    installed_types.clear();
}
} // namespace

bool virtual_block_BuildView(swrLoader_TYPE type, const char *source_path,
                             std::vector<VirtualOverride> overrides, VirtualBlockView *out) {
    (void) overrides;
    build_attempts.push_back(static_cast<int>(type));
    if (out == nullptr || source_path == nullptr ||
        static_cast<int>(type) == fail_build_type)
        return false;
    out->source_path = source_path;
    return true;
}

void virtual_block_Install(swrLoader_TYPE type, VirtualBlockView view) {
    (void) view;
    installed_types.push_back(static_cast<int>(type));
}

void virtual_block_Remove(swrLoader_TYPE type) {
    (void) type;
}

bool virtual_block_IsInstalled(swrLoader_TYPE type) {
    (void) type;
    return false;
}

void virtual_block_LoadFolderOverrides() {}

const char **virtual_block_SourcePath(swrLoader_TYPE type) {
    switch (type) {
        case swrLoader_TYPE_MODEL_BLOCK:
            return &model_source_path;
        case swrLoader_TYPE_SPLINE_BLOCK:
            return &spline_source_path;
        case swrLoader_TYPE_TEXTURE_BLOCK:
            return &texture_source_path;
        default:
            return nullptr;
    }
}

void virtual_block_RegisterHooks() {}

void swrLoader_OpenBlock_delta(swrLoader_TYPE type) {
    (void) type;
}

size_t swrLoader_ReadAt_delta(swrLoader_TYPE type, long offset, void *dst, size_t size) {
    (void) type;
    (void) offset;
    (void) dst;
    (void) size;
    return 0;
}

void swrLoader_CloseBlock_delta(swrLoader_TYPE type) {
    (void) type;
}

int main() {
    namespace fs = std::filesystem;
    const fs::path original_directory = fs::current_path();
    const fs::path root = fs::temp_directory_path() / "swracer-track-manifest-integration-tests";
    std::error_code ec;
    fs::remove_all(root, ec);
    fs::create_directories(root);
    fs::current_path(root);
    hook_log = std::tmpfile();

    const std::string abc_hash =
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    const std::string minimal_model = asset_json(abc_hash, 3, "block_id", 0);
    TrackManifest parsed{};

    check(track_manifest_Read(
              write_manifest(root, "valid", manifest_json("valid-track", 1, minimal_model)),
              &parsed),
          "C++ manifest parser accepts a valid manifest");
    check(parsed.slug == "valid-track" && parsed.model.sha256 == abc_hash &&
              parsed.model.size == 3 && parsed.placement.overrides_stock_slot == 0,
          "C++ manifest parser populates model and placement fields");

    const std::string no_stock_spline_slot =
        "{\"planet\":0,\"planet_track_number\":0,"
        "\"favorite_pilot\":0,\"overrides_stock_slot\":-1}";
    check(!track_manifest_Read(
              write_manifest(root, "missing-spline-and-stock-slot",
                             manifest_json("missing-spline-and-stock-slot", 1, minimal_model,
                                           no_stock_spline_slot)),
              &parsed),
          "C++ manifest parser rejects a track with neither custom nor stock spline");

    check(track_manifest_Read(
              write_manifest(root, "own-spline-no-stock-slot",
                             manifest_json("own-spline-no-stock-slot", 1, minimal_model,
                                           no_stock_spline_slot, "[]",
                                           asset_json(abc_hash, 3, "block_id", 1))),
              &parsed) && parsed.has_spline &&
                  parsed.placement.overrides_stock_slot == -1,
          "C++ manifest parser accepts a custom spline without a stock slot");

    check(!track_manifest_Read(
              write_manifest(root, "bad-schema", manifest_json("bad-schema", 2, minimal_model)),
              &parsed),
          "C++ manifest parser rejects unsupported schema");
    check(!track_manifest_Read(
              write_manifest(root, "unsafe-slug", manifest_json("../escape", 1, minimal_model)),
              &parsed),
          "C++ manifest parser rejects path-like slugs");
    check(!track_manifest_Read(
              write_manifest(root, "bad-hash",
                             manifest_json("bad-hash", 1,
                                           asset_json(std::string(64, 'g'), 3, "block_id", 0))),
              &parsed),
          "C++ manifest parser rejects malformed SHA-256");
    check(!track_manifest_Read(
              write_manifest(root, "missing-model", manifest_json("missing-model", 1, "null")),
              &parsed),
          "C++ manifest parser rejects missing or unusable model asset");
    check(!track_manifest_Read(
              write_manifest(root, "bad-placement",
                             manifest_json("bad-placement", 1, minimal_model,
                                           "{\"planet\":8,\"planet_track_number\":0,"
                                           "\"favorite_pilot\":0,\"overrides_stock_slot\":-1}")),
              &parsed),
          "C++ manifest parser rejects out-of-range placement");
    check(!track_manifest_Read(
              write_manifest(root, "duplicate-textures",
                             manifest_json("duplicate-textures", 1, minimal_model,
                                           "{\"planet\":0,\"planet_track_number\":0,"
                                           "\"favorite_pilot\":0,\"overrides_stock_slot\":-1}",
                                           "[" + asset_json(abc_hash, 3, "block_index", 7) +
                                               "," + asset_json(abc_hash, 3, "block_index", 7) + "]")),
              &parsed),
          "C++ manifest parser rejects duplicate texture indices");

    write_text(root / "assets" / "tracks" / "good" / "track.json",
               manifest_json("good", 1, minimal_model));
    write_text(root / "assets" / "tracks" / "bad" / "track.json",
               manifest_json("bad", 99, minimal_model));
    const auto scanned = track_manifest_ScanAll();
    check(scanned.size() == 1 && scanned.front().slug == "good",
          "manifest scan skips invalid entries and retains valid entries");

    const fs::path abc_blob = root / "assets" / "content" / abc_hash.substr(0, 2) / abc_hash;
    write_bytes(abc_blob, std::vector<uint8_t>{'x', 'y', 'z'});
    TrackAsset abc_asset{abc_hash, 0, 3};
    std::vector<uint8_t> loaded;
    check(!track_manifest_ReadAsset(abc_asset, &loaded),
          "content-store reader rejects a blob with the wrong hash");

    abc_asset.size = 4;
    check(!track_manifest_ReadAsset(abc_asset, &loaded),
          "content-store reader rejects a blob with the wrong declared size");
    abc_asset.size = 3;
    write_bytes(abc_blob, std::vector<uint8_t>{'a', 'b', 'c'});
    check(track_manifest_ReadAsset(abc_asset, &loaded) &&
              loaded == std::vector<uint8_t>({'a', 'b', 'c'}),
          "content-store reader accepts a blob with matching size and SHA-256");
    TrackAsset missing_asset{std::string(64, '0'), 0, 3};
    check(!track_manifest_ReadAsset(missing_asset, &loaded),
          "content-store reader rejects a missing blob");

    const auto model_chunk = raw_model_chunk();
    const auto texture_chunk = raw_texture_chunk();
    const std::string model_hash = put_blob(root, model_chunk);
    const std::string texture_hash = put_blob(root, texture_chunk);

    TrackManifest install_manifest{};
    install_manifest.schema = 1;
    install_manifest.slug = "install-test";
    install_manifest.name = "Install Test";
    install_manifest.model = {model_hash, 2, static_cast<uint32_t>(model_chunk.size())};
    install_manifest.has_spline = false;
    install_manifest.textures.push_back(
        {texture_hash, 7, static_cast<uint32_t>(texture_chunk.size())});
    install_manifest.placement = {0, 0, 0, -1};

    reset_view_state();
    fail_build_type = static_cast<int>(swrLoader_TYPE_TEXTURE_BLOCK);
    check(!track_manifest_InstallViews(install_manifest),
          "view installation fails if the texture view cannot be built");
    check(build_attempts.size() == 2 && installed_types.empty(),
          "failed view build installs no partial model view");

    reset_view_state();
    check(track_manifest_InstallViews(install_manifest),
          "view installation succeeds after all views build");
    check(installed_types.size() == 2 &&
              installed_types[0] == static_cast<int>(swrLoader_TYPE_MODEL_BLOCK) &&
              installed_types[1] == static_cast<int>(swrLoader_TYPE_TEXTURE_BLOCK),
          "successful view installation commits model and texture views together");

    if (hook_log != nullptr) {
        std::fclose(hook_log);
        hook_log = nullptr;
    }
    fs::current_path(original_directory);
    fs::remove_all(root, ec);
    return failures == 0 ? 0 : 1;
}
