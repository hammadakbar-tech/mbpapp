"""Render 'What if the ocean rose 2,500 m?' video frames and pipe them to ffmpeg."""
import json, math, sys, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from multiprocessing import Pool

D = sys.argv[1]
OUT = sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 and not OUT.endswith('.png') else None   # render only first N frames (preview)
FPS = 30
W, H = 1920, 1080
TOP, MAP_H = 150, 779            # map strip: lat 84N .. 62S
LAT0, LAT1 = 84.0, -62.0
FONT = '/usr/share/fonts/opentype/inter/'
def font(w, s): return ImageFont.truetype(FONT + {'b': 'Inter-Bold.otf', 'x': 'Inter-ExtraBold.otf',
                                                 's': 'Inter-SemiBold.otf', 'r': 'Inter-Regular.otf',
                                                 'k': 'Inter-Black.otf'}[w], s)
BG = (9, 17, 33)
ACC = (94, 205, 240)
MAXL = 2500.0

# ---------------------------------------------------------------- data
z = np.load(D + '/z.npy').astype(np.float32)       # 1801x3600, north up
fl = np.load(D + '/fl.npy').astype(np.float32)
fl[~np.isfinite(fl)] = 1e5
ZH, ZW = z.shape
def hillshade(a, dx):
    gy, gx = np.gradient(a)
    sl = np.arctan(np.hypot(gx, gy) / dx)
    asp = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(40)
    hs = np.sin(alt) * np.cos(sl) + np.cos(alt) * np.sin(sl) * np.cos(az - asp)
    return np.clip(hs, 0, 1)
HS = hillshade(np.maximum(z, 0) * 1.0, 11000 / 8).astype(np.float32)   # exaggerated relief

countries = json.load(open(D + '/countries.json'))
sov = [c for c in countries if c['type'] in ('Sovereign country', 'Country', 'Sovereignty') and c['elim'] > 0]
NCOUNT = len(sov)
events = sorted(sov, key=lambda c: c['elim'])
ids = np.load(D + '/ids.npy')
for c in sov:
    m = ids == c['i']
    c['pct2500'] = float((fl[m] >= MAXL).mean()) if m.any() else 0.0
