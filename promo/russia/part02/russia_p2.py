"""The Entire History of Russia - Part 02: Terror and Troubles (1533-1613). 9:16 map documentary.
Cold-open hook, British narrator, and every caption, year, name and animation fired on the narrator's spoken word
(edge-tts word boundaries). Reuses the map and drawing helpers from russia.py and the voice from russia2.py.
Usage: python3 russia_p2.py <data_dir> <out.mp4> [--preview t1,t2,...]
"""
import math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import russia as R
from russia import (GOLD, CRIMSON, WHITE, AMBER, ICE, PARCH, INK, RIVER, W, H, FPS, MAPY, L, S, poly, route, at, win,
                    ptext, rrect, tw, fit, face, emoji, pop_k, path_xy)
from russia2 import WordVoice, norm
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

BLOOD, BLACK, ROMANOV = hexc('#8E0E1C'), (0.02, 0.02, 0.03, 1), hexc('#F5C542')
P = {
    'moscow': (37.62, 55.75), 'kazan': (49.12, 55.79), 'astrakhan': (48.03, 46.35), 'novgorod': (31.27, 58.52),
    'alexandrov': (38.70, 56.40), 'riga': (24.11, 56.95), 'reval': (24.75, 59.44), 'polotsk': (28.78, 55.49),
    'narva': (28.19, 59.38), 'uglich': (38.33, 57.53), 'qashliq': (68.25, 58.20), 'solikamsk': (56.77, 59.65),
    'warsaw': (21.01, 52.23), 'krakow': (19.94, 50.06), 'smolensk': (32.05, 54.78), 'nizhny': (44.00, 56.33),
    'tver': (35.90, 56.86), 'pskov': (28.33, 57.82), 'tyumen': (65.53, 57.15),
}
RUS_1533 = [(31, 56), (28, 57.6), (27.8, 59.5), (30, 61), (33, 63), (38, 66), (45, 66.8), (52, 66), (58, 64), (57, 60),
            (52, 57.5), (47, 56), (44, 54.5), (41, 53), (37, 52.5), (34, 53.5), (32, 54.5)]
KAZAN_KH = [(46, 54), (46, 57), (50, 58.2), (54, 57.5), (55, 55), (53, 53.5), (49, 53.5)]
ASTRA_KH = [(44, 46), (45, 48.5), (48, 49.5), (50.5, 48), (49, 45.5), (47, 44.5)]
VOLGA_LINK = [(46, 54), (49, 53.5), (50.5, 48), (48, 49.5), (45, 48.5), (44.5, 50), (45, 52.5)]
LIVONIA = [(21.5, 57), (22, 59.2), (24, 59.6), (28, 59.4), (28.2, 57.8), (27.5, 56), (24, 56), (21, 56.4)]
OPRICH = [(36, 56.5), (36.5, 59.5), (39, 61), (43, 61.5), (45, 59.5), (43, 57), (39.5, 56.2)]
SIBIR = [(60, 56), (60, 60.5), (66, 61.5), (73, 59.5), (73, 55), (66, 54.5)]
URALS = [(59.5, 51), (59.3, 54), (59.0, 57), (59.3, 60), (60.0, 63), (61, 66), (64, 68)]
YERMAK = [(57.8, 58.3), (59.2, 58.5), (61.5, 58.0), (63.5, 57.5), P['tyumen'], (67, 57.8), P['qashliq']]
POLAND = [(14.5, 54.5), (21, 55), (24.5, 56.5), (28, 56), (31, 55.5), (32.5, 54), (31, 51.5), (27, 50), (24, 49), (19, 49.4), (15, 50.8)]

TODAY_CAM = (37.6, 56.5, 0.5)
# key, narration, year, word that flips the year, camera (lon, lat, px/km), chapter, card (emoji, name, subtitle, word)
BEATS = [
    ('h1', "He unleashed riders dressed in black...", None, None, TODAY_CAM, None, None),
    ('h2', "slaughtered an entire city...", None, None, TODAY_CAM, None, None),
    ('h3', "and killed his own son.", None, None, TODAY_CAM, None, None),
    ('intro', "This is Ivan the Terrible... and what came after him was even worse.", None, None, TODAY_CAM, None, None),
    ('title', "", None, None, (40, 56, 0.3), None, None),
    ('child', "In 1533, Ivan became ruler of Moscow at just three years old, and grew up amid the violent feuds of the boyars.",
     1533, '1533', (37.6, 55.6, 0.45), ('I', 'THE BOY TSAR'), ('👦', 'IVAN IV', 'Ruler of Moscow from age 3 · 1533', 'Ivan')),
    ('crowned', "In 1547, at sixteen, he was crowned the first Tsar of All Russia, from the Roman title, Caesar.",
     1547, '1547', (37.6, 55.75, 1.1), None, None),
    ('anastasia', "That same year, he married Anastasia Romanovna. Remember that name.", 1547, None, (37.6, 55.75, 1.0), None,
     ('💍', 'ANASTASIA ROMANOVNA', 'Tsaritsa · wife of Ivan IV · d. 1560', 'Anastasia')),
    ('kazan', "In 1552, he stormed Kazan, a Tatar stronghold on the Volga, and built Saint Basil's Cathedral to celebrate.",
     1552, '1552', (43.5, 55.5, 0.42), ('II', 'THE CONQUEROR'), None),
    ('astrakhan', "Astrakhan fell four years later, and Russia controlled the whole Volga.", 1556, 'later', (45, 51.5, 0.22), None, None),
    ('livonia', "But his war in the west, the Livonian War, dragged on for twenty-five years... and ended in defeat.",
     1558, 'Livonian', (27.5, 57.5, 0.42), None, None),
    ('loss', "In 1560, Anastasia died. Ivan was convinced she had been poisoned... and something in him broke.",
     1560, '1560', (37.6, 55.75, 0.9), ('III', 'THE TERROR'), None),
    ('oprichnina', "In 1565, he created the Oprichnina, a terror police of riders in black, with dogs' heads and brooms on their saddles: to sniff out treason, and sweep it away.",
     1565, '1565', (38.5, 57.8, 0.42), None, None),
    ('novgorod', "In 1570, suspecting betrayal, they fell on Novgorod. Thousands were slaughtered.", 1570, '1570', (34, 57.6, 0.55), None, None),
    ('son', "In 1581, in a fit of rage, Ivan struck his own son and heir. Days later, the young man was dead.", 1581, '1581',
     (37.6, 55.75, 0.9), None, ('👑', 'IVAN IVANOVICH', 'Heir to the throne · 1554–1581', 'heir')),
    ('siberia', "Meanwhile, Cossacks led by Yermak crossed the Urals and began the conquest of Siberia.", 1582, 'Yermak',
     (58, 57.5, 0.19), None, ('🏹', 'YERMAK', 'Cossack leader · d. 1585', 'Yermak')),
    ('death', "Ivan died in 1584. In Russian, he's Ivan Grozny: the Formidable. In English... the Terrible.", 1584, '1584',
     (37.6, 55.75, 0.8), None, None),
    ('fyodor', "His son Fyodor was gentle and weak. The real power was his adviser, Boris Godunov.", 1584, None,
     (37.6, 55.75, 0.8), ('IV', 'THE TIME OF TROUBLES'), ('🕊️', 'FYODOR I', 'Tsar · r. 1584–1598', 'Fyodor')),
    ('dmitry', "In 1591, Ivan's youngest son, Dmitry, was found with his throat cut. Many blamed Boris.", 1591, '1591',
     (38.1, 56.7, 0.9), None, None),
    ('end', "In 1598, Fyodor died childless, and the Rurik dynasty, over seven centuries old, came to an end.", 1598, '1598',
     (37.6, 56, 0.5), None, None),
    ('boris', "Boris became Tsar. Then a volcano in Peru froze Russia's summers, and famine killed perhaps two million people.",
     1601, 'famine', (37.6, 56, 0.32), None, ('🦊', 'BORIS GODUNOV', 'Tsar · r. 1598–1605', 'Boris')),
    ('false', "In 1605, a man claiming to be the dead Dmitry seized the throne with Polish help. Within a year, he was murdered.",
     1605, '1605', (29.5, 54, 0.3), None, ('🎭', 'FALSE DMITRY I', 'Impostor tsar · r. 1605–1606', 'claiming')),
    ('poles', "By 1610, a Polish army was sitting in the Kremlin.", 1610, '1610', (33, 54.5, 0.35), None, None),
    ('minin', "Then a butcher, Kuzma Minin, and a prince, Dmitry Pozharsky, raised a people's army, and in 1612 they drove the Poles out.",
     1612, '1612', (40.5, 56, 0.55), None, ('🛡️', 'MININ & POZHARSKY', 'Leaders of the people’s army · 1612', 'Kuzma')),
    ('romanov', "In 1613, an assembly chose sixteen-year-old Michael Romanov, Anastasia's great-nephew, as tsar. His family would rule for three hundred years.",
     1613, '1613', (37.6, 55.75, 0.7), None, ('👑', 'MICHAEL ROMANOV', 'Tsar · r. 1613–1645', 'Michael')),
    ('cliff', "And his grandson would drag Russia into the modern world... by force.", 1613, None, (37.6, 55.75, 0.6), None, None),
    ('next', "Peter the Great. That's Part Three. Follow, so you don't miss it.", 1682, 'Peter', (37.6, 55.75, 0.75), None, None),
]
HOOK = ('h1', 'h2', 'h3')
TL = None
G = None
ANCHOR = {}
_missing = set()

