#ifndef BOONTA_REBORN_INPUT_BACKEND_H
#define BOONTA_REBORN_INPUT_BACKEND_H

#include <math.h>
#include <stdint.h>

/*
 * Platform-neutral logical buttons. Their bit positions intentionally match
 * libogc's PAD_BUTTON_* / PAD_TRIGGER_* values so gameplay decisions stay
 * independent of the physical controller backend.
 */
#define BOONTA_BUTTON_LEFT   0x0001u
#define BOONTA_BUTTON_RIGHT  0x0002u
#define BOONTA_BUTTON_DOWN   0x0004u
#define BOONTA_BUTTON_UP     0x0008u
#define BOONTA_TRIGGER_R     0x0020u
#define BOONTA_TRIGGER_L     0x0040u
#define BOONTA_BUTTON_A      0x0100u
#define BOONTA_BUTTON_B      0x0200u
#define BOONTA_BUTTON_X      0x0400u
#define BOONTA_BUTTON_Y      0x0800u
#define BOONTA_BUTTON_START  0x1000u

/*
 * libogc's WPAD_CLASSIC_BUTTON_* masks (gc/wiiuse/wpad.h). Keeping the raw
 * masks here lets host tests validate translation without requiring a Wii SDK.
 */
#define BOONTA_CLASSIC_BUTTON_UP       (0x0001u << 16)
#define BOONTA_CLASSIC_BUTTON_LEFT     (0x0002u << 16)
#define BOONTA_CLASSIC_BUTTON_ZR       (0x0004u << 16)
#define BOONTA_CLASSIC_BUTTON_X        (0x0008u << 16)
#define BOONTA_CLASSIC_BUTTON_A        (0x0010u << 16)
#define BOONTA_CLASSIC_BUTTON_Y        (0x0020u << 16)
#define BOONTA_CLASSIC_BUTTON_B        (0x0040u << 16)
#define BOONTA_CLASSIC_BUTTON_ZL       (0x0080u << 16)
#define BOONTA_CLASSIC_BUTTON_FULL_R   (0x0200u << 16)
#define BOONTA_CLASSIC_BUTTON_PLUS     (0x0400u << 16)
#define BOONTA_CLASSIC_BUTTON_FULL_L   (0x2000u << 16)
#define BOONTA_CLASSIC_BUTTON_DOWN     (0x4000u << 16)
#define BOONTA_CLASSIC_BUTTON_RIGHT    (0x8000u << 16)

typedef struct {
    uint32_t buttons_down;
    uint32_t buttons_held;
    int8_t stick_x;
    int8_t stick_y;
    uint8_t trigger_l;
    uint8_t trigger_r;
} BoontaInputFrame;

/* A sample is accepted only after WPAD_Probe reports WPAD_EXP_CLASSIC. */
typedef struct {
    int classic_connected;
    uint32_t buttons_down;
    uint32_t buttons_held;
    int8_t stick_x;
    int8_t stick_y;
    float left_shoulder;
    float right_shoulder;
} BoontaClassicInputSample;

/*
 * libogc exposes Classic joystick pos/min/center/max as unsigned raw bytes.
 * Convert each calibrated half-range to the signed [-128, 127] range expected
 * by the existing GameCube gameplay helpers; never cast the raw byte directly.
 */
static inline int8_t boonta_classic_axis_to_signed(uint8_t raw,
                                                    uint8_t minimum,
                                                    uint8_t center,
                                                    uint8_t maximum)
{
    int delta = (int)raw - (int)center;
    int range = delta >= 0
        ? (int)maximum - (int)center
        : (int)center - (int)minimum;
    int scaled;

    if (range <= 0) return 0;
    if (delta > 0) {
        scaled = delta * 127 / range;
        if (scaled > 127) scaled = 127;
    } else if (delta < 0) {
        scaled = delta * 128 / range;
        if (scaled < -128) scaled = -128;
    } else {
        scaled = 0;
    }
    return (int8_t)scaled;
}

/*
 * WPAD_SetDataFormat is channel-specific and only takes effect once a
 * controller has been assigned to that channel. Configure after a successful
 * Classic probe, not immediately after WPAD_Init.
 */
static inline int boonta_classic_format_should_configure(int probe_succeeded,
                                                          int is_classic,
                                                          int already_configured)
{
    return probe_succeeded && is_classic && !already_configured;
}

static inline uint8_t boonta_classic_trigger_to_byte(float value)
{
    if (!isfinite(value) || value <= 0.0f) return 0U;
    if (value >= 1.0f) return 255U;
    return (uint8_t)(value * 255.0f + 0.5f);
}

static inline uint32_t boonta_classic_buttons_to_logical(uint32_t buttons)
{
    uint32_t mapped = 0U;

    if ((buttons & BOONTA_CLASSIC_BUTTON_LEFT) != 0U) mapped |= BOONTA_BUTTON_LEFT;
    if ((buttons & BOONTA_CLASSIC_BUTTON_RIGHT) != 0U) mapped |= BOONTA_BUTTON_RIGHT;
    if ((buttons & BOONTA_CLASSIC_BUTTON_DOWN) != 0U) mapped |= BOONTA_BUTTON_DOWN;
    if ((buttons & BOONTA_CLASSIC_BUTTON_UP) != 0U) mapped |= BOONTA_BUTTON_UP;
    if ((buttons & BOONTA_CLASSIC_BUTTON_A) != 0U) mapped |= BOONTA_BUTTON_A;
    if ((buttons & BOONTA_CLASSIC_BUTTON_B) != 0U) mapped |= BOONTA_BUTTON_B;
    if ((buttons & BOONTA_CLASSIC_BUTTON_X) != 0U) mapped |= BOONTA_BUTTON_X;
    if ((buttons & BOONTA_CLASSIC_BUTTON_Y) != 0U) mapped |= BOONTA_BUTTON_Y;
    if ((buttons & BOONTA_CLASSIC_BUTTON_PLUS) != 0U) mapped |= BOONTA_BUTTON_START;
    if ((buttons & (BOONTA_CLASSIC_BUTTON_ZL | BOONTA_CLASSIC_BUTTON_FULL_L)) != 0U) {
        mapped |= BOONTA_TRIGGER_L;
    }
    if ((buttons & (BOONTA_CLASSIC_BUTTON_ZR | BOONTA_CLASSIC_BUTTON_FULL_R)) != 0U) {
        mapped |= BOONTA_TRIGGER_R;
    }
    return mapped;
}

static inline BoontaInputFrame boonta_classic_input_translate(
    const BoontaClassicInputSample *sample)
{
    BoontaInputFrame frame = {0U, 0U, 0, 0, 0U, 0U};

    /* Disconnected pads and non-Classic expansions always become neutral. */
    if (sample == 0 || !sample->classic_connected) return frame;

    frame.buttons_down = boonta_classic_buttons_to_logical(sample->buttons_down);
    frame.buttons_held = boonta_classic_buttons_to_logical(sample->buttons_held);
    frame.stick_x = sample->stick_x;
    frame.stick_y = sample->stick_y;
    frame.trigger_l = boonta_classic_trigger_to_byte(sample->left_shoulder);
    frame.trigger_r = boonta_classic_trigger_to_byte(sample->right_shoulder);
    return frame;
}

void boonta_input_init(void);
void boonta_input_poll(BoontaInputFrame *frame);

#endif
