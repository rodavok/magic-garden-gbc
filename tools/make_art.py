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
# Gardener, 8x16 (one OBJ): feet in her cell, head overhanging the cell above.
# 1 = dark purple (hair/outline/boots), 2 = purple dress, 3 = white (face, collar, socks).
# Four walk frames per direction: legs and arms only, no vertical bob.
HEAD = {    # 7 rows. The original is 2/3 hair and 1/3 face; the bob closes under the chin, so the white
            # face never touches the white of the hands. The face is an oval - narrow forehead and chin
            # rows, wide eye rows - so the 1x2 eye bars read as eyes instead of as stripes.
 'down': ["..1111..", ".111111.", "11333311", "13133131", "13133131", ".133331.", "..1111.."],
 'up':   ["..1111..", ".111111.", "11111111", "11111111", "11111111", ".111111.", "..1111.."],
 # side: face on the left, bob-cut hair falling to the shoulder on the right
 'left': ["..1111..", ".111111.", "11331111", "13131111", "13131111", ".1331111", "..11111."],
}
TORSO = {   # 5 rows: collar, arms x2, waist, hem (arm and hem rows are patched per frame)
 'down': [".222222.", "32222223", "32222223", ".222222.", "22222222"],
 'up':   [".222222.", "32222223", "32222223", ".222222.", "22222222"],
 'left': [".222111.", ".223222.", ".223222.", ".222222.", "22222222"],
}
ARMS = {    # torso rows 1-2: front/back views swing opposite arms; side view swings the near arm across the dress
 'down': [("32222223", "32222223"), (".2222223", "32222223"), ("32222223", "32222223"), ("32222223", ".2222223")],
 'up':   [("32222223", "32222223"), ("32222223", ".2222223"), ("32222223", "32222223"), (".2222223", "32222223")],
 'left': [(".223222.", ".223222."), (".232222.", ".232222."), (".223222.", ".223222."), (".222322.", ".222322.")],
}
HEM = {     # torso row 4: the hem sways toward the leading leg
 'down': ["22222222", ".2222222", "22222222", "2222222."],
 'up':   ["22222222", "2222222.", "22222222", ".2222222"],
 'left': ["22222222", ".2222222", "22222222", "2222222."],
}
LEGS = {    # 4 rows: legs (2) + boots (2)
 'down': [("..3..3..", "..3..3..", ".11..11.", ".11..11."),
          ("..3..3..", ".11..3..", "....11..", "....11.."),
          ("..3..3..", "..3..3..", ".11..11.", ".11..11."),
          ("..3..3..", "..3..11.", "..11....", "..11....")],
 'up':   [("..3..3..", "..3..3..", ".11..11.", ".11..11."),
          ("..3..3..", ".11..3..", "....11..", "....11.."),
          ("..3..3..", "..3..3..", ".11..11.", ".11..11."),
          ("..3..3..", "..3..11.", "..11....", "..11....")],
 'left': [("..3.3...", "..3.3...", ".11.11..", ".11.11.."),
          (".3...3..", "11...3..", "11..11..", "....11.."),
          ("...33...", "...33...", "..1111..", "..1111.."),
          (".3...3..", ".3...11.", "11...11.", "11......")],
}
def gardener_frames(direction):
    out = []
    for f in range(4):
        torso = list(TORSO[direction]); torso[1], torso[2] = ARMS[direction][f]; torso[4] = HEM[direction][f]
        frame = HEAD[direction] + torso + list(LEGS[direction][f])
        assert len(frame) == 16
        out.append(frame)
    return out
GARDENER = {}
for _d in ('down', 'up', 'left'):
    for _f, _fr in enumerate(gardener_frames(_d)): GARDENER['%s%d' % (_d, _f)] = '\n'.join(_fr)
# three-quarter turn poses (facing down-left / up-left; mirrored for the right side)
DIAG_DOWN = ["..1111..", ".111111.", "11333111", "13131311", "13131311", ".133311.", "..1111..",
             ".222211.", ".2322223", ".2322223", ".222222.", "22222222",
             "..3.3...", "..3.3...", ".11.11..", ".11.11.."]
DIAG_UP   = ["..1111..", ".111111.", "11111111", "13111111", "13111111", ".111111.", "..1111..",
             ".222222.", ".3222223", ".3222223", ".222222.", "22222222",
             "..3.3...", "..3.3...", ".11.11..", ".11.11.."]
GARDENER['diagdown'] = '\n'.join(DIAG_DOWN)
GARDENER['diagup'] = '\n'.join(DIAG_UP)
FONT_DIGITS = {
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
}
# Oppie as a sprite (title screen hoppers / menu cursor). OBJ palette 6: 1 = body colour, 2 = white, 3 = black
OPPIE_SPR = """
..1111..
.111111.
11111111
12211221
12311231
11111111
.111111.
........
"""
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
for k in ['%s%d' % (d, f) for d in ('down', 'up', 'left') for f in range(4)] + ['diagdown', 'diagup']:
    add_sprite('SPR_' + k.upper(), rows(GARDENER[k]))
