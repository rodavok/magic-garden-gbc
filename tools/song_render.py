#!/usr/bin/env python3
"""Render the gameplay score through the real driver: compile res/music/gameplay.song, build a music-test
ROM (tools/musictest/main.c) and record it in SameBoy. Also writes one solo WAV per channel.

usage: song_render.py [score] [--solo-only | --no-solo] [--loops N]
out:   src/music_gameplay.c (the compiled score, which the game links)
       build/song/full.wav, lead.wav, chord.wav, bass.wav, noise.wav   (44.1 kHz stereo, first loop)
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import song

GBDK = os.environ.get('GBDK_HOME', os.path.expanduser('~/.local/opt/gbdk'))
LCC = os.path.join(GBDK, 'bin', 'lcc')
BOOT = os.path.expanduser('~/.local/opt/SameBoy-1.0.3/build/bin/BootROMs/cgb_boot.bin')
OUT = 'build/song'

def build(solo):
    obj = os.path.join(OUT, 'obj%d' % solo); os.makedirs(obj, exist_ok=True)
    cf = ['-Iinclude', '-Wf--opt-code-speed']
    objs = []
    for src, extra in (('tools/musictest/main.c', ['-DSOLO=%d' % solo]), ('src/music.c', []),
                       ('src/music_data.c', []), ('src/music_gameplay.c', [])):
        o = os.path.join(obj, os.path.basename(src)[:-2] + '.o')
        subprocess.run([LCC] + cf + extra + ['-c', '-o', o, src], check=True)
        objs.append(o)
    o = os.path.join(obj, 'hugebank.o'); subprocess.run([LCC, '-c', '-o', o, 'src/hugebank.s'], check=True); objs.append(o)
    rom = os.path.join(OUT, 'musictest%d.gbc' % solo)
    subprocess.run([LCC, '-Wm-yC', '-Wm-yt0x1B', '-Wm-ya1', '-Wl-yo4', '-o', rom] + objs + ['lib/hUGEDriver.o'], check=True)
    return rom

def record(rom, wav, frames):
    env = dict(os.environ, SAMEBOY_BOOT=BOOT, SAMEBOY_WAV=wav)
    subprocess.run(['tools/sameboy/dump', rom, str(frames), os.path.join(OUT, 'shot')], env=env, check=True,
                   stdout=subprocess.DEVNULL)

def trim(wav, nrows, loops, start=None):
    """cut the recording to start at the song's first row (the boot ROM and init take a moment) and remove
       the DC offset the GB's enabled DACs add. Every ROM starts the song on the same frame, so the start
       found in the full mix is used for the solos too (a solo may be silent for bars)."""
    import numpy as np, soundfile as sf, scipy.signal as ss
    y, sr = sf.read(wav)
    y = ss.sosfiltfilt(ss.butter(2, 20, 'highpass', fs=sr, output='sos'), y, axis=0)
    if start is None:   # skip the power-on click and the boot chime: the song is the last sound in the first
        loud = np.abs(y).sum(1) > 0.02      # 6 s that follows half a second of silence
        quiet = 0; start = 0
        for i in np.flatnonzero(np.diff(loud.astype(np.int8)) == 1) + 1:
            if i > 6 * sr: break
            gap = i - (np.flatnonzero(loud[:i])[-1] if loud[:i].any() else 0)
            if gap > sr // 2: start = int(i)
    n = int(nrows * 11 / 59.7275 * sr * loops)
    sf.write(wav, y[start:start + n], sr)
    return start

if __name__ == '__main__':
    args = sys.argv[1:]
    path = next((a for a in args if a.endswith('.song')), 'res/music/gameplay.song')
    loops = int(args[args.index('--loops') + 1]) if '--loops' in args else 1
    s = song.parse(path)
    song.compile_song(s, 'src/music_gameplay.c')
    nrows = len(song.rows(s))
    frames = int(nrows * 11 * loops + 200)
    os.makedirs(OUT, exist_ok=True)
    jobs = []
    if '--solo-only' not in args: jobs.append((15, 'full'))
    if '--no-solo' not in args: jobs += [(1, 'lead'), (2, 'chord'), (4, 'bass'), (8, 'noise')]
    start = None
    if '--solo-only' in args: jobs.insert(0, (15, 'full'))
    for mask, name in jobs:
        rom = build(mask); wav = os.path.join(OUT, name + '.wav')
        record(rom, wav, frames); st = trim(wav, nrows, loops, start)
        if name == 'full': start = st
        print('wrote', wav)
