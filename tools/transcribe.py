#!/usr/bin/env python3
"""Approximate chiptune transcription of the reference OGGs into hUGEDriver song data.
Row = 11 frames (an eighth note at the original's 163.6 BPM). Voices: CH1 lead (highest strong pitch),
CH2 harmony (next strong pitch), CH3 bass (lowest strong pitch, wave channel), CH4 drums (percussive onsets).
usage: transcribe.py <ogg> <song_name> <out.c> [--loop] [--rows N]"""
import sys, numpy as np, librosa
from scipy.signal import find_peaks
ROW = 11 / 60.0
NOTE_MIN, NOTE_MAX = 36, 107   # hUGE note table: C3 (index 0) .. B8 ; we map midi 36 (C2) -> hUGE? see below
# hUGE note 0 = C_3 which is midi 48 in tracker naming (C-3 = 130.8 Hz? In hUGETracker C-3 is ~130 Hz = midi 48)
def midi_to_huge(m):  # hUGE note 0 (C_3 in tracker naming) is 65.4 Hz = midi 36
    return m - 36

def analyse(path, loop, rows_override=None):
    y, sr = librosa.load(path, sr=22050, mono=True)
    dur = len(y) / sr
    nrows = rows_override or int(round(dur / ROW))
    yh, yp = librosa.effects.hpss(y)
    hop = 128
    bpo = 36
    fmin = librosa.note_to_hz('C1')
    n_bins = 7 * bpo
    C = np.abs(librosa.cqt(yh, sr=sr, hop_length=hop, fmin=fmin, n_bins=n_bins, bins_per_octave=bpo))
    t = librosa.frames_to_time(np.arange(C.shape[1]), sr=sr, hop_length=hop)
    onset_p = librosa.onset.onset_strength(y=yp, sr=sr, hop_length=hop)
    S = np.abs(librosa.stft(yp, n_fft=1024, hop_length=hop))
    cent = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
    lead, harm, bass, drums = [], [], [], []
    prev = {'lead': None, 'harm': None, 'bass': None}
    gmax = C.max()
    for r in range(nrows):
        a, b = r * ROW, (r + 1) * ROW
        m = (t >= a + 0.02) & (t < b - 0.01)
        if not m.any(): m = (t >= a) & (t < b)
        spec = C[:, m].mean(axis=1) if m.any() else np.zeros(n_bins)
        semi = spec.reshape(-1, 3).max(axis=1)          # one value per semitone, midi 24..107
        pk, props = find_peaks(semi, prominence=0.15 * (semi.max() + 1e-9))
        cands = sorted([(int(p) + 24, float(semi[p])) for p in pk if semi[p] > 0.06 * gmax], key=lambda x: -x[1])
        cands = cands[:6]
        # bass: lowest candidate below midi 60 (C4) that is reasonably strong
        low = [c for c in cands if c[0] < 60]
        high = [c for c in cands if c[0] >= 55]
        bn = min(low, key=lambda c: c[0])[0] if low else None
        # lead: strongest candidate at/above C4 that is not the bass' harmonic (octave)
        hi_sorted = sorted(high, key=lambda c: -c[1])
        ln = None; hn = None
        for c in hi_sorted:
            if bn is not None and (c[0] - bn) % 12 == 0 and c[1] < 1.5 * dict(low)[bn]: continue
            if ln is None: ln = c[0]
            elif hn is None and c[0] != ln: hn = c[0]
        if ln is not None and hn is not None and hn > ln: ln, hn = hn, ln   # lead = higher voice
        # onset detection per voice: new note if pitch changed or harmonic energy rose sharply at the row start
        mstart = (t >= a) & (t < a + 0.06)
        def energy(mask, note):
            if note is None or not mask.any(): return 0.0
            i = (note - 24) * 3
            return float(C[i:i+3, mask].max())
        def voice(name, note):
            if note is None: prev[name] = None; return None
            e0 = energy(mstart, note); e_prev = prev[name][1] if prev[name] else 0.0
            new = prev[name] is None or prev[name][0] != note or e0 > 1.6 * e_prev
            prev[name] = (note, e0)
            return (note, new)
        lead.append(voice('lead', ln)); harm.append(voice('harm', hn)); bass.append(voice('bass', bn))
        # drums: percussive onset strength in the first 1/3 of the row
        mm = (t >= a - 0.02) & (t < a + ROW / 3)
        o = float(onset_p[mm].max()) if mm.any() else 0.0
        c = float(cent[mm].mean()) if mm.any() else 0.0
        drums.append((o, c))
    omax = max(d[0] for d in drums) + 1e-9
    drum_rows = []
    for o, c in drums:
        if o < 0.25 * omax: drum_rows.append(None)
        else: drum_rows.append('snare' if c > 3000 else 'kick')
    return nrows, lead, harm, bass, drum_rows

