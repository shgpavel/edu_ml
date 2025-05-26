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

#define COUNT_ARGS_IMPL(_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, N, ...) N
#define COUNT_ARGS(...) \
	COUNT_ARGS_IMPL(__VA_ARGS__, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)

#define bintree_add(bintree, ...) \
	bintree_add_impl(bintree, COUNT_ARGS(__VA_ARGS__), __VA_ARGS__)

#define DEFAULT_BTSIZE 1000

struct bintree {
	size_t size;
	size_t capacity;
	size_t data_size;
	uint8_t *memory;
};

static struct huffman_el null_huf = {0, 0, NULL, NULL};

static void bintree_create(struct bintree *bt, size_t data_size,
                           size_t capacity) {
	bt->data_size = data_size;
	bt->memory = (uint8_t *)malloc(data_size * capacity);
	bt->size = 0;
	bt->capacity = capacity;
}

static void *bintree_at(struct bintree *bt, size_t i) {
	return bt->memory + i * bt->data_size;
}

static void free_elrec(struct huffman_el *el) {
	if (!el) return;
	if (el->left != NULL) free_elrec(el->left);
	if (el->right != NULL) free_elrec(el->right);
	free(el);
}

static void bintree_destroy_others(struct bintree *bt) {
	if (!bt) return;
	for (size_t i = 0; i < bt->size; ++i) {
		struct huffman_el *a = bintree_at(bt, i);
		if (a->left != NULL) free_elrec(a->left);
		if (a->right != NULL) free_elrec(a->right);
	}
}

static void bintree_destroy(struct bintree *bt) {
	bintree_destroy_others(bt);
	free(bt->memory);
	bt->data_size = 0;
	bt->size = 0;
	bt->capacity = 0;
}

static void bintree_print_recaux(struct bintree *bt, size_t index, int depth) {
	if (index >= bt->size) return;

	bintree_print_recaux(bt, 2 * index + 2, depth + 1);

	struct huffman_el *value =
	    (struct huffman_el *)(bt->memory + index * bt->data_size);

	if (value->freq == 0 && value->el == 0) goto next_iter;

	for (int i = 0; i < depth; ++i) wprintf(L"     ");

	wprintf(L"%zu(%lc)\n", value->freq, value->el);

next_iter:
	bintree_print_recaux(bt, 2 * index + 1, depth + 1);
}

static void bintree_print(struct bintree *bt) {
	if (!bt || !bt->memory || bt->size == 0) {
		fprintf(stderr, "Error: bintree print got invalid struct\n");
		return;
	}

	bintree_print_recaux(bt, 0, 0);
}

static void bintree_add_impl(struct bintree *bt, size_t count, ...) {
	va_list args;
	va_start(args, count);

	if (count > bt->capacity - bt->size) {
		va_end(args);
		return;
	}

	size_t prev_size = bt->size;
	bt->size += count;

	for (size_t i = 0; i < count; ++i) {
		struct huffman_el toadd = va_arg(args, struct huffman_el);
		size_t offset = (prev_size + i) * bt->data_size;
		memcpy(bt->memory + offset, &toadd, sizeof(struct huffman_el));
	}
	va_end(args);
}

static size_t bintree_find(struct bintree *bt, wchar_t ch) {
	for (size_t i = 0; i < bt->size; ++i) {
		struct huffman_el *cur = bintree_at(bt, i);
		if (cur->el == ch) return i;
	}
	return (size_t)-1;
}

static uint32_t utf8_decode(unsigned char const *p, uint32_t *cp, size_t *len) {
	if (*p < 0x80) {
		*cp = *p;
		*len = 1;
	} else if ((*p & 0xE0) == 0xC0) {
		*cp = *p & 0x1F;
		*len = 2;
	} else if ((*p & 0xF0) == 0xE0) {
		*cp = *p & 0x0F;
		*len = 3;
	} else if ((*p & 0xF8) == 0xF0) {
		*cp = *p & 0x07;
		*len = 4;
	} else {
		return 0;
	}
	for (size_t i = 1; i < *len; ++i) {
		if ((p[i] & 0xC0) != 0x80) return 0;
		*cp = (*cp << 6) | (p[i] & 0x3F);
	}
	return 1;
}

static void count_freq(wchar_t const *in, struct bintree *bt) {
	for (wchar_t const *p = in; *p; ++p) {
		size_t i = bintree_find(bt, *p);

		if (i != (size_t)-1) {
			struct huffman_el *el = bintree_at(bt, i);
			el->freq++;
		} else {
			struct huffman_el el = {1, *p, NULL, NULL};
			bintree_add(bt, el);
		}
	}
}

static int compare_freq(void const *a, void const *b) {
	struct huffman_el const *ea = a, *eb = b;
	return (ea->freq - eb->freq);
}

static void tree_shift(struct bintree *bt, struct huffman_el *a) {
	size_t j = bt->size;
	size_t jf = 0;
	for (; j != 0;) {
		if (!jf) {
			--j;
			struct huffman_el *right =
			    (struct huffman_el *)bintree_at(bt, j);
			if (right->freq <= a->freq) {
				++j;
				jf = 1;
				break;
			}
		}
	}
	size_t stm = (bt->size - j) * sizeof(struct huffman_el);
	if (bt->capacity < bt->size + 1) return;

	memmove(bintree_at(bt, j + 1), bintree_at(bt, j), stm);
	memmove(bintree_at(bt, j), a, sizeof(struct huffman_el));

	memcpy(a, &null_huf, sizeof(struct huffman_el));

	bt->size++;
}

