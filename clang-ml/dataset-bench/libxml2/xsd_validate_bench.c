#include <libxml/parser.h>
#include <libxml/xmlschemas.h>
#define LOOP_COUNT 500

int
main()
{
	xmlDocPtr doc = xmlReadFile("books.xml", NULL, 0);
	if (doc == NULL)
		return 1;

	xmlSchemaParserCtxtPtr pctxt  = xmlSchemaNewParserCtxt("books.xsd");
	xmlSchemaPtr           schema = xmlSchemaParse(pctxt);
	xmlSchemaValidCtxtPtr  vctxt  = xmlSchemaNewValidCtxt(schema);

	int                    result = 0;
	for (int i = 0; i < LOOP_COUNT; i++) {
		if (xmlSchemaValidateDoc(vctxt, doc) != 0) {
			result = 1;
			break;
		}
	}

	xmlSchemaFreeValidCtxt(vctxt);
	xmlSchemaFree(schema);
	xmlSchemaFreeParserCtxt(pctxt);
	xmlFreeDoc(doc);
	xmlCleanupParser();
	return result;
}
