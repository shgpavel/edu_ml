#include <sodium.h>
#include <stdio.h>

#define DERIVED_KEY_LEN 32

int
main(void)
{
	if (sodium_init() < 0)
		return 1;

	char          password[] = "a-very-strong-and-long-password-for-testing";
	unsigned char salt[crypto_pwhash_SALTBYTES];
	unsigned char derived_key[DERIVED_KEY_LEN];
	randombytes_buf(salt, sizeof(salt));

	if (crypto_pwhash(
	            derived_key, sizeof(derived_key), password, strlen(password),
	            salt, crypto_pwhash_OPSLIMIT_INTERACTIVE,
	            crypto_pwhash_MEMLIMIT_INTERACTIVE, crypto_pwhash_ALG_DEFAULT)
	    != 0) {
		return 1;
	}

	return 0;
}

