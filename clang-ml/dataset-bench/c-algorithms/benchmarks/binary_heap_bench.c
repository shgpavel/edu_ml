#include <binary-heap.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

static int int_cmp(void *a, void *b) {
    int ia = *(int*)a;
    int ib = *(int*)b;
    return (ia>ib)-(ia<ib);
}

int main(void) {
    const int N = 200000;
    BinaryHeap *h = binary_heap_new(BINARY_HEAP_TYPE_MIN, int_cmp);
    if (!h) return 1;

    int *vals = malloc(sizeof(int)*N);
    srand(2);
    for (int i = 0; i < N; ++i) vals[i] = rand();

    clock_t t0 = clock();
    for (int i = 0; i < N; ++i)
        binary_heap_insert(h, &vals[i]);
    clock_t t1 = clock();

    for (int i = 0; i < N; ++i)
        if (binary_heap_pop(h) == NULL) return 1;
    clock_t t2 = clock();

    printf("binary_heap_insert=%f pop=%f\n",
           (double)(t1-t0)/CLOCKS_PER_SEC,
           (double)(t2-t1)/CLOCKS_PER_SEC);

    binary_heap_free(h);
    free(vals);
    return 0;
}
