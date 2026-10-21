"""'Canada Is Bigger Than You Think' (9:16, ~1.5 min): Mercator hook, then true-size comparisons on a 3D globe.
Moving a shape across a globe keeps its real area, so every comparison here is to scale.
Usage: python3 canada.py <data_dir> <voices_dir> <out.mp4> [--preview t1,t2,...]
"""
import json, math, os, subprocess, sys, wave
import numpy as np
import cairo
import quiz
from quiz import (font, tw, text, fit_font, rrect, pill, clamp, lerp, prog, ease_io, ease_out, ease_back, merc, hexc,
                  Voice, SR)

W, H, FPS = 1080, 1920, 30
GX, GY = 540, 830                       # globe centre on screen
quiz.SPEED = 1.05

NAVY0, NAVY1 = hexc('#0B1630'), hexc('#050A18')
OCEAN0, OCEAN1 = hexc('#16365E'), hexc('#0B1D3A')
LAND, LAND_EDGE = hexc('#2C4A6E'), hexc('#4E74A0')
RED, WHITE, GOLD, ICE = hexc('#EF3340'), hexc('#FFFFFF'), hexc('#FFC845'), hexc('#9FC3E8')
LAKE = hexc('#45C4FF')
HOME = (-97.0, 61.0)                    # Canada's rough centre

EU = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark', 'Estonia', 'Finland', 'France',
      'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands',
      'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden']

# key, narration lines, header, stat (big, small), Canada placed at (lon, lat), globe radius px, highlight
BEATS = [
    ('hook', ["This is Canada. On most maps, it looks gigantic... even bigger than Africa!",
              "But your map has been lying to you."],
     'CANADA > AFRICA?', None, None, None, None),
    ('africa', ["Put Canada on a real globe, and Africa is actually three times bigger."],
     'THE REAL SIZE', ('3×', 'Africa is 3 times bigger'), (19, 4), 760, 'AFRICA'),
    ('twist', ["But here's the twist. Canada is still absolutely massive.",
               "Let's drag it around the world."],
     "BUT HERE'S THE TWIST", ('9.98M km²', 'Canada: 2nd biggest country'), HOME, 980, None),
    ('usa', ["First, the United States. Canada is bigger, even with Alaska included."],
     'CANADA vs USA', ('9.98M > 9.83M', 'km², total area'), (-99, 41), 980, ['United States of America']),
    ('europe', ["Now Europe. Canada stretches from Portugal, all the way past Moscow.",
                "That's more than twice the size of the entire European Union!"],
     'CANADA vs EUROPE', ('2.4×', 'the size of the whole EU'), (16, 53), 980, EU),
    ('india', ["India? Canada is three times bigger."],
     'CANADA vs INDIA', ('3×', 'bigger than India'), (79, 23), 980, ['India']),
    ('australia', ["Australia, a whole continent? Canada still wins, by about thirty percent."],
     'CANADA vs AUSTRALIA', ('+30%', 'bigger than Australia'), (134, -25), 980, ['Australia']),
    ('china', ["Even China is smaller... just barely."],
     'CANADA vs CHINA', ('9.98M > 9.60M', 'km², total area'), (103, 35), 980, ['China']),
    ('russia', ["In fact, only one country on Earth is bigger than Canada.", "Russia."],
     'THE ONLY ONE BIGGER', ('17.1M km²', 'Russia is #1. Canada is #2.'), (96, 62), 640, ['Russia']),
    ('coast', ["Canada also has the longest coastline on the planet. Over two hundred forty thousand kilometers...",
               "enough to wrap around the Earth six times!"],
     'LONGEST COASTLINE ON EARTH', ('243,042 km', '= 6 times around the Earth'), HOME, 980, None),
    ('lakes', ["It also has more lakes than the rest of the world combined."],
     '#1 FOR LAKES', ('MORE LAKES', 'than the rest of the world combined'), HOME, 980, None),
    ('people', ["Yet only about forty-one million people live there... and most of them live close to the US border."],
     'SO MUCH SPACE', ('~41 MILLION', 'people, mostly near the US border'), HOME, 980, None),
    ('outro', ["So, Canada isn't as big as your map says... It's bigger than almost everything else.",
               "Which country should we compare next? Tell me in the comments!"],
     None, None, HOME, 430, None),
]
GAP, LEAD, TAIL = 0.25, 0.35, 0.45

