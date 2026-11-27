# Cover for "Countryballs: USA vs Philippines vs Australia, the Triple Threat" (9:16).
import sys, os, math
import cairo
import trio as K
from trio import ptext, rrect, tw, emoji, ball, GOLD, WHITE, INK, CRIMSON, US_C, PH_C, AU_C, W, H

def cover(data, out):
    K.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_trio'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    for j, fn in enumerate((K.set_usa, K.set_philippines, K.set_australia)):
        cr.save(); cr.rectangle(j * 360, 0, 360, H); cr.clip(); fn(cr, 3.0); cr.restore()
    for x in (360, 720): cr.move_to(x + 40, 0); cr.line_to(x - 40, H); cr.set_source_rgb(1, 1, 1); cr.set_line_width(12); cr.stroke()
    g = cairo.LinearGradient(0, 0, 0, 1000); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.95); g.add_color_stop_rgba(0.75, 0, 0, 0.05, 0.6); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 1000); cr.set_source(g); cr.fill()
    for n, x in (('USA', 190), ('Philippines', 540), ('Australia', 890)): ball(cr, n, x, 1320, 165, 'angry', 0, (540 - x) / 500)
    for em, x, y, r in (('🍔', 330, 1080, -0.4), ('🥧', 760, 1060, 0.4), ('🍗', 540, 1010, 0.2)): emoji(cr, em, x, y, 140, 1, rot=r)
    ptext(cr, 'USA', 540, 210, 150, US_C, 1, sw=16); ptext(cr, 'PHILIPPINES', 540, 380, 130, PH_C, 1, sw=14); ptext(cr, 'AUSTRALIA', 540, 545, 130, AU_C, 1, sw=14)
    t = "FOOD FIGHT! WHO WINS?"; wd = tw(cr, t, 56)
    rrect(cr, 540 - wd / 2 - 40, 640, wd + 80, 96, 48); cr.set_source_rgb(1, 1, 1); cr.fill(); ptext(cr, t, 540, 708, 56, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 1730); cr.rotate(-0.03); t = 'THE TRIPLE THREAT'; wd = tw(cr, t, 88)
    rrect(cr, -wd / 2 - 46, -96, wd + 92, 140, 30); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 8, 88, WHITE, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, '6 ROUNDS · YOU PICK THE TIEBREAKER', 540, 1870, 46, GOLD, 1, sw=7)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
