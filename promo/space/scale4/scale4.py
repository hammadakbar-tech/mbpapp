"""Scale of the Universe, Part 4 (9:16): one continuous zoom IN, you -> one cell -> DNA -> an atom -> the nucleus -> a proton -> quarks.
The world is laid out in metres with every zoom target at the origin, so float64 keeps its precision 20 orders of magnitude down.
Same markers as Part 3: level titles, the 'Screen:' ruler, word-synced stat chips and a pink pin on where we dive next.
Usage: python3 scale4.py <out.mp4> [--preview t1,t2,...]
"""
import math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import vs
import space_choice as SC
from vs import ptext, rrect, tw, fit, face
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

def emoji(cr, e, *a, **k): vs.emoji(cr, e.replace('️', ''), *a, **k)

W, H, FPS = 1080, 1920, 30
CY = 860
SC.VOICE, SC.RATE = 'en-US-AvaNeural', '+4%'
WHITE, GOLD, CYAN, PINK, VIOLET = hexc('#FFFFFF'), hexc('#FFD60A'), hexc('#3DE0FF'), hexc('#FF4FA3'), hexc('#9B6BFF')
BIG = '1,000,000,000,000,000×'

BEATS = [
    ('hook', "This is you. Now we're going to zoom in... a million billion times, to the smallest things we know."),
    ('you', "Your body is built from about thirty trillion cells. Let's dive into just one."),
    ('cell', "A typical cell is about ten micrometres wide, far too small to see. But inside its nucleus, two metres of DNA are packed into a space just six micrometres across."),
    ('dna', "Zoom in. The DNA strand is only two nanometres wide, and it spells out your genetic code in about three billion letters."),
    ('atom', "Zoom in again. DNA is made of atoms, each roughly a ten-billionth of a metre across... and almost entirely empty space."),
    ('stadium', "If an atom were as big as a stadium, its nucleus would be like a grain of rice in the middle."),
    ('proton', "Dive into that nucleus, and you'll find protons, about a million billion times smaller than you."),
    ('quarks', "And inside every proton are three quarks, held together by the strongest force in nature."),
    ('end', "And smaller than that... no one knows."),
    ('cta', "So, which blew your mind more: zooming out, or zooming in? Tell me in the comments, and follow for Part 5."),
]

# ---------- the world, in metres (y down); every zoom target sits at the origin ----------
rng = np.random.default_rng(4)

# you: a standing figure pointing right; the pad of the index fingertip is the origin
FD = np.array([1.0, -0.06]); FD /= np.linalg.norm(FD)
PALM = np.array([0.72, -0.565]); FEND = PALM + FD * 0.085
TIP = FEND - FD * 0.006
def B(x, y): return np.array([x, y]) - TIP
LIMBS = [([B(0, -0.64), B(0, -0.5)], 0.09),
         ([B(-0.09, 0.0), B(-0.115, 0.45), B(-0.13, 0.86)], 0.14),
         ([B(0.09, 0.0), B(0.115, 0.45), B(0.13, 0.86)], 0.14),
         ([B(-0.2, -0.47), B(-0.27, -0.2), B(-0.3, 0.06)], 0.085),
         ([B(0.2, -0.47), B(0.45, -0.52), B(0.68, -0.56)], 0.08),
         ([PALM - TIP, FEND - TIP], 0.018)]
TORSO = [B(-0.2, -0.52), B(0.2, -0.52), B(0.15, 0.05), B(-0.15, 0.05)]
HEAD, HEAD_R = B(0, -0.75), 0.105
PALM_W, PALM_R = PALM - TIP, 0.045
HUMAN_C = B(0.24, 0.1)

