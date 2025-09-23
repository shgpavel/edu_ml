#include <openssl/evp.h>
#include <stdlib.h>

#define BUFFER_SIZE (16 * 1024 * 1024)

int
main()
{
	unsigned char  key[32]    = { 0 };
	unsigned char  iv[12]     = { 0 };
	unsigned char *plaintext  = malloc(BUFFER_SIZE);
	unsigned char *ciphertext = malloc(BUFFER_SIZE + 16);
	if (!plaintext || !ciphertext)
		return 1;

	EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
	int             len, ciphertext_len;

	EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, key, iv);
	EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, BUFFER_SIZE);
	ciphertext_len = len;
	EVP_EncryptFinal_ex(ctx, ciphertext + len, &len);
	ciphertext_len += len;

	EVP_CIPHER_CTX_free(ctx);
	free(plaintext);
	free(ciphertext);
	return 0;
}
