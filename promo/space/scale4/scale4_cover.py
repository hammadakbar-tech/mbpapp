# Cover image for Scale of the Universe Part 4 (9:16), built from the video's own renderer.
import os, sys
import cairo
import scale4 as V
from vs import ptext, rrect, tw, fit

def cover(out, t=29.6):
    V.setup(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_scale'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, V.W, V.H); cr = cairo.Context(surf)
    V.draw_world(cr, t)
    g = cairo.LinearGradient(0, 0, 0, V.H)  # darken top and bottom for the text
    for o, a in ((0, 0.8), (0.3, 0.0), (0.68, 0.0), (1, 0.85)): g.add_color_stop_rgba(o, 0, 0, 0.03, a)
    cr.set_source(g); cr.paint()
    ptext(cr, 'ZOOM INTO', 540, 300, fit(cr, 'ZOOM INTO', 150, 960), V.WHITE, 1, fam='Poppins Black', sw=14)
    ptext(cr, 'YOURSELF', 540, 470, fit(cr, 'YOURSELF', 170, 980), V.GOLD, 1, fam='Poppins Black', sw=16)
    ptext(cr, V.BIG, 540, 1430, fit(cr, V.BIG, 70, 960), V.CYAN, 1, fam='Poppins Black', sw=9)
    txt = 'SCALE OF THE UNIVERSE · PART 4'; wd_ = tw(cr, txt, 46)
    rrect(cr, 540 - wd_ / 2 - 44, 1488, wd_ + 88, 84, 42); cr.set_source_rgba(*V.PINK[:3], 1); cr.fill()
    ptext(cr, txt, 540, 1546, 46, V.WHITE, 1, sw=5)
    surf.write_to_png(out)

if __name__ == '__main__':
    cover(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 29.6)
