"""'Africa Is WAY Bigger Than You Think' (9:16): Mercator hook, then true-size countries dropped into Africa on a globe.
Renders frames in parallel worker processes.
Usage: python3 africa.py <data_dir> <voices_dir> <out.mp4> [--preview t1,t2,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import quiz, canada as cn
from quiz import font, tw, text, fit_font, rrect, pill, clamp, lerp, prog, ease_io, ease_out, ease_back, merc, hexc, Voice, SR
from canada import vec, rot_between, slerp, View, rings, path_rings, draw_bg, chunks, GX, GY

W, H, FPS = 1080, 1920, 30
quiz.SPEED = 1.05
OCEAN0, OCEAN1 = hexc('#16365E'), hexc('#0B1D3A')
LAND, LAND_EDGE = hexc('#2C4A6E'), hexc('#4E74A0')
SAND, WHITE, GOLD, ICE, RED = hexc('#E9B949'), hexc('#FFFFFF'), hexc('#FFC845'), hexc('#CFE6FF'), hexc('#EF3340')
AFRICA_C, AFRICA_KM2 = (19.0, 3.0), 30.37

# piece key -> NE names, home centre, spot inside Africa, colour, km² (millions), label
PIECES = {
    'greenland': (['Greenland'], (-41, 72), (19, 3), ICE, 2.166, 'GREENLAND'),
    'usa': (['United States of America'], (-98, 39), (4, 19), hexc('#4E79FF'), 9.83, 'USA'),
    'china': (['China'], (103, 35), (31, 17), hexc('#FF4D4D'), 9.60, 'CHINA'),
    'india': (['India'], (79, 22), (24, -5), hexc('#FF9F1C'), 3.29, 'INDIA'),
    'eu': (cn.EU, (14, 50), (25, -24), hexc('#9B7BFF'), 4.23, 'EU'),
    'japan': (['Japan'], (138, 37), (44, 4), hexc('#FF5FA2'), 0.378, 'JAPAN'),
    'uk': (['United Kingdom'], (-2, 54), (-8, 7), hexc('#2EC4B6'), 0.244, 'UK'),
    'mexico': (['Mexico'], (-102, 24), (9, 0), hexc('#9BE564'), 1.96, 'MEXICO'),
}
FILL_ORDER = ['usa', 'china', 'india', 'eu', 'japan', 'uk', 'mexico']

BEATS = [  # key, lines, header, stat
    ('hook', ["On most maps, Greenland looks just as big as Africa.",
              "But that's a lie... and it's hiding something huge."], 'GREENLAND = AFRICA?', None),
    ('greenland', ["Drop Greenland onto Africa, and it's tiny.", "Africa is actually fourteen times bigger!"],
     'THE REAL SIZE', ('14×', 'Africa vs Greenland')),
    ('setup', ["So how big is Africa, really? Let's fill it up."], "LET'S FILL IT UP", None),
    ('usa', ["The entire United States covers only about a third."], '+ USA', None),
    ('china', ["Now add all of China."], '+ CHINA', None),
    ('india', ["Then squeeze in India."], '+ INDIA', None),
    ('eu', ["Now, the whole European Union."], '+ THE WHOLE EU', None),
    ('japan', ["Japan, and the United Kingdom too."], '+ JAPAN + UK', None),
    ('mexico', ["And there's still room left over... for all of Mexico!"], '+ MEXICO', None),
    ('total', ["Some of the biggest countries on Earth... all inside one continent."],
     'ALL INSIDE AFRICA', ('29.5M < 30.4M', 'km²: all of them vs Africa')),
    ('why', ["Why do maps lie? Most use the Mercator projection, drawn in fifteen sixty-nine for sailors.",
             "It stretches lands near the poles... and shrinks everything near the equator. Like Africa."],
     'WHY MAPS LIE', None),
    ('people', ["Africa has fifty-four countries, and about one and a half billion people.",
                "By twenty fifty, one in four humans will be African."],
     'THE FUTURE IS AFRICAN', ('1 in 4', 'humans will be African by 2050')),
    ('outro', ["So next time you see a map, remember... Africa is way bigger than it looks.",
               "Which country should we shrink next? Tell me in the comments!"], None, None),
]
GAP, LEAD, TAIL = 0.25, 0.35, 0.45

# ---------- data ----------
class Geo:
    def __init__(self, data_dir):
        lo = json.load(open(os.path.join(data_dir, 'countries_110m.geojson')))
        hi = json.load(open(os.path.join(data_dir, 'countries_50m.geojson')))
        self.world_ll = [r for f in lo['features'] for r in rings(f['geometry'])]
        self.world = cn.Geo.pack(self.world_ll)
        by = {}
        africa = []
        for f in hi['features']:
            rs = [r for r in rings(f['geometry']) if len(r) >= 6]
            by.setdefault(f['properties']['NAME'], []).extend(rs)
            if f['properties']['CONTINENT'] == 'Africa': africa.extend(rs)
        self.africa_ll = africa
        self.africa = cn.Geo.pack(africa)
        self.pieces = {}
        for key, (names, home, *_rest) in PIECES.items():
            rs = [r for n in names for r in by[n]]
            if key == 'usa':   # contiguous states only, so the shape reads at a glance
                rs = [r for r in rs if -130 < r[:, 0].mean() < -60 and r[:, 1].mean() < 50]
            if key == 'eu':    # drop overseas territories
                rs = [r for r in rs if -25 < r[:, 0].mean() < 45 and 33 < r[:, 1].mean() < 72]
            self.pieces[key] = cn.Geo.pack(rs)
        self.greenland_ll = by['Greenland']

GEO = None
TL = None

def build(voice):
    t, beats, clips = 0.15, [], []
    for key, lines, head, stat in BEATS:
        b = dict(key=key, head=head, stat=stat, start=t, lines=[])
        cur = t + LEAD
        for i, s in enumerate(lines):
            a = voice.get(s); cur += GAP if i else 0
            clips.append((cur, a)); b['lines'].append((cur, cur + len(a) / SR, s)); cur += len(a) / SR
        t = cur + (TAIL if key != 'outro' else 1.8)
        if key in FILL_ORDER + ['japan']: t = max(t, b['start'] + 2.9)  # let each piece land before the next
        b['end'] = t; beats.append(b)
    return dict(beats=beats, clips=clips, dur=t, by={b['key']: b for b in beats})

def beat_at(T, t):
    for b in T['beats']:
        if b['start'] <= t < b['end']: return b
    return T['beats'][-1]

# ---------- drawing ----------
def piece_pos(key, k):
    """Where a piece's centre is at drop progress k (0 = just over the horizon, 1 = in place)."""
    _, home, spot, *_ = PIECES[key]
    tgt = vec(*spot); h = vec(*home); c = vec(*AFRICA_C)
    ang = math.acos(clamp(float(np.dot(c, h)), -1, 1))
    start = slerp(c, h, min(1.0, math.radians(75) / max(ang, 1e-6)))  # 75° out from Africa, towards home
    return slerp(start, tgt, ease_out(k)), vec(*home)

