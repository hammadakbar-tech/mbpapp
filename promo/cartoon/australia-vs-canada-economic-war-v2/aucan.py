# Countryballs: Australia vs Canada, the Economic War (Version 2), the Geography War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (oil sands, the Pilbara, maple syrup, gold...).
# Usage: python3 aucan.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

A_C, U_C = hexc('#FFC233')[:3], hexc('#FF4A3D')[:3]   # Australia gold, Canada maple red
AU_C, CA_C = A_C, U_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Australia': ('en-AU-WilliamNeural', '+4%'), 'Canada': ('en-CA-LiamNeural', '+4%')}
LINES = [
    ('h1', 'Canada', "Australia, all your money comes from digging holes!"),
    ('h2', 'Australia', "And you sell three quarters of everything to America, mate!"),
    ('h3', None, "Two of the richest resource economies on Earth. But who is actually richer?"),
    ('title', None, "Eight rounds. One winner. This is the economic war."),
    ('c1', None, "Round one: the size of the economy."),
    ('r1a', 'Australia', "My economy is worth about two trillion dollars!"),
    ('r1b', 'Canada', "Sorry, but mine is about two point four trillion, eh."),
    ('c2', None, "Round two: money per person."),
    ('r2a', 'Canada', "Per person, I make about fifty-eight thousand dollars!"),
    ('r2b', 'Australia', "Cute. I make about seventy thousand per person, mate!"),
    ('c3', None, "Round three: oil."),
    ('r3a', 'Australia', "I've got coal and gas!"),
    ('r3b', 'Canada', "I have about one hundred and seventy billion barrels of oil. One of the biggest reserves on Earth!"),
    ('c4', None, "Round four: iron ore."),
    ('r4a', 'Canada', "We mine iron too, eh!"),
    ('r4b', 'Australia', "I dig up over a third of the world's iron ore. And ship more than half of it!"),
    ('c5', None, "Round five: maple syrup."),
    ('r5a', 'Australia', "We've got Vegemite!"),
    ('r5b', 'Canada', "I make over three quarters of the world's maple syrup. I even have a strategic syrup reserve!"),
    ('c6', None, "Round six: no recessions."),
    ('r6a', 'Canada', "My economy is pretty stable, eh."),
    ('r6b', 'Australia', "I went almost thirty years without a recession. A record for a rich country!"),
    ('c7', None, "Round seven: house prices. The round nobody wants to win."),
    ('r7a', 'Australia', "A Sydney house costs fourteen years of income!"),
    ('r7b', 'Canada', "Ouch. Vancouver is only eleven. So... I win?"),
    ('c8', None, "Round eight: minimum wage."),
    ('r8a', 'Canada', "My federal minimum wage is eighteen fifteen an hour!"),
    ('r8b', 'Australia', "Mine is twenty-six forty. Even in US dollars, I pay more!"),
    ('c9', None, "Four all. Tiebreaker: gold. Who digs up more?"),
    ('r9a', 'Canada', "I mined about two hundred tonnes of gold last year!"),
    ('r9b', 'Australia', "And I dug up about two hundred and eighty. Pure gold, mate!"),
    ('e1', 'Canada', "Sorry... rematch?"),
    ('e2', 'Australia', "Anytime, mate. Bring the syrup!"),
    ('cta', None, "Australia, or Canada? Comment your side, and follow for the next battle.")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('GDP', 'U', ('r1b', 'trillion')), 2: ('MONEY PER PERSON', 'A', ('r2b', 'seventy')), 3: ('OIL', 'U', ('r3b', 'Earth')), 4: ('IRON ORE', 'A', ('r4b', 'half')),
      5: ('MAPLE SYRUP', 'U', ('r5b', 'reserve')), 6: ('NO RECESSIONS', 'A', ('r6b', 'country')), 7: ('HOUSE PRICES', 'U', ('r7b', 'win')), 8: ('MINIMUM WAGE', 'A', ('r8b', 'more')),
      9: ('GOLD', 'A', ('r9b', 'Pure'))}
