"""Why Does Europe Have So Many Countries? (9:16, British female voice).
Map story: same size as the USA -> 44 countries pop in -> mountains and peninsulas -> languages -> empires that fell apart
-> 1914/1920 -> the 1990s break-ups -> microstates -> recap. Everything fires on the narrator's spoken words (edge-tts boundaries).
Usage: python3 europe.py <data_dir> <out.mp4> [--preview t1,t2,...]
"""
import json, math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import vs
import space_choice as SC
from vs import ptext, rrect, tw, fit, face
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

def emoji(cr, e, *a, **k): vs.emoji(cr, e.replace('️', ''), *a, **k)

W, H, FPS = 1080, 1920, 30
MAPY = 840
SC.VOICE, SC.RATE = 'en-GB-SoniaNeural', '+6%'
WHITE, GOLD, CYAN, PINK, VIOLET = hexc('#FFFFFF'), hexc('#FFD60A'), hexc('#3DE0FF'), hexc('#FF4FA3'), hexc('#9B6BFF')
INK = (0.03, 0.02, 0.08)

BEATS = [
    ('hook', "Europe is about the same size as the United States... so why is it split into forty-four countries?"),
    ('land', "It starts with the land. Europe is carved up by mountains, like the Alps, the Pyrenees and the Carpathians."),
    ('seas', "And by seas, which break it into peninsulas: Iberia, Italy, the Balkans and Scandinavia."),
    ('walls', "These natural walls made it hard for any one ruler to control it all, so separate kingdoms grew up behind them."),
    ('lang', "Over the centuries, each region developed its own language. Romance in the south-west, Germanic in the north, Slavic in the east... plus Greek, Hungarian, Finnish and many more."),
    ('eu', "The European Union alone has twenty-four official languages."),
    ('empires', "Many tried to unite it. The Romans ruled the south and west. Charlemagne united much of the west. Napoleon marched all the way to Moscow."),
    ('fell', "But every one of those empires fell apart."),
    ('ww1', "After World War One, four great empires collapsed, and countries like Poland, Czechoslovakia and Yugoslavia appeared on the map."),
    ('ussr', "Then in the nineteen-nineties, the Soviet Union and Yugoslavia broke up, creating more than ten new countries."),
    ('tiny', "And some are tiny. San Marino says it has been independent since the year 301, and Vatican City could fit inside New York's Central Park about seven times."),
    ('why', "Mountains, seas, languages and history... that's why Europe has forty-four countries, while the US has just one."),
    ('cta', "Which country are you watching from? Drop your flag in the comments, and follow for more."),
]

# the 44 UN-recognised European states (Kosovo is drawn but not counted; see the posting kit)
COUNTED = ['ALB', 'AND', 'AUT', 'BLR', 'BEL', 'BIH', 'BGR', 'HRV', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'ISL', 'IRL',
           'ITA', 'LVA', 'LIE', 'LTU', 'LUX', 'MLT', 'MDA', 'MCO', 'MNE', 'NLD', 'MKD', 'NOR', 'POL', 'PRT', 'ROU', 'RUS', 'SMR', 'SRB',
           'SVK', 'SVN', 'ESP', 'SWE', 'CHE', 'UKR', 'GBR', 'VAT']
assert len(COUNTED) == 44
DEPEND = {'ALD': 'FIN', 'FRO': 'DNK', 'GGY': 'GBR', 'JEY': 'GBR', 'IMN': 'GBR'}
MICRO = ['VAT', 'SMR', 'MCO', 'LIE', 'AND', 'MLT', 'LUX']
PAL9 = [hexc(c) for c in ('#FF5A5F', '#3DA5FF', '#FFC93C', '#8CFF5A', '#B06BFF', '#FF8A3D', '#3DE0C8', '#FF4FA3', '#5A7BFF')]

FAM_COL = {'rom': (1.0, 0.6, 0.15), 'ger': (0.25, 0.6, 1.0), 'sla': (1.0, 0.32, 0.42), 'gre': (0.62, 0.42, 1.0),
           'ura': (0.45, 0.95, 0.45), 'bal': (0.2, 0.9, 0.85), 'alb': (1.0, 0.84, 0.2), 'mlt': (0.9, 0.9, 0.95)}
FAMILY = {}
for c in ('PRT', 'ESP', 'FRA', 'ITA', 'ROU', 'MDA', 'AND', 'MCO', 'SMR', 'VAT'): FAMILY[c] = ('rom', 'Romance')
for c in ('GBR', 'IRL', 'ISL', 'NOR', 'SWE', 'DNK', 'DEU', 'NLD', 'BEL', 'LUX', 'AUT', 'CHE', 'LIE'): FAMILY[c] = ('ger', 'Germanic')
for c in ('POL', 'CZE', 'SVK', 'SVN', 'HRV', 'BIH', 'SRB', 'MNE', 'MKD', 'BGR', 'UKR', 'BLR', 'RUS'): FAMILY[c] = ('sla', 'Slavic')
FAMILY.update({'GRC': ('gre', 'Greek'), 'HUN': ('ura', 'Hungarian'), 'FIN': ('ura', 'Finnish'), 'EST': ('ura', 'more'),
               'LVA': ('bal', 'more'), 'LTU': ('bal', 'more'), 'ALB': ('alb', 'more'), 'KOS': ('alb', 'more'), 'MLT': ('mlt', 'more')})
STRIPED = {'BEL': ('ger', 'rom'), 'CHE': ('ger', 'rom')}  # officially multilingual

# ---------- projection ----------
LON0, LAT0 = 15.0, 52.0
def laea(lon, lat):
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    l, p, p0 = np.radians(lon - LON0), np.radians(lat), math.radians(LAT0)
    cosc = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l)
    k = np.sqrt(2 / np.maximum(1 + cosc, 1e-9))
    return 6371 * k * np.cos(p) * np.sin(l), 6371 * k * (math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l))

def rings(geom):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    return [np.array(p[0], dtype=float) for p in polys]

