#include <yaml.h>
#include <stdio.h>

#define LOOP_COUNT 1000

int
main()
{
	FILE           *fh;
	yaml_parser_t   parser;
	yaml_document_t document;

	for (int i = 0; i < LOOP_COUNT; i++) {
		fh = fopen("config.yaml", "r");
		if (fh == NULL)
			return 1;

		yaml_parser_initialize(&parser);
		yaml_parser_set_input_file(&parser, fh);

		if (!yaml_parser_load(&parser, &document)) {
			yaml_parser_delete(&parser);
			fclose(fh);
			return 1;
		}

		yaml_document_delete(&document);
		yaml_parser_delete(&parser);
		fclose(fh);
	}
	return 0;
}
