#include <yaml.h>
#include <stdio.h>

#define LOOP_COUNT  1000
#define BUFFER_SIZE 65536

int
main()
{
	FILE *fh = fopen("config.yaml", "r");
	if (fh == NULL)
		return 1;

	yaml_parser_t   parser;
	yaml_document_t document;
	yaml_parser_initialize(&parser);
	yaml_parser_set_input_file(&parser, fh);
	yaml_parser_load(&parser, &document);
	yaml_parser_delete(&parser);
	fclose(fh);

	yaml_emitter_t emitter;
	unsigned char  buffer[BUFFER_SIZE];
	size_t         written = 0;

	for (int i = 0; i < LOOP_COUNT; i++) {
		yaml_emitter_initialize(&emitter);
		yaml_emitter_set_output_string(&emitter, buffer, BUFFER_SIZE,
		                               &written);

		if (yaml_emitter_dump(&emitter, &document) != 1) {
			yaml_emitter_delete(&emitter);
			yaml_document_delete(&document);
			return 1;
		}
		yaml_emitter_delete(&emitter);
	}

	yaml_document_delete(&document);
	return 0;
}
