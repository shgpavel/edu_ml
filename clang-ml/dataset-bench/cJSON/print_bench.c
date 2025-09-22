#include "cJSON.h"
#include <stdio.h>
#include <stdlib.h>

#define ITER 20000

int
main(void)
{
	cJSON *root = cJSON_CreateObject();
	cJSON_AddStringToObject(root, "language", "C");
	cJSON_AddNumberToObject(root, "year", 1972);

	for (int i = 0; i < ITER; ++i) {
		char *printed = cJSON_PrintUnformatted(root);
		free(printed);
	}
	cJSON_Delete(root);
	return 0;
}

