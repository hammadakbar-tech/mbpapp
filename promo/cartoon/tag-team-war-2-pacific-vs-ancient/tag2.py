# GeoBall Wars: Tag Team War 2. Team Pacific (Australia + Philippines) vs Team Ancient (Greece + Japan), 9:16, 3+ min.
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

TA_C, TB_C = hexc('#FFC233')[:3], hexc('#4F8CFF')[:3]
A_C, U_C = TA_C, TB_C
COL = {'Australia': hexc('#FFC233')[:3], 'Philippines': hexc('#E8333F')[:3], 'Greece': hexc('#9CCBFF')[:3], 'Japan': hexc('#F5F5F5')[:3]}
TEAM = {'Australia': 'A', 'Philippines': 'A', 'Greece': 'B', 'Japan': 'B'}
TNAME = {'A': 'TEAM PACIFIC', 'B': 'TEAM ANCIENT'}; TMEM = {'A': ('Australia', 'Philippines'), 'B': ('Greece', 'Japan')}
NARR = ('en-US-GuyNeural', '+8%')
VOICE = {'Australia': ('en-AU-WilliamNeural', '+8%'), 'Philippines': ('fil-PH-AngeloNeural', '+8%'), 'Greece': ('el-GR-NestorasNeural', '+6%'), 'Japan': ('ja-JP-KeitaNeural', '+4%')}
# round: (title, icon, winner team, [(speaker, line, value_label)...4 lines: loser, winner, loser, winner], verdict word in last line, kind, values{country: number}, unit/footnote)
ROUNDS = [
 ('SIZE', '📏', 'A', [('Greece', "Together we're over half a million square kilometres!", '0.51M KM²'), ('Australia', "Cute. I'm almost eight million on my own!", '7.69M KM²'),
                     ('Japan', "Size isn't everything!", ''), ('Philippines', "With me, almost eight million. Sixteen times bigger!", '8.0M KM²')], 'bigger', 'area',
  {'Australia': 7.69, 'Philippines': 0.30, 'Greece': 0.132, 'Japan': 0.378}, 'MILLION KM²'),
 ('HISTORY', '🏛️', 'B', [('Philippines', "My independence was declared in eighteen ninety-eight!", '1898'), ('Greece', "My Olympics started in seven seventy-six B.C.!", '776 BC'),
                        ('Australia', "I became a country in nineteen oh one!", '1901'), ('Japan', "My oldest company was founded in five seventy-eight. Ancient wins!", '578 AD')], 'wins', 'years',
  {'Philippines': 1898, 'Greece': -776, 'Australia': 1901, 'Japan': 578}, 'OLDER WINS'),
 ('PEOPLE', '👥', 'A', [('Japan', "One hundred and twenty-three million Japanese!", '123M'), ('Philippines', "One hundred and twelve million Filipinos!", '113M'),
                       ('Greece', "Plus ten million Greeks. One hundred and thirty-three million!", '133.7M'), ('Australia', "Plus twenty-eight million Aussies. One hundred and forty! We win!", '140.3M')], 'win', 'sum',
  {'Japan': 123.3, 'Philippines': 112.7, 'Greece': 10.4, 'Australia': 27.6}, 'MILLION PEOPLE'),
 ('ISLANDS', '🏝️', 'B', [('Australia', "I have over eight thousand islands!", '8,222'), ('Japan', "I recounted mine. Fourteen thousand!", '14,125'),
                        ('Philippines', "Plus my seven thousand six hundred. Almost sixteen thousand!", '15,863'), ('Greece', "Plus my six thousand. Over twenty thousand. Islands are ours!", '~20,000')], 'ours', 'sum',
  {'Australia': 8222, 'Japan': 14125, 'Philippines': 7641, 'Greece': 6000}, 'ISLANDS'),
 ('COASTLINE', '🏖️', 'A', [('Greece', "Thirteen thousand kilometres of coastline!", '13,676 KM'), ('Philippines', "I have thirty-six thousand!", '36,289 KM'),
                          ('Japan', "Twenty-nine thousand. Forty-three thousand together!", '43,427 KM'), ('Australia', "Plus my twenty-five thousand. Sixty-two thousand! Beach team wins!", '62,049 KM')], 'wins', 'sum',
  {'Greece': 13676, 'Philippines': 36289, 'Japan': 29751, 'Australia': 25760}, 'KM OF COASTLINE'),
 ('VOLCANOES', '🌋', 'B', [('Philippines', "I have twenty-four active volcanoes!", '24'), ('Greece', "Santorini's eruption shook the ancient world!", 'SANTORINI'),
                          ('Australia', "Mainland Australia has zero. Very relaxing.", '0'), ('Japan', "I have one hundred and eleven. Eruption team wins!", '111')], 'wins', 'sum',
  {'Philippines': 24, 'Greece': 4, 'Australia': 0, 'Japan': 111}, 'ACTIVE VOLCANOES'),
 ('YOUNGEST', '🎂', 'A', [('Japan', "My average age is almost fifty.", '49.9'), ('Australia', "Mine's thirty-eight, mate!", '38.4'),
                         ('Greece', "Mine is forty-seven.", '46.9'), ('Philippines', "Mine is twenty-seven! Young team wins!", '27.1')], 'wins', 'avg_low',
  {'Japan': 49.9, 'Australia': 38.4, 'Greece': 46.9, 'Philippines': 27.1}, 'MEDIAN AGE · YOUNGER WINS'),
 ('LIVING LONGER', '❤️', 'B', [('Australia', "Aussies live to eighty-three!", '83.1'), ('Greece', "Greeks live to eighty-one!", '81.4'),
                              ('Philippines', "Filipinos live to about seventy-one.", '~71'), ('Japan', "Japanese live to eighty-four. Longest-living team wins!", '84.1')], 'wins', 'avg_high',
  {'Australia': 83.1, 'Greece': 81.4, 'Philippines': 71.0, 'Japan': 84.1}, 'LIFE EXPECTANCY (YEARS)')]
