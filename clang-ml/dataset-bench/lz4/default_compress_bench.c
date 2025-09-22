#include "lz4.h"
#include <stdio.h>
#include <stdlib.h>

char *
read_file(const char *filename, size_t *size)
{
	FILE *f = fopen(filename, "rb");
	if (!f)
		return NULL;
	fseek(f, 0, SEEK_END);
	*size = ftell(f);
	fseek(f, 0, SEEK_SET);
	char *buffer = (char *)malloc(*size);
	if (buffer) {
		fread(buffer, 1, *size, f);
	}
	fclose(f);
	return buffer;
}

int
main(int argc, char *argv[])
{
	if (argc < 2) {
		fprintf(stderr, "Usage: %s <input_file>\n", argv[0]);
		return 1;
	}
	const char *filename = argv[1];

	size_t      in_size;
	char       *in_buffer = read_file(filename, &in_size);
	if (!in_buffer || in_size == 0)
		return 1;

	const int max_dst_size      = LZ4_compressBound(in_size);
	char     *compressed_buffer = (char *)malloc(max_dst_size);
	if (!compressed_buffer) {
		free(in_buffer);
		return 1;
	}

	const int compressed_size = LZ4_compress_default(
	        in_buffer, compressed_buffer, in_size, max_dst_size);
	if (compressed_size <= 0) {
		free(in_buffer);
		free(compressed_buffer);
		return 1;
	}

	free(in_buffer);
	free(compressed_buffer);
	return 0;
}
