"""Scale of the Universe, Part 3 (9:16): one continuous zoom-out, Milky Way -> Local Group -> Laniakea -> observable universe.
World is laid out in light-years; the camera zooms logarithmically. Text markers (level title, field-of-view counter,
stat chips, YOU ARE HERE) fire on the narrator's spoken words (edge-tts word boundaries).
Usage: python3 scale3.py <out.mp4> [--preview t1,t2,...]
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
WHITE, GOLD, CYAN, PINK, INK = hexc('#FFFFFF'), hexc('#FFD60A'), hexc('#3DE0FF'), hexc('#FF4FA3'), (0.03, 0.02, 0.08)

BEATS = [
    ('hook', "This is the Milky Way. Everything you have ever known... is inside it."),
    ('mw', "It's about a hundred thousand light-years across, with up to four hundred billion stars. Our Sun needs two hundred and thirty million years to circle it just once."),
    ('lg', "Now, zoom out. The Milky Way is just one of more than eighty galaxies in our Local Group, about ten million light-years wide."),
    ('andromeda', "Our biggest neighbour, Andromeda, is two and a half million light-years away... and it's heading our way."),
    ('lan', "Zoom out again. Our Local Group is a tiny speck in Laniakea, a supercluster of about a hundred thousand galaxies, over five hundred million light-years across."),
    ('name', "In Hawaiian, Laniakea means... immeasurable heaven."),
    ('obs', "And Laniakea is just one strand in the cosmic web. The observable universe is ninety-three billion light-years across, with hundreds of billions of galaxies."),
    ('end', "And beyond that edge... no one knows."),
    ('cta', "So... how small do you feel right now? Tell me in the comments, and follow for Part 4."),
]

# ---------- the universe, in light-years ----------
rng = np.random.default_rng(3)
M31 = np.array([2.5e6 * math.cos(math.radians(35)), -2.5e6 * math.sin(math.radians(35))])
M33 = M31 + np.array([0.55e6, 0.5e6])
GA = np.array([-1.6e8, 1.3e8])  # toward the Great Attractor (Laniakea's centre), schematic

def spiral(n, rmax, arms=4, seed=0):
    g = np.random.default_rng(seed); pts, cols = [], []
    for i in range(n):
        if g.random() < 0.22:  # bulge / bar
            x, y = g.normal(0, rmax * 0.09), g.normal(0, rmax * 0.05)
            c = (1.0, 0.85, 0.6)
        else:
            k = g.integers(arms); major = k % 2 == 0
            th = g.uniform(0, 3 * math.pi) ** 1.0
            b = math.log(1 / 0.12) / (3 * math.pi)
            r = rmax * 0.12 * math.exp(b * th)
            spread = 0.07 if major else 0.12
            if g.random() < 0.18: r = g.uniform(0.1, 1.0) * rmax; spread = 3.0  # thin disc between the arms
            ang = th + k * 2 * math.pi / arms + g.normal(0, spread)
            r *= 1 + g.normal(0, 0.05)
            x, y = r * math.cos(ang), r * math.sin(ang)
            c = (0.75, 0.85, 1.0) if g.random() > 0.08 else (1.0, 0.55, 0.75)
        pts.append((x, y)); cols.append(c)
    return np.array(pts), np.array(cols)

MW_P, MW_C = spiral(14000, 5.2e4, seed=1)
SUN = np.array([2.6e4 * math.cos(2.1), 2.6e4 * math.sin(2.1)])
AND_P, AND_C = spiral(5000, 1.1e5, seed=2)
TRI_P, TRI_C = spiral(1200, 3.0e4, arms=2, seed=4)
DWARFS = np.concatenate([rng.normal(0, 4e5, (28, 2)), M31 + rng.normal(0, 5e5, (30, 2)), rng.uniform(-4.5e6, 4.5e6, (22, 2)) + M31 * 0.4])
DWARFS = np.concatenate([DWARFS, [[1.6e5 * math.cos(4.0), 1.6e5 * math.sin(4.0)], [2.0e5 * math.cos(4.3), 2.0e5 * math.sin(4.3)]]])

def laniakea():
    g = np.random.default_rng(5); pts, lines = [], []
    for k in range(46):  # flow lines converging on the Great Attractor
        a = 2 * math.pi * k / 46 + g.normal(0, 0.06)
        r0 = 2.6e8 * (1 + 0.28 * math.sin(3 * a) + 0.12 * math.cos(5 * a + 1))
        p = GA + r0 * np.array([math.cos(a), math.sin(a)]); line = [p.copy()]
        for s in range(40):
            d = GA - p; dist = np.linalg.norm(d)
            if dist < 1.2e7: break
            d /= dist; perp = np.array([-d[1], d[0]])
            p = p + d * dist * 0.06 + perp * dist * 0.025 * math.sin(s * 0.4 + k)
            line.append(p.copy())
        lines.append(np.array(line))
        for q in line:
            for _ in range(5): pts.append(q + g.normal(0, 6e6, 2))
    for _ in range(1600): pts.append(GA + g.normal(0, 2.5e7, 2))
    pts = np.array(pts); pts = pts[np.linalg.norm(pts, axis=1) > 8e6]
    ang = np.linspace(0, 2 * math.pi, 120)
    edge = np.array([GA + 2.6e8 * (1 + 0.28 * math.sin(3 * a) + 0.12 * math.cos(5 * a + 1)) * 1.08 * np.array([math.cos(a), math.sin(a)]) for a in ang])
    return pts, lines, edge
LAN_P, LAN_LINES, LAN_EDGE = laniakea()

def cosmic_web():
    g = np.random.default_rng(9); R = 4.65e10
    nodes = []
    while len(nodes) < 230:
        p = g.uniform(-R, R, 2)
        if np.linalg.norm(p) < R * 0.98: nodes.append(p)
    nodes = np.array(nodes); pts, segs = [], []
    for i, p in enumerate(nodes):
        d = np.linalg.norm(nodes - p, axis=1); nb = np.argsort(d)[1:4]
        for j in nb:
            if j < i and i in np.argsort(np.linalg.norm(nodes - nodes[j], axis=1))[1:4]: continue
            q = nodes[j]; segs.append((p, q))
            for u in g.uniform(0, 1, 60): pts.append(p + (q - p) * u + g.normal(0, 3.5e8, 2))
        for _ in range(25): pts.append(p + g.normal(0, 6e8, 2))
    pts = np.array(pts); pts = pts[(np.linalg.norm(pts, axis=1) < R) & (np.linalg.norm(pts, axis=1) > 6e8)]
    return pts, segs, R
WEB_P, WEB_SEGS, R_OBS = cosmic_web()

# colour groups, so the large layers stay colourful but still draw in one fill per colour
WEB_PAL = [(0.62, 0.42, 1.0), (0.35, 0.55, 1.0), (0.24, 0.88, 1.0), (1.0, 0.35, 0.75), (1.0, 0.84, 0.4)]
_f = np.sin(WEB_P[:, 0] / 1.3e10 + 1.0) + np.cos(WEB_P[:, 1] / 1.1e10 - 0.5) + 0.6 * np.sin((WEB_P[:, 0] + WEB_P[:, 1]) / 0.7e10)
WEB_G = np.clip(((_f + 2.6) / 5.2 * 4).astype(int), 0, 3)
WEB_G[np.random.default_rng(5).random(len(WEB_P)) < 0.08] = 4
LAN_PAL = [(1.0, 0.8, 0.4), (1.0, 0.45, 0.7), (0.62, 0.42, 1.0), (0.35, 0.6, 1.0)]
_d = np.linalg.norm(LAN_P - GA, axis=1)
LAN_G = np.clip((_d / np.percentile(_d, 99) * 4).astype(int), 0, 3)

# ---------- timeline ----------
TL = None
_missing = set()
def build(voice):
    t, beats, clips = 0.0, [], []
    lead = {'hook': 0.3}; tail = {'hook': 0.4, 'end': 1.0, 'cta': 2.6, 'name': 0.8}
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

# ---------- camera: log zoom keyed to the words ----------
def keys():
    S0 = 470 / 5.2e4
    return [
        (0.0, S0 * 0.93, np.zeros(2)),
        (w('mw', 'Sun'), S0 * 1.02, np.zeros(2)),
        (w('lg', 'zoom'), S0 * 1.02, np.zeros(2)),
        (w('lg', 'Group', end=True), 470 / 5.2e6, M31 * 0.42),
        (w('andromeda', 'Andromeda'), 470 / 5.2e6, M31 * 0.42),
        (w('andromeda', 'away', end=True), 470 / 2.4e6, M31 * 0.5),
        (w('lan', 'Zoom'), 470 / 2.6e6, M31 * 0.5),
        (w('lan', 'Laniakea', end=True), 470 / 3.1e8, GA * 0.5),
        (w('name', 'immeasurable'), 470 / 3.4e8, GA * 0.5),
        (w('obs', 'just'), 470 / 3.5e8, GA * 0.5),
        (w('obs', 'web', end=True), 470 / 5.0e10, np.zeros(2)),
        (bt('cta')['end'], 470 / 6.5e10, np.zeros(2)),
    ]

def camera(t):
    K = TL['keys']
    for (t0, s0, c0), (t1, s1, c1) in zip(K, K[1:]):
        if t <= t1:
            k = ease_io(prog(t, t0, t1))
            s = math.exp(lerp(math.log(s0), math.log(s1), k))
            kc = k ** 3 if s1 < s0 else 1 - (1 - k) ** 3  # move the centre late when zooming out
            return s, c0 + (c1 - c0) * kc
    return K[-1][1], K[-1][2]

def to_screen(p, s, c): return W / 2 + (p[..., 0] - c[0]) * s, CY + (p[..., 1] - c[1]) * s

def vis(radius_ly, s, lo=6, hi=None):
    px = radius_ly * s
    a = clamp((px - lo) / (lo * 4))
    if hi: a *= clamp((hi - px) / (hi * 0.5))
    return a

# ---------- drawing ----------
STARS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.5, 1.8), rng.uniform(0, 6.28)) for _ in range(220)]

def dots(cr, X, Y, cols, size, a, cull=True):
    if a <= 0.01: return
    m = (X > -10) & (X < W + 10) & (Y > -10) & (Y < H + 10) if cull else np.ones(len(X), bool)
    if not m.any(): return
    X, Y = X[m], Y[m]
    if cols is None:
        cr.set_source_rgba(1, 1, 1, a)
        for x, y in zip(X, Y): cr.rectangle(x - size / 2, y - size / 2, size, size)
        cr.fill(); return
    cols = cols[m]
    for x, y, c in zip(X, Y, cols):
        cr.rectangle(x - size / 2, y - size / 2, size, size); cr.set_source_rgba(c[0], c[1], c[2], a); cr.fill()

def dots_grp(cr, X, Y, grp, pal, size, a):
    if a <= 0.01: return
    m = (X > -10) & (X < W + 10) & (Y > -10) & (Y < H + 10)
    for k, col in enumerate(pal):
        mk = m & (grp == k)
        if not mk.any(): continue
        for x, y in zip(X[mk], Y[mk]): cr.rectangle(x - size / 2, y - size / 2, size, size)
        cr.set_source_rgba(*col, a); cr.fill()

def glow(cr, x, y, r, col, a):
    if a <= 0 or r <= 0: return
    g = cairo.RadialGradient(x, y, 0, x, y, r); g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    cr.set_source(g); cr.arc(x, y, r, 0, 2 * math.pi); cr.fill()

def rot(P, ang):
    c, s_ = math.cos(ang), math.sin(ang)
    return np.stack([P[:, 0] * c - P[:, 1] * s_, P[:, 0] * s_ + P[:, 1] * c], axis=1)

def draw_universe(cr, t):
    s, c = camera(t)
    cr.set_source_rgb(0.01, 0.01, 0.03); cr.paint()
    for x, y, r, ph in STARS:
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25 + 0.3 * math.sin(t + ph) ** 2); cr.fill()
    cr.save(); cr.set_operator(cairo.OPERATOR_ADD)
    # cosmic web
    aw = vis(R_OBS, s, lo=60)
    if aw > 0:
        X, Y = to_screen(WEB_P, s, c); dots_grp(cr, X, Y, WEB_G, WEB_PAL, 2.4, 0.55 * aw)
        cx, cy = to_screen(np.zeros(2), s, c); r = R_OBS * s
        g = cairo.RadialGradient(cx, cy, r * 0.96, cx, cy, r * 1.04)
        g.add_color_stop_rgba(0, 0.9, 0.5, 0.3, 0); g.add_color_stop_rgba(0.5, 0.9, 0.5, 0.3, 0.55 * aw); g.add_color_stop_rgba(1, 0.9, 0.5, 0.3, 0)
        cr.set_source(g); cr.arc(cx, cy, r * 1.05, 0, 2 * math.pi); cr.fill()
    # Laniakea
    al = vis(2.6e8, s, lo=40, hi=None) * (1 - 0.6 * aw)
    if al > 0:
        X, Y = to_screen(LAN_P, s, c); dots_grp(cr, X, Y, LAN_G, LAN_PAL, 2.6, 0.85 * al)
        tn = w('name', 'Laniakea') if TL else 0
        flow = ease_out(prog(t, tn, tn + 1.0)) * (1 - prog(t, bt('obs')['start'], bt('obs')['start'] + 1.5))
        cr.set_line_width(2)
        for i, line in enumerate(LAN_LINES):
            X, Y = to_screen(line, s, c)
            cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:], Y[1:])]
            cr.set_source_rgba(0.4, 0.75, 1.0, (0.12 + 0.3 * flow) * al); cr.stroke()
            if flow > 0:
                u = (t * 0.25 + i * 0.13) % 1.0; j = int(u * (len(line) - 1))
                glow(cr, X[j], Y[j], 9, (0.6, 0.9, 1.0), 0.8 * flow * al)
        gx, gy = to_screen(GA, s, c); glow(cr, gx, gy, 2.6e8 * s * 0.35, (0.8, 0.7, 1.0), 0.35 * al)
        X, Y = to_screen(LAN_EDGE, s, c)
        cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:], Y[1:])]; cr.close_path()
        cr.set_dash([10, 10]); cr.set_source_rgba(1, 0.85, 0.5, 0.5 * al); cr.set_line_width(2.5); cr.stroke(); cr.set_dash([])
    # Local Group
    ag = vis(5e6, s, lo=40)
    if ag > 0:
        X, Y = to_screen(DWARFS, s, c)
        for x, y in zip(X, Y): glow(cr, x, y, 7, (0.9, 0.9, 1.0), 0.55 * ag)
        for P, Cc, ctr, ang, sq in ((AND_P, AND_C, M31, 0.6, 0.38), (TRI_P, TRI_C, M33, 1.2, 0.7)):
            pr = rot(P, ang + t * 0.01); pr[:, 1] *= sq; pr = rot(pr, -0.5) + ctr
            X, Y = to_screen(pr, s, c); dots(cr, X, Y, Cc, 2.0, 0.5 * ag)
            gx, gy = to_screen(ctr, s, c); size = 1.1e5 if P is AND_P else 3e4
            glow(cr, gx, gy, max(30 if P is AND_P else 18, size * s * 0.6), (1, 0.85, 0.6), 0.65 * ag)
        bc = M31 * 0.42; bx, by = to_screen(bc, s, c)
        cr.new_path(); cr.arc(bx, by, 5.2e6 * s, 0, 2 * math.pi); cr.set_dash([10, 10]); cr.set_source_rgba(0.6, 0.85, 1, 0.45 * ag * (1 - al * 0.8))
        cr.set_line_width(2.5); cr.stroke(); cr.set_dash([])
    cr.restore()
    if ag > 0.05 and al < 0.5:  # names at Local Group scale
        la = ag * (1 - al * 2)
        for name, pos, dy in (('MILKY WAY', np.zeros(2), 70), ('ANDROMEDA', M31, -70), ('TRIANGULUM', M33, 60)):
            if name == 'ANDROMEDA' and bt('andromeda')['start'] <= t < bt('andromeda')['end']: continue
            x, y = to_screen(pos, s, c)
            ptext(cr, name, x, y + dy, 30, (0.85, 0.9, 1.0), la * (0 if (5.2e4 * s > 120) else 1), fam='Poppins ExtraBold', sw=5)
    cr.save(); cr.set_operator(cairo.OPERATOR_ADD)
    # Milky Way
    pr = rot(MW_P, t * 0.03)
    X, Y = to_screen(pr, s, c)
    mw_px = 5.2e4 * s
    if mw_px > 3:
        dots(cr, X, Y, MW_C, max(1.4, min(2.4, mw_px / 180)), 0.42)
    ox, oy = to_screen(np.zeros(2), s, c)
    glow(cr, ox, oy, max(16, mw_px * 0.32), (1, 0.85, 0.6), 0.75)
    glow(cr, ox, oy, max(26, mw_px * 0.9), (0.55, 0.65, 1.0), 0.18)
    cr.restore()

def you_are_here(cr, t):
    s, c = camera(t)
    sun = rot(SUN[None, :], t * 0.03)[0]
    k = clamp((math.log10(s) - math.log10(1.5e-4)) / 1.0)  # sun position when zoomed in, our galaxy otherwise
    p = sun * k
    x, y = to_screen(p, s, c)
    a = ease_out(prog(t, w('hook', 'you'), w('hook', 'you') + 0.4))
    if a <= 0: return
    cr.new_path(); cr.arc(x, y, 9, 0, 2 * math.pi); cr.set_source_rgba(*PINK[:3], a); cr.fill()
    rr = 14 + 18 * ((t * 1.2) % 1.0)
    cr.new_path(); cr.arc(x, y, rr, 0, 2 * math.pi); cr.set_source_rgba(*PINK[:3], a * (1 - (t * 1.2) % 1.0)); cr.set_line_width(3); cr.stroke()
    lx, ly = x + 70, y - 90
    cr.new_path(); cr.move_to(x + 8, y - 8); cr.line_to(lx - 8, ly + 18); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(3); cr.stroke()
    ptext(cr, 'YOU ARE HERE', lx, ly, 36, WHITE, a, anchor='l', sw=6)

def fov_text(width_ly):
    if width_ly < 1e6: return f'{width_ly:,.0f} light-years'
    if width_ly < 1e9: return f'{width_ly / 1e6:,.0f} million light-years'
    return f'{width_ly / 1e9:,.1f} billion light-years'

TITLES = [('hook', 'Milky', 'THE MILKY WAY'), ('lg', 'Local', 'THE LOCAL GROUP'), ('lan', 'Laniakea', 'LANIAKEA'), ('obs', 'observable', 'THE OBSERVABLE UNIVERSE')]

def draw_markers(cr, t):
    s, c = camera(t)
    # level title, switched on the spoken word
    cur, t0 = None, 0
    for key, word, txt in TITLES:
        tw0 = w(key, word)
        if t >= tw0: cur, t0 = txt, tw0
    if cur:
        k = prog(t, t0, t0 + 0.3); sc = lerp(1.8, 1.0, ease_out(k))
        cr.save(); cr.translate(540, 210); cr.scale(sc, sc)
        ptext(cr, cur, 0, 0, fit(cr, cur, 84, 1000), WHITE, clamp(k * 3), sw=11); cr.restore()
    # live field-of-view counter
    a = ease_out(prog(t, 0.4, 0.9))
    txt = 'Screen: ' + fov_text(W / s)
    face(cr, 40); cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(40); wd_ = cr.text_extents(txt).x_advance
    x0, x1 = 540 - wd_ / 2 - 80, 540 + wd_ / 2 + 80
    rrect(cr, x0, 262, x1 - x0, 64, 32); cr.set_source_rgba(0.05, 0.08, 0.2, 0.75 * a); cr.fill()
    for xa, d in ((x0 + 22, -1), (x1 - 22, 1)):  # drawn double arrow ends
        cr.new_path(); cr.move_to(xa, 294); cr.line_to(xa - d * 30, 294); cr.set_source_rgba(*CYAN[:3], a); cr.set_line_width(4); cr.stroke()
        cr.new_path(); cr.move_to(xa + d * 2, 294); cr.line_to(xa - d * 12, 284); cr.line_to(xa - d * 12, 304); cr.close_path(); cr.fill()
    ptext(cr, txt, 540, 307, 40, CYAN, a, fam='Poppins ExtraBold', sw=5)
    # part tag during the hook
    if t < bt('mw')['start'] + 0.3:
        ta = 1 - ease_io(prog(t, bt('mw')['start'] - 0.2, bt('mw')['start'] + 0.3))
        ptext(cr, 'SCALE OF THE UNIVERSE · PART 3', 540, 1520, 40, GOLD, ta * ease_out(prog(t, 0.1, 0.5)), fam='Poppins ExtraBold', sw=6)

CHIPS = {  # beat: (emoji, text, trigger word)
    'mw': [('📏', '100,000 LIGHT-YEARS ACROSS', 'hundred'), ('✨', 'UP TO 400 BILLION STARS', 'four'), ('☀️', '1 LAP = 230 MILLION YEARS', 'thirty')],
    'lg': [('🌌', '80+ GALAXIES', 'eighty'), ('📏', '~10 MILLION LIGHT-YEARS', 'ten')],
    'andromeda': [('🌀', 'ANDROMEDA: 2.5 MILLION LY', 'two'), ('💥', 'APPROACHING AT ~110 KM/S', 'heading')],
    'lan': [('🌌', '~100,000 GALAXIES', 'hundred'), ('📏', '500+ MILLION LIGHT-YEARS', 'five')],
    'name': [('🌺', '"IMMEASURABLE HEAVEN"', 'immeasurable')],
    'obs': [('🕸️', 'THE COSMIC WEB', 'cosmic'), ('📏', '93 BILLION LIGHT-YEARS', 'ninety'), ('🌌', 'HUNDREDS OF BILLIONS OF GALAXIES', 'hundreds')],
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
            cr.save(); cr.translate(540, y); cr.scale(k, k)
            wd_ = tw(cr, txt, 44, 'Poppins ExtraBold'); bw = wd_ + 120
            rrect(cr, -bw / 2, -40, bw, 80, 40); cr.set_source_rgba(0.05, 0.06, 0.18, 0.85 * out); cr.fill_preserve()
            cr.set_source_rgba(*CYAN[:3], out); cr.set_line_width(3); cr.stroke()
            emoji(cr, e, -bw / 2 + 45, -2, 50, out)
            ptext(cr, txt, 22, 15, 44, WHITE, out, fam='Poppins ExtraBold', sw=5)
            cr.restore()
    # Andromeda: distance line and approach arrow
    b = bt('andromeda')
    if b['start'] <= t < b['end'] + 0.3:
        s, c = camera(t); out = 1 - ease_io(prog(t, b['end'] - 0.3, b['end'] + 0.3))
        x0, y0 = to_screen(np.zeros(2), s, c); x1, y1 = to_screen(M31, s, c)
        ta = w('andromeda', 'Andromeda'); k = ease_io(prog(t, ta, ta + 0.8))
        if k > 0:
            cr.new_path(); cr.move_to(x0, y0); cr.line_to(lerp(x0, x1, k), lerp(y0, y1, k)); cr.set_dash([12, 10])
            cr.set_source_rgba(*GOLD[:3], out); cr.set_line_width(3); cr.stroke(); cr.set_dash([])
            ptext(cr, 'ANDROMEDA', x1, y1 - 110, 44, GOLD, out * ease_out(prog(t, ta, ta + 0.3)), sw=6)
        th = w('andromeda', 'heading')
        if t >= th:
            u = ((t - th) * 0.6) % 1.0
            ax, ay = lerp(x1, x0, 0.25 + 0.3 * u), lerp(y1, y0, 0.25 + 0.3 * u)
            ang = math.atan2(y0 - y1, x0 - x1)
            cr.save(); cr.translate(ax, ay); cr.rotate(ang)
            cr.move_to(28, 0); cr.line_to(-14, 18); cr.line_to(-14, -18); cr.close_path(); cr.set_source_rgba(1, 0.4, 0.4, out); cr.fill(); cr.restore()

def draw_end(cr, t):
    b, c = bt('end'), bt('cta')
    if t < b['start']: return
    tk = w('end', 'knows')
    if t >= w('end', 'beyond'):
        k = pop_k(t, w('end', 'beyond')); out = 1 - ease_io(prog(t, c['start'], c['start'] + 0.4))
        cr.save(); cr.translate(540, 1420); cr.scale(k, k); ptext(cr, 'AND BEYOND THAT EDGE...', 0, 0, 62, WHITE, out, sw=8); cr.restore()
        if t >= tk:
            k = pop_k(t, tk); cr.save(); cr.translate(540, 1540); cr.scale(k, k); ptext(cr, 'NO ONE KNOWS', 0, 0, 92, GOLD, out, sw=11); cr.restore()
    tq = w('cta', 'small')
    if t >= tq:
        k = pop_k(t, tq) * (1 + 0.03 * math.sin(t * 5))
        cr.save(); cr.translate(540, 1400); cr.scale(k, k)
        ptext(cr, 'HOW SMALL DO YOU FEEL?', 0, 0, 72, WHITE, 1, sw=9); ptext(cr, '1 – 10 👇'.replace(' 👇', ''), 0, 110, 96, GOLD, 1, sw=11)
        cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1720); cr.scale(k, k)
        txt = 'FOLLOW FOR PART 4'; wd_ = tw(cr, txt, 54)
        rrect(cr, -wd_ / 2 - 90, -62, wd_ + 180, 96, 48); cr.set_source_rgba(*PINK[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 54, WHITE, 1, sw=6); emoji(cr, '🔔', -wd_ / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def draw_captions(cr, t):
    for b in TL['beats']:
        if b['key'] == 'cta' and t >= w('cta', 'small'): return
        if b['key'] == 'end' and t >= w('end', 'beyond'): return
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
    draw_universe(cr, t)
    you_are_here(cr, t)
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
    chords = [[50, 57, 62, 64], [46, 53, 58, 62], [43, 50, 55, 59], [45, 52, 57, 61]]  # Dsus2 Bb G A
    for ci in range(int(dur / 4.8) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(6.0 * SR)) / SR
        env = np.minimum(1, L_ / 1.5) * np.exp(-L_ * 0.3)
        put(music, ci * 4.8, sum(0.03 * (np.sin(2 * np.pi * note(m) * L_) + 0.6 * np.sin(2 * np.pi * note(m) * 1.003 * L_ + 1)) for m in ch) * env)
        put(music, ci * 4.8, 0.09 * np.sin(2 * np.pi * note(ch[0] - 12) * L_) * env)
        for j in range(4):
            pt = np.arange(int(1.6 * SR)) / SR; m = ch[(j * 3) % 4] + 12
            put(music, ci * 4.8 + j * 1.2, 0.03 * np.sin(2 * np.pi * note(m) * pt) * np.exp(-pt * 3))
    rev = np.zeros(n)
    for d, gg in ((0.29, 0.3), (0.47, 0.2)): k = int(d * SR); rev[k:] += gg * music[:-k]
    music = np.tanh((music + rev) * 1.3) * 0.55
    fx = np.zeros(n)
    def riser(t0, t1, amp=0.25):  # rising filtered noise during each zoom-out
        L_ = int((t1 - t0) * SR)
        if L_ <= 0: return
        nz = g.standard_normal(L_); win = np.linspace(0, 1, L_) ** 2
        k = 40; sm = np.convolve(nz, np.ones(k) / k, 'same')
        put(fx, t0, amp * (sm * (1 - win) + (nz - sm) * win * 0.4) * np.sin(np.pi * np.linspace(0, 1, L_)) ** 0.5)
    def boom(t0, amp=0.6):
        L_ = np.arange(int(2.2 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-L_ * 8)) / SR) * np.exp(-L_ * 2))
    def chime(t0, amp=0.08):
        L_ = np.arange(int(1.0 * SR)) / SR; put(fx, t0, amp * sum(np.sin(2 * np.pi * f * L_) * np.exp(-L_ * d) for f, d in ((1568, 4), (2349, 5))))
    for k0, k1 in (('lg', 'zoom'), ('lan', 'Zoom'), ('obs', 'just')):
        t0 = w(k0, k1); riser(t0, t0 + 2.8)
    for key, word, _ in TITLES: boom(w(key, word), 0.55)
    for key, chips in CHIPS.items():
        for _, _, word in chips: chime(w(key, word))
    boom(w('end', 'knows'), 0.7)
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
    TL = build(SC.WordVoice(cache)); TL['keys'] = keys()

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
