"""'The Babysitter App' (9:16): a second-person suspense story told in flat 2D vector animation: phone screens, a living room,
a staircase, a HUD clock and an 'IN THE HOUSE' counter, a new camera angle every few seconds, and a one-word comment choice.
Word-synced to the narrator (timing engine from china.py). Usage: python3 sitter.py <out.mp4> [--preview t1,...]
"""
import math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
from china import ptext, rrect, tw, fit, emoji, pop_k, W, H, FPS, WHITE
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

C.VOICE, C.RATE = os.environ.get('SITTER_VOICE', 'en-US-ChristopherNeural'), '-3%'
C.SAY = {None: {}}
C.HOT = ('baby', 'monitor', 'crib', 'holding', 'noah', 'shape', 'tall', 'offline', 'nursery', 'upstairs', 'leave', 'bedtime', 'smiles', 'door',
         'stairs', 'motion', 'second', 'dark', 'camera', 'breathing', 'creaks', 'whispers', 'footsteps', 'majority', 'midnight')
C.TAIL_OVERRIDE = {'h1': 0.25, 'h2': 0.7, 's2': 0.5, 's5': 0.6, 's6': 0.8, 's8': 0.7, 's10': 0.8, 's11': 1.2, 'cta': 2.6}
BEATS = [(k, s, None, None, None, None, None) for k, s in (
    ('h1', "The baby monitor says the baby is asleep in his crib."),
    ('h2', "But you're holding the baby."),
    ('s1', "It's almost midnight. Your first night babysitting for the Carters. Noah is six months old, warm against your shoulder, finally quiet."),
    ('s2', "On your phone, the nursery camera shows a crib. And under the blanket... a small shape, breathing."),
    ('s3', "You text Mrs Carter: is there a second baby? She replies in seconds. No. Just Noah. Why?"),
    ('s4', "Then the app pings. Motion detected. In the nursery."),
    ('s5', "On the screen, the blanket slides down. The shape sits up. It is far too tall to be a baby."),
    ('s6', "Slowly, it turns its head toward the camera. Then the feed goes dark. Camera offline."),
    ('s7', "Upstairs, a floorboard creaks. Then your phone's speaker crackles."),
    ('s8', "A voice whispers, in Mrs Carter's voice: bring him up, sweetie. It's bedtime."),
    ('s9', "Your phone buzzes. It's Mrs Carter. We're still at dinner, twenty minutes away. Is everything okay?"),
    ('s10', "The nursery door opens. Slow footsteps cross the landing... and stop at the top of the stairs."),
    ('s11', "In your arms, Noah lifts his head, looks up into the dark... and smiles."),
    ('cta', "Go upstairs... or leave? Comment one word. The majority writes part two."))]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2')
bt, w = C.bt, C.w
OUT = (0.07, 0.06, 0.11)
SKIN, HAIR, HOOD, BLANKET = hexc('#F2C9A4')[:3], hexc('#5A3420')[:3], hexc('#E0A526')[:3], hexc('#9CC9F0')[:3]
YEL, RED, GREEN = hexc('#FFD23F')[:3], hexc('#FF4D4D')[:3], hexc('#3DDC84')[:3]

