#!/usr/bin/env python3
"""Writes assets/music/*.mml (EU Simulator soundtrack, original chiptune arrangements).

Conventions: 4/4, 48 ticks per quarter. Track 0 lead (sq 8), 1 harmony (sq 9), 2 arpeggio/chords (sq 10),
3 bass (wave 0), 4 drums (noise 14). Every track loops at L with equal lengths (checked by mml.py).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets/music')

INSTR = """
#instr lead env=100,118,116,110,104,98,94,90 loop=7 rel=7 duty=2 vib=16,5,5
#instr lead_s env=90,104,100,94,88,84,80 loop=6 rel=6 duty=1 vib=14,4,5
#instr lead_b env=110,120,116,108,100,94 loop=5 rel=10 duty=2 vib=10,6,6
#instr pluck env=110,90,72,58,46,36,28,22,18 loop=8 rel=12 duty=1
#instr harm env=64,60,56,52,50 loop=4 rel=6 duty=1
#instr pad env=30,40,50,56,60,60 loop=5 rel=4 duty=3 vib=20,3,4
#instr arpM env=58,52,46,42 loop=3 rel=8 duty=3 arp=0,4,7
#instr arpm env=58,52,46,42 loop=3 rel=8 duty=3 arp=0,3,7
#instr arp7 env=58,52,46,42 loop=3 rel=8 duty=3 arp=0,4,10
#instr arpd env=58,52,46,42 loop=3 rel=8 duty=3 arp=0,3,6
#instr bass env=127,120,112,104 loop=3 rel=12 wave=0
#instr bassp env=127,110,90,70,56,46,40 loop=6 rel=14 wave=0
#instr organ env=80,90,90,86 loop=3 rel=6 wave=3 vib=18,3,5
#instr piano env=110,96,84,74,66,60,54,50 loop=7 rel=10 wave=5
#instr kick env=127,90,50,20,0 rel=40 duty=0
#instr snare env=110,80,50,30,15,0 rel=30
#instr hat env=44,18,0 rel=50
#instr crash env=90,80,70,60,50,40,30,20,10 rel=20
"""

DR_BASIC = "@kick o6 c @hat o8 c @snare o7 c @hat o8 c @kick o6 c @kick o6 c @snare o7 c @hat o8 c"
DR_MARCH = "@snare o7 c @snare o7 c16 c16 @snare o7 c @hat o8 c @snare o7 c @hat o8 c @snare o7 c16 c16 c"
DR_BATTLE = "@kick o6 c16 c16 @hat o8 c @snare o7 c @hat o8 c16 c16 @kick o6 c @kick o6 c @snare o7 c @hat o8 c16 c16"
DR_WALTZ = "@kick o6 c4 @hat o8 c4 @hat o8 c4 @hat o8 c4"
DR_SOFT = "@hat o8 c4 @hat o8 c4 @hat o8 c4 @hat o8 c4"


def song(name, tempo, tracks):
    body = [f'; {name} — EU Simulator (original)', f'#tempo {tempo}', INSTR]
    for kind, ch, mml in tracks:
        body.append(f'#track {kind} {ch}')
        body.append(mml.strip())
    open(os.path.join(OUT, name + '.mml'), 'w', encoding='utf-8').write('\n'.join(body) + '\n')


def drums(pattern, bars, vol=80):
    return f"v{vol} q50 l8 L [ {pattern} ]{bars}"


def chords(seq, kinds=None, octave=4, vol=56):
    """seq: list of (note, kind) per bar; plays the root 8 eighths with the arp instrument."""
    out = [f'v{vol} q80 o{octave} l8 L']
    for note, k in seq:
        out.append(f'@{k} ' + ' '.join([note] * 8) + ' |')
    return '\n'.join(out)


def bass(seq, octave=3, vol=118, inst='bass'):
    """seq: list of bar strings already in MML using o-relative notes (quarters)."""
    return f'@{inst} v{vol} q70 o{octave} l4 L\n' + '\n'.join(s + ' |' for s in seq)


def main():
    os.makedirs(OUT, exist_ok=True)

    # ---------------------------------------------------------- Bruxelles (F major, jazzy stroll)
    lead = """@lead v104 q90 o5 l8 L
