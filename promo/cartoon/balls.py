"""Countryballs: Canada vs USA (9:16 cartoon). Two AI voices, lip-synced mouths from each voice's loudness,
hops on every spoken word, blinking, reactions, a fact card per claim, a live scoreboard and karaoke speech bubbles.
Usage: python3 balls.py <out.mp4> [--preview t1,t2,...]
"""
import asyncio, hashlib, json, math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import vs
import space_choice as SC
import cartoon as C
from vs import ptext, rrect, tw, fit, face
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

def emoji(cr, e, *a, **k): vs.emoji(cr, e.replace('️', ''), *a, **k)

W, H, FPS = 1080, 1920, 30
OUT = C.OUT
RED, BLUE, GOLD = (0.85, 0.12, 0.17), (0.2, 0.3, 0.7), hexc('#FFD60A')[:3]
VOICES = {'ca': ('en-CA-LiamNeural', '+8%', '+18Hz'), 'us': ('en-US-GuyNeural', '+10%', '+12Hz')}

LINES = [  # key, speaker, text
    ('hey', 'us', "Hey Canada! I'm the biggest country in North America!"),
    ('bigger', 'ca', "Sorry, eh... but I'm actually bigger."),
    ('what', 'us', "WHAT?! Only because you count all your lakes!"),
    ('lakes', 'ca', "Exactly. I have more lakes than the rest of the world combined."),
    ('people', 'us', "Well, I have way more people. Over three hundred and forty million!"),
    ('polite', 'ca', "True. I have about forty-one million... but they're very polite."),
    ('moon', 'us', "I put astronauts on the Moon!"),
    ('arm', 'ca', "And who built the robot arm for your Space Shuttle? Me."),
    ('econ', 'us', "Okay, but I have the biggest economy in the world."),
    ('bball', 'ca', "Sure. But basketball? Invented by a Canadian."),
    ('mass', 'us', "...in Massachusetts!"),
    ('olymp', 'us', "And I've won the most Olympic gold medals ever!"),
    ('hockey', 'ca', "Not in hockey, you haven't."),
    ('insulin', 'ca', "I discovered insulin."),
    ('internet', 'us', "Well, I invented the internet!"),
    ('tie', 'ca', "So... it's a tie?"),
    ('border', 'us', "Ugh. Fine. At least we share the longest border in the world."),
    ('best1', 'ca', "Best neighbours?"),
    ('best2', 'us', "Best neighbours!"),
    ('cta', 'ca', "Now you tell us: who really won? Comment below!"),
    ('obv', 'us', "Obviously me."),
]
# score events: (line index, trigger word, side)
POINTS = [('insulin', 'insulin', 'ca'), ('internet', 'internet', 'us'), ('bigger', 'bigger', 'ca'), ('lakes', 'combined', 'ca'), ('people', 'three', 'us'), ('moon', 'Moon', 'us'), ('arm', 'Me', 'ca'), ('econ', 'economy', 'us'),
          ('bball', 'Canadian', 'ca'), ('mass', 'Massachusetts', 'us'), ('olymp', 'Olympic', 'us'), ('hockey', 'hockey', 'ca')]
# fact cards: (line index, trigger word, kind)
CARDS = [('insulin', 'insulin', 'insulin'), ('internet', 'internet', 'internet'), ('bigger', 'bigger', 'area'), ('lakes', 'lakes', 'lakes'), ('people', 'people', 'people'), ('moon', 'Moon', 'moon'), ('arm', 'robot', 'arm'),
         ('econ', 'economy', 'econ'), ('bball', 'basketball', 'bball'), ('olymp', 'Olympic', 'olympics'), ('hockey', 'hockey', 'hockey'), ('border', 'border', 'border')]
# moods: (line, word or None for line start, who, mood, duration)
MOODS = [('internet', 'internet', 'us', 'sly', 1.2), ('insulin', 'insulin', 'ca', 'sly', 1.0), ('what', None, 'us', 'shocked', 1.6), ('bigger', 'bigger', 'ca', 'sly', 1.4), ('lakes', 'combined', 'ca', 'sly', 1.0), ('people', 'three', 'us', 'sly', 1.3),
         ('polite', 'polite', 'ca', 'happy', 1.0), ('arm', 'Me', 'ca', 'sly', 1.2), ('arm', 'robot', 'us', 'shocked', 1.0), ('bball', 'Canadian', 'ca', 'sly', 1.0),
         ('bball', 'Canadian', 'us', 'shocked', 0.9), ('mass', None, 'us', 'sly', 1.4), ('mass', 'Massachusetts', 'ca', 'shocked', 1.3),
         ('olymp', 'Olympic', 'us', 'sly', 1.2), ('hockey', 'hockey', 'ca', 'sly', 1.2), ('hockey', 'hockey', 'us', 'shocked', 1.0),
         ('border', None, 'us', 'grumpy', 1.4), ('obv', None, 'us', 'sly', 2.0), ('obv', None, 'ca', 'grumpy', 2.0)]

