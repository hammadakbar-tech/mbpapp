# Fast cold-open intro for the Season 1 compilation: rapid montage of real episode moments, a "did Australia
# beat the world?" retention hook (record hidden until the end), then straight into Episode 1.
# Usage: python3 season_intro.py <repo_cartoon_dir> <data_dir> <out_dir>
import math, os, subprocess, sys, glob
import numpy as np, cairo
import season as S
import warballs as B
from china import ptext, rrect, tw, fit, emoji, pop_k, chip, slam, GOLD, WHITE, INK, CRIMSON
from quiz import clamp, lerp, prog, ease_out, ease_io
W, H, FPS, SR = 1920, 1080, 30, 44100
CLIPS = [('australia-vs-usa/australia-vs-usa.mp4', 1.0, 'vs THE USA!'), ('australia-vs-uk/australia-vs-uk.mp4', 1.0, 'vs THE UK!'),
         ('australia-vs-greece/australia-vs-greece.mp4', 1.0, 'vs GREECE!'), ('australia-vs-canada-economic-war-v2/australia-vs-canada-economic-war.mp4', 1.0, 'vs CANADA!'),
         ('australia-vs-philippines/australia-vs-philippines.mp4', 7.6, 'vs THE PHILIPPINES!'), ('australia-vs-the-world-cricket-war/australia-vs-the-world-cricket-war.mp4', 7.0, 'vs THE CRICKET WORLD!'),
         ('usa-vs-philippines-vs-australia/usa-vs-philippines-vs-australia.mp4', 9.3, 'A FOOD FIGHT!'), ('philippines-vs-indonesia/philippines-vs-indonesia.mp4', 102.3, 'EVEN AS THE REF!')]
