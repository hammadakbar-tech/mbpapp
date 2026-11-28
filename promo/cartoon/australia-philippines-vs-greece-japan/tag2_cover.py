# 9:16 cover for Team Pacific vs Team Ancient: Team Pacific (Australia + Philippines) vs Team Ancient (Greece + Japan).
import sys, math, os, cairo
import warballs as B
from warballs import ball
from china import ptext, rrect, emoji
from quiz import hexc
data, out = sys.argv[1:3]
for n, f in (('au', 'au'), ('ph', 'ph'), ('gr', 'gr'), ('jp', 'jp')): B.FL[n] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', f + '.png'))
W, H = 1080, 1920; TA = hexc('#FFC233')[:3]; TB = hexc('#4F8CFF')[:3]; RED = hexc('#E8333F')[:3]
def outlined(cr, txt, x, y, size, fill, sw=None, rot=0.0, maxw=1000):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); e = cr.text_extents(txt)
    if e.width > maxw: size *= maxw / e.width; cr.set_font_size(size); e = cr.text_extents(txt)
    sw = sw or size * 0.16; x0 = -e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.05, size * 0.07); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.5); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(txt); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(sw); cr.stroke_preserve(); cr.set_source_rgb(*fill[:3]); cr.fill(); cr.restore()
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
cr.rectangle(0, 0, W, 960); cr.set_source_rgb(0.98, 0.7, 0.2); cr.fill(); cr.rectangle(0, 960, W, 960); cr.set_source_rgb(0.12, 0.3, 0.75); cr.fill()
for half, cy, col in ((0, 560, (1, 1, 1)), (1, 1380, (0.6, 0.8, 1))):
    cr.save(); cr.rectangle(0, half * 960, W, 960); cr.clip()
    for j in range(26):
        a = j / 26 * 2 * math.pi; cr.new_path(); cr.move_to(540, cy); cr.line_to(540 + 2000 * math.cos(a), cy + 2000 * math.sin(a)); cr.line_to(540 + 2000 * math.cos(a + 0.1), cy + 2000 * math.sin(a + 0.1)); cr.close_path(); cr.set_source_rgba(*col, 0.15); cr.fill()
    cr.restore()
cr.new_path(); cr.move_to(0, 920); cr.line_to(W, 860); cr.line_to(W, 1000); cr.line_to(0, 1060); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill()
outlined(cr, 'TEAM PACIFIC', 540, 200, 120, (1, 1, 1), sw=22, rot=-0.03)
ball(cr, 'au', 330, 560, 190, 'angry', 0, 0.4); ball(cr, 'ph', 750, 560, 190, 'angry', 0, -0.4)
cr.new_path(); cr.arc(540, 960, 110, 0, 2 * math.pi); cr.set_source_rgb(0.05, 0.05, 0.12); cr.fill(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); outlined(cr, 'VS', 540, 1000, 110, TA, sw=18)
ball(cr, 'gr', 330, 1360, 190, 'angry', 0, 0.4); ball(cr, 'jp', 750, 1360, 190, 'angry', 0, -0.4)
outlined(cr, 'TEAM ANCIENT', 540, 1680, 120, (1, 1, 1), sw=22, rot=-0.03)
cr.save(); cr.translate(540, 1820); cr.rotate(-0.03); rrect(cr, -400, -70, 800, 124, 30); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); outlined(cr, 'WHO WINS?', 0, 32, 84, (1, 1, 1), sw=14); cr.restore()
emoji(cr, '⚡', 160, 960, 130, 1, rot=-0.3); emoji(cr, '⚡', 920, 960, 130, 1, rot=0.3)
s.write_to_png(out); print('ok')
