# GeoBall Wars: The Worst Alliance, Part 01. Australia recruits the weakest militaries for Emu War II (9:16, 4+ min long-form).
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

AU_C = hexc('#FFC233')[:3]
A_C, U_C = AU_C, hexc('#4F8CFF')[:3]
NARR = ('en-US-GuyNeural', '+6%')
RECRUITS = [  # name, flag, voice, colour, landmark, geo name, map centre, map scale
    ('Mongolia', 'mn', ('mn-MN-BataaNeural', '+4%'), '#E8333F', '🐎', 'Mongolia', (103.0, 46.8), 0.32),
    ('Bolivia', 'bo', ('es-BO-MarceloNeural', '+4%'), '#2DBE6C', '🦙', 'Bolivia', (-64.5, -16.5), 0.33),
    ('Liechtenstein', 'li', ('de-AT-JonasNeural', '+4%'), '#4F8CFF', '🏰', 'Liechtenstein', (9.55, 47.15), 9.0),
    ('Vatican', 'va', ('it-IT-DiegoNeural', '-4%'), '#FFD23F', '⛪', 'Vatican', (12.453, 41.903), 900.0),
    ('Andorra', 'ad', ('ca-ES-EnricNeural', '+4%'), '#4F8CFF', '⛷️', 'Andorra', (1.55, 42.55), 12.0),
    ('Iceland', 'is', ('is-IS-GunnarNeural', '+4%'), '#4F8CFF', '🌋', 'Iceland', (-18.6, 64.9), 1.1),
    ('San Marino', 'sm', ('it-IT-DiegoNeural', '+6%'), '#9CCBFF', '🏹', 'San Marino', (12.46, 43.94), 40.0),
    ('Costa Rica', 'cr', ('es-CR-JuanNeural', '+4%'), '#2DBE6C', '🦥', 'Costa Rica', (-84.2, 9.9), 1.9),
    ('Nauru', 'nr', ('en-NZ-MitchellNeural', '+4%'), '#4F8CFF', '🏝️', 'Nauru', (166.93, -0.53), 60.0),
    ('Switzerland', 'ch', ('de-CH-JanNeural', '+4%'), '#E8333F', '🏔️', 'Switzerland', (8.2, 46.8), 1.6)]
NRC = len(RECRUITS)
RNAME = {i + 1: r[0] for i, r in enumerate(RECRUITS)}
COL = {'Australia': AU_C, 'USA': hexc('#4F8CFF')[:3], 'UK': hexc('#E8333F')[:3], 'France': hexc('#4F8CFF')[:3], **{r[0]: hexc(r[3])[:3] for r in RECRUITS}}
VOICE = {'Australia': ('en-AU-WilliamNeural', '+6%'), **{r[0]: r[2] for r in RECRUITS}}
POWER = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 4, 7: 4, 8: 4, 9: 5, 10: 5}
STAMP = {1: 'ACCEPTED', 2: 'ACCEPTED?', 3: 'ACCEPTED', 4: 'ACCEPTED (BLESSED)', 5: 'ACCEPTED (ALONE)', 6: 'HIRED!', 7: 'ACCEPTED (PARADES)', 8: 'ACCEPTED…?', 9: 'ALREADY OURS', 10: 'SNACKS ONLY'}
NUMW = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
A = 'Australia'
# (key, speaker, text, visual)
SCRIPT = [
    ('h1', A, "Emergency! The emus are back!", 'panic'),
    ('h2', None, "In nineteen thirty-two, Australia sent soldiers with two machine guns to fight twenty thousand emus.", 'sc:emuwar'),
    ('h3', None, "After about a month, the soldiers pulled out. The emus won.", 'sc:emuwin'),
    ('h4', A, "The emus were very fast, okay?! This time, I'm building an alliance!", 'low'),
    ('h5', None, "There's just one problem. Nobody strong wants to join. This is: the worst alliance.", 'sc:declined'),
    ('r1n', None, 'Recruit number one: Mongolia.', 'card'),
    ('r1a', A, "Mongolia! You've got the toughest horsemen on Earth. Join me!", 'two'),
    ('r1b', 'Mongolia', 'Even better. I have a navy!', 'close'),
    ('r1c', A, "A navy? You're landlocked!", 'sc:landlocked'),
    ('r1d', 'Mongolia', 'One tugboat. Seven sailors. On a lake.', 'sc:tug'),
    ('r1e', A, '…Welcome aboard.', 'stamp'),
    ('r1p', None, 'Alliance power: one percent.', 'power'),
    ('r2n', None, 'Recruit number two: Bolivia.', 'card'),
    ('r2a', 'Bolivia', 'I heard you need a navy. I have five thousand sailors!', 'sc:bonavy'),
    ('r2b', A, "Now we're talking! Where's your sea?", 'sc:landlocked'),
    ('r2c', 'Bolivia', 'I lost it. In a war, back in the eighteen hundreds.', 'close'),
    ('r2d', 'Bolivia', 'But every year, I still celebrate the Day of the Sea!', 'sc:seaday'),
    ('r2e', A, "…We'll practise on a lake.", 'stamp'),
    ('r2p', None, 'Alliance power: two percent.', 'power'),
    ('r3n', None, 'Recruit number three: Liechtenstein.', 'card'),
    ('r3a', A, 'Liechtenstein! How big is your army?', 'two'),
    ('r3b', 'Liechtenstein', "I don't have one. I got rid of it in eighteen sixty-eight.", 'sc:limap'),
    ('r3c', 'Liechtenstein', 'But in my last war, I sent eighty soldiers… and eighty-one came back!', 'sc:eightyone'),
    ('r3d', A, 'Wait… how?!', 'react'),
    ('r3e', 'Liechtenstein', 'We made a friend.', 'stamp'),
    ('r3p', None, 'Alliance power: two percent.', 'power'),
    ('r4n', None, 'Recruit number four: Vatican City, the smallest country on Earth.', 'card'),
    ('r4a', 'Vatican', 'My army is the Swiss Guard. About one hundred and thirty-five of them.', 'sc:guards'),
    ('r4b', A, "Swiss? Aren't you in Italy?", 'ots'),
    ('r4c', 'Vatican', "They're Swiss. They've guarded the Pope for over five hundred years.", 'sc:since1506'),
    ('r4d', A, 'Do they have tanks?', 'two'),
    ('r4e', 'Vatican', 'They have halberds.', 'close'),
    ('r4f', A, '…Perfect for emus.', 'stamp'),
    ('r4p', None, 'Alliance power: three percent.', 'power'),
    ('r5n', None, 'Recruit number five: Andorra.', 'card'),
    ('r5a', 'Andorra', "I don't have an army either.", 'close'),
    ('r5b', A, 'Then who protects you?', 'ots'),
    ('r5c', 'Andorra', 'France and Spain. By treaty.', 'sc:admap'),
    ('r5d', A, 'Great! Can you bring them along?', 'two'),
    ('r5e', 'Andorra', 'They said no.', 'stamp'),
    ('r5p', None, 'Alliance power: three percent.', 'power'),
    ('r6n', None, 'Recruit number six: Iceland.', 'card'),
    ('r6a', 'Iceland', 'I have no army at all.', 'close'),
    ('r6b', A, 'Then why are you here?', 'ots'),
    ('r6c', 'Iceland', 'Because I beat the U.K. Three times. In the Cod Wars.', 'sc:codwars'),
    ('r6d', 'Iceland', 'With fishing boats and net cutters.', 'sc:netcut'),
    ('r6e', A, "…You're hired!", 'stamp'),
    ('r6p', None, 'Alliance power: four percent.', 'power'),
    ('r7n', None, 'Recruit number seven: San Marino, one of the oldest republics on Earth.', 'card'),
    ('r7a', 'San Marino', 'I have an army! With a crossbow corps!', 'sc:crossbow'),
    ('r7b', A, 'Crossbows? Against emus?', 'two'),
    ('r7c', 'San Marino', "They're very good at parades.", 'close'),
    ('r7d', A, '…Good enough.', 'stamp'),
    ('r7p', None, 'Alliance power: four percent.', 'power'),
    ('r8n', None, 'Recruit number eight: Costa Rica.', 'card'),
    ('r8a', 'Costa Rica', 'Pura vida! I abolished my army in nineteen forty-eight.', 'sc:crmap'),
    ('r8b', A, 'So what do you bring to the fight?', 'two'),
    ('r8c', 'Costa Rica', 'Sloths!', 'sc:sloth'),
    ('r8d', A, 'Sloths are slower than emus, mate!', 'sc:speed'),
    ('r8e', 'Costa Rica', 'Pura vida.', 'stamp'),
    ('r8p', None, 'Alliance power: four percent.', 'power'),
    ('r9n', None, 'Recruit number nine: Nauru.', 'card'),
    ('r9a', 'Nauru', "G'day! I'm one of the smallest countries on Earth. No army.", 'sc:nrmap'),
    ('r9b', A, 'Then who defends you?', 'ots'),
    ('r9c', 'Nauru', 'You do, Australia.', 'close'),
    ('r9d', A, '…Right. Welcome aboard, I guess.', 'stamp'),
    ('r9p', None, 'Alliance power: five percent.', 'power'),
    ('r10n', None, 'Final recruit: Switzerland.', 'card'),
    ('r10a', A, "Switzerland! You've got mountains, knives, and the Swiss Guard!", 'two'),
    ('r10b', 'Switzerland', 'I am neutral.', 'sc:neutral'),
    ('r10c', A, 'Come on! Just this once?', 'close'),
    ('r10d', 'Switzerland', 'I have not fought a foreign war since eighteen fifteen. I will not start with emus.', 'low'),
    ('r10e', A, '…Fine. You can hold the snacks.', 'stamp'),
    ('r10p', None, 'Alliance power: five percent. Emu power: one hundred percent.', 'power'),
    ('f1', None, "The worst alliance is ready.", 'sc:lineup'),
    ('f1b', A, "Alright team! Sound off!", 'cry'),
    ('f1c', 'Mongolia', "Navy ready! Well… the tugboat.", 'cry'),
    ('f1d', 'Vatican', "The Swiss Guard is ready. With halberds.", 'cry'),
    ('f1e', 'Iceland', "Net cutters ready!", 'cry'),
    ('f1f', 'San Marino', "Crossbows polished for the parade!", 'cry'),
    ('f1g', 'Costa Rica', "Pura vida.", 'cry'),
    ('f1h', 'Switzerland', "I brought the snacks.", 'cry'),
    ('f2', A, "Alright! Emus, prepare to—", 'sc:lineup'),
    ('f3', 'Mongolia', "Uh… Australia?", 'sc:stampede'),
    ('f4', A, "…Oh no.", 'sc:stampede'),
    ('cta', None, "Will the worst alliance survive? Find out in part two. Which country should join next? Comment below, and subscribe!", 'end')]
