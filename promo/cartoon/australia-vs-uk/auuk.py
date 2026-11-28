# Countryballs: Australia vs the UK, the Geography War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (rain, cricket, the Tube, Stonehenge...).
# Usage: python3 auuk.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

A_C, U_C = hexc('#FFC233')[:3], hexc('#F0435A')[:3]   # Australia gold, UK red
AU_C, UK_C = A_C, U_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Australia': ('en-AU-WilliamNeural', '+4%'), 'UK': ('en-GB-RyanNeural', '+4%')}
LINES = [
    ('h1', 'UK', "Oi, Australia! You're just a big empty beach!"),
    ('h2', 'Australia', "And you're just a big grey cloud, mate!"),
    ('h3', None, "The UK fits inside Australia thirty-one times. But size isn't everything."),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: size."),
    ('r1a', 'UK', "I may be small, but I'm packed with history!"),
    ('r1b', 'Australia', "Cute. I'm thirty-one times bigger than you, mate!"),
    ('c2', None, "Round two: people."),
    ('r2a', 'Australia', "Twenty-eight million Aussies, mate!"),
    ('r2b', 'UK', "Sixty-nine and a half million Brits. London alone has about nine million!"),
    ('c3', None, "Round three: sunshine."),
    ('r3a', 'UK', "We have lovely weather. Sometimes."),
    ('r3b', 'Australia', "Perth gets about three thousand two hundred hours of sunshine a year. London? About sixteen hundred."),
    ('c4', None, "Round four: football."),
    ('r4a', 'Australia', "Our Socceroos have played at seven World Cups!"),
    ('r4b', 'UK', "Seven? England actually won one. Nineteen sixty-six!"),
    ('c5', None, "Round five: cricket."),
    ('r5a', 'UK', "We invented cricket!"),
    ('r5b', 'Australia', "And I've won six Cricket World Cups. You've won one!"),
    ('c6', None, "Round six: trains."),
    ('r6a', 'Australia', "I have the longest straight railway on Earth!"),
    ('r6b', 'UK', "I invented the railway. And London had the world's first underground, in eighteen sixty-three!"),
    ('c7', None, "Round seven: history."),
    ('r7a', 'UK', "Stonehenge is five thousand years old!"),
    ('r7b', 'Australia', "Respect. But Aboriginal cultures go back over sixty-five thousand years. The oldest living culture on Earth."),
    ('c8', None, "Round eight: the GDP war."),
    ('r8a', 'Australia', "My economy is worth about two trillion dollars!"),
    ('r8b', 'UK', "Mine is over four trillion. Cheers!"),
    ('c9', None, "Four all. Tiebreaker: who do people move to?"),
    ('r9a', 'UK', "Loads of Aussies live in London!"),
    ('r9b', 'Australia', "Sure. But over a million Brits live in Australia. Sunshine wins, mate!"),
    ('e1', 'UK', "Fair enough. Fancy a cup of tea?"),
    ('e2', 'Australia', "Only if it's a flat white, mate!"),
    ('cta', None, "Australia, or the UK? Comment your side, and follow for the next battle.")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SIZE', 'A', ('r1b', 'bigger')), 2: ('PEOPLE', 'U', ('r2b', 'nine')), 3: ('SUNSHINE', 'A', ('r3b', 'sixteen')), 4: ('FOOTBALL', 'U', ('r4b', 'Nineteen')),
      5: ('CRICKET', 'A', ('r5b', 'one')), 6: ('TRAINS', 'U', ('r6b', 'underground')), 7: ('HISTORY', 'A', ('r7b', 'Earth')), 8: ('THE GDP WAR', 'U', ('r8b', 'Cheers')),
      9: ('THE BIG MOVE', 'A', ('r9b', 'Sunshine'))}
