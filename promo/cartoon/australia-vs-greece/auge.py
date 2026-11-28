# Countryballs: Australia vs Greece, the Geography War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (islands, Olympus, olive oil, Melbourne's Greeks...).
# Usage: python3 auge.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

A_C, U_C = hexc('#FFC233')[:3], hexc('#2F80FF')[:3]   # Australia gold, Greece blue
AU_C, GR_C = A_C, U_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Australia': ('en-AU-WilliamNeural', '+4%'), 'Greece': ('el-GR-NestorasNeural', '+4%')}
LINES = [
    ('h1', 'Greece', "Australia, you're just one giant empty island!"),
    ('h2', 'Australia', "And you're mostly islands, mate!"),
    ('h3', None, "Greece fits inside Australia fifty-eight times. But over four hundred thousand Australians have Greek roots."),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: size."),
    ('r1a', 'Greece', "I may be small, but I am beautiful!"),
    ('r1b', 'Australia', "Cute. I'm fifty-eight times bigger than you, mate!"),
    ('c2', None, "Round two: mountains."),
    ('r2a', 'Australia', "Mount Kosciuszko: two thousand two hundred metres!"),
    ('r2b', 'Greece', "Mount Olympus: almost two thousand nine hundred. Home of the gods!"),
    ('c3', None, "Round three: islands."),
    ('r3a', 'Greece', "I have six thousand islands!"),
    ('r3b', 'Australia', "Cute. I have eight thousand two hundred and twenty-two!"),
    ('c4', None, "Round four: tourists."),
    ('r4a', 'Australia', "Nine million tourists visit me every year!"),
    ('r4b', 'Greece', "Thirty-eight million visit me. That's almost four tourists for every Greek!"),
    ('c5', None, "Round five: heat."),
    ('r5a', 'Greece', "Athens once hit forty-eight degrees!"),
    ('r5b', 'Australia', "Cute. I've hit fifty point seven. Pack sunscreen, mate!"),
    ('c6', None, "Round six: olive oil."),
    ('r6a', 'Australia', "We grow olives too!"),
    ('r6b', 'Greece', "Greeks use more olive oil per person than almost anyone on Earth. We put it on everything!"),
    ('c7', None, "Round seven: sheep."),
    ('r7a', 'Greece', "My sheep make the best feta!"),
    ('r7b', 'Australia', "Nice. I have seventy-four million sheep. About ten times more than you!"),
    ('c8', None, "Round eight: the Olympics."),
    ('r8a', 'Australia', "I've hosted the Olympics twice, and Brisbane makes three!"),
    ('r8b', 'Greece', "Cute. I invented them. Twenty-eight centuries ago."),
    ('c9', None, "Four all. Tiebreaker: who has more Greeks?"),
    ('r9a', 'Australia', "Easy! Melbourne has one of the biggest Greek communities outside Greece!"),
    ('r9b', 'Greece', "Outside Greece, mate. I AM Greece. Ten million Greeks!"),
    ('e1', 'Australia', "Fair enough... Opa?"),
    ('e2', 'Greece', "Opa! Come for dinner, cousin!"),
    ('cta', None, "Australia, or Greece? Comment your side, and follow for the next battle.")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SIZE', 'A', ('r1b', 'bigger')), 2: ('MOUNTAINS', 'U', ('r2b', 'gods')), 3: ('ISLANDS', 'A', ('r3b', 'twenty')), 4: ('TOURISTS', 'U', ('r4b', 'Greek')),
      5: ('HEAT', 'A', ('r5b', 'sunscreen')), 6: ('OLIVE OIL', 'U', ('r6b', 'everything')), 7: ('SHEEP', 'A', ('r7b', 'more')), 8: ('THE OLYMPICS', 'U', ('r8b', 'centuries')),
      9: ('WHO HAS MORE GREEKS?', 'U', ('r9b', 'Ten'))}
