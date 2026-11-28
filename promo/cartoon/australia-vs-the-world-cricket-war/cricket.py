# Countryballs: Australia vs the World, the Cricket War (9:16, multi-voice, multi-shot).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (trophies, speed guns, scoreboards, the Ashes urn...).
# Usage: python3 cricket.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

AU_C, W_C = hexc('#FFC233')[:3], hexc('#3FD0C9')[:3]
A_C, U_C = AU_C, W_C
COL = {'Australia': AU_C, 'England': hexc('#F0435A')[:3], 'India': hexc('#4F8CFF')[:3], 'West Indies': hexc('#D8506E')[:3], 'Pakistan': hexc('#2DBE6C')[:3],
       'New Zealand': hexc('#C8CCD4')[:3], 'Sri Lanka': hexc('#5B8DEF')[:3], 'Afghanistan': hexc('#4FA3FF')[:3], 'South Africa': hexc('#2DBE6C')[:3]}
FLAGF = {'Australia': 'au', 'England': 'gb-eng', 'India': 'in', 'West Indies': 'wi', 'Pakistan': 'pk', 'New Zealand': 'nzfern', 'Sri Lanka': 'lk', 'Afghanistan': 'af', 'South Africa': 'za'}
OPPS = {1: 'England', 2: 'India', 3: 'West Indies', 4: 'Pakistan', 5: 'New Zealand', 6: 'Sri Lanka', 7: 'Afghanistan', 8: 'South Africa'}
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Australia': ('en-AU-WilliamNeural', '+4%'), 'England': ('en-GB-RyanNeural', '+4%'), 'India': ('en-IN-PrabhatNeural', '+4%'), 'West Indies': ('en-GB-ThomasNeural', '+4%'),
         'Pakistan': ('ur-PK-AsadNeural', '+4%'), 'New Zealand': ('en-NZ-MitchellNeural', '+4%'), 'Sri Lanka': ('si-LK-SameeraNeural', '+4%'), 'Afghanistan': ('ps-AF-GulNawazNeural', '+4%'),
         'South Africa': ('en-ZA-LukeNeural', '+4%')}
