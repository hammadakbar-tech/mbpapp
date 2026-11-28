"""Cartoon character kit (cairo): thick-outline flat characters with big eyes, blinking, lip-sync mouths,
squash-and-stretch, plus countryballs. style_board() renders a sample sheet.
Usage: python3 cartoon.py <out.png>
"""
import math, sys
import cairo
import vs
from vs import ptext
from quiz import hexc

OUT = (0.12, 0.09, 0.17)  # outline ink

def outline(cr, w=6):
    cr.set_source_rgb(*OUT); cr.set_line_width(w); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()

def blob(cr, x, y, r, col, sq=0.0, w=6):
    """Filled circle with outline and squash (sq > 0 squashes vertically)."""
    cr.save(); cr.translate(x, y); cr.scale(1 + sq * 0.5, 1 - sq)
    cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgb(*col); cr.fill_preserve(); outline(cr, w)

def shade(cr, x, y, r, sq=0.0):
    cr.save(); cr.translate(x, y); cr.scale(1 + sq * 0.5, 1 - sq)
    g = cairo.RadialGradient(-r * 0.35, -r * 0.4, r * 0.1, 0, 0, r * 1.02)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.35); g.add_color_stop_rgba(0.55, 1, 1, 1, 0.0); g.add_color_stop_rgba(1, 0, 0, 0, 0.25)
    cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source(g); cr.fill(); cr.restore()

