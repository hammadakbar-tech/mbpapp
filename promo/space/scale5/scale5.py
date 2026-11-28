"""Scale of the Universe, Part 5: Black Holes (9:16). Six black holes at true scale (event-horizon diameter = 2GM/c^2 x 2):
Earth crushed (1.8 cm), the Sun crushed (5.9 km), a 10-solar-mass stellar black hole (59 km), Sagittarius A* (25 million km),
M87* (257 AU) and TON 618 (1,600 AU). One log-zoom camera; the hook is an infinite zoom that follows the Earth as it is crushed.
Same markers as Parts 3-4: level titles, the 'Screen:' ruler, word-synced chips and karaoke captions.
Usage: python3 scale5.py <data_dir> <out.mp4> [--preview t1,t2,...]
"""
import json, math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import vs
import space_choice as SC
from vs import ptext, rrect, tw, fit, face
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

def emoji(cr, e, *a, **k): vs.emoji(cr, e.replace('️', ''), *a, **k)

W, H, FPS = 1080, 1920, 30
CY = 860
SC.VOICE, SC.RATE = 'en-US-AvaNeural', '+4%'
WHITE, GOLD, CYAN, PINK, VIOLET = hexc('#FFFFFF'), hexc('#FFD60A'), hexc('#3DE0FF'), hexc('#FF4FA3'), hexc('#9B6BFF')
INK = (0.03, 0.02, 0.08)

BEATS = [
    ('hook', "If you crushed the entire Earth into a black hole... it would be about the size of a marble."),
    ('sun', "Crush the Sun, and you'd get a black hole just six kilometres wide... smaller than Mount Everest is tall."),
    ('stellar', "Real black holes are born when giant stars collapse. A typical one weighs about ten Suns, and it's around sixty kilometres across. That's big enough to swallow a whole city."),
    ('sgr', "Now, zoom out. At the heart of our galaxy sits Sagittarius A-star. It weighs four million Suns, and it's twenty-five million kilometres across... small enough to fit inside Mercury's orbit."),
    ('m87', "M87-star, the first black hole ever photographed, weighs six and a half billion Suns. Its event horizon is three times wider than Pluto's entire orbit."),
    ('ton', "And then there's TON six-eighteen. At around forty billion Suns, you could line up our whole solar system across it more than twenty times."),
    ('end', "And it's still not the limit. Astronomers think even bigger ones are out there, hiding in the dark."),
    ('cta', "So, which one blew your mind? Comment the number, and follow for Part 6."),
]

# ---------- sizes, in metres ----------
AU = 1.496e11
RS_SUN = 2953.0  # Schwarzschild radius of one solar mass
R_EARTH, RS_EARTH = 6.371e6, 8.87e-3
BH = {  # key: (Schwarzschild radius, name)
    'earth': (RS_EARTH, 'EARTH'), 'sun': (RS_SUN, 'THE SUN'), 'stellar': (10 * RS_SUN, 'STAR'),
    'sgr': (4.3e6 * RS_SUN, 'SGR A*'), 'm87': (6.5e9 * RS_SUN, 'M87*'), 'ton': (4.07e10 * RS_SUN, 'TON 618')}
COIN_X, COIN_R = 0.0245, 0.01325          # Canadian $1 coin, 26.5 mm
GROUND = RS_SUN                           # Everest stands on the line the Sun black hole rests on
EVEREST = [(4.2e3, 0), (6.5e3, -3.1e3), (7.4e3, -4.6e3), (8.6e3, -6.9e3), (9.3e3, -8.849e3), (10.1e3, -7.6e3), (11.0e3, -6.4e3),
           (12.4e3, -4.0e3), (14.6e3, -1.6e3), (16.5e3, 0)]
ORBITS = [('MERCURY', 0.387), ('VENUS', 0.723), ('EARTH', 1.0), ('MARS', 1.524), ('JUPITER', 5.2), ('SATURN', 9.58), ('URANUS', 19.2),
          ('NEPTUNE', 30.07), ('PLUTO', 39.5)]
TOR = (-79.38, 43.66)

class Geo:
    def __init__(self, d):
        def ll(path, keep):
            out = []
            for f in json.load(open(os.path.join(d, path)))['features']:
                g = f['geometry']; ps = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
                for p in ps:
                    r = np.array(p[0], float)
                    if keep(r): out.append(r)
            return out
        self.globe = ll('land.geojson', lambda r: len(r) > 3)
        near = lambda r: -84 < r[:, 0].mean() < -74 and 41 < r[:, 1].mean() < 47 or (r[:, 0].min() < -76 and r[:, 0].max() > -82 and r[:, 1].min() < 46 and r[:, 1].max() > 42)
        loc = lambda r: np.stack([(r[:, 0] - TOR[0]) * 111320 * math.cos(math.radians(TOR[1])), -(r[:, 1] - TOR[1]) * 110540], 1)
        self.tor_land = [loc(r) for r in ll('ne_50m_land.geojson', near)]
        self.tor_lakes = [loc(r) for r in ll('ne_50m_lakes.geojson', near)]

G = None
TL = None

# ---------- timeline ----------
_missing = set()
def build(voice):
    t, beats, clips = 0.0, [], []
    lead = {'hook': 0.3}; tail = {'hook': 0.6, 'end': 0.9, 'cta': 2.6, 'ton': 0.8}
    for key, text in BEATS:
        a, words = voice.get(text)
        b = dict(key=key, text=text, start=t, l0=t + lead.get(key, 0.35)); b['l1'] = b['l0'] + len(a) / SR
        b['words'] = [(b['l0'] + s, b['l0'] + e, x) for s, e, x in words]; b['tokens'] = text.split()
        clips.append((b['l0'], a)); t = b['l1'] + tail.get(key, 0.45); b['end'] = t; beats.append(b)
    return dict(beats=beats, by={b['key']: b for b in beats}, clips=clips, dur=t)
