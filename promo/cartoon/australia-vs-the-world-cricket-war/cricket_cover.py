# Cover for "Countryballs: Australia vs the World, the Cricket War" (9:16).
import sys, os, math
import cairo
import cricket as K
from cricket import ptext, rrect, tw, emoji, ball, GOLD, WHITE, INK, CRIMSON, AU_C, W_C, W, H, RING

def cover(data, out):
    K.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_cricket'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    cr.save(); cr.translate(0, 120); K.set_ground(cr, 3.0, 'Australia'); cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 980); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.95); g.add_color_stop_rgba(0.75, 0, 0, 0.05, 0.65); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 980); cr.set_source(g); cr.fill()
    for j, nm in enumerate(RING):
        a = -math.pi / 2 + j / 8 * 2 * math.pi + math.pi / 8; x, y = 540 + 400 * math.cos(a), 1330 + 300 * math.sin(a)
        ball(cr, nm, x, y, 100, 'angry', 0, (540 - x) / 400)
    ball(cr, 'Australia', 540, 1330, 200, 'angry', 0, 0)
    cr.save(); cr.translate(540, 220); cr.rotate(-0.03); ptext(cr, 'AUSTRALIA', 0, 0, 170, AU_C, 1, sw=16); cr.restore()
    cr.new_path(); cr.arc(540, 370, 85, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, 'VS', 540, 405, 94, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 590); cr.rotate(0.03); ptext(cr, 'THE WORLD', 0, 0, 170, W_C, 1, sw=16); cr.restore()
    t = "8 NATIONS. WHO WINS?"; wd = tw(cr, t, 56)
    rrect(cr, 540 - wd / 2 - 40, 680, wd + 80, 96, 48); cr.set_source_rgb(1, 1, 1); cr.fill(); ptext(cr, t, 540, 748, 56, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 1730); cr.rotate(-0.03); t = 'THE CRICKET WAR'; wd = tw(cr, t, 90)
    rrect(cr, -wd / 2 - 46, -96, wd + 92, 140, 30); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 8, 90, WHITE, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, '8 ROUNDS · YOU PICK THE FINAL', 540, 1870, 48, GOLD, 1, sw=7)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
