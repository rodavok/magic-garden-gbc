# Magic Garden GBC port

"What if it shipped on the Game Boy Color" port of *Magic Garden* (UFO 50 #5). C with GBDK-2020,
CGB-only, MBC5 + 8 KiB battery SRAM, must run on real hardware (an MBC5 flash cart). Fan project;
art is redrawn at GBC resolution, nothing from the original data ships in the ROM.

## Commands

```bash
make                      # build/magicgarden.gbc   (GBDK_HOME defaults to ~/.local/opt/gbdk)
make run                  # open in mGBA (~/.local/opt/mgba.appimage)
python3 tools/make_art.py # regenerate src/gfx_data.c + include/gfx_data.h after editing pixel art
~/.local/opt/pyboy-venv/bin/python tools/sim_test.py    # 19 rule checks (poke grid via RAM) - run after any rules change
~/.local/opt/pyboy-venv/bin/python tools/perf_test.py   # one update per frame + scanline timing
~/.local/opt/pyboy-venv/bin/python tools/autopilot.py   # bot plays; screenshots in build/auto
SAMEBOY_BOOT=~/.local/opt/SameBoy-1.0.3/build/bin/BootROMs/cgb_boot.bin ./tools/sameboy/dump build/magicgarden.gbc "200,5:start,200" build/sameboy/x   # accurate headless run + PPU dump
~/.local/opt/pyboy-venv/bin/python tools/mgba_capture.py build/magicgarden.gbc build/mgba "4,0.3:Return,3"   # drives mGBA on DISPLAY :0
```

## Layout

- `include/game.h` game state struct `game_t` (field order matters: `tools/gbmem.py` parses it) and all tuning constants
- `src/game.c` rules; `src/render.c` BG rows/sprites/HUD; `src/main.c` state machine (title, scores, play, over)
- `src/palettes.c` 4 in-game palette sets + title set; `src/sfx.c` register-level sound effects
- `tools/make_art.py` all pixel art as text + frame/title tile maps -> generated `src/gfx_data.c` (committed)
- `MAGIC_GARDEN_GBC_BRIEF.md` research on the original game; `reference/` extracted originals (git-ignored)

## Hard rules (learned the hard way)

- VRAM and palette writes only in VBlank (after `wait_vbl_done()`) or with the LCD off at boot. Screen
  transitions use `vram_draw_map()` (2 rows per VBlank); the game flushes at most 4 dirty rows per frame.
  Never switch the LCD off after boot: emulators such as John GBC drop LCD-off writes.
- No per-frame full-grid scans. SDCC sm83 code costs 200-500 cycles per loop iteration; use the entity lists
  (`angry_list`, `appear_list`, `flask_list`) and `DIRTY_ROW`.
- Avoid signed casts into inline helpers (SDCC 4.5 miscompiled `cidx((uint8_t)nx, (uint8_t)ny)`); use
  `neighbor()` with unsigned bounds checks.
- Game logic runs from scanline 2 (`while (LY_REG != 2)`), so PyBoy tests read RAM at frame boundaries
  and step by `frame_count`, not emulator ticks.
- Palette budget: BG 0/1 friendly on floor A/B, 2/3 angry+mushroom, 4/5 star row, 6 decoration
  (ground, black, purple, light blue), 7 HUD. OBJ 0 player, 1-4 flasks, 5 shadow, 6 oppie sprite.

## Remaining features (backlog)

1. High scores + stats (biggest drop-off, most cleared at once/total) in battery SRAM; the HIGH SCORES
   screen is a zero-filled stub; name entry optional
2. Music: hUGETracker arrangements of gameplay / clear / ending (reference OGGs in `reference/audio/`)
3. Ending cutscene at 200 saved with the Cloverana dialogue, then credits
4. Score pop-ups, "READY" prompt, palette fade on transitions
5. Witch animation when she spawns mushrooms; angry-oppie hop as a sprite; richer appear/stun frames
6. Tighter per-object jump timing windows (now: any press in the cell before the obstacle clears it)
7. Tuning vs. the original: cells/second, spawn intervals, star-row relocation rule, loose-oppie count
8. Easter eggs ("I LOVE JESCA!" after inactivity, running in circles) and the OVER-GROW cheat; tutorial
9. Remove `dbg[]` / `frame_count` diagnostics once tuning is done
