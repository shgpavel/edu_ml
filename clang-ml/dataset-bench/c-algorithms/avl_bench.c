#include <avl-tree.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

static int
cmp(void *a, void *b)
{
	int ia = *(int *)a;
	int ib = *(int *)b;
	return (ia > ib) - (ia < ib);
}

int
main(void)
{
	const int N    = 100000;
	AVLTree  *tree = avl_tree_new(cmp);
	if (!tree)
		return 1;

	int *vals = malloc(sizeof(int) * N);
	for (int i = 0; i < N; ++i)
		vals[i] = i;

	clock_t t0 = clock();
	for (int i = 0; i < N; ++i)
		avl_tree_insert(tree, &vals[i], &vals[i]);
	clock_t t1 = clock();

	for (int i = 0; i < N; ++i)
		if (avl_tree_lookup(tree, &vals[i]) == NULL)
			return 1;
	clock_t t2 = clock();

	printf("avl_insert=%f lookup=%f\n",
	       (double)(t1 - t0) / CLOCKS_PER_SEC,
	       (double)(t2 - t1) / CLOCKS_PER_SEC);

	avl_tree_free(tree);
	free(vals);
	return 0;
}
