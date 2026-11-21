"""Europe's Weirdest Borders (9:16, British female voice).
One camera flies across Europe (Natural Earth 50m/10m) and zooms down to exact OpenStreetMap boundaries:
Baarle, Pheasant Island, Llivia, Busingen, Jungholz, Kaliningrad. Everything fires on the narrator's words.
Usage: python3 borders.py <data_dir> <out.mp4> [--preview t1,t2,...]
"""
import json, math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import vs
import space_choice as SC
import europe as E
from vs import ptext, rrect, tw, fit, face
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

def emoji(cr, e, *a, **k): vs.emoji(cr, e.replace('️', ''), *a, **k)

W, H, FPS = 1080, 1920, 30
SC.VOICE, SC.RATE = 'en-GB-SoniaNeural', '+6%'
WHITE, GOLD, CYAN, PINK, INK = E.WHITE, E.GOLD, E.CYAN, E.PINK, E.INK

BEATS = [
    ('hook', "This town is split between two countries... in more than twenty pieces. And it's not even the weirdest border in Europe."),
    ('baarle', "This is Baarle. Over twenty tiny patches of Belgium are scattered inside the Netherlands... and some of those patches have little bits of the Netherlands inside them."),
    ('door', "The border even runs through homes and cafés. Which country your house is in depends on where your front door is."),
    ('pheasant', "Between France and Spain sits Pheasant Island. Every six months, it switches countries... and it's been doing that since 1659."),
    ('llivia', "Nearby, Llívia is a Spanish town completely surrounded by France. In 1659, Spain handed France thirty-three villages, but Llívia was a town, not a village... so it stayed Spanish."),
    ('busingen', "Büsingen belongs to Germany, but it's surrounded by Switzerland. Locals mostly pay in Swiss francs, and homes can have German and Swiss phone numbers."),
    ('jungholz', "Jungholz, in Austria, touches the rest of its country at one single point: a mountaintop. To drive there, you have to go through Germany."),
    ('kalin', "And Russia has a piece of land stuck in the middle of Europe: Kaliningrad, wedged between Poland and Lithuania, hundreds of kilometres from the rest of Russia. Until 1945, it was the German city of Königsberg."),
    ('cta', "So, which border is the weirdest? Tell me the number in the comments, and follow for more."),
]

CC = {k: hexc(v)[:3] for k, v in {'NLD': '#FF7A1A', 'BEL': '#FFE14D', 'FRA': '#3DA5FF', 'ESP': '#FF5A5F', 'AND': '#B06BFF', 'DEU': '#3DE0C8',
                                   'CHE': '#FF4F6D', 'AUT': '#B06BFF', 'ITA': '#3DFF8F', 'LIE': '#FFC93C', 'RUS': '#FF4F6D', 'POL': '#FFE14D',
                                   'LTU': '#3DA5FF', 'BLR': '#8CFF5A', 'LVA': '#B06BFF', 'UKR': '#FFC93C', 'LUX': '#B06BFF'}.items()}
NE10 = ['RUS', 'BLR', 'UKR', 'POL', 'LTU', 'LVA', 'FRA', 'DEU', 'AUT', 'ITA', 'NLD', 'ESP', 'AND', 'BEL', 'LUX', 'CHE', 'LIE']
STOPS = [('BAARLE', (4.93, 51.44), ''), ('PHEASANT ISLAND', (-1.766, 43.343), 'FRANCE / SPAIN'), ('LLÍVIA', (1.985, 42.47), 'SPAIN in FRANCE'),
         ('BÜSINGEN', (8.69, 47.70), 'GERMANY in SWITZERLAND'), ('JUNGHOLZ', (10.45, 47.57), 'AUSTRIA via GERMANY'), ('KALININGRAD', (20.5, 54.7), 'RUSSIA, SURROUNDED BY THE EU')]

def polys_of(geom):
    ps = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    return [[np.array(r, float) for r in p] for p in ps]
def proj_polys(ps): return [[E.laea(r[:, 0], r[:, 1]) for r in p] for p in ps]

