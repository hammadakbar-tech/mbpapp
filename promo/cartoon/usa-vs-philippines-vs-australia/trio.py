# Countryballs: USA vs Philippines vs Australia, the Triple Threat (food-fight cold open, 2-2-2 tie).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (islands, volcanoes, reefs, Christmas in September...).
# Usage: python3 trio.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

US_C, PH_C, AU_C = hexc('#4F8CFF')[:3], hexc('#FFC233')[:3], hexc('#2DBE6C')[:3]
A_C, U_C = US_C, AU_C
TEAMS = ('USA', 'Philippines', 'Australia')
COLS = {'USA': US_C, 'Philippines': PH_C, 'Australia': AU_C}
POSX = {'USA': 200, 'Philippines': 540, 'Australia': 880}
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'USA': ('en-US-EricNeural', '+4%'), 'Philippines': ('fil-PH-AngeloNeural', '+4%'), 'Australia': ('en-AU-WilliamNeural', '+4%')}
LINES = [
    ('h1', 'USA', "Burgers rule the world!"),
    ('h2', 'Australia', "Mate, a meat pie beats a burger any day!"),
    ('h3', 'Philippines', "Excuse me? Chickenjoy and rice beats you both!"),
    ('h4', None, "Three countries. One food fight. Who wins?"),
    ('title', None, "Six rounds. Three countries. One champion. This is the triple threat."),
    ('c1', None, "Round one: heat."),
    ('r1a', 'Philippines', "My record is forty-two degrees!"),
    ('r1b', 'Australia', "Mine's fifty point seven, mate!"),
    ('r1c', 'USA', "Death Valley hit fifty-six point seven. The hottest ever recorded on Earth!"),
    ('c2', None, "Round two: coastline."),
    ('r2a', 'USA', "I've got almost twenty thousand kilometres of coastline!"),
    ('r2b', 'Australia', "I've got over twenty-five thousand!"),
    ('r2c', 'Philippines', "Thirty-six thousand. Longer than both of you!"),
    ('c3', None, "Round three: deadly animals."),
    ('r3a', 'USA', "I've got grizzly bears and rattlesnakes!"),
    ('r3b', 'Philippines', "I've got the Philippine cobra. It can spit venom!"),
    ('r3c', 'Australia', "Cute. I've got the inland taipan. The most venomous snake on Earth!"),
    ('c4', None, "Round four: space."),
    ('r4a', 'Australia', "The first Moon walk was beamed to the world through Australia!"),
    ('r4b', 'Philippines', "I launched my own satellite, Diwata-1!"),
    ('r4c', 'USA', "Nice. But I put twelve humans on the Moon!"),
    ('c5', None, "Round five: food."),
    ('r5a', 'Australia', "Aussies eat two hundred and seventy million meat pies a year!"),
    ('r5b', 'USA', "McDonald's has over forty thousand restaurants worldwide!"),
    ('r5c', 'Philippines', "And in the Philippines, Jollibee still beats McDonald's. Chickenjoy wins!"),
    ('c6', None, "Final round: reefs."),
    ('r6a', 'USA', "Florida has the third biggest barrier reef on Earth!"),
    ('r6b', 'Philippines', "Tubbataha Reef is a UNESCO World Heritage Site!"),
    ('r6c', 'Australia', "The Great Barrier Reef. The biggest on Earth!"),
    ('e1', 'Australia', "Two, two, and two?! It's a three-way tie!"),
    ('e2', 'Philippines', "Then let the viewers decide! Salamat!"),
    ('e3', 'USA', "Fine. But I'm still the loudest!"),
    ('cta', None, "It's a three-way tie! You pick the tiebreaker. Comment it below, and subscribe to see who wins!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('HEAT', 'USA', ('r1c', 'Earth')), 2: ('COASTLINE', 'Philippines', ('r2c', 'both')), 3: ('DEADLY ANIMALS', 'Australia', ('r3c', 'Earth')),
      4: ('SPACE', 'USA', ('r4c', 'Moon')), 5: ('FOOD', 'Philippines', ('r5c', 'wins')), 6: ('REEFS', 'Australia', ('r6c', 'Earth'))}
NR = 6
PREV = {}
for i in range(1, NR + 1): PREV[f'r{i}b'], PREV[f'r{i}c'], PREV[f'r{i}a'] = SPK[f'r{i}a'], SPK[f'r{i}b'], SPK[f'r{i}c']
SHOTS = {
    'r1a': [(None, 'close'), ('record', 'map:phheat')], 'r1b': [(None, 'ots'), ('fifty', 'map:auheat')], 'r1c': [(None, 'three'), ('Death', 'map:usheat')],
    'r2a': [(None, 'low'), ('twenty', 'map:coast_us')], 'r2b': [(None, 'ots'), ('over', 'map:coast_au')], 'r2c': [(None, 'close'), ('Thirty', 'map:coast_ph')],
    'r3a': [(None, 'three'), ('grizzly', 'map:usanimals')], 'r3b': [(None, 'ots'), ('Philippine', 'map:cobra')], 'r3c': [(None, 'low'), ('inland', 'map:taipan')],
    'r4a': [(None, 'close'), ('beamed', 'map:honeysuckle')], 'r4b': [(None, 'ots'), ('satellite', 'map:diwata')], 'r4c': [(None, 'three'), ('twelve', 'map:apollo')],
    'r5a': [(None, 'low'), ('two', 'map:pies')], 'r5b': [(None, 'ots'), ('McDonald', 'map:mcd')], 'r5c': [(None, 'close'), ('Jollibee', 'map:jollibee')],
    'r6a': [(None, 'three'), ('Florida', 'map:florida')], 'r6b': [(None, 'ots'), ('Tubbataha', 'map:tubbataha')], 'r6c': [(None, 'low'), ('Great', 'map:reef')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3', 'h4')
C.SAY = {None: {'Tubbataha': 'Too-bah-tah-ha', 'Diwata-1': 'Dee-wah-tah one', 'Jollibee': 'Jolly-bee', 'Chickenjoy': 'Chicken joy'}}
C.HOT = ('usa', 'philippines', 'australia', 'food', 'fight', 'burgers', 'pie', 'chickenjoy', 'tie', 'tiebreaker', 'comment', 'subscribe', 'champion', 'triple', 'threat')
C.TAIL_OVERRIDE = {'h1': 0.1, 'h2': 0.12, 'h3': 0.15, 'h4': 0.6, 'title': 0.6, 'e1': 0.3, 'e2': 0.3, 'e3': 0.4, 'cta': 3.6, **{f'c{i}': 0.15 for i in range(1, 7)},
                   **{k: 0.25 for k, s, _ in LINES if s and k[0] == 'r'}, **{RD[i][2][0]: 1.1 for i in RD}}
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
        self.ref = {'US': (-98.0, 39.0), 'AU': (134.0, -26.0), 'PH': (122.0, 12.0)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('US', 'United States of America', ['Canada', 'Mexico', 'Cuba', 'Bahamas']), ('AU', 'Australia', ['Indonesia', 'Papua New Guinea', 'New Zealand', 'Timor-Leste']),
                          ('PH', 'Philippines', ['Malaysia', 'Indonesia', 'Taiwan', 'China', 'Vietnam', 'Brunei'])):
            rs = R(n)
            if k == 'US': rs = [r for r in rs if -126 < r[:, 0].mean() < -66 and 24 < r[:, 1].mean() < 50]
            if k == 'AU': rs = [r for r in rs if 112 < r[:, 0].mean() < 155 and -45 < r[:, 1].mean() < -9]
            pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs if nn in cf for r in local(R(nn), *self.ref[k])]
        for nm, f in (('USA', 'us'), ('Philippines', 'ph'), ('Australia', 'au')): B.FL[nm] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', f + '.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def col_of(name): return COLS.get(name, WHITE)
def rival_of(name): return 'Australia' if name != 'Australia' else 'USA'

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



# ---------- themed sets ----------
def set_usa(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.05, 0.08, 0.24); g.add_color_stop_rgb(0.55, 0.45, 0.35, 0.6); g.add_color_stop_rgb(0.7, 0.98, 0.6, 0.45); g.add_color_stop_rgb(1, 0.15, 0.12, 0.2); cr.set_source(g); cr.paint()
    rng = np.random.default_rng(5)
    for _ in range(60): x, y = rng.uniform(0, W), rng.uniform(0, 600); cr.new_path(); cr.arc(x, y, 1.6, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.5 + 0.3 * math.sin(t * 2 + x)); cr.fill()
    for k in range(11):
        x = -60 + k * 110; h = 260 + 380 * abs(math.sin(k * 1.9)); cr.rectangle(x, 1340 - h, 96, h); cr.set_source_rgb(0.12, 0.12, 0.22); cr.fill()
        for r in range(int(h // 50)):
            for c_ in range(3):
                if (k + r + c_) % 3: cr.rectangle(x + 12 + c_ * 28, 1340 - h + 16 + r * 50, 14, 22); cr.set_source_rgba(1, 0.85, 0.5, 0.7); cr.fill()
    sx, sb = 860, 1340  # statue-like silhouette on a pedestal
    cr.rectangle(sx - 70, sb - 160, 140, 160); cr.set_source_rgb(0.08, 0.32, 0.3); cr.fill()
    cr.new_path(); cr.move_to(sx - 50, sb - 160); cr.line_to(sx - 30, sb - 440); cr.line_to(sx + 30, sb - 440); cr.line_to(sx + 50, sb - 160); cr.close_path(); cr.fill()
    cr.new_path(); cr.arc(sx, sb - 470, 34, 0, 2 * math.pi); cr.fill(); cr.rectangle(sx + 20, sb - 620, 22, 170); cr.fill()
    cr.new_path(); cr.arc(sx + 31, sb - 640, 22, 0, 2 * math.pi); cr.set_source_rgb(1, 0.8, 0.3); cr.fill()
    cr.rectangle(-200, 1340, 1500, 800); cr.set_source_rgb(0.1, 0.12, 0.2); cr.fill()
    for j in range(12): cr.rectangle(80 + j * 90 + 20 * math.sin(t + j), 1380 + (j % 4) * 50, 70, 4); cr.set_source_rgba(1, 0.8, 0.5, 0.3); cr.fill()
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
def set_philippines(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.35, 0.7, 0.98); g.add_color_stop_rgb(0.55, 0.85, 0.93, 1.0); g.add_color_stop_rgb(0.62, 0.1, 0.65, 0.75); g.add_color_stop_rgb(1, 0.04, 0.35, 0.55); cr.set_source(g); cr.paint()
    cr.new_path(); cr.arc(800, 760, 120, 0, 2 * math.pi); cr.set_source_rgba(1, 0.92, 0.5, 0.95); cr.fill()
    for j in range(3):  # limestone islets
        x = 200 + j * 300; cr.new_path(); cr.move_to(x - 130, 1180); cr.curve_to(x - 120, 960 - j * 40, x + 60, 930 - j * 30, x + 120, 1180); cr.close_path(); cr.set_source_rgb(0.18, 0.45, 0.3); cr.fill()
    for j in range(16):
        y = 1200 + j * 26; ph = (t * 0.4 + j * 0.37) % 1; cr.rectangle(60 + 420 * math.sin(j * 1.7) + 80 * ph, y, 140, 4); cr.set_source_rgba(1, 1, 1, 0.35); cr.fill()
    cr.new_path(); cr.move_to(-200, 1420); cr.curve_to(300, 1380, 700, 1400, 1300, 1430); cr.line_to(1300, 2100); cr.line_to(-200, 2100); cr.close_path(); cr.set_source_rgb(0.98, 0.92, 0.78); cr.fill()
    for x, lean in ((90, 1), (990, -1)):
        cr.new_path(); cr.move_to(x - 10, 1440); cr.curve_to(x, 1250, x + lean * 40, 1100, x + lean * 70, 980); cr.line_to(x + lean * 70 + 16, 990); cr.curve_to(x + lean * 50, 1110, x + 18, 1250, x + 12, 1440); cr.close_path(); cr.set_source_rgb(0.45, 0.32, 0.2); cr.fill()
        for k in range(6):
            a = -math.pi / 2 + (k - 2.5) * 0.55 + 0.05 * math.sin(t * 1.5 + k); L = 150
            cr.new_path(); cr.move_to(x + lean * 75, 985); cr.curve_to(x + lean * 75 + math.cos(a) * L * 0.5, 985 + math.sin(a) * L * 0.3 - 40, x + lean * 75 + math.cos(a) * L, 985 + math.sin(a) * L * 0.4 + 20, x + lean * 75 + math.cos(a) * L * 1.1, 985 + 60)
            cr.set_source_rgb(0.12, 0.5, 0.25); cr.set_line_width(22); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
def set_of(name, cr, t): {'USA': set_usa, 'Australia': set_australia, 'Philippines': set_philippines}[name](cr, t)
def sgn_of(name): return {'USA': -1, 'Philippines': 0, 'Australia': 1}[name]
# ---------- shots ----------
def sh_close(cr, t, b, name, t0, t1, mood='happy'):
    sgn = sgn_of(name) or (1 if sum(map(ord, b['key'])) % 2 else -1); h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.07 * sgn, 540, 1100); set_of(name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1, mood='happy'):
    h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, mood, 0.04 * h, 0); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_ots(cr, t, b, name, t0, t1):
    rv = PREV.get(b['key'], rival_of(name)); sgn = 1 if POSX[name] >= POSX[rv] else -1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.06), 0.02 * sgn, 540 + lerp(0, -sgn * 40, prog(t, t0, t1)), 1000); set_of(name, cr, t)
    ball(cr, name, 540 + sgn * 150, 1080 - h * 36, 210, 'happy', 0.05 * h, -sgn * 0.6)
    ball(cr, rv, 540 - sgn * 470, 1700, 560, 'angry', 0, sgn * 0.9); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.paint()
    bubble(cr, t, b, 540 + sgn * 150, 520); nametag(cr, name, 540 + sgn * 150, 1340, col_of(name))
