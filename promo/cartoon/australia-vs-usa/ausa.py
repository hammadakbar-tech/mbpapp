# Countryballs: Australia vs USA, the Geography War (9:16, multi-voice, dialogue-driven).
# Usage: python3 ausa.py <data_dir> <out.mp4> [--preview t1,t2,...]
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

A_C, U_C = hexc('#FFC233')[:3], hexc('#4A86FF')[:3]
NARR = ('en-CA-LiamNeural', '+6%')
VOICE = {'Australia': ('en-AU-WilliamNeural', '+4%'), 'USA': ('en-US-EricNeural', '+4%'), 'New Zealand': ('en-NZ-MitchellNeural', '+6%')}
LINES = [
    ('h1', None, "Australia, or the USA: who would win?"),
    ('h2', None, "Plot twist: they are almost exactly the same size."),
    ('h3a', 'Australia', "G'day! I've got kangaroos!"), ('h3u', 'USA', "And I've got fifty states, buddy!"),
    ('title', None, "Eight rounds. One winner. This is the geography war."),
    ('c1', None, "Round one: size."),
    ('r1a', 'Australia', "Mainland USA? I'm almost exactly the same size, mate!"),
    ('r1b', 'USA', "Mainland, sure. Add Alaska, and I'm two million square kilometres bigger!"),
    ('c2', None, "Round two: beaches."),
    ('r2a', 'USA', "We have Miami, Malibu, and Hawaii!"),
    ('r2b', 'Australia', "Cute. I have over eleven thousand beaches. Visit one a day, and it takes thirty years!"),
    ('c3', None, "Round three: people."),
    ('r3a', 'Australia', "Twenty-eight million Aussies, mate!"),
    ('r3b', 'USA', "California alone has thirty-nine million. You'd fit in one of my states!"),
    ('c4', None, "Round four: deadly animals."),
    ('r4a', 'USA', "We've got bears, alligators, and rattlesnakes!"),
    ('r4b', 'Australia', "I've got the most venomous snake on Earth. Plus spiders, sharks, crocodiles, and jellyfish. Even my birds can kill you!"),
    ('c5', None, "Round five: the Olympics."),
    ('r5a', 'Australia', "We punch way above our weight at the Olympics!"),
    ('r5b', 'USA', "I've won over eleven hundred gold medals. More than anyone, ever!"),
    ('c6', None, "Round six: living longer."),
    ('r6a', 'USA', "We spend more on healthcare than anyone in the world!"),
    ('r6b', 'Australia', "And I still live about four years longer than you. No worries!"),
    ('c7', None, "Round seven: minimum wage."),
    ('r7a', 'USA', "Federal minimum wage: seven twenty-five an hour."),
    ('r7b', 'Australia', "Mine is twenty-six dollars forty. Australian dollars, but still: more than double yours!"),
    ('c8', None, "Final round: the GDP war."),
    ('r8a', 'Australia', "My economy is worth about two trillion dollars!"),
    ('r8b', 'USA', "Mine is over thirty trillion. That's more than fifteen of you!"),
    ('end', None, "Four all. It's a tie!"),
    ('e1', 'New Zealand', "Excuse me! I can settle this!"),
    ('e2', 'USA', "Who are you?"),
    ('e3', 'Australia', "That's New Zealand, mate. Don't worry about it."),
    ('cta', None, "Australia, or the USA? You break the tie: comment your pick!")]
SPK = {k: s for k, s, _ in LINES}
RD = {1: ('SIZE', 'U', ('r1b', 'bigger')), 2: ('BEACHES', 'A', ('r2b', 'thirty')), 3: ('PEOPLE', 'U', ('r3b', 'states')), 4: ('DEADLY ANIMALS', 'A', ('r4b', 'kill')),
      5: ('THE OLYMPICS', 'U', ('r5b', 'ever')), 6: ('LIVING LONGER', 'A', ('r6b', 'longer')), 7: ('MINIMUM WAGE', 'A', ('r7b', 'double')), 8: ('THE GDP WAR', 'U', ('r8b', 'fifteen'))}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2')