NR = len(ROUNDS)
NUMW = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight']
LINES = [('h1', 'Philippines', "Australia! Let's team up!"),
         ('h2', 'Australia', "Too right, mate! Against who?"),
         ('h3', 'Greece', "Against the oldest civilizations on Earth."),
         ('h4', 'Japan', "Greece and Japan. Ancient, and legendary."),
         ('title', None, "Team Pacific versus Team Ancient. Eight rounds. This is Tag Team War two.")]
RD = {}
for i, (ttl, ic, win, lines, vw, kind, vals, unit) in enumerate(ROUNDS, 1):
    LINES.append((f'c{i}', None, f"{'Final round' if i == NR else 'Round ' + NUMW[i]}: {ttl.lower()}."))
    for j, (sp, ln, lab) in enumerate(lines): LINES.append((f'r{i}{"abcd"[j]}', sp, ln))
    LINES.append((f'r{i}v', None, f"{'Team Pacific' if win == 'A' else 'Team Ancient'}!"))
    RD[i] = (ttl, win, (f'r{i}d', vw))
LINES += [('e1', 'Australia', "Four all?! Not again!"), ('e2', 'Japan', "Then let the viewers decide."),
          ('cta', None, "It's a tie! You pick the tiebreaker. Comment it below, and subscribe to see who wins!")]
SPK = {k: s for k, s, _ in LINES}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3', 'h4')
C.SAY = {None: {'B.C.': 'B C', 'Santorini': 'Santo-reeni'}}
C.HOT = ('pacific', 'ancient', 'team', 'wins', 'win', 'tag', 'war', 'tie', 'tiebreaker', 'comment', 'subscribe', 'ours')
C.TAIL_OVERRIDE = {'h1': 0.12, 'h2': 0.15, 'h3': 0.15, 'h4': 0.3, 'h5': 0.4, 'title': 0.6, 'e1': 0.3, 'e2': 0.3, 'e3': 0.4, 'cta': 3.6, **{f'c{i}': 0.1 for i in range(1, NR + 1)},
                   **{k: 0.18 for k, s, _ in LINES if s and k[0] == 'r'}, **{f'r{i}d': 0.75 for i in range(1, NR + 1)}, **{f'r{i}v': 0.4 for i in range(1, NR + 1)}}
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
class Geo:
    def __init__(self, d):
        for nm, f in (('Australia', 'au'), ('Philippines', 'ph'), ('Greece', 'gr'), ('Japan', 'jp')): B.FL[nm] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', f + '.png'))