static void tree_revpass(struct bintree *bt) {
	size_t count = bt->size;
	for (; count > 1; --count) {
		struct huffman_el *a = bintree_at(bt, bt->size - count);
		struct huffman_el *b = bintree_at(bt, bt->size - count + 1);

		struct huffman_el *newa =
		    (struct huffman_el *)malloc(sizeof(struct huffman_el));
		struct huffman_el *newb =
		    (struct huffman_el *)malloc(sizeof(struct huffman_el));

		memcpy(newa, a, sizeof(struct huffman_el));
		memcpy(newb, b, sizeof(struct huffman_el));

		a->left = newa;
		a->right = newb;

		a->el = 0;
		a->freq = newa->freq + newb->freq;

		memcpy(b, &null_huf, sizeof(struct huffman_el));

		tree_shift(bt, a);
	}
}

static size_t bit_fit(struct bintree *bt, struct bitbuf *code_table) {
	if (!bt) return 0;

	struct stack_item {
		struct huffman_el *node;
		uint16_t code;
		uint8_t len;
	};

	struct stack_item stack[512];
	size_t sp = 0;
	size_t out = 0;

	struct huffman_el *top =
	    (struct huffman_el *)bintree_at(bt, bt->size - 1);

	stack[sp++] = (struct stack_item){top, 0, 0};

	while (sp) {
		struct stack_item cur = stack[--sp];
		struct huffman_el *n = cur.node;

		if (!n->left && !n->right) {
			code_table[out].el = n->el;
			code_table[out].buf = cur.code;
			code_table[out].len = cur.len;
			++out;
			continue;
		}

		if (n->right) {
			uint16_t code = (cur.code << 1) | 1;
			stack[sp++] = (struct stack_item){
			    n->right, code, (uint8_t)(cur.len + 1)};
		}

		if (n->left) {
			uint16_t code = (cur.code << 1);
			stack[sp++] = (struct stack_item){
			    n->left, code, (uint8_t)(cur.len + 1)};
		}
	}

	return out;
}

struct eout encoder(wchar_t const *in) {
	struct eout res = {0, NULL, NULL};
	if (!in || !*in) return res;

	struct bintree bt;
	bintree_create(&bt, sizeof(struct huffman_el), DEFAULT_BTSIZE);

	count_freq(in, &bt);
	qsort(bt.memory, bt.size, bt.data_size, compare_freq);

	tree_revpass(&bt);

	struct bitbuf *code_table =
	    calloc(DEFAULT_BTSIZE, sizeof(struct bitbuf));
	size_t ct_size = bit_fit(&bt, code_table);
	bintree_destroy(&bt);

	uint8_t *outbuf = calloc(wcslen(in) * 8, 1);
	size_t bit_pos = 0;

	for (const wchar_t *p = in; *p; ++p) {
		struct bitbuf *found = NULL;
		for (size_t i = 0; i < ct_size; ++i) {
			if (code_table[i].el == *p) {
				found = &code_table[i];
				break;
			}
		}
		if (!found) continue;

		for (int i = found->len - 1; i >= 0; --i) {
			int bit = (found->buf >> i) & 1;
			if (bit) {
				outbuf[bit_pos / 8] |=
				    (1u << (7 - (bit_pos % 8)));
			}
			bit_pos++;
		}
	}

	res.size = bit_pos;
	res.m = outbuf;
	res.t = code_table;

	return res;
}

wchar_t *decoder(struct eout encoded) {
	if (!encoded.m || !encoded.t || encoded.size == 0) return NULL;

	size_t cap = encoded.size;
	wchar_t *out = malloc((cap + 1) * sizeof(wchar_t));
	size_t out_pos = 0;

	uint16_t current_bits = 0;
	uint8_t bit_count = 0;

	for (size_t i = 0; i < encoded.size; ++i) {
		size_t byte_index = i / 8;
		size_t bit_index = 7 - (i % 8);
		uint8_t bit = (encoded.m[byte_index] >> bit_index) & 1;

		current_bits = (current_bits << 1) | bit;
		bit_count++;

		for (size_t j = 0;; ++j) {
			struct bitbuf entry = encoded.t[j];
			if (entry.len == 0) break;

			if (entry.len == bit_count &&
			    entry.buf == current_bits) {
				out[out_pos++] = entry.el;
				current_bits = 0;
				bit_count = 0;
				break;
			}
		}
	}

	out[out_pos] = L'\0';
	return out;
}

/*
 * set of useful debug prints
 *
 * debug what is added in bit fit
 * wprintf(L"ADD: %lc code: ", n->el);
 * for (int i = cur.len - 1; i >= 0; --i)
 *   putchar((cur.code & (1 << i)) ? '1' : '0');
 * putchar('\n');
 *
 * debug out code table
 * for (size_t i = 0; i < ct_size; ++i) {
 *   wprintf(L"code el=%lc %d\n", code_table[i].el, code_table[i].buf);
 * }
 *
 * dump of bitbuf's buf
 * for (int i = bb.len - 1; i >= 0; --i) {
 *   putchar((bb.buf & (1u << i)) ? '1' : '0');
 * }
 *
 */
