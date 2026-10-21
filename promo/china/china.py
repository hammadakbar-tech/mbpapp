"""'The Entire History of China' (9:16). A fast cold-open hook (terracotta army, the Great Wall, the inventions, a dynasty
montage) and then a map documentary from the Shang to today: real dynasty extents (historical-basemaps), seal-stamp dynasty
plates, routes, character cards, a dynasty timeline, and karaoke captions synced to the narrator's actual words.
Usage: python3 china.py <data_dir> <out.mp4> [--preview t1,t2,...]
"""
import asyncio, hashlib, json, math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import russia as R
R.LON0, R.LAT0 = 104.0, 34.0
R.MAPY = MAPY = 960
from russia import (GOLD, CRIMSON, WHITE, AMBER, ICE, PARCH, INK, RIVER, W, H, FPS, ptext, rrect, tw, fit, face, emoji, pop_k,
                    route, path_xy, laea, S, L)
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

VOICE, RATE = 'en-GB-RyanNeural', '+8%'
CJK = 'WenQuanYi Zen Hei'
JADE, BRICK, TERRA = hexc('#3FA36B'), hexc('#B5523B'), hexc('#C7744E')
OVER = (104, 35.5, 0.19)

# dynasty: (seal character, name, years, colour)
DYN = {
    'shang': ('商', 'SHANG DYNASTY', 'c. 1600–1046 BC', hexc('#C98A3A')), 'zhou': ('周', 'ZHOU DYNASTY', '1046–256 BC', JADE),
    'qin': ('秦', 'QIN DYNASTY', '221–206 BC', hexc('#8A5BE0')), 'han': ('汉', 'HAN DYNASTY', '202 BC – 220 AD', CRIMSON),
    'jin': ('晋', 'AGE OF DIVISION', '220–589', hexc('#5A7BA8')), 'sui': ('隋', 'SUI DYNASTY', '581–618', hexc('#2E9CCA')),
    'tang': ('唐', 'TANG DYNASTY', '618–907', GOLD), 'song': ('宋', 'SONG DYNASTY', '960–1279', hexc('#2FB89A')),
    'yuan': ('元', 'YUAN DYNASTY', '1271–1368', hexc('#4A6FE3')), 'ming': ('明', 'MING DYNASTY', '1368–1644', hexc('#E8602C')),
    'qing': ('清', 'QING DYNASTY', '1644–1912', hexc('#F2C94C')), 'roc': ('民', 'REPUBLIC OF CHINA', '1912–1949', hexc('#3A7BD5')),
    'prc': ('中', "PEOPLE'S REPUBLIC", '1949–today', CRIMSON),
}
ORDER = ['shang', 'zhou', 'qin', 'han', 'jin', 'sui', 'tang', 'song', 'yuan', 'ming', 'qing', 'roc', 'prc']
STARTS = [-1600, -1046, -221, -202, 220, 581, 618, 960, 1271, 1368, 1644, 1912, 1949]

# key, narration, year, word that flips the year, camera (lon, lat, px per km), chapter card, character card (emoji, name, sub, word)
BEATS = [
    ('h1', "An emperor, buried with eight thousand clay soldiers.", None, None, OVER, None, None),
    ('h2', "A wall, over twenty thousand kilometres long.", None, None, OVER, None, None),
    ('h3', "Paper. Gunpowder. The compass.", None, None, OVER, None, None),
    ('h4', "And a civilisation that has lasted more than three thousand years.", None, None, OVER, None, None),
    ('title', "This is the entire history of China.", None, None, OVER, None, None),
    ('shang', "Around 1600 BC, the Shang dynasty rose along the Yellow River. They carved the oldest known Chinese writing onto bones, to ask their ancestors about the future.",
     -1600, '1600', (113, 35.4, 0.40), ('I', 'THE FIRST DYNASTIES'), None),
    ('zhou', "Then the Zhou took over, claiming the Mandate of Heaven: heaven picks who rules... and can take that power away.",
     -1046, 'Zhou', (113.5, 34.8, 0.33), None, None),
    ('confucius', "As the Zhou weakened, rival states went to war. In the chaos, a teacher named Confucius taught respect, duty and family.",
     -500, 'Confucius', (114, 34.5, 0.33), None, ('📜', 'CONFUCIUS', 'Teacher and philosopher · 551–479 BC', 'Confucius')),
    ('qin', "In 221 BC, the king of Qin crushed every rival, and named himself the First Emperor: Qin Shi Huang.",
     -221, '221', (111.5, 34.6, 0.30), ('II', 'THE FIRST EMPEROR'), ('👑', 'QIN SHI HUANG', 'First Emperor · r. 221–210 BC', 'Shi')),
    ('qin2', "He standardised writing, money and measurements, linked up walls in the north... and was buried with an army of clay soldiers.",
     None, None, (110, 37.5, 0.22), None, None),
    ('han', "His dynasty collapsed just four years after he died. The Han that followed ruled for four centuries, and opened the Silk Road. Even today, most Chinese people call themselves Han.",
     -202, 'Han', (95, 37, 0.15), None, None),
    ('split', "When the Han fell, China split apart for almost four hundred years.",
     220, 'fell', (111, 33.5, 0.24), ('III', 'GOLDEN AGES'), None),
    ('sui', "The Sui reunited it, and dug the Grand Canal, still the longest canal on Earth.",
     589, 'Sui', (115.5, 34, 0.30), None, None),
    ('tang', "Then came the Tang: a golden age, with a capital that was one of the biggest cities in the world.",
     618, 'Tang', (106, 34.5, 0.21), None, None),
    ('song', "Under the Song, China printed with movable type, used paper money and the compass, and built the first gunpowder weapons.",
     960, 'Song', (112, 33, 0.25), None, None),
    ('yuan', "Then the Mongols came. By 1279, Kublai Khan, grandson of Genghis, ruled all of China.",
     1279, '1279', (108, 40, 0.13), ('IV', 'CONQUERORS & EMPERORS'), ('🏹', 'KUBLAI KHAN', 'Yuan emperor · r. 1260–1294', 'Kublai')),
    ('ming', "In 1368, a former peasant drove them out and founded the Ming, who built the Forbidden City, and most of the Great Wall you see today.",
     1368, '1368', (112, 36.5, 0.24), None, None),
    ('zheng', "Admiral Zheng He sailed giant treasure fleets as far as Africa, decades before Columbus.",
     1405, 'Zheng', (79, 12, 0.088), None, ('⛵', 'ZHENG HE', 'Admiral · seven voyages, 1405–1433', 'Zheng')),
    ('qing', "In 1644, the Manchus swept in and founded the Qing: China's last dynasty, and one of the largest empires on Earth.",
     1644, '1644', (100, 40, 0.15), None, None),
    ('opium', "But in the 1800s, Britain defeated China in the Opium Wars, starting what China calls the Century of Humiliation.",
     1839, 'Opium', (114.5, 26, 0.32), ('V', 'THE MODERN AGE'), None),
    ('puyi', "In 1912, the last emperor, six-year-old Puyi, gave up the throne. Two thousand years of emperors were over.",
     1912, '1912', (108, 35, 0.2), None, ('👑', 'PUYI', 'The Last Emperor · abdicated aged 6', 'Puyi')),
    ('war', "Then came civil war, and a brutal Japanese invasion.", 1937, 'Japanese', (114, 35, 0.2), None, None),
    ('prc', "In 1949, Mao Zedong's Communists won, and founded the People's Republic. Their rivals fled to Taiwan.",
     1949, '1949', (110, 32, 0.19), None, ('⭐', 'MAO ZEDONG', 'Founder of the PRC · 1893–1976', 'Mao')),
    ('today', "Today, China has over 1.4 billion people, and the world's second biggest economy.", 'TODAY', None, OVER, None, None),
    ('moon', "From writing on bones... to the far side of the Moon.", 'TODAY', None, OVER, None, None),
    ('cta', "Which dynasty was the greatest? Tell us in the comments, and follow for more.", 'TODAY', None, OVER, None, None),
]
HOOK = ('h1', 'h2', 'h3', 'h4')
# how the narrator should pronounce names (the captions keep the real spelling)
SAY = {None: {'Qin': 'Chin', 'Zhou': 'Joe', 'Sui': 'Sway', 'Qing': 'Ching', 'Puyi': 'Pooyee', 'Shi': 'Shir', 'Huang': 'Hwang'},
       'zheng': {'Zheng': 'Jung', 'He': 'Huh'}}
def say(key, text):
    for tab in (SAY.get(key, {}), SAY[None]):
        for a, b in tab.items(): text = re.sub(rf'\b{a}\b', b, text)
    return text

# places (lon, lat)
P = {'anyang': (114.35, 36.1), 'xianyang': (108.7, 34.33), 'xian': (108.94, 34.26), 'luoyang': (112.45, 34.62), 'beijing': (116.4, 39.9),
     'nanjing': (118.8, 32.06), 'hangzhou': (120.16, 30.27), 'kaifeng': (114.3, 34.8), 'canton': (113.26, 23.13), 'hongkong': (114.17, 22.3),
     'taipei': (121.5, 25.03), 'karakorum': (102.8, 47.2), 'shenyang': (123.4, 41.8), 'calicut': (75.8, 11.25), 'malindi': (40.1, -3.2),
     'hormuz': (56.3, 27.1), 'kashgar': (76.0, 39.5), 'samarkand': (66.96, 39.65), 'dunhuang': (94.7, 40.1), 'shanghai': (121.47, 31.23)}
WALL = [(124.4, 40.2), (122.6, 41.3), (121.0, 40.9), (119.75, 40.0), (118.6, 40.35), (117.3, 40.65), (116.5, 40.45), (116.0, 40.35),
        (115.0, 40.75), (113.8, 40.4), (112.5, 40.2), (111.3, 39.5), (110.2, 38.8), (109.7, 38.3), (108.5, 37.9), (107.0, 37.7),
        (106.2, 38.4), (105.2, 37.6), (103.8, 37.3), (102.6, 37.9), (101.3, 38.4), (100.4, 38.9), (99.0, 39.5), (98.2, 39.8),
        (96.0, 40.2), (94.0, 40.3)]
QIN_WALL = [(103.9, 35.4), (104.6, 37.0), (106.2, 38.8), (107.6, 40.6), (110.0, 41.2), (112.0, 41.3), (114.0, 41.5), (116.0, 41.8),
            (118.0, 42.0), (120.5, 41.8), (122.5, 41.4), (124.0, 40.6)]
SHANG = [(110.6, 35.0), (111.3, 36.6), (112.8, 37.8), (114.6, 38.6), (116.6, 38.2), (118.2, 36.8), (117.8, 34.8), (116.2, 33.4),
         (114.0, 32.9), (112.0, 33.3)]
SILK = [P['xian'], (103.8, 36.1), (102.6, 37.9), (100.4, 38.9), (98.2, 39.8), P['dunhuang'], (89.2, 42.9), (82.9, 41.7), P['kashgar'],
        (71.8, 40.4), P['samarkand'], (61.8, 37.6), (54, 36.5)]
