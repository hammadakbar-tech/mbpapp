# "Australia vs the World: Season 1", a 16:9 long-form compilation of the 9:16 countryballs episodes.
# Each episode plays full-height in the centre over a blurred copy of itself. Side panels show the episode
# and a season leaderboard; animated cards sit between episodes; narrated intro and outro.
# Usage: python3 season.py <repo_cartoon_dir> <data_dir> <out_dir>
import asyncio, math, os, ssl, subprocess, sys, wave
import numpy as np, cairo
import edge_tts, edge_tts.communicate as _etc
if os.path.exists('/root/.ccr/ca-bundle.crt'): _etc._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
import warballs as B
from warballs import ball
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, GOLD, WHITE, INK, CRIMSON
from quiz import clamp, lerp, prog, ease_out, ease_io, hexc
W, H, FPS, SR = 1920, 1080, 30, 44100
AU_C = hexc('#FFC233')[:3]; WIN_C, LOSS_C, TIE_C = hexc('#2DBE6C')[:3], hexc('#F0435A')[:3], hexc('#4F8CFF')[:3]
EPS = [  # dir, file, opponents (flag codes), title, result, score
    ('australia-vs-usa', 'australia-vs-usa.mp4', ['us'], 'USA', 'T', '4–4'),
    ('australia-vs-japan', 'australia-vs-japan.mp4', ['jp'], 'JAPAN', 'W', '5–4'),
    ('australia-vs-france', 'australia-vs-france.mp4', ['fr'], 'FRANCE', 'L', '4–5'),
    ('australia-vs-uk', 'australia-vs-uk.mp4', ['gb'], 'THE UK', 'W', '5–4'),
    ('australia-vs-canada-economic-war-v2', 'australia-vs-canada-economic-war.mp4', ['ca'], 'CANADA', 'W', '5–4'),
    ('australia-vs-greece', 'australia-vs-greece.mp4', ['gr'], 'GREECE', 'L', '4–5'),
    ('australia-vs-greece-rematch', 'australia-vs-greece-rematch.mp4', ['gr'], 'GREECE II', 'T', '1–1'),
    ('tag-team-aus-can-vs-rus-ind', 'tag-team-war.mp4', ['ru', 'in'], 'RUSSIA + INDIA', 'T', '4–4'),
    ('australia-vs-philippines', 'australia-vs-philippines.mp4', ['ph'], 'PHILIPPINES', 'T', '4–4'),
    ('australia-vs-the-world-cricket-war', 'australia-vs-the-world-cricket-war.mp4', ['in', 'gb-eng', 'pk', 'nzfern'], 'CRICKET WORLD', 'T', '4–4'),
    ('usa-vs-philippines-vs-australia', 'usa-vs-philippines-vs-australia.mp4', ['us', 'ph'], 'USA + PHILIPPINES', 'T', '2–2–2'),
    ('philippines-vs-indonesia', 'philippines-vs-indonesia.mp4', ['ph', 'id'], 'BONUS: AUSSIE REF', '-', '')]
TAGS = {1: 'TAG TEAM WITH CANADA', 10: 'CRICKET WAR', 11: '3-WAY FOOD FIGHT', 12: 'PHILIPPINES vs INDONESIA'}
RES_COL = {'W': WIN_C, 'L': LOSS_C, 'T': TIE_C, '-': (0.6, 0.6, 0.7)}
RES_TXT = {'W': 'WIN', 'L': 'LOSS', 'T': 'TIE', '-': 'BONUS'}
def record(n): r = [e[4] for e in EPS[:n]]; return r.count('W'), r.count('L'), r.count('T')

def bg(cr, t, a=1.0):
    g = cairo.LinearGradient(0, 0, W, H); g.add_color_stop_rgb(0, 0.03, 0.04, 0.12); g.add_color_stop_rgb(1, 0.1, 0.06, 0.2); cr.set_source(g); cr.paint()
    for x0, col in ((0, AU_C), (W, (0.3, 0.55, 1))):
        r = cairo.RadialGradient(x0, H, 50, x0, H, 1100); r.add_color_stop_rgba(0, *col, 0.3); r.add_color_stop_rgba(1, *col, 0); cr.set_source(r); cr.paint()
    rng = np.random.default_rng(3)
    for _ in range(120): x, y, s = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.8, 2.4); cr.new_path(); cr.arc(x, y, s, 0, 6.283); cr.set_source_rgba(1, 1, 1, 0.2 + 0.2 * math.sin(t * 2 + x)); cr.fill()