# ---------- timeline ----------
def build(voice):
    t, beats, clips = 0.0, [], []
    lead = {'h1': 0.05, 'h2': 0.05, 'h3': 0.05, 'intro': 0.25}
    tail = {'h1': 0.1, 'h2': 0.1, 'h3': 0.35, 'intro': 0.5, 'next': 2.2, 'end': 0.7, 'son': 0.8, 'death': 0.7}
    for key, text, year, yword, cam, chap, card in BEATS:
        b = dict(key=key, text=text, year=year, yword=yword, cam=cam, chap=chap, card=card[:3] if card else None,
                 cword=card[3] if card else None, start=t)
        if text:
            a, words = voice.get(text)
            b['l0'] = t + (1.55 if chap else lead.get(key, 0.35)); b['l1'] = b['l0'] + len(a) / SR
            b['words'] = [(b['l0'] + s, b['l0'] + e, x) for s, e, x in words]
            clips.append((b['l0'], a))
        else:  # silent title card
            b['l0'] = b['l1'] = t + 0.1; b['words'] = []
        b['tokens'] = text.split()
        t = (b['l1'] + tail.get(key, 0.45)) if text else t + 2.3
        b['end'] = t; beats.append(b)
    return dict(beats=beats, by={b['key']: b for b in beats}, clips=clips, dur=t)

def bt(key): return TL['by'][key]

def w(key, word, n=0, end=False):
    q, hits = norm(word), []
    for s, e, x in bt(key)['words']:
        if any(norm(part).startswith(q) for part in x.split()): hits.append((s, e))
    if len(hits) > n: return hits[n][1] if end else hits[n][0]
    if (key, word) not in _missing: _missing.add((key, word)); print(f'  ! no word "{word}" in {key}', file=sys.stderr)
    return bt(key)['l0']

def year_events():
    ev = []
    for b in TL['beats']:
        if isinstance(b['year'], int): ev.append((w(b['key'], b['yword']) if b['yword'] else b['l0'], b['year']))
    return sorted(ev, key=lambda e: e[0])

def year_at(t):
    if t < bt('child')['start']: return None
    val, prev = None, None
    for te, v in TL['yev']:
        if t < te - 0.1: break
        val = lerp(prev, v, ease_out(prog(t, te - 0.1, te + 0.7))) if isinstance(prev, int) and prev != v else v
        prev = v
    return val

def draw_year(cr, t):
    v = year_at(t)
    if v is None: return
    a = ease_out(prog(t, bt('child')['l0'] - 0.2, bt('child')['l0'] + 0.2))
    txt = str(int(round(v)))
    ptext(cr, txt, 540, 300, 170, GOLD, a, sw=16)
    ptext(cr, 'AD', 540 + tw(cr, txt, 170) / 2 + 52, 300, 46, PARCH, a, fam='Poppins ExtraBold', sw=6)

# ---------- small drawing pieces ----------
def knight(cr, x, y, size, a=1.0, col=BLOOD):
    cr.save(); cr.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); cr.set_font_size(size)
    wd = cr.text_extents('♞').x_advance
    cr.new_path(); cr.move_to(x - wd / 2, y + size * 0.35); cr.text_path('♞')
    cr.set_source_rgba(0, 0, 0, a); cr.fill_preserve(); cr.set_source_rgba(*col[:3], a); cr.set_line_width(max(2, size * 0.05)); cr.stroke()
    cr.restore()

def onion_church(cr, x, y, s, a=1.0):
    """Stylised St Basil's: a base and five striped onion domes."""
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    rrect(cr, -110, -40, 220, 90, 8); cr.set_source_rgba(0.75, 0.22, 0.18, a); cr.fill()
    for dx, h, col, r in ((-80, 70, (0.16, 0.55, 0.32), 26), (80, 70, (0.2, 0.4, 0.8), 26), (-40, 105, (0.95, 0.75, 0.2), 30),
                          (40, 105, (0.85, 0.2, 0.25), 30), (0, 150, (0.2, 0.6, 0.45), 34)):
        rrect(cr, dx - r * 0.55, -40 - h + r, r * 1.1, h - r, 4); cr.set_source_rgba(0.82, 0.3, 0.22, a); cr.fill()
        cy = -40 - h
        cr.new_path(); cr.move_to(dx, cy - r * 1.6)
        cr.curve_to(dx + r * 0.2, cy - r * 0.9, dx + r * 1.2, cy - r * 0.6, dx + r * 0.9, cy + r * 0.2)
        cr.line_to(dx - r * 0.9, cy + r * 0.2)
        cr.curve_to(dx - r * 1.2, cy - r * 0.6, dx - r * 0.2, cy - r * 0.9, dx, cy - r * 1.6); cr.close_path()
        cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, 0.6 * a); cr.set_line_width(3); cr.stroke()
        cr.new_path(); cr.move_to(dx, cy - r * 1.6); cr.line_to(dx, cy - r * 2.3); cr.move_to(dx - 8, cy - r * 2.05); cr.line_to(dx + 8, cy - r * 2.05)
        cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
    cr.restore()

def cyr_text(cr, txt, x, y, size, col, a=1.0):
    cr.save(); cr.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); cr.set_font_size(size)
    wd = cr.text_extents(txt).x_advance; cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.new_path(); cr.move_to(x - wd / 2, y); cr.text_path(txt)
    cr.set_source_rgba(*INK, a); cr.set_line_width(size * 0.16); cr.stroke_preserve(); cr.set_source_rgba(*col[:3], a); cr.fill()
    cr.restore()

def chip(cr, txt, x, y, size, bg, fg, t, t0, a=1.0, rot=0.0):
    if t < t0 or a <= 0: return
    k = pop_k(t, t0); cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(k, k)
    wd = tw(cr, txt, size); rrect(cr, -wd / 2 - size * 0.55, -size * 1.0, wd + size * 1.1, size * 1.45, size * 0.72)
    cr.set_source_rgba(*bg[:3], a); cr.fill(); ptext(cr, txt, 0, size * 0.08, size, fg, a, sw=0, shadow=False); cr.restore()

