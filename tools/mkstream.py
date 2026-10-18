#!/usr/bin/env python3
"""Streamed music: assets/music_ogg/<name>.ogg -> nitrofs/music/<name>.ads (signed 8-bit PCM, mono, 22050 Hz).

The DS plays these through one hardware channel fed from a PCM16 ring buffer that the ARM9 refills every
frame (source/stream.c). Format:
    'ADS1', u32 sample_rate, u32 sample_count, u32 flags (bit 0: loop, bit 1: PCM8), then the samples.
(IMA-ADPCM, flags bit 1 clear, is still understood by the player, but chiptune square waves only reach
~17 dB SNR with it, so the tracks ship as dithered 8-bit PCM, ~45 dB.)
Loudness is normalised with ffmpeg so every track sits at the same level. Outputs are cached: a track is
re-encoded only when its .ogg is newer.
"""
import glob
import multiprocessing
import os
import random
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'music_ogg')
OUT = os.path.join(ROOT, 'nitrofs', 'music')
RATE = 22050
ONE_SHOT = {'evolution'}   # everything else loops

STEPS = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80,
         88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598,
         658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327,
         3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289,
         16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767]
IDX = [-1, -1, -1, -1, 2, 4, 6, 8]


def encode(pcm):
    pred, index = 0, 0
    out = bytearray((len(pcm) + 1) // 2)
    steps, idx = STEPS, IDX
    for i, s in enumerate(pcm):
        step = steps[index]
        diff = s - pred
        code = 0
        if diff < 0:
            code = 8
            diff = -diff
        # same arithmetic as the decoder, so encoder and decoder never drift apart
        dq = step >> 3
        if diff >= step:
            code |= 4
            diff -= step
            dq += step
        step >>= 1
        if diff >= step:
            code |= 2
            diff -= step
            dq += step
        step >>= 1
        if diff >= step:
            code |= 1
            dq += step
        pred = pred - dq if code & 8 else pred + dq
        if pred > 32767:
            pred = 32767
        elif pred < -32768:
            pred = -32768
        index += idx[code & 7]
        if index < 0:
            index = 0
        elif index > 88:
            index = 88
        if i & 1:
            out[i >> 1] |= code << 4
        else:
            out[i >> 1] = code
    return out


def convert(path):
    name = os.path.basename(path)[:-4]
    dst = os.path.join(OUT, name + '.ads')
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(path):
        return name, False
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11',
                          '-ac', '1', '-ar', str(RATE), '-f', 's16le', '-'], capture_output=True, check=True).stdout
    n = len(raw) // 2
    pcm = struct.unpack('<%dh' % n, raw[:n * 2])
    rnd = random.Random(name)
    data = bytearray(n)
    for i, v in enumerate(pcm):
        q = (v + (rnd.random() - rnd.random()) * 256) / 256.0   # TPDF dither
        q = int(round(q))
        data[i] = (max(-128, min(127, q))) & 0xFF
    flags = (0 if name in ONE_SHOT else 1) | 2
    open(dst, 'wb').write(b'ADS1' + struct.pack('<III', RATE, n, flags) + bytes(data))
    return name, True


def main():
    os.makedirs(OUT, exist_ok=True)
    srcs = sorted(glob.glob(os.path.join(SRC, '*.ogg')))
    with multiprocessing.Pool() as pool:
        res = pool.map(convert, srcs)
    done = [n for n, d in res if d]
    print(f'stream {len(srcs)} tracks' + (f', encoded {len(done)}' if done else ''))


if __name__ == '__main__':
    sys.exit(main())
