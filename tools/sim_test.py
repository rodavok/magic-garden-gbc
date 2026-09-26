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
PS_READY, PS_PLAY, PS_DEAD, PS_WIN = range(4)   # PS_READY == PS_WAIT

pb = PyBoy(rom, window="null", cgb=True); pb.set_emulation_speed(0)
M = Mem(pb, rom.replace('.gbc', '.noi')); rd, wr = M.rd, M.wr
CELL = M.defs['CELL_UNITS']
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
    """advance to just after the next cell arrival"""
    flush(); tick(CELL - rd('sub'))
def clear_field():
    for i in range(144): wr('grid', C_EMPTY, i)
    wr('n_angry', 0); wr('n_appear', 0); wr('n_flask', 0); wr('n_friend', 0); wr('dirty_rows', 0xFFF)
    wr('friend_target', 0); wr('potion_delay', 0)
fails = 0
def poke_angry(x, y):
    wr('grid', C_ANGRY, cell(x, y)); wr('gstate', 0, cell(x, y)); wr('gtimer', 250, cell(x, y))
    n = rd('n_angry'); wr('angry_list', cell(x, y), n); wr('n_angry', n + 1); wr('dirty_rows', 0xFFF)
def poke_flask(x, y, level):
    wr('grid', C_FLASK, cell(x, y)); wr('gstate', level, cell(x, y)); wr('gtimer', 100, cell(x, y))
    n = rd('n_flask'); wr('flask_list', cell(x, y), n); wr('flask_fall', 0, n); wr('n_flask', n + 1); wr('dirty_rows', 0xFFF)
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
    if rd('state') == PS_READY and rd('px') == 1: break
    raw_tick(1)
raw_tick(25)   # let the start-of-game screen wipe finish so the main loop reads input again
check('waiting at (1,1)', rd('state') == PS_READY and (rd('px'), rd('py')) == (1, 1), (rd('state'), rd('px'), rd('py')))
clear_field(); flush()
def set_pad(rows):
    for y in range(12): wr('pad_rows', rows.get(y, 0), y)
    wr('pad_life', 30000); wr('pad_flash', 0); wr('dirty_rows', 0xFFF)
set_pad({})
# start by pressing Down: the run begins, moving down column 1
pb.button_press('down'); tick(2); pb.button_release('down')
check('started moving down', rd('state') == PS_PLAY and rd('dir') == 2, (rd('state'), rd('dir')))
# T1 collect the oppie below (cell-aligned pickup)
poke_friend(1, 2); wr('friend_target', 0); step_once()
check('T1 collect -> trail 1', rd('trail_len') == 1 and (rd('px'), rd('py')) == (1, 2), (rd('trail_len'), rd('px'), rd('py')))
check('T1 trail cell marked', rd('grid', cell(1, 1)) == C_TRAIL)
# T2 save: pad = row 2 only (trail is at (1,1) after the next step? no: trail follows one cell behind),
# so turn right along row 2: after one step the trail sits at (1,2) which is on the pad
set_pad({2: 0xFFF}); press('right'); step_once()
check('T2 moved right', (rd('px'), rd('py')) == (2, 2), (rd('px'), rd('py')))
press('b'); tick(12)
check('T2 saved 1, score 10', rd('saved') == 1 and rd('score') == 10 and rd('trail_len') == 0, (rd('saved'), rd('score')))
check('T2 flask counter 1', rd('flask_counter') == 1)
check('T2 pad flashing', rd('pad_flash') > 0, rd('pad_flash'))
tick(35)
check('T2 new pad made', rd('pad_flash') == 0 and rd('pad_life') > 900, (rd('pad_flash'), rd('pad_life')))
set_pad({})
# T3 bad drop -> angry at the trail cell (player keeps moving right along row 2)
tick(CELL - rd('sub')); x3 = rd('px')
poke_friend(x3 + 1, 2); step_once(); press('b'); tick(12)
check('T3 bad drop -> angry at old head', rd('grid', cell(x3, 2)) == C_ANGRY and rd('trail_len') == 0 and rd('n_angry') == 1, (rd('grid', cell(x3, 2)), rd('n_angry')))
wr('grid', C_EMPTY, cell(x3, 2)); wr('n_angry', 0); wr('dirty_rows', 0xFFF)
DXY = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}
NAME = {0: 'up', 1: 'right', 2: 'down', 3: 'left'}
def ahead(k=1):
    dx, dy = DXY[rd('dir')]; return rd('px') + dx * k, rd('py') + dy * k
