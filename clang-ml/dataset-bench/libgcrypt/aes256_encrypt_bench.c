#include <stdio.h>
#include <stdlib.h>
#include <gcrypt.h>

#define BUFFER_SIZE (16 * 1024 * 1024) // 16 MB
#define KEY_LENGTH  32                 // AES-256
#define IV_LENGTH   16                 // AES block size

int
main()
{
	gcry_check_version(GCRYPT_VERSION);
	gcry_control(GCRYCTL_DISABLE_SECMEM, 0);
	gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);

	unsigned char  key[KEY_LENGTH] = "my-very-secret-key-for-aes-256";
	unsigned char  iv[IV_LENGTH]   = "initial-vector-!";

	unsigned char *buffer          = malloc(BUFFER_SIZE);
	if (!buffer)
		return 1;

	gcry_cipher_hd_t hd;
	if (gcry_cipher_open(&hd, GCRY_CIPHER_AES256, GCRY_CIPHER_MODE_CBC, 0))
		return 1;
	if (gcry_cipher_setkey(hd, key, KEY_LENGTH))
		return 1;
	if (gcry_cipher_setiv(hd, iv, IV_LENGTH))
		return 1;

	if (gcry_cipher_encrypt(hd, buffer, BUFFER_SIZE, NULL, 0))
		return 1;

	gcry_cipher_close(hd);
	free(buffer);
	return 0;
}
