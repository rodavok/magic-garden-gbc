#!/usr/bin/env python3
"""Mechanics test: runs the ROM in PyBoy, pokes cells into the game struct and asserts rules.
usage: sim_test.py build/magicgarden.gbc"""
import re, sys, os
from pyboy import PyBoy
ROOT = os.path.join(os.path.dirname(__file__), '..')
rom = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build/magicgarden.gbc')

sys.path.insert(0, os.path.dirname(__file__))
from gbmem import Mem
C_EMPTY, C_FRIEND, C_TRAIL, C_ANGRY, C_MUSH, C_FLASK = range(6)
PS_READY, PS_PLAY, PS_DEAD, PS_WIN = range(4)
CELL = 12

pb = PyBoy(rom, window="null", cgb=True); pb.set_emulation_speed(0)
M = Mem(pb, rom.replace('.gbc', '.noi')); rd, wr = M.rd, M.wr
def cell(x, y): return y * 12 + x
def raw_tick(n): pb.tick(n, True)
def tick(n):
    """advance exactly n game updates, using the ROM's own frame counter (robust to emulator tick boundaries)"""
    for _ in range(n):
        fc = rd('frame_count')
        for _ in range(4):
            pb.tick(1, True)
            if rd('frame_count') != fc: break
def press(btn, frames=3):
    pb.button_press(btn); tick(frames); pb.button_release(btn)
def flush(): pass   # direct pokes apply immediately (CPU is halted at the tick boundary)
def step_once():
    """advance to just after the next cell step (queued pokes are applied first)"""
    flush(); tick(CELL - rd('sub'))
def clear_field():
    for i in range(144): wr('grid', C_EMPTY, i)
    wr('n_angry', 0); wr('n_appear', 0); wr('n_flask', 0); wr('n_friend', 0); wr('dirty_rows', 0xFFF)
    wr('angry_spawn_timer', 60000); wr('mush_timer', 60000); wr('friend_target', 0); wr('friend_timer', 200)
fails = 0
def poke_angry(x, y):
    wr('grid', C_ANGRY, cell(x, y)); wr('gstate', 0, cell(x, y)); wr('gtimer', 200, cell(x, y))
    n = rd('n_angry'); wr('angry_list', cell(x, y), n); wr('n_angry', n + 1); wr('dirty_rows', 0xFFF)
def poke_flask(x, y, level):
    wr('grid', C_FLASK, cell(x, y)); wr('gstate', level, cell(x, y)); wr('gtimer', 100, cell(x, y))
    n = rd('n_flask'); wr('flask_list', cell(x, y), n); wr('n_flask', n + 1); wr('dirty_rows', 0xFFF)
def poke_friend(x, y):
    wr('grid', C_FRIEND, cell(x, y)); wr('n_friend', rd('n_friend') + 1); wr('dirty_rows', 0xFFF)
def poke_mush(x, y):
    wr('grid', C_MUSH, cell(x, y)); wr('dirty_rows', 0xFFF)
def check(name, cond, info=''):
    global fails
    print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else f'  [{info}]'))
    if not cond: fails += 1
def shot(tag): pb.screen.image.save(os.path.join(ROOT, 'build/shots', f'sim_{tag}.png'))
os.makedirs(os.path.join(ROOT, 'build/shots'), exist_ok=True)

raw_tick(200); pb.button_press('start'); raw_tick(5); pb.button_release('start')
for _ in range(400):
    if rd('state') == PS_PLAY and rd('px') == 5: break
    raw_tick(1)
