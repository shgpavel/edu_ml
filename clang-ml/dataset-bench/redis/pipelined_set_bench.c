#include <hiredis/hiredis.h>
#define TOTAL_COMMANDS 10000

int
main()
{
	redisContext *c = redisConnect("127.0.0.1", 6379);
	if (c == NULL || c->err)
		return 1;

	redisCommand(c, "FLUSHDB");

	for (int i = 0; i < TOTAL_COMMANDS; i++) {
		redisAppendCommand(c, "SET key:%d value:%d", i, i);
	}

	void *reply;
	for (int i = 0; i < TOTAL_COMMANDS; i++) {
		redisGetReply(c, &reply);
		freeReplyObject(reply);
	}

	redisFree(c);
	return 0;
}