NR = 9
SHOTS = {
    'r1a': [(None, 'two'), ('history', 'close')], 'r1b': [(None, 'close'), ('thirty', 'map:size')],
    'r2a': [(None, 'low'), ('million', 'map:aupop')], 'r2b': [(None, 'ots'), ('Sixty', 'map:ukpop')],
    'r3a': [(None, 'close'), ('weather', 'map:rain')], 'r3b': [(None, 'two'), ('Perth', 'map:sun')],
    'r4a': [(None, 'close'), ('seven', 'map:socceroos')], 'r4b': [(None, 'low'), ('won', 'map:england66')],
    'r5a': [(None, 'two'), ('cricket', 'map:crickinv')], 'r5b': [(None, 'ots'), ('six', 'map:cricwc')],
    'r6a': [(None, 'close'), ('straight', 'map:rail')], 'r6b': [(None, 'low'), ('London', 'map:tube')],
    'r7a': [(None, 'two'), ('Stonehenge', 'map:stonehenge')], 'r7b': [(None, 'ots'), ('Aboriginal', 'map:culture')],
    'r8a': [(None, 'close'), ('two', 'map:gdpau')], 'r8b': [(None, 'two'), ('four', 'map:gdpuk')],
    'r9a': [(None, 'close'), ('Aussies', 'map:ukmove')], 'r9b': [(None, 'low'), ('million', 'map:move')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {}}
C.HOT = ('australia', 'uk', 'win', 'bigger', 'people', 'war', 'tiebreaker', 'move', 'comment', 'geography', 'winner', 'twice')
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
        self.ref = {'AU': (134.0, -26.0), 'UK': (-2.5, 54.5)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('AU', 'Australia', ['Indonesia', 'Papua New Guinea', 'New Zealand', 'Timor-Leste']),
                          ('UK', 'United Kingdom', ['Ireland', 'UK', 'Belgium', 'Netherlands', 'Norway', 'Denmark', 'Germany', 'Iceland', 'Faeroe Is.'])):
            rs = R(n)
            if k == 'AU': rs = [r for r in rs if 112 < r[:, 0].mean() < 155 and -45 < r[:, 1].mean() < -9]
            else: rs = [r for r in rs if -9 < r[:, 0].mean() < 2 and 49 < r[:, 1].mean() < 61]
            pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs if nn in cf for r in local(R(nn), *self.ref[k])]
        self.uk_true = [r - np.concatenate(self.c['UK']).mean(axis=0) for r in self.c['UK']]
        print('areas M km2: australia', round(area(self.c['AU']) / 1e6, 2), 'uk', round(area(self.c['UK']) / 1e6, 3), 'ratio', round(area(self.c['AU']) / area(self.c['UK']), 1))
        B.FL['Australia'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'au.png')); B.FL['UK'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'gb.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'Australia' else 'U'
def col_of(name): return AU_C if name == 'Australia' else UK_C
def rival_of(name): return 'UK' if name == 'Australia' else 'Australia'
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
def set_uk(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.36, 0.4, 0.48); g.add_color_stop_rgb(0.6, 0.62, 0.66, 0.72); g.add_color_stop_rgb(1, 0.24, 0.26, 0.32); cr.set_source(g); cr.paint()
    for k in range(5):
        cx_ = (k * 300 + t * 20) % 1500 - 200; cr.new_path(); [cr.arc(cx_ + dx, 380 + k % 2 * 120 + dy, r, 0, 2 * math.pi) for dx, dy, r in ((0, 0, 90), (90, -30, 110), (190, 10, 80))]; cr.set_source_rgba(0.82, 0.84, 0.88, 0.8); cr.fill()
    for k in range(8):
        x = -120 + k * 170; h = 220 + 70 * math.sin(k * 2.3); cr.rectangle(x, 1300 - h, 170, h + 200); cr.set_source_rgb(0.32, 0.3, 0.34); cr.fill()
        for c_ in range(3): cr.rectangle(x + 30 + c_ * 45, 1300 - h - 30, 18, 34); cr.fill()
        for r in range(2):
            for c_ in range(3): cr.rectangle(x + 24 + c_ * 46, 1300 - h + 40 + r * 80, 24, 40); cr.set_source_rgba(1, 0.86, 0.55, 0.7 if (k + r + c_) % 3 else 0.2); cr.fill()
            cr.set_source_rgb(0.32, 0.3, 0.34)
    tx = 780  # clock tower silhouette
    cr.rectangle(tx - 60, 620, 120, 700); cr.set_source_rgb(0.22, 0.2, 0.24); cr.fill(); cr.rectangle(tx - 74, 700, 148, 150); cr.fill()
    cr.new_path(); cr.move_to(tx - 70, 620); cr.line_to(tx, 470); cr.line_to(tx + 70, 620); cr.close_path(); cr.fill()
    cr.new_path(); cr.arc(tx, 775, 52, 0, 2 * math.pi); cr.set_source_rgb(0.95, 0.9, 0.7); cr.fill()
    hr = (t * 0.2) % (2 * math.pi)
    for a_, L in ((hr, 30), (hr * 12, 44)): cr.move_to(tx, 775); cr.line_to(tx + L * math.sin(a_), 775 - L * math.cos(a_)); cr.set_source_rgb(0.1, 0.1, 0.12); cr.set_line_width(5); cr.stroke()
    cr.rectangle(120, 1180, 80, 160); cr.set_source_rgb(0.85, 0.12, 0.15); cr.fill(); cr.rectangle(132, 1200, 56, 60); cr.set_source_rgba(1, 1, 0.9, 0.6); cr.fill()
    cr.rectangle(-200, 1330, 1500, 800); cr.set_source_rgb(0.2, 0.21, 0.25); cr.fill()
    cr.set_line_width(2)
    for j in range(70):
        x = (j * 83 + 30 * math.sin(j)) % 1100; y = ((t * 900 + j * 211) % 2000) - 100; cr.move_to(x, y); cr.line_to(x - 8, y + 34); cr.set_source_rgba(0.85, 0.9, 1, 0.5); cr.stroke()
def set_of(name, cr, t): (set_australia if name == 'Australia' else set_uk)(cr, t)

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
    for n, x in (('Australia', 290), ('UK', 790)):
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
AU_LAND, UK_LAND = (0.86, 0.5, 0.24), (0.82, 0.86, 0.8)
def rail(cr, pts, k, col, wd):
    if k <= 0 or len(pts) < 2: return
    seg = [math.hypot(b_[0] - a[0], b_[1] - a[1]) for a, b_ in zip(pts, pts[1:])]; tot = sum(seg); L = tot * k
    cr.new_path(); cr.move_to(*pts[0]); done = 0; end = pts[0]
    for (a, b_), sl in zip(zip(pts, pts[1:]), seg):
        if done + sl >= L: f = (L - done) / max(sl, 1e-9); end = (lerp(a[0], b_[0], f), lerp(a[1], b_[1], f)); cr.line_to(*end); break
        cr.line_to(*b_); done += sl; end = b_
    cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_source_rgba(*col, 0.3); cr.set_line_width(wd * 3); cr.stroke_preserve(); cr.set_source_rgb(*col); cr.set_line_width(wd); cr.stroke(); return end
def sc_size(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, -100), 0.2, 0.22, t0, t1 + 1.5, AU_LAND)
    k = ease_out(prog(t, t0, t0 + 0.5)); cr.save(); cr.translate(0, (1 - k) * -900); km_shape(cr, G.uk_true, cx, cy, s, UK_LAND, 1, 300, 300, fill=0.95, lw=3, edge=INK); cr.restore()
    if k >= 1: chip(cr, 'UK', cx + 300 * s, cy - 300 * s + 170, 30, WHITE, INK, 1, 1)
    endmap(cr)
    tx = at('r1b', 'thirty') + 0.4
    if t >= tx: sx, sy = shake(t, tx, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'AUSTRALIA = 31 UKs', 540, 640, 90, WHITE, t, tx); cr.restore()
