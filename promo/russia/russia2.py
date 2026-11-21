"""Russia Part 01, v2: cold-open hook montage + everything on screen synced to the narrator's actual words.
Uses edge-tts word boundaries: captions, years, names, labels and animations fire on the spoken word.
Reuses the map, geometry and drawing helpers from russia.py.
Usage: python3 russia2.py <data_dir> <out.mp4> [--preview t1,t2,...]
"""
import asyncio, hashlib, json, math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import russia as R
from russia import (P, KIEV_RUS, HORDE, MOSCOW_1300, MUSCOVY_1480, SPLITS, VIKING, UGRA, GOLD, CRIMSON, WHITE, AMBER, ICE,
                    PARCH, INK, RIVER, W, H, FPS, MAPY, L, poly, route, pin, at, win, ptext, rrect, tw, fit, face, emoji, pop_k)
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

VOICE, RATE = 'en-GB-RyanNeural', '+5%'
TODAY_CAM = (100, 63, 0.105)

# key, narration, year, word that flips the year, camera, chapter card, medallion (emoji, name, subtitle, trigger word)
BEATS = [
    ('h1', "The biggest country on Earth began with a Viking...", None, None, TODAY_CAM, None, None),
    ('h2', "its cities were burned by the Mongols...", None, None, TODAY_CAM, None, None),
    ('h3', "and it rose again from a tiny town called Moscow.", None, None, TODAY_CAM, None, None),
    ('today', "Today, it spans eleven time zones.", 'TODAY', None, TODAY_CAM, None, None),
    ('past', "But twelve hundred years ago... it didn't exist at all.", 862, None, TODAY_CAM, None, None),
    ('title', "This is how it all began.", 862, None, (33, 54, 0.32), None, None),
    ('forest', "In the ninth century, these lands were dense forest, home to East Slavic tribes... and crossed by mighty rivers.",
     862, None, (33, 55, 0.5), ('I', 'RIVERS AND RAIDERS'), None),
    ('vikings', "Scandinavian traders, known as the Varangians, used those rivers as highways, sailing all the way to Constantinople.",
     862, None, (27, 51, 0.36), None, None),
    ('rurik', "In 862, according to the old chronicles, the people of Novgorod invited a Varangian named Rurik to rule over them.",
     862, '862', (31.3, 58.3, 0.85), None, ('👑', 'RURIK', 'Varangian prince · r. 862–879', 'Rurik')),
    ('dynasty', "His dynasty would rule for more than seven hundred years.", 862, None, (31.3, 57.5, 0.7), None, None),
    ('oleg', "In 882, his successor Oleg sailed south and seized Kyiv. A new power was born: Kievan Rus', the shared ancestor of Russia, Ukraine and Belarus.",
     882, '882', (31, 54.5, 0.5), ('II', 'THE RISE OF KYIV'), ('⚔️', 'OLEG', 'Prince of Kyiv · r. 882–912', 'Oleg')),
    ('faith', "In 988, Prince Vladimir chose a faith for his people. The chronicle says he rejected Islam because, as he put it, drinking is the joy of the Rus'.",
     988, '988', (31, 52, 0.45), None, ('⛪', 'VLADIMIR THE GREAT', 'Grand Prince · r. 980–1015', 'Vladimir')),
    ('orthodox', "Instead, he chose Orthodox Christianity from Constantinople... a decision that shapes Russia to this day.",
     988, None, (30, 47, 0.33), None, None),
    ('yaroslav', "Under Yaroslav the Wise, Kyiv became one of the richest cities in Europe. His daughters became queens of France, Norway and Hungary.",
     1019, 'Yaroslav', (17, 54.5, 0.2), None, ('📜', 'YAROSLAV THE WISE', 'Grand Prince · r. 1019–1054', 'Yaroslav')),
    ('split', "But after Yaroslav, his heirs fought each other, and the realm split apart. In 1147, a small town called Moscow appears in the chronicles for the first time.",
     1147, '1147', (34, 55, 0.5), ('III', 'THE STORM FROM THE EAST'), None),
    ('mongols', "Then, in 1237, the Mongols arrived. Batu Khan's armies burned city after city. In 1240, Kyiv fell.",
     1237, '1237', (40, 53.5, 0.33), None, ('🏹', 'BATU KHAN', 'Mongol commander · d. 1255', 'Batu')),
    ('horde', "For nearly two and a half centuries, the Russian princes would pay tribute to the Golden Horde.",
     1240, None, (52, 51, 0.15), None, None),
    ('nevsky', "In the northwest, Prince Alexander Nevsky crushed the Teutonic Knights on a frozen lake: the Battle on the Ice.",
     1242, 'Alexander', (27.6, 58.6, 1.5), None, ('🛡️', 'ALEXANDER NEVSKY', 'Prince of Novgorod · 1221–1263', 'Alexander')),
    ('kalita', "Meanwhile, Moscow played a clever game. Its prince, Ivan Kalita, nicknamed Moneybag, collected taxes for the Khans... and grew rich and powerful.",
     1325, 'Ivan', (40, 52.5, 0.36), ('IV', 'THE RISE OF MOSCOW'), ('💰', 'IVAN I KALITA', 'Prince of Moscow · r. 1325–1340', 'Ivan')),
    ('kulikovo', "In 1380, Prince Dmitry defeated a Horde army at Kulikovo Field.",
     1380, '1380', (38.6, 54.6, 0.8), None, ('⚔️', 'DMITRY DONSKOY', 'Prince of Moscow · r. 1359–1389', 'Dmitry')),
    ('ugra', "And in 1480, Ivan the Great faced down the Horde at the Ugra River. The Mongols retreated without a major battle.",
     1480, '1480', (35.3, 54.62, 2.6), None, ('👑', 'IVAN III THE GREAT', 'Grand Prince · r. 1462–1505', 'Ivan')),
    ('free', "After two hundred and forty years, Moscow was free.", 1480, None, (42, 58, 0.2), None, None),
    ('cliff', "But its rise was only beginning... and Ivan's grandson would become one of the most feared rulers in history.",
     1480, None, (37.6, 55.75, 0.7), None, None),
    ('next', "Ivan the Terrible. That's Part Two. Follow, so you don't miss it.", 1533, 'Ivan', (37.6, 55.75, 0.9), None, None),
]
HOOK = ('h1', 'h2', 'h3')

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
            c = edge_tts.Communicate(text, VOICE, rate=RATE, proxy=os.environ.get('HTTPS_PROXY'), boundary='WordBoundary')
            async for ch in c.stream():
                if ch['type'] == 'audio': buf.extend(ch['data'])
                elif ch['type'] == 'WordBoundary':
                    words.append((ch['offset'] / 1e7, (ch['offset'] + ch['duration']) / 1e7, ch['text']))
            return bytes(buf), words
        mp3, words = asyncio.run(run())
        pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', 'pipe:0', '-f', 's16le', '-ac', '1', '-ar', str(SR), 'pipe:1'],
                             input=mp3, capture_output=True, check=True).stdout
        a = np.frombuffer(pcm, '<i2').astype(np.float32) / 32767
        nz = np.nonzero(np.abs(a) > 0.01)[0]; i0 = max(nz[0] - 200, 0)
        a = a[i0:nz[-1] + 1200]; sh = i0 / SR
        words = [(max(0.0, s - sh), max(0.0, e - sh), w) for s, e, w in words]
        np.save(pa, a); json.dump(words, open(pw, 'w')); return a, words