class Data:
    def __init__(self, d):
        self.ne10 = {}
        for f in json.load(open(os.path.join(d, 'ne10', 'ne_10m_admin_0_countries.geojson')))['features']:
            a3 = f['properties']['ADM0_A3']
            if a3 in NE10:
                for r in E.rings(f['geometry']):
                    if (E.overlaps(r) or a3 == 'RUS') and len(r) > 3:
                        self.ne10.setdefault('UKR' if (a3 == 'RUS' and E.crimea(r)) else a3, []).append(E.laea(r[:, 0], r[:, 1]))
        def osm(i, j=0): return polys_of(json.load(open(os.path.join(d, 'osm', f'q{i}.geojson')))['features'][j]['geometry'])
        bh, bn = osm(1), osm(2)
        area = lambda r: 0.5 * abs(np.dot(r[:, 0], np.roll(r[:, 1], 1)) - np.dot(r[:, 1], np.roll(r[:, 0], 1)))
        main = max(range(len(bh)), key=lambda k: area(bh[k][0]))
        self.bh_main = proj_polys([bh[main]])
        cx, cy = 4.93, 51.44
        rest = [p for k, p in enumerate(bh) if k != main]
        rest.sort(key=lambda p: math.hypot(p[0][:, 0].mean() - cx, p[0][:, 1].mean() - cy))
        self.bh_parts = proj_polys(rest)
        near = [p for p in rest if abs(p[0][:, 0].mean() - 4.935) < 0.03 and abs(p[0][:, 1].mean() - 51.443) < 0.018]
        ex = np.concatenate([p[0] for p in near]); x0, x1 = ex[:, 0].min(), ex[:, 0].max(); y0, y1 = ex[:, 1].min(), ex[:, 1].max()
        self.baarle_c = ((x0 + x1) / 2, (y0 + y1) / 2 - 0.0016)
        wkm = (x1 - x0) * 111.32 * math.cos(math.radians(51.44)); hkm = (y1 - y0) * 110.54
        self.baarle_s = min(940 / wkm, 820 / hkm)
        self.bn = proj_polys(bn)
        self.busingen = proj_polys(osm(3)); self.reutte = proj_polys(osm(4)); self.jungholz_ll = osm(5); self.jungholz = proj_polys(self.jungholz_ll)
        self.llivia = proj_polys(osm(6)); self.pheasant_ll = osm(7)[0][0]
        # where Jungholz touches the rest of Austria: the closest pair of vertices
        rt = osm(4); main_r = max(rt, key=lambda p: len(p[0]))[0]; jr = self.jungholz_ll[0][0]
        d2 = ((jr[:, None, :] - main_r[None, :, :]) ** 2).sum(-1); i, j = np.unravel_index(np.argmin(d2), d2.shape)
        self.touch = tuple((jr[i] + main_r[j]) / 2)

D = None
TL = None

# ---------- timeline ----------
_missing = set()
def build(voice):
    t, beats, clips = 0.0, [], []
    lead = {'hook': 0.25, 'pheasant': 1.4, 'llivia': 1.0, 'busingen': 1.3, 'jungholz': 1.0, 'kalin': 1.3}
    tail = {'hook': 0.5, 'door': 0.5, 'cta': 2.4}
    for key, text in BEATS:
        a, words = voice.get(text)
        b = dict(key=key, text=text, start=t, l0=t + lead.get(key, 0.3)); b['l1'] = b['l0'] + len(a) / SR
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
def during(t, k0, k1=None, fin=0.4, fout=0.4):
    a, b = bt(k0)['start'], bt(k1 or k0)['end']
    return ease_out(prog(t, a, a + fin)) * (1 - ease_io(prog(t, b - fout, b)))

# ---------- camera: fly between the stops ----------
BAARLE_V, HENDAYE_V, LLIVIA_V = (4.905, 51.428, 118), (-1.77, 43.33, 32), (1.99, 42.462, 46)
BUSINGEN_V, JUNGHOLZ_V, KALIN_V, END_V = (8.685, 47.698, 62), (10.43, 47.555, 40), (24.5, 55.0, 0.58), (11.5, 49.0, 0.33)
def keys():
    hp, lv, bs, jh, kl, ct = (bt(k)['start'] for k in ('pheasant', 'llivia', 'busingen', 'jungholz', 'kalin', 'cta'))
    bc, bs_ = D.baarle_c, D.baarle_s
    K = [(0.0, (bc[0], bc[1], bs_ * 0.62)), (w('hook', 'pieces'), (bc[0], bc[1], bs_)), (bt('door')['end'], (bc[0], bc[1], bs_ * 1.05)),
         (hp + 0.5, (3.0, 49.0, 2.2)), (hp + 1.2, (0.0, 46.0, 0.9)), (hp + 2.0, (-1.6, 43.6, 6)), (hp + 2.6, HENDAYE_V),
         (lv, HENDAYE_V), (lv + 0.6, (0.2, 43.0, 4)), (lv + 1.4, LLIVIA_V),
         (bs, LLIVIA_V), (bs + 0.5, (2.5, 44.5, 2.2)), (bs + 1.0, (5.5, 46.2, 0.9)), (bs + 1.5, (8.4, 47.6, 6)), (bs + 2.0, BUSINGEN_V),
         (jh, BUSINGEN_V), (jh + 0.6, (9.6, 47.6, 7)), (jh + 1.4, JUNGHOLZ_V),
         (kl, JUNGHOLZ_V), (kl + 0.5, (12.0, 49.0, 4)), (kl + 1.0, (16.0, 52.0, 1.0)), (kl + 1.6, KALIN_V),
         (ct, KALIN_V), (ct + 1.2, END_V)]
    return [(t, E.laea(c[0], c[1]), c[2]) for t, c in K]
