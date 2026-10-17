# Cover for "The Planet Show-Off" (9:16).
import os, sys, math
import cairo
import planets as V
import cartoon as C
from vs import ptext, rrect, tw

def cover(out, t=20.0):
    V.setup(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_planets'))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, V.W, V.H); cr = cairo.Context(surf)
    V.draw_scene(cr, t)
    # the host
    V.character(cr, 'sun', 540, 905, 175, t, 0.55, 'sly', (0.0, 0.3))
    V.badge(cr, 790, 760, '11/10', 1.0, s=1.25)
    # the contestants, shocked
    for kind, x, y, r, look in (('jupiter', 205, 1330, 150, (0.6, -0.5)), ('saturn', 865, 1345, 105, (-0.6, -0.5)), ('earth', 535, 1420, 118, (0, -0.6)),
                                ('mars', 150, 1640, 82, (0.6, -0.6)), ('neptune', 930, 1630, 82, (-0.6, -0.6))):
        V.character(cr, kind, x, y, r, t, 0.6, 'shocked', look)
    # Pluto, left out
    V.character(cr, 'pluto', 545, 1700, 95, t, 0.0, 'sad', (0.3, 0.4))
    V.badge(cr, 665, 1600, '0/10', 1.0, (0.75, 0.75, 0.8), s=0.8)
    cr.save(); cr.translate(330, 1585); C.burst(cr, 0, 0, 70, 'NOPE!', (1, 0.35, 0.3), -0.12); cr.restore()
    # title
    rrect(cr, 50, 90, 980, 520, 50); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); C.outline(cr, 10)
    ptext(cr, 'WHICH PLANET', 540, 240, 112, C.OUT, 1, sw=0, shadow=False)
    word, size = 'WINS?', 210; x = 540 - tw(cr, word, size) / 2
    for i, ch in enumerate(word):
        cw = tw(cr, ch, size)
        cr.save(); cr.translate(x + cw / 2, 445); cr.rotate(0.07 * math.sin(i * 2.1))
        ptext(cr, ch, 0, 0, size, V.TITLE_COLS[i], 1, sw=16); cr.restore(); x += cw
    rrect(cr, 250, 500, 580, 76, 38); cr.set_source_rgb(1, 0.31, 0.64); cr.fill_preserve(); C.outline(cr, 6)
    ptext(cr, '8 PLANETS. 1 WINNER.', 540, 553, 44, (1, 1, 1), 1, sw=0, shadow=False)
    surf.write_to_png(out)

if __name__ == '__main__':
    cover(sys.argv[1])
