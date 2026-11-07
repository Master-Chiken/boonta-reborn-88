#include "../dinput_hook/catalog_http_policy.h"

#include <cstdio>

int main() {
    int failures = 0;
    const auto check = [&failures](bool condition, const char *name) {
        if (!condition) {
            std::fprintf(stderr, "FAIL: %s\n", name);
            ++failures;
        } else {
            std::printf("PASS: %s\n", name);
        }
    };

    check(catalog_http_policy::is_loopback_host(L"localhost"),
          "localhost is allowed for the local development server");
    check(catalog_http_policy::is_loopback_host(L"LOCALHOST"),
          "loopback host matching is case-insensitive");
    check(catalog_http_policy::is_loopback_host(L"127.0.0.1"),
          "IPv4 loopback is allowed");
    check(catalog_http_policy::is_loopback_host(L"::1"),
          "IPv6 loopback is allowed");
    check(catalog_http_policy::is_loopback_host(L"[::1]"),
          "bracketed IPv6 loopback is allowed defensively");

    check(!catalog_http_policy::is_loopback_host(L""),
          "empty hosts are rejected");
    check(!catalog_http_policy::is_loopback_host(L"example.com"),
          "public hosts cannot use plain HTTP");
    check(!catalog_http_policy::is_loopback_host(L"localhost.example.com"),
          "lookalike hosts are not treated as localhost");
    check(!catalog_http_policy::is_loopback_host(L"127.0.0.2"),
          "non-canonical IPv4 hosts are not accidentally allowed");
    check(!catalog_http_policy::is_loopback_host(L"::2"),
          "non-loopback IPv6 addresses are rejected");

    if (failures != 0) {
        std::fprintf(stderr, "%d catalog HTTP-policy test(s) failed\n", failures);
        return 1;
    }
    std::printf("All catalog HTTP-policy tests passed.\n");
    return 0;
}
