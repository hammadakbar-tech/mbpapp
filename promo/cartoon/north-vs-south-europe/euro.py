# Countryballs: North Europe vs South Europe, the Geography War (9:16, multi-voice, dialogue-driven).
# Usage: python3 euro.py <data_dir> <out.mp4> [--preview t1,t2,...]
import json, math, os, ssl, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import edge_tts.communicate as _etc
if os.path.exists('/root/.ccr/ca-bundle.crt'): _etc._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
import china as C
import warballs as B
from warballs import ball
from big import local, bounds, km_shape
from popu import streaks, shake
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, hexc, SR

N_C, S_C = hexc('#4DA8FF')[:3], hexc('#FF7A3D')[:3]
MID_C = (0.62, 0.64, 0.7)
NARR = ('en-US-GuyNeural', '+7%')
VOICE = {'Germany': 'de-DE-ConradNeural', 'Italy': 'it-IT-DiegoNeural', 'Spain': 'es-ES-AlvaroNeural', 'Ireland': 'en-IE-ConnorNeural', 'Cyprus': 'el-GR-NestorasNeural',
         'Greece': 'el-GR-NestorasNeural', 'Finland': 'fi-FI-HarriNeural', 'France': 'fr-FR-HenriNeural', 'Switzerland': 'de-CH-JanNeural', 'United Kingdom': 'en-GB-RyanNeural',
         'Norway': 'nb-NO-FinnNeural', 'Portugal': 'pt-PT-DuarteNeural', 'Luxembourg': 'fr-FR-HenriNeural'}
