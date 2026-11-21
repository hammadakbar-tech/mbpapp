"""'WHERE WOULD YOU LIVE?' space would-you-rather reel (9:16) + matching static graphics.
Four worlds, facts and reaction emojis popping on the narrator's spoken words, recap grid, comment CTA.
Usage: python3 space_choice.py <out.mp4> [--preview t1,t2,...] | --graphics <out_dir>
"""
import asyncio, hashlib, json, math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import vs
from vs import ptext, rrect, tw, fit, face
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

def emoji(cr, e, *a, **k): vs.emoji(cr, e.replace('️', ''), *a, **k)

W, H, FPS = 1080, 1920, 30
VOICE, RATE = 'en-US-AvaNeural', '+6%'
WHITE, GOLD, INK = hexc('#FFFFFF'), hexc('#FFD60A'), (0.03, 0.02, 0.08)
CYAN, PINK, LIME, VIOLET = hexc('#3DE0FF'), hexc('#FF4FA3'), hexc('#8CFF5A'), hexc('#9B6BFF')

WORLDS = {
    'A': dict(name='VENUS', kind='venus', col=hexc('#FFB347'), key='465°C · ACID CLOUDS',
              text="Option A: Venus. It's over four hundred and sixty degrees, the air pressure would crush you, and the clouds are made of sulfuric acid. Oh, and a day lasts longer than a year.",
              chips=[('🌡️', '465°C', 'sixty'), ('🗜️', "92× EARTH'S PRESSURE", 'crush'), ('☁️', 'SULFURIC ACID CLOUDS', 'acid'), ('🔄', 'A DAY > A YEAR', 'year')],
              react=[('🥵', 'sixty'), ('😵', 'crush'), ('🤢', 'acid'), ('🤯', 'year')]),
    'B': dict(name='MARS', kind='mars', col=hexc('#FF5A36'), key='−63°C · THIN AIR',
              text="Option B: Mars. It's minus sixty degrees on average, the air is far too thin to breathe, and dust storms can swallow the whole planet. But... the sunsets are blue.",
              chips=[('🥶', '−63°C AVERAGE', 'minus'), ('💨', "1% OF EARTH'S AIR", 'breathe'), ('🌪️', 'PLANET-WIDE DUST STORMS', 'swallow'), ('🌅', 'BLUE SUNSETS', 'blue')],
              react=[('🥶', 'minus'), ('😮', 'breathe'), ('😱', 'swallow'), ('😍', 'blue')]),
    'C': dict(name='TITAN', kind='titan', col=hexc('#FFC24B'), key='METHANE LAKES · LOW GRAVITY',
              text="Option C: Titan, Saturn's biggest moon. It's minus one hundred eighty degrees, with lakes of liquid methane. But the gravity is so low and the air so thick, you could strap on wings... and fly.",
              chips=[('🥶', '−179°C', 'minus'), ('🛢️', 'LIQUID METHANE LAKES', 'methane'), ('🪶', '14% OF EARTH’S GRAVITY', 'gravity'), ('🦅', 'YOU COULD FLY', 'fly')],
              react=[('🥶', 'minus'), ('😳', 'methane'), ('🤩', 'fly')]),
    'D': dict(name='EUROPA', kind='europa', col=hexc('#7FD8FF'), key='HIDDEN OCEAN · RADIATION',
              text="Option D: Europa, a moon of Jupiter. Under its ice hides an ocean with twice as much water as Earth. But Jupiter's radiation would give you a deadly dose in about a day.",
              chips=[('🧊', 'MILES OF ICE', 'ice'), ('🌊', "2× EARTH'S WATER", 'twice'), ('☢️', 'DEADLY RADIATION', 'radiation')],
              react=[('🤯', 'twice'), ('💀', 'deadly')]),
}
ORDER = ['A', 'B', 'C', 'D']
LETTER_COL = {'A': PINK, 'B': CYAN, 'C': GOLD, 'D': LIME}
BEATS = [('hook', "You have to move to one of these four worlds. Where would you live?")] + \
        [(k, WORLDS[k]['text']) for k in ORDER] + \
        [('recap', "So... A, B, C, or D?"),
         ('cta', "I'm choosing Titan, for the low gravity. Which one are you choosing? Tell me why in the comments!")]