def norm(s): return re.sub(r"[^a-z0-9]", '', s.lower())

def build(voice):
    t, beats, clips = 0.05, [], []
    lead = {'h1': 0.05, 'h2': 0.05, 'h3': 0.05, 'today': 0.25, 'past': 0.15}
    tail = {'h1': 0.08, 'h2': 0.08, 'h3': 0.25, 'title': 1.6, 'past': 0.8, 'next': 2.2, 'free': 0.9}
    for key, text, year, yword, cam, chap, card in BEATS:
        b = dict(key=key, text=text, year=year, yword=yword, cam=cam, chap=chap, card=card[:3] if card else None,
                 cword=card[3] if card else None, start=t)
        a, words = voice.get(text)
        b['l0'] = t + (1.55 if chap else lead.get(key, 0.35)); b['l1'] = b['l0'] + len(a) / SR
        b['words'] = [(b['l0'] + s, b['l0'] + e, w) for s, e, w in words]
        b['tokens'] = text.split()
        clips.append((b['l0'], a))
        t = b['l1'] + tail.get(key, 0.45); b['end'] = t
        beats.append(b)
    return dict(beats=beats, by={b['key']: b for b in beats}, clips=clips, dur=t)

TL = None
G = None
_missing = set()

def bt(key): return TL['by'][key]

def w(key, word, n=0, end=False):
    """Time the narrator says `word` (n-th match) in beat `key`."""
    q, hits = norm(word), []
    for s, e, x in bt(key)['words']:
        if any(norm(part).startswith(q) for part in x.split()): hits.append((s, e))
    if len(hits) > n: return hits[n][1] if end else hits[n][0]
    if (key, word) not in _missing: _missing.add((key, word)); print(f'  ! no word "{word}" in {key}', file=sys.stderr)
    return bt(key)['l0']

# ---------- years, synced to the spoken year ----------
def year_events():
    ev = [(bt('today')['start'], 'TODAY')]
    for b in TL['beats']:
        if b['key'] in HOOK or b['key'] in ('today', 'past', 'title'): continue
        if isinstance(b['year'], int):
            ev.append((w(b['key'], b['yword']) if b['yword'] else b['l0'], b['year']))
    ev.append((w('mongols', '1240'), 1240))
    return sorted(ev, key=lambda e: e[0])

def year_at(t):
    if t < bt('today')['start']: return None
    pb = bt('past')
    r0, r1 = w('past', 'twelve'), w('past', 'ago', end=True) + 0.2
    if r0 <= t < bt('forest')['start'] + 0.01 or (pb['start'] <= t < r0):
        if t < r0: return 'TODAY'
        return lerp(2026, 862, ease_io(prog(t, r0, r1)))
    val, prev = None, None
    for te, v in TL['yev']:
        if t < te - 0.1: break
        if isinstance(v, int) and isinstance(prev, int) and prev != v:
            val = lerp(prev, v, ease_out(prog(t, te - 0.1, te + 0.7)))
        else: val = v
        prev = v
    return val

def draw_year(cr, t):
    if bt('title')['start'] - 0.2 < t < bt('title')['end'] + 0.2: return
    v = year_at(t)
    if v is None: return
    txt = v if isinstance(v, str) else str(int(round(v)))
    a = ease_out(prog(t, bt('today')['start'], bt('today')['start'] + 0.3))
    size = 170 if not isinstance(v, str) else 120
    ptext(cr, txt, 540, 300, size, GOLD, a, sw=16)
    if not isinstance(v, str): ptext(cr, 'AD', 540 + tw(cr, txt, size) / 2 + 52, 300, 46, PARCH, a, fam='Poppins ExtraBold', sw=6)

