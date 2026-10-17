# Cover for "Countryballs: Canada vs USA" (9:16).
import os, sys, math
import cairo
import balls as V
import cartoon as C
from vs import ptext, rrect, tw, fit

def cover(out, t=12.0):
    V.setup(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_balls'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, V.W, V.H); cr = cairo.Context(surf)
    V.draw_scene(cr, t)
    R = 230
    for spk, x, mood, look, talk, tilt in (('ca', 290, 'sly', (0.7, 0), 0.0, 0.12), ('us', 800, 'shocked', (-0.7, 0), 0.7, -0.08)):
        cr.new_path(); cr.save(); cr.translate(x, 1430 + R * 0.95 - 230); cr.scale(1, 0.18); cr.arc(0, 0, R * 0.85, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgba(0, 0, 0, 0.18); cr.fill()
        V.R = R; C.countryball(cr, 'canada' if spk == 'ca' else 'usa', x, 1200, R, talk=talk, look=look, mood=mood, tilt=tilt, sq=0.0)
        V.accessory(cr, spk, x, 1200, tilt, 0.0)
    cr.save(); cr.translate(540, 1020); cr.rotate(-0.06); C.burst(cr, 0, 0, 120, 'VS', (1, 0.8, 0.15), 0.0); cr.restore()
    cr.save(); cr.translate(810, 820); C.burst(cr, 0, 0, 100, 'WHAT?!', (1, 0.35, 0.3), 0.12); cr.restore()
    rrect(cr, 60, 120, 960, 470, 50); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); C.outline(cr, 10)
    ptext(cr, 'CANADA', 540, 270, 140, V.RED, 1, sw=0, shadow=False)
    ptext(cr, 'vs USA', 540, 410, 130, V.BLUE, 1, sw=0, shadow=False)
    ptext(cr, 'WHO WINS?', 540, 535, 90, C.OUT, 1, sw=0, shadow=False)
    surf.write_to_png(out)

if __name__ == '__main__':
    cover(sys.argv[1])
