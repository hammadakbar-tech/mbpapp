# Countryballs: Canada vs Japan, the Geography War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (lakes, volcanoes, coastline, snow...).
# Usage: python3 cajp.py <data_dir> <out.mp4> [--preview t1,t2,...]
import json, math, os, ssl, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import edge_tts.communicate as _etc
if os.path.exists('/root/.ccr/ca-bundle.crt'): _etc._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
import china as C
import warballs as B
from warballs import ball
from big import local, bounds, area, km_shape
from popu import streaks, shake
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, hexc, SR

A_C, U_C = hexc('#FF4A3D')[:3], hexc('#4FA8FF')[:3]   # Canada maple red, Japan "samurai blue"
CA_C, JP_C = A_C, U_C
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Canada': ('en-CA-LiamNeural', '+4%'), 'Japan': ('ja-JP-KeitaNeural', '+0%')}
LINES = [
    ('h1', None, "Canada, or Japan: who would win?"),
    ('h2', None, "One is twenty-six times bigger. The other has three times the people."),
    ('h3c', 'Canada', "Sorry, but this will be easy, eh!"), ('h3j', 'Japan', "Konnichiwa. We will see."),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: size."),
    ('r1a', 'Japan', "I may be small, but I'm three thousand kilometres long!"),
    ('r1b', 'Canada', "Cute. I'm twenty-six times bigger than you, eh!"),
    ('c2', None, "Round two: people."),
    ('r2a', 'Canada', "Almost forty-two million friendly Canadians!"),
    ('r2b', 'Japan', "I have over one hundred and twenty-three million. The Tokyo area alone has almost as many people as all of Canada!"),
    ('c3', None, "Round three: lakes."),
    ('r3a', 'Japan', "We have Lake Biwa. It's four million years old!"),
    ('r3b', 'Canada', "Cute. I have over eight hundred and fifty thousand lakes. That's sixty-two percent of the world's lakes!"),
    ('c4', None, "Round four: volcanoes."),
    ('r4a', 'Canada', "I have the Rockies. Big, calm mountains."),
    ('r4b', 'Japan', "Calm is boring. I have one hundred and eleven active volcanoes. Nearly a tenth of the world's!"),
    ('c5', None, "Round five: coastline."),
    ('r5a', 'Japan', "I'm made of over fourteen thousand islands!"),
    ('r5b', 'Canada', "And I have the longest coastline on Earth. Two hundred and forty-three thousand kilometres. Six times around the equator!"),
    ('c6', None, "Round six: cold."),
    ('r6a', 'Japan', "We have snow monkeys, relaxing in hot springs!"),
    ('r6b', 'Canada', "Cute. Snag, Yukon: minus sixty-three degrees. Your monkeys would freeze!"),
    ('c7', None, "Round seven: living long."),
    ('r7a', 'Canada', "Canadians live to almost eighty-two!"),
    ('r7b', 'Japan', "Japanese women have lived the longest on Earth for forty-one years in a row. And over one hundred thousand of us are older than one hundred!"),
    ('c8', None, "Round eight: the GDP war."),
    ('r8a', 'Canada', "My economy is worth about two point four trillion dollars!"),
    ('r8b', 'Japan', "Mine is four point four trillion. Almost double!"),
    ('c9', None, "Four all. Tiebreaker: snow. Surely, Canada wins this one."),
    ('r9a', 'Canada', "Snow? I'm Canada! I own snow!"),
    ('r9b', 'Japan', "Aomori gets over six metres of snow every year. Your snowiest big city? About three and a half."),
    ('e1', 'Canada', "Sorry..."),
    ('e2', 'Japan', "Arigatou gozaimasu."),
    ('cta', None, "Canada, or Japan? Comment your side, and follow for the next battle.")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SIZE', 'A', ('r1b', 'bigger')), 2: ('PEOPLE', 'U', ('r2b', 'Canada')), 3: ('LAKES', 'A', ('r3b', 'world')), 4: ('VOLCANOES', 'U', ('r4b', 'tenth')),
      5: ('COASTLINE', 'A', ('r5b', 'equator')), 6: ('COLD', 'A', ('r6b', 'freeze')), 7: ('LIVING LONG', 'U', ('r7b', 'older')), 8: ('THE GDP WAR', 'U', ('r8b', 'double')),
      9: ('SNOW', 'U', ('r9b', 'half'))}
