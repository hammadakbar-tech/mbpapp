# 9:16 trailer Short for "Australia vs the World: Full Season 1": real moments from the original episodes,
# then a cliffhanger end card pointing to the full video (set it as the Short's Related video).
# Usage: python3 season1_trailer.py <repo_cartoon_dir> <data_dir> <out_dir>
import os, sys, math, subprocess, cairo
import season as S
import warballs as B
from warballs import ball
from china import ptext, rrect, slam, pop_k, emoji, GOLD, WHITE, INK
from quiz import lerp, prog, ease_out
W, H, SR = 1080, 1920, 44100
CLIPS = [('australia-vs-uk/australia-vs-uk.mp4', 0.0, 2.5), ('australia-vs-greece/australia-vs-greece.mp4', 0.0, 2.5),
         ('australia-vs-the-world-cricket-war/australia-vs-the-world-cricket-war.mp4', 5.0, 7.8), ('australia-vs-philippines/australia-vs-philippines.mp4', 8.4, 10.8),
         ('australia-vs-canada-economic-war-v2/australia-vs-canada-economic-war.mp4', 0.0, 2.4), ('usa-vs-philippines-vs-australia/usa-vs-philippines-vs-australia.mp4', 7.7, 10.4),
         ('philippines-vs-indonesia/philippines-vs-indonesia.mp4', 101.8, 104.4)]
def main():
    repo, data, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
    for c in ('au', 'us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id'): B.FL[c] = cairo.ImageSurface.create_from_png(os.path.join(data, 'flags', c + '.png'))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
    cr.rectangle(0, 0, W, 96); cr.set_source_rgba(0.02, 0.03, 0.08, 0.88); cr.fill(); ptext(cr, 'AUSTRALIA vs THE WORLD · FULL SEASON', 540, 66, 40, S.AU_C, 1, sw=0, shadow=False)
    rrect(cr, 150, 1790, 780, 90, 45); cr.set_source_rgb(0.9, 0.08, 0.12); cr.fill(); ptext(cr, 'FULL SEASON: LINK BELOW', 540, 1850, 46, WHITE, 1, sw=0, shadow=False)
    s.write_to_png(f'{out}/ov.png'); parts = []
    for j, (src, a, b) in enumerate(CLIPS):
        p = f'{out}/clip{j}.mp4'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', os.path.join(repo, src), '-loop', '1', '-i', f'{out}/ov.png',
                        '-t', f'{b - a:.3f}', '-filter_complex', '[0:v][1:v]overlay=0:0:shortest=1,format=yuv420p[v];[0:a]afade=t=in:d=0.04,afade=t=out:st=%.3f:d=0.08[a]' % (b - a - 0.08), '-map', '[v]', '-map', '[a]', '-shortest',
                        '-r', '30', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', p], check=True)
        parts.append(p)
    S.tts("Australia fought eleven countries. Did it beat the world? The answer is in the full season. Link below!", f'{out}/end.mp3', rate='+10%')
    v = S.load_wav(f'{out}/end.mp3'); dur = len(v) / SR + 2.0
    opp = ['us', 'jp', 'fr', 'gb', 'ca', 'gr', 'ru', 'in', 'ph', 'id']
    def draw(cr, t):
        g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.05, 0.08, 0.25); g.add_color_stop_rgb(1, 0.28, 0.08, 0.18); cr.set_source(g); cr.paint()
        for j in range(28):
            a = j / 28 * 2 * math.pi + t * 0.25; cr.new_path(); cr.move_to(540, 800); cr.line_to(540 + 2000 * math.cos(a), 800 + 2000 * math.sin(a)); cr.line_to(540 + 2000 * math.cos(a + 0.08), 800 + 2000 * math.sin(a + 0.08)); cr.close_path(); cr.set_source_rgba(1, 0.8, 0.2, 0.06); cr.fill()
        for j, c in enumerate(opp):
            a = -math.pi / 2 + j / len(opp) * 2 * math.pi; k = ease_out(prog(t, 0.1 + j * 0.06, 0.5 + j * 0.06))
            ball(cr, c, 540 + lerp(900, 380, k) * math.cos(a), 800 + lerp(900, 340, k) * math.sin(a), 72, 'angry', 0, -math.cos(a))
        ball(cr, 'au', 540, 800, 185 - abs(math.sin(t * 5)) * 6, 'shock' if t > 2.0 else 'angry', 0, 0)
        slam(cr, 'DID AUSTRALIA', 540, 200, 100, WHITE, t, 0.15); slam(cr, 'BEAT THE WORLD?', 540, 330, 100, S.AU_C, t, 0.55)
        for j, (lab, col) in enumerate((('W ?', S.WIN_C), ('L ?', S.LOSS_C), ('T ?', S.TIE_C))):
            tj = 1.3 + j * 0.25
            if t >= tj:
                kk = pop_k(t, tj, 0.3); cr.save(); cr.translate(230 + j * 310, 1290); cr.scale(kk, kk); rrect(cr, -125, -85, 250, 170, 28); cr.set_source_rgb(*col); cr.fill(); ptext(cr, lab, 0, 32, 96, INK, 1, sw=0, shadow=False); cr.restore()
        if t >= 2.3:
            k = pop_k(t, 2.3, 0.3); cr.save(); cr.translate(540, 1540); cr.scale(k, k); rrect(cr, -420, -70, 840, 130, 65); cr.set_source_rgb(0.9, 0.08, 0.12); cr.fill(); ptext(cr, 'WATCH FULL SEASON', 0, 22, 64, WHITE, 1, sw=0, shadow=False); cr.restore()
            for j in range(3): emoji(cr, '👇', 300 + j * 240, 1745 + 22 * abs(math.sin(t * 6 + j)), 110, 1)
        f = 1 - prog(t, 0, 0.12)
        if f > 0: cr.set_source_rgba(1, 1, 1, 0.6 * f); cr.paint()
    S.W, S.H = W, H
    S.write_wav(f'{out}/end.wav', S.sfx_track(dur, [('whoosh', 0.0), ('boom', 0.15), ('boom', 0.55), ('pop', 1.3), ('pop', 1.55), ('pop', 1.8), ('ding', 2.3)], v, 0.4))
    S.render(f'{out}/end.mp4', dur, draw, f'{out}/end.wav'); parts.append(f'{out}/end.mp4')
    open(f'{out}/parts.txt', 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{out}/parts.txt', '-c', 'copy', '-movflags', '+faststart', f'{out}/australia-vs-the-world-season-1-trailer.mp4'], check=True)
    print('done')
if __name__ == '__main__':
    main()
