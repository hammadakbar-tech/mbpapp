# "GTA 6 Is Finally Here: the 13-Year Wait" (9:16 news short, word-synced narration).
# Countdown concept, dates and palette from github.com/andresjosehr/gta6launchday (target Nov 19 2026, progress since Nov 6 2025).
# No official Rockstar artwork or logo fonts are used.
# Usage: python3 gta6.py <data_dir> <out.mp4> [--preview t1,t2,...]
import json, math, os, ssl, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import edge_tts.communicate as _etc
if os.path.exists('/root/.ccr/ca-bundle.crt'): _etc._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
import china as C
from big import local, bounds
from popu import streaks, shake
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, WHITE, INK, CRIMSON
from vs import face
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, hexc, SR

# palette from the repo's :root
PINK, CREAM, PURPLE = hexc('#ffb0c4')[:3], hexc('#fff9cb')[:3], hexc('#5c1663')[:3]
HOTPINK, CYAN, RED, GREEN = hexc('#ff4fa0')[:3], hexc('#4ff0ff')[:3], hexc('#ff3355')[:3], hexc('#3dff8f')[:3]
C.VOICE, C.RATE = 'en-US-GuyNeural', '+6%'
BEATS = [
    ('h1', "Thirteen years of waiting. Two delays."),
    ('h2', "And on day one: over two billion dollars."),
    ('h3', "GTA 6 is finally here. This is the whole story."),
    ('b1', "September 2013. GTA 5 launches, and makes eight hundred million dollars in a single day."),
    ('b2', "It hits one billion in three days, and goes on to sell over two hundred million copies."),
    ('b3', "Then... years of silence. Fans get nothing but rumours and memes."),
    ('b4', "February 2022. Rockstar finally confirms the next Grand Theft Auto is in development."),
    ('b5', "That September, a hacker leaks ninety videos of early footage. One of the biggest leaks in gaming history."),
    ('b6', "December 2023. Trailer one. Ninety million YouTube views in twenty-four hours. A world record."),
    ('b7', "The setting: Leonida, a state inspired by Florida. And yes, Vice City is back."),
    ('b8', "The plan was fall 2025. Then, delay number one: May 2026."),
    ('b9', "Trailer two drops. Four hundred and seventy-five million views in one day, across every platform."),
    ('b10', "Then, delay number two: November nineteenth, 2026."),
    ('b11', "Seventy-nine ninety-nine. PlayStation 5 and Xbox Series only. PC players still have to wait."),
    ('b12', "And yesterday, the countdown finally hit zero."),
    ('b13', "Sensor Tower estimates around twenty-four million copies sold on day one."),
    ('b14', "Two point three six billion dollars. Almost three times GTA 5's record."),
    ('b15', "Thirteen years, two months and two days after GTA 5."),
    ('cta', "Did you buy it on day one? Tell me in the comments, and follow for more.")]
C.BEATS = [(k, s, None, None, None, None, None) for k, s in BEATS]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {'GTA 6': 'GTA six', 'GTA 5': 'GTA five', "GTA 5's": "GTA five's"}}
C.HOT = ('gta', 'thirteen', 'delays', 'billion', 'million', 'record', 'leonida', 'vice', 'city', 'delay', 'zero', 'leaks', 'trailer', 'comments')
C.TAIL_OVERRIDE = {'h1': 0.15, 'h2': 0.2, 'h3': 0.35, 'b12': 0.6, 'b14': 0.4, 'b15': 0.5, 'cta': 2.2}
bt, w = C.bt, C.w
YEAR = {'b1': 2013, 'b2': 2013, 'b3': 2017.5, 'b4': 2022, 'b5': 2022.7, 'b6': 2023.9, 'b7': 2023.9, 'b8': 2025.3, 'b9': 2025.35, 'b10': 2025.85,
        'b11': 2026.5, 'b12': 2026.88, 'b13': 2026.88, 'b14': 2026.88, 'b15': 2026.88, 'cta': 2026.88}
G = None

class Geo:
    def __init__(self, d):
        fl = next(f for f in json.load(open(os.path.join(d, 'admin1_50m.geojson')))['features'] if f['properties'].get('name') == 'Florida' and 'United States' in f['properties'].get('admin', ''))
        rs = [r for r in rings(fl['geometry']) if len(r) > 3]
        pr = local(rs, -83.5, 28.0); x0, x1, y0, y1 = bounds(pr); self.off = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        self.fl = [r - self.off for r in pr]; self.ext = (x1 - x0, y1 - y0)
    def pt(self, lon, lat): return local([np.array([[lon, lat]], float)], -83.5, 28.0)[0][0] - self.off

# ---------- look ----------
def cam(cr, z=1.0, tilt=0.0, fx=540, fy=960):
    cr.translate(540, 960); cr.rotate(tilt); cr.scale(z, z); cr.translate(-fx, -fy)
