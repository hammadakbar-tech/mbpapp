"""'Why Is Australia So Empty?' (9:16): wider than the Moon, as big as the mainland USA, fewer people than Texas; the coastal
strip, the dry outback, history and today. Word-synced map video (engine from china.py, layout from cpop.py).
Usage: python3 aus.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
from china import R, ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON, PARCH, laea, S, L, path_xy
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

R.LON0, R.LAT0 = 134.0, -26.0
R.MAPY = 1000
OCHRE, SAND, GREEN, BLUE, TEAL = hexc('#D9822B'), hexc('#E8C07A'), hexc('#4CB86A'), hexc('#4FA3D9'), hexc('#2EC4B6')
C.SAY = {None: {}}
C.HOT = ('australia', 'australians', 'moon', 'texas', 'united', 'states', 'coast', 'desert', 'driest', 'outback', 'sydney', 'melbourne',
         'perth', 'bali', 'sheep', 'territory', 'france', 'spain', 'rain', 'water', 'cities', 'empty', 'nations', '1788')
BEATS = [
    ('h1', "Australia is wider than the Moon.", None, None, None, None, None),
    ('h2', "It's almost as big as the mainland United States...", None, None, None, None, None),
    ('h3', "but it has fewer people than Texas. And almost all of them live right here.", None, None, None, None, None),
    ('title', "So why is Australia so empty?", None, None, None, None, None),
    ('nums', "Australia has about twenty-seven million people. Texas has over thirty million. The whole United States, three hundred and forty million.",
     None, None, None, ('I', 'THE NUMBERS'), None),
    ('coast', "About eighty-five percent of Australians live within fifty kilometres of the coast. And two in three live in just eight capital cities.", None, None, None, None, None),
    ('dry', "The reason is water. Australia is the driest inhabited continent. About seventy percent of it is arid or semi-arid.",
     None, None, None, ('II', 'THE OUTBACK'), None),
    ('heat', "In the centre, summer days can pass forty-five degrees, and the record is fifty point seven.", None, None, None, None, None),
    ('range', "The Great Dividing Range catches the rain along the east coast. Behind it, the land dries out fast.", None, None, None, None, None),
    ('nt', "The Northern Territory is bigger than France and Spain combined, with only about a quarter of a million people.", None, None, None, None, None),
    ('first', "First Nations peoples have lived across this land for at least fifty thousand years, even in the driest deserts.",
     None, None, None, ('III', 'HISTORY'), None),
    ('fleet', "In 1788, British ships arrived at Sydney Cove. New colonies followed by sea: Hobart, Brisbane, Perth, Melbourne, Adelaide. All on the coast.",
     None, None, None, None, None),
    ('sheep', "Inland, the land became giant sheep and cattle stations. Even today, Australia has about three sheep for every person.", None, None, None, None, None),
    ('cities', "Today, Sydney and Melbourne each have around five million people. Together, that's nearly forty percent of the country.",
     None, None, None, ('IV', 'TODAY'), None),
    ('perth', "And Perth is one of the most isolated big cities on Earth. It's closer to Bali than to Sydney.", None, None, None, None, None),
    ('cta', "Would you live in the outback? Tell us in the comments, and follow for more.", None, None, None, None, None),
]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2', 'h3')
C.TAIL_OVERRIDE = {'h1': 0.9, 'h2': 0.5, 'h3': 0.4}
bt, w, win = C.bt, C.w, C.win
G = None
FULL = (134, -27, 0.235)
CAMS = {'fleet': (142, -32, 0.33), 'perth': (128, -21, 0.17), 'cities': (145, -35, 0.42)}
CITIES = [('Sydney', 151.21, -33.87, 5450), ('Melbourne', 144.96, -37.81, 5210), ('Brisbane', 153.03, -27.47, 2710), ('Perth', 115.86, -31.95, 2310),
          ('Adelaide', 138.6, -34.93, 1450), ('Gold Coast', 153.4, -28.0, 720), ('Newcastle', 151.78, -32.93, 520), ('Canberra', 149.13, -35.28, 470),
          ('Sunshine Coast', 153.07, -26.65, 400), ('Wollongong', 150.89, -34.42, 310), ('Geelong', 144.36, -38.15, 300), ('Hobart', 147.33, -42.88, 250),
          ('Townsville', 146.82, -19.26, 185), ('Cairns', 145.77, -16.92, 160), ('Darwin', 130.84, -12.46, 150), ('Toowoomba', 151.95, -27.56, 145),
          ('Ballarat', 143.85, -37.56, 115), ('Bendigo', 144.28, -36.76, 105), ('Launceston', 147.14, -41.43, 90), ('Mackay', 149.19, -21.14, 85),
          ('Rockhampton', 150.51, -23.38, 80), ('Bunbury', 115.64, -33.33, 75), ('Kalgoorlie', 121.47, -30.75, 30), ('Alice Springs', 133.88, -23.7, 25),
          ('Mount Isa', 139.49, -20.73, 18), ('Broome', 122.24, -17.96, 15)]
ARID = [(113.8, -26), (116, -21.5), (121, -19.3), (126, -18.6), (130, -17.6), (135, -18.2), (138, -19.8), (141, -21.5), (144.8, -23.5),
        (146, -27.5), (144.5, -31.5), (141, -33.5), (138, -31.8), (134, -31.6), (129, -31.4), (124, -32.4), (120, -31), (116.5, -28.8)]
RANGE = [(145.3, -15.5), (145.6, -18.5), (146.5, -21.5), (148.3, -24.5), (150.6, -27.5), (151.6, -30.2), (150.1, -33.4), (149, -36.2), (146.6, -37.3), (143.8, -37.6)]
COLONIES = [('SYDNEY', 151.21, -33.87, '1788', 'Sydney'), ('HOBART', 147.33, -42.88, '1804', 'Hobart'), ('BRISBANE', 153.03, -27.47, '1824', 'Brisbane'),
            ('PERTH', 115.86, -31.95, '1829', 'Perth'), ('MELBOURNE', 144.96, -37.81, '1835', 'Melbourne'), ('ADELAIDE', 138.6, -34.93, '1836', 'Adelaide')]
DESERTS = [('GREAT SANDY', 124.5, -20.5), ('GIBSON', 124, -24.3), ('GREAT VICTORIA', 128, -28.5), ('SIMPSON', 137, -25), ('TANAMI', 130.5, -20)]
BALI = (115.19, -8.65)

class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        def pr(geom, keep=lambda r: True): return [laea(r[:, 0], r[:, 1]) for r in rings(geom) if len(r) > 3 and keep(r)]
        self.aus = pr(cf['Australia']['geometry'])
        self.main = sorted(self.aus, key=lambda r: -len(r[0]))[:1]
        raw = lambda geom, keep=lambda r: True: [r for r in rings(geom) if len(r) > 3 and keep(r)]
        self.usa48 = raw(cf['United States of America']['geometry'], lambda r: -126 < r[:, 0].mean() < -66 and 24 < r[:, 1].mean() < 50)
        self.fr = raw(cf['France']['geometry'], lambda r: -6 < r[:, 0].mean() < 10 and r[:, 1].mean() > 41)
        self.es = raw(cf['Spain']['geometry'], lambda r: r[:, 0].mean() > -10 and r[:, 1].mean() > 35)
        self.land = [laea(r[:, 0], r[:, 1]) for f in json.load(open(os.path.join(d, 'ne_50m_land.geojson')))['features']
                     for r in rings(f['geometry']) if len(r) > 3 and 90 < r[:, 0].mean() < 180 and -50 < r[:, 1].mean() < 15]
        self.prov = {}
        for f in json.load(open(os.path.join(d, 'admin1_50m.geojson')))['features']:
            p = f['properties']
            if p.get('admin') == 'Australia': self.prov[p['name']] = pr(f['geometry'])
            if p.get('admin') == 'United States of America' and p['name'] == 'Texas': self.texas = [r for r in rings(f['geometry']) if len(r) > 3]

def camera(t):
    cur = FULL
    for k, cam in CAMS.items():
        b = bt(k); a = ease_io(prog(t, b['start'], b['start'] + 1.2)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'] + 1.0)))
        if a > 0: cur = (lerp(cur[0], cam[0], a), lerp(cur[1], cam[1], a), math.exp(lerp(math.log(cur[2]), math.log(cam[2]), a)))
    x, y = laea(cur[0], cur[1]); return float(x), float(y), cur[2] * (1 + 0.015 * math.sin(t * 0.4))

def poly(cr, cam, pts, col, a, edge=None, lw=3, dash=None):
    if a <= 0: return
    x, y = laea(np.array([p[0] for p in pts]), np.array([p[1] for p in pts]))
    cr.new_path(); path_xy(cr, cam, [(x, y)]); cr.set_source_rgba(*col[:3], a); cr.fill_preserve()
    if edge:
        if dash: cr.set_dash(dash)
        cr.set_source_rgba(*edge[:3], min(1, a * 2)); cr.set_line_width(lw); cr.stroke(); cr.set_dash([])
    cr.new_path()

def label(cr, cam, lon, lat, txt, size, col, a, t0, t):
    if t < t0 or a <= 0: return
    k = pop_k(t, t0); x, y = L(cam, lon, lat); cr.save(); cr.translate(x, y); cr.scale(k, k)
    ptext(cr, txt, 0, 0, size, col, a, fam='Poppins ExtraBold', sw=7); cr.restore()

def coast_band(cr, cam, a, km=50, col=GOLD):
    if a <= 0: return
    cr.save(); cr.new_path(); path_xy(cr, cam, G.aus); cr.clip(); cr.new_path(); path_xy(cr, cam, G.aus)
    cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.set_source_rgba(*col[:3], 0.9 * a); cr.set_line_width(max(6, 2 * km * cam[2])); cr.stroke(); cr.restore()

def dots(cr, cam, a, t, t0):
    if a <= 0 or t < t0: return
    for i, (n, lon, lat, pop) in enumerate(CITIES):
        k = pop_k(t, t0 + i * 0.03); x, y = L(cam, lon, lat); r = (3 + math.sqrt(pop) * 0.6) * k * (cam[2] / 0.235) ** 0.5
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 0.92, 0.35, 0.9 * a); cr.fill_preserve()
        cr.set_source_rgba(0, 0, 0, 0.5 * a); cr.set_line_width(2); cr.stroke()

def moved(shapes, src, dst, k=1.0):
    """Shapes (lon/lat rings) at true size: equal-area projected around their own centre `src`, then placed at `dst`."""
    lon0, lat0 = R.LON0, R.LAT0; R.LON0, R.LAT0 = src
    loc = [laea(r[:, 0], r[:, 1]) for r in shapes]
    R.LON0, R.LAT0 = lon0, lat0
    dx, dy = laea(*dst)
    return [(x + float(dx), y + float(dy)) for x, y in loc]

def draw_base(cr, cam, t):
    cr.set_source_rgb(0.03, 0.07, 0.13); cr.paint()
    g = cairo.RadialGradient(W / 2, R.MAPY, 100, W / 2, R.MAPY, 1300); g.add_color_stop_rgba(0, 0.08, 0.22, 0.36, 1); g.add_color_stop_rgba(1, 0.02, 0.06, 0.12, 1)
    cr.set_source(g); cr.paint()
    cr.new_path(); path_xy(cr, cam, G.land); cr.set_source_rgb(0.22, 0.22, 0.22); cr.fill()
    ka = ease_out(prog(t, 0.0, 0.3))
    cr.new_path(); path_xy(cr, cam, G.aus); cr.set_source_rgba(*OCHRE[:3], 0.92 * ka); cr.fill()
    cr.new_path(); path_xy(cr, cam, [r for rs in G.prov.values() for r in rs]); cr.set_source_rgba(1, 1, 1, 0.35 * ka); cr.set_line_width(1.3); cr.stroke()

def draw_story(cr, cam, t):
    # ----- hook -----
    a = win('h1', t=t)
    if a > 0:  # the Moon, to scale (3,474 km), rolls across Australia (~4,000 km wide)
        tm = w('h1', 'Moon') - 0.3; k = ease_out(prog(t, tm, tm + 0.6))
        x, y = L(cam, 134, -25.5); r = 3474 / 2 * cam[2]
        cx = lerp(W + r, x, k)
        cr.new_path(); cr.arc(cx, y, r, 0, 2 * math.pi)
        g = cairo.RadialGradient(cx - r * 0.3, y - r * 0.3, r * 0.1, cx, y, r); g.add_color_stop_rgba(0, 0.95, 0.95, 0.92, 0.85); g.add_color_stop_rgba(1, 0.6, 0.6, 0.62, 0.85)
        cr.set_source(g); cr.fill()
        for ox, oy, cr_ in ((-0.3, -0.2, 0.16), (0.3, 0.15, 0.12), (-0.05, 0.45, 0.1), (0.35, -0.45, 0.08)):
            cr.new_path(); cr.arc(cx + ox * r, y + oy * r, cr_ * r, 0, 2 * math.pi); cr.set_source_rgba(0.45, 0.45, 0.48, 0.6); cr.fill()
        if k >= 1:
            (x0, _), (x1, _) = L(cam, 113.2, -25.5), L(cam, 153.6, -25.5); yy = y + r + 60
            cr.new_path(); cr.move_to(x0, yy); cr.line_to(x1, yy); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(5); cr.stroke()
            for xx in (x0, x1): cr.new_path(); cr.move_to(xx, yy - 18); cr.line_to(xx, yy + 18); cr.stroke()
            ptext(cr, 'AUSTRALIA ~4,000 KM', (x0 + x1) / 2, yy + 60, 40, GOLD, a, sw=7)
            ptext(cr, 'MOON 3,474 KM', cx, y + 10, 40, INK, a, sw=0, shadow=False)
        slam(cr, 'WIDER THAN', 540, 250, 120, WHITE, t, w('h1', 'wider'), a)
        slam(cr, 'THE MOON', 540, 390, 150, GOLD, t, w('h1', 'Moon'), a)
    a = win('h2', t=t)
    if a > 0:  # the mainland USA, at true size, laid over Australia
        tu = w('h2', 'United') - 0.2; k = ease_io(prog(t, tu, tu + 0.7))
        cr.new_path(); path_xy(cr, cam, moved(G.usa48, (-98, 39), (134, -25.5), 1.0))
        cr.save(); cr.translate(0, (1 - k) * -900); cr.set_source_rgba(*BLUE[:3], 0.55 * a * k); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, a * k); cr.set_line_width(3); cr.stroke(); cr.restore()
        slam(cr, 'AS BIG AS', 540, 250, 110, WHITE, t, w('h2', 'big'), a)
        slam(cr, 'THE MAINLAND USA', 540, 390, 110, BLUE, t, w('h2', 'United'), a)
    a = win('h3', 'title', t=t)
    if a > 0:
        if bt('h3')['start'] <= t < bt('title')['start']:
            tt = w('h3', 'Texas'); k = ease_io(prog(t, tt - 0.2, tt + 0.5)); ka = a * (1 - prog(t, w('h3', 'almost') - 0.2, w('h3', 'almost') + 0.2))
            if ka > 0:
                cr.new_path(); path_xy(cr, cam, moved(G.texas, (-99.3, 31.3), (134, -25.5), 1.0)); cr.set_source_rgba(*CRIMSON[:3], 0.7 * ka * k); cr.fill_preserve()
                cr.set_source_rgba(1, 1, 1, ka * k); cr.set_line_width(3); cr.stroke()
                label(cr, cam, 134, -25.5, 'TEXAS · 31M PEOPLE', 40, WHITE, ka, tt, t)
            slam(cr, 'FEWER PEOPLE', 540, 250, 120, WHITE, t, w('h3', 'fewer'), a)
            slam(cr, 'THAN TEXAS', 540, 390, 140, CRIMSON, t, tt, a)
        th = w('h3', 'here')
        coast_band(cr, cam, a * ease_out(prog(t, w('h3', 'almost'), th + 0.3)), 50)
        dots(cr, cam, a, t, w('h3', 'live'))
    # ----- numbers -----
    a = win('nums', t=t)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.55 * a); cr.paint()
        rows = (('twenty', 'AUSTRALIA', 27, OCHRE), ('Texas', 'TEXAS', 31, CRIMSON), ('whole', 'USA', 340, BLUE))
        for i, (word, lab, m, col) in enumerate(rows):
            te = w('nums', word)
            if t < te: continue
            k = ease_out(prog(t, te, te + 0.8)); y = 820 + i * 230; wd = 860 * m / 340 * k
            ptext(cr, lab, 110, y - 40, 48, WHITE, a, anchor='l', sw=7)
            rrect(cr, 110, y, max(20, wd), 80, 40); cr.set_source_rgba(*col[:3], a); cr.fill()
            ptext(cr, f'{int(m * k)}M', 110 + max(20, wd) + 20, y + 58, 52, WHITE, a, anchor='l', sw=7)
    a = win('coast', t=t)
    if a > 0:
        coast_band(cr, cam, a * ease_out(prog(t, w('coast', 'fifty'), w('coast', 'coast') + 0.3)), 50)
        dots(cr, cam, a, t, bt('coast')['start'])
        chip(cr, '~85% WITHIN 50 KM OF THE COAST', 540, 1380, 44, GOLD, INK, pop_k(t, w('coast', 'eighty')), a, em='🏖️')
        chip(cr, '2 IN 3 IN 8 CAPITAL CITIES', 540, 1500, 46, WHITE, INK, pop_k(t, w('coast', 'two')), a, em='🏙️')
    # ----- the outback -----
    a = win('dry', t=t)
    if a > 0:
        ta = w('dry', 'arid')
        poly(cr, cam, ARID, SAND, 0.85 * a * ease_out(prog(t, w('dry', 'seventy'), w('dry', 'seventy') + 0.8)), (1, 0.95, 0.8), 3, [10, 8])
        for i, (n, lon, lat) in enumerate(DESERTS): label(cr, cam, lon, lat, n, 28, (0.35, 0.2, 0.08), a, ta + i * 0.12, t)
        slam(cr, 'DRIEST', 540, 300, 140, SAND, t, w('dry', 'driest'), a)
        chip(cr, 'INHABITED CONTINENT', 540, 420, 44, WHITE, INK, pop_k(t, w('dry', 'inhabited')), a)
        chip(cr, '~70% ARID OR SEMI-ARID', 540, 1420, 52, SAND, INK, pop_k(t, w('dry', 'seventy')), a, em='🏜️')
    a = win('heat', t=t)
    if a > 0:
        tf = w('heat', 'forty')
        cr.set_source_rgba(1, 0.3, 0.05, 0.25 * a * ease_out(prog(t, tf, tf + 0.6))); cr.paint()
        chip(cr, 'SUMMER: 45 °C+', 540, 1360, 54, (1, 0.6, 0.2), INK, pop_k(t, tf), a, em='🌡️')
        tr = w('heat', 'record')
        if t >= tr:
            C.pin(cr, cam, (135.45, -27.55), 'OODNADATTA', t, tr, (1, 0.35, 0.2), 'r', 34, a)
            slam(cr, '50.7 °C', 540, 1500, 120, (1, 0.35, 0.2), t, w('heat', 'fifty'), a)
    a = win('range', t=t)
    if a > 0:
        tg = w('range', 'Great')
        R.route(cr, cam, RANGE, ease_io(prog(t, tg, tg + 1.0)), (0.45, 0.32, 0.22), width=14, dashed_rest=False)
        label(cr, cam, 141.5, -24, 'GREAT DIVIDING RANGE', 32, WHITE, a, tg + 0.5, t)
        trn = w('range', 'rain')
        if t >= trn:
            for i, (lon, lat) in enumerate(((151, -25), (153, -29.5), (151.5, -33), (148.5, -37), (146.5, -19))):
                at = L(cam, lon + 1.5, lat); emoji(cr, '🌧️', at[0], at[1], 70 * pop_k(t, trn + i * 0.08), a)
        td = w('range', 'dries')
        if t >= td:
            for i, (lon, lat) in enumerate(((140, -27), (137, -22), (142, -31))): x, y = L(cam, lon, lat); emoji(cr, '☀️', x, y, 80 * pop_k(t, td + i * 0.1), a)
    a = win('nt', t=t)
    if a > 0:
        tn = w('nt', 'Northern')
        cr.new_path(); path_xy(cr, cam, G.prov['Northern Territory']); cr.set_source_rgba(1, 1, 1, 0.3 * a * ease_out(prog(t, tn, tn + 0.4))); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(4); cr.stroke()
        tf = w('nt', 'France')
        if t >= tf:  # France + Spain at true size, dropped onto the Territory
            k = ease_out(prog(t, tf, tf + 0.7))
            for shapes, src, dst, col in ((G.fr, (2.5, 46.5), (134.5, -15.6), BLUE), (G.es, (-3.7, 40.2), (132.5, -21.6), (0.95, 0.75, 0.2))):
                cr.new_path(); path_xy(cr, cam, moved(shapes, src, dst, 1.0)); cr.save(); cr.translate(0, (1 - k) * -700)
                cr.set_source_rgba(*col[:3], 0.65 * a * k); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a * k); cr.set_line_width(3); cr.stroke(); cr.restore()
            label(cr, cam, 134.5, -15.6, 'FRANCE', 36, WHITE, a, tf + 0.5, t); label(cr, cam, 132.5, -21.6, 'SPAIN', 36, WHITE, a, w('nt', 'Spain') + 0.3, t)
        chip(cr, '~250,000 PEOPLE', 540, 1420, 56, WHITE, INK, pop_k(t, w('nt', 'quarter')), a, em='👥')
    # ----- history -----
    a = win('first', t=t)
    if a > 0:
        tf = w('first', 'lived')
        rng = np.random.default_rng(8)
        for i in range(160):  # dot-painting style marks across the land
            lon, lat = rng.uniform(116, 150), rng.uniform(-36, -15); x, y = L(cam, lon, lat)
            k = pop_k(t, tf + i * 0.008)
            if t >= tf + i * 0.008:
                cr.new_path(); cr.arc(x, y, 7 * k, 0, 2 * math.pi)
                cr.set_source_rgba(*[(1, 0.95, 0.85), (0.95, 0.75, 0.3), (0.85, 0.3, 0.15)][i % 3], 0.9 * a); cr.fill()
        chip(cr, '50,000+ YEARS', 540, 1420, 64, (0.95, 0.75, 0.3), INK, pop_k(t, w('first', 'fifty')), a)
    a = win('fleet', t=t)
    if a > 0:
        t1 = w('fleet', '1788')
        R.route(cr, cam, [(158, -36.5), (153.5, -34.5), (151.25, -33.86)], ease_io(prog(t, t1 - 0.4, w('fleet', 'Cove', end=True))), WHITE, width=5,
                head='⛵', head_size=80, dashed_rest=False)
        for i, (nm, lon, lat, yr, word) in enumerate(COLONIES):
            ts = t1 + 0.3 if i == 0 else w('fleet', word)
            C.pin(cr, cam, (lon, lat), f'{nm} {yr}', t, ts, GOLD, 'l' if nm in ('PERTH', 'ADELAIDE', 'MELBOURNE', 'HOBART') else 'r', 32, a)
        chip(cr, 'ALL ON THE COAST', 540, 1460, 56, GOLD, INK, pop_k(t, w('fleet', 'All')), a, em='⚓')
    a = win('sheep', t=t)
    if a > 0:
        ts = w('sheep', 'sheep')
        rng = np.random.default_rng(4)
        for i in range(26):
            lon, lat = rng.uniform(118, 150), rng.uniform(-36, -20)
            if t >= ts + i * 0.04: x, y = L(cam, lon, lat); emoji(cr, '🐑' if i % 4 else '🐄', x, y, 56 * pop_k(t, ts + i * 0.04), a)
        if t >= w('sheep', 'three'):
            k = pop_k(t, w('sheep', 'three')); cr.save(); cr.translate(540, 1430); cr.scale(k, k)
            rrect(cr, -380, -80, 760, 160, 40); cr.set_source_rgba(0.05, 0.05, 0.08, 0.9 * a); cr.fill()
            for i in range(3): emoji(cr, '🐑', -270 + i * 120, -6, 100, a)
            ptext(cr, '=', 60, 22, 80, WHITE, a, sw=6); emoji(cr, '🧍', 180, -6, 100, a); cr.restore()
    # ----- today -----
    a = win('cities', t=t)
    if a > 0:
        dots(cr, cam, a, t, bt('cities')['start'])
        for i, (word, nm, lon, lat) in enumerate((('Sydney', 'SYDNEY ~5.5M', 151.21, -33.87), ('Melbourne', 'MELBOURNE ~5.2M', 144.96, -37.81))):
            te = w('cities', word)
            if t >= te:
                x, y = L(cam, lon, lat); k = pop_k(t, te); cr.new_path(); cr.arc(x, y, 70 * k, 0, 2 * math.pi); cr.set_source_rgba(1, 0.92, 0.35, 0.35 * a); cr.fill()
                label(cr, cam, lon - (3.5 if i == 0 else -0.5), lat + (1.6 if i == 0 else -1.9), nm, 38, WHITE, a, te, t)
        chip(cr, '~40% OF AUSTRALIANS', 540, 1440, 58, GOLD, INK, pop_k(t, w('cities', 'forty')), a)
    a = win('perth', t=t)
    if a > 0:
        tp = w('perth', 'Perth'); C.pin(cr, cam, (115.86, -31.95), 'PERTH', t, tp, GOLD, 'l', 36, a)
        for dst, word, txt, col, d in ((BALI, 'Bali', 'BALI ~2,600 KM', TEAL, 0.0), ((151.21, -33.87), 'Sydney', 'SYDNEY ~3,300 KM', WHITE, 0.0)):
            td = w('perth', word)
            mid = ((115.86 + dst[0]) / 2, (-31.95 + dst[1]) / 2 + (2 if dst is BALI else 4))
            R.route(cr, cam, [(115.86, -31.95), mid, dst], ease_io(prog(t, td - 0.3, td + 0.6)), col, width=6, arrow=True, dashed_rest=False)
            if t >= td: C.pin(cr, cam, dst, txt, t, td + 0.4, col, 'r' if dst is BALI else 'l', 34, a)
        slam(cr, 'CLOSER TO BALI', 540, 470, 110, TEAL, t, w('perth', 'closer'), a)

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end'] + 0.2): return
    a = 1 - ease_io(prog(t, b['end'] - 0.25, b['end'] + 0.2))
    k = pop_k(t, w('title', 'why') - 0.1); cr.save(); cr.translate(540, 250); cr.scale(k, k); ptext(cr, 'SO WHY IS', 0, 0, 100, WHITE, a, sw=12); cr.restore()
    slam(cr, 'AUSTRALIA', 540, 400, 140, WHITE, t, w('title', 'Australia'), a)
    slam(cr, 'SO EMPTY?', 540, 570, 170, OCHRE, t, w('title', 'empty'), a)

def draw_cta(cr, t):
    b = bt('cta')
    if t < b['start']: return
    a = ease_out(prog(t, b['start'], b['start'] + 0.4))
    cr.set_source_rgba(0.03, 0.03, 0.05, 0.6 * a); cr.paint()
    k = pop_k(t, w('cta', 'Would')); cr.save(); cr.translate(540, 520); cr.scale(k, k)
    ptext(cr, 'WOULD YOU LIVE IN', 0, 0, 80, WHITE, a, sw=10); ptext(cr, 'THE OUTBACK?', 0, 130, 130, OCHRE, a, sw=13); cr.restore()
    for i, (txt, col, d) in enumerate((('YES', (0.3, 0.8, 0.4), 0.3), ('NO WAY', (0.9, 0.3, 0.3), 0.45))):
        if t < w('cta', 'outback') + d: continue
        kk = pop_k(t, w('cta', 'outback') + d) * (1 + 0.03 * math.sin(t * 6 + i)); cr.save(); cr.translate(310 + i * 460, 880); cr.scale(kk, kk)
        rrect(cr, -190, -70, 380, 140, 70); cr.set_source_rgba(*col, 1); cr.fill(); ptext(cr, txt, 0, 26, 72, WHITE, 1, sw=8); cr.restore()
    tc = w('cta', 'comments')
    if t >= tc: k = pop_k(t, tc); cr.save(); cr.translate(540, 1080); cr.scale(k, k); ptext(cr, 'COMMENT BELOW', -50, 0, 66, WHITE, 1, sw=9); emoji(cr, '👇', 330, -20, 80, 1); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1260); cr.scale(k, k); txt = 'FOLLOW FOR MORE'; wd = tw(cr, txt, 56)
        rrect(cr, -wd / 2 - 90, -62, wd + 180, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 56, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 66, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def render_frame(cr, t):
    cam = camera(t)
    draw_base(cr, cam, t)
    if t >= bt('cta')['start']: coast_band(cr, cam, 1, 50); dots(cr, cam, 1, t, bt('cta')['start'])
    C.vignette(cr, 0.65)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0, 0.75); g.add_color_stop_rgba(1, 0, 0, 0, 0); cr.set_source(g); cr.paint()
    g = cairo.LinearGradient(0, 1500, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.8); cr.set_source(g); cr.paint()
    draw_story(cr, cam, t)
    C.draw_chapter_label(cr, t)
    draw_title(cr, t)
    C.draw_chapter_card(cr, t)
    draw_cta(cr, t)
    C.draw_captions(cr, t, 1680)
    for k in ('h2', 'h3', 'title'):
        f = 1 - prog(t, bt(k)['start'], bt(k)['start'] + 0.15)
        if t >= bt(k)['start'] and f > 0: cr.set_source_rgba(1, 1, 1, 0.5 * f); cr.paint()
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR; rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 104; bar = beat * 4
    L_ = np.arange(int(dur * SR)) / SR  # a didgeridoo-like drone under everything
    drone = 0.05 * np.sin(2 * np.pi * 65.4 * L_ + 0.8 * np.sin(2 * np.pi * 0.7 * L_)) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * L_))
    drone += 0.02 * np.sin(2 * np.pi * 130.8 * L_ + 1.2 * np.sin(2 * np.pi * 1.4 * L_)); music[:len(drone)] += drone
    chords = [[52, 59, 64, 67], [48, 55, 60, 64], [50, 57, 62, 66], [47, 54, 59, 62]]
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar * 1.3 * SR)) / SR; env = np.minimum(1, Lc / 0.4) * np.exp(-Lc * 0.6)
        put(music, ci * bar, sum(0.025 * np.sin(2 * np.pi * note(m) * Lc) for m in ch) * env)
        for j in range(8):
            m = ch[[0, 2, 1, 3, 2, 1, 3, 2][j]] + 12; P = np.arange(int(0.35 * SR)) / SR
            put(music, ci * bar + j * beat / 2, 0.03 * np.sin(2 * np.pi * note(m) * P) * np.exp(-P * 10))
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 > bt('cta')['start'] + 3: break
        if bi % 2 == 0 or t0 < bt('title')['start']:
            Ld = np.arange(int(0.4 * SR)) / SR; put(music, t0, 0.35 * np.sin(2 * np.pi * np.cumsum(55 + 60 * np.exp(-Ld * 20)) / SR) * np.exp(-Ld * 8))
        M = np.arange(int(0.04 * SR)); put(music, t0 + beat / 2, 0.03 * rng.standard_normal(len(M)) * np.exp(-M / SR * 70))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.6):
        Lb = np.arange(int(1.8 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 80 * np.exp(-Lb * 10)) / SR) * np.exp(-Lb * 2.5))
    def whoosh(t0, amp=0.25):
        nz = rng.standard_normal(int(0.7 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2; put(fx, t0, amp * np.convolve(nz, np.ones(30) / 30, 'same') * env)
    whoosh(w('h1', 'Moon') - 0.6); whoosh(w('h2', 'United') - 0.5); whoosh(w('h3', 'Texas') - 0.5)
    for key, word in (('h1', 'Moon'), ('h2', 'United'), ('h3', 'Texas'), ('title', 'empty'), ('dry', 'driest'), ('heat', 'fifty'),
                      ('nt', 'France'), ('fleet', '1788'), ('sheep', 'three'), ('perth', 'closer')):
        boom(w(key, word), 0.7)
    for b in T['beats']:
        if b['chap']: boom(b['start'] + 0.1, 0.4)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    global G
    C.TL = C.build(C.WordVoice(cache)); G = Geo(data_dir)

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    data_dir, out = sys.argv[1:3]
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_aus'))
    print(f"duration {C.TL['dur']:.1f}s")
    for b in C.TL['beats']: print(f"  {b['key']:8s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','): render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]; make_audio(C.TL, base + '.wav')
    nfr = int(C.TL['dur'] * FPS); workers = os.cpu_count() or 4
    bounds = np.linspace(0, nfr, workers * 3 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