a4 > c < a g4 f4 | d4 f a g2 | g4 b- > d c4 < b-4 | a4 g f e4 c4 |
f4 a > c < b-4 a4 | g4 f d f2 | d4 f b- a4 g4 | f2 r2 |
c4 f a > c4 < a4 | b-4 a g f2 | d4 g b- > d4 < b-4 | a4 g e c2 |
f4 a > c d4 c4 < | b-4 a g f2 | g4 b- > d < c4 e4 | f2. r4 |"""
    harm = """@harm v70 q85 o4 l8 L
f4 a f e4 c4 | < b-4 > d f e2 | d4 g b- a4 g4 | f4 e d c4 < g4 > |
c4 f a g4 f4 | d4 c < b- > d2 | < b-4 > d g f4 e4 | c2 r2 |
< a4 > c f a4 f4 | g4 f e d2 | < b-4 > d g b-4 g4 | f4 e c < g2 > |
c4 f a b-4 a4 | g4 f e d2 | d4 g b- a4 g4 | a2. r4 |"""
    ch = chords([('f', 'arpM'), ('d', 'arpm'), ('g', 'arpm'), ('c', 'arp7'), ('f', 'arpM'), ('d', 'arpm'), ('b-', 'arpM'), ('c', 'arp7')] * 2, octave=4)
    bs = bass(['< f > c < f > c', 'd a d a', '< g > d < g > d', 'c < g > c e', '< f > c < f > c', 'd a d a',
               '< b- > f < b- > f', 'c < g > c c'] * 2)
    song('bruxelles', 112, [('square', 8, lead), ('square', 9, harm), ('square', 10, ch), ('wave', 0, bs),
                            ('noise', 14, drums(DR_BASIC, 16, 70))])

    # ---------------------------------------------------------- Route (G major, adventurous)
    lead = """@lead_b v108 q88 o5 l8 L
b4 a g d4 g4 | e4 g b a2 | > c4 < e g > c4 < b4 | a4 g f+ d2 |
b4 > c < b a4 g4 | e4 f+ g a4 b4 | > c4 < e4 d4 f+4 | g2 r2 |
d4 g b > d4 < b4 | > c4 < b a g2 | e4 g > c e4 d4 | < b4 a g f+2 |
g4 b > d e4 d4 | c4 < b a g4 e4 | > c4 < a4 d4 f+4 | g2 r2 |"""
    harm = """@harm v68 q85 o4 l8 L
g4 f+ e < b4 > d4 | < b4 > e g f+2 | e4 c e a4 g4 | f+4 e d < a2 > |
g4 a g f+4 e4 | c4 d e f+4 g4 | a4 c4 < a4 > c4 | < b2 r2 > |
< b4 > d g b4 g4 | a4 g f+ e2 | c4 e g > c4 < b4 | g4 f+ e d2 |
d4 g b > c4 < b4 | a4 g f+ e4 c4 | a4 f+4 < a4 > c4 | < b2 r2 > |"""
    ch = chords([('g', 'arpM'), ('e', 'arpm'), ('c', 'arpM'), ('d', 'arp7'), ('g', 'arpM'), ('e', 'arpm'), ('c', 'arpM'), ('g', 'arpM'),
                 ('g', 'arpM'), ('c', 'arpM'), ('c', 'arpM'), ('d', 'arp7'), ('g', 'arpM'), ('a', 'arpm'), ('d', 'arp7'), ('g', 'arpM')], octave=4)
    bs = bass(['g d g d', 'e b e b', 'c g c g', 'd a d f+', 'g d g d', 'e b e b', 'c c d d', 'g d g g',
               'g d g d', 'c g c g', 'c g c e', 'd a d d', 'g d g d', 'a e a e', 'd a d f+', 'g d g g'], octave=2)
    song('route', 128, [('square', 8, lead), ('square', 9, harm), ('square', 10, ch), ('wave', 0, bs),
                        ('noise', 14, drums(DR_BASIC, 16, 76))])

    # ---------------------------------------------------------- Luxembourg (calm, D major, chimes)
    lead = """@pluck v100 q95 o5 l8 L
