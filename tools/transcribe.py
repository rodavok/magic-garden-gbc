#!/usr/bin/env python3
"""Approximate chiptune transcription of the reference OGGs into hUGEDriver song data.

Row = 11 frames (an eighth note at the original's 163.6 BPM), 8 rows to a bar.

Each voice is tracked inside its own register band with a leap penalty (Viterbi), so a voice cannot
swap roles with another or jump octaves when a harmonic happens to be louder than the fundamental:
picking the loudest peak per row independently gave a lead that leapt 11 semitones on average across
four octaves, which reads as noise rather than melody.

What the gameplay track actually is (measured, see CLAUDE.md): a bright bass that moves nearly every
row and fills 160-640 Hz with its overtones, chord stabs on the 3-3-2 accents (rows 1, 4 and 6 of the
bar), a light noise tick on the same accents, and a plucked lead - every voice decays within a row.
So: the bass is a one-cycle wave with the original's overtone balance (which also reaches down to G1),
the harmony channel plays a short decaying stab only on rows where the original has a mid-band attack,
the noise channel ticks only where the original has a high-band attack, and repeated notes are
re-struck when the original re-strikes them. There is no kick/snare: an imposed backbeat put the snare
on row 5, the quietest row of the original's bar.

usage: transcribe.py <ogg> <song_name> <out.c> [--loop] [--rows N]
"""
import sys, numpy as np, librosa
ROW = 11 / 60.0
BAR = 8                      # rows per bar

# midi bands, one per voice; hUGE note 0 is midi 36 (65.4 Hz) on the pulse channels and the table ends
# at note 71. The bass wave is one cycle per 32 samples, which sounds an octave lower: note 0 is midi 24.
BASS_LO, BASS_HI = 31, 56
HARM_LO, HARM_HI = 55, 72
LEAD_LO, LEAD_HI = 67, 91

def midi_to_huge(m):
    return m - 36

def midi_to_huge_wave(m):
    return m - 24

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

def _track(S, lo, hi, pen, rest_frac, E=None):
    """best-cost path through one register band; returns a midi note or None per row"""
    nr = S.shape[0]; ns = hi - lo
    if E is None: E = S[:, lo - 24:hi - 24]
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

def _gate(line, struck):
    """notes change only on rows in `struck` (where the original has an attack in this voice's range);
       elsewhere the sounding note is held. Between the original's attacks the pitch tracker mostly hears
       other voices' partials: in the intro the lead range is silent between chord hits, and following
       those partials gave a note on every row where the original has three a bar."""
    out = []; held = None
    for r, v in enumerate(line):
        if v is None: out.append(None); held = None
        elif struck[r] or held is None:
            if v[1] or v[0] != held: out.append((v[0], True))
            else: out.append((v[0], False))
            held = v[0]
        else: out.append((held, False))
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

    # bass: score each candidate by its own partials, so the fundamental wins over the octave its
    # bright timbre makes nearly as loud
    Eb = np.array([S[:, m - 24] + 0.6 * S[:, m - 12] + 0.4 * S[:, m - 5] for m in range(BASS_LO, BASS_HI)]).T
    bass_line = _hold_through_rests(_track(S, BASS_LO, BASS_HI, 0.090, 0.40, Eb))

    # harmony: the loudest real peak in the harmony band that is neither a bass partial nor the lead.
    # (Discounting those bins and taking the maximum instead picks their spill into the next semitone.)
    def harm_note(r):
        v = S[r]; cands = []
        for m in range(HARM_LO, HARM_HI):
            k = m - 24
            if not (v[k] >= v[k - 1] and v[k] >= v[k + 1]): continue
            b, l = bass_line[r], lead_line[r]
            partial = b is not None and (m - b) in (12, 19, 24, 28, 31)
            lead_oct = l is not None and (l - m) % 12 == 0
            cands.append((v[k] * (0.3 if partial or lead_oct else 1.0), m))
        return max(cands)[1] if cands else None
    # attacks per row from spectral flux around the row start, relative to the song's median
    Sf = np.abs(librosa.stft(y, n_fft=1024, hop_length=64))
    f = librosa.fft_frequencies(sr=sr, n_fft=1024)
    tf = librosa.frames_to_time(np.arange(Sf.shape[1]), sr=sr, hop_length=64)
    def flux(lo, hi):
        B = Sf[(f >= lo) & (f < hi)]
        d = np.maximum(0, np.diff(B, axis=1, prepend=B[:, :1])).sum(0)
        v = np.array([d[(tf >= r * ROW - 0.02) & (tf < r * ROW + 0.04)].max() for r in range(nrows)])
        return v / (np.median(v) + 1e-9)
    stab = flux(250, 1500) > 1.3
    tick = flux(5000, 11000) > 1.3

    # a voice only strikes where the original has an attack in its range. The original is silent on row 5
    # of the bar, and restriking there flattened the 3-3-2 accents into eight even beats.
    lead = _gate(_articulate(lead_line, A, LEAD_LO, attack=1.25), flux(700, 2500) > 1.0)
    bass = _gate(_articulate(bass_line, A, BASS_LO, attack=1.3), flux(0, 200) > 1.0)
    harm = []
    for r in range(nrows):
        n = harm_note(r) if stab[r] else None
        harm.append((n, True) if n is not None else 'ring')
    drums = ['tick' if tick[r] else None for r in range(nrows)]
    return nrows, lead, harm, bass, drums