CANAL = [P['hangzhou'], (120.6, 31.3), (119.45, 32.2), (119.0, 33.6), (117.6, 33.9), (116.0, 34.3), P['kaifeng'], P['luoyang'],
         (113.9, 35.3), (114.5, 36.5), (115.5, 38.0), P['beijing']]
ZHENG = [P['nanjing'], (121.5, 30.5), (120.5, 25.5), (116.5, 22.0), (110.5, 17.5), (108.5, 12.0), (105.5, 6.5), (103.5, 2.0),
         (99.0, 5.5), (95.5, 6.5), (85.5, 6.0), (80.0, 6.0), P['calicut'], (68.0, 15.0), (60.0, 21.0), P['hormuz'], (58.5, 22.0),
         (52.0, 13.5), (46.0, 9.0), (43.0, 3.0), P['malindi']]
JAPAN_IN = [[(130.0, 36.0), (124.5, 39.5), (123.4, 41.8)], [(131.0, 31.5), (124.0, 31.3), P['shanghai'], P['nanjing']]]

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

def build(voice):
    t, beats, clips = 0.05, [], []
    lead = {'h1': 0.0, 'h2': 0.05, 'h3': 0.05, 'h4': 0.05, 'title': 0.1}
    tail = {'h1': 0.12, 'h2': 0.12, 'h3': 0.15, 'h4': 0.2, 'title': 1.3, 'cta': 2.4, 'moon': 0.5, 'puyi': 0.5}
    tail.update(TAIL_OVERRIDE)
    for key, text, year, yword, cam, chap, card in BEATS:
        b = dict(key=key, text=text, year=year, yword=yword, cam=cam, chap=chap, card=card[:3] if card else None,
                 cword=card[3] if card else None, start=t)
        a, words = voice.get(say(key, text))
        b['l0'] = t + (1.25 if chap else lead.get(key, 0.3)); b['l1'] = b['l0'] + len(a) / SR
        b['words'] = [(b['l0'] + s, b['l0'] + e, x) for s, e, x in words]
        b['tokens'] = text.split()
        clips.append((b['l0'], a))
        t = b['l1'] + tail.get(key, 0.32); b['end'] = t
        beats.append(b)
    return dict(beats=beats, by={b['key']: b for b in beats}, clips=clips, dur=t)

TL = None
G = None
TAIL_OVERRIDE = {}  # other videos reusing this engine can lengthen pauses
_missing = set()
def bt(key): return TL['by'][key]
def w(key, word, n=0, end=False):
    """Time the narrator says `word` (n-th match) in beat `key`."""
    q, hits = norm(say(key, word)), []
    for s, e, x in bt(key)['words']:
        if any(norm(part).startswith(q) for part in x.split()): hits.append((s, e))
    if len(hits) > n: return hits[n][1] if end else hits[n][0]
    if (key, word) not in _missing: _missing.add((key, word)); print(f'  ! no word "{word}" in {key}', file=sys.stderr)
    return bt(key)['l0']
def win(key_a, key_b=None, fin=0.4, fout=0.4, t=0.0, t0=None, t1=None):
    a = bt(key_a)['start'] if t0 is None else t0; b = bt(key_b or key_a)['end'] if t1 is None else t1
    return ease_out(prog(t, a + 0.1, a + 0.1 + fin)) * (1 - ease_io(prog(t, b - fout, b)))
def span(t, t0, t1, fin=0.4, fout=0.4): return ease_out(prog(t, t0, t0 + fin)) * (1 - ease_io(prog(t, t1, t1 + fout)))

# ---------- geography ----------
class Geo:
    def __init__(self, d):
        def keep(x, y): return 20 < x.mean() < 175 and -40 < y.mean() < 80
        def proj(rs): return [laea(r[:, 0], r[:, 1]) for r in rs]
        def polys(path, names=None, key='NAME'):
            out = []
            for f in json.load(open(os.path.join(d, path)))['features']:
                if not f['geometry'] or (names and f['properties'].get(key) not in names): continue
                out += [r for r in rings(f['geometry']) if len(r) > 3 and keep(r[:, 0], r[:, 1])]
            return proj(out)
        self.land = polys('ne_50m_land.geojson'); self.lakes = polys('ne_50m_lakes.geojson')
        self.rivers = []
        for f in json.load(open(os.path.join(d, 'ne_50m_rivers_lake_centerlines.geojson')))['features']:
            g = f['geometry']
            if not g or not g['coordinates']: continue
            for c in (g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]):
                c = np.array(c, float)
                if len(c) > 1 and keep(c[:, 0], c[:, 1]): self.rivers.append((f['properties'].get('name') or '', laea(c[:, 0], c[:, 1])))
        self.prc = polys('countries_50m.geojson', ('China', 'Hong Kong', 'Macao'))
        self.taiwan = polys('countries_50m.geojson', ('Taiwan',))
        H_ = lambda y, n: polys(f'hist/world_{y}.geojson', n)
        self.realm = {'zhou': H_('bc500', ('Zhou states',)), 'states': H_('bc300', ('Zhou states',)), 'qinstate': H_('bc300', ('Qin',)),
                      'han': H_('100', ('Han',)), 'jin': H_('400', ('Jin',)), 'sixteen': H_('400', ('Sixteen Kingdoms',)),
                      'sui': H_('600', ('Sui Empire',)), 'tang': H_('800', ('Tang Empire',)), 'song': H_('1100', ('Song Empire',)),
                      'liao': H_('1100', ('Liao',)), 'xixia': H_('1100', ('Xixia',)), 'yuan': H_('1300', ('Great Khanate',)),
                      'ming': H_('1500', ('Ming Chinese Empire',)), 'qing': H_('1800', ('Qing Empire',)), 'roc': H_('1914', ('Manchu Empire',)),
                      'shang': [laea(np.array([p[0] for p in SHANG]), np.array([p[1] for p in SHANG]))], 'prc': self.prc}

def camera(t):
    beats = TL['beats']; prev = beats[0]['cam']; cur = prev
    for b in beats:
        if t < b['start']: break
        k = ease_io(prog(t, b['start'], b['start'] + 1.2)); nxt = b['cam']
        cur = (lerp(prev[0], nxt[0], k), lerp(prev[1], nxt[1], k), math.exp(lerp(math.log(prev[2]), math.log(nxt[2]), k)))
        prev = nxt
    x, y = laea(cur[0], cur[1])
    return float(x), float(y), cur[2] * (1 + 0.02 * math.sin(t * 0.4))

def draw_map(cr, cam, river_glow=None, glow_a=0.0):
    cr.set_source_rgba(*R.BG); cr.paint()
    g = cairo.RadialGradient(W / 2, MAPY, 100, W / 2, MAPY, 1300)
    g.add_color_stop_rgba(0, *R.WATER0[:3], 1); g.add_color_stop_rgba(1, *R.WATER1[:3], 1); cr.set_source(g); cr.paint()
    cr.new_path(); path_xy(cr, cam, G.land); cr.set_source_rgba(*R.LAND[:3], 1); cr.fill_preserve()
    cr.set_source_rgba(*R.COAST[:3], 0.9); cr.set_line_width(1.6); cr.stroke()
    cr.new_path(); path_xy(cr, cam, G.lakes); cr.set_source_rgba(*R.WATER0[:3], 1); cr.fill()
    cr.new_path()
    for name, (x, y) in G.rivers:
        X, Y = S(cam, x, y); cr.move_to(X[0], Y[0]); [cr.line_to(a, b) for a, b in zip(X[1:], Y[1:])]
    cr.set_source_rgba(*RIVER[:3], 0.4); cr.set_line_width(1.8); cr.stroke()
    if river_glow and glow_a > 0:
        cr.new_path()
        for name, (x, y) in G.rivers:
            if name in river_glow:
                X, Y = S(cam, x, y); cr.move_to(X[0], Y[0]); [cr.line_to(a, b) for a, b in zip(X[1:], Y[1:])]
        cr.set_source_rgba(1, 0.82, 0.35, 0.95 * glow_a); cr.set_line_width(5); cr.stroke_preserve()
        cr.set_source_rgba(1, 0.82, 0.35, 0.25 * glow_a); cr.set_line_width(20); cr.stroke()

def vignette(cr, a=0.75):
    g = cairo.RadialGradient(W / 2, H / 2, 500, W / 2, H / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, a); cr.set_source(g); cr.paint()

def realm(cr, cam, key, a, col=None, edge=True, lw=3.5):
    if a <= 0: return
    col = col or DYN[key][3]
    cr.new_path(); path_xy(cr, cam, G.realm[key]); cr.set_fill_rule(cairo.FILL_RULE_WINDING)
    cr.set_source_rgba(*col[:3], 0.45 * a); cr.fill_preserve()
    if edge: cr.set_source_rgba(*col[:3], min(1, 1.6 * a)); cr.set_line_width(lw); cr.stroke()
    cr.new_path()

def line(cr, cam, pts, k, col, width=6, glow=True, ticks=False):
    """A polyline that draws itself (k 0..1), optionally with battlements (for walls)."""
    if k <= 0: return
    X, Y = L(cam, [p[0] for p in pts], [p[1] for p in pts]); sp = R.smooth(list(zip(X, Y)), 8)
    seg = np.hypot(*np.diff(sp, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)]) / max(seg.sum(), 1e-6)
    n = int(np.searchsorted(cum, k)); pts_ = sp[:max(n, 1)]
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    for lw, al in (((width * 4, 0.18), (width * 2, 0.35)) if glow else ()) + ((width, 1),):
        cr.new_path(); cr.move_to(*pts_[0]); [cr.line_to(*q) for q in pts_[1:]]
        cr.set_source_rgba(*col[:3], al); cr.set_line_width(lw); cr.stroke()
    if ticks:
        for i in range(0, len(pts_) - 1, 2):
            (x0, y0), (x1, y1) = pts_[i], pts_[i + 1]; ang = math.atan2(y1 - y0, x1 - x0)
            cr.save(); cr.translate(x0, y0); cr.rotate(ang); cr.rectangle(-3, -width * 1.3, 6, width * 0.8)
            cr.set_source_rgba(*col[:3], 1); cr.fill(); cr.restore()
    return pts_[-1]

def pin(cr, cam, place, label, t, t0, col=GOLD, side='r', size=34, a=1.0):
    R.pin(cr, cam, P[place] if isinstance(place, str) else place, label, t, t0, col, side, size, a)
def at(cr, cam, place, e, size, a=1.0, rot=0.0, dy=0):
    x, y = L(cam, *(P[place] if isinstance(place, str) else place)); emoji(cr, e, x, y + dy, size, a, rot)

def cjk(cr, txt, x, y, size, col, a=1.0, stroke=None, sw=0.0):
    cr.save(); cr.select_font_face(CJK, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); cr.set_font_size(size)
    ext = cr.text_extents(txt); cr.new_path(); cr.move_to(x - ext.x_advance / 2, y + size * 0.36); cr.text_path(txt)
    if stroke: cr.set_source_rgba(*stroke[:3], a); cr.set_line_width(sw); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
    cr.set_source_rgba(*col[:3], a); cr.fill(); cr.restore()