LINES = [(k, s, t) for k, s, t, _ in SCRIPT]
VIS = {k: v for k, _, _, v in SCRIPT}
SPK = {k: s for k, s, _ in LINES}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3', 'h4', 'h5')
C.SAY = {None: {'Liechtenstein': 'Lick-ten-stine', 'halberds': 'hal-berds', 'Nauru': 'Na-oo-roo'}}
C.HOT = ('emus', 'emu', 'alliance', 'worst', 'navy', 'tugboat', 'landlocked', 'sloths', 'neutral', 'won', 'comment', 'subscribe', 'eighty-one', 'halberds')
C.TAIL_OVERRIDE = {**{k: 0.3 for k, s, _ in LINES}, 'h2': 0.4, 'h3': 0.9, 'h5': 1.2, **{f'r{i}n': 0.5 for i in range(1, NRC + 1)}, **{f'r{i}p': 0.5 for i in range(1, NRC + 1)}, **{k: 1.4 for k, _, _, v in SCRIPT if v == 'stamp'}, 'f1': 0.8, 'f3': 0.4, 'f4': 1.2, 'cta': 3.8}
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
        specs = [('AU', 'Australia', (134.0, -26.0), 30)] + [(r[1].upper(), r[5], r[6], max(1.5, 1100 / r[7] / 111 * 1.6)) for r in RECRUITS if r[5] in cf]
        self.ref, self.c, self.nb, self.off = {}, {}, {}, {}
        for k, n, ref, win in specs:
            rs = R(n)
            if k == 'AU': rs = [r for r in rs if 112 < r[:, 0].mean() < 155 and -45 < r[:, 1].mean() < -9]
            self.ref[k] = ref; pr = local(rs, *ref); x0, x1, y0, y1 = bounds(pr); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); self.off[k] = off
            self.c[k] = [r - off for r in pr]
            nbs = []
            for nn, f in cf.items():
                if nn == n: continue
                for r in R(nn):
                    if abs(r[:, 0].mean() - ref[0]) < win * 1.6 and abs(r[:, 1].mean() - ref[1]) < win: nbs.append(r)
            self.nb[k] = [r - off for r in local(nbs, *ref)] if nbs else []
        for nm, f in [('Australia', 'au'), ('USA', 'us'), ('UK', 'gb'), ('France', 'fr')] + [(r[0], r[1]) for r in RECRUITS]: B.FL[nm] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', f + '.png'))
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]

def at(key, word, n=0): return w(key, word, n)
def ri_of(key):
    if key[0] != 'r' or not key[1].isdigit(): return 0
    j = 1
    while key[j].isdigit(): j += 1
    return int(key[1:j])
CUR = [1]
def col_of(name): return COL.get(name, WHITE)
def rival_of(name): return RNAME[CUR[0]] if name == A else A
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
# ---------- emus ----------
def emu(cr, x, y, s, ph, flip=1, a=1.0):
    cr.save(); cr.translate(x, y); cr.scale(s * flip, s)
    for leg in (0, 1):
        sw = math.sin(ph * 2 * math.pi + leg * math.pi) * 0.6
        cr.move_to(-8 + leg * 14, 20); cr.line_to(-8 + leg * 14 + 30 * math.sin(sw), 90); cr.set_source_rgba(0.35, 0.28, 0.22, a); cr.set_line_width(7); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
    cr.save(); cr.scale(1.25, 0.85); cr.new_path(); cr.arc(0, 0, 45, 0, 2 * math.pi); cr.restore(); cr.set_source_rgba(0.42, 0.36, 0.3, a); cr.fill()
    for j in range(7): cr.new_path(); cr.arc(-30 + j * 10, -10 + 18 * math.sin(j * 1.7), 9, 0, 2 * math.pi); cr.set_source_rgba(0.32, 0.26, 0.21, a); cr.fill()
    cr.move_to(35, -15); cr.curve_to(55, -50, 50, -80, 62, -100); cr.set_source_rgba(0.45, 0.5, 0.65, a); cr.set_line_width(13); cr.stroke()
    cr.new_path(); cr.arc(66, -106, 12, 0, 2 * math.pi); cr.set_source_rgba(0.3, 0.3, 0.4, a); cr.fill()
    cr.move_to(76, -106); cr.line_to(94, -101); cr.line_to(76, -98); cr.close_path(); cr.set_source_rgba(0.2, 0.18, 0.15, a); cr.fill()
    cr.new_path(); cr.arc(70, -110, 3.5, 0, 2 * math.pi); cr.set_source_rgba(0.95, 0.5, 0.1, a); cr.fill()
    cr.restore()
