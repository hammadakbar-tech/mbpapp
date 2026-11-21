"""'Guess the Country' quiz Shorts (9:16) with narration, countdown, map reveal and recap.
Usage: python3 quiz.py <data_dir> <voices_dir> <episode> <out.mp4> [--preview t1,t2,...]
  data_dir:   countries_50m.geojson + countries_110m.geojson (Natural Earth)
  voices_dir: kokoro-v1.0.onnx + voices-v1.0.bin
"""
import hashlib, json, math, os, subprocess, sys, wave
import numpy as np
import cairo

W, H, FPS = 1080, 1920, 30
SR = 48000
VOICE, SPEED = 'af_heart', 1.1

# country (Natural Earth NAME), shown name, difficulty, spoken reveal, on-screen fact
EPISODES = {
    1: [('Italy', 'ITALY', 'EASY', "It's Italy, the famous boot of Europe!", 'The boot of Europe'),
        ('Japan', 'JAPAN', 'EASY', "It's Japan, made of over fourteen thousand islands!", '14,000+ islands'),
        ('Brazil', 'BRAZIL', 'MEDIUM', "It's Brazil, home to most of the Amazon rainforest!", 'Home of the Amazon'),
        ('Turkey', 'TURKEY', 'MEDIUM', "It's Turkey, sitting in both Europe and Asia!", 'In Europe AND Asia'),
        ('Mongolia', 'MONGOLIA', 'HARD', "It's Mongolia, the most sparsely populated country on Earth!", 'Fewest people per km²')],
    2: [('Chile', 'CHILE', 'EASY', "It's Chile, over four thousand kilometers long!", '4,300 km long'),
        ('Egypt', 'EGYPT', 'EASY', "It's Egypt, home of the Great Pyramid of Giza!", 'Land of the pyramids'),
        ('Vietnam', 'VIETNAM', 'MEDIUM', "It's Vietnam, shaped like a long letter S!", 'Shaped like an S'),
        ('Madagascar', 'MADAGASCAR', 'MEDIUM', "It's Madagascar, where most wildlife lives nowhere else on Earth!", 'Wildlife found nowhere else'),
        ('Kazakhstan', 'KAZAKHSTAN', 'HARD', "It's Kazakhstan, the biggest landlocked country in the world!", 'Biggest landlocked country')],
}
INTRO = "Can you guess all five countries just from their shape? Let's go!"
ASKS = ["Number one. An easy one to start.", "Number two.", "Number three. Getting harder!",
        "Number four.", "Number five. Only geniuses get this one!"]
OUTRO = "How many did you get? Comment your score, and follow for part two!"
COUNT = 3.0

def hexc(h, a=1.0):
    h = h.lstrip('#'); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)
BG_TOP, BG_BOT = hexc('#2A1260'), hexc('#0F0A2E')
CARD, CARD_EDGE = hexc('#1A1145'), hexc('#5B48C8')
YELLOW, PINK, CYAN, GREEN, WHITE = hexc('#FFD23F'), hexc('#FF4F8B'), hexc('#3DDCFF'), hexc('#3DDC84'), hexc('#FFFFFF')
MAP_FILL, MAP_EDGE, LILAC = hexc('#3A2C84'), hexc('#6E5BC4'), hexc('#B9AEF5')
DIFF_COLOR = {'EASY': GREEN, 'MEDIUM': YELLOW, 'HARD': PINK}
CARD_RECT = (60, 400, 960, 880)  # x, y, w, h
CX, CY = 540, 840                # silhouette centre

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def ease_io(t): t = clamp(t); return 4*t*t*t if t < .5 else 1 - (-2*t + 2)**3 / 2
def ease_out(t): t = clamp(t); return 1 - (1 - t)**3
def ease_back(t, s=2.2): t = clamp(t) - 1; return max(1e-3, 1 + (s + 1) * t**3 + s * t**2)

def merc(lat):
    lat = np.clip(lat, -82, 82)
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))

# ---------- geo ----------
def rings_of(geom):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    return [np.array(p[0], dtype=float) for p in polys]