RATE = {'Cyprus': '+12%', 'Luxembourg': '+12%'}
NORTH = ['Germany', 'United Kingdom', 'Poland', 'Netherlands', 'Sweden', 'Norway', 'Finland', 'Denmark', 'Ireland', 'Belgium', 'Lithuania', 'Latvia', 'Estonia', 'Luxembourg', 'Iceland']
SOUTH = ['Italy', 'Spain', 'Greece', 'Portugal', 'Serbia', 'Bulgaria', 'Croatia', 'Bosnia and Herz.', 'Albania', 'Slovenia', 'North Macedonia', 'Montenegro', 'Cyprus', 'Malta']
MID = ['France', 'Switzerland', 'Austria', 'Czechia', 'Slovakia', 'Hungary', 'Romania', 'Moldova', 'Ukraine', 'Belarus', 'Liechtenstein', 'Kosovo', 'Andorra', 'Monaco', 'San Marino']
CODE_FIX = {'Norway': 'no', 'France': 'fr', 'Cyprus': 'cy', 'Kosovo': 'xk'}
LINES = [
    ('h1', None, "North Europe, or South Europe: who would win a war?"),
    ('h2', None, "One side has the money. The other side has the sun."),
    ('h3n', 'Germany', "We have the money!"), ('h3s', 'Italy', "We have the sun... and the pasta!"),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: sunshine."),
    ('r1a', 'Ireland', "Sunshine? We get about fourteen hundred hours a year. Plenty!"),
    ('r1b', 'Cyprus', "Plenty? My capital gets over three thousand. Bring sunscreen!"),
    ('c2', None, "Round two: money."),
    ('r2a', 'Italy', "We have style. Fashion. Ferrari!"),
    ('r2b', 'Luxembourg', "Cute. I make over a hundred and fifty thousand dollars per person. The most in the world!"),
    ('c3', None, "Round three: football."),
    ('r3a', 'Germany', "Four World Cups for me. One for England. Five for the north!"),
    ('r3b', 'Spain', "Italy has four. And I just won my second, this summer. Six!"),
    ('c4', None, "Round four: happiness."),
    ('r4a', 'Greece', "We have the sea, the islands, the sunsets..."),
    ('r4b', 'Finland', "And I am the happiest country on Earth. Nine years in a row!"),
    ('c5', None, "Round five: tourists."),
    ('r5a', 'United Kingdom', "Everybody wants to visit London!"),
    ('r5b', 'Spain', "Ninety-seven million tourists visited me last year. And the biggest group? British!"),
    ('c6', None, "Round six: coffee."),
    ('r6a', 'Italy', "Espresso. Cappuccino. Coffee is Italian!"),
    ('r6b', 'Finland', "Italians drink about six kilos a year each. Finns drink twelve!"),
    ('c7', None, "Round seven: history."),
    ('r7a', 'Norway', "We had the Vikings!"),
    ('r7b', 'Greece', "We invented democracy, the Olympics and the theatre. Rome did the rest!"),
    ('c8', None, "Final round: the GDP war."),
    ('r8a', 'Portugal', "All of the south together: over five trillion dollars!"),
    ('r8b', 'Germany', "I make five trillion alone. The whole north? Almost fifteen!"),
    ('end', None, "Four all. A draw... or is it?"),
    ('e1', 'France', "Excusez-moi. I have the sun, the money, and two World Cups. I win!"),
    ('e2', 'Germany', "Nobody asked you, France!"),
    ('e3', 'Switzerland', "I stay neutral."),
    ('cta', None, "North, or South? Comment your side... and tell us where France belongs!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SUNSHINE', 'S', ('r1b', 'thousand')), 2: ('MONEY', 'N', ('r2b', 'world')), 3: ('FOOTBALL', 'S', ('r3b', 'Six')), 4: ('HAPPINESS', 'N', ('r4b', 'row')),
      5: ('TOURISTS', 'S', ('r5b', 'British')), 6: ('COFFEE', 'N', ('r6b', 'twelve')), 7: ('HISTORY', 'S', ('r7b', 'rest')), 8: ('THE GDP WAR', 'N', ('r8b', 'fifteen'))}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2')
C.SAY = {None: {}}
C.HOT = ('north', 'south', 'europe', 'war', 'money', 'sun', 'draw', 'comment', 'france', 'geography', 'winner')
C.TAIL_OVERRIDE = {'h1': 0.25, 'h2': 1.1, 'title': 0.6, 'end': 0.4, 'e3': 0.7, 'cta': 2.4, **{f'c{i}': 0.15 for i in range(1, 9)},
                   **{k: 0.3 for k, s, _ in LINES if s}, **{RD[i][2][0]: 0.9 for i in RD}, 'h3n': 0.2, 'h3s': 0.4}
bt, w = C.bt, C.w
VOICE_OF = {C.say(k, s): ((VOICE[sp], RATE.get(sp, '+4%')) if sp else NARR) for k, sp, s in LINES}
class MultiVoice(C.WordVoice):
    def get(self, text):
        import time
        C.VOICE, C.RATE = VOICE_OF.get(text, NARR)
        for attempt in range(6):  # the speech service throttles now and then
            try: return super().get(text)
            except Exception:
                if attempt == 5: raise
                time.sleep(2 + attempt * 2)

SIZE = {'Germany': 1.3, 'United Kingdom': 1.2, 'Poland': 1.1, 'Italy': 1.3, 'Spain': 1.2, 'Greece': 1.05, 'Malta': 0.75, 'Luxembourg': 0.75, 'Montenegro': 0.8, 'Iceland': 0.9, 'Cyprus': 0.8}
SHORT = {'Bosnia and Herz.': 'BOSNIA', 'North Macedonia': 'N. MACEDONIA', 'United Kingdom': 'UK'}
G = None; SLOT = {}
LON0, LAT0 = 12.0, 52.0

class Geo:
    def __init__(self, d):
        feats = json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']
        cf = {f['properties']['NAME']: f for f in feats}
        def keep(r): return -26 < r[:, 0].mean() < 45 and 33.5 < r[:, 1].mean() < 72
        self.raw = {}
        for n in NORTH + SOUTH + MID:
            if n in cf: self.raw[n] = [r for r in rings(cf[n]['geometry']) if len(r) > 3 and keep(r)]
        bg = []
        for f in feats:
            n = f['properties']['NAME']
            if n in self.raw or not f['geometry']: continue
            rs = [r for r in rings(f['geometry']) if len(r) > 3 and (r[:, 0].min() < 50 and r[:, 0].max() > -30 and r[:, 1].max() > 28 and r[:, 1].min() < 75)]
            bg += rs
        pr = {n: local(v, LON0, LAT0) for n, v in self.raw.items()}
        x0, x1, y0, y1 = bounds([r for v in pr.values() for r in v]); self.off = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        print('europe extent km', round(x1 - x0), round(y1 - y0))
        self.c = {n: [r - self.off for r in v] for n, v in pr.items()}
        self.bg = [r - self.off for r in local(bg, LON0, LAT0)]
        for n in NORTH + SOUTH + MID + ['Costa Rica']:
            code = CODE_FIX.get(n) or cf[n]['properties']['ISO_A2'].lower(); p = os.path.join(d, 'flags', code + '.png')
            if os.path.exists(p): B.FL[n] = cairo.ImageSurface.create_from_png(p)
        B.FL['England'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'gb-eng.png'))
        for names, x0_, sgn in ((NORTH, 430, -1), (SOUTH, 650, 1)):
            cols, dx, dy, y0_ = 3, 128, 136, 760
            slots = [(x0_ + sgn * ((i % cols) * dx + ((i // cols) % 2) * dx * 0.42), y0_ + (i // cols) * dy) for i in range(len(names))]
            slots.sort(key=lambda p: (abs(p[0] - 540), -p[1]))
            for n, p in zip(sorted(names, key=lambda n: -SIZE.get(n, 0.9)), slots): SLOT[n] = (p[0], p[1], 56 * SIZE.get(n, 0.9))
    def pt(self, lon, lat): return local([np.array([[lon, lat]], float)], LON0, LAT0)[0][0] - self.off

# ---------- shared drawing ----------
def cam(cr, z=1.0, tilt=0.0, fx=540, fy=960):
    cr.translate(540, 960); cr.rotate(tilt); cr.scale(z, z); cr.translate(-fx, -fy)
def push(t, a, b, z0, z1): return lerp(z0, z1, ease_out(prog(t, a, b)))
def arena(cr, t, tint=None):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.03, 0.1); g.add_color_stop_rgb(1, 0.1, 0.08, 0.2); cr.set_source(g); cr.paint()
    for col, x0 in ((N_C, 0), (S_C, W)):
        c = tint or col; g = cairo.RadialGradient(x0, 1100, 50, x0, 1100, 900); g.add_color_stop_rgba(0, *c, 0.36); g.add_color_stop_rgba(1, *c, 0); cr.set_source(g); cr.paint()
    rng = np.random.default_rng(3)
    for _ in range(90):
        x, y, s = rng.uniform(0, W), rng.uniform(0, 700), rng.uniform(0.8, 2.4); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25 + 0.25 * math.sin(t * 2 + x)); cr.fill()
def ocean(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.1, 0.22); g.add_color_stop_rgb(1, 0.05, 0.2, 0.36); cr.set_source(g); cr.paint()
def shade(col, i): f = 0.8 + 0.2 * ((i * 7) % 5) / 4; return tuple(min(1, v * f) for v in col)
def emap(cr, cx, cy, s, kn=1.0, ks=1.0, split=0.0, france=0.0, lw=1.2):
    """Europe. kn / ks fade the north and south from grey to their colours; split pushes them apart (km); france lights France up."""
    km_shape(cr, G.bg, cx, cy, s, (0.13, 0.17, 0.24), 1, lw=0.8, edge=(0.03, 0.05, 0.1))
    for i, n in enumerate(MID):
        if n not in G.c: continue
        col = tuple(lerp(a, b, france) for a, b in zip(shade(MID_C, i), GOLD[:3])) if n == 'France' else shade(MID_C, i)
        km_shape(cr, G.c[n], cx, cy, s, col, 1, lw=lw, edge=(0.03, 0.04, 0.1))
    for names, col, k, dy in ((NORTH, N_C, kn, split), (SOUTH, S_C, ks, -split)):
        for i, n in enumerate(names):
            c = tuple(lerp(a, b, k) for a, b in zip(shade(MID_C, i), shade(col, i)))
            km_shape(cr, G.c[n], cx, cy, s, c, 1, 0, dy, lw=lw, edge=(0.03, 0.04, 0.1))
def scr(lon, lat, cx, cy, s, dy=0.0):
    p = G.pt(lon, lat); return cx + p[0] * s, cy - (p[1] + dy) * s

def nametag(cr, name, x, y, col):
    nm = SHORT.get(name, name.upper()); wd = tw(cr, nm, 42)
    rrect(cr, x - wd / 2 - 30, y - 42, wd + 60, 80, 40); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    ptext(cr, nm, x, y + 14, 42, INK, 1, sw=0, shadow=False)
def bubble(cr, t, b, tail_x, y=520, size=56):
    if len(' '.join(b['tokens'])) > 70: size = min(size, 50)
    toks = b['tokens']; n = sum(1 for s, e, _ in b['words'] if s <= t + 0.03); n = min(len(toks), max(1, round(n * len(toks) / max(1, len(b['words'])))))
    lines, cur = [], []
    for tk in toks:
        if cur and tw(cr, ' '.join(cur + [tk]), size, 'Poppins ExtraBold') > 860: lines.append(cur); cur = []
        cur.append(tk)
    lines.append(cur)
    lh = size * 1.29; bw = max(tw(cr, ' '.join(l), size, 'Poppins ExtraBold') for l in lines) + 90; bh = len(lines) * lh + 56
    k = pop_k(t, b['l0'] - 0.1, 0.22); cr.save(); cr.translate(540, y); cr.scale(k, k); cr.translate(-540, -y)
    tx = clamp(tail_x, 540 - bw / 2 + 70, 540 + bw / 2 - 70)
    cr.new_path(); cr.move_to(tx - 30, y + bh / 2 - 6); cr.line_to(lerp(tx, tail_x, 0.4), y + bh / 2 + 62); cr.line_to(tx + 36, y + bh / 2 - 6); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(7); cr.stroke()
    rrect(cr, 540 - bw / 2, y - bh / 2, bw, bh, 42); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(7); cr.stroke()
    cr.rectangle(tx - 22, y + bh / 2 - 12, 50, 12); cr.set_source_rgb(1, 1, 1); cr.fill()
    i = 0
    for li, l in enumerate(lines):
        xx = 540 - tw(cr, ' '.join(l), size, 'Poppins ExtraBold') / 2; yy = y - bh / 2 + 28 + size * 0.93 + li * lh
        for tk in l:
            ptext(cr, tk, xx, yy, size, INK if i < n else (0.8, 0.8, 0.85), 1, fam='Poppins ExtraBold', anchor='l', sw=0, shadow=False); xx += tw(cr, tk + ' ', size, 'Poppins ExtraBold'); i += 1
    cr.restore()
def hop_of(t, b):
    h = 0.0
    for s, e, _ in b['words']:
        if s <= t < s + 0.26: h = max(h, math.sin(math.pi * (t - s) / 0.26))
    return h
def side_of(name): return 'N' if name in NORTH else ('S' if name in SOUTH else 'M')
def col_of(name): return {'N': N_C, 'S': S_C}.get(side_of(name), GOLD[:3])

def talk(cr, t, key, prop=None, mood='happy', rival_mood='angry'):
    """A countryball speaks: bubble on top, an illustration in the middle, the speaker below, the rival captain in the corner."""
    b = bt(key); name = SPK[key]; side = side_of(name); col = col_of(name); sgn = -1 if side == 'N' else 1
    tilt = 0.035 * (1 if sum(map(ord, key)) % 2 else -1)
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.07), tilt, 540, 980); arena(cr, t, col)
    if prop: prop(cr, t, b)
    rival = 'Italy' if side == 'N' else 'Germany'
    ball(cr, rival, 540 - sgn * 365, 1440 - abs(math.sin(t * 4)) * 6, 92, rival_mood, 0, sgn * 0.8)
    h = hop_of(t, b); sx = 540 + sgn * 130
    ball(cr, name, sx, 1350 - h * 40, 175, mood, 0.05 * h, -sgn * 0.5)
    cr.restore()
    bubble(cr, t, b, sx); nametag(cr, name, sx, 1600, col)
    f = 1 - prog(t, b['start'], b['start'] + 0.12)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.5 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.18)))

