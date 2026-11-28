# GeoBall Wars Short: "The Only Flag That Flips for War". The Philippine flag is flown red-side-up in wartime (RA 8491).
# Usage: python3 flip.py <data_dir> <out.mp4> [--preview t1,t2,...]
import os, sys, math, subprocess, wave
import numpy as np, cairo
from multiprocessing import Pool
import phjp as P
import china as C
import warballs as B
from warballs import ball
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON
from popu import streaks, shake
from quiz import clamp, lerp, prog, ease_io, ease_out, hexc, SR
src = open('auph.py').read(); i = src.index('def set_australia('); j = src.index('\ndef ', i + 5); exec(src[i:j], P.__dict__)
PH_C, AU_C, JP_C, RED = hexc('#3D7BFF')[:3], hexc('#FFC233')[:3], hexc('#FF4D5E')[:3], hexc('#E8333F')[:3]
NARR = ('en-US-GuyNeural', '+6%')
VOICE = {'Philippines': ('fil-PH-AngeloNeural', '+4%'), 'Australia': ('en-AU-WilliamNeural', '+6%'), 'Japan': ('ja-JP-KeitaNeural', '+2%')}
LINES = [
    ('h1', 'Philippines', "Ahh. A peaceful day. Adobo time!"),
    ('h2', None, "But the Philippines has a secret that almost no other country has."),
    ('h3', 'Philippines', "Wait… is that a challenge?"),
    ('flip', 'Philippines', "War mode."),
    ('n1', None, "In peacetime, the Philippine flag flies with blue on top."),
    ('n2', None, "But in a state of war, it's flipped. Red goes on top."),
    ('n3', None, "Blue stands for peace and justice. Red stands for patriotism and valour."),
    ('n3b', None, "The three stars are Luzon, Visayas and Mindanao. The sun's eight rays honour the first eight provinces to revolt against Spain."),
    ('n4', None, "And the war rule is written into Philippine law, in Republic Act eighty-four ninety-one."),
    ('r1', 'Australia', "Wait, you can DO that?!"),
    ('r2a', 'Australia', "Watch this, mate!"),
    ('r2b', 'Australia', "…I'm just upside down, aren't I."),
    ('r3', 'Japan', "Mine looks the same either way."),
    ('r4', 'Philippines', "So. Who wants to fight me?"),
    ('r5', 'Australia', "Uh… what's the challenge, anyway?"),
    ('r6', None, "The challenge was… karaoke!"),
    ('r7', 'Philippines', "Karaoke? Then this IS war."),
    ('cta', None, "Which other flag has a secret meaning? Comment below, and subscribe for more!")]
SPK = {k: s for k, s, _ in LINES}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1',)
C.SAY = {None: {'valour': 'valor'}}
C.HOT = ('war', 'flipped', 'red', 'blue', 'secret', 'peace', 'karaoke', 'law', 'comment', 'subscribe', 'mode')
C.TAIL_OVERRIDE = {k: 0.3 for k, _, _ in LINES}; C.TAIL_OVERRIDE.update({'h3': 0.5, 'flip': 1.3, 'n2': 0.9, 'r2a': 1.2, 'r2b': 0.5, 'r3': 0.6, 'r6': 1.0, 'r7': 0.8, 'cta': 3.6})
P.VOICE_OF.clear(); P.VOICE_OF.update({C.say(k, s): (VOICE[sp] if sp else NARR) for k, sp, s in LINES})
bt, w = C.bt, C.w
COL = {'Philippines': PH_C, 'PHW': RED, 'Australia': AU_C, 'AUD': AU_C, 'Japan': JP_C}

def load_flags(d):
    for nm, f in (('Philippines', 'ph'), ('Australia', 'au'), ('Japan', 'jp')): B.FL[nm] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', f + '.png'))
    def flipped(src_):
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, src_.get_width(), src_.get_height()); c = cairo.Context(s)
        c.translate(0, src_.get_height()); c.scale(1, -1); c.set_source_surface(src_, 0, 0); c.paint(); return s
    B.FL['PHW'] = flipped(B.FL['Philippines'])
    s = B.FL['Australia']; u = cairo.ImageSurface(cairo.FORMAT_ARGB32, s.get_width(), s.get_height()); c = cairo.Context(u)
    c.translate(s.get_width(), s.get_height()); c.rotate(math.pi); c.set_source_surface(s, 0, 0); c.paint(); B.FL['AUD'] = u