def bt(k): return TL['by'][k]
def w(key, word, n=0, end=False):
    q, hits = SC.norm(word), []
    for s, e, x in bt(key)['words']:
        if any(SC.norm(p).startswith(q) for p in x.split()): hits.append((s, e))
    if len(hits) > n: return hits[n][1] if end else hits[n][0]
    if (key, word) not in _missing: _missing.add((key, word)); print(f'  ! no word "{word}" in {key}', file=sys.stderr)
    return bt(key)['l0']
def pop_k(t, t0, d=0.35): return max(1e-3, ease_back(prog(t, t0, t0 + d), 2.6))
def during(t, k0, k1=None, fin=0.4, fout=0.4):
    a, b = bt(k0)['start'], bt(k1 or k0)['end']
    return ease_out(prog(t, a, a + fin)) * (1 - ease_io(prog(t, b - fout, b)))

# ---------- camera ----------
PX0, PX1 = 360.0, 150.0  # Earth's on-screen radius before / after the crush
def crush_k(t): return ease_io(prog(t, w('hook', 'crushed'), w('hook', 'marble')))
def earth_radius(t): return math.exp(lerp(math.log(R_EARTH), math.log(RS_EARTH), crush_k(t)))
def keys():
    s_m = PX1 / RS_EARTH
    return [
        (w('hook', 'marble'), s_m, (0.0, 0.0)), (w('hook', 'marble') + 0.8, 1080 / 0.062, (0.0105, 0.0)),
        (w('sun', 'Crush'), 1080 / 0.066, (0.0105, 0.0)), (w('sun', 'six', end=True) + 0.2, 1080 / 23e3, (4.3e3, -2.2e3)),
        (w('stellar', 'giant'), 1080 / 24e3, (4.3e3, -2.2e3)), (w('stellar', 'ten', end=True), 1080 / 150e3, (0.0, 8e3)),
        (w('sgr', 'zoom'), 1080 / 160e3, (0.0, 8e3)), (w('sgr', 'Sagittarius'), 1080 / (1.3 * AU), (0.0, 0.0)),
        (w('sgr', 'Mercury'), 1080 / (1.25 * AU), (0.0, 0.0)), (bt('m87')['start'] + 0.2, 1080 / (1.25 * AU), (0.0, 0.0)),
        (w('m87', 'photographed'), 1080 / (470 * AU), (0.0, 0.0)), (w('m87', 'Pluto'), 1080 / (450 * AU), (0.0, 0.0)),
        (bt('ton')['start'] + 0.1, 1080 / (450 * AU), (0.0, 0.0)), (w('ton', 'forty'), 1080 / (2650 * AU), (0.0, 0.0)),
        (bt('end')['start'] + 0.3, 1080 / (2600 * AU), (0.0, 0.0)), (bt('cta')['start'], 1080 / (6500 * AU), (0.0, 0.0)),
        (bt('cta')['end'], 1080 / (7000 * AU), (0.0, 0.0)),
    ]
def camera(t):
    tm = w('hook', 'marble')
    if t < tm:  # infinite zoom: the camera follows the Earth as it is crushed
        k = crush_k(t); px = lerp(PX0, PX1, k) * (1 + 0.01 * math.sin(t * 0.8))
        return px / earth_radius(t), (0.0, 0.0)
    K = TL['keys']
    for (t0, s0, c0), (t1, s1, c1) in zip(K, K[1:]):
        if t <= t1:
            k = ease_io(prog(t, t0, t1)); s = math.exp(lerp(math.log(s0), math.log(s1), k))
            c0, c1 = np.array(c0), np.array(c1)
            if s1 > s0 * 1.01: c = c1 - (c1 - c0) * s0 * (1 - k) / s
            elif s1 < s0 / 1.01: c = c0 - (c0 - c1) * s1 * k / s
            else: c = c0 + (c1 - c0) * k
            return s, (float(c[0]), float(c[1]))
    return K[-1][1], K[-1][2]

def SX(p, s, c): return W / 2 + (p[0] - c[0]) * s, CY + (p[1] - c[1]) * s

# ---------- drawing helpers ----------
rng = np.random.default_rng(5)
STARS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.5, 1.9), rng.uniform(0, 6.28)) for _ in range(260)]
WARP = [(rng.uniform(0, 2 * math.pi), rng.uniform(0, 1)) for _ in range(150)]
def glow(cr, x, y, r, col, a):
    if a <= 0 or r <= 0: return
    g = cairo.RadialGradient(x, y, 0, x, y, r); g.add_color_stop_rgba(0, *col[:3], a); g.add_color_stop_rgba(1, *col[:3], 0)
    cr.set_source(g); cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.fill()

