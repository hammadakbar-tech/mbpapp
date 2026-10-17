"""'Canada vs USA: Who Wins?' (9:16) - 8-round head-to-head game show in full motion graphics.
Two voices (Canadian host + American rival) via edge-tts, Poppins type, scoreboard, animated stat visuals,
karaoke captions, confetti, sound design. Frames render in parallel workers.
Usage: python3 vs.py <data_dir> <out.mp4> [--preview t1,t2,...]
"""
import asyncio, hashlib, json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR
from canada import rings

W, H, FPS = 1080, 1920, 30
NAVY, NAVY2 = hexc('#0B0A24'), hexc('#05040F')
RED, RED2 = hexc('#FF2D47'), hexc('#B5001B')
BLUE, BLUE2 = hexc('#2F6BFF'), hexc('#0A2BB0')
GOLD, WHITE, VIOLET, MINT = hexc('#FFD60A'), hexc('#FFFFFF'), hexc('#8B3DFF'), hexc('#3DFFB0')
INK = (0.03, 0.02, 0.09)
SIDE = {'ca': RED, 'us': BLUE}
CX = {'ca': 270, 'us': 810}
VOICES = {'ca': 'en-CA-ClaraNeural', 'us': 'en-US-GuyNeural'}

def f2(v): return f'{v:.2f}'
ROUNDS = [
    dict(key='size', title='SIZE', emoji='📏', viz='map', win='ca',
         ca=(9.98, lambda v: f'{v:.2f}M km²'), us=(9.83, lambda v: f'{v:.2f}M km²'),
         lines=[('ca', "Round one: size!", None),
                ('ca', "Canada: nine point nine eight million square kilometres.", 'ca'),
                ('us', "The USA: nine point eight three million.", 'us'),
                ('ca', "Canada wins... by a hair!", 'win')]),
    dict(key='people', title='PEOPLE', emoji='👥', viz='people', win='us',
         ca=(41, lambda v: f'{v:.0f}M'), us=(340, lambda v: f'{v:.0f}M'),
         lines=[('us', "Round two: people!", None),
                ('us', "America has about three hundred forty million.", 'us'),
                ('ca', "Canada has about forty-one million.", 'ca'),
                ('us', "That's eight times more. Point, USA!", 'win')]),
    dict(key='coast', title='COASTLINE', emoji='🌊', viz='coast', win='ca',
         ca=(243042, lambda v: f'{v:,.0f} km'), us=(19924, lambda v: f'{v:,.0f} km'),
         lines=[('ca', "Round three: coastline!", None),
                ('ca', "Canada's is over two hundred forty thousand kilometres. The longest on Earth!", 'ca'),
                ('us', "Ours is about twenty thousand.", 'us'),
                ('ca', "Twelve times longer. Canada!", 'win')]),
    dict(key='money', title='ECONOMY', emoji='💰', viz='bars', win='us',
         ca=(2.2, lambda v: f'${v:.1f}T'), us=(29.2, lambda v: f'${v:.1f}T'),
         lines=[('us', "Round four: money!", None),
                ('us', "The US economy is worth about twenty-nine trillion dollars.", 'us'),
                ('ca', "Canada's? About two point two trillion.", 'ca'),
                ('us', "USA takes it!", 'win')]),
    dict(key='peak', title='TALLEST PEAK', emoji='🏔️', viz='mountain', win='us',
         ca=(5959, lambda v: f'{v:,.0f} m'), us=(6190, lambda v: f'{v:,.0f} m'),
         lines=[('us', "Round five: tallest mountain!", None),
                ('us', "Denali, Alaska: six thousand one hundred ninety metres.", 'us'),
                ('ca', "Mount Logan, Yukon: five thousand nine hundred fifty-nine.", 'ca'),
                ('us', "USA, by over two hundred metres!", 'win')]),
    dict(key='life', title='LIFE EXPECTANCY', emoji='❤️', viz='life', win='ca',
         ca=(82, lambda v: f'~{v:.0f} yrs'), us=(78, lambda v: f'~{v:.0f} yrs'),
         lines=[('ca', "Round six: life expectancy!", None),
                ('ca', "Canadians live about eighty-two years.", 'ca'),
                ('us', "Americans... about seventy-eight.", 'us'),
                ('ca', "Canada wins!", 'win')]),
    dict(key='moon', title='MOON LANDINGS', emoji='🌕', viz='moon', win='us',
         ca=(0, lambda v: f'{v:.0f}'), us=(6, lambda v: f'{v:.0f}'),
         lines=[('us', "Round seven: Moon landings!", None),
                ('us', "USA: six.", 'us'),
                ('ca', "Canada: zero... but hey, we built the Canadarm!", 'ca'),
                ('us', "USA!", 'win')]),
    dict(key='maple', title='MAPLE SYRUP', emoji='🍁', viz='pie', win='ca',
         ca=(70, lambda v: f'~{v:.0f}%'), us=(30, lambda v: f'~{v:.0f}%'),
         lines=[('ca', "Final round: maple syrup!", None),
                ('ca', "Canada makes about seventy percent of the world's supply.", 'ca'),
                ('us', "Okay... that one's yours.", 'us'),
                ('ca', "Canada!", 'win')]),
]
INTRO = [('ca', "Canada versus the USA!"), ('us', "Eight rounds. One winner."), ('ca', "Let's settle this!")]
OUTRO = [('ca', "Wait... that's four to four!"), ('us', "It's a tie!"), ('ca', "So, you decide."),
         ('us', "Canada, or USA?"), ('ca', "Tell us in the comments!")]
NUM = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'FINAL']

