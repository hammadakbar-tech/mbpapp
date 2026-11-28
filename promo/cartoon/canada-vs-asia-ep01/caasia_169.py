# 16:9 long-form layout for "Canada vs Asia, Episode 01": the 9:16 episode plays full-height in the centre over a
# blurred copy; left panel shows the current match, right panel the Europe-tour board (results revealed as they happen).
# Usage: python3 pheu169.py <data_dir> <episode_9x16.mp4> <out_dir>
import os, sys, subprocess, cairo
import caasia as P
import china as C
from china import ptext, rrect, fit, chip, GOLD, WHITE, INK
from warballs import ball
W, H = 1920, 1080
WIN_C, LOSS_C = (0.18, 0.75, 0.42), (0.94, 0.26, 0.35)
def overlay(path, m):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(s)
    rrect(cr, 40, 70, 576, 940, 30); cr.set_source_rgba(0.02, 0.03, 0.08, 0.84); cr.fill()
    ptext(cr, 'GEOBALL WARS', 328, 135, 34, GOLD, 1, fam='Poppins ExtraBold', sw=0, shadow=False)
    ptext(cr, 'CANADA vs ASIA', 328, 195, 44, P.PH_C, 1, sw=0, shadow=False); ptext(cr, 'EPISODE 01', 328, 245, 34, WHITE, 0.85, fam='Poppins ExtraBold', sw=0, shadow=False)
    if m == 0:
        ball(cr, 'Canada', 328, 470, 130, 'angry', 0, 0); ptext(cr, '10 COUNTRIES', 328, 680, 56, WHITE, 1, sw=8); ptext(cr, '5 ROUNDS EACH', 328, 745, 40, GOLD, 1, fam='Poppins ExtraBold', sw=6)
    else:
        op = P.OPP[m]; ball(cr, 'Canada', 200, 450, 105, 'angry', 0, 0.6); ball(cr, op, 456, 450, 105, 'angry', 0, -0.6)
        cr.new_path(); cr.arc(328, 450, 42, 0, 6.283); cr.set_source_rgb(*GOLD[:3]); cr.fill(); ptext(cr, 'VS', 328, 467, 44, INK, 1, sw=0, shadow=False)
        ptext(cr, f'MATCH {m} OF {P.NM}', 328, 640, 40, GOLD, 1, fam='Poppins ExtraBold', sw=6)
        lab = f"vs {'THE ' if op in ('UK', 'Netherlands') else ''}{op.upper()}"; ptext(cr, lab, 328, 720, fit(cr, lab, 64, 520), WHITE, 1, sw=8)
        ptext(cr, 'BEST OF 5 ROUNDS', 328, 785, 30, WHITE, 0.7, fam='Poppins ExtraBold', sw=5)
    rrect(cr, 88, 880, 480, 84, 42); cr.set_source_rgb(0.9, 0.08, 0.12); cr.fill(); ptext(cr, 'SUBSCRIBE FOR EP 02', 328, 935, 36, WHITE, 1, sw=0, shadow=False)
    x, y = 1304, 70; done = [k for k in range(1, m)] if m else []
    rrect(cr, x, y, 580, 940, 30); cr.set_source_rgba(0.02, 0.03, 0.08, 0.84); cr.fill()
    ptext(cr, 'ASIA TOUR', x + 290, y + 62, 44, GOLD, 1, sw=0, shadow=False)
    wn = sum(1 for k in done if P.MRES[k][0] == 'Canada'); ln = len(done) - wn
    ptext(cr, f'{wn}', x + 190, y + 150, 72, WIN_C, 1, sw=0, shadow=False); ptext(cr, 'W', x + 190, y + 190, 28, WHITE, 0.8, fam='Poppins ExtraBold', sw=0, shadow=False)
    ptext(cr, f'{ln}', x + 390, y + 150, 72, LOSS_C, 1, sw=0, shadow=False); ptext(cr, 'L', x + 390, y + 190, 28, WHITE, 0.8, fam='Poppins ExtraBold', sw=0, shadow=False)
    for i in range(1, P.NM + 1):
        yy = y + 250 + (i - 1) * 66; op = P.OPP[i]; cur = (i == m)
        if cur: rrect(cr, x + 14, yy - 30, 552, 58, 16); cr.set_source_rgba(*P.PH_C, 0.3); cr.fill()
        ball(cr, op, x + 60, yy, 22, 'happy', 0, 0)
        ptext(cr, ('vs ' + op).upper(), x + 100, yy + 10, 30, WHITE if (i in done or cur) else (0.55, 0.57, 0.65), 1, fam='Poppins ExtraBold', sw=0, shadow=False, anchor='l')
        if i in done:
            win = P.MRES[i][0] == 'Canada'; pw, ow = P.MRES[i][1], P.MRES[i][2]
            rrect(cr, x + 400, yy - 22, 150, 42, 21); cr.set_source_rgb(*(WIN_C if win else LOSS_C)); cr.fill(); ptext(cr, f"{'W' if win else 'L'} {pw}–{ow}", x + 475, yy + 10, 26, INK, 1, sw=0, shadow=False)
        elif cur: cr.new_path(); cr.arc(x + 430, yy, 8, 0, 6.283); cr.set_source_rgb(*LOSS_C); cr.fill(); ptext(cr, 'NOW', x + 490, yy + 10, 26, GOLD, 1, fam='Poppins ExtraBold', sw=0, shadow=False)
        else: ptext(cr, '?', x + 475, yy + 10, 28, (0.55, 0.57, 0.65), 1, sw=0, shadow=False)
    s.write_to_png(path)
def main():
    data, src, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
    P.setup(data, os.path.join(os.path.dirname(os.path.abspath(src)), 'voice_cache', 'edge_caasia'))
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
    cuts = [0.0] + [P.bt(f'm{m}c')['start'] for m in range(1, P.NM + 1)] + [dur]
    fc = ('[0:v]split[a][b];[a]scale=480:-2,crop=480:270,boxblur=12:2,eq=brightness=-0.22:saturation=1.2,scale=1920:1080[bg];'
          '[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0[v1];[v1][1:v]overlay=0:0,format=yuv420p[v]')
    segs = []
    for m in range(0, P.NM + 1):
        ov = f'{out}/ov{m:02d}.png'; overlay(ov, m); seg = f'{out}/seg{m:02d}.mp4'; a, b = cuts[m], cuts[m + 1]
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', src, '-loop', '1', '-i', ov, '-filter_complex', fc, '-map', '[v]', '-map', '0:a', '-shortest',
                        '-r', '30', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', seg], check=True)
        segs.append(seg); print('segment', m, 'done', flush=True)
    open(f'{out}/segs.txt', 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in segs))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{out}/segs.txt', '-c', 'copy', '-movflags', '+faststart', f'{out}/canada-vs-asia-ep01.mp4'], check=True)
    with open(f'{out}/chapters.txt', 'w') as f:
        f.write('0:00 Canada vs Asia!\n')
        for m in range(1, P.NM + 1):
            t = cuts[m]; op = P.OPP[m]; f.write(f"{int(t // 60)}:{int(t % 60):02d} Match {m}: vs {'the ' if op in ('UK', 'Netherlands') else ''}{op}\n")
        t = P.bt('cta')['start']; f.write(f'{int(t // 60)}:{int(t % 60):02d} Final record\n')
    print(open(f'{out}/chapters.txt').read())
if __name__ == '__main__':
    main()