def camera(t):
    K = TL['keys']
    for (t0, p0, s0), (t1, p1, s1) in zip(K, K[1:]):
        if t <= t1:
            k = ease_io(prog(t, t0, t1)); s = math.exp(lerp(math.log(s0), math.log(s1), k))
            if s1 > s0 * 1.05:  # zooming in: keep the target gliding to the centre in screen space
                cx = p1[0] - (p1[0] - p0[0]) * s0 * (1 - k) / s; cy = p1[1] - (p1[1] - p0[1]) * s0 * (1 - k) / s
            elif s1 < s0 / 1.05:
                cx = p0[0] - (p0[0] - p1[0]) * s1 * k / s; cy = p0[1] - (p0[1] - p1[1]) * s1 * k / s
            else: cx, cy = lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k)
            return float(cx), float(cy), s * (1 + 0.01 * math.sin(t * 0.4))
    (_, p, s) = K[-1]; return float(p[0]), float(p[1]), s

def path_polys(cr, cam, ps):
    for p in ps:
        for x, y in p:
            X, Y = E.S(cam, x, y)
            if X.max() < -50 or X.min() > W + 50 or Y.max() < -50 or Y.min() > H + 50: continue
            cr.move_to(X[0], Y[0]); [cr.line_to(a, b) for a, b in zip(X[1:], Y[1:])]; cr.close_path()

def fill_polys(cr, cam, ps, col, a, edge=0.9, lw=2.0):
    if a <= 0.01: return
    cr.new_path(); cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); path_polys(cr, cam, ps)
    cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, edge * a); cr.set_line_width(lw); cr.stroke()
    cr.set_fill_rule(cairo.FILL_RULE_WINDING)

def glow_polys(cr, cam, ps, col, a):
    if a <= 0.01: return
    cr.new_path(); path_polys(cr, cam, ps); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.set_source_rgba(*col, 0.35 * a); cr.set_line_width(18); cr.stroke_preserve(); cr.set_source_rgba(*col, a); cr.set_line_width(5); cr.stroke()

# ---------- the map ----------
def draw_countries(cr, t, cam):
    s = cam[2]
    for code, rs in E.G.c.items():  # Natural Earth 50m overview
        col = CC.get(code, E.PAL9[(E.G.mapc.get(code, 1) - 1) % 9][:3]); a = 0.92 if code in CC else 0.55
        cr.new_path(); E.path_rings(cr, cam, rs); cr.set_source_rgba(*col, a); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, 0.5); cr.set_line_width(1.2); cr.stroke()
    k10 = clamp((s - 1.5) / 1.5)
    if k10 > 0:  # Natural Earth 10m once we're closer
        dim = 1 - 0.55 * clamp((s - 25) / 40)
        for code in NE10:
            cr.new_path(); E.path_rings(cr, cam, D.ne10.get(code, [])); cr.set_source_rgba(*[v * dim for v in CC[code]], k10); cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, 0.7 * k10); cr.set_line_width(2); cr.stroke()

def osm_alpha(s, lo=12): return clamp((s - lo) / lo)

