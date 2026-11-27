# Cover for "Countryballs: Philippines vs Indonesia, the Island War" (9:16).
import sys, os, math
import cairo
import phid as K
from phid import ptext, rrect, tw, emoji, ball, GOLD, WHITE, INK, CRIMSON, PH_C, ID_C, AU_C, W, H

def cover(data, out):
    K.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_phid'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    cr.save(); cr.rectangle(0, 0, 540, H); cr.clip(); K.set_philippines(cr, 3.0); cr.restore()
    cr.save(); cr.rectangle(540, 0, 540, H); cr.clip(); K.set_indonesia(cr, 3.0); cr.restore()
    cr.move_to(600, 0); cr.line_to(480, H); cr.set_source_rgb(1, 1, 1); cr.set_line_width(14); cr.stroke()
    g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.95); g.add_color_stop_rgba(0.75, 0, 0, 0.05, 0.6); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 900); cr.set_source(g); cr.fill()
    ball(cr, 'Philippines', 270, 1330, 235, 'angry', 0, 0.8); ball(cr, 'Indonesia', 815, 1330, 235, 'angry', 0, -0.8)
    ball(cr, 'Australia', 542, 1030, 95, 'happy', 0, 0); emoji(cr, '⚡', 542, 1330, 180, 1, rot=0.15)
    emoji(cr, '🏝️', 110, 1030, 120, 1, rot=-0.12); emoji(cr, '🦎', 970, 1030, 130, 1, rot=0.12)
    cr.save(); cr.translate(540, 230); cr.rotate(-0.03); ptext(cr, 'PHILIPPINES', 0, 0, 150, PH_C, 1, sw=16); cr.restore()
    cr.new_path(); cr.arc(540, 380, 85, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, 'VS', 540, 415, 94, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 600); cr.rotate(0.03); ptext(cr, 'INDONESIA', 0, 0, 160, ID_C, 1, sw=16); cr.restore()
    t = "7,641 vs 17,000 ISLANDS"; wd = tw(cr, t, 54)
    rrect(cr, 540 - wd / 2 - 40, 700, wd + 80, 96, 48); cr.set_source_rgb(1, 1, 1); cr.fill(); ptext(cr, t, 540, 768, 54, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 1730); cr.rotate(-0.03); t = 'THE ISLAND WAR'; wd = tw(cr, t, 96)
    rrect(cr, -wd / 2 - 46, -96, wd + 92, 140, 30); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 8, 96, WHITE, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, '8 ROUNDS · AUSTRALIA REFS · YOU DECIDE', 540, 1870, 44, GOLD, 1, sw=7)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
