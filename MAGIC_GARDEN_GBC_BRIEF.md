# Magic Garden (UFO 50) → Game Boy Color port: development brief

Compiled 2026-09-17 from the UFO 50 wiki (Miraheze + Fandom), the Steam "Magic Garden rules?" thread,
the UFO 50 Diaries write-up, Spriters Resource, Pan Docs, and GBDK-2020 / hUGEDriver docs.
Reference screenshots: `reference/gameplay.png` (1920x1080, 5x scale of 384x216 native) and `reference/title.png`.

---

## 1. The source game

### 1.1 Facts
| Item | Value |
|---|---|
| Position in UFO 50 | #5, "CUTE.UFO", fictional release Feb 1984 on the fictional LX-II |
| Genre | Single-player arcade; Snake meets Pac-Man |
| Native resolution | 384 x 216 (UFO 50 standard) |
| Playfield | 12 x 12 grid, 16 px cells = 192 x 192 px, centred, top edge at y=24 |
| Real credits | Design: Mossmouth (fictional: Benedikt Chun). Music: Eirik Suhrke |
| Music tracks | "Gameplay" (2:24 loop), "Clear" (0:14), "Ending" (0:49) |
| Cheat (terminal code) | `OVER-GROW` = no potions spawn |
| Stats tracked | Biggest Drop Off, Most Enemies Cleared at Once, Most Enemies Cleared Total |

### 1.2 Premise and cast
Stop the jealous witch **Cloverana** from sabotaging your garden. The player character is an unnamed girl
(community name "the Gardener"): dark bob haircut, purple dress, white socks, purple boots.
Cloverana: blue skin, blue witch hat and dress, wand. She stands at the right edge of the playfield during play.
A sleeping orange cat sits at the left edge and shows the flask counter in a speech bubble.

### 1.3 Controls
| Input | Action |
|---|---|
| D-pad | Turn the Gardener (she never stops moving). Cannot reverse 180°, even with no trail. |
| Button 1 (B in UFO 50 default) | Spin and **drop the whole trail** on the current tile |
| Button 2 (A) | **Jump**: hops over the next tile's contents if timed right. Window varies by object type. |

### 1.4 Rules
**Movement.** Gardener moves continuously along the grid in one of four directions. Touching the outer wall,
her own trail, an angry oppie, or a mushroom = game over (single life; the run is over). Input latency /
tight turn timing is part of the intended feel.

**Friendly oppies (red).** Loose ones sit on the grid; walk over one to collect it. Collected oppies follow in a
trail (Snake). The trail is an obstacle. A gold flask permanently adds +1 to the number of loose friendly
oppies kept on the field (base count unconfirmed; screenshot shows 2 loose reds with 12 saved).

**Star pads.** In the screenshot the pad is an entire grid row of 12 stars (row index 1). The pad
"periodically changes location" (Substack review). Exact cadence/trigger unknown.

**Dropping.** Press drop while standing on a star pad → every oppie in the trail is **saved**.
Press drop anywhere else → every trailing oppie becomes an **angry oppie** (blue, "bloppy") in place.

**Angry oppies (blue).** Spawn slowly on their own over time (independent of player action) and are also
created by bad drops. They hop one tile at a time, slowly; they visibly "look" toward the target tile before
hopping. If the target tile holds the trail or a loose friendly oppie they pick another direction. Jumping over
one stuns it for several seconds (stunned sprite has spiral eyes). Lethal on contact unless powered up.

**Mushrooms.** If the player goes too long without saving oppies at a star pad, Cloverana spawns a mushroom
(stationary obstacle). Later in the run she spawns 2, then 3 at a time. Only a blue or gold flask lets you
remove mushrooms (Steam thread confirms green does NOT).

