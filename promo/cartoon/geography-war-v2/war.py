"""'North America vs Europe: The Geography War' (9:16). Eight rounds with a live scoreboard; every round is a different shot:
country-by-country globes, a true-size overlay, split-screen crowds, a mountain side view, incoming flights, rivers drawn on
close-up globes, a timeline pan and rising coin towers. Word-synced (engine from china.py).
Usage: python3 war.py <data_dir> <out.mp4> [--preview t1,...]
"""
import json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
import cairo
import china as C
from big import local, bounds, recentre, area, km_shape, km_path, ortho, bg
from popu import streaks, shake
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, W, H, FPS, GOLD, WHITE, INK, CRIMSON
from canada import rings
from quiz import clamp, lerp, prog, ease_io, ease_out, ease_back, hexc, SR

C.VOICE, C.RATE = 'en-US-ChristopherNeural', '+7%'
C.SAY = {None: {'Elbrus': 'Elbroos', 'Denali': 'Deh-nah-lee', 'Bologna': 'Bolonya'}}
C.HOT = ('europe', 'america', 'north', 'round', 'war', 'countries', 'size', 'people', 'peak', 'visitors', 'river', 'history', 'money', 'final',
         'elbrus', 'denali', 'volga', 'mississippi', 'missouri', 'bologna', 'draw', 'tie', 'blood', 'victory', 'wins', 'trillion', 'million')
C.TAIL_OVERRIDE = {'h1': 0.25, 'h2': 0.25, 'h3': 0.3, 'title': 0.7, 'end': 0.6, 'cta': 2.4, **{f'r{i}': 0.55 for i in range(1, 9)}}
NA_C, EU_C = hexc('#FF8A1F')[:3], hexc('#3FA9FF')[:3]
BEATS = [(k, s, None, None, None, None, None) for k, s in (
    ('h1', "Two continents. Sixty-seven countries. One war."),
    ('h2', "One has the size. The other has the numbers."),
    ('h3', "Eight rounds... and it goes down to the very last one."),
    ('title', "North America versus Europe: the geography war."),
    ('r1', "Round one: countries. North America has twenty-three, from Canada down to Panama and across the Caribbean. Europe packs in forty-four. First blood: Europe."),
    ('r2', "Round two: size. North America covers almost twenty-five million square kilometres. All of Europe would fit inside it nearly two and a half times. North America strikes back."),
    ('r3', "Round three: people. Europe has about seven hundred and forty-five million. North America, about six hundred and seventeen million. Europe takes the lead."),
    ('r4', "Round four: the highest peak. Europe sends Mount Elbrus: five thousand six hundred and forty-two metres. North America answers with Denali: six thousand one hundred and ninety. All square."),
    ('r5', "Round five: visitors. In 2024, Europe welcomed roughly four times as many international tourists as North America. Europe, again."),
    ('r6', "Round six: the longest river. The Volga runs three thousand five hundred kilometres. The Mississippi and Missouri together: over six thousand. Level again."),
    ('r7', "Round seven: history. Europe's oldest university, Bologna, opened in 1088. North America's oldest, in Santo Domingo, came four hundred and fifty years later. Europe is one round from victory."),
    ('r8', "Final round: money. Europe's economy is about twenty-seven trillion dollars. North America's: about thirty-four trillion. North America wins the last round!"),
    ('end', "Four rounds each. The war ends in a draw... unless you break the tie."),
    ('cta', "North America, or Europe? Comment your side, and follow for the next battle."))]
C.BEATS = BEATS; C.HOOK = ('h1', 'h2', 'h3')
bt, w = C.bt, C.w
# round: title, winner, word after the title card, verdict word, big numbers (NA, EU)
ROUNDS = {'r1': ('COUNTRIES', 'EU', 'North', 'blood'), 'r2': ('SIZE', 'NA', 'North', 'strikes'), 'r3': ('PEOPLE', 'EU', 'Europe', 'takes'),
          'r4': ('HIGHEST PEAK', 'NA', 'Europe', 'square'), 'r5': ('VISITORS', 'EU', 'In', 'again'), 'r6': ('LONGEST RIVER', 'NA', 'Volga', 'Level'),
          'r7': ('HISTORY', 'EU', "Europe's", 'one'), 'r8': ('MONEY', 'NA', "Europe's", 'wins')}
NA = ['Canada', 'United States of America', 'Mexico', 'Guatemala', 'Belize', 'El Salvador', 'Honduras', 'Nicaragua', 'Costa Rica', 'Panama', 'Cuba', 'Bahamas',
      'Jamaica', 'Haiti', 'Dominican Rep.', 'St. Kitts and Nevis', 'Antigua and Barb.', 'Dominica', 'Saint Lucia', 'St. Vin. and Gren.', 'Barbados', 'Grenada', 'Trinidad and Tobago']
EU = ['Iceland', 'Ireland', 'United Kingdom', 'Portugal', 'Spain', 'Andorra', 'France', 'Monaco', 'Belgium', 'Netherlands', 'Luxembourg', 'Switzerland', 'Liechtenstein',
      'Germany', 'Denmark', 'Norway', 'Sweden', 'Finland', 'Italy', 'San Marino', 'Vatican', 'Malta', 'Austria', 'Czechia', 'Poland', 'Slovakia', 'Hungary', 'Slovenia',
      'Croatia', 'Bosnia and Herz.', 'Montenegro', 'Serbia', 'Albania', 'North Macedonia', 'Greece', 'Bulgaria', 'Romania', 'Moldova', 'Ukraine', 'Belarus', 'Lithuania',
      'Latvia', 'Estonia', 'Russia']
