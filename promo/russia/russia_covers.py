"""9:16 Shorts covers for 'The Entire History of Russia', Parts 01 and 02, drawn from each episode's own map.
Usage: python3 russia_covers.py <data_dir> <part01.png> <part02.png>
"""
import math, sys
import numpy as np
import cairo
import russia as R
import russia_p2 as R2
from russia import GOLD, CRIMSON, WHITE, AMBER, ICE, PARCH, INK, KIEV_RUS, HORDE, VIKING, ptext, rrect, tw, fit, emoji
from russia_p2 import BLOOD, RUS_1533, KAZAN_KH, ASTRA_KH, LIVONIA, SIBIR, YERMAK, URALS, knight

W, H = R.W, R.H

def cam_at(lon, lat, scale):
    x, y = R.laea(lon, lat); return float(x), float(y), scale

def base_map(cr, cam, land=(0.24, 0.21, 0.17)):
    cr.set_source_rgba(*R.BG); cr.paint()
    g = cairo.RadialGradient(W / 2, R.MAPY, 100, W / 2, R.MAPY, 1300)
    g.add_color_stop_rgba(0, *R.WATER0[:3], 1); g.add_color_stop_rgba(1, *R.WATER1[:3], 1); cr.set_source(g); cr.paint()
    cr.new_path(); R.path_xy(cr, cam, R.G.land); cr.set_source_rgb(*land); cr.fill_preserve()
    cr.set_source_rgba(*R.COAST[:3], 0.9); cr.set_line_width(1.8); cr.stroke()
    cr.new_path(); R.path_xy(cr, cam, R.G.lakes); cr.set_source_rgba(*R.WATER0[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*R.COAST[:3], 0.7); cr.set_line_width(1); cr.stroke()
    cr.new_path()
    for name, (x, y) in R.G.rivers:
        X, Y = R.S(cam, x, y); cr.move_to(X[0], Y[0]); [cr.line_to(a, b) for a, b in zip(X[1:], Y[1:])]
    cr.set_source_rgba(*R.RIVER[:3], 0.45); cr.set_line_width(2); cr.stroke()

def shade(cr, y0, y1, a0, a1, col=(0, 0, 0)):
    g = cairo.LinearGradient(0, y0, 0, y1); g.add_color_stop_rgba(0, *col, a0); g.add_color_stop_rgba(1, *col, a1)
    cr.rectangle(0, min(y0, y1), W, abs(y1 - y0)); cr.set_source(g); cr.fill()

def vignette(cr, col=(0, 0, 0), a=0.8):
    g = cairo.RadialGradient(W / 2, H / 2, 450, W / 2, H / 2, 1200)
    g.add_color_stop_rgba(0, *col, 0); g.add_color_stop_rgba(1, *col, a); cr.set_source(g); cr.paint()

def label(cr, cam, lon, lat, txt, size, col=WHITE, dx=0, dy=0, anchor='c'):
    x, y = R.L(cam, lon, lat); ptext(cr, txt, x + dx, y + dy, size, col, 1, fam='Poppins ExtraBold', anchor=anchor, sw=8)

def dot(cr, cam, lon, lat, col=GOLD, r=13):
    x, y = R.L(cam, lon, lat)
    cr.new_path(); cr.arc(x, y, r * 2.2, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], 0.25); cr.fill()
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, 1); cr.set_line_width(4); cr.stroke()
    return x, y

def chip(cr, txt, x, y, size, bg, fg=INK, rot=0.0, pad=0.6):
    cr.save(); cr.translate(x, y); cr.rotate(rot); wd = tw(cr, txt, size)
    rrect(cr, -wd / 2 - size * pad, -size * 0.95, wd + size * pad * 2, size * 1.4, size * 0.7)
    cr.set_source_rgba(*bg[:3], 1); cr.fill_preserve(); cr.set_source_rgba(*INK, 1); cr.set_line_width(6); cr.stroke()
    ptext(cr, txt, 0, size * 0.1, size, fg, 1, sw=0, shadow=False); cr.restore()

