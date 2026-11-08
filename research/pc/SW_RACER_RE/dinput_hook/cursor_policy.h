#pragma once

// Small, side-effect-free policy helpers for the game/OS cursor split. Kept independent of Win32,
// GLFW, ImGui and game symbols so the behavior can be regression-tested on any host compiler.
constexpr bool cursor_policy_should_draw_game_sprite(bool game_cursor_enabled, bool imgui_overlay_open) noexcept {
    return game_cursor_enabled && !imgui_overlay_open;
}

// The software cursor is authored in widget (640x480) units, but the engine's shared sprite draw
// call uses its separate ~320x240 scale. Return the factor that converts the engine scale to widget
// scale. A non-positive engine scale is not expected during rendering; preserve the input scale if
// called defensively before the display has been initialized.
constexpr float cursor_policy_scale_factor(float widget_scale, float engine_sprite_scale) noexcept {
    return engine_sprite_scale > 0.0f ? widget_scale / engine_sprite_scale : 1.0f;
}