def vec(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
def frame(lon, lat):
    lo, la = math.radians(lon), math.radians(lat)
    return (vec(lon, lat), np.array([-math.sin(lo), math.cos(lo), 0.0]),
            np.array([-math.sin(la) * math.cos(lo), -math.sin(la) * math.sin(lo), math.cos(la)]))
def move(r, src, dst):  # true-size move on the sphere, keeping north up at the centre
    v = vec(r[:, 0], r[:, 1]); c1, e1, n1 = frame(*src); c2, e2, n2 = frame(*dst)
    v2 = (v @ c1)[:, None] * c2 + (v @ e1)[:, None] * e2 + (v @ n1)[:, None] * n2
    return np.degrees(np.arctan2(v2[:, 1], v2[:, 0])), np.degrees(np.arcsin(np.clip(v2[:, 2], -1, 1)))

def inbox(r): return -40 < r[:, 0].mean() < 75 and 22 < r[:, 1].mean() < 84
def overlaps(r): return r[:, 0].min() < 75 and r[:, 0].max() > -40 and r[:, 1].max() > 22 and r[:, 1].min() < 84

class Geo:
    def __init__(self, d):
        P = lambda r: laea(r[:, 0], r[:, 1])
        self.land = [P(r) for f in json.load(open(os.path.join(d, 'ne_50m_land.geojson')))['features'] for r in rings(f['geometry']) if inbox(r) and len(r) > 3]
        self.lakes = [P(r) for f in json.load(open(os.path.join(d, 'ne_50m_lakes.geojson')))['features'] for r in rings(f['geometry']) if inbox(r) and len(r) > 3]
        self.c, self.label, self.mapc, self.ll = {}, {}, {}, {}
        usa = []
        for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']:
            p = f['properties']; a3 = p['ADM0_A3']; rs = rings(f['geometry'])
            if a3 == 'USA':
                usa = [r for r in rs if r[:, 0].mean() < -60 and not (r[:, 1].mean() < 25 and r[:, 0].mean() < -150) and len(r) > 8]
                continue
            keep = [r for r in rs if (inbox(r) or a3 == 'RUS') and len(r) > 3]
            if not keep: continue
            code = DEPEND.get(a3, a3)
            self.c.setdefault(code, []).extend(P(r) for r in keep)
            self.ll.setdefault(code, []).extend(keep)
            if a3 == code: self.label[code] = (p['LABEL_X'], p['LABEL_Y']); self.mapc[code] = p['MAPCOLOR9']
        self.label['RUS'] = (40.0, 56.0); self.label['NOR'] = (9.0, 61.0); self.label['SWE'] = (15.5, 62.0); self.label['ITA'] = (12.6, 42.8)
        src, dst = (-98.6, 39.8), (14.0, 51.5)
        self.usa = [laea(*move(r, src, dst)) for r in usa]
        self.usa_c = laea(*dst)
        def hist(path, pick):
            out = {}
            for f in json.load(open(os.path.join(d, 'hist', path)))['features']:
                if not f['geometry']: continue
                n = f['properties'].get('NAME') or ''
                for r in rings(f['geometry']):
                    if overlaps(r) and len(r) > 3: out.setdefault(n if (pick is None or n in pick) else '_', []).append(P(r))
            return out
        self.rome = hist('world_100.geojson', {'Roman Empire'}).get('Roman Empire', [])
        self.charl = hist('world_800.geojson', {'Carolingian Empire'}).get('Carolingian Empire', [])
        self.h1914 = hist('world_1914.geojson', None)
        self.h1920 = hist('world_1920.geojson', None)
        self.order = sorted(COUNTED + ['KOS'], key=lambda c: self.label[c][0] + 0.15 * (60 - self.label[c][1]))

G = None
TL = None

# ---------- timeline ----------
_missing = set()
def build(voice):
    t, beats, clips = 0.0, [], []
    lead = {'hook': 0.25}; tail = {'hook': 0.7, 'fell': 0.6, 'eu': 0.6, 'cta': 2.4, 'why': 0.7}
    for key, text in BEATS:
        a, words = voice.get(text)
        b = dict(key=key, text=text, start=t, l0=t + lead.get(key, 0.3)); b['l1'] = b['l0'] + len(a) / SR
        b['words'] = [(b['l0'] + s, b['l0'] + e, x) for s, e, x in words]; b['tokens'] = text.split()
        clips.append((b['l0'], a)); t = b['l1'] + tail.get(key, 0.4); b['end'] = t; beats.append(b)
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

# ---------- camera ----------
FULL, MTN, WEST, LANGV = (19, 53.5, 0.215), (12, 46.4, 0.43), (12.5, 53.0, 0.29), (17, 52.5, 0.262)
ROME_V, CHARL_V, NAP_V, WW1_V, USSR_V, ITALY_V = (10, 44.5, 0.29), (7.5, 47.5, 0.33), (16.5, 49.5, 0.245), (21, 49.5, 0.255), (26, 51.5, 0.235), (12.6, 42.4, 0.92)
def keys():
    K = [(0.0, (FULL[0], FULL[1], FULL[2] * 0.9)), (w('hook', 'split'), FULL), (bt('land')['start'], FULL), (w('land', 'mountains'), MTN), (bt('seas')['start'], MTN), (w('seas', 'peninsulas'), WEST),
         (bt('lang')['start'], WEST), (bt('lang')['start'] + 1.2, LANGV), (bt('empires')['start'] + 0.3, LANGV), (w('empires', 'Romans'), ROME_V),
         (w('empires', 'Charlemagne') - 0.3, ROME_V), (w('empires', 'Charlemagne') + 0.7, CHARL_V), (w('empires', 'Napoleon') - 0.3, CHARL_V),
         (w('empires', 'Napoleon') + 0.8, NAP_V), (bt('ww1')['start'], NAP_V), (bt('ww1')['start'] + 1.0, WW1_V), (bt('ussr')['start'], WW1_V),
         (bt('ussr')['start'] + 1.0, USSR_V), (bt('tiny')['start'], USSR_V), (w('tiny', 'San'), ITALY_V), (bt('why')['start'], ITALY_V),
         (bt('why')['start'] + 1.3, FULL)]
    return [(t, laea(c[0], c[1]), c[2]) for t, c in K]

def camera(t):
    K = TL['keys']
    for (t0, p0, s0), (t1, p1, s1) in zip(K, K[1:]):
        if t <= t1:
            k = ease_io(prog(t, t0, t1))
            s = math.exp(lerp(math.log(s0), math.log(s1), k))
            return float(lerp(p0[0], p1[0], k)), float(lerp(p0[1], p1[1], k)), s * (1 + 0.012 * math.sin(t * 0.4))
    (_, p, s) = K[-1]; return float(p[0]), float(p[1]), s

def S(cam, x, y): return W / 2 + (np.asarray(x) - cam[0]) * cam[2], MAPY - (np.asarray(y) - cam[1]) * cam[2]
def L(cam, lon, lat): x, y = laea(lon, lat); return S(cam, x, y)

def path_rings(cr, cam, rs):
    for x, y in rs:
        X, Y = S(cam, x, y)
        if X.max() < -50 or X.min() > W + 50 or Y.max() < -50 or Y.min() > H + 50: continue
        cr.move_to(X[0], Y[0])
        for a, b in zip(X[1:], Y[1:]): cr.line_to(a, b)
        cr.close_path()

# ---------- base map ----------
def draw_base(cr, t, cam):
    g = cairo.RadialGradient(W / 2, MAPY, 100, W / 2, MAPY, 1300)
    g.add_color_stop_rgb(0, 0.05, 0.12, 0.25); g.add_color_stop_rgb(1, 0.02, 0.05, 0.12)
    cr.set_source(g); cr.paint()
    cr.new_path(); path_rings(cr, cam, G.land); cr.set_source_rgb(0.2, 0.23, 0.3); cr.fill_preserve()
    cr.set_source_rgba(0.5, 0.7, 0.95, 0.45); cr.set_line_width(1.4); cr.stroke()

def draw_lakes_vignette(cr, cam):
    cr.new_path(); path_rings(cr, cam, G.lakes); cr.set_source_rgb(0.05, 0.12, 0.25); cr.fill()
    g = cairo.RadialGradient(W / 2, H / 2, 520, W / 2, H / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.7)
    cr.set_source(g); cr.paint()

def pop_time(code):
    i = G.order.index(code); n = len(G.order)
    t0, t1 = w('hook', 'split'), w('hook', 'forty', end=True) - 0.25
    return t0 + (t1 - t0) * i / (n - 1)

def lang_time(code):
    if code not in FAMILY: return None
    return w('lang', FAMILY[code][1])

def country_style(code, t):
    """(colour, alpha, pop scale) of a modern country at time t."""
    tp = pop_time(code)
    if t < tp: return None
    k = pop_k(t, tp, 0.4)
    base = PAL9[(G.mapc.get(code, 1) - 1) % 9][:3]
    col, a = base, 0.92
    # muted while the land itself is the story
    mute = during(t, 'land', 'walls', 0.6, 0.6) * (1 - during(t, 'walls', None, 0.3, 0.3) * ease_out(prog(t, w('walls', 'kingdoms'), w('walls', 'kingdoms') + 0.6)))
    a *= 1 - 0.55 * mute
    # language families
    tl = lang_time(code)
    if tl is not None:
        kl = ease_out(prog(t, tl, tl + 0.45)) * (1 - ease_io(prog(t, bt('eu')['end'] - 0.2, bt('eu')['end'] + 0.4)))
        col = tuple(lerp(x, y, kl) for x, y in zip(col, FAM_COL[FAMILY[code][0]]))
    # empires: modern map fades back while the old ones are drawn
    a *= 1 - 0.6 * during(t, 'empires', None, 0.5, 0.01)
    tf = w('fell', 'apart')
    if bt('fell')['start'] <= t < bt('ww1')['start']:
        rk = (sum(map(ord, code)) * 37 % 97) / 97 * 0.6
        a *= 0.4 + 0.6 * ease_out(prog(t, tf + rk, tf + rk + 0.3)); k = pop_k(t, tf + rk, 0.35) if t > tf + rk else 1.0
    # 1914/1920 maps replace the modern one
    a *= 1 - during(t, 'ww1', None, 0.6, 0.6)
    return col, a, k

def draw_countries(cr, t, cam):
    ussr_k = ussr_split(t)
    for code in G.order:
        st = country_style(code, t)
        if st is None: continue
        col, a, k = st
        if a <= 0.01: continue
        group = GROUP_OF.get(code)
        if group and bt('ussr')['start'] <= t < bt('ussr')['end']:
            sk = ussr_k[group]; col = tuple(lerp(x, y, sk) for x, y in zip(GROUP_COL[group], col))
        cx, cy = L(cam, *G.label[code])
        cr.save(); cr.translate(cx, cy); cr.scale(k, k); cr.translate(-cx, -cy)
        if group and bt('ussr')['start'] <= t < bt('ussr')['end']:  # pieces drift apart when the union breaks
            d = ussr_drift(t, group); gx, gy = L(cam, *GROUP_C[group])
            cr.translate((cx - gx) * d, (cy - gy) * d)
        cr.new_path(); path_rings(cr, cam, G.c[code])
        if code in STRIPED and lang_time(code) is not None and t >= lang_time(code) and t < bt('eu')['end'] + 0.4:
            kl = ease_out(prog(t, lang_time(code), lang_time(code) + 0.45))
            cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.save(); cr.clip_preserve()
            cr.set_source_rgba(*FAM_COL[STRIPED[code][1]], a * kl); cr.set_line_width(9)
            x0, y0 = cx - 400, cy - 400
            for i in range(0, 60): cr.move_to(x0 + i * 26, y0); cr.line_to(x0 + i * 26 - 400, y0 + 800)
            cr.stroke(); cr.restore()
            cr.new_path(); path_rings(cr, cam, G.c[code])
        else:
            cr.set_source_rgba(*col, a); cr.fill_preserve()
        hide = group and bt('ussr')['start'] <= t < bt('ussr')['end'] and ussr_k[group] < 0.5
        cr.set_source_rgba(*(col if hide else (1, 1, 1)), (0.9 if hide else 0.55) * a); cr.set_line_width(1.2); cr.stroke()
        cr.restore()
        if code in MICRO:
            x, y = L(cam, *G.label[code]); r = 6 * k
            cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, min(1, a * 1.1)); cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(2); cr.stroke()