# skin tissue around the fingertip, and the one cell we dive into
TC, RC = np.array([2.2e-6, -1.6e-6]), 7.0e-6
NC, RN = np.array([1.0e-6, -0.6e-6]), 3.0e-6
TIS_SP = 13e-6
_gx = np.arange(-1.0e-3, 1.0e-3, TIS_SP)
_G = np.stack(np.meshgrid(_gx, _gx), -1).reshape(-1, 2)
_G[:, 0] += (np.arange(len(_G)) // len(_gx) % 2) * TIS_SP / 2
_G += rng.normal(0, 1.6e-6, _G.shape)
_G = _G[np.linalg.norm(_G - TC, axis=1) > 13.5e-6]
TIS_P, TIS_R, TIS_G = _G, rng.uniform(5.0e-6, 6.4e-6, len(_G)), rng.integers(0, 4, len(_G))
TIS_PAL = [(1.0, 0.42, 0.62), (0.95, 0.35, 0.78), (0.78, 0.42, 0.98), (1.0, 0.58, 0.48)]

def organelles():
    g = np.random.default_rng(12); mito, ves = [], []
    while len(mito) < 9:
        a = g.uniform(0, 2 * math.pi); p = TC + g.uniform(4.2e-6, 5.9e-6) * np.array([math.cos(a), math.sin(a)])
        if np.linalg.norm(p - NC) > RN + 0.9e-6 and all(np.linalg.norm(p - q[0]) > 1.7e-6 for q in mito):
            mito.append((p, a + math.pi / 2 + g.normal(0, 0.4), g.uniform(1.3e-6, 1.9e-6)))
    while len(ves) < 34:
        a = g.uniform(0, 2 * math.pi); p = TC + g.uniform(0, 6.4e-6) * np.array([math.cos(a), math.sin(a)])
        if np.linalg.norm(p - NC) > RN + 0.3e-6: ves.append((p, g.uniform(0.12e-6, 0.3e-6), int(g.integers(3))))
    er = [(RN + g.uniform(0.35e-6, 1.3e-6), g.uniform(0, 2 * math.pi), g.uniform(0.8, 1.8), g.uniform(0, 6)) for _ in range(7)]
    return mito, ves, er
MITO, VES, ER = organelles()
_gd = (TC - NC) / np.linalg.norm(TC - NC); GOLGI = NC + _gd * (RN + 1.9e-6)

# chromatin: tangled 30 nm fibres filling the nucleus, plus the one fibre that runs through the origin
def chromatin():
    g = np.random.default_rng(11); fibres = []
    for i in range(90):
        p = NC + g.uniform(-0.6, 0.6, 2) * RN; ang = g.uniform(0, 2 * math.pi); pts = [p.copy()]
        for _ in range(70):
            ang += g.normal(0, 0.55); q = p + 0.11e-6 * np.array([math.cos(ang), math.sin(ang)])
            if np.linalg.norm(q - NC) > 0.92 * RN: ang += math.pi * 0.8; continue
            p = q; pts.append(p.copy())
        P = np.array(pts)
        if len(P) < 8: continue
        k = np.ones(5) / 5; P = np.stack([np.convolve(P[:, 0], k, 'valid'), np.convolve(P[:, 1], k, 'valid')], 1)
        if np.linalg.norm(P, axis=1).min() < 0.3e-6: continue  # keep the area around the origin clear
        fibres.append((P, i % 4))
    return fibres
FIBRES = chromatin()
FIB_PAL = [(1.0, 0.45, 0.8), (0.65, 0.5, 1.0), (0.4, 0.75, 1.0), (1.0, 0.6, 0.55)]

SP_D = np.array([math.cos(math.radians(-15)), math.sin(math.radians(-15))]); SP_N = np.array([-SP_D[1], SP_D[0]])
SP_A, SP_L = 0.3e-6, 0.35e-6
def spec(u): return u[:, None] * SP_D + (SP_A * np.sin(u / SP_L))[:, None] * SP_N
_u = np.unique(np.concatenate([np.linspace(-2.6e-6, 2.6e-6, 2600), np.linspace(-60e-9, 60e-9, 600)]))
_S = spec(_u); _in = np.linalg.norm(_S - NC, axis=1) < 0.93 * RN
_i0 = int(np.argmin(np.abs(_u))); _lo, _hi = _i0, _i0
while _lo > 0 and _in[_lo - 1]: _lo -= 1
while _hi < len(_u) - 1 and _in[_hi + 1]: _hi += 1
SPEC_U, SPEC = _u[_lo:_hi + 1], _S[_lo:_hi + 1]
_sp = np.linalg.norm(SP_D + SP_N * SP_A / SP_L)
T_DNA = (SP_D + SP_N * SP_A / SP_L) / _sp; N_DNA = np.array([-T_DNA[1], T_DNA[0]])
BEADS_U = np.array([(k + 0.5) * 50e-9 / _sp for k in range(-60, 60)])
BEADS = spec(BEADS_U[(BEADS_U > SPEC_U[0]) & (BEADS_U < SPEC_U[-1])])

# the DNA double helix along the linker between two nucleosomes
R_DNA, P_DNA = 1.0e-9, 3.4e-9
def helix_pts(x, ph=0.0):
    th = 2 * math.pi * x / P_DNA + ph
    return x[:, None] * T_DNA + (R_DNA * np.sin(th))[:, None] * N_DNA, np.cos(th)
HX = np.arange(-380, 381) * 0.05e-9
H1, Z1 = helix_pts(HX); H2, Z2 = helix_pts(HX, 2.4)
BPX = np.arange(-55, 56) * 0.34e-9
BPS = rng.integers(0, 4, len(BPX))
BASES, COMP = 'ATCG', [1, 0, 3, 2]
BASE_COL = [(0.3, 0.95, 0.5), (1.0, 0.45, 0.35), (0.4, 0.6, 1.0), (1.0, 0.84, 0.3)]

# atoms of the helix (space-filling); the backbone carbon at the origin is the one we dive into
ATOM_COL = {'C': (0.78, 0.82, 0.92), 'O': (1.0, 0.33, 0.35), 'N': (0.38, 0.55, 1.0), 'P': (1.0, 0.62, 0.2), 'H': (0.95, 0.95, 1.0)}
def dna_atoms():
    g = np.random.default_rng(14); P, Z, T, R = [], [], [], []
    ax = np.arange(-253, 254) * 0.075e-9
    for ph in (0.0, 2.4):
        pts, z = helix_pts(ax, ph)
        for i, (p, zz) in enumerate(zip(pts, z)):
            P.append(p); Z.append(zz); R.append(0.07e-9)
            T.append('P' if i % 9 == 4 else ('O' if g.random() < 0.3 else 'C'))
    T[253] = 'C'
    for x in BPX:
        p1, z1 = helix_pts(np.array([x])); p2, z2 = helix_pts(np.array([x]), 2.4)
        for f in (0.14, 0.28, 0.42, 0.58, 0.72, 0.86):
            typ = str(g.choice(['C', 'N', 'C', 'O', 'H']))
            P.append(p1[0] + (p2[0] - p1[0]) * f); Z.append(z1[0] + (z2[0] - z1[0]) * f - 0.05); T.append(typ)
            R.append(0.045e-9 if typ == 'H' else 0.065e-9)
    P, Z, R = np.array(P), np.array(Z), np.array(R)
    order = np.argsort(Z, kind='stable')
    return P[order], Z[order], [T[i] for i in order], R[order], int(np.nonzero(order == 253)[0][0])
ATOMS_P, ATOMS_Z, ATOMS_T, ATOMS_R, ORIGIN_I = dna_atoms()
_sg = np.random.default_rng(15)
SPK_R = _sg.gamma(2.0, 0.035e-9, 900); SPK_A = _sg.uniform(0, 2 * math.pi, 900)
SPK = np.stack([SPK_R * np.cos(SPK_A), SPK_R * np.sin(SPK_A)], 1); SPK_G = _sg.integers(0, 4, 900)

# carbon-12 nucleus: 6 protons + 6 neutrons; the front proton sits at the origin
def nucleus():
    g = np.random.default_rng(21); P = g.normal(0, 1.0, (12, 3))
    for _ in range(500):
        for i in range(12):
            d = P[i] - P; L = np.linalg.norm(d, axis=1); L[i] = 9
            push = np.clip(1.55 - L, 0, None)[:, None] * d / L[:, None]
            P[i] += 0.3 * push.sum(0)
        P -= P.mean(0); P *= 0.985
    tgt = int(np.argmax(P[:, 2] - 0.6 * np.linalg.norm(P[:, :2], axis=1)))
    kinds = np.array([k % 2 for k in range(12)]); others = [i for i in range(12) if i != tgt]
    kinds[tgt] = 0; kinds[others] = [1] * 6 + [0] * 5  # 0 = proton, 1 = neutron
    order = [i for i in np.argsort(P[:, 2]) if i != tgt] + [tgt]
    xy = (P[:, :2] - P[tgt, :2]) * 1e-15
    return xy[order], kinds[order], (P[:, :2].mean(0) - P[tgt, :2]) * 1e-15
NUC_P, NUC_K, NUC_C = nucleus()
RNUC, RP = 0.85e-15, 0.84e-15
QCOL, QLAB = [(1.0, 0.3, 0.35), (0.3, 1.0, 0.5), (0.35, 0.55, 1.0)], ['u', 'u', 'd']
_qg = np.random.default_rng(31)
SEA = [(_qg.uniform(0, 0.62e-15) * np.array([math.cos(a), math.sin(a)]), _qg.uniform(0, 6.28), _qg.uniform(1.2, 2.4), _qg.uniform(0, 3.14))
       for a in _qg.uniform(0, 2 * math.pi, 16)]
QMARKS = [(_qg.uniform(0, 6.28), _qg.uniform(170, 430), _qg.uniform(44, 96), int(_qg.integers(4)), _qg.uniform(0, 6.28)) for _ in range(13)]

# ---------- timeline ----------
TL = None
_missing = set()
def build(voice):
    t, beats, clips = 0.0, [], []
    lead = {'hook': 0.3}; tail = {'hook': 0.45, 'end': 1.0, 'cta': 2.6, 'stadium': 0.6, 'you': 0.55}
    for key, text in BEATS:
        a, words = voice.get(text)
        b = dict(key=key, text=text, start=t, l0=t + lead.get(key, 0.35)); b['l1'] = b['l0'] + len(a) / SR
        b['words'] = [(b['l0'] + s, b['l0'] + e, x) for s, e, x in words]; b['tokens'] = text.split()
        clips.append((b['l0'], a)); t = b['l1'] + tail.get(key, 0.45); b['end'] = t; beats.append(b)
    return dict(beats=beats, by={b['key']: b for b in beats}, clips=clips, dur=t)
def bt(k): return TL['by'][k]
def w(key, word, n=0, end=False):
    q, hits = SC.norm(word), []
    for s, e, x in bt(key)['words']:
        if any(SC.norm(p).startswith(q) for p in x.split()): hits.append((s, e))
    if len(hits) > n: return hits[n][1] if end else hits[n][0]
    if (key, word) not in _missing: _missing.add((key, word)); print(f'  ! no word "{word}" in {key}', file=sys.stderr)
    return bt(key)['l0']
def pop_k(t, t0, d=0.35): return max(1e-3, ease_back(prog(t, t0, t0 + d), 2.6))

def quark_pos(t):
    te = min(t, bt('end')['start']) if TL else t
    out = []
    for i in range(3):
        ang = -math.pi / 2 + i * 2 * math.pi / 3 + te * 0.35
        r = 0.45e-15 * (1 + 0.08 * math.sin(te * 2.1 + i * 2))
        out.append(np.array([r * math.cos(ang), r * math.sin(ang)]))
    return out

# ---------- camera: log zoom keyed to the words ----------
def keys():
    S_H = 520; Q1 = quark_pos(bt('end')['start'])[0]
    return [
        (0.0, S_H, HUMAN_C),
        (w('hook', 'zoom'), S_H, HUMAN_C),
        (bt('hook')['end'], S_H * 1.06, HUMAN_C * 0.97),
        (w('you', 'Your'), S_H * 1.06, HUMAN_C * 0.97),
        (w('you', 'cells', end=True), 1080 / 300e-6, np.array([-20e-6, 45e-6])),
        (w('you', 'dive'), 1080 / 280e-6, np.array([-20e-6, 45e-6])),
        (w('you', 'one', end=True) + 0.25, 1080 / 24e-6, TC + np.array([0, 1.0e-6])),
        (w('cell', 'nucleus'), 1080 / 22e-6, TC + np.array([0, 1.0e-6])),
        (w('cell', 'across', end=True), 1080 / 8.5e-6, NC + np.array([0, 0.4e-6])),
        (w('dna', 'Zoom'), 1080 / 8e-6, NC + np.array([0, 0.4e-6])),
        (w('dna', 'wide', end=True), 1080 / 14e-9, np.array([0, 0.6e-9])),
        (w('dna', 'letters', end=True), 1080 / 9e-9, np.array([0, 0.4e-9])),
        (w('atom', 'Zoom'), 1080 / 9e-9, np.array([0, 0.4e-9])),
        (w('atom', 'atoms', end=True), 1080 / 1.6e-9, np.array([0, 0.1e-9])),
        (w('atom', 'each'), 1080 / 1.6e-9, np.array([0, 0.1e-9])),
        (w('atom', 'across', end=True), 1080 / 0.52e-9, np.zeros(2)),
        (bt('stadium')['end'], 1080 / 0.45e-9, np.zeros(2)),
        (w('proton', 'Dive'), 1080 / 0.45e-9, np.zeros(2)),
        (w('proton', 'protons', end=True), 1080 / 12e-15, NUC_C * 0.7),
        (bt('proton')['end'], 1080 / 10.5e-15, NUC_C * 0.6),
        (w('quarks', 'inside'), 1080 / 10.5e-15, NUC_C * 0.6),
        (w('quarks', 'proton', end=True) + 0.3, 1080 / 2.4e-15, np.zeros(2)),
        (w('end', 'smaller'), 1080 / 2.3e-15, np.zeros(2)),
        (w('end', 'knows', end=True), 1080 / 2.3e-15 * 400, Q1),
        (bt('cta')['end'], 1080 / 2.3e-15 * 520, Q1),
    ]

def camera(t):
    K = TL['keys']
    for (t0, s0, c0), (t1, s1, c1) in zip(K, K[1:]):
        if t <= t1:
            k = ease_io(prog(t, t0, t1))
            s = math.exp(lerp(math.log(s0), math.log(s1), k))
            if s1 > s0 * 1.01:  # zooming in: glide the target point to the centre in screen space
                return s, c1 - (c1 - c0) * s0 * (1 - k) / s
            if s1 < s0 / 1.01:
                return s, c0 - (c0 - c1) * s1 * k / s
            return s, c0 + (c1 - c0) * k
    return K[-1][1], K[-1][2]

def to_screen(p, s, c): return W / 2 + (p[..., 0] - c[0]) * s, CY + (p[..., 1] - c[1]) * s
def L10(s): return math.log10(s)
def band(s, a0, a1, b0=None, b1=None):  # fade in over log10 a0..a1, out over b0..b1
    x = clamp((L10(s) - a0) / (a1 - a0))
    if b0 is not None: x *= 1 - clamp((L10(s) - b0) / (b1 - b0))
    return x

# ---------- drawing ----------
def glow(cr, x, y, r, col, a):
    if a <= 0 or r <= 0: return
    g = cairo.RadialGradient(x, y, 0, x, y, r); g.add_color_stop_rgba(0, *col[:3], a); g.add_color_stop_rgba(1, *col[:3], 0)
    cr.set_source(g); cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.fill()

def sphere(cr, x, y, r, col, a, dark=0.35):
    g = cairo.RadialGradient(x - 0.35 * r, y - 0.4 * r, 0.05 * r, x, y, r)
    g.add_color_stop_rgba(0, min(1, col[0] + 0.4), min(1, col[1] + 0.4), min(1, col[2] + 0.4), a)
    g.add_color_stop_rgba(0.7, *col[:3], a); g.add_color_stop_rgba(1, col[0] * dark, col[1] * dark, col[2] * dark, a)
    cr.set_source(g); cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.fill()

def capsule(cr, x0, y0, x1, y1, r):
    ang = math.atan2(y1 - y0, x1 - x0); cr.new_path()
    cr.arc(x1, y1, r, ang - math.pi / 2, ang + math.pi / 2); cr.arc(x0, y0, r, ang + math.pi / 2, ang + 3 * math.pi / 2); cr.close_path()

BG = [(2.5, (0.03, 0.03, 0.09)), (4.6, (0.08, 0.04, 0.12)), (6.6, (0.10, 0.03, 0.09)), (7.6, (0.02, 0.07, 0.10)),
      (8.6, (0.08, 0.03, 0.14)), (10.3, (0.03, 0.03, 0.12)), (12.2, (0.02, 0.03, 0.09)), (13.6, (0.01, 0.01, 0.035)),
      (16.3, (0.06, 0.01, 0.04)), (18.0, (0.08, 0.01, 0.07)), (21.0, (0.05, 0.0, 0.06))]
def bg_col(s):
    l = L10(s)
    for (a, ca), (b, cb) in zip(BG, BG[1:]):
        if l <= b: k = clamp((l - a) / (b - a)); return tuple(lerp(x, y, k) for x, y in zip(ca, cb))
    return BG[-1][1]

WARP = [(rng.uniform(0, 2 * math.pi), rng.uniform(0, 1), rng.integers(3)) for _ in range(170)]
WARP_COL = [(1, 1, 1), (0.6, 0.9, 1.0), (1.0, 0.7, 0.9)]
def draw_bg(cr, t, s):
    cr.set_source_rgb(*bg_col(s)); cr.paint()
    g = cairo.RadialGradient(540, CY, 0, 540, CY, 1100); g.add_color_stop_rgba(0, 1, 1, 1, 0.04); g.add_color_stop_rgba(1, 0, 0, 0, 0.35)
    cr.set_source(g); cr.paint()
    for th, ph, ci in WARP:  # particles stream outward while the camera zooms in
        u = (L10(s) * 0.9 + ph + t * 0.012) % 1.0; r = 40 * math.exp(u * 3.9)
        x, y = 540 + r * math.cos(th), CY + r * math.sin(th)
        if -5 < x < W + 5 and -5 < y < H + 5:
            cr.new_path(); cr.arc(x, y, 0.8 + 2.4 * u, 0, 2 * math.pi); cr.set_source_rgba(*WARP_COL[ci], 0.45 * math.sin(math.pi * u) ** 1.5); cr.fill()

def draw_human(cr, t, s, c):
    a = 1 - clamp((L10(s) - 6.2) / 0.4)
    if a <= 0: return
    P = lambda p: tuple(float(v) for v in to_screen(np.asarray(p), s, c))
    y0, y1 = P(B(0, -0.86))[1], P(B(0, 0.93))[1]
    grad = cairo.LinearGradient(0, y0, 0, y1)
    grad.add_color_stop_rgba(0, 0.24, 0.88, 1.0, a); grad.add_color_stop_rgba(1, 0.62, 0.42, 1.0, a)
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    for extra, src in ((26, (0.3, 0.8, 1.0, 0.16 * a)), (0, grad)):
        if isinstance(src, tuple): cr.set_source_rgba(*src)
        else: cr.set_source(src)
        for pts, wd in LIMBS:
            cr.new_path(); cr.move_to(*P(pts[0])); [cr.line_to(*P(q)) for q in pts[1:]]
            cr.set_line_width(wd * s + extra); cr.stroke()
        cr.new_path(); cr.move_to(*P(TORSO[0])); [cr.line_to(*P(q)) for q in TORSO[1:]]; cr.close_path()
        cr.set_line_width(0.08 * s + extra); cr.stroke_preserve(); cr.fill()
        hx, hy = P(HEAD); cr.new_path(); cr.arc(hx, hy, HEAD_R * s + extra / 2, 0, 2 * math.pi); cr.fill()
        px, py = P(PALM_W); cr.new_path(); cr.arc(px, py, PALM_R * s + extra / 2, 0, 2 * math.pi); cr.fill()
    cr.set_line_cap(cairo.LINE_CAP_BUTT)
    # fingerprint ridges on the fingertip
    ra = band(s, 4.1, 4.6, 6.0, 6.5) * a
    if ra > 0:
        x0, y0_ = P(PALM_W); x1, y1_ = P(FEND - TIP)
        cr.save(); capsule(cr, x0, y0_, x1, y1_, 0.009 * s); cr.clip()
        cx, cy = P(-FD * 0.002); cr.translate(cx, cy); cr.rotate(math.atan2(FD[1], FD[0]))
        cr.set_line_width(max(1.0, 0.17e-3 * s)); cr.set_source_rgba(1, 1, 1, 0.32 * ra)
        for k in range(1, 46):
            cr.save(); cr.scale(1, 0.72); cr.new_path(); cr.arc(0, 0, k * 0.47e-3 * s, 0, 2 * math.pi); cr.restore(); cr.stroke()
        cr.restore()

def draw_tissue(cr, t, s, c):
    a = clamp((TIS_SP * s - 4) / 14) * (1 - clamp((L10(s) - 8.5) / 0.4))
    if a <= 0: return
    X, Y = to_screen(TIS_P, s, c); R = TIS_R * s
    m = (X > -R) & (X < W + R) & (Y > -R) & (Y < H + R)
    cr.push_group()
    for k, col in enumerate(TIS_PAL):
        mk = m & (TIS_G == k)
        for x, y, r in zip(X[mk], Y[mk], R[mk]): cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi)
        cr.set_source_rgba(*col, 0.5); cr.fill()
    for x, y, r in zip(X[m], Y[m], R[m]): cr.new_sub_path(); cr.arc(x + 0.15 * r, y - 0.1 * r, r * 0.33, 0, 2 * math.pi)
    cr.set_source_rgba(0.42, 0.12, 0.52, 0.8); cr.fill()
    if TIS_SP * s > 30:
        for x, y, r in zip(X[m], Y[m], R[m]): cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi)
        cr.set_source_rgba(1, 0.8, 0.9, 0.35); cr.set_line_width(2); cr.stroke()
    cr.pop_group_to_source()
    ox, oy = to_screen(np.zeros(2), s, c); rr = 0.85e-3 * s
    g = cairo.RadialGradient(ox, oy, rr * 0.65, ox, oy, rr); g.add_color_stop_rgba(0, 1, 1, 1, a); g.add_color_stop_rgba(1, 1, 1, 1, 0)
    cr.mask(g)