LINES = [
    ('h1', 'England', "Australia! You stole our game!"),
    ('h2', 'India', "And we stole your trophies!"),
    ('h3', 'Australia', "Mate, I'll take on every single one of you."),
    ('title', None, "Eight nations. Eight rounds. This is the cricket war."),
    ('c1', None, "Round one: England."),
    ('r1a', 'England', "I invented cricket! I've got Lord's!"),
    ('r1b', 'Australia', "And I won the first Test ever, in eighteen seventy-seven. Plus the last Ashes, four-one!"),
    ('c2', None, "Round two: India."),
    ('r2a', 'Australia', "I've got a T twenty World Cup!"),
    ('r2b', 'India', "I've got three. And I won the last two in a row!"),
    ('c3', None, "Round three: the West Indies."),
    ('r3a', 'West Indies', "I won the first two World Cups ever! Seventy-five and seventy-nine!"),
    ('r3b', 'Australia', "Respect. But I've won six. More than anyone!"),
    ('c4', None, "Round four: Pakistan."),
    ('r4a', 'Australia', "Brett Lee bowled at one hundred and sixty-one kilometres an hour!"),
    ('r4b', 'Pakistan', "Shoaib Akhtar bowled one hundred and sixty-one point three. The fastest ball ever recorded!"),
    ('c5', None, "Round five: New Zealand."),
    ('r5a', 'New Zealand', "I won the first ever World Test Championship!"),
    ('r5b', 'Australia', "Nice. But I beat you in two World Cup finals. Twenty fifteen, and twenty twenty-one!"),
    ('c6', None, "Round six: Sri Lanka."),
    ('r6a', 'Australia', "Shane Warne took seven hundred and eight Test wickets!"),
    ('r6b', 'Sri Lanka', "Muttiah Muralitharan took eight hundred. The most ever!"),
    ('c7', None, "Round seven: Afghanistan."),
    ('r7a', 'Afghanistan', "At the World Cup, we had you at ninety-one for seven!"),
    ('r7b', 'Australia', "Then Maxwell hit two hundred and one not out. On one leg!"),
    ('c8', None, "Final round: South Africa."),
    ('r8a', 'Australia', "I've won the World Test Championship!"),
    ('r8b', 'South Africa', "And I beat you in the next final. At Lord's!"),
    ('e1', 'Australia', "Four all?! So who do I play in the final?"),
    ('e2', 'India', "Let the fans decide!"),
    ('cta', None, "It's four all! Who should Australia face in the final? Comment below, and subscribe to see who wins!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('THE ASHES', 'A', ('r1b', 'four')), 2: ('T20 WORLD CUPS', 'U', ('r2b', 'row')), 3: ('ODI WORLD CUPS', 'A', ('r3b', 'anyone')), 4: ('FASTEST BALL', 'U', ('r4b', 'recorded')),
      5: ('BIG FINALS', 'A', ('r5b', 'twenty-one')), 6: ('MOST WICKETS', 'U', ('r6b', 'ever')), 7: ('GREATEST CHASE', 'A', ('r7b', 'leg')), 8: ('TEST CHAMPIONSHIP', 'U', ('r8b', 'Lord'))}
NR = 8
SHOTS = {
    'r1a': [(None, 'close'), ('Lord', 'map:lords')], 'r1b': [(None, 'two'), ('first', 'map:firsttest')],
    'r2a': [(None, 'low'), ('twenty', 'map:t20aus')], 'r2b': [(None, 'ots'), ('three', 'map:t20ind')],
    'r3a': [(None, 'close'), ('first', 'map:wi7579')], 'r3b': [(None, 'low'), ('six', 'map:odi6')],
    'r4a': [(None, 'two'), ('Brett', 'map:speedlee')], 'r4b': [(None, 'ots'), ('Shoaib', 'map:speedshoaib')],
    'r5a': [(None, 'close'), ('first', 'map:wtc21')], 'r5b': [(None, 'two'), ('beat', 'map:finals')],
    'r6a': [(None, 'low'), ('Shane', 'map:warne')], 'r6b': [(None, 'ots'), ('Muttiah', 'map:murali')],
    'r7a': [(None, 'two'), ('ninety', 'map:s917')], 'r7b': [(None, 'low'), ('Maxwell', 'map:maxwell')],
    'r8a': [(None, 'close'), ('won', 'map:wtc23')], 'r8b': [(None, 'ots'), ('beat', 'map:lords25')]}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {}}
