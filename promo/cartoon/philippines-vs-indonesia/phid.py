# Countryballs: Philippines vs Indonesia, the Island War (Australia drops in at the end).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (islands, volcanoes, reefs, Christmas in September...).
# Usage: python3 phid.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

PH_C, ID_C, AU_C = hexc('#3D7BFF')[:3], hexc('#F0435A')[:3], hexc('#FFC233')[:3]
A_C, U_C = PH_C, ID_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Philippines': ('fil-PH-AngeloNeural', '+4%'), 'Indonesia': ('id-ID-ArdiNeural', '+4%'), 'Australia': ('en-AU-WilliamNeural', '+6%')}
LINES = [
    ('h1', 'Philippines', "Indonesia! You copied my islands!"),
    ('h2', 'Indonesia', "Copied? I have seventeen thousand. You have seven!"),
    ('h3', None, "Together, they have about twenty-five thousand islands. But only one can win."),
    ('title', None, "Eight rounds. One winner. This is the island war."),
    ('c1', None, "Round one: islands."),
    ('r1a', 'Philippines', "Seven thousand six hundred and forty-one islands!"),
    ('r1b', 'Indonesia', "Over seventeen thousand. More than double!"),
    ('c2', None, "Round two: basketball."),
    ('r2a', 'Indonesia', "We co-hosted the Basketball World Cup!"),
    ('r2b', 'Philippines', "So did we. And thirty-eight thousand fans packed one game. A World Cup record!"),
    ('c3', None, "Round three: people."),
    ('r3a', 'Philippines', "One hundred and twelve million Filipinos!"),
    ('r3b', 'Indonesia', "Two hundred and eighty-four million Indonesians. Fourth biggest on Earth!"),
    ('c4', None, "Round four: eagles."),
    ('r4a', 'Indonesia', "My national bird is the Javan hawk-eagle!"),
    ('r4b', 'Philippines', "Mine is the Philippine eagle. One of the biggest eagles on Earth!"),
    ('c5', None, "Round five: volcanoes."),
    ('r5a', 'Philippines', "I have twenty-four active volcanoes!"),
    ('r5b', 'Indonesia', "I have one hundred and twenty-seven. The most of any country!"),
    ('c6', None, "Round six: pearls."),
    ('r6a', 'Indonesia', "I'm famous for my South Sea pearls!"),
    ('r6b', 'Philippines', "I found the biggest pearl ever. Thirty-four kilograms!"),
    ('c7', None, "Round seven: weird animals."),
    ('r7a', 'Philippines', "I have the tarsier. Each eye is as big as its brain!"),
    ('r7b', 'Indonesia', "Cute. I have real dragons. Komodo dragons, the biggest lizard on Earth!"),
    ('c8', None, "Final round: social media."),
    ('r8a', 'Indonesia', "Indonesians love social media!"),
    ('r8b', 'Philippines', "Filipinos spend about three and a half hours a day on it. Top five in the world!"),
    ('e1', 'Philippines', "Four all?!"),
    ('e2', 'Indonesia', "Then who wins?!"),
    ('e3', 'Australia', "Oi, you two! I'm neighbours with both of ya, so I'm not picking sides. Let the fans settle it!"),
    ('cta', None, "It's a tie! You pick the tiebreaker. Comment it below, and subscribe to see who wins!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('ISLANDS', 'U', ('r1b', 'double')), 2: ('BASKETBALL', 'A', ('r2b', 'record')), 3: ('PEOPLE', 'U', ('r3b', 'Earth')), 4: ('EAGLES', 'A', ('r4b', 'Earth')),
      5: ('VOLCANOES', 'U', ('r5b', 'country')), 6: ('PEARLS', 'A', ('r6b', 'kilograms')), 7: ('WEIRD ANIMALS', 'U', ('r7b', 'Earth')), 8: ('SOCIAL MEDIA', 'A', ('r8b', 'world'))}
NR = 8
SHOTS = {
    'r1a': [(None, 'close'), ('Seven', 'map:phislands')], 'r1b': [(None, 'low'), ('seventeen', 'map:idislands')],
    'r2a': [(None, 'two'), ('Basketball', 'map:fiba')], 'r2b': [(None, 'ots'), ('thirty', 'map:crowd')],
    'r3a': [(None, 'close'), ('One', 'map:phpop')], 'r3b': [(None, 'low'), ('Two', 'map:idpop')],
    'r4a': [(None, 'two'), ('Javan', 'map:javan')], 'r4b': [(None, 'ots'), ('Philippine', 'map:pheagle')],
    'r5a': [(None, 'close'), ('twenty', 'map:phvolc')], 'r5b': [(None, 'low'), ('one', 'map:idvolc')],
    'r6a': [(None, 'two'), ('South', 'map:southsea')], 'r6b': [(None, 'ots'), ('biggest', 'map:bigpearl')],
    'r7a': [(None, 'close'), ('tarsier', 'map:tarsier')], 'r7b': [(None, 'low'), ('Komodo', 'map:komodo')],
    'r8a': [(None, 'two'), ('social', 'map:idsocial')], 'r8b': [(None, 'ots'), ('three', 'map:social')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {'Komodo': 'Ko-mo-do'}}
C.HOT = ('philippines', 'indonesia', 'islands', 'copied', 'seven', 'seventeen', 'war', 'tie', 'tiebreaker', 'comment', 'subscribe', 'winner', 'oi', 'fans')
C.TAIL_OVERRIDE = {'h1': 0.12, 'h2': 0.2, 'h3': 0.5, 'title': 0.6, 'e1': 0.2, 'e2': 0.3, 'e3': 0.5, 'cta': 3.6, **{f'c{i}': 0.15 for i in range(1, 9)},
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
SEA = ['Malaysia', 'Philippines', 'Indonesia', 'Papua New Guinea', 'Australia', 'Timor-Leste', 'Brunei', 'Singapore', 'Thailand', 'Vietnam', 'Cambodia', 'Laos', 'Myanmar', 'Taiwan', 'China']
class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        R = lambda n: [r for r in rings(cf[n]['geometry']) if len(r) > 3 and 88 < r[:, 0].mean() < 160 and -30 < r[:, 1].mean() < 30]
        self.ref = {'PH': (122.0, 12.0), 'ID': (118.0, -2.0)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n in (('PH', 'Philippines'), ('ID', 'Indonesia')):
            rs = R(n); pr = local(rs, *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in SEA if nn != n and nn in cf for r in local(R(nn), *self.ref[k])]
        self.ph_in_id = [r - self.off['ID'] for r in local(R('Philippines'), *self.ref['ID'])]
        print('areas M km2: philippines', round(area(self.c['PH']) / 1e6, 3), 'indonesia', round(area(self.c['ID']) / 1e6, 3))
        for nm, f in (('Philippines', 'ph'), ('Indonesia', 'id'), ('Australia', 'au'), ('Japan', 'jp')): B.FL[nm] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', f + '.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'Philippines' else 'U'
def col_of(name): return {'Philippines': PH_C, 'Indonesia': ID_C}.get(name, AU_C)
def rival_of(name): return 'Indonesia' if name == 'Philippines' else 'Philippines'
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
def set_indonesia(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.35, 0.22, 0.45); g.add_color_stop_rgb(0.45, 0.98, 0.55, 0.38); g.add_color_stop_rgb(0.62, 1, 0.8, 0.55); g.add_color_stop_rgb(1, 0.2, 0.3, 0.18); cr.set_source(g); cr.paint()
    cr.new_path(); cr.arc(540, 820, 140, 0, 2 * math.pi); cr.set_source_rgba(1, 0.9, 0.6, 0.9); cr.fill()
    cr.new_path(); cr.move_to(150, 1100); cr.line_to(430, 700); cr.line_to(520, 690); cr.line_to(820, 1100); cr.close_path(); cr.set_source_rgb(0.35, 0.3, 0.4); cr.fill()  # volcano
    for j in range(5): ph = ((t * 0.3 + j * 0.2) % 1); cr.new_path(); cr.arc(475 + 30 * math.sin(j + t), 670 - ph * 260, 30 + 40 * ph, 0, 2 * math.pi); cr.set_source_rgba(0.85, 0.85, 0.9, 0.5 * (1 - ph)); cr.fill()
    for j in range(7):  # rice terraces
        y = 1080 + j * 50; cr.new_path(); cr.move_to(-100, y); cr.curve_to(300, y - 40 + 8 * math.sin(j), 700, y + 30, 1200, y - 10); cr.line_to(1200, y + 50); cr.curve_to(700, y + 80, 300, y + 10, -100, y + 50); cr.close_path()
        cr.set_source_rgb(0.25 + 0.05 * (j % 2), 0.55 + 0.04 * (j % 3), 0.25); cr.fill()
    for x, sgn in ((300, 1), (780, -1)):  # candi bentar split gate
        cr.new_path(); cr.move_to(x - 110 * sgn, 1420); cr.line_to(x - 110 * sgn, 1100); cr.line_to(x - 80 * sgn, 1040); cr.line_to(x - 60 * sgn, 980); cr.line_to(x - 40 * sgn, 900); cr.line_to(x - 20 * sgn, 820); cr.line_to(x, 820); cr.line_to(x, 1420); cr.close_path()
        cr.set_source_rgb(0.32, 0.22, 0.2); cr.fill()
        for yy in (1000, 1120, 1240): cr.rectangle(min(x, x - 100 * sgn), yy, 100, 10); cr.set_source_rgba(0.95, 0.75, 0.5, 0.5); cr.fill()
    cr.rectangle(-200, 1410, 1500, 700); cr.set_source_rgb(0.45, 0.36, 0.3); cr.fill()
    for j in range(10): cr.rectangle(j * 120 - 30, 1450 + (j % 3) * 70, 90, 24); cr.set_source_rgba(0.3, 0.24, 0.2, 0.6); cr.fill()
def set_of(name, cr, t): (set_philippines if name == 'Philippines' else set_indonesia)(cr, t)

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
    for n, x in (('Philippines', 290), ('Indonesia', 790)):
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
_DOTS = {}
def dots(cr, k_, n, cx, cy, s, lon0, lon1, lat0, lat1, col, seed):
    key = (k_, lon0, lon1, lat0, lat1, seed)
    if key not in _DOTS:
        rng = np.random.default_rng(seed); pts = []; tries = 0
        while len(pts) < 1600 and tries < 12000:
            tries += 1; lon, lat = rng.uniform(lon0, lon1), rng.uniform(lat0, lat1); p = G.p(k_, lon, lat)
            if inside(p, G.c[k_]): pts.append(p)
        _DOTS[key] = pts
    for p in _DOTS[key][:n]: x, y = cx + p[0] * s, cy - p[1] * s; cr.new_path(); cr.arc(x, y, 3.5, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.9); cr.fill()
PH_LAND, ID_LAND = (0.82, 0.86, 0.95), (0.95, 0.84, 0.8)
def islands(cr, t, rs, cx, cy, s, col, k):
    for j, r in enumerate(sorted(rs, key=len)[:int(len(rs) * k)]):
        ph = (t * 1.5 + j * 0.13) % 1; km_shape(cr, [r], cx, cy, s, col, 0.6 * (1 - ph), lw=3, edge=col, glow=True)
def sparkle(cr, t, k_, n, cx, cy, s, rs, seed, col=(1, 0.92, 0.4)):
    rng = np.random.default_rng(seed); big = max(rs, key=len)
    for j in range(n):
        r = rs[j % len(rs)] if j % 3 else big; p = r[rng.integers(len(r))] + rng.normal(0, 25, 2); ph = (t * 1.2 + j * 0.11) % 1
        cr.new_path(); cr.arc(cx + p[0] * s, cy - p[1] * s, 4 + 3 * (1 - ph), 0, 2 * math.pi); cr.set_source_rgba(*col, 0.95); cr.fill()
def sc_phislands(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'PH', (0, 0), (0, 0), 0.48, 0.5, t0, t1 + 1.5, PH_LAND); k = ease_out(prog(t, t0, at('r1a', 'forty') + 0.3))
    islands(cr, t, G.c['PH'], cx, cy, s, GOLD[:3], k); sparkle(cr, t, 'PH', int(160 * k), cx, cy, s, G.c['PH'], 3); endmap(cr)
    label(cr, f'{int(7641 * k):,} ISLANDS', 540, 620, 104, PH_C); ptext(cr, 'NAMRIA OFFICIAL COUNT · 2016', 540, 700, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
def sc_idislands(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'ID', (0, 0), (0, 0), 0.2, 0.21, t0, t1 + 1.5, ID_LAND); k = ease_out(prog(t, t0, at('r1b', 'thousand') + 0.3))
    islands(cr, t, G.c['ID'], cx, cy, s, GOLD[:3], k); sparkle(cr, t, 'ID', int(360 * k), cx, cy, s, G.c['ID'], 5); endmap(cr)
    label(cr, f'{int(17000 * k):,}+ ISLANDS', 540, 620, 104, ID_C); ptext(cr, '17,380 NAMED ISLANDS (2023)', 540, 700, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
    td = at('r1b', 'double') - 0.1
    if t >= td: chip(cr, 'MORE THAN DOUBLE', 540, 800, 52, GOLD, INK, pop_k(t, td), 1)
def court(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.05, 0.04, 0.12); g.add_color_stop_rgb(1, 0.18, 0.1, 0.06); cr.set_source(g); cr.paint()
    cr.save(); cr.translate(540, 1500); cr.scale(1, 0.35); rrect(cr, -560, -500, 1120, 1000, 30); cr.restore(); cr.set_source_rgb(0.78, 0.52, 0.28); cr.fill()
    cr.save(); cr.translate(540, 1500); cr.scale(1, 0.35); cr.new_path(); cr.arc(0, 0, 160, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
def sc_fiba(cr, t, b, t0, t1):
    court(cr, t); label(cr, 'BASKETBALL WORLD CUP 2023', 540, 600, 70, WHITE); ptext(cr, 'CO-HOSTS', 540, 690, 44, GOLD, 1, fam='Poppins ExtraBold', sw=6)
    for j, nm in enumerate(('Philippines', 'Japan', 'Indonesia')):
        tj = t0 + 0.2 + j * 0.2
        if t >= tj: k = pop_k(t, tj); x = 220 + j * 320; ball(cr, nm, x, 1000 - abs(math.sin(t * 4 + j)) * 14, 110 * k, 'happy', 0, 0); ptext(cr, nm.upper(), x, 1170, 36, WHITE, k, fam='Poppins ExtraBold', sw=6)
    emoji(cr, '🏀', 540, 1380 - abs(math.sin(t * 5)) * 120, 130, 1)
def sc_crowd(cr, t, b, t0, t1):
    court(cr, t); rng = np.random.default_rng(9); k = ease_out(prog(t, t0, at('r2b', 'fans') + 0.3))
    for j in range(int(900 * k)):
        x = rng.uniform(-20, 1100); y = rng.uniform(780, 1330); cr.new_path(); cr.arc(x, y + 4 * math.sin(t * 8 + j), 7, 0, 2 * math.pi); cr.set_source_rgba(*((PH_C, (1, 1, 1), (1, 0.85, 0.3), (0.95, 0.3, 0.35))[j % 4]), 0.8); cr.fill()
    label(cr, f'{int(38115 * k):,} FANS', 540, 600, 110, PH_C); ptext(cr, 'PHILIPPINE ARENA · AUG 25, 2023', 540, 690, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tr = at('r2b', 'record') - 0.1
    if t >= tr: chip(cr, 'FIBA WORLD CUP RECORD CROWD', 540, 1450, 48, GOLD, INK, pop_k(t, tr), 1)
def sc_phpop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'PH', (0, 0), (0, 0), 0.48, 0.44, t0, t1 + 1, PH_LAND); k = ease_out(prog(t, t0, at('r3a', 'Filipinos') + 0.3))
    dots(cr, 'PH', int(700 * k), cx, cy, s, 116, 127, 4.5, 21, (1, 0.85, 0.3), 9); endmap(cr); label(cr, f'{112.7 * k:.1f} MILLION', 540, 620, 100, PH_C)
def sc_idpop(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'ID', (0, 0), (0, 0), 0.2, 0.21, t0, t1 + 1, ID_LAND); k = ease_out(prog(t, t0, at('r3b', 'Indonesians') + 0.3))
    dots(cr, 'ID', int(1100 * k), cx, cy, s, 105, 115, -8.8, -5.8, (1, 0.85, 0.3), 3); dots(cr, 'ID', int(500 * k), cx, cy, s, 95, 141, -11, 6, (1, 0.85, 0.3), 4)
    x, y = kpt('ID', 106.85, -6.2, cx, cy, s); pin(cr, x, y, t, t0 + 0.6, WHITE); endmap(cr)
    if t >= t0 + 0.6: ptext(cr, 'JAKARTA', x, y + 70, 34, WHITE, pop_k(t, t0 + 0.6), fam='Poppins ExtraBold', sw=6)
    label(cr, f'{284 * k:.0f} MILLION', 540, 620, 104, ID_C)
    tf = at('r3b', 'Fourth') - 0.1
    if t >= tf: chip(cr, '#4 ON EARTH · 2.5× PHILIPPINES', 540, 730, 46, GOLD, INK, pop_k(t, tf), 1)
def eagle_bar(cr, x, y, L, k, col, lab):
    rrect(cr, x - L * k / 2, y, L * k, 26, 13); cr.set_source_rgb(*col); cr.fill(); ptext(cr, lab, x, y + 80, 40, WHITE, clamp(k * 2), fam='Poppins ExtraBold', sw=6)
def sky(cr):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.2, 0.45, 0.8); g.add_color_stop_rgb(0.7, 0.7, 0.85, 0.95); g.add_color_stop_rgb(1, 0.25, 0.45, 0.3); cr.set_source(g); cr.paint()
    for j in range(5): cr.new_path(); [cr.arc((j * 260 + 60) % 1150 + dx, 1500 + (j % 2) * 60 + dy, r, 0, 6.28) for dx, dy, r in ((0, 0, 120), (110, -40, 140), (230, 10, 110))]; cr.set_source_rgb(0.15, 0.4, 0.22); cr.fill()
def sc_javan(cr, t, b, t0, t1):
    sky(cr); k = pop_k(t, t0 + 0.1, 0.4); emoji(cr, '🦅', 540, 1050 + 20 * math.sin(t * 2), 260 * k, 1, rot=0.05 * math.sin(t * 3))
    label(cr, 'JAVAN HAWK-EAGLE', 540, 600, 90, ID_C); eagle_bar(cr, 540, 1250, 300, ease_out(prog(t, t0 + 0.3, t0 + 1)), ID_C, '≈ 60 CM LONG')
def sc_pheagle(cr, t, b, t0, t1):
    sky(cr); k = pop_k(t, t0 + 0.1, 0.4); emoji(cr, '🦅', 540, 990 + 20 * math.sin(t * 2), 420 * k, 1, rot=0.05 * math.sin(t * 3))
    label(cr, 'PHILIPPINE EAGLE', 540, 600, 96, PH_C); ptext(cr, 'NATIONAL BIRD · CRITICALLY ENDANGERED', 540, 690, 32, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    kb = ease_out(prog(t, t0 + 0.4, t0 + 1.2)); eagle_bar(cr, 540, 1240, 300, 1, ID_C, ''); eagle_bar(cr, 540, 1290, 500, kb, PH_C, 'UP TO ~1 M LONG · ~2 M WINGS')
    tb = at('r4b', 'biggest') - 0.1
    if t >= tb: chip(cr, 'ONE OF THE BIGGEST EAGLES ON EARTH', 540, 790, 42, GOLD, INK, pop_k(t, tb), 1)
VOLC = [('MAYON', 13.257, 123.685), ('TAAL', 14.002, 120.993), ('PINATUBO', 15.13, 120.35), ('', 10.412, 123.132), ('', 12.77, 124.05), ('', 9.203, 124.673), ('', 18.83, 121.86), ('', 7.0, 125.27), ('', 20.33, 121.95), ('', 11.52, 124.53)]
def sc_phvolc(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'PH', (0, 0), (0, 0), 0.48, 0.5, t0, t1 + 2, PH_LAND)
    for j, (nm, lat, lon) in enumerate(VOLC):
        tj = t0 + 0.2 + j * 0.1
        if t >= tj:
            x, y = kpt('PH', lon, lat, cx, cy, s); emoji(cr, '🌋', x, y - 20, (100 if nm else 60) * pop_k(t, tj), 1)
            if nm: ptext(cr, nm, x + (120 if nm != 'PINATUBO' else -150), y + 10, 34, WHITE, pop_k(t, tj), sw=6)
    endmap(cr); k = ease_out(prog(t, t0, at('r5a', 'active') + 0.3)); label(cr, f'{int(24 * k)} ACTIVE VOLCANOES', 540, 620, 76, (1, 0.5, 0.35))
IDV = [(95.5, 5.0), (97.0, 3.0), (98.4, 2.6), (100.3, -0.4), (101.3, -1.7), (102.3, -3.5), (103.6, -4.0), (105.4, -6.1), (106.7, -6.8), (107.7, -7.2), (108.4, -7.3), (109.9, -7.2), (110.4, -7.5),
       (110.9, -7.6), (112.3, -7.9), (112.9, -8.1), (113.6, -7.9), (114.2, -8.1), (115.5, -8.3), (116.5, -8.4), (118.0, -8.2), (119.4, -8.5), (121.7, -8.5), (123.5, -8.4), (125.7, -7.5),
       (127.4, 1.4), (127.9, 1.7), (125.4, 2.8), (124.8, 1.4), (129.9, -4.5), (128.5, 3.0), (126.6, -2.4), (127.3, 0.8)]
def sc_idvolc(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'ID', (0, 0), (0, -50), 0.2, 0.21, t0, t1 + 2, ID_LAND)
    for j, (lon, lat) in enumerate(IDV):
        tj = t0 + 0.2 + j * 0.05
        if t >= tj: x, y = kpt('ID', lon, lat, cx, cy, s); emoji(cr, '🌋', x, y - 14, 58 * pop_k(t, tj), 1)
    endmap(cr); k = ease_out(prog(t, t0, at('r5b', 'twenty') + 0.3)); label(cr, f'{int(127 * k)} ACTIVE VOLCANOES', 540, 620, 76, (1, 0.5, 0.35))
    tm = at('r5b', 'most') - 0.1
    if t >= tm: chip(cr, 'THE MOST OF ANY COUNTRY', 540, 730, 50, GOLD, INK, pop_k(t, tm), 1)
def pearl(cr, x, y, r, a=1.0):
    g = cairo.RadialGradient(x - r * 0.35, y - r * 0.4, r * 0.05, x, y, r); g.add_color_stop_rgba(0, 1, 1, 1, a); g.add_color_stop_rgba(0.6, 0.93, 0.9, 0.88, a); g.add_color_stop_rgba(1, 0.72, 0.7, 0.75, a)
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source(g); cr.fill()
def sea(cr):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.02, 0.15, 0.3); g.add_color_stop_rgb(1, 0.01, 0.05, 0.12); cr.set_source(g); cr.paint()
def sc_southsea(cr, t, b, t0, t1):
    sea(cr); label(cr, 'SOUTH SEA PEARLS', 540, 600, 96, ID_C); ptext(cr, "INDONESIA: WORLD'S TOP PRODUCER", 540, 690, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    for j in range(9):
        tj = t0 + 0.2 + j * 0.08
        if t >= tj: k = pop_k(t, tj); pearl(cr, 250 + (j % 3) * 290, 900 + (j // 3) * 200 + 8 * math.sin(t * 2 + j), 60 * k)
def sc_bigpearl(cr, t, b, t0, t1):
    sea(cr); k = ease_out(prog(t, t0, at('r6b', 'kilograms') + 0.2))
    cr.save(); cr.translate(540, 1080); cr.scale(1.3, 0.85); pearl(cr, 0, 0, 40 + 270 * k); cr.restore()
    pearl(cr, 920, 1440, 40); ptext(cr, 'NORMAL PEARL (BIG!)', 920, 1530, 26, WHITE, 1, fam='Poppins ExtraBold', sw=5)
    label(cr, f'{34 * k:.0f} KG PEARL', 540, 600, 110, PH_C); ptext(cr, 'PEARL OF PUERTO PRINCESA · PALAWAN', 540, 690, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tb = at('r6b', 'biggest') - 0.1
    if t >= tb: chip(cr, 'BIGGEST PEARL EVER FOUND · 67 CM', 540, 1520 - 160, 44, GOLD, INK, pop_k(t, tb), 1)
def sc_tarsier(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.04, 0.12, 0.06); g.add_color_stop_rgb(1, 0.1, 0.25, 0.1); cr.set_source(g); cr.paint()
    cr.move_to(-50, 1300); cr.curve_to(300, 1250, 700, 1350, 1150, 1280); cr.set_source_rgb(0.3, 0.2, 0.1); cr.set_line_width(40); cr.stroke()
    k = pop_k(t, t0 + 0.1, 0.4); cr.save(); cr.translate(540, 1100); cr.scale(k, k)
    cr.save(); cr.scale(1, 1.2); cr.new_path(); cr.arc(0, 120, 150, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(0.62, 0.45, 0.3); cr.fill()
    for sx in (-1, 1): cr.new_path(); cr.arc(sx * 150, -110, 55, 0, 2 * math.pi); cr.set_source_rgb(0.55, 0.38, 0.25); cr.fill()
    cr.new_path(); cr.arc(0, -40, 175, 0, 2 * math.pi); cr.set_source_rgb(0.68, 0.5, 0.34); cr.fill()
    blink = 0.15 if (t % 3) < 0.12 else 1
    for sx in (-1, 1):
        cr.save(); cr.translate(sx * 78, -50); cr.scale(1, blink); cr.new_path(); cr.arc(0, 0, 72, 0, 2 * math.pi); cr.set_source_rgb(0.95, 0.7, 0.2); cr.fill(); cr.new_path(); cr.arc(0, 0, 50, 0, 2 * math.pi); cr.set_source_rgb(0.05, 0.03, 0.02); cr.fill()
        cr.new_path(); cr.arc(-18, -20, 14, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill(); cr.restore()
    cr.new_path(); cr.arc(0, 45, 10, 0, 2 * math.pi); cr.set_source_rgb(0.3, 0.2, 0.15); cr.fill(); cr.restore()
    label(cr, 'PHILIPPINE TARSIER', 540, 600, 92, PH_C); ptext(cr, 'ONE OF THE SMALLEST PRIMATES · FITS IN YOUR HAND', 540, 690, 30, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    te = at('r7a', 'Each') - 0.1
    if t >= te: chip(cr, 'EACH EYE ≈ AS BIG AS ITS BRAIN', 540, 1500, 44, GOLD, INK, pop_k(t, te), 1)
def sc_komodo(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.95, 0.75, 0.5); g.add_color_stop_rgb(0.6, 0.85, 0.65, 0.4); g.add_color_stop_rgb(1, 0.5, 0.4, 0.25); cr.set_source(g); cr.paint()
    for j in range(4): cr.new_path(); cr.move_to(-100 + j * 330, 1150); cr.curve_to(60 + j * 330, 850, 200 + j * 330, 850, 360 + j * 330, 1150); cr.close_path(); cr.set_source_rgb(0.55, 0.55, 0.3); cr.fill()
    cr.rectangle(-100, 1140, 1300, 900); cr.set_source_rgb(0.75, 0.62, 0.42); cr.fill()
    k = ease_out(prog(t, t0, t0 + 0.6)); emoji(cr, '🦎', lerp(1300, 560, k), 1240 + 6 * math.sin(t * 6), 520, 1, rot=0.05 * math.sin(t * 4))
    label(cr, 'KOMODO DRAGON', 540, 600, 104, ID_C); ptext(cr, 'UP TO 3 M LONG · ~70 KG', 540, 690, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tb = at('r7b', 'biggest') - 0.1
    if t >= tb: chip(cr, 'BIGGEST LIZARD ON EARTH', 540, 800, 52, GOLD, INK, pop_k(t, tb), 1)
def phone(cr, t, t0, col):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.12, 0.05, 0.3); g.add_color_stop_rgb(1, 0.05, 0.15, 0.4); cr.set_source(g); cr.paint()
    rrect(cr, 340, 760, 400, 700, 50); cr.set_source_rgb(0.08, 0.08, 0.12); cr.fill(); rrect(cr, 360, 800, 360, 620, 30); cr.set_source_rgb(0.95, 0.96, 1); cr.fill()
    for j in range(4):
        y = 840 + j * 145; rrect(cr, 380, y, 320, 125, 16); cr.set_source_rgb(*((0.85, 0.9, 1) if j % 2 else (1, 0.92, 0.85))); cr.fill()
        cr.new_path(); cr.arc(420, y + 40, 24, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill(); rrect(cr, 460, y + 25, 200, 16, 8); cr.set_source_rgb(0.6, 0.6, 0.7); cr.fill(); rrect(cr, 460, y + 60, 150, 14, 7); cr.fill()
    for j in range(10):
        ph = ((t - t0) * 0.6 + j / 10) % 1; emoji(cr, '❤️' if j % 2 else '👍', 300 + (j * 97) % 480, lerp(1400, 700, ph), 60, 1 - ph)
def sc_idsocial(cr, t, b, t0, t1):
    phone(cr, t, t0, ID_C); label(cr, 'INDONESIA LOVES SOCIAL MEDIA', 540, 620, 56, ID_C)
def sc_social(cr, t, b, t0, t1):
    phone(cr, t, t0, PH_C); k = ease_out(prog(t, at('r8b', 'three') - 0.2, at('r8b', 'day') + 0.3)); label(cr, f'{3.5 * k:.1f} HOURS A DAY', 540, 620, 86, PH_C)
    tw0 = at('r8b', 'Top') - 0.1
    if t >= tw0: chip(cr, 'TOP 5 IN THE WORLD · DIGITAL 2025', 540, 700, 40, GOLD, INK, pop_k(t, tw0), 1)
SCENE = {'phislands': sc_phislands, 'idislands': sc_idislands, 'fiba': sc_fiba, 'crowd': sc_crowd, 'phpop': sc_phpop, 'idpop': sc_idpop, 'javan': sc_javan, 'pheagle': sc_pheagle,
         'phvolc': sc_phvolc, 'idvolc': sc_idvolc, 'southsea': sc_southsea, 'bigpearl': sc_bigpearl, 'tarsier': sc_tarsier, 'komodo': sc_komodo, 'idsocial': sc_idsocial, 'social': sc_social}

# ---------- hook, title ----------
def draw_hook(cr, t):
    """Cold open: island insults, then both archipelagos light up: about 25,000 islands between them."""
    if t >= bt('title')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        sh_close(cr, t, b1, 'Philippines', 0, b1['end'], 'angry'); tf = w('h1', 'copied') - 0.1
        if t >= tf: emoji(cr, '🏝️', 860, 820, 150 * pop_k(t, tf, 0.3), 1, rot=-0.1 + 0.05 * math.sin(t * 3))
        return True
    if t < b3['start']:
        sx, sy = shake(t, w('h2', 'seven', 1) - 0.05, 20, 0.4); cr.save(); cr.translate(sx, sy)
        sh_low(cr, t, b2, 'Indonesia', b2['start'], b2['end'], 'angry'); cr.restore()
        ts = w('h2', 'seventeen') - 0.1
        if t >= ts: ptext(cr, '17,000', 820, 840, 110, GOLD, pop_k(t, ts), sw=12)
        tv = w('h2', 'seven', 1) - 0.1
        if t >= tv: ptext(cr, 'vs 7,000?', 820, 960, 70, WHITE, pop_k(t, tv), sw=9)
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2)))
        return True
    cx, cy, s = mview(cr, t, 'ID', (0, 0), (0, 500), 0.24, 0.19, b3['start'], b3['start'] + 1.2, ID_LAND)
    km_shape(cr, G.ph_in_id, cx, cy, s, PH_LAND, 1, lw=1.6, edge=(0.03, 0.04, 0.1))
    k = ease_out(prog(t, w('h3', 'about') - 0.1, w('h3', 'islands') + 0.3))
    sparkle(cr, t, 'ID', int(380 * k), cx, cy, s, G.c['ID'], 5); sparkle(cr, t, 'ID', int(200 * k), cx, cy, s, G.ph_in_id, 7)
    for nm, lon, lat, col in (('PHILIPPINES', 122, 12.5, PH_C), ('INDONESIA', 112, -2.5, ID_C)):
        x, y = kpt('ID', lon, lat, cx, cy, s)
        if t >= b3['start'] + 0.4: chip(cr, nm, x, y, 38, col, INK, pop_k(t, b3['start'] + 0.4), 1)
    endmap(cr)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
    if t >= w('h3', 'about') - 0.1: sx, sy = shake(t, w('h3', 'islands'), 8, 0.15); cr.save(); cr.translate(sx, sy); ptext(cr, f'≈ {int(25000 * k):,} ISLANDS', 540, 330, 96, GOLD, 1, sw=12); cr.restore()
    to = w('h3', 'only') - 0.1
    if t >= to:
        cr.set_source_rgba(0, 0, 0.05, 0.45 * clamp((t - to) * 4)); cr.paint()
        sx, sy = shake(t, to, 18); cr.save(); cr.translate(sx, sy); slam(cr, 'ONLY ONE', 540, 860, 160, WHITE, t, to); slam(cr, 'CAN WIN', 540, 1030, 160, GOLD, t, w('h3', 'win') - 0.1); cr.restore()
    C.draw_captions(cr, t, 1700)
    f = 1 - prog(t, b3['start'], b3['start'] + 0.15)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b3['start'], b3['start'] + 0.2)))
    return True
def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.5))
    ball(cr, 'Philippines', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'Indonesia', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'PHILIPPINES', 540, 560, 150, PH_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 730); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'INDONESIA', 540, 960, 160, ID_C, t, w('title', 'winner'))
    tg = w('title', 'island')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE ISLAND WAR', 540, 1160, 104, WHITE, t, tg); cr.restore()
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
    for side, x, col, sc, lab in (('A', 250, PH_C, sn, 'PHILIPPINES'), ('U', 830, ID_C, ss, 'INDONESIA')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = f'ROUND {i}/8' if i else ('FINAL: 4 — 4' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '🏝️', 2: '🏀', 3: '👥', 4: '🦅', 5: '🌋', 6: '🦪', 7: '🦎', 8: '📱'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((PH_C, ID_C)):
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
    col = PH_C if win == 'A' else ID_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('PHILIPPINES' if win == 'A' else 'INDONESIA') + ' WINS'
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
    e1, e2, e3, c = bt('e1'), bt('e2'), bt('e3'), bt('cta')
    if t < e2['start']:
        sx, sy = shake(t, e1['l0'], 20, 0.4); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540 + sx, 1100 + sy); set_philippines(cr, t); ball(cr, 'Philippines', 540, 1290, 290, 'shock', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Philippines', 540, 1640, PH_C)
        ptext(cr, '4 — 4', 540, 820, 130, WHITE, pop_k(t, e1['start'] + 0.1), sw=14); return
    if t < e3['start']:
        sx, sy = shake(t, e2['l0'], 16, 0.4); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540 + sx, 1100 + sy); set_indonesia(cr, t)
        ball(cr, 'Indonesia', 540, 1270, 290, 'shock', 0, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Indonesia', 540, 1640, ID_C); return
    if t < c['start']:  # Australia drops in between them
        t0 = e3['start']; land = t0 + 0.45; h = hop_of(t, e3)
        cr.save(); cam(cr, push(t, t0, e3['end'], 1.05, 1.0), 0, 540, 1100); set_philippines(cr, t)
        cr.save(); cr.rectangle(540, 0, 540, H); cr.clip(); set_indonesia(cr, t); cr.restore()
        look = -0.3 if t > land else 0
        ball(cr, 'Philippines', 180, 1420, 150, 'shock' if t < land + 1.2 else 'happy', 0, 0.6); ball(cr, 'Indonesia', 900, 1420, 150, 'shock' if t < land + 1.2 else 'happy', 0, -0.6)
        if t < land: y = lerp(-300, 1200, ease_io(prog(t, t0, land))); sq = 0
        else: y = 1200 - h * 40; sq = 0.25 * math.exp(-(t - land) * 8) * math.cos((t - land) * 30)
        ball(cr, 'Australia', 540, y, 210, 'happy', sq + 0.04 * h, 0); cr.restore()
        if t >= land:
            sx, sy = shake(t, land, 22, 0.4); cr.save(); cr.translate(sx, sy)
            for j in range(10):
                a = math.pi + j / 9 * math.pi; r = 120 + 380 * ease_out(prog(t, land, land + 0.6)); f = 1 - prog(t, land, land + 0.8)
                if f > 0: cr.new_path(); cr.arc(540 + r * math.cos(a), 1400 + r * math.sin(a) * 0.3, 30 * f + 6, 0, 2 * math.pi); cr.set_source_rgba(0.95, 0.88, 0.7, f); cr.fill()
            cr.restore()
            emoji(cr, '🦘', 860, 980, 150 * pop_k(t, land + 0.2, 0.3), 1, rot=0.1 * math.sin(t * 4))
        if t >= land - 0.05: slam(cr, "G'DAY!", 540, 840, 120, AU_C, t, land - 0.05) if t < land + 1.0 else None
        bubble(cr, t, e3, 540, 520, 50); nametag(cr, 'Australia', 540, 1600, AU_C); return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.06), 0.02, 540, 1000); arena(cr, t)
    for n, x, lk in (('Philippines', 290, 0.8), ('Indonesia', 790, -0.8)): ball(cr, n, x, 1280 - abs(math.sin(t * 5 + x)) * 10, 170, 'angry', 0, lk)
    cr.restore(); ball(cr, 'Australia', 540, 1160 - abs(math.sin(t * 4)) * 8, 70, 'happy', 0, 0); ptext(cr, 'REF', 540, 1260, 30, AU_C, 1, fam='Poppins ExtraBold', sw=5)
    sx, sy = shake(t, c['start'], 16, 0.4); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A TIE!", 540, 470, 140, GOLD, t, c['start']); cr.restore()
    ptext(cr, 'PHILIPPINES', 210, 590, 46, PH_C, 1, sw=8); ptext(cr, '4 — 4', 540, 600, 84, WHITE, 1, sw=10); ptext(cr, 'INDONESIA', 870, 590, 48, ID_C, 1, sw=8)
    tp = w('cta', 'pick') - 0.1
    if t >= tp:
        kk = pop_k(t, tp); cr.save(); cr.translate(540, 730); cr.scale(kk, kk); ptext(cr, 'YOU PICK THE TIEBREAKER', 0, 0, 66, WHITE, 1, sw=9); cr.restore()
        for j, (em, lab) in enumerate((('🍜', 'FOOD?'), ('🏸', 'BADMINTON?'), ('🎤', 'KARAOKE?'))):
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
    boom(0.0, 1.0); rumble(0.0, 1.0, 0.25); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(w('h2', 'seven', 1) - 0.05, 0.8)
    whoosh(bt('h3')['start'] - 0.3, 0.3); t0_ = w('h3', 'about') - 0.1; t1_ = w('h3', 'islands') + 0.3
    for k_ in range(16): pop(t0_ + (k_ + 1) / 16 * (t1_ - t0_), 0.08, 600 + 40 * k_)
    boom(w('h3', 'only') - 0.1, 1.0); boom(w('h3', 'win') - 0.1, 0.8); whoosh(bt('title')['start'] - 0.35)
    for wd in ('Eight', 'winner', 'island'): boom(w('title', wd), 0.7)
    horn(w('title', 'island'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1); pop(tv + 0.55, 0.12, 500)
    for k, sp, _ in LINES:
        if sp and k[0] == 'r': whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
        if k in SHOTS:
            for s0, sh in shot_list(k)[1:]: whoosh(s0 - 0.2, 0.16, 0.22)
    whoosh(bt('e3')['start'] - 0.1, 0.4, 0.5); boom(bt('e3')['start'] + 0.45, 1.0); cheer(bt('e3')['start'] + 0.5, 0.1, 1.0); boom(bt('e1')['start'], 0.9); rumble(bt('e1')['start'], 1.0, 0.2); boom(bt('cta')['start'], 0.9); horn(bt('cta')['start'], 0.1)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_phid'))
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

