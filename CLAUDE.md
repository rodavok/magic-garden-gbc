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
~/.local/opt/pyboy-venv/bin/python tools/hw_check.py    # SameBoy: counts VRAM/palette writes real hardware drops (0 expected); run after touching render/main
SAMEBOY_BOOT=~/.local/opt/SameBoy-1.0.3/build/bin/BootROMs/cgb_boot.bin ./tools/sameboy/dump build/magicgarden.gbc "230,5:start,40,5:down,600" build/sameboy/x   # accurate headless run: PPM frames + PPU/palette/tilemap dump per step
SAMEBOY_WAV=build/sameboy/out.wav SAMEBOY_BOOT=... ./tools/sameboy/dump ...                 # same, also records the audio
~/.local/opt/pyboy-venv/bin/python tools/mgba_capture.py build/magicgarden.gbc build/mgba "4,0.3:Return,3"   # drives mGBA on DISPLAY :0
```

Gameplay song: edited as a text score, `res/music/gameplay.song` (one line per row, a column per channel;
format in the `tools/song.py` docstring). `src/music_gameplay.c` is generated from it - never edit it by hand.

```bash
python3 tools/song.py show res/music/gameplay.song 4-7          # what each channel plays in bars 4-7
~/.local/opt/pyboy-venv/bin/python tools/song_render.py         # compile score -> src/music_gameplay.c, record full + solo WAVs in SameBoy (build/song)
~/.local/opt/pyboy-venv/bin/python tools/song_page.py           # review page in build/song; serve with the "song-viewer" launch entry (port 8766)
~/.local/opt/pyboy-venv/bin/python tools/song_view.py 4 5 out.png --lo D4 --hi D6 --gamma 0 --ph 5 --px 80 [--render build/song/full.wav]   # original's piano roll with the score outlined
```

Sound effects: `~/.local/opt/pyboy-venv/bin/python tools/sfx_page.py` records every effect in `src/sfx.c` in SameBoy
(test ROM `tools/sfxtest/main.c`) and builds a board in build/sfx with the original's effect for each event beside it
(serve with the "sfx-board" launch entry, port 8767). The originals come from `tools/extract_gm.py --audio-only`.

`tools/draft_gameplay.py` wrote the first draft of the score from the OGG (it overwrites the score: don't rerun it).
What the original's gameplay track is: intro 0-3 (bass, chords and a quiet lead figure D5 C5 G4 . C5 in bar 0, C5
in bar 2) | B 4-11, B' 12-17 (= 4-9) | turnaround 18-19 | intro 20-23 (= 0-3) | C 24-31, C' 32-39 (loud 4-note
stabs around G3-A4, a bass that answers itself an octave up on rows 2 and 6, and the section's melody: a near-pure
whistle tone high up, A6 E6 B6 | G#6 A6 E7 | D7 E7 A7~ in dotted quarters played 2 rows on, 1 off, with a fast
tremolo and a scoop into each note) | outro 40-43 (C5 A#4 F4 ... C5 A#4). No percussion anywhere: CH4 is silent.
Bass strikes rows 1, 2, 5, 7 of the bar in the intro and B; chord stabs rows 0, 3, 5. In C the wave channel plays the
whistle melody as a real sine at the original's octave, level with the stabs as in the original (wave
instruments 2/4, 4- or 3-cycle per note for tuning, half-height waves). Keep it there: an octave lower it sits on the
stabs' upper harmonics, masks them, and its G#/C# against their G turn into a harsh rub that sounds like a wrong key, CH1 plays the bass (a square: a pulse
stops at C2, so bar 28's A#1 is an octave up) and CH2 carries the stabs, alternating two stab notes where there are two. A pure tone has no
harmonics to test, so look for it as a strong peak with weak 2f and 3f that no lower note explains (not the 5th/6th
harmonic of a stab note: bars 31 and 39 are rests although D4's harmonics show there). `tools/song_check.py [--bars a-b] [--lead-lo 55]` lists, per bar
and channel, what the score strikes against what attacks in the original.
The GB plays each chord as a 3-note arpeggio on CH2 (`C4^47`). In spectrogram work, CQT bin 3(m-24) is centred
on note m: grouping bins 3k..3k+2 reads a third of a semitone sharp.
The original's lead is an octave stack: f, 2f, 4f, 8f at about 0, -1.4, -5, -20 dB with almost no odd harmonics, so
its note is the bottom of the stack (a chord tone has a weak 2f and strong 3f; the bass a strong 2f and 3f). Test a
note's octave by those levels, never by the strongest peak: that is usually 2f, which read the lead an octave high.
It decays ~1 dB per 20 ms after a 40 ms hold (GB env=-1). The composer wrote echoes into it: quieter repeats of a
phrase usually 3 rows later (bar 7 repeats D5 A4 every 2 rows); the score gives them lead instruments 4-7 (vol 12-3).
Soft "lead" peaks at -18 dB exactly on the chord rows (0, 3, 5) are chord harmonics, not notes.
High notes are out of tune on the GB: pitch is an integer period, so at A6-A7 a note can be 10-20 cents off (the
pulse lead in B is fine below G5). A wave holding k sine cycles sounds k/2 x its table note (`cycles=` in the score);
a 3- and a 4-cycle wave give two period grids to pick from if a melody has to sit that high.
Fewer steps per sine cycle means brighter: 4 cycles (8 steps) put -17 dB partials at 7f and 9f, which an octave
down land at 5-8 kHz and sound harsh. Scale a wave down in the waveform itself (optimize the 4-bit shape), never
with the channel's 50/25 % volume, which drops bits and adds low harmonics.
so a 3- and a 4-cycle wave give two period grids; each high melody note uses the closer one (within 8.5 cents).
Never cut or mute a wave-channel note between phrases: its output drops from the waveform's mean (~7.5) to 0 and
thumps (-11 dB below 300 Hz); rests play a flat wave at 7 instead (`hush`, instrument 3). Measuring a GB render: scale time by
60/59.7275, don't resample - resampling shifts every pitch 7.9 cents sharp.

Regenerating the other songs (only if the transcriber or reference audio changes):

```bash
( echo '#pragma bank 2'; echo '#include "hUGEDriver.h"'; echo '#include <stddef.h>'; echo ) > src/music_data.c
for spec in "bgm27_stingWin song_win" "bgm27_stingLose song_lose" "bgm27_end song_end"; do
  set -- $spec; ~/.local/opt/pyboy-venv/bin/python tools/transcribe.py reference/audio/$1.ogg $2 /tmp/$2.c $3 $4 $5; cat /tmp/$2.c >> src/music_data.c; done