CL = 0.7
def main():
    repo, data, out = sys.argv[1:4]; tmp = os.path.join(out, 'intro_frames'); os.makedirs(tmp, exist_ok=True)
    for c in ('au', 'us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id'): B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
    fc = '[0:v]split[a][b];[a]scale=480:-2,crop=480:270,boxblur=12:2,eq=brightness=-0.3:saturation=1.3,scale=1920:1080[bg];[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0'
    for j, (src, t0, _) in enumerate(CLIPS):
        if not glob.glob(f'{tmp}/c{j}_*.png'):
            subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(CL), '-i', os.path.join(repo, src), '-filter_complex', fc, '-r', str(FPS), f'{tmp}/c{j}_%03d.png'], check=True)
    frames = [sorted(glob.glob(f'{tmp}/c{j}_*.png')) for j in range(len(CLIPS))]
    lines = [("Australia versus the world. Eleven countries. One crazy season.", 0.15), ("Did Australia beat them all?", 5.75), ("Watch every episode, right now!", 8.45)]
    voices = []
    for k, (txt, st) in enumerate(lines):
        S.tts(txt, f'{out}/in{k}.mp3', rate='+14%'); voices.append((S.load_wav(f'{out}/in{k}.mp3'), st))
    m_end = CL * len(CLIPS); h_end = m_end + 2.9; dur = max(h_end + 1.6, voices[-1][1] + len(voices[-1][0]) / SR + 0.35)
    cache = {}
    def surf(p):
        if p not in cache: cache.clear(); cache[p] = cairo.ImageSurface.create_from_png(p)
        return cache[p]
    def draw(cr, t):
        if t < m_end:
            j = min(len(CLIPS) - 1, int(t / CL)); lt = t - j * CL; fr = frames[j][min(len(frames[j]) - 1, int(lt * FPS))]
            z = lerp(1.12, 1.0, ease_out(clamp(lt / 0.25))); cr.save(); cr.translate(960, 540); cr.scale(z, z); cr.rotate(0.02 * (1 if j % 2 else -1) * (1 - clamp(lt / 0.2))); cr.translate(-960, -540)
            cr.set_source_surface(surf(fr), 0, 0); cr.paint(); cr.restore()
            f = 1 - clamp(lt / 0.08)
            if f > 0: cr.set_source_rgba(1, 1, 1, 0.55 * f); cr.paint()
            lab = CLIPS[j][2]; side = 330 if j % 2 == 0 else 1600
            cr.save(); cr.translate(side, 540); cr.rotate(-0.06 if j % 2 == 0 else 0.06); k = pop_k(t, j * CL, 0.18); cr.scale(k, k)
            ptext(cr, lab, 0, 0, fit(cr, lab, 92, 540), S.AU_C if j < 6 else GOLD, 1, sw=14); cr.restore()
            rrect(cr, 640, 30, 640, 84, 42); cr.set_source_rgba(0.02, 0.03, 0.08, 0.85); cr.fill(); ptext(cr, 'AUSTRALIA vs THE WORLD', 960, 88, 46, S.AU_C, 1, sw=0, shadow=False)
            ptext(cr, f'{j + 1}/8', 960, 1040, 30, WHITE, 0.6, fam='Poppins ExtraBold', sw=0, shadow=False)
            return
        S.bg(cr, t); lt = t - m_end
        if t < h_end:
            sx, sy = (math.sin(t * 90) * 12 * math.exp(-lt * 6), math.cos(t * 77) * 12 * math.exp(-lt * 6))
            cr.save(); cr.translate(sx, sy); S.flagball(cr, 'au', 960, 560, 140 + 6 * math.sin(t * 8), 'shock', 0)
            slam(cr, 'DID AUSTRALIA', 960, 170, 120, WHITE, t, m_end + 0.02); slam(cr, 'BEAT THE WORLD?', 960, 310, 120, S.AU_C, t, m_end + 0.35); cr.restore()
            for k_, (lab, col) in enumerate((('WINS', S.WIN_C), ('LOSSES', S.LOSS_C), ('TIES', S.TIE_C))):
                tk = m_end + 0.9 + k_ * 0.25
                if t >= tk:
                    kk = pop_k(t, tk, 0.25); cx = 960 + (k_ - 1) * 380
                    cr.save(); cr.translate(cx, 850); cr.scale(kk, kk); rrect(cr, -160, -95, 320, 190, 30); cr.set_source_rgb(*col); cr.fill()
                    ptext(cr, '?', 0, 22, 120, INK, 1, sw=0, shadow=False); ptext(cr, lab, 0, 75, 34, INK, 1, fam='Poppins ExtraBold', sw=0, shadow=False); cr.restore()
            tr = m_end + 1.9
            if t >= tr: chip(cr, 'FINAL RECORD AT THE END', 960, 1025, 44, GOLD, INK, pop_k(t, tr), 1)
            return
        lt = t - h_end; k = ease_out(clamp(lt / 0.3))
        opp = ['us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id']
        for j, c in enumerate(opp):
            a = -math.pi / 2 + j / len(opp) * 2 * math.pi; S.flagball(cr, c, 960 + lerp(1500, 520, k) * math.cos(a), 545 + lerp(1000, 300, k) * math.sin(a), 74, 'angry', -math.cos(a))
        S.flagball(cr, 'au', 960, 545, 170, 'angry', 0)
        slam(cr, 'ALL 12 EPISODES', 960, 160, 110, S.AU_C, t, h_end + 0.05); slam(cr, "LET'S GO!", 960, 1010, 100, WHITE, t, h_end + 0.45)
        zf = prog(t, dur - 0.35, dur)
        if zf > 0: cr.set_source_rgba(1, 1, 1, zf); cr.paint()
    ev = [('boom', 0.0)] + [('whoosh', j * CL - 0.12) for j in range(1, len(CLIPS))] + [('boom', j * CL) for j in range(len(CLIPS))] + [('pop', j * CL + 0.05) for j in range(len(CLIPS))]
    ev += [('boom', m_end), ('boom', m_end + 0.35), ('pop', m_end + 0.9), ('pop', m_end + 1.12), ('pop', m_end + 1.4), ('ding', m_end + 1.9), ('whoosh', h_end - 0.15), ('boom', h_end + 0.05), ('boom', h_end + 0.45), ('whoosh', dur - 0.4)]
    mix = S.sfx_track(dur, ev, music=True)
    for v, st in voices:
        i0 = int(st * SR); v = v / max(1e-6, np.abs(v).max()) * 0.9; mix[i0:i0 + len(v)] += v[:len(mix) - i0]
    mix = mix / max(1.0, np.abs(mix).max() / 0.97)
    S.write_wav(f'{out}/intro2.wav', mix); S.render(f'{out}/s00_intro.mp4', dur, draw, f'{out}/intro2.wav'); print('intro', round(dur, 2))

if __name__ == '__main__':
    main()
