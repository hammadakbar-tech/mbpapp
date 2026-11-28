"""'Why Africa's Borders Look Like This' (9:16): 54 countries, straight lines, the Berlin Conference, the Scramble,
the 2024 'not so arbitrary' twist, independence and today. Word-synced map documentary (engine from china.py).
Usage: python3 afb.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
from china import R, ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON, PARCH, laea, S, L, path_xy
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

R.LON0, R.LAT0 = 17.0, 2.0
R.MAPY = 1000
C.SAY = {None: {'Maasai': 'Mah-sigh'}}
C.HOT = ('africa', 'african', 'africans', 'berlin', 'ethiopia', 'liberia', 'maasai', 'somali', 'kenya', 'tanzania', 'eritrea', 'sudan',
         'nigeria', 'straight', 'lines', 'borders', 'deserts', 'invited', 'independent', 'independence', 'rivers', 'frontiers')
BEATS = [
    ('h1', "Africa has fifty-four countries.", None, None, None, None, None),
    ('h2', "But look at these borders: perfectly straight lines, across deserts, and through entire peoples.", None, None, None, None, None),
    ('h3', "And many of the people who drew them... had never even been there.", None, None, None, None, None),
    ('title', "This is why Africa's borders look like this.", None, None, None, None, None),
    ('pre', "In 1870, Europeans controlled only about a tenth of Africa, mostly along the coasts. The rest was ruled by African kingdoms and peoples, speaking over two thousand languages.",
     None, None, None, ('I', 'BEFORE THE SCRAMBLE'), None),
    ('berlin', "Then, in 1884, fourteen countries met in Berlin to set the rules for claiming Africa. Not a single African was invited.",
     None, None, None, ('II', 'THE SCRAMBLE'), None),
    ('scramble', "Within thirty years, almost the whole continent was taken. By 1914, only Ethiopia and Liberia were still independent.", None, None, None, None, None),
    ('lines', "Many borders were drawn on maps in Europe. In 1890, Britain's prime minister even joked that they were drawing lines where no white man's foot had ever trod.",
     None, None, None, None, None),
    ('split', "Some lines split peoples apart: the Maasai between Kenya and Tanzania, the Somali people across five territories.", None, None, None, None, None),
    ('twist', "But it's not that simple. A 2024 study found that most borders actually followed older frontiers, rivers and lakes. The straight lines were mostly drawn through empty deserts.",
     None, None, None, ('III', 'THE TWIST'), None),
    ('indep', "After the Second World War, independence swept the continent. In 1960 alone, seventeen African countries became independent.",
     None, None, None, ('IV', 'INDEPENDENCE'), None),
    ('keep', "In 1964, the new states agreed to keep the colonial borders, to avoid endless wars over land.", None, None, None, None, None),
    ('new', "So the map barely changed. Only a few new countries were born, like Eritrea in 1993, and South Sudan in 2011: the youngest country in the world.",
     None, None, None, None, None),
    ('today', "Today: fifty-four countries, and over two thousand languages. Nigeria alone has more than five hundred.", None, None, None, None, None),
    ('cta', "Should Africa's borders be redrawn? Tell us in the comments, and follow for more.", None, None, None, None, None),
]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2', 'h3')
bt, w, win = C.bt, C.w, C.win
G = None
FULL = (19, 2, 0.128); NORTH = (14, 30, 0.105)
CAMS = {'berlin': NORTH, 'split': (40, 1, 0.3), 'new': (34, 11, 0.22)}

POWER = {  # colonial power in 1914, by modern country
    'BRITAIN': ('Egypt', 'Sudan', 'S. Sudan', 'Uganda', 'Kenya', 'Nigeria', 'Ghana', 'Sierra Leone', 'Gambia', 'South Africa', 'Botswana',
                'Lesotho', 'eSwatini', 'Zimbabwe', 'Zambia', 'Malawi', 'Somaliland'),
    'FRANCE': ('Morocco', 'Algeria', 'Tunisia', 'Mauritania', 'Senegal', 'Mali', 'Guinea', "Côte d'Ivoire", 'Burkina Faso', 'Niger', 'Chad',
               'Benin', 'Gabon', 'Congo', 'Central African Rep.', 'Madagascar', 'Djibouti', 'Comoros'),
    'GERMANY': ('Togo', 'Cameroon', 'Namibia', 'Tanzania', 'Rwanda', 'Burundi'), 'BELGIUM': ('Dem. Rep. Congo',),
    'PORTUGAL': ('Angola', 'Mozambique', 'Guinea-Bissau', 'Cabo Verde', 'São Tomé and Principe'), 'ITALY': ('Libya', 'Eritrea', 'Somalia'),
    'SPAIN': ('W. Sahara', 'Eq. Guinea'), 'INDEPENDENT': ('Ethiopia', 'Liberia')}
PCOL = {'BRITAIN': hexc('#E0414F'), 'FRANCE': hexc('#3D7BE0'), 'GERMANY': hexc('#8A8F98'), 'BELGIUM': hexc('#F2C94C'), 'PORTUGAL': hexc('#3FB37A'),
        'ITALY': hexc('#9B6BFF'), 'SPAIN': hexc('#F08A2C'), 'INDEPENDENT': hexc('#FFE27A')}
POWER_OF = {c: p for p, cs in POWER.items() for c in cs}
INDEP = {'Libya': 1951, 'Sudan': 1956, 'Morocco': 1956, 'Tunisia': 1956, 'Ghana': 1957, 'Guinea': 1958, 'Sierra Leone': 1961, 'Tanzania': 1961,
         'Burundi': 1962, 'Rwanda': 1962, 'Algeria': 1962, 'Uganda': 1962, 'Kenya': 1963, 'Malawi': 1964, 'Zambia': 1964, 'Gambia': 1965,
         'Botswana': 1966, 'Lesotho': 1966, 'eSwatini': 1968, 'Eq. Guinea': 1968, 'Guinea-Bissau': 1974, 'Mozambique': 1975, 'Cabo Verde': 1975,
         'Comoros': 1975, 'São Tomé and Principe': 1975, 'Angola': 1975, 'Djibouti': 1977, 'Zimbabwe': 1980, 'Namibia': 1990,
         'Egypt': 1922, 'South Africa': 1910, 'Ethiopia': 0, 'Liberia': 0, 'Eritrea': 1993, 'S. Sudan': 2011, 'W. Sahara': 9999}
for c in ('Cameroon', 'Senegal', 'Togo', 'Mali', 'Madagascar', 'Dem. Rep. Congo', 'Somalia', 'Benin', 'Niger', 'Burkina Faso', "Côte d'Ivoire",
          'Chad', 'Central African Rep.', 'Congo', 'Gabon', 'Nigeria', 'Mauritania'): INDEP[c] = 1960  # the Year of Africa: 17
PAL = [hexc(h) for h in ('#F4A261', '#2A9D8F', '#E9C46A', '#E76F51', '#8AB17D', '#6C8EBF', '#C084FC', '#F28482')]
KINGDOMS = [('ETHIOPIA', 39, 9.5), ('MOROCCO', -6, 32), ('ZULU', 31, -28.2), ('ASANTE', -1.6, 6.8), ('SOKOTO', 6.5, 12.5), ('BUGANDA', 32.5, 0.6)]

class Geo:
    def __init__(self, d):
        self.c, self.lab = {}, {}
        for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']:
            p = f['properties']
            if p.get('CONTINENT') != 'Africa': continue
            n = p['NAME']; rs = [r for r in rings(f['geometry']) if len(r) > 3]
            self.c[n] = [laea(r[:, 0], r[:, 1]) for r in rs]
            self.lab[n] = (p.get('LABEL_X') or np.mean([r[:, 0].mean() for r in rs]), p.get('LABEL_Y') or np.mean([r[:, 1].mean() for r in rs]))
        self.raw = {n: [r for r in rings(f['geometry']) if len(r) > 3] for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']
                    if f['properties'].get('CONTINENT') == 'Africa' for n in [f['properties']['NAME']]}
        self.land = [laea(r[:, 0], r[:, 1]) for f in json.load(open(os.path.join(d, 'ne_50m_land.geojson')))['features']
                     for r in rings(f['geometry']) if len(r) > 3 and -40 < r[:, 0].mean() < 80 and -45 < r[:, 1].mean() < 75]
        self.order = sorted(self.c, key=lambda n: (-self.lab[n][1], self.lab[n][0]))
        self.order = [n for n in self.order if n != 'Somaliland']
        # straight borders: long, vertex-free runs that are not coastline (coasts are densely sampled)
        self.straight = []
        allpts = {n: set(map(tuple, np.round(np.concatenate(rs), 2))) for n, rs in self.raw.items()}
        for n, rs in self.raw.items():
            others = set().union(*[allpts[m] for m in allpts if m != n])
            for r in rs:
                dv = np.diff(r, axis=0); ang = np.degrees(np.arctan2(dv[:, 1], dv[:, 0])); ln = np.hypot(dv[:, 0], dv[:, 1])
                i = 0
                while i < len(dv):
                    j, tot = i, 0.0
                    while j < len(dv) and abs((ang[j] - ang[i] + 180) % 360 - 180) < 1.5: tot += ln[j]; j += 1
                    if tot > 2.0:
                        mid = r[(i + j) // 2]
                        if tuple(np.round(mid, 2)) in others and (r[i][0] < r[j][0] or (r[i][0] == r[j][0] and r[i][1] < r[j][1])):
                            self.straight.append((r[i], r[j]))
                    i = max(j, i + 1)
        # map colouring by adjacency
        names = list(self.raw); adj = {n: set() for n in names}
        pts = {n: np.round(np.concatenate(self.raw[n]), 1) for n in names}
        sets = {n: set(map(tuple, pts[n])) for n in names}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if len(sets[a] & sets[b]) > 2: adj[a].add(b); adj[b].add(a)
        self.col = {}
        for n in sorted(names, key=lambda n: -len(adj[n])):
            used = {self.col[m] for m in adj[n] if m in self.col}
            self.col[n] = next(i for i in range(len(PAL)) if i not in used)
        h = json.load(open(os.path.join(d, 'hist/world_1880.geojson')))
        self.h1880 = []
        for f in h['features']:
            if not f['geometry']: continue
            sub = f['properties'].get('SUBJECTO') or ''
            eu = sub in ('France', 'Spain', 'Portugal', 'Cape Colony', 'Natal', 'Griqualand West') or 'United Kingdom' in sub
            for r in rings(f['geometry']):
                mx, my = r[:, 0].mean(), r[:, 1].mean()
                if len(r) > 3 and -20 < mx < 52 and -36 < my < 37 and not (mx > 36 and my > 12.5) and not (mx > 33 and my > 29):
                    self.h1880.append((eu, sub, laea(r[:, 0], r[:, 1])))

def camera(t):
    cur = FULL
    for k, cam in CAMS.items():
        b = bt(k); a = ease_io(prog(t, b['start'], b['start'] + 1.2)) * (1 - ease_io(prog(t, b['end'] - 0.2, b['end'] + 1.0)))
        if a > 0: cur = tuple(lerp(x, y, a) for x, y in zip(cur, cam)) if k != 'split' else (lerp(cur[0], cam[0], a), lerp(cur[1], cam[1], a), math.exp(lerp(math.log(cur[2]), math.log(cam[2]), a)))
    x, y = laea(cur[0], cur[1]); return float(x), float(y), cur[2] * (1 + 0.015 * math.sin(t * 0.4))

# ---------- country colour by time ----------
def modern_col(n): return PAL[G.col.get(n, 0)]
def country_style(n, t):
    """(colour, alpha) of a modern country."""
    if t < bt('pre')['start']:  # hook: countries pop in, in modern colours
        tp = lerp(w('h1', 'Africa'), w('h1', 'countries', end=True), G.order.index(n if n != 'Somaliland' else 'Somalia') / (len(G.order) - 1))
        return (modern_col(n if n != 'Somaliland' else 'Somalia'), 0.92 * ease_out(prog(t, tp, tp + 0.25))) if t >= tp else None
    p = POWER_OF.get(n, 'BRITAIN'); colonial = PCOL[p]
    ts = w('berlin', 'claiming'); te = w('scramble', 'taken', end=True)
    # the scramble: colonies fill in, coastal ones first
    order = sorted(G.c, key=lambda m: G.lab[m][1] ** 2 + G.lab[m][0] ** 2 * 0.3)
    tf = lerp(ts, te, order.index(n) / len(order)) if n in order else te
    if p == 'INDEPENDENT': tf = w('scramble', 'Ethiopia')
    neutral = (0.32, 0.3, 0.27)
    col, a = neutral, 0.85
    if t >= tf: col = tuple(lerp(x, y, ease_out(prog(t, tf, tf + 0.4))) for x, y in zip(neutral, colonial))
    # independence: back to own colours as the year passes
    yr = year_now(t); iy = INDEP.get(n, 1960)
    if n == 'Somaliland': iy = 1960
    if isinstance(yr, (int, float)) and yr >= iy and t >= bt('indep')['start']:
        col = modern_col(n if n != 'Somaliland' else 'Somalia')
    if t >= bt('today')['start']: col = modern_col(n if n != 'Somaliland' else 'Somalia')
    return col, a

YEARS = None
def year_events():
    return [(bt('pre')['l0'], 1870), (w('berlin', '1884'), 1884), (w('scramble', 'taken'), 1900), (w('scramble', '1914'), 1914),
            (w('lines', '1890'), 1890), (bt('twist')['start'], None), (w('indep', 'After'), 1950), (w('indep', '1960'), 1960),
            (w('keep', '1964'), 1964), (w('new', 'Eritrea'), 1993), (w('new', '2011'), 2011), (bt('today')['start'], 'TODAY')]
def year_now(t):
    val, prev = None, None
    for te, v in YEARS:
        if t < te - 0.1: break
        if isinstance(v, int) and isinstance(prev, int) and v > prev: val = lerp(prev, v, ease_out(prog(t, te - 0.1, te + (2.5 if v == 1960 else 0.7))))
        else: val = v
        prev = v
    if t >= bt('indep')['start'] and t < w('indep', '1960'):  # sweep through the 1950s while "independence swept"
        val = lerp(1950, 1960, ease_io(prog(t, w('indep', 'independence'), w('indep', '1960'))))
    if bt('keep')['start'] <= t < w('new', 'Eritrea'): val = lerp(1964, 1990, ease_io(prog(t, w('keep', '1964') + 0.5, w('new', 'Eritrea'))))
    return val

# ---------- drawing ----------
def draw_base(cr, cam, t):
    cr.set_source_rgb(0.05, 0.08, 0.13); cr.paint()
    g = cairo.RadialGradient(W / 2, R.MAPY, 100, W / 2, R.MAPY, 1300); g.add_color_stop_rgba(0, 0.1, 0.2, 0.32, 1); g.add_color_stop_rgba(1, 0.03, 0.06, 0.1, 1)
    cr.set_source(g); cr.paint()
    cr.new_path(); path_xy(cr, cam, G.land); cr.set_source_rgb(0.2, 0.19, 0.18); cr.fill()
    pre = win('pre', t=t)
    if pre > 0:  # 1880: European coastal colonies vs African states
        for eu, sub, rs in G.h1880:
            cr.new_path(); path_xy(cr, cam, [rs])
            if eu: cr.set_source_rgba(0.85, 0.2, 0.25, 0.9 * pre)
            else:
                h = (sum(map(ord, sub)) * 37) % 5; cr.set_source_rgba(*[(0.62, 0.45, 0.28), (0.55, 0.5, 0.3), (0.5, 0.38, 0.3), (0.6, 0.52, 0.36), (0.45, 0.4, 0.3)][h], 0.75 * pre)
            cr.fill_preserve(); cr.set_source_rgba(0, 0, 0, 0.3 * pre); cr.set_line_width(1); cr.stroke()
    a_mod = 1 - pre
    for n in G.c:
        st = country_style(n, t)
        if not st or a_mod <= 0: continue
        col, a = st
        cr.new_path(); path_xy(cr, cam, G.c[n]); cr.set_source_rgba(*col[:3], a * a_mod); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, 0.6 * a * a_mod); cr.set_line_width(1.4); cr.stroke()
        if n == 'W. Sahara' and t >= bt('pre')['start']:
            cr.save(); cr.new_path(); path_xy(cr, cam, G.c[n]); cr.clip(); cr.set_source_rgba(0, 0, 0, 0.35 * a_mod); cr.set_line_width(5)
            x0, y0 = L(cam, -14, 25)
            for i in range(-20, 20): cr.move_to(x0 + i * 22, y0 - 300); cr.line_to(x0 + i * 22 + 300, y0 + 300)
            cr.stroke(); cr.restore()

def draw_straight(cr, cam, t, k, a=1.0, col=(1, 0.92, 0.3), width=9):
    if a <= 0 or k <= 0: return
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_source_rgba(0, 0, 0, 0.35 * a * clamp(k * 4)); cr.paint()  # dim the map so the lines pop
    for i, (p, q) in enumerate(G.straight):
        kk = clamp(k * len(G.straight) * 0.25 - i * 0.25)
        if kk <= 0: continue
        (x0, y0), (x1, y1) = L(cam, p[0], p[1]), L(cam, lerp(p[0], q[0], kk), lerp(p[1], q[1], kk))
        for lw, al in ((width * 4, 0.3), (width, 1)):
            cr.new_path(); cr.move_to(x0, y0); cr.line_to(x1, y1); cr.set_source_rgba(*col[:3], a * al); cr.set_line_width(lw); cr.stroke()

def label(cr, cam, lon, lat, txt, size, col, a, t0, t):
    if t < t0 or a <= 0: return
    k = pop_k(t, t0); x, y = L(cam, lon, lat); cr.save(); cr.translate(x, y); cr.scale(k, k)
    ptext(cr, txt, 0, 0, size, col, a, fam='Poppins ExtraBold', sw=7); cr.restore()

def blob(cr, cam, lon, lat, rx, ry, col, a, t0, t, txt):
    if t < t0 or a <= 0: return
    k = ease_out(prog(t, t0, t0 + 0.5)); x, y = L(cam, lon, lat); s = cam[2] / 0.3
    cr.save(); cr.translate(x, y); cr.scale(rx * s * k, ry * s * k); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgba(*col[:3], 0.35 * a); cr.fill_preserve(); cr.set_dash([14, 10]); cr.set_source_rgba(*col[:3], a); cr.set_line_width(5); cr.stroke(); cr.set_dash([])
    ptext(cr, txt, x, y + ry * s + 50, 42, col, a * k, fam='Poppins ExtraBold', sw=7)

def draw_story(cr, cam, t):
    # hook
    if t < bt('title')['start']:
        n = int(54 * ease_out(prog(t, w('h1', 'Africa'), w('h1', 'countries', end=True))))
        if t >= w('h1', 'fifty'): slam(cr, f'{max(n, 1)} COUNTRIES', 540, 300, 130, GOLD, t, w('h1', 'fifty'), win('h1', t=t))
        a = win('h2', 'h3', t=t)
        draw_straight(cr, cam, t, prog(t, w('h2', 'look'), w('h2', 'straight') + 0.8), a)
        if t >= w('h2', 'straight'): slam(cr, 'STRAIGHT LINES', 540, 300, 130, GOLD, t, w('h2', 'straight'), win('h2', t=t))
        if bt('h2')['start'] <= t < bt('h3')['start']:
            label(cr, cam, 10, 23, 'DESERTS', 46, WHITE, 1, w('h2', 'deserts'), t)
            label(cr, cam, 37, -2, 'PEOPLES', 46, WHITE, 1, w('h2', 'peoples'), t)
        if bt('h3')['start'] <= t:
            tr = w('h3', 'drew')
            if t >= tr:  # a ruler sweeps a line across the map
                k = ease_io(prog(t, tr, tr + 1.0)); x = lerp(150, 930, k)
                cr.new_path(); cr.move_to(150, 760); cr.line_to(x, 760); cr.set_source_rgba(*CRIMSON[:3], 1); cr.set_line_width(10); cr.stroke()
                emoji(cr, '✏️', x, 720, 110, 1); emoji(cr, '📏', 540, 820, 150 * pop_k(t, tr), 1)
            slam(cr, 'NEVER BEEN THERE', 540, 300, 110, WHITE, t, w('h3', 'never'))
            if t >= w('h3', 'never'): emoji(cr, '🚫', 540, 1250, 200 * pop_k(t, w('h3', 'never')), 1)
        return
    # 1870
    a = win('pre', t=t)
    if a > 0:
        k = ease_out(prog(t, w('pre', 'tenth'), w('pre', 'tenth') + 1.0)); x0, x1, y = 120, 960, 1360
        rrect(cr, x0, y - 30, x1 - x0, 60, 30); cr.set_source_rgba(0.62, 0.45, 0.28, a); cr.fill()
        rrect(cr, x0, y - 30, max(60, (x1 - x0) * 0.1 * k), 60, 30); cr.set_source_rgba(0.85, 0.2, 0.25, a); cr.fill()
        if k > 0: ptext(cr, 'EUROPEAN ~10%', x0, y - 52, 36, (1, 0.5, 0.55), a, anchor='l', sw=6); ptext(cr, 'AFRICAN ~90%', x1, y - 52, 36, (0.95, 0.75, 0.5), a, anchor='r', sw=6)
        tk = w('pre', 'kingdoms')
        for i, (nm, lon, lat) in enumerate(KINGDOMS): label(cr, cam, lon, lat, nm, 32, PARCH, a, tk + i * 0.12, t)
        chip(cr, '2,000+ LANGUAGES', 540, 1490, 48, GOLD, INK, pop_k(t, w('pre', 'languages')), a, em='🗣️')
        label(cr, cam, 2, 35.5, 'COASTS', 40, (1, 0.5, 0.55), a, w('pre', 'coasts'), t)
    # Berlin
    a = win('berlin', t=t)
    if a > 0:
        C.pin(cr, cam, (13.4, 52.5), 'BERLIN', t, w('berlin', 'Berlin'), GOLD, 'r', 44, a)
        tb = w('berlin', 'fourteen')
        if t >= tb: chip(cr, '14 COUNTRIES · 1884–85', 540, 1330, 48, WHITE, INK, pop_k(t, tb), a, em='🏛️')
        tn = w('berlin', 'single')
        if t >= tn:
            k = prog(t, tn, tn + 0.2); s = lerp(2.4, 1, ease_out(k))
            cr.save(); cr.translate(540, 1480); cr.rotate(-0.08); cr.scale(s, s); wd = tw(cr, 'AFRICANS INVITED: 0', 70)
            rrect(cr, -wd / 2 - 30, -62, wd + 60, 96, 14); cr.set_source_rgba(*CRIMSON[:3], a * clamp(k * 3)); cr.set_line_width(8); cr.stroke()
            ptext(cr, 'AFRICANS INVITED: 0', 0, 8, 70, CRIMSON, a * clamp(k * 3), sw=0, shadow=False); cr.restore()
    # scramble legend
    a = win('scramble', 'lines', t=t)
    if a > 0:
        rrect(cr, 25, 1290, 1030, 190, 30); cr.set_source_rgba(0.04, 0.05, 0.1, 0.85 * a); cr.fill()
        for i, (p, col) in enumerate(PCOL.items()):
            t0 = w('scramble', 'Within') + i * 0.15 if p != 'INDEPENDENT' else w('scramble', 'Ethiopia')
            if t < t0: continue
            x, y = 50 + (i % 4) * 255, 1340 + (i // 4) * 84; k = pop_k(t, t0)
            cr.save(); cr.translate(x + 22, y); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 17, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], a); cr.fill()
            ptext(cr, p if p != 'INDEPENDENT' else 'FREE', 28, 11, fit(cr, p, 30, 200, 'Poppins ExtraBold'), WHITE, a, fam='Poppins ExtraBold', anchor='l', sw=5); cr.restore()
        if bt('scramble')['start'] <= t < bt('lines')['start']:
            label(cr, cam, 39.5, 8.5, 'ETHIOPIA', 40, WHITE, a, w('scramble', 'Ethiopia'), t); label(cr, cam, -9.5, 4.0, 'LIBERIA', 38, WHITE, a, w('scramble', 'Liberia'), t)
    # lines + the quote
    a = win('lines', t=t)
    if a > 0:
        draw_straight(cr, cam, t, prog(t, w('lines', 'drawn'), w('lines', 'drawn') + 2.0), a)
        tq = w('lines', 'joked')
        if t >= tq:
            k = pop_k(t, tq); cr.save(); cr.translate(540, 520); cr.scale(k, k)
            rrect(cr, -480, -150, 960, 300, 30); cr.set_source_rgba(0.96, 0.93, 0.85, a); cr.fill()
            for i, ln in enumerate(('"We have been engaged in drawing lines', 'upon maps where no white man\'s', 'foot ever trod..."')):
                ptext(cr, ln, 0, -70 + i * 56, 42, INK, a, fam='Poppins ExtraBold', sw=0, shadow=False)
            ptext(cr, '— LORD SALISBURY, 1890', 0, 110, 32, CRIMSON, a, sw=0, shadow=False); cr.restore()
    # split peoples
    a = win('split', t=t)
    if a > 0:
        blob(cr, cam, 36.3, -2.6, 150, 110, GOLD, a, w('split', 'Maasai'), t, 'MAASAI')
        label(cr, cam, 37.8, 1.0, 'KENYA', 38, WHITE, a, w('split', 'Kenya'), t); label(cr, cam, 34.5, -5.5, 'TANZANIA', 38, WHITE, a, w('split', 'Tanzania'), t)
        blob(cr, cam, 44.5, 6.5, 240, 190, (0.5, 0.85, 1), a, w('split', 'Somali'), t, 'SOMALI PEOPLE')
        chip(cr, '5 TERRITORIES', 540, 1400, 50, (0.5, 0.85, 1), INK, pop_k(t, w('split', 'five')), a, em='⭐')
    # twist
    a = win('twist', t=t)
    if a > 0:
        slam(cr, "NOT SO SIMPLE", 540, 470, 100, WHITE, t, w('twist', 'simple'), a)
        chip(cr, '2024 STUDY: MOST BORDERS FOLLOWED', 540, 1300, 40, WHITE, INK, pop_k(t, w('twist', 'study')), a)
        chip(cr, 'OLDER FRONTIERS · RIVERS · LAKES', 540, 1400, 40, (0.4, 0.75, 1), INK, pop_k(t, w('twist', 'frontiers')), a)
        td = w('twist', 'deserts')
        draw_straight(cr, cam, t, prog(t, w('twist', 'straight'), w('twist', 'straight') + 1.0), a, (1, 0.85, 0.4))
        label(cr, cam, 12, 22, 'SAHARA', 56, (1, 0.85, 0.4), a, td, t); label(cr, cam, 20, -22, 'KALAHARI', 40, (1, 0.85, 0.4), a, td + 0.2, t)
    # independence
    a = win('indep', t=t)
    if a > 0:
        ty = w('indep', '1960')
        if t >= ty:
            k = pop_k(t, ty); cr.save(); cr.translate(540, 1380); cr.scale(k, k)
            ptext(cr, '1960: THE YEAR OF AFRICA', 0, 0, 56, GOLD, a, sw=8); ptext(cr, '17 NEW COUNTRIES', 0, 80, 70, WHITE, a, sw=9); cr.restore()
    a = win('keep', t=t)
    if a > 0: chip(cr, 'KEEP THE COLONIAL BORDERS', 540, 1360, 46, GOLD, INK, pop_k(t, w('keep', 'agreed')), a, em='🤝')
    a = win('new', t=t)
    if a > 0:
        for nm, word, lon, lat, txt in (('Eritrea', 'Eritrea', 38.8, 15.3, 'ERITREA 1993'), ('S. Sudan', 'South', 30.5, 7.3, 'SOUTH SUDAN 2011')):
            tn = w('new', word)
            if t >= tn:
                pulse = 0.5 + 0.5 * math.sin(t * 6)
                cr.new_path(); path_xy(cr, cam, G.c[nm]); cr.set_source_rgba(1, 1, 1, a * pulse); cr.set_line_width(8); cr.stroke()
                label(cr, cam, lon, lat + (2.2 if nm == 'Eritrea' else -2.6), txt, 40, GOLD, a, tn, t)
        chip(cr, "WORLD'S YOUNGEST COUNTRY", 540, 1420, 44, GOLD, INK, pop_k(t, w('new', 'youngest')), a, em='🎂')
    a = win('today', t=t)
    if a > 0:
        slam(cr, '54 COUNTRIES', 540, 470, 120, GOLD, t, w('today', 'fifty'), a)
        chip(cr, '2,000+ LANGUAGES', 540, 1320, 50, WHITE, INK, pop_k(t, w('today', 'languages')), a, em='🗣️')
        chip(cr, 'NIGERIA: 500+ LANGUAGES', 540, 1440, 50, (0.3, 0.75, 0.4), INK, pop_k(t, w('today', 'Nigeria')), a)

def draw_year(cr, t):
    if t < bt('pre')['start'] + 0.2 or t >= bt('cta')['start'] or bt('twist')['start'] <= t < bt('indep')['start']: return
    v = year_now(t)
    if v is None: return
    txt = v if isinstance(v, str) else str(int(round(v)))
    ptext(cr, txt, 540, 300, 150, GOLD, ease_out(prog(t, bt('pre')['start'] + 0.2, bt('pre')['start'] + 0.5)), sw=16)

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end'] + 0.2): return
    a = 1 - ease_io(prog(t, b['end'] - 0.25, b['end'] + 0.2))
    cr.set_source_rgba(0.02, 0.02, 0.03, 0.55 * a); cr.paint()
    k = pop_k(t, w('title', 'why') - 0.1); cr.save(); cr.translate(540, 700); cr.scale(k, k); ptext(cr, 'WHY', 0, 0, 110, WHITE, a, sw=12); cr.restore()
    slam(cr, "AFRICA'S BORDERS", 540, 870, 120, GOLD, t, w('title', 'Africa'), a)
    slam(cr, 'LOOK LIKE THIS', 540, 1020, 110, WHITE, t, w('title', 'look'), a)

def draw_cta(cr, t):
    b = bt('cta')
    if t < b['start']: return
    a = ease_out(prog(t, b['start'], b['start'] + 0.4))
    cr.set_source_rgba(0.03, 0.03, 0.05, 0.6 * a); cr.paint()
    k = pop_k(t, w('cta', 'Should')); cr.save(); cr.translate(540, 560); cr.scale(k, k)
    ptext(cr, "SHOULD AFRICA'S BORDERS", 0, 0, 70, WHITE, a, sw=10); ptext(cr, 'BE REDRAWN?', 0, 120, 120, GOLD, a, sw=13); cr.restore()
    for i, (txt, col, d) in enumerate((('YES', (0.3, 0.8, 0.4), 0.3), ('NO', (0.9, 0.3, 0.3), 0.45))):
        if t < w('cta', 'redrawn') + d: continue
        kk = pop_k(t, w('cta', 'redrawn') + d) * (1 + 0.03 * math.sin(t * 6 + i)); cr.save(); cr.translate(310 + i * 460, 900); cr.scale(kk, kk)
        rrect(cr, -190, -70, 380, 140, 70); cr.set_source_rgba(*col, 1); cr.fill(); ptext(cr, txt, 0, 26, 80, WHITE, 1, sw=8); cr.restore()
    tc = w('cta', 'comments')
    if t >= tc: k = pop_k(t, tc); cr.save(); cr.translate(540, 1100); cr.scale(k, k); ptext(cr, 'COMMENT BELOW', -50, 0, 66, WHITE, 1, sw=9); emoji(cr, '👇', 330, -20, 80, 1); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1280); cr.scale(k, k); txt = 'FOLLOW FOR MORE'; wd = tw(cr, txt, 56)
        rrect(cr, -wd / 2 - 90, -62, wd + 180, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 56, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 66, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def render_frame(cr, t):
    cam = camera(t)
    draw_base(cr, cam, t)
    C.vignette(cr, 0.7)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0, 0.7); g.add_color_stop_rgba(1, 0, 0, 0, 0); cr.set_source(g); cr.paint()
    g = cairo.LinearGradient(0, 1500, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.8); cr.set_source(g); cr.paint()
    draw_story(cr, cam, t)
    draw_year(cr, t)
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
    music = np.zeros(n); beat = 60 / 96; bar = beat * 4
    chords = [[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 55]]
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(bar * 1.3 * SR)) / SR; env = np.minimum(1, L_ / 0.6) * np.exp(-L_ * 0.5)
        put(music, ci * bar, sum(0.03 * np.sin(2 * np.pi * note(m) * L_) for m in ch) * env); put(music, ci * bar, 0.1 * np.sin(2 * np.pi * note(ch[0] - 12) * L_) * env)
    for bi in range(int(dur / (beat / 2))):  # djembe-like pattern
        t0 = bi * beat / 2
        if t0 > bt('cta')['start'] + 3: break
        if bi % 8 in (0, 3, 6) or (t0 < bt('pre')['start'] and bi % 2 == 0):
            L_ = np.arange(int(0.3 * SR)) / SR; f0 = 90 if bi % 8 == 0 else 160
            put(music, t0, 0.35 * np.sin(2 * np.pi * np.cumsum(f0 + 80 * np.exp(-L_ * 30)) / SR) * np.exp(-L_ * 14))
        if bi % 2 == 1:
            M = np.arange(int(0.04 * SR)); put(music, t0, 0.04 * rng.standard_normal(len(M)) * np.exp(-M / SR * 70))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.6):
        L_ = np.arange(int(1.8 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 80 * np.exp(-L_ * 10)) / SR) * np.exp(-L_ * 2.5))
    def pop(t0, amp=0.06):
        L_ = np.arange(int(0.05 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * 900 * L_) * np.exp(-L_ * 60))
    for i in range(54): pop(lerp(w('h1', 'Africa'), w('h1', 'countries', end=True), i / 53))
    for key, word in (('h1', 'fifty'), ('h2', 'straight'), ('h3', 'never'), ('title', 'Africa'), ('berlin', 'single'), ('scramble', '1914'),
                      ('lines', 'joked'), ('twist', 'simple'), ('indep', '1960'), ('new', 'youngest'), ('today', 'fifty')):
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
    global G, YEARS
    C.TL = C.build(C.WordVoice(cache)); G = Geo(data_dir); YEARS = year_events()

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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_afb'))
    print(f"duration {C.TL['dur']:.1f}s, straight segments {len(G.straight)}")
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