def slam(cr, txt, x, y, size, col, t, t0, a=1.0, rot=-0.05, maxw=900):
    if t < t0 or a <= 0: return
    k = prog(t, t0, t0 + 0.25); s = lerp(2.2, 1.0, ease_out(k)); sh = 12 * math.sin(t * 70) * (1 - prog(t, t0 + 0.25, t0 + 0.6))
    cr.save(); cr.translate(x + sh, y); cr.rotate(rot); cr.scale(s, s)
    ptext(cr, txt, 0, 0, fit(cr, txt, size, maxw), col, a * clamp(k * 3), sw=size * 0.12); cr.restore()

def pop_text(cr, txt, x, y, size, col, t, t0, a=1.0, fam='Poppins Black', maxw=960):
    if t < t0 or a <= 0: return
    k = pop_k(t, t0); cr.save(); cr.translate(x, y); cr.scale(k, k)
    ptext(cr, txt, 0, 0, fit(cr, txt, size, maxw, fam), col, a, fam=fam, sw=size * 0.13); cr.restore()

def pin(cr, cam, place, label, t, t0, col=GOLD, side='r', size=34, a=1.0):
    R.pin(cr, cam, P[place] if isinstance(place, str) else place, label, t, t0, col, side, size, a)

def atp(cr, cam, place, e, size, a=1.0, rot=0.0, dy=0):
    R.at(cr, cam, P[place] if isinstance(place, str) else place, e, size, a, rot, dy)

def dark(cr, a):
    if a <= 0: return
    g = cairo.RadialGradient(W / 2, MAPY, 150, W / 2, MAPY, 1100)
    g.add_color_stop_rgba(0, 0.25, 0.0, 0.03, 0.45 * a); g.add_color_stop_rgba(1, 0.02, 0, 0, 0.9 * a)
    cr.set_source(g); cr.paint()