# ---------- voice ----------
class EdgeVoice:
    def __init__(self, cache): self.cache = cache; os.makedirs(cache, exist_ok=True)
    def get(self, spk, s):
        v = VOICES[spk]; rate = '+8%' if spk == 'ca' else '+5%'
        p = os.path.join(self.cache, hashlib.md5(f'edge|{v}|{rate}|{s}'.encode()).hexdigest() + '.npy')
        if os.path.exists(p): return np.load(p)
        import edge_tts
        async def run():
            buf = bytearray()
            async for ch in edge_tts.Communicate(s, v, rate=rate, proxy=os.environ.get('HTTPS_PROXY')).stream():
                if ch['type'] == 'audio': buf.extend(ch['data'])
            return bytes(buf)
        mp3 = asyncio.run(run())
        pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', 'pipe:0', '-f', 's16le', '-ac', '1', '-ar', str(SR), 'pipe:1'],
                             input=mp3, capture_output=True, check=True).stdout
        a = np.frombuffer(pcm, '<i2').astype(np.float32) / 32767
        nz = np.nonzero(np.abs(a) > 0.01)[0]; a = a[max(nz[0] - 200, 0):nz[-1] + 1200]
        np.save(p, a); return a

# ---------- timeline ----------
def build(voice):
    t, clips, lines = 0.2, [], []
    def say(spk, s, tag=None, gap=0.18):
        nonlocal t
        a = voice.get(spk, s); clips.append((t, a)); seg = (t, t + len(a) / SR, s, spk, tag); lines.append(seg)
        t = seg[1] + gap; return seg
    intro = dict(start=0.0)
    t = 0.9
    intro['lines'] = [say(s, x, gap=0.25) for s, x in INTRO]
    intro['end'] = t + 0.3; t = intro['end']
    rounds, score = [], {'ca': 0, 'us': 0}
    for i, r in enumerate(ROUNDS):
        R = dict(r, i=i, start=t)
        t += 0.75   # banner slam before the first line
        R['lines'] = [say(s, x, tag) for s, x, tag in r['lines']]
        R['reveal'] = {tag: seg[0] for seg in R['lines'] for tag in [seg[4]] if tag}
        score[r['win']] += 1; R['score'] = dict(score)
        R['end'] = t + 0.9; t = R['end']; rounds.append(R)
    outro = dict(start=t); t += 0.5
    outro['lines'] = [say(s, x, gap=0.3) for s, x in OUTRO]
    outro['end'] = t + 2.0
    return dict(intro=intro, rounds=rounds, outro=outro, clips=clips, lines=lines, dur=outro['end'])

# ---------- type ----------
def face(cr, size, fam='Poppins Black'):
    if fam == 'emoji': cr.select_font_face('Noto Color Emoji')
    elif fam == 'Poppins': cr.select_font_face('Poppins', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    else: cr.select_font_face(fam)
    cr.set_font_size(size)

def tw(cr, s, size, fam='Poppins Black'): face(cr, size, fam); return cr.text_extents(s).x_advance

def ptext(cr, s, x, y, size, fill, a=1.0, fam='Poppins Black', anchor='c', sw=None, shadow=True):
    face(cr, size, fam)
    w = cr.text_extents(s).x_advance
    x0 = x - w / 2 if anchor == 'c' else (x - w if anchor == 'r' else x)
    sw = size * 0.16 if sw is None else sw
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    if shadow:
        cr.new_path(); cr.move_to(x0 + size * 0.04, y + size * 0.08); cr.text_path(s)
        cr.set_source_rgba(0, 0, 0, 0.45 * a); cr.set_line_width(sw); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, y); cr.text_path(s)
    if sw > 0: cr.set_source_rgba(*INK, a); cr.set_line_width(sw); cr.stroke_preserve()
    cr.set_source_rgba(*fill[:3], a); cr.fill()
    return w

def fit(cr, s, size, maxw, fam='Poppins Black'):
    w = tw(cr, s, size, fam); return size * min(1.0, maxw / max(w, 1))

def emoji(cr, e, x, y, size, a=1.0, rot=0.0):
    if size < 1 or a <= 0: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); s = size / 109; cr.scale(s, s)
    face(cr, 109, 'emoji'); w = cr.text_extents(e).x_advance
    cr.push_group(); cr.move_to(-w / 2, 40); cr.show_text(e); cr.pop_group_to_source(); cr.paint_with_alpha(a)
    cr.restore()

