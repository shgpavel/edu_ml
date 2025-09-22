#include <stdio.h>
#include <stdlib.h>
#include <gcrypt.h>

#define BUFFER_SIZE (16 * 1024 * 1024) // 16 MB
#define LOOP_COUNT  5

int
main()
{
	if (!gcry_check_version(GCRYPT_VERSION)) {
		fprintf(stderr, "libgcrypt version mismatch\n");
		return 1;
	}
	gcry_control(GCRYCTL_DISABLE_SECMEM, 0);
	gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);

	unsigned char *buffer = malloc(BUFFER_SIZE);
	if (!buffer)
		return 1;

	for (size_t i = 0; i < BUFFER_SIZE; i++) {
		buffer[i] = (unsigned char)i;
	}

	unsigned char digest[64];

	for (int i = 0; i < LOOP_COUNT; i++) {
		gcry_md_hash_buffer(GCRY_MD_SHA512, digest, buffer, BUFFER_SIZE);
	}

	free(buffer);
	return 0;
}