CITIES = [('SYDNEY', 151.21, -33.87, 5.5), ('MELBOURNE', 144.96, -37.81, 5.3), ('BRISBANE', 153.03, -27.47, 2.8), ('PERTH', 115.86, -31.95, 2.4), ('ADELAIDE', 138.6, -34.93, 1.5)]
def sc_aupop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (150, -300), 0.2, 0.24, t0, t1 + 2, AU_LAND)
    for j, (nm, lon, lat, m) in enumerate(CITIES):
        x, y = kpt('AU', lon, lat, cx, cy, s); tj = t0 + 0.2 + j * 0.15
        if t >= tj:
            k = pop_k(t, tj); cr.new_path(); cr.arc(x, y, 16 * math.sqrt(m) * k, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.85); cr.fill()
            if j < 4: ptext(cr, nm, x + (-120 if lon > 140 else 110), y + 10, 30, WHITE, k, fam='Poppins ExtraBold', sw=5)
    endmap(cr); k = ease_out(prog(t, t0, t0 + 1)); label(cr, f'{28 * k:.0f} MILLION', 540, 620, 100, AU_C)
UKC = [('LONDON', -0.13, 51.51, 9.0), ('BIRMINGHAM', -1.9, 52.48, 2.9), ('MANCHESTER', -2.24, 53.48, 2.8), ('GLASGOW', -4.25, 55.86, 1.7), ('LEEDS', -1.55, 53.8, 1.9), ('BELFAST', -5.93, 54.6, 0.7), ('CARDIFF', -3.18, 51.48, 0.5), ('EDINBURGH', -3.19, 55.95, 0.9)]
def sc_ukpop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'UK', (0, 0), (50, -150), 0.85, 1.0, t0, t1 + 2, UK_LAND)
    for j, (nm, lon, lat, m) in enumerate(UKC):
        x, y = kpt('UK', lon, lat, cx, cy, s); tj = t0 + 0.2 + j * 0.1
        if t >= tj: k = pop_k(t, tj); cr.new_path(); cr.arc(x, y, 14 * math.sqrt(m) * k, 0, 2 * math.pi); cr.set_source_rgba(*UK_C, 0.85); cr.fill()
    lx, ly = kpt('UK', -0.13, 51.51, cx, cy, s); tl = at('r2b', 'London') - 0.1; pin(cr, lx, ly, t, tl, WHITE); endmap(cr)
    k = ease_out(prog(t, t0, t0 + 1)); label(cr, f'{69.5 * k:.1f} MILLION', 540, 620, 100, UK_C)
    if t >= tl: chip(cr, 'LONDON ≈ 9 MILLION', 540, 730, 46, WHITE, INK, pop_k(t, tl), 1)
