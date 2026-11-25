# Countryballs: USA vs Japan, the Geography War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (bullet trains, the Moon, Skytree, Tokyo...).
# Usage: python3 usjp.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

A_C, U_C = hexc('#FF4D5E')[:3], hexc('#F5F5F5')[:3]
US_C, JP_C = hexc('#4F8CFF')[:3], hexc('#FF4D5E')[:3]
A_C, U_C = US_C, JP_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'USA': ('en-US-EricNeural', '+4%'), 'Japan': ('ja-JP-KeitaNeural', '+0%')}
LINES = [
    ('h1', 'USA', "Japan, you're tiny! You'd fit in Texas!"),
    ('h2', 'Japan', "And your trains are slower than my grandma!"),
    ('h3', None, "Japan fits inside the mainland USA twenty-one times. But size isn't everything."),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: size."),
    ('r1a', 'Japan', "I may be small, but Tokyo is the biggest city on Earth!"),
    ('r1b', 'USA', "Cute. I'm twenty-six times bigger than you, buddy!"),
    ('c2', None, "Round two: people."),
    ('r2a', 'Japan', "One hundred and twenty-three million people!"),
    ('r2b', 'USA', "Three hundred and forty-two million. Almost three times more!"),
    ('c3', None, "Round three: trains."),
    ('r3a', 'USA', "My new Acela train hits one hundred and sixty miles an hour!"),
    ('r3b', 'Japan', "My bullet trains do three hundred and twenty kilometres an hour. That's almost two hundred miles an hour."),
    ('c4', None, "Round four: the Moon."),
    ('r4a', 'Japan', "My lander SLIM touched down on the Moon, right on target!"),
    ('r4b', 'USA', "Nice. But twelve humans have walked on the Moon. All of them American!"),
    ('c5', None, "Round five: living longer."),
    ('r5a', 'USA', "Americans live to seventy-nine!"),
    ('r5b', 'Japan', "Japanese live to eighty-four. And our women have lived the longest on Earth for forty-one years in a row!"),
    ('c6', None, "Round six: the GDP war."),
    ('r6a', 'Japan', "My economy is worth over four trillion dollars!"),
    ('r6b', 'USA', "Mine is over thirty trillion. That's seven Japans!"),
    ('c7', None, "Round seven: tallest tower."),
    ('r7a', 'USA', "One World Trade Center: five hundred and forty-one metres!"),
    ('r7b', 'Japan', "Tokyo Skytree: six hundred and thirty-four. The tallest tower on Earth!"),
    ('c8', None, "Final round: history."),
    ('r8a', 'USA', "I'm two hundred and fifty years old this year!"),
    ('r8b', 'Japan', "Happy birthday. My oldest company was founded in the year five seventy-eight. Over a thousand years before you!"),
    ('e1', 'USA', "Four all?! Rematch!"),
    ('e2', 'Japan', "No. Let the viewers decide."),
    ('cta', None, "It's a tie! You pick the tiebreaker. Comment it below, and subscribe to see who wins!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SIZE', 'A', ('r1b', 'bigger')), 2: ('PEOPLE', 'A', ('r2b', 'more')), 3: ('TRAINS', 'U', ('r3b', 'miles')), 4: ('THE MOON', 'A', ('r4b', 'American')),
      5: ('LIVING LONGER', 'U', ('r5b', 'row')), 6: ('THE GDP WAR', 'A', ('r6b', 'Japans')), 7: ('TALLEST TOWER', 'U', ('r7b', 'Earth')), 8: ('HISTORY', 'U', ('r8b', 'before'))}
NR = 8
SHOTS = {
    'r1a': [(None, 'two'), ('Tokyo', 'map:tokyo')], 'r1b': [(None, 'close'), ('twenty', 'map:size')],
    'r2a': [(None, 'low'), ('One', 'map:jppop')], 'r2b': [(None, 'ots'), ('Three', 'map:uspop')],
    'r3a': [(None, 'close'), ('Acela', 'map:acela')], 'r3b': [(None, 'low'), ('bullet', 'map:shinkansen')],
    'r4a': [(None, 'two'), ('SLIM', 'map:slim')], 'r4b': [(None, 'ots'), ('twelve', 'map:apollo')],
    'r5a': [(None, 'close'), ('seventy', 'map:life_us')], 'r5b': [(None, 'low'), ('eighty', 'map:life')],
    'r6a': [(None, 'two'), ('four', 'map:gdpjp')], 'r6b': [(None, 'low'), ('thirty', 'map:gdpus')],
    'r7a': [(None, 'close'), ('One', 'map:wtc')], 'r7b': [(None, 'ots'), ('Tokyo', 'map:skytree')],
    'r8a': [(None, 'low'), ('two', 'map:usa250')], 'r8b': [(None, 'two'), ('oldest', 'map:kongo')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {'SLIM': 'Slim', 'Skytree': 'Sky tree', 'Acela': 'Ah-sell-ah'}}
C.HOT = ('usa', 'japan', 'tiny', 'texas', 'trains', 'war', 'tie', 'tiebreaker', 'comment', 'subscribe', 'winner', 'twenty-one', 'size')
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
        self.ref = {'US': (-98.0, 39.0), 'JP': (137.0, 37.0)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('US', 'United States of America', ['Canada', 'Mexico', 'Cuba', 'Bahamas']), ('JP', 'Japan', ['Russia', 'China', 'North Korea', 'South Korea', 'Taiwan'])):
            rs = R(n)
            if k == 'US': rs = [r for r in rs if -126 < r[:, 0].mean() < -66 and 24 < r[:, 1].mean() < 50]
            pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs if nn in cf for r in local(R(nn), *self.ref[k])]
        self.jp_true = [r - np.concatenate(self.c['JP']).mean(axis=0) for r in self.c['JP']]
        print('areas M km2: mainland usa', round(area(self.c['US']) / 1e6, 2), 'japan', round(area(self.c['JP']) / 1e6, 3), 'ratio', round(area(self.c['US']) / area(self.c['JP']), 1))
        B.FL['USA'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'us.png')); B.FL['Japan'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'jp.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'USA' else 'U'
def col_of(name): return US_C if name == 'USA' else JP_C
def rival_of(name): return 'Japan' if name == 'USA' else 'USA'
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
def set_of(name, cr, t): (set_usa if name == 'USA' else set_japan)(cr, t)

# ---------- shots ----------
def sh_close(cr, t, b, name, t0, t1, mood='happy'):
    sgn = -1 if name == 'USA' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.07 * sgn * (1 if sum(map(ord, b['key'])) % 2 else -1), 540, 1100); set_of(name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1, mood='happy'):
    sgn = -1 if name == 'USA' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, mood, 0.04 * h, -sgn * 0.2); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_ots(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'USA' else 1; h = hop_of(t, b); rv = rival_of(name)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.06), 0.02 * sgn, 540 + lerp(0, -sgn * 40, prog(t, t0, t1)), 1000); set_of(name, cr, t)
    ball(cr, name, 540 + sgn * 150, 1080 - h * 36, 210, 'happy', 0.05 * h, -sgn * 0.6)
    ball(cr, rv, 540 - sgn * 470, 1700, 560, 'angry', 0, sgn * 0.9); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.paint()
    bubble(cr, t, b, 540 + sgn * 150, 520); nametag(cr, name, 540 + sgn * 150, 1340, col_of(name))
