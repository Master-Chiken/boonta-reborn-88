# Native GameCube DOL for the isolated N64Recomp memory semantics probe.
.SUFFIXES:
.DEFAULT_GOAL := all

ifeq ($(strip $(DEVKITPPC)),)
$(error "DEVKITPPC is not set. Use the devkitpro/devkitppc container.")
endif
ifeq ($(strip $(N64RECOMP_INCLUDE)),)
ifneq ($(filter clean,$(MAKECMDGOALS)),clean)
$(error "N64RECOMP_INCLUDE must point to the locally patched upstream N64Recomp include directory.")
endif
endif

include $(DEVKITPPC)/gamecube_rules

TARGET   := recomp_memory_probe
BUILD    := build
SOURCES  := .
INCLUDES := . ..
N64MODERN_RUNTIME_INCLUDE ?=

CFLAGS   = -g -O2 -Wall -Wextra -Werror -std=gnu11 $(MACHDEP) $(INCLUDE)
CXXFLAGS = -g -O2 -Wall -Wextra -Werror -std=gnu++20 $(MACHDEP) $(INCLUDE)
LDFLAGS  = -g $(MACHDEP) -Wl,-Map,$(notdir $@).map
LIBS     := -logc -lm
LIBDIRS  :=

ifneq ($(BUILD),$(notdir $(CURDIR)))
export OUTPUT  := $(CURDIR)/$(TARGET)
export VPATH   := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir))
export DEPSDIR := $(CURDIR)/$(BUILD)

CFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
CPPFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.cpp)))
sFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))
SFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.S)))

ifeq ($(strip $(CPPFILES)),)
  export LD := $(CC)
else
  export LD := $(CXX)
endif

export OFILES_SOURCES := $(CPPFILES:.cpp=.o) $(CFILES:.c=.o) $(sFILES:.s=.o) $(SFILES:.S=.o)
export OFILES := $(OFILES_SOURCES)
export INCLUDE := $(foreach dir,$(INCLUDES),-iquote $(CURDIR)/$(dir)) -I$(N64RECOMP_INCLUDE) $(if $(N64MODERN_RUNTIME_INCLUDE),-I$(N64MODERN_RUNTIME_INCLUDE)) -I$(LIBOGC_INC)
export LIBPATHS := -L$(LIBOGC_LIB) $(foreach dir,$(LIBDIRS),-L$(dir)/lib)

.PHONY: all $(BUILD) clean
all: $(BUILD)

$(BUILD):
	@[ -d $@ ] || mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

clean:
	@rm -fr $(BUILD) $(OUTPUT).elf $(OUTPUT).dol $(OUTPUT).elf.map

else
.PHONY: all
all: $(OUTPUT).dol

DEPENDS := $(OFILES:.o=.d)

$(OUTPUT).dol: $(OUTPUT).elf
$(OUTPUT).elf: $(OFILES_SOURCES)

$(OFILES_SOURCES):

-include $(DEPENDS)
endif