check('playing', rd('state') == PS_PLAY, rd('state'))
clear_field(); flush()
px, py = rd('px'), rd('py'); check('start pos', (px, py) == (5, 7), (px, py))
# T1 collect the oppie ahead (facing up)
poke_friend(5, 6); step_once()
check('T1 collect -> trail 1', rd('trail_len') == 1 and rd('py') == 6, (rd('trail_len'), rd('py')))
check('T1 trail cell marked', rd('grid', cell(5, 7)) == C_TRAIL)
# T2 save on star row: move left along row 6 with star_row = 6
wr('star_row', 6); flush(); press('left'); step_once()
check('T2 moved left', (rd('px'), rd('py')) == (4, 6), (rd('px'), rd('py')))
shot('t2_before_drop'); press('b'); tick(2)
check('T2 saved 1, score 10', rd('saved') == 1 and rd('score') == 10 and rd('trail_len') == 0, (rd('saved'), rd('score')))
check('T2 flask counter 1', rd('flask_counter') == 1)
check('T2 star relocated', rd('star_row') != 6, rd('star_row'))
# T3 bad drop -> angry
poke_friend(3, 6); step_once(); wr('star_row', 0); flush(); press('b'); tick(2)
check('T3 bad drop -> angry at old head', rd('grid', cell(4, 6)) == C_ANGRY and rd('trail_len') == 0, rd('grid', cell(4, 6)))
wr('grid', C_EMPTY, cell(4, 6)); wr('n_angry', 0); wr('dirty_rows', 0xFFF)
# T4 jump over angry ahead: align to a cell boundary (this steps once: player now at (2,6) facing left)
flush(); tick(CELL - rd('sub'))
check('T4 aligned', rd('sub') == 0 and (rd('px'), rd('py')) == (2, 6), (rd('sub'), rd('px'), rd('py')))
poke_angry(1, 6); flush()
press('a', 2); tick(22)
check('T4 alive after jump', rd('state') == PS_PLAY, rd('state'))
check('T4 landed 2 cells on', (rd('px'), rd('py')) == (0, 6) and rd('jump') == 0, (rd('px'), rd('py'), rd('jump')))
check('T4 angry stunned', rd('gstate', cell(1, 6)) & 3 == 2, rd('gstate', cell(1, 6)))
shot('t4_after_jump'); wr('grid', C_EMPTY, cell(1, 6)); wr('n_angry', 0); wr('dirty_rows', 0xFFF)
# T5 turn down, gold flask ahead at (0,7)
press('down'); poke_flask(0, 7, 3); step_once()
check('T5 moved down onto flask', (rd('px'), rd('py')) == (0, 7), (rd('px'), rd('py')))
check('T5 powered, x2, mush ok, +friend', rd('power_timer') == 48 and rd('mult') == 2 and rd('power_mush') == 1 and rd('friend_target') == 1,
      (rd('power_timer'), rd('mult'), rd('power_mush'), rd('friend_target')))
shot('t5_powered')
# T6 kill: angry at (0,8)
poke_angry(0, 8); step_once()
check('T6 killed, score 30, chain 1', rd('score') == 30 and rd('chain') == 1 and rd('grid', cell(0, 8)) == C_EMPTY and rd('state') == PS_PLAY,
      (rd('score'), rd('chain'), rd('state')))
# T6b mushroom kill with power_mush
poke_mush(0, 9); step_once()
check('T6b mushroom killed, score 70', rd('score') == 70 and rd('state') == PS_PLAY, (rd('score'), rd('state')))
# T6c power expiry resets chain/mult
wr('power_timer', 1); wr('power_tick', 1); tick(2)
check('T6c power expired', rd('power_timer') == 0 and rd('mult') == 1 and rd('chain') == 0, (rd('power_timer'), rd('mult'), rd('chain')))
# T8 turn input: presses are queued for the next boundary; a d-pad roll (old dir still held) is not dropped
tick(CELL - rd('sub')); tick(2)               # sub = 2, moving down at x=0
press('right', 2)
check('T8 press queued, no immediate turn', rd('dir') == 2 and rd('next_dir') == 1, (rd('dir'), rd('next_dir')))
tick(CELL - rd('sub'))
check('T8 queued turn applied at boundary', rd('dir') == 1 and rd('next_dir') == 255, (rd('dir'), rd('next_dir')))
pb.button_press('right'); tick(2); pb.button_press('down'); tick(2); pb.button_release('right'); pb.button_release('down')
check('T8 roll with old dir held is registered', rd('next_dir') == 2, rd('next_dir'))
tick(CELL - rd('sub'))
check('T8 roll turn applied', rd('dir') == 2, rd('dir'))
press('left', 2); tick(CELL - rd('sub'))      # back to x=0 for T7
# T7 death: angry ahead while unpowered
poke_angry(rd('px') + (0 if rd('dir') != 1 else 1), rd('py') + (1 if rd('dir') == 2 else 0)); step_once()
check('T7 dead', rd('state') == PS_DEAD, rd('state'))
tick(100); shot('t7_gameover')
pb.stop(save=False)
print('FAILS:', fails); sys.exit(1 if fails else 0)