def sh_two(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'USA' else 1; h = hop_of(t, b); rv = rival_of(name)
    pan = lerp(-60, 60, prog(t, t0, t1)) * sgn
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    for n, x in (('USA', 290), ('Japan', 790)):
        hh = h if n == name else 0; ball(cr, n, x, 1300 - hh * 40, 220, 'happy' if n == name else 'angry', 0.05 * hh, 0.8 if n == 'USA' else -0.8)
    cr.restore()
    sx = (290 if name == 'USA' else 790) - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1600, col_of(name))
def sh_react(cr, t, b, name, t0, t1):
    rv = rival_of(name); k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.25, 1.08, k), -0.06 if rv == 'USA' else 0.06, 540 + sx, 1080 + sy); set_of(rv, cr, t)
    ball(cr, rv, 540, 1150, 360, 'shock', 0, 0); cr.restore()
    ptext(cr, '?!', 860, 760, 170, GOLD, pop_k(t, t0 + 0.05), sw=14)
    nametag(cr, rv, 540, 1640, col_of(rv))
def sh_map(cr, t, b, name, t0, t1, scene):
    SCENE[scene](cr, t, b, t0, t1)
    sgn = -1 if name == 'USA' else 1; h = hop_of(t, b); x = 540 + sgn * 380
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
US_LAND, JP_LAND = (0.36, 0.5, 0.78), (0.93, 0.9, 0.86)
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
def sc_tokyo(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), tuple(G.p('JP', 139.7, 35.7)), 0.26, 0.9, t0, t0 + 1.2, JP_LAND)
    x, y = kpt('JP', 139.76, 35.68, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, JP_C)
    rng = np.random.default_rng(5); kk = ease_out(prog(t, t0 + 0.8, t0 + 2.0))
    for j in range(int(260 * kk)):
        r, a = abs(rng.normal(0, 70)), rng.uniform(0, 2 * math.pi); cr.new_path(); cr.arc(x + r * math.cos(a), y + r * math.sin(a), 4, 0, 2 * math.pi); cr.set_source_rgba(1, 0.9, 0.4, 0.85); cr.fill()
    endmap(cr); label(cr, 'TOKYO AREA ≈ 37 MILLION', 540, 620, 76, JP_C); ptext(cr, 'THE BIGGEST CITY ON EARTH', 540, 700, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_size(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'US', (0, 0), (0, -100), 0.2, 0.21, t0, t1 + 1.5, US_LAND)
    k = ease_out(prog(t, t0, t0 + 0.5)); cr.save(); cr.translate(0, (1 - k) * -900); km_shape(cr, G.jp_true, cx, cy, s, JP_LAND, 1, 300, 0, fill=0.95, lw=2, edge=INK); cr.restore()
    if k >= 1: chip(cr, 'JAPAN', cx + 300 * s, cy + 230, 30, WHITE, INK, 1, 1)
    endmap(cr)
    tx = at('r1b', 'twenty') + 0.4
    if t >= tx: sx, sy = shake(t, tx, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'USA = 26 JAPANS', 540, 640, 96, WHITE, t, tx); cr.restore()
    ptext(cr, 'WITH ALASKA & HAWAII', 540, 730, 32, WHITE, 0.85, fam='Poppins ExtraBold', sw=5) if t >= tx else None
def sc_jppop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), (0, 50), 0.3, 0.27, t0, t1 + 1, JP_LAND); k = ease_out(prog(t, t0, t0 + 1.0))
    dots(cr, 'JP', int(500 * k), cx, cy, s, 129, 146, 30, 46, (1, 0.85, 0.3), 9); endmap(cr); label(cr, f'{123 * k:.0f} MILLION', 540, 620, 104, JP_C)
