#include "../source/input_backend.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>

static void test_classic_report_format_is_configured_only_after_classic_probe(void)
{
    assert(!boonta_classic_format_should_configure(0, 0, 0));
    assert(!boonta_classic_format_should_configure(1, 0, 0));
    assert(boonta_classic_format_should_configure(1, 1, 0));
    assert(!boonta_classic_format_should_configure(1, 1, 1));
    /* A disconnect/non-Classic probe clears the runtime flag; a later
       Classic connection therefore requests its report format again. */
    assert(boonta_classic_format_should_configure(1, 1, 0));
}

static void test_classic_stick_uses_unsigned_calibrated_raw_values(void)
{
    assert(boonta_classic_axis_to_signed(32U, 0U, 32U, 63U) == 0);
    assert(boonta_classic_axis_to_signed(63U, 0U, 32U, 63U) == 127);
    assert(boonta_classic_axis_to_signed(0U, 0U, 32U, 63U) == -128);
    assert(boonta_classic_axis_to_signed(48U, 0U, 32U, 63U) >= 63);
    assert(boonta_classic_axis_to_signed(16U, 0U, 32U, 63U) <= -64);
    assert(boonta_classic_axis_to_signed(255U, 0U, 32U, 63U) == 127);
    assert(boonta_classic_axis_to_signed(32U, 0U, 32U, 32U) == 0);
}

static void test_all_gameplay_buttons_map(void)
{
    const uint32_t raw =
        BOONTA_CLASSIC_BUTTON_UP | BOONTA_CLASSIC_BUTTON_DOWN |
        BOONTA_CLASSIC_BUTTON_LEFT | BOONTA_CLASSIC_BUTTON_RIGHT |
        BOONTA_CLASSIC_BUTTON_A | BOONTA_CLASSIC_BUTTON_B |
        BOONTA_CLASSIC_BUTTON_X | BOONTA_CLASSIC_BUTTON_Y |
        BOONTA_CLASSIC_BUTTON_PLUS | BOONTA_CLASSIC_BUTTON_ZL |
        BOONTA_CLASSIC_BUTTON_ZR;
    const uint32_t expected =
        BOONTA_BUTTON_UP | BOONTA_BUTTON_DOWN |
        BOONTA_BUTTON_LEFT | BOONTA_BUTTON_RIGHT |
        BOONTA_BUTTON_A | BOONTA_BUTTON_B |
        BOONTA_BUTTON_X | BOONTA_BUTTON_Y |
        BOONTA_BUTTON_START | BOONTA_TRIGGER_L | BOONTA_TRIGGER_R;

    assert(boonta_classic_buttons_to_logical(raw) == expected);
}

static void test_disconnected_and_wrong_expansion_are_neutral(void)
{
    BoontaClassicInputSample sample = {
        0, BOONTA_CLASSIC_BUTTON_A, BOONTA_CLASSIC_BUTTON_A,
        100, -100, 1.0f, 1.0f
    };
    BoontaInputFrame frame = boonta_classic_input_translate(&sample);

    assert(frame.buttons_down == 0U);
    assert(frame.buttons_held == 0U);
    assert(frame.stick_x == 0 && frame.stick_y == 0);
    assert(frame.trigger_l == 0U && frame.trigger_r == 0U);
    assert(boonta_classic_input_translate(0).buttons_held == 0U);

    sample.classic_connected = 1;
    sample.buttons_held = BOONTA_CLASSIC_BUTTON_A;
    sample.stick_x = -44;
    sample.stick_y = 51;
    sample.left_shoulder = 0.0f;
    sample.right_shoulder = 0.0f;
    frame = boonta_classic_input_translate(&sample);
    assert(frame.buttons_held == BOONTA_BUTTON_A);
    assert(frame.stick_x == -44 && frame.stick_y == 51);
}

static void test_shoulders_keep_analog_range_and_digital_clicks(void)
{
    BoontaClassicInputSample sample = {
        1, 0U,
        BOONTA_CLASSIC_BUTTON_FULL_L | BOONTA_CLASSIC_BUTTON_ZR,
        0, 0, 0.5f, 1.0f
    };
    BoontaInputFrame frame = boonta_classic_input_translate(&sample);

    assert((frame.buttons_held & BOONTA_TRIGGER_L) != 0U);
    assert((frame.buttons_held & BOONTA_TRIGGER_R) != 0U);
    assert(frame.trigger_l >= 127U && frame.trigger_l <= 128U);
    assert(frame.trigger_r == 255U);
    assert(boonta_classic_trigger_to_byte(0.0f) == 0U);
    assert(boonta_classic_trigger_to_byte(-0.2f) == 0U);
    assert(boonta_classic_trigger_to_byte(1.0f) == 255U);
    assert(boonta_classic_trigger_to_byte(NAN) == 0U);
}

int main(void)
{
    test_classic_report_format_is_configured_only_after_classic_probe();
    test_classic_stick_uses_unsigned_calibrated_raw_values();
    test_all_gameplay_buttons_map();
    test_disconnected_and_wrong_expansion_are_neutral();
    test_shoulders_keep_analog_range_and_digital_clicks();
    puts("Wii Classic Controller input translation tests passed.");
    return 0;
}