def sh_three(cr, t, b, name, t0, t1):
    h = hop_of(t, b); pan = lerp(-40, 40, prog(t, t0, t1))
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    for n in TEAMS:
        hh = h if n == name else 0; ball(cr, n, POSX[n], 1300 - hh * 40, 165 if n == name else 140, 'happy' if n == name else 'angry', 0.05 * hh, (540 - POSX[n]) / 500)
    cr.restore()
    sx = POSX[name] - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1560, col_of(name))
def sh_react(cr, t, b, name, t0, t1):
    losers = [n for n in TEAMS if n != name]; k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.2, 1.05, k), 0.03, 540 + sx, 1080 + sy); set_of(losers[0], cr, t)
    for j, n in enumerate(losers): ball(cr, n, 300 + j * 480, 1180, 230, 'shock', 0, 0)
    cr.restore(); ptext(cr, '?!', 540, 820, 170, GOLD, pop_k(t, t0 + 0.05), sw=14)
    for j, n in enumerate(losers): nametag(cr, n, 300 + j * 480, 1500, col_of(n))
def sh_map(cr, t, b, name, t0, t1, scene):
    SCENE[scene](cr, t, b, t0, t1)
    x = 160 if name == 'USA' else 920; h = hop_of(t, b)
    g = cairo.LinearGradient(0, 1380, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.05, 0); g.add_color_stop_rgba(0.4, 0, 0, 0.05, 0.75); cr.rectangle(0, 1380, W, 540); cr.set_source(g); cr.fill()
    ball(cr, name, x, 1480 - h * 26, 115, 'happy', 0.05 * h, 0); nametag(cr, name, x, 1625, col_of(name))
    C.draw_captions(cr, t, 1760)