def push(t, a, b, z0, z1): return lerp(z0, z1, ease_out(prog(t, a, b)))
HZ = 1180
def palm(cr, x, base, h, lean, t, flip=1):
    sw = 0.04 * math.sin(t * 1.3 + x)
    tx, ty = x + flip * (lean + sw * 300), base - h
    cr.new_path(); cr.move_to(x - 14, base); cr.curve_to(x - 10, base - h * 0.4, tx - 30 * flip, ty + h * 0.3, tx - 6, ty); cr.line_to(tx + 6, ty)
    cr.curve_to(tx - 18 * flip, ty + h * 0.3, x + 10, base - h * 0.4, x + 14, base); cr.close_path(); cr.set_source_rgb(0.06, 0.0, 0.08); cr.fill()
    for k in range(7):
        ang = -math.pi / 2 + (k - 3) * 0.48 + sw * 2; L = h * 0.42
        ex, ey = tx + math.cos(ang) * L * 1.3, ty + math.sin(ang) * L * 0.55 + L * 0.35
        cr.new_path(); cr.move_to(tx, ty); cr.curve_to(tx + math.cos(ang) * L * 0.5, ty - L * 0.25, ex - math.cos(ang) * 20, ey - 40, ex, ey)
        cr.curve_to(ex - math.cos(ang) * 40, ey - 10, tx + math.cos(ang) * L * 0.4, ty - L * 0.05, tx, ty + 6); cr.close_path(); cr.fill()
def vice(cr, t, glow=1.0):
    g = cairo.LinearGradient(0, 0, 0, HZ); g.add_color_stop_rgb(0, 0.02, 0.0, 0.05); g.add_color_stop_rgb(0.55, *PURPLE); g.add_color_stop_rgb(1, 0.95, 0.38, 0.52)
    cr.rectangle(-400, -400, W + 800, HZ + 400); cr.set_source(g); cr.fill()
    rng = np.random.default_rng(7)
    for _ in range(70):
        x, y, s = rng.uniform(0, W), rng.uniform(0, 600), rng.uniform(0.8, 2.2); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.3 + 0.3 * math.sin(t * 2 + x)); cr.fill()
    sy = HZ - 40; r = 300
    g = cairo.LinearGradient(0, sy - r, 0, sy + r); g.add_color_stop_rgb(0, *CREAM); g.add_color_stop_rgb(0.5, 1, 0.62, 0.45); g.add_color_stop_rgb(1, *HOTPINK)
    cr.save(); cr.new_path(); cr.arc(540, sy, r, math.pi, 2 * math.pi); cr.close_path(); cr.clip(); cr.rectangle(0, sy - r, W, r); cr.set_source(g); cr.fill()
    for k in range(6):
        yy = sy - 18 - k * 34 + (t * 30) % 34; cr.rectangle(0, yy, W, 4 + k * 1.6); cr.set_source_rgb(*[c * 0.9 for c in (0.95, 0.38, 0.52)]); cr.fill()
    cr.restore()
    g = cairo.RadialGradient(540, sy, 50, 540, sy, 700); g.add_color_stop_rgba(0, 1, 0.5, 0.6, 0.35 * glow); g.add_color_stop_rgba(1, 1, 0.5, 0.6, 0); cr.set_source(g); cr.rectangle(-400, -400, W + 800, H + 800); cr.fill()
    cr.rectangle(-400, HZ, W + 800, H - HZ + 400); cr.set_source_rgb(0.07, 0.0, 0.1); cr.fill()
    cr.set_line_width(2.5)
    for k in range(12):
        f = ((k + (t * 1.2) % 1) / 12); y = HZ + (H - HZ + 200) * f * f
        cr.move_to(-400, y); cr.line_to(W + 400, y); cr.set_source_rgba(*HOTPINK, 0.25 + 0.6 * f); cr.stroke()
    for k in range(-12, 13):
        cr.move_to(540 + k * 30, HZ); cr.line_to(540 + k * 260, H + 200); cr.set_source_rgba(*HOTPINK, 0.45); cr.stroke()
    palm(cr, 60, HZ + 30, 520, 60, t, 1); palm(cr, 1030, HZ + 30, 470, 70, t + 1, -1); palm(cr, 170, HZ + 30, 330, 40, t + 2, 1)
def dim(cr, a=0.45): cr.set_source_rgba(0.02, 0.0, 0.05, a); cr.paint()
def neon(cr, s, x, y, size, col, a=1.0, fam='Poppins Black', rot=0.0):
    if a <= 0: return
    face(cr, size, fam); ext = cr.text_extents(s); cr.save(); cr.translate(x, y); cr.rotate(rot); x0 = -ext.x_advance / 2
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    for wd, al in ((size * 0.42, 0.10), (size * 0.22, 0.22), (size * 0.09, 0.75)):
        cr.new_path(); cr.move_to(x0, 0); cr.text_path(s); cr.set_source_rgba(*col, al * a); cr.set_line_width(wd); cr.stroke()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(s); cr.set_source_rgba(1, 1, 1, a); cr.fill(); cr.restore()
