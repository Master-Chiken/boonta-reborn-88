#pragma once

// Pure volume policy for pre-rendered Smush cinematics. This header intentionally has no Windows
// or game dependencies so its behavior can be regression-tested independently of the injected DLL.
constexpr float cinematic_effective_volume(int sound_enabled, float master_volume,
                                           float cutscene_volume) noexcept {
    const float effective =
        sound_enabled != 0 ? master_volume * cutscene_volume : 0.0f;
    return effective < 0.0f ? 0.0f : (effective > 1.0f ? 1.0f : effective);
}