def at(key, word, n=0): return w(key, word, n)
def col_of(name): return COL.get(name, WHITE)
def tcol(tm): return TA_C if tm == 'A' else TB_C
def partner(name): a, b = TMEM[TEAM[name]]; return b if name == a else a
def rival_of(name): return {'Australia': 'Japan', 'Philippines': 'Greece', 'Greece': 'Philippines', 'Japan': 'Australia'}[name]
def set_of(name, cr, t): {'Australia': set_australia, 'Philippines': set_philippines, 'Greece': set_greece, 'Japan': set_japan}[name](cr, t)
def sgn_of(name): return -1 if TEAM[name] == 'A' else 1
def ri_of(key): return int(key[1]) if key[0] in 'rc' and key[1].isdigit() else 0

# ---------- shots ----------
def sh_close(cr, t, b, name, t0, t1, mood='happy'):
    sgn = sgn_of(name); h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.06 * sgn, 540, 1100); set_of(name, cr, t); ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1, mood='happy'):
    h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, mood, 0.04 * h, 0); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_team(cr, t, b, name, t0, t1, mood='happy'):
    """Speaker and teammate side by side."""
    h = hop_of(t, b); p = partner(name); pan = lerp(-40, 40, prog(t, t0, t1))
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    xs = {name: 330, p: 760} if TEAM[name] == 'A' else {p: 320, name: 750}
    for n, x in xs.items():
        hh = h if n == name else 0; ball(cr, n, x, 1300 - hh * 40, 220 if n == name else 180, mood if n == name else 'happy', 0.05 * hh, 0.3 if x < 540 else -0.3)
    cr.restore(); sx = xs[name] - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1600, col_of(name))
    rrect(cr, 540 - 210, 1700, 420, 70, 35); cr.set_source_rgb(*tcol(TEAM[name])); cr.fill(); ptext(cr, TNAME[TEAM[name]], 540, 1748, 38, INK, 1, sw=0, shadow=False)
def sh_four(cr, t, b, name, t0, t1, mood='happy'):
    h = hop_of(t, b); cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.05), 0, 540, 1000); arena(cr, t)
    for n, x in (('Australia', 150), ('Philippines', 390), ('Greece', 690), ('Japan', 930)):
        hh = h if n == name else 0; ball(cr, n, x, 1300 - hh * 40, 150 if n == name else 120, mood if n == name else 'angry', 0.05 * hh, 0.6 if x < 540 else -0.6)
    emoji(cr, '⚡', 540, 1300, 120, 1, rot=0.2 * math.sin(t * 10)); cr.restore()
    sx = {'Australia': 150, 'Philippines': 390, 'Greece': 690, 'Japan': 930}[name]; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1520, col_of(name))
def sh_react(cr, t, b, losers, t0):
    k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.2, 1.05, k), 0.03, 540 + sx, 1080 + sy); set_of(losers[0], cr, t)
    for j, n in enumerate(losers): ball(cr, n, 300 + j * 480, 1180, 230, 'shock', 0, 0)
    cr.restore(); ptext(cr, '?!', 540, 820, 170, GOLD, pop_k(t, t0 + 0.05), sw=14)
    for j, n in enumerate(losers): nametag(cr, n, 300 + j * 480, 1500, col_of(n))

# ---------- stat scene ----------
def fmtv(v, unit):
    if unit == 'MILLION KM²': return f'{v:.2f}M'
    if unit == 'MILLION PEOPLE': return f'{v:.1f}M'
    if v >= 1000: return f'{v:,.0f}'
    return f'{v:g}'