# ---------- base map ----------
def draw_map(cr, t, cam):
    cr.set_source_rgba(*R.BG); cr.paint()
    g = cairo.RadialGradient(W / 2, MAPY, 100, W / 2, MAPY, 1300)
    g.add_color_stop_rgba(0, *R.WATER0[:3], 1); g.add_color_stop_rgba(1, *R.WATER1[:3], 1)
    cr.set_source(g); cr.paint()
    cr.new_path(); path_xy(cr, cam, G.land); cr.set_source_rgba(*R.LAND[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*R.COAST[:3], 0.9); cr.set_line_width(1.6); cr.stroke()
    cr.new_path(); path_xy(cr, cam, G.lakes); cr.set_source_rgba(*R.WATER0[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*R.COAST[:3], 0.7); cr.set_line_width(1); cr.stroke()
    glow = win('kazan', 'astrakhan', t=t)
    cr.new_path()
    for name, (x, y) in G.rivers:
        X, Y = S(cam, x, y); cr.move_to(X[0], Y[0]); [cr.line_to(a, b) for a, b in zip(X[1:], Y[1:])]
    cr.set_source_rgba(*RIVER[:3], 0.35); cr.set_line_width(1.6); cr.stroke()
    if glow > 0:
        cr.new_path()
        for name, (x, y) in G.rivers:
            if name == 'Volga':
                X, Y = S(cam, x, y); cr.move_to(X[0], Y[0]); [cr.line_to(a, b) for a, b in zip(X[1:], Y[1:])]
        cr.set_source_rgba(*RIVER[:3], 0.9 * glow); cr.set_line_width(5); cr.stroke_preserve()
        cr.set_source_rgba(*RIVER[:3], 0.25 * glow); cr.set_line_width(18); cr.stroke()
    g = cairo.RadialGradient(W / 2, H / 2, 500, W / 2, H / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.75)
    cr.set_source(g); cr.paint()

def realm_alpha(t):
    return ease_out(prog(t, bt('child')['start'] + 0.3, bt('child')['l0'] + 0.5))

# ---------- story ----------
def draw_story(cr, t, cam):
    # the realm, growing with each conquest
    ra = realm_alpha(t) * (0.55 if cam[2] > 0.6 else 1.0) * 0.6
    if ra > 0:
        poly(cr, cam, RUS_1533, CRIMSON, 0.26 * ra, CRIMSON, 2.5)
        tk = w('kazan', 'Kazan'); ta = w('astrakhan', 'Astrakhan'); ts = w('siberia', 'Siberia')
        if t >= tk: poly(cr, cam, KAZAN_KH, CRIMSON, 0.3 * ra * ease_out(prog(t, tk, tk + 0.5)), CRIMSON, 2.5)
        if t >= ta:
            k = ease_out(prog(t, ta, ta + 0.6))
            poly(cr, cam, ASTRA_KH, CRIMSON, 0.3 * ra * k, CRIMSON, 2.5); poly(cr, cam, VOLGA_LINK, CRIMSON, 0.3 * ra * k)
        if t >= ts: poly(cr, cam, SIBIR, CRIMSON, 0.3 * ra * ease_out(prog(t, ts, ts + 0.6)), CRIMSON, 2.5, dash=[10, 8])
    # child: age chip on "three", feuding boyars on "boyars"
    a = win('child', t=t)
    if a > 0:
        pin(cr, cam, 'moscow', 'MOSCOW', t, w('child', 'Moscow'), GOLD, 'r', 40, a)
        chip(cr, 'AGE 3', 540, 1180, 60, GOLD, INK, t, w('child', 'three'), a)
        tb = w('child', 'boyars')
        for i, (lon, lat) in enumerate(((36.2, 56.4), (39.2, 56.3), (36.4, 55.0), (39.0, 55.1))):
            if t >= tb + i * 0.1: atp(cr, cam, (lon, lat), '⚔️', 70 * pop_k(t, tb + i * 0.1), a, rot=0.2 * math.sin(t * 5 + i))
        x, y = R.L(cam, 37.6, 56.9); pop_text(cr, 'BOYAR FEUDS', x, y, 44, WHITE, t, tb, a)
    # crowned: crown on "crowned", title on "first", Caesar chip on "Caesar"
    a = win('crowned', t=t)
    if a > 0:
        tc = w('crowned', 'crowned')
        if t >= tc:
            x, y = R.L(cam, *P['moscow']); emoji(cr, '👑', x, y - 40, 230 * pop_k(t, tc), a, rot=0.08 * math.sin(t * 3))
            fl = 1 - prog(t, tc, tc + 0.3)
            if 0 < fl < 1: cr.set_source_rgba(1, 0.85, 0.4, 0.25 * fl); cr.paint()
        pop_text(cr, 'FIRST TSAR', 540, 560, 96, GOLD, t, w('crowned', 'first'), a)
        pop_text(cr, 'OF ALL RUSSIA', 540, 660, 64, WHITE, t, w('crowned', 'Russia'), a)
        chip(cr, 'TSAR = CAESAR', 540, 1180, 56, CRIMSON, WHITE, t, w('crowned', 'Caesar'), a)
    # Anastasia: "Remember that name" lights up ROMANOV
    a = win('anastasia', t=t)
    if a > 0:
        tm = w('anastasia', 'married')
        if t >= tm: atp(cr, cam, 'moscow', '💍', 150 * pop_k(t, tm), a, dy=-60)
        tr = w('anastasia', 'Remember')
        if t >= tr:
            k = pop_k(t, tr); cr.save(); cr.translate(540, 600); cr.scale(k, k)
            ptext(cr, 'ROMANOVNA', 0, 0, 120, ROMANOV, a * (0.75 + 0.25 * math.sin(t * 6)), sw=14); cr.restore()
            chip(cr, 'REMEMBER THIS NAME', 540, 720, 44, CRIMSON, WHITE, t, tr + 0.15, a)
    # Kazan: march on "stormed", the Khanate falls on "Kazan", St Basil's rises on "Basil's"
    a = win('kazan', t=t)
    if a > 0:
        ts, tk = w('kazan', 'stormed'), w('kazan', 'Kazan')
        route(cr, cam, [P['moscow'], (41.5, 56.0), P['nizhny'], (46.5, 55.9), P['kazan']], ease_io(prog(t, ts - 0.4, tk + 0.2)), CRIMSON, 8, dashed_rest=False, arrow=True)
        pin(cr, cam, 'moscow', 'MOSCOW', t, bt('kazan')['l0'], GOLD, 'l', 34, a)
        pin(cr, cam, 'kazan', 'KAZAN', t, tk, AMBER, 'b', 40, a)
        if t >= tk + 0.2: atp(cr, cam, 'kazan', '🔥', 80 * pop_k(t, tk + 0.2), a, dy=-40)
        x, y = R.L(cam, 49, 57.6); pop_text(cr, 'TATAR STRONGHOLD', x - 60, y, 34, AMBER, t, w('kazan', 'Tatar'), a)
        tb = w('kazan', 'Basil')
        if t >= tb:
            k = pop_k(t, tb); onion_church(cr, 300, 1110, 0.95 * k, a)
            pop_text(cr, "ST. BASIL'S CATHEDRAL", 640, 1170, 40, GOLD, t, tb + 0.2, a, maxw=600)
    # Astrakhan: down the Volga on "Astrakhan", whole river lights up on "Volga"
    a = win('astrakhan', t=t)
    if a > 0:
        ta = w('astrakhan', 'Astrakhan')
        route(cr, cam, [P['kazan'], (48.5, 53), (46, 51.5), (45.5, 49), P['astrakhan']], ease_io(prog(t, ta - 0.2, ta + 1.2)), CRIMSON, 8, dashed_rest=False, arrow=True)
        pin(cr, cam, 'kazan', 'KAZAN', t, bt('astrakhan')['start'] + 0.3, CRIMSON, 'r', 32, a)
        pin(cr, cam, 'astrakhan', 'ASTRAKHAN', t, ta + 1.0, AMBER, 'r', 38, a)
        x, y = R.L(cam, 51.5, 44); pop_text(cr, 'CASPIAN SEA', x, y, 32, RIVER, t, ta + 1.0, a, fam='Poppins ExtraBold')
        chip(cr, 'THE WHOLE VOLGA', 540, 1180, 56, RIVER, INK, t, w('astrakhan', 'Volga'), a)
    # Livonia: westward push on "west", 25 years on "twenty", DEFEAT on "defeat"
    a = win('livonia', t=t)
    if a > 0:
        twst = w('livonia', 'west')
        poly(cr, cam, LIVONIA, hexc('#9AA4B5'), 0.25 * a * ease_out(prog(t, twst, twst + 0.5)), hexc('#9AA4B5'), 2.5)
        route(cr, cam, [P['pskov'], (27.0, 58.0), (25.5, 58.4)], ease_io(prog(t, twst - 0.3, twst + 0.8)), CRIMSON, 9, dashed_rest=False, arrow=True)
        x, y = R.L(cam, 24.8, 58.3); pop_text(cr, 'LIVONIA', x, y, 44, WHITE, t, w('livonia', 'Livonian'), a)
        tl = w('livonia', 'dragged')
        for i, (lon, lat) in enumerate(((26.5, 57.3), (25.0, 59.0), (27.8, 56.2), (23.8, 57.6))):
            if t >= tl + i * 0.2: atp(cr, cam, (lon, lat), '⚔️', 60 * pop_k(t, tl + i * 0.2), a, rot=0.2 * math.sin(t * 5 + i))
        chip(cr, '1558–1583 · 25 YEARS', 540, 560, 52, GOLD, INK, t, w('livonia', 'twenty'), a)
        slam(cr, 'DEFEAT', 540, 1190, 130, CRIMSON, t, w('livonia', 'defeat'), a)
    # Loss: darkness, POISONED? on "poisoned", a crack on "broke"
    a = win('loss', t=t)
    if a > 0:
        dark(cr, a * ease_out(prog(t, w('loss', 'died'), w('loss', 'died') + 0.6)))
        td = w('loss', 'died')
        if t >= td: atp(cr, cam, 'moscow', '🥀', 160 * pop_k(t, td), a, dy=-30)
        pop_text(cr, 'ANASTASIA †1560', 540, 560, 64, WHITE, t, td, a)
        tp = w('loss', 'poisoned')
        if t >= tp:
            slam(cr, 'POISONED?', 540, 1190, 120, hexc('#7CFF4F'), t, tp, a)
            emoji(cr, '☠️'.replace('️', ''), 900, 1060, 90 * pop_k(t, tp + 0.15), a, rot=0.2 * math.sin(t * 6))
        tb = w('loss', 'broke')
        if t >= tb:
            k = ease_out(prog(t, tb, tb + 0.4)); rng = np.random.default_rng(7)
            pts = [(rng.uniform(0, W), 0)]
            for j in range(1, 12): pts.append((pts[-1][0] + rng.uniform(-120, 120), j * H / 11))
            n = max(2, int(len(pts) * k))
            cr.new_path(); cr.move_to(*pts[0]); [cr.line_to(*p) for p in pts[1:n]]
            cr.set_source_rgba(1, 1, 1, 0.9 * a); cr.set_line_width(6); cr.stroke()
    # Oprichnina: black land on "Oprichnina", riders on "riders", dog + broom, two slogans
    a = win('oprichnina', t=t)
    if a > 0:
        to = w('oprichnina', 'Oprichnina')
        poly(cr, cam, OPRICH, BLACK, 0.75 * a * ease_out(prog(t, to, to + 0.5)), BLOOD, 4)
        slam(cr, 'OPRICHNINA', 540, 1190, 120, BLOOD, t, to, a)
        tr = w('oprichnina', 'riders')
        if t >= tr:
            rng = np.random.default_rng(4)
            for i in range(18):
                lon, lat = rng.uniform(30, 48), rng.uniform(54.0, 62.5)
                dx = 0.25 * math.sin(t * 2 + i)
                x, y = R.L(cam, lon + dx, lat)
                knight(cr, x, y, 84 * pop_k(t, tr + i * 0.05), a)
        td, tbr = w('oprichnina', 'dogs'), w('oprichnina', 'brooms')
        if t >= td: emoji(cr, '🐕', 170, 820, 130 * pop_k(t, td), a, rot=-0.15)
        if t >= tbr: emoji(cr, '🧹', 910, 820, 130 * pop_k(t, tbr), a, rot=0.3 * math.sin(t * 4))
        pop_text(cr, 'SNIFF OUT TREASON', 540, 560, 64, WHITE, t, w('oprichnina', 'sniff'), a)
        pop_text(cr, 'SWEEP IT AWAY', 540, 660, 64, BLOOD, t, w('oprichnina', 'sweep'), a)
    # Novgorod: riders sweep in on "fell", the city burns on "Novgorod", THOUSANDS on "Thousands"
    a = win('novgorod', t=t)
    if a > 0:
        tf, tn = w('novgorod', 'fell'), w('novgorod', 'Novgorod')
        for i in range(8):
            k = ease_io(prog(t, tf - 0.6 + i * 0.05, tn + 0.3))
            lon = lerp(37.0 + 0.4 * math.sin(i), 31.6 + 0.3 * math.cos(i), k); lat = lerp(56.2 + 0.2 * i, 58.4 + 0.08 * i, k)
            x, y = R.L(cam, lon, lat); knight(cr, x, y, 58, a * (1 - 0.5 * prog(t, tn + 1.5, tn + 2.5)))
        pin(cr, cam, 'novgorod', 'NOVGOROD', t, tn, CRIMSON, 'l', 40, a)
        if t >= tn:
            atp(cr, cam, 'novgorod', '🔥', 120 * pop_k(t, tn) * (1 + 0.08 * math.sin(t * 12)), a, dy=-40)
            r = (t - tn) % 1.0; x, y = R.L(cam, *P['novgorod'])
            cr.new_path(); cr.arc(x, y, 30 + 200 * r, 0, 2 * math.pi); cr.set_source_rgba(*BLOOD[:3], (1 - r) * a); cr.set_line_width(6); cr.stroke()
        slam(cr, 'THOUSANDS KILLED', 540, 1190, 96, CRIMSON, t, w('novgorod', 'Thousands'), a)
    # Son: dark room, the crown cracks on "struck" and falls on "dead"
    a = win('son', t=t)
    if a > 0:
        dark(cr, a)
        ts, td = w('son', 'struck'), w('son', 'dead')
        fall = ease_io(prog(t, td, td + 1.0))
        cr.save(); cr.translate(540, 820 + 260 * fall); cr.rotate(0.6 * fall)
        emoji(cr, '👑', 0, 0, 300 * pop_k(t, bt('son')['l0'] + 0.2), a * (1 - 0.6 * fall))
        if t >= ts:
            k = ease_out(prog(t, ts, ts + 0.25)); rng = np.random.default_rng(3)
            for j in range(6):
                ang = rng.uniform(0, 2 * math.pi); ln = 160 * k
                cr.new_path(); cr.move_to(0, -10); cr.line_to(math.cos(ang) * ln * 0.5 + 12, math.sin(ang) * ln * 0.5 - 6)
                cr.line_to(math.cos(ang) * ln, math.sin(ang) * ln); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(5); cr.stroke()
        cr.restore()
        if t >= ts:
            fl = 1 - prog(t, ts, ts + 0.3)
            if 0 < fl < 1: cr.set_source_rgba(0.9, 0, 0, 0.4 * fl); cr.paint()
        pop_text(cr, 'HIS OWN SON', 540, 560, 100, CRIMSON, t, w('son', 'son'), a)
        slam(cr, 'DEAD', 540, 1190, 140, WHITE, t, td, a)
    # Siberia: Cossacks cross the Urals as named
    a = win('siberia', t=t)
    if a > 0:
        tc, tu, tsb = w('siberia', 'crossed'), w('siberia', 'Urals'), w('siberia', 'Siberia')
        X, Y = R.L(cam, [p[0] for p in URALS], [p[1] for p in URALS])
        for i, (x, y) in enumerate(zip(X, Y)):
            if t >= tu - 0.6 + i * 0.06: emoji(cr, '⛰️'.replace('️', ''), x, y, 70 * pop_k(t, tu - 0.6 + i * 0.06), a)
        x, y = R.L(cam, 56.8, 64.5); pop_text(cr, 'URAL MOUNTAINS', x, y, 34, PARCH, t, tu, a, fam='Poppins ExtraBold')
        route(cr, cam, YERMAK, ease_io(prog(t, tc - 0.3, tsb + 0.6)), GOLD, 8, head='🛶', head_size=70, dashed_rest=False, arrow=True)
        pin(cr, cam, 'qashliq', 'SIBIR', t, tsb + 0.5, AMBER, 'r', 38, a)
        pop_text(cr, 'SIBERIA', 540, 1190, 120, ICE, t, tsb, a)
    # Death: GROZNY → FORMIDABLE → TERRIBLE
    a = win('death', t=t)
    if a > 0:
        tg, tfo, tte = w('death', 'Grozny'), w('death', 'Formidable'), w('death', 'Terrible')
        tru = w('death', 'Russian')
        if t >= tru:
            k = pop_k(t, tru); cr.save(); cr.translate(540, 560); cr.scale(k, k); cyr_text(cr, 'ИВАН ГРОЗНЫЙ', 0, 0, 80, PARCH, a); cr.restore()
        pop_text(cr, '"GROZNY"', 540, 700, 110, GOLD, t, tg, a)
        chip(cr, '= FORMIDABLE', 540, 1030, 60, GOLD, INK, t, tfo, a)
        slam(cr, 'THE TERRIBLE', 540, 1190, 120, CRIMSON, t, tte, a)
        tdie = w('death', 'died')
        if t >= tdie: atp(cr, cam, 'moscow', '⚰️'.replace('️', ''), 120 * pop_k(t, tdie), a * (1 - ease_io(prog(t, tg - 0.3, tg))), dy=-40)
    # Fyodor and Boris
    a = win('fyodor', t=t)
    if a > 0:
        pop_text(cr, 'GENTLE & WEAK', 540, 560, 84, ICE, t, w('fyodor', 'gentle'), a)
        tb = w('fyodor', 'Boris')
        if t >= tb:
            k = pop_k(t, tb); cr.save(); cr.translate(540, 1150); cr.rotate(-0.04); cr.scale(k, k)
            ptext(cr, 'THE REAL POWER:', 0, -60, 46, PARCH, a, fam='Poppins ExtraBold', sw=6)
            ptext(cr, 'BORIS GODUNOV', 0, 30, 92, AMBER, a, sw=11); cr.restore()
    # Dmitry at Uglich
    a = win('dmitry', t=t)
    if a > 0:
        td = w('dmitry', 'Dmitry')
        pin(cr, cam, 'uglich', 'UGLICH', t, td, CRIMSON, 'r', 40, a)
        pin(cr, cam, 'moscow', 'MOSCOW', t, bt('dmitry')['start'] + 0.3, GOLD, 'r', 34, a)
        pop_text(cr, 'DMITRY · AGE 8', 540, 560, 70, WHITE, t, td, a)
        tth = w('dmitry', 'throat')
        if t >= tth: atp(cr, cam, 'uglich', '🗡️'.replace('️', ''), 110 * pop_k(t, tth), a, rot=0.3, dy=-70)
        tbl = w('dmitry', 'blamed')
        if t >= tbl:
            slam(cr, 'BORIS?', 540, 1190, 130, AMBER, t, tbl, a)
            emoji(cr, '🤔', 870, 1080, 100 * pop_k(t, tbl + 0.15), a)
    # End of the Rurikids: the dynasty bar from Part 1 slams shut
    a = win('end', t=t)
    if a > 0:
        tr = w('end', 'Rurik')
        k = ease_io(prog(t, tr, tr + 1.2))
        x0, x1, y = 120, 960, 1000
        rrect(cr, x0, y - 30, x1 - x0, 60, 30); cr.set_source_rgba(1, 1, 1, 0.12 * a); cr.fill()
        rrect(cr, x0, y - 30, max(60, (x1 - x0) * k), 60, 30); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
        if t >= tr:
            ptext(cr, '862', x0, y - 52, 44, WHITE, a, anchor='l', sw=6); ptext(cr, '1598', x1, y - 52, 44, WHITE, a * clamp(k * 3 - 2), anchor='r', sw=6)
            ptext(cr, 'RURIK DYNASTY', 540, y + 18, 38, INK, a, sw=0, shadow=False)
        pop_text(cr, 'NO HEIR', 540, 560, 100, WHITE, t, w('end', 'childless'), a)
        chip(cr, '736 YEARS', 540, 1130, 56, GOLD, INK, t, w('end', 'seven'), a)
        slam(cr, 'THE END', 540, 1290, 120, CRIMSON, t, w('end', 'end'), a)
    # Boris: volcano on "volcano", snow on "froze", toll on "two"
    a = win('boris', t=t)
    if a > 0:
        tv, tfz, ttw = w('boris', 'volcano'), w('boris', 'froze'), w('boris', 'two')
        if t >= tv:
            emoji(cr, '🌋', 170, 620, 200 * pop_k(t, tv), a)
            pop_text(cr, 'PERU · 1600', 170, 760, 38, AMBER, t, tv + 0.2, a, fam='Poppins ExtraBold', maxw=320)
        if t >= tfz:
            rng = np.random.default_rng(2); fa = a * ease_out(prog(t, tfz, tfz + 0.5))
            cr.set_source_rgba(0.75, 0.9, 1.0, 0.15 * fa); cr.paint()
            for i in range(120):
                x = (rng.uniform(0, W) + 30 * math.sin(t + i)) % W; y = (rng.uniform(0, H) + (t - tfz) * rng.uniform(80, 200)) % H
                cr.new_path(); cr.arc(x, y, rng.uniform(2, 5), 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.85 * fa); cr.fill()
            pop_text(cr, 'FROZEN SUMMERS', 640, 560, 64, ICE, t, tfz, a, maxw=700)
        slam(cr, '~2,000,000 DEAD', 540, 1190, 104, CRIMSON, t, ttw, a)
    # False Dmitry rides in from Poland
    a = win('false', 'poles', t=t)
    if a > 0:
        poly(cr, cam, POLAND, hexc('#E9E4F0'), 0.18 * a, hexc('#E9E4F0'), 2)
        x, y = R.L(cam, 23.5, 53.0); ptext(cr, 'POLAND–LITHUANIA', x, y, 32, WHITE, a * 0.9, fam='Poppins ExtraBold', sw=5)
    a = win('false', t=t)
    if a > 0:
        ts, tm = w('false', 'seized'), w('false', 'murdered')
        route(cr, cam, [P['krakow'], (25, 52.5), P['smolensk'], P['moscow']], ease_io(prog(t, w('false', 'claiming'), ts + 0.4)), hexc('#E9E4F0'), 8, head='🎭', head_size=70, dashed_rest=False, arrow=True)
        pin(cr, cam, 'moscow', 'MOSCOW', t, ts, GOLD, 'r', 38, a)
        pop_text(cr, 'IMPOSTOR!', 540, 560, 104, AMBER, t, w('false', 'dead'), a)
        if t >= tm:
            slam(cr, 'MURDERED', 540, 1190, 120, CRIMSON, t, tm, a)
    # Poles in the Kremlin
    a = win('poles', t=t)
    if a > 0:
        tk = w('poles', 'Kremlin')
        route(cr, cam, [P['warsaw'], (27, 53.3), P['smolensk'], P['moscow']], ease_io(prog(t, w('poles', 'Polish'), tk)), hexc('#E9E4F0'), 9, dashed_rest=False, arrow=True)
        pin(cr, cam, 'moscow', 'KREMLIN', t, tk, CRIMSON, 'r', 40, a)
        if t >= tk: atp(cr, cam, 'moscow', '⚔️', 110 * pop_k(t, tk), a, dy=-80)
        slam(cr, 'POLES IN THE KREMLIN', 540, 1190, 84, WHITE, t, tk, a, maxw=980)
    # Minin & Pozharsky: a people's army from Nizhny Novgorod
    a = win('minin', t=t)
    if a > 0:
        tr, tdr = w('minin', 'raised'), w('minin', 'drove')
        pin(cr, cam, 'nizhny', 'NIZHNY NOVGOROD', t, w('minin', 'Kuzma'), GOLD, 'b', 32, a)
        rng = np.random.default_rng(5)
        for i in range(14):
            k = ease_io(prog(t, tr + i * 0.03, tdr + 0.3))
            lon = lerp(44.0 + rng.uniform(-0.6, 0.6), 38.0 + rng.uniform(-0.3, 0.3), k); lat = lerp(56.33 + rng.uniform(-0.4, 0.4), 55.8 + rng.uniform(-0.3, 0.3), k)
            x, y = R.L(cam, lon, lat); emoji(cr, '🛡️'.replace('️', ''), x, y, 50 * pop_k(t, tr + i * 0.04), a)
        pin(cr, cam, 'moscow', 'MOSCOW', t, w('minin', 'Kuzma'), CRIMSON, 'l', 36, a)
        pop_text(cr, 'A BUTCHER', 300, 560, 64, WHITE, t, w('minin', 'butcher'), a, maxw=480)
        pop_text(cr, '& A PRINCE', 790, 560, 64, GOLD, t, w('minin', 'prince'), a, maxw=480)
        slam(cr, 'MOSCOW LIBERATED', 540, 1190, 90, GOLD, t, tdr, a, maxw=980)
    # Romanov: the name from earlier returns
    a = win('romanov', t=t)
    if a > 0:
        tm, tr, tan, tth = w('romanov', 'Michael'), w('romanov', 'Romanov'), w('romanov', 'Anastasia'), w('romanov', 'three')
        if t >= tm: atp(cr, cam, 'moscow', '👑', 200 * pop_k(t, tm), a, rot=0.06 * math.sin(t * 3), dy=-60)
        slam(cr, 'ROMANOV', 540, 600, 170, ROMANOV, t, tr, a)
        chip(cr, "ANASTASIA'S GREAT-NEPHEW", 540, 720, 40, CRIMSON, WHITE, t, tan, a)
        if t >= tth:
            k = ease_io(prog(t, tth, tth + 1.2)); x0, x1, y = 120, 960, 1180
            rrect(cr, x0, y - 30, x1 - x0, 60, 30); cr.set_source_rgba(1, 1, 1, 0.12 * a); cr.fill()
            rrect(cr, x0, y - 30, max(60, (x1 - x0) * k), 60, 30); cr.set_source_rgba(*ROMANOV[:3], a); cr.fill()
            ptext(cr, '1613', x0, y - 52, 44, WHITE, a, anchor='l', sw=6); ptext(cr, '1917', x1, y - 52, 44, WHITE, a * clamp(k * 3 - 2), anchor='r', sw=6)
            ptext(cr, f'{int(304 * k)} YEARS', 540, y + 18, 38, INK, a, sw=0, shadow=False)

# ---------- hook / intro / title / cliff ----------
def draw_hook(cr, t):
    if t >= bt('intro')['start']: return False
    b = next((x for x in TL['beats'] if x['key'] in HOOK and x['start'] <= t < x['end'] + 1e-6), bt('h1'))
    tv = ANCHOR[b['key']] + (t - b['start'])
    cx, cy, s = R.camera(tv)
    s *= 1.0 + 0.18 * (1 - ease_out(prog(t, b['start'], b['start'] + 0.7))) + 0.04 * prog(t, b['start'], b['end'])
    cam = (cx, cy, s)
    draw_map(cr, tv, cam); draw_story(cr, tv, cam)
    g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgba(0, 0, 0, 0, 0.85); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    cr.set_source(g); cr.paint()
    rows = {'h1': [('unleashed', 'HE UNLEASHED', 70, WHITE, 270), ('riders', 'RIDERS', 190, BLOOD, 500), ('black', 'IN BLACK', 100, WHITE, 650)],
            'h2': [('slaughtered', 'SLAUGHTERED', 150, CRIMSON, 380), ('entire', 'AN ENTIRE CITY', 90, WHITE, 540)],
            'h3': [('killed', 'AND KILLED', 90, WHITE, 300), ('own', 'HIS OWN', 120, WHITE, 450), ('son', 'SON', 230, CRIMSON, 680)]}[b['key']]
    for word, txt, size, col, y in rows:
        tw0 = w(b['key'], word)
        if size > 140: slam(cr, txt, 540, y, size, col, t, tw0, 1.0, maxw=880)
        else: pop_text(cr, txt, 540, y, size, col, t, tw0, 1.0)
        if size > 140:
            fl = 1 - prog(t, tw0, tw0 + 0.25)
            if t >= tw0 and 0 < fl < 1: cr.set_source_rgba(1, 1, 1, 0.2 * fl); cr.paint()
    fl = 1 - prog(t, b['start'], b['start'] + 0.18)
    if b['key'] != 'h1' and 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.55 * fl); cr.paint()
    return True

def draw_intro(cr, t):
    b = bt('intro')
    if not (b['start'] <= t < b['end']): return
    a = 1 - ease_io(prog(t, b['end'] - 0.25, b['end']))
    dark(cr, 0.9)
    ti, tt, taf, two = w('intro', 'Ivan'), w('intro', 'Terrible'), w('intro', 'after'), w('intro', 'worse')
    slam(cr, 'IVAN', 540, 600, 220, CRIMSON, t, ti, a)
    slam(cr, 'THE TERRIBLE', 540, 780, 130, WHITE, t, tt, a, maxw=980)
    pop_text(cr, '...AND WHAT CAME AFTER', 540, 1050, 60, PARCH, t, taf, a)
    slam(cr, 'WAS EVEN WORSE', 540, 1210, 100, CRIMSON, t, two, a, maxw=980)
    fl = 1 - prog(t, b['start'], b['start'] + 0.18)
    if 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.55 * fl); cr.paint()