def nslam(cr, s, x, y, size, col, t, t0, rot=-0.03, maxw=980):
    if t < t0: return
    k = prog(t, t0, t0 + 0.2); sc = lerp(2.2, 1.0, ease_out(k)); sz = fit(cr, s, size, maxw)
    cr.save(); cr.translate(x + 10 * math.sin(t * 70) * (1 - prog(t, t0 + 0.2, t0 + 0.45)), y); cr.scale(sc, sc); neon(cr, s, 0, 0, sz, col, clamp(k * 3), rot=rot); cr.restore()
def stamp(cr, s, x, y, size, col, t, t0, rot=-0.12):
    if t < t0: return
    k = prog(t, t0, t0 + 0.18); sc = lerp(3.0, 1.0, ease_out(k)); face(cr, size, 'Poppins Black'); wd = cr.text_extents(s).x_advance
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(sc, sc)
    rrect(cr, -wd / 2 - 34, -size * 0.95, wd + 68, size * 1.3, 18); cr.set_source_rgba(*col, 0.15 * clamp(k * 3)); cr.fill_preserve(); cr.set_source_rgba(*col, clamp(k * 3)); cr.set_line_width(10); cr.stroke()
    ptext(cr, s, 0, 0, size, col, clamp(k * 3), sw=0, shadow=False); cr.restore()
def card(cr, s, y, col, t, t0, size=74):
    if t < t0: return
    k = pop_k(t, t0, 0.25); face(cr, size, 'Poppins Black'); wd = cr.text_extents(s).x_advance
    cr.save(); cr.translate(540, y); cr.scale(k, k); rrect(cr, -wd / 2 - 40, -size * 0.95, wd + 80, size * 1.35, 26); cr.set_source_rgba(0.04, 0.0, 0.07, 0.85); cr.fill_preserve()
    cr.set_source_rgba(*col, 1); cr.set_line_width(6); cr.stroke(); neon(cr, s, 0, 0, size, col); cr.restore()
def counter(cr, txt, x, y, size, col, a=1.0): neon(cr, txt, x, y, fit(cr, txt, size, 960), col, a)
def bar(cr, x, base, val, vmax, hmax, k, col, lab_top, lab_in, wd=220):
    hh = max(8, hmax * val / vmax * k); rrect(cr, x - wd / 2, base - hh, wd, hh, 20)
    g = cairo.LinearGradient(0, base - hh, 0, base); g.add_color_stop_rgb(0, *col); g.add_color_stop_rgb(1, *[c * 0.45 for c in col]); cr.set_source(g); cr.fill_preserve()
    cr.set_source_rgb(1, 1, 1); cr.set_line_width(4); cr.stroke()
    neon(cr, lab_top, x, base - hh - 26, 52, col, clamp(k * 2)); ptext(cr, lab_in, x, base + 50, 34, WHITE, 1, fam='Poppins ExtraBold', sw=6)
