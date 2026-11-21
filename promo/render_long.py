"""Long cut (9:16, ~1.5 min) of How America Got Discovered, timed from the narration.
Reuses the drawing helpers in render_vertical.py; scene timing comes from voice_long.py's timings.json.
Usage: python3 render_long.py <land.geojson> <timings.json> <voice.wav> <out.mp4> [--preview t1,t2,...]
"""
import json, math, subprocess, sys, wave
import numpy as np
import cairo
import render_vertical as rv
from render_vertical import (W, H, FPS, hexc, clamp, lerp, ease_io, ease_out, ease_back, prog, window,
                             set_font, text_w, draw_text, wrap, Route, glow_dot, star, Proj,
                             BG0, BG1, GOLD, RED, CREAM, MUTED, TEAL, load_land, draw_background, draw_land)

VIOLET = hexc('#9AA8FF')

CARDS = {  # scene key -> eyebrow, title, body
    'bering': ('15,000+ YEARS AGO', 'The First Americans', 'Ice Age hunters cross a land bridge from Asia to Alaska.'),
    'empires': ('THOUSANDS OF YEARS', 'Great Civilizations Rise', 'The Maya, Aztec and Inca build cities, roads and empires.'),
    'vikings': ('c. 1000 AD', 'The Vikings Arrive', "Leif Erikson lands in 'Vinland', today's Newfoundland."),
    'columbus': (None, 'Columbus Crosses the Atlantic', 'Sailing for Spain, he lands in the Bahamas, sure it is Asia.'),
    'naming': ('1507', 'A New World Gets a Name', 'Waldseemüller\'s map names it after Amerigo Vespucci.'),
    'race': ('1497 – 1534', 'The Race for a New World', 'England, Spain and France send explorers west.'),
    'colonies': ('1607 – 1620', 'The First Colonies', 'Jamestown, Virginia, then the Pilgrims at Plymouth.'),
    'nation': ('JULY 4, 1776', 'A Nation Is Born', '13 colonies declare independence: the United States.'),
}
TIMELINE = ['15k ago', 'Empires', '1000', '1492', '1507', '1534', '1607', '1776']
CAMS = {  # scene key -> list of (offset into scene, lon, lat, zoom); negative offset counts from the end
    'title': [(0, -60, 25, 4.2), (-0.01, -62, 28, 4.8)],
    'bering': [(1.2, -168, 62, 11.0), ('L1', -160, 60, 11.6), ('L1+1.6', -105, 14, 5.8), (-0.01, -104, 12, 6.0)],
    'empires': [(1.2, -85, 13, 8.6), (-0.01, -85, 12, 9.2)],
    'vikings': [(1.2, -26, 59, 12.0), (-0.01, -28, 57, 12.8)],
    'columbus': [(1.2, -36, 30, 9.6), (-0.01, -37, 29, 10.2)],
    'naming': [(1.2, -82, 12, 5.6), (-0.01, -82, 12, 6.0)],
    'race': [(1.2, -40, 40, 8.6), (-0.01, -41, 39, 9.2)],
    'colonies': [(1.2, -74.2, 39.6, 22.0), (-0.01, -74, 39.6, 23.5)],
    'nation': [(1.2, -77, 36.5, 17.0), (-0.01, -76.5, 36.8, 18.5)],
    'outro': [(1.4, -72, 25, 4.6), (-0.01, -74, 26, 4.2)],
}

R_BERING = Route([(-200, 62), (-186, 65.5), (-170, 66), (-156, 64.5), (-142, 61), (-128, 56)])
R_SOUTH = Route([(-128, 56), (-121, 44), (-110, 30), (-97, 18), (-83, 8), (-77, -6), (-72, -25), (-71, -45), (-69, -53)])
R_EAST = Route([(-128, 56), (-112, 50), (-96, 43), (-82, 38)])
R_NORSE = Route([(6, 61), (-8, 63), (-21, 64.1), (-34, 63), (-46, 60.8), (-54, 56.5), (-55.5, 51.6)])
R_COLUMBUS = Route([(-6.9, 37.2), (-15.5, 28.1), (-34, 25.5), (-54, 24.6), (-74.5, 24.1)])
R_CABOT = Route([(-2.6, 51.45), (-20, 53.5), (-40, 51.5), (-53.1, 48.7)])
R_PONCE = Route([(-66.1, 18.4), (-72, 22.5), (-77.5, 26.5), (-81.3, 29.9)])
R_CARTIER = Route([(-2.0, 48.65), (-20, 50.5), (-42, 50.5), (-57, 49.5), (-64.5, 48.8)])
EMPIRES = [(-89.62, 17.22, 'MAYA', 'r'), (-99.13, 19.43, 'AZTECS', 'l'), (-71.97, -13.53, 'INCA', 'r'),
           (-90.06, 38.66, 'CAHOKIA', 'r')]