def perp():
    """a perpendicular direction with room to run"""
    d = rd('dir')
    if d in (0, 2): return 1 if rd('px') < 6 else 3
    return 2 if rd('py') < 6 else 0
def align():
    tick(CELL - rd('sub'))
def turn_to(d):
    align(); press(NAME[d], 2); tick(1)
    assert rd('dir') == d, ('turn failed', rd('dir'), d)
# head down a column with room below
turn_to(perp())
# T4 jump over an enemy in the next cell: press at a boundary (window is -3..+6 units); land in the cell after
align(); x0, y0 = rd('px'), rd('py'); ex, ey = ahead(1)
check('T4 aligned', rd('sub') == 0, rd('sub'))
poke_angry(ex, ey); flush()
press('a', 1); tick(29)
check('T4 airborne then landed', rd('z') == 0 and rd('state') == PS_PLAY and (rd('px'), rd('py')) == (ex, ey) and rd('sub') == 14, (rd('z'), rd('state'), rd('px'), rd('py'), rd('sub')))
check('T4 angry stunned by the pass', rd('gstate', cell(ex, ey)) & 3 == 3, rd('gstate', cell(ex, ey)))
shot('t4_after_jump')
wr('grid', C_EMPTY, cell(ex, ey)); wr('n_angry', 0); wr('dirty_rows', 0xFFF)
# T5 gold flask on the floor in the next cell: picked up 2 units into the approach
align(); fx, fy = ahead(1)
poke_flask(fx, fy, 3); wr('flask_fall', 0, 0); flush(); tick(3)
check('T5 powered early in the approach', rd('power_timer') > 470 and rd('mult') == 2 and rd('power_mush') == 1 and rd('friend_target') == 1,
      (rd('power_timer'), rd('mult'), rd('power_mush'), rd('friend_target')))
shot('t5_powered')
# T6 kill: enemy in the next cell is hit 6 units into the approach: (10 + 0) x2 = 20
align(); ex, ey = ahead(1); poke_angry(ex, ey); flush(); tick(7)
check('T6 killed, score 30, chain 1', rd('score') == 30 and rd('chain') == 1 and rd('n_angry') == 0 and rd('state') == PS_PLAY,
      (rd('score'), rd('chain'), rd('n_angry'), rd('state')))
