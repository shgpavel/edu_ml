#include <glib.h>

static gint
int_compare(gconstpointer a, gconstpointer b)
{
	gint ia = GPOINTER_TO_INT(a);
	gint ib = GPOINTER_TO_INT(b);
	return (ia < ib) ? -1 : (ia > ib) ? 1 : 0;
}

static gboolean
visit_node(gpointer key, gpointer value, gpointer data)
{
	(void)key;
	(void)value;
	return FALSE; /* continue traversal */
}

int
main(void)
{
	GTree *t = g_tree_new(int_compare);
	for (gint i = 0; i < 5000; i++)
		g_tree_insert(t, GINT_TO_POINTER(i), GINT_TO_POINTER(i + 1));
	g_tree_foreach(t, visit_node, NULL);
	g_tree_destroy(t);
	return 0;
}