SHOT = {'close': sh_close, 'low': sh_low, 'ots': sh_ots, 'three': sh_three, 'react': sh_react}
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
AU_LAND, PH_LAND = (0.86, 0.5, 0.24), (0.55, 0.8, 0.45)
def rail(cr, pts, k, col, wd):
    if k <= 0 or len(pts) < 2: return
    seg = [math.hypot(b_[0] - a[0], b_[1] - a[1]) for a, b_ in zip(pts, pts[1:])]; tot = sum(seg); L = tot * k
    cr.new_path(); cr.move_to(*pts[0]); done = 0; end = pts[0]
    for (a, b_), sl in zip(zip(pts, pts[1:]), seg):
        if done + sl >= L: f = (L - done) / max(sl, 1e-9); end = (lerp(a[0], b_[0], f), lerp(a[1], b_[1], f)); cr.line_to(*end); break
        cr.line_to(*b_); done += sl; end = b_
    cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_source_rgba(*col, 0.3); cr.set_line_width(wd * 3); cr.stroke_preserve(); cr.set_source_rgb(*col); cr.set_line_width(wd); cr.stroke(); return end
def dots(cr, k_, n, cx, cy, s, lon0, lon1, lat0, lat1, col, seed):
    rng = np.random.default_rng(seed); m = 0; tries = 0
    while m < n and tries < n * 8:
        tries += 1; lon, lat = rng.uniform(lon0, lon1), rng.uniform(lat0, lat1); p = G.p(k_, lon, lat)
        if inside(p, G.c[k_]): x, y = cx + p[0] * s, cy - p[1] * s; cr.new_path(); cr.arc(x, y, 3.5, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.9); cr.fill(); m += 1