TILE = {'A': (290, 760), 'B': (790, 760), 'C': (290, 1310), 'D': (790, 1310)}

# ---------- voice with word timings ----------
class WordVoice:
    def __init__(self, cache): self.cache = cache; os.makedirs(cache, exist_ok=True)
    def get(self, text):
        key = hashlib.md5(f'wb|{VOICE}|{RATE}|{text}'.encode()).hexdigest()
        pa, pw = os.path.join(self.cache, key + '.npy'), os.path.join(self.cache, key + '.json')
        if os.path.exists(pa) and os.path.exists(pw): return np.load(pa), json.load(open(pw))
        import edge_tts
        async def run():
            buf, words = bytearray(), []
            async for ch in edge_tts.Communicate(text, VOICE, rate=RATE, proxy=os.environ.get('HTTPS_PROXY'), boundary='WordBoundary').stream():
                if ch['type'] == 'audio': buf.extend(ch['data'])
                elif ch['type'] == 'WordBoundary': words.append((ch['offset'] / 1e7, (ch['offset'] + ch['duration']) / 1e7, ch['text']))
            return bytes(buf), words
        mp3, words = asyncio.run(run())
        pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', 'pipe:0', '-f', 's16le', '-ac', '1', '-ar', str(SR), 'pipe:1'],
                             input=mp3, capture_output=True, check=True).stdout
        a = np.frombuffer(pcm, '<i2').astype(np.float32) / 32767
        nz = np.nonzero(np.abs(a) > 0.01)[0]; i0 = max(nz[0] - 200, 0); a = a[i0:nz[-1] + 1200]; sh = i0 / SR
        words = [(max(0.0, s - sh), max(0.0, e - sh), x) for s, e, x in words]
        np.save(pa, a); json.dump(words, open(pw, 'w')); return a, words

def norm(s): return re.sub(r"[^a-z0-9]", '', s.lower())
TL = None
_missing = set()

def build(voice):
    t, beats, clips = 0.0, [], []
    lead = {'hook': 0.15, 'recap': 0.3, 'cta': 0.2}
    tail = {'hook': 0.5, 'recap': 0.5, 'cta': 2.4}
    for key, text in BEATS:
        a, words = voice.get(text)
        b = dict(key=key, text=text, start=t, l0=t + lead.get(key, 0.55))
        b['l1'] = b['l0'] + len(a) / SR
        b['words'] = [(b['l0'] + s, b['l0'] + e, x) for s, e, x in words]; b['tokens'] = text.split()
        clips.append((b['l0'], a)); t = b['l1'] + tail.get(key, 0.6); b['end'] = t; beats.append(b)
    return dict(beats=beats, by={b['key']: b for b in beats}, clips=clips, dur=t)

def bt(k): return TL['by'][k]
def w(key, word, n=0, end=False):
    q, hits = norm(word), []
    for s, e, x in bt(key)['words']:
        if any(norm(p).startswith(q) for p in x.split()): hits.append((s, e))
    if len(hits) > n: return hits[n][1] if end else hits[n][0]
    if (key, word) not in _missing: _missing.add((key, word)); print(f'  ! no word "{word}" in {key}', file=sys.stderr)
    return bt(key)['l0']

def pop_k(t, t0, d=0.35): return max(1e-3, ease_back(prog(t, t0, t0 + d), 2.8))

# ---------- space ----------
rng0 = np.random.default_rng(42)
STARS = [(rng0.uniform(0, W), rng0.uniform(0, H), rng0.uniform(0.6, 2.6), rng0.uniform(0, 6.28), rng0.uniform(0.5, 2.0)) for _ in range(260)]

