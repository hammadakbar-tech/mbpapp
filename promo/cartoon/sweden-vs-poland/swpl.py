# Countryballs: Sweden vs Poland, the Geography War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (lakes, Nobel medals, Malbork, Minecraft, moose...).
# Usage: python3 swpl.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

SE_C, PL_C = hexc('#3D8BFF')[:3], hexc('#F0435A')[:3]
A_C, U_C = SE_C, PL_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Sweden': ('sv-SE-MattiasNeural', '+4%'), 'Poland': ('pl-PL-MarekNeural', '+4%')}
LINES = [
    ('h1', 'Poland', "Sweden! All you've got is flat-pack furniture!"),
    ('h2', 'Sweden', "And all you've got is pierogi!"),
    ('h3', None, "Sweden is so long that if you flip it over at its southern tip, it reaches about as far as Rome!"),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: size."),
    ('r1a', 'Poland', "I'm bigger than Italy!"),
    ('r1b', 'Sweden', "Cute. I'm almost one and a half times bigger than you!"),
    ('c2', None, "Round two: people."),
    ('r2a', 'Sweden', "Ten and a half million Swedes!"),
    ('r2b', 'Poland', "Thirty-seven million Poles. Three and a half times more!"),
    ('c3', None, "Round three: lakes."),
    ('r3a', 'Poland', "The Masurian Lake District has over two thousand lakes!"),
    ('r3b', 'Sweden', "Cute. I have almost one hundred thousand!"),
    ('c4', None, "Round four: the Nobel Prize."),
    ('r4a', 'Sweden', "I created the Nobel Prize!"),
    ('r4b', 'Poland', "And Marie Curie won it twice. The first person ever!"),
    ('c5', None, "Round five: music."),
    ('r5a', 'Poland', "I gave the world Chopin!"),
    ('r5b', 'Sweden', "I gave the world ABBA. And seven Eurovision wins. Tied for the most ever!"),
    ('c6', None, "Round six: castles."),
    ('r6a', 'Sweden', "I built the world's first ice hotel!"),
    ('r6b', 'Poland', "I built Malbork. The biggest castle on Earth by area!"),
    ('c7', None, "Round seven: video games."),
    ('r7a', 'Poland', "I made The Witcher!"),
    ('r7b', 'Sweden', "I made Minecraft. The best-selling video game of all time!"),
    ('c8', None, "Final round: wildlife."),
    ('r8a', 'Sweden', "I have around three hundred thousand moose!"),
    ('r8b', 'Poland', "I have the European bison. The heaviest land animal in Europe!"),
    ('e1', 'Sweden', "Four all?! Seriously?"),
    ('e2', 'Poland', "Let the viewers decide! Na zdrowie!"),
    ('cta', None, "It's a tie! You pick the tiebreaker. Comment it below, and subscribe to see who wins!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SIZE', 'A', ('r1b', 'bigger')), 2: ('PEOPLE', 'U', ('r2b', 'more')), 3: ('LAKES', 'A', ('r3b', 'thousand')), 4: ('THE NOBEL PRIZE', 'U', ('r4b', 'ever')),
      5: ('MUSIC', 'A', ('r5b', 'most')), 6: ('CASTLES', 'U', ('r6b', 'area')), 7: ('VIDEO GAMES', 'A', ('r7b', 'time')), 8: ('WILDLIFE', 'U', ('r8b', 'Europe'))}
NR = 8
SHOTS = {
    'r1a': [(None, 'two'), ('Italy', 'map:italy')], 'r1b': [(None, 'close'), ('one', 'map:size')],
    'r2a': [(None, 'low'), ('Ten', 'map:sepop')], 'r2b': [(None, 'ots'), ('Thirty', 'map:plpop')],
    'r3a': [(None, 'close'), ('Masurian', 'map:masuria')], 'r3b': [(None, 'low'), ('almost', 'map:selakes')],
    'r4a': [(None, 'two'), ('Nobel', 'map:nobel')], 'r4b': [(None, 'ots'), ('Marie', 'map:curie')],
    'r5a': [(None, 'close'), ('Chopin', 'map:chopin')], 'r5b': [(None, 'two'), ('ABBA', 'map:abba')],
    'r6a': [(None, 'low'), ('first', 'map:icehotel')], 'r6b': [(None, 'ots'), ('Malbork', 'map:malbork')],
    'r7a': [(None, 'two'), ('Witcher', 'map:witcher')], 'r7b': [(None, 'low'), ('Minecraft', 'map:minecraft')],
    'r8a': [(None, 'close'), ('three', 'map:moose')], 'r8b': [(None, 'ots'), ('European', 'map:bison')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {}}
C.HOT = ('sweden', 'poland', 'rome', 'flip', 'long', 'war', 'tie', 'tiebreaker', 'comment', 'subscribe', 'winner', 'furniture', 'pierogi')
C.TAIL_OVERRIDE = {'h1': 0.12, 'h2': 0.2, 'h3': 0.8, 'title': 0.6, 'e1': 0.3, 'e2': 0.4, 'cta': 3.6, **{f'c{i}': 0.15 for i in range(1, 9)},
                   **{k: 0.3 for k, s, _ in LINES if s and k[0] == 'r'}, **{RD[i][2][0]: 1.1 for i in RD}, 'h1': 0.12, 'h2': 0.2}
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
EURO = ['Norway', 'Finland', 'Denmark', 'Germany', 'Poland', 'Lithuania', 'Latvia', 'Estonia', 'Belarus', 'Ukraine', 'Czechia', 'Slovakia', 'Austria', 'Hungary', 'Italy', 'Switzerland',
        'France', 'Netherlands', 'Belgium', 'Luxembourg', 'Slovenia', 'Croatia', 'Bosnia and Herz.', 'Serbia', 'Montenegro', 'Albania', 'Kosovo', 'North Macedonia', 'Romania', 'Moldova', 'Bulgaria', 'Russia']
class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        R = lambda n: [r for r in rings(cf[n]['geometry']) if len(r) > 3 and (n != 'Russia' or r[:, 0].mean() < 40)]
        self.ref = {'SE': (16.0, 62.0), 'PL': (19.4, 52.0)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('SE', 'Sweden', EURO), ('PL', 'Poland', [x for x in EURO if x != 'Poland'] + ['Sweden'])):
            rs = R(n); pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs if nn in cf for r in local(R(nn), *self.ref[k])]
        self.pl_in_se = [r - self.off['SE'] for r in local(R('Poland'), *self.ref['SE'])]
        self.pl_true = [r - np.concatenate(self.c['PL']).mean(axis=0) for r in self.c['PL']]
        it = local(R('Italy'), *self.ref['PL']); self.it_true = [r - np.concatenate(it).mean(axis=0) for r in it]
        self.tip, self.ntip, self.rome = self.p('SE', 13.36, 55.34), self.p('SE', 20.55, 69.06), self.p('SE', 12.5, 41.9)
        print('areas M km2: sweden', round(area(self.c['SE']) / 1e6, 3), 'poland', round(area(self.c['PL']) / 1e6, 3), 'ratio', round(area(self.c['SE']) / area(self.c['PL']), 2),
              '| length km', round(float(np.hypot(*(self.ntip - self.tip)))), 'tip->rome km', round(float(np.hypot(*(self.rome - self.tip)))))
        B.FL['Sweden'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'se.png')); B.FL['Poland'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'pl.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'Sweden' else 'U'
def col_of(name): return SE_C if name == 'Sweden' else PL_C
def rival_of(name): return 'Poland' if name == 'Sweden' else 'Sweden'
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
def set_sweden(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.02, 0.04, 0.14); g.add_color_stop_rgb(0.55, 0.08, 0.16, 0.3); g.add_color_stop_rgb(1, 0.85, 0.9, 0.96); cr.set_source(g); cr.paint()
    rng = np.random.default_rng(5)
    for _ in range(70): x, y = rng.uniform(0, W), rng.uniform(0, 700); cr.new_path(); cr.arc(x, y, 1.6, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.5 + 0.3 * math.sin(t * 2 + x)); cr.fill()
    for j in range(3):  # aurora ribbons
        cr.new_path(); cr.move_to(-50, 380 + j * 90)
        for x in range(0, 1200, 60): cr.line_to(x, 380 + j * 90 + 70 * math.sin(x / 170 + t * 0.8 + j))
        cr.set_source_rgba(0.3, 1, 0.6, 0.22 - j * 0.05); cr.set_line_width(60 - j * 12); cr.stroke()
    for k in range(13):  # pine forest
        x = -40 + k * 95; h = 260 + 120 * abs(math.sin(k * 1.7)); cr.new_path(); cr.move_to(x - 70, 1320); cr.line_to(x, 1320 - h); cr.line_to(x + 70, 1320); cr.close_path(); cr.set_source_rgb(0.05, 0.2, 0.16); cr.fill()
        cr.new_path(); cr.move_to(x - 30, 1320 - h * 0.6); cr.line_to(x, 1320 - h); cr.line_to(x + 30, 1320 - h * 0.6); cr.close_path(); cr.set_source_rgb(0.93, 0.95, 1); cr.fill()
    hx = 720; cr.rectangle(hx, 1120, 260, 200); cr.set_source_rgb(0.62, 0.12, 0.1); cr.fill()  # falu-red cottage
    cr.new_path(); cr.move_to(hx - 30, 1130); cr.line_to(hx + 130, 1020); cr.line_to(hx + 290, 1130); cr.close_path(); cr.set_source_rgb(0.95, 0.97, 1); cr.fill()
    for wx in (hx + 40, hx + 170): cr.rectangle(wx, 1170, 50, 50); cr.set_source_rgb(1, 0.85, 0.5); cr.fill(); cr.rectangle(wx - 6, 1164, 62, 62); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke()
    cr.rectangle(-200, 1310, 1500, 800); cr.set_source_rgb(0.9, 0.93, 0.98); cr.fill()
    for j in range(60):
        x = (j * 83 + 30 * math.sin(j)) % 1100; y = ((t * 90 + j * 211) % 2000) - 100; cr.new_path(); cr.arc(x + 10 * math.sin(t + j), y, 3, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.8); cr.fill()
def set_poland(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.32, 0.2, 0.42); g.add_color_stop_rgb(0.5, 0.98, 0.58, 0.42); g.add_color_stop_rgb(0.7, 1, 0.82, 0.6); g.add_color_stop_rgb(1, 0.4, 0.24, 0.22); cr.set_source(g); cr.paint()
    cr.new_path(); cr.arc(300, 760, 150, 0, 2 * math.pi); cr.set_source_rgba(1, 0.92, 0.7, 0.85); cr.fill()
    for k in range(9):  # old town tenements
        x = -60 + k * 135; h = 330 + 80 * math.sin(k * 2.1); cr.rectangle(x, 1330 - h, 135, h); cr.set_source_rgb(*((0.85, 0.55, 0.4), (0.9, 0.78, 0.5), (0.7, 0.45, 0.45))[k % 3]); cr.fill()
        cr.new_path(); cr.move_to(x, 1330 - h); cr.line_to(x + 67, 1330 - h - 70); cr.line_to(x + 135, 1330 - h); cr.close_path(); cr.set_source_rgb(0.55, 0.22, 0.18); cr.fill()
        for r in range(3):
            for c_ in range(2): cr.rectangle(x + 30 + c_ * 50, 1330 - h + 40 + r * 90, 26, 46); cr.set_source_rgba(1, 0.95, 0.75, 0.8); cr.fill()
    tx = 760  # church towers
    for dx, hh in ((-70, 640), (70, 560)):
        cr.rectangle(tx + dx - 45, 1330 - hh, 90, hh); cr.set_source_rgb(0.5, 0.2, 0.18); cr.fill()
        cr.new_path(); cr.move_to(tx + dx - 50, 1330 - hh); cr.line_to(tx + dx, 1330 - hh - 150); cr.line_to(tx + dx + 50, 1330 - hh); cr.close_path(); cr.set_source_rgb(0.25, 0.42, 0.35); cr.fill()
    cr.rectangle(-200, 1320, 1500, 800); cr.set_source_rgb(0.5, 0.4, 0.38); cr.fill()
    for j in range(16): cr.rectangle(j * 80 - 20, 1360 + (j % 3) * 60, 60, 26); cr.set_source_rgba(0.35, 0.27, 0.25, 0.6); cr.fill()
    for j in range(8):
        ph = (t * 0.25 + j * 0.13) % 1; x = (j * 137) % 1080 + 60 * math.sin(t + j); cr.save(); cr.translate(x, 700 - 300 * ph); cr.scale(1, 0.4)
        cr.new_path(); cr.arc(-14, 0, 14, math.pi, 0); cr.arc(14, 0, 14, math.pi, 0); cr.set_source_rgba(0.15, 0.1, 0.1, 0.6 * (1 - ph)); cr.set_line_width(4); cr.stroke(); cr.restore()
def set_of(name, cr, t): (set_sweden if name == 'Sweden' else set_poland)(cr, t)

# ---------- shots ----------
def sh_close(cr, t, b, name, t0, t1, mood='happy'):
    sgn = -1 if name == 'Sweden' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.07 * sgn * (1 if sum(map(ord, b['key'])) % 2 else -1), 540, 1100); set_of(name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1, mood='happy'):
    sgn = -1 if name == 'Sweden' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, mood, 0.04 * h, -sgn * 0.2); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_ots(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Sweden' else 1; h = hop_of(t, b); rv = rival_of(name)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.06), 0.02 * sgn, 540 + lerp(0, -sgn * 40, prog(t, t0, t1)), 1000); set_of(name, cr, t)
    ball(cr, name, 540 + sgn * 150, 1080 - h * 36, 210, 'happy', 0.05 * h, -sgn * 0.6)
    ball(cr, rv, 540 - sgn * 470, 1700, 560, 'angry', 0, sgn * 0.9); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.paint()
    bubble(cr, t, b, 540 + sgn * 150, 520); nametag(cr, name, 540 + sgn * 150, 1340, col_of(name))
def sh_two(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Sweden' else 1; h = hop_of(t, b); rv = rival_of(name)
    pan = lerp(-60, 60, prog(t, t0, t1)) * sgn
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    for n, x in (('Sweden', 290), ('Poland', 790)):
        hh = h if n == name else 0; ball(cr, n, x, 1300 - hh * 40, 220, 'happy' if n == name else 'angry', 0.05 * hh, 0.8 if n == 'Sweden' else -0.8)
    cr.restore()
    sx = (290 if name == 'Sweden' else 790) - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1600, col_of(name))
def sh_react(cr, t, b, name, t0, t1):
    rv = rival_of(name); k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.25, 1.08, k), -0.06 if rv == 'Sweden' else 0.06, 540 + sx, 1080 + sy); set_of(rv, cr, t)
    ball(cr, rv, 540, 1150, 360, 'shock', 0, 0); cr.restore()
    ptext(cr, '?!', 860, 760, 170, GOLD, pop_k(t, t0 + 0.05), sw=14)
    nametag(cr, rv, 540, 1640, col_of(rv))