US_LAND, AU_LAND, PH_LAND = (0.36, 0.5, 0.78), (0.86, 0.5, 0.24), (0.55, 0.8, 0.45)
def thermo(cr, k, v, x=900, y=1030, col=(1, 0.35, 0.2)):
    rrect(cr, x - 34, y - 300, 68, 360, 34); cr.set_source_rgb(1, 1, 1); cr.fill(); cr.new_path(); cr.arc(x, y + 70, 60, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill()
    hh = lerp(30, 320 * v / 58, k); rrect(cr, x - 18, y + 40 - hh, 36, hh, 18); cr.set_source_rgb(*col); cr.fill()
def heat(cr, t, k_, lon, lat, ctr, s0, s1, land, t0, key, w0, w1, v, place, col):
    cx, cy, s = mview(cr, t, k_, (0, 0), tuple(G.p(k_, *ctr)), s0, s1, t0, t0 + 1.1, land)
    x, y = kpt(k_, lon, lat, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, col); endmap(cr)
    k = ease_out(prog(t, at(key, w0) - 0.2, at(key, w1) + 0.2)); thermo(cr, k, v, col=col)
    if t >= t0 + 0.9: label(cr, place, 540, 620, 70, WHITE)
    if k > 0: label(cr, f'{v * k:.1f}°C', 560, 1000, 130, col, clamp(k * 3))
    return k
def sc_phheat(cr, t, b, t0, t1): heat(cr, t, 'PH', 121.73, 17.61, (121.7, 17.6), 0.48, 1.4, PH_LAND, t0, 'r1a', 'forty', 'degrees', 42.2, 'TUGUEGARAO · 1969', (1, 0.6, 0.4))
def sc_auheat(cr, t, b, t0, t1): heat(cr, t, 'AU', 135.45, -27.55, (135.4, -27.5), 0.2, 0.6, AU_LAND, t0, 'r1b', 'fifty', 'seven', 50.7, 'OODNADATTA · 1960', (1, 0.45, 0.2))
def sc_usheat(cr, t, b, t0, t1):
    k = heat(cr, t, 'US', -116.87, 36.46, (-116.9, 36.5), 0.19, 0.6, US_LAND, t0, 'r1c', 'fifty', 'seven', 56.7, 'DEATH VALLEY · 1913', (1, 0.25, 0.1))
    f = clamp(k) * 0.4; g = cairo.RadialGradient(540, 960, 300, 540, 960, 1100); g.add_color_stop_rgba(0, 1, 0.5, 0.1, 0); g.add_color_stop_rgba(1, 1, 0.35, 0.05, f); cr.set_source(g); cr.paint()
    te = at('r1c', 'hottest') - 0.1
    if t >= te: chip(cr, 'HOTTEST EVER RECORDED ON EARTH', 540, 720, 44, GOLD, INK, pop_k(t, te), 1)
def coast(cr, t, k_, s0, s1, land, col, t0, t1, key, w0, w1, val, sub_):
    cx, cy, s = mview(cr, t, k_, (0, 0), (0, 0), s0, s1, t0, t1 + 1.5, land); k = ease_out(prog(t, at(key, w0) - 0.2, at(key, w1) + 0.3))
    ph = (t * 1.2) % 1; km_shape(cr, G.c[k_], cx, cy, s, col, 0.5 + 0.5 * k, fill=0.0, lw=4 + 4 * k, edge=col, glow=True); endmap(cr)
    label(cr, f'{int(val * k):,} KM', 540, 620, 110, col); ptext(cr, sub_, 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_coast_us(cr, t, b, t0, t1): coast(cr, t, 'US', 0.19, 0.2, US_LAND, US_C, t0, t1, 'r2a', 'twenty', 'coastline', 19924, 'USA COASTLINE (CIA)')
def sc_coast_au(cr, t, b, t0, t1): coast(cr, t, 'AU', 0.2, 0.21, AU_LAND, AU_C, t0, t1, 'r2b', 'over', 'thousand', 25760, 'AUSTRALIA COASTLINE (CIA)')
def sc_coast_ph(cr, t, b, t0, t1):
    coast(cr, t, 'PH', 0.48, 0.5, PH_LAND, PH_C, t0, t1, 'r2c', 'Thirty', 'thousand', 36289, 'PHILIPPINES COASTLINE (CIA)')
    tb = at('r2c', 'Longer') - 0.1
    if t >= tb:
        k = ease_out(prog(t, tb, tb + 0.6))
        for j, (n, v) in enumerate((('USA', 19924), ('Australia', 25760), ('Philippines', 36289))):
            y = 1160 + j * 70; ww = 640 * v / 36289 * k; rrect(cr, 300, y, ww, 46, 23); cr.set_source_rgb(*COLS[n]); cr.fill(); ball(cr, n, 250, y + 23, 30, 'happy', 0, 0)
        chip(cr, 'LONGER THAN BOTH!', 540, 800, 52, GOLD, INK, pop_k(t, tb), 1)
def sc_usanimals(cr, t, b, t0, t1):
    arena(cr, t, US_C); label(cr, 'GRIZZLY BEARS & RATTLESNAKES', 540, 620, 64, US_C); emopops(cr, t, 'r3a', [('🐻', 'grizzly'), ('🐍', 'rattlesnakes')], y=1050, size=240)
def sc_cobra(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.05, 0.15, 0.08); g.add_color_stop_rgb(1, 0.12, 0.3, 0.12); cr.set_source(g); cr.paint()
    emoji(cr, '🐍', 460, 1080 + 10 * math.sin(t * 3), 380 * pop_k(t, t0 + 0.1, 0.4), 1, rot=-0.1)
    ts = at('r3b', 'spit') - 0.1
    if t >= ts:
        for j in range(12): ph = ((t - ts) * 1.5 + j / 12) % 1; cr.new_path(); cr.arc(600 + 420 * ph, 960 - 80 * ph + 160 * ph * ph + (j % 3) * 12, 9 * (1 - ph) + 3, 0, 2 * math.pi); cr.set_source_rgba(0.75, 1, 0.4, 1 - ph); cr.fill()
        chip(cr, 'SPITS VENOM AT YOUR EYES', 540, 720, 46, GOLD, INK, pop_k(t, ts), 1)
    label(cr, 'PHILIPPINE COBRA', 540, 620, 96, PH_C)
def sc_taipan(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.5, 0.22, 0.1); g.add_color_stop_rgb(1, 0.2, 0.08, 0.05); cr.set_source(g); cr.paint()
    emoji(cr, '🐍', 540, 1080 + 10 * math.sin(t * 3), 460 * pop_k(t, t0 + 0.1, 0.4), 1, rot=0.1); tm = at('r3c', 'most') - 0.1
    if t >= tm: emoji(cr, '☠️', 840, 860, 150 * pop_k(t, tm, 0.3), 1); chip(cr, 'MOST VENOMOUS SNAKE ON EARTH', 540, 720, 46, GOLD, INK, pop_k(t, tm), 1)
    label(cr, 'INLAND TAIPAN', 540, 620, 110, AU_C)
def sc_honeysuckle(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 148.98, -35.58)), 0.2, 1.0, t0, t0 + 1.2, AU_LAND)
    x, y = kpt('AU', 148.98, -35.58, cx, cy, s); pin(cr, x, y, t, t0 + 1.0, WHITE); endmap(cr)
    if t >= t0 + 1.0:
        emoji(cr, '📡', x - 40, y - 140, 150 * pop_k(t, t0 + 1.0, 0.3), 1)
        for j in range(4): ph = ((t - t0) * 0.8 + j / 4) % 1; cr.new_path(); cr.arc(x - 40, y - 180, 60 + 400 * ph, -2.4, -0.7); cr.set_source_rgba(1, 1, 1, 0.7 * (1 - ph)); cr.set_line_width(6); cr.stroke()
    label(cr, 'APOLLO 11 · JULY 1969', 540, 620, 84, AU_C); ptext(cr, 'HONEYSUCKLE CREEK & PARKES DISHES', 540, 700, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_diwata(cr, t, b, t0, t1):
    cr.set_source_rgb(0.01, 0.01, 0.05); cr.paint(); rng = np.random.default_rng(2)
    for _ in range(140): x, y, s_ = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.4); cr.new_path(); cr.arc(x, y, s_, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.5); cr.fill()
    emoji(cr, '🌏', 540, 1080, 420, 1); a = (t - t0) * 1.2; emoji(cr, '🛰️', 540 + 330 * math.cos(a), 1080 + 120 * math.sin(a), 110, 1, rot=0.3)
    label(cr, 'DIWATA-1 · 2016', 540, 620, 100, PH_C); ptext(cr, "THE PHILIPPINES' FIRST MICROSATELLITE", 540, 700, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def moon(cr, t):
    cr.set_source_rgb(0.01, 0.01, 0.05); cr.paint(); rng = np.random.default_rng(2)
    for _ in range(160): x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.6); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.4 + 0.4 * math.sin(t * 2 + x)); cr.fill()
    cr.new_path(); cr.arc(540, 2350, 1250, 0, 2 * math.pi); cr.set_source_rgb(0.62, 0.62, 0.66); cr.fill()
    for x, y, r in ((200, 1290, 60), (640, 1350, 90), (950, 1300, 50), (420, 1500, 70), (820, 1560, 110)):
        cr.save(); cr.translate(x, y); cr.scale(1, 0.35); cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(0.5, 0.5, 0.55); cr.fill()
    emoji(cr, '🌍', 860, 820, 140, 1)