SHORT = {'United States of America': 'USA', 'Dominican Rep.': 'DOMINICAN REP.', 'St. Kitts and Nevis': 'ST KITTS & NEVIS', 'Antigua and Barb.': 'ANTIGUA & BARBUDA',
         'St. Vin. and Gren.': 'ST VINCENT', 'Bosnia and Herz.': 'BOSNIA', 'Trinidad and Tobago': 'TRINIDAD & TOBAGO', 'United Kingdom': 'UK', 'North Macedonia': 'N. MACEDONIA'}
NA_VIEW, EU_VIEW = (-92, 40, 1.55), (18, 55, 2.35)
G = None

class Geo:
    def __init__(self, d):
        cf = {f['properties']['NAME']: f for f in json.load(open(os.path.join(d, 'countries_50m.geojson')))['features']}
        def keep(n, r):
            lon, lat = r[:, 0].mean(), r[:, 1].mean()
            if n == 'France': return -6 < lon < 10 and lat > 41
            if n == 'Netherlands': return lon > 0
            if n == 'Norway': return lat < 72
            if n == 'Russia': return lon < 60 and lat > 41
            if n == 'Spain': return lat > 35
            if n == 'Portugal': return lon > -10
            return True
        self.raw, self.pt, self.tiny = {}, {}, {}
        for n in NA + EU + ['Greenland', 'Kosovo']:
            rs = [r for r in rings(cf[n]['geometry']) if len(r) > 3]
            if n == 'Russia':  # European Russia only: keep the vertices west of the Urals
                rs = [r[(r[:, 0] < 60) & (r[:, 0] > 19) & (r[:, 1] > 41)] for r in rs]; rs = [r for r in rs if len(r) > 3]
            rs = [r for r in rs if keep(n, r)]
            self.raw[n] = rs; big = max(rs, key=len); self.pt[n] = (float(big[:, 0].mean()), float(big[:, 1].mean()))
            p = np.concatenate(rs); self.tiny[n] = max(np.ptp(p[:, 0]), np.ptp(p[:, 1])) < 1.6
        self.land = [r for f in json.load(open(os.path.join(d, 'land.geojson')))['features'] for r in rings(f['geometry']) if len(r) > 3]
        na = [r for n in NA + ['Greenland'] for r in self.raw[n] if not (n == 'United States of America' and r[:, 0].mean() < -150 and r[:, 1].mean() < 30)]
        eu = [r for n in EU + ['Kosovo'] for r in self.raw[n] if not (n == 'Norway' and r[:, 1].mean() > 72)]
        self.na_km = recentre(local(na, -96, 50)); self.eu_km = recentre(local(eu, 22, 54))
        self.riv = {}
        for f in json.load(open(os.path.join(d, 'rivers_50m.geojson')))['features']:
            n = f['properties'].get('name')
            if n in ('Volga', 'Mississippi', 'Missouri') and f['geometry']:
                g = f['geometry']; self.riv.setdefault(n, []).extend(np.array(c) for c in (g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]))
        print('areas M km²: NA', round(area(self.na_km) / 1e6, 1), 'EU', round(area(self.eu_km) / 1e6, 1))

# ---------- drawing ----------
def globe(cr, cx, cy, R, lon0, lat0, fills=(), rivers=None):
    """fills: [(name, colour, alpha)]"""
    g = cairo.RadialGradient(cx - R * 0.3, cy - R * 0.35, R * 0.1, cx, cy, R); g.add_color_stop_rgb(0, 0.16, 0.36, 0.62); g.add_color_stop_rgb(1, 0.04, 0.11, 0.3)
    cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.set_source(g); cr.fill()
    cr.save(); cr.new_path(); cr.arc(cx, cy, R, 0, 2 * math.pi); cr.clip()
    def path(rs):
        cr.new_path()
        for r in rs:
            x, y, cc = ortho(r[:, 0], r[:, 1], lon0, lat0)
            if (cc < 0).all(): continue
            cr.move_to(cx + x[0] * R, cy + y[0] * R); [cr.line_to(cx + u * R, cy + v * R) for u, v in zip(x[1:], y[1:])]; cr.close_path()
    path(G.land); cr.set_source_rgb(0.24, 0.3, 0.3); cr.fill()
    for n, col, a in fills:
        if a <= 0: continue
        path(G.raw[n]); cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(0.03, 0.04, 0.1, 0.9 * a); cr.set_line_width(1.6); cr.stroke()
        if G.tiny[n]:
            x, y, cc = ortho(np.array([G.pt[n][0]]), np.array([G.pt[n][1]]), lon0, lat0)
            if cc[0] > 0: cr.new_path(); cr.arc(cx + x[0] * R, cy + y[0] * R, 9, 0, 2 * math.pi); cr.set_source_rgba(*col, a); cr.fill_preserve(); cr.set_source_rgba(1, 1, 1, a); cr.set_line_width(2.5); cr.stroke()
    if rivers:
        segs, k, col = rivers; tot = sum(len(s) for s in segs); done = 0
        for s in segs:
            m = int(clamp((k * tot - done) / len(s)) * len(s)); done += len(s)
            if m < 2: continue
            x, y, cc = ortho(s[:m, 0], s[:m, 1], lon0, lat0)
            for lw, al in ((22, 0.25), (8, 1)):
                cr.new_path(); cr.move_to(cx + x[0] * R, cy + y[0] * R); [cr.line_to(cx + u * R, cy + v * R) for u, v in zip(x[1:], y[1:])]
                cr.set_source_rgba(*col, al); cr.set_line_width(lw); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
    g = cairo.RadialGradient(cx - R * 0.35, cy - R * 0.4, R * 0.05, cx, cy, R * 1.02)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.16); g.add_color_stop_rgba(0.6, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0, 0, 0.05, 0.6); cr.set_source(g); cr.paint(); cr.restore()
    cr.new_path(); cr.arc(cx, cy, R + 8, 0, 2 * math.pi); cr.set_source_rgba(0.5, 0.75, 1, 0.28); cr.set_line_width(10); cr.stroke()

