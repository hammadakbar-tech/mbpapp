"""Original procedural soundtrack + sound effects (no third-party audio)."""
import numpy as np

SR = 44100


def _env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / r)


def _reverb(x, secs=1.8, mix=0.25, seed=0):
    rng = np.random.default_rng(seed)
    n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.2)
    ir[:200] = 0
    ir /= np.sqrt((ir ** 2).sum())
    wet = np.real(np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n)))[:len(x)]
    return x * (1 - mix) + wet * mix * 0.6


def _lp(x, k):
    """cheap one-pole low-pass, k in (0,1]: smaller = darker"""
    from scipy.signal import lfilter
    return lfilter([k], [1, k - 1], x)


def _hp(x, k):
    return x - _lp(x, k)


def note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def music(total, intensity):
    """total seconds; intensity(t)->0..1 controls which layers play."""
    n = int(total * SR)
    out = np.zeros(n)
    bpm = 96
    beat = 60 / bpm
    bar = beat * 4
    # A minor: Am - F - C - G   (root midi notes)
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (60, [55, 60, 64]), (55, [55, 59, 62])]
    t_all = np.arange(n) / SR
    inten = np.array([intensity(x) for x in np.arange(0, total, 0.05)])
    inten = np.interp(t_all, np.arange(len(inten)) * 0.05, inten)
    rng = np.random.default_rng(3)

    pad = np.zeros(n); bass = np.zeros(n); arp = np.zeros(n); drums = np.zeros(n)
    nbars = int(total / bar) + 1
    for b in range(nbars):
        t0 = b * bar
        root, chord = prog[b % 4]
        i0 = int(t0 * SR); i1 = min(n, int((t0 + bar) * SR))
        if i0 >= n: break
        tt = np.arange(i1 - i0) / SR
        # pad: detuned saws (band-limited approximation via few harmonics)
        p = np.zeros(i1 - i0)
        for m in chord:
            for det in (-0.08, 0.08):
                f = note(m + 12) * (1 + det / 100)
                for h in range(1, 7):
                    p += np.sin(2 * np.pi * f * h * tt + h) / h
        fade = np.minimum(tt / 0.4, 1) * np.minimum((bar - tt) / 0.4, 1)
        pad[i0:i1] += p * fade * 0.012
        # bass: pulsing eighths
        for k in range(8):
            j0 = i0 + int(k * beat / 2 * SR); j1 = min(n, j0 + int(beat / 2 * SR * 0.9))
            if j0 >= n: break
            ttt = np.arange(j1 - j0) / SR
            f = note(root - 12)
            s = np.sin(2 * np.pi * f * ttt) + 0.4 * np.sin(2 * np.pi * 2 * f * ttt) + 0.15 * np.sign(np.sin(2 * np.pi * f * ttt))
            bass[j0:j1] += s * _env(j1 - j0, 0.004, 0.18) * 0.09
        # arp: sixteenths over chord tones, two octaves
        tones = [m + 24 for m in chord] + [chord[1] + 36]
        for k in range(16):
            j0 = i0 + int(k * beat / 4 * SR); j1 = min(n, j0 + int(0.25 * SR))
            if j0 >= n: break
            ttt = np.arange(j1 - j0) / SR
            f = note(tones[(k * 3 + b) % len(tones)])
            s = np.sin(2 * np.pi * f * ttt) * 0.7 + np.sin(2 * np.pi * 2 * f * ttt) * 0.2
            arp[j0:j1] += s * _env(j1 - j0, 0.002, 0.07) * 0.035
        # drums
        for k in range(4):
            j0 = i0 + int(k * beat * SR)
            if j0 >= n: break
            # kick on 1 and 3, plus pickup
            if k in (0, 2):
                m_ = min(n - j0, int(0.35 * SR)); ttt = np.arange(m_) / SR
                f = 50 + 90 * np.exp(-ttt * 30)
                drums[j0:j0 + m_] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-ttt * 9) * 0.32
            if k in (1, 3):  # snare-ish clap
                m_ = min(n - j0, int(0.25 * SR)); ttt = np.arange(m_) / SR
                nz = _hp(rng.standard_normal(m_), 0.3)
                drums[j0:j0 + m_] += nz * np.exp(-ttt * 22) * 0.09 + np.sin(2 * np.pi * 190 * ttt) * np.exp(-ttt * 30) * 0.08
            for h in range(2):   # hats on eighths
                jj = j0 + int(h * beat / 2 * SR); m_ = min(n - jj, int(0.06 * SR))
                if m_ <= 0: continue
                ttt = np.arange(m_) / SR
                drums[jj:jj + m_] += _hp(rng.standard_normal(m_), 0.9) * np.exp(-ttt * 70) * (0.035 if h else 0.05)
    pad = _lp(pad, 0.25)
    # layer gating by intensity
    g_pad = 0.7 + 0.3 * inten
    g_bass = np.clip((inten - 0.15) / 0.2, 0, 1)
    g_arp = np.clip((inten - 0.35) / 0.2, 0, 1)
    g_drm = np.clip((inten - 0.55) / 0.2, 0, 1)
    out = pad * g_pad + bass * g_bass + arp * g_arp + drums * g_drm
    out = _reverb(out, 2.2, 0.3)
    return out


