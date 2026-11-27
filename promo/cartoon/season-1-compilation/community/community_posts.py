# 9:16 (1080x1920) community-post images for the Season 1 compilation.
import sys, math, os, cairo
import warballs as B
from warballs import ball
from china import ptext, rrect, INK, WHITE
from quiz import hexc
data, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
for c in ('au', 'us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id', 'pk'): B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
W, H = 1080, 1920; AU = hexc('#FFC233')[:3]; RED = hexc('#E8333F')[:3]; BLUE = hexc('#4F8CFF')[:3]; GREEN = hexc('#2DBE6C')[:3]
def outlined(cr, txt, x, y, size, fill, sw=None, rot=0.0):
    sw = sw or size * 0.16; cr.save(); cr.translate(x, y); cr.rotate(rot)
    cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); e = cr.text_extents(txt)
    if e.width > 1000: size *= 1000 / e.width; cr.set_font_size(size); e = cr.text_extents(txt); sw = min(sw, size * 0.16)
    x0 = -e.width / 2 - e.x_bearing
    cr.new_path(); cr.move_to(x0 + size * 0.05, size * 0.07); cr.text_path(txt); cr.set_source_rgba(0, 0, 0, 0.5); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, 0); cr.text_path(txt); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(sw); cr.stroke_preserve(); cr.set_source_rgb(*fill); cr.fill(); cr.restore()
def rays(cr, cx, cy, col, a, n=28):
    for j in range(n):
        th = j / n * 2 * math.pi; dw = math.pi / n * 0.5
        cr.new_path(); cr.move_to(cx, cy); cr.line_to(cx + 3000 * math.cos(th - dw), cy + 3000 * math.sin(th - dw)); cr.line_to(cx + 3000 * math.cos(th + dw), cy + 3000 * math.sin(th + dw)); cr.close_path(); cr.set_source_rgba(*col, a); cr.fill()
def ribbon(cr, txt, y, col=RED, size=70, rot=-0.03):
    cr.save(); cr.translate(540, y); cr.rotate(rot); cr.select_font_face('Poppins ExtraBold'); cr.set_font_size(size); w = cr.text_extents(txt).width + 110
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.6, 28); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); outlined(cr, txt, 0, size * 0.36, size, (1, 1, 1), sw=12); cr.restore()
def bgdark(cr, col=BLUE):
    g = cairo.LinearGradient(0, 0, W, H); g.add_color_stop_rgb(0, 0.05, 0.08, 0.25); g.add_color_stop_rgb(1, 0.22, 0.05, 0.25); cr.set_source(g); cr.paint(); rays(cr, 540, 760, col, 0.09)
def tiles(cr, y, rows):
    rrect(cr, 70, y, 940, 110 + 86 * len(rows), 40); cr.set_source_rgba(0.02, 0.03, 0.08, 0.92); cr.fill_preserve(); cr.set_source_rgb(*AU); cr.set_line_width(8); cr.stroke()
    outlined(cr, "AUSTRALIA'S SEASON", 540, y + 78, 58, AU, sw=11)
    for j, (lab, r) in enumerate(rows):
        yy = y + 150 + j * 86; ptext(cr, lab, 130, yy + 14, 48, WHITE, 1, fam='Poppins ExtraBold', sw=0, shadow=False, anchor='l')
        col, a = (BLUE, 1) if r == 'TIE' else ((1, 1, 1), 0.15)
        rrect(cr, 760, yy - 32, 200, 68, 34); cr.set_source_rgba(*col, a); cr.fill(); ptext(cr, r, 860, yy + 16, 44, INK if r == 'TIE' else WHITE, 1 if r == 'TIE' else 0.8, sw=0, shadow=False)
def save(s, n): s.write_to_png(os.path.join(out, n))

