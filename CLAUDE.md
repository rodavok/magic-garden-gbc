# Magic Garden GBC port

"What if it shipped on the Game Boy Color" port of *Magic Garden* (UFO 50 #5). C with GBDK-2020,
CGB-only, MBC5 + 8 KiB battery SRAM, must run on real hardware (an MBC5 flash cart). Fan project;
art is redrawn at GBC resolution, nothing from the original data ships in the ROM. The rules follow the
original exactly (see "Original rules"); when in doubt, read the original's code, don't guess.

## Commands

```bash
make                      # build/magicgarden.gbc   (GBDK_HOME defaults to ~/.local/opt/gbdk)
make run                  # open in mGBA (~/.local/opt/mgba.appimage)
python3 tools/make_art.py # regenerate src/gfx_data.c + include/gfx_data.h after editing pixel art
~/.local/opt/pyboy-venv/bin/python tools/sim_test.py    # 22 rule checks (poke grid via RAM) - run after any rules change
~/.local/opt/pyboy-venv/bin/python tools/perf_test.py   # one update per frame + scanline timing
~/.local/opt/pyboy-venv/bin/python tools/stress_test.py build/magicgarden.gbc 64 48 [play|power|drop]   # full field: 0 skipped frames expected
~/.local/opt/pyboy-venv/bin/python tools/autopilot.py   # bot plays a minute; screenshots in build/auto
SAMEBOY_BOOT=~/.local/opt/SameBoy-1.0.3/build/bin/BootROMs/cgb_boot.bin ./tools/sameboy/dump build/magicgarden.gbc "230,5:start,40,5:down,600" build/sameboy/x   # accurate headless run: PPM frames + PPU/palette/tilemap dump per step
SAMEBOY_WAV=build/sameboy/out.wav SAMEBOY_BOOT=... ./tools/sameboy/dump ...                 # same, also records the audio
~/.local/opt/pyboy-venv/bin/python tools/mgba_capture.py build/magicgarden.gbc build/mgba "4,0.3:Return,3"   # drives mGBA on DISPLAY :0
```

Regenerating music (only if the transcriber or reference audio changes):

```bash
( echo '#pragma bank 2'; echo '#include "hUGEDriver.h"'; echo '#include <stddef.h>'; echo ) > src/music_data.c
for spec in "bgm27_gameplay song_gameplay --loop --rows 352" "bgm27_stingWin song_win" "bgm27_stingLose song_lose" "bgm27_end song_end"; do
  set -- $spec; ~/.local/opt/pyboy-venv/bin/python tools/transcribe.py reference/audio/$1.ogg $2 /tmp/$2.c $3 $4 $5; cat /tmp/$2.c >> src/music_data.c; done
~/.local/opt/pyboy-venv/bin/python tools/eval_transcription.py   # chroma score of the transcription vs the original
```

Never run the PyBoy tests while `make` is still writing the ROM: they read a half-written file and report garbage.

## Layout

- `include/game.h` game state struct `game_t` (field order matters: `tools/gbmem.py` parses it, and `pop_t` is 7 bytes) and all tuning constants
- `src/game.c` rules; `src/render.c` BG rows/sprites/HUD/pop-ups; `src/main.c` main loop (bank 0)
- `src/screens.c` title, high scores, game start, ending (bank 1); `src/save.c` SRAM; `src/palettes.c`; `src/sfx.c` register-level effects (all bank 1)
- `src/music.c` song control (bank 0); `src/music_data.c` generated songs (bank 2); `src/hugebank.s` bank symbols for the driver
- `lib/hUGEDriver.o` hUGEDriver in bank 2: RGBDS 0.7.0 `rgbasm -I. -DGBDK` on a copy whose "Sound Driver"
  section is `ROMX, BANK[2]`, then `rgb2sdas.py -b 2`, then its `S b*hUGE_* Ref000002` records patched to
  `Ref000000` (GBDK's linker rejects a nonzero S_REF). Sources: ~/.local/opt/hUGEDriver, ~/.local/opt/rgbds-v0.7.0
- `tools/make_art.py` all pixel art as text + frame/title tile maps -> `src/gfx_data.c` (committed, bank 1)
- `tools/gml_dump.py` disassembles the original's GameMaker bytecode into reference/gml/ (git-ignored)
- `tools/extract_gm.py` pulls the original sprites/audio from the local UFO 50 install into reference/ (git-ignored)
- `tools/transcribe.py` OGG -> hUGEDriver song C (row = 11 frames = an eighth note); `tools/eval_transcription.py` scorer
- `tools/sameboy/dump.c` SameBoy-core harness (frames, PPU state, WAV); `tools/gbmem.py` RAM access for PyBoy tests
- `MAGIC_GARDEN_GBC_BRIEF.md` research on the original game

## Hard rules (learned the hard way)

- VRAM and palette writes only in VBlank (after `wait_vbl_done()`) or with the LCD off at boot. Screen
  transitions use `vram_draw_map()` (2 rows per VBlank); the game flushes at most 4 dirty rows per frame
  by direct `memcpy` into the tile map (GBDK's `set_bkg_tiles` is several times slower and overran VBlank).
  Never switch the LCD off after boot: emulators such as John GBC drop LCD-off writes.
- Never call `hud_text()` with an empty string: a zero width underflows to 256 tiles in `set_bkg_tiles`.
- No per-frame full-grid scans. SDCC sm83 code costs 200-500 cycles per loop iteration; use the entity lists
  (`angry_list`, `appear_list`, `flask_list`) and `DIRTY_ROW`. No division, modulo or 16-bit multiply on the
  frame path, not even 8-bit `i % GW` / `i / GW` (a library call each; use `cell_x[]` / `cell_y[]`): they
  made the game slow down with 8 enemies. Collision scans the cells around the player, not the angry list;
  the enemy loop only calls out when a timer hits 0 or ENEMY_LOOK_AT. Tile rows are rebuilt last in the
  frame and only while LY < ROW_LY_LIMIT (about 15 lines a row); at most one 32-bit decimal conversion
  (pop-up or HUD) per frame. Check with `tools/stress_test.py` after touching the frame path.
- Avoid signed casts into inline helpers (SDCC 4.5 miscompiled `cidx((uint8_t)nx, (uint8_t)ny)`); use
  `neighbor()` with unsigned bounds checks.
- Game logic runs from scanline 2 (or at once if a flush ran late), so PyBoy tests read RAM at frame
  boundaries and step by `frame_count`, not emulator ticks. PyBoy's hook_register misses ~1 in 10 hits.
- Banks: bank 1 is mapped by default (graphics, screens, palettes, sfx, save). Every hUGEDriver call
  (`hUGE_init`, `hUGE_dosound`, `hUGE_mute_channel`) must be wrapped in `SWITCH_ROM(2)` / `SWITCH_ROM(1)`;
  a call with bank 1 mapped executes tile data as code and corrupts RAM. Only bank-0 code may switch banks.
- Sound: `music_update()` runs in VBlank; sfx.c mutes the driver's channel for the effect's length via
  `music_sfx_hold()`. hUGE note 0 is C2 (65 Hz) on the pulse channels. The wave channel plays a
  one-cycle waveform an octave low (note 0 is C1), which the gameplay bass needs to reach A1/G1; the
  older songs still use a two-cycle wave at pulse pitch.
- The GB runs at 59.73 fps, so the port plays 0.45% slower than the original (inaudible). Correct for
  it (resample by 60/59.7275) before comparing a render with the original row by row, or the drift
  of 1.6 rows over the loop smears every per-row measurement.
- hUGE instrument ids are 1-based: the driver does `dec a` before indexing, so instrument 1 is entry [0]
  of the table. A leading "unused" row silently shifts every instrument by one - that bug had the melody
  playing a decaying 50% patch while the harmony got the loud sustained one.
- Channel 1 is the melody. No effect that fires during play may touch it, or the tune drops out for a
  third of a second every jump: gameplay effects use channel 2 (the harmony, which sounds about one row
  in seven) or channel 4. Only death and the win fanfare use channel 1, and the track is ending by then.
  Channel 2 has no hardware sweep, so `sfx_update()` walks the frequency itself once a frame, writing
  pitch without the restart bit; it clamps at a ceiling instead of sweeping into an overflow silence.
- Palette budget: BG 0/1 friendly on floor A/B, 2/3 angry+mushroom, 4/5 star pad, 6 decoration
  (ground, black, purple, light blue), 7 HUD. OBJ 0 player, 1-4 flasks, 5 shadow, 6 red oppie/pop-ups, 7 blue oppie.
- Sprite slots: 0 player (8x16, head overhangs the cell above), 1 unused, 2 shadow, 3-8 hopping enemies,
  9-14 flasks, 15-32 pop-ups (3 objects each, only as many shown as the value needs).
- Score is `uint32` end to end (state, SRAM, HUD, high-score table) and displays 8 digits, so it is exact to
  99,999,999. A kill award is `(10 + 10 x kills) x multiplier` in 32-bit: the multiplier stacks across flasks
  picked up while power is still running, so awards reach five digits. Pop-ups render up to 6 digits.
  Decimal conversion is repeated subtraction of a power of ten, never `/` or `%` on a 32-bit value, and the
  pop-up tiles are composed in phase 1 - only the VRAM copy belongs in VBlank.

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
  last shape); life 960 frames. Stars are still: the pad inverts (white cell, green star) every 20 frames in its
  last 120, and every 5 frames during the 40-frame flash after a save. Expiring unused summons (rank+1) mushrooms and a new pad. A save flashes
  the pad 40 frames, then a new pad appears. Drop (B): every trail oppie is judged at once, then resolved
  one per 10 frames: on the pad it is saved for 10 x trail position, otherwise it becomes an enemy in place.
- Flasks: counter += saved; at >= 6 the level is min(3, counter-6) and the counter resets; the flask drops
  in 60 frames later and falls 90 units; it upgrades a level every 512 frames on the floor. Pickup: 480
  frames of power, +1 multiplier for green+, mushrooms killable with blue+, gold adds a permanent loose
  oppie. Kill score (10 + 10 x kills this flask) x multiplier. Ranks at 50/100/150 saved; win at 200.
- Two loose oppies on the field, replaced immediately when collected.
- Music: gameplay loop is 44 bars at 163.6 BPM (88 frames a bar); win sting, lose sting, ending theme.
  Ending: the field fills with oppies one cell per 5 frames, four dialogue lines, credits.

## Done

Playable core on the original rules; title with menu, hoppers and high-score screen; battery-backed high
scores and stats; ending with dialogue and credits; cascading drop-off with pop-ups; death bump; start
hint; four auto-transcribed music tracks with sound effects; verified in SameBoy, mGBA and John GBC.

## Remaining features (backlog)

1. Music quality: the tracks are auto-transcribed and still approximate. The gameplay track follows
   what the original is: a 3-3-2 groove (attacks on rows 1, 4, 6 of the bar, nothing on row 5), chord
   stabs and a quiet noise tick on those accents, a bright bass whose overtones fill 160-640 Hz, and
   voices that only strike where the original strikes. No kick/snare: an imposed backbeat put the snare
   on the original's quietest row (rhythm correlation with the original went from -0.71 to 0.82, GB-render
   chroma from 0.715 to 0.746). The win/lose/ending songs were not regenerated with this transcriber
   yet. Next: melody octave choices and phrases in bars 9-44 by ear, hand-polish in src/music_data.c
2. Sound effects closer to the originals (sfx_special02 on flask, the 150/100/50 ticks, witch cackle)
3. Ending polish: the witch walking in beside the Gardener, a happy sprite, the original's credit roll timing
4. Palette fade on transitions
5. Witch animation when she spawns mushrooms; richer appear/stun frames; flash hop sprites while powered
6. Clear effect frames on the cascading drop-off (FollowClear animation)
7. The original game-over flow (60-frame bump, then the UFO 50 frame's GAME OVER card)
8. Easter eggs ("I LOVE JESCA!" after inactivity, running in circles) and the OVER-GROW cheat; tutorial
9. Remove `dbg[]` / `frame_count` diagnostics once tuning is done (the tests read `frame_count`)