def sc_rain(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'UK', (0, 0), (0, -50), 0.85, 0.95, t0, t1 + 2, UK_LAND); endmap(cr)
    for j in range(6):
        x = (j * 190 + (t - t0) * 60) % 1200 - 60; y = 760 + (j % 3) * 230; emoji(cr, '🌧️', x, y, 150, 0.95)
    cr.set_line_width(3)
    for j in range(90):
        x = (j * 61) % 1100; y = ((t * 1100 + j * 197) % 1300) + 600; cr.move_to(x, y); cr.line_to(x - 10, y + 40); cr.set_source_rgba(0.75, 0.85, 1, 0.6); cr.stroke()
    label(cr, 'BRITISH WEATHER', 540, 620, 96, (0.8, 0.88, 1))
def sun_bar(cr, x, base, val, hmax, k, col, name, lab):
    hh = max(8, hmax * val / 3300 * k); rrect(cr, x - 100, base - hh, 200, hh, 18); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    label(cr, lab, x, base - hh - 24, 54, WHITE, clamp(k * 2)); ptext(cr, name, x, base + 46, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6); return base - hh
def sc_sun(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'SUNSHINE HOURS PER YEAR', 540, 620, 56, WHITE)
    k = ease_out(prog(t, at('r3b', 'three') - 0.2, at('r3b', 'hundred') + 0.3)); top = sun_bar(cr, 330, 1250, 3200, 520, k, AU_C, 'PERTH', f'{int(3200 * k):,}')
    if k > 0: emoji(cr, '☀️', 480, top - 40, 110, 1, rot=t * 0.6)
    tl = at('r3b', 'London') - 0.1
    if t >= tl:
        k2 = ease_out(prog(t, tl, at('r3b', 'sixteen') + 0.3)); top = sun_bar(cr, 750, 1250, 1600, 520, k2, UK_C, 'LONDON', f'{int(1600 * k2):,}')
        emoji(cr, '🌧️', 900, top - 40, 110, 1)
