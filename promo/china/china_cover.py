# Cover for "The Entire History of China" (9:16).
import os, sys, math
import cairo
import china as V
from china import R, W, H, GOLD, CRIMSON, PARCH, INK, WHITE, BRICK, ptext, rrect, tw, fit, laea, path_xy

def cover(data_dir, out):
    V.setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_china'))
    R.MAPY = 900
    x, y = laea(104, 35.5); cam = (float(x), float(y), 0.175)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
    V.draw_map(cr, cam)
    cr.new_path(); path_xy(cr, cam, V.G.prc); cr.set_source_rgba(*CRIMSON[:3], 0.55); cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, 0.8); cr.set_line_width(3); cr.stroke()
    V.line(cr, cam, V.WALL, 1.0, BRICK, 9, ticks=True)
    V.vignette(cr, 0.8)
    g = cairo.LinearGradient(0, 0, 0, 700); g.add_color_stop_rgba(0, 0, 0, 0, 0.9); g.add_color_stop_rgba(1, 0, 0, 0, 0); cr.set_source(g); cr.paint()
    # the army rises from the bottom
    g = cairo.LinearGradient(0, 1150, 0, H); g.add_color_stop_rgba(0, 0.1, 0.05, 0.03, 0); g.add_color_stop_rgba(0.35, 0.1, 0.05, 0.03, 0.9)
    g.add_color_stop_rgba(1, 0.2, 0.12, 0.08, 1); cr.set_source(g); cr.paint()
    V.army(cr, 540, 1990, 5, 9, 1.45, 99, 0, 0, 1.0, 140, y_back=1380)
    # dynasty seals
    for i, k in enumerate(('shang', 'zhou', 'qin', 'han', 'tang', 'song', 'yuan', 'ming', 'qing')):
        V.seal(cr, V.DYN[k][0], 92 + i * 112, 1160 + (12 if i % 2 else -12), 100, 1, CRIMSON, rot=0.08 * math.sin(i * 2.1))
    # title
    ptext(cr, 'THE ENTIRE HISTORY OF', 540, 150, 64, PARCH, 1, sw=10)
    cr.save(); cr.translate(540, 360); cr.rotate(-0.03); ptext(cr, 'CHINA', 0, 0, 270, CRIMSON, 1, sw=26); cr.restore()
    cr.save(); cr.translate(540, 500); cr.rotate(-0.03)
    txt = '3,000 YEARS IN 3 MINUTES'; wd = tw(cr, txt, 60)
    rrect(cr, -wd / 2 - 44, -66, wd + 88, 100, 50); cr.set_source_rgb(*GOLD[:3]); cr.fill_preserve(); cr.set_source_rgba(*INK, 1); cr.set_line_width(6); cr.stroke()
    ptext(cr, txt, 0, 6, 60, INK, 1, sw=0, shadow=False); cr.restore()
    surf.write_to_png(out)

if __name__ == '__main__':
    cover(sys.argv[1], sys.argv[2])
