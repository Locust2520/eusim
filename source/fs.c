#include "fs.h"
#include <filesystem.h>
#include <nds.h>

bool fs_init(void)
{
    return nitroFSInit(NULL);
}

void *fs_try_load(const char *path, u32 *size)
{
    char full[96];
    snprintf(full, sizeof(full), "nitro:/%s", path);
    FILE *f = fopen(full, "rb");
    if (!f)
        return NULL;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    void *buf = malloc(n > 0 ? n : 1);
    if (!buf) {
        fclose(f);
        fatal("Out of memory loading %s (%ld)", path, n);
    }
    // the SD/card driver may DMA straight into RAM: keep the data cache out of the way
    DC_FlushRange(buf, n > 0 ? n : 1);
    size_t got = fread(buf, 1, n, f);
    DC_InvalidateRange(buf, n > 0 ? n : 1);
    if (got != (size_t)n) {
        fclose(f);
        free(buf);
        fatal("Read error %s", path);
    }
    fclose(f);
    if (size)
        *size = n;
    return buf;
}

void *fs_load(const char *path, u32 *size)
{
    void *p = fs_try_load(path, size);
    if (!p)
        fatal("Missing file: %s", path);
    return p;
}

u32 fs_load_into(const char *path, void *dst, u32 max)
{
    char full[96];
    snprintf(full, sizeof(full), "nitro:/%s", path);
    FILE *f = fopen(full, "rb");
    if (!f)
        return 0;
    DC_FlushRange(dst, max);
    u32 n = fread(dst, 1, max, f);
    DC_InvalidateRange(dst, max);
    fclose(f);
    return n;
}

bool fs_exists(const char *path)
{
    char full[96];
    snprintf(full, sizeof(full), "nitro:/%s", path);
    FILE *f = fopen(full, "rb");
    if (!f)
        return false;
    fclose(f);
    return true;
}
