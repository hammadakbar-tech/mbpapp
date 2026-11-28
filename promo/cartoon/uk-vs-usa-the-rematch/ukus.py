# Countryballs: UK vs USA, the Rematch (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (Big Ben, Oxford, the Moon, Boston Harbor, tea...).
# Usage: python3 ukus.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

US_C, UK_C = hexc('#4F8CFF')[:3], hexc('#F0435A')[:3]
A_C, U_C = US_C, UK_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'USA': ('en-US-EricNeural', '+4%'), 'UK': ('en-GB-RyanNeural', '+4%')}
LINES = [
    ('h1', 'UK', "Oi, America! You still owe me for that tea!"),
    ('h2', 'USA', "Come and get it, grandpa!"),
    ('h3', None, "In seventeen seventy-three, Americans dumped three hundred and forty-two chests of British tea into Boston Harbor. Two hundred and fifty years later, it's rematch time."),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: size."),
    ('r1a', 'UK', "I may be small, but I gave the world Big Ben and the Beatles!"),
    ('r1b', 'USA', "Cute. I'm forty times bigger, buddy!"),
    ('c2', None, "Round two: history."),
    ('r2a', 'USA', "I just turned two hundred and fifty years old!"),
    ('r2b', 'UK', "Adorable. Oxford University is older than the Aztec Empire!"),
    ('c3', None, "Round three: people."),
    ('r3a', 'UK', "Sixty-nine million Brits!"),
    ('r3b', 'USA', "Three hundred and forty-two million Americans. Five times more!"),
    ('c4', None, "Round four: sport."),
    ('r4a', 'USA', "I invented basketball and the Super Bowl!"),
    ('r4b', 'UK', "I invented football, rugby, tennis and golf. And football is the biggest sport on Earth!"),
    ('c5', None, "Round five: space."),
    ('r5a', 'UK', "I launched my own satellite in nineteen seventy-one!"),
    ('r5b', 'USA', "Nice. But twelve humans have walked on the Moon. All of them American!"),
    ('c6', None, "Round six: living longer."),
    ('r6a', 'USA', "Americans live to seventy-nine!"),
    ('r6b', 'UK', "Brits live to eighty-one. Must be the tea!"),
    ('c7', None, "Round seven: the money war."),
    ('r7a', 'UK', "My economy is worth four trillion dollars!"),
    ('r7b', 'USA', "Mine is over thirty trillion. That's almost eight Britains!"),
    ('c8', None, "Final round: tea."),
    ('r8a', 'USA', "Tea? I threw yours in the harbor!"),
    ('r8b', 'UK', "And we still drink one hundred million cups a day. Every single day!"),
    ('e1', 'USA', "Four all?! Rematch!"),
    ('e2', 'UK', "Let the viewers decide. Cheers!"),
    ('cta', None, "It's a tie! You pick the tiebreaker. Comment it below, and subscribe to see who wins!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SIZE', 'A', ('r1b', 'bigger')), 2: ('HISTORY', 'U', ('r2b', 'Empire')), 3: ('PEOPLE', 'A', ('r3b', 'more')), 4: ('SPORT', 'U', ('r4b', 'Earth')),
      5: ('SPACE', 'A', ('r5b', 'American')), 6: ('LIVING LONGER', 'U', ('r6b', 'tea')), 7: ('THE MONEY WAR', 'A', ('r7b', 'Britains')), 8: ('TEA TIME', 'U', ('r8b', 'single'))}
NR = 8
SHOTS = {
    'r1a': [(None, 'two'), ('Big', 'map:bigben')], 'r1b': [(None, 'close'), ('forty', 'map:size')],
    'r2a': [(None, 'low'), ('two', 'map:usa250')], 'r2b': [(None, 'ots'), ('Oxford', 'map:oxford')],
    'r3a': [(None, 'close'), ('Sixty', 'map:ukpop')], 'r3b': [(None, 'ots'), ('Three', 'map:uspop')],
    'r4a': [(None, 'two'), ('basketball', 'map:ussport')], 'r4b': [(None, 'low'), ('football', 'map:uksport')],
    'r5a': [(None, 'close'), ('satellite', 'map:prospero')], 'r5b': [(None, 'ots'), ('twelve', 'map:apollo')],
    'r6a': [(None, 'close'), ('seventy', 'map:life_us')], 'r6b': [(None, 'low'), ('eighty', 'map:life')],
    'r7a': [(None, 'two'), ('four', 'map:gdpuk')], 'r7b': [(None, 'low'), ('thirty', 'map:gdpus')],
    'r8a': [(None, 'close'), ('threw', 'map:harbor')], 'r8b': [(None, 'two'), ('one', 'map:cups')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {}}
C.HOT = ('usa', 'uk', 'america', 'tea', 'grandpa', 'rematch', 'harbor', 'war', 'tie', 'tiebreaker', 'comment', 'subscribe', 'winner')
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
        self.ref = {'US': (-98.0, 39.0), 'UK': (-2.5, 54.5)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('US', 'United States of America', ['Canada', 'Mexico', 'Cuba', 'Bahamas']),
                          ('UK', 'United Kingdom', ['Ireland', 'France', 'Belgium', 'Netherlands', 'Norway', 'Denmark', 'Germany', 'Iceland', 'Faeroe Is.'])):
            rs = R(n)
            if k == 'US': rs = [r for r in rs if -126 < r[:, 0].mean() < -66 and 24 < r[:, 1].mean() < 50]
            else: rs = [r for r in rs if -9 < r[:, 0].mean() < 2 and 49 < r[:, 1].mean() < 61]
            pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs if nn in cf for r in local(R(nn), *self.ref[k])]
        self.uk_true = [r - np.concatenate(self.c['UK']).mean(axis=0) for r in self.c['UK']]
        print('areas M km2: mainland usa', round(area(self.c['US']) / 1e6, 2), 'uk', round(area(self.c['UK']) / 1e6, 3), 'ratio', round(area(self.c['US']) / area(self.c['UK']), 1))
        B.FL['USA'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'us.png')); B.FL['UK'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'gb.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'USA' else 'U'
def col_of(name): return US_C if name == 'USA' else UK_C
def rival_of(name): return 'UK' if name == 'USA' else 'USA'
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
def set_of(name, cr, t): (set_usa if name == 'USA' else set_uk)(cr, t)

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
    for n, x in (('USA', 290), ('UK', 790)):
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
def sc_bigben(cr, t, b, t0, t1):
    cr.save(); cam(cr, push(t, t0, t1 + 1, 1.0, 1.3), 0, 780, 760); set_uk(cr, t); cr.restore()
    cr.set_source_rgba(0.02, 0.02, 0.08, 0.25); cr.paint()
    label(cr, 'BIG BEN · 1859', 540, 560, 96, UK_C)
    tb = at('r1a', 'Beatles') - 0.1
    if t >= tb:
        k = pop_k(t, tb); chip(cr, 'THE BEATLES · LIVERPOOL', 540, 680, 46, WHITE, INK, k, 1)
        for j, x in enumerate((180, 330)): emoji(cr, '🎸', x, 1020 - abs(math.sin(t * 5 + j)) * 16, 150 * k, 1, rot=-0.25 + 0.5 * j)
def sc_size(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'US', (0, 0), (0, -100), 0.2, 0.21, t0, t1 + 1.5, US_LAND)
    k = ease_out(prog(t, t0, t0 + 0.5)); cr.save(); cr.translate(0, (1 - k) * -900); km_shape(cr, G.uk_true, cx, cy, s, UK_LAND, 1, 1800, 300, fill=0.95, lw=2, edge=INK); cr.restore()
    if k >= 1: chip(cr, 'UK', cx + 1800 * s, cy - 300 * s - 150, 30, WHITE, INK, 1, 1)
    endmap(cr)
    tx = at('r1b', 'bigger') - 0.1
    if t >= tx:
        sx, sy = shake(t, tx, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'USA = 40 UKs', 540, 640, 110, WHITE, t, tx); cr.restore()
        ptext(cr, 'WITH ALASKA & HAWAII', 540, 730, 32, WHITE, 0.85, fam='Poppins ExtraBold', sw=5)
UKC = [('LONDON', -0.13, 51.51, 9.0), ('BIRMINGHAM', -1.9, 52.48, 2.9), ('MANCHESTER', -2.24, 53.48, 2.8), ('GLASGOW', -4.25, 55.86, 1.7), ('LEEDS', -1.55, 53.8, 1.9), ('BELFAST', -5.93, 54.6, 0.7), ('CARDIFF', -3.18, 51.48, 0.5), ('EDINBURGH', -3.19, 55.95, 0.9)]
def sc_ukpop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'UK', (0, 0), (50, -150), 0.85, 1.0, t0, t1 + 2, UK_LAND)
    for j, (nm, lon, lat, m) in enumerate(UKC):
        x, y = kpt('UK', lon, lat, cx, cy, s); tj = t0 + 0.2 + j * 0.1
        if t >= tj: k = pop_k(t, tj); cr.new_path(); cr.arc(x, y, 14 * math.sqrt(m) * k, 0, 2 * math.pi); cr.set_source_rgba(*UK_C, 0.85); cr.fill()
    lx, ly = kpt('UK', -0.13, 51.51, cx, cy, s); tl = t0 + 0.9; pin(cr, lx, ly, t, tl, WHITE); endmap(cr)
    k = ease_out(prog(t, t0, t0 + 1)); label(cr, f'{69 * k:.0f} MILLION', 540, 620, 104, UK_C)
    if t >= tl: chip(cr, 'LONDON ≈ 9 MILLION', 540, 730, 46, WHITE, INK, pop_k(t, tl), 1)