def rrect(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()

def pop(t, t0, d=0.4, s=2.6): return ease_back(prog(t, t0, t0 + d), s)

# ---------- geo (equal-area silhouettes at one shared scale) ----------
def laea(lon, lat, lon0, lat0):
    l, p, p0 = np.radians(lon - lon0), np.radians(lat), math.radians(lat0)
    cosc = math.sin(p0) * np.sin(p) + math.cos(p0) * np.cos(p) * np.cos(l)
    k = np.sqrt(2 / np.maximum(1 + cosc, 1e-9))
    return 6371 * k * np.cos(p) * np.sin(l), 6371 * k * (math.cos(p0) * np.sin(p) - math.sin(p0) * np.cos(p) * np.cos(l))

class Geo:
    def __init__(self, data_dir):
        c50 = json.load(open(os.path.join(data_dir, 'countries_50m.geojson')))
        def get(name, lon0, lat0, keep):
            rs = [r for f in c50['features'] if f['properties']['NAME'] == name for r in rings(f['geometry'])
                  if len(r) >= 10 and keep(r)]
            out = [laea(r[:, 0], r[:, 1], lon0, lat0) for r in rs]
            xs = np.concatenate([o[0] for o in out]); ys = np.concatenate([o[1] for o in out])
            cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
            out = [(x - cx, y - cy) for x, y in out]
            return out, xs.max() - xs.min(), ys.max() - ys.min()
        self.ca, wc, hc = get('Canada', -96, 62, lambda r: True)
        self.us, wu, hu = get('United States of America', -115, 50, lambda r: r[:, 1].mean() > 24 and r[:, 0].mean() < -60)
        self.scale = min(470 / max(wc, wu), 560 / max(hc, hu))
        self.npts = {k: sum(len(x) for x, _ in getattr(self, k)) for k in ('ca', 'us')}

G = None
TL = None

def shape_path(cr, side, cx, cy, s, upto=None):
    rs = getattr(G, side); n = 0
    for x, y in rs:
        if upto is not None and n >= upto: break
        m = len(x) if upto is None else min(len(x), upto - n)
        X, Y = cx + x[:m] * s, cy - y[:m] * s
        cr.move_to(X[0], Y[0])
        for a, b in zip(X[1:], Y[1:]): cr.line_to(a, b)
        if upto is None or m == len(x): cr.close_path()
        n += len(x)

# ---------- background & chrome ----------
def draw_bg(cr, t, tilt=0.0):
    cr.set_source_rgba(*NAVY); cr.paint()
    for side, col, x in (('ca', RED, 0), ('us', BLUE, W)):
        g = cairo.RadialGradient(x, H * 0.45, 50, x, H * 0.45, 900)
        g.add_color_stop_rgba(0, *col[:3], 0.55); g.add_color_stop_rgba(1, *col[:3], 0)
        cr.set_source(g); cr.paint()
    # moving chevrons
    cr.save()
    for side, col, sgn in (('ca', RED, 1), ('us', BLUE, -1)):
        cr.save(); cr.rectangle(0 if side == 'ca' else W / 2, 0, W / 2, H); cr.clip()
        off = (t * 120) % 160
        for k in range(-2, 16):
            y = k * 160 + off * sgn
            cr.move_to(0, y); cr.line_to(W, y - 300 * sgn)
        cr.set_source_rgba(*col[:3], 0.08); cr.set_line_width(40); cr.stroke(); cr.restore()
    cr.restore()
    # divider
    wob = 6 * math.sin(t * 2)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(0.3, 1, 1, 1, 0.5); g.add_color_stop_rgba(0.7, 1, 1, 1, 0.5); g.add_color_stop_rgba(1, 1, 1, 1, 0)
    cr.move_to(W / 2 + 40 + wob, 230); cr.line_to(W / 2 - 40 - wob, 1450)
    cr.set_source(g); cr.set_line_width(4); cr.stroke()
    # sparkles
    rng = np.random.default_rng(4)
    for _ in range(50):
        x, y, sp = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(20, 60)
        y = (y - t * sp) % H; a = 0.3 + 0.3 * math.sin(t * 3 + x)
        cr.new_path(); cr.arc(x, y, rng.uniform(1.5, 3.5), 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, a * 0.6); cr.fill()

def current_score(t):
    sc = {'ca': 0, 'us': 0}; bump = {'ca': 0.0, 'us': 0.0}
    for R in TL['rounds']:
        tw_ = R['reveal']['win'] + 0.35
        if t >= tw_:
            sc = dict(R['score']); bump[R['win']] = max(0.0, 1 - (t - tw_) / 0.5) if t - tw_ < 0.5 else 0
    return sc, bump

def draw_scoreboard(cr, t):
    a = ease_out(prog(t, 2.0, 2.5))
    if a <= 0: return
    sc, bump = current_score(t)
    for side, x0, lab, em in (('ca', 30, 'CANADA', '🍁'), ('us', 570, 'USA', '🦅')):
        k = pop(t, 2.0 + (0.1 if side == 'us' else 0))
        cr.save(); cr.translate(x0 + 240, 125); cr.scale(k, k)
        rrect(cr, -240, -62, 480, 124, 62)
        g = cairo.LinearGradient(-240, 0, 240, 0)
        c1, c2 = (RED, RED2) if side == 'ca' else (BLUE2, BLUE)
        g.add_color_stop_rgba(0, *c1[:3], a); g.add_color_stop_rgba(1, *c2[:3], a)
        cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, 0.9 * a); cr.set_line_width(4); cr.stroke()
        if side == 'ca':
            emoji(cr, em, -185, -6, 64, a); ptext(cr, lab, -140, 18, 44, WHITE, a, anchor='l', sw=6)
            s = 1 + 0.5 * bump[side]
            cr.save(); cr.translate(150, 0); cr.scale(s, s); ptext(cr, str(sc[side]), 0, 30, 84, GOLD, a, sw=9); cr.restore()
        else:
            s = 1 + 0.5 * bump[side]
            cr.save(); cr.translate(-150, 0); cr.scale(s, s); ptext(cr, str(sc[side]), 0, 30, 84, GOLD, a, sw=9); cr.restore()
            ptext(cr, lab, 140, 18, 44, WHITE, a, anchor='r', sw=6); emoji(cr, em, 185, -6, 64, a)
        cr.restore()
    k = pop(t, 2.2) * (1 + 0.06 * math.sin(t * 5))
    cr.save(); cr.translate(540, 125); cr.scale(k, k)
    cr.new_path(); cr.arc(0, 0, 50, 0, 2 * math.pi); cr.set_source_rgba(*VIOLET[:3], a); cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(5); cr.stroke()
    ptext(cr, 'VS', 0, 17, 44, WHITE, a, sw=5)
    cr.restore()

