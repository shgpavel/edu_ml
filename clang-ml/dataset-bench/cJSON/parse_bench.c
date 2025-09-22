#include "cJSON.h"
#include <stdio.h>

#define ITER 20000

int
main(void)
{
	const char *json
	        = "{\"name\":\"John\",\"age\":30,\"cars\":[\"Ford\",\"BMW\",\"Fiat\"]}";
	for (int i = 0; i < ITER; ++i) {
		cJSON *root = cJSON_Parse(json);
		cJSON_Delete(root);
	}
	return 0;
}

