#!/usr/bin/env python3
"""Headless smoke test with PyBoy: boot, start a game, drive inputs, dump screenshots.
usage: play_test.py ROM OUTDIR [script]
script: comma list of  <frames>[:buttons]  e.g. "120,30:start,200:left,24:a,600:right"
Buttons: up down left right a b start select (held for that many frames, then released)."""
import sys, os
from pyboy import PyBoy
rom, out = sys.argv[1], sys.argv[2]
script = sys.argv[3] if len(sys.argv) > 3 else "120,30:start,180,60:left,120:down,120:right,120:up,12:a,240"
os.makedirs(out, exist_ok=True)
pb = PyBoy(rom, window="null", cgb=True)
pb.set_emulation_speed(0)
shot = 0
def snap(tag):
    global shot
    pb.screen.image.save(os.path.join(out, f"{shot:02d}_{tag}.png")); shot += 1
for part in script.split(','):
    if ':' in part: n, btn = part.split(':'); n = int(n)
    else: n, btn = int(part), None
    if btn: pb.button_press(btn)
    pb.tick(n, True)
    if btn: pb.button_release(btn)
    snap(btn or 'idle')
pb.stop(save=False)
print("screenshots:", shot)