def draw_space(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgba(0, 0.04, 0.02, 0.12, 1); g.add_color_stop_rgba(1, 0.01, 0.01, 0.04, 1)
    cr.set_source(g); cr.paint()
    for cx, cy, r, col in ((250 + 60 * math.sin(t * 0.1), 500, 700, (0.45, 0.15, 0.7)), (850, 1450 + 50 * math.cos(t * 0.08), 800, (0.1, 0.3, 0.75))):
        g = cairo.RadialGradient(cx, cy, 0, cx, cy, r); g.add_color_stop_rgba(0, *col, 0.28); g.add_color_stop_rgba(1, *col, 0)
        cr.set_source(g); cr.paint()
    for x, y, r, ph, sp in STARS:
        y2 = (y + t * 6 * r) % H
        a = 0.35 + 0.6 * (0.5 + 0.5 * math.sin(t * sp + ph))
        cr.new_path(); cr.arc(x, y2, r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, a); cr.fill()

def planet(cr, kind, cx, cy, r, t, a=1.0):
    if r < 2 or a <= 0: return
    base = {'venus': ((0.98, 0.86, 0.6), (0.72, 0.5, 0.25)), 'mars': ((0.86, 0.36, 0.16), (0.45, 0.14, 0.06)),
            'titan': ((0.95, 0.72, 0.32), (0.6, 0.38, 0.1)), 'europa': ((0.96, 0.93, 0.86), (0.72, 0.64, 0.52))}[kind]
    g = cairo.RadialGradient(cx, cy, r * 0.6, cx, cy, r * 1.6)
    glow = {'venus': (1, 0.8, 0.4), 'mars': (1, 0.35, 0.15), 'titan': (1, 0.7, 0.25), 'europa': (0.6, 0.85, 1)}[kind]
    g.add_color_stop_rgba(0, *glow, 0.45 * a); g.add_color_stop_rgba(1, *glow, 0)
    cr.set_source(g); cr.arc(cx, cy, r * 1.6, 0, 2 * math.pi); cr.fill()
    cr.save(); cr.new_path(); cr.arc(cx, cy, r, 0, 2 * math.pi); cr.clip()
    g = cairo.RadialGradient(cx - r * 0.35, cy - r * 0.35, r * 0.1, cx, cy, r)
    g.add_color_stop_rgba(0, *base[0], a); g.add_color_stop_rgba(1, *base[1], a)
    cr.set_source(g); cr.paint()
    rot = t * 0.12
    rng = np.random.default_rng({'venus': 1, 'mars': 2, 'titan': 3, 'europa': 4}[kind])
    if kind in ('venus', 'titan'):
        for i in range(11):
            y = cy - r + (i + 0.5) * 2 * r / 11
            cr.new_path(); cr.move_to(cx - r, y)
            for k in range(41):
                x = cx - r + k * 2 * r / 40
                cr.line_to(x, y + r * 0.04 * math.sin(k * 0.5 + i * 1.7 + rot * 6))
            light = i % 2 == 0
            cr.set_source_rgba(*((1, 1, 1) if light else (0.4, 0.25, 0.1)), (0.18 if kind == 'venus' else 0.1) * a)
            cr.set_line_width(r * 0.12); cr.stroke()
    if kind == 'mars':
        for i in range(9):
            ex = cx - r + ((rng.uniform(0, 2) + rot) % 2.4 - 0.2) * r; ey = cy + rng.uniform(-0.7, 0.7) * r
            cr.save(); cr.translate(ex, ey); cr.scale(rng.uniform(0.3, 0.6) * r, rng.uniform(0.12, 0.25) * r)
            cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore(); cr.set_source_rgba(0.35, 0.1, 0.05, 0.45 * a); cr.fill()
        cr.save(); cr.translate(cx, cy - r * 0.92); cr.scale(r * 0.42, r * 0.16); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgba(1, 1, 1, 0.85 * a); cr.fill()
    if kind == 'europa':
        for i in range(16):
            x0 = cx - r + ((rng.uniform(0, 2) + rot) % 2.4 - 0.2) * r; y0 = cy + rng.uniform(-0.9, 0.9) * r
            cr.new_path(); cr.move_to(x0, y0)
            cr.curve_to(x0 + rng.uniform(-0.4, 0.4) * r, y0 + rng.uniform(-0.4, 0.4) * r, x0 + rng.uniform(-0.6, 0.6) * r,
                        y0 + rng.uniform(-0.6, 0.6) * r, x0 + rng.uniform(-0.9, 0.9) * r, y0 + rng.uniform(-0.5, 0.5) * r)
            cr.set_source_rgba(0.55, 0.32, 0.2, 0.55 * a); cr.set_line_width(r * 0.025); cr.stroke()
    g = cairo.LinearGradient(cx - r, cy - r * 0.6, cx + r, cy + r * 0.6)  # night side
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(0.55, 0, 0, 0, 0.15 * a); g.add_color_stop_rgba(1, 0, 0, 0.02, 0.82 * a)
    cr.set_source(g); cr.paint(); cr.restore()
    if kind == 'titan':  # thick hazy atmosphere
        g = cairo.RadialGradient(cx, cy, r * 0.95, cx, cy, r * 1.14)
        g.add_color_stop_rgba(0, 1, 0.7, 0.3, 0.55 * a); g.add_color_stop_rgba(1, 1, 0.7, 0.3, 0)
        cr.set_source(g); cr.arc(cx, cy, r * 1.14, 0, 2 * math.pi); cr.fill()
    cr.new_path(); cr.arc(cx, cy, r, math.pi * 0.75, math.pi * 1.6)  # rim light
    cr.set_source_rgba(1, 1, 1, 0.35 * a); cr.set_line_width(r * 0.03); cr.stroke()

# ---------- pieces ----------
def badge(cr, letter, x, y, r, a=1.0):
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*LETTER_COL[letter][:3], a); cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(r * 0.1); cr.stroke()
    ptext(cr, letter, x, y + r * 0.42, r * 1.25, INK, a, sw=0, shadow=False)

