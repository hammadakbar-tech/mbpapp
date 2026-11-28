# GeoBall Wars: Canada vs Asia, Episode 01. Canada takes on 10 Asian countries, best of 5 each (9:16 render).
# Every ball line is cut into shots (close-up, low angle, over-the-shoulder, two-shot, reaction) and cuts to a
# full-screen visual of whatever is being talked about (islands, volcanoes, reefs, Christmas in September...).
# Usage: python3 caasia.py <data_dir> <out.mp4> [--preview t1,t2,...]
import json, math, os, ssl, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import edge_tts.communicate as _etc
if os.path.exists('/root/.ccr/ca-bundle.crt'): _etc._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
import china as C
import warballs as B
from warballs import ball
from big import local, bounds, area, km_shape, km_path
from popu import streaks, shake
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, hexc, SR

PH_C = hexc('#E8333F')[:3]
A_C, U_C = PH_C, hexc('#F0435A')[:3]
NARR = ('en-US-GuyNeural', '+8%')
PHV = ('en-CA-LiamNeural', '+6%')
# name, flag, voice, colour, landmark emoji, reaction, (insult, reply), rounds, (e1 speaker, e1), (e2 speaker, e2)
# each round: (topic, icon, loser_first, line_a, line_b, verdict_word, (ph_val, ph_lab), (op_val, op_lab), kind)
MATCHES = [
 ('India', 'in', 'en-IN-PrabhatNeural', '#FF8C2B', '🏏', 'Arre!',
  ("Canada! Sorry? You'll be saying that a lot today.", "Sorry, but I came to win, eh!"),
  [('SIZE', '📏', 'OP', "I'm three point three million square kilometres!", "Sorry, I'm almost ten million!", 'million', (9984670, '9.98M KM²'), (3287263, '3.29M KM²'), 'size'),
   ('PEOPLE', '👥', 'PH', "Forty-one million Canadians!", "One point four six billion Indians. The most on Earth!", 'Earth', (41.5, '41.5M'), (1460, '1.46 BILLION'), 'bar'),
   ('CRICKET', '🏏', 'PH', "I play cricket too… a little.", "I've won five World Cups!", 'Cups', (0, 'A LITTLE'), (5, '5 WORLD CUPS'), 'icon'),
   ('HEAT RECORD', '🔥', 'PH', "Lytton hit forty-nine point six degrees!", "Phalodi hit fifty-one!", 'fifty', (49.6, '49.6°C'), (51.0, '51.0°C'), 'bar'),
   ('COASTLINE', '🏖️', 'OP', "Seven thousand kilometres of coast!", "Sorry. Two hundred thousand. The longest on Earth!", 'Earth', (202080, '202,080 KM'), (7000, '7,000 KM'), 'bar')],
  ('PH', "Sorry… I mean, well played."), ('OP', "Told you! Namaste, Canada!")),
 ('Philippines', 'ph', 'fil-PH-AngeloNeural', '#3D7BFF', '🏝️', 'Ay, grabe!',
  ("Canada! Over a million Filipinos live with you!", "And I love every one of them. Sorry, but let's battle!"),
  [('SIZE', '📏', 'OP', "Three hundred thousand square kilometres!", "Sorry. I'm thirty-three times bigger!", 'bigger', (9984670, '9.98M KM²'), (300000, '300,000 KM²'), 'size'),
   ('PEOPLE', '👥', 'PH', "Forty-one million Canadians!", "One hundred and twelve million Filipinos!", 'Filipinos', (41.5, '41.5M'), (112.7, '112.7M'), 'bar'),
   ('ISLANDS', '🏝️', 'OP', "Seven thousand six hundred and forty-one islands!", "Sorry. I have over fifty-two thousand!", 'thousand', (52455, '52,455'), (7641, '7,641'), 'bar'),
   ('CHRISTMAS', '🎄', 'PH', "We decorate for a whole month!", "I start Christmas in September!", 'September', (1, 'DECEMBER'), (4, 'SEP–DEC'), 'icon'),
   ('BASKETBALL', '🏀', 'OP', "Basketball is life!", "Sorry… basketball was invented by a Canadian. James Naismith!", 'Naismith', (1891, 'INVENTED IT'), (0, 'LOVES IT'), 'icon')],
  ('OP', "Hmph. Salamat, Canada."), ('PH', "Sorry! Pancit later?")),
 ('Japan', 'jp', 'ja-JP-KeitaNeural', '#FF4D5E', '🗻', 'Nani?!',
  ("Canada. Your trains are slow.", "Sorry. But my lakes are huge!"),
  [('SIZE', '📏', 'OP', "Three hundred and seventy-eight thousand square kilometres.", "Sorry. I'm twenty-six times bigger!", 'bigger', (9984670, '9.98M KM²'), (377975, '377,975 KM²'), 'size'),
   ('PEOPLE', '👥', 'PH', "Forty-one million Canadians!", "One hundred and twenty-three million Japanese.", 'Japanese', (41.5, '41.5M'), (123.3, '123.3M'), 'bar'),
   ('LIVING LONGER', '❤️', 'PH', "Canadians live to eighty-two!", "Japanese live to eighty-four.", 'eighty', (81.7, '81.7'), (84.1, '84.1'), 'bar'),
   ('COASTLINE', '🏖️', 'OP', "Twenty-nine thousand kilometres of coast.", "Two hundred thousand! Sorry!", 'thousand', (202080, '202,080 KM'), (29751, '29,751 KM'), 'bar'),
   ('LAKES', '🏞️', 'OP', "I have Lake Biwa!", "Sorry. I have about sixty-two percent of the world's large lakes!", 'lakes', (62, '~62% OF LARGE LAKES'), (1, 'LAKE BIWA'), 'icon')],
  ('OP', "Arigato… you win."), ('PH', "Sorry! Good game!")),
 ('South Korea', 'kr', 'ko-KR-InJoonNeural', '#4F8CFF', '🎤', 'Aigoo!',
  ("Canada! Do you even know K-pop?", "Sorry… I know Justin Bieber!"),
  [('SIZE', '📏', 'OP', "One hundred thousand square kilometres.", "Sorry. I'm one hundred times bigger!", 'bigger', (9984670, '9.98M KM²'), (100410, '100,410 KM²'), 'size'),
   ('PEOPLE', '👥', 'PH', "Forty-one million Canadians!", "Fifty-one million Koreans!", 'Koreans', (41.5, '41.5M'), (51.7, '51.7M'), 'bar'),
   ('K-POP', '🎤', 'PH', "I have Bieber and Drake!", "I have BTS and BLACKPINK!", 'BLACKPINK', (0, 'BIEBER & DRAKE'), (1, 'BTS & BLACKPINK'), 'icon'),
   ('COASTLINE', '🏖️', 'OP', "Two thousand four hundred kilometres of coast!", "Two hundred thousand. Sorry!", 'thousand', (202080, '202,080 KM'), (2413, '2,413 KM'), 'bar'),
   ('SMARTPHONES', '📱', 'PH', "I made the BlackBerry!", "I make Samsung. The biggest phone brand on Earth!", 'Earth', (0, 'BLACKBERRY'), (1, 'SAMSUNG'), 'icon')],
  ('PH', "Sorry… that was close."), ('OP', "Annyeong! Better luck next time!")),
 ('Vietnam', 'vn', 'vi-VN-NamMinhNeural', '#E8333F', '☕', 'Trời ơi!',
  ("Canada! Want some real coffee?", "Sorry, I have Tim Hortons!"),
  [('SIZE', '📏', 'OP', "Three hundred and thirty-one thousand square kilometres.", "Sorry, I'm thirty times bigger!", 'bigger', (9984670, '9.98M KM²'), (331212, '331,212 KM²'), 'size'),
   ('PEOPLE', '👥', 'PH', "Forty-one million Canadians!", "One hundred and one million Vietnamese!", 'Vietnamese', (41.5, '41.5M'), (101, '101M'), 'bar'),
   ('COFFEE', '☕', 'PH', "Tim Hortons everywhere!", "I'm the world's second biggest coffee producer!", 'producer', (0, 'TIM HORTONS'), (2, '#2 PRODUCER'), 'icon'),
   ('MAPLE SYRUP', '🍁', 'OP', "We love sweet sauces!", "Sorry. I make about seventy percent of the world's maple syrup!", 'syrup', (70, '~70% OF THE WORLD'), (0, 'SWEET SAUCE'), 'icon'),
   ('MOTORBIKES', '🛵', 'PH', "I drive pickup trucks!", "I have over seventy million motorbikes!", 'motorbikes', (0, 'PICKUP TRUCKS'), (70, '70M+ MOTORBIKES'), 'icon')],
  ('PH', "Sorry… you win."), ('OP', "Cảm ơn! Coffee's on me!")),
 ('Pakistan', 'pk', 'ur-PK-AsadNeural', '#2DBE6C', '🏔️', 'Oh no!',
  ("Canada! My mountains are taller than your whole country!", "Sorry, that's not how size works!"),
  [('SIZE', '📏', 'OP', "Eight hundred and eighty-one thousand square kilometres!", "Sorry. I'm eleven times bigger!", 'bigger', (9984670, '9.98M KM²'), (881913, '881,913 KM²'), 'size'),
   ('PEOPLE', '👥', 'PH', "Forty-one million Canadians!", "Two hundred and fifty million Pakistanis!", 'Pakistanis', (41.5, '41.5M'), (251, '251M'), 'bar'),
   ('MOUNTAINS', '⛰️', 'PH', "Mount Logan, five thousand nine hundred and fifty-nine metres!", "K2. Eight thousand six hundred and eleven!", 'eleven', (5959, '5,959 M'), (8611, '8,611 M'), 'bar'),
   ('COASTLINE', '🏖️', 'OP', "One thousand kilometres of coast!", "Two hundred thousand! Sorry!", 'thousand', (202080, '202,080 KM'), (1046, '1,046 KM'), 'bar'),
   ('FRESH WATER', '🏞️', 'OP', "I have the Indus River!", "Sorry. I have about twenty percent of the world's fresh water!", 'water', (20, '~20%'), (1, 'INDUS RIVER'), 'icon')],
  ('OP', "Hmm. Shabash, Canada."), ('PH', "Sorry! Thank you!")),
 ('Indonesia', 'id', 'id-ID-ArdiNeural', '#F0435A', '🌋', 'Aduh!',
  ("Canada! I have seventeen thousand islands!", "Sorry… you're about to be surprised."),
  [('SIZE', '📏', 'OP', "One point nine million square kilometres!", "Sorry. I'm five times bigger!", 'bigger', (9984670, '9.98M KM²'), (1904569, '1.90M KM²'), 'size'),
   ('PEOPLE', '👥', 'PH', "Forty-one million Canadians!", "Two hundred and eighty-four million Indonesians!", 'Indonesians', (41.5, '41.5M'), (284, '284M'), 'bar'),
   ('ISLANDS', '🏝️', 'OP', "Seventeen thousand islands!", "Sorry. I have over fifty-two thousand!", 'thousand', (52455, '52,455'), (17380, '17,380'), 'bar'),
   ('VOLCANOES', '🌋', 'PH', "I have a few volcanoes!", "I have one hundred and twenty-seven active!", 'active', (0, 'A FEW'), (127, '127 ACTIVE'), 'icon'),
   ('COASTLINE', '🏖️', 'OP', "Fifty-four thousand kilometres of coast!", "Two hundred thousand! Sorry!", 'thousand', (202080, '202,080 KM'), (54716, '54,716 KM'), 'bar')],
  ('OP', "Wah… you surprised me."), ('PH', "Sorry! Told you!")),
 ('Thailand', 'th', 'th-TH-NiwatNeural', '#4F8CFF', '🐘', 'Oy!',
  ("Canada! Is it always cold over there?", "Sorry… yes. Minus sixty-three once!"),
  [('SIZE', '📏', 'OP', "Five hundred and thirteen thousand square kilometres!", "Sorry, I'm nineteen times bigger!", 'bigger', (9984670, '9.98M KM²'), (513120, '513,120 KM²'), 'size'),
   ('PEOPLE', '👥', 'PH', "Forty-one million Canadians!", "Seventy-one million Thais!", 'Thais', (41.5, '41.5M'), (71.7, '71.7M'), 'bar'),
   ('ELEPHANTS', '🐘', 'PH', "I have moose!", "The elephant is my national animal!", 'animal', (0, 'MOOSE'), (1, 'ELEPHANTS'), 'icon'),
   ('COASTLINE', '🏖️', 'OP', "Three thousand kilometres of coast!", "Two hundred thousand! Sorry!", 'thousand', (202080, '202,080 KM'), (3219, '3,219 KM'), 'bar'),
   ('TOURISM', '✈️', 'PH', "Tourists love Niagara Falls!", "Bangkok is the most visited city on Earth!", 'Earth', (0, 'NIAGARA FALLS'), (1, '#1 CITY: BANGKOK'), 'icon')],
  ('PH', "Sorry… that one hurt."), ('OP', "Khop khun! Come visit!")),
 ('Mongolia', 'mn', 'mn-MN-BataaNeural', '#E8333F', '🐎', 'Ai!',
  ("Canada! I have more horses than people!", "Sorry, I have more moose than… okay, let's just battle."),
  [('SIZE', '📏', 'OP', "One point five million square kilometres!", "Sorry. I'm six times bigger!", 'bigger', (9984670, '9.98M KM²'), (1564116, '1.56M KM²'), 'size'),
   ('PEOPLE', '👥', 'OP', "Three and a half million Mongolians!", "Forty-one million Canadians! Sorry!", 'Canadians', (41.5, '41.5M'), (3.5, '3.5M'), 'bar'),
   ('COLD CAPITAL', '🥶', 'PH', "Ottawa gets really cold!", "Ulaanbaatar is the coldest capital city on Earth!", 'Earth', (0, 'OTTAWA'), (1, 'ULAANBAATAR'), 'icon'),
   ('HORSES', '🐎', 'PH', "I have the RCMP horses!", "I have over four million horses!", 'horses', (0, 'RCMP HORSES'), (4, '4M+ HORSES'), 'icon'),
   ('COASTLINE', '🏖️', 'OP', "I have no coast at all.", "Two hundred thousand kilometres! Sorry!", 'kilometres', (202080, '202,080 KM'), (0.001, '0 KM'), 'bar')],
  ('OP', "Hmm. Strong, for a sorry country."), ('PH', "Sorry! Thank you!")),
 ('Singapore', 'sg', 'en-SG-WayneNeural', '#F0435A', '🦁', 'Alamak!',
  ("Canada! I'm small, but I'm rich!", "Sorry… final match. Let's go!"),
  [('SIZE', '📏', 'OP', "Seven hundred and thirty-five square kilometres!", "Sorry. I'm thirteen thousand times bigger!", 'bigger', (9984670, '9.98M KM²'), (735, '735 KM²'), 'size'),
   ('PEOPLE', '👥', 'OP', "Six million Singaporeans!", "Forty-one million Canadians!", 'Canadians', (41.5, '41.5M'), (6.0, '6.0M'), 'bar'),
   ('MONEY PER PERSON', '💰', 'PH', "About fifty-four thousand dollars per person!", "About ninety thousand!", 'thousand', (54, '≈ $54K'), (90, '≈ $90K'), 'bar'),
   ('AIRPORTS', '✈️', 'PH', "Toronto Pearson is busy!", "Changi has been voted the world's best airport many times!", 'times', (0, 'PEARSON'), (1, 'CHANGI'), 'icon'),
   ('COASTLINE', '🏖️', 'OP', "One hundred and ninety-three kilometres of coast!", "Two hundred thousand! Sorry, final win!", 'win', (202080, '202,080 KM'), (193, '193 KM'), 'bar')],
  ('OP', "Can lah… you win."), ('PH', "Sorry, Asia! That was fun!")),
]
FACTS = {'India': "Fun fact: India has twenty-two officially recognized languages.",
         'Philippines': "Fun fact: over one million people in Canada have Filipino roots.",
         'Japan': "Fun fact: Japan has more than five million vending machines.",
         'South Korea': "Fun fact: in South Korea, babies used to turn one year old on the day they were born.",
         'Vietnam': "Fun fact: Hang Son Doong in Vietnam is the largest cave on Earth.",
         'Pakistan': "Fun fact: Pakistan has five of the world's fourteen mountains over eight thousand metres.",
         'Indonesia': "Fun fact: Indonesia is home to the Komodo dragon, the biggest lizard on Earth.",
         'Thailand': "Fun fact: Bangkok's full ceremonial name is one of the longest city names in the world.",
         'Mongolia': "Fun fact: Mongolia is the most sparsely populated country on Earth.",
         'Singapore': "Fun fact: chewing gum sales are banned in Singapore."}