# ---------- story, every beat keyed to the narration ----------
def draw_story(cr, t, cam):
    # today: eleven time zones tick in while "eleven time zones" is spoken
    b = bt('today')
    if b['start'] <= t < b['end'] + 0.4:
        a = 1 - ease_io(prog(t, b['end'] - 0.2, b['end'] + 0.3))
        z0, z1 = w('today', 'eleven'), w('today', 'zones', end=True)
        for i in range(11):
            k = pop_k(t, lerp(z0, z1, i / 10))
            if t < lerp(z0, z1, i / 10): continue
            lon = 30 + i * 14.5
            X, Y = L(cam, np.full(30, lon), np.linspace(44, 78, 30))
            cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:], Y[1:])]
            cr.set_dash([8, 8]); cr.set_source_rgba(1, 1, 1, 0.45 * a); cr.set_line_width(2); cr.stroke(); cr.set_dash([])
            x, y = L(cam, lon + 7, 75 if i % 2 else 72)
            cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, str(i + 1), 0, 0, 40, GOLD, a, sw=6); cr.restore()
    # forest: trees on "dense forest", tribes on "East", rivers on "rivers"
    a = win('forest', t=t)
    if a > 0:
        rng = np.random.default_rng(3); t0 = w('forest', 'dense')
        for i in range(55):
            lon, lat = rng.uniform(24, 44), rng.uniform(49.5, 61)
            if t >= t0 + i * 0.02: at(cr, cam, (lon, lat), '🌲', 46 * pop_k(t, t0 + i * 0.02), a * 0.9)
        x, y = L(cam, 36, 56.5); te = w('forest', 'East')
        ptext(cr, 'EAST SLAVIC TRIBES', x, y, 40, PARCH, a * ease_out(prog(t, te, te + 0.3)), fam='Poppins ExtraBold', sw=6)
        tr = w('forest', 'rivers')
        for name, lon, lat in (('DNIPRO', 31.2, 52.6), ('VOLGA', 42.5, 57.2)):
            x, y = L(cam, lon, lat); ptext(cr, name, x, y, 30, RIVER, a * ease_out(prog(t, tr, tr + 0.3)), fam='Poppins ExtraBold', sw=5)
    # Varangians: the ship leaves on "Scandinavian" and reaches Constantinople as it's spoken
    b = bt('vikings'); a = win('vikings', 'rurik', t=t)
    if a > 0:
        s0, s1 = w('vikings', 'Scandinavian'), w('vikings', 'Constantinople', end=True)
        route(cr, R.camera(t) if False else cam, VIKING, ease_io(prog(t, s0, s1)), GOLD, width=5, head='⛵', head_size=64)
        pin(cr, cam, 'uppsala', 'SCANDINAVIA', t, s0, GOLD, 'l', a=a)
        pin(cr, cam, 'constantinople', 'CONSTANTINOPLE', t, w('vikings', 'Constantinople'), GOLD, 'r', a=a)
        tv = w('vikings', 'Varangians'); qa = win('vikings', t=t) * ease_out(prog(t, tv, tv + 0.3))
        x, y = L(cam, 22, 55.5)
        ptext(cr, '"FROM THE VARANGIANS', x, y, 30, PARCH, qa, fam='Poppins ExtraBold', sw=5)
        ptext(cr, 'TO THE GREEKS"', x, y + 38, 30, PARCH, qa, fam='Poppins ExtraBold', sw=5)
    # Rurik: Novgorod on "Novgorod", crown on "Rurik"
    a = win('rurik', 'dynasty', t=t)
    if a > 0:
        pin(cr, cam, 'novgorod', 'NOVGOROD', t, w('rurik', 'Novgorod'), CRIMSON, 'r', 40, a)
        tr = w('rurik', 'Rurik')
        if t >= tr: at(cr, cam, 'novgorod', '👑', 90 * pop_k(t, tr), a, dy=-90)
    # dynasty bar fills while "rule for more than seven hundred years" is spoken
    a = win('dynasty', t=t)
    if a > 0:
        k = ease_io(prog(t, w('dynasty', 'rule'), w('dynasty', 'years', end=True)))
        x0, x1, y = 120, 960, 1180
        rrect(cr, x0, y - 26, x1 - x0, 52, 26); cr.set_source_rgba(1, 1, 1, 0.12 * a); cr.fill()
        rrect(cr, x0, y - 26, max(52, (x1 - x0) * k), 52, 26); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
        ptext(cr, '862', x0, y - 50, 40, WHITE, a, anchor='l', sw=6)
        ptext(cr, '1598', x1, y - 50, 40, WHITE, a * clamp(k * 3 - 2), anchor='r', sw=6)
        td = w('dynasty', 'dynasty')
        ptext(cr, 'RURIKID DYNASTY', 540, y + 80, 44, GOLD, a * ease_out(prog(t, td, td + 0.3)), sw=7)
        ptext(cr, f'{int(736 * k)} YEARS', 540, y + 16, 34, INK, a, sw=0, shadow=False)
    # Oleg: arrow on "sailed" arriving on "Kyiv"; the state fills on "power"; name on "Kievan"; chip on "shared"
    b = bt('oleg')
    tp = w('oleg', 'power')
    a = ease_out(prog(t, tp, tp + 0.6)) * (1 - ease_io(prog(t, w('mongols', 'Kyiv'), w('mongols', 'fell', end=True) + 0.5)))
    if a > 0: poly(cr, cam, KIEV_RUS, CRIMSON, 0.32 * a, CRIMSON, 3)
    a2 = win('oleg', t=t)
    if a2 > 0:
        route(cr, cam, [P['novgorod'], P['smolensk'], (30.8, 53.2), P['kyiv']],
              ease_io(prog(t, w('oleg', 'sailed'), w('oleg', 'Kyiv'))), WHITE, 6, arrow=True, dashed_rest=False)
        pin(cr, cam, 'kyiv', 'KYIV', t, w('oleg', 'Kyiv'), GOLD, 'r', 42, a2)
        tk = w('oleg', 'Kievan')
        if t >= tk:
            k = pop_k(t, tk); x, y = L(cam, 33, 56.2)
            cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, "KIEVAN RUS'", 0, 0, 64, WHITE, a2, sw=9); cr.restore()
        ts = w('oleg', 'shared'); k = ease_out(prog(t, ts, ts + 0.3))
        if k > 0:
            txt = 'ANCESTOR OF RUSSIA · UKRAINE · BELARUS'; wd = tw(cr, txt, 30, 'Poppins ExtraBold')
            rrect(cr, 540 - wd / 2 - 26, 1170, wd + 52, 60, 30); cr.set_source_rgba(*GOLD[:3], a2 * k); cr.fill()
            ptext(cr, txt, 540, 1211, 30, INK, a2 * k, fam='Poppins ExtraBold', sw=0, shadow=False)
    # Faith: the four options on "faith", Islam crossed on "Islam", wine + quote on "drinking"
    a = win('faith', t=t)
    if a > 0:
        tf = w('faith', 'faith')
        for i, (e, lab) in enumerate([('🕌', 'ISLAM'), ('🕍', 'JUDAISM'), ('⛪', 'CATHOLIC'), ('⛪', 'ORTHODOX')]):
            if t < tf + i * 0.15: continue
            k = pop_k(t, tf + i * 0.15); x = 165 + i * 250
            cr.save(); cr.translate(x, 760); cr.scale(k, k)
            rrect(cr, -110, -110, 220, 230, 34); cr.set_source_rgba(0.05, 0.05, 0.08, 0.85 * a); cr.fill_preserve()
            cr.set_source_rgba(*(GOLD if i == 3 else WHITE)[:3], 0.8 * a); cr.set_line_width(4); cr.stroke()
            emoji(cr, e, 0, -30, 110, a); ptext(cr, lab, 0, 85, 30, WHITE, a, fam='Poppins ExtraBold', sw=5)
            cr.restore()
        ti = w('faith', 'Islam')
        if t >= ti:
            xk = pop_k(t, ti)
            cr.save(); cr.translate(165, 760); cr.scale(xk, xk)
            cr.set_source_rgba(*CRIMSON[:3], a); cr.set_line_width(18); cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.move_to(-80, -80); cr.line_to(80, 80); cr.move_to(80, -80); cr.line_to(-80, 80); cr.stroke(); cr.restore()
        td = w('faith', 'drinking')
        if t >= td:
            emoji(cr, '🍷', 165, 920, 90 * pop_k(t, td), a, rot=0.3 * math.sin(t * 5))
            qk = ease_out(prog(t, td, td + 0.3))
            rrect(cr, 80, 1000, 920, 190, 30); cr.set_source_rgba(*PARCH[:3], 0.95 * a * qk); cr.fill()
            ptext(cr, '"DRINKING IS THE JOY', 540, 1070, 48, INK, a * qk, sw=0, shadow=False)
            ptext(cr, "OF THE RUS'\"", 540, 1128, 48, INK, a * qk, sw=0, shadow=False)
            ptext(cr, '— PRIMARY CHRONICLE', 540, 1172, 26, (0.4, 0.3, 0.2), a * qk, fam='Poppins SemiBold', sw=0, shadow=False)
    # Orthodoxy travels from Constantinople to Kyiv as it's named
    b = bt('orthodox'); a = win('orthodox', t=t)
    if a > 0:
        to = w('orthodox', 'Orthodox')
        route(cr, cam, [P['constantinople'], (30.2, 44.5), (31.5, 47), P['kyiv']],
              ease_io(prog(t, to, w('orthodox', 'Constantinople', end=True))), GOLD, 7, dashed_rest=False)
        pin(cr, cam, 'constantinople', 'CONSTANTINOPLE', t, b['start'] + 0.3, GOLD, 'r', 34, a)
        pin(cr, cam, 'kyiv', 'KYIV', t, b['start'] + 0.3, GOLD, 'r', 38, a)
        tc = w('orthodox', 'Constantinople', end=True)
        if t >= tc: at(cr, cam, 'kyiv', '⛪', 110 * pop_k(t, tc), a, dy=-100)
        if t >= to:
            k = pop_k(t, to); x, y = L(cam, 30.5, 45.6)
            cr.save(); cr.translate(x, y + 30); cr.scale(k, k); ptext(cr, 'ORTHODOX CHRISTIANITY', 0, 0, 40, GOLD, a, sw=7); cr.restore()
    # Yaroslav: Kyiv's riches on "richest"; each daughter's arc lands on her country's name
    a = win('yaroslav', t=t)
    if a > 0:
        pin(cr, cam, 'kyiv', 'KYIV', t, w('yaroslav', 'Kyiv'), GOLD, 'r', 38, a)
        tr = w('yaroslav', 'richest')
        if t >= tr: at(cr, cam, 'kyiv', '💎', 70 * pop_k(t, tr), a, dy=-70)
        for pl, lab, side, word in (('paris', 'QUEEN OF FRANCE', 'b', 'France'), ('nidaros', 'QUEEN OF NORWAY', 't', 'Norway'),
                                    ('esztergom', 'QUEEN OF HUNGARY', 'b', 'Hungary')):
            ta = w('yaroslav', word)
            mid = ((P['kyiv'][0] + P[pl][0]) / 2, (P['kyiv'][1] + P[pl][1]) / 2 + 3)
            route(cr, cam, [P['kyiv'], mid, P[pl]], ease_io(prog(t, ta - 0.6, ta)), hexc('#FF7AB6'), 4, dashed_rest=False, arrow=True)
            pin(cr, cam, pl, lab, t, ta, hexc('#FF7AB6'), side, 28, a)
            if t >= ta: at(cr, cam, pl, '👑', 60 * pop_k(t, ta), a, dy=-60 if side == 'b' else 70)
    # Split: swords on "fought", cracks on "split", Moscow on "Moscow"
    a = win('split', t=t)
    if a > 0:
        tsp = w('split', 'split')
        for i, ln in enumerate(SPLITS):
            k = ease_out(prog(t, tsp + i * 0.12, tsp + 0.5 + i * 0.12))
            if k <= 0: continue
            X, Y = L(cam, [p[0] for p in ln], [p[1] for p in ln]); n = max(2, int(len(X) * k + 1))
            jag = np.array([(x + 6 * math.sin(j * 7.3), y + 6 * math.cos(j * 5.1)) for j, (x, y) in enumerate(zip(X, Y))])
            cr.new_path(); cr.move_to(*jag[0]); [cr.line_to(*q) for q in jag[1:n]]
            cr.set_source_rgba(1, 1, 1, 0.9 * a); cr.set_line_width(5); cr.stroke()
        tf = w('split', 'fought')
        for i, (lon, lat) in enumerate(((28, 53), (34, 57), (39, 55), (30.5, 51.5))):
            if t >= tf + i * 0.12: at(cr, cam, (lon, lat), '⚔️', 60 * pop_k(t, tf + i * 0.12), a, rot=0.2 * math.sin(t * 4 + i))
        tm = w('split', 'Moscow')
        pin(cr, cam, 'moscow', 'MOSCOW', t, tm, GOLD, 'r', 46, a)
        tfi = w('split', 'first'); k = ease_out(prog(t, tfi, tfi + 0.3))
        if k > 0:
            x, y = L(cam, *P['moscow']); ptext(cr, 'first mentioned · 1147', x + 26, y + 52, 28, PARCH, a * k, fam='Poppins SemiBold', anchor='l', sw=5)
    # Mongols: each city burns as the narrator says it
    a = win('mongols', t=t)
    if a > 0:
        hits = [('ryazan', (52, 54.5), w('mongols', 'burned')), ('vladimir', (50, 57), w('mongols', 'city', 0)),
                ('moscow', (44, 56.5), w('mongols', 'city', 1)), ('kyiv', (40, 49.5), w('mongols', 'fell'))]
        for i, (pl, src, ta) in enumerate(hits):
            t0 = ta - (1.0 if pl != 'kyiv' else ta - w('mongols', '1240'))
            route(cr, cam, [src, ((src[0] + P[pl][0]) / 2, (src[1] + P[pl][1]) / 2 + 0.6), P[pl]], ease_io(prog(t, t0, ta)),
                  AMBER, 9, head='🐎', head_size=60, dashed_rest=False, arrow=True)
            if t >= ta:
                at(cr, cam, pl, '🔥', 80 * pop_k(t, ta) * (1 + 0.08 * math.sin(t * 12 + i)), a, dy=-30)
                pin(cr, cam, pl, pl.upper(), t, ta, AMBER, 'b' if pl != 'vladimir' else 't', 30, a)
    # Golden Horde spreads on "Golden"; tribute flows on "tribute"
    tg = w('horde', 'Golden')
    a = ease_out(prog(t, tg - 0.4, tg + 0.3)) * (1 - ease_io(prog(t, w('free', 'free'), w('free', 'free', end=True) + 0.4)))
    if a > 0:
        poly(cr, cam, HORDE, AMBER, 0.32 * a, AMBER, 4)
        x, y = L(cam, 62, 48); ptext(cr, 'GOLDEN HORDE', x, y, 56 if cam[2] < 0.25 else 44, AMBER, a, sw=8)
        pin(cr, cam, 'sarai', 'SARAI', t, tg + 0.4, AMBER, 'b', 30, a)
    a2 = win('horde', t=t)
    if a2 > 0:
        tp = w('horde', 'princes')
        poly(cr, cam, KIEV_RUS, CRIMSON, 0.22 * a2 * ease_out(prog(t, tp - 0.2, tp + 0.2)), CRIMSON, 2, dash=[8, 8])
        x, y = L(cam, 34, 57); ptext(cr, "RUS' PRINCES", x, y, 34, WHITE, a2 * ease_out(prog(t, tp, tp + 0.3)), fam='Poppins ExtraBold', sw=6)
        tt = w('horde', 'tribute')
        if t >= tt:
            k = pop_k(t, tt)
            cr.save(); cr.translate(540, 1180); cr.scale(k, k)
            txt = 'TRIBUTE FOR ~240 YEARS'; wd = tw(cr, txt, 44)
            rrect(cr, -wd / 2 - 30, -56, wd + 60, 86, 43); cr.set_source_rgba(*AMBER[:3], a2); cr.fill()
            ptext(cr, txt, 0, 2, 44, INK, a2, sw=0, shadow=False); cr.restore()
            for i in range(8):
                u = ((t - tt) * 0.6 + i / 8) % 1.0
                if (t - tt) * 0.6 < i / 8: continue
                x0, y0 = L(cam, 36, 55); x1, y1 = L(cam, *P['sarai'])
                emoji(cr, '🪙', lerp(x0, x1, u), lerp(y0, y1, u) - 60 * math.sin(math.pi * u), 40, a2 * math.sin(math.pi * u))
    # Battle on the Ice: armies close on "crushed", clash on "frozen", title on "Battle"
    a = win('nevsky', t=t)
    if a > 0:
        tc, tf = w('nevsky', 'crushed'), w('nevsky', 'frozen')
        route(cr, cam, [(25.6, 58.35), (26.5, 58.55), (27.3, 58.63)], ease_io(prog(t, tc - 0.3, tf)), hexc('#9AA4B5'), 9, dashed_rest=False, arrow=True)
        route(cr, cam, [(29.6, 58.8), (28.7, 58.74), (27.8, 58.68)], ease_io(prog(t, tc - 0.3, tf)), CRIMSON, 9, dashed_rest=False, arrow=True)
        tt = w('nevsky', 'Teutonic')
        x, y = L(cam, 25.8, 58.3); ptext(cr, 'TEUTONIC KNIGHTS', x, y + 110, 30, WHITE, a * ease_out(prog(t, tt, tt + 0.3)), fam='Poppins ExtraBold', sw=5)
        tn = w('nevsky', 'Nevsky')
        x, y = L(cam, 29.4, 58.85); ptext(cr, 'NOVGOROD ARMY', x, y - 90, 30, WHITE, a * ease_out(prog(t, tn, tn + 0.3)), fam='Poppins ExtraBold', sw=5)
        if t >= tf:
            at(cr, cam, (27.55, 58.66), '⚔️', 110 * pop_k(t, tf), a, rot=0.15 * math.sin(t * 6))
            at(cr, cam, (26.3, 59.25), '❄️', 70 * pop_k(t, tf + 0.1), a * 0.9, rot=t * 0.5)
            rng = np.random.default_rng(1); x, y = L(cam, 27.55, 58.66)
            for j in range(9):
                ang = rng.uniform(0, 2 * math.pi); ln = rng.uniform(60, 200) * ease_out(prog(t, tf, tf + 0.9))
                cr.new_path(); cr.move_to(x, y); cr.line_to(x + math.cos(ang) * ln * 0.5 + 10, y + math.sin(ang) * ln * 0.5 - 8)
                cr.line_to(x + math.cos(ang) * ln, y + math.sin(ang) * ln); cr.set_source_rgba(*ICE[:3], a); cr.set_line_width(3); cr.stroke()
        tb = w('nevsky', 'Battle')
        ptext(cr, '1242 · BATTLE ON THE ICE', 540, 1190, 42, ICE, a * ease_out(prog(t, tb, tb + 0.3)), sw=7)
    # Kalita: Moscow on "Moscow", nickname on "Moneybag", taxes on "collected", tribute south on "Khans", bag on "rich"
    a = win('kalita', t=t)
    if a > 0:
        tm = w('kalita', 'Moscow')
        poly(cr, cam, MOSCOW_1300, GOLD, 0.45 * a * ease_out(prog(t, tm, tm + 0.6)), GOLD, 3)
        pin(cr, cam, 'moscow', 'MOSCOW', t, tm, GOLD, 'r', 40, a)
        tmb = w('kalita', 'Moneybag')
        if t >= tmb:
            k = pop_k(t, tmb); x, y = L(cam, *P['moscow'])
            cr.save(); cr.translate(x - 30, y - 150); cr.rotate(-0.08); cr.scale(k, k)
            ptext(cr, '"MONEYBAG"', 0, 0, 52, GOLD, a, sw=8); cr.restore()
        tco, tkh = w('kalita', 'collected'), w('kalita', 'Khans')
        pin(cr, cam, 'sarai', 'SARAI', t, tkh, AMBER, 'r', 34, a)
        for i, pl in enumerate(('novgorod', 'tver', 'rostov', 'vladimir', 'ryazan', 'smolensk')):
            pin(cr, cam, pl, None, t, tco + i * 0.08, WHITE, a=a)
            if t < tco: continue
            for j in range(3):
                if (t - tco) * 0.7 < j / 3: continue
                u = ((t - tco) * 0.7 + j / 3 + i * 0.11) % 1.0
                x0, y0 = L(cam, *P[pl]); x1, y1 = L(cam, *P['moscow'])
                emoji(cr, '🪙', lerp(x0, x1, u), lerp(y0, y1, u), 36, a * math.sin(math.pi * u))
        if t > tkh:
            for j in range(5):
                if (t - tkh) * 0.5 < j / 5: continue
                u = ((t - tkh) * 0.5 + j / 5) % 1.0; x0, y0 = L(cam, *P['moscow']); x1, y1 = L(cam, *P['sarai'])
                emoji(cr, '💰', lerp(x0, x1, u) + 60 * math.sin(math.pi * u), lerp(y0, y1, u), 46, a * math.sin(math.pi * u))
        tr = w('kalita', 'rich')
        if t >= tr: at(cr, cam, 'moscow', '💰', 90 * pop_k(t, tr) * (1 + 0.1 * math.sin(t * 6)), a, dy=-90)
    # Kulikovo: armies meet on "defeated", title on "Kulikovo"
    b = bt('kulikovo'); a = win('kulikovo', t=t)
    if a > 0:
        td, tk = w('kulikovo', 'defeated'), w('kulikovo', 'Kulikovo')
        route(cr, cam, [P['moscow'], (38.0, 54.8), (38.55, 53.8)], ease_io(prog(t, w('kulikovo', 'Dmitry'), td)), CRIMSON, 9, dashed_rest=False, arrow=True)
        route(cr, cam, [(40.2, 52.3), (39.4, 52.9), (38.8, 53.5)], ease_io(prog(t, w('kulikovo', 'Dmitry'), td)), AMBER, 9, dashed_rest=False, arrow=True)
        pin(cr, cam, 'moscow', 'MOSCOW', t, b['start'] + 0.3, GOLD, 'r', 36, a)
        if t >= td: at(cr, cam, 'kulikovo', '⚔️', 120 * pop_k(t, td), a, rot=0.15 * math.sin(t * 6))
        ptext(cr, '1380 · KULIKOVO FIELD', 540, 1190, 44, GOLD, a * ease_out(prog(t, tk, tk + 0.3)), sw=7)
        tf = w('kulikovo', 'Field', end=True)
        if t >= tf: at(cr, cam, 'kulikovo', '🏆', 70 * pop_k(t, tf), a, dy=-110)
    # Ugra: river on "Ugra", armies face off on "faced", the Horde pulls back on "retreated"
    a = win('ugra', t=t)
    if a > 0:
        tu = w('ugra', 'Ugra')
        X, Y = L(cam, [p[0] for p in UGRA], [p[1] for p in UGRA])
        n = max(2, int(len(X) * ease_out(prog(t, tu - 0.3, tu + 0.5)) + 1))
        cr.new_path(); cr.move_to(X[0], Y[0]); [cr.line_to(x, y) for x, y in zip(X[1:n], Y[1:n])]
        cr.set_source_rgba(*RIVER[:3], 0.4 * a); cr.set_line_width(26); cr.stroke_preserve()
        cr.set_source_rgba(*RIVER[:3], a); cr.set_line_width(8); cr.stroke()
        x, y = L(cam, 35.3, 54.62); ptext(cr, 'UGRA RIVER', x, y + 70, 34, RIVER, a * ease_out(prog(t, tu, tu + 0.3)), fam='Poppins ExtraBold', sw=6)
        tfc, tre = w('ugra', 'faced'), w('ugra', 'retreated')
        retreat = ease_io(prog(t, tre, tre + 1.6))
        if t >= tfc:
            ka = pop_k(t, tfc)
            for i in range(5):
                x, y = L(cam, 34.3 + i * 0.5, 54.8); emoji(cr, '🛡️', x, y - 40, 70 * ka, a)
                x, y = L(cam, 34.3 + i * 0.5, 54.42 - retreat * 0.3); emoji(cr, '🐎', x, y + 40, 70 * ka, a * (1 - retreat * 0.7))
            x, y = L(cam, 35.3, 55.05); ptext(cr, 'MOSCOW', x, y - 40, 36, CRIMSON, a * min(1, ka), sw=6)
            x, y = L(cam, 34.05, 54.42 - retreat * 0.3)
            ptext(cr, 'THE HORDE', x - 50, y + 50, 36, AMBER, a * min(1, ka) * (1 - retreat * 0.6), anchor='r', sw=6)
        tw_ = w('ugra', 'without')
        ptext(cr, 'THE GREAT STAND · 1480', 540, 1190, 44, GOLD, a * ease_out(prog(t, tw_, tw_ + 0.3)), sw=7)
    # Free: duchy on "Moscow", 240 on "forty", stamp on "free"
    b = bt('free')
    if t >= b['start']:
        a = win('free', t=t) if t < b['end'] else 1 - ease_io(prog(t, b['end'] - 0.2, bt('cliff')['l0'] + 1))
        if a > 0:
            tm = w('free', 'Moscow')
            poly(cr, cam, MUSCOVY_1480, CRIMSON, 0.4 * a * ease_out(prog(t, b['start'] + 0.3, tm)), WHITE, 3)
            x, y = L(cam, 42, 60.5); ptext(cr, 'GRAND DUCHY OF MOSCOW', x, y, 40, WHITE, a * ease_out(prog(t, tm, tm + 0.3)), sw=7)
            tfy = w('free', 'forty')
            if t >= tfy and t < b['end']:
                k = pop_k(t, tfy); cr.save(); cr.translate(540, 470); cr.scale(k, k)
                ptext(cr, '240 YEARS', 0, 0, 70, AMBER, a, sw=9); cr.restore()
            tf = w('free', 'free')
            k = prog(t, tf - 0.1, tf + 0.2)
            if k > 0:
                s = lerp(2.4, 1.0, ease_out(k)); sh = 10 * math.sin(t * 70) * (1 - prog(t, tf + 0.2, tf + 0.6))
                cr.save(); cr.translate(540 + sh, 1180); cr.rotate(-0.08); cr.scale(s, s)
                wd = tw(cr, 'FREE', 120); rrect(cr, -wd / 2 - 40, -110, wd + 80, 150, 22)
                cr.set_source_rgba(*CRIMSON[:3], a * clamp(k * 3)); cr.set_line_width(10); cr.stroke()
                ptext(cr, 'FREE', 0, 0, 120, CRIMSON, a * clamp(k * 3), sw=10); cr.restore()

