#include <openssl/evp.h>
#include <stdlib.h>

#define BUFFER_SIZE (16 * 1024 * 1024)

int
main()
{
	unsigned char *buffer = malloc(BUFFER_SIZE);
	if (!buffer)
		return 1;

	EVP_MD_CTX   *mdctx = EVP_MD_CTX_new();
	const EVP_MD *md    = EVP_sha256();
	unsigned char md_value[EVP_MAX_MD_SIZE];
	unsigned int  md_len;

	EVP_DigestInit_ex(mdctx, md, NULL);
	EVP_DigestUpdate(mdctx, buffer, BUFFER_SIZE);
	EVP_DigestFinal_ex(mdctx, md_value, &md_len);

	EVP_MD_CTX_free(mdctx);
	free(buffer);
	return 0;
}