COLONIES = rv.COLONIES

class Story:
    def __init__(self, timings):
        self.dur = timings['duration']
        self.sc = {s['key']: s for s in timings['scenes']}
        self.order = [s['key'] for s in timings['scenes']]
        keys = []
        for s in timings['scenes']:
            for off, lon, lat, z in CAMS[s['key']]:
                keys.append((self.at(s['key'], off), lon, lat, z))
        rv.CAM_KEYS = sorted(keys)

    def at(self, key, off):
        s = self.sc[key]
        if isinstance(off, str):  # 'L1' or 'L1+1.6': relative to the end of line N (0-based)
            base, _, extra = off.partition('+')
            return s['lines'][int(base[1:]) - 1][1] + float(extra or 0)
        return s['start'] + off if off >= 0 else s['end'] + off

    def line(self, key, i):
        return self.sc[key]['lines'][i][:2]

    def span(self, key):
        return self.sc[key]['start'], self.sc[key]['end']

def pin(cr, pr, lon, lat, label, t, t0, color=GOLD, alpha=1.0, side='r', size=32):
    k = prog(t, t0, t0 + 0.45)
    if k <= 0 or alpha <= 0: return
    x, y = pr.xy(lon, lat)
    ring = prog(t, t0, t0 + 1.2)
    cr.new_path(); cr.set_source_rgba(*color[:3], (1 - ring) * 0.8 * alpha); cr.set_line_width(2)
    cr.arc(x, y, 8 + 34 * ease_out(ring), 0, 2 * math.pi); cr.stroke()
    glow_dot(cr, x, y, 8 * ease_back(k), color, alpha)
    if not label: return
    set_font(cr, size, bold=True)
    lk = ease_out(prog(t, t0 + 0.15, t0 + 0.6)); a = alpha * lk
    if side == 'b': draw_text(cr, label, x, y + 30 + size + (1 - lk) * 12, CREAM, a, 1, 'c')
    elif side == 't': draw_text(cr, label, x, y - 30 - (1 - lk) * 12, CREAM, a, 1, 'c')
    elif side == 'r': draw_text(cr, label, x + 22 + (1 - lk) * 12, y + size * 0.35, CREAM, a, 1, 'l')
    else: draw_text(cr, label, x - 22 - (1 - lk) * 12, y + size * 0.35, CREAM, a, 1, 'r')

def year_text(st, key, t):
    if key == 'columbus':
        a, _ = st.span(key)
        return str(int(round(lerp(1000, 1492, ease_out(prog(t, a + 0.1, a + 1.2))))))
    return CARDS[key][0]

def draw_panel(cr, st, t):
    for key in CARDS:
        a, b = st.span(key)
        al = window(t, a + 0.15, b + 0.1, 0.5, 0.4)
        if al <= 0: continue
        _, title, body = CARDS[key]
        x0, y0 = 80, 1430
        rise = (1 - ease_out(prog(t, a + 0.15, a + 0.85))) * 40
        g = cairo.LinearGradient(0, 1080, 0, H)
        g.add_color_stop_rgba(0, *BG1[:3], 0); g.add_color_stop_rgba(0.45, *BG1[:3], 0.82 * al)
        g.add_color_stop_rgba(1, *BG1[:3], 0.92 * al)
        cr.set_source(g); cr.rectangle(0, 1080, W, H - 1080); cr.fill()
        bk = ease_out(prog(t, a + 0.2, a + 0.75))
        cr.set_source_rgba(*GOLD[:3], al); cr.rectangle(x0, y0 - 104 + rise, 10, 300 * bk); cr.fill()
        yr = year_text(st, key, t); set_font(cr, 96, bold=True)
        if text_w(cr, yr, 2) > 900: set_font(cr, 96 * 900 / text_w(cr, yr, 2), bold=True)
        draw_text(cr, yr, x0 + 40, y0 - 20 + rise, GOLD, al, spacing=2)
        set_font(cr, 60, bold=True)
        tk = ease_out(prog(t, a + 0.3, a + 0.95))
        draw_text(cr, title, x0 + 40, y0 + 62 + rise + (1 - tk) * 30, CREAM, al * tk)
        set_font(cr, 38, bold=False, display=False)
        bkk = ease_out(prog(t, a + 0.5, a + 1.15))
        for j, line in enumerate(wrap(cr, body, 880)):
            draw_text(cr, line, x0 + 40, y0 + 132 + j * 52 + rise + (1 - bkk) * 30, MUTED, al * bkk)

