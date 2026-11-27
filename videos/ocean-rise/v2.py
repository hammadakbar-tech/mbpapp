"""v2: flag-map 'ocean rises until one country is left' video with narration, music and SFX.

usage: python v2.py DATA_DIR OUT.mp4            full render
       python v2.py DATA_DIR frame.png SECONDS  single still
"""
import json, math, sys, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from scipy import ndimage

D, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FPS, W, H = 30, 1920, 1080
FONT = '/usr/share/fonts/opentype/inter/'
_fc = {}
def font(w, s):
    k = (w, s)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT + {'b': 'Inter-Bold.otf', 'x': 'Inter-ExtraBold.otf', 's': 'Inter-SemiBold.otf',
                                            'r': 'Inter-Regular.otf', 'k': 'Inter-Black.otf', 'm': 'Inter-Medium.otf'}[w], s)
    return _fc[k]

# ------------------------------------------------------------------ data
z = np.load(D + '/z.npy').astype(np.float32)
fl = np.load(D + '/fl.npy').astype(np.float32)
fl = np.where(np.isfinite(fl) & (fl < 1e5), fl, z)
ZH, ZW = z.shape
def hillshade(a):
    gy, gx = np.gradient(a)
    sl = np.arctan(np.hypot(gx, gy) / 900)
    asp = np.arctan2(-gx, gy)
    az, alt = math.radians(315), math.radians(45)
    return np.clip(np.sin(alt) * np.cos(sl) + np.cos(alt) * np.sin(sl) * np.cos(az - asp), 0, 1).astype(np.float32)
HS = hillshade(np.maximum(z, 0))

EXCLUDE = {'Jersey', 'Guernsey', 'Isle of Man', 'Åland', 'Aruba', 'Curaçao', 'Sint Maarten', 'Hong Kong', 'Macao',
           'Greenland', 'Somaliland', 'N. Cyprus', 'Faeroe Is.', 'Cook Is.', 'Niue'}
S = [s for s in json.load(open(D + '/sink2.json')) if s['name'] not in EXCLUDE and s.get('half') is not None]
for s in S:
    s['half'] = max(1.0, round(s['half']))
NICE = {'United States of America': 'United States', 'Dem. Rep. Congo': 'DR Congo', 'Central African Rep.': 'Central African Rep.',
        'Bosnia and Herz.': 'Bosnia & Herzegovina', 'Dominican Rep.': 'Dominican Republic', 'Eq. Guinea': 'Equatorial Guinea',
        'S. Sudan': 'South Sudan', 'Solomon Is.': 'Solomon Islands', 'Marshall Is.': 'Marshall Islands',
        'St. Vin. and Gren.': 'St Vincent & Grenadines', 'Antigua and Barb.': 'Antigua & Barbuda',
        'St. Kitts and Nevis': 'St Kitts & Nevis', 'São Tomé and Principe': 'São Tomé & Príncipe', 'W. Sahara': 'Western Sahara'}
for s in S:
    s['disp'] = NICE.get(s['name'], s['name'])
BYNAME = {s['name']: s for s in S}
NCOUNT = len(S)
ORDER = sorted(S, key=lambda s: (s['half'], s['name']))
LAST = ORDER[-1]