def emu_herd(cr, t, n, y0, y1, speed, seed, s=0.8, a=1.0):
    rng = np.random.default_rng(seed)
    for j in range(n):
        x = (rng.uniform(-300, 1400) + t * speed * rng.uniform(0.8, 1.2)) % 1700 - 300; y = rng.uniform(y0, y1)
        emu(cr, x, y, s * (0.6 + 0.6 * (y - y0) / max(1, y1 - y0)), t * 2.5 + j * 0.37, 1, a)

# ---------- sets ----------
def set_generic(cr, t, name):
    col = col_of(name); lm = next(r[4] for r in RECRUITS if r[0] == name)
    sky = {'Mongolia': ((0.4, 0.65, 0.95), (0.85, 0.92, 1.0), (0.55, 0.65, 0.3)), 'Bolivia': ((0.3, 0.5, 0.9), (0.8, 0.88, 0.98), (0.92, 0.92, 0.95)),
           'Liechtenstein': ((0.35, 0.6, 0.95), (0.85, 0.93, 1.0), (0.35, 0.6, 0.3)), 'Vatican': ((0.95, 0.65, 0.4), (1.0, 0.88, 0.7), (0.75, 0.68, 0.6)),
           'Iceland': ((0.05, 0.1, 0.25), (0.3, 0.4, 0.55), (0.3, 0.32, 0.35)), 'Costa Rica': ((0.3, 0.7, 0.95), (0.85, 0.95, 0.9), (0.2, 0.55, 0.25)),
           'Switzerland': ((0.3, 0.55, 0.95), (0.85, 0.92, 1.0), (0.35, 0.6, 0.3)), 'Andorra': ((0.35, 0.6, 0.95), (0.88, 0.93, 1.0), (0.4, 0.55, 0.35)),
           'San Marino': ((0.95, 0.7, 0.45), (1.0, 0.9, 0.75), (0.6, 0.6, 0.55)), 'Nauru': ((0.2, 0.65, 0.95), (0.8, 0.95, 1.0), (0.95, 0.88, 0.7))}[name]
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *sky[0]); g.add_color_stop_rgb(0.6, *sky[1]); g.add_color_stop_rgb(1, *sky[2]); cr.set_source(g); cr.paint()
    if name == 'Iceland':
        for j in range(3):
            cr.new_path(); cr.move_to(-50, 380 + j * 90)
            for x in range(0, 1200, 60): cr.line_to(x, 380 + j * 90 + 70 * math.sin(x / 170 + t * 0.8 + j))
            cr.set_source_rgba(0.3, 1, 0.6, 0.25 - j * 0.06); cr.set_line_width(60 - j * 12); cr.stroke()
    mcol = (0.95, 0.97, 1.0) if name in ('Switzerland', 'Liechtenstein', 'Iceland', 'Bolivia', 'Andorra') else (0.5, 0.55, 0.6)
    for j, (x, hh) in enumerate(((150, 520), (480, 640), (820, 560), (1050, 470))):
        cr.new_path(); cr.move_to(x - 330, 1320); cr.line_to(x, 1320 - hh); cr.line_to(x + 330, 1320); cr.close_path(); cr.set_source_rgb(*[c * 0.75 for c in sky[2]]) if name not in ('Switzerland', 'Liechtenstein', 'Bolivia') else cr.set_source_rgb(0.45, 0.5, 0.6); cr.fill()
        cr.new_path(); cr.move_to(x - 90, 1320 - hh * 0.72); cr.line_to(x, 1320 - hh); cr.line_to(x + 90, 1320 - hh * 0.72); cr.close_path(); cr.set_source_rgb(*mcol); cr.fill()
    if name == 'Vatican':
        cr.new_path(); cr.arc(540, 1000, 230, math.pi, 0); cr.set_source_rgb(0.85, 0.78, 0.65); cr.fill(); cr.rectangle(280, 1000, 520, 330); cr.fill()
        for j in range(8): cr.rectangle(300 + j * 64, 1050, 26, 270); cr.set_source_rgb(0.95, 0.9, 0.8); cr.fill()
        cr.rectangle(530, 720, 20, 80); cr.set_source_rgb(0.85, 0.78, 0.65); cr.fill()
    if name == 'Mongolia':  # yurt
        cr.new_path(); cr.arc(820, 1300, 150, math.pi, 0); cr.set_source_rgb(0.97, 0.95, 0.9); cr.fill(); cr.new_path(); cr.move_to(660, 1200); cr.line_to(820, 1100); cr.line_to(980, 1200); cr.close_path(); cr.set_source_rgb(0.9, 0.3, 0.25); cr.fill()
        cr.rectangle(790, 1210, 60, 90); cr.set_source_rgb(0.85, 0.25, 0.2); cr.fill()
    cr.rectangle(-200, 1310, 1500, 800); cr.set_source_rgb(*sky[2]); cr.fill()
    emoji(cr, lm, 180, 1200 + 8 * math.sin(t * 2), 160, 1, rot=0.05 * math.sin(t))
def set_of(name, cr, t): set_australia(cr, t) if name == A else set_generic(cr, t, name)

# ---------- shots ----------
def sgn_of(name): return -1 if name == A else 1
def sh_close(cr, t, b, name, t0, t1, mood='happy'):
    sgn = sgn_of(name); h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.06 * sgn, 540, 1100); set_of(name, cr, t); ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1, mood='happy'):
    h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, mood, 0.04 * h, 0); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_ots(cr, t, b, name, t0, t1, mood='happy'):
    sgn = sgn_of(name); h = hop_of(t, b); rv = rival_of(name)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.06), 0.02 * sgn, 540 + lerp(0, -sgn * 40, prog(t, t0, t1)), 1000); set_of(name, cr, t)
    ball(cr, name, 540 + sgn * 150, 1080 - h * 36, 210, mood, 0.05 * h, -sgn * 0.6); ball(cr, rv, 540 - sgn * 470, 1700, 560, 'happy', 0, sgn * 0.9); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.paint(); bubble(cr, t, b, 540 + sgn * 150, 520); nametag(cr, name, 540 + sgn * 150, 1340, col_of(name))
def sh_two(cr, t, b, name, t0, t1, mood='happy'):
    h = hop_of(t, b); rv = RNAME[CUR[0]]; pan = lerp(-50, 50, prog(t, t0, t1)) * sgn_of(name)
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    for n, x in ((A, 290), (rv, 790)):
        hh = h if n == name else 0; ball(cr, n, x, 1300 - hh * 40, 220, mood if n == name else 'happy', 0.05 * hh, 0.8 if n == A else -0.8)
    cr.restore(); sx = (290 if name == A else 790) - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1600, col_of(name))
