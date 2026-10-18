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
    def test_english_covers_current_sources_and_preserves_placeholders(self):
        catalog = json.loads((ROOT / 'assets/i18n/catalog.json').read_text())
        active = {e['id']: e for e in catalog if e.get('used', True)}
        english, _, bad = mklang.validated_translations('en', active, require_complete=True)
        self.assertFalse(bad)
        self.assertEqual(set(active), set(english))
        extracted = i18n_extract.c_strings() + i18n_extract.script_strings()
        extracted += i18n_extract.data_strings() + i18n_extract.map_names()
        covered = {e['fr'] for e in active.values()}
        self.assertFalse({s for s, _ in extracted if s.strip() and s not in i18n_extract.C_SKIP} - covered)
        for path in (ROOT / 'assets/text').glob('*.txt'):
            self.assertTrue((path.parent / 'en' / path.name).is_file(), path.name)

    def test_invalid_or_blank_translations_use_english_and_english_is_required(self):
        entries = {1: {'fr': 'Bonjour %s'}, 2: {'fr': 'Oui'}, 3: {'fr': 'Non'}}
        english = {1: 'Hello %s', 2: 'Yes', 3: 'No'}
        with patch.object(mklang, 'load', return_value={1: 'Hallo %d', 2: ' ', 3: 'Nein'}):
            with contextlib.redirect_stderr(io.StringIO()):
                result, _, bad = mklang.validated_translations('de', entries, english)
            self.assertEqual(result, {1: 'Hello %s', 2: 'Yes', 3: 'Nein'})
            self.assertEqual(bad, 2)
            with self.assertRaises(ValueError):
                mklang.validated_translations('en', entries, require_complete=True)
        with patch.object(mklang, 'load', return_value={1: 'Hello %s'}):
            with self.assertRaisesRegex(ValueError, 'missing translation'):
                mklang.validated_translations('en', entries, require_complete=True)

    def test_runtime_fallback_switching_and_localized_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(mklang, 'OUT', str(root / 'lang')):
                with contextlib.redirect_stdout(io.StringIO()):
                    mklang.main()
            # Simulate an older partial table with an explicit identity translation.
            translations = {'ARRÊT': 'URTEIL', 'Archives': 'Archives'}
            entries = sorted((mklang.fnv(s.encode()), t.encode() + b'\0') for s, t in translations.items())
            blob = bytearray(b'LNG1' + struct.pack('<I', len(entries)))
            offset = 8 + 8 * len(entries)
            for h, t in entries:
                blob += struct.pack('<II', h, offset)
                offset += len(t)
            blob += b''.join(t for _, t in entries)
            (root / 'lang/de.bin').write_bytes(blob)
            (root / 'lang/es.bin').unlink()
            (root / 'lang/nl.bin').write_bytes(b'LNG1')
            (root / 'lang/it.bin').write_bytes(b'LNG1' + struct.pack('<III', 1, 0, 99999))
            (root / 'text/en').mkdir(parents=True)
            (root / 'text/de').mkdir()
            (root / 'text/credits.txt').write_bytes(b'French credits')
            (root / 'text/en/credits.txt').write_bytes(b'English credits')
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
static const char *type_names[] = {"ARRÊT"};
static struct { const char *name, *desc; } moves[] = {{"ARRÊT", "Oui"}}, items[] = {{"ARRÊT", "Oui"}};
static struct { const char *name, *dex, *category; } species[] = {{"ARRÊT", "Oui", "Non"}};
static struct { const char *name, *cls, *intro, *defeat, *win; } trainers[] = {{"ARRÊT", "Oui", "Non", "Oui", "Non"}};
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
    assert(!strcmp(tr("ARRÊT"), "RULING"));
    assert(!strcmp(type_names[0], "RULING"));
    assert(!strcmp(tr("Oui"), "Yes"));
    assert(!tr(NULL) && !strcmp(tr(""), ""));
    assert(!strcmp(tr("Player nickname"), "Player nickname"));
    credits("English credits");
    lang_set(lang_index("de"));
    assert(!strcmp(tr("ARRÊT"), "URTEIL"));
    assert(!strcmp(tr("Archives"), "Archives"));
    assert(!strcmp(tr("Oui"), "Yes"));
    assert(!strcmp(type_names[0], "URTEIL"));
    credits("German credits");
    const char *broken[] = {"es", "nl", "it"};
    for (int i = 0; i < 3; i++) {
        lang_set(lang_index(broken[i]));
        assert(!strcmp(tr("ARRÊT"), "RULING"));
        credits("English credits");
    }
    lang_set(lang_index("fr"));
    assert(!strcmp(tr("ARRÊT"), "ARRÊT"));
    assert(!strcmp(type_names[0], "ARRÊT"));
    credits("French credits");
    lang_set(LANG_COUNT);
    assert(!strcmp(type_names[0], "RULING"));
    return 0;
}
''')


if __name__ == '__main__':
    unittest.main()
