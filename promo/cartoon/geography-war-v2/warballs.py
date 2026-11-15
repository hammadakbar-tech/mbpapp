"""'Countryballs: North America vs Europe, the Geography War' (9:16). All 67 countries as flag balls: two armies, a roll call,
eight fact rounds (visuals from war.py) and a voiced countryball reaction after every round. Ten voices, live scoreboard.
Usage: python3 warballs.py <data_dir> <out.mp4> [--preview t1,...]
"""
import math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
import war as V
from war import NA, EU, NA_C, EU_C, ROUNDS, cam, push, hud, verdict, round_card, card_end, SHORT
from popu import streaks, shake
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

NARR = ('en-US-ChristopherNeural', '+7%')
Q = {  # reaction: speaker, side, voice, line
    'q1': ('Vatican', 'EU', 'en-GB-MaisieNeural', "I'm tiny... but I still count!"),
    'q2': ('Canada', 'NA', 'en-CA-LiamNeural', "Sorry, Europe. We're just... bigger, eh."),
    'q3': ('United Kingdom', 'EU', 'en-GB-RyanNeural', "Rather crowded over here. We like it that way."),
    'q4': ('United States of America', 'NA', 'en-US-GuyNeural', "Denali says hi!"),
    'q5': ('France', 'EU', 'fr-FR-HenriNeural', "Of course they visit us. Have you seen us?"),
    'q6': ('Mexico', 'NA', 'es-MX-JorgeNeural', "¡Vamos! We are level again!"),
    'q7': ('Italy', 'EU', 'it-IT-DiegoNeural', "We had universities before you had maps!"),
    'q8': ('United States of America', 'NA', 'en-US-GuyNeural', "Money talks, baby!"),
    'q9': ('Switzerland', 'EU', 'en-GB-ThomasNeural', "A draw? Perfect. I stay neutral."),
}
LINES = [
    ('h1', "Two continents. Sixty-seven countries. One war."),
    ('h2', "One has the size. The other has the numbers."),
    ('title', "North America versus Europe: the geography war."),
    ('r1', "Round one: countries. North America has twenty-three. Europe packs in forty-four. First blood: Europe."), ('q1', Q['q1'][3]),
    ('r2', "Round two: size. North America is almost twenty-five million square kilometres. Europe would fit inside nearly two and a half times. North America strikes back."), ('q2', Q['q2'][3]),
    ('r3', "Round three: people. Europe: seven hundred and forty-five million. North America: six hundred and seventeen million. Europe takes the lead."), ('q3', Q['q3'][3]),
    ('r4', "Round four: the highest peak. Europe's Mount Elbrus: five thousand six hundred and forty-two metres. North America's Denali: six thousand one hundred and ninety. All square."), ('q4', Q['q4'][3]),
    ('r5', "Round five: visitors. In 2024, Europe welcomed roughly four times as many tourists as North America. Europe, again."), ('q5', Q['q5'][3]),
    ('r6', "Round six: the longest river. The Volga: three thousand five hundred kilometres. The Mississippi and Missouri: over six thousand. Level again."), ('q6', Q['q6'][3]),
    ('r7', "Round seven: history. Europe's oldest university, Bologna, opened in 1088. North America's oldest came four hundred and fifty years later. Europe is one round from victory."), ('q7', Q['q7'][3]),
    ('r8', "Final round: the GDP war. Europe sends its six biggest economies: Germany, the UK, France, Italy, Russia and Spain. Together: about eighteen trillion dollars. Then the United States rolls in... alone. Twenty-nine trillion. North America wins the last round!"), ('q8', Q['q8'][3]),
    ('end', "Four rounds each. The war ends in a draw."), ('q9', Q['q9'][3]),
    ('cta', "North America, or Europe? Comment your side, and follow for the next battle.")]
C.BEATS = [(k, s, None, None, None, None, None) for k, s in LINES]; C.HOOK = ('h1', 'h2')
C.TAIL_OVERRIDE = {'h1': 0.25, 'h2': 0.3, 'title': 0.6, 'end': 0.4, 'cta': 2.4, **{f'r{i}': 0.4 for i in range(1, 9)}, **{k: 0.35 for k in Q}}
bt = C.bt
def w(key, word, n=0, end=False):
    if (key, word) == ('r7', 'Santo'): word = 'North'
    return C.w(key, word, n, end)
