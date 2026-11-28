# Cover for "Countryballs: Australia vs USA, the Geography War" (9:16).
import sys, os, math
import cairo
import ausa as A
from ausa import ptext, rrect, tw, emoji, ball, GOLD, WHITE, INK, CRIMSON, A_C, U_C, W, H

def cover(data, out):
    A.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_ausa'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    A.ocean(cr, 0)
    cr.save(); cr.translate(540, 1080); cr.rotate(-0.05); cr.translate(-540, -1080); A.overlay(cr, 0, 560, 1080, 0.2, 1); cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.97); g.add_color_stop_rgba(0.7, 0, 0, 0.05, 0.75); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 900); cr.set_source(g); cr.fill()
    g = cairo.LinearGradient(0, 1500, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.05, 0); g.add_color_stop_rgba(0.45, 0, 0, 0.05, 0.95); g.add_color_stop_rgba(1, 0, 0, 0.05, 1); cr.rectangle(0, 1500, W, 420); cr.set_source(g); cr.fill()
    ball(cr, 'Australia', 265, 1290, 235, 'angry', 0, 0.8); ball(cr, 'USA', 815, 1290, 235, 'angry', 0, -0.8)
    emoji(cr, '⚡', 542, 1220, 200, 1, rot=0.15); emoji(cr, '🦘', 110, 1010, 140, 1, rot=-0.15); emoji(cr, '🦅', 970, 1010, 140, 1, rot=0.15)
    cr.save(); cr.translate(540, 250); cr.rotate(-0.03); ptext(cr, 'AUSTRALIA', 0, 0, 170, A_C, 1, sw=18); cr.restore()
    cr.new_path(); cr.arc(540, 420, 95, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, 'VS', 540, 458, 104, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 700); cr.rotate(0.03); ptext(cr, 'USA', 0, 0, 230, U_C, 1, sw=22); cr.restore()
    t = 'SAME SIZE?!'; wd = tw(cr, t, 64)
    rrect(cr, 540 - wd / 2 - 40, 790, wd + 80, 104, 52); cr.set_source_rgb(1, 1, 1); cr.fill(); ptext(cr, t, 540, 865, 64, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 1690); cr.rotate(-0.03); t = 'THE GEOGRAPHY WAR'; wd = tw(cr, t, 84)
    rrect(cr, -wd / 2 - 46, -92, wd + 92, 136, 30); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 8, 84, WHITE, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, '8 ROUNDS · 1 WINNER · YOU DECIDE', 540, 1840, 46, GOLD, 1, sw=7)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