**Flasks / potions.**
- Flask counter (cat's speech bubble, 5 dots visible = 0..5) increments by the number of oppies saved.
  At 6 it resets and one flask spawns. Extra oppies in the same drop raise the flask's level by one per extra
  oppie (9+ in one drop = gold immediately). Overflow carries? Unconfirmed.
- Levels: Red → Green → Blue → Gold. A flask left on the field slowly upgrades toward gold on its own.
- Walking onto a flask consumes it: powered-up state, timer shown top-centre counting down from 48
  (ticks much faster than 1/sec, exact rate unknown). While powered up, walking into angry oppies (and
  mushrooms with blue/gold) destroys them.
- Picking up another flask while powered up resets the timer to 48. Green/blue/gold also add +1 to the
  score multiplier. Multiplier and kill-chain reset when the timer expires.
- Gold additionally adds one permanent loose friendly oppie to the field.

| Flask | Raises multiplier | Kills mushrooms | Extra |
|---|---|---|---|
| Red | no | no | |
| Green | yes | no | |
| Blue | yes | yes | |
| Gold | yes | yes | +1 permanent friendly oppie on field |

**Scoring.**
- Saved oppie = 10 x its position in the trail (1st = 10, 2nd = 20 ...). Saving N at once = 10 x N(N+1)/2.
- Kill chain: 1st kill 10, 2nd 20, 3rd 30 ... each multiplied by the current multiplier (e.g. 2 x 30 = 60).
  Chain and multiplier reset when the flask timer runs out.
- High-score table shown after each run (no completed/failed marker).

**Progression / end.**
- Palette swap every 50 saved (4 palettes total: 0-49, 50-99, 100-149, 150-199).
- Difficulty ramps via more simultaneous mushroom spawns (and presumably angry-oppie spawn rate).
- Run ends (win) at 200 saved regardless of score. Ending cutscene: Gardener talks to Cloverana.
  Dialogue: "PLEASE DON'T BE JEALOUS OF ME. WE NEED TO HELP EACH OTHER, NOT TEAR EACH OTHER DOWN.
  I CAN TEACH YOU HOW TO GROW A WONDERFUL GARDEN OF YOUR OWN!" / "CLOVERANA: YOU'RE RIGHT... THANK YOU!"
- Goals: Gold = save 200. Cherry = 20,000+ points AND 200 saved in one run. Gift = save 10+ at once.

**Easter eggs.** "I LOVE JESCA!" appears after long inactivity; running in circles prints a message in the
SAVED box.

### 1.5 Screen layout (from `reference/gameplay.png`, native 384x216)
- Top strip (y 0-24): grey stone wall with arched windows; centre emblem panel = flask timer display.
- Playfield (x 96-288, y 24-216): 12x12 checkerboard, two greens + two oranges (the 4 tile colours alternate
  in a 2x2 checker, with a darker left column and lighter right column variation). Star pad row is bright
  green with white stars.
- Left/right playfield borders: cyan/orange triangle pattern strips (16 px wide).
- Left panel: "Saved" box (pink frame, blue ornament, white digits), cat + bubble with 5 dots.
- Right panel: "Score" box, Cloverana standing on black ground under bat silhouettes.
- Decorative purple/blue round trees fill the rest.
- Screenshot palette = 18 unique colours (this is one of 4 palettes).

### 1.6 Sprite sizes (native pixels)
| Object | Size | Notes |
|---|---|---|
| Gardener | 16 w x ~30 h | Tall character, overhangs the cell above; idle/walk/happy/sad/drop-off anims |
| Friendly / angry oppie | 16 x 16 | Blob with eyes; angry has "looking" and "stunned" frames |
| Mushroom | 16 x 16 | Scared / appearing frames |
| Flask | 16 x 16 | 4 colours, animated |
| Star pad tile | 16 x 16 | |
| Cloverana | ~32 x 48 | Walk/jump/cast/yawn anims (side panel only) |
Spriters Resource sheet: 159 files, prefix `s27_`, by MightyKingJoker (2024-10-04). All Mossmouth-copyrighted.

### 1.7 Local copy of the game
UFO 50 is installed at `~/.steam/debian-installation/steamapps/common/UFO 50/` (GameMaker: `data.win`
54.8 MB, `Textures/`, `audiogroup_bgm*.dat`). Sprites/sounds could be extracted for reference with
UndertaleModTool (needs .NET) or a small Python data.win parser (SPRT/TPAG/TXTR chunks).

### 1.8 Unknowns (not documented anywhere I found)
- Movement speed (frames per cell) and whether it ramps up.
- Angry-oppie passive spawn interval; hop interval; stun duration; whether they can hop diagonally (assume no).
- Starting number of loose friendly oppies; respawn rule after a pickup.
- Star-pad relocation rule (timer? after each save? row only, or column too?).
- Mushroom spawn timer length; whether a good save resets it.
- Flask timer tick rate (48 units in how many frames?); flask self-upgrade interval.
- Jump: duration, per-object timing windows, whether you can jump the wall.
- Whether the flask counter overflow (e.g. 8 saved from 4) spawns a green flask and keeps 2, or discards.
- What each of the 4 palettes looks like (only palette 1 seen).

---

## 2. Game Boy Color hardware constraints

| Item | Value | Consequence for this port |
|---|---|---|
| CPU | Sharp SM83 (8080-like), 4.19 MHz, 8.39 MHz double-speed | Plenty for a grid game; enable double speed anyway |
| Screen | 160 x 144, 59.73 Hz | Original 384x216 must be re-laid-out (see §4) |
| Tiles | 8x8, 2 bpp; 2 VRAM banks x 384 tiles (256 BG-addressable + 128 shared) | |
| BG | 32x32 tile map (256x256), scrollable; per-tile attribute: palette 0-7, bank, flip, priority | |
| Window | second layer, fixed offset, good for a HUD | |
| Sprites (OBJ) | 40 total, **10 per scanline**, 8x8 or 8x16, 3 colours + transparent, 8 OBJ palettes | Trail of up to 12 oppies in one row cannot be sprites → grid objects go on the BG |
| Palettes | 8 BG x 4 colours, 8 OBJ x 3 colours, 15-bit RGB (32,768) | Original has ~18 colours per palette set; 4 palette sets fit fine. LCD colours are dim: boost saturation |
| RAM | 32 KiB WRAM (8 KiB fixed + 7 banks), 127 B HRAM | 12x12 grid state is tiny |
| VRAM writes | Only during VBlank / HBlank / LCD off on real hardware | Batch tile-map updates in VBlank; emulators are lenient, hardware is not |
| Sound | 2 pulse (duty, envelope, sweep on ch1), 1 wave (4-bit, 32 samples), 1 noise; stereo panning | hUGETracker/hUGEDriver |
| Cart | MBC5 recommended (up to 8 MB ROM, 128 KiB SRAM), battery SRAM for high scores | 32-64 KiB ROM is enough; 8 KiB SRAM |
| Boot ROM | Verifies Nintendo logo bytes and header checksum (0x014D); global checksum NOT verified by hardware | rgbfix / makebin handle both |
| CGB flag | 0x80 = CGB enhanced, DMG compatible; 0xC0 = CGB only (hardware treats both the same) | Choose whether to support DMG (see questions) |
| Header title | 15 chars max when CGB flag set (11 with manufacturer code) | e.g. "MAGIC GARDEN" |

Other real-hardware rules of thumb: initialise CGB palettes with LCD off or in VBlank; wait for VBlank
before touching OAM/VRAM; don't rely on uninitialised RAM (SameBoy randomises it, hardware varies);
avoid DMG-specific palette assumptions; test the ROM in SameBoy (most accurate) and mGBA before flashing.

---

## 3. Toolchain (all free, Linux x86_64)

| Tool | Version / source | Purpose |
|---|---|---|
| **GBDK-2020** | 4.5.0 (2025-12-28), `gbdk-linux64.tar.gz`, 6.9 MB, github.com/gbdk-2020/gbdk-2020 | C compiler (SDCC), `lcc` driver, GB libraries, `png2asset`, `makebin`, `gbcompress` (zx0) |
| RGBDS | v1.0.3 (2026-08-01), github.com/gbdev/rgbds | Assembly alternative; `rgbfix` for header fixing (not needed if using lcc/makebin) |
| **hUGEDriver + hUGETracker** | public domain, github.com/SuperDisk/hUGEDriver | Music/SFX driver; tracker exports `.c` song data; call `hUGE_init()` once, `hUGE_dosound()` every VBlank |
| SameBoy | not in apt; AppImage / build from source | Most accurate emulator (hardware-verified) |
| mGBA | apt `mgba-sdl` / `mgba-qt` 0.10.2 (needs sudo) or AppImage | Second emulator; debugger |
| Emulicious / BGB | Java / Wine | Optional debuggers with VRAM viewers |
| Pillow 10.2, pypng | already installed | Asset pre-processing (palette reduction, scaling) |
| Flash cart | Any flash cart with MBC5 support | Running on real GBC |

Nothing GB-specific is installed on this machine yet (checked: no lcc, rgbasm, sameboy, mgba; sudo needs a
password). GBDK-2020 installs by untarring into a user directory, no root needed.

### 3.1 Build command (CGB, MBC5 + battery SRAM)
```
lcc -Wa-l -Wl-m -Wl-j \
    -Wm-yc            # CGB compatible (0x80); use -Wm-yC for CGB-only (0xC0)
    -Wm-yt0x1B        # MBC5+RAM+BATTERY
    -Wm-ya1           # 1 RAM bank (8 KiB) for high scores
    -Wm-yn"MAGICGARDEN" \
    -Wl-yo4           # 4 ROM banks = 64 KiB (grow if needed; -autobank for auto assignment)
    -o magicgarden.gbc src/*.c res/*.c hUGEDriver.o
```
`makebin` (invoked by lcc) writes the Nintendo logo, header checksum and global checksum.

### 3.2 png2asset key options
`-spr8x16` (or `-sprite_size 8 16`), `-bpp 2`, `-max_palettes 8`, `-keep_palette_order` (indexed PNGs with
palettes laid out in groups of 4), `-map` (tile map + tileset), `-use_map_attributes` (CGB palette/bank/flip
attributes), `-noflip`, `-tiles_only`, `-c out.c`, `-b <bank>`.

---

## 4. Proposed port design (to be confirmed)

### 4.1 Layout: 160x144
The original playfield is 44% of the screen width; a 12x12 grid of **8x8 cells = 96x96** keeps that proportion
and lines up with hardware BG tiles. Option B is **12x12 cells = 144x144** filling the height with a 16 px
side column for HUD; it looks bigger but misaligns with 8 px tiles, forcing every grid object to be a sprite
and breaking the 10-sprites-per-line limit with long trails. Recommendation: **8 px cells**, playfield at
x=32..128, y=24..120, with 8x8 oppies and a 8x16 Gardener sprite that overhangs one cell upward like the original.

Around it: Saved (left top), Score (right top), cat + 5-dot flask counter (left), flask timer (top centre),
Cloverana (right), tree decorations, using the Window layer or plain BG tiles for the HUD text.

### 4.2 Rendering strategy
- Everything grid-locked (loose oppies, trail segments, angry oppies, mushrooms, flasks, star pad) is drawn as
  BG tiles; the tile map for the 12x12 area is rebuilt from the grid state during VBlank each frame
  (144 bytes + 144 attribute bytes, well within budget, or diff-based).
- Sprites are used for: the Gardener (2-4 OBJs), the jump arc, an angry oppie mid-hop, the drop "spin" and
  score pop-ups. Never more than a handful per scanline.
- Movement: the Gardener and trail advance one cell per N frames (classic Snake step) with the Gardener
  sprite interpolated between cells for smoothness; the trail can be stepped (BG) since it is cell-based.
  N is tunable (e.g. 12 frames/cell at 60 Hz = 5 cells/s) once we know the original speed.
- Palette sets: 4 x (8 BG + 8 OBJ palettes) in ROM, swapped at 50/100/150 saved.
- High scores: 8 KiB battery SRAM (5 entries + stats: biggest drop-off, most cleared at once, most cleared total).
- Sound: hUGEDriver; original tunes re-arranged for 2 pulse + wave + noise, or new music.
- Ending: text box dialogue between Gardener and Cloverana, then credits.

### 4.3 Memory/ROM estimate
32 KiB ROM is probably enough for code + tiles + one song; 64 KiB (MBC5, 4 banks) gives comfortable room for
3 songs, 4 palette sets, title/ending art. RAM use < 2 KiB.

---

## 5. Sources
- https://ufo50.miraheze.org/wiki/Magic_Garden (CC BY-SA 4.0)
- https://ufo50.fandom.com/wiki/Magic_Garden
- https://steamcommunity.com/app/1147860/discussions/0/4638240774905961302/
- https://staticcanvas.substack.com/p/the-ufo-50-diaries-magic-garden
- https://www.spriters-resource.com/pc_computer/ufo50/sheet/240512/
- https://ufo50.miraheze.org/wiki/Cheats
- https://gbdev.io/pandocs/Specifications.html , https://gbdev.io/pandocs/The_Cartridge_Header.html
- https://github.com/gbdk-2020/gbdk-2020/releases/tag/4.5.0 , http://gbdk.org/docs/api/docs_toolchain.html
- https://github.com/SuperDisk/hUGEDriver , https://github.com/gbdev/rgbds
- https://vgmdb.net/album/143175 (soundtrack track list)