# ---------- primitives ----------
def ol(cr, lw=7):
    cr.set_source_rgb(*OUT); cr.set_line_width(lw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
def fo(cr, col, lw=7, a=1.0):
    cr.set_source_rgba(*col, a); cr.fill_preserve(); ol(cr, lw)
def ell(cr, x, y, rx, ry, rot=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(rx, ry); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
def cam(cr, z=1.0, tilt=0.0, fx=540, fy=960):
    cr.translate(540, 960); cr.rotate(tilt); cr.scale(z, z); cr.translate(-fx, -fy)
def vignette(cr, a=0.8):
    g = cairo.RadialGradient(540, 960, 420, 540, 960, 1250); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0.02, a); cr.set_source(g); cr.paint()
def shake(t, t0, amp=14, d=0.5):
    if t < t0: return 0.0, 0.0
    k = 1 - prog(t, t0, t0 + d); return amp * k * math.sin(t * 90), amp * k * math.cos(t * 77)

# ---------- characters ----------
def eyes(cr, x, y, gap, r, look, scared, blink=0.0):
    for sx in (-1, 1):
        rr_ = r * (1 + 0.35 * scared)
        ell(cr, x + sx * gap, y, rr_, rr_ * max(0.1, 1 - blink)); fo(cr, (1, 1, 1), 5)
        if blink < 0.6:
            cr.new_path(); cr.arc(x + sx * gap + look[0] * rr_ * 0.4, y + look[1] * rr_ * 0.4, rr_ * (0.5 - 0.15 * scared), 0, 2 * math.pi); cr.set_source_rgb(*OUT); cr.fill()

def baby_small(cr, x, y, s, awake=0.0):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    ell(cr, 10, 120, 100, 150, 0.1); fo(cr, BLANKET)
    cr.new_path(); cr.arc(0, 0, 66, 0, 2 * math.pi); fo(cr, SKIN)
    cr.new_path(); cr.move_to(-6, -64); cr.curve_to(4, -92, 26, -86, 14, -66); ol(cr, 6)
    if awake > 0.5: eyes(cr, 0, -4, 24, 11, (0.5, -0.9), 0.0)
    else:
        for sx in (-24, 24): cr.new_path(); cr.arc(sx, -4, 11, 0.15 * math.pi, 0.85 * math.pi); ol(cr, 5)
    cr.restore()

def sitter(cr, x, y, s, scared=0.0, look=(0, 0), blink=0.0, awake=0.0):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    ell(cr, 112, -300, 44, 86, 0.55); fo(cr, HAIR)  # ponytail
    rrect(cr, -160, -150, 320, 520, 100); fo(cr, HOOD)
    cr.new_path(); cr.move_to(-40, -150); cr.line_to(0, -96); cr.line_to(40, -150); ol(cr, 6)
    rrect(cr, -32, -175, 64, 50, 20); fo(cr, SKIN)
    cr.new_path(); cr.arc(0, -262, 112, 0, 2 * math.pi); fo(cr, SKIN)
    cr.new_path(); cr.arc(0, -272, 116, math.pi * 1.0, math.pi * 2.0); cr.curve_to(96, -246, 40, -330, -6, -286); cr.curve_to(-44, -246, -96, -262, -116, -272); cr.close_path(); fo(cr, HAIR)
    eyes(cr, 0, -246, 44, 22, look, scared, blink)
    for sx in (-1, 1):  # brows lift with fear
        cr.new_path(); cr.move_to(sx * 22, -290 - 14 * scared); cr.line_to(sx * 66, -284 - 26 * scared); ol(cr, 6)
    if scared > 0.4: ell(cr, 0, -188, 13 + 6 * scared, 10 + 12 * scared); fo(cr, (0.35, 0.1, 0.12), 5)
    else: cr.new_path(); cr.arc(0, -200, 22, 0.2 * math.pi, 0.8 * math.pi); ol(cr, 6)
    baby_small(cr, -92, -70, 1.0, awake)
    cr.new_path(); cr.move_to(150, 30); cr.curve_to(120, 190, -40, 210, -150, 130); cr.set_source_rgb(*HOOD); cr.set_line_width(74); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke_preserve()
    cr.set_source_rgba(*OUT, 0.0); cr.stroke()
    cr.new_path(); cr.move_to(150, -8); cr.curve_to(120, 152, -40, 172, -150, 92); ol(cr, 6)
    cr.new_path(); cr.move_to(150, 68); cr.curve_to(120, 228, -40, 248, -150, 168); ol(cr, 6)
    ell(cr, -156, 132, 40, 34); fo(cr, SKIN, 6)
    cr.restore()

def baby_close(cr, t, awake, smile):
    """Close-up of Noah on the hoodie."""
    cr.set_source_rgb(*[c * 0.55 for c in HOOD]); cr.paint()
    ell(cr, 540, 1840, 700, 520); fo(cr, BLANKET, 9)
    cr.new_path(); cr.arc(540, 980, 390, 0, 2 * math.pi); fo(cr, SKIN, 10)
    cr.new_path(); cr.move_to(510, 596); cr.curve_to(560, 470, 690, 500, 620, 600); ol(cr, 10)
    for sx in (-1, 1): ell(cr, 540 + sx * 250, 1090, 62, 40); cr.set_source_rgba(1, 0.55, 0.55, 0.45); cr.fill()
    if awake > 0:
        for sx in (-1, 1):
            ell(cr, 540 + sx * 150, 940, 78, 78 * max(0.12, awake)); fo(cr, (1, 1, 1), 8)
            if awake > 0.5:
                cr.new_path(); cr.arc(540 + sx * 150 + 14, 940 - 34, 40, 0, 2 * math.pi); cr.set_source_rgb(*OUT); cr.fill()
                cr.new_path(); cr.arc(540 + sx * 150 + 2, 940 - 50, 12, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill()
    else:
        for sx in (-1, 1): cr.new_path(); cr.arc(540 + sx * 150, 930, 66, 0.12 * math.pi, 0.88 * math.pi); ol(cr, 10)
    if smile > 0:
        cr.new_path(); cr.move_to(540 - 150 * smile, 1150); cr.curve_to(480, 1150 + 150 * smile, 600, 1150 + 150 * smile, 540 + 150 * smile, 1150); ol(cr, 12)
    else: cr.new_path(); cr.arc(540, 1160, 26, 0.15 * math.pi, 0.85 * math.pi); ol(cr, 9)

# ---------- sets ----------
def living_room(cr, t, dim=0.0):
    g = cairo.LinearGradient(0, 0, 0, 1300); g.add_color_stop_rgb(0, 0.13, 0.1, 0.22); g.add_color_stop_rgb(1, 0.2, 0.15, 0.3); cr.set_source(g); cr.paint()
    cr.rectangle(0, 1290, W, 630); cr.set_source_rgb(0.24, 0.15, 0.12); cr.fill()
    cr.rectangle(0, 1270, W, 26); cr.set_source_rgb(0.34, 0.3, 0.42); cr.fill_preserve(); ol(cr, 5)
    rrect(cr, 90, 330, 300, 380, 12); fo(cr, (0.07, 0.1, 0.2), 8)  # window, moon
    cr.new_path(); cr.arc(300, 440, 44, 0, 2 * math.pi); cr.set_source_rgb(0.9, 0.9, 0.8); cr.fill()
    cr.new_path(); cr.move_to(240, 330); cr.line_to(240, 710); cr.move_to(90, 520); cr.line_to(390, 520); ol(cr, 6)
    cr.new_path(); cr.arc(800, 420, 70, 0, 2 * math.pi); fo(cr, (0.92, 0.9, 0.84), 7)  # wall clock, just before midnight
    cr.new_path(); cr.move_to(800, 420); cr.line_to(796, 366); cr.move_to(800, 420); cr.line_to(778, 380); ol(cr, 6)
    g = cairo.RadialGradient(930, 900, 20, 930, 900, 560); g.add_color_stop_rgba(0, 1, 0.8, 0.4, 0.5); g.add_color_stop_rgba(1, 1, 0.8, 0.4, 0); cr.set_source(g); cr.paint()
    cr.new_path(); cr.move_to(930, 980); cr.line_to(930, 1290); ol(cr, 10)
    cr.new_path(); cr.move_to(860, 980); cr.line_to(1000, 980); cr.line_to(968, 840); cr.line_to(892, 840); cr.close_path(); fo(cr, (1.0, 0.86, 0.5))
    rrect(cr, 70, 1000, 760, 420, 70); fo(cr, (0.16, 0.36, 0.4), 8)  # sofa
    rrect(cr, 40, 1180, 820, 300, 60); fo(cr, (0.2, 0.44, 0.48), 8)
    if dim > 0: cr.set_source_rgba(0.02, 0.02, 0.06, 0.6 * dim); cr.paint()

def stairs(cr, t, door=0.0, fig=None, eyes_a=0.0):
    """Looking up the staircase. door 0..1 opens the nursery door; fig = x position of the figure on the landing."""
    cr.set_source_rgb(0.05, 0.04, 0.09); cr.paint()
    cr.new_path(); cr.move_to(0, 0); cr.line_to(W, 0); cr.line_to(W, 1920); cr.line_to(800, 620); cr.line_to(280, 620); cr.line_to(0, 1920); cr.close_path()
    cr.set_source_rgb(0.11, 0.09, 0.18); cr.fill()
    cr.rectangle(250, 150, 580, 480); cr.set_source_rgb(0.08, 0.07, 0.14); cr.fill_preserve(); ol(cr, 6)
    dx0, dw = 590, 190  # nursery door at the top right
    if door > 0:
        g = cairo.LinearGradient(dx0, 0, dx0 + dw, 0); g.add_color_stop_rgb(0, 0.75, 0.95, 0.7); g.add_color_stop_rgb(1, 0.4, 0.6, 0.45)
        cr.rectangle(dx0, 230, dw * door, 400); cr.set_source(g); cr.fill()
        cr.new_path(); cr.move_to(dx0, 630); cr.line_to(dx0 + dw * door, 630); cr.line_to(dx0 + dw * door - 260 * door, 900); cr.line_to(dx0 - 330 * door, 900); cr.close_path()
        cr.set_source_rgba(0.7, 0.95, 0.7, 0.16 * door); cr.fill()
    cr.rectangle(dx0 + dw * door, 230, dw * (1 - door), 400); cr.set_source_rgb(0.16, 0.13, 0.25); cr.fill()
    cr.rectangle(dx0, 230, dw, 400); ol(cr, 7)
    for i in range(12):  # steps, narrowing upward
        y = 1840 - i * 104; wd = 1060 - i * 46; sh = 0.16 - i * 0.008
        cr.rectangle(540 - wd / 2, y - 104, wd, 104); cr.set_source_rgb(sh + 0.05, sh, sh + 0.08); cr.fill_preserve(); ol(cr, 5)
        cr.rectangle(540 - wd / 2, y - 104, wd, 22); cr.set_source_rgb(sh + 0.12, sh + 0.06, sh + 0.14); cr.fill()
    cr.new_path(); cr.move_to(40, 1500); cr.line_to(296, 470); ol(cr, 16)
    for i in range(8): x = 60 + i * 30; cr.new_path(); cr.move_to(x, 1500 - i * 125 + 40); cr.line_to(x, 1700 - i * 125); ol(cr, 6)
    if fig is not None:
        cr.save(); cr.translate(fig, 0)
        cr.new_path(); cr.move_to(-46, 640); cr.curve_to(-70, 420, -40, 300, -26, 250); cr.line_to(26, 250); cr.curve_to(40, 300, 70, 420, 46, 640); cr.close_path(); cr.set_source_rgb(0.01, 0.01, 0.02); cr.fill()
        ell(cr, 0, 196, 44, 62); cr.fill()
        for sx in (-1, 1): cr.new_path(); cr.move_to(sx * 50, 300); cr.curve_to(sx * 96, 440, sx * 86, 560, sx * 78, 700); cr.set_line_width(20); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
        if eyes_a > 0:
            for sx in (-16, 16):
                cr.new_path(); cr.arc(sx, 190, 7, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, eyes_a); cr.fill()
        cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgba(0, 0, 0, 0.03, 0.75); g.add_color_stop_rgba(1, 0, 0, 0.03, 0); cr.rectangle(0, 0, W, 900); cr.set_source(g); cr.fill()

# ---------- phone ----------
PW, PH = 640, 1290
def phone(cr, t, screen, cx=540, cy=1010, tilt=0.0, s=1.0, clock='11:52'):
    cr.save(); cr.translate(cx, cy); cr.rotate(tilt); cr.scale(s, s); cr.translate(-PW / 2, -PH / 2)
    rrect(cr, -22, -22, PW + 44, PH + 44, 78); fo(cr, (0.1, 0.1, 0.14), 8)
    cr.save(); rrect(cr, 0, 0, PW, PH, 58); cr.clip()
    cr.set_source_rgb(0.06, 0.07, 0.11); cr.paint()
    screen(cr)
    ptext(cr, clock, 70, 52, 28, WHITE, 1, fam='Poppins SemiBold', sw=0, shadow=False)
    rrect(cr, PW - 110, 28, 56, 26, 8); cr.set_source_rgb(1, 1, 1); cr.set_line_width(3); cr.stroke(); rrect(cr, PW - 106, 32, 16, 18, 4); cr.set_source_rgb(*RED); cr.fill()
    rrect(cr, PW / 2 - 80, 18, 160, 40, 20); cr.set_source_rgb(0, 0, 0); cr.fill()
    cr.restore()
    for y in (PH * 0.56, PH * 0.66): ell(cr, -30, y, 40, 30); fo(cr, SKIN, 6)  # fingers
    cr.restore()

def feed(cr, t, x, y, wd, hh, slide=0.0, sit=0.0, turn=0.0, offline=0.0):
    """The nursery camera, in night vision."""
    cr.save(); cr.rectangle(x, y, wd, hh); cr.clip(); cr.translate(x, y)
    g = cairo.LinearGradient(0, 0, 0, hh); g.add_color_stop_rgb(0, 0.2, 0.27, 0.23); g.add_color_stop_rgb(1, 0.08, 0.11, 0.1); cr.set_source(g); cr.paint()
    mx = wd * 0.3 + 10 * math.sin(t * 1.3)  # the mobile above the crib
    cr.new_path(); cr.move_to(wd * 0.3, 0); cr.line_to(mx, hh * 0.2); cr.set_source_rgb(0.5, 0.6, 0.55); cr.set_line_width(3); cr.stroke()
    for i, dx in enumerate((-56, 0, 56)): cr.new_path(); cr.arc(mx + dx, hh * 0.2 + 26 + 8 * (i % 2), 15, 0, 2 * math.pi); cr.set_source_rgb(0.55, 0.66, 0.6); cr.fill()
    top, bot = hh * 0.52, hh * 0.86
    cr.rectangle(40, top - 40, wd - 80, bot - top + 40); cr.set_source_rgb(0.13, 0.17, 0.15); cr.fill()
    cr.rectangle(40, hh * 0.7, wd - 80, bot - hh * 0.7); cr.set_source_rgb(0.42, 0.5, 0.46); cr.fill()
    cxm, cym = wd * 0.5, hh * 0.69
    if sit > 0:  # the shape: far too tall
        hgt = sit * hh * 0.52
        cr.new_path(); cr.move_to(cxm - 52, cym + 20); cr.curve_to(cxm - 58, cym - hgt * 0.5, cxm - 30, cym - hgt * 0.85, cxm - 20, cym - hgt)
        cr.line_to(cxm + 20, cym - hgt); cr.curve_to(cxm + 30, cym - hgt * 0.85, cxm + 58, cym - hgt * 0.5, cxm + 52, cym + 20); cr.close_path(); cr.set_source_rgb(0.02, 0.03, 0.025); cr.fill()
        ell(cr, cxm, cym - hgt - 44, 40, 56); cr.fill()
        if turn > 0:
            for sx in (-1, 1):
                cr.new_path(); cr.arc(cxm + sx * 15 * turn, cym - hgt - 50, 6.5, 0, 2 * math.pi); cr.set_source_rgba(0.9, 1, 0.9, turn); cr.fill()
    ell(cr, cxm, cym + 6 + 70 * slide, 150 * (1 - 0.25 * slide), (56 + 5 * math.sin(t * 2.4)) * (1 - 0.6 * slide)); cr.set_source_rgb(0.62, 0.72, 0.67); cr.fill()
    for i in range(12):
        bx = 46 + i * (wd - 92) / 11; cr.rectangle(bx - 6, top, 12, bot - top); cr.set_source_rgb(0.3, 0.37, 0.34); cr.fill()
    for yy in (top - 14, bot - 6): rrect(cr, 34, yy, wd - 68, 22, 8); cr.set_source_rgb(0.36, 0.44, 0.4); cr.fill()
    for yy in range(0, int(hh), 6): cr.rectangle(0, yy, wd, 2); cr.set_source_rgba(0, 0, 0, 0.16); cr.fill()
    g = cairo.RadialGradient(wd / 2, hh / 2, hh * 0.25, wd / 2, hh / 2, hh * 0.75); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.7); cr.set_source(g); cr.paint()
    if offline > 0:
        rng = np.random.default_rng(int(t * 30))
        if offline < 1:
            for _ in range(260):
                cr.rectangle(rng.uniform(0, wd), rng.uniform(0, hh), rng.uniform(8, 90), rng.uniform(2, 8)); v = rng.uniform(0.2, 1); cr.set_source_rgba(v, v, v, 0.8); cr.fill()
        else:
            cr.set_source_rgb(0.03, 0.03, 0.05); cr.paint()
            ptext(cr, 'CAMERA OFFLINE', wd / 2, hh / 2 + 10, 48, RED, 0.6 + 0.4 * math.sin(t * 8), sw=0, shadow=False)
            ptext(cr, 'Reconnecting…', wd / 2, hh / 2 + 70, 28, (0.6, 0.6, 0.66), 1, fam='Poppins SemiBold', sw=0, shadow=False)
    else:
        if int(t * 2) % 2 == 0: cr.new_path(); cr.arc(34, 36, 10, 0, 2 * math.pi); cr.set_source_rgb(*RED); cr.fill()
        ptext(cr, 'LIVE', 54, 46, 26, WHITE, 1, anchor='l', sw=0, shadow=False)
        ptext(cr, 'NIGHT VISION', wd - 24, 46, 22, (0.7, 0.9, 0.78), 1, fam='Poppins SemiBold', anchor='r', sw=0, shadow=False)
    cr.restore()

def scr_cam(t, clock, **kw):
    def draw(cr):
        ptext(cr, 'NestView', PW / 2, 122, 40, WHITE, 1, sw=0, shadow=False)
        ptext(cr, 'Nursery · Noah', PW / 2, 164, 26, (0.6, 0.65, 0.75), 1, fam='Poppins SemiBold', sw=0, shadow=False)
        feed(cr, t, 0, 190, PW, 720, **kw)
        rrect(cr, 30, 940, PW - 60, 130, 30); cr.set_source_rgb(0.12, 0.14, 0.2); cr.fill()
        off = kw.get('offline', 0) >= 1; sitting = kw.get('sit', 0) > 0.2
        cr.new_path(); cr.arc(96, 1005, 34, 0, 2 * math.pi); cr.set_source_rgb(*(RED if (off or sitting) else GREEN)); cr.fill()
        ptext(cr, 'Noah', 150, 1000, 34, WHITE, 1, anchor='l', sw=0, shadow=False)
        ptext(cr, 'No signal' if off else ('Awake · moving' if sitting else 'Asleep · 2 h 14 min'), 150, 1040, 26, (0.65, 0.7, 0.8), 1, fam='Poppins SemiBold', anchor='l', sw=0, shadow=False)
        for i, lab in enumerate(('Talk', 'Listen', 'Lullaby')):
            rrect(cr, 30 + i * 198, 1100, 184, 84, 26); cr.set_source_rgb(0.16, 0.19, 0.27); cr.fill(); ptext(cr, lab, 122 + i * 198, 1152, 26, WHITE, 0.9, fam='Poppins SemiBold', sw=0, shadow=False)
    return draw

def bubble(cr, lines, y, mine, k=1.0, col=None):
    wd = max(tw(cr, l, 32, 'Poppins SemiBold') for l in lines) + 56; hh = 44 * len(lines) + 36; x = PW - 30 - wd if mine else 30
    cr.save(); cr.translate(x + (wd if mine else 0), y + hh); cr.scale(k, k); cr.translate(-(x + (wd if mine else 0)), -(y + hh))
    rrect(cr, x, y, wd, hh, 30); cr.set_source_rgb(*(col or ((0.2, 0.5, 1.0) if mine else (0.2, 0.22, 0.3)))); cr.fill()
    for i, l in enumerate(lines): ptext(cr, l, x + 28, y + 52 + i * 44, 32, WHITE, 1, fam='Poppins SemiBold', anchor='l', sw=0, shadow=False)
    cr.restore(); return hh

def scr_text(t, items, typing=None):
    """items: [(mine, lines, time shown)]"""
    def draw(cr):
        cr.new_path(); cr.arc(84, 132, 36, 0, 2 * math.pi); cr.set_source_rgb(0.55, 0.4, 0.75); cr.fill(); ptext(cr, 'C', 84, 146, 38, WHITE, 1, sw=0, shadow=False)
        ptext(cr, 'Mrs Carter', 140, 128, 36, WHITE, 1, anchor='l', sw=0, shadow=False)
        ptext(cr, 'Noah’s mom', 140, 164, 24, (0.6, 0.65, 0.75), 1, fam='Poppins SemiBold', anchor='l', sw=0, shadow=False)
        cr.rectangle(0, 196, PW, 2); cr.set_source_rgb(0.2, 0.22, 0.3); cr.fill()
        y = 250
        for mine, lines, ts in items:
            if t < ts: continue
            y += bubble(cr, lines, y, mine, pop_k(t, ts, 0.25)) + 26
        if typing and typing[0] <= t < typing[1]:
            rrect(cr, 30, y, 130, 70, 30); cr.set_source_rgb(0.2, 0.22, 0.3); cr.fill()
            for i in range(3): cr.new_path(); cr.arc(66 + i * 30, y + 35 - 8 * max(0, math.sin(t * 9 - i * 0.9)), 9, 0, 2 * math.pi); cr.set_source_rgb(0.7, 0.72, 0.8); cr.fill()
    return draw

def scr_lock(t, tb):
    def draw(cr):
        g = cairo.LinearGradient(0, 0, 0, PH); g.add_color_stop_rgb(0, 0.1, 0.1, 0.24); g.add_color_stop_rgb(1, 0.03, 0.04, 0.1); cr.set_source(g); cr.paint()
        ptext(cr, '11:53', PW / 2, 420, 170, WHITE, 1, fam='Poppins SemiBold', sw=0, shadow=False)
        ptext(cr, 'Friday', PW / 2, 480, 34, (0.75, 0.78, 0.9), 1, fam='Poppins SemiBold', sw=0, shadow=False)
        if t >= tb:
            k = ease_back(prog(t, tb, tb + 0.35), 2.2); y = lerp(-180, 560, k)
            rrect(cr, 26, y, PW - 52, 170, 36); cr.set_source_rgb(0.93, 0.94, 0.97); cr.fill()
            rrect(cr, 50, y + 28, 70, 70, 18); cr.set_source_rgb(*GREEN); cr.fill(); ptext(cr, 'N', 85, y + 80, 44, WHITE, 1, sw=0, shadow=False)
            ptext(cr, 'NESTVIEW', 140, y + 58, 24, (0.4, 0.42, 0.5), 1, anchor='l', sw=0, shadow=False); ptext(cr, 'now', PW - 56, y + 58, 24, (0.4, 0.42, 0.5), 1, fam='Poppins SemiBold', anchor='r', sw=0, shadow=False)
            ptext(cr, 'Motion detected', 140, y + 100, 36, (0.08, 0.08, 0.12), 1, anchor='l', sw=0, shadow=False)
            ptext(cr, 'Nursery · Noah’s crib', 140, y + 140, 28, (0.3, 0.32, 0.4), 1, fam='Poppins SemiBold', anchor='l', sw=0, shadow=False)
    return draw

def scr_audio(t, t0, tq):
    def draw(cr):
        ptext(cr, 'NestView', PW / 2, 122, 40, WHITE, 1, sw=0, shadow=False)
        ptext(cr, 'Nursery audio · LIVE', PW / 2, 164, 26, RED, 1, fam='Poppins SemiBold', sw=0, shadow=False)
        rng = np.random.default_rng(int(t * 14)); amp = (0.35 + 0.65 * (t >= tq)) * (t >= t0)
        for i in range(27):
            hh = (20 + 330 * amp * rng.random() * (0.4 + 0.6 * math.sin(i / 26 * math.pi))) if amp else 8
            rrect(cr, 44 + i * 20.6, 560 - hh / 2, 12, hh, 6); cr.set_source_rgb(*(RED if t >= tq else (0.5, 0.8, 1.0))); cr.fill()
        if t >= tq:
            k = pop_k(t, tq + 0.1, 0.3); cr.save(); cr.translate(PW / 2, 900); cr.scale(k, k)
            ptext(cr, '“bring him up,', 0, 0, 50, RED, 1, sw=0, shadow=False); ptext(cr, 'sweetie.”', 0, 66, 50, RED, 1, sw=0, shadow=False); cr.restore()
    return draw

# ---------- HUD ----------
def hud(cr, t):
    clock = '11:52 PM'
    for k, c in (('s4', '11:53 PM'), ('s7', '11:54 PM'), ('s10', '11:55 PM')):
        if t >= bt(k)['start']: clock = c
    ptext(cr, clock, 70, 196, 40, WHITE, 1, anchor='l', sw=6)
    ptext(cr, 'BABYSITTING: NOAH', 70, 240, 26, YEL, 1, fam='Poppins ExtraBold', anchor='l', sw=5)
    t3 = w('s5', 'tall'); n = 3 if t >= t3 else 2
    ptext(cr, 'IN THE HOUSE', 1010, 190, 26, WHITE, 1, fam='Poppins ExtraBold', anchor='r', sw=5)
    k = pop_k(t, t3, 0.4) if t >= t3 else 1.0
    cr.save(); cr.translate(984, 250); cr.scale(k, k); ptext(cr, str(n), 0, 0, 64, RED, 1, sw=7); cr.restore()
    if t >= bt('s9')['start']:
        ptext(cr, 'PARENTS: 20 MIN AWAY', 70, 280, 26, RED, pop_k(t, w('s9', 'twenty')) if t >= w('s9', 'twenty') else 0, fam='Poppins ExtraBold', anchor='l', sw=5)

# ---------- shots ----------
def shot(cr, t):
    def push(a, b, z0, z1): return lerp(z0, z1, ease_out(prog(t, a, b)))
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); k = b['key']; s, e = b['start'], b['end']
    cr.save()
    if k == 'h1':
        cam(cr, push(s, e, 1.0, 1.1), 0.0, 540, 900); cr.set_source_rgb(0.05, 0.05, 0.1); cr.paint(); phone(cr, t, scr_cam(t, '11:52'))
    elif k == 'h2':
        sx, sy = shake(t, w('h2', 'holding'), 16); cam(cr, push(s, e, 1.5, 1.75), -0.03, 540 + sx, 880 + sy); living_room(cr, t)
        sitter(cr, 500, 1240, 1.25, scared=ease_out(prog(t, w('h2', 'holding'), w('h2', 'holding') + 0.25)), look=(-0.6, 0.7))
    elif k == 's1':
        tn = w('s1', 'Noah')
        if t < tn: cam(cr, push(s, tn, 1.0, 1.08), 0.02); living_room(cr, t); sitter(cr, 500, 1240, 1.25, look=(0.2, 0.1), blink=1 if (t % 3.1) < 0.12 else 0)
        else: cam(cr, push(tn, e, 1.0, 1.1), -0.03, 540, 1000); baby_close(cr, t, 0, 0)
    elif k == 's2':
        tu = w('s2', 'under')
        if t < tu: cam(cr, push(s, tu, 1.0, 1.06), 0.05); living_room(cr, t, 1.0); phone(cr, t, scr_cam(t, '11:52'), tilt=-0.05)
        else: cam(cr, push(tu, e, 1.5, 1.68), 0.0, 540, 930); cr.set_source_rgb(0.05, 0.05, 0.1); cr.paint(); phone(cr, t, scr_cam(t, '11:52'))
    elif k == 's3':
        cam(cr, push(s, e, 1.02, 1.1), -0.02); cr.set_source_rgb(0.05, 0.05, 0.1); cr.paint()
        tr = w('s3', 'No')
        phone(cr, t, scr_text(t, [(True, ['is there a second', 'baby??'], w('s3', 'is')), (False, ['No. Just Noah.', 'Why?'], tr)], (w('s3', 'replies'), tr)))
    elif k == 's4':
        tp = w('s4', 'pings'); sx, sy = shake(t, tp, 12, 0.6)
        cam(cr, push(s, e, 1.0, 1.12), 0.03, 540 + sx, 960 + sy); living_room(cr, t, 1.0); phone(cr, t, scr_lock(t, tp), clock='')
    elif k == 's5':
        ts, tu = w('s5', 'slides'), w('s5', 'sits')
        cam(cr, push(s, e, 1.45, 1.66), 0.0, 540, 900); cr.set_source_rgb(0.05, 0.05, 0.1); cr.paint()
        phone(cr, t, scr_cam(t, '11:53', slide=ease_io(prog(t, ts, ts + 1.0)), sit=ease_io(prog(t, tu, tu + 1.6))))
    elif k == 's6':
        tt, td = w('s6', 'turns'), w('s6', 'dark')
        cam(cr, push(s, e, 1.6, 1.72), 0.02, 540, 880); cr.set_source_rgb(0.05, 0.05, 0.1); cr.paint()
        phone(cr, t, scr_cam(t, '11:53', slide=1, sit=1, turn=ease_io(prog(t, tt, tt + 1.2)), offline=0 if t < td else (0.5 if t < td + 0.35 else 1)))
    elif k == 's7':
        tc, tp = w('s7', 'creaks'), w('s7', 'phone')
        if t < tp: sx, sy = shake(t, tc, 10, 0.7); cam(cr, push(s, tp, 1.0, 1.12), -0.04, 540 + sx, 960 + sy); stairs(cr, t)
        else: cam(cr, push(tp, e, 1.0, 1.1), 0.04); cr.set_source_rgb(0.05, 0.05, 0.1); cr.paint(); phone(cr, t, scr_audio(t, w('s7', 'crackles'), 1e9), clock='11:54')
    elif k == 's8':
        tq, tb = w('s8', 'bring'), w('s8', 'bedtime')
        if t < tb: cam(cr, push(s, tb, 1.1, 1.3), 0.04, 540, 1000); cr.set_source_rgb(0.05, 0.05, 0.1); cr.paint(); phone(cr, t, scr_audio(t, s, tq), clock='11:54')
        else: cam(cr, push(tb, e, 2.1, 2.5), -0.05, 500, 900); living_room(cr, t, 0.6); sitter(cr, 500, 1240, 1.25, scared=1, look=(0.3, -0.9))
    elif k == 's9':
        cam(cr, push(s, e, 1.02, 1.1), 0.03); cr.set_source_rgb(0.05, 0.05, 0.1); cr.paint()
        sx, sy = shake(t, w('s9', 'buzzes'), 10, 0.5); cr.translate(sx, sy)
        items = [(True, ['is there a second', 'baby??'], 0), (False, ['No. Just Noah.', 'Why?'], 0), (False, ['We’re still at dinner', '20 min away'], w('s9', 'still') - 0.2), (False, ['Is everything ok?'], w('s9', 'everything') - 0.3)]
        phone(cr, t, scr_text(t, items), clock='11:54')
    elif k == 's10':
        to, tf, tst = w('s10', 'opens'), w('s10', 'footsteps'), w('s10', 'stop')
        step = min(4, int(max(0, t - tf) / max(0.01, (tst - tf) / 4))) if t >= tf else 0
        sx, sy = (0, 0) if t < tf else shake(t, tf + (step - 1) * (tst - tf) / 4 if step else tf, 9, 0.3)
        cam(cr, push(s, e, 1.0, 1.3), 0.03, 540 + sx, 640 + sy)
        stairs(cr, t, ease_io(prog(t, to, to + 1.2)), None if t < tf else lerp(690, 520, step / 4), ease_out(prog(t, tst, tst + 0.4)))
    elif k == 's11':
        tl, tsm = w('s11', 'lifts'), w('s11', 'smiles')
        cam(cr, push(s, e, 1.0, 1.16), -0.03, 540, 1000); baby_close(cr, t, ease_out(prog(t, tl, tl + 0.4)), ease_out(prog(t, tsm, tsm + 0.5)))
    else:
        cam(cr, push(s, e, 1.3, 1.42), 0.02, 540, 620); stairs(cr, t, 1.0, 520, 1.0)
    cr.restore()
    return k