def sh_map(cr, t, b, name, t0, t1, scene):
    SCENE[scene](cr, t, b, t0, t1)
    sgn = -1 if name == 'Sweden' else 1; h = hop_of(t, b); x = 540 + sgn * 380
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
US_LAND, UK_LAND = (0.36, 0.5, 0.78), (0.82, 0.86, 0.8)
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
    while m < n and tries < n * 6:
        tries += 1; lon, lat = rng.uniform(lon0, lon1), rng.uniform(lat0, lat1); p = G.p(k_, lon, lat)
        if inside(p, G.c[k_]): x, y = cx + p[0] * s, cy - p[1] * s; cr.new_path(); cr.arc(x, y, 3.5, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.9); cr.fill(); m += 1
SE_LAND, PL_LAND = (0.36, 0.55, 0.85), (0.92, 0.82, 0.8)
def sc_italy(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'PL', (0, 0), (0, 0), 0.95, 1.0, t0, t1 + 1, PL_LAND)
    k = ease_out(prog(t, t0 + 0.2, t0 + 0.7)); cr.save(); cr.translate(0, (1 - k) * -1200)
    km_shape(cr, G.it_true, cx, cy, s, (0.3, 0.75, 0.45), 0.85, 0, 0, fill=0.75, lw=3, edge=INK); cr.restore(); endmap(cr)
    label(cr, 'POLAND > ITALY', 540, 600, 104, PL_C)
    if k >= 1: chip(cr, '312,696 KM²  vs  302,068 KM²', 540, 710, 46, WHITE, INK, pop_k(t, t0 + 0.7), 1)
    if t >= t0 + 0.9: chip(cr, 'ITALY', 540, 1300, 36, (0.3, 0.75, 0.45), INK, 1, 1)