def sh_react(cr, t, b, name, t0, t1):
    k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.3, 1.1, k), -0.06, 540 + sx, 1080 + sy); set_of(name, cr, t); ball(cr, name, 540, 1150, 380, 'shock', 0, 0); cr.restore()
    bubble(cr, t, b, 540, 540); ptext(cr, '?!', 860, 820, 170, GOLD, pop_k(t, t0 + 0.05), sw=14); nametag(cr, name, 540, 1640, col_of(name))
def corner(cr, t, b, name, cy=1760):
    g = cairo.LinearGradient(0, 1380, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.05, 0); g.add_color_stop_rgba(0.4, 0, 0, 0.05, 0.75); cr.rectangle(0, 1380, W, 540); cr.set_source(g); cr.fill()
    if name:
        x = 160 if name == A else 920; h = hop_of(t, b); ball(cr, name, x, 1480 - h * 26, 115, 'happy', 0.05 * h, 0); nametag(cr, name, x, 1625, col_of(name))
    C.draw_captions(cr, t, cy)

# ---------- full-screen scenes ----------
def stampbox(cr, t, t0, txt, col, x=540, y=760, size=84, rot=-0.08):
    if t < t0: return
    k = prog(t, t0, t0 + 0.2); s = lerp(2.4, 1, ease_out(k)); sz = fit(cr, txt, size, 900)
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(s, s); wd = tw(cr, txt, sz)
    rrect(cr, -wd / 2 - 40, -sz * 0.95, wd + 80, sz * 1.45, 18); cr.set_source_rgba(*col, 0.15); cr.fill_preserve(); cr.set_source_rgb(*col); cr.set_line_width(10); cr.stroke()
    ptext(cr, txt, 0, sz * 0.08, sz, col, 1, sw=0, shadow=False); cr.restore()
def mapscene(cr, t, k, t0, t1, land, lab, sub, stamp=None, stamp_t=None):
    sc = next((r[7] for r in RECRUITS if r[1].upper() == k), 0.2)
    cx, cy, s = mview(cr, t, k, (0, 0), (0, 0), sc * 0.85, sc, t0, t1 + 1, land)
    for j in range(3):
        ph = ((t - t0) * 0.7 + j / 3) % 1; km_shape(cr, G.c[k], cx, cy, s, land, 0.5 * (1 - ph), lw=4 + 10 * ph, edge=GOLD[:3], fill=0.0)
    endmap(cr); label(cr, lab, 540, 520, fit(cr, lab, 96, 980), WHITE); ptext(cr, sub, 540, 610, fit(cr, sub, 40, 980), GOLD, 1, fam='Poppins ExtraBold', sw=6)
    if stamp: stampbox(cr, t, stamp_t if stamp_t is not None else t0 + 0.5, stamp, (1, 0.3, 0.3), 540, 1260)
def sc_emuwar(cr, t, b, t0, t1):
    cx, cy, s = mview(cr, t, 'AU', (0, 0), tuple(G.p('AU', 118.4, -31.0)), 0.2, 0.9, t0, t0 + 1.4, (0.86, 0.5, 0.24))
    x, y = kpt('AU', 118.4, -31.0, cx, cy, s); pin(cr, x, y, t, t0 + 1.2, (1, 0.3, 0.3)); endmap(cr)
    k = ease_out(prog(t, t0 + 1.3, t0 + 2.5)); cr.save(); cr.rectangle(0, 900, W, 500); cr.clip(); emu_herd(cr, t, int(14 * k), 1000, 1320, 160, 3, 0.7); cr.restore()
    label(cr, '1932 · THE GREAT EMU WAR', 540, 520, 76, AU_C); tw0 = at('h2', 'twenty') - 0.1
    if t >= tw0: chip(cr, '2 MACHINE GUNS  vs  ~20,000 EMUS', 540, 620, 46, WHITE, INK, pop_k(t, tw0), 1)
def sc_emuwin(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.95, 0.6, 0.35); g.add_color_stop_rgb(0.7, 0.98, 0.8, 0.5); g.add_color_stop_rgb(1, 0.75, 0.45, 0.25); cr.set_source(g); cr.paint()
    cr.rectangle(0, 1200, W, 800); cr.set_source_rgb(0.8, 0.5, 0.28); cr.fill(); emu_herd(cr, t, 12, 1150, 1450, 220, 5, 0.9)
    emu(cr, 540, 900, 2.4, 0.1); emoji(cr, '👑', 700, 640, 140, 1, rot=0.2)
    label(cr, 'WINNER: THE EMUS', 540, 470, 96, AU_C); tw0 = at('h3', 'won') - 0.1; stampbox(cr, t, tw0, 'EMUS WIN', (0.9, 0.15, 0.2), 540, 1600, 110)
def sc_declined(cr, t, b, t0, t1):
    arena(cr, t)
    for j, n in enumerate(('USA', 'UK', 'France')):
        x = 220 + j * 320; ball(cr, n, x, 900, 120, 'angry', 0, 0); stampbox(cr, t, t0 + 0.6 + j * 0.3, 'NO', (0.95, 0.25, 0.3), x, 900, 90, -0.2)
    ptext(cr, 'STRONG COUNTRIES:', 540, 640, 60, WHITE, 1, sw=8)
    tw0 = at('h5', 'worst') - 0.2
    if t >= tw0:
        sx, sy = shake(t, tw0, 18); cr.save(); cr.translate(sx, sy); slam(cr, 'THE WORST', 540, 1250, 150, WHITE, t, tw0); slam(cr, 'ALLIANCE', 540, 1420, 160, AU_C, t, tw0 + 0.25); cr.restore()
        chip(cr, 'PART 1', 540, 1560, 56, GOLD, INK, pop_k(t, tw0 + 0.5), 1)
def sc_landlocked(cr, t, b, t0, t1):
    i = CUR[0]; r = RECRUITS[i - 1]; mapscene(cr, t, r[1].upper(), t0, t1, col_of(r[0]), r[0].upper(), 'COASTLINE: 0 KM', 'LANDLOCKED', t0 + 0.6)
def lake(cr, x, y, rx, ry):
    cr.save(); cr.translate(x, y); cr.scale(rx, ry); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(0.2, 0.55, 0.9); cr.fill()
def tugboat(cr, x, y, s):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.new_path(); cr.move_to(-120, 0); cr.line_to(120, 0); cr.line_to(95, 50); cr.line_to(-100, 50); cr.close_path(); cr.set_source_rgb(0.85, 0.2, 0.2); cr.fill()
    cr.rectangle(-60, -60, 90, 60); cr.set_source_rgb(0.97, 0.97, 0.95); cr.fill(); cr.rectangle(-40, -45, 22, 22); cr.set_source_rgb(0.4, 0.7, 1); cr.fill(); cr.rectangle(-5, -45, 22, 22); cr.fill()
    cr.rectangle(40, -100, 24, 70); cr.set_source_rgb(0.2, 0.2, 0.25); cr.fill(); cr.restore()