def load_geo(data_dir, wanted):
    hi = json.load(open(os.path.join(data_dir, 'countries_50m.geojson')))
    lo = json.load(open(os.path.join(data_dir, 'countries_110m.geojson')))
    world = []
    for f in lo['features']:
        for r in rings_of(f['geometry']):
            if r[:, 1].mean() > -60: world.append((r[:, 0], merc(r[:, 1])))
    shapes = {}
    for f in hi['features']:
        name = f['properties']['NAME']
        if name not in wanted: continue
        rings = rings_of(f['geometry'])
        main = max(rings, key=lambda r: np.ptp(r[:, 0]) * np.ptp(r[:, 1]))
        x0, x1, y0, y1 = main[:, 0].min(), main[:, 0].max(), main[:, 1].min(), main[:, 1].max()
        pad = max(x1 - x0, y1 - y0) * 0.6 + 2
        keep = [r for r in rings if x0 - pad < r[:, 0].mean() < x1 + pad and y0 - pad < r[:, 1].mean() < y1 + pad]
        rr = [(r[:, 0], merc(r[:, 1])) for r in keep]
        xs = np.concatenate([r[0] for r in rr]); ys = np.concatenate([r[1] for r in rr])
        bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
        fit = min(700 / (bx1 - bx0), 700 / (by1 - by0))
        shapes[name] = dict(rings=rr, cx=(bx0 + bx1) / 2, cy=(by0 + by1) / 2, fit=fit)
    return world, shapes

def ring_path(cr, rx, ry, cam):
    cx, cy, z, sx, sy = cam
    xs = sx + (rx - cx) * z; ys = sy - (ry - cy) * z
    cr.move_to(xs[0], ys[0])
    for x, y in zip(xs[1:], ys[1:]): cr.line_to(x, y)
    cr.close_path()
    return xs, ys

# ---------- text ----------
def font(cr, size, bold=True):
    cr.select_font_face('Inter Display', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(size)

def tw(cr, s, sp=0): return sum(cr.text_extents(c).x_advance + sp for c in s) - (sp if s else 0)

def text(cr, s, x, y, col, a=1.0, sp=0, anchor='c', shadow=False):
    w = tw(cr, s, sp)
    x = x - w / 2 if anchor == 'c' else (x - w if anchor == 'r' else x)
    for dx, dy, c, aa in ([(0, 6, (0, 0, 0), 0.35 * a)] if shadow else []) + [(0, 0, col[:3], col[3] * a)]:
        cr.set_source_rgba(*c, aa); xx = x + dx
        for ch in s:
            cr.move_to(xx, y + dy); cr.show_text(ch); xx += cr.text_extents(ch).x_advance + sp

def fit_font(cr, s, size, maxw, sp=0, bold=True):
    font(cr, size, bold)
    w = tw(cr, s, sp)
    if w > maxw: font(cr, size * maxw / w, bold)

def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()

def pill(cr, s, x, y, size, bg, fg, a=1.0, scale=1.0, padx=30, pady=16):
    font(cr, size); w = tw(cr, s, 2)
    cr.save(); cr.translate(x, y); cr.scale(scale, scale)
    rrect(cr, -w / 2 - padx, -size * 0.5 - pady, w + 2 * padx, size + 2 * pady, (size + 2 * pady) / 2)
    cr.set_source_rgba(*bg[:3], bg[3] * a); cr.fill()
    text(cr, s, 0, size * 0.36, fg, a, sp=2)
    cr.restore()

# ---------- voice ----------
class Voice:
    def __init__(self, vdir, cache):
        self.vdir, self.cache, self.k = vdir, cache, None
        os.makedirs(cache, exist_ok=True)
    def get(self, s):
        p = os.path.join(self.cache, hashlib.md5(f'{VOICE}|{SPEED}|{s}'.encode()).hexdigest() + '.npy')
        if os.path.exists(p): return np.load(p)
        if self.k is None:
            from kokoro_onnx import Kokoro
            self.k = Kokoro(os.path.join(self.vdir, 'kokoro-v1.0.onnx'), os.path.join(self.vdir, 'voices-v1.0.bin'))
        a, sr = self.k.create(s, voice=VOICE, speed=SPEED, lang='en-us')
        nz = np.nonzero(np.abs(a) > 0.01)[0]; a = a[max(nz[0] - 200, 0):nz[-1] + 1200]
        a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a)
        np.save(p, a); return a

