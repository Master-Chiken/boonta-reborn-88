#pragma once

#include <cstddef>
#include <string_view>

namespace catalog_http_policy {

// Plain HTTP is only safe for local development. Match the host returned by WinHttpCrackUrl;
// ports are intentionally excluded because WinHTTP stores them separately.
inline bool is_loopback_host(std::wstring_view host) noexcept {
    const auto equals_ascii_case_insensitive = [host](std::wstring_view expected) noexcept {
        if (host.size() != expected.size())
            return false;
        for (std::size_t i = 0; i < host.size(); ++i) {
            wchar_t actual = host[i];
            wchar_t wanted = expected[i];
            if (actual >= L'A' && actual <= L'Z')
                actual = static_cast<wchar_t>(actual - L'A' + L'a');
            if (wanted >= L'A' && wanted <= L'Z')
                wanted = static_cast<wchar_t>(wanted - L'A' + L'a');
            if (actual != wanted)
                return false;
        }
        return true;
    };

    return equals_ascii_case_insensitive(L"localhost") ||
           equals_ascii_case_insensitive(L"127.0.0.1") ||
           equals_ascii_case_insensitive(L"::1") ||
           equals_ascii_case_insensitive(L"[::1]");
}

} // namespace catalog_http_policy
