#!/usr/bin/env python3
"""Event script compiler: assets/scripts/*.evs -> nitrofs/scripts.bin, build/script_ids.json,
build/flag_ids.json, include/gen/flags.h

Syntax: one command per line, '#' or ';' comments. Strings in double quotes; adjacent strings
on the following lines starting with '"' are concatenated with a space. Labels: ':name'.

  script NAME ... end
  say WHO "text"          WHO = '-' for narration, or a speaker name (quoted if spaces)
  ask WHO "text"          like say but leaves the box open (use before choice/yesno)
  close
  show L|R CHAR [EXPR]    portrait
  expr L|R EXPR
  hide L|R|all
  focus L|R|none
  shake L|R [frames]
  choice "a" "b" ... -> VAR
  yesno -> VAR            (VAR = 1 yes / 0 no)
  goto LABEL
  if flag F goto L | if !flag F goto L
  if var V == N goto L     (== != < >=)
  if badge N goto L | if money >= N goto L | if item ITEM [N] goto L | if gender N goto L
  if party >= N goto L
  setflag F | clearflag F
  setvar V N | addvar V N
  givemon SPECIES LEVEL
  giveitem ITEM [N] | takeitem ITEM [N]
  money N            (signed)
  heal
  battle TRAINER [nolose]      result in var RESULT (1 win, 0 lose)
  wild SPECIES LEVEL
  music NAME | music stop | fanfare NAME
  sfx NAME
  wait N
  fade out|in|outwhite|inwhite [frames]
  screenshake N
  warp MAP X Y [DIR]
  move ACTOR "U2 L R3" [nowait]   ACTOR = player | npc name
  face ACTOR down|up|left|right|player|toplayer
  emote ACTOR excl|question|dots|heart|anger|sweat|note|idea [frames]
  hidenpc NAME | shownpc NAME
  spawn NAME SPRITE X Y DIR | despawn NAME
  lock | release
  minigame NAME           result in RESULT
  badge N | chapter N | loading N
  call SCRIPT
  special NAME [ARG]
  strvar N "text"
  notice "text"
  random N -> VAR
"""
import glob
import json
import os
import re
import shlex
import struct
import sys
from map_ids import ordered_map_sources

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MOTIONS = ['still', 'zoom_in', 'zoom_out', 'pan_right', 'pan_left', 'tilt_up', 'tilt_down']
TRANSITIONS = ['fade', 'cut', 'flash', 'iris', 'wipe']
OPS = {name: i for i, name in enumerate([
    'END', 'SAY', 'ASK', 'CLOSE', 'SHOW', 'EXPR', 'HIDE', 'FOCUS', 'CHOICE', 'GOTO',
    'IF_FLAG', 'IF_VAR', 'SETFLAG', 'SETVAR', 'ADDVAR', 'GIVEMON', 'GIVEITEM', 'TAKEITEM', 'MONEY', 'HEAL',
    'BATTLE', 'WILD', 'MUSIC', 'SFX', 'WAIT', 'FADE', 'SCREENSHAKE', 'WARP', 'MOVE', 'FACE',
    'EMOTE', 'NPCVIS', 'LOCK', 'RELEASE', 'MINIGAME', 'BADGE', 'CHAPTER', 'LOADING', 'IF_MONEY', 'IF_ITEM',
    'CALL', 'SPECIAL', 'STRVAR', 'FANFARE', 'SHAKE', 'IF_BADGE', 'NOTICE', 'RANDOM', 'IF_GENDER', 'SPAWN',
    'DESPAWN', 'IF_PARTY', 'YESNO', 'CINE', 'SLIDE', 'CARD',
])}
VARS_FIXED = ['RESULT', 'TMP', 'TMP2', 'STARTER', 'RIVAL_STARTER']
EMOTES = {'excl': 1, 'question': 2, 'dots': 3, 'heart': 4, 'anger': 5, 'sweat': 6, 'note': 7, 'idea': 8}
DIRS = {'down': 0, 'up': 1, 'left': 2, 'right': 3, 'toplayer': 4, 'player': 5, 'keep': 255}
SFX = ['BLIP', 'SELECT', 'CANCEL', 'CURSOR', 'BUMP', 'DOOR', 'STAMP', 'HIT', 'HIT_SUPER', 'HIT_WEAK', 'FAINT',
       'HEAL', 'LEVELUP', 'CAPTURE_SHAKE', 'CAPTURE_OK', 'THROW', 'SMS', 'GAVEL', 'VOTE', 'PAPER', 'COIN', 'ERROR',
       'STAR', 'EXP', 'SAVE', 'TRAIN', 'JUMP', 'ALARM', 'WHOOSH', 'STATUP', 'STATDOWN']