TICK_NOTE = 60   # high noise pitch

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
                if n == 'ring': rows[ch].append(cell(90, 0, 0)); continue   # a stab decays on its own
                if n is None: rows[ch].append(cell(90, 0, 0x000) if (i == 0 or v[i-1] is None) else cell(90, 0, 0xE00))  # note cut when a voice stops... hUGE has no cut; use volume 0? keep silent via instrument 0? simpler: E00 = no-op
                elif n[1]:
                    h = midi_to_huge_wave(n[0]) if ch == 3 else midi_to_huge(n[0])
                    if not 0 <= h < 72: rows[ch].append(cell(90, 0, 0))
                    else: rows[ch].append(cell(h, instr, 0))
                else: rows[ch].append(cell(90, 0, 0))
            d = drums[i]
            rows[4].append(cell(90, 0, 0) if d is None else cell(TICK_NOTE, 1, 0))
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
    {0, 0x40, 0xC4, 0, 128},   /* 1 lead: 25% duty (its octave partial matches the original's), volume 12 fading a step per 4/64 s: about a quarter down by the end of a row, like the original's pluck */
    {0, 0x80, 0x92, 0, 128},   /* 2 stab: 50% duty, volume 9 gone in about a row and a half */
};
static const hUGEWaveInstr_t NAME_wave[] = {
    {0, 0x20, 0, 0, 128},      /* 1 bass: full volume */
};
static const hUGENoiseInstr_t NAME_noise[] = {
    {0x41, 0, 0, 0, 0},        /* 1 tick: quiet and short, on the accents only */
};
static const unsigned char NAME_waves[] = {
    0x8B,0xEF,0xEC,0xA9,0x89,0x99,0x98,0x77,0x88,0x87,0x66,0x66,0x76,0x53,0x10,0x14,   /* one bright cycle: partials 2-4 at -1, -3, -7 dB like the original bass (a triangle has almost none) */
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
    def fmt(v): return '.' if v == 'ring' else '-' if v is None else ('%s%s' % (librosa.midi_to_note(v[0]), '*' if v[1] else ''))
    print(name, 'rows', nrows)
    for bar in range(0, min(nrows - 8, 64), 8):
        print('bar %2d lead %s' % (bar // 8, ' '.join('%-5s' % fmt(lead[i]) for i in range(bar, bar + 8))))
        print('       harm %s' % ' '.join('%-5s' % fmt(harm[i]) for i in range(bar, bar + 8)))
        print('       bass %s' % ' '.join('%-5s' % fmt(bass[i]) for i in range(bar, bar + 8)))
        print('       drum %s' % ' '.join('%-5s' % (drums[i] or '-') for i in range(bar, bar + 8)))