def draw_timeline(cr, st, t):
    keys = list(CARDS)
    a0, b0 = st.span(keys[0])[0], st.span(keys[-1])[1]
    al = window(t, a0 - 0.2, b0 + 0.2, 0.6, 0.5)
    if al <= 0: return
    active = max([i for i, k in enumerate(keys) if t >= st.span(k)[0] - 0.2] or [0])
    x0, x1, y = 110, 970, 1790
    xs = [lerp(x0, x1, i / (len(TIMELINE) - 1)) for i in range(len(TIMELINE))]
    cr.new_path(); cr.set_line_width(2); cr.set_source_rgba(*MUTED[:3], 0.35 * al)
    cr.move_to(x0, y); cr.line_to(x1, y); cr.stroke()
    a = st.span(keys[active])[0]
    px = lerp(xs[max(active - 1, 0)], xs[active], ease_io(prog(t, a - 0.2, a + 0.4)))
    cr.set_source_rgba(*GOLD[:3], al); cr.set_line_width(3)
    cr.move_to(x0, y); cr.line_to(px, y); cr.stroke()
    set_font(cr, 22, bold=True, display=False)
    for i, (x, lab) in enumerate(zip(xs, TIMELINE)):
        on = i <= active
        cr.new_path(); cr.set_source_rgba(*(GOLD if on else MUTED)[:3], al * (1 if on else 0.5))
        cr.arc(x, y, 9 if i == active else 6, 0, 2 * math.pi); cr.fill()
        draw_text(cr, lab, x, y - 26, CREAM if i == active else MUTED, al * (1 if i == active else 0.6), anchor='c')

def draw_title(cr, st, t):
    a, b = st.span('title')
    al = window(t, 0.0, b + 0.1, 0.3, 0.6)
    if al <= 0: return
    cr.set_source_rgba(*BG1[:3], 0.55 * al); cr.paint()
    set_font(cr, 34, bold=True)
    k = ease_out(prog(t, 0.2, 0.9))
    draw_text(cr, 'THE STORY OF HOW', W / 2, 700 + (1 - k) * 20, GOLD, al * k, spacing=10, anchor='c')
    set_font(cr, 150, bold=True)
    for li, line in enumerate(['AMERICA', 'WAS', 'DISCOVERED']):
        x = W / 2 - text_w(cr, line, 4) / 2
        for ci, ch in enumerate(line):
            ck = prog(t, 0.45 + li * 0.25 + ci * 0.035, 0.95 + li * 0.25 + ci * 0.035)
            cr.set_source_rgba(*CREAM[:3], al * clamp(ck * 2))
            cr.move_to(x, 880 + li * 160 + (1 - ease_back(ck)) * 80); cr.show_text(ch)
            x += cr.text_extents(ch).x_advance + 4
    lk = ease_io(prog(t, 1.5, 2.3))
    cr.set_source_rgba(*GOLD[:3], al); cr.rectangle(W / 2 - 220 * lk, 1260, 440 * lk, 8); cr.fill()
    l1 = st.line('title', 1)[0]
    set_font(cr, 40, bold=False, display=False)
    for j, s in enumerate(['A lot more interesting', 'than one name.']):
        k2 = ease_out(prog(t, l1 + j * 0.25, l1 + 0.6 + j * 0.25))
        draw_text(cr, s, W / 2, 1350 + j * 54 + (1 - k2) * 16, MUTED, al * k2, anchor='c')