def draw_cta(cr, t):
    b = bt('cta'); a = ease_out(prog(t, b['start'], b['start'] + 0.4))
    cr.set_source_rgba(0.01, 0.01, 0.04, 0.72 * a); cr.paint()
    cr.rectangle(537, 520, 6, 520); cr.set_source_rgba(1, 1, 1, a); cr.fill()
    tu, tl = w('cta', 'upstairs'), w('cta', 'leave')
    if t >= tu: k = pop_k(t, tu); cr.save(); cr.translate(280, 800); cr.rotate(-0.04); cr.scale(k, k); ptext(cr, 'UPSTAIRS', 0, 0, 92, YEL, 1, sw=12); emoji(cr, '⬆️', 0, -150, 110, 1); cr.restore()
    if t >= tl: k = pop_k(t, tl); cr.save(); cr.translate(800, 800); cr.rotate(0.04); cr.scale(k, k); ptext(cr, 'LEAVE', 0, 0, 108, WHITE, 1, sw=12); emoji(cr, '🚪', 0, -150, 110, 1); cr.restore()
    tc = w('cta', 'Comment')
    if t >= tc: k = pop_k(t, tc); cr.save(); cr.translate(540, 440); cr.scale(k, k); ptext(cr, 'COMMENT ONE WORD', 0, 0, 78, WHITE, 1, sw=11); cr.restore()
    tm = w('cta', 'majority')
    if t >= tm:
        k = pop_k(t, tm); cr.save(); cr.translate(540, 1150); cr.scale(k, k)
        rrect(cr, -400, -70, 800, 190, 30); cr.set_source_rgba(0.06, 0.06, 0.12, 0.95); cr.fill_preserve(); cr.set_source_rgb(*YEL); cr.set_line_width(4); cr.stroke()
        ptext(cr, 'THE MAJORITY WRITES PART 2', 0, 0, 44, YEL, 1, sw=0, shadow=False)
        prg = prog(t, tm, b['end'] - 0.5); rrect(cr, -340, 40, 680, 24, 12); cr.set_source_rgba(1, 1, 1, 0.15); cr.fill(); rrect(cr, -340, 40, max(24, 680 * prg), 24, 12); cr.set_source_rgb(*YEL); cr.fill(); cr.restore()
        k = pop_k(t, tm + 0.5) * (1 + 0.04 * math.sin(t * 6)) if t >= tm + 0.5 else 0
        if k: cr.save(); cr.translate(540, 1390); cr.scale(k, k); rrect(cr, -190, -56, 380, 104, 52); cr.set_source_rgb(*RED); cr.fill(); ptext(cr, 'FOLLOW', 0, 18, 56, WHITE, 1, sw=0, shadow=False); cr.restore()

