# Cover for "Countryballs: Australia vs France, the Geography War" (9:16).
import sys, os, math
import cairo
import aufr as K
from aufr import ptext, rrect, tw, emoji, ball, GOLD, WHITE, INK, CRIMSON, AU_C, FR_C, W, H

def cover(data, out):
    K.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_aufr'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    cr.save(); cr.rectangle(0, 0, 540, H); cr.clip(); K.set_australia(cr, 3.0); cr.restore()
    cr.save(); cr.rectangle(540, 0, 540, H); cr.clip(); K.set_france(cr, 3.0); cr.restore()
    cr.move_to(600, 0); cr.line_to(480, H); cr.set_source_rgb(1, 1, 1); cr.set_line_width(14); cr.stroke()
    g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.95); g.add_color_stop_rgba(0.75, 0, 0, 0.05, 0.6); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 900); cr.set_source(g); cr.fill()
    ball(cr, 'Australia', 270, 1290, 235, 'angry', 0, 0.8); ball(cr, 'France', 815, 1290, 235, 'angry', 0, -0.8)
    emoji(cr, '⚡', 542, 1220, 200, 1, rot=0.15); emoji(cr, '🦘', 110, 1000, 130, 1, rot=-0.12); emoji(cr, '🥐', 960, 1000, 130, 1, rot=0.12)
    cr.save(); cr.translate(540, 250); cr.rotate(-0.03); ptext(cr, 'AUSTRALIA', 0, 0, 165, AU_C, 1, sw=18); cr.restore()
    cr.new_path(); cr.arc(540, 420, 95, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, 'VS', 540, 458, 104, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 680); cr.rotate(0.03); ptext(cr, 'FRANCE', 0, 0, 200, FR_C, 1, sw=20); cr.restore()
    t = '14× BIGGER… BUT WHO WINS?'; wd = tw(cr, t, 54)
    rrect(cr, 540 - wd / 2 - 40, 772, wd + 80, 96, 48); cr.set_source_rgb(1, 1, 1); cr.fill(); ptext(cr, t, 540, 840, 54, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 1690); cr.rotate(-0.03); t = 'THE GEOGRAPHY WAR'; wd = tw(cr, t, 84)
    rrect(cr, -wd / 2 - 46, -92, wd + 92, 136, 30); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 8, 84, WHITE, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, '8 ROUNDS + A TIEBREAKER', 540, 1840, 46, GOLD, 1, sw=7)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
