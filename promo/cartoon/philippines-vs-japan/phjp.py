# Countryballs: Philippines vs Japan, Jeepney vs Bullet Train (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (bullet trains, the Moon, Skytree, Tokyo...).
# Usage: python3 phjp.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

PH_C, JP_C = hexc('#3D7BFF')[:3], hexc('#FF4D5E')[:3]
A_C, U_C = PH_C, JP_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Philippines': ('fil-PH-AngeloNeural', '+6%'), 'Japan': ('ja-JP-KeitaNeural', '+2%')}
LINES = [
    ('h1', 'Japan', "Philippines! My trains are never late!"),
    ('h2', 'Philippines', "And my jeepneys are never empty!"),
    ('h3', None, "Japan's bullet trains hit three hundred and twenty kilometres an hour. The jeepney? It has style. So who wins?"),
    ('title', None, "Eight rounds. One winner. Jeepney versus bullet train."),
    ('c1', None, "Round one: transport."),
    ('r1a', 'Philippines', "My jeepneys are the kings of the road! Colourful, and always full!"),
    ('r1b', 'Japan', "My bullet trains go three hundred and twenty kilometres an hour."),
    ('c2', None, "Round two: coastline."),
    ('r2a', 'Japan', "Twenty-nine thousand kilometres of coastline!"),
    ('r2b', 'Philippines', "Thirty-six thousand. Way more!"),
    ('c3', None, "Round three: volcanoes."),
    ('r3a', 'Philippines', "I have twenty-four active volcanoes!"),
    ('r3b', 'Japan', "I have one hundred and eleven."),
    ('c4', None, "Round four: youngest."),
    ('r4a', 'Japan', "My average age is almost fifty."),
    ('r4b', 'Philippines', "Mine is twenty-seven! Young and wild!"),
    ('c5', None, "Round five: mountains."),
    ('r5a', 'Philippines', "Mount Apo, two thousand nine hundred and fifty-four metres!"),
    ('r5b', 'Japan', "Mount Fuji. Three thousand seven hundred and seventy-six."),
    ('c6', None, "Round six: bananas."),
    ('r6a', 'Japan', "I love bananas!"),
    ('r6b', 'Philippines', "Most of your bananas come from me!"),
    ('c7', None, "Round seven: living longer."),
    ('r7a', 'Philippines', "Filipinos live to about seventy-one."),
    ('r7b', 'Japan', "Japanese live to eighty-four. Among the longest on Earth."),
    ('c8', None, "Final round: Christmas."),
    ('r8a', 'Japan', "On Christmas, I eat fried chicken!"),
    ('r8b', 'Philippines', "I start Christmas in September! The longest Christmas on Earth!"),
    ('e1', 'Philippines', "Four all?!"),
    ('e2', 'Japan', "Then let the viewers decide."),
    ('cta', None, "It's a tie! You pick the tiebreaker. Comment it below, and subscribe to see who wins!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('TRANSPORT', 'U', ('r1b', 'hour')), 2: ('COASTLINE', 'A', ('r2b', 'more')), 3: ('VOLCANOES', 'U', ('r3b', 'eleven')), 4: ('YOUNGEST', 'A', ('r4b', 'wild')),
      5: ('MOUNTAINS', 'U', ('r5b', 'seventy')), 6: ('BANANAS', 'A', ('r6b', 'me')), 7: ('LIVING LONGER', 'U', ('r7b', 'Earth')), 8: ('CHRISTMAS', 'A', ('r8b', 'Earth'))}
NR = 8
SHOTS = {
    'r1a': [(None, 'low'), ('jeepneys', 'map:jeepney')], 'r1b': [(None, 'close'), ('bullet', 'map:shinkansen')],
    'r2a': [(None, 'two'), ('Twenty', 'map:coast_jp')], 'r2b': [(None, 'ots'), ('Thirty', 'map:coast_ph')],
    'r3a': [(None, 'close'), ('twenty', 'map:phvolc')], 'r3b': [(None, 'low'), ('one', 'map:jpvolc')],
    'r4a': [(None, 'two'), ('average', 'map:age_jp')], 'r4b': [(None, 'close'), ('twenty', 'map:age_ph')],
    'r5a': [(None, 'low'), ('Apo', 'map:apo')], 'r5b': [(None, 'ots'), ('Fuji', 'map:fuji')],
    'r6a': [(None, 'close'), ('bananas', 'map:bananajp')], 'r6b': [(None, 'two'), ('bananas', 'map:bananaph')],
    'r7a': [(None, 'ots'), ('seventy', 'map:life_ph')], 'r7b': [(None, 'low'), ('eighty', 'map:life_jp')],
    'r8a': [(None, 'two'), ('Christmas', 'map:kfc')], 'r8b': [(None, 'close'), ('September', 'map:sept')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {}}
C.HOT = ('philippines', 'japan', 'jeepney', 'jeepneys', 'bullet', 'trains', 'tie', 'tiebreaker', 'comment', 'subscribe', 'winner', 'wins')
C.TAIL_OVERRIDE = {'h1': 0.12, 'h2': 0.2, 'h3': 0.45, 'title': 0.6, 'e1': 0.3, 'e2': 0.4, 'cta': 3.6, **{f'c{i}': 0.15 for i in range(1, 9)},
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
class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        R = lambda n: [r for r in rings(cf[n]['geometry']) if len(r) > 3]
        self.ref = {'PH': (122.0, 12.0), 'JP': (137.0, 37.0)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('PH', 'Philippines', ['Malaysia', 'Indonesia', 'Taiwan', 'Vietnam', 'Brunei']), ('JP', 'Japan', ['Russia', 'China', 'North Korea', 'South Korea', 'Taiwan'])):
            rs = R(n)
            pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs if nn in cf for r in local(R(nn), *self.ref[k])]
        B.FL['Philippines'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'ph.png')); B.FL['Japan'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'jp.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'Philippines' else 'U'
def col_of(name): return PH_C if name == 'Philippines' else JP_C
def rival_of(name): return 'Japan' if name == 'Philippines' else 'Philippines'
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
def set_of(name, cr, t): (set_philippines if name == 'Philippines' else set_japan)(cr, t)

# ---------- shots ----------
def sh_close(cr, t, b, name, t0, t1, mood='happy'):
    sgn = -1 if name == 'Philippines' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.07 * sgn * (1 if sum(map(ord, b['key'])) % 2 else -1), 540, 1100); set_of(name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1, mood='happy'):
    sgn = -1 if name == 'Philippines' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, mood, 0.04 * h, -sgn * 0.2); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_ots(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Philippines' else 1; h = hop_of(t, b); rv = rival_of(name)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.06), 0.02 * sgn, 540 + lerp(0, -sgn * 40, prog(t, t0, t1)), 1000); set_of(name, cr, t)
    ball(cr, name, 540 + sgn * 150, 1080 - h * 36, 210, 'happy', 0.05 * h, -sgn * 0.6)
    ball(cr, rv, 540 - sgn * 470, 1700, 560, 'angry', 0, sgn * 0.9); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.paint()
    bubble(cr, t, b, 540 + sgn * 150, 520); nametag(cr, name, 540 + sgn * 150, 1340, col_of(name))
def sh_two(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Philippines' else 1; h = hop_of(t, b); rv = rival_of(name)
    pan = lerp(-60, 60, prog(t, t0, t1)) * sgn
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    for n, x in (('Philippines', 290), ('Japan', 790)):
        hh = h if n == name else 0; ball(cr, n, x, 1300 - hh * 40, 220, 'happy' if n == name else 'angry', 0.05 * hh, 0.8 if n == 'Philippines' else -0.8)
    cr.restore()
    sx = (290 if name == 'Philippines' else 790) - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1600, col_of(name))
def sh_react(cr, t, b, name, t0, t1):
    rv = rival_of(name); k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.25, 1.08, k), -0.06 if rv == 'Philippines' else 0.06, 540 + sx, 1080 + sy); set_of(rv, cr, t)
    ball(cr, rv, 540, 1150, 360, 'shock', 0, 0); cr.restore()
    ptext(cr, '?!', 860, 760, 170, GOLD, pop_k(t, t0 + 0.05), sw=14)
    nametag(cr, rv, 540, 1640, col_of(rv))
