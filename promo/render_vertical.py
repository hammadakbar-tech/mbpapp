"""30-second motion graphic: How America Got Discovered (9:16 vertical, with narration).

Renders frames with pycairo and pipes them to ffmpeg; soundtrack is synthesised with numpy.
Usage: python3 render_vertical.py <land.geojson> <voice.wav> <out.mp4> [--preview t1,t2,...]
"""
import json, math, subprocess, sys, wave
import numpy as np
import cairo

W, H, FPS, DUR = 1080, 1920, 30, 30.0
FY = H * 0.36  # map focus sits in the upper part, text panel below
N = int(FPS * DUR)

# ---------- palette ----------
def hexc(h, a=1.0):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

BG0, BG1 = hexc('#0E2238'), hexc('#060E1A')
LAND, LAND_EDGE = hexc('#1D3B55'), hexc('#4A7FA6')
GOLD, RED, CREAM, MUTED = hexc('#F2B544'), hexc('#E8553E'), hexc('#F6F0E4'), hexc('#8FA9C2')
TEAL = hexc('#4FD1C5')

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def ease_io(t): t = clamp(t); return 4*t*t*t if t < .5 else 1 - (-2*t + 2)**3 / 2
def ease_out(t): t = clamp(t); return 1 - (1 - t)**3
def ease_back(t, s=1.7):
    t = clamp(t) - 1
    return 1 + (s + 1) * t**3 + s * t**2
def prog(t, a, b): return clamp((t - a) / (b - a))
def window(t, a, b, fin=0.5, fout=0.4):
    """Opacity envelope that fades in at a and out at b."""
    return ease_out(prog(t, a, a + fin)) * (1 - ease_io(prog(t, b - fout, b)))

# ---------- projection (Mercator, degree units) ----------
def merc(lat):
    lat = np.clip(lat, -82, 82)
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))

CAM_KEYS = [  # time, lon, lat, pixels-per-degree
    (0.0, -60, 25, 4.2), (3.2, -62, 28, 4.8),
    (4.4, -168, 62, 11.0), (6.6, -160, 60, 11.5), (8.6, -112, 14, 6.0),
    (9.8, -26, 59, 12.0), (14.0, -26, 57, 12.6),
    (15.2, -36, 30, 9.6), (19.8, -37, 29, 10.0),
    (21.0, -82, 12, 5.6), (24.2, -82, 12, 5.9),
    (25.2, -77, 36, 18.0), (27.4, -76.5, 36.5, 19.5),
    (30.0, -70, 25, 4.6),
]

def camera(t):
    for (t0, *a), (t1, *b) in zip(CAM_KEYS, CAM_KEYS[1:]):
        if t <= t1:
            k = ease_io(prog(t, t0, t1))
            # zoom interpolates geometrically so moves feel even
            z = math.exp(lerp(math.log(a[2]), math.log(b[2]), k))
            return lerp(a[0], b[0], k), lerp(a[1], b[1], k), z
    return CAM_KEYS[-1][1:]

class Proj:
    def __init__(self, t):
        self.lon, lat, self.z = camera(t)
        self.my = float(merc(lat))
    def xy(self, lon, lat):
        return (W / 2 + (np.asarray(lon) - self.lon) * self.z,
                FY - (merc(np.asarray(lat, dtype=float)) - self.my) * self.z)

# ---------- data ----------
def load_land(path):
    polys = []
    for f in json.load(open(path))['features']:
        ring = np.array(f['geometry']['coordinates'][0], dtype=float)
        lon, lat = ring[:, 0], ring[:, 1]
        cx, cy = lon.mean(), lat.mean()
        americas = -170 < cx < -30 and not (cx > -75 and cy > 58)  # exclude Greenland
        if cy < -60: continue  # Antarctica gets clipped flat by Mercator
        polys.append((lon, merc(lat), americas))
    return polys

