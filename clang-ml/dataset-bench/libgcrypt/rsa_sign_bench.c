#include <gcrypt.h>
#include <string.h>

int
main()
{
	gcry_check_version(GCRYPT_VERSION);
	gcry_control(GCRYCTL_DISABLE_SECMEM, 0);
	gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);

	gcry_sexp_t  rsa_parms, rsa_keypair;
	gcry_error_t err;

	err = gcry_sexp_build(&rsa_parms, NULL, "(genkey (rsa (nbits 4:2048)))");
	if (err)
		return 1;
	err = gcry_pk_genkey(&rsa_keypair, rsa_parms);
	if (err)
		return 1;
	gcry_sexp_release(rsa_parms);

	const char   *message = "This is a message to be signed.";
	unsigned char digest[32];
	gcry_md_hash_buffer(GCRY_MD_SHA256, digest, message, strlen(message));

	gcry_sexp_t data_to_sign;
	err = gcry_sexp_build(&data_to_sign, NULL,
	                      "(data (flags pkcs1) (hash sha256 %b))",
	                      sizeof(digest), digest);
	if (err)
		return 1;

	gcry_sexp_t signature;
	err = gcry_pk_sign(&signature, data_to_sign, rsa_keypair);
	if (err)
		return 1;

	gcry_sexp_release(rsa_keypair);
	gcry_sexp_release(data_to_sign);
	gcry_sexp_release(signature);

	return 0;
}
