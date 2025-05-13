/* SPDX-License-Identifier: Apache-2.0 */

/*
 * Copyright (C) 2025 Pavel Shago <pavel@shago.dev>
 */

#include "huffman.h"

#include <locale.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

void bintree_create(struct bintree *bt, size_t data_size, size_t capacity) {
	bt->data_size = data_size;
	bt->memory = (uint8_t *)malloc(data_size * capacity);
	bt->size = 0;
	bt->capacity = capacity;
}

void bintree_destroy(struct bintree *bt) {
	free(bt->memory);
	bt->data_size = 0;
	bt->size = 0;
	bt->capacity = 0;
}

static void bintree_print_recaux(struct bintree *bt, size_t index, int depth) {
	if (index >= bt->size) return;

	bintree_print_recaux(bt, 2 * index + 2, depth + 1);

	for (int i = 0; i < depth; ++i) printf("     ");

	struct tree_el *value =
	    (struct tree_el *)(bt->memory + index * bt->data_size);
	printf("%zu(%lc)\n", value->freq, value->el);

	bintree_print_recaux(bt, 2 * index + 1, depth + 1);
}

void bintree_print(struct bintree *bt) {
	if (!bt || !bt->memory || bt->size == 0) {
		fprintf(stderr, "Error: bintree print got invalid struct\n");
		return;
	}

	bintree_print_recaux(bt, 0, 0);
}

void bintree_add_impl(struct bintree *bt, size_t count, ...) {
	va_list args;
	va_start(args, count);

	if (count > bt->capacity - bt->size) {
		return;
	}

	bt->data_size = sizeof(struct tree_el);
	bt->size += count;

	for (size_t i = 0; i < count; ++i) {
		struct tree_el toadd = va_arg(args, struct tree_el);
		memcpy(&bt->memory[i * sizeof(struct tree_el)], &toadd,
		       sizeof(struct tree_el));
	}
	va_end(args);
}

struct eout encoder(struct ined in) {
	struct eout res = {0, in.data};

	for (size_t i = 0; i < in.data_size; ++i) {
		wprintf(L"%lc", in.data[i]);
	}

	return res;
}

void *decoder(struct ined in) {
	return in.data;
}

int main() {
	setlocale(LC_ALL, "");
	struct bintree bt;
	bintree_create(&bt, sizeof(struct tree_el), 1000);

	struct tree_el t1 = {1, L'з'};
	struct tree_el t2 = {2, 'a'};
	struct tree_el t3 = {3, L'к'};
	struct tree_el t4 = {1, L'Р'};

	bintree_add(&bt, t1, t2, t3, t4);
	bintree_print(&bt);
	bintree_destroy(&bt);

	char *str = (char *)malloc(20 * sizeof(char));
	strcpy(str, "Hello Мир\n");
	printf("%s\n", str);
	struct ined in = {20, str};
	encoder(in);

	free(str);
}
