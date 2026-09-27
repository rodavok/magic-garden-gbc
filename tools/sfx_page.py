#!/usr/bin/env python3
"""Sound-effect board in build/sfx/: every game event with the original's effect and the port's side by side,
each with a spectrogram. Builds tools/sfxtest/main.c (every effect in src/sfx.c in turn, no music), records it
in SameBoy and cuts the recording into one WAV per effect. Serve build/sfx (the "sfx-board" entry in
.claude/launch.json) and open index.html.

Needs the original effects in reference/audio: tools/extract_gm.py --audio-only
usage: sfx_page.py
"""
import json, os, re, shutil, subprocess, time
import numpy as np, soundfile as sf, scipy.signal as ss
from PIL import Image

GBDK = os.environ.get('GBDK_HOME', os.path.expanduser('~/.local/opt/gbdk'))
LCC = os.path.join(GBDK, 'bin', 'lcc')
BOOT = os.path.expanduser('~/.local/opt/SameBoy-1.0.3/build/bin/BootROMs/cgb_boot.bin')
OUT = 'build/sfx'
FPS = 59.7275
GAP = 150                      # frames between effects in the test ROM
# in the order tools/sfxtest/main.c plays them
PORT = ['pickup_a', 'pickup_b', 'pickup_c', 'pickup_d', 'sfx_jump', 'sfx_bad_drop', 'sfx_save', 'sfx_flask', 'sfx_kill', 'sfx_tick',
        'sfx_death']
# what the original plays for each event (reference/gml; scrSfx keeps one effect a frame, highest priority wins)
EVENTS = [
    ('Collect an oppie', 'Walking onto a loose oppie adds it to the trail.',
     ['sfx_collect05a', 'sfx_collect05b', 'sfx_collect05c', 'sfx_collect05d'],
     ['pickup_a', 'pickup_b', 'pickup_c', 'pickup_d'],
     'Both pick one of four at random every time; the variant buttons switch both sides.'),
    ('Jump', 'A while grounded.', ['sfx_jump03'], 'sfx_jump', ''),
    ('Drop-off, nothing saved', 'B with no trail oppie on the star pad.', ['sfx_nope03'], 'sfx_bad_drop', ''),
    ('Drop-off, oppies saved', 'B with at least one oppie on the pad (plays once per drop).',
     ['sfx_score03'], 'sfx_save',
     'The original calls nope03 then score03 in the same frame; score03 has the higher priority and replaces it.'),
    ('Flask lands', 'A new flask reaches the floor after its 90-unit fall.', ['sfx_glass00'], None,
     'The port plays nothing here yet.'),
    ('Flask pickup', 'Walking over a flask: power starts.', ['sfx_special02'], 'sfx_flask', ''),
    ('Eat an enemy', 'Touching an angry oppie (or a mushroom with blue+) while powered.',
     ['sfx_die00'], 'sfx_kill', ''),
    ('Power running out', 'At 150, 100 and 50 frames of power left.', ['sfx_select06'], 'sfx_tick', ''),
    ('Death', 'Touching an enemy without power.', ['sfx_bonk00'], 'sfx_death',
     'The original follows it with the lose sting; the port starts the sting on the same frame.'),
]
PORT_SRC = {}   # sfx name -> its line in src/sfx.c, or where its table is

def build():
    obj = os.path.join(OUT, 'obj'); os.makedirs(obj, exist_ok=True)
    objs = []
    for src in ('tools/sfxtest/main.c', 'src/sfx.c', 'src/sfx_tables.c', 'src/music.c', 'src/music_data.c', 'src/music_gameplay.c'):
        o = os.path.join(obj, os.path.basename(src)[:-2] + '.o')
        subprocess.run([LCC, '-Iinclude', '-Wf--opt-code-speed', '-c', '-o', o, src], check=True); objs.append(o)
    o = os.path.join(obj, 'hugebank.o'); subprocess.run([LCC, '-c', '-o', o, 'src/hugebank.s'], check=True); objs.append(o)
    rom = os.path.join(OUT, 'sfxtest.gbc')
    subprocess.run([LCC, '-Wm-yC', '-Wm-yt0x1B', '-Wm-ya1', '-Wl-yo4', '-o', rom] + objs + ['lib/hUGEDriver.o'], check=True)
    return rom

def record(rom):
    wav = os.path.join(OUT, 'all.wav')
    frames = 600 + 240 + len(PORT) * GAP
    env = dict(os.environ, SAMEBOY_BOOT=BOOT, SAMEBOY_WAV=wav)
    subprocess.run(['tools/sameboy/dump', rom, str(frames), os.path.join(OUT, 'shot')], env=env, check=True,
                   stdout=subprocess.DEVNULL)
    return wav