def cam(cr, z=1.0, tilt=0.0, fx=540, fy=960):
    cr.translate(540, 960); cr.rotate(tilt); cr.scale(z, z); cr.translate(-fx, -fy)
def push(t, a, b, z0, z1): return lerp(z0, z1, ease_out(prog(t, a, b)))
def side_fills(names, col, a=1.0, shade=True):
    out = []
    for i, n in enumerate(names):
        f = 0.82 + 0.18 * ((i * 7) % 5) / 4 if shade else 1.0; out.append((n, tuple(min(1, c * f) for c in col), a))
    return out
def big_num(cr, txt, x, y, size, col, k=1.0, a=1.0):
    cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, txt, 0, 0, fit(cr, txt, size, 500), col, a, sw=size * 0.12); cr.restore()
def side_label(cr, t, t0, txt, x, y, col, size=44):
    if t >= t0: k = pop_k(t, t0, 0.3); cr.save(); cr.translate(x, y); cr.scale(k, k); ptext(cr, txt, 0, 0, fit(cr, txt, size, 500, 'Poppins ExtraBold'), col, 1, fam='Poppins ExtraBold', sw=7); cr.restore()

# ---------- score ----------
def score_at(t):
    na = eu = 0
    for k, (ttl, win, _, vw) in ROUNDS.items():
        if t >= w(k, vw): na += win == 'NA'; eu += win == 'EU'
    return na, eu
def hud(cr, t):
    if t < bt('title')['start']: return
    a = ease_out(prog(t, bt('title')['end'] - 0.4, bt('title')['end']))
    if a <= 0: return
    na, eu = score_at(t)
    rrect(cr, 30, 140, 1020, 190, 44); cr.set_source_rgba(0.03, 0.04, 0.1, 0.88 * a); cr.fill()
    for side, x, col, sc, lab in (('NA', 250, NA_C, na, 'N. AMERICA'), ('EU', 830, EU_C, eu, 'EUROPE')):
        ptext(cr, lab, x, 200, 44, col, a, sw=0, shadow=False)
        tv = max([w(k, v[3]) for k, v in ROUNDS.items() if v[1] == side and t >= w(k, v[3])] or [-9])
        k = pop_k(t, tv, 0.4) if t - tv < 0.6 else 1.0
        cr.save(); cr.translate(x, 300); cr.scale(k, k); ptext(cr, str(sc), 0, 0, 100, WHITE, a, sw=0, shadow=False); cr.restore()
    rk = next((k for k in ROUNDS if bt(k)['start'] <= t < bt(k)['end']), None)
    ptext(cr, f'ROUND {rk[1]}/8' if rk else ('FINAL' if t >= bt('end')['start'] else 'VS'), 540, 200, 34, GOLD, a, fam='Poppins ExtraBold', sw=0, shadow=False)
    ptext(cr, '—', 540, 290, 70, WHITE, a, sw=0, shadow=False)

def round_card(cr, t, key):
    b = bt(key); ttl = ROUNDS[key][0]; t1 = card_end(key)
    if not (b['start'] <= t < t1): return False
    k = ease_out(prog(t, b['start'], b['start'] + 0.2)); n = int(key[1])
    cr.save(); cam(cr, 1.0 + 0.06 * prog(t, b['start'], t1), -0.05)
    cr.rectangle(-200, -200, 1500, 2400); cr.set_source_rgb(0.03, 0.03, 0.09); cr.fill()
    for i, col in enumerate((NA_C, EU_C)):
        cr.new_path(); cr.move_to(-200 if i == 0 else 1280, 500); cr.line_to(540 + (-40 if i == 0 else 40), 960); cr.line_to(-200 if i == 0 else 1280, 1420); cr.close_path(); cr.set_source_rgba(*col, 0.35); cr.fill()
    s = lerp(2.2, 1, k)
    cr.save(); cr.translate(540, 820); cr.scale(s, s); ptext(cr, 'FINAL ROUND' if n == 8 else f'ROUND {n}', 0, 0, 120 if n == 8 else 150, CRIMSON if n == 8 else GOLD, clamp(k * 3), sw=16); cr.restore()
    tt = b['l0'] + 0.55
    if t >= tt: kk = pop_k(t, tt, 0.25); cr.save(); cr.translate(540, 1010); cr.scale(kk, kk); ptext(cr, ttl, 0, 0, fit(cr, ttl, 130, 960), WHITE, 1, sw=14); cr.restore()
    cr.restore(); streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.25)))
    return True
def card_end(key):
    word = ROUNDS[key][2]; return w(key, word) - (0.35 if key == 'r6' else 0.15)