f+4 a > d c+4 < a4 | b4 a g f+2 | e4 g b a4 g4 | f+4 e d e2 |
f+4 a > d e4 d4 < | b4 > c+ d < a2 | g4 b > d c+4 e4 | d2 r2 |"""
    ch = chords([('d', 'arpM'), ('g', 'arpM'), ('e', 'arpm'), ('a', 'arp7'), ('d', 'arpM'), ('g', 'arpM'), ('e', 'arpm'), ('d', 'arpM')], octave=4, vol=50)
    bs = bass(['d a d a', 'g d g d', 'e b e b', 'a e a e', 'd a d a', 'g d g d', 'e b a c+', 'd a d d'], octave=2, inst='bassp')
    pad = """@pad v46 q100 o4 l1 L
d | d | < b > | c+ | d | d | e | f+ |"""
    song('luxembourg', 96, [('square', 8, lead), ('square', 9, pad), ('square', 10, ch), ('wave', 0, bs),
                            ('noise', 14, drums(DR_SOFT, 8, 50))])

    # ---------------------------------------------------------- Strasbourg (waltz feel in 4/4 swung, organ)
    lead = """@organ v100 q90 o5 l8 L
c4 e g > c4 < g4 | a4 g f e2 | d4 f a > d4 < a4 | g4 f e d2 |
e4 g > c e4 d4 | < b4 > c d < g2 | a4 f d < b4 > d4 | c2 r2 |"""
    ch = chords([('c', 'arpM'), ('f', 'arpM'), ('d', 'arpm'), ('g', 'arp7'), ('c', 'arpM'), ('g', 'arpM'), ('d', 'arpm'), ('c', 'arpM')], octave=4)
    bs = bass(['c g e g', 'f c a c', 'd a f a', 'g d b d', 'c g e g', 'g d b d', 'd a g b', 'c g c c'], octave=2, inst='bassp')
    song('strasbourg', 104, [('wave', 1, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_WALTZ, 8, 60))])

    # ---------------------------------------------------------- Athènes (D Phrygian dominant flavour)
    lead = """@lead_s v104 q90 o5 l8 L
d4 e- f+ g4 f+4 | e-4 d c+ d2 | a4 g f+ g4 a4 | b-4 a g f+2 |
d4 e- f+ a4 g4 | f+4 e- d c+4 d4 | e-4 f+4 g4 e-4 | d2 r2 |"""
    ch = chords([('d', 'arpM'), ('e-', 'arpM'), ('g', 'arpm'), ('d', 'arpM'), ('d', 'arpM'), ('c', 'arpm'), ('e-', 'arpM'), ('d', 'arpM')], octave=4)
    bs = bass(['d a d a', 'e- b- e- b-', 'g d g d', 'd a f+ a', 'd a d a', 'c g c g', 'e- b- e- b-', 'd a d d'], octave=2)
    song('athenes', 118, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_BASIC, 8, 66))])

    # ---------------------------------------------------------- Londres (march, Bb major, pompous)
    lead = """@lead_b v108 q80 o5 l8 L
b-4. f b-4 > d4 | c4. < a f2 | g4. b- > e-4 d4 | c4 < b- a b-2 |
> d4. c < b-4 a4 | g4 b- a g4 f4 | e-4 g4 f4 a4 | b-2 r2 |"""
    ch = chords([('b-', 'arpM'), ('f', 'arp7'), ('e-', 'arpM'), ('f', 'arp7'), ('b-', 'arpM'), ('g', 'arpm'), ('e-', 'arpM'), ('b-', 'arpM')], octave=4)
    bs = bass(['b- f b- f', 'f c f c', 'e- b- e- b-', 'f c f f', 'b- f b- f', 'g d g d', 'e- e- f f', 'b- f b- b-'], octave=2)
    song('londres', 108, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_MARCH, 8, 72))])

    # ---------------------------------------------------------- Budapest (A minor, csárdás-like)
    lead = """@lead v104 q85 o5 l8 L
a4 > c < b a g+ a b | > c4 e d c < b > c d | e4 a g f e d c | < b4 > e d c < b a g+ |
a4 > c < b a g+ a b | > c4 e d c < b > c d | e4 d c < b a g+ b | a2 r2 |"""
    ch = chords([('a', 'arpm'), ('a', 'arpm'), ('d', 'arpm'), ('e', 'arp7'), ('a', 'arpm'), ('a', 'arpm'), ('e', 'arp7'), ('a', 'arpm')], octave=4)
    bs = bass(['a e a e', 'a e a e', 'd a d a', 'e b e g+', 'a e a e', 'a e a e', 'e b e e', 'a e a a'], octave=2)
    song('budapest', 132, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_BASIC, 8, 70))])

    # ---------------------------------------------------------- Paris (musette, G major, accordion)
    lead = """@organ v100 q88 o5 l8 L
