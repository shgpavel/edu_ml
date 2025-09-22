#include <glib.h>
int
main(void)
{
	GList *list = NULL;
	for (int i = 0; i < 10000; i++)
		list = g_list_prepend(list, GINT_TO_POINTER(i));
	for (GList *l = list; l; l = l->next)
		(void)GPOINTER_TO_INT(l->data);
	g_list_free(list);
	return 0;
}
