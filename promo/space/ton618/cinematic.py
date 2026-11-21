"""Cinematic space-fact reel (9:16): a slow push toward the black hole TON 618 with minimal type, no voiceover.
Made to sit under a trending track added in the Facebook/Instagram editor. Writes a silent master and an
ambient-score fallback.
Usage: python3 cinematic.py <out_base> [--preview t1,t2,...]
"""
import math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
from quiz import clamp, lerp, prog, ease_io, ease_out, SR

W, H, FPS = 1080, 1920, 30
CX, CY = 540, 860
WARM = (1.0, 0.93, 0.82)
GOLDW = (1.0, 0.8, 0.5)

# (start, end, lines): each line is (text, size, weight, colour)
CARDS = [
    (0.4, 4.6, [("One of the biggest", 58, 'Poppins Light', WARM), ("black holes ever found", 58, 'Poppins Light', WARM)]),
    (4.9, 8.9, [("TON 618", 150, 'Poppins SemiBold', WARM)]),
    (9.2, 13.4, [("It weighs about", 54, 'Poppins Light', WARM), ("40 billion suns", 96, 'Poppins SemiBold', GOLDW)]),
    (13.7, 18.6, [("Our entire solar system", 54, 'Poppins Light', WARM), ("could line up across its edge", 54, 'Poppins Light', WARM),
                  ("20+ times", 104, 'Poppins SemiBold', GOLDW)]),
    (18.9, 23.4, [("Its light left", 54, 'Poppins Light', WARM), ("10.8 billion years ago", 84, 'Poppins SemiBold', GOLDW)]),
    (23.7, 28.2, [("before the Earth", 64, 'Poppins Light', WARM), ("even existed.", 64, 'Poppins Light', WARM)]),
]
DUR = 30.5
END_CARD = 28.4

rng0 = np.random.default_rng(7)
STARS = [(rng0.uniform(-200, W + 200), rng0.uniform(-200, H + 200), rng0.uniform(0.4, 2.4), rng0.uniform(0, 6.28), rng0.uniform(0.3, 1.2), rng0.uniform(0.2, 1.0))
         for _ in range(520)]
# turbulence texture for the disk: random phases per ring
NR = 70
PH = rng0.uniform(0, 6.28, (NR, 4)); KK = rng0.integers(3, 11, (NR, 4))

def zoom(t): return lerp(0.82, 1.22, ease_io(prog(t, 0, DUR)))

def draw_stars(cr, t, z):
    cr.set_source_rgb(0.005, 0.005, 0.015); cr.paint()
    for cx, cy, r, col, a in ((300, 450, 900, (0.25, 0.08, 0.35), 0.35), (800, 1500, 1000, (0.05, 0.12, 0.3), 0.35)):
        g = cairo.RadialGradient(cx, cy, 0, cx, cy, r); g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
        cr.set_source(g); cr.paint()
    for x, y, r, ph, sp, depth in STARS:
        # parallax: deeper stars move less with the push-in; stars near the hole get pulled into a lensing arc
        sx = CX + (x - CX) * (1 + (z - 1) * depth) + t * 3 * depth
        sy = CY + (y - CY) * (1 + (z - 1) * depth)
        dx, dy = sx - CX, sy - CY; d = math.hypot(dx, dy) + 1e-6
        rs = 178 * z
        if d < rs * 1.15: continue
        push = (rs * 2.2) ** 2 / d  # Einstein-ring-ish displacement
        sx, sy = sx + dx / d * push * 0.35, sy + dy / d * push * 0.35
        a = 0.35 + 0.55 * (0.5 + 0.5 * math.sin(t * sp + ph))
        cr.new_path(); cr.arc(sx, sy, r, 0, 2 * math.pi); cr.set_source_rgba(1, 0.97, 0.92, a); cr.fill()

def disk_color(f):
    """f: 0 inner -> 1 outer"""
    if f < 0.25: return lerp(1.0, 1.0, f / 0.25), lerp(0.98, 0.85, f / 0.25), lerp(0.9, 0.55, f / 0.25)
    if f < 0.6: k = (f - 0.25) / 0.35; return 1.0, lerp(0.85, 0.5, k), lerp(0.55, 0.15, k)
    k = (f - 0.6) / 0.4; return lerp(1.0, 0.7, k), lerp(0.5, 0.15, k), lerp(0.15, 0.05, k)