# ---------- illustrations ----------
def at(key, word): return w(key, word)
def bar(cr, x, base, val, vmax, hmax, k, col, name, lab, wd=190):
    hh = max(8, hmax * val / vmax * k); rrect(cr, x - wd / 2, base - hh, wd, hh, 18); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    ptext(cr, lab, x, base - hh - 22, 50, WHITE, clamp(k * 2), sw=8); ptext(cr, name, x, base - 26, 34, INK, 1, fam='Poppins ExtraBold', sw=0, shadow=False)
    return base - hh
def emopops(cr, t, key, items, y=930, size=170):
    for i, (em, word) in enumerate(items):
        tt = at(key, word) - 0.1
        if t < tt: continue
        x = 540 + (i - (len(items) - 1) / 2) * 290; emoji(cr, em, x, y - abs(math.sin(t * 4 + i)) * 14, size * pop_k(t, tt, 0.3), 1, rot=0.12 * math.sin(t * 3 + i))
def sun_title(cr): ptext(cr, 'SUNSHINE HOURS PER YEAR', 540, 770, 34, WHITE, 0.85, fam='Poppins ExtraBold', sw=6)
def p_rain(cr, t, b):
    sun_title(cr); k = ease_out(prog(t, at('r1a', 'fourteen') - 0.2, at('r1a', 'hours')))
    top = bar(cr, 330, 1130, 1424, 3400, 280, k, N_C, 'DUBLIN', f'{int(1400 * k):,}')
    emoji(cr, '🌧️', 330, top - 120 + 6 * math.sin(t * 5), 110, 1)