# T6b mushroom kill with power_mush: second kill scores (10 + 10) x2 = 40
turn_to(perp()); align(); mx, my = ahead(1); poke_mush(mx, my); flush(); tick(7)
check('T6b mushroom killed, score 70', rd('score') == 70 and rd('state') == PS_PLAY, (rd('score'), rd('state')))
# T6c power expiry resets chain/mult and re-arms the spawn timer
wr('power_timer', 1); tick(2)
check('T6c power expired', rd('power_timer') == 0 and rd('mult') == 1 and rd('chain') == 0 and rd('angry_spawn_timer') <= 240, (rd('power_timer'), rd('mult'), rd('chain'), rd('angry_spawn_timer')))
# T8 turn input: a late turn within 2 units snaps back and applies at once; later presses queue for the boundary
align(); tick(1); d1 = perp()
press(NAME[d1], 2)
check('T8 late turn applied at once', rd('dir') == d1 and rd('sub') <= 3, (rd('dir'), rd('sub'), d1))
tick(8 - rd('sub')); d2 = perp()
press(NAME[d2], 2)
check('T8 later press queued', rd('dir') == d1 and rd('dir_choice') == d2, (rd('dir'), rd('dir_choice'), d2))
tick(CELL - rd('sub')); tick(1)
check('T8 queued turn applied at boundary', rd('dir') == d2, (rd('dir'), d2))
d3 = perp()
pb.button_press(NAME[d2]); tick(2); pb.button_press(NAME[d3]); tick(2); pb.button_release(NAME[d2]); pb.button_release(NAME[d3])
check('T8 roll with old dir held is registered', rd('dir_choice') == d3, (rd('dir_choice'), d3))
# T9/T10 an enemy that hops into the cell the player is leaving (airborne) keeps it: the trail oppie goes under
# it, as the original's followers pass over enemies. Writing the trail over it left the enemy listed but
# invisible, and its next hop blanked whatever held that cell by then.
def trail_over_enemy():
    turn_to(perp()); align()
    fx, fy = ahead(1); poke_friend(fx, fy); wr('friend_target', 0); step_once()   # collect: trail of 1
    px, py = rd('px'), rd('py')
    press('a', 1); poke_angry(px, py)   # jump, and an enemy lands in the cell being left
    step_once()
    c = cell(px, py)
    check('T9 enemy keeps the cell, trail oppie under it', rd('grid', c) == C_ANGRY and rd('trail_under', c) == 1
          and rd('trail_len') == 1 and rd('trail', 0) == c and rd('n_angry') == 1,
          (rd('grid', c), rd('trail_under', c), rd('trail_len'), rd('trail', 0), rd('n_angry')))
    return c
def no_ghosts():
    friends = sum(rd('grid', i) == C_FRIEND for i in range(144))
    listed = [rd('angry_list', k) for k in range(rd('n_angry'))]
    return friends == rd('n_friend') and all(rd('grid', i) == C_ANGRY for i in listed) and len(set(listed)) == len(listed)
c = trail_over_enemy()
tick(15 - rd('sub')); press('b', 1)   # landed: drop with the only trail oppie covered
check('T9 drop leaves the covering enemy alone', rd('grid', c) == C_ANGRY and rd('gstate', c) & 3 == 3 and rd('n_angry') == 1
      and rd('trail_under', c) == 0 and rd('trail_len') == 0 and no_ghosts(), (rd('grid', c), rd('gstate', c), rd('n_angry'), rd('trail_under', c)))
tick(12); wr('grid', C_EMPTY, c); wr('n_angry', 0); wr('dirty_rows', 0xFFF)
c = trail_over_enemy()
d = (rd('dir') + 1) & 3
t = cell(c % 12 + DXY[d][0], c // 12 + DXY[d][1])
if not (0 <= c % 12 + DXY[d][0] < 12 and 0 <= c // 12 + DXY[d][1] < 12):
    d = (d + 2) & 3; t = cell(c % 12 + DXY[d][0], c // 12 + DXY[d][1])
wr('gstate', 1 | (d << 2), c); wr('gtimer', 1, c); tick(1)   # A_LOOK, hops now
check('T10 enemy hops off, the trail oppie shows again', rd('grid', c) == C_TRAIL and rd('trail_under', c) == 0 and rd('grid', t) == C_ANGRY
      and rd('angry_list', 0) == t and rd('hop_sprites') == 1, (rd('grid', c), rd('trail_under', c), rd('grid', t), rd('hop_sprites')))
tick(16)
check('T10 hop sprite released, trail moved on', rd('hop_sprites') == 0 and rd('grid', c) == C_EMPTY and no_ghosts(), (rd('hop_sprites'), rd('grid', c)))
wr('grid', C_EMPTY, t); wr('n_angry', 0); wr('dirty_rows', 0xFFF)
# T7 death: unpowered walk into an enemy in the next cell
align(); tick(1); ex, ey = ahead(1); poke_angry(ex, ey); flush(); tick(8)
check('T7 dead', rd('state') == PS_DEAD, rd('state'))
tick(100); shot('t7_gameover')
pb.stop(save=False)
print('FAILS:', fails); sys.exit(1 if fails else 0)
