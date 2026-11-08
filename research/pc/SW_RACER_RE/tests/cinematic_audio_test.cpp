#include "../dinput_hook/cinematic_audio.h"

#include <cmath>
#include <iostream>

struct TestCase {
    const char *name;
    int sound_enabled;
    float master_volume;
    float cutscene_volume;
    float expected;
};

int main() {
    constexpr TestCase cases[] = {
        {"sound-off mutes full-volume cinematic", 0, 1.0f, 1.0f, 0.0f},
        {"sound-off mutes partial-volume cinematic", 0, 0.25f, 0.7f, 0.0f},
        {"sound-on preserves cutscene slider", 1, 1.0f, 0.7f, 0.7f},
        {"sound-on multiplies master and cutscene sliders", 1, 0.5f, 0.6f, 0.3f},
        {"lower volume is clamped", 1, -0.5f, 1.0f, 0.0f},
        {"upper volume is clamped", 1, 2.0f, 1.0f, 1.0f},
    };

    int failures = 0;
    for (const TestCase &test : cases) {
        const float actual = cinematic_effective_volume(
            test.sound_enabled, test.master_volume, test.cutscene_volume);
        if (std::fabs(actual - test.expected) > 0.0001f) {
            std::cerr << "FAIL: " << test.name << " (expected " << test.expected
                      << ", got " << actual << ")\n";
            ++failures;
        } else {
            std::cout << "PASS: " << test.name << "\n";
        }
    }
    return failures == 0 ? 0 : 1;
}