add_sprite('SPR_FLASK', ['........']*8 + rows(FLASK))
add_sprite('SPR_SHADOW', ['........']*8 + rows(SHADOW))
add_sprite('SPR_OPPIE', ['........']*8 + rows(OPPIE_SPR))
# dynamic tiles for score pop-ups: 6 pop-ups x 3 objects (8x16), composed at runtime from a 3x5 font
# (3 objects = 6 digits, enough for the biggest award a long power chain can pay)
for _k in range(18):
    add_sprite('SPR_POP%d' % _k, ['........'] * 16)

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
T('T_STAR_INV', """
www.wwww
www.wwww
w.....ww
ww...www
ww...www
w.www.ww
wwwwwwww
wwwwwwww
""")   # T_STAR inverted: the original's second FloorStar frame, shown only while the pad flashes
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
for _n in ('T_OPPIE', 'T_OPPIE_LOOK_L', 'T_OPPIE_LOOK_U', 'T_OPPIE_LOOK_D', 'T_OPPIE_STUN', 'T_MUSH'):
    _r = dict(bg)[_n]
    bg.append((_n + '_W', [x.replace('c', '#').replace('w', 'c').replace('#', 'w') for x in _r]))
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
# --- decoration, palette P6: 0 = ground (dark green), 1 = black, 2 = purple, 3 = light blue
def block(name, art, w):
    """split a w*8 x h*8 pixel block (strings of digits) into tiles named name0.. row-major"""
    r = rows(art); h = len(r) // 8
    for ty in range(h):
        for tx in range(w):
            T('%s%d' % (name, ty * w + tx), '\n'.join(r[ty*8+k][tx*8:tx*8+8] for k in range(8)))
T('T_GRASS', """
00000000
00000000
00000000
00000000
00000000
00000000
00000000
00000000
""")
block('T_TREE', """
0000011000110000
0001122111221000
0012222222222100
0112222332222110
1222223322222221
1222222222222221
1221122222211221
1221122222211221
1222222222222221
1222122222221221
1222212222212221
0122222111122210
0012322222232100
0001122222211000
0000011211100000
0000000110000000
""", 2)
# sleeping cat, 24x16, light blue with black outline and purple ears/nose
block('T_CAT', """
000000000000000000000000
000000000000000000000000
000011000011000000000000
000131100131100000000000
001333331333310000000000
001333333333311111000000
001313333313333333100000
001333333333333333310000
001332333333333333310000
000133333333333333310000
000013333333333333310000
000001333333333333310000
000000133333333333100000
000000013333333331000000
000000001111111110000000
000000000000000000000000
""", 3)
# Cloverana, 16x24: purple hat with light blue band, light blue face, purple dress
block('T_WITCH', """
0000000010000000
0000000122000000
0000001222100000
0000012222210000
0000122222221000
0001222222222100
0012222222222210
0133333333333331
1222222222222221
0113333333331100
0001333333310000
0001313333130000
0001333333310000
0000133333100000
0000013331000000
0000122222100000
0001222222210000
0012222222221000
0012222222221000
0122222222222100
0122222222222100
0001110000111000
0001110000111000
0000000000000000
""", 2)
# --- title screen: palette P1 (black, green, light green, white) vines & flowers; P0 (black, yellow, olive, white) big letters
T('T_VINE_H', """
........
...2....
..212...
11111111
....2.1.
.....21.
........
........
""")
T('T_VINE_H2', """
........
.....2..
....212.
11111111
..2.1...
.21.....
........
........
""")
T('T_VINE_V', """
...1....
..21....
...12...
...1....
..21....
...1....
...12...
...1....
""")
T('T_FLOWER', """
........
...3....
..333...
.33233..
..333...
...3....
........
........
""")
T('T_VINE_CORNER', """
........
........
........
...11111
..1.....
..1.....
..1.....
..1.....
""")
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
'@': ["01110","10001","10111","10101","10111","10001","01110"],
}
FONT_ORDER = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-!.',x @"
font_first = len(bg)
for ch in FONT_ORDER:
    g = FONT[ch]
    r = ['.' + ''.join('2' if b == '1' else '.' for b in row) + '..' for row in g] + ['........']
    bg.append(('T_FONT_' + str(ord(ch)), r))