def eyes(cr, x, y, size, look=(0.0, 0.0), blink=0.0, mood='happy', gap=1.0):
    """Two big cartoon eyes. mood: happy / grumpy / shocked / sly."""
    for side in (-1, 1):
        ex = x + side * size * 0.95 * gap; ey = y
        h = size * (1.25 if mood == 'shocked' else 1.0) * max(0.08, 1 - blink)
        cr.save(); cr.translate(ex, ey); cr.scale(0.82, h / size)
        cr.new_path(); cr.arc(0, 0, size, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); outline(cr, size * 0.12)
        if blink < 0.7:
            px, py = ex + look[0] * size * 0.3, ey + look[1] * size * 0.3
            pr = size * (0.38 if mood == 'shocked' else 0.5)
            cr.new_path(); cr.arc(px, py, pr, 0, 2 * math.pi); cr.set_source_rgb(*OUT); cr.fill()
            cr.new_path(); cr.arc(px - pr * 0.35, py - pr * 0.4, pr * 0.32, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill()
        if mood in ('grumpy', 'sly'):  # eyebrows
            cr.new_path(); tilt = 0.35 if mood == 'grumpy' else -0.2
            cr.move_to(ex - size * 0.8, ey - size * (1.05 - side * tilt * (1 if mood == 'grumpy' else -1)))
            cr.line_to(ex + size * 0.8, ey - size * (1.05 + side * tilt * (1 if mood == 'grumpy' else -1)))
            outline(cr, size * 0.22)

def mouth(cr, x, y, w, open_=0.0, mood='happy'):
    """open_ 0..1 (drive it from the voice for lip-sync)."""
    if mood == 'grumpy' and open_ < 0.15:
        cr.new_path(); cr.move_to(x - w / 2, y + w * 0.12); cr.curve_to(x - w / 4, y - w * 0.1, x + w / 4, y - w * 0.1, x + w / 2, y + w * 0.12); outline(cr, w * 0.1); return
    hgt = w * (0.12 + 0.55 * open_)
    cr.new_path(); cr.move_to(x - w / 2, y); cr.curve_to(x - w / 2, y + hgt * 1.4, x + w / 2, y + hgt * 1.4, x + w / 2, y)
    cr.curve_to(x + w / 4, y + hgt * 0.15, x - w / 4, y + hgt * 0.15, x - w / 2, y); cr.close_path()
    cr.set_source_rgb(0.45, 0.08, 0.15); cr.fill_preserve(); outline(cr, w * 0.08)
    if open_ > 0.25:  # tongue
        cr.save(); cr.new_path(); cr.move_to(x - w / 2, y); cr.curve_to(x - w / 2, y + hgt * 1.4, x + w / 2, y + hgt * 1.4, x + w / 2, y); cr.close_path(); cr.clip()
        cr.new_path(); cr.arc(x, y + hgt * 1.15, w * 0.28, 0, 2 * math.pi); cr.set_source_rgb(1, 0.45, 0.5); cr.fill(); cr.restore()

def cheeks(cr, x, y, r, gap):
    for side in (-1, 1):
        cr.new_path(); cr.save(); cr.translate(x + side * gap, y); cr.scale(1, 0.6); cr.arc(0, 0, r, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgba(1, 0.4, 0.5, 0.45); cr.fill()

def arm(cr, x0, y0, x1, y1, bend=0.3, col=(1, 1, 1), w=16):
    mx, my = (x0 + x1) / 2 - (y1 - y0) * bend, (y0 + y1) / 2 + (x1 - x0) * bend
    cr.new_path(); cr.move_to(x0, y0); cr.curve_to(mx, my, mx, my, x1, y1)
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_source_rgb(*OUT); cr.set_line_width(w + 10); cr.stroke_preserve()
    cr.set_source_rgb(*col); cr.set_line_width(w); cr.stroke()
    cr.new_path(); cr.arc(x1, y1, w * 0.9, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill_preserve(); outline(cr, 5)

# ---------- characters ----------
def planet_char(cr, kind, x, y, r, t=0.0, talk=0.0, mood='happy', look=(0, 0), blink=0.0, bounce=0.0):
    sq = 0.08 * math.sin(bounce * math.pi) if bounce else 0.0
    y = y - abs(math.sin(bounce * math.pi)) * r * 0.25 if bounce else y
    if kind == 'earth':
        blob(cr, x, y, r, (0.25, 0.6, 1.0), sq)
        cr.save(); cr.new_path(); cr.arc(x, y, r - 3, 0, 2 * math.pi); cr.clip()
        for dx, dy, rx, ry, rot in ((-0.45, -0.35, 0.38, 0.25, 0.4), (0.35, -0.55, 0.3, 0.18, -0.3), (0.45, 0.35, 0.32, 0.22, 0.8), (-0.3, 0.55, 0.25, 0.14, -0.5)):
            cr.save(); cr.translate(x + dx * r, y + dy * r); cr.rotate(rot); cr.scale(rx * r, ry * r); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
            cr.set_source_rgb(0.35, 0.82, 0.4); cr.fill()
        cr.restore()
    elif kind == 'mars':
        blob(cr, x, y, r, (0.95, 0.45, 0.25), sq)
        for dx, dy, cr_ in ((-0.5, -0.4, 0.14), (0.45, -0.5, 0.1), (0.5, 0.45, 0.16), (-0.45, 0.5, 0.09)):
            cr.new_path(); cr.arc(x + dx * r, y + dy * r, cr_ * r, 0, 2 * math.pi); cr.set_source_rgb(0.8, 0.32, 0.18); cr.fill()
    elif kind == 'sun':
        for i in range(12):
            a = i * math.pi / 6 + t * 0.5; cr.new_path()
            cr.move_to(x + r * 1.05 * math.cos(a - 0.12), y + r * 1.05 * math.sin(a - 0.12)); cr.line_to(x + r * 1.45 * math.cos(a), y + r * 1.45 * math.sin(a))
            cr.line_to(x + r * 1.05 * math.cos(a + 0.12), y + r * 1.05 * math.sin(a + 0.12)); cr.close_path()
            cr.set_source_rgb(1, 0.7, 0.15); cr.fill_preserve(); outline(cr, 5)
        blob(cr, x, y, r, (1, 0.85, 0.25), sq)
    shade(cr, x, y, r, sq)
    eyes(cr, x, y - r * 0.12, r * 0.22, look, blink, mood)
    mouth(cr, x, y + r * 0.38, r * 0.42, talk, mood)
    if mood == 'happy': cheeks(cr, x, y + r * 0.22, r * 0.13, r * 0.52)

MAPLE = [(0, -1.0), (0.12, -0.72), (0.3, -0.8), (0.24, -0.38), (0.55, -0.6), (0.5, -0.45), (0.78, -0.48), (0.66, -0.25), (0.75, -0.16),
         (0.35, 0.12), (0.4, 0.28), (0.04, 0.22), (0.04, 0.62), (-0.04, 0.62), (-0.04, 0.22), (-0.4, 0.28), (-0.35, 0.12), (-0.75, -0.16),
         (-0.66, -0.25), (-0.78, -0.48), (-0.5, -0.45), (-0.55, -0.6), (-0.24, -0.38), (-0.3, -0.8), (-0.12, -0.72)]
def flag_canada(cr, x, y, r):
    cr.set_source_rgb(0.85, 0.12, 0.17); cr.rectangle(x - r, y - r, 2 * r, 2 * r); cr.fill()
    cr.set_source_rgb(1, 1, 1); cr.rectangle(x - r * 0.5, y - r, r, 2 * r); cr.fill()
    cr.new_path(); s = r * 0.42
    for i, (px, py) in enumerate(MAPLE): (cr.move_to if i == 0 else cr.line_to)(x + px * s, y + py * s - s * 0.05)
    cr.close_path(); cr.set_source_rgb(0.85, 0.12, 0.17); cr.fill()
def flag_usa(cr, x, y, r):
    for i in range(13):
        cr.set_source_rgb(*((0.75, 0.1, 0.18) if i % 2 == 0 else (1, 1, 1))); cr.rectangle(x - r, y - r + i * 2 * r / 13, 2 * r, 2 * r / 13 + 1); cr.fill()
    cr.set_source_rgb(0.15, 0.2, 0.45); cr.rectangle(x - r, y - r, r * 0.95, r * 1.08); cr.fill()
    cr.set_source_rgb(1, 1, 1)
    for i in range(5):
        for j in range(6):
            cr.new_path(); cr.arc(x - r + r * 0.1 + j * r * 0.15, y - r + r * 0.13 + i * r * 0.2, r * 0.025, 0, 2 * math.pi); cr.fill()
FLAGS = {'canada': flag_canada, 'usa': flag_usa}

def countryball(cr, flag, x, y, r, talk=0.0, look=(0, 0), blink=0.0, mood='happy', tilt=0.0, bounce=0.0, sq=None):
    """Countryball: a flag-filled ball with plain white eyes (talking mouth optional). sq: squash (+) / stretch (-)."""
    if sq is None:
        y = y - abs(math.sin(bounce * math.pi)) * r * 0.25 if bounce else y
        sq = 0.07 * math.sin(bounce * math.pi * 2) if bounce else 0.0
    cr.save(); cr.translate(x, y); cr.rotate(tilt); cr.scale(1 + sq * 0.5, 1 - sq)
    cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.save(); cr.clip(); FLAGS[flag](cr, 0, 0, r); cr.restore()
    cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); outline(cr, 7)
    shade(cr, 0, 0, r)
    for side in (-1, 1):
        ex = side * r * 0.32 + look[0] * r * 0.08; ey = -r * 0.12 + look[1] * r * 0.06
        hh = r * 0.2 * max(0.08, 1 - blink) * (1.2 if mood == 'shocked' else 1)
        cr.save(); cr.translate(ex, ey); cr.scale(r * 0.14, hh); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); outline(cr, 5)
        if mood == 'grumpy':
            cr.new_path(); cr.move_to(ex - r * 0.18, ey - r * (0.3 - side * 0.08)); cr.line_to(ex + r * 0.18, ey - r * (0.3 + side * 0.08)); outline(cr, 8)
    if talk > 0.02 or mood != 'happy': mouth(cr, 0, r * 0.42, r * 0.36, talk, mood)
    cr.restore()

def astronaut(cr, x, y, s, t=0.0, wave=0.0, talk=0.0, mood='happy', blink=0.0):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.new_path(); cr.rectangle(-70, -10, 140, 120); rr = 50
    rect = lambda X, Y, Wd, Hh, R: (cr.new_path(), cr.arc(X + R, Y + R, R, math.pi, 1.5 * math.pi), cr.arc(X + Wd - R, Y + R, R, 1.5 * math.pi, 0),
                                    cr.arc(X + Wd - R, Y + Hh - R, R, 0, 0.5 * math.pi), cr.arc(X + R, Y + Hh - R, R, 0.5 * math.pi, math.pi), cr.close_path())
    rect(-95, 20, 190, 120, 34); cr.set_source_rgb(0.85, 0.87, 0.93); cr.fill_preserve(); outline(cr, 7)  # backpack
    for side in (-1, 1):  # legs
        cr.new_path(); cr.move_to(side * 35, 170); cr.line_to(side * 45, 250); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_source_rgb(*OUT); cr.set_line_width(58); cr.stroke_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(46); cr.stroke()
        cr.new_path(); cr.arc(side * 47, 262, 30, math.pi, 2 * math.pi); cr.close_path(); cr.set_source_rgb(0.6, 0.65, 0.75); cr.fill_preserve(); outline(cr, 6)
    rect(-75, 0, 150, 190, 60); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); outline(cr, 7)  # body
    rect(-35, 60, 70, 46, 10); cr.set_source_rgb(0.3, 0.75, 1); cr.fill_preserve(); outline(cr, 5)
    for i, col in enumerate(((1, 0.35, 0.4), (1, 0.85, 0.2), (0.4, 0.9, 0.4))):
        cr.new_path(); cr.arc(-18 + i * 18, 83, 6, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill()
    arm(cr, -70, 40, -125, 120, -0.3, w=30)
    ang = -1.2 - 0.5 * math.sin(wave * math.pi * 4)
    arm(cr, 70, 40, 70 + 85 * math.cos(ang + 0.6), 40 + 85 * math.sin(ang + 0.6) - 30, 0.25, w=30)
    blob(cr, 0, -70, 105, (1, 1, 1), 0, 7)  # helmet
    cr.save(); cr.new_path(); cr.save(); cr.translate(0, -62); cr.scale(1.0, 0.78); cr.arc(0, 0, 78, 0, 2 * math.pi); cr.restore()
    g = cairo.LinearGradient(0, -130, 0, 0); g.add_color_stop_rgb(0, 0.15, 0.25, 0.55); g.add_color_stop_rgb(1, 0.06, 0.1, 0.25)
    cr.set_source(g); cr.fill_preserve(); outline(cr, 6); cr.restore()
    cr.save(); cr.translate(0, -62); cr.scale(1, 0.78); cr.new_path(); cr.arc(0, 0, 74, 0, 2 * math.pi); cr.restore(); cr.save(); cr.clip()
    blob(cr, 0, -55, 60, (1.0, 0.82, 0.68), 0, 0); eyes(cr, 0, -70, 15, (0.3, -0.1), blink, mood); mouth(cr, 0, -38, 30, talk, mood)
    cheeks(cr, 0, -48, 9, 32); cr.restore()
    cr.new_path(); cr.save(); cr.translate(-35, -100); cr.rotate(-0.6); cr.scale(18, 8); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgba(1, 1, 1, 0.75); cr.fill()
    cr.restore()

def black_hole_toon(cr, x, y, r, t=0.0):
    for i in range(5, 0, -1):
        cr.save(); cr.translate(x, y); cr.rotate(t * 0.8 + i * 0.4); cr.scale(1.0, 0.42)
        cr.new_path(); cr.arc(0, 0, r * (1.05 + i * 0.18), 0, 2 * math.pi); cr.restore()
        cr.set_source_rgb(*[(1, 0.85, 0.3), (1, 0.6, 0.2), (1, 0.4, 0.3), (0.9, 0.3, 0.6), (0.6, 0.3, 0.9)][i - 1]); cr.set_line_width(r * 0.14); cr.stroke()
    blob(cr, x, y, r, (0.05, 0.03, 0.08), 0, 7)
    eyes(cr, x, y - r * 0.1, r * 0.2, (-0.6, 0.2), 0.0, 'sly'); mouth(cr, x, y + r * 0.38, r * 0.5, 0.35, 'happy')

def burst(cr, x, y, r, txt, col, rot=-0.15):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.new_path()
    for i in range(24):
        a = i * math.pi / 12; rr = r * (1.0 if i % 2 == 0 else 0.72); (cr.move_to if i == 0 else cr.line_to)(rr * 1.3 * math.cos(a), rr * math.sin(a))
    cr.close_path(); cr.set_source_rgb(*col); cr.fill_preserve(); outline(cr, 6)
    ptext(cr, txt, 0, r * 0.22, r * 0.62, (1, 1, 1), 1, sw=10); cr.restore()

def bubble(cr, x, y, txt, size=40, tail=(0, 1), maxw=520):
    from vs import tw
    wd = tw(cr, txt, size, 'Poppins ExtraBold'); bw, bh = wd + 60, size * 1.9
    cr.new_path(); r = bh / 2
    cr.arc(x - bw / 2 + r, y, r, 0.5 * math.pi, 1.5 * math.pi); cr.arc(x + bw / 2 - r, y, r, 1.5 * math.pi, 0.5 * math.pi); cr.close_path()
    cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); outline(cr, 6)
    tx, ty = x + tail[0] * bw * 0.25, y + bh / 2 - 3
    cr.new_path(); cr.move_to(tx - 18, ty); cr.line_to(tx + tail[0] * 40, ty + 46); cr.line_to(tx + 18, ty); cr.close_path()
    cr.set_source_rgb(1, 1, 1); cr.fill(); cr.new_path(); cr.move_to(tx - 18, ty); cr.line_to(tx + tail[0] * 40, ty + 46); cr.line_to(tx + 18, ty); outline(cr, 6)
    ptext(cr, txt, x, y + size * 0.35, size, OUT, 1, fam='Poppins ExtraBold', sw=0, shadow=False)

