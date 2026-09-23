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
# Gardener, 8x16 (one OBJ): 14 px tall, feet in her cell, head overhanging 6 px into the cell above.
# 1 = dark purple outline, 2 = purple (hair and dress), 3 = white (face, hands, socks).
# Chibi proportions (8-row head, 4-row dress, 2-row legs): the dark outline runs round the top of the
# head and the hair tips; beside the face the edge is hair purple, so the hair frames the face instead
# of the face filling the head. Long hair falls over the shoulders and curls in at the tips.
# Four walk frames per direction: stand, step, stand, step (legs, hands and hem only, no vertical bob).
HEAD = {    # 8 rows
 'down': ["..1111..", ".122221.", "12222221", "21333312", "23133132", "23133132", ".233332.", ".123321."],
 'up':   ["..1111..", ".122221.", "12222221", "12222221", "12222221", "12222221", "12222221", "12222221"],
 # side: face on the left, hair down the back on the right
 'left': ["..1111..", ".122221.", "12222221", "3312222.", "31312221", "31312221", ".3312221", "..312221"],
}
BODY = {    # 4 rows per frame: hair tips over the shoulders, hands, dress, hem (swaying toward the leading leg)
 'down': [["2.2222.2", "13222231", ".222222.", "22222222"], ["2.2222.2", "1.222221", ".222222.", ".2222222"],
          ["2.2222.2", "13222231", ".222222.", "22222222"], ["2.2222.2", "122222.1", ".222222.", "2222222."]],
 'up':   [[".122221.", ".311113.", ".222222.", "22222222"], [".122221.", "321111..", ".222222.", "2222222."],
          [".122221.", ".311113.", ".222222.", "22222222"], [".122221.", "..111123", ".222222.", ".2222222"]],
 'left': [["..21221.", "..23121.", ".22221..", "2222222."], ["..21221.", ".322121.", ".22221..", ".222222."],
          ["..21221.", "..23121.", ".22221..", "2222222."], ["..21221.", "..22121.", ".22221..", "2222222."]],
}
LEGS = {    # 2 rows: sock + shoe
 'down': [("..3..3..", "..1..1.."), (".3...3..", ".1...11."), ("..3..3..", "..1..1.."), ("..3...3.", ".11...1.")],
 'up':   [("..3..3..", "..1..1.."), ("..3...3.", ".11...1."), ("..3..3..", "..1..1.."), (".3...3..", ".1...11.")],
 'left': [("..3.3...", ".11.11.."), (".3...3..", "11...11."), ("..33....", ".111...."), (".3...3..", "11...11.")],
}
TOP = ["........"] * 2
def gardener_frames(direction):
    out = []
    for f in range(4):
        frame = TOP + HEAD[direction] + BODY[direction][f] + list(LEGS[direction][f])
        assert len(frame) == 16
        out.append(frame)
    return out
GARDENER = {}
for _d in ('down', 'up', 'left'):
    for _f, _fr in enumerate(gardener_frames(_d)): GARDENER['%s%d' % (_d, _f)] = '\n'.join(_fr)
# three-quarter turn poses (facing down-left / up-left; mirrored for the right side)
DIAG_DOWN = TOP + ["..1111..", ".122221.", "12222221", "13331221", "31313221", "31313221", ".3332221", "..132221",
                   ".222221.", ".3222231", ".222222.", "22222222", "..3.3...", ".11.11.."]
DIAG_UP   = TOP + ["..1111..", ".122221.", "12222221", "12222221", "13222221", "13222221", "12222221", "12222221",
                   ".122221.", ".311113.", ".222222.", "22222222", "..3.3...", ".11.11.."]
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


# ------------------------------------------------------------------ sidebars (the original's grove)
# Trees: BG palette 6 (0 ground, 1 blue rim/skirt, 2 tree colour, 3 white eyes); the tree colour follows the
# rank like the original's (purple, red, blue, white). Drawn back to front, clipped to the 32x96 side strip.
TREE24 = """
........11111111........
......112222222211......
....1122222222222211....
...122222222222222221...
..12222222222222222221..
..12222222222222222221..
.1222222222222222222221.
.1222223322222233222221.
.1222223122222231222221.
.1222223322222233222221.
.1222222222332222222221.
122222222222222222222221
112222222222222222222211
111222222222222222222111
111121222122212221221111
111112111211121112111111
111111111111111111111111
111111111111111111111111
.1111111111111111111111.
..1.111.11111.1111.11...
"""
TUFT = """
.22.22..
2112112.
.1..1...
"""
SIDE_TREES_L = [(-10, -10), (12, 4), (-10, 22), (12, 62), (-10, 76), (14, 90)]
SIDE_TREES_R = [(-12, -8), (14, 2), (-10, 40), (14, 54), (-12, 70), (12, 86)]
SIDE_TUFTS_L = [(6, 40), (20, 60)]
SIDE_TUFTS_R = [(2, 34), (22, 44)]
def compose_side(trees, tufts):
    img = [['0'] * 32 for _ in range(96)]
    for art, spots in ((TUFT, tufts), (TREE24, trees)):
        r = [l for l in art.strip('\n').split('\n')]
        for x, y in spots:
            for j, line in enumerate(r):
                for i, c in enumerate(line):
                    if c != '.' and 0 <= x + i < 32 and 0 <= y + j < 96: img[y + j][x + i] = c
    return img