~/.local/opt/pyboy-venv/bin/python tools/eval_transcription.py   # chroma score of the transcription vs the original
```

Never run the PyBoy tests while `make` is still writing the ROM: they read a half-written file and report garbage.

## Layout

- `include/game.h` game state struct `game_t` (field order matters: `tools/gbmem.py` parses it, and `pop_t` is 7 bytes) and all tuning constants
- `src/game.c` rules; `src/render.c` BG rows/sprites/HUD/pop-ups; `src/main.c` main loop (bank 0)
- `src/screens.c` title, high scores, game start, ending (bank 1); `src/save.c` SRAM; `src/palettes.c`; `src/sfx.c` register-level effects (all bank 1)
- `src/sfx_tables.c` per-frame pickup/jump/power-up effects, generated by `tools/sfx_tables.py` (editable lists measured
  from the original's effects; never edit the .c by hand)
- `src/music.c` song control (bank 0); `src/music_gameplay.c` compiled from `res/music/gameplay.song` and `src/music_data.c`
  (win/lose/ending, auto-transcribed), both bank 2; `src/hugebank.s` bank symbols for the driver
- `tools/song.py` score parser/compiler/printer; `tools/song_render.py` music-test ROM (`tools/musictest/main.c`) + SameBoy
  recording; `tools/song_page.py` + `tools/song_page.html` review page; `tools/song_view.py` spectrogram with the score outlined
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
  by an unrolled copy into the tile map (GBDK's `set_bkg_tiles` is several times slower and overran VBlank).
  VBlank is budgeted: from line 145 it fits 4 rows (~1.3 lines each) and the bob; 2 rows beside a pop-up
  upload or the HUD; nothing beside a palette load (GBDK's waits for HBlank per byte and runs far past
  VBlank). Tile-map writes after line 153 are silently dropped on hardware and SameBoy but not in PyBoy,
  so `tools/stress_test.py` fails when the flush ends outside VBlank (dbg[3]) and `tools/hw_check.py`
  counts every dropped write in SameBoy. On a flash cart a dropped attribute write shows as a cell in the
  wrong palette (a star pad cell that stays floor-coloured) until the row is redrawn.
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
- Sound: `music_update()` / `sfx_update()` run once a frame right after the VBlank flush, never before it
  (run first, they took half of VBlank and pushed row writes into the visible frame); sfx.c mutes the driver's channel for the effect's length via
  `music_sfx_hold()`. hUGE note 0 is C2 (65 Hz) on the pulse channels. The wave channel plays a
  one-cycle waveform an octave low (note 0 is C1), which the gameplay bass needs to reach A1/G1; the
  older songs still use a two-cycle wave at pulse pitch.
- The GB runs at 59.73 fps, so the port plays 0.45% slower than the original (inaudible). Correct for
  it (resample by 60/59.7275) before comparing a render with the original row by row, or the drift
  of 1.6 rows over the loop smears every per-row measurement.
- hUGE instrument ids are 1-based: the driver does `dec a` before indexing, so instrument 1 is entry [0]
  of the table. A leading "unused" row silently shifts every instrument by one - that bug had the melody
  playing a decaying 50% patch while the harmony got the loud sustained one.
- Channel 1 is the melody. `tools/sfx_tables.py` GAIN keeps every effect under it (a 50 % pulse at 11 out-RMSes the
  12.5 % lead at 15). No effect that fires during play may touch it, or the tune drops out for a
  third of a second every jump: gameplay effects use channel 2 (the harmony, which sounds about one row
  in seven) or channel 4. Only death uses channel 1, and the track is ending by then.
  Channel 2 has no hardware sweep, so `sfx_update()` walks the frequency itself once a frame, writing
  pitch without the restart bit; it clamps at a ceiling instead of sweeping into an overflow silence.
- Palette budget: BG 0/1 friendly on floor A/B, 2/3 angry+mushroom, 4/5 star pad, 6 sidebar grove
  (ground, blue rim/skirt, tree colour, eyes; tree colour follows the rank), 7 back wall + bottom HUD (dark,
  brick grey, white, plaque colour: entry 3 is pink, or a new flask's colour while it is on its way). OBJ 0 player and jump
  shadow, 1-4 flasks, 5 cat, 6 witch, 7 blue oppie and score pop-ups (pop-ups only draw colour 2, white).
  The title screen loads its own OBJ set with the red oppie in 6.
- Sprite slots: 0 player (8x16, 14 px tall, head overhangs the cell above), 1 unused, 2 shadow, 3-8 hopping
  enemies, 9-14 flasks, 15-32 pop-ups (3 objects each, only as many shown as the value needs), 33-35 cat,
  36-39 witch (cat is 24 px wide: 3 objects). The sidebar characters take the lowest-priority slots and never share a scanline.
- Tiles: sprites and BG share VRAM bank 0 (0x8000, 256 tiles; make_art.py asserts the total). The sidebar
  grove and the bottom HUD (plaques, tall digits `B1_DIGIT`, flask meter `B1_FLASK`) are composed in
  make_art.py and cut into tiles in VRAM bank 1 (attribute bit 3). The HUD flush is straight `memcpy` into
  the tile map (attributes are static); anything that overwrites rows 15-17 restores them from `frame_map`.
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
hint; four auto-transcribed music tracks with sound effects; chibi gardener; sidebar grove like the original
(trees with faces, a cat that yawns awake when a flask is made, Cloverana zapping while a mushroom
grows and jumping when you die); bottom HUD as the original's plaques with a flask meter;
verified in SameBoy, mGBA and John GBC.

## Remaining features (backlog)

1. Music quality: the lead of bars 0-23 and 40-43 was re-derived row by row from the octave-stack signature (with
   its echoes and dynamics). Section C's whistle melody was transcribed the same way. Still from the earlier draft: chord qualities where the original plays 4-note chords, and
   the win/lose/ending songs (old auto-transcriptions in src/music_data.c).
2. Sound effects closer to the originals (sfx_special02 on flask, the 150/100/50 ticks, witch cackle)
3. Ending polish: the witch walking in beside the Gardener, a happy sprite, the original's credit roll timing
4. Palette fade on transitions
5. Richer appear/stun frames; flash hop sprites while powered; the cat's slow breathing
6. Clear effect frames on the cascading drop-off (FollowClear animation)
7. The original game-over flow (60-frame bump, then the UFO 50 frame's GAME OVER card)
8. Easter eggs ("I LOVE JESCA!" after inactivity, running in circles) and the OVER-GROW cheat; tutorial
9. Remove `dbg[]` / `frame_count` diagnostics once tuning is done (the tests read `frame_count`)