def emit(name, nrows, lead, harm, bass, drums, loop, out):
    def cell(note, instr, fx=0):
        return 'DN(%d,%d,0x%03X)' % (note, instr, fx)
    npat = (nrows + 63) // 64
    pats = {1: [], 2: [], 3: [], 4: []}
    for p in range(npat):
        rows = {1: [], 2: [], 3: [], 4: []}
        for r in range(64):
            i = p * 64 + r
            if i >= nrows:
                for ch in rows: rows[ch].append(cell(90, 0, 0))
                continue
            for ch, v, instr in ((1, lead, 1), (2, harm, 2), (3, bass, 1)):
                n = v[i]
                if n is None: rows[ch].append(cell(90, 0, 0x000) if (i == 0 or v[i-1] is None) else cell(90, 0, 0xE00))  # note cut when a voice stops... hUGE has no cut; use volume 0? keep silent via instrument 0? simpler: E00 = no-op
                elif n[1]: rows[ch].append(cell(midi_to_huge(n[0]) if 0 <= midi_to_huge(n[0]) < 72 else 90, instr, 0))
                else: rows[ch].append(cell(90, 0, 0))
            d = drums[i]
            rows[4].append(cell(90, 0, 0) if d is None else cell(24 if d == 'kick' else 36, 1 if d == 'kick' else 2, 0))
        # pattern break (D00) on the song's last row so the order list wraps there
        end_row = nrows - p * 64
        if 0 < end_row < 64:
            rows[1][end_row - 1] = rows[1][end_row - 1][:-6] + '0xD00)'
        for ch in rows: pats[ch].append(rows[ch])
    lines = []
    for ch in (1, 2, 3, 4):
        for p, rows in enumerate(pats[ch]):
            lines.append('static const unsigned char %s_c%dp%d[] = {' % (name, ch, p))
            for k in range(0, 64, 4): lines.append('    ' + ','.join(rows[k:k+4]) + ',')
            lines.append('};')
    lines.append('static const unsigned char %s_order_cnt = %d;' % (name, 2 * npat))
    for ch in (1, 2, 3, 4):
        lines.append('static const unsigned char* const %s_order%d[] = { %s };' % (name, ch, ', '.join('%s_c%dp%d' % (name, ch, p) for p in range(npat))))
    lines.append('''static const hUGEDutyInstr_t NAME_duty[] = {
    {0, 0x80, 0xB2, 0, 128},   /* 0 unused */
    {0, 0x40, 0xC0, 0, 128},   /* 1 lead: 25% duty, sustained */
    {0, 0x80, 0x70, 0, 128},   /* 2 harmony: 50% duty, softer, sustained */
};
static const hUGEWaveInstr_t NAME_wave[] = {
    {0, 32, 0, 0, 128},        /* 0 unused */
    {0, 32, 0, 0, 128},        /* 1 bass: full volume, wave 0 */
};
static const hUGENoiseInstr_t NAME_noise[] = {
    {0xA1, 0, 0, 0, 0},        /* 0 unused */
    {0xC1, 0, 0, 0, 0},        /* 1 kick: short */
    {0x91, 0, 0, 0, 0},        /* 2 snare */
};
static const unsigned char NAME_waves[] = {
    0x02,0x46,0x8A,0xCE,0xFD,0xB9,0x75,0x31,0x02,0x46,0x8A,0xCE,0xFD,0xB9,0x75,0x31,   /* triangle, two cycles so the wave channel matches the pulse octave */
};
const hUGESong_t NAME = { 11, &NAME_order_cnt, NAME_order1, NAME_order2, NAME_order3, NAME_order4, NAME_duty, NAME_wave, NAME_noise, NULL, NAME_waves };
'''.replace('NAME', name))
    open(out, 'w').write('\n'.join(lines) + '\n')

if __name__ == '__main__':
    path, name, out = sys.argv[1:4]
    loop = '--loop' in sys.argv
    rows = None
    if '--rows' in sys.argv: rows = int(sys.argv[sys.argv.index('--rows') + 1])
    nrows, lead, harm, bass, drums = analyse(path, loop, rows)
    emit(name, nrows, lead, harm, bass, drums, loop, out)
    # summary
    def fmt(v): return '-' if v is None else ('%s%s' % (librosa.midi_to_note(v[0]), '*' if v[1] else ''))
    print(name, 'rows', nrows)
    for bar in range(0, min(nrows, 64), 8):
        print('bar %2d lead %s' % (bar // 8, ' '.join('%-5s' % fmt(lead[i]) for i in range(bar, bar + 8))))
        print('       harm %s' % ' '.join('%-5s' % fmt(harm[i]) for i in range(bar, bar + 8)))
        print('       bass %s' % ' '.join('%-5s' % fmt(bass[i]) for i in range(bar, bar + 8)))
        print('       drum %s' % ' '.join('%-5s' % (drums[i] or '-') for i in range(bar, bar + 8)))
