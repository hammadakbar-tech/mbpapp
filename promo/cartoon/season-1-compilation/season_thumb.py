# 1280x720 YouTube thumbnail for "Australia vs the World: Season 1".
import sys, math, os, cairo
import warballs as B
from warballs import ball
from china import ptext, rrect, tw, emoji, GOLD, WHITE, INK, CRIMSON
from quiz import hexc
data, out = sys.argv[1:3]
for c in ('au', 'us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id'): B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
W, H = 1920, 1080; AU = hexc('#FFC233')[:3]
s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
g = cairo.LinearGradient(0, 0, W, H); g.add_color_stop_rgb(0, 0.05, 0.06, 0.2); g.add_color_stop_rgb(1, 0.25, 0.08, 0.2); cr.set_source(g); cr.paint()
r = cairo.RadialGradient(1300, 600, 50, 1300, 600, 800); r.add_color_stop_rgba(0, *AU, 0.45); r.add_color_stop_rgba(1, *AU, 0); cr.set_source(r); cr.paint()
opp = ['us', 'jp', 'fr', 'gb', 'ca', 'gr', 'in', 'ph', 'ru', 'id']
for j, c in enumerate(opp):
    a = -math.pi / 2 + j / len(opp) * 2 * math.pi; ball(cr, c, 1400 + 400 * math.cos(a), 545 + 400 * math.sin(a), 95, 'angry', 0, -math.cos(a))
ball(cr, 'au', 1400, 545, 240, 'angry', 0, -0.3)
cr.save(); cr.translate(520, 250); cr.rotate(-0.04); ptext(cr, 'AUSTRALIA', 0, 0, 150, AU, 1, sw=18); cr.restore()
cr.new_path(); cr.arc(520, 395, 66, 0, 6.283); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 520, 422, 76, INK, 1, sw=0, shadow=False)
cr.save(); cr.translate(520, 570); cr.rotate(0.03); ptext(cr, 'THE WORLD', 0, 0, 150, WHITE, 1, sw=18); cr.restore()
cr.save(); cr.translate(520, 760); cr.rotate(-0.03); t = 'FULL SEASON 1'; wd = tw(cr, t, 90)
rrect(cr, -wd / 2 - 40, -88, wd + 80, 126, 28); cr.set_source_rgb(*CRIMSON[:3]); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(7); cr.stroke(); ptext(cr, t, 0, 6, 90, WHITE, 1, sw=0, shadow=False); cr.restore()
ptext(cr, '12 EPISODES · WHO WON?', 520, 930, 60, GOLD, 1, sw=9)
s.write_to_png(out + '.full.png')
from PIL import Image; Image.open(out + '.full.png').resize((1280, 720), Image.LANCZOS).save(out); os.remove(out + '.full.png')