def seal(cr, ch, x, y, s, a=1.0, col=CRIMSON, rot=0.0):
    """A red seal stamp with a white character."""
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    rrect(cr, -s / 2, -s / 2, s, s, s * 0.12); cr.set_source_rgba(*col[:3], a); cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, 0.9 * a); cr.set_line_width(max(2, s * 0.04)); cr.stroke()
    rrect(cr, -s * 0.4, -s * 0.4, s * 0.8, s * 0.8, s * 0.06); cr.set_source_rgba(1, 1, 1, 0.5 * a); cr.set_line_width(max(1, s * 0.02)); cr.stroke()
    cjk(cr, ch, 0, 0, s * 0.62, (1, 1, 1), a); cr.restore()

def chip(cr, txt, x, y, size, bg, fg, k, a=1.0, rot=0.0, em=None):
    if k <= 0 or a <= 0: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(k, k)
    wd = tw(cr, txt, size); ex = size * 1.2 if em else 0
    rrect(cr, -wd / 2 - size * 0.55 - ex / 2, -size * 1.0, wd + size * 1.1 + ex, size * 1.45, size * 0.72)
    cr.set_source_rgba(*bg[:3], a); cr.fill_preserve(); cr.set_source_rgba(*INK, a); cr.set_line_width(4); cr.stroke()
    if em: emoji(cr, em, -wd / 2 - size * 0.25, -size * 0.32, size * 1.1, a)
    ptext(cr, txt, ex / 2, size * 0.08, size, fg, a, sw=0, shadow=False); cr.restore()

def slam(cr, txt, x, y, size, col, t, t0, a=1.0, rot=-0.04, maxw=980):
    if t < t0 or a <= 0: return
    k = prog(t, t0, t0 + 0.22); s = lerp(2.3, 1.0, ease_out(k)); sh = 12 * math.sin(t * 70) * (1 - prog(t, t0 + 0.22, t0 + 0.5))
    cr.save(); cr.translate(x + sh, y); cr.rotate(rot); cr.scale(s, s)
    ptext(cr, txt, 0, 0, fit(cr, txt, size, maxw), col, a * clamp(k * 3), sw=size * 0.12); cr.restore()

# ---------- props ----------
def soldier(cr, x, y, s, a=1.0, tone=0.0, depth=1.0):
    """A terracotta warrior standing with its feet at (x, y)."""
    c = tuple(v * depth for v in (0.72 + tone, 0.45 + tone * 0.8, 0.31 + tone * 0.6)); d = (c[0] * 0.62, c[1] * 0.6, c[2] * 0.6)
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.new_path(); cr.save(); cr.scale(1, 0.25); cr.arc(0, 0, 60, 0, 2 * math.pi); cr.restore(); cr.set_source_rgba(0, 0, 0, 0.3 * a); cr.fill()
    for lx in (-22, 6): rrect(cr, lx, -78, 16, 78, 5); cr.set_source_rgba(*d, a); cr.fill()
    cr.new_path(); cr.move_to(-50, -200); cr.line_to(50, -200); cr.line_to(60, -70); cr.line_to(-60, -70); cr.close_path()
    cr.set_source_rgba(*c, a); cr.fill_preserve(); cr.set_source_rgba(*d, a); cr.set_line_width(4); cr.stroke()
    for row in range(4):  # armour plates
        for col in range(5):
            cr.rectangle(-38 + col * 16, -188 + row * 18, 12, 13); cr.set_source_rgba(*d, 0.8 * a); cr.fill()
    for side in (-1, 1):
        cr.new_path(); cr.move_to(side * 50, -196); cr.curve_to(side * 72, -160, side * 70, -120, side * 58, -96)
        cr.set_source_rgba(*c, a); cr.set_line_width(22); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
    cr.new_path(); cr.arc(0, -228, 27, 0, 2 * math.pi); cr.set_source_rgba(*c, a); cr.fill_preserve(); cr.set_source_rgba(*d, a); cr.set_line_width(3); cr.stroke()
    cr.new_path(); cr.arc(14, -258, 11, 0, 2 * math.pi); cr.set_source_rgba(*d, a); cr.fill()
    for ex in (-9, 9): cr.new_path(); cr.arc(ex, -230, 3, 0, 2 * math.pi); cr.set_source_rgba(0.2, 0.12, 0.08, a); cr.fill()
    cr.restore()

def army(cr, x0, y0, rows, cols, s0, t, t0, dt=0.03, a=1.0, spread=150, y_back=None):
    rng = np.random.default_rng(5); n = 0
    for r in range(rows):  # back rows (q = 0) first, so the front rows overlap them
        q = r / max(rows - 1, 1); s = s0 * (0.42 + 0.58 * q)
        y = lerp(y_back, y0, q ** 1.3) if y_back is not None else y0 - (rows - 1 - r) * 120 * s0 * (0.6 + 0.4 * q)
        for c in range(cols):
            x = x0 + (c - (cols - 1) / 2) * spread * s + (r % 2) * spread * s * 0.5
            ts = t0 + dt * (n % 40) + 0.05 * r; n += 1
            if t < ts: continue
            rise = 1 - ease_out(prog(t, ts, ts + 0.25))
            soldier(cr, x, y + rise * 60 * s, s, a * clamp(prog(t, ts, ts + 0.12) * 2), rng.uniform(-0.05, 0.05), 0.5 + 0.5 * r / max(rows - 1, 1))

def oracle_bone(cr, x, y, s, a=1.0, crack=1.0):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.new_path(); cr.move_to(-150, -90); cr.curve_to(-60, -130, 60, -130, 150, -90); cr.curve_to(175, 0, 160, 80, 120, 115)
    cr.curve_to(40, 140, -40, 140, -120, 115); cr.curve_to(-160, 80, -175, 0, -150, -90); cr.close_path()
    cr.set_source_rgba(0.93, 0.86, 0.7, a); cr.fill_preserve(); cr.set_source_rgba(0.45, 0.33, 0.2, a); cr.set_line_width(6); cr.stroke()
    for (cx, cy) in ((-70, -40), (60, 20), (-20, 70)):  # the heat cracks the diviners read
        cr.new_path(); cr.move_to(cx, cy - 40 * crack); cr.line_to(cx, cy + 40 * crack); cr.move_to(cx, cy); cr.line_to(cx + 30 * crack, cy - 18 * crack)
        cr.set_source_rgba(0.25, 0.15, 0.08, a); cr.set_line_width(4); cr.stroke()
    for ch, cx, cy in (('王', 0, -55), ('卜', 100, -40), ('雨', -110, 30), ('日', 80, 85), ('月', 10, 20)):
        cjk(cr, ch, cx, cy, 44, (0.35, 0.22, 0.12), a * crack)
    cr.restore()

def coin(cr, x, y, r, a=1.0):
    """A Qin 'ban liang' coin: round, with a square hole."""
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.rectangle(x + r * 0.28, y - r * 0.28, -r * 0.56, r * 0.56)
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); cr.set_source_rgba(0.8, 0.6, 0.25, a); cr.fill_preserve()
    cr.set_source_rgba(0.4, 0.28, 0.1, a); cr.set_line_width(5); cr.stroke(); cr.set_fill_rule(cairo.FILL_RULE_WINDING)
    cjk(cr, '半', x - r * 0.62, y, r * 0.5, (0.4, 0.28, 0.1), a); cjk(cr, '两', x + r * 0.62, y, r * 0.5, (0.4, 0.28, 0.1), a)

def palace(cr, x, y, s, a=1.0):
    """The Forbidden City's gate: red wall, double golden roof."""
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.rectangle(-150, -20, 300, 80); cr.set_source_rgba(0.75, 0.15, 0.12, a); cr.fill()
    for gx in (-70, 0, 70): rrect(cr, gx - 18, 10, 36, 50, 18); cr.set_source_rgba(0.3, 0.05, 0.05, a); cr.fill()
    for (yy, wd, h) in ((-20, 190, 40), (-80, 150, 36)):
        if yy == -80: cr.rectangle(-100, -44, 200, 28); cr.set_source_rgba(0.75, 0.15, 0.12, a); cr.fill()
        cr.new_path(); cr.move_to(-wd, yy); cr.curve_to(-wd * 0.7, yy - h * 0.4, -wd * 0.55, yy - h, -wd * 0.45, yy - h)
        cr.line_to(wd * 0.45, yy - h); cr.curve_to(wd * 0.55, yy - h, wd * 0.7, yy - h * 0.4, wd, yy); cr.close_path()
        cr.set_source_rgba(0.95, 0.72, 0.15, a); cr.fill_preserve(); cr.set_source_rgba(0.45, 0.28, 0.05, a); cr.set_line_width(4); cr.stroke()
    cr.restore()

def moon(cr, x, y, r, a=1.0):
    cr.new_path(); cr.arc(x, y, r, 0, 2 * math.pi)
    g = cairo.RadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r); g.add_color_stop_rgba(0, 0.92, 0.92, 0.9, a); g.add_color_stop_rgba(1, 0.55, 0.55, 0.58, a)
    cr.set_source(g); cr.fill()
    for cx, cy, cr_ in ((-0.3, -0.2, 0.18), (0.35, 0.1, 0.14), (-0.1, 0.45, 0.12), (0.2, -0.5, 0.1), (-0.55, 0.25, 0.08)):
        cr.new_path(); cr.arc(x + cx * r, y + cy * r, cr_ * r, 0, 2 * math.pi); cr.set_source_rgba(0.45, 0.45, 0.48, 0.6 * a); cr.fill()

# ---------- the story ----------
def dyn_alpha(t):
    """How strongly each realm shows at time t (crossfades keyed to the spoken words)."""
    def on(t0, t1, fin=0.5, fout=0.5): return span(t, t0, t1, fin, fout)
    end = TL['dur']
    return {
        'shang': on(w('shang', 'Shang'), bt('zhou')['start'] + 0.3),
        'zhou': on(w('zhou', 'Zhou'), w('confucius', 'war')),
        'states': on(w('confucius', 'war') - 0.2, w('qin', 'crushed') + 0.9),
        'qinstate': on(w('qin', 'Qin'), w('han', 'collapsed') + 0.3),
        'qinall': on(w('qin', 'crushed') + 0.6, w('han', 'collapsed') + 0.3, fin=0.9),
        'han': on(w('han', 'Han'), w('split', 'fell')),
        'jin': on(w('split', 'split'), w('sui', 'reunited')), 'sixteen': on(w('split', 'split'), w('sui', 'reunited')),
        'sui': on(w('sui', 'reunited') - 0.2, w('tang', 'Tang')),
        'tang': on(w('tang', 'Tang'), w('song', 'Song')),
        'song': on(w('song', 'Song'), w('yuan', '1279')), 'liao': on(w('song', 'Song'), w('yuan', 'Mongols')),
        'xixia': on(w('song', 'Song'), w('yuan', 'Mongols')),
        'yuan': on(w('yuan', '1279') - 0.3, w('ming', 'drove')),
        'ming': on(w('ming', 'Ming'), w('qing', 'swept') + 0.4),
        'qing': on(w('qing', 'swept') + 0.3, w('puyi', 'throne')),
        'roc': on(w('puyi', 'throne'), w('prc', 'founded')),
        'prc': on(w('prc', 'founded'), end + 1),
    }

