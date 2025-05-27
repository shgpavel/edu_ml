#include <list.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <time.h>

int main(void) {
    const int N = 100000;
    ListEntry *list = NULL;

    clock_t t0 = clock();
    for (int i = 0; i < N; ++i)
        list_append(&list, (void*)(intptr_t)i);
    clock_t t1 = clock();

    long long sum = 0;
    for (ListEntry *e = list; e; e = list_next(e))
        sum += (intptr_t)list_data(e);
    clock_t t2 = clock();

    printf("list_append=%f iterate=%f\n",
           (double)(t1-t0)/CLOCKS_PER_SEC,
           (double)(t2-t1)/CLOCKS_PER_SEC);

    list_free(list);
    return sum > 0 ? 0 : 1;
}