C.HOT = ('australia', 'england', 'india', 'cricket', 'war', 'trophies', 'tie', 'final', 'comment', 'subscribe', 'four', 'world')
C.TAIL_OVERRIDE = {'h1': 0.12, 'h2': 0.2, 'h3': 0.5, 'title': 0.6, 'e1': 0.3, 'e2': 0.4, 'cta': 3.6, **{f'c{i}': 0.15 for i in range(1, 9)},
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
CUR_OPP = 'India'
class Geo:
    def __init__(self, d):
        for n, f in FLAGF.items(): B.FL[n] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', f + '.png'))

def at(key, word, n=0): return w(key, word, n)
def side_of(name): return 'A' if name == 'Australia' else 'U'
def col_of(name): return COL.get(name, W_C)
def rival_of(name): return CUR_OPP if name == 'Australia' else 'Australia'

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



def set_ground(cr, t, name='Australia', zoom=1.0):
    col = col_of(name)
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.05, 0.16); g.add_color_stop_rgb(0.42, 0.14, 0.17, 0.36); g.add_color_stop_rgb(1, 0.05, 0.1, 0.08); cr.set_source(g); cr.paint()
    rng = np.random.default_rng(5)
    for _ in range(50): x, y = rng.uniform(0, W), rng.uniform(0, 450); cr.new_path(); cr.arc(x, y, 1.5, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.4 + 0.3 * math.sin(t * 2 + x)); cr.fill()
    for fx_ in (70, 1010):  # floodlights
        cr.rectangle(fx_ - 8, 330, 16, 520); cr.set_source_rgb(0.2, 0.22, 0.3); cr.fill()
        rrect(cr, fx_ - 70, 270, 140, 80, 10); cr.set_source_rgb(0.95, 0.95, 0.85); cr.fill()
        gl = cairo.RadialGradient(fx_, 310, 10, fx_, 310, 420); gl.add_color_stop_rgba(0, 1, 1, 0.9, 0.45); gl.add_color_stop_rgba(1, 1, 1, 0.9, 0); cr.set_source(gl); cr.paint()
    cr.new_path(); cr.move_to(-100, 1180); cr.curve_to(200, 700, 880, 700, 1180, 1180); cr.line_to(1180, 1250); cr.line_to(-100, 1250); cr.close_path(); cr.set_source_rgb(0.1, 0.1, 0.18); cr.fill()
    crowd = [col, (1, 1, 1), (0.95, 0.75, 0.25), (0.9, 0.3, 0.35), (0.3, 0.6, 1)]
    for j in range(520):
        x = rng.uniform(-60, 1140); y0 = 1180 - 420 * (1 - ((x - 540) / 700) ** 2); y = rng.uniform(y0 + 25, 1170)
        c_ = crowd[j % 5]; cr.new_path(); cr.arc(x, y + 3 * math.sin(t * 6 + j), 6, 0, 2 * math.pi); cr.set_source_rgba(*c_, 0.65); cr.fill()
    cr.save(); cr.new_path(); cr.translate(540, 1560); cr.scale(1, 0.42); cr.arc(0, 0, 1000, 0, 2 * math.pi); cr.restore()
    cr.save(); cr.clip_preserve(); cr.set_source_rgb(0.16, 0.5, 0.22); cr.fill()
    for j in range(-10, 12, 2): cr.rectangle(540 + j * 100, 1100, 100, 1000); cr.set_source_rgba(1, 1, 1, 0.05); cr.fill()
    cr.restore()
    cr.new_path(); cr.move_to(480, 1250); cr.line_to(600, 1250); cr.line_to(680, 1960); cr.line_to(400, 1960); cr.close_path(); cr.set_source_rgb(0.82, 0.74, 0.52); cr.fill()
    for x in (528, 540, 552): cr.rectangle(x - 2.5, 1222, 5, 30); cr.set_source_rgb(0.98, 0.95, 0.85); cr.fill()
    gt = cairo.RadialGradient(540, 1900, 100, 540, 1900, 900); gt.add_color_stop_rgba(0, *col, 0.25); gt.add_color_stop_rgba(1, *col, 0); cr.set_source(gt); cr.paint()
def set_of(name, cr, t): set_ground(cr, t, name)

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
    for n, x in (('Australia', 290), (CUR_OPP, 790)):
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
def label(cr, txt, x, y, size, col, a=1.0): ptext(cr, txt, x, y, fit(cr, txt, size, 1000), col, a, sw=size * 0.14)
def sub(cr, txt, y, a=1.0): ptext(cr, txt, 540, y, 36, WHITE, a, fam='Poppins ExtraBold', sw=6)
def trophy(cr, t, x, y, size, year, col, t0):
    if t < t0: return
    k = pop_k(t, t0, 0.3); emoji(cr, '🏆', x, y - abs(math.sin(t * 3 + x)) * 8, size * k, 1, rot=0.06 * math.sin(t * 2 + x))
    ptext(cr, year, x, y + size * 0.78, size * 0.34, col, k, sw=7)
def board(cr, t, t0, rows, y=1000, wd=900):
    if t < t0: return
    k = pop_k(t, t0, 0.3); hh = 80 + sum(r[2] * 1.25 for r in rows); cr.save(); cr.translate(540, y); cr.scale(k, k)
    rrect(cr, -wd / 2, -hh / 2, wd, hh, 30); cr.set_source_rgb(0.04, 0.12, 0.08); cr.fill_preserve(); cr.set_source_rgb(0.95, 0.85, 0.4); cr.set_line_width(7); cr.stroke()
    y_ = -hh / 2 + 40
    for txt, col, sz in rows: y_ += sz * 0.95; ptext(cr, txt, 0, y_, fit(cr, txt, sz, wd - 80), col, 1, sw=0, shadow=False); y_ += sz * 0.3
    cr.restore()
