"""Narration for the video: Kokoro TTS, one line per scene, each sped up just enough to fit its slot.
Usage: python3 voice.py <kokoro.onnx> <voices.bin> <out.wav> [voice]
"""
import sys, wave
import numpy as np
from kokoro_onnx import Kokoro

SR_OUT, DUR = 48000, 30.0
LINES = [  # start, latest end, text
    (0.25, 3.3, "Who really discovered America?"),
    (3.6, 9.2, "Fifteen thousand years ago, the first people walked over from Asia... and spread across two continents."),
    (9.5, 14.7, "Around the year one thousand, Viking Leif Erikson landed in Newfoundland."),
    (14.95, 20.4, "In fourteen ninety-two, Columbus sailed for Spain... and was sure he'd found Asia!"),
    (20.65, 24.9, "A mapmaker named the land America, after Amerigo Vespucci."),
    (25.05, 27.95, "By seventeen seventy-six, a new nation was born."),
    (28.05, 29.9, "Discovered? Again, and again."),
]

def main():
    model, voices, out = sys.argv[1:4]
    voice = sys.argv[4] if len(sys.argv) > 4 else 'af_heart'
    k = Kokoro(model, voices)
    track = np.zeros(int(SR_OUT * DUR))
    for start, end, text in LINES:
        speed = 1.05
        while True:
            audio, sr = k.create(text, voice=voice, speed=speed, lang='en-us')
            nz = np.nonzero(np.abs(audio) > 0.01)[0]
            audio = audio[max(nz[0] - 200, 0):nz[-1] + 1200]
            length = len(audio) / sr
            if length <= end - start or speed >= 1.5:
                break
            speed = round(speed * min(1.25, length / (end - start)) + 0.02, 3)
        # resample to 48 kHz
        x = np.linspace(0, len(audio) - 1, int(len(audio) * SR_OUT / sr))
        audio = np.interp(x, np.arange(len(audio)), audio)
        i0 = int(start * SR_OUT)
        track[i0:i0 + len(audio)] += audio[:len(track) - i0]
        print(f'{start:5.2f}-{start + length:5.2f} (slot {end:5.2f}) speed {speed}: {text}')
    track = track / max(1e-6, np.abs(track).max()) * 0.95
    with wave.open(out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR_OUT)
        w.writeframes((track * 32767).astype('<i2').tobytes())

if __name__ == '__main__':
    main()