def stat_scene(cr, t, i):
    ttl, ic, win, lines, vw, kind, vals, unit = ROUNDS[i - 1]
    arena(cr, t, tcol(win) if t >= tv_of(i) else None)
    label(cr, f'ROUND {i} · {ttl}', 540, 470, fit(cr, f'ROUND {i} · {ttl}', 72, 980), WHITE); ptext(cr, unit, 540, 545, 32, GOLD, 1, fam='Poppins ExtraBold', sw=5)
    spoke = {sp: bt(f'r{i}{"abcd"[j]}')['start'] + 0.2 for j, (sp, _, _) in enumerate(lines)}
    for tm, cx in (('A', 285), ('B', 795)):
        rrect(cr, cx - 245, 600, 490, 920, 36); cr.set_source_rgba(*tcol(tm), 0.14); cr.fill()
        ptext(cr, TNAME[tm], cx, 665, 40, tcol(tm), 1, sw=6)
        tot = 0; shown = 0
        for j, n in enumerate(TMEM[tm]):
            y = 800 + j * 210; ball(cr, n, cx - 150, y, 62, 'happy', 0, 0)
            if t >= spoke[n]:
                k = pop_k(t, spoke[n], 0.3); v = vals[n]; shown += 1; tot += v
                lab = {'years': (f'{-v} BC' if v < 0 else f'{v} AD' if v < 1000 else str(v))}.get(kind, fmtv(v, unit))
                if n == 'Greece' and ttl == 'VOLCANOES': lab = 'SANTORINI'
                if n == 'Greece' and ttl == 'ISLANDS': lab = '~6,000'
                if n == 'Philippines' and ttl == 'LIVING LONGER': lab = '~71'
                ptext(cr, lab, cx + 75, y + 22, fit(cr, lab, 62, 250), WHITE, k, sw=8)
        if kind in ('sum', 'area') and shown == 2:
            tk = max(spoke[n] for n in TMEM[tm]); kk = pop_k(t, tk + 0.4, 0.3); tl = fmtv(tot, unit) if ttl != 'ISLANDS' or tm == 'A' else '~20,000'
            if ttl == 'VOLCANOES' and tm == 'B': tl = '111+'
            rrect(cr, cx - 200, 1250, 400, 120, 30); cr.set_source_rgb(*tcol(tm)); cr.fill(); ptext(cr, 'TOTAL', cx, 1290, 30, INK, kk, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, tl, cx, 1352, fit(cr, tl, 60, 360), INK, kk, sw=0, shadow=False)
        if kind in ('avg_low', 'avg_high') and shown == 2:
            tk = max(spoke[n] for n in TMEM[tm]); kk = pop_k(t, tk + 0.4, 0.3); av = sum(vals[n] for n in TMEM[tm]) / 2
            rrect(cr, cx - 200, 1250, 400, 120, 30); cr.set_source_rgb(*tcol(tm)); cr.fill(); ptext(cr, 'TEAM AVERAGE', cx, 1290, 28, INK, kk, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, f'{av:.1f}', cx, 1352, 60, INK, kk, sw=0, shadow=False)
        if kind == 'years' and shown == 2:
            tk = max(spoke[n] for n in TMEM[tm]); kk = pop_k(t, tk + 0.4, 0.3); old = min(vals[n] for n in TMEM[tm]); ol = f'{-old} BC' if old < 0 else f'{old} AD' if old < 1000 else str(old)
            rrect(cr, cx - 200, 1250, 400, 120, 30); cr.set_source_rgb(*tcol(tm)); cr.fill(); ptext(cr, 'OLDEST', cx, 1290, 30, INK, kk, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, ol, cx, 1352, 60, INK, kk, sw=0, shadow=False)
        if t >= tv_of(i) and tm == win: emoji(cr, '👑', cx, 560, 90 * pop_k(t, tv_of(i), 0.3), 1)
    emoji(cr, ic, 540, 1450, 90, 1)
def tv_of(i): return w(*RD[i][2])
def verdict(cr, t, i):
    tv = tv_of(i); win = RD[i][1]
    if t < tv: return
    col = tcol(win); f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); txt = f'{TNAME[win]} WINS'
    cr.save(); cr.translate(540, 1580); cr.rotate(-0.04 if win == 'A' else 0.04); cr.scale(s, s); sz = fit(cr, txt, 70, 880); wd = tw(cr, txt, sz)
    rrect(cr, -wd / 2 - 40, -80, wd + 80, 116, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 6, sz, INK, 1, sw=0, shadow=False); cr.restore()
def score_at(t): return sum(t >= tv_of(i) and RD[i][1] == 'A' for i in RD), sum(t >= tv_of(i) and RD[i][1] == 'B' for i in RD)
def round_of(t):
    for i in RD:
        nxt = bt(f'c{i + 1}')['start'] if i < NR else bt('e1')['start']
        if bt(f'c{i}')['start'] <= t < nxt: return i
    return None