def urn(cr, x, y, s):
    cr.save(); cr.translate(x, y); cr.scale(s, s); cr.new_path(); cr.move_to(-18, -60); cr.curve_to(-50, -40, -60, 10, -30, 40); cr.line_to(-36, 70); cr.line_to(36, 70); cr.line_to(30, 40); cr.curve_to(60, 10, 50, -40, 18, -60); cr.close_path()
    cr.set_source_rgb(0.55, 0.38, 0.22); cr.fill_preserve(); cr.set_source_rgb(0.2, 0.12, 0.05); cr.set_line_width(5); cr.stroke(); rrect(cr, -24, -78, 48, 22, 8); cr.set_source_rgb(0.4, 0.27, 0.15); cr.fill(); cr.restore()
def sc_lords(cr, t, b, t0, t1):
    cr.save(); cam(cr, push(t, t0, t1 + 1, 1.0, 1.12), 0, 540, 1000); set_ground(cr, t, 'England')
    x0 = 300; cr.rectangle(x0, 760, 480, 380); cr.set_source_rgb(0.62, 0.32, 0.24); cr.fill()
    for tx in (x0 + 20, x0 + 400): cr.rectangle(tx, 640, 60, 140); cr.fill(); cr.new_path(); cr.move_to(tx - 8, 640); cr.line_to(tx + 30, 590); cr.line_to(tx + 68, 640); cr.close_path(); cr.set_source_rgb(0.3, 0.32, 0.36); cr.fill(); cr.set_source_rgb(0.62, 0.32, 0.24)
    for r in range(3):
        for c_ in range(6): rrect(cr, x0 + 40 + c_ * 72, 800 + r * 105, 44, 70, 18); cr.set_source_rgba(1, 0.9, 0.6, 0.85); cr.fill()
    cr.rectangle(x0 - 20, 900, 520, 16); cr.set_source_rgb(0.95, 0.95, 0.9); cr.fill(); cr.restore()
    cr.set_source_rgba(0.02, 0.02, 0.08, 0.2); cr.paint()
    label(cr, "LORD'S · HOME OF CRICKET", 540, 560, 72, COL['England'])
    ti = at('r1a', 'Lord') - 0.1
    if t >= ti: chip(cr, 'FIRST LAWS OF CRICKET · 1744', 540, 670, 44, WHITE, INK, pop_k(t, ti), 1)
def sc_firsttest(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'FIRST TEST EVER · 1877', 540, 600, 80, AU_C)
    board(cr, t, t0 + 0.3, [('MCG · MARCH 1877', WHITE, 50), ('AUSTRALIA WON', AU_C, 74), ('BY 45 RUNS', WHITE, 56)], 930)
    ta = at('r1b', 'Ashes') - 0.1
    if t >= ta:
        k = pop_k(t, ta, 0.3); urn(cr, 540, 1330, 1.6 * k)
        sx, sy = shake(t, at('r1b', 'four'), 12); cr.save(); cr.translate(sx, sy); slam(cr, 'ASHES 2025–26: 4–1', 540, 1540, 74, GOLD, t, at('r1b', 'four') - 0.1) if t >= at('r1b', 'four') - 0.1 else None; cr.restore()
def sc_t20aus(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'T20 WORLD CUPS', 540, 600, 96, AU_C); trophy(cr, t, 540, 1030, 280, '2021', AU_C, t0 + 0.2)
def sc_t20ind(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'T20 WORLD CUPS', 540, 600, 96, COL['India'])
    tt = at('r2b', 'three') - 0.1
    for j, yr in enumerate(('2007', '2024', '2026')): trophy(cr, t, 220 + j * 320, 1000, 210, yr, COL['India'], tt + j * 0.18)
    tr = at('r2b', 'last') - 0.1
    if t >= tr: chip(cr, 'BACK TO BACK · FIRST TEAM EVER', 540, 720, 46, GOLD, INK, pop_k(t, tr), 1)
    ptext(cr, 'AUSTRALIA: 1', 540, 1420, 44, AU_C, 1, sw=7)
def sc_wi7579(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'THE FIRST TWO WORLD CUPS', 540, 600, 80, COL['West Indies'])
    trophy(cr, t, 330, 1010, 240, '1975', COL['West Indies'], at('r3a', 'Seventy') - 0.1); trophy(cr, t, 750, 1010, 240, '1979', COL['West Indies'], at('r3a', 'seventy', 1) - 0.1)
