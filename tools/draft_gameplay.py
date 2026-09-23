#!/usr/bin/env python3
"""First draft of res/music/gameplay.song from the original's OGG. Run once; the score is then edited by hand.

What the original is (read off its spectrogram, see tools/song_view.py): four voices.
  lead   a plucked pulse with a strong octave partial, mostly between A4 and G5
  chord  three-note stabs around F3-D4, struck on the syncopated accents of the bar
  bass   a bright bass between A1 and C3
  drums  a light high tick
Structure (bar self-similarity): intro 0-3 | B 4-11 | B' 12-17 | turnaround 18-19 | intro 20-23 |
C 24-31 | C' 32-39 | outro 40-43.

Per row this measures the spectrum just after the row starts and decides for each voice whether it strikes
and what: the lead from its fundamental + octave pair in E4-C6, the bass from an NNLS fit of harmonic
templates below D3, the chord from the pitch classes the NNLS finds in F3-F4 that are not bass partials,
fitted to a triad (the GB plays it as an arpeggio on CH2).

usage: draft_gameplay.py [out.song]
"""
import sys, numpy as np, librosa
from scipy.optimize import nnls
sys.path.insert(0, 'tools')
from song import midi_to_note, NAMES

OGG = 'reference/audio/bgm27_gameplay.ogg'
ROW = 11 / 60; NR = 352; BPO = 36
SECTIONS = {0: 'intro', 4: 'B', 12: "B'", 18: 'turnaround', 20: 'intro again', 24: 'C', 32: "C'", 40: 'outro'}