NR = 9
# shots per ball line: (cut word or None for the start, shot). 'map:x' = full-screen visual x with the speaker as picture-in-picture.
# A reaction shot of the loser is added automatically half a second after each round's deciding word.
SHOTS = {
    'r1a': [(None, 'two'), ('three', 'map:jlength')], 'r1b': [(None, 'close'), ('twenty', 'map:size')],
    'r2a': [(None, 'low'), ('friendly', 'map:caflag')], 'r2b': [(None, 'ots'), ('one', 'map:tokyo')],
    'r3a': [(None, 'close'), ('Biwa', 'map:biwa')], 'r3b': [(None, 'two'), ('eight', 'map:lakes')],
    'r4a': [(None, 'close'), ('Rockies', 'map:rockies')], 'r4b': [(None, 'low'), ('one', 'map:volcano')],
    'r5a': [(None, 'two'), ('fourteen', 'map:islands')], 'r5b': [(None, 'ots'), ('longest', 'map:coast')],
    'r6a': [(None, 'close'), ('snow', 'map:onsen')], 'r6b': [(None, 'low'), ('Snag', 'map:snag')],
    'r7a': [(None, 'two'), ('eighty', 'close')], 'r7b': [(None, 'ots'), ('women', 'map:age')],
    'r8a': [(None, 'close'), ('two', 'map:gdpca')], 'r8b': [(None, 'two'), ('four', 'map:gdpjp')],
    'r9a': [(None, 'low'), ('own', 'close')], 'r9b': [(None, 'map:aomori')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2')
C.SAY = {None: {}}
C.HOT = ('canada', 'japan', 'win', 'bigger', 'people', 'war', 'tiebreaker', 'snow', 'comment', 'geography', 'winner', 'lakes', 'volcanoes')
C.TAIL_OVERRIDE = {'h1': 0.25, 'h2': 0.4, 'title': 0.6, 'c9': 0.3, 'e2': 0.6, 'cta': 2.4, **{f'c{i}': 0.15 for i in range(1, 9)},
                   **{k: 0.3 for k, s, _ in LINES if s}, **{RD[i][2][0]: 1.1 for i in RD}, 'h3c': 0.2, 'h3j': 0.4}
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
        self.ref = {'CA': (-96.0, 60.0), 'JP': (137.0, 37.0)}
        self.c, self.nb, self.off = {}, {}, {}
        for k, n, nbs in (('CA', 'Canada', ['United States of America', 'Greenland']), ('JP', 'Japan', ['Russia', 'China', 'North Korea', 'South Korea', 'Taiwan'])):
            pr = local(R(n), *self.ref[k]); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]; self.nb[k] = [r - off for nn in nbs for r in local(R(nn), *self.ref[k])]
        self.coast = sorted(self.c['CA'], key=lambda r: -len(r))
        lakes = []
        for f in json.load(open(os.path.join(d, 'ne_50m_lakes.geojson')))['features']:
            rs = [r for r in rings(f['geometry']) if len(r) > 3]; p = np.concatenate(rs); cx, cy = p[:, 0].mean(), p[:, 1].mean()
            if f['properties'].get('name') == 'Biwa Ko': self.biwa = [r - self.off['JP'] for r in local(rs, *self.ref['JP'])]
            if -141 < cx < -52 and 41.5 < cy < 83:
                pr = [r - self.off['CA'] for r in local(rs, *self.ref['CA'])]; pc = np.concatenate(pr).mean(axis=0)
                if inside(pc, self.c['CA']) or f['properties'].get('name') in ('Lake Superior', 'Lake Huron', 'Lake Erie', 'Lake Ontario'): lakes.append((cx, pr))
        self.lakes = [pr for _, pr in sorted(lakes, key=lambda x: x[0])]
        self.jp_true = [r - np.concatenate(self.c['JP']).mean(axis=0) for r in self.c['JP']]
        print('areas M km2: canada', round(area(self.c['CA']) / 1e6, 2), 'japan', round(area(self.c['JP']) / 1e6, 3), 'ratio', round(area(self.c['CA']) / area(self.c['JP']), 1), 'lakes', len(self.lakes))
        for n, c in (('Canada', 'ca'), ('Japan', 'jp')): B.FL[n] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', c + '.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'Canada' else 'U'
def col_of(name): return CA_C if name == 'Canada' else JP_C
def rival_of(name): return 'Japan' if name == 'Canada' else 'Canada'
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
def set_of(name, cr, t): (set_canada if name == 'Canada' else set_japan)(cr, t)

# ---------- shots ----------
def sh_close(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Canada' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.07 * sgn * (1 if sum(map(ord, b['key'])) % 2 else -1), 540, 1100); set_of(name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, 'happy', 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Canada' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, 'happy', 0.04 * h, -sgn * 0.2); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_ots(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Canada' else 1; h = hop_of(t, b); rv = rival_of(name)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.06), 0.02 * sgn, 540 + lerp(0, -sgn * 40, prog(t, t0, t1)), 1000); set_of(name, cr, t)
    ball(cr, name, 540 + sgn * 150, 1080 - h * 36, 210, 'happy', 0.05 * h, -sgn * 0.6)
    ball(cr, rv, 540 - sgn * 470, 1700, 560, 'angry', 0, sgn * 0.9); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.paint()
    bubble(cr, t, b, 540 + sgn * 150, 520); nametag(cr, name, 540 + sgn * 150, 1340, col_of(name))
def sh_two(cr, t, b, name, t0, t1):
    sgn = -1 if name == 'Canada' else 1; h = hop_of(t, b); rv = rival_of(name)
    pan = lerp(-60, 60, prog(t, t0, t1)) * sgn
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    for n, x in (('Canada', 290), ('Japan', 790)):
        hh = h if n == name else 0; ball(cr, n, x, 1300 - hh * 40, 220, 'happy' if n == name else 'angry', 0.05 * hh, 0.8 if n == 'Canada' else -0.8)
    cr.restore()
    sx = (290 if name == 'Canada' else 790) - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1600, col_of(name))
def sh_react(cr, t, b, name, t0, t1):
    rv = rival_of(name); k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.25, 1.08, k), -0.06 if rv == 'Canada' else 0.06, 540 + sx, 1080 + sy); set_of(rv, cr, t)
    ball(cr, rv, 540, 1150, 360, 'shock', 0, 0); cr.restore()
    ptext(cr, '?!', 860, 760, 170, GOLD, pop_k(t, t0 + 0.05), sw=14)
    nametag(cr, rv, 540, 1640, col_of(rv))