FACT_EMOJI = {'India': '🗣️', 'Philippines': '🇨🇦', 'Japan': '🥤', 'South Korea': '🎂', 'Vietnam': '🕳️', 'Pakistan': '⛰️', 'Indonesia': '🦎', 'Thailand': '🔤', 'Mongolia': '🏜️', 'Singapore': '🚫'}
NM = len(MATCHES)
OPP = {m + 1: d[0] for m, d in enumerate(MATCHES)}
COL = {'Canada': PH_C, **{d[0]: hexc(d[3])[:3] for d in MATCHES}}
VOICE = {'Canada': PHV, **{d[0]: (d[2], '+4%') for d in MATCHES}}
PH_REACT = ['Sorry, what?!', 'Sorry… no way!', 'Oh, sorry!', 'Sorry, eh?!', 'Sorry… that hurt.']
LINES = [('h1', 'Canada', "Asia! Sorry to bother you… but I'm here to win, eh."),
         ('h2', 'India', "Sorry? Wait until you meet all of Asia!"),
         ('h3', None, "Ten Asian countries. Five rounds each. Can Canada beat Asia, without saying sorry?")]
RD = {}; MRES = {}; RINFO = {}
for m, (nm, fl, vo, co, lm, react, (ins, rep), rounds, (s1, e1), (s2, e2)) in enumerate(MATCHES, 1):
    LINES.append((f'm{m}c', None, f"Match {['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'][m - 1]}: {'the ' if nm in ('UK', 'Netherlands') else ''}{nm if nm != 'UK' else 'U.K.'}!"))
    LINES += [(f'm{m}f', None, FACTS[nm]), (f'm{m}i1', nm, ins), (f'm{m}i2', 'Canada', rep)]
    ph_w = 0
    for r, (topic, icon, lf, la, lb, vw, phv, opv, kind) in enumerate(rounds, 1):
        a_sp, b_sp = ('Canada', nm) if lf == 'PH' else (nm, 'Canada')
        LINES += [(f'm{m}r{r}a', a_sp, la), (f'm{m}r{r}b', b_sp, lb)]
        win = b_sp; ph_w += win == 'Canada'
        LINES.append((f'm{m}r{r}x', a_sp, react if a_sp == nm else PH_REACT[(m + r) % len(PH_REACT)]))
        RD[(m, r)] = (topic, win, (f'm{m}r{r}b', vw)); RINFO[(m, r)] = (topic, icon, phv, opv, kind, a_sp)
    win_m = 'Canada' if ph_w >= 3 else nm; MRES[m] = (win_m, ph_w, 5 - ph_w)
    sc = f"{max(ph_w, 5 - ph_w)} to {min(ph_w, 5 - ph_w)}"
    LINES.append((f'm{m}w', None, f"{'Canada' if win_m == 'Canada' else ('The ' + nm if nm in ('UK', 'Netherlands') else nm)} wins, {sc}!".replace('The UK', 'The U.K.')))
    LINES += [(f'm{m}e1', nm if s1 == 'OP' else 'Canada', e1), (f'm{m}e2', nm if s2 == 'OP' else 'Canada', e2)]
