#!/usr/bin/env python3
"""Score a transcription against the original: synthesize pulse/triangle voices from the note lists and
compare chroma per 16th-note frame. Higher is better; misaligned baseline is ~0."""
import sys, numpy as np, librosa
sys.path.insert(0, 'tools')
ROW = 11 / 60.0
def synth(nrows, voices, sr=22050):
    n = int(nrows * ROW * sr) + sr // 10
    out = np.zeros(n)
    for notes, kind, gain in voices:
        cur = None; start = 0
        events = []
        for r, v in enumerate(notes + [None]):
            if v == 'ring': v = (cur, False) if cur is not None else None   # a stab left to decay
            if v is None or v[1]:
                if cur is not None: events.append((cur, start, r))
                cur = v[0] if v else None; start = r
        for midi, r0, r1 in events:
            f = librosa.midi_to_hz(midi); t = np.arange(int((r1 - r0) * ROW * sr)) / sr
            ph = (t * f) % 1.0
            if kind == 'pulse25': w = np.where(ph < 0.25, 1.0, -1.0)
            elif kind == 'pulse50': w = np.where(ph < 0.5, 1.0, -1.0)
            else: w = 2 * np.abs(2 * ph - 1) - 1
            env = np.exp(-t * 1.5)
            i0 = int(r0 * ROW * sr); out[i0:i0 + len(w)] += gain * w * env
    return out
def score(nrows, lead, harm, bass, orig_path, seconds=None):
    y = synth(nrows, [(lead, 'pulse25', 0.5), (harm, 'pulse50', 0.3), (bass, 'tri', 0.6)])
    o, sr = librosa.load(orig_path, sr=22050, mono=True)
    n = min(len(y), len(o)) if seconds is None else int(seconds * sr)
    y, o = y[:n], o[:n]
    cg = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048); co = librosa.feature.chroma_cqt(y=o, sr=sr, hop_length=2048)
    m = min(cg.shape[1], co.shape[1])
    vals = [np.corrcoef(cg[:, i], co[:, i])[0, 1] for i in range(m) if cg[:, i].std() > 0 and co[:, i].std() > 0]
    return float(np.mean(vals))
if __name__ == '__main__':
    src = open('tools/transcribe.py').read().split("if __name__ == '__main__':")[0]
    ns = {}; exec(src, ns)
    nrows, lead, harm, bass, drums = ns['analyse']('reference/audio/bgm27_gameplay.ogg', True, 352)
    print('baseline score', round(score(nrows, lead, harm, bass, 'reference/audio/bgm27_gameplay.ogg', 30), 3))
    print('lead only', round(score(nrows, lead, [None]*nrows, [None]*nrows, 'reference/audio/bgm27_gameplay.ogg', 30), 3))
    print('bass only', round(score(nrows, [None]*nrows, [None]*nrows, bass, 'reference/audio/bgm27_gameplay.ogg', 30), 3))