def draw_bg(cr, t, s):
    cr.set_source_rgb(0.012, 0.01, 0.03); cr.paint()
    g = cairo.RadialGradient(540, CY, 0, 540, CY, 1150); g.add_color_stop_rgba(0, 0.25, 0.12, 0.45, 0.22); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    cr.set_source(g); cr.paint()
    for x, y, r, ph in STARS:
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.2 + 0.35 * math.sin(t * 1.3 + ph) ** 2); cr.fill()
    for th, ph in WARP:  # streaks fly inward while we zoom out
        u = (-math.log10(s) * 0.9 + ph + t * 0.01) % 1.0; r = 40 * math.exp(u * 3.9)
        x, y = 540 + r * math.cos(th), CY + r * math.sin(th)
        if -5 < x < W + 5 and -5 < y < H + 5:
            cr.new_path(); cr.arc(x, y, 0.8 + 2.2 * u, 0, 2 * math.pi); cr.set_source_rgba(0.8, 0.85, 1, 0.4 * math.sin(math.pi * u) ** 1.5); cr.fill()

def black_hole(cr, x, y, r, a=1.0, t=0.0, eht=False):
    """Event horizon of radius r px (true scale), with a decorative accretion glow and photon ring."""
    if a <= 0.01 or r > 4e6: return
    rr = max(r, 2.5)
    if rr * 3.2 < 4e6: glow(cr, x, y, rr * 3.2, (1.0, 0.45, 0.15), 0.28 * a)
    # photon ring, brighter on one side (Doppler beaming), like the Event Horizon Telescope images
    cr.save(); cr.translate(x, y)
    for i in range(48):
        a0 = 2 * math.pi * i / 48; br = 0.55 + 0.45 * math.sin(a0 - (0.3 if eht else 0.0) + (0 if eht else t * 0.4))
        cr.new_path(); cr.arc(0, 0, rr * 1.32, a0, a0 + 2 * math.pi / 48 + 0.01)
        cr.set_source_rgba(1.0, 0.55 + 0.35 * br, 0.2 + 0.4 * br, a * (0.55 + 0.45 * br)); cr.set_line_width(max(1.5, rr * (0.32 if eht else 0.18))); cr.stroke()
    cr.restore()
    cr.new_path(); cr.arc(x, y, rr, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, a); cr.fill()
    cr.new_path(); cr.arc(x, y, rr, 0, 2 * math.pi); cr.set_source_rgba(1, 0.75, 0.4, 0.55 * a); cr.set_line_width(max(1.0, rr * 0.03)); cr.stroke()

def size_label(cr, x, y, r, txt, a, side=1):
    """Dimension line across a black hole's diameter with its size."""
    if a <= 0.01 or r < 12: return
    yy = y + r + 46
    cr.new_path(); cr.move_to(x - r, yy); cr.line_to(x + r, yy); cr.set_source_rgba(1, 1, 1, 0.9 * a); cr.set_line_width(3); cr.stroke()
    for xe, d in ((x - r, 1), (x + r, -1)):
        cr.new_path(); cr.move_to(xe, yy - 12); cr.line_to(xe, yy + 12); cr.stroke()
    ptext(cr, txt, x, yy + 44, 38, WHITE, a, fam='Poppins ExtraBold', sw=6)

# ---------- scenes ----------
def draw_earth(cr, t, s, c):
    tm = w('hook', 'marble')
    if t > tm + 1.0: return
    k = crush_k(t); R = earth_radius(t) * s; x, y = SX((0, 0), s, c)
    dark = ease_io(prog(k, 0.55, 0.95))
    if dark < 1:
        lon0, lat0 = -80 + t * 6, 25.0
        cr.save(); cr.new_path(); cr.arc(x, y, R, 0, 2 * math.pi); cr.clip()
        g = cairo.RadialGradient(x - R * 0.3, y - R * 0.3, R * 0.1, x, y, R)
        g.add_color_stop_rgb(0, 0.15, 0.45, 0.85); g.add_color_stop_rgb(1, 0.03, 0.12, 0.35); cr.set_source(g); cr.paint()
        p0 = math.radians(lat0); cr.new_path()
        for r in G.globe:
            lo, la = np.radians(r[:, 0] - lon0), np.radians(r[:, 1])
            cosc = math.sin(p0) * np.sin(la) + math.cos(p0) * np.cos(la) * np.cos(lo)
            if (cosc > 0).sum() < 2: continue
            X = np.cos(la) * np.sin(lo); Y = math.cos(p0) * np.sin(la) - math.sin(p0) * np.cos(la) * np.cos(lo)
            nrm = np.maximum(np.hypot(X, Y), 1e-9); X = np.where(cosc > 0, X, X / nrm); Y = np.where(cosc > 0, Y, Y / nrm)
            cr.move_to(x + X[0] * R, y - Y[0] * R); [cr.line_to(x + a_ * R, y - b_ * R) for a_, b_ in zip(X[1:], Y[1:])]; cr.close_path()
        cr.set_source_rgb(0.3, 0.7, 0.35); cr.fill()
        sh = cairo.RadialGradient(x - R * 0.35, y - R * 0.35, R * 0.2, x, y, R * 1.05)
        sh.add_color_stop_rgba(0, 1, 1, 1, 0.12); sh.add_color_stop_rgba(0.7, 0, 0, 0, 0); sh.add_color_stop_rgba(1, 0, 0, 0, 0.55)
        cr.set_source(sh); cr.paint(); cr.restore()
        glow(cr, x, y, R * 1.12, (0.4, 0.7, 1.0), 0.25 * (1 - dark))
        if 0 < k < 1:  # crushing streaks
            for i in range(28):
                ang = i * 2 * math.pi / 28 + t; ph = (t * 2.2 + i * 0.37) % 1.0
                r0, r1 = R * (2.6 - 1.4 * ph), R * (1.9 - 1.4 * ph)
                cr.new_path(); cr.move_to(x + r0 * math.cos(ang), y + r0 * math.sin(ang)); cr.line_to(x + r1 * math.cos(ang), y + r1 * math.sin(ang))
                cr.set_source_rgba(0.7, 0.85, 1, 0.5 * (1 - ph) * math.sin(math.pi * k)); cr.set_line_width(3); cr.stroke()
    if dark > 0:
        black_hole(cr, x, y, R, dark * (1 - prog(t, bt('sun')['end'] - 0.3, bt('sun')['end'])), t)
    if t >= tm - 0.05:
        fl = 1 - prog(t, tm - 0.05, tm + 0.4)
        if fl > 0: cr.set_source_rgba(1, 0.9, 0.8, 0.45 * fl); cr.paint()