def title_block(cr, top, big, big_col, sub=None):
    ptext(cr, top, 540, 150, fit(cr, top, 64, 960), PARCH, 1, sw=10)
    cr.save(); cr.translate(540, 370); cr.rotate(-0.03)
    ptext(cr, big, 0, 0, fit(cr, big, 250, 1000), big_col, 1, sw=26); cr.restore()
    if sub:
        cr.save(); cr.translate(540, 500); cr.rotate(-0.03); ptext(cr, sub, 0, 0, fit(cr, sub, 120, 980), WHITE, 1, sw=16); cr.restore()

def part01(path):
    R.MAPY = 1090; cam = cam_at(34, 51.5, 0.345)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
    base_map(cr, cam)
    # the Golden Horde to the south-east, Kievan Rus' in gold
    R.poly(cr, cam, HORDE, CRIMSON, 0.42, edge=CRIMSON, lw=4)
    R.poly(cr, cam, KIEV_RUS, GOLD, 0.55, edge=GOLD, lw=5)
    # the Vikings' river road from Sweden to Constantinople
    R.route(cr, cam, VIKING, 1.0, ICE, width=7, arrow=True, dashed_rest=False)
    # Mongol invasions from the east
    for pts in ([(62, 53.5), (54, 54.5), (47, 55.5), R.P['vladimir']], [(58, 48.5), (48, 49.5), (38, 50.2), (33, 50.4)]):
        R.route(cr, cam, pts, 1.0, CRIMSON, width=9, arrow=True, dashed_rest=False)
    vignette(cr)
    shade(cr, 0, 700, 0.92, 0.0); shade(cr, 1380, 1920, 0.0, 0.95)
    # places
    dot(cr, cam, *R.P['novgorod']); label(cr, cam, *R.P['novgorod'], 'NOVGOROD', 40, dx=-26, dy=14, anchor='r')
    x, y = dot(cr, cam, *R.P['kyiv']); label(cr, cam, *R.P['kyiv'], 'KYIV', 46, dx=-26, dy=16, anchor='r')
    emoji(cr, '🔥', x + 10, y - 60, 80, 1)
    x, y = dot(cr, cam, *R.P['moscow'], col=CRIMSON, r=16); label(cr, cam, *R.P['moscow'], 'MOSCOW', 46, dx=28, dy=-22, anchor='l')
    dot(cr, cam, *R.P['constantinople'], col=ICE, r=10)
    label(cr, cam, *R.P['constantinople'], 'CONSTANTINOPLE', 30, col=ICE, dy=56)
    label(cr, cam, 39.2, 53.0, "KIEVAN RUS'", 50, col=GOLD)
    label(cr, cam, 50.5, 47.5, 'GOLDEN HORDE', 44, col=(1, 0.55, 0.6))
    emoji(cr, '👑', *np.add(R.L(cam, *R.P['novgorod']), (60, -70)), 110, 1, rot=0.15)
    emoji(cr, '⛵', *R.L(cam, 21.5, 59.0), 120, 1, rot=-0.1)
    for lon, lat in ((62, 53.5), (58, 48.5)): emoji(cr, '🏹', *np.add(R.L(cam, lon, lat), (25, 0)), 100, 1, rot=0.3)
    title_block(cr, 'THE ENTIRE HISTORY OF', 'RUSSIA', CRIMSON)
    chip(cr, 'PART 1', 540, 545, 76, GOLD, rot=-0.03)
    # the arc of the episode
    y = 1630; items = (('⛵', 'VIKINGS', ICE), ('🏹', 'MONGOLS', (1, 0.5, 0.55)), ('👑', 'MOSCOW', GOLD))
    for i, (e, txt, col) in enumerate(items):
        x = 180 + i * 360; emoji(cr, e, x, y - 95, 100, 1)
        ptext(cr, txt, x, y + 10, 56, col, 1, sw=10)
        if i < 2: ptext(cr, '›', x + 180, y + 4, 90, WHITE, 0.95, sw=8)
    ptext(cr, '862 – 1480', 540, 1810, 92, WHITE, 1, sw=12)
    s.write_to_png(path)

