#!/bin/sh
# Test build that skips the title and intro (eusim_quick.nds)
set -e
cd "$(dirname "$0")"
python3 tools/build_assets.py
rm -f build/eusim_quick/source/game.c.o
sh tools/dsmake.sh QUICK=1 SCEN="${SCEN:-0}" QLANG="${QLANG:-}" -j6
test -f eusim_quick.nds
