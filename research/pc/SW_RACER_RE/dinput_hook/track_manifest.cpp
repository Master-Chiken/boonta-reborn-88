#include "track_manifest.h"

#include <algorithm>
#include <cctype>
#include <climits>
#include <cstdio>
#include <cstring>
#include <limits>
#include <set>
#include <string_view>

#include <windows.h>
#include <bcrypt.h>

#include <simdjson.h>

#include "virtual_block.h"
#include "track_manifest_policy.h"

extern "C" FILE *hook_log;

namespace fs = std::filesystem;

namespace {
    constexpr int SUPPORTED_SCHEMA = 1;
    const char *TRACKS_DIR = "./assets/tracks";
    const char *CONTENT_DIR = "./assets/content";

    constexpr uint32_t MAX_TRACK_ASSET_BYTES = track_manifest_policy::kMaxTrackAssetBytes;

    std::string get_string(simdjson::dom::element parent, const char *key, const char *fallback) {
        std::string_view value;
        if (parent[key].get(value) != simdjson::SUCCESS)
            return fallback;
        return std::string(value);
    }

    int64_t get_int(simdjson::dom::element parent, const char *key, int64_t fallback) {
        int64_t value = 0;
        if (parent[key].get(value) != simdjson::SUCCESS)
            return fallback;
        return value;
    }

    bool normalize_sha256(std::string_view sha, std::string *normalized) {
        return track_manifest_policy::normalize_sha256(sha, normalized);
    }

    bool is_sha256(const std::string &sha) {
        std::string normalized;
        return normalize_sha256(sha, &normalized) && normalized == sha;
    }

    // An asset is {sha256, size, format, block_id|block_index}. Indices and lengths are range
    // checked before narrowing to uint32_t; hashes are canonicalized before being used as paths.
    bool read_asset(simdjson::dom::element element, const char *index_key, TrackAsset *out) {
        if (out == nullptr)
            return false;
        std::string_view sha;
        if (element["sha256"].get(sha) != simdjson::SUCCESS)
            return false;
        std::string normalized_sha;
        if (!normalize_sha256(sha, &normalized_sha))
            return false;

        int64_t index = -1;
        if (element[index_key].get(index) != simdjson::SUCCESS)
            return false;

        int64_t declared_size = 0;
        if (element["size"].get(declared_size) != simdjson::SUCCESS ||
            !track_manifest_policy::is_valid_asset_index_and_size(index, declared_size))
            return false;

        out->sha256 = std::move(normalized_sha);
        out->block_index = static_cast<uint32_t>(index);
        out->size = static_cast<uint32_t>(declared_size);
        return true;
    }

    fs::path blob_path(const std::string &sha256) {
        // Callers verify a canonical 64-character SHA-256 digest before reaching this helper.
        return fs::path(CONTENT_DIR) / sha256.substr(0, 2) / sha256;
    }

    // The content store names a blob by its hash, so a blob that does not hash to its own name has
    // been corrupted or swapped. Hashing is done through CNG rather than a vendored implementation.
    // The content store names a blob by its hash, so a blob that does not hash to its own name has
    // been corrupted or swapped. Hashing is done through CNG rather than a vendored implementation.
    bool sha256_hex(const std::vector<uint8_t> &data, std::string *out) {
        BCRYPT_ALG_HANDLE algorithm = nullptr;
        if (!BCRYPT_SUCCESS(
                BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0)))
            return false;

        uint8_t digest[32] = {};
        BCRYPT_HASH_HANDLE hash = nullptr;
        bool ok = BCRYPT_SUCCESS(BCryptCreateHash(algorithm, &hash, nullptr, 0, nullptr, 0, 0));
        if (ok) {
            ok = BCRYPT_SUCCESS(BCryptHashData(hash, (PUCHAR) data.data(), (ULONG) data.size(), 0)) &&
                BCRYPT_SUCCESS(BCryptFinishHash(hash, digest, sizeof(digest), 0));
            BCryptDestroyHash(hash);
        }
        BCryptCloseAlgorithmProvider(algorithm, 0);
        if (!ok)
            return false;

        static const char HEX[] = "0123456789abcdef";
        out->clear();
        for (uint8_t byte: digest) {
            out->push_back(HEX[byte >> 4]);
            out->push_back(HEX[byte & 0xf]);
        }
        return true;
    }

    // Blobs are immutable, so one verification per hash per session is enough; a track raced twice
    // does not pay for it twice.
    std::set<std::string> verified_blobs;
}

