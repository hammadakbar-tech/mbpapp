# Thumbnails for "The Worst Alliance, Part 01": 1280x720 (YouTube) and 1080x1920 (cover).
import sys, math, os, cairo
import numpy as np
import warballs as B
from warballs import ball
from china import ptext, rrect, INK, WHITE
from quiz import hexc
data, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
AL = ['mn', 'bo', 'li', 'va', 'ad', 'is', 'sm', 'cr', 'nr', 'ch']
for c in AL + ['au']: B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
AU = hexc('#FFC233')[:3]; RED = hexc('#E8333F')[:3]
def outlined(cr, txt, x, y, size, fill, sw=None, rot=0.0, maxw=None):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); e = cr.text_extents(txt)
    if maxw and e.width > maxw: size *= maxw / e.width; cr.set_font_size(size); e = cr.text_extents(txt)
    sw = sw or size * 0.16; x0 = -e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.05, size * 0.07); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.5); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(txt); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(sw); cr.stroke_preserve(); cr.set_source_rgb(*fill[:3]); cr.fill(); cr.restore()
def emu(cr, x, y, s, ph=0.2):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    for leg in (0, 1):
        sw = math.sin(ph * 2 * math.pi + leg * math.pi) * 0.6; cr.move_to(-8 + leg * 14, 20); cr.line_to(-8 + leg * 14 + 30 * math.sin(sw), 90); cr.set_source_rgb(0.35, 0.28, 0.22); cr.set_line_width(7); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
    cr.save(); cr.scale(1.25, 0.85); cr.new_path(); cr.arc(0, 0, 45, 0, 2 * math.pi); cr.restore(); cr.set_source_rgb(0.42, 0.36, 0.3); cr.fill()
    for j in range(7): cr.new_path(); cr.arc(-30 + j * 10, -10 + 18 * math.sin(j * 1.7), 9, 0, 2 * math.pi); cr.set_source_rgb(0.32, 0.26, 0.21); cr.fill()
    cr.move_to(35, -15); cr.curve_to(55, -50, 50, -80, 62, -100); cr.set_source_rgb(0.45, 0.5, 0.65); cr.set_line_width(13); cr.stroke()
    cr.new_path(); cr.arc(66, -106, 12, 0, 2 * math.pi); cr.set_source_rgb(0.3, 0.3, 0.4); cr.fill(); cr.move_to(76, -106); cr.line_to(94, -101); cr.line_to(76, -98); cr.close_path(); cr.set_source_rgb(0.2, 0.18, 0.15); cr.fill()
    cr.new_path(); cr.arc(70, -110, 3.5, 0, 2 * math.pi); cr.set_source_rgb(0.95, 0.5, 0.1); cr.fill(); cr.restore()
def bg(cr, W, H):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.95, 0.55, 0.3); g.add_color_stop_rgb(0.55, 0.98, 0.78, 0.5); g.add_color_stop_rgb(1, 0.7, 0.4, 0.22); cr.set_source(g); cr.paint()
from PIL import Image
# 16:9
W, H = 1920, 1080; s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); bg(cr, W, H)
cr.rectangle(0, 760, W, 400); cr.set_source_rgb(0.78, 0.48, 0.27); cr.fill()
rng = np.random.default_rng(3)
for j in range(26): emu(cr, 1050 + rng.uniform(0, 900), 640 + rng.uniform(0, 380), rng.uniform(0.7, 1.3), rng.uniform(0, 1))
emu(cr, 1500, 640, 2.6)
ball(cr, 'au', 330, 650, 230, 'shock', 0, 0.6)
for j, c in enumerate(AL[:6]): ball(cr, c, 120 + j * 120, 960, 62, 'happy', 0, 0.5)
outlined(cr, 'THE WORST', 560, 170, 150, (1, 1, 1), sw=26, rot=-0.04); outlined(cr, 'ALLIANCE', 560, 330, 170, AU, sw=30, rot=-0.04)
cr.save(); cr.translate(1500, 140); cr.rotate(0.04); rrect(cr, -330, -70, 660, 120, 28); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); outlined(cr, 'vs 20,000 EMUS', 0, 30, 74, (1, 1, 1), sw=12); cr.restore()
cr.save(); cr.translate(860, 520); rrect(cr, -250, -50, 500, 90, 45); cr.set_source_rgb(0.05, 0.05, 0.12); cr.fill(); outlined(cr, 'POWER: 5%', 0, 22, 58, (0.95, 0.35, 0.35), sw=10); cr.restore()
s.write_to_png(f'{out}/t.png'); Image.open(f'{out}/t.png').convert('RGB').resize((1280, 720), Image.LANCZOS).save(f'{out}/thumbnail-16x9.png'); os.remove(f'{out}/t.png')
# 9:16 cover
W, H = 1080, 1920; s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); bg(cr, W, H)
cr.rectangle(0, 1250, W, 700); cr.set_source_rgb(0.78, 0.48, 0.27); cr.fill()
for j in range(22): emu(cr, rng.uniform(-50, 1100), 1180 + rng.uniform(0, 600), rng.uniform(0.7, 1.4), rng.uniform(0, 1))
outlined(cr, 'THE WORST', 540, 220, 150, (1, 1, 1), sw=26, rot=-0.04); outlined(cr, 'ALLIANCE', 540, 390, 170, AU, sw=30, rot=-0.04)
ball(cr, 'au', 540, 850, 200, 'shock', 0, 0)
for j, c in enumerate(AL):
    a = math.pi + (j + 0.5) / len(AL) * math.pi; ball(cr, c, 540 + 440 * math.cos(a), 880 + 360 * math.sin(a), 64, 'happy', 0, 0)
cr.save(); cr.translate(540, 1110); cr.rotate(-0.03); rrect(cr, -380, -70, 760, 120, 30); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); outlined(cr, 'vs 20,000 EMUS', 0, 30, 80, (1, 1, 1), sw=13); cr.restore()
outlined(cr, 'PART 1', 540, 1840, 110, (1, 1, 1), sw=20)
s.write_to_png(f'{out}/cover-9x16.png'); print('ok')