def war_now(t): return bt('flip')['l0'] + 0.25 <= t
def ph_name(t): return 'PHW' if war_now(t) else 'Philippines'
def war_set(cr, t):
    P.set_philippines(cr, t); a = 0.35 + 0.08 * math.sin(t * 6); cr.set_source_rgba(0.75, 0.05, 0.08, a); cr.paint()
    for j in range(14):
        ph = ((t * 0.9) + j / 14) % 1; x = (j * 157) % 1080; cr.new_path(); cr.arc(x, 1900 - ph * 1900, 6 + 8 * ph, 0, 2 * math.pi); cr.set_source_rgba(1, 0.6, 0.2, 0.6 * (1 - ph)); cr.fill()
def set_for(name, cr, t):
    if name in ('PHW',): war_set(cr, t)
    elif name in ('Philippines',): P.set_philippines(cr, t)
    elif name in ('Australia', 'AUD'): P.set_australia(cr, t)
    else: P.set_japan(cr, t)
def tag_name(n): return {'PHW': 'Philippines', 'AUD': 'Australia'}.get(n, n)
def close(cr, t, b, name, mood='happy', z0=1.0, z1=1.12, tilt=0.05, setn=None):
    h = P.hop_of(t, b); cr.save(); P.cam(cr, P.push(t, b['start'], b['end'], z0, z1), tilt, 540, 1100); set_for(setn or name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, 0); cr.restore()
    P.bubble(cr, t, b, 540, 540); P.nametag(cr, tag_name(name), 540, 1640, COL[name])
def flagcard(cr, img, x, y, wd, scale_y=1.0):
    iw, ih = img.get_width(), img.get_height(); s = wd / iw; hh = ih * s
    cr.save(); cr.translate(x, y); cr.scale(1, scale_y); cr.translate(-wd / 2, -hh / 2)
    rrect(cr, -8, -8, wd + 16, hh + 16, 12); cr.set_source_rgb(1, 1, 1); cr.fill()
    cr.save(); cr.scale(s, s); cr.set_source_surface(img, 0, 0); cr.paint(); cr.restore(); cr.restore(); return hh
def nbg(cr, t, tint=None): P.arena(cr, t, tint)

