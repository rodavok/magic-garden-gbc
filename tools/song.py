#!/usr/bin/env python3
"""Text score <-> hUGEDriver song.

The score (res/music/*.song) is a tracker sheet you can read and edit: one line per row (11 frames, an
eighth note at 163.6 BPM), 8 rows to a bar, one column per Game Boy channel.

    song song_gameplay                      C symbol
    speed 11                                frames per row
    duty  1 lead  duty=25 vol=12 env=-4     pulse instrument: duty 12/25/50/75, start volume 0-15,
    duty  2 chord duty=50 vol=9  env=-2     env=-n fades one step per n/64 s (+n grows, 0 holds)
    wave  1 bass  vol=100 wave=0            wave instrument: volume 100/50/25, waveform index
    noise 1 tick  vol=4 env=-1              noise instrument
    waveform 0 8BEFECA989999877888766667653101 4   32 hex digits (spaces ignored)

    == bar 4  B section                     a bar header, then 8 rows
    0  D5      C4^47    C3     x
    1  .       .        .      .

Columns: row-in-bar, lead (CH1), chord (CH2), bass (CH3 wave), noise (CH4).
  C#5 / Db5   strike a note (scientific pitch, C4 = middle C). `@2` after it picks another instrument
  C4^47       chord: strike C4 and arpeggiate +4 and +7 semitones (hUGE effect 0xy) until the next note
  .           nothing new (a note keeps sounding / decaying; a chord keeps arpeggiating)
  -           cut the note
  x           noise hit (noise pitch from `noise_note`, or x@2 for instrument 2, xNN for pitch NN)
  !Axy        raw hUGE effect after a token, e.g. `D5!C08` (set volume) or `.!E02`
A `#` at the start of a line or after a space starts a comment (C#5 is a note).

usage:
  song.py compile <in.song> <out.c>
  song.py show <in.song> [bars e.g. 4-7] [--ch lead,bass]   print a bar-by-bar channel view
  song.py json <in.song> <out.json>                          notes per channel, for the viewer
"""
import re, sys, json

NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLATS = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
CHANNELS = ['lead', 'chord', 'bass', 'noise']
CHORD_NAMES = {(4, 7): '', (3, 7): 'm', (3, 6): 'dim', (4, 8): '+', (5, 7): 'sus4', (2, 7): 'sus2',
               (4, 10): '7', (3, 10): 'm7', (4, 11): 'maj7', (7, 12): '5', (4, 9): '6', (3, 9): 'm6',
               (7, 10): '7(no3)', (7, 11): 'maj7(no3)', (4, 14): 'add9', (7, 14): 'sus2'}

def note_to_midi(s):
    m = re.fullmatch(r'([A-G])([#b]?)(-?\d)', s)
    if not m: raise ValueError('bad note %r' % s)
    n = m.group(1) + m.group(2)
    n = FLATS.get(n, n)
    return NAMES.index(n) + 12 * (int(m.group(3)) + 1)