def draw_title(cr, t):
    b = bt('title')
    a = ease_out(prog(t, b['start'], b['start'] + 0.3)) * (1 - ease_io(prog(t, b['end'] - 0.3, b['end'])))
    if a <= 0: return
    cr.set_source_rgba(0.03, 0.02, 0.04, 0.65 * a); cr.paint()
    k1 = pop_k(t, b['start'] + 0.05)
    cr.save(); cr.translate(540, 640); cr.scale(k1, k1); ptext(cr, 'THE ENTIRE HISTORY OF', 0, 0, 56, PARCH, a, fam='Poppins ExtraBold', sw=7); cr.restore()
    slam(cr, 'RUSSIA', 540, 840, 230, CRIMSON, t, b['start'] + 0.3, a, rot=0, maxw=1000)
    chip(cr, 'PART 02', 540, 990, 70, GOLD, INK, t, b['start'] + 0.85, a)
    pop_text(cr, 'TERROR AND TROUBLES · 1533–1613', 540, 1110, 40, WHITE, t, b['start'] + 1.15, a, fam='Poppins ExtraBold')
    fl = 1 - prog(t, b['start'] + 0.3, b['start'] + 0.65)
    if 0 < fl < 1: cr.set_source_rgba(1, 1, 1, 0.25 * fl * a); cr.paint()