def sh_map(cr, t, b, name, t0, t1, scene):
    SCENE[scene](cr, t, b, t0, t1)
    sgn = -1 if name == 'Canada' else 1; h = hop_of(t, b); x = 540 + sgn * 380
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
CA_LAND, JP_LAND = (0.78, 0.26, 0.23), (0.93, 0.9, 0.86)
def sc_jlength(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), (0, 0), 0.24, 0.28, t0, t1, JP_LAND)
    a = kpt('JP', 122.93, 24.45, cx, cy, s); z = kpt('JP', 145.58, 43.33, cx, cy, s); k = ease_out(prog(t, t0 + 0.1, t0 + 0.9))
    cr.move_to(*a); cr.line_to(lerp(a[0], z[0], k), lerp(a[1], z[1], k)); cr.set_source_rgb(*GOLD[:3]); cr.set_line_width(10); cr.set_dash([26, 14]); cr.stroke(); cr.set_dash([])
    endmap(cr); label(cr, f'≈ {int(3000 * k):,} KM', 540, 640, 96, GOLD)
def sc_size(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (300, -300), (200, -500), 0.13, 0.15, t0, t1 + 1.5, CA_LAND)
    k = ease_out(prog(t, t0, t0 + 0.5)); cr.save(); cr.translate(0, (1 - k) * -900); km_shape(cr, G.jp_true, cx, cy, s, JP_LAND, 1, 300, -500, fill=0.95, lw=3, edge=INK); cr.restore()
    if k >= 1: chip(cr, 'JAPAN', cx + 300 * s, cy + 500 * s + 170 * s / 0.15, 30, WHITE, INK, 1, 1)
    endmap(cr)
    tx = at('r1b', 'twenty') + 0.4
    if t >= tx: sx, sy = shake(t, tx, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'CANADA = 26 JAPANS', 540, 640, 84, WHITE, t, tx); cr.restore()
def sc_caflag(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, -400), (0, -1100), 0.15, 0.2, t0, t1 + 2, CA_LAND); endmap(cr)
    k = ease_out(prog(t, t0, t0 + 1.0))
    for j in range(int(42 * k)):
        x, y = 160 + (j % 14) * 55, 1080 + (j // 14) * 64; cr.new_path(); cr.arc(x, y - 10, 9, 0, 2 * math.pi); cr.rectangle(x - 10, y, 20, 26); cr.set_source_rgb(1, 1, 1); cr.fill()
    label(cr, '41.8 MILLION', 540, 640, 100, WHITE); ptext(cr, 'STATISTICS CANADA · JULY 2026', 540, 710, 30, WHITE, 0.9, fam='Poppins ExtraBold', sw=5)
def sc_tokyo(cr, t, b, t0, t1):
    tt = at('r2b', 'Tokyo') - 0.3
    cx, cy, s = mview(cr, t, 'JP', (0, 0), tuple(G.p('JP', 139.7, 35.7)), 0.26, 0.9, tt, tt + 1.2, JP_LAND)
    x, y = kpt('JP', 139.76, 35.68, cx, cy, s); pin(cr, x, y, t, tt, JP_C)
    if t >= tt:
        rng = np.random.default_rng(5); kk = ease_out(prog(t, tt, tt + 1.4))
        for j in range(int(260 * kk)):
            r, a = abs(rng.normal(0, 70)), rng.uniform(0, 2 * math.pi); cr.new_path(); cr.arc(x + r * math.cos(a), y + r * math.sin(a), 4, 0, 2 * math.pi); cr.set_source_rgba(1, 0.9, 0.4, 0.85); cr.fill()
    endmap(cr)
    k = ease_out(prog(t, t0, t0 + 1.2)); label(cr, f'JAPAN {123 * k:.0f}M', 540, 600, 90, JP_C)
    if t >= tt: chip(cr, 'TOKYO AREA ≈ 37M', 540, 720, 46, GOLD, INK, pop_k(t, tt + 0.6), 1)
    tc = at('r2b', 'Canada') - 0.1
    if t >= tc: chip(cr, 'ALL OF CANADA: 41.8M', 540, 820, 46, CA_C, INK, pop_k(t, tc), 1)
def sc_biwa(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), tuple(G.p('JP', 136.1, 35.25)), 0.26, 2.6, t0, t0 + 1.3, JP_LAND)
    km_shape(cr, G.biwa, cx, cy, s, (0.3, 0.75, 1.0), 1, lw=4, edge=WHITE, glow=True); endmap(cr)
    if t >= t0 + 1.0: label(cr, 'LAKE BIWA', 540, 620, 100, (0.5, 0.85, 1)); ptext(cr, '~4 MILLION YEARS OLD', 540, 700, 44, WHITE, pop_k(t, t0 + 1.2), sw=7)