# ---------- intro / outro ----------
def draw_intro(cr, t):
    I = TL['intro']
    if t > I['end'] + 0.4: return
    out = 1 - ease_io(prog(t, I['end'] - 0.2, I['end'] + 0.3))
    # silhouettes slide in
    for side, sx, d in (('ca', 270, -1), ('us', 810, 1)):
        k = ease_out(prog(t, 0.0, 0.6))
        cx = sx + d * (1 - k) * 600
        cr.new_path(); shape_path(cr, side, cx, 820, G.scale * 0.95)
        cr.set_source_rgba(*SIDE[side][:3], 0.85 * out); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, 0.9 * out); cr.set_line_width(3); cr.stroke()
    # names
    for side, x, lab, t0 in (('ca', 270, 'CANADA', 0.25), ('us', 810, 'USA', 0.45)):
        k = pop(t, t0, 0.45, 3)
        cr.save(); cr.translate(x, 470); cr.rotate(-0.06 if side == 'ca' else 0.06); cr.scale(k, k)
        ptext(cr, lab, 0, 0, fit(cr, lab, 120, 480), SIDE[side], out); cr.restore()
    # VS slam
    k = prog(t, 0.7, 1.0)
    if k > 0:
        s = lerp(3.5, 1.0, ease_out(k)) * (1 + 0.05 * math.sin(t * 8))
        shake = 14 * math.sin(t * 80) * (1 - prog(t, 1.0, 1.4))
        cr.save(); cr.translate(540 + shake, 820); cr.scale(s, s); cr.rotate(-0.08)
        cr.new_path(); cr.arc(0, 0, 120, 0, 2 * math.pi); cr.set_source_rgba(*GOLD[:3], out * clamp(k * 3)); cr.fill()
        ptext(cr, 'VS', 0, 42, 130, WHITE, out * clamp(k * 3), sw=12)
        cr.restore()
        fl = 1 - prog(t, 0.95, 1.35)
        if 0 < fl < 1: cr.set_source_rgba(1, 1, 1, 0.3 * fl); cr.paint()
    l1 = I['lines'][1]
    k = pop(t, l1[0], 0.4, 3)
    if k > 0.01:
        cr.save(); cr.translate(540, 1270); cr.scale(k, k)
        txt = '8 ROUNDS · 1 WINNER'; w = tw(cr, txt, 56)
        rrect(cr, -w / 2 - 40, -62, w + 80, 96, 48); cr.set_source_rgba(*VIOLET[:3], out); cr.fill()
        ptext(cr, txt, 0, 4, 56, WHITE, out, sw=6); cr.restore()
    l2 = I['lines'][2]
    k = pop(t, l2[0], 0.4, 3)
    if k > 0.01:
        cr.save(); cr.translate(540, 1420); cr.rotate(-0.05); cr.scale(k, k)
        ptext(cr, "LET'S SETTLE THIS!", 0, 0, fit(cr, "LET'S SETTLE THIS!", 92, 980), GOLD, out); cr.restore()
        emoji(cr, '🥊', 130, 1330, 110 * k, out, rot=0.3 * math.sin(t * 6))
        emoji(cr, '🥊', 950, 1330, 110 * k, out, rot=-0.3 * math.sin(t * 6))

def draw_outro(cr, t):
    O = TL['outro']
    if t < O['start']: return
    a = ease_out(prog(t, O['start'], O['start'] + 0.4))
    ls = O['lines']
    cr.set_source_rgba(*NAVY2[:3], 0.55 * a); cr.paint()
    k = pop(t, ls[0][0] + 0.2, 0.5, 3)
    cr.save(); cr.translate(540, 640); cr.scale(k, k)
    ptext(cr, '4', -230, 120, 330, RED, a, sw=22); ptext(cr, '-', 0, 100, 260, WHITE, a, sw=18); ptext(cr, '4', 230, 120, 330, BLUE, a, sw=22)
    cr.restore()
    k = pop(t, ls[1][0], 0.45, 3.5)
    if k > 0.01:
        sh = 10 * math.sin(t * 70) * (1 - prog(t, ls[1][0] + 0.3, ls[1][0] + 0.7))
        cr.save(); cr.translate(540 + sh, 920); cr.rotate(-0.06); cr.scale(k, k)
        ptext(cr, "IT'S A TIE!", 0, 0, fit(cr, "IT'S A TIE!", 150, 1000), GOLD, a, sw=16); cr.restore()
        emoji(cr, '😱', 110, 760, 120 * k, a, rot=0.2 * math.sin(t * 5)); emoji(cr, '🤯', 970, 760, 120 * k, a, rot=-0.2 * math.sin(t * 5))
    k = pop(t, ls[2][0], 0.4, 3)
    if k > 0.01:
        cr.save(); cr.translate(540, 1080); cr.scale(k, k)
        ptext(cr, 'YOU DECIDE', 0, 0, 100, WHITE, a); cr.restore()
        emoji(cr, '👇', 540, 1180 + 14 * abs(math.sin(t * 5)), 90 * k, a)
    for side, x, lab, em, t0 in (('ca', 290, 'CANADA', '🍁', ls[3][0]), ('us', 790, 'USA', '🦅', ls[3][0] + 0.5)):
        k = pop(t, t0, 0.45, 3) * (1 + 0.06 * math.sin(t * 7 + (0 if side == 'ca' else math.pi)))
        if k <= 0.01: continue
        cr.save(); cr.translate(x, 1330); cr.scale(k, k)
        rrect(cr, -220, -70, 440, 140, 70); cr.set_source_rgba(*SIDE[side][:3], a); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(5); cr.stroke()
        emoji(cr, em, -140, -4, 80, a); ptext(cr, lab, 40, 22, fit(cr, lab, 66, 280), WHITE, a, sw=7)
        cr.restore()
    k = pop(t, ls[4][0], 0.4, 3)
    if k > 0.01:
        cr.save(); cr.translate(540, 1480); cr.scale(k, k)
        txt = 'COMMENT BELOW'; w = tw(cr, txt, 52)
        rrect(cr, -w / 2 - 90, -58, w + 180, 92, 46); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
        ptext(cr, txt, 30, 6, 52, INK, a, sw=0, shadow=False); emoji(cr, '💬', -w / 2 - 30, -10, 66, a)
        cr.restore()

