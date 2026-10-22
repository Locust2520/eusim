"""Translation coverage, generated tables and production runtime fallback regressions."""
import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from test_progression import ROOT, run_c
import mklang
import i18n_extract


class TranslationTests(unittest.TestCase):
    def test_catalog_covers_current_sources_and_french_is_complete(self):
        catalog = json.loads((ROOT / 'assets/i18n/catalog.json').read_text())
        active = {e['id']: e for e in catalog if e.get('used', True)}
        french, _, bad = mklang.validated_translations('fr', active, require_complete=True)
        self.assertFalse(bad)
        self.assertEqual(set(active), set(french))
        extracted = i18n_extract.c_strings() + i18n_extract.script_strings()
        extracted += i18n_extract.data_strings() + i18n_extract.map_names()
        covered = {e['en'] for e in active.values()}
        self.assertFalse({s for s, _ in extracted if s.strip() and s not in i18n_extract.C_SKIP} - covered)
        self.assertEqual(len(covered), len(active), 'two catalogue ids share the same English source')
        for path in (ROOT / 'assets/text').glob('*.txt'):
            self.assertTrue((path.parent / 'fr' / path.name).is_file(), path.name)

    def test_invalid_or_blank_translations_fall_back_to_the_english_source(self):
        entries = {1: {'en': 'Hello %s'}, 2: {'en': 'Yes'}, 3: {'en': 'No'}}
        with patch.object(mklang, 'load', return_value={1: 'Hallo %d', 2: ' ', 3: 'Nein'}):
            with contextlib.redirect_stderr(io.StringIO()):
                result, _, bad = mklang.validated_translations('de', entries)
            self.assertEqual(result, {3: 'Nein'})
            self.assertEqual(bad, 2)
            with self.assertRaises(ValueError):
                mklang.validated_translations('de', entries, require_complete=True)
        with patch.object(mklang, 'load', return_value={1: 'Bonjour %s'}):
            with self.assertRaisesRegex(ValueError, 'missing translation'):
                mklang.validated_translations('fr', entries, require_complete=True)

    def test_runtime_fallback_switching_and_localized_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(mklang, 'OUT', str(root / 'lang')):
                with contextlib.redirect_stdout(io.StringIO()):
                    mklang.main()
            # Simulate partial tables, one with an explicit identity translation.
            def table(code, translations):
                entries = sorted((mklang.fnv(s.encode()), t.encode() + b'\0') for s, t in translations.items())
                blob = bytearray(b'LNG1' + struct.pack('<I', len(entries)))
                offset = 8 + 8 * len(entries)
                for h, t in entries:
                    blob += struct.pack('<II', h, offset)
                    offset += len(t)
                blob += b''.join(t for _, t in entries)
                (root / f'lang/{code}.bin').write_bytes(blob)
            self.assertFalse((root / 'lang/en.bin').exists())
            table('de', {'RULING': 'URTEIL', 'Archives': 'Archives'})
            table('fr', {'RULING': 'ARRÊT', 'Yes': 'Oui'})
            (root / 'lang/es.bin').unlink()
            (root / 'lang/nl.bin').write_bytes(b'LNG1')
            (root / 'lang/it.bin').write_bytes(b'LNG1' + struct.pack('<III', 1, 0, 99999))
            (root / 'text/fr').mkdir(parents=True)
            (root / 'text/de').mkdir()
            (root / 'text/credits.txt').write_bytes(b'English credits')
            (root / 'text/fr/credits.txt').write_bytes(b'French credits')
            (root / 'text/de/credits.txt').write_bytes(b'German credits')
            source = (ROOT / 'source/lang.c').read_text()
            source = '\n'.join(line for line in source.splitlines() if not line.startswith('#include'))
            run_c(r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;
typedef uint32_t u32;
#define LANG_COUNT 24
#define LANG_DEFAULT 5
typedef struct { const char *code, *name; } LangInfo;
#define NUM_TYPES 1
#define NUM_MOVES 1
#define NUM_SPECIES 1
#define NUM_ITEMS_DEF 1
#define NUM_TRAINERS 1
static const char *type_names[] = {"RULING"};
static struct { const char *name, *desc; } moves[] = {{"RULING", "Yes"}}, items[] = {{"RULING", "Yes"}};
static struct { const char *name, *dex, *category; } species[] = {{"RULING", "Yes", "No"}};
static struct { const char *name, *cls, *intro, *defeat, *win; } trainers[] = {{"RULING", "Yes", "No", "Yes", "No"}};
static void *fs_try_load(const char *path, u32 *size) {
    char full[1024];
    snprintf(full, sizeof full, "%s/%s", ''' + json.dumps(directory) + r''', path);
    FILE *f = fopen(full, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END); long n = ftell(f); rewind(f);
    void *data = malloc(n ? n : 1);
    assert(fread(data, 1, n, f) == (size_t)n); fclose(f);
    if (size) *size = n;
    return data;
}
''' + source + r'''
static void credits(const char *expected) {
    u32 size; void *text = lang_load_text("text/credits.txt", &size);
    assert(text && size == strlen(expected) && !memcmp(text, expected, size)); free(text);
}
int main(void) {
    assert(g_lang == lang_index("en"));
    lang_set(-1);
    assert(g_lang == lang_index("en"));
    assert(!strcmp(tr("RULING"), "RULING"));
    assert(!strcmp(type_names[0], "RULING"));
    assert(!strcmp(tr("Yes"), "Yes"));
    assert(!tr(NULL) && !strcmp(tr(""), ""));
    assert(!strcmp(tr("Player nickname"), "Player nickname"));
    credits("English credits");
    lang_set(lang_index("de"));
    assert(!strcmp(tr("RULING"), "URTEIL"));
    assert(!strcmp(tr("Archives"), "Archives"));
    assert(!strcmp(tr("Yes"), "Yes"));
    assert(!strcmp(type_names[0], "URTEIL"));
    credits("German credits");
    const char *broken[] = {"es", "nl", "it"};
    for (int i = 0; i < 3; i++) {
        lang_set(lang_index(broken[i]));
        assert(!strcmp(tr("RULING"), "RULING"));
        credits("English credits");
    }
    lang_set(lang_index("fr"));
    assert(!strcmp(tr("RULING"), "ARRÊT"));
    assert(!strcmp(tr("Yes"), "Oui"));
    assert(!strcmp(type_names[0], "ARRÊT"));
    assert(!strcmp(moves[0].desc, "Oui"));
    credits("French credits");
    lang_set(LANG_COUNT);
    assert(!strcmp(type_names[0], "RULING"));
    assert(!strcmp(moves[0].desc, "Yes"));
    return 0;
}
''')


if __name__ == '__main__':
    unittest.main()
