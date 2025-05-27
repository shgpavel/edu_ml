#include "cJSON.h"
#include <stdio.h>

#define ITER 2500
#define ARR  1000

int main(void)
{
    for (int i = 0; i < ITER; ++i) {
        cJSON *arr = cJSON_CreateIntArray(NULL, 0);
        for (int n = 0; n < ARR; ++n) {
            cJSON_AddItemToArray(arr, cJSON_CreateNumber(n));
        }
        cJSON_Delete(arr);
    }
    return 0;
}

