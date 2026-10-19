#include <kos.h>
#include <dc/pvr.h>

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    printf("\nBoonta Reborn 88 — Dreamcast video smoke test\n");
    printf("Original clean-room test. No commercial game assets loaded.\n");
    printf("The screen colour changes when a controller button is pressed.\n");

    cont_init();

    if (pvr_init_defaults() < 0) {
        printf("ERROR: PVR initialization failed.\n");
        for (;;) {
            thd_sleep(1000);
        }
    }

    for (;;) {
        maple_device_t *dev = maple_enum_type(0, MAPLE_FUNC_CONTROLLER);
        cont_state_t *state = NULL;
        uint16_t buttons = 0;

        if (dev != NULL) {
            state = (cont_state_t *)maple_dev_status(dev);
            if (state != NULL) {
                buttons = state->buttons;
            }
        }

        /*
         * Visible smoke test: use the Dreamcast PowerVR background colour.
         * The colour changes with controller input, so the screen gives
         * immediate visual feedback even without a text overlay.
         */
        if (buttons != 0) {
            pvr_set_bg_color(0.0f, 0.45f, 0.85f);
        } else if (dev != NULL) {
            pvr_set_bg_color(0.02f, 0.12f, 0.18f);
        } else {
            pvr_set_bg_color(0.16f, 0.02f, 0.20f);
        }

        pvr_wait_ready();
        pvr_scene_begin();
        pvr_scene_finish();

        thd_sleep(16);
    }

    return 0;
}
