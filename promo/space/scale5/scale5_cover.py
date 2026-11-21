# Cover for Scale of the Universe Part 5: Black Holes (9:16), built from the video's own renderer.
import os, sys
import cairo
import scale5 as V
from vs import ptext, rrect, tw, fit

def cover(data_dir, out, t=55.4):
    V.setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_scale5'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, V.W, V.H); cr = cairo.Context(surf)
    s, c = V.camera(t); V.draw_bg(cr, t, s); V.draw_space_scenes(cr, t, s, c)
    g = cairo.LinearGradient(0, 0, 0, V.H)
    for o, a in ((0, 0.85), (0.3, 0.0), (0.72, 0.0), (1, 0.9)): g.add_color_stop_rgba(o, 0.01, 0.0, 0.03, a)
    cr.set_source(g); cr.paint()
    ptext(cr, 'HOW BIG DO', 540, 220, fit(cr, 'HOW BIG DO', 130, 980), V.WHITE, 1, sw=14)
    ptext(cr, 'BLACK HOLES', 540, 370, fit(cr, 'BLACK HOLES', 150, 1000), V.GOLD, 1, sw=15)
    ptext(cr, 'GET?', 540, 510, 140, V.GOLD, 1, sw=15)
    ptext(cr, 'FROM A MARBLE TO 26 SOLAR SYSTEMS', 540, 1440, fit(cr, 'FROM A MARBLE TO 26 SOLAR SYSTEMS', 46, 980, 'Poppins ExtraBold'), V.CYAN, 1, fam='Poppins ExtraBold', sw=6)
    txt = 'SCALE OF THE UNIVERSE · PART 5'; wd_ = tw(cr, txt, 46)
    rrect(cr, 540 - wd_ / 2 - 44, 1500, wd_ + 88, 84, 42); cr.set_source_rgba(*V.PINK[:3], 1); cr.fill()
    ptext(cr, txt, 540, 1558, 46, V.WHITE, 1, sw=5)
    surf.write_to_png(out)

if __name__ == '__main__':
    cover(sys.argv[1], sys.argv[2])