def tile(cr, letter, t, a=1.0, scale=1.0, highlight=0.0, at=None):
    cx, cy = at or TILE[letter]; wd = WORLDS[letter]
    cr.save(); cr.translate(cx, cy); cr.scale(scale, scale)
    rrect(cr, -230, -265, 460, 530, 40); cr.set_source_rgba(0.06, 0.04, 0.16, 0.82 * a); cr.fill_preserve()
    cr.set_source_rgba(*(GOLD if highlight > 0 else LETTER_COL[letter])[:3], a); cr.set_line_width(5 + 6 * highlight); cr.stroke()
    planet(cr, wd['kind'], 0, -40, 130, t, a)
    badge(cr, letter, -170, -205, 44, a)
    ptext(cr, wd['name'], 0, 165, fit(cr, wd['name'], 66, 400), WHITE, a, sw=8)
    ptext(cr, wd['key'], 0, 222, fit(cr, wd['key'], 30, 410, 'Poppins ExtraBold'), LETTER_COL[letter], a, fam='Poppins ExtraBold', sw=5)
    if highlight > 0:
        emoji(cr, '✅', 175, -205, 90 * highlight, a)
    cr.restore()

def title(cr, txt, y, size, t, t0, col=WHITE, a=1.0, x=540, maxw=1000):
    if t < t0 or a <= 0: return
    k = prog(t, t0, t0 + 0.25); s = lerp(2.2, 1.0, ease_out(k)); sh = 10 * math.sin(t * 70) * (1 - prog(t, t0 + 0.25, t0 + 0.55))
    cr.save(); cr.translate(x + sh, y); cr.rotate(-0.03); cr.scale(s, s)
    ptext(cr, txt, 0, 0, fit(cr, txt, size, maxw), col, a * clamp(k * 3), sw=size * 0.13); cr.restore()

def header(cr, t, current):
    ptext(cr, 'WHERE WOULD YOU LIVE?', 540, 110, 52, WHITE, 1, sw=7)
    for i, L in enumerate(ORDER):
        x = 540 + (i - 1.5) * 110
        on = L == current; done = ORDER.index(current) > i if current in ORDER else True
        cr.new_path(); cr.arc(x, 185, 34 if on else 26, 0, 2 * math.pi)
        cr.set_source_rgba(*LETTER_COL[L][:3], 1 if on or done else 0.3); cr.fill()
        ptext(cr, L, x, 185 + (14 if on else 11), 40 if on else 30, INK, 1, sw=0, shadow=False)

# ---------- scenes ----------
def scene_hook(cr, t):
    b = bt('hook'); tf = w('hook', 'four'); twh = w('hook', 'Where')
    for i, L in enumerate(ORDER):
        t0 = tf + i * 0.12
        if t >= t0: tile(cr, L, t, 1.0, pop_k(t, t0))
    title(cr, 'WHERE WOULD', 230, 120, t, twh, WHITE)
    title(cr, 'YOU LIVE?', 380, 150, t, w('hook', 'live'), GOLD)
    if t < tf:  # opening line before the tiles land
        k = pop_k(t, b['l0'])
        cr.save(); cr.translate(540, 900); cr.scale(k, k)
        ptext(cr, 'YOU HAVE TO MOVE', 0, 0, 90, WHITE, 1, sw=11); ptext(cr, 'TO ANOTHER WORLD', 0, 110, 90, CYAN, 1, sw=11)
        cr.restore()
        emoji(cr, '🚀', 540, 1200, 180 * pop_k(t, w('hook', 'move')), 1, rot=0.15 * math.sin(t * 5))