def draw_realms(cr, cam, t):
    A = dyn_alpha(t)
    realm(cr, cam, 'liao', A['liao'] * 0.6, (0.55, 0.6, 0.7)); realm(cr, cam, 'xixia', A['xixia'] * 0.6, (0.75, 0.68, 0.5))
    realm(cr, cam, 'sixteen', A['sixteen'], hexc('#8E6BB0')); realm(cr, cam, 'jin', A['jin'])
    for k in ('shang', 'zhou', 'han', 'sui', 'tang', 'song', 'yuan', 'ming', 'qing', 'roc'): realm(cr, cam, k, A[k])
    realm(cr, cam, 'states', A['states'] * (1 - A['qinall']), JADE); realm(cr, cam, 'states', A['qinall'], DYN['qin'][3])
    realm(cr, cam, 'qinstate', A['qinstate'], DYN['qin'][3], lw=5)
    if A['prc'] > 0:
        cr.new_path(); path_xy(cr, cam, G.prc); cr.set_source_rgba(*CRIMSON[:3], 0.55 * A['prc']); cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, 0.85 * A['prc']); cr.set_line_width(3); cr.stroke()

def label_at(cr, cam, lon, lat, txt, size, col, a, t0=None, t=0.0):
    if a <= 0 or (t0 is not None and t < t0): return
    k = 1.0 if t0 is None else pop_k(t, t0)
    x, y = L(cam, lon, lat); cr.save(); cr.translate(x, y); cr.scale(k, k)
    ptext(cr, txt, 0, 0, size, col, a, fam='Poppins ExtraBold', sw=7); cr.restore()

