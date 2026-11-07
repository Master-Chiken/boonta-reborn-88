#include "../dinput_hook/cursor_policy.h"

#include <cmath>
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
    const auto near = [](float a, float b) { return std::fabs(a - b) < 0.0001f; };

    check(!cursor_policy_should_draw_game_sprite(false, false),
          "OS-cursor mode suppresses the software cursor");
    check(cursor_policy_should_draw_game_sprite(true, false),
          "game-cursor mode draws the software cursor when the overlay is closed");
    check(!cursor_policy_should_draw_game_sprite(true, true),
          "ImGui overlay owns the cursor when open");
    check(!cursor_policy_should_draw_game_sprite(false, true),
          "OS-cursor mode stays suppressed with the overlay open");

    check(near(cursor_policy_scale_factor(1.0f, 2.0f), 0.5f),
          "640x480 widget space is not doubled by the engine sprite scale");
    check(near(cursor_policy_scale_factor(2.25f, 4.5f), 0.5f),
          "widget scaling is consistent at 1080p");
    check(near(cursor_policy_scale_factor(1.5f, 3.0f), 0.5f),
          "widget scaling is consistent with a changed UI scale");
    check(near(cursor_policy_scale_factor(2.0f, 0.0f), 1.0f),
          "non-positive engine scale safely preserves the incoming scale");

    if (failures != 0) {
        std::fprintf(stderr, "%d cursor-policy test(s) failed\n", failures);
        return 1;
    }
    std::printf("All cursor-policy tests passed.\n");
    return 0;
}