def render_frame(cr, t):
    k = shot(cr, t)
    vignette(cr, 0.75)
    g = cairo.LinearGradient(0, 0, 0, 380); g.add_color_stop_rgba(0, 0, 0, 0.03, 0.8); g.add_color_stop_rgba(1, 0, 0, 0.03, 0); cr.rectangle(0, 0, W, 380); cr.set_source(g); cr.fill()
    if k == 'cta': draw_cta(cr, t)
    hud(cr, t)
    if k != 'cta' or t < w('cta', 'Comment'): C.draw_captions(cr, t, 1500)
    for key, word in (('s5', 'tall'), ('s6', 'dark'), ('s11', 'smiles')):
        tf = w(key, word); f = 1 - prog(t, tf, tf + 0.25)
        if t >= tf and f > 0: cr.set_source_rgba(0.9, 0.05, 0.1, 0.3 * f); cr.paint()
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- sound ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR; rng = np.random.default_rng(13)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    bed = 0.10 * np.sin(2 * np.pi * 55 * tt) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * tt)) + 0.07 * np.sin(2 * np.pi * 58.3 * tt)
    bed += 0.018 * np.sin(2 * np.pi * (880 + 6 * np.sin(2 * np.pi * 0.2 * tt)) * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * tt))
    bed += 0.02 * np.sin(2 * np.pi * 932 * tt) * np.clip((tt - bt('s5')['start']) / 20, 0, 1)
    fx = np.zeros(n)
    def thump(t0, amp=0.5, f0=60):
        L = np.arange(int(0.5 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(f0 + 60 * np.exp(-L * 25)) / SR) * np.exp(-L * 9))
    def boom(t0, amp=0.7):
        L = np.arange(int(2.2 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(32 + 70 * np.exp(-L * 9)) / SR) * np.exp(-L * 2.0))
    def sting(t0, amp=0.1):
        L = np.arange(int(2.5 * SR)) / SR; put(fx, t0, amp * sum(np.sin(2 * np.pi * f * L) for f in (311, 330, 466, 622)) * np.exp(-L * 1.4))
    def noise(t0, d, amp, smooth=1, env=None):
        z = rng.standard_normal(int(d * SR)); z = np.convolve(z, np.ones(smooth) / smooth, 'same') if smooth > 1 else z
        put(fx, t0, amp * z * (env if env is not None else np.sin(np.pi * np.linspace(0, 1, len(z)))))
    def creak(t0, d=1.1, amp=0.16):
        L = np.arange(int(d * SR)) / SR; f = 420 - 190 * L / d + 30 * np.sin(2 * np.pi * 7 * L)
        put(fx, t0, amp * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * L)) * np.sin(np.pi * L / d) * 0.5)
    def tone(t0, f, d, amp):
        L = np.arange(int(d * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * f * L) * np.exp(-L * 6))
    t0 = bt('s4')['start']  # a heartbeat that speeds up
    while t0 < bt('cta')['start']:
        thump(t0, 0.3); thump(t0 + 0.17, 0.2); t0 += lerp(0.95, 0.5, prog(t0, bt('s4')['start'], bt('s11')['start']))
    boom(w('h2', 'holding'), 0.8); sting(w('h2', 'holding'), 0.07)
    tp = w('s4', 'pings'); tone(tp, 1320, 0.5, 0.2); tone(tp + 0.14, 1760, 0.6, 0.2)
    boom(w('s5', 'tall'), 0.7); sting(w('s5', 'tall')); sting(w('s6', 'turns'), 0.06)
    noise(w('s6', 'dark'), 0.5, 0.35); boom(w('s6', 'dark') + 0.35, 0.6)
    creak(w('s7', 'creaks')); thump(w('s7', 'creaks') + 0.9, 0.4, 45)
    tc, te = w('s7', 'crackles'), bt('s8')['end']
    for _ in range(int((te - tc) * 22)): noise(tc + rng.uniform(0, te - tc), 0.012, rng.uniform(0.1, 0.3), env=1.0)
    tq = w('s8', 'bring'); noise(tq, w('s8', 'bedtime') - tq + 0.8, 0.12, smooth=6)
    boom(w('s8', 'bedtime'), 0.6)
    tb = w('s9', 'buzzes')
    for i in range(2):
        L = np.arange(int(0.35 * SR)) / SR; put(fx, tb + i * 0.5, 0.12 * np.sign(np.sin(2 * np.pi * 150 * L)) * np.minimum(1, (0.35 - L) * 20))
    creak(w('s10', 'opens'), 1.6, 0.18)
    tf, ts = w('s10', 'footsteps'), w('s10', 'stop')
    for i in range(4): thump(tf + (i + 1) * (ts - tf) / 4, 0.55, 48)
    boom(ts + 0.35, 0.8); sting(w('s11', 'smiles'), 0.14); boom(w('s11', 'smiles'), 0.9)
    L = np.arange(int(3.0 * SR)) / SR; put(fx, bt('cta')['start'] - 3.0, 0.06 * np.sin(2 * np.pi * np.cumsum(200 + 500 * (L / 3) ** 2) / SR) * (L / 3) ** 2)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.5 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = bed * duck * 1.4 + fx * (0.65 + 0.35 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(cache): C.TL = C.build(C.WordVoice(cache))

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        cr.identity_matrix(); render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    out = sys.argv[1]
    setup(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_sitter'))
    print(f"duration {C.TL['dur']:.1f}s")
    for b in C.TL['beats']: print(f"  {b['key']:5s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 2 and sys.argv[2] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[3].split(','): cr.identity_matrix(); render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]; make_audio(C.TL, base + '.wav')
    nfr = int(C.TL['dur'] * FPS); workers = os.cpu_count() or 4
    bounds_ = np.linspace(0, nfr, workers * 3 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds_[:-1], bounds_[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
