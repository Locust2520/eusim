#!/usr/bin/env python3
"""Export the game's MML compositions as standalone MIDI files (no dependencies).

Uses the game compiler for note lengths, ties and repeats. Exports one pass through
each song, marking loop points. General MIDI sounds approximate the DS instruments;
envelopes, vibrato and pitch sweeps are not reproduced. Arpeggios use rapid notes.
"""
from pathlib import Path
import re
import struct

import mml

ROOT = Path(__file__).resolve().parent.parent
SCALE = 10
PPQ = mml.TPQ * SCALE


def vlq(value):
    result = [value & 127]
    value >>= 7
    while value:
        result.insert(0, (value & 127) | 128)
        value >>= 7
    return bytes(result)


def meta(kind, payload):
    return bytes([255, kind]) + vlq(len(payload)) + payload


def chunk(events, end):
    data = bytearray()
    previous = 0
    for tick, _, message in sorted(events, key=lambda e: (e[0], e[1])):
        data += vlq(tick - previous) + message
        previous = tick
    data += vlq(max(end, previous) - previous) + b'\xff\x2f\x00'
    return b'MTrk' + struct.pack('>I', len(data)) + data


def program(name, kind):
    if name.startswith('bass'):
        return 38  # synth bass
    return {'organ': 16, 'piano': 0, 'pluck': 24, 'pad': 89,
            'harm': 80}.get(name, 80 if kind == 0 else 81)


def export(source, destination):
    data = mml.compile_file(source)
    count, bpm, instrument_count = struct.unpack_from('<BHB', data, 4)
    names = re.findall(r'^#instr\s+(\S+)', source.read_text(), re.MULTILINE)
    instruments = []
    pos = 8
    for name in names[:instrument_count]:
        envlen, arplen = data[pos], data[pos + 8]
        arp = struct.unpack_from('<8b', data, pos + 9)[:arplen]
        instruments.append((name, arp))
        pos += 17 + envlen
    tempos = {(0, bpm)}
    tracks = []
    end = 0
    for index in range(count):
        kind, hardware, pc = struct.unpack_from('<BBH', data, pos + index * 4)
        channel = 9 if kind == 1 else index if index < 9 else index + 1
        events = [(0, -2, meta(3, f'{source.stem}: {("square", "noise", "wave")[kind]} {hardware}'.encode()))]
        events += [(0, -1, bytes([0xB0 | channel, 7, 100])),
                   (0, -1, bytes([0xB0 | channel, 10, 64])),
                   (0, -1, bytes([0xC0 | channel, program('', kind)]))]
        tick, instrument, gate, transpose, tempo = 0, 0, 90, 0, bpm
        repeats = []

        def read_length():
            nonlocal pc
            length = data[pc]
            pc += 1
            if length == 0:
                length = struct.unpack_from('<H', data, pc)[0]
                pc += 2
            return length * SCALE

        while True:
            op = data[pc]
            pc += 1
            if op <= 0x80:
                length = read_length()
                if op < 0x80:
                    name, arp = instruments[instrument]
                    sounding = max(SCALE, length * gate // 100)
                    sounding = min(length, sounding)
                    pitch = op + transpose
                    if kind == 1:
                        pitch = {'kick': 36, 'snare': 38, 'hat': 42, 'crash': 49}.get(name, 42)
                        arp = ()
                    step = max(1, round(PPQ * tempo / (60 * 59.8261))) if arp else sounding
                    for offset in range(0, sounding, step):
                        note = max(0, min(127, pitch + (arp[(offset // step) % len(arp)] if arp else 0)))
                        events.append((tick + offset, 1, bytes([0x90 | channel, note, 100])))
                        events.append((tick + min(offset + step, sounding), 0, bytes([0x80 | channel, note, 0])))
                tick += length
            elif op == 0x81:
                instrument = data[pc]
                pc += 1
                if kind != 1:
                    events.append((tick, -1, bytes([0xC0 | channel, program(instruments[instrument][0], kind)])))
            elif op in (0x82, 0x83):
                events.append((tick, -1, bytes([0xB0 | channel, 7 if op == 0x82 else 10, data[pc]])))
                pc += 1
            elif op == 0x84:
                events.append((tick, -1, meta(6, b'loopStart')))
            elif op == 0x85:
                repeats.append([data[pc], pc + 1])
                pc += 1
            elif op == 0x86:
                repeats[-1][0] -= 1
                if repeats[-1][0]:
                    pc = repeats[-1][1]
                else:
                    repeats.pop()
            elif op == 0x87:
                transpose = struct.unpack_from('b', data, pc)[0]
                pc += 1
            elif op == 0x89:
                tempo = struct.unpack_from('<H', data, pc)[0]
                pc += 2
                tempos.add((tick, tempo))
            elif op == 0x8A:
                gate = data[pc]
                pc += 1
            elif op == 0xFF:
                break
            else:
                raise ValueError(f'{source}: unsupported opcode {op:#x}')
        tracks.append(chunk(events, tick))
        end = max(end, tick)
    conductor = [(0, -1, meta(3, source.stem.encode()))]
    conductor += [(tick, 0, meta(0x51, round(60_000_000 / tempo).to_bytes(3, 'big')))
                  for tick, tempo in sorted(tempos)]
    destination.write_bytes(b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks) + 1, PPQ)
                            + chunk(conductor, end) + b''.join(tracks))


def main():
    output = ROOT / 'midi'
    output.mkdir(exist_ok=True)
    sources = sorted((ROOT / 'assets/music').glob('*.mml'))
    for source in sources:
        export(source, output / (source.stem + '.mid'))
    print(f'Exported {len(sources)} MIDI files to {output}')


if __name__ == '__main__':
    main()
