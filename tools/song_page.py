#!/usr/bin/env python3
"""Build the song review page in build/song/: the original and the GB render in sync, a lane per channel
with its notes, per-channel solo/mute, bar looping. Run tools/song_render.py first; serve build/song
(the "song-viewer" entry in .claude/launch.json) and open index.html.

usage: song_page.py [score]
"""
import json, os, shutil, subprocess, sys, time
import numpy as np, librosa
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import song

OUT = 'build/song'
ORIG = 'reference/audio/bgm27_gameplay.ogg'
LO, HI = song.note_to_midi('G1'), song.note_to_midi('C8')
PX_ROW = 16

def spectro(path, rate, png):
    """piano-roll spectrogram, one pixel column per 1/16 row, 3 pixel rows per semitone, low notes at the bottom"""
    y, sr = librosa.load(path, sr=22050, mono=True)
    row_s = 11 / rate
    C = np.abs(librosa.cqt(y, sr=sr, hop_length=64, fmin=librosa.note_to_hz('C1'), n_bins=88 * 3, bins_per_octave=36))
    L = librosa.amplitude_to_db(C, ref=np.percentile(C, 99.9)); L = np.clip((L + 34) / 34, 0, 1)
    nrow = 352
    cols = (np.arange(nrow * PX_ROW) / PX_ROW * row_s * sr / 64).astype(int).clip(0, L.shape[1] - 1)
    sub = L[3 * (LO - 24) - 1:3 * (HI - 24) - 1][::-1][:, cols]
    rgb = (np.stack([sub, sub ** 1.6, sub ** 3.5], -1) * 255).astype(np.uint8)
    Image.fromarray(rgb).save(png)

def ogg(src, dst):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-c:a', 'libvorbis', '-q:a', '5', dst], check=True)

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'res/music/gameplay.song'
    s = song.parse(path)
    ev = song.events(s)
    data = {'rows': len(song.rows(s)), 'lo': LO, 'hi': HI, 'pxRow': PX_ROW,
            'bars': [{'n': n, 'label': l} for n, l, _ in s.bars], 'channels': {}, 'grid': []}
    for c in song.CHANNELS:
        data['channels'][c] = [{'row': r, 'len': n, 'notes': t, 'label': lab} for r, n, t, lab in ev[c]]
    # the score as text, one line per row, for the per-bar table
    for num, label, rs in s.bars:
        for r in rs: data['grid'].append([cl.text for cl in r])
    data['build'] = int(time.time())       # cache-buster for the audio URLs
    if os.path.exists(os.path.join(OUT, 'alt.wav')):     # an earlier render kept for A/B: the page offers it as a third source
        data['alt'] = open(os.path.join(OUT, 'alt.txt')).read().strip() if os.path.exists(os.path.join(OUT, 'alt.txt')) else 'Previous GB'
    json.dump(data, open(os.path.join(OUT, 'song.json'), 'w'))
    spectro(ORIG, 60.0, os.path.join(OUT, 'spec_orig.png'))
    spectro(os.path.join(OUT, 'full.wav'), 59.7275, os.path.join(OUT, 'spec_gb.png'))
    ogg(ORIG, os.path.join(OUT, 'original.ogg'))
    for n in ('full', 'lead', 'chord', 'bass', 'noise'): ogg(os.path.join(OUT, n + '.wav'), os.path.join(OUT, n + '.ogg'))
    if 'alt' in data: ogg(os.path.join(OUT, 'alt.wav'), os.path.join(OUT, 'alt.ogg'))
    shutil.copy(os.path.join(os.path.dirname(__file__), 'song_page.html'), os.path.join(OUT, 'index.html'))
    print('wrote', OUT + '/index.html')