V.w = w
VOICE_OF = {C.say(k, s): (Q[k][2], '+3%') if k in Q else NARR for k, s in LINES}
class MultiVoice(C.WordVoice):
    def get(self, text):
        C.VOICE, C.RATE = VOICE_OF.get(text, NARR); return super().get(text)

CODES = dict(zip(NA + EU, 'ca us mx gt bz sv hn ni cr pa cu bs jm ht do kn ag dm lc vc bb gd tt is ie gb pt es ad fr mc be nl lu ch li de dk no se fi it sm va mt at cz pl sk hu si hr ba me rs al mk gr bg ro md ua by lt lv ee ru'.split()))
SIZE = {'United States of America': 1.45, 'Canada': 1.45, 'Mexico': 1.25, 'Russia': 1.4, 'Germany': 1.2, 'France': 1.2, 'United Kingdom': 1.2, 'Italy': 1.15, 'Spain': 1.15,
        'Ukraine': 1.1, 'Poland': 1.1, 'Cuba': 1.05, 'Vatican': 0.62, 'Monaco': 0.62, 'San Marino': 0.66, 'Liechtenstein': 0.66, 'Andorra': 0.68, 'Malta': 0.72, 'Luxembourg': 0.75}
FL, SLOT = {}, {}

def load_flags(d):
    for n, c in CODES.items(): FL[n] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', c + '.png'))
    for names, cols, x0, dx, y0, dy, sgn, base in ((NA, 4, 462, 108, 760, 116, -1, 50), (EU, 6, 618, 76, 730, 92, 1, 37)):
        slots = []
        for i in range(len(names)):
            row, col = i // cols, i % cols; slots.append((x0 + sgn * (col * dx + (row % 2) * dx * 0.4), y0 + row * dy))
        slots.sort(key=lambda p: (abs(p[0] - 540), -p[1]))  # the biggest countries stand at the front line
        for n, p in zip(sorted(names, key=lambda n: -SIZE.get(n, 0.9)), slots): SLOT[n] = (p[0], p[1], base * SIZE.get(n, 0.9))

# ---------- countryballs ----------
def eye(cr, x, y, rx, ry, mood, side, lw):
    if mood == 'happy':
        cr.new_path(); cr.arc(x, y + ry * 0.35, rx, math.pi * 1.12, math.pi * 1.88); cr.set_source_rgb(0, 0, 0); cr.set_line_width(lw * 1.6); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke(); return
    if mood == 'shock': rx, ry = rx * 1.15, ry * 1.3
    sl = {'angry': 0.5, 'sad': -0.35}.get(mood, 0.0) * -side; cut = y - ry * (0.2 if mood == 'angry' else 0.45)
    cr.save()
    if sl:
        cr.new_path(); cr.move_to(x - rx * 2, cut - sl * rx * 2); cr.line_to(x + rx * 2, cut + sl * rx * 2); cr.line_to(x + rx * 2, y + ry * 2); cr.line_to(x - rx * 2, y + ry * 2); cr.close_path(); cr.clip()
    cr.save(); cr.translate(x, y); cr.scale(rx, ry); cr.new_path(); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0, 0, 0); cr.set_line_width(lw); cr.stroke(); cr.restore()
    if sl:
        cr.new_path(); cr.move_to(x - rx * 1.15, cut - sl * rx * 1.15); cr.line_to(x + rx * 1.15, cut + sl * rx * 1.15); cr.set_source_rgb(0, 0, 0); cr.set_line_width(lw * 1.3); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()