class MultiVoice:
    def __init__(self, cache): self.cache = cache; os.makedirs(cache, exist_ok=True)
    def get(self, spk, text):
        v, rate, pitch = VOICES[spk]
        key = hashlib.md5(f'mv|{v}|{rate}|{pitch}|{text}'.encode()).hexdigest()
        pa, pw = os.path.join(self.cache, key + '.npy'), os.path.join(self.cache, key + '.json')
        if os.path.exists(pa) and os.path.exists(pw): return np.load(pa), json.load(open(pw))
        import edge_tts
        async def run():
            buf, words = bytearray(), []
            async for ch in edge_tts.Communicate(text, v, rate=rate, pitch=pitch, proxy=os.environ.get('HTTPS_PROXY'), boundary='WordBoundary').stream():
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

TL = None
_missing = set()
INTRO = 1.0
def build(voice):
    t, lines = INTRO, []
    gaps = {'bigger': 0.25, 'what': 0.15, 'mass': 0.25, 'hockey': 0.3, 'internet': 0.3, 'tie': 0.5, 'best1': 0.15, 'best2': 0.6, 'cta': 0.3}
    for i, (key, spk, text) in enumerate(LINES):
        a, words = voice.get(spk, text)
        b = dict(i=i, key=key, spk=spk, text=text, l0=t); b['l1'] = t + len(a) / SR
        b['words'] = [(t + s, t + e, x) for s, e, x in words]; b['tokens'] = text.split(); b['audio'] = a
        lines.append(b); t = b['l1'] + gaps.get(key, 0.3)
    dur = t + 2.8
    nf = int(dur * FPS) + 2; env = {'ca': np.zeros(nf), 'us': np.zeros(nf)}
    for b in lines:  # per-frame mouth openness from each speaker's own loudness
        a = b['audio']; win = SR // FPS
        for f in range(int(b['l0'] * FPS), min(nf, int(b['l1'] * FPS) + 1)):
            i0 = int((f / FPS - b['l0']) * SR) - win // 2
            seg = a[max(0, i0):max(0, i0 + win)]
            if len(seg): env[b['spk']][f] = max(env[b['spk']][f], float(np.sqrt(np.mean(seg ** 2))))
    for k in env:
        m = np.percentile(env[k][env[k] > 0], 90) if (env[k] > 0).any() else 1
        env[k] = np.clip(env[k] / m, 0, 1)
    return dict(lines=lines, by={b['key']: b for b in lines}, dur=dur, env=env)

def ln(k): return TL['by'][k]
def w(i, word, end=False):
    q = SC.norm(word)
    for s, e, x in ln(i)['words']:
        if any(SC.norm(p).startswith(q) for p in x.split()): return e if end else s
    if (i, word) not in _missing: _missing.add((i, word)); print(f'  ! no word "{word}" in line {i}', file=sys.stderr)
    return ln(i)['l0']
def pop_k(t, t0, d=0.35): return max(1e-3, ease_back(prog(t, t0, t0 + d), 2.6))

# ---------- scene ----------
import random
_rnd = random.Random(7)
SNOW = [(_rnd.uniform(0, 520), _rnd.uniform(0, 1920), _rnd.uniform(4, 9), _rnd.uniform(30, 70), _rnd.uniform(0, 6.28)) for _ in range(70)]
CLOUDS = [(150, 330, 1.0), (870, 250, 0.8), (560, 470, 0.6)]
GROUND_Y = 1440