def draw_cliff(cr, t, cam):
    b, n = bt('cliff'), bt('next')
    if t < b['start']: return
    dark(cr, ease_out(prog(t, b['start'], b['l0'] + 1.0)))
    fade = 1 - ease_io(prog(t, n['start'], n['l0']))
    pop_text(cr, 'HIS GRANDSON...', 540, 560, 80, WHITE, t, w('cliff', 'grandson'), fade)
    pop_text(cr, 'INTO THE MODERN WORLD', 540, 1020, 56, PARCH, t, w('cliff', 'modern'), fade)
    slam(cr, 'BY FORCE', 540, 1260, 130, CRIMSON, t, w('cliff', 'force'), fade)
    slam(cr, 'PETER', 540, 700, 220, GOLD, t, w('next', 'Peter'), 1, rot=0)
    slam(cr, 'THE GREAT', 540, 880, 140, WHITE, t, w('next', 'Great'), 1, rot=0, maxw=1000)
    chip(cr, 'PART 03', 540, 1060, 70, GOLD, INK, t, w('next', 'Part'))
    tf = w('next', 'Follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1260); cr.scale(k, k)
        wd = tw(cr, 'FOLLOW FOR PART 03', 52); rrect(cr, -wd / 2 - 90, -60, wd + 180, 94, 47); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, 'FOLLOW FOR PART 03', 30, 4, 52, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9))
        cr.restore()