def part02(path):
    R.MAPY = 1290; cam = cam_at(46.5, 56.3, 0.31)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
    base_map(cr, cam, land=(0.2, 0.15, 0.13))
    R.poly(cr, cam, LIVONIA, (0.6, 0.6, 0.65), 0.3, edge=(0.8, 0.8, 0.85), lw=3, dash=[10, 8])
    R.poly(cr, cam, RUS_1533, CRIMSON, 0.6, edge=WHITE, lw=4)
    for shp in (KAZAN_KH, ASTRA_KH): R.poly(cr, cam, shp, BLOOD, 0.85, edge=CRIMSON, lw=4)
    R.poly(cr, cam, SIBIR, AMBER, 0.45, edge=AMBER, lw=4, dash=[12, 8])
    R.route(cr, cam, YERMAK, 1.0, AMBER, width=7, arrow=True, dashed_rest=False)
    # blood-red mood
    g = cairo.RadialGradient(W / 2, 900, 200, W / 2, 900, 1250)
    g.add_color_stop_rgba(0, 0.35, 0.0, 0.04, 0.35); g.add_color_stop_rgba(1, 0.04, 0, 0, 0.85); cr.set_source(g); cr.paint()
    shade(cr, 0, 900, 0.85, 0.0, (0.06, 0, 0.01)); shade(cr, 1500, 1920, 0.0, 0.95, (0.03, 0, 0))
    # places, with the year each fell to Ivan
    x, y = dot(cr, cam, *R2.P['moscow'], col=GOLD, r=16); label(cr, cam, *R2.P['moscow'], 'MOSCOW', 42, dx=-28, dy=50, anchor='r')
    dot(cr, cam, *R2.P['kazan'], col=CRIMSON); label(cr, cam, *R2.P['kazan'], 'KAZAN 1552', 38, dx=24, dy=48, anchor='l')
    dot(cr, cam, *R2.P['astrakhan'], col=CRIMSON); label(cr, cam, *R2.P['astrakhan'], 'ASTRAKHAN 1556', 36, dx=-24, dy=12, anchor='r')
    x, y = dot(cr, cam, *R2.P['novgorod'], col=CRIMSON); label(cr, cam, *R2.P['novgorod'], 'NOVGOROD 1570', 36, dx=26, dy=12, anchor='l')
    emoji(cr, '🔥', x - 4, y - 58, 76, 1)
    label(cr, cam, 66.5, 60.8, 'SIBERIA', 44, col=AMBER)
    # the Oprichniki: black riders
    for i, (kx, ky, ks) in enumerate(((95, 1610, 110), (215, 1525, 78), (865, 1525, 78), (985, 1610, 110))):
        knight(cr, kx, ky, ks, 1, BLOOD)
    # the cracked crown
    cr.save(); cr.translate(540, 300); emoji(cr, '👑', 0, 0, 330, 1, rot=-0.06)
    rng = np.random.default_rng(3)
    for j in range(6):
        ang = rng.uniform(0, 2 * math.pi); ln = 170
        cr.new_path(); cr.move_to(0, -10); cr.line_to(math.cos(ang) * ln * 0.5 + 12, math.sin(ang) * ln * 0.5 - 6)
        cr.line_to(math.cos(ang) * ln, math.sin(ang) * ln); cr.set_source_rgba(1, 1, 1, 1); cr.set_line_width(6); cr.stroke()
    cr.restore()
    ptext(cr, 'THE ENTIRE HISTORY OF RUSSIA', 540, 100, fit(cr, 'THE ENTIRE HISTORY OF RUSSIA', 54, 960), PARCH, 1, sw=10)
    cr.save(); cr.translate(540, 700); cr.rotate(-0.03); ptext(cr, 'IVAN', 0, 0, 270, CRIMSON, 1, sw=28); cr.restore()
    cr.save(); cr.translate(540, 840); cr.rotate(-0.03); ptext(cr, 'THE TERRIBLE', 0, 0, fit(cr, 'THE TERRIBLE', 130, 980), WHITE, 1, sw=18); cr.restore()
    chip(cr, 'PART 2', 540, 965, 76, GOLD, rot=-0.03)
    chip(cr, "RUSSIA'S FIRST TSAR", 540, 1770, 60, CRIMSON, WHITE, rot=0.02)
    ptext(cr, '1533 – 1613', 540, 1880, 70, WHITE, 1, sw=12)
    s.write_to_png(path)

if __name__ == '__main__':
    R.G = R.Geo(sys.argv[1])
    part01(sys.argv[2]); part02(sys.argv[3])