# ---------- rounds ----------
def side_k(R, side, t): return prog(t, R['reveal'][side], R['reveal'][side] + 1.1)

def value_text(cr, R, side, t, y=1260):
    k = side_k(R, side, t)
    if k <= 0:
        q = pop(t, R['start'] + 0.6, 0.4)
        ptext(cr, '?', CX[side], y + 20, 110 * q, WHITE, 0.6 * clamp(q), sw=10)
        return
    target, fmt = R[side]
    v = target * ease_out(k)
    s = 1 + 0.25 * (1 - ease_out(prog(t, R['reveal'][side] + 1.0, R['reveal'][side] + 1.4))) * (k >= 1)
    txt = fmt(v)
    cr.save(); cr.translate(CX[side], y); cr.scale(s * pop(t, R['reveal'][side], 0.35), s * pop(t, R['reveal'][side], 0.35))
    ptext(cr, txt, 0, 20, fit(cr, txt, 76, 480), GOLD if R['win'] == side and t > R['reveal']['win'] else WHITE, 1, sw=9)
    cr.restore()

def viz_map(cr, R, t, coast=False):
    for side in ('ca', 'us'):
        k = side_k(R, side, t)
        if k <= 0: continue
        s = G.scale * (0.98 if not coast else 0.98)
        if not coast:
            sc = ease_back(clamp(k * 1.6), 2)
            cr.save(); cr.translate(CX[side], 820); cr.scale(sc, sc)
            cr.new_path(); shape_path(cr, side, 0, 0, s)
            cr.set_source_rgba(*SIDE[side][:3], 0.9); cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, 1); cr.set_line_width(3 / max(sc, 0.05)); cr.stroke()
            cr.restore()
        else:
            n = int(G.npts[side] * ease_io(clamp(k * 1.2)))
            cr.new_path(); shape_path(cr, side, CX[side], 820, s)
            cr.set_source_rgba(*SIDE[side][:3], 0.25); cr.fill()
            cr.new_path(); shape_path(cr, side, CX[side], 820, s, upto=n)
            for lw, al in ((14, 0.25), (6, 0.6), (2.5, 1)):
                cr.set_source_rgba(*(MINT if side == 'ca' else hexc('#7FD8FF'))[:3], al); cr.set_line_width(lw); cr.stroke_preserve()
            cr.new_path()
    if coast:
        emoji(cr, '🌊', 540, 1120, 90 * pop(t, R['start'] + 0.8), 1, rot=0.2 * math.sin(t * 3))

def person(cr, x, y, s, col, a):
    cr.new_path(); cr.arc(x, y - 18 * s, 11 * s, 0, 2 * math.pi); cr.set_source_rgba(*col[:3], a); cr.fill()
    rrect(cr, x - 17 * s, y - 4 * s, 34 * s, 30 * s, 14 * s); cr.fill()

def viz_people(cr, R, t):
    for side in ('ca', 'us'):
        k = side_k(R, side, t)
        n = int(round(R[side][0] / 10))
        cols, size = 6, 62
        for i in range(n):
            pk = pop(t, R['reveal'][side] + 0.05 + i * min(0.06, 1.6 / n), 0.3, 3)
            if pk <= 0.01: continue
            r, c = divmod(i, cols)
            x = CX[side] - (cols - 1) * size / 2 + c * size
            y = 1120 - r * size * 1.05
            person(cr, x, y, 1.35 * pk, SIDE[side] if side == 'us' else RED, 1)
        if k > 0:
            ptext(cr, '1 = 10M people', CX[side], 1190, 28, WHITE, clamp(k * 2) * 0.8, fam='Poppins SemiBold', sw=4)

def viz_bars(cr, R, t, emo='💰', vmax=None, base=1170, hmax=560):
    vmax = vmax or max(R['ca'][0], R['us'][0])
    for side in ('ca', 'us'):
        k = side_k(R, side, t)
        if k <= 0: continue
        h = hmax * R[side][0] / vmax * ease_back(clamp(k * 1.2), 1.6)
        x = CX[side] - 110
        rrect(cr, x, base - max(h, 24), 220, max(h, 24), 26)
        g = cairo.LinearGradient(0, base - h, 0, base)
        c1, c2 = (RED, RED2) if side == 'ca' else (BLUE, BLUE2)
        g.add_color_stop_rgba(0, *c1[:3], 1); g.add_color_stop_rgba(1, *c2[:3], 1)
        cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, 0.9); cr.set_line_width(4); cr.stroke()
        emoji(cr, emo, CX[side], base - max(h, 24) - 60 + 8 * math.sin(t * 6 + (0 if side == 'ca' else 2)), 90 * pop(t, R['reveal'][side] + 0.5), 1)

def viz_mountain(cr, R, t):
    base = 1170
    for side in ('ca', 'us'):
        k = side_k(R, side, t)
        if k <= 0: continue
        h = 600 * R[side][0] / 6190 * ease_out(clamp(k * 1.2))
        x = CX[side]
        cr.new_path(); cr.move_to(x - 220, base); cr.line_to(x - 30, base - h * 0.97); cr.line_to(x, base - h)
        cr.line_to(x + 40, base - h * 0.93); cr.line_to(x + 220, base); cr.close_path()
        g = cairo.LinearGradient(0, base - h, 0, base)
        c1, c2 = (RED, RED2) if side == 'ca' else (BLUE, BLUE2)
        g.add_color_stop_rgba(0, *c1[:3], 1); g.add_color_stop_rgba(1, *c2[:3], 1)
        cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, 0.9); cr.set_line_width(4); cr.stroke()
        cr.new_path(); cr.move_to(x - 60, base - h * 0.82); cr.line_to(x - 30, base - h * 0.97); cr.line_to(x, base - h)
        cr.line_to(x + 40, base - h * 0.93); cr.line_to(x + 75, base - h * 0.8); cr.line_to(x + 30, base - h * 0.86)
        cr.line_to(x, base - h * 0.8); cr.line_to(x - 25, base - h * 0.86); cr.close_path()
        cr.set_source_rgba(1, 1, 1, 0.95); cr.fill()
        fk = pop(t, R['reveal'][side] + 1.0, 0.4, 3)
        if fk > 0.01:
            cr.new_path(); cr.move_to(x, base - h); cr.line_to(x, base - h - 70 * fk); cr.set_source_rgba(1, 1, 1, 1); cr.set_line_width(4); cr.stroke()
            cr.new_path(); cr.move_to(x, base - h - 70 * fk); cr.line_to(x + 50 * fk, base - h - 55 * fk); cr.line_to(x, base - h - 40 * fk)
            cr.close_path(); cr.set_source_rgba(*GOLD[:3], 1); cr.fill()
        name = 'MT LOGAN' if side == 'ca' else 'DENALI'
        ptext(cr, name, x, base - 30, 36, WHITE, clamp(k * 2), fam='Poppins ExtraBold', sw=5)