def sc_socceroos(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.1, 0.45, 0.2); g.add_color_stop_rgb(1, 0.05, 0.28, 0.12); cr.set_source(g); cr.paint()
    cr.set_source_rgba(1, 1, 1, 0.5); cr.set_line_width(6); cr.new_path(); cr.arc(540, 1000, 180, 0, 2 * math.pi); cr.stroke(); cr.move_to(0, 1000); cr.line_to(1080, 1000); cr.stroke()
    for j, yr in enumerate((1974, 2006, 2010, 2014, 2018, 2022, 2026)):
        tj = t0 + 0.1 + j * 0.12
        if t < tj: continue
        x, y = 180 + (j % 4) * 240, 880 + (j // 4) * 260; k = pop_k(t, tj); emoji(cr, '⚽', x, y, 130 * k, 1, rot=t * 2 + j); ptext(cr, str(yr), x, y + 110, 40, WHITE, k, sw=7)
    label(cr, '7 WORLD CUPS', 540, 620, 110, AU_C); ptext(cr, 'THE SOCCEROOS', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_england66(cr, t, b, t0, t1):
    set_uk(cr, t); cr.set_source_rgba(0.05, 0.05, 0.1, 0.45); cr.paint()
    k = pop_k(t, t0, 0.35); emoji(cr, '🏆', 540, 1050, 380 * k, 1, rot=0.05 * math.sin(t * 3))
    for j in range(16):
        ph = ((t - t0) * 0.5 + j / 16) % 1; cr.new_path(); cr.rectangle((j * 71) % 1080, lerp(500, 1800, ph), 14, 24); cr.set_source_rgba(*((1, 1, 1) if j % 2 else UK_C), 1 - ph); cr.fill()
    ty = at('r4b', 'Nineteen') - 0.1
    if t >= ty: slam(cr, '1966', 540, 1400, 200, GOLD, t, ty)
    label(cr, 'ENGLAND: WORLD CHAMPIONS', 540, 620, 60, UK_C)
def sc_crickinv(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'UK', (0, 0), tuple(G.p('UK', -1.5, 52.5)), 0.85, 1.4, t0, t0 + 1.2, UK_LAND); endmap(cr)
    emoji(cr, '🏏', 540, 1080, 260 * pop_k(t, t0 + 0.6), 1, rot=-0.3 + 0.15 * math.sin(t * 4))
    label(cr, 'CRICKET', 540, 620, 110, WHITE); ptext(cr, 'BORN IN ENGLAND', 540, 700, 40, UK_C, 1, fam='Poppins ExtraBold', sw=6)
def sc_cricwc(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'CRICKET WORLD CUPS (MEN)', 540, 620, 60, WHITE)
    for j, yr in enumerate((1987, 1999, 2003, 2007, 2015, 2023)):
        tj = at('r5b', 'six') + j * 0.1
        if t >= tj: x = 170 + j * 148; emoji(cr, '🏆', x, 860, 110 * pop_k(t, tj), 1); ptext(cr, str(yr), x, 950, 30, WHITE, 1, fam='Poppins ExtraBold', sw=5)
    ptext(cr, 'AUSTRALIA 6', 540, 1040, 60, AU_C, 1, sw=8)
    to = at('r5b', 'one') - 0.1
    if t >= to: emoji(cr, '🏆', 540, 1180, 110 * pop_k(t, to), 1); ptext(cr, '2019', 540, 1270, 30, WHITE, 1, fam='Poppins ExtraBold', sw=5); ptext(cr, 'ENGLAND 1', 540, 1350, 60, UK_C, 1, sw=8)
def sc_rail(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 129.5, -30.6)), 0.2, 0.55, t0, t0 + 1.2, AU_LAND)
    full = [kpt('AU', lon, lat, cx, cy, s) for lon, lat in ((121.47, -30.75), (123.4, -30.9), (126.6, -30.9), (131.8, -30.45), (134.6, -30.6), (137.77, -32.49))]
    rail(cr, full, 1, (0.3, 0.28, 0.3), 5)
    k = ease_io(prog(t, t0 + 0.9, b['l1'] + 0.2)); a, z = kpt('AU', 126.6, -30.9, cx, cy, s), kpt('AU', 131.8, -30.45, cx, cy, s)
    e = rail(cr, [a, z], k, WHITE[:3], 9)
    if e: emoji(cr, '🚂', e[0], e[1] - 40, 80, 1)
    endmap(cr); label(cr, f'{int(478 * k)} KM', 540, 620, 110, WHITE); ptext(cr, 'DEAD STRAIGHT · NULLARBOR PLAIN', 540, 700, 38, AU_C, 1, fam='Poppins ExtraBold', sw=6)
