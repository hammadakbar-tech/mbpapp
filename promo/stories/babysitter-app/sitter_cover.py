# Cover for "The Babysitter App" (9:16).
import sys, os, math
import cairo
import sitter as S
from sitter import ptext, rrect, tw, C, YEL, RED, WHITE, W, H

def cover(out):
    S.setup(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_sitter'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    t = 51.0
    cr.save(); S.cam(cr, 1.38, 0.03, 540, 800); cr.set_source_rgb(0.05, 0.05, 0.1); cr.paint()
    S.phone(cr, t, S.scr_cam(t, '11:53', slide=1, sit=1, turn=1), clock='11:53'); cr.restore()
    S.vignette(cr, 0.85)
    g = cairo.LinearGradient(0, 0, 0, 620); g.add_color_stop_rgba(0, 0, 0, 0.03, 1); g.add_color_stop_rgba(0.6, 0, 0, 0.03, 0.9); g.add_color_stop_rgba(1, 0, 0, 0.03, 0); cr.rectangle(0, 0, W, 520); cr.set_source(g); cr.fill()
    g = cairo.LinearGradient(0, 1300, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.03, 0); g.add_color_stop_rgba(0.45, 0, 0, 0.03, 0.95); g.add_color_stop_rgba(1, 0, 0, 0.03, 1); cr.rectangle(0, 1300, W, 620); cr.set_source(g); cr.fill()
    cr.save(); cr.translate(540, 210); cr.rotate(-0.03)
    ptext(cr, 'THE MONITOR SAYS', 0, 0, 88, WHITE, 1, sw=13); ptext(cr, "HE'S ASLEEP", 0, 120, 132, YEL, 1, sw=16); cr.restore()
    cr.save(); cr.translate(540, 1500); cr.rotate(0.02)
    ptext(cr, "BUT YOU'RE", 0, 0, 100, WHITE, 1, sw=13); ptext(cr, 'HOLDING HIM', 0, 130, 132, RED, 1, sw=16); cr.restore()
    s.write_to_png(out)

cover(sys.argv[1])