TW = sum(1 for m in MRES if MRES[m][0] == 'Canada'); TL = NM - TW
NUMW = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
LINES.append(('cta', None, f"Canada finishes with {NUMW[TW]} wins and {NUMW[TL]} losses! And it said sorry a lot. Who should Canada fight next? Comment below, and subscribe for episode two!"))
SPK = {k: s for k, s, _ in LINES}
C.BEATS = [(k, s, None, None, None, None, None) for k, _, s in LINES]; C.HOOK = ('h1', 'h2', 'h3')
C.SAY = {None: {'Naismith': 'Naysmith', 'Lytton': 'Litton', 'Phalodi': 'Pha-lo-dee', 'Ulaanbaatar': 'Oolan-bah-tar', 'Changi': 'Chang-ee', 'Siargao': 'Shar-gow', 'Nazaré': 'Nazareh', 'Lapulapu': 'Lapu-Lapu', 'Teide': 'Tay-deh', 'Gilas': 'Gee-las', 'Malbork': 'Mal-bork', 'Santo': 'Santo'}}
C.HOT = ('philippines', 'europe', 'wins', 'bigger', 'match', 'million', 'earth', 'comment', 'subscribe', 'gods', 'filipinos')
C.TAIL_OVERRIDE = {'h1': 0.12, 'h2': 0.2, 'h3': 0.5, 'cta': 3.8, **{f'm{m}c': 0.25 for m in range(1, NM + 1)}, **{f'm{m}f': 0.4 for m in range(1, NM + 1)}, **{f'm{m}w': 0.9 for m in range(1, NM + 1)},
                   **{k: 0.25 for k, s, _ in LINES if s and k[0] == 'm'}, **{RD[x][2][0]: 1.3 for x in RD}, **{f'm{m}r{r}x': 0.35 for m in range(1, NM + 1) for r in range(1, 6)}}
bt, w = C.bt, C.w
VOICE_OF = {C.say(k, s): (VOICE[sp] if sp else NARR) for k, sp, s in LINES}
class MultiVoice(C.WordVoice):
    def get(self, text):
        import time
        C.VOICE, C.RATE = VOICE_OF.get(text, NARR)
        for attempt in range(6):  # the speech service throttles now and then
            try: return super().get(text)
            except Exception:
                if attempt == 5: raise
                time.sleep(2 + attempt * 2)
G = None
SHORT = {}

def inside(pt, rs):
    x, y = pt; c = False
    for r in rs:
        xs, ys = r[:, 0], r[:, 1]; xj, yj = np.roll(xs, 1), np.roll(ys, 1)
        hit = ((ys > y) != (yj > y)) & (x < (xj - xs) * (y - ys) / np.where(yj - ys == 0, 1e-12, yj - ys) + xs)
        c ^= bool(np.count_nonzero(hit) % 2)
    return c
EU_NAMES = ['India', 'Philippines', 'Japan', 'South Korea', 'Vietnam', 'Pakistan', 'Indonesia', 'Thailand', 'Mongolia', 'Singapore']
EU_BG = ['China', 'Kazakhstan', 'Myanmar', 'Laos', 'Cambodia', 'Malaysia', 'North Korea', 'Taiwan', 'Bangladesh', 'Nepal', 'Afghanistan', 'Iran', 'Sri Lanka', 'Bhutan',
         'Uzbekistan', 'Kyrgyzstan', 'Tajikistan', 'Turkmenistan', 'Brunei', 'Timor-Leste', 'Papua New Guinea']
GEONAME = {'UK': 'United Kingdom'}
CLIP = {'Norway': (4, 32, 57, 72), 'Denmark': (7, 16, 54, 58.5), 'France': (-6, 10, 41, 52), 'Spain': (-10, 5, 35, 44.5), 'Portugal': (-10, -6, 36.5, 42.5), 'Netherlands': (3, 8, 50.5, 54), 'Greece': (19, 30, 34, 42), 'Italy': (6, 19, 36, 47.5),
        'United Kingdom': (-9, 2, 49, 61), 'Germany': (5, 16, 47, 55.5), 'Poland': (14, 25, 49, 55), 'Philippines': (116, 127, 4, 22)}
PHFLAG = {}
class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        def R(n):
            box = CLIP.get(n)
            rs = [r for r in rings(cf[n]['geometry']) if len(r) > 3]
            if box: rs = [r for r in rs if box[0] < r[:, 0].mean() < box[1] and box[2] < r[:, 1].mean() < box[3]]
            if n == 'Russia': rs = [r for r in rs if r[:, 0].mean() < 45]
            return rs
        self.ref = {'EU': (110.0, 22.0)}
        eu = {n: local(R(n), 110.0, 22.0) for n in EU_NAMES + EU_BG if n in cf}
        allp = np.concatenate([np.concatenate(v) for k, v in eu.items() if k in EU_NAMES]); x0, x1, y0, y1 = allp[:, 0].min(), allp[:, 0].max(), allp[:, 1].min(), allp[:, 1].max()
        self.off = {'EU': np.array([(x0 + x1) / 2, (y0 + y1) / 2])}; self.eu = {k: [r - self.off['EU'] for r in v] for k, v in eu.items()}
        self.shape = {}
        for n in EU_NAMES + ['Canada']:
            lon0 = float(np.mean([r[:, 0].mean() for r in R(n)])); lat0 = float(np.mean([r[:, 1].mean() for r in R(n)]))
            pr = local(R(n), lon0, lat0); c = np.concatenate(pr); mid = np.array([(c[:, 0].min() + c[:, 0].max()) / 2, (c[:, 1].min() + c[:, 1].max()) / 2])
            self.shape[n] = [r - mid for r in pr]
        for nm, f in [('Canada', 'ca')] + [(m[0], m[1]) for m in MATCHES]: B.FL[nm] = cairo.ImageSurface.create_from_png(os.path.join(d, 'flags', f + '.png'))
        s0 = B.FL['Canada']; u = cairo.ImageSurface(cairo.FORMAT_ARGB32, s0.get_width(), s0.get_height()); c = cairo.Context(u); c.translate(0, s0.get_height()); c.scale(1, -1); c.set_source_surface(s0, 0, 0); c.paint()
        PHFLAG['peace'], PHFLAG['war'] = s0, u
    def p(self, k, lon, lat): return local([np.array([[lon, lat]], float)], *self.ref[k])[0][0] - self.off[k]
def extent(rs): c = np.concatenate(rs); return c[:, 0].max() - c[:, 0].min(), c[:, 1].max() - c[:, 1].min()

def at(key, word, n=0): return w(key, word, n)
def mi_of(key):
    if key[0] == 'm':
        j = 1
        while key[j].isdigit(): j += 1
        return int(key[1:j])
    return 0
CUR = [1]
def col_of(name): return COL.get(name, WHITE)
def rival_of(name): return OPP[CUR[0]] if name == 'Canada' else 'Canada'
def side_of(name): return 'A' if name == 'Canada' else 'U'

# ---------- shared drawing ----------
def cam(cr, z=1.0, tilt=0.0, fx=540, fy=960):
    cr.translate(540, 960); cr.rotate(tilt); cr.scale(z, z); cr.translate(-fx, -fy)
def push(t, a, b, z0, z1): return lerp(z0, z1, ease_out(prog(t, a, b)))
def arena(cr, t, tint=None):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.03, 0.1); g.add_color_stop_rgb(1, 0.1, 0.08, 0.2); cr.set_source(g); cr.paint()
    for col, x0 in ((A_C, 0), (U_C, W)):
        c = tint or col; g = cairo.RadialGradient(x0, 1100, 50, x0, 1100, 900); g.add_color_stop_rgba(0, *c, 0.36); g.add_color_stop_rgba(1, *c, 0); cr.set_source(g); cr.paint()
    rng = np.random.default_rng(3)
    for _ in range(90):
        x, y, s = rng.uniform(0, W), rng.uniform(0, 700), rng.uniform(0.8, 2.4); cr.new_path(); cr.arc(x, y, s, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25 + 0.25 * math.sin(t * 2 + x)); cr.fill()
