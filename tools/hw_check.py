#!/usr/bin/env python3
"""Real-hardware check: runs the ROM in SameBoy (accurate PPU timing) and counts every write the hardware
would drop - VRAM or tile-map writes while the PPU is drawing (mode 3), CGB palette writes while the
palettes are locked - with where and on which scanline. PyBoy performs those writes, so the other tests
cannot see this. A dropped attribute write is a cell in the wrong palette until something redraws it.
usage: hw_check.py [rom] [scenario ...]    scenarios: menus play stress power drop pads ending (default: all)
Compiles tools/sameboy/hwlib.c against ~/.local/opt/SameBoy-1.0.3 into build/sameboy/libhw.so on first use.
Exit status 1 if anything was dropped."""
import ctypes, os, random, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from gbmem import Mem
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SB = os.path.expanduser('~/.local/opt/SameBoy-1.0.3')
BOOT = os.environ.get('SAMEBOY_BOOT', os.path.join(SB, 'build/bin/BootROMs/cgb_boot.bin'))
LIB = os.path.join(ROOT, 'build/sameboy/libhw.so')
SRC = os.path.join(ROOT, 'tools/sameboy/hwlib.c')
args = sys.argv[1:]
rom = args.pop(0) if args and args[0].endswith('.gbc') else os.path.join(ROOT, 'build/magicgarden.gbc')
ALL = ['menus', 'play', 'stress', 'power', 'drop', 'pads', 'ending']
scenarios = args or ALL

if not os.path.exists(LIB) or os.path.getmtime(LIB) < os.path.getmtime(SRC):
    os.makedirs(os.path.dirname(LIB), exist_ok=True)
    core = [os.path.join(SB, 'Core', f) for f in sorted(os.listdir(os.path.join(SB, 'Core'))) if f.endswith('.c')
            and not any(x in f for x in ('debugger', 'cheat', 'rewind', 'disassembler', 'symbol_hash'))]
    subprocess.run(['gcc', '-O2', '-std=gnu11', '-fPIC', '-shared', '-w', '-I' + os.path.join(SB, 'Core'), '-DGB_INTERNAL',
                    '-D_GNU_SOURCE', '-DGB_DISABLE_DEBUGGER', '-DGB_DISABLE_CHEATS', '-DGB_DISABLE_CHEAT_SEARCH',
                    '-DGB_DISABLE_REWIND', '-DGB_VERSION="1.0.3"', '-DGB_COPYRIGHT_YEAR="2025"', '-o', LIB, SRC] + core + ['-lm'],
                   check=True)
L = ctypes.CDLL(LIB)
L.hw_rd.restype = ctypes.c_uint8; L.hw_vram.restype = ctypes.c_uint8; L.hw_frame_no.restype = ctypes.c_uint32
L.hw_counts.restype = ctypes.c_uint32
KEYS = {'right': 0, 'left': 1, 'up': 2, 'down': 3, 'a': 4, 'b': 5, 'select': 6, 'start': 7}

class Bus:   # what gbmem.Mem expects of a PyBoy instance
    class _M:
        def __getitem__(self, a): return L.hw_rd(a)
        def __setitem__(self, a, v): L.hw_wr(a, v)
    memory = _M()
C_EMPTY, C_FRIEND, C_TRAIL, C_ANGRY, C_MUSH, C_FLASK, C_APP_A, C_APP_M = range(8)
PS_WAIT, PS_PLAY, PS_DEAD, PS_WIN = range(4)
DX = [0, 1, 0, -1]; DY = [-1, 0, 1, 0]; NAME = ['up', 'right', 'down', 'left']

def boot():
    r = L.hw_init(rom.encode(), BOOT.encode())
    if r: sys.exit(f'SameBoy init failed ({r}): boot ROM {BOOT}')
    M = Mem(Bus(), rom.replace('.gbc', '.noi'))
    return M.rd, M.wr
def frames(n):
    for _ in range(n): L.hw_frame()
def press(k, n=3):
    L.hw_key(KEYS[k], 1); frames(n); L.hw_key(KEYS[k], 0)

