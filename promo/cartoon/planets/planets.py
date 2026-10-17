"""The Planet Show-Off (9:16 cartoon). The Sun (in sunglasses) hosts; each planet brags with one true fact and gets a score;
then Pluto asks to join. Ten AI voices, lip-synced mouths, hops on every word, blinking, karaoke speech bubbles, fact cards.
Usage: python3 planets.py <out.mp4> [--preview t1,t2,...]
"""
import asyncio, hashlib, json, math, os, random, re, subprocess, sys, wave
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
GOLD = hexc('#FFD60A')[:3]
VOICES = {  # character: (voice, rate, pitch)
    'sun': ('en-GB-RyanNeural', '+0%', '-8Hz'), 'mercury': ('en-US-AnaNeural', '+22%', '+10Hz'), 'venus': ('en-GB-SoniaNeural', '-6%', '+4Hz'),
    'earth': ('en-US-JennyNeural', '+6%', '+14Hz'), 'mars': ('en-GB-ThomasNeural', '+4%', '-4Hz'), 'jupiter': ('en-US-GuyNeural', '-12%', '-22Hz'),
    'saturn': ('en-IE-EmilyNeural', '+2%', '+10Hz'), 'uranus': ('en-NZ-MitchellNeural', '+4%', '+6Hz'), 'neptune': ('en-ZA-LeahNeural', '+12%', '+6Hz'),
    'pluto': ('en-GB-MaisieNeural', '+0%', '+22Hz')}
LINES = [  # key, speaker, text
    ('intro', 'sun', "Welcome to the Planet Show-Off! Every planet gets one line to prove it's the best."),
    ('mercury', 'mercury', "I'm the fastest! I zoom around the Sun in just eighty-eight days!"),
    ('venus', 'venus', "I'm the hottest planet. Four hundred and sixty-five degrees, darling."),
    ('sun1', 'sun', "Hotter than Mercury? Impressive."),
    ('earth', 'earth', "I'm the only planet we know of with life! Including you, watching this."),
    ('mars', 'mars', "I have the tallest volcano in the solar system. Two and a half times taller than Everest!"),
    ('jupiter', 'jupiter', "All the other planets could fit inside me... with room to spare."),
    ('saturn', 'saturn', "I'm so light, I'd float in a bathtub. If you could find one big enough."),
    ('uranus', 'uranus', "I spin on my side, like a rolling ball. Nobody knows exactly why."),
    ('neptune', 'neptune', "I have the fastest winds. Over two thousand kilometres an hour!"),
    ('sun2', 'sun', "Nice try, everyone. But I am ninety-nine point eight percent of the solar system's mass. I win."),
    ('pluto1', 'pluto', "Wait! Can I join?"),
    ('sun3', 'sun', "Sorry, Pluto. You're a dwarf planet now."),
    ('pluto2', 'pluto', "But... I have a heart."),
    ('aww', 'earth', "Awww!"),
    ('pluto3', 'pluto', "So... I'm in?"),
    ('sun4', 'sun', "Still no."),
    ('cta', 'earth', "Should Pluto be a planet again? Tell us in the comments!"),
]
ORDER = ['mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']
SIZE = {'mercury': 165, 'venus': 215, 'earth': 220, 'mars': 190, 'jupiter': 270, 'saturn': 205, 'uranus': 210, 'neptune': 210, 'pluto': 125}
SCORE = {'mercury': '7', 'venus': '8', 'earth': '10', 'mars': '8', 'jupiter': '9', 'saturn': '9', 'uranus': '7', 'neptune': '8'}
CARDS = {  # key: (trigger word, colour, emoji, big line, small line)
    'mercury': ('eighty', (0.6, 0.6, 0.65), '⚡', '1 YEAR = 88 DAYS', 'fastest planet: 47 km per second'),
    'venus': ('four', (1.0, 0.55, 0.2), '🔥', '~465 °C', 'hotter than Mercury: CO2 clouds trap heat'),
    'earth': ('life', (0.25, 0.6, 1.0), '🌱', 'THE ONLY KNOWN LIFE', '8 billion humans… and counting'),
    'mars': ('volcano', (0.9, 0.35, 0.2), '🌋', 'OLYMPUS MONS: ~22 km', 'Mount Everest: 8.8 km'),
    'jupiter': ('fit', (0.85, 0.55, 0.3), '🪐', '1,300+ EARTHS FIT INSIDE', 'more than all the other planets combined'),
    'saturn': ('float', (0.9, 0.75, 0.35), '🛁', 'LIGHTER THAN WATER', 'density 0.69 g/cm³ (water = 1)'),
    'uranus': ('side', (0.3, 0.8, 0.85), '🔄', 'TILTED 98°', 'probably knocked over by a giant crash'),
    'neptune': ('winds', (0.25, 0.4, 0.95), '💨', 'WINDS: ~2,100 km/h', 'the fastest in the solar system'),
    'sun2': ('ninety', (1.0, 0.7, 0.1), '☀️', '99.8% OF ALL THE MASS', 'in the whole solar system'),
    'sun3': ('dwarf', (0.7, 0.6, 0.5), '🤏', 'DWARF PLANET SINCE 2006', 'officially reclassified by astronomers'),
    'pluto2': ('heart', (1.0, 0.4, 0.55), '❤️', 'TOMBAUGH REGIO', "a real heart-shaped region of ice on Pluto"),
}

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
INTRO = 0.8
def build(voice):
    t, lines = INTRO, []
    pre = {k: 0.85 for k in ORDER}; pre.update({'pluto1': 0.5, 'sun2': 0.3})  # room for the stage change before a planet speaks
    post = {'venus': 0.2, 'sun2': 0.5, 'pluto2': 0.2, 'aww': 0.4, 'sun4': 0.6}
    for key, spk, text in LINES:
        t += pre.get(key, 0.0)
        a, words = voice.get(spk, text)
        b = dict(key=key, spk=spk, text=text, l0=t); b['l1'] = t + len(a) / SR
        b['words'] = [(t + s, t + e, x) for s, e, x in words]; b['tokens'] = text.split(); b['audio'] = a
        lines.append(b); t = b['l1'] + post.get(key, 0.22)
    dur = t + 2.8
    nf = int(dur * FPS) + 2; env = {k: np.zeros(nf) for k in VOICES}
    for b in lines:
        a = b['audio']; win = SR // FPS
        for f in range(int(b['l0'] * FPS), min(nf, int(b['l1'] * FPS) + 1)):
            i0 = int((f / FPS - b['l0']) * SR) - win // 2; seg = a[max(0, i0):max(0, i0 + win)]
            if len(seg): env[b['spk']][f] = float(np.sqrt(np.mean(seg ** 2)))
    for k in env:
        if (env[k] > 0).any(): env[k] = np.clip(env[k] / np.percentile(env[k][env[k] > 0], 90), 0, 1)
    return dict(lines=lines, by={b['key']: b for b in lines}, dur=dur, env=env)
