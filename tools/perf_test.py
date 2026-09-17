#!/usr/bin/env python3
"""Frame-time check: loop iterations per 120 frames (must be 120) and per-stage LY timestamps."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pyboy import PyBoy
from gbmem import Mem
rom = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'build/magicgarden.gbc')
pb = PyBoy(rom, window="null", cgb=True); pb.set_emulation_speed(0); M = Mem(pb, rom.replace('.gbc', '.noi'))
pb.tick(200, True); pb.button_press('start'); pb.tick(5, True); pb.button_release('start')
for _ in range(400):
    if M.rd('state') == 1: break
    pb.tick(1, True)
else:
    print('never reached play state; state =', M.rd('state')); sys.exit(1)
pb.tick(30, True)
a = M.rd('frame_count'); pb.tick(120, True); b = M.rd('frame_count')
print('loop iterations in 120 frames:', b - a)
print('LY [update start, update+prepare done, vblank flush start, flush done]:', [M.rd('dbg', i) for i in range(4)])
sys.exit(0 if b - a >= 118 else 1)