# ---------- cards, chapter label, timeline, captions ----------
def draw_card(cr, t):
    for b in TL['beats']:
        if not b['card']: continue
        t0 = w(b['key'], b['cword']); t1 = b['end']
        if not (t0 <= t <= t1): continue
        e, name, sub = b['card']
        k = ease_out(prog(t, t0, t0 + 0.35)); out = 1 - ease_io(prog(t, t1 - 0.35, t1)); a = k * out
        cr.save(); cr.translate(lerp(-500, 0, k), 0)
        rrect(cr, 50, 1300, 980, 170, 85); cr.set_source_rgba(0.05, 0.04, 0.07, 0.9 * a); cr.fill_preserve()
        cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
        cr.new_path(); cr.arc(135, 1385, 70, 0, 2 * math.pi)
        g = cairo.RadialGradient(115, 1360, 10, 135, 1385, 70); g.add_color_stop_rgba(0, *GOLD[:3], a); g.add_color_stop_rgba(1, 0.55, 0.38, 0.1, a)
        cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(4); cr.stroke()
        emoji(cr, e, 135, 1380, 84 * ease_back(prog(t, t0 + 0.1, t0 + 0.45), 3), a)
        ptext(cr, name, 230, 1385, fit(cr, name, 58, 760), WHITE, a, anchor='l', sw=8)
        ptext(cr, sub, 232, 1435, fit(cr, sub, 32, 760, 'Poppins SemiBold'), PARCH, a, fam='Poppins SemiBold', anchor='l', sw=5)
        cr.restore()

def draw_chapter_label(cr, t):
    if t < bt('child')['start'] or t > bt('cliff')['start']: return
    ch = None
    for b in TL['beats']:
        if t >= b['start'] and b['chap']: ch = b['chap']
    if ch:
        txt = f'CHAPTER {ch[0]} · {ch[1]}'
        ptext(cr, txt, 540, 110, fit(cr, txt, 34, 960, 'Poppins ExtraBold'), PARCH, 0.9, fam='Poppins ExtraBold', sw=5)

def draw_timeline(cr, t):
    a = ease_out(prog(t, bt('child')['start'], bt('child')['start'] + 0.5)) * (1 - ease_io(prog(t, bt('cliff')['start'], bt('cliff')['start'] + 0.5)))
    if a <= 0: return
    v = year_at(t) or 1533
    x0, x1, y = 90, 990, 1815; y0, y1 = 1533, 1613
    cr.new_path(); cr.move_to(x0, y); cr.line_to(x1, y); cr.set_source_rgba(1, 1, 1, 0.25 * a); cr.set_line_width(4); cr.stroke()
    xv = lerp(x0, x1, clamp((v - y0) / (y1 - y0)))
    cr.new_path(); cr.move_to(x0, y); cr.line_to(xv, y); cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(6); cr.stroke()
    for yr in (1533, 1547, 1565, 1584, 1598, 1613):
        x = lerp(x0, x1, (yr - y0) / (y1 - y0)); on = v >= yr - 0.5
        cr.new_path(); cr.arc(x, y, 9 if on else 6, 0, 2 * math.pi); cr.set_source_rgba(*(GOLD if on else WHITE)[:3], a * (1 if on else 0.4)); cr.fill()
        ptext(cr, str(yr), x, y + 44, 24, WHITE if on else (0.6, 0.6, 0.6), a, fam='Poppins SemiBold', sw=0, shadow=False)
    cr.new_path(); cr.arc(xv, y, 14, 0, 2 * math.pi); cr.set_source_rgba(*GOLD[:3], a); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(3); cr.stroke()

def caption_groups(b):
    words, src, toks = b['words'], list(b['tokens']), []
    for _, _, x in words:
        n = len(x.split()); toks.append(' '.join(src[:n])); src = src[n:]
    if src or len(toks) != len(words): toks = [x for _, _, x in words]
    groups, cur = [], []
    for tok, (s, e, _) in zip(toks, words):
        cur.append((s, e, tok))
        if len(cur) == 3 or re.search(r"[.,!?:;…]$", tok): groups.append(cur); cur = []
    if cur: groups.append(cur)
    return groups

HOT = ('ivan', 'terrible', 'tsar', 'kazan', 'volga', 'novgorod', 'oprichnina', 'son', 'siberia', 'boris', 'dmitry', 'romanov',
       'moscow', 'kremlin', 'poles', 'peter', 'anastasia', 'grozny', 'dead', 'murdered', 'defeat')

