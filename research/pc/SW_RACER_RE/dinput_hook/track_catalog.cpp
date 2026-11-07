#include "track_catalog.h"

#include <algorithm>
#include <atomic>
#include <cctype>
#include <condition_variable>
#include <cstdio>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <map>
#include <mutex>
#include <set>
#include <string_view>
#include <thread>

#include <windows.h>
#include <winhttp.h>
#include <bcrypt.h>

#include <simdjson.h>

#include "catalog_http_policy.h"
#include "config.h"
#include "track_manifest.h"

extern "C" FILE *hook_log;

namespace fs = std::filesystem;

namespace {
    constexpr uint64_t MAX_RESPONSE_BYTES = 64ull * 1024 * 1024;
    constexpr uint64_t MAX_MANIFEST_BYTES = 8ull * 1024 * 1024;
    constexpr int TIMEOUT_MS = 15000;

    std::mutex state_mutex;
    CatalogStatus status = {CatalogState::Idle, "", "", 0, 0, 0};
    std::vector<CatalogTrack> tracks;
    std::atomic<bool> pending_rescan{false};

    std::mutex queue_mutex;
    std::condition_variable queue_signal;
    std::deque<std::string> install_queue;// slugs; "" means "refresh the catalog"
    std::thread worker;
    std::atomic<bool> stopping{false};

    bool valid_slug(const std::string &slug) {
        if (slug.empty() || slug.size() > 128 || slug == "." || slug == "..")
            return false;
        for (unsigned char ch: slug) {
            const bool ascii_alnum = (ch >= 'a' && ch <= 'z') ||
                                     (ch >= 'A' && ch <= 'Z') ||
                                     (ch >= '0' && ch <= '9');
            if (!ascii_alnum && ch != '.' && ch != '_' && ch != '-')
                return false;
        }
        return true;
    }

    bool valid_sha256(const std::string &sha) {
        if (sha.size() != 64)
            return false;
        for (unsigned char ch: sha) {
            if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f')))
                return false;
        }
        return true;
    }