# ---------- hook ----------
ANCHOR = {}  # hook beat -> (scene time to replay from)

def hook_tv(b, t): return ANCHOR[b['key']] + (t - b['start'])

def draw_hook(cr, t):
    if t >= bt('today')['start']: return False
    b = next((x for x in TL['beats'] if x['key'] in HOOK and x['start'] <= t < x['end'] + 1e-6), bt('h1'))
    if b is None: return False
    tv = hook_tv(b, t)
    cx, cy, s = R.camera(tv)
    s *= 1.0 + 0.18 * (1 - ease_out(prog(t, b['start'], b['start'] + 0.7))) + 0.04 * prog(t, b['start'], b['end'])
    cam = (cx, cy, s)
    R.draw_map(cr, tv, cam)
    draw_story(cr, tv, cam)
    # legibility gradient behind the hook text
    g = cairo.LinearGradient(0, 0, 0, 900)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.8); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    cr.set_source(g); cr.paint()
    rows = {
        'h1': [('biggest', 'THE BIGGEST COUNTRY ON EARTH', 50, WHITE, 250, None), ('began', 'BEGAN WITH A', 70, WHITE, 390, None),
               ('Viking', 'VIKING', 200, GOLD, 640, '⛵')],
        'h2': [('cities', 'ITS CITIES WERE', 70, WHITE, 270, None), ('burned', 'BURNED', 210, CRIMSON, 540, '🔥'),
               ('Mongols', 'BY THE MONGOLS', 84, AMBER, 740, None)],
        'h3': [('rose', 'AND ROSE AGAIN FROM', 60, WHITE, 250, None), ('tiny', 'A TINY TOWN', 84, WHITE, 390, None),
               ('Moscow', 'MOSCOW', 210, GOLD, 640, '👑')],
    }[b['key']]
    for word, txt, size, col, y, em in rows:
        tw0 = w(b['key'], word)
        if t < tw0: continue
        k = ease_back(prog(t, tw0, tw0 + 0.25), 3)
        big = size > 150
        sh = (12 * math.sin(t * 70) * (1 - prog(t, tw0 + 0.2, tw0 + 0.5))) if big else 0
        cr.save(); cr.translate(540 + sh, y); cr.rotate(-0.05 if big else 0)
        sc = (lerp(2.2, 1.0, ease_out(prog(t, tw0, tw0 + 0.25))) if big else max(1e-3, k)) * (1 + (0.03 * math.sin(t * 6) if big else 0))
        cr.scale(sc, sc)
        ptext(cr, txt, 0, 0, fit(cr, txt, size, 880 if big else 1000), col, clamp(prog(t, tw0, tw0 + 0.12) * 1.5), sw=size * 0.12)
        cr.restore()
        if em and b['key'] == 'h2':
            for ex, d in ((95, 0.1), (985, 0.2)):
                emoji(cr, '🔥', ex, y + 95, 110 * pop_k(t, tw0 + d), 1, rot=0.2 * math.sin(t * 7 + ex))
        elif em:
            emoji(cr, em, 540, y + 150, 130 * pop_k(t, tw0 + 0.1), 1, rot=0.25 * math.sin(t * 6))
        if big:
            fl = 1 - prog(t, tw0, tw0 + 0.25)
            if 0 < fl < 1: cr.set_source_rgba(1, 1, 1, 0.22 * fl); cr.paint()
    fl = 1 - prog(t, b['start'], b['start'] + 0.18)  # hard flash cut into each shot
    if b['key'] != 'h1' and 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.55 * fl); cr.paint()
    return True

