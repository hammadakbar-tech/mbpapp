# Countryballs: Australia vs France, the Geography War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (the Riviera, time zones, Michelin stars, the ocean...).
# Usage: python3 aufr.py <data_dir> <out.mp4> [--preview t1,t2,...]
import json, math, os, ssl, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import edge_tts.communicate as _etc
if os.path.exists('/root/.ccr/ca-bundle.crt'): _etc._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
import china as C
import warballs as B
from warballs import ball
from big import local, bounds, area, km_shape, km_path
from popu import streaks, shake
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, hexc, SR

A_C, U_C = hexc('#FFC233')[:3], hexc('#4A78FF')[:3]   # Australia gold, France bleu
AU_C, FR_C = A_C, U_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Australia': ('en-AU-WilliamNeural', '+4%'), 'France': ('fr-FR-HenriNeural', '+2%')}
LINES = [
    ('h1', None, "Australia, or France: who would win?"),
    ('h2', None, "One is fourteen times bigger. The other is secretly Australia's neighbour."),
    ('h3c', 'Australia', "G'day! Let's do this, mate!"), ('h3j', 'France', "Bonjour. This will be... magnifique."),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: size."),
    ('r1a', 'France', "I am the biggest country in the European Union!"),
    ('r1b', 'Australia', "Cute. I'm fourteen times bigger than you, mate!"),
    ('c2', None, "Round two: tourists."),
    ('r2a', 'Australia', "Everyone wants to see the Sydney Opera House!"),
    ('r2b', 'France', "Of course. But one hundred and two million tourists visited me last year. The most on Earth!"),
    ('c3', None, "Round three: beaches."),
    ('r3a', 'France', "I have the French Riviera!"),
    ('r3b', 'Australia', "Lovely. I have over eleven thousand beaches. Visit one a day, and it takes thirty years!"),
    ('c4', None, "Round four: food."),
    ('r4a', 'Australia', "We've got meat pies and the flat white!"),
    ('r4b', 'France', "I have over six hundred and fifty Michelin-starred restaurants. You have zero. Michelin doesn't even go to Australia!"),
    ('c5', None, "Round five: heat."),
    ('r5a', 'France', "France's record: forty-six degrees!"),
    ('r5b', 'Australia', "Cute. I've hit fifty point seven. Pack sunscreen, mate!"),
    ('c6', None, "Round six: time zones."),
    ('r6a', 'Australia', "I have three main time zones. Pretty big, right?"),
    ('r6b', 'France', "I have twelve. The most on Earth. And one of them is your neighbour: New Caledonia!"),
    ('c7', None, "Round seven: swimming."),
    ('r7a', 'France', "Léon Marchand won four gold medals in Paris!"),
    ('r7b', 'Australia', "Nice. I've won over seventy-five Olympic gold medals in the pool. Only America has more!"),
    ('c8', None, "Round eight: the GDP war."),
    ('r8a', 'Australia', "My economy is worth about two trillion dollars!"),
    ('r8b', 'France', "Mine is three point six trillion. Merci!"),
    ('c9', None, "Four all. Tiebreaker: the ocean. Who controls more sea?"),
    ('r9a', 'Australia', "Easy. I already beat Japan at sea. Over ten million square kilometres!"),
    ('r9b', 'France', "Only if you count Antarctica, mate. Without it, about eight and a half. Me? Over ten and a half million, thanks to my islands all over the world!"),
    ('e1', 'Australia', "Wait... France is my neighbour?!"),
    ('e2', 'France', "Bonjour, neighbour!"),
    ('cta', None, "Australia, or France? Comment your side, and follow for the next battle.")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SIZE', 'A', ('r1b', 'bigger')), 2: ('TOURISTS', 'U', ('r2b', 'Earth')), 3: ('BEACHES', 'A', ('r3b', 'thirty')), 4: ('FOOD', 'U', ('r4b', 'Australia')),
      5: ('HEAT', 'A', ('r5b', 'sunscreen')), 6: ('TIME ZONES', 'U', ('r6b', 'Caledonia')), 7: ('SWIMMING', 'A', ('r7b', 'more')), 8: ('THE GDP WAR', 'U', ('r8b', 'Merci')),
      9: ('THE OCEAN', 'U', ('r9b', 'world'))}