def viz_moon(cr, R, t):
    for side in ('ca', 'us'):
        k = side_k(R, side, t)
        x, y, r = CX[side], 830, 170
        mk = pop(t, R['start'] + 0.5, 0.5)
        if mk <= 0.01: continue
        g = cairo.RadialGradient(x - 50, y - 60, 20, x, y, r * mk)
        g.add_color_stop_rgba(0, 0.95, 0.95, 0.9, 1); g.add_color_stop_rgba(1, 0.6, 0.6, 0.62, 1)
        cr.new_path(); cr.arc(x, y, r * mk, 0, 2 * math.pi); cr.set_source(g); cr.fill()
        for cx, cy, cr_ in ((-60, -40, 30), (50, 30, 22), (-20, 70, 18), (70, -70, 14), (-90, 40, 12)):
            cr.new_path(); cr.arc(x + cx * mk, y + cy * mk, cr_ * mk, 0, 2 * math.pi); cr.set_source_rgba(0.5, 0.5, 0.55, 0.6); cr.fill()
        if k <= 0: continue
        if side == 'us':
            for i in range(6):
                fk = pop(t, R['reveal']['us'] + 0.3 + i * 0.15, 0.3, 3)
                if fk <= 0.01: continue
                ang = -math.pi / 2 + (i - 2.5) * 0.45
                fx, fy = x + math.cos(ang) * (r - 40), y + math.sin(ang) * (r - 40) + 30
                cr.new_path(); cr.move_to(fx, fy); cr.line_to(fx, fy - 60 * fk); cr.set_source_rgba(1, 1, 1, 1); cr.set_line_width(4); cr.stroke()
                rrect(cr, fx, fy - 60 * fk, 44 * fk, 28 * fk, 4); cr.set_source_rgba(*BLUE[:3], 1); cr.fill()
        else:
            emoji(cr, '🦾', x, y + 10, 150 * pop(t, R['reveal']['ca'] + 1.4, 0.45, 3), 1, rot=0.2 * math.sin(t * 4))
            kk = pop(t, R['reveal']['ca'] + 1.6, 0.4, 3)
            if kk > 0.01:
                cr.save(); cr.translate(x, y + 230); cr.scale(kk, kk); cr.rotate(-0.06)
                ptext(cr, 'CANADARM!', 0, 0, 44, GOLD, 1, sw=6); cr.restore()

def viz_pie(cr, R, t):
    x, y, r = 540, 830, 300
    ka, ku = side_k(R, 'ca', t), side_k(R, 'us', t)
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.08); cr.set_line_width(110); cr.stroke()
    a0 = -math.pi / 2
    sweep_ca = 2 * math.pi * 0.70 * ease_io(ka)
    if sweep_ca > 0:
        cr.new_path(); cr.arc(x, y, r, a0, a0 + sweep_ca); cr.set_source_rgba(*RED[:3], 1); cr.set_line_width(110); cr.stroke()
    sweep_us = 2 * math.pi * 0.30 * ease_io(ku)
    if sweep_us > 0:
        cr.new_path(); cr.arc(x, y, r, a0 + 2 * math.pi * 0.70, a0 + 2 * math.pi * 0.70 + sweep_us)
        cr.set_source_rgba(*BLUE[:3], 1); cr.set_line_width(110); cr.stroke()
    emoji(cr, '🍁', x, y - 10, 210 * pop(t, R['start'] + 0.6, 0.5, 3), 1, rot=0.15 * math.sin(t * 3))
    ptext(cr, "OF THE WORLD'S SYRUP", x, y + 140, 30, WHITE, clamp(ka * 2), fam='Poppins ExtraBold', sw=4)

