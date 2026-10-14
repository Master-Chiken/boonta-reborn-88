# KallistiOS Dreamcast application.
TARGET = boonta_dc.elf
OBJS = main.o

all: $(TARGET)

include $(KOS_BASE)/Makefile.rules
include $(KOS_BASE)/Makefile.prefab

clean:
	-rm -f $(OBJS) $(TARGET) boonta_dc.bin boonta_dc.map

.PHONY: all clean