NR = 9
SHOTS = {
    'r1a': [(None, 'two'), ('European', 'map:eu')], 'r1b': [(None, 'close'), ('fourteen', 'map:size')],
    'r2a': [(None, 'low'), ('Sydney', 'map:opera')], 'r2b': [(None, 'ots'), ('hundred', 'map:tourists')],
    'r3a': [(None, 'close'), ('Riviera', 'map:riviera')], 'r3b': [(None, 'two'), ('eleven', 'map:beaches')],
    'r4a': [(None, 'close'), ('pies', 'map:pies')], 'r4b': [(None, 'low'), ('six', 'map:michelin')],
    'r5a': [(None, 'two'), ('record', 'map:frheat')], 'r5b': [(None, 'low'), ('fifty', 'map:auheat')],
    'r6a': [(None, 'close'), ('three', 'map:au3tz')], 'r6b': [(None, 'ots'), ('twelve', 'map:clocks'), ('neighbour', 'map:caledonia')],
    'r7a': [(None, 'two'), ('Marchand', 'map:marchand')], 'r7b': [(None, 'ots'), ('seventy', 'map:ausswim')],
    'r8a': [(None, 'close'), ('two', 'map:gdpau')], 'r8b': [(None, 'two'), ('three', 'map:gdpfr')],
    'r9a': [(None, 'close'), ('ten', 'map:worldau')], 'r9b': [(None, 'low'), ('Antarctica', 'map:worldnoaq'), ('Me', 'map:worldfr')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2')
C.SAY = {None: {}}
C.HOT = ('australia', 'france', 'win', 'bigger', 'neighbour', 'war', 'tiebreaker', 'ocean', 'comment', 'geography', 'winner', 'secretly', 'caledonia')
C.TAIL_OVERRIDE = {'h1': 0.25, 'h2': 0.5, 'title': 0.6, 'c9': 0.3, 'e2': 0.6, 'cta': 2.4, **{f'c{i}': 0.15 for i in range(1, 9)},
                   **{k: 0.3 for k, s, _ in LINES if s}, **{RD[i][2][0]: 1.1 for i in RD}, 'h3c': 0.2, 'h3j': 0.4}
bt, w = C.bt, C.w
VOICE_OF = {C.say(k, s): (VOICE[sp] if sp else NARR) for k, sp, s in LINES}
class MultiVoice(C.WordVoice):
    def get(self, text):
        import time
        C.VOICE, C.RATE = VOICE_OF.get(text, NARR)
        for attempt in range(6):  # the speech service throttles now and then
            try: return super().get(text)
            except Exception:
                if attempt == 5: raise
                time.sleep(2 + attempt * 2)
G = None
SHORT = {}

def inside(pt, rs):
    x, y = pt; c = False
    for r in rs:
        xs, ys = r[:, 0], r[:, 1]; xj, yj = np.roll(xs, 1), np.roll(ys, 1)
        hit = ((ys > y) != (yj > y)) & (x < (xj - xs) * (y - ys) / np.where(yj - ys == 0, 1e-12, yj - ys) + xs)
        c ^= bool(np.count_nonzero(hit) % 2)
    return c
class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        R = lambda n: [r for r in rings(cf[n]['geometry']) if len(r) > 3]
        self.ref = {'AU': (134.0, -26.0), 'FR': (2.5, 46.5)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('AU', 'Australia', ['Indonesia', 'Papua New Guinea', 'New Zealand', 'Timor-Leste']),
                          ('FR', 'France', ['Spain', 'Portugal', 'Italy', 'Switzerland', 'Germany', 'Belgium', 'Luxembourg', 'Netherlands', 'United Kingdom', 'Andorra', 'Austria', 'Ireland', 'Algeria', 'Tunisia', 'Morocco', 'Denmark', 'Czechia', 'Poland', 'Slovenia', 'Croatia'])):
            rs = R(n)
            if k == 'AU': rs = [r for r in rs if 112 < r[:, 0].mean() < 155 and -45 < r[:, 1].mean() < -9]
            else: rs = [r for r in rs if -6 < r[:, 0].mean() < 10 and 41 < r[:, 1].mean() < 52]
            pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs if nn in cf for r in local(R(nn), *self.ref[k])]
        self.nc = [r - self.off['AU'] for r in local(R('New Caledonia'), *self.ref['AU'])]
        self.fr_true = [r - np.concatenate(self.c['FR']).mean(axis=0) for r in self.c['FR']]
        self.world = [r for f in json.load(open(os.path.join(d, 'ne_110m_land.geojson')))['features'] for r in rings(f['geometry']) if len(r) > 3]
        print('areas M km2: australia', round(area(self.c['AU']) / 1e6, 2), 'france (metro)', round(area(self.c['FR']) / 1e6, 3), 'ratio', round(area(self.c['AU']) / area(self.c['FR']), 1))
        for n, c in (('Australia', 'au'), ('France', 'fr')): B.FL[n] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', c + '.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'Australia' else 'U'
def col_of(name): return AU_C if name == 'Australia' else FR_C
def rival_of(name): return 'France' if name == 'Australia' else 'Australia'
def ocean(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.1, 0.22); g.add_color_stop_rgb(1, 0.05, 0.2, 0.36); cr.set_source(g); cr.paint()

# ---------- shared drawing ----------
def cam(cr, z=1.0, tilt=0.0, fx=540, fy=960):
    cr.translate(540, 960); cr.rotate(tilt); cr.scale(z, z); cr.translate(-fx, -fy)
def push(t, a, b, z0, z1): return lerp(z0, z1, ease_out(prog(t, a, b)))
def arena(cr, t, tint=None):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.03, 0.1); g.add_color_stop_rgb(1, 0.1, 0.08, 0.2); cr.set_source(g); cr.paint()
    for col, x0 in ((A_C, 0), (U_C, W)):
        c = tint or col; g = cairo.RadialGradient(x0, 1100, 50, x0, 1100, 900); g.add_color_stop_rgba(0, *c, 0.36); g.add_color_stop_rgba(1, *c, 0); cr.set_source(g); cr.paint()
    rng = np.random.default_rng(3)
    for _ in range(90):
        x, y, s = rng.uniform(0, W), rng.uniform(0, 700), rng.uniform(0.8, 2.4); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25 + 0.25 * math.sin(t * 2 + x)); cr.fill()
def ocean(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.1, 0.22); g.add_color_stop_rgb(1, 0.05, 0.2, 0.36); cr.set_source(g); cr.paint()
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

def bar(cr, x, base, val, vmax, hmax, k, col, name, lab, wd=190):
    hh = max(8, hmax * val / vmax * k); rrect(cr, x - wd / 2, base - hh, wd, hh, 18); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    ptext(cr, lab, x, base - hh - 22, 50, WHITE, clamp(k * 2), sw=8); ptext(cr, name, x, base - 26, 34, INK, 1, fam='Poppins ExtraBold', sw=0, shadow=False)
    return base - hh
def emopops(cr, t, key, items, y=930, size=170):
    for i, (em, word) in enumerate(items):
        tt = at(key, word) - 0.1
        if t < tt: continue
        x = 540 + (i - (len(items) - 1) / 2) * 290; emoji(cr, em, x, y - abs(math.sin(t * 4 + i)) * 14, size * pop_k(t, tt, 0.3), 1, rot=0.12 * math.sin(t * 3 + i))


# ---------- themed sets for the talking shots ----------
def set_australia(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.16, 0.12, 0.36); g.add_color_stop_rgb(0.45, 0.98, 0.5, 0.26); g.add_color_stop_rgb(0.62, 1.0, 0.78, 0.45); g.add_color_stop_rgb(1, 0.7, 0.3, 0.16); cr.set_source(g); cr.paint()
    cr.new_path(); cr.arc(300, 880, 150, 0, 2 * math.pi); cr.set_source_rgba(1, 0.95, 0.75, 0.9); cr.fill()
    cr.new_path(); cr.move_to(-200, 1180); cr.curve_to(200, 1160, 500, 1190, 1300, 1170); cr.line_to(1300, 2100); cr.line_to(-200, 2100); cr.close_path(); cr.set_source_rgb(0.78, 0.36, 0.18); cr.fill()
    cr.new_path(); cr.move_to(420, 1185); cr.curve_to(450, 1040, 520, 1010, 640, 1012); cr.curve_to(800, 1012, 900, 1030, 960, 1080); cr.curve_to(990, 1120, 1000, 1160, 1010, 1185); cr.close_path(); cr.set_source_rgb(0.66, 0.24, 0.12); cr.fill()
    for j, x in enumerate((90, 1000)):
        cr.new_path(); cr.move_to(x - 10, 1400); cr.curve_to(x - 4, 1250, x + 20, 1150, x + 6, 980); cr.line_to(x + 22, 980); cr.curve_to(x + 30, 1150, x + 14, 1260, x + 12, 1400); cr.close_path(); cr.set_source_rgb(0.92, 0.88, 0.8); cr.fill()
        for k in range(5):
            cr.new_path(); cr.arc(x + 14 + (k - 2) * 46, 960 - 30 * math.sin(k * 1.3), 60, 0, 2 * math.pi); cr.set_source_rgba(0.22, 0.42, 0.24, 0.95); cr.fill()
    rng = np.random.default_rng(4)
    for _ in range(40):
        x, y = rng.uniform(0, W), rng.uniform(1250, 1900); cr.new_path(); cr.arc(x, y, rng.uniform(4, 12), 0, 2 * math.pi); cr.set_source_rgba(0.5, 0.2, 0.1, 0.5); cr.fill()
    for j in range(12):
        ph = (t * 0.06 + j * 0.27) % 1; cr.new_path(); cr.arc((j * 131 + 50 * math.sin(t * 0.5 + j)) % 1100, 1300 - 500 * ph, 3, 0, 2 * math.pi); cr.set_source_rgba(1, 0.9, 0.6, 0.6 * (1 - ph)); cr.fill()