def p_sun(cr, t, b):
    sun_title(cr); top = bar(cr, 330, 1130, 1424, 3400, 280, 1, N_C, 'DUBLIN', '1,400'); emoji(cr, '🌧️', 330, top - 120, 110, 1)
    k = ease_out(prog(t, at('r1b', 'three') - 0.2, at('r1b', 'thousand') + 0.3)); top = bar(cr, 750, 1130, 3340, 3400, 280, k, S_C, 'NICOSIA', f'{int(3300 * k):,}+' if k >= 1 else f'{int(3300 * k):,}')
    if t >= at('r1b', 'three'): emoji(cr, '☀️', 930, 860, 120 * pop_k(t, at('r1b', 'three')), 1, rot=t * 0.8)
def p_style(cr, t, b): emopops(cr, t, 'r2a', (('😎', 'style'), ('👗', 'Fashion'), ('🏎️', 'Ferrari')))
def p_rich(cr, t, b):
    ptext(cr, 'GDP PER PERSON · IMF 2026', 540, 770, 34, WHITE, 0.85, fam='Poppins ExtraBold', sw=6)
    bar(cr, 330, 1130, 46.5, 160, 280, 1, S_C, 'ITALY', '$47K')
    k = ease_out(prog(t, at('r2b', 'hundred') - 0.2, at('r2b', 'dollars'))); bar(cr, 750, 1130, 158.7, 160, 280, k, N_C, 'LUXEMB.', f'${int(159 * k)}K')
    tm = at('r2b', 'most')
    if t >= tm: chip(cr, '#1 IN THE WORLD', 330, 880, 40, GOLD, INK, pop_k(t, tm), 1)
def cups(cr, t, name, x, y, n, t0, glow_last=False):
    if t < t0: return
    ball(cr, name, x, y, 95 * pop_k(t, t0, 0.3), 'happy')
    for j in range(n):
        tj = t0 + j * 0.08
        if t >= tj: emoji(cr, '🏆', x - (n - 1) * 27 + j * 54, y - 145, 62 * pop_k(t, tj, 0.25), 1)
    if glow_last and t >= t0 + 0.5: ptext(cr, '2026', x - (n - 1) * 27 + (n - 1) * 54, y - 205, 30, GOLD, pop_k(t, t0 + 0.5), fam='Poppins ExtraBold', sw=5)
def p_cups_n(cr, t, b):
    cups(cr, t, 'Germany', 330, 930, 4, at('r3a', 'Four') - 0.2); cups(cr, t, 'England', 750, 930, 1, at('r3a', 'One') - 0.2)
    tf = at('r3a', 'Five') - 0.1
    if t >= tf: slam(cr, '= 5', 540, 1120, 110, N_C, t, tf)
def p_cups_s(cr, t, b):
    cups(cr, t, 'Italy', 330, 930, 4, at('r3b', 'four') - 0.2); cups(cr, t, 'Spain', 750, 930, 2, at('r3b', 'second') - 0.2, True)
    ts = at('r3b', 'summer') - 0.1
    if t >= ts: chip(cr, 'SPAIN · 2026 CHAMPIONS', 750, 1060, 32, S_C, INK, pop_k(t, ts), 1)
    tx = at('r3b', 'Six') - 0.1
    if t >= tx: sx, sy = shake(t, tx, 14); cr.save(); cr.translate(sx, sy); slam(cr, '6 – 5', 330, 1110, 110, WHITE, t, tx); cr.restore()
def p_sea(cr, t, b): emopops(cr, t, 'r4a', (('🌊', 'sea'), ('🏝️', 'islands'), ('🌅', 'sunsets')))
HAPPY = [('Finland', 7.764), ('Iceland', 7.540), ('Denmark', 7.539), ('Costa Rica', 7.439), ('Sweden', 7.255), ('Norway', 7.242), ('Netherlands', 7.223)]
def p_happy(cr, t, b):
    ptext(cr, 'WORLD HAPPINESS REPORT 2026', 540, 760, 34, WHITE, 0.85, fam='Poppins ExtraBold', sw=6); t0 = at('r4b', 'happiest') - 0.3
    for i, (n, sc) in enumerate(HAPPY):
        ti = t0 + i * 0.12
        if t < ti: continue
        y = 820 + i * 50; k = ease_out(prog(t, ti, ti + 0.3)); x = lerp(1300, 0, k); col = N_C if n in NORTH else MID_C
        cr.save(); cr.translate(x, 0)
        if i == 0: rrect(cr, 260, y - 25, 560, 50, 25); cr.set_source_rgba(*GOLD[:3], 0.9); cr.fill()
        ptext(cr, f'{i + 1}', 300, y + 14, 36, INK if i == 0 else WHITE, 1, sw=0 if i == 0 else 5, shadow=False)
        ball(cr, n, 360, y, 20, 'happy'); ptext(cr, n.upper(), 400, y + 13, 34, INK if i == 0 else col, 1, fam='Poppins ExtraBold', anchor='l', sw=0 if i == 0 else 5, shadow=False)
        ptext(cr, f'{sc:.2f}', 790, y + 13, 30, INK if i == 0 else WHITE, 0.9, fam='Poppins ExtraBold', anchor='r', sw=0 if i == 0 else 5, shadow=False); cr.restore()
    tn = at('r4b', 'Nine') - 0.1
    if t >= tn: chip(cr, '9 YEARS IN A ROW', 820, 1180, 36, GOLD, INK, pop_k(t, tn), 1, rot=0.05)
