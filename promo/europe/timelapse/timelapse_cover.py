# Cover for "Europe's Borders: 1914 -> Today" (9:16): 1914 on top, today below.
import os, sys
import cairo
import europe as E
import timelapse as V
from vs import ptext, rrect, tw, fit

def cover(data_dir, out):
    V.setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_timelapse'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, V.W, V.H); cr = cairo.Context(surf)
    x, y = E.laea(19.0, 51.5); cam = (float(x), float(y), 0.205)
    for name, top, cy in (('1914', 0, 470), ('today', 960, 1450)):
        cr.save(); cr.rectangle(0, top, V.W, 960); cr.clip(); cr.translate(0, cy - E.MAPY)
        E.draw_base(cr, 80.0, cam); V.draw_map(cr, 80.0, cam, name, 1.0); E.draw_lakes_vignette(cr, cam); cr.restore()
    g = cairo.LinearGradient(0, 760, 0, 1160)
    for o, a in ((0, 0.0), (0.35, 0.92), (0.65, 0.92), (1, 0.0)): g.add_color_stop_rgba(o, 0.02, 0.03, 0.08, a)
    cr.set_source(g); cr.rectangle(0, 760, V.W, 400); cr.fill()
    ptext(cr, '1914', 540, 250, 190, V.GOLD, 1, sw=18)
    ptext(cr, '100 YEARS', 540, 935, fit(cr, '100 YEARS', 130, 980), V.WHITE, 1, sw=14)
    ptext(cr, 'OF BORDERS', 540, 1060, fit(cr, 'OF BORDERS', 110, 980), V.WHITE, 1, sw=12)
    ptext(cr, 'TODAY', 540, 1820, 170, V.GOLD, 1, sw=17)
    surf.write_to_png(out)

if __name__ == '__main__':
    cover(sys.argv[1], sys.argv[2])
