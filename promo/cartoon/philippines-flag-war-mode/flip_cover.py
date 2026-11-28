# 9:16 cover for "The Only Flag That Flips for War".
import sys, math, os, cairo
import warballs as B
from warballs import ball
from china import ptext, rrect, emoji
from quiz import hexc
data, out = sys.argv[1:3]
B.FL['ph'] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', 'ph.png'))
s0 = B.FL['ph']; u = cairo.ImageSurface(cairo.FORMAT_ARGB32, s0.get_width(), s0.get_height()); c = cairo.Context(u); c.translate(0, s0.get_height()); c.scale(1, -1); c.set_source_surface(s0, 0, 0); c.paint(); B.FL['phw'] = u
W, H = 1080, 1920; RED = hexc('#E8333F')[:3]; BLUE = hexc('#3D7BFF')[:3]; GOLD = hexc('#FFC233')[:3]
def outlined(cr, txt, x, y, size, fill, sw=None, rot=0.0, maxw=1000):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); e = cr.text_extents(txt)
    if e.width > maxw: size *= maxw / e.width; cr.set_font_size(size); e = cr.text_extents(txt)
    sw = sw or size * 0.16; x0 = -e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.05, size * 0.07); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.5); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(txt); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(sw); cr.stroke_preserve(); cr.set_source_rgb(*fill); cr.fill(); cr.restore()
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
cr.rectangle(0, 0, W, 960); cr.set_source_rgb(0.15, 0.35, 0.85); cr.fill(); cr.rectangle(0, 960, W, 960); cr.set_source_rgb(0.75, 0.08, 0.12); cr.fill()
for half, cy in ((0, 600), (1, 1350)):
    cr.save(); cr.rectangle(0, half * 960, W, 960); cr.clip()
    for j in range(26):
        a = j / 26 * 2 * math.pi; cr.new_path(); cr.move_to(540, cy); cr.line_to(540 + 2000 * math.cos(a), cy + 2000 * math.sin(a)); cr.line_to(540 + 2000 * math.cos(a + 0.1), cy + 2000 * math.sin(a + 0.1)); cr.close_path(); cr.set_source_rgba(1, 1, 1, 0.1); cr.fill()
    cr.restore()
outlined(cr, 'PEACE', 540, 240, 150, (1, 1, 1), sw=24, rot=-0.03)
ball(cr, 'ph', 540, 620, 220, 'happy', 0, 0)
cr.new_path(); cr.arc(540, 960, 105, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill(); emoji(cr, '🔄', 540, 960, 150, 1)
ball(cr, 'phw', 540, 1310, 220, 'angry', 0, 0)
outlined(cr, 'WAR MODE', 540, 1700, 160, GOLD, sw=26, rot=-0.03)
cr.save(); cr.translate(540, 1835); rrect(cr, -440, -60, 880, 104, 28); cr.set_source_rgb(0.05, 0.05, 0.12); cr.fill(); outlined(cr, 'THE FLAG THAT FLIPS FOR WAR', 0, 22, 54, (1, 1, 1), sw=10); cr.restore()
s.write_to_png(out); print('ok')