def verdict(cr, t, key):
    ttl, win, _, vw = ROUNDS[key]; tv = w(key, vw)
    if t < tv: return
    col = NA_C if win == 'NA' else EU_C; f = 1 - prog(t, tv, tv + 0.3)
    if f > 0: cr.set_source_rgba(*col, 0.35 * f); cr.paint()
    k = prog(t, tv, tv + 0.22); s = lerp(2.6, 1, ease_out(k)); x = lerp(-300 if win == 'NA' else 1380, 540, ease_out(k))
    txt = ('NORTH AMERICA' if win == 'NA' else 'EUROPE') + ' WINS'
    cr.save(); cr.translate(x, 1320); cr.rotate(-0.05 if win == 'NA' else 0.05); cr.scale(s, s); wd = tw(cr, txt, 76)
    rrect(cr, -wd / 2 - 44, -86, wd + 88, 124, 24); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(6); cr.stroke()
    ptext(cr, txt, 0, 6, 76, INK, 1, sw=0, shadow=False); cr.restore()

# ---------- the rounds ----------
def pops(names, t, t0, t1):
    n = len(names); return [1.0 if t >= lerp(t0, t1, i / max(1, n - 1)) else 0.0 for i in range(n)]

def r1(cr, t, b):
    te = w('r1', 'Europe'); bg(cr, t, NA_C if t < te else EU_C)
    if t < te:
        t0, t1 = w('r1', 'twenty') - 0.2, w('r1', 'Caribbean', end=True); al = pops(NA, t, t0, t1); n = int(sum(al))
        cr.save(); cam(cr, push(t, b['start'], te, 1.0, 1.1), -0.05, 540, 1000)
        globe(cr, 540, 1040, 400 * NA_VIEW[2], NA_VIEW[0] + 6 * prog(t, t0, te), NA_VIEW[1] - 8 * prog(t, t0, te), [(nm, c, a) for (nm, c, _), a in zip(side_fills(NA, NA_C), al)] + [('Greenland', (0.5, 0.42, 0.36), 0.6)])
        cr.restore(); col = NA_C; names = NA
    else:
        t0, t1 = te + 0.1, w('r1', 'forty') + 0.9; al = pops(EU, t, t0, t1); n = int(sum(al))
        cr.save(); cam(cr, push(t, te, b['end'], 1.0, 1.1), 0.05, 540, 1000)
        globe(cr, 540, 1040, 400 * EU_VIEW[2], EU_VIEW[0], EU_VIEW[1], [(nm, c, a) for (nm, c, _), a in zip(side_fills(EU, EU_C), al)] + [('Kosovo', tuple(c * 0.75 for c in EU_C), 1.0 if n > 31 else 0)])
        cr.restore(); streaks(cr, 1 - ease_out(prog(t, te, te + 0.22))); col = EU_C; names = EU
    if n:
        ptext(cr, str(n), 540, 560, 190, col, 1, sw=18)
        nm = names[n - 1]; ptext(cr, SHORT.get(nm, nm.upper()), 540, 640, 44, WHITE, 1, fam='Poppins ExtraBold', sw=6)

def r2(cr, t, b):
    bg(cr, t, NA_C); s = 0.118; cx, cy = 540, 1080; tf = w('r2', 'fit') - 0.3
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.045, cx, cy)
    km_shape(cr, G.na_km, cx, cy, s, NA_C, 1, glow=True, lw=2)
    for i, (ox, oy, t0, frac) in enumerate(((-900, 1250, tf, 1), (1150, -550, w('r2', 'two') - 0.2, 1), (-700, -2350, w('r2', 'half') - 0.2, 0.42))):
        if t < t0: continue
        k = ease_out(prog(t, t0, t0 + 0.5)); sx, sy = shake(t, t0 + 0.5, 12, 0.3)
        cr.save(); cr.translate(sx, sy - (1 - k) * 900)
        if frac < 1:
            x0, x1, y0, y1 = bounds(G.eu_km); cr.rectangle(cx + (x0 + ox) * s, cy - (y1 + oy) * s, (x1 - x0) * s * frac, (y1 - y0) * s); cr.clip()
        km_shape(cr, G.eu_km, cx, cy, s, EU_C, k, ox, oy, fill=0.78, lw=2.5, edge=WHITE); cr.restore()
    cr.restore()
    side_label(cr, t, w('r2', 'twenty'), 'N. AMERICA: 24.7M KM²', 540, 420, NA_C, 54)
    side_label(cr, t, tf, 'EUROPE: 10.2M KM²', 540, 495, EU_C, 54)
    if t >= w('r2', 'half'): chip(cr, 'EUROPE FITS ×2.4', 540, 1480, 56, WHITE, INK, pop_k(t, w('r2', 'half')), 1)