def scene_world(cr, L, t):
    b = bt(L); wd = WORLDS[L]
    k_in = ease_out(prog(t, b['start'], b['start'] + 0.6)); k_out = ease_io(prog(t, b['end'] - 0.35, b['end']))
    px = lerp(1500, 540, k_in) - k_out * 1100
    r = 290 * (1 + 0.02 * math.sin(t * 1.5))
    planet(cr, wd['kind'], px, 820, r, t)
    ta = b['l0']
    if t >= ta - 0.1:
        k = pop_k(t, ta - 0.1); cr.save(); cr.translate(150, 380); cr.scale(k, k); badge(cr, L, 0, 0, 80, 1 - k_out); cr.restore()
    title(cr, wd['name'], 420, 150, t, w(L, wd['name'].capitalize()), wd['col'], 1 - k_out, x=610, maxw=740)
    for i, (e, txt, word) in enumerate(wd['chips']):
        t0 = w(L, word)
        if t < t0: continue
        k = pop_k(t, t0); y = 1235 + i * 95
        cr.save(); cr.translate(lerp(540 + 300, 540, ease_out(prog(t, t0, t0 + 0.3))), y); cr.scale(k, k)
        cr.translate(0, 0)
        wd_ = tw(cr, txt, 46, 'Poppins ExtraBold'); bw = wd_ + 130
        rrect(cr, -bw / 2, -42, bw, 82, 41); cr.set_source_rgba(0.06, 0.04, 0.16, 0.9 * (1 - k_out)); cr.fill_preserve()
        cr.set_source_rgba(*wd['col'][:3], 1 - k_out); cr.set_line_width(4); cr.stroke()
        emoji(cr, e, -bw / 2 + 48, -2, 54, 1 - k_out)
        ptext(cr, txt, 25, 16, 46, WHITE, 1 - k_out, fam='Poppins ExtraBold', sw=6)
        cr.restore()
    # reaction face: the latest one pops big beside the planet
    cur = None
    for e, word in wd['react']:
        t0 = w(L, word)
        if t >= t0: cur = (e, t0)
    if cur and t < b['end'] - 0.35:
        e, t0 = cur; k = pop_k(t, t0, 0.3)
        emoji(cr, e, 860, 560, 210 * k, 1, rot=0.18 * math.sin((t - t0) * 9) * math.exp(-(t - t0) * 2))

def scene_recap(cr, t):
    b, c = bt('recap'), bt('cta')
    tc = w('cta', 'Titan')
    for i, L in enumerate(ORDER):
        t0 = b['start'] + 0.1 + i * 0.1
        if t < t0: continue
        hl = ease_out(prog(t, tc, tc + 0.4)) if L == 'C' else 0.0
        dim = 0.45 if (t >= tc and L != 'C') else 1.0
        sc = pop_k(t, t0) * (1 + 0.08 * hl * (1 + 0.3 * math.sin(t * 6)))
        cr.save()
        if dim < 1: cr.push_group()
        tile(cr, L, t, 1.0, sc, hl)
        if dim < 1: cr.pop_group_to_source(); cr.paint_with_alpha(dim)
        cr.restore()
    for L, word in (('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')):
        t0 = w('recap', word) if word != 'A' else w('recap', 'A')
    title(cr, 'A, B, C OR D?', 330, 150, t, w('recap', 'So'), GOLD, 1 - ease_io(prog(t, c['start'], c['start'] + 0.25)))
    if t >= c['start']:
        title(cr, "I'M CHOOSING TITAN", 330, 110, t, tc, GOLD)
        ptext(cr, 'for the low gravity 🪶'.replace('🪶', ''), 540, 430, 50, WHITE, ease_out(prog(t, w('cta', 'low'), w('cta', 'low') + 0.3)), fam='Poppins ExtraBold', sw=6)
        tq = w('cta', 'comments')
        if t >= w('cta', 'Which'):
            k = pop_k(t, w('cta', 'Which')) * (1 + 0.04 * math.sin(t * 6))
            cr.save(); cr.translate(540, 1690); cr.scale(k, k)
            txt = 'COMMENT A, B, C OR D'; wd_ = tw(cr, txt, 60)
            rrect(cr, -wd_ / 2 - 50, -68, wd_ + 100, 104, 52); cr.set_source_rgba(*PINK[:3], 1); cr.fill()
            ptext(cr, txt, 0, 6, 60, WHITE, 1, sw=7); cr.restore()
            emoji(cr, '👇', 540, 1810 + 12 * abs(math.sin(t * 5)), 90 * pop_k(t, tq), 1)

