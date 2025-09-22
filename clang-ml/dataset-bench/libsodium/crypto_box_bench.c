#include <sodium.h>
#include <stdio.h>
#include <stdlib.h>

#define MESSAGE_SIZE (1 * 1024 * 1024)
#define LOOP_COUNT   10

int
main(void)
{
	if (sodium_init() < 0)
		return 1;

	unsigned char alice_pk[crypto_box_PUBLICKEYBYTES],
	        alice_sk[crypto_box_SECRETKEYBYTES];
	unsigned char bob_pk[crypto_box_PUBLICKEYBYTES],
	        bob_sk[crypto_box_SECRETKEYBYTES];
	crypto_box_keypair(alice_pk, alice_sk);
	crypto_box_keypair(bob_pk, bob_sk);

	unsigned char *message    = malloc(MESSAGE_SIZE);
	unsigned char *ciphertext = malloc(MESSAGE_SIZE + crypto_box_MACBYTES);
	if (!message || !ciphertext)
		return 1;
	randombytes_buf(message, MESSAGE_SIZE);

	unsigned char nonce[crypto_box_NONCEBYTES];

	for (int i = 0; i < LOOP_COUNT; i++) {
		randombytes_buf(nonce, sizeof(nonce));
		crypto_box_easy(ciphertext, message, MESSAGE_SIZE, nonce, bob_pk,
		                alice_sk);
	}

	free(message);
	free(ciphertext);
	return 0;
}