C.SAY = {None: {}}
C.HOT = ('australia', 'usa', 'win', 'twist', 'same', 'size', 'war', 'tie', 'comment', 'geography', 'winner')
C.TAIL_OVERRIDE = {'h1': 0.25, 'h2': 0.9, 'title': 0.6, 'end': 0.4, 'e3': 0.6, 'cta': 2.4, **{f'c{i}': 0.15 for i in range(1, 9)},
                   **{k: 0.3 for k, s, _ in LINES if s}, **{RD[i][2][0]: 0.9 for i in RD}, 'h3a': 0.2, 'h3u': 0.4}
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

class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        us = [r for r in rings(cf['United States of America']['geometry']) if len(r) > 3]
        l48 = [r for r in us if -126 < r[:, 0].mean() < -66 and 24 < r[:, 1].mean() < 50]
        ak = [r for r in us if r[:, 1].mean() > 50 and r[:, 0].mean() < -129]
        au = [r for r in rings(cf['Australia']['geometry']) if len(r) > 3 and r[:, 0].mean() > 110 and -45 < r[:, 1].mean() < -9]
        rc = lambda rs: (lambda x0, x1, y0, y1: [r - np.array([(x0 + x1) / 2, (y0 + y1) / 2]) for r in rs])(*bounds(rs))
        self.l48, self.ak, self.au = rc(local(l48, -98, 39)), rc(local(ak, -152, 62)), rc(local(au, 134, -26))
        print('areas M km2 (land, map data): l48', round(area(self.l48) / 1e6, 2), 'alaska', round(area(self.ak) / 1e6, 2), 'australia', round(area(self.au) / 1e6, 2))
        for n, c in (('Australia', 'au'), ('USA', 'us'), ('New Zealand', 'nz'), ('California', 'us-ca')):
            B.FL[n] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', c + '.png'))

def at(key, word): return w(key, word)
def side_of(name): return 'A' if name == 'Australia' else ('U' if name in ('USA', 'California') else 'M')
def col_of(name): return {'A': A_C, 'U': U_C}.get(side_of(name), (0.4, 0.85, 0.6))
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

def talk(cr, t, key, prop=None, mood='happy', rival_mood='angry'):
    """A countryball speaks: bubble on top, an illustration in the middle, the speaker below, the rival in the corner."""
    b = bt(key); name = SPK[key]; side = side_of(name); col = col_of(name); sgn = -1 if side == 'A' else 1
    tilt = 0.035 * (1 if sum(map(ord, key)) % 2 else -1)
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.07), tilt, 540, 980); arena(cr, t, col)
    if prop: prop(cr, t, b)
    rival = 'USA' if side == 'A' else 'Australia'
    ball(cr, rival, 540 - sgn * 365, 1440 - abs(math.sin(t * 4)) * 6, 92, rival_mood, 0, sgn * 0.8)
    h = hop_of(t, b); sx = 540 + sgn * 130
    ball(cr, name, sx, 1350 - h * 40, 175, mood, 0.05 * h, -sgn * 0.5)
    cr.restore()
    bubble(cr, t, b, sx); nametag(cr, name, sx, 1600, col)
    f = 1 - prog(t, b['start'], b['start'] + 0.12)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.5 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.18)))

# ---------- illustrations ----------
MS = 0.15
def overlay(cr, t, cx, cy, s, ka, alaska=0.0, labels=True):
    km_shape(cr, G.l48, cx, cy, s, U_C, 1, lw=2, edge=(0.03, 0.04, 0.1))
    if alaska > 0:
        k = ease_out(alaska); km_shape(cr, G.ak, cx, cy, s, U_C, 1, -2600 + (1 - k) * -2500, 950, lw=2, edge=(0.03, 0.04, 0.1))
    if ka > 0:
        k = ease_out(ka); cr.save(); cr.translate(0, (1 - k) * -900); km_shape(cr, G.au, cx, cy, s, A_C, 1, 150, -120, fill=0.78, lw=3, edge=INK); cr.restore()