bool track_manifest_Read(const fs::path &path, TrackManifest *out) {
    if (out == nullptr)
        return false;

    simdjson::dom::parser parser;
    simdjson::dom::element root;
    if (parser.load(path.generic_string()).get(root) != simdjson::SUCCESS) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] %s is not readable JSON\n",
                    path.generic_string().c_str());
            fflush(hook_log);
        }
        return false;
    }

    const int64_t schema = get_int(root, "schema", 0);
    if (schema != SUPPORTED_SCHEMA) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] %s declares unsupported schema %lld\n",
                    path.generic_string().c_str(), static_cast<long long>(schema));
            fflush(hook_log);
        }
        return false;
    }

    TrackManifest manifest = {};
    manifest.schema = SUPPORTED_SCHEMA;
    manifest.slug = get_string(root, "slug", "");
    manifest.version = get_string(root, "version", "");
    manifest.name = get_string(root, "name", manifest.slug.c_str());
    manifest.content_hash = get_string(root, "content_hash", "");
    if (!track_manifest_policy::is_valid_slug(manifest.slug)) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] %s has an invalid or empty slug\n",
                    path.generic_string().c_str());
            fflush(hook_log);
        }
        return false;
    }

    simdjson::dom::element author;
    if (root["author"].get(author) == simdjson::SUCCESS)
        manifest.author = get_string(author, "name", "");

    simdjson::dom::element model;
    if (root["model"].get(model) != simdjson::SUCCESS ||
        !read_asset(model, "block_id", &manifest.model)) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] %s has no usable model asset\n",
                    path.generic_string().c_str());
            fflush(hook_log);
        }
        return false;
    }

    simdjson::dom::element spline;
    const simdjson::error_code spline_error = root["spline"].get(spline);
    if (spline_error == simdjson::SUCCESS) {
        if (!read_asset(spline, "block_id", &manifest.spline)) {
            if (hook_log) {
                fprintf(hook_log, "[track_manifest] %s has an invalid spline asset\n",
                        path.generic_string().c_str());
                fflush(hook_log);
            }
            return false;
        }
        manifest.has_spline = true;
    } else if (spline_error != simdjson::NO_SUCH_FIELD) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] %s has a malformed spline field\n",
                    path.generic_string().c_str());
            fflush(hook_log);
        }
        return false;
    }

    simdjson::dom::array textures;
    const simdjson::error_code textures_error = root["textures"].get(textures);
    if (textures_error == simdjson::SUCCESS) {
        for (simdjson::dom::element texture: textures) {
            TrackAsset asset;
            if (!read_asset(texture, "block_index", &asset)) {
                if (hook_log) {
                    fprintf(hook_log, "[track_manifest] %s contains an invalid texture asset\n",
                            path.generic_string().c_str());
                    fflush(hook_log);
                }
                return false;
            }
            manifest.textures.push_back(std::move(asset));
        }
        std::set<uint32_t> texture_indices;
        for (const TrackAsset &asset: manifest.textures) {
            if (!texture_indices.insert(asset.block_index).second) {
                if (hook_log) {
                    fprintf(hook_log, "[track_manifest] %s repeats texture block index %u\n",
                            path.generic_string().c_str(), asset.block_index);
                    fflush(hook_log);
                }
                return false;
            }
        }
    } else if (textures_error != simdjson::NO_SUCH_FIELD) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] %s has a malformed textures field\n",
                    path.generic_string().c_str());
            fflush(hook_log);
        }
        return false;
    }

    manifest.placement = {0, 0, 0, -1};
    simdjson::dom::element placement;
    const simdjson::error_code placement_error = root["placement"].get(placement);
    if (placement_error == simdjson::SUCCESS) {
        const int64_t planet = get_int(placement, "planet", 0);
        const int64_t planet_track = get_int(placement, "planet_track_number", 0);
        const int64_t favorite = get_int(placement, "favorite_pilot", 0);
        const int64_t stock_slot = get_int(placement, "overrides_stock_slot", -1);
        if (!track_manifest_policy::is_valid_placement(
                planet, planet_track, favorite, stock_slot)) {
            if (hook_log) {
                fprintf(hook_log, "[track_manifest] %s has an out-of-range placement value\n",
                        path.generic_string().c_str());
                fflush(hook_log);
            }
            return false;
        }
        manifest.placement = {static_cast<int>(planet), static_cast<int>(planet_track),
                              static_cast<int>(favorite), static_cast<int>(stock_slot)};
    } else if (placement_error != simdjson::NO_SUCH_FIELD) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] %s has a malformed placement field\n",
                    path.generic_string().c_str());
            fflush(hook_log);
        }
        return false;
    }

    if (!manifest.has_spline && manifest.placement.overrides_stock_slot < 0) {
        if (hook_log) {
            fprintf(hook_log,
                    "[track_manifest] %s has neither a custom spline nor a stock spline slot\n",
                    path.generic_string().c_str());
            fflush(hook_log);
        }
        return false;
    }

    manifest.directory = path.parent_path();
    *out = std::move(manifest);
    return true;
}