def ball(cr, name, x, y, r, mood='neutral', squash=0.0, look=0.0):
    img = FL[name]; iw, ih = img.get_width(), img.get_height()
    cr.save(); cr.translate(x, y + r * squash); cr.scale(1 + squash * 0.5, 1 - squash)
    cr.save(); cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.clip()
    s = max(2 * r / iw, 2 * r / ih); cr.scale(s, s); cr.set_source_surface(img, -iw / 2, -ih / 2); cr.get_source().set_filter(cairo.FILTER_BILINEAR); cr.paint(); cr.restore()
    g = cairo.RadialGradient(-r * 0.35, -r * 0.4, r * 0.1, 0, 0, r * 1.02); g.add_color_stop_rgba(0, 1, 1, 1, 0.28); g.add_color_stop_rgba(0.55, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.35)
    cr.new_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source(g); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(max(2.5, r * 0.07)); cr.stroke()
    for side in (-1, 1): eye(cr, side * r * 0.34 + look * r * 0.12, -r * 0.14, r * 0.2, r * 0.26, mood, side, max(2, r * 0.05))
    cr.restore()

def arena(cr, t, tint=None):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.03, 0.1); g.add_color_stop_rgb(1, 0.1, 0.08, 0.2); cr.set_source(g); cr.paint()
    for col, x0 in ((NA_C, 0), (EU_C, W)):
        c = tint or col; g = cairo.RadialGradient(x0, 1100, 50, x0, 1100, 900); g.add_color_stop_rgba(0, *c, 0.4); g.add_color_stop_rgba(1, *c, 0); cr.set_source(g); cr.paint()
    rng = np.random.default_rng(3)
    for _ in range(90):
        x, y, s = rng.uniform(0, W), rng.uniform(0, 700), rng.uniform(0.8, 2.4); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25 + 0.25 * math.sin(t * 2 + x)); cr.fill()

def army(cr, t, names, mood='neutral', enter=1.0, drop=None, hop=8.0):
    """Draw a team in formation. enter slides it in from its side; drop = {name: time it lands} for the roll call."""
    sgn = -1 if names is NA else 1
    for i, n in sorted(enumerate(names), key=lambda p: SLOT[p[1]][1]):
        x, y, r = SLOT[n]; sq = 0.0
        if drop is not None:
            ts = drop[n]
            if t < ts: continue
            k = prog(t, ts, ts + 0.3); y = lerp(-150, y, ease_out(k)); sq = 0.18 * math.sin(math.pi * clamp((t - ts - 0.3) / 0.2)) if t > ts + 0.3 else 0.0
        x += sgn * (1 - enter) * 700
        ball(cr, n, x, y - abs(math.sin(t * 5 + i * 1.7)) * hop, r, mood, sq, -sgn * 0.6)

def speech(cr, t, b, x, y, col, name):
    """Speech bubble whose words appear as they are spoken."""
    toks = b['tokens']; n = sum(1 for s, e, _ in b['words'] if s <= t + 0.03); n = min(len(toks), max(1, round(n * len(toks) / max(1, len(b['words'])))))
    size = 58; lines, cur = [], []
    for tk in toks:
        if cur and tw(cr, ' '.join(cur + [tk]), size, 'Poppins ExtraBold') > 800: lines.append(cur); cur = []
        cur.append(tk)
    lines.append(cur)
    bw = max(tw(cr, ' '.join(l), size, 'Poppins ExtraBold') for l in lines) + 90; bh = len(lines) * 76 + 60
    k = pop_k(t, b['l0'] - 0.1, 0.25); cr.save(); cr.translate(540, y); cr.scale(k, k); cr.translate(-540, -y)
    cr.new_path(); cr.move_to(x - 30, y + bh / 2 - 6); cr.line_to(x, y + bh / 2 + 70); cr.line_to(x + 40, y + bh / 2 - 6); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(7); cr.stroke()
    rrect(cr, 540 - bw / 2, y - bh / 2, bw, bh, 44); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(7); cr.stroke()
    cr.rectangle(x - 22, y + bh / 2 - 12, 54, 12); cr.set_source_rgb(1, 1, 1); cr.fill()
    i = 0
    for li, l in enumerate(lines):
        lw_ = tw(cr, ' '.join(l), size, 'Poppins ExtraBold'); xx = 540 - lw_ / 2; yy = y - bh / 2 + 84 + li * 76
        for tk in l:
            ptext(cr, tk, xx, yy, size, INK if i < n else (0.8, 0.8, 0.85), 1, fam='Poppins ExtraBold', anchor='l', sw=0, shadow=False)
            xx += tw(cr, tk + ' ', size, 'Poppins ExtraBold'); i += 1
    cr.restore()
    nm = SHORT.get(name, name.upper()); wd = tw(cr, nm, 44)
    rrect(cr, 540 - wd / 2 - 34, 1560, wd + 68, 84, 42); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    ptext(cr, nm, 540, 1617, 44, INK, 1, sw=0, shadow=False)

