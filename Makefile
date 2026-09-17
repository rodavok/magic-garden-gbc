# Magic Garden GBC port — GBDK-2020 build
GBDK_HOME ?= $(HOME)/.local/opt/gbdk
LCC       := $(GBDK_HOME)/bin/lcc
PNG2ASSET := $(GBDK_HOME)/bin/png2asset
ROMUSAGE  := $(GBDK_HOME)/bin/romusage
MGBA      ?= $(HOME)/.local/opt/mgba.appimage

PROJECT := magicgarden
BUILD   := build
OBJDIR  := $(BUILD)/obj

# CGB-only ROM, MBC5 + 8 KiB battery SRAM, 4 ROM banks (64 KiB), title "MAGIC GARDEN"
CFLAGS  := -Wa-l -Wl-m -Wl-j -Wf-MMD -Wf--opt-code-speed -Iinclude -I$(BUILD)/res
LDFLAGS := -Wm-yC -Wm-yt0x1B -Wm-ya1 -Wm-yn"MAGIC GARDEN" -Wl-yo4 -Wm-yj

SRC_C  := $(wildcard src/*.c)
GEN_C  := $(patsubst res/%.png,$(BUILD)/res/%.c,$(wildcard res/*.png))
OBJS   := $(patsubst src/%.c,$(OBJDIR)/%.o,$(SRC_C)) $(patsubst $(BUILD)/res/%.c,$(OBJDIR)/res_%.o,$(GEN_C))

all: $(BUILD)/$(PROJECT).gbc

# Asset conversion: res/foo.png -> build/res/foo.c/.h via png2asset.
# Per-file options live in res/foo.opts (one line), e.g. "-spr8x8 -b 255".
$(BUILD)/res/%.c: res/%.png res/%.opts | $(BUILD)/res
	$(PNG2ASSET) $< -c $@ $(shell cat res/$*.opts)

$(OBJDIR)/%.o: src/%.c | $(OBJDIR)
	$(LCC) $(CFLAGS) -c -o $@ $<

$(OBJDIR)/res_%.o: $(BUILD)/res/%.c | $(OBJDIR)
	$(LCC) $(CFLAGS) -c -o $@ $<

$(BUILD)/$(PROJECT).gbc: $(GEN_C) $(OBJS)
	$(LCC) $(CFLAGS) $(LDFLAGS) -o $@ $(OBJS)
	$(ROMUSAGE) $(BUILD)/$(PROJECT).noi -sR 2>/dev/null | head -20 || true

$(BUILD) $(BUILD)/res $(OBJDIR):
	mkdir -p $@

run: all
	$(MGBA) $(BUILD)/$(PROJECT).gbc &

clean:
	rm -rf $(BUILD)

-include $(OBJDIR)/*.d
.PHONY: all run clean
.SECONDARY: $(GEN_C)
