# Cover for "Countryballs: South America vs Africa, the Geography War" (9:16).
import sys, os, math
import cairo
import saaf as S
from saaf import ptext, rrect, tw, emoji, ball, GOLD, WHITE, INK, CRIMSON, SA_C, AF_C, W, H

def cover(data, out):
    S.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_saaf'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    S.ocean(cr, 0)
    cr.save(); cr.translate(540, 1180); cr.rotate(-0.04); cr.translate(-540, -1180)
    pb, pn = S.joined(cr, 0, 0.62, 0.105, 1150); cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.97); g.add_color_stop_rgba(0.7, 0, 0, 0.05, 0.75); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 900); cr.set_source(g); cr.fill()
    g = cairo.LinearGradient(0, 1500, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.05, 0); g.add_color_stop_rgba(0.45, 0, 0, 0.05, 0.95); g.add_color_stop_rgba(1, 0, 0, 0.05, 1); cr.rectangle(0, 1500, W, 420); cr.set_source(g); cr.fill()
    ball(cr, 'Brazil', 270, 1260, 235, 'angry', 0, 0.8); ball(cr, 'Nigeria', 815, 1260, 235, 'angry', 0, -0.8)
    ball(cr, 'Argentina', 120, 1010, 120, 'angry', 0, 0.7); ball(cr, 'South Africa', 965, 1010, 120, 'angry', 0, -0.7)
    emoji(cr, '⚡', 542, 1230, 230, 1, rot=0.15)
    cr.save(); cr.translate(540, 250); cr.rotate(-0.03); ptext(cr, 'SOUTH AMERICA', 0, 0, 124, SA_C, 1, sw=16); cr.restore()
    cr.save(); cr.translate(540, 650); cr.rotate(0.03); ptext(cr, 'AFRICA', 0, 0, 240, AF_C, 1, sw=22); cr.restore()
    cr.new_path(); cr.arc(540, 420, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, 'VS', 540, 460, 110, INK, 1, sw=0, shadow=False)
    t = 'THEY USED TO BE ONE LAND'; wd = tw(cr, t, 58)
    rrect(cr, 540 - wd / 2 - 36, 762, wd + 72, 96, 48); cr.set_source_rgb(1, 1, 1); cr.fill(); ptext(cr, t, 540, 830, 58, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 1690); cr.rotate(-0.03); t = 'THE GEOGRAPHY WAR'; wd = tw(cr, t, 84)
    rrect(cr, -wd / 2 - 46, -92, wd + 92, 136, 30); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 8, 84, WHITE, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, '66 COUNTRYBALLS · 8 ROUNDS · 1 WINNER?', 540, 1840, 44, GOLD, 1, sw=7)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