# ---------- hook: the USA dropped on Europe, then the 44 pop in ----------
def draw_usa(cr, t, cam, a_mul=1.0):
    tu = w('hook', 'United'); t0 = 0.05
    k = ease_out(prog(t, t0, tu)); out = 1 - ease_io(prog(t, w('hook', 'split') - 0.4, w('hook', 'split') + 0.2))
    tw1 = w('why', 'one')
    back = ease_out(prog(t, tw1, tw1 + 0.5)) * (1 - ease_io(prog(t, bt('why')['end'] - 0.3, bt('why')['end'] + 0.3)))
    a = max(k * out, back) * a_mul
    if a <= 0.01: return
    dy = (1 - k) * -900 if back < 0.01 else 0
    cr.save(); cr.translate(0, dy)
    cr.new_path(); path_rings(cr, cam, G.usa)
    cr.set_source_rgba(*PINK[:3], 0.55 * a); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, 0.95 * a); cr.set_line_width(3.5); cr.stroke()
    x, y = S(cam, *G.usa_c)
    ptext(cr, 'USA', x, y + 30, 90, WHITE, a, sw=10)
    ptext(cr, '(same scale)', x, y + 80, 34, WHITE, a * 0.9, fam='Poppins ExtraBold', sw=5)
    cr.restore()

def draw_counter(cr, t):
    t0 = w('hook', 'split'); hb = bt('hook')
    if not (t0 <= t < hb['end'] + 0.3): return
    n = sum(1 for c in G.order if c != 'KOS' and pop_time(c) <= t)
    out = 1 - ease_io(prog(t, hb['end'] - 0.2, hb['end'] + 0.3))
    big = n == 44; k = pop_k(t, pop_time(G.order[-1]), 0.4) if big else 1.0
    cr.save(); cr.translate(540, 1440); cr.scale(k * (1.15 if big else 1), k * (1.15 if big else 1))
    ptext(cr, str(n), 0, 40, 170, GOLD if big else WHITE, out, sw=16)
    ptext(cr, 'COUNTRIES', 0, 110, 46, WHITE, out, fam='Poppins ExtraBold', sw=6)
    cr.restore()