def sc_tube(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'UK', (0, 0), tuple(G.p('UK', -0.12, 51.5)), 0.85, 7.0, t0, t0 + 1.2, UK_LAND)
    ox, oy = kpt('UK', -0.12, 51.51, cx, cy, s); endmap(cr)
    cols = [(0.86, 0.14, 0.12), (0.0, 0.2, 0.62), (0.0, 0.6, 0.25), (1.0, 0.82, 0.0), (0.55, 0.3, 0.15), (0.6, 0.6, 0.65)]
    k = ease_io(prog(t, t0 + 0.8, t0 + 2.2))
    for j, col in enumerate(cols):
        a = j / len(cols) * math.pi + 0.3; L = 700
        p1 = (ox - L * math.cos(a), oy - L * math.sin(a)); m = (ox + 60 * math.sin(j * 1.7), oy + 50 * math.cos(j * 1.3)); p2 = (ox + L * math.cos(a), oy + L * math.sin(a))
        rail(cr, [p1, m, p2], k, col, 12)
    if k > 0.5:
        for j in range(6): cr.new_path(); cr.arc(ox + 60 * math.sin(j * 1.7), oy + 50 * math.cos(j * 1.3), 12, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0.1, 0.1, 0.1); cr.set_line_width(4); cr.stroke()
    label(cr, 'LONDON · 1863', 540, 620, 100, UK_C); ptext(cr, "THE WORLD'S FIRST UNDERGROUND RAILWAY", 540, 700, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tr = at('r6b', 'railway') - 0.1
    if t >= tr and t < at('r6b', 'London') + 0.5: chip(cr, '1825 · FIRST PUBLIC STEAM RAILWAY', 540, 800, 40, WHITE, INK, pop_k(t, tr), 1)
def stones(cr, x, y, sc, a):
    cr.save(); cr.translate(x, y); cr.scale(sc, sc)
    for j in range(5):
        dx = (j - 2) * 120; cr.rectangle(dx - 45, -160, 30, 160); cr.rectangle(dx + 15, -160, 30, 160); cr.set_source_rgba(0.6, 0.6, 0.62, a); cr.fill()
        if j % 2 == 0: cr.rectangle(dx - 55, -190, 110, 32); cr.fill()
    cr.restore()
def sc_stonehenge(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'UK', (0, 0), tuple(G.p('UK', -1.83, 51.18)), 0.85, 2.5, t0, t0 + 1.2, UK_LAND)
    x, y = kpt('UK', -1.826, 51.179, cx, cy, s); pin(cr, x, y, t, t0 + 1.0, WHITE); endmap(cr)
    if t >= t0 + 0.8: stones(cr, 540, 1250, 1.2, clamp((t - t0 - 0.8) * 3))
    label(cr, 'STONEHENGE', 540, 620, 110, WHITE); ptext(cr, '~5,000 YEARS OLD', 540, 700, 44, UK_C, 1, fam='Poppins ExtraBold', sw=6)
def sc_culture(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (0, -60), 0.2, 0.22, t0, t1 + 2, AU_LAND, rot=0.02)
    rng = np.random.default_rng(8); k = ease_out(prog(t, t0, t0 + 1.4))
    for j in range(int(9 * k)):
        x, y = cx + rng.uniform(-300, 300) * s * 3.5, cy + rng.uniform(-260, 260) * s * 3.5
        for r in range(4):
            cr.new_path()
            for q in range(14 + r * 6):
                a = q / (14 + r * 6) * 2 * math.pi; cr.arc(x + (18 + r * 16) * math.cos(a), y + (18 + r * 16) * math.sin(a), 4, 0, 2 * math.pi); cr.new_sub_path()
            cr.set_source_rgba(*((1, 0.95, 0.85) if r % 2 else (0.95, 0.75, 0.35)), 0.9); cr.fill()
    endmap(cr)
    ky = ease_out(prog(t, at('r7b', 'sixty') - 0.2, at('r7b', 'years') + 0.3))
    rrect(cr, 120, 1240, 840 * ky, 40, 20); cr.set_source_rgb(*AU_C); cr.fill(); ptext(cr, f'{int(65 * ky)},000+ YEARS', 540, 1225, 52, AU_C, clamp(ky * 3), sw=8)
    rrect(cr, 120, 1320, 840 * 5 / 65, 40, 20); cr.set_source_rgb(*UK_C); cr.fill(); ptext(cr, 'STONEHENGE ~5,000', 300, 1395, 30, WHITE, 1, fam='Poppins ExtraBold', anchor='l', sw=5)
    label(cr, 'OLDEST LIVING CULTURE', 540, 620, 84, AU_C); ptext(cr, 'ABORIGINAL & TORRES STRAIT ISLANDER PEOPLES', 540, 700, 30, WHITE, 1, fam='Poppins ExtraBold', sw=5)
def gdp_circle(cr, x, y, g, col, k, lab, size=50):
    r = 150 * math.sqrt(g / 4.25) * k
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.92); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    if lab: ptext(cr, lab, x, y + size * 0.35, size, INK, clamp(k), sw=0, shadow=False)
def sc_gdpau(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE)
    k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 540, 1000, 2.0, AU_C, 0.2 + 0.8 * k, f'${2.0 * k:.1f}T', 66)
def sc_gdpuk(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE)
    gdp_circle(cr, 790, 1080, 2.0, AU_C, 1, '$2T', 46)
    k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 360, 980, 4.25, UK_C, 0.2 + 0.8 * k, f'${4.25 * k:.2f}T', 70)
def sc_ukmove(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'UK', (0, 0), tuple(G.p('UK', -0.12, 51.5)), 0.85, 3.0, t0, t0 + 1.0, UK_LAND)
    ox, oy = kpt('UK', -0.12, 51.51, cx, cy, s); pin(cr, ox, oy, t, t0 + 0.8, UK_C); endmap(cr)
    for j in range(8):
        tj = t0 + 0.9 + j * 0.08
        if t >= tj: a = j / 8 * 2 * math.pi; emoji(cr, '🦘', ox + 170 * math.cos(a), oy + 130 * math.sin(a), 70 * pop_k(t, tj), 1)
    label(cr, 'AUSSIES IN LONDON', 540, 620, 90, AU_C); ptext(cr, '~150,000 AUSTRALIAN-BORN IN THE UK', 540, 700, 32, WHITE, 0.9, fam='Poppins ExtraBold', sw=5)
