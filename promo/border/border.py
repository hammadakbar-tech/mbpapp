"""'Why 90% of Canadians Live Near the Border' (9:16): Canada-at-night city lights, border band, four reasons.
Map is a Lambert azimuthal equal-area projection centred on Canada; frames render in parallel workers.
Usage: python3 border.py <data_dir> <voices_dir> <out.mp4> [--preview t1,t2,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import quiz
from quiz import font, tw, text, fit_font, rrect, pill, clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, Voice, SR
from canada import vec, rings, chunks
from ca_cities import CITIES

W, H, FPS = 1080, 1920, 30
MAPY = 800
quiz.SPEED = 1.05
LON0, LAT0, RE = -96.0, 58.0, 6371.0

NIGHT0, NIGHT1 = hexc('#070C18'), hexc('#02040A')
CAN_FILL, CAN_EDGE, PROV_EDGE = hexc('#111C30'), hexc('#3A5277'), hexc('#22324D')
US_FILL, US_EDGE = hexc('#0B1322'), hexc('#26344C')
LIGHT, GOLD, WHITE, RED, ICE = hexc('#FFE3A3'), hexc('#FFC845'), hexc('#FFFFFF'), hexc('#EF3340'), hexc('#9FD8FF')
ROCK, FARM, TRADE, RAIL = hexc('#8C86A8'), hexc('#5BD16E'), hexc('#4FC3F7'), hexc('#FF8A3D')

PERMAFROST = [(-141, 61), (-135, 60), (-125, 59), (-118, 58), (-112, 57.5), (-104, 56.5), (-97, 55.5), (-92, 54.5),
              (-87, 53.5), (-82, 52.5), (-79, 52.8), (-76, 54.5), (-72, 54.8), (-66, 53.5), (-60, 53.5), (-55, 52.5),
              (-50, 60), (-50, 85), (-145, 85), (-145, 61)]
SHIELD = [(-110, 60), (-105, 57), (-100, 55), (-96, 51), (-90, 48.6), (-84, 46.5), (-80, 45.3), (-76, 45.2), (-72, 46.6),
          (-67, 49.5), (-60, 51.5), (-56, 53), (-60, 58), (-65, 60), (-70, 62.5), (-78, 62.5), (-85, 66), (-95, 68),
          (-105, 68), (-115, 67), (-120, 64), (-116, 61)]
FARMS = [[(-114, 49), (-101, 49), (-97, 49), (-97, 50.5), (-100, 52.5), (-104, 53.5), (-110, 54), (-115, 53.8),
          (-118, 55.5), (-119, 56.2), (-117, 52), (-114.5, 50)],
         [(-83, 42), (-79, 42.8), (-76, 44), (-73.5, 45), (-71, 46.5), (-72.5, 46.6), (-75, 45.6), (-78, 44.6), (-80, 45),
          (-81.7, 45.2), (-82.4, 43)]]
TRADE_ROUTES = [((-79.38, 43.65), (-74.0, 40.7)), ((-83.04, 42.31), (-87.6, 41.9)), ((-73.57, 45.50), (-71.06, 42.36)),
                ((-123.12, 49.28), (-122.3, 47.6)), ((-114.07, 51.05), (-104.99, 39.74)), ((-97.14, 49.90), (-93.27, 44.98)),
                ((-79.38, 43.65), (-83.05, 42.33)), ((-75.70, 45.42), (-74.0, 40.7))]
CPR = [('Montreal', -73.57, 45.50), ('Ottawa', -75.70, 45.42), ('North Bay', -79.46, 46.31), ('Sudbury', -80.99, 46.49),
       ('White River', -85.28, 48.59), ('Thunder Bay', -89.25, 48.38), ('Kenora', -94.49, 49.77), ('Winnipeg', -97.14, 49.90),
       ('Brandon', -99.95, 49.85), ('Regina', -104.61, 50.45), ('Medicine Hat', -110.68, 50.04), ('Calgary', -114.07, 51.05),
       ('Banff', -115.57, 51.18), ('Revelstoke', -118.20, 51.0), ('Kamloops', -120.33, 50.67), ('Vancouver', -123.12, 49.28)]

BEATS = [  # key, lines, header, stat, stat at (line index, offset), camera (lon, lat, zoom vs full)
    ('hook', ["This is Canada, at night.",
              "The second biggest country on Earth... and almost everyone lives in one thin strip."],
     'CANADA AT NIGHT', None, None, (-96, 57, 1.0)),
    ('band', ["Draw a line one hundred sixty kilometers from the US border...",
              "and about three out of four Canadians live inside it.",
              "Stretch it to three hundred kilometers, and it's about ninety percent!"],
     'THE BORDER STRIP', None, None, (-96, 53, 1.12)),
    ('north', ["Meanwhile, Nunavut covers a fifth of Canada... but only about forty thousand people live there."],
     'THE EMPTY NORTH', ('21% vs 0.1%', "Nunavut: share of land vs share of people"), (0, 1.6), (-90, 64, 1.1)),
    ('why', ["So why does everyone crowd the border? Four reasons."], 'BUT WHY?', None, None, (-96, 57, 1.0)),
    ('cold', ["Reason one: the cold. Northern winters hit minus forty, and roughly forty percent of Canada sits on permafrost... ground that never thaws."],
     '#1  THE COLD', ('-40°', 'northern winters, on frozen ground'), (0, 2.2), (-96, 59, 1.0)),
    ('shield', ["Reason two: the Canadian Shield. Ancient rock with thin soil, covering nearly half the country.",
                "Only about seven percent of Canada is farmland... and most of it hugs the south."],
     '#2  ROCK, NOT SOIL', ('~7%', 'of Canada is farmland'), (1, 0.6), (-92, 55, 1.05)),
    ('trade', ["Reason three: the United States. About three quarters of Canada's exports go south...",
               "so cities grew right next to their biggest customer."],
     '#3  THE BIG NEIGHBOUR', ('~75%', 'of exports go to the USA'), (0, 2.6), (-96, 47, 1.3)),
    ('rail', ["And reason four: history. Canada's first coast-to-coast railway, finished in eighteen eighty-five, ran close to the border...",
              "and towns grew up along the tracks."],
     '#4  THE RAILWAY', ('1885', 'Montreal to Vancouver by rail'), (0, 3.0), (-98, 50, 1.35)),
    ('fact', ["Here's a wild one. Toronto is further south than Seattle...", "and even Minneapolis!"],
     'WAIT, WHAT?', None, None, (-100, 47, 1.05)),
    ('outro', ["So Canada isn't empty. It's just squeezed along the border.",
               "Would you live up north? Tell me in the comments!"], 'SQUEEZED ALONG THE BORDER', None, None, (-96, 57, 1.0)),
]
GAP, LEAD, TAIL = 0.25, 0.35, 0.5

# ---------- projection ----------
def laea(lon, lat):
    l, p = np.radians(np.asarray(lon, float) - LON0), np.radians(np.asarray(lat, float))
    p0 = math.radians(LAT0)
    cosc = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l)
    k = np.sqrt(2 / np.maximum(1 + cosc, 1e-9))
    return RE * k * np.cos(p) * np.sin(l), RE * k * (math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l))

def proj_rings(rs):
    out = []
    for r in rs:
        x, y = laea(r[:, 0], r[:, 1]); out.append((x, y))
    return out

# ---------- data ----------
class Data:
    def __init__(self, data_dir):
        a1 = json.load(open(os.path.join(data_dir, 'admin1_50m.geojson')))
        c50 = json.load(open(os.path.join(data_dir, 'countries_50m.geojson')))
        c110 = json.load(open(os.path.join(data_dir, 'countries_110m.geojson')))
        self.prov = {}
        for f in a1['features']:
            if f['properties']['admin'] == 'Canada':
                self.prov[f['properties']['name']] = proj_rings([r for r in rings(f['geometry']) if len(r) >= 8])
        self.canada_ll = [r for f in c50['features'] if f['properties']['NAME'] == 'Canada' for r in rings(f['geometry']) if len(r) >= 8]
        self.canada = proj_rings(self.canada_ll)
        us_ll = [r for f in c50['features'] if f['properties']['NAME'] == 'United States of America' for r in rings(f['geometry'])]
        self.us = proj_rings([r for r in us_ll if len(r) >= 8 and r[:, 1].mean() > 20])
        self.others = proj_rings([r for f in c110['features'] if f['properties']['NAME'] not in ('Canada', 'United States of America')
                                  for r in rings(f['geometry']) if -180 < r[:, 0].mean() < 10 and r[:, 1].mean() > 10])
        self.dots, self.halos = self.make_dots(np.concatenate([vec(r[:, 0], r[:, 1]) for r in us_ll]))
        x, y = np.concatenate([r[0] for r in self.canada]), np.concatenate([r[1] for r in self.canada])
        self.bbox = (x.min(), x.max(), y.min(), y.max())
        self.full_s = min(1000 / (x.max() - x.min()), 900 / (y.max() - y.min()))

    def make_dots(self, U):
        s = cairo.ImageSurface(cairo.FORMAT_A8, 4, 4); cr = cairo.Context(s)
        for r in self.canada_ll:
            cr.move_to(r[0, 0], -r[0, 1]); [cr.line_to(a, -b) for a, b in r[1:]]; cr.close_path()
        rng = np.random.default_rng(11)
        pts = []  # lon, lat, weight (thousands of people), city index
        per = 14.0
        for ci, (name, pop, lat, lon) in enumerate(CITIES):
            n = max(2, int(pop / per)); sig = 0.05 + 0.012 * math.sqrt(pop)
            for _ in range(n):
                la, lo = lat + rng.normal(0, sig), lon + rng.normal(0, sig * 1.5)
                if cr.in_fill(lo, -la): pts.append((lo, la, pop / n, ci))
        rest = 41500 - sum(c[1] for c in CITIES)  # towns and countryside, spread around the cities
        w = np.array([c[1] for c in CITIES], float); w /= w.sum()
        k = 0
        while k < 900:
            ci = rng.choice(len(CITIES), p=w); _, pop, lat, lon = CITIES[ci]
            la, lo = lat + rng.normal(0, 1.4), lon + rng.normal(0, 2.4)
            if cr.in_fill(lo, -la): pts.append((lo, la, rest / 900, -1)); k += 1
        P = np.array(pts)
        V = vec(P[:, 0], P[:, 1])
        dist = np.array([6371 * np.arccos(np.clip(U @ v, -1, 1)).min() for v in V])
        x, y = laea(P[:, 0], P[:, 1])
        order = rng.permutation(len(P))
        dots = dict(x=x[order], y=y[order], w=P[order, 2], dist=dist[order], ci=P[order, 3].astype(int),
                    seed=rng.uniform(0, 1, len(P)))
        hx, hy = laea([c[3] for c in CITIES], [c[2] for c in CITIES])
        halos = [(hx[i], hy[i], c[1], c[0]) for i, c in enumerate(CITIES)]
        return dots, halos

D = None
TL = None

# ---------- timeline / camera ----------
def build(voice):
    t, beats, clips = 0.15, [], []
    for key, lines, head, stat, stat_at, cam in BEATS:
        b = dict(key=key, head=head, stat=stat, stat_at=stat_at, cam=cam, start=t, lines=[])
        cur = t + LEAD
        for i, s in enumerate(lines):
            a = voice.get(s); cur += GAP if i else 0
            clips.append((cur, a)); b['lines'].append((cur, cur + len(a) / SR, s)); cur += len(a) / SR
        t = cur + (TAIL if key != 'outro' else 1.8)
        b['end'] = t; beats.append(b)
    return dict(beats=beats, clips=clips, dur=t, by={b['key']: b for b in beats})

def beat_at(T, t):
    for b in T['beats']:
        if b['start'] <= t < b['end']: return b
    return T['beats'][-1]

def cam_of(c):
    x, y = laea(c[0], c[1]); return float(x), float(y), D.full_s * c[2]

def camera(T, t):
    prev = cam_of(T['beats'][0]['cam'])
    cur = prev
    for b in T['beats']:
        if t < b['start']: break
        nxt = cam_of(b['cam'])
        k = ease_io(prog(t, b['start'], b['start'] + 1.2))
        cur = (lerp(prev[0], nxt[0], k), lerp(prev[1], nxt[1], k), math.exp(lerp(math.log(prev[2]), math.log(nxt[2]), k)))
        prev = nxt
    # slow push-in for life
    return cur[0], cur[1], cur[2] * (1 + 0.012 * math.sin(t * 0.4))

def sx(cam, x): return W / 2 + (x - cam[0]) * cam[2]
def sy(cam, y): return MAPY - (y - cam[1]) * cam[2]

def path(cr, cam, rs, close=True):
    for x, y in rs:
        X, Y = sx(cam, x), sy(cam, y)
        cr.move_to(X[0], Y[0])
        for a, b in zip(X[1:], Y[1:]): cr.line_to(a, b)
        if close: cr.close_path()

def ll(cam, lon, lat):
    x, y = laea(lon, lat); return sx(cam, x), sy(cam, y)

def poly_ll(cr, cam, pts):
    X, Y = ll(cam, [p[0] for p in pts], [p[1] for p in pts])
    cr.move_to(X[0], Y[0]); [cr.line_to(a, b) for a, b in zip(X[1:], Y[1:])]; cr.close_path()

# ---------- drawing ----------
def draw_base(cr, T, t, cam):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgba(0, *NIGHT0); g.add_color_stop_rgba(1, *NIGHT1)
    cr.set_source(g); cr.paint()
    rng = np.random.default_rng(3)
    for _ in range(90):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.5, 1.8)
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi)
        cr.set_source_rgba(1, 1, 1, 0.25 + 0.25 * abs(math.sin(t * rng.uniform(.3, 1.5) + rng.uniform(0, 6)))); cr.fill()
    cr.new_path(); path(cr, cam, D.others); cr.set_source_rgba(*US_FILL[:3], 0.8); cr.fill()
    cr.new_path(); path(cr, cam, D.us); cr.set_source_rgba(*US_FILL[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*US_EDGE[:3], 1); cr.set_line_width(1.2); cr.stroke()
    cr.new_path(); path(cr, cam, D.canada); cr.set_source_rgba(*CAN_FILL[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*CAN_EDGE[:3], 1); cr.set_line_width(1.5); cr.stroke()
    cr.new_path()
    for rs in D.prov.values(): path(cr, cam, rs)
    cr.set_source_rgba(*PROV_EDGE[:3], 1); cr.set_line_width(1); cr.stroke()
    a = 0.6
    X, Y = ll(cam, -100, 41); font(cr, 30); text(cr, 'USA', X, Y, US_EDGE, a * 1.5, sp=10)

def clip_canada(cr, cam):
    cr.new_path(); path(cr, cam, D.canada); cr.clip()

def band_km(T, t):
    b = T['by']['band']
    l0, l2 = b['lines'][0], b['lines'][2]
    k1 = ease_io(prog(t, l0[0] + 0.4, l0[1]))
    k2 = ease_io(prog(t, l2[0] + 0.8, l2[0] + 2.4))
    off = 1 - ease_io(prog(t, T['by']['north']['start'], T['by']['north']['start'] + 0.6))
    on_again = ease_io(prog(t, T['by']['outro']['start'], T['by']['outro']['start'] + 1.0))
    return (160 * k1 + 140 * k2) * off + 300 * on_again, max(off * min(1, k1 * 3), on_again)

def draw_band(cr, T, t, cam):
    km, a = band_km(T, t)
    if km <= 1 or a <= 0: return
    cr.save(); clip_canada(cr, cam)
    cr.new_path(); path(cr, cam, D.us)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.set_line_width(2 * km * cam[2]); cr.set_source_rgba(*GOLD[:3], 0.26 * a); cr.stroke_preserve()
    cr.set_line_width(4); cr.set_source_rgba(*RED[:3], 0.9 * a); cr.stroke()
    cr.restore()

def lights_on(T, t):
    """Fraction of lights on (hook animation)."""
    return ease_out(prog(t, 0.2, 2.6))

def draw_lights(cr, T, t, cam):
    d = D.dots; on = lights_on(T, t)
    km, ba = band_km(T, t)
    X, Y = sx(cam, d['x']), sy(cam, d['y'])
    cr.save(); cr.set_operator(cairo.OPERATOR_ADD)
    # city halos
    for (hx, hy, pop, name) in D.halos:
        r = (3 + 0.42 * math.sqrt(pop)) * cam[2] / D.full_s
        X0, Y0 = sx(cam, hx), sy(cam, hy)
        g = cairo.RadialGradient(X0, Y0, 0, X0, Y0, r * 2.2)
        flick = 0.85 + 0.15 * math.sin(t * 2 + pop)
        g.add_color_stop_rgba(0, *LIGHT[:3], 0.32 * on * flick); g.add_color_stop_rgba(1, *LIGHT[:3], 0)
        cr.set_source(g); cr.arc(X0, Y0, r * 2.2, 0, 2 * math.pi); cr.fill()
    inside = d['dist'] <= km
    rad = 1.6 * max(1.0, (cam[2] / D.full_s) ** 0.5)
    for i in range(len(X)):
        if d['seed'][i] > on: continue
        if inside[i] and ba > 0: c, al = GOLD, 0.95
        else: c, al = LIGHT, 0.75 * (1 - 0.6 * ba) if km > 1 else 0.75
        cr.new_path(); cr.arc(X[i], Y[i], rad, 0, 2 * math.pi); cr.set_source_rgba(*c[:3], al); cr.fill()
    cr.restore()

def draw_counter(cr, T, t):
    b = T['by']['band']
    if not (b['start'] <= t < b['end']): return
    l1, l2 = b['lines'][1], b['lines'][2]
    a = ease_out(prog(t, l1[0], l1[0] + 0.4)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    v = lerp(0, 75, ease_out(prog(t, l1[0], l1[0] + 1.2)))
    v = lerp(v, 90, ease_out(prog(t, l2[0] + 1.2, l2[0] + 2.6)))
    km = 160 if t < l2[0] + 1.0 else 300
    k = ease_back(prog(t, l1[0], l1[0] + 0.45))
    cr.save(); cr.translate(540, 1345); cr.scale(k, k)
    rrect(cr, -440, -110, 880, 210, 36); cr.set_source_rgba(0.01, 0.02, 0.06, 0.85 * a); cr.fill_preserve()
    cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
    font(cr, 110); text(cr, f'{v:.0f}%', 0, 22, GOLD, a, sp=2)
    font(cr, 36, bold=False); text(cr, f'of Canadians within {km} km of the US border', 0, 75, WHITE, a)
    cr.restore()

def draw_north(cr, T, t, cam):
    b = T['by']['north']
    a = ease_out(prog(t, b['start'] + 0.6, b['start'] + 1.2)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    cr.new_path(); path(cr, cam, D.prov['Nunavut'])
    cr.set_source_rgba(*ICE[:3], 0.22 * a); cr.fill_preserve()
    cr.set_source_rgba(*ICE[:3], 0.9 * a); cr.set_line_width(2.5); cr.stroke()
    X, Y = ll(cam, -92, 66); font(cr, 48); text(cr, 'NUNAVUT', X, Y, WHITE, a, sp=4, shadow=True)
    font(cr, 30, bold=False); text(cr, '~40,000 people', X, Y + 46, ICE, a)

def draw_cold(cr, T, t, cam):
    b = T['by']['cold']
    a = ease_out(prog(t, b['start'] + 0.4, b['start'] + 0.9)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    wipe = ease_io(prog(t, b['lines'][0][0] + 2.5, b['lines'][0][0] + 5.0))
    cr.save(); clip_canada(cr, cam)
    cr.rectangle(0, 0, W, 300 + 900 * wipe); cr.clip()
    cr.new_path(); poly_ll(cr, cam, PERMAFROST)
    g = cairo.LinearGradient(0, 300, 0, 1100)
    g.add_color_stop_rgba(0, *ICE[:3], 0.55 * a); g.add_color_stop_rgba(1, *ICE[:3], 0.25 * a)
    cr.set_source(g); cr.fill()
    rng = np.random.default_rng(1)  # drifting snow
    for _ in range(140):
        x = (rng.uniform(0, W) + 20 * math.sin(t + rng.uniform(0, 6))) % W
        y = (rng.uniform(0, H) + t * rng.uniform(30, 80)) % H
        cr.new_path(); cr.arc(x, y, rng.uniform(1, 3), 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.7 * a); cr.fill()
    cr.restore()
    k = ease_out(prog(t, b['lines'][0][0] + 3.0, b['lines'][0][0] + 3.5))
    X, Y = ll(cam, -100, 66); font(cr, 40); text(cr, 'PERMAFROST', X, Y, WHITE, a * k, sp=4, shadow=True)

def hatch(cr, spacing=14):
    cr.save(); cr.clip()
    for x in range(-H, W + H, spacing): cr.move_to(x, 0); cr.line_to(x + H, H)
    cr.restore()

def draw_shield(cr, T, t, cam):
    b = T['by']['shield']
    a = ease_out(prog(t, b['start'] + 0.6, b['start'] + 1.2)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    cr.save(); clip_canada(cr, cam)
    cr.new_path(); poly_ll(cr, cam, SHIELD); cr.set_source_rgba(*ROCK[:3], 0.3 * a); cr.fill_preserve()
    cr.set_source_rgba(*ROCK[:3], 0.9 * a); cr.set_line_width(2); cr.stroke_preserve()
    hatch(cr); cr.set_source_rgba(*ROCK[:3], 0.35 * a); cr.set_line_width(2); cr.stroke()
    fk = ease_out(prog(t, b['lines'][1][0] + 0.3, b['lines'][1][0] + 1.0))
    if fk > 0:
        cr.new_path()
        for fp in FARMS: poly_ll(cr, cam, fp)
        cr.set_source_rgba(*FARM[:3], 0.55 * a * fk); cr.fill_preserve()
        cr.set_source_rgba(*FARM[:3], a * fk); cr.set_line_width(2.5); cr.stroke()
    cr.restore()
    X, Y = ll(cam, -88, 57); font(cr, 38); text(cr, 'CANADIAN SHIELD', X, Y, WHITE, a, sp=3, shadow=True)
    if fk > 0:
        X, Y = ll(cam, -108, 49.5); font(cr, 30); text(cr, 'FARMLAND', X, Y + 40, FARM, a * fk, sp=3, shadow=True)

def bezier_pt(p0, p1, c, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1])

def draw_trade(cr, T, t, cam):
    b = T['by']['trade']
    a = ease_out(prog(t, b['start'] + 0.8, b['start'] + 1.3)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    for i, (src, dst) in enumerate(TRADE_ROUTES):
        p0 = [float(v) for v in ll(cam, *src)]; p1 = [float(v) for v in ll(cam, *dst)]
        c = ((p0[0] + p1[0]) / 2 + (p1[1] - p0[1]) * 0.25, (p0[1] + p1[1]) / 2 - (p1[0] - p0[0]) * 0.25)
        cr.new_path(); cr.move_to(*p0); cr.curve_to(*[lerp(p0[j], c[j], 0.66) for j in (0, 1)], *[lerp(p1[j], c[j], 0.66) for j in (0, 1)], *p1)
        cr.set_source_rgba(*TRADE[:3], 0.35 * a); cr.set_line_width(3); cr.stroke()
        for k in range(4):
            u = ((t * 0.5 + i * 0.13 + k / 4) % 1.0)
            x, y = bezier_pt(p0, p1, c, u)
            cr.new_path(); cr.arc(x, y, 6, 0, 2 * math.pi); cr.set_source_rgba(*TRADE[:3], a * math.sin(math.pi * u)); cr.fill()
        cr.new_path(); cr.arc(p1[0], p1[1], 7, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.8 * a); cr.fill()
    font(cr, 26)
    for name, lon, lat in (('NEW YORK', -74.0, 40.7), ('CHICAGO', -87.6, 41.9), ('DENVER', -104.99, 39.74)):
        X, Y = ll(cam, lon, lat); text(cr, name, X, Y + 34, TRADE, a, sp=2)

def draw_rail(cr, T, t, cam):
    b = T['by']['rail']
    a = ease_out(prog(t, b['start'] + 0.6, b['start'] + 1.0)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    k = ease_io(prog(t, b['lines'][0][0] + 1.0, b['lines'][1][1]))
    pts = np.array([[float(v) for v in ll(cam, lon, lat)] for _, lon, lat in CPR])
    seg = np.hypot(*np.diff(pts, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    n = min(int(np.searchsorted(cum, k)), len(pts) - 1)
    f = 0 if n == 0 else (k - cum[n - 1]) / max(1e-9, cum[n] - cum[n - 1])
    hx, hy = lerp(pts[max(n - 1, 0)][0], pts[n][0], f), lerp(pts[max(n - 1, 0)][1], pts[n][1], f)
    cr.new_path(); cr.move_to(*pts[0])
    for p in pts[1:n]: cr.line_to(*p)
    cr.line_to(hx, hy)
    for lw, al in ((14, 0.2), (6, 0.9)):
        cr.set_source_rgba(*RAIL[:3], al * a); cr.set_line_width(lw); cr.stroke_preserve()
    cr.set_dash([2, 10]); cr.set_source_rgba(1, 1, 1, 0.8 * a); cr.set_line_width(12); cr.stroke(); cr.set_dash([])
    font(cr, 22)
    for i, (name, lon, lat) in enumerate(CPR):
        if cum[i] <= k:
            pk = ease_back(prog(t, b['lines'][0][0] + 1.0 + cum[i] * (b['lines'][1][1] - b['lines'][0][0] - 1.0), 0) + 0.0) if False else 1
            cr.new_path(); cr.arc(pts[i][0], pts[i][1], 7, 0, 2 * math.pi); cr.set_source_rgba(*RAIL[:3], a); cr.fill()
            if i % 3 == 0 or i == len(CPR) - 1:
                text(cr, name.upper(), pts[i][0], pts[i][1] - 18, WHITE, a, sp=1, shadow=True)
    if k < 1:  # the train
        cr.new_path(); cr.arc(hx, hy, 12, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, a); cr.fill()
        g = cairo.RadialGradient(hx, hy, 0, hx, hy, 50)
        g.add_color_stop_rgba(0, *RAIL[:3], 0.6 * a); g.add_color_stop_rgba(1, *RAIL[:3], 0)
        cr.set_source(g); cr.arc(hx, hy, 50, 0, 2 * math.pi); cr.fill()

def draw_fact(cr, T, t, cam):
    b = T['by']['fact']
    a = ease_out(prog(t, b['start'] + 0.8, b['start'] + 1.3)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    lons = np.linspace(-135, -55, 120)
    k = ease_io(prog(t, b['start'] + 1.0, b['start'] + 2.2))
    X, Y = ll(cam, lons, np.full_like(lons, 43.65))
    n = max(2, int(len(X) * k))
    cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:n], Y[1:n])]
    cr.set_dash([14, 10]); cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke(); cr.set_dash([])
    l0, l1 = b['lines'][0], b['lines'][1]
    for name, lon, lat, t0, col, side in (('TORONTO 43.7°N', -79.38, 43.65, b['start'] + 0.8, GOLD, 'b'),
                                         ('SEATTLE 47.6°N', -122.33, 47.61, l0[1] - 1.2, WHITE, 't'),
                                         ('MINNEAPOLIS 45.0°N', -93.27, 44.98, l1[0], WHITE, 't')):
        pk = ease_back(prog(t, t0, t0 + 0.4))
        if pk <= 0.01: continue
        x, y = ll(cam, lon, lat)
        cr.new_path(); cr.arc(x, y, 11 * pk, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], a); cr.fill()
        cr.new_path(); cr.arc(x, y, 11 + 40 * prog(t, t0, t0 + 1), 0, 2 * math.pi)
        cr.set_source_rgba(*col[:3], a * (1 - prog(t, t0, t0 + 1))); cr.set_line_width(3); cr.stroke()
        font(cr, 32)
        text(cr, name, x, y + (52 if side == 'b' else -28), col, a * clamp(pk), sp=1, shadow=True)
    font(cr, 30); X0, Y0 = ll(cam, -108, 43.65); text(cr, 'SAME LATITUDE AS TORONTO', X0, Y0 + 44, GOLD, a * k, sp=2)

def draw_header(cr, b, t):
    if not b['head']: return
    a = ease_out(prog(t, b['start'], b['start'] + 0.4)) * (1 - ease_io(prog(t, b['end'] - 0.25, b['end'])))
    k = ease_back(prog(t, b['start'], b['start'] + 0.45))
    cr.save(); cr.translate(540, 250); cr.scale(k, k)
    fit_font(cr, b['head'], 74, 980, 3); text(cr, b['head'], 0, 25, WHITE, a, sp=3, shadow=True)
    cr.restore()
    cr.set_source_rgba(*RED[:3], a); w = 160 * ease_out(prog(t, b['start'] + 0.2, b['start'] + 0.7))
    cr.rectangle(540 - w, 300, 2 * w, 8); cr.fill()

def stat_time(b): return b['lines'][b['stat_at'][0]][0] + b['stat_at'][1]

def draw_stat(cr, b, t):
    if not b['stat']: return
    t0 = stat_time(b)
    a = ease_out(prog(t, t0, t0 + 0.35)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    big, small = b['stat']; k = ease_back(prog(t, t0, t0 + 0.45))
    cr.save(); cr.translate(540, 1345); cr.scale(k, k)
    rrect(cr, -440, -110, 880, 210, 36); cr.set_source_rgba(0.01, 0.02, 0.06, 0.85 * a); cr.fill_preserve()
    cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
    fit_font(cr, big, 100, 800, 2); text(cr, big, 0, 14, GOLD, a, sp=2)
    fit_font(cr, small, 36, 820, 1, bold=False); text(cr, small, 0, 72, WHITE, a)
    cr.restore()

HOT = ('CANADA', 'BORDER', 'NUNAVUT', 'COLD', 'SHIELD', 'FARMLAND', 'STATES', 'RAILWAY', 'TORONTO', 'SEATTLE',
       'MINNEAPOLIS', 'REASON', 'FROZEN', 'PERMAFROST', 'STRIP')

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
                    rrect(cr, -w / 2 - 28, -70, w + 56, 100, 22); cr.set_source_rgba(0, 0, 0, 0.6); cr.fill()
                    hl = any(ch.isdigit() for ch in c) or any(x in up for x in HOT)
                    text(cr, up, 0, 0, GOLD if hl else WHITE, 1, sp=1)
                    cr.restore(); return

def draw_hook_extra(cr, T, t, cam):
    b = T['by']['hook']
    if t > b['end']: return
    l1 = b['lines'][1]
    k = ease_out(prog(t, l1[1] - 1.6, l1[1] - 1.0))
    if k <= 0: return
    a = k * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    cr.save(); clip_canada(cr, cam); cr.new_path(); path(cr, cam, D.us)
    cr.set_line_width(2 * 160 * cam[2]); cr.set_source_rgba(*GOLD[:3], 0.12 * a); cr.stroke()
    cr.restore()
    X, Y = ll(cam, -84, 52.5)
    font(cr, 36); text(cr, 'EVERYONE IS HERE', X, Y, GOLD, a, sp=3, shadow=True)
    cr.new_path(); cr.move_to(X, Y + 14); cr.line_to(X - 20, Y + 90); cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
    cr.new_path(); cr.move_to(X - 34, Y + 74); cr.line_to(X - 20, Y + 96); cr.line_to(X - 4, Y + 76); cr.stroke()

def draw_outro(cr, b, t):
    a = ease_out(prog(t, b['start'] + 0.3, b['start'] + 0.8))
    if a <= 0: return
    k2 = ease_back(prog(t, b['lines'][1][0], b['lines'][1][0] + 0.4))
    if k2 > 0.01:
        pill(cr, 'WOULD YOU LIVE UP NORTH?  COMMENT', 540, 1360, 38, RED, WHITE, 1, scale=k2 * (1 + 0.03 * math.sin(t * 6)))

def render_frame(cr, t):
    T = TL
    cam = camera(T, t)
    draw_base(cr, T, t, cam)
    draw_cold(cr, T, t, cam)
    draw_shield(cr, T, t, cam)
    draw_north(cr, T, t, cam)
    draw_band(cr, T, t, cam)
    draw_lights(cr, T, t, cam)
    draw_trade(cr, T, t, cam)
    draw_rail(cr, T, t, cam)
    draw_fact(cr, T, t, cam)
    draw_hook_extra(cr, T, t, cam)
    b = beat_at(T, t)
    draw_header(cr, b, t)
    draw_counter(cr, T, t)
    draw_stat(cr, b, t)
    if b['key'] == 'outro': draw_outro(cr, b, t)
    draw_captions(cr, T, t)
    f = prog(t, T['dur'] - 0.4, T['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- audio ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(8)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 112
    chords = [[52, 55, 59], [48, 52, 55], [55, 59, 62], [50, 54, 57]]  # Em C G D
    for bi in range(int(dur / beat)):
        t0 = bi * beat; ch = chords[(bi // 4) % 4]; L = np.arange(int(0.3 * SR)) / SR
        if t0 > 2.6: put(music, t0, 0.4 * np.sin(2 * np.pi * np.cumsum(48 + 80 * np.exp(-L * 35)) / SR) * np.exp(-L * 10))
        if t0 > 2.6:
            M = np.arange(int(0.05 * SR)); put(music, t0 + beat / 2, 0.04 * np.diff(rng.standard_normal(len(M) + 1)) * np.exp(-M / SR * 70))
        mt = np.arange(int(beat * SR)) / SR; put(music, t0, 0.1 * np.tanh(3 * np.sin(2 * np.pi * note(ch[0] - 24) * mt)) * np.exp(-mt * 3))
        for s in range(2):
            m = ch[(bi * 2 + s) % 3] + 24; pt = np.arange(int(0.4 * SR)) / SR  # bell-like arpeggio
            put(music, t0 + s * beat / 2, 0.035 * (np.sin(2 * np.pi * note(m) * pt) + 0.4 * np.sin(2 * np.pi * 2.76 * note(m) * pt) * np.exp(-pt * 20)) * np.exp(-pt * 7))
    pad = np.zeros(n)
    for ci in range(int(dur / (beat * 4)) + 1):
        ch = chords[ci % 4]; L = np.arange(int(beat * 4.5 * SR)) / SR
        put(pad, ci * beat * 4, sum(0.03 * np.sin(2 * np.pi * note(m) * L) for m in ch) * np.minimum(1, L / 0.5) * np.exp(-L * 0.35))
    music = np.tanh((music + pad) * 1.2) * 0.5
    fx = np.zeros(n)
    for b in T['beats'][1:]:
        nz = rng.standard_normal(int(0.9 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2
        put(fx, b['start'] - 0.2, 0.15 * np.convolve(nz, np.ones(40) / 40, 'same') * env)
    def chime(t0, amp=0.12):
        L = np.arange(int(0.8 * SR)) / SR
        put(fx, t0, amp * sum(np.sin(2 * np.pi * f * L) * np.exp(-L * d) for f, d in ((1318.5, 6), (1975.5, 7))))
    for b in T['beats']:
        if b['stat']: chime(stat_time(b))
    bb = T['by']['band']; chime(bb['lines'][1][0]); chime(bb['lines'][2][0] + 1.2)
    L = np.arange(int(1.3 * SR)) / SR
    put(fx, T['by']['hook']['lines'][1][1] - 1.6, 0.5 * np.sin(2 * np.pi * np.cumsum(40 + 90 * np.exp(-L * 12)) / SR) * np.exp(-L * 3.5))
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
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
                           '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait()
    return out

def main():
    global D, TL
    data_dir, vdir, out = sys.argv[1:4]
    voice = Voice(vdir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache'))
    TL = build(voice); D = Data(data_dir)
    print(f"duration {TL['dur']:.1f}s, {len(D.dots['x'])} light dots")
    for b in TL['beats']: print(f"  {b['key']:7s} {b['start']:6.2f}-{b['end']:6.2f}")
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
