#include <kos.h>

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    /* KOS routes printf output to the configured console/serial output. */
    printf("\nBoonta Reborn 88 — Dreamcast starter\n");
    printf("Clean-room platform test. No game assets loaded.\n");
    printf("Press a controller button to report input.\n");

    cont_init();

    for (;;) {
        maple_device_t *dev = maple_enum_type(0, MAPLE_FUNC_CONTROLLER);
        if (dev != NULL) {
            cont_state_t *state = (cont_state_t *)maple_dev_status(dev);
            if (state != NULL && state->buttons != 0) {
                printf("Controller buttons: 0x%04x\n", state->buttons);
                /* Avoid flooding the console while a button is held. */
                thd_sleep(250);
            }
        }

        thd_sleep(16);
    }

    return 0;
}