def ocean(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.1, 0.22); g.add_color_stop_rgb(1, 0.05, 0.2, 0.36); cr.set_source(g); cr.paint()
def nametag(cr, name, x, y, col):
    nm = SHORT.get(name, name.upper()); wd = tw(cr, nm, 42)
    rrect(cr, x - wd / 2 - 30, y - 42, wd + 60, 80, 40); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    ptext(cr, nm, x, y + 14, 42, INK, 1, sw=0, shadow=False)
def bubble(cr, t, b, tail_x, y=520, size=56):
    if len(' '.join(b['tokens'])) > 70: size = min(size, 50)
    toks = b['tokens']; n = sum(1 for s, e, _ in b['words'] if s <= t + 0.03); n = min(len(toks), max(1, round(n * len(toks) / max(1, len(b['words'])))))
    lines, cur = [], []
    for tk in toks:
        if cur and tw(cr, ' '.join(cur + [tk]), size, 'Poppins ExtraBold') > 860: lines.append(cur); cur = []
        cur.append(tk)
    lines.append(cur)
    lh = size * 1.29; bw = max(tw(cr, ' '.join(l), size, 'Poppins ExtraBold') for l in lines) + 90; bh = len(lines) * lh + 56
    k = pop_k(t, b['l0'] - 0.1, 0.22); cr.save(); cr.translate(540, y); cr.scale(k, k); cr.translate(-540, -y)
    tx = clamp(tail_x, 540 - bw / 2 + 70, 540 + bw / 2 - 70)
    cr.new_path(); cr.move_to(tx - 30, y + bh / 2 - 6); cr.line_to(lerp(tx, tail_x, 0.4), y + bh / 2 + 62); cr.line_to(tx + 36, y + bh / 2 - 6); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(7); cr.stroke()
    rrect(cr, 540 - bw / 2, y - bh / 2, bw, bh, 42); cr.set_source_rgb(1, 1, 1); cr.fill_preserve(); cr.set_source_rgb(0.02, 0.02, 0.05); cr.set_line_width(7); cr.stroke()
    cr.rectangle(tx - 22, y + bh / 2 - 12, 50, 12); cr.set_source_rgb(1, 1, 1); cr.fill()
    i = 0
    for li, l in enumerate(lines):
        xx = 540 - tw(cr, ' '.join(l), size, 'Poppins ExtraBold') / 2; yy = y - bh / 2 + 28 + size * 0.93 + li * lh
        for tk in l:
            ptext(cr, tk, xx, yy, size, INK if i < n else (0.8, 0.8, 0.85), 1, fam='Poppins ExtraBold', anchor='l', sw=0, shadow=False); xx += tw(cr, tk + ' ', size, 'Poppins ExtraBold'); i += 1
    cr.restore()
def hop_of(t, b):
    h = 0.0
    for s, e, _ in b['words']:
        if s <= t < s + 0.26: h = max(h, math.sin(math.pi * (t - s) / 0.26))
    return h

def bar(cr, x, base, val, vmax, hmax, k, col, name, lab, wd=190):
    hh = max(8, hmax * val / vmax * k); rrect(cr, x - wd / 2, base - hh, wd, hh, 18); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
    ptext(cr, lab, x, base - hh - 22, 50, WHITE, clamp(k * 2), sw=8); ptext(cr, name, x, base - 26, 34, INK, 1, fam='Poppins ExtraBold', sw=0, shadow=False)
    return base - hh
def emopops(cr, t, key, items, y=930, size=170):
    for i, (em, word) in enumerate(items):
        tt = at(key, word) - 0.1
        if t < tt: continue
        x = 540 + (i - (len(items) - 1) / 2) * 290; emoji(cr, em, x, y - abs(math.sin(t * 4 + i)) * 14, size * pop_k(t, tt, 0.3), 1, rot=0.12 * math.sin(t * 3 + i))




def set_philippines(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.35, 0.7, 0.98); g.add_color_stop_rgb(0.55, 0.85, 0.93, 1.0); g.add_color_stop_rgb(0.62, 0.1, 0.65, 0.75); g.add_color_stop_rgb(1, 0.04, 0.35, 0.55); cr.set_source(g); cr.paint()
    cr.new_path(); cr.arc(800, 760, 120, 0, 2 * math.pi); cr.set_source_rgba(1, 0.92, 0.5, 0.95); cr.fill()
    for j in range(3):  # limestone islets
        x = 200 + j * 300; cr.new_path(); cr.move_to(x - 130, 1180); cr.curve_to(x - 120, 960 - j * 40, x + 60, 930 - j * 30, x + 120, 1180); cr.close_path(); cr.set_source_rgb(0.18, 0.45, 0.3); cr.fill()
    for j in range(16):
        y = 1200 + j * 26; ph = (t * 0.4 + j * 0.37) % 1; cr.rectangle(60 + 420 * math.sin(j * 1.7) + 80 * ph, y, 140, 4); cr.set_source_rgba(1, 1, 1, 0.35); cr.fill()
    cr.new_path(); cr.move_to(-200, 1420); cr.curve_to(300, 1380, 700, 1400, 1300, 1430); cr.line_to(1300, 2100); cr.line_to(-200, 2100); cr.close_path(); cr.set_source_rgb(0.98, 0.92, 0.78); cr.fill()
    for x, lean in ((90, 1), (990, -1)):
        cr.new_path(); cr.move_to(x - 10, 1440); cr.curve_to(x, 1250, x + lean * 40, 1100, x + lean * 70, 980); cr.line_to(x + lean * 70 + 16, 990); cr.curve_to(x + lean * 50, 1110, x + 18, 1250, x + 12, 1440); cr.close_path(); cr.set_source_rgb(0.45, 0.32, 0.2); cr.fill()
        for k in range(6):
            a = -math.pi / 2 + (k - 2.5) * 0.55 + 0.05 * math.sin(t * 1.5 + k); L = 150
            cr.new_path(); cr.move_to(x + lean * 75, 985); cr.curve_to(x + lean * 75 + math.cos(a) * L * 0.5, 985 + math.sin(a) * L * 0.3 - 40, x + lean * 75 + math.cos(a) * L, 985 + math.sin(a) * L * 0.4 + 20, x + lean * 75 + math.cos(a) * L * 1.1, 985 + 60)
            cr.set_source_rgb(0.12, 0.5, 0.25); cr.set_line_width(22); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
def set_canada(cr, t, zoom=1.0):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.02, 0.04, 0.12); g.add_color_stop_rgb(0.6, 0.06, 0.16, 0.26); g.add_color_stop_rgb(1, 0.1, 0.12, 0.18); cr.set_source(g); cr.paint()
    for j, col in enumerate(((0.2, 1, 0.6), (0.5, 0.4, 1))):  # aurora
        cr.new_path(); cr.move_to(-200, 420 + j * 90)
        for x in range(-200, 1300, 60): cr.line_to(x, 420 + j * 90 + 70 * math.sin(x / 170 + t * 0.7 + j))
        cr.line_to(1300, 0); cr.line_to(-200, 0); cr.close_path(); g = cairo.LinearGradient(0, 200, 0, 560); g.add_color_stop_rgba(0, *col, 0); g.add_color_stop_rgba(1, *col, 0.28); cr.set_source(g); cr.fill()
    for k, (yb, col) in enumerate(((1250, (0.12, 0.16, 0.26)), (1350, (0.07, 0.1, 0.17)))):
        cr.new_path(); cr.move_to(-200, H)
        for x in range(-200, 1400, 120): cr.line_to(x, yb - 260 - 160 * abs(math.sin(x * 0.011 + k * 2)))
        cr.line_to(1400, H); cr.close_path(); cr.set_source_rgb(*col); cr.fill()
    rng = np.random.default_rng(2)
    for _ in range(26):
        x, s = rng.uniform(-100, 1180), rng.uniform(90, 200); y = 1420 + rng.uniform(0, 160)
        cr.new_path(); cr.move_to(x, y - s * 1.6); cr.line_to(x - s * 0.45, y); cr.line_to(x + s * 0.45, y); cr.close_path(); cr.set_source_rgb(0.03, 0.08, 0.06); cr.fill()
    cr.rectangle(-200, 1560, 1500, 600); cr.set_source_rgb(0.86, 0.9, 0.96); cr.fill()
    for j in range(40):
        ph = (t * 0.12 + j * 0.37) % 1; cr.new_path(); cr.arc((j * 97 + 30 * math.sin(t + j)) % 1100, ph * 1900, 4, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.7); cr.fill()
def mview(cr, t, k, ctr0, ctr1, s0, s1, t0, t1, land, fy=900, rot=0.0):
    e = ease_io(prog(t, t0, t1)); kx, ky = [lerp(a, b_, e) for a, b_ in zip(ctr0, ctr1)]; s = lerp(s0, s1, e)
    ocean(cr, t); cr.save(); cr.translate(540, fy); cr.rotate(rot); cr.translate(-540, -fy)
    cx, cy = 540 - kx * s, fy + ky * s
    km_shape(cr, G.nb[k], cx, cy, s, (0.32, 0.36, 0.42), 1, lw=1, edge=(0.08, 0.1, 0.16))
    km_shape(cr, G.c[k], cx, cy, s, land, 1, lw=1.6, edge=(0.03, 0.04, 0.1))
    return cx, cy, s