def draw_disk_half(cr, t, rs, front, tilt=0.2):
    cr.save(); cr.set_operator(cairo.OPERATOR_ADD)
    segs = 90
    for i in range(NR):
        f = i / (NR - 1)
        r = rs * lerp(1.65, 4.6, f ** 0.9)
        omega = 0.9 / (0.4 + f) ** 1.5
        col = disk_color(f)
        base_a = 0.16 * (1 - f) ** 1.3 + 0.018
        lw = rs * 0.075
        a0, a1 = (0.0, math.pi) if front else (math.pi, 2 * math.pi)
        for s in range(segs):
            ang = lerp(a0, a1, (s + 0.5) / segs)
            turb = 0.55 + 0.45 * sum(math.sin(KK[i, j] * ang + PH[i, j] + t * omega * (1 + j * 0.3)) for j in range(4)) / 4
            dop = 1 + 0.75 * math.cos(ang)  # the side moving toward us is brighter
            a = base_a * turb * dop
            if a <= 0.003: continue
            cr.new_path()
            cr.save(); cr.translate(CX, CY); cr.scale(1, tilt)
            cr.arc(0, 0, r, lerp(a0, a1, s / segs), lerp(a0, a1, (s + 1) / segs)); cr.restore()
            cr.set_source_rgba(*col, a); cr.set_line_width(lw); cr.stroke()
    cr.restore()

def draw_lensed_ring(cr, t, rs):
    """The far side of the disk, bent over and under the shadow by gravity."""
    cr.save(); cr.set_operator(cairo.OPERATOR_ADD)
    for k in range(26):
        f = k / 25
        r = rs * lerp(1.08, 1.75, f)
        col = disk_color(f * 0.8)
        segs = 180
        for s in range(segs):
            ang = 2 * math.pi * s / segs
            band = abs(math.sin(ang)) ** 0.8  # thick over the top and bottom
            flick = 0.85 + 0.15 * math.sin(3 * ang + t * 1.3 + k)
            dop = 1 + 0.5 * math.cos(ang)
            a = 0.09 * (1 - f) ** 1.6 * (0.25 + band) * flick * dop
            cr.new_path(); cr.arc(CX, CY, r, ang, ang + 2 * math.pi / segs)
            cr.set_source_rgba(*col, a); cr.set_line_width(rs * 0.06); cr.stroke()
    cr.restore()

def draw_black_hole(cr, t):
    z = zoom(t); rs = 178 * z
    g = cairo.RadialGradient(CX, CY, rs, CX, CY, rs * 6)  # warm haze
    g.add_color_stop_rgba(0, 1, 0.6, 0.25, 0.22); g.add_color_stop_rgba(1, 1, 0.5, 0.2, 0)
    cr.set_source(g); cr.paint()
    draw_disk_half(cr, t, rs, front=False)
    draw_lensed_ring(cr, t, rs)
    g = cairo.RadialGradient(CX, CY, rs * 0.9, CX, CY, rs * 1.08)  # shadow with a soft edge
    g.add_color_stop_rgba(0, 0, 0, 0, 1); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    cr.set_source(g); cr.arc(CX, CY, rs * 1.08, 0, 2 * math.pi); cr.fill()
    cr.save(); cr.set_operator(cairo.OPERATOR_ADD)  # photon ring
    cr.new_path(); cr.arc(CX, CY, rs * 1.04, 0, 2 * math.pi); cr.set_source_rgba(1, 0.9, 0.7, 0.55); cr.set_line_width(rs * 0.025); cr.stroke()
    cr.new_path(); cr.arc(CX, CY, rs * 1.04, 0, 2 * math.pi); cr.set_source_rgba(1, 0.8, 0.5, 0.15); cr.set_line_width(rs * 0.1); cr.stroke()
    cr.restore()
    draw_disk_half(cr, t, rs, front=True)
    rng = np.random.default_rng(11)  # in-falling sparks
    cr.save(); cr.set_operator(cairo.OPERATOR_ADD)
    for i in range(70):
        r0 = rng.uniform(2.0, 5.5); ph = rng.uniform(0, 6.28); sp = rng.uniform(0.15, 0.35)
        u = (t * sp + rng.uniform(0, 1)) % 1.0
        r = rs * lerp(r0, 1.7, u ** 1.5); ang = ph + u * 4.0
        x = CX + r * math.cos(ang); y = CY + r * math.sin(ang) * 0.2
        cr.new_path(); cr.arc(x, y, 1.6 + 1.5 * u, 0, 2 * math.pi); cr.set_source_rgba(1, 0.75, 0.45, 0.5 * math.sin(math.pi * u)); cr.fill()
    cr.restore()

def tracked(cr, txt, x, y, size, fam, col, a, spacing, glow=True):
    cr.select_font_face(fam); cr.set_font_size(size)
    widths = [cr.text_extents(ch).x_advance for ch in txt]
    total = sum(widths) + spacing * (len(txt) - 1); x0 = x - total / 2
    for pass_, (al, off) in enumerate(((0.18, 3), (1.0, 0)) if glow else ((1.0, 0),)):
        xx = x0
        for ch, wd in zip(txt, widths):
            if pass_ == 0:
                for dx, dy in ((-off, 0), (off, 0), (0, -off), (0, off)):
                    cr.move_to(xx + dx, y + dy); cr.set_source_rgba(*col, a * al * 0.5); cr.show_text(ch)
            else:
                cr.move_to(xx, y); cr.set_source_rgba(*col, a); cr.show_text(ch)
            xx += wd + spacing