def draw_today(cr, t):
    b, p = bt('today'), bt('past')
    if not (b['start'] <= t < p['end']): return
    if t < b['end']:
        a = 1 - ease_io(prog(t, b['end'] - 0.2, b['end']))
        te = w('today', 'eleven')
        if t >= te:
            k = pop_k(t, te); cr.save(); cr.translate(540, 1200); cr.scale(k, k)
            txt = '11 TIME ZONES'; wd = tw(cr, txt, 76)
            rrect(cr, -wd / 2 - 44, -80, wd + 88, 118, 59); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
            ptext(cr, txt, 0, 4, 76, INK, a, sw=0, shadow=False); cr.restore()
    if t >= p['start']:
        td = w('past', 'didn')
        a2 = 1 - ease_io(prog(t, p['end'] - 0.3, p['end']))
        if t >= td:
            k = prog(t, td, td + 0.25); s = lerp(2.2, 1.0, ease_out(k)); sh = 12 * math.sin(t * 70) * (1 - prog(t, td + 0.25, td + 0.6))
            cr.save(); cr.translate(540 + sh, 1220); cr.rotate(-0.05); cr.scale(s, s)
            ptext(cr, "IT DIDN'T EXIST", 0, 0, 104, CRIMSON, a2 * clamp(k * 3), sw=13); cr.restore()
    fl = 1 - prog(t, b['start'], b['start'] + 0.18)
    if 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.55 * fl); cr.paint()

