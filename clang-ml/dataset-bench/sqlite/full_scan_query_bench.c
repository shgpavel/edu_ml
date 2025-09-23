#include <sqlite3.h>
#include <stdio.h>
#include <stdlib.h>

#define DB_NAME     "query_test_no_index.db"
#define TABLE_SIZE  100000
#define NUM_QUERIES 50

int
main()
{
	sqlite3 *db;
	remove(DB_NAME);
	sqlite3_open(DB_NAME, &db);

	sqlite3_exec(db, "BEGIN;", 0, 0, 0);
	sqlite3_exec(db, "CREATE TABLE Users(Id INT, Name TEXT);", 0, 0, 0);
	sqlite3_stmt *stmt;
	sqlite3_prepare_v2(db, "INSERT INTO Users VALUES(?, ?);", -1, &stmt, 0);
	for (int i = 0; i < TABLE_SIZE; i++) {
		char name[20];
		sprintf(name, "user%d", i);
		sqlite3_bind_int(stmt, 1, i);
		sqlite3_bind_text(stmt, 2, name, -1, SQLITE_TRANSIENT);
		sqlite3_step(stmt);
		sqlite3_reset(stmt);
	}
	sqlite3_finalize(stmt);
	sqlite3_exec(db, "COMMIT;", 0, 0, 0);

	sqlite3_prepare_v2(db, "SELECT * FROM Users WHERE Name = ?;", -1, &stmt, 0);
	for (int i = 0; i < NUM_QUERIES; i++) {
		char name_to_find[20];
		sprintf(name_to_find, "user%d", rand() % TABLE_SIZE);
		sqlite3_bind_text(stmt, 1, name_to_find, -1, SQLITE_TRANSIENT);
		while (sqlite3_step(stmt) == SQLITE_ROW) {
		}
		sqlite3_reset(stmt);
	}
	sqlite3_finalize(stmt);

	sqlite3_close(db);
	remove(DB_NAME);
	return 0;
}
