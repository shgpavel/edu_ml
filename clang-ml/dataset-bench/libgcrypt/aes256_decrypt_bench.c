#include <stdio.h>
#include <stdlib.h>
#include <gcrypt.h>

#define BUFFER_SIZE (16 * 1024 * 1024) // 16 MB
#define KEY_LENGTH  32
#define IV_LENGTH   16

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

	gcry_cipher_hd_t enc_hd;
	gcry_cipher_open(&enc_hd, GCRY_CIPHER_AES256, GCRY_CIPHER_MODE_CBC, 0);
	gcry_cipher_setkey(enc_hd, key, KEY_LENGTH);
	gcry_cipher_setiv(enc_hd, iv, IV_LENGTH);
	gcry_cipher_encrypt(enc_hd, buffer, BUFFER_SIZE, NULL, 0);
	gcry_cipher_close(enc_hd);

	gcry_cipher_hd_t dec_hd;
	if (gcry_cipher_open(&dec_hd, GCRY_CIPHER_AES256, GCRY_CIPHER_MODE_CBC, 0))
		return 1;
	if (gcry_cipher_setkey(dec_hd, key, KEY_LENGTH))
		return 1;
	if (gcry_cipher_setiv(dec_hd, iv, IV_LENGTH))
		return 1;

	if (gcry_cipher_decrypt(dec_hd, buffer, BUFFER_SIZE, NULL, 0))
		return 1;

	gcry_cipher_close(dec_hd);
	free(buffer);
	return 0;
}