def draw_earth_bh(cr, t, s, c):
    tm = w('hook', 'marble')
    if t <= tm + 1.0: return
    x, y = SX((0, 0), s, c)
    black_hole(cr, x, y, RS_EARTH * s, 1 - prog(t, bt('sun')['start'] + 1.0, bt('sun')['start'] + 1.6), t)

def draw_coin(cr, t, s, c):
    tm = w('hook', 'marble'); a = ease_out(prog(t, tm + 0.3, tm + 0.8)) * (1 - prog(t, w('sun', 'Crush'), w('sun', 'Crush') + 0.6))
    if a <= 0.01: return
    x, y = SX((COIN_X, 0), s, c); r = COIN_R * s
    if r < 2: return
    g = cairo.RadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r)
    g.add_color_stop_rgba(0, 1, 0.9, 0.55, a); g.add_color_stop_rgba(1, 0.75, 0.55, 0.15, a)
    cr.new_path()
    for i in range(11):  # the loonie is an 11-sided coin
        ang = -math.pi / 2 + i * 2 * math.pi / 11; (cr.move_to if i == 0 else cr.line_to)(x + r * math.cos(ang), y + r * math.sin(ang))
    cr.close_path(); cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(0.55, 0.38, 0.08, a); cr.set_line_width(max(1, r * 0.04)); cr.stroke()
    ptext(cr, '$1', x, y + r * 0.2, r * 0.6, (0.55, 0.38, 0.08), a, sw=0, shadow=False)
    ptext(cr, 'CANADIAN $1 COIN', x, y + r + 60, 34, WHITE, a, fam='Poppins ExtraBold', sw=6)
    ptext(cr, '26.5 mm', x, y + r + 102, 30, (0.85, 0.9, 1.0), a, fam='Poppins ExtraBold', sw=5)
    bx, by = SX((0, 0), s, c)
    ptext(cr, 'EARTH AS A', bx, by + RS_EARTH * s * 1.55 + 50, 34, GOLD, a, fam='Poppins ExtraBold', sw=6)
    ptext(cr, 'BLACK HOLE: ~1.8 cm', bx, by + RS_EARTH * s * 1.55 + 92, 30, GOLD, a, fam='Poppins ExtraBold', sw=5)

def draw_sun_scene(cr, t, s, c):
    tg = w('stellar', 'giant')
    a = ease_out(prog(t, bt('sun')['start'], bt('sun')['start'] + 0.3)) * (1 - ease_io(prog(t, tg, tg + 0.6)))
    tb = w('sun', 'six')
    if a <= 0: return
    x, y = SX((0, 0), s, c)
    gx0, gy = SX((-20e3, GROUND), s, c); gx1, _ = SX((30e3, GROUND), s, c)
    cr.new_path(); cr.rectangle(gx0, gy, gx1 - gx0, H); cr.set_source_rgba(0.12, 0.1, 0.18, 0.9 * a); cr.fill()
    cr.new_path(); cr.move_to(gx0, gy); cr.line_to(gx1, gy); cr.set_source_rgba(1, 1, 1, 0.6 * a); cr.set_line_width(2); cr.stroke()
    te = w('sun', 'Everest'); ea = a * ease_out(prog(t, te - 0.2, te + 0.4))
    if ea > 0:
        P = [SX((px, GROUND + py), s, c) for px, py in EVEREST]
        cr.new_path(); cr.move_to(*P[0]); [cr.line_to(*q) for q in P[1:]]; cr.close_path()
        g = cairo.LinearGradient(0, P[4][1], 0, gy); g.add_color_stop_rgba(0, 0.75, 0.78, 0.9, ea); g.add_color_stop_rgba(1, 0.3, 0.3, 0.42, ea)
        cr.set_source(g); cr.fill()
        snow = [SX((px, GROUND + py), s, c) for px, py in EVEREST[2:7]]
        cr.new_path(); cr.move_to(*snow[0]); [cr.line_to(*q) for q in snow[1:]]; cr.close_path(); cr.set_source_rgba(1, 1, 1, 0.9 * ea); cr.fill()
        px_, py_ = SX((9.3e3, GROUND - 8.849e3), s, c)
        ptext(cr, 'MOUNT EVEREST', px_, py_ - 60, 36, WHITE, ea, fam='Poppins ExtraBold', sw=6)
        ptext(cr, '8.8 km tall', px_, py_ - 20, 32, (0.85, 0.9, 1.0), ea, fam='Poppins ExtraBold', sw=5)
    k = pop_k(t, w('sun', 'Sun'), 0.5) if t >= w('sun', 'Sun') else 0
    if k > 0.01:
        bx, by = SX((0, GROUND - RS_SUN), s, c)
        black_hole(cr, bx, by, RS_SUN * s * k, a, t)
        if t >= tb: size_label(cr, bx, by, RS_SUN * s, 'THE SUN: ~6 km', a * ease_out(prog(t, tb, tb + 0.4)))