def wobble_circle(cr, cx, cy, r, t, k1=5, k2=9, amp=0.03):
    cr.new_path()
    for i in range(121):
        th = 2 * math.pi * i / 120; rr = r * (1 + amp * math.sin(k1 * th + t * 0.6) + amp * 0.7 * math.sin(k2 * th - t * 0.4))
        (cr.move_to if i == 0 else cr.line_to)(cx + rr * math.cos(th), cy + rr * math.sin(th))
    cr.close_path()

def draw_cell(cr, t, s, c):
    a = clamp((RC * s - 4) / 10) * (1 - clamp((L10(s) - 9.2) / 0.3))
    if a <= 0: return
    P = lambda p: tuple(float(v) for v in to_screen(np.asarray(p), s, c))
    cx, cy = P(TC); r = RC * s
    if r < 2.5e6:
        wobble_circle(cr, cx, cy, r, t)
        g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
        g.add_color_stop_rgba(0, 0.12, 0.5, 0.7, 0.55 * a); g.add_color_stop_rgba(1, 0.25, 0.85, 1.0, 0.3 * a)
        cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(0.5, 0.95, 1.0, 0.95 * a); cr.set_line_width(max(2, 0.09e-6 * s)); cr.stroke()
    da = a * clamp((RC * s - 60) / 120)  # organelles once the cell is big enough
    if da > 0:
        for p, ang, ln in MITO:
            x, y = P(p); cr.save(); cr.translate(x, y); cr.rotate(ang)
            L, Wd = ln * s / 2, 0.3e-6 * s
            cr.save(); cr.scale(L, Wd); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
            cr.set_source_rgba(1.0, 0.5, 0.4, 0.85 * da); cr.fill_preserve(); cr.set_source_rgba(1, 0.8, 0.6, da); cr.set_line_width(max(1.5, 0.05e-6 * s)); cr.stroke()
            cr.new_path()
            for i in range(9):
                xx = -L * 0.75 + i * L * 1.5 / 8; cr.line_to(xx, Wd * (0.6 if i % 2 else -0.6))
            cr.set_source_rgba(1, 0.85, 0.7, 0.8 * da); cr.stroke(); cr.restore()
        for p, rv, k in VES:
            x, y = P(p); cr.new_path(); cr.arc(x, y, max(1.5, rv * s), 0, 2 * math.pi)
            cr.set_source_rgba(*[(1.0, 0.84, 0.3), (0.6, 1.0, 0.6), (1.0, 0.6, 0.9)][k], 0.75 * da); cr.fill()
        nx, ny = P(NC)
        cr.set_line_width(max(1.5, 0.07e-6 * s))
        for rr, a0, span, ph in ER:
            cr.new_path()
            for i in range(60):
                th = a0 + span * i / 59; q = rr * (1 + 0.04 * math.sin(th * 14 + ph))
                cr.line_to(nx + q * s * math.cos(th), ny + q * s * math.sin(th))
            cr.set_source_rgba(0.75, 0.55, 1.0, 0.7 * da); cr.stroke()
        gx, gy = P(GOLGI + _gd * 1.5e-6); base = math.atan2(-_gd[1], -_gd[0])
        for k in range(4):
            cr.new_path(); cr.arc(gx, gy, (1.0 + 0.24 * k) * 1e-6 * s, base - 0.5, base + 0.5)
            cr.set_source_rgba(0.5, 0.95, 0.55, 0.8 * da); cr.set_line_width(max(2, 0.12e-6 * s)); cr.stroke()
    # the nucleus
    nx, ny = P(NC); rn = RN * s
    na = a * clamp((rn - 3) / 10)
    if na > 0 and rn < 2.5e6:
        fade = 1 - clamp((L10(s) - 8.9) / 0.3)
        wobble_circle(cr, nx, ny, rn, t + 2, 4, 7, 0.015)
        g = cairo.RadialGradient(nx, ny, 0, nx, ny, rn)
        g.add_color_stop_rgba(0, 0.45, 0.2, 0.8, 0.35 * na * fade); g.add_color_stop_rgba(1, 0.6, 0.3, 0.95, 0.6 * na * fade)
        cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(0.85, 0.7, 1.0, na); cr.set_line_width(max(2, 0.08e-6 * s)); cr.stroke()
        if rn > 80:  # nuclear pores and nucleolus
            for i in range(28):
                th = 2 * math.pi * i / 28; cr.new_path(); cr.arc(nx + rn * math.cos(th), ny + rn * math.sin(th), max(2, 0.06e-6 * s), 0, 2 * math.pi)
                cr.set_source_rgba(1, 0.9, 1, 0.8 * na); cr.fill()
            lx, ly = P(NC + np.array([0.9e-6, 0.9e-6])); glow(cr, lx, ly, 0.8e-6 * s, (0.3, 0.1, 0.45), 0.8 * na * fade)