NR = 9
SHOTS = {
    'r1a': [(None, 'two'), ('beautiful', 'map:santorini')], 'r1b': [(None, 'close'), ('fifty', 'map:size')],
    'r2a': [(None, 'low'), ('Kosciuszko', 'map:kosci')], 'r2b': [(None, 'ots'), ('Olympus', 'map:olympus')],
    'r3a': [(None, 'close'), ('six', 'map:grislands')], 'r3b': [(None, 'two'), ('eight', 'map:auislands')],
    'r4a': [(None, 'low'), ('Nine', 'map:autour')], 'r4b': [(None, 'ots'), ('Thirty', 'map:grtour')],
    'r5a': [(None, 'two'), ('Athens', 'map:grheat')], 'r5b': [(None, 'low'), ('fifty', 'map:auheat')],
    'r6a': [(None, 'close'), ('olives', 'two')], 'r6b': [(None, 'ots'), ('olive', 'map:oil')],
    'r7a': [(None, 'two'), ('sheep', 'map:feta')], 'r7b': [(None, 'low'), ('seventy', 'map:sheep')],
    'r8a': [(None, 'close'), ('twice', 'map:auolympics')], 'r8b': [(None, 'two'), ('invented', 'map:olympia')],
    'r9a': [(None, 'close'), ('Melbourne', 'map:melbourne')], 'r9b': [(None, 'low'), ('Ten', 'map:greeks')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {'Kosciuszko': 'Kozzy-osko'}}
C.HOT = ('australia', 'greece', 'greek', 'roots', 'war', 'tiebreaker', 'comment', 'winner', 'islands', 'fifty-eight', 'thousand')
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
        self.ref = {'AU': (134.0, -26.0), 'GR': (23.5, 38.5)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('AU', 'Australia', ['Indonesia', 'Papua New Guinea', 'New Zealand', 'Timor-Leste']),
                          ('GR', 'Greece', ['Turkey', 'Albania', 'North Macedonia', 'Bulgaria', 'Italy', 'Cyprus', 'Serbia', 'Kosovo', 'Montenegro', 'Libya', 'Egypt'])):
            rs = R(n)
            if k == 'AU': rs = [r for r in rs if 112 < r[:, 0].mean() < 155 and -45 < r[:, 1].mean() < -9]
            pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs if nn in cf for r in local(R(nn), *self.ref[k])]
        self.gr_true = [r - np.concatenate(self.c['GR']).mean(axis=0) for r in self.c['GR']]
        print('areas M km2: australia', round(area(self.c['AU']) / 1e6, 2), 'greece', round(area(self.c['GR']) / 1e6, 3), 'ratio', round(area(self.c['AU']) / area(self.c['GR']), 1))
        B.FL['Australia'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'au.png')); B.FL['Greece'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'gr.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'Australia' else 'U'
def col_of(name): return AU_C if name == 'Australia' else GR_C
def rival_of(name): return 'Greece' if name == 'Australia' else 'Australia'
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
def set_greece(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.45, 0.72, 0.98); g.add_color_stop_rgb(0.5, 0.98, 0.82, 0.7); g.add_color_stop_rgb(0.62, 0.2, 0.5, 0.85); g.add_color_stop_rgb(1, 0.08, 0.28, 0.6); cr.set_source(g); cr.paint()
    cr.new_path(); cr.arc(250, 900, 120, 0, 2 * math.pi); cr.set_source_rgba(1, 0.92, 0.75, 0.9); cr.fill()
    for j in range(16):
        y = 1210 + j * 28; ph = (t * 0.4 + j * 0.37) % 1; cr.rectangle(80 + 400 * math.sin(j * 1.9) + 80 * ph, y, 150, 4); cr.set_source_rgba(1, 1, 1, 0.3); cr.fill()
    cr.new_path(); cr.move_to(380, 1200); cr.curve_to(560, 900, 900, 860, 1300, 900); cr.line_to(1300, 1400); cr.line_to(380, 1400); cr.close_path(); cr.set_source_rgb(0.62, 0.5, 0.4); cr.fill()
    rng = np.random.default_rng(6)
    for j in range(16):
        x = 520 + rng.uniform(0, 640); y = 1000 + (x - 520) * -0.05 + rng.uniform(0, 260); w_, h_ = rng.uniform(70, 120), rng.uniform(50, 90)
        cr.rectangle(x, y, w_, h_); cr.set_source_rgb(0.97, 0.97, 0.95); cr.fill(); cr.rectangle(x + w_ * 0.35, y + h_ * 0.4, w_ * 0.25, h_ * 0.6); cr.set_source_rgb(0.15, 0.4, 0.8); cr.fill()
        if j % 4 == 0: cr.new_path(); cr.arc(x + w_ / 2, y, w_ * 0.32, math.pi, 2 * math.pi); cr.close_path(); cr.set_source_rgb(0.1, 0.38, 0.85); cr.fill()
    cr.rectangle(-200, 1400, 1500, 700); cr.set_source_rgb(0.95, 0.93, 0.88); cr.fill()
    for j in range(6): cr.new_path(); cr.arc(120 + j * 190, 1470, 18, 0, 2 * math.pi); cr.set_source_rgba(0.5, 0.6, 0.3, 0.7); cr.fill()
def set_of(name, cr, t): (set_australia if name == 'Australia' else set_greece)(cr, t)

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
    for n, x in (('Australia', 290), ('Greece', 790)):
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
AU_LAND, GR_LAND = (0.86, 0.5, 0.24), (0.92, 0.94, 0.97)
def sc_santorini(cr, t, b, t0, t1):
    set_greece(cr, t); cr.save(); cam(cr, push(t, t0, t1 + 1, 1.0, 1.12), 0.02, 700, 1100); set_greece(cr, t); cr.restore(); label(cr, 'SANTORINI', 540, 620, 110, GR_C)
def sc_size(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, -100), 0.2, 0.22, t0, t1 + 1.5, AU_LAND)
    k = ease_out(prog(t, t0, t0 + 0.5)); cr.save(); cr.translate(0, (1 - k) * -900); km_shape(cr, G.gr_true, cx, cy, s, GR_LAND, 1, 300, 300, fill=0.95, lw=2, edge=INK); cr.restore()
    if k >= 1: chip(cr, 'GREECE', cx + 300 * s, cy - 300 * s + 120, 30, WHITE, INK, 1, 1)
    endmap(cr)
    tx = at('r1b', 'fifty') + 0.4
    if t >= tx: sx, sy = shake(t, tx, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'AUSTRALIA = 58 GREECES', 540, 640, 80, WHITE, t, tx); cr.restore()
