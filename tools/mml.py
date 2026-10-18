#!/usr/bin/env python3
"""MML -> .sng compiler for the EU Simulator sequencer (source/audio.c).

File syntax
-----------
  # comment
  #tempo 120                      quarter notes per minute
  #instr NAME env=127,110,90,80 loop=3 rel=10 duty=2 wave=0 vib=8,4,6 sweep=-3 arp=0,4,7
        env  : volume per frame (0..127), max 32 values; loop = index to loop (sustain), default last value held
        rel  : volume decrease per frame after note-off
        duty : PSG duty 0..7 (12.5%*(n+1)); for wave tracks use wave=0..5
               (0 triangle, 1 sine, 2 saw, 3 organ, 4 soft square, 5 piano)
        vib  : delay frames, depth (1/16 semitone), speed
        sweep: pitch slide per frame (1/16 semitone, signed)
        arp  : semitone offsets cycled per frame
  #track square|noise|wave CH       starts a track (CH = hardware channel)
  then MML lines for that track.

MML
---
  c d e f g a b   notes, followed by + / # (sharp) or - (flat), optional length (1 2 4 8 16 32 + dots)
  r               rest
  oN < >          octave set / down / up   (o4 c = middle C = MIDI 60)
  lN              default length
  @NAME           instrument
  vN pN qN        volume 0..127, pan 0..127, gate percent
  KN              transpose (semitones, signed)
  tN              tempo change
  L               loop point (song loops back here at the end)
  [ ... ]N        repeat N times (nestable up to 4)
  ^LEN or &       tie: 'c4^8' or 'c4&c8' extends without retrigger
  n60,8           raw MIDI note with length
"""
import re
import struct
import sys

TPQ = 48


class Instr:
    def __init__(self, name):
        self.name = name
        self.env = [127]
        self.loop = 0xFF
        self.rel = 12
        self.duty = 2
        self.vib = (0, 0, 0)
        self.sweep = 0
        self.arp = []

    def pack(self):
        env = [max(0, min(127, int(v))) for v in self.env][:32]
        arp = (self.arp + [0] * 8)[:8]
        b = struct.pack('<BBBBBBBbB', len(env), self.loop, self.rel, self.duty,
                        self.vib[0], self.vib[1], self.vib[2], self.sweep, len(self.arp))
        b += struct.pack('<8b', *arp)
        b += bytes(env)
        return b


def length_ticks(num, dots):
    if num is None:
        return None
    t = TPQ * 4 // num
    add = t
    for _ in range(dots):
        add //= 2
        t += add
    return t


def enc_len(n):
    if 0 < n < 256:
        return bytes([n])
    return bytes([0]) + struct.pack('<H', n)


NOTE = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}


def compile_track(src, instrs, name):
    out = bytearray()
    octave = 4
    deflen = TPQ
    i = 0
    s = src
    n = len(s)
    stack = []

    def num():
        nonlocal i
        m = re.match(r'-?\d+', s[i:])
        if not m:
            return None
        i += len(m.group(0))
        return int(m.group(0))

    def dots():
        nonlocal i
        d = 0
        while i < n and s[i] == '.':
            d += 1
            i += 1
        return d

    def read_length():
        nonlocal i
        v = num()
        d = dots()
        if v is None:
            t = deflen
            add = t
            for _ in range(d):
                add //= 2
                t += add
            return t
        return length_ticks(v, d)

    def ties(total):
        nonlocal i
        # handle ^len and &note (same pitch assumed)
        while i < n:
            if s[i] == '^':
                i += 1
                total += read_length()
            elif s[i] == '&':
                j = i + 1
                while j < n and s[j] == ' ':
                    j += 1
                if j < n and s[j] in NOTE:
                    i = j + 1
                    while i < n and s[i] in '+#-':
                        i += 1
                    total += read_length()
                else:
                    break
            else:
                break
        return total

    while i < n:
        ch = s[i]
        if ch.isspace() or ch == '|':
            i += 1
            continue
        lc = ch.lower()
        if lc in NOTE and ch == lc:
            i += 1
            p = NOTE[lc]
            while i < n and s[i] in '+#-':
                p += 1 if s[i] in '+#' else -1
                i += 1
            t = ties(read_length())
            midi = (octave + 1) * 12 + p
            if not 0 <= midi < 128:
                raise SystemExit(f'{name}: note out of range at {i}')
            out += bytes([midi]) + enc_len(t)
        elif ch == 'r':
            i += 1
            t = read_length()
            while i < n and s[i] == '^':
                i += 1
                t += read_length()
            out += b'\x80' + enc_len(t)
        elif ch == 'n':
            i += 1
            midi = num()
            i += 1  # comma
            t = read_length()
            out += bytes([midi]) + enc_len(t)
        elif ch == 'o':
            i += 1
            octave = num()
        elif ch == '<':
            i += 1
            octave -= 1
        elif ch == '>':
            i += 1
            octave += 1
        elif ch == 'l':
            i += 1
            v = num()
            d = dots()
            deflen = length_ticks(v, d)
        elif ch == '@':
            i += 1
            m = re.match(r'[A-Za-z_0-9]+', s[i:])
            nm = m.group(0)
            i += len(nm)
            if nm not in instrs:
                raise SystemExit(f'{name}: unknown instrument {nm}')
            out += bytes([0x81, instrs[nm]])
        elif ch == 'v':
            i += 1
            out += bytes([0x82, max(0, min(127, num()))])
        elif ch == 'p':
            i += 1
            out += bytes([0x83, max(0, min(127, num()))])
        elif ch == 'q':
            i += 1
            out += bytes([0x8A, max(1, min(100, num()))])
        elif ch == 'K':
            i += 1
            out += bytes([0x87, num() & 0xFF])
        elif ch == 't':
            i += 1
            out += b'\x89' + struct.pack('<H', num())
        elif ch == 'L':
            i += 1
            out += b'\x84'
        elif ch == '[':
            i += 1
            stack.append(len(out))
            out += b'\x85\x00'
        elif ch == ']':
            i += 1
            cnt = num() or 2
            pos = stack.pop()
            out[pos + 1] = cnt
            out += b'\x86'
        else:
            raise SystemExit(f'{name}: unexpected {ch!r} at {i}: ...{s[max(0, i - 20):i + 20]}...')
    out += b'\xFF'
    return bytes(out)