def draw_chromatin(cr, t, s, c):
    fa = band(s, 7.3, 7.7, 9.0, 9.35)
    if fa > 0:
        wd = max(1.3, 30e-9 * s); cr.set_line_width(wd); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
        for P, k in FIBRES:
            X, Y = to_screen(P, s, c)
            if X.max() < -wd or X.min() > W + wd or Y.max() < -wd or Y.min() > H + wd: continue
            cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:], Y[1:])]
            cr.set_source_rgba(*FIB_PAL[k], 0.6 * fa); cr.stroke()
        X, Y = to_screen(SPEC[::8], s, c)
        cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:], Y[1:])]
        cr.set_source_rgba(1.0, 0.45, 0.75, 0.95 * fa); cr.stroke()
        cr.set_line_cap(cairo.LINE_CAP_BUTT)
    # beads on a string: nucleosomes along the fibre that runs through the origin
    ba = band(s, 8.95, 9.25, 10.6, 10.9)
    if ba > 0:
        la = ba * (1 - band(s, 10.15, 10.45))
        X, Y = to_screen(SPEC, s, c); m = (X > -50) & (X < W + 50) & (Y > -50) & (Y < H + 50)
        if m.any() and la > 0:
            idx = np.nonzero(m)[0]; cr.new_path(); cr.move_to(X[idx[0]], Y[idx[0]])
            for i in idx[1:]: cr.line_to(X[i], Y[i])
            cr.set_source_rgba(0.4, 0.9, 1.0, la); cr.set_line_width(max(2, 2e-9 * s)); cr.stroke()
        X, Y = to_screen(BEADS, s, c); rb = 5.5e-9 * s
        for x, y in zip(X, Y):
            if -rb < x < W + rb and -rb < y < H + rb:
                sphere(cr, x, y, rb, (0.75, 0.5, 1.0), ba)
                cr.new_path(); cr.arc(x, y, rb * 0.92, 0, 2 * math.pi); cr.set_source_rgba(0.4, 0.9, 1.0, 0.9 * ba); cr.set_line_width(max(1.5, 2e-9 * s)); cr.stroke()

