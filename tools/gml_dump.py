#!/usr/bin/env python3
"""Minimal GameMaker (bytecode 17) disassembler for reading constants out of UFO 50's data.win.
usage: gml_dump.py <substring of code entry name> [...]    e.g. gml_dump.py o27_Player_Create o27_Player_Step
Reference-only tool; prints opcodes, resolved variable/function names and numeric constants."""
import os, struct, sys
GAME = os.path.expanduser('~/.steam/debian-installation/steamapps/common/UFO 50')
d = open(os.path.join(GAME, 'data.win'), 'rb').read()
u32 = lambda o: struct.unpack_from('<I', d, o)[0]
i32 = lambda o: struct.unpack_from('<i', d, o)[0]
u16 = lambda o: struct.unpack_from('<H', d, o)[0]
i16 = lambda o: struct.unpack_from('<h', d, o)[0]
def chunks():
    total = u32(4); p = 8; c = {}
    while p < 8 + total:
        c[d[p:p+4].decode()] = (p + 8, u32(p + 4)); p += 8 + u32(p + 4)
    return c
C = chunks()
def rstr(ptr): return d[ptr:ptr + u32(ptr - 4)].decode('utf-8', 'replace')
# strings by index (for push.s)
so, ss = C['STRG']; sn = u32(so)
strings = [rstr(u32(so + 4 + 4 * i) + 4) for i in range(sn)]
# variable / function occurrence chains -> address -> name
names = {}
def walk(first, count, name, is_func):
    # variables: `first` is the instruction address, operand at +4
    # functions: `first` is the operand address, the call instruction is at -4
    a = first
    for _ in range(count):
        if a <= 0 or a >= len(d): break
        if is_func:
            names[a - 4] = name; op = u32(a)
        else:
            names[a] = name; op = u32(a + 4)
        nxt = op & 0xFFFFFF
        if nxt == 0: break
        a += nxt
vo, vs = C['VARI']; p = vo + 12
while p + 20 <= vo + vs:
    nm = rstr(u32(p)); cnt = i32(p + 12); first = i32(p + 16)
    if cnt > 0 and first > 0: walk(first, cnt, nm, False)
    p += 20
fo, fs = C['FUNC']; fn = u32(fo); p = fo + 4
for _ in range(fn):
    nm = rstr(u32(p)); cnt = i32(p + 4); first = i32(p + 8)
    if cnt > 0 and first > 0: walk(first, cnt, nm, True)
    p += 12
# asset names for pushref (break -11 followed by a ref word: type in bits 24-31, index in bits 0-23)
def asset_list(chunk):
    o, sz = C[chunk]; n = u32(o); out = []
    for i in range(n):
        e = u32(o + 4 + 4 * i); out.append(rstr(u32(e)) if e else '?')
    return out
ASSETS = {0: asset_list('OBJT'), 1: asset_list('SPRT'), 2: asset_list('SOND'), 4: asset_list('BGND'), 6: asset_list('FONT') if u32(C['FONT'][0]) else []}
# code entries
co, cs = C['CODE']; cn = u32(co)
entries = []
for i in range(cn):
    e = u32(co + 4 + 4 * i)
    nm = rstr(u32(e)); ln = u32(e + 4); rel = i32(e + 12); off = u32(e + 16)
    entries.append((nm, ln, e + 12 + rel + off))
OPS = {0x07:'conv',0x08:'mul',0x09:'div',0x0A:'rem',0x0B:'mod',0x0C:'add',0x0D:'sub',0x0E:'and',0x0F:'or',0x10:'xor',0x11:'neg',0x12:'not',
       0x13:'shl',0x14:'shr',0x15:'cmp',0x45:'pop',0x84:'pushi',0x86:'dup',0x9C:'ret',0x9D:'exit',0x9E:'popz',0xB6:'b',0xB7:'bt',0xB8:'bf',
       0xB9:'pushenv',0xBA:'popenv',0xC0:'push',0xC1:'pushloc',0xC2:'pushglb',0xC3:'pushbltn',0xD9:'call',0x99:'callv',0xFF:'break'}
CMP = {1:'<',2:'<=',3:'==',4:'!=',5:'>=',6:'>'}
TYPES = {0:'d',1:'f',2:'i',3:'l',4:'b',5:'v',6:'s',15:'e'}
def disasm(name, ln, start):
    print('===', name, 'len', ln)
    a = start; end = start + ln
    while a < end:
        w = u32(a); op = w >> 24; t1 = (w >> 16) & 0xF; t2 = (w >> 20) & 0xF; lo = w & 0xFFFF
        mn = OPS.get(op, '?%02X' % op); text = mn; size = 4
        if mn in ('push', 'pushloc', 'pushglb', 'pushbltn', 'pushi'):
            if t1 == 0: text += ' %g' % struct.unpack_from('<d', d, a + 4)[0]; size = 12
            elif t1 == 1: text += ' %g' % struct.unpack_from('<f', d, a + 4)[0]; size = 8
            elif t1 == 2: text += ' %d' % i32(a + 4); size = 8
            elif t1 == 3: text += ' %d' % struct.unpack_from('<q', d, a + 4)[0]; size = 12
            elif t1 == 4: text += ' %s' % bool(u32(a + 4)); size = 8
            elif t1 == 5: text += ' ' + names.get(a, '?var'); size = 8
            elif t1 == 6: text += ' "%s"' % strings[u32(a + 4)] if u32(a + 4) < len(strings) else ' ?str'; size = 8
            elif t1 == 15: text += ' %d' % i16(a)
        elif mn == 'pop':
            text += '.%s%s %s' % (TYPES.get(t1, '?'), TYPES.get(t2, '?'), names.get(a, '?var')); size = 8
        elif mn == 'call':
            text += ' %s(%d)' % (names.get(a, '?func'), lo); size = 8
        elif mn in ('b', 'bt', 'bf', 'pushenv', 'popenv'):
            off = w & 0xFFFFFF
            if off & 0x800000: off -= 0x1000000
            text += ' -> +%d' % (off * 4)
        elif mn == 'cmp': text += ' ' + CMP.get((w >> 8) & 0xFF, '?')
        elif mn == 'break':
            v = i16(a); text += ' %d' % v
            if v == -11:
                ref = u32(a + 4); ty = ref >> 24; idx = ref & 0xFFFFFF
                lst = ASSETS.get(ty, []); text = 'pushref ' + ({0:'obj',1:'spr',2:'snd',4:'bg',6:'font'}.get(ty, 't%d' % ty)) + ':' + (lst[idx] if idx < len(lst) else str(idx)); size = 8
        print('  %06X  %s' % (a - start, text)); a += size
pats = sys.argv[1:]
for nm, ln, start in entries:
    if any(p in nm for p in pats): disasm(nm, ln, start)