def sc_uspop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'US', (0, 0), (0, 0), 0.19, 0.2, t0, t1 + 1, US_LAND); k = ease_out(prog(t, t0, at('r2b', 'million') + 0.3))
    dots(cr, 'US', int(1400 * k), cx, cy, s, -125, -67, 25, 49, (1, 0.85, 0.3), 3); endmap(cr); label(cr, f'{342 * k:.0f} MILLION', 540, 620, 104, US_C)
    tm = at('r2b', 'Almost') - 0.1
    if t >= tm: chip(cr, '≈ 2.8× JAPAN', 540, 730, 50, GOLD, INK, pop_k(t, tm), 1)
NEC = [(-71.06, 42.36), (-71.41, 41.82), (-72.92, 41.31), (-73.99, 40.75), (-75.17, 39.95), (-76.61, 39.29), (-77.01, 38.9)]
def sc_acela(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'US', (0, 0), tuple(G.p('US', -74.0, 40.6)), 0.19, 1.3, t0, t0 + 1.1, US_LAND)
    k = ease_io(prog(t, t0 + 0.9, at('r3a', 'hour') + 0.2)); pts = [kpt('US', lon, lat, cx, cy, s) for lon, lat in NEC]; e = rail(cr, pts, k, (1, 1, 1), 9)
    for nm, lon, lat in (('BOSTON', -71.06, 42.36), ('NEW YORK', -73.99, 40.75), ('WASHINGTON', -77.01, 38.9)):
        if t >= t0 + 1.0: x, y = kpt('US', lon, lat, cx, cy, s); ptext(cr, nm, x + 130, y + 10, 30, WHITE, 1, fam='Poppins ExtraBold', sw=5)
    if e: emoji(cr, '🚆', e[0], e[1] - 40, 80, 1)
    endmap(cr); kk = ease_out(prog(t, at('r3a', 'one') - 0.2, at('r3a', 'hour'))); label(cr, f'{int(160 * kk)} MPH', 540, 620, 120, US_C); ptext(cr, 'NEXTGEN ACELA · TOP SPEED', 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
SHIN = [(130.54, 31.58), (130.42, 33.59), (132.46, 34.40), (135.50, 34.73), (136.88, 35.17), (139.77, 35.68), (140.88, 38.26), (141.15, 39.70), (140.69, 40.83), (140.65, 41.90)]
def sc_shinkansen(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), (0, -100), 0.28, 0.32, t0, t1 + 2, JP_LAND, rot=0.02)
    k = ease_io(prog(t, t0 + 0.1, at('r3b', 'hour') + 0.2)); pts = [kpt('JP', lon, lat, cx, cy, s) for lon, lat in SHIN]; e = rail(cr, pts, k, JP_C, 10)
    if e: emoji(cr, '🚄', e[0], e[1] - 40, 90, 1)
    endmap(cr); kk = ease_out(prog(t, at('r3b', 'three') - 0.2, at('r3b', 'hour'))); label(cr, f'{int(320 * kk)} KM/H', 540, 620, 120, JP_C)
    tm = at('r3b', 'almost') - 0.1
    if t >= tm: chip(cr, '≈ 199 MPH  vs  160 MPH', 540, 740, 48, GOLD, INK, pop_k(t, tm), 1)