def draw_toronto(cr, t, s, c):
    a = during(t, 'stellar', 'sgr', 0.1, 0.1) * clamp((0.03 - s) / 0.012) * clamp((s - 1.2e-3) / 0.8e-3)
    if a <= 0.01: return
    cr.new_path()
    for r in G.tor_land:
        X, Y = W / 2 + (r[:, 0] - c[0]) * s, CY + (r[:, 1] - c[1]) * s
        cr.move_to(X[0], Y[0]); [cr.line_to(p, q) for p, q in zip(X[1:], Y[1:])]; cr.close_path()
    cr.set_source_rgba(0.2, 0.32, 0.26, a); cr.fill()
    cr.new_path()
    for r in G.tor_lakes:
        X, Y = W / 2 + (r[:, 0] - c[0]) * s, CY + (r[:, 1] - c[1]) * s
        cr.move_to(X[0], Y[0]); [cr.line_to(p, q) for p, q in zip(X[1:], Y[1:])]; cr.close_path()
    cr.set_source_rgba(0.1, 0.3, 0.6, a); cr.fill_preserve(); cr.set_source_rgba(0.5, 0.75, 1, 0.6 * a); cr.set_line_width(2); cr.stroke()
    x, y = SX((0, 0), s, c)
    ptext(cr, 'LAKE ONTARIO', *SX((38e3, 34e3), s, c), 40, (0.7, 0.88, 1.0), a, fam='Poppins ExtraBold', sw=6)
    tb = w('stellar', 'ten')
    if t < tb:
        cr.new_path(); cr.arc(x, y, 9, 0, 2 * math.pi); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
        ptext(cr, 'TORONTO', x, y - 26, 40, WHITE, a, sw=7)
    else:
        k = pop_k(t, tb, 0.5); black_hole(cr, x, y, BH['stellar'][0] * s * k, a, t)
        ptext(cr, 'TORONTO', x, y - BH['stellar'][0] * s * 1.45 - 20, 40, WHITE, a, sw=7)
        ts = w('stellar', 'sixty')
        if t >= ts: size_label(cr, x, y, BH['stellar'][0] * s, '~60 km', a * ease_out(prog(t, ts, ts + 0.4)))

def draw_orbits(cr, t, s, c, a, names=()):
    if a <= 0.01: return
    x, y = SX((0, 0), s, c)
    glow(cr, x, y, max(10, 7e8 * s * 3), (1, 0.85, 0.4), 0.9 * a)
    cr.new_path(); cr.arc(x, y, max(3, 6.96e8 * s), 0, 2 * math.pi); cr.set_source_rgba(1, 0.92, 0.6, a); cr.fill()
    for name, au in ORBITS:
        r = au * AU * s
        if r < 6 or r > 3000: continue
        oa = a * clamp((r - 6) / 30)
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_dash([10, 8] if name == 'PLUTO' else [])
        cr.set_source_rgba(0.6, 0.8, 1, (0.85 if name in names else 0.35) * oa); cr.set_line_width(3 if name in names else 1.5); cr.stroke(); cr.set_dash([])
        if name in names and 20 < r < 900:
            ang = -math.pi / 4 if name != 'PLUTO' else -math.pi * 0.62
            ptext(cr, name + ("'S ORBIT" if name in ('MERCURY', 'PLUTO') else ''), x + r * math.cos(ang), y + r * math.sin(ang) - 14, 32, (0.75, 0.9, 1), oa, fam='Poppins ExtraBold', sw=5)

