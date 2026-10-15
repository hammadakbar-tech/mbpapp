"""Narration for the long cut. Synthesises every line with Kokoro, lays the lines out back to back,
and writes the voice track plus timings.json; the renderer times every scene from that file.
Usage: python3 voice_long.py <kokoro.onnx> <voices.bin> <out_dir> [voice]
"""
import json, os, sys, wave
import numpy as np
from kokoro_onnx import Kokoro

SR_OUT = 48000
SPEED = 1.05
# scene key -> lines; a line is text or (pause_before_seconds, text)
SCENES = [
    ('title', ["Who really discovered America?",
               "The answer is a lot more interesting than one name."]),
    ('bering', ["Over fifteen thousand years ago, in the last Ice Age, the seas dropped so low that Asia and Alaska were joined by land.",
                "The first Americans walked across... and spread all the way to the tip of South America."]),
    ('empires', ["Over thousands of years, they built great civilizations.",
                 "The Maya. The Aztecs. The Inca. And the city of Cahokia."]),
    ('vikings', ["Around the year one thousand, Viking explorer Leif Erikson sailed west from Greenland...",
                 "and landed in a place he called Vinland, in today's Newfoundland.",
                 (0.35, "But the Norse didn't stay.")]),
    ('columbus', ["Five centuries later, in fourteen ninety-two, Christopher Columbus sailed west for Spain, hoping to reach Asia.",
                  "After ten weeks at sea, he landed in the Bahamas... and insisted he'd found the Indies."]),
    ('naming', ["But it was Amerigo Vespucci who argued this was a whole new world.",
                "In fifteen oh seven, a German mapmaker put his name on the map... America!"]),
    ('race', ["Soon, Europe's powers raced across the ocean.",
              "John Cabot, for England.",
              "Ponce de León, for Spain.",
              "And Jacques Cartier, for France."]),
    ('colonies', ["In sixteen oh seven, English settlers founded Jamestown, Virginia.",
                  "Thirteen years later, the Pilgrims landed at Plymouth."]),
    ('nation', ["And on July fourth, seventeen seventy-six, thirteen colonies declared independence...",
                "and the United States was born."]),
    ('outro', ["So, who discovered America?",
               "It wasn't discovered just once. It was discovered again, and again.",
               (0.3, "And its first peoples were there all along.")]),
]
LEAD, GAP, TAIL = 0.45, 0.28, 0.75

def synth(k, text, voice):
    audio, sr = k.create(text, voice=voice, speed=SPEED, lang='en-us')
    nz = np.nonzero(np.abs(audio) > 0.01)[0]
    audio = audio[max(nz[0] - 200, 0):nz[-1] + 1200]
    x = np.linspace(0, len(audio) - 1, int(len(audio) * SR_OUT / sr))
    return np.interp(x, np.arange(len(audio)), audio)

def main():
    model, voices, out_dir = sys.argv[1:4]
    voice = sys.argv[4] if len(sys.argv) > 4 else 'af_heart'
    k = Kokoro(model, voices)
    t, clips, scenes = 0.0, [], []
    for key, lines in SCENES:
        start, cursor, spans = t, t + LEAD, []
        for i, line in enumerate(lines):
            pause, text = line if isinstance(line, tuple) else (0.0, line)
            cursor += pause + (GAP if i else 0)
            a = synth(k, text, voice)
            clips.append((cursor, a))
            spans.append([round(cursor, 3), round(cursor + len(a) / SR_OUT, 3), text])
            cursor += len(a) / SR_OUT
        t = cursor + (TAIL if key != 'outro' else 1.6)
        scenes.append({'key': key, 'start': round(start, 3), 'end': round(t, 3), 'lines': spans})
        print(f'{key:9s} {start:6.2f} -> {t:6.2f}')
    total = t
    track = np.zeros(int(SR_OUT * total) + 1)
    for s, a in clips:
        i0 = int(s * SR_OUT); track[i0:i0 + len(a)] += a[:len(track) - i0]
    track = track / max(1e-6, np.abs(track).max()) * 0.95
    with wave.open(os.path.join(out_dir, 'voice_long.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR_OUT)
        w.writeframes((track * 32767).astype('<i2').tobytes())
    json.dump({'duration': round(total, 3), 'scenes': scenes},
              open(os.path.join(out_dir, 'timings.json'), 'w'), indent=1)
    print('total', round(total, 2))

if __name__ == '__main__':
    main()