def countdown(cr, secs, pct, y, a=1.0, flash=0.0):
    """The repo's countdown block: four boxes (days, hours, minutes, seconds) and a progress bar."""
    d, rem = divmod(max(0, int(secs)), 86400); h, rem = divmod(rem, 3600); m, s = divmod(rem, 60)
    for i, (v, lab) in enumerate(((d, 'DAYS'), (h, 'HOURS'), (m, 'MINUTES'), (s, 'SECONDS'))):
        x = 165 + i * 250; rrect(cr, x - 108, y - 110, 216, 200, 24); cr.set_source_rgba(0.02, 0.0, 0.04, 0.85 * a); cr.fill_preserve()
        cr.set_source_rgba(*PINK, a); cr.set_line_width(4); cr.stroke()
        neon(cr, f'{v:02d}' if i else f'{v:03d}' if v >= 100 else f'{v:02d}', x, y + 20, 86 if i or v < 100 else 70, CREAM, a)
        ptext(cr, lab, x, y + 72, 24, PINK, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    rrect(cr, 60, y + 135, 960, 34, 17); cr.set_source_rgba(1, 1, 1, 0.12 * a); cr.fill()
    if pct > 0: rrect(cr, 60, y + 135, max(34, 960 * pct), 34, 17); cr.set_source_rgba(*PINK, a); cr.fill()
    ptext(cr, f'{pct * 100:.0f}%', 540, y + 162, 26, INK, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    if flash > 0: cr.set_source_rgba(1, 1, 1, 0.8 * flash); cr.paint()
def yearline(cr, t, key):
    if key not in YEAR: return
    keys = [k for k, _ in BEATS if k in YEAR]; i = keys.index(key); prev = YEAR[keys[i - 1]] if i else YEAR[key]
    b = bt(key); yv = lerp(prev, YEAR[key], ease_io(prog(t, b['start'], b['start'] + 0.7)))
    if key == 'b3': yv = lerp(2013.5, 2021.9, prog(t, b['l0'], b['l1']))
    x0, x1, y = 110, 970, 175; cr.set_line_width(4); cr.move_to(x0, y); cr.line_to(x1, y); cr.set_source_rgba(1, 1, 1, 0.35); cr.stroke()
    fx = lerp(x0, x1, (yv - 2013) / 14); cr.move_to(x0, y); cr.line_to(fx, y); cr.set_source_rgba(*PINK, 1); cr.set_line_width(6); cr.stroke()
    for yr in range(2013, 2028, 1):
        xx = lerp(x0, x1, (yr - 2013) / 14); cr.new_path(); cr.arc(xx, y, 4, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.5); cr.fill()
    cr.new_path(); cr.arc(fx, y, 14, 0, 2 * math.pi); cr.set_source_rgb(*CREAM); cr.fill()
    neon(cr, str(int(yv)), fx, y - 34, 40, CREAM)

# ---------- scenes ----------
def at(key, word, n=0): return w(key, word, n)
def h1(cr, t, b):
    sx, sy = shake(t, 0.75, 26, 0.5); cr.save(); cam(cr, push(t, 0, b['end'], 1.12, 1.0), -0.03, 540 + sx, 960 + sy); vice(cr, t); cr.restore(); dim(cr, 0.35)
    secs = max(0, 3 - t * 4); countdown(cr, secs, min(1, 0.9 + t * 0.15), 1180, 1, max(0, 1 - prog(t, 0.75, 1.0)) if t >= 0.75 else 0)
    nslam(cr, '13 YEARS', 540, 420, 190, CREAM, t, 0.0); nslam(cr, 'OF WAITING', 540, 560, 96, PINK, t, at('h1', 'waiting') - 0.15)
    td = at('h1', 'Two') - 0.1; stamp(cr, 'DELAYED', 330, 1120, 76, RED, t, td, -0.14); stamp(cr, 'DELAYED', 760, 1260, 76, RED, t, at('h1', 'delays') - 0.05, 0.1)
def h2(cr, t, b):
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.15), 0.03); vice(cr, t); cr.restore(); dim(cr, 0.5)
    k = ease_out(prog(t, at('h2', 'day'), at('h2', 'dollars') + 0.2)); v = 2_360_000_000 * k
    neon(cr, 'DAY ONE', 540, 600, 110, PINK, pop_k(t, b['start'], 0.3))
    counter(cr, f'${v:,.0f}', 540, 860, 130, CREAM)
    for j in range(14):
        ph = ((t - b['start']) * 0.8 + j / 14) % 1; emoji(cr, '💵', 80 + (j * 157) % 940, lerp(-80, 1900, ph), 80, clamp(k * 3), rot=j + t)
    if k > 0.95: ptext(cr, '* SENSOR TOWER ESTIMATE', 540, 960, 30, WHITE, 0.8, fam='Poppins ExtraBold', sw=5)
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.2)))
def h3(cr, t, b):
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.25, 1.0), 0.0); vice(cr, t, 1.6); cr.restore()
    nslam(cr, 'GTA 6', 540, 640, 260, CREAM, t, at('h3', 'GTA') - 0.1, rot=-0.02); nslam(cr, 'IS FINALLY HERE', 540, 800, 92, HOTPINK, t, at('h3', 'finally') - 0.1)
    f = 1 - prog(t, at('h3', 'GTA') - 0.1, at('h3', 'GTA') + 0.2)
    if t >= at('h3', 'GTA') - 0.1 and f > 0: cr.set_source_rgba(1, 1, 1, 0.8 * f); cr.paint()
def b1(cr, t, b):
    card(cr, 'SEPT 17, 2013', 520, CYAN, t, b['l0'] - 0.05); neon(cr, 'GTA V LAUNCHES', 540, 660, 70, PINK, pop_k(t, at('b1', 'launches'), 0.3) if t >= at('b1', 'launches') else 0)
    k = ease_out(prog(t, at('b1', 'eight') - 0.2, at('b1', 'dollars'))); bar(cr, 540, 1250, 800, 800, 400, k, CYAN, f'${int(800 * k)}M', 'DAY ONE')