def sc_size(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'SE', (0, 0), (0, -60), 0.6, 0.62, t0, t1 + 1.5, SE_LAND)
    k = ease_out(prog(t, t0, t0 + 0.5)); cr.save(); cr.translate(0, (1 - k) * -1200); km_shape(cr, G.pl_true, cx, cy, s, PL_LAND, 1, 0, -250, fill=0.85, lw=3, edge=INK); cr.restore()
    endmap(cr)
    if k >= 1: chip(cr, 'POLAND', cx, cy + 250 * s, 34, WHITE, INK, 1, 1)
    tx = at('r1b', 'bigger') - 0.1
    if t >= tx:
        sx, sy = shake(t, tx, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'SWEDEN ≈ 1.4 POLANDS', 540, 620, 92, WHITE, t, tx); cr.restore()
        ptext(cr, '450,295 KM²  vs  312,696 KM²', 540, 710, 36, WHITE, 0.9, fam='Poppins ExtraBold', sw=5)
SEC = [('STOCKHOLM', 18.07, 59.33, 2.4), ('GOTHENBURG', 11.97, 57.71, 1.1), ('MALMÖ', 13.0, 55.6, 0.75), ('UPPSALA', 17.64, 59.86, 0.25)]
def sc_sepop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'SE', (0, 0), (60, -350), 0.6, 0.85, t0, t1 + 1.5, SE_LAND); k = ease_out(prog(t, t0, t0 + 1.2))
    dots(cr, 'SE', int(260 * k), cx, cy, s, 11, 19, 55.3, 61, (1, 0.85, 0.3), 3); dots(cr, 'SE', int(60 * k), cx, cy, s, 12, 24, 61, 69, (1, 0.85, 0.3), 4)
    for j, (nm, lon, lat, m) in enumerate(SEC):
        x, y = kpt('SE', lon, lat, cx, cy, s)
        if t >= t0 + 0.3 + j * 0.15: kk = pop_k(t, t0 + 0.3 + j * 0.15); cr.new_path(); cr.arc(x, y, 18 * math.sqrt(m) * kk, 0, 2 * math.pi); cr.set_source_rgba(*SE_C, 0.9); cr.fill(); ptext(cr, nm, x + (150 if lon > 15 else -150), y + 10, 30, WHITE, kk, fam='Poppins ExtraBold', sw=5) if j < 3 else None
    endmap(cr); label(cr, f'{10.6 * k:.1f} MILLION', 540, 620, 104, SE_C)
