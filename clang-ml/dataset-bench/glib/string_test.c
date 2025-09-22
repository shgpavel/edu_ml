#include <glib.h>
int
main(void)
{
	gchar *s = g_strdup("");
	for (int i = 0; i < 10000; i++) {
		gchar buf[16];
		g_snprintf(buf, sizeof(buf), "%d", i);
		gchar *new = g_strjoin("", s, buf, NULL);
		g_free(s);
		s = new;
	}
	g_free(s);
	return 0;
}