def panel_bg(cr, y0, h, c0, c1, kind='sky'):
    g = cairo.LinearGradient(0, y0, 0, y0 + h); g.add_color_stop_rgb(0, *c0); g.add_color_stop_rgb(1, *c1)
    cr.rectangle(0, y0, 1080, h); cr.set_source(g); cr.fill()
    cr.save(); cr.rectangle(0, y0, 1080, h); cr.clip()
    for i in range(0, 1080, 36):  # halftone dots
        for j in range(int(y0), int(y0 + h), 36):
            cr.new_path(); cr.arc(i + (18 if (j // 36) % 2 else 0), j, 3.2, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.12); cr.fill()
    if kind == 'space':
        import random; rnd = random.Random(3)
        for _ in range(60):
            sx, sy = rnd.uniform(0, 1080), rnd.uniform(y0, y0 + h); cr.new_path()
            for k in range(8):
                a = k * math.pi / 4; rr = 9 if k % 2 == 0 else 3; (cr.move_to if k == 0 else cr.line_to)(sx + rr * math.cos(a), sy + rr * math.sin(a))
            cr.close_path(); cr.set_source_rgba(1, 1, 0.8, 0.8); cr.fill()
    elif kind == 'hills':
        cr.new_path(); cr.move_to(0, y0 + h); cr.line_to(0, y0 + h - 110); cr.curve_to(300, y0 + h - 230, 600, y0 + h - 40, 1080, y0 + h - 170); cr.line_to(1080, y0 + h); cr.close_path()
        cr.set_source_rgb(0.45, 0.82, 0.45); cr.fill_preserve(); outline(cr, 6)
        for cx_, cy_ in ((200, y0 + 90), (820, y0 + 70)):
            for dx, rr in ((-45, 38), (0, 52), (48, 36)): cr.new_path(); cr.arc(cx_ + dx, cy_, rr, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill()
    cr.restore()
    cr.rectangle(0, y0, 1080, h); outline(cr, 10)

def style_board(out):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1080, 1920); cr = cairo.Context(surf)
    cr.set_source_rgb(0.12, 0.09, 0.17); cr.paint()
    # panel 1: talking planets
    panel_bg(cr, 0, 640, (0.2, 0.15, 0.45), (0.45, 0.25, 0.6), 'space')
    planet_char(cr, 'sun', 860, 150, 80, t=0.3, talk=0.0, mood='sly')
    planet_char(cr, 'earth', 300, 400, 150, talk=0.6, mood='happy', look=(0.6, 0))
    planet_char(cr, 'mars', 760, 430, 120, talk=0.0, mood='grumpy', look=(-0.6, 0))
    bubble(cr, 330, 150, "I have OCEANS!", 40, (-0.6, 1))
    bubble(cr, 690, 240, "...and I have dust.", 34, (0.4, 1))
    ptext(cr, 'TALKING PLANETS', 540, 610, 44, (1, 0.85, 0.3), 1, sw=8)
    # panel 2: countryballs
    panel_bg(cr, 640, 640, (0.45, 0.78, 1.0), (0.75, 0.92, 1.0), 'hills')
    countryball(cr, 'canada', 300, 1010, 150, talk=0.5, look=(0.6, 0), tilt=-0.08)
    countryball(cr, 'usa', 790, 1000, 165, talk=0.0, look=(-0.7, 0), mood='shocked', tilt=0.06)
    bubble(cr, 330, 780, "Sorry, eh! I'm bigger!", 38, (-0.2, 1))
    burst(cr, 820, 760, 85, 'WHAT?!', (1, 0.35, 0.3), 0.12)
    ptext(cr, 'COUNTRYBALLS', 540, 1250, 44, (0.15, 0.2, 0.45), 1, sw=0, shadow=False)
    # panel 3: astronaut + black hole
    panel_bg(cr, 1280, 640, (0.08, 0.05, 0.2), (0.25, 0.1, 0.35), 'space')
    black_hole_toon(cr, 800, 1560, 110, t=0.6)
    astronaut(cr, 300, 1570, 1.05, wave=0.1, talk=0.7, mood='shocked')
    burst(cr, 560, 1370, 70, 'NOPE!', (1, 0.8, 0.2), -0.18)
    ptext(cr, 'CARTOON EXPLAINERS', 540, 1890, 44, (1, 0.85, 0.3), 1, sw=8)
    surf.write_to_png(out)

if __name__ == '__main__':
    style_board(sys.argv[1])