def peak(cr, x, base, metres, k, col, name):
    h = 0.17 * metres * k
    if h < 4: return
    wd = 420; cr.new_path(); cr.move_to(x - wd / 2, base); cr.line_to(x - wd * 0.12, base - h * 0.72); cr.line_to(x, base - h); cr.line_to(x + wd * 0.16, base - h * 0.66); cr.line_to(x + wd / 2, base); cr.close_path()
    cr.set_source_rgb(*[c * 0.6 for c in col]); cr.fill_preserve(); cr.set_source_rgb(0.03, 0.04, 0.1); cr.set_line_width(5); cr.stroke()
    cr.new_path(); cr.move_to(x - wd * 0.1, base - h * 0.78); cr.line_to(x, base - h); cr.line_to(x + wd * 0.12, base - h * 0.76); cr.close_path(); cr.set_source_rgb(0.97, 0.98, 1); cr.fill()
    ptext(cr, name, x, base - h * 0.32, 36, WHITE, 1, sw=6); ptext(cr, f'{int(metres * k):,} M', x, base - h * 0.32 + 46, 40, GOLD, 1, sw=6)
def sc_kosci(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'HIGHEST MOUNTAIN', 540, 620, 70, WHITE)
    k = ease_io(prog(t, t0, at('r2a', 'metres') + 0.2)); peak(cr, 330, 1350, 2228, k, AU_C, 'KOSCIUSZKO')
def sc_olympus(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'HIGHEST MOUNTAIN', 540, 620, 70, WHITE); peak(cr, 330, 1350, 2228, 1, AU_C, 'KOSCIUSZKO')
    k = ease_io(prog(t, t0, at('r2b', 'hundred') + 0.2)); peak(cr, 750, 1350, 2918, k, GR_C, 'OLYMPUS')
    tg = at('r2b', 'gods') - 0.1
    if t >= tg: emoji(cr, '⚡', 750, 1350 - 0.17 * 2918 - 90, 140 * pop_k(t, tg), 1, rot=0.3); chip(cr, 'HOME OF THE GODS', 540, 760, 44, GOLD, INK, pop_k(t, tg), 1)