def endmap(cr): cr.restore()
def kpt(k, lon, lat, cx, cy, s): p = G.p(k, lon, lat); return cx + p[0] * s, cy - p[1] * s
def label(cr, txt, x, y, size, col, a=1.0): ptext(cr, txt, x, y, size, col, a, sw=size * 0.14)
def pin(cr, x, y, t, t0, col):
    col = tuple(col[:3])
    if t < t0: return
    for j in range(3):
        ph = ((t - t0) * 0.8 + j / 3) % 1; cr.new_path(); cr.arc(x, y, 14 + 70 * ph, 0, 2 * math.pi); cr.set_source_rgba(*col, 1 - ph); cr.set_line_width(5); cr.stroke()
    cr.new_path(); cr.arc(x, y, 14 * pop_k(t, t0, 0.3), 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(3); cr.stroke()
AU_LAND, PH_LAND = (0.86, 0.5, 0.24), (0.55, 0.8, 0.45)
def rail(cr, pts, k, col, wd):
    if k <= 0 or len(pts) < 2: return
    seg = [math.hypot(b_[0] - a[0], b_[1] - a[1]) for a, b_ in zip(pts, pts[1:])]; tot = sum(seg); L = tot * k
    cr.new_path(); cr.move_to(*pts[0]); done = 0; end = pts[0]
    for (a, b_), sl in zip(zip(pts, pts[1:]), seg):
        if done + sl >= L: f = (L - done) / max(sl, 1e-9); end = (lerp(a[0], b_[0], f), lerp(a[1], b_[1], f)); cr.line_to(*end); break
        cr.line_to(*b_); done += sl; end = b_
    cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_source_rgba(*col, 0.3); cr.set_line_width(wd * 3); cr.stroke_preserve(); cr.set_source_rgb(*col); cr.set_line_width(wd); cr.stroke(); return end
# ---------- sets ----------
def set_europe(cr, t, name):
    col = col_of(name); lm = next(d[4] for d in MATCHES if d[0] == name)
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *[c * 0.35 for c in col]); g.add_color_stop_rgb(0.55, *[0.55 + 0.4 * c for c in col]); g.add_color_stop_rgb(1, 0.25, 0.22, 0.25); cr.set_source(g); cr.paint()
    cr.new_path(); cr.arc(820, 640, 130, 0, 2 * math.pi); cr.set_source_rgba(1, 0.95, 0.8, 0.8); cr.fill()
    pal = [(0.95, 0.85, 0.7), (0.85, 0.55, 0.45), (0.9, 0.75, 0.5), (0.7, 0.75, 0.85), (0.92, 0.9, 0.85)]
    for k in range(9):
        x = -60 + k * 135; h = 360 + 90 * math.sin(k * 2.3 + len(name)); cr.rectangle(x, 1340 - h, 135, h); cr.set_source_rgb(*pal[(k + len(name)) % 5]); cr.fill()
        cr.new_path(); cr.move_to(x - 4, 1340 - h); cr.line_to(x + 67, 1340 - h - 80); cr.line_to(x + 139, 1340 - h); cr.close_path(); cr.set_source_rgb(0.55, 0.25, 0.2); cr.fill()
        for r in range(3):
            for c_ in range(2): rrect(cr, x + 28 + c_ * 52, 1340 - h + 40 + r * 95, 28, 50, 12); cr.set_source_rgba(0.25, 0.3, 0.4, 0.8); cr.fill()
    for j in range(16):  # bunting in team colour
        x = j * 72; y = 760 + 30 * math.sin(j * 0.45); cr.new_path(); cr.move_to(x, y); cr.line_to(x + 60, y + 4); cr.line_to(x + 30, y + 60); cr.close_path(); cr.set_source_rgb(*(col if j % 2 else (1, 1, 1))); cr.fill()
    cr.rectangle(-200, 1330, 1500, 800); cr.set_source_rgb(0.6, 0.55, 0.52); cr.fill()
    for j in range(18): cr.rectangle(j * 70 - 20, 1370 + (j % 3) * 55, 50, 22); cr.set_source_rgba(0.45, 0.4, 0.38, 0.7); cr.fill()
    emoji(cr, lm, 880, 1180 + 10 * math.sin(t * 2), 170, 1, rot=0.05 * math.sin(t))
def set_of(name, cr, t): set_canada(cr, t) if name == 'Canada' else set_europe(cr, t, name)

# ---------- shots ----------
def sgn_of(name): return -1 if name == 'Canada' else 1
def sh_close(cr, t, b, name, t0, t1, mood='happy'):
    sgn = sgn_of(name); h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.12), 0.06 * sgn * (1 if sum(map(ord, b['key'])) % 2 else -1), 540, 1100); set_of(name, cr, t)
    ball(cr, name, 540, 1230 - h * 46, 330, mood, 0.05 * h, -sgn * 0.4); cr.restore()
    bubble(cr, t, b, 540, 540); nametag(cr, name, 540, 1640, col_of(name))
def sh_low(cr, t, b, name, t0, t1, mood='happy'):
    h = hop_of(t, b)
    cr.save(); cam(cr, push(t, t0, t1, 1.15, 1.02), 0.0, 540, 760); cr.translate(0, 300); set_of(name, cr, t); cr.restore()
    cr.save(); cr.translate(540, 1500 - h * 30); cr.scale(1.0, 1.08); ball(cr, name, 0, 0, 470, mood, 0.04 * h, 0); cr.restore()
    bubble(cr, t, b, 540, 520); nametag(cr, name, 540, 1830, col_of(name))
def sh_ots(cr, t, b, name, t0, t1, mood='happy'):
    sgn = sgn_of(name); h = hop_of(t, b); rv = rival_of(name)
    cr.save(); cam(cr, push(t, t0, t1, 1.0, 1.06), 0.02 * sgn, 540 + lerp(0, -sgn * 40, prog(t, t0, t1)), 1000); set_of(name, cr, t)
    ball(cr, name, 540 + sgn * 150, 1080 - h * 36, 210, mood, 0.05 * h, -sgn * 0.6); ball(cr, rv, 540 - sgn * 470, 1700, 560, 'angry', 0, sgn * 0.9); cr.restore()
    cr.set_source_rgba(0, 0, 0, 0.18); cr.paint(); bubble(cr, t, b, 540 + sgn * 150, 520); nametag(cr, name, 540 + sgn * 150, 1340, col_of(name))
def sh_two(cr, t, b, name, t0, t1, mood='happy'):
    h = hop_of(t, b); rv = rival_of(name); pan = lerp(-50, 50, prog(t, t0, t1)) * sgn_of(name)
    cr.save(); cam(cr, 1.0, 0.0, 540 + pan, 1000); set_of(name, cr, t)
    for n, x in (('Canada', 290), (OPP[CUR[0]], 790)):
        hh = h if n == name else 0; ball(cr, n, x, 1300 - hh * 40, 220, mood if n == name else 'angry', 0.05 * hh, 0.8 if n == 'Canada' else -0.8)
    cr.restore(); sx = (290 if name == 'Canada' else 790) - pan; bubble(cr, t, b, sx, 560); nametag(cr, name, sx, 1600, col_of(name))
def sh_react(cr, t, b, name, t0, t1, mood='shock'):
    k = ease_out(prog(t, t0, t0 + 0.25)); sx, sy = shake(t, t0, 22, 0.4)
    cr.save(); cam(cr, lerp(1.25, 1.08, k), -0.06 * sgn_of(name), 540 + sx, 1080 + sy); set_of(name, cr, t); ball(cr, name, 540, 1150, 360, 'shock', 0, 0); cr.restore()
    ptext(cr, '?!', 860, 760, 170, GOLD, pop_k(t, t0 + 0.05), sw=14); nametag(cr, name, 540, 1640, col_of(name))