def sc_odi6(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'MEN\'S ODI WORLD CUPS', 540, 600, 80, AU_C); ts = at('r3b', 'six') - 0.1
    for j, yr in enumerate(('1987', '1999', '2003', '2007', '2015', '2023')): trophy(cr, t, 220 + (j % 3) * 320, 900 + (j // 3) * 330, 170, yr, AU_C, ts + j * 0.12)
    tm = at('r3b', 'More') - 0.1
    if t >= tm: chip(cr, 'MOST EVER', 540, 710, 56, GOLD, INK, pop_k(t, tm), 1)
def speed(cr, t, t0, t1, val, col, who, k_end):
    arena(cr, t); k = ease_out(prog(t, t0, k_end))
    for j in range(6): y = 1250 + j * 14; cr.move_to(lerp(-200, 900, k) - 400 - j * 60, y); cr.line_to(lerp(-200, 900, k) - 30, y); cr.set_source_rgba(1, 1, 1, 0.15 + 0.05 * j); cr.set_line_width(4); cr.stroke()
    x = lerp(-200, 900, k); cr.new_path(); cr.arc(x, 1290, 40, 0, 2 * math.pi); cr.set_source_rgb(0.8, 0.1, 0.12); cr.fill(); cr.move_to(x - 30, 1270); cr.curve_to(x - 10, 1300, x + 10, 1300, x + 30, 1270); cr.set_source_rgb(1, 1, 1); cr.set_line_width(3); cr.stroke()
    rrect(cr, 190, 820, 700, 260, 36); cr.set_source_rgb(0.02, 0.03, 0.06); cr.fill_preserve(); cr.set_source_rgb(*col); cr.set_line_width(8); cr.stroke()
    ptext(cr, f'{val * k:.1f}', 540, 1000, 170, col, 1, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, 'KM/H', 800, 1060, 40, WHITE, 1, fam='Poppins ExtraBold', sw=0, shadow=False)
    label(cr, who, 540, 640, 76, col)
def sc_speedlee(cr, t, b, t0, t1):
    speed(cr, t, t0, t1, 161.1, AU_C, 'BRETT LEE · 2005', at('r4a', 'hour') + 0.2)
def sc_speedshoaib(cr, t, b, t0, t1):
    speed(cr, t, t0, t1, 161.3, COL['Pakistan'], 'SHOAIB AKHTAR · 2003', at('r4b', 'three') + 0.3)
    tf = at('r4b', 'fastest') - 0.1
    if t >= tf: chip(cr, 'FASTEST BALL EVER RECORDED', 540, 740, 48, GOLD, INK, pop_k(t, tf), 1)
    ptext(cr, 'BRETT LEE: 161.1', 540, 1450, 40, AU_C, 1, sw=6)
def sc_wtc21(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'WORLD TEST CHAMPIONSHIP', 540, 600, 70, COL['New Zealand']); trophy(cr, t, 540, 1020, 260, '2021', COL['New Zealand'], t0 + 0.2)
    tf = at('r5a', 'first') - 0.1
    if t >= tf: chip(cr, 'FIRST EVER WINNERS', 540, 710, 48, GOLD, INK, pop_k(t, tf), 1)
def sc_finals(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'WORLD CUP FINALS VS NZ', 540, 600, 74, AU_C)
    board(cr, t, at('r5b', 'Twenty') - 0.1, [('2015 · MCG', WHITE, 50), ('AUSTRALIA WON BY 7 WKTS', AU_C, 56)], 860, 940)
    board(cr, t, at('r5b', 'twenty-one') - 0.2, [('2021 T20 · DUBAI', WHITE, 50), ('AUSTRALIA WON BY 8 WKTS', AU_C, 56)], 1200, 940)
def sc_warne(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'SHANE WARNE', 540, 600, 100, AU_C); k = ease_out(prog(t, at('r6a', 'seven') - 0.2, at('r6a', 'wickets') + 0.2))
    ptext(cr, f'{int(708 * k)}', 540, 1060, 260, WHITE, 1, sw=18); sub(cr, 'TEST WICKETS', 1170)
    for j in range(3):
        a = -0.9 * ease_out(prog(t, at('r6a', 'wickets') - 0.1, at('r6a', 'wickets') + 0.4)) * (j - 1)
        cr.save(); cr.translate(500 + j * 40, 1460); cr.rotate(a); cr.rectangle(-6, -180, 12, 180); cr.set_source_rgb(0.98, 0.94, 0.82); cr.fill(); cr.restore()
def sc_murali(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'MOST TEST WICKETS', 540, 600, 84, COL['Sri Lanka'])
    def wbar(x, v, k, col, nm, lab):
        hh = max(8, 560 * v / 800 * k); rrect(cr, x - 110, 1350 - hh, 220, hh, 18); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
        ptext(cr, lab, x, 1350 - hh - 26, 64, WHITE, clamp(k * 2), sw=8); ball(cr, nm, x, 1440, 56, 'happy', 0, 0)
    wbar(270, 708, 1, AU_C, 'Australia', '708'); k = ease_out(prog(t, at('r6b', 'eight') - 0.2, at('r6b', 'eight') + 0.8)); wbar(640, 800, k, COL['Sri Lanka'], 'Sri Lanka', '800')
    ptext(cr, 'WARNE', 270, 1530, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6); ptext(cr, 'MURALITHARAN', 640, 1530, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_s917(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'WORLD CUP 2023 · MUMBAI', 540, 600, 70, COL['Afghanistan'])
    board(cr, t, t0 + 0.2, [('AUSTRALIA', AU_C, 60), ('91 / 7', (1, 0.35, 0.35), 150), ('NEEDING 292', WHITE, 54)], 1000)
def sc_maxwell(cr, t, b, t0, t1):
    arena(cr, t); k = ease_io(prog(t, t0 + 0.2, at('r7b', 'out') + 0.2)); runs = int(lerp(91, 293, k)); mx = int(lerp(0, 201, k))
    label(cr, f'MAXWELL {mx}*', 540, 600, 110, AU_C)
    board(cr, t, t0, [('AUSTRALIA', AU_C, 60), (f'{runs} / 7', WHITE, 150), ('WON BY 3 WICKETS' if k >= 1 else 'CHASING 292', GOLD if k >= 1 else WHITE, 54)], 1000)
    tl = at('r7b', 'leg') - 0.1
    if t >= tl: chip(cr, 'CRAMPING · BARELY ABLE TO RUN', 540, 1330, 44, GOLD, INK, pop_k(t, tl), 1)
def sc_wtc23(cr, t, b, t0, t1):
    arena(cr, t); label(cr, 'WORLD TEST CHAMPIONSHIP', 540, 600, 70, AU_C); trophy(cr, t, 540, 1020, 260, '2023', AU_C, t0 + 0.2)
    chip(cr, 'BEAT INDIA AT THE OVAL', 540, 710, 46, WHITE, INK, pop_k(t, t0 + 0.4), 1) if t >= t0 + 0.4 else None
def sc_lords25(cr, t, b, t0, t1):
    arena(cr, t); label(cr, "WTC FINAL 2025 · LORD'S", 540, 600, 74, COL['South Africa'])
    board(cr, t, t0 + 0.2, [('SOUTH AFRICA', COL['South Africa'], 70), ('BEAT AUSTRALIA', WHITE, 64), ('BY 5 WICKETS', GOLD, 56)], 1000)
    tl = at('r8b', 'Lord') - 0.1
    if t >= tl: chip(cr, 'FIRST ICC TITLE IN 27 YEARS', 540, 1300, 46, GOLD, INK, pop_k(t, tl), 1)
SCENE = {'lords': sc_lords, 'firsttest': sc_firsttest, 't20aus': sc_t20aus, 't20ind': sc_t20ind, 'wi7579': sc_wi7579, 'odi6': sc_odi6, 'speedlee': sc_speedlee, 'speedshoaib': sc_speedshoaib,
         'wtc21': sc_wtc21, 'finals': sc_finals, 'warne': sc_warne, 'murali': sc_murali, 's917': sc_s917, 'maxwell': sc_maxwell, 'wtc23': sc_wtc23, 'lords25': sc_lords25}

# ---------- hook, title ----------
RING = ['England', 'India', 'West Indies', 'Pakistan', 'New Zealand', 'Sri Lanka', 'Afghanistan', 'South Africa']
def ring_pos(j): a = -math.pi / 2 + j / 8 * 2 * math.pi + math.pi / 8; return 540 + 400 * math.cos(a), 1180 + 330 * math.sin(a)
def draw_hook(cr, t):
    """Cold open: England and India pile on, Australia accepts, then all eight rivals drop in around it."""
    if t >= bt('title')['start']: return False
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        sh_close(cr, t, b1, 'England', 0, b1['end'], 'angry'); emoji(cr, '🏏', 880, 820, 150, 1, rot=-0.3 + 0.1 * math.sin(t * 4))
        return True
    if t < b3['start']:
        sx, sy = shake(t, w('h2', 'trophies') - 0.05, 20, 0.4); cr.save(); cr.translate(sx, sy)
        sh_low(cr, t, b2, 'India', b2['start'], b2['end'], 'angry'); cr.restore()
        tt = w('h2', 'trophies') - 0.1
        if t >= tt: emoji(cr, '🏆', 860, 820, 150 * pop_k(t, tt, 0.3), 1)
        streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2)))
        return True
    h = hop_of(t, b3); te = w('h3', 'every') - 0.1
    cr.save(); cam(cr, push(t, b3['start'], b3['end'] + 0.5, 1.1, 0.95), 0, 540, 1150); set_ground(cr, t, 'Australia')
    for j, nm in enumerate(RING):
        tj = te + j * 0.13
        if t < tj: continue
        x, y = ring_pos(j); k = ease_out(prog(t, tj, tj + 0.25)); yy = lerp(y - 900, y, k)
        ball(cr, nm, x, yy - abs(math.sin(t * 5 + j)) * 8, 92, 'angry', 0, (540 - x) / 400)
    ball(cr, 'Australia', 540, 1180 - h * 30, 190, 'angry' if t >= te else 'happy', 0.04 * h, 0)
    cr.restore()
    bubble(cr, t, b3, 540, 480); nametag(cr, 'Australia', 540, 1640, AU_C)
    ty = w('h3', 'you') + 0.05
    if t >= ty: sx, sy = shake(t, ty, 16); cr.save(); cr.translate(sx, sy); slam(cr, 'AUSTRALIA VS THE WORLD', 540, 1780, 76, GOLD, t, ty); cr.restore()
    f = 1 - prog(t, b3['start'], b3['start'] + 0.15)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b3['start'], b3['start'] + 0.2)))
    return True