def sc_uspop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'US', (0, 0), (0, 0), 0.19, 0.2, t0, t1 + 1, US_LAND); k = ease_out(prog(t, t0, at('r3b', 'million') + 0.3))
    dots(cr, 'US', int(1400 * k), cx, cy, s, -125, -67, 25, 49, (1, 0.85, 0.3), 3); endmap(cr); label(cr, f'{342 * k:.0f} MILLION', 540, 620, 104, US_C)
    tm = at('r3b', 'Five') - 0.1
    if t >= tm: chip(cr, '≈ 5× THE UK', 540, 730, 50, GOLD, INK, pop_k(t, tm), 1)
def sc_ussport(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'MADE IN THE USA', 540, 620, 96, US_C)
    emopops(cr, t, 'r4a', [('🏀', 'basketball'), ('🏈', 'Super')], y=1000, size=200)
    for i, (lab, wd) in enumerate((('BASKETBALL · 1891', 'basketball'), ('SUPER BOWL · 1967', 'Super'))):
        tt = at('r4a', wd) - 0.1
        if t >= tt: ptext(cr, lab, 540 + (i - 0.5) * 290, 1180, 34, WHITE, pop_k(t, tt), fam='Poppins ExtraBold', sw=6)
def sc_uksport(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'MADE IN THE UK', 540, 620, 96, UK_C)
    for i, (em, wd) in enumerate((('⚽', 'football'), ('🏉', 'rugby'), ('🎾', 'tennis'), ('⛳', 'golf'))):
        tt = at('r4b', wd) - 0.1
        if t < tt: continue
        x, y = [(540, 980), (220, 1250), (540, 1290), (860, 1250)][i]
        emoji(cr, em, x, y - abs(math.sin(t * 4 + i)) * 12, (230 if i == 0 else 150) * pop_k(t, tt, 0.3), 1, rot=0.1 * math.sin(t * 3 + i))
    tb = at('r4b', 'biggest') - 0.1
    if t >= tb: chip(cr, 'FOOTBALL ≈ 3.5 BILLION FANS', 540, 740, 46, GOLD, INK, pop_k(t, tb), 1)