def set_japan(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.98, 0.86, 0.78); g.add_color_stop_rgb(0.55, 1.0, 0.72, 0.62); g.add_color_stop_rgb(1, 0.55, 0.32, 0.38); cr.set_source(g); cr.paint()
    cr.new_path(); cr.arc(760, 600, 230, 0, 2 * math.pi); cr.set_source_rgb(0.86, 0.12, 0.2); cr.fill()
    cr.new_path(); cr.move_to(-100, 1350); cr.line_to(330, 760); cr.line_to(420, 740); cr.line_to(860, 1350); cr.close_path(); cr.set_source_rgb(0.33, 0.3, 0.46); cr.fill()
    cr.new_path(); cr.move_to(240, 880); cr.line_to(330, 760); cr.line_to(420, 740); cr.line_to(520, 880); cr.line_to(460, 860); cr.line_to(400, 900); cr.line_to(330, 860); cr.line_to(290, 900); cr.close_path(); cr.set_source_rgb(0.98, 0.98, 1); cr.fill()
    cr.rectangle(-200, 1350, 1500, 700); cr.set_source_rgb(0.3, 0.2, 0.28); cr.fill()
    x0 = 860  # torii gate
    for xx in (x0 - 120, x0 + 120): cr.rectangle(xx - 16, 1060, 32, 300); cr.set_source_rgb(0.85, 0.15, 0.12); cr.fill()
    cr.rectangle(x0 - 200, 1040, 400, 34); cr.fill(); cr.rectangle(x0 - 165, 1110, 330, 22); cr.fill()
    for j in range(36):
        ph = (t * 0.1 + j * 0.29) % 1; x = (j * 113 + 80 * math.sin(t * 0.8 + j)) % 1150
        cr.save(); cr.translate(x, ph * 2000); cr.rotate(t + j); cr.scale(1, 0.6); cr.new_path(); cr.arc(0, 0, 9, 0, 2 * math.pi); cr.set_source_rgba(1, 0.75, 0.82, 0.9); cr.fill(); cr.restore()
def set_france(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.12, 0.12, 0.34); g.add_color_stop_rgb(0.5, 0.86, 0.5, 0.62); g.add_color_stop_rgb(0.68, 1.0, 0.78, 0.6); g.add_color_stop_rgb(1, 0.2, 0.16, 0.3); cr.set_source(g); cr.paint()
    for k in range(9):  # Haussmann rooftops
        x = -100 + k * 150; h = 260 + 60 * math.sin(k * 1.7)
        cr.rectangle(x, 1300 - h, 150, h + 200); cr.set_source_rgb(0.28, 0.22, 0.36); cr.fill()
        cr.new_path(); cr.move_to(x, 1300 - h); cr.line_to(x + 75, 1300 - h - 60); cr.line_to(x + 150, 1300 - h); cr.close_path(); cr.set_source_rgb(0.22, 0.2, 0.32); cr.fill()
        for r in range(3):
            for c_ in range(3): cr.rectangle(x + 20 + c_ * 42, 1300 - h + 40 + r * 70, 22, 34); cr.set_source_rgba(1, 0.85, 0.5, 0.75 if (k + r + c_) % 3 else 0.25); cr.fill()
    ex, base, top = 760, 1300, 560  # Eiffel Tower silhouette
    cr.new_path(); cr.move_to(ex - 190, base); cr.curve_to(ex - 120, base - 200, ex - 40, top + 260, ex - 10, top); cr.line_to(ex + 10, top)
    cr.curve_to(ex + 40, top + 260, ex + 120, base - 200, ex + 190, base); cr.line_to(ex + 110, base); cr.curve_to(ex + 80, base - 120, ex - 80, base - 120, ex - 110, base); cr.close_path()
    cr.set_source_rgb(0.16, 0.12, 0.22); cr.fill(); cr.rectangle(ex - 120, base - 240, 240, 22); cr.fill(); cr.rectangle(ex - 70, top + 300, 140, 16); cr.fill()
    cr.rectangle(ex - 3, top - 70, 6, 72); cr.fill()
    cr.rectangle(-200, 1300, 1500, 800); cr.set_source_rgb(0.18, 0.22, 0.4); cr.fill()
    for j in range(14):
        y = 1330 + j * 40; ph = (t * 0.5 + j * 0.3) % 1; cr.rectangle(80 + 300 * math.sin(j * 2.1) + 60 * ph, y, 160, 4); cr.set_source_rgba(1, 0.8, 0.6, 0.35); cr.fill()
def set_of(name, cr, t): (set_australia if name == 'Australia' else set_france)(cr, t)

# ---------- shots ----------
def sh_close(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Australia' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.07 * sgn * (1 if sum(map(ord, b['key'])) % 2 else -1), 540, 1100); set_of(name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, 'happy', 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Australia' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, 'happy', 0.04 * h, -sgn * 0.2); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_ots(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Australia' else 1; h = hop_of(t, b); rv = rival_of(name)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.06), 0.02 * sgn, 540 + lerp(0, -sgn * 40, prog(t, t0, t1)), 1000); set_of(name, cr, t)
    ball(cr, name, 540 + sgn * 150, 1080 - h * 36, 210, 'happy', 0.05 * h, -sgn * 0.6)
    ball(cr, rv, 540 - sgn * 470, 1700, 560, 'angry', 0, sgn * 0.9); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.paint()
    bubble(cr, t, b, 540 + sgn * 150, 520); nametag(cr, name, 540 + sgn * 150, 1340, col_of(name))
def sh_two(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Australia' else 1; h = hop_of(t, b); rv = rival_of(name)
    pan = lerp(-60, 60, prog(t, t0, t1)) * sgn
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    for n, x in (('Australia', 290), ('France', 790)):
        hh = h if n == name else 0; ball(cr, n, x, 1300 - hh * 40, 220, 'happy' if n == name else 'angry', 0.05 * hh, 0.8 if n == 'Australia' else -0.8)
    cr.restore()
    sx = (290 if name == 'Australia' else 790) - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1600, col_of(name))
def sh_react(cr, t, b, name, t0, t1):
    rv = rival_of(name); k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.25, 1.08, k), -0.06 if rv == 'Australia' else 0.06, 540 + sx, 1080 + sy); set_of(rv, cr, t)
    ball(cr, rv, 540, 1150, 360, 'shock', 0, 0); cr.restore()
    ptext(cr, '?!', 860, 760, 170, GOLD, pop_k(t, t0 + 0.05), sw=14)
    nametag(cr, rv, 540, 1640, col_of(rv))
def sh_map(cr, t, b, name, t0, t1, scene):
    SCENE[scene](cr, t, b, t0, t1)
    sgn = -1 if name == 'Australia' else 1; h = hop_of(t, b); x = 540 + sgn * 380
    g = cairo.LinearGradient(0, 1380, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.05, 0); g.add_color_stop_rgba(0.4, 0, 0, 0.05, 0.75); cr.rectangle(0, 1380, W, 540); cr.set_source(g); cr.fill()
    ball(cr, name, x, 1480 - h * 26, 115, 'happy', 0.05 * h, -sgn * 0.5); nametag(cr, name, x, 1625, col_of(name))
    C.draw_captions(cr, t, 1760)
SHOT = {'close': sh_close, 'low': sh_low, 'ots': sh_ots, 'two': sh_two, 'react': sh_react}
def shot_list(key):
    b = bt(key); out = []
    for wd, sh in SHOTS[key]: out.append((b['start'] if wd is None else at(key, wd) - 0.12, sh))
    i = int(key[1])
    if RD[i][2][0] == key: out.append((tv_of(i) + 0.55, 'react'))
    out.sort(key=lambda x: x[0]); return out