def draw_scene(cr, t):
    g = cairo.LinearGradient(0, 0, 0, GROUND_Y); g.add_color_stop_rgb(0, 0.38, 0.72, 1.0); g.add_color_stop_rgb(1, 0.78, 0.93, 1.0)
    cr.set_source(g); cr.paint()
    for i in range(0, 1080, 36):
        for j in range(0, GROUND_Y, 36):
            cr.new_path(); cr.arc(i + (18 if (j // 36) % 2 else 0), j, 3.0, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.12); cr.fill()
    for cx, cy, sc in CLOUDS:
        x = (cx + t * 12 * sc) % 1300 - 110
        for dx, dy, rr in ((-55, 10, 42), (0, -8, 58), (58, 8, 44), (20, 22, 40)):
            cr.new_path(); cr.arc(x + dx * sc, cy + dy * sc, rr * sc, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.95); cr.fill()
    # rolling hills, snowy on Canada's side
    cr.new_path(); cr.move_to(0, H); cr.line_to(0, GROUND_Y - 30); cr.curve_to(300, GROUND_Y - 120, 700, GROUND_Y + 40, 1080, GROUND_Y - 60)
    cr.line_to(1080, H); cr.close_path(); cr.set_source_rgb(0.42, 0.8, 0.42); cr.fill_preserve(); C.outline(cr, 7)
    cr.save(); cr.rectangle(0, 0, 540, H); cr.clip()
    cr.new_path(); cr.move_to(0, H); cr.line_to(0, GROUND_Y - 30); cr.curve_to(300, GROUND_Y - 120, 700, GROUND_Y + 40, 1080, GROUND_Y - 60)
    cr.line_to(1080, H); cr.close_path(); cr.set_source_rgb(0.95, 0.97, 1.0); cr.fill_preserve(); C.outline(cr, 7); cr.restore()
    # the border: a dashed line and a little sign
    cr.new_path(); cr.move_to(540, GROUND_Y - 40); cr.line_to(540, H); cr.set_dash([26, 18]); cr.set_source_rgb(*OUT); cr.set_line_width(8); cr.stroke(); cr.set_dash([])
    rrect(cr, 540 - 9, 1560, 18, 150, 6); cr.set_source_rgb(0.55, 0.35, 0.2); cr.fill_preserve(); C.outline(cr, 5)
    rrect(cr, 540 - 150, 1540, 300, 80, 14); cr.set_source_rgb(0.95, 0.85, 0.6); cr.fill_preserve(); C.outline(cr, 6)
    ptext(cr, 'CANADA | USA', 540, 1593, 40, OUT, 1, fam='Poppins Black', sw=0, shadow=False)
    for x, y0, r, sp, ph in SNOW:  # snow falls only on Canada
        y = (y0 + t * sp) % (GROUND_Y + 60) - 30; xx = x + 14 * math.sin(t * 1.3 + ph)
        cr.new_path(); cr.arc(xx, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.9); cr.fill()

# ---------- characters ----------
BASE = {'ca': (285, 1250), 'us': (795, 1250)}; R = 168
def hop(t, spk):
    """Little hop on every word the character speaks."""
    y, sq = 0.0, 0.0
    for b in TL['lines']:
        if b['spk'] != spk or not (b['l0'] - 0.1 <= t <= b['l1'] + 0.4): continue
        for s, e, x in b['words']:
            if s <= t < s + 0.28:
                k = (t - s) / 0.28; y = max(y, 22 * math.sin(math.pi * k)); sq = 0.06 * math.cos(math.pi * k * 2) * (1 - k)
    return y, sq

def mood_of(t, spk):
    m = 'happy'
    for li, word, who, mood, d in MOODS:
        if who != spk: continue
        t0 = ln(li)['l0'] if word is None else w(li, word)
        if t0 <= t < t0 + d: m = mood
    return m

def blink_of(t, spk):
    ph = (t + (0.0 if spk == 'ca' else 1.7)) % 3.4
    return max(0.0, 1 - abs(ph - 0.1) / 0.08) if ph < 0.2 else 0.0

def speaking(t):
    for b in TL['lines']:
        if b['l0'] - 0.05 <= t < b['l1'] + 0.25: return b
    return None

def positions(t):
    """Base positions, the intro drop-in, and the 'best neighbours' bump."""
    out = {}
    for spk, (x, y) in BASE.items():
        k = prog(t, 0.05 + (0.15 if spk == 'us' else 0), 0.65 + (0.15 if spk == 'us' else 0))
        yy = y - (1 - ease_out(k)) * 1500 if k < 1 else y
        land = t - (0.65 + (0.15 if spk == 'us' else 0)); sq = 0.18 * math.exp(-land * 7) * math.cos(land * 22) if land > 0 else -0.1
        tb = w('best2', 'neighbours') if TL else 1e9; tn = w('best1', 'Best')
        lean = ease_io(prog(t, tn, tn + 0.8)) * 90 - ease_io(prog(t, tb + 0.5, tb + 1.2)) * 90
        bump = math.sin(math.pi * clamp((t - tb) / 0.5)) * 85 if tb <= t < tb + 0.5 else 0
        d = 1 if spk == 'ca' else -1
        out[spk] = (x + d * (lean + bump), yy, sq)
    return out

def draw_ball(cr, t, spk, pos):
    x, y, sq0 = pos; other = 'us' if spk == 'ca' else 'ca'
    hy, hsq = hop(t, spk); fr = min(int(t * FPS), len(TL['env'][spk]) - 1)
    talk = TL['env'][spk][fr]
    mood = mood_of(t, spk)
    sp = speaking(t); look = (0.7 if spk == 'ca' else -0.7, 0) if (sp and sp['spk'] == other) else (0.25 if spk == 'ca' else -0.25, 0.1)
    if mood == 'shocked': hy += 30 * max(0, math.sin(t * 9))
    tilt = (0.06 if spk == 'ca' else -0.06) * math.sin(t * 1.3) + (0.12 * (1 if spk == 'ca' else -1) if mood == 'sly' else 0)
    yy = y - hy
    # shadow
    cr.new_path(); cr.save(); cr.translate(x, y + R * 0.95); cr.scale(1, 0.18); cr.arc(0, 0, R * (0.85 - hy / 400), 0, 2 * math.pi); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.fill()
    C.countryball(cr, 'canada' if spk == 'ca' else 'usa', x, yy, R, talk=talk if talk > 0.08 else 0.0, look=look, blink=blink_of(t, spk),
                  mood=mood, tilt=tilt, sq=sq0 + hsq)
    accessory(cr, spk, x, yy, tilt, sq0 + hsq)

def accessory(cr, spk, x, y, tilt, sq):
    cr.save(); cr.translate(x, y); cr.rotate(tilt); cr.scale(1 + sq * 0.5, 1 - sq)
    if spk == 'ca':  # a red toque with a pom-pom
        cr.new_path(); cr.move_to(-R * 0.78, -R * 0.62); cr.curve_to(-R * 0.7, -R * 1.35, R * 0.7, -R * 1.35, R * 0.78, -R * 0.62); cr.close_path()
        cr.set_source_rgb(0.85, 0.1, 0.15); cr.fill_preserve(); C.outline(cr, 6)
        rrect(cr, -R * 0.84, -R * 0.72, R * 1.68, R * 0.22, R * 0.1); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); C.outline(cr, 6)
        for i in range(-3, 4):
            cr.new_path(); cr.move_to(i * R * 0.17, -R * 0.95); cr.line_to(i * R * 0.17, -R * 0.78); cr.set_source_rgba(0.6, 0.05, 0.1, 0.5); cr.set_line_width(5); cr.stroke()
        cr.new_path(); cr.arc(0, -R * 1.25, R * 0.17, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); C.outline(cr, 6)
    else:  # a blue cap with a star
        cr.new_path(); cr.arc(0, -R * 0.62, R * 0.72, math.pi, 2 * math.pi); cr.close_path(); cr.set_source_rgb(0.18, 0.28, 0.65); cr.fill_preserve(); C.outline(cr, 6)
        cr.new_path(); cr.move_to(-R * 0.05, -R * 0.64); cr.curve_to(-R * 0.4, -R * 0.74, -R * 1.05, -R * 0.66, -R * 1.12, -R * 0.56)
        cr.curve_to(-R * 0.9, -R * 0.5, -R * 0.3, -R * 0.52, -R * 0.05, -R * 0.56); cr.close_path(); cr.set_source_rgb(0.15, 0.22, 0.55); cr.fill_preserve(); C.outline(cr, 6)
        cr.new_path()
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5; rr = R * (0.17 if k % 2 == 0 else 0.07); (cr.move_to if k == 0 else cr.line_to)(rr * math.cos(a), -R * 0.95 + rr * math.sin(a))
        cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); C.outline(cr, 4)
    cr.restore()

# ---------- overlays ----------
def score_at(t):
    s = {'ca': 0, 'us': 0}; last = None
    for li, word, side in POINTS:
        tp = w(li, word)
        if t >= tp: s[side] += 1; last = (side, tp)
    return s, last

def draw_scoreboard(cr, t):
    a = ease_out(prog(t, 0.3, 0.8))
    if a <= 0: return
    s, last = score_at(t)
    k = pop_k(t, 0.3, 0.5)
    cr.save(); cr.translate(540, 115); cr.scale(k, k)
    rrect(cr, -440, -70, 880, 140, 40); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); C.outline(cr, 8)
    tie = t >= w('tie', 'tie')
    for side, x, col, name in (('ca', -250, RED, 'CANADA'), ('us', 250, BLUE, 'USA')):
        ptext(cr, name, x, 20, 52, col, 1, sw=0, shadow=False)
    for side, x in (('ca', -60), ('us', 60)):
        kk = pop_k(t, last[1], 0.4) if (last and last[0] == side and t < last[1] + 0.5) else 1.0
        cr.save(); cr.translate(x, 0); cr.scale(kk, kk); ptext(cr, str(s[side]), 0, 30, 84, OUT, 1, sw=0, shadow=False); cr.restore()
    ptext(cr, ':', 0, 24, 70, OUT, 1, sw=0, shadow=False)
    cr.restore()
    if tie:
        kt = pop_k(t, w('tie', 'tie'), 0.4); cr.save(); cr.translate(540, 222); cr.rotate(-0.04); cr.scale(kt, kt)
        rrect(cr, -110, -34, 220, 68, 30); cr.set_source_rgb(*GOLD); cr.fill_preserve(); C.outline(cr, 6)
        ptext(cr, 'TIE!', 0, 18, 50, OUT, 1, sw=0, shadow=False); cr.restore()
    if last and t < last[1] + 1.2:  # +1 floating over the scorer
        side, tp = last; k = prog(t, tp, tp + 1.2); x = BASE[side][0]
        ptext(cr, '+1', x, BASE[side][1] - R * 1.5 - 80 * k, 80, GOLD, 1 - k ** 3, sw=10)