# ---------- drawing helpers ----------
def set_font(cr, size, bold=True, display=True):
    cr.select_font_face('Inter Display' if display else 'Inter', cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(size)

def text_w(cr, s, spacing=0.0):
    return sum(cr.text_extents(ch).x_advance + spacing for ch in s) - (spacing if s else 0)

def draw_text(cr, s, x, y, color, alpha=1.0, spacing=0.0, anchor='l'):
    w = text_w(cr, s, spacing)
    if anchor == 'c': x -= w / 2
    elif anchor == 'r': x -= w
    cr.set_source_rgba(*color[:3], color[3] * alpha)
    for ch in s:
        cr.move_to(x, y); cr.show_text(ch)
        x += cr.text_extents(ch).x_advance + spacing
    return w

def wrap(cr, s, maxw):
    lines, cur = [], ''
    for word in s.split():
        trial = (cur + ' ' + word).strip()
        if text_w(cr, trial) > maxw and cur:
            lines.append(cur); cur = word
        else:
            cur = trial
    return lines + [cur]

def catmull(points, n=24):
    p = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = map(np.array, p[i - 1:i + 3])
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2*p0 - 5*p1 + 4*p2 - p3) * s*s
                              + (-p0 + 3*p1 - 3*p2 + p3) * s**3))
    out.append(np.array(p[-2]))
    return np.array(out)

class Route:
    def __init__(self, lonlat):
        ll = np.array(lonlat, dtype=float)
        self.pts = catmull(np.column_stack([ll[:, 0], merc(ll[:, 1])]))
        seg = np.hypot(*np.diff(self.pts, axis=0).T)
        self.cum = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()

    def draw(self, cr, pr, k, color, alpha=1.0, width=4, head='dot'):
        if alpha <= 0: return
        xs = W / 2 + (self.pts[:, 0] - pr.lon) * pr.z
        ys = FY - (self.pts[:, 1] - pr.my) * pr.z
        # faint full path, dashed
        cr.set_dash([6, 10]); cr.set_line_width(2)
        cr.set_source_rgba(*color[:3], 0.25 * alpha)
        cr.move_to(xs[0], ys[0])
        for x, y in zip(xs[1:], ys[1:]): cr.line_to(x, y)
        cr.stroke(); cr.set_dash([])
        if k <= 0: return
        n = min(int(np.searchsorted(self.cum, k)), len(self.cum) - 1)
        f = 0 if n == 0 else (k - self.cum[n - 1]) / max(1e-9, self.cum[n] - self.cum[n - 1])
        hx = lerp(xs[max(n - 1, 0)], xs[n], f); hy = lerp(ys[max(n - 1, 0)], ys[n], f)
        cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
        for lw, a in ((width * 5, 0.10), (width * 2.4, 0.22), (width, 1.0)):
            cr.set_line_width(lw); cr.set_source_rgba(*color[:3], a * alpha)
            cr.move_to(xs[0], ys[0])
            for x, y in zip(xs[1:n], ys[1:n]): cr.line_to(x, y)
            cr.line_to(hx, hy); cr.stroke()
        if k < 1:
            ang = math.atan2(ys[n] - ys[max(n - 1, 0)], xs[n] - xs[max(n - 1, 0)])
            if head == 'ship': draw_ship(cr, hx, hy, ang, color, alpha)
            else: glow_dot(cr, hx, hy, 9, color, alpha)