def hud(cr, t):
    a = ease_out(prog(t, bt('title')['end'] - 0.4, bt('title')['end']))
    if a <= 0: return
    sa, sb = score_at(t); rrect(cr, 30, 120, 1020, 200, 44); cr.set_source_rgba(0.03, 0.04, 0.1, 0.88 * a); cr.fill()
    for tm, x, sc in (('A', 250, sa), ('B', 830, sb)):
        ptext(cr, TNAME[tm], x, 178, 34, tcol(tm), a, sw=0, shadow=False)
        for j, n in enumerate(TMEM[tm]): ball(cr, n, x - 110 + j * 220, 260, 32, 'happy', 0, 0)
        last = max([tv_of(i) for i in RD if RD[i][1] == tm and t >= tv_of(i)] or [-9]); k = pop_k(t, last, 0.4) if t - last < 0.6 else 1.0
        cr.save(); cr.translate(x, 290); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 90, WHITE, a, sw=0, shadow=False); cr.restore()
    i = round_of(t); lab = f'ROUND {i}/{NR}' if i else ('FINAL: 4 — 4' if t >= bt('e1')['start'] else 'VS')
    ptext(cr, lab, 540, 200, 32, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, '—', 540, 285, 60, WHITE, a, sw=0, shadow=False)
def card(cr, t, i):
    b = bt(f'c{i}'); k = ease_out(prog(t, b['start'], b['start'] + 0.2)); ttl, ic = ROUNDS[i - 1][0], ROUNDS[i - 1][1]
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], b['end']), -0.05); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((TA_C, TB_C)):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 500); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, 'FINAL ROUND' if i == NR else f'ROUND {i}', 0, 0, 120 if i == NR else 150, CRIMSON if i == NR else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = b['l0'] + 0.4
    if t >= tt:
        kk = pop_k(t, tt, 0.25); cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore(); emoji(cr, ic, 540, 1230, 170 * kk, 1, rot=0.1 * math.sin(t * 5))
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def round_result(cr, t, i):
    b = bt(f'r{i}v'); win = RD[i][1]; arena(cr, t, tcol(win)); k = ease_out(prog(t, b['start'], b['start'] + 0.3))
    for j, n in enumerate(TMEM[win]): ball(cr, n, 330 + j * 420, 1050 - abs(math.sin(t * 6 + j)) * 24, 190 * k + 1, 'happy', 0, 0)
    emoji(cr, '👑', 540, 760, 160 * k, 1); slam(cr, f'{TNAME[win]}!', 540, 560, 100, tcol(win), t, b['start'] + 0.05)
    sa, sb = score_at(t); ptext(cr, f'{sa} — {sb}', 540, 1420, 130, WHITE, pop_k(t, b['start'] + 0.2), sw=14)
    ptext(cr, 'PACIFIC', 300, 1530, 40, TA_C, 1, fam='Poppins ExtraBold', sw=6); ptext(cr, 'ANCIENT', 780, 1530, 40, TB_C, 1, fam='Poppins ExtraBold', sw=6)
    C.draw_captions(cr, t, 1760)

# ---------- hook, title, end ----------
def team_intro(cr, t):
    b = bt('h5'); arena(cr, t)
    ta = b['start'] + 0.1; tb = w('h5', 'Ancient') - 0.2
    for tm, y, t0 in (('A', 700, ta), ('B', 1250, tb)):
        if t < t0: continue
        k = ease_out(prog(t, t0, t0 + 0.4)); rrect(cr, 60, y - 230, 960, 420, 40); cr.set_source_rgba(*tcol(tm), 0.18 * k); cr.fill()
        slam(cr, TNAME[tm], 540, y - 130, 92, tcol(tm), t, t0)
        for j, n in enumerate(TMEM[tm]): ball(cr, n, lerp(-300 if j == 0 else 1380, 330 + j * 420, k), y + 60, 120, 'angry', 0, 0.4 if j == 0 else -0.4)
    C.draw_captions(cr, t, 1760)
