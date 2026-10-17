"""Punchier cut of the border video: instant hook, colourful pop text, emoji stickers, karaoke captions.
Builds on border.py (same map and animations). Voice: Microsoft's Canadian voice (en-CA-ClaraNeural) via
edge-tts when its host is reachable, otherwise the local Kokoro voice.
Usage: python3 border2.py <data_dir> <voices_dir> <out.mp4> [--preview t1,t2,...]
"""
import asyncio, hashlib, io, math, os, subprocess, sys
import numpy as np
import cairo
import border as B
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, Voice, SR

POP = [hexc('#FF3D7F'), hexc('#FFD60A'), hexc('#2EE6FF'), hexc('#7CFF4F'), hexc('#FF8A00'), hexc('#B46BFF')]
INK = (0.04, 0.02, 0.10)
W, H = B.W, B.H

B.BEATS = [
    ('hook', ["Almost ninety percent of Canadians live in this one thin strip.",
              "In the second biggest country on Earth! So... why?"],
     None, None, None, (-96, 57, 1.0)),
    ('band', ["Here's the deal. Draw a line one hundred sixty kilometres from the US border...",
              "and about three out of four Canadians live inside it.",
              "Push it to three hundred kilometres, and it's about ninety percent!"],
     'THE BORDER STRIP', None, None, (-96, 53, 1.12)),
    ('north', ["Meanwhile, Nunavut covers a fifth of Canada... but only about forty thousand people live there."],
     'THE EMPTY NORTH', ('21% vs 0.1%', 'land vs people'), (0, 1.6), (-90, 64, 1.1)),
    ('why', ["So why does everyone crowd the border? Four reasons."], 'BUT WHY?', None, None, (-96, 57, 1.0)),
    ('cold', ["Reason one: the cold. Northern winters hit minus forty, and roughly forty percent of Canada sits on permafrost... ground that never thaws."],
     '#1 THE COLD', ('-40°', 'frozen ground up north'), (0, 2.2), (-96, 59, 1.0)),
    ('shield', ["Reason two: the Canadian Shield. Ancient rock with thin soil, covering nearly half the country.",
                "Only about seven percent of Canada is farmland... and most of it hugs the south."],
     '#2 ROCK, NOT SOIL', ('~7%', 'is farmland'), (1, 0.6), (-92, 55, 1.05)),
    ('trade', ["Reason three: the United States. About three quarters of Canada's exports go south...",
               "so cities grew right next door to their biggest customer."],
     '#3 THE BIG NEIGHBOUR', ('~75%', 'of exports go to the USA'), (0, 2.6), (-96, 47, 1.3)),
    ('rail', ["And reason four: history. Canada's first coast-to-coast railway, finished in eighteen eighty-five, ran close to the border...",
              "and towns grew up right along the tracks."],
     '#4 THE RAILWAY', ('1885', 'Montreal to Vancouver'), (0, 3.0), (-98, 50, 1.35)),
    ('fact', ["Okay, here's a wild one. Toronto is further south than Seattle...", "and even Minneapolis!"],
     'WAIT, WHAT?!', None, None, (-100, 47, 1.05)),
    ('outro', ["So Canada isn't empty. It's just squeezed along the border.",
               "Would you live up north? Tell me in the comments!"],
     'SQUEEZED ALONG THE BORDER', None, None, (-96, 57, 1.0)),
]
STICKER = {'hook': '👀', 'band': '📏', 'north': '🥶', 'why': '🤔', 'cold': '❄️', 'shield': '🪨', 'trade': '📦',
           'rail': '🚂', 'fact': '🤯', 'outro': '💬'}

# ---------- voice ----------
class EdgeVoice:
    """Canadian neural voice through edge-tts; same interface as quiz.Voice (returns float32 at SR)."""
    VOICE = 'en-CA-ClaraNeural'
    def __init__(self, cache):
        self.cache = cache; os.makedirs(cache, exist_ok=True)
    def get(self, s):
        p = os.path.join(self.cache, hashlib.md5(f'edge|{self.VOICE}|{s}'.encode()).hexdigest() + '.npy')
        if os.path.exists(p): return np.load(p)
        import edge_tts
        async def run():
            buf = bytearray()
            async for ch in edge_tts.Communicate(s, self.VOICE, rate='+6%', proxy=os.environ.get('HTTPS_PROXY')).stream():
                if ch['type'] == 'audio': buf.extend(ch['data'])
            return bytes(buf)
        mp3 = asyncio.run(run())
        pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', 'pipe:0', '-f', 's16le', '-ac', '1', '-ar', str(SR), 'pipe:1'],
                             input=mp3, capture_output=True, check=True).stdout
        a = np.frombuffer(pcm, '<i2').astype(np.float32) / 32767
        nz = np.nonzero(np.abs(a) > 0.01)[0]; a = a[max(nz[0] - 200, 0):nz[-1] + 1200]
        np.save(p, a); return a

