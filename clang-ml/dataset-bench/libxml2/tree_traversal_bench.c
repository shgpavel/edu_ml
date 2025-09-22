#include <libxml/parser.h>
#define LOOP_COUNT 1000

static long node_count = 0;
void
walk_tree(xmlNode *a_node)
{
	for (xmlNode *cur_node = a_node; cur_node; cur_node = cur_node->next) {
		node_count++;
		walk_tree(cur_node->children);
	}
}

int
main()
{
	xmlDocPtr doc = xmlReadFile("books.xml", NULL, 0);
	if (doc == NULL)
		return 1;
	xmlNode *root_element = xmlDocGetRootElement(doc);

	for (int i = 0; i < LOOP_COUNT; i++) {
		node_count = 0;
		walk_tree(root_element);
	}

	xmlFreeDoc(doc);
	xmlCleanupParser();
	return (node_count > 0) ? 0 : 1;
}
