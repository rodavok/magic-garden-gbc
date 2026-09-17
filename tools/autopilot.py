#!/usr/bin/env python3
"""Integration run: a simple bot plays the game for N frames, avoiding obstacles, collecting oppies and
dropping them on the star row. Saves periodic screenshots and prints a summary.
usage: autopilot.py [rom] [frames] [outdir]"""
import sys, os, random
sys.path.insert(0, os.path.dirname(__file__))
from pyboy import PyBoy
from gbmem import Mem
ROOT = os.path.join(os.path.dirname(__file__), '..')
rom = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build/magicgarden.gbc')
frames = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, 'build/auto')
os.makedirs(out, exist_ok=True)
random.seed(1)
pb = PyBoy(rom, window="null", cgb=True); pb.set_emulation_speed(0); M = Mem(pb, rom.replace('.gbc', '.noi'))
C_EMPTY, C_FRIEND, C_TRAIL, C_ANGRY, C_MUSH, C_FLASK, C_APP_A, C_APP_M = range(8)
UP, RIGHT, DOWN, LEFT = range(4)
DX = [0, 1, 0, -1]; DY = [-1, 0, 1, 0]; NAME = ['up', 'right', 'down', 'left']

pb.tick(200, True); pb.button_press('start'); pb.tick(5, True); pb.button_release('start')
while not (M.rd('state') == 0 and M.rd('px') == 1): pb.tick(1, True)
pb.tick(30, True); pb.button_press('down'); pb.tick(3, True); pb.button_release('down')
CELL = M.defs['CELL_UNITS']

def cell_ahead(x, y, d):
    nx, ny = x + DX[d], y + DY[d]
    if nx < 0 or ny < 0 or nx > 11 or ny > 11: return None, None, 'wall'
    return nx, ny, M.rd('grid', ny * 12 + nx)
def safe(g, powered):
    if g in (C_EMPTY, C_FRIEND, C_FLASK, C_APP_A, C_APP_M): return True
    if g == C_ANGRY and powered: return True
    return False
held = None; shots = 0; last_shot = 0; jumps = 0; drops = 0; decided_at = -1
for f in range(frames):
    st = M.rd('state')
    if st != 1: break
    sub = M.rd('sub'); x, y, d = M.rd('px'), M.rd('py'), M.rd('dir')
    if sub == 0 and M.rd('z') == 0:
        powered = M.rd('power_timer') > 0
        pad = [M.rd('pad_rows', y) for y in range(12)]; tl = M.rd('trail_len')
        def on_pad(c): return (pad[c // 12] >> (c % 12)) & 1
        # drop when the whole trail lies on the pad
        if tl >= 1 and M.rd('pad_flash') == 0 and all(on_pad(M.rd('trail', k)) for k in range(tl)):
            pb.button_press('b'); pb.tick(1, True); pb.button_release('b'); drops += 1
        # choose a direction: prefer friend/flask ahead, else straight if safe, else any safe, else jump
        opts = [dd for dd in range(4) if dd != (d + 2) % 4]
        scored = []
        for dd in opts:
            nx, ny, g = cell_ahead(x, y, dd)
            if g == 'wall' or not safe(g, powered): continue
            sc = 0
            if g in (C_FRIEND, C_FLASK): sc += 5
            if dd == d: sc += 1
            if on_pad(ny * 12 + nx) and tl >= 1: sc += 3
            nx2, ny2, g2 = cell_ahead(nx, ny, dd)   # look one further: avoid dead ends
            if g2 == 'wall' or not safe(g2, powered): sc -= 2
            scored.append((sc + random.random() * 0.5, dd))
        if scored:
            best = max(scored)[1]
            if best != d:
                if held: pb.button_release(held)
                held = NAME[best]; pb.button_press(held)
        else:
            pb.button_press('a'); pb.tick(1, True); pb.button_release('a'); jumps += 1
    pb.tick(1, True)
    if held and M.rd('sub') >= 3 and M.rd('dir') == NAME.index(held): pb.button_release(held); held = None
    if f - last_shot >= 300:
        pb.screen.image.save(os.path.join(out, f'{shots:02d}_f{f}.png')); shots += 1; last_shot = f
pb.screen.image.save(os.path.join(out, f'{shots:02d}_end.png'))
print(f'frames={f} state={M.rd("state")} saved={M.rd("saved")} score={M.rd("score")} angry={M.rd("n_angry")} flasks={M.rd("n_flask")} '
      f'friends={M.rd("n_friend")} jumps={jumps} drops={drops} best_drop={M.rd("best_drop")} kills={M.rd("total_kills")} palette={M.rd("palette_set")}')
pb.stop(save=False)