def reaction(cr, t, key):
    b = bt(key); name, side, _, _ = Q[key]; neutral = key == 'q9'
    col = (0.85, 0.85, 0.9) if neutral else (NA_C if side == 'NA' else EU_C); sgn = -1 if side == 'NA' else 1; n = int(key[1])
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.12), 0.05 * (1 if n % 2 else -1), 540, 1050)
    arena(cr, t, col)
    cr.save(); cr.translate(540, 1420); cr.scale(1, 0.22); cr.new_path(); cr.arc(0, 0, 640, 0, 2 * math.pi); cr.restore(); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
    mates = [m for m in (NA if side == 'NA' else EU) if m != name]; rivals = EU if side == 'NA' else NA
    for i, m in enumerate(mates[:4] if not neutral else []):
        ball(cr, m, 540 + sgn * (300 + (i % 2) * 150) * (1 if i < 2 else -0.0) + (i - 1.5) * 20, 1000 + (i // 2) * 170 - abs(math.sin(t * 7 + i)) * 26, 86, 'happy')
    for i, m in enumerate(rivals[:3] if not neutral else (['United States of America', 'France', 'Canada', 'Germany'])):
        x = 540 - sgn * (330 - i * 70) if not neutral else 150 + i * 260
        ball(cr, m, x, 1390 + (i % 2) * 40, 72, 'angry' if not neutral else 'shock', 0, sgn if not neutral else 0)
    hop = 0.0
    for s, e, _ in b['words']:
        if s <= t < s + 0.26: hop = max(hop, math.sin(math.pi * (t - s) / 0.26))
    r = 150 if name == 'Vatican' else 250
    ball(cr, name, 540, 1130 + (250 - r) - hop * 46, r, 'happy' if not neutral else 'neutral', 0.05 * hop)
    cr.restore()
    speech(cr, t, b, 560, 560, col, name)
    f = 1 - prog(t, b['start'], b['start'] + 0.14)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.55 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.2)))

# ---------- round one: the roll call ----------
def r1(cr, t, b):
    te, tv = w('r1', 'Europe') - 0.15, w('r1', 'blood') - 0.35
    ta0, ta1 = w('r1', 'North') + 0.1, w('r1', 'twenty') + 0.7; tb0, tb1 = te + 0.15, w('r1', 'forty') + 0.9
    dn = {n: lerp(ta0, ta1, i / 22) for i, n in enumerate(sorted(NA, key=lambda n: -SLOT[n][1]))}
    de = {n: lerp(tb0, tb1, i / 43) for i, n in enumerate(sorted(EU, key=lambda n: -SLOT[n][1]))}
    cna = sum(t >= v + 0.2 for v in dn.values()); ceu = sum(t >= v + 0.2 for v in de.values())
    cr.save()
    if t < te: cam(cr, push(t, b['start'], te, 1.75, 1.9), -0.04, 300, 1080)
    elif t < tv: cam(cr, push(t, te, tv, 1.75, 1.9), 0.04, 800, 1080)
    else: cam(cr, push(t, tv, b['end'], 1.0, 1.06), 0.0, 540, 1000)
    arena(cr, t)
    army(cr, t, NA, 'angry' if t >= tv + 0.35 else 'neutral', drop=dn, hop=5); army(cr, t, EU, 'happy' if t >= tv + 0.35 else 'neutral', drop=de, hop=14 if t >= tv + 0.35 else 5)
    cr.restore()
    if te <= t < te + 0.25: streaks(cr, 1 - ease_out(prog(t, te, te + 0.22)))
    if t < te:
        if cna: ptext(cr, str(cna), 540, 520, 200, NA_C, 1, sw=18); nm = max(dn, key=lambda n: dn[n] if t >= dn[n] + 0.2 else -1); ptext(cr, SHORT.get(nm, nm.upper()), 540, 610, 46, WHITE, 1, fam='Poppins ExtraBold', sw=7)
    elif t < tv:
        if ceu: ptext(cr, str(ceu), 540, 520, 200, EU_C, 1, sw=18); nm = max(de, key=lambda n: de[n] if t >= de[n] + 0.2 else -1); ptext(cr, SHORT.get(nm, nm.upper()), 540, 610, 46, WHITE, 1, fam='Poppins ExtraBold', sw=7)
    else:
        ptext(cr, '23', 270, 560, 190, NA_C, 1, sw=18); ptext(cr, '44', 810, 560, 190, EU_C, 1, sw=18)