# ---------- medallion cards, on the spoken name ----------
def draw_card(cr, t):
    for b in TL['beats']:
        if not b['card']: continue
        t0 = w(b['key'], b['cword']); t1 = b['end']
        if not (t0 <= t <= t1): continue
        e, name, sub = b['card']
        k = ease_out(prog(t, t0, t0 + 0.35)); out = 1 - ease_io(prog(t, t1 - 0.35, t1))
        a = k * out; x = lerp(-500, 0, k)
        cr.save(); cr.translate(x, 0)
        rrect(cr, 50, 1300, 980, 170, 85); cr.set_source_rgba(0.05, 0.04, 0.07, 0.9 * a); cr.fill_preserve()
        cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
        cr.new_path(); cr.arc(135, 1385, 70, 0, 2 * math.pi)
        g = cairo.RadialGradient(115, 1360, 10, 135, 1385, 70); g.add_color_stop_rgba(0, *GOLD[:3], a); g.add_color_stop_rgba(1, 0.55, 0.38, 0.1, a)
        cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(4); cr.stroke()
        emoji(cr, e, 135, 1380, 84 * ease_back(prog(t, t0 + 0.1, t0 + 0.45), 3), a)
        ptext(cr, name, 230, 1385, fit(cr, name, 58, 760), WHITE, a, anchor='l', sw=8)
        ptext(cr, sub, 232, 1435, fit(cr, sub, 32, 760, 'Poppins SemiBold'), PARCH, a, fam='Poppins SemiBold', anchor='l', sw=5)
        cr.restore()