def p_london(cr, t, b): emopops(cr, t, 'r5a', (('🎡', 'Everybody'), ('💂', 'visit'), ('☔', 'London')))
def p_tourists(cr, t, b):
    k = ease_out(prog(t, at('r5b', 'Ninety') - 0.1, at('r5b', 'tourists') + 0.2))
    for i in range(7):
        ph = ((t - b['start']) * 0.45 + i * 0.143) % 1; emoji(cr, '✈️', lerp(-100, 1180, ph), 790 + (i * 53) % 260, 70, clamp(k * 3))
    ptext(cr, f'{int(97 * k)} MILLION', 540, 960, 104, S_C, 1, sw=13); ptext(cr, 'VISITORS TO SPAIN · 2025', 540, 1030, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
    tb = at('r5b', 'biggest') - 0.1
    if t >= tb: kk = pop_k(t, tb); ball(cr, 'United Kingdom', 330, 1120, 50 * kk, 'shock'); chip(cr, '#1 GROUP: BRITISH', 610, 1135, 36, WHITE, INK, kk, 1)
def p_espresso(cr, t, b): emopops(cr, t, 'r6a', (('☕', 'Espresso'), ('🥛', 'Cappuccino'), ('🤌', 'Italian')))
def p_coffee(cr, t, b):
    ptext(cr, 'COFFEE PER PERSON PER YEAR · EACH CUP = 1 KG', 540, 760, 28, WHITE, 0.85, fam='Poppins ExtraBold', sw=5)
    for row, (lab, n, word, col, y) in enumerate((('ITALY ~6 KG', 6, 'six', S_C, 870), ('FINLAND ~12 KG', 12, 'twelve', N_C, 1050))):
        t0 = at('r6b', word) - 0.3
        if t < t0: continue
        ptext(cr, lab, 160, y - 62, 38, col, 1, anchor='l', sw=6)
        for j in range(n):
            tj = t0 + j * 0.06
            if t >= tj: emoji(cr, '☕', 180 + j * 66, y, 60 * pop_k(t, tj, 0.2), 1)
def p_vikings(cr, t, b):
    k = prog(t, b['start'], b['end']); emoji(cr, '⛵', lerp(150, 930, k), 920 + 12 * math.sin(t * 3), 170, 1, rot=0.08 * math.sin(t * 3))
    tv = at('r7a', 'Vikings') - 0.1
    if t >= tv: emoji(cr, '⚔️', 540, 790, 110 * pop_k(t, tv), 1); ptext(cr, 'THE VIKING AGE · 793–1066', 540, 1110, 36, WHITE, pop_k(t, tv), fam='Poppins ExtraBold', sw=6)
def p_greece(cr, t, b):
    for i, (em, word, lab) in enumerate((('🗳️', 'democracy', 'DEMOCRACY'), ('🏅', 'Olympics', 'OLYMPICS'), ('🎭', 'theatre', 'THEATRE'))):
        tt = at('r7b', word) - 0.1
        if t < tt: continue
        x = 250 + i * 290; k = pop_k(t, tt, 0.3); emoji(cr, em, x, 880, 150 * k, 1); ptext(cr, lab, x, 1000, 36, WHITE, k, fam='Poppins ExtraBold', sw=6)
    tr = at('r7b', 'Rome') - 0.1
    if t >= tr: emoji(cr, '🏛️', 470, 1100, 80 * pop_k(t, tr), 1); ptext(cr, '+ ROME', 610, 1120, 44, S_C, pop_k(t, tr), sw=7)
def gdp_circle(cr, x, y, g, col, k, lab, a=0.92):
    r = 125 * math.sqrt(g / 5.3) * k
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    if lab: ptext(cr, lab, x, y + 18, 54, INK, clamp(k), sw=0, shadow=False)
def p_gdp_s(cr, t, b):
    ptext(cr, 'CIRCLE SIZE = SIZE OF ECONOMY', 540, 760, 28, WHITE, 0.8, fam='Poppins ExtraBold', sw=5)
    k = ease_out(prog(t, at('r8a', 'together') - 0.5, at('r8a', 'trillion'))); gdp_circle(cr, 540, 940, 5.3, S_C, 0.3 + 0.7 * k, f'${5.3 * k:.1f}T')
    ptext(cr, 'ALL 14 COUNTRIES OF THE SOUTH', 540, 1125, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
def p_gdp_n(cr, t, b):
    gdp_circle(cr, 850, 950, 5.3, S_C, 1, '$5.3T'); ptext(cr, 'SOUTH', 850, 1110, 34, S_C, 1, fam='Poppins ExtraBold', sw=6)
    tn = at('r8b', 'north') - 0.2; kn = ease_out(prog(t, tn, at('r8b', 'fifteen') + 0.2))
    if t >= tn: gdp_circle(cr, 330, 930, 14.7, tuple(c * 0.7 for c in N_C), 0.55 + 0.45 * kn, '', 0.85)
    kb = ease_out(prog(t, at('r8b', 'five') - 0.2, at('r8b', 'alone')))
    gdp_circle(cr, 330, 930, 5.0, N_C, 0.3 + 0.7 * kb, f'${5.0 * kb:.1f}T' if t < tn else '')
    if t >= tn:
        sx, sy = shake(t, at('r8b', 'fifteen'), 12); ptext(cr, f'${lerp(5.0, 14.7, kn):.1f}T', 330 + sx, 950 + sy, 76, INK, 1, sw=0, shadow=False); ptext(cr, 'THE NORTH', 330, 1170, 34, N_C, 1, fam='Poppins ExtraBold', sw=6)
    else: ptext(cr, 'GERMANY ALONE', 330, 1110, 34, N_C, 1, fam='Poppins ExtraBold', sw=6)
PROP = {'r1a': p_rain, 'r1b': p_sun, 'r2a': p_style, 'r2b': p_rich, 'r3a': p_cups_n, 'r3b': p_cups_s, 'r4a': p_sea, 'r4b': p_happy, 'r5a': p_london, 'r5b': p_tourists,
        'r6a': p_espresso, 'r6b': p_coffee, 'r7a': p_vikings, 'r7b': p_greece, 'r8a': p_gdp_s, 'r8b': p_gdp_n}

# ---------- hook ----------
MS = 0.205  # map scale, px per km
def draw_hook(cr, t):
    if t >= bt('h3n')['start']: return False
    b1, b2 = bt('h1'), bt('h2')
    if t < b2['start']:
        ti = 0.3; e = ease_out(prog(t, 0, ti)); sx, sy = shake(t, ti, 30, 0.6)
        cr.save(); cam(cr, push(t, 0, b2['start'], 1.0, 1.16), 0.05 * math.sin(t * 1.3), 540 + sx, 1000 + sy); arena(cr, t)
        rec = 26 * math.sin(math.pi * clamp((t - ti) / 0.35)) if t > ti else 0
        for n, x0, x1, sg, ph in (('Germany', 20, 318, -1, 0), ('Italy', 1060, 762, 1, 1.3)):
            ball(cr, n, lerp(x0, x1, e) + sg * rec, 1040 - abs(math.sin(t * 8 + ph)) * 22 * (t > ti + 0.3), 215, 'angry', 0.12 * (rec / 26), -sg * 0.8)
        if t >= ti: emoji(cr, '⚡', 540, 1010, 210 * pop_k(t, ti, 0.25), 1, rot=0.2 * math.sin(t * 14))
        cr.restore()
        g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.8); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 760); cr.set_source(g); cr.fill()
        slam(cr, 'NORTH EUROPE', 540, 300, 124, N_C, t, -0.3)
        if t >= w('h1', 'or') - 0.1: ptext(cr, 'OR', 540, 420, 70, WHITE, pop_k(t, w('h1', 'or') - 0.1), sw=9)
        slam(cr, 'SOUTH EUROPE?', 540, 590, 124, S_C, t, w('h1', 'South') - 0.15, rot=0.03)
        tq = w('h1', 'who') - 0.1
        if t >= tq: qx, qy = shake(t, tq, 14); cr.save(); cr.translate(qx, qy); slam(cr, 'WHO WOULD WIN?', 540, 1500, 124, GOLD, t, tq); cr.restore()
        f = 1 - prog(t, ti, ti + 0.15)
        if ti <= t and f > 0: cr.set_source_rgba(1, 1, 1, 0.75 * f); cr.paint()
        return True
    tm, tsn = w('h2', 'money') - 0.1, w('h2', 'sun') - 0.1; tsp = tsn + 0.75
    kn = ease_out(prog(t, tm, tm + 0.4)); ks = ease_out(prog(t, tsn, tsn + 0.4)); sp = ease_io(prog(t, tsp, tsp + 0.6)) * 330
    sx, sy = shake(t, tsp, 22, 0.6)
    cr.save(); cam(cr, push(t, b2['start'], b2['end'], 1.18, 1.0), 0.03 - 0.05 * prog(t, b2['start'], b2['end']), 540 + sx, 1010 + sy); ocean(cr, t)
    emap(cr, 540, 1010, MS, kn, ks, sp)
    if t >= tsp:  # the crack along the line
        f = 1 - prog(t, tsp, tsp + 0.5); cr.set_source_rgba(1, 1, 1, 0.8 * f); cr.rectangle(0, 1010 - G.pt(0, 47.3)[1] * MS - 6, W, 12); cr.fill()
    for word, em, side, t0 in (('money', '💰', 1, tm), ('sun', '☀️', -1, tsn)):
        if t < t0: continue
        for j in range(5):
            lon, lat = ((-6, 54), (9, 56), (17, 60), (21, 52), (26, 64))[j] if side > 0 else ((-4, 39), (13, 42), (22, 39), (19, 44), (33, 35))[j]
            x, y = scr(lon, lat, 540, 1010, MS, sp * side); emoji(cr, em, x, y - abs(math.sin(t * 6 + j)) * 18, 76 * pop_k(t, t0 + j * 0.06, 0.25), 1)
    cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 560); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 560); cr.set_source(g); cr.fill()
    if t >= tm: slam(cr, 'ONE SIDE: MONEY', 540, 250, 100, N_C, t, tm)
    if t >= tsn: slam(cr, 'THE OTHER: SUN', 540, 380, 100, S_C, t, tsn, rot=0.03)
    if t >= tsp: slam(cr, 'NORTH', 300, 520, 90, WHITE, t, tsp); slam(cr, 'SOUTH', 800, 1560, 90, WHITE, t, tsp + 0.1)
    streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.22)))
    return True