ROUNDS['r8'] = ('THE GDP WAR', 'NA', 'Europe', 'wins')
GDP6 = [('Germany', 4.7, 230, 610, 'Germany'), ('United Kingdom', 3.6, 540, 600, 'UK'), ('France', 3.2, 830, 610, 'France'),
        ('Italy', 2.4, 300, 870, 'Italy'), ('Russia', 2.2, 560, 870, 'Russia'), ('Spain', 1.7, 800, 870, 'Spain')]
def r8(cr, t, b):
    """The GDP war: every ball's area matches its economy."""
    tu = w('r8', 'United') - 0.5; k = ease_out(prog(t, tu, tu + 0.8)); sx, sy = shake(t, tu + 0.8, 26, 0.6); kr = 50
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.06), 0.03 - 0.06 * k, 540 + sx, 960 + sy); arena(cr, t)
    tot = 0.0
    for n, g, x, y, word in GDP6:
        ts = w('r8', word) - 0.15
        if t < ts: continue
        tot += g; r = kr * math.sqrt(g) * pop_k(t, ts, 0.3)
        ball(cr, n, x, y - abs(math.sin(t * 5 + x)) * 6, r, 'shock' if t >= tu + 0.5 else 'angry', 0, -0.7 if t >= tu else 0)
        ptext(cr, f'${g}T', x, y + kr * math.sqrt(g) + 46, 40, WHITE, 1, sw=6)
    if t >= tu:
        R = kr * math.sqrt(29.2); x = lerp(-R - 100, 540, k)
        cr.save(); cr.translate(x, 1385); cr.rotate((1 - k) * -4.0); ball(cr, 'United States of America', 0, 0, R, 'happy' if k >= 1 else 'angry', 0.06 * math.sin(math.pi * clamp((t - tu - 0.8) / 0.25)) if t > tu + 0.8 else 0); cr.restore()
        if k >= 1:
            for n, g, bx in (('Canada', 2.2, 110), ('Mexico', 1.9, 980)): ball(cr, n, bx, 1560 - abs(math.sin(t * 7 + bx)) * 20, kr * math.sqrt(g) * pop_k(t, tu + 0.9, 0.3), 'happy')
    cr.restore()
    if tot: chip(cr, f"EUROPE'S TOP 6: ${ease_out(prog(t, w('r8', 'Together') - 0.6, w('r8', 'eighteen') + 0.3)) * 17.8:.1f}T" if t >= w('r8', 'Together') - 0.6 else "EUROPE'S TOP 6", 540, 400, 48, EU_C, INK, pop_k(t, w('r8', 'six') - 0.2), 1)
    tn = w('r8', 'Twenty')
    if t >= tn: slam(cr, 'USA ALONE: $29T', 540, 1085, 88, NA_C, t, tn)
    ptext(cr, 'BALL SIZE = SIZE OF ECONOMY (GDP)', 540, 470, 28, WHITE, 0.85, fam='Poppins ExtraBold', sw=5)
ROUND_FN = dict(V.ROUND_FN, r1=r1, r8=r8)

