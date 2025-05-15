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

#include "uthash.h"

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

	size_t prev_size = bt->size;
	bt->data_size = sizeof(struct tree_el);
	bt->size += count;

	for (size_t i = 0; i < count; ++i) {
		struct tree_el toadd = va_arg(args, struct tree_el);
		size_t offset = (prev_size + i) * bt->data_size;
		memcpy(bt->memory + offset, &toadd, sizeof(struct tree_el));
	}
	va_end(args);
}

struct char_counts {
	uint32_t code;
	size_t count;
	UT_hash_handle hh;
};

struct char_counts *map = NULL;

void add_codepoint(uint32_t cp) {
	struct char_counts *entry;
	HASH_FIND(hh, map, &cp, sizeof(cp), entry);
	if (entry) {
		entry->count++;
	} else {
		entry = malloc(sizeof(struct char_counts));
		entry->code = cp;
		entry->count = 1;
		HASH_ADD(hh, map, code, sizeof(cp), entry);
	}
}

void count_utf8(char *s) {
	unsigned char *p = (unsigned char *)s;
	while (*p) {
		uint32_t cp;
		int len;
		if (*p < 0x80) {
			cp = *p;
			len = 1;
		} else if ((*p & 0xE0) == 0xC0) {
			cp = *p & 0x1F;
			len = 2;
		} else if ((*p & 0xF0) == 0xE0) {
			cp = *p & 0x0F;
			len = 3;
		} else if ((*p & 0xF8) == 0xF0) {
			cp = *p & 0x07;
			len = 4;
		} else {
			p++;
			continue;
		}

		for (int i = 1; i < len && (p[i] & 0xC0) == 0x80; i++) {
			cp = (cp << 6) | (p[i] & 0x3F);
		}
		add_codepoint(cp);
		p += len;
	}
}

int compare_inbt(void const *a, void const *b) {
	struct tree_el const *ena = (struct tree_el const *)a;
	struct tree_el const *enb = (struct tree_el const *)b;
	return (ena->freq - enb->freq);
}

struct eout encoder(char *in) {
	struct eout res = {-1, NULL};

	struct bintree bt;
	bintree_create(&bt, sizeof(struct tree_el), 1000);

	// struct tree_el min_heap[1000];

	count_utf8(in);
	struct char_counts *entry, *tmp;
	HASH_ITER(hh, map, entry, tmp) {
		struct tree_el item = {entry->count, entry->code};

		// skip CR & LF
		if (entry->code == 10 || entry->code == 13) continue;
		bintree_add(&bt, item);

		// printf("U+%04X: %zu\n", entry->code, entry->count);
		// printf("%lc: %zu\n", entry->code, entry->count);

		HASH_DEL(map, entry);
		free(entry);
	}

	qsort(bt.memory, bt.size, bt.data_size, compare_inbt);
	bintree_print(&bt);

	bintree_destroy(&bt);

	return res;
}

void *decoder(char *in) {
	return in;
}

int main() {
	setlocale(LC_ALL, "");

	char *str = (char *)malloc(40 * sizeof(char));
	strcpy(str, "abracadabra");
	encoder(str);

	free(str);
}