def moon(cr, t):
    cr.set_source_rgb(0.01, 0.01, 0.05); cr.paint(); rng = np.random.default_rng(2)
    for _ in range(160): x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.6); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.4 + 0.4 * math.sin(t * 2 + x)); cr.fill()
    cr.new_path(); cr.arc(540, 2350, 1250, 0, 2 * math.pi); cr.set_source_rgb(0.62, 0.62, 0.66); cr.fill()
    for x, y, r in ((200, 1290, 60), (640, 1350, 90), (950, 1300, 50), (420, 1500, 70), (820, 1560, 110)):
        cr.save(); cr.translate(x, y); cr.scale(1, 0.35); cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(0.5, 0.5, 0.55); cr.fill()
    emoji(cr, '🌍', 860, 820, 140, 1)
def sc_slim(cr, t, b, t0, t1):
    moon(cr, t); k = ease_out(prog(t, t0, t0 + 1.2)); y = lerp(500, 1250, k)
    emoji(cr, '🛰️', 540, y, 150, 1, rot=0.2 * (1 - k))
    if k >= 1:
        for j in range(3): ph = ((t - t0 - 1.2) * 0.8 + j / 3) % 1; cr.new_path(); cr.arc(540, 1300, 30 + 160 * ph, 0, 2 * math.pi); cr.set_source_rgba(*JP_C, 1 - ph); cr.set_line_width(5); cr.stroke()
        chip(cr, 'WITHIN ~100 M OF TARGET', 540, 760, 46, WHITE, INK, pop_k(t, t0 + 1.2), 1)
    label(cr, 'SLIM · JANUARY 2024', 540, 620, 86, JP_C)
