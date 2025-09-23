#include <sqlite3.h>
#include <stdio.h>

#define DB_NAME     "insert_test.db"
#define NUM_INSERTS 50000

int
main()
{
	sqlite3 *db;
	char    *err_msg = 0;

	remove(DB_NAME);

	int rc = sqlite3_open(DB_NAME, &db);
	if (rc != SQLITE_OK)
		return 1;

	const char *sql_create = "CREATE TABLE Users(Id INT, Name TEXT);";
	rc                     = sqlite3_exec(db, sql_create, 0, 0, &err_msg);
	if (rc != SQLITE_OK) {
		sqlite3_close(db);
		return 1;
	}

	sqlite3_exec(db, "BEGIN TRANSACTION;", 0, 0, &err_msg);

	const char   *sql_insert = "INSERT INTO Users VALUES(?, ?);";
	sqlite3_stmt *stmt;
	sqlite3_prepare_v2(db, sql_insert, -1, &stmt, 0);

	for (int i = 0; i < NUM_INSERTS; i++) {
		sqlite3_bind_int(stmt, 1, i);
		sqlite3_bind_text(stmt, 2, "test_user_name", -1, SQLITE_STATIC);
		sqlite3_step(stmt);
		sqlite3_reset(stmt);
	}

	sqlite3_finalize(stmt);
	sqlite3_exec(db, "END TRANSACTION;", 0, 0, &err_msg);

	sqlite3_close(db);
	remove(DB_NAME);
	return 0;
}
