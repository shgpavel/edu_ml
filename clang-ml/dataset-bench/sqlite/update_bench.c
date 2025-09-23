#include <sqlite3.h>
#include <stdio.h>

#define DB_NAME     "update_test.db"
#define TABLE_SIZE  50000
#define NUM_UPDATES 2000

int
main()
{
	sqlite3 *db;
	remove(DB_NAME);
	sqlite3_open(DB_NAME, &db);

	sqlite3_exec(db, "BEGIN;", 0, 0, 0);
	sqlite3_exec(db, "CREATE TABLE Accounts(Id INT, Balance INT);", 0, 0, 0);
	sqlite3_stmt *stmt;
	sqlite3_prepare_v2(db, "INSERT INTO Accounts VALUES(?, 100);", -1, &stmt,
	                   0);
	for (int i = 0; i < TABLE_SIZE; i++) {
		sqlite3_bind_int(stmt, 1, i);
		sqlite3_step(stmt);
		sqlite3_reset(stmt);
	}
	sqlite3_finalize(stmt);
	sqlite3_exec(db, "COMMIT;", 0, 0, 0);

	sqlite3_exec(db, "BEGIN;", 0, 0, 0);
	sqlite3_prepare_v2(
	        db, "UPDATE Accounts SET Balance = Balance + 50 WHERE Id = ?;", -1,
	        &stmt, 0);
	for (int i = 0; i < NUM_UPDATES; i++) {
		sqlite3_bind_int(stmt, 1, i);
		sqlite3_step(stmt);
		sqlite3_reset(stmt);
	}
	sqlite3_finalize(stmt);
	sqlite3_exec(db, "COMMIT;", 0, 0, 0);

	sqlite3_close(db);
	remove(DB_NAME);
	return 0;
}