# ---------- hook, title, ending ----------
def draw_hook(cr, t):
    if t >= bt('title')['start']: return False
    if t < bt('h2')['start']:
        b = bt('h1'); tw_ = w('h1', 'One'); sx, sy = shake(t, tw_, 22)
        cr.save(); cam(cr, push(t, 0, b['end'], 1.0, 1.1), -0.03, 540 + sx, 1000 + sy); arena(cr, t)
        e = ease_out(prog(t, 0.0, 0.7)); mood = 'angry' if t >= tw_ else 'neutral'
        army(cr, t, NA, mood, e, hop=10); army(cr, t, EU, mood, e, hop=10); cr.restore()
        slam(cr, '2 CONTINENTS', 540, 380, 124, WHITE, t, 0.03)
        t0, t1 = w('h1', 'Sixty') - 0.1, w('h1', 'countries', end=True)
        if t >= t0: ptext(cr, f'{int(67 * ease_out(prog(t, t0, t1)))} COUNTRYBALLS', 540, 510, 84, GOLD, 1, sw=11)
        if t >= tw_: slam(cr, '1 WAR', 540, 1730, 190, CRIMSON, t, tw_)
    else:
        b = bt('h2'); ts = w('h2', 'other') - 0.3
        if t < ts:
            cr.save(); cam(cr, push(t, b['start'], ts, 1.0, 1.14), 0.06, 540, 1050); arena(cr, t, NA_C)
            for n, x, y, r in (('Canada', 320, 820, 250), ('Mexico', 300, 1390, 210), ('United States of America', 720, 1090, 310)):
                ball(cr, n, x, y - abs(math.sin(t * 4 + x)) * 14, r * pop_k(t, b['start'], 0.3), 'angry', 0, 0.5)
            cr.restore(); slam(cr, 'ONE HAS THE SIZE', 540, 420, 104, NA_C, t, b['start'] + 0.05)
        else:
            cr.save(); cam(cr, push(t, ts, b['end'], 1.9, 2.15), -0.05, 800, 1070); arena(cr, t, EU_C); army(cr, t, EU, 'angry', 1.0, hop=16); cr.restore()
            slam(cr, 'ONE HAS THE NUMBERS', 540, 420, 90, EU_C, t, ts)
        for tt in (b['start'], ts):
            f = 1 - prog(t, tt, tt + 0.14)
            if t >= tt and f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint(); streaks(cr, f)
    return True

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end']): return False
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.03, 540, 1000); arena(cr, t); army(cr, t, NA, 'angry', hop=10); army(cr, t, EU, 'angry', hop=10); cr.restore()
    cr.set_source_rgba(0, 0, 0.03, 0.5); cr.paint()
    slam(cr, 'NORTH AMERICA', 540, 560, 112, NA_C, t, w('title', 'North'))
    tv = w('title', 'versus')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 760); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 110, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 42, 120, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'EUROPE', 540, 1000, 190, EU_C, t, w('title', 'Europe'))
    tg = w('title', 'geography')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE GEOGRAPHY WAR', 540, 1240, 92, WHITE, t, tg); cr.restore()
    if t >= tg + 0.3: chip(cr, 'VERSION 2 · COUNTRYBALLS', 540, 1400, 44, GOLD, INK, pop_k(t, tg + 0.3), 1)
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22)))
    return True