# ---------- timeline ----------
def build(ep, voice):
    clips, qs, t = [], [], 0.3
    a = voice.get(INTRO); clips.append((t, a)); intro_end = t + len(a) / SR
    t = intro_end + 0.5
    for i, (name, shown, diff, reveal, fact) in enumerate(EPISODES[ep]):
        q = dict(name=name, shown=shown, diff=diff, fact=fact, i=i, start=t)
        a = voice.get(ASKS[i]); clips.append((t + 0.35, a))
        q['ask'] = (t + 0.35, t + 0.35 + len(a) / SR)
        q['cd'] = q['ask'][1] + 0.15
        q['reveal'] = q['cd'] + COUNT
        a = voice.get(reveal); clips.append((q['reveal'] + 0.3, a))
        q['say'] = (q['reveal'] + 0.3, q['reveal'] + 0.3 + len(a) / SR)
        q['end'] = max(q['say'][1] + 0.7, q['reveal'] + 3.2)
        t = q['end']; qs.append(q)
    a = voice.get(OUTRO); outro = (t + 0.4, t + 0.4 + len(a) / SR); clips.append((outro[0], a))
    return dict(intro_end=intro_end, qs=qs, outro_start=t, outro=outro, dur=outro[1] + 1.8, clips=clips)

# ---------- drawing ----------
def draw_bg(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *BG_TOP); g.add_color_stop_rgba(1, *BG_BOT)
    cr.set_source(g); cr.paint()
    # slow sunburst behind the card
    cr.save(); cr.translate(CX, CY); cr.rotate(t * 0.12)
    for k in range(18):
        a0 = k * 2 * math.pi / 18
        cr.move_to(0, 0); cr.arc(0, 0, 1400, a0, a0 + math.pi / 18); cr.close_path()
    cr.set_source_rgba(1, 1, 1, 0.035); cr.fill(); cr.restore()
    # drifting dots
    rng = np.random.default_rng(7)
    for _ in range(40):
        x, y, s, sp = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 6), rng.uniform(10, 40)
        y = (y - t * sp) % H
        cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(*LILAC[:3], 0.18); cr.fill()

def confetti(cr, t, t0, seed):
    u = t - t0
    if not 0 <= u <= 2.2: return
    rng = np.random.default_rng(seed)
    cols = [YELLOW, PINK, CYAN, GREEN, WHITE]
    for _ in range(90):
        ang = rng.uniform(-math.pi, 0) if rng.random() < .8 else rng.uniform(0, math.pi)
        sp = rng.uniform(500, 1500)
        x = CX + math.cos(ang) * sp * u * (1 - 0.35 * u)
        y = CY + math.sin(ang) * sp * u * (1 - 0.35 * u) + 900 * u * u
        rot = rng.uniform(0, 6) + u * rng.uniform(-10, 10)
        c = cols[rng.integers(len(cols))]
        cr.save(); cr.translate(x, y); cr.rotate(rot)
        cr.rectangle(-9, -5, 18, 10); cr.set_source_rgba(*c[:3], clamp(1.6 - u)); cr.fill(); cr.restore()

