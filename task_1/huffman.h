/* SPDX-License-Identifier: Apache-2.0 */

/*
 * Copyright (C) 2025 Pavel Shago <pavel@shago.dev>
 */

#ifndef HUFFMAN_H
#define HUFFMAN_H

#include <stddef.h>
#include <stdint.h>

#define COUNT_ARGS_IMPL(_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, N, ...) N
#define COUNT_ARGS(...) \
	COUNT_ARGS_IMPL(__VA_ARGS__, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)

#define bintree_add(bintree, ...) \
	bintree_add_impl(bintree, COUNT_ARGS(__VA_ARGS__), __VA_ARGS__)

struct bintree {
	size_t size;
	size_t capacity;
	size_t data_size;
	uint8_t *memory;
};

struct tree_el {
	size_t freq;
	wchar_t el;
};

struct eout {
	int state;
	char *r;
};

struct ined {
	size_t data_size;
	char *data;
};

struct eout encoder(struct ined);
void *decoder(struct ined);

#endif
