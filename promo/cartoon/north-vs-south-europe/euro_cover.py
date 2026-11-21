# Cover for "Countryballs: North Europe vs South Europe, the Geography War" (9:16).
import sys, os, math
import cairo
import euro as E
from euro import ptext, rrect, tw, emoji, ball, GOLD, WHITE, INK, CRIMSON, N_C, S_C, W, H

def cover(data, out):
    E.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_euro'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    E.ocean(cr, 0)
    cr.save(); cr.translate(540, 1150); cr.rotate(-0.03); cr.scale(1.25, 1.25); cr.translate(-540, -1150)
    E.emap(cr, 540, 1150, E.MS, 1, 1, 260); cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.97); g.add_color_stop_rgba(0.7, 0, 0, 0.05, 0.75); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 900); cr.set_source(g); cr.fill()
    g = cairo.LinearGradient(0, 1500, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.05, 0); g.add_color_stop_rgba(0.45, 0, 0, 0.05, 0.95); g.add_color_stop_rgba(1, 0, 0, 0.05, 1); cr.rectangle(0, 1500, W, 420); cr.set_source(g); cr.fill()
    ball(cr, 'Germany', 270, 1250, 230, 'angry', 0, 0.8); ball(cr, 'Italy', 815, 1250, 230, 'angry', 0, -0.8)
    ball(cr, 'France', 540, 1440, 95, 'shock', 0, 0); emoji(cr, '👑', 540, 1325, 90, 1, rot=-0.15)
    ball(cr, 'United Kingdom', 115, 990, 115, 'angry', 0, 0.7); ball(cr, 'Spain', 965, 990, 115, 'angry', 0, -0.7)
    emoji(cr, '⚡', 542, 1180, 200, 1, rot=0.15)
    emoji(cr, '💰', 120, 1450, 120, 1, rot=-0.2); emoji(cr, '☀️', 960, 1450, 120, 1, rot=0.2)
    cr.save(); cr.translate(540, 250); cr.rotate(-0.03); ptext(cr, 'NORTH EUROPE', 0, 0, 128, N_C, 1, sw=16); cr.restore()
    cr.save(); cr.translate(540, 630); cr.rotate(0.03); ptext(cr, 'SOUTH EUROPE', 0, 0, 128, S_C, 1, sw=16); cr.restore()
    cr.new_path(); cr.arc(540, 420, 100, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, 'VS', 540, 460, 110, INK, 1, sw=0, shadow=False)
    t = 'MONEY VS SUN'; wd = tw(cr, t, 62)
    rrect(cr, 540 - wd / 2 - 40, 742, wd + 80, 100, 50); cr.set_source_rgb(1, 1, 1); cr.fill(); ptext(cr, t, 540, 815, 62, INK, 1, sw=0, shadow=False)
    cr.save(); cr.translate(540, 1690); cr.rotate(-0.03); t = 'THE GEOGRAPHY WAR'; wd = tw(cr, t, 84)
    rrect(cr, -wd / 2 - 46, -92, wd + 92, 136, 30); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 8, 84, WHITE, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, '29 COUNTRYBALLS · 8 ROUNDS · 1 WINNER?', 540, 1840, 44, GOLD, 1, sw=7)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
