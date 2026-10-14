#include <kos.h>
#include <conio/conio.h>

int main(int argc, char **argv)
{
    uint32_t previous_buttons = 0;

    (void)argc;
    (void)argv;

    /* Initialize KOS video and the on-screen console. */
    pvr_init_defaults();
    conio_init(CONIO_TTY_PVR, CONIO_INPUT_LINE);

    conio_printf("\nBOONTA REBORN 88\n");
    conio_printf("Dreamcast prototype — milestone 1\n\n");
    conio_printf("Video output: initialized\n");
    conio_printf("Controller test: press a button\n");
    conio_printf("START exits only after a later milestone.\n\n");

    cont_init();

    for (;;) {
        maple_device_t *dev = maple_enum_type(0, MAPLE_FUNC_CONTROLLER);
        if (dev != NULL) {
            cont_state_t *state = (cont_state_t *)maple_dev_status(dev);
            if (state != NULL && state->buttons != previous_buttons) {
                if (state->buttons != 0) {
                    conio_printf("Controller buttons: 0x%04x\n",
                                 (unsigned int)state->buttons);
                }
                previous_buttons = state->buttons;
            }
        }

        thd_sleep(16);
    }

    return 0;
}