def flagball(cr, code, x, y, r, mood='angry', look=0.0): ball(cr, code, x, y, r, mood, 0, look)
def team(cr, codes, x, y, r, look):
    n = len(codes)
    if n == 1: flagball(cr, codes[0], x, y, r, 'angry', look); return
    rr = r * (0.72 if n == 2 else 0.55)
    for j, c in enumerate(codes): a = (j / n) * 2 * math.pi - math.pi / 2; d = r * 0.55; flagball(cr, c, x + d * math.cos(a), y + d * math.sin(a) * 0.8, rr, 'angry', look)
def leaderboard(cr, x, y, upto, now=None, hl=None, k=1.0):
    """Season table: results revealed for episodes < upto; 'now' marks the one playing."""
    w_, l_, t_ = record(upto); rrect(cr, x, y, 580, 940, 30); cr.set_source_rgba(0.02, 0.03, 0.08, 0.82); cr.fill()
    ptext(cr, "AUSTRALIA'S SEASON", x + 290, y + 62, 40, AU_C, 1, sw=0, shadow=False)
    for j, (lab, v, col) in enumerate((('W', w_, WIN_C), ('L', l_, LOSS_C), ('T', t_, TIE_C))):
        cx = x + 130 + j * 160; ptext(cr, str(v), cx, y + 150, 72, col, 1, sw=0, shadow=False); ptext(cr, lab, cx, y + 190, 30, WHITE, 0.8, fam='Poppins ExtraBold', sw=0, shadow=False)
    for i, e in enumerate(EPS):
        yy = y + 245 + i * 56; cur = (now == i); done = i < upto
        if cur: rrect(cr, x + 14, yy - 30, 552, 50, 14); cr.set_source_rgba(*AU_C, 0.25); cr.fill()
        ptext(cr, f'{i + 1:02d}', x + 50, yy + 8, 26, WHITE, 0.6, fam='Poppins ExtraBold', sw=0, shadow=False, anchor='l')
        ptext(cr, 'vs ' + e[3] if e[4] != '-' else e[3], x + 100, yy + 8, fit(cr, 'vs ' + e[3], 26, 300), WHITE if done or cur else (0.55, 0.57, 0.65), 1, fam='Poppins ExtraBold', sw=0, shadow=False, anchor='l')
        if done:
            kk = k if (hl == i) else 1.0; col = RES_COL[e[4]]
            if kk > 0: cr.save(); cr.translate(x + 500, yy); cr.scale(kk, kk); rrect(cr, -58, -22, 116, 40, 20); cr.set_source_rgb(*col); cr.fill(); ptext(cr, RES_TXT[e[4]], 0, 9, 22, INK, 1, sw=0, shadow=False); cr.restore()
        elif cur: cr.new_path(); cr.arc(x + 452, yy, 8, 0, 6.283); cr.set_source_rgba(*LOSS_C, 0.9); cr.fill(); ptext(cr, 'NOW', x + 505, yy + 8, 24, AU_C, 1, fam='Poppins ExtraBold', sw=0, shadow=False)
        else: ptext(cr, '?', x + 500, yy + 8, 26, (0.55, 0.57, 0.65), 1, sw=0, shadow=False)
time_hint = [0.0]

def overlay_png(i, path):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s); e = EPS[i]
    rrect(cr, 40, 70, 576, 940, 30); cr.set_source_rgba(0.02, 0.03, 0.08, 0.82); cr.fill()
    ptext(cr, 'AUSTRALIA vs THE WORLD', 328, 140, 40, AU_C, 1, sw=0, shadow=False); ptext(cr, f'SEASON 1 · EPISODE {i + 1}/{len(EPS)}', 328, 190, 30, WHITE, 0.85, fam='Poppins ExtraBold', sw=0, shadow=False)
    if e[4] == '-': team(cr, ['ph'], 210, 430, 110, 0.6); team(cr, ['id'], 450, 430, 110, -0.6); flagball(cr, 'au', 330, 300, 60, 'happy')
    else:
        team(cr, ['au', 'ca'] if i == 7 else ['au'], 190, 430, 115, 0.6); team(cr, e[2], 470, 430, 115, -0.6)
        cr.new_path(); cr.arc(330, 430, 44, 0, 6.283); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 330, 448, 46, INK, 1, sw=0, shadow=False)
    ttl = 'AUSTRALIA THE REF' if e[4] == '-' else 'AUSTRALIA' + (' + CANADA' if i == 7 else ''); ptext(cr, ttl, 328, 640, fit(cr, ttl, 60, 520), AU_C, 1, sw=8)
    ptext(cr, 'vs ' + e[3] if e[4] != '-' else 'PHILIPPINES vs INDONESIA', 328, 715, fit(cr, 'vs ' + e[3], 56, 520), WHITE, 1, sw=8)
    if i + 1 in TAGS and e[4] != '-': chip(cr, TAGS[i + 1], 328, 790, 30, GOLD, INK, 1, 1)
    rrect(cr, 88, 880, 480, 84, 42); cr.set_source_rgb(0.9, 0.08, 0.12); cr.fill(); ptext(cr, 'SUBSCRIBE FOR SEASON 2', 328, 935, 34, WHITE, 1, sw=0, shadow=False)
    time_hint[0] = 0.25; leaderboard(cr, 1304, 70, i, now=i)
    s.write_to_png(path)

