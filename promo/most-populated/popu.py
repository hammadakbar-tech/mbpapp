"""'The 10 Most Populated Countries, Resized by People' (9:16). Countdown: a fly-through dive on a 3D globe, a whip-pan,
then each country rescaled so its area matches its population (ghost outline = real size). Word-synced (engine from china.py).
Usage: python3 popu.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
import big as B
from big import local, bounds, recentre, area, km_shape, km_path, globe, bg, TEAL, SKY, CORAL, LIME, VIOLET, ORANGE
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON, PARCH
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

C.SAY = {None: {}}
C.HOT = ('ethiopia', 'russia', 'bangladesh', 'brazil', 'nigeria', 'pakistan', 'indonesia', 'united', 'states', 'china', 'india', 'florida', 'java',
         'number', 'million', 'billion', 'people', 'humans', 'biggest', 'shrinks', 'explodes', 'shrinking', 'third', 'africans')
C.TAIL_OVERRIDE = {'h1': 0.3, 'h2': 0.3, 'h3': 0.4}
WORLD_DENSITY = 8200 / 134.0  # people per km² of land (millions / million km², Antarctica excluded)
# rank, key, NE name, display, population (millions), total area (M km²), colour, cut word, narration, fact chip, tease for what comes next
ENTRIES = [
    (10, 'm10', 'Ethiopia', 'ETHIOPIA', 135, 1.104, LIME, 'hundred',
     "Number ten: Ethiopia. A hundred and thirty-five million people, and the most populated landlocked country on Earth.",
     ('landlocked', '🔒', 'MOST POPULATED LANDLOCKED'), 'NEXT: THE BIGGEST COUNTRY… SHRINKS'),
    (9, 'm9', 'Russia', 'RUSSIA', 144, 17.098, SKY, 'hundred',
     "Number nine: Russia. The biggest country on Earth has just a hundred and forty-four million people. Sized by people, it shrinks to almost nothing.",
     ('shrinks', '🗺️', '#1 BY AREA · #9 BY PEOPLE'), 'NEXT: SMALLER THAN FLORIDA'),
    (8, 'm8', 'Bangladesh', 'BANGLADESH', 176, 0.148, CORAL, 'hundred',
     "Number eight: Bangladesh. A hundred and seventy-six million people, in a country smaller than Florida. Sized by people, it explodes.",
     ('Florida', '🌴', 'SMALLER THAN FLORIDA'), None),
    (7, 'm7', 'Brazil', 'BRAZIL', 213, 8.51, LIME, 'Two',
     "Number seven: Brazil. Two hundred and thirteen million. Almost half of all South Americans live here.",
     ('half', '🌎', '~HALF OF SOUTH AMERICA'), None),
    (6, 'm6', 'Nigeria', 'NIGERIA', 238, 0.924, TEAL, 'Two',
     "Number six: Nigeria. Two hundred and thirty-eight million. Around one in every six Africans is Nigerian.",
     ('six', '🌍', '1 IN 6 AFRICANS'), 'NEXT: MORE PEOPLE THAN BRAZIL, IN 1/10 THE SPACE'),
    (5, 'm5', 'Pakistan', 'PAKISTAN', 255, 0.881, VIOLET, 'Two',
     "Number five: Pakistan. Two hundred and fifty-five million: more people than Brazil, in a tenth of the space.",
     ('tenth', '📦', '1/10 THE SPACE OF BRAZIL'), None),
    (4, 'm4', 'Indonesia', 'INDONESIA', 286, 1.905, ORANGE, 'Two',
     "Number four: Indonesia. Two hundred and eighty-six million people across seventeen thousand islands, and over half of them live on just one: Java.",
     ('Java', '🏝️', '56% LIVE ON JAVA'), 'TOP 3: THE GAP GETS HUGE'),
    (3, 'm3', 'United States of America', 'UNITED STATES', 347, 9.834, SKY, 'Three',
     "Number three: the United States. Three hundred and forty-seven million. That sounds huge... but it's less than a quarter of number one.",
     ('quarter', '📊', 'LESS THAN 1/4 OF #1'), None),
    (2, 'm2', 'China', 'CHINA', 1420, 9.597, GOLD, 'point',
     "Number two: China. One point four two billion. It was number one for centuries, until 2023. Now its population is shrinking.",
     ('2023', '📉', '#1 UNTIL 2023 · NOW SHRINKING'), None),
    (1, 'm1', 'India', 'INDIA', 1460, 3.287, CORAL, 'point',
     "And number one: India. One point four six billion people. More than one in every six humans alive.",
     ('six', '🧍', '1 IN 6 HUMANS'), None),
]
BEATS = [
    ('h1', "Two countries hold more than a third of all the humans on Earth.", None, None, None, None, None),
    ('h2', "The biggest country in the world... doesn't even make the top eight.", None, None, None, None, None),
    ('h3', "And a country smaller than Florida has more people than all of Russia.", None, None, None, None, None),
    ('title', "These are the ten most populated countries, resized by people.", None, None, None, None, None),
] + [(e[1], e[8], None, None, None, None, None) for e in ENTRIES] + [
    ('cta', "Was your country on the list? Tell us in the comments, and follow for more.", None, None, None, None, None)]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2', 'h3')
bt, w = C.bt, C.w
G = None
CENTRE = {'Ethiopia': (40, 9), 'Russia': (98, 62), 'Bangladesh': (90.3, 23.8), 'Brazil': (-53, -11), 'Nigeria': (8, 9.5), 'Pakistan': (69.5, 30),
          'Indonesia': (118, -2.5), 'United States of America': (-98, 39), 'China': (104, 36), 'India': (79, 22)}
def factor(e): return math.sqrt((e[4] / e[5]) / WORLD_DENSITY)
def fmt(m): return f'{m / 1000:.2f} BILLION' if m >= 1000 else f'{int(m)} MILLION'

class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        self.raw, self.sh = {}, {}
        for n, c in CENTRE.items():
            rs = [r for r in rings(cf[n]['geometry']) if len(r) > 3]; self.raw[n] = rs
            sel = [r for r in rs if -126 < r[:, 0].mean() < -66 and 24 < r[:, 1].mean() < 50] if n == 'United States of America' else rs
            self.sh[n] = recentre(local(sel, *c))
        st = {f['properties']['name']: f for f in json.load(open(os.path.join(d, 'admin1_50m.geojson')))['features'] if f['properties'].get('admin') == 'United States of America'}
        self.sh['Florida'] = recentre(local([r for r in rings(st['Florida']['geometry']) if len(r) > 3], -82, 28))
        self.land = [r for f in json.load(open(os.path.join(d, 'land.geojson')))['features'] for r in rings(f['geometry']) if len(r) > 3]

def scaled(rs, f): return [r * f for r in rs]
def streaks(cr, a, col=(1, 1, 1)):
    """Motion streaks for the whip-pan."""
    if a <= 0: return
    rng = np.random.default_rng(9)
    for _ in range(26):
        y, wd, hh = rng.uniform(0, H), rng.uniform(300, 1000), rng.uniform(4, 22)
        cr.rectangle(rng.uniform(-200, W), y, wd, hh); cr.set_source_rgba(*col, 0.35 * a); cr.fill()
def shake(t, t0, amp=16, d=0.45):
    if t < t0: return 0.0, 0.0
    k = 1 - prog(t, t0, t0 + d); return amp * k * math.sin(t * 95), amp * k * math.cos(t * 81)

def dive(cr, t, name, col, t0, t1, prev, tilt):
    """Fly-through: the globe spins from the previous country and the camera dives toward this one."""
    k = ease_io(prog(t, t0, t0 + 0.9)); c0, c1 = CENTRE.get(prev, (20, 20)), CENTRE[name]
    d = (c1[0] - c0[0] + 180) % 360 - 180; lon, lat = c0[0] + d * k, lerp(c0[1], c1[1], k)
    z = 0.8 * (1 - 0.15 * math.sin(math.pi * k)) * math.exp(1.25 * prog(t, t0 + 0.3, t1) ** 1.6)
    cr.save(); cr.translate(540, 1000); cr.rotate(tilt * (1 - 0.5 * prog(t, t0, t1))); cr.translate(-540, -1000)
    globe(cr, 540, 1040, 400 * z, lon + 4 * prog(t, t0, t1), lat, name, col, ease_out(prog(t, t0 + 0.45, t0 + 0.8)))
    cr.restore()

def header(cr, t, e, a):
    rank, key, ne, name = e[:4]; col = e[6]; b = bt(key)
    k = prog(t, b['start'], b['start'] + 0.25); sc = lerp(2.4, 1, ease_out(k))
    cr.save(); cr.translate(160, 220); cr.rotate(-0.08); cr.scale(sc, sc)
    cr.new_path(); cr.arc(0, 0, 105, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], a * clamp(k * 3)); cr.fill()
    ptext(cr, f'#{rank}', 0, 34, 100 if rank < 10 else 84, INK, a * clamp(k * 3), sw=0, shadow=False); cr.restore()
    k2 = pop_k(t, b['l0'] + 0.5); cr.save(); cr.translate(620, 215); cr.scale(k2, k2); ptext(cr, name, 0, 0, fit(cr, name, 84, 660), WHITE, a, sw=10); cr.restore()
    for i in range(10):
        r_ = 10 - i; x = 120 + i * 93; on = r_ == rank; done = r_ > rank
        cr.new_path(); cr.arc(x, 1880, 20 if on else 13, 0, 2 * math.pi)
        cr.set_source_rgba(*(col[:3] if on else ((0.9, 0.9, 0.95) if done else (0.3, 0.3, 0.38))), 1); cr.fill()

def resize_shot(cr, t, e, tc, a):
    rank, key, ne, name, popm, ar, col = e[:7]; b = bt(key); f = factor(e)
    host = G.sh[ne]; x0, x1, y0, y1 = bounds(host); s = min(900 / ((x1 - x0) * max(1, f)), 760 / ((y1 - y0) * max(1, f)))
    cx, cy = 540, 960; tr = tc + 0.55; k = ease_io(prog(t, tr, tr + 0.9)); cur = lerp(1.0, f, k)
    sx, sy = shake(t, tr + 0.9, 18 if abs(f - 1) > 0.5 else 8)
    zoom = 1.0 + 0.05 * prog(t, tc, b['end']); tilt = (0.04 if rank % 2 else -0.04) * (1 - 0.5 * prog(t, tc, b['end']))
    cr.save(); cr.translate(cx + sx, cy + sy); cr.rotate(tilt); cr.scale(zoom, zoom); cr.translate(-cx, -cy)
    kp = pop_k(t, tc, 0.35); cr.save(); cr.translate(cx, cy); cr.scale(kp, kp); cr.translate(-cx, -cy)
    km_shape(cr, scaled(host, cur), cx, cy, s, col, a, glow=True)
    ga = a * ease_out(prog(t, tr, tr + 0.3))  # ghost: the real size stays behind as a dashed outline
    if ga > 0:
        km_path(cr, host, cx, cy, s); cr.set_dash([14, 10]); cr.set_source_rgba(1, 1, 1, 0.9 * ga); cr.set_line_width(3.5); cr.stroke(); cr.set_dash([])
        ptext(cr, 'REAL SIZE', cx, cy - (y1 - y0) * s / 2 - 22, 30, WHITE, ga, fam='Poppins ExtraBold', sw=5)
    cr.restore(); cr.restore()
    n = popm * ease_out(prog(t, tc, tc + 1.1))
    ptext(cr, fmt(n) if n > 0 else '', 620, 330, 62, col, a, sw=9)
    if t >= tr:
        txt = f'SIZED BY PEOPLE: ×{f:.1f}' if f >= 1 else f'SIZED BY PEOPLE: ÷{1 / f:.1f}'
        chip(cr, txt, 540, 1460, 46, col, INK, pop_k(t, tr + 0.5), a, em='👥')
    word, em, txt = e[9]; chip(cr, txt, 540, 1572, 42, WHITE, INK, pop_k(t, w(key, word)), a, em=em)

def draw_entry(cr, t, e, i):
    rank, key, ne = e[:3]; col = e[6]; b = bt(key)
    a = 1 - ease_io(prog(t, b['end'] - 0.15, b['end']))
    tc = w(key, e[7]) - (0.5 if e[7] == 'point' else 0.2)
    bg(cr, t, col)
    wp = 1 - ease_out(prog(t, b['start'], b['start'] + 0.28))  # whip-pan in from the right
    cr.save(); cr.translate(wp * W * 0.9, 0)
    if t < tc: dive(cr, t, ne, col, b['start'], tc, ENTRIES[i - 1][2] if i else 'India', -0.06 if rank % 2 else 0.06)
    else: resize_shot(cr, t, e, tc, a)
    cr.restore(); streaks(cr, wp)
    if t >= tc:
        fl = 1 - prog(t, tc, tc + 0.14)
        if 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.6 * fl); cr.paint()
    g = cairo.LinearGradient(0, 0, 0, 520); g.add_color_stop_rgba(0, 0, 0, 0.03, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.03, 0); cr.rectangle(0, 0, W, 520); cr.set_source(g); cr.fill()
    g = cairo.LinearGradient(0, 1380, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.03, 0); g.add_color_stop_rgba(0.4, 0, 0, 0.03, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.03, 0.95)
    cr.rectangle(0, 1380, W, 540); cr.set_source(g); cr.fill()
    header(cr, t, e, a)
    if e[10] and t >= b['l1'] - 0.9:  # a tease for what is coming, so nobody swipes away
        k = pop_k(t, b['l1'] - 0.9); cr.save(); cr.translate(540, 480); cr.rotate(-0.02); cr.scale(k, k); fs = fit(cr, e[10], 44, 900); wd = tw(cr, e[10], fs)
        rrect(cr, -wd / 2 - 36, -58, wd + 72, 86, 43); cr.set_source_rgba(*CRIMSON[:3], a); cr.fill(); ptext(cr, e[10], 0, 4, fs, WHITE, a, sw=0, shadow=False); cr.restore()

def draw_hook(cr, t):
    if t >= bt('title')['start']: return False
    b = next(bt(k) for k in ('h1', 'h2', 'h3') if t < bt(k)['end'] + 1e-6); key = b['key']
    if key == 'h1':  # split screen: India | China, both sized by people at one scale
        for i, (n, col, x) in enumerate((('India', CORAL, 270), ('China', GOLD, 810))):
            cr.rectangle(i * 540, 0, 540, H); cr.set_source_rgb(*[0.05 + 0.16 * c for c in col[:3]]); cr.fill()
            e = next(e for e in ENTRIES if e[2] == n); f = factor(e) * lerp(0.2, 1, ease_out(prog(t, 0.0, 0.7)))
            km_shape(cr, scaled(G.sh[n], f), x, 1060, 0.058, col, 1, glow=True)
            ptext(cr, e[3], x, 1420, 70, WHITE, 1, sw=9)
            ptext(cr, fmt(e[4] * ease_out(prog(t, 0.05, 1.6))), x, 1510, 46, col, 1, sw=7)
        cr.rectangle(536, 0, 8, H); cr.set_source_rgb(1, 1, 1); cr.fill()
        slam(cr, '2 COUNTRIES', 540, 250, 140, WHITE, t, 0.03)
        slam(cr, '1/3 OF ALL HUMANS', 540, 400, 100, GOLD, t, w('h1', 'third') - 0.15)
    elif key == 'h2':
        bg(cr, t, SKY); e = ENTRIES[1]; host = G.sh['Russia']; x0, x1, y0, y1 = bounds(host); s = 940 / (x1 - x0)
        td = w('h2', 'doesn'); f = lerp(1, factor(e), ease_io(prog(t, td, td + 0.7))); sx, sy = shake(t, td, 22)
        cr.save(); cr.translate(sx, sy); km_shape(cr, scaled(host, f), 540, 1000, s, SKY, 1, glow=True)
        if t >= td: km_path(cr, host, 540, 1000, s); cr.set_dash([14, 10]); cr.set_source_rgba(1, 1, 1, 0.8); cr.set_line_width(3); cr.stroke(); cr.set_dash([])
        cr.restore()
        slam(cr, 'BIGGEST COUNTRY', 540, 250, 110, WHITE, t, w('h2', 'biggest'))
        if t >= td: emoji(cr, '❌', 540, 1000, 320 * pop_k(t, td), 0.9)
        slam(cr, 'NOT EVEN TOP 8', 540, 400, 120, CRIMSON, t, td)
    else:
        bg(cr, t, CORAL); s = 0.62; tm = w('h3', 'more'); e = ENTRIES[2]
        f = lerp(1, 2.6, ease_io(prog(t, tm, tm + 0.7))); sx, sy = shake(t, tm + 0.7, 22)
        cr.save(); cr.translate(sx, sy)
        km_shape(cr, G.sh['Florida'], 540, 1040, s, (0.85, 0.87, 0.92), ease_out(prog(t, w('h3', 'Florida') - 0.2, w('h3', 'Florida') + 0.2)), fill=0.9, lw=3, edge=INK)
        km_shape(cr, scaled(G.sh['Bangladesh'], f), 540, 1040, s, CORAL, 1, glow=True, fill=0.9)
        cr.restore()
        if t < tm: ptext(cr, 'FLORIDA', 540, 1040 + 330, 44, WHITE, ease_out(prog(t, w('h3', 'Florida'), w('h3', 'Florida') + 0.2)), sw=6)
        slam(cr, 'SMALLER THAN FLORIDA', 540, 250, 92, WHITE, t, w('h3', 'smaller'))
        slam(cr, 'MORE PEOPLE THAN RUSSIA', 540, 390, 80, CORAL, t, tm)
    wp = 1 - ease_out(prog(t, b['start'], b['start'] + 0.22))
    if key != 'h1': streaks(cr, wp); fl = 1 - prog(t, b['start'], b['start'] + 0.14); cr.set_source_rgba(1, 1, 1, 0.6 * max(fl, 0)); cr.paint()
    return True

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end']): return False
    bg(cr, t, GOLD)
    cr.save(); cr.translate(540, 1000); cr.rotate(0.03); cr.translate(-540, -1000)
    globe(cr, 540, 1300, 520 * (1 + 0.05 * prog(t, b['start'], b['end'])), 60 + 40 * prog(t, b['start'], b['end']), 25, None); cr.restore()
    cr.set_source_rgba(0, 0, 0.03, 0.5); cr.paint()
    k = pop_k(t, w('title', 'ten') - 0.1); cr.save(); cr.translate(540, 560); cr.scale(k, k); ptext(cr, 'THE 10', 0, 0, 190, GOLD, 1, sw=16); cr.restore()
    slam(cr, 'MOST POPULATED', 540, 760, 106, WHITE, t, w('title', 'most'))
    slam(cr, 'COUNTRIES', 540, 890, 120, WHITE, t, w('title', 'countries'))
    tt = w('title', 'resized')
    if t >= tt: chip(cr, 'RESIZED BY PEOPLE', 540, 1060, 62, GOLD, INK, pop_k(t, tt), 1, em='👥')
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22)))
    return True

def draw_cta(cr, t):
    b = bt('cta'); bg(cr, t, GOLD)
    globe(cr, 540, 1300, 520, 60 + 30 * (t - b['start']), 25, None); cr.set_source_rgba(0, 0, 0.03, 0.55); cr.paint()
    k = pop_k(t, w('cta', 'Was')); cr.save(); cr.translate(540, 520); cr.scale(k, k)
    ptext(cr, 'WAS YOUR COUNTRY', 0, 0, 92, WHITE, 1, sw=12); ptext(cr, 'ON THE LIST?', 0, 140, 130, GOLD, 1, sw=13); cr.restore()
    tc = w('cta', 'comments')
    if t >= tc: k = pop_k(t, tc); cr.save(); cr.translate(540, 1000); cr.scale(k, k); ptext(cr, 'COMMENT BELOW', -50, 0, 66, WHITE, 1, sw=9); emoji(cr, '👇', 330, -20, 80, 1); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1200); cr.scale(k, k); txt = 'FOLLOW FOR MORE'; wd = tw(cr, txt, 56)
        rrect(cr, -wd / 2 - 90, -62, wd + 180, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 56, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 66, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def render_frame(cr, t):
    if draw_hook(cr, t) or draw_title(cr, t):
        C.draw_captions(cr, t, 1700); return
    if t >= bt('cta')['start']: draw_cta(cr, t); C.draw_captions(cr, t, 1640)
    else:
        i = next((i for i, e in enumerate(ENTRIES) if bt(e[1])['start'] <= t < bt(e[1])['end']), len(ENTRIES) - 1)
        draw_entry(cr, t, ENTRIES[i], i); C.draw_captions(cr, t, 1740)
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR; rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 124; bar = beat * 4
    chords = [[52, 55, 59], [48, 52, 55], [55, 59, 62], [50, 54, 57]]  # Em C G D
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar * 1.2 * SR)) / SR; env = np.minimum(1, Lc / 0.2) * np.exp(-Lc * 0.7)
        put(music, ci * bar, sum(0.03 * (np.sin(2 * np.pi * note(m) * Lc) + 0.4 * np.sin(2 * np.pi * note(m + 12) * 1.003 * Lc)) for m in ch) * env)
        put(music, ci * bar, 0.09 * np.sin(2 * np.pi * note(ch[0] - 24) * Lc) * env)
        for j in range(8):
            m = ch[(j * 2) % 3] + 12 + (12 if j % 4 == 2 else 0); P = np.arange(int(0.2 * SR)) / SR
            put(music, ci * bar + j * beat / 2, 0.025 * np.sign(np.sin(2 * np.pi * note(m) * P)) * np.exp(-P * 18))
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 > bt('cta')['start'] + 3: break
        Ld = np.arange(int(0.35 * SR)) / SR; put(music, t0, 0.38 * np.sin(2 * np.pi * np.cumsum(55 + 70 * np.exp(-Ld * 22)) / SR) * np.exp(-Ld * 9))
        M = np.arange(int(0.05 * SR)); put(music, t0 + beat / 2, 0.05 * rng.standard_normal(len(M)) * np.exp(-M / SR * 60))
        if bi % 2 == 1: M = np.arange(int(0.12 * SR)); put(music, t0, 0.07 * rng.standard_normal(len(M)) * np.exp(-M / SR * 30))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.6):
        Lb = np.arange(int(1.6 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-Lb * 10)) / SR) * np.exp(-Lb * 2.8))
    def whoosh(t0, amp=0.28, d=0.45):
        nz = rng.standard_normal(int(d * SR)); env = np.linspace(0, 1, len(nz)) ** 2; put(fx, t0, amp * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def ding(t0, amp=0.09):
        Ld = np.arange(int(0.8 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * 1318 * Ld) + 0.5 * np.sin(2 * np.pi * 1976 * Ld)) * np.exp(-Ld * 5))
    def stretch(t0, up, amp=0.12):
        Ls = np.arange(int(0.9 * SR)) / SR; f = (200 + 500 * Ls / 0.9) if up else (700 - 500 * Ls / 0.9)
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * Ls / 0.9))
    boom(0.03, 0.8); boom(w('h1', 'third'), 0.6); boom(w('h2', 'doesn'), 0.8); stretch(w('h2', 'doesn'), False); stretch(w('h3', 'more'), True); boom(w('h3', 'more') + 0.7, 0.8)
    for key in ('h2', 'h3', 'title'): whoosh(bt(key)['start'] - 0.4)
    boom(w('title', 'ten'), 0.7)
    for e in ENTRIES:
        b = bt(e[1]); whoosh(b['start'] - 0.4); boom(b['start'] + 0.05, 0.55 if e[0] > 1 else 0.95)
        tc = w(e[1], e[7]) - (0.5 if e[7] == 'point' else 0.2); whoosh(tc - 0.3, 0.3, 0.3); boom(tc, 0.4)
        stretch(tc + 0.55, factor(e) >= 1); boom(tc + 1.45, 0.5); ding(w(e[1], e[9][0]), 0.07)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    global G
    C.TL = C.build(C.WordVoice(cache)); G = Geo(data_dir); B.G = G

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    data_dir, out = sys.argv[1:3]
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_popu'))
    print(f"duration {C.TL['dur']:.1f}s", {e[3]: round(factor(e), 2) for e in ENTRIES})
    for b in C.TL['beats']: print(f"  {b['key']:8s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','): render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
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