def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.08), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.5))
    ball(cr, 'Australia', lerp(-200, 290, e), 1400 - abs(math.sin(t * 6)) * 14, 180, 'angry', 0, 0.8)
    for j, nm in enumerate(RING):
        x = lerp(1300, 600 + (j % 4) * 115, e); y = 1330 + (j // 4) * 135
        ball(cr, nm, x, y - abs(math.sin(t * 6 + j)) * 10, 58, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'AUSTRALIA', 540, 540, 150, AU_C, t, w('title', 'Eight'))
    tv = w('title', 'rounds')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 700); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 90, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 34, 100, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'THE WORLD', 540, 900, 150, W_C, t, w('title', 'This'))
    tg = w('title', 'cricket')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE CRICKET WAR 🏏'.replace(' 🏏', ''), 540, 1080, 96, WHITE, t, tg); cr.restore()
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
    for side, x, col, sc, lab in (('A', 250, AU_C, sn, 'AUSTRALIA'), ('U', 830, W_C, ss, 'THE WORLD')):
        ptext(cr, lab, x, 200, 42, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = f'ROUND {i}/8' if i else ('FINAL: 4 — 4' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2)); opp = OPPS[i]
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((AU_C, COL[opp])):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    head = 'FINAL ROUND' if i == NR else f'ROUND {i}'
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 760); cr.scale(s, s); ptext(cr, head, 0, 0, 120 if i == NR else 140, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = b['l0'] + 0.35
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = 'VS ' + opp.upper(); cr.save(); cr.translate(540, 940); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 120, 860), WHITE, 1, sw=14); cr.restore()
        ball(cr, opp, 540, 1200 - abs(math.sin(t * 5)) * 12, 130 * kk, 'angry', 0, 0)
        ptext(cr, RD[i][0], 540, 1420, 52, COL[opp], kk, fam='Poppins ExtraBold', sw=8)
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = AU_C if win == 'A' else COL[OPPS[i]]; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('AUSTRALIA' if win == 'A' else OPPS[i].upper()) + ' WINS'
    cr.save(); cr.translate(x, 1450); cr.rotate(-0.05 if win == 'A' else 0.05); cr.scale(s, s); sz = fit(cr, txt, 72, 820); wd = tw(cr, txt, sz)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, sz, INK, 1, sw=0, shadow=False); cr.restore()

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
        sx, sy = shake(t, e1['l0'], 20, 0.4); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540 + sx, 1100 + sy); set_ground(cr, t, 'Australia'); ball(cr, 'Australia', 540, 1290, 290, 'shock', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Australia', 540, 1640, AU_C)
        ptext(cr, '4 — 4', 540, 820, 130, WHITE, pop_k(t, e1['start'] + 0.1), sw=14); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540, 1100); set_ground(cr, t, 'India')
        ball(cr, 'India', 540, 1260 - h * 50, 300, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'India', 540, 1640, COL['India']); emoji(cr, '🏏', 200, 900, 140 * pop_k(t, e2['l0'] + 0.3), 1, rot=-0.3)
        return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.06), 0.02, 540, 1000); arena(cr, t); cr.restore()
    sx, sy = shake(t, c['start'], 16, 0.4); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A TIE!", 540, 470, 140, GOLD, t, c['start']); cr.restore()
    ptext(cr, 'AUSTRALIA', 230, 590, 50, AU_C, 1, sw=8); ptext(cr, '4 — 4', 540, 600, 84, WHITE, 1, sw=10); ptext(cr, 'THE WORLD', 850, 590, 50, W_C, 1, sw=8)
    tp = w('cta', 'Who') - 0.1
    if t >= tp:
        kk = pop_k(t, tp); cr.save(); cr.translate(540, 730); cr.scale(kk, kk); ptext(cr, 'WHO DOES AUSTRALIA', 0, 0, 62, WHITE, 1, sw=9); ptext(cr, 'PLAY IN THE FINAL?', 0, 76, 62, WHITE, 1, sw=9); cr.restore()
        for j, nm in enumerate(('India', 'England', 'New Zealand')):
            tj = tp + 0.5 + j * 0.25
            if t < tj: continue
            x = 220 + j * 320; k2 = pop_k(t, tj); ball(cr, nm, x, 1010 - abs(math.sin(t * 4 + j)) * 10, 100 * k2, 'angry', 0, 0)
            ptext(cr, nm.upper() + '?', x, 1170, fit(cr, nm.upper() + '?', 40, 300), COL[nm], k2, fam='Poppins ExtraBold', sw=6)
    tc = w('cta', 'Comment') - 0.1
    if t >= tc: chip(cr, 'COMMENT YOUR PICK', 540, 1460, 46, WHITE, INK, pop_k(t, tc), 1)
    ts_ = w('cta', 'subscribe') - 0.1
    if t >= ts_: subscribe_button(cr, t, ts_, 540, 1640)