def sh_map(cr, t, b, name, t0, t1, scene):
    SCENE[scene](cr, t, b, t0, t1)
    sgn = -1 if name == 'Philippines' else 1; h = hop_of(t, b); x = 540 + sgn * 380
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
PH_LAND, JP_LAND = (0.55, 0.8, 0.45), (0.93, 0.9, 0.86)
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
def sc_jeepney(cr, t, b, t0, t1):
    set_philippines(cr, t); cr.set_source_rgba(0, 0, 0.05, 0.25); cr.paint()
    k = ease_out(prog(t, t0, t0 + 0.8)); x = lerp(-500, 540, k) + 6 * math.sin(t * 9); y = 1180 + 4 * abs(math.sin(t * 12))
    cr.save(); cr.translate(x, y)
    rrect(cr, -330, -170, 660, 220, 30); cr.set_source_rgb(0.85, 0.85, 0.88); cr.fill()
    for j, c in enumerate(((0.9, 0.2, 0.25), (1, 0.8, 0.15), (0.2, 0.5, 0.9), (0.25, 0.75, 0.35))): cr.rectangle(-330, -120 + j * 18, 660, 10); cr.set_source_rgb(*c); cr.fill()
    for j in range(5): rrect(cr, -290 + j * 115, -160, 95, 70, 12); cr.set_source_rgb(0.25, 0.35, 0.5); cr.fill()
    for j in range(5): ball(cr, 'Philippines', -242 + j * 115, -128, 30, 'happy', 0, 0)
    rrect(cr, -360, -230, 720, 70, 20); cr.set_source_rgb(0.95, 0.75, 0.15); cr.fill(); ptext(cr, 'PINOY PRIDE', 0, -182, 40, (0.7, 0.1, 0.15), 1, sw=0, shadow=False)
    for j in range(3): emoji(cr, '🐎', -150 + j * 150, -270, 60, 1)
    for wx in (-200, 200): cr.new_path(); cr.arc(wx, 60, 62, 0, 2 * math.pi); cr.set_source_rgb(0.1, 0.1, 0.12); cr.fill(); cr.new_path(); cr.arc(wx, 60, 28, 0, 2 * math.pi); cr.set_source_rgb(0.8, 0.8, 0.85); cr.fill()
    cr.restore()
    label(cr, 'THE JEEPNEY', 540, 560, 120, PH_C); ptext(cr, 'KING OF THE ROAD · ALWAYS FULL', 540, 650, 42, WHITE, 1, fam='Poppins ExtraBold', sw=6)