def draw_space_scenes(cr, t, s, c):
    x, y = SX((0, 0), s, c)
    # Sagittarius A* where the Sun is
    a = during(t, 'sgr', None, 0.4, 0.4) * clamp((60 - 6.96e8 * s) / 40)  # wait until the Sun is small on screen
    draw_orbits(cr, t, s, c, a, ('MERCURY', 'VENUS', 'EARTH'))
    tg = w('sgr', 'Sagittarius')
    if t >= tg and a > 0:
        r = BH['sgr'][0] * s * pop_k(t, tg, 0.5); black_hole(cr, x, y, r, a, t)
        tz = w('sgr', 'twenty')
        if t >= tz: size_label(cr, x, y, BH['sgr'][0] * s, '25 MILLION km', a * ease_out(prog(t, tz, tz + 0.4)))
    # M87* over the whole planetary system
    a = during(t, 'm87', None, 0.4, 0.4)
    draw_orbits(cr, t, s, c, a, ('PLUTO',))
    tm = w('m87', 'M87')
    if t >= tm and a > 0:
        ka = ease_out(prog(t, tm + 0.6, tm + 1.6))
        r = BH['m87'][0] * s; black_hole(cr, x, y, r, a * ka, t, eht=True)
        draw_orbits(cr, t, s, c, a * ka * 0.9, ('PLUTO',))
        ts = w('m87', 'three')
        if t >= ts: size_label(cr, x, y, r, '257 AU · 38 BILLION km', a * ease_out(prog(t, ts, ts + 0.4)))
    # TON 618, with solar systems lined up across it
    a = during(t, 'ton', 'end', 0.4, 0.4) * (1 - 0.0)
    if a > 0:
        tt = w('ton', 'TON'); k = pop_k(t, tt, 0.6) if t >= tt else 0
        rt = BH['ton'][0] * s
        if k > 0.01: black_hole(cr, x, y, rt * k, a, t)
        rm = BH['m87'][0] * s
        if t < tt + 0.8: black_hole(cr, x, y, rm, a * (1 - prog(t, tt, tt + 0.8)), t, eht=True)
        tl = w('ton', 'line')
        if t >= tl:  # 26-27 copies of Neptune's orbit across the event horizon
            d = 2 * 30.07 * AU * s; n = int(2 * BH['ton'][0] / (2 * 30.07 * AU))
            for i in range(n):
                ti = tl + i * 1.4 / n
                if t < ti: continue
                cx_ = x - rt + d / 2 + i * d; kk = pop_k(t, ti, 0.25)
                cr.new_path(); cr.arc(cx_, y, d / 2 * 0.92 * kk, 0, 2 * math.pi); cr.set_source_rgba(0.45, 0.8, 1.0, 0.95 * a); cr.set_line_width(2.5); cr.stroke()
                cr.new_path(); cr.arc(cx_, y, 2.2, 0, 2 * math.pi); cr.set_source_rgba(1, 0.9, 0.5, a); cr.fill()
            tw_ = w('ton', 'twenty')
            if t >= tw_:
                cnt = int(clamp((t - tw_) / 0.8) * n)
                ptext(cr, f'{cnt}× OUR SOLAR SYSTEM', x, y - 50, 44, (0.6, 0.9, 1.0), a, sw=8)
        if t >= tt + 0.4: size_label(cr, x, y, rt, '~1,600 AU · 240 BILLION km', a * ease_out(prog(t, tt + 0.4, tt + 0.9)))
    # the end: bigger ones, maybe
    tb = w('end', 'bigger'); a = during(t, 'end', 'cta', 0.1, 0.3)
    if t >= tb and a > 0:
        for i, f in enumerate((1.7, 2.4, 3.2)):
            ti = tb + i * 0.35
            if t < ti: continue
            r = BH['ton'][0] * s * f * ease_out(prog(t, ti, ti + 0.6))
            cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_dash([16, 14]); cr.set_source_rgba(1, 1, 1, (0.5 - 0.1 * i) * a); cr.set_line_width(3); cr.stroke(); cr.set_dash([])
            ang = -math.pi / 2 + 0.7 * (i - 1)
            ptext(cr, '?', x + r * math.cos(ang), y + r * math.sin(ang) + 22, 64, GOLD, a * ease_out(prog(t, ti, ti + 0.4)), sw=8)

# ---------- markers ----------
UNITS = [(1e12, 'billion km'), (1e9, 'million km'), (1e3, 'km'), (1.0, 'metres'), (0.01, 'centimetres')]
def fov_text(wm):
    for u, name in UNITS:
        if wm >= u * (1 if u >= 1e9 else 1): break
    v = wm / u
    if name == 'km' and v >= 1000: return f'{v:,.0f} km'
    return (f'{v:.3g}' if v < 100 else f'{v:,.0f}') + ' ' + name

TITLES = [('hook', 'Earth', '#1 EARTH'), ('sun', 'Sun', '#2 THE SUN'), ('stellar', 'giant', '#3 A DEAD STAR'), ('sgr', 'Sagittarius', '#4 SAGITTARIUS A*'),
          ('m87', 'M87', '#5 M87*'), ('ton', 'TON', '#6 TON 618'), ('end', 'limit', 'EVEN BIGGER?'), ('cta', 'which', None)]
def draw_markers(cr, t, s):
    cur, t0 = None, 0
    for key, word, txt in TITLES:
        tw0 = w(key, word)
        if t >= tw0: cur, t0 = txt, tw0
    if cur:
        k = prog(t, t0, t0 + 0.3); sc = lerp(1.8, 1.0, ease_out(k))
        cr.save(); cr.translate(540, 210); cr.scale(sc, sc)
        ptext(cr, cur, 0, 0, fit(cr, cur, 84, 1000), WHITE, clamp(k * 3), sw=11); cr.restore()
    a = ease_out(prog(t, 0.3, 0.8))
    txt = 'Screen: ' + fov_text(W / s)
    cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(40); wd_ = cr.text_extents(txt).x_advance
    x0, x1 = 540 - wd_ / 2 - 80, 540 + wd_ / 2 + 80
    rrect(cr, x0, 262, x1 - x0, 64, 32); cr.set_source_rgba(0.05, 0.08, 0.2, 0.75 * a); cr.fill()
    for xa, d in ((x0 + 22, -1), (x1 - 22, 1)):
        cr.new_path(); cr.move_to(xa, 294); cr.line_to(xa - d * 30, 294); cr.set_source_rgba(*CYAN[:3], a); cr.set_line_width(4); cr.stroke()
        cr.new_path(); cr.move_to(xa + d * 2, 294); cr.line_to(xa - d * 12, 284); cr.line_to(xa - d * 12, 304); cr.close_path(); cr.fill()
    ptext(cr, txt, 540, 307, 40, CYAN, a, fam='Poppins ExtraBold', sw=5)
    hb = bt('hook')
    if t < hb['end'] + 0.3:
        ta = 1 - ease_io(prog(t, hb['end'] - 0.2, hb['end'] + 0.3))
        ptext(cr, 'SCALE OF THE UNIVERSE · PART 5', 540, 1480, 40, CYAN, ta * ease_out(prog(t, 0.1, 0.5)), fam='Poppins ExtraBold', sw=6)
        ptext(cr, 'BLACK HOLES', 540, 1560, 70, GOLD, ta * ease_out(prog(t, 0.2, 0.6)), sw=9)

