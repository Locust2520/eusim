"""Stamp the battle ABI/content, independently of ROM artwork and language."""
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent.parent
paths = [*sorted((root / 'data').glob('*.json')),
         *[root / p for p in ('source/battle.c', 'source/mon.c', 'source/multiplayer.c',
                              'include/multiplayer.h', 'include/save.h', 'include/data.h',
                              'source/local_link.c', 'source/local_wire.c', 'include/local_wire.h')]]
digest = hashlib.sha256()
for path in paths:
    digest.update(path.relative_to(root).as_posix().encode() + b'\0' + path.read_bytes())
content = f'#define LINK_BUILD 0x{digest.hexdigest()[:8]}u\n'
target = root / 'include/gen/link_build.h'
if not target.exists() or target.read_text() != content:
    target.write_text(content)