# ---------- stat scene ----------
def stat_scene(cr, t, m, r, stage_t):
    topic, icon, phv, opv, kind, first = RINFO[(m, r)]; op = OPP[m]; vt = tv_of(m, r); win = RD[(m, r)][1]
    arena(cr, t, col_of(op) if win != 'Canada' else PH_C)
    label(cr, f'ROUND {r} · {topic}', 540, 470, fit(cr, f'ROUND {r} · {topic}', 70, 980), WHITE); emoji(cr, icon, 540, 590, 90, 1)
    ta, tb = bt(f'm{m}r{r}a'), bt(f'm{m}r{r}b')
    show = {first: t >= ta['start'] + 0.15, ('Canada' if first != 'Canada' else op): t >= tb['start'] + 0.15}
    cols = (('Canada', 290, phv), (op, 790, opv))
    if kind == 'size':
        GS = lambda n: G.shape[GEONAME.get(n, n)]
        mx = max(max(extent(GS(n))) for n, _, _ in cols); s = 420 / mx
        for n, x, (v, lab) in cols:
            if not show[n]: continue
            k = ease_out(prog(t, (ta if n == first else tb)['start'] + 0.15, (ta if n == first else tb)['start'] + 0.6))
            km_shape(cr, GS(n), x, 1000, s * k, col_of(n), 1, fill=0.9, lw=3, edge=INK)
            ptext(cr, lab, x, 1290, fit(cr, lab, 46, 470), WHITE, k, sw=7)
        ptext(cr, 'SAME SCALE', 540, 1340, 26, WHITE, 0.6, fam='Poppins ExtraBold', sw=4)
    elif kind in ('bar', 'young', 'old'):
        vmax = max(phv[0], opv[0]) or 1
        for n, x, (v, lab) in cols:
            if not show[n]: continue
            k = ease_out(prog(t, (ta if n == first else tb)['start'] + 0.15, (ta if n == first else tb)['start'] + 0.9))
            frac = (v / vmax) if kind == 'bar' else ((1 - (v - min(phv[0], opv[0])) / (abs(phv[0] - opv[0]) or 1)) * 0.6 + 0.4 if kind == 'young' else (1 - (v - 1096) / 600) * 0.6 + 0.4)
            hh = max(12, 520 * frac * k); rrect(cr, x - 120, 1260 - hh, 240, hh, 22); cr.set_source_rgb(*col_of(n)); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
            ptext(cr, lab, x, 1260 - hh - 26, fit(cr, lab, 64, 440), WHITE, clamp(k * 2), sw=8)
        if kind == 'young': ptext(cr, 'MEDIAN AGE · YOUNGER WINS', 540, 1330, 30, WHITE, 0.7, fam='Poppins ExtraBold', sw=5)
        if kind == 'old': ptext(cr, 'FOUNDED · OLDER WINS', 540, 1330, 30, WHITE, 0.7, fam='Poppins ExtraBold', sw=5)
    else:
        for n, x, (v, lab) in cols:
            if not show[n]: continue
            k = pop_k(t, (ta if n == first else tb)['start'] + 0.15, 0.3)
            rrect(cr, x - 230, 870, 460, 300, 40); cr.set_source_rgba(*col_of(n), 0.35); cr.fill()
            emoji(cr, icon, x, 960, 120 * k, 1); ptext(cr, lab, x, 1120, fit(cr, lab, 52, 420), WHITE, k, sw=8)
    for n, x, _ in cols:
        ball(cr, n, x, 1420, 75, ('happy' if t < vt else ('happy' if n == win else 'shock')), 0, 0)
        if t >= vt and n == win: emoji(cr, '👑', x, 1320, 90 * pop_k(t, vt, 0.3), 1)
def tv_of(m, r): return w(*RD[(m, r)][2])
def verdict(cr, t, m, r):
    tv = tv_of(m, r); win = RD[(m, r)][1]
    if t < tv: return
    col = col_of(win); f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); txt = f"{'CANADA' if win == 'Canada' else win.upper()} WINS ROUND {r}"
    cr.save(); cr.translate(540, 1560); cr.rotate(-0.04 if win == 'Canada' else 0.04); cr.scale(s, s); sz = fit(cr, txt, 60, 880); wd = tw(cr, txt, sz)
    rrect(cr, -wd / 2 - 40, -74, wd + 80, 108, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke(); ptext(cr, txt, 0, 4, sz, INK, 1, sw=0, shadow=False); cr.restore()

def shot_list(key):
    b = bt(key); m = mi_of(key); d = b['end'] - b['start']
    if key.endswith('a') and 'r' in key[1:]: return [(b['start'], 'close'), (b['start'] + 0.42 * d, 'stat')]
    if key.endswith('b') and 'r' in key[1:]:
        r = int(key.split('r')[1][0]); return [(b['start'], 'two'), (b['start'] + 0.3 * d, 'stat'), (tv_of(m, r) + 0.75, 'react')]
    return [(b['start'], 'close')]
SHOT = {'close': sh_close, 'low': sh_low, 'ots': sh_ots, 'two': sh_two}
def draw_line(cr, t, key):
    b = bt(key); name = SPK[key]; m = mi_of(key); sl = shot_list(key)
    j = max(i for i, (s, _) in enumerate(sl) if s <= t or i == 0); t0 = sl[j][0]; t1 = sl[j + 1][0] if j + 1 < len(sl) else b['end']; sh = sl[j][1]
    if sh == 'stat':
        r = int(key.split('r')[1][0]); stat_scene(cr, t, m, r, t0); verdict(cr, t, m, r)
        x = 160 if name == 'Canada' else 920; h = hop_of(t, b); C.draw_captions(cr, t, 1760)
    elif sh == 'react':
        r = int(key.split('r')[1][0]); loser = RINFO[(m, r)][5]; sh_react(cr, t, b, loser, t0, t1)
    else:
        kind = key.split('r')[-1][-1] if 'r' in key[1:] else key[-2:]
        if key.endswith('x'): sh_close(cr, t, b, name, t0, t1, 'angry')
        elif key.endswith('i1'): sh_low(cr, t, b, name, t0, t1, 'angry')
        elif key.endswith('i2'): sh_ots(cr, t, b, name, t0, t1, 'happy')
        elif key.endswith('e1') or key.endswith('e2'): (sh_close if key.endswith('e1') else sh_two)(cr, t, b, name, t0, t1, 'happy' if name == MRES[m][0] else 'angry')
        elif key.endswith('a'): (sh_close if (m + int(key.split('r')[1][0])) % 2 else sh_low)(cr, t, b, name, t0, t1)
        else: SHOT[sh](cr, t, b, name, t0, t1)
    f = 1 - prog(t, t0, t0 + 0.1)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.45 * f); cr.paint()
    streaks(cr, 1 - ease_out(prog(t, t0, t0 + 0.16)))

# ---------- HUD, cards, results ----------
def match_score(t, m): return sum(t >= tv_of(m, r) and RD[(m, r)][1] == 'Canada' for r in range(1, 6)), sum(t >= tv_of(m, r) and RD[(m, r)][1] != 'Canada' for r in range(1, 6))
def round_now(t, m):
    for r in range(5, 0, -1):
        if t >= bt(f'm{m}r{r}a')['start']: return r
    return 0
def tour_done(t): return [m for m in MRES if t >= bt(f'm{m}w')['start'] + 0.3]
def tour_strip(cr, t, y, size=44, a=1.0):
    done = tour_done(t)
    for m in range(1, NM + 1):
        x = 540 + (m - (NM + 1) / 2) * (size * 2.2); op = OPP[m]; ball(cr, op, x, y, size, 'happy', 0, 0)
        if m in done:
            won = MRES[m][0] == 'Canada'; cr.new_path(); cr.arc(x, y, size + 6, 0, 2 * math.pi); cr.set_source_rgb(*((0.18, 0.75, 0.42) if won else (0.94, 0.26, 0.35))); cr.set_line_width(8); cr.stroke()
            ptext(cr, 'W' if won else 'L', x, y + size + 34, 30, (0.18, 0.75, 0.42) if won else (0.94, 0.26, 0.35), a, sw=5)
_SORRY = []
def sorry_times():
    if not _SORRY:
        for bb in C.TL['beats']:
            if SPK.get(bb['key']) == 'Canada':
                for s_, e_, x_ in bb['words']:
                    if x_.lower().startswith('sorry'): _SORRY.append(s_)
        _SORRY.sort()
    return _SORRY
def sorry_meter(cr, t, y=372):
    st = sorry_times(); n = sum(1 for s_ in st if s_ <= t); last = max([s_ for s_ in st if s_ <= t] or [-9]); k = pop_k(t, last, 0.35) if t - last < 0.5 else 1.0
    cr.save(); cr.translate(540, y); cr.scale(k, k); rrect(cr, -210, -34, 420, 66, 33); cr.set_source_rgb(*PH_C); cr.fill()
    ptext(cr, f'SORRY METER: {n}', 30, 14, 34, WHITE, 1, sw=0, shadow=False); cr.restore(); emoji(cr, '🍁', 540 - 170 * k, y, 46 * k, 1)
def hud(cr, t, m):
    ps, os_ = match_score(t, m); op = OPP[m]; r = round_now(t, m)
    rrect(cr, 30, 120, 1020, 200, 44); cr.set_source_rgba(0.03, 0.04, 0.1, 0.88); cr.fill()
    for n, x, sc in (('Canada', 230, ps), (op, 850, os_)):
        ball(cr, n, 78 if n == 'Canada' else 1002, 220, 40, 'happy', 0, 0)
        ptext(cr, 'CANADA' if n == 'Canada' else op.upper(), x, 190, fit(cr, n.upper(), 34, 260), col_of(n), 1, sw=0, shadow=False)
        ptext(cr, str(sc), x, 290, 84, WHITE, 1, sw=0, shadow=False)
    ptext(cr, f'MATCH {m}/{NM}', 540, 185, 32, GOLD, 1, fam='Poppins ExtraBold', sw=0, shadow=False); ptext(cr, f'ROUND {r}/5' if r else 'FIRST TO 3', 540, 240, 30, WHITE, 0.85, fam='Poppins ExtraBold', sw=0, shadow=False)
    ptext(cr, '—', 540, 300, 50, WHITE, 0.8, sw=0, shadow=False)
    sorry_meter(cr, t)
