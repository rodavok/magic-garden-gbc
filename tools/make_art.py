#!/usr/bin/env python3
"""Generates GBC tile data + static tile maps for Magic Garden.
Writes src/gfx_data.c and include/gfx_data.h. Pixel art is authored inline as strings.
Index legend for BG object tiles: '.'=0 (floor/background), 'w'=1 white, 'k'=2 black, 'c'=3 colour.
"""
import os
ROOT = os.path.join(os.path.dirname(__file__), '..')
CH = {'.': 0, 'w': 1, 'k': 2, 'c': 3, '1': 1, '2': 2, '3': 3, '0': 0}

def tile2bpp(rows):
    assert len(rows) == 8, rows
    out = []
    for r in rows:
        assert len(r) == 8, r
        lo = hi = 0
        for x, ch in enumerate(r):
            v = CH[ch]
            lo |= (v & 1) << (7 - x); hi |= ((v >> 1) & 1) << (7 - x)
        out += [lo, hi]
    return out

def hflip(rows): return [r[::-1] for r in rows]

# ------------------------------------------------------------------ sprites (OBJ, 8x16 mode)
# Gardener: 1 = dark hair/outline, 2 = purple dress, 3 = white/skin
GARDENER = {
'down0': """
..1111..
.111111.
11111111
11333311
11313311
.133331.
..3333..
.222222.
12222221
12222221
.222222.
.222222.
..2222..
..3..3..
..1..1..
.11..11.
""",
'down1': """
..1111..
.111111.
11111111
11333311
11313311
.133331.
..3333..
.222222.
12222221
12222221
.222222.
.222222.
..2222..
..3..3..
..11....
.111.11.
""",
'up0': """
..1111..
.111111.
11111111
11111111
11111111
.111111.
..3333..
.222222.
12222221
12222221
.222222.
.222222.
..2222..
..3..3..
..1..1..
.11..11.
""",
'up1': """
..1111..
.111111.
11111111
11111111
11111111
.111111.
..3333..
.222222.
12222221
12222221
.222222.
.222222.
..2222..
..3..3..
....11..
.11.111.
""",
'left0': """
..1111..
.111111.
11111111
11113311
11111311
.111331.
..3333..
.222222.
.222222.
.222222.
.222222.
.222222.
..2222..
..3.3...
..1.1...
.11.11..
""",
'left1': """
..1111..
.111111.
11111111
11113311
11111311
.111331.
..3333..
.222222.
.222222.
.222222.
.222222.
.222222.
..2222..
..3.3...
.1...1..
11..11..
""",
'spin': """
..1111..
.111111.
11111111
11111111
11111111
.111111.
..3333..
.222222.
22222222
22222222
22222222
.222222.
..2222..
..3..3..
..1..1..
.11..11.
""",
}
# Flask (bottom 8 rows of an 8x16 OBJ; top is blank): 1 = dark, 2 = colour, 3 = white
FLASK = """
...33...
...22...
..2222..
.223222.
.232222.
.222222.
..2112..
..1111..
"""
SHADOW = """
........
........
........
........
........
..1111..
.111111.
........
"""
SCOREPOP = None  # v2

def rows(s): return [l for l in s.strip('\n').split('\n')]

sprite_tiles = []   # list of (name, 16 rows)
def add_sprite(name, r16):
    assert len(r16) == 16, (name, len(r16))
    sprite_tiles.append((name, r16))
for k in ('down0','down1','up0','up1','left0','left1','spin'):
    add_sprite('SPR_' + k.upper(), rows(GARDENER[k]))
add_sprite('SPR_RIGHT0', hflip(rows(GARDENER['left0'])))
add_sprite('SPR_RIGHT1', hflip(rows(GARDENER['left1'])))
add_sprite('SPR_FLASK', ['........']*8 + rows(FLASK))
add_sprite('SPR_SHADOW', ['........']*8 + rows(SHADOW))

# ------------------------------------------------------------------ BG tiles
bg = []  # (name, 8 rows)
def T(name, s): bg.append((name, rows(s)))