def p_same(cr, t, b):
    ka = prog(t, at('r1a', 'same') - 0.5, at('r1a', 'same') + 0.1); overlay(cr, t, 560, 990, MS, ka)
    ptext(cr, 'MAINLAND USA ≈ 8.1M KM²', 540, 775, 38, U_C, 1, sw=7)
    if ka >= 1: ptext(cr, 'AUSTRALIA', 580, 990, 46, INK, pop_k(t, at('r1a', 'same') + 0.1), sw=0, shadow=False); ptext(cr, '≈ 7.7M KM²', 580, 1045, 40, INK, pop_k(t, at('r1a', 'same') + 0.1), sw=0, shadow=False)
def p_alaska(cr, t, b):
    kk = prog(t, at('r1b', 'Alaska') - 0.3, at('r1b', 'Alaska') + 0.4); overlay(cr, t, 600, 1010, 0.13, 1, kk)
    if kk > 0: ptext(cr, '+ ALASKA', 262, 1010, 44, WHITE, clamp(kk * 2), sw=7)
    tb = at('r1b', 'two') - 0.1
    if t >= tb: chip(cr, 'USA 9.8M  vs  AUS 7.7M KM²', 600, 765, 36, WHITE, INK, pop_k(t, tb), 1)
def p_usbeach(cr, t, b): emopops(cr, t, 'r2a', (('🏖️', 'Miami'), ('🏄', 'Malibu'), ('🌺', 'Hawaii')))
def p_beaches(cr, t, b):
    k = ease_out(prog(t, at('r2b', 'eleven') - 0.2, at('r2b', 'beaches') + 0.2))
    for j in range(int(30 * k)): emoji(cr, '🏖️', 170 + (j % 10) * 82, 780 + (j // 10) * 66, 56, 1)
    ptext(cr, f'{int(11000 * k):,}+ BEACHES', 540, 1040, 84, A_C, 1, sw=11)
    tv = at('r2b', 'Visit') - 0.1
    if t >= tv: chip(cr, 'ONE A DAY = 30 YEARS', 540, 1125, 38, WHITE, INK, pop_k(t, tv), 1)
def figs(cr, x0, y0, n, cols, col, dx=30, dy=42):
    for j in range(n):
        x, y = x0 + (j % cols) * dx, y0 + (j // cols) * dy
        cr.new_path(); cr.arc(x, y - 9, 7.5, 0, 2 * math.pi); cr.rectangle(x - 8, y - 1, 16, 20); cr.set_source_rgb(*col); cr.fill()
def p_aussies(cr, t, b):
    k = ease_out(prog(t, b['l0'] + 0.2, at('r3a', 'Aussies') + 0.3)); figs(cr, 330, 860, int(28 * k), 14, A_C, 30, 46)
    ptext(cr, f'{int(28 * k)} MILLION', 540, 1060, 84, A_C, 1, sw=11); ptext(cr, 'EACH FIGURE = 1 MILLION', 540, 1120, 28, WHITE, 0.8, fam='Poppins ExtraBold', sw=5)
def p_calif(cr, t, b):
    figs(cr, 120, 820, 28, 7, A_C, 30, 46); ptext(cr, 'AUSTRALIA 28M', 210, 1060, 36, A_C, 1, sw=6)
    tc = at('r3b', 'California') - 0.2
    if t >= tc:
        ball(cr, 'California', 760, 770, 70 * pop_k(t, tc, 0.3), 'happy')
        k = ease_out(prog(t, tc + 0.3, at('r3b', 'million') + 0.2)); figs(cr, 640, 880, int(39.5 * k), 10, U_C, 26, 40)
        ptext(cr, f'CALIFORNIA {39.5 * k:.1f}M', 790, 1090, 36, U_C, 1, sw=6)
def p_usanimals(cr, t, b): emopops(cr, t, 'r4a', (('🐻', 'bears'), ('🐊', 'alligators'), ('🐍', 'rattlesnakes')))
def p_ozanimals(cr, t, b):
    items = (('🐍', 'snake'), ('🕷️', 'spiders'), ('🦈', 'sharks'), ('🐊', 'crocodiles'), ('🪼', 'jellyfish'), ('🐦', 'birds'))
    for i, (em, word) in enumerate(items):
        tt = at('r4b', word) - 0.1
        if t < tt: continue
        x, y = 250 + (i % 3) * 290, 830 + (i // 3) * 190
        emoji(cr, em, x, y - abs(math.sin(t * 5 + i)) * 12, (190 if word == 'birds' else 140) * pop_k(t, tt, 0.3), 1, rot=0.12 * math.sin(t * 4 + i))
    ts = at('r4b', 'snake') - 0.1
    if t >= ts and t < at('r4b', 'spiders'): chip(cr, 'INLAND TAIPAN', 250, 950, 32, A_C, INK, pop_k(t, ts), 1)
    tb = at('r4b', 'birds')
    if t >= tb: chip(cr, 'CASSOWARY', 830, 1130, 32, WHITE, INK, pop_k(t, tb), 1)
def p_punch(cr, t, b): emopops(cr, t, 'r5a', (('🦘', 'punch'), ('🥊', 'weight'), ('🏊', 'Olympics')))
def p_golds(cr, t, b):
    ptext(cr, 'ALL-TIME SUMMER OLYMPIC GOLDS', 540, 770, 32, WHITE, 0.85, fam='Poppins ExtraBold', sw=6)
    bar(cr, 330, 1130, 185, 1110, 300, 1, A_C, 'AUSTRALIA', '~185')
    k = ease_out(prog(t, at('r5b', 'eleven') - 0.2, at('r5b', 'medals') + 0.2)); bar(cr, 750, 1130, 1110, 1110, 300, k, U_C, 'USA', f'{int(1110 * k):,}')
    tm = at('r5b', 'medals')
    for j in range(8):
        if t >= tm: ph = ((t - tm) * 0.7 + j / 8) % 1; emoji(cr, '🥇', 620 + j * 36, lerp(760, 1120, ph), 44, math.sin(math.pi * ph))
def p_health(cr, t, b):
    emopops(cr, t, 'r6a', (('🏥', 'spend'), ('💵', 'healthcare'), ('🌎', 'world')), y=900)
    tw_ = at('r6a', 'world')
    if t >= tw_: chip(cr, '#1 HEALTH SPENDING PER PERSON', 540, 1110, 34, WHITE, INK, pop_k(t, tw_), 1)
def p_life(cr, t, b):
    ptext(cr, 'LIFE EXPECTANCY (YEARS)', 540, 770, 34, WHITE, 0.85, fam='Poppins ExtraBold', sw=6)
    bar(cr, 330, 1130, 79.0 - 70, 14, 300, 1, U_C, 'USA', '79.0')
    k = ease_out(prog(t, at('r6b', 'four') - 0.2, at('r6b', 'longer') + 0.1)); bar(cr, 750, 1130, 83.2 - 70, 14, 300, k, A_C, 'AUSTRALIA', f'{lerp(79.0, 83.2, k):.1f}' if k > 0 else '')
    ptext(cr, 'BARS START AT 70', 540, 1180, 24, WHITE, 0.6, fam='Poppins ExtraBold', sw=4)
def p_wage_us(cr, t, b):
    ptext(cr, 'MINIMUM WAGE PER HOUR', 540, 770, 34, WHITE, 0.85, fam='Poppins ExtraBold', sw=6)
    k = ease_out(prog(t, at('r7a', 'seven') - 0.2, at('r7a', 'hour'))); bar(cr, 330, 1130, 7.25, 17, 300, k, U_C, 'USA', f'${7.25 * k:.2f}')
def p_wage_au(cr, t, b):
    ptext(cr, 'MINIMUM WAGE PER HOUR', 540, 770, 34, WHITE, 0.85, fam='Poppins ExtraBold', sw=6)
    bar(cr, 330, 1130, 7.25, 17, 300, 1, U_C, 'USA', '$7.25')
    k = ease_out(prog(t, at('r7b', 'twenty') - 0.2, at('r7b', 'forty') + 0.2)); bar(cr, 750, 1130, 16.5, 17, 300, k, A_C, 'AUSTRALIA', f'A${26.44 * k:.2f}')
    tx = at('r7b', 'double') - 0.1
    if t >= tx: chip(cr, 'MORE THAN 2× IN US$', 540, 1070, 34, WHITE, INK, pop_k(t, tx), 1)
def gdp_circle(cr, x, y, g, col, k, lab, a=0.92, size=50):
    r = 62 * math.sqrt(g / 2.0) * k
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    if lab: ptext(cr, lab, x, y + size * 0.35, size, INK, clamp(k), sw=0, shadow=False)
def p_gdp_au(cr, t, b):
    ptext(cr, 'CIRCLE SIZE = SIZE OF ECONOMY', 540, 770, 28, WHITE, 0.8, fam='Poppins ExtraBold', sw=5)
    k = ease_out(prog(t, at('r8a', 'economy') - 0.3, at('r8a', 'trillion'))); gdp_circle(cr, 540, 950, 2.0, A_C, 0.3 + 0.7 * k, f'${2.0 * k:.1f}T', size=40)
    ptext(cr, 'AUSTRALIA', 540, 1110, 36, A_C, 1, fam='Poppins ExtraBold', sw=6)
def p_gdp_us(cr, t, b):
    gdp_circle(cr, 880, 1060, 2.0, A_C, 1, '$2T', size=34); ptext(cr, 'AUSTRALIA', 880, 1150, 30, A_C, 1, fam='Poppins ExtraBold', sw=5)
    k = ease_out(prog(t, at('r8b', 'thirty') - 0.3, at('r8b', 'trillion') + 0.2)); gdp_circle(cr, 400, 950, 32.0, U_C, 0.2 + 0.8 * k, f'${32 * k:.0f}T', size=80)
    tf = at('r8b', 'fifteen') - 0.1
    if t >= tf: sx, sy = shake(t, tf, 12); cr.save(); cr.translate(sx, sy); slam(cr, '16×', 860, 860, 110, WHITE, t, tf); cr.restore()
PROP = {'r1a': p_same, 'r1b': p_alaska, 'r2a': p_usbeach, 'r2b': p_beaches, 'r3a': p_aussies, 'r3b': p_calif, 'r4a': p_usanimals, 'r4b': p_ozanimals,
        'r5a': p_punch, 'r5b': p_golds, 'r6a': p_health, 'r6b': p_life, 'r7a': p_wage_us, 'r7b': p_wage_au, 'r8a': p_gdp_au, 'r8b': p_gdp_us}

# ---------- hook ----------
def draw_hook(cr, t):
    if t >= bt('h3a')['start']: return False
    b1, b2 = bt('h1'), bt('h2')
    if t < b2['start']:
        ti = 0.3; e = ease_out(prog(t, 0, ti)); sx, sy = shake(t, ti, 30, 0.6)
        cr.save(); cam(cr, push(t, 0, b2['start'], 1.0, 1.16), 0.05 * math.sin(t * 1.3), 540 + sx, 1000 + sy); arena(cr, t)
        rec = 26 * math.sin(math.pi * clamp((t - ti) / 0.35)) if t > ti else 0
        for n, x0, x1, sg, ph in (('Australia', 20, 318, -1, 0), ('USA', 1060, 762, 1, 1.3)):
            ball(cr, n, lerp(x0, x1, e) + sg * rec, 1040 - abs(math.sin(t * 8 + ph)) * 22 * (t > ti + 0.3), 215, 'angry', 0.12 * (rec / 26), -sg * 0.8)
        if t >= ti: emoji(cr, '⚡', 540, 1010, 210 * pop_k(t, ti, 0.25), 1, rot=0.2 * math.sin(t * 14))
        cr.restore()
        g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.8); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 760); cr.set_source(g); cr.fill()
        slam(cr, 'AUSTRALIA', 540, 300, 150, A_C, t, -0.3)
        if t >= w('h1', 'or') - 0.1: ptext(cr, 'OR', 540, 420, 70, WHITE, pop_k(t, w('h1', 'or') - 0.1), sw=9)
        slam(cr, 'THE USA?', 540, 600, 170, U_C, t, w('h1', 'USA') - 0.15, rot=0.03)
        tq = w('h1', 'who') - 0.1
        if t >= tq: qx, qy = shake(t, tq, 14); cr.save(); cr.translate(qx, qy); slam(cr, 'WHO WOULD WIN?', 540, 1500, 124, GOLD, t, tq); cr.restore()
        f = 1 - prog(t, ti, ti + 0.15)
        if ti <= t and f > 0: cr.set_source_rgba(1, 1, 1, 0.75 * f); cr.paint()
        return True
    ts = w('h2', 'same') - 0.6; ka = prog(t, ts, ts + 0.55); sx, sy = shake(t, ts + 0.55, 26, 0.6)
    cr.save(); cam(cr, push(t, b2['start'], b2['end'], 1.25, 1.02), 0.03 - 0.05 * prog(t, b2['start'], b2['end']), 540 + sx, 1000 + sy); ocean(cr, t)
    overlay(cr, t, 560, 1000, 0.17, ka); cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 600); cr.set_source(g); cr.fill()
    slam(cr, 'PLOT TWIST', 540, 280, 140, CRIMSON, t, b2['start'])
    if t >= ts + 0.55: slam(cr, 'SAME SIZE?!', 540, 440, 120, GOLD, t, ts + 0.55, rot=0.03)
    if t >= ts + 0.8:
        chip(cr, 'MAINLAND USA 8.1M KM²', 540, 1430, 46, U_C, INK, pop_k(t, ts + 0.8), 1); chip(cr, 'AUSTRALIA 7.7M KM²', 540, 1540, 46, A_C, INK, pop_k(t, ts + 1.0), 1)
    streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.22)))
    f = 1 - prog(t, ts + 0.55, ts + 0.75)
    if t >= ts + 0.55 and f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
    return True