def frame_main(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); k = b['key']
    if k == 'h1':
        close(cr, t, b, 'Philippines', 'happy'); emoji(cr, '🍲', 860, 860, 150 * pop_k(t, b['l0'], 0.3), 1, rot=0.1 * math.sin(t * 3))
    elif k == 'h2':
        cr.save(); P.cam(cr, P.push(t, b['start'], b['end'], 1.1, 1.35), 0, 540, 1150); P.set_philippines(cr, t); ball(cr, 'Philippines', 540, 1230, 330, 'happy', 0, 0); cr.restore()
        cr.set_source_rgba(0, 0, 0.05, 0.45 * clamp((t - b['start']) * 3)); cr.paint()
        ts = w('h2', 'secret') - 0.1
        if t >= ts: slam(cr, 'A SECRET?', 540, 560, 140, GOLD, t, ts)
        C.draw_captions(cr, t, 1760)
    elif k == 'h3':
        close(cr, t, b, 'Philippines', 'shock', tilt=-0.06)
        on = int(t * 4) % 2; cr.set_source_rgba(1, 0, 0, 0.25 if on else 0.05); cr.paint(); emoji(cr, '🚨', 860, 820, 160 + 20 * on, 1)
    elif k == 'flip':
        t0 = b['start']; k1 = ease_io(prog(t, t0, b['l0'] + 0.25)); sx, sy = shake(t, b['l0'] + 0.25, 26, 0.6)
        cr.save(); cr.translate(sx, sy); war_set(cr, t) if k1 >= 1 else P.set_philippines(cr, t)
        cr.save(); cr.translate(540, 1150); cr.rotate(math.pi * k1); ball(cr, 'Philippines' if k1 < 1 else 'PHW', 0, 0, 340, 'angry', 0, 0) if k1 < 1 else None; cr.restore()
        if k1 >= 1: ball(cr, 'PHW', 540, 1150, 340, 'angry', 0, 0)
        cr.restore()
        if k1 >= 1:
            sx, sy = shake(t, b['l0'] + 0.25, 18); cr.save(); cr.translate(sx, sy); slam(cr, 'WAR MODE', 540, 520, 170, (1, 0.25, 0.25), t, b['l0'] + 0.25); cr.restore()
            chip(cr, 'RED ON TOP', 540, 680, 56, WHITE, INK, pop_k(t, b['l0'] + 0.5), 1)
        P.nametag(cr, 'Philippines', 540, 1640, RED if k1 >= 1 else PH_C); emoji(cr, '🔄', 860, 900, 130 * (1 - k1) + 1, 1, rot=t * 8)
    elif k in ('n1', 'n2', 'n3', 'n3b', 'n4'):
        nbg(cr, t, PH_C if k == 'n1' else RED)
        if k == 'n1':
            flagcard(cr, B.FL['Philippines'], 540, 1000, 760); label = 'PEACETIME'; ptext(cr, label, 540, 600, 120, PH_C, pop_k(t, b['start'] + 0.1), sw=14)
            ta = w('n1', 'blue') - 0.1
            if t >= ta: chip(cr, 'BLUE ON TOP', 540, 1340, 56, PH_C, INK, pop_k(t, ta), 1)
        elif k == 'n2':
            tf = w('n2', 'flipped') - 0.2; kf = ease_io(prog(t, tf, tf + 0.7)); sy_ = math.cos(math.pi * kf)
            img = B.FL['Philippines'] if sy_ >= 0 else B.FL['PHW']; flagcard(cr, img, 540, 1000, 760, abs(sy_) + 0.02)
            ptext(cr, 'WARTIME' if kf > 0.5 else 'PEACETIME', 540, 600, 120, RED if kf > 0.5 else PH_C, 1, sw=14)
            tr = w('n2', 'Red') - 0.1
            if t >= tr: chip(cr, 'RED ON TOP = WAR', 540, 1340, 56, RED, INK, pop_k(t, tr), 1)
        elif k == 'n3':
            hh = flagcard(cr, B.FL['Philippines'], 540, 1000, 760)
            tb = w('n3', 'Blue') - 0.1; trd = w('n3', 'Red') - 0.1
            if t >= tb: chip(cr, 'BLUE = PEACE & JUSTICE', 600, 1000 - hh / 4, 42, WHITE, INK, pop_k(t, tb), 1)
            if t >= trd: chip(cr, 'RED = PATRIOTISM & VALOUR', 600, 1000 + hh / 4, 42, WHITE, INK, pop_k(t, trd), 1)
            ptext(cr, 'THE COLOURS MEAN', 540, 600, 84, WHITE, 1, sw=12)
        elif k == 'n3b':
            hh = flagcard(cr, B.FL['Philippines'], 540, 1000, 760); ptext(cr, 'THE SYMBOLS', 540, 600, 96, GOLD, 1, sw=12)
            ts = w('n3b', 'three') - 0.1; tr = w('n3b', 'eight') - 0.1
            if t >= ts: chip(cr, '3 STARS: LUZON · VISAYAS · MINDANAO', 540, 1340, 40, WHITE, INK, pop_k(t, ts), 1)
            if t >= tr: chip(cr, '8 RAYS: THE FIRST 8 PROVINCES TO REVOLT', 540, 1440, 38, GOLD, INK, pop_k(t, tr), 1)
        else:
            k2 = pop_k(t, b['start'] + 0.15, 0.4); cr.save(); cr.translate(540, 1050); cr.scale(k2, k2)
            rrect(cr, -380, -330, 760, 660, 30); cr.set_source_rgb(0.97, 0.94, 0.85); cr.fill(); cr.set_source_rgb(0.55, 0.4, 0.25); cr.set_line_width(8); rrect(cr, -380, -330, 760, 660, 30); cr.stroke()
            ptext(cr, 'REPUBLIC ACT', 0, -200, 70, INK, 1, sw=0, shadow=False); ptext(cr, 'No. 8491', 0, -90, 110, RED, 1, sw=0, shadow=False)
            ptext(cr, 'FLAG AND HERALDIC CODE', 0, 30, 44, INK, 1, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, 'OF THE PHILIPPINES · 1998', 0, 90, 40, INK, 1, fam='Poppins ExtraBold', sw=0, shadow=False)
            for j in range(4): rrect(cr, -300, 150 + j * 36, 600 - (j % 2) * 120, 14, 7); cr.set_source_rgba(0.4, 0.35, 0.3, 0.5); cr.fill()
            cr.restore(); emoji(cr, '⚖️', 540, 560, 140, 1)
        C.draw_captions(cr, t, 1760)
    elif k == 'r1': close(cr, t, b, 'Australia', 'shock', tilt=0.06); ptext(cr, '?!', 860, 800, 170, GOLD, pop_k(t, b['l0']), sw=14)
    elif k == 'r2a':
        tsp = b['l1'] + 0.1; k1 = ease_io(prog(t, tsp, tsp + 0.8)); h = P.hop_of(t, b)
        cr.save(); P.cam(cr, 1.05, 0, 540, 1100); P.set_australia(cr, t); cr.save(); cr.translate(540, 1230 - h * 46); cr.rotate(math.pi * k1); ball(cr, 'Australia', 0, 0, 330, 'happy', 0.05 * h, 0); cr.restore(); cr.restore()
        P.bubble(cr, t, b, 540, 540); P.nametag(cr, 'Australia', 540, 1640, AU_C)
        if k1 > 0: emoji(cr, '🔄', 860, 900, 130, 1, rot=t * 8)
    elif k == 'r2b':
        cr.save(); P.cam(cr, 1.05, 0, 540, 1100); P.set_australia(cr, t); cr.save(); cr.translate(540, 1230); cr.rotate(math.pi); ball(cr, 'Australia', 0, 0, 330, 'shock', 0, 0); cr.restore(); cr.restore()
        P.bubble(cr, t, b, 540, 540); P.nametag(cr, 'Australia', 540, 1640, AU_C); emoji(cr, '😵‍💫'.replace('‍💫', ''), 860, 820, 1, 0)
        chip(cr, 'NOT HOW IT WORKS', 540, 820, 56, GOLD, INK, pop_k(t, b['l0'] + 0.6), 1) if t >= b['l0'] + 0.6 else None
    elif k == 'r3':
        k1 = ease_io(prog(t, b['l0'], b['l0'] + 0.9)); h = P.hop_of(t, b)
        cr.save(); P.cam(cr, 1.05, 0.04, 540, 1100); P.set_japan(cr, t); cr.save(); cr.translate(540, 1230 - h * 46); cr.rotate(math.pi * k1); ball(cr, 'Japan', 0, 0, 330, 'happy', 0.05 * h, 0); cr.restore(); cr.restore()
        P.bubble(cr, t, b, 540, 540); P.nametag(cr, 'Japan', 540, 1640, JP_C)
        if k1 >= 1: chip(cr, 'SAME FLAG ⬆️⬇️'.replace(' ⬆️⬇️', ''), 540, 820, 56, GOLD, INK, pop_k(t, b['l0'] + 0.9), 1)
    elif k == 'r4':
        close(cr, t, b, 'PHW', 'angry', 1.0, 1.18, 0.0); sx, sy = shake(t, b['l0'], 8, 0.3)
    elif k == 'r5': close(cr, t, b, 'Australia', 'shock', tilt=-0.05)
    elif k == 'r6':
        nbg(cr, t); tk = w('r6', 'karaoke') - 0.1
        for j in range(3): ptext(cr, '.', 400 + j * 140, 900, 200, WHITE, 1 if (t - b['start']) * 3 > j else 0.2, sw=0, shadow=False)
        if t >= tk:
            cr.set_source_rgba(1, 1, 1, 0.5 * (1 - prog(t, tk, tk + 0.2))); cr.paint()
            sx, sy = shake(t, tk, 20); cr.save(); cr.translate(sx, sy); slam(cr, 'KARAOKE!', 540, 760, 180, GOLD, t, tk); cr.restore()
            emoji(cr, '🎤', 540, 1150, 300 * pop_k(t, tk, 0.4), 1, rot=0.15 * math.sin(t * 6))
            for j in range(10): ph = ((t - tk) * 0.6 + j / 10) % 1; emoji(cr, '🎵' if j % 2 else '🎶', 120 + (j * 97) % 840, 1500 - 700 * ph, 70, 1 - ph)
        ptext(cr, 'THE CHALLENGE WAS…'.replace('…', '...'), 540, 520, 80, WHITE, 1, sw=10); C.draw_captions(cr, t, 1760)
    elif k == 'r7':
        close(cr, t, b, 'PHW', 'angry', 1.0, 1.2, -0.05); emoji(cr, '🎤', 860, 860, 170 * pop_k(t, b['l0'], 0.3), 1, rot=-0.2)
        ti = w('r7', 'IS') - 0.1
        if t >= ti: sx, sy = shake(t, ti, 16); cr.save(); cr.translate(sx, sy); slam(cr, 'THIS IS WAR', 540, 820, 110, (1, 0.3, 0.3), t, ti); cr.restore()
    else:
        nbg(cr, t, RED); ball(cr, 'PHW', 540, 900 - abs(math.sin(t * 5)) * 16, 210, 'angry', 0, 0); emoji(cr, '🎤', 760, 960, 140, 1, rot=-0.2)
        flagcard(cr, B.FL['Philippines'], 300, 1240, 280); flagcard(cr, B.FL['PHW'], 780, 1240, 280)
        ptext(cr, 'PEACE', 300, 1380, 44, PH_C, 1, sw=7); ptext(cr, 'WAR', 780, 1380, 44, RED, 1, sw=7)
        slam(cr, 'WHICH FLAG HAS', 540, 360, 90, WHITE, t, b['start']); slam(cr, 'A SECRET MEANING?', 540, 480, 90, GOLD, t, b['start'] + 0.3)
        tc = w('cta', 'Comment') - 0.1
        if t >= tc: chip(cr, 'COMMENT BELOW', 540, 1500, 50, WHITE, INK, pop_k(t, tc), 1)
        ts_ = w('cta', 'subscribe') - 0.1
        if t >= ts_: P.subscribe_button(cr, t, ts_, 540, 1680)
    f = 1 - prog(t, b['start'], b['start'] + 0.1)
    if f > 0 and k not in ('h1',): cr.set_source_rgba(1, 1, 1, 0.4 * f); cr.paint()
    if k not in ('h1', 'n3', 'n3b', 'n4'): streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.16)))
    ff = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if ff > 0: cr.set_source_rgba(0, 0, 0, ff); cr.paint()