def runs(mask):
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None: start = i
        if not v and start is not None: out.append((start, i)); start = None
    if start is not None: out.append((start, len(mask)))
    return out

def draw_helix(cr, t, s, c):
    ha = band(s, 10.15, 10.45, 11.5, 11.8)
    if ha <= 0: return
    wd = max(3, 0.32e-9 * s); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    strands = ((H1, Z1, (0.24, 0.88, 1.0)), (H2, Z2, (1.0, 0.31, 0.64)))
    def strand(front):
        for Hp, Z, col in strands:
            X, Y = to_screen(Hp, s, c)
            for i0, i1 in runs((Z >= 0) == front):
                i1 = min(len(X), i1 + 1)
                cr.new_path(); cr.move_to(X[i0], Y[i0]); [cr.line_to(X[i], Y[i]) for i in range(i0 + 1, i1)]
                cr.set_source_rgba(*(col if front else tuple(v * 0.55 for v in col)), ha * (1 if front else 0.8)); cr.set_line_width(wd); cr.stroke()
    strand(False)
    sp = 0.34e-9 * s
    for x, b in zip(BPX, BPS):
        (p1,), (z1,) = helix_pts(np.array([x])); (p2,), (z2,) = helix_pts(np.array([x]), 2.4)
        X1, Y1 = to_screen(p1, s, c); X2, Y2 = to_screen(p2, s, c)
        if max(X1, X2) < -40 or min(X1, X2) > W + 40 or max(Y1, Y2) < -40 or min(Y1, Y2) > H + 40: continue
        mx, my = (X1 + X2) / 2, (Y1 + Y2) / 2; d = 0.6 + 0.4 * (z1 + z2) / 2
        cr.set_line_width(max(2.5, 0.2e-9 * s))
        for (xa, ya, xb, yb), base in (((X1, Y1, mx, my), b), ((mx, my, X2, Y2), COMP[b])):
            cr.new_path(); cr.move_to(xa, ya); cr.line_to(xb, yb); cr.set_source_rgba(*[v * d for v in BASE_COL[base]], ha); cr.stroke()
        if sp > 24:
            fs = min(46, 0.75 * sp); la = ha * clamp((sp - 24) / 12)
            ptext(cr, BASES[b], lerp(X1, X2, 0.27), lerp(Y1, Y2, 0.27) + fs * 0.35, fs, WHITE, la, sw=max(3, fs / 7))
            ptext(cr, BASES[COMP[b]], lerp(X1, X2, 0.73), lerp(Y1, Y2, 0.73) + fs * 0.35, fs, WHITE, la, sw=max(3, fs / 7))
    strand(True)
    cr.set_line_cap(cairo.LINE_CAP_BUTT)

def draw_atoms(cr, t, s, c):
    ab = band(s, 11.35, 11.65)
    if ab <= 0 or s > 6e13: return
    cl = band(s, 11.95, 12.3)
    X, Y = to_screen(ATOMS_P, s, c); Rp = ATOMS_R * s
    m = (X > -Rp * 1.8) & (X < W + Rp * 1.8) & (Y > -Rp * 1.8) & (Y < H + Rp * 1.8)
    for i in np.nonzero(m)[0]:
        col = ATOM_COL[ATOMS_T[i]]; d = 0.55 + 0.45 * (ATOMS_Z[i] + 1) / 2; col = tuple(v * d for v in col)
        x, y, r = X[i], Y[i], Rp[i]
        if cl < 1: sphere(cr, x, y, r, col, ab * (1 - cl))
        if cl > 0 and i != ORIGIN_I: glow(cr, x, y, r * 1.7, col, 0.2 * cl * ab)

def draw_origin_atom(cr, t, s, c):
    cl = band(s, 11.95, 12.3) * (1 - band(s, 15.6, 16.0))
    if cl <= 0: return
    x, y = to_screen(np.zeros(2), s, c)
    ga = cl * (1 - band(s, 12.45, 13.0))
    if ga > 0:
        glow(cr, x, y, 0.17e-9 * s, (0.35, 0.45, 1.0), 0.7 * ga)
        for i, (col, ph) in enumerate((((1.0, 0.4, 0.8), 0.0), ((0.3, 0.9, 1.0), math.pi / 2))):
            ang = ph + t * 0.15
            for sg in (-1, 1):
                lx, ly = x + sg * 0.075e-9 * s * math.cos(ang), y + sg * 0.075e-9 * s * math.sin(ang)
                cr.save(); cr.translate(lx, ly); cr.rotate(ang); cr.scale(1, 0.55)
                g = cairo.RadialGradient(0, 0, 0, 0, 0, 0.075e-9 * s); g.add_color_stop_rgba(0, *col, 0.6 * ga); g.add_color_stop_rgba(1, *col, 0)
                cr.set_source(g); cr.new_path(); cr.arc(0, 0, 0.075e-9 * s, 0, 2 * math.pi); cr.fill(); cr.restore()
        glow(cr, x, y, 0.05e-9 * s, (0.8, 0.9, 1.0), 0.75 * ga)
    X, Y = to_screen(SPK, s, c)
    m = (X > 0) & (X < W) & (Y > 0) & (Y < H)
    for gi in range(4):
        mk = m & (SPK_G == gi)
        for xx, yy in zip(X[mk], Y[mk]): cr.new_sub_path(); cr.arc(xx, yy, 2.4, 0, 2 * math.pi)
        cr.set_source_rgba(0.85, 0.95, 1.0, cl * (0.25 + 0.6 * math.sin(t * 3 + gi * 1.6) ** 2)); cr.fill()
    na = cl * (1 - band(s, 15.0, 15.3))  # the nucleus: far too small to see, so marked by a dot
    if na > 0: glow(cr, x, y, 12, GOLD, 0.8 * na); cr.new_path(); cr.arc(x, y, 3, 0, 2 * math.pi); cr.set_source_rgba(1, 0.95, 0.7, na); cr.fill()