def glow_dot(cr, x, y, r, color, alpha=1.0):
    cr.new_path()
    g = cairo.RadialGradient(x, y, 0, x, y, r * 4)
    g.add_color_stop_rgba(0, *color[:3], 0.55 * alpha); g.add_color_stop_rgba(1, *color[:3], 0)
    cr.set_source(g); cr.arc(x, y, r * 4, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgba(*CREAM[:3], alpha); cr.arc(x, y, r * 0.55, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgba(*color[:3], alpha); cr.set_line_width(2.5); cr.arc(x, y, r, 0, 2 * math.pi); cr.stroke()

def draw_ship(cr, x, y, ang, color, alpha):
    glow_dot(cr, x, y, 6, color, alpha * 0.6)
    cr.save(); cr.translate(x, y - 6); s = 1.4; cr.scale(s, s)
    flip = -1 if math.cos(ang) < 0 else 1
    cr.scale(flip, 1)
    cr.set_source_rgba(*CREAM[:3], alpha)
    cr.move_to(-16, 0); cr.line_to(16, 0); cr.line_to(10, 8); cr.line_to(-11, 8); cr.close_path(); cr.fill()
    cr.move_to(0, -2); cr.line_to(0, -26); cr.set_line_width(2); cr.stroke()
    cr.set_source_rgba(*color[:3], alpha)
    cr.move_to(2, -25); cr.curve_to(14, -20, 14, -8, 2, -4); cr.close_path(); cr.fill()
    cr.move_to(-2, -22); cr.curve_to(-11, -17, -11, -9, -2, -6); cr.close_path(); cr.fill()
    cr.restore()

def pin(cr, pr, lon, lat, label, t, t0, color=GOLD, alpha=1.0, side='r', size=32):
    k = prog(t, t0, t0 + 0.45)
    if k <= 0 or alpha <= 0: return
    x, y = pr.xy(lon, lat)
    s = ease_back(k)
    ring = prog(t, t0, t0 + 1.2)
    cr.new_path()
    cr.set_source_rgba(*color[:3], (1 - ring) * 0.8 * alpha); cr.set_line_width(2)
    cr.arc(x, y, 8 + 34 * ease_out(ring), 0, 2 * math.pi); cr.stroke()
    glow_dot(cr, x, y, 8 * s, color, alpha)
    if label:
        set_font(cr, size, bold=True)
        lk = ease_out(prog(t, t0 + 0.15, t0 + 0.6))
        if side == 'b':
            draw_text(cr, label, x, y + 30 + size + (1 - lk) * 12, CREAM, alpha * lk, spacing=1, anchor='c')
            return
        dx = 22 if side == 'r' else -22
        draw_text(cr, label, x + dx + (1 - lk) * 12 * (1 if side == 'r' else -1), y + size * 0.35,
                  CREAM, alpha * lk, spacing=1, anchor='l' if side == 'r' else 'r')

def star(cr, x, y, r, color, alpha):
    cr.new_path(); cr.set_source_rgba(*color[:3], alpha)
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        (cr.move_to if i == 0 else cr.line_to)(x + rr * math.cos(a), y + rr * math.sin(a))
    cr.close_path(); cr.fill()

# ---------- story ----------
SCENES = [  # start, end, eyebrow (year), title, body
    (3.6, 9.1, '15,000+ YEARS AGO', 'The First Americans',
     'Hunters cross the Bering land bridge from Asia and spread across two continents.'),
    (9.4, 14.7, 'c. 1000 AD', 'The Vikings Arrive',
     "Leif Erikson sails from Greenland and lands in 'Vinland', today's Newfoundland."),
    (14.9, 20.4, None, 'Columbus Crosses the Atlantic',
     'Sailing for Spain, he reaches the Caribbean, sure he has found Asia.'),
    (20.6, 24.8, '1507', 'A New World Gets a Name',
     "A German mapmaker labels it 'America', after explorer Amerigo Vespucci."),
    (25.0, 27.9, None, 'From Colony to Country',
     'English settlers found Jamestown. 169 years later, 13 colonies declare independence.'),
]
TIMELINE = ['15,000 yrs ago', '1000', '1492', '1507', '1776']

R_BERING = Route([(-200, 62), (-186, 65.5), (-170, 66), (-156, 64.5), (-142, 61), (-128, 56)])
R_SOUTH = Route([(-128, 56), (-121, 44), (-110, 30), (-97, 18), (-83, 8), (-77, -6), (-72, -25), (-71, -45)])
R_EAST = Route([(-128, 56), (-112, 50), (-96, 43), (-82, 38)])
R_NORSE = Route([(6, 61), (-8, 63), (-21, 64.1), (-34, 63), (-46, 60.8), (-54, 56.5), (-55.5, 51.6)])
R_COLUMBUS = Route([(-6.9, 37.2), (-15.5, 28.1), (-34, 25.5), (-54, 24.6), (-74.5, 24.1)])
COLONIES = [(-81.1, 32.08), (-79.93, 32.78), (-78.64, 35.78), (-77.43, 37.54), (-76.49, 38.98),
            (-75.52, 39.16), (-75.16, 39.95), (-74.76, 40.22), (-73.8, 42.65), (-72.7, 41.76),
            (-71.4, 41.8), (-71.06, 42.36), (-71.5, 43.2)]

def year_for(i, t):
    if i == 2:   # roll the counter from 1000 up to 1492
        return str(int(round(lerp(1000, 1492, ease_out(prog(t, 15.0, 16.0))))))
    if i == 4:
        return str(int(round(lerp(1607, 1776, ease_io(prog(t, 26.0, 26.7))))))
    return SCENES[i][2]

# ---------- frame ----------
def draw_background(cr, pr):
    g = cairo.RadialGradient(W * 0.5, FY, 100, W * 0.5, FY, H * 0.7)
    g.add_color_stop_rgba(0, *BG0); g.add_color_stop_rgba(1, *BG1)
    cr.set_source(g); cr.paint()
    # graticule
    cr.set_line_width(1); cr.set_source_rgba(*MUTED[:3], 0.08)
    for lon in range(-540, 541, 15):
        x = W / 2 + (lon - pr.lon) * pr.z
        if -5 < x < W + 5: cr.move_to(x, 0); cr.line_to(x, H)
    for lat in range(-75, 76, 15):
        _, y = pr.xy(0, lat)
        if -5 < y < H + 5: cr.move_to(0, y); cr.line_to(W, y)
    cr.stroke()

def draw_land(cr, pr, polys, gold_k):
    for off in (-360, 0, 360):
        for lon, my, amer in polys:
            xs = W / 2 + (lon + off - pr.lon) * pr.z
            ys = FY - (my - pr.my) * pr.z
            if xs.max() < -50 or xs.min() > W + 50 or ys.max() < -50 or ys.min() > H + 50: continue
            cr.move_to(xs[0], ys[0])
            for x, y in zip(xs[1:], ys[1:]): cr.line_to(x, y)
            cr.close_path()
            k = gold_k if amer else 0
            fill = [lerp(a, b, k * 0.55) for a, b in zip(LAND[:3], GOLD[:3])]
            cr.set_source_rgba(*fill, 1); cr.fill_preserve()
            edge = [lerp(a, b, k) for a, b in zip(LAND_EDGE[:3], GOLD[:3])]
            cr.set_source_rgba(*edge, 0.9); cr.set_line_width(1.6); cr.stroke()

def draw_panel(cr, t):
    for i, (a, b, _, title, body) in enumerate(SCENES):
        al = window(t, a, b)
        if al <= 0: continue
        x0, y0 = 80, 1430
        rise = (1 - ease_out(prog(t, a, a + 0.7))) * 40
        # backing gradient for legibility
        g = cairo.LinearGradient(0, 1080, 0, H)
        g.add_color_stop_rgba(0, *BG1[:3], 0); g.add_color_stop_rgba(0.45, *BG1[:3], 0.82 * al)
        g.add_color_stop_rgba(1, *BG1[:3], 0.92 * al)
        cr.set_source(g); cr.rectangle(0, 1080, W, H - 1080); cr.fill()
        # accent bar grows
        bk = ease_out(prog(t, a + 0.05, a + 0.6))
        cr.set_source_rgba(*GOLD[:3], al); cr.rectangle(x0, y0 - 104 + rise, 10, 300 * bk); cr.fill()
        yr = year_for(i, t); set_font(cr, 96, bold=True)
        if text_w(cr, yr, 2) > 900: set_font(cr, 96 * 900 / text_w(cr, yr, 2), bold=True)
        draw_text(cr, yr, x0 + 40, y0 - 20 + rise, GOLD, al, spacing=2)
        set_font(cr, 60, bold=True)
        tk = ease_out(prog(t, a + 0.15, a + 0.8))
        draw_text(cr, title if text_w(cr, title) < 900 else title, x0 + 40, y0 + 62 + rise + (1 - tk) * 30, CREAM, al * tk)
        set_font(cr, 38, bold=False, display=False)
        bkk = ease_out(prog(t, a + 0.35, a + 1.0))
        for j, line in enumerate(wrap(cr, body, 880)):
            draw_text(cr, line, x0 + 40, y0 + 132 + j * 52 + rise + (1 - bkk) * 30, MUTED, al * bkk)

def draw_timeline(cr, t):
    al = window(t, 3.4, 28.0, 0.6, 0.5)
    if al <= 0: return
    active = max([i for i, s in enumerate(SCENES) if t >= s[0] - 0.2] or [0])
    x0, x1, y = 150, 930, 1790
    xs = [lerp(x0, x1, i / (len(TIMELINE) - 1)) for i in range(len(TIMELINE))]
    cr.set_line_width(2); cr.set_source_rgba(*MUTED[:3], 0.35 * al)
    cr.move_to(x0, y); cr.line_to(x1, y); cr.stroke()
    # progress fill moves smoothly between nodes
    a, b = SCENES[active][0], SCENES[active][1]
    px = lerp(xs[active], xs[min(active + 1, len(xs) - 1)], 0) if active == len(xs) - 1 else xs[active]
    prev = xs[max(active - 1, 0)]
    px = lerp(prev, px, ease_io(prog(t, a - 0.2, a + 0.4)))
    cr.set_source_rgba(*GOLD[:3], al); cr.set_line_width(3)
    cr.move_to(x0, y); cr.line_to(px, y); cr.stroke()
    set_font(cr, 24, bold=True, display=False)
    for i, (x, lab) in enumerate(zip(xs, TIMELINE)):
        on = i <= active
        cr.set_source_rgba(*(GOLD if on else MUTED)[:3], al * (1 if on else 0.5))
        r = 9 if i == active else 6
        cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.fill()
        draw_text(cr, lab, x, y - 26, CREAM if i == active else MUTED, al * (1 if i == active else 0.6), anchor='c')

def draw_title(cr, t):
    al = window(t, 0.2, 3.5, 0.3, 0.6)
    if al <= 0: return
    cr.set_source_rgba(*BG1[:3], 0.55 * al); cr.paint()
    set_font(cr, 34, bold=True)
    k = ease_out(prog(t, 0.2, 0.9))
    draw_text(cr, 'THE STORY OF HOW', W / 2, 700 + (1 - k) * 20, GOLD, al * k, spacing=10, anchor='c')
    set_font(cr, 150, bold=True)
    for li, line in enumerate(['AMERICA', 'WAS', 'DISCOVERED']):
        w = text_w(cr, line, 4); x = W / 2 - w / 2
        for ci, ch in enumerate(line):
            ck = prog(t, 0.45 + li * 0.25 + ci * 0.035, 0.95 + li * 0.25 + ci * 0.035)
            dy = (1 - ease_back(ck)) * 80
            cr.set_source_rgba(*CREAM[:3], al * clamp(ck * 2))
            cr.move_to(x, 880 + li * 160 + dy); cr.show_text(ch)
            x += cr.text_extents(ch).x_advance + 4
    lk = ease_io(prog(t, 1.5, 2.3))
    cr.set_source_rgba(*GOLD[:3], al); cr.rectangle(W / 2 - 220 * lk, 1260, 440 * lk, 8); cr.fill()
    set_font(cr, 38, bold=False, display=False)
    k2 = ease_out(prog(t, 1.9, 2.5))
    draw_text(cr, '...and why it is more than one name', W / 2, 1340 + (1 - k2) * 16, MUTED, al * k2, anchor='c')

def draw_outro(cr, t):
    al = ease_out(prog(t, 27.9, 28.5))
    if al <= 0: return
    cr.set_source_rgba(*BG1[:3], 0.62 * al); cr.paint()
    set_font(cr, 96, bold=True)
    k = ease_out(prog(t, 28.0, 28.6))
    draw_text(cr, 'Not discovered', W / 2, 820 + (1 - k) * 30, CREAM, al * k, anchor='c')
    draw_text(cr, 'once.', W / 2, 930 + (1 - k) * 30, CREAM, al * k, anchor='c')
    k2 = ease_out(prog(t, 28.4, 29.0))
    draw_text(cr, 'Again and', W / 2, 1080 + (1 - k2) * 30, GOLD, k2, anchor='c')
    draw_text(cr, 'again.', W / 2, 1190 + (1 - k2) * 30, GOLD, k2, anchor='c')
    k3 = ease_out(prog(t, 28.9, 29.4))
    set_font(cr, 40, bold=False, display=False)
    draw_text(cr, 'Its first peoples were here all along.', W / 2, 1300, MUTED, k3, anchor='c')

def draw_america_stamp(cr, pr, t):
    al = window(t, 21.3, 24.8, 0.25, 0.5)
    if al <= 0: return
    x, y = pr.xy(-84, 20)
    k = prog(t, 21.3, 21.65)
    s = lerp(1.6, 1.0, ease_out(k))
    cr.save(); cr.translate(x, y); cr.rotate(-0.06); cr.scale(s, s)
    set_font(cr, 104, bold=True)
    w = text_w(cr, 'AMERICA', 14)
    cr.set_source_rgba(*BG1[:3], 0.5 * al); cr.rectangle(-w / 2 - 40, -125, w + 80, 165); cr.fill()
    cr.set_source_rgba(*GOLD[:3], al); cr.set_line_width(5); cr.rectangle(-w / 2 - 40, -125, w + 80, 165); cr.stroke()
    draw_text(cr, 'AMERICA', 0, 0, GOLD, al, spacing=14, anchor='c')
    cr.restore()
    flash = 1 - prog(t, 21.6, 22.1)
    if 0 < flash < 1:
        cr.set_source_rgba(*GOLD[:3], 0.25 * flash); cr.paint()

def render_frame(cr, t, polys):
    pr = Proj(t)
    draw_background(cr, pr)
    draw_land(cr, pr, polys, ease_io(prog(t, 21.3, 22.0)) * (1 - ease_io(prog(t, 24.3, 25.2))))

    # Scene 1: Beringia
    a1 = window(t, 4.0, 9.4, 0.4, 0.6)
    R_BERING.draw(cr, pr, ease_io(prog(t, 4.6, 6.7)), TEAL, a1)
    R_SOUTH.draw(cr, pr, ease_io(prog(t, 6.8, 8.7)), TEAL, a1)
    R_EAST.draw(cr, pr, ease_io(prog(t, 7.0, 8.5)), TEAL, a1)
    pin(cr, pr, -200, 62, 'SIBERIA', t, 4.4, TEAL, a1, side='b')
    pin(cr, pr, -168, 65.8, 'BERING LAND BRIDGE', t, 5.6, TEAL, a1)

    # Scene 2: Norse
    a2 = window(t, 9.6, 14.9, 0.4, 0.5)
    R_NORSE.draw(cr, pr, ease_io(prog(t, 10.2, 13.2)), RED, a2, head='ship')
    pin(cr, pr, 6, 61, 'NORWAY', t, 10.0, RED, a2, side='b')
    pin(cr, pr, -21, 64.1, 'ICELAND', t, 10.9, RED, a2)
    pin(cr, pr, -46, 60.8, 'GREENLAND', t, 11.8, RED, a2)
    pin(cr, pr, -55.5, 51.6, 'VINLAND', t, 13.1, GOLD, a2)

    # Scene 3: Columbus
    a3 = window(t, 15.0, 20.6, 0.4, 0.5)
    R_COLUMBUS.draw(cr, pr, ease_io(prog(t, 15.6, 19.0)), GOLD, a3, head='ship')
    pin(cr, pr, -6.9, 37.2, 'SPAIN', t, 15.3, GOLD, a3)
    pin(cr, pr, -15.5, 28.1, 'CANARY ISLANDS', t, 16.1, GOLD, a3)
    pin(cr, pr, -74.5, 24.1, 'SAN SALVADOR', t, 19.0, RED, a3, side='b')

    draw_america_stamp(cr, pr, t)

    # Scene 5: Jamestown & 13 colonies
    a5 = window(t, 25.0, 28.6, 0.3, 0.6)
    pin(cr, pr, -76.78, 37.21, 'JAMESTOWN 1607', t, 25.4, GOLD, a5, side='l', size=30)
    for i, (lon, lat) in enumerate(COLONIES):
        k = prog(t, 26.1 + i * 0.07, 26.4 + i * 0.07)
        if k > 0:
            x, y = pr.xy(lon, lat)
            star(cr, x, y, 14 * ease_back(k), CREAM, a5)
    if a5 > 0:
        set_font(cr, 32, bold=True)
        x, y = pr.xy(-71, 40.2)
        k = ease_out(prog(t, 26.9, 27.3))
        draw_text(cr, '13 COLONIES', x + 20, y, CREAM, a5 * k, spacing=2)

    draw_panel(cr, t)
    draw_timeline(cr, t)
    draw_title(cr, t)
    draw_outro(cr, t)

    # end fade
    f = prog(t, 29.5, 30.0)
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- audio ----------
def make_audio(path, voice_path, sr=48000):
    n = int(sr * DUR); tt = np.arange(n) / sr
    out = np.zeros(n)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    chords = [[57, 64, 69, 72], [53, 60, 65, 69], [48, 55, 64, 67], [55, 62, 67, 71]]  # Am F C G
    seg = 3.75
    for ci in range(int(DUR / seg)):
        ch = chords[ci % 4]; t0 = ci * seg
        i0, i1 = int(t0 * sr), min(n, int((t0 + seg + 1.0) * sr))
        lt = tt[i0:i1] - t0
        env = np.minimum(1, lt / 0.6) * np.exp(-np.maximum(0, lt - seg) * 3)
        for m in ch:
            f = note(m)
            out[i0:i1] += env * 0.05 * (np.sin(2*np.pi*f*lt) + 0.5*np.sin(2*np.pi*f*1.003*lt)
                                        + 0.25*np.sin(2*np.pi*2*f*lt))
        out[i0:i1] += env * 0.09 * np.sin(2 * np.pi * note(ch[0] - 12) * lt)
    # pulse (soft kick) on every beat from 3.4s, 128 bpm-ish
    beat = 60 / 120
    for bt in np.arange(3.4, 28.0, beat):
        i0 = int(bt * sr); L = int(0.35 * sr); lt = np.arange(L) / sr
        f = 50 + 70 * np.exp(-lt * 30)
        out[i0:i0 + L] += 0.32 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-lt * 9)
    # hi-hat ticks off-beat
    rng = np.random.default_rng(1)
    for bt in np.arange(3.4 + beat / 2, 28.0, beat):
        i0 = int(bt * sr); L = int(0.06 * sr)
        nz = np.diff(rng.standard_normal(L + 1))
        out[i0:i0 + L] += 0.03 * nz * np.exp(-np.arange(L) / sr * 60)
    # whooshes on transitions
    for wt in [3.3, 9.3, 14.8, 20.5, 24.9, 27.8]:
        L = int(1.0 * sr); i0 = int((wt - 0.5) * sr)
        nz = rng.standard_normal(L); lt = np.arange(L) / L
        y = np.zeros(L); a = 0.0
        for j in range(L):  # sweeping one-pole lowpass
            c = 0.02 + 0.25 * math.sin(math.pi * lt[j])
            a += c * (nz[j] - a); y[j] = a
        out[i0:i0 + L] += 0.35 * y * np.sin(np.pi * lt) ** 2
    # impacts: title & AMERICA stamp
    for it in [0.5, 21.35, 28.0]:
        i0 = int(it * sr); L = int(1.5 * sr); lt = np.arange(L) / sr
        f = 40 + 90 * np.exp(-lt * 12)
        out[i0:i0 + L] += 0.5 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-lt * 3)
        out[i0:i0 + L] += 0.08 * rng.standard_normal(L) * np.exp(-lt * 18)
    out *= np.minimum(1, tt / 0.3) * np.minimum(1, (DUR - tt) / 1.2)
    with wave.open(voice_path) as w:
        assert w.getframerate() == sr
        v = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float) / 32767
    v = np.pad(v, (0, max(0, n - len(v))))[:n]
    # sidechain: music dips to 35% under the voice
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = 1 - 0.65 * np.clip(env / 0.03, 0, 1)
    duck = np.convolve(duck, np.ones(9600) / 9600, mode='same')
    music = np.tanh(out * 1.2) * 0.55 * duck
    mix = music + 0.95 * v
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    st = np.column_stack([mix * 0.98 + 0.0 * np.roll(music, 240), mix])
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype('<i2').tobytes())

def main():
    land_path, voice_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    polys = load_land(land_path)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    if len(sys.argv) > 4 and sys.argv[4] == '--preview':
        for ts in sys.argv[5].split(','):
            render_frame(cr, float(ts), polys); surf.write_to_png(f'{out}_{ts}.png')
        return
    wav = out.rsplit('.', 1)[0] + '.wav'
    make_audio(wav, voice_path)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                          stdin=subprocess.PIPE)
    for i in range(N):
        render_frame(cr, i / FPS, polys); surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait()

if __name__ == '__main__':
    main()
