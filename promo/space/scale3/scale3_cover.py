# Cover image for Scale of the Universe Part 3 (9:16), built from the video's own renderer.
import math, os, sys
import cairo
import scale3 as V
from vs import ptext, rrect, tw, fit

def cover(out, t=53.0):
    V.setup(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_scale'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, V.W, V.H); cr = cairo.Context(surf)
    V.draw_universe(cr, t); V.you_are_here(cr, t)
    g = cairo.LinearGradient(0, 0, 0, V.H)  # darken top and bottom for the text
    for o, a in ((0, 0.75), (0.32, 0.0), (0.7, 0.0), (1, 0.8)): g.add_color_stop_rgba(o, 0, 0, 0.02, a)
    cr.set_source(g); cr.paint()
    ptext(cr, 'HOW SMALL', 540, 330, fit(cr, 'HOW SMALL', 150, 960), V.WHITE, 1, fam='Poppins Black', sw=14)
    ptext(cr, 'ARE WE?', 540, 500, fit(cr, 'ARE WE?', 170, 960), V.GOLD, 1, fam='Poppins Black', sw=16)
    ptext(cr, '93 BILLION LIGHT-YEARS', 540, 1420, 60, V.CYAN, 1, fam='Poppins ExtraBold', sw=8)
    txt = 'SCALE OF THE UNIVERSE · PART 3'; wd_ = tw(cr, txt, 46)
    rrect(cr, 540 - wd_ / 2 - 44, 1478, wd_ + 88, 84, 42); cr.set_source_rgba(*V.PINK[:3], 1); cr.fill()
    ptext(cr, txt, 540, 1536, 46, V.WHITE, 1, sw=5)
    surf.write_to_png(out)

if __name__ == '__main__':
    cover(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 53.0)