def draw_piece(cr, v, key, k, alpha, label_a):
    P, offs = GEO.pieces[key]
    pos, home = piece_pos(key, k)
    M = rot_between(home, pos)
    xs, ys, d = v.project(P @ M.T)
    col = PIECES[key][3]
    cr.new_path(); path_rings(cr, xs, ys, offs)
    cr.set_source_rgba(*col[:3], 0.25 * alpha); cr.set_line_width(12); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
    cr.set_source_rgba(*col[:3], 0.82 * alpha); cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, 0.9 * alpha); cr.set_line_width(1.8); cr.stroke()
    if label_a > 0:
        cx, cy, _ = v.project(pos[None, :])
        font(cr, 30); text(cr, PIECES[key][5], cx[0], cy[0] + 10, WHITE, label_a * alpha, sp=1, shadow=True)

def globe(cr, T, t, alpha, R=760, center=AFRICA_C, spin=0.0):
    c = vec(center[0] + spin, center[1])
    v = View(c, R)
    g = cairo.RadialGradient(GX, GY, R * 0.9, GX, GY, R * 1.12)
    g.add_color_stop_rgba(0, 0.35, 0.6, 1, 0.35 * alpha); g.add_color_stop_rgba(1, 0.35, 0.6, 1, 0)
    cr.set_source(g); cr.arc(GX, GY, R * 1.12, 0, 2 * math.pi); cr.fill()
    g = cairo.RadialGradient(GX - R * 0.3, GY - R * 0.35, R * 0.1, GX, GY, R)
    g.add_color_stop_rgba(0, *OCEAN0[:3], alpha); g.add_color_stop_rgba(1, *OCEAN1[:3], alpha)
    cr.new_path(); cr.arc(GX, GY, R, 0, 2 * math.pi); cr.set_source(g); cr.fill_preserve()
    cr.save(); cr.clip()
    P, offs = GEO.world; xs, ys, d = v.project(P)
    cr.new_path(); path_rings(cr, xs, ys, offs)
    cr.set_source_rgba(*LAND[:3], alpha); cr.fill_preserve()
    cr.set_source_rgba(*LAND_EDGE[:3], 0.8 * alpha); cr.set_line_width(1.2); cr.stroke()
    # Africa itself
    P, offs = GEO.africa; xs, ys, d = v.project(P)
    cr.new_path(); path_rings(cr, xs, ys, offs)
    cr.set_source_rgba(*SAND[:3], 0.55 * alpha); cr.fill_preserve()
    cr.set_source_rgba(*SAND[:3], 0.45 * alpha); cr.set_line_width(1); cr.stroke()
    return v

