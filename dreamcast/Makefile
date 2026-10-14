# Minimal KallistiOS project template.
# Requires a configured Dreamcast KallistiOS toolchain and KOS_BASE.
TARGET = boonta_dc
OBJS = main.o

all: rm-elf $(TARGET).elf

include $(KOS_BASE)/Makefile.rules
include $(KOS_BASE)/Makefile.prefab

clean:
	-rm -f $(OBJS) $(TARGET).elf $(TARGET).bin $(TARGET).bin.* $(TARGET).map
