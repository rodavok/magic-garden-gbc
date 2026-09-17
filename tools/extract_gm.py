#!/usr/bin/env python3
"""Extract Magic Garden (internal game 27) reference assets from a local UFO 50 install.
Reads GameMaker data.win + Textures/*.yytex (bz2-wrapped QOI) + audiogroup_*.dat.
Output: reference/sprites/<name>_<frame>.png, reference/audio/*.wav|ogg
Reference use only; all assets are (c) Mossmouth."""
import bz2, os, struct, sys, glob
from PIL import Image

GAME = os.path.expanduser('~/.steam/debian-installation/steamapps/common/UFO 50')
OUT = os.path.join(os.path.dirname(__file__), '..', 'reference')
PREFIXES = ('s27_', 'bgTitle_MagicGarden', 'sSaveIconGarden')

d = open(os.path.join(GAME, 'data.win'), 'rb').read()
u32 = lambda o: struct.unpack_from('<I', d, o)[0]
i32 = lambda o: struct.unpack_from('<i', d, o)[0]
u16 = lambda o: struct.unpack_from('<H', d, o)[0]

def chunks_of(buf):
    total = struct.unpack_from('<I', buf, 4)[0]; p = 8; c = {}
    while p < 8 + total:
        name = buf[p:p+4].decode(); size = struct.unpack_from('<I', buf, p+4)[0]
        c[name] = (p+8, size); p += 8 + size
    return c
C = chunks_of(d)
def rstr(ptr): return d[ptr:ptr+u32(ptr-4)].decode('utf-8', 'replace')

# ---- QOI decode: GameMaker uses the pre-1.0 draft QOI opcodes ('fioq' header) ----
def qoi_decode(buf):
    assert buf[:4] == b'fioq', buf[:4]
    w, h, ln = struct.unpack_from('<HHI', buf, 4)
    n = w*h; px = bytearray(n*4); idx = [(0,0,0,0)]*64
    r=g=b=0; a=255; p=12; o=0; i=0; run=0
    while i < n:
        if run > 0:
            run -= 1
        else:
            b1 = buf[p]; p += 1
            if (b1 & 0xC0) == 0x00: r,g,b,a = idx[b1 & 0x3F]
            elif (b1 & 0xE0) == 0x40: run = b1 & 0x1F
            elif (b1 & 0xE0) == 0x60: b2 = buf[p]; p += 1; run = (((b1 & 0x1F) << 8) | b2) + 32
            elif (b1 & 0xC0) == 0x80:
                r=(r+((b1>>4)&3)-2)&255; g=(g+((b1>>2)&3)-2)&255; b=(b+(b1&3)-2)&255
            elif (b1 & 0xE0) == 0xC0:
                b2 = buf[p]; p += 1
                r=(r+(b1&0x1F)-16)&255; g=(g+(b2>>4)-8)&255; b=(b+(b2&0x0F)-8)&255
            elif (b1 & 0xF0) == 0xE0:
                b2 = buf[p]; b3 = buf[p+1]; p += 2
                r=(r+(((b1&0x0F)<<1)|(b2>>7))-16)&255; g=(g+((b2&0x7C)>>2)-16)&255
                b=(b+(((b2&0x03)<<3)|((b3&0xE0)>>5))-16)&255; a=(a+(b3&0x1F)-16)&255
            elif (b1 & 0xF0) == 0xF0:
                if b1 & 8: r = buf[p]; p += 1
                if b1 & 4: g = buf[p]; p += 1
                if b1 & 2: b = buf[p]; p += 1
                if b1 & 1: a = buf[p]; p += 1
            idx[(r^g^b^a) & 63] = (r,g,b,a)
        px[o]=r; px[o+1]=g; px[o+2]=b; px[o+3]=a; o += 4; i += 1
    return Image.frombytes('RGBA', (w, h), bytes(px))

# ---- TXTR: map texture index -> yytex file (external) by block size ----
to, ts = C['TXTR']; tn = u32(to)
tex_files = {os.path.getsize(f): f for f in glob.glob(os.path.join(GAME, 'Textures', '*.yytex'))}
tex_info = {}
for i in range(tn):
    e = u32(to+4+4*i)
    blocksize, w, h, dataptr = u32(e+8), u32(e+12), u32(e+16), u32(e+24)
    tex_info[i] = (blocksize, w, h, dataptr)