def close_up(cr, t, key):
    b = bt(key); name = SPK[key]; col = col_of(name); sgn = -1 if side_of(name) == 'A' else 1; h = hop_of(t, b)
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.12), 0.06 * sgn, 540, 1000); arena(cr, t, col)
    ball(cr, name, 540, 1120 - h * 50, 300 * pop_k(t, b['start'], 0.25), 'happy', 0.05 * h, -sgn * 0.6)
    em = '🦘' if name == 'Australia' else '🦅'
    for j in range(6):
        ph = ((t - b['start']) * 0.6 + j / 6) % 1; emoji(cr, em, 140 + j * 160, lerp(1700, 700, ph), 90, math.sin(math.pi * ph))
    cr.restore()
    bubble(cr, t, b, 540, 560, 64); nametag(cr, name, 540, 1560, col)
    f = 1 - prog(t, b['start'], b['start'] + 0.12)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.55 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.18)))

def draw_title(cr, t):
    b = bt('title')
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.5))
    ball(cr, 'Australia', lerp(-200, 290, e), 1440 - abs(math.sin(t * 6)) * 14, 190, 'angry', 0, 0.8); ball(cr, 'USA', lerp(1280, 790, e), 1440 - abs(math.sin(t * 6 + 1)) * 14, 190, 'angry', 0, -0.8)
    cr.restore()
    slam(cr, 'AUSTRALIA', 540, 560, 160, A_C, t, w('title', 'Eight'))
    tv = w('title', 'One')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 740); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 38, 110, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'USA', 540, 980, 200, U_C, t, w('title', 'winner'))
    tg = w('title', 'geography')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE GEOGRAPHY WAR', 540, 1170, 92, WHITE, t, tg); cr.restore()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22)))