def draw_line(cr, t, key):
    b = bt(key); name = SPK[key]; sl = shot_list(key)
    j = max(i for i, (s, _) in enumerate(sl) if s <= t or i == 0); t0 = sl[j][0]; t1 = sl[j + 1][0] if j + 1 < len(sl) else b['end']; sh = sl[j][1]
    if sh.startswith('map:'): sh_map(cr, t, b, name, t0, t1, sh[4:])
    else: SHOT[sh](cr, t, b, name, t0, t1)
    f = 1 - prog(t, t0, t0 + 0.1)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.45 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, t0, t0 + 0.16)))

# ---------- full-screen visuals ----------
def mview(cr, t, k, ctr0, ctr1, s0, s1, t0, t1, land, fy=900, rot=0.0):
    e = ease_io(prog(t, t0, t1)); kx, ky = [lerp(a, b_, e) for a, b_ in zip(ctr0, ctr1)]; s = lerp(s0, s1, e)
    ocean(cr, t); cr.save(); cr.translate(540, fy); cr.rotate(rot); cr.translate(-540, -fy)
    cx, cy = 540 - kx * s, fy + ky * s
    km_shape(cr, G.nb[k], cx, cy, s, (0.32, 0.36, 0.42), 1, lw=1, edge=(0.08, 0.1, 0.16))
    km_shape(cr, G.c[k], cx, cy, s, land, 1, lw=1.6, edge=(0.03, 0.04, 0.1))
    return cx, cy, s
def endmap(cr): cr.restore()
def kpt(k, lon, lat, cx, cy, s): p = G.p(k, lon, lat); return cx + p[0] * s, cy - p[1] * s
def label(cr, txt, x, y, size, col, a=1.0): ptext(cr, txt, x, y, size, col, a, sw=size * 0.14)
def pin(cr, x, y, t, t0, col):
    col = tuple(col[:3])
    if t < t0: return
    for j in range(3):
        ph = ((t - t0) * 0.8 + j / 3) % 1; cr.new_path(); cr.arc(x, y, 14 + 70 * ph, 0, 2 * math.pi); cr.set_source_rgba(*col, 1 - ph); cr.set_line_width(5); cr.stroke()
    cr.new_path(); cr.arc(x, y, 14 * pop_k(t, t0, 0.3), 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(3); cr.stroke()
AU_LAND, FR_LAND = (0.86, 0.5, 0.24), (0.86, 0.88, 0.95)
def sc_eu(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'FR', (0, 0), (100, 0), 0.75, 0.62, t0, t1 + 1.5, FR_LAND); endmap(cr)
    label(cr, 'BIGGEST IN THE EU', 540, 620, 96, FR_C); chip(cr, '≈ 550,000 KM²', 540, 730, 46, WHITE, INK, pop_k(t, t0 + 0.4), 1)
def sc_size(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, -100), 0.2, 0.22, t0, t1 + 1.5, AU_LAND)
    k = ease_out(prog(t, t0, t0 + 0.5)); cr.save(); cr.translate(0, (1 - k) * -900); km_shape(cr, G.fr_true, cx, cy, s, FR_LAND, 1, 300, 300, fill=0.95, lw=3, edge=INK); cr.restore()
    if k >= 1: chip(cr, 'FRANCE', cx + 300 * s, cy - 300 * s + 150, 30, WHITE, INK, 1, 1)
    endmap(cr)
    tx = at('r1b', 'fourteen') + 0.4
    if t >= tx: sx, sy = shake(t, tx, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'AUSTRALIA = 14 FRANCES', 540, 640, 84, WHITE, t, tx); cr.restore()
def opera(cr, x, y, sc, a):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc)
    cr.rectangle(-260, 0, 520, 40); cr.set_source_rgba(0.85, 0.75, 0.6, a); cr.fill()
    for j, (dx, h, w_) in enumerate(((-200, 150, 120), (-90, 220, 150), (40, 260, 170), (170, 180, 120))):
        cr.new_path(); cr.move_to(dx - w_ / 2, 0); cr.curve_to(dx - w_ / 2, -h * 0.6, dx, -h, dx + w_ / 2, -h); cr.curve_to(dx + w_ * 0.2, -h * 0.5, dx + w_ * 0.4, -h * 0.2, dx + w_ / 2, 0); cr.close_path()
        cr.set_source_rgba(0.98, 0.98, 1, a); cr.fill_preserve(); cr.set_source_rgba(0.6, 0.65, 0.75, a); cr.set_line_width(4); cr.stroke()
    cr.restore()
def sc_opera(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 151.2, -33.9)), 0.2, 0.8, t0, t0 + 1.1, AU_LAND)
    x, y = kpt('AU', 151.21, -33.86, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, WHITE); endmap(cr)
    if t >= t0 + 0.6: opera(cr, 540, 1180, 1.0, clamp((t - t0 - 0.6) * 3)); label(cr, 'SYDNEY OPERA HOUSE', 540, 620, 80, WHITE)
def sc_tourists(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'FR', (0, 0), tuple(G.p('FR', 2.35, 48.86)), 0.62, 0.8, t0, t1 + 1.5, FR_LAND)
    px, py = kpt('FR', 2.35, 48.86, cx, cy, s)
    for j in range(10):
        a = j / 10 * 2 * math.pi; ph = ((t - t0) * 0.6 + j * 0.37) % 1; R = lerp(700, 40, ph)
        emoji(cr, '✈️', px + R * math.cos(a), py + R * math.sin(a), 64, 1 - ph * 0.6, rot=a + math.pi)
    pin(cr, px, py, t, t0 + 0.3, FR_C); endmap(cr)
    k = ease_out(prog(t, t0, at('r2b', 'tourists') + 0.2)); label(cr, f'{int(102 * k)} MILLION', 540, 620, 110, FR_C); ptext(cr, 'INTERNATIONAL TOURISTS · 2025', 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    te = at('r2b', 'most') - 0.1
    if t >= te: chip(cr, 'AUSTRALIA ≈ 9M', 540, 800, 46, AU_C, INK, pop_k(t, te), 1)
def rail(cr, pts, k, col, wd):
    if k <= 0 or len(pts) < 2: return
    seg = [math.hypot(b_[0] - a[0], b_[1] - a[1]) for a, b_ in zip(pts, pts[1:])]; tot = sum(seg); L = tot * k
    cr.new_path(); cr.move_to(*pts[0]); done = 0; end = pts[0]
    for (a, b_), sl in zip(zip(pts, pts[1:]), seg):
        if done + sl >= L: f = (L - done) / max(sl, 1e-9); end = (lerp(a[0], b_[0], f), lerp(a[1], b_[1], f)); cr.line_to(*end); break
        cr.line_to(*b_); done += sl; end = b_
    cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_source_rgba(*col, 0.3); cr.set_line_width(wd * 3); cr.stroke_preserve(); cr.set_source_rgb(*col); cr.set_line_width(wd); cr.stroke(); return end
def sc_riviera(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'FR', (0, 0), tuple(G.p('FR', 6.6, 43.5)), 0.62, 3.0, t0, t0 + 1.2, FR_LAND)
    pts = [kpt('FR', lon, lat, cx, cy, s) for lon, lat in ((5.95, 43.10), (6.4, 43.15), (6.65, 43.27), (6.93, 43.53), (7.02, 43.55), (7.26, 43.69), (7.42, 43.74))]
    k = ease_io(prog(t, t0 + 0.8, t0 + 1.8)); rail(cr, pts, k, (0.4, 0.9, 1.0), 10)
    for j, (em, lon, lat) in enumerate((('🏖️', 7.0, 43.4), ('⛵', 6.6, 43.0), ('🌴', 7.3, 43.55))):
        if t >= t0 + 1.2 + j * 0.15: x, y = kpt('FR', lon, lat, cx, cy, s); emoji(cr, em, x, y, 100 * pop_k(t, t0 + 1.2 + j * 0.15), 1)
    endmap(cr); label(cr, 'THE FRENCH RIVIERA', 540, 620, 86, (0.5, 0.92, 1))
def sc_beaches(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, -80), 0.2, 0.22, t0, t1 + 2, AU_LAND)
    ring = max(G.c['AU'], key=len); idx = np.linspace(0, len(ring) - 1, 220).astype(int); k = prog(t, t0 + 0.1, at('r3b', 'beaches') + 0.3)
    for j in idx[:int(len(idx) * k)]:
        x, y = cx + ring[j, 0] * s, cy - ring[j, 1] * s; cr.new_path(); cr.arc(x, y, 6, 0, 2 * math.pi); cr.set_source_rgba(1, 0.95, 0.6, 0.95); cr.fill()
    endmap(cr); label(cr, f'{int(11000 * ease_out(k)):,}+ BEACHES', 540, 620, 96, (1, 0.93, 0.6))
    tv = at('r3b', 'Visit') - 0.1
    if t >= tv: chip(cr, 'ONE A DAY = 30 YEARS', 540, 730, 46, WHITE, INK, pop_k(t, tv), 1)