SHIN = [(130.54, 31.58), (130.42, 33.59), (132.46, 34.40), (135.50, 34.73), (136.88, 35.17), (139.77, 35.68), (140.88, 38.26), (141.15, 39.70), (140.69, 40.83), (140.65, 41.90)]
def sc_shinkansen(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), (0, -100), 0.28, 0.32, t0, t1 + 2, JP_LAND, rot=0.02)
    k = ease_io(prog(t, t0 + 0.1, at('r1b', 'hour') + 0.2)); pts = [kpt('JP', lon, lat, cx, cy, s) for lon, lat in SHIN]; e = rail(cr, pts, k, JP_C, 10)
    if e: emoji(cr, '🚄', e[0], e[1] - 40, 90, 1)
    endmap(cr); kk = ease_out(prog(t, at('r1b', 'three') - 0.2, at('r1b', 'hour'))); label(cr, f'{int(320 * kk)} KM/H', 540, 620, 120, JP_C)
    ptext(cr, 'SHINKANSEN · BULLET TRAIN', 540, 710, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def coastk(cr, t, k_, s0, land, col, t0, t1, key, w0, w1, val):
    cx, cy, s = mview(cr, t, k_, (0, 0), (0, 0), s0, s0 * 1.04, t0, t1 + 1.5, land); k = ease_out(prog(t, at(key, w0) - 0.2, at(key, w1) + 0.3))
    km_shape(cr, G.c[k_], cx, cy, s, col, 0.5 + 0.5 * k, fill=0.0, lw=4 + 4 * k, edge=col, glow=True); endmap(cr)
    label(cr, f'{int(val * k):,} KM', 540, 620, 110, col); ptext(cr, 'OF COASTLINE (CIA)', 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_coast_jp(cr, t, b, t0, t1): coastk(cr, t, 'JP', 0.28, JP_LAND, JP_C, t0, t1, 'r2a', 'Twenty', 'coastline', 29751)
def sc_coast_ph(cr, t, b, t0, t1):
    coastk(cr, t, 'PH', 0.48, PH_LAND, PH_C, t0, t1, 'r2b', 'Thirty', 'thousand', 36289)
    tm = at('r2b', 'more') - 0.1
    if t >= tm: chip(cr, '36,289  vs  29,751', 540, 800, 50, GOLD, INK, pop_k(t, tm), 1)
VOLC = [('MAYON', 13.257, 123.685), ('TAAL', 14.002, 120.993), ('PINATUBO', 15.13, 120.35), ('', 10.412, 123.132), ('', 12.77, 124.05), ('', 9.203, 124.673), ('', 18.83, 121.86), ('', 7.0, 125.27), ('', 20.33, 121.95), ('', 11.52, 124.53)]
def sc_phvolc(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'PH', (0, 0), (0, 0), 0.48, 0.5, t0, t1 + 2, PH_LAND)
    for j, (nm, lat, lon) in enumerate(VOLC):
        tj = t0 + 0.2 + j * 0.1
        if t >= tj:
            x, y = kpt('PH', lon, lat, cx, cy, s); emoji(cr, '🌋', x, y - 20, (100 if nm else 60) * pop_k(t, tj), 1)
            if nm: ptext(cr, nm, x + (120 if nm != 'PINATUBO' else -150), y + 10, 34, WHITE, pop_k(t, tj), sw=6)
    endmap(cr); k = ease_out(prog(t, t0, at('r3a', 'active') + 0.3)); label(cr, f'{int(24 * k)} ACTIVE VOLCANOES', 540, 620, 76, (1, 0.5, 0.35))
JPV = [(130.66, 31.59), (131.1, 32.88), (130.3, 32.76), (132.6, 34.4), (138.73, 35.36), (138.53, 36.4), (139.0, 34.7), (139.5, 34.08), (140.03, 37.6), (140.28, 38.14), (140.45, 39.07),
       (140.92, 39.96), (140.88, 40.65), (141.13, 41.3), (140.85, 42.54), (141.17, 42.69), (142.88, 43.42), (143.0, 43.64), (144.0, 43.45), (145.2, 44.13), (138.24, 36.89), (139.7, 32.45), (130.2, 30.44)]
def sc_jpvolc(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), (0, 0), 0.28, 0.3, t0, t1 + 2, JP_LAND)
    k = prog(t, t0 + 0.1, at('r3b', 'eleven') + 0.2)
    for j, (lon, lat) in enumerate(JPV):
        if k * len(JPV) >= j: x, y = kpt('JP', lon, lat, cx, cy, s); emoji(cr, '🌋', x, y - 14, 58 * pop_k(t, t0 + 0.1 + j * 0.06), 1)
    x, y = kpt('JP', 138.73, 35.36, cx, cy, s); ptext(cr, 'FUJI', x + 90, y + 10, 32, WHITE, 1, sw=6) if k > 0.3 else None
    endmap(cr); label(cr, f'{int(111 * clamp(ease_out(k)))} ACTIVE VOLCANOES', 540, 620, 76, (1, 0.5, 0.35))
def bars2(cr, t, title, sub, vals, kfun, fmt):
    arena(cr, t); label(cr, title, 540, 600, 72, WHITE); ptext(cr, sub, 540, 680, 30, WHITE, 0.75, fam='Poppins ExtraBold', sw=5)
    vmax = max(v for _, v in vals)
    for j, (n, v) in enumerate(vals):
        k = kfun(n); x = 330 + j * 420
        if k <= 0: ball(cr, n, x, 1290, 62, 'happy', 0, 0); continue
        hh = max(12, 380 * v / vmax * k); rrect(cr, x - 120, 1200 - hh, 240, hh, 22); cr.set_source_rgb(*col_of(n)); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
        ptext(cr, fmt(v), x, 1200 - hh - 28, 64, WHITE, clamp(k * 2), sw=8); ball(cr, n, x, 1290, 62, 'happy', 0, 0)
def kspan(t, key, wd): a = at(key, wd) - 0.2; return ease_out(prog(t, a, a + 0.9))
def sc_age_jp(cr, t, b, t0, t1): bars2(cr, t, 'MEDIAN AGE', 'YOUNGER WINS', [('Philippines', 27.1), ('Japan', 49.9)], lambda n: kspan(t, 'r4a', 'fifty') if n == 'Japan' else 0, lambda v: f'{v:.1f}')
def sc_age_ph(cr, t, b, t0, t1):
    bars2(cr, t, 'MEDIAN AGE', 'YOUNGER WINS', [('Philippines', 27.1), ('Japan', 49.9)], lambda n: 1 if n == 'Japan' else kspan(t, 'r4b', 'twenty'), lambda v: f'{v:.1f}')
    tw0 = at('r4b', 'Young') - 0.1
    if t >= tw0: chip(cr, 'YOUNG AND WILD!', 540, 745, 52, GOLD, INK, pop_k(t, tw0), 1)
def mountain(cr, x, base, h, col, snow, k):
    hh = h * k; cr.new_path(); cr.move_to(x - 230, base); cr.line_to(x, base - hh); cr.line_to(x + 230, base); cr.close_path(); cr.set_source_rgb(*col); cr.fill()
    if snow and k > 0.5: cr.new_path(); cr.move_to(x - 70, base - hh * 0.7); cr.line_to(x, base - hh); cr.line_to(x + 70, base - hh * 0.7); cr.line_to(x + 30, base - hh * 0.75); cr.line_to(x, base - hh * 0.68); cr.line_to(x - 35, base - hh * 0.76); cr.close_path(); cr.set_source_rgb(0.97, 0.98, 1); cr.fill()
def sc_mtn(cr, t, b, t0, t1, final=False):
    arena(cr, t); label(cr, 'TALLEST MOUNTAIN', 540, 600, 84, WHITE); base = 1230; sc_ = 480 / 3776
    ka = kspan(t, 'r5a', 'two') if not final else 1; kf = kspan(t, 'r5b', 'three') if final else 0
    mountain(cr, 330, base, 2954 * sc_, (0.25, 0.55, 0.3), False, ka); mountain(cr, 750, base, 3776 * sc_, (0.4, 0.42, 0.55), True, kf)
    if ka > 0: ptext(cr, 'APO · 2,954 M', 330, base - 2954 * sc_ * ka - 30, 44, WHITE, clamp(ka * 2), sw=7)
    if kf > 0: ptext(cr, 'FUJI · 3,776 M', 750, base - 3776 * sc_ * kf - 30, 44, WHITE, clamp(kf * 2), sw=7)
    ball(cr, 'Philippines', 330, 1310, 62, 'happy', 0, 0); ball(cr, 'Japan', 750, 1310, 62, 'happy', 0, 0)
def sc_apo(cr, t, b, t0, t1): sc_mtn(cr, t, b, t0, t1, False)
def sc_fuji(cr, t, b, t0, t1): sc_mtn(cr, t, b, t0, t1, True)
def sc_bananajp(cr, t, b, t0, t1):
    set_japan(cr, t); cr.set_source_rgba(0, 0, 0.05, 0.3); cr.paint()
    for j in range(9): emoji(cr, '🍌', 200 + (j % 3) * 340, 950 + (j // 3) * 170 + 10 * math.sin(t * 3 + j), 110 * pop_k(t, t0 + j * 0.06), 1, rot=0.3 * math.sin(j))
    label(cr, 'JAPAN LOVES BANANAS', 540, 600, 84, JP_C)
def sc_bananaph(cr, t, b, t0, t1):
    ocean(cr, t); k = ease_io(prog(t, t0 + 0.2, t0 + 1.6))
    ball(cr, 'Philippines', 250, 1300, 130, 'happy', 0, 0); ball(cr, 'Japan', 830, 820, 130, 'shock' if k > 0.9 else 'happy', 0, 0)
    for j in range(10):
        f = (k * 1.4 - j * 0.04)
        if 0 < f < 1: x = lerp(250, 830, f); y = lerp(1300, 820, f) - 260 * math.sin(math.pi * f); emoji(cr, '🍌', x, y, 80, 1, rot=f * 8)
    label(cr, 'MADE IN THE PHILIPPINES', 540, 560, 76, PH_C); tm = at('r6b', 'Most') - 0.1
    if t >= tm: chip(cr, "MOST OF JAPAN'S BANANA IMPORTS", 540, 660, 46, GOLD, INK, pop_k(t, tm), 1)
def sc_life_ph(cr, t, b, t0, t1): bars2(cr, t, 'LIFE EXPECTANCY', 'YEARS', [('Philippines', 71.0), ('Japan', 84.1)], lambda n: kspan(t, 'r7a', 'seventy') if n == 'Philippines' else 0, lambda v: f'~{v:.0f}' if v < 72 else f'{v:.1f}')
def sc_life_jp(cr, t, b, t0, t1):
    bars2(cr, t, 'LIFE EXPECTANCY', 'YEARS', [('Philippines', 71.0), ('Japan', 84.1)], lambda n: 1 if n == 'Philippines' else kspan(t, 'r7b', 'eighty'), lambda v: f'~{v:.0f}' if v < 72 else f'{v:.1f}')
    tl = at('r7b', 'longest') - 0.1
    if t >= tl: chip(cr, 'AMONG THE LONGEST ON EARTH', 540, 745, 46, GOLD, INK, pop_k(t, tl), 1)
def sc_kfc(cr, t, b, t0, t1):
    set_japan(cr, t); cr.set_source_rgba(0, 0, 0.05, 0.35); cr.paint()
    emoji(cr, '🎄', 300, 1080, 260 * pop_k(t, t0 + 0.1), 1); emoji(cr, '🍗', 740, 1040, 220 * pop_k(t, t0 + 0.4), 1, rot=-0.2); emoji(cr, '🪣', 740, 1260, 160 * pop_k(t, t0 + 0.6), 1)
    label(cr, 'CHRISTMAS IN JAPAN:', 540, 560, 76, WHITE); label(cr, 'FRIED CHICKEN!', 540, 660, 96, JP_C)
    chip(cr, 'A FAMOUS TRADITION SINCE 1974', 540, 1250, 44, GOLD, INK, pop_k(t, t0 + 0.8), 1) if t >= t0 + 0.8 else None
def sc_sept(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.05, 0.05, 0.2); g.add_color_stop_rgb(1, 0.25, 0.05, 0.15); cr.set_source(g); cr.paint()
    for j in range(30):
        x = (j * 137) % 1080; y = (j * 211) % 1700 + 100; cr.new_path(); cr.arc(x, y, 6, 0, 2 * math.pi); cr.set_source_rgba(*((1, 0.85, 0.3) if j % 2 else (1, 0.3, 0.35)), 0.5 + 0.5 * math.sin(t * 4 + j)); cr.fill()
    months = ('SEP', 'OCT', 'NOV', 'DEC'); ts = at('r8b', 'September') - 0.1
    for j, m in enumerate(months):
        tj = ts + j * 0.35
        if t < tj: continue
        x = 170 + j * 247; k = pop_k(t, tj); cr.save(); cr.translate(x, 1000); cr.scale(k, k)
        rrect(cr, -100, -110, 200, 220, 24); cr.set_source_rgb(1, 1, 1); cr.fill(); rrect(cr, -100, -110, 200, 60, 24); cr.set_source_rgb(0.85, 0.15, 0.2); cr.fill()
        ptext(cr, m, 0, -64, 40, WHITE, 1, sw=0, shadow=False); emoji(cr, '⭐' if j < 3 else '🎄', 0, 30, 100, 1); cr.restore()
    label(cr, 'CHRISTMAS STARTS', 540, 600, 84, PH_C); label(cr, 'IN SEPTEMBER!', 540, 700, 84, GOLD)
    tl = at('r8b', 'longest') - 0.1
    if t >= tl: chip(cr, 'THE LONGEST CHRISTMAS SEASON ON EARTH', 540, 1260, 38, GOLD, INK, pop_k(t, tl), 1)

SCENE = {'jeepney': sc_jeepney, 'shinkansen': sc_shinkansen, 'coast_jp': sc_coast_jp, 'coast_ph': sc_coast_ph, 'phvolc': sc_phvolc, 'jpvolc': sc_jpvolc, 'age_jp': sc_age_jp, 'age_ph': sc_age_ph,
         'apo': sc_apo, 'fuji': sc_fuji, 'bananajp': sc_bananajp, 'bananaph': sc_bananaph, 'life_ph': sc_life_ph, 'life_jp': sc_life_jp, 'kfc': sc_kfc, 'sept': sc_sept}

# ---------- hook, close-ups, title ----------
def jeep(cr, x, y, s):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    rrect(cr, -160, -90, 320, 110, 18); cr.set_source_rgb(0.85, 0.85, 0.88); cr.fill()
    for j, c in enumerate(((0.9, 0.2, 0.25), (1, 0.8, 0.15), (0.2, 0.5, 0.9))): cr.rectangle(-160, -60 + j * 12, 320, 7); cr.set_source_rgb(*c); cr.fill()
    rrect(cr, -175, -120, 350, 40, 12); cr.set_source_rgb(0.95, 0.75, 0.15); cr.fill()
    for wx in (-100, 100): cr.new_path(); cr.arc(wx, 25, 32, 0, 2 * math.pi); cr.set_source_rgb(0.1, 0.1, 0.12); cr.fill()
    for j in range(4): ball(cr, 'Philippines', -120 + j * 80, -80, 18, 'happy', 0, 0)
    cr.restore()
def train(cr, x, y, s):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.new_path(); cr.move_to(-500, -60); cr.line_to(150, -60); cr.curve_to(300, -60, 330, 30, 330, 50); cr.line_to(-500, 50); cr.close_path(); cr.set_source_rgb(0.97, 0.97, 0.98); cr.fill()
    cr.rectangle(-500, 10, 820, 14); cr.set_source_rgb(0.15, 0.35, 0.75); cr.fill()
    for j in range(7): rrect(cr, -470 + j * 85, -40, 60, 30, 8); cr.set_source_rgb(0.2, 0.25, 0.35); cr.fill()
    cr.restore()
def draw_hook(cr, t):
    if t >= bt('title')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        sh_close(cr, t, b1, 'Japan', 0, b1['end'], 'angry'); emoji(cr, '🚄', 860, 820, 140 * pop_k(t, b1['l0'], 0.3), 1); return True
    if t < b3['start']:
        sx, sy = shake(t, w('h2', 'empty') - 0.05, 20, 0.4); cr.save(); cr.translate(sx, sy); sh_low(cr, t, b2, 'Philippines', b2['start'], b2['end'], 'angry'); cr.restore()
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2))); return True
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.4, 0.7, 0.98); g.add_color_stop_rgb(0.6, 0.9, 0.95, 1); g.add_color_stop_rgb(1, 0.45, 0.45, 0.5); cr.set_source(g); cr.paint()
    cr.new_path(); cr.move_to(500, 1000); cr.line_to(800, 640); cr.line_to(1100, 1000); cr.close_path(); cr.set_source_rgb(0.5, 0.5, 0.65); cr.fill()
    cr.new_path(); cr.move_to(720, 735); cr.line_to(800, 640); cr.line_to(880, 735); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill()
    for y in (1080, 1480): cr.rectangle(0, y, W, 16); cr.set_source_rgb(0.3, 0.3, 0.35); cr.fill()
    cr.rectangle(0, 1500, W, 420); cr.set_source_rgb(0.35, 0.35, 0.4); cr.fill()
    tb = w('h3', 'bullet') - 0.2; tj = w('h3', 'jeepney') - 0.2
    if t >= tb:
        k = prog(t, tb, tb + 0.9); x = lerp(-900, 2200, k)
        if k < 1:
            for j in range(6): cr.rectangle(x - 900 - j * 80, 1010 + j * 10, 400, 4); cr.set_source_rgba(1, 1, 1, 0.5); cr.fill()
        train(cr, x, 1030, 1.4); label(cr, '320 KM/H', 540, 860, 120, JP_C, clamp(prog(t, tb, tb + 0.2)))
    if t >= tj:
        jeep(cr, lerp(-200, 420, ease_out(prog(t, tj, tj + 2.0))), 1430 + 4 * abs(math.sin(t * 12)), 1.3)
        ts = w('h3', 'style') - 0.1
        if t >= ts: chip(cr, 'STYLE: 100%', 540, 1640, 54, GOLD, INK, pop_k(t, ts), 1)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.8); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
    tw_ = w('h3', 'wins') - 0.1
    if t >= tw_: sx, sy = shake(t, tw_, 16); cr.save(); cr.translate(sx, sy); slam(cr, 'WHO WINS?', 540, 380, 140, WHITE, t, tw_); cr.restore()
    C.draw_captions(cr, t, 1800)
    f = 1 - prog(t, b3['start'], b3['start'] + 0.15)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
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
    ball(cr, 'Philippines', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'Japan', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'PHILIPPINES', 540, 560, 150, PH_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'JAPAN', 540, 980, 190, JP_C, t, w('title', 'winner'))
    tg = w('title', 'Jeepney')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'JEEPNEY vs BULLET TRAIN', 540, 1170, 74, WHITE, t, tg); cr.restore()
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
    for side, x, col, sc, lab in (('A', 250, PH_C, sn, 'PHILIPPINES'), ('U', 830, JP_C, ss, 'JAPAN')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = f'ROUND {i}/8' if i else ('FINAL: 4 — 4' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '🚄', 2: '🏖️', 3: '🌋', 4: '🎂', 5: '⛰️', 6: '🍌', 7: '❤️', 8: '🎄'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((PH_C, JP_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
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
    col = PH_C if win == 'A' else JP_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('PHILIPPINES' if win == 'A' else 'JAPAN') + ' WINS'
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
        sx, sy = shake(t, e1['l0'], 20, 0.4); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540 + sx, 1100 + sy); set_philippines(cr, t); ball(cr, 'Philippines', 540, 1290, 290, 'shock', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Philippines', 540, 1640, PH_C)
        ptext(cr, '4 — 4', 540, 820, 130, WHITE, pop_k(t, e1['start'] + 0.1), sw=14); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540, 1100); set_japan(cr, t)
        ball(cr, 'Japan', 540, 1260 - h * 50, 300, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Japan', 540, 1640, JP_C); emoji(cr, '🙇', 200, 900, 140 * pop_k(t, e2['l0'] + 0.4), 1)
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.06), 0.02, 540, 1000); arena(cr, t)
    for n, x, lk in (('Philippines', 290, 0.8), ('Japan', 790, -0.8)): ball(cr, n, x, 1280 - abs(math.sin(t * 5 + x)) * 10, 170, 'angry', 0, lk)
    emoji(cr, '⚡', 540, 1280, 140, 1, rot=0.2 * math.sin(t * 10)); cr.restore()
    sx, sy = shake(t, c['start'], 16, 0.4); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A TIE!", 540, 470, 140, GOLD, t, c['start']); cr.restore()
    ptext(cr, 'PHILIPPINES', 210, 590, 46, PH_C, 1, sw=8); ptext(cr, '4 — 4', 540, 600, 84, WHITE, 1, sw=10); ptext(cr, 'JAPAN', 860, 590, 60, JP_C, 1, sw=8)
    tp = w('cta', 'pick') - 0.1
    if t >= tp:
        kk = pop_k(t, tp); cr.save(); cr.translate(540, 730); cr.scale(kk, kk); ptext(cr, 'YOU PICK THE TIEBREAKER', 0, 0, 66, WHITE, 1, sw=9); cr.restore()
        for j, (em, lab) in enumerate((('🍜', 'FOOD?'), ('🏀', 'BASKETBALL?'), ('🎤', 'KARAOKE?'))):
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
    if key in ('h3c', 'h3j'): close_up(cr, t, key); return
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
    boom(0.0, 1.0); rumble(0.0, 1.0, 0.25); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(w('h2', 'empty') - 0.05, 0.8)
    whoosh(bt('h3')['start'] - 0.3, 0.3); whoosh(w('h3', 'bullet') - 0.2, 0.35, 0.6); boom(w('h3', 'style') - 0.1, 0.6); boom(w('h3', 'wins') - 0.1, 1.0); whoosh(bt('title')['start'] - 0.35)
    for wd in ('Eight', 'winner', 'Jeepney'): boom(w('title', wd), 0.7)
    horn(w('title', 'Jeepney'), 0.09)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_phjp'))
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