def pick_voice(vdir, cache):
    try:
        v = EdgeVoice(os.path.join(cache, 'edge')); v.get('Hello from Canada.'); print('voice: en-CA-ClaraNeural (Canadian)')
        return v
    except Exception as e:
        print(f'voice: Canadian voice unavailable ({type(e).__name__}); using Kokoro af_heart')
        return Voice(vdir, cache)

# ---------- pop text ----------
def face(cr, size, emoji=False):
    if emoji: cr.select_font_face('Noto Color Emoji')
    else: cr.select_font_face('Inter Display', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(size)

def ptext(cr, s, x, y, size, fill, a=1.0, anchor='c', sw=None):
    """Chunky text: drop shadow, thick dark outline, bright fill."""
    face(cr, size)
    w = cr.text_extents(s).x_advance
    x0 = x - w / 2 if anchor == 'c' else (x - w if anchor == 'r' else x)
    sw = sw or size * 0.17
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.new_path(); cr.move_to(x0 + size * 0.05, y + size * 0.09); cr.text_path(s)
    cr.set_source_rgba(0, 0, 0, 0.45 * a); cr.set_line_width(sw); cr.stroke_preserve(); cr.fill()
    cr.new_path(); cr.move_to(x0, y); cr.text_path(s)
    cr.set_source_rgba(*INK, a); cr.set_line_width(sw); cr.stroke_preserve()
    cr.set_source_rgba(*fill[:3], a); cr.fill()
    return w

def emoji(cr, e, x, y, size, a=1.0, rot=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot); s = size / 109; cr.scale(s, s)
    face(cr, 109, emoji=True); w = cr.text_extents(e).x_advance
    cr.push_group(); cr.move_to(-w / 2, 40); cr.show_text(e); cr.pop_group_to_source(); cr.paint_with_alpha(a)
    cr.restore()

def beat_color(b):
    keys = [x[0] for x in B.BEATS]; return POP[keys.index(b['key']) % len(POP)]

def wrap_words(cr, words, size, maxw):
    face(cr, size); lines, cur = [], []
    for wd in words:
        trial = ' '.join(cur + [wd])
        if cur and cr.text_extents(trial).x_advance > maxw: lines.append(cur); cur = [wd]
        else: cur.append(wd)
    return lines + [cur]

def draw_header(cr, b, t):
    if not b['head']: return
    out = 1 - ease_io(prog(t, b['end'] - 0.25, b['end']))
    if out <= 0: return
    col = beat_color(b); size = 92
    lines = wrap_words(cr, b['head'].split(), size, 940)
    idx = 0
    for li, words in enumerate(lines):
        face(cr, size); space = cr.text_extents(' ').x_advance
        widths = [cr.text_extents(w).x_advance for w in words]
        x = W / 2 - (sum(widths) + space * (len(words) - 1)) / 2
        y = 250 + li * 100 - (len(lines) - 1) * 50
        for w, wd in zip(widths, words):
            k = prog(t, b['start'] + idx * 0.09, b['start'] + idx * 0.09 + 0.4)
            if k > 0:
                s = ease_back(k, 3); bob = 5 * math.sin(t * 3 + idx)
                cr.save(); cr.translate(x + w / 2, y + bob); cr.rotate((1 - ease_out(k)) * (0.35 if idx % 2 else -0.35) + 0.03 * math.sin(t * 2 + idx))
                cr.scale(s, s)
                ptext(cr, wd, 0, 0, size, col if idx % 2 == 0 or len(words) == 1 else hexc('#FFFFFF'), out * clamp(k * 3))
                cr.restore()
            x += w + space; idx += 1
    st = STICKER.get(b['key'])
    if st:
        k = prog(t, b['start'] + 0.35, b['start'] + 0.8)
        if k > 0: emoji(cr, st, 985, 75, 100 * ease_back(k, 3), out, rot=0.25 * math.sin(t * 4))

def draw_stat(cr, b, t):
    if not b['stat']: return
    t0 = B.stat_time(b)
    a = ease_out(prog(t, t0, t0 + 0.25)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    big, small = b['stat']; col = beat_color(b)
    k = ease_back(prog(t, t0, t0 + 0.4), 3)
    cr.save(); cr.translate(540, 1330); cr.rotate(-0.04 + 0.02 * math.sin(t * 3)); cr.scale(k, k)
    face(cr, 150); w = cr.text_extents(big).x_advance; size = 150 * min(1, 900 / w)
    ptext(cr, big, 0, 20, size, hexc('#FFD60A'), a)
    face(cr, 40); w2 = cr.text_extents(small.upper()).x_advance
    B.rrect(cr, -w2 / 2 - 30, 55, w2 + 60, 64, 32); cr.set_source_rgba(*col[:3], a); cr.fill()
    ptext(cr, small.upper(), 0, 100, 40, hexc('#FFFFFF'), a, sw=6)
    cr.restore()

def draw_counter(cr, T, t):
    b = T['by']['band']
    if not (b['start'] <= t < b['end']): return
    l1, l2 = b['lines'][1], b['lines'][2]
    a = ease_out(prog(t, l1[0], l1[0] + 0.3)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    v = lerp(0, 75, ease_out(prog(t, l1[0], l1[0] + 1.2)))
    v = lerp(v, 90, ease_out(prog(t, l2[0] + 1.2, l2[0] + 2.6)))
    km = 160 if t < l2[0] + 1.0 else 300
    punch = 1 + 0.12 * (1 - prog(t, l2[0] + 2.6, l2[0] + 3.0)) * (t > l2[0] + 2.6)
    k = ease_back(prog(t, l1[0], l1[0] + 0.4), 3) * punch
    cr.save(); cr.translate(540, 1330); cr.scale(k, k)
    ptext(cr, f'{v:.0f}%', 0, 30, 190, POP[1] if v < 89.5 else POP[3], a)
    txt = f'LIVE WITHIN {km} KM OF THE USA'
    face(cr, 38); w2 = cr.text_extents(txt).x_advance
    B.rrect(cr, -w2 / 2 - 30, 70, w2 + 60, 62, 31); cr.set_source_rgba(*POP[0][:3], a); cr.fill()
    ptext(cr, txt, 0, 114, 38, hexc('#FFFFFF'), a, sw=6)
    cr.restore()

def draw_captions(cr, T, t):
    """Karaoke captions: three words at a time, the spoken word pops in colour."""
    for b in T['beats']:
        for l0, l1, s in b['lines']:
            if not (l0 <= t < l1 + 0.2): continue
            words = s.split()
            wts = np.array([len(w.strip('.,!?')) + 2.5 for w in words], float)
            edges = l0 + (l1 - l0) * np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
            cur = int(np.clip(np.searchsorted(edges, t, side='right') - 1, 0, len(words) - 1))
            g0 = (cur // 3) * 3; group = words[g0:g0 + 3]
            size = 78; face(cr, size); space = cr.text_extents(' ').x_advance
            ups = [w.upper() for w in group]
            widths = [cr.text_extents(u).x_advance * (1.14 if g0 + j == cur else 1.0) for j, u in enumerate(ups)]
            total = sum(widths) + space * (len(ups) - 1)
            sc = min(1.0, 960 / total)
            cr.save(); cr.translate(540, 1650); cr.scale(sc, sc)
            x = -total / 2
            for j, (u, w) in enumerate(zip(ups, widths)):
                wi = g0 + j
                active = wi == cur
                k = ease_back(prog(t, edges[wi], edges[wi] + 0.15), 3) if active else 1.0
                cr.save(); cr.translate(x + w / 2, 0)
                if active: cr.scale(1.0 + 0.14 * k, 1.0 + 0.14 * k); cr.rotate(-0.03)
                col = POP[wi % len(POP)] if active else hexc('#FFFFFF')
                ptext(cr, u, 0, 0, size, col, 1.0 if wi <= cur else 0.75)
                cr.restore()
                x += w + space
            cr.restore(); return

def lights_on(T, t): return ease_out(prog(t, 0.0, 0.9))

def draw_hook_extra(cr, T, t, cam):
    b = T['by']['hook']
    if t > b['end']: return
    out = 1 - ease_io(prog(t, b['end'] - 0.3, b['end']))
    k = ease_out(prog(t, 0.25, 0.9))
    cr.save(); B.clip_canada(cr, cam); cr.new_path(); B.path(cr, cam, B.D.us)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.set_line_width(2 * 300 * cam[2] * k); cr.set_source_rgba(*POP[1][:3], 0.28 * out * (0.8 + 0.2 * math.sin(t * 6)))
    cr.stroke_preserve(); cr.set_line_width(5); cr.set_source_rgba(*POP[0][:3], out); cr.stroke()
    cr.restore()
    # big hook text
    k1 = prog(t, 0.15, 0.55)
    if k1 > 0:
        cr.save(); cr.translate(540, 300); s = ease_back(k1, 3) * (1 + 0.03 * math.sin(t * 5)); cr.scale(s, s); cr.rotate(-0.05)
        ptext(cr, '90%', 0, 40, 230, POP[1], out); cr.restore()
    k2 = prog(t, 0.45, 0.85)
    if k2 > 0:
        cr.save(); cr.translate(540, 430); s = ease_back(k2, 3); cr.scale(s, s)
        ptext(cr, 'OF CANADIANS', 0, 0, 74, hexc('#FFFFFF'), out); cr.restore()
    k3 = prog(t, 0.7, 1.1)
    if k3 > 0:
        cr.save(); cr.translate(540, 530); s = ease_back(k3, 3); cr.scale(s, s); cr.rotate(0.04)
        ptext(cr, 'LIVE HERE', 0, 0, 96, POP[0], out); cr.restore()
        bob = 18 * abs(math.sin(t * 5))
        emoji(cr, '👇', 540, 650 + bob, 110 * ease_back(k3, 3), out)
    emoji(cr, '🍁', 150, 150, 120 * ease_back(prog(t, 0.9, 1.3), 3), out, rot=0.2 * math.sin(t * 3))
    l1 = b['lines'][1]
    kw = prog(t, l1[1] - 0.9, l1[1] - 0.5)
    if kw > 0:
        cr.save(); cr.translate(540, 1300); s = ease_back(kw, 3) * (1 + 0.05 * math.sin(t * 9)); cr.scale(s, s); cr.rotate(-0.08)
        ptext(cr, 'WHY?!', 0, 40, 210, POP[0], out); cr.restore()

def draw_outro(cr, b, t):
    k2 = ease_back(prog(t, b['lines'][1][0], b['lines'][1][0] + 0.4), 3)
    if k2 > 0.01:
        cr.save(); cr.translate(540, 1330); cr.scale(k2 * (1 + 0.04 * math.sin(t * 6)), k2 * (1 + 0.04 * math.sin(t * 6)))
        face(cr, 46); txt = 'WOULD YOU LIVE UP NORTH?'; w = cr.text_extents(txt).x_advance
        B.rrect(cr, -w / 2 - 34, -60, w + 68, 84, 42); cr.set_source_rgba(*POP[0][:3], 1); cr.fill()
        ptext(cr, txt, 0, 0, 46, hexc('#FFFFFF'), 1, sw=7)
        emoji(cr, '💬', w / 2 + 70, -20, 90, 1)
        cr.restore()

# patch the base video with the new look
for name, fn in dict(draw_header=draw_header, draw_stat=draw_stat, draw_counter=draw_counter, draw_captions=draw_captions,
                     lights_on=lights_on, draw_hook_extra=draw_hook_extra, draw_outro=draw_outro).items():
    setattr(B, name, fn)

def main():
    data_dir, vdir, out = sys.argv[1:4]
    cache = os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache')
    B.TL = B.build(pick_voice(vdir, cache)); B.D = B.Data(data_dir)
    print(f"duration {B.TL['dur']:.1f}s")
    for b in B.TL['beats']: print(f"  {b['key']:7s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 4 and sys.argv[4] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[5].split(','):
            B.render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]
    B.make_audio(B.TL, base + '.wav')
    from multiprocessing import Pool
    n = int(B.TL['dur'] * B.FPS); workers = os.cpu_count() or 4
    bounds = np.linspace(0, n, workers * 2 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(B.render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt',
                    '-i', base + '.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
