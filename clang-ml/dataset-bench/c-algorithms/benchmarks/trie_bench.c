#include <trie.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

int main(void) {
    const int N = 100000;
    Trie *trie = trie_new();
    if (!trie) return 1;

    char **words = malloc(sizeof(char*) * N);
    for (int i = 0; i < N; ++i) {
        words[i] = malloc(16);
        sprintf(words[i], "word%07d", i);
    }

    clock_t t0 = clock();
    for (int i = 0; i < N; ++i)
        trie_insert(trie, words[i], words[i]);
    clock_t t1 = clock();

    for (int i = 0; i < N; ++i)
        if (!trie_lookup(trie, words[i])) return 1;
    clock_t t2 = clock();

    printf("trie_insert=%f lookup=%f\n",
           (double)(t1-t0)/CLOCKS_PER_SEC,
           (double)(t2-t1)/CLOCKS_PER_SEC);

    for (int i = 0; i < N; ++i) free(words[i]);
    free(words);
    trie_free(trie);
    return 0;
}