# ---------- scoreboard, cards, verdicts ----------
def tv_of(i): return w(*RD[i][2])
def score_at(t): return sum(t >= tv_of(i) and RD[i][1] == 'A' for i in RD), sum(t >= tv_of(i) and RD[i][1] == 'U' for i in RD)
def round_of(t):
    for i in RD:
        nxt = bt(f'c{i + 1}')['start'] if i < 8 else bt('end')['start']
        if bt(f'c{i}')['start'] <= t < nxt: return i
    return None
def hud(cr, t):
    a = ease_out(prog(t, bt('title')['end'] - 0.4, bt('title')['end']))
    if a <= 0: return
    sn, ss = score_at(t); rrect(cr, 30, 140, 1020, 190, 44); cr.set_source_rgba(0.03, 0.04, 0.1, 0.88 * a); cr.fill()
    for side, x, col, sc, lab in (('A', 250, A_C, sn, 'AUSTRALIA'), ('U', 830, U_C, ss, 'USA')):
        ptext(cr, lab, x, 200, 40, col, a, sw=0, shadow=False)
        last = max([tv_of(i) for i in RD if RD[i][1] == side and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); ptext(cr, f'ROUND {i}/8' if i else ('FINAL' if t >= bt('end')['start'] else 'VS'), 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)
ICON = {1: '📏', 2: '🏖️', 3: '👥', 4: '🐍', 5: '🏅', 6: '❤️', 7: '💵', 8: '📈'}
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2))
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((A_C, U_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, 'FINAL ROUND' if i == 8 else f'ROUND {i}', 0, 0, 120 if i == 8 else 150, CRIMSON if i == 8 else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = b['l0'] + 0.5
    if t >= tt:
        kk = pop_k(t, tt, 0.25); ttl = RD[i][0]; cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
        emoji(cr, ICON[i], 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = A_C if win == 'A' else U_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'A' else 1380, 540, ease_out(k)); txt = ('AUSTRALIA' if win == 'A' else 'USA') + ' WINS'
    cr.save(); cr.translate(x, 1490); cr.rotate(-0.05 if win == 'A' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 72)
    rrect(cr, -wd / 2 - 44, -84, wd + 88, 120, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, 72, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- ending ----------
def draw_end(cr, t):
    b, e1, e2, e3, c = bt('end'), bt('e1'), bt('e2'), bt('e3'), bt('cta')
    if t < e1['start']:
        cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.08), 0.02, 540, 1000); arena(cr, t)
        ball(cr, 'Australia', 290, 1430, 170, 'neutral', 0, 0.8); ball(cr, 'USA', 790, 1430, 170, 'neutral', 0, -0.8); cr.restore()
        ptext(cr, '4', 300, 900, 380, A_C, 1, sw=26); ptext(cr, '4', 780, 900, 380, U_C, 1, sw=26); ptext(cr, '—', 540, 850, 160, WHITE, 1, sw=14)
        td = w('end', 'tie')
        if t >= td: sx, sy = shake(t, td, 18); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A TIE!", 540, 1140, 150, GOLD, t, td); cr.restore()
        C.draw_captions(cr, t, 1700); return
    sx, sy = shake(t, e1['start'] + 0.4, 18, 0.5)
    cr.save(); cam(cr, push(t, e1['start'], c['end'], 1.0, 1.08), 0.02, 540 + sx, 1000 + sy); arena(cr, t)
    key = 'e1' if t < e2['start'] else ('e2' if t < e3['start'] else ('e3' if t < c['start'] else None))
    ha = hop_of(t, e3) if key == 'e3' else 0; hu = hop_of(t, e2) if key == 'e2' else 0; hn = hop_of(t, e1) if key == 'e1' else 0
    ball(cr, 'Australia', 270, 1150 - ha * 30, 165, 'happy' if key in ('e3', None) else 'shock', 0, 0.6)
    ball(cr, 'USA', 810, 1150 - hu * 30, 165, 'shock' if key in ('e1', 'e2') else 'happy', 0, -0.6)
    drop = lerp(-1200, 0, ease_out(prog(t, e1['start'], e1['start'] + 0.4)))
    ball(cr, 'New Zealand', 540, 1400 + drop - hn * 30, 95, 'happy' if key == 'e1' else 'sad', 0, 0)
    cr.restore()
    if key:
        nm = SPK[key]; bubble(cr, t, bt(key), {'e1': 540, 'e2': 810, 'e3': 270}[key], 560)
        nametag(cr, nm, {'e1': 540, 'e2': 810, 'e3': 270}[key], 1640 if key == 'e1' else 1360, col_of(nm))
    else:
        for x, col, word, lab, rot in ((290, A_C, 'Australia', 'AUSTRALIA', -0.04), (800, U_C, 'USA', 'USA', 0.04)):
            tt = w('cta', word)
            if t < tt: continue
            kk = pop_k(t, tt) * (1 + 0.03 * math.sin(t * 6 + x)); cr.save(); cr.translate(x, 650); cr.rotate(rot); cr.scale(kk, kk); ptext(cr, lab, 0, 0, 100 if lab == 'AUSTRALIA' else 140, col, 1, sw=12); cr.restore()
        tc = w('cta', 'comment')
        if t >= tc: kk = pop_k(t, tc); cr.save(); cr.translate(540, 450); cr.scale(kk, kk); ptext(cr, 'COMMENT YOUR PICK', 0, 0, 82, WHITE, 1, sw=11); cr.restore()
        tb = w('cta', 'break')
        if t >= tb:
            kk = pop_k(t, tb) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1640); cr.scale(kk, kk); txt = 'YOU BREAK THE TIE'; wd = tw(cr, txt, 56)
            rrect(cr, -wd / 2 - 50, -70, wd + 100, 110, 55); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill(); ptext(cr, txt, 0, 4, 56, WHITE, 1, sw=0, shadow=False); cr.restore()

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if draw_hook(cr, t): C.draw_captions(cr, t, 1700); return
    if key in ('h3a', 'h3u'): close_up(cr, t, key); return
    if key == 'title': draw_title(cr, t); return
    if key in ('end', 'e1', 'e2', 'e3', 'cta'): draw_end(cr, t); hud(cr, t)
    elif key[0] == 'c': card(cr, t, int(key[1])); hud(cr, t)
    else:
        i = int(key[1]); talk(cr, t, key, PROP.get(key), rival_mood='shock' if t >= tv_of(i) and RD[i][2][0] == key else 'angry')
        verdict(cr, t, i); hud(cr, t)
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
    boom(0.3, 1.0); boom(w('h1', 'USA') - 0.15, 0.7); boom(w('h1', 'who') - 0.1, 0.8)
    boom(bt('h2')['start'], 0.8); tsm = w('h2', 'same') - 0.05; whoosh(tsm - 0.55, 0.3, 0.5); boom(tsm, 1.0); rumble(tsm, 1.0, 0.2)
    for k in ('h3a', 'h3u', 'title'): whoosh(bt(k)['start'] - 0.35)
    for wd in ('Eight', 'winner', 'geography'): boom(w('title', wd), 0.7)
    horn(w('title', 'geography'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1)
    for k, sp, _ in LINES:
        if sp: whoosh(bt(k)['start'] - 0.25, 0.18, 0.25); pop(bt(k)['l0'] - 0.08, 0.1, 700)
    boom(w('end', 'tie'), 1.0); horn(w('end', 'tie'), 0.1)
    e1 = bt('e1'); whoosh(e1['start'] - 0.3, 0.3, 0.45); boom(e1['start'] + 0.4, 0.9); pop(bt('e2')['start'], 0.12, 500); cheer(bt('e3')['l1'], 0.08)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_ausa'))
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