T('T_FLOOR', """
........
........
........
........
........
........
........
........
""")
T('T_STAR', """
...w....
...w....
.wwwww..
..www...
..www...
.w...w..
........
........
""")
OPPIE = """
..cccc..
.cccccc.
cccccccc
cwwccwwc
cwkccwkc
cccccccc
.cccccc.
........
"""
T('T_OPPIE', OPPIE)
T('T_OPPIE_HAPPY', """
..cccc..
.cccccc.
cccccccc
ckccckcc
cckcccck
cccccccc
.cccccc.
........
""")
T('T_OPPIE_LOOK_L', """
..cccc..
.cccccc.
cccccccc
wwccwwcc
kwcckwcc
cccccccc
.cccccc.
........
""")
T('T_OPPIE_LOOK_U', """
..cccc..
.cwwcww.
cwkccwkc
cccccccc
cccccccc
cccccccc
.cccccc.
........
""")
T('T_OPPIE_LOOK_D', """
..cccc..
.cccccc.
cccccccc
cccccccc
cwwccwwc
cwkccwkc
.cccccc.
........
""")
T('T_OPPIE_STUN', """
..cccc..
.cccccc.
cwwccwwc
wkwcwkwc
wwwcwwwc
cccccccc
.cccccc.
........
""")
T('T_APPEAR0', """
........
........
........
........
........
...cc...
..cccc..
........
""")
T('T_APPEAR1', """
........
........
........
........
..cccc..
.cccccc.
.cccccc.
........
""")
T('T_APPEAR2', """
........
........
..cccc..
.cccccc.
cwwccwwc
cccccccc
.cccccc.
........
""")
T('T_MUSH', """
..cccc..
.cwcccw.
cccccccc
ccccwccc
.wwwwww.
..wkkw..
..wwww..
........
""")
T('T_MUSH_APPEAR', """
........
........
........
........
..cccc..
.cccccc.
..wwww..
........
""")
# --- frame / HUD tiles. Palette P7 (HUD): 0 = dark grey, 1 = light grey, 2 = white, 3 = pink
T('T_BRICK', """
11111111
10001000
11111111
01000100
11111111
10001000
11111111
01000100
""")
T('T_BRICK_BOTTOM', """
11111111
10001000
11111111
00000000
00000000
00000000
00000000
00000000
""")
T('T_WINDOW', """
11111111
10022000
10222200
02222220
02222220
02222220
02222220
11111111
""")
T('T_PANEL', """
33333333
33333333
33333333
33333333
33333333
33333333
33333333
33333333
""")
T('T_PANEL_EDGE_L', """
23333333
23333333
23333333
23333333
23333333
23333333
23333333
23333333
""")
T('T_PANEL_EDGE_R', """
33333332
33333332
33333332
33333332
33333332
33333332
33333332
33333332
""")
T('T_DOT_OFF', """
........
........
...11...
..1..1..
..1..1..
...11...
........
........
""")
T('T_DOT_ON', """
........
........
...33...
..3333..
..3333..
...33...
........
........
""")
T('T_BLACK', """
00000000
00000000
00000000
00000000
00000000
00000000
00000000
00000000
""")
# --- decoration, palette P6: 0 = black, 1 = dark green, 2 = purple, 3 = light blue
T('T_GRASS', """
11111111
11111111
11111111
11111111
11111111
11111111
11111111
11111111
""")
TREE = [
"""
..222222
.2222222
22222222
22222222
22222222
22233222
22232222
22233222
""","""
222222..
2222222.
22222222
22222222
22222222
22332222
22322222
22332222
""","""
22222222
22222222
.2222222
..222222
...22222
1111.222
1111..22
11111111
""","""
22222222
22222222
2222222.
222222..
22222...
222.1111
22..1111
11111111
"""]
for i, t in enumerate(TREE): T('T_TREE%d' % i, t)
# Cat (HUD palette P7: 0 dark grey,1 light grey,2 white,3 pink) drawn as a pink cat, 3x2 tiles
CAT = [
"""
........
.3....3.
.33..33.
.333333.
.323323.
.333333.
.333333.
..3333..
""","""
........
........
........
33333333
33333333
33333333
33333333
33333333
""","""
........
........
....33..
...333..
..3333..
33333333
33333333
33333333
""","""
..3333..
.333333.
.333333.
.333333.
.333333.
..3333..
........
........
""","""
33333333
33333333
33333333
33333333
33333333
.333333.
........
........
""","""
33333333
33333333
33333333
33333333
33333333
.333333.
........
........
"""]
for i, t in enumerate(CAT): T('T_CAT%d' % i, t)
# Witch (P6: 0 black, 1 dark green, 2 purple, 3 light blue) 2x3 tiles
WITCH = [
"""
......3.
.....33.
....333.
...3333.
..33333.
.333333.
33333333
...33...
""","""
........
........
........
........
........
........
33......
........
""","""
..3333..
.333333.
.303303.
.333333.
..3333..
.323323.
.323323.
32222223
""","""
........
........
........
........
...3....
...3....
...3....
...3....
""","""
32222223
.222222.
.222222.
.222222.
..2222..
..3..3..
..3..3..
.33..33.
""","""
...3....
...3....
...3....
...3....
........
........
........
........
"""]
for i, t in enumerate(WITCH): T('T_WITCH%d' % i, t)