def draw_globe_scene(cr, T, t, alpha):
    by = T['by']; b = beat_at(T, t)
    spin = 0.0; R = 760
    if b['key'] == 'outro':
        spin = (t - b['start']) * 3; R = 760 - 280 * ease_io(prog(t, b['start'], b['start'] + 1.5))
    v = globe(cr, T, t, alpha, R=R, spin=spin)
    # Greenland drop
    gb = by['greenland']
    gk = prog(t, gb['start'] + 0.2, gb['start'] + 1.5)
    ga = 1 - ease_io(prog(t, gb['end'] - 0.3, gb['end']))
    if gk > 0 and ga > 0: draw_piece(cr, v, 'greenland', gk, alpha * ga, ease_out(prog(t, gb['start'] + 1.4, gb['start'] + 1.8)))
    # filling pieces
    fade = 1 - 0.65 * ease_io(prog(t, by['why']['start'], by['why']['start'] + 0.5)) if t < by['outro']['start'] else 0.9
    for key in FILL_ORDER:
        fb = by[key if key != 'uk' else 'japan']
        t0 = fb['lines'][0][0] + (0.0 if key != 'uk' else (fb['lines'][0][1] - fb['lines'][0][0]) * 0.45)
        k = prog(t, t0, t0 + 1.1)
        if k <= 0: continue
        lab = ease_out(prog(t, t0 + 1.0, t0 + 1.3)) * (1 if t < by['why']['start'] else 0)
        draw_piece(cr, v, key, k, alpha * fade, lab)
        if 0.95 < k and t < t0 + 1.5:  # landing ring
            pos, _ = piece_pos(key, 1); x, y, _ = v.project(pos[None, :]); r = prog(t, t0 + 1.0, t0 + 1.5)
            cr.new_path(); cr.arc(x[0], y[0], 20 + 120 * ease_out(r), 0, 2 * math.pi)
            cr.set_source_rgba(1, 1, 1, (1 - r) * alpha); cr.set_line_width(4); cr.stroke()
    # people dots
    pb = by['people']
    if pb['start'] <= t < pb['end'] + 0.3:
        a = ease_out(prog(t, pb['start'], pb['start'] + 0.4)) * (1 - ease_io(prog(t, pb['end'] - 0.3, pb['end'] + 0.2)))
        rng = np.random.default_rng(9)
        l0, l1 = pb['lines'][0][:2]
        P, offs = GEO.africa
        pts = P[rng.integers(0, len(P), 420)]
        jitter = rng.normal(0, 0.03, pts.shape); pts = pts + jitter; pts /= np.linalg.norm(pts, axis=1)[:, None]
        xs, ys, d = v.project(pts)
        for i, (x, y) in enumerate(zip(xs, ys)):
            k = ease_back(prog(t, l0 + i / len(xs) * (l1 - l0), l0 + 0.3 + i / len(xs) * (l1 - l0)))
            if k > 0.01:
                cr.new_path(); cr.arc(x, y, 5 * k, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.85 * a); cr.fill()
    cr.restore()

