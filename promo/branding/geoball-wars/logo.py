# GeoBall Wars channel branding: logo (1024 sq, circle-safe), icon (no text) and banner (2560x1440).
# Usage: python3 logo.py <data_dir> <out_dir>
import json, math, os, sys
import numpy as np, cairo
import warballs as B
from warballs import ball
from big import ortho
from canada import rings
from china import ptext, rrect, tw, emoji, GOLD, WHITE, INK, CRIMSON
from quiz import hexc
data, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
GOLD3, RED3, NAVY = hexc('#FFC233')[:3], hexc('#E8333F')[:3], (0.04, 0.06, 0.18)

def earth_surface(lon0=125.0, lat0=-5.0, S=1000):
    """An orthographic Earth texture (oceans + land) used as the 'flag' of the GeoBall."""
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); cr = cairo.Context(s); R = S / 2
    g = cairo.RadialGradient(R * 0.8, R * 0.7, R * 0.1, R, R, R * 1.05); g.add_color_stop_rgb(0, 0.25, 0.62, 0.98); g.add_color_stop_rgb(1, 0.05, 0.28, 0.65); cr.set_source(g); cr.paint()
    feats = json.load(open(os.path.join(data, 'countries_50m.geojson')))['features']
    for f in feats:
        for r in rings(f['geometry']):
            x, y, cc = ortho(r[:, 0], r[:, 1], lon0, lat0)
            if (cc > 0).mean() < 0.35: continue
            cr.new_path(); cr.move_to(R + x[0] * R, R + y[0] * R)
            for xx, yy in zip(x[1:], y[1:]): cr.line_to(R + xx * R, R + yy * R)
            cr.close_path(); cr.set_source_rgb(0.3, 0.78, 0.38); cr.fill_preserve(); cr.set_source_rgb(0.12, 0.45, 0.2); cr.set_line_width(4); cr.stroke()
    for la in (-30, 0, 30):  # faint latitude lines for a 'globe' feel
        pts = [ortho(np.array([lo]), np.array([la]), lon0, lat0) for lo in range(-180, 181, 4)]
        cr.new_path(); first = True
        for x, y, cc in pts:
            if cc[0] > 0:
                (cr.move_to if first else cr.line_to)(R + x[0] * R, R + y[0] * R); first = False
            else: first = True
        cr.set_source_rgba(1, 1, 1, 0.18); cr.set_line_width(3); cr.stroke()
    return s
B.FL['earth'] = earth_surface()
for c in ('au', 'us', 'ph', 'jp', 'gb', 'ca', 'fr', 'gr', 'in', 'id', 'br', 'de'):
    p = os.path.join(data, 'flags', c + '.png')
    if os.path.exists(p): B.FL[c] = cairo.ImageSurface.create_from_png(p)

def sword(cr, x0, y0, x1, y1, w=34):
    a = math.atan2(y1 - y0, x1 - x0); L = math.hypot(x1 - x0, y1 - y0)
    cr.save(); cr.translate(x0, y0); cr.rotate(a)
    cr.new_path(); cr.move_to(0, -w / 2); cr.line_to(L * 0.8, -w / 2); cr.line_to(L, 0); cr.line_to(L * 0.8, w / 2); cr.line_to(0, w / 2); cr.close_path()
    g = cairo.LinearGradient(0, -w / 2, 0, w / 2); g.add_color_stop_rgb(0, 0.97, 0.98, 1); g.add_color_stop_rgb(0.5, 0.75, 0.8, 0.88); g.add_color_stop_rgb(1, 0.55, 0.6, 0.7); cr.set_source(g); cr.fill_preserve()
    cr.set_source_rgb(*INK[:3]); cr.set_line_width(7); cr.stroke()
    cr.move_to(20, 0); cr.line_to(L * 0.78, 0); cr.set_source_rgba(1, 1, 1, 0.6); cr.set_line_width(4); cr.stroke()
    rrect(cr, -26, -w * 1.9, 30, w * 3.8, 12); cr.set_source_rgb(*GOLD3); cr.fill_preserve(); cr.set_source_rgb(*INK[:3]); cr.set_line_width(7); cr.stroke()  # crossguard
    rrect(cr, -150, -w * 0.42, 126, w * 0.84, 10); cr.set_source_rgb(0.45, 0.22, 0.12); cr.fill_preserve(); cr.set_source_rgb(*INK[:3]); cr.stroke()  # grip
    cr.new_path(); cr.arc(-165, 0, w * 0.75, 0, 2 * math.pi); cr.set_source_rgb(*GOLD3); cr.fill_preserve(); cr.set_source_rgb(*INK[:3]); cr.stroke()  # pommel
    cr.restore()
def starburst(cr, cx, cy, n, r0, r1, col, a):
    for j in range(n):
        th = j / n * 2 * math.pi; dw = math.pi / n * 0.55
        cr.new_path(); cr.move_to(cx + r0 * math.cos(th), cy + r0 * math.sin(th)); cr.line_to(cx + r1 * math.cos(th - dw), cy + r1 * math.sin(th - dw)); cr.line_to(cx + r1 * math.cos(th + dw), cy + r1 * math.sin(th + dw)); cr.close_path()
        cr.set_source_rgba(*col, a); cr.fill()
def outlined(cr, txt, x, y, size, fill, stroke=INK, sw=None, fam='Poppins ExtraBold'):
    sw = sw or size * 0.16
    cr.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL); cr.set_font_size(size)
    e = cr.text_extents(txt); x0 = x - e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.04, y + size * 0.06); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.45); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, y); cr.text_path(txt); cr.set_source_rgb(*stroke[:3]); cr.set_line_width(sw); cr.stroke_preserve()
    g = cairo.LinearGradient(0, y - size * 0.8, 0, y); g.add_color_stop_rgb(0, *[min(1, c * 1.15 + 0.1) for c in fill]); g.add_color_stop_rgb(1, *fill); cr.set_source(g); cr.fill()