PLC = [('WARSAW', 21.01, 52.23, 1.9), ('KRAKÓW', 19.94, 50.06, 0.8), ('ŁÓDŹ', 19.46, 51.76, 0.65), ('WROCŁAW', 17.04, 51.11, 0.67), ('POZNAŃ', 16.93, 52.41, 0.54), ('GDAŃSK', 18.65, 54.35, 0.48), ('SZCZECIN', 14.55, 53.43, 0.39)]
def sc_plpop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'PL', (0, 0), (0, 0), 0.95, 1.05, t0, t1 + 1.5, PL_LAND); k = ease_out(prog(t, t0, at('r2b', 'Poles') + 0.4))
    dots(cr, 'PL', int(900 * k), cx, cy, s, 14, 24.2, 49, 55, (1, 0.85, 0.3), 7)
    for j, (nm, lon, lat, m) in enumerate(PLC):
        x, y = kpt('PL', lon, lat, cx, cy, s)
        if t >= t0 + 0.3 + j * 0.1: kk = pop_k(t, t0 + 0.3 + j * 0.1); cr.new_path(); cr.arc(x, y, 18 * math.sqrt(m) * kk, 0, 2 * math.pi); cr.set_source_rgba(*PL_C, 0.9); cr.fill(); ptext(cr, nm, x, y - 34, 28, WHITE, kk, fam='Poppins ExtraBold', sw=5) if j < 3 else None
    endmap(cr); label(cr, f'{37 * k:.0f} MILLION', 540, 620, 104, PL_C)
    tm = at('r2b', 'Three') - 0.1
    if t >= tm: chip(cr, '≈ 3.5× SWEDEN', 540, 730, 50, GOLD, INK, pop_k(t, tm), 1)
def lakes(cr, n, cx, cy, s, k_, lon0, lon1, lat0, lat1, seed, rmax=7):
    rng = np.random.default_rng(seed); m = 0; tries = 0
    while m < n and tries < n * 6:
        tries += 1; lon, lat = rng.uniform(lon0, lon1), rng.uniform(lat0, lat1); p = G.p(k_, lon, lat)
        if inside(p, G.c[k_]):
            x, y = cx + p[0] * s, cy - p[1] * s; r = rng.uniform(2, rmax); cr.save(); cr.translate(x, y); cr.rotate(rng.uniform(0, 3)); cr.scale(1, rng.uniform(0.4, 0.9)); cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.restore()
            cr.set_source_rgb(0.2, 0.55, 0.95); cr.fill(); m += 1
def sc_masuria(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'PL', (0, 0), tuple(G.p('PL', 21.7, 53.8)), 0.95, 3.2, t0, t0 + 1.2, PL_LAND)
    k = ease_out(prog(t, t0 + 0.8, at('r3a', 'thousand') + 0.3)); lakes(cr, int(260 * k), cx, cy, s, 'PL', 20.3, 23.0, 53.4, 54.3, 4, 9); endmap(cr)
    label(cr, 'MASURIAN LAKES', 540, 600, 100, PL_C); kk = ease_out(prog(t, at('r3a', 'two') - 0.2, at('r3a', 'thousand') + 0.3))
    if t >= at('r3a', 'two') - 0.2: chip(cr, f'{int(round(2000 * kk, -1)):,}+ LAKES', 540, 710, 56, GOLD, INK, 1, 1)
