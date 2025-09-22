#include <gcrypt.h>
#include <string.h>

#define ITERATIONS 100000
#define KEY_LEN    64

int
main()
{
	gcry_check_version(GCRYPT_VERSION);
	gcry_control(GCRYCTL_DISABLE_SECMEM, 0);
	gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);

	const char         *password = "super-secret-password";
	const unsigned char salt[]   = "some-random-salt";
	unsigned char       derived_key[KEY_LEN];

	if (gcry_kdf_derive(password, strlen(password), GCRY_KDF_PBKDF2,
	                    GCRY_MD_SHA512, salt, sizeof(salt) - 1, ITERATIONS,
	                    KEY_LEN, derived_key)) {
		return 1;
	}

	return 0;
}