y, sr = librosa.load(OGG, sr=22050, mono=True)
hop = 128; fps = sr / hop
nb = 7 * BPO + 12
C = np.abs(librosa.cqt(y, sr=sr, hop_length=hop, fmin=librosa.note_to_hz('C1'), n_bins=nb, bins_per_octave=BPO))
t = np.arange(C.shape[1]) / fps
Cp = np.vstack([C[:1], C])                                      # bin 3k is centred on note 24+k: group bins 3k-1..3k+1
S = Cp[:(nb // 3) * 3].reshape(nb // 3, 3, -1).max(1)          # one bin per semitone, index = midi - 24

def rowspec(A, a, b):
    out = np.zeros((NR, A.shape[0]))
    for r in range(NR):
        m = (t >= r * ROW + a) & (t < r * ROW + b)
        out[r] = A[:, m].mean(1)
    return out
Sm = rowspec(S, 0.03, ROW - 0.01)       # body of the row
Se = rowspec(S, 0.0, 0.05)              # attack
Sp = np.vstack([Sm[:1], Sm[:-1]])       # previous row's body

# ---- NNLS over harmonic templates (for bass and chord)
M = np.arange(28, 80)
def templ(kind):
    T = np.zeros((nb, len(M)))
    for j, m in enumerate(M):
        for h in range(1, 16):
            if kind == 'odd' and h % 2 == 0: continue
            a = 1 / h if kind != 'tri' else 1 / h ** 2
            b = 3 * (m - 24) + BPO * np.log2(h)
            if b >= nb - 1: break
            for k in range(int(b) - 2, int(b) + 3):
                if 0 <= k < nb: T[k, j] += a * np.exp(-0.5 * ((k - b) / 0.7) ** 2)
        T[:, j] /= np.linalg.norm(T[:, j])
    return T
T = np.hstack([templ('saw'), templ('odd'), templ('tri')])
act = np.zeros((NR, len(M)))
for r in range(NR):
    m = (t >= r * ROW + 0.03) & (t < r * ROW + ROW - 0.01)
    x, _ = nnls(T, C[:, m].mean(1)); act[r] = x.reshape(3, -1).sum(0)
act /= np.percentile(act.max(1), 90)
def A(midi): return act[:, midi - 28]

# ---- attacks per band (log spectral flux around the row start)
Lg = np.log1p(C * 100)
fl = np.maximum(0, np.diff(Lg, axis=1, prepend=Lg[:, :1]))
def attacks(lo_midi, hi_midi):
    v = fl[3 * (lo_midi - 24):3 * (hi_midi - 24)].sum(0)
    r = np.array([v[max(0, int((i * ROW - 0.02) * fps)):int((i * ROW + 0.05) * fps)].max() for i in range(NR)])
    return r / np.median(r)
att_lead = attacks(64, 88); att_chord = attacks(52, 66); att_bass = attacks(28, 50)
Sf = np.abs(librosa.stft(y, n_fft=512, hop_length=64)); f = librosa.fft_frequencies(sr=sr, n_fft=512)
tf = np.arange(Sf.shape[1]) * 64 / sr
Bh = Sf[f > 6000]; dh = np.maximum(0, np.diff(Bh, axis=1, prepend=Bh[:, :1])).sum(0)
att_hi = np.array([dh[(tf >= i * ROW - 0.02) & (tf < i * ROW + 0.04)].max() for i in range(NR)]); att_hi /= np.median(att_hi)

def viterbi(E, pen, cap=12):
    nr, ns = E.shape; idx = np.arange(ns)
    step = pen * np.minimum(np.abs(idx[None, :] - idx[:, None]), cap)
    cost = E[0].copy(); back = np.zeros((nr, ns), int)
    for r in range(1, nr):
        Mx = cost[None, :] - step; k = Mx.argmax(1); cost = Mx[idx, k] + E[r]; back[r] = k
    p = [int(cost.argmax())]
    for r in range(nr - 1, 0, -1): p.append(back[r, p[-1]])
    return p[::-1]

# ---- lead: fundamental with its octave partial. The register moves by section: none in the intro (the
# partials up there belong to the chord voice), G4-C6 in B and the turnaround, A5-C7 in C and the outro.
def lead_range(bar):
    if bar < 4 or 20 <= bar < 24: return None
    if bar < 20: return (67, 85)
    return (81, 98)
LO, HI = 64, 98
E = np.array([Sm[:, m - 24] + 0.5 * Sm[:, min(m - 12, Sm.shape[1] - 1)] for m in range(LO, HI)]).T
for r in range(NR):
    rg = lead_range(r // 8)
    if rg is None: E[r] = 0
    else: E[r, :rg[0] - LO] = 0; E[r, rg[1] - LO:] = 0
for a, b in ((32, 160), (192, 352)):          # normalise per register: the high line in C is quieter
    E[a:b] /= np.percentile(E[a:b].max(1), 80)
lp = viterbi(E, 0.05)
lead = []; lead_note = None
for r in range(NR):
    m = LO + lp[r]; e = E[r, lp[r]]
    if e < 0.3: lead.append(None if (not lead or lead[-1] is None or e < 0.15) else '.'); continue
    k = m - 24
    new = (r == 0 or lead[-1] is None or lead_note != m or
           Se[r, k] > 1.35 * Sp[r, k] and att_lead[r] > 0.9)
    lead.append(m if new else '.')
    lead_note = m

# the B-section tune, read off the spectrogram by eye (tools/song_view.py): it overrides the tracker there
B_TUNE = {
    4: 'D5 C5 G5 F#5 . D5 . C5', 5: '. E5 . A4 . A4 G4 A4',
    6: '. D5 G5 F#5 . D5 B4!706 C5!702', 7: 'D5 A4 G4 F#4 . . . .',
    10: 'F#5 G5 B4 F#5 C#5 . . .',
}
for src, dst in ((4, 8), (5, 9), (4, 12), (5, 13), (6, 14), (7, 15), (4, 16), (5, 17)): B_TUNE[dst] = B_TUNE[src]
lead_fx = {}
for bar, txt in B_TUNE.items():
    for i, tkn in enumerate(txt.split()):
        r = bar * 8 + i
        if '!' in tkn: tkn, fx = tkn.split('!'); lead_fx[r] = fx
        lead[r] = '.' if tkn == '.' else librosa.note_to_midi(tkn)

# ---- band envelopes, 10 steps a row: a voice strikes where its band jumps at the row start
import scipy.signal as ss
def band_env(lo, hi):
    b, a = ss.butter(4, [lo, hi], btype='band', fs=sr); z = ss.filtfilt(b, a, y) ** 2
    st = ROW * sr / 10
    return np.array([np.sqrt(z[int(i * st):int((i + 1) * st)].mean() + 1e-12) for i in range(NR * 10)])
def strikes(env, ratio):
    e = env.reshape(NR, 10)
    prev = np.concatenate([[1e-6], e[:-1, 7:].mean(1)])
    return e[:, :3].max(1) > ratio * prev, e[:, 1:6].mean(1) / np.median(e[:, 1:6].mean(1))
bass_hit, bass_lvl = strikes(band_env(40, 140), 1.5)
chord_hit, chord_lvl = strikes(band_env(400, 1200), 1.3)

# ---- bass: harmonic sum on a long STFT of each row (the CQT smears low notes across rows), G1..E3
W, NF = 3072, 32768
win = np.hanning(W); BC = np.arange(31, 53); HS = np.zeros((NR, len(BC)))
for r in range(NR):
    c = int((r * ROW + 0.03) * sr); seg = y[c:c + W]
    seg = np.pad(seg, (0, W - len(seg)))
    X = np.abs(np.fft.rfft(seg * win, NF))
    for j, m in enumerate(BC):
        f0 = librosa.midi_to_hz(m)
        HS[r, j] = sum(X[int(round(f0 * h * NF / sr)) - 2:int(round(f0 * h * NF / sr)) + 3].max() / h ** 0.5 for h in range(1, 7))
HS /= np.percentile(HS.max(1), 90)
bass = []; bnote = None
for r in range(NR):
    j = int(HS[r].argmax()); m = int(BC[j])
    if bass_lvl[r] < 0.25: bass.append(None); bnote = None; continue
    if bass_hit[r] or (bnote is not None and m != bnote and HS[r, j] > 0.6): bass.append(m); bnote = m
    else: bass.append('.' if bnote is not None else None)
BLO = 31; bp = [0] * NR
cur = None
for r in range(NR):
    if isinstance(bass[r], int): cur = bass[r]
    elif bass[r] is None: cur = None
    bp[r] = (cur - BLO) if cur is not None else 0

# ---- chord: pitch classes in F3..F4 (not bass partials, not the lead) on rows with a mid attack
TRIADS = [((0, 4, 7), ''), ((0, 3, 7), 'm'), ((0, 3, 6), 'dim'), ((0, 5, 7), 'sus4'), ((0, 2, 7), 'sus2'),
          ((0, 4, 10), '7'), ((0, 4, 11), 'maj7'), ((0, 3, 10), 'm7')]
chord = []; last = None
for r in range(NR):
    b = BLO + bp[r]
    ch = np.zeros(12); lowest = {}
    for m in range(50, 68):
        v = A(m)[r]
        if (m - b) in (12, 19, 24, 28, 31) and v < 0.6: v *= 0.3
        if lead[r] not in (None, '.') and (lead[r] - m) % 12 == 0: v *= 0.5
        ch[m % 12] += v
        if v > 0.15: lowest.setdefault(m % 12, m)
    best = None
    for root in range(12):
        for iv, q in TRIADS:
            sc = sum(ch[(root + i) % 12] for i in iv) - 0.5 * (ch.sum() - sum(ch[(root + i) % 12] for i in iv)) / 4
            if best is None or sc > best[0]: best = (sc, root, iv, q)
    sc, root, iv, q = best
    if sc < 0.5: chord.append(None); last = None; continue
    tones = sorted(lowest.get((root + i) % 12, 55 + ((root + i - 55) % 12)) for i in iv)
    lo_t = tones[0]; arp = (tones[1] - lo_t, tones[2] - lo_t)
    if arp[1] > 15: arp = (arp[0], arp[1] - 12)
    key = (lo_t, arp)
    strike = chord_hit[r] or (key != last and att_chord[r] > 1.2)
    chord.append(key if strike else '.')
    if strike: last = key

drums = ['x' if att_hi[r] > 1.6 else '.' for r in range(NR)]

# ---- write the score
out = sys.argv[1] if len(sys.argv) > 1 else 'res/music/gameplay.song'
L = ['# Magic Garden - gameplay loop, transcribed from the original (UFO 50 #5, bgm27_gameplay).',
     '# 44 bars x 8 rows, 11 frames a row (an eighth note at 163.6 BPM). tools/song.py documents the format.',
     '# First draft by tools/draft_gameplay.py; edited by hand from here on.', '',
     'song song_gameplay', 'speed 11', '',
     'duty  1 lead  duty=25 vol=12 env=-4     # plucked: a quarter of the way down by the end of a row',
     'duty  2 chord duty=50 vol=8  env=-2     # a stab that is gone in about a row and a half',
     'wave  1 bass  vol=100 wave=0',
     'noise 1 tick  vol=4 env=-1',
     'noise_note 60',
     'waveform 0 8BEFECA989999877 88876666765310 14   # one bright cycle: sounds an octave below the note table, reaching G1', '']
def tok(v, kind):
    if v is None: return '.'
    if v == '.': return '.'
    if kind == 'chord':
        lo_t, (a, b) = v; return '%s^%X%X' % (midi_to_note(lo_t), a, b)
    return midi_to_note(v)
prev = {'lead': None, 'bass': None}
for r in range(NR):
    if r % 8 == 0:
        bar = r // 8
        L.append('== bar %d%s' % (bar, ('  ' + SECTIONS[bar]) if bar in SECTIONS else ''))
        L.append('#  lead    chord     bass    noise')
    cells = []
    for name, v in (('lead', lead[r]), ('chord', chord[r]), ('bass', bass[r])):
        tk = tok(v, name)
        if name == 'lead' and r in lead_fx: tk += '!' + lead_fx[r]
        if v is None and name in prev and prev[name] not in (None,): tk = '-'   # a voice that stops is cut
        if name in prev: prev[name] = v
        cells.append(tk)
    cells.append(drums[r])
    L.append('%d  %-7s %-9s %-7s %s' % (r % 8, *cells))
open(out, 'w').write('\n'.join(L) + '\n')
print('wrote', out)