def close_up(cr, t, key):
    b = bt(key); name = SPK[key]; col = col_of(name); sgn = -1 if side_of(name) == 'N' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.12), 0.06 * sgn, 540, 1000); arena(cr, t, col)
    ball(cr, name, 540, 1120 - h * 50, 300 * pop_k(t, b['start'], 0.25), 'angry', 0.05 * h, -sgn * 0.6)
    em = '💰' if side_of(name) == 'N' else '☀️'
    for j in range(6):
        ph = ((t - b['start']) * 0.6 + j / 6) % 1; emoji(cr, em, 140 + j * 160, lerp(1700, 700, ph), 80, math.sin(math.pi * ph))
    cr.restore()
    bubble(cr, t, b, 540, 560, 64); nametag(cr, name, 540, 1560, col)
    f = 1 - prog(t, b['start'], b['start'] + 0.12)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.55 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.18)))

def army(cr, t, names, mood='neutral', enter=1.0, hop=8.0):
    sgn = -1 if names is NORTH else 1
    for i, n in sorted(enumerate(names), key=lambda p: SLOT[p[1]][1]):
        x, y, r = SLOT[n]; ball(cr, n, x + sgn * (1 - enter) * 700, y - abs(math.sin(t * 5 + i * 1.7)) * hop, r, mood, 0, -sgn * 0.6)