def sc_pies(cr, t, b, t0, t1):
    set_australia(cr, t); cr.set_source_rgba(0.1, 0.04, 0.02, 0.3); cr.paint()
    emoji(cr, '🥧', 360, 1050, 300 * pop_k(t, t0), 1, rot=-0.1); tf = at('r4a', 'flat') - 0.1
    if t >= tf: emoji(cr, '☕', 760, 1080, 240 * pop_k(t, tf), 1, rot=0.1)
    label(cr, 'MEAT PIE & FLAT WHITE', 540, 620, 80, WHITE)
def sc_michelin(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'FR', (0, 0), (0, 0), 0.62, 0.7, t0, t1 + 2, FR_LAND)
    rng = np.random.default_rng(11); pts = []
    while len(pts) < 70:
        p = np.array([rng.uniform(-500, 500), rng.uniform(-500, 500)])
        if inside(p, G.c['FR']): pts.append(p)
    k = prog(t, t0 + 0.1, at('r4b', 'restaurants') + 0.2)
    for j, p in enumerate(pts[:int(70 * k)]):
        emoji(cr, '⭐', cx + p[0] * s, cy - p[1] * s, 44, 1)
    endmap(cr); label(cr, f'{int(668 * ease_out(k))} STARRED RESTAURANTS', 540, 620, 72, GOLD); ptext(cr, 'MICHELIN GUIDE FRANCE & MONACO 2026', 540, 690, 30, WHITE, 0.9, fam='Poppins ExtraBold', sw=5)
    tz = at('r4b', 'zero') - 0.1
    if t >= tz: chip(cr, 'AUSTRALIA: 0', 540, 790, 52, AU_C, INK, pop_k(t, tz), 1)
    tm = at('r4b', 'Michelin', 1) - 0.1
    if t >= tm: chip(cr, 'NO MICHELIN GUIDE IN AUSTRALIA', 540, 890, 40, WHITE, INK, pop_k(t, tm), 1)
def thermo(cr, k, v, x=900, y=1030, col=(1, 0.35, 0.2)):
    rrect(cr, x - 34, y - 300, 68, 360, 34); cr.set_source_rgb(1, 1, 1); cr.fill(); cr.new_path(); cr.arc(x, y + 70, 60, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill()
    hh = lerp(30, 320 * v / 52, k); rrect(cr, x - 18, y + 40 - hh, 36, hh, 18); cr.set_source_rgb(*col); cr.fill()
def sc_frheat(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'FR', (0, 0), tuple(G.p('FR', 4.0, 43.8)), 0.62, 1.6, t0, t0 + 1.1, FR_LAND)
    x, y = kpt('FR', 4.05, 43.72, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (1, 0.5, 0.3)); endmap(cr)
    k = ease_out(prog(t, at('r5a', 'forty') - 0.2, at('r5a', 'degrees') + 0.2)); thermo(cr, k, 46.0)
    if t >= t0 + 0.9: label(cr, 'VÉRARGUES · JUNE 2019', 540, 620, 66, WHITE)
    if k > 0: label(cr, f'{46.0 * k:.1f}°C', 560, 1000, 130, (1, 0.6, 0.4), clamp(k * 3))
def sc_auheat(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 135.4, -27.5)), 0.2, 0.6, t0, t0 + 1.1, AU_LAND)
    x, y = kpt('AU', 135.45, -27.55, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (1, 0.4, 0.2)); endmap(cr)
    k = ease_out(prog(t, at('r5b', 'fifty') - 0.2, at('r5b', 'seven') + 0.2)); thermo(cr, k, 50.7, col=(1, 0.25, 0.1))
    if t >= t0 + 0.9: label(cr, 'OODNADATTA · 1960', 540, 620, 70, WHITE)
    if k > 0: label(cr, f'{50.7 * k:.1f}°C', 560, 1000, 140, (1, 0.45, 0.2), clamp(k * 3))
    f = clamp(k) * 0.35; g = cairo.RadialGradient(540, 960, 300, 540, 960, 1100); g.add_color_stop_rgba(0, 1, 0.5, 0.1, 0); g.add_color_stop_rgba(1, 1, 0.4, 0.1, f); cr.set_source(g); cr.paint()
def sc_au3tz(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, -60), 0.2, 0.22, t0, t1 + 2, AU_LAND)
    def poly(pts, col, a):
        q = [kpt('AU', lon, lat, cx, cy, s) for lon, lat in pts]; cr.new_path(); cr.move_to(*q[0]); [cr.line_to(*p) for p in q[1:]]; cr.close_path(); cr.set_source_rgba(*col, a); cr.fill()
    k = ease_out(prog(t, t0, t0 + 0.6))
    cr.save(); km_path(cr, G.c['AU'], cx, cy, s); cr.clip()
    poly(((100, -5), (129, -5), (129, -50), (100, -50)), (0.3, 0.6, 1), 0.45 * k)
    poly(((129, -5), (138, -5), (138, -26), (141, -26), (141, -50), (129, -50)), (0.4, 0.95, 0.5), 0.45 * k)
    poly(((138, -5), (170, -5), (170, -50), (141, -50), (141, -26), (138, -26)), (1, 0.4, 0.5), 0.45 * k); cr.restore()
    for lab, lon, lat in (('AWST', 122, -25), ('ACST', 134, -23), ('AEST', 145, -24)):
        x, y = kpt('AU', lon, lat, cx, cy, s); ptext(cr, lab, x, y, 40, WHITE, k, sw=7)
    endmap(cr); label(cr, '3 MAIN TIME ZONES', 540, 620, 96, AU_C)
CLOCKS = [('TAHITI', -10), ('MARQUESAS', -9.5), ('GAMBIER', -9), ('CLIPPERTON', -8), ('GUADELOUPE', -4), ('GUIANA', -3), ('PARIS', 1), ('MAYOTTE', 3), ('RÉUNION', 4),
          ('KERGUELEN', 5), ('NEW CALEDONIA', 11), ('WALLIS', 12)]