def draw_mercator(cr, T, t, alpha, labels=False):
    if alpha <= 0: return
    lon0, my0, z = -18.0, float(merc(np.array(38.0))), 4.0
    def pr(r): return GX + (r[:, 0] - lon0) * z, GY - (merc(r[:, 1]) - my0) * z
    cr.save()
    rrect(cr, 30, 430, 1020, 800, 40); cr.set_source_rgba(*OCEAN1[:3], 0.95 * alpha); cr.fill_preserve(); cr.clip()
    def fill(rs, col, a):
        cr.new_path()
        for r in rs:
            xs, ys = pr(r); cr.move_to(xs[0], ys[0]); [cr.line_to(x, y) for x, y in zip(xs[1:], ys[1:])]; cr.close_path()
        cr.set_source_rgba(*col[:3], a); cr.fill()
    fill(GEO.world_ll, LAND, alpha)
    hb = T['by']['hook']
    t0 = hb['start'] if not labels else T['by']['why']['start']
    fill(GEO.greenland_ll, ICE, 0.9 * alpha * ease_out(prog(t, t0 + 0.6, t0 + 1.0)))
    fill(GEO.africa_ll, SAND, 0.9 * alpha * ease_out(prog(t, t0 + 1.6, t0 + 2.0)))
    if labels:  # stretch / shrink annotations
        wb = T['by']['why']; l1 = wb['lines'][1][0]
        for txt, lon, lat, col, tt in (('STRETCHED', -41, 74, RED, l1 + 0.5), ('SHRUNK', 19, 4, GOLD, l1 + 2.8)):
            k = ease_back(prog(t, tt, tt + 0.4))
            if k > 0.01:
                x, y = pr(np.array([[lon, lat]]))
                cr.save(); cr.translate(x[0], y[0]); cr.scale(k, k)
                pill(cr, txt, 0, 0, 40, col, WHITE if col is RED else hexc('#0B1630'), alpha)
                cr.restore()
    cr.restore()
    font(cr, 30); text(cr, 'A NORMAL WORLD MAP (MERCATOR)', 540, 1275, ICE, alpha * 0.9, sp=3)
    if not labels:
        l1 = hb['lines'][1][0]
        k = prog(t, l1 + 0.6, l1 + 0.9)
        if k > 0:
            shake = 10 * math.sin(t * 70) * (1 - prog(t, l1 + 0.9, l1 + 1.2))
            cr.save(); cr.translate(540 + shake, 830); cr.rotate(-0.12); s = lerp(2.2, 1, ease_out(k)); cr.scale(s, s)
            font(cr, 110); w = tw(cr, 'MAP LIES', 8)
            cr.set_source_rgba(*RED[:3], alpha * k); cr.set_line_width(10)
            rrect(cr, -w / 2 - 40, -110, w + 80, 150, 20); cr.stroke()
            text(cr, 'MAP LIES', 0, 0, RED, alpha * k, sp=8)
            cr.restore()

def draw_fillbar(cr, T, t):
    by = T['by']
    a = ease_out(prog(t, by['usa']['start'] - 0.3, by['usa']['start'] + 0.2)) * (1 - ease_io(prog(t, by['total']['end'] - 0.3, by['total']['end'])))
    if a <= 0: return
    x0, y0, w, h = 90, 1290, 900, 46
    font(cr, 30); text(cr, 'AFRICA  30.4M km²', x0, y0 - 18, SAND, a, sp=2, anchor='l')
    total = 0.0
    for key in FILL_ORDER:
        fb = by[key if key != 'uk' else 'japan']
        t0 = fb['lines'][0][0] + (0.0 if key != 'uk' else (fb['lines'][0][1] - fb['lines'][0][0]) * 0.45) + 0.9
        total += PIECES[key][4] * ease_out(prog(t, t0, t0 + 0.6))
    rrect(cr, x0, y0, w, h, h / 2); cr.set_source_rgba(1, 1, 1, 0.12 * a); cr.fill()
    cr.save(); rrect(cr, x0, y0, w, h, h / 2); cr.clip()
    xx = x0; shown = 0.0
    for key in FILL_ORDER:
        fb = by[key if key != 'uk' else 'japan']
        t0 = fb['lines'][0][0] + (0.0 if key != 'uk' else (fb['lines'][0][1] - fb['lines'][0][0]) * 0.45) + 0.9
        part = PIECES[key][4] * ease_out(prog(t, t0, t0 + 0.6))
        ww = w * part / AFRICA_KM2
        cr.rectangle(xx, y0, ww, h); cr.set_source_rgba(*PIECES[key][3][:3], a); cr.fill(); xx += ww
    cr.restore()
    pct = 100 * total / AFRICA_KM2
    font(cr, 44); text(cr, f'{pct:.0f}% FULL', x0 + w, y0 - 14, WHITE, a, anchor='r')
    font(cr, 28, bold=False); text(cr, f'{total:.1f}M km² so far', x0 + w, y0 + h + 40, ICE, a, anchor='r')