def cut(wav):
    """one clip per effect. The effects start every GAP frames, so the first one is the onset that lines up
       with the most onsets at that spacing (the boot chime and the power-on click do not)"""
    y, sr = sf.read(wav)
    y = ss.sosfiltfilt(ss.butter(2, 20, 'highpass', fs=sr, output='sos'), y, axis=0)
    loud = np.abs(y).sum(1) > 0.01
    on = np.flatnonzero(np.diff(loud.astype(np.int8)) == 1) + 1
    step = GAP / FPS * sr
    tol = 0.02 * sr
    hits = lambda i: sum(np.any(np.abs(on - (i + k * step)) < tol) for k in range(len(PORT)))
    first = int(max(on, key=hits))
    assert hits(first) >= len(PORT) - 1, 'effects not found in the recording'
    out = {}
    for k, name in enumerate(PORT):
        a = int(first + k * step) - int(0.004 * sr)
        clip = y[a:a + int(step) - int(0.05 * sr)]
        lv = np.flatnonzero(np.abs(clip).sum(1) > 0.004)
        clip = clip[:(lv[-1] + int(0.03 * sr)) if len(lv) else int(0.1 * sr)]
        fade = np.linspace(1, 0, min(len(clip), int(0.01 * sr)))[:, None]
        clip[-len(fade):] *= fade
        path = os.path.join(OUT, 'port_%s.wav' % name)
        sf.write(path, clip, sr); out[name] = path
    return out

LO_HZ, HI_HZ, SPEC_H, PX_S = 60.0, 12000.0, 128, 400

def spectro(path, png):
    """log-frequency spectrogram, PX_S pixels a second, SPEC_H rows from LO_HZ (bottom) to HI_HZ"""
    y, sr = sf.read(path)
    if y.ndim > 1: y = y.mean(1)
    hop = int(sr / PX_S)
    f, t, Z = ss.stft(y, fs=sr, nperseg=2048, noverlap=2048 - hop, boundary=None, padded=True)
    M = np.abs(Z)
    edges = np.geomspace(LO_HZ, HI_HZ, SPEC_H + 1)
    rows = np.stack([M[(f >= edges[i]) & (f < edges[i + 1])].max(0) if ((f >= edges[i]) & (f < edges[i + 1])).any()
                     else M[np.argmin(np.abs(f - edges[i]))] for i in range(SPEC_H)])
    L = 20 * np.log10(rows / (rows.max() + 1e-12) + 1e-9)
    L = np.clip((L + 60) / 60, 0, 1)[::-1]
    rgb = (np.stack([L, L ** 1.6, L ** 3.5], -1) * 255).astype(np.uint8)
    Image.fromarray(rgb).save(png)
    return len(y) / sr, float(np.abs(y).max()), float(np.sqrt((y ** 2).mean()))

def clip_info(name, wav):
    png = os.path.join(OUT, name + '.png')
    dur, peak, rms = spectro(wav, png)
    return {'name': name, 'wav': os.path.basename(wav), 'png': os.path.basename(png),
            'dur': round(dur, 3), 'peak': round(peak, 4), 'rms': round(rms, 5)}

def port_source():
    for line in open('src/sfx.c'):
        s = line.strip()
        if s.startswith('void sfx_') and '{' in s and '(void)' in s:
            PORT_SRC[s.split('(')[0][5:]] = s[s.index('{'):]
    tables = open('tools/sfx_tables.py').read()
    for n in PORT:
        key = n[4:] if n.startswith('sfx_') else n
        body = PORT_SRC.get(n, '')
        m = re.search(r'SFX_([A-Z_]+)', body)
        prog = key if "'%s'" % key in tables else (m[1].lower() if m else None)
        if prog: PORT_SRC[n] = 'tools/sfx_tables.py: %s' % prog

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    port_source()
    port = cut(record(build()))
    data = {'build': int(time.time()), 'pxPerSec': PX_S,   # build: cache-buster for the clip URLs
            'loHz': LO_HZ, 'hiHz': HI_HZ, 'specH': SPEC_H, 'events': []}
    for title, when, orig, p, note in EVENTS:
        ev = {'title': title, 'when': when, 'note': note, 'orig': []}
        for o in orig:
            src = 'reference/audio/%s.wav' % o
            assert os.path.exists(src), src + ' missing: run tools/extract_gm.py --audio-only'
            dst = os.path.join(OUT, 'orig_%s.wav' % o); shutil.copy(src, dst)
            ev['orig'].append(clip_info('orig_' + o, dst))
        ev['port'] = []
        for q in ([p] if isinstance(p, str) else p or []):
            c = clip_info('port_' + q, port[q]); c['code'] = PORT_SRC.get(q, ''); ev['port'].append(c)
        data['events'].append(ev)
    json.dump(data, open(os.path.join(OUT, 'sfx.json'), 'w'), indent=1)
    shutil.copy(os.path.join(os.path.dirname(__file__), 'sfx_page.html'), os.path.join(OUT, 'index.html'))
    print('wrote %s/index.html (%d events)' % (OUT, len(data['events'])))