def render_frame(cr, t):
    global CUR_OPP
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    CUR_OPP = OPPS.get(round_of(t) or 0, 'India')
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
    boom(0.0, 1.0); rumble(0.0, 1.0, 0.25); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(w('h2', 'trophies') - 0.05, 0.8)
    whoosh(bt('h3')['start'] - 0.3, 0.3); te = w('h3', 'every') - 0.1
    for j in range(8): whoosh(te + j * 0.13 - 0.1, 0.12, 0.15); pop(te + j * 0.13 + 0.2, 0.1, 400 + 60 * j)
    boom(w('h3', 'you') + 0.05, 1.0); whoosh(bt('title')['start'] - 0.35)
    for wd in ('Eight', 'rounds', 'This', 'cricket'): boom(w('title', wd), 0.7)
    horn(w('title', 'cricket'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1); pop(tv + 0.55, 0.12, 500)
    for k, sp, _ in LINES:
        if sp and k[0] == 'r': whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
        if k in SHOTS:
            for s0, sh in shot_list(k)[1:]: whoosh(s0 - 0.2, 0.16, 0.22)
    boom(bt('e1')['start'], 0.9); rumble(bt('e1')['start'], 1.0, 0.2); boom(bt('cta')['start'], 0.9); horn(bt('cta')['start'], 0.1)
    for j in range(3): pop(w('cta', 'Who') + 0.6 + j * 0.25, 0.12, 900 + 200 * j)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_cricket'))
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

