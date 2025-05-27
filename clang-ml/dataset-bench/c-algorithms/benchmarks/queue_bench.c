#include <queue.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>

int main(void) {
    const int N = 50000;
    Queue *q = queue_new();
    if (!q) return 1;

    clock_t t0 = clock();
    for (int i = 0; i < N; ++i)
        queue_push_tail(q, (void*)(intptr_t)i);
    clock_t t1 = clock();

    long long sum = 0;
    while (!queue_is_empty(q))
        sum += (intptr_t)queue_pop_head(q);
    clock_t t2 = clock();

    printf("queue_push=%f pop=%f\n",
           (double)(t1-t0)/CLOCKS_PER_SEC,
           (double)(t2-t1)/CLOCKS_PER_SEC);

    queue_free(q);
    return sum > 0 ? 0 : 1;
}