def report(name):
    vb, pb_, vw = ctypes.c_uint32(), ctypes.c_uint32(), ctypes.c_uint32()
    n = L.hw_counts(ctypes.byref(vb), ctypes.byref(pb_), ctypes.byref(vw))
    where = {}
    for k in range(n):
        f, a, ly, v, kind = ctypes.c_uint32(), ctypes.c_uint16(), ctypes.c_uint8(), ctypes.c_uint8(), ctypes.c_uint8()
        L.hw_event(k, *(ctypes.byref(x) for x in (f, a, ly, v, kind)))
        a, kd = a.value, kind.value
        if kd == 2: what = 'palette data'
        elif a < 0x9800: what = f'tile data (bank {kd >> 4})'
        else:
            row, col = (a - 0x9800) // 32, (a - 0x9800) % 32
            area = 'playfield' if 3 <= row < 15 and 4 <= col < 16 else 'HUD' if row >= 15 or row < 3 else 'sidebar'
            what = f'tile map {"attributes" if kd >> 4 else "tiles"} ({area})'
        w = where.setdefault(what, [0, 255, 0, set()]); w[0] += 1; w[1] = min(w[1], ly.value); w[2] = max(w[2], ly.value); w[3].add(f.value)
    print(f'{name}: {L.hw_frame_no()} frames, {vw.value} VRAM writes, {vb.value} dropped VRAM writes, {pb_.value} dropped palette writes')
    for what, (c, lo, hi, fs) in sorted(where.items(), key=lambda kv: -kv[1][0]):
        print(f'    {c:6d} x {what}, on {len(fs)} frames, scanlines {lo}-{hi}')
    shot = os.path.join(ROOT, 'build/sameboy', f'hw_{name}.ppm'); L.hw_screen(shot.encode())
    return vb.value + pb_.value

def start_game(rd):
    frames(230); press('start', 5)
    for _ in range(600):
        if rd('state') == PS_WAIT and rd('px') == 1: break
        frames(1)
    frames(30); press('down', 3)

def tick(rd, n):   # n game updates (the frame counter, not emulator frames)
    for _ in range(n):
        fc = rd('frame_count')
        for _ in range(4):
            L.hw_frame()
            if rd('frame_count') != fc: break