def draw_outro(cr, st, t):
    a, b = st.span('outro')
    (l0, _), (l1, l1e), (l2, _) = st.line('outro', 0), st.line('outro', 1), st.line('outro', 2)
    al = ease_out(prog(t, a, a + 0.6))
    if al <= 0: return
    cr.set_source_rgba(*BG1[:3], 0.62 * al); cr.paint()
    set_font(cr, 50, bold=True)
    k0 = ease_out(prog(t, l0, l0 + 0.5)) * (1 - ease_io(prog(t, l1 - 0.2, l1 + 0.2)) * 0.6)
    draw_text(cr, 'So, who discovered America?', W / 2, 640 + (1 - k0) * 20, GOLD, k0, anchor='c')
    set_font(cr, 96, bold=True)
    k = ease_out(prog(t, l1, l1 + 0.6))
    draw_text(cr, 'Not discovered', W / 2, 820 + (1 - k) * 30, CREAM, k, anchor='c')
    draw_text(cr, 'once.', W / 2, 930 + (1 - k) * 30, CREAM, k, anchor='c')
    mid = lerp(l1, l1e, 0.55)
    k2 = ease_out(prog(t, mid, mid + 0.6))
    draw_text(cr, 'Again and', W / 2, 1080 + (1 - k2) * 30, GOLD, k2, anchor='c')
    draw_text(cr, 'again.', W / 2, 1190 + (1 - k2) * 30, GOLD, k2, anchor='c')
    k3 = ease_out(prog(t, l2, l2 + 0.6))
    set_font(cr, 40, bold=False, display=False)
    draw_text(cr, 'Its first peoples were here all along.', W / 2, 1310, MUTED, k3, anchor='c')

def draw_america_stamp(cr, pr, st, t):
    l1, l1e = st.line('naming', 1)
    t0 = l1e - 0.75
    _, b = st.span('naming')
    al = window(t, t0, b + 0.2, 0.25, 0.5)
    if al <= 0: return
    x, y = pr.xy(-84, 20)
    s = lerp(1.6, 1.0, ease_out(prog(t, t0, t0 + 0.35)))
    cr.save(); cr.translate(x, y); cr.rotate(-0.06); cr.scale(s, s)
    set_font(cr, 104, bold=True)
    w = text_w(cr, 'AMERICA', 14)
    cr.set_source_rgba(*BG1[:3], 0.5 * al); cr.rectangle(-w / 2 - 40, -125, w + 80, 165); cr.fill()
    cr.set_source_rgba(*GOLD[:3], al); cr.set_line_width(5); cr.rectangle(-w / 2 - 40, -125, w + 80, 165); cr.stroke()
    draw_text(cr, 'AMERICA', 0, 0, GOLD, al, spacing=14, anchor='c')
    cr.restore()
    flash = 1 - prog(t, t0 + 0.3, t0 + 0.8)
    if 0 < flash < 1: cr.set_source_rgba(*GOLD[:3], 0.25 * flash); cr.paint()