# ---------- cliffhanger, on the spoken words ----------
def draw_cliff(cr, t, cam):
    b, n = bt('cliff'), bt('next')
    if t < b['start']: return
    a = ease_out(prog(t, b['start'], b['l0'] + 1.0))
    g = cairo.RadialGradient(W / 2, MAPY, 100, W / 2, MAPY, 1100)
    g.add_color_stop_rgba(0, 0.5, 0.0, 0.05, 0.25 * a); g.add_color_stop_rgba(1, 0.05, 0, 0, 0.85 * a)
    cr.set_source(g); cr.paint()
    pin(cr, cam, 'moscow', 'MOSCOW', t, b['l0'], CRIMSON, 'r', 44, 1 - ease_io(prog(t, n['l0'], n['l0'] + 0.4)))
    tg, tf = w('cliff', 'grandson'), w('cliff', 'feared')
    fade = 1 - ease_io(prog(t, n['start'], n['l0']))
    if t >= tg:
        k = pop_k(t, tg); cr.save(); cr.translate(540, 520); cr.scale(k, k)
        ptext(cr, "IVAN'S GRANDSON...", 0, 0, 64, WHITE, fade, sw=9); cr.restore()
    if t >= tf:
        k = pop_k(t, tf); cr.save(); cr.translate(540, 1220); cr.rotate(-0.04); cr.scale(k, k)
        ptext(cr, 'THE MOST FEARED', 0, 0, 84, CRIMSON, fade, sw=11); cr.restore()
    ti, tt = w('next', 'Ivan'), w('next', 'Terrible')
    if t >= ti:
        k = prog(t, ti, ti + 0.3); s = lerp(3.0, 1.0, ease_out(k)); sh = 14 * math.sin(t * 60) * (1 - prog(t, ti + 0.3, ti + 0.8))
        cr.save(); cr.translate(540 + sh, 760); cr.scale(s, s); ptext(cr, 'IVAN', 0, 0, 200, CRIMSON, clamp(k * 3), sw=18); cr.restore()
        fl = 1 - prog(t, ti + 0.25, ti + 0.7)
        if 0 < fl < 1: cr.set_source_rgba(0.8, 0, 0, 0.35 * fl); cr.paint()
    if t >= tt:
        k = prog(t, tt, tt + 0.3); s = lerp(2.4, 1.0, ease_out(k))
        cr.save(); cr.translate(540, 930); cr.scale(s, s)
        ptext(cr, 'THE TERRIBLE', 0, 0, fit(cr, 'THE TERRIBLE', 140, 1000), WHITE, clamp(k * 3), sw=14); cr.restore()
    tp = w('next', 'Part')
    if t >= tp:
        k = pop_k(t, tp); cr.save(); cr.translate(540, 1110); cr.scale(k, k)
        wd = tw(cr, 'PART 02', 70); rrect(cr, -wd / 2 - 40, -66, wd + 80, 100, 50); cr.set_source_rgba(*GOLD[:3], 1); cr.fill()
        ptext(cr, 'PART 02', 0, 8, 70, INK, 1, sw=0, shadow=False); cr.restore()
    tfo = w('next', 'Follow')
    if t >= tfo:
        k = pop_k(t, tfo) * (1 + 0.04 * math.sin(t * 6))
        cr.save(); cr.translate(540, 1300); cr.scale(k, k)
        wd = tw(cr, 'FOLLOW FOR PART 02', 52); rrect(cr, -wd / 2 - 90, -60, wd + 180, 94, 47); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, 'FOLLOW FOR PART 02', 30, 4, 52, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 64, 1, rot=0.3 * math.sin(t * 9))
        cr.restore()