std::vector<TrackManifest> track_manifest_ScanAll() {
    std::vector<TrackManifest> manifests;
    std::error_code ec;
    if (!fs::is_directory(TRACKS_DIR, ec) || ec)
        return manifests;

    std::vector<fs::path> directories;
    fs::directory_iterator it(TRACKS_DIR, ec);
    const fs::directory_iterator end;
    while (!ec && it != end) {
        std::error_code entry_ec;
        if (it->is_directory(entry_ec) && !entry_ec)
            directories.push_back(it->path());
        it.increment(ec);
    }
    std::sort(directories.begin(), directories.end());

    for (const fs::path &directory: directories) {
        const fs::path path = directory / "track.json";
        std::error_code file_ec;
        if (!fs::is_regular_file(path, file_ec) || file_ec)
            continue;

        TrackManifest manifest;
        if (!track_manifest_Read(path, &manifest))
            continue;

        if (hook_log) {
            fprintf(hook_log,
                    "[track_manifest] %s '%s' by %s: model %u, %s, %u texture(s)\n",
                    manifest.slug.c_str(), manifest.name.c_str(),
                    manifest.author.empty() ? "?" : manifest.author.c_str(),
                    manifest.model.block_index, manifest.has_spline ? "own spline" : "stock spline",
                    static_cast<unsigned>(manifest.textures.size()));
            fflush(hook_log);
        }
        manifests.push_back(std::move(manifest));
    }
    return manifests;
}


bool track_manifest_ReadAsset(const TrackAsset &asset, std::vector<uint8_t> *out) {
    if (out == nullptr || !is_sha256(asset.sha256) || asset.size == 0 ||
        asset.size > MAX_TRACK_ASSET_BYTES) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] invalid asset hash/size in manifest\n");
            fflush(hook_log);
        }
        return false;
    }

    const fs::path path = blob_path(asset.sha256);
    FILE *f = fopen(path.generic_string().c_str(), "rb");
    if (!f) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] content store has no %s\n", asset.sha256.c_str());
            fflush(hook_log);
        }
        return false;
    }

    if (fseek(f, 0, SEEK_END) != 0) {
        fclose(f);
        return false;
    }
    const long size = ftell(f);
    if (size < 0 || static_cast<uint64_t>(size) > MAX_TRACK_ASSET_BYTES ||
        static_cast<uint64_t>(size) != asset.size || fseek(f, 0, SEEK_SET) != 0) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] %s has invalid length %ld (manifest expects %u)\n",
                    asset.sha256.c_str(), size, asset.size);
            fflush(hook_log);
        }
        fclose(f);
        return false;
    }

    try {
        out->resize(static_cast<size_t>(size));
    } catch (...) {
        fclose(f);
        return false;
    }
    const bool complete = out->empty() || fread(out->data(), 1, out->size(), f) == out->size();
    const int close_result = fclose(f);
    if (!complete || close_result != 0)
        return false;

    if (verified_blobs.count(asset.sha256) != 0)
        return true;

    std::string digest;
    if (!sha256_hex(*out, &digest)) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] could not hash %s to verify it\n",
                    asset.sha256.c_str());
            fflush(hook_log);
        }
        return false;
    }
    if (digest != asset.sha256) {
        if (hook_log) {
            fprintf(hook_log, "[track_manifest] %s hashes to %s -- corrupted or not the asset the manifest names\n",
                    asset.sha256.c_str(), digest.c_str());
            fflush(hook_log);
        }
        return false;
    }

    verified_blobs.insert(asset.sha256);
    return true;
}


namespace {
    uint32_t read_le32(const uint8_t *bytes) {
        return static_cast<uint32_t>(bytes[0]) |
               (static_cast<uint32_t>(bytes[1]) << 8) |
               (static_cast<uint32_t>(bytes[2]) << 16) |
               (static_cast<uint32_t>(bytes[3]) << 24);
    }