def render_frame(cr, st, t, polys):
    pr = Proj(t)
    draw_background(cr, pr)
    nt0 = st.line('naming', 1)[1] - 0.75
    draw_land(cr, pr, polys, ease_io(prog(t, nt0, nt0 + 0.7)) * (1 - ease_io(prog(t, st.span('naming')[1] - 0.5, st.span('naming')[1] + 0.4))))

    # First Americans
    a, b = st.span('bering'); al = window(t, a + 0.4, b + 0.3, 0.4, 0.6)
    (l0, l0e), (l1, l1e) = st.line('bering', 0), st.line('bering', 1)
    R_BERING.draw(cr, pr, ease_io(prog(t, l0 + 1.0, l0e)), TEAL, al)
    R_SOUTH.draw(cr, pr, ease_io(prog(t, l1 + 0.6, l1e)), TEAL, al)
    R_EAST.draw(cr, pr, ease_io(prog(t, l1 + 0.9, l1e - 0.5)), TEAL, al)
    pin(cr, pr, -200, 62, 'ASIA', t, a + 1.0, TEAL, al, side='b')
    pin(cr, pr, -168, 65.8, 'LAND BRIDGE', t, l0 + 2.5, TEAL, al)
    pin(cr, pr, -150, 64, 'ALASKA', t, l0e - 1.2, TEAL, al, side='b')

    # Civilizations
    a, b = st.span('empires'); al = window(t, a + 0.4, b + 0.3, 0.4, 0.6)
    l1, l1e = st.line('empires', 1)
    for i, (lon, lat, name, side) in enumerate(EMPIRES):
        pin(cr, pr, lon, lat, name, t, lerp(l1, l1e, i / 4) + 0.1, GOLD if i < 3 else TEAL, al, side=side)

    # Vikings
    a, b = st.span('vikings'); al = window(t, a + 0.4, b + 0.3, 0.4, 0.6)
    (l0, l0e), (l1, l1e) = st.line('vikings', 0), st.line('vikings', 1)
    R_NORSE.draw(cr, pr, ease_io(prog(t, l0 + 0.3, l1e - 0.6)), RED, al, head='ship')
    pin(cr, pr, 6, 61, 'NORWAY', t, l0, RED, al, side='b')
    pin(cr, pr, -21, 64.1, 'ICELAND', t, lerp(l0, l0e, 0.45), RED, al)
    pin(cr, pr, -46, 60.8, 'GREENLAND', t, l0e - 1.0, RED, al)
    pin(cr, pr, -55.5, 51.6, 'VINLAND', t, l1e - 0.6, GOLD, al)

    # Columbus
    a, b = st.span('columbus'); al = window(t, a + 0.4, b + 0.3, 0.4, 0.6)
    (l0, l0e), (l1, l1e) = st.line('columbus', 0), st.line('columbus', 1)
    R_COLUMBUS.draw(cr, pr, ease_io(prog(t, l0 + 2.0, l1 + 2.2)), GOLD, al, head='ship')
    pin(cr, pr, -6.9, 37.2, 'SPAIN', t, l0 + 1.2, GOLD, al)
    pin(cr, pr, -15.5, 28.1, 'CANARY ISLANDS', t, l0 + 3.2, GOLD, al, side='b')
    pin(cr, pr, -74.5, 24.1, 'THE BAHAMAS', t, l1 + 2.2, RED, al, side='b')

    draw_america_stamp(cr, pr, st, t)

    # Race for the New World
    a, b = st.span('race'); al = window(t, a + 0.4, b + 0.3, 0.4, 0.6)
    for i, (route, color, src, dst) in enumerate([
            (R_CABOT, RED, (-2.6, 51.45, 'ENGLAND', 'r'), (-53.1, 48.7, 'CABOT 1497', 't')),
            (R_PONCE, GOLD, (-66.1, 18.4, 'PUERTO RICO', 'r'), (-81.3, 29.9, 'PONCE DE LEÓN 1513', 't')),
            (R_CARTIER, VIOLET, (-2.0, 48.65, 'FRANCE', 'b'), (-64.5, 48.8, 'CARTIER 1534', 'b'))]):
        s0, s1 = st.line('race', i + 1)
        dur = max(1.6, s1 - s0 + 0.4)
        route.draw(cr, pr, ease_io(prog(t, s0 - 0.1, s0 - 0.1 + dur)), color, al, head='ship')
        pin(cr, pr, *src[:2], src[2], t, s0 - 0.2, color, al, side=src[3], size=28)
        pin(cr, pr, *dst[:2], dst[2], t, s0 - 0.1 + dur, color, al, side=dst[3], size=28)

    # First colonies
    a, b = st.span('colonies'); al = window(t, a + 0.4, b + 0.3, 0.4, 0.6)
    (l0, l0e), (l1, l1e) = st.line('colonies', 0), st.line('colonies', 1)
    pin(cr, pr, -76.78, 37.21, 'JAMESTOWN 1607', t, l0 + 1.6, GOLD, al, side='l')
    pin(cr, pr, -70.66, 41.96, 'PLYMOUTH 1620', t, l1 + 1.4, RED, al, side='b')

    # Nation
    a, b = st.span('nation'); al = window(t, a + 0.3, b + 0.6, 0.3, 0.6)
    l0, l0e = st.line('nation', 0)
    for i, (lon, lat) in enumerate(COLONIES):
        k = prog(t, l0 + 2.4 + i * 0.09, l0 + 2.7 + i * 0.09)
        if k > 0:
            x, y = pr.xy(lon, lat)
            star(cr, x, y, 16 * ease_back(k), CREAM, al)
    if al > 0:
        set_font(cr, 34, bold=True)
        x, y = pr.xy(-71, 40.2)
        draw_text(cr, '13 COLONIES', x + 20, y, CREAM, al * ease_out(prog(t, l0 + 3.6, l0 + 4.1)), spacing=2)
        l1, l1e = st.line('nation', 1)
        k = ease_out(prog(t, l1 + 0.2, l1 + 0.7))
        set_font(cr, 72, bold=True)
        draw_text(cr, 'UNITED STATES', W / 2, 330 + (1 - k) * 30, GOLD, al * k, spacing=6, anchor='c')
        flash = 1 - prog(t, l1 + 0.2, l1 + 0.8)
        if 0 < flash < 1: cr.set_source_rgba(*GOLD[:3], 0.2 * flash * al); cr.paint()

    draw_panel(cr, st, t)
    draw_timeline(cr, st, t)
    draw_title(cr, st, t)
    draw_outro(cr, st, t)
    f = prog(t, st.dur - 0.5, st.dur)
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