def draw_header(cr, b, t):
    if not b['head']: return
    a = ease_out(prog(t, b['start'], b['start'] + 0.4)) * (1 - ease_io(prog(t, b['end'] - 0.25, b['end'])))
    k = ease_back(prog(t, b['start'], b['start'] + 0.45))
    cr.save(); cr.translate(540, 250); cr.scale(k, k)
    fit_font(cr, b['head'], 72, 980, 3); text(cr, b['head'], 0, 25, WHITE, a, sp=3, shadow=True)
    cr.restore()
    cr.set_source_rgba(*SAND[:3], a); w = 160 * ease_out(prog(t, b['start'] + 0.2, b['start'] + 0.7))
    cr.rectangle(540 - w, 300, 2 * w, 8); cr.fill()

def stat_time(b):
    return b['lines'][-1][0] + 0.4

def draw_stat(cr, b, t):
    if not b['stat']: return
    t0 = stat_time(b)
    a = ease_out(prog(t, t0, t0 + 0.35)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    big, small = b['stat']; k = ease_back(prog(t, t0, t0 + 0.45))
    cr.save(); cr.translate(540, 1345); cr.scale(k, k)
    rrect(cr, -440, -110, 880, 210, 36); cr.set_source_rgba(0.02, 0.05, 0.12, 0.85 * a); cr.fill_preserve()
    cr.set_source_rgba(*SAND[:3], a); cr.set_line_width(4); cr.stroke()
    fit_font(cr, big, 96, 800, 2); text(cr, big, 0, 10, GOLD, a, sp=2)
    fit_font(cr, small, 38, 800, 1, bold=False); text(cr, small, 0, 70, WHITE, a)
    cr.restore()

HOT = ('AFRICA', 'GREENLAND', 'LIE', 'TINY', 'BIGGER', 'MEXICO', 'CHINA', 'INDIA', 'UNION', 'STATES', 'JAPAN', 'KINGDOM')

def draw_captions(cr, T, t):
    for b in T['beats']:
        for l0, l1, s in b['lines']:
            if not (l0 <= t < l1 + 0.15): continue
            cs = chunks(s); total = sum(len(c) + 2 for c in cs); acc = 0
            for c in cs:
                c0 = l0 + (l1 - l0) * acc / total; acc += len(c) + 2; c1 = l0 + (l1 - l0) * acc / total
                if c0 <= t < c1 + (0.15 if c is cs[-1] else 0):
                    k = ease_back(prog(t, c0, c0 + 0.18), 3)
                    cr.save(); cr.translate(540, 1640); cr.scale(k, k)
                    up = c.upper(); fit_font(cr, up, 66, 960, 1); w = tw(cr, up, 1)
                    rrect(cr, -w / 2 - 28, -70, w + 56, 100, 22); cr.set_source_rgba(0, 0, 0, 0.55); cr.fill()
                    hl = any(ch.isdigit() for ch in c) or any(x in up for x in HOT)
                    text(cr, up, 0, 0, GOLD if hl else WHITE, 1, sp=1)
                    cr.restore(); return

def draw_outro(cr, b, t):
    a = ease_out(prog(t, b['start'] + 0.3, b['start'] + 0.8))
    if a <= 0: return
    font(cr, 80); text(cr, 'AFRICA IS', 540, 230, WHITE, a, sp=3, shadow=True)
    text(cr, 'WAY BIGGER', 540, 330, GOLD, a, sp=3, shadow=True)
    k2 = ease_back(prog(t, b['lines'][1][0], b['lines'][1][0] + 0.4))
    if k2 > 0.01:
        pill(cr, 'WHICH COUNTRY NEXT?  COMMENT', 540, 1380, 40, RED, WHITE, 1, scale=k2 * (1 + 0.03 * math.sin(t * 6)))

def render_frame(cr, t):
    T = TL
    draw_bg(cr, t)
    by = T['by']
    g0 = by['hook']['end']; w0, w1 = by['why']['start'], by['why']['end']
    merc_a = (1 - ease_io(prog(t, g0 - 0.35, g0 + 0.35)))
    why_a = ease_io(prog(t, w0 - 0.2, w0 + 0.4)) * (1 - ease_io(prog(t, w1 - 0.4, w1 + 0.2)))
    globe_a = (1 - merc_a) * (1 - why_a)
    draw_mercator(cr, T, t, merc_a)
    if globe_a > 0.001: draw_globe_scene(cr, T, t, globe_a)
    draw_mercator(cr, T, t, why_a, labels=True)
    b = beat_at(T, t)
    draw_header(cr, b, t)
    draw_fillbar(cr, T, t)
    draw_stat(cr, b, t)
    if b['key'] == 'outro': draw_outro(cr, b, t)
    draw_captions(cr, T, t)
    if b['key'] == 'hook':
        k = ease_back(prog(t, 0.0, 0.35))
        cr.save(); cr.translate(540, 1460); cr.scale(k, k)
        font(cr, 44); text(cr, 'WAIT FOR IT...', 0, 0, ICE, 0.9 * (1 - prog(t, b['lines'][1][0], b['lines'][1][0] + 0.3)), sp=6)
        cr.restore()
    f = prog(t, T['dur'] - 0.4, T['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- audio ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(6)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 116
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    for bi in range(int(dur / beat)):
        t0 = bi * beat; ch = chords[(bi // 4) % 4]; L = np.arange(int(0.3 * SR)) / SR
        if t0 > 1.0: put(music, t0, 0.42 * np.sin(2 * np.pi * np.cumsum(48 + 80 * np.exp(-L * 35)) / SR) * np.exp(-L * 10))
        M = np.arange(int(0.05 * SR)); put(music, t0 + beat / 2, 0.045 * np.diff(rng.standard_normal(len(M) + 1)) * np.exp(-M / SR * 70))
        mt = np.arange(int(beat * SR)) / SR; put(music, t0, 0.11 * np.tanh(3 * np.sin(2 * np.pi * note(ch[0] - 24) * mt)) * np.exp(-mt * 3))
        for s in range(2):  # marimba-ish arpeggio
            m = ch[(bi * 2 + s) % 3] + 12; pt = np.arange(int(0.3 * SR)) / SR
            put(music, t0 + s * beat / 2, 0.05 * (np.sin(2 * np.pi * note(m) * pt) + 0.25 * np.sin(2 * np.pi * 4 * note(m) * pt) * np.exp(-pt * 30)) * np.exp(-pt * 12))
    music = np.tanh(music * 1.2) * 0.5
    fx = np.zeros(n); by = T['by']
    for b in T['beats'][1:]:
        nz = rng.standard_normal(int(0.9 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2
        put(fx, b['start'] - 0.2, 0.15 * np.convolve(nz, np.ones(40) / 40, 'same') * env)
    def boom(t0, amp):
        L = np.arange(int(1.3 * SR)) / SR
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(40 + 90 * np.exp(-L * 12)) / SR) * np.exp(-L * 3.5))
    boom(by['hook']['lines'][1][0] + 0.6, 0.7)
    for key in FILL_ORDER + ['greenland']:  # thud when each piece lands
        fb = by[key if key != 'uk' else 'japan']
        t0 = fb['lines'][0][0] + (0.0 if key != 'uk' else (fb['lines'][0][1] - fb['lines'][0][0]) * 0.45) + 1.0
        if key == 'greenland': t0 = by['greenland']['start'] + 1.5
        boom(t0, 0.35)
    for b in T['beats']:
        if b['stat']:
            L = np.arange(int(0.8 * SR)) / SR
            put(fx, stat_time(b), 0.12 * sum(np.sin(2 * np.pi * f * L) * np.exp(-L * d) for f, d in ((1318.5, 6), (1975.5, 7))))
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.9
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.6 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx + v
    mix *= np.minimum(1, tt / 0.1) * np.minimum(1, (dur - tt) / 1.2)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

# ---------- parallel render ----------
def render_chunk(args):
    i0, i1, path = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
                           '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait()
    return path

def main():
    global GEO, TL
    data_dir, vdir, out = sys.argv[1:4]
    voice = Voice(vdir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache'))
    TL = build(voice); GEO = Geo(data_dir)
    print(f"duration {TL['dur']:.1f}s")
    for b in TL['beats']: print(f"  {b['key']:9s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 4 and sys.argv[4] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[5].split(','):
            render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]
    make_audio(TL, base + '.wav')
    n = int(TL['dur'] * FPS); workers = os.cpu_count() or 4
    bounds = np.linspace(0, n, workers * 2 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt',
                    '-i', base + '.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