def draw_nucleus(cr, t, s, c):
    na = band(s, 15.0, 15.3)
    if na <= 0: return
    ez = ease_io(prog(t, w('end', 'smaller'), w('end', 'smaller') + 1.5)) if TL else 0
    rq = RNUC * s; qa = clamp((RP * s - 140) / 220)
    cx, cy = to_screen(NUC_C, s, c)
    if 4.5e-15 * s < 4e6: glow(cr, cx, cy, 4.5e-15 * s, (1.0, 0.75, 0.3), 0.3 * na * (1 - qa * 0.6))
    X, Y = to_screen(NUC_P, s, c)
    for i, (x, y, k) in enumerate(zip(X, Y, NUC_K)):
        last = i == len(X) - 1
        if not (-rq < x < W + rq and -rq < y < H + rq) or rq > 4e6: continue
        col = (1.0, 0.32, 0.45) if k == 0 else (0.42, 0.58, 1.0)
        a = na * ((1 - 0.72 * qa) * (1 - ez) if last else (1 - 0.85 * ez) * (1 - 0.55 * qa))
        sphere(cr, x, y, rq, col, a)
        if rq > 36 and k == 0 and qa < 1: ptext(cr, '+', x, y + rq * 0.22, rq * 0.6, WHITE, 0.85 * a * (1 - qa), sw=max(3, rq / 18))
    if qa > 0:  # inside the proton
        ox, oy = to_screen(np.zeros(2), s, c)
        if RP * s < 4e6: glow(cr, ox, oy, RP * s * 1.05, (1.0, 0.35, 0.5), 0.5 * qa * (1 - ez))
        Q = [to_screen(q, s, c) for q in quark_pos(t)]
        for i, j in ((0, 1), (1, 2), (2, 0)):
            (xa, ya), (xb, yb) = Q[i], Q[j]; dx, dy = xb - xa, yb - ya; L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L; nw = max(4, L / 38)
            cr.new_path()
            for k in range(0, 121):
                u = k / 120; o = 11 * math.sin(2 * math.pi * nw * u - t * 8) * math.sin(math.pi * u) ** 0.3
                cr.line_to(xa + dx * u + nx * o, ya + dy * u + ny * o)
            ga = qa * (1 - 0.5 * ez)
            cr.set_source_rgba(1.0, 0.84, 0.3, 0.3 * ga); cr.set_line_width(14); cr.stroke_preserve()
            cr.set_source_rgba(1.0, 0.9, 0.45, 0.95 * ga); cr.set_line_width(5); cr.stroke()
        for p, ph, om, d in SEA:
            sa = max(0.0, math.sin(t * om + ph)) ** 6 * qa
            if sa < 0.02: continue
            x, y = to_screen(p, s, c); ddx, ddy = 0.05e-15 * s * math.cos(d), 0.05e-15 * s * math.sin(d)
            glow(cr, x - ddx, y - ddy, 10, (0.3, 0.9, 1.0), 0.8 * sa); glow(cr, x + ddx, y + ddy, 10, (1.0, 0.4, 0.9), 0.8 * sa)
        for (x, y), col, lab in zip(Q, QCOL, QLAB):
            r = 44
            glow(cr, x, y, r * 3.2, col, 0.6 * qa); sphere(cr, x, y, r, col, qa)
            ptext(cr, lab, x, y + 16, 52, WHITE, qa, fam='Poppins ExtraBold', sw=6)

def draw_qmarks(cr, t):
    t0 = w('end', 'smaller') + 0.8
    if t < t0: return
    a = ease_out(prog(t, t0, t0 + 1.2))
    for i, (th, r, sz, ci, ph) in enumerate(QMARKS):
        th2 = th + t * 0.08; x, y = 540 + r * math.cos(th2), CY + r * math.sin(th2) * 1.05
        aa = a * (0.45 + 0.4 * math.sin(t * 1.5 + ph))
        cr.save(); cr.translate(x, y); cr.rotate(0.25 * math.sin(t + ph))
        ptext(cr, '?', 0, sz * 0.35, sz, [CYAN, PINK, GOLD, VIOLET][ci], aa, sw=6); cr.restore()

def draw_world(cr, t):
    s, c = camera(t)
    draw_bg(cr, t, s)
    if s < 3e6: draw_human(cr, t, s, c)
    if 2e5 < s < 4e8: draw_tissue(cr, t, s, c)
    if 2e5 < s < 2.5e9: draw_cell(cr, t, s, c)
    if 1.5e7 < s < 1e11: draw_chromatin(cr, t, s, c)
    if 1e10 < s < 1e12: draw_helix(cr, t, s, c)
    draw_atoms(cr, t, s, c)
    if s > 7e11: draw_origin_atom(cr, t, s, c)
    if s > 8e14: draw_nucleus(cr, t, s, c)
    draw_qmarks(cr, t)

def pin_stages():
    return [(0.0, 'ZOOMING IN HERE'), (w('you', 'cells'), 'NEXT: ONE CELL'), (bt('cell')['start'], 'NEXT: DNA'),
            (w('dna', 'strand'), 'NEXT: AN ATOM'), (w('atom', 'atoms'), 'NEXT: THE NUCLEUS'), (w('proton', 'protons'), 'NEXT: A PROTON')]

def draw_pin(cr, t):
    s, c = camera(t); x, y = to_screen(np.zeros(2), s, c)
    a = ease_out(prog(t, w('hook', 'zoom'), w('hook', 'zoom') + 0.4))
    st, ts = bt('stadium'), w('stadium', 'stadium')
    a *= 1 - ease_io(prog(t, ts - 0.3, ts)) * (1 - ease_io(prog(t, st['end'] - 0.1, st['end'] + 0.3)))
    a *= 1 - ease_io(prog(t, w('quarks', 'inside') - 0.2, w('quarks', 'inside') + 0.3))
    if a <= 0.01: return
    label, t0 = TL['pins'][0][1], 0.0
    for tt, lab in TL['pins']:
        if t >= tt: label, t0 = lab, tt
    la = a * (ease_out(prog(t, t0, t0 + 0.35)) if t0 > 0 else 1)
    cr.new_path(); cr.arc(x, y, 9, 0, 2 * math.pi); cr.set_source_rgba(*PINK[:3], a); cr.fill()
    rr = 14 + 18 * ((t * 1.2) % 1.0)
    cr.new_path(); cr.arc(x, y, rr, 0, 2 * math.pi); cr.set_source_rgba(*PINK[:3], a * (1 - (t * 1.2) % 1.0)); cr.set_line_width(3); cr.stroke()
    up = y - 110 > 380
    lx, ly = min(max(x, 200), 880), (y - 110 if up else y + 125)
    cr.new_path(); cr.move_to(x, y + (-12 if up else 12)); cr.line_to(lx, ly + (14 if up else -40))
    cr.set_source_rgba(1, 1, 1, la); cr.set_line_width(3); cr.stroke()
    ptext(cr, label, lx, ly, 36, WHITE, la, fam='Poppins ExtraBold', sw=6)

UNITS = [(1, 'metres'), (1e-2, 'centimetres'), (1e-3, 'millimetres'), (1e-6, 'micrometres'), (1e-9, 'nanometres'),
         (1e-12, 'picometres'), (1e-15, 'femtometres'), (1e-18, 'attometres')]
def fov_text(wm):
    for u, name in UNITS:
        if wm >= u: break
    v = wm / u
    return (f'{v:.3g}' if v < 100 else f'{v:,.0f}') + ' ' + name

TITLES = [('hook', 'you', 'YOU'), ('you', 'one', 'ONE CELL'), ('dna', 'DNA', 'DNA'), ('atom', 'atoms', 'AN ATOM'),
          ('proton', 'nucleus', 'THE NUCLEUS'), ('quarks', 'proton', 'INSIDE A PROTON')]