NR = 9
SHOTS = {
    'r1a': [(None, 'two'), ('two', 'map:gdpau')], 'r1b': [(None, 'close'), ('point', 'map:gdpca')],
    'r2a': [(None, 'low'), ('fifty', 'map:percapca')], 'r2b': [(None, 'ots'), ('seventy', 'map:percap')],
    'r3a': [(None, 'close'), ('coal', 'map:coalgas')], 'r3b': [(None, 'two'), ('hundred', 'map:oil')],
    'r4a': [(None, 'two'), ('iron', 'map:ironca')], 'r4b': [(None, 'low'), ('third', 'map:iron')],
    'r5a': [(None, 'close'), ('Vegemite', 'map:vegemite')], 'r5b': [(None, 'ots'), ('three', 'map:syrup')],
    'r6a': [(None, 'two'), ('stable', 'close')], 'r6b': [(None, 'low'), ('thirty', 'map:recession')],
    'r7a': [(None, 'close'), ('fourteen', 'map:housing')], 'r7b': [(None, 'ots'), ('Vancouver', 'map:housing2')],
    'r8a': [(None, 'two'), ('eighteen', 'map:wageca')], 'r8b': [(None, 'low'), ('twenty', 'map:wage')],
    'r9a': [(None, 'close'), ('two', 'map:goldca')], 'r9b': [(None, 'low'), ('two', 'map:gold')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {}}
C.HOT = ('australia', 'canada', 'richer', 'economic', 'war', 'tiebreaker', 'gold', 'comment', 'winner', 'money', 'trillion', 'billion')
C.TAIL_OVERRIDE = {'h1': 0.12, 'h2': 0.2, 'h3': 0.45, 'title': 0.6, 'c9': 0.3, 'e2': 0.6, 'cta': 2.4, **{f'c{i}': 0.15 for i in range(1, 9)},
                   **{k: 0.3 for k, s, _ in LINES if s}, **{RD[i][2][0]: 1.1 for i in RD}, 'h1': 0.12, 'h2': 0.2}
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
        self.ref = {'AU': (134.0, -26.0), 'CA': (-96.0, 60.0)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('AU', 'Australia', ['Indonesia', 'Papua New Guinea', 'New Zealand', 'Timor-Leste']), ('CA', 'Canada', ['United States of America', 'Greenland'])):
            rs = R(n)
            if k == 'AU': rs = [r for r in rs if 112 < r[:, 0].mean() < 155 and -45 < r[:, 1].mean() < -9]
            pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs if nn in cf for r in local(R(nn), *self.ref[k])]
        print('areas M km2: australia', round(area(self.c['AU']) / 1e6, 2), 'canada', round(area(self.c['CA']) / 1e6, 2))
        B.FL['Australia'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'au.png')); B.FL['Canada'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'ca.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'Australia' else 'U'
def col_of(name): return AU_C if name == 'Australia' else CA_C
def rival_of(name): return 'Canada' if name == 'Australia' else 'Australia'
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
def set_canada(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.02, 0.04, 0.12); g.add_color_stop_rgb(0.6, 0.06, 0.16, 0.26); g.add_color_stop_rgb(1, 0.1, 0.12, 0.18); cr.set_source(g); cr.paint()
    for j, col in enumerate(((0.2, 1, 0.6), (0.5, 0.4, 1))):  # aurora
        cr.new_path(); cr.move_to(-200, 420 + j * 90)
        for x in range(-200, 1300, 60): cr.line_to(x, 420 + j * 90 + 70 * math.sin(x / 170 + t * 0.7 + j))
        cr.line_to(1300, 0); cr.line_to(-200, 0); cr.close_path(); g = cairo.LinearGradient(0, 200, 0, 560); g.add_color_stop_rgba(0, *col, 0); g.add_color_stop_rgba(1, *col, 0.28); cr.set_source(g); cr.fill()
    for k, (yb, col) in enumerate(((1250, (0.12, 0.16, 0.26)), (1350, (0.07, 0.1, 0.17)))):
        cr.new_path(); cr.move_to(-200, H)
        for x in range(-200, 1400, 120): cr.line_to(x, yb - 260 - 160 * abs(math.sin(x * 0.011 + k * 2)))
        cr.line_to(1400, H); cr.close_path(); cr.set_source_rgb(*col); cr.fill()
    rng = np.random.default_rng(2)
    for _ in range(26):
        x, s = rng.uniform(-100, 1180), rng.uniform(90, 200); y = 1420 + rng.uniform(0, 160)
        cr.new_path(); cr.move_to(x, y - s * 1.6); cr.line_to(x - s * 0.45, y); cr.line_to(x + s * 0.45, y); cr.close_path(); cr.set_source_rgb(0.03, 0.08, 0.06); cr.fill()
    cr.rectangle(-200, 1560, 1500, 600); cr.set_source_rgb(0.86, 0.9, 0.96); cr.fill()
    for j in range(40):
        ph = (t * 0.12 + j * 0.37) % 1; cr.new_path(); cr.arc((j * 97 + 30 * math.sin(t + j)) % 1100, ph * 1900, 4, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.7); cr.fill()
def set_of(name, cr, t): (set_australia if name == 'Australia' else set_canada)(cr, t)

# ---------- shots ----------
def sh_close(cr, t, b, name, t0, t1, mood='happy'):
    sgn = -1 if name == 'Australia' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.07 * sgn * (1 if sum(map(ord, b['key'])) % 2 else -1), 540, 1100); set_of(name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1, mood='happy'):
    sgn = -1 if name == 'Australia' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, mood, 0.04 * h, -sgn * 0.2); cr.restore()
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
    for n, x in (('Australia', 290), ('Canada', 790)):
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
AU_LAND, CA_LAND = (0.86, 0.5, 0.24), (0.78, 0.26, 0.23)
def gdp_circle(cr, x, y, g, col, k, lab, size=50):
    r = 150 * math.sqrt(g / 2.4) * k
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.92); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    if lab: ptext(cr, lab, x, y + size * 0.35, size, INK, clamp(k), sw=0, shadow=False)
def coins(cr, t, t0, n=14):
    for j in range(n):
        ph = ((t - t0) * 0.6 + j / n) % 1; emoji(cr, '🪙' if j % 2 else '💵', (j * 151) % 1080, lerp(500, 1800, ph), 64, 0.8 * (1 - ph), rot=j + t)