def draw_round(cr, R, t):
    if not (R['start'] - 0.05 <= t <= R['end'] + 0.05): return
    a_in = ease_out(prog(t, R['start'], R['start'] + 0.25))
    out = 1 - ease_io(prog(t, R['end'] - 0.3, R['end']))
    al = a_in * out
    # banner
    k = prog(t, R['start'], R['start'] + 0.35)
    s = lerp(2.6, 1.0, ease_out(k))
    shake = 10 * math.sin(t * 70) * (1 - prog(t, R['start'] + 0.35, R['start'] + 0.7))
    cr.save(); cr.translate(540 + shake, 300); cr.scale(s, s); cr.rotate(-0.04)
    lab = f"ROUND {R['i'] + 1}" if R['i'] < 7 else 'FINAL ROUND'
    w = tw(cr, lab, 54); R['_pill_w'] = w
    rrect(cr, -w / 2 - 36, -56, w + 72, 84, 42); cr.set_source_rgba(*GOLD[:3], al * clamp(k * 3)); cr.fill()
    ptext(cr, lab, 0, 6, 54, INK, al * clamp(k * 3), sw=0, shadow=False)
    cr.restore()
    kk = pop(t, R['start'] + 0.2, 0.45, 3)
    if kk > 0.01:
        cr.save(); cr.translate(540, 445); cr.scale(kk, kk)
        size = fit(cr, R['title'], 104, 820)
        ptext(cr, R['title'], 0, 0, size, WHITE, al, sw=12)
        cr.restore()
        emoji(cr, R['emoji'], 540 + R.get('_pill_w', 300) / 2 + 135, 285, 96 * kk, al, rot=0.25 * math.sin(t * 4))
    # visuals
    cr.push_group()
    {'map': lambda: viz_map(cr, R, t), 'coast': lambda: viz_map(cr, R, t, coast=True), 'people': lambda: viz_people(cr, R, t),
     'bars': lambda: viz_bars(cr, R, t), 'mountain': lambda: viz_mountain(cr, R, t),
     'life': lambda: viz_bars(cr, R, t, emo='❤️', vmax=90), 'moon': lambda: viz_moon(cr, R, t),
     'pie': lambda: viz_pie(cr, R, t)}[R['viz']]()
    for side in ('ca', 'us'):
        if R['viz'] != 'pie' or True: value_text(cr, R, side, t)
        lab = 'CANADA' if side == 'ca' else 'USA'
        ptext(cr, lab, CX[side], 1350, 34, SIDE[side], 1, fam='Poppins ExtraBold', sw=5)
    # winner
    tw0 = R['reveal']['win']
    if t >= tw0:
        lose = 'us' if R['win'] == 'ca' else 'ca'
        dk = ease_out(prog(t, tw0, tw0 + 0.3))
        cr.save(); cr.rectangle(0 if lose == 'ca' else W / 2, 500, W / 2, 900)
        cr.set_source_rgba(*NAVY2[:3], 0.55 * dk); cr.fill(); cr.restore()
    cr.pop_group_to_source(); cr.paint_with_alpha(al)
    if t >= tw0:
        sk = prog(t, tw0, tw0 + 0.3)
        sc = lerp(2.2, 1.0, ease_out(sk))
        x = CX[R['win']] if R['viz'] != 'pie' else 540
        y = 640 if R['viz'] != 'pie' else 470
        cr.save(); cr.translate(x, y); cr.rotate(-0.12); cr.scale(sc, sc)
        w = tw(cr, 'WINNER!', 64)
        rrect(cr, -w / 2 - 30, -62, w + 60, 92, 20); cr.set_source_rgba(*GOLD[:3], al * clamp(sk * 3)); cr.fill_preserve()
        cr.set_source_rgba(*INK, al); cr.set_line_width(6); cr.stroke()
        ptext(cr, 'WINNER!', 0, 4, 64, INK, al * clamp(sk * 3), sw=0, shadow=False)
        cr.restore()
        emoji(cr, '🏆', x + 190 if R['win'] == 'ca' else x - 190, y - 30, 90 * pop(t, tw0 + 0.15, 0.4, 3), al)
        confetti(cr, t, tw0, R['i'] + 3, CX[R['win']], R['win'])

def confetti(cr, t, t0, seed, cx, side):
    u = t - t0
    if not 0 <= u <= 2.0: return
    rng = np.random.default_rng(seed)
    cols = [SIDE[side], GOLD, WHITE, MINT if side == 'ca' else hexc('#7FD8FF')]
    for _ in range(80):
        ang = rng.uniform(-math.pi, 0); sp = rng.uniform(500, 1400)
        x = cx + math.cos(ang) * sp * u * (1 - 0.3 * u); y = 700 + math.sin(ang) * sp * u * (1 - 0.3 * u) + 1000 * u * u
        cr.save(); cr.translate(x, y); cr.rotate(rng.uniform(0, 6) + u * rng.uniform(-10, 10))
        cr.rectangle(-10, -5, 20, 10); c = cols[rng.integers(len(cols))]
        cr.set_source_rgba(*c[:3], clamp(1.6 - u)); cr.fill(); cr.restore()

def draw_wipe(cr, t):
    for R in TL['rounds'][1:] + [TL['outro']]:
        u = prog(t, R['start'] - 0.25, R['start'] + 0.25)
        if 0 < u < 1:
            x = lerp(-W * 1.6, W * 1.6, ease_io(u))
            cr.save(); cr.translate(x, 0)
            for j, col in enumerate((RED, GOLD, BLUE)):
                cr.new_path(); off = j * 140
                cr.move_to(off - 300, H); cr.line_to(off + 300, 0); cr.line_to(off + 430, 0); cr.line_to(off - 170, H); cr.close_path()
                cr.set_source_rgba(*col[:3], 1); cr.fill()
            cr.restore()