def b2(cr, t, b):
    tb = at('b2', 'billion') - 0.1
    if t >= tb: card(cr, '$1 BILLION · 3 DAYS', 520, CREAM, t, tb, 70)
    tc = at('b2', 'two') - 0.2; k = ease_out(prog(t, tc, at('b2', 'copies') + 0.2))
    if t >= tc:
        for j in range(int(40 * k)): emoji(cr, '💿', 180 + (j % 8) * 103, 760 + (j // 8) * 92, 78, 1)
        counter(cr, f'{int(200 * k)}M+ COPIES', 540, 1330, 110, CYAN)
def b3(cr, t, b):
    yv = int(lerp(2014, 2021.99, prog(t, b['l0'], b['l1'])))
    neon(cr, str(yv), 540, 640, 230, CREAM); neon(cr, '...', 540, 760, 120, PINK)
    for j, em in enumerate(('🤡', '💀', '⏳', '😴', '🙃')):
        ph = ((t - b['start']) * 0.35 + j / 5) % 1; emoji(cr, em, 120 + j * 210, lerp(1500, 850, ph), 110, math.sin(math.pi * ph), rot=0.3 * math.sin(t * 2 + j))
    rrect(cr, 140, 1180, 800, 50, 25); cr.set_source_rgba(1, 1, 1, 0.15); cr.fill(); rrect(cr, 140, 1180, 800 * 0.99, 50, 25); cr.set_source_rgb(*PINK); cr.fill()
    ptext(cr, 'LOADING GTA 6 ... 99%', 540, 1290, 44, WHITE, 1, fam='Poppins ExtraBold', sw=7)
def check(cr, x, y, s, col):
    cr.new_path(); cr.move_to(x - s * 0.5, y); cr.line_to(x - s * 0.12, y + s * 0.38); cr.line_to(x + s * 0.55, y - s * 0.42)
    cr.set_source_rgb(*col); cr.set_line_width(s * 0.16); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
def b4(cr, t, b):
    card(cr, 'FEBRUARY 2022', 520, CYAN, t, b['l0'] - 0.05)
    tc = at('b4', 'confirms') - 0.1
    if t >= tc: stamp(cr, 'CONFIRMED', 540, 900, 110, GREEN, t, tc, -0.08); k = pop_k(t, tc + 0.2, 0.3); check(cr, 540, 1150, 220 * k, GREEN)
def thumb(cr, x, y, s, a):
    rrect(cr, x - s * 0.8, y - s * 0.45, s * 1.6, s * 0.9, 6); cr.set_source_rgba(0.15, 0.12, 0.2, a); cr.fill_preserve(); cr.set_source_rgba(*PINK, a * 0.8); cr.set_line_width(2); cr.stroke()
    cr.new_path(); cr.move_to(x - s * 0.15, y - s * 0.22); cr.line_to(x + s * 0.25, y); cr.line_to(x - s * 0.15, y + s * 0.22); cr.close_path(); cr.set_source_rgba(1, 1, 1, a); cr.fill()
def b5(cr, t, b):
    card(cr, 'SEPTEMBER 2022', 520, CYAN, t, b['l0'] - 0.05); tn = at('b5', 'ninety') - 0.1; k = prog(t, tn, at('b5', 'footage') + 0.3)
    for j in range(int(90 * k)): thumb(cr, 145 + (j % 10) * 88, 700 + (j // 10) * 60, 50, 1)
    if t >= tn: counter(cr, f'{int(90 * k)} VIDEOS', 540, 1330, 100, CREAM)
    stamp(cr, 'LEAKED', 540, 960, 150, RED, t, at('b5', 'leaks') - 0.05, -0.15)
def playbtn(cr, x, y, s, k):
    if k <= 0: return
    cr.save(); cr.translate(x, y); cr.scale(k, k); rrect(cr, -s, -s * 0.7, 2 * s, 1.4 * s, s * 0.35); cr.set_source_rgb(0.92, 0.1, 0.15); cr.fill()
    cr.new_path(); cr.move_to(-s * 0.3, -s * 0.38); cr.line_to(s * 0.45, 0); cr.line_to(-s * 0.3, s * 0.38); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill(); cr.restore()
def b6(cr, t, b):
    card(cr, 'DECEMBER 2023', 520, CYAN, t, b['l0'] - 0.05); nslam(cr, 'TRAILER 1', 540, 690, 100, PINK, t, at('b6', 'Trailer') - 0.1)
    tv = at('b6', 'Ninety') - 0.1; k = ease_out(prog(t, tv, at('b6', 'views') + 0.3)); playbtn(cr, 540, 910, 120, pop_k(t, tv - 0.3, 0.3) if t >= tv - 0.3 else 0)
    if t >= tv: counter(cr, f'{int(90 * k)}M VIEWS', 540, 1170, 110, CREAM); ptext(cr, 'YOUTUBE · FIRST 24 HOURS', 540, 1240, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
    tr = at('b6', 'record') - 0.1
    if t >= tr: emoji(cr, '🏆', 830, 880, 150 * pop_k(t, tr), 1, rot=0.1); stamp(cr, 'WORLD RECORD', 540, 1380, 70, CREAM, t, tr, -0.05)
def b7(cr, t, b):
    s = 0.85; tl = at('b7', 'Leonida') - 0.2; k = ease_out(prog(t, b['l0'], tl + 0.4))
    cr.save(); cr.translate(540, 980); cr.scale(lerp(0.6, 1.0, k), lerp(0.6, 1.0, k)); cr.translate(-540, -940)
    for wd, al, col in ((26, 0.15, HOTPINK), (12, 0.35, HOTPINK), (4, 1.0, CREAM)):
        cr.new_path()
        for r in G.fl:
            cr.move_to(540 + r[0, 0] * s, 940 - r[0, 1] * s)
            for x, y in r[1:]: cr.line_to(540 + x * s, 940 - y * s)
            cr.close_path()
        if wd == 26: cr.set_source_rgba(*PURPLE, 0.6 * k); cr.fill_preserve()
        cr.set_source_rgba(*col, al * k); cr.set_line_width(wd); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
    cr.restore()
    if t >= tl: nslam(cr, 'LEONIDA', 540, 460, 150, PINK, t, tl); ptext(cr, 'INSPIRED BY FLORIDA', 540, 545, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6)
    tv = at('b7', 'Vice') - 0.15
    if t >= tv:
        p = G.pt(-80.19, 25.76); x, y = 540 + p[0] * s, 940 - p[1] * s; kk = pop_k(t, tv)
        for j in range(3):
            ph = ((t - tv) * 0.8 + j / 3) % 1; cr.new_path(); cr.arc(x, y, 20 + 90 * ph, 0, 2 * math.pi); cr.set_source_rgba(*CYAN, 1 - ph); cr.set_line_width(5); cr.stroke()
        cr.new_path(); cr.arc(x, y, 18 * kk, 0, 2 * math.pi); cr.set_source_rgb(*CYAN); cr.fill()
        nslam(cr, 'VICE CITY', 700, y + 130, 100, CYAN, t, tv, rot=0.03); emoji(cr, '🌴', 330, y + 90, 110 * kk, 1)
def strike(cr, txt, y, col, t, t0, tx):
    a = 1.0 if t < tx + 0.4 else lerp(1.0, 0.45, prog(t, tx + 0.4, tx + 0.8)); neon(cr, txt, 540, y, 96, col, a)
    if t >= tx:
        k = ease_out(prog(t, tx, tx + 0.25)); wd = tw(cr, txt, 96) / 2 + 30
        for sgn in (1, -1):
            cr.move_to(540 - wd, y - 30 - sgn * 50); cr.line_to(lerp(540 - wd, 540 + wd, k), y - 30 - sgn * 50 + sgn * 100 * k); cr.set_source_rgb(*RED); cr.set_line_width(16); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
def b8(cr, t, b):
    neon(cr, 'ORIGINAL PLAN', 540, 560, 56, PINK, pop_k(t, b['l0'], 0.3)); strike(cr, 'FALL 2025', 720, CREAM, t, b['l0'], at('b8', 'delay') - 0.1)
    stamp(cr, 'DELAY #1', 540, 950, 110, RED, t, at('b8', 'delay') + 0.15, -0.1); nslam(cr, 'MAY 26, 2026', 540, 1220, 110, CYAN, t, at('b8', 'May') - 0.1)
def b9(cr, t, b):
    card(cr, 'MAY 2025', 520, CYAN, t, b['l0'] - 0.05); nslam(cr, 'TRAILER 2', 540, 690, 100, PINK, t, b['l0'] + 0.05)
    tv = at('b9', 'Four') - 0.1; k = ease_out(prog(t, tv, at('b9', 'views') + 0.3)); playbtn(cr, 540, 900, 110, pop_k(t, b['l0'], 0.3))
    if t >= tv: counter(cr, f'{int(475 * k)}M VIEWS', 540, 1170, 116, CREAM)
    ta = at('b9', 'every') - 0.1
    if t >= ta: chip(cr, 'ALL PLATFORMS · 24 HOURS', 540, 1280, 40, PINK, INK, pop_k(t, ta), 1)
def b10(cr, t, b):
    strike(cr, 'MAY 26, 2026', 640, CREAM, t, b['l0'], at('b10', 'delay') - 0.1)
    stamp(cr, 'DELAY #2', 540, 900, 110, RED, t, at('b10', 'two') - 0.05, 0.08); nslam(cr, 'NOV 19, 2026', 540, 1180, 130, CYAN, t, at('b10', 'November') - 0.1)
def tag(cr, x, y, s, k, txt):
    if k <= 0: return
    cr.save(); cr.translate(x, y); cr.rotate(-0.12); cr.scale(k, k)
    cr.new_path(); cr.move_to(-s, -s * 0.45); cr.line_to(s * 0.7, -s * 0.45); cr.line_to(s, 0); cr.line_to(s * 0.7, s * 0.45); cr.line_to(-s, s * 0.45); cr.close_path()
    cr.set_source_rgb(*CREAM); cr.fill_preserve(); cr.set_source_rgb(*HOTPINK); cr.set_line_width(8); cr.stroke(); cr.new_path(); cr.arc(s * 0.62, 0, s * 0.08, 0, 2 * math.pi); cr.set_source_rgb(*HOTPINK); cr.fill()
    ptext(cr, txt, -s * 0.1, s * 0.16, s * 0.42, INK, 1, sw=0, shadow=False); cr.restore()
def b11(cr, t, b):
    tag(cr, 540, 640, 260, pop_k(t, b['l0'] - 0.05, 0.3) if t >= b['l0'] - 0.05 else 0, '$79.99')
    for word, txt, y, col in (('PlayStation', 'PS5  ✓', 930, CYAN), ('Xbox', 'XBOX SERIES X|S  ✓', 1050, GREEN)):
        tt = at('b11', word) - 0.1
        if t >= tt: chip(cr, txt.replace('  ✓', ''), 540, y, 54, col, INK, pop_k(t, tt), 1)
    tp = at('b11', 'PC') - 0.1
    if t >= tp: stamp(cr, 'PC: NOT YET', 540, 1260, 90, RED, t, tp, -0.06)
def b12(cr, t, b):
    tz = at('b12', 'zero'); k = ease_io(prog(t, b['l0'], tz)); total = 378 * 86400
    secs = total * (1 - k); pct = k
    sx, sy = shake(t, tz, 30, 0.6); cr.save(); cr.translate(sx, sy)
    neon(cr, 'THE COUNTDOWN', 540, 640, 90, PINK); countdown(cr, secs, pct, 960, 1, max(0, 1 - prog(t, tz, tz + 0.35)) if t >= tz else 0)
    ptext(cr, 'NOV 6, 2025  TO  NOV 19, 2026', 540, 1220, 32, WHITE, 0.85, fam='Poppins ExtraBold', sw=5)
    nslam(cr, "IT'S HERE", 540, 1420, 150, CREAM, t, tz + 0.05); cr.restore()
def figs(cr, x0, y0, n, cols, col, dx=30, dy=44):
    for j in range(n):
        x, y = x0 + (j % cols) * dx, y0 + (j // cols) * dy
        cr.new_path(); cr.arc(x, y - 9, 8, 0, 2 * math.pi); cr.rectangle(x - 9, y, 18, 22); cr.set_source_rgb(*col); cr.fill()
def b13(cr, t, b):
    tt = at('b13', 'twenty') - 0.2; k = ease_out(prog(t, tt, at('b13', 'copies') + 0.3))
    figs(cr, 210, 620, int(50 * k), 10, PINK, 74, 76)
    counter(cr, f'{24.6 * k:.1f}M COPIES', 540, 1100, 120, CREAM); ptext(cr, 'EACH FIGURE ≈ 500,000 · DAY ONE', 540, 1180, 32, WHITE, 0.85, fam='Poppins ExtraBold', sw=5)
    ptext(cr, '* SENSOR TOWER ESTIMATE · NOT OFFICIAL', 540, 1260, 30, PINK, 0.9, fam='Poppins ExtraBold', sw=5)
def b14(cr, t, b):
    bar(cr, 300, 1250, 0.8, 2.36, 560, 1, CYAN, '$0.8B', 'GTA V · DAY 1')
    k = ease_out(prog(t, b['l0'], at('b14', 'dollars') + 0.2)); bar(cr, 780, 1250, 2.36, 2.36, 560, k, HOTPINK, f'${2.36 * k:.2f}B', 'GTA 6 · DAY 1 (EST.)')
    tx = at('b14', 'three') - 0.1
    if t >= tx: sx, sy = shake(t, tx, 14); cr.save(); cr.translate(sx, sy); nslam(cr, '≈ 3×', 330, 820, 170, CREAM, t, tx); cr.restore()
def b15(cr, t, b):
    for j, (num, lab, word) in enumerate((('13', 'YEARS', 'Thirteen'), ('2', 'MONTHS', 'months'), ('2', 'DAYS', 'days'))):
        tt = at('b15', word) - (0.1 if j == 0 else 0.4)
        if t < tt: continue
        x = 210 + j * 330; k = pop_k(t, tt, 0.3); cr.save(); cr.translate(x, 860); cr.scale(k, k)
        rrect(cr, -140, -170, 280, 300, 30); cr.set_source_rgba(0.03, 0.0, 0.06, 0.85); cr.fill_preserve(); cr.set_source_rgb(*PINK); cr.set_line_width(5); cr.stroke()
        neon(cr, num, 0, 20, 170, CREAM); ptext(cr, lab, 0, 95, 40, PINK, 1, fam='Poppins ExtraBold', sw=0, shadow=False); cr.restore()
    ta = at('b15', 'after') - 0.1
    if t >= ta: neon(cr, 'SEPT 2013  TO  NOV 2026', 540, 1140, 50, CYAN, pop_k(t, ta))
def cta(cr, t, b):
    nslam(cr, 'DID YOU BUY IT', 540, 560, 110, CREAM, t, b['l0'] - 0.05); nslam(cr, 'ON DAY ONE?', 540, 700, 130, HOTPINK, t, at('cta', 'day') - 0.1)
    tc = at('cta', 'comments') - 0.1
    if t >= tc:
        kk = pop_k(t, tc); emoji(cr, '🎮', 380, 950, 170 * kk, 1, rot=-0.15 + 0.08 * math.sin(t * 4)); emoji(cr, '👇', 700, 960, 150 * kk, 1, rot=0.1 * math.sin(t * 5))
        chip(cr, 'COMMENT: YES OR NOT YET', 540, 1180, 50, CREAM, INK, kk, 1)
    tf = at('cta', 'follow') - 0.1
    if t >= tf:
        kk = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1360); cr.scale(kk, kk); txt = 'FOLLOW FOR MORE'; wd = tw(cr, txt, 54)
        rrect(cr, -wd / 2 - 50, -70, wd + 100, 108, 54); cr.set_source_rgb(*HOTPINK); cr.fill(); ptext(cr, txt, 0, 4, 54, WHITE, 1, sw=0, shadow=False); cr.restore()
SCENE = {'h1': h1, 'h2': h2, 'h3': h3, 'b1': b1, 'b2': b2, 'b3': b3, 'b4': b4, 'b5': b5, 'b6': b6, 'b7': b7, 'b8': b8, 'b9': b9, 'b10': b10, 'b11': b11, 'b12': b12,
         'b13': b13, 'b14': b14, 'b15': b15, 'cta': cta}

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if key in ('h1', 'h2', 'h3'): SCENE[key](cr, t, b)
    else:
        i = [k for k, _ in BEATS].index(key); tilt = 0.03 * (1 if i % 2 else -1)
        cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.08), tilt, 540, 900 if i % 3 else 1000); vice(cr, t); cr.restore(); dim(cr, 0.5)
        cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.04), tilt * 0.4, 540, 960); SCENE[key](cr, t, b); cr.restore()
        yearline(cr, t, key)
        f = 1 - prog(t, b['start'], b['start'] + 0.12)
        if f > 0: cr.set_source_rgba(1, 1, 1, 0.45 * f); cr.paint()
        streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.18)))
    C.draw_captions(cr, t, 1690)
    fo = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if fo > 0: cr.set_source_rgba(0, 0, 0, fo); cr.paint()