def draw_captions(cr, t):
    for b in TL['beats']:
        if b['key'] == 'cta' and t >= w('cta', 'Which'): return  # the CTA pill takes the caption slot
        if not (b['l0'] - 0.05 <= t < b['l1'] + 0.3): continue
        words, src, toks = b['words'], list(b['tokens']), []
        for _, _, x in words:
            n = len(x.split()); toks.append(' '.join(src[:n])); src = src[n:]
        if src or len(toks) != len(words): toks = [x for _, _, x in words]
        groups, cur = [], []
        for tok, (s, e, _) in zip(toks, words):
            cur.append((s, e, tok))
            if len(cur) == 3 or re.search(r"[.,!?:;…]$", tok): groups.append(cur); cur = []
        if cur: groups.append(cur)
        g = None
        for i, gr in enumerate(groups):
            nxt = groups[i + 1][0][0] if i + 1 < len(groups) else b['l1'] + 0.3
            if gr[0][0] - 0.05 <= t < nxt: g = gr; break
        if g is None: return
        ups = [x[2].upper() for x in g]
        size = 70; face(cr, size); space = cr.text_extents(' ').x_advance
        ci = max([j for j, x in enumerate(g) if x[0] <= t + 0.02] or [0])
        widths = [cr.text_extents(u).x_advance * (1.12 if j == ci else 1.0) for j, u in enumerate(ups)]
        total = sum(widths) + space * (len(ups) - 1); sc = min(1.0, 980 / total)
        y = 1690 if b['key'] in ORDER else 1700
        cr.save(); cr.translate(540, y); cr.scale(sc, sc); x = -total / 2
        col_active = WORLDS[b['key']]['col'] if b['key'] in WORLDS else GOLD
        for j, (u, wd_) in enumerate(zip(ups, widths)):
            cr.save(); cr.translate(x + wd_ / 2, 0)
            if j == ci: k = ease_back(prog(t, g[j][0], g[j][0] + 0.15), 3); cr.scale(1 + 0.12 * k, 1 + 0.12 * k)
            ptext(cr, u, 0, 0, size, col_active if j == ci else WHITE, 1.0 if j <= ci else 0.6, sw=11)
            cr.restore(); x += wd_ + space
        cr.restore(); return