def draw_hook(cr, t):
    for k_, nm, shot, mood in (('h1', 'Philippines', sh_close, 'happy'), ('h2', 'Australia', sh_team, 'happy'), ('h3', 'Greece', sh_low, 'angry'), ('h4', 'Japan', sh_team, 'angry')):
        b = bt(k_)
        if b['start'] <= t < b['end']:
            shot(cr, t, b, nm, b['start'], b['end'], mood)
            if k_ == 'h3': emoji(cr, '🏛️', 860, 820, 150 * pop_k(t, b['l0'], 0.3), 1)
            if k_ == 'h4': emoji(cr, '⛩️', 540, 1450, 140 * pop_k(t, b['l0'] + 0.4, 0.3), 1)
            streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.2))); return True
    return False
def draw_title(cr, t):
    b = bt('title'); cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.08), 0.03, 540, 1000); arena(cr, t); e = ease_out(prog(t, b['start'], b['start'] + 0.5))
    for n, x0, x1 in (('Australia', -300, 170), ('Philippines', -300, 400), ('Greece', 1380, 680), ('Japan', 1380, 910)):
        ball(cr, n, lerp(x0, x1, e), 1450 - abs(math.sin(t * 6 + x1)) * 14, 130, 'angry', 0, 0.7 if x1 < 540 else -0.7)
    emoji(cr, '⚡', 540, 1450, 140, 1, rot=0.2 * math.sin(t * 10)); cr.restore()
    slam(cr, 'TEAM PACIFIC', 540, 500, 120, TA_C, t, w('title', 'Team'))
    tv = w('title', 'versus')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 650); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 80, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 30, 90, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'TEAM ANCIENT', 540, 820, 120, TB_C, t, w('title', 'Team', 1))
    tg = w('title', 'Tag')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'TAG TEAM WAR 2', 540, 1050, 110, WHITE, t, tg); cr.restore()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22)))
def draw_end(cr, t):
    e1, e2, c = bt('e1'), bt('e2'), bt('cta')
    if t < e2['start']:
        sx, sy = shake(t, e1['l0'], 20, 0.4); cr.save(); cam(cr, push(t, e1['start'], e1['end'], 1.0, 1.15), -0.05, 540 + sx, 1100 + sy); set_australia(cr, t); ball(cr, 'Australia', 540, 1290, 290, 'shock', 0, 0); cr.restore()
        bubble(cr, t, e1, 540, 540); nametag(cr, 'Australia', 540, 1640, col_of('Australia')); ptext(cr, '4 — 4', 540, 820, 130, WHITE, pop_k(t, e1['start'] + 0.1), sw=14); return
    if t < c['start']:
        h = hop_of(t, e2); cr.save(); cam(cr, push(t, e2['start'], e2['end'], 1.0, 1.12), 0.05, 540, 1100); set_japan(cr, t); ball(cr, 'Japan', 540, 1260 - h * 50, 300, 'happy', 0.05 * h, 0); cr.restore()
        bubble(cr, t, e2, 540, 540); nametag(cr, 'Japan', 540, 1640, col_of('Japan')); emoji(cr, '🙇', 200, 900, 140 * pop_k(t, e2['l0'] + 0.3), 1); return
    cr.save(); cam(cr, push(t, c['start'], c['end'], 1.0, 1.06), 0.02, 540, 1000); arena(cr, t)
    for n, x in (('Australia', 150), ('Philippines', 390), ('Greece', 690), ('Japan', 930)): ball(cr, n, x, 1290 - abs(math.sin(t * 5 + x)) * 10, 110, 'angry', 0, 0.6 if x < 540 else -0.6)
    emoji(cr, '⚡', 540, 1290, 110, 1, rot=0.2 * math.sin(t * 10)); cr.restore()
    sx, sy = shake(t, c['start'], 16, 0.4); cr.save(); cr.translate(sx, sy); slam(cr, "IT'S A TIE!", 540, 470, 140, GOLD, t, c['start']); cr.restore()
    ptext(cr, 'PACIFIC', 220, 590, 54, TA_C, 1, sw=8); ptext(cr, '4 — 4', 540, 600, 84, WHITE, 1, sw=10); ptext(cr, 'ANCIENT', 860, 590, 54, TB_C, 1, sw=8)
    tp = w('cta', 'pick') - 0.1
    if t >= tp:
        kk = pop_k(t, tp); cr.save(); cr.translate(540, 730); cr.scale(kk, kk); ptext(cr, 'YOU PICK THE TIEBREAKER', 0, 0, 66, WHITE, 1, sw=9); cr.restore()
        for j, (em, lab) in enumerate((('🍜', 'FOOD?'), ('🏅', 'OLYMPICS?'), ('🎤', 'KARAOKE?'))):
            tj = tp + 0.4 + j * 0.25
            if t < tj: continue
            x = 220 + j * 320; k2 = pop_k(t, tj); emoji(cr, em, x, 880 + 8 * math.sin(t * 4 + j), 120 * k2, 1); ptext(cr, lab, x, 1010, 40, GOLD, k2, fam='Poppins ExtraBold', sw=6)
    tc = w('cta', 'Comment') - 0.1
    if t >= tc: chip(cr, 'COMMENT THE TIEBREAKER', 540, 1460, 46, WHITE, INK, pop_k(t, tc), 1)
    ts_ = w('cta', 'subscribe') - 0.1
    if t >= ts_: subscribe_button(cr, t, ts_, 540, 1640)