def draw_baarle(cr, t, cam):
    a = osm_alpha(cam[2], 20)
    if a <= 0: return
    fill_polys(cr, cam, D.bn, CC['NLD'], a, 0.6)
    fill_polys(cr, cam, D.bh_main, CC['BEL'], a, 0.9)
    t0, t1 = w('hook', 'split'), w('hook', 'pieces', end=True)
    n = len(D.bh_parts)
    for i, p in enumerate(D.bh_parts):
        ti = t0 + (t1 - t0) * i / max(1, n - 1)
        if t < ti: continue
        k = pop_k(t, ti, 0.3)
        X, Y = E.S(cam, p[0][0], p[0][1]); cx, cy = X.mean(), Y.mean()
        cr.save(); cr.translate(cx, cy); cr.scale(k, k); cr.translate(-cx, -cy); fill_polys(cr, cam, [p], CC['BEL'], a, 1.0, 2.5); cr.restore()
    ti = w('baarle', 'inside', 1) if w('baarle', 'inside', 1) != bt('baarle')['l0'] else w('baarle', 'little')
    if t >= ti:  # the Dutch counter-enclaves inside the Belgian patches
        ka = ease_out(prog(t, ti, ti + 0.4)) * (1 - ease_io(prog(t, bt('door')['end'] - 0.3, bt('door')['end'])))
        holes = [[r] for p in D.bh_parts + D.bh_main for r in p[1:]]
        for h in holes:
            X, Y = E.S(cam, h[0][0], h[0][1]); x, y = X.mean(), Y.mean()
            rr = 22 + 12 * math.sin(t * 6); cr.new_path(); cr.arc(x, y, rr, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, ka); cr.set_line_width(4); cr.stroke()
    la = a * during(t, 'hook', 'door', 0.4, 0.4)
    if la > 0:
        for txt, col, x in (('BELGIUM', CC['BEL'], 300), ('NETHERLANDS', CC['NLD'], 700)):
            wd_ = tw(cr, txt, 34, 'Poppins ExtraBold'); bw = wd_ + 90
            rrect(cr, x - bw / 2, 296, bw, 60, 30); cr.set_source_rgba(0.04, 0.06, 0.16, 0.85 * la); cr.fill()
            cr.new_path(); cr.arc(x - bw / 2 + 32, 326, 15, 0, 2 * math.pi); cr.set_source_rgba(*col, la); cr.fill()
            ptext(cr, txt, x + 20, 338, 34, WHITE, la, fam='Poppins ExtraBold', sw=0, shadow=False)

def draw_jungholz(cr, t, cam):
    a = osm_alpha(cam[2], 10)
    if a <= 0: return
    fill_polys(cr, cam, D.reutte, CC['AUT'], a, 0.25, 1.5)
    hl = during(t, 'jungholz', None, 0.3, 0.5)
    fill_polys(cr, cam, D.jungholz, tuple(lerp(x, y, 0.35 * hl) for x, y in zip(CC['AUT'], (1, 1, 1))), a, 1.0, 3)
    if hl > 0:
        tp = w('jungholz', 'single'); x, y = E.L(cam, *D.touch)
        if t >= tp:
            r = prog(t, tp, tp + 1.2) % 1.0 if t < tp + 3 else 1.0
            cr.new_path(); cr.arc(x, y, 12 + 60 * ease_out(r), 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, hl * (1 - r)); cr.set_line_width(4); cr.stroke()
            cr.new_path(); cr.arc(x, y, 9, 0, 2 * math.pi); cr.set_source_rgba(*GOLD[:3], hl); cr.fill()
            emoji(cr, '⛰️', x + 4, y - 60, 70 * pop_k(t, w('jungholz', 'mountaintop')), hl)
            ptext(cr, 'ONE SINGLE POINT', x + 60, y + 70, 38, GOLD, hl * ease_out(prog(t, tp, tp + 0.4)), fam='Poppins Black', anchor='l', sw=7)
        td = w('jungholz', 'drive')
        if t >= td:  # the only road in: through Germany
            pts = [(10.38, 47.62), (10.40, 47.595), (10.425, 47.585), (10.445, 47.576)]
            X, Y = E.L(cam, [p[0] for p in pts], [p[1] for p in pts]); k = ease_io(prog(t, td, td + 1.4)); n = max(2, int(len(X) * 8 * k))
            dense = np.stack([np.interp(np.linspace(0, len(X) - 1, 40), np.arange(len(X)), X), np.interp(np.linspace(0, len(X) - 1, 40), np.arange(len(X)), Y)], 1)
            n = max(2, int(40 * k)); cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.new_path(); cr.move_to(*dense[0]); [cr.line_to(*q) for q in dense[1:n]]; cr.set_source_rgba(1, 1, 1, hl); cr.set_line_width(8); cr.set_dash([18, 12]); cr.stroke(); cr.set_dash([])
            emoji(cr, '🚗', dense[n - 1][0], dense[n - 1][1] - 10, 64, hl)
        for txt, ll in (('GERMANY', (10.36, 47.535)), ('AUSTRIA', (10.53, 47.505)), ('JUNGHOLZ', (10.49, 47.6))):
            x, y = E.L(cam, *ll); ptext(cr, txt, x, y, 44 if txt != 'JUNGHOLZ' else 46, GOLD if txt == 'JUNGHOLZ' else WHITE, hl, sw=8)

def draw_single(cr, t, cam, ps, beat, col, labels, lo=10):
    a = osm_alpha(cam[2], lo)
    if a <= 0: return
    fill_polys(cr, cam, ps, col, a, 1.0, 3)
    hl = during(t, beat, None, 0.4, 0.5)
    if hl > 0:
        glow_polys(cr, cam, ps, (1, 1, 1), hl * (0.55 + 0.45 * math.sin(t * 5)))
        for txt, ll, size, c in labels:
            x, y = E.L(cam, *ll); ptext(cr, txt, x, y, size, c, hl, sw=8)