def sc_selakes(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'SE', (0, 0), (0, -40), 0.6, 0.62, t0, t1 + 1.5, SE_LAND); k = ease_out(prog(t, t0, at('r3b', 'thousand') + 0.4))
    lakes(cr, int(2200 * k), cx, cy, s, 'SE', 11, 24, 55.3, 69, 6, 5); endmap(cr)
    label(cr, f'≈ {int(100 * k)},000 LAKES', 540, 620, 100, SE_C); ptext(cr, 'LAKES BIGGER THAN 1 HECTARE (SMHI)', 540, 700, 32, WHITE, 0.85, fam='Poppins ExtraBold', sw=5)
def medal(cr, t, x, y, r, t0, txt, sub_, col=(1, 0.8, 0.25)):
    if t < t0: return
    k = pop_k(t, t0, 0.3); cr.save(); cr.translate(x, y - abs(math.sin(t * 3 + x)) * 8); cr.scale(k, k)
    for sgn in (-1, 1): cr.new_path(); cr.move_to(sgn * 20, -r - 160); cr.line_to(sgn * 70, -r - 160); cr.line_to(sgn * 25, -r + 10); cr.line_to(-sgn * 20, -r + 10); cr.close_path(); cr.set_source_rgb(*(SE_C if sgn < 0 else (1, 0.85, 0.2))); cr.fill()
    cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(0.65, 0.45, 0.1); cr.set_line_width(10); cr.stroke()
    cr.new_path(); cr.arc(0, 0, r * 0.78, 0, 2 * math.pi); cr.set_source_rgba(0.65, 0.45, 0.1, 0.6); cr.set_line_width(4); cr.stroke()
    ptext(cr, txt, 0, r * 0.12, r * 0.36, (0.45, 0.3, 0.05), 1, sw=0, shadow=False); ptext(cr, sub_, 0, r * 0.42, r * 0.17, (0.45, 0.3, 0.05), 1, fam='Poppins ExtraBold', sw=0, shadow=False); cr.restore()