def sc_tug(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.4, 0.65, 0.95); g.add_color_stop_rgb(1, 0.6, 0.75, 0.4); cr.set_source(g); cr.paint()
    for x, hh in ((200, 400), (600, 480), (950, 380)): cr.new_path(); cr.move_to(x - 300, 1200); cr.line_to(x, 1200 - hh); cr.line_to(x + 300, 1200); cr.close_path(); cr.set_source_rgb(0.45, 0.55, 0.4); cr.fill()
    lake(cr, 540, 1250, 560, 180); tugboat(cr, 540 + 40 * math.sin(t * 0.7), 1230 + 6 * math.sin(t * 2), 1.4 * pop_k(t, at('r1d', 'tugboat') - 0.1, 0.3) if t >= at('r1d', 'tugboat') - 0.1 else 0.001)
    ts = at('r1d', 'Seven') - 0.1
    if t >= ts:
        for j in range(7):
            tj = ts + j * 0.07
            if t >= tj: x = 330 + j * 70; ball(cr, 'Mongolia', x, 1500, 26 * pop_k(t, tj, 0.25), 'happy', 0, 0)
    label(cr, 'THE MONGOLIAN NAVY', 540, 520, 90, col_of('Mongolia')); ptext(cr, '1 TUGBOAT · ~7 SAILORS · LAKE KHÖVSGÖL', 540, 610, 36, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_bonavy(cr, t, b, t0, t1):
    arena(cr, t, col_of('Bolivia')); k = ease_out(prog(t, at('r2a', 'five') - 0.2, at('r2a', 'sailors') + 0.3)); rng = np.random.default_rng(4)
    for j in range(int(300 * k)): x, y = rng.uniform(120, 960), rng.uniform(800, 1350); cr.new_path(); cr.arc(x, y, 7, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.85); cr.fill()
    label(cr, f'{int(5000 * k):,} SAILORS', 540, 560, 100, col_of('Bolivia')); ptext(cr, 'THE BOLIVIAN NAVY', 540, 650, 44, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_seaday(cr, t, b, t0, t1):
    arena(cr, t, col_of('Bolivia')); k = pop_k(t, t0 + 0.2, 0.35); cr.save(); cr.translate(540, 1000); cr.scale(k, k)
    rrect(cr, -230, -250, 460, 500, 40); cr.set_source_rgb(1, 1, 1); cr.fill(); rrect(cr, -230, -250, 460, 130, 40); cr.set_source_rgb(0.85, 0.15, 0.2); cr.fill()
    ptext(cr, 'MARCH', 0, -165, 64, WHITE, 1, sw=0, shadow=False); ptext(cr, '23', 0, 120, 230, INK, 1, sw=0, shadow=False); cr.restore()
    emoji(cr, '🌊', 830, 760, 140, 1); label(cr, 'DAY OF THE SEA', 540, 560, 104, col_of('Bolivia')); ptext(cr, 'CELEBRATED EVERY YEAR · SEA: 0 KM', 540, 650, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_limap(cr, t, b, t0, t1): mapscene(cr, t, 'LI', t0, t1, col_of('Liechtenstein'), 'LIECHTENSTEIN', 'ARMY: NONE SINCE 1868', 'NO ARMY', t0 + 0.8)
def soldier(cr, x, y, s, col):
    cr.save(); cr.translate(x, y); cr.scale(s, s); rrect(cr, -14, -10, 28, 46, 10); cr.set_source_rgb(*col); cr.fill(); cr.new_path(); cr.arc(0, -24, 14, 0, 2 * math.pi); cr.set_source_rgb(1, 0.85, 0.7); cr.fill()
    rrect(cr, -16, -46, 32, 16, 6); cr.set_source_rgb(0.2, 0.2, 0.25); cr.fill(); cr.restore()
def sc_eightyone(cr, t, b, t0, t1):
    arena(cr, t, col_of('Liechtenstein')); t80 = at('r3c', 'eighty') - 0.1; t81 = at('r3c', 'eighty-one') - 0.1
    n = int(80 * clamp(prog(t, t80, t80 + 0.9)))
    for j in range(n): soldier(cr, 120 + (j % 10) * 93, 790 + (j // 10) * 82, 0.95, (0.25, 0.4, 0.8))
    if t >= t81:
        k = pop_k(t, t81, 0.35); soldier(cr, 540, 1520, 1.8 * k, (0.95, 0.75, 0.2)); chip(cr, '+1 NEW FRIEND', 540, 1640 - 100, 44, GOLD, INK, k, 1)
    label(cr, f"{80 if t < t81 else 81} SOLDIERS", 540, 560, 104, col_of('Liechtenstein')); ptext(cr, '1866 · AUSTRO-PRUSSIAN WAR', 540, 650, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def guard(cr, x, y, s):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    for j in range(4): cr.rectangle(-16 + j * 8, -8, 8, 48); cr.set_source_rgb(*((0.95, 0.75, 0.15), (0.2, 0.3, 0.8))[j % 2]); cr.fill()
    cr.new_path(); cr.arc(0, -22, 13, 0, 2 * math.pi); cr.set_source_rgb(1, 0.85, 0.7); cr.fill(); cr.new_path(); cr.arc(0, -34, 12, math.pi, 0); cr.set_source_rgb(0.75, 0.75, 0.8); cr.fill()
    cr.move_to(22, 40); cr.line_to(22, -60); cr.set_source_rgb(0.4, 0.3, 0.2); cr.set_line_width(3); cr.stroke(); cr.move_to(22, -60); cr.line_to(32, -50); cr.line_to(22, -44); cr.set_source_rgb(0.8, 0.8, 0.85); cr.fill(); cr.restore()
def sc_guards(cr, t, b, t0, t1):
    set_generic(cr, t, 'Vatican'); cr.set_source_rgba(0, 0, 0.05, 0.35); cr.paint(); n = int(135 * clamp(prog(t, at('r4a', 'one') - 0.2, at('r4a', 'thirty') + 0.4)))
    for j in range(n): guard(cr, 90 + (j % 15) * 64, 830 + (j // 15) * 80, 0.9)
    label(cr, f'{n} SWISS GUARDS', 540, 540, 96, GOLD); ptext(cr, 'THE ENTIRE VATICAN ARMY · COUNTRY SIZE: 0.44 KM²', 540, 630, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_since1506(cr, t, b, t0, t1):
    arena(cr, t, col_of('Vatican')); guard(cr, 540, 1080, 4.5 * pop_k(t, t0 + 0.1, 0.35))
    label(cr, 'SINCE 1506', 540, 540, 130, GOLD); ptext(cr, 'SWISS SOLDIERS GUARDING THE POPE', 540, 640, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_codwars(cr, t, b, t0, t1):
    mapscene(cr, t, 'IS', t0, t1, col_of('Iceland'), 'THE COD WARS', 'ICELAND vs THE UK')
    for j, yr in enumerate(('1958–61', '1972–73', '1975–76')):
        tj = at('r6c', 'Three') - 0.1 + j * 0.3
        if t >= tj: stampbox(cr, t, tj, f'WIN {yr}', (0.2, 0.75, 0.45), 540, 1080 + j * 130, 58, -0.05)
def sc_netcut(cr, t, b, t0, t1):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.15, 0.25, 0.4); g.add_color_stop_rgb(1, 0.02, 0.1, 0.2); cr.set_source(g); cr.paint()
    for j in range(14): y = 1100 + j * 40; cr.move_to(0, y); [cr.line_to(x, y + 8 * math.sin(x / 60 + t * 2 + j)) for x in range(0, 1100, 40)]; cr.set_source_rgba(0.6, 0.8, 1, 0.2); cr.set_line_width(3); cr.stroke()
    tugboat(cr, 400 + 30 * math.sin(t), 1080, 1.2); emoji(cr, '✂️', 760, 1000, 160 * pop_k(t, at('r6d', 'net') - 0.1, 0.3) if t >= at('r6d', 'net') - 0.1 else 0, 1, rot=0.3 * math.sin(t * 6))
    for j in range(6): emoji(cr, '🐟', 150 + j * 160, 1400 + 20 * math.sin(t * 3 + j), 70, 1)
    label(cr, 'NET CUTTERS', 540, 540, 120, col_of('Iceland')); ptext(cr, "CUT BRITISH TRAWLERS' NETS", 540, 640, 42, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_crmap(cr, t, b, t0, t1): mapscene(cr, t, 'CR', t0, t1, col_of('Costa Rica'), 'COSTA RICA', 'ARMY ABOLISHED IN 1948', 'NO ARMY', at('r8a', 'abolished') - 0.1)
def sc_sloth(cr, t, b, t0, t1):
    set_generic(cr, t, 'Costa Rica'); emoji(cr, '🦥', 540, 1000 + 6 * math.sin(t), 520 * pop_k(t, t0 + 0.05, 0.4), 1, rot=0.04 * math.sin(t * 0.7))
    label(cr, 'SECRET WEAPON:', 540, 520, 80, WHITE); label(cr, 'SLOTHS', 540, 640, 140, col_of('Costa Rica'))
def sc_speed(cr, t, b, t0, t1):
    arena(cr, t); k = ease_out(prog(t, t0 + 0.2, t0 + 1.2))
    for j, (lab, v, col, em) in enumerate((('EMU', 50, (0.55, 0.45, 0.35), None), ('SLOTH', 0.24, col_of('Costa Rica'), '🦥'))):
        y = 900 + j * 300; ww = 820 * (v / 50) * k; rrect(cr, 130, y - 50, max(12, ww), 100, 30); cr.set_source_rgb(*col); cr.fill()
        ptext(cr, f'{lab} ≈ {v} KM/H', 540, y - 80, 54, WHITE, 1, sw=8)
        if em: emoji(cr, em, 170 + max(12, ww), y, 110, 1)
        else: emu(cr, 150 + ww, y + 10, 0.9, t * 3)
    label(cr, 'TOP SPEED', 540, 560, 110, WHITE)
def sc_neutral(cr, t, b, t0, t1):
    mapscene(cr, t, 'CH', t0, t1, col_of('Switzerland'), 'SWITZERLAND', 'NEUTRAL SINCE 1815', 'NEUTRAL', t0 + 0.4)
def sc_admap(cr, t, b, t0, t1): mapscene(cr, t, 'AD', t0, t1, col_of('Andorra'), 'ANDORRA', 'NO ARMY · DEFENDED BY FRANCE & SPAIN', 'NO ARMY', t0 + 0.4)
def sc_crossbow(cr, t, b, t0, t1):
    set_generic(cr, t, 'San Marino'); cr.set_source_rgba(0, 0, 0.05, 0.3); cr.paint()
    for j in range(8):
        x = (j * 140 + (t - t0) * 120) % 1300 - 110; soldier(cr, x, 1250 + 8 * abs(math.sin(t * 6 + j)), 2.0, (0.2, 0.35, 0.75)); emoji(cr, '🏹', x + 40, 1160, 70, 1, rot=-0.6)
    label(cr, 'CROSSBOW CORPS', 540, 540, 104, col_of('San Marino')); ptext(cr, 'CEREMONIAL · MOSTLY PARADES', 540, 640, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def sc_nrmap(cr, t, b, t0, t1): mapscene(cr, t, 'NR', t0, t1, col_of('Nauru'), 'NAURU', '≈ 21 KM² · NO ARMY', 'NO ARMY', t0 + 0.6)
def power_scene(cr, t, b, i):
    arena(cr, t, AU_C); pw = POWER[i]; prev = POWER[i - 1]; k = ease_out(prog(t, b['start'] + 0.2, b['start'] + 1.0)); v = lerp(prev, pw, k)
    label(cr, 'ALLIANCE POWER', 540, 560, 96, AU_C)
    rrect(cr, 120, 760, 840, 110, 55); cr.set_source_rgba(1, 1, 1, 0.12); cr.fill(); rrect(cr, 120, 760, max(40, 840 * v / 100), 110, 55); cr.set_source_rgb(0.95, 0.3, 0.3); cr.fill()
    ptext(cr, f'{v:.0f}%', 540, 1000, 160, WHITE, 1, sw=14)
    ptext(cr, 'EMU POWER', 540, 1220, 56, (0.7, 0.6, 0.5), 1, sw=8); rrect(cr, 120, 1260, 840, 80, 40); cr.set_source_rgb(0.5, 0.4, 0.32); cr.fill(); ptext(cr, '100%', 540, 1318, 56, WHITE, 1, sw=0, shadow=False)
    emu(cr, 930, 1180, 0.8, t * 2); ball(cr, A, 160, 1550, 90, 'shock' if i == NRC else 'happy', 0, 0)
    for j in range(1, i + 1): ball(cr, RNAME[j], 160 + j * 78, 1560, 34, 'happy', 0, 0)
    C.draw_captions(cr, t, 1760)
def cry_scene(cr, t, b, key):
    arena(cr, t, AU_C); name = SPK[key]; names = [A] + [r[0] for r in RECRUITS]
    for j, n in enumerate(names):
        row = 0 if j < 4 else (1 if j < 8 else 2); col = j if row == 0 else (j - 4 if row == 1 else j - 8); ncol = 4 if row < 2 else 3
        x = 540 + (col - (ncol - 1) / 2) * 250; y = 980 + row * 250; hh = hop_of(t, b) if n == name else 0
        ball(cr, n, x, y - hh * 40, 125 if n == name else 95, 'angry' if n == A else 'happy', 0.05 * hh, 0)
        if n == name: sx = x
    bubble(cr, t, b, sx, 520); nametag(cr, name, 540, 1760, col_of(name))
def lineup(cr, t, shock=False):
    names = [A] + [r[0] for r in RECRUITS]
    for j, n in enumerate(names):
        row = 0 if j < 4 else (1 if j < 8 else 2); col = j if row == 0 else (j - 4 if row == 1 else j - 8); ncol = 4 if row < 2 else 3
        x = 540 + (col - (ncol - 1) / 2) * 250; y = 980 + row * 250; ball(cr, n, x, y - abs(math.sin(t * 5 + j)) * (0 if shock else 10), 105, 'shock' if shock else ('angry' if n == A else 'happy'), 0, 0)
def sc_lineup(cr, t, b, t0, t1):
    arena(cr, t, AU_C); lineup(cr, t)
    rrect(cr, 60, 420, 960, 420, 36); cr.set_source_rgba(0.02, 0.03, 0.08, 0.85); cr.fill(); ptext(cr, 'ALLIANCE STATS', 540, 495, 56, AU_C, 1, sw=0, shadow=False)
    for j, (k_, v) in enumerate((('TANKS', '0'), ('WARSHIPS', '0'), ('TUGBOATS', '1'), ('HALBERDS', '~135'), ('SLOTHS', 'LOTS'))):
        tj = t0 + 0.3 + j * 0.25
        if t >= tj: ptext(cr, k_, 160, 580 + j * 52, 40, WHITE, pop_k(t, tj), fam='Poppins ExtraBold', sw=0, shadow=False, anchor='l'); ptext(cr, v, 920, 580 + j * 52, 40, GOLD, pop_k(t, tj), sw=0, shadow=False, anchor='r')
def sc_stampede(cr, t, b, t0, t1):
    s0 = bt('f3')['start']; g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.95, 0.55, 0.3); g.add_color_stop_rgb(1, 0.6, 0.3, 0.18); cr.set_source(g); cr.paint()
    cr.rectangle(0, 900, W, 1100); cr.set_source_rgb(0.75, 0.45, 0.25); cr.fill()
    k = ease_out(prog(t, s0, s0 + 3.5)); sx, sy = shake(t, s0, 10 * k, 3.0)
    cr.save(); cr.translate(sx, sy); emu_herd(cr, t, 40, lerp(880, 820, k), lerp(980, 1300, k), 90, 9, lerp(0.35, 0.9, k)); cr.restore()
    for j in range(30):
        ph = ((t - s0) * 0.5 + j / 30) % 1; cr.new_path(); cr.arc((j * 137) % 1080, 900 + 120 * ph, 30 + 60 * ph, 0, 2 * math.pi); cr.set_source_rgba(0.85, 0.65, 0.45, 0.35 * (1 - ph) * k); cr.fill()
    cr.save(); cr.translate(0, 110); lineup(cr, t, t >= bt('f4')['start']); cr.restore()
    if t >= bt('f3')['start'] + 0.6: stampbox(cr, t, bt('f3')['start'] + 0.6, '~20,000 EMUS', (0.95, 0.25, 0.3), 540, 520, 110)
SCENE = {'emuwar': sc_emuwar, 'emuwin': sc_emuwin, 'declined': sc_declined, 'landlocked': sc_landlocked, 'tug': sc_tug, 'bonavy': sc_bonavy, 'seaday': sc_seaday, 'limap': sc_limap,
         'eightyone': sc_eightyone, 'guards': sc_guards, 'since1506': sc_since1506, 'codwars': sc_codwars, 'netcut': sc_netcut, 'crmap': sc_crmap, 'sloth': sc_sloth, 'speed': sc_speed,
         'neutral': sc_neutral, 'lineup': sc_lineup, 'stampede': sc_stampede, 'admap': sc_admap, 'crossbow': sc_crossbow, 'nrmap': sc_nrmap}

# ---------- HUD, cards, stamps ----------
STAMPKEY = {}
for _k, _s, _t, _v in SCRIPT:
    if _v == 'stamp': STAMPKEY[ri_of(_k)] = _k
def recruited(t): return [i for i in range(1, NRC + 1) if t >= bt(STAMPKEY[i])['l0'] + 0.5]
def hud(cr, t):
    rec = recruited(t); pw = POWER[len(rec)]
    rrect(cr, 30, 110, 1020, 190, 40); cr.set_source_rgba(0.03, 0.04, 0.1, 0.88); cr.fill()
    ptext(cr, 'THE WORST ALLIANCE', 300, 170, 40, AU_C, 1, sw=0, shadow=False)
    ball(cr, A, 80, 240, 34, 'angry', 0, 0)
    for j in range(NRC):
        x = 140 + j * 48
        if (j + 1) in rec: ball(cr, RNAME[j + 1], x, 240, 21, 'happy', 0, 0)
        else: cr.new_path(); cr.arc(x, 240, 20, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.15); cr.fill(); ptext(cr, '?', x, 249, 22, WHITE, 0.6, sw=0, shadow=False)
    ptext(cr, 'ALLIANCE POWER', 830, 165, 30, WHITE, 0.85, fam='Poppins ExtraBold', sw=0, shadow=False)
    rrect(cr, 660, 195, 340, 40, 20); cr.set_source_rgba(1, 1, 1, 0.15); cr.fill(); rrect(cr, 660, 195, max(20, 340 * pw / 100 * 5), 40, 20); cr.set_source_rgb(0.95, 0.3, 0.3); cr.fill()
    ptext(cr, f'{pw}%', 830, 280, 40, GOLD, 1, sw=0, shadow=False)
def card(cr, t, i):
    b = bt(f'r{i}n'); k = ease_out(prog(t, b['start'], b['start'] + 0.25)); n = RNAME[i]
    cr.save(); cam(cr, 1.0 + 0.05 * prog(t, b['start'], b['end']), -0.04); arena(cr, t, col_of(n)); cr.restore()
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 520); cr.scale(s, s); ptext(cr, 'FINAL RECRUIT' if i == NRC else f'RECRUIT #{i}', 0, 0, 110, GOLD, clamp(k * 3), sw=14); cr.restore()
    rrect(cr, 140, 640, 800, 720, 40); cr.set_source_rgba(0.95, 0.9, 0.78, 0.95); cr.fill(); cr.set_source_rgb(0.55, 0.4, 0.25); cr.set_line_width(6); rrect(cr, 140, 640, 800, 720, 40); cr.stroke()
    ptext(cr, 'APPLICATION FORM', 540, 720, 44, (0.45, 0.3, 0.2), 1, sw=0, shadow=False)
    ball(cr, n, 540, 960, 170 * pop_k(t, b['start'] + 0.2, 0.35), 'happy', 0, 0)
    ptext(cr, n.upper() if n != 'Vatican' else 'VATICAN CITY', 540, 1230, fit(cr, n.upper(), 90, 720), INK, 1, sw=0, shadow=False)
    ptext(cr, 'APPLYING FOR: EMU WAR II', 540, 1310, 34, (0.45, 0.3, 0.2), 1, fam='Poppins ExtraBold', sw=0, shadow=False)
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def stamp_shot(cr, t, b, key):
    i = ri_of(key); n = RNAME[i]; h = hop_of(t, b)
    cr.save(); cam(cr, 1.0, 0, 540, 1000); set_australia(cr, t)
    ball(cr, A, 290, 1300 - h * 40, 200, 'happy', 0.05 * h, 0.8); ball(cr, n, 790, 1300, 200, 'happy', 0, -0.8); cr.restore()
    sx = 290 if SPK[key] == A else 790; bubble(cr, t, b, sx, 560); nametag(cr, SPK[key], sx, 1580, col_of(SPK[key]))
    stampbox(cr, t, b['l0'] + 0.5, STAMP[i], (0.2, 0.75, 0.45) if i != NRC else (0.95, 0.6, 0.15), 540, 900, 96)
    if t >= b['l0'] + 0.5: chip(cr, f'ALLIANCE POWER: {POWER[i]}%', 540, 1050, 44, WHITE, INK, pop_k(t, b['l0'] + 0.7), 1)

def draw_beat(cr, t, key):
    b = bt(key); name = SPK[key]; v = VIS[key]; i = ri_of(key)
    if i: CUR[0] = i
    t0 = b['start']; t1 = b['end']
    if v == 'card': card(cr, t, i)
    elif v == 'stamp': stamp_shot(cr, t, b, key)
    elif v in ('sc:lineup', 'sc:stampede'): SCENE[v[3:]](cr, t, b, t0, t1); corner(cr, t, b, None, 1870)
    elif v.startswith('sc:'): SCENE[v[3:]](cr, t, b, t0, t1); corner(cr, t, b, name)
    elif v == 'react': sh_react(cr, t, b, name, t0, t1)
    elif v == 'panic':
        sx, sy = shake(t, t0, 18, 2.0); cr.save(); cr.translate(sx, sy); sh_close(cr, t, b, name, t0, t1, 'shock'); cr.restore()
        cr.save(); cr.rectangle(0, 1150, W, 400); cr.clip(); emu_herd(cr, t, 6, 1250, 1380, 260, 2, 0.5, 0.85); cr.restore()
    elif v == 'end': draw_end(cr, t)
    elif v == 'power': power_scene(cr, t, b, i)
    elif v == 'cry': cry_scene(cr, t, b, key)
    else: {'close': sh_close, 'low': sh_low, 'ots': sh_ots, 'two': sh_two}[v](cr, t, b, name, t0, t1)
    f = 1 - prog(t, t0, t0 + 0.1)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.4 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, t0, t0 + 0.16)))
def draw_end(cr, t):
    c = bt('cta'); arena(cr, t, AU_C); lineup(cr, t, True)
    slam(cr, 'TO BE CONTINUED…'.replace('…', '...'), 540, 380, 96, GOLD, t, c['start'])
    tp = w('cta', 'part') - 0.1
    if t >= tp: chip(cr, 'PART 2: EMU WAR II', 540, 520, 56, WHITE, INK, pop_k(t, tp), 1)
    tc = w('cta', 'join') - 0.1
    if t >= tc: chip(cr, 'WHO SHOULD JOIN NEXT? COMMENT', 540, 1650, 42, GOLD, INK, pop_k(t, tc), 1)
    ts_ = w('cta', 'subscribe') - 0.1
    if t >= ts_: subscribe_button(cr, t, ts_, 540, 1800)
def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    draw_beat(cr, t, key)
    if key[0] == 'r' and VIS[key] not in ('card', 'power'): hud(cr, t)
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()
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
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 118; bar_ = beat * 4
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    for ci in range(int(dur / bar_) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar_ * 1.15 * SR)) / SR; env = np.minimum(1, Lc / 0.15) * np.exp(-Lc * 0.7)
        put(music, ci * bar_, sum(0.026 * np.sin(2 * np.pi * note(m) * Lc) for m in ch) * env); put(music, ci * bar_, 0.08 * np.sin(2 * np.pi * note(ch[0] - 24) * Lc) * env)
        for j, st in enumerate((0, 0.75, 1.5, 2.5, 3, 3.5)):
            m = ch[j % 3] + 12; P = np.arange(int(0.25 * SR)) / SR; put(music, ci * bar_ + st * beat, 0.026 * sum((1 / h) * np.sin(2 * np.pi * note(m) * h * P) for h in (1, 2, 3)) * np.exp(-P * 14))
    for bi in range(int(dur / (beat / 2))):
        t0 = bi * beat / 2
        if bi % 8 in (0, 3, 6): Ld = np.arange(int(0.3 * SR)) / SR; put(music, t0, 0.32 * np.sin(2 * np.pi * np.cumsum((85 if bi % 8 == 0 else 150) + 80 * np.exp(-Ld * 30)) / SR) * np.exp(-Ld * 13))
        if bi % 2 == 1: M = np.arange(int(0.04 * SR)); put(music, t0, 0.04 * rng.standard_normal(len(M)) * np.exp(-M / SR * 70))
    music = np.tanh(music * 1.3) * 0.45
    fx = np.zeros(n)
    def boom(t0, amp=0.6): Lb = np.arange(int(1.6 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-Lb * 10)) / SR) * np.exp(-Lb * 2.8))
    def whoosh(t0, amp=0.26, d=0.4): nz = rng.standard_normal(int(d * SR)); env = np.linspace(0, 1, len(nz)) ** 2; put(fx, t0, amp * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def bell(t0, amp=0.1, f=1175): Ld = np.arange(int(1.2 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * f * Ld) + 0.5 * np.sin(2 * np.pi * f * 2.76 * Ld)) * np.exp(-Ld * 4))
    def pop(t0, amp=0.05, f=1100): Lp = np.arange(int(0.05 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * (f + 400 * np.exp(-Lp * 60)) * Lp) * np.exp(-Lp * 60))
    def cheer(t0, amp=0.1, d=1.3): z = np.convolve(rng.standard_normal(int(d * SR)), np.ones(8) / 8, 'same'); L_ = np.linspace(0, 1, len(z)); put(fx, t0, amp * z * np.sin(np.pi * L_) ** 0.6)
    def horn(t0, amp=0.07): Lh = np.arange(int(0.9 * SR)) / SR; put(fx, t0, amp * sum(np.sign(np.sin(2 * np.pi * f * Lh)) for f in (146.8, 220, 293.7)) * np.minimum(1, Lh / 0.05) * np.exp(-Lh * 2.5) / 3)
    def rumble(t0, d=2.0, amp=0.3): z = np.convolve(rng.standard_normal(int(d * SR)), np.ones(300) / 300, 'same') * 8; put(fx, t0, amp * z * np.sin(np.pi * np.linspace(0, 1, len(z))))
    def stomp(t0, amp=0.25): Lb = np.arange(int(0.25 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(60 + 60 * np.exp(-Lb * 20)) / SR) * np.exp(-Lb * 18))
    boom(0.0, 1.0); rumble(0.0, 2.0, 0.25)
    for k, sp, _ in LINES:
        b = bt(k); v = VIS[k]
        whoosh(b['start'] - 0.2, 0.16, 0.22)
        if v == 'card': boom(b['start'] + 0.03, 0.8); bell(b['start'] + 0.03)
        if v == 'stamp': ts = b['l0'] + 0.5; boom(ts, 0.7); pop(ts, 0.18, 380); bell(ts + 0.05, 0.08, 1568)
        if v == 'react': boom(b['start'], 0.6)
    tw0 = w('h3', 'won'); boom(tw0 - 0.1, 0.9); horn(tw0 - 0.1, 0.09)
    tw1 = w('h5', 'worst') - 0.2; boom(tw1, 1.0); boom(tw1 + 0.25, 0.9); horn(tw1 + 0.25, 0.1)
    for j in range(3): pop(bt('h5')['start'] + 0.6 + j * 0.3, 0.14, 300)
    s0 = bt('f3')['start']
    for j in range(int((bt('cta')['start'] - s0) / 0.16)): stomp(s0 + j * 0.16 + 0.02 * np.sin(j), 0.15 + 0.15 * min(1, j / 20))
    rumble(s0, bt('cta')['start'] - s0, 0.35); boom(bt('f4')['start'] + 0.3, 1.0)
    c = bt('cta'); boom(c['start'], 0.9)
    tsc = w('cta', 'subscribe') - 0.1 + 1.3; pop(tsc, 0.18, 1800); bell(tsc + 0.05, 0.16, 1568); bell(tsc + 0.25, 0.12, 2093); cheer(tsc + 0.1, 0.1, 1.4)
    v = np.zeros(n); tt = np.arange(n) / SR
    for s0, a in T['clips']: put(v, s0, a / max(1e-6, np.abs(a).max()) * 0.9)
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_alliance'))
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


