"""'Countryballs: South America vs Africa, the Geography War' (9:16). The two continents start as one piece of land, split, and
argue through eight rounds. The countryballs do the talking (Brazil and Nigeria as captains, with cameos); the announcer only
calls the rounds. All 66 countries appear as flag balls. Usage: python3 saaf.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, ssl, subprocess, sys, wave
import edge_tts.communicate as _etc
if os.path.exists('/root/.ccr/ca-bundle.crt'): _etc._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
import warballs as B
from warballs import ball
from big import local, bounds, area, km_shape, km_path
from popu import streaks, shake
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

SA_C, AF_C = hexc('#2ECC71')[:3], hexc('#FFB020')[:3]
NARR = ('en-US-GuyNeural', '+7%')
VOICE = {'Brazil': 'pt-BR-ThalitaMultilingualNeural', 'Nigeria': 'en-NG-AbeoNeural', 'Tanzania': 'en-TZ-ElimuNeural', 'Kenya': 'en-KE-ChilembaNeural',
         'South Africa': 'en-ZA-LukeNeural', 'Argentina': 'es-AR-TomasNeural', 'Chile': 'es-CL-LorenzoNeural'}
SA = ['Brazil', 'Argentina', 'Colombia', 'Peru', 'Venezuela', 'Chile', 'Ecuador', 'Bolivia', 'Paraguay', 'Uruguay', 'Guyana', 'Suriname']
SA_CODE = dict(zip(SA, 'br ar co pe ve cl ec bo py uy gy sr'.split()))
# key, speaker (None = announcer), line
LINES = [
    ('h1', None, "South America, or Africa: which continent would win a war?"),
    ('h2', None, "Plot twist: a hundred and forty million years ago, they were one piece of land."),
    ('h2s', None, "Then they split... and they never stopped arguing."),
    ('h3b', 'Brazil', "I kept the rainforest!"), ('h3n', 'Nigeria', "I kept everything else!"),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: countries."),
    ('r1a', 'Nigeria', "Africa has fifty-four countries. Count them!"), ('r1b', 'Brazil', "We have twelve. Quality over quantity!"),
    ('c2', None, "Round two: the highest peak."),
    ('r2a', 'Tanzania', "Kilimanjaro. Five thousand eight hundred and ninety-five metres. Top that!"),
    ('r2b', 'Argentina', "Aconcagua. Six thousand nine hundred and sixty-one. Topped."),
    ('c3', None, "Round three: people."),
    ('r3a', 'Brazil', "South America has four hundred and forty million people."),
    ('r3b', 'Nigeria', "Cute. Africa has one and a half billion. I alone have more than half of your whole continent!"),
    ('c4', None, "Round four: the mightiest river."),
    ('r4a', 'Nigeria', "They call the Nile the longest river on Earth."),
    ('r4b', 'Brazil', "Longest, maybe. But the Amazon carries more water than the next seven rivers combined!"),
    ('c5', None, "Round five: deserts."),
    ('r5a', 'Chile', "The Atacama is the driest desert on Earth."), ('r5b', 'Kenya', "Dry? The Sahara alone is bigger than Brazil!"),
    ('c6', None, "Round six: football."),
    ('r6a', 'South Africa', "Morocco reached the World Cup semi-final!"),
    ('r6b', 'Brazil', "Adorable. Brazil: five World Cups. Argentina: three. Uruguay: two. Ten... to zero."),
    ('c7', None, "Round seven: size."),
    ('r7a', 'Brazil', "South America is almost eighteen million square kilometres."),
    ('r7b', 'Nigeria', "Africa is thirty million. You would fit inside me, with room left for the whole United States!"),
    ('c8', None, "Final round: the GDP war."),
    ('r8a', 'Nigeria', "All fifty-four of us together: about two point eight trillion dollars."),
    ('r8b', 'Brazil', "I make two point two trillion alone. With my neighbours? Over four trillion!"),
    ('end', None, "Four all. It's a draw."),
    ('e1', 'Nigeria', "You know... we used to fit together."), ('e2', 'Brazil', "Like a puzzle. Come here, brother!"),
    ('cta', None, "South America, or Africa? Comment your side, and follow for the next battle.")]
SPK = {k: s for k, s, _ in LINES}
# round: title, winner, (beat, word) where the point is scored
RD = {1: ('COUNTRIES', 'AF', ('r1b', 'twelve')), 2: ('HIGHEST PEAK', 'SA', ('r2b', 'Topped')), 3: ('PEOPLE', 'AF', ('r3b', 'continent')), 4: ('MIGHTIEST RIVER', 'SA', ('r4b', 'combined')),
      5: ('DESERTS', 'AF', ('r5b', 'Brazil')), 6: ('FOOTBALL', 'SA', ('r6b', 'zero')), 7: ('SIZE', 'AF', ('r7b', 'inside')), 8: ('THE GDP WAR', 'SA', ('r8b', 'four'))}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h2s')
C.SAY = {None: {}}
C.HOT = ('south', 'america', 'africa', 'split', 'arguing', 'war', 'draw', 'comment', 'battle', 'million', 'land', 'geography')
C.TAIL_OVERRIDE = {'h1': 0.25, 'h2': 0.2, 'h2s': 0.3, 'title': 0.6, 'end': 0.5, 'e2': 1.0, 'cta': 2.4, **{f'c{i}': 0.15 for i in range(1, 9)},
                   **{k: 0.3 for k, s, _ in LINES if s}, **{RD[i][2][0]: 0.9 for i in RD}, 'h3b': 0.2, 'h3n': 0.4}
bt, w = C.bt, C.w
VOICE_OF = {C.say(k, s): ((VOICE[sp], '+4%') if sp else NARR) for k, sp, s in LINES}
class MultiVoice(C.WordVoice):
    def get(self, text):
        import time
        C.VOICE, C.RATE = VOICE_OF.get(text, NARR)
        for attempt in range(6):  # the speech service throttles now and then
            try: return super().get(text)
            except Exception:
                if attempt == 5: raise
                time.sleep(2 + attempt * 2)

SIZE = {'Brazil': 1.35, 'Argentina': 1.2, 'Colombia': 1.05, 'Nigeria': 1.3, 'Egypt': 1.2, 'South Africa': 1.2, 'Dem. Rep. Congo': 1.15, 'Ethiopia': 1.15, 'Algeria': 1.15,
        'Kenya': 1.05, 'Tanzania': 1.05, 'Morocco': 1.05, 'Guyana': 0.8, 'Suriname': 0.8, 'Seychelles': 0.68, 'Mauritius': 0.7, 'Comoros': 0.7, 'São Tomé and Principe': 0.68,
        'Cabo Verde': 0.7, 'Gambia': 0.75, 'Djibouti': 0.75, 'eSwatini': 0.75, 'Lesotho': 0.75}
SHORT = {'Dem. Rep. Congo': 'DR CONGO', 'Central African Rep.': 'CENTRAL AFRICAN REP.', 'São Tomé and Principe': 'SÃO TOMÉ', 'Eq. Guinea': 'EQ. GUINEA', 'S. Sudan': 'SOUTH SUDAN'}
SAHARA = [(-17, 21), (-13, 27.5), (-9, 29.5), (-2, 32.5), (8, 33.5), (12, 32), (20, 30.5), (25, 31.3), (32, 30.8), (34.5, 28), (36.5, 22), (37, 18), (33, 15.5), (25, 14.5),
          (15, 14.5), (5, 15.5), (-5, 16), (-12, 16.5), (-16.5, 17)]
G = None; AF = []; SLOT = {}

class Geo:
    def __init__(self, d):
        global AF
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        codes = json.load(open(os.path.join(d, 'africa_codes.json'))); AF = sorted(codes, key=lambda n: -cf[n]['properties'].get('POP_EST', 0))
        def raw(n):
            rs = [r for r in rings(cf[n]['geometry']) if len(r) > 3]
            if n == 'Chile': rs = [r for r in rs if r[:, 0].mean() > -90]
            if n == 'Ecuador': rs = [r for r in rs if r[:, 0].mean() > -85]
            if n == 'France': rs = [r for r in rs if r[:, 0].mean() < -50]
            if n == 'United States of America': rs = [r for r in rs if -126 < r[:, 0].mean() < -66 and 24 < r[:, 1].mean() < 50]
            return rs
        def cont(names, lon0, lat0):
            pr = {n: local(raw(n), lon0, lat0) for n in names}; x0, x1, y0, y1 = bounds([r for v in pr.values() for r in v]); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
            return {n: [r - off for r in v] for n, v in pr.items()}, (lon0, lat0, off)
        self.c = {}; self.ref = {}
        self.c['SA'], self.ref['SA'] = cont(SA + ['France'], -60, -17); self.c['AF'], self.ref['AF'] = cont(AF, 18, 2)
        one = lambda n, c: cont([n], *c)[0][n]
        self.us = one('United States of America', (-98, 39)); self.brazil = one('Brazil', (-53, -11))
        self.sahara = self.pts('AF', np.array(SAHARA, float))
        self.j = {'SA': [r for n in SA + ['France'] for r in local(raw(n), -15, -8)], 'AF': [r for n in AF for r in local(raw(n), -15, -8)]}
        self.riv = {}
        for f in json.load(open(os.path.join(d, 'rivers_50m.geojson')))['features']:
            n = f['properties'].get('name'); key = 'nile' if n in ('Nile', 'Albert Nile', 'Victoria Nile') else ('amazon' if n in ('Amazonas', 'Ucayali') else None)
            if key and f['geometry']:
                g = f['geometry']
                for c in (g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]): self.riv.setdefault(key, []).append(self.pts('AF' if key == 'nile' else 'SA', np.array(c, float)))
        for n in SA: B.FL[n] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', SA_CODE[n] + '.png'))
        for n in AF: B.FL[n] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', codes[n] + '.png'))
        for names, cols, x0, dx, y0, dy, sgn, base in ((SA, 3, 440, 132, 800, 150, -1, 58), (AF, 6, 606, 77, 700, 82, 1, 35)):
            slots = [(x0 + sgn * ((i % cols) * dx + ((i // cols) % 2) * dx * 0.4), y0 + (i // cols) * dy) for i in range(len(names))]
            slots.sort(key=lambda p: (abs(p[0] - 540), -p[1]))
            for n, p in zip(sorted(names, key=lambda n: -SIZE.get(n, 0.9)), slots): SLOT[n] = (p[0], p[1], base * SIZE.get(n, 0.9))
        print('areas M km²: SA', round(sum(area(v) for n, v in self.c['SA'].items() if n != 'France') / 1e6, 1), 'AF', round(sum(area(v) for v in self.c['AF'].values()) / 1e6, 1),
              'Sahara', round(area([self.sahara]) / 1e6, 1), 'rivers', {k: len(v) for k, v in self.riv.items()})
    def pts(self, which, lonlat):
        lon0, lat0, off = self.ref[which]; return local([lonlat], lon0, lat0)[0] - off

# ---------- shared drawing ----------
def cam(cr, z=1.0, tilt=0.0, fx=540, fy=960):
    cr.translate(540, 960); cr.rotate(tilt); cr.scale(z, z); cr.translate(-fx, -fy)
def push(t, a, b, z0, z1): return lerp(z0, z1, ease_out(prog(t, a, b)))
def arena(cr, t, tint=None):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.03, 0.1); g.add_color_stop_rgb(1, 0.1, 0.08, 0.2); cr.set_source(g); cr.paint()
    for col, x0 in ((SA_C, 0), (AF_C, W)):
        c = tint or col; g = cairo.RadialGradient(x0, 1100, 50, x0, 1100, 900); g.add_color_stop_rgba(0, *c, 0.36); g.add_color_stop_rgba(1, *c, 0); cr.set_source(g); cr.paint()
    rng = np.random.default_rng(3)
    for _ in range(90):
        x, y, s = rng.uniform(0, W), rng.uniform(0, 700), rng.uniform(0.8, 2.4); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25 + 0.25 * math.sin(t * 2 + x)); cr.fill()
def cmap(cr, which, cx, cy, s, a=1.0, col=None, lw=1.3):
    col = col or (SA_C if which == 'SA' else AF_C)
    for i, (n, rs) in enumerate(G.c[which].items()):
        f = 0.8 + 0.2 * ((i * 7) % 5) / 4; c = (0.45, 0.5, 0.48) if n == 'France' else tuple(min(1, v * f) for v in col)
        km_shape(cr, rs, cx, cy, s, c, a, lw=lw, edge=(0.03, 0.04, 0.1))
def kline(cr, segs, cx, cy, s, k, col, lw=9):
    tot = sum(len(g) for g in segs); done = 0
    for g in segs:
        m = int(clamp((k * tot - done) / len(g)) * len(g)); done += len(g)
        if m < 2: continue
        for wd, al in ((lw * 2.6, 0.25), (lw, 1)):
            cr.new_path(); cr.move_to(cx + g[0, 0] * s, cy - g[0, 1] * s); [cr.line_to(cx + x * s, cy - y * s) for x, y in g[1:m]]
            cr.set_source_rgba(*col, al); cr.set_line_width(wd); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
def army(cr, t, names, mood='neutral', enter=1.0, drop=None, hop=8.0):
    sgn = -1 if names is SA else 1
    for i, n in sorted(enumerate(names), key=lambda p: SLOT[p[1]][1]):
        x, y, r = SLOT[n]; sq = 0.0
        if drop is not None:
            ts = drop[n]
            if t < ts: continue
            y = lerp(-150, y, ease_out(prog(t, ts, ts + 0.3))); sq = 0.18 * math.sin(math.pi * clamp((t - ts - 0.3) / 0.2)) if t > ts + 0.3 else 0.0
        ball(cr, n, x + sgn * (1 - enter) * 700, y - abs(math.sin(t * 5 + i * 1.7)) * hop, r, mood, sq, -sgn * 0.6)
def nametag(cr, name, x, y, col):
    nm = SHORT.get(name, name.upper()); wd = tw(cr, nm, 42)
    rrect(cr, x - wd / 2 - 30, y - 42, wd + 60, 80, 40); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    ptext(cr, nm, x, y + 14, 42, INK, 1, sw=0, shadow=False)
def bubble(cr, t, b, tail_x, y=520, size=56):
    toks = b['tokens']; n = sum(1 for s, e, _ in b['words'] if s <= t + 0.03); n = min(len(toks), max(1, round(n * len(toks) / max(1, len(b['words'])))))
    lines, cur = [], []
    for tk in toks:
        if cur and tw(cr, ' '.join(cur + [tk]), size, 'Poppins ExtraBold') > 860: lines.append(cur); cur = []
        cur.append(tk)
    lines.append(cur)
    bw = max(tw(cr, ' '.join(l), size, 'Poppins ExtraBold') for l in lines) + 90; bh = len(lines) * 72 + 56
    k = pop_k(t, b['l0'] - 0.1, 0.22); cr.save(); cr.translate(540, y); cr.scale(k, k); cr.translate(-540, -y)
    tx = clamp(tail_x, 540 - bw / 2 + 70, 540 + bw / 2 - 70)
    cr.new_path(); cr.move_to(tx - 30, y + bh / 2 - 6); cr.line_to(lerp(tx, tail_x, 0.4), y + bh / 2 + 62); cr.line_to(tx + 36, y + bh / 2 - 6); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(7); cr.stroke()
    rrect(cr, 540 - bw / 2, y - bh / 2, bw, bh, 42); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(7); cr.stroke()
    cr.rectangle(tx - 22, y + bh / 2 - 12, 50, 12); cr.set_source_rgb(1, 1, 1); cr.fill()
    i = 0
    for li, l in enumerate(lines):
        xx = 540 - tw(cr, ' '.join(l), size, 'Poppins ExtraBold') / 2; yy = y - bh / 2 + 80 + li * 72
        for tk in l:
            ptext(cr, tk, xx, yy, size, INK if i < n else (0.8, 0.8, 0.85), 1, fam='Poppins ExtraBold', anchor='l', sw=0, shadow=False); xx += tw(cr, tk + ' ', size, 'Poppins ExtraBold'); i += 1
    cr.restore()
def hop_of(t, b):
    h = 0.0
    for s, e, _ in b['words']:
        if s <= t < s + 0.26: h = max(h, math.sin(math.pi * (t - s) / 0.26))
    return h
def side_of(name): return 'SA' if name in SA else 'AF'

def talk(cr, t, key, prop=None, mood='happy', rival_mood='angry'):
    """A countryball speaks: bubble on top, an illustration in the middle, the speaker below, the rival captain in the corner."""
    b = bt(key); name = SPK[key]; side = side_of(name); col = SA_C if side == 'SA' else AF_C; sgn = -1 if side == 'SA' else 1
    tilt = 0.035 * (1 if sum(map(ord, key)) % 2 else -1)
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.07), tilt, 540, 980); arena(cr, t, col)
    if prop: prop(cr, t, b)
    rival = 'Nigeria' if side == 'SA' else 'Brazil'
    ball(cr, rival, 540 - sgn * 365, 1440 - abs(math.sin(t * 4)) * 6, 92, rival_mood, 0, sgn * 0.8)
    h = hop_of(t, b); sx = 540 + sgn * 130
    ball(cr, name, sx, 1350 - h * 40, 175, mood, 0.05 * h, -sgn * 0.5)
    cr.restore()
    bubble(cr, t, b, sx); nametag(cr, name, sx, 1600, col)
    f = 1 - prog(t, b['start'], b['start'] + 0.12)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.5 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.18)))

# ---------- illustrations ----------
def peak(cr, x, base, hpx, wd, col, k, name, metres):
    h = hpx * k
    if h < 4: return
    cr.new_path(); cr.move_to(x - wd / 2, base); cr.line_to(x - wd * 0.12, base - h * 0.72); cr.line_to(x, base - h); cr.line_to(x + wd * 0.16, base - h * 0.66); cr.line_to(x + wd / 2, base); cr.close_path()
    cr.set_source_rgb(*[c * 0.6 for c in col]); cr.fill_preserve(); cr.set_source_rgb(0.03, 0.04, 0.1); cr.set_line_width(6); cr.stroke()
    cr.new_path(); cr.move_to(x - wd * 0.1, base - h * 0.76); cr.line_to(x, base - h); cr.line_to(x + wd * 0.12, base - h * 0.74); cr.line_to(x + wd * 0.04, base - h * 0.8); cr.line_to(x - wd * 0.02, base - h * 0.73); cr.close_path()
    cr.set_source_rgb(0.95, 0.97, 1); cr.fill()
    ptext(cr, name, x, base - h * 0.32, 40, WHITE, 1, sw=7); ptext(cr, f'{int(metres * k):,} M', x, base - h * 0.32 + 52, 42, GOLD, 1, sw=7)
def p_kili(cr, t, b): peak(cr, 540, 1150, 5895 * 0.066, 520, AF_C, ease_io(prog(t, b['l0'], b['l0'] + 1.4)), 'KILIMANJARO', 5895)
def p_acon(cr, t, b):
    peak(cr, 760, 1150, 5895 * 0.066, 460, AF_C, 1, 'KILIMANJARO', 5895)
    k = ease_io(prog(t, b['l0'], w('r2b', 'Topped') - 0.1)); peak(cr, 330, 1150, 6961 * 0.066, 500, SA_C, k, 'ACONCAGUA', 6961)
    if k >= 1: ptext(cr, '+1,066 M', 760, 1150 - 6961 * 0.066 + 30, 44, GOLD, pop_k(t, w('r2b', 'Topped')), sw=7)
def figs(cr, x0, y0, n, cols, col, dx=30, dy=42):
    for j in range(n):
        x, y = x0 + (j % cols) * dx, y0 + (j // cols) * dy
        cr.new_path(); cr.arc(x, y - 9, 7.5, 0, 2 * math.pi); cr.rectangle(x - 8, y - 1, 16, 20); cr.set_source_rgb(*col); cr.fill()
def p_pop_sa(cr, t, b):
    k = ease_out(prog(t, b['l0'] + 0.4, b['l1'])); figs(cr, 220, 800, int(44 * k), 22, SA_C)
    ptext(cr, f'{int(440 * k)} MILLION', 540, 1020, 84, SA_C, 1, sw=10); ptext(cr, 'EACH FIGURE = 10 MILLION', 540, 1090, 28, WHITE, 0.8, fam='Poppins ExtraBold', sw=5)
def p_pop_af(cr, t, b):
    figs(cr, 120, 760, 44, 4, SA_C, 30, 36); ptext(cr, '440M', 165, 730, 40, SA_C, 1, sw=6)
    k = ease_out(prog(t, w('r3b', 'Africa'), w('r3b', 'billion') + 0.4)); figs(cr, 310, 760, int(150 * k), 25, AF_C, 28, 52)
    ptext(cr, f'{1.5 * k:.1f} BILLION', 650, 730, 56, AF_C, 1, sw=8)
    th = w('r3b', 'alone')
    if t >= th: chip(cr, 'NIGERIA ALONE: 238M', 650, 905, 44, WHITE, INK, pop_k(t, th), 1)
def p_nile(cr, t, b):
    cmap(cr, 'AF', 540, 910, 0.06); kline(cr, G.riv['nile'], 540, 910, 0.06, ease_io(prog(t, w('r4a', 'Nile') - 0.2, b['l1'])), (0.6, 0.9, 1))
    tl = w('r4a', 'longest')
    if t >= tl: ptext(cr, 'NILE', 170, 880, 64, (0.6, 0.9, 1), pop_k(t, tl), sw=9); ptext(cr, '~6,650 KM', 170, 950, 44, WHITE, pop_k(t, tl), sw=7)
def p_amazon(cr, t, b):
    cmap(cr, 'SA', 300, 910, 0.062); kline(cr, G.riv['amazon'], 300, 910, 0.062, ease_io(prog(t, w('r4b', 'Amazon') - 0.2, w('r4b', 'water'))), (0.6, 0.9, 1))
    tb = w('r4b', 'water')
    for i, (lab, v, col) in enumerate((('AMAZON', 209, SA_C), ('CONGO', 41, AF_C), ('NILE', 2.8, AF_C))):
        if t < tb: break
        k = ease_out(prog(t, tb + i * 0.15, tb + i * 0.15 + 0.8)); hh = max(6, 380 * v / 209 * k); x = 640 + i * 130
        rrect(cr, x - 46, 1110 - hh, 92, hh, 12); cr.set_source_rgb(*col); cr.fill(); ptext(cr, lab, x, 1160, 28, WHITE, 1, fam='Poppins ExtraBold', sw=5)
    if t >= tb: ptext(cr, 'WATER FLOW', 770, 700, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=5)
def p_atacama(cr, t, b):
    cmap(cr, 'SA', 540, 910, 0.062); p = G.pts('SA', np.array([[-69.3, -24.0]]))[0]; x, y = 540 + p[0] * 0.062, 910 - p[1] * 0.062; ta = w('r5a', 'Atacama')
    if t >= ta:
        k = pop_k(t, ta); cr.new_path(); cr.arc(x, y, 26 * k + 8 * math.sin(t * 6), 0, 2 * math.pi); cr.set_source_rgba(1, 0.3, 0.2, 0.9); cr.fill()
        emoji(cr, '☀️', x - 150, y - 20, 110 * k, 1); ptext(cr, 'ATACAMA', x - 150, y + 80, 40, WHITE, 1, sw=6)
def p_sahara(cr, t, b):
    s = 0.06; cmap(cr, 'AF', 540, 910, s, col=(0.55, 0.5, 0.42)); ts = w('r5b', 'Sahara')
    km_shape(cr, [G.sahara], 540, 910, s, (0.98, 0.82, 0.45), ease_out(prog(t, ts, ts + 0.5)), lw=3, edge=WHITE)
    if t >= ts: ptext(cr, 'SAHARA · 9.2M KM²', 540, 1150, 46, (1, 0.88, 0.5), pop_k(t, ts), sw=7)
    tb = w('r5b', 'bigger') - 0.3
    if t >= tb:
        k = ease_out(prog(t, tb, tb + 0.5)); c = G.pts('AF', np.array([[11.0, 22.5]]))[0]
        cr.save(); cr.translate(0, (1 - k) * -600); km_shape(cr, G.brazil, 540, 910, s, SA_C, k, c[0], c[1], fill=0.72, lw=3, edge=INK); cr.restore()
        if k >= 1: ptext(cr, 'BRAZIL 8.5M', 540 + c[0] * s, 910 - c[1] * s + 12, 32, INK, 1, sw=0, shadow=False)
def p_morocco(cr, t, b):
    ball(cr, 'Morocco', 540, 900, 150 * pop_k(t, b['l0'], 0.3), 'happy'); emoji(cr, '⚽', 760, 980, 120, 1, rot=t * 3)
    ts = w('r6a', 'semi')
    if t >= ts: chip(cr, 'WORLD CUP SEMI-FINAL · 2022', 540, 1140, 44, AF_C, INK, pop_k(t, ts), 1)
def p_cups(cr, t, b):
    tot = 0
    for i, (n, cups, word) in enumerate((('Brazil', 5, 'five'), ('Argentina', 3, 'three'), ('Uruguay', 2, 'two'))):
        ts = w('r6b', word) - 0.2; x = 220 + i * 320
        if t < ts: continue
        tot += cups; ball(cr, n, x, 900, 100 * pop_k(t, ts, 0.3), 'happy')
        for j in range(cups):
            if t >= ts + j * 0.07: emoji(cr, '🏆', x - (cups - 1) * 26 + j * 52, 760, 60 * pop_k(t, ts + j * 0.07, 0.25), 1)
    tt = w('r6b', 'Ten') - 0.1
    if t >= tt: sx, sy = shake(t, w('r6b', 'zero'), 14); cr.save(); cr.translate(sx, sy); slam(cr, '10 – 0', 540, 1090, 130, WHITE, t, tt); cr.restore()
def p_size_sa(cr, t, b):
    cmap(cr, 'SA', 540, 910, 0.062); ts = w('r7a', 'eighteen')
    if t >= ts: ptext(cr, '17.8M KM²', 540, 940, 84, WHITE, pop_k(t, ts), sw=11)
def p_size_af(cr, t, b):
    s = 0.062; cmap(cr, 'AF', 540, 910, s); tf, tr = w('r7b', 'fit') - 0.2, w('r7b', 'room') - 0.2
    ptext(cr, '30.4M KM²', 540, 700, 60, AF_C, pop_k(t, w('r7b', 'thirty')) if t >= w('r7b', 'thirty') else 0, sw=9)
    for rs, col, t0, pos, lab in (([r for n, v in G.c['SA'].items() for r in v], SA_C, tf, (21.0, -6.0), 'S. AMERICA'), (G.us, (0.75, 0.85, 1.0), tr, (9.0, 21.5), 'USA')):
        if t < t0: continue
        k = ease_out(prog(t, t0, t0 + 0.5)); c = G.pts('AF', np.array([pos]))[0]
        cr.save(); cr.translate(0, (1 - k) * -700); km_shape(cr, rs, 540, 910, s, col, k, c[0], c[1], fill=0.78, lw=2.5, edge=INK); cr.restore()
        if k >= 1: ptext(cr, lab, 540 + c[0] * s, 910 - c[1] * s + 12, 34, INK, 1, sw=0, shadow=False)
def gdp_circle(cr, x, y, g, col, k, lab):
    r = 190 * math.sqrt(g / 4.2) * k
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.9); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    ptext(cr, lab, x, y + 18, 50, INK, clamp(k), sw=0, shadow=False)
def p_gdp_af(cr, t, b):
    k = ease_out(prog(t, w('r8a', 'together') - 0.5, w('r8a', 'trillion')))
    gdp_circle(cr, 540, 910, 2.8, AF_C, 0.3 + 0.7 * k, f'${2.8 * k:.1f}T'); ptext(cr, 'ALL OF AFRICA · 54 COUNTRIES', 540, 1120, 36, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
    ptext(cr, 'CIRCLE SIZE = SIZE OF ECONOMY', 540, 720, 26, WHITE, 0.7, fam='Poppins ExtraBold', sw=5)
def p_gdp_sa(cr, t, b):
    gdp_circle(cr, 840, 930, 2.8, AF_C, 1, '$2.8T'); ptext(cr, 'AFRICA', 840, 1130, 34, AF_C, 1, fam='Poppins ExtraBold', sw=6)
    tn = w('r8b', 'neighbours') - 0.2; kn = ease_out(prog(t, tn, w('r8b', 'four') + 0.2))
    if t >= tn: gdp_circle(cr, 320, 910, 4.2, tuple(c * 0.75 for c in SA_C), 0.72 + 0.28 * kn, '')
    kb = ease_out(prog(t, w('r8b', 'two') - 0.2, w('r8b', 'alone')))
    gdp_circle(cr, 320, 910, 2.2, SA_C, 0.3 + 0.7 * kb, f'${2.2 * kb:.1f}T' if t < tn else '')
    if t >= tn:
        sx, sy = shake(t, w('r8b', 'four'), 12); ptext(cr, f'${lerp(2.2, 4.2, kn):.1f}T', 330 + sx, 930 + sy, 70, INK, 1, sw=0, shadow=False); ptext(cr, 'S. AMERICA', 330, 1135, 34, SA_C, 1, fam='Poppins ExtraBold', sw=6)
    else: ptext(cr, 'BRAZIL ALONE', 330, 1100, 34, SA_C, 1, fam='Poppins ExtraBold', sw=6)
PROP = {'r2a': p_kili, 'r2b': p_acon, 'r3a': p_pop_sa, 'r3b': p_pop_af, 'r4a': p_nile, 'r4b': p_amazon, 'r5a': p_atacama, 'r5b': p_sahara, 'r6a': p_morocco, 'r6b': p_cups,
        'r7a': p_size_sa, 'r7b': p_size_af, 'r8a': p_gdp_af, 'r8b': p_gdp_sa}

# ---------- the split (hook and ending) ----------
FIT_ANG, GAP = 33.0, (150.0, -60.0)
def joined(cr, t, k, s, cy=1000, balls=None):
    """Both continents on one map. k = 1: fitted together as they were; k = 0: where they are today."""
    P = local([np.array([[-35.2, -5.5]])], -15, -8)[0][0]; T = local([np.array([[8.6, 3.9]])], -15, -8)[0][0] - np.array(GAP)
    ang = math.radians(FIT_ANG) * k; ca, sa = math.cos(ang), math.sin(ang); R = np.array([[ca, -sa], [sa, ca]])
    fxk = lerp(-350, 2400, k); cx = 540 - fxk * s
    mv = lambda r: (r - P) @ R.T + P + (T - P) * k
    km_shape(cr, G.j['AF'], cx, cy, s, AF_C, 1, lw=1.2, edge=(0.03, 0.04, 0.1)); km_shape(cr, [mv(r) for r in G.j['SA']], cx, cy, s, SA_C, 1, lw=1.2, edge=(0.03, 0.04, 0.1))
    bz = mv(local([np.array([[-52.0, -10.0]])], -15, -8)[0])[0]; ng = local([np.array([[19.0, 8.0]])], -15, -8)[0][0]
    return (cx + bz[0] * s, cy - bz[1] * s), (cx + ng[0] * s, cy - ng[1] * s)
def ocean(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.1, 0.22); g.add_color_stop_rgb(1, 0.05, 0.2, 0.36); cr.set_source(g); cr.paint()

def draw_hook(cr, t):
    if t >= bt('h3b')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h2s')
    if t < b2['start']:
        # the question: two captains crash into each other in the very first frames
        ti = 0.3; e = ease_out(prog(t, 0, ti)); sx, sy = shake(t, ti, 30, 0.6)
        cr.save(); cam(cr, push(t, 0, b2['start'], 1.0, 1.16), 0.05 * math.sin(t * 1.3), 540 + sx, 1000 + sy); arena(cr, t)
        rec = 26 * math.sin(math.pi * clamp((t - ti) / 0.35)) if t > ti else 0
        for n, x0, x1, sg, ph in (('Brazil', 20, 318, -1, 0), ('Nigeria', 1060, 762, 1, 1.3)):
            ball(cr, n, lerp(x0, x1, e) + sg * rec, 1040 - abs(math.sin(t * 8 + ph)) * 22 * (t > ti + 0.3), 215, 'angry', 0.12 * (rec / 26), -sg * 0.8)
        if t >= ti: emoji(cr, '⚡', 540, 1010, 210 * pop_k(t, ti, 0.25), 1, rot=0.2 * math.sin(t * 14))
        cr.restore()
        g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.8); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 760); cr.set_source(g); cr.fill()
        slam(cr, 'SOUTH AMERICA', 540, 300, 118, SA_C, t, -0.3); ta = w('h1', 'Africa') - 0.15
        if t >= w('h1', 'or') - 0.1: ptext(cr, 'OR', 540, 420, 70, WHITE, pop_k(t, w('h1', 'or') - 0.1), sw=9)
        slam(cr, 'AFRICA?', 540, 610, 210, AF_C, t, ta, rot=0.03)
        tq = w('h1', 'which') - 0.1
        if t >= tq: qx, qy = shake(t, tq, 14); cr.save(); cr.translate(qx, qy); slam(cr, 'WHO WOULD WIN?', 540, 1500, 124, GOLD, t, tq); cr.restore()
        f = 1 - prog(t, ti, ti + 0.15)
        if ti <= t and f > 0: cr.set_source_rgba(1, 1, 1, 0.75 * f); cr.paint()
        return True
    ts = w('h2s', 'split') - 0.15
    k = 1 - ease_io(prog(t, ts, ts + 1.6)); sx, sy = shake(t, ts, 24, 0.7)
    cr.save(); cam(cr, push(t, b2['start'], b3['end'], 1.14, 1.0), -0.03 + 0.05 * (1 - k), 540 + sx, 960 + sy); ocean(cr, t)
    pb, pn = joined(cr, t, k, lerp(0.071, 0.1, k))
    ta = w('h2s', 'arguing') - 0.3
    if t >= ta:
        ball(cr, 'Brazil', pb[0], pb[1] - abs(math.sin(t * 9)) * 16, 105 * pop_k(t, ta, 0.3), 'angry', 0, 0.8); ball(cr, 'Nigeria', pn[0], pn[1] - abs(math.sin(t * 9 + 1)) * 16, 105 * pop_k(t, ta + 0.1, 0.3), 'angry', 0, -0.8)
        emoji(cr, '⚡', (pb[0] + pn[0]) / 2, (pb[1] + pn[1]) / 2, 150 * pop_k(t, ta + 0.2, 0.3), 1, rot=0.2 * math.sin(t * 12))
    cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 620); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 620); cr.set_source(g); cr.fill()
    if t < ts:
        ty = w('h2', 'hundred') - 0.15
        if t < ty: slam(cr, 'PLOT TWIST', 540, 320, 150, CRIMSON, t, b2['start'])
        else:
            slam(cr, '140 MILLION', 540, 260, 140, GOLD, t, ty); slam(cr, 'YEARS AGO', 540, 380, 92, WHITE, t, w('h2', 'years') - 0.2)
        if t >= w('h2', 'one') - 0.2: chip(cr, 'ONE PIECE OF LAND', 540, 1560, 60, WHITE, INK, pop_k(t, w('h2', 'one') - 0.2), 1)
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2)))
    else:
        slam(cr, 'THEN THEY SPLIT', 540, 290, 112, WHITE, t, ts)
        if t >= ta: slam(cr, '…AND NEVER STOPPED ARGUING', 540, 1560, 62, GOLD, t, ta)
        f = 1 - prog(t, ts, ts + 0.2)
        if f > 0: cr.set_source_rgba(1, 1, 1, 0.7 * f); cr.paint()
    return True

def close_up(cr, t, key):
    b = bt(key); name = SPK[key]; side = side_of(name); col = SA_C if side == 'SA' else AF_C; sgn = -1 if side == 'SA' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.12), 0.06 * sgn, 540, 1000); arena(cr, t, col)
    ball(cr, name, 540, 1120 - h * 50, 300 * pop_k(t, b['start'], 0.25), 'angry', 0.05 * h, -sgn * 0.6); cr.restore()
    bubble(cr, t, b, 540, 560, 64); nametag(cr, name, 540, 1560, col)
    f = 1 - prog(t, b['start'], b['start'] + 0.12)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.55 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.18)))

def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.6))
    army(cr, t, SA, 'angry', e, hop=10); army(cr, t, AF, 'angry', e, hop=10); cr.restore()
    cr.set_source_rgba(0, 0, 0.03, 0.5); cr.paint()
    slam(cr, 'SOUTH AMERICA', 540, 560, 112, SA_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 760); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 110, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 42, 120, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'AFRICA', 540, 1000, 200, AF_C, t, w('title', 'winner'))
    tg = w('title', 'geography')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE GEOGRAPHY WAR', 540, 1240, 92, WHITE, t, tg); cr.restore()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22)))

# ---------- scoreboard, cards, verdicts ----------
def tv_of(i): return w(*RD[i][2])
def score_at(t): return sum(t >= tv_of(i) and RD[i][1] == 'SA' for i in RD), sum(t >= tv_of(i) and RD[i][1] == 'AF' for i in RD)
def round_of(t):
    for i in RD:
        nxt = bt(f'c{i + 1}')['start'] if i < 8 else bt('end')['start']
        if bt(f'c{i}')['start'] <= t < nxt: return i
    return None
def hud(cr, t):
    a = ease_out(prog(t, bt('title')['end'] - 0.4, bt('title')['end']))
    if a <= 0: return
    sa, af = score_at(t); rrect(cr, 30, 140, 1020, 190, 44); cr.set_source_rgba(0.03, 0.04, 0.1, 0.88 * a); cr.fill()
    for side, x, col, sc, lab in (('SA', 250, SA_C, sa, 'S. AMERICA'), ('AF', 830, AF_C, af, 'AFRICA')):
        ptext(cr, lab, x, 200, 44, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); ptext(cr, f'ROUND {i}/8' if i else ('FINAL' if t >= bt('end')['start'] else 'VS'), 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((SA_C, AF_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, 'FINAL ROUND' if i == 8 else f'ROUND {i}', 0, 0, 120 if i == 8 else 150, CRIMSON if i == 8 else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = b['l0'] + 0.5
    if t >= tt: kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = SA_C if win == 'SA' else AF_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'SA' else 1380, 540, ease_out(k)); txt = ('SOUTH AMERICA' if win == 'SA' else 'AFRICA') + ' WINS'
    cr.save(); cr.translate(x, 1130); cr.rotate(-0.05 if win == 'SA' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 72)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, 72, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- round one: the roll call ----------
def rollcall(cr, t, key):
    b = bt(key); a_, b_ = bt('r1a'), bt('r1b'); tv = tv_of(1)
    da = {n: lerp(a_['l0'] + 0.2, a_['l1'] + 0.1, i / 53) for i, n in enumerate(sorted(AF, key=lambda n: -SLOT[n][1]))}
    ds = {n: lerp(b_['l0'], w('r1b', 'twelve') + 0.3, i / 11) for i, n in enumerate(sorted(SA, key=lambda n: -SLOT[n][1]))}
    ca = sum(t >= v + 0.2 for v in da.values()); cs = sum(t >= v + 0.2 for v in ds.values())
    cr.save()
    if key == 'r1a': cam(cr, push(t, b['start'], b['end'], 1.5, 1.62), 0.04, 800, 1040)
    else: cam(cr, push(t, b['start'], b['end'], 1.0, 1.06), -0.02, 540, 1010)
    arena(cr, t); army(cr, t, SA, 'angry' if t >= tv else 'neutral', drop=ds, hop=5); army(cr, t, AF, 'happy' if t >= tv else 'neutral', drop=da, hop=14 if t >= tv else 5); cr.restore()
    name = SPK[key]; x, y, r = SLOT[name]; col = AF_C if key == 'r1a' else SA_C
    bubble(cr, t, b, 760 if key == 'r1a' else 300, 500); nametag(cr, name, 540, 1590, col)
    if ca: ptext(cr, str(ca), 880 if key == 'r1b' else 890, 1500, 130, AF_C, 1, sw=14)
    if cs: ptext(cr, str(cs), 200, 1500, 130, SA_C, 1, sw=14)
    if key == 'r1a' and ca:
        nm = max(da, key=lambda n: da[n] if t >= da[n] + 0.2 else -1); ptext(cr, SHORT.get(nm, nm.upper()), 420, 1490, fit(cr, SHORT.get(nm, nm.upper()), 44, 520, 'Poppins ExtraBold'), WHITE, 1, fam='Poppins ExtraBold', sw=7)
    f = 1 - prog(t, b['start'], b['start'] + 0.12)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.5 * f); cr.paint()

# ---------- ending ----------
def draw_end(cr, t):
    b, e1, e2, c = bt('end'), bt('e1'), bt('e2'), bt('cta')
    if t < e1['start']:
        cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.08), 0.02, 540, 1000); arena(cr, t); army(cr, t, SA, 'neutral', hop=10); army(cr, t, AF, 'neutral', hop=10); cr.restore()
        cr.set_source_rgba(0, 0, 0.03, 0.5); cr.paint()
        ptext(cr, '4', 300, 900, 380, SA_C, 1, sw=26); ptext(cr, '4', 780, 900, 380, AF_C, 1, sw=26); ptext(cr, '—', 540, 850, 160, WHITE, 1, sw=14)
        td = w('end', 'draw')
        if t >= td: sx, sy = shake(t, td, 18); cr.save(); cr.translate(sx, sy); slam(cr, 'A DRAW', 540, 1250, 190, GOLD, t, td); cr.restore()
        C.draw_captions(cr, t, 1600); return
    tp = w('e2', 'puzzle') - 0.2; k = ease_io(prog(t, tp, tp + 1.6)); sx, sy = shake(t, tp + 1.6, 16, 0.4)
    cr.save(); cam(cr, push(t, e1['start'], c['end'], 1.0, 1.1), 0.02, 540 + sx, 960 + sy); ocean(cr, t)
    pb, pn = joined(cr, t, k, lerp(0.071, 0.1, k), 1080)
    key = 'e1' if t < e2['start'] else ('e2' if t < c['start'] else None)
    hb = hop_of(t, e2) if key == 'e2' else 0; hn = hop_of(t, e1) if key == 'e1' else 0
    mood = 'happy' if k > 0.6 else 'neutral'
    ball(cr, 'Brazil', pb[0], pb[1] - hb * 30, 110, mood, 0, 0.8); ball(cr, 'Nigeria', pn[0], pn[1] - hn * 30, 110, mood, 0, -0.8)
    if k >= 1:
        for i in range(6):
            ph = ((t - tp) * 0.5 + i * 0.17) % 1; emoji(cr, '❤️', (pb[0] + pn[0]) / 2 + (i - 2.5) * 50, (pb[1] + pn[1]) / 2 - 120 - 220 * ph, 60, 1 - ph)
    cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 760); cr.set_source(g); cr.fill()
    if key:
        bb = bt(key); bubble(cr, t, bb, pb[0] if key == 'e2' else pn[0], 540)
    else:
        for x, col, word, lab, rot in ((280, SA_C, 'South', ['SOUTH', 'AMERICA'], -0.04), (800, AF_C, 'Africa', ['AFRICA'], 0.04)):
            tt = w('cta', word)
            if t < tt: continue
            kk = pop_k(t, tt) * (1 + 0.03 * math.sin(t * 6 + x)); cr.save(); cr.translate(x, 640); cr.rotate(rot); cr.scale(kk, kk)
            for i, l in enumerate(lab): ptext(cr, l, 0, i * 100 - (50 if len(lab) > 1 else 0), 96 if len(lab) > 1 else 120, col, 1, sw=12)
            cr.restore()
        tc = w('cta', 'Comment')
        if t >= tc: kk = pop_k(t, tc); cr.save(); cr.translate(540, 440); cr.scale(kk, kk); ptext(cr, 'COMMENT YOUR SIDE', 0, 0, 82, WHITE, 1, sw=11); cr.restore()
        tf = w('cta', 'follow')
        if t >= tf:
            kk = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1560); cr.scale(kk, kk); txt = 'FOLLOW FOR THE NEXT BATTLE'; wd = tw(cr, txt, 46)
            rrect(cr, -wd / 2 - 50, -62, wd + 100, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill(); ptext(cr, txt, 0, 4, 46, WHITE, 1, sw=0, shadow=False); cr.restore()

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if draw_hook(cr, t): C.draw_captions(cr, t, 1700); return
    if key in ('h3b', 'h3n'): close_up(cr, t, key); return
    if key == 'title': draw_title(cr, t); return
    if key in ('end', 'e1', 'e2', 'cta'): draw_end(cr, t); hud(cr, t)
    elif key[0] == 'c': card(cr, t, int(key[1])); hud(cr, t)
    else:
        if key in ('r1a', 'r1b'): rollcall(cr, t, key)
        else: talk(cr, t, key, PROP.get(key), rival_mood='shock' if t >= tv_of(int(key[1])) and RD[int(key[1])][2][0] == key else 'angry')
        verdict(cr, t, int(key[1])); hud(cr, t)
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR; rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 112; bar = beat * 4
    chords = [[57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 55, 59]]  # Am F G Em, with a syncopated hand-drum groove
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar * 1.15 * SR)) / SR; env = np.minimum(1, Lc / 0.15) * np.exp(-Lc * 0.7)
        put(music, ci * bar, sum(0.028 * np.sin(2 * np.pi * note(m) * Lc) for m in ch) * env); put(music, ci * bar, 0.09 * np.sin(2 * np.pi * note(ch[0] - 24) * Lc) * env)
        for j, st in enumerate((0, 0.75, 1.5, 2.5, 3, 3.5)):
            m = ch[j % 3] + 12; P = np.arange(int(0.25 * SR)) / SR; put(music, ci * bar + st * beat, 0.03 * sum((1 / h) * np.sin(2 * np.pi * note(m) * h * P) for h in (1, 2, 3)) * np.exp(-P * 14))
    for bi in range(int(dur / (beat / 2))):
        t0 = bi * beat / 2
        if t0 > bt('cta')['start'] + 3: break
        if bi % 8 in (0, 3, 6):
            Ld = np.arange(int(0.3 * SR)) / SR; put(music, t0, 0.36 * np.sin(2 * np.pi * np.cumsum((85 if bi % 8 == 0 else 150) + 80 * np.exp(-Ld * 30)) / SR) * np.exp(-Ld * 13))
        if bi % 2 == 1: M = np.arange(int(0.04 * SR)); put(music, t0, 0.045 * rng.standard_normal(len(M)) * np.exp(-M / SR * 70))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.6):
        Lb = np.arange(int(1.6 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-Lb * 10)) / SR) * np.exp(-Lb * 2.8))
    def whoosh(t0, amp=0.26, d=0.4):
        nz = rng.standard_normal(int(d * SR)); env = np.linspace(0, 1, len(nz)) ** 2; put(fx, t0, amp * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def bell(t0, amp=0.1, f=1175):
        Ld = np.arange(int(1.2 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * f * Ld) + 0.5 * np.sin(2 * np.pi * f * 2.76 * Ld)) * np.exp(-Ld * 4))
    def horn(t0, amp=0.07):
        Lh = np.arange(int(0.9 * SR)) / SR; put(fx, t0, amp * sum(np.sign(np.sin(2 * np.pi * f * Lh)) for f in (146.8, 220, 293.7)) * np.minimum(1, Lh / 0.05) * np.exp(-Lh * 2.5) / 3)
    def pop(t0, amp=0.05, f=1100):
        Lp = np.arange(int(0.05 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * (f + 400 * np.exp(-Lp * 60)) * Lp) * np.exp(-Lp * 60))
    def cheer(t0, amp=0.1, d=1.3):
        z = np.convolve(rng.standard_normal(int(d * SR)), np.ones(8) / 8, 'same'); L_ = np.linspace(0, 1, len(z)); put(fx, t0, amp * z * np.sin(np.pi * L_) ** 0.6)
    def rumble(t0, d=2.0, amp=0.3):
        z = np.convolve(rng.standard_normal(int(d * SR)), np.ones(300) / 300, 'same') * 8; put(fx, t0, amp * z * np.sin(np.pi * np.linspace(0, 1, len(z))))
    boom(0.3, 0.9); boom(w('h1', 'Africa') - 0.15, 0.7); boom(w('h1', 'which') - 0.1, 0.7); boom(w('h2', 'Plot') - 0.1, 0.7)
    ts = w('h2s', 'split') - 0.15; boom(ts, 1.0); rumble(ts, 2.2); boom(w('h2s', 'arguing') - 0.3, 0.6)
    for k in ('h2', 'h3b', 'h3n', 'title'): whoosh(bt(k)['start'] - 0.35)
    for wd in ('Eight', 'winner', 'geography'): boom(w('title', wd), 0.7)
    horn(w('title', 'geography'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'SA' else 1319); cheer(tv + 0.1)
    for k, sp, _ in LINES:
        if sp: whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
    a_ = bt('r1a')
    for i in range(54): pop(lerp(a_['l0'] + 0.2, a_['l1'] + 0.1, i / 53) + 0.3, 0.04, 1400)
    for i in range(12): pop(lerp(bt('r1b')['l0'], w('r1b', 'twelve') + 0.3, i / 11) + 0.3, 0.06, 1000)
    boom(w('end', 'draw'), 1.0); horn(w('end', 'draw'), 0.1); tp = w('e2', 'puzzle') - 0.2; rumble(tp, 1.6, 0.2); boom(tp + 1.6, 0.9); bell(tp + 1.6, 0.14, 1568); cheer(tp + 1.7, 0.12, 2.0)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a / max(1e-6, np.abs(a).max()) * 0.9)
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    global G
    C.TL = C.build(MultiVoice(cache)); G = Geo(data_dir)

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        cr.identity_matrix(); cr.reset_clip(); render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    data_dir, out = sys.argv[1:3]
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_saaf'))
    print(f"duration {C.TL['dur']:.1f}s")
    for b in C.TL['beats']: print(f"  {b['key']:6s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','): cr.identity_matrix(); cr.reset_clip(); render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
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
