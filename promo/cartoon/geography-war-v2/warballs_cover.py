# Cover for "Countryballs: North America vs Europe, the Geography War (Version 2)" (9:16).
import sys, os, math
import cairo
import warballs as B
from warballs import ptext, rrect, tw, GOLD, WHITE, INK, CRIMSON, NA_C, EU_C, W, H, NA, EU, cam, ball

def cover(data, out):
    B.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_warballs'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    cr.save(); cam(cr, 1.0, 0.0, 540, 900); B.arena(cr, 0); B.army(cr, 0.3, NA, 'angry', hop=0); B.army(cr, 0.3, EU, 'angry', hop=0); cr.restore()
    cr.set_source_rgba(0, 0, 0.03, 0.35); cr.paint()
    for n, x, y, r, lk in (('United States of America', 250, 1330, 250, 0.7), ('Germany', 850, 1360, 200, -0.7), ('Canada', 110, 1010, 150, 0.7), ('United Kingdom', 985, 1050, 140, -0.7)):
        ball(cr, n, x, y, r, 'angry', 0, lk)
    g = cairo.LinearGradient(0, 0, 0, 800); g.add_color_stop_rgba(0, 0, 0, 0.03, 0.95); g.add_color_stop_rgba(0.65, 0, 0, 0.03, 0.7); g.add_color_stop_rgba(1, 0, 0, 0.03, 0); cr.rectangle(0, 0, W, 800); cr.set_source(g); cr.fill()
    g = cairo.LinearGradient(0, 1480, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.03, 0); g.add_color_stop_rgba(0.4, 0, 0, 0.03, 0.95); g.add_color_stop_rgba(1, 0, 0, 0.03, 1); cr.rectangle(0, 1480, W, 440); cr.set_source(g); cr.fill()
    cr.save(); cr.translate(540, 250); cr.rotate(-0.03); ptext(cr, 'NORTH AMERICA', 0, 0, 124, NA_C, 1, sw=16); cr.restore()
    cr.save(); cr.translate(540, 640); cr.rotate(0.03); ptext(cr, 'EUROPE', 0, 0, 220, EU_C, 1, sw=22); cr.restore()
    cr.new_path(); cr.arc(540, 420, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, 'VS', 540, 460, 110, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 1690); cr.rotate(-0.03); t = 'THE GEOGRAPHY WAR'; wd = tw(cr, t, 84)
    rrect(cr, -wd / 2 - 46, -92, wd + 92, 136, 30); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 8, 84, WHITE, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, 'VERSION 2 · 67 COUNTRYBALLS · GDP WAR', 540, 1840, 44, GOLD, 1, sw=7)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