# ---------- sphere maths ----------
def vec(lon, lat):
    lon, lat = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1)

def rot_between(a, b, k=1.0):
    """Rotation matrix taking unit vector a towards b by fraction k (great-circle)."""
    axis = np.cross(a, b); s = np.linalg.norm(axis)
    if s < 1e-9: return np.eye(3)
    axis /= s; ang = math.atan2(s, np.dot(a, b)) * k
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K

def slerp(a, b, k):
    return rot_between(a, b, k) @ a

class View:
    def __init__(self, center, R):
        self.c = center / np.linalg.norm(center); self.R = R
        east = np.cross([0, 0, 1.0], self.c)
        if np.linalg.norm(east) < 1e-6: east = np.array([0, 1.0, 0])
        self.e = east / np.linalg.norm(east); self.n = np.cross(self.c, self.e)
    def project(self, P):
        x, y, d = P @ self.e, P @ self.n, P @ self.c
        back = d < 0
        if back.any():  # snap hidden points onto the limb
            r = np.hypot(x[back], y[back]) + 1e-9
            x = x.copy(); y = y.copy(); x[back] /= r; y[back] /= r
        return GX + x * self.R, GY - y * self.R, d

# ---------- data ----------
def rings(geom):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    return [np.array(p[0], dtype=float) for p in polys]

class Geo:
    def __init__(self, data_dir):
        lo = json.load(open(os.path.join(data_dir, 'countries_110m.geojson')))
        hi = json.load(open(os.path.join(data_dir, 'countries_50m.geojson')))
        self.world_ll = []
        for f in lo['features']:
            for r in rings(f['geometry']): self.world_ll.append(r)
        self.world = self.pack(self.world_ll)
        self.hi = {}
        for f in hi['features']:
            p = f['properties']
            self.hi.setdefault(p['NAME'], []).extend(r for r in rings(f['geometry']) if len(r) >= 6)
            if p['CONTINENT'] == 'Africa':
                self.hi.setdefault('AFRICA', []).extend(r for r in rings(f['geometry']) if len(r) >= 6)
        self.canada_ll = [r for r in self.hi['Canada'] if len(r) >= 12]
        self.canada = self.pack(self.canada_ll)
        self.groups = {}
        self.lakes, self.people = self.sample_points()

    @staticmethod
    def pack(rs):
        P = np.concatenate([vec(r[:, 0], r[:, 1]) for r in rs])
        offs = np.cumsum([0] + [len(r) for r in rs])
        return P, offs

    def group(self, names):
        key = names if isinstance(names, str) else tuple(names)
        if key not in self.groups:
            rs = self.hi[names] if isinstance(names, str) else [r for n in names for r in self.hi[n]]
            self.groups[key] = self.pack(rs)
        return self.groups[key]

    def sample_points(self):
        # point-in-Canada test on a scratch equirectangular canvas
        s = cairo.ImageSurface(cairo.FORMAT_A8, 10, 10); cr = cairo.Context(s)
        for r in self.canada_ll:
            cr.move_to(r[0, 0], -r[0, 1])
            for x, y in r[1:]: cr.line_to(x, -y)
            cr.close_path()
        rng = np.random.default_rng(5)
        lakes, people = [], []
        while len(lakes) < 260:
            lon, lat = rng.uniform(-140, -56), rng.uniform(43, 70)
            if cr.in_fill(lon, -lat): lakes.append((lon, lat))
        while len(people) < 220:
            lon, lat = rng.uniform(-128, -53), 42 + rng.exponential(3.2)
            if lat < 72 and cr.in_fill(lon, -lat): people.append((lon, lat))
        return vec(*np.array(lakes).T), vec(*np.array(people).T)