def render_frame(cr, t):
    draw_space(cr, t)
    cur = None
    for b in TL['beats']:
        if b['start'] <= t < b['end']: cur = b['key']
    cur = cur or TL['beats'][-1]['key']
    if cur == 'hook': scene_hook(cr, t)
    elif cur in ORDER:
        header(cr, t, cur); scene_world(cr, cur, t)
    else: scene_recap(cr, t)
    draw_captions(cr, t)
    for b in TL['beats'][1:]:  # flash on every cut
        fl = 1 - prog(t, b['start'], b['start'] + 0.15)
        if 0 < fl <= 1 and t >= b['start']: cr.set_source_rgba(1, 1, 1, 0.35 * fl); cr.paint()
    f = prog(t, TL['dur'] - 0.4, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- music & sound ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(5)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 100
    chords = [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 69]]  # Cmaj7 Am7 Fmaj7 G6
    for ci in range(int(dur / (beat * 4)) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(beat * 4.6 * SR)) / SR
        env = np.minimum(1, L_ / 0.6) * np.exp(-L_ * 0.4)
        put(music, ci * beat * 4, sum(0.028 * (np.sin(2 * np.pi * note(m) * L_) + 0.4 * np.sin(2 * np.pi * note(m) * 1.004 * L_)) for m in ch) * env)
        put(music, ci * beat * 4, 0.1 * np.sin(2 * np.pi * note(ch[0] - 24) * L_) * env)
    for bi in range(int(dur / beat)):
        t0 = bi * beat; ch = chords[(bi // 4) % 4]
        for s in range(2):  # twinkly arpeggio
            m = ch[(bi * 2 + s) % 4] + 12; pt = np.arange(int(0.45 * SR)) / SR
            put(music, t0 + s * beat / 2, 0.035 * (np.sin(2 * np.pi * note(m) * pt) + 0.3 * np.sin(2 * np.pi * 2 * note(m) * pt)) * np.exp(-pt * 7))
        if t0 > bt('hook')['end'] - 0.2:
            L_ = np.arange(int(0.3 * SR)) / SR
            put(music, t0, 0.32 * np.sin(2 * np.pi * np.cumsum(48 + 70 * np.exp(-L_ * 35)) / SR) * np.exp(-L_ * 10))
            M = np.arange(int(0.04 * SR)); put(music, t0 + beat / 2, 0.025 * np.diff(rng.standard_normal(len(M) + 1)) * np.exp(-M / SR * 70))
    music = np.tanh(music * 1.2) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp):
        L_ = np.arange(int(1.6 * SR)) / SR
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(38 + 90 * np.exp(-L_ * 12)) / SR) * np.exp(-L_ * 3))
    def whoosh(t0, amp=0.2):
        nz = rng.standard_normal(int(0.7 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2
        put(fx, t0, amp * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def blip(t0, f=880, amp=0.1):
        L_ = np.arange(int(0.18 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * f * L_ * (1 + 0.6 * L_)) * np.exp(-L_ * 22))
    boom(w('hook', 'Where'), 0.7); boom(w('cta', 'Titan'), 0.6)
    for i in range(4): blip(w('hook', 'four') + i * 0.12, 660 + i * 110, 0.09)
    for b in T['beats'][1:]: whoosh(b['start'] - 0.25)
    for L in ORDER:
        for _, _, word in WORLDS[L]['chips']: blip(w(L, word), 1320, 0.08)
        for _, word in WORLDS[L]['react']: blip(w(L, word) + 0.05, 520, 0.12)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx + v
    mix *= np.minimum(1, tt / 0.02) * np.minimum(1, (dur - tt) / 1.0)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

# ---------- static graphics (feed post + green-screen backdrop) ----------
def graphics(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    layouts = {  # name: canvas height, title baselines, tile scale, tile centres, CTA y
        'where-would-you-live-backdrop.png': (1920, (250, 400), 1.0, None, 1700),
        'where-would-you-live-post.png': (1350, (130, 265), 0.8, {'A': (300, 540), 'B': (780, 540), 'C': (300, 994), 'D': (780, 994)}, 1282),
    }
    for name, (h, (y1, y2), sc, centres, ycta) in layouts.items():
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, h); cr = cairo.Context(s)
        cr.save(); cr.scale(1, h / H); draw_space(cr, 3.0); cr.restore()
        ptext(cr, 'WHERE WOULD', 540, y1, 120 if h == 1920 else 104, WHITE, 1, sw=15)
        ptext(cr, 'YOU LIVE?', 540, y2, 150 if h == 1920 else 132, GOLD, 1, sw=18)
        for L in ORDER: tile(cr, L, 3.0, 1.0, sc, at=centres[L] if centres else None)
        txt = 'COMMENT A, B, C OR D'; wd_ = tw(cr, txt, 56)
        rrect(cr, 540 - wd_ / 2 - 50, ycta - 64, wd_ + 100, 98, 49); cr.set_source_rgba(*PINK[:3], 1); cr.fill()
        ptext(cr, txt, 540, ycta + 4, 56, WHITE, 1, sw=7)
        s.write_to_png(os.path.join(out_dir, name)); print('wrote', name)

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    global TL
    if sys.argv[1] == '--graphics': graphics(sys.argv[2]); return
    out = sys.argv[1]
    TL = build(WordVoice(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_space')))
    print(f"duration {TL['dur']:.1f}s")
    for b in TL['beats']: print(f"  {b['key']:6s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 2 and sys.argv[2] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[3].split(','):
            render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]
    make_audio(TL, base + '.wav')
    nfr = int(TL['dur'] * FPS); workers = os.cpu_count() or 4
    bounds = np.linspace(0, nfr, workers * 2 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