def sc_apollo(cr, t, b, t0, t1):
    moon(cr, t); k = prog(t, at('r4b', 'twelve') - 0.2, at('r4b', 'Moon') + 0.3)
    for j in range(int(12 * k + 0.999)):
        x = 130 + (j % 6) * 165; y = 960 + (j // 6) * 190 - abs(math.sin(t * 3 + j)) * 10; kk = pop_k(t, at('r4b', 'twelve') - 0.2 + j * 0.08)
        cr.save(); cr.translate(x, y); cr.scale(kk, kk)
        rrect(cr, -34, -10, 68, 90, 24); cr.set_source_rgb(0.95, 0.95, 0.97); cr.fill(); cr.new_path(); cr.arc(0, -40, 36, 0, 2 * math.pi); cr.fill()
        rrect(cr, -24, -58, 48, 32, 14); cr.set_source_rgb(0.85, 0.65, 0.2); cr.fill(); rrect(cr, -14, 14, 28, 22, 4); cr.set_source_rgb(*US_C); cr.fill(); cr.restore()
    label(cr, f'{int(12 * clamp(k))} MOONWALKERS', 540, 620, 96, US_C); ptext(cr, 'APOLLO 11–17 · 1969–1972', 540, 700, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def pbar(cr, x, base, v, vmin, vmax, k, col, name, lab):
    hh = max(8, 560 * (v - vmin) / (vmax - vmin) * k); rrect(cr, x - 110, base - hh, 220, hh, 18); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    label(cr, lab, x, base - hh - 24, 60, WHITE, clamp(k * 2)); ball(cr, name, x, base + 80, 56, 'happy', 0, 0)
def sc_life_us(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'LIFE EXPECTANCY (YEARS)', 540, 620, 62, WHITE); ptext(cr, 'BARS START AT 60', 540, 690, 28, WHITE, 0.7, fam='Poppins ExtraBold', sw=5)
    k = ease_out(prog(t, at('r5a', 'seventy') - 0.2, at('r5a', 'seventy') + 0.8)); pbar(cr, 330, 1300, 79.0, 60, 90, k, US_C, 'USA', '79.0')
def sc_life(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'LIFE EXPECTANCY (YEARS)', 540, 620, 62, WHITE); ptext(cr, 'BARS START AT 60', 540, 690, 28, WHITE, 0.7, fam='Poppins ExtraBold', sw=5)
    pbar(cr, 330, 1300, 79.0, 60, 90, 1, US_C, 'USA', '79.0'); k = ease_out(prog(t, at('r5b', 'eighty') - 0.2, at('r5b', 'eighty') + 0.8)); pbar(cr, 750, 1300, 84.3, 60, 90, k, JP_C, 'Japan', '84.3')
    tw0 = at('r5b', 'women') - 0.1
    if t >= tw0: chip(cr, 'JAPANESE WOMEN: 87.3 · #1 FOR 41 YEARS', 460, 1420, 34, GOLD, INK, pop_k(t, tw0), 1)
def gdp_circle(cr, x, y, g, col, k, lab, size=50):
    r = 240 * math.sqrt(g / 31.0) * k
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.92); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    if lab: ptext(cr, lab, x, y + size * 0.35, size, INK if col != US_C else WHITE, clamp(k), sw=0, shadow=False)
def sc_gdpjp(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE); k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 540, 1050, 4.4, JP_C, 0.2 + 0.8 * k, f'${4.4 * k:.1f}T', 40)
def sc_gdpus(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE); k = ease_out(prog(t, t0, t0 + 1.0)); gdp_circle(cr, 470, 1050, 31.0, US_C, 0.2 + 0.8 * k, f'${31 * k:.0f}T', 90)
    gdp_circle(cr, 900, 1260, 4.4, JP_C, 1, '', 30); ptext(cr, 'JAPAN', 900, 1370, 34, JP_C, 1, fam='Poppins ExtraBold', sw=6)
    tj = at('r6b', 'seven') - 0.1
    if t >= tj: slam(cr, '= 7 JAPANS', 540, 760, 90, GOLD, t, tj)
