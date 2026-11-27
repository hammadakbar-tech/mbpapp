# Three A/B-test thumbnails (1280x720) for "Australia vs the World: Season 1".
# A = the ring (existing), B = "1 vs 11" underdog face-off, C = "6 TIES?!" curiosity scoreboard.
import sys, math, os, shutil, cairo, numpy as np
import warballs as B
from warballs import ball
from china import ptext, rrect, tw, emoji, GOLD, WHITE, INK, CRIMSON
from quiz import hexc
data, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
for c in ('au', 'us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id', 'pk'): B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
W, H = 1920, 1080; AU = hexc('#FFC233')[:3]; RED = hexc('#E8333F')[:3]; BLUE = hexc('#4F8CFF')[:3]; GREEN = hexc('#2DBE6C')[:3]
def outlined(cr, txt, x, y, size, fill, sw=None, rot=0.0):
    sw = sw or size * 0.16; cr.save(); cr.translate(x, y); cr.rotate(rot)
    cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); e = cr.text_extents(txt); x0 = -e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.05, size * 0.07); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.5); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(txt); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(sw); cr.stroke_preserve(); cr.set_source_rgb(*fill); cr.fill(); cr.restore()
def rays(cr, cx, cy, col, a, n=28):
    for j in range(n):
        th = j / n * 2 * math.pi; dw = math.pi / n * 0.5
        cr.new_path(); cr.move_to(cx, cy); cr.line_to(cx + 2600 * math.cos(th - dw), cy + 2600 * math.sin(th - dw)); cr.line_to(cx + 2600 * math.cos(th + dw), cy + 2600 * math.sin(th + dw)); cr.close_path(); cr.set_source_rgba(*col, a); cr.fill()
def save(s, name):
    from PIL import Image
    s.write_to_png(f'{out}/{name}.full.png'); Image.open(f'{out}/{name}.full.png').convert('RGB').resize((1280, 720), Image.LANCZOS).save(f'{out}/{name}.png'); os.remove(f'{out}/{name}.full.png')

# ---- B: 1 vs 11 ----
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
cr.rectangle(0, 0, 820, H); cr.set_source_rgb(0.98, 0.72, 0.15); cr.fill(); cr.rectangle(820, 0, W - 820, H); cr.set_source_rgb(0.12, 0.08, 0.3); cr.fill()
cr.save(); cr.rectangle(0, 0, 820, H); cr.clip(); rays(cr, 410, 600, (1, 1, 1), 0.18); cr.restore()
cr.save(); cr.rectangle(820, 0, W, H); cr.clip(); rays(cr, 1380, 600, (0.6, 0.3, 1), 0.12); cr.restore()
cr.new_path(); cr.move_to(760, 0); cr.line_to(900, 0); cr.line_to(800, H); cr.line_to(660, H); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill()
ball(cr, 'au', 400, 640, 330, 'angry', 0, 0.7)
opp = ['us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id', 'pk']
pos = [(1030, 330), (1225, 300), (1420, 320), (1615, 300), (1790, 345), (1090, 560), (1315, 540), (1540, 560), (1765, 565), (1200, 785), (1660, 785)]
for c, (x, y) in zip(opp, pos): ball(cr, c, x, y, 112, 'angry', 0, -0.8)
outlined(cr, '1', 400, 230, 260, (1, 1, 1), sw=40, rot=-0.06)
outlined(cr, 'vs 11', 1430, 1020, 200, AU, sw=34, rot=-0.04)
cr.save(); cr.translate(1440, 120); cr.rotate(0.03); rrect(cr, -330, -62, 660, 112, 26); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); outlined(cr, 'FULL SEASON', 0, 30, 76, (1, 1, 1), sw=12); cr.restore()
save(s, 'thumb-B-1vs11')

# ---- C: 6 TIES?! ----
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
g = cairo.LinearGradient(0, 0, W, H); g.add_color_stop_rgb(0, 0.05, 0.08, 0.25); g.add_color_stop_rgb(1, 0.2, 0.05, 0.25); cr.set_source(g); cr.paint(); rays(cr, 520, 560, BLUE, 0.1)
ball(cr, 'au', 520, 560, 295, 'shock', 0, 0.4)
for x, y, r in ((200, 250, 0.3), (850, 230, -0.3)): outlined(cr, '?!', x, y, 170, AU, sw=26, rot=r)
rrect(cr, 1010, 70, 840, 940, 40); cr.set_source_rgba(0.02, 0.03, 0.08, 0.9); cr.fill_preserve(); cr.set_source_rgb(*AU); cr.set_line_width(8); cr.stroke()
outlined(cr, "AUSTRALIA'S SEASON", 1430, 165, 62, AU, sw=12)
rows = [('vs USA', 'TIE'), ('vs JAPAN', '?'), ('vs FRANCE', '?'), ('vs GREECE', '?'), ('vs PHILIPPINES', 'TIE'), ('vs CRICKET', 'TIE'), ('vs FOOD FIGHT', 'TIE')]
for j, (lab, r) in enumerate(rows):
    y = 270 + j * 78; ptext(cr, lab, 1070, y + 14, 46, WHITE, 1, fam='Poppins ExtraBold', sw=0, shadow=False, anchor='l')
    if r == 'TIE': rrect(cr, 1610, y - 30, 190, 64, 32); cr.set_source_rgb(*BLUE); cr.fill(); ptext(cr, 'TIE', 1705, y + 14, 40, INK, 1, sw=0, shadow=False)
    else: rrect(cr, 1610, y - 30, 190, 64, 32); cr.set_source_rgba(1, 1, 1, 0.15); cr.fill(); ptext(cr, '?', 1705, y + 16, 44, WHITE, 0.8, sw=0, shadow=False)
outlined(cr, '6 TIES?!', 1430, 950, 150, BLUE, sw=26, rot=-0.04)
cr.save(); cr.translate(520, 1000); cr.rotate(-0.03); rrect(cr, -330, -60, 660, 108, 26); cr.set_source_rgb(*RED); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); outlined(cr, 'FULL SEASON 1', 0, 28, 70, (1, 1, 1), sw=12); cr.restore()
save(s, 'thumb-C-6ties')
shutil.copy(sys.argv[3] if len(sys.argv) > 3 else f'{out}/../thumbnail.png', f'{out}/thumb-A-ring.png')
print('ok')