# --- font: 1 = white (index 1 in HUD palette is light grey; use index 2 for white)
FONT = {
'0': ["01110","10001","10011","10101","11001","10001","01110"],
'1': ["00100","01100","00100","00100","00100","00100","01110"],
'2': ["01110","10001","00001","00010","00100","01000","11111"],
'3': ["11111","00010","00100","00010","00001","10001","01110"],
'4': ["00010","00110","01010","10010","11111","00010","00010"],
'5': ["11111","10000","11110","00001","00001","10001","01110"],
'6': ["00110","01000","10000","11110","10001","10001","01110"],
'7': ["11111","00001","00010","00100","01000","01000","01000"],
'8': ["01110","10001","10001","01110","10001","10001","01110"],
'9': ["01110","10001","10001","01111","00001","00010","01100"],
'A': ["01110","10001","10001","11111","10001","10001","10001"],
'B': ["11110","10001","10001","11110","10001","10001","11110"],
'C': ["01110","10001","10000","10000","10000","10001","01110"],
'D': ["11100","10010","10001","10001","10001","10010","11100"],
'E': ["11111","10000","10000","11110","10000","10000","11111"],
'F': ["11111","10000","10000","11110","10000","10000","10000"],
'G': ["01110","10001","10000","10111","10001","10001","01111"],
'H': ["10001","10001","10001","11111","10001","10001","10001"],
'I': ["01110","00100","00100","00100","00100","00100","01110"],
'J': ["00111","00010","00010","00010","00010","10010","01100"],
'K': ["10001","10010","10100","11000","10100","10010","10001"],
'L': ["10000","10000","10000","10000","10000","10000","11111"],
'M': ["10001","11011","10101","10101","10001","10001","10001"],
'N': ["10001","10001","11001","10101","10011","10001","10001"],
'O': ["01110","10001","10001","10001","10001","10001","01110"],
'P': ["11110","10001","10001","11110","10000","10000","10000"],
'Q': ["01110","10001","10001","10001","10101","10010","01101"],
'R': ["11110","10001","10001","11110","10100","10010","10001"],
'S': ["01111","10000","10000","01110","00001","00001","11110"],
'T': ["11111","00100","00100","00100","00100","00100","00100"],
'U': ["10001","10001","10001","10001","10001","10001","01110"],
'V': ["10001","10001","10001","10001","10001","01010","00100"],
'W': ["10001","10001","10001","10101","10101","10101","01010"],
'X': ["10001","10001","01010","00100","01010","10001","10001"],
'Y': ["10001","10001","01010","00100","00100","00100","00100"],
'Z': ["11111","00001","00010","00100","01000","10000","11111"],
'-': ["00000","00000","00000","11111","00000","00000","00000"],
'!': ["00100","00100","00100","00100","00100","00000","00100"],
'.': ["00000","00000","00000","00000","00000","01100","01100"],
"'": ["01100","00100","01000","00000","00000","00000","00000"],
',': ["00000","00000","00000","00000","00000","01100","00100"],
'x': ["00000","00000","10001","01010","00100","01010","10001"],
' ': ["00000"]*7,
}
FONT_ORDER = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-!.',x "
font_first = len(bg)
for ch in FONT_ORDER:
    g = FONT[ch]
    r = ['.' + ''.join('2' if b == '1' else '.' for b in row) + '..' for row in g] + ['........']
    bg.append(('T_FONT_' + str(ord(ch)), r))

# ------------------------------------------------------------------ indices
SPR_BASE = 0                              # OBJ tiles 0..(2*len-1)
BG_BASE = 2 * len(sprite_tiles)           # BG tiles follow sprite tiles in the shared 0x8000 space
BG_BASE = (BG_BASE + 1) & ~1
names = {n: BG_BASE + i for i, (n, _) in enumerate(bg)}
assert BG_BASE + len(bg) <= 256, (BG_BASE, len(bg))

# ------------------------------------------------------------------ static frame map (20x18)
W, H = 20, 18
tmap = [[names['T_BLACK']] * W for _ in range(H)]
amap = [[7] * W for _ in range(H)]        # palette index per tile
P_HUD, P_DECO = 7, 6
def put(x, y, name, pal, flip=0):
    tmap[y][x] = names[name]; amap[y][x] = pal | flip
# top wall rows 0-2
for x in range(W):
    put(x, 0, 'T_BRICK', P_HUD); put(x, 1, 'T_BRICK', P_HUD); put(x, 2, 'T_BRICK_BOTTOM', P_HUD)
