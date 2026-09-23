#!/usr/bin/env python3
"""Piano roll of the original with the score drawn on top, to see where a transcription is off.

usage: song_view.py <first_bar> <last_bar> <out.png> [--lo C2 --hi C7] [--render build/song/full.wav] [--score f]
Each semitone is a band (C lines in blue); rows are thin green lines, bars bright green. The original is the
heat map; the score's notes are outlined: lead red, chord tones blue, bass green (drawn at the pitch that
sounds, i.e. the wave channel an octave below its note table). With --render the GB recording is drawn
below the original on the same scale.
"""
import sys, os, numpy as np, librosa
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import song

ROW = 11 / 60
args = sys.argv[1:]
def opt(k, d):
    return args[args.index(k) + 1] if k in args else d
b0, b1, out = int(args[0]), int(args[1]), args[2]
lo = song.note_to_midi(opt('--lo', 'C2')); hi = song.note_to_midi(opt('--hi', 'C7'))
score = opt('--score', 'res/music/gameplay.song')
render = opt('--render', None)

def cqt(path, stretch=1.0):
    y, sr = librosa.load(path, sr=22050, mono=True)
    if stretch != 1.0: y = librosa.resample(y, orig_sr=sr * stretch, target_sr=sr)  # GB plays 0.45% slow
    C = np.abs(librosa.vqt(y, sr=sr, hop_length=128, fmin=librosa.note_to_hz('C1'), n_bins=84 * 3, bins_per_octave=36, gamma=GAMMA))
    L = librosa.amplitude_to_db(C, ref=np.percentile(C, 99.9))
    return np.clip((L + 32) / 32, 0, 1), sr / 128

GAMMA = float(opt('--gamma', '25'))   # variable-Q: shorter windows in the bass, so notes do not smear across rows
PX_ROW = int(opt('--px', '48')); PH = int(opt('--ph', '3'))       # pixels per row, pixels per third of a semitone
W = (b1 - b0 + 1) * 8 * PX_ROW; Hb = (hi - lo) * 3 * PH
panels = [cqt('reference/audio/bgm27_gameplay.ogg')]
if render: panels.append(cqt(render, 60 / 59.7275))
img = Image.new('RGB', (W + 40, Hb * len(panels) + 6 * (len(panels) - 1)), 'black'); d = ImageDraw.Draw(img)
s = song.parse(score); ev = song.events(s)
COL = {'lead': (255, 60, 60), 'chord': (80, 160, 255), 'bass': (60, 255, 90)}
for p, (L, fps) in enumerate(panels):
    y0 = p * (Hb + 6)
    f0 = b0 * 8 * ROW * fps
    xs = np.arange(W); fr = (f0 + xs / PX_ROW * ROW * fps).astype(int).clip(0, L.shape[1] - 1)
    sub = L[3 * (lo - 24) - 1:3 * (hi - 24) - 1][::-1][:, fr]          # bin 3(m-24) is centred on note m; high notes on top
    rgb = np.stack([sub, sub ** 1.6, sub ** 3.5], -1) * 255
    rgb = np.repeat(rgb, PH, axis=0).astype(np.uint8)
    img.paste(Image.fromarray(rgb), (40, y0))
    for m in range(lo, hi + 1):
        yy = y0 + (hi - m) * 3 * PH - 1
        if m % 12 == 0: d.line([40, yy, W + 40, yy], fill=(0, 60, 120))
        if m % 12 in (0, 4, 7): d.text((2, yy - 3 * PH // 2 - 5), song.midi_to_note(m), fill='cyan' if m % 12 == 0 else (130, 130, 130))
    for r in range(b0 * 8, (b1 + 1) * 8 + 1):
        x = 40 + (r - b0 * 8) * PX_ROW
        d.line([x, y0, x, y0 + Hb], fill=(0, 200, 0) if r % 8 == 0 else (0, 60, 0))
        if r % 8 == 0 and r // 8 <= b1: d.text((x + 3, y0 + 2), 'bar %d' % (r // 8), fill=(0, 255, 0))
    if p == 0:
        for ch, col in COL.items():
            for row, n, tones, lab in ev[ch]:
                if row + n < b0 * 8 or row > (b1 + 1) * 8: continue
                x0 = 40 + (row - b0 * 8) * PX_ROW; x1 = x0 + n * PX_ROW - 2
                for m in tones:
                    if not lo <= m < hi: continue
                    yy = y0 + (hi - 1 - m) * 3 * PH
                    d.rectangle([x0 + 1, yy + 1, x1, yy + 3 * PH - 1], outline=col)
                if lab and x0 >= 40: d.text((x0 + 3, y0 + (hi - 1 - tones[0]) * 3 * PH + 3 * PH), lab.split()[0], fill=col)
img.save(out)
print('wrote', out)