# Post 1: 6 TIES?!
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); bgdark(cr)
outlined(cr, 'AUSTRALIA FOUGHT', 540, 190, 84, (1, 1, 1), sw=16); outlined(cr, '11 COUNTRIES…', 540, 300, 96, AU, sw=18)
ball(cr, 'au', 540, 590, 215, 'shock', 0, 0); outlined(cr, '?!', 220, 470, 150, AU, sw=24, rot=0.25); outlined(cr, '?!', 870, 460, 150, AU, sw=24, rot=-0.25)
tiles(cr, 850, [('vs USA', 'TIE'), ('vs JAPAN', '?'), ('vs FRANCE', '?'), ('vs GREECE', '?'), ('vs PHILIPPINES', 'TIE'), ('vs CRICKET', 'TIE'), ('vs FOOD FIGHT', 'TIE')])
outlined(cr, '6 TIES?!', 540, 1720, 160, BLUE, sw=28, rot=-0.04); ribbon(cr, 'FULL SEASON 1 · LINK BELOW', 1850, RED, 52)
save(s, 'post1-6ties-9x16.png')

# Post 2: poll, GUESS THE WINS
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); bgdark(cr, AU)
outlined(cr, 'HOW MANY', 540, 210, 120, (1, 1, 1), sw=20); outlined(cr, 'DID AUSTRALIA', 540, 340, 100, (1, 1, 1), sw=18); outlined(cr, 'WIN?', 540, 500, 190, AU, sw=30, rot=-0.04)
ball(cr, 'au', 540, 900, 210, 'angry', 0, 0)
opp = ['us', 'jp', 'fr', 'gb', 'ca', 'gr', 'in', 'ph', 'id', 'ru', 'pk']
for j, c in enumerate(opp): a = -math.pi / 2 + j / len(opp) * 2 * math.pi; ball(cr, c, 540 + 380 * math.cos(a), 900 + 300 * math.sin(a), 66, 'angry', 0, -math.cos(a))
for j, (lab, col) in enumerate((('0–1', RED), ('2–3', BLUE), ('4–5', GREEN), ('6+', AU))):
    x = 160 + j * 253; rrect(cr, x - 110, 1290, 220, 170, 30); cr.set_source_rgb(*col); cr.fill(); ptext(cr, lab, x, 1395, 72, INK, 1, sw=0, shadow=False)
outlined(cr, 'VOTE, THEN WATCH', 540, 1590, 84, (1, 1, 1), sw=16); outlined(cr, 'THE ANSWER IS AT THE END 👀'.replace(' 👀', ''), 540, 1690, 58, AU, sw=12)
ribbon(cr, 'FULL SEASON 1 · LINK BELOW', 1820, RED, 56)
save(s, 'post2-guess-9x16.png')

# Post 3: 1 vs 11
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
cr.rectangle(0, 0, W, 900); cr.set_source_rgb(0.98, 0.72, 0.15); cr.fill(); cr.rectangle(0, 900, W, H - 900); cr.set_source_rgb(0.12, 0.08, 0.3); cr.fill()
cr.save(); cr.rectangle(0, 0, W, 900); cr.clip(); rays(cr, 540, 520, (1, 1, 1), 0.18); cr.restore(); cr.save(); cr.rectangle(0, 900, W, H); cr.clip(); rays(cr, 540, 1350, (0.6, 0.3, 1), 0.12); cr.restore()
cr.new_path(); cr.move_to(0, 860); cr.line_to(W, 800); cr.line_to(W, 900); cr.line_to(0, 960); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill()
ball(cr, 'au', 540, 520, 300, 'angry', 0, 0); outlined(cr, '1', 540, 170, 200, (1, 1, 1), sw=34)
pos = [(170, 1080), (370, 1060), (570, 1080), (770, 1060), (950, 1100), (260, 1290), (480, 1280), (700, 1290), (910, 1310), (360, 1500), (720, 1500)]
for c, (x, y) in zip(['us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id', 'pk'], pos): ball(cr, c, x, y, 105, 'angry', 0, 0)
outlined(cr, 'vs 11', 540, 1720, 200, AU, sw=34, rot=-0.04); ribbon(cr, 'FULL SEASON 1 · LINK BELOW', 1835, RED, 52)
save(s, 'post3-1vs11-9x16.png')
print('ok')
