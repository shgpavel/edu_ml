#include <hiredis/hiredis.h>
#define TOTAL_COMMANDS 10000

int
main()
{
	redisContext *c = redisConnect("127.0.0.1", 6379);
	if (c == NULL || c->err)
		return 1;

	redisCommand(c, "FLUSHDB");

	void *reply;
	for (int i = 0; i < TOTAL_COMMANDS; i++) {
		reply = redisCommand(c, "LPUSH mylist value:%d", i);
		freeReplyObject(reply);
	}

	redisFree(c);
	return 0;
}