def sc_gdpau(cr, t, b, t0, t1):
    arena(cr, t); coins(cr, t, t0); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE)
    k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 540, 1000, 2.0, AU_C, 0.2 + 0.8 * k, f'${2.0 * k:.1f}T', 66)
def sc_gdpca(cr, t, b, t0, t1):
    arena(cr, t); coins(cr, t, t0); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE)
    gdp_circle(cr, 790, 1080, 2.0, AU_C, 1, '$2.0T', 46)
    k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 360, 980, 2.4, CA_C, 0.2 + 0.8 * k, f'${2.4 * k:.1f}T', 66)
def person_bar(cr, x, base, v, vmax, k, col, name, lab):
    hh = max(8, 460 * v / vmax * k); rrect(cr, x - 100, base - hh, 200, hh, 18); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    label(cr, lab, x, base - hh - 24, 56, WHITE, clamp(k * 2)); ptext(cr, name, x, base + 46, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    cr.new_path(); cr.arc(x, base - hh - 140, 22, 0, 2 * math.pi); cr.rectangle(x - 24, base - hh - 112, 48, 60); cr.set_source_rgba(1, 1, 1, clamp(k * 2)); cr.fill()
def sc_percapca(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP PER PERSON', 540, 620, 66, WHITE)
    k = ease_out(prog(t, t0, at('r2a', 'thousand') + 0.2)); person_bar(cr, 330, 1260, 58, 72, k, CA_C, 'CANADA', f'${int(58 * k)}K')
def sc_percap(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP PER PERSON', 540, 620, 66, WHITE); person_bar(cr, 330, 1260, 58, 72, 1, CA_C, 'CANADA', '$58K')
    k = ease_out(prog(t, t0, w('r2b', 'seventy', end=True) + 0.2)); person_bar(cr, 750, 1260, 70, 72, k, AU_C, 'AUSTRALIA', f'${int(70 * k)}K')
def sc_coalgas(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, 0), 0.2, 0.22, t0, t1 + 2, AU_LAND)
    for j, (em, lon, lat) in enumerate((('⛏️', 148.0, -22.5), ('⛏️', 150.5, -32.5), ('🔥', 116.5, -20.0), ('🔥', 129.0, -12.5), ('🚢', 152.0, -24.0), ('🚢', 114.5, -21.0))):
        tj = t0 + 0.2 + j * 0.12
        if t >= tj: x, y = kpt('AU', lon, lat, cx, cy, s); emoji(cr, em, x, y, 90 * pop_k(t, tj), 1)
    endmap(cr); label(cr, 'COAL & GAS', 540, 620, 110, AU_C)
def sc_oil(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, 0), tuple(G.p('CA', -112.0, 56.5)), 0.15, 0.6, t0, t0 + 1.1, CA_LAND)
    x, y = kpt('CA', -111.6, 57.0, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (0.15, 0.15, 0.15)); endmap(cr)
    k = ease_out(prog(t, at('r3b', 'one') - 0.2, at('r3b', 'barrels') + 0.3))
    for j in range(int(24 * k)): emoji(cr, '🛢️', 200 + (j % 8) * 97, 1180 - (j // 8) * 95, 86, 1)
    label(cr, f'{int(170 * k)} BILLION BARRELS', 540, 620, 80, WHITE); ptext(cr, 'OIL SANDS · ALBERTA', 540, 700, 40, CA_C, 1, fam='Poppins ExtraBold', sw=6)
def sc_ironca(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, 0), tuple(G.p('CA', -67.0, 53.0)), 0.15, 0.5, t0, t0 + 1.1, CA_LAND)
    x, y = kpt('CA', -66.9, 52.95, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (0.8, 0.4, 0.3)); endmap(cr)
    if t >= t0 + 0.9: emoji(cr, '⛏️', 540, 1100, 200 * pop_k(t, t0 + 0.9), 1, rot=0.2 * math.sin(t * 6))
    label(cr, 'LABRADOR TROUGH', 540, 620, 86, WHITE); ptext(cr, 'CANADA: ~3.6% OF SEABORNE IRON ORE', 540, 700, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
def pie(cr, x, y, r, frac, col, k, lab, sub):
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.18); cr.fill()
    if k > 0: cr.new_path(); cr.move_to(x, y); cr.arc(x, y, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * frac * k); cr.close_path(); cr.set_source_rgb(*col); cr.fill()
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.set_line_width(4); cr.stroke()
    label(cr, lab, x, y + 24, 60, WHITE, clamp(k * 2)); ptext(cr, sub, x, y + r + 50, 30, WHITE, 1, fam='Poppins ExtraBold', sw=5)
def sc_iron(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 118.5, -22.5)), 0.2, 0.55, t0, t0 + 1.1, AU_LAND)
    x, y = kpt('AU', 118.6, -22.6, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (0.75, 0.25, 0.12))
    for j in range(5):
        ph = ((t - t0) * 0.35 + j / 5) % 1; sx_, sy_ = kpt('AU', lerp(117.5, 112.0, ph), lerp(-20.4, -17.0, ph), cx, cy, s); emoji(cr, '🚢', sx_, sy_, 70, 1)
    endmap(cr); label(cr, 'THE PILBARA', 540, 620, 100, AU_C)
    k1 = ease_out(prog(t, at('r4b', 'third') - 0.2, at('r4b', 'ore') + 0.2)); pie(cr, 300, 1150, 150, 0.373, AU_C, k1, f'{int(37 * k1)}%', 'OF WORLD PRODUCTION')
    th = at('r4b', 'half') - 0.3
    if t >= th: k2 = ease_out(prog(t, th, th + 0.6)); pie(cr, 780, 1150, 150, 0.553, AU_C, k2, f'{int(55 * k2)}%', 'OF SEABORNE EXPORTS')