# ---------- land: mountains, seas, peninsulas, kingdoms ----------
RANGES = [  # name, (lon, lat) polyline, trigger word (beat, word), label?
    ('ALPS', [(5.8, 43.9), (6.8, 45.0), (7.6, 45.9), (9.5, 46.4), (11.0, 46.8), (12.5, 47.0), (14.0, 47.2), (15.6, 47.6)], ('land', 'Alps'), True),
    ('PYRENEES', [(-1.8, 43.2), (0.0, 42.7), (1.5, 42.5), (3.1, 42.4)], ('land', 'Pyrenees'), True),
    ('CARPATHIANS', [(17.3, 48.3), (19.5, 49.2), (22.0, 49.0), (24.5, 47.9), (25.8, 46.6), (25.5, 45.4), (23.0, 45.4), (22.2, 44.9)], ('land', 'Carpathians'), True),
    ('APENNINES', [(8.8, 44.4), (10.5, 44.1), (12.5, 43.2), (14.0, 42.0), (15.5, 40.6), (16.2, 39.3)], ('land', 'mountains'), False),
    ('DINARIC ALPS', [(14.5, 45.5), (16.0, 44.4), (17.8, 43.5), (19.2, 42.6), (20.0, 42.0)], ('land', 'mountains'), False),
    ('BALKAN MTS', [(22.4, 43.8), (24.0, 42.8), (26.0, 42.7), (27.5, 42.7)], ('land', 'mountains'), False),
    ('SCANDES', [(6.0, 59.0), (8.0, 61.5), (12.0, 63.5), (14.5, 66.5), (17.5, 68.5), (20.5, 69.3)], ('land', 'mountains'), False),
    ('CAUCASUS', [(38.0, 44.5), (41.0, 43.4), (44.0, 42.7), (47.0, 41.6), (49.0, 40.8)], ('land', 'mountains'), False),
    ('URALS', [(59.0, 51.0), (58.6, 55.0), (59.2, 60.0), (60.0, 64.0), (65.0, 68.0)], ('land', 'mountains'), False),
]
def mountains_alpha(t):
    a = during(t, 'land', 'walls', 0.3, 0.6)
    tm = w('why', 'Mountains'); a = max(a, ease_out(prog(t, tm, tm + 0.4)) * (1 - ease_io(prog(t, tm + 2.5, tm + 3.2))))
    return a

def draw_mountains(cr, t, cam):
    A = mountains_alpha(t)
    if A <= 0: return
    wall = ease_out(prog(t, w('walls', 'walls'), w('walls', 'walls') + 0.5)) * during(t, 'walls', None, 0.1, 0.5)
    for name, pts, (bk, wd), lab in RANGES:
        t0 = min(w(bk, wd), w('why', 'Mountains')) if t >= w('why', 'Mountains') else w(bk, wd)
        k = ease_io(prog(t, t0, t0 + 0.9))
        if k <= 0: continue
        X, Y = L(cam, [p[0] for p in pts], [p[1] for p in pts])
        seg = np.hypot(np.diff(X), np.diff(Y)); total = seg.sum()
        if wall > 0:  # the 'natural walls' glow
            cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:], Y[1:])]
            cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
            cr.set_source_rgba(1.0, 0.85, 0.4, 0.35 * wall * A); cr.set_line_width(26); cr.stroke_preserve()
            cr.set_source_rgba(1.0, 0.9, 0.5, 0.9 * wall * A); cr.set_line_width(5); cr.stroke()
        step = 30; n = int(total * k / step)
        for i in range(n + 1):
            d = i * step; j = min(int(np.searchsorted(np.cumsum(seg), d)), len(seg) - 1)
            prev = np.cumsum(seg)[j - 1] if j > 0 else 0.0; f = (d - prev) / max(seg[j], 1e-6)
            x, y = lerp(X[j], X[j + 1], f), lerp(Y[j], Y[j + 1], f)
            hgt = 28 + 10 * math.sin(i * 2.3 + len(name)); wd_ = 19
            pk = clamp((total * k - d) / 40)
            cr.new_path(); cr.move_to(x - wd_, y + 8); cr.line_to(x, y + 8 - hgt * pk); cr.line_to(x + wd_, y + 8); cr.close_path()
            cr.set_source_rgba(0.62, 0.46, 0.32, A); cr.fill_preserve(); cr.set_source_rgba(0.2, 0.12, 0.06, 0.7 * A); cr.set_line_width(1.5); cr.stroke()
            cr.new_path(); cr.move_to(x - wd_ * 0.36, y + 8 - hgt * pk * 0.64); cr.line_to(x, y + 8 - hgt * pk); cr.line_to(x + wd_ * 0.36, y + 8 - hgt * pk * 0.64); cr.close_path()
            cr.set_source_rgba(1, 1, 1, 0.95 * A); cr.fill()
        if lab and k > 0.2:
            m = len(X) // 2; la = A * ease_out(prog(t, t0 + 0.2, t0 + 0.6)) * (1 - during(t, 'seas', 'walls', 0.3, 0.1) * 0.0)
            ptext(cr, name, X[m], Y[m] - 34, 38, WHITE, la, fam='Poppins ExtraBold', sw=7)

SEAS = [('ATLANTIC', (-14.0, 48.0)), ('NORTH SEA', (3.5, 56.3)), ('BALTIC', (19.3, 57.6)), ('MEDITERRANEAN', (15.0, 36.5)), ('BLACK SEA', (34.2, 43.3))]
PENIN = [('IBERIA', ['ESP', 'PRT', 'AND'], (-4.2, 40.0), 'Iberia'), ('ITALY', ['ITA', 'SMR', 'VAT'], (13.5, 42.2), 'Italy'),
         ('BALKANS', ['ALB', 'GRC', 'MKD', 'BGR', 'SRB', 'MNE', 'BIH', 'KOS'], (22.0, 42.4), 'Balkans'), ('SCANDINAVIA', ['NOR', 'SWE'], (15.0, 64.0), 'Scandinavia')]
def draw_seas(cr, t, cam):
    a = during(t, 'seas', 'walls', 0.3, 0.5)
    if a <= 0: return
    ts = w('seas', 'seas')
    for i, (name, ll) in enumerate(SEAS):
        k = ease_out(prog(t, ts + i * 0.12, ts + i * 0.12 + 0.4)) * a
        x, y = L(cam, *ll); ptext(cr, name, x, y, 30, (0.6, 0.88, 1.0), k, fam='Poppins ExtraBold', sw=5)
    for name, members, ll, word in PENIN:
        tp = w('seas', word); k = ease_out(prog(t, tp, tp + 0.4)) * a
        if k <= 0: continue
        cr.new_path()
        for c in members: path_rings(cr, cam, G.c[c])
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_source_rgba(*GOLD[:3], 0.3 * k); cr.set_line_width(14); cr.stroke_preserve()
        cr.set_source_rgba(*GOLD[:3], 0.95 * k); cr.set_line_width(3.5); cr.stroke()
        x, y = L(cam, *ll); kk = pop_k(t, tp)
        cr.save(); cr.translate(x, y); cr.scale(kk, kk); ptext(cr, name, 0, 0, 40, GOLD, k, sw=8); cr.restore()

CROWNS = [(-3.7, 40.4), (2.4, 46.8), (-1.5, 52.5), (19.5, 52.0), (15.5, 60.5), (19.0, 47.2), (10.5, 51.0), (12.5, 42.5), (25.0, 45.5), (30.0, 55.5)]
def draw_crowns(cr, t, cam):
    tk = w('walls', 'kingdoms'); a = during(t, 'walls', None, 0.1, 0.4)
    for i, ll in enumerate(CROWNS):
        t0 = tk + i * 0.09
        if t < t0: continue
        x, y = L(cam, *ll); emoji(cr, '👑', x, y - 6, 52 * pop_k(t, t0), a, rot=0.15 * math.sin(t * 3 + i))