    std::wstring widen(const std::string &text) {
        if (text.empty())
            return std::wstring();
        const int size = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS,
                                             text.c_str(), (int) text.size(), nullptr, 0);
        if (size <= 0)
            return std::wstring();
        std::wstring wide(size, L'\0');
        if (MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text.c_str(),
                                (int) text.size(), wide.data(), size) != size)
            return std::wstring();
        return wide;
    }

    void set_status(CatalogState state, const std::string &message,
                    const std::string &slug = std::string(), uint64_t done = 0,
                    uint64_t total = 0) {
        std::lock_guard<std::mutex> lock(state_mutex);
        status.state = state;
        status.message = message;
        status.active_slug = slug;
        status.bytes_done = done;
        status.bytes_total = total;
    }

    bool sha256_hex(const std::vector<uint8_t> &data, std::string *out) {
        if (out == nullptr || data.size() > MAX_RESPONSE_BYTES ||
            data.size() > std::numeric_limits<ULONG>::max())
            return false;

        BCRYPT_ALG_HANDLE algorithm = nullptr;
        if (!BCRYPT_SUCCESS(BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM,
                                                        nullptr, 0)))
            return false;

        uint8_t digest[32] = {};
        BCRYPT_HASH_HANDLE hash = nullptr;
        bool ok = BCRYPT_SUCCESS(BCryptCreateHash(algorithm, &hash, nullptr, 0,
                                                  nullptr, 0, 0));
        if (ok) {
            ok = BCRYPT_SUCCESS(BCryptHashData(hash, const_cast<PUCHAR>(data.data()),
                                               static_cast<ULONG>(data.size()), 0)) &&
                 BCRYPT_SUCCESS(BCryptFinishHash(hash, digest, sizeof(digest), 0));
            BCryptDestroyHash(hash);
        }
        BCryptCloseAlgorithmProvider(algorithm, 0);
        if (!ok)
            return false;

        static const char HEX[] = "0123456789abcdef";
        out->clear();
        out->reserve(64);
        for (uint8_t byte: digest) {
            out->push_back(HEX[byte >> 4]);
            out->push_back(HEX[byte & 0xf]);
        }
        return true;
    }

    bool read_file_limited(const fs::path &path, uint64_t max_bytes,
                           std::vector<uint8_t> *out) {
        if (out == nullptr)
            return false;
        std::error_code ec;
        const uint64_t size = fs::file_size(path, ec);
        if (ec || size > max_bytes)
            return false;
        std::ifstream f(path, std::ios::binary);
        if (!f)
            return false;
        try {
            out->resize(static_cast<size_t>(size));
        } catch (...) {
            return false;
        }
        if (size != 0)
            f.read(reinterpret_cast<char *>(out->data()), static_cast<std::streamsize>(size));
        return f.good() || (f.eof() && static_cast<uint64_t>(f.gcount()) == size);
    }

    bool write_file(const fs::path &path, const void *data, size_t size) {
        if (size > MAX_RESPONSE_BYTES)
            return false;
        std::error_code ec;
        fs::create_directories(path.parent_path(), ec);
        if (ec)
            return false;
        FILE *f = fopen(path.generic_string().c_str(), "wb");
        if (!f)
            return false;
        bool ok = size == 0 || fwrite(data, 1, size, f) == size;
        if (fflush(f) != 0)
            ok = false;
        if (fclose(f) != 0)
            ok = false;
        if (!ok)
            fs::remove(path, ec);
        return ok;
    }

    fs::path blob_path(const std::string &sha256) {
        // Only canonical SHA-256 names reach this path helper.
        return fs::path("./assets/content") / sha256.substr(0, 2) / sha256;
    }

    // One GET, whole response in memory. Fails loudly rather than half-succeeding: a partial body
    // would only be caught later by the hash check, and the message would be less useful.
    // Network is strictly worker-thread work. Reject malformed schemes and cap every response.
    bool http_get(const std::string &url, std::vector<uint8_t> *out, std::string *error) {
        if (out == nullptr || error == nullptr ||
            (url.rfind("https://", 0) != 0 && url.rfind("http://", 0) != 0) ||
            url.find_first_of("\r\n") != std::string::npos) {
            if (error)
                *error = "only valid HTTP(S) URLs are supported";
            return false;
        }

        const std::wstring wide_url = widen(url);
        if (wide_url.empty()) {
            *error = "URL is not valid UTF-8: " + url;
            return false;
        }

        URL_COMPONENTS parts = {};
        parts.dwStructSize = sizeof(parts);
        wchar_t host[256] = {};
        wchar_t path[2048] = {};
        parts.lpszHostName = host;
        parts.dwHostNameLength = static_cast<DWORD>(std::size(host));
        parts.lpszUrlPath = path;
        parts.dwUrlPathLength = static_cast<DWORD>(std::size(path));
        if (!WinHttpCrackUrl(wide_url.c_str(), 0, 0, &parts) ||
            parts.dwHostNameLength == 0 || parts.dwHostNameLength >= std::size(host) ||
            parts.dwUrlPathLength >= std::size(path)) {
            *error = "not a usable URL: " + url;
            return false;
        }

        // The catalog controls both asset names and their hashes. Plain HTTP to a remote host
        // would let a network attacker replace the catalog and then supply matching malicious
        // hashes, so HTTP is reserved for the loopback development server.
        if (parts.nScheme == INTERNET_SCHEME_HTTP &&
            !catalog_http_policy::is_loopback_host(
                std::wstring_view(host, parts.dwHostNameLength))) {
            *error = "plain HTTP is only permitted for loopback catalog hosts";
            return false;
        }

        HINTERNET session = WinHttpOpen(L"SW_RACER_RE", WINHTTP_ACCESS_TYPE_AUTOMATIC_PROXY,
                                        WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
        if (!session) {
            *error = "could not open an HTTP session";
            return false;
        }
        WinHttpSetTimeouts(session, TIMEOUT_MS, TIMEOUT_MS, TIMEOUT_MS, TIMEOUT_MS);

        bool ok = false;
        HINTERNET connection = WinHttpConnect(session, host, parts.nPort, 0);
        if (connection) {
            const DWORD flags = parts.nScheme == INTERNET_SCHEME_HTTPS ? WINHTTP_FLAG_SECURE : 0;
            HINTERNET request = WinHttpOpenRequest(connection, L"GET", path, nullptr,
                                                   WINHTTP_NO_REFERER,
                                                   WINHTTP_DEFAULT_ACCEPT_TYPES, flags);
            if (request) {
                // Automatic redirects change the destination host/scheme, while the URL policy
                // above validates only the configured endpoint. Catalog and blob URLs are stable
                // content-addressed resources and do not need redirects, so reject them explicitly
                // rather than rely on WinHTTP's defaults or contact a second origin.
                DWORD disabled_features = WINHTTP_DISABLE_REDIRECTS;
                if (!WinHttpSetOption(request, WINHTTP_OPTION_DISABLE_FEATURE,
                                      &disabled_features, sizeof(disabled_features))) {
                    *error = "could not enforce redirect policy for " + url;
                } else if (WinHttpSendRequest(request, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                                              WINHTTP_NO_REQUEST_DATA, 0, 0, 0) &&
                           WinHttpReceiveResponse(request, nullptr)) {
                    DWORD code = 0;
                    DWORD code_size = sizeof(code);
                    if (!WinHttpQueryHeaders(request,
                                             WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
                                             WINHTTP_HEADER_NAME_BY_INDEX, &code, &code_size,
                                             WINHTTP_NO_HEADER_INDEX)) {
                        *error = "could not read HTTP status for " + url;
                    } else if (code != 200) {
                        *error = "HTTP " + std::to_string(code) + " for " + url;
                    } else {
                        ok = true;
                        for (;;) {
                            DWORD available = 0;
                            if (!WinHttpQueryDataAvailable(request, &available)) {
                                *error = "could not read response length for " + url;
                                ok = false;
                                break;
                            }
                            if (available == 0)
                                break;
                            if (out->size() > MAX_RESPONSE_BYTES ||
                                static_cast<uint64_t>(available) > MAX_RESPONSE_BYTES - out->size()) {
                                *error = "response larger than the " +
                                    std::to_string(MAX_RESPONSE_BYTES) + " byte limit";
                                ok = false;
                                break;
                            }

                            const size_t offset = out->size();
                            try {
                                out->resize(offset + available);
                            } catch (...) {
                                *error = "not enough memory to read " + url;
                                ok = false;
                                break;
                            }
                            DWORD read = 0;
                            if (!WinHttpReadData(request, out->data() + offset, available, &read) ||
                                read == 0) {
                                *error = "read failed partway through " + url;
                                out->resize(offset);
                                ok = false;
                                break;
                            }
                            out->resize(offset + read);
                        }
                    }
                } else {
                    *error = "request failed (" + std::to_string(GetLastError()) + ") for " + url;
                }
                WinHttpCloseHandle(request);
            } else {
                *error = "could not build a request for " + url;
            }
            WinHttpCloseHandle(connection);
        } else {
            *error = "could not reach the host of " + url;
        }
        WinHttpCloseHandle(session);
        return ok;
    }

    // Unique hashes that a manifest names, and their exact declared chunk lengths.
    struct WantedAsset {
        std::string sha256;
        uint64_t size;
    };

    bool wanted_assets(const std::string &manifest_json, std::vector<WantedAsset> *out,
                       std::string *error, std::string *slug_out = nullptr,
                       std::string *content_hash_out = nullptr) {
        if (out == nullptr || error == nullptr)
            return false;
        out->clear();

        simdjson::dom::parser parser;
        simdjson::dom::element root;
        if (parser.parse(manifest_json).get(root) != simdjson::SUCCESS) {
            *error = "the track manifest is not readable JSON";
            return false;
        }

        int64_t schema = 0;
        if (root["schema"].get(schema) != simdjson::SUCCESS || schema != 1) {
            *error = "the track manifest has an unsupported schema";
            return false;
        }
        std::string_view slug_view;
        if (root["slug"].get(slug_view) != simdjson::SUCCESS) {
            *error = "the track manifest has no slug";
            return false;
        }
        const std::string manifest_slug(slug_view);
        if (!valid_slug(manifest_slug)) {
            *error = "the track manifest has an invalid slug";
            return false;
        }
        if (slug_out)
            *slug_out = manifest_slug;

        std::string_view content_hash_view;
        const simdjson::error_code content_hash_error = root["content_hash"].get(content_hash_view);
        std::string manifest_content_hash;
        if (content_hash_error == simdjson::SUCCESS) {
            manifest_content_hash = std::string(content_hash_view);
            if (!manifest_content_hash.empty() && !valid_sha256(manifest_content_hash)) {
                *error = "the manifest content_hash is not a lowercase SHA-256 digest";
                return false;
            }
        } else if (content_hash_error != simdjson::NO_SUCH_FIELD) {
            *error = "the manifest content_hash field is malformed";
            return false;
        }
        if (content_hash_out)
            *content_hash_out = manifest_content_hash;

        std::map<std::string, uint64_t> unique;
        const auto add = [&](simdjson::dom::element asset, const char *expected_format,
                             const char *index_key) -> bool {
            std::string_view format, sha_view;
            int64_t size = 0, index = -1;
            if (asset["format"].get(format) != simdjson::SUCCESS || format != expected_format ||
                asset["sha256"].get(sha_view) != simdjson::SUCCESS ||
                asset["size"].get(size) != simdjson::SUCCESS ||
                asset[index_key].get(index) != simdjson::SUCCESS ||
                index < 0 || static_cast<uint64_t>(index) >= 1'000'000ULL ||
                size <= 0 || static_cast<uint64_t>(size) > MAX_RESPONSE_BYTES) {
                *error = std::string("a manifest asset has an invalid format, index or size; expected ") +
                         expected_format;
                return false;
            }
            const std::string sha(sha_view);
            if (!valid_sha256(sha)) {
                *error = "a manifest asset hash must be a lowercase SHA-256 digest";
                return false;
            }
            const auto inserted = unique.emplace(sha, static_cast<uint64_t>(size));
            if (!inserted.second && inserted.first->second != static_cast<uint64_t>(size)) {
                *error = "the same hash is declared with different sizes";
                return false;
            }
            return true;
        };

        simdjson::dom::element model;
        if (root["model"].get(model) != simdjson::SUCCESS || !add(model, "RAWM", "block_id")) {
            if (error->empty())
                *error = "the track manifest has no usable model asset";
            return false;
        }

        simdjson::dom::element spline;
        const simdjson::error_code spline_error = root["spline"].get(spline);
        if (spline_error == simdjson::SUCCESS) {
            if (!add(spline, "RAWS", "block_id"))
                return false;
        } else if (spline_error != simdjson::NO_SUCH_FIELD) {
            *error = "the track manifest has a malformed spline field";
            return false;
        }

        simdjson::dom::element preview;
        const simdjson::error_code preview_error = root["preview_model"].get(preview);
        if (preview_error == simdjson::SUCCESS) {
            if (!add(preview, "RAWM", "block_id"))
                return false;
        } else if (preview_error != simdjson::NO_SUCH_FIELD) {
            *error = "the track manifest has a malformed preview_model field";
            return false;
        }

        simdjson::dom::array textures;
        const simdjson::error_code textures_error = root["textures"].get(textures);
        if (textures_error == simdjson::SUCCESS) {
            std::set<uint32_t> texture_indices;
            for (simdjson::dom::element texture: textures) {
                int64_t texture_index = -1;
                if (texture["block_index"].get(texture_index) != simdjson::SUCCESS ||
                    texture_index < 0 || static_cast<uint64_t>(texture_index) >= 1'000'000ULL ||
                    !texture_indices.insert(static_cast<uint32_t>(texture_index)).second) {
                    *error = "the manifest has an invalid or duplicate texture block index";
                    return false;
                }
                if (!add(texture, "RAWT", "block_index"))
                    return false;
            }
        } else if (textures_error != simdjson::NO_SUCH_FIELD) {
            *error = "the track manifest has a malformed textures field";
            return false;
        }

        // Reject malformed placements before downloading any of the referenced blobs.
        simdjson::dom::element placement;
        const simdjson::error_code placement_error = root["placement"].get(placement);
        if (placement_error == simdjson::SUCCESS) {
            const auto get_placement_int = [&](const char *key, int64_t fallback, int64_t *value) {
                const simdjson::error_code field_error = placement[key].get(*value);
                if (field_error == simdjson::NO_SUCH_FIELD) {
                    *value = fallback;
                    return true;
                }
                return field_error == simdjson::SUCCESS;
            };
            int64_t planet = 0, planet_track = 0, favorite = 0, stock_slot = -1;
            if (!get_placement_int("planet", 0, &planet) ||
                !get_placement_int("planet_track_number", 0, &planet_track) ||
                !get_placement_int("favorite_pilot", 0, &favorite) ||
                !get_placement_int("overrides_stock_slot", -1, &stock_slot) ||
                planet < 0 || planet >= 8 || planet_track < 0 || planet_track > 255 ||
                favorite < 0 || favorite > 255 || stock_slot < -1 || stock_slot >= 25) {
                *error = "the manifest has a malformed or out-of-range placement";
                return false;
            }
        } else if (placement_error != simdjson::NO_SUCH_FIELD) {
            *error = "the manifest has a malformed placement field";
            return false;
        }

        uint64_t total = 0;
        for (const auto &entry: unique) {
            if (entry.second > std::numeric_limits<uint64_t>::max() - total) {
                *error = "the manifest's total download size overflows";
                return false;
            }
            total += entry.second;
            out->push_back({entry.first, entry.second});
        }
        if (total > MAX_RESPONSE_BYTES * 16ULL) {
            *error = "the track's combined assets exceed the safe download budget";
            out->clear();
            return false;
        }
        return true;
    }

    bool blob_matches_asset(const fs::path &path, const WantedAsset &asset) {
        if (!valid_sha256(asset.sha256) || asset.size == 0 || asset.size > MAX_RESPONSE_BYTES)
            return false;
        std::vector<uint8_t> bytes;
        if (!read_file_limited(path, asset.size, &bytes) || bytes.size() != asset.size)
            return false;
        std::string digest;
        return sha256_hex(bytes, &digest) && digest == asset.sha256;
    }

    bool installed_matches(const CatalogTrack &track) {
        if (!valid_slug(track.slug) || !valid_sha256(track.content_hash))
            return false;
        const fs::path path = fs::path("./assets/tracks") / track.slug / "track.json";
        std::vector<uint8_t> bytes;
        if (!read_file_limited(path, MAX_MANIFEST_BYTES, &bytes))
            return false;

        const std::string manifest_json(reinterpret_cast<const char *>(bytes.data()), bytes.size());
        std::vector<WantedAsset> assets;
        std::string local_slug, local_content_hash, error;
        if (!wanted_assets(manifest_json, &assets, &error, &local_slug, &local_content_hash) ||
            local_slug != track.slug || local_content_hash != track.content_hash)
            return false;

        // A matching track.json is not enough: verify every local blob before showing "installed".
        for (const WantedAsset &asset: assets) {
            if (!blob_matches_asset(blob_path(asset.sha256), asset))
                return false;
        }
        return true;
    }

    bool read_catalog_text(simdjson::dom::element entry, const char *key, std::string *out) {
        std::string_view value;
        if (out == nullptr || entry[key].get(value) != simdjson::SUCCESS)
            return false;
        *out = std::string(value);
        return true;
    }

    void do_refresh() {
        set_status(CatalogState::Fetching, "fetching the catalog");
        std::vector<uint8_t> body;
        std::string error;
        if (!http_get(track_catalog_Url() + "/index.json", &body, &error)) {
            if (hook_log) {
                fprintf(hook_log, "[track_catalog] %s\n", error.c_str());
                fflush(hook_log);
            }
            set_status(CatalogState::Failed, error);
            return;
        }

        simdjson::dom::parser parser;
        simdjson::dom::element root;
        if (parser.parse(body.data(), body.size()).get(root) != simdjson::SUCCESS) {
            set_status(CatalogState::Failed, "the catalog is not readable JSON");
            return;
        }
        int64_t schema = 0;
        if (root["schema"].get(schema) != simdjson::SUCCESS || schema != 1) {
            set_status(CatalogState::Failed, "the catalog has an unsupported schema");
            return;
        }

        simdjson::dom::array entries;
        if (root["tracks"].get(entries) != simdjson::SUCCESS) {
            set_status(CatalogState::Failed, "the catalog has no tracks array");
            return;
        }

        std::vector<CatalogTrack> fetched;
        std::set<std::string> seen_slugs;
        for (simdjson::dom::element entry: entries) {
            CatalogTrack track = {};
            if (!read_catalog_text(entry, "slug", &track.slug) || !valid_slug(track.slug)) {
                if (hook_log) {
                    fprintf(hook_log, "[track_catalog] skipping an entry with an invalid slug\n");
                    fflush(hook_log);
                }
                continue;
            }
            if (!seen_slugs.insert(track.slug).second) {
                if (hook_log) {
                    fprintf(hook_log, "[track_catalog] skipping duplicate slug '%s'\n",
                            track.slug.c_str());
                    fflush(hook_log);
                }
                continue;
            }

            read_catalog_text(entry, "name", &track.name);
            read_catalog_text(entry, "author", &track.author);
            read_catalog_text(entry, "version", &track.version);
            read_catalog_text(entry, "content_hash", &track.content_hash);
            if (track.name.empty())
                track.name = track.slug;
            if (!track.content_hash.empty() && !valid_sha256(track.content_hash)) {
                if (hook_log) {
                    fprintf(hook_log, "[track_catalog] skipping '%s': invalid content_hash\n",
                            track.slug.c_str());
                    fflush(hook_log);
                }
                continue;
            }

            simdjson::dom::element manifest;
            if (entry["manifest"].get(manifest) != simdjson::SUCCESS) {
                if (hook_log) {
                    fprintf(hook_log, "[track_catalog] skipping '%s': no embedded manifest\n",
                            track.slug.c_str());
                    fflush(hook_log);
                }
                continue;
            }
            track.manifest_json = simdjson::to_string(manifest);
            std::vector<WantedAsset> assets;
            std::string manifest_slug, manifest_content_hash, manifest_error;
            if (!wanted_assets(track.manifest_json, &assets, &manifest_error, &manifest_slug,
                               &manifest_content_hash) ||
                manifest_slug != track.slug ||
                (!track.content_hash.empty() && track.content_hash != manifest_content_hash)) {
                if (hook_log) {
                    fprintf(hook_log, "[track_catalog] skipping '%s': manifest mismatch: %s\n",
                            track.slug.c_str(),
                            manifest_error.empty() ? "slug does not match catalog entry" :
                                                     manifest_error.c_str());
                    fflush(hook_log);
                }
                continue;
            }

            // Never trust download_bytes from a remote catalog; derive it from validated hashes.
            uint64_t total = 0;
            bool overflow = false;
            for (const WantedAsset &asset: assets) {
                if (asset.size > std::numeric_limits<uint64_t>::max() - total) {
                    overflow = true;
                    break;
                }
                total += asset.size;
            }
            if (overflow) {
                if (hook_log) {
                    fprintf(hook_log, "[track_catalog] skipping '%s': download size overflow\n",
                            track.slug.c_str());
                    fflush(hook_log);
                }
                continue;
            }
            track.download_bytes = total;
            if (track.content_hash.empty())
                track.content_hash = manifest_content_hash;
            track.installed = installed_matches(track);
            fetched.push_back(std::move(track));
        }

        const size_t fetched_count = fetched.size();
        {
            std::lock_guard<std::mutex> lock(state_mutex);
            tracks = std::move(fetched);
            status.tracks_installed_since_refresh = 0;
        }
        if (hook_log) {
            fprintf(hook_log, "[track_catalog] catalog lists %u valid track(s)\n",
                    static_cast<unsigned>(fetched_count));
            fflush(hook_log);
        }
        set_status(CatalogState::Idle, "");
    }

    void do_install(const std::string &slug) {
        CatalogTrack track = {};
        bool found_track = false;
        {
            std::lock_guard<std::mutex> lock(state_mutex);
            const auto it = std::find_if(tracks.begin(), tracks.end(),
                                         [&](const CatalogTrack &entry) {
                                             return entry.slug == slug;
                                         });
            if (it != tracks.end()) {
                track = *it;
                found_track = true;
            }
        }
        // Do not call set_status while holding state_mutex; that would deadlock on the same mutex.
        if (!found_track) {
            set_status(CatalogState::Failed, "no valid catalog entry for " + slug);
            return;
        }
        if (!valid_slug(slug) || track.slug != slug) {
            set_status(CatalogState::Failed, "invalid track slug");
            return;
        }

        std::vector<WantedAsset> assets;
        std::string manifest_slug, manifest_content_hash, error;
        if (!wanted_assets(track.manifest_json, &assets, &error, &manifest_slug,
                           &manifest_content_hash) ||
            manifest_slug != slug ||
            (!track.content_hash.empty() && track.content_hash != manifest_content_hash)) {
            set_status(CatalogState::Failed, "invalid track manifest: " + error);
            return;
        }

        std::vector<WantedAsset> missing;
        uint64_t total = 0;
        for (const WantedAsset &asset: assets) {
            const fs::path path = blob_path(asset.sha256);
            std::error_code ec;
            if (fs::is_regular_file(path, ec) && !ec && blob_matches_asset(path, asset))
                continue;

            // A corrupt or truncated cache entry must not be trusted merely because it exists.
            fs::remove(path, ec);
            missing.push_back(asset);
            if (asset.size > std::numeric_limits<uint64_t>::max() - total) {
                set_status(CatalogState::Failed, "track download size overflows");
                return;
            }
            total += asset.size;
        }

        if (hook_log) {
            fprintf(hook_log, "[track_catalog] installing %s: %u missing asset(s), %llu bytes\n",
                    slug.c_str(), static_cast<unsigned>(missing.size()),
                    static_cast<unsigned long long>(total));
            fflush(hook_log);
        }

        uint64_t done = 0;
        for (const WantedAsset &asset: missing) {
            if (stopping)
                return;

            set_status(CatalogState::Downloading, "downloading " + track.name, slug, done, total);
            std::vector<uint8_t> body;
            if (!http_get(track_catalog_Url() + "/blobs/" + asset.sha256, &body, &error)) {
                if (hook_log) {
                    fprintf(hook_log, "[track_catalog] %s\n", error.c_str());
                    fflush(hook_log);
                }
                set_status(CatalogState::Failed, error);
                return;
            }
            if (body.size() != asset.size) {
                set_status(CatalogState::Failed,
                           "download size mismatch for " + asset.sha256.substr(0, 12));
                return;
            }

            std::string digest;
            if (!sha256_hex(body, &digest) || digest != asset.sha256) {
                set_status(CatalogState::Failed,
                           "the download of " + asset.sha256.substr(0, 12) + " did not match its hash");
                return;
            }

            // Only verified bytes are written under their final content-addressed filename.
            if (!write_file(blob_path(asset.sha256), body.data(), body.size())) {
                set_status(CatalogState::Failed, "could not store blob " + asset.sha256.substr(0, 12));
                return;
            }
            done += asset.size;
        }

        // Validate the entire manifest with the same parser used by the registry before publishing
        // the final filename. A failed install leaves no track.json visible to the game.
        const fs::path manifest_dir = fs::path("./assets/tracks") / slug;
        std::error_code ec;
        fs::create_directories(manifest_dir, ec);
        if (ec) {
            set_status(CatalogState::Failed, "could not create directory for " + slug);
            return;
        }
        const fs::path pending_path = manifest_dir / ".track.json.pending";
        const fs::path final_path = manifest_dir / "track.json";
        if (!write_file(pending_path, track.manifest_json.data(), track.manifest_json.size())) {
            set_status(CatalogState::Failed, "could not write pending manifest for " + slug);
            return;
        }

        TrackManifest parsed_manifest;
        if (!track_manifest_Read(pending_path, &parsed_manifest) || parsed_manifest.slug != slug) {
            fs::remove(pending_path, ec);
            set_status(CatalogState::Failed, "manifest failed validation for " + slug);
            return;
        }
        if (!MoveFileExW(pending_path.c_str(), final_path.c_str(),
                         MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
            fs::remove(pending_path, ec);
            set_status(CatalogState::Failed, "could not publish track manifest for " + slug);
            return;
        }

        {
            std::lock_guard<std::mutex> lock(state_mutex);
            for (CatalogTrack &entry: tracks) {
                if (entry.slug == slug)
                    entry.installed = true;
            }
            status.tracks_installed_since_refresh++;
        }
        pending_rescan = true;
        if (hook_log) {
            fprintf(hook_log, "[track_catalog] installed %s\n", slug.c_str());
            fflush(hook_log);
        }
        set_status(CatalogState::Idle, track.name + " installed");
    }

    void worker_main() {
        while (!stopping) {
            std::string job;
            {
                std::unique_lock<std::mutex> lock(queue_mutex);
                queue_signal.wait(lock, [] { return stopping || !install_queue.empty(); });
                if (stopping)
                    return;
                job = install_queue.front();
                install_queue.pop_front();
            }

            if (job.empty())
                do_refresh();
            else
                do_install(job);
        }
    }

    void enqueue(const std::string &job) {
        if (stopping) {
            set_status(CatalogState::Failed, "catalog worker is shutting down");
            return;
        }
        {
            std::lock_guard<std::mutex> lock(queue_mutex);
            if (!worker.joinable())
                worker = std::thread(worker_main);
            install_queue.push_back(job);
        }
        queue_signal.notify_one();
    }
}

const std::string &track_catalog_Url() {
    // Blobs are content-addressed. HTTPS is preferred, and trailing slashes are normalized once.
    static const std::string url = [] {
        std::string value = config::get_string("tracks", "catalog_url",
                                               "https://bottosjunkyard.com/api/v1/customtracks");
        while (!value.empty() && value.back() == '/')
            value.pop_back();
        if (value.size() > 1024 || value.find_first_of("?#\r\n") != std::string::npos ||
            (value.rfind("https://", 0) != 0 && value.rfind("http://", 0) != 0))
            return std::string("https://bottosjunkyard.com/api/v1/customtracks");
        return value;
    }();
    return url;
}

void track_catalog_Refresh() {
    enqueue("");
}

void track_catalog_Install(const std::string &slug) {
    enqueue(slug);
}

std::vector<CatalogTrack> track_catalog_Tracks() {
    std::lock_guard<std::mutex> lock(state_mutex);
    return tracks;
}

CatalogStatus track_catalog_Status() {
    std::lock_guard<std::mutex> lock(state_mutex);
    return status;
}

bool track_catalog_TakePendingRescan() {
    return pending_rescan.exchange(false);
}

void track_catalog_Shutdown() {
    stopping = true;
    queue_signal.notify_all();
    if (worker.joinable())
        worker.join();
}