def draw_kalin(cr, t, cam):
    hl = during(t, 'kalin', None, 0.5, 0.4)
    if hl <= 0: return
    tk = w('kalin', 'Kaliningrad')
    if t >= tk:
        x0, y0 = E.L(cam, 20.5, 54.7); x1, y1 = E.L(cam, 28.2, 56.1); k = ease_io(prog(t, tk + 0.6, tk + 1.6))
        cr.new_path(); cr.move_to(x0, y0); cr.line_to(lerp(x0, x1, k), lerp(y0, y1, k)); cr.set_source_rgba(1, 1, 1, hl); cr.set_line_width(5); cr.set_dash([14, 10]); cr.stroke(); cr.set_dash([])
        r = (t * 0.9) % 1.0; cr.new_path(); cr.arc(x0, y0, 20 + 70 * r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, hl * (1 - r)); cr.set_line_width(4); cr.stroke()
        k2 = pop_k(t, tk); cr.save(); cr.translate(x0 - 30, y0 - 80); cr.scale(k2, k2)
        ptext(cr, 'KALININGRAD', 0, 0, 46, GOLD, hl, anchor='r', sw=8); ptext(cr, '(RUSSIA)', 0, 44, 34, WHITE, hl, fam='Poppins ExtraBold', anchor='r', sw=6); cr.restore()
    for txt, ll, word in (('POLAND', (19.4, 52.4), 'Poland'), ('LITHUANIA', (25.2, 55.55), 'Lithuania'), ('RUSSIA', (33.0, 56.5), 'rest')):
        t0 = w('kalin', word)
        if t >= t0:
            x, y = E.L(cam, *ll); k = pop_k(t, t0); cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, txt, 0, 0, 40, WHITE, hl, sw=7); cr.restore()

# ---------- cards ----------
def card_house(cr, t):
    b = bt('door'); t0 = w('door', 'border')
    if not (t0 <= t < b['end'] + 0.3): return
    a = 1 - ease_io(prog(t, b['end'] - 0.2, b['end'] + 0.3)); k = pop_k(t, t0, 0.45)
    cr.save(); cr.translate(540, 1080); cr.scale(k, k)
    rrect(cr, -440, -270, 880, 520, 40); cr.set_source_rgba(0.04, 0.06, 0.16, 0.94 * a); cr.fill()
    cr.save(); rrect(cr, -410, -240, 820, 460, 26); cr.clip()
    cr.rectangle(-410, -240, 410, 460); cr.set_source_rgba(*CC['BEL'], 0.9 * a); cr.fill()
    cr.rectangle(0, -240, 410, 460); cr.set_source_rgba(*CC['NLD'], 0.9 * a); cr.fill(); cr.restore()
    # the house straddling the border
    cr.new_path(); cr.move_to(-230, -40); cr.line_to(0, -200); cr.line_to(230, -40); cr.close_path(); cr.set_source_rgba(0.75, 0.25, 0.2, a); cr.fill()
    rrect(cr, -200, -40, 400, 230, 6); cr.set_source_rgba(0.97, 0.95, 0.9, a); cr.fill()
    for wx in (-150, 70): rrect(cr, wx, 0, 80, 70, 6); cr.set_source_rgba(0.55, 0.8, 1.0, a); cr.fill()
    tf = w('door', 'front'); glow_d = ease_out(prog(t, tf, tf + 0.4))
    if glow_d > 0:
        g = cairo.RadialGradient(-75, 120, 0, -75, 120, 120); g.add_color_stop_rgba(0, 1, 0.9, 0.3, 0.8 * glow_d * a); g.add_color_stop_rgba(1, 1, 0.9, 0.3, 0)
        cr.set_source(g); cr.arc(-75, 120, 120, 0, 2 * math.pi); cr.fill()
    rrect(cr, -110, 60, 70, 130, 8); cr.set_source_rgba(0.45, 0.25, 0.12, a); cr.fill()
    cr.new_path(); cr.arc(-52, 128, 5, 0, 2 * math.pi); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
    kb = ease_io(prog(t, t0, t0 + 0.8))  # the border line cuts through the house
    cr.new_path(); cr.move_to(0, -240); cr.line_to(0, -240 + 460 * kb); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(6); cr.set_dash([16, 10]); cr.stroke(); cr.set_dash([])
    ptext(cr, 'BELGIUM', -205, -195, 40, INK, a, sw=0, shadow=False); ptext(cr, 'NETHERLANDS', 205, -195, 40, INK, a, sw=0, shadow=False)
    ptext(cr, 'FRONT DOOR IN BELGIUM = BELGIAN HOME', 0, 225, 32, WHITE, a * glow_d, fam='Poppins ExtraBold', sw=6)
    cr.restore()

