"""'The 10 Biggest Countries on Earth, at True Size' (9:16). Countdown with two alternating camera angles per country:
a spinning, zooming 3D globe, then a hard cut to a tilted true-size comparison. Word-synced (engine from china.py).
Usage: python3 big.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON, PARCH
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

TEAL, SKY, CORAL, LIME, VIOLET, ORANGE = hexc('#2EC4B6'), hexc('#7FD8FF'), hexc('#FF6B6B'), hexc('#A3E635'), hexc('#9B6BFF'), hexc('#FF9F1C')
C.SAY = {None: {}}
C.HOT = ('algeria', 'kazakhstan', 'argentina', 'india', 'australia', 'brazil', 'china', 'united', 'states', 'canada', 'russia', 'france', 'japan',
         'texas', 'alaska', 'sahara', 'number', 'biggest', 'eleven', 'twice', 'european', 'union', 'kingdom', 'lakes', 'coastline', 'continent')
C.TAIL_OVERRIDE = {'h1': 0.3, 'h2': 0.3, 'h3': 0.4}
# rank, key, NE name, display, area, colour, cut word (globe -> true size), comparison, narration, fact chips [(word, emoji, text)]
ENTRIES = [
    (10, 'm10', 'Algeria', 'ALGERIA', '2.38M KM²', ORANGE, 'four', ('grid', 'France', 4, 2, '4× FRANCE'),
     "Number ten: Algeria. The biggest country in Africa, over four times the size of France, and more than eighty percent of it is the Sahara desert.",
     [('four', '🗼', '4× FRANCE'), ('eighty', '🏜️', '80%+ SAHARA DESERT')]),
    (9, 'm9', 'Kazakhstan', 'KAZAKHSTAN', '2.72M KM²', TEAL, 'seven', ('grid', 'Japan', 7, 4, '7× JAPAN'),
     "Number nine: Kazakhstan. The largest landlocked country on Earth, about seven times the size of Japan.",
     [('landlocked', '🔒', 'LARGEST LANDLOCKED'), ('seven', '🗾', '7× JAPAN')]),
    (8, 'm8', 'Argentina', 'ARGENTINA', '2.78M KM²', SKY, 'eleven', ('grid', 'United Kingdom', 11, 2, '11× THE UK'),
     "Number eight: Argentina. Over three thousand six hundred kilometres from top to bottom, and eleven times the size of the United Kingdom.",
     [('three', '📏', '3,600+ KM TOP TO BOTTOM'), ('eleven', '💂', '11× THE UK')]),
    (7, 'm7', 'India', 'INDIA', '3.29M KM²', CORAL, 'third', ('behind', 'US48', 'MAINLAND USA'),
     "Number seven: India. Only a third the size of the United States, but home to over four times as many people.",
     [('third', '📐', '1/3 THE SIZE OF THE USA'), ('four', '👥', '4× THE PEOPLE · 1.4 BILLION')]),
    (6, 'm6', 'Australia', 'AUSTRALIA', '7.69M KM²', LIME, 'Texas', ('grid', 'Texas', 11, 4, '11× TEXAS'),
     "Number six: Australia. The only country that is also a continent. You could fit Texas inside it eleven times.",
     [('continent', '🌏', 'A COUNTRY AND A CONTINENT'), ('eleven', '🤠', '11× TEXAS')]),
    (5, 'm5', 'Brazil', 'BRAZIL', '8.51M KM²', LIME, 'bigger', ('over', 'US48', 'MAINLAND USA'),
     "Number five: Brazil. It covers almost half of South America, it's bigger than the mainland United States, and twice the size of the European Union.",
     [('half', '🌎', '~HALF OF SOUTH AMERICA'), ('twice', '⭐', '2× THE EUROPEAN UNION')]),
    (4, 'm4', 'China', 'CHINA', '9.60M KM²', CORAL, 'wide', ('zones', 5),
     "Number four: China. As wide as five time zones, yet the whole country runs on just one clock.",
     [('five', '🕐', '5 TIME ZONES WIDE'), ('one', '⏰', 'ONE OFFICIAL TIME')]),
    (3, 'm3', 'United States of America', 'UNITED STATES', '9.83M KM²', SKY, 'Alaska', ('alaska',),
     "Number three: the United States. Alaska alone is bigger than Texas, California and Montana combined.",
     [('Alaska', '🏔️', 'ALASKA: 1.7M KM²'), ('combined', '➕', '> TEXAS + CALIFORNIA + MONTANA')]),
    (2, 'm2', 'Canada', 'CANADA', '9.98M KM²', CORAL, 'longest', ('lakes',),
     "Number two: Canada. It has the longest coastline on Earth, and more lakes than the rest of the world combined.",
     [('longest', '🌊', 'LONGEST COASTLINE: 243,000 KM'), ('lakes', '💧', 'MOST LAKES ON EARTH')]),
    (1, 'm1', 'Russia', 'RUSSIA', '17.1M KM²', GOLD, 'eleven', ('russia',),
     "And number one: Russia. Seventeen million square kilometres, eleven time zones, and almost twice the size of the United States.",
     [('eleven', '🕚', '11 TIME ZONES'), ('twice', '🗽', 'ALMOST 2× THE USA')]),
]
BEATS = [
    ('h1', "One country covers more than a tenth of all the land on Earth.", None, None, None, None, None),
    ('h2', "Another is twice the size of the entire European Union.", None, None, None, None, None),
    ('h3', "And in a third, one single state is bigger than most countries.", None, None, None, None, None),
    ('title', "These are the ten biggest countries on Earth, at true size.", None, None, None, None, None),
] + [(e[1], e[8], None, None, None, None, None) for e in ENTRIES] + [
    ('cta', "Which one surprised you most? Tell us in the comments, and follow for more.", None, None, None, None, None)]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2', 'h3')
bt, w = C.bt, C.w
G = None
EKEY = {e[1]: e for e in ENTRIES}

def local(rs, lon0, lat0):
    out = []
    for r in rs:
        l, p, p0 = np.radians(r[:, 0] - lon0), np.radians(r[:, 1]), math.radians(lat0)
        cosc = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l)
        k = np.sqrt(2 / np.maximum(1 + cosc, 1e-9))
        out.append(np.column_stack([6371 * k * np.cos(p) * np.sin(l), 6371 * k * (math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l))]))
    return out
def bounds(rs):
    p = np.concatenate(rs); return p[:, 0].min(), p[:, 0].max(), p[:, 1].min(), p[:, 1].max()
def recentre(rs):
    x0, x1, y0, y1 = bounds(rs); c = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); return [r - c for r in rs]
def area(rs): return sum(abs(0.5 * np.sum(r[:, 0] * np.roll(r[:, 1], 1) - r[:, 1] * np.roll(r[:, 0], 1))) for r in rs)

CENTRE = {'Algeria': (2.6, 28), 'Kazakhstan': (67, 48), 'Argentina': (-64, -38), 'India': (79, 22), 'Australia': (134, -26), 'Brazil': (-53, -11),
          'China': (104, 36), 'United States of America': (-98, 39), 'Canada': (-98, 61), 'Russia': (98, 62), 'France': (2.5, 46.5), 'Japan': (138, 37),
          'United Kingdom': (-2.5, 54.5)}
class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        self.raw, self.sh = {}, {}
        keep = {'France': lambda r: -6 < r[:, 0].mean() < 10 and r[:, 1].mean() > 41, 'United Kingdom': lambda r: r[:, 1].mean() > 49,
                'Japan': lambda r: True, 'Australia': lambda r: r[:, 1].mean() > -45, 'Argentina': lambda r: True}
        for n, c in CENTRE.items():
            rs = [r for r in rings(cf[n]['geometry']) if len(r) > 3]
            self.raw[n] = rs
            sel = [r for r in rs if keep.get(n, lambda r: True)(r)]
            if n == 'United States of America': sel = [r for r in rs if -126 < r[:, 0].mean() < -66 and 24 < r[:, 1].mean() < 50]
            self.sh[n] = recentre(local(sel, *c))
        self.sh['US48'] = self.sh['United States of America']
        st = {f['properties']['name']: f for f in json.load(open(os.path.join(d, 'admin1_50m.geojson')))['features'] if f['properties'].get('admin') == 'United States of America'}
        for n, c in (('Texas', (-99.3, 31.3)), ('Alaska', (-152, 64)), ('California', (-119.5, 37.2)), ('Montana', (-109.6, 47))):
            rs = [r for r in rings(st[n]['geometry']) if len(r) > 3]
            if n == 'Alaska': rs = [r for r in rs if r[:, 0].mean() < -129 and r[:, 0].mean() > -170 and len(r) > 8]
            self.sh[n] = recentre(local(rs, *c)); self.raw[n] = rs
        # the three states in the lower-48 frame (for the Alaska comparison)
        x0, x1, y0, y1 = bounds(local([r for r in self.raw['United States of America'] if -126 < r[:, 0].mean() < -66 and 24 < r[:, 1].mean() < 50], -98, 39))
        off = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        self.in48 = {n: [r - off for r in local(self.raw[n], -98, 39)] for n in ('Texas', 'California', 'Montana')}
        lk = [r for f in json.load(open(os.path.join(d, 'ne_50m_lakes.geojson')))['features'] for r in rings(f['geometry'])
              if len(r) > 3 and -141 < r[:, 0].mean() < -55 and 42 < r[:, 1].mean() < 75]
        x0, x1, y0, y1 = bounds(local([r for r in self.raw['Canada']], -98, 61)); off = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        self.lakes = [r - off for r in local(lk, -98, 61)]
        self.land = [r for f in json.load(open(os.path.join(d, 'land.geojson')))['features'] for r in rings(f['geometry']) if len(r) > 3]
        print('areas M km²:', {k: round(area(v) / 1e6, 2) for k, v in self.sh.items()})

# ---------- drawing ----------
def bg(cr, t, col, dark=0.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.02, 0.03, 0.09); g.add_color_stop_rgb(1, *[0.05 + 0.13 * c for c in col[:3]])
    cr.set_source(g); cr.paint()
    rng = np.random.default_rng(3)
    for _ in range(110):
        x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.4)
        cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25 + 0.25 * math.sin(t * 2 + x)); cr.fill()

def km_path(cr, rs, cx, cy, s, ox=0.0, oy=0.0):
    cr.new_path()
    for r in rs:
        cr.move_to(cx + (r[0, 0] + ox) * s, cy - (r[0, 1] + oy) * s)
        for x, y in r[1:]: cr.line_to(cx + (x + ox) * s, cy - (y + oy) * s)
        cr.close_path()
def km_shape(cr, rs, cx, cy, s, col, a, ox=0.0, oy=0.0, fill=0.92, lw=3, edge=WHITE, glow=False):
    if a <= 0: return
    km_path(cr, rs, cx, cy, s, ox, oy)
    if glow: cr.set_source_rgba(*col[:3], 0.3 * a); cr.set_line_width(24); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
    cr.set_source_rgba(*col[:3], fill * a); cr.fill_preserve(); cr.set_source_rgba(*edge[:3], a); cr.set_line_width(lw); cr.stroke()

def ortho(lon, lat, lon0, lat0):
    l, p, l0, p0 = np.radians(lon), np.radians(lat), math.radians(lon0), math.radians(lat0)
    cc = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l - l0)
    x = np.cos(p) * np.sin(l - l0); y = -(math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l - l0))
    r = np.hypot(x, y); hid = cc < 0
    return np.where(hid, x / np.maximum(r, 1e-9), x), np.where(hid, y / np.maximum(r, 1e-9), y), cc

def globe(cr, cx, cy, R, lon0, lat0, hi=None, hcol=GOLD, ha=1.0):
    g = cairo.RadialGradient(cx - R * 0.3, cy - R * 0.35, R * 0.1, cx, cy, R); g.add_color_stop_rgb(0, 0.2, 0.45, 0.75); g.add_color_stop_rgb(1, 0.05, 0.15, 0.4)
    cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.set_source(g); cr.fill()
    cr.save(); cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.clip()
    def path(rs):
        cr.new_path()
        for r in rs:
            x, y, cc = ortho(r[:, 0], r[:, 1], lon0, lat0)
            if (cc < 0).all(): continue
            cr.move_to(cx + x[0] * R, cy + y[0] * R); [cr.line_to(cx + u * R, cy + v * R) for u, v in zip(x[1:], y[1:])]; cr.close_path()
    path(G.land); cr.set_source_rgb(0.3, 0.5, 0.36); cr.fill()
    if hi and ha > 0:
        path(G.raw[hi]); cr.set_source_rgba(*hcol[:3], ha); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, ha); cr.set_line_width(3); cr.stroke()
    g = cairo.RadialGradient(cx - R * 0.35, cy - R * 0.4, R * 0.05, cx, cy, R * 1.02)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.2); g.add_color_stop_rgba(0.6, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0, 0, 0.05, 0.6); cr.set_source(g); cr.paint(); cr.restore()
    cr.new_path(); cr.arc(cx, cy, R + 8, 0, 2 * math.pi); cr.set_source_rgba(0.5, 0.75, 1, 0.3); cr.set_line_width(10); cr.stroke()

# camera: each globe shot flies from the previous country to the next one
STOPS = None
def stops():
    s = [(0.0, 60, 30, 0.75)]
    for key, name, z in (('h1', 'Russia', 0.95), ('h2', 'Brazil', 1.25)): s.append((bt(key)['start'], *CENTRE[name], z))
    s.append((bt('title')['start'], 10, 25, 0.8))
    for e in ENTRIES:
        z = {'Russia': 1.05, 'Canada': 1.15, 'United States of America': 1.3, 'China': 1.45, 'Brazil': 1.45, 'Australia': 1.5}.get(e[2], 1.6)
        s.append((bt(e[1])['start'], *CENTRE[e[2]], z))
    s.append((bt('cta')['start'], 20, 20, 0.8))
    return s
def cam_at(t):
    """Globe pose (lon, lat, zoom) at time t: fly from each stop to the next, dipping out a little mid-flight."""
    pose = STOPS[0][1:]
    for st in STOPS[1:]:
        if t < st[0]: break
        k = ease_io(prog(t, st[0], st[0] + 1.0)); d = (st[1] - pose[0] + 180) % 360 - 180
        pose = (pose[0] + d * k, lerp(pose[1], st[2], k), math.exp(lerp(math.log(pose[2]), math.log(st[3]), k)) * (1 - 0.2 * math.sin(math.pi * k)))
    return pose

def globe_shot(cr, t, hi, col, t0, tilt):
    lon0, lat0, z = cam_at(t)
    drift = 1 + 0.05 * prog(t, t0, t0 + 4)
    cr.save(); cr.translate(540, 1000); cr.rotate(tilt); cr.translate(-540, -1000)
    globe(cr, 540, 1040, 400 * z * drift, lon0 + 3 * math.sin(t * 0.5), lat0, hi, col, ease_out(prog(t, t0 + 0.5, t0 + 0.9)))
    cr.restore()

def header(cr, t, e, a):
    rank, key, ne, name, ar, col = e[:6]; b = bt(key)
    k = prog(t, b['start'], b['start'] + 0.25); sc = lerp(2.4, 1, ease_out(k))
    cr.save(); cr.translate(160, 220); cr.rotate(-0.08); cr.scale(sc, sc)
    cr.new_path(); cr.arc(0, 0, 105, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], a * clamp(k * 3)); cr.fill()
    ptext(cr, f'#{rank}', 0, 34, 100 if rank < 10 else 84, INK, a * clamp(k * 3), sw=0, shadow=False); cr.restore()
    tn = b['l0'] + 0.5; k2 = pop_k(t, tn)
    cr.save(); cr.translate(620, 200); cr.scale(k2, k2); ptext(cr, name, 0, 0, fit(cr, name, 84, 660), WHITE, a, sw=10); cr.restore()
    if t >= tn + 0.35: chip(cr, ar, 620, 320, 56, col, INK, pop_k(t, tn + 0.35), a)
    for i in range(10):
        r_ = 10 - i; x = 120 + i * 93; on = r_ == rank; done = r_ > rank
        cr.new_path(); cr.arc(x, 1880, 20 if on else 13, 0, 2 * math.pi)
        cr.set_source_rgba(*(col[:3] if on else ((0.9, 0.9, 0.95) if done else (0.3, 0.3, 0.38))), 1); cr.fill()

def true_shot(cr, t, e, tc, a):
    """The cut: the country at true size, tilted the other way, with its comparison."""
    rank, key, ne, name, ar, col, cutw, cmp_ = e[:8]; b = bt(key)
    host = G.sh[ne]; x0, x1, y0, y1 = bounds(host); wk, hk = x1 - x0, y1 - y0
    if cmp_[0] in ('behind', 'over', 'russia'):
        u0, u1, v0, v1 = bounds(G.sh['US48']); wk, hk = max(wk, u1 - u0), max(hk, v1 - v0)
    if cmp_[0] == 'alaska': wk, hk = wk * 1.0, hk * 1.25
    s = min(960 / wk, 820 / hk); cx, cy = 540, 960
    zoom = 1.0 + 0.06 * prog(t, tc, b['end']); tilt = (0.045 if rank % 2 else -0.045) * (1 - 0.4 * prog(t, tc, b['end']))
    cr.save(); cr.translate(cx, cy); cr.rotate(tilt); cr.scale(zoom, zoom); cr.translate(-cx, -cy)
    k = pop_k(t, tc, 0.4); cr.save(); cr.translate(cx, cy); cr.scale(k, k); cr.translate(-cx, -cy)
    kind = cmp_[0]
    if kind == 'behind':
        km_shape(cr, G.sh['US48'], cx, cy, s, (0.5, 0.55, 0.65), a * ease_out(prog(t, tc + 0.3, tc + 0.8)), fill=0.6, lw=2)
        ptext(cr, cmp_[2], cx, cy - (bounds(G.sh['US48'])[3]) * s - 30, 36, WHITE, a * ease_out(prog(t, tc + 0.3, tc + 0.8)), fam='Poppins ExtraBold', sw=6)
    km_shape(cr, host, cx, cy, s, col, a, glow=True)
    if kind == 'grid':
        shp = G.sh[cmp_[1]]; n, cols = cmp_[2], cmp_[3]; rows = math.ceil(n / cols); u0, u1, v0, v1 = bounds(shp)
        sx = min((wk * 0.66) / cols, (u1 - u0) * 1.02); sy = min((hk * 0.62) / rows, (v1 - v0) * 1.02)
        tw0 = w(key, cutw)
        for i in range(n):
            ts = tw0 + 0.15 + i * (1.4 / n)
            if t < ts: continue
            ox = (i % cols - (cols - 1) / 2) * sx; oy = -((i // cols) - (rows - 1) / 2) * sy
            if ne == 'Argentina': ox *= 0.55 if (i // cols) > 2 else 0.9; ox -= 150 if (i // cols) > 2 else 0
            kk = pop_k(t, ts, 0.3)
            cr.save(); cr.translate(cx + ox * s, cy - oy * s); cr.scale(kk, kk); cr.translate(-(cx + ox * s), -(cy - oy * s))
            km_shape(cr, shp, cx, cy, s, (1, 1, 1), a * 0.9, ox, oy, fill=0.5, lw=2.5, edge=INK); cr.restore()
    elif kind == 'over':
        kk = ease_out(prog(t, w(key, 'bigger') - 0.2, w(key, 'bigger') + 0.5))
        cr.save(); cr.translate(0, (1 - kk) * -700); km_shape(cr, G.sh['US48'], cx, cy, s, (1, 1, 1), a * kk, 0, 150, fill=0.45, lw=3, edge=INK); cr.restore()
        if kk > 0.9: ptext(cr, cmp_[2], cx, cy - 150 * s + 10, 40, INK, a, sw=0, shadow=False)
    elif kind == 'zones':
        cr.save(); km_path(cr, host, cx, cy, s); cr.clip()
        merge = ease_io(prog(t, w(key, 'one') - 0.2, w(key, 'one') + 0.5))
        for i in range(5):
            ts = w(key, 'five') - 0.3 + i * 0.12
            if t < ts: continue
            xa = cx + (x0 + wk * i / 5 - (x0 + x1) / 2) * s
            cr.rectangle(xa, cy - hk * s / 2, wk * s / 5, hk * s); cr.set_source_rgba(*[(1, 1, 1), (0, 0, 0)][i % 2], 0.22 * a * (1 - merge)); cr.fill()
        cr.restore()
        for i in range(5):
            ts = w(key, 'five') - 0.3 + i * 0.12
            if t >= ts: ptext(cr, f'+{5 + i}', cx + (x0 + wk * (i + 0.5) / 5 - (x0 + x1) / 2) * s, cy + hk * s / 2 + 60, 44, WHITE, a * (1 - merge) * pop_k(t, ts), sw=6)
        if merge > 0: emoji(cr, '⏰', cx + 40, cy, 220 * pop_k(t, w(key, 'one') - 0.2), a); ptext(cr, 'UTC+8 EVERYWHERE', cx, cy + hk * s / 2 + 60, 50, GOLD, a * merge, sw=7)
    elif kind == 'alaska':
        for n_, word in (('Texas', 'Texas'), ('California', 'California'), ('Montana', 'Montana')):
            km_shape(cr, G.in48[n_], cx, cy, s, GOLD, a * ease_out(prog(t, w(key, word), w(key, word) + 0.3)), fill=0.9, lw=2, edge=INK)
        kk = ease_out(prog(t, tc + 0.1, tc + 0.7))
        cr.save(); cr.translate(0, (1 - kk) * -600); km_shape(cr, G.sh['Alaska'], cx, cy, s, (1, 1, 1), a * kk, -150, 1150, fill=0.85, lw=3, edge=INK); cr.restore()
        if kk > 0.9: ptext(cr, 'ALASKA', cx - 150 * s, cy - 1150 * s + 10, 44, INK, a, sw=0, shadow=False)
    elif kind == 'lakes':
        km_shape(cr, G.lakes, cx, cy, s, (0.3, 0.75, 1.0), a * ease_out(prog(t, w(key, 'lakes') - 0.3, w(key, 'lakes') + 0.4)), fill=1.0, lw=0.5, edge=(0.3, 0.75, 1.0))
        kc = ease_out(prog(t, w(key, 'longest'), w(key, 'longest') + 0.8))
        if kc > 0:
            km_path(cr, host, cx, cy, s); cr.set_source_rgba(0.5, 0.9, 1, a * kc * (0.6 + 0.4 * math.sin(t * 6))); cr.set_line_width(7); cr.stroke()
    elif kind == 'russia':
        cr.save(); km_path(cr, host, cx, cy, s); cr.clip()
        for i in range(11):
            ts = w(key, 'eleven') - 0.2 + i * 0.07
            if t < ts: continue
            cr.rectangle(cx + (x0 + (x1 - x0) * i / 11 - (x0 + x1) / 2) * s, cy - 500, (x1 - x0) * s / 11, 1000)
            cr.set_source_rgba(*[(1, 1, 1), (0, 0, 0)][i % 2], 0.2 * a); cr.fill()
        cr.restore()
        kk = ease_out(prog(t, w(key, 'twice') - 0.3, w(key, 'twice') + 0.4))
        cr.save(); cr.translate(0, (1 - kk) * 700); km_shape(cr, G.sh['US48'], cx, cy, s, (1, 1, 1), a * kk, -600, -300, fill=0.5, lw=3, edge=INK); cr.restore()
        if kk > 0.9: ptext(cr, 'MAINLAND USA', cx - 600 * s, cy + 300 * s + 12, 34, INK, a, sw=0, shadow=False)
    cr.restore(); cr.restore()
    ptext(cr, 'TRUE SIZE', 540, 480, 34, col, 0.9 * a * ease_out(prog(t, tc, tc + 0.3)), fam='Poppins ExtraBold', sw=5)

def draw_entry(cr, t, e):
    rank, key, ne, name, ar, col, cutw = e[:7]; b = bt(key)
    a = 1 - ease_io(prog(t, b['end'] - 0.2, b['end']))
    tc = w(key, cutw) - 0.25
    bg(cr, t, col)
    if t < tc: globe_shot(cr, t, ne, col, b['start'], -0.05 if rank % 2 else 0.05)
    else:
        true_shot(cr, t, e, tc, a)
        fl = 1 - prog(t, tc, tc + 0.14)
        if 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.6 * fl); cr.paint()
    g = cairo.LinearGradient(0, 0, 0, 520); g.add_color_stop_rgba(0, 0, 0, 0.03, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.03, 0); cr.rectangle(0, 0, W, 520); cr.set_source(g); cr.fill()
    g = cairo.LinearGradient(0, 1380, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.03, 0); g.add_color_stop_rgba(0.4, 0, 0, 0.03, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.03, 0.95)
    cr.rectangle(0, 1380, W, 540); cr.set_source(g); cr.fill()
    header(cr, t, e, a)
    for i, (word, em, txt) in enumerate(e[9]):
        chip(cr, txt, 540, 1460 + i * 112, 42, WHITE if i == 0 else col, INK, pop_k(t, w(key, word)), a, em=em)

def draw_hook(cr, t):
    if t >= bt('title')['start']: return False
    b = next(bt(k) for k in ('h1', 'h2', 'h3') if t < bt(k)['end'] + 1e-6); key = b['key']
    if key == 'h1':
        bg(cr, t, GOLD); globe_shot(cr, t, 'Russia', GOLD, -0.3, -0.05)
        slam(cr, 'ONE COUNTRY', 540, 250, 130, WHITE, t, 0.03)
        slam(cr, '11% OF ALL LAND', 540, 400, 110, GOLD, t, w('h1', 'tenth') - 0.1)
    elif key == 'h2':
        bg(cr, t, LIME); globe_shot(cr, t, 'Brazil', LIME, b['start'] - 0.3, 0.05)
        slam(cr, '2× THE ENTIRE', 540, 250, 120, WHITE, t, w('h2', 'twice'))
        slam(cr, 'EUROPEAN UNION', 540, 400, 110, LIME, t, w('h2', 'European'))
    else:
        bg(cr, t, SKY); host = G.sh['US48']; x0, x1, y0, y1 = bounds(host); s = 900 / (x1 - x0)
        cr.save(); cr.translate(540, 1000); cr.rotate(-0.05); cr.translate(-540, -1000)
        km_shape(cr, host, 540, 1100, s, SKY, 1, glow=True)
        kk = ease_out(prog(t, w('h3', 'one') - 0.2, w('h3', 'one') + 0.5))
        cr.save(); cr.translate(0, (1 - kk) * -800); km_shape(cr, G.sh['Alaska'], 540, 1100, s, (1, 1, 1), kk, -150, 150, fill=0.85, lw=3, edge=INK); cr.restore()
        if kk > 0.9: ptext(cr, 'ALASKA', 540 - 150 * s, 1100 - 150 * s + 12, 54, INK, 1, sw=0, shadow=False)
        cr.restore()
        slam(cr, 'ONE SINGLE STATE', 540, 250, 110, WHITE, t, w('h3', 'one'))
        slam(cr, '> MOST COUNTRIES', 540, 400, 110, SKY, t, w('h3', 'bigger'))
    fl = 1 - prog(t, b['start'], b['start'] + 0.14)
    if key != 'h1' and 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.6 * fl); cr.paint()
    return True

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end']): return False
    bg(cr, t, GOLD); globe_shot(cr, t, None, GOLD, b['start'], 0.0)
    cr.set_source_rgba(0, 0, 0.03, 0.45); cr.paint()
    k = pop_k(t, w('title', 'ten') - 0.1); cr.save(); cr.translate(540, 620); cr.scale(k, k); ptext(cr, 'THE 10', 0, 0, 190, GOLD, 1, sw=16); cr.restore()
    slam(cr, 'BIGGEST COUNTRIES', 540, 820, 100, WHITE, t, w('title', 'biggest'))
    slam(cr, 'ON EARTH', 540, 950, 100, WHITE, t, w('title', 'Earth'))
    tt = w('title', 'true')
    if t >= tt: chip(cr, 'AT TRUE SIZE', 540, 1110, 64, GOLD, INK, pop_k(t, tt), 1, em='📐')
    fl = 1 - prog(t, b['start'], b['start'] + 0.14)
    if 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.6 * fl); cr.paint()
    return True

def draw_cta(cr, t):
    b = bt('cta'); bg(cr, t, GOLD); globe_shot(cr, t, None, GOLD, b['start'], 0.04)
    cr.set_source_rgba(0, 0, 0.03, 0.55); cr.paint()
    k = pop_k(t, w('cta', 'Which')); cr.save(); cr.translate(540, 520); cr.scale(k, k)
    ptext(cr, 'WHICH ONE', 0, 0, 110, WHITE, 1, sw=12); ptext(cr, 'SURPRISED YOU?', 0, 140, 110, GOLD, 1, sw=13); cr.restore()
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
        e = next((e for e in ENTRIES if bt(e[1])['start'] <= t < bt(e[1])['end']), ENTRIES[-1])
        draw_entry(cr, t, e); C.draw_captions(cr, t, 1740)
        fl = 1 - prog(t, bt(e[1])['start'], bt(e[1])['start'] + 0.14)
        if 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.5 * fl); cr.paint()
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR; rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 120; bar = beat * 4
    chords = [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 48, 52]]  # Dm Bb C Am: driving, epic
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar * 1.2 * SR)) / SR; env = np.minimum(1, Lc / 0.2) * np.exp(-Lc * 0.7)
        put(music, ci * bar, sum(0.03 * (np.sin(2 * np.pi * note(m) * Lc) + 0.4 * np.sin(2 * np.pi * note(m + 12) * 1.003 * Lc)) for m in ch) * env)
        put(music, ci * bar, 0.09 * np.sin(2 * np.pi * note(ch[0] - 24) * Lc) * env)
        for j in range(8):
            m = ch[j % 3] + 12 + (12 if j % 4 == 3 else 0); P = np.arange(int(0.2 * SR)) / SR
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
    def whoosh(t0, amp=0.25, d=0.5):
        nz = rng.standard_normal(int(d * SR)); env = np.linspace(0, 1, len(nz)) ** 2; put(fx, t0, amp * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def ding(t0, amp=0.1):
        Ld = np.arange(int(0.8 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * 1318 * Ld) + 0.5 * np.sin(2 * np.pi * 1976 * Ld)) * np.exp(-Ld * 5))
    boom(0.03, 0.8)
    for key, word in (('h1', 'tenth'), ('h2', 'twice'), ('h3', 'one'), ('title', 'ten')): boom(w(key, word), 0.7)
    for key in ('h2', 'h3', 'title'): whoosh(bt(key)['start'] - 0.45)
    for e in ENTRIES:
        b = bt(e[1]); whoosh(b['start'] - 0.45); boom(b['start'] + 0.05, 0.55 if e[0] > 1 else 0.95)
        tc = w(e[1], e[6]) - 0.25; whoosh(tc - 0.3, 0.3, 0.3); boom(tc, 0.45)
        for word, _, _ in e[9]: ding(w(e[1], word), 0.07)
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
    global G, STOPS
    C.TL = C.build(C.WordVoice(cache)); G = Geo(data_dir); STOPS = stops()

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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_big'))
    print(f"duration {C.TL['dur']:.1f}s")
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
