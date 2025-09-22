#include <yaml.h>
#include <stdio.h>

#define LOOP_COUNT 1000

int
main()
{
	FILE         *fh;
	yaml_parser_t parser;
	yaml_event_t  event;
	int           done = 0;

	for (int i = 0; i < LOOP_COUNT; i++) {
		fh = fopen("config.yaml", "r");
		if (fh == NULL)
			return 1;

		yaml_parser_initialize(&parser);
		yaml_parser_set_input_file(&parser, fh);

		done = 0;
		while (!done) {
			if (!yaml_parser_parse(&parser, &event)) {
				yaml_parser_delete(&parser);
				fclose(fh);
				return 1;
			}
			done = (event.type == YAML_STREAM_END_EVENT);
			yaml_event_delete(&event);
		}

		yaml_parser_delete(&parser);
		fclose(fh);
	}
	return 0;
}
