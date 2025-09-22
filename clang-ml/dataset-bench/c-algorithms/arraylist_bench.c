#include <arraylist.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>

int
main(void)
{
	const int  N    = 1000000;
	ArrayList *list = arraylist_new(0);
	if (!list)
		return 1;

	long long sum = 0;
	clock_t   t0  = clock();
	for (int i = 0; i < N; ++i) {
		arraylist_append(list, (void *)(intptr_t)i);
		sum += i;
	}
	clock_t t1 = clock();

	printf("arraylist_append=%f\n", (double)(t1 - t0) / CLOCKS_PER_SEC);

	arraylist_free(list);
	return sum == (long long)N * (N - 1) / 2 ? 0 : 1;
}