def sc_apollo(cr, t, b, t0, t1):
    moon(cr, t); k = prog(t, at('r4c', 'twelve') - 0.2, at('r4c', 'Moon') + 0.3)
    for j in range(int(12 * k + 0.999)):
        x = 130 + (j % 6) * 165; y = 960 + (j // 6) * 190 - abs(math.sin(t * 3 + j)) * 10; kk = pop_k(t, at('r4c', 'twelve') - 0.2 + j * 0.08)
        cr.save(); cr.translate(x, y); cr.scale(kk, kk)
        rrect(cr, -34, -10, 68, 90, 24); cr.set_source_rgb(0.95, 0.95, 0.97); cr.fill(); cr.new_path(); cr.arc(0, -40, 36, 0, 2 * math.pi); cr.fill()
        rrect(cr, -24, -58, 48, 32, 14); cr.set_source_rgb(0.85, 0.65, 0.2); cr.fill(); rrect(cr, -14, 14, 28, 22, 4); cr.set_source_rgb(*US_C); cr.fill(); cr.restore()
    label(cr, f'{int(12 * clamp(k))} MOONWALKERS', 540, 620, 96, US_C); ptext(cr, 'APOLLO 11–17 · 1969–1972', 540, 700, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def food_bg(cr, t, col):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.2, 0.06, 0.06); g.add_color_stop_rgb(1, 0.45, 0.2, 0.08); cr.set_source(g); cr.paint()
    for j in range(14):  # checkered tablecloth
        for i in range(10):
            if (i + j) % 2: cr.rectangle(i * 110, 1250 + j * 60, 110, 60); cr.set_source_rgba(*col, 0.35); cr.fill()
def sc_pies(cr, t, b, t0, t1):
    food_bg(cr, t, AU_C); k = ease_out(prog(t, t0, at('r5a', 'meat') + 0.3))
    for j in range(int(24 * k)): emoji(cr, '🥧', 160 + (j % 6) * 152, 880 + (j // 6) * 120 - abs(math.sin(t * 4 + j)) * 8, 100, 1)
    label(cr, f'{int(270 * k)} MILLION PIES', 540, 620, 90, AU_C); ptext(cr, 'EVERY YEAR · ~12 PER AUSSIE', 540, 700, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_mcd(cr, t, b, t0, t1):
    food_bg(cr, t, US_C); k = ease_out(prog(t, t0, at('r5b', 'thousand') + 0.3))
    emoji(cr, '🍔', 380, 1050 + 10 * math.sin(t * 3), 300 * pop_k(t, t0 + 0.1, 0.4), 1, rot=-0.08); emoji(cr, '🍟', 760, 1060 + 10 * math.sin(t * 3 + 1), 240 * pop_k(t, t0 + 0.3, 0.4), 1, rot=0.1)
    label(cr, f'{int(40 * k)},000+ RESTAURANTS', 540, 620, 80, US_C); ptext(cr, "McDONALD'S · ABOUT 100 COUNTRIES", 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_jollibee(cr, t, b, t0, t1):
    food_bg(cr, t, PH_C)
    emoji(cr, '🐝', 300, 980 + 30 * math.sin(t * 5), 220 * pop_k(t, t0 + 0.1, 0.4), 1, rot=0.2 * math.sin(t * 4)); emoji(cr, '🍗', 700, 1060, 260 * pop_k(t, t0 + 0.3, 0.4), 1, rot=-0.1)
    emoji(cr, '🍚', 760, 1250, 160 * pop_k(t, t0 + 0.5, 0.4), 1)
    label(cr, 'JOLLIBEE', 540, 600, 130, PH_C); ptext(cr, '#1 FAST FOOD CHAIN IN THE PHILIPPINES', 540, 690, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tb = at('r5c', 'beats') - 0.1
    if t >= tb: chip(cr, "MORE STORES THAN McDONALD'S IN THE PH", 540, 790, 42, GOLD, INK, pop_k(t, tb), 1)
FLA = [(-80.1, 26.7), (-80.1, 25.9), (-80.2, 25.4), (-80.4, 25.1), (-80.7, 24.9), (-81.0, 24.7), (-81.5, 24.55), (-81.9, 24.5), (-82.3, 24.55)]
def sc_florida(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'US', (0, 0), tuple(G.p('US', -81.3, 26.0)), 0.19, 1.3, t0, t0 + 1.2, US_LAND)
    k = ease_io(prog(t, t0 + 0.9, at('r6a', 'reef') + 0.3)); pts = [kpt('US', lon, lat, cx, cy, s) for lon, lat in FLA]; rng = np.random.default_rng(4)
    for j in range(int(200 * k)):
        f = j / 200; i = min(len(pts) - 2, int(f * (len(pts) - 1))); u = f * (len(pts) - 1) - i
        cr.new_path(); cr.arc(lerp(pts[i][0], pts[i + 1][0], u) + rng.normal(0, 10), lerp(pts[i][1], pts[i + 1][1], u) + rng.normal(0, 10), rng.uniform(2.5, 5), 0, 2 * math.pi); cr.set_source_rgba(0.35, 1, 0.92, 0.85); cr.fill()
    endmap(cr); label(cr, 'FLORIDA REEF', 540, 620, 110, US_C); ptext(cr, '3RD BIGGEST BARRIER REEF ON EARTH', 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_tubbataha(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'PH', (0, 0), tuple(G.p('PH', 119.9, 8.9)), 0.48, 1.4, t0, t0 + 1.1, PH_LAND)
    x, y = kpt('PH', 119.9, 8.9, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (0.4, 1, 0.9))
    for j in range(8):
        a = j / 8 * 2 * math.pi; tj = t0 + 1.0 + j * 0.06
        if t >= tj: emoji(cr, '🪸' if j % 2 else '🐠', x + 190 * math.cos(a), y + 130 * math.sin(a), 70 * pop_k(t, tj), 1)
    endmap(cr); label(cr, 'TUBBATAHA REEF', 540, 620, 90, PH_C); ptext(cr, 'UNESCO WORLD HERITAGE SITE', 540, 700, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
REEF = [(143.4, -11.2), (143.9, -13.3), (145.0, -14.8), (145.9, -16.4), (147.0, -18.0), (148.6, -19.4), (150.0, -20.4), (151.3, -21.5), (152.3, -22.8), (152.9, -24.0)]
def sc_reef(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 147.5, -18.0)), 0.2, 0.5, t0, t0 + 1.3, AU_LAND, rot=-0.03)
    k = ease_io(prog(t, t0 + 0.8, at('r6c', 'biggest') + 0.2)); pts = [kpt('AU', lon, lat, cx, cy, s) for lon, lat in REEF]
    rng = np.random.default_rng(3); n = int(420 * k)
    for j in range(n):
        f = j / 420; i = min(len(pts) - 2, int(f * (len(pts) - 1))); u = f * (len(pts) - 1) - i
        cr.new_path(); cr.arc(lerp(pts[i][0], pts[i + 1][0], u) + rng.normal(0, 14), lerp(pts[i][1], pts[i + 1][1], u) + rng.normal(0, 14), rng.uniform(2.5, 6), 0, 2 * math.pi); cr.set_source_rgba(0.35, 1.0, 0.92, 0.85); cr.fill()
    endmap(cr); label(cr, f'{int(2300 * k):,} KM', 540, 620, 110, (0.45, 1, 0.93)); ptext(cr, 'THE GREAT BARRIER REEF', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tb = at('r6c', 'biggest') - 0.1
    if t >= tb: chip(cr, 'BIGGEST CORAL REEF ON EARTH', 540, 800, 44, GOLD, INK, pop_k(t, tb), 1)
SCENE = {'phheat': sc_phheat, 'auheat': sc_auheat, 'usheat': sc_usheat, 'coast_us': sc_coast_us, 'coast_au': sc_coast_au, 'coast_ph': sc_coast_ph, 'usanimals': sc_usanimals,
         'cobra': sc_cobra, 'taipan': sc_taipan, 'honeysuckle': sc_honeysuckle, 'diwata': sc_diwata, 'apollo': sc_apollo, 'pies': sc_pies, 'mcd': sc_mcd, 'jollibee': sc_jollibee,
         'florida': sc_florida, 'tubbataha': sc_tubbataha, 'reef': sc_reef}

# ---------- hook: the food fight ----------
FOOD = {'USA': '🍔', 'Australia': '🥧', 'Philippines': '🍗'}
def throw(cr, t, ts, frm, to, em, y0=1250, dur=0.55):
    """A food item arcs from one ball to another and splats."""
    if t < ts: return
    k = prog(t, ts, ts + dur); x0, x1 = POSX[frm], POSX[to]
    if k < 1: x = lerp(x0, x1, k); y = y0 - 420 * math.sin(math.pi * k); emoji(cr, em, x, y, 160, 1, rot=k * 9); return
    f = 1 - prog(t, ts + dur, ts + dur + 0.6)
    if f > 0:
        rng = np.random.default_rng(int(ts * 100))
        for j in range(9): a = rng.uniform(0, 6.28); r = 40 + 120 * (1 - f); cr.new_path(); cr.arc(x1 + r * 1.4 * math.cos(a), y0 + r * 1.4 * math.sin(a) * 0.7, 28 * f + 6, 0, 6.28); cr.set_source_rgba(0.95, 0.7, 0.25, f); cr.fill()
def draw_hook(cr, t):
    if t >= bt('title')['start']: return False
    b1, b2, b3, b4 = bt('h1'), bt('h2'), bt('h3'), bt('h4')
    for b, nm, mood, shot in ((b1, 'USA', 'angry', sh_close), (b2, 'Australia', 'angry', sh_low), (b3, 'Philippines', 'angry', sh_close)):
        if b['start'] <= t < b['end'] and t < b4['start']:
            sx, sy = shake(t, b['start'] + 0.05, 16, 0.3); cr.save(); cr.translate(sx, sy); shot(cr, t, b, nm, b['start'], b['end'], mood); cr.restore()
            em = FOOD[nm]; emoji(cr, em, 860, 820 + 10 * math.sin(t * 6), 170 * pop_k(t, b['l0'], 0.3), 1, rot=0.15 * math.sin(t * 5))
            if nm == 'Philippines': emoji(cr, '🍚', 730, 900, 110 * pop_k(t, b['l0'] + 0.2, 0.3), 1)
            streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.2)))
            return True
    t0 = b4['start']
    cr.save(); cam(cr, push(t, t0, b4['end'] + 0.6, 1.08, 1.0), 0, 540, 1150); arena(cr, t)
    for n in TEAMS:
        hit = [ts + 0.55 for ts, fr, to in FIGHT if to == n and t >= ts + 0.55]; sq = 0.2 * math.exp(-(t - max(hit)) * 8) if hit else 0
        ball(cr, n, POSX[n], 1250, 178, 'shock' if hit and t - max(hit) < 0.5 else 'angry', sq, (540 - POSX[n]) / 500)
    for ts, fr, to in FIGHT: throw(cr, t, ts, fr, to, FOOD[fr])
    cr.restore()
    for n in TEAMS: nametag(cr, n, POSX[n], 1460, col_of(n))
    tf = w('h4', 'food') - 0.1
    if t >= tf: sx, sy = shake(t, tf, 18); cr.save(); cr.translate(sx, sy); slam(cr, 'FOOD FIGHT!', 540, 560, 150, GOLD, t, tf); cr.restore()
    tw_ = w('h4', 'Who') - 0.1
    if t >= tw_: slam(cr, 'WHO WINS?', 540, 760, 110, WHITE, t, tw_)
    C.draw_captions(cr, t, 1700)
    f = 1 - prog(t, t0, t0 + 0.15)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, t0, t0 + 0.2)))
    return True
FIGHT = []
def build_fight():
    t0 = bt('h4')['start']; FIGHT.clear()
    for j, (fr, to) in enumerate((('USA', 'Australia'), ('Australia', 'USA'), ('Philippines', 'USA'), ('Philippines', 'Australia'), ('USA', 'Philippines'), ('Australia', 'Philippines'))):
        FIGHT.append((t0 + 0.15 + j * 0.32, fr, to))
def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.08), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.5))
    for n in TEAMS: ball(cr, n, POSX[n], lerp(2300, 1450, e) - abs(math.sin(t * 6 + POSX[n])) * 14, 150, 'angry', 0, (540 - POSX[n]) / 500)
    cr.restore()
    slam(cr, 'USA', 540, 460, 150, US_C, t, w('title', 'Six'))
    slam(cr, 'PHILIPPINES', 540, 640, 130, PH_C, t, w('title', 'Three'))
    slam(cr, 'AUSTRALIA', 540, 810, 130, AU_C, t, w('title', 'champion'))
    tg = w('title', 'triple')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE TRIPLE THREAT', 540, 1000, 100, WHITE, t, tg); cr.restore()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22)))

