#!/usr/bin/env python3
"""Approximate chiptune transcription of the reference OGGs into hUGEDriver song data.

Row = 11 frames (an eighth note at the original's 163.6 BPM), 8 rows to a bar.

Each voice is tracked inside its own register band with a leap penalty (Viterbi), so a voice cannot
swap roles with another or jump octaves when a harmonic happens to be louder than the fundamental:
picking the loudest peak per row independently gave a lead that leapt 11 semitones on average across
four octaves, which reads as noise rather than melody. Notes are then articulated only where the pitch
really changes or the attack is strong, the accompaniment is quantised to the bar grid, and the drums
are a fixed kick/snare pattern gated by percussive energy. Where the lead band is loudest (the song's
peak) the accompaniment thins to one chord a bar so the melody is exposed.

usage: transcribe.py <ogg> <song_name> <out.c> [--loop] [--rows N]
"""
import sys, numpy as np, librosa
ROW = 11 / 60.0
BAR = 8                      # rows per bar

# midi bands, one per voice; hUGE note 0 is midi 36 (65.4 Hz) and the table ends at note 71
BASS_LO, BASS_HI = 36, 56
HARM_LO, HARM_HI = 55, 72
LEAD_LO, LEAD_HI = 67, 91

def midi_to_huge(m):
    return m - 36

def _salience(y, sr, nrows):
    """per-row, per-semitone energy of the harmonic part: sustained (mean) and attack (row onset)"""
    hop, bpo = 128, 36
    C = np.abs(librosa.cqt(y, sr=sr, hop_length=hop, fmin=librosa.note_to_hz('C1'),
                           n_bins=7 * bpo, bins_per_octave=bpo))
    t = librosa.frames_to_time(np.arange(C.shape[1]), sr=sr, hop_length=hop)
    S = np.zeros((nrows, 84)); A = np.zeros((nrows, 84))
    for r in range(nrows):
        a, b = r * ROW, (r + 1) * ROW
        m = (t >= a + 0.02) & (t < b - 0.01)
        if not m.any(): m = (t >= a) & (t < b)
        S[r] = C[:, m].mean(axis=1).reshape(-1, 3).max(axis=1)
        ms = (t >= a) & (t < a + 0.06)
        A[r] = (C[:, ms].max(axis=1).reshape(-1, 3).max(axis=1)) if ms.any() else S[r]
    return S, A

def _track(S, lo, hi, pen, rest_frac):
    """best-cost path through one register band; returns a midi note or None per row"""
    nr = S.shape[0]; ns = hi - lo
    E = S[:, lo - 24:hi - 24]
    scale = np.median(E.max(axis=1)) + 1e-9
    E = E / scale
    idx = np.arange(ns)
    step = pen * np.minimum(np.abs(idx[None, :] - idx[:, None]), 12)   # cost of moving k -> j
    cost = np.zeros((nr, ns)); back = np.zeros((nr, ns), dtype=np.int16)
    cost[0] = E[0]
    for r in range(1, nr):
        M = cost[r - 1][None, :] - step
        k = M.argmax(axis=1)
        cost[r] = M[idx, k] + E[r]; back[r] = k
    path = [int(cost[-1].argmax())]
    for r in range(nr - 1, 0, -1): path.append(int(back[r, path[-1]]))
    path = path[::-1]
    return [(p + lo) if E[r, p] > rest_frac else None for r, p in enumerate(path)]

def _articulate(line, A, lo, grid=1, attack=1.7):
    """(note, is_new) per row: a new note on a pitch change, or a clear re-attack of the same pitch.
       grid > 1 restricts note starts to every `grid`-th row, which thins an accompaniment part."""
    out = []; cur = None; cur_att = 0.0
    for r, n in enumerate(line):
        if n is None:
            out.append(None); cur = None; continue
        att = float(A[r, n - 24])
        new = False
        if cur != n: new = True
        elif att > attack * cur_att: new = True
        if new and grid > 1 and (r % grid) and cur is not None: new = False
        if new:
            cur = n; cur_att = att
            out.append((n, True))
        else:
            cur_att = max(cur_att, att) if cur == n else cur_att
            out.append((n, False))
    return out