def jar(cr, x, y, sc):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc)
    rrect(cr, -110, -60, 220, 260, 40); cr.set_source_rgb(0.24, 0.12, 0.05); cr.fill(); rrect(cr, -120, -110, 240, 70, 20); cr.set_source_rgb(1, 0.82, 0.12); cr.fill()
    rrect(cr, -100, 20, 200, 110, 14); cr.set_source_rgb(1, 0.86, 0.2); cr.fill(); ptext(cr, 'YEAST', 0, 92, 40, (0.6, 0.05, 0.05), 1, sw=0, shadow=False); cr.restore()
def sc_vegemite(cr, t, b, t0, t1):
    set_australia(cr, t); cr.set_source_rgba(0.1, 0.04, 0.02, 0.3); cr.paint(); jar(cr, 540, 1040, pop_k(t, t0, 0.3)); emoji(cr, '🍞', 820, 1180, 160 * pop_k(t, t0 + 0.2), 1)
    label(cr, 'VEGEMITE', 540, 620, 120, (1, 0.85, 0.2))
def sc_syrup(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, 0), tuple(G.p('CA', -72.0, 47.5)), 0.15, 0.45, t0, t0 + 1.1, CA_LAND); endmap(cr)
    k = ease_out(prog(t, at('r5b', 'three') - 0.2, at('r5b', 'syrup') + 0.2)); pie(cr, 300, 1050, 160, 0.75, (0.85, 0.5, 0.12), k, f'{int(75 * k)}%+', "OF THE WORLD'S MAPLE SYRUP")
    emoji(cr, '🍁', 780, 900, 150 * pop_k(t, t0 + 0.4), 1, rot=0.2 * math.sin(t * 2))
    tr = at('r5b', 'strategic') - 0.1
    if t >= tr:
        kk = pop_k(t, tr)
        for j in range(9):
            x, y = 680 + (j % 3) * 110, 1340 - (j // 3) * 120; rrect(cr, x - 46, y - 52, 92, 104, 14); cr.set_source_rgba(0.85, 0.5, 0.12, kk); cr.fill_preserve(); cr.set_source_rgba(0.4, 0.2, 0.05, kk); cr.set_line_width(5); cr.stroke()
        chip(cr, 'STRATEGIC MAPLE SYRUP RESERVE', 540, 760, 40, WHITE, INK, kk, 1)
    label(cr, 'QUÉBEC', 540, 620, 110, WHITE)
def sc_recession(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'NO RECESSION', 540, 620, 96, AU_C); ptext(cr, '1991 TO 2020', 540, 700, 44, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    k = ease_io(prog(t, t0, at('r6b', 'recession') + 0.3)); pts = [(120 + i * 28, 1350 - i * 14 - 40 * math.sin(i * 0.7) * 0.3) for i in range(30)]
    n = max(2, int(30 * k)); cr.new_path(); cr.move_to(*pts[0]); [cr.line_to(*p) for p in pts[1:n]]; cr.set_source_rgb(*AU_C); cr.set_line_width(12); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
    label(cr, f'{int(29 * k)} YEARS', 540, 1000, 130, WHITE)
    tc = at('r6b', 'record') - 0.1
    if t >= tc: chip(cr, 'A RECORD FOR A RICH COUNTRY', 540, 1480, 44, GOLD, INK, pop_k(t, tc), 1)
def house_bar(cr, y, yrs, k, col, name):
    ptext(cr, name, 150, y - 40, 44, col, 1, anchor='l', sw=7)
    for j in range(int(yrs * k)): emoji(cr, '💵', 170 + j * 56, y + 40, 50, 1)
    if k > 0: label(cr, f'{yrs * k:.0f} YRS' if yrs > 11 else f'{yrs * k:.1f} YRS', 900, y + 60, 50, WHITE)
def sc_housing(cr, t, b, t0, t1):
    arena(cr, t); emoji(cr, '🏠', 540, 820, 170 * pop_k(t, t0), 1); label(cr, 'YEARS OF INCOME FOR ONE HOUSE', 540, 620, 56, WHITE); ptext(cr, 'DEMOGRAPHIA 2026 · MEDIAN PRICE ÷ MEDIAN INCOME', 540, 690, 26, WHITE, 0.8, fam='Poppins ExtraBold', sw=5)
    k = ease_out(prog(t, at('r7a', 'fourteen') - 0.2, at('r7a', 'income') + 0.3)); house_bar(cr, 1030, 14, k, AU_C, 'SYDNEY · #2 LEAST AFFORDABLE')
def sc_housing2(cr, t, b, t0, t1):
    arena(cr, t); emoji(cr, '🏠', 540, 820, 170, 1); label(cr, 'YEARS OF INCOME FOR ONE HOUSE', 540, 620, 56, WHITE)
    house_bar(cr, 1030, 14, 1, AU_C, 'SYDNEY'); k = ease_out(prog(t, at('r7b', 'Vancouver') - 0.2, at('r7b', 'eleven') + 0.3)); house_bar(cr, 1250, 10.8, k, CA_C, 'VANCOUVER')
    tw_ = at('r7b', 'win') - 0.1
    if t >= tw_: chip(cr, "STILL TERRIBLE. JUST LESS TERRIBLE.", 540, 760, 40, WHITE, INK, pop_k(t, tw_), 1)
def wage_bar(cr, x, base, usd, k, col, name, loc):
    hh = max(8, 520 * usd / 18 * k); rrect(cr, x - 100, base - hh, 200, hh, 18); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    label(cr, loc, x, base - hh - 70, 50, WHITE, clamp(k * 2)); ptext(cr, f'≈ US${usd:.0f}', x, base - hh - 20, 34, GOLD, clamp(k * 2), fam='Poppins ExtraBold', sw=6); ptext(cr, name, x, base + 46, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_wageca(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'MINIMUM WAGE PER HOUR', 540, 620, 60, WHITE)
    k = ease_out(prog(t, t0, at('r8a', 'hour') + 0.2)); wage_bar(cr, 330, 1280, 13, k, CA_C, 'CANADA (FEDERAL)', 'C$18.15')
def sc_wage(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'MINIMUM WAGE PER HOUR', 540, 620, 60, WHITE); wage_bar(cr, 330, 1280, 13, 1, CA_C, 'CANADA (FEDERAL)', 'C$18.15')
    k = ease_out(prog(t, t0, at('r8b', 'forty') + 0.2)); wage_bar(cr, 750, 1280, 17, k, AU_C, 'AUSTRALIA', 'A$26.44')
def bars_of_gold(cr, x0, y0, n, k, cols=5):
    for j in range(int(n * k)):
        x, y = x0 + (j % cols) * 74, y0 - (j // cols) * 40
        cr.new_path(); cr.move_to(x - 30, y); cr.line_to(x + 30, y); cr.line_to(x + 22, y - 30); cr.line_to(x - 22, y - 30); cr.close_path()
        g = cairo.LinearGradient(0, y - 30, 0, y); g.add_color_stop_rgb(0, 1, 0.9, 0.4); g.add_color_stop_rgb(1, 0.85, 0.6, 0.1); cr.set_source(g); cr.fill_preserve(); cr.set_source_rgb(0.6, 0.4, 0.05); cr.set_line_width(2); cr.stroke()
def sc_goldca(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, 0), tuple(G.p('CA', -81.0, 48.5)), 0.15, 0.45, t0, t0 + 1.1, CA_LAND)
    x, y = kpt('CA', -81.33, 48.48, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (1, 0.85, 0.3)); endmap(cr)
    k = ease_out(prog(t, at('r9a', 'two') - 0.2, at('r9a', 'tonnes') + 0.3)); bars_of_gold(cr, 390, 1420, 20, k)
    label(cr, f'~{int(200 * k)} TONNES', 540, 620, 100, CA_C); ptext(cr, 'GOLD MINED · 2025 (USGS EST.)', 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_gold(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 121.5, -30.8)), 0.2, 0.6, t0, t0 + 1.1, AU_LAND)
    x, y = kpt('AU', 121.5, -30.78, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (1, 0.85, 0.3)); endmap(cr)
    bars_of_gold(cr, 150, 1420, 20, 1, 4); ptext(cr, 'CANADA', 260, 1480, 32, CA_C, 1, fam='Poppins ExtraBold', sw=5)
    k = ease_out(prog(t, at('r9b', 'two') - 0.2, at('r9b', 'eighty') + 0.3)); bars_of_gold(cr, 640, 1420, 28, k, 4); ptext(cr, 'AUSTRALIA', 750, 1480, 32, AU_C, 1, fam='Poppins ExtraBold', sw=5)
    label(cr, f'~{int(280 * k)} TONNES', 540, 620, 100, AU_C); ptext(cr, 'KALGOORLIE · WESTERN AUSTRALIA', 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
SCENE = {'gdpau': sc_gdpau, 'gdpca': sc_gdpca, 'percapca': sc_percapca, 'percap': sc_percap, 'coalgas': sc_coalgas, 'oil': sc_oil, 'ironca': sc_ironca, 'iron': sc_iron,
         'vegemite': sc_vegemite, 'syrup': sc_syrup, 'recession': sc_recession, 'housing': sc_housing, 'housing2': sc_housing2, 'wageca': sc_wageca, 'wage': sc_wage,
         'goldca': sc_goldca, 'gold': sc_gold}

# ---------- hook, close-ups, title ----------
def draw_hook(cr, t):
    """Cold open: Canada and Australia trade economic insults, then the money question."""
    if t >= bt('title')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        sh_close(cr, t, b1, 'Canada', 0, b1['end'], 'angry'); emoji(cr, '⛏️', 880, 820, 140, 1, rot=-0.3 + 0.2 * math.sin(t * 8)); return True
    if t < b3['start']:
        sx, sy = shake(t, w('h2', 'America') - 0.05, 20, 0.4); cr.save(); cr.translate(sx, sy)
        sh_low(cr, t, b2, 'Australia', b2['start'], b2['end'], 'angry'); cr.restore()
        if t >= w('h2', 'three') - 0.1: chip(cr, '~75% OF CANADA’S EXPORTS GO TO THE USA', 540, 820, 40, WHITE, INK, pop_k(t, w('h2', 'three') - 0.1), 1)
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2))); return True
    arena(cr, t); coins(cr, t, b3['start'], 22)
    for n, x, xs in (('Australia', 290, -300), ('Canada', 790, 1380)):
        e = ease_out(prog(t, b3['start'], b3['start'] + 0.5)); ball(cr, n, lerp(xs, x, e), 1250 - abs(math.sin(t * 6 + x)) * 12, 200, 'angry', 0, 0.8 if n == 'Australia' else -0.8)
    tr = w('h3', 'richer') - 0.15
    slam(cr, 'WHO IS RICHER?', 540, 480, 120, GOLD, t, tr)
    if t >= tr: emoji(cr, '💰', 540, 820, 230 * pop_k(t, tr), 1, rot=0.1 * math.sin(t * 5))
    C.draw_captions(cr, t, 1700)
    f = 1 - prog(t, b3['start'], b3['start'] + 0.15)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b3['start'], b3['start'] + 0.2)))
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
    ball(cr, 'Australia', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'Canada', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'AUSTRALIA', 540, 560, 180, AU_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'CANADA', 540, 980, 190, CA_C, t, w('title', 'winner'))
    tg = w('title', 'economic')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE ECONOMIC WAR', 540, 1170, 96, GOLD, t, tg); chip(cr, 'VERSION 2', 540, 1330, 50, WHITE, INK, pop_k(t, tg + 0.3), 1); cr.restore()
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
    for side, x, col, sc, lab in (('A', 250, AU_C, sn, 'AUSTRALIA'), ('U', 830, CA_C, ss, 'CANADA')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = ('TIEBREAKER' if i == NR else f'ROUND {i}/8') if i else ('FINAL' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📈', 2: '💵', 3: '🛢️', 4: '⛏️', 5: '🍁', 6: '📉', 7: '🏠', 8: '💰', 9: '🥇'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((AU_C, CA_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    head = 'TIEBREAKER' if i == NR else f'ROUND {i}'
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, head, 0, 0, 130 if i == NR else 150, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = (at('c9', 'gold') - 0.1) if i == NR else b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    if i == NR:
        ptext(cr, '4 — 4', 540, 600, 90, WHITE, pop_k(t, b['l0']), sw=10)
        ts = at('c9', 'digs') - 0.1
        if t >= ts: chip(cr, 'WHO DIGS UP MORE?', 540, 1420, 44, GOLD, INK, pop_k(t, ts), 1)
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = AU_C if win == 'A' else CA_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('AUSTRALIA' if win == 'A' else 'CANADA') + ' WINS'
    cr.save(); cr.translate(x, 1450); cr.rotate(-0.05 if win == 'A' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 72)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, 72, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- ending ----------
def draw_end(cr, t):
    e1, e2, c = bt('e1'), bt('e2'), bt('cta')
    if t < e2['start']:
        cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540, 1100); set_canada(cr, t); ball(cr, 'Canada', 540, 1290, 290, 'sad', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Canada', 540, 1640, CA_C)
        ptext(cr, 'AUSTRALIA WINS 5 — 4', 540, 790, 76, AU_C, pop_k(t, e1['start'] + 0.2), sw=12); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), -0.05, 540, 1100); set_australia(cr, t)
        ball(cr, 'Australia', 540, 1260 - h * 50, 320, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Australia', 540, 1640, AU_C); emoji(cr, '🥞', 860, 820, 140 * pop_k(t, e2['l0'] + 0.5), 1)
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.08), 0.02, 540, 1000); arena(cr, t)
    ball(cr, 'Australia', 290, 1300, 200, 'happy', 0, 0.8); ball(cr, 'Canada', 790, 1300, 200, 'sad', 0, -0.8); cr.restore()
    ptext(cr, '5 — 4', 540, 1000, 140, WHITE, 1, sw=14)
    for x, col, word, lab, rot in ((290, AU_C, 'Australia', 'AUSTRALIA', -0.04), (790, CA_C, 'Canada', 'CANADA', 0.04)):
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
    if draw_hook(cr, t): return
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
    boom(0.0, 1.0); rumble(0.0, 1.0, 0.25); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(w('h2', 'America') - 0.05, 0.8)
    whoosh(bt('h3')['start'] - 0.3, 0.3); boom(w('h3', 'richer') - 0.15, 1.0); bell(w('h3', 'richer'), 0.12, 1568)
    for k in ('title',): whoosh(bt(k)['start'] - 0.35)
    for wd in ('Eight', 'winner', 'economic'): boom(w('title', wd), 0.7)
    horn(w('title', 'economic'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1); pop(tv + 0.55, 0.12, 500)
    for k, sp, _ in LINES:
        if sp: whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
        if k in SHOTS:
            for s0, sh in shot_list(k)[1:]: whoosh(s0 - 0.2, 0.16, 0.22)
    boom(at('c9', 'gold') - 0.1, 0.9); rumble(at('c9', 'digs'), 1.2, 0.15)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_aucan'))
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