def make_audio(path, st, voice_path, sr=48000):
    dur = st.dur
    n = int(sr * dur); tt = np.arange(n) / sr
    out = np.zeros(n)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    chords = [[57, 64, 69, 72], [53, 60, 65, 69], [48, 55, 64, 67], [55, 62, 67, 71]]  # Am F C G
    seg = 3.75
    for ci in range(int(dur / seg) + 1):
        ch = chords[ci % 4]; t0 = ci * seg
        i0, i1 = int(t0 * sr), min(n, int((t0 + seg + 1.0) * sr))
        if i0 >= n: break
        lt = tt[i0:i1] - t0
        env = np.minimum(1, lt / 0.6) * np.exp(-np.maximum(0, lt - seg) * 3)
        for m in ch:
            f = note(m)
            out[i0:i1] += env * 0.05 * (np.sin(2*np.pi*f*lt) + 0.5*np.sin(2*np.pi*f*1.003*lt)
                                        + 0.25*np.sin(2*np.pi*2*f*lt))
        out[i0:i1] += env * 0.09 * np.sin(2 * np.pi * note(ch[0] - 12) * lt)
    rng = np.random.default_rng(1)
    beat = 0.5
    o0, o1 = st.span('title')[1], st.span('outro')[0]
    for bt in np.arange(o0, o1, beat):
        i0 = int(bt * sr); L = int(0.35 * sr); lt = np.arange(L) / sr
        f = 50 + 70 * np.exp(-lt * 30)
        out[i0:i0 + L] += 0.32 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-lt * 9)
        j0 = int((bt + beat / 2) * sr); M = int(0.06 * sr)
        out[j0:j0 + M] += 0.03 * np.diff(rng.standard_normal(M + 1)) * np.exp(-np.arange(M) / sr * 60)
    for key in st.order[1:]:
        wt = st.span(key)[0]
        L = int(1.0 * sr); i0 = int((wt - 0.5) * sr)
        nz = rng.standard_normal(L); lt = np.arange(L) / L
        y = np.zeros(L); a = 0.0
        for j in range(L):
            c = 0.02 + 0.25 * math.sin(math.pi * lt[j])
            a += c * (nz[j] - a); y[j] = a
        out[i0:i0 + L] += 0.35 * y * np.sin(np.pi * lt) ** 2
    for it in [0.5, st.line('naming', 1)[1] - 0.7, st.line('nation', 1)[0] + 0.2, st.line('outro', 1)[0]]:
        i0 = int(it * sr); L = min(int(1.5 * sr), n - i0); lt = np.arange(L) / sr
        f = 40 + 90 * np.exp(-lt * 12)
        out[i0:i0 + L] += 0.5 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-lt * 3)
        out[i0:i0 + L] += 0.08 * rng.standard_normal(L) * np.exp(-lt * 18)
    out *= np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 1.5)
    with wave.open(voice_path) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float) / 32767
    v = np.pad(v, (0, max(0, n - len(v))))[:n]
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = 1 - 0.65 * np.clip(env / 0.03, 0, 1)
    duck = np.convolve(duck, np.ones(9600) / 9600, mode='same')
    mix = np.tanh(out * 1.2) * 0.55 * duck + 0.95 * v
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    st2 = np.column_stack([mix, mix])
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(st2, -1, 1) * 32767).astype('<i2').tobytes())

def main():
    land, timings, voice, out = sys.argv[1:5]
    st = Story(json.load(open(timings)))
    polys = load_land(land)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    if len(sys.argv) > 5 and sys.argv[5] == '--preview':
        for ts in sys.argv[6].split(','):
            render_frame(cr, st, float(ts), polys); surf.write_to_png(f'{out}_{ts}.png')
        return
    wav = out.rsplit('.', 1)[0] + '.wav'
    make_audio(wav, st, voice)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                          stdin=subprocess.PIPE)
    for i in range(int(st.dur * FPS)):
        render_frame(cr, st, i / FPS, polys); surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait()

if __name__ == '__main__':
    main()
