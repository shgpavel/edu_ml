#include <sodium.h>
#include <stdlib.h>

#define MESSAGE_SIZE 4096
#define LOOP_COUNT   1000

int
main(void)
{
	if (sodium_init() < 0)
		return 1;

	unsigned char pk[crypto_sign_PUBLICKEYBYTES];
	unsigned char sk[crypto_sign_SECRETKEYBYTES];
	crypto_sign_keypair(pk, sk);

	unsigned char *message = malloc(MESSAGE_SIZE);
	if (!message)
		return 1;
	randombytes_buf(message, MESSAGE_SIZE);

	unsigned char      signed_message[MESSAGE_SIZE + crypto_sign_BYTES];
	unsigned long long signed_message_len;

	for (int i = 0; i < LOOP_COUNT; i++) {
		crypto_sign(signed_message, &signed_message_len, message,
		            MESSAGE_SIZE, sk);
	}

	free(message);
	return 0;
}

