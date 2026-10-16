# Cover for "Europe's Weirdest Borders" (9:16): the Baarle patchwork.
import os, sys, math
import cairo
import europe as E
import borders as V
from vs import ptext, rrect, tw, fit

def cover(data_dir, out, t=6.6):
    V.setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_borders'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, V.W, V.H); cr = cairo.Context(surf)
    x, y = E.laea(*V.D.baarle_c); cam = (float(x), float(y) + 0.35, V.D.baarle_s * 0.95)
    E.draw_base(cr, t, cam); V.draw_countries(cr, t, cam); V.draw_baarle(cr, t, cam); E.draw_lakes_vignette(cr, cam)
    g = cairo.LinearGradient(0, 0, 0, V.H)
    for o, a in ((0, 0.92), (0.3, 0.6), (0.4, 0.0), (0.75, 0.0), (1, 0.9)): g.add_color_stop_rgba(o, 0.02, 0.03, 0.08, a)
    cr.set_source(g); cr.paint()
    ptext(cr, 'THIS TOWN IS IN', 540, 230, fit(cr, 'THIS TOWN IS IN', 110, 980), V.WHITE, 1, sw=13)
    ptext(cr, '2 COUNTRIES', 540, 400, fit(cr, '2 COUNTRIES', 170, 980), V.GOLD, 1, sw=16)
    for txt, col, xx in (('BELGIUM', V.CC['BEL'], 300), ('NETHERLANDS', V.CC['NLD'], 720)):
        wd_ = tw(cr, txt, 40, 'Poppins ExtraBold'); bw = wd_ + 100
        rrect(cr, xx - bw / 2, 1440, bw, 70, 35); cr.set_source_rgba(0.04, 0.06, 0.16, 0.9); cr.fill()
        cr.new_path(); cr.arc(xx - bw / 2 + 36, 1475, 18, 0, 2 * math.pi); cr.set_source_rgba(*col, 1); cr.fill()
        ptext(cr, txt, xx + 22, 1489, 40, V.WHITE, 1, fam='Poppins ExtraBold', sw=0, shadow=False)
    txt = "EUROPE'S WEIRDEST BORDERS"; wd_ = tw(cr, txt, 50)
    rrect(cr, 540 - wd_ / 2 - 48, 1560, wd_ + 96, 92, 46); cr.set_source_rgba(*V.PINK[:3], 1); cr.fill()
    ptext(cr, txt, 540, 1624, 50, V.WHITE, 1, sw=6)
    surf.write_to_png(out)

if __name__ == '__main__':
    cover(sys.argv[1], sys.argv[2])