# Cat asleep in the left grove: 24x16, three 8x16 objects, OBJ palette 5 (1 brown, 2 orange, 3 white)
CAT = ["." * 24] * 3 + [
 "..1....1" + "." * 16,
 ".131..131" + "." * 15,
 ".12211221" + "......" + "11111" + "....",
 "1221212221" + ".." + "1122122211" + "..",
 "12222222221" + "122212222221" + ".",
 "12112221121" + "222212222221" + ".",
 "12222122221" + "222221222221" + ".",
 "12223132221" + "222222222221" + ".",
 ".122333221" + "2222212222221" + ".",
 "..1111111" + "22222222222221" + ".",
 "." + "133" + "2" * 19 + "1",
 "." + "1331" + "11111" + "2" * 13 + "1",
 "..11" + ".." + "1" * 16 + "..",
]
# Yawning (the original's bgCatYawn): she wakes for the 60 frames between a flask being made and it dropping in
CAT_YAWN = list(CAT)
CAT_YAWN[12] = "12231113221" + CAT[12][11:]
CAT_YAWN[13] = ".123111321" + CAT[13][10:]
CAT_YAWN[14] = "..1133311" + CAT[14][9:]
# Cloverana in the right grove: 16x32 (four 8x16 objects), OBJ palette 6 (1 black, 2 blue, 3 mint).
# Frames as the original's bgWitch: 0 idle, 1-2 zap (staff raised, spark) while a mushroom grows,
# 3-4 jump for joy when the gardener dies.
WITCH_BODY = [
 "..........1.....", ".........121....", "........1221....", ".......12221....", "......122221....",
 ".....1222221....", "....12222221....", "...1222222221...", ".11111111111111.", "1222222222222221",
 ".11133333333111.", "..113333333311..", "..113133331311..", "..113133331311..", "..113333333311..",
 "..113331133311..", "..111333333111..", "....11111111....", "...1222222221...", "..132222222231..",
 "..122222222221..", ".12222222222221.", ".11111111111111.", "...11......11...",
]
def witch_frame(dy, staff, spark=False, crouch=False):
    c = [['.'] * 16 for _ in range(32)]
    body = WITCH_BODY[:-1] if crouch else WITCH_BODY
    for j, line in enumerate(body):
        for i, ch in enumerate(line):
            y = dy + j
            if ch != '.' and 0 <= y < 32: c[y][i] = ch
    def put(y, x, ch):
        if 0 <= y < 32: c[y][x] = ch
    if staff == 'low':                              # staff held at her side, orb at shoulder height
        for y in range(14, 24 - crouch): put(dy + y, 14, '1')
        for y, x in ((12, 14), (13, 13), (13, 14), (13, 15)): put(dy + y, x, '3')
    else:                                           # staff raised above the hat, hand on it at chin height
        put(dy + 19, 12, '2')                       # the low hand is gone from the dress
        for y in range(-2, 20): put(dy + y, 14, '1')
        for y, x in ((-5, 14), (-4, 13), (-4, 14), (-4, 15), (-3, 14)): put(dy + y, x, '3')
        put(dy + 15, 14, '3'); put(dy + 15, 15, '3')
    if spark:                                       # burst round the orb
        for y, x in ((-7, 14), (-6, 12), (-6, 11), (-4, 11), (-2, 12), (-7, 11), (-1, 11), (-8, 13)): put(dy + y, x, '3')
    return [''.join(r) for r in c]
