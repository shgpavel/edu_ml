#include <glib.h>
int
main(void)
{
	GHashTable *ht = g_hash_table_new(g_direct_hash, g_direct_equal);
	for (int i = 0; i < 5000; i++)
		g_hash_table_insert(ht, GINT_TO_POINTER(i), GINT_TO_POINTER(i * i));
	for (int i = 0; i < 5000; i++)
		(void)GPOINTER_TO_INT(g_hash_table_lookup(ht, GINT_TO_POINTER(i)));
	g_hash_table_destroy(ht);
	return 0;
}