def tts(text, path, voice='en-US-GuyNeural', rate='+4%'):
    async def go():
        with open(path, 'wb') as f:
            async for ch in edge_tts.Communicate(text, voice, rate=rate).stream():
                if ch['type'] == 'audio': f.write(ch['data'])
    for a in range(5):
        try: asyncio.run(go()); return
        except Exception:
            import time; time.sleep(2 + 2 * a)
    raise RuntimeError('tts failed')
def load_wav(path):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-ac', '1', '-ar', str(SR), path + '.wav'], check=True)
    with wave.open(path + '.wav') as w: return np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float) / 32768
def sfx_track(dur, events, voice=None, vstart=0.0, music=True):
    n = int(dur * SR); out = np.zeros(n); rng = np.random.default_rng(1)
    def put(t0, sig):
        i0 = int(t0 * SR)
        if 0 <= i0 < n: out[i0:i0 + len(sig)] += sig[:n - i0]
    L = lambda d: np.arange(int(d * SR)) / SR
    for kind, t0 in events:
        if kind == 'boom': l = L(1.2); put(t0, 0.6 * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-l * 10)) / SR) * np.exp(-l * 3))
        if kind == 'whoosh': z = rng.standard_normal(int(0.4 * SR)); put(t0, 0.25 * np.convolve(z, np.ones(25) / 25, 'same') * np.linspace(0, 1, len(z)) ** 2)
        if kind == 'ding': l = L(1.0); put(t0, 0.12 * (np.sin(2 * np.pi * 1568 * l) + 0.5 * np.sin(2 * np.pi * 2349 * l)) * np.exp(-l * 4))
        if kind == 'pop': l = L(0.06); put(t0, 0.1 * np.sin(2 * np.pi * (900 + 400 * np.exp(-l * 60)) * l) * np.exp(-l * 50))
    if music:
        beat = 60 / 116; tt = np.arange(n) / SR
        for bi in range(int(dur / (beat / 2))):
            if bi % 4 in (0, 3): l = L(0.25); put(bi * beat / 2, 0.25 * np.sin(2 * np.pi * np.cumsum(90 + 70 * np.exp(-l * 30)) / SR) * np.exp(-l * 14))
        pad = sum(0.025 * np.sin(2 * np.pi * f * tt) for f in (220, 261.6, 329.6)) * (0.6 + 0.4 * np.sin(tt * 0.8)); out += pad
    if voice is not None:
        v = voice / max(1e-6, np.abs(voice).max()) * 0.9; put(vstart, v)
    fade = np.minimum(1, np.arange(n) / SR / 0.05) * np.minimum(1, (dur - np.arange(n) / SR) / 0.3); out *= fade
    return out / max(1.0, np.abs(out).max() / 0.95)
def write_wav(path, x):
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(np.column_stack([x, x]), -1, 1) * 32767).astype('<i2').tobytes())
def render(path, dur, draw, wav):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', path], stdin=subprocess.PIPE)
    for f in range(int(dur * FPS)):
        t = f / FPS; time_hint[0] = t; cr.identity_matrix(); draw(cr, t); surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait()