WITCH_FRAMES = [witch_frame(8, 'low'), witch_frame(8, 'high'), witch_frame(8, 'high', spark=True),
                witch_frame(9, 'low', crouch=True), witch_frame(5, 'high')]

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
for _k in range(3): add_sprite('SPR_CAT%d' % _k, [r[_k*8:_k*8+8] for r in CAT])
for _k in range(3): add_sprite('SPR_CAT_YAWN%d' % _k, [r[_k*8:_k*8+8] for r in CAT_YAWN])
for _f, _fr in enumerate(WITCH_FRAMES):     # per frame: top-left, top-right, bottom-left, bottom-right
    for _k, (_y0, _x0) in enumerate(((0, 0), (0, 8), (16, 0), (16, 8))):
        add_sprite('SPR_WITCH%d_%d' % (_f, _k), [r[_x0:_x0+8] for r in _fr[_y0:_y0+16]])
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
# trail oppie (the original's s27_Follow): wide-open eyes, pupils toward the middle, and a 2-frame bob that
# render.c swaps into this one VRAM tile every 5 frames (image_speed 0.2). Frame 1 squashes down a pixel.
FOLLOW_BOB = [rows(s) for s in ("""
..cccc..
.cccccc.
cccccccc
cwwccwwc
cwkcckwc
cwwccwwc
cccccccc
.cccccc.
""", """
........
..cccc..
.cccccc.
cccccccc
cwwccwwc
cwkcckwc
cwwccwwc
.cccccc.
""")]
bg.append(('T_FOLLOW', FOLLOW_BOB[0]))
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
# --- decoration, palette P6: 0 = ground, 1 = blue (tree rim and skirt), 2 = tree colour, 3 = white (eyes)
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
# composed sidebars (cols 0-3 and 16-19, rows 3-14) -> tiles in VRAM bank 1 (attribute bit 3)
side_tiles = []; side_index = {}
def side_tile(r8):
    k = tuple(r8)
    if k not in side_index: side_index[k] = len(side_tiles); side_tiles.append(list(r8))
    return side_index[k]
for x0, trees, tufts in ((0, SIDE_TREES_L, SIDE_TUFTS_L), (16, SIDE_TREES_R, SIDE_TUFTS_R)):
    img = compose_side(trees, tufts)
    for ty in range(12):
        for tx in range(4):
            r8 = [''.join(img[ty*8+k][tx*8:tx*8+8]) for k in range(8)]
            tmap[3+ty][x0+tx] = side_tile(r8); amap[3+ty][x0+tx] = P_DECO | 0x08
assert len(side_tiles) <= 256, len(side_tiles)
# playfield cols 4-15 rows 3-14: floor checker (palettes 0/1), overwritten at runtime
for y in range(12):
    for x in range(12):
        put(4+x, 3+y, 'T_FLOOR', (x + y) & 1)
# bottom HUD rows 15-17 (palette 7: 0 dark, 1 grey, 2 white, 3 plaque/liquid colour, which render.c
# switches to a new flask's colour while it is on its way): the original's two plaques on a dark ledge,
# "Saved" / "Score" in a small script, tall digits, and a flask meter between them.
# Everything is composed as a 160x24 picture and cut into tiles in VRAM bank 1 (with the grove).
def hud_blit(cv, art, x, y):
    for j, r in enumerate(art):
        for i, ch in enumerate(r):
            if ch != '.' and 0 <= y + j < len(cv) and 0 <= x + i < len(cv[0]): cv[y + j][x + i] = ch
def plaque(cv, x0, x1):
    """dark outline, white inner line, rounded top corners, runs off the bottom of the screen"""
    for y in range(24):
        for x in range(x0, x1):
            dx = min(x - x0, x1 - 1 - x)
            if (y == 0 and dx < 2) or (y == 1 and dx < 1): continue
            edge = y == 0 or dx == 0 or (y == 1 and dx == 1)
            inner = (y == 1 or dx == 1 or (y == 2 and dx == 2)) and not edge
            cv[y][x] = '0' if edge else ('2' if inner else '3')
    curl = [".00.", "0..0", "0.00", "0..."]
    hud_blit(cv, curl, x0 + 3, 3); hud_blit(cv, [r[::-1] for r in curl], x1 - 7, 3)
SCRIPT = {  # label letters, 6 rows
 'S': [".000.", "0....", ".00..", "...0.", "...0.", "000.."],
 'a': [".....", ".....", ".000.", "0..0.", "0..0.", ".00.0"],
 'v': [".....", ".....", "0...0", "0...0", ".0.0.", "..0.."],
 'e': [".....", ".....", ".00..", "0.00.", "00...", ".000."],
 'd': ["...0.", "...0.", ".000.", "0..0.", "0..0.", ".00.0"],
 'c': [".....", ".....", ".00..", "0....", "0....", ".000."],
 'o': [".....", ".....", ".00..", "0..0.", "0..0.", ".00.."],
 'r': [".....", ".....", "0.00.", "00...", "0....", "0...."],
}
def script(cv, word, x, y):
    for ch in word:
        hud_blit(cv, SCRIPT[ch], x, y); x += len(SCRIPT[ch][0])