def r3(cr, t, b):
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.08), -0.03)
    for i, (col, x0) in enumerate(((NA_C, -100), (EU_C, 540))):
        cr.rectangle(x0, -200, 640, 2400); cr.set_source_rgb(*[0.04 + 0.2 * c for c in col]); cr.fill()
    cr.rectangle(536, -200, 8, 2400); cr.set_source_rgb(1, 1, 1); cr.fill()
    for side, cx, col, word, tot, lab in (('EU', 810, EU_C, 'seven', 745, 'EUROPE'), ('NA', 270, NA_C, 'six', 617, 'N. AMERICA')):
        t0 = w('r3', word) - 0.2
        if t < t0: ptext(cr, lab, cx, 560, 54, col, 0.5, sw=8); continue
        k = ease_out(prog(t, t0, t0 + 1.8)); n = int(round(tot / 10 * k))
        for j in range(n):
            x = cx - 180 + (j % 7) * 60; y = 720 + (j // 7) * 62
            cr.new_path(); cr.arc(x, y - 14, 11, 0, 2 * math.pi); cr.rectangle(x - 12, y - 2, 24, 30); cr.set_source_rgb(*col); cr.fill()
        ptext(cr, lab, cx, 560, 54, col, 1, sw=8); ptext(cr, f'{int(tot * k)}M', cx, 660, 84, WHITE, 1, sw=10)
    cr.restore()
    ptext(cr, 'EACH FIGURE = 10 MILLION PEOPLE', 540, 400, 32, WHITE, 0.85, fam='Poppins ExtraBold', sw=5)

def peak(cr, x, base, hpx, wd, col, k, name, metres, snow=True):
    h = hpx * k
    cr.new_path(); cr.move_to(x - wd / 2, base); cr.line_to(x - wd * 0.12, base - h * 0.72); cr.line_to(x, base - h); cr.line_to(x + wd * 0.16, base - h * 0.66); cr.line_to(x + wd / 2, base); cr.close_path()
    cr.set_source_rgb(*[c * 0.55 for c in col]); cr.fill_preserve(); cr.set_source_rgb(0.03, 0.04, 0.1); cr.set_line_width(6); cr.stroke()
    cr.new_path(); cr.move_to(x - wd * 0.1, base - h * 0.76); cr.line_to(x, base - h); cr.line_to(x + wd * 0.12, base - h * 0.74); cr.line_to(x + wd * 0.04, base - h * 0.8); cr.line_to(x - wd * 0.02, base - h * 0.73); cr.close_path()
    cr.set_source_rgb(0.95, 0.97, 1); cr.fill()
    if k > 0.05:
        ptext(cr, name, x, base - h * 0.3, 60, WHITE, 1, sw=9); ptext(cr, f'{int(metres * k):,} M', x, base - h * 0.3 + 70, 54, GOLD, 1, sw=8)

def r4(cr, t, b):
    te, td = w('r4', 'Elbrus') - 0.2, w('r4', 'Denali') - 0.2
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.04, 0.14); g.add_color_stop_rgb(1, 0.2, 0.24, 0.4); cr.set_source(g); cr.paint()
    rise = ease_io(prog(t, td, td + 1.4)); sx, sy = shake(t, td + 1.4, 12, 0.35)
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.06), 0.03 - 0.06 * rise, 540 + sx, 960 - 120 * rise + sy)  # the camera tilts up as Denali rises
    cr.rectangle(-300, 1560, 1700, 800); cr.set_source_rgb(0.1, 0.13, 0.2); cr.fill()
    px = 0.19  # px per metre
    peak(cr, 790, 1560, 5642 * px, 620, EU_C, ease_io(prog(t, te, te + 1.3)), 'ELBRUS', 5642)
    peak(cr, 300, 1560, 6190 * px, 640, NA_C, rise, 'DENALI', 6190)
    if rise >= 1:
        y = 1560 - 6190 * px; cr.new_path(); cr.move_to(300, y); cr.line_to(1000, y); cr.set_dash([14, 10]); cr.set_source_rgb(1, 1, 1); cr.set_line_width(3); cr.stroke(); cr.set_dash([])
        ptext(cr, '+548 M', 790, y - 22, 56, GOLD, pop_k(t, td + 1.45), sw=8)
    cr.restore()

def r5(cr, t, b):
    bg(cr, t, EU_C); tf = w('r5', 'four') - 0.2
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.12), -0.04, 540, 1000)
    globe(cr, 540, 1040, 560, 5 - 6 * prog(t, b['start'], b['end']), 45, side_fills(EU, EU_C, 0.95) + side_fills(NA, NA_C, 0.95))
    ex, ey, _ = ortho(np.array([12.0]), np.array([49.0]), 5, 45); ex, ey = 540 + ex[0] * 560, 1040 + ey[0] * 560
    for i in range(14):  # flights curving into Europe
        ang = i / 14 * 2 * math.pi + 0.3; ph = ((t - b['start']) * 0.45 + i * 0.37) % 1.0; d = 620 * (1 - ph)
        x, y = ex + d * math.cos(ang) + 60 * math.sin(ph * math.pi), ey + d * math.sin(ang) * 0.8 - 90 * math.sin(ph * math.pi)
        emoji(cr, '✈️', x, y, 46 + 20 * ph, min(1, 3 * ph) * min(1, 4 * (1 - ph)), rot=ang + math.pi * 0.75)
    cr.restore()
    for i, (lab, val, col, n) in enumerate((('EUROPE', '~750M', EU_C, 4), ('N. AMERICA', '~185M', NA_C, 1))):
        t0 = tf + i * 0.5
        if t < t0: continue
        k = pop_k(t, t0, 0.3); y = 1330 + i * 120
        cr.save(); cr.translate(540, y); cr.scale(k, k); rrect(cr, -470, -50, 940, 100, 30); cr.set_source_rgba(0.03, 0.04, 0.1, 0.9); cr.fill()
        ptext(cr, lab, -440, 16, 40, col, 1, anchor='l', sw=0, shadow=False); ptext(cr, val, -120, 16, 44, WHITE, 1, anchor='l', sw=0, shadow=False)
        for j in range(n): emoji(cr, '🧳', 150 + j * 78, -6, 64, 1)
        cr.restore()
    side_label(cr, t, w('r5', '2024'), 'INTERNATIONAL ARRIVALS · 2024', 540, 400, WHITE, 40)

