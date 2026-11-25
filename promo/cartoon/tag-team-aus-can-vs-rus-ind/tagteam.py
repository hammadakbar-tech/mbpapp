# Countryballs: Australia + Canada vs Russia + India, the Tag Team War, the Geography War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (oil sands, the Pilbara, maple syrup, gold...).
# Usage: python3 tagteam.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

A_C, U_C = hexc('#FFC233')[:3], hexc('#4F8CFF')[:3]   # team AUS+CAN gold, team RUS+IND blue
AU_C, CA_C = A_C, U_C
TEAM_A, TEAM_U = 'AUS + CAN', 'RUS + IND'
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Australia': ('en-AU-WilliamNeural', '+4%'), 'Canada': ('en-CA-LiamNeural', '+4%'), 'Russia': ('bg-BG-BorislavNeural', '+0%'), 'India': ('en-IN-PrabhatNeural', '+4%')}
TEAM_SGN = {'Australia': -1, 'Canada': -1, 'Russia': 1, 'India': 1}
LINES = [
    ('h1', 'Australia', "Canada! Team-up, mate?"),
    ('h2', 'Canada', "Sorry... against who, eh?"),
    ('h3', 'Russia', "Against the biggest country on Earth."),
    ('h4', 'India', "And the most people on Earth!"),
    ('title', None, "Two versus two. Eight rounds. One winning team. This is the tag team war."),
    ('c1', None, "Round one: size."),
    ('r1a', 'Canada', "Together, we're almost eighteen million square kilometres!"),
    ('r1b', 'Russia', "I alone am seventeen million. With India? Over twenty."),
    ('c2', None, "Round two: people."),
    ('r2a', 'Australia', "Seventy million of us, mate!"),
    ('r2b', 'India', "Seventy million? I have one point four six billion. The most people on Earth!"),
    ('c3', None, "Round three: coastline."),
    ('r3a', 'Russia', "My Arctic coast is very, very long."),
    ('r3b', 'Canada', "And I have the longest coastline on Earth. With Australia, over three hundred thousand kilometres!"),
    ('c4', None, "Round four: cold."),
    ('r4a', 'Canada', "Snag, Yukon: minus sixty-three degrees!"),
    ('r4b', 'Russia', "Oymyakon: minus sixty-eight. And people live there, every winter."),
    ('c5', None, "Round five: money per person."),
    ('r5a', 'India', "My economy is one of the fastest growing on Earth!"),
    ('r5b', 'Australia', "Fair. But per person, we both make over fifty-five thousand dollars. You two? Under twenty."),
    ('c6', None, "Round six: cricket."),
    ('r6a', 'India', "Cricket is life! Two World Cups!"),
    ('r6b', 'Australia', "Love it, mate. But I've won six."),
    ('c7', None, "Round seven: space."),
    ('r7a', 'Canada', "I built the Canadarm for the space shuttle!"),
    ('r7b', 'Russia', "I sent the first satellite and the first human into space. And India landed near the Moon's south pole first!"),
    ('c8', None, "Round eight: living longer."),
    ('r8a', 'Russia', "We are tough. Strong people!"),
    ('r8b', 'Australia', "Strong, sure. But Aussies and Canadians live past eighty. About ten years longer!"),
    ('e1', 'Australia', "Four all?! Nobody wins?"),
    ('e2', 'India', "Then let the viewers decide!"),
    ('cta', None, "It's a tie! You pick the tiebreaker. Comment it below, and subscribe to see who wins!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SIZE', 'U', ('r1b', 'twenty')), 2: ('PEOPLE', 'U', ('r2b', 'Earth')), 3: ('COASTLINE', 'A', ('r3b', 'thousand')), 4: ('COLD', 'U', ('r4b', 'winter')),
      5: ('MONEY PER PERSON', 'A', ('r5b', 'twenty')), 6: ('CRICKET', 'A', ('r6b', 'six')), 7: ('SPACE', 'U', ('r7b', 'first', 2)), 8: ('LIVING LONGER', 'A', ('r8b', 'longer'))}
NR = 8
SHOTS = {
    'r1a': [(None, 'two'), ('almost', 'map:sizeA')], 'r1b': [(None, 'low'), ('seventeen', 'map:sizeB')],
    'r2a': [(None, 'close'), ('million', 'map:popA')], 'r2b': [(None, 'ots'), ('one', 'map:popB')],
    'r3a': [(None, 'two'), ('Arctic', 'map:arctic')], 'r3b': [(None, 'close'), ('longest', 'map:coast')],
    'r4a': [(None, 'low'), ('Snag', 'map:snag')], 'r4b': [(None, 'ots'), ('Oymyakon', 'map:oymyakon')],
    'r5a': [(None, 'close'), ('fastest', 'map:growth')], 'r5b': [(None, 'two'), ('person', 'map:percap')],
    'r6a': [(None, 'low'), ('Two', 'map:crickin')], 'r6b': [(None, 'ots'), ('six', 'map:crickau')],
    'r7a': [(None, 'close'), ('Canadarm', 'map:canadarm')], 'r7b': [(None, 'two'), ('first', 'map:space')],
    'r8a': [(None, 'low'), ('Strong', 'close')], 'r8b': [(None, 'ots'), ('eighty', 'map:life')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3', 'h4')
C.SAY = {None: {'Oymyakon': 'Oy-ya-kon', 'Phalodi': 'Pha-lo-dee', 'Canadarm': 'Canada-arm'}}
C.HOT = ('australia', 'canada', 'russia', 'india', 'team', 'war', 'tiebreaker', 'heat', 'comment', 'subscribe', 'billion', 'million', 'thousand')
C.TAIL_OVERRIDE = {'h1': 0.12, 'h2': 0.15, 'h3': 0.12, 'h4': 0.35, 'title': 0.6, 'e1': 0.3, 'e2': 0.4, 'cta': 3.6, **{f'c{i}': 0.15 for i in range(1, 9)},
                   **{k: 0.3 for k, s, _ in LINES if s and k[0] == 'r'}, **{RD[i][2][0]: 1.1 for i in RD}}
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
        B.FL['Russia'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'ru.png')); B.FL['India'] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', 'in.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if TEAM_SGN[name] < 0 else 'U'
def col_of(name): return AU_C if TEAM_SGN[name] < 0 else CA_C
RIVAL = {'Australia': 'India', 'Canada': 'Russia', 'Russia': 'Canada', 'India': 'Australia'}
PARTNER = {'Australia': 'Canada', 'Canada': 'Australia', 'Russia': 'India', 'India': 'Russia'}
def rival_of(name): return RIVAL[name]
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
def set_russia(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.05, 0.16); g.add_color_stop_rgb(0.6, 0.18, 0.26, 0.42); g.add_color_stop_rgb(1, 0.5, 0.58, 0.72); cr.set_source(g); cr.paint()
    for j, (x, h, wd) in enumerate(((720, 520, 120), (880, 420, 100), (580, 380, 90), (1000, 330, 80))):  # onion domes
        cr.rectangle(x - wd * 0.45, 1400 - h, wd * 0.9, h); cr.set_source_rgb(0.12, 0.14, 0.24); cr.fill()
        top = 1400 - h; cr.new_path(); cr.move_to(x - wd * 0.6, top); cr.curve_to(x - wd * 0.8, top - wd * 0.7, x - wd * 0.1, top - wd * 0.9, x, top - wd * 1.4)
        cr.curve_to(x + wd * 0.1, top - wd * 0.9, x + wd * 0.8, top - wd * 0.7, x + wd * 0.6, top); cr.close_path(); cr.set_source_rgb(*((0.75, 0.2, 0.25) if j % 2 else (0.2, 0.55, 0.45))); cr.fill()
    for j in range(7):
        x = 60 + j * 70; cr.rectangle(x, 1080 + (j % 3) * 30, 14, 400); cr.set_source_rgb(0.92, 0.92, 0.9); cr.fill()
        for k in range(5): cr.rectangle(x, 1120 + k * 70 + (j % 3) * 30, 14, 8); cr.set_source_rgb(0.15, 0.15, 0.15); cr.fill()
    cr.rectangle(-200, 1400, 1500, 700); cr.set_source_rgb(0.9, 0.93, 0.97); cr.fill()
    for j in range(60):
        ph = (t * 0.12 + j * 0.37) % 1; cr.new_path(); cr.arc((j * 97 + 30 * math.sin(t + j)) % 1100, ph * 1900, 4, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.8); cr.fill()
def set_india(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.98, 0.55, 0.22); g.add_color_stop_rgb(0.55, 1.0, 0.78, 0.45); g.add_color_stop_rgb(1, 0.6, 0.3, 0.2); cr.set_source(g); cr.paint()
    cr.new_path(); cr.arc(300, 820, 140, 0, 2 * math.pi); cr.set_source_rgba(1, 0.95, 0.8, 0.9); cr.fill()
    x0, base = 760, 1320  # domed monument silhouette
    cr.rectangle(x0 - 210, base - 260, 420, 260); cr.set_source_rgb(0.98, 0.94, 0.9); cr.fill()
    cr.new_path(); cr.move_to(x0 - 130, base - 260); cr.curve_to(x0 - 190, base - 480, x0 - 20, base - 520, x0, base - 600); cr.curve_to(x0 + 20, base - 520, x0 + 190, base - 480, x0 + 130, base - 260); cr.close_path(); cr.fill()
    for dx in (-290, 290): cr.rectangle(x0 + dx - 18, base - 480, 36, 480); cr.fill(); cr.new_path(); cr.arc(x0 + dx, base - 480, 26, math.pi, 2 * math.pi); cr.fill()
    cr.rectangle(x0 - 60, base - 160, 120, 160); cr.set_source_rgb(0.85, 0.75, 0.68); cr.fill()
    cr.rectangle(-200, base, 1500, 800); cr.set_source_rgb(0.72, 0.45, 0.3); cr.fill()
    for j in range(10): cr.new_path(); cr.arc(80 + j * 110, base + 60 + (j % 2) * 30, 14, 0, 2 * math.pi); cr.set_source_rgba(1, 0.6, 0.1, 0.8); cr.fill()
def set_of(name, cr, t): {'Australia': set_australia, 'Canada': set_canada, 'Russia': set_russia, 'India': set_india}[name](cr, t)

# ---------- shots ----------
def sh_close(cr, t, b, name, t0, t1, mood='happy'):
    sgn = TEAM_SGN[name]; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.07 * sgn * (1 if sum(map(ord, b['key'])) % 2 else -1), 540, 1100); set_of(name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1, mood='happy'):
    sgn = TEAM_SGN[name]; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, mood, 0.04 * h, -sgn * 0.2); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_ots(cr, t, b, name, t0, t1):
    sgn = TEAM_SGN[name]; h = hop_of(t, b); rv = rival_of(name)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.06), 0.02 * sgn, 540 + lerp(0, -sgn * 40, prog(t, t0, t1)), 1000); set_of(name, cr, t)
    ball(cr, name, 540 + sgn * 150, 1080 - h * 36, 210, 'happy', 0.05 * h, -sgn * 0.6)
    ball(cr, rv, 540 - sgn * 470, 1700, 560, 'angry', 0, sgn * 0.9); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.paint()
    bubble(cr, t, b, 540 + sgn * 150, 520); nametag(cr, name, 540 + sgn * 150, 1340, col_of(name))
