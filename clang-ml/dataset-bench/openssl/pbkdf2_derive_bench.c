#include <openssl/evp.h>
#define ITERATIONS 100000

int
main()
{
	unsigned char       out[64];
	const char          password[] = "my-secret-password";
	const unsigned char salt[]     = "random-salt";

	PKCS5_PBKDF2_HMAC(password, -1, salt, sizeof(salt), ITERATIONS,
	                  EVP_sha256(), sizeof(out), out);

	return 0;
}