def ln(k): return TL['by'][k]
def w(k, word, end=False):
    q = SC.norm(word)
    for s, e, x in ln(k)['words']:
        if any(SC.norm(p).startswith(q) for p in x.split()): return e if end else s
    if (k, word) not in _missing: _missing.add((k, word)); print(f'  ! no word "{word}" in {k}', file=sys.stderr)
    return ln(k)['l0']
def pop_k(t, t0, d=0.35): return max(1e-3, ease_back(prog(t, t0, t0 + d), 2.6))

# ---------- planets ----------
def ring(cr, x, y, rx, ry, rot, width, col, half):
    """Half of a planetary ring: half='back' (behind the planet) or 'front'."""
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    cr.rectangle(-rx * 1.2, -ry * 1.5 if half == 'back' else 0, rx * 2.4, ry * 1.5); cr.clip()
    cr.new_path(); cr.save(); cr.scale(rx, ry); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
    cr.new_sub_path(); cr.save(); cr.scale(rx - width, ry - width * ry / rx); cr.arc_negative(0, 0, 1, 2 * math.pi, 0); cr.restore()
    cr.set_source_rgb(*col); cr.fill_preserve(); C.outline(cr, 5); cr.restore()

def body(cr, kind, x, y, r):
    cols = {'mercury': (0.72, 0.7, 0.7), 'venus': (1.0, 0.82, 0.5), 'earth': (0.25, 0.6, 1.0), 'mars': (0.95, 0.45, 0.25),
            'jupiter': (0.95, 0.82, 0.62), 'saturn': (0.98, 0.86, 0.55), 'uranus': (0.55, 0.9, 0.95), 'neptune': (0.25, 0.42, 0.95),
            'pluto': (0.88, 0.76, 0.6), 'sun': (1, 0.85, 0.25)}
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgb(*cols[kind]); cr.fill()
    cr.save(); cr.new_path(); cr.arc(x, y, r - 2, 0, 2 * math.pi); cr.clip()
    def spot(dx, dy, rx, ry, col, rot=0.0):
        cr.save(); cr.translate(x + dx * r, y + dy * r); cr.rotate(rot); cr.scale(rx * r, ry * r); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgb(*col); cr.fill()
    if kind == 'mercury':
        for dx, dy, rr in ((-0.55, -0.45, 0.16), (0.5, -0.55, 0.12), (0.6, 0.4, 0.18), (-0.5, 0.55, 0.1), (0.05, 0.75, 0.09)): spot(dx, dy, rr, rr, (0.58, 0.56, 0.57))
    elif kind == 'venus':
        cr.set_line_width(r * 0.1); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for dy, ph in ((-0.6, 0), (-0.25, 1), (0.6, 2)):
            cr.new_path(); cr.move_to(x - r, y + dy * r); cr.curve_to(x - r * 0.3, y + (dy - 0.15) * r, x + r * 0.3, y + (dy + 0.15) * r, x + r, y + dy * r)
            cr.set_source_rgba(1, 0.95, 0.8, 0.7); cr.stroke()
    elif kind == 'earth':
        for dx, dy, rx, ry, rot in ((-0.5, -0.4, 0.38, 0.25, 0.4), (0.4, -0.6, 0.3, 0.18, -0.3), (0.55, 0.35, 0.32, 0.22, 0.8), (-0.35, 0.6, 0.25, 0.14, -0.5)):
            spot(dx, dy, rx, ry, (0.35, 0.82, 0.4), rot)
    elif kind == 'mars':
        for dx, dy, rr in ((-0.55, -0.45, 0.14), (0.5, -0.55, 0.1), (0.55, 0.45, 0.16), (-0.5, 0.5, 0.09)): spot(dx, dy, rr, rr, (0.8, 0.32, 0.18))
        spot(0, -0.92, 0.4, 0.14, (1, 1, 1))
    elif kind in ('jupiter', 'saturn'):
        bands = [(-0.75, 0.12, (0.85, 0.6, 0.4)), (-0.5, 0.1, (0.92, 0.75, 0.55)), (0.55, 0.1, (0.85, 0.6, 0.4)), (0.78, 0.12, (0.75, 0.48, 0.32))]
        if kind == 'saturn': bands = [(-0.7, 0.1, (0.92, 0.75, 0.42)), (0.65, 0.12, (0.9, 0.72, 0.4))]
        for dy, hh, col in bands: cr.rectangle(x - r, y + (dy - hh) * r, 2 * r, 2 * hh * r); cr.set_source_rgb(*col); cr.fill()
        if kind == 'jupiter': spot(-0.3, 0.62, 0.2, 0.1, (0.9, 0.38, 0.28)); cr.new_path()
    elif kind == 'uranus':
        spot(0.0, -0.85, 0.5, 0.2, (0.7, 0.96, 1.0))
    elif kind == 'neptune':
        spot(-0.5, -0.5, 0.2, 0.12, (0.12, 0.22, 0.6), -0.3); spot(-0.3, -0.72, 0.25, 0.05, (0.9, 0.95, 1.0), -0.2)
    elif kind == 'pluto':
        cr.save(); cr.translate(x - 0.5 * r, y + 0.42 * r); s = r * 0.27; cr.new_path(); cr.move_to(0, s * 0.9)
        cr.curve_to(-s * 1.4, -s * 0.1, -s * 0.6, -s * 1.1, 0, -s * 0.35); cr.curve_to(s * 0.6, -s * 1.1, s * 1.4, -s * 0.1, 0, s * 0.9); cr.close_path()
        cr.set_source_rgb(1, 0.95, 0.85); cr.fill(); cr.restore()
    cr.restore()
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); C.outline(cr, max(4, r * 0.04))
    C.shade(cr, x, y, r)

