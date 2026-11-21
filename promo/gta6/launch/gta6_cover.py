# Cover for "GTA 6 Is Finally Here: the 13-Year Wait" (9:16). Original neon art, no official Rockstar assets.
import sys, os, math
import cairo
import gta6 as V
from gta6 import ptext, rrect, tw, emoji, chip, INK, WHITE, W, H, PINK, CREAM, HOTPINK, CYAN, RED

def cover(data, out):
    V.setup(data, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_gta6'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); cr.set_antialias(cairo.ANTIALIAS_BEST)
    V.vice(cr, 0.4, 1.4); V.dim(cr, 0.2)
    V.neon(cr, 'GTA 6', 540, 420, 300, CREAM, rot=-0.03)
    V.neon(cr, 'IS FINALLY HERE', 540, 600, 96, HOTPINK, rot=-0.02)
    V.countdown(cr, 0, 1.0, 870)
    V.stamp(cr, '13-YEAR WAIT', 540, 1210, 92, CYAN, 9, 0, -0.06)
    V.neon(cr, '$2.36B ON DAY ONE*', 540, 1520, 92, CREAM)
    ptext(cr, '* SENSOR TOWER ESTIMATE', 540, 1600, 34, WHITE, 0.9, fam='Poppins ExtraBold', sw=6)
    chip(cr, 'THE WHOLE STORY IN 100 SECONDS', 540, 1790, 44, PINK, INK, 1, 1)
    s.write_to_png(out)

cover(sys.argv[1], sys.argv[2])
