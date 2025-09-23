#include <hiredis/hiredis.h>
#define LIST_SIZE  10000
#define LOOP_COUNT 1000

int
main()
{
	redisContext *c = redisConnect("127.0.0.1", 6379);
	if (c == NULL || c->err)
		return 1;

	redisCommand(c, "FLUSHDB");
	for (int i = 0; i < LIST_SIZE; i++) {
		redisAppendCommand(c, "LPUSH mylist value:%d", i);
	}
	void *reply;
	for (int i = 0; i < LIST_SIZE; i++) {
		redisGetReply(c, &reply);
		freeReplyObject(reply);
	}

	for (int i = 0; i < LOOP_COUNT; i++) {
		reply = redisCommand(c, "LRANGE mylist 0 99");
		freeReplyObject(reply);
	}

	redisFree(c);
	return 0;
}
