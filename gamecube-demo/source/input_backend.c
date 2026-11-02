#include "input_backend.h"

#include <string.h>

#ifdef BOONTA_WII
#include <wiiuse/wpad.h>
static int g_wpad_classic_format_ready;
#else
#include <ogc/pad.h>
#endif

void boonta_input_init(void)
{
#ifdef BOONTA_WII
    g_wpad_classic_format_ready = 0;
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
        {
            const int probe_succeeded =
                WPAD_Probe(WPAD_CHAN_0, &expansion_type) == WPAD_ERR_NONE;
            const int is_classic = probe_succeeded &&
                expansion_type == WPAD_EXP_CLASSIC;

            if (!probe_succeeded || !is_classic) {
                /* A later connection or newly attached Classic pad needs setup. */
                g_wpad_classic_format_ready = 0;
                return;
            }

            if (boonta_classic_format_should_configure(
                    probe_succeeded, is_classic, g_wpad_classic_format_ready)) {
                /*
                 * WPAD_SetDataFormat silently has no effect for an unassigned
                 * channel. Probe first, then configure once per Classic
                 * connection. Let the next scan deliver the requested report.
                 */
                if (WPAD_SetDataFormat(WPAD_CHAN_0, WPAD_FMT_BTNS_ACC_IR) !=
                    WPAD_ERR_NONE) {
                    return;
                }
                g_wpad_classic_format_ready = 1;
                return;
            }
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
        sample.stick_x = boonta_classic_axis_to_signed(
            data->exp.classic.ljs.pos.x,
            data->exp.classic.ljs.min.x,
            data->exp.classic.ljs.center.x,
            data->exp.classic.ljs.max.x);
        sample.stick_y = boonta_classic_axis_to_signed(
            data->exp.classic.ljs.pos.y,
            data->exp.classic.ljs.min.y,
            data->exp.classic.ljs.center.y,
            data->exp.classic.ljs.max.y);
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
