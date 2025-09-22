#include <libxml/parser.h>
#define LOOP_COUNT 1000

int
main()
{
	for (int i = 0; i < LOOP_COUNT; i++) {
		xmlDocPtr doc = xmlReadFile("books.xml", NULL, 0);
		if (doc == NULL)
			return 1;
		xmlFreeDoc(doc);
	}
	xmlCleanupParser();
	return 0;
}
