# Cover for "Countryballs: Australia + Canada vs Russia + India, the Tag Team War" (9:16).
import sys, os, math
import cairo
import tagteam as K
from tagteam import ptext, rrect, tw, emoji, ball, GOLD, WHITE, INK, CRIMSON, AU_C, CA_C, W, H

def cover(data, out):
    K.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_tag'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    cr.save(); cr.rectangle(0, 0, 540, H); cr.clip(); K.set_australia(cr, 3.0); cr.restore()
    cr.save(); cr.rectangle(540, 0, 540, H); cr.clip(); K.set_russia(cr, 3.0); cr.restore()
    cr.move_to(600, 0); cr.line_to(480, H); cr.set_source_rgb(1, 1, 1); cr.set_line_width(14); cr.stroke()
    g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.95); g.add_color_stop_rgba(0.75, 0, 0, 0.05, 0.6); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 900); cr.set_source(g); cr.fill()
    ball(cr, 'Canada', 150, 1180, 150, 'angry', 0, 0.8); ball(cr, 'Australia', 330, 1330, 175, 'angry', 0, 0.8)
    ball(cr, 'Russia', 930, 1180, 150, 'angry', 0, -0.8); ball(cr, 'India', 750, 1330, 175, 'angry', 0, -0.8)
    emoji(cr, '⚡', 542, 1250, 200, 1, rot=0.15); emoji(cr, '🤝', 240, 980, 110, 1); emoji(cr, '🤝', 840, 980, 110, 1)
    cr.save(); cr.translate(540, 230); cr.rotate(-0.03); ptext(cr, 'AUSTRALIA + CANADA', 0, 0, 84, AU_C, 1, sw=13); cr.restore()
    cr.new_path(); cr.arc(540, 390, 90, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, 'VS', 540, 426, 100, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 590); cr.rotate(0.03); ptext(cr, 'RUSSIA + INDIA', 0, 0, 118, CA_C, 1, sw=16); cr.restore()
    t = '2 VS 2 · WHO WINS?'; wd = tw(cr, t, 58)
    rrect(cr, 540 - wd / 2 - 40, 700, wd + 80, 100, 50); cr.set_source_rgb(1, 1, 1); cr.fill(); ptext(cr, t, 540, 772, 58, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 1690); cr.rotate(-0.03); t = 'THE TAG TEAM WAR'; wd = tw(cr, t, 84)
    rrect(cr, -wd / 2 - 46, -92, wd + 92, 136, 30); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 8, 84, WHITE, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, '8 ROUNDS · YOU PICK THE TIEBREAKER', 540, 1840, 42, GOLD, 1, sw=7)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
