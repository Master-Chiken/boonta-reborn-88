# Standalone clean-room GameCube build smoke test.
# This is deliberately separate from the full Step 102 prototype.

TARGET := boonta_smoke
BUILD := build
SOURCES := source
DATA :=
INCLUDES :=

CFLAGS = -g -O2 -Wall -Wextra $(MACHDEP) $(INCLUDE)
CXXFLAGS = $(CFLAGS)
LDFLAGS = $(MACHDEP)
LIBS := -logc -lm

include $(DEVKITPPC)/gamecube_rules