def sc_clocks(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.05, 0.06, 0.2); g.add_color_stop_rgb(1, 0.12, 0.14, 0.34); cr.set_source(g); cr.paint()
    base = 10.0 + (t - t0) * 0.5
    for j, (nm, off) in enumerate(CLOCKS):
        tj = t0 + 0.15 + j * 0.09
        if t < tj: continue
        x, y = 200 + (j % 3) * 340, 820 + (j // 3) * 200; k = pop_k(t, tj, 0.25); hr = (base + off - 1) % 12
        cr.save(); cr.translate(x, y); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 62, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(*(FR_C if nm != 'NEW CALEDONIA' else AU_C)); cr.set_line_width(8); cr.stroke()
        for a_, L, wd in ((hr / 12 * 2 * math.pi, 34, 7), ((hr % 1) * 2 * math.pi, 50, 4)):
            cr.move_to(0, 0); cr.line_to(L * math.sin(a_), -L * math.cos(a_)); cr.set_source_rgb(0.1, 0.1, 0.15); cr.set_line_width(wd); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
        ptext(cr, nm, 0, 100, 26, WHITE, 1, fam='Poppins ExtraBold', sw=5); cr.restore()
    label(cr, '12 TIME ZONES', 540, 620, 110, FR_C); ptext(cr, 'THE MOST OF ANY COUNTRY (13 WITH ANTARCTICA)', 540, 700, 30, WHITE, 0.9, fam='Poppins ExtraBold', sw=5)
def sc_caledonia(cr, t, b, t0, t1, key='r6b'):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (900, -200), 0.2, 0.2, t0, t0 + 1.0, AU_LAND)
    k = ease_out(prog(t, t0 + 0.2, t0 + 0.6)); km_shape(cr, G.nc, cx, cy, s, FR_C, k, lw=3, edge=WHITE, glow=True)
    a, z = kpt('AU', 153.03, -27.47, cx, cy, s), kpt('AU', 166.45, -22.27, cx, cy, s); kk = ease_out(prog(t, t0 + 0.5, t0 + 1.0))
    cr.move_to(*a); cr.line_to(lerp(a[0], z[0], kk), lerp(a[1], z[1], kk)); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.set_dash([16, 10]); cr.stroke(); cr.set_dash([])
    if kk >= 1: ptext(cr, '~1,500 KM', (a[0] + z[0]) / 2, (a[1] + z[1]) / 2 - 24, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    nx, ny = kpt('AU', 165.5, -21.3, cx, cy, s); pin(cr, nx, ny, t, t0 + 0.3, FR_C); endmap(cr)
    label(cr, 'NEW CALEDONIA', 540, 620, 100, FR_C); chip(cr, 'PART OF FRANCE', 540, 730, 46, WHITE, INK, pop_k(t, t0 + 0.4), 1)
def pool(cr, t):
    g = cairo.LinearGradient(0, 700, 0, 1500); g.add_color_stop_rgb(0, 0.2, 0.7, 0.95); g.add_color_stop_rgb(1, 0.05, 0.35, 0.7); cr.set_source(g); cr.paint()
    for j in range(6):
        y = 760 + j * 140; cr.set_line_width(10)
        for x in range(-40, 1120, 40): cr.move_to(x, y); cr.line_to(x + 20, y); cr.set_source_rgb(*((1, 0.3, 0.3) if (x // 40) % 2 else (1, 1, 1))); cr.stroke()
    for j in range(30):
        x = (j * 137 + 80 * math.sin(t + j)) % 1100; y = 700 + (j * 71) % 800; cr.move_to(x, y); cr.line_to(x + 60, y + 6); cr.set_source_rgba(1, 1, 1, 0.25); cr.set_line_width(3); cr.stroke()
def sc_marchand(cr, t, b, t0, t1):
    pool(cr, t); emoji(cr, '🏊', lerp(100, 980, prog(t, t0, t1 + 1)), 1040, 150, 1)
    tf = at('r7a', 'four') - 0.1
    for j in range(4):
        if t >= tf + j * 0.12: emoji(cr, '🥇', 270 + j * 180, 1300, 110 * pop_k(t, tf + j * 0.12), 1)
    label(cr, 'LÉON MARCHAND', 540, 620, 96, FR_C); ptext(cr, '4 GOLDS · PARIS 2024', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_ausswim(cr, t, b, t0, t1):
    pool(cr, t); k = ease_out(prog(t, t0, at('r7b', 'pool') + 0.3)); n = int(77 * k)
    for j in range(n): emoji(cr, '🥇', 120 + (j % 11) * 84, 820 + (j // 11) * 84, 64, 1)
    label(cr, f'{n} OLYMPIC GOLDS', 540, 620, 96, AU_C); ptext(cr, 'AUSTRALIAN SWIMMING · ALL-TIME', 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tm = at('r7b', 'America') - 0.1
    if t >= tm: chip(cr, '#2 EVER · ONLY THE USA HAS MORE', 540, 1500, 44, GOLD, INK, pop_k(t, tm), 1)
def gdp_circle(cr, x, y, g, col, k, lab, size=50):
    r = 150 * math.sqrt(g / 3.6) * k
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.92); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    if lab: ptext(cr, lab, x, y + size * 0.35, size, INK, clamp(k), sw=0, shadow=False)
def sc_gdpau(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE)
    k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 540, 1000, 2.0, AU_C, 0.2 + 0.8 * k, f'${2.0 * k:.1f}T', 66)
def sc_gdpfr(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE)
    gdp_circle(cr, 790, 1080, 2.0, AU_C, 1, '$2T', 46)
    k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 360, 980, 3.6, FR_C, 0.2 + 0.8 * k, f'${3.6 * k:.1f}T', 76)
FR_SEA = [(2.0, 46.0, 0.35), (-149.4, -17.7, 4.77), (165.6, -21.3, 1.42), (55.5, -21.1, 0.31), (69.4, -49.3, 0.57), (51.8, -46.4, 0.57), (77.5, -38.0, 0.51), (-109.2, 10.3, 0.43),
          (-53.0, 4.5, 0.13), (-61.5, 16.2, 0.09), (-61.0, 14.6, 0.05), (45.1, -12.8, 0.07), (-176.2, -13.3, 0.27), (-56.3, 46.9, 0.01), (40.4, -22.4, 0.64)]
AU_SEA = [(134.0, -26.0, 6.6), (105.6, -10.5, 0.33), (96.9, -12.2, 0.47), (167.95, -29.0, 0.43), (73.5, -53.1, 0.41), (158.9, -54.6, 0.47)]
def world(cr, t, t0, lon0=60.0, kz=3.0, cy=1060):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.1, 0.22); g.add_color_stop_rgb(1, 0.05, 0.2, 0.36); cr.set_source(g); cr.paint()
    def xy(lon, lat): return 540 + (((lon - lon0 + 180) % 360) - 180) * kz, cy - lat * kz
    for r in G.world:
        q = [xy(lon, lat) for lon, lat in r]
        if max(p[0] for p in q) - min(p[0] for p in q) > 600: continue
        cr.new_path(); cr.move_to(*q[0]); [cr.line_to(*p) for p in q[1:]]; cr.close_path(); cr.set_source_rgb(0.3, 0.34, 0.4); cr.fill()
    return xy
def zones(cr, xy, t, items, col, k, kz=3.0, stagger=0.0, t0=0.0):
    for j, (lon, lat, a) in enumerate(items):
        kk = k if not stagger else clamp((t - t0 - j * stagger) * 3)
        r = 34 * math.sqrt(a) * kz / 3.0 * ease_out(kk); x, y = xy(lon, lat)
        if r > 0: cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.55); cr.fill_preserve(); cr.set_source_rgba(*col, 1); cr.set_line_width(3); cr.stroke()
def aq_band(cr, xy, a):
    if a <= 0: return
    q = [xy(lon, -64.5) for lon in range(45, 161, 5)] + [xy(lon, -69) for lon in range(160, 44, -5)]
    cr.new_path(); cr.move_to(*q[0]); [cr.line_to(*p) for p in q[1:]]; cr.close_path(); cr.set_source_rgba(*AU_C, 0.55 * a); cr.fill()
def wnote(cr): ptext(cr, 'ILLUSTRATION · CIRCLE AREA ∝ SEA AREA', 540, 1460, 26, WHITE, 0.8, fam='Poppins ExtraBold', sw=5)
def sc_worldau(cr, t, b, t0, t1):
    xy = world(cr, t, t0, 110, 3.4); k = ease_out(prog(t, t0, t0 + 0.8)); zones(cr, xy, t, AU_SEA, AU_C, k, 3.4); aq_band(cr, xy, ease_out(prog(t, t0 + 0.5, t0 + 1.1)))
    label(cr, '10M+ KM² OF SEA', 540, 620, 96, AU_C); ptext(cr, 'INCLUDING THE ANTARCTIC CLAIM', 540, 700, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6); wnote(cr)
def sc_worldnoaq(cr, t, b, t0, t1):
    xy = world(cr, t, t0, 110, 3.4); zones(cr, xy, t, AU_SEA, AU_C, 1, 3.4); f = 1 - ease_out(prog(t, t0 + 0.3, t0 + 1.0)); aq_band(cr, xy, f)
    x, y = xy(100, -66.5)
    if t >= t0 + 0.2: stamp_x(cr, x, y, t, t0 + 0.2)
    label(cr, '≈ 8.5M KM² WITHOUT IT', 540, 620, 86, AU_C); wnote(cr)
def stamp_x(cr, x, y, t, t0):
    k = ease_out(prog(t, t0, t0 + 0.2)); cr.set_line_width(14); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_source_rgba(1, 0.2, 0.2, 1)
    for s_ in (1, -1): cr.move_to(x - 60 * k, y - 60 * k * s_); cr.line_to(x + 60 * k, y + 60 * k * s_); cr.stroke()
def sc_worldfr(cr, t, b, t0, t1):
    xy = world(cr, t, t0, 20, 3.0); zones(cr, xy, t, AU_SEA, AU_C, 1, 3.0); zones(cr, xy, t, FR_SEA, FR_C, 1, 3.0, stagger=0.12, t0=t0)
    k = ease_out(prog(t, t0, at('r9b', 'million') + 0.3)); label(cr, f'{10.7 * k:.1f}M KM² OF SEA', 540, 620, 96, FR_C); ptext(cr, 'FRANCE: ISLANDS ON EVERY OCEAN', 540, 700, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6); wnote(cr)
SCENE = {'eu': sc_eu, 'size': sc_size, 'opera': sc_opera, 'tourists': sc_tourists, 'riviera': sc_riviera, 'beaches': sc_beaches, 'pies': sc_pies, 'michelin': sc_michelin,
         'frheat': sc_frheat, 'auheat': sc_auheat, 'au3tz': sc_au3tz, 'clocks': sc_clocks, 'caledonia': sc_caledonia, 'marchand': sc_marchand, 'ausswim': sc_ausswim,
         'gdpau': sc_gdpau, 'gdpfr': sc_gdpfr, 'worldau': sc_worldau, 'worldnoaq': sc_worldnoaq, 'worldfr': sc_worldfr}

# ---------- hook, close-ups, title ----------
def draw_hook(cr, t):
    if t >= bt('h3c')['start']: return False
    b1, b2 = bt('h1'), bt('h2')
    if t < b2['start']:
        ti = 0.3; e = ease_out(prog(t, 0, ti)); sx, sy = shake(t, ti, 30, 0.6)
        cr.save(); cam(cr, push(t, 0, b2['start'], 1.0, 1.16), 0.05 * math.sin(t * 1.3), 540 + sx, 1000 + sy); arena(cr, t)
        rec = 26 * math.sin(math.pi * clamp((t - ti) / 0.35)) if t > ti else 0
        for n, x0, x1, sg, ph in (('Australia', 20, 318, -1, 0), ('France', 1060, 762, 1, 1.3)):
            ball(cr, n, lerp(x0, x1, e) + sg * rec, 1040 - abs(math.sin(t * 8 + ph)) * 22 * (t > ti + 0.3), 215, 'angry', 0.12 * (rec / 26), -sg * 0.8)
        if t >= ti: emoji(cr, '⚡', 540, 1010, 210 * pop_k(t, ti, 0.25), 1, rot=0.2 * math.sin(t * 14))
        cr.restore()
        g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.8); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 760); cr.set_source(g); cr.fill()
        slam(cr, 'AUSTRALIA', 540, 300, 170, AU_C, t, -0.3)
        if t >= w('h1', 'or') - 0.1: ptext(cr, 'OR', 540, 420, 70, WHITE, pop_k(t, w('h1', 'or') - 0.1), sw=9)
        slam(cr, 'FRANCE?', 540, 600, 170, FR_C, t, w('h1', 'France') - 0.15, rot=0.03)
        tq = w('h1', 'who') - 0.1
        if t >= tq: qx, qy = shake(t, tq, 14); cr.save(); cr.translate(qx, qy); slam(cr, 'WHO WOULD WIN?', 540, 1500, 124, GOLD, t, tq); cr.restore()
        f = 1 - prog(t, ti, ti + 0.15)
        if ti <= t and f > 0: cr.set_source_rgba(1, 1, 1, 0.75 * f); cr.paint()
        return True
    tp = w('h2', 'secretly') - 0.3
    if t < tp:
        cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, -100), 0.19, 0.22, b2['start'], tp, AU_LAND)
        tj = w('h2', 'fourteen') - 0.2; k = ease_out(prog(t, tj, tj + 0.4))
        if t >= tj: cr.save(); cr.translate(0, (1 - k) * -900); km_shape(cr, G.fr_true, cx, cy, s, FR_LAND, 1, 300, 300, fill=0.95, lw=3, edge=INK); cr.restore()
        endmap(cr)
        g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
        slam(cr, '14× BIGGER', 540, 330, 150, AU_C, t, tj + 0.2)
    else:
        cx, cy, s = mview(cr, t, 'AU', (0, -100), (900, -200), 0.22, 0.2, tp, tp + 0.8, AU_LAND)
        k = ease_out(prog(t, tp + 0.4, tp + 0.8)); km_shape(cr, G.nc, cx, cy, s, FR_C, k, lw=3, edge=WHITE, glow=True)
        nx, ny = kpt('AU', 165.5, -21.3, cx, cy, s); pin(cr, nx, ny, t, tp + 0.5, FR_C); endmap(cr)
        g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
        slam(cr, 'SECRET NEIGHBOURS?!', 540, 330, 110, FR_C, t, tp + 0.4)
    streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.22)))
    return True