def card_box(cr, title, col, k, a):
    cr.translate(540, 470); cr.scale(k, k)
    rrect(cr, -470, -175, 940, 350, 38); cr.set_source_rgba(1, 1, 1, a); cr.fill_preserve(); cr.set_source_rgba(*OUT, a); cr.set_line_width(8); cr.stroke()
    rrect(cr, -470, -175, 940, 76, 38); cr.set_source_rgba(*col, a); cr.fill()
    cr.rectangle(-470, -137, 940, 38); cr.fill()
    cr.new_path(); cr.move_to(-470, -99); cr.line_to(470, -99); cr.set_source_rgba(*OUT, a); cr.set_line_width(6); cr.stroke()
    ptext(cr, title, 0, -120, 44, (1, 1, 1), a, sw=0, shadow=False)

def bars(cr, a, t0, t, rows):
    for i, (label, val, mx, txt, col) in enumerate(rows):
        y = -30 + i * 100; k = ease_out(prog(t, t0 + 0.2 + i * 0.2, t0 + 1.0 + i * 0.2)); wmax = 520
        ptext(cr, label, -310, y + 18, 40, OUT, a, fam='Poppins Black', anchor='r', sw=0, shadow=False)
        rrect(cr, -285, y - 26, max(30, wmax * val / mx * k), 56, 22); cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(*OUT, a); cr.set_line_width(5); cr.stroke()
        ptext(cr, txt, -285 + max(30, wmax * val / mx * k) + 16, y + 15, 38, OUT, a * clamp(k * 2 - 1), fam='Poppins ExtraBold', anchor='l', sw=0, shadow=False)

