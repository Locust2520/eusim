# Translator brief — EU Simulator (Nintendo DS parody RPG)

You translate the game's text catalogue from French into ONE target language.
Write only your own files `assets/i18n/<code>-1.txt` … `<code>-4.txt` (paths below are relative to
`/opt/ordinatrice/eusim`). Do not touch any other file (other translators work in parallel).

## Source
`assets/i18n/catalog.txt` — one line per entry: `id<TAB>French text` (1752 entries, ids 0–1751).
Read it in chunks (e.g. `awk -F'\t' '$1>=0 && $1<250' assets/i18n/catalog.txt`). Translate from the
French. Finished reference translations to compare tone/terminology: `en-*.txt`, `de-*.txt`,
`sv-*.txt`, `pl-*.txt`, `fi-*.txt` (same ids).

## Output format
- Split: `<code>-1.txt` ids 0–499, `-2` 500–999, `-3` 1000–1499, `-4` 1500–1751.
- First line a comment: `# <Language> — ids X-Y`. Then one line per entry: `id<space>translation`.
- Keep `\f` (page break) and `\n` exactly as written (backslash sequences), same positions roughly.
- Keep every printf conversion (`%s`, `%d`, `%lu`, `%02lu`, `%03d`…) and every `{P}` placeholder,
  same count and SAME ORDER. A line that fails this check is dropped by the build.
- If the target grammar needs case endings on a `%s` name, rephrase with a colon
  (`%s: funds are frozen!`) instead of attaching suffixes to `%s`.
- Skip (omit) entries that are pure proper names that stay identical in your language
  (people like `Angela Merkel`, NPC first names like `Léa`, `Hugo`, `{P}`, `Help.`, `Ehm.`, `fr` id 142):
  missing ids fall back to French automatically. Exception: Greek and Bulgarian MUST transliterate all
  person names (speaker-name ids and names inside sentences) into their alphabet; Latvian uses
  Latvian name forms (see `lv-1.txt`: Angela Merkele, Emanuels Makrons…).
- Translate city names (Bruxelles→Brussels in your language, etc.), place names, item/move/type names.

## Style
- Humorous, light satire of EU institutions; keep jokes working in your language (adapt puns).
- Oliver is a British intern: keep his English interjections in English ("Easy.", "What?!",
  "That's just smart negotiation.", "See you, loser…", "Bloody hell", "Rejoin?").
- Trump/Farage/etc. English catchphrases stay English (TREMENDOUS, Sad!, Get Brexit done!,
  Whatever it takes, Wir schaffen das, OXI/NAI…).
- Use the language's normal punctuation and quotes; no French spaces before ! ? : ;
- Informal "you" (tu-form) for the player unless the French uses "vous" in a formal setting
  (officials) — follow what's natural; be consistent.
- Screen is tiny (DS, 256 px). Keep UI labels short:
  - ids 0–4: 3-letter status abbreviations (lobby influence, scandal, frozen funds, asleep, blocked).
  - id 5 / 213: level abbreviation (e.g. "Lv.%d") — ≤4 chars before %d.
  - ids 6–9: battle menu buttons (DEBATE/BAG/RUN/TEAM), uppercase, ≤9 chars ideally.
  - ids 26–32: stat names, ≤13 chars (Argumentation, Resilience, Expertise, Diplomacy, Reactivity,
    Accuracy, Evasion). Reuse exactly these stat names inside move descriptions later.
  - ids 1001–1016: type names, ≤10 chars (abbreviate if needed).
  - id 211: HP label (keep "HP" unless your language has a standard short form). PP stays "PP".
  - Menu labels (205–209, 215–224, 328–335 etc.) short.
- Consistent glossary inside your language: Euromon(s), Eurodex, badge, stamp (the capture item),
  debate (=battle), intern, Team Lobby, Team Europe (keep both in English).

## Validation (do this before finishing)
1. `python3 tools/i18n_missing.py <code>` — lists untranslated ids; the only ones left should be
   intentional proper names. Fix anything else.
2. `python3 tools/mklang.py 2>&1 | grep -E "<code>[:-]"` — reports lines with mismatched
   placeholders and the count `<code>:N/1752`; fix every reported line.
3. Check each file has no duplicated ids and no line where you accidentally left French text.

Report at the end: count translated, any doubts.

## Completion pass (filling gaps)
- Run `python3 tools/i18n_missing.py <code>` to list every untranslated id (French source in catalog.txt).
- Translate every listed id except intentional proper names that stay identical in your language
  (see "Skip" rule above; Greek/Bulgarian/Latvian adapt names). Ids ≥ 1752 are new (jukebox track titles,
  Maastricht house): translate them all. Reference wording for the jukebox ids: `en-4.txt`, `de-4.txt`.
- Read your existing `<code>-*.txt` files first and reuse their terminology (stat names, Euromon, badge…).
- Write ONLY a new file `<code>-5.txt` (header comment `# <Language> — completion`), one `id text` per line.
  Do not edit the other files. If an id already exists elsewhere, do not repeat it.
- Validate with i18n_missing and mklang as above.

## Euromon names pass (localized puns)
The 100 Euromon names (catalogue ids 1819–1918, listed with types, category and Pokédex-style entry in
`assets/i18n/euromon_names.txt`) are now translatable. Goal: **funny, adapted names in your language**, like
Pokémon localizations do (Bulbizarre → Bulbasaur → Bisasam). Do NOT translate literally: build a pun from the
concept (EU policy, the creature's category/dex joke) + a creature-like ending that sounds good in your language.
Examples of the spirit (French): Glyphosaure = glyphosate + dinosaure; Vetoad = veto + toad; Erasmouse = Erasmus + mouse.
Rules:
- ≤ 11 characters (DS screen), one word preferably (CamelCase/accents allowed), pronounceable, unique in the list.
- Keep EU/brand acronyms recognisable when they are the joke (MiCA, IAct, PACtor, CECAgon…): adapt only if it
  makes a better pun in your language (e.g. PAC → CAP/GAP/WPR…).
- Evolution families should stay visibly related (Amendon → Amendomax, Lobbyrax → Lobbyron → Lobbyzilla,
  Inflaton → Hyperflaton, Vetoad → Vetoadmax, Roamy → Roamfree…).
- Greek and Bulgarian: write the names in your alphabet. Hungarian/Latvian/etc.: native morphology welcome.
- Some catalogue sentences mention a Euromon by name (listed under each name in euromon_names.txt as
  "mentioned in"). Re-provide those sentences (full translation, your existing wording) using your new name,
  so dialogue matches the Eurodex. Ignore false positives that refer to real things (Manneken-Pis, the MiCA
  regulation).
- Write ONLY `assets/i18n/<code>-9.txt` (header `# <Language> — Euromon names`). Validate with mklang.
- In your final report, list each French name → your name, so the coordinator can review.