# ---------- languages ----------
GREET = [('Hello', (-1.6, 52.6), 'ger'), ('Olá', (-8.0, 39.8), 'rom'), ('Hola', (-3.6, 40.3), 'rom'), ('Bonjour', (2.3, 46.9), 'rom'),
         ('Ciao', (12.6, 42.9), 'rom'), ('Hallo', (10.2, 51.0), 'ger'), ('Hej', (15.6, 62.5), 'ger'), ('Moi', (26.3, 63.4), 'ura'),
         ('Halló', (-18.6, 64.9), 'ger'), ('Cześć', (19.3, 52.1), 'sla'), ('Szia', (19.4, 47.1), 'ura'), ('Bună', (25.0, 45.9), 'rom'),
         ('Γειά σου', (22.2, 39.4), 'gre'), ('Labas', (24.0, 55.3), 'bal'), ('Привіт', (31.2, 49.3), 'sla'), ('Привет', (38.5, 55.6), 'sla')]
def nonlatin(s): return any(ord(ch) > 0x24F for ch in s)
def bubble(cr, txt, x, y, col, k, a):
    if a <= 0.01: return
    size = 30
    if nonlatin(txt):
        cr.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); cr.set_font_size(size)
    else: face(cr, size, 'Poppins ExtraBold')
    wd_ = cr.text_extents(txt).x_advance
    cr.save(); cr.translate(x, y); cr.scale(k, k)
    rrect(cr, -wd_ / 2 - 16, -26, wd_ + 32, 46, 18); cr.set_source_rgba(*col, a); cr.fill()
    cr.new_path(); cr.move_to(-8, 19); cr.line_to(0, 33); cr.line_to(8, 19); cr.close_path(); cr.fill()
    cr.move_to(-wd_ / 2, 8); cr.text_path(txt); cr.set_source_rgba(*INK, a); cr.fill()
    cr.restore()

def draw_greetings(cr, t, cam):
    t0 = w('eu', 'European') - 0.2; a = 1 - ease_io(prog(t, bt('eu')['end'] - 0.3, bt('eu')['end'] + 0.2))
    if t < t0 or a <= 0: return
    for i, (txt, ll, fam) in enumerate(GREET):
        ti = t0 + i * 0.13
        if t < ti: continue
        x, y = L(cam, *ll); bubble(cr, txt, x, y - 24, FAM_COL[fam], pop_k(t, ti), a)

# ---------- empires ----------
def reveal_clip(cr, cam, origin, t0, t, dur=1.0):
    x, y = L(cam, *origin); r = 2200 * ease_io(prog(t, t0, t0 + dur))
    cr.new_path(); cr.arc(x, y, max(1, r), 0, 2 * math.pi); cr.clip()

def draw_empires(cr, t, cam):
    eb, fb = bt('empires'), bt('fell')
    if not (eb['start'] <= t < fb['end']): return
    tf = w('fell', 'apart'); gone = 1 - ease_io(prog(t, tf, tf + 0.5))
    for rs, origin, word, col, name, lab_ll in ((G.rome, (12.5, 41.9), 'Romans', (0.9, 0.2, 0.25), 'ROMAN EMPIRE', (14.0, 46.3)),
                                                 (G.charl, (6.08, 50.78), 'Charlemagne', (0.25, 0.5, 1.0), "CHARLEMAGNE'S EMPIRE", (6.0, 52.6))):
        t0 = w('empires', word)
        if t < t0: continue
        dim = 0.45 if (word == 'Romans' and t > w('empires', 'Charlemagne')) else 1.0
        dim *= 0.6 if t > w('empires', 'Napoleon') else 1.0
        a = gone * dim
        cr.save(); reveal_clip(cr, cam, origin, t0, t)
        cr.new_path(); path_rings(cr, cam, rs); cr.set_source_rgba(*col, 0.55 * a); cr.fill_preserve()
        cr.set_source_rgba(*GOLD[:3], 0.95 * a); cr.set_line_width(3); cr.stroke(); cr.restore()
        if word == 'Romans' and t > w('empires', 'Charlemagne'): continue
        if word == 'Charlemagne' and t > w('empires', 'Napoleon'): continue
        x, y = L(cam, *lab_ll); k = pop_k(t, t0 + 0.3)
        cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, name, 0, 0, 44, WHITE, a, sw=8); cr.restore()
    # Napoleon's campaigns: Paris -> Madrid, Vienna, Berlin, Moscow
    tn = w('empires', 'Napoleon')
    if t >= tn:
        paris = (2.35, 48.85)
        x0, y0 = L(cam, *paris)
        legs = [((-3.7, 40.4), tn + 0.1, [(0.0, 45.5)]), ((16.37, 48.2), tn + 0.4, [(9.0, 49.0)]), ((13.4, 52.5), tn + 0.7, [(8.0, 51.5)]),
                ((37.6, 55.75), w('empires', 'Moscow') - 1.2, [(12.0, 52.3), (24.0, 54.6)])]
        for dest, t0, via in legs:
            k = ease_io(prog(t, t0, t0 + (1.3 if dest[0] > 30 else 0.6)))
            if k <= 0: continue
            pts = [paris] + via + [dest]
            X, Y = L(cam, [p[0] for p in pts], [p[1] for p in pts])
            from_pts = np.stack([X, Y], 1)
            dense = [from_pts[0]]
            for p, q in zip(from_pts[:-1], from_pts[1:]):
                for u in np.linspace(0, 1, 20)[1:]: dense.append(p + (q - p) * u)
            dense = np.array(dense); n = max(2, int(len(dense) * k))
            cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
            for lw, al in ((22, 0.2), (8, 1.0)):
                cr.new_path(); cr.move_to(*dense[0]); [cr.line_to(*q) for q in dense[1:n]]
                cr.set_source_rgba(0.25, 0.45, 1.0, al * gone); cr.set_line_width(lw); cr.stroke()
            hx, hy = dense[n - 1]; px, py = dense[max(0, n - 3)]; ang = math.atan2(hy - py, hx - px)
            cr.save(); cr.translate(hx, hy); cr.rotate(ang); cr.new_path(); cr.move_to(26, 0); cr.line_to(-14, 18); cr.line_to(-14, -18); cr.close_path()
            cr.set_source_rgba(1, 1, 1, gone); cr.fill(); cr.restore()
            if k >= 1:
                name = {(-3.7, 40.4): 'MADRID', (16.37, 48.2): 'VIENNA', (13.4, 52.5): 'BERLIN', (37.6, 55.75): 'MOSCOW'}[dest]
                ptext(cr, name, hx, hy + 48, 32 if name != 'MOSCOW' else 46, GOLD if name == 'MOSCOW' else WHITE, gone, fam='Poppins ExtraBold', sw=6)
        k = pop_k(t, tn); cr.save(); cr.translate(x0, y0 - 60); cr.scale(k, k); ptext(cr, 'NAPOLEON', 0, 0, 46, WHITE, gone, sw=8); cr.restore()
        emoji(cr, '⚔️', x0, y0 - 2, 48 * k, gone)
    # cracks as it all falls apart
    if tf <= t < tf + 0.8:
        a = 1 - prog(t, tf + 0.3, tf + 0.8); g = np.random.default_rng(7)
        cr.set_source_rgba(1, 1, 1, 0.85 * a); cr.set_line_width(4)
        for _ in range(9):
            x, y = g.uniform(100, 980), g.uniform(450, 1250); ang = g.uniform(0, 6.28); cr.new_path(); cr.move_to(x, y)
            for _ in range(7):
                ang += g.normal(0, 0.6); x += 60 * math.cos(ang) * ease_out(prog(t, tf, tf + 0.25)); y += 60 * math.sin(ang) * ease_out(prog(t, tf, tf + 0.25)); cr.line_to(x, y)
            cr.stroke()

