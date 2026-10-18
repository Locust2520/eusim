Standalone MIDI exports of the 24 compositions in assets/music/*.mml.
These files are for listening and editing, and are not used by the game.

Each MIDI contains one pass through the composition. MML repeats are expanded;
loopStart markers identify where playback would loop in the game.
Tracks, note timing, tempo, gate lengths, volume, pan and transposition are
preserved. Instrument arpeggios become rapid MIDI notes, approximating their
59.8261 Hz pitch changes. Drums use standard General MIDI percussion.

MIDI instruments approximate the DS sounds. The custom envelopes, vibrato,
pitch sweeps and exact square/noise/wave timbres are not reproduced.
Playback sound depends on your MIDI player or soundfont.

Regenerate from the project root with:
    python3 tools/mml_to_midi.py

Requires only Python's standard library and the project's tools/mml.py.