def sc_lakes(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, -200), (200, -500), 0.15, 0.19, t0, t1 + 2, CA_LAND)
    k = prog(t, t0 + 0.1, at('r3b', 'lakes') + 0.4); n = int(len(G.lakes) * k)
    for j, rs in enumerate(G.lakes[:n]):
        a = clamp((t - (t0 + 0.1 + j / len(G.lakes) * (at('r3b', 'lakes') + 0.3 - t0))) * 3)
        km_shape(cr, rs, cx, cy, s, (0.35, 0.8, 1.0), a, lw=1.5, edge=(0.85, 0.97, 1), glow=True)
    endmap(cr)
    label(cr, f'{int(850000 * ease_out(k)):,}+ LAKES', 540, 620, 96, (0.55, 0.88, 1))
    tp = at('r3b', 'sixty') - 0.1
    if t >= tp: chip(cr, "62% OF THE WORLD'S LAKES*", 540, 740, 46, WHITE, INK, pop_k(t, tp), 1); ptext(cr, '*LAKES LARGER THAN 10 HECTARES · HydroLAKES', 540, 820, 26, WHITE, 0.9, fam='Poppins ExtraBold', sw=5)
def sc_rockies(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, 0), tuple(G.p('CA', -120, 54)), 0.15, 0.42, t0, t0 + 1.3, CA_LAND)
    for j, (lon, lat) in enumerate(((-114.5, 49.5), (-116.2, 51.2), (-117.8, 52.5), (-119.5, 53.8), (-121.5, 55.5), (-123.5, 57.3), (-125.5, 59.0))):
        x, y = kpt('CA', lon, lat, cx, cy, s); tj = t0 + 1.0 + j * 0.1
        if t >= tj: emoji(cr, '🏔️', x, y - 30, 100 * pop_k(t, tj), 1)
    endmap(cr); label(cr, 'THE ROCKIES', 540, 620, 100, WHITE)
VOLC = [('FUJI', 35.36, 138.73), ('', 31.58, 130.66), ('', 32.88, 131.10), ('', 36.41, 138.52), ('', 32.76, 130.30), ('', 42.54, 140.84), ('', 35.89, 137.48), ('', 37.60, 140.08),
        ('', 31.93, 130.87), ('', 43.42, 142.69), ('', 34.08, 139.53), ('', 29.64, 129.71), ('', 35.23, 139.02), ('', 38.14, 140.44), ('', 39.85, 141.00), ('', 41.80, 140.82), ('', 36.79, 139.38)]
def sc_volcano(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), (0, 80), 0.27, 0.3, t0, t1 + 2, JP_LAND, rot=0.03)
    for j, (nm, lat, lon) in enumerate(VOLC):
        x, y = kpt('JP', lon, lat, cx, cy, s); tj = t0 + 0.2 + j * 0.09
        if t >= tj:
            emoji(cr, '🌋', x, y - 20, (90 if nm else 58) * pop_k(t, tj), 1)
            if nm: label(cr, nm, x + 90, y + 10, 40, WHITE, pop_k(t, tj))
    endmap(cr); k = ease_out(prog(t, t0, at('r4b', 'volcanoes') + 0.2)); label(cr, f'{int(111 * k)} ACTIVE VOLCANOES', 540, 620, 84, (1, 0.5, 0.35))
    tt = at('r4b', 'tenth') - 0.1
    if t >= tt: chip(cr, "≈ 10% OF THE WORLD'S", 540, 730, 46, WHITE, INK, pop_k(t, tt), 1)