def islands(cr, t, rs, cx, cy, s, col, k):
    for j, r in enumerate(sorted(rs, key=len)[:int(len(rs) * k)]):
        ph = (t * 1.5 + j * 0.13) % 1; km_shape(cr, [r], cx, cy, s, col, 0.6 * (1 - ph), lw=3, edge=col, glow=True)
def sc_grislands(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'GR', (0, 0), (60, -60), 1.4, 1.6, t0, t1 + 1.5, GR_LAND); islands(cr, t, G.c['GR'], cx, cy, s, GOLD[:3], 1); endmap(cr)
    k = ease_out(prog(t, t0, t0 + 0.8)); label(cr, f'~{int(6000 * k):,} ISLANDS', 540, 620, 100, GR_C); ptext(cr, '~227 INHABITED', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_auislands(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, -50), 0.2, 0.22, t0, t1 + 1.5, AU_LAND); k = ease_out(prog(t, t0, at('r3b', 'twenty') + 0.3))
    small = [r for r in G.c['AU'] if len(r) < max(len(x) for x in G.c['AU'])]; islands(cr, t, small, cx, cy, s, GOLD[:3], k)
    rng = np.random.default_rng(21); ring_ = max(G.c['AU'], key=len); idx = rng.choice(len(ring_), 160)
    for j, i_ in enumerate(idx[:int(160 * k)]):
        p = ring_[i_] * 1.0 + rng.normal(0, 40, 2); ph = (t * 1.2 + j * 0.11) % 1
        cr.new_path(); cr.arc(cx + p[0] * s, cy - p[1] * s, 5 + 3 * (1 - ph), 0, 2 * math.pi); cr.set_source_rgba(1, 0.92, 0.4, 0.95); cr.fill()
    endmap(cr)
    label(cr, f'{int(8222 * k):,} ISLANDS', 540, 620, 104, AU_C); ptext(cr, 'INCLUDING EXTERNAL TERRITORIES', 540, 700, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
def planes(cr, t, t0, px, py, n=10):
    for j in range(n):
        a = j / n * 2 * math.pi; ph = ((t - t0) * 0.6 + j * 0.37) % 1; R = lerp(700, 40, ph); emoji(cr, '✈️', px + R * math.cos(a), py + R * math.sin(a), 60, 1 - ph * 0.6, rot=a + math.pi)
def sc_autour(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (300, -400), 0.2, 0.24, t0, t1 + 1.5, AU_LAND); x, y = kpt('AU', 151.2, -33.87, cx, cy, s); planes(cr, t, t0, x, y, 5); pin(cr, x, y, t, t0 + 0.2, AU_C); endmap(cr)
    k = ease_out(prog(t, t0, t0 + 0.8)); label(cr, f'{int(9 * k)} MILLION', 540, 620, 110, AU_C); ptext(cr, 'VISITORS A YEAR', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_grtour(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'GR', (0, 0), tuple(G.p('GR', 23.7, 37.98)), 1.4, 1.8, t0, t1 + 1.5, GR_LAND); x, y = kpt('GR', 23.73, 37.98, cx, cy, s); planes(cr, t, t0, x, y, 12); pin(cr, x, y, t, t0 + 0.2, GR_C); endmap(cr)
    k = ease_out(prog(t, t0, at('r4b', 'me') + 0.3)); label(cr, f'{int(38 * k)} MILLION', 540, 620, 110, GR_C); ptext(cr, 'TOURISTS IN 2025 · RECORD', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tg = at('r4b', 'four') - 0.1
    if t >= tg: chip(cr, '≈ 4 TOURISTS PER GREEK', 540, 800, 46, GOLD, INK, pop_k(t, tg), 1)
def thermo(cr, k, v, x=900, y=1030, col=(1, 0.35, 0.2)):
    rrect(cr, x - 34, y - 300, 68, 360, 34); cr.set_source_rgb(1, 1, 1); cr.fill(); cr.new_path(); cr.arc(x, y + 70, 60, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill()
    hh = lerp(30, 320 * v / 52, k); rrect(cr, x - 18, y + 40 - hh, 36, hh, 18); cr.set_source_rgb(*col); cr.fill()
def sc_grheat(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'GR', (0, 0), tuple(G.p('GR', 23.7, 38.0)), 1.4, 2.4, t0, t0 + 1.1, GR_LAND)
    x, y = kpt('GR', 23.73, 37.98, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (1, 0.5, 0.3)); endmap(cr)
    k = ease_out(prog(t, at('r5a', 'forty') - 0.2, at('r5a', 'degrees') + 0.2)); thermo(cr, k, 48.0)
    if t >= t0 + 0.9: label(cr, 'ATHENS · 1977', 540, 620, 80, WHITE)
    if k > 0: label(cr, f'{48.0 * k:.1f}°C', 560, 1000, 130, (1, 0.6, 0.4), clamp(k * 3))
def sc_auheat(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 135.4, -27.5)), 0.2, 0.6, t0, t0 + 1.1, AU_LAND)
    x, y = kpt('AU', 135.45, -27.55, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (1, 0.4, 0.2)); endmap(cr)
    k = ease_out(prog(t, at('r5b', 'fifty') - 0.2, at('r5b', 'seven') + 0.2)); thermo(cr, k, 50.7, col=(1, 0.25, 0.1))
    if t >= t0 + 0.9: label(cr, 'OODNADATTA · 1960', 540, 620, 70, WHITE)
    if k > 0: label(cr, f'{50.7 * k:.1f}°C', 560, 1000, 140, (1, 0.45, 0.2), clamp(k * 3))
    f = clamp(k) * 0.35; g = cairo.RadialGradient(540, 960, 300, 540, 960, 1100); g.add_color_stop_rgba(0, 1, 0.5, 0.1, 0); g.add_color_stop_rgba(1, 1, 0.4, 0.1, f); cr.set_source(g); cr.paint()
def bottle(cr, x, y, sc, a):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc)
    rrect(cr, -70, -120, 140, 300, 40); g = cairo.LinearGradient(-70, 0, 70, 0); g.add_color_stop_rgba(0, 0.55, 0.6, 0.12, a); g.add_color_stop_rgba(0.5, 0.85, 0.85, 0.25, a); g.add_color_stop_rgba(1, 0.5, 0.55, 0.1, a); cr.set_source(g); cr.fill()
    rrect(cr, -25, -200, 50, 90, 10); cr.set_source_rgba(0.45, 0.5, 0.1, a); cr.fill(); rrect(cr, -30, -230, 60, 36, 8); cr.set_source_rgba(0.2, 0.2, 0.2, a); cr.fill()
    rrect(cr, -60, -10, 120, 90, 10); cr.set_source_rgba(0.98, 0.96, 0.9, a); cr.fill(); ptext(cr, 'EXTRA VIRGIN', 0, 45, 20, (0.2, 0.3, 0.1), a, fam='Poppins ExtraBold', sw=0, shadow=False); cr.restore()
def sc_oil(cr, t, b, t0, t1):
    set_greece(cr, t); cr.set_source_rgba(0.05, 0.05, 0.1, 0.3); cr.paint()
    bottle(cr, 540, 1080, 1.4 * pop_k(t, t0, 0.3), 1)
    for j in range(14):
        ph = ((t - t0) * 0.5 + j / 14) % 1; emoji(cr, '🫒', (j * 137 + 40) % 1080, lerp(500, 1700, ph), 70, 1 - ph * 0.5, rot=j + t)
    label(cr, 'OLIVE OIL', 540, 620, 110, (0.75, 0.85, 0.3)); ptext(cr, 'AMONG THE TOP CONSUMERS PER PERSON ON EARTH', 540, 700, 30, WHITE, 1, fam='Poppins ExtraBold', sw=5)
    te = at('r6b', 'everything') - 0.1
    if t >= te:
        for j, em in enumerate(('🥗', '🍞', '🐟', '🍅')): emoji(cr, em, 200 + j * 230, 1450, 110 * pop_k(t, te + j * 0.08), 1)
def sc_feta(cr, t, b, t0, t1):
    set_greece(cr, t); cr.set_source_rgba(0.05, 0.05, 0.1, 0.25); cr.paint()
    for j in range(7): emoji(cr, '🐑', 150 + j * 130, 1250 + 20 * math.sin(t * 3 + j), 110 * pop_k(t, t0 + j * 0.07), 1)
    rrect(cr, 380, 900, 320, 180, 20); cr.set_source_rgb(0.98, 0.97, 0.92); cr.fill_preserve(); cr.set_source_rgb(0.8, 0.78, 0.7); cr.set_line_width(5); cr.stroke(); ptext(cr, 'FETA', 540, 1010, 60, (0.2, 0.4, 0.7), pop_k(t, t0 + 0.3), sw=0, shadow=False)
    label(cr, 'FETA', 540, 620, 110, WHITE); ptext(cr, 'MADE WITH SHEEP’S MILK', 540, 700, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_sheep(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (100, -250), 0.2, 0.23, t0, t1 + 2, AU_LAND)
    rng = np.random.default_rng(14); k = ease_out(prog(t, t0, at('r7b', 'sheep') + 0.4)); n = 0
    while n < int(90 * k):
        p = np.array([rng.uniform(-1600, 2000), rng.uniform(-1900, 600)])
        if inside(p, G.c['AU']): emoji(cr, '🐑', cx + p[0] * s, cy - p[1] * s, 44, 1); n += 1
    endmap(cr); label(cr, f'{int(74 * k)} MILLION SHEEP', 540, 620, 90, AU_C)
    tm = at('r7b', 'ten') - 0.1
    if t >= tm: chip(cr, 'GREECE: ~7 MILLION', 540, 730, 46, GR_C, INK, pop_k(t, tm), 1)
def sc_auolympics(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'OLYMPIC HOSTS', 540, 620, 90, AU_C)
    for j, (city, yr) in enumerate((('MELBOURNE', 1956), ('SYDNEY', 2000), ('BRISBANE', 2032))):
        tj = t0 + 0.2 + j * 0.3 if j < 2 else at('r8a', 'Brisbane') - 0.1
        if t < tj: continue
        y = 860 + j * 200; k = pop_k(t, tj); emoji(cr, '🔥', 250, y, 110 * k, 1); ptext(cr, f'{city} {yr}', 330, y + 20, 60, WHITE, k, anchor='l', sw=8)
def sc_olympia(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'GR', (0, 0), tuple(G.p('GR', 21.63, 37.64)), 1.4, 4.0, t0, t0 + 1.1, GR_LAND)
    x, y = kpt('GR', 21.63, 37.64, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, GOLD); endmap(cr)
    if t >= t0 + 0.9: emoji(cr, '🏛️', 540, 1150, 220 * pop_k(t, t0 + 0.9), 1); emoji(cr, '🔥', 720, 1050, 120 * pop_k(t, t0 + 1.0), 1)
    label(cr, 'OLYMPIA · 776 BC', 540, 620, 90, GOLD); ptext(cr, 'FIRST MODERN GAMES: ATHENS 1896', 540, 700, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_melbourne(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 145.0, -37.8)), 0.2, 0.9, t0, t0 + 1.1, AU_LAND)
    x, y = kpt('AU', 144.96, -37.81, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, GR_C)
    if t >= t0 + 0.9:
        rng = np.random.default_rng(3); kk = ease_out(prog(t, t0 + 0.9, t0 + 2.0))
        for j in range(int(180 * kk)):
            r, a = abs(rng.normal(0, 55)), rng.uniform(0, 2 * math.pi); cr.new_path(); cr.arc(x + r * math.cos(a), y + r * math.sin(a), 4, 0, 2 * math.pi); cr.set_source_rgba(*GR_C, 0.9); cr.fill()
    endmap(cr); label(cr, 'MELBOURNE', 540, 620, 110, GR_C); ptext(cr, '~181,000 GREEK AUSTRALIANS IN VICTORIA', 540, 700, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_greeks(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'GR', (0, 0), (0, 0), 1.3, 1.45, t0, t1 + 2, GR_LAND)
    rng = np.random.default_rng(9); kk = ease_out(prog(t, t0, t0 + 1.0)); n = 0
    while n < int(600 * kk):
        lon, lat = rng.uniform(19.5, 28.5), rng.uniform(34.8, 41.8); p = G.p('GR', lon, lat)
        if inside(p, G.c['GR']): px, py = kpt('GR', lon, lat, cx, cy, s); cr.new_path(); cr.arc(px, py, 4, 0, 2 * math.pi); cr.set_source_rgba(*GR_C, 0.9); cr.fill(); n += 1
    endmap(cr); label(cr, '10.4 MILLION GREEKS', 540, 620, 90, GR_C); chip(cr, 'I AM GREECE.', 540, 730, 54, WHITE, INK, pop_k(t, at('r9b', 'AM') - 0.1) if t >= at('r9b', 'AM') - 0.1 else 0, 1)
SCENE = {'santorini': sc_santorini, 'size': sc_size, 'kosci': sc_kosci, 'olympus': sc_olympus, 'grislands': sc_grislands, 'auislands': sc_auislands, 'autour': sc_autour,
         'grtour': sc_grtour, 'grheat': sc_grheat, 'auheat': sc_auheat, 'oil': sc_oil, 'feta': sc_feta, 'sheep': sc_sheep, 'auolympics': sc_auolympics, 'olympia': sc_olympia,
         'melbourne': sc_melbourne, 'greeks': sc_greeks}

# ---------- hook, close-ups, title ----------
GR_TILES = None
def uk_tiles():
    global GR_TILES
    if GR_TILES is None:
        pts = []
        for jj, y in enumerate(np.arange(-2000, 2000, 420)):
            for x in np.arange(-2200 + (jj % 2) * 150, 2200, 300):
                if inside(np.array([x, y]), G.c['AU']): pts.append((x, y))
        rng = np.random.default_rng(58); order = rng.permutation(len(pts))[:58]; GR_TILES = [pts[k] for k in order]
    return GR_TILES
def draw_hook(cr, t):
    """Cold open: the two balls trade insults, then 58 Greeces stamp onto Australia."""
    if t >= bt('title')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        sh_close(cr, t, b1, 'Greece', 0, b1['end'], 'angry'); emoji(cr, '🏛️', 880, 820, 140, 1, rot=-0.1 + 0.05 * math.sin(t * 3))
        return True
    if t < b3['start']:
        sx, sy = shake(t, w('h2', 'islands') - 0.05, 20, 0.4); cr.save(); cr.translate(sx, sy)
        sh_low(cr, t, b2, 'Australia', b2['start'], b2['end'], 'angry'); cr.restore()
        emoji(cr, '😎', 860, 820, 130 * pop_k(t, b2['l0'], 0.3), 1)
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2)))
        return True
    cx, cy, s = mview(cr, t, 'AU', (0, -100), (0, 0), 0.2, 0.19, b3['start'], b3['end'], AU_LAND)
    t0 = w('h3', 'fits') - 0.1; t1 = w('h3', 'fifty-eight', end=True) + 0.2; n = int(clamp(prog(t, t0, t1)) * 58) if t >= t0 else 0
    tiles = uk_tiles()
    for k_, (x, y) in enumerate(tiles[:n]):
        tk = t0 + (k_ + 1) / 58 * (t1 - t0); kk = ease_out(prog(t, tk - 0.08, tk + 0.12)); sc = lerp(1.8, 1.0, kk)
        cr.save(); px, py = cx + x * s, cy - y * s; cr.translate(px, py); cr.scale(sc, sc); cr.translate(-px, -py)
        km_shape(cr, G.gr_true, cx, cy, s, GR_LAND, 1, x, y, fill=0.92, lw=1.5, edge=INK); cr.restore()
    endmap(cr)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
    if n: sx, sy = shake(t, t0 + n / 58 * (t1 - t0), 6, 0.12); cr.save(); cr.translate(sx, sy); ptext(cr, f'×{n}', 540, 360, 190, GR_C, 1, sw=18); cr.restore()
    ts = w('h3', 'four') - 0.1
    if t >= ts:
        cr.set_source_rgba(0, 0, 0.05, 0.5 * clamp((t - ts) * 4)); cr.paint()
        sx, sy = shake(t, ts, 18); cr.save(); cr.translate(sx, sy); slam(cr, '400,000+', 540, 860, 170, GR_C, t, ts); slam(cr, 'GREEK AUSTRALIANS', 540, 1010, 96, WHITE, t, w('h3', 'Greek') - 0.1); cr.restore()
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
    ball(cr, 'Australia', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'Greece', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'AUSTRALIA', 540, 560, 180, AU_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'GREECE', 540, 980, 190, GR_C, t, w('title', 'winner'))
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
    for side, x, col, sc, lab in (('A', 250, AU_C, sn, 'AUSTRALIA'), ('U', 830, GR_C, ss, 'GREECE')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = ('TIEBREAKER' if i == NR else f'ROUND {i}/8') if i else ('FINAL' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📏', 2: '⛰️', 3: '🏝️', 4: '✈️', 5: '🔥', 6: '🫒', 7: '🐑', 8: '🏅', 9: '🏛️'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((AU_C, GR_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    head = 'TIEBREAKER' if i == NR else f'ROUND {i}'
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, head, 0, 0, 130 if i == NR else 150, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = (at('c9', 'who') - 0.1) if i == NR else b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    if i == NR:
        ptext(cr, '4 — 4', 540, 600, 90, WHITE, pop_k(t, b['l0']), sw=10)
        ts = at('c9', 'Greeks') - 0.1
        if t >= ts: chip(cr, 'MELBOURNE VS ATHENS?', 540, 1420, 44, GOLD, INK, pop_k(t, ts), 1)
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = AU_C if win == 'A' else GR_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('AUSTRALIA' if win == 'A' else 'GREECE') + ' WINS'
    cr.save(); cr.translate(x, 1450); cr.rotate(-0.05 if win == 'A' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 72)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, 72, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- ending ----------
def draw_end(cr, t):
    e1, e2, c = bt('e1'), bt('e2'), bt('cta')
    if t < e2['start']:
        h = hop_of(t, e1); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.12), -0.05, 540, 1100); set_australia(cr, t); ball(cr, 'Australia', 540, 1290 - h * 40, 290, 'neutral', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Australia', 540, 1640, AU_C)
        ptext(cr, 'GREECE WINS 5 — 4', 540, 790, 80, GR_C, pop_k(t, e1['start'] + 0.2), sw=12); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540, 1100); set_greece(cr, t)
        ball(cr, 'Greece', 540, 1260 - h * 50, 320, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Greece', 540, 1640, GR_C)
        for j, em in enumerate(('🥙', '🍷', '🫒')): emoji(cr, em, 200 + j * 340, 800 + 20 * math.sin(t * 4 + j), 120 * pop_k(t, e2['l0'] + 0.2 + j * 0.1), 1)
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.08), 0.02, 540, 1000); arena(cr, t)
    ball(cr, 'Australia', 290, 1300, 200, 'happy', 0, 0.8); ball(cr, 'Greece', 790, 1300, 200, 'happy', 0, -0.8); cr.restore()
    ptext(cr, '4 — 5', 540, 1000, 140, WHITE, 1, sw=14)
    for x, col, word, lab, rot in ((290, AU_C, 'Australia', 'AUSTRALIA', -0.04), (790, GR_C, 'Greece', 'GREECE', 0.04)):
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
    boom(0.0, 1.0); rumble(0.0, 1.0, 0.25); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(w('h2', 'islands') - 0.05, 0.8)
    whoosh(bt('h3')['start'] - 0.3, 0.3); t0_ = w('h3', 'fits') - 0.1; t1_ = w('h3', 'fifty-eight', end=True) + 0.2
    for k_ in range(58): pop(t0_ + (k_ + 1) / 58 * (t1_ - t0_), 0.07, 600 + 14 * k_)
    boom(w('h3', 'four') - 0.1, 1.0); boom(w('h3', 'Greek') - 0.1, 0.8)
    for k in ('title',): whoosh(bt(k)['start'] - 0.35)
    for wd in ('Eight', 'winner', 'geography'): boom(w('title', wd), 0.7)
    horn(w('title', 'geography'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1); pop(tv + 0.55, 0.12, 500)
    for k, sp, _ in LINES:
        if sp: whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
        if k in SHOTS:
            for s0, sh in shot_list(k)[1:]: whoosh(s0 - 0.2, 0.16, 0.22)
    boom(at('c9', 'who') - 0.1, 0.9); rumble(at('c9', 'Greeks'), 1.2, 0.15)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_auge'))
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
