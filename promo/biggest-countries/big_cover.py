# Cover for "The 10 Biggest Countries on Earth, at True Size" (9:16, text kept inside TikTok's safe area).
import sys, math
import numpy as np
import cairo
import big as B
from big import ptext, rrect, tw, fit, emoji, GOLD, WHITE, INK, CRIMSON, SKY, LIME, CORAL, W, H

def cover(data, out):
    B.G = B.Geo(data); G = B.G
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.02, 0.03, 0.1); g.add_color_stop_rgb(0.55, 0.05, 0.08, 0.22); g.add_color_stop_rgb(1, 0.02, 0.03, 0.1)
    cr.set_source(g); cr.paint()
    rng = np.random.default_rng(5)
    for _ in range(160):
        cr.new_path(); cr.arc(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.6), 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, rng.uniform(0.2, 0.7)); cr.fill()
    # the globe, huge, half out of frame, lit from the top left
    B.globe(cr, 540, 1700, 780, 95, 58, 'Russia', GOLD, 1.0)
    g = cairo.LinearGradient(0, 1250, 0, H); g.add_color_stop_rgba(0, 0.02, 0.03, 0.1, 0); g.add_color_stop_rgba(1, 0.02, 0.03, 0.1, 0.85); cr.rectangle(0, 1250, W, 700); cr.set_source(g); cr.fill()
    # glow behind the title
    g = cairo.RadialGradient(540, 420, 50, 540, 420, 620); g.add_color_stop_rgba(0, 1, 0.75, 0.2, 0.22); g.add_color_stop_rgba(1, 1, 0.75, 0.2, 0); cr.set_source(g); cr.paint()
    cr.save(); cr.translate(540, 300); cr.rotate(-0.04)
    ptext(cr, 'THE 10', 0, 0, 230, GOLD, 1, sw=22)
    ptext(cr, 'BIGGEST', 0, 190, 190, WHITE, 1, sw=20)
    ptext(cr, 'COUNTRIES', 0, 350, 150, WHITE, 1, sw=18); cr.restore()
    # sticker
    cr.save(); cr.translate(540, 790); cr.rotate(0.03); t = 'AT TRUE SIZE'; wd = tw(cr, t, 84)
    rrect(cr, -wd / 2 - 50, -92, wd + 100, 136, 68); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke()
    ptext(cr, t, 0, 8, 84, WHITE, 1, sw=0, shadow=False); cr.restore()
    # one curiosity line and the rank badge on the glowing country
    cr.save(); cr.translate(250, 1010); cr.rotate(-0.1); cr.new_path(); cr.arc(0, 0, 120, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve()
    cr.set_source_rgb(1, 1, 1); cr.set_line_width(8); cr.stroke(); ptext(cr, '#1', 0, 38, 120, INK, 1, sw=0, shadow=False); cr.restore()
    cr.save(); cr.translate(640, 985); cr.rotate(-0.03)
    ptext(cr, 'COVERS 11%', 0, 0, 92, WHITE, 1, sw=12); ptext(cr, 'OF ALL LAND', 0, 100, 92, GOLD, 1, sw=12); cr.restore()
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