def draw_captions(cr, t):
    for b in TL['beats']:
        if not b['words'] or not (b['l0'] - 0.05 <= t < b['l1'] + 0.3): continue
        groups = b.setdefault('_groups', caption_groups(b)); g = None
        for i, gr in enumerate(groups):
            nxt = groups[i + 1][0][0] if i + 1 < len(groups) else b['l1'] + 0.3
            if gr[0][0] - 0.05 <= t < nxt: g = gr; break
        if g is None: return
        ups = [x[2].upper() for x in g]
        size = 66; face(cr, size); space = cr.text_extents(' ').x_advance
        cur = max([j for j, x in enumerate(g) if x[0] <= t + 0.02] or [0])
        widths = [cr.text_extents(u).x_advance * (1.12 if j == cur else 1.0) for j, u in enumerate(ups)]
        total = sum(widths) + space * (len(ups) - 1); sc = min(1.0, 980 / total)
        cr.save(); cr.translate(540, 1650); cr.scale(sc, sc); x = -total / 2
        for j, (u, wd) in enumerate(zip(ups, widths)):
            cr.save(); cr.translate(x + wd / 2, 0)
            if j == cur:
                k = ease_back(prog(t, g[j][0], g[j][0] + 0.15), 3); cr.scale(1 + 0.12 * k, 1 + 0.12 * k)
            hot = any(ch.isdigit() for ch in u) or any(norm(u).startswith(h) for h in HOT)
            col = GOLD if j == cur else (hexc('#FFCF70') if hot else WHITE)
            ptext(cr, u, 0, 0, size, col, 1.0 if j <= cur else 0.6, sw=10)
            cr.restore(); x += wd + space
        cr.restore(); return

def draw_footnote(cr, t):
    a = realm_alpha(t) * (1 - ease_io(prog(t, bt('cliff')['start'], bt('cliff')['start'] + 0.5)))
    if a > 0: ptext(cr, 'Borders approximate', 1040, 1545, 22, (0.7, 0.66, 0.58), 0.8 * a, fam='Poppins SemiBold', anchor='r', sw=0, shadow=False)

def render_frame(cr, t):
    if draw_hook(cr, t):
        draw_captions(cr, t); return
    cam = R.camera(t)
    draw_map(cr, t, cam)
    draw_story(cr, t, cam)
    draw_intro(cr, t)
    draw_cliff(cr, t, cam)
    draw_year(cr, t)
    draw_chapter_label(cr, t)
    draw_card(cr, t)
    draw_timeline(cr, t)
    draw_footnote(cr, t)
    draw_title(cr, t)
    R.draw_chapter_card(cr, t)
    draw_captions(cr, t)
    f = prog(t, TL['dur'] - 0.5, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- score ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(31)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n)
    chords = [[52, 55, 59], [48, 52, 55], [50, 53, 57], [47, 51, 54]]  # Em C Dm B: darker
    bar = 60 / 80 * 4
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(bar * 1.3 * SR)) / SR
        env = np.minimum(1, L_ / 0.8) * np.exp(-L_ * 0.45); vib = 1 + 0.003 * np.sin(2 * np.pi * 5 * L_)
        put(music, ci * bar, sum(0.035 * (np.sin(2 * np.pi * note(m) * vib * L_) + 0.5 * np.sin(2 * np.pi * note(m + 12) * 1.002 * L_)) for m in ch) * env)
        put(music, ci * bar, 0.13 * np.sin(2 * np.pi * note(ch[0] - 24) * L_) * env)
    beat = 60 / 80
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 > bt('cliff')['start'] or bt('intro')['start'] <= t0 < bt('child')['start']: continue
        if bi % 2 == 0 or bi % 8 == 7 or t0 < bt('intro')['start']:
            L_ = np.arange(int(0.6 * SR)) / SR
            put(music, t0, 0.5 * np.sin(2 * np.pi * np.cumsum(58 + 50 * np.exp(-L_ * 18)) / SR) * np.exp(-L_ * 6))
            put(music, t0, 0.05 * rng.standard_normal(len(L_)) * np.exp(-L_ * 30))
        M = np.arange(int(0.05 * SR)); put(music, t0 + beat / 2, 0.02 * rng.standard_normal(len(M)) * np.exp(-M / SR * 60))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.7):
        L_ = np.arange(int(2.0 * SR)) / SR
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 80 * np.exp(-L_ * 10)) / SR) * np.exp(-L_ * 2.5))
        put(fx, t0, 0.15 * amp * rng.standard_normal(len(L_)) * np.exp(-L_ * 12))
    def whoosh(t0, amp=0.18):
        nz = rng.standard_normal(int(0.8 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2
        put(fx, t0, amp * np.convolve(nz, np.ones(30) / 30, 'same') * env)
    def bell(t0, amp=0.25):
        L_ = np.arange(int(3.0 * SR)) / SR
        put(fx, t0, amp * sum(np.sin(2 * np.pi * f * L_) * np.exp(-L_ * d) for f, d in ((196, 0.9), (392 * 1.01, 1.3), (587, 1.8), (784 * 0.99, 2.4))))
    for key, word in (('h1', 'riders'), ('h2', 'slaughtered'), ('h3', 'son'), ('intro', 'Ivan'), ('intro', 'worse')):
        boom(w(key, word), 0.85)
    for key in ('h2', 'h3', 'intro'): whoosh(bt(key)['start'] - 0.25, 0.25)
    boom(bt('title')['start'] + 0.3, 0.9); bell(bt('title')['start'] + 0.3)
    for b in T['beats']:
        if b['key'] in HOOK or b['key'] in ('intro', 'title'): continue
        whoosh(b['start'] - 0.2, 0.12)
        if b['chap']: boom(b['start'] + 0.15, 0.6)
    for key, word in (('crowned', 'crowned'), ('kazan', 'Kazan'), ('livonia', 'defeat'), ('loss', 'broke'), ('novgorod', 'Novgorod'),
                      ('son', 'struck'), ('son', 'dead'), ('death', 'Terrible'), ('dmitry', 'blamed'), ('end', 'end'),
                      ('false', 'murdered'), ('poles', 'Kremlin'), ('minin', 'drove'), ('romanov', 'Romanov'), ('cliff', 'force'), ('next', 'Peter')):
        boom(w(key, word), 0.55)
    bell(w('crowned', 'crowned'), 0.2); bell(w('romanov', 'Romanov'), 0.2)
    for key, a0, a1 in (('oprichnina', 'riders', 'sweep'), ('novgorod', 'fell', 'Novgorod')):  # hoofbeats
        t0, t1 = w(key, a0) - 0.5, w(key, a1) + 0.5
        for k in range(int((t1 - t0) / 0.18)):
            L_ = np.arange(int(0.08 * SR)) / SR; put(fx, t0 + k * 0.18 + (0.05 if k % 2 else 0), 0.12 * np.sin(2 * np.pi * 90 * L_) * np.exp(-L_ * 40))
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.02) * np.minimum(1, (dur - tt) / 1.2)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

# ---------- setup & render ----------
def setup(data_dir, cache):
    global TL, G
    TL = build(WordVoice(cache)); G = R.Geo(data_dir)
    R.TL, R.G = TL, G
    TL['yev'] = year_events()
    ANCHOR['h1'] = w('oprichnina', 'riders') - 0.1
    ANCHOR['h2'] = w('novgorod', 'Novgorod') - 0.4
    ANCHOR['h3'] = w('son', 'struck') - 0.5

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    data_dir, out = sys.argv[1:3]
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_ru_wb'))
    print(f"duration {TL['dur']:.1f}s")
    for b in TL['beats']: print(f"  {b['key']:10s} {b['start']:6.2f}-{b['end']:6.2f}  words {len(b['words'])}/{len(b['tokens'])}")
    if len(sys.argv) > 3 and sys.argv[3] == '--preview':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        for ts in sys.argv[4].split(','):
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
