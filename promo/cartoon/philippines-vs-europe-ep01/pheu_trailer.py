# 9:16 trailer Short for "Philippines vs Europe, Episode 01": real moments from the episode, then a cliffhanger end card
# pointing to the full episode (set it as the Short's Related video). Usage: python3 pheu_trailer.py <data_dir> <episode_9x16.mp4> <out_dir>
import os, sys, math, subprocess, cairo, numpy as np
import pheu as P
import season as S
from china import ptext, rrect, fit, chip, slam, pop_k, emoji, GOLD, WHITE, INK
from warballs import ball
from quiz import clamp, lerp, prog, ease_out
W, H, FPS, SR = 1080, 1920, 30, 44100
def main():
    data, src, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
    P.setup(data, os.path.join(os.path.dirname(os.path.abspath(src)), 'voice_cache', 'edge_pheu')); bt, w = P.bt, P.w
    clips = [(bt('h1')['start'], bt('h2')['end']),                      # insults
             (bt('h3')['start'] + 0.3, bt('h3')['start'] + 3.4),        # Europe lights up
             (bt('m1w')['start'], bt('m1w')['start'] + 2.0),            # SPAIN WINS!
             (bt('m6r3b')['start'], bt('m6r3b')['end']),                # tallest on Earth
             (bt('m7r4b')['start'], bt('m7r4b')['end']),                # Nazare wave
             (bt('m3r4b')['start'], bt('m3r4b')['start'] + 2.6),        # Christmas in September
             (bt('m10r5a')['end'] - 0.8, bt('m10r5b')['end'])]          # Apo vs Olympus
    # banner overlay for the clips
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
    cr.rectangle(0, 0, W, 96); cr.set_source_rgba(0.02, 0.03, 0.08, 0.88); cr.fill(); ptext(cr, 'PHILIPPINES vs EUROPE · EP 1', 540, 66, 44, GOLD, 1, sw=0, shadow=False)
    rrect(cr, 170, 1790, 740, 90, 45); cr.set_source_rgb(0.9, 0.08, 0.12); cr.fill(); ptext(cr, 'FULL EPISODE: LINK BELOW', 540, 1850, 44, WHITE, 1, sw=0, shadow=False)
    s.write_to_png(f'{out}/trailer_ov.png')
    parts = []
    for j, (a, b) in enumerate(clips):
        p = f'{out}/tclip{j}.mp4'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', src, '-loop', '1', '-i', f'{out}/trailer_ov.png',
                        '-t', f'{b - a:.3f}', '-filter_complex', '[0:v][1:v]overlay=0:0:shortest=1,format=yuv420p[v];[0:a]afade=t=in:d=0.05,afade=t=out:st=%.3f:d=0.08[a]' % (b - a - 0.08), '-map', '[v]', '-map', '[a]', '-shortest',
                        '-r', '30', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', p], check=True)
        parts.append(p)
    # end card with narration
    S.tts("Ten countries. Five rounds each. Did the Philippines beat Europe? Watch the full episode, link below!", f'{out}/tr_end.mp3', rate='+10%')
    v = S.load_wav(f'{out}/tr_end.mp3'); dur = len(v) / SR + 2.2
    eu = [m[0] for m in P.MATCHES]
    def draw(cr, t):
        g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.05, 0.08, 0.25); g.add_color_stop_rgb(1, 0.22, 0.05, 0.25); cr.set_source(g); cr.paint()
        for j in range(28):
            a = j / 28 * 2 * math.pi + t * 0.25; cr.new_path(); cr.move_to(540, 820); cr.line_to(540 + 2000 * math.cos(a), 820 + 2000 * math.sin(a)); cr.line_to(540 + 2000 * math.cos(a + 0.08), 820 + 2000 * math.sin(a + 0.08)); cr.close_path(); cr.set_source_rgba(1, 0.8, 0.2, 0.06); cr.fill()
        for j, n in enumerate(eu):
            a = -math.pi / 2 + j / len(eu) * 2 * math.pi; k = ease_out(prog(t, 0.1 + j * 0.06, 0.5 + j * 0.06))
            ball(cr, n, 540 + lerp(900, 380, k) * math.cos(a), 820 + lerp(900, 340, k) * math.sin(a), 74, 'angry', 0, -math.cos(a))
        ball(cr, 'Philippines', 540, 820, 190 - abs(math.sin(t * 5)) * 6, 'shock' if t > 2.2 else 'angry', 0, 0)
        slam(cr, 'DID THE PHILIPPINES', 540, 200, 84, WHITE, t, 0.15); slam(cr, 'BEAT EUROPE?', 540, 320, 110, GOLD, t, 0.55)
        for j, (lab, col) in enumerate((('W ?', (0.18, 0.75, 0.42)), ('L ?', (0.94, 0.26, 0.35)))):
            tj = 1.4 + j * 0.3
            if t >= tj:
                kk = pop_k(t, tj, 0.3); cr.save(); cr.translate(370 + j * 340, 1300); cr.scale(kk, kk); rrect(cr, -140, -90, 280, 180, 30); cr.set_source_rgb(*col); cr.fill(); ptext(cr, lab, 0, 34, 110, INK, 1, sw=0, shadow=False); cr.restore()
        tf = 2.4
        if t >= tf:
            k = pop_k(t, tf, 0.3); cr.save(); cr.translate(540, 1560); cr.scale(k, k); rrect(cr, -400, -70, 800, 130, 65); cr.set_source_rgb(0.9, 0.08, 0.12); cr.fill(); ptext(cr, 'WATCH FULL EPISODE', 0, 22, 62, WHITE, 1, sw=0, shadow=False); cr.restore()
            for j in range(3): emoji(cr, '👇', 300 + j * 240, 1760 + 22 * abs(math.sin(t * 6 + j)), 110, 1)
        f = 1 - prog(t, 0, 0.12)
        if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
    S.W, S.H = W, H
    S.write_wav(f'{out}/tr_end.wav', S.sfx_track(dur, [('whoosh', 0.0), ('boom', 0.15), ('boom', 0.55), ('pop', 1.4), ('pop', 1.7), ('ding', 2.4)], v, 0.4))
    S.render(f'{out}/tr_end.mp4', dur, draw, f'{out}/tr_end.wav'); parts.append(f'{out}/tr_end.mp4')
    open(f'{out}/tparts.txt', 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{out}/tparts.txt', '-c', 'copy', '-movflags', '+faststart', f'{out}/philippines-vs-europe-ep01-trailer.mp4'], check=True)
    print('trailer done')
if __name__ == '__main__':
    main()
