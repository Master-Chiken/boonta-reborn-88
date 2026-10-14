# Standalone clean-room GameCube build smoke test.
# This is deliberately separate from the full Step 102 prototype.

.SUFFIXES:

TARGET := boonta_smoke
BUILD := build
SOURCES := source
OUTPUT := $(TARGET)

CFILES := $(wildcard $(SOURCES)/*.c)
OFILES := $(patsubst $(SOURCES)/%.c,$(BUILD)/%.o,$(CFILES))
DEPENDS := $(OFILES:.o=.d)

CFLAGS = -g -O2 -Wall -Wextra $(MACHDEP) -I$(DEVKITPRO)/libogc/include
CXXFLAGS = $(CFLAGS)
LDFLAGS = $(MACHDEP)

include $(DEVKITPPC)/gamecube_rules

LIBPATHS := -L$(LIBOGC_LIB)
LIBS := -logc -lm

.PHONY: all clean
all: $(OUTPUT).dol

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.o: $(SOURCES)/%.c | $(BUILD)
	$(CC) -MMD -MP -MF $(BUILD)/$*.d $(CPPFLAGS) $(CFLAGS) -c $< -o $@

# devkitPPC's gamecube_rules provides the linker/ELF-to-DOL recipes.
$(OUTPUT).elf: $(OFILES)
$(OUTPUT).dol: $(OUTPUT).elf

clean:
	rm -rf $(BUILD) $(OUTPUT).elf $(OUTPUT).dol

-include $(DEPENDS)
