# Magic Garden — Game Boy Color port

A "what if it had shipped on the GBC" port of *Magic Garden* (game #5 of UFO 50, Mossmouth).
Written in C with GBDK-2020, built as a CGB-only MBC5 cartridge image that runs on real hardware
(any MBC5 flash cart).

Fan project. All characters, names and the original game are (c) Mossmouth. Nothing from the
original game's data ships in the ROM; the art here is redrawn at GBC resolution.

## Build & run

Requirements: GBDK-2020 4.5.0 in `~/.local/opt/gbdk` (or set `GBDK_HOME`), Python 3 + Pillow for
the art generator, mGBA for playing on PC.

```bash
make            # -> build/magicgarden.gbc (64 KiB, CGB-only, MBC5+RAM+battery)
make run        # opens the ROM in mGBA ($MGBA, default ~/.local/opt/mgba.appimage)
```

Art is generated: edit `tools/make_art.py` and run `python3 tools/make_art.py` to regenerate
`src/gfx_data.c` / `include/gfx_data.h` (both are committed).

### Tests (PyBoy, headless)

```bash
~/.local/opt/pyboy-venv/bin/python tools/sim_test.py     # 19 rule checks by poking the grid in RAM
~/.local/opt/pyboy-venv/bin/python tools/perf_test.py    # asserts one game update per frame + LY timing
~/.local/opt/pyboy-venv/bin/python tools/autopilot.py    # a bot plays for a while; screenshots in build/auto
~/.local/opt/pyboy-venv/bin/python tools/play_test.py build/magicgarden.gbc build/shots "200,30:start,300"
```

`tools/gbmem.py` derives the `game_t` layout from `include/game.h`, so the tests follow struct changes.

## Real hardware notes

- Header: CGB flag `$C0`, cart type `$1B` (MBC5+RAM+BATTERY), 64 KiB ROM, 8 KiB SRAM, Nintendo logo and
  header checksum written by `makebin` (verified in the built file at `$0134`).
- Runs in CGB double-speed mode. Frame budget is ~6 scanlines of the 154 available.
- All VRAM writes happen in VBlank right after `wait_vbl_done()` (row updates capped at 4 rows per
  frame) or with the LCD off (title, game start). Game logic runs from scanline 2.
- Flash cart: copy `build/magicgarden.gbc` to the cart. SRAM is reserved but not used yet.

## Controls

| Input | Action |
|---|---|
| D-pad | Turn (no 180° reversal). The Gardener never stops. |
| A | Jump: skips the next cell entered, lands in the one after (stuns an angry oppie you pass over) |
| B | Drop the whole trail: saved on the star row, angry anywhere else |
| Start / A | Menu select, start; B leaves the high-score screen |

## What is implemented (v1 playable core)

- 12x12 grid, continuous movement with an interpolated 8x16 Gardener sprite, cell-stepped trail
- Loose friendly oppies (kept at a target count), trail collection, per-segment drop resolution
- Star row that relocates after every save; saved oppie scoring `10 x trail position`
- Angry oppies: passive spawns, dropped-trail conversions, look-then-hop movement, stun on jump-over
- Mushrooms from the witch after 20 s without a save (1/2/3 at 0/100/150 saved)
- Flasks: counter of 6, overflow levels (red/green/blue/gold), floor upgrades, 48-unit power timer,
  chain scoring with multiplier, mushroom kills need blue/gold, gold adds a permanent friendly oppie
- Palette set change every 50 saved, win at 200, game over on any collision, HUD, sound effects
- Music via hUGEDriver: gameplay loop, win sting, lose sting, ending theme (auto-transcribed from the originals)
- Battery-backed high scores and stats; ending sequence with dialogue and credits

## Backlog

See the "Remaining features" list in `CLAUDE.md`.

## Layout

```
include/game.h      game state, tuning constants
src/game.c          rules: movement, trail, drops, entities, spawners, flasks, scoring
src/render.c        BG row rendering (dirty rows), sprites, HUD
src/palettes.c      4 palette sets (BG 0-5 grid, 6 decoration, 7 HUD; OBJ 0 player, 1-4 flasks, 5 shadow)
src/sfx.c           register-level sound effects
src/main.c          title / play / game-over loop
tools/make_art.py   pixel art + frame map generator -> src/gfx_data.c
tools/extract_gm.py reference extractor for a local UFO 50 install (not needed to build)
reference/          research brief, original screenshots, extracted reference sprites (git-ignored)
```