# ---------- timing ----------
def build(voice):
    t, beats, clips = 0.15, [], []
    for key, lines, head, stat, pos, R, hl in BEATS:
        b = dict(key=key, head=head, stat=stat, pos=pos, R=R, hl=hl, start=t, lines=[])
        cur = t + LEAD
        for i, s in enumerate(lines):
            a = voice.get(s); cur += GAP if i else 0
            clips.append((cur, a)); b['lines'].append((cur, cur + len(a) / SR, s)); cur += len(a) / SR
        t = cur + (TAIL if key != 'outro' else 1.8)
        b['end'] = t; beats.append(b)
    return dict(beats=beats, clips=clips, dur=t)

def state(T, t):
    """Where Canada sits and how the globe is framed at time t."""
    globe_beats = [b for b in T['beats'] if b['pos'] is not None]
    home = vec(*HOME)
    pos, R = home, globe_beats[0]['R']
    prev_pos, prev_R = vec(*HOME), 980
    for b in globe_beats:
        tgt = vec(*b['pos'])
        if t < b['start']: break
        k = ease_io(prog(t, b['start'] + 0.1, b['start'] + 1.4))
        pos = slerp(prev_pos, tgt, k); R = math.exp(lerp(math.log(prev_R), math.log(b['R']), k))
        prev_pos, prev_R = tgt, b['R']
    return pos, R

# ---------- drawing ----------
def path_rings(cr, xs, ys, offs):
    for a, b in zip(offs[:-1], offs[1:]):
        cr.move_to(xs[a], ys[a])
        for i in range(a + 1, b): cr.line_to(xs[i], ys[i])
        cr.close_path()

def draw_bg(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgba(0, *NAVY0); g.add_color_stop_rgba(1, *NAVY1)
    cr.set_source(g); cr.paint()
    rng = np.random.default_rng(2)
    for _ in range(120):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.6, 2.2)
        tw_ = 0.4 + 0.6 * abs(math.sin(t * rng.uniform(0.5, 2) + rng.uniform(0, 6)))
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.5 * tw_); cr.fill()