def draw_story(cr, t, cam):
    # Shang: the Yellow River, the capital, the oracle bones
    a = win('shang', t=t)
    if a > 0:
        label_at(cr, cam, 108.5, 37.6, 'YELLOW RIVER', 34, (1, 0.85, 0.4), a, w('shang', 'Yellow'), t)
        pin(cr, cam, 'anyang', 'ANYANG', t, w('shang', 'rose'), GOLD, 'r', 36, a)
        tb = w('shang', 'bones')
        if t >= w('shang', 'carved') - 0.1:
            k = pop_k(t, w('shang', 'carved') - 0.1, 0.45)
            oracle_bone(cr, 540, 1180, 1.05 * k, a, ease_out(prog(t, tb, tb + 0.5)))
            ptext(cr, 'ORACLE BONE · c. 1200 BC', 540, 1370, 30, PARCH, a * ease_out(prog(t, tb, tb + 0.3)), fam='Poppins ExtraBold', sw=5)
        tf = w('shang', 'future')
        chip(cr, 'ASKING THE ANCESTORS', 540, 970, 40, AMBER, INK, pop_k(t, tf), a, em='🔮')
    # Zhou: the Mandate of Heaven
    a = win('zhou', t=t)
    if a > 0:
        tm = w('zhou', 'Mandate')
        if t >= tm:
            k = pop_k(t, tm); cr.save(); cr.translate(540, 1160); cr.scale(k, k)
            cjk(cr, '天命', 0, -40, 170, GOLD, a, stroke=INK, sw=12)
            ptext(cr, 'MANDATE OF HEAVEN', 0, 120, 56, WHITE, a, sw=8); cr.restore()
            emoji(cr, '☁️', 230, 1060, 110, a * pop_k(t, tm + 0.15), rot=0.1 * math.sin(t * 2))
            emoji(cr, '☁️', 850, 1080, 90, a * pop_k(t, tm + 0.25), rot=-0.1 * math.sin(t * 2))
        ta = w('zhou', 'away')
        if t >= ta:
            emoji(cr, '⚡', 800, 1010, 130 * pop_k(t, ta), a, rot=0.2)
            fl = 1 - prog(t, ta, ta + 0.25)
            if 0 < fl < 1: cr.set_source_rgba(1, 1, 0.85, 0.3 * fl); cr.paint()
    # Warring states and Confucius
    a = win('confucius', t=t)
    if a > 0:
        tw_ = w('confucius', 'war')
        for i, (lon, lat) in enumerate(((112, 36.5), (116.5, 36.6), (114.5, 33.5), (110.5, 34.5), (117.5, 32.5), (113.5, 35.0))):
            ts = tw_ + i * 0.08
            if t >= ts: at(cr, cam, (lon, lat), '⚔️', 70 * pop_k(t, ts), a, rot=0.2 * math.sin(t * 8 + i))
        for i, (word, txt, col) in enumerate((('respect', 'RESPECT', GOLD), ('duty', 'DUTY', WHITE), ('family', 'FAMILY', JADE))):
            chip(cr, txt, 200 + i * 340, 1300, 50, col, INK, pop_k(t, w('confucius', word)), a)
    # Qin: the arrows of conquest from Xianyang
    a = win('qin', t=t)
    if a > 0:
        tc, tr = w('qin', 'crushed'), w('qin', 'rival', end=True)
        for tgt in ((114.5, 36.6), (118.3, 36.8), (116.8, 32.6), (114.3, 34.8), (116.4, 39.6), (112.0, 31.0)):
            route(cr, cam, [P['xianyang'], ((P['xianyang'][0] + tgt[0]) / 2, (P['xianyang'][1] + tgt[1]) / 2 + 0.8), tgt],
                  ease_io(prog(t, tc - 0.1, tr + 0.2)), DYN['qin'][3], width=7, arrow=True, dashed_rest=False)
        pin(cr, cam, 'xianyang', 'XIANYANG', t, w('qin', 'Qin'), GOLD, 'l', 34, a)
    # Qin II: one script, one coin, one measure; the wall; the army
    a = win('qin2', t=t)
    if a > 0:
        ai = a * (1 - ease_io(prog(t, w('qin2', 'army') - 0.2, w('qin2', 'army') + 0.1)))
        tws = w('qin2', 'writing')
        if t >= tws:
            k = pop_k(t, tws); cr.save(); cr.translate(210, 1150); cr.scale(k, k)
            rrect(cr, -90, -90, 180, 180, 24); cr.set_source_rgba(*PARCH[:3], ai); cr.fill(); cjk(cr, '文', 0, 0, 120, INK, ai); cr.restore()
            ptext(cr, 'WRITING', 210, 1290, 40, WHITE, ai * k, sw=6)
        tm = w('qin2', 'money')
        if t >= tm and ai > 0: k = pop_k(t, tm); coin(cr, 540, 1150, 90 * k, ai); ptext(cr, 'MONEY', 540, 1290, 40, WHITE, ai * k, sw=6)
        tme = w('qin2', 'measurements')
        if t >= tme: emoji(cr, '⚖️', 870, 1150, 150 * pop_k(t, tme), ai); ptext(cr, 'MEASURES', 870, 1290, 40, WHITE, ai * pop_k(t, tme), sw=6)
        tl = w('qin2', 'linked')
        end = line(cr, cam, QIN_WALL, ease_io(prog(t, tl, w('qin2', 'north', end=True) + 0.3)), BRICK, 6, ticks=True)
        if t >= tl: label_at(cr, cam, 113, 42.6, 'QIN WALLS', 34, (1, 0.6, 0.5), a, tl + 0.4, t)
    # the clay army near Xi'an (in front of the HUD, lower screen)
    a = span(t, w('qin2', 'army'), bt('qin2')['end'] - 0.1, 0.2, 0.3)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.62 * a); cr.paint()
        army(cr, 540, 1420, 4, 7, 0.85, t, w('qin2', 'army'), 0.015, a, 170)
        slam(cr, 'TERRACOTTA ARMY', 540, 940, 96, TERRA, t, w('qin2', 'clay'), a)
    # Han: Qin collapses, the Silk Road opens, most Chinese are Han
    a = win('han', t=t)
    if a > 0:
        tcol = w('han', 'collapsed')
        if tcol <= t < tcol + 1.2: at(cr, cam, (110, 35), '💥', 200 * pop_k(t, tcol), a * (1 - prog(t, tcol + 0.8, tcol + 1.2)))
        ts = w('han', 'Silk')
        route(cr, cam, SILK, ease_io(prog(t, ts - 0.2, ts + 2.4)), GOLD, width=6, head='🐫', head_size=74, dashed_rest=False, arrow=True)
        label_at(cr, cam, 84, 44.2, 'SILK ROAD', 46, GOLD, a, ts + 0.3, t)
        pin(cr, cam, 'xian', "CHANG'AN", t, w('han', 'Han'), GOLD, 'r', 34, a)
        th = w('han', 'Han', n=1)
        chip(cr, 'HAN CHINESE: ~9 IN 10 PEOPLE', 540, 1330, 46, CRIMSON, WHITE, pop_k(t, th), a)
    # the split
    a = win('split', t=t)
    if a > 0:
        tsp = w('split', 'split')
        if t >= tsp:
            for i, (lon, lat) in enumerate(((108, 34), (113, 33.5), (117, 33))):
                at(cr, cam, (lon, lat), '⚔️', 80 * pop_k(t, tsp + i * 0.1), a, rot=0.25 * math.sin(t * 7 + i))
        label_at(cr, cam, 108.5, 39.3, 'NORTH', 46, (0.85, 0.75, 1), a, tsp + 0.1, t)
        label_at(cr, cam, 113.5, 28.5, 'SOUTH', 46, (0.75, 0.85, 1), a, tsp + 0.25, t)
        chip(cr, '~370 YEARS OF DIVISION', 540, 1330, 48, WHITE, INK, pop_k(t, w('split', 'hundred')), a)
    # Sui: the Grand Canal
    a = win('sui', t=t)
    if a > 0:
        td = w('sui', 'dug')
        line(cr, cam, CANAL, ease_io(prog(t, td, td + 1.8)), (0.35, 0.8, 1.0), 7)
        label_at(cr, cam, 118.6, 35.4, 'GRAND CANAL', 40, (0.55, 0.88, 1), a, w('sui', 'Grand'), t)
        pin(cr, cam, 'hangzhou', 'HANGZHOU', t, td, (0.35, 0.8, 1.0), 'r', 32, a)
        pin(cr, cam, 'beijing', 'BEIJING', t, td + 1.6, (0.35, 0.8, 1.0), 'r', 32, a)
        chip(cr, 'LONGEST CANAL ON EARTH', 540, 1330, 48, (0.35, 0.8, 1.0), INK, pop_k(t, w('sui', 'longest')), a, em='🛶')
    # Tang: a golden age and its giant capital
    a = win('tang', t=t)
    if a > 0:
        tg = w('tang', 'golden')
        chip(cr, 'GOLDEN AGE', 540, 1300, 60, GOLD, INK, pop_k(t, tg), a, em='✨')
        pin(cr, cam, 'xian', "CHANG'AN", t, w('tang', 'capital'), GOLD, 'r', 40, a)
        chip(cr, "CHANG'AN: ~1 MILLION PEOPLE", 540, 1440, 46, WHITE, INK, pop_k(t, w('tang', 'biggest')), a, em='🏮')
    # Song: four inventions
    a = win('song', t=t)
    if a > 0:
        for i, (word, e, txt) in enumerate((('movable', '🔠', 'PRINTING'), ('paper', '💵', 'PAPER MONEY'), ('compass', '🧭', 'COMPASS'),
                                            ('gunpowder', '🧨', 'GUNPOWDER'))):
            te = w('song', word)
            if t < te: continue
            k = pop_k(t, te); x, y = 290 + (i % 2) * 500, 1090 + (i // 2) * 190
            cr.save(); cr.translate(x, y); cr.scale(k, k)
            rrect(cr, -230, -75, 460, 150, 40); cr.set_source_rgba(0.05, 0.04, 0.07, 0.9 * a); cr.fill_preserve()
            cr.set_source_rgba(*DYN['song'][3][:3], a); cr.set_line_width(5); cr.stroke()
            emoji(cr, e, -160, -6, 90, a); ptext(cr, txt, 40, 16, fit(cr, txt, 46, 300), WHITE, a, sw=6); cr.restore()
        label_at(cr, cam, 111, 41.3, 'LIAO', 34, (0.8, 0.85, 0.95), a * 0.9, w('song', 'Song') + 0.3, t)
        label_at(cr, cam, 104.5, 39.4, 'XIXIA', 34, (0.95, 0.88, 0.7), a * 0.9, w('song', 'Song') + 0.4, t)
    # Yuan: the Mongols ride in
    a = win('yuan', t=t)
    if a > 0:
        tm = w('yuan', 'Mongols')
        for tgt in (P['beijing'], P['hangzhou'], (104.0, 30.6)):
            route(cr, cam, [P['karakorum'], ((P['karakorum'][0] + tgt[0]) / 2 + 2, (P['karakorum'][1] + tgt[1]) / 2), tgt],
                  ease_io(prog(t, tm, w('yuan', '1279') + 0.4)), DYN['yuan'][3], width=9, arrow=True, dashed_rest=False)
        pin(cr, cam, 'karakorum', 'MONGOLIA', t, tm, DYN['yuan'][3], 'r', 38, a)
        if t >= tm: at(cr, cam, 'karakorum', '🐎', 90 * pop_k(t, tm), a, dy=-80)
        pin(cr, cam, 'beijing', 'KHANBALIQ (BEIJING)', t, w('yuan', 'Kublai'), GOLD, 'r', 32, a)
    # Ming: out go the Mongols, up go the palace and the wall
    a = win('ming', t=t)
    if a > 0:
        td = w('ming', 'drove')
        route(cr, cam, [P['nanjing'], (114, 38), (111, 43.5)], ease_io(prog(t, td, td + 0.9)), DYN['ming'][3], width=9, arrow=True, dashed_rest=False)
        pin(cr, cam, 'nanjing', 'NANJING', t, w('ming', 'peasant'), GOLD, 'r', 34, a)
        tf = w('ming', 'Forbidden')
        if t >= tf:
            pin(cr, cam, 'beijing', 'BEIJING', t, tf, GOLD, 'r', 34, a)
            palace(cr, 540, 1210, 1.3 * pop_k(t, tf), a); ptext(cr, 'THE FORBIDDEN CITY', 540, 1340, 46, GOLD, a * pop_k(t, tf), sw=7)
        tg = w('ming', 'Great')
        line(cr, cam, WALL, ease_io(prog(t, tg, tg + 1.6)), BRICK, 7, ticks=True)
        if t >= tg: label_at(cr, cam, 103.5, 40.4, 'GREAT WALL', 40, (1, 0.6, 0.5), a, tg + 0.3, t)
    # Zheng He's treasure fleet
    a = win('zheng', t=t)
    if a > 0:
        ts = w('zheng', 'sailed')
        route(cr, cam, ZHENG, ease_io(prog(t, ts - 0.2, w('zheng', 'Africa', end=True) + 0.3)), GOLD, width=6, head='⛵', head_size=80, dashed_rest=True, arrow=True)
        pin(cr, cam, 'nanjing', 'NANJING', t, ts - 0.2, GOLD, 'r', 32, a)
        pin(cr, cam, 'calicut', 'INDIA', t, w('zheng', 'treasure') + 0.6, GOLD, 'r', 32, a)
        pin(cr, cam, 'malindi', 'EAST AFRICA', t, w('zheng', 'Africa'), GOLD, 'r', 36, a)
        chip(cr, 'FIRST VOYAGE 1405 · COLUMBUS 1492', 540, 1300, 40, WHITE, INK, pop_k(t, w('zheng', 'Columbus')), a)
    # Qing: the Manchus sweep in
    a = win('qing', t=t)
    if a > 0:
        tsw = w('qing', 'swept')
        route(cr, cam, [P['shenyang'], (120.5, 41.3), P['beijing']], ease_io(prog(t, tsw - 0.2, tsw + 0.7)), DYN['qing'][3], width=9, arrow=True, dashed_rest=False)
        pin(cr, cam, 'shenyang', 'MANCHURIA', t, w('qing', 'Manchus'), DYN['qing'][3], 'r', 34, a)
        chip(cr, 'PEAK: ~13 MILLION KM²', 540, 1330, 50, DYN['qing'][3], INK, pop_k(t, w('qing', 'largest')), a)
    # Opium Wars
    a = win('opium', t=t)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.25 * a); cr.paint()
        to = w('opium', 'Britain')
        for i, (lon, lat) in enumerate(((118.5, 19.5), (116.5, 18.5), (120, 21))):
            route(cr, cam, [(lon, lat), (114.6, 21.6), P['canton']], ease_io(prog(t, to + i * 0.15, to + 1.2 + i * 0.15)), WHITE, width=4,
                  head='⛵', head_size=64, dashed_rest=False)
        pin(cr, cam, 'canton', 'CANTON', t, to + 0.8, CRIMSON, 'l', 36, a)
        pin(cr, cam, 'hongkong', 'HONG KONG', t, w('opium', 'Wars'), CRIMSON, 'r', 32, a)
        tw_ = w('opium', 'Wars')
        if t >= tw_:
            for i, (lon, lat) in enumerate(((113.0, 24.3), (115.0, 23.4), (112.3, 22.3))):
                at(cr, cam, (lon, lat), '💥', 80 * pop_k(t, tw_ + i * 0.12), a)
        chip(cr, 'OPIUM WARS · 1839–1860', 540, 1330, 48, WHITE, INK, pop_k(t, w('opium', 'Opium')), a)
        slam(cr, 'CENTURY OF HUMILIATION', 540, 1480, 74, CRIMSON, t, w('opium', 'Century'), a)
    # Puyi: the crown cracks; 2,000 years of emperors end
    a = win('puyi', t=t)
    if a > 0:
        tt, te = w('puyi', 'throne'), w('puyi', 'emperors')
        if t < te + 0.2:
            aa = a * (1 - prog(t, te, te + 0.2)); fall = ease_io(prog(t, tt + 0.3, tt + 1.2))
            cr.save(); cr.translate(540, 1080 + 120 * fall); cr.rotate(0.5 * fall)
            emoji(cr, '👑', 0, 0, 220 * pop_k(t, w('puyi', 'last')), aa)
            if t >= tt:
                k = ease_out(prog(t, tt, tt + 0.2)); rng = np.random.default_rng(3)
                for j in range(6):
                    ang = rng.uniform(0, 2 * math.pi); ln = 120 * k
                    cr.new_path(); cr.move_to(0, -8); cr.line_to(math.cos(ang) * ln * 0.5 + 10, math.sin(ang) * ln * 0.5 - 5)
                    cr.line_to(math.cos(ang) * ln, math.sin(ang) * ln); cr.set_source_rgba(1, 1, 1, aa); cr.set_line_width(5); cr.stroke()
            cr.restore()
        if t >= te - 0.3:
            k = ease_io(prog(t, te - 0.2, w('puyi', 'over') + 0.1)); x0, x1, y = 120, 960, 1060
            rrect(cr, x0, y - 26, x1 - x0, 52, 26); cr.set_source_rgba(1, 1, 1, 0.15 * a); cr.fill()
            rrect(cr, x0, y - 26, max(52, (x1 - x0) * k), 52, 26); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
            ptext(cr, '221 BC', x0, y - 50, 38, WHITE, a, anchor='l', sw=6); ptext(cr, '1912', x1, y - 50, 38, WHITE, a * clamp(k * 3 - 2), anchor='r', sw=6)
            ptext(cr, f'{int(2132 * k):,} YEARS OF EMPERORS', 540, y + 16, 32, INK, a, sw=0, shadow=False)
            slam(cr, 'OVER.', 540, 1300, 120, CRIMSON, t, w('puyi', 'over'), a)
    # war
    a = win('war', t=t)
    if a > 0:
        cr.set_source_rgba(0.15, 0, 0, 0.35 * a); cr.paint()
        tc = w('war', 'civil')
        for i, (lon, lat) in enumerate(((108, 36), (113, 31), (116, 37))):
            if t >= tc + i * 0.1: at(cr, cam, (lon, lat), '⚔️', 80 * pop_k(t, tc + i * 0.1), a, rot=0.2 * math.sin(t * 8 + i))
        tj = w('war', 'Japanese')
        for pts in JAPAN_IN:
            route(cr, cam, pts, ease_io(prog(t, tj - 0.2, tj + 0.9)), (0.95, 0.2, 0.25), width=9, arrow=True, dashed_rest=False)
        chip(cr, 'CIVIL WAR', 540, 1320, 50, WHITE, INK, pop_k(t, tc), a)
        chip(cr, 'JAPANESE INVASION · 1937–45', 540, 1450, 46, CRIMSON, WHITE, pop_k(t, tj), a)
    # PRC and Taiwan
    a = win('prc', 'today', t=t)
    if a > 0:
        tf = w('prc', 'founded')
        pin(cr, cam, 'beijing', 'BEIJING', t, tf, GOLD, 'l', 34, win('prc', t=t))
        if t >= tf: at(cr, cam, (104, 34), '⭐', 110 * pop_k(t, tf), a)
        tt = w('prc', 'Taiwan')
        route(cr, cam, [P['nanjing'], (121.5, 28.5), P['taipei']], ease_io(prog(t, w('prc', 'rivals'), tt + 0.3)), (0.5, 0.75, 1), width=6, arrow=True, dashed_rest=False)
        label_at(cr, cam, 125.2, 23.4, 'TAIWAN', 36, (0.6, 0.8, 1), win('prc', t=t), tt, t)
        if t >= tt: cr.new_path(); path_xy(cr, cam, G.taiwan); cr.set_source_rgba(0.45, 0.7, 1, 0.6 * win('prc', t=t)); cr.fill()
    # today
    a = win('today', t=t)
    if a > 0:
        chip(cr, '1.4 BILLION PEOPLE', 540, 1300, 56, WHITE, INK, pop_k(t, w('today', '1.4')), a, em='👥')
        chip(cr, "WORLD'S #2 ECONOMY", 540, 1440, 56, GOLD, INK, pop_k(t, w('today', 'second')), a, em='📈')
    # bones to the Moon
    a = win('moon', t=t)
    if a > 0:
        cr.set_source_rgba(0, 0, 0, 0.5 * a); cr.paint()
        tb, tm = w('moon', 'bones'), w('moon', 'Moon')
        if t >= w('moon', 'writing'): oracle_bone(cr, 270, 1050, 0.75 * pop_k(t, w('moon', 'writing')), a)
        if t >= tb: ptext(cr, 'c. 1200 BC', 270, 1210, 40, PARCH, a * pop_k(t, tb), sw=6)
        if t >= w('moon', 'far') - 0.2:
            k = pop_k(t, w('moon', 'far') - 0.2); moon(cr, 800, 1040, 150 * k, a); emoji(cr, '🚀', 870, 930, 90 * k, a, rot=0.5)
            ptext(cr, "2019: FIRST LANDING", 800, 1240, 38, WHITE, a * k, sw=6)
            ptext(cr, 'ON THE FAR SIDE', 800, 1290, 38, WHITE, a * k, sw=6)
        if t >= tb + 0.3:
            k = pop_k(t, tb + 0.3); cr.save(); cr.translate(540, 1050); cr.scale(k, k); cr.new_path()
            cr.move_to(-70, -16); cr.line_to(20, -16); cr.line_to(20, -42); cr.line_to(75, 0); cr.line_to(20, 42); cr.line_to(20, 16); cr.line_to(-70, 16); cr.close_path()
            cr.set_source_rgba(*GOLD[:3], a); cr.fill_preserve(); cr.set_source_rgba(*INK, a); cr.set_line_width(5); cr.stroke(); cr.restore()