def card_pheasant(cr, t):
    b = bt('pheasant'); t0 = w('pheasant', 'Pheasant')
    if not (t0 <= t < b['end'] + 0.3): return
    a = 1 - ease_io(prog(t, b['end'] - 0.2, b['end'] + 0.3)); k = pop_k(t, t0, 0.45)
    cr.save(); cr.translate(540, 1060); cr.scale(k, k)
    rrect(cr, -460, -300, 920, 600, 40); cr.set_source_rgba(0.04, 0.06, 0.16, 0.95 * a); cr.fill()
    cr.save(); rrect(cr, -430, -270, 860, 540, 26); cr.clip()
    cr.set_source_rgba(0.12, 0.38, 0.65, a); cr.paint()
    cr.new_path(); cr.move_to(-430, -270); cr.line_to(430, -270); cr.line_to(430, -140); cr.curve_to(150, -150, -150, -110, -430, -60); cr.close_path()
    cr.set_source_rgba(*CC['FRA'], 0.95 * a); cr.fill()
    cr.new_path(); cr.move_to(-430, 270); cr.line_to(430, 270); cr.line_to(430, 120); cr.curve_to(150, 150, -150, 170, -430, 190); cr.close_path()
    cr.set_source_rgba(*CC['ESP'], 0.95 * a); cr.fill()
    ptext(cr, 'FRANCE (HENDAYE)', 0, -200, 38, WHITE, a, sw=7); ptext(cr, 'SPAIN (IRUN)', 0, 235, 38, WHITE, a, sw=7)
    # the island itself, true shape (about 200 m long)
    r = D.pheasant_ll; lat0 = r[:, 1].mean(); X = (r[:, 0] - r[:, 0].mean()) * 111320 * math.cos(math.radians(lat0)); Y = -(r[:, 1] - lat0) * 110540
    sc = 520 / (X.max() - X.min())
    ts = w('pheasant', 'switches'); flips = int(max(0, t - ts) / 0.55) if t >= ts else 0
    spain = flips % 2 == 1
    col = CC['ESP'] if spain else CC['FRA']
    cr.new_path(); cr.move_to(X[0] * sc, Y[0] * sc + 30); [cr.line_to(x * sc, y * sc + 30) for x, y in zip(X[1:], Y[1:])]; cr.close_path()
    cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(5); cr.stroke()
    if t >= ts: ptext(cr, 'SPAIN' if spain else 'FRANCE', 0, 50, 40, WHITE, a, sw=7)
    else: ptext(cr, 'PHEASANT ISLAND', 0, 50, 34, WHITE, a, fam='Poppins ExtraBold', sw=6)
    cr.restore()
    ptext(cr, '~200 m long', 330, 300 - 20, 26, WHITE, a * 0.9, fam='Poppins ExtraBold', anchor='r', sw=4)
    cr.restore()

# ---------- titles, chips, CTA ----------
TITLES = [('hook', 'town', '1 TOWN · 2 COUNTRIES'), ('hook', 'weirdest', "EUROPE'S WEIRDEST BORDERS"), ('baarle', 'Baarle', '#1 BAARLE'),
          ('pheasant', 'Pheasant', '#2 PHEASANT ISLAND'), ('llivia', 'Llívia', '#3 LLÍVIA'), ('busingen', 'Büsingen', '#4 BÜSINGEN'),
          ('jungholz', 'Jungholz', '#5 JUNGHOLZ'), ('kalin', 'Kaliningrad', '#6 KALININGRAD'), ('cta', 'which', None)]
def draw_title(cr, t):
    cur, t0 = None, 0
    for key, word, txt in TITLES:
        tw0 = w(key, word)
        if t >= tw0: cur, t0 = txt, tw0
    if cur:
        k = prog(t, t0, t0 + 0.3); sc = lerp(1.7, 1.0, ease_out(k))
        cr.save(); cr.translate(540, 210); cr.scale(sc, sc)
        ptext(cr, cur, 0, 0, fit(cr, cur, 84, 1000), WHITE, clamp(k * 3), sw=11); cr.restore()
        for name, ll, sub in STOPS:
            if cur.endswith(name) and sub:
                ptext(cr, sub.upper(), 540, 292, 40, GOLD, clamp(k * 3), fam='Poppins ExtraBold', sw=6)