def midi_to_note(m):
    return '%s%d' % (NAMES[m % 12], m // 12 - 1)

def chord_name(root, x, y):
    if x == y: return '%s+%s' % (NAMES[root % 12], NAMES[(root + x) % 12])   # two notes alternating
    a, b = sorted((x, y))
    q = CHORD_NAMES.get((a, b))
    if q is None:
        # try the inversions: which of the three notes is the root of a known shape
        tones = [root, root + x, root + y]
        for r in tones:
            iv = tuple(sorted(((t - r) % 12) for t in tones if t != r))
            if iv in CHORD_NAMES: return NAMES[r % 12] + CHORD_NAMES[iv] + '/' + NAMES[root % 12]
        return '%s(+%d+%d)' % (NAMES[root % 12], x, y)
    return NAMES[root % 12] + q

class Cell:
    __slots__ = ('kind', 'note', 'instr', 'arp', 'fx', 'text')
    def __init__(self, text):
        self.text = text; self.kind = 'hold'; self.note = None; self.instr = None; self.arp = None; self.fx = None
        t = text
        if '!' in t:
            t, fx = t.split('!', 1)
            self.fx = int(fx, 16)
        if '@' in t:
            t, ins = t.split('@', 1)
            self.instr = int(ins)
        if t in ('.', ''): return
        if t == '-': self.kind = 'cut'; return
        if t[0] == 'x':
            self.kind = 'hit'
            if len(t) > 1: self.note = int(t[1:])
            return
        if '^' in t:
            t, arp = t.split('^', 1)
            self.arp = (int(arp[0], 16), int(arp[1], 16))
        self.kind = 'note'; self.note = note_to_midi(t)

class Song:
    def __init__(self):
        self.name = 'song'; self.speed = 11; self.duty = {}; self.wave = {}; self.noise = {}; self.waves = {}
        self.noise_note = 60; self.bars = []   # [(number, label, [[Cell x4] x8])]

def parse(path):
    s = Song(); bar = None
    for ln, line in enumerate(open(path), 1):
        line = re.split(r'(?:^|\s)#', line, 1)[0].rstrip()
        if not line.strip(): continue
        w = line.split()
        try:
            if w[0] == '==':
                bar = (int(w[2]), ' '.join(w[3:]), []); s.bars.append(bar)
            elif w[0] == 'song': s.name = w[1]
            elif w[0] == 'speed': s.speed = int(w[1])
            elif w[0] == 'noise_note': s.noise_note = int(w[1])
            elif w[0] in ('duty', 'wave', 'noise'):
                kv = dict(x.split('=') for x in w[3:])
                getattr(s, w[0])[int(w[1])] = (w[2], {k: int(v) for k, v in kv.items()})
            elif w[0] == 'waveform':
                hx = ''.join(w[2:]); assert len(hx) == 32, 'waveform needs 32 hex digits'
                s.waves[int(w[1])] = bytes.fromhex(hx)
            else:
                assert bar is not None, 'row before the first bar header'
                r = int(w[0]); assert r == len(bar[2]), 'row %d out of order in bar %d' % (r, bar[0])
                cells = [Cell(x) for x in w[1:5]]
                while len(cells) < 4: cells.append(Cell('.'))
                bar[2].append(cells)
        except Exception as e:
            sys.exit('%s:%d: %s' % (path, ln, e))
    for b in s.bars:
        if len(b[2]) != 8: sys.exit('%s: bar %d has %d rows, want 8' % (path, b[0], len(b[2])))
    return s

def rows(s):
    out = []
    for b in s.bars: out.extend(b[2])
    return out

# ---------------------------------------------------------------- compile
def env_byte(vol, env):
    """NRx2: volume in the high nibble, bit 3 = grow, low 3 bits = step period (0 = hold)"""
    if env == 0: return vol << 4
    return (vol << 4) | (0x08 if env > 0 else 0) | min(7, abs(env))

def compile_song(s, out):
    R = rows(s); nrows = len(R); npat = (nrows + 63) // 64
    DUTY = {12: 0x00, 25: 0x40, 50: 0x80, 75: 0xC0}
    WVOL = {100: 0x20, 50: 0x40, 25: 0x60, 0: 0x00}
    def dn(note, instr, fx): return 'DN(%d,%d,0x%03X)' % (note, instr, fx)
    pats = {c: [] for c in range(4)}
    for c in range(4):
        cur_arp = None; cur_note = None
        cells = []
        for i in range(npat * 64):
            if i >= nrows: cells.append([90, 0, 0]); continue
            cl = R[i][c]; note, instr, fx = 90, 0, 0
            if cl.kind == 'note':
                m = cl.note
                h = m - (24 if c == 2 else 36)
                if not 0 <= h < 72: sys.exit('%s: row %d %s out of range for %s' % (s.name, i, cl.text, CHANNELS[c]))
                note, instr = h, cl.instr or 1
                cur_arp = cl.arp; cur_note = m
            elif cl.kind == 'hit':
                note, instr = (cl.note if cl.note is not None else s.noise_note), cl.instr or 1
            elif cl.kind == 'cut':
                fx = 0xE00; cur_arp = None
            if cur_arp and cl.kind in ('note', 'hold'):
                fx = (cur_arp[0] << 4) | cur_arp[1]        # effect 0xy, repeated on every row the chord holds
            if cl.fx is not None: fx = cl.fx
            cells.append([note, instr, fx])
        pats[c] = cells
    # the order list wraps after the last pattern; a partial last pattern needs a pattern break (D00)
    end = nrows % 64
    if end:
        i = (npat - 1) * 64 + end - 1
        for c in (3, 2, 0, 1):
            if pats[c][i][2] == 0: pats[c][i][2] = 0xD00; break
        else: sys.exit('no free effect slot for the pattern break on the last row')
    # identical patterns are stored once
    L = ['/* Generated by tools/song.py from res/music/%s.song - edit the score, not this file. */' % s.name.replace('song_', ''),
         '#pragma bank 2', '#include "hUGEDriver.h"', '#include <stddef.h>', '']
    uniq = {}; order = {c: [] for c in range(4)}
    for c in range(4):
        for p in range(npat):
            body = tuple(tuple(x) for x in pats[c][p * 64:(p + 1) * 64])
            if body not in uniq:
                nm = '%s_p%d' % (s.name, len(uniq)); uniq[body] = nm
                L.append('static const unsigned char %s[] = {' % nm)
                for k in range(0, 64, 4): L.append('    ' + ','.join(dn(*x) for x in body[k:k + 4]) + ',')
                L.append('};')
            order[c].append(uniq[body])
    L.append('static const unsigned char %s_order_cnt = %d;' % (s.name, 2 * npat))
    for c in range(4):
        L.append('static const unsigned char* const %s_order%d[] = { %s };' % (s.name, c + 1, ', '.join(order[c])))
    L.append('/* instrument ids are 1-based: the driver does `dec a`, so instrument 1 is entry [0] */')
    L.append('static const hUGEDutyInstr_t %s_duty[] = {' % s.name)
    for i in range(1, max(s.duty, default=0) + 1):
        nm, p = s.duty.get(i, ('unused', {}))
        L.append('    {0x%02X, 0x%02X, 0x%02X, 0, 128},   /* %d %s */' % (p.get('sweep', 0), DUTY[p.get('duty', 50)] | p.get('len', 0),
                 env_byte(p.get('vol', 15), p.get('env', 0)), i, nm))
    L.append('};')
    L.append('static const hUGEWaveInstr_t %s_wave[] = {' % s.name)
    for i in range(1, max(s.wave, default=0) + 1):
        nm, p = s.wave.get(i, ('unused', {}))
        L.append('    {0, 0x%02X, %d, 0, 128},   /* %d %s */' % (WVOL[p.get('vol', 100)], p.get('wave', 0), i, nm))
    L.append('};')
    L.append('static const hUGENoiseInstr_t %s_noise[] = {' % s.name)
    for i in range(1, max(s.noise, default=1) + 1):      # C wants at least one entry
        nm, p = s.noise.get(i, ('unused', {'vol': 0}))
        L.append('    {0x%02X, 0, %d, 0, 0},   /* %d %s */' % (env_byte(p.get('vol', 15), p.get('env', 0)), 0x80 if p.get('periodic') else 0, i, nm))
    L.append('};')
    L.append('static const unsigned char %s_waves[] = {' % s.name)
    for i in range(max(s.waves, default=-1) + 1):
        w = s.waves.get(i, bytes(16))
        L.append('    ' + ','.join('0x%02X' % b for b in w) + ',')
    L.append('};')
    L.append('const hUGESong_t {0} = {{ {1}, &{0}_order_cnt, {0}_order1, {0}_order2, {0}_order3, {0}_order4, '
             '{0}_duty, {0}_wave, {0}_noise, NULL, {0}_waves }};'.format(s.name, s.speed))
    open(out, 'w').write('\n'.join(L) + '\n')
    print('%s: %d rows, %d patterns stored (%d unique), %d bytes of pattern data' % (s.name, nrows, 4 * npat, len(uniq), len(uniq) * 192))

# ---------------------------------------------------------------- views
def events(s):
    """per channel: list of (row, length_rows, midi_or_None, label) for each struck note"""
    R = rows(s); ev = {c: [] for c in CHANNELS}
    for ci, c in enumerate(CHANNELS):
        cur = None
        for i, r in enumerate(R + [None]):
            cl = r[ci] if r else None
            if cl is None or cl.kind in ('note', 'hit', 'cut'):
                if cur: cur[1] = i - cur[0]; ev[c].append(tuple(cur)); cur = None
            if cl is not None and cl.kind == 'note':
                lab = midi_to_note(cl.note)
                if cl.arp: lab = '%s %s' % (chord_name(cl.note, *cl.arp), lab)
                tones = [cl.note] + ([cl.note + cl.arp[0], cl.note + cl.arp[1]] if cl.arp else [])
                cur = [i, 1, tones, lab]
            elif cl is not None and cl.kind == 'hit':
                ev[c].append((i, 1, [], 'x')); cur = None
    return ev

def show(s, sel=None, chans=CHANNELS):
    for num, label, rs in s.bars:
        if sel and num not in sel: continue
        print('bar %-3d %s' % (num, label))
        print('        ' + ''.join('%-9d' % r for r in range(8)))
        for ci, c in enumerate(CHANNELS):
            if c not in chans: continue
            cells = []
            for r in rs:
                cl = r[ci]
                if cl.kind == 'note':
                    t = midi_to_note(cl.note)
                    if cl.arp: t = chord_name(cl.note, *cl.arp)
                elif cl.kind == 'hit': t = 'x'
                elif cl.kind == 'cut': t = '-'
                else: t = '.'
                cells.append('%-9s' % t)
            print('  %-6s' % c + ''.join(cells))
        print()

if __name__ == '__main__':
    cmd = sys.argv[1]; s = parse(sys.argv[2])
    if cmd == 'compile': compile_song(s, sys.argv[3])
    elif cmd == 'show':
        sel = None; chans = CHANNELS
        args = sys.argv[3:]
        if '--ch' in args:
            k = args.index('--ch'); chans = args[k + 1].split(','); del args[k:k + 2]
        if args:
            sel = set()
            for part in args[0].split(','):
                a, _, b = part.partition('-'); sel.update(range(int(a), int(b or a) + 1))
        show(s, sel, chans)
    elif cmd == 'json':
        ev = events(s)
        json.dump({'name': s.name, 'rows': len(rows(s)), 'bars': [[n, l] for n, l, _ in s.bars],
                   'channels': {c: [{'row': r, 'len': n, 'notes': t, 'label': lab} for r, n, t, lab in ev[c]] for c in CHANNELS}},
                  open(sys.argv[3], 'w'))
    else: sys.exit(__doc__)