def tall_digit(d):
    """the 5x7 font doubled vertically, white with a dark outline: 7x16"""
    art = [['.'] * 7 for _ in range(16)]
    for j, row in enumerate(FONT[str(d)]):
        for i, b in enumerate(row):
            if b == '1': art[1 + 2*j][1 + i] = art[2 + 2*j][1 + i] = '2'
    out = [r[:] for r in art]
    for y in range(16):
        for x in range(7):
            if art[y][x] == '.' and any(0 <= y+dy < 16 and 0 <= x+dx < 7 and art[y+dy][x+dx] == '2'
                                        for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                out[y][x] = '0'
    return [''.join(r) for r in out]
HUD_FLASK = [
 "......0000......", ".....011110.....", "......0220......", "......0220......", ".....022220.....",
 "....02222220....", "...0222222220...", "..022222222220..", "..022222222220..", ".02222222222220.",
 ".02222222222220.", ".02222222222220.", "..022222222220..", "...0222222220...", "....00000000....",
 "................"]
def hud_flask(level):   # 0-5 saved toward the next flask, 6 = a flask is made; the liquid is colour 3
    a = [list(r) for r in HUD_FLASK]
    top = 13 - [0, 2, 4, 6, 8, 9, 10][level]
    for y in range(top + 1, 14):
        for x in range(16):
            if a[y][x] == '2': a[y][x] = '3'
    a[9][3] = a[10][3] = a[8][4] = '2'   # glint
    return [''.join(r) for r in a]
def cut(cv, tx, ty):
    return [''.join(cv[ty*8 + k][tx*8:tx*8 + 8]) for k in range(8)]
hud = [['0'] * 160 for _ in range(24)]
plaque(hud, 0, 48); plaque(hud, 80, 160)
script(hud, 'Saved', 13, 2); script(hud, 'Score', 106, 2)
# dynamic tiles, each set consecutive in bank 1: tall digits (10 tops, then 10 bottoms) on the plaque colour,
# then the flask meter, 7 states x 4 tiles (top-left, top-right, bottom-left, bottom-right)
B1_DIGIT = len(side_tiles)
for half in (0, 1):
    for d in range(10):
        cell = [['3'] * 8 for _ in range(16)]
        hud_blit(cell, tall_digit(d), 0, 0)
        side_tiles.append([''.join(r) for r in cell[half*8:half*8 + 8]])
B1_FLASK = len(side_tiles)
for lv in range(7):
    cell = [['0'] * 16 for _ in range(16)]
    hud_blit(cell, hud_flask(lv), 0, 0)
    for ty, tx in ((0, 0), (0, 1), (1, 0), (1, 1)): side_tiles.append(cut(cell, tx, ty))
for ty in range(3):
    for tx in range(20):
        tmap[15 + ty][tx] = side_tile(cut(hud, tx, ty)); amap[15 + ty][tx] = P_HUD | 0x08
for i, d in enumerate((0, 0, 0)):                       # SAVED digits cols 2-4, SCORE cols 11-18, rows 16-17
    tmap[16][2 + i] = B1_DIGIT + d; tmap[17][2 + i] = B1_DIGIT + 10 + d
for i in range(8):
    tmap[16][11 + i] = B1_DIGIT; tmap[17][11 + i] = B1_DIGIT + 10
for k, (ty, tx) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):   # flask meter cols 7-8, rows 15-16
    tmap[15 + ty][7 + tx] = B1_FLASK + k
for x in (7, 8, 9):                                     # multiplier "x2" in the bank-0 font, row 17
    put(x, 17, 'T_BLACK', P_HUD)
assert len(side_tiles) <= 256, len(side_tiles)

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
      'extern const uint8_t follow_bob[32];',
      'extern const uint8_t side_tiles[];', f'#define SIDE_TILE_COUNT {len(side_tiles)}',
      f'#define B1_DIGIT {B1_DIGIT}', f'#define B1_FLASK {B1_FLASK}',
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
     carr('follow_bob', tile2bpp(FOLLOW_BOB[0]) + tile2bpp(FOLLOW_BOB[1])), '',
     carr('side_tiles', [b for r8 in side_tiles for b in tile2bpp(r8)]), '',
     carr('frame_map', [t for row in tmap for t in row]), '',
     carr('frame_attr', [a for row in amap for a in row]), '',
     carr('title_map', [t for row in ttmap for t in row]), '',
     carr('title_attr', [a for row in tamap for a in row])]
open(os.path.join(ROOT, 'src', 'gfx_data.c'), 'w').write('\n'.join(c) + '\n')
print(f'sprite tiles: {2*len(sprite_tiles)}  bg tiles: {len(bg)}  BG_BASE={BG_BASE}  total={BG_BASE+len(bg)}  side tiles (VRAM bank 1): {len(side_tiles)}')
assert BG_BASE + len(bg) <= 256
