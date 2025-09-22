#include <libxml/parser.h>
#define LOOP_COUNT 1000

static xmlSAXHandler sax_handler = { 0 };

int
main()
{
	for (int i = 0; i < LOOP_COUNT; i++) {
		if (xmlSAXUserParseFile(&sax_handler, NULL, "books.xml") != 0) {
			return 1;
		}
	}
	xmlCleanupParser();
	return 0;
}