# --- big title letters: 5x7 glyph scaled 2x (10x14) at (3,1) with a 1px olive drop shadow; 2x2 tiles per letter
BIG = "MAGICRDEN"
big_first = len(bg)
for ch in BIG:
    g = FONT[ch]; px = [['.'] * 16 for _ in range(16)]
    for dy, dx, col in ((1, 1, '2'), (0, 0, '1')):
        for gy in range(7):
            for gx in range(5):
                if g[gy][gx] == '1':
                    for yy in range(2):
                        for xx in range(2):
                            px[1 + gy*2 + yy + dy][3 + gx*2 + xx + dx] = col
    art = '\n'.join(''.join(r) for r in px)
    block('T_BIG_' + ch, art, 2)

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
# flask timer digits are drawn over the bricks at (9,1),(10,1) while a flask is active
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
for i in range(3): put(i, 8, 'T_CAT%d' % i, P_DECO); put(i, 9, 'T_CAT%d' % (i+3), P_DECO)
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

# ------------------------------------------------------------------ title map (20x18)
ttmap = [[names['T_BLACK']] * W for _ in range(H)]
tamap = [[7] * W for _ in range(H)]
def tput(x, y, name, pal): ttmap[y][x] = names[name]; tamap[y][x] = pal
# vine frame: top row 1, bottom row 8, sides cols 1 and 18 rows 2-7
for x in range(2, 18):
    tput(x, 1, 'T_VINE_H' if x % 2 == 0 else 'T_VINE_H2', 1)
    tput(x, 8, 'T_VINE_H2' if x % 2 == 0 else 'T_VINE_H', 1)
for y in range(2, 8):
    tput(1, y, 'T_VINE_V', 1); tput(18, y, 'T_VINE_V', 1)
for x in (3, 8, 13, 16): tput(x, 1, 'T_FLOWER', 1)
for x in (2, 6, 11, 15): tput(x, 8, 'T_FLOWER', 1)
tput(1, 4, 'T_FLOWER', 1); tput(18, 6, 'T_FLOWER', 1)
def big_text(x, y, word):
    for i, ch in enumerate(word):
        tput(x + 2*i, y, 'T_BIG_%s0' % ch, 0); tput(x + 2*i + 1, y, 'T_BIG_%s1' % ch, 0)
        tput(x + 2*i, y + 1, 'T_BIG_%s2' % ch, 0); tput(x + 2*i + 1, y + 1, 'T_BIG_%s3' % ch, 0)
big_text(5, 2, 'MAGIC')
big_text(4, 5, 'GARDEN')
def ttext(x, y, st):
    for i, ch in enumerate(st): tput(x + i, y, 'T_FONT_' + str(ord(ch)), 7)
ttext(5, 11, 'GAME START')
ttext(5, 12, 'HIGH SCORES')
ttext(2, 16, '@1984 LX SYSTEMS')

# ------------------------------------------------------------------ emit
os.makedirs(os.path.join(ROOT, 'include'), exist_ok=True)
h = ['// Generated by tools/make_art.py - do not edit', '#ifndef GFX_DATA_H', '#define GFX_DATA_H', '#include <stdint.h>', '']
for i, (n, _) in enumerate(sprite_tiles): h.append(f'#define {n} {2*i}')
h.append(f'#define SPR_TILE_COUNT {2*len(sprite_tiles)}')
h.append(f'#define BG_BASE {BG_BASE}')
for n, v in names.items(): h.append(f'#define {n} {v}')
h.append(f'#define BG_TILE_COUNT {len(bg)}')
h.append(f'#define FONT_FIRST {BG_BASE + font_first}')
h.append(f'#define BIG_FIRST {BG_BASE + big_first}')
h.append('#define FONT_ORDER "' + FONT_ORDER.replace('\\', '\\\\').replace('"', '\\"') + '"')
h += ['', 'extern const uint8_t spr_tiles[];', 'extern const uint8_t bg_tiles[];',
      'extern const uint8_t frame_map[20*18];', 'extern const uint8_t frame_attr[20*18];',
      'extern const uint8_t title_map[20*18];', 'extern const uint8_t title_attr[20*18];', '', '#endif']
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
c = ['// Generated by tools/make_art.py - do not edit', '#pragma bank 1', '#include <stdint.h>', '#include "gfx_data.h"', '',
     carr('spr_tiles', spr), '', carr('bg_tiles', bgd), '',
     carr('frame_map', [t for row in tmap for t in row]), '',
     carr('frame_attr', [a for row in amap for a in row]), '',
     carr('title_map', [t for row in ttmap for t in row]), '',
     carr('title_attr', [a for row in tamap for a in row])]
open(os.path.join(ROOT, 'src', 'gfx_data.c'), 'w').write('\n'.join(c) + '\n')
print(f'sprite tiles: {2*len(sprite_tiles)}  bg tiles: {len(bg)}  BG_BASE={BG_BASE}  total={BG_BASE+len(bg)}')
