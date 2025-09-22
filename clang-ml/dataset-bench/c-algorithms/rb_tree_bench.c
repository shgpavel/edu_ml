#include <rb-tree.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

static int
int_cmp(void *a, void *b)
{
	int ia = *(int *)a;
	int ib = *(int *)b;
	return (ia > ib) - (ia < ib);
}

int
main(void)
{
	const int N = 200000;
	RBTree   *t = rb_tree_new(int_cmp);
	if (!t)
		return 1;

	int *vals = malloc(sizeof(int) * N);
	for (int i = 0; i < N; ++i)
		vals[i] = i;

	clock_t t0 = clock();
	for (int i = 0; i < N; ++i)
		rb_tree_insert(t, &vals[i], &vals[i]);
	clock_t t1 = clock();

	for (int i = 0; i < N; ++i)
		if (rb_tree_lookup(t, &vals[i]) == NULL)
			return 1;
	clock_t t2 = clock();

	printf("rb_tree_insert=%f lookup=%f\n",
	       (double)(t1 - t0) / CLOCKS_PER_SEC,
	       (double)(t2 - t1) / CLOCKS_PER_SEC);

	rb_tree_free(t);
	free(vals);
	return 0;
}