def sc_nobel(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'THE NOBEL PRIZE', 540, 600, 100, SE_C); ptext(cr, 'ALFRED NOBEL · STOCKHOLM · SINCE 1901', 540, 690, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    medal(cr, t, 540, 1120, 190, t0 + 0.1, 'NOBEL', 'SINCE 1901')
def sc_curie(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'MARIE SKŁODOWSKA-CURIE', 540, 600, 74, PL_C)
    medal(cr, t, 300, 1130, 150, at('r4b', 'twice') - 0.2, '1903', 'PHYSICS'); medal(cr, t, 780, 1130, 150, at('r4b', 'twice') + 0.1, '1911', 'CHEMISTRY')
    tf = at('r4b', 'first') - 0.1
    if t >= tf: chip(cr, 'FIRST PERSON TO WIN TWO', 540, 710, 52, GOLD, INK, pop_k(t, tf), 1)
def sc_chopin(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'FRÉDÉRIC CHOPIN', 540, 600, 96, PL_C); ptext(cr, 'BORN NEAR WARSAW · 1810', 540, 690, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    x0 = 120; k = ease_out(prog(t, t0, t0 + 0.6))
    for j in range(14): cr.rectangle(x0 + j * 60, 1000, 56, 330 * k); cr.set_source_rgb(0.97, 0.96, 0.92); cr.fill()
    for j in (0, 1, 3, 4, 5, 7, 8, 10, 11, 12): cr.rectangle(x0 + j * 60 + 38, 1000, 40, 200 * k); cr.set_source_rgb(0.06, 0.06, 0.08); cr.fill()
    for j in range(8):
        ph = ((t - t0) * 0.6 + j / 8) % 1; emoji(cr, '🎵' if j % 2 else '🎶', 160 + (j * 131) % 760 + 40 * math.sin(t * 2 + j), 980 - 320 * ph, 70, (1 - ph) * k)
def sc_abba(cr, t, b, t0, t1):
    arena(cr, t, SE_C); label(cr, 'ABBA · EUROVISION 1974', 540, 600, 72, SE_C)
    emoji(cr, '🪩', 540, 900 + 10 * math.sin(t * 3), 210 * pop_k(t, t0 + 0.1), 1, rot=0.2 * math.sin(t * 2))
    ts = at('r5b', 'seven') - 0.1
    for j, yr in enumerate(('1974', '1984', '1991', '1999', '2012', '2015', '2023')):
        tj = ts + j * 0.1
        if t < tj: continue
        x = 150 + (j % 4) * 260 + (130 if j >= 4 else 0); y = 1160 + (j // 4) * 200; kk = pop_k(t, tj); emoji(cr, '🏆', x, y, 100 * kk, 1); ptext(cr, yr, x, y + 82, 34, SE_C, kk, sw=6)
    tm = at('r5b', 'Tied') - 0.1
    if t >= tm: chip(cr, '7 WINS · TIED MOST EVER', 540, 720, 50, GOLD, INK, pop_k(t, tm), 1)
def sc_icehotel(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.05, 0.1, 0.25); g.add_color_stop_rgb(1, 0.7, 0.85, 0.95); cr.set_source(g); cr.paint()
    k = prog(t, t0, t0 + 1.4)
    for r in range(6):
        for c_ in range(7 - (r % 2)):
            j = r * 7 + c_; kk = clamp(k * 42 - j)
            if kk <= 0: continue
            x = 140 + c_ * 120 + (60 if r % 2 else 0); y = 1420 - r * 80 - (1 - ease_out(kk)) * 300
            rrect(cr, x - 56, y - 36, 112, 72, 10); cr.set_source_rgba(0.85, 0.95, 1, 0.9); cr.fill_preserve(); cr.set_source_rgba(0.5, 0.75, 0.95, 1); cr.set_line_width(3); cr.stroke()
    rrect(cr, 470, 1300, 140, 160, 70); cr.set_source_rgba(0.2, 0.4, 0.7, 0.8); cr.fill()
    label(cr, 'ICEHOTEL · 1989', 540, 600, 100, SE_C); ptext(cr, 'JUKKASJÄRVI · REBUILT FROM ICE EVERY WINTER', 540, 690, 30, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tf = at('r6a', 'first') - 0.1
    if t >= tf: chip(cr, "WORLD'S FIRST ICE HOTEL", 540, 790, 48, GOLD, INK, pop_k(t, tf), 1)
def sc_malbork(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.25, 0.3, 0.55); g.add_color_stop_rgb(0.6, 0.98, 0.7, 0.5); g.add_color_stop_rgb(1, 0.2, 0.25, 0.3); cr.set_source(g); cr.paint()
    k = ease_out(prog(t, t0, t0 + 0.9)); base = 1380
    def tower(x, w_, h_, roof=True):
        hh = h_ * k; cr.rectangle(x - w_ / 2, base - hh, w_, hh); cr.set_source_rgb(0.62, 0.25, 0.18); cr.fill()
        for yy in range(int(base - hh + 30), base - 20, 60):
            for xx in range(int(x - w_ / 2 + 14), int(x + w_ / 2 - 20), 40): cr.rectangle(xx, yy, 14, 26); cr.set_source_rgba(0.2, 0.08, 0.05, 0.6); cr.fill()
        if roof: cr.new_path(); cr.move_to(x - w_ / 2 - 10, base - hh); cr.line_to(x, base - hh - w_ * 0.9); cr.line_to(x + w_ / 2 + 10, base - hh); cr.close_path(); cr.set_source_rgb(0.4, 0.15, 0.12); cr.fill()
    tower(540, 900, 300, False)
    for x, w_, h_ in ((180, 140, 520), (360, 110, 430), (540, 180, 640), (720, 110, 430), (900, 140, 520)): tower(x, w_, h_)
    cr.rectangle(-100, base, 1300, 600); cr.set_source_rgb(0.18, 0.32, 0.45); cr.fill()
    for j in range(8): cr.move_to(0, base + 40 + j * 40); [cr.line_to(x, base + 40 + j * 40 + 6 * math.sin(x / 50 + t * 2 + j)) for x in range(0, 1100, 40)]; cr.set_source_rgba(1, 1, 1, 0.15); cr.set_line_width(3); cr.stroke()
    label(cr, 'MALBORK CASTLE', 540, 560, 104, PL_C); ptext(cr, 'TEUTONIC ORDER · 13TH CENTURY · UNESCO', 540, 650, 32, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    ta = at('r6b', 'biggest') - 0.1
    if t >= ta: chip(cr, 'BIGGEST CASTLE BY AREA · 21 HA', 540, 740, 46, GOLD, INK, pop_k(t, ta), 1)
def sc_witcher(cr, t, b, t0, t1):
    arena(cr, t, PL_C); label(cr, 'THE WITCHER', 540, 600, 120, PL_C); ptext(cr, 'CD PROJEKT RED · WARSAW', 540, 690, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    emoji(cr, '🐺', 540, 1050, 260 * pop_k(t, t0 + 0.1), 1); emoji(cr, '⚔️', 300, 1150, 150 * pop_k(t, t0 + 0.3), 1, rot=-0.2); emoji(cr, '🗡️', 780, 1150, 150 * pop_k(t, t0 + 0.4), 1, rot=0.2)
def sc_minecraft(cr, t, b, t0, t1):
    arena(cr, t, SE_C); label(cr, 'MINECRAFT', 540, 600, 130, SE_C); ptext(cr, 'MOJANG · STOCKHOLM · 2011', 540, 690, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    k = prog(t, t0, t0 + 1.0)
    for j in range(24):
        kk = clamp(k * 24 - j)
        if kk <= 0: continue
        x = 180 + (j % 6) * 144; y = 1440 - (j // 6) * 144 - (1 - ease_out(kk)) * 400; top = (j // 6) == 3
        cr.rectangle(x - 70, y - 70, 140, 140); cr.set_source_rgb(*((0.35, 0.7, 0.25) if top else (0.52, 0.36, 0.22))); cr.fill()
        rng = np.random.default_rng(j)
        for _ in range(6): cr.rectangle(x - 70 + rng.integers(0, 5) * 28, y - 70 + rng.integers(0, 5) * 28, 28, 28); cr.set_source_rgba(0, 0, 0, 0.15); cr.fill()
    ts = at('r7b', 'best') - 0.1
    if t >= ts: chip(cr, '300 MILLION+ SOLD · #1 EVER', 540, 800, 50, GOLD, INK, pop_k(t, ts), 1)
def sc_moose(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'SE', (0, 0), (0, -60), 0.6, 0.62, t0, t1 + 1.5, SE_LAND)
    rng = np.random.default_rng(12); k = ease_out(prog(t, t0, at('r8a', 'moose') + 0.3)); m = 0
    while m < int(40 * k):
        lon, lat = rng.uniform(12, 23), rng.uniform(56, 67.5); p = G.p('SE', lon, lat)
        if inside(p, G.c['SE']): x, y = cx + p[0] * s, cy - p[1] * s; emoji(cr, '🫎', x, y, 46, 1); m += 1
    endmap(cr); label(cr, f'≈ {int(300 * k)},000 MOOSE', 540, 620, 96, SE_C)
def sc_bison(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'PL', (0, 0), tuple(G.p('PL', 23.8, 52.7)), 0.95, 2.6, t0, t0 + 1.2, PL_LAND)
    x, y = kpt('PL', 23.8, 52.7, cx, cy, s); pin(cr, x, y, t, t0 + 1.0, (0.2, 0.7, 0.3))
    rng = np.random.default_rng(3)
    for j in range(int(60 * ease_out(prog(t, t0 + 0.6, t0 + 1.6)))):
        r, a = abs(rng.normal(0, 90)), rng.uniform(0, 6.28); cr.new_path(); cr.arc(x + r * math.cos(a), y + r * math.sin(a) * 0.8, 9, 0, 6.28); cr.set_source_rgba(0.1, 0.45, 0.2, 0.85); cr.fill()
    endmap(cr)
    if t >= t0 + 0.8: emoji(cr, '🦬', 540, 1080, 260 * pop_k(t, t0 + 0.8, 0.35), 1)
    label(cr, 'EUROPEAN BISON', 540, 600, 104, PL_C); ptext(cr, 'BIAŁOWIEŻA FOREST', 540, 690, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    th = at('r8b', 'heaviest') - 0.1
    if t >= th: chip(cr, 'UP TO ~900 KG · HEAVIEST IN EUROPE', 540, 1300, 44, GOLD, INK, pop_k(t, th), 1)
SCENE = {'italy': sc_italy, 'size': sc_size, 'sepop': sc_sepop, 'plpop': sc_plpop, 'masuria': sc_masuria, 'selakes': sc_selakes, 'nobel': sc_nobel, 'curie': sc_curie,
         'chopin': sc_chopin, 'abba': sc_abba, 'icehotel': sc_icehotel, 'malbork': sc_malbork, 'witcher': sc_witcher, 'minecraft': sc_minecraft, 'moose': sc_moose, 'bison': sc_bison}

# ---------- hook, title ----------
def rot_rings(rs, c, a):
    ca, sa = math.cos(a), math.sin(a); M = np.array([[ca, -sa], [sa, ca]]); return [(r - c) @ M.T + c for r in rs]
def flip_angle():
    v1, v2 = G.ntip - G.tip, G.rome - G.tip; a = math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
    return (a + math.pi) % (2 * math.pi) - math.pi if abs(a) <= math.pi else a
def draw_hook(cr, t):
    """Cold open: insults, then Sweden flips over at its southern tip and lands near Rome."""
    if t >= bt('title')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        sh_close(cr, t, b1, 'Poland', 0, b1['end'], 'angry'); tf = w('h1', 'flat') - 0.1
        if t >= tf: emoji(cr, '📦', 860, 820, 150 * pop_k(t, tf, 0.3), 1, rot=-0.1 + 0.05 * math.sin(t * 3))
        return True
    if t < b3['start']:
        sx, sy = shake(t, w('h2', 'pierogi') - 0.05, 20, 0.4); cr.save(); cr.translate(sx, sy)
        sh_low(cr, t, b2, 'Sweden', b2['start'], b2['end'], 'angry'); cr.restore()
        tp = w('h2', 'pierogi') - 0.1
        if t >= tp: emoji(cr, '🥟', 860, 820, 150 * pop_k(t, tp, 0.3), 1)
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2)))
        return True
    mid = tuple((G.tip + (G.ntip + G.rome) / 2) / 2 * np.array([1, 1])); ctr0 = (0, 0)
    tf0 = w('h3', 'flip') - 0.1; tf1 = w('h3', 'tip', end=True) + 0.5
    cx, cy, s = mview(cr, t, 'SE', ctr0, tuple(G.tip), 0.62, 0.44, b3['start'], tf0 + 0.6, SE_LAND)
    km_shape(cr, G.pl_in_se, cx, cy, s, PL_LAND, 1, lw=1.5, edge=(0.08, 0.1, 0.16))
    tl = w('h3', 'long') - 0.1
    if t >= tl:  # length ruler
        a_, b_ = kpt_xy(G.tip, cx, cy, s), kpt_xy(G.ntip, cx, cy, s); kk = ease_out(prog(t, tl, tl + 0.5))
        cr.move_to(*a_); cr.line_to(lerp(a_[0], b_[0], kk), lerp(a_[1], b_[1], kk)); cr.set_source_rgb(*GOLD[:3]); cr.set_line_width(8); cr.set_dash([18, 12]); cr.stroke(); cr.set_dash([])
    if t >= tf0:
        a = flip_angle() * ease_io(prog(t, tf0, tf1)); rr = rot_rings(G.c['SE'], G.tip, a)
        km_shape(cr, rr, cx, cy, s, SE_C, 0.75, fill=0.7, lw=3, edge=WHITE)
    x, y = kpt_xy(G.tip, cx, cy, s); pin(cr, x, y, t, tf0, GOLD)
    tr = w('h3', 'Rome') - 0.15
    rx, ry = kpt_xy(G.rome, cx, cy, s); pin(cr, rx, ry, t, tr, (1, 0.35, 0.35))
    if t >= tr: ptext(cr, 'ROME', rx + 110, ry + 14, 44, WHITE, pop_k(t, tr), sw=7)
    endmap(cr)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
    if t >= tl: label(cr, 'SWEDEN: 1,572 KM LONG', 540, 250, 76, SE_C, pop_k(t, tl))
    if t >= tr: sx, sy = shake(t, tr, 18); cr.save(); cr.translate(sx, sy); slam(cr, 'ALL THE WAY TO ROME!', 540, 400, 84, GOLD, t, tr); cr.restore()
    C.draw_captions(cr, t, 1700)
    f = 1 - prog(t, b3['start'], b3['start'] + 0.15)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b3['start'], b3['start'] + 0.2)))
    return True
def kpt_xy(p, cx, cy, s): return cx + p[0] * s, cy - p[1] * s
def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.5))
    ball(cr, 'Sweden', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'Poland', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'SWEDEN', 540, 560, 190, SE_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'POLAND', 540, 980, 190, PL_C, t, w('title', 'winner'))
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
    for side, x, col, sc, lab in (('A', 250, SE_C, sn, 'SWEDEN'), ('U', 830, PL_C, ss, 'POLAND')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = f'ROUND {i}/8' if i else ('FINAL: 4 — 4' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📏', 2: '👥', 3: '🏞️', 4: '🏅', 5: '🎵', 6: '🏰', 7: '🎮', 8: '🦬'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((SE_C, PL_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    head = 'FINAL ROUND' if i == NR else f'ROUND {i}'
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, head, 0, 0, 120 if i == NR else 150, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 860), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = SE_C if win == 'A' else PL_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('SWEDEN' if win == 'A' else 'POLAND') + ' WINS'
    cr.save(); cr.translate(x, 1450); cr.rotate(-0.05 if win == 'A' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 72)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, 72, INK, 1, sw=0, shadow=False); cr.restore()

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
    e1, e2, c = bt('e1'), bt('e2'), bt('cta')
    if t < e2['start']:
        sx, sy = shake(t, e1['l0'], 20, 0.4); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540 + sx, 1100 + sy); set_sweden(cr, t); ball(cr, 'Sweden', 540, 1290, 290, 'shock', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Sweden', 540, 1640, SE_C)
        ptext(cr, '4 — 4', 540, 820, 130, WHITE, pop_k(t, e1['start'] + 0.1), sw=14); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540, 1100); set_poland(cr, t)
        ball(cr, 'Poland', 540, 1260 - h * 50, 300, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Poland', 540, 1640, PL_C); emoji(cr, '🥟', 200, 900, 140 * pop_k(t, e2['l0'] + 0.4), 1)
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.06), 0.02, 540, 1000); arena(cr, t)
    for n, x, lk in (('Sweden', 290, 0.8), ('Poland', 790, -0.8)): ball(cr, n, x, 1280 - abs(math.sin(t * 5 + x)) * 10, 170, 'angry', 0, lk)
    emoji(cr, '⚡', 540, 1280, 140, 1, rot=0.2 * math.sin(t * 10)); cr.restore()
    sx, sy = shake(t, c['start'], 16, 0.4); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A TIE!", 540, 470, 140, GOLD, t, c['start']); cr.restore()
    ptext(cr, 'SWEDEN', 220, 590, 60, SE_C, 1, sw=8); ptext(cr, '4 — 4', 540, 600, 84, WHITE, 1, sw=10); ptext(cr, 'POLAND', 860, 590, 60, PL_C, 1, sw=8)
    tp = w('cta', 'pick') - 0.1
    if t >= tp:
        kk = pop_k(t, tp); cr.save(); cr.translate(540, 730); cr.scale(kk, kk); ptext(cr, 'YOU PICK THE TIEBREAKER', 0, 0, 66, WHITE, 1, sw=9); cr.restore()
        for j, (em, lab) in enumerate((('🍲', 'FOOD?'), ('⚽', 'FOOTBALL?'), ('❄️', 'WINTER?'))):
            tj = tp + 0.4 + j * 0.25
            if t < tj: continue
            x = 220 + j * 320; k2 = pop_k(t, tj); emoji(cr, em, x, 880 + 8 * math.sin(t * 4 + j), 120 * k2, 1); ptext(cr, lab, x, 1010, 40, GOLD, k2, fam='Poppins ExtraBold', sw=6)
    tc = w('cta', 'Comment') - 0.1
    if t >= tc: chip(cr, 'COMMENT THE TIEBREAKER 👇'.replace(' 👇', ''), 540, 1460, 46, WHITE, INK, pop_k(t, tc), 1)
    ts_ = w('cta', 'subscribe') - 0.1
    if t >= ts_: subscribe_button(cr, t, ts_, 540, 1640)

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if draw_hook(cr, t): return
    if key == 'title': draw_title(cr, t); return
    if key in ('e1', 'e2', 'cta'): draw_end(cr, t); hud(cr, t)
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
    boom(0.0, 1.0); rumble(0.0, 1.0, 0.25); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(w('h2', 'pierogi') - 0.05, 0.8)
    whoosh(bt('h3')['start'] - 0.3, 0.3); pop(w('h3', 'long') - 0.1, 0.12, 700); whoosh(w('h3', 'flip') - 0.1, 0.3, 0.9); boom(w('h3', 'tip', end=True) + 0.5, 0.8)
    boom(w('h3', 'Rome') - 0.15, 1.0); whoosh(bt('title')['start'] - 0.35)
    for wd in ('Eight', 'winner', 'geography'): boom(w('title', wd), 0.7)
    horn(w('title', 'geography'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1); pop(tv + 0.55, 0.12, 500)
    for k, sp, _ in LINES:
        if sp and k[0] == 'r': whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
        if k in SHOTS:
            for s0, sh in shot_list(k)[1:]: whoosh(s0 - 0.2, 0.16, 0.22)
    boom(bt('e1')['start'], 0.9); rumble(bt('e1')['start'], 1.0, 0.2); boom(bt('cta')['start'], 0.9); horn(bt('cta')['start'], 0.1)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_swpl'))
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