# ---------- 1914 -> 1920 ----------
E1914 = {'German Empire': ((0.35, 0.5, 0.95), (11.0, 52.0), 'GERMAN'), 'Austro-Hungarian Empire': ((1.0, 0.72, 0.2), (18.5, 47.6), 'AUSTRIA-HUNGARY'),
         'Russian Empire': ((0.3, 0.8, 0.45), (36.0, 56.5), 'RUSSIAN'), 'Ottoman Empire': ((0.95, 0.3, 0.3), (33.0, 39.6), 'OTTOMAN')}
NEW1920 = {'Poland': ('Poland', (19.5, 52.3)), 'Czechoslovakia': ('Czechoslovakia', (17.5, 49.3)), 'Yugoslavia': ('Yugoslavia', (19.0, 44.2)),
           'Finland': ('appeared', (26.0, 63.0)), 'Estonia': ('appeared', (25.7, 58.8)), 'Latvia': ('appeared', (25.5, 56.9)),
           'Lithuania': ('appeared', (24.0, 55.2)), 'Austria': ('appeared', (14.3, 47.6)), 'Hungary': ('appeared', (19.3, 47.1))}
NEW_COL = [(1.0, 0.35, 0.55), (0.3, 0.9, 0.85), (1.0, 0.84, 0.2), (0.62, 0.42, 1.0), (0.45, 0.95, 0.45), (1.0, 0.6, 0.15), (0.25, 0.6, 1.0), (1.0, 0.45, 0.35), (0.8, 0.5, 1.0)]
def draw_ww1(cr, t, cam):
    a = during(t, 'ww1', None, 0.6, 0.6)
    if a <= 0: return
    tc = w('ww1', 'collapsed'); x20 = ease_io(prog(t, tc, tc + 0.8))
    for which, data, amul in (('1914', G.h1914, (1 - x20) * a), ('1920', G.h1920, x20 * a)):
        if amul <= 0.01: continue
        for name, rs in data.items():
            col, edge = (0.27, 0.3, 0.38), 0.45
            if which == '1914' and name in E1914: col = E1914[name][0]; edge = 0.9
            if which == '1920' and name in NEW1920:
                i = list(NEW1920).index(name); tp = w('ww1', NEW1920[name][0]) + (i - 3) * 0.08 * (NEW1920[name][0] == 'appeared')
                kk = ease_out(prog(t, tp, tp + 0.4)); col = tuple(lerp(x, y, kk) for x, y in zip(col, NEW_COL[i])); edge = 0.45 + 0.5 * kk
            cr.new_path(); path_rings(cr, cam, rs); cr.set_source_rgba(*col, 0.92 * amul); cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, edge * amul); cr.set_line_width(1.4); cr.stroke()
        if which == '1914':
            for name, (col, ll, lab) in E1914.items():
                x, y = L(cam, *ll); ptext(cr, lab, x, y, 34, WHITE, amul * ease_out(prog(t, w('ww1', 'World'), w('ww1', 'World') + 0.5)), fam='Poppins ExtraBold', sw=6)
        else:
            for i, (name, (word, ll)) in enumerate(NEW1920.items()):
                tp = w('ww1', word) + (i - 3) * 0.08 * (word == 'appeared')
                if t < tp: continue
                x, y = L(cam, *ll); k = pop_k(t, tp); big = word != 'appeared'
                cr.save(); cr.translate(x, y); cr.scale(k, k)
                ptext(cr, name.upper(), 0, 0, 34 if big else 24, WHITE, amul, fam='Poppins ExtraBold', sw=6); cr.restore()

# ---------- the 1990s break-ups (modern borders) ----------
GROUPS = {'USSR': ['RUS', 'UKR', 'BLR', 'MDA', 'EST', 'LVA', 'LTU'], 'YUG': ['SVN', 'HRV', 'BIH', 'SRB', 'MNE', 'MKD', 'KOS']}
GROUP_OF = {c: g for g, cs in GROUPS.items() for c in cs}
GROUP_COL = {'USSR': (0.85, 0.15, 0.2), 'YUG': (0.25, 0.4, 0.95)}
GROUP_C = {'USSR': (33.0, 54.0), 'YUG': (18.5, 44.0)}
GROUP_LAB = {'USSR': ('SOVIET UNION', (36.0, 55.5), 'Soviet'), 'YUG': ('YUGOSLAVIA', (18.0, 44.6), 'Yugoslavia')}
def ussr_split(t):
    tb = w('ussr', 'broke'); return {g: ease_out(prog(t, tb + (0.25 if g == 'YUG' else 0), tb + (0.25 if g == 'YUG' else 0) + 0.5)) for g in GROUPS}
def ussr_drift(t, g):
    tb = w('ussr', 'broke') + (0.25 if g == 'YUG' else 0)
    return 0.12 * math.sin(math.pi * clamp((t - tb) / 0.9)) * (t > tb)

def draw_ussr_labels(cr, t, cam):
    b = bt('ussr')
    if not (b['start'] <= t < b['end']): return
    a = during(t, 'ussr', None, 0.4, 0.4); sk = ussr_split(t)
    for g, (lab, ll, word) in GROUP_LAB.items():
        tg = w('ussr', word)
        if t < tg: continue
        x, y = L(cam, *ll); k = pop_k(t, tg)
        cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, lab, 0, 0, 40 if g == 'USSR' else 34, WHITE, a * (1 - sk[g]), sw=7); cr.restore()
        if sk[g] > 0:
            for c in GROUPS[g]:
                if c == 'RUS': continue
                x, y = L(cam, *G.label[c]); nm = {'BIH': 'BOSNIA', 'MKD': 'N. MACEDONIA'}.get(c, NAMES.get(c, c))
                ptext(cr, nm, x, y + 8, 22, WHITE, a * sk[g], fam='Poppins ExtraBold', sw=4)

NAMES = {'UKR': 'UKRAINE', 'BLR': 'BELARUS', 'MDA': 'MOLDOVA', 'EST': 'ESTONIA', 'LVA': 'LATVIA', 'LTU': 'LITHUANIA', 'SVN': 'SLOVENIA',
         'HRV': 'CROATIA', 'SRB': 'SERBIA', 'MNE': 'MONTENEGRO', 'KOS': 'KOSOVO'}