def draw_text(cr, t):
    for t0, t1, lines in CARDS:
        if not (t0 <= t <= t1): continue
        ys, y = [], 0.0
        for i, (_, size, _, _) in enumerate(lines):
            if i: y += lines[i - 1][1] * 0.42 + size * 0.98
            ys.append(y)
        y0 = 1450 - (ys[-1] + lines[-1][1] * 0.3 - lines[0][1] * 0.7) / 2
        for i, (txt, size, fam, col) in enumerate(lines):
            y = y0 + ys[i]
            li0 = t0 + i * 0.45
            a = ease_out(prog(t, li0, li0 + 0.9)) * (1 - ease_io(prog(t, t1 - 0.7, t1)))
            spacing = lerp(14, 3, ease_out(prog(t, li0, li0 + 1.6)))
            dy = (1 - ease_out(prog(t, li0, li0 + 1.2))) * 18
            if a > 0: tracked(cr, txt, 540, y + dy, size, fam, col, a, spacing)
    a = ease_out(prog(t, END_CARD, END_CARD + 0.9)) * (1 - prog(t, DUR - 0.6, DUR))
    if a > 0:
        tracked(cr, 'FOLLOW FOR MORE OF THE UNIVERSE', 540, 1500, 34, 'Poppins Regular' if False else 'Poppins Light', WARM, a, 6)

def render_frame(cr, t):
    draw_stars(cr, t, zoom(t))
    draw_black_hole(cr, t)
    g = cairo.RadialGradient(W / 2, H / 2, 420, W / 2, H / 2, 1150)  # vignette
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.85)
    cr.set_source(g); cr.paint()
    g = cairo.LinearGradient(0, 1150, 0, 1800)  # darken behind the type
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(0.5, 0, 0, 0, 0.45); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    cr.set_source(g); cr.paint()
    draw_text(cr, t)
    rng = np.random.default_rng(int(t * FPS))  # film grain
    for _ in range(500):
        cr.rectangle(rng.uniform(0, W), rng.uniform(0, H), 2, 2); cr.set_source_rgba(1, 1, 1, rng.uniform(0, 0.05)); cr.fill()
    fi = 1 - ease_out(prog(t, 0, 0.25)); fo = prog(t, DUR - 0.6, DUR)
    if fi > 0 or fo > 0: cr.set_source_rgba(0, 0, 0, max(fi, fo)); cr.paint()

def ambient(path):
    """Fallback score: slow pads and soft piano-like notes (only used if the trending track isn't added)."""
    n = int(SR * DUR); tt = np.arange(n) / SR; out = np.zeros(n)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: out[i0:i0 + len(sig)] += sig[:n - i0]
    chords = [[57, 60, 64, 71], [53, 57, 60, 67], [48, 55, 59, 64], [55, 59, 62, 66]]
    for ci in range(int(DUR / 5) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(6.5 * SR)) / SR
        env = np.minimum(1, L_ / 1.8) * np.exp(-L_ * 0.35)
        put(ci * 5, sum(0.03 * (np.sin(2 * np.pi * note(m) * L_) + 0.6 * np.sin(2 * np.pi * note(m) * 1.003 * L_ + 1)) for m in ch) * env)
        put(ci * 5, 0.08 * np.sin(2 * np.pi * note(ch[0] - 24) * L_) * env)
        for j, m in enumerate([ch[3] + 12, ch[1] + 12, ch[2] + 12]):
            pt = np.arange(int(2.5 * SR)) / SR
            put(ci * 5 + 0.6 + j * 1.4, 0.05 * (np.sin(2 * np.pi * note(m) * pt) + 0.25 * np.sin(4 * np.pi * note(m) * pt)) * np.exp(-pt * 2.2))
    rev = np.zeros(n)  # simple echo for space
    for d, g in ((0.31, 0.35), (0.53, 0.25), (0.79, 0.15)):
        k = int(d * SR); rev[k:] += g * out[:-k]
    mix = np.tanh((out + rev) * 1.5) * 0.6
    mix *= np.minimum(1, tt / 1.5) * np.minimum(1, (DUR - tt) / 2.0)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    base = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[3].split(','):
            render_frame(cr, float(ts)); surf.write_to_png(f'{base}_{ts}.png')
        return
    nfr = int(DUR * FPS); workers = os.cpu_count() or 4
    bounds = np.linspace(0, nfr, workers * 2 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    ambient(base + '.wav')
    # silent master (a silent audio track keeps every editor happy) and an ambient-score fallback
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt',
                    '-f', 'lavfi', '-i', f'anullsrc=r={SR}:cl=stereo', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest',
                    '-movflags', '+faststart', base + '-silent.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', base + '-ambient.mp4'], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