# ---------- captions from the real word timings ----------
def caption_groups(b):
    words, src, toks = b['words'], list(b['tokens']), []
    for _, _, x in words:  # the voice may speak several written tokens as one unit ("In 1147")
        n = len(x.split()); toks.append(' '.join(src[:n])); src = src[n:]
    if src or len(toks) != len(words): toks = [x for _, _, x in words]
    groups, cur = [], []
    for i, (tok, (s, e, _)) in enumerate(zip(toks, words)):
        cur.append((s, e, tok))
        if len(cur) == 3 or re.search(r"[.,!?:;…]$", tok) or tok.endswith('...'):
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    return groups

def draw_captions(cr, t):
    for b in TL['beats']:
        if not (b['l0'] - 0.05 <= t < b['l1'] + 0.3): continue
        groups = b.setdefault('_groups', caption_groups(b))
        g = None
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
            hot = any(ch.isdigit() for ch in u) or norm(u) in ('russia', 'rurik', 'kyiv', 'moscow', 'mongols', 'viking', 'varangians',
                                                                 'novgorod', 'orthodox', 'horde', 'terrible', 'free', 'burned')
            col = GOLD if j == cur else (hexc('#FFCF70') if hot else WHITE)
            ptext(cr, u, 0, 0, size, col, 1.0 if j <= cur else 0.6, sw=10)
            cr.restore(); x += wd + space
        cr.restore(); return

# ---------- frame ----------
def render_frame(cr, t):
    if draw_hook(cr, t):
        draw_captions(cr, t)
        return
    cam = R.camera(t)
    R.draw_map(cr, t, cam)
    draw_story(cr, t, cam)
    draw_today(cr, t)
    draw_cliff(cr, t, cam)
    draw_year(cr, t)
    R.draw_chapter_label(cr, t)
    draw_card(cr, t)
    R.draw_timeline(cr, t)
    R.draw_footnote(cr, t)
    R.draw_title(cr, t)
    R.draw_chapter_card(cr, t)
    draw_captions(cr, t)
    f = prog(t, TL['dur'] - 0.5, TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()

# ---------- score ----------
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); tt = np.arange(n) / SR
    rng = np.random.default_rng(21)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n)
    chords = [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 49, 52]]
    bar = 60 / 84 * 4
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(bar * 1.3 * SR)) / SR
        env = np.minimum(1, L_ / 0.8) * np.exp(-L_ * 0.45); vib = 1 + 0.003 * np.sin(2 * np.pi * 5 * L_)
        put(music, ci * bar, sum(0.035 * (np.sin(2 * np.pi * note(m) * vib * L_) + 0.5 * np.sin(2 * np.pi * note(m + 12) * 1.002 * L_)) for m in ch) * env)
        put(music, ci * bar, 0.12 * np.sin(2 * np.pi * note(ch[0] - 24) * L_) * env)
    beat = 60 / 84
    hook_end = bt('today')['start']
    for bi in range(int(dur / beat)):
        t0 = bi * beat
        if t0 > bt('cliff')['start'] or (hook_end <= t0 < bt('forest')['start']): continue
        if bi % 2 == 0 or bi % 8 == 7 or t0 < hook_end:
            L_ = np.arange(int(0.6 * SR)) / SR
            put(music, t0, 0.5 * np.sin(2 * np.pi * np.cumsum(60 + 50 * np.exp(-L_ * 18)) / SR) * np.exp(-L_ * 6))
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
    def ticks(t0, t1):
        for k in range(int((t1 - t0) / 0.06)):
            L_ = np.arange(int(0.03 * SR)) / SR; put(fx, t0 + k * 0.06, 0.08 * np.sin(2 * np.pi * 1800 * L_) * np.exp(-L_ * 90))
    # hook: a hit on every punch word, a cut whoosh into every shot
    for key, word in (('h1', 'Viking'), ('h2', 'burned'), ('h3', 'Moscow')):
        boom(w(key, word), 0.85)
        if key != 'h1': whoosh(bt(key)['start'] - 0.25, 0.25)
    whoosh(bt('today')['start'] - 0.25, 0.25); boom(bt('today')['start'], 0.5)
    ticks(w('past', 'twelve'), w('past', 'ago', end=True) + 0.2); boom(w('past', 'didn'), 0.8)
    boom(bt('title')['start'] + 0.4, 0.9)
    for b in T['beats']:
        if b['key'] in HOOK or b['key'] in ('today', 'past'): continue
        whoosh(b['start'] - 0.2, 0.12)
        if b['chap']: boom(b['start'] + 0.15, 0.6)
    for key, word in (('mongols', 'burned'), ('mongols', 'fell'), ('nevsky', 'frozen'), ('kulikovo', 'defeated'),
                      ('free', 'free'), ('next', 'Ivan')):
        boom(w(key, word), 0.6 if key != 'next' else 1.0)
    mg0, mg1 = w('mongols', 'Mongols'), w('mongols', 'fell', end=True)
    for k in range(int((mg1 - mg0) / 0.18)):
        L_ = np.arange(int(0.08 * SR)) / SR; put(fx, mg0 + k * 0.18 + (0.05 if k % 2 else 0), 0.12 * np.sin(2 * np.pi * 90 * L_) * np.exp(-L_ * 40))
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
    R.year_at = year_at
    TL['yev'] = year_events()
    ANCHOR['h1'] = w('vikings', 'Varangians')
    ANCHOR['h2'] = w('mongols', 'burned') - 0.5
    ANCHOR['h3'] = w('kalita', 'collected') - 0.2

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
    for b in TL['beats']: print(f"  {b['key']:9s} {b['start']:6.2f}-{b['end']:6.2f}  words {len(b['words'])}/{len(b['tokens'])}")
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
