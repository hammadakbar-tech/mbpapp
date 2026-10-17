"""Europe's Borders, 1914 -> Today (9:16, British female voice).
Historical maps (historical-basemaps) cross-fade on the narrator's words; countries that split later are drawn merged
until the word that breaks them apart. Reuses the projection and base map from europe.py.
Usage: python3 timelapse.py <data_dir> <out.mp4> [--preview t1,t2,...]
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
    ('hook', "A hundred years of Europe's borders, in ninety seconds. Watch closely, because this map is about to be torn up again and again."),
    ('y1914', "Nineteen fourteen. Four giant empires rule much of Europe: Germany, Austria-Hungary, Russia and the Ottomans."),
    ('ww1', "Then World War One destroys all four. By 1920, new countries fill the gap: Poland, Czechoslovakia, Yugoslavia, Finland and the Baltic states."),
    ('y1938', "But the peace doesn't last. In 1938, Nazi Germany swallows Austria, and then part of Czechoslovakia."),
    ('ww2', "World War Two redraws the map again. Poland is pushed west, the Soviet Union takes the Baltic states, and Germany is split in two."),
    ('cold', "For forty years, an Iron Curtain divides Europe into East and West."),
    ('fall', "Then in 1989, the Berlin Wall falls. Germany reunites, and in 1991, the Soviet Union breaks into fifteen countries."),
    ('split', "Yugoslavia breaks apart in a series of wars, and Czechoslovakia splits peacefully in two."),
    ('today', "And it's still changing. Montenegro became independent in 2006, and Kosovo declared independence in 2008."),
    ('end', "From a continent of empires, to forty-four countries, in just over a century."),
    ('cta', "Which change surprised you the most? Tell me in the comments, and follow for more maps."),
]

# ---------- maps ----------
CANON = {'German Empire': 'Germany', 'Germany (UK)': 'Germany', 'Germany (USA)': 'Germany', 'Germany (France)': 'Germany', 'West Germany': 'Germany',
         'Saar Protectorate': 'Germany', 'East Prussia': 'Germany', 'Germany (Soviet)': 'East Germany',
         'Russian Empire': 'Russia', 'USSR': 'Russia', 'South Russia': 'Russia', 'White Russia': 'Belarus', 'Byelarus': 'Belarus',
         'Ottoman Empire': 'Turkey', 'Ottoman Sultanate': 'Turkey', 'Republic of Turkey': 'Turkey',
         'United Kingdom of Great Britain and Ireland': 'United Kingdom', 'Kingdom of Italy': 'Italy', 'Dodecanese Islands': 'Italy',
         'Macedonia': 'North Macedonia', 'Czech Republic': 'Czechia', 'Bosnia and Herz.': 'Bosnia and Herzegovina',
         'Austro-Hungarian Empire': 'Austria-Hungary', 'Turkish Cypriot-administered area': 'N. Cyprus', 'Faeroe Is.': 'Denmark',
         'Åland': 'Finland', 'Jersey': 'United Kingdom', 'Guernsey': 'United Kingdom', 'Isle of Man': 'United Kingdom'}
OVERRIDE = {'1914': {'Finland': 'Russia', 'Iceland': 'Denmark', 'Malta': 'United Kingdom'}, '1920': {'Malta': 'United Kingdom'},
            '1938': {'Malta': 'United Kingdom'}, '1945': {'Malta': 'United Kingdom'}, '1960': {'Malta': 'United Kingdom'}}
COLORS = {k: hexc(v)[:3] for k, v in {
    'Germany': '#5A7BFF', 'East Germany': '#FF5A5F', 'Russia': '#3DC8B0', 'Austria-Hungary': '#FFC93C', 'Austria': '#FFC93C', 'Hungary': '#8CFF5A',
    'Turkey': '#FF8A3D', 'France': '#3DA5FF', 'Spain': '#FF9F1C', 'Portugal': '#8CFF5A', 'United Kingdom': '#FF4FA3', 'Ireland': '#3DFFB0',
    'Italy': '#3DFF8F', 'Switzerland': '#FF5A5F', 'Belgium': '#FFC93C', 'Netherlands': '#FF8A3D', 'Luxembourg': '#B06BFF', 'Denmark': '#FF5A5F',
    'Norway': '#B06BFF', 'Sweden': '#3DA5FF', 'Finland': '#E0E4FF', 'Iceland': '#3DE0C8', 'Poland': '#FF4F6D', 'Czechoslovakia': '#3DE0FF',
    'Czechia': '#3DE0FF', 'Slovakia': '#FF8A3D', 'Yugoslavia': '#B06BFF', 'Serbia': '#B06BFF', 'Croatia': '#3DA5FF', 'Slovenia': '#8CFF5A',
    'Bosnia and Herzegovina': '#FFC93C', 'North Macedonia': '#FF5A5F', 'Montenegro': '#3DE0C8', 'Kosovo': '#FFD60A', 'Romania': '#FFD60A',
    'Bulgaria': '#3DFF8F', 'Greece': '#5A7BFF', 'Albania': '#FF5A5F', 'Estonia': '#3DA5FF', 'Latvia': '#FF5A5F', 'Lithuania': '#FFC93C',
    'Ukraine': '#FFD60A', 'Belarus': '#FF8A3D', 'Moldova': '#B06BFF', 'Georgia': '#FF4FA3', 'Armenia': '#FFC93C', 'Azerbaijan': '#3DA5FF',
    'Danzig': '#E0E4FF', 'Andorra': '#FF5A5F', 'Liechtenstein': '#FF5A5F', 'Malta': '#FF5A5F', 'Cyprus': '#FFC93C', 'N. Cyprus': '#FF8A3D',
    'Monaco': '#FF5A5F', 'San Marino': '#3DA5FF', 'Vatican': '#FFD60A', 'Montenegro ': '#3DE0C8'}.items()}
NEUTRAL = (0.27, 0.3, 0.38)
WARSAW = {'Russia', 'Poland', 'East Germany', 'Czechoslovakia', 'Hungary', 'Romania', 'Bulgaria', 'Albania'}
MONTAGE = [('1914', '1914'), ('1920', '1920'), ('1938', '1938'), ('1945', '1945'), ('1960', '1960'), ('1994', '1994'), ('today', 'TODAY')]

class Maps:
    def __init__(self, d):
        self.m = {}
        for y in ('1914', '1920', '1938', '1945', '1960', '1994'):
            ents = {}
            for f in json.load(open(os.path.join(d, 'hist', f'world_{y}.geojson')))['features']:
                if not f['geometry']: continue
                n = f['properties'].get('NAME') or ''
                c = OVERRIDE.get(y, {}).get(n, CANON.get(n, n))
                for r in E.rings(f['geometry']):
                    if E.overlaps(r) and len(r) > 3: ents.setdefault(c, []).append(E.laea(r[:, 0], r[:, 1]))
            self.m[y] = ents
        ents = {}
        for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']:
            n = f['properties']['NAME']; c = CANON.get(n, n)
            for r in E.rings(f['geometry']):
                cc = 'Ukraine' if (n == 'Russia' and E.crimea(r)) else c
                if (E.overlaps(r) or n == 'Russia') and len(r) > 3: ents.setdefault(cc, []).append(E.laea(r[:, 0], r[:, 1]))
        self.m['today'] = ents
        for y in ('1914', '1920', '1938', '1945', '1960', '1994'):  # patch broken outlines (e.g. a 4-point Switzerland in 1994)
            for c, rs in list(self.m[y].items()):
                if c in ents and sum(len(x) for x, _ in rs) < 12:
                    print(f'  patched {c} in {y}', file=sys.stderr); self.m[y][c] = ents[c]
        self.germany_now = ents['Germany']; self.austria_now = ents['Austria']
        self.baltic_now = ents['Estonia'] + ents['Latvia'] + ents['Lithuania']

M = None
TL = None

# ---------- timeline ----------
_missing = set()
def build(voice):
    t, beats, clips = 0.0, [], []
    lead = {'hook': 0.25, 'y1914': 0.9}; tail = {'hook': 0.5, 'end': 0.7, 'cta': 2.4, 'cold': 0.6}
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

MONT_T0, MONT_DT, REW_DT = 0.3, 0.55, 0.1
def map_states():
    """(time, map) keys after the hook: a fast montage, a rewind, then the story."""
    S = [(MONT_T0 + i * MONT_DT, m) for i, (m, _) in enumerate(MONTAGE)]
    r0 = bt('y1914')['start']
    S += [(r0 + i * REW_DT, m) for i, (m, _) in enumerate(reversed(MONTAGE))]
    S += [(w('ww1', '1920'), '1920'), (w('y1938', '1938'), '1938'), (w('ww2', 'World'), '1945'), (w('ww2', 'split'), '1960'),
          (w('fall', '1991'), '1994'), (bt('today')['start'] + 0.2, 'today')]
    return S
def year_keys():
    K = [(MONT_T0 + i * MONT_DT, y) for i, (_, y) in enumerate(MONTAGE)]
    r0 = bt('y1914')['start']
    K += [(r0 + i * REW_DT, y) for i, (_, y) in enumerate(reversed(MONTAGE))]
    K += [(w('ww1', 'World'), '1914–18'), (w('ww1', '1920'), '1920'), (w('y1938', '1938'), '1938'), (w('ww2', 'World'), '1939–45'),
          (w('ww2', 'split'), '1949'), (bt('cold')['start'] + 0.2, '1949–1989'), (w('fall', '1989'), '1989'), (w('fall', 'reunites'), '1990'),
          (w('fall', '1991'), '1991'), (w('split', 'Yugoslavia'), '1991–92'), (w('split', 'Czechoslovakia'), '1993'), (w('today', '2006'), '2006'),
          (w('today', '2008'), '2008'), (bt('end')['start'], 'TODAY')]
    return K

def merges():
    return {'1994': [(['Slovenia', 'Croatia', 'Bosnia and Herzegovina', 'North Macedonia', 'Serbia', 'Montenegro'], 'Yugoslavia', w('split', 'Yugoslavia')),
                     (['Serbia', 'Montenegro'], 'Serbia', None),
                     (['Czechia', 'Slovakia'], 'Czechoslovakia', w('split', 'Czechoslovakia'))],
            'today': [(['Serbia', 'Montenegro', 'Kosovo'], 'Serbia', w('today', '2006')), (['Serbia', 'Kosovo'], 'Serbia', w('today', '2008'))]}

# ---------- camera ----------
FULL, MID, CENT, BALK, MNE_V = (19, 52, 0.24), (18, 51, 0.3), (15, 50, 0.42), (18.5, 46.5, 0.5), (20.2, 42.8, 1.05)
def keys():
    K = [(0.0, FULL), (bt('y1938')['start'], FULL), (w('y1938', '1938'), CENT), (bt('ww2')['start'], CENT), (bt('ww2')['start'] + 1.0, MID),
         (w('fall', 'Berlin') - 0.3, MID), (w('fall', 'Berlin') + 0.6, CENT), (w('fall', '1991') - 0.4, CENT), (w('fall', '1991') + 0.6, FULL),
         (bt('split')['start'], FULL), (bt('split')['start'] + 1.0, BALK), (bt('today')['start'], BALK), (bt('today')['start'] + 1.0, MNE_V),
         (bt('end')['start'], MNE_V), (bt('end')['start'] + 1.3, FULL)]
    return [(t, E.laea(c[0], c[1]), c[2]) for t, c in K]
def camera(t):
    K = TL['keys']
    for (t0, p0, s0), (t1, p1, s1) in zip(K, K[1:]):
        if t <= t1:
            k = ease_io(prog(t, t0, t1)); s = math.exp(lerp(math.log(s0), math.log(s1), k))
            return float(lerp(p0[0], p1[0], k)), float(lerp(p0[1], p1[1], k)), s * (1 + 0.012 * math.sin(t * 0.4))
    (_, p, s) = K[-1]; return float(p[0]), float(p[1]), s

# ---------- map drawing ----------
def ent_color(c): return COLORS.get(c, NEUTRAL)
def draw_map(cr, t, cam, name, alpha):
    if alpha <= 0.01: return
    ents = M.m[name]; groups = TL['merges'].get(name, [])
    order = sorted(ents, key=lambda c: 0 if c not in COLORS else (1 if any(c in g for g, _, _ in groups) else 2))
    for c in order:
        col, hide, k = ent_color(c), False, 1.0
        for members, parent, ts in groups:
            if c in members:
                if ts is None or t < ts: col, hide = ent_color(parent), True; break
                if t < ts + 0.5: k = pop_k(t, ts, 0.45)
        if name in ('1960',) and c in WARSAW:
            ri = ease_out(prog(t, w('cold', 'East'), w('cold', 'East') + 0.6)) * during(t, 'cold', None, 0.1, 0.4)
            col = tuple(lerp(x, y, 0.65 * ri) for x, y in zip(col, (0.85, 0.1, 0.15)))
        cr.save()
        if k != 1.0:
            xs = np.concatenate([x for x, _ in ents[c]]); ys = np.concatenate([y for _, y in ents[c]])
            cx, cy = E.S(cam, xs.mean(), ys.mean()); cr.translate(cx, cy); cr.scale(k, k); cr.translate(-cx, -cy)
        cr.new_path(); E.path_rings(cr, cam, ents[c]); cr.set_source_rgba(*col, 0.94 * alpha); cr.fill_preserve()
        if hide: cr.set_source_rgba(*col, 0.94 * alpha); cr.set_line_width(1.6)
        else: cr.set_source_rgba(1, 1, 1, (0.6 if col != NEUTRAL else 0.25) * alpha); cr.set_line_width(1.3)
        cr.stroke(); cr.restore()

def draw_maps(cr, t, cam):
    S = TL['states']; cur, prev, tc = S[0][1], None, S[0][0]
    for ts, m in S:
        if t >= ts: prev, cur, tc = cur, m, ts
    dur = 0.12 if (t < bt('y1914')['start'] + 1.0) else 0.6
    x = ease_io(prog(t, tc, tc + dur)) if prev and prev != cur else 1.0
    if t < S[0][0]: cur, x = '1914', ease_out(prog(t, 0, S[0][0]))
    if prev and x < 1: draw_map(cr, t, cam, prev, 1.0)
    draw_map(cr, t, cam, cur, x if prev or t >= S[0][0] else x)

def glow_rings(cr, cam, rs, col, a, dash=None):
    if a <= 0: return
    cr.new_path(); E.path_rings(cr, cam, rs); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.set_source_rgba(*col, 0.3 * a); cr.set_line_width(16); cr.stroke_preserve()
    if dash: cr.set_dash(dash)
    cr.set_source_rgba(*col, a); cr.set_line_width(4); cr.stroke(); cr.set_dash([])

# ---------- story overlays ----------
LABELS = [  # beat, word, text, (lon, lat), size, until-beat
    ('y1914', 'Germany', 'GERMAN EMPIRE', (11.0, 52.0), 34, 'y1914'), ('y1914', 'Austria', 'AUSTRIA-HUNGARY', (18.5, 47.6), 34, 'y1914'),
    ('y1914', 'Russia', 'RUSSIAN EMPIRE', (36.0, 57.0), 38, 'y1914'), ('y1914', 'Ottomans', 'OTTOMAN EMPIRE', (33.0, 39.6), 34, 'y1914'),
    ('ww1', 'Poland', 'POLAND', (19.5, 52.3), 34, 'ww1'), ('ww1', 'Czechoslovakia', 'CZECHOSLOVAKIA', (17.5, 49.4), 30, 'ww1'),
    ('ww1', 'Yugoslavia', 'YUGOSLAVIA', (19.0, 44.4), 32, 'ww1'), ('ww1', 'Finland', 'FINLAND', (26.0, 63.0), 32, 'ww1'),
    ('ww1', 'Baltic', 'ESTONIA', (25.8, 58.8), 26, 'ww1'), ('ww1', 'Baltic', 'LATVIA', (25.5, 56.9), 26, 'ww1'), ('ww1', 'Baltic', 'LITHUANIA', (24.0, 55.2), 26, 'ww1'),
    ('y1938', 'Nazi', 'NAZI GERMANY', (10.5, 51.0), 40, 'y1938'), ('y1938', 'Austria', 'AUSTRIA ANNEXED', (14.0, 47.0), 34, 'y1938'),
    ('y1938', 'Czechoslovakia', 'SUDETENLAND', (13.0, 50.55), 30, 'y1938'),
    ('ww2', 'west', 'POLAND', (19.0, 52.0), 36, 'ww2'), ('ww2', 'Baltic', 'BALTICS TAKEN BY USSR', (25.0, 57.3), 28, 'ww2'),
    ('ww2', 'split', 'WEST GERMANY', (8.6, 50.3), 30, 'cold'), ('ww2', 'split', 'EAST GERMANY', (12.9, 52.2), 28, 'cold'),
    ('fall', 'reunites', 'GERMANY', (10.3, 51.2), 40, 'fall'),
    ('fall', 'fifteen', 'UKRAINE', (31.3, 49.0), 30, 'fall'), ('fall', 'fifteen', 'BELARUS', (28.0, 53.6), 26, 'fall'),
    ('fall', 'fifteen', 'MOLDOVA', (28.6, 47.2), 26, 'fall'), ('fall', 'fifteen', 'RUSSIA', (40.0, 56.5), 38, 'fall'),
    ('fall', 'fifteen', 'ESTONIA', (25.8, 58.8), 26, 'fall'), ('fall', 'fifteen', 'LATVIA', (25.5, 56.9), 26, 'fall'), ('fall', 'fifteen', 'LITHUANIA', (24.0, 55.2), 26, 'fall'),
    ('split', 'Yugoslavia', 'SLOVENIA', (14.2, 46.5), 28, 'split'), ('split', 'Yugoslavia', 'CROATIA', (16.5, 45.45), 26, 'split'),
    ('split', 'Yugoslavia', 'BOSNIA', (17.2, 43.95), 26, 'split'), ('split', 'Yugoslavia', 'SERBIA &', (21.4, 44.35), 28, 'split'),
    ('split', 'Yugoslavia', 'MONTENEGRO', (21.4, 43.8), 26, 'split'), ('split', 'Yugoslavia', 'N. MACEDONIA', (21.7, 41.6), 26, 'split'),
    ('split', 'Czechoslovakia', 'CZECHIA', (15.3, 49.8), 30, 'split'), ('split', 'Czechoslovakia', 'SLOVAKIA', (19.4, 48.7), 28, 'split'),
    ('today', '2006', 'MONTENEGRO', (18.9, 42.4), 40, 'today'), ('today', '2008', 'KOSOVO', (21.05, 42.85), 40, 'today'),
]
def draw_labels(cr, t, cam):
    for beat, word, txt, ll, size, until in LABELS:
        t0 = w(beat, word); t1 = bt(until)['end']
        if not (t0 <= t < t1): continue
        a = 1 - ease_io(prog(t, t1 - 0.35, t1)); k = pop_k(t, t0)
        x, y = E.L(cam, *ll)
        cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, txt, 0, size * 0.35, size, WHITE, a, fam='Poppins ExtraBold', sw=6); cr.restore()

CURTAIN = [(10.9, 54.0), (10.8, 53.0), (11.0, 52.4), (10.6, 51.9), (10.1, 51.2), (10.0, 50.6), (11.9, 50.4), (12.5, 50.2), (12.4, 49.7),
           (13.4, 49.1), (13.8, 48.8), (14.8, 48.8), (15.3, 48.98), (16.9, 48.6), (17.1, 48.0), (16.6, 47.5), (16.1, 46.85)]
def draw_story(cr, t, cam):
    # WW1 flash
    tw1 = w('ww1', 'World')
    if tw1 <= t < tw1 + 0.6:
        cr.set_source_rgba(1, 0.9, 0.7, 0.55 * (1 - prog(t, tw1, tw1 + 0.6))); cr.paint()
    if tw1 <= t < w('ww1', '1920') + 0.3:
        for i, ll in enumerate(((11.0, 52.0), (18.5, 47.6), (36.0, 57.0), (33.0, 39.6))):
            t0 = tw1 + 0.15 * i; x, y = E.L(cam, *ll)
            if t >= t0: emoji(cr, '💥', x, y - 10, 90 * pop_k(t, t0), 1 - prog(t, w('ww1', '1920') - 0.2, w('ww1', '1920') + 0.3))
    # 1938: Austria annexed, Sudetenland
    ta = w('y1938', 'Austria'); a = during(t, 'y1938', None, 0.1, 0.4)
    if t >= ta and a > 0: glow_rings(cr, cam, M.austria_now, (1, 1, 1), a * ease_out(prog(t, ta, ta + 0.4)), dash=[10, 8])
    tc = w('y1938', 'Czechoslovakia')
    if t >= tc and a > 0:
        x, y = E.L(cam, 13.0, 50.4); r = 40 + 30 * ease_out(prog(t, tc, tc + 0.5))
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_dash([10, 8]); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(4); cr.stroke(); cr.set_dash([])
    # WW2: Poland pushed west, the Baltic states taken
    tp = w('ww2', 'west'); a = during(t, 'ww2', None, 0.1, 0.4)
    if t >= tp and a > 0:
        k = ease_io(prog(t, tp, tp + 0.9)); x0, y0 = E.L(cam, 25.5, 51.2); x1, y1 = E.L(cam, 15.5, 51.2); hx = lerp(x0, x1, k)
        cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.new_path(); cr.move_to(x0, y0); cr.line_to(hx, y1); cr.set_source_rgba(1, 1, 1, 0.9 * a); cr.set_line_width(14); cr.stroke()
        cr.save(); cr.translate(hx, y1); cr.rotate(math.pi); cr.new_path(); cr.move_to(34, 0); cr.line_to(-16, 26); cr.line_to(-16, -26); cr.close_path()
        cr.set_source_rgba(1, 1, 1, a); cr.fill(); cr.restore()
    tb = w('ww2', 'Baltic')
    if t >= tb and a > 0: glow_rings(cr, cam, M.baltic_now, (1, 0.3, 0.3), a * ease_out(prog(t, tb, tb + 0.4)))
    # Iron Curtain
    ti = w('cold', 'Iron'); a = during(t, 'cold', None, 0.1, 0.5)
    if t >= ti and a > 0:
        k = ease_io(prog(t, ti, ti + 1.6)); X, Y = E.L(cam, [p[0] for p in CURTAIN], [p[1] for p in CURTAIN])
        n = max(2, int(len(X) * k)); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for lw, al in ((22, 0.25), (7, 1.0)):
            cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:n], Y[1:n])]
            cr.set_source_rgba(0.95, 0.15, 0.2, al * a); cr.set_line_width(lw); cr.stroke()
        ptext(cr, 'IRON CURTAIN', X[0] + 10, Y[0] - 30, 38, (1, 0.45, 0.45), a * ease_out(prog(t, ti, ti + 0.5)), sw=7)
        te = w('cold', 'East')
        if t >= te:
            for txt, ll, col in (('WEST', (2.0, 47.0), (0.6, 0.85, 1.0)), ('EAST', (27.0, 50.0), (1, 0.5, 0.5))):
                x, y = E.L(cam, *ll); k2 = pop_k(t, te + (0.25 if txt == 'WEST' else 0))
                cr.save(); cr.translate(x, y); cr.scale(k2, k2); ptext(cr, txt, 0, 0, 70, col, a, sw=10); cr.restore()
    # the Berlin Wall falls, Germany reunites
    tbw = w('fall', 'Berlin'); a = during(t, 'fall', None, 0.1, 0.4)
    if t >= tbw and a > 0:
        x, y = E.L(cam, 13.4, 52.52); k = pop_k(t, tbw)
        emoji(cr, '🧱', x, y - 6, 64 * k, a * (1 - prog(t, w('fall', 'reunites') + 0.5, w('fall', 'reunites') + 0.9)))
        ptext(cr, 'BERLIN WALL', x, y - 60, 34, WHITE, a * (1 - prog(t, w('fall', 'reunites'), w('fall', 'reunites') + 0.4)), fam='Poppins ExtraBold', sw=6)
    tr = w('fall', 'reunites')
    if t >= tr and t < w('fall', '1991') + 0.7:
        k = ease_out(prog(t, tr, tr + 0.5))
        cr.new_path(); E.path_rings(cr, cam, M.germany_now); cr.set_source_rgba(*COLORS['Germany'], 0.95 * k); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, k); cr.set_line_width(3); cr.stroke()

def draw_year(cr, t):
    K = TL['years']; cur, t0, prev = K[0][1], K[0][0], None
    for ts, y in K:
        if t >= ts: prev, cur, t0 = cur, y, ts
    if t < K[0][0]: cur, t0 = '1914', 0.0
    k = pop_k(t, t0, 0.3) if t0 > 0 else 1.0
    cr.save(); cr.translate(540, 230); cr.scale(k, k)
    ptext(cr, cur, 0, 0, fit(cr, cur, 140, 900), GOLD, 1, sw=14); cr.restore()

SUBS = [('hook', 'hundred', '100 YEARS OF BORDERS'), ('y1914', 'Four', 'THE AGE OF EMPIRES'), ('ww1', 'World', 'WORLD WAR ONE'),
        ('y1938', 'peace', 'THE ROAD TO WAR'), ('ww2', 'World', 'WORLD WAR TWO'), ('cold', 'Iron', 'THE COLD WAR'), ('fall', 'Berlin', 'THE WALL FALLS'),
        ('split', 'Yugoslavia', 'BREAK-UPS'), ('today', 'still', 'STILL CHANGING'), ('end', 'continent', '44 COUNTRIES TODAY'), ('cta', 'Which', None)]
def draw_sub(cr, t):
    cur, t0 = None, 0
    for key, word, txt in SUBS:
        tw0 = w(key, word)
        if t >= tw0: cur, t0 = txt, tw0
    if cur:
        k = pop_k(t, t0); cr.save(); cr.translate(540, 330); cr.scale(k, k)
        wd_ = tw(cr, cur, 44); rrect(cr, -wd_ / 2 - 34, -42, wd_ + 68, 70, 35); cr.set_source_rgba(0.04, 0.06, 0.16, 0.85); cr.fill()
        ptext(cr, cur, 0, 14, 44, WHITE, 1, sw=0, shadow=False); cr.restore()
    rb = bt('y1914')['start']
    if rb <= t < rb + REW_DT * len(MONTAGE) + 0.2:
        emoji(cr, '⏪', 540, 470, 90, 1 - prog(t, rb + REW_DT * len(MONTAGE), rb + REW_DT * len(MONTAGE) + 0.2))

def chip(cr, t, t0, x, y, txt, e, out=1.0, size=44):
    if t < t0 or out <= 0: return
    k = pop_k(t, t0); fs = fit(cr, txt, size, 760, 'Poppins ExtraBold')
    cr.save(); cr.translate(x, y); cr.scale(k, k)
    wd_ = tw(cr, txt, fs, 'Poppins ExtraBold'); bw = wd_ + 130
    rrect(cr, -bw / 2, -40, bw, 80, 40); cr.set_source_rgba(0.05, 0.06, 0.18, 0.88 * out); cr.fill_preserve()
    cr.set_source_rgba(*CYAN[:3], out); cr.set_line_width(3); cr.stroke()
    emoji(cr, e, -bw / 2 + 48, -2, 48, out); ptext(cr, txt, 35, fs * 0.36, fs, WHITE, out, fam='Poppins ExtraBold', sw=5); cr.restore()

def draw_chips(cr, t):
    chip(cr, t, w('fall', 'fifteen'), 540, 1400, '15 COUNTRIES FROM 1', '🧩', during(t, 'fall', None, 0.1, 0.4))
    chip(cr, t, w('end', 'forty'), 540, 1400, '44 COUNTRIES TODAY', '🗺️', during(t, 'end', None, 0.1, 0.4))

def draw_cta(cr, t):
    tq = w('cta', 'Which')
    if t < tq: return
    k = pop_k(t, tq) * (1 + 0.025 * math.sin(t * 5))
    cr.save(); cr.translate(540, 1360); cr.scale(k, k)
    rrect(cr, -500, -120, 1000, 250, 40); cr.set_source_rgba(0.04, 0.06, 0.16, 0.88); cr.fill()
    ptext(cr, 'WHICH CHANGE SURPRISED', 0, -30, fit(cr, 'WHICH CHANGE SURPRISED', 70, 900), WHITE, 1, sw=9)
    ptext(cr, 'YOU THE MOST?', 0, 60, 76, GOLD, 1, sw=10); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1720); cr.scale(k, k)
        txt = 'FOLLOW FOR MORE MAPS'; wd_ = tw(cr, txt, 50)
        rrect(cr, -wd_ / 2 - 90, -60, wd_ + 180, 92, 46); cr.set_source_rgba(*PINK[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 50, WHITE, 1, sw=6); emoji(cr, '🔔', -wd_ / 2 - 30, -12, 60, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

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
    E.draw_base(cr, t, cam)
    draw_maps(cr, t, cam)
    draw_story(cr, t, cam)
    E.draw_lakes_vignette(cr, cam)
    draw_labels(cr, t, cam)
    draw_year(cr, t)
    draw_sub(cr, t)
    draw_chips(cr, t)
    draw_cta(cr, t)
    draw_captions(cr, t)
    f = prog(t, TL['dur'] - 0.4, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- score ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    g = np.random.default_rng(3)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n)
    chords = [[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 56]]  # Am F G E: a ticking, cinematic loop
    beat = 0.5
    for ci in range(int(dur / (beat * 8)) + 1):
        ch = chords[ci % 4]; t0 = ci * beat * 8; L_ = np.arange(int(4.8 * SR)) / SR
        env = np.minimum(1, L_ / 1.0) * np.exp(-L_ * 0.4)
        put(music, t0, sum(0.028 * (np.sin(2 * np.pi * note(m) * L_) + 0.5 * np.sin(2 * np.pi * note(m) * 1.004 * L_ + 1)) for m in ch) * env)
        put(music, t0, 0.08 * np.sin(2 * np.pi * note(ch[0] - 12) * L_) * env)
        for j in range(8):  # clock-like ticks
            kt = np.arange(int(0.05 * SR)) / SR; put(music, t0 + j * beat, (0.05 if j % 2 else 0.08) * np.sin(2 * np.pi * 2400 * kt) * np.exp(-kt * 120))
        for j in range(0, 8, 4):
            kt = np.arange(int(0.3 * SR)) / SR; put(music, t0 + j * beat, 0.14 * np.sin(2 * np.pi * (50 + 60 * np.exp(-kt * 22)) * kt) * np.exp(-kt * 12))
    rev = np.zeros(n)
    for d, gg in ((0.23, 0.25), (0.41, 0.15)): k = int(d * SR); rev[k:] += gg * music[:-k]
    music = np.tanh((music + rev) * 1.2) * 0.6
    fx = np.zeros(n)
    def boom(t0, amp=0.5):
        L_ = np.arange(int(1.8 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(34 + 60 * np.exp(-L_ * 8)) / SR) * np.exp(-L_ * 2.4))
    def whoosh(t0, amp=0.15, d=0.8):
        L_ = int(d * SR); nz = g.standard_normal(L_); sm = np.convolve(nz, np.ones(30) / 30, 'same')
        put(fx, t0, amp * sm * np.sin(np.pi * np.linspace(0, 1, L_)) ** 2)
    def tick(t0, amp=0.08, f=1800):
        L_ = np.arange(int(0.06 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * f * L_) * np.exp(-L_ * 70))
    for ts, _ in T['states']:
        if ts < bt('y1914')['start'] + 1.0: tick(ts, 0.1, 1500 + 200 * (ts > bt('y1914')['start']))
        else: whoosh(ts - 0.3); boom(ts, 0.35)
    boom(w('ww1', 'World'), 0.8); boom(w('cold', 'Iron'), 0.5); boom(w('fall', 'Berlin'), 0.6); boom(w('end', 'forty'), 0.5)
    for key, word in (('fall', 'fifteen'), ('split', 'Yugoslavia'), ('split', 'Czechoslovakia'), ('today', '2006'), ('today', '2008')): boom(w(key, word), 0.35)
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
    global M, TL
    E.G = E.Geo(data_dir); M = Maps(data_dir)
    TL = build(SC.WordVoice(cache))
    TL['keys'] = keys(); TL['states'] = map_states(); TL['years'] = year_keys(); TL['merges'] = merges()

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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_timelapse'))
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
