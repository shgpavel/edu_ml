#include <hash-table.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <string.h>

static unsigned str_hash(void *s) {
    unsigned char *p = s;
    unsigned h = 0;
    while (*p) h = h*31 + *p++;
    return h;
}
static int str_equal(void *a, void *b) {
    return strcmp(a,b)==0;
}

int main(void) {
    const int N = 100000;
    HashTable *ht = hash_table_new(str_hash, str_equal);
    if (!ht) return 1;

    char **keys = malloc(sizeof(char*)*N);
    for (int i = 0; i < N; ++i) {
        keys[i]=malloc(16);
        sprintf(keys[i], "k%07d", i);
    }

    clock_t t0 = clock();
    for (int i = 0; i < N; ++i)
        hash_table_insert(ht, keys[i], keys[i]);
    clock_t t1 = clock();

    for (int i = 0; i < N; ++i)
        if (!hash_table_lookup(ht, keys[i])) return 1;
    clock_t t2 = clock();

    printf("hash_insert=%f lookup=%f\n",
           (double)(t1-t0)/CLOCKS_PER_SEC,
           (double)(t2-t1)/CLOCKS_PER_SEC);

    hash_table_free(ht);
    for (int i = 0; i < N; ++i) free(keys[i]);
    free(keys);
    return 0;
}
