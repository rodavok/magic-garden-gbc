#!/usr/bin/env python3
"""What the original plays that the Game Boy render does not (and the reverse), row by row.

usage: song_diff.py <first_bar> <last_bar> [render.wav]
Both recordings go through the same semitone spectrum (the render resampled to the original's 60 fps timing).
Per row: `+` notes present in the original but missing or much weaker in the render, `-` notes the render
plays that the original does not have. Levels are relative to the B lead's first note (100).
"""
import sys, numpy as np, librosa
ROW = 11 / 60
b0, b1 = int(sys.argv[1]), int(sys.argv[2])
render = sys.argv[3] if len(sys.argv) > 3 else 'build/song/full.wav'

def semis(path, stretch=1.0):
    y, sr = librosa.load(path, sr=22050, mono=True)
    if stretch != 1.0: y = librosa.resample(y, orig_sr=sr * stretch, target_sr=sr)
    C = np.abs(librosa.cqt(y, sr=sr, hop_length=128, fmin=librosa.note_to_hz('C1'), n_bins=7 * 36 + 12, bins_per_octave=36))
    Cp = np.vstack([C[:1], C]); nb = C.shape[0] // 3
    S = Cp[:nb * 3].reshape(nb, 3, -1).max(1)
    t = np.arange(S.shape[1]) * 128 / sr
    out = np.zeros((352, nb)); att = np.zeros((352, nb))
    for r in range(352):
        m = (t >= r * ROW + 0.03) & (t < r * ROW + ROW - 0.01); out[r] = S[:, m].mean(1)
        e = S[:, (t >= r * ROW) & (t < r * ROW + 0.05)].mean(1)
        p = S[:, (t >= r * ROW - 0.07) & (t < r * ROW - 0.005)].mean(1) if r else e * 0
        att[r] = e / (p + 1e-9)
    return out, att
O, Oa = semis('reference/audio/bgm27_gameplay.ogg')
G, Ga = semis(render, 60 / 59.7275)
ref_o = O[32, 50]; ref_g = G[32, 50]            # both scaled to their own B-lead D5
O /= ref_o; G /= ref_g
def pk(v, k): return v[k] >= v[k - 1] and v[k] >= v[k + 1]
for b in range(b0, b1 + 1):
    print('bar', b)
    for i in range(8):
        r = b * 8 + i; plus = []; minus = []
        for k in range(26, 72):            # D2..C6
            o, g = O[r, k], G[r, k]
            if pk(O[r], k) and o > 0.35 and g < 0.4 * o: plus.append('%s%s%d' % (librosa.midi_to_note(k + 24, unicode=False), '*' if Oa[r, k] > 1.5 else '', o * 100))
            if pk(G[r], k) and g > 0.35 and o < 0.3 * g: minus.append('%s%d' % (librosa.midi_to_note(k + 24, unicode=False), g * 100))
        print('  %d  + %-50s - %s' % (i, ' '.join(plus), ' '.join(minus)))
