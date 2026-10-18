#!/bin/sh
# Full build: assets (Python) then ROM (BlocksDS)
set -e
cd "$(dirname "$0")"
python3 tools/build_assets.py
sh tools/dsmake.sh -j6
test -f EU_Simulator.nds
