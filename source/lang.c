// Runtime translation: FNV-1a hash of the French text -> translated text, binary search in a sorted table.
#include "lang.h"
#include "fs.h"
#include "data.h"

const LangInfo g_langs[LANG_COUNT] = {
    {"bg", "Български"}, {"cs", "Čeština"}, {"da", "Dansk"}, {"de", "Deutsch"}, {"el", "Ελληνικά"},
    {"en", "English"}, {"es", "Español"}, {"et", "Eesti"}, {"fi", "Suomi"}, {"fr", "Français"},
    {"ga", "Gaeilge"}, {"hr", "Hrvatski"}, {"hu", "Magyar"}, {"it", "Italiano"}, {"lt", "Lietuvių"},
    {"lv", "Latviešu"}, {"mt", "Malti"}, {"nl", "Nederlands"}, {"pl", "Polski"}, {"pt", "Português"},
    {"ro", "Română"}, {"sk", "Slovenčina"}, {"sl", "Slovenščina"}, {"sv", "Svenska"},
};
int g_lang = LANG_DEFAULT; // English

// 'LNG1', u32 count, count x {u32 hash, u32 offset}, then the UTF-8 strings (NUL-terminated)
static u8 *table;
static u32 count;
static u8 *english;
static u32 english_count;

static u32 fnv(const char *s)
{
    u32 h = 2166136261u;
    while (*s)
        h = (h ^ (u8)*s++) * 16777619u;
    return h;
}

static const char *lookup(const u8 *data, u32 n, u32 h)
{
    if (!data)
        return NULL;
    const u32 *e = (const u32 *)(data + 8);
    int lo = 0, hi = (int)n - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        u32 v = e[mid * 2];
        if (v == h)
            return (const char *)data + e[mid * 2 + 1];
        if (v < h)
            lo = mid + 1;
        else
            hi = mid - 1;
    }
    return NULL;
}

const char *tr(const char *s)
{
    if (!s || !s[0] || !strcmp(g_langs[g_lang].code, "fr"))
        return s;
    u32 h = fnv(s);
    const char *translated = lookup(table, count, h);
    if (!translated)
        translated = lookup(english, english_count, h);
    return translated ? translated : s;
}

int lang_index(const char *code)
{
    for (int i = 0; i < LANG_COUNT; i++)
        if (!strcmp(g_langs[i].code, code))
            return i;
    return -1;
}

// French originals of the game data, kept so the language can be changed more than once
static const char **fr_strings;
static int fr_n;

#define DATA_FIELDS(X)                                                                   \
    for (int i = 0; i < NUM_TYPES; i++) X(type_names[i]);                               \
    for (int i = 0; i < NUM_MOVES; i++) { X(moves[i].name); X(moves[i].desc); }         \
    for (int i = 0; i < NUM_SPECIES; i++) { X(species[i].name); X(species[i].dex); X(species[i].category); } \
    for (int i = 0; i < NUM_ITEMS_DEF; i++) { X(items[i].name); X(items[i].desc); }     \
    for (int i = 0; i < NUM_TRAINERS; i++) {                                            \
        X(trainers[i].name); X(trainers[i].cls);                                        \
        X(trainers[i].intro); X(trainers[i].defeat); X(trainers[i].win);                \
    }

static void swap_data(void)
{
    int k = 0;
    if (!fr_strings) {
#define COUNT(f) fr_n++
        DATA_FIELDS(COUNT)
#undef COUNT
        fr_strings = malloc(sizeof(char *) * fr_n);
#define SAVE(f) fr_strings[k++] = (f)
        DATA_FIELDS(SAVE)
#undef SAVE
        k = 0;
    }
#define SET(f) (f) = tr(fr_strings[k++])
    DATA_FIELDS(SET)
#undef SET
}

static u8 *load_table(const char *code, u32 *n)
{
    char path[32];
    snprintf(path, sizeof path, "lang/%s.bin", code);
    u32 size = 0;
    u8 *data = fs_try_load(path, &size);
    *n = 0;
    if (!data)
        return NULL;
    if (size < 8 || memcmp(data, "LNG1", 4) != 0)
        goto invalid;
    u32 entries = *(u32 *)(data + 4);
    if (entries > (size - 8) / 8)
        goto invalid;
    const u32 *e = (const u32 *)(data + 8);
    for (u32 i = 0; i < entries; i++) {
        u32 offset = e[i * 2 + 1];
        if (offset < 8 + entries * 8 || offset >= size ||
            !memchr(data + offset, 0, size - offset) ||
            (i && e[i * 2] <= e[(i - 1) * 2]))
            goto invalid;
    }
    *n = entries;
    return data;
invalid:
    free(data);
    return NULL;
}

void lang_set(int index)
{
    if (index < 0 || index >= LANG_COUNT)
        index = LANG_DEFAULT;
    g_lang = index;
    free(table);
    table = NULL;
    count = 0;
    if (!english)
        english = load_table("en", &english_count);
    if (index != LANG_DEFAULT && strcmp(g_langs[index].code, "fr") != 0)
        table = load_table(g_langs[index].code, &count);
    swap_data();
}

void *lang_load_text(const char *path, u32 *size)
{
    // Selected translation, then English; explicit French uses the original file.
    if (!strncmp(path, "text/", 5) && strcmp(g_langs[g_lang].code, "fr") != 0) {
        char p[64];
        snprintf(p, sizeof p, "text/%s/%s", g_langs[g_lang].code, path + 5);
        void *d = fs_try_load(p, size);
        if (d)
            return d;
    }
    if (!strncmp(path, "text/", 5) && strcmp(g_langs[g_lang].code, "fr") != 0 &&
        g_lang != LANG_DEFAULT) {
        char p[64];
        snprintf(p, sizeof p, "text/en/%s", path + 5);
        void *d = fs_try_load(p, size);
        if (d)
            return d;
    }
    return fs_try_load(path, size);
}
