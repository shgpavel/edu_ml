#include <libxml/parser.h>
#define LOOP_COUNT 1000

int
main()
{
	xmlDocPtr doc = xmlReadFile("books.xml", NULL, 0);
	if (doc == NULL)
		return 1;

	xmlChar *mem;
	int      size;
	for (int i = 0; i < LOOP_COUNT; i++) {
		xmlDocDumpMemory(doc, &mem, &size);
		if (mem) {
			xmlFree(mem);
		} else {
			return 1;
		}
	}

	xmlFreeDoc(doc);
	xmlCleanupParser();
	return 0;
}