def subscribe(cr, t, t0, x, y, s=1.0):
    tc = t0 + 1.3; clicked = t >= tc; k = pop_k(t, t0, 0.3) * s
    cr.save(); cr.translate(x, y); cr.scale(k, k); txt = '✓ SUBSCRIBED' if clicked else 'SUBSCRIBE'
    txt = 'SUBSCRIBED' if clicked else 'SUBSCRIBE'; bw = tw(cr, txt, 60) + 120
    rrect(cr, -bw / 2, -60, bw, 110, 55); cr.set_source_rgb(*((0.32, 0.32, 0.36) if clicked else (0.9, 0.08, 0.12))); cr.fill(); ptext(cr, txt, 0, 18, 60, WHITE, 1, sw=0, shadow=False); cr.restore()
    emoji(cr, '🔔', x + (bw / 2 + 70) * k, y - 5, 80 * k, 1, rot=(0.5 * math.sin((t - tc) * 30) * math.exp(-(t - tc) * 3)) if clicked else 0)
    if t < tc + 0.4: emoji(cr, '👆', lerp(x + 400, x + 20, ease_out(prog(t, t0 + 0.2, tc))), lerp(y + 260, y + 60, ease_out(prog(t, t0 + 0.2, tc))), 110, clamp((tc + 0.4 - t) * 4))

