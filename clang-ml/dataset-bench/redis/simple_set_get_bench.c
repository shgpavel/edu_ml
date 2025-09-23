#include <hiredis/hiredis.h>
#define TOTAL_OPS 5000

int
main()
{
	redisContext *c = redisConnect("127.0.0.1", 6379);
	if (c == NULL || c->err)
		return 1;

	redisCommand(c, "FLUSHDB");

	void *reply;
	for (int i = 0; i < TOTAL_OPS; i++) {
		reply = redisCommand(c, "SET key:%d value:%d", i, i);
		freeReplyObject(reply);
		reply = redisCommand(c, "GET key:%d", i);
		freeReplyObject(reply);
	}

	redisFree(c);
	return 0;
}