# ---------- scoreboard, cards, verdicts ----------
def tv_of(i): return w(*RD[i][2])
def score_at(t): return {n: sum(t >= tv_of(i) and RD[i][1] == n for i in RD) for n in TEAMS}
def round_of(t):
    for i in RD:
        nxt = bt(f'c{i + 1}')['start'] if i < NR else bt('e1')['start']
        if bt(f'c{i}')['start'] <= t < nxt: return i
    return None
def hud(cr, t):
    a = ease_out(prog(t, bt('title')['end'] - 0.4, bt('title')['end']))
    if a <= 0: return
    sc = score_at(t); rrect(cr, 30, 140, 1020, 190, 44); cr.set_source_rgba(0.03, 0.04, 0.1, 0.88 * a); cr.fill()
    for n, x in zip(TEAMS, (190, 540, 890)):
        ptext(cr, n.upper(), x, 200, 38, COLS[n], a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == n and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc[n]), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = f'ROUND {i}/6' if i else ('FINAL: 2 — 2 — 2' if t >= bt('e1')['start'] else '')
    if lab and t < bt('cta')['start']: chip(cr, lab, 540, 370, 30, GOLD, INK, a, 1)
ICON = {1: '🔥', 2: '🏖️', 3: '🐍', 4: '🚀', 5: '🍔', 6: '🪸'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, n in enumerate(TEAMS): cr.new_path(); cr.move_to(-200 + j * 500, 2200); cr.line_to(540, 960); cr.line_to(-200 + (j + 1) * 500, 2200); cr.close_path(); cr.set_source_rgba(*COLS[n], 0.3); cr.fill()
    head = 'FINAL ROUND' if i == NR else f'ROUND {i}'
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, head, 0, 0, 120 if i == NR else 150, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = COLS[win]; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); txt = win.upper() + ' WINS'
    cr.save(); cr.translate(540, 1450); cr.rotate(-0.04); cr.scale(s, s); sz = fit(cr, txt, 72, 820); wd = tw(cr, txt, sz)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, sz, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- ending ----------