def sfx_sink(n_total, t, gain=1.0, out=None):
    """bubbly 'bloop' + splash."""
    m = int(0.5 * SR); i0 = int(t * SR)
    if i0 + m >= len(out): return
    tt = np.arange(m) / SR
    f = 700 * np.exp(-tt * 6) + 120
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * 0.25
    nz = np.random.default_rng(int(t * 100)).standard_normal(m)
    s += _lp(nz, 0.2) * np.exp(-tt * 7) * 0.25
    out[i0:i0 + m] += s * gain


def sfx_stamp(t, out):
    m = int(0.6 * SR); i0 = int(t * SR)
    if i0 + m >= len(out): return
    tt = np.arange(m) / SR
    s = np.sin(2 * np.pi * (45 + 80 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 7) * 0.6
    nz = np.random.default_rng(7).standard_normal(m)
    s += _lp(nz, 0.35) * np.exp(-tt * 30) * 0.5
    out[i0:i0 + m] += s


def sfx_whoosh(t, out, dur=1.2, up=True):
    m = int(dur * SR); i0 = int(t * SR)
    if i0 < 0 or i0 + m >= len(out): return
    tt = np.arange(m) / SR
    nz = np.random.default_rng(11).standard_normal(m)
    from scipy.signal import lfilter
    y = np.zeros(m)
    # sweep a resonant-ish lowpass by chunk
    step = 512
    for k in range(0, m, step):
        x = k / m
        c = 0.02 + 0.5 * (x if up else 1 - x) ** 2
        y[k:k + step] = lfilter([c], [1, c - 1], nz[k:k + step])
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    out[i0:i0 + m] += y * env * 0.5


def sfx_riser(t, out, dur=3.0):
    m = int(dur * SR); i0 = int(t * SR)
    if i0 < 0 or i0 + m >= len(out): return
    tt = np.arange(m) / SR
    f = 110 * 2 ** (tt / dur * 2)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.05 * (tt / dur) ** 2
    out[i0:i0 + m] += s
    sfx_whoosh(t, out, dur, True)


def sfx_ding(t, out, f=880, gain=0.12):
    m = int(1.5 * SR); i0 = int(t * SR)
    if i0 + m >= len(out): return
    tt = np.arange(m) / SR
    s = sum(w * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * 2.5 * r) for r, w in ((1, 1), (2.01, .35), (3.9, .15)))
    out[i0:i0 + m] += s * gain


def sfx_impact(t, out):
    m = int(2.0 * SR); i0 = int(t * SR)
    if i0 + m >= len(out): return
    tt = np.arange(m) / SR
    s = np.sin(2 * np.pi * (38 + 40 * np.exp(-tt * 8)) * tt) * np.exp(-tt * 2.2) * 0.7
    nz = np.random.default_rng(5).standard_normal(m)
    s += _lp(nz, 0.1) * np.exp(-tt * 4) * 0.4
    out[i0:i0 + m] += s
