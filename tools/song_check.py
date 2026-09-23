#!/usr/bin/env python3
"""Compare the score with the original, row by row: where does the score strike a note the original does not,
and where does the original strike one the score leaves out.

usage: song_check.py [score] [--bars 24-31]
Per bar and channel, two lines: the score (note names where it strikes) and the original (what attacks there:
the bass from its band envelope and a harmonic-sum pitch, the chord stab from the mid band, the lead as the
strongest freshly attacked peak in its register). `!` marks a disagreement.
"""
import os, sys, numpy as np, librosa, scipy.signal as ss
sys.path.insert(0, os.path.dirname(__file__))
import song

OGG = 'reference/audio/bgm27_gameplay.ogg'
ROW = 11 / 60
args = sys.argv[1:]
path = next((a for a in args if a.endswith('.song')), 'res/music/gameplay.song')
s = song.parse(path); R = song.rows(s); NR = len(R)
sel = None
if '--bars' in args:
    a, _, b = args[args.index('--bars') + 1].partition('-'); sel = range(int(a), int(b or a) + 1)

y, sr = librosa.load(OGG, sr=22050, mono=True)
C = np.abs(librosa.cqt(y, sr=sr, hop_length=128, fmin=librosa.note_to_hz('C1'), n_bins=7 * 36 + 12, bins_per_octave=36))
t = np.arange(C.shape[1]) * 128 / sr
Cp = np.vstack([C[:1], C]); nb = C.shape[0] // 3
S = Cp[:nb * 3].reshape(nb, 3, -1).max(1)            # index = midi - 24
def rowspec(a, b):
    out = np.zeros((NR, nb))
    for r in range(NR):
        m = (t >= r * ROW + a) & (t < r * ROW + b); out[r] = S[:, m].mean(1)
    return out
Sm = rowspec(0.03, ROW - 0.01); Se = rowspec(0.0, 0.05); Sl = rowspec(ROW - 0.07, ROW - 0.005)
Sp = np.vstack([Sl[:1] * 0 + 1e-6, Sl[:-1]])
ref = Sm[32, 74 - 24]                                  # the B lead's first note, D5

def band_env(lo, hi):
    b, a = ss.butter(4, [lo, hi], btype='band', fs=sr); z = ss.filtfilt(b, a, y) ** 2
    st = ROW * sr / 10
    return np.array([np.sqrt(z[int(i * st):int((i + 1) * st)].mean() + 1e-12) for i in range(NR * 10)]).reshape(NR, 10)
def hits(e, ratio):
    prev = np.concatenate([[1e-6], e[:-1, 7:].mean(1)])
    return e[:, :3].max(1) > ratio * prev
eb = band_env(40, 140); bass_hit = hits(eb, 1.5); bass_on = eb[:, 1:6].mean(1) > 0.25 * np.median(eb[:, 1:6].mean(1))
em = band_env(300, 900); chord_hit = hits(em, 1.3)

W, NF = 3072, 32768; win = np.hanning(W); BC = np.arange(31, 53)
def bass_pitch(r):
    c = int((r * ROW + 0.03) * sr); seg = np.pad(y[c:c + W], (0, max(0, W - len(y[c:c + W]))))
    X = np.abs(np.fft.rfft(seg * win, NF))
    sc = [sum(X[int(round(librosa.midi_to_hz(m) * h * NF / sr)) - 2:int(round(librosa.midi_to_hz(m) * h * NF / sr)) + 3].max() / h ** .5
              for h in range(1, 7)) for m in BC]
    return int(BC[int(np.argmax(sc))])

LEAD_LO = int(args[args.index('--lead-lo') + 1]) if '--lead-lo' in args else 64
def lead_orig(r, lo=None, hi=97):
    lo = lo or LEAD_LO
    """the loudest freshly attacked spectral peak in the lead register, relative to the B lead"""
    v, e, p = Sm[r], Se[r], Sp[r]
    c = [(v[m - 24] / ref, m) for m in range(lo, hi)
         if v[m - 24] >= v[m - 25] and v[m - 24] >= v[m - 23] and e[m - 24] > 1.5 * p[m - 24] and v[m - 24] / ref > 0.3]
    return max(c) if c else None

def tok(cl):
    if cl.kind == 'note': return song.midi_to_note(cl.note) + ('^%X%X' % cl.arp if cl.arp else '')
    return {'hit': 'x', 'cut': '-'}.get(cl.kind, '.')

for num, label, rs in s.bars:
    if sel and num not in sel: continue
    print('bar %d %s' % (num, label))
    base = num * 8
    # bass
    sc = [tok(r[2]) for r in rs]
    og = []
    for i in range(8):
        r = base + i
        og.append(song.midi_to_note(bass_pitch(r)) if bass_hit[r] and bass_on[r] else '.')
    flag = ['!' if (sc[i] not in '.-') != (og[i] != '.') or (sc[i] not in '.-' and og[i] != '.' and sc[i] != og[i]) else ' ' for i in range(8)]
    print('  bass  score ' + ''.join('%-9s' % x for x in sc))
    print('        orig  ' + ''.join('%-8s%s' % (x, f) for x, f in zip(og, flag)))
    # chord
    sc = [tok(r[1]) for r in rs]
    og = ['hit' if chord_hit[base + i] else '.' for i in range(8)]
    flag = ['!' if (sc[i] not in '.-') != (og[i] != '.') else ' ' for i in range(8)]
    print('  chord score ' + ''.join('%-9s' % x for x in sc))
    print('        orig  ' + ''.join('%-8s%s' % (x, f) for x, f in zip(og, flag)))
    # lead
    sc = [tok(r[0]) for r in rs]
    og = []
    for i in range(8):
        l = lead_orig(base + i)
        og.append('%s%d' % (song.midi_to_note(l[1]), int(l[0] * 100)) if l else '.')
    print('  lead  score ' + ''.join('%-9s' % x for x in sc))
    print('        orig  ' + ''.join('%-9s' % x for x in og))
    nz = [tok(r[3]) for r in rs]
    if any(x != '.' for x in nz): print('  noise score ' + ''.join('%-9s' % x for x in nz) + '   (the original has no percussion)')