d4 g a b4 a g | f+4 a g e2 | c4 e g b4 a g | f+4 e d c2 |
d4 g a b4 > d4 < | > c4 < b a g2 | e4 f+ g a4 f+ d | g2 r2 |"""
    ch = chords([('g', 'arpM'), ('d', 'arp7'), ('c', 'arpM'), ('d', 'arp7'), ('g', 'arpM'), ('c', 'arpM'), ('d', 'arp7'), ('g', 'arpM')], octave=4)
    bs = bass(['g d b d', 'd a f+ a', 'c g e g', 'd a f+ a', 'g d b d', 'c g e g', 'd a f+ a', 'g d g g'], octave=2, inst='bassp')
    song('paris', 116, [('wave', 1, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_WALTZ, 8, 56))])

    # ---------------------------------------------------------- Cantine / home / shop (cozy C major)
    lead = """@pluck v96 q95 o5 l8 L
e g > c < g e g f d | e c d < b > c2 | f a > c < a g e f d | e4 d4 c2 |"""
    ch = chords([('c', 'arpM'), ('g', 'arp7'), ('f', 'arpM'), ('c', 'arpM')], octave=4, vol=50)
    bs = bass(['c g e g', 'g d b c', 'f c a c', 'g g c c'], octave=2, inst='bassp')
    song('cantine', 100, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_SOFT, 4, 44))])

    # ---------------------------------------------------------- Labo / intro (gentle, F major)
    lead = """@lead_s v90 q95 o5 l4 L
a g f c | d f e2 | f a > c < a | g2. r4 | b- a g f | e g f d | c e g e | f1 |"""
    ch = chords([('f', 'arpM'), ('b-', 'arpM'), ('f', 'arpM'), ('c', 'arp7'), ('b-', 'arpM'), ('c', 'arp7'), ('c', 'arp7'), ('f', 'arpM')], octave=4, vol=44)
    bs = bass(['f c f c', 'b- f b- f', 'f c f c', 'c g c g', 'b- f b- f', 'c g c g', 'c g e g', 'f c f f'], octave=2, inst='bassp')
    song('labo', 88, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs)])

    # ---------------------------------------------------------- Gym (tense, E minor)
    lead = """@lead_b v104 q75 o5 l8 L
e e b4 a g f+ e | d d a4 g f+ e d | c c g4 f+ e d c | < b b > d+4 f+4 b4 |
e e b4 a g f+ e | d d a4 g f+ e d | c c e4 g4 b4 | > c4 < b4 a4 g4 |"""
    ch = chords([('e', 'arpm'), ('d', 'arpM'), ('c', 'arpM'), ('b', 'arp7'), ('e', 'arpm'), ('d', 'arpM'), ('c', 'arpM'), ('a', 'arpm')], octave=4)
    bs = bass(['e e e e', 'd d d d', 'c c c c', '< b b b b >', 'e e e e', 'd d d d', 'c c c c', 'a a b b'], octave=2)
    song('gym', 140, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_BATTLE, 8, 74))])

    # ---------------------------------------------------------- Ghost tower / lobby (spooky, chromatic)
    lead = """@lead_s v84 q70 o5 l8 L
e4 r f e d+ e4 | r g f+ e d+2 | c4 r d+ e f+ e4 | d+2 r2 |
e4 r f e d+ e4 | r b- a g+ g2 | f4 e d+ d c+ c c | < b2 r2 > |"""
    ch = chords([('e', 'arpm'), ('e', 'arpd'), ('c', 'arpM'), ('b', 'arp7'), ('e', 'arpm'), ('e', 'arpd'), ('f', 'arpM'), ('b', 'arp7')], octave=3, vol=46)
    bs = bass(['e r e r', 'e r f r', 'c r c r', '< b r b r >', 'e r e r', 'e r f r', 'f r f r', '< b b b b >'], octave=2, inst='bassp')
    song('ghost', 84, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_SOFT, 8, 30))])

    # ---------------------------------------------------------- Council hall (solemn, organ, C minor)
    lead = """@organ v96 q95 o5 l4 L