def draw_markers(cr, t):
    s, c = camera(t)
    cur, t0 = None, 0
    for key, word, txt in TITLES:
        tw0 = w(key, word)
        if t >= tw0: cur, t0 = txt, tw0
    if cur:
        k = prog(t, t0, t0 + 0.3); sc = lerp(1.8, 1.0, ease_out(k))
        cr.save(); cr.translate(540, 210); cr.scale(sc, sc)
        ptext(cr, cur, 0, 0, fit(cr, cur, 84, 1000), WHITE, clamp(k * 3), sw=11); cr.restore()
    # live field-of-view ruler
    a = ease_out(prog(t, 0.4, 0.9))
    txt = 'Screen: ' + fov_text(W / s)
    cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(40); wd_ = cr.text_extents(txt).x_advance
    x0, x1 = 540 - wd_ / 2 - 80, 540 + wd_ / 2 + 80
    rrect(cr, x0, 262, x1 - x0, 64, 32); cr.set_source_rgba(0.05, 0.08, 0.2, 0.75 * a); cr.fill()
    for xa, d in ((x0 + 22, -1), (x1 - 22, 1)):
        cr.new_path(); cr.move_to(xa, 294); cr.line_to(xa - d * 30, 294); cr.set_source_rgba(*CYAN[:3], a); cr.set_line_width(4); cr.stroke()
        cr.new_path(); cr.move_to(xa + d * 2, 294); cr.line_to(xa - d * 12, 284); cr.line_to(xa - d * 12, 304); cr.close_path(); cr.fill()
    ptext(cr, txt, 540, 307, 40, CYAN, a, fam='Poppins ExtraBold', sw=5)
    # hook: the zoom factor and the series tag
    hb, yb = bt('hook'), bt('you')
    tm = w('hook', 'million')
    if tm <= t < yb['start'] + 0.4:
        k = pop_k(t, tm, 0.45); out = 1 - ease_io(prog(t, yb['start'] - 0.1, yb['start'] + 0.4))
        cr.save(); cr.translate(540, 1420); cr.scale(k, k)
        ptext(cr, BIG, 0, 0, fit(cr, BIG, 96, 1000), GOLD, out, sw=11); cr.restore()
    if t < yb['start'] + 0.3:
        ta = 1 - ease_io(prog(t, yb['start'] - 0.2, yb['start'] + 0.3))
        ptext(cr, 'SCALE OF THE UNIVERSE · PART 4', 540, 1530, 40, CYAN, ta * ease_out(prog(t, 0.1, 0.5)), fam='Poppins ExtraBold', sw=6)

CHIPS = {  # beat: (emoji, text, trigger word)
    'you': [('🧫', '~30 TRILLION CELLS', 'thirty')],
    'cell': [('📏', '~10 MICROMETRES WIDE', 'ten'), ('🧬', '2 METRES OF DNA INSIDE', 'two'), ('🎯', 'NUCLEUS: ~6 MICROMETRES', 'six')],
    'dna': [('📏', '2 NANOMETRES WIDE', 'two'), ('🔤', '~3 BILLION LETTERS', 'three')],
    'atom': [('⚛️', '~0.1 NANOMETRES ACROSS', 'ten'), ('💨', '99.9999999999996% EMPTY', 'empty')],
    'stadium': [('🏟️', 'ATOM = A STADIUM', 'stadium'), ('🍚', 'NUCLEUS = A GRAIN OF RICE', 'rice')],
    'proton': [('🔴', 'PROTON: ~1.7 FEMTOMETRES', 'protons'), ('🤯', BIG + ' SMALLER', 'million')],
    'quarks': [('🔺', '3 QUARKS', 'three'), ('💪', 'THE STRONGEST FORCE', 'strongest')],
}

def draw_chips(cr, t):
    for key, chips in CHIPS.items():
        b = bt(key)
        if not (b['start'] <= t < b['end']): continue
        out = 1 - ease_io(prog(t, b['end'] - 0.3, b['end']))
        for i, (e, txt, word) in enumerate(chips):
            t0 = w(key, word)
            if t < t0: continue
            k = pop_k(t, t0); y = 1330 + i * 92
            fs = fit(cr, txt, 44, 840, 'Poppins ExtraBold')
            cr.save(); cr.translate(540, y); cr.scale(k, k)
            wd_ = tw(cr, txt, fs, 'Poppins ExtraBold'); bw = wd_ + 120
            rrect(cr, -bw / 2, -40, bw, 80, 40); cr.set_source_rgba(0.05, 0.06, 0.18, 0.85 * out); cr.fill_preserve()
            cr.set_source_rgba(*CYAN[:3], out); cr.set_line_width(3); cr.stroke()
            emoji(cr, e, -bw / 2 + 45, -2, 50, out)
            ptext(cr, txt, 22, 15 * fs / 44, fs, WHITE, out, fam='Poppins ExtraBold', sw=5)
            cr.restore()