def draw_captions(cr, t):
    for l0, l1, s, spk, tag in TL['lines']:
        if not (l0 <= t < l1 + 0.18): continue
        words = s.split()
        wts = np.array([len(w.strip('.,!?')) + 2.5 for w in words], float)
        edges = l0 + (l1 - l0) * np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
        cur = int(np.clip(np.searchsorted(edges, t, side='right') - 1, 0, len(words) - 1))
        g0 = (cur // 3) * 3; group = [w.upper() for w in words[g0:g0 + 3]]
        size = 74; face(cr, size); space = cr.text_extents(' ').x_advance
        widths = [cr.text_extents(u).x_advance * (1.14 if g0 + j == cur else 1.0) for j, u in enumerate(group)]
        total = sum(widths) + space * (len(group) - 1); sc = min(1.0, 900 / total)
        # speaker badge
        em = '🍁' if spk == 'ca' else '🦅'
        bx = 540 - total * sc / 2 - 70 if spk == 'ca' else 540 + total * sc / 2 + 70
        emoji(cr, em, bx, 1620 + 6 * math.sin(t * 8), 80, 1)
        cr.save(); cr.translate(540, 1650); cr.scale(sc, sc)
        x = -total / 2
        for j, (u, w) in enumerate(zip(group, widths)):
            wi = g0 + j; active = wi == cur
            cr.save(); cr.translate(x + w / 2, 0)
            if active:
                k = ease_back(prog(t, edges[wi], edges[wi] + 0.15), 3); cr.scale(1 + 0.14 * k, 1 + 0.14 * k); cr.rotate(-0.03)
            col = (GOLD if j % 2 else SIDE[spk]) if active else WHITE
            ptext(cr, u, 0, 0, size, col, 1.0 if wi <= cur else 0.7, sw=11)
            cr.restore(); x += w + space
        cr.restore(); return

def render_frame(cr, t):
    draw_bg(cr, t)
    draw_intro(cr, t)
    for R in TL['rounds']: draw_round(cr, R, t)
    draw_scoreboard(cr, t)
    draw_outro(cr, t)
    draw_captions(cr, t)
    draw_wipe(cr, t)
    f = prog(t, TL['dur'] - 0.4, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- audio ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(12)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 126
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    for bi in range(int(dur / beat)):
        t0 = bi * beat; ch = chords[(bi // 4) % 4]; L = np.arange(int(0.3 * SR)) / SR
        put(music, t0, 0.45 * np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-L * 40)) / SR) * np.exp(-L * 11))
        if bi % 2 == 1:  # clap
            M = np.arange(int(0.12 * SR)); nz = rng.standard_normal(len(M))
            put(music, t0, 0.12 * np.convolve(nz, [1, -1], 'same') * np.exp(-M / SR * 30))
        M = np.arange(int(0.04 * SR)); put(music, t0 + beat / 2, 0.05 * np.diff(rng.standard_normal(len(M) + 1)) * np.exp(-M / SR * 80))
        mt = np.arange(int(beat * 0.9 * SR)) / SR
        for h in (0, 0.5):
            put(music, t0 + h * beat, 0.1 * np.tanh(4 * np.sin(2 * np.pi * note(ch[0] - 24) * mt[:len(mt) // 2])) * np.exp(-mt[:len(mt) // 2] * 5))
        if bi % 4 in (0, 3):  # synth stab
            st = np.arange(int(0.18 * SR)) / SR
            put(music, t0 + (0.5 * beat if bi % 4 == 3 else 0), sum(0.03 * np.sign(np.sin(2 * np.pi * note(m + 12) * st)) for m in ch) * np.exp(-st * 14))
    music = np.tanh(music * 1.2) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp):
        L = np.arange(int(1.2 * SR)) / SR
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(40 + 100 * np.exp(-L * 14)) / SR) * np.exp(-L * 4))
    def bell(t0):
        L = np.arange(int(0.9 * SR)) / SR
        sig = sum(np.sin(2 * np.pi * f * L) * np.exp(-L * d) for f, d in ((1760, 5), (2637, 6), (4186, 9)))
        put(fx, t0, 0.1 * sig); put(fx, t0 + 0.18, 0.1 * sig)
    def whoosh(t0):
        nz = rng.standard_normal(int(0.6 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2
        put(fx, t0, 0.2 * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def cheer(t0):
        L = int(1.6 * SR); nz = rng.standard_normal(L); lt = np.arange(L) / SR
        band = np.convolve(nz, np.ones(6) / 6, 'same') - np.convolve(nz, np.ones(60) / 60, 'same')
        env = np.minimum(1, lt / 0.15) * np.exp(-lt * 1.6)
        put(fx, t0, 0.35 * band * env)
        for c in range(10):  # claps
            ct = t0 + 0.1 + c * 0.11 + rng.uniform(0, 0.05); M = np.arange(int(0.05 * SR))
            put(fx, ct, 0.08 * rng.standard_normal(len(M)) * np.exp(-M / SR * 60))
    def tick(t0):
        L = np.arange(int(0.05 * SR)) / SR; put(fx, t0, 0.15 * np.sin(2 * np.pi * 1500 * L) * np.exp(-L * 70))
    boom(1.0, 0.8)
    for R in T['rounds']:
        whoosh(R['start'] - 0.3); bell(R['start'] + 0.05); boom(R['start'] + 0.3, 0.35)
        for side in ('ca', 'us'):
            for k in range(8): tick(R['reveal'][side] + k * 0.12)
        cheer(R['reveal']['win'] + 0.1); boom(R['reveal']['win'], 0.4)
    O = T['outro']; whoosh(O['start'] - 0.3)
    roll0 = O['lines'][0][0] - 0.2  # drumroll into the tie
    for k in range(int(1.2 / 0.045)):
        M = np.arange(int(0.04 * SR)); put(fx, roll0 + k * 0.045, 0.07 * (k / 26) * rng.standard_normal(len(M)) * np.exp(-M / SR * 50))
    boom(O['lines'][1][0], 0.9); cheer(O['lines'][1][0] + 0.1)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.9
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.62 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 1.0)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

# ---------- render ----------
def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                           '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait()
    return out

def main():
    global G, TL
    data_dir, out = sys.argv[1:3]
    TL = build(EdgeVoice(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_vs')))
    G = Geo(data_dir)
    print(f"duration {TL['dur']:.1f}s")
    for R in TL['rounds']: print(f"  {R['key']:7s} {R['start']:6.2f}-{R['end']:6.2f}  win {R['win']}  {R['score']}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','):
            render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]
    make_audio(TL, base + '.wav')
    n = int(TL['dur'] * FPS); workers = os.cpu_count() or 4
    bounds = np.linspace(0, n, workers * 2 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt',
                    '-i', base + '.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