c e- g > c < | b- a- g2 | a- > c < f a- | g2. r4 | e- g > c e- < | d c < b2 > | c e- d < b > | c1 |"""
    ch = chords([('c', 'arpm'), ('e-', 'arpM'), ('f', 'arpm'), ('g', 'arp7'), ('c', 'arpm'), ('g', 'arpM'), ('g', 'arp7'), ('c', 'arpm')], octave=4, vol=46)
    bs = bass(['c g c g', 'e- b- e- b-', 'f c f c', 'g d g d', 'c g c g', 'g d g d', 'g d g d', 'c g c c'], octave=2, inst='bassp')
    song('council_hall', 80, [('wave', 1, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_SOFT, 8, 36))])

    # ---------------------------------------------------------- Powers (comedic swagger march, F major)
    lead = """@lead_b v108 q70 o5 l8 L
f r f a > c4 < a4 | b-4 g4 e2 | f r f a > c4 d4 | c2 < a2 |
b- r b- > d f4 d4 | c4 < b-4 a4 g4 | f a g e f4 c4 | f2 r2 |"""
    ch = chords([('f', 'arpM'), ('c', 'arp7'), ('f', 'arpM'), ('f', 'arpM'), ('b-', 'arpM'), ('f', 'arpM'), ('c', 'arp7'), ('f', 'arpM')], octave=4)
    bs = bass(['f c f c', 'c g c g', 'f c f c', 'f c f a', 'b- f b- f', 'f c f c', 'c g c c', 'f c f f'], octave=2)
    song('powers_map', 120, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_MARCH, 8, 70))])

    # ---------------------------------------------------------- Battles
    lead = """@lead_b v110 q80 o5 l16 L
e8 e e b8 a8 g8 f+8 e8 d+8 | d8 d d a8 g8 f+8 e8 d8 c+8 | c8 c c g8 f+8 e8 d8 c8 < b8 > | < b8 b b > d+8 f+8 b8 a8 g8 f+8 |
e8 g8 b8 > e8 d8 < b8 g8 e8 | f+8 a8 > d8 f+8 e8 d8 < a8 f+8 | g8 b8 > d8 g8 f+8 d8 < b8 g8 | a8 > c8 < b8 a8 g8 f+8 e8 d+8 |"""
    ch = chords([('e', 'arpm'), ('d', 'arpM'), ('c', 'arpM'), ('b', 'arp7'), ('e', 'arpm'), ('d', 'arpM'), ('g', 'arpM'), ('a', 'arpm')], octave=4, vol=60)
    bs = bass(['e8 e8 e8 e8 e8 e8 e8 e8', 'd8 d8 d8 d8 d8 d8 d8 d8', 'c8 c8 c8 c8 c8 c8 c8 c8', '< b8 b8 b8 b8 b8 b8 b8 b8 >',
               'e8 e8 e8 e8 e8 e8 e8 e8', 'd8 d8 d8 d8 d8 d8 d8 d8', 'g8 g8 g8 g8 g8 g8 g8 g8', 'a8 a8 a8 a8 b8 b8 b8 b8'], octave=2)
    song('battle_wild', 150, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_BATTLE, 8, 80))])

    lead = """@lead_b v110 q78 o5 l8 L
a4 > c < a e4 a4 | g4 b g d2 | f4 a f c4 f4 | e4 g+ b > e2 < |
a4 > c e d4 c4 | < b4 > d c < b2 | a4 g f e4 d4 | e4 g+4 b4 > e4 < |
f4 a > c < b4 a4 | g4 b > d c2 < | f4 e d c4 < b4 > | e2 g+2 |
a4 > c e a4 g4 | f4 e d e2 | c4 < a4 > d4 < b4 | a2 r2 |"""
    ch = chords([('a', 'arpm'), ('g', 'arpM'), ('f', 'arpM'), ('e', 'arp7')] * 2 + [('f', 'arpM'), ('g', 'arpM'), ('d', 'arpm'), ('e', 'arp7'), ('a', 'arpm'), ('d', 'arpm'), ('f', 'arpM'), ('a', 'arpm')], octave=4, vol=60)
    bs = bass(['a8 a8 a8 a8 a8 a8 a8 a8', 'g8 g8 g8 g8 g8 g8 g8 g8', 'f8 f8 f8 f8 f8 f8 f8 f8', 'e8 e8 e8 e8 e8 e8 e8 e8'] * 2 +
              ['f8 f8 f8 f8 f8 f8 f8 f8', 'g8 g8 g8 g8 g8 g8 g8 g8', 'd8 d8 d8 d8 d8 d8 d8 d8', 'e8 e8 e8 e8 e8 e8 e8 e8',
               'a8 a8 a8 a8 a8 a8 a8 a8', 'd8 d8 d8 d8 e8 e8 e8 e8', 'f8 f8 f8 f8 e8 e8 e8 e8', 'a8 a8 a8 a8 a8 a8 a8 a8'], octave=2)
    song('battle_trainer', 156, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_BATTLE, 16, 80))])

    lead = """@lead_b v114 q80 o5 l8 L
