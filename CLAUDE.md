# Magic Garden GBC port

"What if it shipped on the Game Boy Color" port of *Magic Garden* (UFO 50 #5). C with GBDK-2020,
CGB-only, MBC5 + 8 KiB battery SRAM, must run on real hardware (an MBC5 flash cart). Fan project;
art is redrawn at GBC resolution, nothing from the original data ships in the ROM.

## Commands

```bash
make                      # build/magicgarden.gbc   (GBDK_HOME defaults to ~/.local/opt/gbdk)
make run                  # open in mGBA (~/.local/opt/mgba.appimage)
python3 tools/make_art.py # regenerate src/gfx_data.c + include/gfx_data.h after editing pixel art
~/.local/opt/pyboy-venv/bin/python tools/sim_test.py    # 22 rule checks (poke grid via RAM) - run after any rules change
~/.local/opt/pyboy-venv/bin/python tools/perf_test.py   # one update per frame + scanline timing
~/.local/opt/pyboy-venv/bin/python tools/autopilot.py   # bot plays; screenshots in build/auto
SAMEBOY_BOOT=~/.local/opt/SameBoy-1.0.3/build/bin/BootROMs/cgb_boot.bin ./tools/sameboy/dump build/magicgarden.gbc "200,5:start,200" build/sameboy/x   # accurate headless run + PPU dump
~/.local/opt/pyboy-venv/bin/python tools/mgba_capture.py build/magicgarden.gbc build/mgba "4,0.3:Return,3"   # drives mGBA on DISPLAY :0
```

## Layout

- `include/game.h` game state struct `game_t` (field order matters: `tools/gbmem.py` parses it) and all tuning constants
- `src/game.c` rules; `src/render.c` BG rows/sprites/HUD; `src/main.c` state machine (title, scores, play, over)
- `src/palettes.c` 4 in-game palette sets + title set; `src/sfx.c` register-level sound effects
- `tools/make_art.py` all pixel art as text + frame/title tile maps -> generated `src/gfx_data.c` (committed, ROM bank 1)
- `tools/gml_dump.py` disassembles the original's GameMaker bytecode (reference/gml/, git-ignored)
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

## Original rules (read from UFO 50's GML bytecode with tools/gml_dump.py; keep the port on these)

- 60 fps, 16-unit cells, player 1 unit/frame (16 frames per cell). Start at cell (1,1) facing right; the run
  begins on the first Right or Down. Input only while grounded: a fresh press wins, else a single held
  direction; never a reversal. Late turn: a changed choice within 2 units of a boundary snaps back to it.
- Jump (A): z=1, v=1.5, v-=0.1/frame -> 30 frames airborne. Boxes (units, cell-relative): player 1..14,
  enemies and mushrooms 4..11, loose/trail oppies 1..14 (checked only when cell-aligned), flasks 0..15.
  Enemy/mushroom/flask collisions are per frame; a pass within 4 units while airborne stuns 240 frames.
- Enemies: idle 128 frames, turn to look at 64, hop one cell in 16 frames (blocked cells rotate the choice),
  frozen while a flask is active, reset to 120 idle when it ends. Passive spawn every 240 frames (paused
  during a flask; one spawns as it ends); growth takes 240 frames. Mushrooms grow the same way.
- Star pads: column 1, column 10, row 1, row 10, or a 4x4 ring / blob at a random spot (no repeat of the
  last shape); life 960 frames. Expiring unused summons (rank+1) mushrooms and a new pad. A save flashes
  the pad 40 frames, then a new pad appears. Drop (B): trail oppies on the pad are saved for
  10 x trail position; the rest become enemies in place.
- Flasks: counter += saved; at >= 6 the level is min(3, counter-6) and the counter resets; the flask drops
  in 60 frames later and falls 90 units; it upgrades a level every 512 frames on the floor. Pickup: 480
  frames of power, +1 multiplier for green+, mushrooms killable with blue+, gold adds a permanent loose
  oppie. Kill score (10 + 10 x kills this flask) x multiplier. Ranks at 50/100/150 saved; win at 200.
- Two loose oppies on the field, replaced immediately when collected.

## Remaining features (backlog)

1. High scores + stats (biggest drop-off, most cleared at once/total) in battery SRAM; the HIGH SCORES
   screen is a zero-filled stub; name entry optional
2. Music: hUGETracker arrangements of gameplay / clear / ending (reference OGGs in `reference/audio/`)
3. Ending cutscene at 200 saved with the Cloverana dialogue, then credits
4. Palette fade on transitions; "PUSH RIGHT OR DOWN" hint while waiting at the start
5. Witch animation when she spawns mushrooms; richer appear/stun frames; flash hop sprites while powered
6. Cascading drop-off conversion (10-frame stagger with a clear effect) and score pop-ups (o27_Points)
7. Player bump animation on death (o27_PlayerBump) and the original game-over flow
8. Easter eggs ("I LOVE JESCA!" after inactivity, running in circles) and the OVER-GROW cheat; tutorial
9. Remove `dbg[]` / `frame_count` diagnostics once tuning is done