def sh_two(cr, t, b, name, t0, t1):
    sgn = TEAM_SGN[name]; h = hop_of(t, b); pan = lerp(-50, 50, prog(t, t0, t1)) * sgn
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    for n, x in (('Canada', 170), ('Australia', 400), ('India', 680), ('Russia', 910)):
        hh = h if n == name else 0; me = n == name; ball(cr, n, x, 1320 - hh * 40 - (30 if me else 0), 150 if me else 125, 'happy' if side_of(n) == side_of(name) else 'angry', 0.05 * hh, -TEAM_SGN[n] * 0.8)
    cr.restore()
    sx = {'Canada': 170, 'Australia': 400, 'India': 680, 'Russia': 910}[name] - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1560, col_of(name))
def sh_react(cr, t, b, name, t0, t1):
    rv = rival_of(name); k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.25, 1.08, k), 0.06 * TEAM_SGN[rv], 540 + sx, 1080 + sy); set_of(rv, cr, t)
    ball(cr, rv, 540, 1150, 360, 'shock', 0, 0); cr.restore()
    ptext(cr, '?!', 860, 760, 170, GOLD, pop_k(t, t0 + 0.05), sw=14)
    nametag(cr, rv, 540, 1640, col_of(rv))
def sh_map(cr, t, b, name, t0, t1, scene):
    SCENE[scene](cr, t, b, t0, t1)
    sgn = TEAM_SGN[name]; h = hop_of(t, b); x = 540 + sgn * 380
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
AREA = {'Australia': 7.69, 'Canada': 9.98, 'Russia': 17.1, 'India': 3.29}
def sq(cr, name, x, ybase, k, col):
    s = 108 * math.sqrt(AREA[name]) * k
    if s < 2: return
    rrect(cr, x - s / 2, ybase - s, s, s, 10); cr.set_source_rgba(*col, 0.85); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(4); cr.stroke()
    ball(cr, name, x, ybase - s / 2, min(60, s * 0.3), 'happy', 0, 0); ptext(cr, f'{AREA[name]:.1f}M', x, ybase + 44, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_sizeA(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'AREA (MILLION KM²)', 540, 620, 60, WHITE); k = ease_out(prog(t, t0, t0 + 0.7))
    sq(cr, 'Australia', 300, 1300, k, AU_C); sq(cr, 'Canada', 700, 1300, k, AU_C); label(cr, f'{17.7 * k:.1f}M', 540, 760, 90, AU_C)
def sc_sizeB(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'AREA (MILLION KM²)', 540, 620, 60, WHITE); k = ease_out(prog(t, t0, t0 + 0.8))
    sq(cr, 'Russia', 380, 1340, k, CA_C); ki = ease_out(prog(t, at('r1b', 'India') - 0.2, at('r1b', 'India') + 0.4)); sq(cr, 'India', 860, 1340, ki, CA_C)
    label(cr, f'{17.1 * k + 3.3 * ki:.1f}M', 540, 760, 90, CA_C); chip(cr, f'{TEAM_A}: 17.7M', 540, 850, 40, AU_C, INK, 1, 1)
def figs(cr, x0, y0, n, cols, col, dx=30, dy=44, sc=1.0):
    for j in range(n):
        x, y = x0 + (j % cols) * dx, y0 + (j // cols) * dy
        cr.new_path(); cr.arc(x, y - 9 * sc, 7.5 * sc, 0, 2 * math.pi); cr.rectangle(x - 8 * sc, y - 1 * sc, 16 * sc, 20 * sc); cr.set_source_rgb(*col); cr.fill()
def sc_popA(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'PEOPLE · EACH FIGURE = 10 MILLION', 540, 620, 46, WHITE); k = ease_out(prog(t, t0, t0 + 0.8))
    figs(cr, 400, 900, int(7 * k), 7, AU_C, 46, 60, 1.6); label(cr, f'{70 * k:.0f} MILLION', 540, 1100, 90, AU_C); ptext(cr, TEAM_A, 540, 1180, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_popB(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'PEOPLE · EACH FIGURE = 10 MILLION', 540, 620, 46, WHITE); figs(cr, 400, 720, 7, 7, AU_C, 46, 60, 1.6)
    k = ease_out(prog(t, t0, at('r2b', 'billion') + 0.5)); figs(cr, 130, 860, int(160 * k), 20, CA_C, 43, 50, 1.0)
    label(cr, f'{1.6 * k:.2f} BILLION', 540, 1420, 90, CA_C); ptext(cr, 'INDIA ALONE: 1.46 BILLION', 540, 1490, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_arctic(cr, t, b, t0, t1):
    set_russia(cr, t); cr.set_source_rgba(0.02, 0.04, 0.1, 0.35); cr.paint()
    ph = prog(t, t0, t1 + 1); emoji(cr, '🚢', lerp(-100, 1180, ph), 1180, 150, 1); emoji(cr, '🧊', 260, 1300, 120, 1); emoji(cr, '🐻‍❄️', 820, 1260, 120, 1)
    label(cr, 'RUSSIA: ~37,650 KM', 540, 620, 86, CA_C); ptext(cr, 'MOSTLY ARCTIC COAST', 540, 700, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_coast(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, 0), (0, 300), 0.15, 0.17, t0, t1 + 2, CA_LAND)
    te = at('r3b', 'kilometres') + 0.3; k = ease_io(prog(t, t0 + 0.1, te)); rings_ = sorted(G.c['CA'], key=lambda r: -len(r)); tot = sum(len(r) for r in rings_); done = 0
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    for r in rings_:
        m = int(clamp((k * tot - done) / len(r)) * len(r)); done += len(r)
        if m < 2: continue
        for wd, al in ((9, 0.3), (3, 1)):
            cr.new_path(); cr.move_to(cx + r[0, 0] * s, cy - r[0, 1] * s); [cr.line_to(cx + x * s, cy - y * s) for x, y in r[1:m]]; cr.set_source_rgba(1, 1, 1, al); cr.set_line_width(wd); cr.stroke()
    endmap(cr); label(cr, f'{int(243042 * k):,} KM', 540, 620, 100, AU_C); ptext(cr, 'CANADA: LONGEST COASTLINE ON EARTH', 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    ta = at('r3b', 'Australia') - 0.1
    if t >= ta: chip(cr, '+ AUSTRALIA 59,736 KM ≈ 300,000 KM', 540, 800, 40, GOLD, INK, pop_k(t, ta), 1)
def thermo(cr, k, v, vmin, vmax, x=880, y=1030, col=(1, 0.35, 0.2), mark=None):
    rrect(cr, x - 34, y - 300, 68, 360, 34); cr.set_source_rgb(1, 1, 1); cr.fill(); cr.new_path(); cr.arc(x, y + 70, 60, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill()
    f = (lerp(vmin if v > 0 else 20, v, k) - vmin) / (vmax - vmin); hh = max(20, 330 * f); rrect(cr, x - 18, y + 40 - hh, 36, hh, 18); cr.set_source_rgb(*col); cr.fill()
    if mark:
        mv, ml = mark; my = y + 40 - 330 * (mv - vmin) / (vmax - vmin); cr.rectangle(x - 70, my - 3, 140, 6); cr.set_source_rgb(*AU_C); cr.fill(); ptext(cr, ml, x - 90, my + 12, 30, AU_C, 1, fam='Poppins ExtraBold', anchor='r', sw=5)
def frost(cr, k):
    g = cairo.RadialGradient(540, 960, 300, 540, 960, 1100); g.add_color_stop_rgba(0, 0.8, 0.95, 1, 0); g.add_color_stop_rgba(1, 0.8, 0.95, 1, 0.35 * clamp(k)); cr.set_source(g); cr.paint()
def sc_snag(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, 0), tuple(G.p('CA', -137, 63)), 0.15, 0.55, t0, t0 + 1.1, CA_LAND)
    x, y = kpt('CA', -140.4, 62.37, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (0.6, 0.9, 1)); endmap(cr)
    k = ease_out(prog(t, at('r4a', 'minus') - 0.2, at('r4a', 'degrees') + 0.3)); thermo(cr, k, -63, -70, 55, col=(0.3, 0.6, 1))
    label(cr, 'SNAG, YUKON · 1947', 540, 620, 76, WHITE)
    if k > 0: label(cr, f'{-63 * k:.0f}°C', 560, 1000, 130, (0.7, 0.92, 1), clamp(k * 3))
    frost(cr, k)
def sc_oymyakon(cr, t, b, t0, t1):
    set_russia(cr, t); cr.set_source_rgba(0.02, 0.04, 0.1, 0.3); cr.paint()
    k = ease_out(prog(t, at('r4b', 'minus') - 0.2, w('r4b', 'sixty', end=True) + 0.3)); thermo(cr, k, -67.7, -70, 55, col=(0.3, 0.6, 1), mark=(-63, 'SNAG −63'))
    label(cr, 'OYMYAKON, SIBERIA', 540, 620, 80, WHITE); ptext(cr, 'COLDEST TOWN WHERE PEOPLE LIVE', 540, 700, 36, CA_C, 1, fam='Poppins ExtraBold', sw=6)
    if k > 0: label(cr, f'{-67.7 * k:.1f}°C', 500, 1000, 130, (0.7, 0.92, 1), clamp(k * 3))
    frost(cr, k * 1.3)
def sc_growth(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'ONE OF THE FASTEST-GROWING', 540, 620, 60, CA_C); ptext(cr, 'MAJOR ECONOMIES · ~6–7% A YEAR', 540, 690, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    k = ease_io(prog(t, t0, t1 + 0.5)); pts = [(140 + i * 26, 1400 - (i ** 1.5) * 3.6) for i in range(31)]; n = max(2, int(31 * k))
    cr.new_path(); cr.move_to(*pts[0]); [cr.line_to(*p) for p in pts[1:n]]; cr.set_source_rgb(*CA_C); cr.set_line_width(14); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
    emoji(cr, '🚀', pts[n - 1][0] + 30, pts[n - 1][1] - 40, 110, 1, rot=-0.6)
def pbar(cr, x, base, v, vmax, k, col, name, lab):
    hh = max(8, 520 * v / vmax * k); rrect(cr, x - 80, base - hh, 160, hh, 16); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(4); cr.stroke()
    ptext(cr, lab, x, base - hh - 20, 40, WHITE, clamp(k * 2), sw=6); ball(cr, name, x, base + 70, 46, 'happy', 0, 0)
def sc_percap(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP PER PERSON (US$)', 540, 620, 62, WHITE); k = ease_out(prog(t, t0, at('r5b', 'dollars') + 0.2)); k2 = ease_out(prog(t, at('r5b', 'two') - 0.2, at('r5b', 'twenty') + 0.3))
    for x, n, v, lab, kk, col in ((160, 'Australia', 70, '~$70K', k, AU_C), (400, 'Canada', 58, '~$58K', k, AU_C), (680, 'Russia', 17, '~$17K', k2, CA_C), (920, 'India', 2.9, '~$3K', k2, CA_C)):
        pbar(cr, x, 1320, v, 72, kk, col, n, lab)
def trophies(cr, t, years, t0, y=1000, col=WHITE):
    for j, yr in enumerate(years):
        tj = t0 + j * 0.12
        if t < tj: continue
        x = 540 + (j - (len(years) - 1) / 2) * 150; emoji(cr, '🏆', x, y, 120 * pop_k(t, tj), 1); ptext(cr, str(yr), x, y + 100, 34, col, 1, fam='Poppins ExtraBold', sw=6)
def sc_crickin(cr, t, b, t0, t1):
    set_india(cr, t); cr.set_source_rgba(0.1, 0.04, 0.02, 0.35); cr.paint(); emoji(cr, '🏏', 540, 760, 160, 1, rot=-0.3 + 0.2 * math.sin(t * 5))
    trophies(cr, t, (1983, 2011), at('r6a', 'Two') - 0.1); label(cr, 'INDIA: 2 WORLD CUPS', 540, 620, 80, CA_C); ptext(cr, "MEN'S 50-OVER", 540, 1230, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_crickau(cr, t, b, t0, t1):
    set_australia(cr, t); cr.set_source_rgba(0.1, 0.04, 0.02, 0.35); cr.paint()
    trophies(cr, t, (1987, 1999, 2003, 2007, 2015, 2023), at('r6b', 'six') - 0.2); label(cr, 'AUSTRALIA: 6 WORLD CUPS', 540, 620, 76, AU_C); ptext(cr, "MEN'S 50-OVER · THE MOST EVER", 540, 1230, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def stars(cr, t):
    cr.set_source_rgb(0.01, 0.01, 0.05); cr.paint(); rng = np.random.default_rng(2)
    for _ in range(160): x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.6); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.4 + 0.4 * math.sin(t * 2 + x)); cr.fill()
    cr.new_path(); cr.arc(540, 2400, 1100, 0, 2 * math.pi); g = cairo.LinearGradient(0, 1300, 0, 1900); g.add_color_stop_rgb(0, 0.2, 0.5, 0.9); g.add_color_stop_rgb(1, 0.05, 0.15, 0.4); cr.set_source(g); cr.fill()
def sc_canadarm(cr, t, b, t0, t1):
    stars(cr, t); k = ease_out(prog(t, t0, t0 + 1.0)); x0, y0 = 300, 1200
    j1 = (x0 + 260 * math.cos(-0.9 + 0.3 * k), y0 + 260 * math.sin(-0.9 + 0.3 * k)); j2 = (j1[0] + 240 * math.cos(-0.2 - 0.4 * k), j1[1] + 240 * math.sin(-0.2 - 0.4 * k))
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    for a, b_ in (((x0, y0), j1), (j1, j2)): cr.move_to(*a); cr.line_to(*b_); cr.set_source_rgb(0.92, 0.92, 0.95); cr.set_line_width(34); cr.stroke()
    for p in ((x0, y0), j1, j2): cr.new_path(); cr.arc(*p, 24, 0, 2 * math.pi); cr.set_source_rgb(0.85, 0.2, 0.2); cr.fill()
    emoji(cr, '🛰️', j2[0] + 80, j2[1] - 40, 130, 1); label(cr, 'CANADARM · 1981', 540, 620, 90, AU_C); ptext(cr, 'ROBOTIC ARM OF THE SPACE SHUTTLE', 540, 700, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_space(cr, t, b, t0, t1):
    stars(cr, t); label(cr, 'SPACE FIRSTS', 540, 620, 100, CA_C)
    for j, (em, yr, lab, word, n_) in enumerate((('🛰️', '1957', 'FIRST SATELLITE', 'satellite', 0), ('👨‍🚀', '1961', 'FIRST HUMAN IN SPACE', 'human', 0), ('🌙', '2023', 'FIRST NEAR MOON SOUTH POLE', 'landed', 0))):
        tj = at('r7b', word, n_) - 0.2
        if t < tj: continue
        y = 840 + j * 210; k = pop_k(t, tj); emoji(cr, em, 230, y, 130 * k, 1); ptext(cr, yr, 330, y - 10, 60, GOLD, k, anchor='l', sw=8); ptext(cr, lab, 330, y + 50, 32, WHITE, k, fam='Poppins ExtraBold', anchor='l', sw=6)
        ball(cr, 'India' if j == 2 else 'Russia', 960, y, 50 * k, 'happy', 0, 0)
def sc_life(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'LIFE EXPECTANCY (YEARS)', 540, 620, 60, WHITE); ptext(cr, 'BARS START AT 60', 540, 690, 28, WHITE, 0.7, fam='Poppins ExtraBold', sw=5)
    k = ease_out(prog(t, at('r8b', 'live') - 0.2, at('r8b', 'eighty') + 0.3)); k2 = ease_out(prog(t, at('r8b', 'ten') - 0.2, at('r8b', 'longer') + 0.2))
    for x, n, v, kk, col in ((160, 'Australia', 83.2, k, AU_C), (400, 'Canada', 81.7, k, AU_C), (680, 'Russia', 72.8, k2, CA_C), (920, 'India', 72.0, k2, CA_C)):
        pbar(cr, x, 1320, v - 60, 25, kk, col, n, f'{v:.1f}')
def heat(cr, k):
    g = cairo.RadialGradient(540, 960, 300, 540, 960, 1100); g.add_color_stop_rgba(0, 1, 0.5, 0.1, 0); g.add_color_stop_rgba(1, 1, 0.4, 0.1, 0.35 * clamp(k)); cr.set_source(g); cr.paint()
def sc_auheat(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 135.4, -27.5)), 0.2, 0.6, t0, t0 + 1.1, AU_LAND)
    x, y = kpt('AU', 135.45, -27.55, cx, cy, s); pin(cr, x, y, t, t0 + 0.9, (1, 0.4, 0.2)); endmap(cr)
    k = ease_out(prog(t, at('r9a', 'Fifty') - 0.2, at('r9a', 'seven') + 0.2)); thermo(cr, k, 50.7, -10, 55, col=(1, 0.25, 0.1))
    label(cr, 'OODNADATTA · 1960', 540, 620, 70, WHITE)
    if k > 0: label(cr, f'{50.7 * k:.1f}°C', 540, 1000, 140, (1, 0.45, 0.2), clamp(k * 3))
    heat(cr, k)
def sc_inheat(cr, t, b, t0, t1):
    set_india(cr, t); cr.set_source_rgba(0.15, 0.04, 0.0, 0.3); cr.paint()
    k = ease_out(prog(t, at('r9b', 'Fifty') - 0.2, at('r9b', 'degrees') + 0.3)); thermo(cr, k, 51.0, -10, 55, col=(1, 0.2, 0.05), mark=(50.7, 'AUS 50.7'))
    label(cr, 'PHALODI, RAJASTHAN · 2016', 540, 620, 64, WHITE)
    if k > 0: label(cr, f'{51.0 * k:.1f}°C', 500, 1000, 150, (1, 0.4, 0.15), clamp(k * 3))
    heat(cr, k * 1.4)
SCENE = {'sizeA': sc_sizeA, 'sizeB': sc_sizeB, 'popA': sc_popA, 'popB': sc_popB, 'arctic': sc_arctic, 'coast': sc_coast, 'snag': sc_snag, 'oymyakon': sc_oymyakon,
         'growth': sc_growth, 'percap': sc_percap, 'crickin': sc_crickin, 'crickau': sc_crickau, 'canadarm': sc_canadarm, 'space': sc_space, 'life': sc_life,
         'auheat': sc_auheat, 'inheat': sc_inheat}

# ---------- hook, close-ups, title ----------
def draw_hook(cr, t):
    """Cold open: Australia recruits Canada, then Russia and India answer the challenge."""
    if t >= bt('title')['start']: return False
    for key, name, shot, mood in (('h1', 'Australia', sh_close, 'happy'), ('h2', 'Canada', sh_low, 'neutral'), ('h3', 'Russia', sh_low, 'angry'), ('h4', 'India', sh_close, 'angry')):
        b = bt(key)
        if t < b['end'] or key == 'h4':
            sx, sy = shake(t, b['start'], 22 if key in ('h3', 'h4') else 0, 0.4); cr.save(); cr.translate(sx, sy); shot(cr, t, b, name, b['start'], b['end'], mood); cr.restore()
            if key == 'h1': emoji(cr, '🤝', 860, 830, 140 * pop_k(t, w('h1', 'Team') - 0.1) if t >= w('h1', 'Team') - 0.1 else 0, 1)
            f = 1 - prog(t, b['start'], b['start'] + 0.12)
            if key != 'h1' and f > 0: cr.set_source_rgba(1, 1, 1, 0.5 * f); cr.paint()
            if key != 'h1': streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.2)))
            return True
    return True
def close_up(cr, t, key): pass
def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.5))
    for n, x, xs in (('Canada', 150, -300), ('Australia', 370, -300), ('India', 710, 1380), ('Russia', 930, 1380)):
        ball(cr, n, lerp(xs, x, e), 1470 - abs(math.sin(t * 6 + x)) * 14, 125, 'angry', 0, -TEAM_SGN[n] * 0.8)
    cr.restore()
    slam(cr, TEAM_A, 540, 560, 150, AU_C, t, w('title', 'Two'))
    tv = w('title', 'versus')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, TEAM_U, 540, 960, 150, CA_C, t, w('title', 'two', 1) if False else w('title', 'versus') + 0.4)
    tg = w('title', 'tag')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE TAG TEAM WAR', 540, 1170, 96, WHITE, t, tg); cr.restore()
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
    for side, x, col, sc, lab in (('A', 250, AU_C, sn, TEAM_A), ('U', 830, CA_C, ss, TEAM_U)):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = f'ROUND {i}/8' if i else ('FINAL: 4 — 4' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📏', 2: '👥', 3: '🌊', 4: '🥶', 5: '💵', 6: '🏏', 7: '🚀', 8: '❤️', 9: '🔥'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((AU_C, CA_C)):
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
    col = AU_C if win == 'A' else CA_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = (TEAM_A if win == 'A' else TEAM_U) + ' WIN'
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
        sx, sy = shake(t, e1['l0'], 20, 0.4); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540 + sx, 1100 + sy); set_australia(cr, t); ball(cr, 'Australia', 540, 1290, 290, 'shock', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Australia', 540, 1640, AU_C)
        ptext(cr, '4 — 4', 540, 820, 130, WHITE, pop_k(t, e1['start'] + 0.1), sw=14); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540, 1100); set_india(cr, t)
        ball(cr, 'India', 540, 1260 - h * 50, 300, 'happy', 0.05 * h, 0); ball(cr, 'Russia', 880, 1380, 140, 'happy', 0, -0.5); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'India', 540, 1640, CA_C); emoji(cr, '👉', 200, 900, 140 * pop_k(t, e2['l0'] + 0.4), 1)
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.06), 0.02, 540, 1000); arena(cr, t)
    for n, x in (('Canada', 150), ('Australia', 370), ('India', 710), ('Russia', 930)): ball(cr, n, x, 1290 - abs(math.sin(t * 5 + x)) * 10, 120, 'angry', 0, -TEAM_SGN[n] * 0.8)
    emoji(cr, '⚡', 540, 1280, 140, 1, rot=0.2 * math.sin(t * 10)); cr.restore()
    sx, sy = shake(t, c['start'], 16, 0.4); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A TIE!", 540, 470, 140, GOLD, t, c['start']); cr.restore()
    ptext(cr, TEAM_A, 190, 590, 52, AU_C, 1, sw=8); ptext(cr, '4 — 4', 540, 600, 84, WHITE, 1, sw=10); ptext(cr, TEAM_U, 890, 590, 52, CA_C, 1, sw=8)
    tp = w('cta', 'pick') - 0.1
    if t >= tp:
        kk = pop_k(t, tp); cr.save(); cr.translate(540, 730); cr.scale(kk, kk); ptext(cr, 'YOU PICK THE TIEBREAKER', 0, 0, 66, WHITE, 1, sw=9); cr.restore()
        for j, (em, lab) in enumerate((('🔥', 'HEAT?'), ('⚽', 'FOOTBALL?'), ('🍛', 'FOOD?'))):
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
    boom(0.0, 0.8); pop(w('h1', 'Team'), 0.12, 900)
    for k in ('h2', 'h3', 'h4', 'title'): whoosh(bt(k)['start'] - 0.3, 0.3, 0.35)
    boom(bt('h3')['start'], 1.0); rumble(bt('h3')['start'], 1.0, 0.2); boom(bt('h4')['start'], 0.9)
    for wd in ('Two', 'versus', 'tag'): boom(w('title', wd), 0.7)
    horn(w('title', 'tag'), 0.09)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_tag'))
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
