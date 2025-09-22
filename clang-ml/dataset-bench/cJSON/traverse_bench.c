#include "cJSON.h"
#include <stdio.h>

#define ITER 5000

int
main(void)
{
	const char *json
	        = "{\"menu\":{\"id\":\"file\",\"value\":\"File\",\"items\":["
	          "{\"id\":\"new\",\"label\":\"New\"},"
	          "{\"id\":\"open\",\"label\":\"Open\"},"
	          "{\"id\":\"close\",\"label\":\"Close\"}]}}";

	for (int i = 0; i < ITER; ++i) {
		cJSON *root = cJSON_Parse(json);
		cJSON *item = NULL;
		cJSON_ArrayForEach(item, root)
		{
			(void)item;
		}
		cJSON_Delete(root);
	}
	return 0;
}

