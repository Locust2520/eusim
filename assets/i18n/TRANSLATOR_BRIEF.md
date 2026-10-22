# Translator brief — EU Simulator (Nintendo DS parody RPG)

The game is written in **English** (the source language since October 2026). Every other language, French
included, is a translation table. You translate into ONE target language and write only your own file.
Paths are relative to the `rom/` folder of the project.

## Source
- `assets/i18n/catalog.txt` — every string: `id<TAB>English text`.
- `assets/i18n/new_2026-10.txt` — the strings added by the city extensions (ids 2169 and up), with a third
  column telling where each one is used (source file and line, script name, map name…). Read the scripts in
  `assets/scripts/zz_*.evs` when you need more context: speaker names, what comes before and after.
- Your language's existing files `assets/i18n/<code>-*.txt` (same ids): reuse their terminology.

## Output format
- One file per batch: for the city extensions, **`assets/i18n/<code>-10.txt`**.
- First line a comment: `# <Language> — city extensions (ids 2169+)`. Then one line per entry: `id<TAB>translation`.
- Keep `\n` and `\f` exactly as written (backslash sequences).
- Keep every printf conversion (`%s`, `%d`…) and every `{P}` placeholder: same count, SAME ORDER. A line that
  breaks this is rejected and the English shows instead.
- If the grammar needs a case ending on `%s`, rephrase (“Front: %s”) rather than gluing suffixes to `%s`.
- An entry may be left out only if it is a proper name identical in your language; the English then shows.
  Greek and Bulgarian transliterate person names (Μαρία Κάλλας / Мария Калас…); Latvian uses Latvian name forms.

## What stays as it is
- **Words in other languages are the point of many lines**: Greek in Athens (“Ένα φραπέ μέτριο (éna frapé
  métrio)”), German in Frankfurt (Ebbelwoi, Bembel, Gerippte, Handkäs mit Musik, Grüne Soße, Guten Abend),
  Luxembourgish (Moien, “Mir wëlle bleiwe wat mir sinn”), Hungarian (Egészségedre, fröccs, lángos), French in
  Brussels and Paris (“Allez, une fois”, “Un café, s'il vous plaît”, tarte flambée), Dutch (Grote Markt).
  Keep those words and their transliteration exactly; translate the explanation around them.
  In your own language's case (e.g. the German words for the German translation), write naturally: no need
  to explain to Germans that “Guten Abend” is German.
- Song and film titles: “Les Enfants du Pirée” stays French; use the established title in your language for
  the films (“Never on Sunday”, “Zorba the Greek”) and for Bertha von Suttner's novel (“Lay Down Your Arms!”).
- Codes and initials: EC145… RB832, DAX, COSCO, ECB (use your language's acronym if it has one: EZB, BCE, ΕΚΤ…),
  K6, Room 18.
- Numbers, dates and facts: never change them. Every fact in these lines was checked.

## Specific strings
- The Schuman Declaration fragments (ids 2692, 2694, 2710, 2713–2715) are excerpts of the declaration of
  9 May 1950 (abridged). Use the official text in your language where you know it, abridged the same way.
  Each fragment must stay short (about 80 characters at most: it is shown on two lines).
- “€%d” and “Specimen note – €%d”: you may write `%d €` if that is your language's convention.
- Screen space is tiny (DS, 256 px wide). Keep these short:
  - buttons ≤ 11 characters: Feel, Look, Tilt, Genuine, Counterfeit, Serve, Step, Kick, Stomp, Light, Medium,
    Dark, Eraser, Undo, Clear, Done, Keep, Retake, Red, Yellow, White, Orange, Let through, Confiscate;
    `H` is the letter painted on heavy containers: one letter, your language's initial for “heavy”, and the
    same letter in the rules of the port mini-game (“Heavy (H) never on top…”);
  - “Front side” / “Back side” name the sides of a banknote (not “go back”): use the same words as in
    “Front: %s” / “Back: %s”;
  - kiosk items (Frappé, Water, Newspaper, Koulouri, Worry beads, Mati, Bus ticket, Chewing gum) ≤ 11 characters;
  - map names (“Port of Piraeus”, “Bank of Greece – Museum”…) ≤ 32 characters;
  - mini-game titles ≤ 22 characters.
- Speaker names (Guide, Curator, Landlady, Yiayia, Evzone sergeant…) are labels above the dialogue box: short.
  Yiayia: keep the Greek word (transliterated in your alphabet if needed).

## Style
- Humorous, light satire; tu-form for the player (informal “you”) as in your existing files.
- The memorials (Grossmarkthalle in Frankfurt, Shoes on the Danube Bank in Budapest) are sober: no jokes.
- Use your language's typographic quotes and punctuation; no French spaces before ! ? : ; unless your language
  uses them.

## Validation (before finishing)
- `python3 tools/i18n_check.py <code> assets/i18n/<code>-10.txt 2169` must report 0 errors and 0 missing
  (proper names you deliberately leave out will show as missing: list them in your report).
- `python3 tools/i18n_fit.py <code> assets/i18n/<code>-10.txt 2169` measures every string that sits in a
  fixed-size box (buttons, titles, map names, captions) with the game's own fonts. It must report 0 `CUT`
  (shorten those). `LINES` means a wrapped text takes more lines than the English: keep it close to the
  English length. Add `-v` to also see the strings that only fit with the small font or condensed spacing.
- Both checks only read files, so several translators can run them at the same time. Do NOT run build
  tools (i18n_extract, mklang, build.sh).
- Report: number of lines, any doubts, the strings you shortened.
