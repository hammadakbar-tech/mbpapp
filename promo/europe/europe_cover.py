# Cover image for "Why Does Europe Have So Many Countries?" (9:16), built from the video's own map renderer.
import os, sys
import cairo
import europe as V
from vs import ptext, rrect, tw, fit

def cover(data_dir, out, t=86.0):
    V.setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_europe'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, V.W, V.H); cr = cairo.Context(surf)
    cam = V.laea(*V.FULL[:2]); cam = (float(cam[0]) - 150, float(cam[1]) + 820, V.FULL[2] * 1.08)
    V.draw_base(cr, t, cam); V.draw_countries(cr, t, cam); V.draw_lakes_vignette(cr, cam)
    g = cairo.LinearGradient(0, 0, 0, V.H)
    for o, a in ((0, 0.85), (0.27, 0.0), (0.72, 0.0), (1, 0.9)): g.add_color_stop_rgba(o, 0, 0, 0.03, a)
    cr.set_source(g); cr.paint()
    ptext(cr, 'WHY DOES EUROPE', 540, 230, fit(cr, 'WHY DOES EUROPE', 110, 980), V.WHITE, 1, sw=13)
    ptext(cr, 'HAVE 44', 540, 400, fit(cr, 'HAVE 44', 170, 980), V.GOLD, 1, sw=16)
    ptext(cr, 'COUNTRIES?', 540, 545, fit(cr, 'COUNTRIES?', 150, 980), V.GOLD, 1, sw=15)
    txt = 'THE USA HAS JUST ONE'; wd_ = tw(cr, txt, 52)
    rrect(cr, 540 - wd_ / 2 - 48, 1530, wd_ + 96, 92, 46); cr.set_source_rgba(*V.PINK[:3], 1); cr.fill()
    ptext(cr, txt, 540, 1594, 52, V.WHITE, 1, sw=6)
    surf.write_to_png(out)

if __name__ == '__main__':
    cover(sys.argv[1], sys.argv[2])