def draw_globe(cr, geo, T, t, alpha=1.0, spin=0.0):
    pos, R = state(T, t)
    view_c = rot_between(vec(0, 0), vec(spin, 0)) @ pos if spin else pos
    v = View(view_c, R)
    # glow + ocean
    g = cairo.RadialGradient(GX, GY, R * 0.9, GX, GY, R * 1.12)
    g.add_color_stop_rgba(0, 0.35, 0.6, 1, 0.35 * alpha); g.add_color_stop_rgba(1, 0.35, 0.6, 1, 0)
    cr.set_source(g); cr.arc(GX, GY, R * 1.12, 0, 2 * math.pi); cr.fill()
    g = cairo.RadialGradient(GX - R * 0.3, GY - R * 0.35, R * 0.1, GX, GY, R)
    g.add_color_stop_rgba(0, *OCEAN0[:3], alpha); g.add_color_stop_rgba(1, *OCEAN1[:3], alpha)
    cr.new_path(); cr.arc(GX, GY, R, 0, 2 * math.pi); cr.set_source(g); cr.fill_preserve()
    cr.save(); cr.clip()
    # graticule
    cr.set_line_width(1); cr.set_source_rgba(1, 1, 1, 0.05 * alpha)
    for lon in range(-180, 180, 20):
        lat = np.linspace(-85, 85, 60); xs, ys, d = v.project(vec(np.full_like(lat, lon), lat))
        cr.move_to(xs[0], ys[0]); [cr.line_to(x, y) for x, y, dd in zip(xs[1:], ys[1:], d[1:]) if dd > 0 or True]
        cr.stroke()
    # land
    P, offs = geo.world
    xs, ys, d = v.project(P)
    cr.new_path(); path_rings(cr, xs, ys, offs)
    cr.set_source_rgba(*LAND[:3], alpha); cr.fill_preserve()
    cr.set_source_rgba(*LAND_EDGE[:3], 0.8 * alpha); cr.set_line_width(1.2); cr.stroke()
    cur = current_beat(T, t)
    # highlighted comparison region
    if cur and cur['hl']:
        k = ease_out(prog(t, cur['start'] + 0.9, cur['start'] + 1.5)) * (1 - ease_io(prog(t, cur['end'] - 0.3, cur['end'] + 0.2)))
        if k > 0:
            P, offs = geo.group(cur['hl']); xs, ys, d = v.project(P)
            cr.new_path(); path_rings(cr, xs, ys, offs)
            cr.set_source_rgba(*GOLD[:3], 0.55 * k * alpha); cr.fill_preserve()
            cr.set_source_rgba(*GOLD[:3], k * alpha); cr.set_line_width(2.5); cr.stroke()
    # Canada's ghost at home, then the moving true-size copy
    P, offs = geo.canada
    away = 1 - float(np.dot(pos, vec(*HOME)) > 0.9999)
    if away:
        xs, ys, d = v.project(P)
        cr.new_path(); path_rings(cr, xs, ys, offs)
        cr.set_dash([8, 8]); cr.set_source_rgba(*RED[:3], 0.55 * alpha); cr.set_line_width(2); cr.stroke(); cr.set_dash([])
    M = rot_between(vec(*HOME), pos)
    Pm = P @ M.T
    xs, ys, d = v.project(Pm)
    cr.new_path(); path_rings(cr, xs, ys, offs)
    cr.set_source_rgba(*RED[:3], 0.25 * alpha); cr.set_line_width(14); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
    cr.set_source_rgba(*RED[:3], 0.72 * alpha); cr.fill_preserve()
    cr.set_source_rgba(*WHITE[:3], 0.95 * alpha); cr.set_line_width(2.2); cr.stroke()
    # beat-specific effects
    if cur:
        if cur['key'] == 'coast': draw_coast(cr, geo, v, xs, ys, offs, cur, t)
        if cur['key'] == 'lakes': draw_dots(cr, v, geo.lakes @ M.T, cur, t, LAKE, 6)
        if cur['key'] == 'people': draw_dots(cr, v, geo.people @ M.T, cur, t, WHITE, 5)
    cr.restore()
    # Canada label sits on the moving shape
    if cur and cur['key'] not in ('outro',):
        cx, cy, _ = v.project(pos[None, :])
        k = ease_out(prog(t, cur['start'] + 1.2, cur['start'] + 1.6))
        if cur['key'] in ('coast', 'lakes', 'people', 'twist'): k = 0
        pill(cr, 'CANADA', cx[0], cy[0], 30, RED, WHITE, k * alpha * (1 - ease_io(prog(t, cur['end'] - 0.3, cur['end']))),
             padx=18, pady=10)

def draw_coast(cr, geo, v, xs, ys, offs, b, t):
    k = ease_io(prog(t, b['start'] + 0.6, b['lines'][0][1]))
    total = offs[-1]; n = int(total * k)
    cr.new_path()
    for a, e in zip(offs[:-1], offs[1:]):
        if a >= n: break
        cr.move_to(xs[a], ys[a])
        for i in range(a + 1, min(e, n)): cr.line_to(xs[i], ys[i])
        if e <= n: cr.close_path()
    for lw, al in ((16, 0.25), (7, 0.5), (3, 1)):
        cr.set_source_rgba(*GOLD[:3], al); cr.set_line_width(lw); cr.stroke_preserve()
    cr.new_path()

def draw_dots(cr, v, P, b, t, col, r):
    xs, ys, d = v.project(P)
    l0, l1 = b['lines'][0][:2]
    for i, (x, y) in enumerate(zip(xs, ys)):
        k = ease_back(prog(t, l0 + 0.3 + (i / len(xs)) * (l1 - l0) * 0.6, l0 + 0.6 + (i / len(xs)) * (l1 - l0) * 0.6))
        if k <= 0.01: continue
        cr.new_path(); cr.arc(x, y, r * k, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], 0.9); cr.fill()

