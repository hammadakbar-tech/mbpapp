# Thumbnail C (1280x720) for "Philippines vs Europe, Ep 1": curiosity scoreboard, "LOST TO SPAIN?!".
import sys, math, os, cairo
import warballs as B
from warballs import ball
from china import ptext, rrect, INK, WHITE
from quiz import hexc
data, out = sys.argv[1:3]
EU = [('es', 'SPAIN'), ('it', 'ITALY'), ('fr', 'FRANCE'), ('de', 'GERMANY'), ('gb', 'UK'), ('nl', 'NETHERLANDS'), ('pt', 'PORTUGAL')]
for c in [e[0] for e in EU] + ['ph']: B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
W, H = 1920, 1080; PH = hexc('#3D7BFF')[:3]; AU = hexc('#FFC233')[:3]; RED = hexc('#E8333F')[:3]
def outlined(cr, txt, x, y, size, fill, sw=None, rot=0.0):
    sw = sw or size * 0.16; cr.save(); cr.translate(x, y); cr.rotate(rot); cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); e = cr.text_extents(txt); x0 = -e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.05, size * 0.07); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.5); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(txt); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(sw); cr.stroke_preserve(); cr.set_source_rgb(*fill[:3]); cr.fill(); cr.restore()
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
g = cairo.LinearGradient(0, 0, W, H); g.add_color_stop_rgb(0, 0.05, 0.1, 0.3); g.add_color_stop_rgb(1, 0.3, 0.06, 0.18); cr.set_source(g); cr.paint()
for j in range(28):
    a = j / 28 * 2 * math.pi; cr.new_path(); cr.move_to(520, 560); cr.line_to(520 + 2600 * math.cos(a), 560 + 2600 * math.sin(a)); cr.line_to(520 + 2600 * math.cos(a + 0.09), 560 + 2600 * math.sin(a + 0.09)); cr.close_path(); cr.set_source_rgba(*PH, 0.1); cr.fill()
ball(cr, 'ph', 520, 600, 300, 'shock', 0, 0.4)
for x, y, r in ((170, 360, 0.3), (880, 340, -0.3)): outlined(cr, '?!', x, y, 150, AU, sw=26, rot=r)
rrect(cr, 1010, 60, 850, 960, 40); cr.set_source_rgba(0.02, 0.03, 0.08, 0.92); cr.fill_preserve(); cr.set_source_rgb(*AU); cr.set_line_width(8); cr.stroke()
outlined(cr, 'EUROPE TOUR', 1435, 150, 66, AU, sw=12)
for j, (c, nm) in enumerate(EU):
    y = 250 + j * 92; ball(cr, c, 1085, y, 34, 'angry', 0, 0); ptext(cr, 'vs ' + nm, 1140, y + 16, 48, WHITE, 1, fam='Poppins ExtraBold', sw=0, shadow=False, anchor='l')
    if j == 0: rrect(cr, 1650, y - 34, 170, 68, 34); cr.set_source_rgb(0.94, 0.26, 0.35); cr.fill(); ptext(cr, 'L', 1735, y + 18, 50, INK, 1, sw=0, shadow=False)
    else: rrect(cr, 1650, y - 34, 170, 68, 34); cr.set_source_rgba(1, 1, 1, 0.15); cr.fill(); ptext(cr, '?', 1735, y + 18, 50, WHITE, 0.8, sw=0, shadow=False)
outlined(cr, '+3 MORE', 1435, 935, 50, WHITE, sw=9)
cr.save(); cr.translate(520, 960); cr.rotate(-0.04); rrect(cr, -440, -80, 880, 140, 34); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); outlined(cr, 'LOST TO SPAIN?!', 0, 32, 96, (1, 1, 1), sw=16); cr.restore()
outlined(cr, 'PHILIPPINES vs EUROPE', 520, 130, 76, PH, sw=14, rot=-0.03)
s.write_to_png(out + '.full.png')
from PIL import Image; Image.open(out + '.full.png').convert('RGB').resize((1280, 720), Image.LANCZOS).save(out); os.remove(out + '.full.png'); print('ok')
