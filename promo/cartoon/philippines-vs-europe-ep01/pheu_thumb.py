# Thumbnail (1280x720) for "Philippines vs Europe, Episode 01": two variants for Test & compare.
import sys, math, os, cairo
import warballs as B
from warballs import ball
from china import rrect
from quiz import hexc
def outlined(cr, txt, x, y, size, fill, sw=None, rot=0.0):
    sw = sw or size * 0.16; cr.save(); cr.translate(x, y); cr.rotate(rot)
    cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); e = cr.text_extents(txt); x0 = -e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.05, size * 0.07); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.5); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(txt); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(sw); cr.stroke_preserve(); cr.set_source_rgb(*fill); cr.fill(); cr.restore()
def rays(cr, cx, cy, col, a, n=28):
    for j in range(n):
        th = j / n * 2 * math.pi; dw = math.pi / n * 0.5
        cr.new_path(); cr.move_to(cx, cy); cr.line_to(cx + 2600 * math.cos(th - dw), cy + 2600 * math.sin(th - dw)); cr.line_to(cx + 2600 * math.cos(th + dw), cy + 2600 * math.sin(th + dw)); cr.close_path(); cr.set_source_rgba(*col, a); cr.fill()
data, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
EU = ['es', 'it', 'fr', 'de', 'gb', 'nl', 'pt', 'pl', 'ie', 'gr']
for c in EU + ['ph']: B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
W, H = 1920, 1080; PH = hexc('#3D7BFF')[:3]; AU = hexc('#FFC233')[:3]; RED = hexc('#E8333F')[:3]
from PIL import Image
def save(s, n): s.write_to_png(f'{out}/{n}.full.png'); Image.open(f'{out}/{n}.full.png').convert('RGB').resize((1280, 720), Image.LANCZOS).save(f'{out}/{n}.png'); os.remove(f'{out}/{n}.full.png')
# A: 1 vs 10 split
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
cr.rectangle(0, 0, 820, H); cr.set_source_rgb(0.12, 0.35, 0.9); cr.fill(); cr.rectangle(820, 0, W, H); cr.set_source_rgb(0.1, 0.08, 0.28); cr.fill()
cr.save(); cr.rectangle(0, 0, 820, H); cr.clip(); rays(cr, 410, 620, (1, 1, 1), 0.14); cr.restore()
cr.new_path(); cr.move_to(760, 0); cr.line_to(900, 0); cr.line_to(800, H); cr.line_to(660, H); cr.close_path(); cr.set_source_rgb(1, 0.82, 0.2); cr.fill()
ball(cr, 'ph', 400, 640, 320, 'angry', 0, 0.7)
pos = [(1030, 330), (1225, 300), (1420, 320), (1615, 300), (1790, 345), (1090, 560), (1315, 540), (1540, 560), (1765, 565), (1430, 780)]
for c, (x, y) in zip(EU, pos): ball(cr, c, x, y, 110, 'angry', 0, -0.8)
outlined(cr, 'PHILIPPINES', 410, 190, 120, (1, 1, 1), sw=22, rot=-0.05)
outlined(cr, 'vs EUROPE', 1400, 1010, 170, AU, sw=30, rot=-0.04)
cr.save(); cr.translate(1420, 120); cr.rotate(0.03); rrect(cr, -250, -60, 500, 108, 26); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); outlined(cr, 'EPISODE 1', 0, 28, 72, (1, 1, 1), sw=12); cr.restore()
save(s, 'thumb-A-1vs10')
# B: map + "CAN IT WIN?"
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
g = cairo.LinearGradient(0, 0, W, H); g.add_color_stop_rgb(0, 0.05, 0.08, 0.25); g.add_color_stop_rgb(1, 0.25, 0.06, 0.2); cr.set_source(g); cr.paint(); rays(cr, 1400, 560, AU, 0.07)
for j, c in enumerate(EU):
    a = -math.pi / 2 + j / len(EU) * 2 * math.pi; ball(cr, c, 1400 + 400 * math.cos(a), 545 + 390 * math.sin(a), 95, 'angry', 0, -math.cos(a))
ball(cr, 'ph', 1400, 545, 230, 'angry', 0, -0.3)
outlined(cr, 'CAN THE', 500, 230, 110, (1, 1, 1), sw=20, rot=-0.04); outlined(cr, 'PHILIPPINES', 500, 380, 140, PH, sw=24, rot=-0.04)
outlined(cr, 'BEAT EUROPE?', 500, 560, 130, AU, sw=24, rot=-0.04)
cr.save(); cr.translate(500, 760); cr.rotate(-0.03); rrect(cr, -330, -62, 660, 112, 26); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); outlined(cr, '10 COUNTRIES', 0, 30, 80, (1, 1, 1), sw=13); cr.restore()
outlined(cr, '1 BY 1', 500, 930, 90, (1, 1, 1), sw=16)
save(s, 'thumb-B-canitwin')
print('ok')