for x in (2, 5, 14, 17): put(x, 1, 'T_WINDOW', P_HUD)
# timer emblem (panel) at cols 8-11 rows 0-2 ; digits drawn at runtime at (9,1),(10,1)
for x in range(8, 12):
    for y in range(0, 3): put(x, y, 'T_PANEL', P_HUD)
put(8, 1, 'T_PANEL_EDGE_L', P_HUD); put(11, 1, 'T_PANEL_EDGE_R', P_HUD)
# side columns rows 3-14: grass + trees, cat left, witch right
for y in range(3, 15):
    for x in list(range(0, 4)) + list(range(16, 20)):
        put(x, y, 'T_GRASS', P_DECO)
def tree(x, y):
    put(x, y, 'T_TREE0', P_DECO); put(x+1, y, 'T_TREE1', P_DECO)
    put(x, y+1, 'T_TREE2', P_DECO); put(x+1, y+1, 'T_TREE3', P_DECO)
tree(0, 3); tree(2, 4); tree(0, 12); tree(2, 13)
tree(16, 3); tree(18, 4); tree(16, 12); tree(18, 13)
# cat at left (cols 0-2, rows 8-9); bubble dots drawn at runtime on row 7 cols 0-4? (we use bottom HUD instead)
for i in range(3): put(i, 8, 'T_CAT%d' % i, P_HUD); put(i, 9, 'T_CAT%d' % (i+3), P_HUD)
# witch at right (cols 17-18, rows 7-9)
for i in range(3): put(17, 7+i, 'T_WITCH%d' % (2*i), P_DECO); put(18, 7+i, 'T_WITCH%d' % (2*i+1), P_DECO)
# playfield cols 4-15 rows 3-14: floor checker (palettes 0/1), overwritten at runtime
for y in range(12):
    for x in range(12):
        put(4+x, 3+y, 'T_FLOOR', (x + y) & 1)
# bottom HUD rows 15-17: pink panel
for x in range(W):
    for y in range(15, 18): put(x, y, 'T_PANEL', P_HUD)
def text(x, y, s):
    for i, ch in enumerate(s): put(x+i, y, 'T_FONT_' + str(ord(ch)), P_HUD)
text(1, 15, 'SAVED'); text(12, 15, 'SCORE')
for i in range(5): put(7+i, 17, 'T_DOT_OFF', P_HUD)

# ------------------------------------------------------------------ emit
os.makedirs(os.path.join(ROOT, 'include'), exist_ok=True)
h = ['// Generated by tools/make_art.py - do not edit', '#ifndef GFX_DATA_H', '#define GFX_DATA_H', '#include <stdint.h>', '']
for i, (n, _) in enumerate(sprite_tiles): h.append(f'#define {n} {2*i}')
h.append(f'#define SPR_TILE_COUNT {2*len(sprite_tiles)}')
h.append(f'#define BG_BASE {BG_BASE}')
for n, v in names.items(): h.append(f'#define {n} {v}')
h.append(f'#define BG_TILE_COUNT {len(bg)}')
h.append(f'#define FONT_FIRST {BG_BASE + font_first}')
h.append('#define FONT_ORDER "' + FONT_ORDER.replace('\\', '\\\\').replace('"', '\\"') + '"')
h += ['', 'extern const uint8_t spr_tiles[];', 'extern const uint8_t bg_tiles[];',
      'extern const uint8_t frame_map[20*18];', 'extern const uint8_t frame_attr[20*18];', '', '#endif']
open(os.path.join(ROOT, 'include', 'gfx_data.h'), 'w').write('\n'.join(h) + '\n')

def carr(name, data):
    lines = [f'const uint8_t {name}[] = {{']
    for i in range(0, len(data), 16):
        lines.append('    ' + ', '.join('0x%02X' % b for b in data[i:i+16]) + ',')
    lines.append('};')
    return '\n'.join(lines)
spr = []
for n, r16 in sprite_tiles: spr += tile2bpp(r16[:8]) + tile2bpp(r16[8:])
bgd = []
for n, r in bg: bgd += tile2bpp(r)
c = ['// Generated by tools/make_art.py - do not edit', '#include <stdint.h>', '#include "gfx_data.h"', '',
     carr('spr_tiles', spr), '', carr('bg_tiles', bgd), '',
     carr('frame_map', [t for row in tmap for t in row]), '',
     carr('frame_attr', [a for row in amap for a in row])]
open(os.path.join(ROOT, 'src', 'gfx_data.c'), 'w').write('\n'.join(c) + '\n')
print(f'sprite tiles: {2*len(sprite_tiles)}  bg tiles: {len(bg)}  BG_BASE={BG_BASE}  total={BG_BASE+len(bg)}')