def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); rng = np.random.default_rng(6); tt = np.arange(n) / SR
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 108; bar_ = beat * 4
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G, synthwave
    for ci in range(int(dur / bar_) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar_ * 1.1 * SR)) / SR; env = np.minimum(1, Lc / 0.3) * np.exp(-Lc * 0.5)
        pad = sum(0.022 * (np.sin(2 * np.pi * note(m) * Lc) + 0.4 * np.sin(2 * np.pi * note(m) * 1.005 * Lc)) for m in ch) * env; put(music, ci * bar_, pad)
        for j in range(8):  # bass eighths
            P = np.arange(int(beat / 2 * SR)) / SR; put(music, ci * bar_ + j * beat / 2, 0.09 * np.sign(np.sin(2 * np.pi * note(ch[0] - 24) * P)) * np.exp(-P * 9) * 0.6)
        for j in range(16):  # arpeggio
            m = ch[j % 3] + 12 + (12 if j % 8 >= 4 else 0); P = np.arange(int(beat / 4 * SR)) / SR; put(music, ci * bar_ + j * beat / 4, 0.022 * np.sin(2 * np.pi * note(m) * P) * np.exp(-P * 18))
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 > bt('cta')['start'] + 2: break
        Ld = np.arange(int(0.3 * SR)) / SR
        if bi % 2 == 0: put(music, t0, 0.38 * np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-Ld * 30)) / SR) * np.exp(-Ld * 12))
        else: put(music, t0, 0.16 * rng.standard_normal(len(Ld)) * np.exp(-Ld * 22))
        M = np.arange(int(0.04 * SR)); put(music, t0 + beat / 2, 0.04 * rng.standard_normal(len(M)) * np.exp(-M / SR * 80))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.6):
        Lb = np.arange(int(1.6 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-Lb * 10)) / SR) * np.exp(-Lb * 2.8))
    def whoosh(t0, amp=0.26, d=0.4):
        nz = rng.standard_normal(int(d * SR)); env = np.linspace(0, 1, len(nz)) ** 2; put(fx, t0, amp * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def ding(t0, amp=0.1, f=1568):
        Ld = np.arange(int(1.0 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * f * Ld) + 0.5 * np.sin(2 * np.pi * f * 2.76 * Ld)) * np.exp(-Ld * 5))
    def tick(t0, amp=0.08): M = np.arange(int(0.02 * SR)); put(fx, t0, amp * np.sin(2 * np.pi * 2200 * M / SR) * np.exp(-M / SR * 200))
    def thud(t0, amp=0.5):
        Lb = np.arange(int(0.25 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * 70 * Lb) * np.exp(-Lb * 18) + 0.15 * amp * rng.standard_normal(len(Lb)) * np.exp(-Lb * 40))
    for j in range(4): tick(j * 0.25)
    boom(0.0, 0.9); boom(0.75, 1.0); thud(w('h1', 'Two') - 0.1); thud(w('h1', 'delays') - 0.05)
    boom(bt('h2')['start'], 0.6); [tick(w('h2', 'day') + j * 0.05, 0.05) for j in range(20)]; ding(w('h2', 'dollars'))
    boom(w('h3', 'GTA') - 0.1, 1.0); whoosh(w('h3', 'GTA') - 0.5, 0.4, 0.45)
    for k, _ in BEATS[3:]: whoosh(bt(k)['start'] - 0.3)
    thud(w('b4', 'confirms') - 0.1); thud(w('b5', 'leaks') - 0.05, 0.6); ding(w('b6', 'record') - 0.1)
    thud(w('b8', 'delay') + 0.15, 0.6); thud(w('b10', 'two') - 0.05, 0.6); thud(w('b11', 'PC') - 0.1)
    tz = w('b12', 'zero')
    for j in range(int((tz - bt('b12')['l0']) / 0.1)): tick(bt('b12')['l0'] + j * 0.1, 0.05)
    boom(tz, 1.0); ding(tz + 0.05, 0.14); boom(w('b14', 'three') - 0.1, 0.8)
    v = np.zeros(n)
    for s0, a in T['clips']: put(v, s0, a / max(1e-6, np.abs(a).max()) * 0.9)
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    global G
    C.TL = C.build(C.WordVoice(cache)); G = Geo(data_dir)

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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_gta6'))
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