def sc_islands(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), (-150, -150), 0.27, 0.33, t0, t1 + 1.5, JP_LAND)
    for j, r in enumerate(sorted(G.c['JP'], key=lambda r: len(r))):
        ph = (t * 1.5 + j * 0.13) % 1; km_shape(cr, [r], cx, cy, s, GOLD[:3], 0.6 * (1 - ph), lw=3, edge=GOLD[:3], glow=True)
    endmap(cr); k = ease_out(prog(t, t0, t0 + 1.0)); label(cr, f'{int(14125 * k):,} ISLANDS', 540, 620, 100, GOLD); ptext(cr, 'OFFICIAL COUNT · 2023', 540, 700, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
def sc_coast(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, 0), (0, 300), 0.15, 0.17, t0, t1 + 2, CA_LAND)
    te = at('r5b', 'kilometres') + 0.3; k = ease_io(prog(t, t0 + 0.1, te)); tot = sum(len(r) for r in G.coast); done = 0
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    for r in G.coast:
        m = int(clamp((k * tot - done) / len(r)) * len(r)); done += len(r)
        if m < 2: continue
        for wd, al in ((9, 0.3), (3, 1)):
            cr.new_path(); cr.move_to(cx + r[0, 0] * s, cy - r[0, 1] * s); [cr.line_to(cx + x * s, cy - y * s) for x, y in r[1:m]]
            cr.set_source_rgba(1, 1, 1, al); cr.set_line_width(wd); cr.stroke()
    endmap(cr); label(cr, f'{int(243042 * k):,} KM', 540, 620, 104, WHITE); ptext(cr, 'LONGEST COASTLINE ON EARTH', 540, 700, 40, GOLD, 1, fam='Poppins ExtraBold', sw=6)
    tq = at('r5b', 'Six') - 0.1
    if t >= tq: chip(cr, '= 6× AROUND THE EQUATOR', 540, 800, 46, GOLD, INK, pop_k(t, tq), 1); emoji(cr, '🌍', 540, 960, 140 * pop_k(t, tq), 1, rot=t)