# ---------- hook ----------
def hook_beat(t):
    for k in HOOK:
        b = bt(k)
        if b['start'] <= t < b['end'] + 1e-6: return b
    return bt('h1') if t < bt('h1')['start'] else None

def draw_hook(cr, t):
    if t >= bt('title')['start']: return False
    b = hook_beat(t)
    if b is None: return False
    key = b['key']
    if key == 'h1':  # the terracotta army
        g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.12, 0.07, 0.05); g.add_color_stop_rgb(1, 0.32, 0.2, 0.13)
        cr.set_source(g); cr.paint()
        z = 1.0 + 0.1 * prog(t, b['start'], b['end'])
        cr.save(); cr.translate(540, 1300); cr.scale(z, z); cr.translate(-540, -1300)
        army(cr, 540, 1960, 6, 9, 1.6, t, 0.02, 0.01, 1.0, 140, y_back=1000)
        cr.restore()
        g = cairo.LinearGradient(0, 0, 0, 900); g.add_color_stop_rgba(0, 0, 0, 0, 0.85); g.add_color_stop_rgba(1, 0, 0, 0, 0); cr.set_source(g); cr.paint()
        rows = [('emperor', 'AN EMPEROR', 96, WHITE, 230), ('buried', 'BURIED WITH', 70, PARCH, 350)]
        for word, txt, size, col, y in rows:
            t0 = w('h1', word) - 0.05
            if t >= t0: k = pop_k(t, t0, 0.25); cr.save(); cr.translate(540, y); cr.scale(k, k); ptext(cr, txt, 0, 0, size, col, 1, sw=12); cr.restore()
        te, ts = w('h1', 'eight'), w('h1', 'soldiers', end=True)
        if t >= te:
            n = int(8000 * ease_out(prog(t, te, ts)))
            slam(cr, f'{n:,}', 540, 560, 230, TERRA, t, te, 1.0)
        slam(cr, 'CLAY SOLDIERS', 540, 700, 100, WHITE, t, w('h1', 'clay'), 1.0)
    elif key == 'h2':  # the wall races across the map
        x, y = laea(108, 39); cam = (float(x), float(y), 0.2 * (1.12 - 0.12 * ease_out(prog(t, b['start'], b['end']))))
        draw_map(cr, cam)
        cr.new_path(); path_xy(cr, cam, G.prc); cr.set_source_rgba(*CRIMSON[:3], 0.18); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, 0.35); cr.set_line_width(2); cr.stroke()
        vignette(cr)
        tw0, tl = w('h2', 'wall'), w('h2', 'long', end=True)
        k = ease_io(prog(t, tw0 - 0.1, tl))
        tip = line(cr, cam, WALL, k, BRICK, 9, ticks=True)
        if tip is not None and k < 1: emoji(cr, '🧱', tip[0], tip[1] - 40, 70, 1)
        g = cairo.LinearGradient(0, 0, 0, 700); g.add_color_stop_rgba(0, 0, 0, 0, 0.8); g.add_color_stop_rgba(1, 0, 0, 0, 0); cr.set_source(g); cr.paint()
        slam(cr, 'A WALL', 540, 300, 150, WHITE, t, w('h2', 'wall'))
        if t >= w('h2', 'twenty') - 0.1:
            km = int(21196 * ease_out(prog(t, w('h2', 'twenty') - 0.1, tl)))
            slam(cr, f'{km:,} KM', 540, 1260, 170, (1, 0.62, 0.5), t, w('h2', 'twenty') - 0.1)
            ptext(cr, 'THE GREAT WALL, ALL SECTIONS', 540, 1370, 40, PARCH, pop_k(t, w('h2', 'long')), fam='Poppins ExtraBold', sw=6)
    elif key == 'h3':  # the inventions slam in
        g = cairo.RadialGradient(540, 960, 100, 540, 960, 1200); g.add_color_stop_rgb(0, 0.62, 0.08, 0.1); g.add_color_stop_rgb(1, 0.18, 0.02, 0.04)
        cr.set_source(g); cr.paint()
        for i in range(0, 1920, 120):  # faint lattice
            for j in range(0, 1080, 120):
                cr.rectangle(j + 20, i + 20, 80, 80); cr.set_source_rgba(1, 0.8, 0.3, 0.04); cr.set_line_width(3); cr.stroke()
        for i, (word, e, txt) in enumerate((('Paper', '📜', 'PAPER'), ('Gunpowder', '🧨', 'GUNPOWDER'), ('compass', '🧭', 'THE COMPASS'))):
            t0 = w('h3', word) - 0.05
            if t < t0: continue
            k = prog(t, t0, t0 + 0.2); s = lerp(2.0, 1.0, ease_out(k)); sh = 10 * math.sin(t * 70) * (1 - prog(t, t0 + 0.2, t0 + 0.45))
            y = 470 + i * 360
            cr.save(); cr.translate(540 + sh, y); cr.rotate((-0.04, 0.04, -0.03)[i]); cr.scale(s, s)
            rrect(cr, -440, -140, 880, 280, 60); cr.set_source_rgba(0.05, 0.03, 0.04, 0.85 * clamp(k * 3)); cr.fill_preserve()
            cr.set_source_rgba(*GOLD[:3], clamp(k * 3)); cr.set_line_width(6); cr.stroke()
            emoji(cr, e, -300, -10, 170, clamp(k * 3)); ptext(cr, txt, 90, 30, fit(cr, txt, 110, 560), WHITE, clamp(k * 3), sw=10); cr.restore()
            fl = 1 - prog(t, t0, t0 + 0.2)
            if 0 < fl < 1: cr.set_source_rgba(1, 1, 1, 0.2 * fl); cr.paint()
        ts = bt('h3')['l1'] - 0.1
        if t >= ts:
            k = prog(t, ts, ts + 0.2); s = lerp(2.5, 1.0, ease_out(k))
            cr.save(); cr.translate(540, 1560); cr.rotate(-0.08); cr.scale(s, s)
            rrect(cr, -380, -70, 760, 120, 20); cr.set_source_rgba(*GOLD[:3], clamp(k * 3)); cr.fill()
            ptext(cr, 'ALL INVENTED IN CHINA', 0, 14, 62, INK, clamp(k * 3), sw=0, shadow=False); cr.restore()
    elif key == 'h4':  # 3,000 years flash past, dynasty by dynasty
        x, y = laea(*OVER[:2]); cam = (float(x), float(y), 0.17)
        draw_map(cr, cam); vignette(cr)
        t0, t1 = w('h4', 'civilisation'), w('h4', 'years', end=True)
        k = ease_io(prog(t, t0, t1))
        seq = list(reversed(ORDER))
        i = min(int(k * len(seq)), len(seq) - 1)
        if t >= t0 - 0.1:
            key_ = seq[i] if t >= t0 else 'prc'
            if key_ == 'prc':
                cr.new_path(); path_xy(cr, cam, G.prc); cr.set_source_rgba(*CRIMSON[:3], 0.6); cr.fill()
            else: realm(cr, cam, key_ if key_ != 'qin' else 'qinstate', 1.0, DYN[key_][3])
            if key_ == 'qin': realm(cr, cam, 'states', 1.0, DYN['qin'][3])
            ch, name = DYN[key_][0], DYN[key_][1]
            seal(cr, ch, 540, 1000, 260, 0.95, DYN[key_][3] if key_ not in ('tang', 'qing', 'shang') else CRIMSON, rot=0.05 * math.sin(i * 1.7))
            ptext(cr, name, 540, 1230, 56, WHITE, 1, sw=8)
        if t < t0: yr = 2026
        else:
            ys = [2026] + [STARTS[ORDER.index(q)] for q in seq]; f = clamp(k * len(seq) - i)
            yr = lerp(ys[i], ys[i + 1], ease_out(clamp(f / 0.5)))
        ptext(cr, fmt_year(yr), 540, 330, 150, GOLD, 1, sw=16)
        slam(cr, '3,000+ YEARS', 540, 1480, 130, WHITE, t, w('h4', 'three'))
    fl = 1 - prog(t, b['start'], b['start'] + 0.15)  # hard flash cut into each shot
    if key != 'h1' and 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.6 * fl); cr.paint()
    return True

