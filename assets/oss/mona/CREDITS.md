# Mona menu emoji

Mona © 2025 Monad ABXY (https://monadabxy.com).
Source: https://github.com/MonadABXY/mona-font
Pinned revision: 07029e3c1f4e3491b0ed707b27953d1ace78d9b2.
Original file: web/Mona12ColorEmoji.woff2 (included unchanged).
License: SIL Open Font License 1.1, included as OFL.txt.
Upstream acknowledgements: UPSTREAM-README.md and NotoEmoji-OFL.txt.

The game uses rendered glyphs U+1F392 (backpack), U+1F465 (team silhouettes),
U+1F5D2 (spiral notepad), U+2699 (gear), and right-facing runners
U+1F3C3 U+200D U+27A1 (orange shirt, Max) and
U+1F3C3 U+200D U+2640 U+200D U+27A1 (purple shirt, Alex).
tools/mkmona.py extracts the
original 12px grid without antialiasing, converts colors to DS RGB15,
and generates include/gen/mona_icons.h. In-game display uses integer scaling.
These rasterized glyphs are font output; the bundled original font retains its OFL license.
