#include <stdio.h>
/* libnds from BlocksDS 1.24 expects a newer picolibc symbol */
int __bufio_flush(FILE *f);
int __bufio_close_nf(FILE *f) { return __bufio_flush(f); }