def sc_prospero(cr, t, b, t0, t1):
    arena(cr, t); k = ease_io(prog(t, t0, t1 + 0.6)); y = lerp(1600, 820, k); x = 540 + 30 * math.sin(t * 2)
    for j in range(16):
        ph = ((t - t0) * 2 + j / 16) % 1; cr.new_path(); cr.arc(x + 40 * math.sin(j * 7.1) * ph, y + 120 + 380 * ph, 20 + 50 * ph, 0, 2 * math.pi); cr.set_source_rgba(1, 0.75 - 0.5 * ph, 0.35, 0.55 * (1 - ph)); cr.fill()
    emoji(cr, '🚀', x, y, 190, 1, rot=-math.pi / 4)
    label(cr, 'BLACK ARROW · 1971', 540, 600, 92, UK_C)
    tb = at('r5a', 'satellite') - 0.1
    if t >= tb: chip(cr, 'PROSPERO · LAUNCHED FROM WOOMERA, AUSTRALIA', 540, 700, 36, WHITE, INK, pop_k(t, tb), 1)
def moon(cr, t):
    cr.set_source_rgb(0.01, 0.01, 0.05); cr.paint(); rng = np.random.default_rng(2)
    for _ in range(160): x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.6); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.4 + 0.4 * math.sin(t * 2 + x)); cr.fill()
    cr.new_path(); cr.arc(540, 2350, 1250, 0, 2 * math.pi); cr.set_source_rgb(0.62, 0.62, 0.66); cr.fill()
    for x, y, r in ((200, 1290, 60), (640, 1350, 90), (950, 1300, 50), (420, 1500, 70), (820, 1560, 110)):
        cr.save(); cr.translate(x, y); cr.scale(1, 0.35); cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(0.5, 0.5, 0.55); cr.fill()
    emoji(cr, '🌍', 860, 820, 140, 1)