def tower(cr, x, base, h_m, k, col, name, kind):
    h = 1.25 * h_m * k
    if h < 4: return
    if kind == 'wtc':
        cr.new_path(); cr.move_to(x - 80, base); cr.line_to(x - 46, base - h * 0.78); cr.line_to(x + 46, base - h * 0.78); cr.line_to(x + 80, base); cr.close_path()
        cr.set_source_rgb(*col); cr.fill(); cr.rectangle(x - 4, base - h, 8, h * 0.22); cr.fill()
    else:
        cr.new_path(); cr.move_to(x - 70, base); cr.line_to(x - 14, base - h * 0.85); cr.line_to(x + 14, base - h * 0.85); cr.line_to(x + 70, base); cr.close_path(); cr.set_source_rgb(*col); cr.fill()
        for f_ in (0.55, 0.73): cr.rectangle(x - 38, base - h * f_ - 14, 76, 28); cr.fill()
        cr.rectangle(x - 4, base - h, 8, h * 0.16); cr.fill()
    ptext(cr, f'{int(h_m * k)} M', x, base - h - 30, 52, WHITE, 1, sw=7); ptext(cr, name, x, base + 46, 32, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_wtc(cr, t, b, t0, t1):
    set_usa(cr, t); cr.set_source_rgba(0.03, 0.03, 0.08, 0.5); cr.paint()
    k = ease_io(prog(t, t0, at('r7a', 'metres') + 0.2)); tower(cr, 540, 1450, 541, k, (0.75, 0.85, 1), 'ONE WORLD TRADE CENTER', 'wtc')
def sc_skytree(cr, t, b, t0, t1):
    set_japan(cr, t); cr.set_source_rgba(0.03, 0.03, 0.08, 0.45); cr.paint()
    tower(cr, 300, 1450, 541, 1, (0.75, 0.85, 1), 'ONE WTC', 'wtc'); k = ease_io(prog(t, t0, w('r7b', 'thirty', end=True) + 0.3)); tower(cr, 780, 1450, 634, k, (0.95, 0.95, 1), 'TOKYO SKYTREE', 'sky')
    te = at('r7b', 'tallest') - 0.1
    if t >= te: chip(cr, 'TALLEST TOWER ON EARTH', 540, 470, 46, GOLD, INK, pop_k(t, te), 1)
def sc_usa250(cr, t, b, t0, t1):
    set_usa(cr, t); cr.set_source_rgba(0.02, 0.02, 0.08, 0.45); cr.paint()
    for j in range(6):
        ph = ((t - t0) * 0.7 + j / 6) % 1; x = 150 + (j * 173) % 800; y = 900 - 300 * j % 3 * 0.3
        for q in range(14):
            a = q / 14 * 2 * math.pi; r = 140 * ph; cr.new_path(); cr.arc(x + r * math.cos(a), 700 + 120 * (j % 3) + r * math.sin(a), 6 * (1 - ph) + 1, 0, 2 * math.pi); cr.set_source_rgba(*((1, 0.3, 0.35) if j % 3 == 0 else (1, 1, 1) if j % 3 == 1 else (0.35, 0.55, 1)), 1 - ph); cr.fill()
    k = pop_k(t, at('r8a', 'two') - 0.1) if t >= at('r8a', 'two') - 0.1 else 0
    if k: cr.save(); cr.translate(540, 1150); cr.scale(k, k); ptext(cr, '250', 0, 0, 280, GOLD, 1, sw=20); cr.restore()
    label(cr, '1776 TO 2026', 540, 620, 90, WHITE)
def sc_kongo(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'OLDEST COMPANY: KONGŌ GUMI', 540, 620, 60, JP_C); ptext(cr, 'TEMPLE BUILDERS · FOUNDED 578 AD', 540, 690, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    x0, x1, y = 120, 960, 1150; k = ease_io(prog(t, at('r8b', 'five') - 0.3, at('r8b', 'before') + 0.3))
    cr.move_to(x0, y); cr.line_to(x1, y); cr.set_source_rgba(1, 1, 1, 0.3); cr.set_line_width(8); cr.stroke()
    cr.move_to(x0, y); cr.line_to(lerp(x0, x1, k), y); cr.set_source_rgb(*JP_C); cr.set_line_width(12); cr.stroke()
    for yr, em, col in ((578, '🏯', JP_C), (1776, '🗽', US_C), (2026, '📍', WHITE)):
        f = (yr - 578) / (2026 - 578); x = lerp(x0, x1, f)
        if k >= f - 0.01: emoji(cr, em, x, y - 120, 110, 1); ptext(cr, str(yr), x, y + 70, 46, col, 1, sw=7)
    tb = at('r8b', 'thousand') - 0.1
    if t >= tb: chip(cr, '1,198 YEARS BEFORE 1776', 540, 880, 50, GOLD, INK, pop_k(t, tb), 1)
SCENE = {'tokyo': sc_tokyo, 'size': sc_size, 'jppop': sc_jppop, 'uspop': sc_uspop, 'acela': sc_acela, 'shinkansen': sc_shinkansen, 'slim': sc_slim, 'apollo': sc_apollo,
         'life_us': sc_life_us, 'life': sc_life, 'gdpjp': sc_gdpjp, 'gdpus': sc_gdpus, 'wtc': sc_wtc, 'skytree': sc_skytree, 'usa250': sc_usa250, 'kongo': sc_kongo}

# ---------- hook, close-ups, title ----------
JP_TILES = None
def uk_tiles():
    global JP_TILES
    if JP_TILES is None:
        pts = []
        for jj, y in enumerate(np.arange(-1600, 1600, 560)):
            for x in np.arange(-2600 + (jj % 2) * 300, 2600, 620):
                if inside(np.array([x, y]), G.c['US']): pts.append((x, y))
        rng = np.random.default_rng(21); order = rng.permutation(len(pts))[:21]; JP_TILES = [pts[k] for k in order]
    return JP_TILES
def draw_hook(cr, t):
    """Cold open: the two balls trade insults, then 21 Japans stamp onto the mainland USA."""
    if t >= bt('title')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        sh_close(cr, t, b1, 'USA', 0, b1['end'], 'angry'); emoji(cr, '🤠', 880, 820, 140, 1, rot=-0.1 + 0.05 * math.sin(t * 3))
        return True
    if t < b3['start']:
        sx, sy = shake(t, w('h2', 'grandma') - 0.05, 20, 0.4); cr.save(); cr.translate(sx, sy)
        sh_low(cr, t, b2, 'Japan', b2['start'], b2['end'], 'angry'); cr.restore()
        emoji(cr, '🚄', 860, 820, 130 * pop_k(t, b2['l0'], 0.3), 1)
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2)))
        return True
    cx, cy, s = mview(cr, t, 'US', (0, -100), (0, 0), 0.21, 0.2, b3['start'], b3['end'], US_LAND)
    t0 = w('h3', 'fits') - 0.1; t1 = w('h3', 'twenty-one', end=True) + 0.2; n = int(clamp(prog(t, t0, t1)) * 21) if t >= t0 else 0
    tiles = uk_tiles()
    for k_, (x, y) in enumerate(tiles[:n]):
        tk = t0 + (k_ + 1) / 21 * (t1 - t0); kk = ease_out(prog(t, tk - 0.08, tk + 0.12)); sc = lerp(1.8, 1.0, kk)
        cr.save(); px, py = cx + x * s, cy - y * s; cr.translate(px, py); cr.scale(sc, sc); cr.translate(-px, -py)
        km_shape(cr, G.jp_true, cx, cy, s, JP_LAND, 1, x, y, fill=0.92, lw=1.5, edge=INK); cr.restore()
    endmap(cr)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
    if n: sx, sy = shake(t, t0 + n / 21 * (t1 - t0), 6, 0.12); cr.save(); cr.translate(sx, sy); ptext(cr, f'×{n}', 540, 360, 190, JP_C, 1, sw=18); cr.restore()
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
    ball(cr, 'USA', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'Japan', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'USA', 540, 560, 210, US_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'JAPAN', 540, 980, 190, JP_C, t, w('title', 'winner'))
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
    for side, x, col, sc, lab in (('A', 250, US_C, sn, 'USA'), ('U', 830, JP_C, ss, 'JAPAN')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = f'ROUND {i}/8' if i else ('FINAL: 4 — 4' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📏', 2: '👥', 3: '🚄', 4: '🌕', 5: '❤️', 6: '📈', 7: '🗼', 8: '🏯'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((US_C, JP_C)):
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
    col = US_C if win == 'A' else JP_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('USA' if win == 'A' else 'JAPAN') + ' WINS'
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
        sx, sy = shake(t, e1['l0'], 20, 0.4); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540 + sx, 1100 + sy); set_usa(cr, t); ball(cr, 'USA', 540, 1290, 290, 'shock', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'USA', 540, 1640, US_C)
        ptext(cr, '4 — 4', 540, 820, 130, WHITE, pop_k(t, e1['start'] + 0.1), sw=14); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540, 1100); set_japan(cr, t)
        ball(cr, 'Japan', 540, 1260 - h * 50, 300, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Japan', 540, 1640, JP_C); emoji(cr, '🙇', 200, 900, 140 * pop_k(t, e2['l0'] + 0.4), 1)
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.06), 0.02, 540, 1000); arena(cr, t)
    for n, x, lk in (('USA', 290, 0.8), ('Japan', 790, -0.8)): ball(cr, n, x, 1280 - abs(math.sin(t * 5 + x)) * 10, 170, 'angry', 0, lk)
    emoji(cr, '⚡', 540, 1280, 140, 1, rot=0.2 * math.sin(t * 10)); cr.restore()
    sx, sy = shake(t, c['start'], 16, 0.4); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A TIE!", 540, 470, 140, GOLD, t, c['start']); cr.restore()
    ptext(cr, 'USA', 220, 590, 60, US_C, 1, sw=8); ptext(cr, '4 — 4', 540, 600, 84, WHITE, 1, sw=10); ptext(cr, 'JAPAN', 860, 590, 60, JP_C, 1, sw=8)
    tp = w('cta', 'pick') - 0.1
    if t >= tp:
        kk = pop_k(t, tp); cr.save(); cr.translate(540, 730); cr.scale(kk, kk); ptext(cr, 'YOU PICK THE TIEBREAKER', 0, 0, 66, WHITE, 1, sw=9); cr.restore()
        for j, (em, lab) in enumerate((('⚾', 'BASEBALL?'), ('🍣', 'FOOD?'), ('🎬', 'MOVIES VS ANIME?'))):
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
    boom(0.0, 1.0); rumble(0.0, 1.0, 0.25); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(w('h2', 'grandma') - 0.05, 0.8)
    whoosh(bt('h3')['start'] - 0.3, 0.3); t0_ = w('h3', 'fits') - 0.1; t1_ = w('h3', 'twenty-one', end=True) + 0.2
    for k_ in range(21): pop(t0_ + (k_ + 1) / 21 * (t1_ - t0_), 0.09, 600 + 30 * k_)
    boom(w('h3', 'size') - 0.1, 1.0); boom(w('h3', 'everything') - 0.1, 0.8); whoosh(bt('title')['start'] - 0.35)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_usjp'))
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
