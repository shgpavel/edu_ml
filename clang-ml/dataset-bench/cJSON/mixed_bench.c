#include "cJSON.h"
#include <stdio.h>
#include <stdlib.h>

#define ITER 5000

int main(void)
{
    const char *templ =
        "{\"x\":%d,\"y\":%d,\"label\":\"point\",\"meta\":{\"valid\":true}}";

    char buf[128];
    for (int i = 0; i < ITER; ++i) {
        snprintf(buf, sizeof(buf), templ, i, ITER - i);
        cJSON *pt = cJSON_Parse(buf);
        /* изменим поле и снова сериализуем */
        cJSON_ReplaceItemInObject(pt, "label",
                                  cJSON_CreateString("point-updated"));
        char *printed = cJSON_PrintUnformatted(pt);
        free(printed);
        cJSON_Delete(pt);
    }
    return 0;
}