def sc_onsen(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.12, 0.14, 0.26); g.add_color_stop_rgb(1, 0.5, 0.56, 0.7); cr.set_source(g); cr.paint()
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.1), 0.02, 540, 1000)
    cr.new_path(); cr.move_to(-200, 1100); cr.curve_to(300, 960, 800, 1000, 1300, 1080); cr.line_to(1300, 2100); cr.line_to(-200, 2100); cr.close_path(); cr.set_source_rgb(0.92, 0.95, 1); cr.fill()
    cr.save(); cr.translate(540, 1180); cr.scale(1, 0.32); cr.new_path(); cr.arc(0, 0, 420, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(0.35, 0.75, 0.85); cr.fill_preserve(); cr.set_source_rgb(0.4, 0.4, 0.45); cr.set_line_width(26); cr.stroke()
    for j in range(7):
        ph = ((t - t0) * 0.4 + j / 7) % 1; cr.new_path(); cr.arc(300 + j * 80 + 30 * math.sin(t + j), 1150 - 400 * ph, 40 + 60 * ph, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25 * (1 - ph)); cr.fill()
    for j, x in enumerate((420, 600, 720)): emoji(cr, '🐒', x, 1150 + 6 * math.sin(t * 2 + j), 120 if j != 1 else 150, 1)
    emoji(cr, '♨️', 860, 820, 120, 1); cr.restore()
    for j in range(50):
        ph = (t * 0.15 + j * 0.37) % 1; cr.new_path(); cr.arc((j * 89 + 40 * math.sin(t + j)) % 1100, ph * 1900, 5, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.8); cr.fill()
    label(cr, 'SNOW MONKEYS', 540, 620, 100, WHITE); ptext(cr, 'JIGOKUDANI, NAGANO', 540, 700, 36, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
def sc_snag(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'CA', (0, 0), tuple(G.p('CA', -137, 63)), 0.15, 0.55, t0, t0 + 1.2, CA_LAND)
    x, y = kpt('CA', -140.4, 62.37, cx, cy, s); pin(cr, x, y, t, t0 + 1.0, (0.6, 0.9, 1)); endmap(cr)
    if t >= t0 + 1.0: label(cr, 'SNAG, YUKON', 540, 620, 96, (0.7, 0.92, 1)); ptext(cr, 'FEBRUARY 3, 1947', 540, 700, 36, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
    k = ease_out(prog(t, at('r6b', 'minus') - 0.2, at('r6b', 'degrees') + 0.3)); tx, ty = 900, 1030
    rrect(cr, tx - 34, ty - 300, 68, 360, 34); cr.set_source_rgb(1, 1, 1); cr.fill(); cr.new_path(); cr.arc(tx, ty + 70, 60, 0, 2 * math.pi); cr.set_source_rgb(0.3, 0.6, 1); cr.fill()
    hh = lerp(320, 30, k); rrect(cr, tx - 18, ty + 40 - hh, 36, hh, 18); cr.set_source_rgb(0.3, 0.6, 1); cr.fill()
    if k > 0: label(cr, f'{-63 * k:.0f}°C', 600, 1000, 130, (0.7, 0.92, 1), clamp(k * 3))
    f = clamp(k) * 0.35; g = cairo.RadialGradient(540, 960, 300, 540, 960, 1100); g.add_color_stop_rgba(0, 0.8, 0.95, 1, 0); g.add_color_stop_rgba(1, 0.8, 0.95, 1, f); cr.set_source(g); cr.paint()
def sc_age(cr, t, b, t0, t1):
    set_japan(cr, t); cr.set_source_rgba(0.1, 0.05, 0.1, 0.45); cr.paint()
    label(cr, 'JAPANESE WOMEN', 540, 600, 84, WHITE); chip(cr, '#1 ON EARTH · 41 YEARS IN A ROW', 540, 700, 44, GOLD, INK, pop_k(t, t0 + 0.2), 1)
    tc = at('r7b', 'thousand') - 0.4
    if t >= tc:
        k = ease_out(prog(t, tc, tc + 1.4)); emoji(cr, '🎂', 540, 1000, 260 * pop_k(t, tc), 1)
        label(cr, f'{int(107677 * k):,}', 540, 1240, 120, GOLD); ptext(cr, 'PEOPLE AGED 100+ · SEPT 2026', 540, 1310, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def gdp_circle(cr, x, y, g, col, k, lab, size=50):
    r = 150 * math.sqrt(g / 4.4) * k
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, 0.92); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    if lab: ptext(cr, lab, x, y + size * 0.35, size, INK, clamp(k), sw=0, shadow=False)
def sc_gdpca(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE)
    k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 540, 1000, 2.4, CA_C, 0.2 + 0.8 * k, f'${2.4 * k:.1f}T', 70)
def sc_gdpjp(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'GDP · IMF 2026', 540, 620, 60, WHITE)
    gdp_circle(cr, 780, 1080, 2.4, CA_C, 1, '$2.4T', 46)
    k = ease_out(prog(t, t0, t0 + 0.9)); gdp_circle(cr, 360, 980, 4.4, JP_C, 0.2 + 0.8 * k, f'${4.4 * k:.1f}T', 76)
    td = at('r8b', 'double') - 0.1
    if t >= td: slam(cr, '≈ 2×', 780, 820, 110, WHITE, t, td)
def sc_aomori(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'JP', (0, 0), tuple(G.p('JP', 140.74, 40.82)), 0.27, 1.1, t0, t0 + 1.2, JP_LAND)
    x, y = kpt('JP', 140.74, 40.82, cx, cy, s); pin(cr, x, y, t, t0 + 1.0, WHITE); endmap(cr)
    for j in range(90):
        ph = (t * 0.25 + j * 0.173) % 1; cr.new_path(); cr.arc((j * 61 + 40 * math.sin(t * 1.5 + j)) % 1100, ph * 1900, 4 + (j % 3) * 2, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.85); cr.fill()
    if t >= t0 + 1.0: label(cr, 'AOMORI', 540, 600, 110, WHITE)
    base = 1330; sc = 105
    k = ease_out(prog(t, at('r9b', 'six') - 0.2, at('r9b', 'snow') + 0.3))
    if k > 0:
        hh = 6.2 * sc * k; rrect(cr, 250, base - hh, 200, hh, 18); cr.set_source_rgb(0.95, 0.97, 1); cr.fill(); label(cr, f'{6.2 * k:.1f} M', 350, base - hh - 20, 52, WHITE); ptext(cr, 'AOMORI', 350, base + 44, 32, WHITE, 1, fam='Poppins ExtraBold', sw=5)
    tc = at('r9b', 'three') - 0.2
    if t >= tc:
        k2 = ease_out(prog(t, tc, tc + 0.6)); hh = 3.4 * sc * k2; rrect(cr, 630, base - hh, 200, hh, 18); cr.set_source_rgb(*CA_C); cr.fill(); label(cr, f'{3.4 * k2:.1f} M', 730, base - hh - 20, 52, WHITE)
        ptext(cr, "CANADA'S SNOWIEST", 730, base + 44, 28, WHITE, 1, fam='Poppins ExtraBold', sw=5)
    if k > 0:
        px = 520; cr.new_path(); cr.arc(px, base - 1.8 * sc + 14, 14, 0, 2 * math.pi); cr.rectangle(px - 14, base - 1.8 * sc + 30, 28, 1.8 * sc - 30); cr.set_source_rgb(0.1, 0.1, 0.15); cr.fill()
        ptext(cr, '1.8 M', px, base - 1.8 * sc - 14, 26, WHITE, 1, fam='Poppins ExtraBold', sw=5)
SCENE = {'jlength': sc_jlength, 'size': sc_size, 'caflag': sc_caflag, 'tokyo': sc_tokyo, 'biwa': sc_biwa, 'lakes': sc_lakes, 'rockies': sc_rockies, 'volcano': sc_volcano,
         'islands': sc_islands, 'coast': sc_coast, 'onsen': sc_onsen, 'snag': sc_snag, 'age': sc_age, 'gdpca': sc_gdpca, 'gdpjp': sc_gdpjp, 'aomori': sc_aomori}

# ---------- hook, close-ups, title ----------
def draw_hook(cr, t):
    if t >= bt('h3c')['start']: return False
    b1, b2 = bt('h1'), bt('h2')
    if t < b2['start']:
        ti = 0.3; e = ease_out(prog(t, 0, ti)); sx, sy = shake(t, ti, 30, 0.6)
        cr.save(); cam(cr, push(t, 0, b2['start'], 1.0, 1.16), 0.05 * math.sin(t * 1.3), 540 + sx, 1000 + sy); arena(cr, t)
        rec = 26 * math.sin(math.pi * clamp((t - ti) / 0.35)) if t > ti else 0
        for n, x0, x1, sg, ph in (('Canada', 20, 318, -1, 0), ('Japan', 1060, 762, 1, 1.3)):
            ball(cr, n, lerp(x0, x1, e) + sg * rec, 1040 - abs(math.sin(t * 8 + ph)) * 22 * (t > ti + 0.3), 215, 'angry', 0.12 * (rec / 26), -sg * 0.8)
        if t >= ti: emoji(cr, '⚡', 540, 1010, 210 * pop_k(t, ti, 0.25), 1, rot=0.2 * math.sin(t * 14))
        cr.restore()
        g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.8); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 760); cr.set_source(g); cr.fill()
        slam(cr, 'CANADA', 540, 300, 170, CA_C, t, -0.3)
        if t >= w('h1', 'or') - 0.1: ptext(cr, 'OR', 540, 420, 70, WHITE, pop_k(t, w('h1', 'or') - 0.1), sw=9)
        slam(cr, 'JAPAN?', 540, 600, 190, JP_C, t, w('h1', 'Japan') - 0.15, rot=0.03)
        tq = w('h1', 'who') - 0.1
        if t >= tq: qx, qy = shake(t, tq, 14); cr.save(); cr.translate(qx, qy); slam(cr, 'WHO WOULD WIN?', 540, 1500, 124, GOLD, t, tq); cr.restore()
        f = 1 - prog(t, ti, ti + 0.15)
        if ti <= t and f > 0: cr.set_source_rgba(1, 1, 1, 0.75 * f); cr.paint()
        return True
    tp = w('h2', 'other') - 0.15
    if t < tp:
        cx, cy, s = mview(cr, t, 'CA', (0, 0), (250, -400), 0.13, 0.16, b2['start'], tp, CA_LAND)
        tj = w('h2', 'twenty') - 0.2; k = ease_out(prog(t, tj, tj + 0.4))
        if t >= tj: cr.save(); cr.translate(0, (1 - k) * -900); km_shape(cr, G.jp_true, cx, cy, s, JP_LAND, 1, 300, -500, fill=0.95, lw=3, edge=INK); cr.restore()
        endmap(cr)
        g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
        slam(cr, '26× BIGGER', 540, 330, 150, CA_C, t, tj + 0.2)
    else:
        cx, cy, s = mview(cr, t, 'JP', (0, 0), (0, 50), 0.32, 0.27, tp, b2['end'], JP_LAND)
        rng = np.random.default_rng(9); kk = ease_out(prog(t, tp, tp + 1.0))
        for j in range(int(700 * kk)):
            lon, lat = rng.uniform(129, 145), rng.uniform(31, 44); x, y = kpt('JP', lon, lat, cx, cy, s)
            p = G.p('JP', lon, lat)
            if inside(p, G.c['JP']): cr.new_path(); cr.arc(x, y, 3.5, 0, 2 * math.pi); cr.set_source_rgba(1, 0.85, 0.3, 0.9); cr.fill()
        endmap(cr)
        g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
        slam(cr, '3× THE PEOPLE', 540, 330, 130, JP_C, t, w('h2', 'three') - 0.1)
    streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.22)))
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
    ball(cr, 'Canada', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'Japan', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'CANADA', 540, 560, 180, CA_C, t, w('title', 'Eight'))
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
    for side, x, col, sc, lab in (('A', 250, CA_C, sn, 'CANADA'), ('U', 830, JP_C, ss, 'JAPAN')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = ('TIEBREAKER' if i == NR else f'ROUND {i}/8') if i else ('FINAL' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📏', 2: '👥', 3: '🏞️', 4: '🌋', 5: '🌊', 6: '🥶', 7: '🎂', 8: '📈', 9: '❄️'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((CA_C, JP_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    head = 'TIEBREAKER' if i == NR else f'ROUND {i}'
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, head, 0, 0, 130 if i == NR else 150, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = (at('c9', 'snow') - 0.1) if i == NR else b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    if i == NR:
        ptext(cr, '4 — 4', 540, 600, 90, WHITE, pop_k(t, b['l0']), sw=10)
        ts = at('c9', 'Surely') - 0.1
        if t >= ts: chip(cr, 'CANADA SHOULD WIN THIS… RIGHT?', 540, 1420, 44, CA_C, INK, pop_k(t, ts), 1)
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = CA_C if win == 'A' else JP_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('CANADA' if win == 'A' else 'JAPAN') + ' WINS'
    cr.save(); cr.translate(x, 1450); cr.rotate(-0.05 if win == 'A' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 72)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, 72, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- ending ----------
def draw_end(cr, t):
    e1, e2, c = bt('e1'), bt('e2'), bt('cta')
    if t < e2['start']:
        cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540, 1100); set_canada(cr, t); ball(cr, 'Canada', 540, 1290, 290, 'sad', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Canada', 540, 1640, CA_C)
        ptext(cr, 'JAPAN WINS 5 — 4', 540, 790, 80, JP_C, pop_k(t, e1['start'] + 0.2), sw=12); return
    if t < c['start']:
        k = ease_io(prog(t, e2['l0'], e2['l0'] + 0.6)); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.1), 0.04, 540, 1100); set_japan(cr, t)
        cr.save(); cr.translate(540, 1230); cr.rotate(0.35 * math.sin(math.pi * k)); ball(cr, 'Japan', 0, 0, 330, 'happy', 0, 0); cr.restore(); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Japan', 540, 1640, JP_C); emoji(cr, '🙇', 860, 820, 150 * pop_k(t, e2['l0'] + 0.3), 1); return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.08), 0.02, 540, 1000); arena(cr, t)
    ball(cr, 'Canada', 290, 1300, 200, 'sad', 0, 0.8); ball(cr, 'Japan', 790, 1300, 200, 'happy', 0, -0.8); cr.restore()
    ptext(cr, '5 — 4', 540, 1000, 140, WHITE, 1, sw=14)
    for x, col, word, lab, rot in ((290, CA_C, 'Canada', 'CANADA', -0.04), (790, JP_C, 'Japan', 'JAPAN', 0.04)):
        tt = w('cta', word)
        if t < tt: continue
        kk = pop_k(t, tt) * (1 + 0.03 * math.sin(t * 6 + x)); cr.save(); cr.translate(x, 650); cr.rotate(rot); cr.scale(kk, kk); ptext(cr, lab, 0, 0, 120, col, 1, sw=12); cr.restore()
    tc = w('cta', 'Comment')
    if t >= tc: kk = pop_k(t, tc); cr.save(); cr.translate(540, 450); cr.scale(kk, kk); ptext(cr, 'COMMENT YOUR SIDE', 0, 0, 82, WHITE, 1, sw=11); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        kk = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1620); cr.scale(kk, kk); txt = 'FOLLOW FOR THE NEXT BATTLE'; wd = tw(cr, txt, 46)
        rrect(cr, -wd / 2 - 50, -62, wd + 100, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill(); ptext(cr, txt, 0, 4, 46, WHITE, 1, sw=0, shadow=False); cr.restore()

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if draw_hook(cr, t): C.draw_captions(cr, t, 1700); return
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
    boom(0.3, 1.0); boom(w('h1', 'Japan') - 0.15, 0.7); boom(w('h1', 'who') - 0.1, 0.8)
    whoosh(bt('h2')['start'] - 0.3); boom(w('h2', 'twenty') + 0.2, 0.9); whoosh(w('h2', 'other') - 0.45, 0.3); boom(w('h2', 'three') - 0.1, 0.7)
    for k in ('h3c', 'h3j', 'title'): whoosh(bt(k)['start'] - 0.35)
    for wd in ('Eight', 'winner', 'geography'): boom(w('title', wd), 0.7)
    horn(w('title', 'geography'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1); pop(tv + 0.55, 0.12, 500)
    for k, sp, _ in LINES:
        if sp: whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
        if k in SHOTS:
            for s0, sh in shot_list(k)[1:]: whoosh(s0 - 0.2, 0.16, 0.22)
    boom(at('c9', 'snow') - 0.1, 0.9); rumble(at('c9', 'Surely'), 1.2, 0.15)
    boom(bt('e1')['start'], 0.6); bell(bt('e2')['l0'] + 0.3, 0.12, 1568); cheer(bt('e2')['l0'] + 0.3, 0.1, 1.6)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_cajp'))
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