def character(cr, kind, x, y, r, t=0.0, talk=0.0, mood='happy', look=(0, 0), blink=0.0, sq=0.0, rot=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(1 + sq * 0.5, 1 - sq); cr.translate(-x, -y)
    if kind == 'sun':
        for i in range(12):
            a = i * math.pi / 6 + t * 0.4; cr.new_path()
            cr.move_to(x + r * 1.02 * math.cos(a - 0.13), y + r * 1.02 * math.sin(a - 0.13)); cr.line_to(x + r * 1.42 * math.cos(a), y + r * 1.42 * math.sin(a))
            cr.line_to(x + r * 1.02 * math.cos(a + 0.13), y + r * 1.02 * math.sin(a + 0.13)); cr.close_path()
            cr.set_source_rgb(1, 0.68, 0.15); cr.fill_preserve(); C.outline(cr, 5)
    if kind == 'saturn': ring(cr, x, y, r * 1.85, r * 0.86, -0.18, r * 0.36, (0.95, 0.78, 0.5), 'back')
    if kind == 'uranus': ring(cr, x, y, r * 1.5, r * 0.82, 1.3, r * 0.08, (0.75, 0.95, 1.0), 'back')
    body(cr, kind, x, y, r)
    sad = mood == 'sad'
    C.eyes(cr, x, y - r * 0.12, r * 0.22, (look[0], 0.55) if sad else look, blink, 'happy' if sad else mood)
    if kind == 'sun':  # sunglasses
        for side in (-1, 1):
            cr.new_path(); cr.save(); cr.translate(x + side * r * 0.21, y - r * 0.14); cr.scale(r * 0.24, r * 0.17); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
            cr.set_source_rgb(0.08, 0.06, 0.12); cr.fill_preserve(); C.outline(cr, 5)
            cr.new_path(); cr.arc(x + side * r * 0.21 - r * 0.08, y - r * 0.2, r * 0.05, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.8); cr.fill()
        cr.new_path(); cr.move_to(x - r * 0.04, y - r * 0.16); cr.line_to(x + r * 0.04, y - r * 0.16); C.outline(cr, 6)
    if sad and talk < 0.1:
        cr.new_path(); cr.move_to(x - r * 0.2, y + r * 0.45); cr.curve_to(x - r * 0.1, y + r * 0.3, x + r * 0.1, y + r * 0.3, x + r * 0.2, y + r * 0.45); C.outline(cr, max(4, r * 0.05))
        cr.new_path(); cr.move_to(x + r * 0.3, y - r * 0.0); cr.curve_to(x + r * 0.22, y + r * 0.15, x + r * 0.38, y + r * 0.15, x + r * 0.3, y); cr.set_source_rgb(0.5, 0.8, 1.0); cr.fill()
    else:
        C.mouth(cr, x, y + r * 0.38, r * 0.42, talk, 'happy' if sad else mood)
    if mood == 'happy' and kind not in ('sun', 'pluto'): C.cheeks(cr, x, y + r * 0.22, r * 0.12, r * 0.52)
    if kind == 'saturn': ring(cr, x, y, r * 1.85, r * 0.86, -0.18, r * 0.36, (0.95, 0.78, 0.5), 'front')
    if kind == 'uranus': ring(cr, x, y, r * 1.5, r * 0.82, 1.3, r * 0.08, (0.75, 0.95, 1.0), 'front')
    cr.restore()

# ---------- scene ----------
_rnd = random.Random(4)
STARS = [(_rnd.uniform(0, W), _rnd.uniform(0, H), _rnd.uniform(4, 10), _rnd.uniform(0, 6.28)) for _ in range(70)]
def draw_scene(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.13, 0.08, 0.35); g.add_color_stop_rgb(1, 0.38, 0.18, 0.55)
    cr.set_source(g); cr.paint()
    for i in range(0, W, 36):
        for j in range(0, H, 36):
            cr.new_path(); cr.arc(i + (18 if (j // 36) % 2 else 0), j, 3.0, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.07); cr.fill()
    for sx, sy, rr, ph in STARS:
        a = 0.5 + 0.5 * math.sin(t * 2 + ph); cr.new_path()
        for k in range(8):
            ang = k * math.pi / 4; q = rr if k % 2 == 0 else rr * 0.35; (cr.move_to if k == 0 else cr.line_to)(sx + q * math.cos(ang), sy + q * math.sin(ang))
        cr.close_path(); cr.set_source_rgba(1, 1, 0.8, 0.5 + 0.4 * a); cr.fill()
    # spotlight and stage
    cr.new_path(); cr.move_to(470, 0); cr.line_to(610, 0); cr.line_to(840, 1470); cr.line_to(240, 1470); cr.close_path()
    sg = cairo.LinearGradient(0, 0, 0, 1470); sg.add_color_stop_rgba(0, 1, 1, 0.85, 0.0); sg.add_color_stop_rgba(1, 1, 1, 0.85, 0.16)
    cr.set_source(sg); cr.fill()
    cr.new_path(); cr.save(); cr.translate(540, 1480); cr.scale(330, 60); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgb(0.55, 0.35, 0.85); cr.fill_preserve(); C.outline(cr, 7)
    cr.new_path(); cr.save(); cr.translate(540, 1468); cr.scale(300, 46); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgb(0.7, 0.5, 1.0); cr.fill()

# ---------- who is on stage ----------
def stage_turns():
    """(time the planet arrives, kind) for each stage occupant."""
    T = []
    for k in ORDER: T.append((ln(k)['l0'] - 0.65, k))
    T.append((ln('sun2')['l0'] - 0.3, None)); T.append((ln('pluto1')['l0'] - 0.5, 'pluto'))
    return T

def stage_state(t):
    T = TL['turns']; cur, prev, tc = None, None, -10
    for ts, k in T:
        if t >= ts: prev, cur, tc = cur, k, ts
    return cur, prev, tc

SUN_P = (885, 230, 112)
def env_of(spk, t):
    f = min(int(t * FPS), len(TL['env'][spk]) - 1); return TL['env'][spk][f]
def hop(t, spk):
    y, sq = 0.0, 0.0
    for b in TL['lines']:
        if b['spk'] != spk or not (b['l0'] - 0.1 <= t <= b['l1'] + 0.4): continue
        for s, e, x in b['words']:
            if s <= t < s + 0.28:
                k = (t - s) / 0.28; y = max(y, 20 * math.sin(math.pi * k)); sq = 0.06 * math.cos(math.pi * k * 2) * (1 - k)
    return y, sq
def blink(t, off): ph = (t + off) % 3.3; return max(0.0, 1 - abs(ph - 0.1) / 0.08) if ph < 0.2 else 0.0
def speaking(t):
    for b in TL['lines']:
        if b['l0'] - 0.05 <= t < b['l1'] + 0.25: return b
    return None

def mood_for(kind, t):
    if kind == 'pluto':
        if ln('sun3')['l0'] + 0.6 <= t < ln('pluto2')['l0']: return 'sad'
        if t >= w('sun4', 'Still') + 0.2: return 'sad'
        if t >= w('pluto2', 'heart'): return 'happy'
        return 'shocked' if t < ln('pluto1')['l1'] + 0.2 else 'happy'
    if kind == 'venus' and t >= w('venus', 'darling') - 0.2: return 'sly'
    if kind == 'mars': return 'grumpy'
    if kind == 'jupiter' and t >= w('jupiter', 'room'): return 'sly'
    if kind == 'mercury': return 'happy'
    return 'happy'

LINE_Y = 1690; SLOT_X = {k: x for k, x in zip(ORDER, np.linspace(85, 995, len(ORDER)))}
def slot_r(kind): return 22 + SIZE[kind] * 0.09
def stage_y(kind): return 1445 - SIZE[kind]
FLY = 0.6
def score_t(kind): return ln(kind)['l1'] - 0.25
def stage_pose(kind, phase, k):
    """Where a planet is while flying lineup -> stage (phase 'in') or stage -> lineup ('out'), k in 0..1."""
    R, ty = SIZE[kind], stage_y(kind)
    if kind == 'pluto': sx, sy, sr = 1250, 1250, R  # Pluto sneaks in from off-screen
    else: sx, sy, sr = SLOT_X[kind], LINE_Y, slot_r(kind)
    p = ease_io(k) if phase == 'in' else 1 - ease_io(k)
    return lerp(sx, 540, p), lerp(sy, ty, p) - math.sin(math.pi * p) * (120 if kind == 'pluto' else 330), lerp(sr, R, p)

def in_flight(kind, t):
    """True while this planet is not sitting in its lineup slot."""
    cur, prev, tc = stage_state(t)
    return kind == cur or (kind == prev and t - tc < FLY)

def draw_stage(cr, t):
    cur, prev, tc = stage_state(t)
    k = clamp((t - tc) / FLY)
    for kind, phase in ((prev, 'out'), (cur, 'in')):
        if not kind: continue
        if phase == 'out' and k >= 1: continue
        x, y, r = stage_pose(kind, phase, k)
        if phase == 'in':
            land = t - tc - FLY; sq = 0.16 * math.exp(-land * 7) * math.cos(land * 20) if land > 0 else -0.08 * math.sin(math.pi * k)
        else: sq = -0.08 * math.sin(math.pi * k)
        talk = env_of(kind, t)
        hy, hsq = hop(t, kind)
        sp = speaking(t); look = (0.6, -0.5) if (sp and sp['spk'] == 'sun') else (0, 0.1)
        if kind == 'pluto' and t < ln('pluto1')['l0']: look = (-0.6, 0)
        mood = mood_for(kind, t)
        if phase == 'in' and k >= 1:
            cr.new_path(); cr.save(); cr.translate(x, 1478); cr.scale(1, 0.2); cr.arc(0, 0, r * 0.8, 0, 2 * math.pi); cr.restore()
            cr.set_source_rgba(0, 0, 0, 0.25); cr.fill()
        spin = math.sin(math.pi * k) * (0.5 if phase == 'in' else -0.5) if kind != 'pluto' else 0.0
        character(cr, kind, x, y - hy, r, t, talk if talk > 0.08 else 0.0, mood, look,
                  blink(t, ORDER.index(kind) * 0.7 if kind in ORDER else 2.2), sq + hsq, spin)
        if kind in SCORE:  # score from the Sun
            ts = score_t(kind)
            if t >= ts: badge(cr, x + r * 0.95, y - r * 0.9, SCORE[kind] + '/10', pop_k(t, ts, 0.4) * (1 - ease_io(k) if phase == 'out' else 1))
        if kind == 'pluto' and phase == 'in':
            ts = w('pluto2', 'heart') + 0.4
            if ts <= t < w('sun4', 'Still'): kk = pop_k(t, ts, 0.4); badge(cr, x + r * 1.25, y - r * 1.1, '', kk, (1, 0.45, 0.65)); emoji(cr, '❤️', x + r * 1.25, y - r * 1.1, 70 * kk, 1)
            ts = w('sun4', 'Still') + 0.15
            if t >= ts: badge(cr, x + r * 1.25, y - r * 1.1, '0/10', pop_k(t, ts, 0.4), (0.75, 0.75, 0.8))

def badge(cr, x, y, txt, k, col=GOLD, s=1.0):
    cr.save(); cr.translate(x, y); cr.rotate(0.15); cr.scale(k * s, k * s); cr.new_path()
    for i in range(20):
        a = i * math.pi / 10; rr = 74 if i % 2 == 0 else 58; (cr.move_to if i == 0 else cr.line_to)(rr * math.cos(a), rr * math.sin(a))
    cr.close_path(); cr.set_source_rgb(*col); cr.fill_preserve(); C.outline(cr, 6)
    ptext(cr, txt, 0, 14 if len(txt) <= 2 else 13, 52 if len(txt) <= 2 else (40 if len(txt) <= 4 else 34), OUT, 1, sw=0, shadow=False); cr.restore()

def draw_sun(cr, t):
    x, y, r = SUN_P
    k = pop_k(t, 0.05, 0.5)
    hy, hsq = hop(t, 'sun'); talk = env_of('sun', t)
    m = 'sly' if t >= w('sun2', 'win') - 0.3 else 'happy'
    character(cr, 'sun', x, y - hy, r * k, t, talk if talk > 0.08 else 0.0, m, (-0.5, 0.4), 0.0, hsq)
    ts = w('sun2', 'win')
    if ts <= t < ln('pluto1')['l0'] + 0.3: badge(cr, x - r * 1.05, y + r * 0.95, '11/10', pop_k(t, ts + 0.1, 0.4))

def draw_lineup(cr, t):
    """The planets waiting their turn at the bottom; each flies up to the stage and back."""
    rrect(cr, 25, LINE_Y - 85, 1030, 190, 50); cr.set_source_rgba(0.08, 0.04, 0.2, 0.55); cr.fill()
    aww = w('aww', 'Awww')
    for i, kind in enumerate(ORDER):
        x, r = SLOT_X[kind], slot_r(kind)
        if in_flight(kind, t):  # an empty glowing slot
            cr.new_path(); cr.arc(x, LINE_Y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.12); cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, 0.35); cr.set_line_width(3); cr.set_dash([8, 8]); cr.stroke(); cr.set_dash([]); continue
        kk = pop_k(t, 0.25 + i * 0.07, 0.4)
        hy, hsq = hop(t, kind)
        b = abs(math.sin(t * 7 + i)) * 16 if t < INTRO + 1.0 or aww <= t < aww + 1.5 else 0
        talk = env_of(kind, t)
        look = (0.6, -0.5) if t > ln('sun2')['l0'] and t < ln('pluto1')['l0'] else ((0.4 if x < 540 else -0.4), -0.5)
        if t >= ln('pluto1')['l0']: look = ((0.7 if x < 540 else -0.7), -0.6)
        mood = 'shocked' if ln('sun2')['l0'] + 2.5 <= t < ln('sun2')['l1'] + 0.3 else 'happy'
        character(cr, kind, x, LINE_Y - b - hy, r * kk, t, talk if talk > 0.08 else 0.0, mood, look, blink(t, i * 0.45), hsq)
        if kind in SCORE and t >= score_t(kind):
            badge(cr, x + r * 0.8, LINE_Y - r * 0.85, SCORE[kind], pop_k(t, TL['back'][kind], 0.3), s=0.42)
        if aww <= t < aww + 2.2:  # everyone melts at Pluto's heart
            q = prog(t, aww + i * 0.05, aww + 2.2); emoji(cr, '❤️', x + 12 * math.sin(t * 5 + i), LINE_Y - r - 30 - 110 * q, 38, 1 - q)

def draw_card(cr, t):
    cur = None
    for key, (word, col, e, big, small) in CARDS.items():
        t0 = w(key, word)
        nxt_l = TL['lines'][[b['key'] for b in TL['lines']].index(key) + 1]
        t1 = nxt_l['l0'] - 0.1 if key not in ('venus', 'sun3') else (ln('sun1')['l1'] + 0.2 if key == 'venus' else ln('pluto2')['l0'] - 0.1)
        if t0 <= t < t1: cur = (key, t0, t1, col, e, big, small)
    if not cur: return
    key, t0, t1, col, e, big, small = cur
    a = 1 - ease_io(prog(t, t1 - 0.25, t1)); k = pop_k(t, t0, 0.45)
    cr.save(); cr.translate(540, 540); cr.scale(k, k)
    rrect(cr, -470, -140, 940, 280, 40); cr.set_source_rgba(1, 1, 1, a); cr.fill_preserve(); cr.set_source_rgba(*OUT, a); cr.set_line_width(8); cr.stroke()
    emoji(cr, e, -360, -2, 130, a, rot=0.1 * math.sin(t * 3))
    fs = fit(cr, big, 64, 640); ptext(cr, big, 90, -6, fs, col, a, sw=0, shadow=False)
    fs2 = fit(cr, small, 34, 660, 'Poppins ExtraBold'); ptext(cr, small, 90, 62, fs2, OUT, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    cr.restore()

def wrap(cr, toks, size, maxw):
    face(cr, size, 'Poppins ExtraBold'); sp = cr.text_extents(' ').x_advance; lines, cur, cw = [], [], 0
    for tk in toks:
        wd = cr.text_extents(tk).x_advance
        if cur and cw + sp + wd > maxw: lines.append(cur); cur, cw = [], 0
        cur.append(tk); cw += (sp if cw else 0) + wd
    if cur: lines.append(cur)
    return lines

NAME_COL = {'sun': (0.85, 0.5, 0.0), 'mercury': (0.45, 0.45, 0.5), 'venus': (0.85, 0.45, 0.1), 'earth': (0.15, 0.45, 0.9), 'mars': (0.85, 0.3, 0.15),
            'jupiter': (0.7, 0.42, 0.2), 'saturn': (0.75, 0.55, 0.15), 'uranus': (0.15, 0.6, 0.7), 'neptune': (0.2, 0.3, 0.85), 'pluto': (0.85, 0.3, 0.5)}
def draw_bubble(cr, t):
    b = speaking(t)
    if not b or (b['key'] == 'cta' and t >= w('cta', 'Should') + 0.1): return
    toks, words = b['tokens'], b['words']; times = []; ti = 0
    for s, e, x in words:
        for _ in range(max(1, len(x.split()))):
            if ti < len(toks): times.append(s); ti += 1
    while len(times) < len(toks): times.append(times[-1] if times else b['l0'])
    is_sun = b['spk'] == 'sun'; size = 44 if is_sun and len(toks) > 12 else 48
    lines = wrap(cr, toks, size, 590 if is_sun else 820)
    face(cr, size, 'Poppins ExtraBold'); sp = cr.text_extents(' ').x_advance; lh = size * 1.25
    bw = max(cr.text_extents(' '.join(l)).x_advance for l in lines) + 80; bh = lh * len(lines) + 56
    if is_sun: cx, by = 718 - bw / 2, 55; tip = (SUN_P[0] - SUN_P[2] * 1.0, SUN_P[1] + 10)
    elif b['spk'] == 'earth' and b['key'] in ('aww', 'cta'):
        cx, by = 250, 1545 - bh; tip = (SLOT_X['earth'] - 15, LINE_Y - 50)
    else:
        top = stage_y(b['spk']) - SIZE[b['spk']]; cx, by = 540, min(985, top - 50) - bh; tip = (565, top - 12)
    k = pop_k(t, b['l0'] - 0.05, 0.3); out = 1 - prog(t, b['l1'] + 0.1, b['l1'] + 0.25)
    cr.save(); cr.translate(cx, by + bh / 2); cr.scale(k, k); cr.translate(-cx, -(by + bh / 2))
    rrect(cr, cx - bw / 2, by, bw, bh, 44); cr.set_source_rgba(1, 1, 1, out); cr.fill_preserve(); cr.set_source_rgba(*OUT, out); cr.set_line_width(7); cr.stroke()
    bx = clamp(tip[0], cx - bw / 2 + 50, cx + bw / 2 - 50); edge_y = by + bh - 4 if tip[1] > by + bh else by + 4
    if is_sun: bx, edge_y = cx + bw / 2 - 4, by + bh / 2
    cr.new_path()
    if is_sun: cr.move_to(bx, edge_y - 22); cr.line_to(tip[0], tip[1]); cr.line_to(bx, edge_y + 22)
    else: cr.move_to(bx - 24, edge_y); cr.line_to(tip[0], tip[1]); cr.line_to(bx + 24, edge_y)
    cr.close_path(); cr.set_source_rgba(1, 1, 1, out); cr.fill_preserve(); cr.set_source_rgba(*OUT, out); cr.set_line_width(7); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
    if is_sun: cr.rectangle(bx - 8, edge_y - 18, 8, 36)
    else: cr.rectangle(bx - 18, edge_y - 8, 36, 10)
    cr.set_source_rgba(1, 1, 1, out); cr.fill()
    idx = 0; col = NAME_COL[b['spk']]
    for li, line in enumerate(lines):
        lw = cr.text_extents(' '.join(line)).x_advance; x = cx - lw / 2; y = by + 28 + lh * li + size * 0.95
        for tk in line:
            said = t >= times[idx] - 0.02
            face(cr, size, 'Poppins ExtraBold'); cr.move_to(x, y); cr.text_path(tk); cr.set_source_rgba(*(col if said else (0.62, 0.62, 0.7)), out); cr.fill()
            x += cr.text_extents(tk).x_advance + sp; idx += 1
    cr.restore()

def draw_cta(cr, t):
    tq = w('cta', 'Should')
    if t < tq: return
    k = pop_k(t, tq, 0.4)
    cr.save(); cr.translate(540, 560); cr.scale(k, k)
    rrect(cr, -480, -210, 960, 420, 44); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); C.outline(cr, 8)
    ptext(cr, 'SHOULD PLUTO BE A', 0, -120, 60, OUT, 1, sw=0, shadow=False)
    ptext(cr, 'PLANET AGAIN?', 0, -45, 78, (0.85, 0.3, 0.5), 1, sw=0, shadow=False)
    for x, col, txt, d in ((-210, (0.3, 0.8, 0.4), 'YES', 0.3), (210, (0.9, 0.3, 0.3), 'NO', 0.5)):
        kk = pop_k(t, tq + d, 0.35) * (1 + 0.04 * math.sin(t * 6 + x))
        cr.save(); cr.translate(x, 65); cr.scale(kk, kk); rrect(cr, -170, -52, 340, 104, 50); cr.set_source_rgb(*col); cr.fill_preserve(); C.outline(cr, 6)
        ptext(cr, txt, 0, 24, 62, (1, 1, 1), 1, sw=0, shadow=False); cr.restore()
    ptext(cr, 'COMMENT BELOW', -20, 178, 46, OUT, 1, sw=0, shadow=False); emoji(cr, '👇', 230, 160, 56, 1)
    cr.restore()
    tf = ln('cta')['l1'] + 0.2
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1000); cr.scale(k, k)
        txt = 'FOLLOW FOR MORE'; wd_ = tw(cr, txt, 54)
        rrect(cr, -wd_ / 2 - 90, -62, wd_ + 180, 96, 48); cr.set_source_rgb(1, 0.31, 0.64); cr.fill_preserve(); C.outline(cr, 7)
        ptext(cr, txt, 30, 4, 54, (1, 1, 1), 1, sw=6); emoji(cr, '🔔', -wd_ / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def draw_fx(cr, t):
    tw_ = w('pluto1', 'Wait')
    if tw_ <= t < tw_ + 1.2:
        k = pop_k(t, tw_, 0.3); a = 1 - prog(t, tw_ + 0.9, tw_ + 1.2)
        if a > 0: cr.save(); cr.translate(270, 1130); cr.scale(k, k); C.burst(cr, 0, 0, 85, 'WAIT!', (1, 0.8, 0.2), -0.12); cr.restore()
    tn = w('sun4', 'Still')
    if tn <= t < tn + 1.6:
        k = pop_k(t, tn, 0.3); a = 1 - prog(t, tn + 1.2, tn + 1.6)
        if a > 0: cr.save(); cr.translate(640, 470); cr.scale(k, k); C.burst(cr, 0, 0, 85, 'NOPE!', (1, 0.35, 0.3), 0.12); cr.restore()
    th = w('pluto2', 'heart')
    if th <= t < ln('pluto3')['l0']:
        for i in range(8):
            t0 = th + i * 0.12; k = prog(t, t0, t0 + 1.4)
            if 0 < k < 1:
                ang = -math.pi / 2 + (i - 3.5) * 0.35; d = 80 + 260 * ease_out(k)
                emoji(cr, '❤️', 540 + d * math.cos(ang), stage_y('pluto') - 40 + d * math.sin(ang), 50, 1 - k ** 2)

TITLE_COLS = [(1, 0.84, 0.04), (1, 0.55, 0.2), (0.35, 0.85, 0.45), (0.3, 0.7, 1.0), (1, 0.4, 0.65), (0.75, 0.55, 1.0), (1, 0.84, 0.04), (0.3, 0.9, 0.9)]
def draw_title(cr, t):
    """The hook: the show's title slams in letter by letter, then shrinks away when Mercury flies up."""
    t_out = TL['turns'][0][0]
    if t >= t_out + 0.35: return
    ko = 1 - ease_io(prog(t, t_out, t_out + 0.35))
    cr.save(); cr.translate(540, 1080); cr.scale(ko, ko); cr.rotate(-0.04 + 0.015 * math.sin(t * 2.2)); cr.translate(-540, -1080)
    k = pop_k(t, 0.0, 0.3); cr.save(); cr.translate(540, 900); cr.scale(k, k)
    ptext(cr, 'THE PLANET', 0, 0, 96, (1, 1, 1), 1, sw=14); cr.restore()
    word, size = 'SHOW-OFF', 178; size *= min(1.0, 940 / tw(cr, word, size)); total = tw(cr, word, size); x = 540 - total / 2
    for i, ch in enumerate(word):
        cw = tw(cr, ch, size); kk = pop_k(t, 0.08 + i * 0.05, 0.3); wob = 10 * math.sin(t * 5 + i * 0.9)
        cr.save(); cr.translate(x + cw / 2, 1085 + wob); cr.scale(kk, kk); cr.rotate(0.06 * math.sin(i * 2.1))
        ptext(cr, ch, 0, 0, size, TITLE_COLS[i % len(TITLE_COLS)], 1, sw=16); cr.restore(); x += cw
    k = pop_k(t, 0.5, 0.35); cr.save(); cr.translate(540, 1215); cr.scale(k, k)
    txt = '8 PLANETS. 1 WINNER.'; wd_ = tw(cr, txt, 54)
    rrect(cr, -wd_ / 2 - 40, -50, wd_ + 80, 96, 48); cr.set_source_rgb(1, 0.31, 0.64); cr.fill_preserve(); C.outline(cr, 7)
    ptext(cr, txt, 0, 18, 54, (1, 1, 1), 1, sw=0, shadow=False); cr.restore()
    cr.restore()

def draw_mass(cr, t):
    """While the Sun brags: its share of the solar system's mass as a bar chart on the empty stage."""
    t0, t1 = w('sun2', 'ninety'), TL['turns'][-1][0]
    if not t0 <= t < t1 + 0.3: return
    a = 1 - prog(t, t1, t1 + 0.3); k = pop_k(t, t0, 0.4)
    cr.save(); cr.translate(540, 1210); cr.scale(k, k)
    rrect(cr, -470, -190, 940, 380, 40); cr.set_source_rgba(1, 1, 1, a); cr.fill_preserve(); cr.set_source_rgba(*OUT, a); cr.set_line_width(8); cr.stroke()
    ptext(cr, 'MASS OF THE SOLAR SYSTEM', 0, -125, 40, OUT, a, sw=0, shadow=False)
    fill = ease_out(prog(t, t0 + 0.3, t0 + 1.6))
    for y, lab, share, col in ((-40, 'SUN', 0.998, (1, 0.72, 0.1)), (100, 'EVERYTHING ELSE', 0.002, (0.45, 0.6, 1.0))):
        ptext(cr, lab, -420, y - 22, 32, OUT, a, anchor='l', sw=0, shadow=False)
        rrect(cr, -420, y, 840, 50, 25); cr.set_source_rgba(0.9, 0.9, 0.95, a); cr.fill()
        bw = max(14, 840 * share * fill); rrect(cr, -420, y, bw, 50, 25); cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(*OUT, a); cr.set_line_width(5); cr.stroke()
        pct = f'{share * 100 * fill:.1f}%'
        ptext(cr, pct, 400 if share > 0.5 else -330, y + 38, 36, (1, 1, 1) if share > 0.5 else OUT, a, anchor='r' if share > 0.5 else 'l', sw=6 if share > 0.5 else 0, shadow=False)
    cr.restore()

def render_frame(cr, t):
    draw_scene(cr, t)
    draw_lineup(cr, t)
    draw_stage(cr, t)
    draw_title(cr, t)
    draw_mass(cr, t)
    draw_sun(cr, t)
    draw_fx(cr, t)
    draw_card(cr, t)
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
    music = np.zeros(n); beat = 0.36
    prog_ = [[60, 64, 67, 71], [57, 60, 64, 67], [62, 65, 69, 72], [55, 59, 62, 65]]  # Cmaj7 Am7 Dm7 G7: game-show swing
    for bi in range(int(dur / beat) + 1):
        ch = prog_[(bi // 8) % 4]; t0 = bi * beat
        pt = np.arange(int(0.3 * SR)) / SR; m = ch[[0, 2, 1, 3][bi % 4]] + 12
        put(music, t0, 0.05 * (np.sin(2 * np.pi * note(m) * pt) + 0.35 * np.sin(6 * np.pi * note(m) * pt)) * np.exp(-pt * 12))
        if bi % 2 == 0:
            bt_ = np.arange(int(0.3 * SR)) / SR; put(music, t0, 0.09 * np.sin(2 * np.pi * note(ch[0] - 24) * bt_) * np.exp(-bt_ * 8))
        if bi % 2 == 1:
            nz = g.standard_normal(int(0.04 * SR)); put(music, t0, 0.03 * nz * np.exp(-np.arange(len(nz)) / SR * 80))
    fx = np.zeros(n)
    def boing(t0, amp=0.12, f0=180, f1=520):
        L_ = np.arange(int(0.35 * SR)) / SR; f = f0 + (f1 - f0) * (1 - np.exp(-L_ * 12)); vib = 1 + 0.05 * np.sin(2 * np.pi * 18 * L_)
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(f * vib) / SR) * np.exp(-L_ * 6))
    def whoosh(t0, amp=0.16):
        L_ = int(0.5 * SR); nz = g.standard_normal(L_); sm = np.convolve(nz, np.ones(20) / 20, 'same'); put(fx, t0, amp * sm * np.sin(np.pi * np.linspace(0, 1, L_)))
    def ding(t0, amp=0.1):
        L_ = np.arange(int(0.8 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * 1318 * L_) + 0.6 * np.sin(2 * np.pi * 1976 * L_)) * np.exp(-L_ * 5))
    def buzzer(t0, amp=0.1):
        L_ = np.arange(int(0.45 * SR)) / SR; put(fx, t0, amp * np.sign(np.sin(2 * np.pi * 110 * L_)) * np.exp(-L_ * 3))
    def aww(t0, amp=0.08):
        L_ = np.arange(int(1.0 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(700 - 250 * L_) / SR) * np.exp(-L_ * 2))
    for ts, k in T['turns']: whoosh(ts - 0.05); boing(ts + FLY - 0.03, 0.13)
    for k in SCORE: ding(score_t(k))
    ding(w('sun2', 'win') + 0.1, 0.13); buzzer(w('sun4', 'Still'), 0.1); boing(w('pluto1', 'Wait'), 0.15, 400, 1200)
    for key, (word, *_ ) in CARDS.items(): boing(w(key, word) - 0.05, 0.05, 600, 900)
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
    TL = build(MultiVoice(cache)); TL['turns'] = stage_turns()
    TL['back'] = {k: TL['turns'][i + 1][0] + FLY for i, k in enumerate(ORDER)}

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
    setup(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_planets'))
    print(f"duration {TL['dur']:.1f}s")
    for b in TL['lines']: print(f"  {b['key']:8s} {b['spk']:8s} {b['l0']:6.2f}-{b['l1']:6.2f} {b['text'][:44]}")
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
