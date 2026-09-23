#!/usr/bin/env python3
"""Slowdown check under load: a full trail, many angry oppies, flasks, pop-ups. Counts game updates per
emulator frame (must be 1:1) and reports the worst logic-phase end scanline (dbg[1]).
usage: stress_test.py [rom] [n_angry] [trail_len] [mode]
mode: play (default), power (a flask is running: enemies flash, frozen), drop (B with the trail half on the pad)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pyboy import PyBoy
from gbmem import Mem
ROOT = os.path.join(os.path.dirname(__file__), '..')
rom = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build/magicgarden.gbc')
NA = int(sys.argv[2]) if len(sys.argv) > 2 else 60
NT = int(sys.argv[3]) if len(sys.argv) > 3 else 48
MODE = sys.argv[4] if len(sys.argv) > 4 else 'play'
C_EMPTY, C_FRIEND, C_TRAIL, C_ANGRY, C_MUSH, C_FLASK = range(6)
pb = PyBoy(rom, window="null", cgb=True); pb.set_emulation_speed(0); M = Mem(pb, rom.replace('.gbc', '.noi')); rd, wr = M.rd, M.wr
pb.tick(200, True); pb.button_press('start'); pb.tick(5, True); pb.button_release('start')
for _ in range(400):
    if rd('state') == 0 and rd('px') == 1: break
    pb.tick(1, True)
pb.tick(30, True); pb.button_press('down'); pb.tick(3, True); pb.button_release('down'); pb.tick(5, True)

def setup():
    for i in range(144): wr('grid', C_EMPTY, i); wr('gstate', 0, i)
    wr('n_angry', 0); wr('n_appear', 0); wr('n_flask', 0); wr('n_friend', 0); wr('friend_target', 0); wr('potion_delay', 0)
    # player parked at (0,0) moving right, never reaching a boundary (sub is re-poked each frame)
    wr('px', 0); wr('py', 0); wr('dir', 1); wr('dir_choice', 1); wr('z', 0)
    # trail snakes through rows 2-5, angry oppies fill rows 6-11 with gaps so they keep hopping
    cells = [y * 12 + x for y in range(2, 6) for x in range(12)][:NT]
    for k, c in enumerate(cells): wr('grid', C_TRAIL, c); wr('trail', c, k)
    wr('trail_len', len(cells))
    n = 0
    for c in range(6 * 12, 144):
        if n >= NA or (c % 3 == 0 and NA < 64): continue
        wr('grid', C_ANGRY, c); wr('gstate', 0, c); wr('gtimer', 1 + (c * 7) % 128, c); wr('angry_list', c, n); n += 1
    wr('n_angry', n)
    for k, c in enumerate([12 + 3, 12 + 7, 12 + 10]):
        wr('grid', C_FLASK, c); wr('gstate', k, c); wr('gtimer', 100, c); wr('flask_list', c, k); wr('flask_fall', 0, k)
    wr('n_flask', 3)
    wr('pad_life', 30000); wr('dirty_rows', 0xFFF)
    return n

n = setup()
if MODE == 'power': wr('power_timer', 30000); wr('mult', 3)
if MODE == 'drop':
    for y in range(12): wr('pad_rows', 0x3F if 2 <= y <= 5 else 0, y)
worst, misses, frames = 0, 0, 600
for f in range(frames):
    wr('sub', 5)
    if MODE == 'drop' and f == 10: pb.button_press('b')
    if MODE == 'drop' and f == 13: pb.button_release('b')
    if rd('state') != 1: print('player died at frame', f); break
    fc = rd('frame_count'); pb.tick(1, True)
    d = (rd('frame_count') - fc) & 0xFFFF
    if d == 0: misses += 1
    ly = rd('dbg', 1)
    if ly < 144: worst = max(worst, ly)
print(f'{MODE} angry={n} trail={NT}: skipped frames {misses}/{frames}, worst logic end LY {worst} (VBlank at 144)')
sys.exit(1 if misses else 0)
