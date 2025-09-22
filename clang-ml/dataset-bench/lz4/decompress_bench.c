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

	size_t      original_size;
	char       *original_buffer = read_file(filename, &original_size);
	if (!original_buffer || original_size == 0)
		return 1;

	const int max_dst_size      = LZ4_compressBound(original_size);
	char     *compressed_buffer = (char *)malloc(max_dst_size);
	if (!compressed_buffer) {
		free(original_buffer);
		return 1;
	}

	const int compressed_size = LZ4_compress_default(
	        original_buffer, compressed_buffer, original_size, max_dst_size);
	if (compressed_size <= 0)
		return 1;

	char *decompressed_buffer = (char *)malloc(original_size);
	if (!decompressed_buffer)
		return 1;

	const int decompressed_size
	        = LZ4_decompress_safe(compressed_buffer, decompressed_buffer,
	                              compressed_size, original_size);
	if (decompressed_size < 0)
		return 1;

	free(original_buffer);
	free(compressed_buffer);
	free(decompressed_buffer);
	return 0;
}