def _hold_through_rests(line, max_gap=2):
    """bridge one- or two-row dropouts inside a held note so a voice does not stutter"""
    out = list(line)
    r = 0
    while r < len(out):
        if out[r] is None:
            j = r
            while j < len(out) and out[j] is None: j += 1
            if 0 < r and j < len(out) and (j - r) <= max_gap and out[r - 1] == out[j]:
                for k in range(r, j): out[k] = out[r - 1]
            r = j
        else: r += 1
    return out

def analyse(path, loop, rows_override=None):
    y, sr = librosa.load(path, sr=22050, mono=True)
    nrows = rows_override or int(round((len(y) / sr) / ROW))
    yh, yp = librosa.effects.hpss(y)
    S, A = _salience(yh, sr, nrows)

    lead_line = _hold_through_rests(_track(S, LEAD_LO, LEAD_HI, 0.055, 0.42))
    harm_line = _hold_through_rests(_track(S, HARM_LO, HARM_HI, 0.090, 0.45))
    bass_line = _hold_through_rests(_track(S, BASS_LO, BASS_HI, 0.090, 0.40))

    # the peak: bars whose lead-band energy is in the top 40%. There the accompaniment moves once a bar.
    nbars = (nrows + BAR - 1) // BAR
    bar_lead = np.array([S[b * BAR:(b + 1) * BAR, LEAD_LO - 24:LEAD_HI - 24].sum() for b in range(nbars)])
    peak = bar_lead >= np.percentile(bar_lead, 60)

    lead = _articulate(lead_line, A, LEAD_LO)
    harm_fine = _articulate(harm_line, A, HARM_LO, grid=4)
    harm_wide = _articulate(harm_line, A, HARM_LO, grid=8)
    harm = [ (harm_wide if peak[i // BAR] else harm_fine)[i] for i in range(nrows) ]
    bass = _articulate(bass_line, A, BASS_LO, grid=2)

    # drums: kick on beat 1, snare on beat 3, only in bars with real percussive energy;
    # a peak bar gets an extra kick before the snare for drive.
    onset = librosa.onset.onset_strength(y=yp, sr=sr, hop_length=128)
    ot = librosa.frames_to_time(np.arange(len(onset)), sr=sr, hop_length=128)
    bar_hit = []
    for b in range(nbars):
        m = (ot >= b * BAR * ROW) & (ot < (b + 1) * BAR * ROW)
        bar_hit.append(float(onset[m].mean()) if m.any() else 0.0)
    thr = 0.35 * (max(bar_hit) + 1e-9)
    drums = []
    for r in range(nrows):
        b, inbar = r // BAR, r % BAR
        if bar_hit[b] < thr: drums.append(None); continue
        if inbar == 0: drums.append('kick')
        elif inbar == 4: drums.append('snare')
        elif inbar == 3 and peak[b]: drums.append('kick')
        else: drums.append(None)
    return nrows, lead, harm, bass, drums

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
    lines.append('''/* The driver does `dec a` on the instrument id (0 means "no instrument"), so instrument 1 is
   entry [0] here. A leading "unused" row would hand the lead the wrong instrument - which is what
   used to happen: the melody played a decaying 50% patch while the harmony got the loud sustained
   one, and the tune sat underneath its own accompaniment. */
static const hUGEDutyInstr_t NAME_duty[] = {
    {0, 0x40, 0xF0, 0, 128},   /* 1 lead: 25% duty, full volume, sustained - it has to carry */
    {0, 0x80, 0x40, 0, 128},   /* 2 harmony: 50% duty at a quarter of the lead, stays underneath */
};
static const hUGEWaveInstr_t NAME_wave[] = {
    {0, 0x20, 0, 0, 128},      /* 1 bass: triangle at full volume - a different register from the lead, so it does not mask it */
};
static const hUGENoiseInstr_t NAME_noise[] = {
    {0xB1, 0, 0, 0, 0},        /* 1 kick: short */
    {0x71, 0, 0, 0, 0},        /* 2 snare: under the kick so the backbeat does not clutter */
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
    for bar in range(0, min(nrows - 8, 64), 8):
        print('bar %2d lead %s' % (bar // 8, ' '.join('%-5s' % fmt(lead[i]) for i in range(bar, bar + 8))))
        print('       harm %s' % ' '.join('%-5s' % fmt(harm[i]) for i in range(bar, bar + 8)))
        print('       bass %s' % ' '.join('%-5s' % fmt(bass[i]) for i in range(bar, bar + 8)))
        print('       drum %s' % ' '.join('%-5s' % (drums[i] or '-') for i in range(bar, bar + 8)))
