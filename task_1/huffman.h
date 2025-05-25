/* SPDX-License-Identifier: Apache-2.0 */

/*
 * Copyright (C) 2025 Pavel Shago <pavel@shago.dev>
 */

#ifndef HUFFMAN_H
#define HUFFMAN_H

#include <stddef.h>
#include <stdint.h>
#include <wchar.h>

struct bitbuf {
	wchar_t el;
	uint16_t buf;
	uint8_t len;
};

struct huffman_el {
	size_t freq;
	wchar_t el;
	struct huffman_el *left, *right;
};

struct eout {
	size_t size;
	uint8_t *m;
	struct bitbuf *t;
};

struct eout encoder(const wchar_t *input);
wchar_t *decoder(struct eout encoded);
void destroy_tree(struct huffman_el *node);

#endif