def card(cr, t, m):
    b = bt(f'm{m}c'); k = ease_out(prog(t, b['start'], b['start'] + 0.25)); op = OPP[m]
    cr.save(); cam(cr, 1.0 + 0.05 * prog(t, b['start'], b['end']), -0.04); cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for j, col in enumerate((PH_C, col_of(op))):
        cr.new_path(); cr.move_to(-200 if j == 0 else 1280, 400); cr.line_to(540 + (-40 if j == 0 else 40), 960); cr.line_to(-200 if j == 0 else 1280, 1520); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    s = lerp(2.2, 1, k); cr.save(); cr.translate(540, 480); cr.scale(s, s); ptext(cr, 'FINAL MATCH' if m == NM else f'MATCH {m}', 0, 0, 130, CRIMSON if m == NM else GOLD, clamp(k * 3), sw=16); cr.restore()
    e = ease_out(prog(t, b['start'] + 0.1, b['start'] + 0.5))
    ball(cr, 'Canada', lerp(-300, 290, e), 900, 210, 'angry', 0, 0.8); ball(cr, op, lerp(1380, 790, e), 900, 210, 'angry', 0, -0.8)
    if e > 0.9: emoji(cr, '⚡', 540, 900, 160, 1, rot=0.2 * math.sin(t * 10))
    lab = f"vs {'THE ' if op in ('UK', 'Netherlands') else ''}{op.upper()}"; ptext(cr, lab, 540, 1250, fit(cr, lab, 120, 980), WHITE, pop_k(t, b['start'] + 0.35), sw=14)
    cr.restore(); tour_strip(cr, t, 1560); ptext(cr, "CANADA vs ASIA · EPISODE 1", 540, 1460, 36, GOLD, 1, fam='Poppins ExtraBold', sw=6)
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
def fact(cr, t, m):
    b = bt(f'm{m}f'); op = OPP[m]; arena(cr, t, col_of(op))
    ball(cr, 'Canada', 290, 1350, 150, 'happy', 0, 0.8); ball(cr, op, 790, 1350, 150, 'happy', 0, -0.8)
    k = pop_k(t, b['start'] + 0.05, 0.35); cr.save(); cr.translate(540, 420); cr.rotate(-0.03); cr.scale(k, k); rrect(cr, -260, -70, 520, 120, 30); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'FUN FACT', 0, 20, 76, INK, 1, sw=0, shadow=False); cr.restore()
    emoji(cr, FACT_EMOJI[op], 540, 720 + 10 * math.sin(t * 3), 260 * pop_k(t, b['start'] + 0.2, 0.35), 1)
    C.draw_captions(cr, t, 1000); tour_strip(cr, t, 1660, 40)
def result(cr, t, m):
    b = bt(f'm{m}w'); win, pw, ow = MRES[m]; op = OPP[m]; lose = op if win == 'Canada' else 'Canada'; k = ease_out(prog(t, b['start'], b['start'] + 0.35))
    sx, sy = shake(t, b['start'], 18, 0.4); cr.save(); cr.translate(sx, sy); arena(cr, t, col_of(win))
    for j in range(24):
        a = j / 24 * 2 * math.pi + t * 0.3; cr.new_path(); cr.move_to(540, 900); cr.line_to(540 + 1400 * math.cos(a), 900 + 1400 * math.sin(a)); cr.line_to(540 + 1400 * math.cos(a + 0.1), 900 + 1400 * math.sin(a + 0.1)); cr.close_path(); cr.set_source_rgba(1, 1, 1, 0.06); cr.fill()
    ball(cr, win, 540, 900 - abs(math.sin(t * 5)) * 20, 260 * k + 1, 'happy', 0, 0); emoji(cr, '👑', 540, 610, 160 * k, 1, rot=0.1 * math.sin(t * 3))
    ball(cr, lose, 900, 1250, 110, 'shock', 0, -0.6); cr.restore()
    txt = f"{'CANADA' if win == 'Canada' else op.upper()} WINS!"; slam(cr, txt, 540, 360, fit(cr, txt, 110, 980), col_of(win), t, b['start'] + 0.05)
    ptext(cr, f'{max(pw, ow)} — {min(pw, ow)}', 540, 1260, 120, WHITE, pop_k(t, b['start'] + 0.3), sw=14)
    tour_strip(cr, t, 1560); ptext(cr, f"ASIA TOUR: {sum(1 for x in tour_done(t) if MRES[x][0] == 'Canada')}W – {sum(1 for x in tour_done(t) if MRES[x][0] != 'Canada')}L", 540, 1460, 40, GOLD, 1, fam='Poppins ExtraBold', sw=6)

# ---------- hook and outro ----------
def draw_hook(cr, t):
    b1, b2, b3 = bt('h1'), bt('h2'), bt('h3')
    if t < b2['start']:
        CUR[0] = 1; sx, sy = shake(t, 0.05, 18, 0.35); cr.save(); cr.translate(sx, sy); sh_low(cr, t, b1, 'Canada', 0, b1['end'], 'angry'); cr.restore()
        emoji(cr, '⚔️', 860, 820, 150 * pop_k(t, b1['l0'], 0.3), 1); return
    if t < b3['start']:
        sh_ots(cr, t, b2, 'India', b2['start'], b2['end'], 'angry'); streaks(cr, 1 - ease_out(prog(t, b2['start'], b2['start'] + 0.2))); return
    t0 = b3['start']; e = ease_io(prog(t, t0, t0 + 1.0)); s = lerp(0.16, 0.15, e)
    ocean(cr, t); cx, cy = 540, 1000
    for n, rs in G.eu.items():
        tgt = n in EU_NAMES; j = EU_NAMES.index(n) if tgt else 0; tj = t0 + 0.3 + j * 0.22
        on = tgt and t >= tj; col = col_of({'United Kingdom': 'UK'}.get(n, n)) if on else (0.35, 0.38, 0.45)
        km_shape(cr, rs, cx, cy, s, col, 1, fill=0.95 if on else 0.8, lw=1.5, edge=(0.05, 0.06, 0.12))
    for j, n in enumerate(EU_NAMES):
        tj = t0 + 0.3 + j * 0.22
        if t >= tj:
            c = np.concatenate(G.eu[n]); x, y = cx + c[:, 0].mean() * s, cy - c[:, 1].mean() * s; nm = {'United Kingdom': 'UK'}.get(n, n)
            ball(cr, nm, x, y - abs(math.sin(t * 5 + j)) * 6, 44 * pop_k(t, tj, 0.3), 'angry', 0, 0.6)
    ta = w('h3', 'Canada') - 0.4
    if t >= ta:
        k = ease_out(prog(t, ta, ta + 0.7)); cr.save(); cr.translate(lerp(1400, 820, k), lerp(1700, 1480, k)); cr.rotate(math.pi * (1 - k)); ball(cr, 'Canada', 0, 0, 170, 'angry', 0, -0.6); cr.restore()
    g = cairo.LinearGradient(0, 0, 0, 560); g.add_color_stop_rgba(0, 0, 0, 0.05, 0.85); g.add_color_stop_rgba(1, 0, 0, 0.05, 0); cr.rectangle(0, 0, W, 560); cr.set_source(g); cr.fill()
    tn = w('h3', 'Ten') - 0.1
    if t >= tn: slam(cr, '10 COUNTRIES', 540, 200, 110, WHITE, t, tn)
    tf = w('h3', 'Five') - 0.1
    if t >= tf: chip(cr, '5 ROUNDS EACH', 540, 320, 50, GOLD, INK, pop_k(t, tf), 1)
    if t >= ta + 0.7: sx, sy = shake(t, ta + 0.7, 16); cr.save(); cr.translate(sx, sy); slam(cr, 'CANADA vs ASIA', 540, 470, 100, PH_C, t, ta + 0.7); cr.restore()
    C.draw_captions(cr, t, 1780)
    f = 1 - prog(t, t0, t0 + 0.15)
    if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
def draw_end(cr, t):
    c = bt('cta'); arena(cr, t, PH_C)
    slam(cr, 'CANADA vs ASIA · EP 1', 540, 300, 76, GOLD, t, c['start'])
    ball(cr, 'Canada', 540, 620, 170 - abs(math.sin(t * 5)) * 6, 'happy', 0, 0)
    tw_ = w('cta', 'wins') - 0.1
    if t >= tw_:
        for j, (lab, v, col) in enumerate((('WINS', TW, (0.18, 0.75, 0.42)), ('LOSSES', TL, (0.94, 0.26, 0.35)))):
            kk = pop_k(t, tw_ + j * 0.4, 0.3); cx = 330 + j * 420; cr.save(); cr.translate(cx, 960); cr.scale(kk, kk); rrect(cr, -150, -110, 300, 200, 30); cr.set_source_rgb(*col); cr.fill()
            ptext(cr, str(v), 0, 30, 120, INK, 1, sw=0, shadow=False); ptext(cr, lab, 0, 76, 34, INK, 1, fam='Poppins ExtraBold', sw=0, shadow=False); cr.restore()
    tour_strip(cr, t, 1230, 42)
    tn = w('cta', 'next') - 0.1
    if t >= tn: chip(cr, 'WHO SHOULD BE NEXT? COMMENT 👇'.replace(' 👇', ''), 540, 1420, 46, WHITE, INK, pop_k(t, tn), 1)
    ts_ = w('cta', 'subscribe') - 0.1
    if t >= ts_: subscribe_button(cr, t, ts_, 540, 1620)

def render_frame(cr, t):
    b = next((x for x in C.TL['beats'] if x['start'] <= t < x['end']), C.TL['beats'][-1]); key = b['key']
    if key in ('h1', 'h2', 'h3'): draw_hook(cr, t); return
    if key == 'cta': draw_end(cr, t)
    else:
        m = mi_of(key); CUR[0] = m
        if key.endswith('c') and key[1:-1].isdigit(): card(cr, t, m)
        elif key.endswith('w') and key[1:-1].isdigit(): result(cr, t, m)
        elif key.endswith('f') and key[1:-1].isdigit(): fact(cr, t, m)
        else:
            draw_line(cr, t, key)
            if not key.endswith('i1') and not key.endswith('i2'): hud(cr, t, m)
    f = prog(t, C.TL['dur'] - 0.5, C.TL['dur'])
    if f > 0: cr.set_source_rgba(0, 0, 0, f); cr.paint()