_page_cache = {}
def page(i):
    if i in _page_cache: return _page_cache[i]
    blocksize, w, h, dataptr = tex_info[i]
    if blocksize in tex_files:
        raw = open(tex_files[blocksize], 'rb').read()
    else:
        raw = d[dataptr:dataptr+blocksize]
    if raw[:4] == b'2zoq':
        buf = bz2.decompress(raw[12:]); img = qoi_decode(buf)
    elif raw[:4] == b'fioq': img = qoi_decode(raw)
    else:
        import io; img = Image.open(io.BytesIO(raw)).convert('RGBA')
    _page_cache[i] = img; return img

# ---- TPAG ----
tpo, tps = C['TPAG']
def tpag(ptr):
    f = struct.unpack_from('<11H', d, ptr)
    return dict(sx=f[0], sy=f[1], sw=f[2], sh=f[3], dx=f[4], dy=f[5], dw=f[6], dh=f[7], bw=f[8], bh=f[9], tex=f[10])

# ---- SPRT ----
so, ss = C['SPRT']; sn = u32(so)
os.makedirs(os.path.join(OUT, 'sprites'), exist_ok=True)
report = []
for i in range(sn):
    e = u32(so+4+4*i)
    if not e: continue
    name = rstr(u32(e))
    if not name.startswith(PREFIXES): continue
    w, h = u32(e+4), u32(e+8)
    ox, oy = i32(e+48), i32(e+52)
    p = e + 56
    if i32(p) == -1:
        ver, typ = u32(p+4), u32(p+8); spd = struct.unpack_from('<f', d, p+12)[0]; spdtype = u32(p+16)
        p += 20
        if ver >= 2: p += 4
        if ver >= 3: p += 4
    else:
        ver, typ, spd, spdtype = 0, 0, 0.0, 0
    cnt = u32(p); ptrs = [u32(p+4+4*k) for k in range(cnt)]
    assert all(tpo <= q < tpo+tps for q in ptrs), (name, ptrs)
    for k, q in enumerate(ptrs):
        t = tpag(q)
        src = page(t['tex']).crop((t['sx'], t['sy'], t['sx']+t['sw'], t['sy']+t['sh']))
        frame = Image.new('RGBA', (w, h), (0,0,0,0))
        frame.paste(src, (t['dx'], t['dy']))
        frame.save(os.path.join(OUT, 'sprites', f'{name}_{k:02d}.png'))
    report.append(f'{name}\t{w}x{h}\tframes={cnt}\torigin=({ox},{oy})\tspeed={spd:g}({"fps" if spdtype==0 else "frames/frame"})\ttex={t["tex"]}')
open(os.path.join(OUT, 'sprites', 'INDEX.txt'), 'w').write('\n'.join(report) + '\n')
print('\n'.join(report))

# ---- Objects ----
oo, osz = C['OBJT']; on = u32(oo)
objs = [rstr(u32(u32(oo+4+4*i))) for i in range(on)]
objs27 = [o for o in objs if o.startswith('o27') or o.startswith('obj27')]
open(os.path.join(OUT, 'objects_27.txt'), 'w').write('\n'.join(objs27) + '\n')
print('objects:', objs27)

# ---- Audio: AGRP names, and group-29 (bgm27) sounds ----
ao, asz = C['AGRP']; an = u32(ao)
agrp = [rstr(u32(u32(ao+4+4*i))) for i in range(an)]
sdo, sds = C['SOND']; sdn = u32(sdo)
os.makedirs(os.path.join(OUT, 'audio'), exist_ok=True)
audio_cache = {}
for i in range(sdn):
    e = u32(sdo+4+4*i); nm = rstr(u32(e)); grp = i32(e+28); aid = i32(e+32)
    if not nm.startswith('bgm27'): continue
    gname = agrp[grp]
    if grp not in audio_cache:
        f = os.path.join(GAME, f'{gname}.dat'); buf = open(f, 'rb').read(); cc = chunks_of(buf)
        a_o, a_s = cc['AUDO']; a_n = struct.unpack_from('<I', buf, a_o)[0]
        entries = []
        for k in range(a_n):
            q = struct.unpack_from('<I', buf, a_o+4+4*k)[0]; ln = struct.unpack_from('<I', buf, q)[0]
            entries.append(buf[q+4:q+4+ln])
        audio_cache[grp] = entries
    blob = audio_cache[grp][aid]
    ext = 'ogg' if blob[:4] == b'OggS' else 'wav'
    open(os.path.join(OUT, 'audio', f'{nm}.{ext}'), 'wb').write(blob)
    print('audio', nm, gname, aid, len(blob), ext)