    // Match each manifest role to its exact on-disk chunk format; do not accept a spline blob as
    // a model simply because both have a plausible size header.
    bool to_override(const std::vector<uint8_t> &chunk, swrLoader_TYPE type,
                     uint32_t index, VirtualOverride *out) {
        if (out == nullptr)
            return false;

        const char *expected_magic = nullptr;
        size_t header = 0;
        switch (type) {
            case swrLoader_TYPE_MODEL_BLOCK:
                expected_magic = "RAWM";
                header = 12;
                break;
            case swrLoader_TYPE_SPLINE_BLOCK:
                expected_magic = "RAWS";
                header = 8;
                break;
            case swrLoader_TYPE_TEXTURE_BLOCK:
                expected_magic = "RAWT";
                header = 12;
                break;
            default:
                return false;
        }
        if (chunk.size() < header || memcmp(chunk.data(), expected_magic, 4) != 0)
            return false;

        const uint32_t first = read_le32(chunk.data() + 4);
        const uint32_t second = header == 12 ? read_le32(chunk.data() + 8) : 0;
        const uint64_t total = static_cast<uint64_t>(header) + first + second;
        if (total != chunk.size() || total > MAX_TRACK_ASSET_BYTES || first == 0)
            return false;

        if (type == swrLoader_TYPE_MODEL_BLOCK &&
            (first % 4 != 0 || second < 4 || second % 4 != 0))
            return false;
        if (type == swrLoader_TYPE_SPLINE_BLOCK && (first < 4 || first % 4 != 0))
            return false;
        if (type == swrLoader_TYPE_TEXTURE_BLOCK &&
            (first % 4 != 0 || second % 4 != 0))
            return false;

        out->index = index;
        out->payload.assign(chunk.begin() + header, chunk.end());
        out->split = second != 0 ? first : 0;
        return !out->payload.empty();
    }

    bool collect(const TrackAsset &asset, swrLoader_TYPE type,
                 std::vector<VirtualOverride> *overrides) {
        std::vector<uint8_t> chunk;
        VirtualOverride override_entry;
        if (!track_manifest_ReadAsset(asset, &chunk) ||
            !to_override(chunk, type, asset.block_index, &override_entry)) {
            if (hook_log) {
                const char *kind =
                    type == swrLoader_TYPE_MODEL_BLOCK ? "model" :
                    type == swrLoader_TYPE_SPLINE_BLOCK ? "spline" : "texture";
                fprintf(hook_log, "[track_manifest] asset %s is not a usable %s chunk\n",
                        asset.sha256.c_str(), kind);
                fflush(hook_log);
            }
            return false;
        }
        overrides->push_back(std::move(override_entry));
        return true;
    }
}

bool track_manifest_InstallViews(const TrackManifest &manifest) {
    std::vector<VirtualOverride> models;
    std::vector<VirtualOverride> splines;
    std::vector<VirtualOverride> textures;

    if (!collect(manifest.model, swrLoader_TYPE_MODEL_BLOCK, &models))
        return false;
    if (manifest.has_spline &&
        !collect(manifest.spline, swrLoader_TYPE_SPLINE_BLOCK, &splines))
        return false;
    for (const TrackAsset &texture: manifest.textures) {
        if (!collect(texture, swrLoader_TYPE_TEXTURE_BLOCK, &textures))
            return false;
    }

    // Build every view before installing any: a track that is missing an asset should change
    // nothing rather than leave the game reading half of it.
    struct Pending {
        swrLoader_TYPE type;
        VirtualBlockView view;
        bool used;
    };
    Pending pending[3] = {{swrLoader_TYPE_MODEL_BLOCK, {}, false},
                          {swrLoader_TYPE_SPLINE_BLOCK, {}, false},
                          {swrLoader_TYPE_TEXTURE_BLOCK, {}, false}};
    std::vector<VirtualOverride> *by_type[3] = {&models, &splines, &textures};

    for (int i = 0; i < 3; i++) {
        if (by_type[i]->empty())
            continue;

        const char **path = virtual_block_SourcePath(pending[i].type);
        if (path == nullptr || *path == nullptr ||
            !virtual_block_BuildView(pending[i].type, *path, std::move(*by_type[i]),
                                     &pending[i].view))
            return false;
        pending[i].used = true;
    }

    for (Pending &entry: pending) {
        if (entry.used)
            virtual_block_Install(entry.type, std::move(entry.view));
    }

    if (hook_log) {
        fprintf(hook_log, "[track_manifest] installed views for '%s' (%s)\n",
                manifest.slug.c_str(),
                manifest.content_hash.empty() ? "no content hash" : manifest.content_hash.c_str());
        fflush(hook_log);
    }
    return true;
}

void track_manifest_InstallFirstAvailable() {
    for (const TrackManifest &manifest: track_manifest_ScanAll()) {
        if (track_manifest_InstallViews(manifest))
            return;
    }

    virtual_block_LoadFolderOverrides();
}