def badge(cr, S, with_text=True):
    c = S / 2; k = S / 1024
    g = cairo.RadialGradient(c, c * 0.85, 40 * k, c, c, c); g.add_color_stop_rgb(0, 0.16, 0.2, 0.45); g.add_color_stop_rgb(1, *NAVY); cr.set_source(g); cr.paint()
    cy = (430 if with_text else 512) * k
    starburst(cr, c, cy, 24, 120 * k, 620 * k, GOLD3, 0.12)
    cr.new_path(); cr.arc(c, c, c - 10 * k, 0, 2 * math.pi); cr.set_source_rgb(*GOLD3); cr.set_line_width(16 * k); cr.stroke()
    cr.new_path(); cr.arc(c, c, c - 30 * k, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25); cr.set_line_width(4 * k); cr.stroke()
    sl = 0.82 if with_text else 0.9
    sword(cr, c - 330 * k * sl, cy + 300 * k * sl, c + 300 * k * sl, cy - 330 * k * sl, 36 * k); sword(cr, c + 330 * k * sl, cy + 300 * k * sl, c - 300 * k * sl, cy - 330 * k * sl, 36 * k)
    r = (255 if with_text else 300) * k
    cr.new_path(); cr.arc(c, cy + 18 * k, r * 1.02, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
    ball(cr, 'earth', c, cy, r, 'angry', 0, 0)
    if with_text:
        outlined(cr, 'GEOBALL', c, 812 * k, 158 * k, GOLD3, sw=30 * k)
        cr.save(); cr.translate(c, 900 * k); cr.rotate(-0.03); bw = 430 * k
        cr.new_path(); cr.move_to(-bw / 2 - 40 * k, -50 * k); cr.line_to(bw / 2 + 40 * k, -50 * k); cr.line_to(bw / 2 + 10 * k, 0); cr.line_to(bw / 2 + 40 * k, 50 * k); cr.line_to(-bw / 2 - 40 * k, 50 * k); cr.line_to(-bw / 2 - 10 * k, 0); cr.close_path()
        cr.set_source_rgb(*RED3); cr.fill_preserve(); cr.set_source_rgb(*INK[:3]); cr.set_line_width(9 * k); cr.stroke()
        outlined(cr, 'WARS', 0, 38 * k, 104 * k, (1, 1, 1), sw=18 * k); cr.restore()

for name, S, txt in (('geoball-wars-logo.png', 1024, True), ('geoball-wars-icon.png', 1024, False)):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST); badge(cr, S, txt); s.write_to_png(os.path.join(out, name))
# YouTube profile-picture preview (circle crop at small size)
from PIL import Image, ImageDraw
lg = Image.open(os.path.join(out, 'geoball-wars-logo.png')).convert('RGBA')
prev = Image.new('RGBA', (900, 340), (24, 24, 24, 255)); d = ImageDraw.Draw(prev)
for size, x in ((240, 30), (120, 320), (64, 480), (40, 590), (24, 680)):
    im = lg.resize((size, size), Image.LANCZOS); m = Image.new('L', (size, size), 0); ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255); prev.paste(im, (x, 170 - size // 2), m)
prev.save(os.path.join(out, 'preview-circle-sizes.png'))

# Banner 2560x1440 (safe area: centre 1546x423)
W, H = 2560, 1440
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
g = cairo.LinearGradient(0, 0, W, H); g.add_color_stop_rgb(0, 0.05, 0.07, 0.22); g.add_color_stop_rgb(0.5, 0.12, 0.08, 0.3); g.add_color_stop_rgb(1, 0.3, 0.07, 0.18); cr.set_source(g); cr.paint()
rng = np.random.default_rng(4)
for _ in range(260): x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1, 3.5); cr.new_path(); cr.arc(x, y, r, 0, 6.283); cr.set_source_rgba(1, 1, 1, rng.uniform(0.2, 0.7)); cr.fill()
starburst(cr, 1280, 720, 32, 100, 1500, GOLD3, 0.05)
deco = [c for c in ('us', 'ph', 'jp', 'gb', 'ca', 'fr', 'gr', 'in', 'id', 'br', 'de') if c in B.FL]
for j, c in enumerate(deco):  # balls bordering the safe area (visible on TV/desktop, cropped on phones)
    a = j / len(deco) * 2 * math.pi; x = 1280 + 1050 * math.cos(a); y = 720 + 520 * math.sin(a)
    ball(cr, c, x, y, 110, 'angry', 0, -math.cos(a))
rrect(cr, 507, 509, 1546, 423, 40); cr.set_source_rgba(0.02, 0.03, 0.1, 0.55); cr.fill()
icon = cairo.ImageSurface.create_from_png(os.path.join(out, 'geoball-wars-icon.png'))
cr.save(); cr.translate(560, 532); cr.scale(377 / 1024, 377 / 1024); cr.set_source_surface(icon, 0, 0); cr.new_path(); cr.arc(512, 512, 512, 0, 6.283); cr.clip(); cr.paint(); cr.restore()
outlined(cr, 'GEOBALL WARS', 1460, 700, 150, GOLD3, sw=26)
cr.select_font_face('Poppins ExtraBold'); outlined(cr, 'COUNTRIES BATTLE. YOU PICK THE WINNER.', 1460, 800, 46, (1, 1, 1), sw=10)
for j, c in enumerate(('au', 'us', 'ph', 'jp', 'gb', 'ca')):
    if c in B.FL: ball(cr, c, 1105 + j * 140, 875, 44, 'angry', 0, 0)
s.write_to_png(os.path.join(out, 'geoball-wars-banner.png'))
print('done')
