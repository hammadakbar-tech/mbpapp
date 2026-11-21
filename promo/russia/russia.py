"""'The Entire History of Russia - Part 01: From Vikings to the Mongols (862-1480)' (9:16).
Animated map documentary: British narrator (edge-tts en-GB-RyanNeural), Poppins type, year counter, chapter cards,
character medallions, routes, invasions, battles, karaoke captions, cinematic score. Renders in parallel workers.
Usage: python3 russia.py <data_dir> <out.mp4> [--preview t1,t2,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import vs
from vs import ptext, rrect, tw, fit, face

def emoji(cr, e, *a, **k):
    vs.emoji(cr, e.replace('\ufe0f', ''), *a, **k)
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR
from canada import rings

W, H, FPS = 1080, 1920, 30
MAPY = 880
vs.VOICES['nar'] = 'en-GB-RyanNeural'

BG = hexc('#0C0B10')
WATER0, WATER1 = hexc('#13202E'), hexc('#0A121C')
LAND, COAST = hexc('#2F2A23'), hexc('#6B5B43')
RIVER = hexc('#4FA3D9')
GOLD, CRIMSON, WHITE, AMBER, ICE = hexc('#E8B54A'), hexc('#D7263D'), hexc('#FFFFFF'), hexc('#D98A1F'), hexc('#BFE6FF')
PARCH = hexc('#F2E3C2')
INK = (0.03, 0.02, 0.05)

P = {  # places (lon, lat)
    'uppsala': (17.64, 59.86), 'novgorod': (31.27, 58.52), 'ladoga': (32.30, 60.00), 'kyiv': (30.52, 50.45),
    'smolensk': (32.05, 54.78), 'constantinople': (28.98, 41.01), 'moscow': (37.62, 55.75), 'vladimir': (40.40, 56.13),
    'ryazan': (39.74, 54.63), 'tver': (35.90, 56.86), 'rostov': (39.40, 57.18), 'sarai': (47.40, 46.97),
    'peipus': (27.50, 58.70), 'kulikovo': (38.67, 53.65), 'paris': (2.35, 48.86), 'nidaros': (10.40, 63.43),
    'esztergom': (18.74, 47.79), 'kaluga': (36.25, 54.53),
}
KIEV_RUS = [(24, 49.5), (23.5, 52), (25, 54.5), (27, 56.5), (27.5, 58.5), (29, 60.5), (33, 61.8), (38, 61.5), (42, 59.5),
            (44, 57), (42, 55), (39, 53.5), (37, 52), (35, 50), (33, 48.8), (30, 48.5), (27, 48.8)]
HORDE = [(28, 45.5), (29, 48), (33, 50), (38, 51), (42, 53.5), (48, 56), (54, 58), (60, 58), (68, 56), (78, 54), (88, 51),
         (88, 44), (80, 42), (70, 40), (60, 38.5), (55, 39.5), (53, 41), (49, 42.5), (46, 42.5), (41, 44), (37, 45),
         (33, 44.5), (30, 45)]
MOSCOW_1300 = [(35.5, 55.2), (36.3, 56.4), (38.5, 56.6), (39.8, 55.7), (38.9, 54.8), (36.8, 54.7)]
MUSCOVY_1480 = [(31, 56), (28.5, 57.8), (28, 59.5), (30, 61), (33, 63), (38, 66), (45, 66.5), (52, 65), (57, 63), (56, 60),
                (50, 58), (46, 56.5), (43, 55.3), (40, 54), (37, 53.5), (35, 54), (33, 55)]
SPLITS = [[(26, 55.5), (30, 55.2), (33, 55.8), (36, 55)], [(31, 52.5), (34, 53), (37, 54.2), (40, 56.5)],
          [(28, 51), (31, 50.9), (33.5, 51.5)], [(33, 58.5), (36, 57.6), (39, 58.2), (42, 57.8)], [(36, 55), (36.5, 52.3)]]
VIKING = [P['uppsala'], (19.5, 59.6), (22, 59.6), (25, 60), (28.5, 60), (30.3, 59.95), (31.2, 60.3), P['ladoga'],
          P['novgorod'], (31.4, 57.5), (31.5, 56.5), P['smolensk'], (30.8, 53.2), (30.5, 51.5), P['kyiv'], (32.5, 48.5),
          (33, 47), (31.8, 46.6), (30.5, 44.5), (29.5, 42.5), P['constantinople']]
UGRA = [(34.0, 54.7), (34.6, 54.5), (35.0, 54.5), (35.6, 54.65), (36.2, 54.55), (36.45, 54.5)]

# key, narration, year (None keeps the previous), camera (lon, lat, px per km), chapter card, medallion card
BEATS = [
    ('today', "Russia is the largest country on Earth. Eleven time zones. Seventeen million square kilometres.",
     'TODAY', (100, 63, 0.105), None, None),
    ('past', "But twelve hundred years ago... it didn't exist at all.", 862, (100, 63, 0.105), None, None),
    ('title', "This is how it all began.", 862, (33, 54, 0.32), None, None),
    ('forest', "In the ninth century, these lands were dense forest, home to East Slavic tribes... and crossed by mighty rivers.",
     862, (33, 55, 0.5), ('I', 'RIVERS AND RAIDERS'), None),
    ('vikings', "Scandinavian traders, known as the Varangians, used those rivers as highways, sailing all the way to Constantinople.",
     862, (27, 51, 0.36), None, None),
    ('rurik', "In 862, according to the old chronicles, the people of Novgorod invited a Varangian named Rurik to rule over them.",
     862, (31.3, 58.3, 0.85), None, ('👑', 'RURIK', 'Varangian prince · r. 862–879')),
    ('dynasty', "His dynasty would rule for more than seven hundred years.", 862, (31.3, 57.5, 0.7), None, None),
    ('oleg', "In 882, his successor Oleg sailed south and seized Kyiv. A new power was born: Kievan Rus', the shared ancestor of Russia, Ukraine and Belarus.",
     882, (31, 54.5, 0.5), ('II', 'THE RISE OF KYIV'), ('⚔️', 'OLEG', 'Prince of Kyiv · r. 882–912')),
    ('faith', "In 988, Prince Vladimir chose a faith for his people. The chronicle says he rejected Islam because, as he put it, drinking is the joy of the Rus'.",
     988, (31, 52, 0.45), None, ('⛪', 'VLADIMIR THE GREAT', 'Grand Prince · r. 980–1015')),
    ('orthodox', "Instead, he chose Orthodox Christianity from Constantinople... a decision that shapes Russia to this day.",
     988, (30, 47, 0.33), None, None),
    ('yaroslav', "Under Yaroslav the Wise, Kyiv became one of the richest cities in Europe. His daughters became queens of France, Norway and Hungary.",
     1019, (17, 54.5, 0.2), None, ('📜', 'YAROSLAV THE WISE', 'Grand Prince · r. 1019–1054')),
    ('split', "But after Yaroslav, his heirs fought each other, and the realm split apart. In 1147, a small town called Moscow appears in the chronicles for the first time.",
     1147, (34, 55, 0.5), ('III', 'THE STORM FROM THE EAST'), None),
    ('mongols', "Then, in 1237, the Mongols arrived. Batu Khan's armies burned city after city. In 1240, Kyiv fell.",
     1240, (40, 53.5, 0.33), None, ('🏹', 'BATU KHAN', 'Mongol commander · d. 1255')),
    ('horde', "For nearly two and a half centuries, the Russian princes would pay tribute to the Golden Horde.",
     1240, (52, 51, 0.15), None, None),
    ('nevsky', "In the northwest, Prince Alexander Nevsky crushed the Teutonic Knights on a frozen lake: the Battle on the Ice.",
     1242, (27.6, 58.6, 1.5), None, ('🛡️', 'ALEXANDER NEVSKY', 'Prince of Novgorod · 1221–1263')),
    ('kalita', "Meanwhile, Moscow played a clever game. Its prince, Ivan Kalita, nicknamed Moneybag, collected taxes for the Khans... and grew rich and powerful.",
     1325, (40, 52.5, 0.36), ('IV', 'THE RISE OF MOSCOW'), ('💰', 'IVAN I KALITA', 'Prince of Moscow · r. 1325–1340')),
    ('kulikovo', "In 1380, Prince Dmitry defeated a Horde army at Kulikovo Field.",
     1380, (38.6, 54.6, 0.8), None, ('⚔️', 'DMITRY DONSKOY', 'Prince of Moscow · r. 1359–1389')),
    ('ugra', "And in 1480, Ivan the Great faced down the Horde at the Ugra River. The Mongols retreated without a major battle.",
     1480, (35.3, 54.62, 2.6), None, ('👑', 'IVAN III THE GREAT', 'Grand Prince · r. 1462–1505')),
    ('free', "After two hundred and forty years, Moscow was free.", 1480, (42, 58, 0.2), None, None),
    ('cliff', "But its rise was only beginning... and Ivan's grandson would become one of the most feared rulers in history.",
     1480, (37.6, 55.75, 0.7), None, None),
    ('next', "Ivan the Terrible. That's Part Two. Follow, so you don't miss it.", 1533, (37.6, 55.75, 0.9), None, None),
]

# ---------- projection ----------
LON0, LAT0 = 60.0, 58.0
def laea(lon, lat):
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    l, p, p0 = np.radians(lon - LON0), np.radians(lat), math.radians(LAT0)
    cosc = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l)
    k = np.sqrt(2 / np.maximum(1 + cosc, 1e-9))
    return 6371 * k * np.cos(p) * np.sin(l), 6371 * k * (math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l))

class Geo:
    def __init__(self, d):
        def keep_box(x, y): return -30 < x.mean() < 200 and y.mean() > 25
        def load(path, kind):
            out = []
            for f in json.load(open(os.path.join(d, path)))['features']:
                g = f['geometry']
                if kind == 'poly':
                    for r in rings(g):
                        if keep_box(r[:, 0], r[:, 1]) and len(r) > 3: out.append(laea(r[:, 0], r[:, 1]))
                else:
                    parts = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
                    for c in parts:
                        c = np.array(c, float)
                        if keep_box(c[:, 0], c[:, 1]): out.append((f['properties'].get('name') or '', laea(c[:, 0], c[:, 1])))
            return out
        self.land = load('ne_50m_land.geojson', 'poly')
        self.lakes = load('ne_50m_lakes.geojson', 'poly')
        self.rivers = load('ne_50m_rivers_lake_centerlines.geojson', 'line')
        c = json.load(open(os.path.join(d, 'countries_50m.geojson')))
        self.borders = [laea(r[:, 0], r[:, 1]) for f in c['features'] for r in rings(f['geometry'])
                        if keep_box(r[:, 0], r[:, 1]) and len(r) > 3]
        self.russia = [laea(r[:, 0], r[:, 1]) for f in c['features'] if f['properties']['NAME'] == 'Russia' for r in rings(f['geometry'])]

G = None
TL = None

# ---------- timeline ----------
def build(voice):
    t, beats, clips = 0.25, [], []
    for key, text, year, cam, chap, card in BEATS:
        b = dict(key=key, text=text, year=year, cam=cam, chap=chap, card=card, start=t)
        lead = 1.55 if chap else (0.15 if key == 'today' else 0.35)
        a = voice.get('nar', text)
        b['l0'] = t + lead; b['l1'] = b['l0'] + len(a) / SR
        clips.append((b['l0'], a))
        tail = {'title': 1.6, 'past': 0.9, 'next': 2.2, 'free': 0.9}.get(key, 0.45)
        t = b['l1'] + tail; b['end'] = t
        beats.append(b)
    return dict(beats=beats, by={b['key']: b for b in beats}, clips=clips, dur=t)

def bt(key): return TL['by'][key]

def camera(t):
    beats = TL['beats']
    prev = beats[0]['cam']; cur = prev
    for b in beats:
        if t < b['start']: break
        k = ease_io(prog(t, b['start'], b['start'] + 1.4))
        nxt = b['cam']
        cur = (lerp(prev[0], nxt[0], k), lerp(prev[1], nxt[1], k), math.exp(lerp(math.log(prev[2]), math.log(nxt[2]), k)))
        prev = nxt
    x, y = laea(cur[0], cur[1])
    return float(x), float(y), cur[2] * (1 + 0.015 * math.sin(t * 0.35))

def S(cam, x, y): return W / 2 + (np.asarray(x) - cam[0]) * cam[2], MAPY - (np.asarray(y) - cam[1]) * cam[2]
def L(cam, lon, lat):
    x, y = laea(lon, lat); return S(cam, x, y)

def path_xy(cr, cam, rs, close=True):
    for x, y in rs:
        X, Y = S(cam, x, y)
        if X.max() < -200 or X.min() > W + 200 or Y.max() < -200 or Y.min() > H + 200: continue
        cr.move_to(X[0], Y[0])
        for a, b in zip(X[1:], Y[1:]): cr.line_to(a, b)
        if close: cr.close_path()

def poly(cr, cam, pts, fill, a, edge=None, lw=3, dash=None):
    if a <= 0: return
    X, Y = L(cam, [p[0] for p in pts], [p[1] for p in pts])
    cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:], Y[1:])]; cr.close_path()
    cr.set_source_rgba(*fill[:3], a); cr.fill_preserve()
    if edge:
        if dash: cr.set_dash(dash)
        cr.set_source_rgba(*edge[:3], min(1, a * 2.5)); cr.set_line_width(lw); cr.stroke(); cr.set_dash([])
    cr.new_path()

def smooth(pts, n=16):
    p = np.array([pts[0]] + list(pts) + [pts[-1]], float); out = []
    for i in range(1, len(p) - 2):
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p[i] + (-p[i - 1] + p[i + 1]) * s + (2 * p[i - 1] - 5 * p[i] + 4 * p[i + 1] - p[i + 2]) * s * s
                              + (-p[i - 1] + 3 * p[i] - 3 * p[i + 1] + p[i + 2]) * s ** 3))
    out.append(p[-2]); return np.array(out)

def route(cr, cam, pts, k, col, width=6, head=None, head_size=70, dashed_rest=True, arrow=False):
    X, Y = L(cam, [p[0] for p in pts], [p[1] for p in pts])
    sp = smooth(list(zip(X, Y)))
    seg = np.hypot(*np.diff(sp, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)]) / max(seg.sum(), 1e-6)
    if dashed_rest:
        cr.new_path(); cr.move_to(*sp[0]); [cr.line_to(*q) for q in sp[1:]]
        cr.set_dash([10, 12]); cr.set_source_rgba(*col[:3], 0.3); cr.set_line_width(3); cr.stroke(); cr.set_dash([])
    if k <= 0: return
    n = min(int(np.searchsorted(cum, k)), len(sp) - 1)
    f = 0 if n == 0 else (k - cum[n - 1]) / max(1e-9, cum[n] - cum[n - 1])
    hx, hy = lerp(sp[max(n - 1, 0)][0], sp[n][0], f), lerp(sp[max(n - 1, 0)][1], sp[n][1], f)
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    for lw, al in ((width * 4, 0.15), (width * 2, 0.35), (width, 1)):
        cr.new_path(); cr.move_to(*sp[0]); [cr.line_to(*q) for q in sp[1:n]]; cr.line_to(hx, hy)
        cr.set_source_rgba(*col[:3], al); cr.set_line_width(lw); cr.stroke()
    ang = math.atan2(sp[n][1] - sp[max(n - 1, 0)][1], sp[n][0] - sp[max(n - 1, 0)][0])
    if arrow:
        cr.save(); cr.translate(hx, hy); cr.rotate(ang)
        cr.move_to(width * 3.2, 0); cr.line_to(-width * 2, width * 2.6); cr.line_to(-width * 2, -width * 2.6); cr.close_path()
        cr.set_source_rgba(*col[:3], 1); cr.fill(); cr.restore()
    if head and k < 1: emoji(cr, head, hx, hy - 10, head_size, 1)

def pin(cr, cam, place, label, t, t0, col=GOLD, side='r', size=34, a=1.0):
    k = prog(t, t0, t0 + 0.4)
    if k <= 0 or a <= 0: return
    x, y = L(cam, *P[place] if isinstance(place, str) else place)
    r = prog(t, t0, t0 + 1.2)
    cr.new_path(); cr.arc(x, y, 10 + 40 * ease_out(r), 0, 2 * math.pi); cr.set_source_rgba(*col[:3], (1 - r) * a); cr.set_line_width(3); cr.stroke()
    s = ease_back(k, 3)
    cr.new_path(); cr.arc(x, y, 11 * s, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], a); cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(3); cr.stroke()
    if label:
        lk = ease_out(prog(t, t0 + 0.1, t0 + 0.5)) * a
        if side == 'r': ptext(cr, label, x + 24, y + size * 0.35, size, WHITE, lk, fam='Poppins ExtraBold', anchor='l', sw=6)
        elif side == 'l': ptext(cr, label, x - 24, y + size * 0.35, size, WHITE, lk, fam='Poppins ExtraBold', anchor='r', sw=6)
        elif side == 't': ptext(cr, label, x, y - 30, size, WHITE, lk, fam='Poppins ExtraBold', sw=6)
        else: ptext(cr, label, x, y + 30 + size, size, WHITE, lk, fam='Poppins ExtraBold', sw=6)

def at(cr, cam, place, e, size, a=1.0, rot=0.0, dy=0):
    x, y = L(cam, *P[place] if isinstance(place, str) else place); emoji(cr, e, x, y + dy, size, a, rot)

def win(key_a, key_b=None, fin=0.5, fout=0.5, t=0.0):
    a = bt(key_a)['start']; b = bt(key_b or key_a)['end']
    return ease_out(prog(t, a + 0.3, a + 0.3 + fin)) * (1 - ease_io(prog(t, b - fout, b)))

# ---------- base map ----------
def draw_map(cr, t, cam):
    cr.set_source_rgba(*BG); cr.paint()
    g = cairo.RadialGradient(W / 2, MAPY, 100, W / 2, MAPY, 1300)
    g.add_color_stop_rgba(0, *WATER0[:3], 1); g.add_color_stop_rgba(1, *WATER1[:3], 1)
    cr.set_source(g); cr.paint()
    modern = 1 - ease_io(prog(t, bt('past')['l0'] + 0.5, bt('past')['l1']))
    land = [lerp(a, b, modern * 0.35) for a, b in zip(LAND[:3], (0.17, 0.2, 0.26))]
    cr.new_path(); path_xy(cr, cam, G.land); cr.set_source_rgba(*land, 1); cr.fill_preserve()
    cr.set_source_rgba(*COAST[:3], 0.9); cr.set_line_width(1.6); cr.stroke()
    cr.new_path(); path_xy(cr, cam, G.lakes); cr.set_source_rgba(*WATER0[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*COAST[:3], 0.7); cr.set_line_width(1); cr.stroke()
    if modern > 0:
        cr.new_path(); path_xy(cr, cam, G.borders); cr.set_source_rgba(1, 1, 1, 0.18 * modern); cr.set_line_width(1); cr.stroke()
        cr.new_path(); path_xy(cr, cam, G.russia); cr.set_source_rgba(*CRIMSON[:3], 0.75 * modern); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, 0.9 * modern); cr.set_line_width(2); cr.stroke()
    # rivers: always faint, glowing when the story is about them
    glow = win('forest', 'vikings', t=t)
    cr.new_path()
    for name, (x, y) in G.rivers:
        X, Y = S(cam, x, y); cr.move_to(X[0], Y[0]); [cr.line_to(a, b) for a, b in zip(X[1:], Y[1:])]
    cr.set_source_rgba(*RIVER[:3], 0.35 + 0.4 * glow); cr.set_line_width(1.6 + 2.0 * glow); cr.stroke()
    if glow > 0:
        cr.new_path()
        for name, (x, y) in G.rivers:
            if name in ('Volga', 'Dnipro', 'Neva', 'Daugava', 'Don'):
                X, Y = S(cam, x, y); cr.move_to(X[0], Y[0]); [cr.line_to(a, b) for a, b in zip(X[1:], Y[1:])]
        cr.set_source_rgba(*RIVER[:3], 0.25 * glow); cr.set_line_width(14); cr.stroke()
    # vignette
    g = cairo.RadialGradient(W / 2, H / 2, 500, W / 2, H / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.75)
    cr.set_source(g); cr.paint()

# ---------- story layers ----------
def draw_story(cr, t, cam):
    # TODAY: eleven time zones
    b = bt('today')
    if t < b['end'] + 0.5:
        a = 1 - ease_io(prog(t, b['end'] - 0.3, b['end'] + 0.3))
        for i in range(11):
            k = pop_k(t, b['l0'] + 1.6 + i * 0.13)
            if k <= 0: continue
            lon = 30 + i * 14.5
            X, Y = L(cam, np.full(30, lon), np.linspace(44, 78, 30))
            cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:], Y[1:])]
            cr.set_dash([8, 8]); cr.set_source_rgba(1, 1, 1, 0.45 * a); cr.set_line_width(2); cr.stroke(); cr.set_dash([])
            x, y = L(cam, lon + 7, 75 if i % 2 else 72)
            cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, str(i + 1), 0, 0, 40, GOLD, a, sw=6); cr.restore()
    # forests and tribes
    a = win('forest', t=t)
    if a > 0:
        rng = np.random.default_rng(3)
        for i in range(55):
            lon, lat = rng.uniform(24, 44), rng.uniform(49.5, 61)
            k = pop_k(t, bt('forest')['l0'] + 0.2 + i * 0.03)
            if k > 0: at(cr, cam, (lon, lat), '🌲', 46 * k, a * 0.9)
        x, y = L(cam, 36, 56.5)
        ptext(cr, 'EAST SLAVIC TRIBES', x, y, 40, PARCH, a * ease_out(prog(t, bt('forest')['l0'] + 1.5, bt('forest')['l0'] + 2.0)), fam='Poppins ExtraBold', sw=6)
        for name, lon, lat in (('DNIPRO', 31.2, 52.6), ('VOLGA', 42.5, 57.2)):
            x, y = L(cam, lon, lat); ptext(cr, name, x, y, 30, RIVER, a * ease_out(prog(t, bt('forest')['l0'] + 4, bt('forest')['l0'] + 4.5)), fam='Poppins ExtraBold', sw=5)
    # Varangian route
    b = bt('vikings'); a = win('vikings', 'rurik', t=t)
    if a > 0:
        k = ease_io(prog(t, b['l0'] + 0.3, b['l1'] - 0.2))
        route(cr, cam, VIKING, k, GOLD, width=5, head='⛵', head_size=64)
        pin(cr, cam, 'uppsala', 'SCANDINAVIA', t, b['l0'] + 0.2, GOLD, 'l', a=a)
        pin(cr, cam, 'constantinople', 'CONSTANTINOPLE', t, b['l1'] - 0.4, GOLD, 'r', a=a)
        x, y = L(cam, 22, 55.5); qa = win('vikings', t=t) * ease_out(prog(t, b['l0'] + 2, b['l0'] + 2.5))
        ptext(cr, '"FROM THE VARANGIANS', x, y, 30, PARCH, qa, fam='Poppins ExtraBold', sw=5)
        ptext(cr, 'TO THE GREEKS"', x, y + 38, 30, PARCH, qa, fam='Poppins ExtraBold', sw=5)
    # Rurik in Novgorod
    a = win('rurik', 'dynasty', t=t)
    if a > 0:
        pin(cr, cam, 'novgorod', 'NOVGOROD', t, bt('rurik')['l0'] + 2.0, CRIMSON, 'r', 40, a)
        at(cr, cam, 'novgorod', '👑', 90 * pop_k(t, bt('rurik')['l0'] + 4.6), a, dy=-90)
    # dynasty bar
    b = bt('dynasty'); a = win('dynasty', t=t)
    if a > 0:
        k = ease_io(prog(t, b['l0'], b['l1']))
        x0, x1, y = 120, 960, 1180
        rrect(cr, x0, y - 26, x1 - x0, 52, 26); cr.set_source_rgba(1, 1, 1, 0.12 * a); cr.fill()
        rrect(cr, x0, y - 26, max(52, (x1 - x0) * k), 52, 26); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
        ptext(cr, '862', x0, y - 50, 40, WHITE, a, anchor='l', sw=6)
        ptext(cr, '1598', x1, y - 50, 40, WHITE, a * clamp(k * 3 - 2), anchor='r', sw=6)
        ptext(cr, 'RURIKID DYNASTY', 540, y + 80, 44, GOLD, a, sw=7)
        ptext(cr, f'{int(736 * k)} YEARS', 540, y + 16, 34, INK, a, sw=0, shadow=False)
    # Kievan Rus'
    b = bt('oleg')
    a = ease_out(prog(t, b['l0'] + 2.5, b['l0'] + 3.3)) * (1 - ease_io(prog(t, bt('mongols')['l0'] + 4, bt('mongols')['l1'])))
    if a > 0:
        poly(cr, cam, KIEV_RUS, CRIMSON, 0.32 * a, CRIMSON, 3)
    a2 = win('oleg', t=t)
    if a2 > 0:
        route(cr, cam, [P['novgorod'], P['smolensk'], (30.8, 53.2), P['kyiv']], ease_io(prog(t, b['l0'] + 0.5, b['l0'] + 2.6)), WHITE, 6, arrow=True, dashed_rest=False)
        pin(cr, cam, 'kyiv', 'KYIV', t, b['l0'] + 2.4, GOLD, 'r', 42, a2)
        x, y = L(cam, 33, 56.2)
        k = pop_k(t, b['l0'] + 3.6)
        cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, "KIEVAN RUS'", 0, 0, 64, WHITE, a2, sw=9); cr.restore()
        k = ease_out(prog(t, b['l0'] + 6.5, b['l0'] + 7.0))
        if k > 0:
            txt = 'ANCESTOR OF RUSSIA · UKRAINE · BELARUS'; w = tw(cr, txt, 30, 'Poppins ExtraBold')
            rrect(cr, 540 - w / 2 - 26, 1170, w + 52, 60, 30); cr.set_source_rgba(*GOLD[:3], a2 * k); cr.fill()
            ptext(cr, txt, 540, 1211, 30, INK, a2 * k, fam='Poppins ExtraBold', sw=0, shadow=False)
    # Faith choice
    b = bt('faith'); a = win('faith', t=t)
    if a > 0:
        opts = [('🕌', 'ISLAM'), ('🕍', 'JUDAISM'), ('⛪', 'CATHOLIC'), ('⛪', 'ORTHODOX')]
        for i, (e, lab) in enumerate(opts):
            k = pop_k(t, b['l0'] + 1.0 + i * 0.25)
            if k <= 0: continue
            x = 165 + i * 250; y = 760
            cr.save(); cr.translate(x, y); cr.scale(k, k)
            rrect(cr, -110, -110, 220, 230, 34); cr.set_source_rgba(0.05, 0.05, 0.08, 0.85 * a); cr.fill_preserve()
            cr.set_source_rgba(*(GOLD if i == 3 else WHITE)[:3], 0.8 * a); cr.set_line_width(4); cr.stroke()
            emoji(cr, e, 0, -30, 110, a); ptext(cr, lab, 0, 85, 30, WHITE, a, fam='Poppins ExtraBold', sw=5)
            cr.restore()
        xk = pop_k(t, b['l0'] + 5.5)
        if xk > 0:
            cr.save(); cr.translate(165, 760); cr.scale(xk, xk)
            cr.set_source_rgba(*CRIMSON[:3], a); cr.set_line_width(18); cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.move_to(-80, -80); cr.line_to(80, 80); cr.move_to(80, -80); cr.line_to(-80, 80); cr.stroke(); cr.restore()
            emoji(cr, '🍷', 165, 920, 90 * xk, a, rot=0.3 * math.sin(t * 5))
        qk = ease_out(prog(t, b['l1'] - 3.4, b['l1'] - 2.8))
        if qk > 0:
            rrect(cr, 80, 1000, 920, 190, 30); cr.set_source_rgba(*PARCH[:3], 0.95 * a * qk); cr.fill()
            ptext(cr, '"DRINKING IS THE JOY', 540, 1070, 48, INK, a * qk, sw=0, shadow=False)
            ptext(cr, "OF THE RUS'\"", 540, 1128, 48, INK, a * qk, sw=0, shadow=False)
            ptext(cr, '— PRIMARY CHRONICLE', 540, 1172, 26, (0.4, 0.3, 0.2), a * qk, fam='Poppins SemiBold', sw=0, shadow=False)
    # Orthodox link
    b = bt('orthodox'); a = win('orthodox', t=t)
    if a > 0:
        route(cr, cam, [P['constantinople'], (30.2, 44.5), (31.5, 47), P['kyiv']], ease_io(prog(t, b['l0'] + 0.3, b['l0'] + 2.5)), GOLD, 7, dashed_rest=False)
        pin(cr, cam, 'constantinople', 'CONSTANTINOPLE', t, b['l0'], GOLD, 'r', 34, a)
        pin(cr, cam, 'kyiv', 'KYIV', t, b['l0'], GOLD, 'r', 38, a)
        at(cr, cam, 'kyiv', '⛪', 110 * pop_k(t, b['l0'] + 2.4), a, dy=-100)
        x, y = L(cam, 30.5, 45.6)
        k = pop_k(t, b['l0'] + 2.6)
        cr.save(); cr.translate(x, y + 30); cr.scale(k, k); ptext(cr, 'ORTHODOX CHRISTIANITY', 0, 0, 40, GOLD, a, sw=7); cr.restore()
    # Yaroslav's daughters
    b = bt('yaroslav'); a = win('yaroslav', t=t)
    if a > 0:
        pin(cr, cam, 'kyiv', 'KYIV', t, b['l0'], GOLD, 'r', 38, a)
        at(cr, cam, 'kyiv', '💎', 70 * pop_k(t, b['l0'] + 1.5), a, dy=-70)
        for i, (pl, lab, side) in enumerate((('paris', 'QUEEN OF FRANCE', 'b'), ('nidaros', 'QUEEN OF NORWAY', 't'), ('esztergom', 'QUEEN OF HUNGARY', 'b'))):
            t0 = b['l1'] - 4.2 + i * 0.9
            mid = ((P['kyiv'][0] + P[pl][0]) / 2, (P['kyiv'][1] + P[pl][1]) / 2 + 3)
            route(cr, cam, [P['kyiv'], mid, P[pl]], ease_io(prog(t, t0, t0 + 0.9)), hexc('#FF7AB6'), 4, dashed_rest=False, arrow=True)
            pin(cr, cam, pl, lab, t, t0 + 0.9, hexc('#FF7AB6'), side, 28, a)
            at(cr, cam, pl, '👑', 60 * pop_k(t, t0 + 1.0), a, dy=-60 if side == 'b' else 70)
    # Split & Moscow
    b = bt('split'); a = win('split', t=t)
    if a > 0:
        for i, ln in enumerate(SPLITS):
            k = ease_out(prog(t, b['l0'] + 0.8 + i * 0.35, b['l0'] + 1.6 + i * 0.35))
            if k <= 0: continue
            X, Y = L(cam, [p[0] for p in ln], [p[1] for p in ln])
            n = max(2, int(len(X) * k + 1))
            jag = np.array([(x + 6 * math.sin(j * 7.3), y + 6 * math.cos(j * 5.1)) for j, (x, y) in enumerate(zip(X, Y))])
            cr.new_path(); cr.move_to(*jag[0]); [cr.line_to(*q) for q in jag[1:n]]
            cr.set_source_rgba(1, 1, 1, 0.9 * a); cr.set_line_width(5); cr.stroke()
        for i, (lon, lat) in enumerate(((28, 53), (34, 57), (39, 55), (30.5, 51.5))):
            k = pop_k(t, b['l0'] + 2.5 + i * 0.3)
            if k > 0: at(cr, cam, (lon, lat), '⚔️', 60 * k, a, rot=0.2 * math.sin(t * 4 + i))
        mk = b['l1'] - 4.8
        pin(cr, cam, 'moscow', 'MOSCOW', t, mk, GOLD, 'r', 46, a)
        k = ease_out(prog(t, mk + 0.5, mk + 1.0))
        if k > 0:
            x, y = L(cam, *P['moscow']); ptext(cr, 'first mentioned · 1147', x + 26, y + 52, 28, PARCH, a * k, fam='Poppins SemiBold', anchor='l', sw=5)
    # Mongols
    b = bt('mongols'); a = win('mongols', t=t)
    if a > 0:
        tgts = [('ryazan', (52, 54.5)), ('vladimir', (50, 57)), ('moscow', (44, 56.5)), ('kyiv', (40, 49.5))]
        for i, (pl, src) in enumerate(tgts):
            t0 = b['l0'] + 0.6 + i * (1.3 if i < 3 else 2.2)
            route(cr, cam, [src, ((src[0] + P[pl][0]) / 2, (src[1] + P[pl][1]) / 2 + 0.6), P[pl]], ease_io(prog(t, t0, t0 + 1.1)), AMBER, 9, head='🐎', head_size=60, dashed_rest=False, arrow=True)
            fk = pop_k(t, t0 + 1.1)
            if fk > 0:
                at(cr, cam, pl, '🔥', 80 * fk * (1 + 0.08 * math.sin(t * 12 + i)), a, dy=-30)
                pin(cr, cam, pl, pl.upper(), t, t0 + 1.1, AMBER, 'b' if pl != 'vladimir' else 't', 30, a)
    # Golden Horde
    a = ease_out(prog(t, bt('horde')['start'] + 0.4, bt('horde')['l0'] + 1.0)) * (1 - ease_io(prog(t, bt('free')['l0'], bt('free')['l1'])))
    if a > 0:
        poly(cr, cam, HORDE, AMBER, 0.32 * a, AMBER, 4)
        x, y = L(cam, 62, 48)
        ptext(cr, 'GOLDEN HORDE', x, y, 56 if cam[2] < 0.25 else 44, AMBER, a, sw=8)
        pin(cr, cam, 'sarai', 'SARAI', t, bt('horde')['l0'] + 1.0, AMBER, 'b', 30, a)
    b = bt('horde'); a2 = win('horde', t=t)
    if a2 > 0:
        poly(cr, cam, KIEV_RUS, CRIMSON, 0.22 * a2, CRIMSON, 2, dash=[8, 8])
        x, y = L(cam, 34, 57); ptext(cr, 'RUS\' PRINCES', x, y, 34, WHITE, a2, fam='Poppins ExtraBold', sw=6)
        k = pop_k(t, b['l0'] + 1.8)
        if k > 0:
            cr.save(); cr.translate(540, 1180); cr.scale(k, k)
            txt = 'TRIBUTE FOR ~240 YEARS'; w = tw(cr, txt, 44)
            rrect(cr, -w / 2 - 30, -56, w + 60, 86, 43); cr.set_source_rgba(*AMBER[:3], a2); cr.fill()
            ptext(cr, txt, 0, 2, 44, INK, a2, sw=0, shadow=False); cr.restore()
        for i in range(8):
            u = ((t * 0.6 + i / 8) % 1.0)
            x0, y0 = L(cam, 36, 55); x1, y1 = L(cam, *P['sarai'])
            emoji(cr, '🪙', lerp(x0, x1, u), lerp(y0, y1, u) - 60 * math.sin(math.pi * u), 40, a2 * math.sin(math.pi * u))
    # Battle on the Ice
    b = bt('nevsky'); a = win('nevsky', t=t)
    if a > 0:
        route(cr, cam, [(25.6, 58.35), (26.5, 58.55), (27.3, 58.63)], ease_io(prog(t, b['l0'] + 2.0, b['l0'] + 3.4)), hexc('#9AA4B5'), 9, dashed_rest=False, arrow=True)
        route(cr, cam, [(29.6, 58.8), (28.7, 58.74), (27.8, 58.68)], ease_io(prog(t, b['l0'] + 2.0, b['l0'] + 3.4)), CRIMSON, 9, dashed_rest=False, arrow=True)
        x, y = L(cam, 25.8, 58.3); ptext(cr, 'TEUTONIC KNIGHTS', x, y + 110, 30, WHITE, a * ease_out(prog(t, b['l0'] + 2, b['l0'] + 2.5)), fam='Poppins ExtraBold', sw=5)
        x, y = L(cam, 29.4, 58.85); ptext(cr, 'NOVGOROD ARMY', x, y - 90, 30, WHITE, a * ease_out(prog(t, b['l0'] + 2, b['l0'] + 2.5)), fam='Poppins ExtraBold', sw=5)
        k = pop_k(t, b['l0'] + 3.5)
        if k > 0:
            at(cr, cam, (27.55, 58.66), '⚔️', 110 * k, a, rot=0.15 * math.sin(t * 6))
            rng = np.random.default_rng(1); x, y = L(cam, 27.55, 58.66)
            for j in range(9):
                ang = rng.uniform(0, 2 * math.pi); ln = rng.uniform(60, 200) * ease_out(prog(t, b['l0'] + 3.6, b['l0'] + 4.6))
                cr.new_path(); cr.move_to(x, y); cr.line_to(x + math.cos(ang) * ln * 0.5 + 10, y + math.sin(ang) * ln * 0.5 - 8)
                cr.line_to(x + math.cos(ang) * ln, y + math.sin(ang) * ln)
                cr.set_source_rgba(*ICE[:3], a); cr.set_line_width(3); cr.stroke()
            ptext(cr, '1242 · BATTLE ON THE ICE', 540, 1190, 42, ICE, a * ease_out(prog(t, b['l0'] + 4, b['l0'] + 4.5)), sw=7)
        at(cr, cam, (26.3, 59.25), '❄️', 70 * pop_k(t, b['l0'] + 1.0), a * 0.9, rot=t * 0.5)
    # Ivan Kalita: taxes flow to Moscow, then to Sarai
    b = bt('kalita'); a = win('kalita', t=t)
    if a > 0:
        poly(cr, cam, MOSCOW_1300, GOLD, 0.45 * a * ease_out(prog(t, b['l0'] + 1, b['l0'] + 2)), GOLD, 3)
        pin(cr, cam, 'moscow', 'MOSCOW', t, b['l0'] + 0.6, GOLD, 'r', 40, a)
        pin(cr, cam, 'sarai', 'SARAI', t, b['l0'] + 0.6, AMBER, 'r', 34, a)
        for i, pl in enumerate(('novgorod', 'tver', 'rostov', 'vladimir', 'ryazan', 'smolensk')):
            pin(cr, cam, pl, None, t, b['l0'] + 1.5 + i * 0.15, WHITE, a=a)
            for j in range(3):
                u = ((t * 0.7 + j / 3 + i * 0.11) % 1.0)
                if t < b['l0'] + 2: continue
                x0, y0 = L(cam, *P[pl]); x1, y1 = L(cam, *P['moscow'])
                emoji(cr, '🪙', lerp(x0, x1, u), lerp(y0, y1, u), 36, a * math.sin(math.pi * u))
        if t > b['l0'] + 4.5:
            for j in range(5):
                u = ((t * 0.5 + j / 5) % 1.0); x0, y0 = L(cam, *P['moscow']); x1, y1 = L(cam, *P['sarai'])
                emoji(cr, '💰', lerp(x0, x1, u) + 60 * math.sin(math.pi * u), lerp(y0, y1, u), 46, a * math.sin(math.pi * u))
        at(cr, cam, 'moscow', '💰', 90 * pop_k(t, b['l1'] - 1.5) * (1 + 0.1 * math.sin(t * 6)), a, dy=-90)
    # Kulikovo
    b = bt('kulikovo'); a = win('kulikovo', t=t)
    if a > 0:
        route(cr, cam, [P['moscow'], (38.0, 54.8), (38.55, 53.8)], ease_io(prog(t, b['l0'] + 0.4, b['l0'] + 2.0)), CRIMSON, 9, dashed_rest=False, arrow=True)
        route(cr, cam, [(40.2, 52.3), (39.4, 52.9), (38.8, 53.5)], ease_io(prog(t, b['l0'] + 0.4, b['l0'] + 2.0)), AMBER, 9, dashed_rest=False, arrow=True)
        pin(cr, cam, 'moscow', 'MOSCOW', t, b['start'] + 0.3, GOLD, 'r', 36, a)
        k = pop_k(t, b['l0'] + 2.1)
        if k > 0:
            at(cr, cam, 'kulikovo', '⚔️', 120 * k, a, rot=0.15 * math.sin(t * 6))
            ptext(cr, '1380 · KULIKOVO FIELD', 540, 1190, 44, GOLD, a * k, sw=7)
            at(cr, cam, 'kulikovo', '🏆', 70 * pop_k(t, b['l1'] - 1.2), a, dy=-110)
    # Ugra standoff
    b = bt('ugra'); a = win('ugra', t=t)
    if a > 0:
        X, Y = L(cam, [p[0] for p in UGRA], [p[1] for p in UGRA])
        cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:], Y[1:])]
        cr.set_source_rgba(*RIVER[:3], 0.4 * a); cr.set_line_width(26); cr.stroke_preserve()
        cr.set_source_rgba(*RIVER[:3], a); cr.set_line_width(8); cr.stroke()
        x, y = L(cam, 35.3, 54.62); ptext(cr, 'UGRA RIVER', x, y + 70, 34, RIVER, a, fam='Poppins ExtraBold', sw=6)
        ka = pop_k(t, b['l0'] + 1.5); retreat = ease_io(prog(t, b['l1'] - 3.2, b['l1'] - 1.0))
        for i in range(5):
            x, y = L(cam, 34.3 + i * 0.5, 54.8)
            if ka > 0: emoji(cr, '🛡️', x, y - 40, 70 * ka, a)
            x, y = L(cam, 34.3 + i * 0.5, 54.42 - retreat * 0.3)
            if ka > 0: emoji(cr, '🐎', x, y + 40, 70 * ka, a * (1 - retreat * 0.7))
        x, y = L(cam, 35.3, 55.05); ptext(cr, 'MOSCOW', x, y - 40, 36, CRIMSON, a * ka, sw=6)
        x, y = L(cam, 34.05, 54.42 - retreat * 0.3); ptext(cr, 'THE HORDE', x - 50, y + 50, 36, AMBER, a * ka * (1 - retreat * 0.6), anchor='r', sw=6)
        if retreat > 0.2:
            ptext(cr, 'THE GREAT STAND · 1480', 540, 1190, 44, GOLD, a * ease_out(prog(t, b['l1'] - 2.4, b['l1'] - 1.9)), sw=7)
    # Free
    b = bt('free'); a = win('free', t=t) if t < bt('free')['end'] else 1 - ease_io(prog(t, bt('free')['end'] - 0.2, bt('cliff')['l0'] + 1))
    if a > 0 and t >= b['start']:
        poly(cr, cam, MUSCOVY_1480, CRIMSON, 0.4 * a * ease_out(prog(t, b['start'] + 0.3, b['l0'] + 0.8)), WHITE, 3)
        x, y = L(cam, 42, 60.5); ptext(cr, 'GRAND DUCHY OF MOSCOW', x, y, 40, WHITE, a * ease_out(prog(t, b['l0'], b['l0'] + 0.5)), sw=7)
        k = prog(t, b['l1'] - 0.6, b['l1'] - 0.2)
        if k > 0:
            s = lerp(2.4, 1.0, ease_out(k)); sh = 10 * math.sin(t * 70) * (1 - prog(t, b['l1'] - 0.2, b['l1'] + 0.3))
            cr.save(); cr.translate(540 + sh, 1180); cr.rotate(-0.08); cr.scale(s, s)
            w = tw(cr, 'FREE', 120); rrect(cr, -w / 2 - 40, -110, w + 80, 150, 22)
            cr.set_source_rgba(*CRIMSON[:3], a * clamp(k * 3)); cr.set_line_width(10); cr.stroke()
            ptext(cr, 'FREE', 0, 0, 120, CRIMSON, a * clamp(k * 3), sw=10); cr.restore()

def pop_k(t, t0, d=0.4): return max(1e-3, ease_back(prog(t, t0, t0 + d), 2.6))

# ---------- chrome ----------
def year_at(t):
    beats = TL['beats']; prev = None; val = None
    for b in beats:
        if t < b['start']: break
        y = b['year']
        if b['key'] == 'past':
            k = ease_io(prog(t, b['l0'] + 0.3, b['l1']))
            val = lerp(2026, 862, k); prev = 862; continue
        if isinstance(y, int):
            if isinstance(prev, int) and prev != y:
                k = ease_out(prog(t, b['l0'] - 0.2, b['l0'] + 1.2)); val = lerp(prev, y, k)
            else: val = y
            prev = y
        else: val = y; prev = None
    return val

def draw_year(cr, t):
    title = bt('title')
    if title['start'] - 0.2 < t < title['end'] + 0.2: return
    v = year_at(t)
    if v is None: return
    txt = v if isinstance(v, str) else str(int(round(v)))
    a = ease_out(prog(t, 0.2, 0.6))
    ptext(cr, txt, 540, 300, 170 if not isinstance(v, str) else 120, GOLD, a, sw=16)
    era = 'AD' if not isinstance(v, str) else ''
    if era: ptext(cr, era, 540 + tw(cr, txt, 170) / 2 + 52, 300, 46, PARCH, a, fam='Poppins ExtraBold', sw=6)

def chapter_now(t):
    cur = None
    for b in TL['beats']:
        if t >= b['start'] and b['chap']: cur = b['chap']
    return cur

def draw_chapter_label(cr, t):
    ch = chapter_now(t)
    if not ch or t > bt('next')['start']: return
    txt = f'CHAPTER {ch[0]} · {ch[1]}'
    ptext(cr, txt, 540, 110, fit(cr, txt, 34, 960, 'Poppins ExtraBold'), PARCH, 0.9, fam='Poppins ExtraBold', sw=5)

def draw_chapter_card(cr, t):
    for b in TL['beats']:
        if not b['chap']: continue
        t0, t1 = b['start'], b['l0'] - 0.05
        if not (t0 <= t <= t1 + 0.3): continue
        k_in = ease_out(prog(t, t0, t0 + 0.35)); k_out = ease_io(prog(t, t1 - 0.25, t1 + 0.2))
        x = lerp(-W, 0, k_in) + lerp(0, W, k_out)
        cr.save(); cr.translate(x, 0)
        cr.rectangle(0, 700, W, 420); cr.set_source_rgba(0.04, 0.03, 0.05, 0.92); cr.fill()
        cr.rectangle(0, 700, W, 8); cr.set_source_rgba(*GOLD[:3], 1); cr.fill()
        cr.rectangle(0, 1112, W, 8); cr.fill()
        ptext(cr, f'CHAPTER {b["chap"][0]}', 540, 830, 54, GOLD, 1, fam='Poppins ExtraBold', sw=6)
        ptext(cr, b['chap'][1], 540, 960, fit(cr, b['chap'][1], 96, 980), WHITE, 1, sw=12)
        ptext(cr, '◆  ◆  ◆', 540, 1050, 30, GOLD, 1, fam='Poppins SemiBold', sw=0)
        cr.restore()

def draw_title(cr, t):
    b = bt('title')
    a = ease_out(prog(t, b['start'], b['start'] + 0.3)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    cr.set_source_rgba(0.03, 0.02, 0.04, 0.6 * a); cr.paint()
    k1 = pop_k(t, b['start'] + 0.1); k2 = prog(t, b['start'] + 0.35, b['start'] + 0.7); k3 = pop_k(t, b['start'] + 0.9)
    if k1 > 0:
        cr.save(); cr.translate(540, 640); cr.scale(k1, k1); ptext(cr, 'THE ENTIRE HISTORY OF', 0, 0, 56, PARCH, a, fam='Poppins ExtraBold', sw=7); cr.restore()
    if k2 > 0:
        s = lerp(2.6, 1.0, ease_out(k2)); sh = 12 * math.sin(t * 70) * (1 - prog(t, b['start'] + 0.7, b['start'] + 1.1))
        cr.save(); cr.translate(540 + sh, 840); cr.scale(s, s); ptext(cr, 'RUSSIA', 0, 0, 230, CRIMSON, a * clamp(k2 * 3), sw=20); cr.restore()
    if k3 > 0:
        cr.save(); cr.translate(540, 990); cr.scale(k3, k3)
        w = tw(cr, 'PART 01', 70); rrect(cr, -w / 2 - 40, -66, w + 80, 100, 50); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
        ptext(cr, 'PART 01', 0, 8, 70, INK, a, sw=0, shadow=False); cr.restore()
        ptext(cr, 'FROM VIKINGS TO THE MONGOLS · 862–1480', 540, 1110, fit(cr, 'FROM VIKINGS TO THE MONGOLS · 862–1480', 40, 960, 'Poppins ExtraBold'),
              WHITE, a * ease_out(prog(t, b['start'] + 1.2, b['start'] + 1.6)), fam='Poppins ExtraBold', sw=6)
    fl = 1 - prog(t, b['start'] + 0.65, b['start'] + 1.0)
    if 0 < fl < 1: cr.set_source_rgba(1, 1, 1, 0.25 * fl * a); cr.paint()

def draw_card(cr, t):
    for b in TL['beats']:
        if not b['card']: continue
        t0 = b['l0'] + 0.4; t1 = b['end']
        if not (t0 <= t <= t1): continue
        e, name, sub = b['card']
        k = ease_out(prog(t, t0, t0 + 0.45)); out = 1 - ease_io(prog(t, t1 - 0.35, t1))
        a = k * out; x = lerp(-500, 0, k)
        cr.save(); cr.translate(x, 0)
        rrect(cr, 50, 1300, 980, 170, 85); cr.set_source_rgba(0.05, 0.04, 0.07, 0.9 * a); cr.fill_preserve()
        cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
        cr.new_path(); cr.arc(135, 1385, 70, 0, 2 * math.pi)
        g = cairo.RadialGradient(115, 1360, 10, 135, 1385, 70); g.add_color_stop_rgba(0, *GOLD[:3], a); g.add_color_stop_rgba(1, 0.55, 0.38, 0.1, a)
        cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(4); cr.stroke()
        emoji(cr, e, 135, 1380, 84 * ease_back(prog(t, t0 + 0.2, t0 + 0.6), 3), a)
        ptext(cr, name, 230, 1385, fit(cr, name, 58, 760), WHITE, a, anchor='l', sw=8)
        ptext(cr, sub, 232, 1435, fit(cr, sub, 32, 760, 'Poppins SemiBold'), PARCH, a, fam='Poppins SemiBold', anchor='l', sw=5)
        cr.restore()

def draw_timeline(cr, t):
    a = ease_out(prog(t, bt('forest')['start'], bt('forest')['start'] + 0.5)) * (1 - ease_io(prog(t, bt('next')['start'], bt('next')['start'] + 0.5)))
    if a <= 0: return
    v = year_at(t); v = v if isinstance(v, (int, float)) else 862
    x0, x1, y = 90, 990, 1815; y0, y1 = 862, 1480
    cr.new_path(); cr.move_to(x0, y); cr.line_to(x1, y); cr.set_source_rgba(1, 1, 1, 0.25 * a); cr.set_line_width(4); cr.stroke()
    xv = lerp(x0, x1, clamp((v - y0) / (y1 - y0)))
    cr.new_path(); cr.move_to(x0, y); cr.line_to(xv, y); cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(6); cr.stroke()
    for yr in (862, 988, 1147, 1240, 1380, 1480):
        x = lerp(x0, x1, (yr - y0) / (y1 - y0)); on = v >= yr - 0.5
        cr.new_path(); cr.arc(x, y, 9 if on else 6, 0, 2 * math.pi); cr.set_source_rgba(*(GOLD if on else WHITE)[:3], a * (1 if on else 0.4)); cr.fill()
        ptext(cr, str(yr), x, y + 44, 24, WHITE if on else (0.6, 0.6, 0.6), a, fam='Poppins SemiBold', sw=0, shadow=False)
    cr.new_path(); cr.arc(xv, y, 14, 0, 2 * math.pi); cr.set_source_rgba(*GOLD[:3], a); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(3); cr.stroke()

def draw_captions(cr, t):
    for b in TL['beats']:
        l0, l1, s = b['l0'], b['l1'], b['text']
        if not (l0 <= t < l1 + 0.2): continue
        words = s.split()
        wts = np.array([len(w.strip('.,!?:')) + 2.5 + (6 if w.endswith(('.', ',', '...', ':')) else 0) for w in words], float)
        edges = l0 + (l1 - l0) * np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
        cur = int(np.clip(np.searchsorted(edges, t, side='right') - 1, 0, len(words) - 1))
        g0 = (cur // 3) * 3; group = [w.upper() for w in words[g0:g0 + 3]]
        size = 66; face(cr, size); space = cr.text_extents(' ').x_advance
        widths = [cr.text_extents(u).x_advance * (1.12 if g0 + j == cur else 1.0) for j, u in enumerate(group)]
        total = sum(widths) + space * (len(group) - 1); sc = min(1.0, 980 / total)
        cr.save(); cr.translate(540, 1650); cr.scale(sc, sc); x = -total / 2
        for j, (u, w) in enumerate(zip(group, widths)):
            wi = g0 + j; active = wi == cur
            cr.save(); cr.translate(x + w / 2, 0)
            if active:
                k = ease_back(prog(t, edges[wi], edges[wi] + 0.15), 3); cr.scale(1 + 0.12 * k, 1 + 0.12 * k)
            hot = any(ch.isdigit() for ch in u) or u.strip(".,!?:'") in ('RUSSIA', 'RURIK', 'KYIV', 'MOSCOW', 'MONGOLS', 'VIKINGS', 'VARANGIANS', 'NOVGOROD', 'ORTHODOX', 'HORDE', 'TERRIBLE.', 'FREE')
            col = GOLD if active else (hexc('#FFCF70') if hot else WHITE)
            ptext(cr, u, 0, 0, size, col, 1.0 if wi <= cur else 0.7, sw=10)
            cr.restore(); x += w + space
        cr.restore(); return

def draw_hook_text(cr, t):
    b = bt('today')
    if t > b['end']: return
    a = 1 - ease_io(prog(t, b['end'] - 0.3, b['end']))
    k = pop_k(t, b['l0'] + 0.1)
    if k > 0:
        cr.save(); cr.translate(540, 470); cr.rotate(-0.04); cr.scale(k, k)
        ptext(cr, 'LARGEST COUNTRY ON EARTH', 0, 0, fit(cr, 'LARGEST COUNTRY ON EARTH', 64, 980), WHITE, a, sw=9); cr.restore()
    for txt, y, t0, col in (('11 TIME ZONES', 1180, b['l0'] + 2.2, GOLD), ('17.1 MILLION KM²', 1290, b['l0'] + 3.6, CRIMSON)):
        k = pop_k(t, t0)
        if k > 0:
            cr.save(); cr.translate(540, y); cr.scale(k, k); w = tw(cr, txt, 64)
            rrect(cr, -w / 2 - 40, -70, w + 80, 104, 52); cr.set_source_rgba(*col[:3], a); cr.fill()
            ptext(cr, txt, 0, 4, 64, INK if col is GOLD else WHITE, a, sw=0, shadow=False); cr.restore()
    b2 = bt('past')
    if b2['start'] <= t <= b2['end']:
        a2 = ease_out(prog(t, b2['l0'] + 1.0, b2['l0'] + 1.5)) * (1 - ease_io(prog(t, b2['end'] - 0.3, b2['end'])))
        cr.save(); cr.translate(540, 1200); cr.scale(pop_k(t, b2['l0'] + 1.0) or 0.001, pop_k(t, b2['l0'] + 1.0) or 0.001)
        ptext(cr, "IT DIDN'T EXIST", 0, 0, 92, CRIMSON, a2, sw=12); cr.restore()

def draw_cliff(cr, t):
    b, n = bt('cliff'), bt('next')
    if t < b['start']: return
    a = ease_out(prog(t, b['start'], b['l0'] + 1.0))
    g = cairo.RadialGradient(W / 2, MAPY, 100, W / 2, MAPY, 1100)
    g.add_color_stop_rgba(0, 0.5, 0.0, 0.05, 0.25 * a); g.add_color_stop_rgba(1, 0.05, 0, 0, 0.85 * a)
    cr.set_source(g); cr.paint()
    pin(cr, None or camera(t), 'moscow', 'MOSCOW', t, b['l0'], CRIMSON, 'r', 44, 1 - ease_io(prog(t, n['l0'], n['l0'] + 0.5)))
    k = prog(t, n['l0'], n['l0'] + 0.4)
    if k > 0:
        s = lerp(3.0, 1.0, ease_out(k)); sh = 14 * math.sin(t * 60) * (1 - prog(t, n['l0'] + 0.4, n['l0'] + 0.9))
        cr.save(); cr.translate(540 + sh, 760); cr.scale(s, s)
        ptext(cr, 'IVAN', 0, 0, 200, CRIMSON, clamp(k * 3), sw=18)
        ptext(cr, 'THE TERRIBLE', 0, 170, fit(cr, 'THE TERRIBLE', 140, 1000), WHITE, clamp(k * 3), sw=14); cr.restore()
        fl = 1 - prog(t, n['l0'] + 0.35, n['l0'] + 0.8)
        if 0 < fl < 1: cr.set_source_rgba(0.8, 0, 0, 0.35 * fl); cr.paint()
    k2 = pop_k(t, n['l0'] + 1.4)
    if k2 > 0:
        cr.save(); cr.translate(540, 1110); cr.scale(k2, k2)
        w = tw(cr, 'PART 02', 70); rrect(cr, -w / 2 - 40, -66, w + 80, 100, 50); cr.set_source_rgba(*GOLD[:3], 1); cr.fill()
        ptext(cr, 'PART 02', 0, 8, 70, INK, 1, sw=0, shadow=False); cr.restore()
    k3 = pop_k(t, n['l0'] + 2.4)
    if k3 > 0:
        cr.save(); cr.translate(540, 1300); cr.scale(k3 * (1 + 0.04 * math.sin(t * 6)), k3 * (1 + 0.04 * math.sin(t * 6)))
        w = tw(cr, 'FOLLOW FOR PART 02', 52); rrect(cr, -w / 2 - 90, -60, w + 180, 94, 47); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, 'FOLLOW FOR PART 02', 30, 4, 52, WHITE, 1, sw=6); emoji(cr, '🔔', -w / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9))
        cr.restore()

def draw_footnote(cr, t):
    a = ease_out(prog(t, bt('oleg')['l0'] + 2.5, bt('oleg')['l0'] + 3)) * (1 - ease_io(prog(t, bt('cliff')['start'], bt('cliff')['start'] + 0.5)))
    if a > 0: ptext(cr, 'Borders approximate', 1040, 1545, 22, (0.7, 0.66, 0.58), 0.8 * a, fam='Poppins SemiBold', anchor='r', sw=0, shadow=False)

def render_frame(cr, t):
    cam = camera(t)
    draw_map(cr, t, cam)
    draw_story(cr, t, cam)
    draw_hook_text(cr, t)
    draw_cliff(cr, t)
    draw_year(cr, t)
    draw_chapter_label(cr, t)
    draw_card(cr, t)
    draw_timeline(cr, t)
    draw_footnote(cr, t)
    draw_title(cr, t)
    draw_chapter_card(cr, t)
    draw_captions(cr, t)
    f = prog(t, TL['dur'] - 0.5, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()
    fi = 1 - prog(t, 0, 0.25)
    if fi > 0: cr.set_source_rgba(0, 0, 0, fi); cr.paint()

# ---------- score ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(21)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n)
    chords = [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 49, 52]]  # Dm Bb C A
    bar = 60 / 84 * 4
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; L = np.arange(int(bar * 1.3 * SR)) / SR
        env = np.minimum(1, L / 0.8) * np.exp(-L * 0.45)
        vib = 1 + 0.003 * np.sin(2 * np.pi * 5 * L)
        pad = sum(0.035 * (np.sin(2 * np.pi * note(m) * vib * L) + 0.5 * np.sin(2 * np.pi * note(m + 12) * 1.002 * L)) for m in ch)
        put(music, ci * bar, pad * env)
        put(music, ci * bar, 0.12 * np.sin(2 * np.pi * note(ch[0] - 24) * L) * env)
    beat = 60 / 84
    t_drums = bt('forest')['start']
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 < t_drums or t0 > bt('cliff')['start']: continue
        if bi % 2 == 0 or bi % 8 == 7:  # taiko-like low tom
            L = np.arange(int(0.6 * SR)) / SR
            put(music, t0, 0.5 * np.sin(2 * np.pi * np.cumsum(60 + 50 * np.exp(-L * 18)) / SR) * np.exp(-L * 6))
            put(music, t0, 0.05 * rng.standard_normal(len(L)) * np.exp(-L * 30))
        M = np.arange(int(0.05 * SR)); put(music, t0 + beat / 2, 0.02 * rng.standard_normal(len(M)) * np.exp(-M / SR * 60))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.7):
        L = np.arange(int(2.0 * SR)) / SR
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 80 * np.exp(-L * 10)) / SR) * np.exp(-L * 2.5))
        put(fx, t0, 0.15 * amp * rng.standard_normal(len(L)) * np.exp(-L * 12))
    def whoosh(t0, amp=0.18):
        nz = rng.standard_normal(int(0.8 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2
        put(fx, t0, amp * np.convolve(nz, np.ones(30) / 30, 'same') * env)
    def tick_roll(t0, t1):
        for k in range(int((t1 - t0) / 0.06)):
            L = np.arange(int(0.03 * SR)) / SR; put(fx, t0 + k * 0.06, 0.08 * np.sin(2 * np.pi * 1800 * L) * np.exp(-L * 90))
    boom(bt('title')['start'] + 0.4, 0.9); boom(bt('next')['l0'], 1.0)
    pb = bt('past'); tick_roll(pb['l0'] + 0.3, pb['l1'])
    for b in T['beats'][1:]:
        whoosh(b['start'] - 0.2, 0.12)
        if b['chap']: boom(b['start'] + 0.15, 0.6)
    for key, off in (('nevsky', 3.5), ('kulikovo', 2.1), ('free', -0.6)):
        boom(bt(key)['l0'] + off if off > 0 else bt(key)['l1'] + off, 0.5)
    mg = bt('mongols')  # hoofbeats
    for k in range(int((mg['l1'] - mg['l0']) / 0.18)):
        L = np.arange(int(0.08 * SR)) / SR; put(fx, mg['l0'] + 0.5 + k * 0.18 + (0.05 if k % 2 else 0), 0.12 * np.sin(2 * np.pi * 90 * L) * np.exp(-L * 40))
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 1.2)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    global G, TL
    data_dir, out = sys.argv[1:3]
    TL = build(vs.EdgeVoice(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_ru')))
    G = Geo(data_dir)
    print(f"duration {TL['dur']:.1f}s")
    for b in TL['beats']: print(f"  {b['key']:9s} {b['start']:6.2f}-{b['end']:6.2f}")
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
