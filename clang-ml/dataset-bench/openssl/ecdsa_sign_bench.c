#include <openssl/evp.h>
#include <openssl/ec.h>

#define LOOP_COUNT 100

int
main()
{
	EVP_PKEY     *pkey = EVP_PKEY_new();
	EVP_PKEY_CTX *pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_EC, NULL);
	EVP_PKEY_keygen_init(pctx);
	EVP_PKEY_CTX_set_ec_paramgen_curve_nid(pctx, NID_X9_62_prime256v1);
	EVP_PKEY_keygen(pctx, &pkey);

	const unsigned char msg[] = "A message to be signed";
	unsigned char       sig[256];
	size_t              siglen;

	for (int i = 0; i < LOOP_COUNT; i++) {
		EVP_MD_CTX *mdctx = EVP_MD_CTX_new();
		EVP_DigestSignInit(mdctx, NULL, EVP_sha256(), NULL, pkey);
		EVP_DigestSignUpdate(mdctx, msg, sizeof(msg));
		EVP_DigestSignFinal(mdctx, sig, &siglen);
		EVP_MD_CTX_free(mdctx);
	}

	EVP_PKEY_CTX_free(pctx);
	EVP_PKEY_free(pkey);
	return 0;
}
