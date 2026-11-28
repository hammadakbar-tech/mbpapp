# Cover for "The 10 Most Populated Countries, Resized by People" (9:16, text inside the safe area).
import sys, math
import numpy as np
import cairo
import popu as P
from popu import ptext, rrect, tw, emoji, GOLD, WHITE, INK, CRIMSON, SKY, CORAL, W, H, km_shape, km_path, scaled, bounds

def cover(data, out):
    P.G = P.Geo(data); P.B.G = P.G; G = P.G
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.02, 0.03, 0.1); g.add_color_stop_rgb(0.6, 0.07, 0.07, 0.22); g.add_color_stop_rgb(1, 0.02, 0.03, 0.1)
    cr.set_source(g); cr.paint()
    rng = np.random.default_rng(5)
    for _ in range(150):
        cr.new_path(); cr.arc(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.6), 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, rng.uniform(0.2, 0.7)); cr.fill()
    g = cairo.RadialGradient(540, 400, 50, 540, 400, 620); g.add_color_stop_rgba(0, 1, 0.75, 0.2, 0.2); g.add_color_stop_rgba(1, 1, 0.75, 0.2, 0); cr.set_source(g); cr.paint()
    cr.save(); cr.translate(540, 280); cr.rotate(-0.04)
    ptext(cr, 'THE 10 MOST', 0, 0, 150, GOLD, 1, sw=18); ptext(cr, 'POPULATED', 0, 170, 168, WHITE, 1, sw=19); ptext(cr, 'COUNTRIES', 0, 330, 168, WHITE, 1, sw=19); cr.restore()
    cr.save(); cr.translate(540, 770); cr.rotate(0.03); t = 'RESIZED BY PEOPLE'; wd = tw(cr, t, 72)
    rrect(cr, -wd / 2 - 46, -84, wd + 92, 124, 62); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke()
    ptext(cr, t, 0, 8, 72, WHITE, 1, sw=0, shadow=False); cr.restore()
    # hero: Russia shrunk inside its real outline, Bangladesh blown up beside it
    rs = G.sh['Russia']; x0, x1, y0, y1 = bounds(rs); sc = 960 / (x1 - x0); cx, cy = 540, 1160
    km_path(cr, rs, cx, cy, sc); cr.set_dash([16, 11]); cr.set_source_rgba(1, 1, 1, 0.9); cr.set_line_width(4); cr.stroke(); cr.set_dash([])
    km_shape(cr, scaled(rs, P.factor(P.ENTRIES[1])), cx + 40, cy + 10, sc, SKY, 1, glow=True)
    ptext(cr, 'RUSSIA, SIZED BY PEOPLE', cx, cy + 330, 54, SKY, 1, sw=8)
    cr.save(); cr.translate(815, 965); cr.rotate(0.08); ptext(cr, 'REAL SIZE', 0, 0, 40, WHITE, 1, fam='Poppins ExtraBold', sw=6); cr.restore()
    cr.save(); cr.translate(230, 1010); cr.rotate(-0.1); cr.new_path(); cr.arc(0, 0, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve()
    cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, '#9', 0, 34, 104, INK, 1, sw=0, shadow=False); cr.restore()
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