def bot(rd, n, rng):
    """plays for n frames: dodges, collects, drops on the pad; restarts from the title after a game over"""
    deaths = 0
    for _ in range(n):
        st = rd('state')
        if st == PS_DEAD:
            deaths += 1; frames(200); press('start', 5); frames(60); start_game_from_title(rd); continue
        if rd('sub') == 0 and rd('z') == 0 and st == PS_PLAY:
            x, y, d = rd('px'), rd('py'), rd('dir'); powered = rd('power_timer') > 0
            pad = [rd('pad_rows', r) for r in range(12)]; tl = rd('trail_len')
            on_pad = lambda c: (pad[c // 12] >> (c % 12)) & 1
            if tl and rd('pad_flash') == 0 and sum(on_pad(rd('trail', k)) for k in range(tl)) * 2 > tl: press('b', 1)
            best = None
            for dd in range(4):
                if dd == (d + 2) % 4: continue
                nx, ny = x + DX[dd], y + DY[dd]
                if not (0 <= nx < 12 and 0 <= ny < 12): continue
                g = rd('grid', ny * 12 + nx)
                ok = g in (C_EMPTY, C_FRIEND, C_FLASK, C_APP_A, C_APP_M) or (powered and g == C_ANGRY)
                if not ok: continue
                sc = (5 if g in (C_FRIEND, C_FLASK) else 0) + (1 if dd == d else 0) + rng.random()
                if best is None or sc > best[0]: best = (sc, dd)
            if best and best[1] != d: press(NAME[best[1]], 1); continue
            if not best: press('a', 1); continue
        L.hw_frame()
    return deaths
def start_game_from_title(rd):
    press('start', 5)
    for _ in range(600):
        if rd('state') == PS_WAIT and rd('px') == 1: break
        frames(1)
    frames(30); press('down', 3)

def field(rd, wr, na, nt):
    """the stress_test field: player parked at (0,0), a 48-oppie trail, angry oppies in rows 6-11, flasks"""
    for i in range(144):
        wr('grid', C_EMPTY, i); wr('gstate', 0, i)
        if 'trail_under' in rd.__self__.OFF: wr('trail_under', 0, i)
    wr('n_angry', 0); wr('n_appear', 0); wr('n_flask', 0); wr('n_friend', 0); wr('friend_target', 0); wr('potion_delay', 0)
    wr('px', 0); wr('py', 0); wr('dir', 1); wr('dir_choice', 1); wr('z', 0)
    cells = [y * 12 + x for y in range(2, 6) for x in range(12)][:nt]
    for k, c in enumerate(cells): wr('grid', C_TRAIL, c); wr('trail', c, k)
    wr('trail_len', len(cells))
    n = 0
    for c in range(72, 144):
        if n >= na or c % 3 == 0: continue
        wr('grid', C_ANGRY, c); wr('gstate', 0, c); wr('gtimer', 1 + (c * 7) % 128, c); wr('angry_list', c, n); n += 1
    wr('n_angry', n)
    for k, c in enumerate([15, 19, 22]):
        wr('grid', C_FLASK, c); wr('gstate', k, c); wr('gtimer', 100, c); wr('flask_list', c, k); wr('flask_fall', 0, k)
    wr('n_flask', 3); wr('pad_life', 30000); wr('dirty_rows', 0xFFF)

def run(name):
    rd, wr = boot(); rng = random.Random(1)
    if name == 'menus':
        frames(400); press('down'); press('start', 5); frames(120); press('b'); frames(120)
        start_game_from_title(rd); frames(120)
    elif name == 'play':
        start_game(rd)
        d = bot(rd, 6000, rng); print(f'  (bot: {d} deaths, saved {rd("saved")}, score {rd("score")})')
    elif name in ('stress', 'power', 'drop'):
        start_game(rd); tick(rd, 20); field(rd, wr, 40, 48)
        if name == 'power': wr('power_timer', 30000); wr('mult', 3)
        if name == 'drop':
            for y in range(12): wr('pad_rows', 0x3F if 2 <= y <= 5 else 0, y)
        for f in range(900):
            wr('sub', 5)
            if name == 'drop' and f == 10: press('b', 1)
            if name == 'power' and f % 7 == 0:   # score pop-ups, as a kill chain makes them
                k = f % 6; base = rd.__self__.base + rd.__self__.OFF['pops'] + k * 7
                for j, v in enumerate((5, 5, 60, 0x39, 0x30, 0, 0)): L.hw_wr(base + j, v)
                wr('pop_dirty', rd('pop_dirty') | (1 << k))
            if f % 150 == 75: wr('palette_set', (f // 150) & 3)   # rank-up palette loads
            if rd('state') != PS_PLAY: print('  player died at', f); break
            tick(rd, 1)
    elif name == 'pads':   # the star pad moves: every row is redrawn with new tiles and palettes
        start_game(rd); tick(rd, 20); field(rd, wr, 30, 24)
        for f in range(1200):
            wr('sub', 5)
            if f % 40 == 0: wr('pad_life', 1)
            if f % 120 == 60: wr('pad_flash', 2)
            if rd('state') != PS_PLAY: print('  player died at', f); break
            tick(rd, 1)
    elif name == 'ending':
        start_game(rd); tick(rd, 20); field(rd, wr, 0, 6)
        for y in range(12): wr('pad_rows', 0xFFF if 2 <= y <= 5 else 0, y)
        wr('saved', 199); wr('pad_flash', 0); tick(rd, 2); press('b', 1)
        frames(3000)
        for _ in range(3): press('a', 3); frames(200)
    return report(name)

total = 0
for s in scenarios: total += run(s)
print('dropped writes in total:', total)
sys.exit(1 if total else 0)