def draw_question(cr, T, q, world, shapes, t):
    a_in = ease_out(prog(t, q['start'], q['start'] + 0.35))
    a_out = 1 - ease_io(prog(t, q['end'] - 0.3, q['end']))
    al = a_in * a_out
    if al <= 0: return
    sh = shapes[q['name']]
    rv = q['reveal']
    # header: progress dots + difficulty chip
    for k in range(5):
        x = 540 + (k - 2) * 70
        done = k < q['i'] or (k == q['i'] and t >= rv)
        cur = k == q['i']
        cr.new_path(); cr.arc(x, 300, 17 if cur else 12, 0, 2 * math.pi)
        cr.set_source_rgba(*(GREEN if done else (YELLOW if cur else LILAC))[:3], al * (1 if done or cur else 0.4)); cr.fill()
    dc = DIFF_COLOR[q['diff']]
    pill(cr, f"#{q['i'] + 1}  ·  {q['diff']}", 540, 1380 if False else 210, 34, dc, BG_BOT, al,
         scale=ease_back(prog(t, q['start'] + 0.1, q['start'] + 0.5)))
    # card
    x, y, w, h = CARD_RECT
    cr.save()
    rrect(cr, x, y, w, h, 48); cr.set_source_rgba(*CARD[:3], 0.85 * al); cr.fill_preserve()
    cr.set_source_rgba(*CARD_EDGE[:3], al); cr.set_line_width(4); cr.stroke_preserve(); cr.clip()
    # camera: fit on country, then zoom out to show it on the map
    zk = ease_io(prog(t, rv + 0.9, rv + 2.1))
    breathe = 1 + 0.025 * math.sin(t * 3.0) * (1 - zk)
    z = sh['fit'] * breathe * math.exp(lerp(0, math.log(0.3), zk))
    cam = (sh['cx'], sh['cy'], z, CX, CY)
    map_a = ease_out(prog(t, rv + 0.8, rv + 1.6)) * al
    if map_a > 0:
        for rx, ry in world:
            sx = CX + (rx - sh['cx']) * z
            if sx.max() < x - 20 or sx.min() > x + w + 20: continue
            cr.new_path(); ring_path(cr, rx, ry, cam)
            cr.set_source_rgba(*MAP_FILL[:3], map_a); cr.fill_preserve()
            cr.set_source_rgba(*MAP_EDGE[:3], map_a); cr.set_line_width(1.5); cr.stroke()
    # silhouette: outline draws in, then fills; turns green on reveal
    draw_k = ease_io(prog(t, q['start'] + 0.2, q['start'] + 1.0))
    fill_k = ease_out(prog(t, q['start'] + 0.7, q['start'] + 1.2))
    green = ease_out(prog(t, rv, rv + 0.25))
    col = [lerp(a, b, green) for a, b in zip(WHITE[:3], GREEN[:3])]
    cr.new_path()
    for rx, ry in sh['rings']: ring_path(cr, rx, ry, cam)
    # glow
    cr.set_source_rgba(*col, 0.18 * al * fill_k); cr.set_line_width(26); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.stroke_preserve()
    cr.set_source_rgba(*col, al * fill_k); cr.fill_preserve()
    cr.set_line_width(4); cr.set_dash([4000 * draw_k, 4000]) if draw_k < 1 else cr.set_dash([])
    cr.set_source_rgba(*col, al); cr.stroke(); cr.set_dash([])
    if t >= rv:  # location pulse on the map
        pr = prog(t, rv + 1.8, rv + 3.0)
        if 0 < pr < 1:
            cr.new_path(); cr.arc(CX, CY, 30 + 160 * ease_out(pr), 0, 2 * math.pi)
            cr.set_source_rgba(*GREEN[:3], (1 - pr) * al); cr.set_line_width(5); cr.stroke()
    cr.restore()
    # countdown
    cd = q['cd']
    ca = ease_out(prog(t, cd - 0.2, cd + 0.2)) * (1 - ease_io(prog(t, rv, rv + 0.25))) * al
    if ca > 0:
        rem = clamp(1 - (t - cd) / COUNT)
        n = max(1, min(3, math.ceil(COUNT - (t - cd)))) if t >= cd else 3
        col = [CYAN, YELLOW, PINK][3 - n]
        shake = 6 * math.sin(t * 60) if n == 1 and t >= cd else 0
        cr.new_path(); cr.arc(540 + shake, 1480, 118, 0, 2 * math.pi)
        cr.set_source_rgba(*CARD[:3], 0.9 * ca); cr.fill()
        cr.set_line_width(16); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.new_path(); cr.arc(540 + shake, 1480, 118, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.12 * ca); cr.stroke()
        cr.new_path(); cr.arc(540 + shake, 1480, 118, -math.pi / 2, -math.pi / 2 + 2 * math.pi * rem)
        cr.set_source_rgba(*col[:3], ca); cr.stroke()
        frac = (t - cd) % 1.0 if t >= cd else 1.0
        s = ease_back(clamp(frac / 0.3)) if t >= cd else 1
        cr.save(); cr.translate(540 + shake, 1480); cr.scale(s, s)
        font(cr, 130); text(cr, str(n), 0, 46, WHITE, ca)
        cr.restore()
        font(cr, 40); text(cr, 'THINK FAST!', 540, 1680, YELLOW, ca * (0.6 + 0.4 * math.sin(t * 8) ** 2), sp=6)
    # reveal
    if t >= rv:
        k = prog(t, rv, rv + 0.45)
        cr.save(); cr.translate(540, 1470); cr.scale(ease_back(k), ease_back(k))
        fit_font(cr, q['shown'], 130, 940, 4)
        text(cr, q['shown'], 0, 40, WHITE, al, sp=4, shadow=True)
        cr.restore()
        fk = ease_out(prog(t, rv + 0.5, rv + 0.9))
        fit_font(cr, q['fact'], 44, 900, 1, bold=False)
        text(cr, q['fact'], 540, 1580 + (1 - fk) * 20, LILAC, al * fk, sp=1)
        pill(cr, 'CORRECT?', 540, 1720, 32, GREEN, BG_BOT, al * fk, scale=0.9 + 0.1 * fk)
        flash = 1 - prog(t, rv, rv + 0.3)
        if flash > 0: cr.set_source_rgba(1, 1, 1, 0.35 * flash); cr.paint()
        confetti(cr, t, rv, q['i'] + 11)