gj = json.load(open(D + '/countries.geojson'))
rings = []
for ft in gj['features']:
    g = ft['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for p in polys:
        for r in p:
            a = np.array(r, np.float32)
            if len(a) > 3: rings.append(a)

# ---------------------------------------------------------------- color
def ramp(stops):
    xs = np.array([s[0] for s in stops], np.float32); cs = np.array([s[1] for s in stops], np.float32)
    return lambda v: np.stack([np.interp(v, xs, cs[:, k]) for k in range(3)], -1)
land_ramp = ramp([(0, (58, 128, 72)), (300, (122, 160, 82)), (900, (196, 182, 112)), (1800, (170, 128, 84)),
                  (3000, (128, 98, 82)), (4200, (205, 200, 196)), (5500, (250, 250, 252))])
water_ramp = ramp([(0, (120, 222, 232)), (40, (64, 176, 214)), (400, (30, 104, 168)), (2000, (16, 58, 118)),
                   (6000, (8, 28, 66))])

def colorize(zc, flc, hsc, L):
    water = flc < L
    depth = np.maximum(L - zc, 0)
    out = np.empty(zc.shape + (3,), np.float32)
    h = np.maximum(zc - L, 0)
    lc = land_ramp(h) * (0.55 + 0.75 * hsc[..., None])
    wc = water_ramp(depth)
    # newly drowned land keeps a faint ghost of its relief
    ghost = (zc > 0) & water
    wc[ghost] *= (0.9 + 0.2 * hsc[ghost][:, None])
    out[:] = np.where(water[..., None], wc, lc)
    return np.clip(out, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- camera
GLOBAL = (-180.0, 180.0, LAT0, LAT1)        # lon0, lon1, latTop, latBottom
def cam_rect(lon_c, lat_c, span_lon):
    span_lat = span_lon * MAP_H / W
    return (lon_c - span_lon / 2, lon_c + span_lon / 2, lat_c + span_lat / 2, lat_c - span_lat / 2)
def lerp_rect(a, b, t):
    # interpolate in log-zoom space for a natural camera move
    sa, sb = a[1] - a[0], b[1] - b[0]
    s = sa * (sb / sa) ** t
    ca = ((a[0] + a[1]) / 2, (a[2] + a[3]) / 2); cb = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2)
    # weight centre so it tracks the zoom
    w = (sa - s) / (sa - sb) if abs(sa - sb) > 1e-6 else t
    cx = ca[0] + (cb[0] - ca[0]) * w; cy = ca[1] + (cb[1] - ca[1]) * w
    return cam_rect(cx, cy, s)

# downsampled arrays for the global view
def resize_f(a, w, h, box):
    im = Image.fromarray(a)
    return np.asarray(im.resize((w, h), Image.BILINEAR, box=box), np.float32)
def src_box(rect):
    lon0, lon1, la0, la1 = rect
    return ((lon0 + 180) / 360 * ZW, (90 - la0) / 180 * (ZH - 1), (lon1 + 180) / 360 * ZW, (90 - la1) / 180 * (ZH - 1))
GB = src_box(GLOBAL)
G_Z, G_FL, G_HS = (resize_f(a, W, MAP_H, GB) for a in (z, fl, HS))

def render_map(rect, L):
    if rect == GLOBAL:
        zc, flc, hsc = G_Z, G_FL, G_HS
    else:
        b = src_box(rect)
        zc, flc, hsc = (resize_f(a, W, MAP_H, b) for a in (z, fl, HS))
    return Image.fromarray(colorize(zc, flc, hsc, L))

def project(rect, lon, lat):
    lon0, lon1, la0, la1 = rect
    return ((lon - lon0) / (lon1 - lon0) * W, (la0 - lat) / (la0 - la1) * MAP_H)

def draw_borders(img, rect, alpha):
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    lon0, lon1, la0, la1 = rect
    wpx = 1 if (lon1 - lon0) > 120 else 2
    for r in rings:
        if r[:, 0].max() < lon0 or r[:, 0].min() > lon1 or r[:, 1].min() > la0 or r[:, 1].max() < la1:
            continue
        x, y = project(rect, r[:, 0], r[:, 1])
        d.line(list(zip(x.tolist(), y.tolist())), fill=(255, 255, 255, alpha), width=wpx)
    img.paste(Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB'))

# ---------------------------------------------------------------- timeline
T_INTRO = 4.0
T_RISE = 52.0
T_HOLD = 3.0
TOURS = [  # (name, rect, caption)
    ('High Asia', cam_rect(80, 34, 52), 'The last big refuge: the roof of the world'),
    ('The Andes', cam_rect(-70, -15, 40), 'A thin spine of islands along South America'),
    ('East Africa', cam_rect(38, 3, 40), 'The Ethiopian Highlands become an island nation'),
]
T_MOVE, T_STAY = 2.2, 3.6
T_TOUR = len(TOURS) * (T_MOVE + T_STAY) + T_MOVE
T_BOARD = 9.0
T_END = 4.0
TOTAL = T_INTRO + T_RISE + T_HOLD + T_TOUR + T_BOARD + T_END

def level_at(t):
    u = min(max((t - T_INTRO) / T_RISE, 0), 1)
    k = 3.6
    return MAXL * (math.exp(k * u) - 1) / (math.exp(k) - 1)

def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

half_level = next(c['elim'] for i, c in enumerate(events) if NCOUNT - (i + 1) <= NCOUNT / 2)
def remaining(L): return sum(1 for c in sov if c['elim'] > L)
CAPTIONS = [  # (level from, level to, text)
    (0.5, 12, 'Every coastline on Earth starts to retreat'),
    (40, 90, 'Melting ALL of Earth\'s ice would add about 70 m. From here on, it\'s pure "what if".'),
    (130, 300, 'Low countries and island nations vanish first'),
    (half_level * 0.97, half_level * 1.12, 'Half of the world\'s countries are now gone'),
    (950, 1350, 'Continents break apart into mountain archipelagos'),
    (2050, 2499, 'Only the great mountain ranges remain'),
]

# ---------------------------------------------------------------- HUD
F_BIG = font('k', 78); F_UNIT = font('b', 34); F_LBL = font('s', 22); F_TICK = font('s', 24)
F_CAP = font('b', 34); F_SMALL = font('r', 18); F_TITLE = font('k', 92); F_SUB = font('s', 36)
F_NAME = font('b', 22)

def text_c(d, xy, s, f, fill, anchor='mm', stroke=0, sfill=(0, 0, 0)):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sfill)

def hud(img, t, L, hud_a):
    d = ImageDraw.Draw(img, 'RGBA')
    a = int(255 * hud_a)
    if a <= 0: return
    # top bar
    d.text((48, 32), 'SEA LEVEL', font=F_LBL, fill=(150, 175, 205, a))
    s = f'+{L:,.0f}'
    d.text((44, 58), s, font=F_BIG, fill=(255, 255, 255, a))
    wv = d.textlength(s, font=F_BIG)
    d.text((44 + wv + 10, 92), 'm', font=F_UNIT, fill=(*ACC, a))
    rem = remaining(L)
    d.text((W - 48, 32), 'COUNTRIES WITH LAND LEFT', font=F_LBL, fill=(150, 175, 205, a), anchor='ra')
    tot = f' / {NCOUNT}'
    d.text((W - 48, 136), tot, font=F_UNIT, fill=(*ACC, a), anchor='rs')
    d.text((W - 48 - d.textlength(tot, font=F_UNIT) - 6, 58), f'{rem}', font=F_BIG, fill=(255, 255, 255, a), anchor='ra')
    # bottom bar: progress + ticker
    y0 = TOP + MAP_H + 34
    x0, x1 = 48, 760
    d.rounded_rectangle((x0, y0, x1, y0 + 12), 6, fill=(40, 56, 84, a))
    p = L / MAXL
    d.rounded_rectangle((x0, y0, x0 + max(12, (x1 - x0) * p), y0 + 12), 6, fill=(*ACC, a))
    for m in (0, 500, 1000, 1500, 2000, 2500):
        xm = x0 + (x1 - x0) * m / MAXL
        d.text((xm, y0 + 26), f'{m:,}', font=F_SMALL, fill=(130, 150, 180, a), anchor='ma')
    d.text((x0, y0 + 64), 'Data: GMT Earth Relief 6′ (smoothed: peaks read low) · Natural Earth',
           font=F_SMALL, fill=(100, 118, 148, a))
    gone = [c for c in events if c['elim'] <= L][-4:]
    d.text((860, y0 - 6), 'JUST LOST', font=F_LBL, fill=(240, 120, 110, a))
    for i, c in enumerate(reversed(gone)):
        fade = a if i < 3 else a // 3
        x = 860 + (i % 2) * 520; y = y0 + 26 + (i // 2) * 40
        d.text((x, y), c['name'], font=F_TICK, fill=(235, 240, 248, fade))
        d.text((x + 470, y), f'+{c["elim"]:,.0f} m', font=F_TICK, fill=(*ACC, fade), anchor='ra')

def caption(img, s, alpha, y=TOP + 46):
    if alpha <= 0: return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    tw = d.textlength(s, font=F_CAP)
    d.rounded_rectangle((W / 2 - tw / 2 - 28, y - 32, W / 2 + tw / 2 + 28, y + 32), 32,
                        fill=(8, 16, 32, int(200 * alpha)))
    text_c(d, (W / 2, y), s, F_CAP, (255, 255, 255, int(255 * alpha)))
    img.paste(Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB'))

def pulses(img, rect, L):
    """Expanding ring + name where a country has just disappeared."""
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    # how long ago (in metres -> seconds) each country went under
    recent = [c['i'] for c in events if c['elim'] <= L][-3:]
    for c in events:
        if c['elim'] > L: break
        # convert level difference into time difference via inverse of curve
        dt = t_of_level(L) - t_of_level(c['elim'])
        if dt > 1.6: continue
        x, y = project(rect, c['lx'], c['ly'])
        r = 6 + 40 * dt
        a = int(255 * (1 - dt / 1.6))
        d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 110, 100, a), width=3)
        if c['i'] in recent:
            text_c(d, (x, y - 22), c['name'], F_NAME, (255, 255, 255, a), stroke=3, sfill=(10, 20, 40, a))
    img.paste(Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB'))

def t_of_level(L):
    k = 3.6
    u = math.log(L / MAXL * (math.exp(k) - 1) + 1) / k
    return T_INTRO + u * T_RISE

def survivor_labels(img, rect, alpha):
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for c in sov:
        if c['elim'] <= MAXL: continue
        x, y = project(rect, c['lx'], c['ly'])
        if not (40 < x < W - 40 and 20 < y < MAP_H - 20): continue
        a = int(255 * alpha)
        text_c(d, (x, y - 12), c['name'], F_NAME, (255, 255, 255, a), stroke=3, sfill=(10, 20, 40, a))
        text_c(d, (x, y + 14), f'{c["pct2500"] * 100:.0f}% left', F_SMALL, (*ACC, a), stroke=3,
               sfill=(10, 20, 40, a))
    img.paste(Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB'))

def board(img, t):
    """Leaderboard: share of each country's land still above water."""
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle((0, 0, W, H), fill=(*BG, int(235 * ease(t / 0.8))))
    a = int(255 * ease(t / 0.8))
    text_c(d, (W / 2, 110), 'At +2,500 m, who keeps the most land?', F_SUB, (255, 255, 255, a))
    text_c(d, (W / 2, 160), f'{remaining(MAXL)} of {NCOUNT} countries still have dry ground. These keep the biggest share of it:',
           F_LBL, (150, 175, 205, a))
    top = sorted([c for c in sov if c['elim'] > MAXL], key=lambda c: -c['pct2500'])[:8]
    for i, c in enumerate(top):
        y = 240 + i * 92
        g = ease((t - 0.6 - i * 0.18) / 1.4)
        d.text((520, y + 26), c['name'], font=F_TICK, fill=(235, 240, 248, a), anchor='rm')
        bw = 900 * c['pct2500'] / top[0]['pct2500'] * g
        col = ACC if i else (255, 200, 90)
        d.rounded_rectangle((550, y + 6, 550 + max(bw, 8), y + 46), 10, fill=(*col, a))
        d.text((566 + bw, y + 26), f'{c["pct2500"] * 100 * g:.0f}%', font=F_TICK, fill=(255, 255, 255, a), anchor='lm')

# ---------------------------------------------------------------- frame
def tour_rect(tt):
    """camera rect during the tour section, tt seconds into it."""
    stops = [GLOBAL] + [r for _, r, _ in TOURS] + [GLOBAL]
    seg = T_MOVE + T_STAY
    i = int(tt // seg); k = tt - i * seg
    if i >= len(TOURS):
        return lerp_rect(stops[-2], stops[-1], ease(k / T_MOVE)), None, 0
    if k < T_MOVE:
        a, b = stops[i], stops[i + 1]
        if a == GLOBAL or b == GLOBAL:
            return lerp_rect(a, b, ease(k / T_MOVE)), i, ease((k - T_MOVE + 0.6) / 0.6)
        u = ease(k / T_MOVE)
        sa, sb = a[1] - a[0], b[1] - b[0]
        span = math.exp(math.log(sa) + (math.log(sb) - math.log(sa)) * u + math.log(3.2) * math.sin(math.pi * u))
        cx = (a[0] + a[1]) / 2 + ((b[0] + b[1]) / 2 - (a[0] + a[1]) / 2) * u
        cy = (a[2] + a[3]) / 2 + ((b[2] + b[3]) / 2 - (a[2] + a[3]) / 2) * u
        span = min(span, 300)
        half_lat = span * MAP_H / W / 2
        cy = min(max(cy, LAT1 + half_lat), LAT0 - half_lat)
        return cam_rect(cx, cy, span), i, ease((k - T_MOVE + 0.6) / 0.6)
    return stops[i + 1], i, min(1, (T_STAY - (k - T_MOVE)) / 0.5)

def frame(n):
    t = n / FPS
    img = Image.new('RGB', (W, H), BG)
    L = level_at(t)
    rect = GLOBAL; tour_i = None; tour_a = 0
    t_tour0 = T_INTRO + T_RISE + T_HOLD
    if t_tour0 <= t < t_tour0 + T_TOUR:
        rect, tour_i, tour_a = tour_rect(t - t_tour0)
    m = render_map(rect, max(L, 0.01))
    draw_borders(m, rect, 70 if rect == GLOBAL else 110)
    if t < t_tour0:
        pulses(m, rect, L)
    if tour_i is not None:
        survivor_labels(m, rect, max(tour_a, 0))
    img.paste(m, (0, TOP))
    d = ImageDraw.Draw(img)
    d.line((0, TOP, W, TOP), fill=(30, 46, 72)); d.line((0, TOP + MAP_H, W, TOP + MAP_H), fill=(30, 46, 72))
    hud(img, t, L, ease((t - T_INTRO + 0.6) / 0.8))
    if t < T_INTRO + 0.4:   # title card
        a = ease(t / 0.8) * (1 - ease((t - T_INTRO + 0.8) / 1.0))
        ov = Image.new('RGBA', img.size, (*BG, int(170 * a))); od = ImageDraw.Draw(ov)
        text_c(od, (W / 2, H / 2 - 40), 'WHAT IF THE OCEAN ROSE', F_TITLE, (255, 255, 255, int(255 * a)))
        text_c(od, (W / 2, H / 2 + 60), '2,500 METERS?', F_TITLE, (*ACC, int(255 * a)))
        text_c(od, (W / 2, H / 2 + 150), 'Real elevation data · every country counted', F_SUB,
               (180, 200, 225, int(255 * a)))
        img = Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')
    if T_INTRO <= t < t_tour0:
        for lo, hi, s in CAPTIONS:
            if lo <= L <= hi:
                tl, th = t_of_level(max(lo, 0.01)), t_of_level(hi)
                a = min(ease((t - tl) / 0.5), ease((th - t) / 0.5))
                caption(img, s, a)
    if tour_i is not None and tour_a > 0:
        caption(img, TOURS[tour_i][2], tour_a)
    tb = t_tour0 + T_TOUR
    if tb <= t < tb + T_BOARD:
        a = 1 - ease((t - (tb + T_BOARD - 0.6)) / 0.6)
        b = img.copy(); board(b, t - tb)
        img = Image.blend(img, b, a) if a < 1 else b
    if t >= tb + T_BOARD:
        te = t - tb - T_BOARD
        d = ImageDraw.Draw(img, 'RGBA')
        d.rectangle((0, 0, W, H), fill=(*BG, int(225 * ease(te / 0.6))))
        a = int(255 * ease((te - 0.3) / 0.6) * (1 - ease((te - T_END + 0.7) / 0.7)))
        text_c(d, (W / 2, H / 2 - 30), 'The oceans would need to rise 8,849 m to cover Everest.', F_SUB, (255, 255, 255, a))
        text_c(d, (W / 2, H / 2 + 30), 'Real-world sea level rise this century: under 1 m. Still enough to redraw coastlines.',
               F_LBL, (150, 175, 205, a))
        img = img
    return np.asarray(img, np.uint8).tobytes()

def make_audio(path):
    import wave
    SR = 44100; n = int(TOTAL * SR); t = np.arange(n) / SR
    out = np.zeros(n, np.float64)
    env = np.clip(t / 3, 0, 1) * np.clip((TOTAL - t) / 3, 0, 1)
    for f, a in ((110, .05), (164.8, .035), (220, .03), (261.6, .022), (329.6, .015)):
        out += a * np.sin(2 * np.pi * f * t + np.sin(2 * np.pi * 0.07 * t) * 2) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.13 * t + f))
    out *= env
    # rising sub tone + "water" noise during the rise
    lv = np.array([level_at(x) for x in t[::441]]); lv = np.interp(np.arange(n), np.arange(0, n, 441), lv) / MAXL
    rising = (t > T_INTRO) & (t < T_INTRO + T_RISE + T_HOLD + 1)
    ph = np.cumsum(2 * np.pi * (55 + 55 * lv) / SR)
    out += rising * 0.05 * np.sqrt(lv) * np.sin(ph)
    rng = np.random.default_rng(1); nz = rng.standard_normal(n)
    k = 400; nz = np.convolve(nz, np.ones(k) / k, 'same') * 6
    out += rising * 0.03 * (0.3 + lv) * nz * (0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * t))
    def blip(t0, f, a, dur=0.18):
        i0 = int(t0 * SR); m = int(dur * SR)
        if i0 + m >= n: return
        tt = np.arange(m) / SR
        out[i0:i0 + m] += a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 22) * np.minimum(tt * 400, 1)
    def bell(t0, f, a):
        i0 = int(t0 * SR); m = int(2.5 * SR)
        if i0 + m >= n: m = n - i0 - 1
        tt = np.arange(m) / SR
        for r, w in ((1, 1), (2.76, .4), (5.4, .2)):
            out[i0:i0 + m] += a * w * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * (1.6 * r))
    notes = [523.3, 587.3, 659.3, 784, 880]
    for j, c in enumerate([e for e in events if e['elim'] <= MAXL]):
        blip(t_of_level(max(c['elim'], 0.01)), notes[j % 5], 0.06)
    for m in (500, 1000, 1500, 2000, 2500):
        bell(t_of_level(m), 440, 0.09)
    t0 = T_INTRO + T_RISE + T_HOLD
    for i in range(len(TOURS)):
        bell(t0 + i * (T_MOVE + T_STAY) + T_MOVE, 330, 0.07)
    tb = t0 + T_TOUR
    for i in range(8):
        blip(tb + 0.6 + i * 0.18, notes[i % 5] / 2, 0.08, 0.3)
    bell(tb + T_BOARD + 0.3, 220, 0.1)
    out = np.tanh(out * 1.6) * 0.8
    st = np.stack([out, np.roll(out, 300)], 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == '__main__':
    if OUT.endswith('.wav'):
        make_audio(OUT); sys.exit()
    N = int(TOTAL * FPS)
    if LIMIT: N = min(N, LIMIT)
    if OUT.endswith('.png'):
        Image.frombytes('RGB', (W, H), frame(int(float(sys.argv[3]) * FPS))).save(OUT); sys.exit()
    print(f'{N} frames, {TOTAL:.1f}s, {NCOUNT} countries, half at {half_level:.0f} m', flush=True)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
                           '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    with Pool(4) as p:
        for i, b in enumerate(p.imap(frame, range(N), chunksize=4)):
            ff.stdin.write(b)
            if i % 150 == 0: print(i, flush=True)
    ff.stdin.close(); ff.wait()