def main():
    repo, data, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
    for c in ('au', 'us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id', 'gb-eng', 'pk', 'nzfern'): B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
    segs = []; chapters = []; clock = 0.0
    def add(path, label=None):
        nonlocal clock
        d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout)
        if label: chapters.append((clock, label))
        segs.append(path); clock += d
    # ---- intro ----
    intro_txt = ("Australia took on the world. Japan, France, the UK, Greece, a cricket war, and even a food fight. "
                 "This is the entire first season. Stay to the end for Australia's final record!")
    tts(intro_txt, f'{out}/intro.mp3'); v = load_wav(f'{out}/intro.mp3'); idur = len(v) / SR + 1.2
    opp = ['us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'pk', 'id']
    def d_intro(cr, t):
        bg(cr, t); e = ease_out(prog(t, 0.1, 1.0))
        for j, c in enumerate(opp):
            a = -math.pi / 2 + j / len(opp) * 2 * math.pi; tj = 0.4 + j * 0.25 * (idur - 3) / len(opp) / 1.0
            if t < tj: continue
            k = ease_out(prog(t, tj, tj + 0.35)); flagball(cr, c, 960 + lerp(1400, 470, k) * math.cos(a), 600 + lerp(900, 330, k) * math.sin(a), 70, 'angry', -math.cos(a))
        flagball(cr, 'au', 960, 600, 160 * e + 1, 'angry', 0)
        slam(cr, 'AUSTRALIA vs THE WORLD', 960, 150, 96, AU_C, t, 0.2); slam(cr, 'SEASON 1 · ALL 12 EPISODES', 960, 1010, 54, WHITE, t, idur - 4.5)
    sfx = [('boom', 0.2), ('whoosh', 0.0)] + [('pop', 0.4 + j * 0.25 * (idur - 3) / len(opp) + 0.3) for j in range(len(opp))] + [('boom', idur - 4.5)]
    write_wav(f'{out}/intro.wav', sfx_track(idur, sfx, v, 0.3)); render(f'{out}/s00_intro.mp4', idur, d_intro, f'{out}/intro.wav'); add(f'{out}/s00_intro.mp4', 'Intro: Australia vs the World')
    # ---- episodes with cards ----
    for i, e in enumerate(EPS):
        cd = 3.6
        def d_card(cr, t, i=i, e=e):
            bg(cr, t); k = ease_out(prog(t, 0.0, 0.4))
            if i > 0: leaderboard(cr, 1304, 70, i, now=None, hl=i - 1, k=pop_k(t, 0.5, 0.35))
            else: leaderboard(cr, 1304, 70, 0, now=0)
            x0 = lerp(-400, 0, k); cr.save(); cr.translate(x0, 0)
            ptext(cr, 'NEXT UP' if i < len(EPS) - 1 else 'BONUS EPISODE', 650, 200, 60, GOLD, 1, sw=8)
            ptext(cr, f'EPISODE {i + 1}', 650, 330, 130, WHITE, 1, sw=14)
            if e[4] == '-': team(cr, ['ph'], 450, 640, 140, 0.6); team(cr, ['id'], 850, 640, 140, -0.6); flagball(cr, 'au', 650, 470, 80, 'happy')
            else:
                team(cr, ['au', 'ca'] if i == 7 else ['au'], 430, 640, 150, 0.6); team(cr, e[2], 870, 640, 150, -0.6)
                cr.new_path(); cr.arc(650, 640, 60, 0, 6.283); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 650, 664, 64, INK, 1, sw=0, shadow=False)
            lab = ('AUSTRALIA' + (' + CANADA' if i == 7 else '') + ' vs ' + e[3]) if e[4] != '-' else 'PHILIPPINES vs INDONESIA'
            ptext(cr, lab, 650, 900, fit(cr, lab, 64, 1150), AU_C, 1, sw=9)
            if i + 1 in TAGS and e[4] != '-': chip(cr, TAGS[i + 1], 650, 985, 36, GOLD, INK, 1, 1)
            if e[4] == '-': chip(cr, 'AUSTRALIA DROPS IN AS THE REF', 650, 985, 36, GOLD, INK, 1, 1)
            cr.restore()
        write_wav(f'{out}/card.wav', sfx_track(cd, [('whoosh', 0.0), ('boom', 0.1), ('ding', 0.55)], music=True))
        cp = f'{out}/s{i + 1:02d}a_card.mp4'; render(cp, cd, d_card, f'{out}/card.wav')
        lab = (f"Ep {i + 1}: Australia{' + Canada' if i == 7 else ''} vs {e[3].title().replace('Uk', 'UK').replace('Usa', 'USA').replace(' Ii', ' II')}") if e[4] != '-' else 'Bonus: Philippines vs Indonesia (Australia refs)'
        add(cp, lab)
        ov = f'{out}/ov{i + 1:02d}.png'; overlay_png(i, ov); src = os.path.join(repo, e[0], e[1]); ep = f'{out}/s{i + 1:02d}b_ep.mp4'
        fc = ('[0:v]split[a][b];[a]scale=480:-2,crop=480:270,boxblur=12:2,eq=brightness=-0.22:saturation=1.2,scale=1920:1080[bg];'
              '[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0[v1];[v1][1:v]overlay=0:0,format=yuv420p[v]')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-loop', '1', '-i', ov, '-filter_complex', fc, '-map', '[v]', '-map', '0:a', '-shortest',
                        '-r', str(FPS), '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', ep], check=True)
        add(ep); print('episode', i + 1, 'done', flush=True)
    # ---- outro ----
    w_, l_, t_ = record(len(EPS) - 1)
    out_txt = (f"That's season one! Australia finished with {w_} wins, {l_} losses, and {t_} ties. Six ties, and you get to settle them. "
               "Which rematch should open season two? Comment below, and subscribe so you don't miss it!")
    tts(out_txt, f'{out}/outro.mp3'); v = load_wav(f'{out}/outro.mp3'); odur = len(v) / SR + 3.5
    def d_outro(cr, t):
        bg(cr, t); leaderboard(cr, 1304, 70, len(EPS) - 1, now=None)
        slam(cr, 'SEASON 1 COMPLETE', 650, 180, 100, AU_C, t, 0.2)
        flagball(cr, 'au', 650, 470, 190 - abs(math.sin(t * 5)) * 6, 'happy', 0)
        for j, (lab, v_, col) in enumerate((('WINS', w_, WIN_C), ('LOSSES', l_, LOSS_C), ('TIES', t_, TIE_C))):
            tj = 1.0 + j * 0.5
            if t >= tj:
                k = pop_k(t, tj, 0.3); cx = 330 + j * 320; cr.save(); cr.translate(cx, 790); cr.scale(k, k); rrect(cr, -130, -110, 260, 200, 30); cr.set_source_rgb(*col); cr.fill()
                ptext(cr, str(v_), 0, 30, 120, INK, 1, sw=0, shadow=False); ptext(cr, lab, 0, 75, 34, INK, 1, fam='Poppins ExtraBold', sw=0, shadow=False); cr.restore()
        if t >= odur - 6.5: chip(cr, 'COMMENT: WHICH REMATCH FIRST?', 650, 980, 40, WHITE, INK, pop_k(t, odur - 6.5), 1)
        if t >= odur - 4.0: subscribe(cr, t, odur - 4.0, 1594, 990, 0.9)
    sfx = [('boom', 0.2), ('pop', 1.0), ('pop', 1.5), ('pop', 2.0), ('ding', 2.1), ('ding', odur - 4.0 + 1.3)]
    write_wav(f'{out}/outro.wav', sfx_track(odur, sfx, v, 0.4)); render(f'{out}/s99_outro.mp4', odur, d_outro, f'{out}/outro.wav'); add(f'{out}/s99_outro.mp4', 'Final record & Season 2')
    with open(f'{out}/segs.txt', 'w') as f:
        for p in segs: f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{out}/segs.txt', '-c', 'copy', '-movflags', '+faststart', f'{out}/season1.mp4'], check=True)
    with open(f'{out}/chapters.txt', 'w') as f:
        for s_, lab in chapters: f.write(f'{int(s_ // 60)}:{int(s_ % 60):02d} {lab}\n')
    print(open(f'{out}/chapters.txt').read()); print('total', clock)

if __name__ == '__main__':
    main()
