"""YouTube thumbnails (16:9 1280x720 and 9:16 cover) for Canada vs USA, in the video's style."""
import math, sys
import cairo
import vs
from vs import ptext, emoji, rrect, tw, fit, RED, RED2, BLUE, BLUE2, GOLD, WHITE, VIOLET, INK, NAVY

def shapes(cr, cx_ca, cx_us, cy, s):
    for side, cx in (('ca', cx_ca), ('us', cx_us)):
        cr.new_path(); vs.shape_path(cr, side, cx, cy, s)
        cr.set_source_rgba(*vs.SIDE[side][:3], 0.95); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, 1); cr.set_line_width(4); cr.stroke()

def bg(cr, w, h):
    cr.set_source_rgba(*NAVY); cr.paint()
    for col, x in ((RED, 0), (BLUE, w)):
        g = cairo.RadialGradient(x, h / 2, 20, x, h / 2, w * 0.75)
        g.add_color_stop_rgba(0, *col[:3], 0.95); g.add_color_stop_rgba(1, *col[:3], 0)
        cr.set_source(g); cr.paint()
    cr.move_to(w / 2 + 60, 0); cr.line_to(w / 2 - 60, h); cr.set_source_rgba(1, 1, 1, 0.8); cr.set_line_width(6); cr.stroke()

def wide(path):
    w, h = 1280, 720
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h); cr = cairo.Context(s)
    bg(cr, w, h)
    shapes(cr, 300, 980, 440, vs.G.scale * 0.95)
    cr.save(); cr.translate(300, 150); cr.rotate(-0.06); ptext(cr, 'CANADA', 0, 0, 120, WHITE, 1, sw=16); cr.restore()
    cr.save(); cr.translate(980, 150); cr.rotate(0.06); ptext(cr, 'USA', 0, 0, 130, WHITE, 1, sw=16); cr.restore()
    cr.new_path(); cr.arc(640, 400, 120, 0, 2 * math.pi); cr.set_source_rgba(*GOLD[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*INK, 1); cr.set_line_width(10); cr.stroke()
    ptext(cr, 'VS', 640, 445, 130, WHITE, 1, sw=14)
    cr.save(); cr.translate(640, 655); cr.rotate(-0.03)
    t = 'WHO WINS?'; ww = tw(cr, t, 110)
    rrect(cr, -ww / 2 - 40, -100, ww + 80, 130, 26); cr.set_source_rgba(*GOLD[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*INK, 1); cr.set_line_width(8); cr.stroke()
    ptext(cr, t, 0, 10, 110, INK, 1, sw=0, shadow=False); cr.restore()
    emoji(cr, '🍁', 90, 620, 120, 1, rot=-0.2); emoji(cr, '🦅', 1190, 620, 120, 1, rot=0.2)
    emoji(cr, '🤯', 1160, 330, 100, 1, rot=0.15)
    s.write_to_png(path)

def tall(path):
    w, h = 1080, 1920
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h); cr = cairo.Context(s)
    bg(cr, w, h)
    shapes(cr, 270, 810, 900, vs.G.scale * 0.95)
    for txt, x, rot in (('CANADA', 270, -0.06), ('USA', 810, 0.06)):
        cr.save(); cr.translate(x, 520); cr.rotate(rot); ptext(cr, txt, 0, 0, fit(cr, txt, 130, 470), WHITE, 1, sw=16); cr.restore()
    cr.new_path(); cr.arc(540, 900, 130, 0, 2 * math.pi); cr.set_source_rgba(*GOLD[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*INK, 1); cr.set_line_width(10); cr.stroke(); ptext(cr, 'VS', 540, 948, 140, WHITE, 1, sw=14)
    cr.save(); cr.translate(540, 1420); cr.rotate(-0.04)
    t = 'WHO WINS?'; ww = tw(cr, t, 130)
    rrect(cr, -ww / 2 - 40, -115, ww + 80, 150, 30); cr.set_source_rgba(*GOLD[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*INK, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, t, 0, 12, 130, INK, 1, sw=0, shadow=False); cr.restore()
    cr.save(); cr.translate(540, 1600); t = '8 ROUNDS · 1 WINNER'; ww = tw(cr, t, 60)
    rrect(cr, -ww / 2 - 40, -66, ww + 80, 100, 50); cr.set_source_rgba(*VIOLET[:3], 1); cr.fill(); ptext(cr, t, 0, 4, 60, WHITE, 1, sw=6); cr.restore()
    emoji(cr, '🍁', 160, 260, 150, 1, rot=-0.2); emoji(cr, '🦅', 920, 260, 150, 1, rot=0.2)
    s.write_to_png(path)

vs.G = vs.Geo(sys.argv[1]); wide(sys.argv[2]); tall(sys.argv[3])