def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); rng = np.random.default_rng(4); out = np.zeros(n)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    L = lambda d: np.arange(int(d * SR)) / SR
    music = np.zeros(n); beat = 60 / 112
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    wf0, wf1 = bt('flip')['l0'] + 0.25, bt('cta')['end']
    for bi in range(int(dur / beat) + 1):
        t0 = bi * beat; war = wf0 <= t0 < wf1; ch = ([50, 53, 57] if war else [60, 64, 67]) if (bi // 4) % 2 == 0 else ([48, 51, 55] if war else [57, 60, 64])
        if bi % 4 == 0: l = L(beat * 4.2); put(music, t0, sum(0.022 * np.sin(2 * np.pi * note(m) * l) for m in ch) * np.minimum(1, l / 0.1) * np.exp(-l * 0.6))
        l = L(0.22); put(music, t0, (0.3 if war else 0.18) * np.sin(2 * np.pi * np.cumsum(90 + 70 * np.exp(-l * 30)) / SR) * np.exp(-l * 14))
        if war and bi % 2: put(music, t0 + beat / 2, 0.15 * np.sin(2 * np.pi * np.cumsum(140 + 60 * np.exp(-l * 30)) / SR) * np.exp(-l * 16))
    fx = np.zeros(n)
    def boom(t0, a=0.7): l = L(1.4); put(fx, t0, a * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-l * 10)) / SR) * np.exp(-l * 2.8))
    def whoosh(t0, a=0.25, d=0.4): z = rng.standard_normal(int(d * SR)); put(fx, t0, a * np.convolve(z, np.ones(25) / 25, 'same') * np.linspace(0, 1, len(z)) ** 2)
    def pop(t0, a=0.1, f=900): l = L(0.06); put(fx, t0, a * np.sin(2 * np.pi * (f + 400 * np.exp(-l * 60)) * l) * np.exp(-l * 50))
    def bell(t0, a=0.12, f=1568): l = L(1.0); put(fx, t0, a * (np.sin(2 * np.pi * f * l) + 0.5 * np.sin(2 * np.pi * f * 2.76 * l)) * np.exp(-l * 4))
    def siren(t0, d): l = L(d); put(fx, t0, 0.12 * np.sign(np.sin(2 * np.pi * np.cumsum(700 + 250 * np.sin(2 * np.pi * 2 * l)) / SR)) * np.minimum(1, l / 0.05) * np.minimum(1, (d - l) / 0.1))
    for b in T['beats']: whoosh(b['start'] - 0.2, 0.15, 0.25)
    boom(0, 0.6); boom(w('h2', 'secret') - 0.1, 0.8); siren(bt('h3')['start'], bt('h3')['end'] - bt('h3')['start'])
    whoosh(bt('flip')['start'], 0.45, 0.6); boom(wf0, 1.1); boom(wf0 + 0.15, 0.8)
    tf = w('n2', 'flipped') - 0.2; whoosh(tf, 0.35, 0.6); boom(tf + 0.7, 0.7)
    for k_, wd in (('n3', 'Blue'), ('n3', 'Red'), ('n1', 'blue'), ('n2', 'Red')): pop(w(k_, wd) - 0.1, 0.12, 1000)
    pop(w('n3b', 'three') - 0.1, 0.12, 1100); pop(w('n3b', 'eight') - 0.1, 0.12, 1200)
    boom(bt('n4')['start'] + 0.15, 0.6); bell(bt('n4')['start'] + 0.3)
    whoosh(bt('r2a')['l1'] + 0.1, 0.35, 0.8); pop(bt('r2b')['l0'] + 0.6, 0.14, 300); whoosh(bt('r3')['l0'], 0.3, 0.9)
    tk = w('r6', 'karaoke') - 0.1
    for j in range(3): pop(bt('r6')['start'] + j / 3, 0.1, 500 + 100 * j)
    boom(tk, 1.0); bell(tk + 0.05, 0.14, 1319); boom(w('r7', 'IS') - 0.1, 1.0)
    tsc = w('cta', 'subscribe') - 0.1 + 1.3; pop(tsc, 0.18, 1800); bell(tsc + 0.05, 0.16, 1568); bell(tsc + 0.25, 0.12, 2093)
    v = np.zeros(n); tt = np.arange(n) / SR
    for s0, a in T['clips']: put(v, s0, a / max(1e-6, np.abs(a).max()) * 0.9)
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = np.tanh(music * 1.3) * 0.5 * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf: wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def main():
    data, out = sys.argv[1:3]; load_flags(data)
    C.TL = C.build(P.MultiVoice(os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_flip'))); P.render_frame = frame_main
    print(f"duration {C.TL['dur']:.1f}s")
    for b in C.TL['beats']: print(f"  {b['key']:6s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','): cr.identity_matrix(); frame_main(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
        return
    base = out.rsplit('.', 1)[0]; make_audio(C.TL, base + '.wav')
    nfr = int(C.TL['dur'] * FPS); wk = os.cpu_count() or 4; bd = np.linspace(0, nfr, wk * 3 + 1).astype(int)
    parts = [(int(a), int(b_), f'{base}.part{k:02d}.mp4') for k, (a, b_) in enumerate(zip(bd[:-1], bd[1:]))]
    with Pool(wk) as p: done = p.map(P.render_chunk, parts)
    open(base + '.parts.txt', 'w').write(''.join(f"file '{os.path.abspath(d)}'\n" for d in done))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)
if __name__ == '__main__':
    main()