def sc_apollo(cr, t, b, t0, t1):
    moon(cr, t); k = prog(t, at('r5b', 'twelve') - 0.2, at('r5b', 'Moon') + 0.3)
    for j in range(int(12 * k + 0.999)):
        x = 130 + (j % 6) * 165; y = 960 + (j // 6) * 190 - abs(math.sin(t * 3 + j)) * 10; kk = pop_k(t, at('r5b', 'twelve') - 0.2 + j * 0.08)
        cr.save(); cr.translate(x, y); cr.scale(kk, kk)
        rrect(cr, -34, -10, 68, 90, 24); cr.set_source_rgb(0.95, 0.95, 0.97); cr.fill(); cr.new_path(); cr.arc(0, -40, 36, 0, 2 * math.pi); cr.fill()
        rrect(cr, -24, -58, 48, 32, 14); cr.set_source_rgb(0.85, 0.65, 0.2); cr.fill(); rrect(cr, -14, 14, 28, 22, 4); cr.set_source_rgb(*US_C); cr.fill(); cr.restore()
    label(cr, f'{int(12 * clamp(k))} MOONWALKERS', 540, 620, 96, US_C); ptext(cr, 'APOLLO 11–17 · 1969–1972', 540, 700, 38, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def pbar(cr, x, base, v, vmin, vmax, k, col, name, lab):
    hh = max(8, 560 * (v - vmin) / (vmax - vmin) * k); rrect(cr, x - 110, base - hh, 220, hh, 18); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    label(cr, lab, x, base - hh - 24, 60, WHITE, clamp(k * 2)); ball(cr, name, x, base + 80, 56, 'happy', 0, 0)
def sc_life_us(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'LIFE EXPECTANCY (YEARS)', 540, 620, 62, WHITE); ptext(cr, 'BARS START AT 60', 540, 690, 28, WHITE, 0.7, fam='Poppins ExtraBold', sw=5)
    k = ease_out(prog(t, at('r6a', 'seventy') - 0.2, at('r6a', 'seventy') + 0.8)); pbar(cr, 330, 1300, 79.0, 60, 90, k, US_C, 'USA', '79.0')
def sc_life(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'LIFE EXPECTANCY (YEARS)', 540, 620, 62, WHITE); ptext(cr, 'BARS START AT 60', 540, 690, 28, WHITE, 0.7, fam='Poppins ExtraBold', sw=5)
    pbar(cr, 330, 1300, 79.0, 60, 90, 1, US_C, 'USA', '79.0'); k = ease_out(prog(t, at('r6b', 'eighty') - 0.2, at('r6b', 'eighty') + 0.8)); pbar(cr, 750, 1300, 81.0, 60, 90, k, UK_C, 'UK', '81.0')
    tw0 = at('r6b', 'Must') - 0.1
    if t >= tw0: chip(cr, 'MUST BE THE TEA', 540, 1450, 46, GOLD, INK, pop_k(t, tw0), 1); emoji(cr, '☕', 880, 1440, 110 * pop_k(t, tw0), 1, rot=0.1 * math.sin(t * 4))
def gdp_circle(cr, x, y, g, col, k, lab, size=50):
    r = 240 * math.sqrt(g / 31.0) * k
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.92); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    if lab: ptext(cr, lab, x, y + size * 0.35, size, INK if col != US_C else WHITE, clamp(k), sw=0, shadow=False)
def sc_gdpuk(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2025', 540, 620, 60, WHITE); k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 540, 1050, 4.0, UK_C, 0.2 + 0.8 * k, f'${4.0 * k:.1f}T', 40)
def sc_gdpus(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2025', 540, 620, 60, WHITE); k = ease_out(prog(t, t0, t0 + 1.0)); gdp_circle(cr, 470, 1050, 30.6, US_C, 0.2 + 0.8 * k, f'${30.6 * k:.1f}T', 84)
    gdp_circle(cr, 900, 1260, 4.0, UK_C, 1, '', 30); ptext(cr, 'UK', 900, 1360, 34, UK_C, 1, fam='Poppins ExtraBold', sw=6)
    tj = at('r7b', 'almost') - 0.1
    if t >= tj: slam(cr, '≈ 8 UKs', 540, 760, 100, GOLD, t, tj)
NCR, CR_FALL = 14, 0.65
def harbor(cr, t, c0, c1, n=NCR):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.02, 0.04, 0.14); g.add_color_stop_rgb(0.6, 0.1, 0.14, 0.32); g.add_color_stop_rgb(1, 0.03, 0.06, 0.16); cr.set_source(g); cr.paint()
    rng = np.random.default_rng(8)
    for _ in range(80): x, y = rng.uniform(0, W), rng.uniform(0, 700); cr.new_path(); cr.arc(x, y, 1.6, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.4 + 0.3 * math.sin(t * 2 + x)); cr.fill()
    cr.new_path(); cr.arc(820, 330, 70, 0, 2 * math.pi); cr.set_source_rgb(0.98, 0.95, 0.82); cr.fill()
    bob = 6 * math.sin(t * 1.6)
    cr.save(); cr.translate(0, bob)
    for mx, mh in ((260, 560), (470, 640), (660, 520)):
        cr.rectangle(mx - 7, 1080 - mh, 14, mh); cr.set_source_rgb(0.25, 0.16, 0.1); cr.fill()
        for yy, wd in ((1080 - mh + 60, 150), (1080 - mh + 230, 190)): cr.rectangle(mx - wd / 2, yy, wd, 130); cr.set_source_rgba(0.92, 0.88, 0.78, 0.9); cr.fill()
    cr.new_path(); cr.move_to(110, 1060); cr.line_to(820, 1060); cr.line_to(760, 1200); cr.line_to(170, 1200); cr.close_path(); cr.set_source_rgb(0.36, 0.22, 0.12); cr.fill()
    for j in range(7): cr.new_path(); cr.arc(220 + j * 85, 1120, 12, 0, 2 * math.pi); cr.set_source_rgb(0.95, 0.75, 0.35); cr.fill()
    cr.restore()
    cr.rectangle(0, 1180, W, H - 1180); cr.set_source_rgb(0.05, 0.16, 0.3); cr.fill()
    for j in range(14):
        y = 1210 + j * 50; cr.move_to(0, y)
        for x in range(0, W + 40, 40): cr.line_to(x, y + 8 * math.sin(x / 60 + t * 2 + j))
        cr.set_source_rgba(0.5, 0.7, 1, 0.18); cr.set_line_width(3); cr.stroke()
    for j in range(n):
        tj = c0 + j * (c1 - c0) / n
        if t < tj: continue
        ph = t - tj; x0 = 280 + (j * 47) % 420; xx = x0 + 330 * min(ph, CR_FALL)
        if ph < CR_FALL: yy = 1040 - 720 * ph + 1400 * ph * ph; rot = ph * 7
        else: yy = 1205 + 6 * math.sin(t * 3 + j); rot = 0.3 * math.sin(t * 2 + j)
        if ph >= CR_FALL:
            sp = ph - CR_FALL
            for q in range(2):
                f = clamp(sp * 1.6 - q * 0.3)
                if 0 < f < 1: cr.save(); cr.translate(xx, 1205); cr.scale(1, 0.3); cr.new_path(); cr.arc(0, 0, 40 + 160 * f, 0, 2 * math.pi); cr.restore(); cr.set_source_rgba(1, 1, 1, 0.8 * (1 - f)); cr.set_line_width(5); cr.stroke()
            if sp < 0.4:
                for q in range(8): a = math.pi + q / 7 * math.pi; r = 260 * sp; cr.new_path(); cr.arc(xx + r * math.cos(a) * 0.8, 1200 + r * math.sin(a) + 500 * sp * sp, 7, 0, 2 * math.pi); cr.set_source_rgba(0.85, 0.93, 1, 1 - sp / 0.4); cr.fill()
        cr.save(); cr.translate(xx, yy); cr.rotate(rot); rrect(cr, -38, -30, 76, 60, 6); cr.set_source_rgb(0.62, 0.42, 0.22); cr.fill_preserve(); cr.set_source_rgb(0.3, 0.18, 0.08); cr.set_line_width(4); cr.stroke()
        ptext(cr, 'TEA', 0, 9, 24, (0.25, 0.12, 0.05), 1, fam='Poppins ExtraBold', sw=0, shadow=False); cr.restore()
def sc_harbor(cr, t, b, t0, t1):
    cr.save(); cr.translate(0, 260); harbor(cr, t, t0 + 0.1, t1 + 0.6, 6); cr.restore(); label(cr, 'BOSTON TEA PARTY · 1773', 540, 620, 70, US_C)
def sc_cups(cr, t, b, t0, t1):
    arena(cr, t); k = ease_out(prog(t, t0, at('r8b', 'cups') + 0.4)); n = int(48 * k)
    for j in range(n): x = 150 + (j % 6) * 156; y = 860 + (j // 6) * 86 - abs(math.sin(t * 4 + j)) * 6; emoji(cr, '☕', x, y, 74 * pop_k(t, t0 + j * (at('r8b', 'cups') + 0.4 - t0) / 48, 0.2), 1)
    label(cr, f'{int(100 * k)} MILLION CUPS', 540, 620, 86, UK_C)
    te = at('r8b', 'Every') - 0.1
    if t >= te: chip(cr, 'EVERY. SINGLE. DAY.', 540, 730, 50, GOLD, INK, pop_k(t, te), 1)
def sc_usa250(cr, t, b, t0, t1):
    set_usa(cr, t); cr.set_source_rgba(0.02, 0.02, 0.08, 0.45); cr.paint()
    for j in range(6):
        ph = ((t - t0) * 0.7 + j / 6) % 1; x = 150 + (j * 173) % 800; y = 900 - 300 * j % 3 * 0.3
        for q in range(14):
            a = q / 14 * 2 * math.pi; r = 140 * ph; cr.new_path(); cr.arc(x + r * math.cos(a), 700 + 120 * (j % 3) + r * math.sin(a), 6 * (1 - ph) + 1, 0, 2 * math.pi); cr.set_source_rgba(*((1, 0.3, 0.35) if j % 3 == 0 else (1, 1, 1) if j % 3 == 1 else (0.35, 0.55, 1)), 1 - ph); cr.fill()
    k = pop_k(t, at('r2a', 'two') - 0.1) if t >= at('r2a', 'two') - 0.1 else 0
    if k: cr.save(); cr.translate(540, 1150); cr.scale(k, k); ptext(cr, '250', 0, 0, 280, GOLD, 1, sw=20); cr.restore()
    label(cr, '1776 TO 2026', 540, 620, 90, WHITE)
def sc_oxford(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'OXFORD: TEACHING SINCE 1096', 540, 620, 62, UK_C)
    x0, x1, y = 120, 960, 1150; k = ease_io(prog(t, at('r2b', 'Oxford') - 0.2, at('r2b', 'Empire') + 0.3))
    cr.move_to(x0, y); cr.line_to(x1, y); cr.set_source_rgba(1, 1, 1, 0.3); cr.set_line_width(8); cr.stroke()
    cr.move_to(x0, y); cr.line_to(lerp(x0, x1, k), y); cr.set_source_rgb(*UK_C); cr.set_line_width(12); cr.stroke()
    for yr, em, col, nm in ((1096, '🎓', UK_C, 'OXFORD'), (1428, '🛕', GOLD, 'AZTEC EMPIRE'), (1776, '🗽', US_C, 'USA'), (2026, '📍', WHITE, 'NOW')):
        f = (yr - 1096) / (2026 - 1096); x = lerp(x0, x1, f)
        if k >= f - 0.01:
            emoji(cr, em, x, y - 120, 100, 1); ptext(cr, str(yr), x, y + 70, 44, col, 1, sw=7); ptext(cr, nm, x, y + 120, 26, WHITE, 1, fam='Poppins ExtraBold', sw=5)
    ta = at('r2b', 'Aztec') - 0.1
    if t >= ta: chip(cr, '332 YEARS OLDER', 540, 880, 50, GOLD, INK, pop_k(t, ta), 1)
SCENE = {'bigben': sc_bigben, 'size': sc_size, 'ukpop': sc_ukpop, 'uspop': sc_uspop, 'ussport': sc_ussport, 'uksport': sc_uksport, 'prospero': sc_prospero, 'apollo': sc_apollo,
         'life_us': sc_life_us, 'life': sc_life, 'gdpuk': sc_gdpuk, 'gdpus': sc_gdpus, 'usa250': sc_usa250, 'oxford': sc_oxford, 'harbor': sc_harbor, 'cups': sc_cups}

# ---------- hook, close-ups, title ----------
def crate_win(): return w('h3', 'dumped') - 0.1, w('h3', 'Harbor') + 0.1
def draw_hook(cr, t):
    """Cold open: UK demands the tea money, USA snaps back, then the Boston Tea Party crates hit the water."""
    if t >= bt('title')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        sh_close(cr, t, b1, 'UK', 0, b1['end'], 'angry'); emoji(cr, '☕', 880, 820, 150 * pop_k(t, w('h1', 'tea') - 0.1, 0.3) if t >= w('h1', 'tea') - 0.1 else 0, 1, rot=-0.1 + 0.05 * math.sin(t * 3))
        return True
    if t < b3['start']:
        sx, sy = shake(t, w('h2', 'grandpa') - 0.05, 20, 0.4); cr.save(); cr.translate(sx, sy)
        sh_low(cr, t, b2, 'USA', b2['start'], b2['end'], 'angry'); cr.restore()
        emoji(cr, '🦅', 860, 820, 140 * pop_k(t, b2['l0'], 0.3), 1)
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2)))
        return True
    c0, c1 = crate_win()
    cr.save(); cam(cr, push(t, b3['start'], b3['end'], 1.0, 1.08), 0.0, 540, 1100); harbor(cr, t, c0, c1); cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
    ty = w('h3', 'seventeen') - 0.1
    if t >= ty: label(cr, 'BOSTON · 1773', 540, 230, 80, WHITE, pop_k(t, ty))
    tn = w('h3', 'three') - 0.1
    if t >= tn:
        n = int(342 * clamp(prog(t, tn, w('h3', 'chests') + 0.2))); sx, sy = shake(t, tn, 6, 0.12)
        cr.save(); cr.translate(sx, sy); ptext(cr, f'{n} CHESTS OF TEA', 540, 360, 84, GOLD, 1, sw=12); cr.restore()
    ts = w('h3', 'years') - 0.2
    if t >= ts:
        cr.set_source_rgba(0, 0, 0.05, 0.5 * clamp((t - ts) * 4)); cr.paint()
        sx, sy = shake(t, ts, 18); cr.save(); cr.translate(sx, sy); slam(cr, '250 YEARS LATER…'.replace('…', ''), 540, 820, 110, WHITE, t, ts)
        tr = w('h3', 'rematch') - 0.1
        if t >= tr: slam(cr, 'THE REMATCH', 540, 990, 140, GOLD, t, tr)
        cr.restore()
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
    ball(cr, 'USA', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'UK', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'USA', 540, 560, 210, US_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'UK', 540, 980, 210, UK_C, t, w('title', 'winner'))
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
    for side, x, col, sc, lab in (('A', 250, US_C, sn, 'USA'), ('U', 830, UK_C, ss, 'UK')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = f'ROUND {i}/8' if i else ('FINAL: 4 — 4' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📏', 2: '🏰', 3: '👥', 4: '⚽', 5: '🚀', 6: '❤️', 7: '💰', 8: '☕'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((US_C, UK_C)):
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
    col = US_C if win == 'A' else UK_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('USA' if win == 'A' else 'UK') + ' WINS'
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
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540, 1100); set_uk(cr, t)
        ball(cr, 'UK', 540, 1260 - h * 50, 300, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'UK', 540, 1640, UK_C); emoji(cr, '☕', 200, 900, 140 * pop_k(t, e2['l0'] + 0.4), 1)
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.06), 0.02, 540, 1000); arena(cr, t)
    for n, x, lk in (('USA', 290, 0.8), ('UK', 790, -0.8)): ball(cr, n, x, 1280 - abs(math.sin(t * 5 + x)) * 10, 170, 'angry', 0, lk)
    emoji(cr, '⚡', 540, 1280, 140, 1, rot=0.2 * math.sin(t * 10)); cr.restore()
    sx, sy = shake(t, c['start'], 16, 0.4); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A TIE!", 540, 470, 140, GOLD, t, c['start']); cr.restore()
    ptext(cr, 'USA', 220, 590, 60, US_C, 1, sw=8); ptext(cr, '4 — 4', 540, 600, 84, WHITE, 1, sw=10); ptext(cr, 'UK', 860, 590, 60, UK_C, 1, sw=8)
    tp = w('cta', 'pick') - 0.1
    if t >= tp:
        kk = pop_k(t, tp); cr.save(); cr.translate(540, 730); cr.scale(kk, kk); ptext(cr, 'YOU PICK THE TIEBREAKER', 0, 0, 66, WHITE, 1, sw=9); cr.restore()
        for j, (em, lab) in enumerate((('🎵', 'MUSIC?'), ('🍔', 'FOOD?'), ('🎬', 'MOVIES?'))):
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
    boom(0.0, 1.0); rumble(0.0, 1.0, 0.25); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(w('h2', 'grandpa') - 0.05, 0.8)
    whoosh(bt('h3')['start'] - 0.3, 0.3); c0, c1 = crate_win()
    for j in range(NCR): tl_ = c0 + j * (c1 - c0) / NCR + CR_FALL; whoosh(tl_ - 0.05, 0.22, 0.18); pop(tl_, 0.09, 260 + 15 * j)
    boom(w('h3', 'years') - 0.2, 0.9); boom(w('h3', 'rematch') - 0.1, 1.0); whoosh(bt('title')['start'] - 0.35)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_ukus'))
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