# ---------- microstates ----------
def draw_tiny(cr, t, cam):
    b = bt('tiny')
    if not (b['start'] <= t < b['end'] + 0.3): return
    a = during(t, 'tiny', None, 0.3, 0.4)
    for word, ll, lab, col in (('San', (12.45, 43.94), 'SAN MARINO', GOLD), ('Vatican', (12.453, 41.903), 'VATICAN CITY', CYAN)):
        t0 = w('tiny', word)
        if t < t0: continue
        x, y = L(cam, *ll); r = prog(t, t0, t0 + 1.2)
        cr.new_path(); cr.arc(x, y, 10 + 50 * ease_out(r), 0, 2 * math.pi); cr.set_source_rgba(*col[:3], (1 - r) * a); cr.set_line_width(4); cr.stroke()
        cr.new_path(); cr.arc(x, y, 12 * ease_back(prog(t, t0, t0 + 0.4), 3), 0, 2 * math.pi); cr.set_source_rgba(*col[:3], a); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(3); cr.stroke()
        ptext(cr, lab, x + 30, y + 14, 40, WHITE, a * ease_out(prog(t, t0 + 0.1, t0 + 0.5)), fam='Poppins ExtraBold', anchor='l', sw=7)
    # Central Park vs Vatican City, by area
    tc = w('tiny', 'Central')
    if t >= tc:
        k = pop_k(t, tc, 0.45); ca = a
        cr.save(); cr.translate(540, 1100); cr.scale(k, k)
        rrect(cr, -470, -170, 940, 340, 36); cr.set_source_rgba(0.04, 0.06, 0.16, 0.92 * ca); cr.fill_preserve()
        cr.set_source_rgba(*CYAN[:3], ca); cr.set_line_width(3); cr.stroke()
        ptext(cr, "NEW YORK'S CENTRAL PARK  (3.4 km²)", 0, -118, 32, WHITE, ca, fam='Poppins ExtraBold', sw=5)
        pw, ph = 840, 120; x0 = -pw / 2
        rrect(cr, x0, -80, pw, ph, 14); cr.set_source_rgba(0.2, 0.7, 0.3, ca); cr.fill()
        ts = w('tiny', 'seven')
        for i in range(7):
            ti = tc + 0.3 + i * (max(0.2, ts - tc - 0.3) / 6)
            if t < ti: continue
            kk = pop_k(t, ti, 0.3); sw_ = pw / 7
            cr.save(); cr.translate(x0 + sw_ * (i + 0.5), -20); cr.scale(kk, kk)
            rrect(cr, -sw_ / 2 + 6, -52, sw_ - 12, 104, 10); cr.set_source_rgba(*GOLD[:3], 0.9 * ca); cr.fill()
            ptext(cr, str(i + 1), 0, 16, 48, INK, ca, sw=0, shadow=False); cr.restore()
        ptext(cr, 'VATICAN CITY  (0.49 km²)  × 7', 0, 110, 36, GOLD, ca * ease_out(prog(t, ts, ts + 0.4)), sw=6)
        cr.restore()

# ---------- top titles, year badge, chips, end ----------
TITLES = [('hook', 'Europe', 'EUROPE vs USA'), ('hook', 'same', 'SAME SIZE AS THE USA'), ('hook', 'forty', '44 COUNTRIES?!'), ('land', 'mountains', 'MOUNTAINS'),
          ('seas', 'seas', 'SEAS & PENINSULAS'), ('walls', 'walls', 'NATURAL WALLS'), ('lang', 'language', 'LANGUAGES'),
          ('empires', 'unite', 'EMPIRES'), ('fell', 'apart', '...THAT ALL FELL APART'), ('ww1', 'World', 'WORLD WAR ONE'),
          ('ussr', 'Soviet', 'THE 1990s'), ('tiny', 'tiny', 'TINY COUNTRIES'), ('why', 'Mountains', "THAT'S WHY"), ('why', 'forty', 'EUROPE 44 · USA 1'),
          ('cta', 'Which', None)]
YEARS = [('empires', 'Romans', 'c. AD 100'), ('empires', 'Charlemagne', 'c. AD 800'), ('empires', 'Napoleon', '1805–1812'), ('ww1', 'World', '1914'),
         ('ww1', 'collapsed', '1920'), ('ussr', 'Soviet', '1991'), ('tiny', 'tiny', None)]

def draw_title(cr, t):
    cur, t0 = None, 0
    for key, word, txt in TITLES:
        tw0 = w(key, word)
        if t >= tw0: cur, t0 = txt, tw0
    if cur:
        k = prog(t, t0, t0 + 0.3); sc = lerp(1.7, 1.0, ease_out(k))
        cr.save(); cr.translate(540, 200); cr.scale(sc, sc)
        ptext(cr, cur, 0, 0, fit(cr, cur, 84, 1000), WHITE, clamp(k * 3), sw=11); cr.restore()
    yr, y0 = None, 0
    for key, word, txt in YEARS:
        tw0 = w(key, word)
        if t >= tw0: yr, y0 = txt, tw0
    if yr and t < bt('ussr')['end']:
        k = pop_k(t, y0); cr.save(); cr.translate(540, 292); cr.scale(k, k)
        wd_ = tw(cr, yr, 50); rrect(cr, -wd_ / 2 - 34, -44, wd_ + 68, 72, 36); cr.set_source_rgba(*GOLD[:3], 1); cr.fill()
        ptext(cr, yr, 0, 8, 50, INK, 1, sw=0, shadow=False); cr.restore()

def chip(cr, t, t0, x, y, txt, e=None, swatch=None, out=1.0, size=40, maxw=900):
    if t < t0 or out <= 0: return
    k = pop_k(t, t0); fs = fit(cr, txt, size, maxw - 140, 'Poppins ExtraBold')
    cr.save(); cr.translate(x, y); cr.scale(k, k)
    wd_ = tw(cr, txt, fs, 'Poppins ExtraBold'); lead = 70 if (e or swatch) else 0; bw = wd_ + 60 + lead
    rrect(cr, -bw / 2, -38, bw, 76, 38); cr.set_source_rgba(0.05, 0.06, 0.18, 0.88 * out); cr.fill_preserve()
    cr.set_source_rgba(*(swatch or CYAN[:3]), out); cr.set_line_width(3); cr.stroke()
    if swatch:
        cr.new_path(); cr.arc(-bw / 2 + 48, 0, 18, 0, 2 * math.pi); cr.set_source_rgba(*swatch, out); cr.fill()
    elif e: emoji(cr, e, -bw / 2 + 48, -2, 46, out)
    ptext(cr, txt, lead / 2, fs * 0.36, fs, WHITE, out, fam='Poppins ExtraBold', sw=5); cr.restore()