CHIPS = {
    'hook': [('🌍', 'EARTH: 12,742 KM WIDE', 'Earth')],
    'sun': [('☀️', 'SUN: 1.4 MILLION KM WIDE', 'Sun'), ('⚫', 'AS A BLACK HOLE: ~6 KM', 'six')],
    'stellar': [('⚖️', '~10 SUNS', 'ten'), ('📏', '~60 KM ACROSS', 'sixty'), ('🏙️', 'BIGGER THAN A CITY', 'city')],
    'sgr': [('🌌', 'CENTRE OF THE MILKY WAY', 'heart'), ('⚖️', '4 MILLION SUNS', 'four'), ('🪐', "FITS INSIDE MERCURY'S ORBIT", 'Mercury')],
    'm87': [('📸', 'FIRST BLACK HOLE PHOTO (2019)', 'photographed'), ('⚖️', '6.5 BILLION SUNS', 'six'), ('📏', "3× PLUTO'S ORBIT", 'three')],
    'ton': [('⚖️', '~40 BILLION SUNS', 'forty'), ('☀️', '20+ SOLAR SYSTEMS ACROSS', 'twenty')],
    'end': [('🔭', 'BIGGER ONES MAY BE OUT THERE', 'bigger')],
}
def draw_chips(cr, t):
    for key, chips in CHIPS.items():
        b = bt(key)
        if not (b['start'] <= t < b['end']): continue
        out = 1 - ease_io(prog(t, b['end'] - 0.3, b['end']))
        for i, (e, txt, word) in enumerate(chips):
            t0 = w(key, word)
            if t < t0: continue
            k = pop_k(t, t0); y = 1360 + i * 92
            fs = fit(cr, txt, 44, 840, 'Poppins ExtraBold')
            cr.save(); cr.translate(540, y); cr.scale(k, k)
            wd_ = tw(cr, txt, fs, 'Poppins ExtraBold'); bw = wd_ + 120
            rrect(cr, -bw / 2, -40, bw, 80, 40); cr.set_source_rgba(0.05, 0.06, 0.18, 0.85 * out); cr.fill_preserve()
            cr.set_source_rgba(*CYAN[:3], out); cr.set_line_width(3); cr.stroke()
            emoji(cr, e, -bw / 2 + 45, -2, 50, out)
            ptext(cr, txt, 22, 15 * fs / 44, fs, WHITE, out, fam='Poppins ExtraBold', sw=5)
            cr.restore()

