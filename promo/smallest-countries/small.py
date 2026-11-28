"""'The 10 Smallest Countries on Earth' (9:16): a countdown, each country drawn at true size next to Manhattan or Central Park,
with a locator globe, its area and one surprising fact. Word-synced (engine from china.py).
Usage: python3 small.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON, PARCH
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

TEAL, SKY, CORAL, LIME, VIOLET = hexc('#2EC4B6'), hexc('#7FD8FF'), hexc('#FF6B6B'), hexc('#A3E635'), hexc('#9B6BFF')
C.SAY = {None: {'Nevis': 'Neevis', 'Liechtenstein': 'Lick-ten-stine', 'Tuvalu': 'Too-vah-loo', 'Nauru': 'Now-roo'}}
C.HOT = ('vatican', 'monaco', 'nauru', 'tuvalu', 'marino', 'liechtenstein', 'marshall', 'kitts', 'nevis', 'maldives', 'malta', 'central',
         'park', 'manhattan', 'smallest', 'capital', 'army', 'nuclear', 'oldest', 'lowest', 'number')
C.TAIL_OVERRIDE = {'h1': 0.3, 'h2': 0.3, 'h3': 0.45}
# rank, key, NE name, display, area km², colour, reference ('man' | 'park' | 'spread'), narration, fact chips [(word, emoji, text)]
ENTRIES = [
    (10, 'm10', 'Malta', 'MALTA', '316 KM²', CORAL, 'man',
     "Number ten: Malta. Three hundred and sixteen square kilometres. The smallest country in the European Union, yet over half a million people live here.",
     [('European', '🇪🇺', 'SMALLEST IN THE EU'), ('half', '👥', '~560,000 PEOPLE')]),
    (9, 'm9', 'Maldives', 'MALDIVES', '298 KM²', TEAL, 'spread',
     "Number nine: the Maldives. Almost twelve hundred tiny islands, and the lowest country on Earth. Its highest natural point is only about two and a half metres.",
     [('twelve', '🏝️', '~1,200 ISLANDS'), ('highest', '🌊', 'HIGHEST POINT ~2.4 M')]),
    (8, 'm8', 'St. Kitts and Nevis', 'ST KITTS & NEVIS', '261 KM²', LIME, 'man',
     "Number eight: Saint Kitts and Nevis, the smallest country in the Americas. Two islands, one country.",
     [('smallest', '🌎', 'SMALLEST IN THE AMERICAS'), ('Two', '🏝️', '2 ISLANDS')]),
    (7, 'm7', 'Marshall Is.', 'MARSHALL ISLANDS', '181 KM²', SKY, 'spread',
     "Number seven: the Marshall Islands. Twenty-nine coral atolls, including Bikini Atoll, where the United States tested nuclear bombs.",
     [('Twenty', '🪸', '29 CORAL ATOLLS'), ('nuclear', '☢️', 'BIKINI ATOLL · 1946–58')]),
    (6, 'm6', 'Liechtenstein', 'LIECHTENSTEIN', '160 KM²', VIOLET, 'man',
     "Number six: Liechtenstein. One of only two doubly landlocked countries on Earth, and it hasn't had an army since 1868.",
     [('doubly', '🔒', 'DOUBLY LANDLOCKED'), ('army', '🚫', 'NO ARMY SINCE 1868')]),
    (5, 'm5', 'San Marino', 'SAN MARINO', '61 KM²', SKY, 'man',
     "Number five: San Marino, about the size of Manhattan, and the oldest republic in the world. Legend says it was founded in the year 301.",
     [('Manhattan', '🗽', '≈ MANHATTAN'), ('oldest', '🏰', 'OLDEST REPUBLIC · 301 AD')]),
    (4, 'm4', 'Tuvalu', 'TUVALU', '26 KM²', TEAL, 'spread',
     "Number four: Tuvalu. Its internet domain is dot T V, and renting it out brings in a big chunk of the country's income.",
     [('domain', '🌐', '.TV'), ('income', '💰', 'A BIG CHUNK OF ITS INCOME')]),
    (3, 'm3', 'Nauru', 'NAURU', '21 KM²', LIME, 'man',
     "Number three: Nauru. You can drive all the way around it in about half an hour, and it has no official capital.",
     [('drive', '🚗', 'ONE RING ROAD · ~19 KM'), ('capital', '❓', 'NO OFFICIAL CAPITAL')]),
    (2, 'm2', 'Monaco', 'MONACO', '2 KM²', CORAL, 'park',
     "Number two: Monaco. Just two square kilometres, smaller than Central Park, and the most densely populated country on Earth.",
     [('Central', '🌳', '< CENTRAL PARK'), ('densely', '🏙️', 'MOST CROWDED ON EARTH')]),
    (1, 'm1', 'Vatican', 'VATICAN CITY', '0.44 KM²', GOLD, 'park',
     "And number one: Vatican City. Less than half a square kilometre, with only about eight hundred residents, and its own army: the Swiss Guard.",
     [('half', '⛪', 'ONLY 0.44 KM²'), ('Swiss', '💂', 'ARMY: THE SWISS GUARD')]),
]
BEATS = [
    ('h1', "You could walk across this country in about twenty minutes.", None, None, None, None, None),
    ('h2', "This one is smaller than New York's Central Park.", None, None, None, None, None),
    ('h3', "And this one... has no official capital.", None, None, None, None, None),
    ('title', "These are the ten smallest countries on Earth.", None, None, None, None, None),
] + [(e[1], e[7], None, None, None, None, None) for e in ENTRIES] + [
    ('cta', "Which one would you visit? Tell us in the comments, and follow for more.", None, None, None, None, None)]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2', 'h3')
bt, w, win = C.bt, C.w, C.win
G = None
MANHATTAN = [(-74.019, 40.700), (-74.013, 40.710), (-74.009, 40.739), (-74.011, 40.756), (-74.000, 40.768), (-73.985, 40.783), (-73.958, 40.823),
             (-73.937, 40.857), (-73.927, 40.877), (-73.910, 40.873), (-73.932, 40.836), (-73.934, 40.808), (-73.943, 40.787), (-73.958, 40.762),
             (-73.971, 40.744), (-73.974, 40.727), (-73.979, 40.711), (-73.996, 40.706), (-74.011, 40.701)]
PARK = [(-73.9812, 40.7681), (-73.9581, 40.8006), (-73.9498, 40.7969), (-73.9730, 40.7644)]

def local(rs, lon0, lat0):
    """Equal-area projection (km) around (lon0, lat0)."""
    out = []
    for r in rs:
        l, p, p0 = np.radians(r[:, 0] - lon0), np.radians(r[:, 1]), math.radians(lat0)
        cosc = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l)
        k = np.sqrt(2 / np.maximum(1 + cosc, 1e-9))
        out.append(np.column_stack([6371 * k * np.cos(p) * np.sin(l), 6371 * k * (math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l))]))
    return out

def area(rs): return sum(abs(0.5 * np.sum(r[:, 0] * np.roll(r[:, 1], 1) - r[:, 1] * np.roll(r[:, 0], 1))) for r in rs)

MONACO = [(7.4093, 43.7247), (7.4150, 43.7262), (7.4225, 43.7283), (7.4205, 43.7320), (7.4240, 43.7345), (7.4290, 43.7380), (7.4330, 43.7420),
          (7.4370, 43.7460), (7.4395, 43.7500), (7.4396, 43.7518), (7.4370, 43.7525), (7.4310, 43.7495), (7.4255, 43.7460), (7.4200, 43.7420),
          (7.4150, 43.7380), (7.4120, 43.7330), (7.4085, 43.7290), (7.4090, 43.7255)]  # land strip, traced; scaled to 2.02 km² below
OSM = {'Vatican': 'Vatican_City.json', 'Nauru': 'Nauru_island_.json', 'San Marino': 'San_Marino.json', 'Liechtenstein': 'Liechtenstein.json'}

class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'ne10/ne_10m_admin_0_countries.geojson')))['features']}
        self.shape, self.ll = {}, {}
        for e in ENTRIES:
            f = cf[e[2]]; rs = [r for r in rings(f['geometry']) if len(r) > 3]
            if e[2] in OSM:  # accurate OpenStreetMap outlines for the tiny ones
                rs = [r for r in rings(json.load(open(os.path.join(d, 'osm_small', OSM[e[2]])))['features'][0]['geometry']) if len(r) > 3]
            if e[2] == 'Monaco': rs = [np.array(MONACO)]
            lon0, lat0 = f['properties']['LABEL_X'], f['properties']['LABEL_Y']
            pts = np.concatenate(rs); lon0, lat0 = (pts[:, 0].min() + pts[:, 0].max()) / 2, (pts[:, 1].min() + pts[:, 1].max()) / 2
            self.shape[e[1]] = local(rs, lon0, lat0); self.ll[e[1]] = (lon0, lat0)
            if e[2] == 'Monaco':
                f_ = math.sqrt(2.02 / area(self.shape[e[1]])); self.shape[e[1]] = [r * f_ for r in self.shape[e[1]]]
        mm = np.array(MANHATTAN); self.man = local([mm], mm[:, 0].mean(), mm[:, 1].mean())
        pk = np.array(PARK); self.park = local([pk], pk[:, 0].mean(), pk[:, 1].mean())
        self.land = [r for f in json.load(open(os.path.join(d, 'land.geojson')))['features'] for r in rings(f['geometry']) if len(r) > 3]
        print('areas km²:', {k: round(area(v), 2) for k, v in self.shape.items()}, 'manhattan', round(area(self.man), 1), 'park', round(area(self.park), 2))

def bg(cr, t, col):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.05, 0.12); g.add_color_stop_rgb(1, *[0.06 + 0.12 * c for c in col[:3]])
    cr.set_source(g); cr.paint()
    off = (t * 30) % 90; cr.set_line_width(1.5)
    for x in range(0, W + 90, 90): cr.move_to(x, 0); cr.line_to(x, H)
    for y in range(-90, H + 90, 90): cr.move_to(0, y + off); cr.line_to(W, y + off)
    cr.set_source_rgba(1, 1, 1, 0.05); cr.stroke()

def bounds(rs):
    p = np.concatenate(rs); return p[:, 0].min(), p[:, 0].max(), p[:, 1].min(), p[:, 1].max()

def draw_shape(cr, rs, cx, cy, s, col, a, k=1.0, glow=False, outline=WHITE, lw=4):
    if a <= 0: return
    x0, x1, y0, y1 = bounds(rs); mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    cr.save(); cr.translate(cx, cy); cr.scale(k, k); cr.new_path()
    for r in rs:
        cr.move_to((r[0, 0] - mx) * s, -(r[0, 1] - my) * s)
        for x, y in r[1:]: cr.line_to((x - mx) * s, -(y - my) * s)
        cr.close_path()
    if glow:
        cr.set_source_rgba(*col[:3], 0.35 * a); cr.set_line_width(26 / max(k, 0.01)); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
    cr.set_source_rgba(*col[:3], 0.92 * a); cr.fill_preserve(); cr.set_source_rgba(*outline[:3], a); cr.set_line_width(lw / max(k, 0.01)); cr.stroke(); cr.restore()

def globe(cr, cx, cy, R, lon0, lat0, a):
    cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.set_source_rgba(0.1, 0.3, 0.55, a); cr.fill()
    cr.save(); cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.clip(); cr.new_path()
    l0, p0 = math.radians(lon0), math.radians(lat0)
    for r in G.land:
        l, p = np.radians(r[:, 0]), np.radians(r[:, 1])
        cc = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l - l0)
        if (cc < 0).all(): continue
        x = np.cos(p) * np.sin(l - l0); y = -(math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l - l0))
        rr = np.hypot(x, y); hid = cc < 0; x = np.where(hid, x / np.maximum(rr, 1e-9), x); y = np.where(hid, y / np.maximum(rr, 1e-9), y)
        cr.move_to(cx + x[0] * R, cy + y[0] * R); [cr.line_to(cx + u * R, cy + v * R) for u, v in zip(x[1:], y[1:])]; cr.close_path()
    cr.set_source_rgba(0.35, 0.6, 0.4, a); cr.fill(); cr.restore()
    cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.6 * a); cr.set_line_width(3); cr.stroke()
    pulse = 0.5 + 0.5 * math.sin(time_now * 6)
    cr.new_path(); cr.arc(cx, cy, 10 + 8 * pulse, 0, 2 * math.pi); cr.set_source_rgba(1, 0.3, 0.3, 0.5 * a); cr.fill()
    cr.new_path(); cr.arc(cx, cy, 8, 0, 2 * math.pi); cr.set_source_rgba(1, 0.25, 0.25, a); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(3); cr.stroke()

time_now = 0.0
def scale_bar(cr, s, a, y=1520):
    """A km bar matching the drawing scale `s` (px per km)."""
    for km in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500):
        if km * s > 120: break
    px = km * s; x0 = 540 - px / 2
    cr.new_path(); cr.move_to(x0, y); cr.line_to(x0 + px, y); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(5); cr.stroke()
    for x in (x0, x0 + px): cr.new_path(); cr.move_to(x, y - 14); cr.line_to(x, y + 14); cr.stroke()
    lab = f'{int(km * 1000)} M' if km < 1 else f'{int(km)} KM'
    ptext(cr, lab, 540, y - 26, 32, WHITE, a, fam='Poppins ExtraBold', sw=5)

def draw_entry(cr, t, e):
    rank, key, ne, name, ar, col, ref, text, facts = e
    b = bt(key); a = ease_out(prog(t, b['start'], b['start'] + 0.3)) * (1 - ease_io(prog(t, b['end'] - 0.25, b['end'])))
    bg(cr, t, col)
    if a <= 0: return
    rs = G.shape[key]; x0, x1, y0, y1 = bounds(rs); wkm, hkm = x1 - x0, y1 - y0
    if ref == 'spread':
        s = min(700 / wkm, 640 / hkm)
        draw_shape(cr, rs, 540, 930, s, col, a, pop_k(t, b['start'] + 0.1, 0.5), glow=True, lw=2)
        if t >= b['start'] + 0.3: ptext(cr, f'SPREAD OVER ~{int(round(max(wkm, hkm), -1)):,} KM', 540, 1300, 40, WHITE, a * pop_k(t, b['start'] + 0.6), sw=6)
    else:
        refs = G.man if ref == 'man' else G.park
        rx0, rx1, ry0, ry1 = bounds(refs); s = min(560 / max(wkm, rx1 - rx0) / 1.0, 620 / max(hkm, ry1 - ry0))
        s = min(s, 600 / (wkm + (rx1 - rx0) + 0.35 * wkm))
        tw0 = w(key, 'Manhattan') if ref == 'man' and key == 'm5' else b['start'] + 0.9
        cxc = 540 - ((rx1 - rx0) * s) / 2 - 20 if t >= tw0 else 540
        cxc = lerp(540, 540 - ((rx1 - rx0) * s) / 2 - 45, ease_io(prog(t, tw0, tw0 + 0.5)))
        draw_shape(cr, rs, cxc, 930, s, col, a, pop_k(t, b['start'] + 0.1, 0.5), glow=True)
        if t >= tw0:
            k = ease_out(prog(t, tw0, tw0 + 0.5)); rxc = cxc + (wkm * s) / 2 + ((rx1 - rx0) * s) / 2 + 90
            draw_shape(cr, refs, rxc, 930, s, (0.3, 0.75, 0.35) if ref == 'park' else (0.55, 0.6, 0.7), a * k, 1.0, outline=WHITE, lw=3)
            ptext(cr, 'CENTRAL PARK' if ref == 'park' else 'MANHATTAN', rxc, 930 - (ry1 - ry0) * s / 2 - 30, 34, WHITE, a * k, fam='Poppins ExtraBold', sw=6)
        scale_bar(cr, s, a, 1320)
    # header: rank, name, area, locator globe
    k = prog(t, b['start'], b['start'] + 0.25); sc = lerp(2.4, 1, ease_out(k))
    cr.save(); cr.translate(170, 230); cr.rotate(-0.08); cr.scale(sc, sc)
    cr.new_path(); cr.arc(0, 0, 105, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], a * clamp(k * 3)); cr.fill()
    ptext(cr, f'#{rank}', 0, 34, 100 if rank < 10 else 84, INK, a * clamp(k * 3), sw=0, shadow=False); cr.restore()
    tn = b['l0'] + 0.5
    cr.save(); cr.translate(570, 210); k2 = pop_k(t, tn); cr.scale(k2, k2)
    ptext(cr, name, 0, 0, fit(cr, name, 80, 560), WHITE, a, sw=10); cr.restore()
    if t >= tn + 0.4: chip(cr, ar, 570, 330, 56, col, INK, pop_k(t, tn + 0.4), a)
    lon0, lat0 = G.ll[key]
    if t >= b['start'] + 0.4:
        gk = pop_k(t, b['start'] + 0.4); globe(cr, 930, 470, 110 * gk, lon0, lat0, a)
    for i, (word, em, txt) in enumerate(facts):
        tf = w(key, word)
        chip(cr, txt, 540, 1420 + i * 120, 44, WHITE if i == 0 else col, INK, pop_k(t, tf), a, em=em)
    # countdown progress
    for i in range(10):
        r_ = 10 - i; x = 120 + i * 93; on = r_ == rank; done = r_ > rank
        cr.new_path(); cr.arc(x, 1880, 20 if on else 13, 0, 2 * math.pi)
        cr.set_source_rgba(*(col[:3] if on else ((0.9, 0.9, 0.95) if done else (0.3, 0.3, 0.38))), 1); cr.fill()

def draw_hook(cr, t):
    b = next((bt(k) for k in ('h1', 'h2', 'h3') if t < bt(k)['end']), None)
    if b is None or t >= bt('title')['start']: return False
    key = b['key']
    if key == 'h1':
        e = ENTRIES[9]; bg(cr, t, GOLD); rs = G.shape['m1']; x0, x1, y0, y1 = bounds(rs); s = 700 / (x1 - x0)
        draw_shape(cr, rs, 540, 1000, s, GOLD, 1, pop_k(t, 0.0, 0.35), glow=True)
        tw0 = w('h1', 'walk'); k = ease_io(prog(t, tw0, b['end'] + 0.2))
        emoji(cr, '🚶', lerp(160, 920, k), 1000 + 10 * math.sin(t * 14), 150, 1)
        mins = int(20 * k); ptext(cr, f'{mins} MIN', 540, 1420, 90, WHITE, clamp(prog(t, tw0, tw0 + 0.2)), sw=10)
        slam(cr, 'WALK ACROSS', 540, 250, 120, WHITE, t, w('h1', 'walk'))
        slam(cr, 'A WHOLE COUNTRY', 540, 390, 100, GOLD, t, w('h1', 'country'))
        scale_bar(cr, s, 1, 1550)
    elif key == 'h2':
        bg(cr, t, CORAL); rs = G.shape['m2']; x0, x1, y0, y1 = bounds(rs); px0, px1, py0, py1 = bounds(G.park)
        s = min(560 / (y1 - y0 + 0.5), 900 / ((x1 - x0) + (px1 - px0) + 0.6))
        draw_shape(cr, rs, 330, 1000, s, CORAL, 1, pop_k(t, b['start'], 0.35), glow=True)
        tp = w('h2', 'Central')
        if t >= tp - 0.2:
            draw_shape(cr, G.park, 760, 1000, s, (0.3, 0.75, 0.35), 1, pop_k(t, tp - 0.2, 0.4))
            ptext(cr, 'CENTRAL PARK', 760, 1000 + (py1 - py0) * s / 2 + 60, 40, WHITE, 1, sw=6)
        ptext(cr, 'THIS COUNTRY', 330, 1000 + (y1 - y0) * s / 2 + 60, 40, CORAL, 1, sw=6)
        slam(cr, 'SMALLER THAN', 540, 250, 120, WHITE, t, w('h2', 'smaller'))
        slam(cr, 'CENTRAL PARK', 540, 390, 120, (0.4, 0.85, 0.45), t, tp)
    else:
        bg(cr, t, LIME); rs = G.shape['m3']; x0, x1, y0, y1 = bounds(rs); s = 600 / (x1 - x0)
        draw_shape(cr, rs, 540, 1000, s, LIME, 1, pop_k(t, b['start'], 0.35), glow=True)
        tc = w('h3', 'capital')
        if t >= tc: emoji(cr, '❓', 540, 980, 260 * pop_k(t, tc), 1, rot=0.15 * math.sin(t * 5))
        slam(cr, 'NO CAPITAL', 540, 300, 150, LIME, t, w('h3', 'official'))
    fl = 1 - prog(t, b['start'], b['start'] + 0.15)
    if key != 'h1' and 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.55 * fl); cr.paint()
    return True

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end'] + 0.1): return False
    bg(cr, t, GOLD)
    # all ten, true size relative to each other, popping in a row from largest to smallest
    s = 0.009 * 60
    for i, e in enumerate(ENTRIES):
        rs = G.shape[e[1]]; tk = b['start'] + 0.15 + i * 0.12
        if t < tk: continue
        x0, x1, y0, y1 = bounds(rs)
        x, y = 160 + (i % 5) * 190, 1180 + (i // 5) * 280
        sc = min(150 / max(x1 - x0, y1 - y0), 6.0)
        draw_shape(cr, rs, x, y, sc, e[5], 1, pop_k(t, tk, 0.35), lw=2)
        ptext(cr, f'#{e[0]}', x, y + 115, 34, WHITE, 1, sw=5)
    k = pop_k(t, w('title', 'ten') - 0.1); cr.save(); cr.translate(540, 380); cr.scale(k, k); ptext(cr, 'THE 10', 0, 0, 170, GOLD, 1, sw=16); cr.restore()
    slam(cr, 'SMALLEST COUNTRIES', 540, 560, 96, WHITE, t, w('title', 'smallest'))
    slam(cr, 'ON EARTH', 540, 690, 96, WHITE, t, w('title', 'Earth'))
    fl = 1 - prog(t, b['start'], b['start'] + 0.15)
    if 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.55 * fl); cr.paint()
    return True

def draw_cta(cr, t):
    b = bt('cta'); bg(cr, t, GOLD)
    for i, e in enumerate(ENTRIES):
        rs = G.shape[e[1]]; x0, x1, y0, y1 = bounds(rs); x, y = 160 + (i % 5) * 190, 1030 + (i // 5) * 250
        sc = min(140 / max(x1 - x0, y1 - y0), 6.0); draw_shape(cr, rs, x, y, sc, e[5], 1, pop_k(t, b['start'] + i * 0.06, 0.3), lw=2)
        ptext(cr, e[3].split()[0][:9], x, y + 100, 26, WHITE, 1, fam='Poppins ExtraBold', sw=5)
    k = pop_k(t, w('cta', 'Which')); cr.save(); cr.translate(540, 470); cr.scale(k, k)
    ptext(cr, 'WHICH ONE WOULD', 0, 0, 90, WHITE, 1, sw=11); ptext(cr, 'YOU VISIT?', 0, 140, 150, GOLD, 1, sw=14); cr.restore()
    tc = w('cta', 'comments')
    if t >= tc: k = pop_k(t, tc); cr.save(); cr.translate(540, 800); cr.scale(k, k); ptext(cr, 'COMMENT BELOW', -50, 0, 66, WHITE, 1, sw=9); emoji(cr, '👇', 330, -20, 80, 1); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1800); cr.scale(k, k); txt = 'FOLLOW FOR MORE'; wd = tw(cr, txt, 56)
        rrect(cr, -wd / 2 - 90, -62, wd + 180, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 56, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 66, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def render_frame(cr, t):
    global time_now
    time_now = t
    if draw_hook(cr, t) or draw_title(cr, t):
        C.draw_captions(cr, t, 1700); return
    if t >= bt('cta')['start']: draw_cta(cr, t); C.draw_captions(cr, t, 1640)
    else:
        e = next((e for e in ENTRIES if bt(e[1])['start'] <= t < bt(e[1])['end']), ENTRIES[-1])
        draw_entry(cr, t, e); C.draw_captions(cr, t, 1720)
        fl = 1 - prog(t, bt(e[1])['start'], bt(e[1])['start'] + 0.15)
        if 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.45 * fl); cr.paint()
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR; rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 118; bar = beat * 4
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G: upbeat countdown
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar * 1.2 * SR)) / SR; env = np.minimum(1, Lc / 0.2) * np.exp(-Lc * 0.8)
        put(music, ci * bar, sum(0.025 * np.sin(2 * np.pi * note(m) * Lc) for m in ch) * env)
        put(music, ci * bar, 0.08 * np.sin(2 * np.pi * note(ch[0] - 24) * Lc) * env)
        for j in range(8):
            m = ch[j % 3] + 12 + (12 if j % 4 == 3 else 0); P = np.arange(int(0.2 * SR)) / SR
            put(music, ci * bar + j * beat / 2, 0.028 * np.sign(np.sin(2 * np.pi * note(m) * P)) * np.exp(-P * 18))
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 > bt('cta')['start'] + 3: break
        Ld = np.arange(int(0.35 * SR)) / SR; put(music, t0, 0.35 * np.sin(2 * np.pi * np.cumsum(55 + 70 * np.exp(-Ld * 22)) / SR) * np.exp(-Ld * 9))
        M = np.arange(int(0.05 * SR)); put(music, t0 + beat / 2, 0.05 * rng.standard_normal(len(M)) * np.exp(-M / SR * 60))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.6):
        Lb = np.arange(int(1.6 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-Lb * 10)) / SR) * np.exp(-Lb * 2.8))
    def whoosh(t0, amp=0.22):
        nz = rng.standard_normal(int(0.5 * SR)); env = np.linspace(0, 1, len(nz)) ** 2; put(fx, t0, amp * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def ding(t0, amp=0.12):
        Ld = np.arange(int(0.8 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * 1318 * Ld) + 0.5 * np.sin(2 * np.pi * 1976 * Ld)) * np.exp(-Ld * 5))
    for key, word in (('h1', 'walk'), ('h2', 'Central'), ('h3', 'capital'), ('title', 'ten')): boom(w(key, word), 0.7)
    for e in ENTRIES:
        b = bt(e[1]); whoosh(b['start'] - 0.45); boom(b['start'] + 0.05, 0.55 if e[0] > 1 else 0.9)
        for word, _, _ in e[8]: ding(w(e[1], word), 0.08)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_small'))
    print(f"duration {C.TL['dur']:.1f}s")
    for b in C.TL['beats']: print(f"  {b['key']:8s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','): render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]; make_audio(C.TL, base + '.wav')
    nfr = int(C.TL['dur'] * FPS); workers = os.cpu_count() or 4
    bounds_ = np.linspace(0, nfr, workers * 3 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds_[:-1], bounds_[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