def close_up(cr, t, key):
    b = bt(key); name = SPK[key]
    if key == 'h3c': sh_low(cr, t, b, name, b['start'], b['end'])
    else: sh_ots(cr, t, b, name, b['start'], b['end'])
    f = 1 - prog(t, b['start'], b['start'] + 0.12)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.55 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.18)))
def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.5))
    ball(cr, 'Australia', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'France', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'AUSTRALIA', 540, 560, 180, AU_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'FRANCE', 540, 980, 190, FR_C, t, w('title', 'winner'))
    tg = w('title', 'geography')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE GEOGRAPHY WAR', 540, 1170, 92, WHITE, t, tg); cr.restore()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22)))

# ---------- scoreboard, cards, verdicts ----------
def tv_of(i): return w(*RD[i][2])
def score_at(t): return sum(t >= tv_of(i) and RD[i][1] == 'A' for i in RD), sum(t >= tv_of(i) and RD[i][1] == 'U' for i in RD)
def round_of(t):
    for i in RD:
        nxt = bt(f'c{i + 1}')['start'] if i < NR else bt('e1')['start']
        if bt(f'c{i}')['start'] <= t < nxt: return i
    return None
def hud(cr, t):
    a = ease_out(prog(t, bt('title')['end'] - 0.4, bt('title')['end']))
    if a <= 0: return
    sn, ss = score_at(t); rrect(cr, 30, 140, 1020, 190, 44); cr.set_source_rgba(0.03, 0.04, 0.1, 0.88 * a); cr.fill()
    for side, x, col, sc, lab in (('A', 250, AU_C, sn, 'AUSTRALIA'), ('U', 830, FR_C, ss, 'FRANCE')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = ('TIEBREAKER' if i == NR else f'ROUND {i}/8') if i else ('FINAL' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📏', 2: '✈️', 3: '🏖️', 4: '🍽️', 5: '🔥', 6: '🕐', 7: '🏊', 8: '📈', 9: '🌊'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((AU_C, FR_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    head = 'TIEBREAKER' if i == NR else f'ROUND {i}'
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, head, 0, 0, 130 if i == NR else 150, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = (at('c9', 'ocean') - 0.1) if i == NR else b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    if i == NR:
        ptext(cr, '4 — 4', 540, 600, 90, WHITE, pop_k(t, b['l0']), sw=10)
        ts = at('c9', 'Who') - 0.1
        if t >= ts: chip(cr, 'WHO CONTROLS MORE SEA?', 540, 1420, 44, GOLD, INK, pop_k(t, ts), 1)
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = AU_C if win == 'A' else FR_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('AUSTRALIA' if win == 'A' else 'FRANCE') + ' WINS'
    cr.save(); cr.translate(x, 1450); cr.rotate(-0.05 if win == 'A' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 72)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, 72, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- ending ----------
def draw_end(cr, t):
    e1, e2, c = bt('e1'), bt('e2'), bt('cta')
    if t < e2['start']:
        sx, sy = shake(t, e1['l0'], 20, 0.4); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540 + sx, 1100 + sy); set_australia(cr, t); ball(cr, 'Australia', 540, 1290, 290, 'shock', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Australia', 540, 1640, AU_C)
        ptext(cr, 'FRANCE WINS 5 — 4', 540, 790, 80, FR_C, pop_k(t, e1['start'] + 0.2), sw=12); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540, 1100); set_france(cr, t)
        ball(cr, 'France', 540, 1260 - h * 50, 320, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'France', 540, 1640, FR_C)
        for j, em in enumerate(('👋', '🥐', '🥖')): emoji(cr, em, 200 + j * 340, 800 + 20 * math.sin(t * 4 + j), 120 * pop_k(t, e2['l0'] + 0.2 + j * 0.1), 1, rot=0.2 * math.sin(t * 5 + j))
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.08), 0.02, 540, 1000); arena(cr, t)
    ball(cr, 'Australia', 290, 1300, 200, 'neutral', 0, 0.8); ball(cr, 'France', 790, 1300, 200, 'happy', 0, -0.8); cr.restore()
    ptext(cr, '4 — 5', 540, 1000, 140, WHITE, 1, sw=14)
    for x, col, word, lab, rot in ((290, AU_C, 'Australia', 'AUSTRALIA', -0.04), (790, FR_C, 'France', 'FRANCE', 0.04)):
        tt = w('cta', word)
        if t < tt: continue
        kk = pop_k(t, tt) * (1 + 0.03 * math.sin(t * 6 + x)); cr.save(); cr.translate(x, 650); cr.rotate(rot); cr.scale(kk, kk); ptext(cr, lab, 0, 0, 96 if lab == 'AUSTRALIA' else 110, col, 1, sw=12); cr.restore()
    tc = w('cta', 'Comment')
    if t >= tc: kk = pop_k(t, tc); cr.save(); cr.translate(540, 450); cr.scale(kk, kk); ptext(cr, 'COMMENT YOUR SIDE', 0, 0, 82, WHITE, 1, sw=11); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        kk = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1620); cr.scale(kk, kk); txt = 'FOLLOW FOR THE NEXT BATTLE'; wd = tw(cr, txt, 46)
        rrect(cr, -wd / 2 - 50, -62, wd + 100, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill(); ptext(cr, txt, 0, 4, 46, WHITE, 1, sw=0, shadow=False); cr.restore()

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if draw_hook(cr, t): C.draw_captions(cr, t, 1700); return
    if key in ('h3c', 'h3j'): close_up(cr, t, key); return
    if key == 'title': draw_title(cr, t); return
    if key in ('e1', 'e2', 'cta'): draw_end(cr, t); hud(cr, t)
    elif key[0] == 'c': card(cr, t, int(key[1])); hud(cr, t); C.draw_captions(cr, t, 1700) if key == 'c9' else None
    else:
        i = int(key[1]); draw_line(cr, t, key); verdict(cr, t, i); hud(cr, t)
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
    boom(0.3, 1.0); boom(w('h1', 'France') - 0.15, 0.7); boom(w('h1', 'who') - 0.1, 0.8)
    whoosh(bt('h2')['start'] - 0.3); boom(w('h2', 'fourteen') + 0.2, 0.9); whoosh(w('h2', 'secretly') - 0.45, 0.3); boom(w('h2', 'secretly') + 0.1, 0.7)
    for k in ('h3c', 'h3j', 'title'): whoosh(bt(k)['start'] - 0.35)
    for wd in ('Eight', 'winner', 'geography'): boom(w('title', wd), 0.7)
    horn(w('title', 'geography'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1); pop(tv + 0.55, 0.12, 500)
    for k, sp, _ in LINES:
        if sp: whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
        if k in SHOTS:
            for s0, sh in shot_list(k)[1:]: whoosh(s0 - 0.2, 0.16, 0.22)
    boom(at('c9', 'ocean') - 0.1, 0.9); rumble(at('c9', 'Who'), 1.2, 0.15)
    boom(bt('e1')['start'], 0.6); bell(bt('e1')['l0'] + 0.3, 0.12, 1568); cheer(bt('e2')['l0'], 0.12, 1.6)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_aufr'))
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