def r6(cr, t, b):
    tm = w('r6', 'Mississippi') - 0.3
    if t < tm:
        bg(cr, t, EU_C); t0 = w('r6', 'Volga'); k = ease_io(prog(t, t0, t0 + 2.2))
        cr.save(); cam(cr, push(t, b['start'], tm, 1.0, 1.12), 0.05, 540, 1000)
        globe(cr, 540, 1040, 2500, 42, 52.5, side_fills(EU, EU_C, 0.55), (G.riv['Volga'], k, (0.75, 0.93, 1)))
        cr.restore(); ptext(cr, 'VOLGA', 540, 500, 110, EU_C, 1, sw=14); ptext(cr, f'{int(3531 * k):,} KM', 540, 610, 76, WHITE, 1, sw=10)
    else:
        bg(cr, t, NA_C); k = ease_io(prog(t, tm + 0.3, tm + 2.6)); sx, sy = shake(t, tm + 2.6, 12, 0.35)
        cr.save(); cam(cr, push(t, tm, b['end'], 1.0, 1.12), -0.05, 540 + sx, 1000 + sy)
        globe(cr, 540, 1040, 1500, -98, 40, side_fills(NA, NA_C, 0.55), (G.riv['Missouri'] + G.riv['Mississippi'], k, (1, 0.95, 0.75)))
        cr.restore(); streaks(cr, 1 - ease_out(prog(t, tm, tm + 0.22)))
        ptext(cr, 'MISSISSIPPI–MISSOURI', 540, 500, 74, NA_C, 1, sw=11); ptext(cr, f'{int(6275 * k):,} KM', 540, 610, 76, WHITE, 1, sw=10)

def r7(cr, t, b):
    cr.set_source_rgb(0.05, 0.04, 0.1); cr.paint()
    ts = w('r7', 'Santo') - 0.4; pan = ease_io(prog(t, ts, ts + 1.1)); px = 3.4  # px per year
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.06), 0.04 - 0.08 * pan, 540 + (1538 - 1088) * px * pan * 0.72, 960)
    x0 = 300
    def X(yr): return x0 + (yr - 1088) * px
    cr.new_path(); cr.move_to(X(950), 1100); cr.line_to(X(1700), 1100); cr.set_source_rgb(0.8, 0.8, 0.9); cr.set_line_width(8); cr.stroke()
    for yr in range(1000, 1701, 100):
        cr.new_path(); cr.move_to(X(yr), 1070); cr.line_to(X(yr), 1130); cr.stroke(); ptext(cr, str(yr), X(yr), 1190, 34, (0.7, 0.7, 0.8), 1, fam='Poppins ExtraBold', sw=5)
    for yr, nm, col, t0 in ((1088, 'BOLOGNA', EU_C, w('r7', 'Bologna') - 0.2), (1538, 'SANTO DOMINGO', NA_C, ts + 0.5)):
        if t < t0: continue
        k = pop_k(t, t0, 0.35); cr.save(); cr.translate(X(yr), 1100); cr.scale(k, k)
        cr.new_path(); cr.arc(0, 0, 26, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(1, 1, 1); cr.set_line_width(5); cr.stroke()
        emoji(cr, '🏛️', 0, -250, 200, 1); ptext(cr, str(yr), 0, -90, 110, col, 1, sw=13); ptext(cr, nm, 0, -400, 50, WHITE, 1, sw=8); cr.restore()
    tg = w('r7', 'four')
    if t >= tg:
        k = ease_out(prog(t, tg, tg + 0.6)); cr.new_path(); cr.move_to(X(1088), 1290); cr.line_to(lerp(X(1088), X(1538), k), 1290); cr.set_source_rgb(*GOLD[:3]); cr.set_line_width(10); cr.stroke()
        ptext(cr, '450 YEARS EARLIER', X(1440), 1370, 54, GOLD, pop_k(t, tg + 0.4) if t >= tg + 0.4 else 0, sw=8)
    cr.restore()

def r8(cr, t, b):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.03, 0.05, 0.1); g.add_color_stop_rgb(1, 0.1, 0.16, 0.12); cr.set_source(g); cr.paint()
    te, tn = w('r8', 'twenty') - 0.2, w('r8', 'thirty') - 0.2; kn = ease_io(prog(t, tn, tn + 1.4)); sx, sy = shake(t, tn + 1.4, 14, 0.4)
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.05), -0.035 + 0.05 * kn, 540 + sx, 960 + sy)
    for cx, col, tot, k, lab in ((790, EU_C, 27, ease_io(prog(t, te, te + 1.3)), 'EUROPE'), (290, NA_C, 34, kn, 'N. AMERICA')):
        n = int(round(tot * k))
        for j in range(n):
            y = 1400 - j * 23; ellw = 150
            cr.save(); cr.translate(cx, y); cr.scale(1, 0.32); cr.new_path(); cr.arc(0, 0, ellw, 0, 2 * math.pi); cr.restore()
            cr.set_source_rgb(*(GOLD[:3] if j % 2 else (0.85, 0.62, 0.15))); cr.fill_preserve(); cr.set_source_rgb(0.25, 0.16, 0.02); cr.set_line_width(4); cr.stroke()
        top = 1400 - n * 23
        ptext(cr, lab, cx, 1500, 50, col, 1, sw=7)
        if k > 0.02: ptext(cr, f'${int(tot * k)}T', cx, top - 70, 100, WHITE, 1, sw=12)
    cr.restore()
    ptext(cr, 'TOTAL ECONOMY (GDP)', 540, 400, 36, WHITE, 0.85, fam='Poppins ExtraBold', sw=5)