def draw_mercator(cr, geo, T, t, alpha):
    if alpha <= 0: return
    lon0, my0, z = -48.0, float(merc(np.array(28.0))), 4.3
    def pr(r): return GX + (r[:, 0] - lon0) * z, GY - (merc(r[:, 1]) - my0) * z
    cr.save()
    rrect(cr, 30, 450, 1020, 760, 40); cr.set_source_rgba(*OCEAN1[:3], 0.95 * alpha); cr.fill_preserve(); cr.clip()
    for r in geo.world_ll:
        xs, ys = pr(r); cr.move_to(xs[0], ys[0]); [cr.line_to(x, y) for x, y in zip(xs[1:], ys[1:])]; cr.close_path()
    cr.set_source_rgba(*LAND[:3], alpha); cr.fill()
    b = T['beats'][0]
    for names, col, t0 in ((geo.hi['Canada'], RED, b['start'] + 0.3), (geo.hi['AFRICA'], GOLD, b['lines'][0][0] + 2.6)):
        k = ease_out(prog(t, t0, t0 + 0.5))
        if k <= 0: continue
        cr.new_path()
        for r in names:
            xs, ys = pr(r); cr.move_to(xs[0], ys[0]); [cr.line_to(x, y) for x, y in zip(xs[1:], ys[1:])]; cr.close_path()
        cr.set_source_rgba(*col[:3], 0.85 * k * alpha); cr.fill()
    cr.restore()
    font(cr, 30); text(cr, 'A NORMAL WORLD MAP (MERCATOR)', 540, 1250, ICE, alpha * 0.9, sp=3)
    # 'lying' stamp
    l1 = b['lines'][1][0]
    k = prog(t, l1 + 0.25, l1 + 0.55)
    if k > 0:
        shake = 10 * math.sin(t * 70) * (1 - prog(t, l1 + 0.55, l1 + 0.9))
        cr.save(); cr.translate(540 + shake, 840); cr.rotate(-0.12); s = lerp(2.2, 1, ease_out(k)); cr.scale(s, s)
        font(cr, 110); w = tw(cr, 'MAP LIES', 8)
        cr.set_source_rgba(*RED[:3], alpha * k); cr.set_line_width(10)
        rrect(cr, -w / 2 - 40, -110, w + 80, 150, 20); cr.stroke()
        text(cr, 'MAP LIES', 0, 0, RED, alpha * k, sp=8)
        cr.restore()

def current_beat(T, t):
    for b in T['beats']:
        if b['start'] <= t < b['end']: return b
    return T['beats'][-1]

def draw_header(cr, b, t):
    if not b['head']: return
    a = ease_out(prog(t, b['start'], b['start'] + 0.4)) * (1 - ease_io(prog(t, b['end'] - 0.25, b['end'])))
    k = ease_back(prog(t, b['start'], b['start'] + 0.45))
    cr.save(); cr.translate(540, 250); cr.scale(k, k)
    fit_font(cr, b['head'], 70, 980, 3); text(cr, b['head'], 0, 25, WHITE, a, sp=3, shadow=True)
    cr.restore()
    cr.set_source_rgba(*RED[:3], a); w = 160 * ease_out(prog(t, b['start'] + 0.2, b['start'] + 0.7))
    cr.rectangle(540 - w, 300, 2 * w, 8); cr.fill()

