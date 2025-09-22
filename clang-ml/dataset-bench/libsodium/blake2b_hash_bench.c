#include <sodium.h>
#include <stdio.h>
#include <stdlib.h>

#define BUFFER_SIZE (32 * 1024 * 1024)
#define HASH_SIZE   crypto_generichash_BYTES

int
main(void)
{
	if (sodium_init() < 0)
		return 1;

	unsigned char *buffer = malloc(BUFFER_SIZE);
	if (!buffer)
		return 1;
	randombytes_buf(buffer, BUFFER_SIZE);

	unsigned char hash[HASH_SIZE];

	crypto_generichash(hash, sizeof(hash), buffer, BUFFER_SIZE, NULL, 0);

	free(buffer);
	return 0;
}