def draw_chips(cr, t):
    o = during(t, 'lang', 'eu', 0.2, 0.4)
    if o > 0:
        chip(cr, t, w('lang', 'Romance'), 290, 1340, 'ROMANCE', swatch=FAM_COL['rom'], out=o, maxw=500)
        chip(cr, t, w('lang', 'Germanic'), 790, 1340, 'GERMANIC', swatch=FAM_COL['ger'], out=o, maxw=500)
        chip(cr, t, w('lang', 'Slavic'), 290, 1432, 'SLAVIC', swatch=FAM_COL['sla'], out=o, maxw=500)
        chip(cr, t, w('lang', 'Greek'), 790, 1432, '+ MANY MORE', swatch=FAM_COL['ura'], out=o, maxw=500)
        chip(cr, t, w('eu', 'twenty'), 540, 1524, '24 OFFICIAL EU LANGUAGES', e='🗣️', out=o)
    o = during(t, 'ussr', None, 0.2, 0.4)
    if o > 0: chip(cr, t, w('ussr', 'ten'), 540, 1400, '10+ NEW COUNTRIES', e='🧩', out=o)
    o = during(t, 'tiny', None, 0.2, 0.4)
    if o > 0: chip(cr, t, w('tiny', '301'), 540, 1400, 'SAN MARINO: SINCE AD 301', e='📜', out=o)
    o = during(t, 'why', None, 0.2, 0.4)
    if o > 0:
        for (word, txt, e, x, y) in (('Mountains', 'MOUNTAINS', '⛰️', 290, 1340), ('seas', 'SEAS', '🌊', 790, 1340),
                                     ('languages', 'LANGUAGES', '🗣️', 290, 1432), ('history', 'HISTORY', '📜', 790, 1432)):
            chip(cr, t, w('why', word), x, y, txt, e=e, out=o, maxw=480)

def draw_cta(cr, t):
    tq = w('cta', 'Which')
    if t < tq: return
    k = pop_k(t, tq) * (1 + 0.025 * math.sin(t * 5))
    cr.save(); cr.translate(540, 1330); cr.scale(k, k)
    rrect(cr, -500, -120, 1000, 250, 40); cr.set_source_rgba(0.04, 0.06, 0.16, 0.88); cr.fill()
    ptext(cr, 'WHICH COUNTRY ARE YOU', 0, -30, fit(cr, 'WHICH COUNTRY ARE YOU', 70, 900), WHITE, 1, sw=9)
    ptext(cr, 'WATCHING FROM?', 0, 60, 76, GOLD, 1, sw=10); cr.restore()
    tf_ = w('cta', 'flag')
    if t >= tf_:
        k = pop_k(t, tf_); cr.save(); cr.translate(540, 1540); cr.scale(k, k)
        ptext(cr, 'DROP YOUR FLAG IN THE COMMENTS', 30, 14, fit(cr, 'DROP YOUR FLAG IN THE COMMENTS', 44, 860, 'Poppins ExtraBold'), WHITE, 1, fam='Poppins ExtraBold', sw=6)
        emoji(cr, '🚩', -470, -4, 56, 1, rot=0.2 * math.sin(t * 6)); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1720); cr.scale(k, k)
        txt = 'FOLLOW FOR MORE'; wd_ = tw(cr, txt, 54)
        rrect(cr, -wd_ / 2 - 90, -62, wd_ + 180, 96, 48); cr.set_source_rgba(*PINK[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 54, WHITE, 1, sw=6); emoji(cr, '🔔', -wd_ / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def draw_captions(cr, t):
    for b in TL['beats']:
        if b['key'] == 'cta' and t >= w('cta', 'Which'): return
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
    draw_base(cr, t, cam)
    draw_countries(cr, t, cam)
    draw_ww1(cr, t, cam)
    draw_empires(cr, t, cam)
    draw_lakes_vignette(cr, cam)
    draw_usa(cr, t, cam)
    draw_mountains(cr, t, cam)
    draw_seas(cr, t, cam)
    draw_crowns(cr, t, cam)
    draw_greetings(cr, t, cam)
    draw_ussr_labels(cr, t, cam)
    draw_tiny(cr, t, cam)
    draw_title(cr, t)
    draw_counter(cr, t)
    draw_chips(cr, t)
    draw_cta(cr, t)
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
    chords = [[50, 57, 62, 66], [47, 54, 59, 62], [43, 50, 55, 59], [45, 52, 57, 61]]  # D Bm G A
    beat = 0.48
    for ci in range(int(dur / (beat * 8)) + 1):
        ch = chords[ci % 4]; t0 = ci * beat * 8; L_ = np.arange(int(4.6 * SR)) / SR
        env = np.minimum(1, L_ / 0.8) * np.exp(-L_ * 0.45)
        put(music, t0, sum(0.025 * (np.sin(2 * np.pi * note(m) * L_) + 0.5 * np.sin(2 * np.pi * note(m) * 1.004 * L_ + 1)) for m in ch) * env)
        for j in range(8):  # light plucked ostinato
            pt = np.arange(int(0.5 * SR)) / SR; m = ch[[0, 2, 1, 3, 2, 1, 3, 2][j]] + 12
            put(music, t0 + j * beat, 0.05 * np.sin(2 * np.pi * note(m) * pt) * np.exp(-pt * 9))
        for j in range(0, 8, 2):
            kt = np.arange(int(0.25 * SR)) / SR; put(music, t0 + j * beat, 0.12 * np.sin(2 * np.pi * (55 + 70 * np.exp(-kt * 25)) * kt) * np.exp(-kt * 14))
    rev = np.zeros(n)
    for d, gg in ((0.21, 0.25), (0.37, 0.15)): k = int(d * SR); rev[k:] += gg * music[:-k]
    music = np.tanh((music + rev) * 1.2) * 0.6
    fx = np.zeros(n)
    def pop(t0, amp=0.07, f=900):
        L_ = np.arange(int(0.07 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * f * L_ * (1 + 2 * L_)) * np.exp(-L_ * 60))
    def boom(t0, amp=0.5):
        L_ = np.arange(int(1.8 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(34 + 60 * np.exp(-L_ * 8)) / SR) * np.exp(-L_ * 2.4))
    def whoosh(t0, amp=0.16, d=0.9):
        L_ = int(d * SR); nz = g.standard_normal(L_); sm = np.convolve(nz, np.ones(30) / 30, 'same')
        put(fx, t0, amp * sm * np.sin(np.pi * np.linspace(0, 1, L_)) ** 2)
    def chime(t0, amp=0.07):
        L_ = np.arange(int(0.9 * SR)) / SR; put(fx, t0, amp * sum(np.sin(2 * np.pi * f * L_) * np.exp(-L_ * d) for f, d in ((1568, 4), (2349, 5))))
    for i, c in enumerate(G.order): pop(pop_time(c), 0.06, 700 + 25 * i)
    for key, word, txt in TITLES:
        if txt: boom(w(key, word), 0.45)
    for t0, _, _ in TL['keys'][1:]: whoosh(t0 - 0.2)
    for key, word in (('lang', 'Romance'), ('lang', 'Germanic'), ('lang', 'Slavic'), ('lang', 'Greek'), ('eu', 'twenty'), ('ussr', 'ten'),
                      ('tiny', '301'), ('tiny', 'Central'), ('why', 'Mountains'), ('why', 'seas'), ('why', 'languages'), ('why', 'history')):
        chime(w(key, word))
    for i in range(len(GREET)): pop(w('eu', 'European') - 0.2 + i * 0.13, 0.05, 1200)
    for i in range(len(CROWNS)): pop(w('walls', 'kingdoms') + i * 0.09, 0.05, 1500)
    boom(w('fell', 'apart'), 0.7); boom(w('ussr', 'broke'), 0.6)
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
    global G, TL
    G = Geo(data_dir)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_europe'))
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
