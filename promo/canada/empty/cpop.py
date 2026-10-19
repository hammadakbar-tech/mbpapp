"""'Why Is Most of Canada Empty?' (9:16): Canada's size vs its population, the 160 km border band, the cold, the Shield,
farmland, history (rivers, railway), the corridor and the big three cities. Word-synced map video (engine from china.py).
Usage: python3 cpop.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
from china import R, ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON, PARCH, laea, S, L, path_xy
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

R.LON0, R.LAT0 = -96.0, 60.0
R.MAPY = 1000
RED, ICE, GREEN, ROCK, BLUE = hexc('#E3263B'), hexc('#BFE6FF'), hexc('#5BC46B'), hexc('#B08A6A'), hexc('#4FA3D9')
C.SAY = {None: {}}
C.HOT = ('canada', 'canadians', 'canadian', 'united', 'states', 'border', 'nunavut', 'mexico', 'permafrost', 'shield', 'farmland', 'railway',
         'california', 'toronto', 'montreal', 'vancouver', 'yukon', 'lawrence', 'lakes', 'cold', 'empty', 'windsor', 'quebec')
BEATS = [
    ('h1', "Canada is the second biggest country on Earth.", None, None, None, None, None),
    ('h2', "But it has about eight times fewer people than the United States.", None, None, None, None, None),
    ('h3', "And three out of four Canadians live within a hundred and sixty kilometres of the US border.", None, None, None, None, None),
    ('title', "So why is most of Canada empty?", None, None, None, None, None),
    ('nums', "Canada has about forty-one million people, roughly as many as California. The United States has about three hundred and forty million.",
     None, None, None, ('I', 'THE NUMBERS'), None),
    ('north', "The three northern territories cover almost forty percent of Canada, but hold less than half a percent of its people. Nunavut alone is bigger than Mexico, with about forty thousand people.",
     None, None, None, None, None),
    ('cold', "The first reason is the cold. About forty percent of Canada sits on permafrost: ground that stays frozen all year. In 1947, Yukon hit minus sixty-three degrees.",
     None, None, None, ('II', 'THE LAND'), None),
    ('shield', "Then there's the Canadian Shield: ancient rock covering about half the country, with thin soil and countless lakes. Great for mining... terrible for farming.",
     None, None, None, None, None),
    ('farm', "Only about seven percent of Canada is farmland, and almost all of it is in the far south.", None, None, None, None, None),
    ('river', "History did the rest. Europeans arrived by water, so towns grew along the Saint Lawrence River and the Great Lakes.",
     None, None, None, ('III', 'HISTORY'), None),
    ('rail', "In 1885, a railway finally linked the country from coast to coast, right along the southern edge.", None, None, None, None, None),
    ('south', "And here's a surprise: Canada's southernmost point is further south than the northern border of California.", None, None, None, None, None),
    ('corridor', "Today, nearly half of all Canadians live in one narrow strip, from Quebec City to Windsor.", None, None, None, ('IV', 'TODAY'), None),
    ('cities', "And over a third live in just three cities: Toronto, Montreal and Vancouver.", None, None, None, None, None),
    ('cta', "Where in Canada do you live? Tell us in the comments, and follow for more.", None, None, None, None, None),
]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2', 'h3')
bt, w, win = C.bt, C.w, C.win
G = None
FULL = (-96, 59, 0.2)
CAMS = {'river': (-76, 46, 0.42), 'corridor': (-77, 44.6, 0.5), 'south': (-100, 50, 0.19)}
CITIES = [('Toronto', -79.38, 43.65, 6202), ('Montréal', -73.57, 45.5, 4291), ('Vancouver', -123.12, 49.28, 2642), ('Calgary', -114.07, 51.05, 1481),
          ('Ottawa', -75.7, 45.42, 1488), ('Edmonton', -113.49, 53.55, 1418), ('Winnipeg', -97.14, 49.9, 834), ('Québec', -71.21, 46.81, 839),
          ('Hamilton', -79.87, 43.26, 785), ('Kitchener', -80.49, 43.45, 575), ('London', -81.25, 42.98, 543), ('Halifax', -63.57, 44.65, 465),
          ('Windsor', -83.03, 42.31, 422), ('Oshawa', -78.86, 43.9, 415), ('Victoria', -123.37, 48.43, 397), ('Saskatoon', -106.67, 52.13, 317),
          ('Regina', -104.62, 50.45, 249), ('Sherbrooke', -71.89, 45.4, 227), ('Kelowna', -119.5, 49.89, 222), ("St. John's", -52.71, 47.56, 212),
          ('Kingston', -76.48, 44.23, 172), ('Sudbury', -81.0, 46.49, 170), ('Moncton', -64.78, 46.09, 157), ('Saint John', -66.06, 45.27, 130),
          ('Thunder Bay', -89.25, 48.38, 123), ('Whitehorse', -135.06, 60.72, 31), ('Yellowknife', -114.37, 62.45, 20), ('Iqaluit', -68.52, 63.75, 8)]
SHIELD = [(-114, 60), (-110, 58.5), (-104, 55.5), (-98, 52.5), (-95.3, 49.3), (-90, 48.3), (-84.5, 46.6), (-80, 45.2), (-76.5, 44.8), (-74.5, 46),
          (-70, 47.3), (-65, 49), (-60, 50.2), (-56.5, 52), (-60, 55.5), (-64, 59.5), (-70, 61.5), (-78, 62.5), (-79, 58), (-82, 55),
          (-86, 55.5), (-92, 57.5), (-95, 59.5), (-96, 62), (-100, 64.5), (-110, 67.5), (-118, 68), (-123, 66), (-120, 62)]
PRAIRIE = [(-114.1, 49), (-114.3, 51), (-115, 53.6), (-113, 55.2), (-108, 54.2), (-102, 53.6), (-99, 52.2), (-97, 51), (-96.5, 49)]
SOUTHON = [(-83, 42.2), (-82.4, 43.0), (-81.7, 44.6), (-80, 45), (-77.8, 44.5), (-75.4, 45.6), (-72, 46.5), (-70.5, 47.2), (-71.5, 46.3),
           (-73.8, 45), (-76.6, 44.1), (-79.2, 43.2), (-81.5, 42.4)]
PERMA = [(-141, 60), (-133, 59), (-124, 58.5), (-118, 57.5), (-110, 56.5), (-102, 56), (-96, 55.5), (-90, 53.5), (-84, 52.5), (-79, 51.5),
         (-75, 51), (-70, 51.5), (-64, 52.5), (-57, 53), (-55, 60), (-60, 75), (-100, 84), (-141, 72)]
CORRIDOR = [(-83.03, 42.31), (-81.25, 42.98), (-79.38, 43.65), (-78.0, 44.0), (-76.48, 44.23), (-75.0, 45.0), (-73.57, 45.5), (-72.5, 46.2), (-71.21, 46.81)]
RAIL = [(-73.57, 45.5), (-75.7, 45.42), (-79.46, 46.31), (-81.0, 46.49), (-84.3, 46.6), (-86.0, 48.6), (-89.25, 48.38), (-93.4, 49.75), (-97.14, 49.9),
        (-101.0, 50.0), (-104.62, 50.45), (-110.7, 50.04), (-114.07, 51.05), (-115.57, 51.18), (-118.2, 51.0), (-120.33, 50.67), (-121.95, 49.17), (-123.12, 49.28)]
RIVER_IN = [(-60, 49.5), (-64.5, 49.2), (-68.5, 48.4), (-71.21, 46.81), (-72.5, 46.25), (-73.57, 45.5), (-75.0, 44.9), (-76.48, 44.23), (-79.38, 43.65)]

class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        self.canr = [r for r in rings(cf['Canada']['geometry']) if len(r) > 3]
        self.can = [laea(r[:, 0], r[:, 1]) for r in self.canr]
        self.usa = [laea(r[:, 0], r[:, 1]) for r in rings(cf['United States of America']['geometry']) if len(r) > 3]
        self.mex = [laea(r[:, 0], r[:, 1]) for r in rings(cf['Mexico']['geometry']) if len(r) > 3]
        uset = set(map(tuple, np.round(np.concatenate([r for r in rings(cf['United States of America']['geometry'])]), 2)))
        self.border = []  # Canada-USA boundary segments (shared vertices)
        for r in self.canr:
            on = [tuple(np.round(p, 2)) in uset for p in r]
            run = []
            for p, o in zip(r, on):
                if o: run.append(p)
                elif len(run) > 1: self.border.append(np.array(run)); run = []
                else: run = []
            if len(run) > 1: self.border.append(np.array(run))
        self.border = [laea(b[:, 0], b[:, 1]) for b in self.border]
        self.land = [laea(r[:, 0], r[:, 1]) for f in json.load(open(os.path.join(d, 'ne_50m_land.geojson')))['features']
                     for r in rings(f['geometry']) if len(r) > 3 and -180 < r[:, 0].mean() < -20 and r[:, 1].mean() > 10]
        self.lakes = [laea(r[:, 0], r[:, 1]) for f in json.load(open(os.path.join(d, 'ne_50m_lakes.geojson')))['features']
                      for r in rings(f['geometry']) if len(r) > 3 and -145 < r[:, 0].mean() < -50 and r[:, 1].mean() > 38]
        self.great = [laea(r[:, 0], r[:, 1]) for f in json.load(open(os.path.join(d, 'ne_50m_lakes.geojson')))['features']
                      if f['properties'].get('name') in ('Lake Erie', 'Lake Ontario', 'Lake Superior', 'Lake Huron', 'Lake Michigan') for r in rings(f['geometry'])]
        self.prov = {}
        for f in json.load(open(os.path.join(d, 'admin1_50m.geojson')))['features']:
            if f['properties'].get('admin') == 'Canada':
                self.prov[f['properties']['name']] = [laea(r[:, 0], r[:, 1]) for r in rings(f['geometry']) if len(r) > 3]
        self.slaw = []
        for f in json.load(open(os.path.join(d, 'ne_50m_rivers_lake_centerlines.geojson')))['features']:
            if f['properties'].get('name') == 'St. Lawrence' and f['geometry']:
                for c in (f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiLineString' else [f['geometry']['coordinates']]):
                    c = np.array(c); self.slaw.append(laea(c[:, 0], c[:, 1]))

def camera(t):
    cur = FULL
    for k, cam in CAMS.items():
        b = bt(k); end = bt('cities')['end'] if k == 'corridor' else b['end']
        a = ease_io(prog(t, b['start'], b['start'] + 1.2)) * (1 - ease_io(prog(t, end - 0.3, end + 1.0)))
        if k == 'river': a *= 1 - ease_io(prog(t, bt('rail')['start'], bt('rail')['start'] + 1.2))
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

def clip_canada(cr, cam): cr.new_path(); path_xy(cr, cam, G.can); cr.clip()

def label(cr, cam, lon, lat, txt, size, col, a, t0, t):
    if t < t0 or a <= 0: return
    k = pop_k(t, t0); x, y = L(cam, lon, lat); cr.save(); cr.translate(x, y); cr.scale(k, k)
    ptext(cr, txt, 0, 0, size, col, a, fam='Poppins ExtraBold', sw=7); cr.restore()

def band(cr, cam, a, km=160, col=GOLD):
    """The strip of Canada within `km` of the US border."""
    if a <= 0: return
    cr.save(); clip_canada(cr, cam); cr.new_path()
    path_xy(cr, cam, G.usa)  # stroking the US outline, clipped to Canada, gives everything within `km` of it
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.set_source_rgba(*col[:3], 0.8 * a); cr.set_line_width(2 * km * cam[2]); cr.stroke(); cr.restore()

def dots(cr, cam, a, t, t0, big=None):
    if a <= 0 or t < t0: return
    for i, (n, lon, lat, pop) in enumerate(CITIES):
        k = pop_k(t, t0 + i * 0.03); x, y = L(cam, lon, lat); r = (3 + math.sqrt(pop) * 0.55) * k * (cam[2] / 0.2) ** 0.5
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 0.9, 0.3, 0.85 * a); cr.fill_preserve()
        cr.set_source_rgba(0, 0, 0, 0.5 * a); cr.set_line_width(2); cr.stroke()

def draw_base(cr, cam, t):
    cr.set_source_rgb(0.04, 0.07, 0.12); cr.paint()
    g = cairo.RadialGradient(W / 2, R.MAPY, 100, W / 2, R.MAPY, 1300); g.add_color_stop_rgba(0, 0.1, 0.2, 0.32, 1); g.add_color_stop_rgba(1, 0.03, 0.06, 0.1, 1)
    cr.set_source(g); cr.paint()
    cr.new_path(); path_xy(cr, cam, G.land); cr.set_source_rgb(0.2, 0.2, 0.21); cr.fill()
    cr.new_path(); path_xy(cr, cam, G.usa); cr.set_source_rgb(0.27, 0.27, 0.3); cr.fill()
    ka = ease_out(prog(t, w('h1', 'Canada'), w('h1', 'Canada') + 0.4))
    cr.new_path(); path_xy(cr, cam, G.can); cr.set_source_rgba(*RED[:3], 0.88 * ka); cr.fill()
    # provinces (faint) and lakes
    cr.new_path(); path_xy(cr, cam, [r for rs in G.prov.values() for r in rs]); cr.set_source_rgba(1, 1, 1, 0.35 * ka); cr.set_line_width(1.2); cr.stroke()
    cr.new_path(); path_xy(cr, cam, G.lakes); cr.set_source_rgb(0.08, 0.16, 0.27); cr.fill()

def draw_story(cr, cam, t):
    # ----- hook -----
    a = win('h1', t=t)
    if a > 0:
        slam(cr, '2ND BIGGEST', 540, 260, 140, WHITE, t, w('h1', 'second'), a)
        slam(cr, 'COUNTRY ON EARTH', 540, 390, 80, GOLD, t, w('h1', 'Earth'), a)
        chip(cr, '9.98 MILLION KM²', 540, 1500, 56, WHITE, INK, pop_k(t, w('h1', 'biggest')), a)
    a = win('h2', t=t)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.55 * a); cr.paint()
        te = w('h2', 'eight')
        for row, (lab, n, col, y) in enumerate((('CANADA', 1, RED, 820), ('USA', 8, BLUE, 1140))):
            ptext(cr, lab, 540, y - 120, 56, col, a, sw=8)
            for i in range(n):
                ts = te + i * 0.06
                if t >= ts: emoji(cr, '🧍', 540 + (i - (n - 1) / 2) * 120, y, 130 * pop_k(t, ts), a)
        slam(cr, '8× FEWER PEOPLE', 540, 400, 110, GOLD, t, w('h2', 'fewer'), a)
    a = win('h3', 'title', t=t)
    if a > 0:
        tb = w('h3', 'hundred'); band(cr, cam, a * ease_out(prog(t, tb, tb + 0.8)))
        dots(cr, cam, a, t, w('h3', 'live'))
        if bt('h3')['start'] <= t < bt('title')['start']:
            slam(cr, '3 IN 4 CANADIANS', 540, 260, 120, GOLD, t, w('h3', 'three'), a)
            slam(cr, 'LIVE IN THIS STRIP', 540, 390, 80, WHITE, t, w('h3', 'live'), a)
            chip(cr, '160 KM FROM THE US BORDER', 540, 1500, 50, GOLD, INK, pop_k(t, w('h3', 'kilometres')), a)
    # ----- numbers -----
    a = win('nums', t=t)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.5 * a); cr.paint()
        rows = (('forty', 'CANADA', 41, RED), ('California', 'CALIFORNIA', 39, GOLD), ('three', 'USA', 340, BLUE))
        for i, (word, lab, m, col) in enumerate(rows):
            te = w('nums', word) if word != 'three' else w('nums', 'States')
            if t < te: continue
            k = ease_out(prog(t, te, te + 0.8)); y = 820 + i * 230; wd = 860 * m / 340 * k
            ptext(cr, lab, 110, y - 40, 48, WHITE, a, anchor='l', sw=7)
            rrect(cr, 110, y, max(20, wd), 80, 40); cr.set_source_rgba(*col[:3], a); cr.fill()
            ptext(cr, f'{int(m * k)}M', 110 + max(20, wd) + 20, y + 58, 52, WHITE, a, anchor='l', sw=7)
    a = win('north', t=t)
    if a > 0:
        tt = w('north', 'territories')
        for n in ('Yukon', 'Northwest Territories', 'Nunavut'):
            cr.new_path(); path_xy(cr, cam, G.prov[n]); cr.set_source_rgba(*ICE[:3], 0.55 * a * ease_out(prog(t, tt, tt + 0.5))); cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, 0.8 * a); cr.set_line_width(2.5); cr.stroke()
        chip(cr, '~40% OF THE LAND', 540, 1360, 50, ICE, INK, pop_k(t, w('north', 'forty')), a)
        chip(cr, '<0.5% OF THE PEOPLE', 540, 1480, 50, WHITE, INK, pop_k(t, w('north', 'half')), a)
        tm = w('north', 'Mexico')
        if t >= tm:  # Mexico, at true size, dropped onto Nunavut (equal-area projection)
            k = ease_out(prog(t, tm, tm + 0.8)); mx, my = laea(-102, 23.5); nx, ny = laea(-88, 67)
            dx, dy = lerp(0, nx - mx, k), lerp(0, ny - float(my), k)
            cr.new_path(); path_xy(cr, cam, [(x + dx, y + dy) for x, y in G.mex]); cr.set_source_rgba(0.3, 0.8, 0.45, 0.6 * a); cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(3); cr.stroke()
            label(cr, cam, -88, 67, 'MEXICO', 44, WHITE, a, tm + 0.6, t)
        label(cr, cam, -95, 72, 'NUNAVUT ~40,000 PEOPLE', 34, ICE, a, w('north', 'forty', n=1), t)
    # ----- the land -----
    a = win('cold', t=t)
    if a > 0:
        tp = w('cold', 'permafrost')
        cr.save(); clip_canada(cr, cam); poly(cr, cam, PERMA, ICE, 0.6 * a * ease_out(prog(t, tp, tp + 0.8))); cr.restore()
        if t >= tp:
            rng = np.random.default_rng(3)
            for i in range(14): emoji(cr, '❄️', *L(cam, rng.uniform(-135, -65), rng.uniform(60, 75)), 44 * pop_k(t, tp + i * 0.05), a)
        chip(cr, '~40% PERMAFROST', 540, 1360, 50, ICE, INK, pop_k(t, w('cold', 'forty')), a, em='🧊')
        ts = w('cold', '1947')
        if t >= ts:
            C.pin(cr, cam, (-140.4, 62.4), 'SNAG, YUKON', t, ts, ICE, 'r', 34, a)
            chip(cr, '−63 °C · 1947', 540, 1480, 56, WHITE, INK, pop_k(t, w('cold', 'minus')), a, em='🥶')
    a = win('shield', t=t)
    if a > 0:
        ts = w('shield', 'Shield')
        cr.save(); clip_canada(cr, cam); poly(cr, cam, SHIELD, ROCK, 0.75 * a * ease_out(prog(t, ts, ts + 0.8)), (0.9, 0.75, 0.6), 3, [10, 8]); cr.restore()
        label(cr, cam, -88, 52.5, 'CANADIAN SHIELD', 40, (1, 0.9, 0.75), a, ts + 0.2, t)
        chip(cr, '~HALF OF CANADA', 540, 1360, 50, ROCK, INK, pop_k(t, w('shield', 'half')), a, em='🪨')
        for word, e, txt, col, y in (('mining', '⛏️', 'MINING ✓', GREEN, 1480), ('terrible', '🌾', 'FARMING ✗', CRIMSON, 1480)):
            te = w('shield', word)
            if t >= te: chip(cr, txt.split()[0], 330 if word == 'mining' else 750, y, 46, col, INK, pop_k(t, te), a, em=e)
    a = win('farm', t=t)
    if a > 0:
        tf = w('farm', 'farmland')
        for shp in (PRAIRIE, SOUTHON): poly(cr, cam, shp, GREEN, 0.8 * a * ease_out(prog(t, tf - 0.2, tf + 0.6)), (0.8, 1, 0.8), 2)
        chip(cr, 'ONLY ~7% IS FARMLAND', 540, 1400, 54, GREEN, INK, pop_k(t, w('farm', 'seven')), a, em='🌾')
        label(cr, cam, -106, 52.8, 'PRAIRIES', 36, WHITE, a, w('farm', 'south'), t)
    # ----- history -----
    a = win('river', t=t)
    if a > 0:
        tr = w('river', 'Lawrence')
        cr.new_path(); path_xy(cr, cam, G.great); cr.set_source_rgba(*BLUE[:3], 0.9 * a * ease_out(prog(t, w('river', 'Great'), w('river', 'Great') + 0.5))); cr.fill()
        R.route(cr, cam, RIVER_IN, ease_io(prog(t, w('river', 'water'), w('river', 'Lakes', end=True))), BLUE, width=7, head='⛵', head_size=70, dashed_rest=False)
        for i, (nm, lon, lat, yr) in enumerate((('QUÉBEC', -71.21, 46.81, '1608'), ('MONTRÉAL', -73.57, 45.5, '1642'), ('TORONTO', -79.38, 43.65, '1793'))):
            C.pin(cr, cam, (lon, lat), f'{nm} {yr}', t, w('river', 'towns') + i * 0.35, GOLD, 'r' if i != 2 else 'b', 32, a)
    a = win('rail', t=t)
    if a > 0:
        R.route(cr, cam, RAIL, ease_io(prog(t, w('rail', 'railway'), w('rail', 'coast', n=1, end=True))), GOLD, width=7, head='🚂', head_size=70, dashed_rest=False)
        band(cr, cam, 0.6 * a * ease_out(prog(t, w('rail', 'southern'), w('rail', 'southern') + 0.5)), 160, GOLD)
        chip(cr, '1885 · COAST TO COAST', 540, 1400, 52, GOLD, INK, pop_k(t, w('rail', '1885')), a, em='🚂')
    a = win('south', t=t)
    if a > 0:
        tl = w('south', 'southernmost')
        if t >= tl:
            k = ease_io(prog(t, tl, tl + 1.2)); x0, y0 = L(cam, -124.2, 42.0); x1, y1 = L(cam, lerp(-124.2, -80, k), 42.0)
            lons = np.linspace(-124.2, lerp(-124.2, -80, k), 60); X, Y = L(cam, lons, np.full(60, 42.0))
            cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(p, q) for p, q in zip(X[1:], Y[1:])]
            cr.set_dash([16, 12]); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(4); cr.stroke(); cr.set_dash([])
            label(cr, cam, -116, 40.6, '42°N · CALIFORNIA BORDER', 30, WHITE, a, tl + 0.3, t)
        C.pin(cr, cam, (-82.68, 41.68), 'MIDDLE ISLAND 41.7°N', t, w('south', 'Canada'), GOLD, 'b', 32, a)
        chip(cr, "CANADA'S SOUTH TIP < CALIFORNIA'S NORTH", 540, 1420, 38, GOLD, INK, pop_k(t, w('south', 'California')), a)
    # ----- today -----
    a = win('corridor', 'cities', t=t)
    if a > 0:
        tc = w('corridor', 'strip')
        R.route(cr, cam, CORRIDOR, ease_io(prog(t, tc - 0.3, tc + 1.0)), GOLD, width=40, dashed_rest=False)
        dots(cr, cam, a, t, bt('corridor')['start'])
        if bt('corridor')['start'] <= t < bt('cities')['start']:
            C.pin(cr, cam, (-71.21, 46.81), 'QUÉBEC CITY', t, w('corridor', 'Quebec'), WHITE, 'r', 32, a)
            C.pin(cr, cam, (-83.03, 42.31), 'WINDSOR', t, w('corridor', 'Windsor'), WHITE, 'b', 32, a)
            chip(cr, '~HALF OF ALL CANADIANS', 540, 1420, 52, GOLD, INK, pop_k(t, w('corridor', 'half')), a)
    a = win('cities', t=t)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.6 * a); cr.paint()
        for i, (word, nm, pop, col) in enumerate((('Toronto', 'TORONTO', '6.2M', RED), ('Montreal', 'MONTRÉAL', '4.3M', BLUE), ('Vancouver', 'VANCOUVER', '2.6M', GREEN))):
            te = w('cities', word)
            if t < te: continue
            k = pop_k(t, te); x = 200 + i * 340; r = 70 + 40 * float(pop[:-1]) / 6.2
            cr.save(); cr.translate(x, 1000); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], a); cr.fill()
            ptext(cr, pop, 0, 18, 52, WHITE, a, sw=7); ptext(cr, nm, 0, r + 60, 40, WHITE, a, sw=6); cr.restore()
        slam(cr, '1 IN 3 CANADIANS', 540, 620, 110, GOLD, t, w('cities', 'third'), a)

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end'] + 0.2): return
    a = 1 - ease_io(prog(t, b['end'] - 0.25, b['end'] + 0.2))
    cr.set_source_rgba(0.02, 0.02, 0.03, 0.5 * a); cr.paint()
    k = pop_k(t, w('title', 'why') - 0.1); cr.save(); cr.translate(540, 300); cr.scale(k, k); ptext(cr, 'SO WHY IS', 0, 0, 100, WHITE, a, sw=12); cr.restore()
    slam(cr, 'MOST OF CANADA', 540, 440, 110, WHITE, t, w('title', 'most'), a)
    slam(cr, 'EMPTY?', 540, 620, 200, RED, t, w('title', 'empty'), a)

def draw_cta(cr, t):
    b = bt('cta')
    if t < b['start']: return
    a = ease_out(prog(t, b['start'], b['start'] + 0.4))
    cr.set_source_rgba(0.03, 0.03, 0.05, 0.55 * a); cr.paint()
    k = pop_k(t, w('cta', 'Where')); cr.save(); cr.translate(540, 420); cr.scale(k, k)
    ptext(cr, 'WHERE IN CANADA', 0, 0, 86, WHITE, a, sw=11); ptext(cr, 'DO YOU LIVE?', 0, 130, 130, RED, a, sw=13); cr.restore()
    tc = w('cta', 'comments')
    if t >= tc: k = pop_k(t, tc); cr.save(); cr.translate(540, 1300); cr.scale(k, k); ptext(cr, 'COMMENT BELOW', -50, 0, 66, WHITE, 1, sw=9); emoji(cr, '👇', 330, -20, 80, 1); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1460); cr.scale(k, k); txt = 'FOLLOW FOR MORE'; wd = tw(cr, txt, 56)
        rrect(cr, -wd / 2 - 90, -62, wd + 180, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 56, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 66, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def render_frame(cr, t):
    cam = camera(t)
    draw_base(cr, cam, t)
    if t >= bt('cta')['start']: dots(cr, cam, 1, t, bt('cta')['start'])
    C.vignette(cr, 0.65)
    g = cairo.LinearGradient(0, 0, 0, 560); g.add_color_stop_rgba(0, 0, 0, 0, 0.7); g.add_color_stop_rgba(1, 0, 0, 0, 0); cr.set_source(g); cr.paint()
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
    music = np.zeros(n); beat = 60 / 100; bar = beat * 4
    chords = [[48, 55, 60, 64], [45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59]]  # C Am F G: bright, open
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(bar * 1.3 * SR)) / SR; env = np.minimum(1, L_ / 0.4) * np.exp(-L_ * 0.6)
        put(music, ci * bar, sum(0.03 * np.sin(2 * np.pi * note(m) * L_) for m in ch) * env); put(music, ci * bar, 0.1 * np.sin(2 * np.pi * note(ch[0] - 12) * L_) * env)
        for j in range(8):
            m = ch[[0, 2, 1, 3, 2, 1, 3, 2][j]] + 12; P = np.arange(int(0.4 * SR)) / SR
            put(music, ci * bar + j * beat / 2, 0.03 * np.sin(2 * np.pi * note(m) * P) * np.exp(-P * 9))
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 > bt('cta')['start'] + 3: break
        if bi % 2 == 0 or t0 < bt('title')['start']:
            L_ = np.arange(int(0.4 * SR)) / SR; put(music, t0, 0.35 * np.sin(2 * np.pi * np.cumsum(55 + 60 * np.exp(-L_ * 20)) / SR) * np.exp(-L_ * 8))
        M = np.arange(int(0.04 * SR)); put(music, t0 + beat / 2, 0.03 * rng.standard_normal(len(M)) * np.exp(-M / SR * 70))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.6):
        L_ = np.arange(int(1.8 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 80 * np.exp(-L_ * 10)) / SR) * np.exp(-L_ * 2.5))
    def pop(t0, amp=0.06):
        L_ = np.arange(int(0.05 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * 900 * L_) * np.exp(-L_ * 60))
    for i in range(8): pop(w('h2', 'eight') + i * 0.06, 0.08)
    for key, word in (('h1', 'second'), ('h2', 'fewer'), ('h3', 'three'), ('title', 'empty'), ('north', 'Mexico'), ('cold', 'minus'),
                      ('south', 'California'), ('corridor', 'half'), ('cities', 'third')):
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_cpop'))
    print(f"duration {C.TL['dur']:.1f}s, border runs {len(G.border)}")
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