def draw_line(cr, t, key):
    b = bt(key); name = SPK[key]; i = ri_of(key); j = 'abcd'.index(key[-1]); d = b['end'] - b['start']
    shots = [(b['start'], ['close', 'team', 'low', 'four'][(i + j) % 4]), (b['start'] + 0.45 * d, 'stat')]
    if j == 3: shots.append((tv_of(i) + 0.6, 'react'))
    k = max(x for x, (s, _) in enumerate(shots) if s <= t or x == 0); t0 = shots[k][0]; t1 = shots[k + 1][0] if k + 1 < len(shots) else b['end']; sh = shots[k][1]
    if sh == 'stat': stat_scene(cr, t, i); verdict(cr, t, i); C.draw_captions(cr, t, 1760)
    elif sh == 'react': sh_react(cr, t, b, list(TMEM['B' if RD[i][1] == 'A' else 'A']), t0)
    else: {'close': sh_close, 'team': sh_team, 'low': sh_low, 'four': sh_four}[sh](cr, t, b, name, t0, t1)
    f = 1 - prog(t, t0, t0 + 0.1)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.45 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, t0, t0 + 0.16)))
def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if key in ('h1', 'h2', 'h3', 'h4'): draw_hook(cr, t)
    elif key == 'h5': team_intro(cr, t)
    elif key == 'title': draw_title(cr, t)
    elif key in ('e1', 'e2', 'e3', 'cta'): draw_end(cr, t); hud(cr, t)
    elif key[0] == 'c': card(cr, t, ri_of(key)); hud(cr, t)
    elif key.endswith('v'): round_result(cr, t, ri_of(key))
    else: draw_line(cr, t, key); hud(cr, t)
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
    boom(0.0, 1.0)
    for k_ in ('h2', 'h3', 'h4'): whoosh(bt(k_)['start'] - 0.25, 0.3, 0.3); boom(bt(k_)['start'] + 0.05, 0.6)
    whoosh(bt('title')['start'] - 0.35)
    for wd, n_ in (('Team', 0), ('versus', 0), ('Team', 1), ('Tag', 0)): boom(w('title', wd, n_), 0.7)
    horn(w('title', 'Tag'), 0.09)
    for i in RD:
        b = bt(f'c{i}'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03)
        tv = tv_of(i); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if RD[i][1] == 'A' else 1319); cheer(tv + 0.1); pop(tv + 0.6, 0.12, 500)
        for x in 'abcd':
            bx = bt(f'r{i}{x}'); whoosh(bx['start'] - 0.2, 0.16, 0.22); whoosh(bx['start'] + 0.45 * (bx['end'] - bx['start']) - 0.15, 0.14, 0.2)
        bv = bt(f'r{i}v'); boom(bv['start'] + 0.05, 0.6); cheer(bv['start'] + 0.1, 0.1, 1.0)
    boom(bt('e1')['start'], 0.9); boom(bt('cta')['start'], 0.9); horn(bt('cta')['start'], 0.1)
    for j in range(3): pop(w('cta', 'pick') + 0.3 + j * 0.25, 0.12, 900 + 200 * j)
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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_tag2'))
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