def draw_stadium(cr, t):
    b, ts = bt('stadium'), w('stadium', 'stadium')
    if not (ts <= t < b['end'] + 0.4): return
    a = ease_out(prog(t, ts, ts + 0.5)) * (1 - ease_io(prog(t, b['end'] - 0.1, b['end'] + 0.4)))
    s, c = camera(t); ox, oy = to_screen(np.zeros(2), s, c)
    k = pop_k(t, ts, 0.5); A, Bv = 440, 330
    cr.save(); cr.translate(ox, oy); cr.scale(k, k)
    def ell(f):
        cr.new_path(); cr.save(); cr.scale(A * f, Bv * f); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
    ell(1.0); cr.set_source_rgba(0.1, 0.12, 0.3, 0.85 * a); cr.fill()
    for f in np.linspace(0.8, 0.98, 7): ell(f); cr.set_source_rgba(0.55, 0.65, 1.0, 0.4 * a); cr.set_line_width(2); cr.stroke()
    ell(0.78); cr.set_source_rgba(0.85, 0.35, 0.25, 0.9 * a); cr.fill()
    ell(0.66); cr.set_source_rgba(0.18, 0.58, 0.3, 0.95 * a); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.75 * a); cr.set_line_width(3)
    cr.rectangle(-0.5 * A, -0.38 * Bv, A, 0.76 * Bv); cr.stroke()
    cr.move_to(0, -0.38 * Bv); cr.line_to(0, 0.38 * Bv); cr.stroke()
    cr.new_path(); cr.arc(0, 0, 0.12 * A, 0, 2 * math.pi); cr.stroke()
    tr = w('stadium', 'rice')
    ra = a * ease_out(prog(t, tr, tr + 0.4))
    glow(cr, 0, 0, 22, GOLD, 0.9 * ra)
    cr.save(); cr.rotate(0.4); cr.scale(1, 0.45); cr.new_path(); cr.arc(0, 0, 6, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgba(1, 0.97, 0.85, ra); cr.fill()
    ptext(cr, 'NUCLEUS', 0, -76, 34, GOLD, ra, fam='Poppins ExtraBold', sw=6)
    ptext(cr, '(this dot is still too big!)', 0, 98, 28, WHITE, ra * ease_out(prog(t, tr + 0.6, tr + 1.0)), fam='Poppins ExtraBold', sw=5)
    cr.restore()

def pill(cr, x, y, txt, e, col, k, size=50):
    cr.save(); cr.translate(x, y); cr.scale(k, k)
    wd_ = tw(cr, txt, size); bw = wd_ + 130
    rrect(cr, -bw / 2, -50, bw, 96, 48); cr.set_source_rgba(*col[:3], 1); cr.fill()
    ptext(cr, txt, 30, 18, size, WHITE, 1, sw=6); emoji(cr, e, -bw / 2 + 50, -2, 56, 1); cr.restore()

def draw_end(cr, t):
    b, c = bt('end'), bt('cta')
    if t < b['start']: return
    out = 1 - ease_io(prog(t, c['start'], c['start'] + 0.4))
    tsm, tk = w('end', 'smaller'), w('end', 'knows')
    if t >= tsm and out > 0:
        k = pop_k(t, tsm); cr.save(); cr.translate(540, 1420); cr.scale(k, k); ptext(cr, 'AND SMALLER THAN THAT...', 0, 0, 62, WHITE, out, sw=8); cr.restore()
        if t >= tk:
            k = pop_k(t, tk); cr.save(); cr.translate(540, 1540); cr.scale(k, k); ptext(cr, 'NO ONE KNOWS', 0, 0, 92, GOLD, out, sw=11); cr.restore()
    tq = w('cta', 'which')
    if t >= tq:
        k = pop_k(t, tq) * (1 + 0.03 * math.sin(t * 5))
        cr.save(); cr.translate(540, 1345); cr.scale(k, k)
        ptext(cr, 'WHICH BLEW YOUR MIND?', 0, 0, fit(cr, 'WHICH BLEW YOUR MIND?', 76, 860), WHITE, 1, sw=9); cr.restore()
    for word, x, txt, e, col in (('out', 290, 'ZOOM OUT', '🌌', CYAN), ('in', 790, 'ZOOM IN', '🔬', VIOLET)):
        tp = w('cta', word)
        if t >= tp: pill(cr, x, 1480, txt, e, col, pop_k(t, tp) * (1 + 0.03 * math.sin(t * 6 + x)), 46)
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1720); cr.scale(k, k)
        txt = 'FOLLOW FOR PART 5'; wd_ = tw(cr, txt, 54)
        rrect(cr, -wd_ / 2 - 90, -62, wd_ + 180, 96, 48); cr.set_source_rgba(*PINK[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 54, WHITE, 1, sw=6); emoji(cr, '🔔', -wd_ / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def draw_captions(cr, t):
    for b in TL['beats']:
        if b['key'] == 'cta' and t >= w('cta', 'which'): return
        if b['key'] == 'end' and t >= w('end', 'smaller'): return
        if not (b['l0'] - 0.05 <= t < b['l1'] + 0.3): continue
        words, src, toks = b['words'], list(b['tokens']), []
        for _, _, x in words:
            n = len(x.split()); toks.append(' '.join(src[:n])); src = src[n:]
        if src or len(toks) != len(words): toks = [x for _, _, x in words]
        groups, cur = [], []
        for tok, (s_, e, _) in zip(toks, words):
            cur.append((s_, e, tok))
            if len(cur) == 3 or re.search(r"[.,!?:;…]$", tok): groups.append(cur); cur = []
        if cur: groups.append(cur)
        g = None
        for i, gr in enumerate(groups):
            nxt = groups[i + 1][0][0] if i + 1 < len(groups) else b['l1'] + 0.3
            if gr[0][0] - 0.05 <= t < nxt: g = gr; break
        if g is None: return
        ups = [x[2].upper() for x in g]
        size = 66; face(cr, size); space = cr.text_extents(' ').x_advance
        ci = max([j for j, x in enumerate(g) if x[0] <= t + 0.02] or [0])
        widths = [cr.text_extents(u).x_advance * (1.12 if j == ci else 1.0) for j, u in enumerate(ups)]
        total = sum(widths) + space * (len(ups) - 1); sc = min(1.0, 980 / total)
        cr.save(); cr.translate(540, 1690); cr.scale(sc, sc); x = -total / 2
        for j, (u, wd_) in enumerate(zip(ups, widths)):
            cr.save(); cr.translate(x + wd_ / 2, 0)
            if j == ci: k = ease_back(prog(t, g[j][0], g[j][0] + 0.15), 3); cr.scale(1 + 0.12 * k, 1 + 0.12 * k)
            ptext(cr, u, 0, 0, size, CYAN if j == ci else WHITE, 1.0 if j <= ci else 0.6, sw=10)
            cr.restore(); x += wd_ + space
        cr.restore(); return

def render_frame(cr, t):
    draw_world(cr, t)
    draw_stadium(cr, t)
    draw_pin(cr, t)
    draw_markers(cr, t)
    draw_chips(cr, t)
    draw_end(cr, t)
    draw_captions(cr, t)
    f = prog(t, TL['dur'] - 0.4, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- score ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    g = np.random.default_rng(2)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n)
    chords = [[52, 59, 64, 67], [48, 55, 60, 64], [43, 50, 55, 62], [50, 57, 62, 66]]  # Em C G D
    for ci in range(int(dur / 4.8) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(6.0 * SR)) / SR
        env = np.minimum(1, L_ / 1.5) * np.exp(-L_ * 0.3)
        put(music, ci * 4.8, sum(0.03 * (np.sin(2 * np.pi * note(m) * L_) + 0.6 * np.sin(2 * np.pi * note(m) * 1.003 * L_ + 1)) for m in ch) * env)
        put(music, ci * 4.8, 0.09 * np.sin(2 * np.pi * note(ch[0] - 12) * L_) * env)
        for j in range(8):  # quicker sparkle arpeggio for the micro world
            pt = np.arange(int(1.0 * SR)) / SR; m = ch[(j * 3) % 4] + (24 if j % 2 else 12)
            put(music, ci * 4.8 + j * 0.6, 0.022 * np.sin(2 * np.pi * note(m) * pt) * np.exp(-pt * 4))
    rev = np.zeros(n)
    for d, gg in ((0.29, 0.3), (0.47, 0.2)): k = int(d * SR); rev[k:] += gg * music[:-k]
    music = np.tanh((music + rev) * 1.3) * 0.55
    fx = np.zeros(n)
    def riser(t0, t1, amp=0.25):
        L_ = int((t1 - t0) * SR)
        if L_ <= 0: return
        nz = g.standard_normal(L_); win = np.linspace(0, 1, L_) ** 2
        k = 40; sm = np.convolve(nz, np.ones(k) / k, 'same')
        put(fx, t0, amp * (sm * (1 - win) + (nz - sm) * win * 0.4) * np.sin(np.pi * np.linspace(0, 1, L_)) ** 0.5)
    def boom(t0, amp=0.6):
        L_ = np.arange(int(2.2 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-L_ * 8)) / SR) * np.exp(-L_ * 2))
    def chime(t0, amp=0.08):
        L_ = np.arange(int(1.0 * SR)) / SR; put(fx, t0, amp * sum(np.sin(2 * np.pi * f * L_) * np.exp(-L_ * d) for f, d in ((1568, 4), (2349, 5))))
    for k0, k1, d in (('you', 'Your', 2.8), ('you', 'dive', 1.6), ('cell', 'nucleus', 2.0), ('dna', 'Zoom', 2.6), ('atom', 'Zoom', 2.0),
                      ('atom', 'each', 2.0), ('proton', 'Dive', 2.4), ('quarks', 'inside', 1.8), ('end', 'smaller', 2.6)):
        t0 = w(k0, k1); riser(t0, t0 + d)
    for key, word, _ in TITLES: boom(w(key, word), 0.55)
    for key, chips in CHIPS.items():
        for _, _, word in chips: chime(w(key, word))
    boom(w('hook', 'million'), 0.6); boom(w('end', 'knows'), 0.7)
    v = np.zeros(n)
    for s_, a in T['clips']: put(v, s_, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.5 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx + v
    mix *= np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 1.5)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(cache):
    global TL
    TL = build(SC.WordVoice(cache)); TL['keys'] = keys(); TL['pins'] = pin_stages()

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    out = sys.argv[1]
    setup(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_scale'))
    print(f"duration {TL['dur']:.1f}s")
    for b in TL['beats']: print(f"  {b['key']:10s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 2 and sys.argv[2] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[3].split(','):
            render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]
    make_audio(TL, base + '.wav')
    nfr = int(TL['dur'] * FPS); workers = os.cpu_count() or 4
    bounds = np.linspace(0, nfr, workers * 2 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
