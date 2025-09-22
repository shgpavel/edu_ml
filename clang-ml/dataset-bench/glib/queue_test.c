#include <glib.h>
int
main(void)
{
	GQueue *q = g_queue_new();
	for (int i = 0; i < 10000; i++)
		g_queue_push_tail(q, GINT_TO_POINTER(i));
	while (!g_queue_is_empty(q))
		(void)GPOINTER_TO_INT(g_queue_pop_head(q));
	g_queue_free(q);
	return 0;
}