def chip(cr, t, t0, x, y, txt, e, out=1.0, size=42):
    if t < t0 or out <= 0: return
    k = pop_k(t, t0); fs = fit(cr, txt, size, 820, 'Poppins ExtraBold')
    cr.save(); cr.translate(x, y); cr.scale(k, k)
    wd_ = tw(cr, txt, fs, 'Poppins ExtraBold'); bw = wd_ + 130
    rrect(cr, -bw / 2, -40, bw, 80, 40); cr.set_source_rgba(0.05, 0.06, 0.18, 0.9 * out); cr.fill_preserve()
    cr.set_source_rgba(*CYAN[:3], out); cr.set_line_width(3); cr.stroke()
    emoji(cr, e, -bw / 2 + 48, -2, 48, out); ptext(cr, txt, 35, fs * 0.36, fs, WHITE, out, fam='Poppins ExtraBold', sw=5); cr.restore()

CHIPS = [('baarle', 'twenty', '22 PATCHES OF BELGIUM', '🧩', 1400), ('baarle', 'little', '+ DUTCH BITS INSIDE THEM', '🤯', 1492),
         ('pheasant', 'six', 'FEB–JUL: SPAIN · AUG–JAN: FRANCE', '📅', 1440), ('pheasant', '1659', 'SINCE 1659', '📜', 1532),
         ('llivia', 'thirty', '33 VILLAGES WENT TO FRANCE', '🏘️', 1400), ('llivia', 'town', 'LLÍVIA WAS A TOWN', '😏', 1492),
         ('busingen', 'francs', 'PAYS IN SWISS FRANCS', '💰', 1400), ('busingen', 'phone', '+49 AND +41 PHONE NUMBERS', '📞', 1492),
         ('kalin', 'Königsberg', 'UNTIL 1945: KÖNIGSBERG', '🏰', 1400)]
def draw_chips(cr, t):
    for beat, word, txt, e, y in CHIPS:
        chip(cr, t, w(beat, word), 540, y, txt, e, during(t, beat, None, 0.1, 0.4))