def track_ticks(code):
    """Ticks from loop point to end (or total if no loop), expanding repeats."""
    def run(pc, end_on_loop_end=False):
        total = 0
        stack = []
        loop_at = None
        while pc < len(code):
            op = code[pc]
            pc += 1
            if op < 0x80 or op in (0x80, 0x88):
                n = code[pc]
                pc += 1
                if n == 0:
                    n = code[pc] | (code[pc + 1] << 8)
                    pc += 2
                total += n
            elif op in (0x81, 0x82, 0x83, 0x87, 0x8A):
                pc += 1
            elif op == 0x89:
                pc += 2
            elif op == 0x84:
                loop_at = total
            elif op == 0x85:
                stack.append([code[pc], pc + 1, total])
                pc += 1
            elif op == 0x86:
                top = stack[-1]
                top[0] -= 1
                if top[0] > 0:
                    pc = top[1]
                else:
                    stack.pop()
            elif op == 0xFF:
                break
        return total - (loop_at or 0)
    return run(0)


def compile_file(path):
    tempo = 120
    instrs = {}
    ilist = []
    tracks = []
    cur = None
    for raw in open(path, encoding='utf-8'):
        line = raw.split(';')[0].rstrip()
        if not line.strip():
            continue
        if line.startswith('#tempo'):
            tempo = int(line.split()[1])
        elif line.startswith('#instr'):
            parts = line.split()
            ins = Instr(parts[1])
            for kv in parts[2:]:
                k, v = kv.split('=')
                if k == 'env':
                    ins.env = [int(x) for x in v.split(',')]
                elif k == 'loop':
                    ins.loop = int(v)
                elif k == 'rel':
                    ins.rel = int(v)
                elif k in ('duty', 'wave'):
                    ins.duty = int(v)
                elif k == 'vib':
                    ins.vib = tuple(int(x) for x in v.split(','))
                elif k == 'sweep':
                    ins.sweep = int(v)
                elif k == 'arp':
                    ins.arp = [int(x) for x in v.split(',')]
            instrs[ins.name] = len(ilist)
            ilist.append(ins)
        elif line.startswith('#track'):
            parts = line.split()
            kind = {'square': 0, 'noise': 1, 'wave': 2}[parts[1]]
            cur = [kind, int(parts[2]), '']
            tracks.append(cur)
        elif line.startswith('#'):
            continue
        else:
            if cur is None:
                raise SystemExit(f'{path}: MML outside a track')
            cur[2] += ' ' + line
    # length check: total ticks after the loop point must match across tracks
    lens = []
    for t in tracks:
        lens.append(track_ticks(compile_track(t[2], instrs, path)))
    if len(set(l for l in lens if l)) > 1:
        print(f'warning: {path}: track lengths differ (ticks after loop): {lens}')
    head = b'SNG\x01' + struct.pack('<BHB', len(tracks), tempo, len(ilist))
    ib = b''.join(ins.pack() for ins in ilist)
    tdir_size = 4 * len(tracks)
    bodies = [compile_track(t[2], instrs, f'{path}:track{k}') for k, t in enumerate(tracks)]
    off = len(head) + len(ib) + tdir_size
    tdir = b''
    for t, body in zip(tracks, bodies):
        tdir += struct.pack('<BBH', t[0], t[1], off)
        off += len(body)
    return head + ib + tdir + b''.join(bodies)


if __name__ == '__main__':
    data = compile_file(sys.argv[1])
    open(sys.argv[2], 'wb').write(data)