def subscribe_button(cr, t, t0, x, y):
    """A subscribe button that a hand pointer clicks: it flips to SUBSCRIBED and the bell rings."""
    tc = t0 + 1.3; clicked = t >= tc; k = pop_k(t, t0, 0.3)
    press = 1 - 0.12 * math.sin(math.pi * clamp((t - tc + 0.08) / 0.16)) if abs(t - tc) < 0.1 else 1.0
    pulse = 1 + (0.04 * math.sin(t * 7) if not clicked else 0)
    cr.save(); cr.translate(x, y); cr.scale(k * press * pulse, k * press * pulse)
    txt = 'SUBSCRIBED' if clicked else 'SUBSCRIBE'; tw_ = tw(cr, txt, 60); bw = tw_ + (150 if clicked else 110); bx = -60
    rrect(cr, bx - bw / 2, -66, bw, 116, 58); cr.set_source_rgb(*((0.32, 0.32, 0.36) if clicked else (0.9, 0.08, 0.12))); cr.fill()
    if clicked:
        cx_ = bx - tw_ / 2 - 30; cr.new_path(); cr.move_to(cx_ - 20, -12); cr.line_to(cx_ - 4, 6); cr.line_to(cx_ + 22, -26); cr.set_source_rgb(1, 1, 1); cr.set_line_width(9); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
        ptext(cr, txt, bx + 20, 10, 60, WHITE, 1, sw=0, shadow=False)
    else: ptext(cr, txt, bx, 10, 60, WHITE, 1, sw=0, shadow=False)
    cr.restore()
    ring = 0.5 * math.sin((t - tc) * 30) * math.exp(-(t - tc) * 3) if clicked else 0
    cr.new_path(); cr.arc(x + 230, y - 8, 58 * k, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.95); cr.fill()
    emoji(cr, '🔔', x + 230, y - 8, 76 * k, 1, rot=ring)
    if clicked:
        for j in range(10):
            a = j / 10 * 2 * math.pi; r = 80 + 300 * ease_out(prog(t, tc, tc + 0.6)); f = 1 - prog(t, tc, tc + 0.7)
            if f > 0: cr.new_path(); cr.arc(x + r * math.cos(a), y + r * math.sin(a) * 0.6, 10, 0, 2 * math.pi); cr.set_source_rgba(*(GOLD[:3] if j % 2 else (1, 1, 1)), f); cr.fill()
    if t < tc + 0.5:
        hx = lerp(x + 420, x - 20, ease_out(prog(t, t0 + 0.2, tc))); hy = lerp(y + 300, y + 60, ease_out(prog(t, t0 + 0.2, tc)))
        emoji(cr, '👆', hx, hy, 120, clamp((tc + 0.5 - t) * 4))
