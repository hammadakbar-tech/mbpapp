# Thumbnails (1280x720) for "Philippines vs Europe, Episode 2: War Mode".
import sys, math, os, cairo
import warballs as B
from warballs import ball
from china import ptext, rrect, INK, WHITE
from quiz import hexc
data, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
EU = ['se', 'ch', 'no', 'be', 'at', 'dk', 'fi', 'cz', 'hu', 'hr']
for c in EU + ['ph']: B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
s0 = B.FL['ph']; u = cairo.ImageSurface(cairo.FORMAT_ARGB32, s0.get_width(), s0.get_height()); c = cairo.Context(u); c.translate(0, s0.get_height()); c.scale(1, -1); c.set_source_surface(s0, 0, 0); c.paint(); B.FL['phw'] = u
W, H = 1920, 1080; GOLD = hexc('#FFC233')[:3]; RED = hexc('#E8333F')[:3]
def outlined(cr, txt, x, y, size, fill, sw=None, rot=0.0, maxw=None):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); e = cr.text_extents(txt)
    if maxw and e.width > maxw: size *= maxw / e.width; cr.set_font_size(size); e = cr.text_extents(txt)
    sw = sw or size * 0.16; x0 = -e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.05, size * 0.07); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.5); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(txt); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(sw); cr.stroke_preserve(); cr.set_source_rgb(*fill[:3]); cr.fill(); cr.restore()
def rays(cr, cx, cy, col, a, n=28):
    for j in range(n):
        th = j / n * 2 * math.pi; dw = math.pi / n * 0.5
        cr.new_path(); cr.move_to(cx, cy); cr.line_to(cx + 2600 * math.cos(th - dw), cy + 2600 * math.sin(th - dw)); cr.line_to(cx + 2600 * math.cos(th + dw), cy + 2600 * math.sin(th + dw)); cr.close_path(); cr.set_source_rgba(*col, a); cr.fill()
from PIL import Image
def save(s, n): s.write_to_png(f'{out}/{n}.f.png'); Image.open(f'{out}/{n}.f.png').convert('RGB').resize((1280, 720), Image.LANCZOS).save(f'{out}/{n}.png'); os.remove(f'{out}/{n}.f.png')
# A: war mode vs wall
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
cr.rectangle(0, 0, 820, H); cr.set_source_rgb(0.7, 0.06, 0.1); cr.fill(); cr.rectangle(820, 0, W, H); cr.set_source_rgb(0.1, 0.08, 0.28); cr.fill()
cr.save(); cr.rectangle(0, 0, 820, H); cr.clip(); rays(cr, 410, 620, (1, 0.6, 0.2), 0.18); cr.restore()
cr.new_path(); cr.move_to(760, 0); cr.line_to(900, 0); cr.line_to(800, H); cr.line_to(660, H); cr.close_path(); cr.set_source_rgb(1, 0.82, 0.2); cr.fill()
ball(cr, 'phw', 400, 640, 320, 'angry', 0, 0.7)
pos = [(1030, 330), (1225, 300), (1420, 320), (1615, 300), (1790, 345), (1090, 560), (1315, 540), (1540, 560), (1765, 565), (1430, 780)]
for c_, (x, y) in zip(EU, pos): ball(cr, c_, x, y, 110, 'shock', 0, -0.8)
outlined(cr, 'WAR MODE', 410, 190, 140, (1, 1, 1), sw=24, rot=-0.05)
outlined(cr, 'vs EUROPE', 1400, 1010, 170, GOLD, sw=30, rot=-0.04)
cr.save(); cr.translate(1420, 120); cr.rotate(0.03); rrect(cr, -250, -60, 500, 108, 26); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); outlined(cr, 'EPISODE 2', 0, 28, 72, (1, 1, 1), sw=12); cr.restore()
save(s, 'thumb-A-warmode')
# B: flip
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
g = cairo.LinearGradient(0, 0, W, H); g.add_color_stop_rgb(0, 0.15, 0.3, 0.8); g.add_color_stop_rgb(0.5, 0.45, 0.1, 0.35); g.add_color_stop_rgb(1, 0.75, 0.06, 0.1); cr.set_source(g); cr.paint(); rays(cr, 960, 560, (1, 1, 1), 0.06)
ball(cr, 'ph', 420, 560, 250, 'happy', 0, 0); ball(cr, 'phw', 1500, 560, 280, 'angry', 0, 0)
cr.save(); cr.translate(960, 560); cr.new_path(); cr.move_to(-180, -40); cr.line_to(120, -40); cr.line_to(120, -110); cr.line_to(240, 0); cr.line_to(120, 110); cr.line_to(120, 40); cr.line_to(-180, 40); cr.close_path(); cr.set_source_rgb(1, 0.82, 0.2); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(8); cr.stroke(); cr.restore()
outlined(cr, 'PEACE', 420, 200, 110, (1, 1, 1), sw=20); outlined(cr, 'WAR MODE', 1500, 200, 130, (1, 0.85, 0.3), sw=22)
outlined(cr, 'PHILIPPINES vs EUROPE 2', 960, 990, 110, (1, 1, 1), sw=20, maxw=1700)
save(s, 'thumb-B-flip')
print('ok')
