#include "input_backend.h"

#include <string.h>

#ifdef BOONTA_WII
#include <ogc/wpad.h>
#else
#include <ogc/pad.h>
#endif

void boonta_input_init(void)
{
#ifdef BOONTA_WII
    (void)WPAD_Init();
#else
    (void)PAD_Init();
#endif
}

void boonta_input_poll(BoontaInputFrame *frame)
{
    if (frame == 0) return;
    memset(frame, 0, sizeof(*frame));

#ifdef BOONTA_WII
    {
        u32 expansion_type = WPAD_EXP_NONE;
        WPADData *data;
        BoontaClassicInputSample sample;

        (void)WPAD_ScanPads();

        /* Never interpret a Wii Remote/Nunchuk/other expansion as Classic. */
        if (WPAD_Probe(WPAD_CHAN_0, &expansion_type) != WPAD_ERR_NONE ||
            expansion_type != WPAD_EXP_CLASSIC) {
            return;
        }

        data = WPAD_Data(WPAD_CHAN_0);
        if (data == 0 ||
            (data->data_present & WPAD_DATA_EXPANSION) == 0U ||
            data->exp.type != WPAD_EXP_CLASSIC) {
            return;
        }

        sample.classic_connected = 1;
        sample.buttons_down = WPAD_ButtonsDown(WPAD_CHAN_0);
        sample.buttons_held = WPAD_ButtonsHeld(WPAD_CHAN_0);
        sample.stick_x = (int8_t)data->exp.classic.ljs.pos.x;
        sample.stick_y = (int8_t)data->exp.classic.ljs.pos.y;
        sample.left_shoulder = data->exp.classic.l_shoulder;
        sample.right_shoulder = data->exp.classic.r_shoulder;
        *frame = boonta_classic_input_translate(&sample);
    }
#else
    PAD_ScanPads();
    frame->buttons_down = (uint32_t)PAD_ButtonsDown(0);
    frame->buttons_held = (uint32_t)PAD_ButtonsHeld(0);
    frame->stick_x = (int8_t)PAD_StickX(0);
    frame->stick_y = (int8_t)PAD_StickY(0);
    frame->trigger_l = (uint8_t)PAD_TriggerL(0);
    frame->trigger_r = (uint8_t)PAD_TriggerR(0);
#endif
}
