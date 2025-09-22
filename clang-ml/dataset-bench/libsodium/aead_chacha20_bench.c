#include <sodium.h>
#include <stdio.h>
#include <stdlib.h>

#define MESSAGE_SIZE (32 * 1024 * 1024)

int
main(void)
{
	if (sodium_init() < 0)
		return 1;

	unsigned char *message = malloc(MESSAGE_SIZE);
	unsigned char *ciphertext
	        = malloc(MESSAGE_SIZE + crypto_aead_chacha20poly1305_IETF_ABYTES);
	if (!message || !ciphertext)
		return 1;
	randombytes_buf(message, MESSAGE_SIZE);

	unsigned char key[crypto_aead_chacha20poly1305_IETF_KEYBYTES];
	unsigned char nonce[crypto_aead_chacha20poly1305_IETF_NPUBBYTES];
	crypto_secretbox_keygen(key);
	randombytes_buf(nonce, sizeof(nonce));

	unsigned long long ciphertext_len;

	crypto_aead_chacha20poly1305_ietf_encrypt(ciphertext, &ciphertext_len,
	                                          message, MESSAGE_SIZE, NULL, 0,
	                                          NULL, nonce, key);

	free(message);
	free(ciphertext);
	return 0;
}