def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.6))
    army(cr, t, NORTH, 'angry', e, hop=10); army(cr, t, SOUTH, 'angry', e, hop=10); cr.restore()
    cr.set_source_rgba(0, 0, 0.03, 0.5); cr.paint()
    slam(cr, 'NORTH', 540, 560, 170, N_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'SOUTH', 540, 980, 170, S_C, t, w('title', 'winner'))
    tg = w('title', 'geography')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE EUROPE WAR', 540, 1210, 100, WHITE, t, tg); cr.restore()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22)))

# ---------- scoreboard, cards, verdicts ----------
def tv_of(i): return w(*RD[i][2])
def score_at(t): return sum(t >= tv_of(i) and RD[i][1] == 'N' for i in RD), sum(t >= tv_of(i) and RD[i][1] == 'S' for i in RD)
def round_of(t):
    for i in RD:
        nxt = bt(f'c{i + 1}')['start'] if i < 8 else bt('end')['start']
        if bt(f'c{i}')['start'] <= t < nxt: return i
    return None
def hud(cr, t):
    a = ease_out(prog(t, bt('title')['end'] - 0.4, bt('title')['end']))
    if a <= 0: return
    sn, ss = score_at(t); rrect(cr, 30, 140, 1020, 190, 44); cr.set_source_rgba(0.03, 0.04, 0.1, 0.88 * a); cr.fill()
    for side, x, col, sc, lab in (('N', 250, N_C, sn, 'NORTH'), ('S', 830, S_C, ss, 'SOUTH')):
        ptext(cr, lab, x, 200, 44, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); ptext(cr, f'ROUND {i}/8' if i else ('FINAL' if t >= bt('end')['start'] else 'VS'), 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '☀️', 2: '💰', 3: '⚽', 4: '😊', 5: '✈️', 6: '☕', 7: '🏛️', 8: '📈'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((N_C, S_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, 'FINAL ROUND' if i == 8 else f'ROUND {i}', 0, 0, 120 if i == 8 else 150, CRIMSON if i == 8 else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = N_C if win == 'N' else S_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'N' else 1380, 540, ease_out(k)); txt = ('NORTH' if win == 'N' else 'SOUTH') + ' WINS'
    cr.save(); cr.translate(x, 1490); cr.rotate(-0.05 if win == 'N' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 72)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, 72, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- ending ----------
def draw_end(cr, t):
    b, e1, e2, e3, c = bt('end'), bt('e1'), bt('e2'), bt('e3'), bt('cta')
    if t < e1['start']:
        cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.08), 0.02, 540, 1000); arena(cr, t); army(cr, t, NORTH, 'neutral', hop=10); army(cr, t, SOUTH, 'neutral', hop=10); cr.restore()
        cr.set_source_rgba(0, 0, 0.03, 0.5); cr.paint()
        ptext(cr, '4', 300, 900, 380, N_C, 1, sw=26); ptext(cr, '4', 780, 900, 380, S_C, 1, sw=26); ptext(cr, '—', 540, 850, 160, WHITE, 1, sw=14)
        td = w('end', 'draw')
        if t >= td: sx, sy = shake(t, td, 18); cr.save(); cr.translate(sx, sy); slam(cr, 'A DRAW…', 540, 1220, 170, GOLD, t, td); cr.restore()
        ti = w('end', 'is') - 0.1
        if t >= ti: slam(cr, 'OR IS IT?', 540, 1400, 110, WHITE, t, ti, rot=0.04)
        C.draw_captions(cr, t, 1640); return
    kf = ease_out(prog(t, e1['start'], e1['start'] + 0.5)); cy = 1060
    sp = 120 + 60 * ease_io(prog(t, e1['start'], e1['start'] + 0.8))
    sx, sy = shake(t, e2['start'], 18, 0.5)
    cr.save(); cam(cr, push(t, e1['start'], c['end'], 1.12, 1.0), 0.02 - 0.03 * prog(t, e1['start'], c['end']), 540 + sx, 1000 + sy); ocean(cr, t)
    emap(cr, 540, cy, MS, 1, 1, sp, kf)
    fx, fy = scr(2.4, 46.6, 540, cy, MS); gx, gy = scr(15.0, 56.0, 540, cy, MS, sp); ix, iy = scr(17.5, 39.0, 540, cy, MS, -sp); swx, swy = scr(8.2, 46.8, 540, cy, MS)
    key = 'e1' if t < e2['start'] else ('e2' if t < e3['start'] else ('e3' if t < c['start'] else None))
    hf = hop_of(t, e1) if key == 'e1' else 0; hg = hop_of(t, e2) if key == 'e2' else 0; hs = hop_of(t, e3) if key == 'e3' else 0
    ball(cr, 'Germany', gx, gy - hg * 30, 88, 'angry' if t >= e2['start'] else 'shock', 0, 0.3)
    ball(cr, 'Italy', ix, iy, 88, 'angry' if t >= e2['start'] else 'shock', 0, -0.3)
    fr_mood = 'shock' if key == 'e2' else 'happy'; drop = lerp(-900, 0, ease_out(prog(t, e1['start'], e1['start'] + 0.45)))
    ball(cr, 'France', fx, fy + drop - hf * 34, 120, fr_mood, 0, 0); emoji(cr, '👑', fx, fy + drop - 150 - hf * 34, 110, 1 if t < e2['start'] else 1 - prog(t, e2['start'], e2['start'] + 0.3), rot=-0.15)
    if t >= e3['start']: ball(cr, 'Switzerland', swx + 60, swy + 30 - hs * 20, 58 * pop_k(t, e3['start'], 0.3), 'neutral', 0, -0.5)
    cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 760); cr.set_source(g); cr.fill()
    if key:
        nm = SPK[key]; bb = bt(key); bubble(cr, t, bb, {'e1': fx, 'e2': gx, 'e3': swx + 60}[key], 540)
        nametag(cr, nm, 540, 1640, col_of(nm) if nm != 'France' else GOLD[:3])
    else:
        for x, col, word, lab, rot in ((300, N_C, 'North', 'NORTH', -0.04), (780, S_C, 'South', 'SOUTH', 0.04)):
            tt = w('cta', word)
            if t < tt: continue
            kk = pop_k(t, tt) * (1 + 0.03 * math.sin(t * 6 + x)); cr.save(); cr.translate(x, 640); cr.rotate(rot); cr.scale(kk, kk); ptext(cr, lab, 0, 0, 120, col, 1, sw=12); cr.restore()
        tc = w('cta', 'Comment')
        if t >= tc: kk = pop_k(t, tc); cr.save(); cr.translate(540, 440); cr.scale(kk, kk); ptext(cr, 'COMMENT YOUR SIDE', 0, 0, 82, WHITE, 1, sw=11); cr.restore()
        tf = w('cta', 'France')
        if t >= tf:
            kk = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1600); cr.scale(kk, kk); txt = 'WHERE DOES FRANCE BELONG?'; wd = tw(cr, txt, 50)
            rrect(cr, -wd / 2 - 50, -66, wd + 100, 104, 52); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill(); ptext(cr, txt, 0, 4, 50, WHITE, 1, sw=0, shadow=False); cr.restore()

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if draw_hook(cr, t): C.draw_captions(cr, t, 1700); return
    if key in ('h3n', 'h3s'): close_up(cr, t, key); return
    if key == 'title': draw_title(cr, t); return
    if key in ('end', 'e1', 'e2', 'e3', 'cta'): draw_end(cr, t); hud(cr, t)
    elif key[0] == 'c': card(cr, t, int(key[1])); hud(cr, t)
    else:
        i = int(key[1]); talk(cr, t, key, PROP.get(key), rival_mood='shock' if t >= tv_of(i) and RD[i][2][0] == key else 'angry')
        verdict(cr, t, i); hud(cr, t)
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 116; bar_ = beat * 4
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G, driving pulse
    for ci in range(int(dur / bar_) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar_ * 1.15 * SR)) / SR; env = np.minimum(1, Lc / 0.15) * np.exp(-Lc * 0.7)
        put(music, ci * bar_, sum(0.028 * np.sin(2 * np.pi * note(m) * Lc) for m in ch) * env); put(music, ci * bar_, 0.09 * np.sin(2 * np.pi * note(ch[0] - 24) * Lc) * env)
        for j, st in enumerate((0, 0.75, 1.5, 2.5, 3, 3.5)):
            m = ch[j % 3] + 12; P = np.arange(int(0.25 * SR)) / SR; put(music, ci * bar_ + st * beat, 0.03 * sum((1 / h) * np.sin(2 * np.pi * note(m) * h * P) for h in (1, 2, 3)) * np.exp(-P * 14))
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
    boom(0.3, 1.0); boom(w('h1', 'South') - 0.15, 0.7); boom(w('h1', 'who') - 0.1, 0.8)
    for wd in ('money', 'sun'):
        t0 = w('h2', wd) - 0.1; boom(t0, 0.6); [pop(t0 + j * 0.06, 0.07, 900 + 120 * j) for j in range(5)]
    tsp = w('h2', 'sun') + 0.65; boom(tsp, 1.0); rumble(tsp, 1.6)
    for k in ('h2', 'h3n', 'h3s', 'title'): whoosh(bt(k)['start'] - 0.35)
    for wd in ('Eight', 'winner', 'geography'): boom(w('title', wd), 0.7)
    horn(w('title', 'geography'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'N' else 1319); cheer(tv + 0.1)
    for k, sp, _ in LINES:
        if sp: whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
    boom(w('end', 'draw'), 1.0); horn(w('end', 'draw'), 0.1); boom(w('end', 'is') - 0.1, 0.7)
    e1 = bt('e1'); whoosh(e1['start'] - 0.3, 0.3, 0.45); boom(e1['start'] + 0.45, 0.9); bell(e1['start'] + 0.45, 0.14, 1568); cheer(e1['start'] + 0.5, 0.08)
    boom(bt('e2')['start'], 0.8); pop(bt('e3')['start'], 0.12, 600)
    v = np.zeros(n); tt = np.arange(n) / SR
    for s0, a in T['clips']: put(v, s0, a / max(1e-6, np.abs(a).max()) * 0.9)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_euro'))
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