def draw_intro(cr, T, shapes, ep, t):
    al = 1 - ease_io(prog(t, T['intro_end'] + 0.1, T['intro_end'] + 0.5))
    if al <= 0: return
    words = [('GUESS', WHITE, 420), ('THE', YELLOW, 560), ('COUNTRY', WHITE, 720)]
    for j, (wd, col, y) in enumerate(words):
        k = prog(t, 0.15 + j * 0.18, 0.55 + j * 0.18)
        cr.save(); cr.translate(540, y); cr.rotate((1 - ease_out(k)) * -0.3 * (1 if j % 2 else -1))
        cr.scale(ease_back(k), ease_back(k)); fit_font(cr, wd, 190 if j != 1 else 110, 960, 6)
        text(cr, wd, 0, 60, col, al, sp=6, shadow=True); cr.restore()
    k = ease_out(prog(t, 0.9, 1.3))
    pill(cr, 'BY ITS SHAPE', 540, 860, 40, PINK, WHITE, al * k, scale=ease_back(k))
    # preview of the five silhouettes, hidden as dark shapes
    names = [e[0] for e in EPISODES[ep]]
    for j, nm in enumerate(names):
        kk = ease_back(prog(t, 1.2 + j * 0.12, 1.6 + j * 0.12))
        if kk <= 0: continue
        sh = shapes[nm]; bx = 540 + (j - 2) * 190; by = 1150 + (40 if j % 2 else 0)
        z = sh['fit'] * 0.22 * kk
        cr.new_path()
        for rx, ry in sh['rings']: ring_path(cr, rx, ry, (sh['cx'], sh['cy'], z, bx, by))
        cr.set_source_rgba(*LILAC[:3], 0.9 * al); cr.fill()
        font(cr, 54); text(cr, '?', bx, by + 130, YELLOW, al * clamp(kk))
    k2 = ease_out(prog(t, 2.0, 2.4))
    font(cr, 44, bold=False); text(cr, '5 countries. Can you get them all?', 540, 1500, LILAC, al * k2)
    font(cr, 36); text(cr, f'PART {ep}', 540, 1620, YELLOW, al * k2, sp=8)

def draw_outro(cr, T, shapes, ep, t):
    a = ease_out(prog(t, T['outro_start'], T['outro_start'] + 0.4))
    if a <= 0: return
    font(cr, 92); text(cr, 'HOW MANY', 540, 300, WHITE, a, sp=4, shadow=True)
    text(cr, 'DID YOU GET?', 540, 410, YELLOW, a, sp=4, shadow=True)
    qs = EPISODES[ep]
    pos = [(250, 640), (540, 640), (830, 640), (395, 980), (685, 980)]
    for j, ((nm, shown, diff, *_), (bx, by)) in enumerate(zip(qs, pos)):
        k = ease_back(prog(t, T['outro_start'] + 0.2 + j * 0.12, T['outro_start'] + 0.6 + j * 0.12))
        if k <= 0: continue
        cr.save(); cr.translate(bx, by); cr.scale(k, k)
        rrect(cr, -130, -140, 260, 300, 32); cr.set_source_rgba(*CARD[:3], 0.9 * a); cr.fill_preserve()
        cr.set_source_rgba(*DIFF_COLOR[diff][:3], a); cr.set_line_width(4); cr.stroke()
        sh = shapes[nm]; z = min(sh['fit'] * 0.25, sh['fit'] * 180 / 700)
        cr.new_path()
        for rx, ry in sh['rings']: ring_path(cr, rx, ry, (sh['cx'], sh['cy'], z, 0, -20))
        cr.set_source_rgba(*GREEN[:3], a); cr.fill()
        fit_font(cr, shown, 34, 230); text(cr, shown, 0, 130, WHITE, a)
        cr.restore()
    k = ease_out(prog(t, T['outro'][0] + 1.0, T['outro'][0] + 1.4))
    pill(cr, 'COMMENT YOUR SCORE  /5', 540, 1320, 46, YELLOW, BG_BOT, a * k, scale=ease_back(k))
    k2 = ease_out(prog(t, T['outro'][0] + 2.2, T['outro'][0] + 2.6))
    pill(cr, f'FOLLOW FOR PART {ep + 1}', 540, 1480, 46, PINK, WHITE, a * k2, scale=ease_back(k2) * (1 + 0.04 * math.sin(t * 6)))