ROUND_FN = {'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4, 'r5': r5, 'r6': r6, 'r7': r7, 'r8': r8}

# ---------- hook, title, ending ----------
def split_globes(cr, t, zoom=1.0, a_na=1.0, a_eu=1.0, spin=0.0):
    for i, (view, names, col, x0, al) in enumerate(((NA_VIEW, NA, NA_C, 0, a_na), (EU_VIEW, EU, EU_C, 540, a_eu))):
        cr.save(); cr.rectangle(x0, 0, 540, H); cr.clip(); cr.set_source_rgb(*[0.03 + 0.14 * c for c in col]); cr.paint()
        fills = side_fills(names, col, al) if isinstance(al, float) else [(n, c, a) for (n, c, _), a in zip(side_fills(names, col), al)]
        globe(cr, x0 + 270, 1040, 250 * view[2] * 0.72 * zoom, view[0] + spin, view[1], fills); cr.restore()
    cr.rectangle(536, 0, 8, H); cr.set_source_rgb(1, 1, 1); cr.fill()

def draw_hook(cr, t):
    if t >= bt('title')['start']: return False
    b = next(bt(k) for k in ('h1', 'h2', 'h3') if t < bt(k)['end'] + 1e-6); key = b['key']
    if key == 'h1':
        t0, t1 = w('h1', 'Sixty') - 0.1, w('h1', 'countries', end=True)
        cr.save(); cam(cr, push(t, 0, b['end'], 1.0, 1.1), -0.03); split_globes(cr, t, 1.0, pops(NA, t, t0, t1), pops(EU, t, t0, t1)); cr.restore()
        slam(cr, '2 CONTINENTS', 540, 260, 130, WHITE, t, 0.03)
        n = int(sum(pops(NA, t, t0, t1)) + sum(pops(EU, t, t0, t1)))
        if n: ptext(cr, f'{n} COUNTRIES', 540, 400, 100, GOLD, 1, sw=12)
        tw_ = w('h1', 'One')
        if t >= tw_: sx, sy = shake(t, tw_, 20); cr.save(); cr.translate(sx, sy); slam(cr, '1 WAR', 540, 1560, 200, CRIMSON, t, tw_); cr.restore()
    elif key == 'h2':
        bg(cr, t, NA_C); ts = w('h2', 'other') - 0.3
        cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.1), 0.05, 540, 980)
        km_shape(cr, G.na_km, 540, 900, 0.125, NA_C, 1, glow=True, lw=2)
        if t >= ts:
            k = ease_out(prog(t, ts, ts + 0.45)); cr.save(); cr.translate(0, (1 - k) * -800); km_shape(cr, G.eu_km, 540, 900, 0.125, EU_C, k, 200, -300, fill=0.85, lw=3, edge=WHITE); cr.restore()
        cr.restore()
        slam(cr, 'ONE HAS THE SIZE', 540, 440, 100, NA_C, t, w('h2', 'size') - 0.3)
        slam(cr, 'ONE HAS THE NUMBERS', 540, 1480, 88, EU_C, t, ts)
    else:
        cr.set_source_rgb(0.03, 0.03, 0.09); cr.paint()
        cr.save(); cam(cr, push(t, b['start'], b['end'], 1.0, 1.12), -0.04)
        for i in range(8):
            ts = b['l0'] + i * 0.12
            if t < ts: continue
            k = pop_k(t, ts, 0.25); x, y = 180 + (i % 4) * 240, 760 + (i // 4) * 260; col = (EU_C, NA_C)[i % 2]
            cr.save(); cr.translate(x, y); cr.scale(k, k); rrect(cr, -100, -100, 200, 200, 36); cr.set_source_rgb(*(col if i < 7 else GOLD[:3])); cr.fill()
            ptext(cr, '?' if i == 7 else str(i + 1), 0, 44, 130, INK, 1, sw=0, shadow=False); cr.restore()
        cr.restore()
        slam(cr, '8 ROUNDS', 540, 440, 150, WHITE, t, b['l0'])
        slam(cr, 'DECIDED BY THE LAST ONE', 540, 1400, 76, GOLD, t, w('h3', 'last') - 0.5)
    if key != 'h1':
        streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22))); f = 1 - prog(t, b['start'], b['start'] + 0.14)
        if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
    return True