def draw_title(cr, t, cam):
    b = bt('title')
    if not (b['start'] <= t < b['end'] + 0.3): return
    a = 1 - ease_io(prog(t, b['end'] - 0.25, b['end'] + 0.3))
    cr.set_source_rgba(0.03, 0.02, 0.04, 0.55 * a); cr.paint()
    s0 = b['start']
    k1 = pop_k(t, w('title', 'entire') - 0.1)
    cr.save(); cr.translate(540, 700); cr.scale(k1, k1); ptext(cr, 'THE ENTIRE HISTORY OF', 0, 0, 62, PARCH, a, fam='Poppins ExtraBold', sw=8); cr.restore()
    tc = w('title', 'China')
    if t >= tc:
        k = prog(t, tc, tc + 0.25); s = lerp(2.6, 1.0, ease_out(k)); sh = 12 * math.sin(t * 70) * (1 - prog(t, tc + 0.25, tc + 0.6))
        cr.save(); cr.translate(540 + sh, 930); cr.rotate(-0.03); cr.scale(s, s); ptext(cr, 'CHINA', 0, 0, 250, CRIMSON, a * clamp(k * 3), sw=22); cr.restore()
        fl = 1 - prog(t, tc, tc + 0.3)
        if 0 < fl < 1: cr.set_source_rgba(1, 1, 1, 0.3 * fl); cr.paint()
    k3 = pop_k(t, tc + 0.4)
    if t >= tc + 0.4:
        cr.save(); cr.translate(540, 1100); cr.scale(k3, k3); txt = 'FROM 1600 BC TO TODAY'; wd = tw(cr, txt, 52)
        rrect(cr, -wd / 2 - 40, -58, wd + 80, 86, 43); cr.set_source_rgba(*GOLD[:3], a); cr.fill()
        ptext(cr, txt, 0, 4, 52, INK, a, sw=0, shadow=False); cr.restore()
        for i, ch in enumerate('中国'):
            k4 = pop_k(t, tc + 0.6 + i * 0.12); cr.save(); cr.translate(460 + i * 160, 1280); cr.scale(k4, k4)
            seal(cr, ch, 0, 0, 140, a, CRIMSON, rot=(-0.06, 0.05)[i]); cr.restore()

# ---------- chrome ----------
def fmt_year(v):
    if isinstance(v, str): return v
    v = int(round(v))
    if v == 0: v = 1
    return f'{-v} BC' if v < 0 else f'{v} AD'

def year_events():
    ev = []
    for b in TL['beats']:
        if b['key'] in HOOK or b['key'] == 'title' or b['year'] is None: continue
        ev.append((w(b['key'], b['yword']) if b['yword'] else b['l0'], b['year']))
    return sorted(ev, key=lambda e: e[0])

def year_at(t):
    if t < bt('shang')['start'] + 0.2: return None
    val, prev = None, None
    for te, v in TL['yev']:
        if t < te - 0.1: break
        if isinstance(v, int) and isinstance(prev, int) and prev != v: val = lerp(prev, v, ease_out(prog(t, te - 0.1, te + 0.7)))
        else: val = v
        prev = v
    return val

def draw_year(cr, t):
    v = year_at(t)
    if v is None or t >= bt('cta')['start']: return
    a = ease_out(prog(t, bt('shang')['start'] + 0.2, bt('shang')['start'] + 0.5))
    txt = fmt_year(v); size = 150 if not isinstance(v, str) else 120
    ptext(cr, txt, 540, 300, fit(cr, txt, size, 900), GOLD, a, sw=16)

def current_dyn(t):
    v = year_at(t)
    if v is None: return None
    if isinstance(v, str): return 'prc'
    cur = 'shang'
    for k, s in zip(ORDER, STARTS):
        if v >= s - 0.5: cur = k
    if cur == 'qin' and t >= w('han', 'Han'): cur = 'han'
    return cur

def draw_plate(cr, t):
    """Seal stamp + dynasty name under the year, popping when the dynasty changes."""
    if t < bt('shang')['start'] + 0.2 or t >= bt('cta')['start']: return
    k = current_dyn(t)
    if k is None: return
    t0 = TL['dyn_t'].get(k, 0)
    pk = pop_k(t, t0, 0.4); a = 1.0
    ch, name, yrs, col = DYN[k]
    cr.save(); cr.translate(540, 450); cr.scale(pk, pk)
    wd = max(tw(cr, name, 50), tw(cr, yrs, 30, 'Poppins ExtraBold'))
    x0 = -(wd + 130) / 2
    rrect(cr, x0 - 20, -62, wd + 170, 124, 30); cr.set_source_rgba(0.05, 0.04, 0.07, 0.82); cr.fill_preserve()
    cr.set_source_rgba(*col[:3], 1); cr.set_line_width(4); cr.stroke()
    seal(cr, ch, x0 + 50, 0, 96, a, CRIMSON if k not in ('han', 'prc') else (0.65, 0.05, 0.1), rot=-0.06)
    ptext(cr, name, x0 + 120, 8, 50, col, a, anchor='l', sw=7)
    ptext(cr, yrs, x0 + 122, 46, 30, PARCH, a, fam='Poppins ExtraBold', anchor='l', sw=5)
    cr.restore()

def chapter_now(t):
    cur = None
    for b in TL['beats']:
        if t >= b['start'] and b['chap']: cur = b['chap']
    return cur

def draw_chapter_label(cr, t):
    ch = chapter_now(t)
    if not ch or t >= bt('cta')['start']: return
    txt = f'CHAPTER {ch[0]} · {ch[1]}'
    ptext(cr, txt, 540, 120, fit(cr, txt, 34, 960, 'Poppins ExtraBold'), PARCH, 0.9, fam='Poppins ExtraBold', sw=5)

def draw_chapter_card(cr, t):
    for b in TL['beats']:
        if not b['chap']: continue
        t0, t1 = b['start'], b['l0'] - 0.05
        if not (t0 <= t <= t1 + 0.3): continue
        k_in = ease_out(prog(t, t0, t0 + 0.3)); k_out = ease_io(prog(t, t1 - 0.2, t1 + 0.2))
        x = lerp(-W, 0, k_in) + lerp(0, W, k_out)
        cr.save(); cr.translate(x, 0)
        cr.rectangle(0, 720, W, 400); cr.set_source_rgba(0.45, 0.04, 0.07, 0.95); cr.fill()
        cr.rectangle(0, 720, W, 8); cr.set_source_rgba(*GOLD[:3], 1); cr.fill(); cr.rectangle(0, 1112, W, 8); cr.fill()
        ptext(cr, f'CHAPTER {b["chap"][0]}', 540, 840, 54, GOLD, 1, fam='Poppins ExtraBold', sw=6)
        ptext(cr, b['chap'][1], 540, 970, fit(cr, b['chap'][1], 96, 980), WHITE, 1, sw=12)
        for dx in (-50, 0, 50):
            cr.new_path(); cr.move_to(540 + dx, 1040); cr.line_to(552 + dx, 1052); cr.line_to(540 + dx, 1064); cr.line_to(528 + dx, 1052); cr.close_path()
            cr.set_source_rgba(*GOLD[:3], 1); cr.fill()
        cr.restore()

def draw_card(cr, t):
    for b in TL['beats']:
        if not b['card']: continue
        t0 = w(b['key'], b['cword']); t1 = b['end']
        if not (t0 <= t <= t1): continue
        e, name, sub = b['card']
        k = ease_out(prog(t, t0, t0 + 0.3)); out = 1 - ease_io(prog(t, t1 - 0.3, t1)); a = k * out; x = lerp(-500, 0, k)
        cr.save(); cr.translate(x, 0)
        rrect(cr, 50, 1400, 980, 160, 80); cr.set_source_rgba(0.05, 0.04, 0.07, 0.92 * a); cr.fill_preserve()
        cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
        cr.new_path(); cr.arc(130, 1480, 64, 0, 2 * math.pi)
        g = cairo.RadialGradient(110, 1455, 10, 130, 1480, 64); g.add_color_stop_rgba(0, 0.95, 0.25, 0.25, a); g.add_color_stop_rgba(1, 0.5, 0.04, 0.08, a)
        cr.set_source(g); cr.fill_preserve(); cr.set_source_rgba(*GOLD[:3], a); cr.set_line_width(4); cr.stroke()
        emoji(cr, e, 130, 1476, 78 * ease_back(prog(t, t0 + 0.1, t0 + 0.4), 3), a)
        ptext(cr, name, 220, 1478, fit(cr, name, 56, 780), WHITE, a, anchor='l', sw=8)
        ptext(cr, sub, 222, 1526, fit(cr, sub, 30, 780, 'Poppins SemiBold'), PARCH, a, fam='Poppins SemiBold', anchor='l', sw=5)
        cr.restore()

def draw_timeline(cr, t):
    """A ribbon of dynasties along the bottom; the current one lights up."""
    a = ease_out(prog(t, bt('shang')['start'], bt('shang')['start'] + 0.5)) * (1 - ease_io(prog(t, bt('cta')['start'], bt('cta')['start'] + 0.4)))
    if a <= 0: return
    cur = current_dyn(t); n = len(ORDER); x0, x1, y = 40, 1040, 1830; sw_ = (x1 - x0) / n
    for i, k in enumerate(ORDER):
        x = x0 + i * sw_; on = k == cur; past = ORDER.index(cur) > i if cur in ORDER else False
        rrect(cr, x + 3, y - 34, sw_ - 6, 68, 14)
        cr.set_source_rgba(*(DYN[k][3][:3] if (on or past) else (0.25, 0.22, 0.28)), a * (1 if on else (0.55 if past else 0.7))); cr.fill()
        if on:
            rrect(cr, x + 1, y - 36, sw_ - 2, 72, 15); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(4); cr.stroke()
        cjk(cr, DYN[k][0], x + sw_ / 2, y, 40, WHITE if (on or past) else (0.65, 0.62, 0.7), a)

def caption_groups(b):
    words, src, toks = b['words'], list(b['tokens']), []
    for _, _, x in words:
        n = len(x.split()); toks.append(' '.join(src[:n])); src = src[n:]
    if src or len(toks) != len(words): toks = [x for _, _, x in words]
    groups, cur = [], []
    for tok, (s, e, _) in zip(toks, words):
        cur.append((s, e, tok))
        if len(cur) == 3 or re.search(r"[.,!?:;…]$", tok) or tok.endswith('...'): groups.append(cur); cur = []
    if cur: groups.append(cur)
    return groups

HOT = ('china', 'shang', 'zhou', 'qin', 'han', 'sui', 'tang', 'song', 'ming', 'qing', 'mongols', 'kublai', 'confucius', 'puyi', 'mao',
       'taiwan', 'emperor', 'wall', 'silk', 'canal', 'opium', 'gunpowder', 'compass', 'paper', 'moon', 'bones', 'zheng', 'africa', 'heaven')
def draw_captions(cr, t, y=1660):
    for b in TL['beats']:
        if not (b['l0'] - 0.05 <= t < b['l1'] + 0.3): continue
        if b['key'] == 'title': return
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
        cr.save(); cr.translate(540, y); cr.scale(sc, sc); x = -total / 2
        for j, (u, wd) in enumerate(zip(ups, widths)):
            cr.save(); cr.translate(x + wd / 2, 0)
            if j == cur: k = ease_back(prog(t, g[j][0], g[j][0] + 0.15), 3); cr.scale(1 + 0.12 * k, 1 + 0.12 * k)
            hot = any(ch.isdigit() for ch in u) or norm(u) in HOT
            col = GOLD if j == cur else (hexc('#FFCF70') if hot else WHITE)
            ptext(cr, u, 0, 0, size, col, 1.0 if j <= cur else 0.6, sw=10); cr.restore(); x += wd + space
        cr.restore(); return