LIST = ['EARTH', 'THE SUN', 'DEAD STAR', 'SGR A*', 'M87*', 'TON 618']
def draw_cta(cr, t):
    tq = w('cta', 'which')
    if t < tq: return
    k = pop_k(t, tq) * (1 + 0.02 * math.sin(t * 5))
    cr.save(); cr.translate(540, 1330); cr.scale(k, k)
    rrect(cr, -500, -150, 1000, 330, 40); cr.set_source_rgba(0.04, 0.05, 0.14, 0.92); cr.fill()
    ptext(cr, 'WHICH BLEW YOUR MIND?', 0, -88, fit(cr, 'WHICH BLEW YOUR MIND?', 66, 900), WHITE, 1, sw=8)
    for i, name in enumerate(LIST):
        col, row = i % 2, i // 2; x, y = -230 + col * 470, -10 + row * 62
        ti = tq + 0.2 + i * 0.12
        if t < ti: continue
        kk = pop_k(t, ti, 0.3); cr.save(); cr.translate(x, y); cr.scale(kk, kk)
        cr.new_path(); cr.arc(-150, -12, 24, 0, 2 * math.pi); cr.set_source_rgba(*PINK[:3], 1); cr.fill()
        ptext(cr, str(i + 1), -150, 0, 32, WHITE, 1, sw=0, shadow=False)
        ptext(cr, name, -112, 2, 38, GOLD, 1, fam='Poppins ExtraBold', anchor='l', sw=5); cr.restore()
    cr.restore()
    tn = w('cta', 'number')
    if t >= tn: ptext(cr, 'COMMENT 1–6 👇'.replace(' 👇', ''), 540, 1580, 60, WHITE, ease_out(prog(t, tn, tn + 0.3)), sw=8)
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1730); cr.scale(k, k)
        txt = 'FOLLOW FOR PART 6'; wd_ = tw(cr, txt, 54)
        rrect(cr, -wd_ / 2 - 90, -62, wd_ + 180, 96, 48); cr.set_source_rgba(*PINK[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 54, WHITE, 1, sw=6); emoji(cr, '🔔', -wd_ / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def draw_captions(cr, t):
    for b in TL['beats']:
        if b['key'] == 'cta' and t >= w('cta', 'which'): return
        if not (b['l0'] - 0.05 <= t < b['l1'] + 0.3): continue
        words, src, toks = b['words'], list(b['tokens']), []
        for _, _, x in words:
            n = len(x.split()); toks.append(' '.join(src[:n])); src = src[n:]
        if src or len(toks) != len(words): toks = [x for _, _, x in words]
        groups, cur = [], []
        for tok, (s_, e, _) in zip(toks, words):
            cur.append((s_, e, tok))
            if len(cur) == 3 or re.search(r"[.,!?:;…]$", tok): groups.append(cur); cur = []
        if cur: groups.append(cur)
        g = None
        for i, gr in enumerate(groups):
            nxt = groups[i + 1][0][0] if i + 1 < len(groups) else b['l1'] + 0.3
            if gr[0][0] - 0.05 <= t < nxt: g = gr; break
        if g is None: return
        ups = [x[2].upper() for x in g]
        size = 66; face(cr, size); space = cr.text_extents(' ').x_advance
        ci = max([j for j, x in enumerate(g) if x[0] <= t + 0.02] or [0])
        widths = [cr.text_extents(u).x_advance * (1.12 if j == ci else 1.0) for j, u in enumerate(ups)]
        total = sum(widths) + space * (len(ups) - 1); sc = min(1.0, 980 / total)
        cr.save(); cr.translate(540, 1700); cr.scale(sc, sc); x = -total / 2
        for j, (u, wd_) in enumerate(zip(ups, widths)):
            cr.save(); cr.translate(x + wd_ / 2, 0)
            if j == ci: k = ease_back(prog(t, g[j][0], g[j][0] + 0.15), 3); cr.scale(1 + 0.12 * k, 1 + 0.12 * k)
            ptext(cr, u, 0, 0, size, CYAN if j == ci else WHITE, 1.0 if j <= ci else 0.6, sw=10)
            cr.restore(); x += wd_ + space
        cr.restore(); return

def render_frame(cr, t):
    s, c = camera(t)
    draw_bg(cr, t, s)
    draw_toronto(cr, t, s, c)
    draw_sun_scene(cr, t, s, c)
    draw_space_scenes(cr, t, s, c)
    draw_earth_bh(cr, t, s, c)
    draw_earth(cr, t, s, c)
    draw_coin(cr, t, s, c)
    draw_markers(cr, t, s)
    draw_chips(cr, t)
    draw_cta(cr, t)
    draw_captions(cr, t)
    f = prog(t, TL['dur'] - 0.4, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- score ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    g = np.random.default_rng(6)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n)
    chords = [[50, 57, 62, 65], [46, 53, 58, 62], [43, 50, 55, 58], [45, 52, 57, 61]]  # Dm Bb Gm A: dark and big
    for ci in range(int(dur / 4.8) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(6.0 * SR)) / SR
        env = np.minimum(1, L_ / 1.6) * np.exp(-L_ * 0.28)
        put(music, ci * 4.8, sum(0.03 * (np.sin(2 * np.pi * note(m) * L_) + 0.6 * np.sin(2 * np.pi * note(m) * 1.003 * L_ + 1)) for m in ch) * env)
        put(music, ci * 4.8, 0.11 * np.sin(2 * np.pi * note(ch[0] - 24) * L_) * env)
        for j in range(4):
            pt = np.arange(int(1.6 * SR)) / SR; m = ch[(j * 3) % 4] + 12
            put(music, ci * 4.8 + j * 1.2, 0.028 * np.sin(2 * np.pi * note(m) * pt) * np.exp(-pt * 3))
    rev = np.zeros(n)
    for d, gg in ((0.31, 0.3), (0.53, 0.2)): k = int(d * SR); rev[k:] += gg * music[:-k]
    music = np.tanh((music + rev) * 1.3) * 0.55
    fx = np.zeros(n)
    def riser(t0, t1, amp=0.25):
        L_ = int((t1 - t0) * SR)
        if L_ <= 0: return
        nz = g.standard_normal(L_); win = np.linspace(0, 1, L_) ** 2; sm = np.convolve(nz, np.ones(40) / 40, 'same')
        put(fx, t0, amp * (sm * (1 - win) + (nz - sm) * win * 0.4) * np.sin(np.pi * np.linspace(0, 1, L_)) ** 0.5)
    def boom(t0, amp=0.6, f0=30):
        L_ = np.arange(int(2.4 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(f0 + 55 * np.exp(-L_ * 7)) / SR) * np.exp(-L_ * 1.8))
    def chime(t0, amp=0.07):
        L_ = np.arange(int(1.0 * SR)) / SR; put(fx, t0, amp * sum(np.sin(2 * np.pi * f * L_) * np.exp(-L_ * d) for f, d in ((1568, 4), (2349, 5))))
    def tick(t0, amp=0.05, f=1500):
        L_ = np.arange(int(0.06 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * f * L_) * np.exp(-L_ * 70))
    tc, tm = w('hook', 'crushed'), w('hook', 'marble')
    L_ = int((tm - tc) * SR)  # the crush: a falling tone into a thump
    if L_ > 0:
        tt_ = np.arange(L_) / SR; f = 220 * np.exp(-tt_ * 2.2); put(fx, tc, 0.12 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.linspace(0.3, 1, L_))
    boom(tm, 0.8, 26)
    for k0, k1, d in (('sun', 'Crush', 1.5), ('stellar', 'giant', 2.0), ('sgr', 'zoom', 2.2), ('m87', 'M87', 2.2), ('ton', 'TON', 2.5)):
        t0 = w(k0, k1); riser(t0, t0 + d)
    for key, word, txt in TITLES:
        if txt and key != 'hook': boom(w(key, word), 0.55)
    for key, chips in CHIPS.items():
        for _, _, word in chips: chime(w(key, word))
    tl = w('ton', 'line')
    for i in range(27): tick(tl + i * 1.4 / 27, 0.05, 1200 + 30 * i)
    v = np.zeros(n)
    for s_, a in T['clips']: put(v, s_, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.5 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx + v
    mix *= np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 1.5)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    global G, TL
    G = Geo(data_dir)
    TL = build(SC.WordVoice(cache)); TL['keys'] = keys()

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    data_dir, out = sys.argv[1], sys.argv[2]
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_scale5'))
    print(f"duration {TL['dur']:.1f}s")
    for b in TL['beats']: print(f"  {b['key']:10s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','):
            render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]
    make_audio(TL, base + '.wav')
    nfr = int(TL['dur'] * FPS); workers = os.cpu_count() or 4
    bounds = np.linspace(0, nfr, workers * 2 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