def draw_title(cr, t):
    b = bt('title')
    if not (b['start'] <= t < b['end']): return False
    cr.save(); cam(cr, push(t, b['start'], b['end'], 1.05, 1.18), 0.03); split_globes(cr, t, 1.0, 1.0, 1.0, 8 * prog(t, b['start'], b['end'])); cr.restore()
    cr.set_source_rgba(0, 0, 0.03, 0.45); cr.paint()
    slam(cr, 'NORTH AMERICA', 540, 560, 112, NA_C, t, w('title', 'North'))
    tv = w('title', 'versus')
    if t >= tv: k = pop_k(t, tv, 0.3); cr.save(); cr.translate(540, 760); cr.scale(k, k); cr.new_path(); cr.arc(0, 0, 110, 0, 2 * math.pi); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 0, 42, 120, INK, 1, sw=0, shadow=False); cr.restore()
    slam(cr, 'EUROPE', 540, 1000, 190, EU_C, t, w('title', 'Europe'))
    tg = w('title', 'geography')
    if t >= tg: sx, sy = shake(t, tg, 14); cr.save(); cr.translate(sx, sy); slam(cr, 'THE GEOGRAPHY WAR', 540, 1240, 92, WHITE, t, tg); cr.restore()
    streaks(cr, 1 - ease_out(prog(t, b['start'], b['start'] + 0.22)))
    return True

def draw_end(cr, t):
    b = bt('end'); c = bt('cta')
    cr.save(); cam(cr, push(t, b['start'], c['end'], 1.0, 1.15), 0.02 * math.sin(t)); split_globes(cr, t, 1.0, 1.0, 1.0, 10 * (t - b['start'])); cr.restore()
    cr.set_source_rgba(0, 0, 0.03, 0.55); cr.paint()
    if t < c['start']:
        ptext(cr, '4', 300, 900, 380, NA_C, 1, sw=26); ptext(cr, '4', 780, 900, 380, EU_C, 1, sw=26); ptext(cr, '—', 540, 850, 160, WHITE, 1, sw=14)
        td = w('end', 'draw')
        if t >= td: sx, sy = shake(t, td, 18); cr.save(); cr.translate(sx, sy); slam(cr, 'A DRAW', 540, 1200, 190, GOLD, t, td); cr.restore()
        tb = w('end', 'unless')
        if t >= tb: slam(cr, '…UNLESS YOU BREAK THE TIE', 540, 1400, 70, WHITE, t, tb)
    else:
        for side, x, col, word, lab, rot in (('NA', 280, NA_C, 'North', ['NORTH', 'AMERICA'], -0.04), ('EU', 800, EU_C, 'Europe', ['EUROPE'], 0.04)):
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
    if draw_hook(cr, t): C.draw_captions(cr, t, 1720 if t < bt('h2')['start'] else 1680); return
    if draw_title(cr, t): return
    if t >= bt('end')['start']:
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
            if key == 'r7' and t >= w('r7', 'one') + 0.5: chip(cr, 'EUROPE NEEDS 1 MORE', 540, 1460, 50, CRIMSON, WHITE, pop_k(t, w('r7', 'one') + 0.5), 1)
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
    chords = [[50, 53, 57], [46, 50, 53], [41, 45, 48], [48, 52, 55]]  # Dm Bb F C: marching, epic
    for ci in range(int(dur / bar) + 1):
        ch = chords[ci % 4]; Lc = np.arange(int(bar * 1.15 * SR)) / SR; env = np.minimum(1, Lc / 0.15) * np.exp(-Lc * 0.7)
        put(music, ci * bar, sum(0.03 * (np.sin(2 * np.pi * note(m) * Lc) + 0.5 * np.sign(np.sin(2 * np.pi * note(m + 12) * Lc)) * 0.3) for m in ch) * env)
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
    def pop(t0, amp=0.05):
        Lp = np.arange(int(0.04 * SR)) / SR; put(fx, t0, amp * np.sin(2 * np.pi * 1100 * Lp) * np.exp(-Lp * 70))
    boom(0.03, 0.8); boom(w('h1', 'One'), 0.9); horn(w('h1', 'One')); boom(w('h2', 'other') + 0.15, 0.6)
    for k in ('h2', 'h3', 'title'): whoosh(bt(k)['start'] - 0.4)
    for wd in ('North', 'Europe', 'geography'): boom(w('title', wd), 0.7)
    horn(w('title', 'geography'), 0.09)
    for k, (ttl, win, _, vw) in ROUNDS.items():
        b = bt(k); whoosh(b['start'] - 0.4); boom(b['start'] + 0.03, 0.7); bell(b['start'] + 0.03, 0.1); whoosh(card_end(k) - 0.3, 0.25, 0.3)
        tv = w(k, vw); boom(tv, 0.85); horn(tv, 0.08); bell(tv, 0.08, 1568 if win == 'NA' else 1319)
    t0, t1 = w('r1', 'twenty') - 0.2, w('r1', 'Caribbean', end=True)
    for i in range(23): pop(lerp(t0, t1, i / 22))
    t0 = w('r1', 'Europe') + 0.1; t1 = w('r1', 'forty') + 0.9
    for i in range(44): pop(lerp(t0, t1, i / 43), 0.04)
    boom(w('end', 'draw'), 1.0); horn(w('end', 'draw'), 0.1)
    v = np.zeros(n)
    for s, a in T['clips']: put(v, s, a)
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, mode='same'); duck = np.convolve(1 - 0.55 * np.clip(env / 0.03, 0, 1), np.ones(9600) / 9600, mode='same')
    mix = music * duck + fx * (0.6 + 0.4 * duck) + v
    mix *= np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 1.2); mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(np.column_stack([mix, mix]), -1, 1) * 32767).astype('<i2').tobytes())

def setup(data_dir, cache):
    global G
    C.TL = C.build(C.WordVoice(cache)); G = Geo(data_dir)

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
    setup(data_dir, os.path.join(os.path.dirname(os.path.abspath(out)), 'voice_cache', 'edge_war'))
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
