"""'Kiribati: the Loneliest Country on Earth' (9:16). 33 atolls across the Pacific, all four hemispheres, first New Year, history,
and the rising sea. Word-synced map video (engine from china.py).
Usage: python3 kir.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
from china import R, ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON, PARCH, laea, S, L, path_xy
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

R.LON0, R.LAT0 = 180.0, 0.0
R.MAPY = 980
TEAL, SKY, CORAL, SAND, BLUE = hexc('#2EC4B6'), hexc('#7FD8FF'), hexc('#FF6B6B'), hexc('#F2D59B'), hexc('#4FA3D9')
C.SAY = {None: {'Kiribati': 'Kiribass', "Kiribati's": "Kiribass's", 'Kiritimati': 'Kirismas', 'Gilberts': 'Gilberts'}}
C.HOT = ('kiribati', 'pacific', 'ocean', 'india', 'hong', 'kong', 'tarawa', 'kiritimati', 'christmas', 'fiji', 'hemispheres', 'year',
         'islands', 'sea', 'disappear', 'loneliest', 'gilbert', 'gilberts', '1943', '1979', '1995', '2014')
C.TAIL_OVERRIDE = {'h1': 0.35, 'h2': 0.35, 'h3': 0.4}
BEATS = [
    ('h1', "This country is spread across an ocean area bigger than India...", None, None, None, None, None),
    ('h2', "but all its land put together is smaller than Hong Kong.", None, None, None, None, None),
    ('h3', "It's the first country to see every new year... and it could be one of the first to disappear.", None, None, None, None, None),
    ('title', "Welcome to Kiribati: the loneliest country on Earth.", None, None, None, None, None),
    ('where', "Kiribati is thirty-three coral islands, scattered across the middle of the Pacific. From one end to the other is over four thousand kilometres.",
     None, None, None, ('I', 'WHERE ON EARTH?'), None),
    ('hemi', "It's the only country in all four hemispheres: north, south, east and west.", None, None, None, None, None),
    ('far', "Most of it is thousands of kilometres from any continent. Hawaii is closer to some of its islands than its own capital is.", None, None, None, None, None),
    ('year', "In 1995, Kiribati moved the International Date Line, so all its islands could share the same day. Now its Line Islands are the first place on Earth to see each new year.",
     None, None, None, ('II', 'FIRST INTO TOMORROW'), None),
    ('xmas', "And Kiritimati, also called Christmas Island, is the largest coral atoll on Earth by land area.", None, None, None, None, None),
    ('hist', "People first reached these islands by canoe, long before Europeans. Later they became the British Gilbert Islands. In 1943, Tarawa saw one of the bloodiest battles of the Pacific War.",
     None, None, None, ('III', 'HISTORY'), None),
    ('name', "In 1979, the country became independent, as Kiribati: the local way of writing Gilberts. That's why it's pronounced Kiribass.", None, None, None, None, None),
    ('sea', "But most of Kiribati is only a few metres above the sea. As sea levels rise, floods and salt water already threaten homes and drinking water.",
     None, None, None, ('IV', 'THE RISING SEA'), None),
    ('fiji', "In 2014, Kiribati even bought land in Fiji, about two thousand kilometres away, as a backup for its food supply.", None, None, None, None, None),
    ('today', "Today, about a hundred and thirty thousand people call Kiribati home, and half of them live on one tiny strip of land: South Tarawa.", None, None, None, None, None),
    ('cta', "Would you live on an island in the middle of the Pacific? Tell us in the comments, and follow for more.", None, None, None, None, None),
]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2', 'h3')
bt, w, win = C.bt, C.w, C.win
G = None
FULL = (-178, -1, 0.115)
CAMS = {'far': (-175, 2, 0.075), 'year': (-170, 0, 0.1), 'xmas': (-157.4, 1.9, 1.6), 'hist': (173.0, 1.4, 1.1), 'sea': (173.0, 1.4, 1.1),
        'fiji': (176, -7.5, 0.16), 'today': (173.0, 1.4, 1.1)}
ATOLLS = {'gilbert': [(172.98, 3.07), (172.79, 3.07), (173.28, 2.0), (172.95, 1.8), (173.0, 1.42), (173.0, 0.92), (173.85, 0.4), (173.4, 0.23),
                      (173.62, 0.18), (174.38, -0.65), (174.85, -1.3), (175.98, -1.33), (176.45, -1.37), (175.55, -1.8), (175.97, -2.5), (176.83, -2.65),
                      (169.53, -0.87)],
          'phoenix': [(-171.72, -2.8), (-171.08, -3.13), (-171.52, -3.58), (-170.71, -3.72), (-171.25, -4.45), (-174.13, -3.6), (-172.2, -4.5), (-174.53, -4.67)],
          'line': [(-160.4, 4.68), (-159.35, 3.86), (-157.4, 1.87), (-154.93, -4.0), (-155.88, -5.62), (-150.22, -9.94), (-152.31, -10.06), (-151.82, -11.43)]}
ALL = [p for g in ('gilbert', 'phoenix', 'line') for p in ATOLLS[g]]
EEZ = [('gilbert', (173.8, 0.2), 578), ('phoenix', (-172.3, -3.8), 492), ('line', (-155.5, -3.0), 722)]  # equal-area circles of each zone
IDL = [(180, 50), (180, 10), (-162, 10), (-148, 7), (-148, -12), (-172.5, -12), (-172.5, -16), (-180, -16), (180, -50)]
TARAWA = (172.98, 1.33); KIRIT = (-157.4, 1.87); VANUALEVU = (179.3, -16.6); HAWAII = (-155.5, 19.6)

class Geo:
    def __init__(self, d):
        self.land = [laea(r[:, 0] % 360, r[:, 1]) for f in json.load(open(os.path.join(d, 'ne_50m_land.geojson')))['features']
                     for r in rings(f['geometry']) if len(r) > 3 and -60 < r[:, 1].mean() < 60]
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        def raw(n, keep=lambda r: True): return [r for r in rings(cf[n]['geometry']) if len(r) > 3 and keep(r)]
        self.india = raw('India'); self.hk = raw('Hong Kong')
        ki = raw('Kiribati') if 'Kiribati' in cf else []
        self.kland = [laea(r[:, 0], r[:, 1]) for r in ki]

def camera(t):
    cur = FULL
    for k, cam in CAMS.items():
        b = bt(k); a = ease_io(prog(t, b['start'], b['start'] + 1.2)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'] + 1.0)))
        if a > 0: cur = (lerp(cur[0], cam[0] if abs(cam[0] - cur[0]) < 180 else cam[0] + (360 if cam[0] < cur[0] else -360), a),
                         lerp(cur[1], cam[1], a), math.exp(lerp(math.log(cur[2]), math.log(cam[2]), a)))
    x, y = laea(cur[0], cur[1]); return float(x), float(y), cur[2] * (1 + 0.015 * math.sin(t * 0.4))

def moved(shapes, src, dst):
    lon0, lat0 = R.LON0, R.LAT0; R.LON0, R.LAT0 = src
    loc = [laea(r[:, 0], r[:, 1]) for r in shapes]
    R.LON0, R.LAT0 = lon0, lat0; dx, dy = laea(*dst)
    return [(x + float(dx), y + float(dy)) for x, y in loc]

def label(cr, cam, lon, lat, txt, size, col, a, t0, t):
    if t < t0 or a <= 0: return
    k = pop_k(t, t0); x, y = L(cam, lon, lat); cr.save(); cr.translate(x, y); cr.scale(k, k)
    ptext(cr, txt, 0, 0, size, col, a, fam='Poppins ExtraBold', sw=7); cr.restore()

def eez(cr, cam, a, t0=None, t=0.0):
    if a <= 0: return
    for i, (g, (lon, lat), rkm) in enumerate(EEZ):
        k = 1.0 if t0 is None else ease_out(prog(t, t0 + i * 0.2, t0 + i * 0.2 + 0.6))
        x, y = L(cam, lon, lat); r = rkm * cam[2] * k
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*TEAL[:3], 0.3 * a); cr.fill_preserve()
        cr.set_dash([12, 8]); cr.set_source_rgba(*TEAL[:3], 0.9 * a); cr.set_line_width(3); cr.stroke(); cr.set_dash([])

def atolls(cr, cam, a, t=0.0, t0=None, t1=None, glow=1.0):
    if a <= 0: return
    n = len(ALL)
    for i, (lon, lat) in enumerate(ALL):
        ts = None if t0 is None else lerp(t0, t1, i / (n - 1))
        if ts is not None and t < ts: continue
        k = 1.0 if ts is None else pop_k(t, ts, 0.3); x, y = L(cam, lon, lat); r = max(5, 3 + cam[2] * 6) * k
        cr.new_path(); cr.arc(x, y, r * 2.4, 0, 2 * math.pi); cr.set_source_rgba(1, 0.9, 0.4, 0.25 * a * glow); cr.fill()
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 0.92, 0.45, a); cr.fill_preserve()
        cr.set_source_rgba(0, 0, 0, 0.5 * a); cr.set_line_width(1.5); cr.stroke()

def atoll_ring(cr, x, y, rx, ry, a, rot=0.0, water=0.0):
    """A stylised atoll: a ring of sand and palms around a turquoise lagoon."""
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(rx, ry); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgba(*SAND[:3], a); cr.fill()
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(rx * 0.8, ry * 0.72); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgba(0.35, 0.85, 0.85, a); cr.fill()

def draw_base(cr, cam, t):
    cr.set_source_rgb(0.02, 0.1, 0.2); cr.paint()
    g = cairo.RadialGradient(W / 2, R.MAPY, 100, W / 2, R.MAPY, 1300); g.add_color_stop_rgba(0, 0.06, 0.32, 0.5, 1); g.add_color_stop_rgba(1, 0.02, 0.08, 0.18, 1)
    cr.set_source(g); cr.paint()
    cr.new_path(); path_xy(cr, cam, G.land); cr.set_source_rgb(0.24, 0.27, 0.25); cr.fill()

def draw_story(cr, cam, t):
    # ----- hook -----
    a = win('h1', t=t)
    if a > 0:
        eez(cr, cam, a, w('h1', 'spread') - 0.2, t); atolls(cr, cam, a, t, 0.05, 0.9)
        ti = w('h1', 'India')
        if t >= ti:  # India at true size, beside the zones
            k = ease_out(prog(t, ti, ti + 0.5)); sh = moved(G.india, (79, 22), (-172, 17))
            cr.new_path(); path_xy(cr, cam, sh); cr.save(); cr.translate(0, (1 - k) * -500)
            cr.set_source_rgba(1, 0.6, 0.2, 0.75 * a * k); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a * k); cr.set_line_width(3); cr.stroke(); cr.restore()
            label(cr, cam, -172, 17, 'INDIA', 44, WHITE, a, ti + 0.3, t)
            label(cr, cam, -172, 13.5, '3.3M KM²', 36, WHITE, a, ti + 0.4, t)
        tw0 = w('h1', 'spread')
        chip(cr, "KIRIBATI'S WATERS: 3.4M KM²", 540, 1430, 50, (0.18, 0.77, 0.71), INK, pop_k(t, tw0 + 0.6), a, em='🌊')
        if t < w('h1', 'ocean'): slam(cr, 'THIS COUNTRY...', 540, 320, 120, WHITE, t, 0.02, a)
        else: slam(cr, 'AN OCEAN AREA', 540, 250, 110, WHITE, t, w('h1', 'ocean'), a)
        slam(cr, 'BIGGER THAN INDIA', 540, 390, 100, (1, 0.6, 0.2), t, ti, a)
    a = win('h2', t=t)
    if a > 0:
        cr.set_source_rgba(0.02, 0.1, 0.2, 0.85 * a); cr.paint()
        th = w('h2', 'Hong')
        # all of Kiribati's land (811 km²) as one square vs Hong Kong (1,106 km²), to scale
        s = 15.0  # px per km at this zoom
        for lab, area, col, x, t0 in (('KIRIBATI 811 KM²', 811, SAND, 300, w('h2', 'land')), ('HONG KONG 1,106 KM²', 1106, CORAL, 780, th)):
            if t < t0: continue
            k = pop_k(t, t0); side = math.sqrt(area) * s * k
            rrect(cr, x - side / 2, 1050 - side / 2, side, side, 12); cr.set_source_rgba(*col[:3], a); cr.fill()
            ptext(cr, lab, x, 1050 + side / 2 + 60, 40, WHITE, a * k, sw=6)
        slam(cr, 'ALL ITS LAND', 540, 300, 110, WHITE, t, w('h2', 'land'), a)
        slam(cr, '< HONG KONG', 540, 450, 130, CORAL, t, th, a)
    a = win('h3', 'title', t=t)
    if a > 0:
        atolls(cr, cam, a)
        tn = w('h3', 'new')
        if t >= tn:
            for i, (dx, dy) in enumerate(((-200, -40), (180, -90), (40, 60), (-80, 120), (230, 80))):
                emoji(cr, '🎆', 540 + dx, 900 + dy, 120 * pop_k(t, tn + i * 0.07), a * (1 - prog(t, w('h3', 'disappear') - 0.5, w('h3', 'disappear'))))
        td = w('h3', 'disappear')
        if t >= td and bt('h3')['start'] <= t < bt('title')['start']:
            k = ease_out(prog(t, td, td + 1.0)); cr.rectangle(0, lerp(H, 980, k), W, H); cr.set_source_rgba(0.1, 0.4, 0.75, 0.75 * a); cr.fill()
            emoji(cr, '🌊', 540, lerp(H, 1000, k), 200, a)
        if bt('h3')['start'] <= t < bt('title')['start']:
            slam(cr, 'FIRST NEW YEAR', 540, 250, 120, GOLD, t, w('h3', 'first'), a)
            slam(cr, 'FIRST TO DISAPPEAR?', 540, 400, 100, SKY, t, td, a)
    # ----- where -----
    a = win('where', t=t)
    if a > 0:
        tt = w('where', 'thirty'); atolls(cr, cam, a, t, tt, tt + 1.4)
        n = int(33 * clamp(prog(t, tt, tt + 1.4))) if t >= tt else 0
        if t >= tt: slam(cr, f'{max(n, 1)} ISLANDS', 540, 300, 120, GOLD, tt, tt, a) if False else slam(cr, f'{max(n, 1)} ISLANDS', 540, 300, 120, GOLD, t, tt, a)
        to = w('where', 'end')
        if t >= to:
            k = ease_io(prog(t, to, to + 1.0)); (x0, y0), (x1, y1) = L(cam, 169.53, -0.87), L(cam, lerp(169.53, 209.78, k), lerp(-0.87, -9.94, k))
            cr.new_path(); cr.move_to(x0, y0 + 60); cr.line_to(x1, y1 + 60); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(5); cr.stroke()
        chip(cr, '4,000+ KM ACROSS', 540, 1420, 56, WHITE, INK, pop_k(t, w('where', 'four')), a, em='📏')
        for nm, lon, lat, word in (('GILBERT IS.', 174, 4.5, 'scattered'), ('PHOENIX IS.', -172.5, -7, 'scattered'), ('LINE IS.', -150, 3, 'scattered')):
            label(cr, cam, lon, lat, nm, 32, WHITE, a, w('where', word) + 0.3, t)
    a = win('hemi', t=t)
    if a > 0:
        atolls(cr, cam, a)
        te, tm = w('hemi', 'north'), w('hemi', 'east')
        k = ease_io(prog(t, te - 0.3, te + 0.6)); X, Y = L(cam, np.linspace(160, 220, 40), np.zeros(40))
        cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(p, q) for p, q in zip(X[1:int(1 + 39 * k)], Y[1:int(1 + 39 * k)])]
        cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(5); cr.stroke()
        k = ease_io(prog(t, tm - 0.3, tm + 0.6)); X, Y = L(cam, np.full(40, 180.0), np.linspace(25, -25, 40))
        cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(p, q) for p, q in zip(X[1:int(1 + 39 * k)], Y[1:int(1 + 39 * k)])]
        cr.set_source_rgba(*CORAL[:3], a); cr.set_line_width(5); cr.stroke()
        for txt, lon, lat, word in (('N', -165, 9, 'north'), ('S', -165, -9, 'south'), ('E', 168, -14, 'east'), ('W', -165, -14, 'west')):
            label(cr, cam, lon, lat, txt, 70, WHITE, a, w('hemi', word), t)
        chip(cr, 'ALL 4 HEMISPHERES', 540, 1420, 60, GOLD, INK, pop_k(t, w('hemi', 'four')), a, em='🌐')
    a = win('far', t=t)
    if a > 0:
        atolls(cr, cam, a)
        for nm, (lon, lat), word in (('HAWAII', HAWAII, 'Hawaii'), ('AUSTRALIA', (147, -24), 'continent')):
            label(cr, cam, lon, lat + 3, nm, 40, WHITE, a, w('far', word), t)
        th = w('far', 'Hawaii')
        R.route(cr, cam, [KIRIT, ((KIRIT[0] + HAWAII[0]) / 2 - 1.5, 11), HAWAII], ease_io(prog(t, th, th + 0.7)), SKY, width=5, dashed_rest=False)
        R.route(cr, cam, [KIRIT, (-170, 4), (TARAWA[0] + 360 - 360, 1.33)], ease_io(prog(t, w('far', 'capital'), w('far', 'capital') + 0.9)), CORAL, width=5, dashed_rest=False)
        if t >= w('far', 'capital'):
            label(cr, cam, -170, 13, '~2,000 KM', 34, SKY, a, th + 0.5, t); label(cr, cam, -166, -1.5, '~3,300 KM', 34, CORAL, a, w('far', 'capital') + 0.6, t)
            C.pin(cr, cam, TARAWA, 'TARAWA (CAPITAL)', t, w('far', 'capital'), CORAL, 'b', 30, a)
    # ----- first into tomorrow -----
    a = win('year', t=t)
    if a > 0:
        atolls(cr, cam, a)
        t95 = w('year', '1995'); tm = w('year', 'moved')
        X, Y = L(cam, np.full(30, 180.0), np.linspace(40, -40, 30))
        cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(p, q) for p, q in zip(X[1:], Y[1:])]
        cr.set_dash([14, 10]); cr.set_source_rgba(1, 1, 1, 0.6 * a * (1 - ease_io(prog(t, tm, tm + 0.8)))); cr.set_line_width(4); cr.stroke(); cr.set_dash([])
        if t >= tm:
            k = ease_io(prog(t, tm, tm + 1.2)); pts = [(lerp(180, p[0] % 360, k), p[1]) for p in IDL]
            X, Y = L(cam, np.array([p[0] for p in pts]), np.array([p[1] for p in pts]))
            cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(p, q) for p, q in zip(X[1:], Y[1:])]
            cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(6); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
            label(cr, cam, -147, 20, 'DATE LINE', 36, GOLD, a, tm + 0.6, t)
        chip(cr, '1995 · ONE COUNTRY, ONE DAY', 540, 1300, 46, WHITE, INK, pop_k(t, t95), a, em='📅')
        tf = w('year', 'first')
        if t >= tf:
            for i in range(6):
                x, y = L(cam, -157 + (i % 3) * 3 - 3, 5 + (i // 3) * 5); emoji(cr, '🎆', x, y, 90 * pop_k(t, tf + i * 0.08), a)
            chip(cr, 'UTC+14: FIRST NEW YEAR ON EARTH', 540, 1440, 44, GOLD, INK, pop_k(t, tf), a, em='🥂')
    a = win('xmas', t=t)
    if a > 0:
        tk = w('xmas', 'Kiritimati')
        if t >= tk:
            k = pop_k(t, tk, 0.6); x, y = L(cam, *KIRIT)
            atoll_ring(cr, x, y, 260 * k, 190 * k, a, 0.3)
            for i in range(8):
                ang = i / 8 * 2 * math.pi; emoji(cr, '🌴', x + 245 * k * math.cos(ang) * 0.95, y + 180 * k * math.sin(ang) * 0.9, 50 * k, a)
        slam(cr, 'KIRITIMATI', 540, 300, 120, GOLD, t, tk, a)
        chip(cr, '"CHRISTMAS ISLAND"', 540, 420, 44, WHITE, INK, pop_k(t, w('xmas', 'Christmas')), a, em='🎄')
        chip(cr, 'LARGEST CORAL ATOLL BY LAND', 540, 1440, 48, SAND, INK, pop_k(t, w('xmas', 'largest')), a)
    # ----- history -----
    a = win('hist', t=t)
    if a > 0:
        x, y = L(cam, *TARAWA); atoll_ring(cr, x, y + 40, 120, 260, a, -0.5)
        tc = w('hist', 'canoe')
        R.route(cr, cam, [(171.0, 2.4), (172.0, 1.9), TARAWA], ease_io(prog(t, tc - 0.4, tc + 0.8)), WHITE, width=4, head='🛶', head_size=80, dashed_rest=False)
        chip(cr, 'GILBERT ISLANDS (BRITISH)', 540, 1300, 46, WHITE, INK, pop_k(t, w('hist', 'British')), a, em='⛵')
        t43 = w('hist', '1943')
        if t >= t43:
            emoji(cr, '⚔️', x + 160, y - 80, 110 * pop_k(t, t43), a)
            chip(cr, '1943 · BATTLE OF TARAWA', 540, 1440, 52, CORAL, WHITE, pop_k(t, t43), a)
    a = win('name', t=t)
    if a > 0:
        cr.set_source_rgba(0.02, 0.08, 0.16, 0.8 * a); cr.paint()
        slam(cr, '1979: INDEPENDENCE', 540, 520, 96, GOLD, t, w('name', '1979'), a)
        tg = w('name', 'Gilberts')
        if t >= tg:
            k = pop_k(t, tg); cr.save(); cr.translate(540, 860); cr.scale(k, k)
            ptext(cr, 'GILBERTS', 0, 0, 90, WHITE, a, sw=10); ptext(cr, '=', 0, 100, 80, GOLD, a, sw=8); ptext(cr, 'KIRIBATI', 0, 200, 110, SKY, a, sw=12); cr.restore()
        tp = w('name', 'pronounced')
        if t >= tp:
            k = pop_k(t, tp); cr.save(); cr.translate(540, 1300); cr.scale(k, k); txt = 'SAY: "KIRI-BASS"'; wd = tw(cr, txt, 70)
            rrect(cr, -wd / 2 - 60, -80, wd + 120, 120, 60); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
            ptext(cr, txt, 0, 4, 70, INK, a, sw=0, shadow=False); emoji(cr, '🗣️', -wd / 2 - 20, -20, 80, a); cr.restore()
    # ----- the rising sea -----
    a = win('sea', t=t)
    if a > 0:
        cr.set_source_rgba(0.02, 0.06, 0.12, 0.85 * a); cr.paint()
        tr = w('sea', 'rise'); lvl = ease_io(prog(t, tr - 0.5, w('sea', 'water', n=1, end=True) if True else tr + 2))
        # cross-section of an atoll: ~3 m high, the sea creeping up
        base = 1250; cr.new_path(); cr.move_to(80, base); cr.curve_to(250, base - 170, 830, base - 170, 1000, base); cr.close_path()
        cr.set_source_rgba(*SAND[:3], a); cr.fill()
        for x in (330, 560, 760): emoji(cr, '🌴', x, base - 230, 110, a)
        emoji(cr, '🏠', 450, base - 175, 90, a); emoji(cr, '🏠', 660, base - 178, 80, a)
        sea = base - 40 - 110 * lvl
        cr.rectangle(0, sea, W, H - sea); cr.set_source_rgba(0.15, 0.5, 0.85, 0.75 * a); cr.fill()
        X = np.linspace(0, W, 60); cr.new_path(); cr.move_to(0, sea)
        for xx in X: cr.line_to(xx, sea + 8 * math.sin(xx / 40 + t * 4))
        cr.set_source_rgba(1, 1, 1, 0.8 * a); cr.set_line_width(4); cr.stroke()
        chip(cr, 'ONLY A FEW METRES ABOVE THE SEA', 540, 560, 44, SKY, INK, pop_k(t, w('sea', 'metres')), a, em='📏')
        tf = w('sea', 'floods')
        if t >= tf: chip(cr, 'FLOODS · SALT WATER IN WELLS', 540, 700, 46, CORAL, WHITE, pop_k(t, tf), a, em='⚠️')
    a = win('fiji', t=t)
    if a > 0:
        tb = w('fiji', 'bought')
        R.route(cr, cam, [TARAWA, (177.5, -7), VANUALEVU], ease_io(prog(t, tb - 0.2, tb + 1.0)), GOLD, width=6, arrow=True, dashed_rest=False)
        C.pin(cr, cam, VANUALEVU, 'FIJI (VANUA LEVU)', t, w('fiji', 'Fiji'), GOLD, 'b', 34, a)
        C.pin(cr, cam, TARAWA, 'TARAWA', t, bt('fiji')['l0'], CORAL, 'r', 34, a)
        label(cr, cam, 179, -6.5, '~2,000 KM', 40, GOLD, a, w('fiji', 'two'), t)
        chip(cr, '2014 · ~20 KM² OF FARMLAND', 540, 1440, 50, GOLD, INK, pop_k(t, w('fiji', 'food')), a, em='🌾')
    a = win('today', t=t)
    if a > 0:
        x, y = L(cam, *TARAWA); atoll_ring(cr, x, y + 40, 120, 260, a, -0.5)
        ts = w('today', 'South')
        if t >= ts:
            cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.new_path(); cr.arc(x, y + 40, 125, 1.0, 2.3)
            cr.set_source_rgba(*CORAL[:3], a * (0.6 + 0.4 * math.sin(t * 6))); cr.set_line_width(26); cr.stroke()
            label(cr, cam, TARAWA[0] + 0.05, TARAWA[1] - 0.32, 'SOUTH TARAWA', 44, CORAL, a, ts, t)
        chip(cr, '~130,000 PEOPLE', 540, 1300, 56, WHITE, INK, pop_k(t, w('today', 'hundred')), a, em='👥')
        chip(cr, '~HALF ON ONE STRIP OF LAND', 540, 1440, 50, CORAL, WHITE, pop_k(t, w('today', 'half')), a)

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end'] + 0.2): return
    a = 1 - ease_io(prog(t, b['end'] - 0.25, b['end'] + 0.2))
    cr.set_source_rgba(0.01, 0.05, 0.1, 0.55 * a); cr.paint()
    k = pop_k(t, w('title', 'Welcome') - 0.1); cr.save(); cr.translate(540, 560); cr.scale(k, k); ptext(cr, 'WELCOME TO', 0, 0, 80, WHITE, a, sw=10); cr.restore()
    slam(cr, 'KIRIBATI', 540, 760, 200, SKY, t, w('title', 'Kiribati'), a)
    slam(cr, 'THE LONELIEST COUNTRY', 540, 920, 84, GOLD, t, w('title', 'loneliest'), a)
    slam(cr, 'ON EARTH', 540, 1030, 84, GOLD, t, w('title', 'Earth'), a)

def draw_cta(cr, t):
    b = bt('cta')
    if t < b['start']: return
    a = ease_out(prog(t, b['start'], b['start'] + 0.4))
    cr.set_source_rgba(0.01, 0.05, 0.1, 0.65 * a); cr.paint()
    k = pop_k(t, w('cta', 'Would')); cr.save(); cr.translate(540, 500); cr.scale(k, k)
    ptext(cr, 'WOULD YOU LIVE', 0, 0, 84, WHITE, a, sw=10); ptext(cr, 'ON AN ISLAND HERE?', 0, 120, 90, SKY, a, sw=11); cr.restore()
    for i, (txt, col, d) in enumerate((('YES 🏝️', (0.3, 0.8, 0.4), 0.3), ('NO WAY', (0.9, 0.3, 0.3), 0.45))):
        if t < w('cta', 'Pacific') + d: continue
        kk = pop_k(t, w('cta', 'Pacific') + d) * (1 + 0.03 * math.sin(t * 6 + i)); cr.save(); cr.translate(310 + i * 460, 860); cr.scale(kk, kk)
        rrect(cr, -190, -70, 380, 140, 70); cr.set_source_rgba(*col, 1); cr.fill(); ptext(cr, txt.split()[0] if i == 0 else txt, 0, 26, 72, WHITE, 1, sw=8); cr.restore()
    tc = w('cta', 'comments')
    if t >= tc: k = pop_k(t, tc); cr.save(); cr.translate(540, 1060); cr.scale(k, k); ptext(cr, 'COMMENT BELOW', -50, 0, 66, WHITE, 1, sw=9); emoji(cr, '👇', 330, -20, 80, 1); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1240); cr.scale(k, k); txt = 'FOLLOW FOR MORE'; wd = tw(cr, txt, 56)
        rrect(cr, -wd / 2 - 90, -62, wd + 180, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 56, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 66, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def render_frame(cr, t):
    cam = camera(t)
    draw_base(cr, cam, t)
    if t >= bt('cta')['start']: eez(cr, cam, 1); atolls(cr, cam, 1)
    C.vignette(cr, 0.6)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0, 0.7); g.add_color_stop_rgba(1, 0, 0, 0, 0); cr.set_source(g); cr.paint()
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
    music = np.zeros(n); beat = 60 / 92; bar = beat * 4
    nz = np.convolve(rng.standard_normal(n), np.ones(400) / 400, 'same')  # ocean surf under everything
    music += 0.6 * nz * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 7.0) ** 2)
    chords = [[55, 59, 62, 66], [52, 55, 59, 62], [48, 52, 55, 59], [50, 54, 57, 60]]  # G maj7, Em7, C maj7, D: warm island colours
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar * 1.3 * SR)) / SR; env = np.minimum(1, Lc / 0.4) * np.exp(-Lc * 0.6)
        put(music, ci * bar, sum(0.025 * np.sin(2 * np.pi * note(m) * Lc) for m in ch) * env)
        for j in range(8):  # ukulele-ish plucks
            m = ch[[0, 2, 1, 3, 2, 1, 3, 2][j]] + 12; P = np.arange(int(0.3 * SR)) / SR
            put(music, ci * bar + j * beat / 2, 0.03 * sum((1 / h) * np.sin(2 * np.pi * note(m) * h * P) for h in (1, 2, 3)) * np.exp(-P * 12))
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 > bt('cta')['start'] + 3: break
        if bi % 2 == 0 or t0 < bt('title')['start']:
            Ld = np.arange(int(0.4 * SR)) / SR; put(music, t0, 0.3 * np.sin(2 * np.pi * np.cumsum(55 + 60 * np.exp(-Ld * 20)) / SR) * np.exp(-Ld * 8))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.6):
        Lb = np.arange(int(1.8 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 80 * np.exp(-Lb * 10)) / SR) * np.exp(-Lb * 2.5))
    def pop(t0, amp=0.06):
        Lp = np.arange(int(0.05 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * 1000 * Lp) * np.exp(-Lp * 60))
    tt0 = w('where', 'thirty')
    for i in range(33): pop(tt0 + 1.4 * i / 32)
    for key, word in (('h1', 'India'), ('h2', 'Hong'), ('h3', 'disappear'), ('title', 'Kiribati'), ('hemi', 'four'), ('year', 'first'),
                      ('hist', '1943'), ('name', 'pronounced'), ('sea', 'rise'), ('fiji', 'bought')):
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_kir'))
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
