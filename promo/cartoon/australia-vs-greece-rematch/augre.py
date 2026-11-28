# Countryballs: Australia vs Greece, THE REMATCH, the Geography War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (islands, Olympus, olive oil, Melbourne's Greeks...).
# Usage: python3 augre.py <data_dir> <out.mp4> [--preview t1,t2,...]
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
    ('h1', None, "Last time, Greece won the tiebreaker... by being Greece."),
    ('h2', None, "And you all said the same thing: unfair."),
    ('h3j', 'Greece', "I stand by it!"), ('h3c', 'Australia', "Rematch, mate!"),
    ('title', None, "Fine. Best of three. Fair rounds only. This is the rematch."),
    ('c1', None, "Round one: Eurovision."),
    ('r1a', 'Australia', "I came second at Eurovision in twenty sixteen!"),
    ('r1b', 'Greece', "Second? I won it. Two thousand and five!"),
    ('c2', None, "Round two: coastline."),
    ('r2a', 'Greece', "I have the longest coastline in the Mediterranean!"),
    ('r2b', 'Australia', "Mine is about thirty-six thousand kilometres. And that's without the islands!"),
    ('c3', None, "Round three: World Heritage Sites."),
    ('r3a', 'Australia', "I have twenty-one UNESCO World Heritage Sites!"),
    ('r3b', 'Greece', "So do I. Twenty-one. I just added Mount Olympus!"),
    ('c4', None, "One all. Sudden death: happiness."),
    ('r4a', 'Greece', "Greeks know how to enjoy life!"),
    ('r4b', 'Australia', "Maybe. But the World Happiness Report ranks me fifteenth. You're eighty-fifth."),
    ('e1', 'Greece', "Fine. One win each. A decider next time?"),
    ('e2', 'Australia', "You're on, mate!"),
    ('cta', None, "The series is one all. What should the decider be? Comment the topic, and subscribe for part three!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('EUROVISION', 'U', ('r1b', 'five')), 2: ('COASTLINE', 'A', ('r2b', 'islands')), 3: ('WORLD HERITAGE', 'T', ('r3b', 'Olympus')), 4: ('HAPPINESS', 'A', ('r4b', 'eighty'))}
NR = 4
SHOTS = {
    'r1a': [(None, 'low'), ('second', 'map:esc_au')], 'r1b': [(None, 'ots'), ('won', 'map:esc_gr')],
    'r2a': [(None, 'close'), ('longest', 'map:coastgr')], 'r2b': [(None, 'two'), ('thirty', 'map:coastau')],
    'r3a': [(None, 'close'), ('twenty', 'map:unesco_au')], 'r3b': [(None, 'ots'), ('Twenty', 'map:unesco_gr')],
    'r4a': [(None, 'two'), ('enjoy', 'map:taverna')], 'r4b': [(None, 'low'), ('World', 'map:happy')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2')
C.SAY = {None: {}}
C.HOT = ('australia', 'greece', 'unfair', 'rematch', 'tiebreaker', 'greek', 'comment', 'decider', 'fair', 'three', 'sudden', 'death')
C.TAIL_OVERRIDE = {'h1': 0.2, 'h2': 0.35, 'title': 0.6, 'c4': 0.3, 'e2': 0.6, 'cta': 3.2, **{f'c{i}': 0.15 for i in range(1, 4)},
                   **{k: 0.3 for k, s, _ in LINES if s}, **{RD[i][2][0]: 1.1 for i in RD}, 'h3c': 0.25, 'h3j': 0.2}
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
def stage(cr, t, col):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.04, 0.02, 0.12); g.add_color_stop_rgb(1, 0.18, 0.06, 0.3); cr.set_source(g); cr.paint()
    for j in range(6):
        a = math.sin(t * 1.2 + j) * 0.35; x0 = 90 + j * 180; cr.new_path(); cr.move_to(x0, 0); cr.line_to(540 + math.sin(a) * 600 - 90, 1500); cr.line_to(540 + math.sin(a) * 600 + 90, 1500); cr.close_path()
        cr.set_source_rgba(*(col if j % 2 else (1, 1, 1)), 0.12); cr.fill()
    cr.save(); cr.translate(540, 1500); cr.scale(1, 0.22); cr.new_path(); cr.arc(0, 0, 520, 0, 2 * math.pi); cr.restore(); cr.set_source_rgba(*col, 0.45); cr.fill()
def sc_esc_au(cr, t, b, t0, t1):
    stage(cr, t, AU_C); emoji(cr, '🎤', 540, 1080, 230 * pop_k(t, t0), 1, rot=0.15 * math.sin(t * 3))
    label(cr, 'EUROVISION 2016', 540, 620, 90, WHITE); tt = at('r1a', 'twenty') - 0.1
    if t >= tt: chip(cr, 'DAMI IM · 2ND PLACE', 540, 740, 50, AU_C, INK, pop_k(t, tt), 1); emoji(cr, '🥈', 800, 900, 150 * pop_k(t, tt), 1)
def sc_esc_gr(cr, t, b, t0, t1):
    stage(cr, t, GR_C); emoji(cr, '🏆', 540, 1080, 280 * pop_k(t, t0), 1, rot=0.05 * math.sin(t * 3))
    for j in range(24):
        ph = ((t - t0) * 0.5 + j / 24) % 1; cr.new_path(); cr.rectangle((j * 47) % 1080, lerp(500, 1800, ph), 12, 22); cr.set_source_rgba(*((1, 1, 1) if j % 2 else GR_C), 1 - ph); cr.fill()
    label(cr, 'EUROVISION 2005', 540, 620, 90, WHITE); tt = at('r1b', 'Two') - 0.1
    if t >= tt: chip(cr, 'HELENA PAPARIZOU · WINNER', 540, 740, 50, GR_C, INK, pop_k(t, tt), 1)
def trace(cr, rings_, cx, cy, s, k, col):
    tot = sum(len(r) for r in rings_); done = 0; cr.set_line_join(cairo.LINE_JOIN_ROUND)
    for r in rings_:
        m = int(clamp((k * tot - done) / len(r)) * len(r)); done += len(r)
        if m < 2: continue
        for wd, al in ((9, 0.3), (3, 1)):
            cr.new_path(); cr.move_to(cx + r[0, 0] * s, cy - r[0, 1] * s); [cr.line_to(cx + x * s, cy - y * s) for x, y in r[1:m]]; cr.set_source_rgba(*col, al); cr.set_line_width(wd); cr.stroke()
def sc_coastgr(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'GR', (0, 0), (0, 0), 1.3, 1.4, t0, t1 + 1.5, GR_LAND)
    k = ease_io(prog(t, t0, at('r2a', 'Mediterranean') + 0.3)); trace(cr, sorted(G.c['GR'], key=lambda r: -len(r)), cx, cy, s, k, (0.4, 0.85, 1)); endmap(cr)
    label(cr, f'{int(13676 * k):,} KM', 540, 620, 110, GR_C); ptext(cr, 'LONGEST COASTLINE IN THE MEDITERRANEAN', 540, 700, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_coastau(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, -60), 0.2, 0.22, t0, t1 + 1.5, AU_LAND)
    k = ease_io(prog(t, t0, at('r2b', 'kilometres') + 0.3)); trace(cr, [max(G.c['AU'], key=len)], cx, cy, s, k, (1, 1, 1)); endmap(cr)
    label(cr, f'{int(35877 * k):,} KM', 540, 620, 110, AU_C); ptext(cr, 'MAINLAND ONLY', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    ti = at('r2b', 'islands') - 0.1
    if t >= ti: chip(cr, '59,736 KM WITH ISLANDS', 540, 800, 46, GOLD, INK, pop_k(t, ti), 1)
def heritage(cr, t, t0, n, col):
    for j in range(n):
        tj = t0 + j * 0.05
        if t >= tj: emoji(cr, '🏛️' if j % 3 else '🏞️', 180 + (j % 6) * 144, 860 + (j // 6) * 130, 90 * pop_k(t, tj, 0.2), 1)
def sc_unesco_au(cr, t, b, t0, t1):
    arena(cr, t); heritage(cr, t, t0, 21, AU_C); k = ease_out(prog(t, t0, t0 + 1.1)); label(cr, f'{int(21 * k)} SITES', 540, 620, 110, AU_C); ptext(cr, 'UNESCO WORLD HERITAGE', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_unesco_gr(cr, t, b, t0, t1):
    arena(cr, t); heritage(cr, t, t0, 21, GR_C); k = ease_out(prog(t, t0, t0 + 1.1)); label(cr, f'{int(21 * k)} SITES', 540, 620, 110, GR_C); ptext(cr, 'UNESCO WORLD HERITAGE', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    to = at('r3b', 'Olympus') - 0.3
    if t >= to: chip(cr, 'NEW: MOUNT OLYMPUS · JULY 2026', 540, 790, 44, GOLD, INK, pop_k(t, to), 1)
def sc_taverna(cr, t, b, t0, t1):
    set_greece(cr, t); cr.set_source_rgba(0.05, 0.05, 0.1, 0.25); cr.paint()
    for j, em in enumerate(('💃', '🍷', '🥙', '🎶', '🫒')): emoji(cr, em, 160 + j * 190, 1050 + 30 * math.sin(t * 4 + j), 130 * pop_k(t, t0 + j * 0.08), 1, rot=0.2 * math.sin(t * 3 + j))
    label(cr, 'OPA!', 540, 620, 150, GR_C)
def sc_happy(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'WORLD HAPPINESS REPORT 2026', 540, 620, 58, WHITE)
    base, top = 1450, 760
    rrect(cr, 520, top - 20, 40, base - top + 40, 20); cr.set_source_rgba(1, 1, 1, 0.15); cr.fill()
    for rank, col, name, word, side in ((15, AU_C, 'AUSTRALIA', 'fifteenth', -1), (85, GR_C, 'GREECE', 'eighty', 1)):
        tw0 = at('r4b', word) - 0.2
        if t < tw0: continue
        k = ease_out(prog(t, tw0, tw0 + 0.6)); y = lerp(base, top + (base - top) * rank / 140, k); x = 540 + side * 200
        ball(cr, 'Australia' if side < 0 else 'Greece', x, y, 70, 'happy' if side < 0 else 'sad', 0, 0); label(cr, f'#{rank}', x + side * 150, y + 20, 70, col)
    ptext(cr, '#1', 600, top + 10, 34, WHITE, 0.8, fam='Poppins ExtraBold', anchor='l', sw=5); ptext(cr, '#140', 600, base + 10, 34, WHITE, 0.8, fam='Poppins ExtraBold', anchor='l', sw=5)
SCENE = {'esc_au': sc_esc_au, 'esc_gr': sc_esc_gr, 'coastgr': sc_coastgr, 'coastau': sc_coastau, 'unesco_au': sc_unesco_au, 'unesco_gr': sc_unesco_gr, 'taverna': sc_taverna, 'happy': sc_happy}

# ---------- hook, close-ups, title ----------
COMMENTS = ['UNFAIR!!', 'RIGGED', 'obviously Greece has more Greeks', 'that tiebreaker tho', 'REMATCH!', 'Australia got robbed', 'not fair mate', 'won by being Greece lol']
def draw_hook(cr, t):
    """Cold open: a replay of last episode's ending, then the comment section explodes."""
    if t >= bt('h3j')['start']: return False
    b1, b2 = bt('h1'), bt('h2')
    if t < b2['start']:
        cr.save(); cam(cr, push(t, 0, b1['end'], 1.15, 1.0), 0.03, 540, 1100); set_greece(cr, t); ball(cr, 'Greece', 540, 1230, 330, 'happy', 0, 0); cr.restore()
        chip(cr, 'I AM GREECE.', 540, 820, 60, WHITE, INK, 1, 1); ptext(cr, 'LAST EPISODE', 540, 300, 60, WHITE, 0.9, sw=8); ptext(cr, 'GREECE 5 — 4 AUSTRALIA', 540, 400, 66, GR_C, 1, sw=9)
        cr.set_source_rgba(0.6, 0.55, 0.4, 0.18); cr.paint()
        for j in range(30): cr.rectangle(0, (j * 67 + t * 300) % H, W, 2); cr.set_source_rgba(1, 1, 1, 0.06); cr.fill()
        C.draw_captions(cr, t, 1700); return True
    arena(cr, t); sx, sy = shake(t, w('h2', 'unfair') - 0.1, 26, 0.5); cr.save(); cr.translate(sx, sy)
    for j, txt in enumerate(COMMENTS):
        tj = b2['l0'] + j * 0.22
        if t < tj: continue
        y = 560 + (j // 2) * 230 + (j % 2) * 100; k = pop_k(t, tj, 0.25); wd0 = tw(cr, txt, 40, 'Poppins ExtraBold') + 70; x = clamp(300 + (j % 2) * 480 + 40 * math.sin(j * 2.3), wd0 / 2 + 20, W - wd0 / 2 - 20)
        cr.save(); cr.translate(x, y); cr.rotate(0.06 * math.sin(j * 3.1)); cr.scale(k, k); wd = tw(cr, txt, 40, 'Poppins ExtraBold') + 70
        rrect(cr, -wd / 2, -50, wd, 90, 26); cr.set_source_rgb(1, 1, 1); cr.fill(); emoji(cr, '💬', -wd / 2 + 6, -46, 46, 1)
        ptext(cr, txt, 0, 10, 40, INK, 1, fam='Poppins ExtraBold', sw=0, shadow=False); cr.restore()
    cr.restore()
    tu = w('h2', 'unfair') - 0.1
    if t >= tu: slam(cr, 'UNFAIR!', 540, 1560, 170, CRIMSON, t, tu)
    ptext(cr, 'YOUR COMMENTS', 540, 300, 70, GOLD, 1, sw=9)
    streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2)))
    return True
def close_up(cr, t, key):
    b = bt(key); name = SPK[key]
    if key == 'h3c': sh_low(cr, t, b, name, b['start'], b['end'], 'angry')
    else: sh_ots(cr, t, b, name, b['start'], b['end'])
    f = 1 - prog(t, b['start'], b['start'] + 0.12)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.55 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.18)))
def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.5))
    ball(cr, 'Australia', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'Greece', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'AUSTRALIA', 540, 560, 160, A_C, t, w('title', 'Fine'))
    tv = w('title', 'three')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'GREECE', 540, 980, 190, U_C, t, w('title', 'Fair'))
    tg = w('title', 'rematch')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE REMATCH', 540, 1170, 120, CRIMSON, t, tg); cr.restore()
    if t >= w('title', 'Best') - 0.1: chip(cr, 'BEST OF 3 · FAIR ROUNDS ONLY', 540, 1330, 44, WHITE, INK, pop_k(t, w('title', 'Best') - 0.1), 1)
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
        ptext(cr, lab, x, 200, 40, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = ('SUDDEN DEATH' if i == NR else f'ROUND {i}/3') if i else ('REMATCH: FINAL' if t >= bt('e1')['start'] else 'REMATCH')
    ptext(cr, lab, 540, 200, 30, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '🎤', 2: '🌊', 3: '🏛️', 4: '😊'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((AU_C, GR_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    head = 'SUDDEN DEATH' if i == NR else f'ROUND {i}'
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, head, 0, 0, 120 if i == NR else 150, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = (at('c4', 'happiness') - 0.1) if i == NR else b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    if i == NR: ptext(cr, '1 — 1', 540, 600, 90, WHITE, pop_k(t, b['l0']), sw=10)
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = AU_C if win == 'A' else (GR_C if win == 'U' else GOLD[:3]); f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)) if win != 'T' else 540
    txt = {'A': 'AUSTRALIA WINS', 'U': 'GREECE WINS', 'T': "IT'S A TIE! 21 — 21"}[win]
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
        h = hop_of(t, e1); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.12), 0.05, 540, 1100); set_greece(cr, t); ball(cr, 'Greece', 540, 1290 - h * 40, 290, 'neutral', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Greece', 540, 1640, GR_C)
        ptext(cr, 'AUSTRALIA WINS THE REMATCH', 540, 780, 60, AU_C, pop_k(t, e1['start'] + 0.2), sw=10); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), -0.05, 540, 1100); set_australia(cr, t)
        ball(cr, 'Australia', 540, 1260 - h * 50, 320, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Australia', 540, 1640, AU_C); return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.08), 0.02, 540, 1000); arena(cr, t)
    ball(cr, 'Australia', 290, 1300, 200, 'angry', 0, 0.8); ball(cr, 'Greece', 790, 1300, 200, 'angry', 0, -0.8); emoji(cr, '⚡', 540, 1290, 160, 1, rot=0.2 * math.sin(t * 10)); cr.restore()
    ptext(cr, 'SERIES', 540, 860, 60, GOLD, 1, sw=8); ptext(cr, '1 — 1', 540, 1010, 150, WHITE, 1, sw=14)
    tc = w('cta', 'Comment')
    if t >= tc: kk = pop_k(t, tc); cr.save(); cr.translate(540, 470); cr.scale(kk, kk); ptext(cr, 'COMMENT THE DECIDER', 0, 0, 80, WHITE, 1, sw=11); cr.restore()
    tq = w('cta', 'What')
    if t >= tq: kk = pop_k(t, tq); cr.save(); cr.translate(540, 620); cr.scale(kk, kk); ptext(cr, 'WHAT SHOULD PART 3 BE?', 0, 0, 62, GOLD, 1, sw=9); cr.restore()
    ts_ = w('cta', 'subscribe') - 0.1
    if t >= ts_: subscribe_button(cr, t, ts_, 540, 1620)

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if draw_hook(cr, t): return
    if key in ('h3c', 'h3j'): close_up(cr, t, key); return
    if key == 'title': draw_title(cr, t); return
    if key in ('e1', 'e2', 'cta'): draw_end(cr, t); hud(cr, t)
    elif key[0] == 'c': card(cr, t, int(key[1])); hud(cr, t); C.draw_captions(cr, t, 1700) if key == 'c4' else None
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
    boom(0.0, 0.8); rumble(0.0, 0.8, 0.15); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35)
    for j in range(len(COMMENTS)): pop(bt('h2')['l0'] + j * 0.22, 0.1, 800 + 60 * j)
    boom(w('h2', 'unfair') - 0.1, 1.0); horn(w('h2', 'unfair') - 0.1, 0.1)
    for k in ('h3j', 'h3c', 'title'): whoosh(bt(k)['start'] - 0.35)
    for wd in ('Fine', 'Fair', 'rematch'): boom(w('title', wd), 0.7)
    horn(w('title', 'rematch'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1); pop(tv + 0.55, 0.12, 500)
    for k, sp, _ in LINES:
        if sp: whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
        if k in SHOTS:
            for s0, sh in shot_list(k)[1:]: whoosh(s0 - 0.2, 0.16, 0.22)
    boom(at('c4', 'Sudden') - 0.1, 0.9); rumble(at('c4', 'happiness'), 1.2, 0.15)
    boom(bt('e1')['start'], 0.6); boom(bt('cta')['start'], 0.8); cheer(bt('cta')['start'], 0.1, 1.6)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_augre'))
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