def draw_stat(cr, b, t):
    if not b['stat']: return
    t0 = b['start'] + 1.3 if b['key'] not in ('twist', 'coast', 'lakes', 'people') else b['lines'][0][0] + 0.8
    if b['key'] == 'russia': t0 = b['lines'][1][0]
    a = ease_out(prog(t, t0, t0 + 0.35)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    big, small = b['stat']
    k = ease_back(prog(t, t0, t0 + 0.45))
    cr.save(); cr.translate(540, 1345); cr.scale(k, k)
    rrect(cr, -440, -110, 880, 210, 36); cr.set_source_rgba(0.02, 0.05, 0.12, 0.82 * a); cr.fill_preserve()
    cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
    fit_font(cr, big, 96, 800, 2); text(cr, big, 0, 10, GOLD, a, sp=2)
    fit_font(cr, small, 38, 800, 1, bold=False); text(cr, small, 0, 70, WHITE, a)
    cr.restore()

def chunks(s, n=3):
    words = s.split(); return [' '.join(words[i:i + n]) for i in range(0, len(words), n)]

def draw_captions(cr, T, t):
    for b in T['beats']:
        for l0, l1, s in b['lines']:
            if not (l0 <= t < l1 + 0.15): continue
            cs = chunks(s); total = sum(len(c) + 2 for c in cs); acc = 0
            for c in cs:
                c0 = l0 + (l1 - l0) * acc / total; acc += len(c) + 2; c1 = l0 + (l1 - l0) * acc / total
                if c0 <= t < c1 + (0.15 if c is cs[-1] else 0):
                    k = ease_back(prog(t, c0, c0 + 0.18), 3)
                    cr.save(); cr.translate(540, 1620); cr.scale(k, k)
                    up = c.upper()
                    fit_font(cr, up, 66, 960, 1)
                    w = tw(cr, up, 1)
                    rrect(cr, -w / 2 - 28, -70, w + 56, 100, 22); cr.set_source_rgba(0, 0, 0, 0.55); cr.fill()
                    hl = any(ch.isdigit() for ch in c) or any(x in up for x in ('CANADA', 'RUSSIA', 'AFRICA', 'LYING', 'BIGGER'))
                    text(cr, up, 0, 0, GOLD if hl else WHITE, 1, sp=1)
                    cr.restore()
                    return

def draw_outro(cr, b, t):
    a = ease_out(prog(t, b['start'] + 0.3, b['start'] + 0.8))
    if a <= 0: return
    font(cr, 76); text(cr, "NOT AS BIG", 540, 230, WHITE, a, sp=3, shadow=True)
    text(cr, "AS IT LOOKS...", 540, 320, WHITE, a, sp=3, shadow=True)
    k = ease_out(prog(t, b['lines'][0][0] + 2.4, b['lines'][0][0] + 2.9))
    font(cr, 64); text(cr, "BIGGER THAN", 540, 1330, GOLD, k, sp=3, shadow=True)
    text(cr, "ALMOST EVERYTHING", 540, 1410, GOLD, k, sp=3, shadow=True)
    k2 = ease_back(prog(t, b['lines'][1][0], b['lines'][1][0] + 0.4))
    if k2 > 0.01:
        pill(cr, 'WHICH COUNTRY NEXT?  COMMENT', 540, 1790, 40, RED, WHITE, 1, scale=k2 * (1 + 0.03 * math.sin(t * 6)))

def render_frame(cr, geo, T, t):
    draw_bg(cr, t)
    hook = T['beats'][0]; gstart = hook['end']
    merc_a = 1 - ease_io(prog(t, gstart - 0.35, gstart + 0.35))
    globe_a = ease_io(prog(t, gstart - 0.35, gstart + 0.35))
    draw_mercator(cr, geo, T, t, merc_a)
    if globe_a > 0:
        ob = T['beats'][-1]
        spin = (t - ob['start']) * 12 if t > ob['start'] else 0.0
        draw_globe(cr, geo, T, t, globe_a, spin=spin)
    b = current_beat(T, t)
    draw_header(cr, b, t)
    draw_stat(cr, b, t)
    if b['key'] == 'outro': draw_outro(cr, b, t)
    draw_captions(cr, T, t)
    if b['key'] == 'hook':  # hook kicker
        k = ease_back(prog(t, 0.0, 0.35))
        cr.save(); cr.translate(540, 1460); cr.scale(k, k)
        font(cr, 44); text(cr, 'WAIT FOR IT...', 0, 0, ICE, 0.9 * (1 - prog(t, hook['lines'][1][0], hook['lines'][1][0] + 0.3)), sp=6)
        cr.restore()
    f = prog(t, T['dur'] - 0.4, T['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- audio ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    music = np.zeros(n); beat = 60 / 118
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    for bi in range(int(dur / beat)):
        t0 = bi * beat; ch = chords[(bi // 4) % 4]
        L = np.arange(int(0.3 * SR)) / SR
        if bi * beat > 1.0:
            put(music, t0, 0.42 * np.sin(2 * np.pi * np.cumsum(48 + 80 * np.exp(-L * 35)) / SR) * np.exp(-L * 10))
        M = np.arange(int(0.05 * SR))
        put(music, t0 + beat / 2, 0.045 * np.diff(rng.standard_normal(len(M) + 1)) * np.exp(-M / SR * 70))
        mt = np.arange(int(beat * SR)) / SR
        put(music, t0, 0.11 * np.tanh(3 * np.sin(2 * np.pi * note(ch[0] - 24) * mt)) * np.exp(-mt * 3))
        for s in range(2):
            m = ch[(bi * 2 + s) % 3] + 12; pt = np.arange(int(0.3 * SR)) / SR
            put(music, t0 + s * beat / 2, 0.045 * (np.sin(2 * np.pi * note(m) * pt) + 0.3 * np.sin(4 * np.pi * note(m) * pt)) * np.exp(-pt * 10))
    pad = np.zeros(n)
    for ci in range(int(dur / (beat * 4)) + 1):
        t0 = ci * beat * 4; ch = chords[ci % 4]; L = np.arange(int(beat * 4.5 * SR)) / SR
        env = np.minimum(1, L / 0.4) * np.exp(-L * 0.4)
        put(pad, t0, sum(0.025 * np.sin(2 * np.pi * note(m) * L) for m in ch) * env)
    music = np.tanh((music + pad) * 1.2) * 0.5
    fx = np.zeros(n)
    for b in T['beats'][1:]:
        nz = rng.standard_normal(int(0.9 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2
        put(fx, b['start'] - 0.2, 0.16 * np.convolve(nz, np.ones(40) / 40, 'same') * env)
    hook = T['beats'][0]
    for it, amp in ((hook['lines'][1][0] + 0.3, 0.7), (T['beats'][2]['start'] + 0.2, 0.5),
                    ([b for b in T['beats'] if b['key'] == 'russia'][0]['lines'][1][0], 0.7)):
        L = np.arange(int(1.4 * SR)) / SR
        put(fx, it, amp * np.sin(2 * np.pi * np.cumsum(40 + 90 * np.exp(-L * 12)) / SR) * np.exp(-L * 3))
    for b in T['beats']:
        if b['stat']:
            L = np.arange(int(0.8 * SR)) / SR
            ding = sum(np.sin(2 * np.pi * f * L) * np.exp(-L * d) for f, d in ((1318.5, 6), (1975.5, 7)))
            t0 = b['start'] + 1.3 if b['key'] not in ('twist', 'coast', 'lakes', 'people') else b['lines'][0][0] + 0.8
            if b['key'] == 'russia': t0 = b['lines'][1][0]
            put(fx, t0, 0.12 * ding)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.9
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.6 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx + v
    mix *= np.minimum(1, tt / 0.1) * np.minimum(1, (dur - tt) / 1.2)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def main():
    data_dir, vdir, out = sys.argv[1:4]
    voice = Voice(vdir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache'))
    T = build(voice)
    geo = Geo(data_dir)
    print(f"duration {T['dur']:.1f}s")
    for b in T['beats']: print(f"  {b['key']:9s} {b['start']:6.2f}-{b['end']:6.2f}")
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    if len(sys.argv) > 4 and sys.argv[4] == '--preview':
        for ts in sys.argv[5].split(','):
            render_frame(cr, geo, T, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    wav = out.rsplit('.', 1)[0] + '.wav'
    make_audio(T, wav)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                          stdin=subprocess.PIPE)
    for i in range(int(T['dur'] * FPS)):
        render_frame(cr, geo, T, i / FPS); surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait()

if __name__ == '__main__':
    main()