def draw_cta(cr, t):
    b = bt('cta')
    if t < b['start']: return
    a = ease_out(prog(t, b['start'], b['start'] + 0.4))
    cr.set_source_rgba(0.05, 0.02, 0.03, 0.6 * a); cr.paint()
    tq = w('cta', 'Which')
    k = pop_k(t, tq); cr.save(); cr.translate(540, 520); cr.scale(k, k)
    ptext(cr, 'WHICH DYNASTY WAS', 0, 0, 74, WHITE, a, sw=10); ptext(cr, 'THE GREATEST?', 0, 110, 104, GOLD, a, sw=12); cr.restore()
    for i, key in enumerate(('han', 'tang', 'song', 'ming', 'qing')):
        ts = w('cta', 'greatest') + i * 0.12
        if t < ts: continue
        kk = pop_k(t, ts) * (1 + 0.03 * math.sin(t * 5 + i)); x = 130 + i * 205
        cr.save(); cr.translate(x, 880); cr.scale(kk, kk)
        seal(cr, DYN[key][0], 0, 0, 150, 1, CRIMSON, rot=0.06 * math.sin(i * 2.3))
        ptext(cr, DYN[key][1].split()[0], 0, 125, 40, DYN[key][3], 1, sw=7); cr.restore()
    tc = w('cta', 'comments')
    if t >= tc:
        k = pop_k(t, tc); cr.save(); cr.translate(540, 1140); cr.scale(k, k)
        ptext(cr, 'COMMENT BELOW', -50, 0, 66, WHITE, 1, sw=9); emoji(cr, '👇', 330, -20, 80, 1); cr.restore()
    tf = w('cta', 'follow')
    if t >= tf:
        k = pop_k(t, tf) * (1 + 0.04 * math.sin(t * 6)); cr.save(); cr.translate(540, 1320); cr.scale(k, k)
        txt = 'FOLLOW FOR MORE'; wd = tw(cr, txt, 56)
        rrect(cr, -wd / 2 - 90, -62, wd + 180, 98, 49); cr.set_source_rgba(*CRIMSON[:3], 1); cr.fill()
        ptext(cr, txt, 30, 4, 56, WHITE, 1, sw=6); emoji(cr, '🔔', -wd / 2 - 30, -12, 66, 1, rot=0.3 * math.sin(t * 9)); cr.restore()

def draw_footnote(cr, t):
    a = ease_out(prog(t, bt('zhou')['start'], bt('zhou')['start'] + 0.5)) * (1 - ease_io(prog(t, bt('moon')['start'], bt('moon')['start'] + 0.4)))
    if a > 0: ptext(cr, 'Borders approximate', 1040, 1765, 22, (0.7, 0.66, 0.58), 0.8 * a, fam='Poppins SemiBold', anchor='r', sw=0, shadow=False)

# ---------- frame ----------
def render_frame(cr, t):
    if draw_hook(cr, t):
        draw_captions(cr, t); return
    cam = camera(t)
    glow = ['Huang'] if t < bt('zhou')['start'] + 0.5 else None
    draw_map(cr, cam, glow, win('shang', t=t) * ease_out(prog(t, w('shang', 'Yellow'), w('shang', 'Yellow') + 0.5)))
    draw_realms(cr, cam, t)
    vignette(cr)
    g = cairo.LinearGradient(0, 0, 0, 600); g.add_color_stop_rgba(0, 0, 0, 0, 0.7); g.add_color_stop_rgba(1, 0, 0, 0, 0); cr.set_source(g); cr.paint()
    g = cairo.LinearGradient(0, 1500, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.75); cr.set_source(g); cr.paint()
    draw_story(cr, t, cam)
    draw_year(cr, t)
    draw_plate(cr, t)
    draw_chapter_label(cr, t)
    draw_card(cr, t)
    draw_timeline(cr, t)
    draw_footnote(cr, t)
    draw_title(cr, t, cam)
    draw_chapter_card(cr, t)
    draw_cta(cr, t)
    draw_captions(cr, t)
    if t < bt('title')['start'] + 0.15:
        fl = 1 - prog(t, bt('title')['start'], bt('title')['start'] + 0.15)
        if 0 < fl <= 1: cr.set_source_rgba(1, 1, 1, 0.6 * fl); cr.paint()
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
    bpm = 100; beat = 60 / bpm; bar = beat * 4
    chords = [[50, 57, 62], [48, 55, 60], [45, 52, 57], [47, 54, 59]]  # D, C, A, B (open fifths, pentatonic colour)
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; L_ = np.arange(int(bar * 1.3 * SR)) / SR
        env = np.minimum(1, L_ / 0.6) * np.exp(-L_ * 0.5)
        put(music, ci * bar, sum(0.03 * (np.sin(2 * np.pi * note(m) * L_) + 0.4 * np.sin(2 * np.pi * note(m + 12) * 1.002 * L_)) for m in ch) * env)
        put(music, ci * bar, 0.1 * np.sin(2 * np.pi * note(ch[0] - 24) * L_) * env)
    penta = [62, 64, 66, 69, 71, 74, 76, 78]  # D major pentatonic, a guzheng-ish pluck line
    pat = [0, 2, 4, 3, 5, 4, 2, 1, 0, 3, 4, 6, 5, 3, 2, 4]
    hook_end, cta = bt('title')['start'], bt('cta')['start']
    for bi in range(int(dur / (beat / 2))):
        t0 = bi * beat / 2
        if t0 < hook_end + 1.5: continue
        if bi % 4 in (0, 1, 3) or bi % 16 == 10:
            f = note(penta[pat[bi % 16]] + (0 if (bi // 32) % 2 == 0 else -5)); L_ = np.arange(int(0.6 * SR)) / SR
            sig = sum((1 / h) * np.sin(2 * np.pi * f * h * L_) * np.exp(-L_ * (5 + 3 * h)) for h in range(1, 6))
            put(music, t0, 0.035 * sig)
    for bi in range(int(dur / beat)):  # drums: taiko-like hits, denser in the hook
        t0 = bi * beat
        if t0 > cta + 3: break
        if t0 < hook_end or bi % 2 == 0 or bi % 8 == 7:
            L_ = np.arange(int(0.5 * SR)) / SR
            put(music, t0, 0.45 * np.sin(2 * np.pi * np.cumsum(55 + 60 * np.exp(-L_ * 20)) / SR) * np.exp(-L_ * 7))
            put(music, t0, 0.05 * rng.standard_normal(len(L_)) * np.exp(-L_ * 35))
        M = np.arange(int(0.05 * SR)); put(music, t0 + beat / 2, 0.02 * rng.standard_normal(len(M)) * np.exp(-M / SR * 60))
    music = np.tanh(music * 1.3) * 0.5
    fx = np.zeros(n)
    def boom(t0, amp=0.7):
        L_ = np.arange(int(2.0 * SR)) / SR
        put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 80 * np.exp(-L_ * 10)) / SR) * np.exp(-L_ * 2.5))
        put(fx, t0, 0.15 * amp * rng.standard_normal(len(L_)) * np.exp(-L_ * 12))
    def whoosh(t0, amp=0.18):
        nz = rng.standard_normal(int(0.7 * SR)); env = np.sin(np.pi * np.linspace(0, 1, len(nz))) ** 2
        put(fx, t0, amp * np.convolve(nz, np.ones(30) / 30, 'same') * env)
    def gong(t0, amp=0.35, f0=98):
        L_ = np.arange(int(4.0 * SR)) / SR; bend = 1 - 0.01 * (1 - np.exp(-L_ * 2))
        sig = sum(a_ * np.sin(2 * np.pi * f0 * r * np.cumsum(bend) / SR) * np.exp(-L_ * d) for r, a_, d in
                  ((1, 1, 0.8), (1.47, 0.6, 1.0), (2.09, 0.5, 1.3), (2.56, 0.35, 1.6), (3.2, 0.25, 2.0), (4.1, 0.15, 2.6)))
        put(fx, t0, amp * sig * np.minimum(1, L_ / 0.01))
    def ticks(t0, t1, gap=0.05):
        for k in range(int((t1 - t0) / gap)):
            L_ = np.arange(int(0.025 * SR)) / SR; put(fx, t0 + k * gap, 0.07 * np.sin(2 * np.pi * 1700 * L_) * np.exp(-L_ * 90))
    # hook: a hit on every punch word, a whoosh into every cut
    boom(0.02, 0.9); boom(w('h1', 'eight'), 0.8); ticks(w('h1', 'eight'), w('h1', 'soldiers', end=True))
    for key, word in (('h2', 'wall'), ('h3', 'Paper'), ('h3', 'Gunpowder'), ('h3', 'compass'), ('h4', 'three')):
        boom(w(key, word), 0.75)
    ticks(w('h2', 'twenty'), w('h2', 'long', end=True))
    for key in ('h2', 'h3', 'h4', 'title'): whoosh(bt(key)['start'] - 0.2, 0.28)
    t0, t1 = w('h4', 'civilisation'), w('h4', 'years', end=True)
    for i in range(len(ORDER)): put(fx, t0 + (t1 - t0) * i / len(ORDER), 0.1 * np.sin(2 * np.pi * 880 * np.arange(int(0.04 * SR)) / SR) * np.exp(-np.arange(int(0.04 * SR)) / SR * 60))
    gong(w('title', 'China'), 0.45); boom(w('title', 'China'), 0.9)
    for b in T['beats']:
        if b['key'] in HOOK or b['key'] == 'title': continue
        whoosh(b['start'] - 0.2, 0.1)
        if b['chap']: gong(b['start'] + 0.1, 0.25, 110)
    for key, word in (('qin', 'crushed'), ('han', 'collapsed'), ('split', 'split'), ('yuan', 'Mongols'), ('qing', 'swept'), ('opium', 'Wars'),
                      ('opium', 'Century'), ('puyi', 'throne'), ('puyi', 'over'), ('war', 'Japanese'), ('prc', 'founded'), ('zhou', 'away')):
        boom(w(key, word), 0.55)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same')
    duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2)
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

# ---------- setup & render ----------
def setup(data_dir, cache):
    global TL, G
    TL = build(WordVoice(cache)); G = Geo(data_dir)
    TL['yev'] = year_events()
    # when each dynasty plate should pop: the first moment it becomes current
    TL['dyn_t'] = {}
    t = bt('shang')['start']
    while t < TL['dur']:
        k = current_dyn(t)
        if k and k not in TL['dyn_t']: TL['dyn_t'][k] = t
        t += 1 / FPS

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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_china'))
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
    bounds = np.linspace(0, nfr, workers * 3 + 1).astype(int)
    parts = [(int(a), int(b), f'{base}.part{k:02d}.mp4') for k, (a, b) in enumerate(zip(bounds[:-1], bounds[1:]))]
    with Pool(workers) as p: done = p.map(render_chunk, parts)
    with open(base + '.parts.txt', 'w') as f:
        for d in done: f.write(f"file '{os.path.abspath(d)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', base + '.parts.txt', '-i', base + '.wav',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    for d in done: os.remove(d)

if __name__ == '__main__':
    main()
