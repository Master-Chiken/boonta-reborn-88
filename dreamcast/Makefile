# KallistiOS Dreamcast application. Follows the upstream KOS hello/maple examples.
TARGET = boonta_dc.elf
OBJS = main.o

all: rm-elf $(TARGET)

include $(KOS_BASE)/Makefile.rules

$(TARGET): $(OBJS)
	kos-cc -o $(TARGET) $(OBJS)

rm-elf:
	-rm -f $(TARGET)

clean: rm-elf
	-rm -f $(OBJS)

.PHONY: all clean rm-elf