def render_frame(cr, T, world, shapes, ep, t):
    draw_bg(cr, t)
    draw_intro(cr, T, shapes, ep, t)
    for q in T['qs']:
        if q['start'] - 0.1 <= t <= q['end'] + 0.1: draw_question(cr, T, q, world, shapes, t)
    draw_outro(cr, T, shapes, ep, t)
    f = prog(t, T['dur'] - 0.4, T['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- audio ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(3)
    music = np.zeros(n)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    bpm = 124; beat = 60 / bpm
    chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]  # C G Am F
    nb = int(dur / beat)
    for b in range(nb):
        t0 = b * beat; i0 = int(t0 * SR)
        ch = chords[(b // 4) % 4]
        L = int(0.3 * SR); lt = np.arange(L) / SR
        f = 48 + 80 * np.exp(-lt * 35)  # kick
        seg = 0.45 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-lt * 10)
        music[i0:i0 + L] += seg[:max(0, n - i0)]
        for h in (0, 0.5):  # bass on 8ths
            j0 = int((t0 + h * beat) * SR); M = int(beat * 0.45 * SR); mt = np.arange(M) / SR
            bs = 0.13 * np.sign(np.sin(2 * np.pi * note(ch[0] - 24) * mt)) * np.exp(-mt * 6)
            music[j0:j0 + M] += bs[:max(0, n - j0)]
        j0 = int((t0 + beat / 2) * SR); M = int(0.05 * SR)  # hat
        music[j0:j0 + M] += (0.05 * np.diff(rng.standard_normal(M + 1)) * np.exp(-np.arange(M) / SR * 70))[:max(0, n - j0)]
        for s in range(2):  # pluck arpeggio on 8ths
            m = ch[(b * 2 + s) % 3] + 12
            j0 = int((t0 + s * beat / 2) * SR); M = int(0.25 * SR); mt = np.arange(M) / SR
            pl = 0.05 * (np.sin(2 * np.pi * note(m) * mt) + 0.3 * np.sin(4 * np.pi * note(m) * mt)) * np.exp(-mt * 14)
            music[j0:j0 + M] += pl[:max(0, n - j0)]
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def add(t0, sig):
        i0 = int(t0 * SR); fx[i0:i0 + len(sig)] += sig[:max(0, n - i0)]
    for q in T['qs']:
        for k in range(3):  # countdown ticks
            L = int(0.08 * SR); lt = np.arange(L) / SR
            add(q['cd'] + k, (0.35 if k < 2 else 0.45) * np.sin(2 * np.pi * (1400 if k < 2 else 1800) * lt) * np.exp(-lt * 60))
        L = int(1.2 * SR); lt = np.arange(L) / SR  # reveal chime
        add(q['reveal'], 0.22 * sum(np.sin(2 * np.pi * f * lt) * np.exp(-lt * d) for f, d in ((1046.5, 4), (1318.5, 4.5), (1568, 5), (2093, 7))))
        nz = rng.standard_normal(int(0.6 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2
        add(q['start'] - 0.1, 0.12 * np.convolve(nz, np.ones(30) / 30, 'same') * env)  # whoosh
    v = np.zeros(n)
    for s, a in T['clips']:
        i0 = int(s * SR); v[i0:i0 + len(a)] += a[:max(0, n - i0)]
    v = v / max(1e-6, np.abs(v).max()) * 0.9
    # music dips under the voice and during countdowns
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = 1 - 0.6 * np.clip(env / 0.03, 0, 1)
    for q in T['qs']:
        duck[int(q['cd'] * SR):int(q['reveal'] * SR)] *= 0.55
    duck = np.convolve(duck, np.ones(4800) / 4800, mode='same')
    mix = music * duck + fx + v
    mix *= np.minimum(1, tt / 0.2) * np.minimum(1, (dur - tt) / 1.0)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def main():
    data_dir, vdir, ep, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    voice = Voice(vdir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache'))
    T = build(ep, voice)
    world, shapes = load_geo(data_dir, {e[0] for e in EPISODES[ep]})
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    print(f"episode {ep}: {T['dur']:.1f}s")
    if len(sys.argv) > 5 and sys.argv[5] == '--preview':
        for ts in sys.argv[6].split(','):
            render_frame(cr, T, world, shapes, ep, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        print(json.dumps({k: v for k, v in T.items() if k != 'clips'}, default=str)[:1500])
        return
    wav = out.rsplit('.', 1)[0] + '.wav'
    make_audio(T, wav)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                          stdin=subprocess.PIPE)
    for i in range(int(T['dur'] * FPS)):
        render_frame(cr, T, world, shapes, ep, i / FPS); surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait()

if __name__ == '__main__':
    main()
