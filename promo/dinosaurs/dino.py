"""'The Day the Dinosaurs Died' (9:16): the Chicxulub impact, from zero seconds to the long night, on a 3D globe.
Narrator (en-GB Ryan) with word-synced visuals and captions (timing engine from china.py).
Usage: python3 dino.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON, PARCH
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

FIRE, LAVA, OCEAN, ASH = hexc('#FF8A1F'), hexc('#FF3B1F'), hexc('#2E8BFF'), hexc('#8A8F98')
IMPACT = (-89.5, 21.3)
C.SAY = {None: {}}
C.HOT = ('dinosaurs', 'asteroid', 'bullet', 'everest', 'chicxulub', 'crater', 'billion', 'tsunami', 'fire', 'forests', 'sulfur', 'charcoal',
         'sunlight', 'extinct', 'mammals', 'birds', 'dinosaur', 'mexico', 'seconds', 'minutes', 'day', 'years', 'months', 'quake')
BEATS = [
    ('h1', "Sixty-six million years ago, a rock the size of Mount Everest hit the Earth.", None, None, None, None, None),
    ('h2', "It was moving twenty times faster than a bullet.", None, None, None, None, None),
    ('h3', "And within twenty-four hours, the world of the dinosaurs was gone.", None, None, None, None, None),
    ('title', "This is the day the dinosaurs died.", None, None, None, None, None),
    ('zero', "Zero seconds. The asteroid, about ten kilometres wide, slams into the sea off Mexico, near today's town of Chicxulub.",
     None, None, None, ('I', 'IMPACT'), None),
    ('blast', "It releases more energy than a billion atomic bombs. In seconds, it blasts a crater a hundred and eighty kilometres wide.", None, None, None, None, None),
    ('quake', "Minutes later, an earthquake far stronger than any in human history shakes the planet.", None, None, None, ('II', 'THE FIRST HOUR'), None),
    ('fire', "Molten rock is thrown into space, and rains back down all over the globe. Scientists think it heated the sky, and set forests on fire.", None, None, None, None, None),
    ('wave', "In the Gulf of Mexico, a tsunami over a kilometre high races out across the oceans.", None, None, None, None, None),
    ('core', "Within a day, the crater was buried under a hundred and thirty metres of rock. In 2016, scientists drilled into it... and found charcoal from burning forests.",
     None, None, None, ('III', 'THE FIRST DAY'), None),
    ('sulfur', "They also found almost no sulfur. The impact had vaporised it, filling the sky with gas and soot.", None, None, None, None, None),
    ('dark', "Sunlight was blocked for months, maybe years. Plants stopped growing. Temperatures plunged.", None, None, None, ('IV', 'THE LONG NIGHT'), None),
    ('die', "About three quarters of all species on Earth went extinct... including every dinosaur that couldn't fly.", None, None, None, None, None),
    ('twist', "But some survived: small mammals, our distant ancestors... and birds.", None, None, None, None, None),
    ('birds', "Which means the dinosaurs never fully disappeared. One of them might be outside your window right now.", None, None, None, None, None),
    ('cta', "Would you have survived? Tell us in the comments, and follow for more.", None, None, None, None, None),
]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2', 'h3')
bt, w, win = C.bt, C.w, C.win
LAND = None
CLOCK = [('zero', 'Zero', 'T + 0 SECONDS'), ('blast', 'seconds', 'T + 10 SECONDS'), ('quake', 'Minutes', 'T + 5 MINUTES'),
         ('fire', 'Molten', 'T + 30 MINUTES'), ('wave', 'tsunami', 'T + 1 HOUR'), ('core', 'Within', 'T + 24 HOURS'),
         ('dark', 'Sunlight', 'T + MONTHS'), ('die', 'About', 'T + YEARS')]

# ---------- globe ----------
def load_land(d):
    out = []
    for f in json.load(open(os.path.join(d, 'land.geojson')))['features']:
        out += [r for r in rings(f['geometry']) if len(r) > 3]
    return out

def ortho(lon, lat, lon0, lat0):
    l, p, l0, p0 = np.radians(lon), np.radians(lat), math.radians(lon0), math.radians(lat0)
    cosc = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l - l0)
    x = np.cos(p) * np.sin(l - l0); y = -(math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l - l0))
    r = np.hypot(x, y); hid = cosc < 0
    x = np.where(hid, x / np.maximum(r, 1e-9), x); y = np.where(hid, y / np.maximum(r, 1e-9), y)  # hidden points sit on the limb
    return x, y, cosc

def globe(cr, cx, cy, R, lon0, lat0, t, land_col=(0.32, 0.55, 0.3), sea=(0.1, 0.3, 0.6), dark=0.0, ash=0.0):
    g = cairo.RadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R)
    g.add_color_stop_rgb(0, *[lerp(v, 0.08, dark) for v in (sea[0] + 0.15, sea[1] + 0.15, sea[2] + 0.15)]); g.add_color_stop_rgb(1, *[lerp(v, 0.02, dark) for v in sea])
    cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.set_source(g); cr.fill()
    cr.save(); cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.clip()
    cr.new_path()
    for r in LAND:
        x, y, cc = ortho(r[:, 0], r[:, 1], lon0, lat0)
        if (cc < 0).all(): continue
        cr.move_to(cx + x[0] * R, cy + y[0] * R)
        for a, b in zip(x[1:], y[1:]): cr.line_to(cx + a * R, cy + b * R)
        cr.close_path()
    cr.set_source_rgb(*[lerp(v, 0.12, dark) for v in land_col]); cr.fill()
    if ash > 0: cr.set_source_rgba(0.35, 0.33, 0.32, 0.75 * ash); cr.paint()
    g = cairo.RadialGradient(cx - R * 0.35, cy - R * 0.4, R * 0.05, cx, cy, R * 1.02)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.18); g.add_color_stop_rgba(0.6, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    cr.set_source(g); cr.paint(); cr.restore()
    cr.new_path(); cr.arc(cx, cy, R + 6, 0, 2 * math.pi); cr.set_source_rgba(0.5, 0.75, 1, 0.35 * (1 - dark)); cr.set_line_width(8); cr.stroke()

def gpt(cx, cy, R, lon, lat, lon0, lat0):
    x, y, cc = ortho(np.array([lon]), np.array([lat]), lon0, lat0); return cx + x[0] * R, cy + y[0] * R, cc[0]

def ring_on_globe(cr, cx, cy, R, lon0, lat0, ang, col, width, a):
    """A circle of angular radius `ang` (degrees) around the impact, drawn on the sphere."""
    if a <= 0 or ang <= 0: return
    lam0, ph0 = map(math.radians, IMPACT); d = math.radians(ang); pts = []
    for b in np.linspace(0, 2 * math.pi, 140):
        ph = math.asin(math.sin(ph0) * math.cos(d) + math.cos(ph0) * math.sin(d) * math.cos(b))
        lam = lam0 + math.atan2(math.sin(b) * math.sin(d) * math.cos(ph0), math.cos(d) - math.sin(ph0) * math.sin(ph))
        pts.append((math.degrees(lam), math.degrees(ph)))
    pts = np.array(pts); x, y, cc = ortho(pts[:, 0], pts[:, 1], lon0, lat0)
    cr.save(); cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.clip(); cr.new_path()
    pen = False
    for xi, yi, c in zip(x, y, cc):
        if c < 0: pen = False; continue
        (cr.line_to if pen else cr.move_to)(cx + xi * R, cy + yi * R); pen = True
    cr.set_source_rgba(*col[:3], a); cr.set_line_width(width); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke(); cr.restore()

def asteroid(cr, x, y, r, t, trail=0.0, ang=-0.75):
    if trail > 0:
        cr.save(); cr.translate(x, y); cr.rotate(ang)
        g = cairo.LinearGradient(0, 0, -r * 8 * trail, 0); g.add_color_stop_rgba(0, 1, 0.6, 0.15, 0.95); g.add_color_stop_rgba(1, 1, 0.2, 0.05, 0)
        cr.new_path(); cr.move_to(0, -r * 0.95); cr.line_to(-r * 8 * trail, 0); cr.line_to(0, r * 0.95); cr.close_path(); cr.set_source(g); cr.fill(); cr.restore()
    rng = np.random.default_rng(7); cr.new_path()
    for i in range(18):
        a = i / 18 * 2 * math.pi; rr = r * (0.85 + 0.15 * rng.random()); (cr.move_to if i == 0 else cr.line_to)(x + rr * math.cos(a), y + rr * math.sin(a))
    cr.close_path(); g = cairo.RadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r); g.add_color_stop_rgb(0, 0.55, 0.5, 0.45); g.add_color_stop_rgb(1, 0.2, 0.18, 0.17)
    cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(1, 0.55, 0.2, 0.8 * trail); cr.set_line_width(5); cr.stroke()
    for cx_, cy_, cr_ in ((-0.3, -0.2, 0.18), (0.25, 0.3, 0.14), (0.3, -0.35, 0.1)):
        cr.new_path(); cr.arc(x + cx_ * r, y + cy_ * r, cr_ * r, 0, 2 * math.pi); cr.set_source_rgba(0.1, 0.09, 0.09, 0.6); cr.fill()

def space(cr, t, glow=0.0):
    cr.set_source_rgb(0.01, 0.01, 0.03); cr.paint()
    rng = np.random.default_rng(3)
    for _ in range(160):
        x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.6)
        cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.4 + 0.4 * math.sin(t * 2 + x)); cr.fill()
    if glow > 0: cr.set_source_rgba(1, 0.45, 0.1, 0.25 * glow); cr.paint()

def flash(cr, t, t0, d=0.3, col=(1, 1, 1), a=0.8):
    f = 1 - prog(t, t0, t0 + d)
    if t >= t0 and f > 0: cr.set_source_rgba(*col, a * f); cr.paint()

def shake(t, t0, amp=18, d=0.8):
    if t < t0: return 0, 0
    k = 1 - prog(t, t0, t0 + d); return amp * k * math.sin(t * 90), amp * k * math.cos(t * 77)

# ---------- hook ----------
def draw_hook(cr, t):
    if t >= bt('title')['start']: return False
    b = next(x for x in (bt('h1'), bt('h2'), bt('h3')) if t < x['end'] + 1e-6)
    key = b['key']
    if key == 'h1':
        space(cr, t)
        k = prog(t, b['start'], b['end'])
        globe(cr, 540, 1650 + 200 * (1 - k), 900, -85, 20, t)
        te = w('h1', 'Everest')
        asteroid(cr, lerp(900, 640, k), lerp(380, 700, k), 120, t, 0.6 + 0.4 * k)
        if t >= te:  # size comparison
            kk = pop_k(t, te); cr.save(); cr.translate(250, 860); cr.scale(kk, kk)
            cr.new_path(); cr.move_to(-150, 120); cr.line_to(-40, -110); cr.line_to(0, -60); cr.line_to(40, -130); cr.line_to(150, 120); cr.close_path()
            cr.set_source_rgb(0.45, 0.42, 0.4); cr.fill(); cr.new_path(); cr.move_to(-40, -110); cr.line_to(-15, -72); cr.line_to(0, -60); cr.line_to(40, -130); cr.line_to(70, -70); cr.line_to(10, -40); cr.close_path()
            cr.set_source_rgb(0.95, 0.95, 1); cr.fill(); ptext(cr, 'EVEREST: 8.8 KM', 0, 180, 40, WHITE, 1, sw=6); cr.restore()
            ptext(cr, 'ASTEROID: ~10 KM', 760, 920, 40, FIRE, pop_k(t, te + 0.2), sw=6)
        slam(cr, '66 MILLION', 540, 220, 130, GOLD, t, w('h1', 'Sixty'))
        slam(cr, 'YEARS AGO', 540, 340, 90, WHITE, t, w('h1', 'years'))
    elif key == 'h2':
        space(cr, t, 0.3)
        tb = w('h2', 'bullet'); k = prog(t, b['start'], b['end'])
        # the race: a bullet crawls, the asteroid streaks
        for y, lab in ((820, 'BULLET · ~1 KM/S'), (1180, 'ASTEROID · ~20 KM/S')):
            cr.new_path(); cr.move_to(80, y); cr.line_to(1000, y); cr.set_dash([14, 14]); cr.set_source_rgba(1, 1, 1, 0.25); cr.set_line_width(3); cr.stroke(); cr.set_dash([])
            ptext(cr, lab, 540, y - 70, 46, WHITE, 1, sw=7)
        xb = lerp(100, 160, k); cr.save(); cr.translate(xb, 820); rrect(cr, -40, -14, 80, 28, 14); cr.set_source_rgb(0.85, 0.7, 0.3); cr.fill(); cr.restore()
        xa = lerp(120, 1250, ease_io(prog(t, b['l0'], b['l1'])))
        asteroid(cr, xa, 1180, 70, t, 1.0, 0.0)
        slam(cr, '20× FASTER', 540, 400, 150, FIRE, t, w('h2', 'twenty'))
        slam(cr, 'THAN A BULLET', 540, 1500, 100, WHITE, t, tb)
    else:
        th = w('h3', 'hours'); tg = w('h3', 'gone')
        sx, sy = shake(t, b['start'], 30, 1.0)
        cr.save(); cr.translate(sx, sy)
        space(cr, t, 1.0)
        globe(cr, 540, 1050, 420, -89, 21, t, dark=prog(t, tg - 0.3, tg + 0.5))
        x, y, _ = gpt(540, 1050, 420, *IMPACT, -89, 21)
        g = cairo.RadialGradient(x, y, 5, x, y, 420); g.add_color_stop_rgba(0, 1, 1, 0.85, 1); g.add_color_stop_rgba(0.3, 1, 0.55, 0.1, 0.8); g.add_color_stop_rgba(1, 1, 0.2, 0, 0)
        cr.set_source(g); cr.paint()
        cr.restore()
        flash(cr, t, b['start'], 0.5, a=1.0)
        if t >= th: slam(cr, '24 HOURS', 540, 340, 170, WHITE, t, w('h3', 'twenty'))
        if t >= tg:
            for i, e in enumerate('🦖🦕🦖'):
                emoji(cr, e, 270 + i * 270, 1650, 150 * pop_k(t, tg + i * 0.08), 1)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            k = ease_out(prog(t, tg + 0.3, tg + 0.5))
            if k > 0:
                cr.move_to(140, 1560); cr.line_to(lerp(140, 940, k), lerp(1560, 1740, k)); cr.set_source_rgba(*LAVA[:3], 1); cr.set_line_width(22); cr.stroke()
    return True

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end'] + 0.2): return False
    space(cr, t, 0.6)
    globe(cr, 540, 1500, 620, -89, 21, t, dark=0.5, ash=0.4)
    x, y, _ = gpt(540, 1500, 620, *IMPACT, -89, 21)
    g = cairo.RadialGradient(x, y, 5, x, y, 380); g.add_color_stop_rgba(0, 1, 0.9, 0.6, 1); g.add_color_stop_rgba(0.4, 1, 0.4, 0.05, 0.7); g.add_color_stop_rgba(1, 1, 0.2, 0, 0)
    cr.set_source(g); cr.paint()
    s0 = b['start']
    k = pop_k(t, w('title', 'day') - 0.1); cr.save(); cr.translate(540, 520); cr.scale(k, k); ptext(cr, 'THE DAY THE', 0, 0, 96, WHITE, 1, sw=12); cr.restore()
    slam(cr, 'DINOSAURS', 540, 700, 180, FIRE, t, w('title', 'dinosaurs'))
    slam(cr, 'DIED', 540, 900, 220, LAVA, t, w('title', 'died'))
    flash(cr, t, w('title', 'died'), 0.3, (1, 0.6, 0.3), 0.5)
    return True

# ---------- main scenes ----------
def view(t):
    """Globe placement and rotation per part of the story."""
    lon0, lat0, R, cy = -89, 21, 520, 980
    if t >= bt('quake')['start']: lon0 = -89 + 40 * ease_io(prog(t, bt('quake')['start'], bt('wave')['start']))
    if t >= bt('wave')['start']: lon0 = lerp(-49, -80, ease_io(prog(t, bt('wave')['start'], bt('wave')['start'] + 1.5))); lat0 = 15
    if t >= bt('dark')['start']: lon0 = -80 + 30 * prog(t, bt('dark')['start'], bt('die')['end'])
    return lon0, lat0, R, cy

def draw_main(cr, t):
    lon0, lat0, R, cy = view(t)
    tz = w('zero', 'slams')
    dark = ease_io(prog(t, w('dark', 'Sunlight'), w('dark', 'plunged', end=True)))
    ash = max(ease_io(prog(t, w('sulfur', 'filling'), w('sulfur', 'soot', end=True))) * 0.8, dark)
    sx, sy = shake(t, tz, 26, 1.2)
    sx2, sy2 = shake(t, w('quake', 'shakes'), 20, 1.6)
    cr.save(); cr.translate(sx + sx2, sy + sy2)
    space(cr, t, 0.15)
    zoomed = bt('zero')['start'] <= t < bt('quake')['start']
    if zoomed:  # the Gulf of Mexico, close up
        Rz = 2200; cyz = 980 + 2200 * 0.0
        globe(cr, 540, 980, Rz, -89.5, 21.3, t)
        x, y = 540, 980
        if t < tz:
            k = prog(t, bt('zero')['l0'], tz)
            asteroid(cr, lerp(1150, x, ease_io(k)), lerp(-150, y, ease_io(k)), lerp(30, 12, k), t, 1.0)
        else:
            g = cairo.RadialGradient(x, y, 5, x, y, 600); g.add_color_stop_rgba(0, 1, 1, 0.9, 1); g.add_color_stop_rgba(0.25, 1, 0.55, 0.1, 0.9); g.add_color_stop_rgba(1, 1, 0.2, 0, 0)
            cr.set_source(g); cr.paint()
            tc = w('blast', 'crater')
            if t >= tc:
                km = 180 * ease_out(prog(t, tc, tc + 1.2)); rr = km / 2 / 6371 * Rz * 57.3 / 57.3
                rpx = km / 2 * (Rz / 6371)
                cr.new_path(); cr.arc(x, y, rpx, 0, 2 * math.pi); cr.set_source_rgba(0.15, 0.08, 0.05, 0.85); cr.fill_preserve()
                cr.set_source_rgba(1, 0.6, 0.2, 1); cr.set_line_width(6); cr.stroke()
                ptext(cr, f'{int(km)} KM', x, y - rpx - 30, 60, WHITE, 1, sw=8)
        lab_a = win('zero', t=t)
        if lab_a > 0:
            for name, lon, lat in (('MEXICO', -102, 23.5), ('YUCATÁN', -88.8, 19.0), ('USA', -97, 31)):
                px, py, cc = gpt(540, 980, Rz, lon, lat, -89.5, 21.3)
                if cc > 0: ptext(cr, name, px, py, 40, WHITE, 0.85 * lab_a, fam='Poppins ExtraBold', sw=6)
            tch = w('zero', 'Chicxulub')
            if t >= tch: ptext(cr, 'CHICXULUB', 540, 1140, 56, GOLD, pop_k(t, tch), sw=8)
    else:
        globe(cr, 540, cy, R, lon0, lat0, t, dark=dark * 0.8, ash=ash)
        x, y, cc = gpt(540, cy, R, *IMPACT, lon0, lat0)
        if cc > 0 and t < bt('dark')['start']:
            g = cairo.RadialGradient(x, y, 3, x, y, 120); g.add_color_stop_rgba(0, 1, 0.8, 0.4, 0.9); g.add_color_stop_rgba(1, 1, 0.3, 0, 0)
            cr.set_source(g); cr.paint()
        tq = w('quake', 'shakes') - 1.0
        if bt('quake')['start'] <= t < bt('fire')['end']:  # seismic waves race around the planet
            for i in range(3):
                ang = ((t - tq) * 25 + i * 30) % 180
                ring_on_globe(cr, 540, cy, R, lon0, lat0, ang, (1, 0.8, 0.4), 4, 0.6 * win('quake', 'fire', t=t) * (1 - ang / 180))
        if bt('fire')['start'] <= t < bt('wave')['end']:  # debris rains down, fires start
            tm, tf = w('fire', 'Molten'), w('fire', 'fire')
            rng = np.random.default_rng(11)
            for i in range(60):
                lon, lat = rng.uniform(-180, 180), rng.uniform(-60, 70); t0 = tm + rng.uniform(0, 3.0)
                k = prog(t, t0, t0 + 1.2)
                if 0 < k < 1:
                    px, py, c = gpt(540, cy, R * (1 + 0.6 * (1 - k)), lon, lat, lon0, lat0)
                    if c > 0:
                        cr.new_path(); cr.arc(px, py, 6, 0, 2 * math.pi); cr.set_source_rgba(1, 0.6 * (1 - k) + 0.3, 0.1, 1 - k * 0.5); cr.fill()
            if t >= tf:
                rng = np.random.default_rng(5)
                for i in range(26):
                    lon, lat = rng.uniform(-130, 40), rng.uniform(-35, 60)
                    px, py, c = gpt(540, cy, R, lon, lat, lon0, lat0)
                    land = any(True for _ in [0])
                    if c > 0.2: emoji(cr, '🔥', px, py, 44 * pop_k(t, tf + i * 0.04), win('fire', 'wave', t=t), rot=0.2 * math.sin(t * 6 + i))
        if bt('wave')['start'] <= t < bt('core')['start'] + 0.5:
            tt = w('wave', 'tsunami')
            ang = 60 * ease_out(prog(t, tt, bt('wave')['end'] + 0.5))
            ring_on_globe(cr, 540, cy, R, lon0, lat0, ang, OCEAN, 10, 0.9 * win('wave', t=t))
            ring_on_globe(cr, 540, cy, R, lon0, lat0, ang * 0.85, (0.6, 0.85, 1), 5, 0.7 * win('wave', t=t))
    cr.restore()

def draw_overlays(cr, t):
    # clock
    lab = None
    for key, word, txt in CLOCK:
        if t >= w(key, word) - 0.05: lab, t0 = txt, w(key, word) - 0.05
    if lab and t < bt('twist')['start']:
        k = pop_k(t, t0, 0.3); cr.save(); cr.translate(540, 290); cr.scale(k, k)
        wd = tw(cr, lab, 70); rrect(cr, -wd / 2 - 50, -70, wd + 100, 104, 52); cr.set_source_rgba(0.05, 0.02, 0.02, 0.85); cr.fill_preserve()
        cr.set_source_rgba(*FIRE[:3], 1); cr.set_line_width(4); cr.stroke()
        ptext(cr, lab, 0, 4, 70, GOLD if 'SEC' in lab or 'MIN' in lab else WHITE, 1, sw=0, shadow=False); cr.restore()
    # blast: a billion bombs
    a = win('blast', t=t)
    if a > 0:
        tb = w('blast', 'billion')
        if t >= tb:
            k = pop_k(t, tb); cr.save(); cr.translate(540, 1420); cr.scale(k, k)
            emoji(cr, '💣', -300, -10, 100, a); ptext(cr, '× 1,000,000,000', 60, 20, 80, GOLD, a, sw=10); cr.restore()
    # quake
    a = win('quake', t=t)
    if a > 0: chip(cr, 'STRONGER THAN ANY QUAKE IN HISTORY', 540, 1560, 40, WHITE, INK, pop_k(t, w('quake', 'stronger')), a)
    a = win('fire', t=t)
    if a > 0:
        chip(cr, 'DEBRIS RAINS DOWN WORLDWIDE', 540, 1560, 40, FIRE, INK, pop_k(t, w('fire', 'rains')), a, em='☄️')
    a = win('wave', t=t)
    if a > 0:
        tt = w('wave', 'kilometre')
        if t >= tt:
            k = pop_k(t, tt); cr.save(); cr.translate(540, 1480); cr.scale(k, k)
            for i, (hgt, lab, col) in enumerate(((1500, 'FIRST WAVE ~1.5 KM', OCEAN), (828, 'BURJ KHALIFA 828 M', ASH))):
                hh = hgt / 1500 * 170; x = -180 + i * 360
                rrect(cr, x - 70, -hh / 2, 140, hh, 10); cr.set_source_rgba(*col[:3], a); cr.fill()
                ptext(cr, lab, x, hh / 2 + 44, 30, WHITE, a, fam='Poppins ExtraBold', sw=5)
            cr.restore()
    # the drill core
    a = win('core', t=t)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.55 * a); cr.paint()
        tr = w('core', 'hundred'); td = w('core', 'drilled'); tc = w('core', 'charcoal')
        h_ = 760 * ease_out(prog(t, tr - 0.2, tr + 1.4))
        x0, y0 = 300, 520
        cols = [(0.45, 0.35, 0.28), (0.6, 0.5, 0.38), (0.35, 0.3, 0.27), (0.7, 0.6, 0.45), (0.25, 0.22, 0.2)]
        for i in range(10):
            seg = h_ / 10; rrect(cr, x0 - 70, y0 + i * seg, 140, seg + 1, 4); cr.set_source_rgba(*cols[i % 5], a); cr.fill()
        if h_ > 10: ptext(cr, '130 M', x0, y0 - 40, 56, GOLD, a, sw=8); ptext(cr, 'IN ONE DAY', x0, y0 + h_ + 60, 40, WHITE, a, sw=6)
        if t >= td:
            k = pop_k(t, td); cr.save(); cr.translate(740, 700); cr.scale(k, k)
            ptext(cr, '2016', 0, 0, 90, GOLD, a, sw=10); ptext(cr, 'DRILL CORE', 0, 70, 44, WHITE, a, sw=6); emoji(cr, '⛏️', 0, -120, 100, a); cr.restore()
        if t >= tc:
            k = pop_k(t, tc); cr.save(); cr.translate(740, 1100); cr.scale(k, k)
            cr.new_path(); cr.arc(0, 0, 80, 0, 2 * math.pi); cr.set_source_rgba(0.1, 0.1, 0.1, a); cr.fill_preserve(); cr.set_source_rgba(*FIRE[:3], a); cr.set_line_width(5); cr.stroke()
            emoji(cr, '🔥', 0, -6, 80, a); ptext(cr, 'CHARCOAL', 0, 140, 50, FIRE, a, sw=7); cr.restore()
    a = win('sulfur', t=t)
    if a > 0:
        ts = w('sulfur', 'sulfur')
        if t >= ts:
            k = pop_k(t, ts); cr.save(); cr.translate(540, 1480); cr.scale(k, k)
            wd = tw(cr, 'S', 120); rrect(cr, -90, -110, 180, 180, 24); cr.set_source_rgba(0.95, 0.85, 0.2, a); cr.fill()
            ptext(cr, 'S', 0, 10, 120, INK, a, sw=0, shadow=False)
            ptext(cr, 'SULFUR VAPORISED', 0, 140, 44, WHITE, a, sw=6); cr.restore()
            tv = w('sulfur', 'vaporised')
            if t >= tv:
                cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.move_to(410, 1300); cr.line_to(670, 1560); cr.set_source_rgba(*LAVA[:3], a); cr.set_line_width(14); cr.stroke()
    # the long night
    a = win('dark', t=t)
    if a > 0:
        for word, e, txt, x in (('Sunlight', '☀️', 'SUN BLOCKED', 190), ('Plants', '🥀', 'PLANTS DIE', 540), ('Temperatures', '🥶', 'FREEZING', 890)):
            te = w('dark', word)
            if t >= te:
                k = pop_k(t, te); emoji(cr, e, x, 1420, 120 * k, a * (0.5 if e == '☀️' and t > te + 0.8 else 1))
                ptext(cr, txt, x, 1540, 42, WHITE, a * k, sw=6)
    a = win('die', t=t)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.6 * a); cr.paint()
        sp = '🦖🦕🐢🦎🐊🐟🦑🐚🦈🌿🌳🐜🦂🦋🐀🐦'
        te = w('die', 'three'); tx = w('die', 'extinct')
        dead = {0, 1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13}  # turtles, crocodiles, mammals and birds pulled through
        for i, e in enumerate(sp):
            x, y = 180 + (i % 4) * 240, 640 + (i // 4) * 220
            if t < te + i * 0.03: continue
            emoji(cr, e, x, y, 110 * pop_k(t, te + i * 0.03), a * (0.35 if (i in dead and t >= tx) else 1))
            if i in dead and t >= tx + i * 0.02:
                k = ease_out(prog(t, tx + i * 0.02, tx + i * 0.02 + 0.15)); cr.set_line_cap(cairo.LINE_CAP_ROUND)
                cr.move_to(x - 60, y - 60); cr.line_to(x - 60 + 120 * k, y - 60 + 120 * k); cr.set_source_rgba(*LAVA[:3], a); cr.set_line_width(14); cr.stroke()
        slam(cr, '~75% OF SPECIES', 540, 1540, 100, LAVA, t, w('die', 'quarters'), a)
    a = win('twist', t=t)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.5 * a); cr.paint()
        for word, e, txt, x in (('mammals', '🐀', 'SMALL MAMMALS', 290), ('birds', '🐦', 'BIRDS', 790)):
            te = w('twist', word)
            if t >= te:
                k = pop_k(t, te); emoji(cr, e, x, 900, 220 * k, a); ptext(cr, txt, x, 1090, 56, WHITE, a * k, sw=8)
        tan = w('twist', 'ancestors')
        chip(cr, 'OUR ANCESTORS!', 290, 1220, 46, GOLD, INK, pop_k(t, tan), a)
        slam(cr, 'SURVIVORS', 540, 560, 140, (0.4, 1, 0.55), t, w('twist', 'survived'), a)
    a = win('birds', t=t)
    if a > 0:
        cr.set_source_rgba(0.02, 0.05, 0.08, 0.85 * a); cr.paint()
        td = w('birds', 'dinosaurs'); tw_ = w('birds', 'window')
        if t >= td:
            k = pop_k(t, td); emoji(cr, '🦖', 270, 980, 260 * k, a)
            if t >= td + 0.4:
                kk = pop_k(t, td + 0.4); cr.save(); cr.translate(540, 980); cr.scale(kk, kk); cr.new_path()
                cr.move_to(-70, -18); cr.line_to(20, -18); cr.line_to(20, -46); cr.line_to(80, 0); cr.line_to(20, 46); cr.line_to(20, 18); cr.line_to(-70, 18); cr.close_path()
                cr.set_source_rgba(*GOLD[:3], a); cr.fill(); cr.restore()
                emoji(cr, '🐔', 810, 980, 260 * pop_k(t, td + 0.6), a)
        slam(cr, 'BIRDS ARE DINOSAURS', 540, 620, 96, GOLD, t, w('birds', 'never'), a)
        if t >= tw_: emoji(cr, '🪟', 540, 1380, 160 * pop_k(t, tw_), a); emoji(cr, '🐦', 560, 1370, 80 * pop_k(t, tw_ + 0.2), a)

def draw_cta(cr, t):
    b = bt('cta')
    if t < b['start']: return
    a = ease_out(prog(t, b['start'], b['start'] + 0.4))
    cr.set_source_rgba(0.05, 0.02, 0.02, 0.75 * a); cr.paint()
    tq = w('cta', 'Would')
    k = pop_k(t, tq); cr.save(); cr.translate(540, 620); cr.scale(k, k)
    ptext(cr, 'WOULD YOU HAVE', 0, 0, 90, WHITE, a, sw=11); ptext(cr, 'SURVIVED?', 0, 140, 150, FIRE, a, sw=14); cr.restore()
    for i, (txt, col, d) in enumerate((('YES 💪', (0.3, 0.8, 0.4), 0.2), ('NO 💀', (0.9, 0.3, 0.3), 0.35))):
        if t < tq + d: continue
        kk = pop_k(t, tq + d) * (1 + 0.03 * math.sin(t * 6 + i)); cr.save(); cr.translate(310 + i * 460, 1000); cr.scale(kk, kk)
        rrect(cr, -190, -70, 380, 140, 70); cr.set_source_rgba(*col, 1); cr.fill(); ptext(cr, txt.split()[0], 0, 26, 76, WHITE, 1, sw=8); cr.restore()
    tc = w('cta', 'comments')
    if t >= tc:
        k = pop_k(t, tc); cr.save(); cr.translate(540, 1200); cr.scale(k, k)
        ptext(cr, 'COMMENT BELOW', -50, 0, 66, WHITE, 1, sw=9); emoji(cr, '👇', 330, -20, 80, 1); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1380); cr.scale(k, k)
        txt = 'FOLLOW FOR MORE'; wd = tw(cr, txt, 56)
        rrect(cr, -wd / 2 - 90, -62, wd + 180, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 56, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 66, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def render_frame(cr, t):
    if draw_hook(cr, t) or draw_title(cr, t):
        C.draw_captions(cr, t); flash(cr, t, bt('title')['start'], 0.2, a=0.7); return
    draw_main(cr, t)
    g = cairo.LinearGradient(0, 1450, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.8); cr.set_source(g); cr.paint()
    draw_overlays(cr, t)
    C.draw_chapter_label(cr, t) if t < bt('twist')['start'] else None
    C.draw_chapter_card(cr, t)
    draw_cta(cr, t)
    C.draw_captions(cr, t, 1700)
    tz = w('zero', 'slams'); flash(cr, t, tz, 0.6, (1, 0.95, 0.8), 1.0)
    flash(cr, t, w('fire', 'fire'), 0.3, (1, 0.5, 0.1), 0.35)
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- score ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(21)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); bar = 60 / 76 * 4
    chords = [[38, 45, 50, 53], [36, 43, 48, 51], [34, 41, 46, 50], [33, 40, 45, 49]]  # dark minor drones
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(bar * 1.4 * SR)) / SR
        env = np.minimum(1, L_ / 1.0) * np.exp(-L_ * 0.35)
        put(music, ci * bar, sum(0.03 * (np.sin(2 * np.pi * note(m) * L_) + 0.3 * np.sin(2 * np.pi * note(m + 12) * 1.003 * L_)) for m in ch) * env)
    beat = 60 / 76; t_end = bt('twist')['start']
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 < bt('title')['start'] or (t0 < t_end and bi % 2 == 0):
            L_ = np.arange(int(0.6 * SR)) / SR
            put(music, t0, 0.4 * np.sin(2 * np.pi * np.cumsum(50 + 60 * np.exp(-L_ * 18)) / SR) * np.exp(-L_ * 6))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.7, d=2.5):
        L_ = np.arange(int(d * SR)) / SR
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(30 + 80 * np.exp(-L_ * 8)) / SR) * np.exp(-L_ * 1.8))
        nz = rng.standard_normal(len(L_)); put(fx, t0, 0.3 * amp * np.convolve(nz, np.ones(40) / 40, 'same') * np.exp(-L_ * 2.5))
    def whoosh(t0, amp=0.2, d=0.9):
        nz = rng.standard_normal(int(d * SR)); env = np.linspace(0, 1, len(nz)) ** 2
        put(fx, t0, amp * np.convolve(nz, np.ones(20) / 20, 'same') * env)
    def rumble(t0, d, amp=0.25):
        L_ = np.arange(int(d * SR)) / SR; nz = rng.standard_normal(len(L_))
        put(fx, t0, amp * np.convolve(nz, np.ones(400) / 400, 'same') * 8 * np.sin(np.pi * L_ / d))
    whoosh(0.0, 0.3, 1.5); boom(w('h1', 'hit'), 0.6)
    whoosh(bt('h2')['start'] - 0.3, 0.35); boom(w('h2', 'bullet'), 0.6)
    boom(bt('h3')['start'], 1.0, 4.0); boom(w('h3', 'gone'), 0.7)
    boom(w('title', 'died'), 1.0, 4.0)
    whoosh(w('zero', 'slams') - 0.9, 0.4); boom(w('zero', 'slams'), 1.1, 5.0)
    boom(w('blast', 'crater'), 0.6); rumble(w('quake', 'earthquake'), 4.0, 0.35); boom(w('quake', 'shakes'), 0.7)
    rumble(w('fire', 'rains'), 3.0, 0.2); whoosh(w('wave', 'tsunami') - 0.4, 0.4, 1.5); boom(w('die', 'extinct'), 0.7)
    for b in T['beats']:
        if b['chap'] and b['key'] != 'zero': boom(b['start'] + 0.1, 0.4)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    global LAND
    C.TL = C.build(C.WordVoice(cache)); LAND = load_land(data_dir)

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    data_dir, out = sys.argv[1:3]
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_dino'))
    TL = C.TL; print(f"duration {TL['dur']:.1f}s")
    for b in TL['beats']: print(f"  {b['key']:8s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','):
            render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]
    make_audio(TL, base + '.wav')
    nfr = int(TL['dur'] * FPS); workers = os.cpu_count() or 4
    bounds = np.linspace(0, nfr, workers * 3 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