def card_content(cr, kind, t, t0, a):
    if kind == 'area':
        card_box(cr, 'TOTAL AREA', RED, pop_k(t, t0, 0.45), a)
        bars(cr, a, t0, t, [('CANADA', 9.98, 10.2, '9.98M km²', RED), ('USA', 9.83, 10.2, '9.83M km²', BLUE)])
        ptext(cr, '(land + lakes and rivers)', 0, 158, 30, (0.4, 0.4, 0.5), a, fam='Poppins ExtraBold', sw=0, shadow=False)
    elif kind == 'lakes':
        card_box(cr, 'LAKES', RED, pop_k(t, t0, 0.45), a)
        emoji(cr, '🏞️', -330, 30, 150, a)
        ptext(cr, '~60% OF ALL', 90, 0, 62, RED, a, sw=0, shadow=False)
        ptext(cr, "THE WORLD'S LAKES", 90, 70, 50, OUT, a, sw=0, shadow=False)
        ptext(cr, 'more than everyone else combined', 90, 130, 30, (0.4, 0.4, 0.5), a, fam='Poppins ExtraBold', sw=0, shadow=False)
    elif kind == 'people':
        card_box(cr, 'POPULATION', BLUE, pop_k(t, t0, 0.45), a)
        bars(cr, a, t0, t, [('CANADA', 41, 345, '~41 M', RED), ('USA', 340, 345, '~340 M', BLUE)])
    elif kind == 'moon':
        card_box(cr, 'THE MOON', BLUE, pop_k(t, t0, 0.45), a)
        emoji(cr, '🌕', -320, 30, 170, a); emoji(cr, '🚀', -230, 90, 80, a, rot=0.5 + 0.1 * math.sin(t * 3))
        ptext(cr, 'APOLLO 11 · 1969', 110, 10, 60, BLUE, a, sw=0, shadow=False)
        ptext(cr, '12 Americans have', 110, 75, 40, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
        ptext(cr, 'walked on the Moon', 110, 125, 40, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    elif kind == 'arm':
        card_box(cr, 'THE CANADARM', RED, pop_k(t, t0, 0.45), a)
        emoji(cr, '🦾', -320, 30, 160, a, rot=0.15 * math.sin(t * 4))
        ptext(cr, 'BUILT IN CANADA', 110, 10, 58, RED, a, sw=0, shadow=False)
        ptext(cr, "for NASA's Space Shuttle", 110, 75, 40, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
        ptext(cr, '(first flew in 1981)', 110, 125, 34, (0.4, 0.4, 0.5), a, fam='Poppins ExtraBold', sw=0, shadow=False)
    elif kind == 'econ':
        card_box(cr, 'ECONOMY', BLUE, pop_k(t, t0, 0.45), a)
        emoji(cr, '💰', -320, 30, 160, a)
        ptext(cr, "#1 IN THE WORLD", 110, 20, 62, BLUE, a, sw=0, shadow=False)
        ptext(cr, 'biggest GDP on Earth', 110, 90, 40, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    elif kind == 'bball':
        card_box(cr, 'BASKETBALL (1891)', (0.95, 0.5, 0.1), pop_k(t, t0, 0.45), a)
        emoji(cr, '🏀', -340, 30, 150, a, rot=t * 2)
        ptext(cr, 'INVENTED BY', 90, -20, 34, (0.4, 0.4, 0.5), a, fam='Poppins ExtraBold', sw=0, shadow=False)
        ptext(cr, 'JAMES NAISMITH 🍁'.replace(' 🍁', ''), 60, 30, 50, RED, a, sw=0, shadow=False)
        emoji(cr, '🍁', 330, 14, 50, a)
        tm = w('mass', 'Massachusetts')
        if t >= tm:
            km = pop_k(t, tm); cr.save(); cr.translate(90, 110); cr.scale(km, km)
            ptext(cr, 'IN SPRINGFIELD, MASSACHUSETTS', 0, 0, 36, BLUE, a, sw=0, shadow=False); cr.restore()
    elif kind == 'olympics':
        card_box(cr, 'OLYMPIC GOLD', BLUE, pop_k(t, t0, 0.45), a)
        emoji(cr, '🥇', -330, 30, 160, a, rot=0.15 * math.sin(t * 4))
        ptext(cr, 'MOST GOLD MEDALS', 110, 10, 58, BLUE, a, sw=0, shadow=False)
        ptext(cr, 'of any country, ever', 110, 75, 40, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    elif kind == 'hockey':
        card_box(cr, 'OLYMPIC HOCKEY', RED, pop_k(t, t0, 0.45), a)
        emoji(cr, '🏒', -330, 30, 160, a, rot=0.2 * math.sin(t * 5))
        ptext(cr, 'MOST HOCKEY GOLDS', 110, 10, 56, RED, a, sw=0, shadow=False)
        ptext(cr, "men's and women's", 110, 75, 40, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    elif kind == 'insulin':
        card_box(cr, 'INSULIN (1921)', RED, pop_k(t, t0, 0.45), a)
        emoji(cr, '💉', -330, 30, 150, a, rot=0.3)
        ptext(cr, 'DISCOVERED IN TORONTO', 110, 10, 50, RED, a, sw=0, shadow=False)
        ptext(cr, 'it has saved millions of lives', 110, 75, 38, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    elif kind == 'internet':
        card_box(cr, 'THE INTERNET', BLUE, pop_k(t, t0, 0.45), a)
        emoji(cr, '🌐', -330, 30, 150, a, rot=t)
        ptext(cr, 'BORN IN THE USA', 110, 10, 58, BLUE, a, sw=0, shadow=False)
        ptext(cr, 'it began as ARPANET in 1969', 110, 75, 38, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    elif kind == 'border':
        card_box(cr, 'THE BORDER', (0.3, 0.65, 0.35), pop_k(t, t0, 0.45), a)
        emoji(cr, '🤝', -330, 30, 150, a)
        ptext(cr, '8,891 km', 110, 20, 80, (0.25, 0.55, 0.3), a, sw=0, shadow=False)
        ptext(cr, 'longest border between', 110, 80, 38, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
        ptext(cr, 'two countries on Earth', 110, 125, 38, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)

def draw_card(cr, t):
    cur = None
    for i, (li, word, kind) in enumerate(CARDS):
        t0 = w(li, word)
        if t >= t0: cur = (kind, t0, CARDS[i + 1] if i + 1 < len(CARDS) else None)
    if not cur: return
    kind, t0, nxt = cur
    t_end = w(nxt[0], nxt[1]) if nxt else w('best2', 'neighbours') + 0.15
    a = 1 - ease_io(prog(t, t_end - 0.25, t_end))
    if kind == 'people': a *= 1.0
    if a <= 0.01: return
    cr.save(); card_content(cr, kind, t, t0, a); cr.restore()

def wrap(cr, toks, size, maxw):
    face(cr, size, 'Poppins ExtraBold'); sp = cr.text_extents(' ').x_advance; lines, cur, cw = [], [], 0
    for tk in toks:
        wd = cr.text_extents(tk).x_advance
        if cur and cw + sp + wd > maxw: lines.append(cur); cur, cw = [], 0
        cur.append(tk); cw += (sp if cw else 0) + wd
    if cur: lines.append(cur)
    return lines

def draw_bubble(cr, t):
    b = speaking(t)
    if not b: return
    if b['key'] == 'cta' and t >= w('cta', 'who'): return
    toks = b['tokens']; words = b['words']
    times = []  # map written tokens to spoken word starts
    src = list(toks); ti = 0
    for s, e, x in words:
        n = max(1, len(x.split()))
        for _ in range(n):
            if ti < len(toks): times.append(s); ti += 1
    while len(times) < len(toks): times.append(times[-1] if times else b['l0'])
    size = 50; lines = wrap(cr, toks, size, 800)
    face(cr, size, 'Poppins ExtraBold'); sp = cr.text_extents(' ').x_advance; lh = size * 1.25
    bw = max(cr.text_extents(' '.join(l)).x_advance for l in lines) + 90; bh = lh * len(lines) + 60
    sx = BASE[b['spk']][0]; cx = clamp(sx, bw / 2 + 30, W - bw / 2 - 30) if bw < 900 else 540
    by = 900 - bh  # bubble bottom sits at y 900
    k = pop_k(t, b['l0'] - 0.05, 0.3); out = 1 - prog(t, b['l1'] + 0.1, b['l1'] + 0.25)
    cr.save(); cr.translate(cx, by + bh / 2); cr.scale(k, k); cr.translate(-cx, -(by + bh / 2))
    rrect(cr, cx - bw / 2, by, bw, bh, 44); cr.set_source_rgba(1, 1, 1, out); cr.fill_preserve(); cr.set_source_rgba(*OUT, out); cr.set_line_width(7); cr.stroke()
    tx = clamp(sx, cx - bw / 2 + 60, cx + bw / 2 - 60); ty = by + bh - 4
    cr.new_path(); cr.move_to(tx - 26, ty); cr.line_to(sx + (20 if sx < 540 else -20), ty + 70); cr.line_to(tx + 26, ty); cr.close_path()
    cr.set_source_rgba(1, 1, 1, out); cr.fill()
    cr.new_path(); cr.move_to(tx - 26, ty); cr.line_to(sx + (20 if sx < 540 else -20), ty + 70); cr.line_to(tx + 26, ty)
    cr.set_source_rgba(*OUT, out); cr.set_line_width(7); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
    idx = 0
    for li, line in enumerate(lines):
        lw = cr.text_extents(' '.join(line)).x_advance; x = cx - lw / 2; y = by + 30 + lh * li + size * 0.95
        for tk in line:
            said = t >= times[idx] - 0.02; col = (RED if b['spk'] == 'ca' else BLUE) if said else (0.62, 0.62, 0.7)
            face(cr, size, 'Poppins ExtraBold'); cr.move_to(x, y); cr.text_path(tk); cr.set_source_rgba(*col, out); cr.fill()
            x += cr.text_extents(tk).x_advance + sp; idx += 1
    cr.restore()

def draw_fx(cr, t):
    tw_ = w('what', 'WHAT')
    if tw_ <= t < tw_ + 1.4:
        k = pop_k(t, tw_, 0.3); a = 1 - prog(t, tw_ + 1.0, tw_ + 1.4)
        if a > 0: cr.save(); cr.translate(860, 980); cr.scale(k, k); C.burst(cr, 0, 0, 95, 'WHAT?!', (1, 0.35, 0.3), 0.12); cr.restore()
    tb = w('best2', 'neighbours')
    if t >= tb:  # bump: hearts and a banner
        for i in range(10):
            t0 = tb + 0.1 + i * 0.07; k = prog(t, t0, t0 + 1.6)
            if 0 < k < 1:
                ang = -math.pi / 2 + (i - 4.5) * 0.28; d = 120 + 420 * ease_out(k)
                emoji(cr, '❤️', 540 + d * math.cos(ang), 1150 + d * math.sin(ang), 60 + 20 * math.sin(i), 1 - k ** 2)
        k = pop_k(t, tb + 0.2, 0.45); a = 1 - prog(t, w('cta', 'who') - 0.2, w('cta', 'who'))
        if a > 0:
            cr.save(); cr.translate(540, 470); cr.rotate(-0.04); cr.scale(k, k)
            rrect(cr, -400, -60, 800, 120, 50); cr.set_source_rgba(1, 0.42, 0.62, a); cr.fill_preserve(); cr.set_source_rgba(*OUT, a); cr.set_line_width(8); cr.stroke()
            ptext(cr, 'BEST NEIGHBOURS', 0, 24, 64, (1, 1, 1), a, sw=0, shadow=False); cr.restore()

def draw_title(cr, t):
    a = 1 - ease_io(prog(t, ln('hey')['l1'] - 0.2, ln('hey')['l1'] + 0.3))
    if a <= 0: return
    k = pop_k(t, 0.75, 0.4)
    cr.save(); cr.translate(540, 560); cr.rotate(-0.05); cr.scale(k, k)
    C.burst(cr, 0, 0, 150, 'VS', (1, 0.8, 0.15), 0.0)
    cr.restore()
    for txt, x, col, d in (('CANADA', 270, RED, 0.85), ('USA', 810, BLUE, 1.0)):
        kk = pop_k(t, d, 0.35); cr.save(); cr.translate(x, 560); cr.scale(kk, kk); ptext(cr, txt, 0, 25, 84, col, a, sw=10); cr.restore()

def draw_cta(cr, t):
    tq = w('cta', 'who')
    if t < tq: return
    k = pop_k(t, tq, 0.4)
    cr.save(); cr.translate(540, 455); cr.scale(k, k)
    rrect(cr, -470, -190, 940, 380, 44); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); C.outline(cr, 8)
    ptext(cr, 'WHO REALLY WON?', 0, -110, 76, OUT, 1, sw=0, shadow=False)
    for side, x, col, txt in (('ca', -220, RED, 'CANADA'), ('us', 220, BLUE, 'USA')):
        kk = pop_k(t, tq + (0.3 if side == 'ca' else 0.5), 0.35) * (1 + 0.04 * math.sin(t * 6 + x))
        cr.save(); cr.translate(x, 20); cr.scale(kk, kk); rrect(cr, -190, -55, 380, 110, 50); cr.set_source_rgb(*col); cr.fill_preserve(); C.outline(cr, 6)
        ptext(cr, txt, 0, 24, 60, (1, 1, 1), 1, sw=0, shadow=False); cr.restore()
    ptext(cr, 'COMMENT BELOW', 0, 150, 50, OUT, 1, sw=0, shadow=False); emoji(cr, '👇', 300, 132, 60, 1)
    cr.restore()
    tf = ln('obv')['l1'] + 0.2
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1780); cr.scale(k, k)
        txt = 'FOLLOW FOR MORE'; wd_ = tw(cr, txt, 54)
        rrect(cr, -wd_ / 2 - 90, -62, wd_ + 180, 96, 48); cr.set_source_rgb(1, 0.31, 0.64); cr.fill_preserve(); C.outline(cr, 7)
        ptext(cr, txt, 30, 4, 54, (1, 1, 1), 1, sw=6); emoji(cr, '🔔', -wd_ / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def render_frame(cr, t):
    draw_scene(cr, t)
    pos = positions(t)
    sp = speaking(t)
    order = ['ca', 'us'] if not sp or sp['spk'] == 'us' else ['us', 'ca']
    for spk in order: draw_ball(cr, t, spk, pos[spk])
    draw_fx(cr, t)
    draw_title(cr, t)
    draw_card(cr, t)
    draw_scoreboard(cr, t)
    draw_bubble(cr, t)
    draw_cta(cr, t)
    f = prog(t, TL['dur'] - 0.4, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- audio ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    g = np.random.default_rng(1)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 0.33
    prog_ = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]  # C G Am F: bouncy
    for bi in range(int(dur / beat) + 1):
        ch = prog_[(bi // 8) % 4]; t0 = bi * beat
        pt = np.arange(int(0.3 * SR)) / SR; m = ch[[0, 1, 2, 1][bi % 4]] + 12
        put(music, t0, 0.06 * (np.sin(2 * np.pi * note(m) * pt) + 0.3 * np.sin(4 * np.pi * note(m) * pt)) * np.exp(-pt * 14))  # pluck
        if bi % 2 == 0:
            bt_ = np.arange(int(0.25 * SR)) / SR; put(music, t0, 0.1 * np.sin(2 * np.pi * note(ch[0] - 24) * bt_) * np.exp(-bt_ * 9))
        if bi % 4 == 2:
            nz = g.standard_normal(int(0.05 * SR)); put(music, t0, 0.04 * nz * np.exp(-np.arange(len(nz)) / SR * 70))
    fx = np.zeros(n)
    def boing(t0, amp=0.12, f0=180, f1=520):
        L_ = np.arange(int(0.35 * SR)) / SR; f = f0 + (f1 - f0) * (1 - np.exp(-L_ * 12)); vib = 1 + 0.05 * np.sin(2 * np.pi * 18 * L_)
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(f * vib) / SR) * np.exp(-L_ * 6))
    def pop(t0, amp=0.12, f=1200):
        L_ = np.arange(int(0.08 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * f * L_ * (1 + 3 * L_)) * np.exp(-L_ * 50))
    def ding(t0, amp=0.1):
        L_ = np.arange(int(0.8 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * 1318 * L_) + 0.6 * np.sin(2 * np.pi * 1976 * L_)) * np.exp(-L_ * 5))
    def whoosh(t0, amp=0.14):
        L_ = int(0.4 * SR); nz = g.standard_normal(L_); sm = np.convolve(nz, np.ones(20) / 20, 'same'); put(fx, t0, amp * sm * np.sin(np.pi * np.linspace(0, 1, L_)))
    boing(0.65, 0.16); boing(0.8, 0.16, 200, 600); pop(0.75, 0.15, 900)
    for li, word, side in POINTS: ding(w(li, word))
    for li, word, kind in CARDS: whoosh(w(li, word) - 0.1)
    boing(w('what', 'WHAT'), 0.18, 300, 900); ding(w('tie', 'tie'), 0.12); boing(w('best2', 'neighbours'), 0.2, 150, 500)
    for i in range(10): pop(w('best2', 'neighbours') + 0.1 + i * 0.07, 0.06, 1500 + 60 * i)
    v = np.zeros(n)
    for b in T['lines']: put(v, b['l0'], b['audio'])
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck * 0.9 + fx + v
    mix *= np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 1.5)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(cache):
    global TL
    TL = build(MultiVoice(cache))
    POINTS.sort(key=lambda e: w(e[0], e[1])); CARDS.sort(key=lambda e: w(e[0], e[1]))  # events in spoken order

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    out = sys.argv[1]
    setup(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_balls'))
    print(f"duration {TL['dur']:.1f}s")
    for b in TL['lines']: print(f"  {b['key']:9s} {b['spk']} {b['l0']:6.2f}-{b['l1']:6.2f} {b['text'][:50]}")
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