def draw_end(cr, t, cam):
    a = ease_out(prog(t, bt('cta')['start'] + 0.6, bt('cta')['start'] + 1.2))
    if a <= 0: return
    for i, (name, ll, _) in enumerate(STOPS):
        x, y = E.L(cam, *ll); t0 = bt('cta')['start'] + 0.7 + i * 0.15
        if t < t0: continue
        k = pop_k(t, t0); cr.save(); cr.translate(x, y); cr.scale(k, k)
        cr.new_path(); cr.arc(0, 0, 26, 0, 2 * math.pi); cr.set_source_rgba(*PINK[:3], 1); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, 1); cr.set_line_width(3); cr.stroke()
        ptext(cr, str(i + 1), 0, 12, 32, WHITE, 1, sw=0, shadow=False); cr.restore()
    tq = w('cta', 'which')
    if t >= tq:
        k = pop_k(t, tq) * (1 + 0.025 * math.sin(t * 5))
        cr.save(); cr.translate(540, 1380); cr.scale(k, k)
        rrect(cr, -500, -120, 1000, 250, 40); cr.set_source_rgba(0.04, 0.06, 0.16, 0.9); cr.fill()
        ptext(cr, 'WHICH IS THE WEIRDEST?', 0, -30, fit(cr, 'WHICH IS THE WEIRDEST?', 72, 900), WHITE, 1, sw=9)
        ptext(cr, 'COMMENT 1–6', 0, 62, 80, GOLD, 1, sw=10); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1720); cr.scale(k, k)
        txt = 'FOLLOW FOR MORE'; wd_ = tw(cr, txt, 54)
        rrect(cr, -wd_ / 2 - 90, -62, wd_ + 180, 96, 48); cr.set_source_rgba(*PINK[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 54, WHITE, 1, sw=6); emoji(cr, '🔔', -wd_ / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def draw_captions(cr, t):
    for b in TL['beats']:
        if b['key'] == 'cta' and t >= w('cta', 'which'): return
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
        cr.save(); cr.translate(540, 1700); cr.scale(sc, sc); x = -total / 2
        for j, (u, wd_) in enumerate(zip(ups, widths)):
            cr.save(); cr.translate(x + wd_ / 2, 0)
            if j == ci: k = ease_back(prog(t, g[j][0], g[j][0] + 0.15), 3); cr.scale(1 + 0.12 * k, 1 + 0.12 * k)
            ptext(cr, u, 0, 0, size, GOLD if j == ci else WHITE, 1.0 if j <= ci else 0.6, sw=10)
            cr.restore(); x += wd_ + space
        cr.restore(); return

def render_frame(cr, t):
    cam = camera(t)
    E.draw_base(cr, t, cam)
    draw_countries(cr, t, cam)
    draw_baarle(cr, t, cam)
    draw_single(cr, t, cam, D.llivia, 'llivia', CC['ESP'], [('LLÍVIA', (1.985, 42.4985), 46, GOLD), ('FRANCE', (2.07, 42.43), 44, WHITE), ('SPAIN', (1.93, 42.405), 44, WHITE)])
    draw_single(cr, t, cam, D.busingen, 'busingen', CC['DEU'], [('BÜSINGEN', (8.688, 47.721), 46, GOLD), ('SWITZERLAND', (8.64, 47.665), 44, WHITE), ('GERMANY', (8.75, 47.735), 40, WHITE)])
    draw_jungholz(cr, t, cam)
    draw_kalin(cr, t, cam)
    E.draw_lakes_vignette(cr, cam)
    card_house(cr, t)
    card_pheasant(cr, t)
    draw_title(cr, t)
    draw_chips(cr, t)
    draw_end(cr, t, cam)
    draw_captions(cr, t)
    oa = osm_alpha(cam[2], 10)
    if oa > 0: ptext(cr, 'Map data © OpenStreetMap contributors', 1050, 1885, 22, WHITE, 0.75 * oa, fam='Poppins ExtraBold', anchor='r', sw=3)
    f = prog(t, TL['dur'] - 0.4, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- score ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    g = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n)
    chords = [[48, 55, 60, 64], [45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59]]  # C Am F G, playful
    beat = 0.42
    for ci in range(int(dur / (beat * 8)) + 1):
        ch = chords[ci % 4]; t0 = ci * beat * 8; L_ = np.arange(int(4.0 * SR)) / SR
        env = np.minimum(1, L_ / 0.6) * np.exp(-L_ * 0.5)
        put(music, t0, sum(0.022 * (np.sin(2 * np.pi * note(m) * L_) + 0.5 * np.sin(2 * np.pi * note(m) * 1.004 * L_ + 1)) for m in ch) * env)
        for j in range(8):
            pt = np.arange(int(0.35 * SR)) / SR; m = ch[[0, 2, 3, 2, 1, 2, 3, 1][j]] + 12
            put(music, t0 + j * beat, 0.055 * np.sin(2 * np.pi * note(m) * pt) * np.exp(-pt * 12))
        for j in range(0, 8, 2):
            kt = np.arange(int(0.22 * SR)) / SR; put(music, t0 + j * beat, 0.12 * np.sin(2 * np.pi * (55 + 70 * np.exp(-kt * 25)) * kt) * np.exp(-kt * 15))
    rev = np.zeros(n)
    for d, gg in ((0.19, 0.25), (0.33, 0.15)): k = int(d * SR); rev[k:] += gg * music[:-k]
    music = np.tanh((music + rev) * 1.2) * 0.6
    fx = np.zeros(n)
    def pop(t0, amp=0.06, f=900):
        L_ = np.arange(int(0.07 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * f * L_ * (1 + 2 * L_)) * np.exp(-L_ * 60))
    def boom(t0, amp=0.5):
        L_ = np.arange(int(1.8 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(34 + 60 * np.exp(-L_ * 8)) / SR) * np.exp(-L_ * 2.4))
    def whoosh(t0, amp=0.18, d=1.4):
        L_ = int(d * SR); nz = g.standard_normal(L_); sm = np.convolve(nz, np.ones(25) / 25, 'same')
        put(fx, t0, amp * sm * np.sin(np.pi * np.linspace(0, 1, L_)) ** 2)
    def chime(t0, amp=0.07):
        L_ = np.arange(int(0.9 * SR)) / SR; put(fx, t0, amp * sum(np.sin(2 * np.pi * f * L_) * np.exp(-L_ * d) for f, d in ((1568, 4), (2349, 5))))
    t0, t1 = w('hook', 'split'), w('hook', 'pieces', end=True); nb = len(D.bh_parts)
    for i in range(nb): pop(t0 + (t1 - t0) * i / max(1, nb - 1), 0.06, 700 + 30 * i)
    for key in ('pheasant', 'llivia', 'busingen', 'jungholz', 'kalin', 'cta'): whoosh(bt(key)['start'] + 0.1)
    for key, word, txt in TITLES:
        if txt: boom(w(key, word), 0.45)
    for beat, word, *_ in CHIPS: chime(w(beat, word))
    ts = w('pheasant', 'switches')
    for i in range(int((bt('pheasant')['end'] - ts) / 0.55)): pop(ts + i * 0.55, 0.05, 1300)
    v = np.zeros(n)
    for s_, a in T['clips']: put(v, s_, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx + v
    mix *= np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 1.5)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    global D, TL
    E.G = E.Geo(data_dir); D = Data(data_dir)
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
    data_dir, out = sys.argv[1], sys.argv[2]
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_borders'))
    print(f"duration {TL['dur']:.1f}s")
    for b in TL['beats']: print(f"  {b['key']:10s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','):
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