def draw_end(cr, t):
    b, c = bt('end'), bt('cta')
    cr.save(); cam(cr, push(t, b['start'], c['end'], 1.0, 1.1), 0.02 * math.sin(t), 540, 1000); arena(cr, t); army(cr, t, NA, 'neutral', hop=10); army(cr, t, EU, 'neutral', hop=10); cr.restore()
    cr.set_source_rgba(0, 0, 0.03, 0.5); cr.paint()
    if t < c['start']:
        ptext(cr, '4', 300, 900, 380, NA_C, 1, sw=26); ptext(cr, '4', 780, 900, 380, EU_C, 1, sw=26); ptext(cr, '—', 540, 850, 160, WHITE, 1, sw=14)
        td = w('end', 'draw')
        if t >= td: sx, sy = shake(t, td, 18); cr.save(); cr.translate(sx, sy); slam(cr, 'A DRAW', 540, 1250, 190, GOLD, t, td); cr.restore()
    else:
        for x, col, word, lab, rot in ((280, NA_C, 'North', ['NORTH', 'AMERICA'], -0.04), (800, EU_C, 'Europe', ['EUROPE'], 0.04)):
            tt = w('cta', word)
            if t < tt: continue
            k = pop_k(t, tt) * (1 + 0.03 * math.sin(t * 6 + x)); cr.save(); cr.translate(x, 820); cr.rotate(rot); cr.scale(k, k)
            for i, l in enumerate(lab): ptext(cr, l, 0, i * 100 - (50 if len(lab) > 1 else 0), 96 if len(lab) > 1 else 112, col, 1, sw=12)
            cr.restore()
        tc = w('cta', 'Comment')
        if t >= tc: k = pop_k(t, tc); cr.save(); cr.translate(540, 500); cr.scale(k, k); ptext(cr, 'COMMENT YOUR SIDE', 0, 0, 82, WHITE, 1, sw=11); cr.restore(); emoji(cr, '👇', 540, 1060, 110 * k, 1)
        tf = w('cta', 'follow')
        if t >= tf:
            k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1300); cr.scale(k, k); txt = 'FOLLOW FOR THE NEXT BATTLE'; wd = tw(cr, txt, 46)
            rrect(cr, -wd / 2 - 50, -62, wd + 100, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill(); ptext(cr, txt, 0, 4, 46, WHITE, 1, sw=0, shadow=False); cr.restore()

def render_frame(cr, t):
    if draw_hook(cr, t): C.draw_captions(cr, t, 1490 if t < bt('h2')['start'] else 1640); return
    if draw_title(cr, t): return
    qk = next((k for k in Q if bt(k)['start'] <= t < bt(k)['end']), None)
    if qk: reaction(cr, t, qk); hud(cr, t)
    elif t >= bt('end')['start']:
        draw_end(cr, t); hud(cr, t)
        if t < w('cta', 'Comment'): C.draw_captions(cr, t, 1600)
    else:
        key = next((k for k in ROUNDS if bt(k)['start'] <= t < bt(k)['end']), 'r8'); b = bt(key)
        if not round_card(cr, t, key):
            cr.save(); ROUND_FN[key](cr, t, b); cr.restore()
            te = card_end(key); f = 1 - prog(t, te, te + 0.14)
            if f > 0: cr.set_source_rgba(1, 1, 1, 0.55 * f); cr.paint()
            g = cairo.LinearGradient(0, 1420, 0, H); g.add_color_stop_rgba(0, 0, 0, 0.03, 0); g.add_color_stop_rgba(0.5, 0, 0, 0.03, 0.8); g.add_color_stop_rgba(1, 0, 0, 0.03, 0.92)
            cr.rectangle(0, 1420, W, 500); cr.set_source(g); cr.fill()
            verdict(cr, t, key)
        hud(cr, t); C.draw_captions(cr, t, 1640)
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR; rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 128; bar = beat * 4
    chords = [[50, 53, 57], [46, 50, 53], [41, 45, 48], [48, 52, 55]]
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar * 1.15 * SR)) / SR; env = np.minimum(1, Lc / 0.15) * np.exp(-Lc * 0.7)
        put(music, ci * bar, sum(0.03 * (np.sin(2 * np.pi * note(m) * Lc) + 0.15 * np.sign(np.sin(2 * np.pi * note(m + 12) * Lc))) for m in ch) * env)
        put(music, ci * bar, 0.1 * np.sin(2 * np.pi * note(ch[0] - 24) * Lc) * env)
        for j in range(8):
            m = ch[j % 3] + 12 + (12 if j % 4 == 3 else 0); P = np.arange(int(0.18 * SR)) / SR
            put(music, ci * bar + j * beat / 2, 0.022 * np.sign(np.sin(2 * np.pi * note(m) * P)) * np.exp(-P * 20))
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 > bt('cta')['start'] + 3: break
        Ld = np.arange(int(0.35 * SR)) / SR; put(music, t0, 0.4 * np.sin(2 * np.pi * np.cumsum(55 + 70 * np.exp(-Ld * 22)) / SR) * np.exp(-Ld * 9))
        M = np.arange(int(0.12 * SR))
        if bi % 2 == 1: put(music, t0, 0.09 * rng.standard_normal(len(M)) * np.exp(-M / SR * 28))
        for q in (0.5, 0.75): put(music, t0 + beat * q, 0.035 * rng.standard_normal(int(0.04 * SR)) * np.exp(-np.arange(int(0.04 * SR)) / SR * 70))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.6):
        Lb = np.arange(int(1.6 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-Lb * 10)) / SR) * np.exp(-Lb * 2.8))
    def whoosh(t0, amp=0.28, d=0.45):
        nz = rng.standard_normal(int(d * SR)); env = np.linspace(0, 1, len(nz)) ** 2; put(fx, t0, amp * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def bell(t0, amp=0.12, f=1175):
        Ld = np.arange(int(1.2 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * f * Ld) + 0.5 * np.sin(2 * np.pi * f * 2.76 * Ld)) * np.exp(-Ld * 4))
    def horn(t0, amp=0.07):
        Lh = np.arange(int(0.9 * SR)) / SR; put(fx, t0, amp * sum(np.sign(np.sin(2 * np.pi * f * Lh)) for f in (146.8, 220, 293.7)) * np.minimum(1, Lh / 0.05) * np.exp(-Lh * 2.5) / 3)
    def pop(t0, amp=0.05, f=1100):
        Lp = np.arange(int(0.05 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * (f + 400 * np.exp(-Lp * 60)) * Lp) * np.exp(-Lp * 60))
    def cheer(t0, amp=0.1, d=1.4):
        z = np.convolve(rng.standard_normal(int(d * SR)), np.ones(8) / 8, 'same'); L_ = np.linspace(0, 1, len(z)); put(fx, t0, amp * z * np.sin(np.pi * L_) ** 0.6 * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * L_ * d)))
    boom(0.03, 0.8); whoosh(0.0, 0.3, 0.7); boom(w('h1', 'One'), 0.9); horn(w('h1', 'One'))
    for tx in (bt('h2')['start'], w('h2', 'other') - 0.3): whoosh(tx - 0.4); boom(tx, 0.6)
    whoosh(bt('title')['start'] - 0.4)
    for wd in ('North', 'Europe', 'geography'): boom(w('title', wd), 0.7)
    horn(w('title', 'geography'), 0.09)
    for k, (ttl, win, _, vw) in ROUNDS.items():
        b = bt(k); whoosh(b['start'] - 0.4); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03, 0.1); whoosh(card_end(k) - 0.3, 0.25, 0.3)
        tv = w(k, vw); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if win == 'NA' else 1319); cheer(tv + 0.1)
    for k in Q: whoosh(bt(k)['start'] - 0.3, 0.22, 0.3); pop(bt(k)['l0'] - 0.1, 0.12, 700)
    t0, t1 = w('r1', 'North') + 0.1, w('r1', 'twenty') + 0.7
    for i in range(23): pop(lerp(t0, t1, i / 22) + 0.3)
    t0, t1 = w('r1', 'Europe'), w('r1', 'forty') + 0.9
    for i in range(44): pop(lerp(t0, t1, i / 43) + 0.3, 0.04, 1400)
    boom(w('end', 'draw'), 1.0); horn(w('end', 'draw'), 0.1)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a / max(1e-6, np.abs(a).max()) * 0.9)  # level every voice
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    C.TL = C.build(MultiVoice(cache)); V.G = V.Geo(data_dir); load_flags(data_dir)

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        cr.identity_matrix(); cr.reset_clip(); render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    data_dir, out = sys.argv[1:3]
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_warballs'))
    print(f"duration {C.TL['dur']:.1f}s")
    for b in C.TL['beats']: print(f"  {b['key']:6s} {b['start']:6.2f}-{b['end']:6.2f}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','): cr.identity_matrix(); cr.reset_clip(); render_frame(cr, float(ts)); surf.write_to_png(f'{out}_{ts}.png')
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