def draw_end(cr, t):
    e1, e2, e3, c = bt('e1'), bt('e2'), bt('e3'), bt('cta')
    if t < c['start']:
        for b, n, mood in ((e1, 'Australia', 'shock'), (e2, 'Philippines', 'happy'), (e3, 'USA', 'angry')):
            if b['start'] <= t < (b['end'] if b is not e3 else c['start']):
                h = hop_of(t, b); sx, sy = shake(t, b['l0'], 16, 0.4) if b is e1 else (0, 0)
                cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.12), 0.04 * sgn_of(n), 540 + sx, 1100 + sy); set_of(n, cr, t); ball(cr, n, 540, 1270 - h * 40, 290, mood, 0.05 * h, 0); cr.restore()
                bubble(cr, t, b, 540, 540); nametag(cr, n, 540, 1640, col_of(n))
                if b is e1: ptext(cr, '2 — 2 — 2', 540, 830, 110, WHITE, pop_k(t, e1['start'] + 0.1), sw=14)
                if b is e2: emoji(cr, '🙏', 200, 900, 140 * pop_k(t, e2['l0'] + 0.3), 1)
                if b is e3: emoji(cr, '📢', 860, 900, 150 * pop_k(t, e3['l0'] + 0.3), 1, rot=-0.2)
                return
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.06), 0.02, 540, 1000); arena(cr, t)
    for n in TEAMS: ball(cr, n, POSX[n], 1290 - abs(math.sin(t * 5 + POSX[n])) * 10, 140, 'angry', 0, (540 - POSX[n]) / 500)
    cr.restore()
    sx, sy = shake(t, c['start'], 16, 0.4); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A 3-WAY TIE!", 540, 470, 112, GOLD, t, c['start']); cr.restore()
    ptext(cr, '2 — 2 — 2', 540, 600, 84, WHITE, 1, sw=10)
    tp = w('cta', 'pick') - 0.1
    if t >= tp:
        kk = pop_k(t, tp); cr.save(); cr.translate(540, 730); cr.scale(kk, kk); ptext(cr, 'YOU PICK THE TIEBREAKER', 0, 0, 66, WHITE, 1, sw=9); cr.restore()
        for j, (em, lab) in enumerate((('🏀', 'BASKETBALL?'), ('🍳', 'BREAKFAST?'), ('🎤', 'KARAOKE?'))):
            tj = tp + 0.4 + j * 0.25
            if t < tj: continue
            x = 220 + j * 320; k2 = pop_k(t, tj); emoji(cr, em, x, 880 + 8 * math.sin(t * 4 + j), 120 * k2, 1); ptext(cr, lab, x, 1010, 40, GOLD, k2, fam='Poppins ExtraBold', sw=6)
    tc = w('cta', 'Comment') - 0.1
    if t >= tc: chip(cr, 'COMMENT THE TIEBREAKER', 540, 1460, 46, WHITE, INK, pop_k(t, tc), 1)
    ts_ = w('cta', 'subscribe') - 0.1
    if t >= ts_: subscribe_button(cr, t, ts_, 540, 1640)

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if draw_hook(cr, t): return
    if key == 'title': draw_title(cr, t); return
    if key in ('e1', 'e2', 'e3', 'cta'): draw_end(cr, t); hud(cr, t)
    elif key[0] == 'c': card(cr, t, int(key[1])); hud(cr, t); None
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
    for k_ in ('h1', 'h2', 'h3'): whoosh(bt(k_)['start'] - 0.2, 0.3, 0.3); boom(bt(k_)['start'] + 0.05, 0.8)
    whoosh(bt('h4')['start'] - 0.3, 0.3)
    for ts, fr, to in FIGHT: whoosh(ts, 0.2, 0.45); pop(ts + 0.55, 0.16, 300 + 80 * TEAMS.index(to)); boom(ts + 0.55, 0.35)
    boom(w('h4', 'food') - 0.1, 1.0); boom(w('h4', 'Who') - 0.1, 0.8); whoosh(bt('title')['start'] - 0.35)
    for wd in ('Six', 'Three', 'champion', 'triple'): boom(w('title', wd), 0.7)
    horn(w('title', 'triple'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, {'USA': 1568, 'Philippines': 1319, 'Australia': 1760}[RD[i][1]]); cheer(tv + 0.1); pop(tv + 0.55, 0.12, 500)
    for k, sp, _ in LINES:
        if sp and k[0] == 'r': whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
        if k in SHOTS:
            for s0, sh in shot_list(k)[1:]: whoosh(s0 - 0.2, 0.16, 0.22)
    boom(bt('e3')['start'], 0.6); boom(bt('e1')['start'], 0.9); rumble(bt('e1')['start'], 1.0, 0.2); boom(bt('cta')['start'], 0.9); horn(bt('cta')['start'], 0.1)
    for j in range(3): pop(w('cta', 'pick') + 0.3 + j * 0.25, 0.12, 900 + 200 * j)
    tsc = w('cta', 'subscribe') - 0.1 + 1.3; pop(tsc, 0.18, 1800); bell(tsc + 0.05, 0.16, 1568); bell(tsc + 0.25, 0.12, 2093); cheer(tsc + 0.1, 0.1, 1.4)
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
    C.TL = C.build(MultiVoice(cache)); G = Geo(data_dir); build_fight()

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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_trio'))
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

