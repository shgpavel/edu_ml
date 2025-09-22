#include <libxml/parser.h>
#include <libxml/xpath.h>
#define LOOP_COUNT 5000

int
main()
{
	xmlDocPtr doc = xmlReadFile("books.xml", NULL, 0);
	if (doc == NULL)
		return 1;
	xmlXPathContextPtr xpathCtx = xmlXPathNewContext(doc);
	if (xpathCtx == NULL)
		return 1;

	const xmlChar *xpathExpr = (const xmlChar *)"//book[price>10]";
	for (int i = 0; i < LOOP_COUNT; i++) {
		xmlXPathObjectPtr xpathObj
		        = xmlXPathEvalExpression(xpathExpr, xpathCtx);
		if (xpathObj == NULL)
			return 1;
		xmlXPathFreeObject(xpathObj);
	}

	xmlXPathFreeContext(xpathCtx);
	xmlFreeDoc(doc);
	xmlCleanupParser();
	return 0;
}