gj = json.load(open(D + '/countries.geojson'))
POLY = {}   # feature index -> list of rings (np arrays) [outer rings only + holes ignored]
for i, ft in enumerate(gj['features'], 1):
    g = ft['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    POLY[i] = [np.array(p[0], np.float64) for p in polys if len(p[0]) > 2]
IDX = {s['i']: s for s in S}
HIRES_LUT = np.zeros(max(POLY) + 1, bool)
for s in S:
    if s.get('hires'): HIRES_LUT[s['i']] = True

FLAG = {}
def flag_img(iso):
    if iso not in FLAG:
        p = f'{ROOT}/flags/png/{iso}.png'
        FLAG[iso] = Image.open(p).convert('RGB') if os.path.exists(p) else Image.new('RGB', (64, 48), (200, 200, 200))
    return FLAG[iso]

# ------------------------------------------------------------------ narration script
from script import build_script   # noqa: E402
BEATS = build_script(S, BYNAME, ORDER, NCOUNT)

# ------------------------------------------------------------------ voice
TTS_DIR = ROOT + '/tts'
def synth_all():
    from kokoro_onnx import Kokoro
    import soundfile as sf
    k = None
    os.makedirs(TTS_DIR + '/lines', exist_ok=True)
    for i, b in enumerate(BEATS):
        if not b.get('say'): b['vo'] = None; b['vo_len'] = 0; continue
        key = f"{abs(hash(b['say'])) % 10**10}"
        p = f"{TTS_DIR}/lines/{key}.wav"
        if not os.path.exists(p):
            if k is None: k = Kokoro(TTS_DIR + '/kokoro-v1.0.onnx', TTS_DIR + '/voices-v1.0.bin')
            a, sr = k.create(b['say'], voice='am_michael', speed=1.08, lang='en-us')
            sf.write(p, a, sr)
        info = sf.info(p)
        b['vo'] = p; b['vo_len'] = info.frames / info.samplerate

# hash() is salted per process; make it stable
os.environ.setdefault('PYTHONHASHSEED', '0')
import hashlib
def _stable(s): return int(hashlib.md5(s.encode()).hexdigest()[:10], 16)
hash = _stable  # noqa: A001
synth_all()

# ------------------------------------------------------------------ timeline
t = 0.0
lvl = 0.0
for b in BEATS:
    b['t0'] = t
    b['dur'] = max(b.get('min', 0), b['vo_len'] + b.get('pad', 0.55))
    b['l0'] = lvl
    b['l1'] = b.get('level', lvl)
    lvl = b['l1']
    t += b['dur']
TOTAL = t

def ease(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def ease_out(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3

def beat_at(tt):
    for i, b in enumerate(BEATS):
        if tt < b['t0'] + b['dur']: return i, b
    return len(BEATS) - 1, BEATS[-1]

def level_at(tt):
    i, b = beat_at(tt)
    u = (tt - b['t0']) / b['dur']
    rs, re_ = b.get('rise', (0.0, 0.85))
    v = ease((u - rs) / (re_ - rs))
    # geometric interpolation feels better across orders of magnitude
    a, c = b['l0'], b['l1']
    if a > 0.5 and c > 0.5:
        return a * (c / a) ** v
    return a + (c - a) * v

# when does each country sink (time)
_lv_t = np.arange(0, TOTAL, 1 / FPS)
_lv = np.array([level_at(x) for x in _lv_t])
_lv_max = np.maximum.accumulate(_lv)
for s in S:
    k = np.searchsorted(_lv_max, s['half'])
    s['t_sink'] = float(_lv_t[k]) if k < len(_lv_t) else 1e9

# camera
GLOBAL = (10.0, 12.0, 400.0)   # lon_c, lat_c, span_lon
def cam_of(b):
    c = b.get('cam')
    if c is None: return GLOBAL
    if isinstance(c, str):
        s = BYNAME[c]; x0, y0, x1, y1 = s['bbox']
        span = max((x1 - x0) * 2.6, (y0 - y1) * 2.6 * W / H, 9)
        return ((x0 + x1) / 2, (y0 + y1) / 2 - 0.08 * span * H / W, span)
    return c
def cam_lerp(a, b, u):
    s = math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * u)
    # zoom out in the middle of long moves
    dist = math.hypot(a[0] - b[0], a[1] - b[1])
    bump = min(dist / max(a[2], b[2]), 1.5) * math.sin(math.pi * u)
    s *= math.exp(bump)
    w = u
    return (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w, s)
def camera(tt):
    i, b = beat_at(tt)
    prev = cam_of(BEATS[i - 1]) if i > 0 else GLOBAL
    cur = cam_of(b)
    u = ease((tt - b['t0']) / min(1.6, b['dur'] * 0.6))
    c = cam_lerp(prev, cur, u)
    # slow push-in while holding
    push = 1 - 0.06 * ease((tt - b['t0']) / b['dur'])
    return (c[0], c[1], c[2] * push)

def rect_of(cam):
    lon, lat, span = cam
    span_lat = span * H / W
    span_lat = min(span_lat, 200)
    return (lon - span / 2, lon + span / 2, lat + span_lat / 2, lat - span_lat / 2)

# ------------------------------------------------------------------ map rendering
def sample(arr, rect, fill):
    lon0, lon1, la0, la1 = rect
    xs = ((np.linspace(lon0, lon1, W, endpoint=False) + 180) % 360) / 360 * ZW
    ys = (90 - np.linspace(la0, la1, H, endpoint=False)) / 180 * (ZH - 1)
    X, Y = np.meshgrid(xs, ys)
    out = ndimage.map_coordinates(arr, [Y, X], order=1, mode='grid-wrap')
    out[(Y < 0) | (Y > ZH - 1)] = fill
    return out.astype(np.float32)

def project(rect, lon, lat):
    lon0, lon1, la0, la1 = rect
    x = (lon - lon0) / (lon1 - lon0) * W
    y = (la0 - lat) / (la0 - la1) * H
    return x, y

_cache = {}
def static_layers(rect):
    """per-camera layers: sampled grids, country-id raster, flag canvas, grey canvas."""
    key = tuple(round(v, 4) for v in rect)
    if key in _cache: return _cache[key]
    if len(_cache) > 2: _cache.clear()
    flc = sample(fl, rect, -5000)
    zc = sample(z, rect, -5000)
    hsc = sample(HS, rect, 0.7)
    lon0, lon1, la0, la1 = rect
    idim = Image.new('I', (W, H), 0)
    dr = ImageDraw.Draw(idim)
    outlines = []
    flag_canvas = Image.new('RGB', (W, H), (0, 0, 0))
    for fi, rings in POLY.items():
        for shift in (-360, 0, 360):
            for r in rings:
                xs = r[:, 0] + shift
                if xs.max() < lon0 or xs.min() > lon1 or r[:, 1].min() > la0 or r[:, 1].max() < la1: continue
                x, y = project(rect, xs, r[:, 1])
                pts = list(zip(x.tolist(), y.tolist()))
                dr.polygon(pts, fill=fi)
                outlines.append(pts)
    ids_out = np.asarray(idim, np.int32)
    present = np.unique(ids_out)
    for fi in present:
        if fi == 0 or fi not in IDX: continue
        s = IDX[fi]
        m = ids_out == fi
        ys, xs = np.nonzero(m)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        bw, bh = x1 - x0, y1 - y0
        f = flag_img(s['iso'])
        # cover-fit the flag into the country's bbox (on screen)
        sc = max(bw / f.width, bh / f.height)
        fw, fh = max(1, int(f.width * sc + 1)), max(1, int(f.height * sc + 1))
        fr = f.resize((fw, fh), Image.BILINEAR)
        ox, oy = x0 - (fw - bw) // 2, y0 - (fh - bh) // 2
        mask = Image.fromarray((m[y0:y1, x0:x1] * 255).astype(np.uint8))
        crop = fr.crop((x0 - ox, y0 - oy, x0 - ox + bw, y0 - oy + bh))
        flag_canvas.paste(crop, (x0, y0), mask)
    fc = np.asarray(flag_canvas, np.float32)
    nf = np.array([0] + [0] * 0)
    grey = fc.mean(-1, keepdims=True) * 0.35 + 150
    border = Image.new('L', (W, H), 0)
    bd = ImageDraw.Draw(border)
    wpx = 1 if (lon1 - lon0) > 150 else 2
    for pts in outlines:
        bd.line(pts + [pts[0]], fill=255, width=wpx)
    border = np.asarray(border, np.float32) / 255
    res = dict(fl=flc, z=zc, hs=hsc, ids=ids_out, flag=fc, grey=np.repeat(grey, 3, -1), border=border)
    _cache[key] = res
    return res

# ocean background texture
_rng = np.random.default_rng(2)
def _noise(h, w, scale):
    n = _rng.standard_normal((h // scale + 2, w // scale + 2)).astype(np.float32)
    return np.asarray(Image.fromarray(n).resize((w + scale * 2, h + scale * 2), Image.BICUBIC))[:h, :w]
WAVES = (_noise(H + 200, W + 200, 40) * 0.6 + _noise(H + 200, W + 200, 12) * 0.4)
yy, xx = np.mgrid[0:H, 0:W]
VIGN = (1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)).astype(np.float32)

def render_map(tt, L, rect, sunk_ids):
    st = static_layers(rect)
    flc, zc, hsc = st['fl'], st['z'], st['hs']
    water = flc < L
    # ocean colour by depth below current sea level, lighter for freshly drowned land
    depth = np.maximum(L - zc, 0)
    dn = np.clip(np.log1p(depth) / np.log1p(6000), 0, 1)
    deep = np.array([10, 46, 120], np.float32); mid = np.array([22, 96, 186], np.float32)
    shallow = np.array([70, 170, 225], np.float32)
    c1 = np.clip(dn * 1.6, 0, 1)[..., None]
    oc = shallow * (1 - c1) + mid * c1
    c2 = np.clip((dn - 0.6) / 0.4, 0, 1)[..., None]
    oc = oc * (1 - c2) + deep * c2
    ox = int(tt * 6) % 200; oy = int(tt * 3) % 200
    wv = WAVES[oy:oy + H, ox:ox + W]
    oc = oc * (1 + 0.035 * wv[..., None]) * VIGN[..., None]
    # land: flag texture with relief shading; sunk countries greyed
    ids = st['ids']
    sunk_lut = np.zeros(max(POLY) + 1, bool)
    for i in sunk_ids: sunk_lut[i] = True
    is_sunk = sunk_lut[ids]
    # small countries measured with high-res data: keep them visible until they actually sink
    keep = HIRES_LUT[ids] & ~is_sunk
    water = water & ~keep
    base = np.where(is_sunk[..., None], st['grey'], st['flag'])
    no_country = ids == 0
    base[no_country] = (150, 160, 150)
    shade = (0.72 + 0.45 * hsc)[..., None]
    land = base * shade
    land = land * (1 - 0.55 * st['border'][..., None])
    img = np.where(water[..., None], oc, land)
    # coastline glow: thin bright band where water is shallow relative to level
    coast = water & (depth < max(4, L * 0.04))
    img[coast] = img[coast] * 0.6 + np.array([150, 215, 245]) * 0.4
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

# ------------------------------------------------------------------ UI pieces
WHITE = (255, 255, 255); NAVY = (8, 20, 48); ACC = (255, 196, 46); RED = (232, 62, 62); CY = (120, 210, 255)

def panel(d, box, r=22, fill=(8, 22, 54, 215), outline=(255, 255, 255, 40)):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=2)

def fmt_m(v): return f'{v:,.0f} m'

def draw_hud(img, tt, L, remaining, a=1.0):
    if a <= 0: return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    A = lambda c, k=255: (*c, int(k * a))
    # sea level pill, top-left
    panel(d, (36, 30, 470, 150), fill=(8, 22, 54, int(215 * a)), outline=(255, 255, 255, int(40 * a)))
    d.text((64, 46), 'SEA LEVEL', font=font('b', 22), fill=A(CY))
    s = f'+{L:,.0f}' if L >= 1 else f'+{L:.1f}'
    d.text((60, 70), s, font=font('k', 66), fill=A(WHITE))
    d.text((70 + d.textlength(s, font=font('k', 66)), 104), 'm', font=font('x', 34), fill=A(ACC))
    # gauge (log), left
    gx, gy0, gy1 = 60, 200, 860
    d.rounded_rectangle((gx, gy0, gx + 26, gy1), 13, fill=(8, 22, 54, int(200 * a)), outline=(255, 255, 255, int(50 * a)), width=2)
    def gy(v): return gy1 - (math.log10(max(v, 1)) / math.log10(4000)) * (gy1 - gy0)
    y = gy(L)
    d.rounded_rectangle((gx + 4, min(y, gy1 - 18), gx + 22, gy1 - 4), 9, fill=A((70, 170, 240)))
    for v in (1, 10, 100, 1000):
        d.line((gx + 30, gy(v), gx + 40, gy(v)), fill=A(WHITE, 140), width=2)
        d.text((gx + 46, gy(v)), f'{v:,} m', font=font('b', 18), fill=A(WHITE, 230), anchor='lm', stroke_width=3, stroke_fill=(8, 20, 48, int(200 * a)))
    # survivors, top-right
    panel(d, (W - 330, 30, W - 36, 150), fill=(8, 22, 54, int(215 * a)), outline=(255, 255, 255, int(40 * a)))
    d.text((W - 64, 46), 'STILL AFLOAT', font=font('b', 22), fill=A(CY), anchor='ra')
    tot = f'/ {NCOUNT}'
    d.text((W - 64, 136), tot, font=font('x', 30), fill=A(WHITE, 160), anchor='rs')
    d.text((W - 72 - d.textlength(tot, font=font('x', 30)), 70), f'{remaining}', font=font('k', 66), fill=A(WHITE), anchor='ra')
    img.alpha_composite(ov)

def draw_next(img, L, a, highlight=None):
    """'Next to sink' list on the right."""
    if a <= 0: return
    nxt = [s for s in ORDER if s['half'] > L][:6]
    if not nxt: return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    A = lambda c, k=255: (*c, int(k * a))
    x0, y0 = W - 400, 176
    hgt = 62 + 52 * len(nxt)
    panel(d, (x0, y0, W - 36, y0 + hgt), fill=(8, 22, 54, int(205 * a)), outline=(255, 255, 255, int(40 * a)))
    d.text((x0 + 24, y0 + 18), 'NEXT TO SINK', font=font('k', 22), fill=A(RED))
    for k, s in enumerate(nxt):
        y = y0 + 58 + k * 52
        f = flag_img(s['iso']).resize((48, 36))
        ov.paste(f, (x0 + 24, y + 4))
        d.rectangle((x0 + 24, y + 4, x0 + 72, y + 40), outline=A(WHITE, 90))
        name = s['disp'] if len(s['disp']) < 17 else s['disp'][:15] + '…'
        d.text((x0 + 86, y + 22), name, font=font('b', 22), fill=A(WHITE), anchor='lm')
        d.text((W - 60, y + 22), fmt_m(s['half']), font=font('x', 22), fill=A(ACC), anchor='rm')
    if a < 1:
        # paste flags were opaque; fade by blending alpha channel
        al = np.asarray(ov)[..., 3].astype(np.float32)
        arr = np.asarray(ov).copy(); arr[..., 3] = np.minimum(al, 255 * a).astype(np.uint8)
        ov = Image.fromarray(arr)
    img.alpha_composite(ov)

def draw_card(img, s, a, sub):
    if a <= 0: return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    A = lambda c, k=255: (*c, int(k * a))
    off = int((1 - ease_out(a)) * 60)
    x0, y0, x1, y1 = 440, H - 190 + off, W - 440, H - 46 + off
    panel(d, (x0, y0, x1, y1), r=26, fill=(8, 22, 54, int(225 * a)), outline=(255, 255, 255, int(60 * a)))
    f = flag_img(s['iso']).resize((136, 102))
    m = Image.new('L', f.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 135, 101), 12, fill=int(255 * a))
    ov.paste(f, (x0 + 22, y0 + 21), m)
    d.text((x0 + 182, y0 + 30), s['disp'].upper(), font=font('k', 46), fill=A(WHITE))
    d.text((x0 + 182, y0 + 92), sub, font=font('m', 24), fill=A(WHITE, 200))
    d.text((x1 - 30, y0 + 34), 'HALF UNDERWATER AT', font=font('b', 18), fill=A(CY), anchor='ra')
    d.text((x1 - 30, y0 + 60), f'+{s["half"]:,.0f} m', font=font('k', 48), fill=A(ACC), anchor='ra')
    img.alpha_composite(ov)

def draw_stamp(img, text, age, color=RED, pos=(W // 2, 300)):
    if age < 0 or age > 2.6: return
    a = min(1, (2.6 - age) / 0.4)
    sc = 2.2 - 1.2 * ease_out(age / 0.18) if age < 0.18 else 1 + 0.04 * math.exp(-age * 6) * math.sin(age * 40)
    f = font('k', 92)
    tmp = Image.new('RGBA', (900, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((450 - tw / 2 - 40, 50, 450 + tw / 2 + 40, 210), 22, outline=(*color, 255), width=12,
                        fill=(255, 255, 255, 235))
    d.text((450, 132), text, font=f, fill=(*color, 255), anchor='mm')
    tmp = tmp.rotate(-8, resample=Image.BICUBIC, expand=False)
    tmp = tmp.resize((int(900 * sc), int(260 * sc)), Image.BICUBIC)
    arr = np.asarray(tmp).copy(); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8); tmp = Image.fromarray(arr)
    img.alpha_composite(tmp, (int(pos[0] - tmp.width / 2), int(pos[1] - tmp.height / 2)))

def draw_act(img, b, u):
    a = min(ease(u / 0.15), ease((1 - u) / 0.15))
    if a <= 0: return
    ov = Image.new('RGBA', img.size, (4, 12, 32, int(150 * a))); d = ImageDraw.Draw(ov)
    A = lambda c, k=255: (*c, int(k * a))
    y = H // 2 - 40 + int((1 - ease_out(u / 0.2)) * 30)
    d.text((W // 2, y - 110), b['act_no'], font=font('k', 34), fill=A(ACC), anchor='mm')
    d.text((W // 2, y), b['act'], font=font('k', 150), fill=A(WHITE), anchor='mm')
    d.text((W // 2, y + 110), b['act_sub'], font=font('s', 38), fill=A(WHITE, 220), anchor='mm')
    rng = b.get('act_range')
    if rng:
        tw = d.textlength(rng, font=font('k', 30))
        d.rounded_rectangle((W / 2 - tw / 2 - 26, y + 160, W / 2 + tw / 2 + 26, y + 214), 27, fill=A(ACC))
        d.text((W // 2, y + 187), rng, font=font('k', 30), fill=A(NAVY), anchor='mm')
    img.alpha_composite(ov)

def draw_caption(img, text, a):
    if a <= 0 or not text: return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    f = font('b', 34)
    # wrap
    words = text.split(); lines = []; cur = ''
    for w_ in words:
        if d.textlength(cur + ' ' + w_, font=f) > 1250 and cur: lines.append(cur); cur = w_
        else: cur = (cur + ' ' + w_).strip()
    lines.append(cur)
    y = H - 70 - 46 * (len(lines) - 1)
    for k, ln in enumerate(lines):
        tw = d.textlength(ln, font=f)
        d.rounded_rectangle((W / 2 - tw / 2 - 18, y + k * 46 - 24, W / 2 + tw / 2 + 18, y + k * 46 + 22), 10,
                            fill=(0, 0, 0, int(150 * a)))
        d.text((W / 2, y + k * 46), ln, font=f, fill=(255, 255, 255, int(255 * a)), anchor='mm')
    img.alpha_composite(ov)

def draw_pulses(img, rect, tt, featured):
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    shown = 0
    for s in sorted(S, key=lambda s: -s['t_sink']):
        age = tt - s['t_sink']
        if age < 0 or age > 1.8: continue
        if featured is not None and s is featured: continue
        x, y = project(rect, s['lx'], s['ly'])
        for shift in (-360, 360):
            if not (0 <= x < W):
                x2, _ = project(rect, s['lx'] + shift, s['ly'])
                if 0 <= x2 < W: x = x2
        if not (-50 < x < W + 50 and -50 < y < H + 50): continue
        a = 1 - age / 1.8
        r = 10 + 46 * ease_out(age / 1.8)
        d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 90, 90, int(255 * a)), width=4)
        if shown < 4:
            f = flag_img(s['iso']).resize((42, 32))
            ov.paste(f, (int(x - 21), int(y - 62)))
            d.text((x, y - 74), s['disp'], font=font('b', 22), fill=(255, 255, 255, int(255 * a)), anchor='ms',
                   stroke_width=4, stroke_fill=(8, 20, 48, int(255 * a)))
            shown += 1
    img.alpha_composite(ov)

def draw_labels(img, rect, names, a):
    if a <= 0: return
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for n in names:
        s = BYNAME[n]
        x, y = project(rect, s['lx'], s['ly'])
        if not (60 < x < W - 60 and 60 < y < H - 60): continue
        d.text((x, y), s['disp'], font=font('k', 30), fill=(255, 255, 255, int(255 * a)), anchor='mm',
               stroke_width=5, stroke_fill=(8, 20, 48, int(255 * a)))
    img.alpha_composite(ov)

# ------------------------------------------------------------------ special screens
def title_screen(img, u, b):
    a = min(ease(u / 0.1), ease((1 - u) / 0.1))
    ov = Image.new('RGBA', img.size, (4, 12, 32, int(170 * a))); d = ImageDraw.Draw(ov)
    A = lambda c, k=255: (*c, int(k * a))
    d.text((W // 2, H // 2 - 150), 'THE OCEAN KEEPS RISING', font=font('k', 104), fill=A(WHITE), anchor='mm')
    d.text((W // 2, H // 2 - 30), 'UNTIL ONE COUNTRY IS LEFT', font=font('k', 104), fill=A(ACC), anchor='mm')
    sub = f'{NCOUNT} countries  ·  real NOAA elevation data  ·  a country sinks when half its land is underwater'
    tw = d.textlength(sub, font=font('s', 30))
    d.rounded_rectangle((W / 2 - tw / 2 - 30, H // 2 + 70, W / 2 + tw / 2 + 30, H // 2 + 128), 29, fill=A((20, 60, 130)))
    d.text((W // 2, H // 2 + 99), sub, font=font('s', 30), fill=A(WHITE), anchor='mm')
    img.alpha_composite(ov)

ACTS = []   # filled from script: (name, lo, hi)
def final_board(img, u, b):
    a = ease(u / 0.06)
    ov = Image.new('RGBA', img.size, (4, 12, 32, int(235 * a))); d = ImageDraw.Draw(ov)
    A = lambda c, k=255: (*c, int(k * a))
    d.text((W // 2, 80), 'WHEN DID YOUR COUNTRY SINK?', font=font('k', 64), fill=A(WHITE), anchor='mm')
    groups = b['groups']
    y = 160
    fw, fh, gap = 60, 44, 7
    per_row = 23
    reveal_n = int(ease(u / 0.75) * NCOUNT * 1.05)
    k = 0
    for gname, grange, members in groups:
        rows = math.ceil(len(members) / per_row) or 1
        d.text((60, y + 4), gname, font=font('k', 26), fill=A(ACC))
        d.text((60, y + 38), grange, font=font('s', 18), fill=A(WHITE, 170))
        for j, s in enumerate(members):
            k += 1
            if k > reveal_n: break
            r, c = divmod(j, per_row)
            x = 330 + c * (fw + gap); yy_ = y + r * (fh + gap)
            ov.paste(flag_img(s['iso']).resize((fw, fh)), (x, yy_))
        y += rows * (fh + gap) + 26
    # winner
    if u > 0.78:
        a2 = ease((u - 0.78) / 0.08) * a
        s = LAST
        bx = (W / 2 - 520, H - 150, W / 2 + 520, H - 50)
        d.rounded_rectangle(bx, 30, fill=(*ACC, int(255 * a2)))
        ov.paste(flag_img(s['iso']).resize((88, 66)), (int(bx[0] + 30), int(bx[1] + 17)))
        d.text((bx[0] + 140, (bx[1] + bx[3]) / 2), f'LAST COUNTRY STANDING: {s["disp"].upper()}', font=font('k', 40),
               fill=(*NAVY, int(255 * a2)), anchor='lm')
    img.alpha_composite(ov)

# ------------------------------------------------------------------ frame
def frame(n):
    tt = n / FPS
    i, b = beat_at(tt)
    u = (tt - b['t0']) / b['dur']
    L = max(level_at(tt), 0.0)
    cam = camera(tt)
    rect = rect_of(cam)
    sunk = [s['i'] for s in S if s['t_sink'] <= tt]
    img = render_map(tt, max(L, 0.05), rect, set(sunk)).convert('RGBA')
    feat = BYNAME[b['feature']] if b.get('feature') else None
    if b.get('kind') not in ('title', 'board'):
        draw_pulses(img, rect, tt, feat)
        if b.get('labels'): draw_labels(img, rect, b['labels'], min(ease(u / 0.2), ease((1 - u) / 0.1)))
    hud_a = 0 if b.get('kind') in ('title', 'board', 'act') else 1
    # smooth hud fade around act/title cards
    hud_a = 1.0
    if b.get('kind') in ('title', 'board'): hud_a = 0.0
    if b.get('kind') == 'act': hud_a = 1 - min(ease(u / 0.15), ease((1 - u) / 0.15))
    rem = NCOUNT - len(sunk)
    draw_hud(img, tt, L, rem, hud_a)
    if b.get('kind') in (None, 'feature') and not b.get('no_next'):
        draw_next(img, L, hud_a * (0 if feat else 1))
    if feat is not None:
        ca = min(ease((tt - b['t0']) / 0.5), ease((b['t0'] + b['dur'] - tt) / 0.4))
        draw_card(img, feat, ca, b.get('card', ''))
        age = tt - feat['t_sink']
        if feat.get('survivor') and b.get('stamp') == 'safe':
            draw_stamp(img, 'STILL DRY', tt - (b['t0'] + b['dur'] * 0.55), (40, 170, 90))
        else:
            draw_stamp(img, 'SUNK!', age)
    if b.get('kind') == 'act': draw_act(img, b, u)
    if b.get('kind') == 'title': title_screen(img, u, b)
    if b.get('kind') == 'board': final_board(img, u, b)
    if b.get('kind') not in ('title', 'board') and b.get('say') and feat is None and b.get('kind') != 'act':
        draw_caption(img, b.get('cap', ''), min(ease(u / 0.1), ease((1 - u) / 0.1)))
    # global fade in/out
    if tt < 0.6 or tt > TOTAL - 1.2:
        k = min(tt / 0.6, (TOTAL - tt) / 1.2)
        img = Image.blend(Image.new('RGBA', img.size, (0, 0, 0, 255)), img, max(0, min(1, k)))
    return np.asarray(img.convert('RGB'), np.uint8).tobytes()

# ------------------------------------------------------------------ audio mix
def mix_audio(path):
    import soundfile as sf
    import audio as A
    SR = A.SR
    n = int(TOTAL * SR) + SR
    vo = np.zeros(n)
    for b in BEATS:
        if not b.get('vo'): continue
        a, sr = sf.read(b['vo'])
        if a.ndim > 1: a = a.mean(1)
        idx = np.arange(0, len(a), sr / SR)
        a = np.interp(idx, np.arange(len(a)), a)
        i0 = int((b['t0'] + b.get('vo_delay', 0.25)) * SR)
        vo[i0:i0 + len(a)] += a[:max(0, n - i0)]
    # music intensity by act
    def inten(x):
        i, b = beat_at(x)
        return b.get('music', 0.5)
    mus = A.music(TOTAL + 1, inten)[:n]
    # sidechain duck under the voice
    env = np.abs(vo)
    k = int(0.25 * SR)
    env = np.convolve(env, np.ones(k) / k, 'same')
    duck = 1 - 0.55 * np.clip(env / 0.03, 0, 1)
    sfx = np.zeros(n)
    for s in S:
        if s['t_sink'] < TOTAL:
            A.sfx_sink(n, s['t_sink'], 0.35, sfx)
    for b in BEATS:
        if b.get('kind') == 'act': A.sfx_whoosh(b['t0'] - 0.3, sfx, 1.4); A.sfx_impact(b['t0'] + 0.25, sfx)
        if b.get('feature'):
            s = BYNAME[b['feature']]
            if b.get('stamp') == 'safe': A.sfx_ding(b['t0'] + b['dur'] * 0.55, sfx, 660, 0.18)
            elif b['t0'] <= s['t_sink'] < b['t0'] + b['dur'] + 0.1: A.sfx_stamp(s['t_sink'], sfx)
        if b.get('kind') == 'title': A.sfx_impact(b['t0'] + 0.4, sfx)
        if b.get('kind') == 'board': A.sfx_riser(b['t0'] + b['dur'] * 0.78 - 3, sfx); A.sfx_impact(b['t0'] + b['dur'] * 0.78, sfx)
        if b.get('riser'): A.sfx_riser(b['t0'] + b['dur'] - 3, sfx)
    master = vo * 1.0 + mus * duck * 0.55 + sfx * 0.5
    master[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))
    peak = np.abs(master).max()
    master = np.tanh(master / peak * 1.25) * 0.92
    st = np.stack([master, master], 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == '__main__':
    if OUT.endswith('.png'):
        Image.frombytes('RGB', (W, H), frame(int(float(sys.argv[3]) * FPS))).save(OUT); sys.exit()
    if OUT.endswith('.txt'):
        with open(OUT, 'w') as f:
            for b in BEATS:
                f.write(f"{b['t0']:7.1f} {b['dur']:5.1f} L={b['l1']:7.0f} {b.get('kind') or ''} {b.get('feature') or ''} | {b.get('say', '')}\n")
            f.write(f'TOTAL {TOTAL:.1f}s  N={NCOUNT}  last={LAST["disp"]} {LAST["half"]}\n')
        sys.exit()
    if OUT.endswith('.wav'):
        mix_audio(OUT); sys.exit()
    from multiprocessing import Pool
    N = int(TOTAL * FPS)
    a0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    a1 = int(sys.argv[4]) if len(sys.argv) > 4 else N
    print(f'{N} frames {TOTAL:.1f}s; rendering {a0}-{a1}', flush=True)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'fast', '-crf', '19',
                           '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    with Pool(4) as p:
        for k, by in enumerate(p.imap(frame, range(a0, a1), chunksize=8)):
            ff.stdin.write(by)
            if k % 300 == 0: print(k, flush=True)
    ff.stdin.close(); ff.wait()