def sc_move(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), (150, -250), 0.2, 0.23, t0, t1 + 2, AU_LAND)
    rng = np.random.default_rng(12); k = ease_out(prog(t, t0, at('r9b', 'Australia') + 0.3))
    for j in range(int(240 * k)):
        nm, lon, lat, m = CITIES[j % 5]; x, y = kpt('AU', lon, lat, cx, cy, s); r, a = abs(rng.normal(0, 40)), rng.uniform(0, 2 * math.pi)
        cr.new_path(); cr.arc(x + r * math.cos(a), y + r * math.sin(a), 4, 0, 2 * math.pi); cr.set_source_rgba(*UK_C, 0.9); cr.fill()
    for j in range(5):
        ph = ((t - t0) * 0.5 + j / 5) % 1; emoji(cr, '✈️', lerp(-80, 700, ph), lerp(600, 1100, ph) + j * 30, 70, 1 - ph * 0.5, rot=0.5)
    endmap(cr); label(cr, f'{1.1 * k:.1f} MILLION', 540, 620, 110, UK_C); ptext(cr, 'UK-BORN PEOPLE LIVING IN AUSTRALIA', 540, 700, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    ts = at('r9b', 'Sunshine') - 0.1
    if t >= ts: chip(cr, 'SUNSHINE WINS', 540, 800, 50, GOLD, INK, pop_k(t, ts), 1)
SCENE = {'size': sc_size, 'aupop': sc_aupop, 'ukpop': sc_ukpop, 'rain': sc_rain, 'sun': sc_sun, 'socceroos': sc_socceroos, 'england66': sc_england66,
         'crickinv': sc_crickinv, 'cricwc': sc_cricwc, 'rail': sc_rail, 'tube': sc_tube, 'stonehenge': sc_stonehenge, 'culture': sc_culture,
         'gdpau': sc_gdpau, 'gdpuk': sc_gdpuk, 'ukmove': sc_ukmove, 'move': sc_move}

# ---------- hook, close-ups, title ----------
UK_TILES = None
def uk_tiles():
    global UK_TILES
    if UK_TILES is None:
        pts = []
        for jj, y in enumerate(np.arange(-2000, 2000, 560)):
            for x in np.arange(-2200 + (jj % 2) * 210, 2200, 420):
                if inside(np.array([x, y]), G.c['AU']): pts.append((x, y))
        rng = np.random.default_rng(31); order = rng.permutation(len(pts))[:31]; UK_TILES = [pts[k] for k in order]
    return UK_TILES
def draw_hook(cr, t):
    """Cold open: the two balls trade insults, then 31 UKs stamp onto Australia."""
    if t >= bt('title')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        sh_close(cr, t, b1, 'UK', 0, b1['end'], 'angry'); emoji(cr, '☂️', 880, 820, 150, 1, rot=-0.2 + 0.05 * math.sin(t * 3))
        return True
    if t < b3['start']:
        sx, sy = shake(t, w('h2', 'cloud') - 0.05, 20, 0.4); cr.save(); cr.translate(sx, sy)
        sh_low(cr, t, b2, 'Australia', b2['start'], b2['end'], 'angry'); cr.restore()
        emoji(cr, '😎', 860, 820, 130 * pop_k(t, b2['l0'], 0.3), 1)
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2)))
        return True
    cx, cy, s = mview(cr, t, 'AU', (0, -100), (0, 0), 0.2, 0.19, b3['start'], b3['end'], AU_LAND)
    t0 = w('h3', 'fits') - 0.1; t1 = w('h3', 'thirty', end=True) + 0.2; n = int(clamp(prog(t, t0, t1)) * 31) if t >= t0 else 0
    tiles = uk_tiles()
    for k_, (x, y) in enumerate(tiles[:n]):
        tk = t0 + (k_ + 1) / 31 * (t1 - t0); kk = ease_out(prog(t, tk - 0.08, tk + 0.12)); sc = lerp(1.8, 1.0, kk)
        cr.save(); px, py = cx + x * s, cy - y * s; cr.translate(px, py); cr.scale(sc, sc); cr.translate(-px, -py)
        km_shape(cr, G.uk_true, cx, cy, s, UK_LAND, 1, x, y, fill=0.92, lw=2, edge=INK); cr.restore()
    endmap(cr)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
    if n: sx, sy = shake(t, t0 + n / 31 * (t1 - t0), 6, 0.12); cr.save(); cr.translate(sx, sy); ptext(cr, f'×{n}', 540, 360, 190, UK_C, 1, sw=18); cr.restore()
    ts = w('h3', 'size') - 0.1
    if t >= ts:
        cr.set_source_rgba(0, 0, 0.05, 0.45 * clamp((t - ts) * 4)); cr.paint()
        sx, sy = shake(t, ts, 18); cr.save(); cr.translate(sx, sy); slam(cr, "SIZE ISN'T", 540, 860, 150, WHITE, t, ts); slam(cr, 'EVERYTHING', 540, 1030, 150, GOLD, t, w('h3', 'everything') - 0.1); cr.restore()
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
    ball(cr, 'Australia', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'UK', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'AUSTRALIA', 540, 560, 180, AU_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'THE UK', 540, 980, 190, UK_C, t, w('title', 'winner'))
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
    for side, x, col, sc, lab in (('A', 250, AU_C, sn, 'AUSTRALIA'), ('U', 830, UK_C, ss, 'THE UK')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = ('TIEBREAKER' if i == NR else f'ROUND {i}/8') if i else ('FINAL' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📏', 2: '👥', 3: '☀️', 4: '⚽', 5: '🏏', 6: '🚂', 7: '🏛️', 8: '📈', 9: '✈️'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((AU_C, UK_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    head = 'TIEBREAKER' if i == NR else f'ROUND {i}'
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, head, 0, 0, 130 if i == NR else 150, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = (at('c9', 'who') - 0.1) if i == NR else b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    if i == NR:
        ptext(cr, '4 — 4', 540, 600, 90, WHITE, pop_k(t, b['l0']), sw=10)
        ts = at('c9', 'move') - 0.1
        if t >= ts: chip(cr, 'WHO DO PEOPLE MOVE TO?', 540, 1420, 44, GOLD, INK, pop_k(t, ts), 1)
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = AU_C if win == 'A' else UK_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('AUSTRALIA' if win == 'A' else 'THE UK') + ' WINS'
    cr.save(); cr.translate(x, 1450); cr.rotate(-0.05 if win == 'A' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 72)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, 72, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- ending ----------
def draw_end(cr, t):
    e1, e2, c = bt('e1'), bt('e2'), bt('cta')
    if t < e2['start']:
        h = hop_of(t, e1); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.1), 0.04, 540, 1100); set_uk(cr, t); ball(cr, 'UK', 540, 1290 - h * 40, 290, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'UK', 540, 1640, UK_C); emoji(cr, '🫖', 860, 860, 150 * pop_k(t, e1['l0'] + 0.6), 1)
        ptext(cr, 'AUSTRALIA WINS 5 — 4', 540, 790, 76, AU_C, pop_k(t, e1['start'] + 0.2), sw=12); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), -0.05, 540, 1100); set_australia(cr, t)
        ball(cr, 'Australia', 540, 1260 - h * 50, 320, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Australia', 540, 1640, AU_C); emoji(cr, '☕', 860, 820, 140 * pop_k(t, e2['l0'] + 0.3), 1)
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.08), 0.02, 540, 1000); arena(cr, t)
    ball(cr, 'Australia', 290, 1300, 200, 'happy', 0, 0.8); ball(cr, 'UK', 790, 1300, 200, 'neutral', 0, -0.8); cr.restore()
    ptext(cr, '5 — 4', 540, 1000, 140, WHITE, 1, sw=14)
    for x, col, word, lab, rot in ((290, AU_C, 'Australia', 'AUSTRALIA', -0.04), (790, UK_C, 'UK', 'THE UK', 0.04)):
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
    boom(0.0, 1.0); rumble(0.0, 1.4, 0.35); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(w('h2', 'cloud') - 0.05, 0.8)
    whoosh(bt('h3')['start'] - 0.3, 0.3); t0_ = w('h3', 'fits') - 0.1; t1_ = w('h3', 'thirty', end=True) + 0.2
    for k_ in range(31): pop(t0_ + (k_ + 1) / 31 * (t1_ - t0_), 0.09, 600 + 25 * k_)
    boom(w('h3', 'size') - 0.1, 1.0); boom(w('h3', 'everything') - 0.1, 0.8)
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
    boom(at('c9', 'who') - 0.1, 0.9); rumble(at('c9', 'move'), 1.2, 0.15)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_auuk'))
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