# ---------- ending ----------
def subscribe_button(cr, t, t0, x, y):
    """A subscribe button that a hand pointer clicks: it flips to SUBSCRIBED and the bell rings."""
    tc = t0 + 1.3; clicked = t >= tc; k = pop_k(t, t0, 0.3)
    press = 1 - 0.12 * math.sin(math.pi * clamp((t - tc + 0.08) / 0.16)) if abs(t - tc) < 0.1 else 1.0
    pulse = 1 + (0.04 * math.sin(t * 7) if not clicked else 0)
    cr.save(); cr.translate(x, y); cr.scale(k * press * pulse, k * press * pulse)
    txt = 'SUBSCRIBED' if clicked else 'SUBSCRIBE'; tw_ = tw(cr, txt, 60); bw = tw_ + (150 if clicked else 110); bx = -60
    rrect(cr, bx - bw / 2, -66, bw, 116, 58); cr.set_source_rgb(*((0.32, 0.32, 0.36) if clicked else (0.9, 0.08, 0.12))); cr.fill()
    if clicked:
        cx_ = bx - tw_ / 2 - 30; cr.new_path(); cr.move_to(cx_ - 20, -12); cr.line_to(cx_ - 4, 6); cr.line_to(cx_ + 22, -26); cr.set_source_rgb(1, 1, 1); cr.set_line_width(9); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
        ptext(cr, txt, bx + 20, 10, 60, WHITE, 1, sw=0, shadow=False)
    else: ptext(cr, txt, bx, 10, 60, WHITE, 1, sw=0, shadow=False)
    cr.restore()
    ring = 0.5 * math.sin((t - tc) * 30) * math.exp(-(t - tc) * 3) if clicked else 0
    cr.new_path(); cr.arc(x + 230, y - 8, 58 * k, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.95); cr.fill()
    emoji(cr, '🔔', x + 230, y - 8, 76 * k, 1, rot=ring)
    if clicked:
        for j in range(10):
            a = j / 10 * 2 * math.pi; r = 80 + 300 * ease_out(prog(t, tc, tc + 0.6)); f = 1 - prog(t, tc, tc + 0.7)
            if f > 0: cr.new_path(); cr.arc(x + r * math.cos(a), y + r * math.sin(a) * 0.6, 10, 0, 2 * math.pi); cr.set_source_rgba(*(GOLD[:3] if j % 2 else (1, 1, 1)), f); cr.fill()
    if t < tc + 0.5:
        hx = lerp(x + 420, x - 20, ease_out(prog(t, t0 + 0.2, tc))); hy = lerp(y + 300, y + 60, ease_out(prog(t, t0 + 0.2, tc)))
        emoji(cr, '👆', hx, hy, 120, clamp((tc + 0.5 - t) * 4))
def make_audio(T, path):
    dur = T['dur']; n = int(SR * dur); rng = np.random.default_rng(4)
    def note(m): return 440 * 2 ** ((m - 69) / 12)
    def put(arr, t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: arr[i0:i0 + len(sig)] += sig[:n - i0]
    music = np.zeros(n); beat = 60 / 118; bar_ = beat * 4
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    for ci in range(int(dur / bar_) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar_ * 1.15 * SR)) / SR; env = np.minimum(1, Lc / 0.15) * np.exp(-Lc * 0.7)
        put(music, ci * bar_, sum(0.026 * np.sin(2 * np.pi * note(m) * Lc) for m in ch) * env); put(music, ci * bar_, 0.08 * np.sin(2 * np.pi * note(ch[0] - 24) * Lc) * env)
        for j, st in enumerate((0, 0.75, 1.5, 2.5, 3, 3.5)):
            m = ch[j % 3] + 12; P = np.arange(int(0.25 * SR)) / SR; put(music, ci * bar_ + st * beat, 0.026 * sum((1 / h) * np.sin(2 * np.pi * note(m) * h * P) for h in (1, 2, 3)) * np.exp(-P * 14))
    for bi in range(int(dur / (beat / 2))):
        t0 = bi * beat / 2
        if bi % 8 in (0, 3, 6): Ld = np.arange(int(0.3 * SR)) / SR; put(music, t0, 0.32 * np.sin(2 * np.pi * np.cumsum((85 if bi % 8 == 0 else 150) + 80 * np.exp(-Ld * 30)) / SR) * np.exp(-Ld * 13))
        if bi % 2 == 1: M = np.arange(int(0.04 * SR)); put(music, t0, 0.04 * rng.standard_normal(len(M)) * np.exp(-M / SR * 70))
    music = np.tanh(music * 1.3) * 0.45
    fx = np.zeros(n)
    def boom(t0, amp=0.6): Lb = np.arange(int(1.6 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-Lb * 10)) / SR) * np.exp(-Lb * 2.8))
    def whoosh(t0, amp=0.26, d=0.4): nz = rng.standard_normal(int(d * SR)); env = np.linspace(0, 1, len(nz)) ** 2; put(fx, t0, amp * np.convolve(nz, np.ones(25) / 25, 'same') * env)
    def bell(t0, amp=0.1, f=1175): Ld = np.arange(int(1.2 * SR)) / SR; put(fx, t0, amp * (np.sin(2 * np.pi * f * Ld) + 0.5 * np.sin(2 * np.pi * f * 2.76 * Ld)) * np.exp(-Ld * 4))
    def pop(t0, amp=0.05, f=1100): Lp = np.arange(int(0.05 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * (f + 400 * np.exp(-Lp * 60)) * Lp) * np.exp(-Lp * 60))
    def cheer(t0, amp=0.1, d=1.3): z = np.convolve(rng.standard_normal(int(d * SR)), np.ones(8) / 8, 'same'); L_ = np.linspace(0, 1, len(z)); put(fx, t0, amp * z * np.sin(np.pi * L_) ** 0.6)
    def horn(t0, amp=0.07): Lh = np.arange(int(0.9 * SR)) / SR; put(fx, t0, amp * sum(np.sign(np.sin(2 * np.pi * f * Lh)) for f in (146.8, 220, 293.7)) * np.minimum(1, Lh / 0.05) * np.exp(-Lh * 2.5) / 3)
    boom(0.0, 1.0); whoosh(bt('h2')['start'] - 0.3, 0.35, 0.35); boom(bt('h2')['start'] + 0.05, 0.6); whoosh(bt('h3')['start'] - 0.3, 0.3)
    for j in range(len(EU_NAMES)): pop(bt('h3')['start'] + 0.3 + j * 0.22, 0.1, 600 + 60 * j)
    boom(w('h3', 'Ten') - 0.1, 0.8); whoosh(w('h3', 'Canada') - 0.4, 0.4, 0.7); boom(w('h3', 'Canada') + 0.3, 1.1); horn(w('h3', 'Canada') + 0.3, 0.1)
    for m in range(1, NM + 1):
        b = bt(f'm{m}c'); whoosh(b['start'] - 0.35); boom(b['start'] + 0.03, 0.8); bell(b['start'] + 0.03); boom(b['start'] + 0.5, 0.5)
        for r in range(1, 6):
            tv = tv_of(m, r); win = RD[(m, r)][1]; boom(tv, 0.7); bell(tv, 0.08, 1568 if win == 'Canada' else 1319); pop(tv + 0.75, 0.12, 500)
            for k in ('a', 'b', 'x'): whoosh(bt(f'm{m}r{r}{k}')['start'] - 0.2, 0.15, 0.22)
            ba = bt(f'm{m}r{r}a'); whoosh(ba['start'] + 0.42 * (ba['end'] - ba['start']) - 0.15, 0.15, 0.2)
        bw = bt(f'm{m}w'); whoosh(bw['start'] - 0.3, 0.3); boom(bw['start'] + 0.05, 1.0); horn(bw['start'] + 0.05, 0.1); cheer(bw['start'] + 0.2, 0.13, 1.6)
        for k in ('i1', 'i2', 'e1', 'e2'): whoosh(bt(f'm{m}{k}')['start'] - 0.2, 0.18, 0.25)
    c = bt('cta'); boom(c['start'], 0.9); tw_ = w('cta', 'wins') - 0.1; pop(tw_, 0.14, 900); pop(tw_ + 0.4, 0.14, 1100)
    tsc = w('cta', 'subscribe') - 0.1 + 1.3; pop(tsc, 0.18, 1800); bell(tsc + 0.05, 0.16, 1568); bell(tsc + 0.25, 0.12, 2093); cheer(tsc + 0.1, 0.1, 1.4)
    for s_ in sorry_times(): bell(s_ + 0.05, 0.05, 2093)
    v = np.zeros(n); tt = np.arange(n) / SR
    for s0, a in T['clips']: put(v, s0, a / max(1e-6, np.abs(a).max()) * 0.9)
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    global G
    C.TL = C.build(MultiVoice(cache)); G = Geo(data_dir)

def render_chunk(args):
    i0, i1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf); cr.set_antialias(cairo.ANTIALIAS_BEST)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        cr.identity_matrix(); cr.reset_clip(); render_frame(cr, i / FPS); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return out

def main():
    data_dir, out = sys.argv[1:3]
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_caasia'))
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


