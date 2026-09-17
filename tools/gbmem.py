"""Shared helper: game_t layout from include/game.h (SDCC packs structs) + _G address from the .noi file."""
import re, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SZ = {'uint8_t': 1, 'int8_t': 1, 'uint16_t': 2, 'int16_t': 2, 'uint32_t': 4}

def layout(noi_path=None):
    hdr = open(os.path.join(ROOT, 'include/game.h')).read()
    defs = {m.group(1): int(m.group(2)) for m in re.finditer(r'#define (\w+)\s+(\d+)', hdr)}
    body = hdr[hdr.index('typedef struct {') + 16: hdr.index('} game_t;')]
    OFF, SIZE, off = {}, {}, 0
    for line in body.split('\n'):
        line = re.sub(r'/\*.*?\*/', '', line).strip()
        if not line or not line.endswith(';'): continue
        typ, rest = line[:-1].split(None, 1)
        for decl in rest.split(','):
            m = re.match(r'(\w+)(?:\[(\w+)\])?', decl.strip())
            n = m.group(2); cnt = 1 if n is None else int(defs.get(n, n))
            OFF[m.group(1)] = off; SIZE[m.group(1)] = SZ[typ]; off += SZ[typ] * cnt
    noi = open(noi_path or os.path.join(ROOT, 'build/magicgarden.noi')).read()
    base = int(re.search(r'DEF _G 0x([0-9A-Fa-f]+)', noi).group(1), 16)
    OFF['__end__'] = off; SIZE['__end__'] = 0
    return base, OFF, SIZE, defs

class Mem:
    def __init__(self, pb, noi_path=None):
        self.pb = pb; self.base, self.OFF, self.SIZE, self.defs = layout(noi_path)
    def rd(self, name, i=0):
        a = self.base + self.OFF[name] + i * self.SIZE[name]; v = 0
        for k in range(self.SIZE[name]): v |= self.pb.memory[a + k] << (8 * k)
        return v
    def wr(self, name, val, i=0):
        a = self.base + self.OFF[name] + i * self.SIZE[name]
        for k in range(self.SIZE[name]): self.pb.memory[a + k] = (val >> (8 * k)) & 0xFF

class HookedMem(Mem):
    """Consistent reads/writes: state is snapshotted (and queued writes applied) each time the ROM
    enters wait_vbl_done, i.e. after a frame's game logic has fully run."""
    def __init__(self, pb, noi_path=None, symbol='_wait_vbl_done'):
        super().__init__(pb, noi_path)
        noi = open(noi_path or os.path.join(ROOT, 'build/magicgarden.noi')).read()
        addr = int(re.search(r'DEF %s 0x([0-9A-Fa-f]+)' % symbol, noi).group(1), 16)
        self.size = self.OFF['__end__']
        self.snap = bytes(self.size); self.queue = []; self.hits = 0
        pb.hook_register(0, addr, self._hook, None)
    def _hook(self, _ctx):
        for a, v in self.queue: self.pb.memory[a] = v
        self.queue = []
        self.snap = bytes(self.pb.memory[self.base:self.base + self.size]); self.hits += 1
    def rd(self, name, i=0):
        o = self.OFF[name] + i * self.SIZE[name]; v = 0
        for k in range(self.SIZE[name]): v |= self.snap[o + k] << (8 * k)
        return v
    def wr(self, name, val, i=0):
        a = self.base + self.OFF[name] + i * self.SIZE[name]
        for k in range(self.SIZE[name]): self.queue.append((a + k, (val >> (8 * k)) & 0xFF))
