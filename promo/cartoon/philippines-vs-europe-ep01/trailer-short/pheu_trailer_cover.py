# 9:16 cover (1080x1920) for the Philippines vs Europe Ep 1 trailer Short.
import sys, math, os, cairo
import warballs as B
from warballs import ball
from china import ptext, rrect, emoji, INK, WHITE
from quiz import hexc
data, out = sys.argv[1:3]
for c in ('ph', 'es', 'it', 'fr', 'de', 'gb', 'nl', 'pt', 'pl', 'ie', 'gr'): B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
W, H = 1080, 1920; AU = hexc('#FFC233')[:3]; RED = hexc('#E8333F')[:3]
def outlined(cr, txt, x, y, size, fill, sw=None, rot=0.0):
    sw = sw or size * 0.16; cr.save(); cr.translate(x, y); cr.rotate(rot); cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); e = cr.text_extents(txt)
    if e.width > 1000: size *= 1000 / e.width; cr.set_font_size(size); e = cr.text_extents(txt)
    x0 = -e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.05, size * 0.07); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.5); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(txt); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(sw); cr.stroke_preserve(); cr.set_source_rgb(*fill); cr.fill(); cr.restore()
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.05, 0.08, 0.25); g.add_color_stop_rgb(1, 0.3, 0.08, 0.18); cr.set_source(g); cr.paint()
for j in range(30):
    a = j / 30 * 2 * math.pi; cr.new_path(); cr.move_to(540, 930); cr.line_to(540 + 2200 * math.cos(a), 930 + 2200 * math.sin(a)); cr.line_to(540 + 2200 * math.cos(a + 0.08), 980 + 2200 * math.sin(a + 0.08)); cr.close_path(); cr.set_source_rgba(1, 0.8, 0.2, 0.08); cr.fill()
opp = ['es', 'it', 'fr', 'de', 'gb', 'nl', 'pt', 'pl', 'ie', 'gr']
for j, c in enumerate(opp):
    a = -math.pi / 2 + j / len(opp) * 2 * math.pi; ball(cr, c, 540 + 400 * math.cos(a), 930 + 360 * math.sin(a), 86, 'angry', 0, -math.cos(a))
ball(cr, 'ph', 540, 930, 220, 'shock', 0, 0)
outlined(cr, 'PHILIPPINES', 540, 200, 140, hexc('#3D7BFF')[:3], sw=26, rot=-0.04)
outlined(cr, 'vs EUROPE', 540, 360, 130, AU, sw=22, rot=-0.04)
for x, y, r in ((150, 640, 0.3), (930, 620, -0.3)): outlined(cr, '?!', x, y, 130, AU, sw=22, rot=r)
for j, (lab, col) in enumerate((('W ?', (0.18, 0.75, 0.42)), ('L ?', (0.94, 0.26, 0.35)))):
    cr.save(); cr.translate(370 + j * 340, 1500); rrect(cr, -125, -85, 250, 170, 28); cr.set_source_rgb(*col); cr.fill(); ptext(cr, lab, 0, 32, 96, INK, 1, sw=0, shadow=False); cr.restore()
cr.save(); cr.translate(540, 1740); cr.rotate(-0.03); rrect(cr, -430, -78, 860, 140, 36); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); outlined(cr, 'EPISODE 1', 0, 34, 100, (1, 1, 1), sw=16); cr.restore()
s.write_to_png(out); print('ok')