d4 f a > d4 < a4 | b-4 a g a2 | g4 b- > d c4 < b-4 | a4 c+ e a2 |
d4 f a > d4 c4 | < b-4 > d f e2 | d4 c < b- a4 g4 | f4 e4 d4 c+4 |"""
    harm = """@harm v66 q80 o4 l8 L
f4 a > d < a4 f4 | g4 f e f2 | e4 g b- a4 g4 | e4 a > c+ < e2 |
f4 a > d < b-4 a4 | g4 b- > d c2 < | b-4 a g f4 e4 | d4 c+4 < a4 a4 > |"""
    ch = chords([('d', 'arpm'), ('b-', 'arpM'), ('g', 'arpm'), ('a', 'arp7'), ('d', 'arpm'), ('b-', 'arpM'), ('g', 'arpm'), ('a', 'arp7')], octave=4, vol=58)
    bs = bass(['d8 d8 d8 d8 d8 d8 d8 d8', 'b-8 b-8 b-8 b-8 b-8 b-8 b-8 b-8', 'g8 g8 g8 g8 g8 g8 g8 g8', 'a8 a8 a8 a8 a8 a8 a8 a8'] * 2, octave=2)
    song('battle_gym', 162, [('square', 8, lead), ('square', 9, harm), ('square', 10, ch), ('wave', 0, bs),
                             ('noise', 14, drums(DR_BATTLE, 8, 84))])

    lead = """@lead_b v116 q78 o5 l8 L