MINIGAMES = ['vote', 'tampon', 'cookies', 'sommet', 'trilogue', 'langues', 'bouchon', 'signature', 'malles',
             'courriels', 'desinfox', 'taux', 'usbc']
ENGINE_TRAIN = ['bruxelles', 'luxembourg', 'francfort', 'strasbourg', 'athenes', 'londres', 'budapest', 'paris',
                'anvers', 'varsovie', 'rome', 'maastricht', 'lisbonne']
SPECIALS = ['shop', 'pc', 'dex_rating', 'credits', 'name_rival', 'save', 'heal_anim', 'map_popup', 'sources',
            'set_heal_point', 'badge_case', 'ending', 'starter_choice', 'clock_check', 'move_tutor', 'game_corner',
            'title_return', 'unlock_postgame', 'greenland', 'gas_cut', 'rare_earth', 'restore_world', 'train',
            'jukebox']


def name_hash(s):
    h = 5381
    for ch in s.encode():
        h = (h * 33 + ch) & 0xFFFF
    return h


def load_ids(name):
    p = os.path.join(ROOT, 'build', name + '_ids.json')
    if not os.path.exists(p):
        return {}
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def tokenize(line):
    lex = shlex.shlex(line, posix=True)
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)


class Compiler:
    def __init__(self):
        self.flags = {}
        self.vars = {v: i for i, v in enumerate(VARS_FIXED)}
        self.strings = {}
        self.strlist = []
        self.scripts = {}   # name -> bytes
        self.order = []
        self.maps = {os.path.basename(p)[:-4]: i for i, p in enumerate(ordered_map_sources(ROOT))}
        self.species = load_ids('species')
        self.items = load_ids('item')
        self.trainers = load_ids('trainer')
        self.sprites = load_ids('sprite')
        self.errors = []
        # flags used by the engine
        for i in range(8):
            self.flag(f'BADGE_{i + 1}')
        for c in ENGINE_TRAIN:
            self.flag('TRAIN_' + c.upper())
        for f in ('GOT_STARTER', 'GAME_CLEARED', 'POSTGAME', 'BREXIT_DONE', 'OLAF_BADGE'):
            self.flag(f)

    def flag(self, name):
        if name not in self.flags:
            self.flags[name] = len(self.flags)
            if len(self.flags) > 2000:
                raise SystemExit('too many flags')
        return self.flags[name]

    def var(self, name):
        if name not in self.vars:
            self.vars[name] = len(self.vars)
            if len(self.vars) > 60:   # vars 60..63 hold the jukebox "heard" bits (source/audio.c)
                raise SystemExit('too many vars')
        return self.vars[name]

    def s(self, text):
        if text not in self.strings:
            self.strings[text] = len(self.strlist)
            self.strlist.append(text)
        return self.strings[text]

    def compile_all(self, files):
        blocks = []
        for f in files:
            lines = open(f, encoding='utf-8').read().split('\n')
            # join continuation strings
            merged = []
            for ln, raw in enumerate(lines, 1):
                t = raw.strip()
                if not t or t.startswith('#') or t.startswith(';'):
                    continue
                if t.startswith('"') and merged:
                    prev_ln, prev = merged[-1]
                    # append inside the last quoted string
                    if prev.rstrip().endswith('"'):
                        prev = prev.rstrip()[:-1] + ' ' + t[1:]
                        merged[-1] = (prev_ln, prev)
                        continue
                merged.append((ln, t))
            cur = None
            for ln, t in merged:
                if t.startswith('script '):
                    cur = (t.split()[1], f, [])
                    blocks.append(cur)
                elif t == 'end' and cur:
                    cur = None
                elif cur:
                    cur[2].append((ln, t))
                else:
                    self.errors.append(f'{f}:{ln}: command outside script')
        # assign ids first (for call / forward refs)
        for name, f, _ in blocks:
            if name in self.scripts:
                self.errors.append(f'duplicate script {name}')
            self.scripts[name] = None
            self.order.append(name)
        self.ids = {n: i for i, n in enumerate(self.order)}
        for name, f, body in blocks:
            self.scripts[name] = self.compile_script(name, f, body)

    def compile_script(self, name, f, body):
        code = bytearray()
        labels = {}
        fixups = []

        def u8(v):
            code.append(v & 0xFF)

        def u16(v):
            code.extend(struct.pack('<H', v & 0xFFFF))

        def s32(v):
            code.extend(struct.pack('<i', v))

        def lab(l):
            fixups.append((len(code), l))
            u16(0)

        def side(x):
            return {'L': 0, 'R': 1, 'all': 2, 'none': 255}[x]

        def actor(x):
            return 0 if x == 'player' else name_hash(x)

        def lookup(table, key, what):
            if key not in table:
                raise ValueError(f'unknown {what} {key}')
            return table[key]

        for ln, t in body:
            try:
                if t.startswith(':'):
                    labels[t[1:]] = len(code)
                    continue
                a = tokenize(t)
                c = a[0]
                if c in ('say', 'ask'):
                    u8(OPS['SAY' if c == 'say' else 'ASK'])
                    who = '' if a[1] == '-' else a[1]
                    u16(self.s(who))
                    u16(self.s(a[2]))
                elif c == 'close':
                    u8(OPS['CLOSE'])
                elif c == 'cine':
                    if a[1] == 'end':
                        u8(OPS['CINE']); u8(1); u16(self.s(''))
                    else:
                        u8(OPS['CINE']); u8(0); u16(self.s(a[1]))
                elif c == 'slide':
                    mot = a[2] if len(a) > 2 else 'still'
                    tr = a[3] if len(a) > 3 else 'fade'
                    u8(OPS['SLIDE']); u16(self.s(a[1])); u8(MOTIONS.index(mot)); u8(TRANSITIONS.index(tr))
                elif c == 'card':
                    u8(OPS['CARD']); u16(self.s(a[1])); u16(self.s(a[2] if len(a) > 2 else ''))
                elif c == 'show':
                    u8(OPS['SHOW']); u8(side(a[1])); u16(self.s(a[2])); u16(self.s(a[3] if len(a) > 3 else 'neutral'))
                elif c == 'expr':
                    u8(OPS['EXPR']); u8(side(a[1])); u16(self.s(a[2]))
                elif c == 'hide':
                    u8(OPS['HIDE']); u8(side(a[1]))
                elif c == 'focus':
                    u8(OPS['FOCUS']); u8(side(a[1]))
                elif c == 'shake':
                    u8(OPS['SHAKE']); u8(side(a[1])); u8(int(a[2]) if len(a) > 2 else 16)
                elif c == 'choice':
                    opts = a[1:a.index('->')]
                    u8(OPS['CHOICE']); u8(len(opts))
                    for o in opts:
                        u16(self.s(o))
                    u8(self.var(a[-1]))
                elif c == 'yesno':
                    u8(OPS['YESNO']); u8(self.var(a[-1]))
                elif c == 'goto':
                    u8(OPS['GOTO']); lab(a[1])
                elif c == 'if':
                    kind = a[1]
                    if kind in ('flag', '!flag'):
                        u8(OPS['IF_FLAG']); u16(self.flag(a[2])); u8(0 if kind == '!flag' else 1); lab(a[4])
                    elif kind == 'var':
                        op = {'==': 0, '!=': 1, '<': 2, '>=': 3}[a[3]]
                        u8(OPS['IF_VAR']); u8(self.var(a[2])); u8(op); u16(int(a[4])); lab(a[6])
                    elif kind == 'badge':
                        u8(OPS['IF_BADGE']); u8(int(a[2])); lab(a[4])
                    elif kind == 'money':
                        u8(OPS['IF_MONEY']); s32(int(a[3])); lab(a[5])
                    elif kind == 'item':
                        cnt = int(a[3]) if a[3] != 'goto' else 1
                        u8(OPS['IF_ITEM']); u16(lookup(self.items, a[2], 'item')); u8(cnt); lab(a[-1])
                    elif kind == 'gender':
                        u8(OPS['IF_GENDER']); u8(int(a[2])); lab(a[4])
                    elif kind == 'party':
                        u8(OPS['IF_PARTY']); u8(int(a[3])); lab(a[5])
                    else:
                        raise ValueError('bad if')
                elif c in ('setflag', 'clearflag'):
                    u8(OPS['SETFLAG']); u16(self.flag(a[1])); u8(1 if c == 'setflag' else 0)
                elif c == 'setvar':
                    u8(OPS['SETVAR']); u8(self.var(a[1])); u16(int(a[2]))
                elif c == 'addvar':
                    u8(OPS['ADDVAR']); u8(self.var(a[1])); u16(int(a[2]))
                elif c == 'givemon':
                    sp = a[1]
                    if sp.startswith('$'):
                        u8(OPS['GIVEMON']); u16(0x8000 | self.var(sp[1:])); u8(int(a[2]))
                    else:
                        u8(OPS['GIVEMON']); u16(lookup(self.species, sp, 'species')); u8(int(a[2]))
                elif c in ('giveitem', 'takeitem'):
                    u8(OPS['GIVEITEM' if c == 'giveitem' else 'TAKEITEM'])
                    u16(lookup(self.items, a[1], 'item')); u8(int(a[2]) if len(a) > 2 else 1)
                elif c == 'money':
                    u8(OPS['MONEY']); s32(int(a[1]))
                elif c == 'heal':
                    u8(OPS['HEAL'])
                elif c == 'battle':
                    u8(OPS['BATTLE']); u16(lookup(self.trainers, a[1], 'trainer')); u8(1 if 'nolose' in a else 0)
                elif c == 'wild':
                    u8(OPS['WILD']); u16(lookup(self.species, a[1], 'species')); u8(int(a[2]))
                elif c == 'music':
                    u8(OPS['MUSIC']); u16(self.s('' if a[1] == 'stop' else a[1]))
                elif c == 'fanfare':
                    u8(OPS['FANFARE']); u16(self.s(a[1]))
                elif c == 'sfx':
                    u8(OPS['SFX']); u8(SFX.index(a[1].upper()))
                elif c == 'wait':
                    u8(OPS['WAIT']); u16(int(a[1]))
                elif c == 'fade':
                    m = {'out': 0, 'in': 1, 'outwhite': 2, 'inwhite': 3}[a[1]]
                    u8(OPS['FADE']); u8(m); u8(int(a[2]) if len(a) > 2 else 20)
                elif c == 'screenshake':
                    u8(OPS['SCREENSHAKE']); u8(int(a[1]))
                elif c == 'warp':
                    d = DIRS[a[5]] if len(a) > 5 else 255
                    u8(OPS['WARP']); u16(lookup(self.maps, a[1], 'map')); u8(int(a[2])); u8(int(a[3])); u8(d)
                elif c == 'move':
                    path = a[2]
                    if not re.fullmatch(r'(\s*[UDLRJFW]\d*\s*)+', path):
                        raise ValueError('bad path ' + path)
                    u8(OPS['MOVE']); u16(actor(a[1])); u16(self.s(path)); u8(1 if 'nowait' in a else 0)
                elif c == 'face':
                    u8(OPS['FACE']); u16(actor(a[1])); u8(DIRS[a[2]])
                elif c == 'emote':
                    u8(OPS['EMOTE']); u16(actor(a[1])); u8(EMOTES[a[2]]); u8(int(a[3]) if len(a) > 3 else 48)
                elif c in ('hidenpc', 'shownpc'):
                    u8(OPS['NPCVIS']); u16(actor(a[1])); u8(1 if c == 'shownpc' else 0)
                elif c == 'spawn':
                    u8(OPS['SPAWN']); u16(actor(a[1])); u16(lookup(self.sprites, a[2], 'sprite'))
                    u8(int(a[3])); u8(int(a[4])); u8(DIRS[a[5]])
                elif c == 'despawn':
                    u8(OPS['DESPAWN']); u16(actor(a[1]))
                elif c == 'lock':
                    u8(OPS['LOCK'])
                elif c == 'release':
                    u8(OPS['RELEASE'])
                elif c == 'minigame':
                    u8(OPS['MINIGAME']); u8(MINIGAMES.index(a[1]))
                elif c == 'badge':
                    u8(OPS['BADGE']); u8(int(a[1]))
                elif c == 'chapter':
                    u8(OPS['CHAPTER']); u8(int(a[1]))
                elif c == 'loading':
                    u8(OPS['LOADING']); u16(int(a[1]))
                elif c == 'call':
                    u8(OPS['CALL']); u16(lookup(self.ids, a[1], 'script'))
                elif c == 'special':
                    u8(OPS['SPECIAL']); u8(SPECIALS.index(a[1])); u16(int(a[2]) if len(a) > 2 else 0)
                elif c == 'strvar':
                    u8(OPS['STRVAR']); u8(int(a[1])); u16(self.s(a[2]))
                elif c == 'notice':
                    u8(OPS['NOTICE']); u16(self.s(a[1]))
                elif c == 'random':
                    u8(OPS['RANDOM']); u16(int(a[1])); u8(self.var(a[-1]))
                else:
                    raise ValueError('unknown command ' + c)
            except (ValueError, IndexError, KeyError) as e:
                self.errors.append(f'{f}:{ln}: {name}: {e}: {t}')
        u8(OPS['END'])
        for pos, l in fixups:
            if l not in labels:
                self.errors.append(f'{f}: {name}: unknown label {l}')
                continue
            struct.pack_into('<H', code, pos, labels[l])
        return bytes(code)

    def write(self):
        if self.errors:
            print('\n'.join(self.errors))
            raise SystemExit('script errors')
        n = len(self.order)
        blob = bytearray(b'SCR1')
        blob += struct.pack('<HH', n, len(self.strlist))
        offs_pos = len(blob)
        blob += b'\0' * (4 * n + 4 * len(self.strlist))
        offs = []
        for name in self.order:
            offs.append(len(blob))
            blob += self.scripts[name]
            while len(blob) % 2:
                blob.append(0)
        soffs = []
        for st in self.strlist:
            soffs.append(len(blob))
            blob += st.encode('utf-8') + b'\0'
        struct.pack_into(f'<{n}I', blob, offs_pos, *offs)
        struct.pack_into(f'<{len(soffs)}I', blob, offs_pos + 4 * n, *soffs)
        os.makedirs(os.path.join(ROOT, 'nitrofs'), exist_ok=True)
        open(os.path.join(ROOT, 'nitrofs/scripts.bin'), 'wb').write(blob)
        json.dump(self.ids, open(os.path.join(ROOT, 'build/script_ids.json'), 'w'), indent=0)
        json.dump(self.flags, open(os.path.join(ROOT, 'build/flag_ids.json'), 'w'), indent=0)
        h = ['// Generated by tools/mkscripts.py', '#pragma once']
        tr = sorted(load_ids('trainer').items(), key=lambda kv: kv[1])
        base = self.flags['TRAINER_' + tr[0][0]] if tr else 0
        for t, i in tr:
            assert self.flags['TRAINER_' + t] == base + i, 'trainer flags not contiguous'
        h.append(f'#define FLAG_TRAINER_BASE {base}')
        for k, v in self.flags.items():
            h.append(f'#define FLAG_{k} {v}')
        for k, v in self.vars.items():
            h.append(f'#define VAR_{k} {v}')
        for k, v in self.ids.items():
            h.append(f'#define SCRIPT_{k.upper()} {v}')
        open(os.path.join(ROOT, 'include/gen/flags.h'), 'w').write('\n'.join(h) + '\n')
        print('scripts', n, 'strings', len(self.strlist), 'flags', len(self.flags), 'bytes', len(blob))


def main():
    files = sorted(glob.glob(os.path.join(ROOT, 'assets/scripts/*.evs')))
    c = Compiler()
    # trainer defeat flags: contiguous, right after the 8 badges (FLAG_TRAINER_BASE + trainer id)
    for t, i in sorted(load_ids('trainer').items(), key=lambda kv: kv[1]):
        c.flag('TRAINER_' + t)
    # flags referenced by maps (hide=/show=/item flags) must exist: scan map files
    for mp in glob.glob(os.path.join(ROOT, 'assets/maps/*.map')):
        for line in open(mp, encoding='utf-8'):
            for m in re.finditer(r'(?:hide|show|if|ifnot)=(\w+)', line):
                c.flag(m.group(1))
            parts = line.split()
            if parts and parts[0] == 'item' and len(parts) >= 5:
                c.flag(parts[4])
    c.compile_all(files)
    c.write()


if __name__ == '__main__':
    main()