c4 e- g > c4 < b4 | a-4 g f g2 | e-4 g > c e-4 d4 | c4 < b a- g2 |
a-4 > c e- d4 c4 < | b-4 > d f e-2 | d4 c < b a-4 g4 | > c4 < g4 > c4 d4 |
e-4 d c < b4 g4 | a-4 b > c d2 | e-4 f g a-4 g4 | f4 e- d c2 |
< a-4 > c e- g4 f4 | e-4 d c < b2 > | c4 e- d < b4 g4 | > c2 r2 |"""
    ch = chords([('c', 'arpm'), ('a-', 'arpM'), ('c', 'arpm'), ('g', 'arp7'), ('a-', 'arpM'), ('b-', 'arpM'), ('g', 'arp7'), ('c', 'arpm'),
                 ('c', 'arpm'), ('f', 'arpm'), ('c', 'arpm'), ('g', 'arp7'), ('a-', 'arpM'), ('g', 'arp7'), ('g', 'arp7'), ('c', 'arpm')], octave=4, vol=60)
    bs = bass([f'{n}8 ' * 8 for n in ['c', 'a-', 'c', 'g', 'a-', 'b-', 'g', 'c', 'c', 'f', 'c', 'g', 'a-', 'g', 'g', 'c']], octave=2)
    song('battle_final', 170, [('square', 8, lead), ('square', 10, ch), ('wave', 0, bs), ('noise', 14, drums(DR_BATTLE, 16, 86))])

    # ---------------------------------------------------------- Jingles / short loops
    song('victory', 132, [
        ('square', 8, "@lead v110 q90 o5 l8 c e g > c4. < g8 | a b > c d e2 < | L c e g e d c d e | c2. r4 |"),
        ('square', 10, "@arpM v56 q80 o4 l8 c c c c c c c c | f f f f g g g g | L c c c c g g g g | c c c c c c c c |"),
        ('wave', 0, "@bass v116 q70 o3 l4 c g e g | f a g b | L c g < g > d | c g c c |"),
        ('noise', 14, "v70 q50 l8 L [ " + DR_BASIC + " ]2")])
    song('evolution', 120, [
        ('square', 8, "@lead_s v100 q90 o5 l8 L c d e g e d c < g > | c d e g a g e c | d e f a g f e d | e f g > c4 < g e d |"),
        ('square', 10, "@arpM v50 q80 o4 l8 L c c c c c c c c | a a a a a a a a | d d d d g g g g | c c c c g g g g |"),
        ('wave', 0, "@bassp v110 q70 o3 l4 L c g c g | < a > e < a > e | d a g d | c g < g > g |")])
    song('sad', 76, [
        ('square', 8, "@lead_s v90 q95 o5 l4 L e d c < b | a2 > c2 | d c < b a | g+1 > | a g f e | d2 f2 | e d c < b | a1 > |"),
        ('square', 10, "@arpm v40 q80 o4 l8 L a a a a a a a a | f f f f f f f f | d d d d d d d d | e e e e e e e e | d d d d d d d d | b- b- b- b- b- b- b- b- | e e e e e e e e | a a a a a a a a |"),
        ('wave', 0, "@bassp v100 q70 o2 l2 L a a | f f | d d | e e | d d | b- b- | e e | a a |")])
    song('minigame', 150, [
        ('square', 8, "@lead v100 q70 o5 l8 L c e g e > c < g e g | f a > c < a g b > d < b | c e g e a g e c | d f e d c2 |"),
        ('square', 10, "@arpM v52 q80 o4 l8 L c c c c c c c c | f f f f g g g g | c c c c a a a a | d d d d c c c c |"),
        ('wave', 0, "@bass v116 q70 o3 l4 L c g c g | f c g d | c g a e | d g c c |"),
        ('noise', 14, "v74 q50 l8 L [ " + DR_BATTLE + " ]4")])
    # ending: slow Ode to Joy (public domain melody)
    song('ending', 92, [
        ('square', 8, """@lead_s v100 q92 o5 l4 L
e e f g | g f e d | c c d e | e. d8 d2 | e e f g | g f e d | c c d e | d. c8 c2 |
d d e c | d e8 f8 e c | d e8 f8 e d | c d < g2 > | e e f g | g f e d | c c d e | d. c8 c2 |"""),
        ('square', 10, chords([('c', 'arpM'), ('g', 'arp7'), ('c', 'arpM'), ('g', 'arp7'), ('c', 'arpM'), ('g', 'arp7'), ('c', 'arpM'), ('c', 'arpM'),
                               ('g', 'arp7'), ('g', 'arp7'), ('g', 'arp7'), ('c', 'arpM'), ('c', 'arpM'), ('g', 'arp7'), ('c', 'arpM'), ('c', 'arpM')], octave=4, vol=40)),
        ('wave', 0, bass(['c g c g', 'g d g d', 'c g c e', 'g d g d', 'c g c g', 'g d g d', 'c g c e', 'g d c c',
                          'g d g d', 'g d g d', 'g d g d', 'c e g g', 'c g c g', 'g d g d', 'c g c e', 'g d c c'], octave=2, inst='bassp'))])

    # aliases (build step copies compiled songs)
    aliases = {'home': 'cantine', 'shop': 'cantine', 'gare': 'cantine', 'intro': 'labo', 'francfort': 'luxembourg',
               'schengen': 'route', 'lobby': 'ghost', 'rival': 'battle_trainer', 'encounter': 'battle_trainer',
               'gym_leader': 'battle_gym', 'boss': 'battle_gym', 'council': 'battle_gym', 'champion': 'battle_final',
               'powers': 'battle_final', 'final': 'battle_final', 'battle_legend': 'battle_final', 'legend': 'labo',
               'victory_wild': 'victory', 'victory_trainer': 'victory', 'champion_hall': 'council_hall',
               'sommet_hall': 'council_hall', 'trump': 'powers_map', 'putin': 'powers_map', 'xi': 'powers_map'}
    open(os.path.join(OUT, 'aliases.txt'), 'w').write('\n'.join(f'{k} {v}' for k, v in aliases.items()) + '\n')
    print('songs written')


if __name__ == '__main__':
    main()
